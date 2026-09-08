"""#216 second pass -- the bench regime. Run FROM THE REPO ROOT:

    PYTHONPATH=. python3 run_216_bench_probe.py --out /abs/dir

Four arms, one process, one code version, the displacement term ON and feasibility_first as
shipped in all of them. They differ in ONE thing: what the engine seat picks when the board is
PURE-BENCH -- no priced row can crack my lineup, i.e. max(bpa + displacement_adj) <= 0 over
priced rows (exact, read off the rows). In a MIXED state every arm takes the board's own first
row after pick_synthesis._board_order.

  B0  the board as shipped (distance to my lineup)
  B1  coverage: the number of my fielded starters whose absence opens a slot the candidate
      can fill (optimizer, one starter out, re-optimised), then projected points
  B2  horizon: projected_points - horizon_floor (the row's own waiting_cost), the pool's
      end-of-draft free alternative -- CROSSES #48's observable-only ruling if adopted
  B3  coverage share x horizon margin

At the end of every draft: every roster's optimal lineup on the season projections, the
league's fielded load per position, the derived per-seat band (roster_size x share_p, minus
the seat's own fielded load for the bench), and the seat's shape against the owner's ordering
on the full roster and on the bench. Written after every draft.
"""
from __future__ import annotations

import argparse
import collections
import json
import time
from pathlib import Path

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

from run_216_fix_probe import _name, _pos, _decomp, _levels, asset_and_character

ARMS = ("B0", "B1", "B2", "B3")


def _entries(ids, points, players_db):
    return [{"id": pid, "value": float(points[pid]), "eligible": set(player_eligible_positions(players_db.get(pid) or {}))}
            for pid in ids if pid in points]


def coverage(my_ids, cand_id, cand_points, cand_elig, points, players_db, slots):
    """How many of my fielded starters this candidate could stand in for (one out, re-solved),
    and the mean gain across those scenarios, in projected points."""
    roster = _entries(my_ids, points, players_db)
    base = lo.optimize_lineup(roster, slots)
    starters = [a["player_id"] for a in base["assignments"]]
    cand = {"id": cand_id, "value": float(cand_points), "eligible": set(cand_elig)}
    covered, gains = 0, []
    for s in starters:
        without = [p for p in roster if p["id"] != s]
        before = lo.optimize_lineup(without, slots)["total_value"]
        after = lo.optimize_lineup(without + [cand], slots)["total_value"]
        gain = round(after - before, 2)
        if gain > 0:
            covered += 1
            gains.append(gain)
    return covered, len(starters), (sum(gains) / len(gains) if gains else 0.0)


def pure_bench(priced):
    return bool(priced) and max((r["bpa"] or 0.0) + (r.get("displacement_adj") or 0.0) for r in priced) <= 0.0


def choose(arm, live, priced, my_ids, points, players_db, slots):
    """The arm's pick in a pure-bench state; returns (row, note)."""
    scored = []
    for r in priced:
        pid = str(r["player_id"])
        key = None
        if arm == "B1":
            cov, n, _ = coverage(my_ids, pid, r["projected_points"], player_eligible_positions(players_db.get(pid) or {}), points, players_db, slots)
            key = (-cov, -r["projected_points"], pid)
            note = f"cov {cov}/{n}"
        elif arm == "B2":
            wc = r.get("waiting_cost")
            key = (0 if wc is not None else 1, -(wc if wc is not None else 0.0), -r["projected_points"], pid)
            note = f"wc {wc}"
        elif arm == "B3":
            cov, n, _ = coverage(my_ids, pid, r["projected_points"], player_eligible_positions(players_db.get(pid) or {}), points, players_db, slots)
            wc = r.get("waiting_cost")
            score = (cov / n if n else 0.0) * (wc if wc is not None else 0.0)
            key = (0 if wc is not None else 1, -score, -r["projected_points"], pid)
            note = f"cov {cov}/{n} wc {wc} score {score:.1f}"
        scored.append((key, r, note))
    scored.sort(key=lambda t: t[0])
    return scored[0][1], scored[0][2]


