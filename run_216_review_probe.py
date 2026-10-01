"""#216 adversarial review probe (Fable). Run FROM THE REPO ROOT:

    python3 run_216_review_probe.py --format 12T_ppr --out /abs/dir

Five arms, one process, one code version (engine-measurement skill: both arms run the same code,
toggle only the thing under test):

  CURRENT   the production board's own first row (replay gate: must reproduce the recorded #216
            sequence pick-for-pick, otherwise this instrument is not reading the engine)
  NOFEAS    CURRENT with feasibility_first disabled -> does the WR/WR/QB tail survive?
  NEEDCAP   CURRENT with NEED_BONUS_MAX = 1e9    -> does the CAP constant bind at all here?
  RFMLV     replacement-filled marginal lineup value replaces bpa + need_bonus
            (every empty starting slot is pre-filled with a phantom at that slot's replacement
            level, then score = lineup(R+phantoms+X) - lineup(R+phantoms); horizon/risk/
            eligibility/depth kept exactly as they are; no new constant)
  RAWMLV    #84's marginal_lineup_value as built (no phantoms) -- the version the contract
            says was rightly stranded

Every non-engine seat is run_roster_proof.control_pick, exactly as in run_roster_shape_probe.
Results are written after every (seat, arm) so a container reclaim loses at most one draft.
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

SEATS = ("1", "6", "12")
ARMS = ("CURRENT", "NOFEAS", "NEEDCAP", "RFMLV_LEX", "RFMLV_ADD", "RAWMLV_LEX")
RECORDED = Path("evidence/roster_shape/ROSTER_SHAPE_2026-09-08_bfc3d47.json")
DECOMP = ("name", "position", "projected_points", "bpa", "time_horizon_adj", "risk_adj",
          "universal_value", "need_bonus", "eligibility_bonus", "depth_exposure", "depth_basis",
          "final_score", "fills_required_slot", "replacement_basis", "waiting_cost")


def _name(players_db, pid):
    info = players_db.get(str(pid)) or {}
    return " ".join(x for x in (info.get("first_name"), info.get("last_name")) if x) or str(pid)


def _pos(players_db, pid):
    return (players_db.get(str(pid)) or {}).get("position") or "?"


def _elig(players_db, pid):
    return set(player_eligible_positions(players_db.get(str(pid)) or {}))


def decomp(row):
    return {k: row.get(k) for k in DECOMP}


def implied_replacement(board):
    out = {}
    for r in board:
        if r.get("bpa") is not None and r.get("projected_points") is not None and r["position"] not in out:
            out[r["position"]] = round(r["projected_points"] - r["bpa"], 2)
    return out


def build_board(merger, players_db, picks, seat, league, season, arm):
    kw = dict(my_roster_id=seat, league=league, mode="balanced",
              sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    if arm == "NOFEAS":
        with mock.patch.object(dr, "feasibility_first",
                               lambda scored, *a, **k: pd.Series(1, index=scored.index, dtype=int)):
            return dr.compute_draft_board(merger, players_db, picks, **kw)
    if arm == "NEEDCAP":
        with mock.patch.object(dr, "NEED_BONUS_MAX", 1e9):
            return dr.compute_draft_board(merger, players_db, picks, **kw)
    return dr.compute_draft_board(merger, players_db, picks, **kw)


def phantom_slots(slots, repl):
    """One phantom per STARTING slot, valued at that slot's replacement level (max over the
    replacement levels of the positions the slot accepts). A slot whose positions carry no
    replacement level gets no phantom, and that is recorded by the caller."""
    out, missing = [], []
    for i, s in enumerate(slots):
        vals = [(repl[p], p) for p in s["eligible"] if p in repl]
        if not vals:
            missing.append(s["slot_id"])
            continue
        # ELIGIBLE ONLY AT THE POSITION WHOSE LEVEL IT CARRIES. A FLEX phantom valued at the WR
        # level and eligible at {RB,WR,TE} could fill the dedicated TE slot at a WR's value, and
        # a candidate's marginal then counted a phantom shuffle (measured: 130.05 for a 99.44 VOR).
        value, position = max(vals)
        out.append({"id": f"__phantom_{i}", "value": float(value), "eligible": {position}})
    return out, missing


def mlv_scores(board, base_players, slots, players_db):
    """{player_id: lineup(base + X) - lineup(base)} in projected points, for every priced row."""
    without = lo.optimize_lineup(base_players, slots)["total_value"]
    scores = {}
    for r in board:
        if r.get("projected_points") is None or r.get("universal_value") is None:
            continue
        pid = str(r["player_id"])
        cand = {"id": pid, "value": float(r["projected_points"]), "eligible": _elig(players_db, pid)}
        scores[pid] = round(lo.optimize_lineup(base_players + [cand], slots)["total_value"] - without, 2)
    return scores


def alt_ranked(board, mlv, combine="lex"):
    """Rows ranked by the marginal lineup value. "lex": starter value first, universal_value
    (the asset ruler) orders everything the lineup cannot use. "add": mlv + universal_value.
    Neither introduces a constant. The horizon/risk terms are NOT added on top of a zero
    marginal: measured, that let a +10 horizon clamp on a 30-point rookie outrank every real
    player once the starters were full."""
    rows = []
    for r in board:
        pid = str(r["player_id"])
        if pid not in mlv:
            continue
        uv = r["universal_value"]
        if combine == "add":
            key = (not r.get("fills_required_slot", False), -(mlv[pid] + uv), -uv, pid)
        else:
            key = (not r.get("fills_required_slot", False), -mlv[pid], -uv, pid)
        rows.append((key, r, mlv[pid] + (uv if combine == "add" else 0.0)))
    rows.sort(key=lambda t: t[0])
    return [(t[1], t[2]) for t in rows]


def my_roster_players(mine, points, players_db):
    return [{"id": pid, "value": float(points[pid]), "eligible": _elig(players_db, pid)} for pid in mine]


def lineup_points(mine, points, players_db, slots):
    return lo.optimize_lineup(my_roster_players(mine, points, players_db), slots)["total_value"]


def draft_one(arm, merger, players_db, league, pick_order, seat, points, season, rounds, slots, log):
    roster_positions = league["roster_positions"]
    num_teams = len(set(str(r) for r in pick_order))
    picks, taken, mine = [], set(), {}
    seq, states = [], []
    last_repl = {}
    for idx in range(min(len(pick_order), rounds * num_teams)):
        who = str(pick_order[idx])
        rnd = idx // num_teams + 1
        free = [p for p in points if p not in taken]
        if not free:
            break
        if who != seat:
            chosen = rp.control_pick(free, points, mine.get(who, []), players_db, slots)
        else:
            t0 = time.time()
            board = build_board(merger, players_db, picks, seat, league, season, arm)
            live = [r for r in board if str(r["player_id"]) in points and str(r["player_id"]) not in taken]
            repl = implied_replacement(live) or last_repl
            # a position with no live priced row keeps its last known level for the phantom
            for p, v in last_repl.items():
                repl.setdefault(p, v)
            last_repl = dict(repl)
            my_players = my_roster_players(mine.get(seat, []), points, players_db)
            ph, ph_missing = phantom_slots(slots, repl)
            rf = mlv_scores(live, my_players + ph, slots, players_db)
            raw = mlv_scores(live, my_players, slots, players_db)
            rf_rank = alt_ranked(live, rf, "add" if arm == "RFMLV_ADD" else "lex")
            raw_rank = alt_ranked(live, raw, "lex")
            board_rank = sorted(live, key=ps._board_order)
            if arm.startswith("RFMLV"):
                chosen = str(rf_rank[0][0]["player_id"])
            elif arm.startswith("RAWMLV"):
                chosen = str(raw_rank[0][0]["player_id"])
            else:
                chosen = str(board_rank[0]["player_id"])
            chosen_row = next(r for r in live if str(r["player_id"]) == chosen)
            priced = [r for r in live if r.get("universal_value") is not None]
            best_by_pos = {}
            for r in board_rank:
                if r.get("universal_value") is not None and r["position"] not in best_by_pos:
                    best_by_pos[r["position"]] = decomp(r)
            need_vals = [r["need_bonus"] for r in priced if r.get("need_bonus") is not None]
            depth_vals = [r["depth_exposure"] for r in priced if r.get("depth_exposure") is not None]
            top10_ids = [str(r["player_id"]) for r in board_rank[:10]]
            rf_pos = {str(r["player_id"]): i for i, (r, _) in enumerate(rf_rank)}
            demand = dr.remaining_starter_demand(roster_positions, num_teams, picks, players_db)
            drafted = dr.drafted_counts_by_position(picks, players_db)
            states.append({
                "round": rnd, "index": idx, "seconds": round(time.time() - t0, 2),
                "chosen": decomp(chosen_row),
                "rf_mlv_of_chosen": rf.get(chosen), "raw_mlv_of_chosen": raw.get(chosen),
                "implied_replacement": repl, "phantom_slots_missing": ph_missing,
                "remaining_starter_demand": {k: round(v, 3) for k, v in demand.items() if v},
                "drafted_league_wide": drafted,
                "my_counts": dict(collections.Counter(_pos(players_db, p) for p in mine.get(seat, []))),
                "best_by_position": best_by_pos,
                "top8": [(r["name"], r["position"], r["final_score"]) for r in board_rank[:8]],
                "need_bonus_max_on_board": max(need_vals) if need_vals else None,
                "rows_at_need_cap": sum(1 for v in need_vals if v >= dr.NEED_BONUS_MAX - 1e-9),
                "depth_exposure_positive_rows": sum(1 for v in depth_vals if v > 0),
                "depth_exposure_max": max(depth_vals) if depth_vals else None,
                "priced_rows": len(priced),
                "rf_top": (rf_rank[0][0]["name"], rf_rank[0][0]["position"], rf_rank[0][1]) if rf_rank else None,
                "raw_top": (raw_rank[0][0]["name"], raw_rank[0][0]["position"], raw_rank[0][1]) if raw_rank else None,
                "rf_top_equals_board_top": bool(rf_rank and str(rf_rank[0][0]["player_id"]) == str(board_rank[0]["player_id"])),
                "rf_rank_of_board_top": rf_pos.get(str(board_rank[0]["player_id"])),
                "board_top10_moved_under_rf": sum(1 for i, pid in enumerate(top10_ids) if rf_pos.get(pid) != i),
                "rf_top10": [(r["name"], r["position"], s) for r, s in rf_rank[:10]],
            })
            seq.append({"round": rnd, "player": _name(players_db, chosen), "position": _pos(players_db, chosen),
                        "projected_points": round(points[chosen], 1),
                        "fills_required_slot": bool(chosen_row.get("fills_required_slot"))})
            log(f"    {arm:8s} seat {seat:>2s} r{rnd:02d} {_pos(players_db, chosen):3s} {_name(players_db, chosen):24s} "
                f"{points[chosen]:6.1f} fs={chosen_row.get('final_score')} req={chosen_row.get('fills_required_slot')} "
                f"({time.time() - t0:.1f}s)")
        taken.add(str(chosen))
        mine.setdefault(who, []).append(str(chosen))
        picks.append({"pick_no": idx + 1, "round": rnd, "roster_id": who, "player_id": str(chosen)})
    order = [str(s) for s in pick_order[:num_teams]]
    control_seat = order[(order.index(str(seat)) + 1) % len(order)]   # as run_roster_shape_probe
    out = {
        "arm": arm, "seat": seat, "sequence": seq, "states": states,
        "composition": dict(collections.Counter(r["position"] for r in seq)),
        "lineup_points": lineup_points(mine.get(seat, []), points, players_db, slots),
        "roster_points": round(sum(points[p] for p in mine.get(seat, [])), 1),
        "control_seat": control_seat,
        "control_composition": dict(collections.Counter(_pos(players_db, p) for p in mine.get(control_seat, []))),
        "control_lineup_points": lineup_points(mine.get(control_seat, []), points, players_db, slots),
        "all_seats_lineup_points": {s: lineup_points(ids, points, players_db, slots) for s, ids in mine.items()},
    }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--seats", default=",".join(SEATS))
    args = ap.parse_args(argv)
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.format}.json"
    log_path = out_dir / f"{args.format}.log"

    def log(msg):
        print(msg, flush=True)
        with log_path.open("a") as fh:
            fh.write(msg + "\n")

    commit = resume_join.head_commit()
    scoring = rdb.scoring_settings_from_capture()
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    spec = next(s for s in rp.PROOF_FORMATS if s["label"] == args.format)
    league = dr.build_mock_league(teams=spec["teams"], superflex=spec["superflex"], scoring=spec["scoring"],
                                  te_premium=spec["te_premium"], dynasty=True, base_scoring=scoring)
    merger.set_league_format(db.league_format_hint(league))          # NEVER SKIP
    points = rp.scoreable_pool(merger, players_db, league, season)
    seats = [str(i) for i in range(1, spec["teams"] + 1)]
    rounds = len(league["roster_positions"])
    slots = lo.slots_from_roster_positions(league["roster_positions"])
    pick_order = ds.generate_pick_order(seats, rounds, "snake")
    recorded = json.loads(RECORDED.read_text()) if RECORDED.exists() else None
    rec_seq = {}
    if recorded:
        for fmt in recorded["formats"]:
            if fmt["label"] == args.format:
                for s in fmt["per_seat"]:
                    rec_seq[s["seat"]] = [r["player"] for r in s["engine_picks"]]
    log(f"commit {commit} | {args.format} | pool {len(points)} "
        f"{dict(collections.Counter(_pos(players_db, p) for p in points))} | rounds {rounds}")
    results = {"commit": commit, "format": args.format, "roster_positions": league["roster_positions"],
               "pool_size": len(points), "universe": universe, "drafts": []}
    started = time.time()
    for seat in args.seats.split(","):
        for arm in args.arms.split(","):
            t0 = time.time()
            d = draft_one(arm, merger, players_db, league, pick_order, seat, points, season, rounds, slots, log)
            if arm == "CURRENT" and seat in rec_seq:
                mine = [r["player"] for r in d["sequence"]]
                d["replay_matches_recorded"] = mine == rec_seq[seat]
                d["first_mismatch"] = next(((i + 1, a, b) for i, (a, b) in enumerate(zip(mine, rec_seq[seat])) if a != b), None)
            d["seconds"] = round(time.time() - t0, 1)
            results["drafts"].append(d)
            results["seconds_total"] = round(time.time() - started, 1)
            out_path.write_text(json.dumps(results, indent=1, default=str))
            log(f"  == {arm} seat {seat}: engine {d['composition']} lineup {d['lineup_points']} | "
                f"control {d['control_composition']} lineup {d['control_lineup_points']}"
                + (f" | replay_matches_recorded={d.get('replay_matches_recorded')} {d.get('first_mismatch')}" if arm == "CURRENT" else "")
                + f" ({d['seconds']}s)")
    log(f"-> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
