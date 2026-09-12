"""The last structural candidate: is it ROSTER CAPACITY?

Three structural differences separated the fixture league (`points` 4/12, -0.28%) from Fourth
and Forever (10/12, +1.04%). Two are already refuted by measurement, and today the third was:

    draft length      REFUTED  #245 -- identical to the cent at 15 and 26 rounds
    scoring rulebook  REFUTED  #248 arm A->B -- 4/12 either way
    flex / startable  REFUTED  the flex cut -- both directions, no consistent sign; and A2 vs E
                               have the SAME 9 startable slots and opposite verdicts

What is left is the one `#248` dismissed as unable to enter, and it is not inert:

    fixture   15 slots   9 startable   15 draftable  ->  15 picks fill it EXACTLY.   0 spare
    F&F       29 slots  10 startable   26 draftable  ->  15 picks fill 15 of 26.    11 spare

`draft_room.draftable_slots_per_team` counts every slot but IR and feeds
`remaining_league_picks` -- its own docstring: "how many draft picks the league still has to
spend, summed per team ... EXACT and BOUNDED, reaching exactly zero when every roster is full" --
which feeds the bench-appetite rates. On the fixture that quantity is driven to zero by the
final round; on F&F it never falls below 11 per team. Capacity reaches the engine independently
of both flex count and round count, and every cut so far held it fixed by construction.

A DOSE-RESPONSE, NOT A MIRROR, and that is a deliberate choice. The obvious mirror -- cut F&F's
capacity to 15 -- can only be done by deleting all eleven of its BN slots, which leaves a roster
with ZERO bench and five TAXI. That is not one variable moved; it is a degenerate roster, and
`bench_capacity` is a real engine input (`#224`). Padding the fixture instead moves capacity
ALONE, and three points on the axis say more than one: an effect that is real should be
monotone in the thing causing it.

THREE ARMS, ONE PROCESS, ONE CODE VERSION, rounds pinned at 15 as in every cut since `#245`:

    A3   fixture, 15 draftable (0 spare)    REPRODUCTION CONTROL for the flex cut's arm A2
    F20  fixture, 20 draftable (5 spare)    THE CUT, halfway
    F26  fixture, 26 draftable (11 spare)   THE CUT, matched to F&F exactly

Only BN slots are added. Startable stays 9, the rulebook stays the fixture's PPR, the pool and
the pick order are untouched. `pad_bench` raises rather than returning an unchanged roster.

PRE-REGISTERED, before any number exists:
  F26 moves toward +1.04% AND F20 sits between A3 and F26 -> ROSTER CAPACITY is the mechanism,
      monotone in the axis, and every fixture-measured verdict in the freeze record was taken in
      a league whose picks run out exactly when the draft does.
  F26 ~ A3 -> capacity is refuted too. All three structural candidates are gone and what remains
      is the only difference left: TAXI, which the fixture has none of and F&F has five.
  F26 moves but F20 does not sit between -> the effect is not monotone in capacity, which means
      it is not capacity but something that switches at a threshold. Report the non-monotonicity;
      do not name a mechanism from two points.
  A3 fails to reproduce -> the harness moved under me. No claim is made from this run.
"""

from __future__ import annotations

import collections
import time
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import league_config as lc
import lineup_optimizer as lo
import run_draft_battery as rdb
import run_roster_proof as rp
import store_io

ROUNDS = 15                     # matched to #245/#248/the flex cut; length refuted long ago
OUT = Path("evidence/roster_proof/ROSTER_PROOF_CAPACITY_CUT.json")

#: F&F's own draftable count, which F26 is matched to. Not a chosen number -- it is read off the
#: capture by the same function the engine uses, so the arm cannot drift away from the league it
#: is imitating.
FF_CAPTURE = Path("data/league_captures/fourth_and_forever.json")


def ff_draftable() -> int:
    import json
    positions = json.loads(FF_CAPTURE.read_text(encoding="utf-8"))["roster_positions"]
    return len(lc.draftable_slots(positions))


def pad_bench(roster_positions: list[str], to_draftable: int) -> list[str]:
    """Append BN slots until the roster offers exactly `to_draftable` draftable slots.

    Raises rather than returning an unchanged roster, and rather than ever REMOVING a slot: an
    arm that silently failed to move its own variable is the artifact this file exists to avoid,
    and a negative pad would be a different experiment wearing this one's name.
    """
    have = len(lc.draftable_slots(roster_positions))
    if to_draftable < have:
        raise ValueError(f"cannot pad {have} draftable slots down to {to_draftable}")
    out = list(roster_positions) + ["BN"] * (to_draftable - have)
    before, after = collections.Counter(roster_positions), collections.Counter(out)
    changed = {k for k in set(before) | set(after) if before[k] != after[k]}
    if changed - {"BN"}:
        raise AssertionError(f"padding moved something other than BN: {changed}")
    if len(lc.draftable_slots(out)) != to_draftable:
        raise AssertionError("padding did not reach the requested draftable count")
    if len(lc.starting_slots(out)) != len(lc.starting_slots(roster_positions)):
        raise AssertionError("padding changed the startable count; the cut is not single-variable")
    return out


