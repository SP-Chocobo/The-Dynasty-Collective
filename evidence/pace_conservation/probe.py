"""Mandate 1.3: measure expected_taken against the picks actually available in the gap.

Run from the repository root. Five-line fixture per the engine-measurement skill, including
set_league_format -- without it every format drafts off one rankings export.
"""
import json, sys
import data_merger as dm, draft_room as dr, draft_battery as db, draft_strategy as ds
import run_draft_battery as rdb

merger = dm.DataMerger()
# THE CAPTURE UNIVERSE, not the vendor reconstruction: build_players_db now REFUSES while a
# capture exists (#201/#204/#222), and it is right to -- the reconstruction has no injury_status
# and an id space that only coincidentally overlaps the real one.
players_db, universe = rdb.build_players_db_from_capture()
season_projections = rdb.season_projections_from_capture()
weekly = rdb.weekly_projections_from_capture()
BASIS = dr.SLEEPER_BASIS_SEASON_SUM
PRICING = dict(sleeper_projections=season_projections, sleeper_basis=BASIS,
               weekly_projections=weekly)

matrix = db.league_matrix(rdb.scoring_settings_from_capture())
arm = next(e for e in matrix if e["label"] == "12T_ppr_SF")
league = arm["league"]
merger.set_league_format(db.league_format_hint(league))
teams, rounds = int(arm["teams"]), int(arm["rounds"])

order = ds.generate_pick_order(list(range(1, teams + 1)), total_rounds=rounds, draft_type="snake")
me = order[0]

def report(current_index, picks):
    """The forfeits at one turn, plus the gap they are summed over."""
    nxt = ds.find_next_pick_index(order, me, current_index)
    intervening = ds.intervening_roster_ids(order, current_index, nxt)
    if not intervening:
        return None
    my_board = {r["player_id"]: r for r in dr.compute_draft_board(
        merger, players_db, picks, my_roster_id=me, league=league, mode="auto", pool_scope="all",
        **PRICING)}
    boards = ds._build_opponent_boards(
        merger, players_db, picks, league, intervening, mode="auto", pool_scope="all",
        **PRICING)
    curves = ds._position_curves(my_board)
    f = ds.positional_forfeits(curves, boards, intervening,
                               ds.detect_positional_run(picks, players_db),
                               picks=picks, players_db=players_db,
                               roster_positions=league.get("roster_positions") or [],
                               picks_made_now=len(picks))
    taken_now = {}
    for p in picks:
        pos = ds.player_position(players_db.get(str(p.get("player_id")), {}))
        taken_now[pos] = taken_now.get(pos, 0) + 1
    end = len(picks) + len(intervening)
    convention_now = ds.expected_position_pace("QB", len(picks), league.get("roster_positions") or [])
    convention_end = ds.expected_position_pace("QB", end, league.get("roster_positions") or [])
    return {
        "picks_made": len(picks),
        "gap": len(intervening),
        "expected_taken": {k: v["expected_taken"] for k, v in sorted(f.items())},
        "total_expected": round(sum(v["expected_taken"] for v in f.values()), 2),
        "forfeit": {k: v["forfeit"] for k, v in sorted(f.items())},
        "qb_taken_so_far": taken_now.get("QB", 0),
        "convention_cumulative_now": convention_now,
        "convention_cumulative_at_my_next_turn": convention_end,
        "convention_increment_over_the_gap": (None if None in (convention_now, convention_end)
                                              else round(convention_end - (taken_now.get("QB", 0)), 2)),
    }

# Turn 0 (1.01, nothing drafted) and a mid-draft turn with real picks on the board.
out = {}
r = report(0, [])
out["1.01"] = r

# A MID-DRAFT TURN WITH A REAL BOARD. Seat 1 picks at 0, 23, 24 and 47 under snake, so index 23
# is back-to-back (no gap AHEAD -- the skill's own warning) and index 24 is the one with 22
# intervening picks. Played by the engine's own chairs so the QBs already gone are really gone.
picks = []
for i in range(24):
    rid = order[i]
    board = dr.compute_draft_board(merger, players_db, picks, my_roster_id=rid, league=league,
                                   mode="auto", pool_scope="all", **PRICING)
    pid = board[0]["player_id"]
    picks.append({"pick_no": i + 1, "round": i // teams + 1, "roster_id": str(rid),
                  "player_id": pid, "draft_slot": (i % teams) + 1})
out["after_24_picks"] = report(24, picks)

print(json.dumps(out, indent=2))
