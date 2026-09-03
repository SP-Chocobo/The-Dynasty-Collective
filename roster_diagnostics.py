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
  - bye_collision: lineup_optimizer.bye_collision (#142) -- the SAME assignment solver, run
    once per bye week against the roster with everyone on that bye removed. Reports value
    lost, not bodies lost, because a roster that covers three absences from its bench loses
    nothing and a headcount would rank it below one that loses a single irreplaceable starter.
    Observable only: it feeds no valuation, and that is a measured decision recorded at the
    function, not an omission.

What's explicitly NOT supported here, reported rather than approximated: age/trajectory
composition. This harness's own synthetic players_db (built from Draft Sharks projections
reconstructed into a Sleeper-like shape for simulation purposes) carries no age or experience
field at all -- the real app's live players_db (from Sleeper's /players/nfl) does, but that
data was never threaded into this harness's player pool. Reported as a data-availability gap,
not filled with an invented estimate.

  CORRECTION (#142, 2026-09-03): the gap is narrower than that paragraph claims, and the
  correction is left visible rather than quietly rewritten. A real `age` column DOES reach
  this repository, on external_values, covering 100% of QB/RB/TE and 98% of WR in the
  valuation frame -- it had simply never been read by anything. So the sentence "carries no
  age or experience field at all" is true of THIS HARNESS's players_db and false of the
  repository. The gap is a wiring gap, not a supply gap, for offensive skill positions; it
  remains a supply gap for IDP (~5%) and DEF (0%). What age would be worth is measured in
  run_age_signal_measurement.py, and the reason it is still not wired is recorded there.
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
    # How many of this roster's players that surplus could NOT be computed for -- their
    # position carries no replacement level in the scored pool. Reported rather than folded
    # into the number above; see the surplus computation for why.
    replacement_level_unpriced: int
    positional_counts: dict
    thin_positions: tuple
    structural_holes: tuple
    # #142: bye-week exposure, as VALUE lost rather than bodies lost. {week: {...}} straight
    # from lineup_optimizer.bye_collision -- see that function for why a headcount ranks two
    # rosters backwards, and for the measurement behind the decision to report this rather
    # than score it. Empty when no rostered player has a resolvable bye; a week's numbers are
    # a FLOOR when its basis is "partial".
    bye_collision: dict


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
        # team comes from players_db rather than the candidate record: the trajectory's own
        # candidate shape carries no team, and a bye is a property of the team (see
        # DataMerger.bye_week_by_team).
        by_team[rec.roster_id].append({
            "id": cand["id"], "name": cand["name"], "position": cand["pos"], "uv": cand["uv"],
            "team": (players_db.get(str(cand["id"])) or {}).get("team"),
        })
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
    # PRE-DRAFT anchor, deliberately: this harness runs against a FULLY DRAFTED board, where
    # every position's remaining starter demand is zero and a live replacement level is
    # therefore undefined (see draft_room.replacement_levels' domain). Passing no demand asks
    # for the pre-draft level -- the value of the Nth-best player in the field, N = league-wide
    # starting slots -- which is what "value above replacement across a roster" has always
    # meant here, and, per the same audit, what the live anchor was numerically equal to
    # anyway for as long as it was defined.
    repl_levels = (
        dr.replacement_levels(scored_pool, "universal_value", roster_positions, num_teams)
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
    bye_by_team = merger.bye_week_by_team()

    results: dict[str, TeamDiagnostics] = {}
    for rid, players in by_team.items():
        opt_players = [{"id": p["id"], "value": p["uv"], "eligible": {p["position"]},
                        "bye": bye_by_team.get(p.get("team"))} for p in players]
        lineup = lineup_optimizer.optimize_lineup(opt_players, slots)
        # Same rows, same solver, one more question asked of them: what is this lineup worth in
        # the week its byes land. Observable only -- nothing here feeds a value (see
        # lineup_optimizer.bye_collision on why that is a measured decision, not an omission).
        bye_exposure = lineup_optimizer.bye_collision(opt_players, roster_positions)
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
        # No default. A position with no replacement level has no surplus to report, and
        # defaulting it to 0.0 silently turned this into a plain sum of universal_value --
        # numerically identical to accumulated_value above, under a name that claims to mean
        # something else. Unpriced players are excluded and COUNTED, so the number states its
        # own coverage instead of quietly absorbing the gap.
        priced = [p for p in players if p["position"] in repl_levels]
        replacement_level_surplus = round(
            sum(p["uv"] - repl_levels[p["position"]] for p in priced), 2,
        )
        replacement_level_unpriced = len(players) - len(priced)

        results[rid] = TeamDiagnostics(
            roster_id=rid, accumulated_value=accumulated_value,
            starting_lineup_value=starting_lineup_value, bench_surplus_value=bench_surplus_value,
            replacement_level_surplus=replacement_level_surplus,
            replacement_level_unpriced=replacement_level_unpriced,
            positional_counts=positional_counts, thin_positions=tuple(sorted(thin_positions)),
            structural_holes=structural_holes, bye_collision=bye_exposure,
        )
    return results
