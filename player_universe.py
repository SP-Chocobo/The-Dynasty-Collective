"""Sleeper-first player and league-ownership helpers.

Player identity comes from Sleeper's ``/players/nfl`` database.  League
rosters only describe ownership, and optional vendors can enrich these rows;
neither is allowed to decide whether a player exists in the application.
"""

from __future__ import annotations

from typing import Optional

# Sleeper's database also includes coaches, old placeholders, and retired
# players.  These positions are the player universe this football app can
# meaningfully display, while rostered/projected records are retained even if
# Sleeper has incomplete metadata for them.
FANTASY_POSITIONS = {"QB", "RB", "WR", "TE", "K", "DEF", "LB", "DL", "DB"}


def _score_projection(stats: dict, scoring_settings: dict) -> float:
    """Score native Sleeper stat projections without coupling this data model to HTTP."""
    total = sum(
        float(value) * float(scoring_settings.get(category, 0))
        for category, value in (stats or {}).items()
        if value
    )
    return round(total, 2)


def player_name(info: dict, player_id: str) -> str:
    """Return a usable Sleeper name, including for incomplete player records."""
    return (
        info.get("full_name")
        or f"{info.get('first_name', '')} {info.get('last_name', '')}".strip()
        or player_id
    )


def _roster_slots(roster: dict) -> dict[str, str]:
    starters = set(roster.get("starters") or [])
    taxi = set(roster.get("taxi") or [])
    reserve = set(roster.get("reserve") or [])
    return {
        str(pid): "TAXI" if pid in taxi else "IR" if pid in reserve else "Starter" if pid in starters else "Bench"
        for pid in (roster.get("players") or [])
    }


def build_player_universe(
    players_db: dict[str, dict],
    rosters: list[dict],
    *,
    users: Optional[list[dict]] = None,
    projections: Optional[dict[str, dict]] = None,
    scoring_settings: Optional[dict] = None,
    include_inactive: bool = False,
) -> list[dict]:
    """Build canonical Sleeper player rows with separate league ownership.

    ``players_db`` remains authoritative for player identity.  Roster and
    projection IDs are unioned in so a temporarily incomplete player database
    can never hide a player who is actually rostered or projected.  By default
    the returned view is useful for fantasy decisions (active players plus all
    rostered/projected players); pass ``include_inactive=True`` to inspect the
    entire cached Sleeper database.
    """
    projections = projections or {}
    owner_names = {
        str(user.get("user_id")): user.get("display_name") or user.get("metadata", {}).get("team_name")
        for user in (users or [])
    }
    ownership: dict[str, dict] = {}
    rostered_ids: set[str] = set()
    for roster in rosters or []:
        for pid, slot in _roster_slots(roster).items():
            rostered_ids.add(pid)
            ownership[pid] = {
                "roster_id": roster.get("roster_id"),
                "owner_id": roster.get("owner_id"),
                "owner_name": owner_names.get(str(roster.get("owner_id"))) or f"Roster {roster.get('roster_id', '?')}",
                "roster_slot": slot,
            }

    player_ids = set(map(str, players_db or {})) | rostered_ids | set(map(str, projections))
    rows: list[dict] = []
    for pid in player_ids:
        info = (players_db or {}).get(pid, {}) or {}
        position = info.get("position")
        is_rostered_or_projected = pid in rostered_ids or pid in projections
        if position not in FANTASY_POSITIONS and not is_rostered_or_projected:
            continue
        # Do not make "active" a destructive truth source: some Sleeper rows
        # omit it, and a rostered/projected player always remains visible.
        if not include_inactive and info.get("active") is False and not is_rostered_or_projected:
            continue
        row = {
            "player_id": pid,
            "name": player_name(info, pid),
            "position": position or "Unknown",
            "team": info.get("team") or "FA",
            "injury_status": info.get("injury_status"),
            "active": info.get("active"),
            "status": info.get("status") or "unknown",
            "ownership": "ROSTERED" if pid in ownership else "FREE AGENT",
            "available": pid not in ownership,
            # Sleeper has no public ADP or season-total-projection endpoint, but
            # search_rank (lower = more universally relevant/rosterable) is the
            # closest thing it exposes natively — good enough to order a free
            # agent list by something better than alphabetical with zero setup.
            "search_rank": info.get("search_rank"),
            **ownership.get(pid, {}),
        }
        stats = projections.get(pid)
        if stats:
            row["sleeper_proj"] = _score_projection(stats, scoring_settings or {})
        rows.append(row)

    # Player names make the canonical pool searchable even when position/team
    # metadata lags during an NFL transaction.
    return sorted(rows, key=lambda row: (row["position"], row["name"].lower(), row["player_id"]))


def available_players(universe: list[dict], position: Optional[str] = None) -> list[dict]:
    """Return only unrostered Sleeper players, retaining missing enrichment."""
    result = [row for row in universe if row.get("available")]
    if position:
        result = [row for row in result if row.get("position") == position]
    return result


def matching_players(universe: list[dict], query: str, limit: int = 12) -> list[dict]:
    """Find likely player mentions without requiring a vendor-name match."""
    query_words = {word.lower() for word in query.replace("'", " ").split() if len(word) > 1}
    if not query_words:
        return []
    matches = []
    for row in universe:
        name_words = set(row["name"].lower().replace("'", " ").split())
        overlap = len(query_words & name_words)
        if overlap:
            matches.append((overlap, row))
    return [row for _, row in sorted(matches, key=lambda item: (-item[0], item[1]["name"]))[:limit]]
