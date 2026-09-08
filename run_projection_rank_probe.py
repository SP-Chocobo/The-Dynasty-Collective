"""Does the engine pass on the best available scorer AS A RULE, or trade at the margin?

THE QUESTION THIS ANSWERS, and the one it does not. #205 established that the engine fields
5-11% fewer projected points than a pure-points drafter, in 67 of 68 seats. That is a statement
about the ACCUMULATED total. It says nothing about the SHAPE of the individual decisions, and
two very different engines produce it:

  (a) an engine that routinely takes a far worse available scorer than a sane drafter would --
      projection is effectively not consulted, and the deficit is arbitrary;
  (b) an engine that lands close to where a sane drafter lands and occasionally trades down a
      little -- the deficit is the accumulated cost of many small deliberate choices.

Both fit "-10% on points". Only (a) is a defect. This measures which one it is, by recording,
for every pick the engine makes, that player's RANK BY PROJECTED POINTS among the players still
available at that moment.

THE RANK IS USELESS WITHOUT A CONTROL RANK, and reporting it alone would be exactly the
"plausible number about something else" this repo keeps catching. RAW PROJECTED POINTS ARE NOT
COMPARABLE ACROSS POSITIONS: in most scoring a quarterback projects far more points than a
running back, so a list of "available, ordered by projected points" is quarterback-heavy at the
top, and a drafter who correctly takes the best WIDE RECEIVER can sit at rank 16 while doing
nothing wrong at all. Measured on the first seat before this note was written: the engine's
median rank was 16 -- a number that reads damning and means nothing on its own.

So the CONTROL's rank is recorded at the control's own picks, on the identical measure. The
control is `run_roster_proof.control_pick`: best projected points at an UNFILLED STARTING SLOT,
which is position-aware and therefore also does not sit at rank 1. The comparison of the two
distributions is the finding; either one alone is not.

WHAT MAKES THE RANK MEANINGFUL: the population is the SHARED POOL (rule 2 of the proof) -- the
players BOTH arms can price. A rank against a pool one arm cannot see would not be a rank.

The engine's own board is also re-ordered internally, so "rank 1" here means "the top projected
scorer available", NOT "the top row of the engine's board".

Run from the repo root (rule 1). No arguments; writes JSON to --out.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import lineup_optimizer as lo
import resume_join
import run_draft_battery as rdb
import run_roster_proof as rp

#: A SUBSET OF #205's formats, and both regimes are represented on purpose: the 1QB and
#: superflex arms straddled each other on the points ruler, so measuring only one would leave
#: the other's decision shape unmeasured.
PROBE_FORMATS = ("12T_ppr", "12T_ppr_SF")

#: Seats measured per format. More than one, because a single seat cannot distinguish "the
#: engine does this" from "this seat's draft position does this".
SEATS_PER_FORMAT = 3


def ranks_for_one_draft(merger, players_db, league, pick_order, seat, points, season,
                        rounds, slots) -> list[dict]:
    """Re-draft the seat; return (engine rows, control rows), each a projection rank per pick.

    Deliberately re-implements run_one's loop rather than post-processing its output: the rank
    has to be taken against the pool as it stood AT THAT PICK, and a finished pick list cannot
    reconstruct that without replaying it anyway.
    """
    import pick_synthesis

    picks: list[dict] = []
    taken: set[str] = set()
    mine: dict[str, list[str]] = {}
    out: list[dict] = []
    control_rows: list[dict] = []
    seat_order = [str(s) for s in pick_order[:len(set(str(r) for r in pick_order))]]
    here = seat_order.index(str(seat))
    control_seat = seat_order[(here + 1) % len(seat_order)]
    num_teams = len(set(str(r) for r in pick_order))

    for idx in range(min(len(pick_order), rounds * num_teams)):
        who = str(pick_order[idx])
        round_no = idx // num_teams + 1
        if who == seat:
            snap = pick_synthesis.build_snapshot(
                merger, players_db, picks, pick_order, idx, who, league,
                pick_label=f"{round_no}.{(idx % num_teams) + 1:02d}",
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
            chosen = next((c.player_id for c in snap.candidates
                           if str(c.player_id) in points and str(c.player_id) not in taken), None)
            if chosen is not None:
                # The available pool, ordered by projected points, highest first. Ties broken by
                # player_id so the rank is deterministic -- an unstable tiebreak would make the
                # same decision score differently between runs.
                free = sorted((pid for pid in points if pid not in taken),
                              key=lambda p: (-points[p], p))
                rank = free.index(str(chosen)) + 1
                best = points[free[0]]
                got = points[str(chosen)]
                out.append({
                    "round": round_no,
                    "pick_no": idx + 1,
                    "player_id": str(chosen),
                    "projection_rank_among_available": rank,
                    "available": len(free),
                    "projected_points": round(got, 2),
                    "best_available_points": round(best, 2),
                    # ABSOLUTE, alongside the rank. A rank of 6 costs nothing when the top six
                    # are within a point of each other, and a rank of 2 can cost 40. Reporting
                    # the rank alone would be a plausible number about a different question.
                    "points_forgone": round(best - got, 2),
                })
        else:
            free_ids = [pid for pid in points if pid not in taken]
            chosen = (rp.control_pick(free_ids, points, mine.get(who, []), players_db, slots)
                      if free_ids else None)
            # THE CONTROL'S OWN RANK, on the identical measure. Only ONE control seat is
            # recorded (the seat immediately after the engine's), so the two populations are
            # the same size and one is not an average over eleven drafters while the other is
            # a single one.
            if chosen is not None and who == control_seat:
                free = sorted((pid for pid in points if pid not in taken),
                              key=lambda p: (-points[p], p))
                control_rows.append({
                    "round": round_no,
                    "pick_no": idx + 1,
                    "player_id": str(chosen),
                    "projection_rank_among_available": free.index(str(chosen)) + 1,
                    "available": len(free),
                    "projected_points": round(points[str(chosen)], 2),
                    "best_available_points": round(points[free[0]], 2),
                    "points_forgone": round(points[free[0]] - points[str(chosen)], 2),
                })
        if chosen is None:
            break
        taken.add(str(chosen))
        mine.setdefault(who, []).append(str(chosen))
        picks.append({"pick_no": idx + 1, "round": round_no, "roster_id": who,
                      "player_id": str(chosen)})
    return out, control_rows


def summarise(rows: list[dict]) -> dict:
    """Distribution, not a mean. A mean rank hides the shape the question is about."""
    if not rows:
        return {"picks": 0}
    ranks = [r["projection_rank_among_available"] for r in rows]
    forgone = [r["points_forgone"] for r in rows]
    hist = Counter(min(r, 21) for r in ranks)          # 21 = "21st or worse"
    return {
        "picks": len(rows),
        "rank_1": sum(1 for r in ranks if r == 1),
        "rank_1_to_3": sum(1 for r in ranks if r <= 3),
        "rank_1_to_5": sum(1 for r in ranks if r <= 5),
        "rank_11_plus": sum(1 for r in ranks if r >= 11),
        "median_rank": sorted(ranks)[len(ranks) // 2],
        "worst_rank": max(ranks),
        "mean_points_forgone": round(sum(forgone) / len(forgone), 2),
        "max_points_forgone": round(max(forgone), 2),
        "total_points_forgone": round(sum(forgone), 2),
        "rank_histogram": {str(k): v for k, v in sorted(hist.items())},
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default="PROJECTION_RANK.json")
    args = ap.parse_args(argv)

    commit = resume_join.head_commit()
    scoring = rdb.scoring_settings_from_capture()          # #213: the REAL rulebook
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    print(f"commit {commit} | universe {universe['players_in_pool']} players", flush=True)

    specs = [s for s in rp.PROOF_FORMATS if s["label"] in PROBE_FORMATS]
    results = []
    started = time.time()
    for spec in specs:
        league = dr.build_mock_league(teams=spec["teams"], superflex=spec["superflex"],
                                      scoring=spec["scoring"], te_premium=spec["te_premium"],
                                      dynasty=True, base_scoring=scoring)
        merger.set_league_format(db.league_format_hint(league))          # rule 4
        points = rp.scoreable_pool(merger, players_db, league, season)   # rule 2
        seats = [str(i) for i in range(1, spec["teams"] + 1)]
        rounds = len(league.get("roster_positions") or [])
        pick_order = ds.generate_pick_order(seats, rounds, "snake")
        slots = lo.slots_from_roster_positions(league.get("roster_positions") or [])

        # Spread across the draft order rather than taking the first N seats: an early, a middle
        # and a late seat see very different pools.
        chosen_seats = [seats[0], seats[len(seats) // 2], seats[-1]][:SEATS_PER_FORMAT]
        per_seat = []
        for seat in chosen_seats:
            t0 = time.time()
            rows, ctl_rows = ranks_for_one_draft(merger, players_db, league, pick_order, seat,
                                                 points, season, rounds, slots)
            per_seat.append({"seat": seat,
                             "engine_summary": summarise(rows),
                             "control_summary": summarise(ctl_rows),
                             "engine_picks": rows, "control_picks": ctl_rows,
                             "seconds": round(time.time() - t0, 1)})
            e = per_seat[-1]["engine_summary"]
            c = per_seat[-1]["control_summary"]
            # BOTH ARMS ON ONE LINE, always. A line showing only the engine's rank invites
            # exactly the misreading this probe exists to prevent.
            print(f"{spec['label']:14s} seat {seat:>3s}  "
                  f"ENGINE median {e['median_rank']:3d} worst {e['worst_rank']:3d} "
                  f"top5 {e['rank_1_to_5']:2d}/{e['picks']:2d} forgone/pick {e['mean_points_forgone']:7.2f}"
                  f"   |   CONTROL median {c['median_rank']:3d} worst {c['worst_rank']:3d} "
                  f"top5 {c['rank_1_to_5']:2d}/{c['picks']:2d} forgone/pick {c['mean_points_forgone']:7.2f}"
                  f"   {per_seat[-1]['seconds']:6.1f}s", flush=True)

        pooled_eng = [r for entry in per_seat for r in entry["engine_picks"]]
        pooled_ctl = [r for entry in per_seat for r in entry["control_picks"]]
        results.append({resume_join.PRODUCED_AT: commit, resume_join.CARRIED: False,
                        "label": spec["label"], "pool": len(points), "rounds": rounds,
                        "seats_measured": chosen_seats,
                        "pooled_engine": summarise(pooled_eng),
                        "pooled_control": summarise(pooled_ctl),
                        "per_seat": per_seat})
        # #213b/#215: after every format, never only on the last line.
        Path(args.out).write_text(json.dumps({
            "commit": commit,
            "commits_present": resume_join.commits_present(results),
            "universe": universe,
            "question": "for each pick, its rank by projected points among players still "
                        "available in the shared pool at that moment -- reported for the ENGINE "
                        "and for the CONTROL, because raw projection rank is not comparable "
                        "across positions and neither arm's number means anything alone",
            "seconds_this_process": round(time.time() - started, 1),
            "formats": results,
        }, indent=2, default=str), encoding="utf-8")

    print(f"\n-> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
