"""Does the engine draft well when graded on WHAT ACTUALLY HAPPENED? Run from the repo root.

    python3 run_backtest_grade.py [--season 2024] [--out BACKTEST_GRADE.json]

THE GAP THIS CLOSES. `run_smoke_seats` grades the engine against a field of sane styles, and it is
the best instrument this repository has — but it scores rosters on PROJECTIONS, drafted from a
capture of a season that has not been played. Two consequences, both measured:

  1. It solves ONE lineup over season totals with NO ABSENCES, so a bench is a pure liability and
     depth cannot pay. Measured starter-band absence rates, 2023/24 weeks 1-17: RB 0.14/0.12,
     WR 0.11/0.14, TE 0.15/0.16, QB 0.08/0.07 against 0.06 for K and DEF (the bye alone).
  2. It is INDIFFERENT to when K and DST are drafted: across three drafts whose first DEF ranged
     from round 5 to round 10 the league total moved −0.16%/+0.08%. Counterfactual surgery on the
     same question, scored on realized outcomes, puts the cost of an early K/DST pick at **+81.4
     points** (42 picks, helped 34 of 42). The projected ruler cannot see an 81-point effect.

So a K/DST repair is unvalidatable under that gate — it can neither catch a regression of this
shape nor confirm a fix. This runs the same mixed-table, seat-controlled design on a season that
FINISHED, and scores with `realized_ruler`: the sum of each week's best legal lineup over real
stats.

WHAT IS REUSED RATHER THAN REBUILT (`#126`): `run_smoke_seats.draft` (the mixed table),
`run_smoke_seats.STYLES` (the field), `run_roster_proof.scoreable_pool` (the shared pool both arms
draw from), and `realized_ruler`. Nothing about how a draft happens is reimplemented here; the
only new thing is the ruler it is graded on.

THE FIELD EXCLUDES `adp`, DELIBERATELY. The ADP table is a 2026-vintage vendor export, so using it
to draft a 2024 season would let an opponent see rankings formed after that season was played.
Worse for the question at hand: all 32 defenses share ONE ADP value and 35 kickers share three,
against an "undrafted" sentinel of 18000 — so `adp` cannot order the positions this instrument
exists to measure. `need_first` and `points_need` derive from the drafted season's own
projections and are period-correct.

LIMITS, stated so no one reads more into a total than it carries:
  - No waivers or trades. The roster is frozen at the draft, so every arm is denied streaming
    equally. That makes this a LOWER bound on any strategy built around in-season transactions.
  - The weekly solve is an ORACLE lineup — it starts the best actual scorers, not the ones a
    manager would have guessed on Saturday. Every arm gets the same advantage, so the comparison
    survives it; the absolute totals are ceilings and must not be quoted as expected scores.
  - The player universe is the capture's, which post-dates the drafted season. That is NOT
    self-correcting, and the first two runs of this instrument were invalid because of it: a
    later rookie has an all-zero projection row for the backtested season, which sends the board
    to the 2026 vendor export for his price and puts him at the top of the board. 133 such
    players in 2023 and 101 in 2024. `period_correct_pool` now removes them before the draft --
    read its docstring before quoting any absolute number from this instrument.
"""

from __future__ import annotations

import argparse
import collections
import json
import statistics
import time
from pathlib import Path

import capture_weekly_lines as cwl
import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import player_universe as pu
import realized_ruler as rr
import run_draft_battery as rdb
import run_roster_proof as rp
import run_smoke_seats as ss

REPORT_PATH = Path("BACKTEST_GRADE.json")

#: Formats to grade. `12T_ppr_K_DEF` FIRST and non-negotiably: every format in the projected
#: grader carries ZERO K and DEF roster slots, so the instrument that would certify a K/DST repair
#: has never been able to see the positions under repair. This one has both, and the full 64-key
#: rulebook that prices them.
BACKTEST_FORMATS = ("12T_ppr_K_DEF",)

#: The field. `adp` is excluded -- see the module docstring.
BACKTEST_STYLES = ("need_first", "points_need")


