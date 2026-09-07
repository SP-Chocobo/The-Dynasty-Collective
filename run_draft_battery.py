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
import player_universe
import store_io

REPORT_PATH = Path("BATTERY_REPORT.json")

#: Every position a format in the matrix can start. Built once and shared, so all 30 formats
#: draft from the SAME pool -- which is what makes the comparative audits legitimate: a
#: difference between two formats has to come from the format, not from a different universe.
BATTERY_POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF", "DL", "LB", "DB")


CAPTURE_PATH = Path("data/fixtures/sleeper_capture.json")


def build_players_db(merger: dm.DataMerger, positions=BATTERY_POSITIONS) -> dict[str, dict]:
    """Every real baseline player as a Sleeper-SHAPED row, reconstructed from the vendor table.

    CARRIES NO injury_status, AND THAT IS THE POINT OF ITS NAME NOW (#201). The vendor export
    has no health column, so a pool built from it gives every player a status of None and
    `risk_adj` is 0.00 for all of them. The battery ran on this for its entire life, which means
    every arm ever certified described a board with no health signal on it at all -- discovered
    when a four-arm risk_adj ablation returned "0 players moved" in every arm and the reason
    turned out to be an empty status counter, not a null result.

    KEPT, NOT DELETED, and kept as the universe of the measurements that already used it:
    run_demand_reach_audit.py records results against this pool, and silently re-pointing it at
    a different universe would make a recorded experiment describe something else under the same
    name -- the hazard test_measurement_script_boundary now enforces. New work uses
    build_players_db_from_capture below.
    """
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


def build_players_db_from_capture(positions=BATTERY_POSITIONS,
                                  path: Path = CAPTURE_PATH) -> tuple[dict[str, dict], dict]:
    """The REAL Sleeper player universe, as the app itself receives it (#201).

    Returns (players_db, provenance). The battery certifies the engine, so it has to draft from
    the universe the engine actually gets: injury_status, fantasy_positions, years_exp, status
    and team, per player, exactly the fields build_available_pool reads. The reconstruction
    above supplies none of them, so every property the battery has ever asserted about health,
    multi-position eligibility or rookie admission was asserted about a pool that could not
    express them.

    NO SILENT FALLBACK. A missing capture raises. Falling back to the vendor reconstruction is
    precisely how this defect stayed invisible for so long: the battery went on producing
    plausible reports about a universe nobody had chosen.

    The provenance dict travels into the report so a reader can tell WHICH capture a run
    drafted from -- a battery is a dated measurement, and #201 exists because one silently
    was not the measurement it claimed.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing -- the battery certifies against the REAL player universe and "
            "must not quietly fall back to the vendor reconstruction (#201)")
    with open(path, encoding="utf-8") as handle:
        capture = json.load(handle)
    players = capture.get("players") or {}
    wanted = set(positions)
    out = {pid: info for pid, info in players.items()
           if player_universe.player_eligible_positions(info) & wanted}
    provenance = {
        "source": str(path),
        "captured_at": capture.get("captured_at"),
        "season": capture.get("season"),
        "players_in_capture": len(players),
        "players_in_pool": len(out),
        # Stated, not assumed: the whole reason this function exists.
        "injury_statuses_present": sorted(
            {info.get("injury_status") for info in out.values() if info.get("injury_status")}),
    }
    return out, provenance


#: Named in front of the coverage sentence so it cannot be read as a claim about the board at
#: the pick. See strength_coverage's docstring and #170.
PREDRAFT_RULER = "against the pre-draft ruler"


def decision_coverage(at_decision: dict | None) -> str:
    """The companion clause: what the board looked like AT THE PICK, not before the draft.

    Absence keeps its own sentence here too -- a record from before draft_battery carried this
    block is unmeasured, never zero."""
    if not at_decision:
        return "absence at the pick not measured"
    examined = at_decision.get("picks_examined")
    if not examined:
        return "no picks carried a candidate set, so nothing at the pick was measurable"
    contended = at_decision.get("picks_with_an_unpriced_candidate", 0)
    took = at_decision.get("picks_that_took_an_unpriced_candidate", 0)
    if not contended:
        return f"no unpriced candidate reached any of the {examined} decisions"
    return (f"an unpriced candidate reached {contended} of {examined} decisions "
            f"and won {took}")


def strength_coverage(strength: dict | None) -> str:
    """The words beside the starter-value range on the per-format line below, so the number
    states its own coverage on the one screen roster strength reaches a person. The phrasing
    is roster_diagnostics.coverage_statement -- the one place it is written -- because the
    battery's starter_value makes the same exclusion that module's starting_lineup_value does
    (an unpriced player contributes nothing, so one anywhere makes the value a floor).

    #170. The sentence NAMES ITS REFERENCE, because without that it claimed more than it knew.
    `reference_values` builds the ruler from the PRE-DRAFT board, which prices every row, and
    every drafted player is necessarily on that board -- so the count behind this sentence is 0
    by construction and was read (by me, in the register) as "the engine priced everyone in this
    draft" when it means "everyone had a pre-draft price". The phrasing is still
    roster_diagnostics.coverage_statement, the one place it is written; the reference is stated
    in front of it. What the engine did at the pick is a DIFFERENT number --
    draft_battery.unpriced_at_decision -- printed separately rather than merged into this one.

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
    return f"{PREDRAFT_RULER}: {roster_diagnostics.coverage_statement(sum(counts))}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", default=str(REPORT_PATH))
    parser.add_argument("--only", default="", help="comma-separated labels, for a partial run")
    args = parser.parse_args(argv)

    merger = dm.DataMerger()
    players_db, universe = build_players_db_from_capture()
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
              f"{strength_coverage(audited.get('strength'))}; "
              f"{decision_coverage(audited.get('unpriced_at_decision'))})"
              f" {audited['seconds']:7.1f}s"
              + ("   <-- DEFECTS" if findings else ""), flush=True)

    total_findings = sum(len(r["findings"]) for r in results)
    # The instrument states its own coverage. `formats` is how many arms RAN;
    # `independent_formats` is how many produced evidence nothing else already produced. They
    # differ whenever two arms resolve to the same rankings export -- see duplicate_arms.
    dupes = draft_battery.duplicate_arms(results)
    report = {
        # WHICH UNIVERSE THIS RUN DRAFTED FROM. A battery is a dated measurement against a
        # dated pool, and #201 is what happens when that goes unrecorded: every arm was
        # certified against a reconstruction with no health signal and nothing said so.
        "universe": universe,
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
