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


def opening_state(rows: list[dict]) -> tuple[dict, dict, dict]:
    """(bar per position, ids above it, opening count) from the OPENING board.

    The bar is recovered from the engine's own two columns rather than recomputed, so the gauge
    and the board can never disagree about where it sits.
    """
    level, above = {}, {}
    for r in rows:
        pos, bpa, pts = r.get("position"), r.get("bpa"), r.get("projected_points")
        if pos is None or bpa is None or pts is None:
            continue
        level.setdefault(pos, round(pts - bpa, 6))
        if bpa > 0:
            above.setdefault(pos, set()).add(str(r["player_id"]))
    return level, above, {p: len(s) for p, s in above.items()}


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


def even_cuts(n: int, k: int) -> list[int]:
    """Equal slices -- the CONTROL the bands must beat, not a display option.

    Any monotone cut of an already-sorted list explains most of its variance, so a high
    separation score proves nothing on its own (#245). Arbitrary equal quarters score 82-96% on
    points. The evidence for banding is therefore the MARGIN OVER THIS, never the level.
    """
    return sorted({max(1, min(n - 1, round(n * (j + 1) / (k + 1)))) for j in range(k)})


def band_marks(board: list[dict], above: dict) -> dict:
    """{position: [mark, ...]} -- the band boundaries, fixed at the OPENING board.

    READ ONCE, AND THAT IS THE POINT. The bands are cut at the opening board and never
    recomputed, the same discipline as the bar and for the same reason: a yardstick re-read
    against the remaining pool drifts as the pool drains, the defect #74/#76 cut out of bpa and
    #271-#280 found fatal in the crossing rule. Fixed at open, a boundary is a property of a
    PLAYER, and it travels down the tank as the players ahead of him leave -- the mark does not
    wander, it APPROACHES, and passing it removes it because you went over it.

    Each mark carries `grades`, the separation the banding achieves on PROJECTED POINTS against
    the same figure for arbitrary equal slices. Points did not place these cuts; bpa did. A
    banding that lives only in the ruler used to draw it would separate bpa and not points, and
    the report would show it.
    """
    marks, grades = {}, {}
    for pos, ids in above.items():
        rows = sorted((r for r in board if str(r["player_id"]) in ids
                       and r.get("bpa") is not None
                       and r.get("projected_points") is not None),
                      key=lambda r: r["bpa"], reverse=True)
        if len(rows) < len(BANDS):
            marks[pos] = []
            continue
        v_bpa = [float(r["bpa"]) for r in rows]
        v_pts = [float(r["projected_points"]) for r in rows]
        cuts = band_cuts(v_bpa, len(BANDS) - 1)
        edges = [0] + cuts + [len(rows)]
        out = []
        for name, cut, (a, b) in zip(BANDS[1:], cuts, list(zip(edges, edges[1:]))[1:]):
            out.append({"pid": str(rows[cut]["player_id"]), "rank": cut, "band_below": name,
                        "size": b - a, "mean_points": round(sum(v_pts[a:b]) / (b - a), 1)})
        marks[pos] = out
        grades[pos] = {
            "bands_on_points": round(separation(v_pts, cuts) * 100, 1),
            "even_slices_on_points": round(
                separation(v_pts, even_cuts(len(rows), len(BANDS) - 1)) * 100, 1),
            "top_band": {"size": edges[1], "mean_points":
                         round(sum(v_pts[:edges[1]]) / edges[1], 1)},
        }
    return marks, grades


def assign_bands(board: list[dict], above: dict, marks: dict) -> tuple[dict, dict]:
    """(pid -> (position, band), position -> {band: [pid ordered]}) -- assigned ONCE, at build.

    THE OWNER'S SPEC, and it is the one the evidence already forced: "let the bands be static,
    almost assigning each player a spot in the spectrum upon build of the roster pool, based on
    the scoring settings. each league's scoring may result in varying placements inside those
    bands, but their valuation is fairly representative of their strength regardless of roster
    state and others being pulled."

    That is exactly right, and static is REQUIRED here rather than merely permitted. The cuts are
    made on opening `bpa`, which is the league's own scoring settings applied to the projection
    minus that position's opening replacement level. Re-banding mid-draft would re-read the
    yardstick against a shrinking pool -- the defect #74/#76 cut out of `bpa` (the ruler carried
    94.5% of its movement) and the one that made the crossing rule useless in #271-#280.

    THE ONE CASE WHERE A STATIC BAND GOES STALE, named rather than hidden: a mid-draft status
    change. An IR or PUP designation moves a player's projection under #191's haircut, and his
    band was cut before it. Small, real, and the only reason this assignment would ever need to
    be re-read.
    """
    band_of, members = {}, {}
    for pos in sorted(above):
        rows = sorted((r for r in board if str(r["player_id"]) in above[pos]
                       and r.get("bpa") is not None),
                      key=lambda r: r["bpa"], reverse=True)
        edges = [0] + [m["rank"] for m in marks[pos]] + [len(rows)]
        members[pos] = {}
        for name, (a, b) in zip(BANDS, zip(edges, edges[1:])):
            ids = [str(r["player_id"]) for r in rows[a:b]]
            members[pos][name] = ids
            for pid in ids:
                band_of[pid] = (pos, name)
    return band_of, members


