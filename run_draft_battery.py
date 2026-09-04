"""#150's driver: draft every format in draft_battery.league_matrix() and write the report.

Committed as an instrument rather than a test because it is a MEASUREMENT, not an assertion --
a full matrix is thousands of real board builds and takes hours, which belongs in a deliberate
run, not in `python -m unittest`. test_draft_battery.py holds the part that must stay fast: that
every audit actually fires on the defect it names.

    python3 run_draft_battery.py [--out BATTERY_REPORT.json] [--only LABEL,LABEL]

The report separates FINDINGS (structural defects -- the league's own rules were violated) from
DISTRIBUTIONS (numbers for a person to read, where judging them would need a threshold nobody
has argued for). See draft_battery's docstring for why that split is the whole design.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import data_merger as dm
import draft_battery
import store_io

REPORT_PATH = Path("BATTERY_REPORT.json")

#: Every position a format in the matrix can start. Built once and shared, so all 30 formats
#: draft from the SAME pool -- which is what makes the comparative audits legitimate: a
#: difference between two formats has to come from the format, not from a different universe.
BATTERY_POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF", "DL", "LB", "DB")


def build_players_db(merger: dm.DataMerger, positions=BATTERY_POSITIONS) -> dict[str, dict]:
    """Every real baseline player as a Sleeper-shaped row, the same reconstruction
    test_draft_room._build_pool_players_db uses -- see merge_player on why first-initial +
    last name is a fair stand-in rather than a test artifact."""
    proj = merger.projections
    out: dict[str, dict] = {}
    pid = 0
    for position in positions:
        rows = proj[proj["position"] == position].sort_values("trade_value", ascending=False)
        for _, row in rows.iterrows():
            pid += 1
            parts = str(row["norm_name"]).split()
            out[str(pid)] = {
                "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                "position": position, "fantasy_positions": [position], "team": row.get("team"),
            }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", default=str(REPORT_PATH))
    parser.add_argument("--only", default="", help="comma-separated labels, for a partial run")
    args = parser.parse_args(argv)

    merger = dm.DataMerger()
    players_db = build_players_db(merger)
    matrix = draft_battery.league_matrix()
    if args.only:
        wanted = {name.strip() for name in args.only.split(",") if name.strip()}
        matrix = [entry for entry in matrix if entry["label"] in wanted]

    started = time.time()
    results = []
    for entry in matrix:
        t0 = time.time()
        audited = draft_battery.run_battery(merger, players_db, [entry])[0]
        audited["seconds"] = round(time.time() - t0, 1)
        results.append(audited)
        findings = len(audited["findings"])
        strength = audited.get("strength") or {}
        print(f"{audited['label']:22s} picks={audited['picks']:4d} "
              f"findings={findings:3d} "
              f"starters {strength.get('starter_value_min')}-{strength.get('starter_value_max')}"
              f" (spread {strength.get('starter_value_spread')})"
              f" {audited['seconds']:7.1f}s"
              + ("   <-- DEFECTS" if findings else ""), flush=True)

    total_findings = sum(len(r["findings"]) for r in results)
    report = {
        "formats": len(results),
        "picks": sum(r["picks"] for r in results),
        "total_findings": total_findings,
        "seconds": round(time.time() - started, 1),
        "results": results,
    }
    store_io.write(Path(args.out), report)
    print(f"\n{report['formats']} formats, {report['picks']} picks, "
          f"{total_findings} structural findings, {report['seconds']}s -> {args.out}")
    return 1 if total_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
