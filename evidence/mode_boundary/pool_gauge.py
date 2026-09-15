"""#282. A DEPLETING POOL GAUGE -- per position, a fuel tank that only ever goes down.

THE PROBLEM IT EXISTS FOR. The crossing rule (#271-#280) was meant to detect "this pool is
tapped" and does not: its quantity is top-minus-replacement, and BOTH ends move together, so it
is insensitive to absolute depletion. Worse, #276/#277 measured a tight end's headroom REBOUNDING
-- 137 -> 24 -> 17 -> 22 -> 30 -- because bench picks lower the replacement faster than the
best-remaining. A gauge built on that would RISE as the pool empties. #280 recommended against
adopting the rule; this is the thing worth having instead.

THE QUANTITY, and why it depletes where the rule does not. Fix the bar ONCE, at draft open, at
each position's own replacement level; then count the survivors above it. Players can only leave
the pool, so the gauge is MONOTONE NON-INCREASING BY CONSTRUCTION -- it cannot rebound, and that
is a property of the definition rather than a hope about the data. The instrument asserts it
anyway: a gauge that ticked up would mean the bar moved, which is the exact defect #74/#76
removed from bpa on finding a moving ruler carried 94.5% of its movement.

THE BAR IS DERIVED, NOT CHOSEN (#56). Read back out of the engine's own columns at the opening
board -- `level = projected_points - bpa` -- exact and unique per position (verified: one
distinct value each, QB 328.60 / RB 185.64 / TE 172.69 / WR 216.25). Nothing here picks a cutoff.

SELF-NORMALISED PER POSITION, DELIBERATELY UNITLESS (owner's spec). Each tank is full at ITS OWN
opening count, not a shared scale. A QB bar therefore never claims to equal a WR bar in value --
the cross-position comparison #75/#76 found bpa's unit could not support and #229 left undefined
for the deep-bench case. Positions draining at DIFFERENT RATES is the signal, not an artifact.

THE DISPLAY CONTRACT, ruled by the owner and narrower than what this instrument computes:
  SHOW      segments; the band marks; optionally a percentage of the position's own full pool.
  NEVER     raw counts, point values, band sizes, or any engine-internal population.
The count is an INTERNAL quantity -- required to compute the fraction, never surfaced. The owner's
standing objection is why: "2 left above replacement feels obscure to someone who hasn't spent
the last month chatting with you. too technical." A count also invites reasoning about WHICH two
players, which a gauge is not entitled to imply. This module prints what a reader would SEE, so
the evidence and the surface cannot drift apart; the JSON keeps counts for audit only.

THE BANDS, and what they are allowed to say. The owner's vocabulary: ELITE / MID / DEPTH /
MEH -- "there should be points where it's pretty clear, these are the elite, these are the mid
grade, these are the ones that are just meh" -- drawn as at most three marks per tank, because
"if we're only using 2 or 3 of these per position, they need to be significant signals of the
strength of the players above and below them". The mark shows WHERE a boundary is and never how
far the drop is: magnitude stays behind the display contract with the counts and the points.
Two earlier definitions of that boundary were built and both lost on measurement -- see
`band_cuts` for the numbers and for the shape fact that killed the second one.

THE SEGMENTS ARE ARITHMETIC, NOT A THRESHOLD (#56 again). bars = ceil(fraction * BARS), equal
divisions of a derived 0-1 fraction; the only chosen number is how many segments to DRAW, which
touches no valuation. Two properties are load-bearing: any survivor shows at least ONE bar, and
EMPTY means genuinely zero -- never "nearly empty", because a gauge reading empty while a
startable player remains would be lying at the one moment anyone reads it.

Run from the repo root. NEVER cd first -- DataMerger resolves baselines against cwd.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/mode_boundary/pool_gauge.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import league_config as lc
import pick_synthesis as ps
import run_draft_battery as rdb

IN = Path("evidence/mode_boundary/depth_battery.json")
OUT = Path("evidence/mode_boundary/pool_gauge.json")
BARS = 6                    # a display choice only: how many segments the WHOLE tank draws.
SPAN = 16                   # display width across all bands (4 bands x 4 parts each).
STRIDE = 10


def opening_state(rows: list[dict]) -> tuple[dict, dict, dict, dict]:
    """(starter-bar points, the FULL priced pool ordered, its size, EVERY board row per position).

    THE TANK SPANS THE WHOLE PRICED POOL, NOT ONLY THE STARTERS -- owner's ruling, and it
    corrects a defect in #282 that was mine rather than the engine's. That version gated tank
    membership on `bpa > 0`, so the tank held exactly the players above replacement: 92 of 312
    picks in the 12-team arm, 127 of 312 in Fourth and Forever. That population is the league's
    STARTING SLOTS almost exactly (8 starters x 12 = 96 against 92 above the bar; 10 x 12 = 120
    against 127), which is not a coincidence -- replacement level IS the last startable player.
    The gauge therefore went fully dark at pick 130 of 312 and said nothing at all about the
    half of the draft where the calls are hardest. The owner: "that leaves no room for anything
    outside of starters."

    AND THE BAR WAS NEVER FORCED. Below it the projection keeps falling hard -- WR runs
    216 -> 204 -> 188 -> 149 -> 98 -> 62 -> 35 -> 0 and RB 186 -> 142 -> 89 -> 64 -> 32 -> 9 -> 0,
    several of those steps steeper than the ones just above the bar. That is a clean ordering,
    so the deep pool is gradeable and the old boundary was a choice of mine, not a limit.

    A CORRECTION TO #282's OWN WORDING, recorded because it was published: that entry said a
    pick below the bar had "no measured production remaining to pass over." Wrong as stated.
    What is absent below the bar is SURPLUS OVER REPLACEMENT, not production, and the two are
    not the same claim. Production still separates those players cleanly; VOR just cannot
    express it, because VOR is defined against the very level they sit under.

    The bar survives as a MARKER rather than an edge -- it still answers "where do the starters
    end", which is worth drawing, and it is still derived exactly (`projected_points - bpa`,
    read off a row that has a positive bpa so the subtraction is in its own domain).
    """
    level, pool, on_board = {}, {}, {}
    for r in rows:
        pos, bpa, pts = r.get("position"), r.get("bpa"), r.get("projected_points")
        if pos is None:
            continue
        on_board[pos] = on_board.get(pos, 0) + 1          # EVERY row a drafter can see
        if pts is None:
            continue
        if bpa is not None and bpa > 0:
            level.setdefault(pos, round(pts - bpa, 6))
        pool.setdefault(pos, []).append((float(pts), str(r["player_id"])))
    for pos in pool:
        pool[pos].sort(key=lambda t: -t[0])
    ordered = {p: [pid for _, pid in v] for p, v in pool.items()}
    return level, ordered, {p: len(v) for p, v in ordered.items()}, on_board


def coverage(priced: dict, on_board: dict) -> dict:
    """{position: fraction of the rows a drafter can SEE that this gauge can price}.

    THE GAUGE MUST DISCLOSE WHAT IT CANNOT SEE, and it cannot see most of the board. Measured:
    the 12-team offensive board carries 155 QB rows and prices 42 (27%); WR 198 of 452 (44%);
    TE 115 of 256 (45%); RB 126 of 256 (49%). On the HEAVY_IDP arm the board carries 394 DB rows
    and prices 130, 298 LB and prices 83, 219 DL and prices 86 -- roughly a third each.

    STRUCTURALLY CERTAIN: the tank is assembled from priced players only, so it reaches EMPTY
    when the priced ones are gone, whatever number of unpriced rows remain beside them. A tank
    reading empty is therefore the statement "nothing priced remains here", never "nothing
    remains here", and without this disclosure a reader cannot tell those apart.

    NOT ESTABLISHED, and recorded as such rather than asserted: whether any real draft reaches
    that point. Unpriced offensive rows are overwhelmingly third-stringers the absence contract
    correctly excludes and orders last, and no draft measured here has run out of priced players
    at a position. The IDP case is the one to WATCH rather than the one proven -- an IDP league
    requires six defensive starters per team, so its demand sits much closer to its priced supply
    than offence does -- but no IDP draft has been run to check. `#210` is the supply defect
    behind the thin IDP pricing; this function is only the disclosure, not a claim about impact.
    """
    return {p: (priced.get(p, 0) / on_board[p] if on_board.get(p) else 0.0) for p in on_board}


def starter_bar_rank(ordered_points: list[float], bar: float | None) -> int | None:
    """How many players sit at or above the starter line -- the marker's place in the tank.

    None when the position never produced a bar (nothing above replacement to read it from),
    which is the absence contract: a marker that cannot be located is not drawn at rank zero.
    """
    if bar is None:
        return None
    return sum(1 for v in ordered_points if v >= bar)


def segments(remaining: int, opening: int) -> int:
    """Equal divisions of remaining/opening. Any survivor shows >=1 bar; 0 means truly empty."""
    if opening <= 0 or remaining <= 0:
        return 0
    return max(1, math.ceil(BARS * remaining / opening))


BANDS = ("ELITE", "MID", "DEPTH", "MEH")     # the owner's vocabulary; 4 bands = 3 marks


def separation(vals: list[float], cuts: list[int]) -> float:
    """Between-band share of a position's own spread. 0 = these cuts tell you nothing.

    Unitless and self-normalised, so RB's 400-point range and TE's 150 are comparable, and no
    constant is involved. This is the quantity the marks are CHOSEN by and, separately, the
    quantity they are GRADED by on a column that did not choose them -- see the module header.
    """
    n = len(vals)
    if n < 2:
        return 0.0
    mu = sum(vals) / n
    tot = sum((v - mu) ** 2 for v in vals)
    if tot <= 0:
        return 0.0
    edges = [0] + sorted(cuts) + [n]
    return sum(len(vals[a:b]) * (sum(vals[a:b]) / len(vals[a:b]) - mu) ** 2
               for a, b in zip(edges, edges[1:]) if b > a) / tot


def band_cuts(vals: list[float], k: int) -> list[int]:
    """The k cuts that best separate strong players from weak ones. EXACT, and parameter-free.

    THE OWNER'S CRITERION IS THE RULE, not a proxy for it: "if we're only using 2 or 3 of these
    per position, they need to be significant signals of the strength of the players above and
    below them", and then the vocabulary -- "these are the elite, these are the mid grade, these
    are the ones that are just meh". Cuts go where they most divide strength. Nothing is compared
    against a constant, and no band is a fixed share or count -- ELITE measures anywhere from 8%
    to 29% of a pool depending on the position and the league's scoring.

    A GREEDY VERSION SHIPPED FIRST AND WAS WRONG AT RB, caught by the owner reading the sizes:
    "is it really 3 and 4 only for elite and decent rb? I'd think solid would be deeper than
    that." It is. Greedy adds one cut at a time and never revisits, so a steep head captures its
    first cut and the second is then stranded inside a flat run. Fourth and Forever RB drops 47.2
    points from RB3 to RB4 and then runs shallow -- 15, 9, 3, 0.6, 5, 4 -- all the way to RB17.
    Greedy answered 3/4/18/11, cutting at RB7 in the middle of that run; exact answers
    4/13/9/10, cutting at RB17 where the next real step is, and scores HIGHER on projected points
    (93.7% vs 92.8%) which is the column that placed neither. WR and TE were unaffected, and that
    is the tell: the defect only bites where the head is steep enough to capture the first cut.

    Exact via the Fisher/Jenks dynamic program -- minimum total within-band squared deviation for
    exactly k+1 bands. O(k*n^2) on a pool of at most a few dozen, so there is no reason to
    approximate. `k` is display capacity (the owner's "at most 2 or 3"), never a cutoff on what
    counts.
    """
    n = len(vals)
    if k <= 0 or n <= k:
        return []
    pre = [0.0] * (n + 1)
    pre2 = [0.0] * (n + 1)
    for i, v in enumerate(vals):
        pre[i + 1] = pre[i] + v
        pre2[i + 1] = pre2[i] + v * v

    def sse(a: int, b: int) -> float:
        m = b - a
        if m <= 0:
            return 0.0
        tot = pre[b] - pre[a]
        return (pre2[b] - pre2[a]) - tot * tot / m

    inf = float("inf")
    cost = [[inf] * (n + 1) for _ in range(k + 2)]
    back = [[0] * (n + 1) for _ in range(k + 2)]
    for j in range(n + 1):
        cost[1][j] = sse(0, j)
    for bands in range(2, k + 2):
        for j in range(bands, n + 1):
            best, arg = inf, bands - 1
            for t in range(bands - 1, j):
                c = cost[bands - 1][t] + sse(t, j)
                if c < best:
                    best, arg = c, t
            cost[bands][j], back[bands][j] = best, arg
    cuts, j = [], n
    for bands in range(k + 1, 1, -1):
        j = back[bands][j]
        cuts.append(j)
    return sorted(cuts)


def drawable(cuts: list[int], n: int, k: int) -> bool:
    """Can every band this cutting produces actually show partial drain?

    A band drawn across `w` segments but holding fewer than `w` players cannot render a partial
    state -- it jumps from full to empty with nothing in between. That is a DISPLAY CAPACITY
    fact, not a judgment about value, and this repo already treats display capacity as a
    legitimate non-threshold (`SPAN`, the mark cap). Nothing here compares a valuation against a
    constant.
    """
    edges = [0] + list(cuts) + [n]
    per = max(1, SPAN // max(1, k + 1))
    return all((b - a) >= per for a, b in zip(edges, edges[1:]))


def staged_cuts(vals: list[float], k: int) -> tuple[list[int], bool]:
    """(cuts, recursed). One-stage cutting, falling back to two-stage when it cannot be drawn.

    THE DEAD TAIL EATS THE CUT BUDGET, and at one position it eats all of it. Squared-deviation
    cutting chases the largest gulf, which in every pool is the drop from real players to roster
    filler projecting ~20 points. Where the live portion is large relative to that tail the cuts
    still land inside it; where the tail dominates they do not.

    QB is the position where it does. Its top band holds 24 of 42 players -- 57% of the pool,
    against 6-8% for RB, TE and WR -- and one-stage cutting answers 24/8/2/8, spending two cuts
    on tail structure and leaving a TWO-PLAYER band drawn across four segments. Inside that
    24-player band there is real structure it never looked at: gaps of 12.4 and 11.2 points at
    QB3 and QB12, both 3.5x+ the median adjacent gap, and both independently called HIGH by
    `pick_synthesis.detect_positional_cliff`, which uses an unrelated rule.

    TWO-STAGE WAS TESTED AS A GENERAL REPLACEMENT AND LOST. Splitting live/dead first and banding
    the live portion costs separation at every skill position -- TE 94.3% -> 87.4%, WR 93.9% ->
    87.2%, RB 93.7% -> 91.7% -- while at QB it is a wash (96.5% -> 96.3%) and transforms the
    shape from 24/8/2/8 into 12/13/7/10, with its first cut landing exactly on the QB12 cliff. So
    it is NOT the default. It is the fallback, and it is reached only when one-stage produces a
    band too small to draw, which on every arm measured means QB and only QB.
    """
    cuts = band_cuts(vals, k)
    if drawable(cuts, len(vals), k):
        return cuts, False
    split = band_cuts(vals, 1)
    if not split:
        return cuts, False
    inner = band_cuts(vals[:split[0]], k - 1)
    staged = sorted(set(inner + split))
    return (staged, True) if drawable(staged, len(vals), k) else (cuts, False)


def even_cuts(n: int, k: int) -> list[int]:
    """Equal slices -- the CONTROL the bands must beat, not a display option.

    Any monotone cut of an already-sorted list explains most of its variance, so a high
    separation score proves nothing on its own (#245). Arbitrary equal quarters score 82-96% on
    points. The evidence for banding is therefore the MARGIN OVER THIS, never the level.
    """
    return sorted({max(1, min(n - 1, round(n * (j + 1) / (k + 1)))) for j in range(k)})


def band_marks(board: list[dict], pool: dict) -> tuple[dict, dict]:
    """{position: [mark, ...]}, {position: grades} -- band boundaries over the WHOLE priced pool.

    Cut on PROJECTED POINTS rather than `bpa`. Above the bar the two order identically (bpa is
    points minus a per-position constant), but below it bpa collapses toward and past zero while
    points keep separating players cleanly. Points is also the quantity the owner means by a
    production pool, and the one #211 established as the honest measure of quality.

    Fixed at the opening board and never recomputed -- a yardstick re-read against a shrinking
    pool drifts, which is the defect #74/#76 cut out of bpa and #271-#280 found fatal in the
    crossing rule.
    """
    by_id = {str(r["player_id"]): r for r in board}
    marks, grades = {}, {}
    for pos, ids in pool.items():
        vals = [float(by_id[pid]["projected_points"]) for pid in ids]
        if len(vals) < len(BANDS):
            marks[pos], grades[pos] = [], {}
            continue
        cuts, recursed = staged_cuts(vals, len(BANDS) - 1)
        edges = [0] + cuts + [len(vals)]
        out = []
        for name, cut, (a, b) in zip(BANDS[1:], cuts, list(zip(edges, edges[1:]))[1:]):
            out.append({"pid": ids[cut], "rank": cut, "band_below": name, "size": b - a,
                        "mean_points": round(sum(vals[a:b]) / (b - a), 1)})
        marks[pos] = out
        grades[pos] = {
            "staged": recursed,
            "bands_on_points": round(separation(vals, cuts) * 100, 1),
            "even_slices_on_points": round(
                separation(vals, even_cuts(len(vals), len(BANDS) - 1)) * 100, 1),
            "top_band": {"size": edges[1],
                         "mean_points": round(sum(vals[:edges[1]]) / edges[1], 1)},
        }
    return marks, grades


def assign_bands(pool: dict, marks: dict) -> dict:
    """{position: {band: [pid ordered]}} -- every player's place in the spectrum, fixed at build.

    THE OWNER'S SPEC: "let the bands be static, almost assigning each player a spot in the
    spectrum upon build of the roster pool, based on the scoring settings. each league's scoring
    may result in varying placements inside those bands, but their valuation is fairly
    representative of their strength regardless of roster state and others being pulled."

    Static is REQUIRED here, not merely permitted -- see `band_marks` for the moving-yardstick
    defect it avoids. The one case where a static band goes stale is named rather than hidden: a
    mid-draft IR or PUP designation moves a projection under #191's haircut, after the cut.
    """
    members = {}
    for pos, ids in pool.items():
        edges = [0] + [m["rank"] for m in marks.get(pos, [])] + [len(ids)]
        members[pos] = {name: ids[a:b] for name, (a, b) in zip(BANDS, zip(edges, edges[1:]))}
    return members


def band_widths(sizes: dict) -> dict:
    """Segments per band: EQUAL, one slice each, not proportional to how many players it holds.

    PROPORTIONAL WAS BUILT FIRST AND LOST ON THE RENDERING. A small ELITE band draws one or two
    segments -- two or three states in total, unable to express "two of the four elite remain",
    the most decision-relevant fact at the position -- while the band a drafter cares least about
    takes the most room. That inverted attention in every position measured. Equal slices give
    every band the resolution to show partial drain, which is the job.

    The cost, stated because it can be misread: equal slices do not show how many players a band
    holds, and a reader could take four equal slices as four equal groups. They are not -- ELITE
    measures anywhere from 11% to 29% of a pool -- and the display contract forbids the counts
    that would state it precisely anyway.
    """
    live = [n for n in BANDS if sizes.get(n, 0) > 0]
    if not live:
        return {n: 0 for n in BANDS}
    base, extra = divmod(SPAN, len(live))
    width = {n: 0 for n in BANDS}
    for i, n in enumerate(live):
        width[n] = max(1, base + (1 if i < extra else 0))
    return width


def render_bands(sizes: dict, left: dict, bar_seg: int | None = None) -> str:
    """The spectrum: each band drains INSIDE ITS OWN SLICE, never from the front of the tank.

    This is the point of the owner's spec. One fill edge over a COUNT of survivors silently
    assumes the players who left were the ones at the front. For an engine draft that is true --
    it takes best-available within a position by construction, which is why the out-of-band-order
    rate measured 0 of 219 and why that zero is the ENGINE's signature, not evidence about
    drafters. For a human it is false: take a mid-grade tight end early for roster reasons and an
    aggregate bar drains its front, showing the elite gone when the elite is still sitting there.

    `bar_seg` marks the segment holding the STARTER LINE -- where this position stops producing
    starters and begins producing bench. It is drawn INSIDE the tank because it is no longer the
    tank's edge (see `opening_state`). In the built surface it is a hairline between segments;
    ASCII has to spend a cell on it.
    """
    width = band_widths(sizes)
    cells, idx = [], 0
    for n in BANDS:
        w = width[n]
        if w <= 0:
            continue
        rem = left.get(n, 0)
        fill = 0 if rem <= 0 else max(1, math.ceil(w * rem / sizes[n]))
        piece = ["#" if i < fill else "." for i in range(w)]
        for i in range(w):
            if bar_seg is not None and idx + i == bar_seg:
                piece[i] = "!"
        idx += w
        cells.append("".join(piece))
    return "[" + "|".join(cells) + "]"


def classify(order, pos_of, pool, starters):
    """Every pick sorted by where it sat relative to the STARTER LINE, which still means something.

    STARTER   the player was at or above his position's opening starter line.
    BENCH     he was below it -- a real, graded player (the bands cover him), but not one the
              league's starting slots had room for at the opening board.

    #282 called the second state DARK and said no measured production remained. That was WRONG
    AS PUBLISHED and is corrected here: what is absent below the line is SURPLUS OVER
    REPLACEMENT, not production. Production separates those players cleanly -- WR falls
    216 -> 149 -> 98 -> 62 -> 35 below the bar -- which is exactly why the tank now spans them.
    """
    left = {p: set(ids) for p, ids in pool.items()}
    tally = {p: {"starter": 0, "bench": 0, "first_bench": None} for p in left}
    for pick_no, pid in order:
        pos = pos_of.get(pid)
        if pos not in left or pid not in left[pos]:
            continue
        rank = pool[pos].index(pid)
        t = tally[pos]
        sb = starters.get(pos)
        if sb is not None and rank < sb:
            t["starter"] += 1
        else:
            t["bench"] += 1
            if t["first_bench"] is None:
                t["first_bench"] = pick_no
    return tally


def main() -> int:
    battery = json.loads(IN.read_text())["arms"]
    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    base = rdb.scoring_settings_from_capture()
    matrix = {e["label"]: e for e in db.league_matrix(base)}
    report = {"span": SPAN, "stride": STRIDE, "bands": list(BANDS), "arms": {}}
    print(f"universe {prov['players_in_pool']}  season {len(season)}", flush=True)
    print("each tank spans the WHOLE priced pool, cut into four bands that drain independently",
          flush=True)
    print("  #  left   .  gone   !  the segment holding the starter line   |  band edge\n",
          flush=True)

    for label in ("12T_ppr_BN18", "CAPTURE_fourth_and_forever"):
        entry = battery[label]
        if label in matrix:
            league = matrix[label]["league"]
        else:
            lg = dr.build_mock_league(teams=entry["teams"], superflex=False, scoring="ppr",
                                      te_premium=False, dynasty=True, base_scoring=base)
            st = [s for s in lg["roster_positions"] if s != "BN"]
            lg["roster_positions"] = st + ["BN"] * (entry["rounds"] - len(lc.draftable_slots(st)))
            league = lg
        merger.set_league_format(db.league_format_hint(league))          # NEVER SKIP
        order = sorted((x["pick_no"], x["pid"])
                       for ps in entry["rules"]["crossing"]["per_seat"].values() for x in ps)
        board0 = dr.compute_draft_board(merger, players_db, [], "1", league,
                                        sleeper_projections=season,
                                        sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        level, pool, opening, on_board = opening_state(board0)
        seen = coverage(opening, on_board)
        by_id = {str(r["player_id"]): r for r in board0}
        pos_of = {pid: p for p, ids in pool.items() for pid in ids}
        positions = sorted(p for p in opening if opening[p] >= len(BANDS))
        marks, grades = band_marks(board0, pool)
        members = assign_bands(pool, marks)
        sizes = {p: {n: len(members[p][n]) for n in BANDS} for p in positions}
        starters = {p: starter_bar_rank([float(by_id[i]["projected_points"]) for i in pool[p]],
                                        level.get(p)) for p in positions}
        bar_seg = {}
        for p in positions:
            sb, w = starters[p], band_widths(sizes[p])
            if sb is None:
                bar_seg[p] = None
                continue
            edges, idx, seg = [0] + [m["rank"] for m in marks[p]] + [opening[p]], 0, None
            for name, (a, bnd) in zip(BANDS, zip(edges, edges[1:])):
                if a <= sb < bnd and bnd > a:
                    seg = idx + min(w[name] - 1, (sb - a) * w[name] // (bnd - a))
                idx += w[name]
            bar_seg[p] = seg

        print(f"== {label}   {entry['teams']} teams x {entry['rounds']} rounds "
              f"= {entry['teams'] * entry['rounds']} picks", flush=True)
        hdr = {p: f"{p} {'/'.join(str(sizes[p][n]) for n in BANDS)}" for p in positions}
        wide = {p: len(render_bands(sizes[p], sizes[p], bar_seg[p])) for p in positions}
        print(f"   {'pick':>5}  " + "  ".join(f"{hdr[p]:<{wide[p]}}" for p in positions),
              flush=True)

        rows = []
        for n in range(0, len(order) + 1, STRIDE * 2):
            taken = {pid for _, pid in order[:n]}
            row = {"after_picks": n, "_band_left": {}}
            for p in positions:
                row["_band_left"][p] = {nm: sum(1 for pid in members[p][nm] if pid not in taken)
                                        for nm in BANDS}
            rows.append(row)
            print(f"   {n:>5}  " + "  ".join(
                render_bands(sizes[p], row["_band_left"][p], bar_seg[p]) for p in positions),
                flush=True)

        census = classify(order, pos_of, pool, starters)
        report["arms"][label] = {"pool_size": opening, "band_sizes": sizes, "bar_points": level,
                                 "rows_on_board": on_board, "coverage": seen,
                                 "starter_line_rank": starters, "marks": marks, "grades": grades,
                                 "samples": rows, "census": census}
        print("   BANDS graded on their own points vs arbitrary equal slices:", flush=True)
        for p in positions:
            g = grades[p]
            print(f"      {p}: bands {g['bands_on_points']:5.1f}%  vs equal "
                  f"{g['even_slices_on_points']:5.1f}%   "
                  f"margin {g['bands_on_points'] - g['even_slices_on_points']:+5.1f}   "
                  f"starter line at rank {starters[p]} of {opening[p]}"
                  f"{'   [STAGED: one-stage band was undrawable]' if g.get('staged') else ''}",
                  flush=True)
        # WHAT THE GAUGE CANNOT SEE, said out loud. A tank drawn over a fraction of the rows a
        # drafter is looking at must disclose the fraction or it will read as exhaustion.
        partial = {p: seen[p] for p in sorted(on_board) if seen.get(p, 0) < 1.0}
        if partial:
            print("   COVERAGE -- positions where the board shows more than this gauge prices:",
                  flush=True)
            for p, frac in sorted(partial.items(), key=lambda t: t[1]):
                print(f"      {p}: prices {opening.get(p, 0):4d} of {on_board[p]:4d} board rows "
                      f"({frac * 100:4.0f}%)"
                      f"{'   <-- DO NOT DRAW A TANK' if frac < 1.0 and p not in positions else ''}",
                  flush=True)
        tot = sum(c["starter"] + c["bench"] for c in census.values())
        st_ = sum(c["starter"] for c in census.values())
        print(f"   PICKS in banded positions: {tot}   at/above the starter line {st_}   "
              f"below it {tot - st_} ({100.0 * (tot - st_) / tot:.0f}%) -- all still graded",
              flush=True)
        print(flush=True)

    # The gauge cannot rebound: players only leave, and each band drains inside its own slice.
    bad = []
    for label, arm in report["arms"].items():
        for p in arm["band_sizes"]:
            seq = [r["_band_left"][p] for r in arm["samples"]]
            for nm in BANDS:
                vals = [s[nm] for s in seq]
                if any(b > a for a, b in zip(vals, vals[1:])):
                    bad.append(f"{label}/{p}/{nm}")
    print("SELF-CHECK  " + ("every band monotone non-increasing -- no band can refill"
                            if not bad else f"BROKEN -- refilled at {bad}"), flush=True)
    report["selfcheck"] = "ok" if not bad else f"BROKEN at {bad}"
    OUT.write_text(json.dumps(report, indent=1))
    print(f"wrote {OUT}", flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
