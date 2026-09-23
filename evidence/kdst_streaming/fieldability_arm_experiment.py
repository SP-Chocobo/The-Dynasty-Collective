"""Does the FIELDABILITY backstop fix the nine-defense roster, and at what cost? Repo root.

    python3 evidence/kdst_streaming/fieldability_arm_experiment.py [--season 2024] [--seats N]
                                                                   [--streaming]

THE A/B. One process, one code version, one toggle: `dr.unfieldable_last` is replaced by a
function returning all zeros for the control arm and restored afterwards -- the shape the
engine-measurement skill requires, and the shape `displacement_adjustments` is module-level and
patchable for. Both arms are graded on the season's REALIZED outcomes through
`run_backtest_grade`, under `period_correct_pool`.

WHY BOTH TOGGLES MATTER TOGETHER. `#30`'s derived streaming replacement level and this backstop
address the same pathology from opposite ends -- the level fixes what a streamable position is
WORTH, the backstop fixes how many of it a roster can USE. Measured separately on 2024 seat 1,
the level alone moved the hoard from rounds 6-16 to 10-16 and left SEVEN defenses. `--streaming`
runs the pair, so the report can say which of the two is doing the work rather than crediting
whichever was measured last.

WHAT THIS CANNOT SETTLE. One season, one format, n seats of self-play against a fixed field. It
says whether the backstop helps on a ruler the engine cannot optimise toward; it does not say
the magnitude transfers to a season the derivation never saw. The 2023 holdout is that test.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import pandas as pd

import draft_battery as db
import draft_room as dr
import run_backtest_grade as bg
import run_draft_battery as rdb

sys.path.insert(0, str(Path("evidence/kdst_streaming").resolve()))
import streaming_arm_experiment as sae  # noqa: E402  (same directory, run from the repo root)

SCRATCH = ("/tmp/claude-0/-home-user-The-Dynasty-Collective/"
           "90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad")
#: WHERE A LIVE RUN WRITES. The scratchpad, never a tracked path -- the battery README's rule 1,
#: which this script broke once: two concurrent 12-seat runs of the same season differing only
#: in --streaming both wrote `FIELDABILITY_ARM_2023.json` and the second overwrote the first.
#: Nothing published was wrong (the surviving file was the one quoted, and both runs' console
#: output is in the logs), but one arm's artifact was destroyed by the other. The ARM is in the
#: name now, so the two cannot collide even by accident, and a finished report is COPIED into
#: evidence deliberately rather than written there live.
OUT_TEMPLATE = SCRATCH + "/FIELDABILITY_ARM_{season}_{arm}.json"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--season", default="2024")
    parser.add_argument("--seats", type=int, default=0)
    parser.add_argument("--streaming", action="store_true",
                        help="also apply #30's derived streaming replacement level, so the pair "
                             "is measured together rather than one crediting the other's work")
    args = parser.parse_args(argv)

    scoring = rdb.scoring_settings_from_capture()
    players_db, _ = rdb.build_players_db_from_capture()
    arm = next(a for a in db.league_matrix(scoring) if a["label"] == sae.ARM)

    real_unfieldable = dr.unfieldable_last
    real_levels = dr.replacement_levels
    levels = {}
    if args.streaming:
        levels = sae.streaming_levels(args.season, scoring, players_db, arm["teams"],
                                      arm["league"]["roster_positions"])
        print(f"derived streaming levels ({args.season}): {levels}", flush=True)

        def streaming_replacement(*a, **k):
            got = real_levels(*a, **k)
            for position, level in levels.items():
                if position in got and level > got[position]:
                    got[position] = level
            return got

        dr.replacement_levels = streaming_replacement

    def no_backstop(scored, *a, **k):
        # The control: the backstop computed and discarded, so both arms run the same code path
        # and differ in exactly one thing.
        return pd.Series(0, index=scored.index, dtype=int)

    report = {"_comment": ("The fieldability backstop (draft_room.unfieldable_last) against a "
                           "control that switches it off, graded on realized outcomes. "
                           "`streaming` says whether #30's derived level was also applied."),
              "season": args.season, "arm": sae.ARM, "streaming": bool(args.streaming),
              "streaming_levels": levels, "arms": {}}

    suffix = ("_stream" if args.streaming else "") + (f"_s{args.seats}" if args.seats else "")
    try:
        for name, on in (("control", False), ("backstop", True)):
            dr.unfieldable_last = real_unfieldable if on else no_backstop
            print(f"\n=== arm: {name} ===", flush=True)
            path = f"{SCRATCH}/fb_{name}{suffix}.json"
            code = bg.main(["--season", args.season, "--out", path]
                           + (["--seats", str(args.seats)] if args.seats else []))
            if code != 0:
                print(f"arm {name} failed", file=sys.stderr)
                return code
            block = json.loads(Path(path).read_text())["results"][0]
            report["arms"][name] = {
                "wins": block["wins"], "seats": block["seats_graded"],
                "mean_delta": block["mean_delta"], "median_delta": block["median_delta"],
                "first_kdst_rounds": sorted({r["engine_first_kdst_round"] for r in block["rows"]}),
                "engine_totals": [r["engine_realized"] for r in block["rows"]],
                "roster_shape": _shape(block["rows"][0]["engine_roster"]),
            }
    finally:
        dr.unfieldable_last = real_unfieldable
        dr.replacement_levels = real_levels

    control, backstop = report["arms"]["control"], report["arms"]["backstop"]
    paired = [b - c for c, b in zip(control["engine_totals"], backstop["engine_totals"])]
    report["paired_engine_delta_mean"] = round(statistics.fmean(paired), 2)
    report["paired_engine_delta_median"] = round(statistics.median(paired), 2)
    report["seats_improved"] = sum(1 for d in paired if d > 0)

    out = Path(OUT_TEMPLATE.format(
        season=args.season,
        arm=("stream" if args.streaming else "base") + (f"_s{args.seats}" if args.seats else "")))
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(f"\n=== FIELDABILITY BACKSTOP vs CONTROL, {args.season} realized"
          f"{' (with #30 streaming levels)' if args.streaming else ''} ===")
    print(f"{'arm':<11}{'wins':>6}{'mean':>10}{'median':>10}  first K/DST   roster shape")
    for name in ("control", "backstop"):
        a = report["arms"][name]
        print(f"{name:<11}{a['wins']:>3}/{a['seats']:<2}{a['mean_delta']:>10.1f}"
              f"{a['median_delta']:>10.1f}  {str(a['first_kdst_rounds']):<13} {a['roster_shape']}")
    print(f"\nPAIRED engine total, backstop minus control, per seat:")
    print(f"   mean {report['paired_engine_delta_mean']:+.1f} | "
          f"median {report['paired_engine_delta_median']:+.1f} | "
          f"improved {report['seats_improved']} of {len(paired)}")
    print(f"\n-> {out}")
    return 0


def _shape(roster) -> dict:
    out: dict[str, int] = {}
    for pick in roster or []:
        out[pick["position"]] = out.get(pick["position"], 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


if __name__ == "__main__":
    raise SystemExit(main())
