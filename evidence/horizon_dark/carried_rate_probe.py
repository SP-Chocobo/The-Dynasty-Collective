"""Is a carried bench-appetite rate "raw BPA with a different name"? Measure it, don't argue it.

THE OWNER'S OBJECTION, which is the reason this file exists: the proposed repair for the
horizon going dark after round 10 was "carry the opening-board decay rate forward, labelled as
carried". The objection was that **a locked curve feels like raw BPA with a different name**,
and that the method "would need to be flushed out pretty aggressively". That is the right
objection to the repair AS I STATED IT, and it is answerable with numbers rather than prose.

WHAT ACTUALLY GOES DARK. `_bench_appetite_rates` measures, per position, the fractional value
drop between rank `demand` and rank `2 x demand` in the CURRENTLY UNDRAFTED PRICED pool:

    rate = 1 - value[2*demand - 1] / value[demand - 1]

It needs `2 x demand` priced rows to exist at that position. Once the board thins under that
bar the position is unmeasurable and takes the mean of whoever is still measurable; once NO
position is measurable, `positional_bench_appetite` returns all-None, `estimated_bench_demand`
returns all-None, and `horizon_replacement` stops placing a floor at all. Measured on the 12T
superflex PPR board: one position measurable after 96 picks, zero after 108.

THREE ARMS, one process, one code version, one pick stream, differing only in what fills an
unmeasurable position's rate:

    A  STATUS QUO   live measurement only; all-or-nothing collapse to None when none is left
    B  HYBRID       live measurement per position where it is available; the OPENING-BOARD
                    rate carried for a position that has fallen under its own bar
    C  LOCKED       opening-board rates always, never re-measured -- the strawman, built on
                    purpose so the objection has something to be true or false ABOUT

B is the proposal. C is what the objection describes. **If B and C are the same numbers, the
objection is correct and the proposal is BPA with a different name. If they differ, the size of
the difference is exactly how much live re-measurement is still contributing after the carry.**

AND THE SECOND HALF OF THE QUESTION -- can a run of five RBs off the board move the curve? --
is measured here as a RESIDUAL rather than as a re-measured rate. A shorter-span rate is not
comparable to a full-span one (the span is in the units), which is why re-measuring over
`demand..demand+k` is not available. The residual is: what did arm B's appetite predict the
last N picks would spend per position, and what did the board actually spend? That quantity is
in PICKS, is dimensionless across positions, and needs no new constant to state. Whether it
carries a usable signal is what the `residual` block reports. If it is noise, the trending term
has nothing to bite on and that is the finding.

THREE CELLS, AND THE THIRD IS THE ONE THAT MATTERS. `sleeper_projections` is what `#180`
wired into the board so the league's own scoring reaches a price. Production passes it on ONE
of its three `build_snapshot` call sites -- the live Draft Room -- and not on the other two, the
Mock Draft and the edit-an-earlier-pick path. That is not a cosmetic difference: with the
projections the fixture board prices 481 players, without them 256, and the horizon estimator's
whole question is whether a position still has `2 x demand` PRICED rows. So the cells are

    12T_ppr_SF_DRAFTROOM                 priced the way the live Draft Room prices
    CAPTURE_fourth_and_forever_DRAFTROOM  ditto, on the owner's real 26-round league
    12T_ppr_SF_MOCKDRAFT                  the SAME league and the SAME pick stream, priced the
                                          way the Mock Draft prices it

The pick stream is deliberately held FIXED across all three: the control drafts from one
priceable set, so the board that arrives at each sample is identical and the pricing path is
the single variable. Any difference in measurability between cells one and three is caused by
the projections and by nothing else.

NOT A REPAIR. Nothing here changes production. It is the measurement that decides whether the
repair is worth building and in which of the three shapes.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

# This probe lives in a subdirectory, so sys.path[0] is that subdirectory rather than the repo
# root, and every engine import below would miss. The repo root stays the WORKING directory --
# DataMerger resolves its baseline paths against the cwd, and a probe that cd'd into its own
# folder loaded an empty frame and only said so three calls later (engine-measurement, rule 1).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import lineup_optimizer as lo
import run_draft_battery as rdb
import run_roster_proof as rp
import store_io

OUT = Path("evidence/horizon_dark/CARRIED_RATE_PROBE.json")
FF_CAPTURE = Path("data/league_captures/fourth_and_forever.json")
STRIDE = 12          # one full round of a 12-team league
RESIDUAL_WINDOW = 12 # picks to compare predicted spend against observed spend


def ff_league() -> dict:
    cap = json.loads(FF_CAPTURE.read_text(encoding="utf-8"))
    league = {"roster_positions": cap["roster_positions"],
              "scoring_settings": {k: v["value"] for k, v in cap["scoring_settings_observed"].items()},
              "total_rosters": 12, "settings": {"type": 2}}
    league["draft_rounds"] = dr.draftable_slots_per_team(league["roster_positions"])
    return league


def fixture_league() -> dict:
    league = dr.build_mock_league(teams=12, superflex=True, scoring="ppr", te_premium=False,
                                 dynasty=True, base_scoring=rdb.scoring_settings_from_capture())
    league["draft_rounds"] = len(league["roster_positions"])
    return league


def pool_at(merger, players_db, league, projections, picks):
    """The board's own pool, built exactly the way compute_draft_board builds it."""
    drafted = {str(p["player_id"]) for p in picks if p.get("player_id")}
    pool = dr.build_available_pool(
        merger, players_db, drafted, dr.league_usable_positions(league["roster_positions"]),
        sleeper_projections=projections, scoring_settings=league.get("scoring_settings"),
        pool_scope="all", sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
    )
    # `_points` is attached by compute_draft_board, not by build_available_pool, and every
    # horizon function reads that column. _derive_points_and_source is the extraction that
    # exists so a second caller gets an IDENTICALLY derived frame rather than a drifting copy
    # -- which is exactly what this probe needs, and re-deriving it here by hand would be the
    # two-representations-of-one-concept defect the module fights.
    dr._derive_points_and_source(pool)
    return pool


