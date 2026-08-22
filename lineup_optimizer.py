"""
Real lineup optimization -- the actual fix for the Travis-Hunter-style gap: a player eligible
at multiple positions (WR/DB, TE/FLEX, whatever a league's own roster_positions and Sleeper's
fantasy_positions actually allow) isn't worth more just for HAVING multiple eligible
positions. He's worth more only when that eligibility lets a roster build a genuinely better
starting lineup than it could without him -- filling a scarce or high-scoring slot a
single-position player couldn't reach. This module computes that directly, as a real
assignment problem, rather than approximating it with a bonus multiplier keyed off "number of
eligible positions."

optimize_lineup solves the actual problem: given a roster of players (each with a value and
an eligible-position set) and a league's real starting slots (dedicated positions PLUS flex
slots expanded to whatever they accept -- see slots_from_roster_positions), find the
assignment of players to slots that maximizes total starting value. This is the classic
assignment problem (maximum-weight bipartite matching) -- solved exactly via
scipy.optimize.linear_sum_assignment, not a greedy heuristic. Greedy (assign each player to
their single best-value slot in descending order) is a well-known trap here: it can strand a
flexible player in a mediocre slot early and leave a genuinely better global assignment
undiscovered, especially exactly in the multi-eligible cases this module exists to get right.

marginal_lineup_value is the number draft_room.py actually needs: optimize_lineup(roster +
candidate) - optimize_lineup(roster) -- literally "best lineup with him minus best lineup
without him," the same formulation this app's design conversation asked for directly. Calling
it once with the candidate's FULL eligible-position set and once with ONLY his single primary
position (player_position()'s existing bucket) and taking the difference isolates the
eligibility bonus specifically -- see eligibility_bonus's own docstring. A single-position
player's bonus is exactly 0 by construction (both calls solve the identical problem), so this
never touches a player whose value the existing engine already gets right.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy.optimize import linear_sum_assignment

from player_universe import FLEX_SLOT_POSITIONS, FANTASY_POSITIONS

# Effectively-infinite cost for an ineligible (player, slot) pairing in the assignment matrix
# -- large enough that the solver will only ever pick it when there is truly no valid
# alternative (more slots of a kind than eligible players, or vice versa), and even then the
# result is filtered back out afterward (see optimize_lineup) rather than trusted as a real
# assignment.
_INELIGIBLE_COST = 1e9


def slots_from_roster_positions(roster_positions: list[str]) -> list[dict]:
    """This league's real roster_positions, expanded into one dict per STARTING slot (bench/
    taxi/IR excluded -- they don't hold a lineup value, a benched player contributes nothing
    either way). Each slot carries its own eligible-position set, so a FLEX slot competes for
    RB/WR/TE and an IDP_FLEX for DL/LB/DB, exactly as the league itself defines them -- no
    generic assumption about what "FLEX" means baked in here beyond what player_universe.py's
    FLEX_SLOT_POSITIONS already documents for the rest of this app."""
    slots = []
    for i, raw in enumerate(roster_positions or []):
        if raw in FANTASY_POSITIONS:
            slots.append({"slot_id": f"{raw}_{i}", "label": raw, "eligible": {raw}})
        elif raw in FLEX_SLOT_POSITIONS:
            slots.append({"slot_id": f"{raw}_{i}", "label": raw, "eligible": set(FLEX_SLOT_POSITIONS[raw])})
        # BN/TAXI/IR/anything else: not a lineup slot, intentionally excluded.
    return slots


def optimize_lineup(players: list[dict], slots: list[dict]) -> dict:
    """Exact maximum-total-value assignment of players to starting slots.

    players: [{"id": ..., "value": float, "eligible": set[str]}, ...]
    slots: [{"slot_id": ..., "eligible": set[str]}, ...] (see slots_from_roster_positions)

    Returns {"total_value", "assignments": [{"slot_id","player_id","value"}], "benched": [id,...]}.
    Solved via scipy's Hungarian-algorithm implementation on a cost matrix (negated value,
    with an effectively-infinite cost for ineligible pairs) -- see module docstring for why a
    greedy assignment isn't trustworthy here. Any (player, slot) pair the solver was forced
    into despite ineligibility (only possible when there's a genuine surplus with no valid
    alternative on one side) is filtered back out rather than counted -- an unfillable slot
    stays empty and that player stays benched, never a fabricated invalid start.
    """
    if not players or not slots:
        return {"total_value": 0.0, "assignments": [], "benched": [p["id"] for p in players]}

    cost = np.full((len(players), len(slots)), _INELIGIBLE_COST)
    for i, player in enumerate(players):
        for j, slot in enumerate(slots):
            if player["eligible"] & slot["eligible"]:
                cost[i, j] = -player["value"]

    row_idx, col_idx = linear_sum_assignment(cost)

    assignments = []
    assigned_player_ids = set()
    for i, j in zip(row_idx, col_idx):
        if cost[i, j] >= _INELIGIBLE_COST:
            continue  # forced pairing with no real eligibility -- not a valid assignment
        assignments.append({
            "slot_id": slots[j]["slot_id"], "player_id": players[i]["id"], "value": players[i]["value"],
        })
        assigned_player_ids.add(players[i]["id"])

    total_value = sum(a["value"] for a in assignments)
    benched = [p["id"] for p in players if p["id"] not in assigned_player_ids]
    return {"total_value": round(total_value, 2), "assignments": assignments, "benched": benched}


def marginal_lineup_value(
    roster_players: list[dict], candidate: dict, roster_positions: list[str],
) -> dict:
    """The real "best lineup with him minus best lineup without him" number. candidate is
    {"id", "value", "eligible"} same shape as roster_players' entries. Returns
    {"with_candidate", "without_candidate", "marginal_value"} -- never just the delta alone,
    so a caller (or a human auditing a recommendation) can see both lineups' actual totals,
    not just trust a single subtracted number."""
    slots = slots_from_roster_positions(roster_positions)
    without = optimize_lineup(roster_players, slots)
    with_candidate = optimize_lineup(roster_players + [candidate], slots)
    return {
        "with_candidate": with_candidate["total_value"],
        "without_candidate": without["total_value"],
        "marginal_value": round(with_candidate["total_value"] - without["total_value"], 2),
    }


def eligibility_bonus(
    roster_players: list[dict], candidate_id, candidate_value: float,
    candidate_full_eligible: set[str], candidate_primary_position: Optional[str],
    roster_positions: list[str],
) -> dict:
    """The value created SPECIFICALLY by a candidate's multi-position eligibility -- the
    actual number this module exists to produce. Computes marginal_lineup_value twice: once
    with the candidate's full eligible-position set, once as if he could only play his single
    primary position (the bucket the rest of this app already uses) -- the difference is
    value his flexibility alone unlocks, isolated from his raw value (which both calls solve
    identically, so a single-position player's bonus is exactly 0.0, never a guess).

    Genuinely roster-dependent, not universal -- the same player's eligibility bonus differs
    by team, since it depends on what's already rostered and which slots are actually tight.
    That's why this lives alongside need_bonus in draft_room.py's team_acquisition_value, not
    folded into universal_value (see draft_room.py's own module docstring on that split).

    Naturally bounded, unlike need_bonus: a candidate's marginal contribution can never
    exceed his own value (the best he can ever do is fill a genuinely empty slot outright),
    so no artificial cap is applied here the way NEED_BONUS_MAX exists for a heuristic
    overlay -- this is a real, self-limiting economic quantity, not a nudge."""
    primary_only = {candidate_primary_position} if candidate_primary_position else set()
    if candidate_full_eligible <= primary_only:
        # Nothing beyond his one primary bucket -- the bonus is exactly 0 by construction
        # regardless of what the assignment problem says, so skip solving it twice (this is
        # the common case -- most players are single-position -- and draft_room.py calls this
        # once per candidate across a full live-draft board, so the redundant second solve
        # isn't free at that scale).
        only_result = marginal_lineup_value(roster_players, {"id": candidate_id, "value": candidate_value, "eligible": primary_only}, roster_positions)
        return {
            "eligibility_bonus": 0.0,
            "marginal_value_full_eligibility": only_result["marginal_value"],
            "marginal_value_primary_position_only": only_result["marginal_value"],
        }

    full_candidate = {"id": candidate_id, "value": candidate_value, "eligible": candidate_full_eligible}
    full_result = marginal_lineup_value(roster_players, full_candidate, roster_positions)

    primary_candidate = {"id": candidate_id, "value": candidate_value, "eligible": primary_only}
    primary_result = marginal_lineup_value(roster_players, primary_candidate, roster_positions)

    bonus = round(full_result["marginal_value"] - primary_result["marginal_value"], 2)
    return {
        "eligibility_bonus": bonus,
        "marginal_value_full_eligibility": full_result["marginal_value"],
        "marginal_value_primary_position_only": primary_result["marginal_value"],
    }
