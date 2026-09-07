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

from typing import Optional


def team_standings(rosters: list[dict], owner_names: dict) -> list[dict]:
    """One row per roster: {roster_id, team, wins, losses, ties, points_for, points_against},
    sorted by the league's own real record (wins desc, then points_for desc -- the standard
    tiebreak), never a computed rating. Every field is a direct read off Sleeper's own
    roster["settings"] sub-dict.

    ABSENCE IS NOT A ZERO. A roster whose settings block is missing entirely, or whose record
    fields are absent/null in it, has NO RECORD -- that is not the same fact as a team that
    has played and stands at 0-0-0, and this module used to render the two identically
    (`settings.get("wins", 0) or 0` collapsed a missing key, an explicit null AND an explicit
    zero into one indistinguishable 0). Downstream that mattered twice over: the League view
    prints W/L/T/PF straight from these fields, and it derives "has this season started" by
    summing them -- so a league whose rosters carried no settings at all produced the positive
    on-screen claim "No games played yet this season (0-0 across the board)" out of data that
    was never there. An absent field now reads as None; a real, measured 0 still reads as 0.

    ORDERING. Rows that carry a measured record sort exactly as before (wins desc, points_for
    desc). Rows with no record are never compared as numbers against ones that have it -- they
    order LAST, alphabetically among themselves, matching the rule this codebase already
    applies to absent values everywhere else (exclude, propagate, order last)."""
    rows = []
    for r in rosters:
        settings = r.get("settings") or {}
        roster_id = r.get("roster_id")
        rows.append({
            "roster_id": roster_id,
            "team": owner_names.get(roster_id, f"Roster {roster_id}"),
            "wins": _reported(settings, "wins"),
            "losses": _reported(settings, "losses"),
            "ties": _reported(settings, "ties"),
            "points_for": _decimal_points(settings, "fpts", "fpts_decimal"),
            "points_against": _decimal_points(settings, "fpts_against", "fpts_against_decimal"),
        })
    rows.sort(key=_sort_key)
    return rows


def has_record(row: dict) -> bool:
    """True when this row's won-lost record was actually reported -- the one test every caller
    should use before doing arithmetic on wins/losses/ties, so "no record" cannot be summed
    into a claim about how many games the league has played."""
    return all(row[field] is not None for field in ("wins", "losses", "ties"))


def _sort_key(row: dict):
    unranked = not has_record(row)
    return (
        unranked,
        0 if unranked else -row["wins"],
        0 if unranked or row["points_for"] is None else -row["points_for"],
        row["team"] if unranked else "",
    )


def _reported(settings: dict, key: str) -> Optional[int]:
    """The raw field if Sleeper reported one, None if it did not. Deliberately NOT
    `.get(key, 0) or 0`: that form is doubly collapsing -- the default already covers a missing
    key, and the `or 0` additionally rewrites an explicit null and cannot tell either from a
    real 0."""
    value = settings.get(key)
    return None if value is None else value


def _decimal_points(settings: dict, whole_key: str, decimal_key: str) -> Optional[float]:
    """Sleeper splits points into a whole-number field and a separate 0-99 decimal remainder
    (fpts=110, fpts_decimal=42 means 110.42) -- combined here once rather than making every
    caller remember the split.

    None when the whole-points field itself was never reported: no points total exists to
    state, and 0.0 would be a claim that this team has scored nothing. The remainder field is
    a refinement of a total that is already there, so a reported whole with no remainder is
    read at whole-point precision rather than discarding the total we do have."""
    whole = _reported(settings, whole_key)
    if whole is None:
        return None
    decimal = _reported(settings, decimal_key) or 0
    return round(whole + decimal / 100, 2)
