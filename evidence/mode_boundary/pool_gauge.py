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
BARS = 6                    # a display choice only: how many segments to draw.
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
    """The k cuts that best separate strong players from weak ones. Greedy, parameter-free.

    THE OWNER'S CRITERION IS THE RULE, not a proxy for it: "if we're only using 2 or 3 of these
    per position, they need to be significant signals of the strength of the players above and
    below them", and then the vocabulary -- "these are the elite, these are the mid grade, these
    are the ones that are just meh". A mark is therefore placed where it MOST DIVIDES STRENGTH,
    which is what `separation` measures. Nothing is compared against a constant.

    TWO EARLIER RULES WERE BUILT AND BOTH LOST, ON MEASUREMENT (evidence/mode_boundary):

    * BIGGEST RAW GAP -- `detect_positional_cliff`'s notion. Graded on projected points it
      separates 66-96%, behind banding in all 8 position/league cells and by 25 points at
      superflex QB. A single wide gap is a standout, which is not the same thing as a boundary.
    * STEEPEST SLOPE CHANGE -- "when the production begins to dip faster, that is a cliff",
      implemented as greatest departure from the chord. It returned NOTHING AT ALL for TE and
      WR in both leagues and 32-38% for RB. The reason is a fact about the shape worth keeping:
      above the replacement bar these curves are CONCAVE -- they fall fastest at the very top
      and flatten from there -- so "where does it start falling faster" has no answer, because
      it never does. The bands the owner wants are real; the bend that was supposed to find
      them is not.

    `k` is display capacity (the owner's "at most 2 or 3"), never a cutoff on what counts.
    """
    cuts: list[int] = []
    for _ in range(k):
        best = max(((separation(vals, cuts + [i]), i)
                    for i in range(1, len(vals)) if i not in cuts), default=(0.0, None))
        if best[1] is None:
            break
        cuts.append(best[1])
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


def band_segments(remaining_order: list[str], marked: dict, bars: int) -> dict:
    """{segment index: tier} -- where each surviving cliff falls across the drawn segments.

    A cliff belongs to the player ABOVE it, so it is still ahead of you exactly while he is.
    Its depth is his rank among the players LEFT, which is why the mark slides toward the front
    of the tank as the drop approaches instead of sitting at a fixed place on the dial.
    """
    if bars <= 0 or not remaining_order:
        return {}
    seen = {}
    for i, pid in enumerate(remaining_order):
        tier = marked.get(pid)
        if tier is None:
            continue
        seg = min(bars - 1, i * bars // len(remaining_order))
        if seen.get(seg) != "HIGH":                 # HIGH wins a shared segment
            seen[seg] = tier
    return seen


def render(bars: int, cliffs: dict | None = None) -> str:
    """What a reader SEES: segments, and which of them a drop-off sits in. Never a number.

    A highlighted segment says WHERE the fall is, not how far it falls -- the magnitude stays
    behind the display contract with the counts and the points.
    """
    cliffs = cliffs or {}
    cells = []
    for i in range(BARS):
        if i >= bars:
            cells.append(".")
        elif cliffs.get(i) == "HIGH":
            cells.append("!")
        elif cliffs.get(i) == "MEDIUM":
            cells.append(":")
        else:
            cells.append("#")
    return "[" + "".join(cells) + "]"


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
    print("  #  pool    !  the drop out of ELITE    :  a lesser band edge    .  gone\n",
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
        # A mark is drawn by the band it OPENS. The first drop out of the top band is the one
        # that costs most, so it draws hardest; the rest are lesser boundaries of the same kind.
        tier_of = {p: {m["pid"]: ("HIGH" if i == 0 else "MEDIUM")
                       for i, m in enumerate(marks[p])} for p in positions}
        # Opening order INSIDE each tank, fixed like the bar: a cliff keeps its place among the
        # players, and only its distance from the front changes as they are taken.
        tank_order = {p: [str(r["player_id"]) for r in
                          sorted((r for r in board0 if str(r["player_id"]) in above[p]),
                                 key=lambda r: r["bpa"], reverse=True)]
                      for p in positions}

        print(f"== {label}", flush=True)
        print(f"   {'pick':>5}   " + "   ".join(f"{p:<13}" for p in positions), flush=True)

        series, rows = {p: [] for p in positions}, []
        for n in range(0, len(order) + 1, STRIDE):
            taken = {pid for _, pid in order[:n]}
            row = {"after_picks": n, "bars": {}, "pct": {}, "_left": {}}
            row["cliffs"] = {}
            for p in positions:
                left = len(above[p] - taken)
                row["_left"][p] = left                      # internal, audit only
                row["bars"][p] = segments(left, opening[p])
                row["pct"][p] = round(100.0 * left / opening[p]) if opening[p] else 0
                alive = [pid for pid in tank_order[p] if pid not in taken]
                row["cliffs"][p] = {str(k): v for k, v in
                                    band_segments(alive, tier_of[p], row["bars"][p]).items()}
                series[p].append(row["bars"][p])
            rows.append(row)
            print(f"   {n:>5}   " + "   ".join(
                f"{render(row['bars'][p], {int(k): v for k, v in row['cliffs'][p].items()})}"
                f"{row['pct'][p]:>4}%" for p in positions), flush=True)

        mono = {p: all(b <= a for a, b in zip(series[p], series[p][1:])) for p in positions}
        tapped = {p: next((r["after_picks"] for r in rows if r["_left"][p] == 0), None)
                  for p in positions}
        census = classify(order, pos_of, above)
        report["arms"][label] = {"opening_count": opening, "bar_points": level,
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
