"""What is the quarterback worth to this engine while his slot is the last one open? (#216 defect b)

Defect (a) -- the positional bias that made the board hoard tight ends -- has been traced,
measured, and (as `displacement_adj`) repaired. Defect (b) has been named in every report on this
item and MEASURED BY NONE OF THEM: `bpa` for the best remaining quarterback is exactly 0.00 for
rounds on end, so the board cannot value him at all and only `need_bonus` eventually picks him up.

This instrument records, at every one of the engine seat's turns, the whole chain that produces
that zero, so the number can be read against its cause instead of asserted:

    remaining_starter_demand["QB"]  ->  the rank _remaining_demand_rank returns
                                    ->  the replacement LEVEL that rank selects
                                    ->  bpa = projected_points - level, for the best QB left

together with every term that could price him instead -- `need_bonus`, `waiting_cost` (his
projection over the end-of-draft free alternative, #48 observable-only), `horizon_floor`, and
`final_score` -- and what the engine actually took at that turn.

ONE DRAFT PER FORMAT, engine seat vs `run_roster_proof`'s control, the board exactly as shipped.
Nothing is toggled and nothing is patched: this is a description of the engine, not an ablation.

    PYTHONPATH=. python3 run_216_qb_price_probe.py --out <dir>
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
import run_216_bench_probe as bench
import run_draft_battery as rdb
import run_roster_proof as rp

FORMATS = ("12T_ppr", "12T_ppr_SF", bench.OWNER_LEAGUE["label"])


def qb_chain(board, picks, players_db, league, points):
    """The demand -> rank -> level -> bpa chain for QB, read at this exact board state."""
    roster_positions = league["roster_positions"]
    num_teams = league["total_rosters"]
    demand = dr.remaining_starter_demand(roster_positions, num_teams, picks, players_db)
    rank = dr._remaining_demand_rank("QB", demand)
    qbs = [r for r in board if r["position"] == "QB" and str(r["player_id"]) in points]
    qbs.sort(key=lambda r: -(r.get("projected_points") or 0.0))
    best = qbs[0] if qbs else None
    return {
        "qb_demand": round(demand.get("QB", 0.0), 4),
        # THE DEMAND RANK ONLY. In superflex, QB's replacement rank comes from
        # `startable_floors` (the projection cliff, see qb_startable_floor) and NOT from this
        # number, so labelling it "the rank" would be a claim the engine does not make. The
        # first version of this probe printed "the rank-th best remaining QB" as the replacement
        # level and was WRONG for every superflex row; caught before publishing.
        "qb_demand_rank": rank,
        "qbs_available": len(qbs),
        # The level ACTUALLY subtracted, recovered from the row itself: bpa = projection - level,
        # so level = projection - bpa. True on both branches, demand-rank and startable-floor
        # alike, because it is read from the answer rather than from a model of the answer.
        "qb_level_used": (None if not qbs or qbs[0].get("bpa") is None
                          else round(qbs[0]["projected_points"] - qbs[0]["bpa"], 1)),
        "qb_at_demand_rank_projection": (round(qbs[rank - 1]["projected_points"], 1)
                                         if rank and len(qbs) >= rank else None),
        "best_qb": None if best is None else {
            k: best.get(k) for k in
            ("name", "projected_points", "bpa", "universal_value", "need_bonus",
             "displacement_adj", "final_score", "waiting_cost", "horizon_floor",
             "fills_required_slot", "replacement_basis")},
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--formats", default=",".join(FORMATS))
    ap.add_argument("--seat", default="1")
    args = ap.parse_args(argv)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    scoring = rdb.scoring_settings_from_capture()
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    report = {"commit": resume_join.head_commit(), "universe": universe, "formats": []}
    lines = ["# What the quarterback is worth while his slot is the last one open", ""]
    for label in args.formats.split(","):
        league, draft_type = bench.build_league(label, scoring)
        merger.set_league_format(db.league_format_hint(league))          # NEVER SKIP
        points = rp.scoreable_pool(merger, players_db, league, season)
        roster_positions = league["roster_positions"]
        num_teams = league["total_rosters"]
        rounds = len(roster_positions)
        slots = lo.slots_from_roster_positions(roster_positions)
        seats = [str(i) for i in range(1, num_teams + 1)]
        pick_order = ds.generate_pick_order(seats, rounds, draft_type)
        seat = args.seat
        picks, taken, mine = [], set(), collections.defaultdict(list)
        states = []
        t0 = time.time()
        for idx in range(min(len(pick_order), rounds * num_teams)):
            who = str(pick_order[idx])
            free = [p for p in points if p not in taken]
            if not free:
                break
            if who != seat:
                chosen = rp.control_pick(free, points, mine[who], players_db, slots)
            else:
                board = dr.compute_draft_board(
                    merger, players_db, picks, seat, league, mode="balanced",
                    sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
                live = [r for r in board if str(r["player_id"]) in points
                        and str(r["player_id"]) not in taken]
                chosen_row = sorted(live, key=ps._board_order)[0]
                chosen = str(chosen_row["player_id"])
                chain = qb_chain(live, picks, players_db, league, points)
                states.append({
                    "round": idx // num_teams + 1,
                    "my_qbs": sum(1 for p in mine[seat]
                                  if (players_db.get(p) or {}).get("position") == "QB"),
                    **chain,
                    "chosen": {"name": chosen_row.get("name"), "position": chosen_row["position"],
                               "final_score": chosen_row.get("final_score"),
                               "fills_required_slot": bool(chosen_row.get("fills_required_slot"))},
                })
            taken.add(str(chosen))
            mine[who].append(str(chosen))
            picks.append({"pick_no": idx + 1, "round": idx // num_teams + 1,
                          "roster_id": who, "player_id": str(chosen)})
        block = {"format": label, "seat": seat, "roster_positions": roster_positions,
                 "seconds": round(time.time() - t0, 1), "states": states}
        report["formats"].append(block)
        lines.append(f"## {label} — seat {seat}")
        lines.append("")
        lines.append("| rnd | my QB | QB demand | demand rank | LEVEL USED | best QB | proj | "
                     "bpa | need | waiting_cost | final | chosen |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for s in states:
            b = s["best_qb"] or {}
            def n(v, f="{:.2f}"):
                return "—" if v is None else f.format(v)
            lines.append(
                f"| {s['round']} | {s['my_qbs']} | {s['qb_demand']:g} | {s['qb_demand_rank']} | "
                f"{n(s['qb_level_used'], '{:.1f}')} | {b.get('name') or '—'} | "
                f"{n(b.get('projected_points'), '{:.1f}')} | {n(b.get('bpa'))} | "
                f"{n(b.get('need_bonus'))} | {n(b.get('waiting_cost'))} | "
                f"{n(b.get('final_score'))} | {s['chosen']['position']} "
                f"{s['chosen']['name']} ({n(s['chosen']['final_score'])}) |")
        lines.append("")
    (out / "qb_price.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    (out / "TABLES_qb_price.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
