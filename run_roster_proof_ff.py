"""The roster proof, run on FOURTH AND FOREVER — the league this engine is actually for.

WHY THIS EXISTS, and why it is the highest-value measurement available.

`run_roster_proof.py` states its own scoring logic (RULERS): a win on `cdme` alone is "a
tautology and must be reported as one"; a win on `points` too is "the strong claim -- the engine
beat the control at the control's own game." The two rulers correlate at only r=0.241, so they
are different questions, not two views of one.

The committed 6-format proof returned: **cdme 68/68 (the tautology), points 1/68 (the strong
claim, not achieved).** That is the only informative test this repo has ever run on the engine,
and the engine did not pass it.

But it was run on `data/fixtures/sleeper_capture.json` -- full PPR, no TE bonus, no first-down
scoring -- and NOT on Fourth and Forever, which is half-PPR, TE-premium, and pays receivers
DOUBLE what backs get per first down, with a completion bonus in superflex. Measured on four
real week-1 starters, the rulebook difference is +15.7% and it runs the OPPOSITE way to the
5-11% deficit being judged. **The confound is larger than the effect.** So the strong claim has
never been tested where it matters.

Both outcomes here are decisive, which is what makes it worth running:
  - engine still loses `points` on F&F  -> the strong claim genuinely fails, and that is the
                                          freeze blocker, named honestly.
  - engine wins or ties `points` on F&F -> it holds in the league being played, and the freeze
                                          has the evidence it currently lacks.

WHAT IS REUSED RATHER THAN REBUILT. Every scoring, drafting and lineup function comes from
run_roster_proof itself -- scoreable_pool, run_one, score_roster, RULERS, COMPARE_ON. This file
supplies ONE thing: the league. A second copy of the proof's logic would be a second source of
truth for the result (#126), and the whole point is that this arm is comparable to the other six.

THE LEAGUE IS READ, NOT ASSUMED. Every number below is derived from the capture:
  - 12 teams                       <- total_rosters
  - 26 rounds                      <- draft_math.draftable_slots_per_team (10 starters + 11 BN
                                      + 5 TAXI; the 3 IR slots are not drafted). The real
                                      startup ran exactly 26 rounds, which the capture records
                                      as independent confirmation of both numbers.
  - 10 startable slots             <- lo.slots_from_roster_positions, which excludes BN/IR/TAXI
  - scoring                        <- scoring_settings_observed, VERIFIED against the live app
                                      on four real box scores (evidence/rulebook_ground_truth/)

STATED ASSUMPTION: snake order, matching all six committed PROOF_FORMATS so this arm is
comparable to them. The capture does not record the startup's draft type. If F&F ran 3RR, that
is a real difference and this arm should be re-run with it.

Run from the repo root:  PYTHONPATH=. python3 run_roster_proof_ff.py
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

CAPTURE = Path("data/league_captures/fourth_and_forever.json")


def ff_league() -> tuple[dict, int]:
    """Fourth and Forever as a Sleeper-shaped league, plus its draftable round count."""
    cap = json.loads(CAPTURE.read_text(encoding="utf-8"))
    league = {
        "roster_positions": cap["roster_positions"],
        "scoring_settings": {k: v["value"] for k, v in cap["scoring_settings_observed"].items()},
        "total_rosters": cap["total_rosters"],
        "settings": {"type": 2},                      # dynasty, per league_type
    }
    rounds = cap["draft_math"]["draftable_slots_per_team"]
    return league, rounds


def main() -> int:
    league, rounds = ff_league()
    teams = league["total_rosters"]
    # DOCTRINE (this session): print which files the fixture actually opened, next to the
    # answer. #241 was a wrong finding produced by reading the wrong capture, and nothing about
    # the wrong league announced itself in any number.
    print(f"rulebook  : {CAPTURE}")
    print(f"universe  : rdb.build_players_db_from_capture() <- {rdb.CAPTURE_PATH}")
    print(f"league    : {teams} teams, {rounds} draftable rounds, "
          f"{len(league['roster_positions'])} roster slots")
    print(f"format    : {db.league_format_hint(league)}")

    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    print(f"pool      : {universe['players_in_pool']} players, {len(season)} season projections")

    merger.set_league_format(db.league_format_hint(league))            # rule 4, never skip
    points = rp.scoreable_pool(merger, players_db, league, season)     # rule 2, shared pool
    values = db.reference_values(merger, players_db, league,
                                 sleeper_projections=season,
                                 sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    slots = lo.slots_from_roster_positions(league["roster_positions"])
    seats = [str(i) for i in range(1, teams + 1)]
    pick_order = ds.generate_pick_order(seats, rounds, "snake")
    rulers = {"cdme": values, "points": points}
    print(f"shared pool: {len(points)} players both arms can price | "
          f"{len(slots)} startable slots | {len(pick_order)} picks\n")

    out = Path("evidence/roster_proof/ROSTER_PROOF_FF_fourth_and_forever.json")
    out.parent.mkdir(parents=True, exist_ok=True)

    def _write(complete: bool, runs, seconds):
        # #213b, and I rebuilt the defect it exists to close: the first version of this file
        # wrote only on its last line, and a container suspend at seat 8 of 12 destroyed all
        # eight. Written after EVERY seat now, with `complete` saying which kind of file a
        # reader is holding.
        store_io.write(out, {
            "league": "Fourth and Forever", "rulebook": str(CAPTURE), "complete": complete,
            "teams": teams, "rounds": rounds, "draft_type": "snake (ASSUMED)",
            "shared_pool": len(points), "seats_done": len(runs), "seats_total": len(seats),
            "summary": _summary(runs), "seats": runs, "seconds": round(seconds, 1)})

    def _summary(runs):
        if not runs:
            return {}
        out_ = {}
        for ruler in rp.RULERS:
            q = rp.COMPARE_ON[ruler]
            wins = sum(1 for r in runs if r["engine"][ruler][q] > r["control_mean"][ruler][q])
            eng = sum(r["engine"][ruler][q] for r in runs) / len(runs)
            ctl = sum(r["control_mean"][ruler][q] for r in runs) / len(runs)
            out_[ruler] = {"wins": wins, "of": len(runs), "engine_mean": round(eng, 2),
                           "control_mean": round(ctl, 2),
                           "pct": round((eng / ctl - 1) * 100, 2) if ctl else None}
        return out_

    runs, t0 = [], time.time()
    for seat in seats:                                                 # seat control, rule 8
        picks = rp.run_one(merger, players_db, league, pick_order, seat,
                           points, season, rounds, slots)
        engine = rp.score_roster(picks, seat, players_db, rulers, slots)
        control_seats = [s for s in seats if s != seat]
        controls = [rp.score_roster(picks, s, players_db, rulers, slots) for s in control_seats]
        row = {"engine_seat": seat, "engine": engine,
               "control_mean": {r: {q: sum(c[r][q] for c in controls) / len(controls)
                                    for q in engine[r]} for r in rp.RULERS}}
        runs.append(row)
        line = "  ".join(
            f"{r}: eng {engine[r][rp.COMPARE_ON[r]]:8.2f} vs ctl "
            f"{row['control_mean'][r][rp.COMPARE_ON[r]]:8.2f}" for r in rp.RULERS)
        print(f"seat {seat:>2}  {line}", flush=True)
        _write(complete=False, runs=runs, seconds=time.time() - t0)    # every seat, #213b

    print()
    summary = _summary(runs)
    for ruler in rp.RULERS:
        note = ("TAUTOLOGY -- the engine's own objective" if ruler == "cdme"
                else "THE STRONG CLAIM -- the control's own game")
        srow = summary[ruler]
        print(f"  ruler {ruler:7} on {rp.COMPARE_ON[ruler]:13}: engine ahead in "
              f"{srow['wins']} of {srow['of']} seats   eng {srow['engine_mean']:9.2f} vs ctl "
              f"{srow['control_mean']:9.2f}  ({srow['pct']:+.2f}%)   {note}")
    _write(complete=True, runs=runs, seconds=time.time() - t0)
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
