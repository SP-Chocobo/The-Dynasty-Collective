"""#245's next cut: does the RULEBOOK or the ROSTER SHAPE own the reversal?

#245 measured the same harness on two leagues and got opposite verdicts on `points`:

    fixture 12T_ppr_SF, 15 rounds :  1 of 12   -5.03%
    Fourth and Forever, 15 rounds : 10 of 12   +1.04%

Draft length is already refuted (identical numbers at 15 and 26 rounds). What remains crossed is
the SCORING RULEBOOK and the ROSTER SHAPE -- F&F is half-PPR with a TE premium, first downs and
a completion bonus, and it is also the only superflex x TE-premium roster in evidence.

THREE ARMS, ONE PROCESS, ONE CODE VERSION -- the only honest A/B this repository allows:

    A  fixture roster + fixture scoring   reproduces the committed  1/12, -5.03%
    B  fixture roster + F&F scoring       THE CUT: rulebook moved, roster held
    C  F&F roster     + F&F scoring       reproduces #245's        10/12, +1.04%

A and C are not decoration. If they do not reproduce their known values, the harness is wrong
and B means nothing -- the #241 lesson, built in rather than remembered.

PRE-REGISTERED, before any number exists:
  B resembles C (engine ahead) -> the RULEBOOK owns the reversal, and every fixture-measured
      result in the freeze record was measured in the wrong scoring environment.
  B resembles A (engine behind) -> the ROSTER SHAPE or the superflex x TE-premium combination
      owns it, and the next cut is F&F's roster with the fixture's scoring.
  B between the two -> both contribute; report the split, do not pick a winner.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import lineup_optimizer as lo
import run_draft_battery as rdb
import run_roster_proof as rp
import store_io

FF_CAPTURE = Path("data/league_captures/fourth_and_forever.json")
ROUNDS = 15                     # matched across all three arms; length is already refuted
OUT = Path("evidence/roster_proof/ROSTER_PROOF_RULEBOOK_CUT.json")


def ff_scoring() -> dict:
    cap = json.loads(FF_CAPTURE.read_text(encoding="utf-8"))
    return {k: v["value"] for k, v in cap["scoring_settings_observed"].items()}


def ff_roster() -> list[str]:
    return json.loads(FF_CAPTURE.read_text(encoding="utf-8"))["roster_positions"]


def arms() -> list[dict]:
    fixture_scoring = rdb.scoring_settings_from_capture()
    ffs = ff_scoring()

    def fixture_league(scoring: dict) -> dict:
        lg = dr.build_mock_league(teams=12, superflex=True, scoring="ppr", te_premium=False,
                                  dynasty=True, base_scoring=scoring)
        lg["draft_rounds"] = ROUNDS                                   # #246: tell the engine
        return lg

    def ff_league(scoring: dict) -> dict:
        lg = {"roster_positions": ff_roster(), "scoring_settings": scoring,
              "total_rosters": 12, "settings": {"type": 2}, "draft_rounds": ROUNDS}
        return lg

    return [
        {"label": "A_fixture_roster_fixture_scoring", "league": fixture_league(fixture_scoring),
         "expect": "reproduces 1/12, -5.03%"},
        {"label": "B_fixture_roster_FF_scoring", "league": fixture_league(ffs),
         "expect": "THE CUT -- no prior value"},
        {"label": "C_FF_roster_FF_scoring", "league": ff_league(ffs),
         "expect": "reproduces 10/12, +1.04%"},
    ]


def summary(runs: list[dict]) -> dict:
    if not runs:
        return {}
    out = {}
    for ruler in rp.RULERS:
        q = rp.COMPARE_ON[ruler]
        wins = sum(1 for r in runs if r["engine"][ruler][q] > r["control_mean"][ruler][q])
        eng = sum(r["engine"][ruler][q] for r in runs) / len(runs)
        ctl = sum(r["control_mean"][ruler][q] for r in runs) / len(runs)
        out[ruler] = {"wins": wins, "of": len(runs), "engine_mean": round(eng, 2),
                      "control_mean": round(ctl, 2),
                      "pct": round((eng / ctl - 1) * 100, 2) if ctl else None}
    return out


def main() -> int:
    print(f"rulebook source : {FF_CAPTURE}")
    print(f"universe        : rdb.build_players_db_from_capture() <- {rdb.CAPTURE_PATH}")
    print(f"rounds          : {ROUNDS} (matched across arms; length refuted by #245)\n")

    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    print(f"pool            : {universe['players_in_pool']} players, "
          f"{len(season)} season projections\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    t0 = time.time()

    def write(complete: bool):
        # #213b: after every SEAT, not every arm. This run is ~1h.
        store_io.write(OUT, {"complete": complete, "rounds": ROUNDS,
                             "arms": results, "seconds": round(time.time() - t0, 1)})

    for arm in arms():
        league = arm["league"]
        hint = db.league_format_hint(league)
        print(f"{arm['label']}")
        print(f"  slots={len(league['roster_positions'])} hint={hint}  ({arm['expect']})")
        merger.set_league_format(hint)                                 # rule 3, never skip
        points = rp.scoreable_pool(merger, players_db, league, season)
        values = db.reference_values(merger, players_db, league, sleeper_projections=season,
                                     sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        slots = lo.slots_from_roster_positions(league["roster_positions"])
        seats = [str(i) for i in range(1, 13)]
        pick_order = ds.generate_pick_order(seats, ROUNDS, "snake")
        rulers = {"cdme": values, "points": points}
        print(f"  shared pool={len(points)} startable={len(slots)} picks={len(pick_order)}")

        runs: list[dict] = []
        entry = {"label": arm["label"], "hint": hint, "expect": arm["expect"],
                 "roster_slots": len(league["roster_positions"]),
                 "shared_pool": len(points), "seats": runs, "summary": {}}
        results.append(entry)
        for seat in seats:
            picks = rp.run_one(merger, players_db, league, pick_order, seat,
                               points, season, ROUNDS, slots)
            engine = rp.score_roster(picks, seat, players_db, rulers, slots)
            others = [s for s in seats if s != seat]
            controls = [rp.score_roster(picks, s, players_db, rulers, slots) for s in others]
            runs.append({"engine_seat": seat, "engine": engine,
                         "control_mean": {r: {q: sum(c[r][q] for c in controls) / len(controls)
                                              for q in engine[r]} for r in rp.RULERS}})
            entry["summary"] = summary(runs)
            write(False)
            p = runs[-1]
            e = p["engine"]["points"]["starter_value"]
            c = p["control_mean"]["points"]["starter_value"]
            print(f"    seat {seat:>2}  points: eng {e:9.2f} vs ctl {c:9.2f}  "
                  f"{100 * (e - c) / c:+6.2f}%", flush=True)
        s = entry["summary"]["points"]
        print(f"  => points {s['wins']} of {s['of']}   {s['pct']:+.2f}%\n", flush=True)

    write(True)
    print("ARM SUMMARY (points, the strong claim)")
    for e in results:
        s = e["summary"]["points"]
        print(f"  {e['label']:34s} {s['wins']:2d}/{s['of']:<2d}  {s['pct']:+6.2f}%   {e['expect']}")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
