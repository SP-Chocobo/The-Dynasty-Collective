"""Driver for the VDS battery: varied drafting strategy x format. See vds_battery.py for why.

Committed as an INSTRUMENT, not a test, for the same reason the format battery is: 36 arms of
real drafts is hours of work and belongs in a deliberate run, never in `python -m unittest`.

    python3 run_vds_battery.py [--out VDS_REPORT.json] [--only LABEL,LABEL] [--resume]

The report is read STRATEGY-WISE, which is the whole point and the difference from the format
battery's report. A finding that appears under every strategy in a format is a FORMAT finding and
the other battery would have caught it. A finding that appears under ONE strategy is what this
battery exists for -- that is the shape `#22` had, and the shape the format matrix cannot see
because 34 of its 36 arms hold strategy at `mode="auto"`.
"""

from __future__ import annotations

import argparse
import collections
import time
from pathlib import Path

import data_merger as dm
import draft_battery
import draft_room as dr
import resume_join
import run_draft_battery as rdb
import store_io
import vds_battery

REPORT_PATH = Path("VDS_REPORT.json")


def _arm_line(audited: dict) -> str:
    findings = len(audited.get("findings", []))
    mark = "  " if not findings else "!!"
    return (f"{mark} {audited['label']:<44} findings={findings:<3} "
            f"{audited.get('seconds', '?')}s")


