"""
Deterministic synthesis layer for "Debate My Pick" -- turns draft_room.py's board and
draft_strategy.py's survival/opportunity-cost/denial analysis into ONE frozen, fully
decomposed snapshot for the LLM debate layer (pick_debate.py) to reason over. Nothing in this
module asks an LLM anything; it exists specifically so the debate layer downstream never has
to compute or guess a single number -- see pick_debate.py's own module docstring for why that
boundary is a hard architectural requirement, not a style preference.

Three real signals this module adds that didn't exist anywhere in the engine before:

  * positional_cliff -- whether a real, computable bpa gap sits between this player and the
    next-best REMAINING player at his position, big enough that waiting risks a genuine tier
    drop rather than "a slightly worse player." Same gap-detection principle draft_room.py's
    own _scale_vor_to_bpa already relies on (comparing a real gap's SIZE, never a percentile
    rank) -- applied one level down, comparing this player's bpa to the very next player at his
    position against how big gaps typically run in that position's own remaining pool.

  * expected_value_of_waiting -- survival_probability x universal_value: the flip side of
    draft_strategy.py's own opportunity_cost (team_acquisition_value x (1 -
    survival_probability)). Exposed directly, in the same units as universal_value, so "what do
    I realistically keep if I wait" is a real, already-computed number the debate can point to
    rather than something a model has to derive on the fly.

  * position_run_detected -- whether this candidate's own position is the one currently
    "running" (draft_strategy.detect_positional_run's own real, observable signal from recent
    picks), computed once per snapshot and attached per candidate rather than left for the LLM
    debate layer to notice or re-derive on its own.

narrow_candidates does the field-narrowing a live debate actually needs: never hand an LLM the
full 100+ player board -- only the top few genuinely live candidates (plus anything the user
has specifically flagged), so the debate argues about the decision, not about rediscovering
the whole remaining pool.

build_snapshot assembles all of the above into one frozen PickSnapshot (a real frozen
dataclass, not a mutable dict a later step could quietly edit), pulling universal_value/
need_bonus/eligibility_bonus straight from draft_room's own board rows and survival_
probability/opportunity_cost/denial_value from draft_strategy.pick_analysis -- each module
stays responsible for the numbers it already owns; this one only merges and packages them.

diff_snapshots computes the literal audit trail the user asked for: given a previous and a
current snapshot, the structured, per-component delta for every candidate present in both --
not prose describing what changed, real numbers per term (universal_value, need_bonus,
eligibility_bonus, survival_probability, opportunity_cost, denial_value, rank) so a UI or an
LLM can answer "why did this guy move from 8th to 3rd" by pointing at exactly which terms moved
and by how much.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import draft_room as dr
import draft_strategy as ds
from data_merger import DataMerger

DEFAULT_NARROW_COUNT = 5

# How much bigger this player's own gap to the next-best remaining player at his position has
# to be than that position's own TYPICAL adjacent gap (median, robust to one already-huge
# outlier skewing a mean) before it counts as a real cliff -- HIGH/MEDIUM/LOW, never a bare
# number the rest of this app would have to interpret itself. Principled starting points, not
# empirically backtested -- same honesty this app applies to every other unproven constant
# (see draft_room.py's and draft_strategy.py's own docstrings on this exact point).
CLIFF_HIGH_RATIO = 2.5
CLIFF_MEDIUM_RATIO = 1.5

# A position needs at least this many players still on the board for "typical gap" to mean
# anything -- below it, there's no real distribution to compare against.
CLIFF_MIN_POOL_SIZE = 3


def _find_row(board: list[dict], player_id) -> Optional[dict]:
    target = str(player_id)
    return next((r for r in board if str(r["player_id"]) == target), None)


def detect_positional_cliff(board: list[dict], player_id) -> Optional[dict]:
    """{"tier": "HIGH"/"MEDIUM"/"LOW", "gap", "typical_gap"} -- how much of a real bpa drop-off
    sits between this player and the next-best remaining player at his own position, relative
    to how big gaps ordinarily run in that position's remaining pool. None when this player
    isn't on the board, is the last one left at his position (no next player to fall off to --
    "cliff" isn't a meaningful question there), or the position has fewer than
    CLIFF_MIN_POOL_SIZE players remaining (not enough of a distribution to call anything
    "typical")."""
    row = _find_row(board, player_id)
    if row is None:
        return None
    same_position = sorted(
        (r for r in board if r["position"] == row["position"]), key=lambda r: r["bpa"], reverse=True,
    )
    if len(same_position) < CLIFF_MIN_POOL_SIZE:
        return None
    idx = next((i for i, r in enumerate(same_position) if str(r["player_id"]) == str(player_id)), None)
    if idx is None or idx == len(same_position) - 1:
        return None

    gaps = [same_position[i]["bpa"] - same_position[i + 1]["bpa"] for i in range(len(same_position) - 1)]
    this_gap = gaps[idx]
    other_gaps = sorted(g for i, g in enumerate(gaps) if i != idx and g > 0)
    if not other_gaps:
        return {"tier": "HIGH" if this_gap > 0 else "LOW", "gap": round(this_gap, 2), "typical_gap": 0.0}

    typical_gap = other_gaps[len(other_gaps) // 2]  # median
    ratio = this_gap / typical_gap if typical_gap > 0 else float("inf") if this_gap > 0 else 0.0
    tier = "HIGH" if ratio >= CLIFF_HIGH_RATIO else "MEDIUM" if ratio >= CLIFF_MEDIUM_RATIO else "LOW"
    return {"tier": tier, "gap": round(this_gap, 2), "typical_gap": round(typical_gap, 2)}


def expected_value_of_waiting(universal_value: float, survival_probability: Optional[float]) -> Optional[float]:
    """The flip side of draft_strategy.py's opportunity_cost -- what you'd expect to walk away
    with, in universal_value's own units, if you pass on this player now and gamble on him
    surviving to your next pick. None when survival_probability itself isn't known (no
    intervening-pick context available), same "don't fabricate a number" posture as everywhere
    else in this app rather than silently assuming certainty."""
    if survival_probability is None:
        return None
    return round(universal_value * survival_probability, 2)


def narrow_candidates(
    board: list[dict], top_n: int = DEFAULT_NARROW_COUNT, user_selected_player_id: Optional[str] = None,
) -> list[dict]:
    """The top top_n rows by team_acquisition_value (final_score, draft_room's own ranking),
    plus the user's own explicitly-flagged player if there is one and it isn't already in that
    top slice -- so a live debate is never blind to a player the user is specifically
    considering (a dynasty stash, a personal favorite, a punt pick) just because the
    deterministic board doesn't currently rank him near the top."""
    ranked = sorted(board, key=lambda r: r["final_score"], reverse=True)
    candidates = list(ranked[:top_n])
    if user_selected_player_id is not None:
        already_in = any(str(r["player_id"]) == str(user_selected_player_id) for r in candidates)
        if not already_in:
            extra = _find_row(board, user_selected_player_id)
            if extra is not None:
                candidates.append(extra)
    return candidates


@dataclass(frozen=True)
class CandidateSnapshot:
    """One candidate's full decomposition, frozen at the moment the snapshot was built -- every
    field here is a real number this app already computed, never something the LLM debate
    layer is allowed to substitute its own guess for (see pick_debate.py)."""
    player_id: str
    name: str
    position: str
    team: Optional[str]
    bpa: float
    bpa_source: str
    confidence: float
    universal_value: float
    need_bonus: float
    eligibility_bonus: float
    team_acquisition_value: float
    survival_probability: Optional[float]
    intervening_picks: Optional[int]
    opportunity_cost: Optional[float]
    expected_value_of_waiting: Optional[float]
    denial_value: Optional[float]
    denial_team: Optional[str]
    positional_cliff: Optional[dict]
    position_run_detected: bool


@dataclass(frozen=True)
class PickSnapshot:
    """The full frozen state a single "Debate My Pick" run reasons over. candidates is a tuple,
    not a list -- genuine immutability, not just a convention, since this snapshot is meant to
    be handed to an LLM debate and then diffed against later, and a caller quietly mutating it
    mid-debate would silently break both."""
    pick_label: str
    round: int
    my_roster_id: str
    candidates: tuple
    user_selected_player_id: Optional[str] = None


def build_snapshot(
    merger: DataMerger,
    players_db: dict[str, dict],
    picks: list[dict],
    pick_order: list,
    current_index: int,
    my_roster_id,
    league: dict,
    *,
    pick_label: str,
    mode: str = "balanced",
    pool_scope: str = "all",
    top_n: int = DEFAULT_NARROW_COUNT,
    user_selected_player_id: Optional[str] = None,
) -> PickSnapshot:
    """Build one frozen PickSnapshot: compute the real board, narrow to the live candidates,
    layer on survival/opportunity-cost/denial (draft_strategy.pick_analysis) and positional
    cliff (this module), and package it all as one immutable object. mode defaults to
    "balanced" (not draft_room's own "auto") -- upside-mode scoring drops universal_value/
    need_bonus/eligibility_bonus entirely (see draft_room.compute_draft_board's own docstring),
    and this snapshot's whole shape depends on those fields existing."""
    board = dr.compute_draft_board(
        merger, players_db, picks, my_roster_id=my_roster_id, league=league, mode=mode, pool_scope=pool_scope,
    )
    narrowed = narrow_candidates(board, top_n=top_n, user_selected_player_id=user_selected_player_id)
    candidate_ids = [row["player_id"] for row in narrowed]
    # A real, observable signal straight from the picks already made (see
    # draft_strategy.detect_positional_run's own docstring) -- computed once and shared across
    # every candidate here, not re-derived or guessed at per candidate.
    run_position = ds.detect_positional_run(picks, players_db)

    analysis_by_id: dict[str, dict] = {}
    if candidate_ids:
        analysis = ds.pick_analysis(
            merger, players_db, picks, pick_order, current_index=current_index, my_roster_id=my_roster_id,
            league=league, candidate_player_ids=candidate_ids, mode=mode, pool_scope=pool_scope,
        )
        analysis_by_id = {str(a["player_id"]): a for a in analysis}

    candidates = []
    for row in narrowed:
        pid = str(row["player_id"])
        a = analysis_by_id.get(pid, {})
        survival = a.get("survival_probability")
        universal_value = row["universal_value"]
        candidates.append(CandidateSnapshot(
            player_id=pid, name=row["name"], position=row["position"], team=row.get("team"),
            bpa=row["bpa"], bpa_source=row["bpa_source"], confidence=row["confidence"],
            universal_value=universal_value, need_bonus=row.get("need_bonus", 0.0),
            eligibility_bonus=row.get("eligibility_bonus", 0.0), team_acquisition_value=row["final_score"],
            survival_probability=survival, intervening_picks=a.get("intervening_picks"),
            opportunity_cost=a.get("opportunity_cost"),
            expected_value_of_waiting=expected_value_of_waiting(universal_value, survival),
            denial_value=a.get("denial_value"), denial_team=a.get("denial_team"),
            positional_cliff=detect_positional_cliff(board, pid),
            position_run_detected=(run_position is not None and row["position"] == run_position),
        ))

    return PickSnapshot(
        pick_label=pick_label,
        round=(max((p.get("round") or 1) for p in picks) if picks else 1),
        my_roster_id=str(my_roster_id),
        candidates=tuple(candidates),
        user_selected_player_id=(str(user_selected_player_id) if user_selected_player_id is not None else None),
    )


_DIFF_FIELDS = (
    "universal_value", "need_bonus", "eligibility_bonus", "team_acquisition_value",
    "survival_probability", "opportunity_cost", "expected_value_of_waiting", "denial_value",
)


def diff_snapshots(previous: PickSnapshot, current: PickSnapshot) -> list[dict]:
    """The literal audit trail: for every candidate present in BOTH snapshots, the real,
    structured per-component delta -- not a prose description of what changed. rank_delta is
    each candidate's position in team_acquisition_value order within each snapshot's own
    candidate list (1 = top candidate); a player moving from rank 8 to rank 3 shows up here as
    rank_delta=-5 alongside exactly which underlying terms moved and by how much, the concrete
    answer to "why did this guy move" rather than a re-derived guess.

    A candidate only in one of the two snapshots (newly appeared, or fell out of the narrowed
    top_n) is reported with entered=True/False rather than silently dropped -- that's real,
    reportable information too (see pick_debate.py's use of this for "what changed" framing)."""
    prev_by_id = {c.player_id: c for c in previous.candidates}
    prev_rank = {c.player_id: i + 1 for i, c in enumerate(previous.candidates)}
    curr_by_id = {c.player_id: c for c in current.candidates}
    curr_rank = {c.player_id: i + 1 for i, c in enumerate(current.candidates)}

    diffs = []
    for player_id in set(prev_by_id) | set(curr_by_id):
        prev_c = prev_by_id.get(player_id)
        curr_c = curr_by_id.get(player_id)
        if prev_c is None:
            diffs.append({"player_id": player_id, "name": curr_c.name, "entered": True, "rank": curr_rank[player_id]})
            continue
        if curr_c is None:
            diffs.append({"player_id": player_id, "name": prev_c.name, "entered": False, "rank": prev_rank[player_id]})
            continue
        deltas = {}
        for attr in _DIFF_FIELDS:
            prev_val, curr_val = getattr(prev_c, attr), getattr(curr_c, attr)
            if prev_val is None or curr_val is None:
                continue
            delta = round(curr_val - prev_val, 2)
            if delta != 0:
                deltas[attr] = delta
        rank_delta = curr_rank[player_id] - prev_rank[player_id]
        if deltas or rank_delta:
            diffs.append({
                "player_id": player_id, "name": curr_c.name, "entered": None,
                "rank_delta": rank_delta, "deltas": deltas,
            })
    return diffs
