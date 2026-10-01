"""Where the 1.12 and 6.03 s/pick figures come from, derived from COMMITTED artifacts.

No engine runs. Reads the shard reports the v4 battery force-added
(`evidence/batteries/shards/`) and every committed historical battery report, and recomputes
each report's own two per-pick rates:

    seconds / picks        -- what `report["seconds"]` divided by `report["picks"]` gives.
                              `seconds` is ONE PROCESS's wall clock for its own arm loop
                              (`time.time() - started` in run_draft_battery._battery_report).
    sum(arm seconds)/picks -- the same rate built from each arm's OWN measured duration.

The two disagree in exactly two situations, and both are present in this project's record:

  --resume: `started` is reset to NOW, so a resumed run's `seconds` covers only the arms IT
            drafted while `picks` counts every arm in the report. `v2_acting_now.json` is the
            worked example: 29 of 36 arms carried forward, 0.52 s/pick reported against 2.34
            s/pick actually measured.

  sharding: the merged report's `seconds` is the SUM of several CONCURRENT processes' wall
            clocks, each inflated by however much the others contended for the box.

    PYTHONPATH=. python3 evidence/performance/probes/figure_provenance.py
"""
import glob
import json
import os
import sys

SHARDS = "evidence/batteries/shards"
BATTS = "evidence/batteries"


def row(path, d):
    arms = d.get("results") or []
    picks = d.get("picks") or 0
    sec = d.get("seconds") or 0.0
    arm_sec = sum(a.get("seconds", 0) or 0 for a in arms)
    carried = d.get("carried_forward") or []
    return {
        "file": os.path.basename(path), "formats": d.get("formats"), "picks": picks,
        "report_seconds": round(sec, 1), "sum_arm_seconds": round(arm_sec, 1),
        "s_per_pick_from_report": round(sec / picks, 3) if picks else None,
        "s_per_pick_from_arms": round(arm_sec / picks, 3) if picks else None,
        "n_arms_carried_forward": len(carried), "n_arms_in_report": len(arms),
        "complete": d.get("complete"), "commits_present": d.get("commits_present"),
    }


def main():
    print("REPO ROOT:", os.getcwd())
    shards = []
    for p in sorted(glob.glob(f"{SHARDS}/*.json")):
        shards.append(row(p, json.load(open(p))))

    print("\n=== THE v4 CANDIDATE'S 53-ARM BATTERY: SIX SHARD REPORTS, THREE AT A TIME ===")
    print(f"{'shard':15s} {'arms':>5s} {'picks':>6s} {'report_s':>10s} {'sum_arm_s':>10s} {'s/pick':>7s}")
    for r in shards:
        print(f"{r['file'][:15]:15s} {r['n_arms_in_report']:5d} {r['picks']:6d} "
              f"{r['report_seconds']:10.1f} {r['sum_arm_seconds']:10.1f} "
              f"{r['s_per_pick_from_report']:7.2f}")
    n_arms = sum(r["n_arms_in_report"] for r in shards)
    n_picks = sum(r["picks"] for r in shards)
    tot = sum(r["report_seconds"] for r in shards)
    # n printed for every population.
    print(f"\nn_shard_files={len(shards)}  n_arms={n_arms}  n_picks={n_picks}")
    print(f"SUM of the six shard wall clocks = {tot:.1f}s")
    print(f"  / {n_picks} picks = {tot/n_picks:.3f} s/pick   <-- the 6.03 figure")
    # The three-at-a-time structure: shard_N and shard_Nb are two PHASES of shard N.
    phase_a = [r for r in shards if not r["file"].split(".")[0].endswith("b")]
    phase_b = [r for r in shards if r["file"].split(".")[0].endswith("b")]
    wall = max(r["report_seconds"] for r in phase_a) + max(r["report_seconds"] for r in phase_b)
    print(f"\nn_concurrent_shards_per_phase={len(phase_a)} (phase a), {len(phase_b)} (phase b)")
    print(f"ELAPSED wall clock, if each phase's three shards ran concurrently")
    print(f"  = max(phase a) + max(phase b) = {max(r['report_seconds'] for r in phase_a):.1f}"
          f" + {max(r['report_seconds'] for r in phase_b):.1f} = {wall:.1f}s")
    print(f"  / {n_picks} picks = {wall/n_picks:.3f} s/pick of ELAPSED time")
    print(f"\nRATIO sum-of-process-wall-clock : elapsed = {tot/wall:.2f}x")

    print("\n=== EVERY COMMITTED BATTERY REPORT: THE TWO RATES SIDE BY SIDE ===")
    print(f"{'file':52s} {'arms':>4s} {'picks':>6s} {'rep_s':>9s} {'arm_s':>9s} "
          f"{'s/pk_rep':>8s} {'s/pk_arm':>8s} {'carried':>7s}")
    hist = []
    for p in sorted(glob.glob(f"{BATTS}/*.json")):
        d = json.load(open(p))
        if not isinstance(d, dict) or "picks" not in d:
            continue
        r = row(p, d)
        hist.append(r)
        print(f"{r['file'][:52]:52s} {r['n_arms_in_report']:4d} {r['picks']:6d} "
              f"{r['report_seconds']:9.1f} {r['sum_arm_seconds']:9.1f} "
              f"{r['s_per_pick_from_report']:8.2f} {r['s_per_pick_from_arms']:8.2f} "
              f"{r['n_arms_carried_forward']:7d}")
    clean = [r for r in hist if r["n_arms_carried_forward"] == 0]
    print(f"\nn_committed_reports={len(hist)}  "
          f"n_with_no_carried_forward_arms={len(clean)}")
    if clean:
        rates = sorted(r["s_per_pick_from_arms"] for r in clean)
        print(f"SERIAL, UNRESUMED s/pick across those {len(clean)}: "
              f"min={rates[0]:.2f} median={rates[len(rates)//2]:.2f} max={rates[-1]:.2f}")
    print("\nNOTE: the v3-freeze 53-arm report JSON is NOT in the repository. BATTERY_REPORT.json")
    print("is gitignored and only the v4 candidate's shards were force-added, so the 1.12 s/pick")
    print("figure cannot be re-derived from committed artifacts. What IS committed about that run")
    print("is evidence/batteries/V2_REPAIRS_BATTERY.md, which records 2920.2s for the same 9336")
    print("picks (= 0.313 s/pick) and states 51 of 53 arms were CARRIED FORWARD -- i.e. its")
    print("`seconds` covers the 2 arms that process actually drafted.")
    json.dump({"shards": shards, "history": hist,
               "sum_shard_wall_clock": tot, "n_picks": n_picks,
               "s_per_pick_sum": tot / n_picks, "elapsed_estimate": wall,
               "s_per_pick_elapsed": wall / n_picks},
              open("/tmp/claude-0/-home-user-The-Dynasty-Collective/"
                   "10effc91-a7fc-5b98-9620-9430e59a7fac/scratchpad/perf/PROVENANCE.json", "w"),
              indent=1)


if __name__ == "__main__":
    sys.exit(main())
