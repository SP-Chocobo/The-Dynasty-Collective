"""Does rival sloppiness delay the crossing, or -- via a rising level -- hasten it?

#263b. The owner's question, and it bounds #261's entire depth battery: every seat there is
the production engine taking its own best candidate, which is the MAXIMALLY EFFICIENT drain,
so every fire-round that battery reports is a LOWER BOUND rather than an estimate.

TWO EFFECTS PULL OPPOSITE WAYS AND THE NET IS NOT DERIVABLE.

  FIRST ORDER, delays firing. A rival who reaches leaves an above-replacement player on the
    board. n_above decays slower, so "nothing left above replacement" arrives later.
  SECOND ORDER, hastens firing. The replacement level is the Nth-best remaining at a position,
    N being remaining demand. If good players are NOT taken, the Nth-best remaining is BETTER,
    so the LEVEL RISES and fewer candidates clear it.

WHY THIS IS WORTH RUNNING, and it is not to confirm the obvious. The owner's stated expectation
is that sloppiness SHOULD delay recognition -- "if others are leaving value on the table and
shopping the dredges, good for them, good for you." If first order dominates, the rule behaves
as wanted and this run says so cheaply. If SECOND order dominates, the crossing would announce
"you are in the thin" precisely when value is still sitting on the board, which inverts the
behaviour the owner asked for. That is the outcome a confirmation-shaped test would miss, and it
is the reason to measure rather than reason.

DESIGN. One format held fixed -- 12T_ppr_BN18, 26 rounds, 312 picks, the same depth as the real
F&F capture and inside #261's known firing range. The only axis is opponent quality: seats other
than "1" choose uniformly from their own top_k instead of their best. k=1 is the no-noise control
and must reproduce the depth battery's own 12T_ppr_BN18 arm exactly -- if it does not, the noise
plumbing is wrong and nothing else here is readable.

TWO SEEDS PER k, because one draw is an anecdote. If the two seeds at a given k disagree about
the fire round by more than the gap between k levels, the axis is swamped by variance and the
run says THAT rather than pretending to a trend.

top_k IS NOT DERIVED and is never chosen: it is swept and reported across (#56).

Run from the repo root, AFTER the depth battery finishes -- they contend for the same 4 cores.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/mode_boundary/noise_arm.py
Resumes from its own output.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_simulation as ds
import draft_strategy as dstrat
import league_config as lc
import run_draft_battery as rdb

OUT = Path("evidence/mode_boundary/noise_arm.json")
TEAMS, BENCH, SHARP = 12, 18, ["1"]
TOP_K = (1, 3, 5, 10)      # 1 = control, must match the depth battery's 12T_ppr_BN18
SEEDS = (11, 22)


def main() -> int:
    t0 = time.time()
    report = json.loads(OUT.read_text()) if OUT.exists() else {"runs": {}}
    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    base = rdb.scoring_settings_from_capture()

    league = dr.build_mock_league(teams=TEAMS, superflex=False, scoring="ppr",
                                  te_premium=False, dynasty=True, base_scoring=base)
    starters = [s for s in league["roster_positions"] if s != "BN"]
    league["roster_positions"] = starters + ["BN"] * BENCH
    rounds = len(lc.draftable_slots(league["roster_positions"]))
    league["draft_rounds"] = rounds
    print(f"universe {prov['players_in_pool']}  12T_ppr_BN{BENCH}  rounds={rounds}  "
          f"picks={TEAMS * rounds}  sharp_seats={SHARP}", flush=True)

    for k in TOP_K:
        for seed in (SEEDS if k > 1 else (0,)):     # k=1 is deterministic; one run suffices
            key = f"k{k}_seed{seed}"
            if key in report["runs"]:
                print(f"[skip] {key}", flush=True)
                continue
            t1 = time.time()
            merger.set_league_format(db.league_format_hint(league))      # NEVER SKIP (#150)
            order = dstrat.generate_pick_order([str(i) for i in range(1, TEAMS + 1)],
                                               rounds, "snake")
            noise = None if k == 1 else {"top_k": k, "seed": seed, "sharp_seats": SHARP}
            traj = ds.simulate_full_draft(
                merger, players_db, league, order, config_label=key,
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
                upside_rule=dr.UPSIDE_RULE_CROSSING, opponent_noise=noise)
            fu = next(({"round": p.round, "pick_no": p.pick_no} for p in traj.picks
                       if p.chosen_growth_signal is not None), None)
            report["runs"][key] = {
                "top_k": k, "seed": seed, "n_picks": len(traj.picks),
                "first_upside_pick": fu, "elapsed_s": round(time.time() - t1, 1),
                "opponent_noise": traj.config.get("opponent_noise"),
            }
            print(f"[done] {key:<14} crossing fires -> "
                  f"{('r%d/p%d' % (fu['round'], fu['pick_no'])) if fu else 'NEVER':<12} "
                  f"{report['runs'][key]['elapsed_s']}s", flush=True)
            OUT.write_text(json.dumps(report, indent=1))                 # checkpoint (#215)

    report["elapsed_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(report, indent=1))
    print(f"\nwrote {OUT}  ({report['elapsed_s']}s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
