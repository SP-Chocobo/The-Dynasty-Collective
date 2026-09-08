"""#216 implementer's probe (Fable). Run FROM THE REPO ROOT:

    PYTHONPATH=. python3 run_216_fix_probe.py --out /abs/dir [--formats 12T_ppr,12T_ppr_SF] [--seats 1,6,12]

Four arms, ONE process, ONE code version (engine-measurement skill). The only things toggled:

  BASE_ON   displacement term OFF (draft_room.displacement_adjustments patched to return {}),
            feasibility_first as shipped        -> the pre-fix engine; REPLAY GATE against the
                                                   recorded #216 sequences (must match 6/6)
  BASE_OFF  displacement OFF, backstop OFF        -> the pre-fix value board alone (the defect)
  FIX_ON    displacement ON,  backstop as shipped -> the fixed engine as a user meets it
  FIX_OFF   displacement ON,  backstop OFF        -> the fixed value board ALONE (gate G1)

Every non-engine seat is run_roster_proof.control_pick. Per state: the board's own first row
(after pick_synthesis._board_order, the second ordering authority), its decomposition, whether
the backstop bound, the best remaining QB's price, the WR/TE level gap on the league anchor and
on the acquisition ledger. Written after every draft so a container reclaim loses at most one.
"""
from __future__ import annotations

import argparse
import collections
import json
import time
from pathlib import Path
from unittest import mock

import pandas as pd

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import lineup_optimizer as lo
import pick_synthesis as ps
import resume_join
import run_draft_battery as rdb
import run_roster_proof as rp
from player_universe import player_eligible_positions

ARMS = ("BASE_ON", "BASE_OFF", "FIX_ON", "FIX_OFF")
RECORDED = Path("evidence/roster_shape/ROSTER_SHAPE_2026-09-08_bfc3d47.json")
DECOMP = ("player_id", "name", "position", "projected_points", "bpa", "time_horizon_adj",
          "universal_value", "need_bonus", "eligibility_bonus", "depth_exposure",
          "displacement_adj", "displacement_basis", "final_score", "fills_required_slot")


def _mean(values):
    vals = [v for v in values if v is not None]
    return (round(sum(vals) / len(vals), 2), len(vals)) if vals else (None, 0)


def asset_and_character(picks, seat, players_db, rulers, slots, horizon_map):
    """G9 (owner's gate): the #205 asset ruler on the finished roster (run_roster_proof's own
    score_roster, both rulers), plus mean age and mean pre-draft time_horizon_adj."""
    mine = [p["player_id"] for p in picks if str(p["roster_id"]) == str(seat)]
    scored = rp.score_roster(picks, seat, players_db, rulers, slots)
    age, n_age = _mean((players_db.get(pid) or {}).get("age") for pid in mine)
    horizon, n_h = _mean(horizon_map.get(pid) for pid in mine)
    return {"cdme_total_value": scored["cdme"]["total_value"], "cdme_starter_value": scored["cdme"]["starter_value"],
            "cdme_unpriced": scored["cdme"]["unpriced"], "points_starter_value": scored["points"]["starter_value"],
            "mean_age": age, "age_n": n_age, "mean_predraft_horizon_adj": horizon, "horizon_n": n_h,
            "players": len(mine)}


def _name(players_db, pid):
    info = players_db.get(str(pid)) or {}
    return " ".join(x for x in (info.get("first_name"), info.get("last_name")) if x) or str(pid)


def _pos(players_db, pid):
    return (players_db.get(str(pid)) or {}).get("position") or "?"


def _decomp(row):
    return {k: row.get(k) for k in DECOMP}


def _levels(board):
    out = {}
    for r in board:
        if r.get("bpa") is not None and r.get("projected_points") is not None and r["position"] not in out:
            out[r["position"]] = round(r["projected_points"] - r["bpa"], 2)
    return out


def _no_backstop(scored, *a, **k):
    return pd.Series(1, index=scored.index, dtype=int)


def _no_displacement(roster_players, roster_positions, levels, unpriced_eligible=None):
    return {}


