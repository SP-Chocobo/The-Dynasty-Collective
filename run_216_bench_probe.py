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
from unittest import mock

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


def pure_bench(priced, my_ids, points, players_db, slots):
    """No priced row would START today: the raw optimizer (no phantoms), so a candidate who
    fills an EMPTY slot is starter-capable even when the league anchor prices him at 0.00 (the
    QB collapse -- the first version of this detector used bpa + displacement_adj <= 0 and
    classified the open-QB state as bench, which pushed the QB out of round 8)."""
    roster = _entries(my_ids, points, players_db)
    base = lo.optimize_lineup(roster, slots)["total_value"]
    for r in priced:
        pid = str(r["player_id"])
        cand = {"id": pid, "value": float(r["projected_points"]), "eligible": set(player_eligible_positions(players_db.get(pid) or {}))}
        if lo.optimize_lineup(roster + [cand], slots)["total_value"] > base + 1e-9:
            return False
    return bool(priced)


def usage_deficits(mine, seat, points, players_db, slots, roster_size):
    """target_total_p - my_count_p from the league's CURRENT fielded load (every roster's
    optimal lineup on its holdings so far). Derived; no literal."""
    league_load, total = collections.Counter(), 0
    for s, ids in mine.items():
        load, n = fielded_load(ids, points, players_db, slots)
        league_load.update(load)
        total += n
    mine_count = collections.Counter(_pos(players_db, p) for p in mine[seat])
    return {p: roster_size * league_load[p] / total - mine_count.get(p, 0) for p in league_load} if total else {}


def choose(arm, live, priced, my_ids, points, players_db, slots, mine=None, seat=None, roster_size=None):
    """The arm's pick in a pure-bench state; returns (row, note)."""
    scored = []
    deficits = usage_deficits(mine, seat, points, players_db, slots, roster_size) if arm == "B4" else {}
    for r in priced:
        pid = str(r["player_id"])
        key = None
        if arm == "B4":
            d = deficits.get(r["position"], -roster_size)
            key = (-round(d, 6), priced.index(r))
            note = f"deficit {d:+.2f} {dict((p, round(v, 2)) for p, v in deficits.items())}"
        elif arm == "B1G":
            cov, n, mean_gain = coverage(my_ids, pid, r["projected_points"], player_eligible_positions(players_db.get(pid) or {}), points, players_db, slots)
            key = (-round(cov * mean_gain, 2), priced.index(r))
            note = f"cov {cov}/{n} gain_sum {cov * mean_gain:.1f}"
        elif arm == "B1":
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


