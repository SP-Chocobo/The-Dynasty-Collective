"""Read a BACKTEST report and say WHERE the engine's points went. Run from the repo root.

    python3 evidence/backtest/roster_diff.py <report.json> [--seat 1]

The grade says the engine lost by N. It does not say whether N is two wasted early picks, a thin
bench, or a position the engine systematically misprices -- and those want completely different
repairs. This reads the rosters the report now carries and splits the deficit three ways:

  BY POSITION   realized total the engine got at each position vs the best field seat's. A
                deficit concentrated at one position is a valuation problem.
  BY ROUND      realized total per draft round. A deficit in rounds 1-6 is an allocation
                problem; one in rounds 9-16 is a depth problem.
  THE EARLY BILL what the engine spent its first six picks on, listed. This is where a round-4
                kicker shows up as itself rather than as a number.

It reads only the report. Nothing is re-drafted, so it costs nothing and can be pointed at any
saved run, including an old one.
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

EARLY_ROUNDS = 6


def totals(roster, key):
    out = collections.defaultdict(float)
    for pick in roster:
        out[pick[key]] += pick["realized"] or 0.0
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("report")
    parser.add_argument("--seat", default=None)
    args = parser.parse_args(argv)

    report = json.loads(Path(args.report).read_text())
    for block in report["results"]:
        print(f"\n=== {block['label']} [{block.get('horizon', 'dynasty')}] "
              f"{block['season']} ===")
        rows = [r for r in block["rows"]
                if args.seat is None or str(r["seat"]) == str(args.seat)]
        if not rows or rows[0].get("engine_roster") is None:
            print("  this report predates the roster dump -- re-run to diff it")
            continue

        by_pos = collections.defaultdict(float)
        by_round = collections.defaultdict(float)
        for row in rows:
            mine = totals(row["engine_roster"], "position")
            theirs = totals(row["best_field_roster"], "position")
            for position in set(mine) | set(theirs):
                by_pos[position] += mine.get(position, 0.0) - theirs.get(position, 0.0)
            mr, tr = totals(row["engine_roster"], "round"), totals(row["best_field_roster"], "round")
            for rnd in set(mr) | set(tr):
                by_round[rnd] += mr.get(rnd, 0.0) - tr.get(rnd, 0.0)

        n = len(rows)
        print(f"  seats: {n}    (every figure below is PER SEAT, engine minus best field seat)")
        print("\n  BY POSITION")
        for position, delta in sorted(by_pos.items(), key=lambda kv: kv[1]):
            print(f"    {position:<5}{delta / n:>+10.1f}")
        print("\n  BY ROUND")
        for rnd in sorted(by_round):
            bar = "#" * min(40, int(abs(by_round[rnd]) / n / 8))
            print(f"    rd {int(rnd):>2}{by_round[rnd] / n:>+10.1f}  {bar}")

        print(f"\n  THE EARLY BILL (rounds 1-{EARLY_ROUNDS}), seat {rows[0]['seat']}")
        for pick in rows[0]["engine_roster"][:EARLY_ROUNDS]:
            print(f"    rd {pick['round']:>2}  {pick['position']:<4} {pick['player'][:26]:<27}"
                  f"proj {str(pick['projected']):>7}   realized {pick['realized']:>7.1f}")
        print(f"  the best field seat ({rows[0]['best_field_seat']}) spent the same picks on")
        for pick in rows[0]["best_field_roster"][:EARLY_ROUNDS]:
            print(f"    rd {pick['round']:>2}  {pick['position']:<4} {pick['player'][:26]:<27}"
                  f"proj {str(pick['projected']):>7}   realized {pick['realized']:>7.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
