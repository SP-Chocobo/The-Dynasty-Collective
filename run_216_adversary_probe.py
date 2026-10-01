"""#216 ADVERSARY instrument: the measurements behind test_216_value_board_falsification.py.

    python3 run_216_adversary_probe.py [--out PATH]

Committed so the numbers quoted in that test file can be re-derived and challenged rather than
cited (#177's harness was lost to a scratchpad; this one is not). Two measurements, one process,
one code version, the engine-measurement fixture throughout:

FEEDBACK (pool held identical). Both states: I own TE#1, rival "2" owns TE#5. TE#2-#4 then go
to the rival (A: I own one) or to me (B: I own four). The league's remaining starter demand is
identical, the same rows leave the pool, so every row's universal_value must match across the
states -- counted, not assumed -- and the only difference is my roster. The next TE's
final_score swing A-B is the whole roster-aware counterweight; level_WR - level_TE, read off
the rows, is the positional bias a surplus TE is handed for free.

ABLATION (the load-bearing one). Engine at one seat, the roster-proof control at every other,
with feasibility_first as shipped (ON) and replaced by its documented no-op (OFF). Per pick:
whether the backstop bound and whether it overrode the pure team_acquisition_value argmax. Per
roster: composition, named-slot legality, and full-lineup fillability by the shipped optimizer.

Run from the repo root. Writes after every arm.
"""

from __future__ import annotations

import argparse
import collections
import json
import time
from pathlib import Path

import pandas as pd

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import lineup_optimizer as lo
import resume_join
import run_draft_battery as rdb
import run_roster_proof as rp

FORMATS = ("12T_ppr", "12T_ppr_SF")
ABLATION_SEATS = {"12T_ppr": ("1", "6", "12"), "12T_ppr_SF": ("1",)}


def _pos(players_db, pid):
    return (players_db.get(str(pid)) or {}).get("position") or "?"


def _name(players_db, pid):
    info = players_db.get(str(pid)) or {}
    return " ".join(x for x in (info.get("first_name"), info.get("last_name")) if x) or str(pid)


def _pick(pid, roster, pick_no, rnd):
    return {"pick_no": pick_no, "round": rnd, "roster_id": roster, "player_id": str(pid)}


def _levels(board):
    by = collections.defaultdict(list)
    for r in board:
        if r.get("bpa") is not None and r.get("projected_points") is not None:
            by[r["position"]].append(round(r["projected_points"] - r["bpa"], 3))
    return {p: {"n": len(v), "min": min(v), "max": max(v)} for p, v in by.items()}