def arms() -> list[dict]:
    fixture_scoring = rdb.scoring_settings_from_capture()
    base = dr.build_mock_league(teams=12, superflex=True, scoring="ppr", te_premium=False,
                                dynasty=True, base_scoring=fixture_scoring)
    have = len(lc.draftable_slots(base["roster_positions"]))
    matched = ff_draftable()
    halfway = (have + matched) // 2

    def league(to_draftable: int) -> dict:
        lg = dict(base)
        lg["roster_positions"] = pad_bench(base["roster_positions"], to_draftable)
        lg["draft_rounds"] = ROUNDS                                   # #246: tell the engine
        return lg

    return [
        {"label": f"A3_fixture_draftable{have}", "league": league(have),
         "expect": "CONTROL: reproduces the flex cut's A2, 4/12, -0.28%"},
        {"label": f"F{halfway}_fixture_draftable{halfway}", "league": league(halfway),
         "expect": "THE CUT, halfway -- no prior value"},
        {"label": f"F{matched}_fixture_draftable{matched}", "league": league(matched),
         "expect": "THE CUT, matched to F&F -- no prior value"},
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
                      "pct": round((eng / ctl - 1) * 100, 2) if ctl else None,
                      "margin": round(eng - ctl, 2)}
    return out


def main() -> int:
    print(f"universe : rdb.build_players_db_from_capture() <- {rdb.CAPTURE_PATH}")
    print(f"rounds   : {ROUNDS} (matched; length refuted by #245)")
    print(f"F&F draftable, read from its own capture: {ff_draftable()}\n")

    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    print(f"pool     : {universe['players_in_pool']} players, {len(season)} season projections\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    t0 = time.time()

    def write(complete: bool):
        store_io.write(OUT, {"complete": complete, "rounds": ROUNDS,
                             "arms": results, "seconds": round(time.time() - t0, 1)})

    for arm in arms():
        league = arm["league"]
        hint = db.league_format_hint(league)
        slots = lo.slots_from_roster_positions(league["roster_positions"])
        draftable = len(lc.draftable_slots(league["roster_positions"]))
        print(f"{arm['label']}")
        print(f"  slots={len(league['roster_positions'])} startable={len(slots)} "
              f"draftable={draftable} spare_at_{ROUNDS}_rounds={draftable - ROUNDS} hint={hint}")
        print(f"  ({arm['expect']})")
        merger.set_league_format(hint)                                 # rule 3, never skip
        points = rp.scoreable_pool(merger, players_db, league, season)
        values = db.reference_values(merger, players_db, league, sleeper_projections=season,
                                     sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        seats = [str(i) for i in range(1, 13)]
        pick_order = ds.generate_pick_order(seats, ROUNDS, "snake")
        rulers = {"cdme": values, "points": points}
        print(f"  shared pool={len(points)} picks={len(pick_order)}")

        runs: list[dict] = []
        entry = {"label": arm["label"], "hint": hint, "expect": arm["expect"],
                 "roster_slots": len(league["roster_positions"]),
                 "startable_slots": len(slots), "draftable_slots": draftable,
                 "spare_slots": draftable - ROUNDS, "shared_pool": len(points),
                 "seats": runs, "summary": {}}
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
            write(False)                                               # #213b: every SEAT
            p = runs[-1]
            e = p["engine"]["points"]["starter_value"]
            c = p["control_mean"]["points"]["starter_value"]
            print(f"    seat {seat:>2}  points: eng {e:9.2f} vs ctl {c:9.2f}  "
                  f"{100 * (e - c) / c:+6.2f}%", flush=True)
        s = entry["summary"]["points"]
        print(f"  => points {s['wins']} of {s['of']}   {s['pct']:+.2f}%   "
              f"margin {s['margin']:+.2f}\n", flush=True)

    write(True)
    print("ARM SUMMARY (points, the strong claim) -- read it as a dose-response")
    for e in results:
        s = e["summary"]["points"]
        print(f"  {e['label']:28s} draftable {e['draftable_slots']:2d} "
              f"spare {e['spare_slots']:2d}  {s['wins']:2d}/{s['of']:<2d} "
              f"{s['pct']:+6.2f}%  margin {s['margin']:+8.2f}   {e['expect']}")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
