"""
Strategic layer on top of draft_room.py's board: not just "who's the best player available"
but "should I take him now, or will he survive to my next pick, and what does an opponent
gain if I let him go." Same zero-LLM, deterministic philosophy as draft_room.py (see its own
module docstring) -- no LLM in this critical path.

CORE IDEA: universal_value (draft_room.py's own bpa-based score) answers "how good is this
player, full stop." It does NOT answer "how urgently do I need to take him THIS pick" -- that
depends on whether he'd still be there next time. This module estimates that survival
probability from data this app already has (draft order, every intervening team's own roster
and needs, recent pick history) and turns it into three real, separate numbers per candidate:

  survival_probability   -- P(still on the board when it's my turn again)
  opportunity_cost       -- universal_value * (1 - survival_probability): the expected value
                             LOST by not taking him now, if he doesn't survive
  denial_value           -- the best VALUE AN OPPONENT WOULD HAVE GOTTEN from him, weighted by
                             how likely that specific opponent actually was to take him -- what
                             the user's own pick prevents someone else from getting, not a
                             number this player's ranking already implies for the user

SURVIVAL MODEL: for each roster picking between now and the user's next turn, this looks at
THAT roster's own compute_draft_board (their own needs, their own board -- a player scarce for
one team isn't necessarily scarce for another). Where the target player ranks on THAT team's
board maps to a bounded, documented take-probability (RANK_TAKE_PROBABILITY) -- a rank-1 guy
is likely gone, a rank-15 guy on their board is not, regardless of how he ranks on the user's
own board. Multiplying (1 - p_take) across every intervening pick gives the compound survival
probability.

PERFORMANCE, and the real bug this shape fixes: an earlier version recomputed
compute_draft_board once per intervening PICK POSITION (not per unique team) AND once per
CANDIDATE separately, with each intervening step simulating a hypothetical removal to feed
the next -- confirmed live, this took 40+ seconds against a modest 212-player pool for a
worst-case 22-pick gap, unusable against any real pick clock. Every opponent board this
module needs is now computed exactly ONCE, off the actual current pool (no hypothetical
sequential removals), and shared across every candidate being analyzed and every later use of
that same roster's board. That's a deliberate precision-for-speed tradeoff: a team that picks
twice in the same intervening window is scored from the same snapshot board both times rather
than a resimulated one accounting for their own first pick -- acceptable given every number
here is already a labeled approximation, not an empirical one, and the alternative was too
slow to use at all.

None of RANK_TAKE_PROBABILITY, POSITIONAL_RUN_BOOST, or the run-detection thresholds are
empirically backtested against real draft behavior -- they are principled, bounded, clearly
labeled starting points, the same honesty this app applies to every other constant that isn't
a real number pulled from a real source (see draft_room.py's own constants for the identical
pattern). A rank-1 take-probability of 55%, not 95%, is a deliberate choice: real drafts have
real variance (reaches, unexpected runs, a team simply preferring someone else) that a
confident-sounding single number would misrepresent as certainty.
"""

from __future__ import annotations

from collections import Counter
from typing import Optional

from data_merger import DataMerger
from draft_room import compute_draft_board
from player_universe import player_position

# How likely a team is to take the player sitting at a given rank on THEIR OWN board (not the
# user's) -- bounded, deliberately not near-certain even at rank 1, since real drafts have
# real variance a single confident number would misrepresent. Never backtested; see module
# docstring.
RANK_TAKE_PROBABILITY = {1: 0.55, 2: 0.32, 3: 0.18, 4: 0.10, 5: 0.06}
RANK_TAKE_PROBABILITY_FLOOR = 0.02

# A real, observable signal from the picks list itself (not an invented one): if most of the
# last few picks concentrated on one position, that position is "running" -- teams tend to
# follow a run rather than let a whole position group evaporate around them. Boosts the
# take-probability for players at that position specifically while a run is active.
RUN_LOOKBACK = 4
RUN_THRESHOLD = 3
RUN_TAKE_PROBABILITY_BOOST = 1.6
RUN_TAKE_PROBABILITY_CAP = 0.90


