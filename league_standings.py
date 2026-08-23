"""Real Sleeper standings -- wins/losses/ties/points, pulled directly off each roster's own
`settings` sub-dict (fields Sleeper's `/league/{id}/rosters` endpoint already returns, per
sleeper_client.get_rosters -- never previously read anywhere in this app).

Deliberately just facts: a team's actual won-lost record and scored/allowed points, never a
computed strength score. See the design-language reference's League "hard contract" --
strength is an entry point, never a conclusion -- this module IS that entry point, and it's a
real one already sitting in data this app fetches, not something invented for the purpose.
Any decomposition of "why is this team strong" (positional depth, roster construction, ...)
stays a separate, later concern; this module only ever answers "what's the actual record."
"""

from __future__ import annotations


def team_standings(rosters: list[dict], owner_names: dict) -> list[dict]:
    """One row per roster: {roster_id, team, wins, losses, ties, points_for, points_against},
    sorted by the league's own real record (wins desc, then points_for desc -- the standard
    tiebreak), never a computed rating. Every field is a direct read off Sleeper's own
    roster["settings"] sub-dict; a missing settings block (an odd but real possibility, e.g. a
    brand new league with no games played yet) reads as all-zero rather than raising."""
    rows = []
    for r in rosters:
        settings = r.get("settings") or {}
        roster_id = r.get("roster_id")
        rows.append({
            "roster_id": roster_id,
            "team": owner_names.get(roster_id, f"Roster {roster_id}"),
            "wins": settings.get("wins", 0) or 0,
            "losses": settings.get("losses", 0) or 0,
            "ties": settings.get("ties", 0) or 0,
            "points_for": _decimal_points(settings, "fpts", "fpts_decimal"),
            "points_against": _decimal_points(settings, "fpts_against", "fpts_against_decimal"),
        })
    rows.sort(key=lambda row: (-row["wins"], -row["points_for"]))
    return rows


def _decimal_points(settings: dict, whole_key: str, decimal_key: str) -> float:
    """Sleeper splits points into a whole-number field and a separate 0-99 decimal remainder
    (fpts=110, fpts_decimal=42 means 110.42) -- combined here once rather than making every
    caller remember the split."""
    whole = settings.get(whole_key, 0) or 0
    decimal = settings.get(decimal_key, 0) or 0
    return round(whole + decimal / 100, 2)
