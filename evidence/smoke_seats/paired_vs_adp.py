"""Is the engine's sub-1% gap to `adp` noise, or a small SYSTEMATIC deficit?

Win rates of 5/12 and 2/10 hint the engine is consistently a little behind rather than randomly
scattered, which are different claims. Seat control makes this a PAIRED comparison: in every run
the engine and the adp seats draft the SAME board from the SAME pool, differing only in chair.
So the per-run difference is the right unit, and its own spread is the right noise scale.
"""
import json
import statistics
import sys

sys.path.insert(0, ".")
d = json.load(open("evidence/smoke_seats/SMOKE_SEATS_2026-09-17_9273a2c.json"))
CLEAN = {"12T_ppr", "10T_ppr", "12T_ppr_TEP"}

for r in d["results"]:
    diffs = []
    for run in r["seat_runs"]:
        rec = run["by_style"]["points"].get("adp")
        if rec:
            diffs.append(rec["engine"] - rec["style_mean"])
    if not diffs:
        continue
    n = len(diffs)
    mean = statistics.mean(diffs)
    sd = statistics.stdev(diffs) if n > 1 else float("nan")
    sem = sd / (n ** 0.5)
    wins = sum(1 for x in diffs if x > 0)
    tag = "CLEAN" if r["label"] in CLEAN else "adp mis-spec"
    # how many standard errors from zero -- >2 means a real systematic gap, not chair luck
    t = mean / sem if sem else float("nan")
    print(f"{r['label']:14} ({tag:12}) n={n:2} | engine-minus-adp mean {mean:+8.2f} pts "
          f"| sd {sd:6.2f} | sem {sem:5.2f} | t {t:+6.2f} | engine ahead in {wins}/{n}")
