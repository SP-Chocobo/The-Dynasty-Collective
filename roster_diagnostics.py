"""Phase 4 of the post-baseline-12chair-v1 validation work: decomposable roster-quality
diagnostics for a completed DraftTrajectory.

Never a single opaque "Team Power Score" -- every field on TeamDiagnostics is independently
inspectable and traces to a named, already-shipped mechanism, never a new valuation invented
for this harness. Same governing principle as League's own hard contract: strength is an entry
point, never a conclusion.

What's covered, and what it reuses:
  - accumulated_value: a plain sum of universal_value across a team's own picks -- no
    computation at all, just addition.
  - starting_lineup_value / bench_surplus_value: lineup_optimizer.optimize_lineup, the
    already-shipped exact-assignment solver (see that module's own docstring) -- run once per
    team against its own final roster, never a new lineup heuristic.
  - positional_counts / thin_positions: depth_ratings.depth_label, the exact shared
    Strong/Average/Weak/None judgment Trade Calculator, League's Depth Map, and Matchup's
    readiness strip already use -- never a second opinion for this harness.
  - replacement_level_surplus: draft_room.replacement_levels, run against a freshly-scored
    compute_draft_board pool reflecting the fully-drafted state -- the same dynamic,
    remaining-demand replacement math the live engine itself uses, not a new baseline.
  - structural_holes: player_universe.league_usable_positions, compared against what a team
    actually rostered -- a set difference, nothing computed.

What's explicitly NOT supported here, reported rather than approximated: age/trajectory
composition. This harness's own synthetic players_db (built from Draft Sharks projections
reconstructed into a Sleeper-like shape for simulation purposes) carries no age or experience
field at all -- the real app's live players_db (from Sleeper's /players/nfl) does, but that
data was never threaded into this harness's player pool. Reported as a data-availability gap,
not filled with an invented estimate.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Optional

import pandas as pd

import depth_ratings
import draft_room as dr
import lineup_optimizer
from data_merger import DataMerger
from draft_simulation import DraftTrajectory
from player_universe import league_usable_positions

AGE_TRAJECTORY_UNAVAILABLE_REASON = (
    "This harness's synthetic players_db (reconstructed from Draft Sharks projections for "
    "simulation purposes) carries no age/experience field -- the real app's live Sleeper "
    "players_db does, but that data was never threaded into this simulation harness. Not "
    "approximated; reported as a data-availability gap."
)


@dataclass(frozen=True)
class TeamDiagnostics:
    roster_id: str
    accumulated_value: float
    starting_lineup_value: float
    bench_surplus_value: float
    replacement_level_surplus: float
    positional_counts: dict
    thin_positions: tuple
    structural_holes: tuple


def _chosen_candidate(rec) -> dict:
    return next(c for c in rec.snapshot["candidates"] if c["id"] == rec.chosen_player_id)


def _all_picks_as_dicts(trajectory: DraftTrajectory) -> list[dict]:
    return [
        {"pick_no": rec.pick_no, "round": rec.round, "roster_id": rec.roster_id, "player_id": rec.chosen_player_id}
        for rec in trajectory.picks
    ]


def compute_team_diagnostics(
    merger: DataMerger, players_db: dict, league: dict, trajectory: DraftTrajectory,
) -> dict[str, TeamDiagnostics]:
    """One TeamDiagnostics per roster_id that appears in `trajectory`. Read-only: never
    mutates merger, players_db, league, or trajectory."""
    roster_positions = league.get("roster_positions") or []
    usable_positions = league_usable_positions(roster_positions)
    num_teams = len({rec.roster_id for rec in trajectory.picks})

    by_team: dict[str, list[dict]] = defaultdict(list)
    drafted_counts: Counter = Counter()
    for rec in trajectory.picks:
        cand = _chosen_candidate(rec)
        by_team[rec.roster_id].append({"id": cand["id"], "name": cand["name"], "position": cand["pos"], "uv": cand["uv"]})
        drafted_counts[cand["pos"]] += 1

    # replacement_levels needs a scored DataFrame carrying "universal_value" -- that column
    # only exists after compute_draft_board's own scoring pass, not on build_available_pool's
    # raw (pre-score) pool. universal_value is deliberately team-agnostic (only need_bonus/
    # eligibility_bonus vary by roster), so which roster_id this call is scored "for" doesn't
    # change the remaining pool's own universal_value column -- any valid roster_id works.
    mode = trajectory.config.get("mode", "auto")
    pool_scope = trajectory.config.get("pool_scope", "all")
    any_roster_id = trajectory.picks[0].roster_id
    scored_board = dr.compute_draft_board(
        merger, players_db, _all_picks_as_dicts(trajectory), my_roster_id=any_roster_id,
        league=league, mode=mode, pool_scope=pool_scope,
    )
    scored_pool = pd.DataFrame(scored_board)
    repl_levels = (
        dr.replacement_levels(scored_pool, "universal_value", roster_positions, num_teams, drafted_counts=dict(drafted_counts))
        if not scored_pool.empty else {}
    )

    # Same shape positional_depth (app.py) already builds -- team -> position -> {count, value}
    # -- so depth_ratings.depth_label is called with the identical peer-comparison shape every
    # other surface already uses.
    depth: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(lambda: {"count": 0, "value": 0.0}))
    for rid, players in by_team.items():
        for p in players:
            cell = depth[rid][p["position"]]
            cell["count"] += 1
            cell["value"] += p["uv"]

    slots = lineup_optimizer.slots_from_roster_positions(roster_positions)

    results: dict[str, TeamDiagnostics] = {}
    for rid, players in by_team.items():
        opt_players = [{"id": p["id"], "value": p["uv"], "eligible": {p["position"]}} for p in players]
        lineup = lineup_optimizer.optimize_lineup(opt_players, slots)
        accumulated_value = round(sum(p["uv"] for p in players), 2)
        starting_lineup_value = lineup["total_value"]
        bench_surplus_value = round(accumulated_value - starting_lineup_value, 2)

        positional_counts = dict(Counter(p["position"] for p in players))
        thin_positions = []
        for pos in positional_counts:
            cell = depth[rid][pos]
            peer_cells = [depth[other][pos] for other in depth if pos in depth[other]]
            label = depth_ratings.depth_label(cell, peer_cells)
            if label in ("Weak", "None — no rostered players here"):
                thin_positions.append(pos)

        structural_holes = tuple(sorted(usable_positions - set(positional_counts)))
        replacement_level_surplus = round(
            sum(p["uv"] - repl_levels.get(p["position"], 0.0) for p in players), 2,
        )

        results[rid] = TeamDiagnostics(
            roster_id=rid, accumulated_value=accumulated_value,
            starting_lineup_value=starting_lineup_value, bench_surplus_value=bench_surplus_value,
            replacement_level_surplus=replacement_level_surplus,
            positional_counts=positional_counts, thin_positions=tuple(sorted(thin_positions)),
            structural_holes=structural_holes,
        )
    return results