def floors(pool, league, picks, players_db) -> dict:
    h = dr.horizon_replacement(pool, "_points", league["roster_positions"],
                               league["total_rosters"], picks, players_db)
    return {p: d["value"] for p, d in h.items()}


def main() -> int:
    print(f"universe : rdb.build_players_db_from_capture() <- {rdb.CAPTURE_PATH}")
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    print(f"pool     : {universe['players_in_pool']} players, {len(season)} season projections\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    results, t0 = [], time.time()
    real_rates = dr._bench_appetite_rates

    for label, league, projections in (
            ("12T_ppr_SF_DRAFTROOM", fixture_league(), season),
            ("CAPTURE_fourth_and_forever_DRAFTROOM", ff_league(), season),
            ("12T_ppr_SF_MOCKDRAFT", fixture_league(), None)):
        hint = db.league_format_hint(league)
        merger.set_league_format(hint)                                   # rule 3, never skip
        rounds = int(league["draft_rounds"])
        slots = lo.slots_from_roster_positions(league["roster_positions"])
        seats = [str(i) for i in range(1, 13)]
        pick_order = ds.generate_pick_order(seats, rounds, "snake")
        points = rp.scoreable_pool(merger, players_db, league, season)
        print(f"{label}  hint={hint} rounds={rounds} startable={len(slots)} "
              f"priceable={len(points)}", flush=True)

        # A control-only board: a realistic pick stream, and deliberately NOT engine-driven --
        # the question here is how the ESTIMATOR responds to a board, not who picked.
        picks, taken, mine = [], set(), {}
        for idx in range(min(len(pick_order), rounds * 12)):
            seat = str(pick_order[idx])
            free = [pid for pid in points if pid not in taken]
            chosen = rp.control_pick(free, points, mine.get(seat, []), players_db, slots) if free else None
            if chosen is None:
                break
            taken.add(str(chosen))
            mine.setdefault(seat, []).append(str(chosen))
            picks.append({"pick_no": idx + 1, "round": idx // 12 + 1,
                          "roster_id": seat, "player_id": str(chosen)})
        print(f"  control board: {len(picks)} picks", flush=True)

        # The opening-board rates -- what arms B and C carry.
        opening_pool = pool_at(merger, players_db, league, projections, [])
        opening_demands, opening_rates = real_rates(
            opening_pool, "_points", league["roster_positions"], league["total_rosters"])
        print(f"  opening rates measurable: {sorted(opening_rates)} "
              f"of demanded {sorted(p for p, d in opening_demands.items() if d >= 1)}", flush=True)

        def hybrid(pool, value_col, roster_positions, num_teams):
            demands, rates = real_rates(pool, value_col, roster_positions, num_teams)
            out = dict(rates)
            for position, rate in opening_rates.items():
                if demands.get(position, 0) >= 1 and position not in out:
                    out[position] = rate                  # carried, only where live went dark
            return demands, out

        def locked(pool, value_col, roster_positions, num_teams):
            demands, _ = real_rates(pool, value_col, roster_positions, num_teams)
            return demands, dict(opening_rates)           # never re-measured

        rows = []
        entry = {"label": label, "hint": hint, "rounds": rounds, "picks": len(picks),
                 "opening_rates": {k: round(v, 6) for k, v in opening_rates.items()},
                 "opening_demands": opening_demands, "stride": STRIDE, "samples": rows}
        results.append(entry)

        for t in range(0, len(picks) + 1, STRIDE):
            sofar = picks[:t]
            pool = pool_at(merger, players_db, league, projections, sofar)
            demands, live = real_rates(pool, "_points", league["roster_positions"],
                                       league["total_rosters"])
            arms = {}
            for arm, fn in (("A_status_quo", real_rates), ("B_hybrid", hybrid), ("C_locked", locked)):
                dr._bench_appetite_rates = fn
                try:
                    arms[arm] = floors(pool, league, sofar, players_db)
                finally:
                    dr._bench_appetite_rates = real_rates

            # What the last window of picks actually spent, against what B's appetite implied.
            window = picks[max(0, t - RESIDUAL_WINDOW):t]
            observed = {}
            for p in window:
                pos = (players_db.get(str(p["player_id"])) or {}).get("position")
                if pos:
                    observed[pos] = observed.get(pos, 0) + 1
            dr._bench_appetite_rates = hybrid
            try:
                app = dr.positional_bench_appetite(pool, "_points", league["roster_positions"],
                                                   league["total_rosters"])
            finally:
                dr._bench_appetite_rates = real_rates
            total = sum(v for v in app.values() if v)
            predicted = ({p: (v or 0.0) / total * len(window) for p, v in app.items()}
                         if total else {})

            rows.append({
                "picks_made": t, "round": t // 12 + 1,
                "priced_left": int(pool["_points"].notna().sum()),
                "measurable_live": sorted(live),
                "rate_live": {k: round(v, 6) for k, v in live.items()},
                "floors": {arm: {p: (None if v is None else round(float(v), 3))
                                 for p, v in f.items()} for arm, f in arms.items()},
                "observed_window": observed,
                "predicted_window": {k: round(v, 3) for k, v in predicted.items()},
                "residual_window": {k: round(observed.get(k, 0) - v, 3)
                                    for k, v in predicted.items()},
            })
            store_io.write(OUT, {"complete": False, "arms": results,
                                 "seconds": round(time.time() - t0, 1)})
            a = rows[-1]["floors"]["A_status_quo"]
            b = rows[-1]["floors"]["B_hybrid"]
            c = rows[-1]["floors"]["C_locked"]
            live_n = len(live)
            defined = sum(1 for v in a.values() if v is not None)
            bc = [abs(b[p] - c[p]) for p in b if b[p] is not None and c[p] is not None]
            print(f"    picks {t:>3}  priced {rows[-1]['priced_left']:>4}  "
                  f"live-measurable {live_n}  A-defined {defined:>2}/{len(a)}  "
                  f"|B-C| mean {statistics.mean(bc) if bc else float('nan'):8.3f} "
                  f"max {max(bc) if bc else float('nan'):8.3f}", flush=True)

    store_io.write(OUT, {"complete": True, "arms": results,
                         "seconds": round(time.time() - t0, 1)})
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
