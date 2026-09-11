"""#175 Q1/Q2/Q3: does the cliff ratio's null-crossing survive the battery, and is it real?

RUN FROM THE REPO ROOT.

This probe exists because the FIRST #175 measurement used the WRONG NULL, and the error
was invisible in the numbers -- they looked plausible either way.

    detect_positional_cliff does NOT divide by a plain median of adjacent gaps. Its yardstick
    (pick_synthesis.py) drops zero gaps, drops the target's OWN gap, and TRIMS the largest
    ~10% before taking the median. Every one of those shrinks the denominator, so every ratio
    is inflated relative to a plain-median ratio. The closed form P(X >= r*med) = 2^-r is the
    null for an estimator this engine does not use.

    Simulated on memoryless (exponential) gaps, the ENGINE'S OWN estimator returns 22.3%
    exceedance at r=2.5, not 17.7%. Using 2^-r understates the null by ~1.26x there and
    ~1.5x at r=4.0 -- and it is the tail where the first pass claimed to find structure.

So the null here is SIMULATED THROUGH THE ENGINE'S OWN ESTIMATOR, at the pool size actually
observed, rather than taken from a closed form.

THE THREE QUESTIONS (owner, this session), and what each is answered with:

  Q1 stability   -- per-format, per-position exceedance vs. its own simulated null; a
                    "crossing" is the smallest r on the grid where observed/null >= 1. If no
                    crossing exists, that is the answer, not a gap in the table.
  Q2 power       -- for each pool, the minimum enrichment detectable at 80% power, one-sided
                    alpha=0.05, GIVEN THAT POOL'S ACTUAL n. Printed next to n so an
                    underpowered cell cannot be read as a null result.
  Q3 recognition -- the players bracketing the largest-ratio gaps, with positional rank, so a
                    human can say whether the crossing lands where a human would put a cliff.

PRE-REGISTERED, before the real boards were built:
  P1. The engine-estimator null exceeds 2^-r at every r (VERIFIED by simulation already).
  P2. Under the corrected null, the r=4.0 enrichment reported by the first pass as 1.21x
      falls BELOW 1.0. If it does not, the first pass's tail claim survives and I say so.
  P3. Most positional pools are too small for 80% power against a 1.2x enrichment at r>=3.
FALSIFIER for the whole framing: if a majority of arms show a stable crossing at a common r
with adequate power, then a global CLIFF_HIGH_RATIO IS derivable and #175 gets a value.

NO CONSTANT IS CHANGED BY THIS FILE. It measures; the ruling is the owner's.
"""
import json, random, statistics, collections, math
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb
import pick_synthesis as ps

random.seed(20260911)
GRID = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
NULL_REPS = 3000


