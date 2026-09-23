"""Score a drafted roster on WHAT ACTUALLY HAPPENED, week by week. The first ruler the engine
cannot optimise toward.

WHY THIS EXISTS. `#288` concluded that no ruler independent of the engine's own objective was
available, so a deficit could never be converted into a claim about real-world cost. Every quality
number in this repository scores rosters on PROJECTIONS -- `run_roster_proof`, `run_smoke_seats`,
`draft_battery.roster_strength`. The engine is built to maximise a projection-derived quantity, so
grading it on projections grades it partly on its own homework.

`#18` changed what is possible. Both arms are now committed for two seasons: 18 weeks of
projections AND 18 weeks of realized stats, 2023 and 2024. So a roster can be drafted from a
season's projections and scored on that season's OUTCOMES.

THE THING A SEASON-TOTAL RULER CANNOT SEE, and the reason this is solved per week. The projected
ruler solves ONE optimal lineup over season totals, with no absences. That makes a bench a pure
liability: every benched player is value you paid for and never field. Measured on the starting
band, 2023/2024 weeks 1-17, roughly 11-16% of skill starter-weeks are absences (RB 0.14/0.12,
WR 0.11/0.14, TE 0.15/0.16, QB 0.08/0.07) against 0.06 for K and DEF, which is the bye alone. A
weekly solve fills those weeks from the bench automatically, because a player who did not play
scores nothing that week and the optimiser starts someone else.

So this ruler REWARDS DEPTH, and the projected ruler cannot. That is not a tuning choice; it falls
out of solving the lineup the way a season is actually played.

IT ALSO MAKES K/DST PLACEMENT MEASURABLE. Under the projected ruler the league total moved
-0.16%/+0.08% across three drafts whose DEF placement ranged from round 5 to round 10 -- it is
INDIFFERENT to when a defense is taken, so it can neither reward nor punish a fix (#30). A weekly
realized solve can, because a defense drafted in round 5 costs a skill player who would have
covered real absences.

WHAT IT DOES NOT MODEL, stated plainly:
  - Waivers and in-season transactions. The roster is frozen at the draft. A real manager streams,
    and this ruler gives them no credit for it -- so it is a LOWER bound on a streaming strategy
    and does not settle streaming by itself.
  - Trades, IR slots, and the fact that a manager sets a lineup on Saturday rather than with
    hindsight. The weekly solve is an ORACLE lineup: it starts the best actual scorers. Every arm
    gets the same advantage, so a comparison survives it, but the absolute totals are ceilings.
  - A player with no stat line in a week is ABSENT, not a zero-point performance (`#187`). He is
    simply not offered to that week's solve, which is what being unavailable means.
"""

from __future__ import annotations

import lineup_optimizer as lo
import player_universe as pu

#: Regular-season weeks to score. A week nobody in the league recorded a line for is skipped, and
#: the count of scored weeks travels with the total so a short capture cannot masquerade as a bad
#: roster.
DEFAULT_WEEKS = range(1, 19)


def weekly_points(season_weeks: dict[str, dict], scoring: dict) -> dict[str, dict[str, float]]:
    """{week: {player_id: realized points}} under this league's scoring.

    Scored through `player_universe.score_projection` -- the same function the engine uses on a
    stat line -- so the ruler cannot drift from how the app values one. Scoring realized stats
    with the projection's own scorer is the point: it removes scoring settings as a variable.
    """
    return {week: {pid: pu.score_projection(stats, scoring) for pid, stats in lines.items()}
            for week, lines in season_weeks.items()}


def score_roster_realized(player_ids, players_db: dict, weekly: dict[str, dict[str, float]],
                          slots: list[dict], weeks=DEFAULT_WEEKS) -> dict:
    """What this roster ACTUALLY scored, as the sum of each week's best legal lineup.

    Returns the total, the weeks scored, and the bench contribution -- the last because "did the
    bench ever play" is the question a season-total ruler structurally cannot answer, and
    reporting only the total would hide it again.
    """
    ids = [str(p) for p in player_ids]
    eligible = {}
    for pid in ids:
        info = players_db.get(pid) or {}
        positions = set(info.get("fantasy_positions") or
                        ([info["position"]] if info.get("position") else []))
        # #172: eligibility comes from fantasy_positions, never the primary `position`. A player
        # listed RB/WR is eligible at both, and collapsing him benches him out of a legal FLEX.
        eligible[pid] = positions

    total, scored_weeks, starts = 0.0, 0, {}
    for week in weeks:
        points = weekly.get(str(week))
        if not points:
            continue
        # ABSENT IS NOT ZERO (#187). A player with no line this week is not offered to the solve
        # at all, which is what being unavailable means. Offering him at 0.0 would let the
        # optimiser "start" him and report a filled slot that never existed.
        available = [{"id": pid, "value": points[pid], "eligible": eligible[pid]}
                     for pid in ids if pid in points]
        if not available:
            continue
        scored_weeks += 1
        solved = lo.optimize_lineup(available, slots)
        total += solved["total_value"]
        for assignment in solved["assignments"]:
            starts[assignment["player_id"]] = starts.get(assignment["player_id"], 0) + 1

    # The draft's own order is not known here, so "bench" is defined by USAGE: a player who never
    # started is one this roster carried and never fielded. That is the honest reading of depth --
    # a backup who covered three absences is not a bench player those weeks.
    never_started = [pid for pid in ids if pid not in starts]
    return {
        "total": round(total, 2),
        "weeks_scored": scored_weeks,
        "players": len(ids),
        "players_who_ever_started": len(starts),
        "players_who_never_started": len(never_started),
        # None, never 0.0, when no week could be scored -- an unscored roster is not a roster
        # that scored nothing.
        "points_per_week": round(total / scored_weeks, 2) if scored_weeks else None,
    }


def slots_for(league: dict) -> list[dict]:
    """The league's starting slots, from the one home that already defines them."""
    return lo.slots_from_roster_positions(league.get("roster_positions") or [])
