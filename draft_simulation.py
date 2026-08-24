"""Multi-chair draft simulation -- an engine-validation harness, not a product feature.

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


def simulate_full_draft(
    merger: DataMerger, players_db: dict[str, dict], league: dict, pick_order: list,
    *, mode: str = "auto", pool_scope: str = "all", config_label: str = "",
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
        )
        if not snap.candidates:
            break
        chosen = snap.candidates[0]
        picks.append({"pick_no": idx + 1, "round": round_no, "roster_id": roster_id, "player_id": chosen.player_id})
        records.append(PickRecord(
            pick_no=idx + 1, round=round_no, roster_id=roster_id, pick_label=pick_label,
            chosen_player_id=chosen.player_id, decision_regime=snap.decision_regime,
            snapshot=draft_board_ui.serialize_snapshot(snap, pick_header=pick_label, state_tags=[]),
        ))

    return DraftTrajectory(
        config={"pick_order": [str(r) for r in pick_order], "mode": mode, "pool_scope": pool_scope, "label": config_label},
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
        )
        for cfg in configs
    ]