# ---------------------------------------------------------------------------------------
# The yardstick, lifted from the engine rather than re-described.
# ---------------------------------------------------------------------------------------
def engine_typical_gap(gaps, idx):
    """pick_synthesis.detect_positional_cliff's yardstick rule, applied to a gap list.

    Kept in lock-step with the engine by test_cliff_null_estimator.py, which drives the real
    detect_positional_cliff and this function over the same board and requires the ratios to
    agree. A private copy that silently drifts is the exact failure this probe is about.
    """
    other = sorted(g for i, g in enumerate(gaps) if i != idx and g > 0)
    if not other:
        return None
    if len(other) >= 10:
        trim = max(1, round(len(other) * 0.1))
        other = other[:len(other) - trim]
    return other[len(other) // 2]


def ratios_from_gaps(gaps):
    out = []
    for i in range(len(gaps)):
        t = engine_typical_gap(gaps, i)
        if t and t > 0:
            out.append(gaps[i] / t)
    return out


def simulated_null(n_gaps, zero_rate, reps=NULL_REPS):
    """Exceedance of the ENGINE'S ratio on memoryless gaps, at this pool's size and tie rate.

    zero_rate injects the observed exact-tie fraction. Ties are not a feature of a continuous
    memoryless model -- they come from the value scale's resolution -- so the null is reported
    BOTH ways (zero_rate as observed, and 0.0) and the sensitivity is printed. Picking one
    silently would be choosing the null that flatters the answer.
    """
    hits = {r: 0 for r in GRID}
    total = 0
    for _ in range(reps):
        gaps = [0.0 if random.random() < zero_rate else random.expovariate(1.0)
                for _ in range(n_gaps)]
        for x in ratios_from_gaps(gaps):
            total += 1
            for r in GRID:
                if x >= r:
                    hits[r] += 1
    if total == 0:
        return None
    return {r: hits[r] / total for r in GRID}


def min_detectable_enrichment(n, p0, power=0.80, alpha=0.05):
    """Smallest true enrichment e (so p1 = e*p0) a one-sided binomial test of n observations
    detects with `power`. None when p0*e would exceed 1 for any detectable e."""
    if n <= 0 or p0 <= 0 or p0 >= 1:
        return None
    z_a, z_b = 1.6449, 0.8416          # one-sided alpha=0.05, power=0.80
    lo, hi = 1.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2
        p1 = p0 * mid
        if p1 >= 1.0:
            hi = mid
            continue
        need = (z_a * math.sqrt(p0 * (1 - p0)) + z_b * math.sqrt(p1 * (1 - p1))) ** 2 / (p1 - p0) ** 2
        if need <= n:
            hi = mid
        else:
            lo = mid
    return hi if hi < 9.99 else None


# ---------------------------------------------------------------------------------------
# The arms. Real universe (#201), real rulebook (#213), format reaches the merger (the skill).
# ---------------------------------------------------------------------------------------
# NOTHING AT MODULE LEVEL READS A FILE OR BUILDS A LEAGUE. test_cliff_null_estimator.py
# imports this module to drive `engine_typical_gap` against the real detector, and an import
# that read the capture and built eight leagues would put ~a second of board setup, and a
# leaked file handle, inside every one of those tests.
def base_scoring() -> dict:
    with open("data/league_captures/fourth_and_forever.json") as fh:
        cap = json.load(fh)
    return {k: v["value"] for k, v in cap["scoring_settings_observed"].items()}


def arms() -> list[tuple[str, dict]]:
    """The eight arms, built on the REAL rulebook (#213).

    Note what §3 of the finding establishes about these: league size and superflex cannot move
    a single gap, so 12T/10T/14T/SF are one arm's worth of evidence on this quantity, not four.
    They are kept because MEASURING that invariance is the point, not because they are
    independent.
    """
    base = base_scoring()

    def mock(teams, scoring, superflex=False, te_premium=False):
        lg = dr.build_mock_league(teams=teams, superflex=superflex, scoring=scoring,
                                  te_premium=te_premium, dynasty=True, base_scoring=base)
        lg["draft_rounds"] = len(lg["roster_positions"])
        return lg

    return [
        ("12T_standard",  mock(12, "standard")),
        ("12T_half_ppr",  mock(12, "half_ppr")),
        ("12T_ppr",       mock(12, "ppr")),
        ("12T_ppr_SF",    mock(12, "ppr", superflex=True)),
        ("12T_ppr_TEP",   mock(12, "ppr", te_premium=True)),
        ("10T_ppr",       mock(10, "ppr")),
        ("14T_ppr",       mock(14, "ppr")),
        ("HEAVY_IDP", {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX",
                                            "DL", "DL", "LB", "LB", "DB", "DB"] + ["BN"] * 5,
                       "scoring_settings": dict(base), "total_rosters": 12,
                       "settings": {"type": 2}, "draft_rounds": 18}),
    ]