def build_board(arm, merger, players_db, picks, seat, league, season):
    kw = dict(my_roster_id=seat, league=league, mode="balanced",
              sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    patches = []
    if arm.endswith("_OFF"):
        patches.append(mock.patch.object(dr, "feasibility_first", _no_backstop))
    if arm.startswith("BASE"):
        patches.append(mock.patch.object(dr, "displacement_adjustments", _no_displacement))
    for p in patches:
        p.start()
    try:
        return dr.compute_draft_board(merger, players_db, picks, **kw)
    finally:
        for p in patches:
            p.stop()


def lineup_points(ids, points, players_db, slots):
    players = [{"id": pid, "value": float(points[pid]), "eligible": set(player_eligible_positions(players_db.get(pid) or {}))}
               for pid in ids if pid in points]
    return lo.optimize_lineup(players, slots)["total_value"]


def draft_one(arm, merger, players_db, league, pick_order, seat, points, season, rounds, slots, log,
              rulers=None, horizon_map=None):
    roster_positions = league["roster_positions"]
    num_teams = len(set(str(r) for r in pick_order))
    superflex = "SUPER_FLEX" in roster_positions
    picks, taken, mine = [], set(), collections.defaultdict(list)
    seq, states = [], []
    order_gate_failures = 0
    for idx in range(min(len(pick_order), rounds * num_teams)):
        who = str(pick_order[idx])
        rnd = idx // num_teams + 1
        free = [p for p in points if p not in taken]
        if not free:
            break
        if who != seat:
            chosen = rp.control_pick(free, points, mine[who], players_db, slots)
        else:
            t0 = time.time()
            board = build_board(arm, merger, players_db, picks, seat, league, season)
            live = [r for r in board if str(r["player_id"]) in points and str(r["player_id"]) not in taken]
            board_first = live[0]
            reordered = sorted(live, key=ps._board_order)[0]
            if str(reordered["player_id"]) != str(board_first["player_id"]):
                order_gate_failures += 1
            chosen_row = reordered
            chosen = str(chosen_row["player_id"])
            priced = [r for r in live if r.get("final_score") is not None]
            pure = min(priced, key=lambda r: (-r["final_score"], str(r["player_id"]))) if priced else None
            my_counts = dict(collections.Counter(_pos(players_db, p) for p in mine[seat]))
            qbs = [r for r in priced if r["position"] == "QB"]
            best_qb = max(qbs, key=lambda r: r["projected_points"] or 0) if qbs else None
            lv = _levels(live)
            disp = {}
            for r in priced:
                if r.get("displacement_adj") is not None and r["position"] not in disp:
                    disp[r["position"]] = (r["displacement_adj"], r.get("displacement_basis"))
            states.append({
                "round": rnd, "index": idx, "seconds": round(time.time() - t0, 2),
                "chosen": _decomp(chosen_row),
                "overrode": pure is not None and str(pure["player_id"]) != chosen,
                "pure_top": _decomp(pure) if pure else None,
                "my_counts_before": my_counts,
                "qb_slot_filled": my_counts.get("QB", 0) >= (1 if not superflex else 1),
                "best_qb": _decomp(best_qb) if best_qb else None,
                "league_levels": lv,
                "league_gap_WR_minus_TE": round(lv["WR"] - lv["TE"], 2) if "WR" in lv and "TE" in lv else None,
                "displacement_by_position": disp,
                "ledger_gap_WR_minus_TE": (round(lv["WR"] - lv["TE"] - (disp.get("WR", (0,))[0] - disp.get("TE", (0,))[0]), 2)
                                           if "WR" in lv and "TE" in lv else None),
                "top5": [(r["name"], r["position"], r["final_score"], r.get("displacement_adj")) for r in sorted(live, key=ps._board_order)[:5]],
            })
            seq.append({"round": rnd, "player": _name(players_db, chosen), "position": _pos(players_db, chosen),
                        "projected_points": round(points[chosen], 1),
                        "fills_required_slot": bool(chosen_row.get("fills_required_slot"))})
            log(f"    {arm:8s} seat {seat:>2s} r{rnd:02d} {_pos(players_db, chosen):3s} {_name(players_db, chosen):24s} "
                f"{points[chosen]:6.1f} fs={chosen_row.get('final_score')} disp={chosen_row.get('displacement_adj')} "
                f"req={chosen_row.get('fills_required_slot')} ({time.time() - t0:.1f}s)")
        taken.add(str(chosen))
        mine[who].append(str(chosen))
        picks.append({"pick_no": idx + 1, "round": rnd, "roster_id": who, "player_id": str(chosen)})
    order = [str(s) for s in pick_order[:num_teams]]
    control_seat = order[(order.index(str(seat)) + 1) % len(order)]
    dedicated = dr.dedicated_slot_counts(roster_positions)
    composition = dict(collections.Counter(r["position"] for r in seq))
    return {
        "arm": arm, "seat": seat, "sequence": seq, "states": states,
        "composition": composition,
        "missing_dedicated": {p: dedicated[p] - composition.get(p, 0) for p in dedicated if dedicated[p] > composition.get(p, 0)},
        "unfillable_starting_slots": sorted(rp.unmet_slot_positions(mine[seat], players_db, slots)),
        "forced": sum(1 for s in seq if s["fills_required_slot"]),
        "overrode": sum(1 for s in states if s["overrode"]),
        "order_gate_failures": order_gate_failures,
        "lineup_points": lineup_points(mine[seat], points, players_db, slots),
        "roster_points": round(sum(points[p] for p in mine[seat]), 1),
        "control_seat": control_seat,
        "control_composition": dict(collections.Counter(_pos(players_db, p) for p in mine[control_seat])),
        "control_lineup_points": lineup_points(mine[control_seat], points, players_db, slots),
        "all_seats_lineup_points": {s: lineup_points(ids, points, players_db, slots) for s, ids in mine.items()},
        "qb_rounds": [s["round"] for s in seq if s["position"] == "QB"],
        # G9 (owner's gate): the asset ruler and the roster's age/horizon character, for the
        # engine seat and for the same control seat, so a reversal can be read per seat.
        "g9_engine": (asset_and_character(picks, seat, players_db, rulers, slots, horizon_map)
                      if rulers is not None else None),
        "g9_control": (asset_and_character(picks, control_seat, players_db, rulers, slots, horizon_map)
                       if rulers is not None else None),
        "engine_mean_at_pick_horizon_adj": _mean(s["chosen"].get("time_horizon_adj") for s in states)[0],
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--formats", default="12T_ppr,12T_ppr_SF")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--seats", default="1,6,12")
    args = ap.parse_args(argv)
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "probe.log"

    def log(msg):
        print(msg, flush=True)
        with log_path.open("a") as fh:
            fh.write(msg + "\n")

    commit = resume_join.head_commit()
    scoring = rdb.scoring_settings_from_capture()
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    recorded = json.loads(RECORDED.read_text()) if RECORDED.exists() else None
    for fmt_label in args.formats.split(","):
        spec = next(s for s in rp.PROOF_FORMATS if s["label"] == fmt_label)
        league = dr.build_mock_league(teams=spec["teams"], superflex=spec["superflex"], scoring=spec["scoring"],
                                      te_premium=spec["te_premium"], dynasty=True, base_scoring=scoring)
        merger.set_league_format(db.league_format_hint(league))          # NEVER SKIP
        points = rp.scoreable_pool(merger, players_db, league, season)
        # G9: the #205 asset ruler (pre-draft board universal_value, run_roster_proof's own
        # `values`) and the pre-draft horizon adjustment per player, roster-independent.
        values = db.reference_values(merger, players_db, league, sleeper_projections=season,
                                     sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        rulers = {"cdme": values, "points": points}
        predraft = dr.compute_draft_board(merger, players_db, [], None, league, mode="balanced",
                                          sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        horizon_map = {str(r["player_id"]): r.get("time_horizon_adj") for r in predraft}
        seats = [str(i) for i in range(1, spec["teams"] + 1)]
        rounds = len(league["roster_positions"])
        slots = lo.slots_from_roster_positions(league["roster_positions"])
        pick_order = ds.generate_pick_order(seats, rounds, "snake")
        rec_seq = {}
        if recorded:
            for fmt in recorded["formats"]:
                if fmt["label"] == fmt_label:
                    for s in fmt["per_seat"]:
                        rec_seq[s["seat"]] = [r["player"] for r in s["engine_picks"]]
        out_path = out_dir / f"{fmt_label}.json"
        log(f"commit {commit} | {fmt_label} | pool {len(points)} "
            f"{dict(collections.Counter(_pos(players_db, p) for p in points))} | rounds {rounds}")
        results = {"commit": commit, "format": fmt_label, "roster_positions": league["roster_positions"],
                   "pool_size": len(points), "universe": universe, "drafts": []}
        started = time.time()
        for seat in args.seats.split(","):
            for arm in args.arms.split(","):
                t0 = time.time()
                d = draft_one(arm, merger, players_db, league, pick_order, seat, points, season, rounds, slots, log,
                              rulers=rulers, horizon_map=horizon_map)
                if arm == "BASE_ON" and seat in rec_seq:
                    mine = [r["player"] for r in d["sequence"]]
                    d["replay_matches_recorded"] = mine == rec_seq[seat]
                    d["first_mismatch"] = next(((i + 1, a, b) for i, (a, b) in enumerate(zip(mine, rec_seq[seat])) if a != b), None)
                d["seconds"] = round(time.time() - t0, 1)
                results["drafts"].append(d)
                results["seconds_total"] = round(time.time() - started, 1)
                out_path.write_text(json.dumps(results, indent=1, default=str))
                log(f"  == {arm} seat {seat}: {d['composition']} lineup {d['lineup_points']} forced {d['forced']} "
                    f"overrode {d['overrode']} missing {d['missing_dedicated']} unfillable {d['unfillable_starting_slots']} "
                    f"QB rounds {d['qb_rounds']} order_gate_failures {d['order_gate_failures']} | control {d['control_composition']} "
                    f"lineup {d['control_lineup_points']}"
                    + (f" | replay={d.get('replay_matches_recorded')} {d.get('first_mismatch')}" if arm == "BASE_ON" else "")
                    + f" ({d['seconds']}s)")
        log(f"-> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
