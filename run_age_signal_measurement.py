"""#142: how much dynasty aging signal reaches universal_value, and how much does not.

WHY THIS IS A MEASUREMENT AND NOT A WIRING. `age` was on #142's orphan list -- present in the
source, read by nothing -- and the obvious move was to add it as a term. This exists because
the measurement says that would not fix what is actually wrong, and a term added anyway would
be a magnitude nobody could justify (#56) sitting next to the real problem.

WHAT IT MEASURES, in three steps, each of which corrects the one before:

  1. THE RAW CORRELATION IS A TRAP. Within position, r(age, trade_value) is +0.05 for QB,
     -0.02 for RB, +0.12 for WR. On its face: the dynasty market does not price age, which
     would be absurd. Two confounds push the same way -- the young cohort is full of unproven
     depth, and the old cohort is survivorship-filtered to players good enough to still be
     rostered at 30 -- and together they cancel the real effect almost exactly. Reporting that
     number as "age does not matter" is the error this script exists to not make.

  2. CONTROL FOR CURRENT PRODUCTION AND THE SIGNAL IS ENORMOUS. Comparing players projected
     to score the SAME this season, the partial correlation is -0.50 (QB), -0.68 (RB), -0.52
     (WR), -0.55 (TE). The vendor's dynasty price carries a very large aging discount. The
     matched pairs are blunter than any coefficient: D Henry at 32 projected for 262 points is
     priced at 26 while O Hampton at 23 projected for 254 is priced at 73.

  3. ALMOST NONE OF IT REACHES universal_value. bpa is Value Over Replacement in raw projected
     POINTS -- deliberately, and for good reasons that are not in question here -- and points
     are a current-season quantity carrying no aging discount at all. The only channel left is
     time_horizon_adj, which is clamped to +/-10 on a universal_value scale spanning ~500. On
     same-position pairs within 15 projected points where the market prefers the younger
     player, the engine agrees 63.2% of the time overall and 51.5% -- a coin flip -- at age
     gaps of nine years or more, which is exactly where the market is most certain.

WHAT THAT IMPLIES, AND WHAT IT DOES NOT. It does NOT imply "add an age term". A fourth bounded
additive nudge cannot close a 4-9x pricing gap, and choosing a bound large enough to try would
be inventing the magnitude the horizon layer already failed to justify. It DOES say the dynasty
horizon layer is undersized against its own market, which is #50's subject (the VOR/
replacement/horizon redefinition) and #81's contract. This script is the evidence that work
should be held to, and is written to be re-run after it.

Run:  python3 run_age_signal_measurement.py
"""

from __future__ import annotations

import argparse
import itertools
import sys
from typing import Optional

POSITIONS = ("QB", "RB", "WR", "TE")
NEAR_PROJECTION = 15.0     # "the same player, as far as a points anchor can tell"


def _partial(frame, a: str, b: str, control: str) -> float:
    """Correlation of a and b with `control` held fixed -- the whole point of this script.

    Written out rather than pulled from a stats package: it is three correlations and a
    division, and a reader checking whether the headline claim is sound should be able to see
    the arithmetic that produced it without leaving the file.
    """
    r_ab, r_ac, r_bc = frame[a].corr(frame[b]), frame[a].corr(frame[control]), frame[b].corr(frame[control])
    denominator = ((1 - r_ac ** 2) * (1 - r_bc ** 2)) ** 0.5
    return (r_ab - r_ac * r_bc) / denominator if denominator else float("nan")


def aged_frame(merger):
    """The valuation frame with `age` attached, joined on the merger's own name key.

    age arrives on external_values, never on the valuation frame, which is the mechanical
    reason nothing had read it: the two tables are joined nowhere else on this path.
    """
    external, projections = merger.external_values, merger.projections
    if external.empty or "age" not in external.columns:
        return None
    ages = external[external["age"].notna()][["_name_key", "age"]].drop_duplicates(subset=["_name_key"])
    frame = projections.merge(ages, on="_name_key", how="left")
    return frame[frame["age"].notna()]