def fielded_load(ids, points, players_db, slots):
    solved = lo.optimize_lineup(_entries(ids, points, players_db), slots)
    load = collections.Counter()
    by_id = {p: (players_db.get(p) or {}).get("position") for p in ids}
    for a in solved["assignments"]:
        load[by_id[a["player_id"]]] += 1
    return dict(load), len(solved["assignments"])


def derived_band(mine, seat, points, players_db, slots, roster_size):
    """The owner's band, derived: league fielded-load share x roster size, minus my own load."""
    league_load, total = collections.Counter(), 0
    for s, ids in mine.items():
        load, n = fielded_load(ids, points, players_db, slots)
        league_load.update(load)
        total += n
    share = {p: league_load[p] / total for p in league_load} if total else {}
    my_load, _ = fielded_load(mine[seat], points, players_db, slots)
    target_total = {p: round(roster_size * share.get(p, 0.0), 2) for p in share}
    bench_slots = roster_size - sum(my_load.values())
    bench_target = {p: round(max(target_total.get(p, 0.0) - my_load.get(p, 0), 0.0), 2) for p in share}
    return {"league_fielded_load": dict(league_load), "league_fielded_total": total, "share": {p: round(v, 4) for p, v in share.items()},
            "my_fielded_load": my_load, "bench_slots": bench_slots, "target_total": target_total, "bench_target": bench_target,
            "derived_ordering": sorted(share, key=lambda p: -share[p])}


def ordering_verdict(comp):
    wr, rb, te, qb = comp.get("WR", 0), comp.get("RB", 0), comp.get("TE", 0), comp.get("QB", 0)
    return {"WR>=RB": wr >= rb, "RB>TE": rb > te, "RB>=TE": rb >= te, "QB<=4": qb <= 4,
            "pass_strict": wr >= rb and rb > te and qb <= 4, "pass_tendency": wr >= rb and rb >= te and qb <= 4}