def generate_pick_order(round_1_order: list, total_rounds: int, draft_type: str = "snake") -> list:
    """The full roster_id sequence for every pick in the draft. Snake reverses the order on
    even rounds (standard fantasy draft convention); "linear" (auction-style leagues sometimes
    draft this way for supplemental rounds) repeats the same order every round."""
    order: list = []
    for round_num in range(1, total_rounds + 1):
        reverse = draft_type == "snake" and round_num % 2 == 0
        order.extend(reversed(round_1_order) if reverse else round_1_order)
    return order


def find_next_pick_index(pick_order: list, roster_id, after_index: int) -> Optional[int]:
    """The next index in pick_order, after after_index, where this roster picks again --
    None if they have no more picks left in the draft (e.g. near the very end)."""
    target = str(roster_id)
    for i in range(after_index + 1, len(pick_order)):
        if str(pick_order[i]) == target:
            return i
    return None


def intervening_roster_ids(pick_order: list, current_index: int, my_next_index: Optional[int]) -> list:
    """Every roster_id picking strictly between the current pick and the user's own next pick
    -- empty if there's no next pick to wait for (my_next_index is None) or nothing between
    them (back-to-back picks, e.g. the turn of a snake round)."""
    if my_next_index is None or my_next_index <= current_index:
        return []
    return list(pick_order[current_index + 1: my_next_index])


def detect_positional_run(picks: list[dict], players_db: dict[str, dict]) -> Optional[str]:
    """The fantasy position of the last RUN_LOOKBACK picks, if at least RUN_THRESHOLD of them
    landed at the same one -- a real, observable signal straight from the picks already made,
    not a modeled guess. None if there's no real run happening (or too few picks yet to tell)."""
    recent = picks[-RUN_LOOKBACK:]
    if len(recent) < RUN_THRESHOLD:
        return None
    positions = [player_position(players_db.get(str(p.get("player_id")), {})) for p in recent]
    positions = [p for p in positions if p]
    if not positions:
        return None
    top_position, count = Counter(positions).most_common(1)[0]
    return top_position if count >= RUN_THRESHOLD else None


def _take_probability(rank: int, is_run_position: bool) -> float:
    p = RANK_TAKE_PROBABILITY.get(rank, RANK_TAKE_PROBABILITY_FLOOR)
    if is_run_position:
        p = min(p * RUN_TAKE_PROBABILITY_BOOST, RUN_TAKE_PROBABILITY_CAP)
    return p


def _build_opponent_boards(
    merger: DataMerger, players_db: dict[str, dict], picks: list[dict], league: dict,
    roster_ids: list, *, mode: str = "auto", pool_scope: str = "all",
) -> dict:
    """One compute_draft_board call per UNIQUE roster_id, off the actual current pool -- see
    module docstring's PERFORMANCE section for why this replaced per-pick-position,
    per-candidate recomputation. Shared by every caller in this module within one analysis
    pass, never recomputed twice for the same roster."""
    boards = {}
    for roster_id in set(str(r) for r in roster_ids):
        board_list = compute_draft_board(
            merger, players_db, picks, my_roster_id=roster_id, league=league,
            mode=mode, pool_scope=pool_scope,
        )
        boards[roster_id] = {
            "by_id": {r["player_id"]: r for r in board_list},
            "rank_by_id": {r["player_id"]: i + 1 for i, r in enumerate(board_list)},
        }
    return boards


