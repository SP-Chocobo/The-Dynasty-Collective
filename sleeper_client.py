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
DEFAULT_SEASON = "2026"
PLAYERS_CACHE_MAX_AGE_SECONDS = 24 * 60 * 60  # Sleeper asks that /players/nfl be pulled at most once/day
REQUEST_TIMEOUT = 15


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

    def get_user_leagues(self, user_id: str, season: str = DEFAULT_SEASON, sport: str = "nfl") -> list[dict]:
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

    # -- player database (large, cached daily) ------------------------------

    def get_players(self, force_refresh: bool = False) -> dict[str, dict]:
        cache_path = self.cache_dir / "players_nfl.json"
        if not force_refresh and cache_path.exists():
            age = time.time() - cache_path.stat().st_mtime
            if age < PLAYERS_CACHE_MAX_AGE_SECONDS:
                return json.loads(cache_path.read_text())

        try:
            players = self._get("/players/nfl")
        except SleeperAPIError:
            players = None

        if players:
            cache_path.write_text(json.dumps(players))
            return players

        if cache_path.exists():
            return json.loads(cache_path.read_text())
        return {}

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
        }

        self._write_snapshot(league_id, snapshot)
        return snapshot

    def _write_snapshot(self, league_id: str, snapshot: dict) -> None:
        ts = int(snapshot.get("synced_at", time.time()))
        (self.cache_dir / f"{league_id}_{ts}.json").write_text(json.dumps(snapshot, indent=2))
        (self.cache_dir / f"{league_id}_latest.json").write_text(json.dumps(snapshot, indent=2))

    def load_latest_snapshot(self, league_id: str) -> Optional[dict]:
        path = self.cache_dir / f"{league_id}_latest.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())


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


def league_format_summary(league: dict) -> dict:
    """Human-readable summary of scoring/roster settings shown in the header bar."""
    settings = league.get("settings", {}) or {}
    scoring_settings = league.get("scoring_settings", {}) or {}
    roster_positions = league.get("roster_positions", []) or []

    is_superflex = roster_positions.count("SUPER_FLEX") > 0 or roster_positions.count("QB") > 1
    is_ppr = scoring_settings.get("rec", 0) >= 1
    is_half_ppr = scoring_settings.get("rec", 0) == 0.5
    ppr_label = "Full PPR" if is_ppr else ("Half PPR" if is_half_ppr else "Standard")

    return {
        "name": league.get("name", "Unnamed League"),
        "season": league.get("season"),
        "type": "Dynasty" if settings.get("type") == 2 else ("Keeper" if settings.get("type") == 1 else "Redraft"),
        "teams": settings.get("num_teams", len(league.get("roster_positions", []) and [])) or league.get("total_rosters"),
        "superflex": is_superflex,
        "scoring": ppr_label,
        "taxi_slots": settings.get("taxi_slots", 0),
        "roster_positions": roster_positions,
    }