def _report(universe: dict, results: list[dict], started: float, *, complete: bool) -> dict:
    by_strategy: dict[str, int] = collections.Counter()
    by_format: dict[str, int] = collections.Counter()
    for row in results:
        label = row["label"]
        fmt, _, strategy = label.partition("__")
        by_strategy[strategy] += len(row.get("findings", []))
        by_format[fmt] += len(row.get("findings", []))

    # INERT ARMS, DERIVED AND REPORTED -- the single most important line in this report.
    #
    # Measured before the first full run, on 12T_ppr_SHORT_DRAFT: `sharp_balanced` and
    # `crossing` produced drafts BYTE-IDENTICAL to the control, 0 of 96 picks different. Both
    # for structural reasons: that format is 8 rounds, `auto` never reaches
    # UPSIDE_MODE_DEFAULT_ROUND (15) so auto IS balanced there, and the crossing rule needs the
    # board to run out of positive VOR, which an 8-round draft never does.
    #
    # So a strategy can be listed, forwarded, and exercise nothing -- which is precisely what the
    # format battery's own mode axis did before it was fixed ("the battery would have reported
    # 'modes covered' while exercising one"). An arm that reproduces its control is not evidence
    # about that strategy, and a report that counts it as a clean arm is counting the control
    # six times.
    #
    # Derived by comparing each arm's pick sequence against its OWN format's control arm, never
    # assumed from the parameters: whether a parameter bites is a property of the format it is
    # applied to.
    inert = []
    controls = {}
    for row in results:
        if row.get("strategy") == vds_battery.CONTROL_STRATEGY:
            controls[row.get("format")] = row.get("pick_sequence")
    for row in results:
        fmt, strategy = row.get("format"), row.get("strategy")
        if strategy == vds_battery.CONTROL_STRATEGY or fmt not in controls:
            continue
        if row.get("pick_sequence") and row["pick_sequence"] == controls[fmt]:
            inert.append(row["label"])

    # A finding under EVERY strategy in a format is a format finding; under ONE it is a strategy
    # finding. Derived here rather than left to a reader, because the whole reason this battery
    # exists is that nobody was reading the axis.
    #
    # INERT ARMS ARE EXCLUDED, AND THE DENOMINATOR IS WHAT RAN. Two defects lived here.
    #
    # (1) An inert arm reproduces its control byte for byte, so the control's finding appears
    #     again under the inert arm's strategy name. Demonstrated: three arms run, two of them
    #     inert copies of the control each carrying the control's single finding, and this block
    #     listed ALL THREE strategies as carrying findings -- "the shape #22 had" reported over a
    #     finding that is a property of the control. The `INERT_ARMS` line twelve lines above
    #     exists to say those arms are not evidence about their strategy; this block then counted
    #     them as exactly that.
    #
    # (2) `len(vds_battery.STRATEGIES)` is the denominator of the CODE's strategy list, not of
    #     the arms in `results`. On a partial run, an `--only` run, or the mid-run file -- which
    #     is what a reader usually holds, because this file is rewritten after every arm and long
    #     runs are routinely killed -- a finding present under every strategy that RAN was
    #     reported as strategy-specific because fewer strategies ran than exist.
    #
    # (3) ARMS WITH NO ENGINE SEAT WERE NEVER ACTUALLY SKIPPED, THOUGH THIS COMMENT SAID THEY
    #     WERE (V4-I1). `noisy_k3`/`noisy_k8` set `sharp_seats: []` -- no seat uses the engine --
    #     so a finding there is a property of uniform random draws and belongs on no strategy's
    #     ledger. But the test read `row["sharp_seats"]`, and that is NOT WHERE THE VALUE LIVES:
    #     it lives at `opponent_noise.sharp_seats` in the matrix, and the serialized result row
    #     carries no such key at all. So the read always returned its truthy default and the
    #     guard COULD NOT FIRE; `by_strategy_effective` never had the guard in the first place.
    #     Measured when it was found: `noisy_k8` held 16 of the run's 19 findings, every one of
    #     them credited to it as a strategy property.
    #
    #     DERIVED FROM THE MATRIX, WHICH IS THE ONE HOME FOR THE RULE (`#126`). The matrix is
    #     available here and already holds the truth, so nothing is read off a row that was never
    #     asked to carry it (`#166`) and no arm has to be re-drafted to be judged correctly.
    inert_labels = set(inert)
    no_engine = {arm["label"] for arm in vds_battery.vds_matrix()
                 if not (arm.get("opponent_noise") or {}).get("sharp_seats", ["present"])}
    # Every strategy that ran appears, at zero if it produced nothing under an effective arm --
    # an absent key and a zero are different claims, and a reader comparing this against
    # `findings_by_strategy` needs the same key set in both.
    by_strategy_effective: dict[str, int] = collections.Counter(
        {row["label"].partition("__")[2]: 0 for row in results})
    for row in results:
        if row["label"] in inert_labels or row["label"] in no_engine:
            continue
        by_strategy_effective[row["label"].partition("__")[2]] += len(row.get("findings", []))
    per_format_strategies: dict[str, set] = collections.defaultdict(set)
    per_format_ran: dict[str, set] = collections.defaultdict(set)
    for row in results:
        fmt, _, strategy = row["label"].partition("__")
        if row["label"] in inert_labels or row["label"] in no_engine:
            continue
        per_format_ran[fmt].add(strategy)
        if row.get("findings"):
            per_format_strategies[fmt].add(strategy)
    strategy_specific = {
        fmt: sorted(strategies) for fmt, strategies in per_format_strategies.items()
        if 0 < len(strategies) < len(per_format_ran[fmt])
    }

    return {
        "_comment": ("VDS battery: varied drafting strategy x format. Read STRATEGY-WISE. A "
                     "finding under every strategy in a format is a format finding the other "
                     "battery would catch; a finding under ONE strategy is what this exists for "
                     "-- the shape #22 had. See vds_battery.py."),
        "complete": complete,
        "seconds": round(time.time() - started, 1),
        "universe": universe,
        "strategies": {name: dict(cfg) for name, cfg in vds_battery.STRATEGIES.items()},
        "control_strategy": vds_battery.CONTROL_STRATEGY,
        "formats": dict(vds_battery.FORMATS),
        "seed": vds_battery.VDS_SEED,
        "top_k_swept": list(vds_battery.VDS_TOP_K),
        "arms_run": len(results),
        "INERT_ARMS": sorted(inert),
        "inert_arm_count": len(inert),
        "effective_arms": len(results) - len(inert),
        "findings_total": sum(len(r.get("findings", [])) for r in results),
        "findings_by_strategy": dict(by_strategy),
        "findings_by_format": dict(by_format),
        # THE SAME TOTALS WITH THE INERT ARMS TAKEN OUT. Both are reported rather than one
        # replacing the other: `findings_total` is what the run produced and is the right number
        # for "did anything fire", while a per-strategy attribution that includes an arm which
        # reproduced its control is counting the control again under another name.
        "findings_total_effective": sum(len(r.get("findings", [])) for r in results
                                        if r["label"] not in set(inert)),
        "findings_by_strategy_effective": dict(by_strategy_effective),
        # THE NO-ENGINE ARMS, NAMED AND COUNTED RATHER THAN QUIETLY DROPPED. Their findings are
        # real and stay in `findings_total`; what they are not is evidence about a STRATEGY, so
        # they are off the per-strategy ledger and disclosed here instead. A reader who wants the
        # engine's own record reads `findings_by_strategy_effective`; a reader asking what the
        # run produced reads `findings_total`. Neither number is silent about the other.
        "NO_ENGINE_ARMS": sorted(no_engine & {r["label"] for r in results}),
        "no_engine_arm_count": len(no_engine & {r["label"] for r in results}),
        "findings_in_no_engine_arms": sum(len(r.get("findings", [])) for r in results
                                          if r["label"] in no_engine),
        "strategies_that_ran": sorted({r["label"].partition("__")[2] for r in results}),
        "STRATEGY_SPECIFIC_FINDINGS": strategy_specific,
        # THE JOIN DISCLOSURE THE FORMAT BATTERY HAS AND THIS ONE DID NOT. `resume_join` treated
        # every VDS file as a single process, so a resumed run could silently mix arms from two
        # commits -- and `INERT_ARMS`, which compares a carried control's pick_sequence against a
        # fresh arm's, would then read an ENGINE CHANGE BETWEEN COMMITS as a strategy effect, or
        # hide a real one. Same three keys, same names as the format battery's (#126).
        "commit": resume_join.head_commit(),
        "commits_present": resume_join.commits_present(results),
        "carried_forward": [r["label"] for r in results if r.get(resume_join.CARRIED)],
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", default=str(REPORT_PATH))
    parser.add_argument("--only", default="", help="comma-separated arm labels, for a partial run")
    parser.add_argument("--resume", action="store_true",
                        help="reuse arms already in --out instead of re-drafting them")
    args = parser.parse_args(argv)

    scoring = rdb.scoring_settings_from_capture()
    players_db, provenance = rdb.build_players_db_from_capture()
    season_projections = rdb.season_projections_from_capture()
    # #30. {} while the committed capture predates weekly lines, in which case no streaming
    # floor is derived and this battery certifies the board WITHOUT it -- recorded in the report
    # below rather than left for a reader to infer. See weekly_projections_from_capture.
    weekly_projections = rdb.weekly_projections_from_capture()
    merger = dm.DataMerger()

    matrix = vds_battery.vds_matrix(scoring)
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        matrix = [e for e in matrix if e["label"] in wanted]
        if not matrix:
            print(f"no VDS arm matches --only {args.only!r}")
            return 1
    if args.only and args.resume:
        # The format battery's #215 refusal, for the same reason: a resume filtered by --only
        # would rewrite --out from the filtered matrix and DROP every arm outside it. A resume
        # that destroys results is worse than no resume.
        raise SystemExit("REFUSING: --only with --resume would drop every arm outside --only.")

    universe = {
        "players_in_pool": len(players_db),
        "provenance": provenance,
        "season_projections_supplied": len(season_projections),
        "priced_from": "vendor+sleeper" if season_projections else "vendor_only",
        "sleeper_basis": dr.SLEEPER_BASIS_SEASON_SUM if season_projections else None,
        # #30, stated in the report itself: a run with no weekly lines certifies a board with no
        # streaming floor, which is a different claim from one that certifies a board with it.
        "weekly_projection_weeks": len(weekly_projections),
        "streaming_floor_exercised": bool(weekly_projections),
    }

    carried = {r["label"]: r for r in (
        resume_join.carry_forward(args.out, [e["label"] for e in matrix], units_key="results")
        if args.resume else [])}
    commit = resume_join.head_commit()

    started = time.time()
    results: list[dict] = []
    print(f"VDS battery: {len(matrix)} arms "
          f"({len(vds_battery.FORMATS)} formats x {len(vds_battery.STRATEGIES)} strategies)",
          flush=True)
    for entry in matrix:
        if entry["label"] in carried:
            results.append(carried[entry["label"]])
            print(_arm_line(carried[entry["label"]]), flush=True)
            continue
        t0 = time.time()
        audited = draft_battery.run_battery(
            merger, players_db, [entry],
            sleeper_projections=season_projections or None,
            weekly_projections=weekly_projections or None,
            sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)[0]
        audited["seconds"] = round(time.time() - t0, 1)
        audited["format"] = entry["format"]
        audited["strategy"] = entry["strategy"]
        audited[resume_join.PRODUCED_AT] = commit
        audited[resume_join.CARRIED] = False
        results.append(audited)
        print(_arm_line(audited), flush=True)
        # Every arm, not just the last: a multi-hour run must survive a restart (#213b).
        store_io.write(Path(args.out), _report(universe, results, started, complete=False))

    report = _report(universe, results, started, complete=True)
    store_io.write(Path(args.out), report)

    print(f"\n=== VDS battery complete: {report['findings_total']} findings across "
          f"{len(results)} arms, {report['seconds']}s ===")
    if report["INERT_ARMS"]:
        print(f"\nINERT ARMS -- byte-identical to their format's control, so they are NOT")
        print(f"evidence about their strategy ({report['inert_arm_count']} of {len(results)}; "
              f"effective arms {report['effective_arms']}):")
        for label in report["INERT_ARMS"]:
            print(f"   {label}")
    else:
        print("\nNo inert arms: every strategy changed the draft in every format.")
    print("\nfindings by STRATEGY (the axis this battery adds):")
    for name in vds_battery.STRATEGIES:
        marker = "  <- control" if name == vds_battery.CONTROL_STRATEGY else ""
        print(f"   {name:<18}{report['findings_by_strategy'].get(name, 0):>4}{marker}")
    print("\nfindings by FORMAT:")
    for name in vds_battery.FORMATS:
        print(f"   {name:<24}{report['findings_by_format'].get(name, 0):>4}")
    if report["STRATEGY_SPECIFIC_FINDINGS"]:
        print("\nSTRATEGY-SPECIFIC findings -- present under some strategies and not others.")
        print("This is the shape #22 had, and the shape the format battery cannot see:")
        for fmt, strategies in report["STRATEGY_SPECIFIC_FINDINGS"].items():
            print(f"   {fmt:<24}{', '.join(strategies)}")
    else:
        print("\nNo strategy-specific findings: every finding appears under all six strategies "
              "or none.\nThat is a real result, not an empty one -- it says the findings this "
              "battery saw are\nproperties of the format rather than of how the draft was "
              "played.")
    print(f"\n-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
