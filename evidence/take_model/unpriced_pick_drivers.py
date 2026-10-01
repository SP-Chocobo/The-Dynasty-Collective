"""#206: what actually drives a real drafter to take a player the engine could not price?

WHY THIS EXISTS. The value-share take model beats the rank table on every board-rank band
(evidence/survival_calibration/VALUE_MODEL_RESULT.md) and STILL loses to a constant, and the
whole remaining gap is the unpriced block: 638 rows carrying RANK_TAKE_PROBABILITY_FLOOR each
outweigh the entire priced board by 2.0x-3.4x. So the block needs a share that is DERIVED
rather than inherited from a constant whose unit belongs to the old model.

THE RECOMMENDATION THIS FILE WAS BUILT TO TEST, AND REFUTES. The proposal was to derive that
share from ROSTER STATE: unpriced rows sit at positions whose starter demand is met, so a rival
takes one when their pick is a depth pick rather than a starter pick. That is a mechanism, it is
computable from quantities the engine already holds (`remaining_starter_demand`), and it is
WRONG.

WHAT THE MEASUREMENT SAYS. 301 resolved picks from the real Greatest Show on Paper 2 board, 31
of which took a player absent from the picking team's priced board.

  * ONSET IS SHARP AND LATE. Rounds 1-13: 0 of 135 picks unpriced. Round 14 onward: 31 of 166.
    Whatever the driver is, it does not exist for the first thirteen rounds.
  * ROSTER STATE LOOKS SIGNIFICANT AND IS NOT. Pooled over the late regime, teams taking an
    unpriced player carried 0.474 less remaining starter demand (permutation p = 0.0158). Split
    by position that contrast DISSOLVES: p = 0.1310 among QB picks, p = 0.1759 among non-QB
    picks. It is Simpson's paradox -- the pooled effect is the position MIX, not roster state.
    The recommendation is WITHDRAWN on this evidence.
  * THE DRIVER IS POSITIONAL, AND THE ENGINE ALREADY HAS A NAME FOR IT. 17 of the 31 are
    quarterbacks, in a SUPERFLEX league. Of late-round QB picks, 70.8% took an unpriced player;
    of late-round non-QB picks, 9.9% did. That is a 7x difference and it is the population
    `#168` and `#185` already describe: QBs past the startable floor, which the engine
    deliberately refuses to price because no remaining QB clears the threshold -- while the
    SUPER_FLEX slot means a rival can still start one.

WHAT FOLLOWS, and it moves the repair to a different layer. The unpriced block's take share is
not a take-model parameter waiting for a derivation. It is the SHADOW OF A PRICING GAP. Rows
the engine declines to price are drafted at 7x the rate elsewhere precisely because they are
startable in a slot the pricing does not model. Inventing a take probability for them would put
a number on the consequence while leaving the cause in place -- and any such number, on this
evidence, could only come from this one capture, which its own LIMITS forbid.

LIMITS, binding and stated before the numbers can be misused: ONE league; 31 events; a data
point for testing, NOT a benchmark. No engine constant may be calibrated to it. This file
REFUTES a proposed mechanism and RELOCATES the question. It does not set anything.

Run from the repo root. NEVER cd first.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/take_model/unpriced_pick_drivers.py
"""
from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

import draft_room as dr

RULES = Path("data/league_captures/greatest_show_on_paper_2.json")
TAKES = Path("evidence/take_model/observed_take_distribution.json")
OUT = Path("evidence/take_model/unpriced_pick_drivers.json")

#: Fixed before the first run and never varied. A seed searched over is a search.
SEED = 20260916
SHUFFLES = 20000
LATE_FROM = 14


def _permutation_p(pool: list[dict], rng: random.Random) -> tuple:
    """One-sided permutation test on mean remaining starter demand, unpriced vs priced.

    Chosen over a t-test because n is 31 and the quantity is a bounded, heavily zero-inflated
    count -- normality is not available and assuming it would be the whole finding."""
    unpriced = [r["demand"] for r in pool if r["unpriced"]]
    priced = [r["demand"] for r in pool if not r["unpriced"]]
    if not unpriced or not priced:
        return None, None, len(unpriced), len(priced)
    observed = sum(unpriced) / len(unpriced) - sum(priced) / len(priced)
    every, k = [r["demand"] for r in pool], len(unpriced)
    hits = 0
    for _ in range(SHUFFLES):
        sample = rng.sample(every, k)
        if sum(sample) / k - (sum(every) - sum(sample)) / (len(every) - k) <= observed:
            hits += 1
    return round(observed, 4), hits / SHUFFLES, k, len(priced)


