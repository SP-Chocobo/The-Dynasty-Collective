"""Multi-chair draft simulation -- a CDME (Contextual Decision Matrix Engine) validation
harness, not a product feature. See README.md's "The Draft Engine" section for CDME's own
canonical definition; this module and the rest of the run_*_validation.py / draft_counterfactual.py
/ roster_diagnostics.py / option_set_analysis.py harness all read CDME's outputs to measure its
behavior -- none of them are part of CDME itself, and none modify its production decision logic
on their own authority.

Every chair uses the exact production decision path a real Draft Room pick already goes
through: pick_synthesis.build_snapshot, the same call live Draft Room makes for a human's own
turn. This module never invents a simulation-specific valuation or selection rule -- the chosen
player at every pick is snap.candidates[0], the identical "top team_acquisition_value board
pick" contract draft_room.simulate_opponent_picks already uses for auto-drafted teams.

Why mode="auto" specifically: build_snapshot's own default is mode="balanced" (what a human
sees on their own live turn, since app.py's Draft Room never passes mode= explicitly either).
compute_draft_board's own default -- the one simulate_opponent_picks implicitly relies on for
EVERY auto-drafted pick -- is mode="auto". These are two different defaults that nobody has
ever reconciled; it's a real, pre-existing inconsistency between "what a human sees for their
own turn" and "how an auto-picked chair already behaves elsewhere in this app," not something
introduced here. Since every chair in this module is auto-picked (there is no human turn),
mode="auto" is the correct match to the EXISTING auto-draft contract -- not a new choice.

Determinism is a tested contract: identical inputs (league, pick_order, mode, pool_scope)
produce an identical trajectory, always -- see test_draft_simulation.py's determinism tests.
Trials vary by changing real inputs (draft slot/pick_order, league format via
draft_room.build_mock_league) -- never by injecting randomness into an otherwise-deterministic
engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import draft_board_ui
import draft_room as dr
import pick_synthesis
from data_merger import DataMerger


@dataclass(frozen=True)
class PickRecord:
    """One pick's full retained decision context. `snapshot` is the entire serialized board
    (draft_board_ui.serialize_snapshot's own shape -- the same translation layer every rendered
    board already uses) at the moment this pick was made, not just the player who was taken --
    so "why did this chair take this player, over what alternatives" is answerable later by
    reading this record, never by re-deriving it from the final rosters alone."""
    pick_no: int
    round: int
    roster_id: str
    pick_label: str
    chosen_player_id: str
    decision_regime: str
    snapshot: dict
    # #138. Read off the chosen candidate, not re-derived: the two qualifiers that say what
    # KIND of number won this pick. chosen_replacement_basis distinguishes a price resting on
    # live starter demand from one resting on the pre-draft anchor; chosen_growth_signal is
    # the trajectory term that decides late upside-mode picks (measured: it changes the argmax
    # by round 15). Both default so trajectories recorded before this field still construct.
    #
    # These are DECOMPOSITIONS of a decision this record already stores, which is exactly what
    # makes them worth storing: without them the record answers "who was taken" but not "on
    # what kind of evidence", and #150 reads these records to judge whether a draft is
    # defensible rather than merely deterministic.
    chosen_replacement_basis: Optional[str] = None
    chosen_growth_signal: Optional[float] = None


@dataclass(frozen=True)
class DraftTrajectory:
    """One complete simulated draft: every pick in order, each with its full retained decision
    context, plus the config that produced it -- so a trajectory is self-describing, and two
    trajectories built from identical configs can be diffed directly for the determinism
    contract."""
    config: dict
    picks: tuple[PickRecord, ...]

    def final_rosters(self) -> dict[str, list[str]]:
        """roster_id -> [player_id, ...] in acquisition order -- a plain derived read of
        self.picks, never separately-tracked state that could drift from it."""
        rosters: dict[str, list[str]] = {}
        for pick in self.picks:
            rosters.setdefault(pick.roster_id, []).append(pick.chosen_player_id)
        return rosters


def _picks_by_mode(mode: str, total_picks: int, num_teams: int) -> dict[str, int]:
    """How many picks of this trajectory each valuation actually produced (#222).

    Reported rather than assumed: mode="auto" flips at UPSIDE_MODE_DEFAULT_ROUND, which is a
    fixed ROUND INDEX, so the same setting buys a different FRACTION of every draft -- 26% of a
    19-round draft and 46% of a 26-round one. A reader of the artifact should not have to
    recompute that from a constant to know what they are comparing.
    """
    if mode == "upside":
        return {"balanced": 0, "upside": total_picks}
    if mode != "auto":
        return {"balanced": total_picks, "upside": 0}
    balanced = min(max((dr.UPSIDE_MODE_DEFAULT_ROUND - 1) * num_teams, 0), total_picks)
    return {"balanced": balanced, "upside": total_picks - balanced}


def simulate_full_draft(
    merger: DataMerger, players_db: dict[str, dict], league: dict, pick_order: list,
    *, mode: str = "auto", pool_scope: str = "all", config_label: str = "",
    sleeper_projections: Optional[dict[str, dict]] = None,
    sleeper_basis: str = dr.SLEEPER_BASIS_WEEKLY,
) -> DraftTrajectory:
    """Run one complete draft, every chair using the real production engine -- never a
    simulation-specific valuation or decision heuristic.

    pick_order: roster_id per overall pick slot (draft_strategy.generate_pick_order's own
    shape). This -- along with `league` -- is what should vary between trials (draft slot
    order, league format/settings); neither this function nor its caller should ever
    substitute a random seed for that. Reads merger/players_db/league only; never mutates
    them, and builds its own local `picks` list rather than touching any caller-owned state.

    Every pick calls pick_synthesis.build_snapshot for whoever is on the clock and takes
    candidates[0] -- see this module's docstring for why mode defaults to "auto" here rather
    than build_snapshot's own "balanced" default. Stops early (never raises) if a board ever
    comes up empty, mirroring draft_room.simulate_opponent_picks' own behavior for the same
    edge case -- a short mock with more rounds than rosterable players is a real, if unlikely,
    config."""
    picks: list[dict] = []
    records: list[PickRecord] = []
    num_teams = len(set(str(r) for r in pick_order))

    for idx in range(len(pick_order)):
        roster_id = str(pick_order[idx])
        round_no = idx // num_teams + 1
        pick_label = f"{round_no}.{(idx % num_teams) + 1:02d}"
        snap = pick_synthesis.build_snapshot(
            merger, players_db, picks, pick_order, idx, roster_id, league,
            pick_label=pick_label, mode=mode, pool_scope=pool_scope,
            # #204: production (app.py's Draft Room) passes BOTH of these, so a simulated
            # draft that omits them is not drafting from the production pricing path -- every
            # row comes back with sleeper_points/sleeper_basis/availability_basis all None,
            # and the scoring-aware path (#180/#192) plus the availability haircut (#191/#202)
            # are silently inert. Defaulted to None/WEEKLY so every existing caller keeps its
            # exact previous behaviour; the battery is what supplies them.
            sleeper_projections=sleeper_projections, sleeper_basis=sleeper_basis,
        )
        if not snap.candidates:
            break
        chosen = snap.candidates[0]
        picks.append({"pick_no": idx + 1, "round": round_no, "roster_id": roster_id, "player_id": chosen.player_id})
        records.append(PickRecord(
            pick_no=idx + 1, round=round_no, roster_id=roster_id, pick_label=pick_label,
            chosen_player_id=chosen.player_id, decision_regime=snap.decision_regime,
            snapshot=draft_board_ui.serialize_snapshot(snap, pick_header=pick_label, state_tags=[]),
            chosen_replacement_basis=chosen.replacement_basis,
            chosen_growth_signal=chosen.growth_signal,
        ))

    return DraftTrajectory(
        config={"pick_order": [str(r) for r in pick_order], "mode": mode, "pool_scope": pool_scope,
                "label": config_label,
                # WHICH PRICING PATH produced this trajectory, carried with it. Two trajectories
                # drafted off different point sources are not comparable, and without this the
                # difference is invisible in the record (#204).
                "sleeper_basis": (sleeper_basis if sleeper_projections else None),
                "priced_from": ("vendor+sleeper" if sleeper_projections else "vendor_only"),
                # WHICH VALUATION produced each pick, for the same reason priced_from exists
                # (#222). mode="auto" is not one valuation: compute_draft_board's upside branch
                # zeroes every team-specific term, so a trajectory can be half roster-aware and
                # half roster-blind with nothing in the record saying so. Measured on a 26-round
                # startup, that split is 168 balanced picks and 144 upside ones -- 46% of the
                # draft -- and two trajectories drafted under different splits are no more
                # comparable than two drafted off different point sources. Derived from the
                # rounds actually run, never from an assumed draft length.
                "upside_from_round": (dr.UPSIDE_MODE_DEFAULT_ROUND if mode == "auto"
                                      else (1 if mode == "upside" else None)),
                "picks_by_mode": _picks_by_mode(mode, len(pick_order), num_teams)},
        picks=tuple(records),
    )


def run_trials(
    merger: DataMerger, players_db: dict[str, dict], configs: list[dict],
) -> list[DraftTrajectory]:
    """Run one full draft per config. Each config: {"league": dict, "pick_order": list,
    optionally "mode"/"pool_scope"/"label"}. Configs are expected to vary real inputs (a
    different pick_order/draft slot, a different league via draft_room.build_mock_league) --
    this function has no randomness of its own to seed, and passing otherwise-identical
    configs must yield identical trajectories (see test_draft_simulation.py)."""
    return [
        simulate_full_draft(
            merger, players_db, cfg["league"], cfg["pick_order"],
            mode=cfg.get("mode", "auto"), pool_scope=cfg.get("pool_scope", "all"),
            config_label=cfg.get("label", ""),
            sleeper_projections=cfg.get("sleeper_projections"),
            sleeper_basis=cfg.get("sleeper_basis", dr.SLEEPER_BASIS_WEEKLY),
        )
        for cfg in configs
    ]