def estimate_survival(
    picks: list[dict],
    players_db: dict[str, dict],
    pick_order: list,
    current_index: int,
    my_roster_id,
    target_player_id: str,
    opponent_boards: dict,
) -> dict:
    """Survival probability for ONE specific player between now and the user's next pick, plus
    the per-team breakdown that produced it (never a single opaque number -- same transparency
    principle as every other score in this app). Takes already-computed opponent_boards (see
    _build_opponent_boards) rather than recomputing anything itself -- this function is now a
    cheap lookup + probability multiply, not a simulation.

    Returns {"survival_probability", "intervening_picks", "risk_by_team": [...]}. An empty
    risk_by_team with survival_probability=1.0 means either no one picks before the user's
    next turn (back-to-back picks) or the user has no more picks left to wait for."""
    my_next_index = find_next_pick_index(pick_order, my_roster_id, current_index)
    intervening = intervening_roster_ids(pick_order, current_index, my_next_index)
    if not intervening:
        return {"survival_probability": 1.0, "intervening_picks": 0, "risk_by_team": []}

    run_position = detect_positional_run(picks, players_db)
    info = players_db.get(str(target_player_id))
    target_position = player_position(info) if info else None

    survival = 1.0
    risk_by_team: list[dict] = []
    for roster_id in intervening:
        board = opponent_boards.get(str(roster_id))
        if not board:
            continue
        rank = board["rank_by_id"].get(str(target_player_id))
        if rank is None:
            continue  # not even in this team's usable-position pool -- no risk from them
        is_run = bool(run_position and target_position == run_position)
        p_take = _take_probability(rank, is_run)
        survival *= (1 - p_take)
        risk_by_team.append({
            "roster_id": roster_id, "rank_on_their_board": rank,
            "take_probability": round(p_take, 3), "run_boosted": is_run,
        })

    return {
        "survival_probability": round(survival, 3),
        "intervening_picks": len(intervening),
        "risk_by_team": risk_by_team,
    }


def pick_analysis(
    merger: DataMerger,
    players_db: dict[str, dict],
    picks: list[dict],
    pick_order: list,
    current_index: int,
    my_roster_id,
    league: dict,
    candidate_player_ids: list[str],
    *,
    mode: str = "auto",
    pool_scope: str = "all",
) -> list[dict]:
    """The actual "should I take him now" answer for a shortlist of candidates (typically the
    top few from draft_room.compute_draft_board) -- universal value plus the three strategic
    numbers from this module's docstring: survival_probability, opportunity_cost (expected
    value lost if he doesn't survive to the user's next pick), and denial_value (the best
    value an intervening opponent would get from him, weighted by how likely they actually
    were to take him -- what THIS pick prevents someone else from getting). Sorted by
    opportunity_cost descending: the highest number is the one where waiting costs the most,
    which is the actual "why take him now" case, not just "who's ranked highest."

    Every opponent board needed is computed exactly once (see _build_opponent_boards) and
    shared across every candidate here, not recomputed per candidate -- see module docstring's
    PERFORMANCE section for the real slowdown this replaced."""
    my_board = {r["player_id"]: r for r in compute_draft_board(
        merger, players_db, picks, my_roster_id=my_roster_id, league=league, mode=mode, pool_scope=pool_scope,
    )}
    my_next_index = find_next_pick_index(pick_order, my_roster_id, current_index)
    intervening = intervening_roster_ids(pick_order, current_index, my_next_index)
    opponent_boards = _build_opponent_boards(
        merger, players_db, picks, league, intervening, mode=mode, pool_scope=pool_scope,
    )

    results = []
    for player_id in candidate_player_ids:
        my_row = my_board.get(str(player_id))
        if my_row is None:
            continue
        survival = estimate_survival(
            picks, players_db, pick_order, current_index, my_roster_id, player_id, opponent_boards,
        )
        universal_value = my_row["final_score"]
        opportunity_cost = round(universal_value * (1 - survival["survival_probability"]), 2)

        denial_value = 0.0
        denial_team = None
        for risk in survival["risk_by_team"]:
            opp_board = opponent_boards.get(str(risk["roster_id"]), {})
            opp_row = opp_board.get("by_id", {}).get(str(player_id))
            if opp_row is None:
                continue
            weighted = opp_row["final_score"] * risk["take_probability"]
            if weighted > denial_value:
                denial_value = weighted
                denial_team = risk["roster_id"]

        results.append({
            "player_id": player_id,
            "name": my_row.get("name"),
            "position": my_row.get("position"),
            "universal_value": universal_value,
            "survival_probability": survival["survival_probability"],
            "intervening_picks": survival["intervening_picks"],
            "opportunity_cost": opportunity_cost,
            "denial_value": round(denial_value, 2),
            "denial_team": denial_team,
        })
    results.sort(key=lambda r: r["opportunity_cost"], reverse=True)
    return results
