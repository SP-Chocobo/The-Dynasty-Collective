"""Is the `adp` seat a STRONG board, or merely a different one?

The owner's freeze condition: losses to `adp` only count as drafting strongly if `adp` is itself
drafting strongly. This tests that instead of asserting it.

The decisive test is NOT "does adp beat the engine" -- it is whether adp beats a points-maximizing
heuristic ON THE POINTS RULER. `points_need` takes the highest-projected player at a position it
still needs to start, which is greedy maximization of the very quantity `points` scores. If adp
beats it there, adp is encoding real drafting knowledge (positional scarcity, lineup shape) that
the projection sheet alone does not, and it is a strong opponent. If adp merely ties or trails it,
a tie with adp says much less.
"""
import json
import statistics
import sys

sys.path.insert(0, ".")

d = json.load(open("evidence/smoke_seats/SMOKE_SEATS_2026-09-17_9273a2c.json"))
CLEAN = {"12T_ppr", "10T_ppr", "12T_ppr_TEP"}      # the 1QB PPR arms where adp is correctly specified

print(f"commit {d['commit']} | formats {d['formats']}\n")
for r in d["results"]:
    rows = {}
    eng = []
    for run in r["seat_runs"]:
        eng.append(run["engine"]["points"]["starter_value"])   # `points` = what you FIELD
        for style, rec in run["by_style"]["points"].items():
            rows.setdefault(style, []).append(rec["style_mean"])
    engine_mean = statistics.mean(eng)
    order = sorted(rows, key=lambda s: -statistics.mean(rows[s]))
    tag = "CLEAN" if r["label"] in CLEAN else "adp mis-specified"
    print(f"== {r['label']:14} ({tag})")
    for i, style in enumerate(order, 1):
        m = statistics.mean(rows[style])
        print(f"   {i}. {style:12} {m:8.2f}")
    print(f"      ENGINE       {engine_mean:8.2f}")
    if "adp" in rows and "points_need" in rows:
        a, p = statistics.mean(rows["adp"]), statistics.mean(rows["points_need"])
        print(f"   -> adp beats the greedy points-maximiser by {a - p:+7.2f} pts ({(a-p)/p*100:+.2f}%)")
        print(f"   -> engine vs adp: {engine_mean - a:+7.2f} pts ({(engine_mean-a)/a*100:+.2f}%)")
    # seat-to-seat spread, to say whether a sub-1% gap is inside the noise
    sd = statistics.pstdev(eng)
    print(f"   -> engine seat-to-seat spread: sd {sd:.2f} pts over {len(eng)} seats "
          f"(range {max(eng)-min(eng):.2f})")
    print()
