"""#86: `round(expected_taken)` as a knife-edge, measured rather than argued.

BOTH ARMS ARE COMPUTED HERE. The rounded arm is recomputed from the curve, never read
back from `positional_forfeits` -- after the repair landed that would compare the fix
against itself and report no difference. `forfeit_live` records what the engine now
actually returns, so the file states the before, the after, and the shipped value.

`positional_forfeits` walks a position's own value curve down by `round(expected_taken)` players
and reports the drop. `expected_taken` is CONTINUOUS -- a sum of per-opponent probabilities -- and
`round` quantises it to a whole player, so 1.49 and 1.51 name different players and report
different costs from indistinguishable inputs.

TWO THINGS THIS PROBE MUST NOT ASSUME.

1. WHAT IT FEEDS. The freeze checklist says "a knife-edge feeding cliff_protection". That is
   STALE: `#160` moved `cliff_protection` onto the cliff machinery, and `pick_synthesis` now
   reads `(positional_cliff or {}).get("tier")`. This probe therefore reports the jump in
   `positional_forfeit` itself and leaves the consumer question to the register entry.

2. THAT THE KNIFE-EDGE IS EVER NEAR. A quantisation defect only bites if real values land near
   .5. If every measured `expected_taken` sits at .05 or .95 the defect is theoretical, and that
   is a finding, not a disappointment. So the FRACTIONAL PART DISTRIBUTION is the headline, not
   the jump size.

Run from the repo root. NEVER cd first -- DataMerger resolves baselines against cwd.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/forfeit_knife_edge/rounding_jump.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import league_config as lc
import run_draft_battery as rdb

OUT = Path("evidence/forfeit_knife_edge/rounding_jump.json")
LABEL = "CAPTURE_fourth_and_forever"


def interpolated(curve: list[float], taken: float) -> float:
    """The curve read at a FRACTIONAL index instead of a rounded one. This adds no constant and
    chooses no threshold -- it removes the arbitrary one already there (why round-half-even?), so
    it is not the calibration `#56` forbids."""
    if not curve:
        return 0.0
    hi = len(curve) - 1
    t = max(0.0, min(float(taken), float(hi)))
    lo_i = int(math.floor(t))
    hi_i = min(lo_i + 1, hi)
    frac = t - lo_i
    at_t = curve[lo_i] + (curve[hi_i] - curve[lo_i]) * frac
    return curve[0] - at_t


def main() -> int:
    battery = json.loads(Path("evidence/mode_boundary/depth_battery.json").read_text())["arms"]
    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    base = rdb.scoring_settings_from_capture()
    matrix = {e["label"]: e for e in db.league_matrix(base)}
    entry = battery[LABEL]
    lg = dr.build_mock_league(teams=entry["teams"], superflex=False, scoring="ppr",
                              te_premium=False, dynasty=True, base_scoring=base)
    st = [s for s in lg["roster_positions"] if s != "BN"]
    lg["roster_positions"] = st + ["BN"] * (entry["rounds"] - len(lc.draftable_slots(st)))
    league = matrix[LABEL]["league"] if LABEL in matrix else lg
    merger.set_league_format(db.league_format_hint(league))            # NEVER SKIP

    teams, rounds = entry["teams"], entry["rounds"]
    roster_ids = [str(i) for i in range(1, teams + 1)]
    pick_order = ds.generate_pick_order(roster_ids, rounds)
    boards = ds._build_opponent_boards(merger, players_db, [], league, roster_ids,
                                       sleeper_projections=season,
                                       sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    curves = ds._position_curves(boards[roster_ids[0]]["by_id"])   # by_id: {player_id: row}
    print(f"universe {prov['players_in_pool']}   curves for {sorted(curves)}", flush=True)

    # Every seat's FIRST turn -- the gap AHEAD is what positional_forfeits is about, and seat by
    # seat that gap varies from 2 to 22, which is the spread this needs.
    rows = []
    for seat in roster_ids:
        i = pick_order.index(seat)
        nxt = ds.find_next_pick_index(pick_order, seat, i)
        intervening = ds.intervening_roster_ids(pick_order, i, nxt)
        if not intervening:
            continue
        got = ds.positional_forfeits(curves, boards, intervening)
        for pos, r in got.items():
            taken = r["expected_taken"]
            curve = curves[pos]
            drop_r = min(round(taken), len(curve) - 1)
            lo = min(math.floor(taken), len(curve) - 1)
            hi = min(lo + 1, len(curve) - 1)
            rows.append({
                "seat": seat, "intervening": len(intervening), "position": pos,
                "expected_taken": taken, "frac": round(taken - math.floor(taken), 4),
                # THE OLD BEHAVIOUR, RECOMPUTED HERE RATHER THAN READ OFF THE LIVE FUNCTION.
                # Once the repair landed, reading r["forfeit"] made both arms the same code and
                # the probe reported a 0.00 delta -- it was comparing the fix against itself.
                "forfeit_rounded": round(curve[0] - curve[drop_r], 2),
                "forfeit_live": r["forfeit"],
                "forfeit_floor": round(curve[0] - curve[lo], 2),
                "forfeit_ceil": round(curve[0] - curve[hi], 2),
                "forfeit_interpolated": round(interpolated(curve, taken), 2),
                "jump": round((curve[0] - curve[hi]) - (curve[0] - curve[lo]), 2),
                "best_now": r["best_now"], "drop_used": drop_r,
            })

    if not rows:
        print("NO ROWS -- population vacuous, reporting nothing.")
        return 1

    # 1. THE HEADLINE: how near the knife-edge do real values actually land?
    fracs = sorted(r["frac"] for r in rows)
    near = [f for f in fracs if abs(f - 0.5) <= 0.1]
    print(f"\n1. {len(rows)} position/turn observations")
    print(f"   fractional part: min {fracs[0]:.3f}  median {fracs[len(fracs)//2]:.3f}  "
          f"max {fracs[-1]:.3f}")
    print(f"   within 0.1 of the .5 knife-edge: {len(near)} of {len(fracs)} "
          f"({100*len(near)/len(fracs):.0f}%)", flush=True)

    # 2. The size of the discontinuity where it exists.
    jumps = sorted((r["jump"] for r in rows), reverse=True)
    print(f"\n2. jump between floor and ceil (the whole-player step):")
    print(f"   max {jumps[0]:.2f}   median {jumps[len(jumps)//2]:.2f}   min {jumps[-1]:.2f}")

    # 3. What interpolation would change.
    deltas = sorted((abs(r["forfeit_interpolated"] - r["forfeit_rounded"]) for r in rows),
                    reverse=True)
    print(f"\n3. |interpolated - rounded|: max {deltas[0]:.2f}  "
          f"median {deltas[len(deltas)//2]:.2f}")
    print(f"   observations where they differ by >1.0: "
          f"{sum(1 for d in deltas if d > 1.0)} of {len(deltas)}")

    print(f"\n   {'seat':<5}{'pos':<5}{'interv':>7}{'taken':>8}{'frac':>7}"
          f"{'rounded':>9}{'interp':>8}{'jump':>8}")
    for r in sorted(rows, key=lambda r: -abs(r["forfeit_interpolated"] - r["forfeit_rounded"]))[:12]:
        print(f"   {r['seat']:<5}{r['position']:<5}{r['intervening']:>7}"
              f"{r['expected_taken']:>8.2f}{r['frac']:>7.2f}"
              f"{r['forfeit_rounded']:>9.2f}{r['forfeit_interpolated']:>8.2f}{r['jump']:>8.2f}")

    OUT.write_text(json.dumps({
        "league": LABEL, "universe": prov["players_in_pool"], "observations": len(rows),
        "frac_min": fracs[0], "frac_median": fracs[len(fracs)//2], "frac_max": fracs[-1],
        "within_0p1_of_knife_edge": len(near),
        "jump_max": jumps[0], "jump_median": jumps[len(jumps)//2],
        "interp_delta_max": deltas[0], "interp_delta_median": deltas[len(deltas)//2],
        "rows": rows,
    }, indent=1))
    print(f"\nwrote {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