def season_sums(season: str, scoring: dict) -> dict[str, dict]:
    """Per-CATEGORY season totals for the drafted season, the shape the board prices from."""
    totals = collections.defaultdict(lambda: collections.defaultdict(float))
    for _week, lines in cwl.load_season(season, "projections").items():
        for pid, stats in lines.items():
            for key, value in stats.items():
                try:
                    totals[pid][key] += float(value)
                except (TypeError, ValueError):
                    # A non-numeric field is not a zero (#187). Skipped, never defaulted.
                    continue
    return {pid: dict(v) for pid, v in totals.items()}


#: Sleeper's own league-type code for a dynasty league, read from `draft_room`'s single test
#: rather than restated, so this instrument cannot disagree with the engine about what dynasty
#: means (#126).
DYNASTY_TYPE = 2


def redraft_league(league: dict) -> dict:
    """The same league with its DYNASTY flag cleared. A copy -- the caller's league is untouched.

    WHY AN ARM FOR THIS. The backtest's arms are all `settings.type == 2`, and `draft_room`
    gates `time_horizon_adj` on exactly that: in a dynasty league every priced row carries an
    adjustment built from the gap between its THREE-YEAR outlook and its season projection.
    Measured on the 2024 board, 258 of 1181 rows change, and the top ten changes composition.

    That is the engine doing its job. It is also a horizon mismatch with this ruler, which scores
    ONE season. Grading a deliberately multi-year objective on a single-season outcome charges
    the engine for value it bought on purpose and will collect in a year this instrument does not
    score. Worse, the three-year outlook is the 2026 vendor's, so in a 2024 draft it is a
    forward-looking ranking formed after the season was played -- the milder cousin of the
    anachronism `period_correct_pool` removes.

    So this arm is not a fix and not a preference. It is the second half of a pair: the dynasty
    arm answers "how does the shipped configuration do on a season we can score", and this one
    answers "how does the same machinery do when its horizon matches the ruler's". Quoting either
    alone would be quoting half a measurement.
    """
    out = dict(league)
    settings = dict(out.get("settings") or {})
    # Anything that is not the dynasty code is redraft, by draft_room's own one-line test. 0 is
    # Sleeper's redraft value; the assertion below is what actually guarantees the arm differs.
    settings["type"] = 0
    out["settings"] = settings
    assert settings["type"] != DYNASTY_TYPE, "the redraft arm must clear the dynasty flag"
    return out


