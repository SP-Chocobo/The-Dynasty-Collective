"""The empty cell of a factorial design nobody built on purpose -- and a defect in `#248` arm B.

Five arms have been measured across `#245`/`#248`/the flex cut, each added to answer its own
single-variable question. Laid on their real axes they looked like a 2x2x2 with one hole. Then
the smoke test for this file printed the arms' format hints, and the hole turned out to be two
holes, because ONE OF THE MEASURED ARMS IS NOT IN THE CELL IT WAS LABELLED WITH.

    #248 arm B was built as `build_mock_league(scoring="ppr", te_premium=False,
    base_scoring=<F&F's 30 observed keys>)` and called "fixture roster + F&F scoring".

    `build_mock_league` OVERWRITES `rec` from its own `scoring` argument -- that is its
    documented job, the rec/te-premium overlay being "the ONLY thing that varies between arms".
    So arm B ran at **rec = 1.0**, not F&F's 0.5. Its `te_premium=False` did not remove
    `bonus_rec_te` either: that key came through from `base_scoring`, so the arm carried a TE
    premium it was told not to have. Measured: `rec 1.0, bonus_rec_te 0.25, rec_fd 0.5,
    pass_cmp 0.1` -- and a resulting hint of `{"scoring": "ppr", "te_premium": True}`.

    That format exists in NEITHER league. Arm B moved first downs, the completion bonus and the
    TE premium, and left the single largest scoring lever -- the value of a reception -- at PPR.

This is not a small mislabel. `rec` does not reach offensive valuation through
`scoring_settings` at all; it reaches it by FILE SELECTION, because `set_league_format` picks a
different rankings export per hint. Arm B's hint said `ppr` and arm C's said `half_ppr`, so the
two arms drew from DIFFERENT EXPORTS -- a larger difference than the scoring keys, and exactly
the failure the engine-measurement checklist was written for.

CONSEQUENCE FOR `#248`: its conclusion "the rulebook moved alone: NO EFFECT" is weakened, not
destroyed. What arm B actually establishes is that first downs + completion bonus + TE premium,
at PPR reception value and on the PPR export, change the verdict by nothing. That is a real
result about part of the rulebook. It is not a result about the rulebook.

So the fixture-roster-with-F&F-scoring row was never occupied, at EITHER flex count. This file
runs both, with F&F's scoring supplied DIRECTLY rather than through `build_mock_league`'s
overlay -- the same way `#248`'s arm C supplied it for the F&F roster.

THREE ARMS, ONE PROCESS, ONE CODE VERSION, rounds pinned at 15:

    D2   fixture roster, FLEX 3, fixture PPR scoring   CONTROL -- must reproduce the flex cut's
                                                       D, 3/12, -0.84%
    B3   fixture roster, FLEX 2, TRUE F&F scoring      the cell #248 arm B was meant to occupy
    G    fixture roster, FLEX 3, TRUE F&F scoring      THE MISSING CELL

The flex slot is moved by EXCHANGING a BN for a FLEX, never appended, so `len(roster_positions)`
never moves and capacity is held fixed across every arm.

PRE-REGISTERED, before any number exists:
  G resembles C (~10/12) -> an INTERACTION between rulebook and flex. Neither moves the verdict
      alone; together they do. Every previous cut was underpowered by construction, and the
      "refuted" verdicts become "refuted AS MAIN EFFECTS".
  G resembles D2 (~3/12) AND B3 resembles D2 -> the true rulebook has no effect either, at
      either flex count. The F&F ROSTER carries the reversal beyond its flex count, and since
      capacity is fenced off from the pick path, the remaining difference is TAXI (F&F 5,
      fixture 0) -- which would need its own path to the board found and named.
  B3 differs from `#248`'s published arm B (4/12, -0.61%) -> the rec/export half of the rulebook
      is doing work that arm B could not see, and `#248`'s rulebook refutation is CORRECTED
      rather than merely qualified.
  D2 fails to reproduce -> the harness moved. No claim from this run.
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
ROUNDS = 15
OUT = Path("evidence/roster_proof/ROSTER_PROOF_MISSING_CELL.json")


def ff_scoring() -> dict:
    cap = json.loads(FF_CAPTURE.read_text(encoding="utf-8"))
    return {k: v["value"] for k, v in cap["scoring_settings_observed"].items()}


def swap_one(roster_positions: list[str], frm: str, to: str) -> list[str]:
    """Exchange exactly one `frm` slot for a `to` slot. Raises rather than returning an
    unchanged roster -- an arm that silently failed to move its own variable is the artifact
    this whole family of files exists to avoid. Same rule as the flex cut's swap."""
    out = list(roster_positions)
    if frm not in out:
        raise ValueError(f"no {frm} slot to exchange in {collections.Counter(out)}")
    out[out.index(frm)] = to
    before, after = collections.Counter(roster_positions), collections.Counter(out)
    if len(out) != len(roster_positions):
        raise AssertionError("length moved; the cut is no longer single-variable")
    changed = {k for k in set(before) | set(after) if before[k] != after[k]}
    if changed != {frm, to}:
        raise AssertionError(f"exchange moved more than {frm}/{to}: {changed}")
    return out


def fixture_roster(flex3: bool) -> list[str]:
    """The fixture mock league's roster_positions, optionally at FLEX 3."""
    base = dr.build_mock_league(teams=12, superflex=True, scoring="ppr", te_premium=False,
                                dynasty=True, base_scoring={})["roster_positions"]
    return swap_one(base, "BN", "FLEX") if flex3 else list(base)


def league_with(scoring: dict, flex3: bool) -> dict:
    """A Sleeper-shaped league built DIRECTLY, so the scoring dict passed is the scoring dict
    used. `build_mock_league` is deliberately not used to carry a rulebook: it overwrites `rec`
    from its own `scoring` argument and leaves any `bonus_rec_te` already present in
    `base_scoring` in place, which is how `#248` arm B ended up at rec 1.0 with a TE premium it
    was told not to have. Same construction `#248`'s arm C used for the F&F roster."""
    return {"roster_positions": fixture_roster(flex3), "scoring_settings": dict(scoring),
            "total_rosters": 12, "settings": {"type": 2}, "draft_rounds": ROUNDS}


def arms() -> list[dict]:
    fixture_scoring = rdb.scoring_settings_from_capture()
    ffs = ff_scoring()
    return [
        {"label": "D2_fixture_FLEX3_pprScoring", "league": league_with(fixture_scoring, True),
         "expect": "CONTROL: reproduces the flex cut's D, 3/12, -0.84%"},
        {"label": "B3_fixture_FLEX2_trueFFScoring", "league": league_with(ffs, False),
         "expect": "the cell #248 arm B was MEANT to occupy -- no prior value"},
        {"label": "G_fixture_FLEX3_trueFFScoring", "league": league_with(ffs, True),
         "expect": "THE MISSING CELL -- no prior value"},
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
    print(f"rulebook source : {FF_CAPTURE}")
    print(f"universe        : rdb.build_players_db_from_capture() <- {rdb.CAPTURE_PATH}")
    print(f"rounds          : {ROUNDS}\n")

    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    print(f"pool            : {universe['players_in_pool']} players, "
          f"{len(season)} season projections\n")

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
    print("ARM SUMMARY (points, the strong claim)")
    for e in results:
        s = e["summary"]["points"]
        print(f"  {e['label']:30s} FLEX{e['flex_slots']} {s['wins']:2d}/{s['of']:<2d} "
              f"{s['pct']:+6.2f}%  margin {s['margin']:+8.2f}   {e['expect']}")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
