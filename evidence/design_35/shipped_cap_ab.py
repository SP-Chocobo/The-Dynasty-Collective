"""Does the SHIPPED engine draft better than the engine without #35's cap? RUN FROM THE REPO ROOT.

    python3 evidence/design_35/shipped_cap_ab.py --season 2024 --out DIR

WHY THIS EXISTS, AND IT IS A CORRECTION. `phantom_cap_experiment.py`'s `c_prime` arm measured
+21.7/seat (2024) and +43.69 (2023) and those figures were attributed to this change. They are
figures about a DIFFERENT configuration. That arm capped `bpa`'s anchor and then fed
`board_slot_alternatives` the UNCAPPED levels with C's cap applied:

    measured arm:  alt(s) = min( max L_uncapped(p),  max b(p) )   over the slot's eligible p
    SHIPPED:       alt(s) = max( min(L(p), b(p)) )                over the slot's eligible p

`min`-of-maxes and `max`-of-mins are not the same function. Measured on one drained 2024 board:
**226 of 1034 rows differ, by up to 16.68 points** in `final_score` and in `displacement_adj`.

So the shipped configuration's outcome was never graded, and this grades it. The ON arm is
production with NOTHING patched. The OFF arm replaces `dr.cap_levels_at_best_remaining` with a
no-op, which is exactly the pre-`#35` engine -- one thing toggled, both arms in one process, which
is what the engine-measurement skill requires.

Production's form is the one to prefer on its merits even before the grade: it caps each position's
level ONCE, and `shared_slot_alternatives`' own rule ("the best thing a free player at this slot
could be, over the positions it admits") then applies to honest levels. The measured arm's form mixed
an uncapped level from one position with a cap from another. But preferring it is not the same as
having graded it.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

_ROOT = Path.cwd()
if not (_ROOT / "draft_room.py").exists():
    raise SystemExit(f"run this from the repo root; cwd is {_ROOT}")
sys.path.insert(0, str(_ROOT))

import draft_room as dr          # noqa: E402
import run_backtest_grade as bg  # noqa: E402

#: How often the shipped cap actually fired, so a null result can be told from an inert arm.
_STATS = {"calls": 0, "levels_capped": 0, "by_position": {}}


def install_counter():
    """Count what the SHIPPED cap does, without changing what it does."""
    real = dr.cap_levels_at_best_remaining

    def counted(levels, priced_pool, streaming_floors=None):
        capped = real(levels, priced_pool, streaming_floors)
        _STATS["calls"] += 1
        _STATS["levels_capped"] += len(capped)
        for position in capped:
            _STATS["by_position"][position] = _STATS["by_position"].get(position, 0) + 1
        return capped

    dr.cap_levels_at_best_remaining = counted
    return real


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--season", default="2024")
    parser.add_argument("--out", required=True)
    parser.add_argument("--seats", type=int, default=0)
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    real = install_counter()
    counted = dr.cap_levels_at_best_remaining

    arms, reports = {}, {}
    for name in ("cap_off", "shipped"):
        # ONE THING TOGGLED. `cap_off` IS the pre-#35 engine; `shipped` is production, counted only.
        dr.cap_levels_at_best_remaining = (
            counted if name == "shipped" else (lambda levels, priced_pool, sf=None: set()))
        for key in ("calls", "levels_capped"):
            _STATS[key] = 0
        _STATS["by_position"] = {}
        report = out_dir / f"{name}_{args.season}.json"
        started = time.time()
        print(f"\n########## ARM {name} ({args.season}) ##########", flush=True)
        argv_arm = ["--season", args.season, "--streaming", "--out", str(report)]
        if args.seats:
            argv_arm += ["--seats", str(args.seats)]
        rc = bg.main(argv_arm)
        if rc != 0:
            print(f"arm {name} refused to run (rc={rc})")
            return rc
        block = json.loads(report.read_text())["results"][0]
        reports[name] = block
        arms[name] = {
            "wins": block["wins"], "seats": block["seats_graded"],
            "mean_delta": block["mean_delta"], "median_delta": block["median_delta"],
            "engine_totals": {r["seat"]: r["engine_realized"] for r in block["rows"]},
            "first_kdst_round": sorted(r["engine_first_kdst_round"] for r in block["rows"]),
            "cap_stats": dict(_STATS, by_position=dict(_STATS["by_position"])),
            "seconds": round(time.time() - started, 1),
        }
        print(f"   arm {name}: wins {block['wins']}/{block['seats_graded']} "
              f"mean {block['mean_delta']:+.1f}  cap {_STATS}", flush=True)

    dr.cap_levels_at_best_remaining = real
    off, on = arms["cap_off"]["engine_totals"], arms["shipped"]["engine_totals"]
    paired = {s: round(on[s] - off[s], 2) for s in off if s in on}
    v = list(paired.values())
    summary = {
        "_comment": ("#35 as SHIPPED vs the engine without it, graded on realized weekly outcomes. "
                     "This replaces the c_prime arm's figures, which were measured on a different "
                     "composition of the slot alternatives -- see this file's docstring."),
        "season": args.season, "arms": arms, "paired_shipped_minus_off": paired,
        "seats_improved": sum(1 for x in v if x > 0),
        "seats_worsened": sum(1 for x in v if x < 0),
        "paired_total": round(sum(v), 2),
        "paired_mean": round(sum(v) / len(v), 2) if v else None,
        "paired_median": round(statistics.median(v), 2) if v else None,
    }
    (out_dir / f"SUMMARY_{args.season}.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"\n=== #35 AS SHIPPED, {args.season} realized ===")
    for name in ("cap_off", "shipped"):
        b = arms[name]
        print(f"{name:>9}: wins {b['wins']}/{b['seats']}  mean {b['mean_delta']:+.1f}  "
              f"median {b['median_delta']:+.1f}  first K/DST {b['first_kdst_round']}")
    print(f"paired shipped - cap_off: {summary['seats_improved']} up, "
          f"{summary['seats_worsened']} down, total {summary['paired_total']:+.1f}, "
          f"mean {summary['paired_mean']}, median {summary['paired_median']}")
    print(f"-> {out_dir}/SUMMARY_{args.season}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