def period_correct_pool(points: dict, projections: dict, scoring: dict) -> tuple[dict, list]:
    """Drop players the DRAFTED SEASON never projected -- the backtest's anachronism guard.

    THE CONFOUND THIS CLOSES, and it invalidated the first two runs of this instrument. The
    player universe comes from a 2026 capture, and so does the vendor rankings export. The
    drafted season's own weekly projections are what SHOULD price the board, and the board takes
    them -- but only when they score to something. `draft_room.build_available_pool` sets
    `sleeper_points = scored if scored != 0 else None` (draft_room.py:1456), and a player who did
    not exist in the drafted season has a projection row of all zeros, which scores to exactly
    0.0. `sleeper_points` goes None, `use_season` does not fire, and the board prices him from
    the **2026 vendor export** instead.

    Measured, in the 12T_ppr_K_DEF pool: 133 such players in 2023 and 101 in 2024, priced as high
    as 340.0 -- Maye, Daniels, C. Williams, Dart, Nix, Jeanty, Bowers, Hampton. Every one is a
    rookie from a later season, every one is priced at the top of the board by a ranking formed
    after the backtested season was played, and every one realizes exactly 0.0 because he has no
    stat line that year. The engine's 2023 seat-1 roster spent round 2 on Bowers and round 8 on
    Dart. An absolute grade against a field is worthless while that is true.

    THIS IS NOT HINDSIGHT. A drafter in the backtested season could not have drafted a player
    nobody projected that season -- he was not in the league. The filter uses only the drafted
    season's own published projections, never its outcomes, and it applies to every arm and every
    seat identically.

    Returns (kept, dropped). The dropped list travels into the report so a future reader can see
    what the guard removed rather than trusting that it fired.
    """
    kept, dropped = {}, []
    for pid, priced in points.items():
        # Exactly the board's own test, so the guard cannot drift from the fallback it guards.
        if pu.score_projection(projections.get(pid) or {}, scoring) != 0.0:
            kept[pid] = priced
        else:
            dropped.append(pid)
    return kept, dropped


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--season", default="2024")
    parser.add_argument("--out", default=str(REPORT_PATH))
    parser.add_argument("--seats", type=int, default=0,
                        help="grade only the first N seats (a smoke run, never an answer)")
    parser.add_argument("--redraft", action="store_true",
                        help="grade the engine on a REDRAFT league, so its objective matches "
                             "this ruler's horizon -- see redraft_league()")
    args = parser.parse_args(argv)

    scoring = rdb.scoring_settings_from_capture()
    players_db, _ = rdb.build_players_db_from_capture()
    projections = season_sums(args.season, scoring)
    realized = rr.weekly_points(cwl.load_season(args.season, "stats"), scoring)
    if not projections or not realized:
        print(f"no captures for {args.season}; need both projections and stats")
        return 1

    results = []
    started = time.time()
    for label in BACKTEST_FORMATS:
        arm = next(a for a in db.league_matrix(scoring) if a["label"] == label)
        league, teams, rounds = arm["league"], arm["teams"], arm["rounds"]
        if args.redraft:
            league = redraft_league(league)
        slots = rr.slots_for(league)
        kdst_slots = [s for s in (league.get("roster_positions") or []) if s in ("K", "DEF")]
        # NON-VACUITY, ASSERTED BEFORE THE RUN. A backtest of K/DST placement in a league with no
        # K or DEF slot measures the format, and this repository has made that exact mistake
        # three times.
        if not kdst_slots:
            print(f"REFUSING: {label} has no K/DEF roster slot, so it cannot grade K/DST.")
            return 1

        merger = dm.DataMerger()
        merger.set_league_format(db.league_format_hint(league))
        priced_pool = rp.scoreable_pool(merger, players_db, league, projections)
        points, anachronisms = period_correct_pool(priced_pool, projections, scoring)
        # NON-VACUITY, ASSERTED BEFORE THE RUN, in the other direction from the slot check above:
        # the guard removing NOTHING on a season whose capture post-dates it would mean it is not
        # firing, and the run would silently be the confounded one again.
        if not anachronisms:
            print(f"REFUSING: the anachronism guard dropped 0 of {len(priced_pool)} for "
                  f"{args.season}. On a capture that post-dates the drafted season it must drop "
                  f"the later rookies; dropping none means it is not firing.")
            return 1
        adp, _ = ss.adp_table(projections)
        seats = [str(i) for i in range(1, teams + 1)]
        order = ds.generate_pick_order(seats, rounds, "snake")
        graded_seats = seats[:args.seats] if args.seats else seats

        print(f"{label} [{'redraft' if args.redraft else 'dynasty'}]: {len(points)} draftable ({len(anachronisms)} of {len(priced_pool)} "
              f"dropped as not projected in {args.season}), K/DEF slots {kdst_slots}, "
              f"grading {len(graded_seats)} seats on {args.season} outcomes", flush=True)

        rows = []
        for seat in graded_seats:
            assigned = ss.style_by_seat(seats, seat, admitted=list(BACKTEST_STYLES))
            picks = ss.draft(merger, players_db, league, order, points, adp,
                             projections, rounds, slots, assigned, seat)
            by_seat = collections.defaultdict(list)
            for pick in picks:
                by_seat[pick["roster_id"]].append(pick["player_id"])
            engine = rr.score_roster_realized(by_seat[seat], players_db, realized, slots)
            field = [rr.score_roster_realized(ids, players_db, realized, slots)
                     for other, ids in by_seat.items() if other != seat]
            field_mean = statistics.fmean(f["total"] for f in field) if field else None
            kdst_rounds = [p["round"] for p in picks
                           if p["roster_id"] == seat
                           and pu.player_position(players_db.get(p["player_id"]) or {})
                           in ("K", "DEF")]
            rows.append({
                "seat": seat,
                "engine_realized": engine["total"],
                "field_mean_realized": round(field_mean, 2) if field_mean is not None else None,
                "delta": round(engine["total"] - field_mean, 2) if field_mean is not None else None,
                "engine_never_started": engine["players_who_never_started"],
                "engine_first_kdst_round": min(kdst_rounds) if kdst_rounds else None,
                "weeks_scored": engine["weeks_scored"],
            })
            print(f"   seat {seat:>2}: engine {engine['total']:>8.1f} vs field "
                  f"{field_mean:>8.1f}  delta {rows[-1]['delta']:>+8.1f}  "
                  f"first K/DST rd {rows[-1]['engine_first_kdst_round']}", flush=True)

        # DUPLICATE SEATS, DERIVED AND REPORTED. Two engine seats can produce the IDENTICAL
        # roster: measured here, seats 2 and 3 both returned 2439.56. It is not a bug -- the
        # engine and the neighbouring style want disjoint players, so swapping which of them
        # picks second merely swaps who takes whom, and the engine's own roster is unchanged.
        # But it means the seats are NOT independent samples, and a mean over 12 that contains
        # a duplicate overstates its own n. `#246`'s lesson in the other direction: identical
        # output is usually a broken instrument, so when it is NOT, that has to be shown rather
        # than assumed.
        totals = [r["engine_realized"] for r in rows]
        duplicate_seats = sorted(
            [r["seat"] for r in rows if totals.count(r["engine_realized"]) > 1])
        distinct = {}
        for r in rows:
            distinct.setdefault(r["engine_realized"], r)
        distinct_deltas = [r["delta"] for r in distinct.values() if r["delta"] is not None]

        deltas = [r["delta"] for r in rows if r["delta"] is not None]
        results.append({
            "label": label, "season": args.season, "teams": teams, "rounds": rounds,
            "styles": list(BACKTEST_STYLES), "pool": len(points),
            "horizon": "redraft" if args.redraft else "dynasty",
            "pool_before_anachronism_guard": len(priced_pool),
            "dropped_not_projected_this_season": len(anachronisms),
            "kdst_slots": kdst_slots, "seats_graded": len(rows), "rows": rows,
            "wins": sum(1 for d in deltas if d > 0),
            "mean_delta": round(statistics.fmean(deltas), 2) if deltas else None,
            "median_delta": round(statistics.median(deltas), 2) if deltas else None,
            "distinct_engine_rosters": len(distinct),
            "duplicate_seats": duplicate_seats,
            "wins_distinct": sum(1 for d in distinct_deltas if d > 0),
            "mean_delta_distinct": (round(statistics.fmean(distinct_deltas), 2)
                                    if distinct_deltas else None),
            "median_delta_distinct": (round(statistics.median(distinct_deltas), 2)
                                      if distinct_deltas else None),
        })

    report = {
        "_comment": ("Engine vs a field of sane styles, drafted on a FINISHED season's "
                     "projections and scored on that season's REALIZED weekly outcomes. The "
                     "first grade in this repository the engine cannot optimise toward. No "
                     "waivers, oracle weekly lineup -- see run_backtest_grade.py."),
        "season": args.season,
        "ruler": "realized: sum of each week's best legal lineup over actual stats",
        "seconds": round(time.time() - started, 1),
        "results": results,
    }
    Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(f"\n=== BACKTEST GRADE, {args.season} realized outcomes ===")
    for block in results:
        print(f"{block['label']}: engine wins {block['wins']} of {block['seats_graded']} seats | "
              f"mean {block['mean_delta']:+.1f} | median {block['median_delta']:+.1f}")
        if block["duplicate_seats"]:
            print(f"   {block['distinct_engine_rosters']} DISTINCT rosters "
                  f"(seats {', '.join(block['duplicate_seats'])} collapse -- not independent "
                  f"samples): wins {block['wins_distinct']} of "
                  f"{block['distinct_engine_rosters']} | "
                  f"mean {block['mean_delta_distinct']:+.1f} | "
                  f"median {block['median_delta_distinct']:+.1f}")
    print(f"\n-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
