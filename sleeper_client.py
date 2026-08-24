"""
Sleeper API client.

Talks to Sleeper's public, key-free REST API (https://api.sleeper.app/v1/) to
auto-discover leagues for a username and pull rosters, scoring settings,
taxi squads, and traded draft picks. Every league sync is cached to disk in
data/sleeper_snapshots/ so the dashboard has something to show even when
offline or rate-limited.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

import requests

BASE_URL = "https://api.sleeper.app/v1"
ROOT_URL = "https://api.sleeper.app"  # projections/stats live outside /v1 — see get_weekly_projections
# Last-resort fallback only -- get_user_leagues derives the real season from Sleeper's own
# live /state/nfl on every call now, so this only matters if that endpoint itself is
# unreachable. Not something that needs bumping every year on its own.
DEFAULT_SEASON = "2026"
PLAYERS_CACHE_MAX_AGE_SECONDS = 24 * 60 * 60  # Sleeper asks that /players/nfl be pulled at most once/day
REQUEST_TIMEOUT = 15
SNAPSHOT_HISTORY_KEEP = 10  # timestamped snapshots kept per league beyond the always-current _latest.json


class SleeperAPIError(RuntimeError):
    """Raised when the Sleeper API returns an unexpected response."""


class SleeperClient:
    def __init__(self, cache_dir: str = "data/sleeper_snapshots"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()

    # -- low-level ---------------------------------------------------------

    def _get(self, path: str, base: str = BASE_URL) -> Any:
        url = f"{base}{path}"
        try:
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            raise SleeperAPIError(f"Failed to reach Sleeper API at {url}: {exc}") from exc
        if resp.status_code == 404:
            return None
        if not resp.ok:
            raise SleeperAPIError(f"Sleeper API {url} returned {resp.status_code}: {resp.text[:200]}")
        if not resp.text:
            return None
        return resp.json()

    # -- user / league discovery --------------------------------------------

    def get_user(self, username: str) -> Optional[dict]:
        return self._get(f"/user/{username}")

    def get_user_leagues(self, user_id: str, season: Optional[str] = None, sport: str = "nfl") -> list[dict]:
        # A hardcoded default season here would silently go stale every year -- confirmed:
        # DEFAULT_SEASON used to be a bare "2026" constant, so on the season rollover a caller
        # that didn't pass one explicitly (app.py's own sync never has) would keep querying the
        # wrong year and just see "no leagues found" with no indication why. Derive it from
        # Sleeper's own live /state/nfl instead when the caller doesn't pass one, falling back
        # to DEFAULT_SEASON only if that call itself fails (offline, API outage) -- same
        # fail-soft posture get_nfl_state already has.
        if season is None:
            state = self.get_nfl_state()
            season = (state or {}).get("season") or DEFAULT_SEASON
        leagues = self._get(f"/user/{user_id}/leagues/{sport}/{season}")
        return leagues or []

    def get_league(self, league_id: str) -> Optional[dict]:
        return self._get(f"/league/{league_id}")

    def get_rosters(self, league_id: str) -> list[dict]:
        return self._get(f"/league/{league_id}/rosters") or []

    def get_league_users(self, league_id: str) -> list[dict]:
        return self._get(f"/league/{league_id}/users") or []

    def get_traded_picks(self, league_id: str) -> list[dict]:
        return self._get(f"/league/{league_id}/traded_picks") or []

    def get_drafts(self, league_id: str) -> list[dict]:
        return self._get(f"/league/{league_id}/drafts") or []

    def get_draft(self, draft_id: str) -> Optional[dict]:
        """One draft's own metadata -- type (snake/linear/auction), status, settings (rounds,
        roster/starter slot counts), draft_order. Distinct from get_drafts (a league's list of
        drafts) and get_draft_picks (that draft's picks so far) -- see draft_room.py, the only
        current caller, for how the three combine into a live draft-pick recommendation."""
        return self._get(f"/draft/{draft_id}")

    def get_draft_picks(self, draft_id: str) -> list[dict]:
        """Every pick made in this draft so far, in draft order -- Sleeper has no push/websocket
        feed for third parties, so a live view re-polls this on demand (a Refresh action, not a
        background timer) same as every other "live-ish" read this client already does."""
        return self._get(f"/draft/{draft_id}/picks") or []

    def get_matchups(self, league_id: str, week: int) -> list[dict]:
        """One entry per roster for this week -- {roster_id, matchup_id, points, starters,
        starters_points, players, custom_points, ...}. Two entries sharing the same non-null
        matchup_id are playing each other that week; a roster with no matchup yet (a bye, or a
        week before Sleeper has generated a schedule -- preseason, most commonly) carries
        matchup_id: null. Unlike get_weekly_projections, this is one of Sleeper's own
        documented, stable v1 endpoints, not a reverse-engineered one -- still returns [] on
        any failure or empty response, matching every other list-returning method here."""
        return self._get(f"/league/{league_id}/matchups/{week}") or []

    # -- player database (large, cached daily) ------------------------------

    def get_players(self, force_refresh: bool = False) -> dict[str, dict]:
        cache_path = self.cache_dir / "players_nfl.json"
        if not force_refresh and cache_path.exists():
            age = time.time() - cache_path.stat().st_mtime
            if age < PLAYERS_CACHE_MAX_AGE_SECONDS:
                cached = self._read_players_cache(cache_path)
                if cached is not None:
                    return cached
                # Corrupt but not yet stale -- fall through to a live re-fetch below rather
                # than raising, same fail-soft posture as every other method here.

        try:
            players = self._get("/players/nfl")
        except SleeperAPIError:
            players = None

        if players:
            cache_path.write_text(json.dumps(players))
            return players

        if cache_path.exists():
            cached = self._read_players_cache(cache_path)
            if cached is not None:
                return cached
        return {}

    @staticmethod
    def _read_players_cache(cache_path: Path) -> Optional[dict[str, dict]]:
        """None (never raises) on a corrupt cache file -- this is a ~10MB re-fetchable cache,
        not durable data, so an interrupted write just means "treat it as a cache miss," not
        an app-crashing exception every future page load until someone manually deletes it."""
        try:
            return json.loads(cache_path.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    # -- native weekly stat-category projections (undocumented endpoint) ----
    #
    # Sleeper's own apps compute the "proj" points you see in-app by pulling a
    # per-player, per-stat-category projection (pass_yd, rush_td, rec, ...)
    # and multiplying it by your league's own scoring_settings — the same
    # weights get_league() already returns. That projections endpoint is NOT
    # part of Sleeper's documented v1 API; it's reverse-engineered from what
    # their own clients call, so it could change or disappear without notice.
    # Every method here fails soft (returns {} / None) rather than raising,
    # so a shape change or outage degrades this one feature, not the app.

    def get_nfl_state(self) -> Optional[dict]:
        """Current NFL season/week, e.g. {'season': '2026', 'week': 3, 'season_type': 'regular'}."""
        try:
            return self._get("/state/nfl")
        except SleeperAPIError:
            return None

    def get_weekly_projections(self, season: str, week: int, season_type: str = "regular") -> dict[str, dict]:
        """player_id -> {stat_category: projected_value, ...} for one week."""
        try:
            # Sleeper's projection API uses season/week as the path and the
            # game segment as a query parameter.  Putting ``season_type`` in
            # the path (as its stats endpoint does) silently returned no
            # records, making otherwise healthy league syncs show no native
            # projections.
            data = self._get(f"/projections/nfl/{season}/{week}?season_type={season_type}", base=ROOT_URL)
        except SleeperAPIError:
            return {}
        if not data:
            return {}

        result: dict[str, dict] = {}
        if isinstance(data, dict):
            for pid, entry in data.items():
                stats = entry.get("stats", entry) if isinstance(entry, dict) else None
                if stats:
                    result[str(pid)] = stats
        elif isinstance(data, list):
            for entry in data:
                if not isinstance(entry, dict):
                    continue
                pid = entry.get("player_id")
                stats = entry.get("stats")
                if pid and stats:
                    result[str(pid)] = stats
        return result

    # -- aggregate sync -------------------------------------------------------

    def sync_league(self, league_id: str, players_db: Optional[dict[str, dict]] = None) -> dict:
        """Pull everything for one league and cache a timestamped snapshot."""
        league = self.get_league(league_id)
        if league is None:
            raise SleeperAPIError(f"League {league_id} not found")

        nfl_state = self.get_nfl_state() or {}
        season = nfl_state.get("season") or league.get("season")
        week = nfl_state.get("week")
        # The state endpoint reports the segment currently being played
        # (including preseason/postseason).  Hard-coding "regular" made a
        # healthy sync look like it had no projections outside that segment.
        season_type = nfl_state.get("season_type") or "regular"
        projections: dict[str, dict] = {}
        projection_attempts: list[dict] = []
        projection_request = {"season": season, "week": week, "season_type": season_type}
        if season and week is not None:
            # During preseason Sleeper's state reports the preseason game
            # number.  For a normal fantasy roster screen the useful next
            # projection is regular-season week 1, so prefer it and retain
            # the preseason request only as a fallback.
            candidates = [(str(season_type), int(week))]
            if season_type == "pre":
                candidates = [("regular", 1), ("pre", int(week))]
            seen: set[tuple[str, int]] = set()
            for candidate_type, candidate_week in candidates:
                if (candidate_type, candidate_week) in seen:
                    continue
                seen.add((candidate_type, candidate_week))
                try:
                    candidate = self.get_weekly_projections(str(season), candidate_week, candidate_type)
                except (TypeError, ValueError):
                    candidate = {}
                projection_attempts.append({
                    "season": season,
                    "week": candidate_week,
                    "season_type": candidate_type,
                    "count": len(candidate),
                })
                if candidate:
                    projections = candidate
                    projection_request = projection_attempts[-1].copy()
                    projection_request.pop("count", None)
                    break

        # Tied to the exact week projections above resolved to (not the raw nfl_state week
        # directly) -- during preseason that's the regular-season-1 fallback, and matchups
        # don't exist for a preseason week anyway (no schedule generated yet), so this keeps
        # "which week is this snapshot about" a single decision instead of two that could
        # silently disagree.
        matchup_week = projection_request.get("week")
        matchups = self.get_matchups(league_id, int(matchup_week)) if matchup_week is not None else []

        snapshot = {
            "synced_at": time.time(),
            "league": league,
            "rosters": self.get_rosters(league_id),
            "users": self.get_league_users(league_id),
            "traded_picks": self.get_traded_picks(league_id),
            "nfl_state": nfl_state,
            "projection_request": projection_request,
            "projection_attempts": projection_attempts,
            "projections": projections,
            "matchups": matchups,
        }

        self._write_snapshot(league_id, snapshot)
        return snapshot

    def _write_snapshot(self, league_id: str, snapshot: dict) -> None:
        ts = int(snapshot.get("synced_at", time.time()))
        (self.cache_dir / f"{league_id}_{ts}.json").write_text(json.dumps(snapshot, indent=2))
        (self.cache_dir / f"{league_id}_latest.json").write_text(json.dumps(snapshot, indent=2))
        self._prune_old_snapshots(league_id)

    def _prune_old_snapshots(self, league_id: str, keep: int = SNAPSHOT_HISTORY_KEEP) -> None:
        """Nothing in this app actually reads a timestamped {league_id}_{ts}.json back
        (load_latest_snapshot only ever reads the _latest.json alongside it) -- every real
        sync still wrote and kept one forever, so a league synced daily for a season
        accumulates hundreds of files nothing ever opens again. Keep a bounded recent history
        (newest-timestamp-first) rather than either deleting the ability to look back entirely
        or leaving it truly unbounded."""
        pattern = f"{league_id}_*.json"
        latest_name = f"{league_id}_latest.json"
        timestamped = sorted(
            (p for p in self.cache_dir.glob(pattern) if p.name != latest_name),
            key=lambda p: p.stat().st_mtime, reverse=True,
        )
        for p in timestamped[keep:]:
            p.unlink(missing_ok=True)

    def load_latest_snapshot(self, league_id: str) -> Optional[dict]:
        path = self.cache_dir / f"{league_id}_latest.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            # Re-syncable (sync_league() rebuilds this from Sleeper's live API), so a corrupt
            # cache is just a cache miss, not an app-crashing exception -- same posture as
            # "no snapshot cached yet" a few lines up.
            return None


# -- helpers for interpreting a synced league --------------------------------

def compute_points_from_stats(stats: dict, scoring_settings: dict) -> float:
    """Apply a league's own scoring_settings to a raw per-category stat projection.

    This reproduces exactly what Sleeper's own apps do to show a "proj" points
    column: stats and scoring_settings share Sleeper's stat-category naming
    (pass_yd, rec, rush_td, ...), so the weighted sum is this league's native,
    scoring-accurate point projection for the week.
    """
    total = 0.0
    for category, weight in (scoring_settings or {}).items():
        value = (stats or {}).get(category)
        if value:
            total += float(value) * float(weight)
    return round(total, 2)


def find_roster_for_user(rosters: list[dict], user_id: str) -> Optional[dict]:
    for roster in rosters:
        if roster.get("owner_id") == user_id:
            return roster
    return None


def find_opponent_roster_id(matchups: list[dict], my_roster_id: int) -> Optional[int]:
    """Given one week's raw get_matchups() list, the roster_id playing my_roster_id this week,
    or None if unresolved -- a bye week, an unpaired roster, or an empty/not-yet-generated
    schedule (preseason most commonly). Never guesses: if more than one other roster somehow
    shares my_roster_id's matchup_id (a malformed or unusual payload), this returns None rather
    than picking one, the same fail-soft-not-fabricate posture as the rest of this client."""
    my_entry = next((m for m in matchups if m.get("roster_id") == my_roster_id), None)
    if my_entry is None or my_entry.get("matchup_id") is None:
        return None
    opponents = [
        m.get("roster_id") for m in matchups
        if m.get("roster_id") != my_roster_id and m.get("matchup_id") == my_entry["matchup_id"]
    ]
    return opponents[0] if len(opponents) == 1 else None


def league_format_summary(league: dict) -> dict:
    """Human-readable summary of scoring/roster settings shown in the header bar."""
    settings = league.get("settings", {}) or {}
    scoring_settings = league.get("scoring_settings", {}) or {}
    roster_positions = league.get("roster_positions", []) or []

    is_superflex = roster_positions.count("SUPER_FLEX") > 0 or roster_positions.count("QB") > 1
    is_ppr = scoring_settings.get("rec", 0) >= 1
    is_half_ppr = scoring_settings.get("rec", 0) == 0.5
    ppr_label = "Full PPR" if is_ppr else ("Half PPR" if is_half_ppr else "Standard")
    # Sleeper's own key for a per-reception bonus specific to TEs -- a league scoring TE
    # receptions any higher than its general "rec" setting is exactly what "TE premium" means
    # (Draft Sharks' own TE-premium exports are built around this same idea -- see
    # data_merger._detect_rankings_format's docstring for how that maps onto which Dynasty
    # Rankings file this app prefers for a league configured this way).
    is_te_premium = scoring_settings.get("bonus_rec_te", 0) > 0

    return {
        "name": league.get("name", "Unnamed League"),
        "season": league.get("season"),
        "type": "Dynasty" if settings.get("type") == 2 else ("Keeper" if settings.get("type") == 1 else "Redraft"),
        "teams": settings.get("num_teams", len(league.get("roster_positions", []) and [])) or league.get("total_rosters"),
        "superflex": is_superflex,
        "scoring": ppr_label,
        "te_premium": is_te_premium,
        "taxi_slots": settings.get("taxi_slots", 0),
        "roster_positions": roster_positions,
    }