def coverage(frame, projections) -> dict:
    """Where age reaches and where it does not -- reported per position, because a signal
    present for RB and absent for TE biases BETWEEN positions, which is worse than a signal
    absent everywhere."""
    out = {}
    for position, group in projections.groupby("position"):
        have = frame[frame["position"] == position]
        out[str(position)] = (len(have), len(group))
    return out


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--quiet", action="store_true", help="totals only")
    args = parser.parse_args(argv)

    import data_merger as dm
    import draft_room as dr

    merger = dm.DataMerger()
    frame = aged_frame(merger)
    if frame is None or frame.empty:
        print("no `age` column reaches the valuation frame -- nothing to measure")
        return 1

    print("COVERAGE -- where age actually reaches the valuation frame")
    for position, (have, total) in sorted(coverage(frame, merger.projections).items(),
                                          key=lambda kv: -kv[1][1]):
        print(f"  {position:5} {have:4}/{total:4}  ({100 * have / total:5.1f}%)")
    print("  The gap is IDP and DEF -- the same supply gap #51 ruled is an input problem.\n")

    priced = frame[frame["trade_value"].notna() & frame["projection"].notna()]
    print("STEP 1/2 -- the raw correlation, and the same question with production held fixed")
    print(f"  {'pos':5} {'n':>4} {'r(age,tv)':>11} {'partial | projection':>22}")
    for position in POSITIONS:
        group = priced[priced["position"] == position]
        if len(group) < 20:
            continue
        print(f"  {position:5} {len(group):>4} {group['age'].corr(group['trade_value']):>+11.3f} "
              f"{_partial(group, 'age', 'trade_value', 'projection'):>+22.3f}")
    print("  A near-zero raw number beside a large partial one is the survivorship confound,")
    print("  not evidence about aging. Read the second column.\n")

    print("STEP 3 -- does that discount survive into universal_value?")
    players_db, pid = {}, 0
    for _, row in merger.projections.iterrows():
        pid += 1
        parts = str(row["name"]).split()
        players_db[str(pid)] = {
            "first_name": parts[0] if parts else "",
            "last_name": " ".join(parts[1:]) or (parts[0] if parts else ""),
            "position": row["position"], "fantasy_positions": [row["position"]],
            "team": row.get("team"),
        }
    league = {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"] + ["BN"] * 5,
              "total_rosters": 12, "settings": {"type": 2}}
    board = dr.compute_draft_board(merger, players_db, [], my_roster_id=None,
                                   league=league, mode="balanced")
    value_of = {r["name"]: r["universal_value"] for r in board
                if r.get("universal_value") is not None}

    rows = [r for _, r in priced.iterrows()
            if r["name"] in value_of and r["position"] in POSITIONS]
    buckets = {"0-2": (0, 2), "3-5": (3, 5), "6-8": (6, 8), "9+": (9, 99)}
    tally = {key: [0, 0, 0.0] for key in buckets}
    for first, second in itertools.combinations(rows, 2):
        if first["position"] != second["position"]:
            continue
        if abs(first["projection"] - second["projection"]) > NEAR_PROJECTION:
            continue
        gap = abs(first["age"] - second["age"])
        if gap < 1:
            continue
        young, old = (first, second) if first["age"] < second["age"] else (second, first)
        # Only pairs the MARKET has an opinion about. Where it prices them level there is
        # nothing for the engine to agree or disagree with, and counting those would dilute
        # the rate toward 50% for a reason that has nothing to do with age.
        if young["trade_value"] <= old["trade_value"]:
            continue
        key = next(k for k, (lo, hi) in buckets.items() if lo <= gap <= hi)
        entry = tally[key]
        entry[1] += 1
        entry[0] += value_of[young["name"]] > value_of[old["name"]]
        entry[2] += young["trade_value"] / max(old["trade_value"], 0.1)

    print(f"  Same-position pairs within {NEAR_PROJECTION:.0f} projected points where the market")
    print("  prefers the YOUNGER player -- does the engine rank him higher too?")
    print(f"  {'age gap':>8} {'pairs':>6} {'engine agrees':>14} {'mean market ratio':>18}")
    for key, (agree, total, ratio) in tally.items():
        if not total:
            continue
        print(f"  {key:>8} {total:>6} {100 * agree / total:>13.1f}% {ratio / total:>17.2f}x")
    total = sum(t[1] for t in tally.values())
    agreed = sum(t[0] for t in tally.values())
    if not total:
        print("\n  no comparable pairs found -- this run measured nothing")
        return 1
    print(f"\n  overall {agreed}/{total} = {100 * agreed / total:.1f}%")
    print(f"  universal_value spans {min(value_of.values()):.0f} to {max(value_of.values()):.0f}; "
          f"time_horizon_adj is clamped to {dr.TIME_HORIZON_CLAMP}.")
    print("\n  The rate FALLING as the age gap widens is the signature that matters: where the")
    print("  market is most certain, the engine is least aligned. A signal being read weakly")
    print("  would show a flat rate; one not being read shows this.")
    print("\n  NOT a prompt to add an age term -- see this module's docstring. It is evidence")
    print("  for #50/#81, the dynasty horizon layer's own magnitude.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
