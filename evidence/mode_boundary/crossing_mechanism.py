"""#274. WHY the crossing fires in 1 arm of 10 -- read off the boards those 10 drafts actually saw.

#271 measured WHERE the crossing rule fires and found two things it could not explain: bench
depth moves it not at all (six arms, 168 -> 408 picks, zero firings), and team count moves it
NON-MONOTONICALLY (8T never, 10T fires, 12T never, 14T never). A 12-team draft consumed 177
more players than 10T needed to fire and still did not fire, so POOL DRAINAGE IS NOT THE
MECHANISM. This probe finds the one that is.

NO NEW DRAFTS ARE SIMULATED. #271 already recorded every pick of all twenty drafts in
depth_battery.json; this replays those exact pick sequences and rebuilds the board at sampled
prefixes. That is a deliberate choice, not a shortcut: a fresh simulation would be a DIFFERENT
draft (the engine's own picks depend on the board it is shown), and "why did THIS draft not
fire" cannot be answered on a draft that is not that one.

WHY bpa IS THE RIGHT COLUMN, and it is not an approximation. The rule tests
`not (pool.loc[measurable, "_vor"] > 0).any()` on an internal column (draft_room.py:3115).
Board rows do not carry `_vor` -- but `_scale_vor_to_bpa` is the IDENTITY function
(`return vor.astype(float)`, draft_room.py:2105, after #74/#76 removed the moving ruler), so
the exported `bpa` IS `_vor`, same values, NaN passed through untouched. `measurable` is
`_vor.notna()`, so it is `bpa is not None` here. Verified against the source rather than
assumed, and asserted at runtime below: the global verdict this probe reconstructs must match
the firing pick #271 recorded independently, or the probe is wrong and says so.

THE HYPOTHESIS BEING TESTED, pre-registered before the run:

  The crossing is NOT a depth condition. replacement_levels' own docstring says the rank
  target is REMAINING STARTER DEMAND, that bench picks create none, and that while demand is
  positive and picks come off the top "rank shrinkage and pool drain cancel exactly". A
  position's top VOR therefore does not decay toward zero as the pool drains -- it is pinned
  until that position's demand falls to 1.0, at which point rank 1 makes the replacement the
  best remaining player himself and VOR is exactly 0.00 by construction (the same degeneracy
  #73 logged and #185 repaired the labelling of).

  So the global rule needs EVERY position with live demand to sit at that degeneracy AT THE
  SAME PICK. That is an alignment coincidence, not a threshold -- which would explain both
  the depth null (bench slots add no demand, so they never move the alignment) and the
  non-monotonicity (alignment is not ordered in team count).

  PREDICTION, falsifiable: individual positions cross zero at WIDELY SEPARATED picks in every
  arm, including the arms where the global rule never fires; and in 10T they happen to
  coincide at the firing pick. If instead positions cross together everywhere, or if per-
  position maxima decay smoothly toward zero with picks taken, the hypothesis is wrong.

Run from the repo root. NEVER cd first -- DataMerger resolves baselines against cwd.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/mode_boundary/crossing_mechanism.py
Resumes from its own output; re-running after a kill picks up at the first unfinished arm.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import league_config as lc
import run_draft_battery as rdb

IN = Path("evidence/mode_boundary/depth_battery.json")
OUT = Path("evidence/mode_boundary/crossing_mechanism.json")
STRIDE = 5          # sample every Nth pick; board build is ~0.5s, a full 260-pick walk is ~4min
#: Ladder B (teams) first because it produced #274, then ladder A (bench depth) and the real
#: capture. All ten have recorded drafts in depth_battery.json, so the six added after #274 cost
#: nothing to simulate -- they only need reading. The bench ladder is the interesting addition:
#: if the HOLDOUT position is a property of roster SHAPE (#274's scope correction), six leagues
#: that differ only in bench depth must all share one holdout, and that is a real prediction.
ARMS = ("8T_ppr_BN18", "10T_ppr_BN18", "12T_ppr_BN18", "14T_ppr_BN18",
        "12T_ppr_BN6", "12T_ppr_BN10", "12T_ppr_BN14", "12T_ppr_BN22", "12T_ppr_BN26",
        "CAPTURE_fourth_and_forever")


def pick_sequence(entry: dict, rule: str) -> list[dict]:
    """The exact global pick order #271 recorded for this arm, as compute_draft_board wants it.

    per_seat is keyed by roster and each entry carries its own pick_no, so the global order is
    recovered by sorting on pick_no rather than by interleaving seats by hand -- the recorded
    number is the authority, not a re-derivation of snake order that could disagree with it.
    """
    flat = [(e["pick_no"], e["pid"], rid)
            for rid, picks in entry["rules"][rule]["per_seat"].items() for e in picks]
    flat.sort()
    return [{"player_id": pid, "roster_id": rid} for _, pid, rid in flat]


def league_for(teams: int, bench: int, base_scoring: dict) -> dict:
    """Rebuilt the way depth_battery.deep_league builds it, from the shipped starters (#126)."""
    lg = dr.build_mock_league(teams=teams, superflex=False, scoring="ppr",
                              te_premium=False, dynasty=True, base_scoring=base_scoring)
    starters = [s for s in lg["roster_positions"] if s != "BN"]
    lg["roster_positions"] = starters + ["BN"] * bench
    lg["draft_rounds"] = len(lc.draftable_slots(lg["roster_positions"]))
    return lg


def league_for_arm(label: str, entry: dict, base_scoring: dict, matrix: dict) -> dict:
    """The league THIS arm was drafted under -- derived from the arm, never assumed.

    The first version of this probe hardcoded bench 18, which was correct for the four ladder-B
    arms it was written for and silently WRONG for every other arm. A league rebuilt at the wrong
    depth still produces a full board and a plausible per-position table; it is the
    engine-measurement failure mode exactly ("a plausible number about something else"), so the
    depth now comes from the arm's own recorded round count rather than from a constant here.

    CAPTURE_fourth_and_forever is not a mock league at all and must come from the battery's own
    matrix, which is where depth_battery got it (#126: one home, derived).
    """
    if label in matrix:
        return matrix[label]["league"]
    starters = len(lc.draftable_slots(
        [s for s in dr.build_mock_league(
            teams=entry["teams"], superflex=False, scoring="ppr", te_premium=False,
            dynasty=True, base_scoring=base_scoring)["roster_positions"] if s != "BN"]))
    bench = entry["rounds"] - starters
    return league_for(entry["teams"], bench, base_scoring)


def probe_board(rows: list[dict], league: dict, teams: int,
                picks: list[dict], players_db: dict) -> dict:
    """Per position: top bpa among MEASURABLE rows, how many are measurable, and live demand.

    ABSENCE IS COUNTED SEPARATELY FROM ZERO, per the engine-measurement rule that a reporting
    function broke once already. `measurable` counts rows whose bpa exists; `top` is None when
    none do -- never 0.0, which is a real and different measurement.
    """
    demand = dr.remaining_starter_demand(
        league["roster_positions"], teams, picks, players_db)
    by_pos: dict[str, dict] = {}
    for r in rows:
        pos, bpa = r.get("position"), r.get("bpa")
        if pos is None:
            continue
        slot = by_pos.setdefault(pos, {"measurable": 0, "unpriced": 0, "top": None})
        if bpa is None or bpa != bpa:            # NaN
            slot["unpriced"] += 1
            continue
        slot["measurable"] += 1
        if slot["top"] is None or bpa > slot["top"]:
            slot["top"] = float(bpa)
    for pos, slot in by_pos.items():
        slot["demand"] = demand.get(pos)          # absent key = no starter-demand replacement
        slot["positive"] = None if slot["top"] is None else slot["top"] > 0
    return by_pos


def main() -> int:
    t0 = time.time()
    report = json.loads(OUT.read_text()) if OUT.exists() else {"arms": {}, "stride": STRIDE}
    battery = json.loads(IN.read_text())["arms"]

    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    base = rdb.scoring_settings_from_capture()
    matrix = {e["label"]: e for e in db.league_matrix(base)}
    print(f"universe {prov['players_in_pool']}  season {len(season)}", flush=True)

    for label in ARMS:
        if label in report["arms"]:
            print(f"[skip] {label}", flush=True)
            continue
        entry = battery[label]
        teams = entry["teams"]
        order = pick_sequence(entry, dr.UPSIDE_RULE_CROSSING)
        league = league_for_arm(label, entry, base, matrix)
        merger.set_league_format(db.league_format_hint(league))      # NEVER SKIP
        recorded = entry["rules"][dr.UPSIDE_RULE_CROSSING]["first_upside_pick"]
        print(f"\n== {label}  teams={teams}  picks={len(order)}  "
              f"#271 recorded: {recorded or 'NEVER'}", flush=True)

        samples, t1 = [], time.time()
        for n in range(0, len(order) + 1, STRIDE):
            prefix = order[:n]
            rows = dr.compute_draft_board(
                merger, players_db, prefix, "1", league,
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
                upside_rule=dr.UPSIDE_RULE_CROSSING)
            by_pos = probe_board(rows, league, teams, prefix, players_db)
            any_measurable = any(s["measurable"] for s in by_pos.values())
            any_positive = any(s["positive"] for s in by_pos.values())
            samples.append({
                "after_picks": n, "by_pos": by_pos,
                "any_measurable": any_measurable,
                # The rule, restated on the exported column. Reconstructed, then CHECKED below
                # against the independent firing pick #271 recorded -- never trusted on its own.
                "would_fire": bool(any_measurable and not any_positive),
            })
            if n % 50 == 0:
                print(f"   pick {n:>4}  " + "  ".join(
                    f"{p}:{'--' if s['top'] is None else format(s['top'], '.1f')}"
                    for p, s in sorted(by_pos.items())), flush=True)

        first_fire = next((s["after_picks"] for s in samples if s["would_fire"]), None)
        # Per position, the first sampled prefix at which ITS OWN best remaining player is at
        # or below its replacement level. This is the per-position crossing -- the quantity the
        # global rule collapses, and the one a per-position mode switch would read.
        per_pos_first = {}
        for pos in sorted({p for s in samples for p in s["by_pos"]}):
            per_pos_first[pos] = next(
                (s["after_picks"] for s in samples
                 if pos in s["by_pos"] and s["by_pos"][pos]["positive"] is False), None)

        report["arms"][label] = {
            "teams": teams, "total_picks": len(order),
            "battery_recorded_fire": recorded,
            "reconstructed_first_fire": first_fire,
            "per_position_first_cross": per_pos_first,
            "samples": samples,
        }
        OUT.write_text(json.dumps(report, indent=1))
        print(f"   global {first_fire}  per-pos {per_pos_first}  ({time.time()-t1:.1f}s)",
              flush=True)

    # SELF-CHECK. The probe restates the rule on an exported column; #271 detected firing from
    # the engine's own growth_signal. If they disagree the probe is wrong, and it must say so
    # rather than let a plausible number stand (engine-measurement: the failure mode to fear is
    # not a crash, it is a plausible number about something else).
    print("\nSELF-CHECK  reconstructed vs #271:", flush=True)
    for label, a in report["arms"].items():
        rec, mine = a["battery_recorded_fire"], a["reconstructed_first_fire"]
        rec_pick = rec["pick_no"] if rec else None
        if rec_pick is None and mine is None:
            verdict = "ok (both NEVER)"
        elif rec_pick is None or mine is None:
            verdict = f"MISMATCH -- #271 {rec_pick}, probe {mine}"
        else:
            verdict = ("ok (within stride)" if abs(rec_pick - mine) <= STRIDE
                       else f"MISMATCH -- #271 {rec_pick}, probe {mine}")
        print(f"  {label:<16} #271={str(rec_pick):<6} probe={str(mine):<6} {verdict}", flush=True)

    OUT.write_text(json.dumps(report, indent=1))
    print(f"\nwrote {OUT}  ({time.time()-t0:.1f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
