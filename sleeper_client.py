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

    def _get(self, path: str) -> Any:
        url = f"{BASE_URL}{path}"
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

        players = self._get("/players/nfl")
        if players:
            cache_path.write_text(json.dumps(players))
            return players

        if cache_path.exists():
            return json.loads(cache_path.read_text())
        return {}

    # -- aggregate sync -------------------------------------------------------

    def sync_league(self, league_id: str, players_db: Optional[dict[str, dict]] = None) -> dict:
        """Pull everything for one league and cache a timestamped snapshot."""
        league = self.get_league(league_id)
        if league is None:
            raise SleeperAPIError(f"League {league_id} not found")

        snapshot = {
            "synced_at": time.time(),
            "league": league,
            "rosters": self.get_rosters(league_id),
            "users": self.get_league_users(league_id),
            "traded_picks": self.get_traded_picks(league_id),
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
