"""What SHAPE of roster does each arm actually build? (#216)

WHY THIS EXISTS. #205 reported that the engine fills every starting slot in every seat of every
format, and read that as "the points deficit is not a lineup artifact". FILLING A SLOT AND
FILLING IT WELL ARE DIFFERENT QUESTIONS, and #205 only asked the first. This asks the second, by
recording the POSITIONAL COMPOSITION of what each arm drafts.

It exists because an aggregate cannot show a degenerate roster. A seat that ends with eight
tight ends and two wide receivers reports 8/8 starting slots filled, exactly like a sane one.

THE CONFOUND IT KILLS FIRST. A positional stack proves nothing if the shared pool is thin at the
positions not taken -- the arm cannot draft receivers that are not there. So the pool's own
composition and its per-position projection depth are reported ALONGSIDE the rosters, in the
same document, rather than left for a reader to assume.

THE SECOND CONFOUND. The engine's pick here is the top row of `build_snapshot`'s candidate list.
That is only the engine's real recommendation if it matches the production board's own first
row, so both are computed at one mid-draft state per seat and recorded together. If they ever
disagree, this instrument is reading something other than the engine and its output is void.

Run from the repo root (rule 1).
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
import pick_synthesis
import resume_join
import run_draft_battery as rdb
import run_roster_proof as rp

PROBE_FORMATS = ("12T_ppr", "12T_ppr_SF")
#: An early, a middle and a late seat -- a single seat cannot separate "the engine does this"
#: from "this draft slot does this".
SEAT_PICKER = (0, 0.5, 1.0)
#: The round at which the snapshot's choice is cross-checked against the production board.
AGREEMENT_ROUND = 5


def _name(players_db, pid) -> str:
    info = players_db.get(str(pid)) or {}
    return " ".join(x for x in (info.get("first_name"), info.get("last_name")) if x) or str(pid)


def _pos(players_db, pid) -> str:
    return (players_db.get(str(pid)) or {}).get("position") or "?"


def pool_shape(points, players_db) -> dict:
    """The pool's own composition and depth. Reported so a stack cannot be read as a stack when
    it is really scarcity."""
    counts = collections.Counter(_pos(players_db, p) for p in points)
    depth = {}
    for pos in sorted(counts):
        ranked = sorted((p for p in points if _pos(players_db, p) == pos),
                        key=lambda p: -points[p])
        depth[pos] = {"in_pool": len(ranked),
                      **{f"rank_{k}_points": round(points[ranked[k - 1]], 1)
                         for k in (1, 12, 24, 36) if len(ranked) >= k}}
    return {"counts": dict(counts), "depth": depth}


def draft_one(merger, players_db, league, pick_order, seat, points, season, rounds, slots):
    """One draft with the engine at `seat`. Returns (engine picks, control picks, agreement)."""
    picks, taken, mine = [], set(), {}
    engine_seq, control_seq, agreement = [], [], None
    num_teams = len(set(str(r) for r in pick_order))

    for idx in range(min(len(pick_order), rounds * num_teams)):
        who = str(pick_order[idx])
        rnd = idx // num_teams + 1
        free = [p for p in points if p not in taken]
        if not free:
            break
        if who == seat:
            snap = pick_synthesis.build_snapshot(
                merger, players_db, picks, pick_order, idx, who, league,
                pick_label=f"{rnd}.{(idx % num_teams) + 1:02d}",
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
            chosen = next((c.player_id for c in snap.candidates
                           if str(c.player_id) in points and str(c.player_id) not in taken), None)
            if chosen is None:
                break
            best = min(free, key=lambda p: (-points[p], p))
            engine_seq.append({
                "round": rnd, "player": _name(players_db, chosen), "position": _pos(players_db, chosen),
                "projected_points": round(points[str(chosen)], 1),
                "best_available": _name(players_db, best),
                "best_available_position": _pos(players_db, best),
                "best_available_points": round(points[best], 1),
            })
            if rnd == AGREEMENT_ROUND:
                board = dr.compute_draft_board(
                    merger, players_db, picks, seat, league,
                    sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
                rows = board[0] if isinstance(board, tuple) else board
                first = (list(rows)[0] or {}) if len(list(rows)) else {}
                board_top = str(first.get("player_id")) if isinstance(first, dict) else None
                agreement = {
                    "round": rnd,
                    "snapshot_top": _name(players_db, chosen),
                    "board_top": _name(players_db, board_top) if board_top else None,
                    # THE GATE. If these disagree, this instrument is not reading the engine.
                    "agree": board_top is not None and str(board_top) == str(chosen),
                }
        else:
            chosen = rp.control_pick(free, points, mine.get(who, []), players_db, slots)
            if chosen is None:
                break
            if who == control_seat_for(seat, pick_order):
                control_seq.append({
                    "round": rnd, "player": _name(players_db, chosen),
                    "position": _pos(players_db, chosen),
                    "projected_points": round(points[str(chosen)], 1),
                })
        taken.add(str(chosen))
        mine.setdefault(who, []).append(str(chosen))
        picks.append({"pick_no": idx + 1, "round": rnd, "roster_id": who,
                      "player_id": str(chosen)})
    return engine_seq, control_seq, agreement


def control_seat_for(seat, pick_order) -> str:
    """The seat immediately after the engine's, so the two populations are the same size."""
    order = [str(s) for s in pick_order[:len(set(str(r) for r in pick_order))]]
    return order[(order.index(str(seat)) + 1) % len(order)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default="ROSTER_SHAPE.json")
    args = ap.parse_args(argv)

    commit = resume_join.head_commit()
    scoring = rdb.scoring_settings_from_capture()
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    print(f"commit {commit} | universe {universe['players_in_pool']} players", flush=True)

    results, started = [], time.time()
    for spec in [s for s in rp.PROOF_FORMATS if s["label"] in PROBE_FORMATS]:
        league = dr.build_mock_league(teams=spec["teams"], superflex=spec["superflex"],
                                      scoring=spec["scoring"], te_premium=spec["te_premium"],
                                      dynasty=True, base_scoring=scoring)
        merger.set_league_format(db.league_format_hint(league))          # rule 4
        points = rp.scoreable_pool(merger, players_db, league, season)   # rule 2
        seats = [str(i) for i in range(1, spec["teams"] + 1)]
        rounds = len(league.get("roster_positions") or [])
        slots = lo.slots_from_roster_positions(league.get("roster_positions") or [])
        pick_order = ds.generate_pick_order(seats, rounds, "snake")

        shape = pool_shape(points, players_db)
        print(f"\n{spec['label']}  starts {league.get('roster_positions')}")
        print(f"  POOL {shape['counts']}")

        per_seat = []
        for frac in SEAT_PICKER:
            seat = seats[min(int(frac * (len(seats) - 1)), len(seats) - 1)]
            eng, ctl, agree = draft_one(merger, players_db, league, pick_order, seat,
                                        points, season, rounds, slots)
            ec = collections.Counter(r["position"] for r in eng)
            cc = collections.Counter(r["position"] for r in ctl)
            per_seat.append({"seat": seat, "engine_picks": eng, "control_picks": ctl,
                             "engine_composition": dict(ec), "control_composition": dict(cc),
                             "board_agreement": agree})
            flag = "" if (agree or {}).get("agree") else "   <-- SNAPSHOT/BOARD DISAGREE, VOID"
            print(f"  seat {seat:>3s}  engine {dict(ec)}"
                  f"   control {dict(cc)}{flag}", flush=True)

        results.append({resume_join.PRODUCED_AT: commit, resume_join.CARRIED: False,
                        "label": spec["label"],
                        "roster_positions": league.get("roster_positions"),
                        "pool": shape, "per_seat": per_seat})
        Path(args.out).write_text(json.dumps({
            "commit": commit,
            "commits_present": resume_join.commits_present(results),
            "universe": universe,
            "question": "the POSITIONAL COMPOSITION each arm drafts, with the pool's own "
                        "composition alongside it so a stack cannot be misread as scarcity",
            "seconds_this_process": round(time.time() - started, 1),
            "formats": results,
        }, indent=2, default=str), encoding="utf-8")

    print(f"\n-> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