def feedback(merger, players_db, season, league, points) -> dict:
    board = lambda picks: dr.compute_draft_board(
        merger, players_db, picks, "1", league, mode="balanced",
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    te = sorted((p for p in points if _pos(players_db, p) == "TE"), key=lambda p: (-points[p], p))
    base = [_pick(te[0], "1", 1, 1), _pick(te[4], "2", 2, 1)]
    a = base + [_pick(p, "2", 3 + i, 2) for i, p in enumerate(te[1:4])]
    b = base + [_pick(p, "1", 3 + i, 2) for i, p in enumerate(te[1:4])]
    ba = {str(r["player_id"]): r for r in board(a)}
    bb = {str(r["player_id"]): r for r in board(b)}
    differing = sum(1 for p in ba if ba[p].get("universal_value") != bb[p].get("universal_value"))
    ra, rb_ = ba[te[5]], bb[te[5]]
    lv = _levels(list(ba.values()))
    keys = ("projected_points", "universal_value", "need_bonus", "eligibility_bonus",
            "depth_exposure", "depth_basis", "final_score")
    # the k-series: my roster only, k = 0..6 tight ends
    series = []
    for k in range(7):
        rows = {str(r["player_id"]): r for r in board([_pick(te[i], "1", i + 1, i + 1) for i in range(k)])}
        lvk = _levels(list(rows.values()))
        fixed = rows.get(te[6])
        series.append({"k_te_owned": k, "gap_WR_minus_TE": round(lvk["WR"]["min"] - lvk["TE"]["min"], 2),
                       "te7_final": fixed["final_score"] if fixed else None,
                       "te7_uv": fixed["universal_value"] if fixed else None})
    return {"rows": len(ba), "uv_rows_differing": differing, "next_te": ra["name"],
            "state_A_own_one": {k: ra.get(k) for k in keys},
            "state_B_own_four": {k: rb_.get(k) for k in keys},
            "swing_A_minus_B": round(ra["final_score"] - rb_["final_score"], 2),
            "bias_levelWR_minus_levelTE": round(lv["WR"]["min"] - lv["TE"]["min"], 2),
            "levels": lv, "k_series_te7": series}


def ablation(merger, players_db, season, league, points, seat, backstop_on) -> dict:
    slots = lo.slots_from_roster_positions(league["roster_positions"])
    seats = [str(i) for i in range(1, league["total_rosters"] + 1)]
    rounds = len(league["roster_positions"])
    order = ds.generate_pick_order(seats, rounds, "snake")
    real = dr.feasibility_first
    if not backstop_on:
        dr.feasibility_first = lambda scored, *a, **k: pd.Series(1, index=scored.index, dtype=int)
    try:
        picks, taken, mine, log = [], set(), collections.defaultdict(list), []
        for idx, who in enumerate(str(s) for s in order):
            rnd = idx // len(seats) + 1
            free = [p for p in points if p not in taken]
            if not free:
                break
            if who == seat:
                board = dr.compute_draft_board(merger, players_db, picks, seat, league, mode="balanced",
                                               sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
                avail = [r for r in board if str(r["player_id"]) in points and str(r["player_id"]) not in taken]
                chosen_row = avail[0]
                priced = [r for r in avail if r.get("final_score") is not None]
                pure = min(priced, key=lambda r: (-r["final_score"], str(r["player_id"]))) if priced else None
                chosen = str(chosen_row["player_id"])
                log.append({"round": rnd, "chosen": _name(players_db, chosen), "position": _pos(players_db, chosen),
                            "final": chosen_row.get("final_score"), "bound": bool(chosen_row.get("fills_required_slot")),
                            "pure_value_top": _name(players_db, pure["player_id"]) if pure else None,
                            "overrode": pure is not None and str(pure["player_id"]) != chosen})
            else:
                chosen = rp.control_pick(free, points, mine[who], players_db, slots)
            taken.add(str(chosen)); mine[who].append(str(chosen))
            picks.append(_pick(chosen, who, idx + 1, rnd))
    finally:
        dr.feasibility_first = real
    comp = dict(collections.Counter(_pos(players_db, p) for p in mine[seat]))
    dedicated = dr.dedicated_slot_counts(league["roster_positions"])
    missing = {p: dedicated[p] - comp.get(p, 0) for p in dedicated if dedicated[p] > comp.get(p, 0)}
    unmet = sorted(rp.unmet_slot_positions(mine[seat], players_db, slots))
    return {"seat": seat, "backstop_on": backstop_on, "composition": comp,
            "missing_dedicated_slots": missing, "unfillable_starting_slots": unmet,
            "legal": not missing and not unmet,
            "backstop_bound_picks": sum(1 for l in log if l["bound"]),
            "backstop_overrode_picks": sum(1 for l in log if l["overrode"]),
            "sequence": " ".join(f"{l['round']}:{l['position']}{'*' if l['overrode'] else ''}" for l in log),
            "picks": log}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default="ADVERSARY_216.json")
    args = ap.parse_args(argv)
    started = time.time()
    scoring = rdb.scoring_settings_from_capture()
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    report = {"commit": resume_join.head_commit(), "universe": universe, "formats": []}
    out = Path(args.out)
    for spec in [s for s in rp.PROOF_FORMATS if s["label"] in FORMATS]:
        league = dr.build_mock_league(teams=spec["teams"], superflex=spec["superflex"], scoring=spec["scoring"],
                                      te_premium=spec["te_premium"], dynasty=True, base_scoring=scoring)
        merger.set_league_format(db.league_format_hint(league))          # rule 3, every format
        points = rp.scoreable_pool(merger, players_db, league, season)
        entry = {"label": spec["label"], "roster_positions": league["roster_positions"],
                 "pool": dict(collections.Counter(_pos(players_db, p) for p in points)), "pool_n": len(points)}
        entry["feedback"] = feedback(merger, players_db, season, league, points)
        fb = entry["feedback"]
        print(f"{spec['label']}: uv rows differing {fb['uv_rows_differing']}/{fb['rows']}; next TE {fb['next_te']} "
              f"own-one {fb['state_A_own_one']['final_score']} own-four {fb['state_B_own_four']['final_score']} "
              f"swing {fb['swing_A_minus_B']} bias {fb['bias_levelWR_minus_levelTE']}", flush=True)
        entry["ablation"] = []
        for seat in ABLATION_SEATS[spec["label"]]:
            for on in (True, False):
                arm = ablation(merger, players_db, season, league, points, seat, on)
                entry["ablation"].append(arm)
                print(f"  seat {seat} backstop={'ON ' if on else 'OFF'} {arm['composition']} legal={arm['legal']} "
                      f"overrode={arm['backstop_overrode_picks']}  {arm['sequence']}", flush=True)
                report["seconds"] = round(time.time() - started, 1)
                out.write_text(json.dumps({**report, "formats": report["formats"] + [entry]}, indent=2, default=str))
        report["formats"].append(entry)
    report["seconds"] = round(time.time() - started, 1)
    out.write_text(json.dumps(report, indent=2, default=str))
    print(f"-> {out} ({report['seconds']}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