def band_widths(sizes: dict) -> dict:
    """Segments per band: EQUAL, one slice each, not proportional to how many players it holds.

    PROPORTIONAL WAS BUILT FIRST, AND IT LOST ON THE RENDERING (both arms, side by side). RB
    opens 3/4/18/11, so proportional widths come out 1/2/8/5: the three elite backs who decide
    the position get ONE segment and eleven replacement-grade backs get five. Two failures, and
    the first is fatal:

      * A one-segment band has exactly two states, full and empty. "Two of the three elite are
        left" -- the single most decision-relevant fact at RB -- cannot be drawn at all.
      * Attention is inverted. The most display area goes to the band a drafter cares least
        about, in every position measured.

    Equal slices give every band enough resolution to show partial depletion, which is the whole
    job. What is given up is the sense of how MANY players a band holds -- but the owner already
    ruled this scale arbitrary and unitless ("each position is going to be arbitrary of the
    entire length is the entire production pool"), and the display contract forbids the counts
    that would state it precisely anyway. A band's size is not a thing this gauge ever promised
    to show; what is left inside each band is.

    Every non-empty band gets at least one segment, the same promise the whole-tank gauge makes.
    """
    live = [n for n in BANDS if sizes.get(n, 0) > 0]
    if not live:
        return {n: 0 for n in BANDS}
    base, extra = divmod(SPAN, len(live))
    width = {n: 0 for n in BANDS}
    for i, n in enumerate(live):
        width[n] = max(1, base + (1 if i < extra else 0))
    return width


def render_bands(sizes: dict, left: dict) -> str:
    """The spectrum: each band drains INSIDE ITS OWN SLICE, never from the front of the tank.

    This is the whole point of the owner's spec. The aggregate gauge drew one fill edge over a
    COUNT of survivors, which silently assumes the players who left were the ones at the front.
    For an engine draft that is true -- it takes the best available at a position by
    construction, which is why the out-of-order rate measured 0 of 219 and why that zero is the
    ENGINE's signature and not evidence about drafters. For the human this gauge is built for it
    is false: take a mid-grade tight end early for roster reasons and the aggregate bar drains
    its front, showing the elite gone when the elite is still sitting there.

    Drawn per band, nothing has to be assumed about who left. Each departure is recorded in the
    band it came from, so the display cannot make a claim that could be wrong.
    """
    width = band_widths(sizes)
    out = []
    for n in BANDS:
        w = width[n]
        if w <= 0:
            continue
        rem = left.get(n, 0)
        fill = 0 if rem <= 0 else max(1, math.ceil(w * rem / sizes[n]))
        out.append("#" * fill + "." * (w - fill))
    return "[" + "|".join(out) + "]"


def classify(order, pos_of, above):
    """Every pick sorted into the only three states the gauge can distinguish.

    ABOVE  the player was still above his position's opening bar -- measured production, taken.
    REACH  he was below it while the tank still held someone above -- the drafter passed over
           measured production to take him. A CHOICE, and the gauge is not entitled to call it
           wrong; it is the one state that carries information the gauge cannot supply.
    DARK   he was below it and the tank was ALREADY EMPTY -- no measured production remained at
           that position to pass over. This is the owner's inference, and it is forced rather
           than chosen: past this point the board's ordering within the position is no longer
           standing on anything the engine measured.

    REACH and DARK must never be merged. They are the same observable pick and opposite
    epistemic situations -- conflating a choice with an absence is the defect `#277a`/`#280`
    already cost us twice. The gauge shows DARK only, because DARK is the one the tank knows.
    """
    left = {p: set(ids) for p, ids in above.items()}
    tally = {p: {"above": 0, "reach": 0, "dark": 0, "first_dark": None} for p in left}
    for pick_no, pid in order:
        pos = pos_of.get(pid)
        if pos not in left:
            continue                                  # K/DEF/IDP: not a gauged position
        t = tally[pos]
        if pid in left[pos]:
            left[pos].discard(pid)
            t["above"] += 1
        elif left[pos]:
            t["reach"] += 1
        else:
            t["dark"] += 1
            if t["first_dark"] is None:
                t["first_dark"] = pick_no
    return tally