def draft_one(arm, merger, players_db, league, pick_order, seat, points, season, rounds, slots, log, rulers, horizon_map):
    roster_positions = league["roster_positions"]
    num_teams = len(set(str(r) for r in pick_order))
    picks, taken, mine = [], set(), collections.defaultdict(list)
    seq, states = [], []
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
            board = dr.compute_draft_board(merger, players_db, picks, seat, league, mode="balanced",
                                           sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
            live = [r for r in board if str(r["player_id"]) in points and str(r["player_id"]) not in taken]
            ordered = sorted(live, key=ps._board_order)
            priced = [r for r in ordered if r.get("final_score") is not None]
            bench = pure_bench(priced)
            note = ""
            if bench and arm != "B0":
                chosen_row, note = choose(arm, live, priced, mine[seat], points, players_db, slots)
            else:
                chosen_row = ordered[0]
            chosen = str(chosen_row["player_id"])
            floors = {}
            for r in priced:
                if r["position"] not in floors and r.get("horizon_floor") is not None:
                    floors[r["position"]] = r["horizon_floor"]
            states.append({"round": rnd, "pure_bench": bench, "chosen": _decomp(chosen_row), "note": note,
                           "board_top": _decomp(ordered[0]), "horizon_floors": floors,
                           "waiting_cost_of_chosen": chosen_row.get("waiting_cost"),
                           "my_counts_before": dict(collections.Counter(_pos(players_db, p) for p in mine[seat]))})
            seq.append({"round": rnd, "player": _name(players_db, chosen), "position": _pos(players_db, chosen),
                        "projected_points": round(points[chosen], 1), "fills_required_slot": bool(chosen_row.get("fills_required_slot"))})
            log(f"    {arm} seat {seat:>2s} r{rnd:02d} {'BENCH' if bench else 'mixed'} {_pos(players_db, chosen):3s} {_name(players_db, chosen):22s} "
                f"{points[chosen]:6.1f} fs={chosen_row.get('final_score')} wc={chosen_row.get('waiting_cost')} {note} ({time.time() - t0:.1f}s)")
        taken.add(str(chosen))
        mine[who].append(str(chosen))
        picks.append({"pick_no": idx + 1, "round": rnd, "roster_id": who, "player_id": str(chosen)})
    order = [str(s) for s in pick_order[:num_teams]]
    control_seat = order[(order.index(str(seat)) + 1) % len(order)]
    composition = dict(collections.Counter(r["position"] for r in seq))
    n_start = sum(1 for s in roster_positions if s != "BN")
    bench_comp = dict(collections.Counter(r["position"] for r in seq[n_start:]))
    band = derived_band(mine, seat, points, players_db, slots, rounds)
    dedicated = dr.dedicated_slot_counts(roster_positions)
    return {
        "arm": arm, "seat": seat, "sequence": seq, "states": states, "composition": composition,
        "bench_composition_by_pick_order": bench_comp,
        "verdict_full_roster": ordering_verdict(composition), "verdict_bench": ordering_verdict(bench_comp),
        "band": band,
        "missing_dedicated": {p: dedicated[p] - composition.get(p, 0) for p in dedicated if dedicated[p] > composition.get(p, 0)},
        "unfillable_starting_slots": sorted(rp.unmet_slot_positions(mine[seat], players_db, slots)),
        "forced": sum(1 for s in seq if s["fills_required_slot"]),
        "pure_bench_states": sum(1 for s in states if s["pure_bench"]),
        "lineup_points": lo.optimize_lineup(_entries(mine[seat], points, players_db), slots)["total_value"],
        "control_lineup_points": lo.optimize_lineup(_entries(mine[control_seat], points, players_db), slots)["total_value"],
        "g9_engine": asset_and_character(picks, seat, players_db, rulers, slots, horizon_map),
        "g9_control": asset_and_character(picks, control_seat, players_db, rulers, slots, horizon_map),
        "qb_rounds": [s["round"] for s in seq if s["position"] == "QB"],
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
    for fmt_label in args.formats.split(","):
        spec = next(s for s in rp.PROOF_FORMATS if s["label"] == fmt_label)
        league = dr.build_mock_league(teams=spec["teams"], superflex=spec["superflex"], scoring=spec["scoring"],
                                      te_premium=spec["te_premium"], dynasty=True, base_scoring=scoring)
        merger.set_league_format(db.league_format_hint(league))
        points = rp.scoreable_pool(merger, players_db, league, season)
        values = db.reference_values(merger, players_db, league, sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        rulers = {"cdme": values, "points": points}
        predraft = dr.compute_draft_board(merger, players_db, [], None, league, mode="balanced",
                                          sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        horizon_map = {str(r["player_id"]): r.get("time_horizon_adj") for r in predraft}
        seats = [str(i) for i in range(1, spec["teams"] + 1)]
        rounds = len(league["roster_positions"])
        slots = lo.slots_from_roster_positions(league["roster_positions"])
        pick_order = ds.generate_pick_order(seats, rounds, "snake")
        out_path = out_dir / f"{fmt_label}.json"
        log(f"commit {commit} | {fmt_label} | pool {len(points)} | rounds {rounds}")
        results = {"commit": commit, "format": fmt_label, "roster_positions": league["roster_positions"], "drafts": []}
        for seat in args.seats.split(","):
            for arm in args.arms.split(","):
                t0 = time.time()
                d = draft_one(arm, merger, players_db, league, pick_order, seat, points, season, rounds, slots, log, rulers, horizon_map)
                d["seconds"] = round(time.time() - t0, 1)
                results["drafts"].append(d)
                out_path.write_text(json.dumps(results, indent=1, default=str))
                log(f"  == {arm} seat {seat}: {d['composition']} bench {d['bench_composition_by_pick_order']} full {d['verdict_full_roster']['pass_strict']}/{d['verdict_full_roster']['pass_tendency']} "
                    f"lineup {d['lineup_points']} forced {d['forced']} bench_states {d['pure_bench_states']} band_total {d['band']['target_total']} "
                    f"my_load {d['band']['my_fielded_load']} cdme {d['g9_engine']['cdme_total_value']} vs {d['g9_control']['cdme_total_value']} ({d['seconds']}s)")
        log(f"-> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
