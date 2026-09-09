"""What happens to the higher-priced WR candidates in the selection path?

  build_snapshot -> board -> narrow_candidates -> candidates -> candidates[0] -> the pick

narrow_candidates is ADDITIVE by contract: top_n by _board_order, PLUS the best remaining at
every position, PLUS the user's flagged player. It removes nothing. So the question is not
"who was filtered out" but "what re-ordered them" -- _board_order is a SECOND ORDERING
AUTHORITY (#155) and it leads with the feasibility backstop, not final_score.

This captures, for each of the five divergent picks: the board's top rows by final_score, the
post-narrowing candidate list in its real order, and for every candidate the two components of
_board_order -- fills_required_slot and final_score -- plus how it entered the list.

Observes production. Run from the repo root with PYTHONPATH=.
"""
import json
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb
import draft_strategy as dstrat, pick_synthesis

CAP = json.load(open("data/league_captures/fourth_and_forever.json")); RP = CAP["roster_positions"]
L = {"roster_positions": RP,
     "scoring_settings": {k: v["value"] for k, v in CAP["scoring_settings_observed"].items()},
     "total_rosters": 12, "settings": {"type": 2}}
D = json.load(open("evidence/roster_shape/ff_rulebook/ff_draft.json"))["picks"]
m = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
m.set_league_format(db.league_format_hint(L)); season = rdb.season_projections_from_capture()
ORDER = dstrat.generate_pick_order([p["roster_id"] for p in D[:12]], 26, "snake")
def f(x):
    try: return float(x)
    except: return None

print(f"roster_positions length = {len(RP)}  (feasibility_first's fallback total_picks "
      f"when draft_rounds is not supplied); actual draft rounds = 26\n")

CAP_NC = {}
_nc = pick_synthesis.narrow_candidates
def nc_spy(board, top_n=pick_synthesis.DEFAULT_NARROW_COUNT, user_selected_player_id=None,
           position_depth=None):
    out = _nc(board, top_n, user_selected_player_id, position_depth)
    CAP_NC.clear()
    CAP_NC["board_n"] = len(board)
    CAP_NC["top_n"] = top_n
    CAP_NC["depth"] = dict(position_depth) if position_depth else None
    CAP_NC["out"] = list(out)
    ranked = sorted(board, key=pick_synthesis._board_order)
    CAP_NC["ranked"] = ranked
    CAP_NC["top_slice_ids"] = {r["player_id"] for r in ranked[:top_n]}
    CAP_NC["backstop_binds"] = any(r.get("fills_required_slot") for r in board)
    return out
pick_synthesis.narrow_candidates = nc_spy

for AT in (193, 205, 229, 241, 281):
    idx = AT - 1
    rec = D[idx]; roster_id = str(ORDER[idx])
    picks = [{"pick_no": i + 1, "round": i // 12 + 1, "roster_id": q["roster_id"],
              "player_id": q["player_id"]} for i, q in enumerate(D[:idx])]
    snap = pick_synthesis.build_snapshot(
        m, players_db, picks, ORDER, idx, roster_id, L,
        pick_label=f"{idx // 12 + 1}.{(idx % 12) + 1:02d}", mode="auto", pool_scope="all",
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    mine = [q for q in D[:idx] if q["roster_id"] == roster_id]
    held = {}
    for q in mine:
        held[q["position"]] = held.get(q["position"], 0) + 1
    print(f"=== pick {AT}  seat {roster_id}  recorded={rec.get('position')}  "
          f"my picks so far={len(mine)}  held={held}")
    print(f"    board rows in={CAP_NC['board_n']}  top_n={CAP_NC['top_n']}  "
          f"position_depth={CAP_NC['depth']}  "
          f"backstop binds on ANY row: {CAP_NC['backstop_binds']}")
    print(f"    {'#':>3} {'pos':4}{'final_score':>12}{'fills_req':>11}{'entered via':>16}  name")
    for i, r in enumerate(CAP_NC["out"], 1):
        via = "top_n slice" if r["player_id"] in CAP_NC["top_slice_ids"] else "best-at-position"
        print(f"    {i:>3} {r['position']:4}"
              f"{(f(r.get('final_score')) if f(r.get('final_score')) is not None else float('nan')):>12.2f}"
              f"{str(r.get('fills_required_slot')):>11}{via:>16}  {str(r.get('name'))[:24]}")
    # where did the board's best-by-score rows go?
    by_score = sorted([r for r in CAP_NC["ranked"] if f(r.get("final_score")) is not None],
                      key=lambda r: -f(r["final_score"]))
    out_ids = [r["player_id"] for r in CAP_NC["out"]]
    print(f"    top 3 by RAW final_score, and where they land in the candidate order:")
    for r in by_score[:3]:
        pos_in = (out_ids.index(r["player_id"]) + 1) if r["player_id"] in out_ids else None
        print(f"        {r['position']:4}{f(r['final_score']):>10.2f}  "
              f"fills_req={str(r.get('fills_required_slot')):>5}  "
              f"candidate #{pos_in if pos_in else 'NOT INCLUDED'}  {str(r.get('name'))[:22]}")
    print()
pick_synthesis.narrow_candidates = _nc
