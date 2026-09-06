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
import roster_diagnostics
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


def strength_coverage(strength: dict | None) -> str:
    """The words beside the starter-value range on the per-format line below, so the number
    states its own coverage on the one screen roster strength reaches a person. The phrasing
    is roster_diagnostics.coverage_statement -- the one place it is written -- because the
    battery's starter_value makes the same exclusion that module's starting_lineup_value does
    (an unpriced player contributes nothing, so one anywhere makes the value a floor).

    Absence is not a value, and there are three absences here, each its own sentence and none
    of them a zero:
      strength is None       -> audit_trajectory was given no pre-draft values; nothing was
                                measured, so there is no coverage to state.
      per_roster absent      -> a strength record with no rosters in it; unmeasured, not zero.
      per_roster empty       -> measured, and there was nobody to price.
      a roster with no count -> a record from before draft_battery carried unpriced_players;
                                the count is unknown, not zero.
    Otherwise the per-roster counts are summed and stated.
    """
    if strength is None:
        return "strength not measured (no pre-draft values), so coverage is unknown"
    per_roster = strength.get("per_roster")
    if per_roster is None:
        return roster_diagnostics.coverage_statement(None)
    if not per_roster:
        return "no rosters to price"
    counts = [row.get("unpriced_players") for row in per_roster.values()]
    if any(count is None for count in counts):
        return roster_diagnostics.coverage_statement(None)
    return roster_diagnostics.coverage_statement(sum(counts))


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
        # The coverage clause reads the RAW strength, not the `or {}` above, so None stays an
        # absence with its own sentence instead of collapsing into an empty record.
        print(f"{audited['label']:22s} picks={audited['picks']:4d} "
              f"findings={findings:3d} "
              f"starters {strength.get('starter_value_min')}-{strength.get('starter_value_max')}"
              f" (spread {strength.get('starter_value_spread')}; "
              f"{strength_coverage(audited.get('strength'))})"
              f" {audited['seconds']:7.1f}s"
              + ("   <-- DEFECTS" if findings else ""), flush=True)

    total_findings = sum(len(r["findings"]) for r in results)
    # The instrument states its own coverage. `formats` is how many arms RAN;
    # `independent_formats` is how many produced evidence nothing else already produced. They
    # differ whenever two arms resolve to the same rankings export -- see duplicate_arms.
    dupes = draft_battery.duplicate_arms(results)
    report = {
        "formats": len(results),
        "independent_formats": len(results) - len(dupes),
        "duplicate_arms": dupes,
        "picks": sum(r["picks"] for r in results),
        "total_findings": total_findings,
        "seconds": round(time.time() - started, 1),
        "results": results,
    }
    store_io.write(Path(args.out), report)
    print(f"\n{report['formats']} formats ({report['independent_formats']} independent), "
          f"{report['picks']} picks, {total_findings} structural findings, "
          f"{report['seconds']}s -> {args.out}")
    for dupe in dupes:
        print(f"  DUPLICATE ARM: {dupe['label']} reproduces {dupe['duplicates']} exactly "
              f"-- same rankings export, so it is not independent evidence")
    return 1 if total_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