def ordering_verdict(comp, roster_positions=None):
    """The owner's ordering rule on a finished roster -- and, in a league with no dedicated TE
    slot, a SECOND reading of it, because the first one rewards the defect.

    `WR >= RB > TE` is trivially satisfied at TE 0. In the owner's real league that is not a
    technicality: the unfixed engine scores 3/3 there BY DRAFTING NO TIGHT ENDS, against his own
    roster which carries two, and against an optimal fielding of that league which uses about
    1.5 per team. So the verdict as written prefers a roster nobody would build to the one he
    actually built.

    He said why before any of this was measured: *"with no TE slot, but flex that can field them,
    the TE act as de-facto WR."* That is the rule, and the LEAGUE'S OWN RULEBOOK decides when it
    applies -- `dedicated_slot_counts["TE"] == 0`, nothing invented here. When it does, tight ends
    count on the receiving side and the ordering reads `(WR + TE) >= RB`; the ceiling on how many
    of them belong is not an ordering question at all, it is the derived band's.

    ADDITIVE, NEVER A REPLACEMENT. `pass_strict` and `pass_tendency` keep their exact meanings so
    every verdict already recorded stays comparable; the new keys sit beside them. A verdict that
    changed under your feet would make two runs of this probe incomparable, which is the failure
    the resume work exists to prevent.

    `roster_positions` is optional so existing callers keep working; without it only the original
    keys are returned, and `te_is_de_facto_receiver` is absent rather than False -- "not asked"
    and "asked, and no" are different answers."""
    wr, rb, te, qb = comp.get("WR", 0), comp.get("RB", 0), comp.get("TE", 0), comp.get("QB", 0)
    verdict = {"WR>=RB": wr >= rb, "RB>TE": rb > te, "RB>=TE": rb >= te, "QB<=4": qb <= 4,
               "pass_strict": wr >= rb and rb > te and qb <= 4,
               "pass_tendency": wr >= rb and rb >= te and qb <= 4}
    if roster_positions is None:
        return verdict
    de_facto = dr.dedicated_slot_counts(roster_positions).get("TE", 0) == 0
    verdict["te_is_de_facto_receiver"] = de_facto
    if de_facto:
        verdict["WR+TE>=RB"] = (wr + te) >= rb
        verdict["pass_flex_te"] = (wr + te) >= rb and qb <= 4
    return verdict


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
            if arm == "BASE":      # the pre-fix engine: the displacement term switched off
                with mock.patch.object(dr, "displacement_adjustments", lambda *a, **k: {}):
                    board = dr.compute_draft_board(merger, players_db, picks, seat, league, mode="balanced",
                                                   sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
            else:
                board = dr.compute_draft_board(merger, players_db, picks, seat, league, mode="balanced",
                                               sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
            live = [r for r in board if str(r["player_id"]) in points and str(r["player_id"]) not in taken]
            ordered = sorted(live, key=ps._board_order)
            priced = [r for r in ordered if r.get("final_score") is not None]
            bench = pure_bench(priced, mine[seat], points, players_db, slots)
            note = ""
            if bench and arm != "B0":
                chosen_row, note = choose(arm, live, priced, mine[seat], points, players_db, slots,
                                          mine=mine, seat=seat, roster_size=rounds)
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
    # roster_positions passed so a TE-slotless league also gets the de-facto-receiver reading;
    # see ordering_verdict for why the bare rule prefers a roster with no tight ends at all.
    dedicated = dr.dedicated_slot_counts(roster_positions)
    return {
        "arm": arm, "seat": seat, "sequence": seq, "states": states, "composition": composition,
        "bench_composition_by_pick_order": bench_comp,
        "verdict_full_roster": ordering_verdict(composition, roster_positions),
        "verdict_bench": ordering_verdict(bench_comp, roster_positions),
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
        # Every roster's player ids, so conditional picks (handcuffs) can be IDENTIFIED post
        # hoc from fields already on the rows -- NFL team + position + who owns the team's
        # top-projected player at that position. Identification only; nothing prices it.
        "all_rosters": {s: list(ids) for s, ids in mine.items()},
        "my_ids": list(mine[seat]),
    }


#: The owner's real league (out of sample for everything measured before it): 9 starters,
#: 5 bench, no dedicated TE slot, superflex, PPR with a 0.5 TE premium, 12 teams, third-round
#: reversal, redraft (no dynasty horizon). Seat 12 is the turn slot.
OWNER_LEAGUE = {
    "label": "OWNER_3RR_SF_noTE",
    "roster_positions": ["QB", "WR", "WR", "RB", "RB", "FLEX", "FLEX", "WRRB_FLEX", "SUPER_FLEX"] + ["BN"] * 5,
    "teams": 12, "rec": 1.0, "bonus_rec_te": 0.5, "dynasty": False, "draft_type": "3rr",
}


def build_league(spec_label, scoring):
    """A PROOF_FORMATS league (snake, dynasty, the mock roster) or the owner's league."""
    if spec_label == OWNER_LEAGUE["label"]:
        settings = dict(scoring or {})
        settings["rec"] = OWNER_LEAGUE["rec"]
        settings["bonus_rec_te"] = OWNER_LEAGUE["bonus_rec_te"]
        league = {"roster_positions": list(OWNER_LEAGUE["roster_positions"]), "scoring_settings": settings,
                  "total_rosters": OWNER_LEAGUE["teams"], "settings": {"type": 2 if OWNER_LEAGUE["dynasty"] else 0}}
        return league, OWNER_LEAGUE["draft_type"]
    spec = next(s for s in rp.PROOF_FORMATS if s["label"] == spec_label)
    league = dr.build_mock_league(teams=spec["teams"], superflex=spec["superflex"], scoring=spec["scoring"],
                                  te_premium=spec["te_premium"], dynasty=True, base_scoring=scoring)
    return league, "snake"


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
        league, draft_type = build_league(fmt_label, scoring)
        merger.set_league_format(db.league_format_hint(league))
        points = rp.scoreable_pool(merger, players_db, league, season)
        values = db.reference_values(merger, players_db, league, sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        rulers = {"cdme": values, "points": points}
        predraft = dr.compute_draft_board(merger, players_db, [], None, league, mode="balanced",
                                          sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        horizon_map = {str(r["player_id"]): r.get("time_horizon_adj") for r in predraft}
        seats = [str(i) for i in range(1, league["total_rosters"] + 1)]
        rounds = len(league["roster_positions"])
        slots = lo.slots_from_roster_positions(league["roster_positions"])
        pick_order = ds.generate_pick_order(seats, rounds, draft_type)
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
