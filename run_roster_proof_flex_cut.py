"""#248's named follow-up: is ONE FLEX SLOT really the mechanism?

`evidence/roster_proof/README_RULEBOOK_CUT.md` closes by naming exactly what it did not
establish:

    "Why one flex slot is worth this much. The mechanism above is a reading, not a
     measurement. The cut that would settle it: the fixture roster with a third FLEX added
     and nothing else changed."

This is that cut, run in both directions so the claim cannot be saved by one arm.

FOUR ARMS, ONE PROCESS, ONE CODE VERSION:

    A2  fixture roster, FLEX 2, fixture scoring   REPRODUCTION CONTROL for #248's arm A
    D   fixture roster, FLEX 3, fixture scoring   THE FORWARD CUT  -- one slot added
    C2  F&F roster,     FLEX 3, F&F scoring       REPRODUCTION CONTROL for #248's arm C
    E   F&F roster,     FLEX 2, F&F scoring       THE MIRROR CUT   -- one slot removed

Each family keeps its own rulebook on purpose. `#248` already moved the rulebook alone
(A -> B) and measured NO effect on the verdict -- 4 of 12 either way -- so holding each
family in its native scoring costs nothing and buys each cut a reproduction control that
means something.

HOW THE SLOT IS MOVED, and why this way. A "BN" is swapped for a "FLEX" (and back), never
appended or deleted. That holds `len(roster_positions)` constant, so every code path that
reads roster LENGTH rather than roster SHAPE -- `feasibility_first`'s pick budget, the
`#242` round derivations -- sees no change at all. Rounds are pinned at 15 in all four arms,
as in `#248`. The startable count is therefore the ONLY thing that moves: 9 <-> 10.

THE REPRODUCTION CONTROLS ARE NOT DECORATION. `#247` shipped after `#248` was measured and it
rewrote `feasibility_first`. If A2 and C2 do not reproduce 4/12 and 10/12, the cut arms are
uninterpretable and this run reports that instead of an answer -- the `#241` lesson, built in
rather than remembered.

PRE-REGISTERED, before any number exists:
  D moves toward C2 AND E moves toward A2  -> one flex slot owns the reversal, in both
      directions. The mechanism reading in README_RULEBOOK_CUT.md becomes a measurement.
  D ~ A2 AND E ~ C2                        -> flex count is NOT the mechanism; the reading is
      refuted and something else separating the two rosters owns it. Next cut would have to
      be the fixture's 9 startable slots against F&F's 10 with the THIRD slot being a named
      position rather than a flex.
  Exactly one arm moves                    -> the effect is not a property of the slot but of
      one of the two rosters. Report the asymmetry; do not pick a winner.
  A2 or C2 fails to reproduce              -> report `#247`'s effect on the baseline. No
      claim about flex is made from this run.
"""

from __future__ import annotations

import collections
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
ROUNDS = 15                     # matched to #248 so its arms are the baseline, not a new one
OUT = Path("evidence/roster_proof/ROSTER_PROOF_FLEX_CUT.json")


def ff_scoring() -> dict:
    cap = json.loads(FF_CAPTURE.read_text(encoding="utf-8"))
    return {k: v["value"] for k, v in cap["scoring_settings_observed"].items()}


def ff_roster() -> list[str]:
    return json.loads(FF_CAPTURE.read_text(encoding="utf-8"))["roster_positions"]


def swap_one(roster_positions: list[str], frm: str, to: str) -> list[str]:
    """Exchange exactly one `frm` slot for a `to` slot, leaving length and order otherwise
    untouched. Raises rather than returning an unchanged roster: an arm that silently failed
    to move its own variable is the artifact this whole file exists to avoid."""
    out = list(roster_positions)
    if frm not in out:
        raise ValueError(f"no {frm} slot to exchange in {collections.Counter(out)}")
    out[out.index(frm)] = to
    before, after = collections.Counter(roster_positions), collections.Counter(out)
    if len(out) != len(roster_positions):
        raise AssertionError("length moved; the cut is no longer single-variable")
    if after[to] != before[to] + 1 or after[frm] != before[frm] - 1:
        raise AssertionError(f"exchange did not move exactly one slot: {before} -> {after}")
    changed = {k for k in set(before) | set(after) if before[k] != after[k]}
    if changed != {frm, to}:
        raise AssertionError(f"exchange moved more than {frm}/{to}: {changed}")
    return out


def arms() -> list[dict]:
    fixture_scoring = rdb.scoring_settings_from_capture()
    ffs = ff_scoring()

    def fixture_league(flex3: bool) -> dict:
        lg = dr.build_mock_league(teams=12, superflex=True, scoring="ppr", te_premium=False,
                                  dynasty=True, base_scoring=fixture_scoring)
        if flex3:
            lg["roster_positions"] = swap_one(lg["roster_positions"], "BN", "FLEX")
        lg["draft_rounds"] = ROUNDS                                   # #246: tell the engine
        return lg

    def ff_league(flex3: bool) -> dict:
        positions = ff_roster()
        if not flex3:
            positions = swap_one(positions, "FLEX", "BN")
        return {"roster_positions": positions, "scoring_settings": ffs,
                "total_rosters": 12, "settings": {"type": 2}, "draft_rounds": ROUNDS}

    return [
        {"label": "A2_fixture_FLEX2", "league": fixture_league(False),
         "expect": "CONTROL: reproduces #248 arm A, 4/12, -0.28%"},
        {"label": "D_fixture_FLEX3", "league": fixture_league(True),
         "expect": "THE FORWARD CUT -- no prior value"},
        {"label": "C2_FF_FLEX3", "league": ff_league(True),
         "expect": "CONTROL: reproduces #248 arm C, 10/12, +1.04%"},
        {"label": "E_FF_FLEX2", "league": ff_league(False),
         "expect": "THE MIRROR CUT -- no prior value"},
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
    print(f"rounds          : {ROUNDS} (matched to #248; length refuted by #245)\n")

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
        slots = lo.slots_from_roster_positions(league["roster_positions"])
        flex = league["roster_positions"].count("FLEX")
        print(f"{arm['label']}")
        print(f"  slots={len(league['roster_positions'])} FLEX={flex} startable={len(slots)} "
              f"hint={hint}")
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
                 "roster_slots": len(league["roster_positions"]), "flex_slots": flex,
                 "startable_slots": len(slots), "shared_pool": len(points),
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
        print(f"  {e['label']:20s} FLEX{e['flex_slots']} start{e['startable_slots']:>3} "
              f"{s['wins']:2d}/{s['of']:<2d}  {s['pct']:+6.2f}%   {e['expect']}")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
