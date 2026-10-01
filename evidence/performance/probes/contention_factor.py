"""How much does a shard's own wall clock inflate when two siblings share the box?

THE QUANTITY THIS DECOMPOSES. The 6.03 s/pick figure is
`sum(six shard wall clocks) / 9336 picks`, and the v4 battery ran THREE shards concurrently on
four cores in two phases. Two separate things inflate that number against a serial run:

  1. SUMMING. Adding three concurrent processes' wall clocks counts the same elapsed time three
     times over. Measured directly from the committed shard reports
     (probes/figure_provenance.py): sum 56,297.9 s against an elapsed
     max(phase a) + max(phase b) = 19,319.4 s, a ratio of 2.91x.
  2. CONTENTION. Each of those three wall clocks is ALSO longer than the same work would take
     alone, because the siblings compete for cores, memory bandwidth and cache.

(1) is arithmetic over committed artifacts. (2) is what this probe measures, and the two
compose: a sum of three contended wall clocks overstates serial cost by roughly
3 x (contention factor).

METHOD. The same arm, the same pick count, run ALONE; then three identical copies launched
together. Wall clock is taken per process. `n` is printed for every population. Nothing is
compared against a saved baseline from a different run -- both arms are measured here, minutes
apart, in this container.

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:evidence/performance/probes \
      python3 evidence/performance/probes/contention_factor.py <arm> <n_picks> [n_concurrent]

Run from the REPO ROOT. This probe DELIBERATELY saturates the box; nothing else may be running.
"""
import json
import os
import subprocess
import sys
import time

OUT = os.environ.get(
    "PERF_OUT",
    "/tmp/claude-0/-home-user-The-Dynasty-Collective/10effc91-a7fc-5b98-9620-9430e59a7fac/scratchpad/perf")


def one(arm, n_picks, tag):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
               PYTHONPATH=".:evidence/performance/probes", PERF_OUT=OUT)
    return subprocess.Popen(
        [sys.executable, "evidence/performance/probes/draft_cost_curve.py", arm, tag,
         "--picks", str(n_picks)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)


def run(arm, n_picks, k, phase):
    procs = []
    t0 = time.time()
    for i in range(k):
        procs.append((i, one(arm, n_picks, f"{phase}{i}"), time.time()))
    walls = []
    for i, p, started in procs:
        p.communicate()
        walls.append(round(time.time() - started, 2))
    elapsed = time.time() - t0
    return walls, elapsed


def main():
    arm = sys.argv[1]
    n_picks = int(sys.argv[2])
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    os.makedirs(OUT, exist_ok=True)
    print(f"n_cores={os.cpu_count()}  arm={arm}  n_picks_per_process={n_picks}", flush=True)

    print("\n--- ALONE: one process, nothing else running ---", flush=True)
    solo, solo_elapsed = run(arm, n_picks, 1, "solo")
    print(f"n_processes=1  wall_clocks={solo}  elapsed={solo_elapsed:.1f}s", flush=True)

    print(f"\n--- CONCURRENT: {k} identical processes launched together ---", flush=True)
    conc, conc_elapsed = run(arm, n_picks, k, "conc")
    print(f"n_processes={k}  wall_clocks={conc}  elapsed={conc_elapsed:.1f}s", flush=True)

    s = solo[0]
    mean_c = sum(conc) / len(conc)
    print(f"\nALONE       wall clock        = {s:.1f}s  ({s/n_picks:.3f} s/pick)")
    print(f"CONCURRENT  mean wall clock    = {mean_c:.1f}s  ({mean_c/n_picks:.3f} s/pick)"
          f"   n={len(conc)}")
    print(f"CONTENTION FACTOR (per process) = {mean_c/s:.2f}x")
    print(f"\nSUM of the {k} concurrent wall clocks = {sum(conc):.1f}s")
    print(f"  over the {k*n_picks} picks they drafted = {sum(conc)/(k*n_picks):.3f} s/pick"
          f"   <-- the shape of the 6.03 figure")
    print(f"ELAPSED for the same {k*n_picks} picks   = {conc_elapsed:.1f}s"
          f" = {conc_elapsed/(k*n_picks):.3f} s/pick")
    print(f"\nOVERSTATEMENT of serial cost by summing contended shards = "
          f"{(sum(conc)/(k*n_picks)) / (s/n_picks):.2f}x")
    json.dump({"arm": arm, "n_picks": n_picks, "n_concurrent": k, "n_cores": os.cpu_count(),
               "solo_wall": solo, "solo_elapsed": solo_elapsed,
               "concurrent_walls": conc, "concurrent_elapsed": conc_elapsed,
               "contention_factor": mean_c / s,
               "sum_over_picks": sum(conc) / (k * n_picks),
               "solo_per_pick": s / n_picks},
              open(f"{OUT}/CONTENTION_{arm}_{n_picks}.json", "w"), indent=1)
    print(f"\nWROTE {OUT}/CONTENTION_{arm}_{n_picks}.json", flush=True)


if __name__ == "__main__":
    main()