def main() -> int:
    rules = json.loads(RULES.read_text())
    rows = json.loads(TAKES.read_text())["rows"]
    slots = dr.starter_slot_counts(list(rules["roster_positions"]), None,
                                   int(rules["total_rosters"]))

    # Each team's own filled-by-position, rebuilt in pick order, so the demand recorded against
    # a pick is the demand that team carried WHEN IT PICKED -- not at the end.
    filled: dict[str, Counter] = {}
    recs: list[dict] = []
    for row in sorted(rows, key=lambda r: r["pick_no"]):
        mine = filled.setdefault(row["seat"], Counter())
        recs.append({
            "round": row["round"],
            "demand": sum(max(slots.get(p, 0.0) - mine.get(p, 0), 0.0) for p in slots),
            "position": (row.get("position") or "").upper(),
            "unpriced": row["rank"] is None,
        })
        if recs[-1]["position"]:
            mine[recs[-1]["position"]] += 1

    rng = random.Random(SEED)
    late = [r for r in recs if r["round"] >= LATE_FROM]
    strata = {
        "late_all_positions": late,
        "late_QB_only": [r for r in late if r["position"] == "QB"],
        "late_non_QB": [r for r in late if r["position"] != "QB"],
    }
    report = {
        "league": rules["league"], "LIMITS": (
            "ONE league, 31 events. Refutes a proposed mechanism and relocates the question. "
            "Sets nothing. No engine constant may be calibrated to it."),
        "seed": SEED, "shuffles": SHUFFLES, "late_regime_from_round": LATE_FROM,
        "picks_resolved": len(recs),
        "picks_unpriced": sum(1 for r in recs if r["unpriced"]),
        "by_round_band": {}, "by_position": {}, "roster_state_contrast": {},
    }

    print(f"{rules['league']}: {len(recs)} resolved picks, "
          f"{report['picks_unpriced']} took an unpriced player\n")
    print(f"{'rounds':<10}{'picks':>7}{'unpriced':>10}{'rate':>9}")
    for lo, hi in ((1, 6), (7, 13), (14, 19), (20, 24), (25, 30)):
        band = [r for r in recs if lo <= r["round"] <= hi]
        u = sum(1 for r in band if r["unpriced"])
        rate = (u / len(band)) if band else None
        report["by_round_band"][f"{lo}-{hi}"] = {"picks": len(band), "unpriced": u, "rate": rate}
        print(f"{f'{lo}-{hi}':<10}{len(band):>7}{u:>10}{(rate or 0):>8.1%}")

    print(f"\n{'position':<10}{'late picks':>12}{'unpriced':>10}{'rate':>9}")
    for pos in sorted({r["position"] for r in late if r["position"]}):
        band = [r for r in late if r["position"] == pos]
        u = sum(1 for r in band if r["unpriced"])
        report["by_position"][pos] = {"late_picks": len(band), "unpriced": u,
                                      "rate": u / len(band) if band else None}
        print(f"{pos:<10}{len(band):>12}{u:>10}{(u/len(band) if band else 0):>8.1%}")

    print(f"\nROSTER-STATE CONTRAST (mean remaining starter demand, unpriced minus priced)")
    print(f"{'stratum':<24}{'n':>6}{'unpriced':>10}{'diff':>9}{'perm p':>9}")
    for name, pool in strata.items():
        diff, p, k, n_priced = _permutation_p(pool, rng)
        report["roster_state_contrast"][name] = {
            "n": len(pool), "unpriced": k, "priced": n_priced, "mean_diff": diff, "perm_p": p}
        print(f"{name:<24}{len(pool):>6}{k:>10}"
              f"{(f'{diff:+.3f}' if diff is not None else '--'):>9}"
              f"{(f'{p:.4f}' if p is not None else '--'):>9}")

    pooled = report["roster_state_contrast"]["late_all_positions"]["perm_p"]
    qb = report["roster_state_contrast"]["late_QB_only"]["perm_p"]
    non = report["roster_state_contrast"]["late_non_QB"]["perm_p"]
    dissolves = pooled is not None and qb is not None and non is not None and (
        pooled < 0.05 <= min(qb, non))
    report["roster_state_effect_dissolves_under_stratification"] = dissolves
    report["VERDICT"] = (
        "WITHDRAWN: the pooled roster-state contrast is a position-mix artifact (Simpson's "
        "paradox), not a driver. The real signal is positional -- superflex QBs past the "
        "startable floor -- which makes the unpriced block a PRICING gap (#168/#185), not a "
        "take-model parameter." if dissolves else
        "NOT REFUTED on this run -- re-read before relying on the withdrawal.")
    print(f"\nVERDICT: {report['VERDICT']}")
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
