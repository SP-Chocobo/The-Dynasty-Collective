"""B4, live: the board's top row is NOT what gets drafted. WHERE is the tight end chosen?

simulate_full_draft takes pick_synthesis.build_snapshot(...).candidates[0], NOT
compute_draft_board's row 0. This calls build_snapshot exactly as the draft did and prints
both orderings side by side at the picks where the recorded draft took a tight end.
Run from the repo root with PYTHONPATH=.
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

for AT in (193, 205, 229, 241, 281):
    idx = AT - 1
    rec = D[idx]
    roster_id = str(ORDER[idx])
    picks = [{"pick_no": i + 1, "round": i // 12 + 1, "roster_id": q["roster_id"],
              "player_id": q["player_id"]} for i, q in enumerate(D[:idx])]
    snap = pick_synthesis.build_snapshot(
        m, players_db, picks, ORDER, idx, roster_id, L,
        pick_label=f"{idx // 12 + 1}.{(idx % 12) + 1:02d}", mode="auto", pool_scope="all",
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    rows = dr.compute_draft_board(m, players_db,
        [{"player_id": q["player_id"], "roster_id": q["roster_id"]} for q in D[:idx]],
        roster_id, L, sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    priced = [r for r in rows if f(r.get("final_score")) is not None]
    priced.sort(key=lambda r: -f(r["final_score"]))
    cands = list(snap.candidates)[:5]
    print(f"pick {AT}  seat {roster_id}  regime={snap.decision_regime}  "
          f"recorded pick = {rec.get('position')} {rec.get('name')}")
    print(f"  compute_draft_board top 5 : "
          f"{[(r['position'], round(f(r['final_score']), 1)) for r in priced[:5]]}")
    print(f"  build_snapshot candidates : "
          f"{[(getattr(c, 'position', '?'), round(f(getattr(c, 'final_score', None)) or 0, 1)) for c in cands]}")
    chosen = cands[0] if cands else None
    if chosen is not None:
        print(f"  candidates[0] = {getattr(chosen, 'position', '?')} "
              f"{getattr(chosen, 'name', '?')}  (id {getattr(chosen, 'player_id', '?')})  "
              f"MATCHES RECORDED: {str(getattr(chosen, 'player_id', '')) == str(rec['player_id'])}")
        top = priced[0] if priced else None
        if top is not None:
            print(f"  board row 0   = {top['position']} {top.get('name')}  "
                  f"(id {top['player_id']})  "
                  f"SAME AS candidates[0]: "
                  f"{str(top['player_id']) == str(getattr(chosen, 'player_id', ''))}")
    print(f"  n candidates = {len(snap.candidates)}, n priced board rows = {len(priced)}")
    print()