def main():
    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    print(f"universe: {prov['players_in_pool']} players, {len(season)} season projections")
    print(f"null: {NULL_REPS} replicates through the ENGINE'S estimator, per (pool size, tie rate)\n")

    null_cache = {}
    crossings = collections.defaultdict(list)
    all_rows = []

    for label, league in arms():
        merger.set_league_format(db.league_format_hint(league))   # NEVER SKIP (the skill)
        board = dr.compute_draft_board(merger, players_db, [], "1", league,
                                       sleeper_projections=season,
                                       sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        by_pos = collections.defaultdict(list)
        for row in board:
            if row.get("bpa") is not None:          # priced only -- the detector's own rule
                by_pos[row["position"]].append(row)

        print(f"=== {label} ===  board rows {len(board)}, "
              f"bpa-priced {sum(len(v) for v in by_pos.values())}")
        for pos in sorted(by_pos):
            rows = sorted(by_pos[pos], key=lambda r: r["bpa"], reverse=True)
            if len(rows) < ps.CLIFF_MIN_POOL_SIZE:
                continue
            gaps = [rows[i]["bpa"] - rows[i + 1]["bpa"] for i in range(len(rows) - 1)]
            if len(gaps) < 5:
                continue
            obs = ratios_from_gaps(gaps)
            if not obs:
                continue
            zero_rate = sum(1 for g in gaps if g <= 0) / len(gaps)
            key = (len(gaps), round(zero_rate, 2))
            if key not in null_cache:
                null_cache[key] = (simulated_null(len(gaps), round(zero_rate, 2)),
                                   simulated_null(len(gaps), 0.0))
            null_tie, null_cont = null_cache[key]
            if null_tie is None:
                continue

            n = len(obs)
            print(f"  {pos:3} pool={len(rows):3} gaps={len(gaps):3} ties={zero_rate:.0%}  n={n}")
            print(f"      {'r':>4} {'obs':>7} {'null':>7} {'enrich':>7} {'2^-r':>7} "
                  f"{'old enr':>8} {'min-det':>8}")
            crossed = None
            for r in GRID:
                o = sum(1 for x in obs if x >= r) / n
                e = null_tie[r]
                enr = o / e if e > 0 else float("nan")
                cf = 2 ** -r
                old = o / cf
                mde = min_detectable_enrichment(n, e)
                if crossed is None and enr >= 1.0:
                    crossed = r
                print(f"      {r:4.1f} {o:7.3f} {e:7.3f} {enr:7.2f} {cf:7.3f} "
                      f"{old:8.2f} {('%.2fx' % mde) if mde else '   n/a':>8}")
                all_rows.append({"arm": label, "pos": pos, "r": r, "n": n, "obs": o,
                                 "null": e, "null_no_ties": null_cont[r], "enrich": enr,
                                 "old_enrich": old, "min_detectable": mde})
            crossings[pos].append((label, crossed))
            print(f"      crossing: {crossed if crossed is not None else 'NONE on this grid'}")

            # Q3: what the biggest ratios actually are, in football terms.
            top = sorted(range(len(gaps)), key=lambda i: -(gaps[i] / (engine_typical_gap(gaps, i) or 1e9)))[:3]
            for i in top:
                t = engine_typical_gap(gaps, i)
                if not t:
                    continue
                print(f"        ratio {gaps[i]/t:5.2f}  {pos}{i+1} {rows[i].get('name','?')} "
                      f"({rows[i]['bpa']:.1f}) -> {pos}{i+2} {rows[i+1].get('name','?')} "
                      f"({rows[i+1]['bpa']:.1f})")
        print()

    print("=== Q1: is the crossing stable across arms? ===")
    for pos in sorted(crossings):
        vals = [c for _, c in crossings[pos]]
        named = [f"{a}:{c if c is not None else '-'}" for a, c in crossings[pos]]
        n_none = sum(1 for v in vals if v is None)
        print(f"  {pos:3} arms={len(vals)}  no-crossing={n_none}  {' '.join(named)}")

    out = "/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/cliff_null_raw.json"
    json.dump(all_rows, open(out, "w"))
    print(f"\nraw -> {out}  ({len(all_rows)} cells)")


if __name__ == "__main__":
    main()