def main() -> int:
    battery = json.loads(IN.read_text())["arms"]
    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    base = rdb.scoring_settings_from_capture()
    matrix = {e["label"]: e for e in db.league_matrix(base)}
    report = {"bars": BARS, "stride": STRIDE, "arms": {}}
    print(f"universe {prov['players_in_pool']}  season {len(season)}  gauge = {BARS} bars",
          flush=True)
    print("display = segments (+ optional %); counts are internal and NOT shown", flush=True)
    print("  each tank is four bands -- ELITE | MID | DEPTH | MEH -- draining INDEPENDENTLY.",
          flush=True)
    print("  taking a mid-grade player shortens the MID slice; the elite slice does not move.\n",
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
        level, above, opening = opening_state(board0)
        pos_of = {str(r["player_id"]): r.get("position") for r in board0}
        positions = sorted(opening)
        marks, grades = band_marks(board0, above)
        band_of, members = assign_bands(board0, above, marks)
        sizes = {p: {n: len(members[p][n]) for n in BANDS} for p in positions}

        print(f"== {label}", flush=True)
        width = {p: len(render_bands(sizes[p], sizes[p])) for p in positions}
        print(f"   {'pick':>5}  " + "  ".join(
            f"{p + ' ' + '/'.join(str(sizes[p][n]) for n in BANDS):<{width[p]}}"
            for p in positions), flush=True)

        series, rows = {p: [] for p in positions}, []
        for n in range(0, len(order) + 1, STRIDE):
            taken = {pid for _, pid in order[:n]}
            row = {"after_picks": n, "bars": {}, "pct": {}, "_left": {}, "_band_left": {}}
            for p in positions:
                left = len(above[p] - taken)
                row["_left"][p] = left                      # internal, audit only
                row["bars"][p] = segments(left, opening[p])
                row["pct"][p] = round(100.0 * left / opening[p]) if opening[p] else 0
                # PER BAND, so nothing is assumed about WHICH players left (owner's spec).
                row["_band_left"][p] = {nm: sum(1 for pid in members[p][nm] if pid not in taken)
                                        for nm in BANDS}
                series[p].append(row["bars"][p])
            rows.append(row)
            print(f"   {n:>5}  " + "  ".join(
                f"{render_bands(sizes[p], row['_band_left'][p])}" for p in positions), flush=True)

        mono = {p: all(b <= a for a, b in zip(series[p], series[p][1:])) for p in positions}
        tapped = {p: next((r["after_picks"] for r in rows if r["_left"][p] == 0), None)
                  for p in positions}
        census = classify(order, pos_of, above)
        report["arms"][label] = {"opening_count": opening, "bar_points": level,
                                 "band_sizes": sizes,
                                 "samples": rows, "monotone": mono, "tapped_at": tapped,
                                 "census": census, "marks": marks,
                                 "grades": grades}
        print(f"   monotone: {mono}", flush=True)
        # THE EVIDENCE FOR THE MARKS, and it is the MARGIN, not the level (#245). A sorted list
        # cut anywhere explains most of its own variance, so arbitrary equal slices already
        # score in the eighties; only the gap between the two columns is earned.
        print("   BANDS graded on projected points (which did NOT place them) vs equal slices:",
              flush=True)
        for p in positions:
            g = grades[p]
            edge = g["bands_on_points"] - g["even_slices_on_points"]
            print(f"      {p}: bands {g['bands_on_points']:5.1f}%  vs equal "
                  f"{g['even_slices_on_points']:5.1f}%   margin {edge:+5.1f}   "
                  f"ELITE {g['top_band']['size']}p avg {g['top_band']['mean_points']:.0f}  -> "
                  + "  ".join(f"{m['band_below']} {m['size']}p avg {m['mean_points']:.0f}"
                              for m in marks[p]), flush=True)
        tot = sum(sum(c[k] for k in ("above", "reach", "dark")) for c in census.values())
        dark = sum(c["dark"] for c in census.values())
        reach = sum(c["reach"] for c in census.values())
        print(f"   PICKS at gauged positions: {tot}   "
              f"above bar {tot - reach - dark}   reached past {reach}   "
              f"in the dark {dark} ({100.0 * dark / tot:.0f}%)", flush=True)
        for p in positions:
            c = census[p]
            print(f"      {p}: above {c['above']:>3}  reach {c['reach']:>3}  "
                  f"dark {c['dark']:>3}   first dark pick "
                  f"{c['first_dark'] if c['first_dark'] is not None else '--'}", flush=True)
        print("   EMPTY AT: " + "  ".join(
            f"{p}={tapped[p] if tapped[p] is not None else 'never in this draft'}"
            for p in positions), flush=True)
        print(flush=True)

    bad = [f"{l}/{p}" for l, a in report["arms"].items()
           for p, ok in a["monotone"].items() if not ok]
    print("SELF-CHECK  " + ("every gauge monotone non-increasing -- it cannot rebound"
                            if not bad else f"BROKEN -- ticked UP at {bad}"), flush=True)
    report["selfcheck"] = "ok" if not bad else f"BROKEN at {bad}"
    OUT.write_text(json.dumps(report, indent=1))
    print(f"wrote {OUT}", flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
