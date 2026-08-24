"""Phase 1 of the post-baseline-12chair-v1 validation work: isolated state-node counterfactual
comparison. This module is measurement, never judgment -- it records what the production
engine, pure BPA, and (where real data exists) market ADP would each have done at an identical,
already-happened board/roster state. It computes no verdict about whether any of them was
"right."

For every pick in an already-completed DraftTrajectory, this reconstructs the exact
picks-so-far state immediately before that pick and re-evaluates that identical state through:

  - the production contextual engine's own choice -- read directly off the trajectory, never
    recomputed (the engine's decision at that node already happened and is not re-derived here).
  - pure Universal Value / BPA -- argmax(universal_value) over compute_draft_board's FULL
    undrafted board, not narrow_candidates' narrowed shortlist. The narrowed list's "best at
    position" inclusion is TAV-based (see narrow_candidates' own docstring), not UV-based, so
    the true UV-argmax across the whole pool is not guaranteed to appear in a stored
    PickRecord's snapshot at all -- this recomputes the full board specifically to get it right.
  - real market consensus (KeepTradeCut) via pick_synthesis._consensus_lookup / consensus_reach
    -- the same, already-shipped lookup the live engine itself uses for reach_label, not a new
    ADP model. That lookup is empty for a non-superflex league BY DESIGN (its own docstring:
    "this app's committed baseline only carries KTC's superflex-format export, and using
    superflex-inflated QB consensus for a 1QB league would silently misrepresent that league's
    real market"). This module surfaces that as an explicit, honest unavailability
    (adp_available=False) rather than inventing a substitute ranking for 1QB nodes.

Every board recomputation is read-only: it builds its own local picks-so-far list and never
mutates the source DraftTrajectory, the merger, or players_db. Re-running this module against
the same trajectory twice must produce identical NodeComparisons -- see
test_draft_counterfactual.py's determinism tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import draft_room as dr
import pick_synthesis as ps
from data_merger import DataMerger
from draft_simulation import DraftTrajectory

# Deviation-support classification (Phase 2's "does contextual TAV support the engine choice"
# bucket): reuses the engine's OWN already-computed necessity label and near-tie flag -- never a
# new threshold invented for this harness. A deviation is "supported" when the engine's own
# signal vocabulary already says this pick was urgent (MUST TAKE / STRONG ACTION) or that BPA
# and the engine's choice were close enough to be a real toss-up (near_tie_with_leader) -- i.e.
# the SAME evidence a human reading the live Draft Room would have seen to justify the pick.
_SUPPORTED_NECESSITY_LABELS = ("MUST TAKE", "STRONG ACTION")


@dataclass(frozen=True)
class NodeComparison:
    pick_no: int
    pick_label: str
    roster_id: str

    engine_player_id: str
    engine_player_name: str
    engine_position: str
    engine_uv: float
    engine_tav: float
    engine_necessity: str
    engine_near_tie: bool

    bpa_player_id: str
    bpa_player_name: str
    bpa_position: str
    bpa_uv: float
    bpa_tav: float  # the engine's OWN team_acquisition_value assigned to the BPA player, same state

    adp_available: bool
    adp_unavailable_reason: Optional[str]
    adp_player_id: Optional[str]
    adp_player_name: Optional[str]
    adp_consensus_rank: Optional[int]
    adp_tav: Optional[float]

    regret_vs_bpa: float  # engine_tav - bpa_tav; >= 0 by construction (engine always TAV-argmax)
    regret_vs_adp: Optional[float]  # engine_tav - adp_tav; sign is NOT constrained

    equals_bpa: bool
    equals_adp: Optional[bool]  # None when adp_available is False
    deviation_supported: Optional[bool]  # None when equals_bpa (nothing to classify)


def _full_board(merger: DataMerger, players_db: dict, picks_so_far: list[dict], roster_id: str, league: dict, mode: str, pool_scope: str) -> list[dict]:
    return dr.compute_draft_board(merger, players_db, picks_so_far, my_roster_id=roster_id, league=league, mode=mode, pool_scope=pool_scope)


def bpa_row(board: list[dict]) -> dict:
    """Pure argmax(universal_value) over a full board -- extracted so this specific property
    (BPA is a UV-argmax, never a TAV-argmax) is directly unit-testable against a small
    synthetic board, not dependent on a real draft happening to produce a case where they
    diverge."""
    return max(board, key=lambda r: r["universal_value"])


def _adp_pick(board: list[dict], merger: DataMerger, is_superflex: bool, current_overall_pick: int) -> tuple[Optional[dict], Optional[str]]:
    """(row, unavailable_reason). row is the board row with the best (lowest) real KTC
    consensus rank -- None with a reason string when no consensus data applies to this node."""
    if not is_superflex:
        return None, "No real ADP/consensus data is loaded for a 1QB league (KTC consensus is only carried for superflex, by design -- see pick_synthesis._consensus_lookup)."
    consensus_by_key = ps._consensus_lookup(merger, is_superflex)
    if not consensus_by_key:
        return None, "Superflex league, but no KTC consensus data is loaded in this merger instance."
    best_row, best_rank = None, None
    for row in board:
        reach = ps.consensus_reach(row["name"], current_overall_pick, consensus_by_key)
        if reach is None:
            continue
        rank = reach["consensus_rank"]
        if best_rank is None or rank < best_rank:
            best_rank, best_row = rank, {**row, "_consensus_rank": rank}
    if best_row is None:
        return None, "No undrafted player at this node matched any KTC consensus entry."
    return best_row, None


def compare_trajectory(
    merger: DataMerger, players_db: dict, league: dict, trajectory: DraftTrajectory,
) -> list[NodeComparison]:
    """One NodeComparison per pick already recorded in `trajectory`. Reconstructs picks-so-far
    from the trajectory's own pick sequence -- never replays or re-simulates a decision, and
    never mutates `trajectory`, `merger`, `players_db`, or `league`."""
    is_superflex = "SUPER_FLEX" in (league.get("roster_positions") or [])
    mode = trajectory.config.get("mode", "auto")
    pool_scope = trajectory.config.get("pool_scope", "all")

    picks_so_far: list[dict] = []
    results: list[NodeComparison] = []

    for rec in trajectory.picks:
        engine_candidates = rec.snapshot["candidates"]
        engine_cand = next(c for c in engine_candidates if c["id"] == rec.chosen_player_id)

        board = _full_board(merger, players_db, picks_so_far, rec.roster_id, league, mode, pool_scope)
        if not board:
            picks_so_far.append({"pick_no": rec.pick_no, "round": rec.round, "roster_id": rec.roster_id, "player_id": rec.chosen_player_id})
            continue

        bpa_row_ = bpa_row(board)
        current_overall_pick = rec.pick_no
        adp_row, adp_reason = _adp_pick(board, merger, is_superflex, current_overall_pick)

        engine_tav = engine_cand["tav"]
        bpa_tav = float(bpa_row_["final_score"])
        adp_tav = float(adp_row["final_score"]) if adp_row is not None else None

        equals_bpa = str(bpa_row_["player_id"]) == rec.chosen_player_id
        equals_adp = (str(adp_row["player_id"]) == rec.chosen_player_id) if adp_row is not None else None

        deviation_supported = None
        if not equals_bpa:
            deviation_supported = (
                engine_cand["necessity"] in _SUPPORTED_NECESSITY_LABELS
                or _near_tie(engine_candidates, rec.chosen_player_id)
            )

        results.append(NodeComparison(
            pick_no=rec.pick_no, pick_label=rec.pick_label, roster_id=rec.roster_id,
            engine_player_id=rec.chosen_player_id, engine_player_name=engine_cand["name"],
            engine_position=engine_cand["pos"], engine_uv=engine_cand["uv"], engine_tav=engine_tav,
            engine_necessity=engine_cand["necessity"], engine_near_tie=_near_tie(engine_candidates, rec.chosen_player_id),
            bpa_player_id=str(bpa_row_["player_id"]), bpa_player_name=bpa_row_["name"],
            bpa_position=bpa_row_["position"], bpa_uv=float(bpa_row_["universal_value"]), bpa_tav=bpa_tav,
            adp_available=adp_row is not None, adp_unavailable_reason=adp_reason,
            adp_player_id=str(adp_row["player_id"]) if adp_row is not None else None,
            adp_player_name=adp_row["name"] if adp_row is not None else None,
            adp_consensus_rank=adp_row["_consensus_rank"] if adp_row is not None else None,
            adp_tav=adp_tav,
            regret_vs_bpa=round(engine_tav - bpa_tav, 3),
            regret_vs_adp=(round(engine_tav - adp_tav, 3) if adp_tav is not None else None),
            equals_bpa=equals_bpa, equals_adp=equals_adp, deviation_supported=deviation_supported,
        ))
        picks_so_far.append({"pick_no": rec.pick_no, "round": rec.round, "roster_id": rec.roster_id, "player_id": rec.chosen_player_id})

    return results


def _near_tie(candidates: list[dict], chosen_id: str) -> bool:
    """Reads the engine's OWN near_tie_with_leader signal off the serialized candidate --
    serialize_candidate exposes it as the string "tie" inside the "forces" list (see
    draft_board_ui._forces), the same rendered signal a human looking at the live board would
    see, not a threshold re-derived here."""
    cand = next((c for c in candidates if c["id"] == chosen_id), None)
    if cand is None:
        return False
    return "tie" in (cand.get("forces") or [])
