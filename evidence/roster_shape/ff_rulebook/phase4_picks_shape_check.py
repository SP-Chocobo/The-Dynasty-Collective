"""Why did the same player get two different final_scores in two of my probes?

One arm passes picks as {player_id, roster_id}; the other as production does
({pick_no, round, roster_id, player_id}). Same process, same code, one thing toggled.
Run from the repo root with PYTHONPATH=.
"""
import json
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

CAP = json.load(open("data/league_captures/fourth_and_forever.json")); RP = CAP["roster_positions"]
L = {"roster_positions": RP,
     "scoring_settings": {k: v["value"] for k, v in CAP["scoring_settings_observed"].items()},
     "total_rosters": 12, "settings": {"type": 2}}
D = json.load(open("evidence/roster_shape/ff_rulebook/ff_draft.json"))["picks"]
m = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
m.set_league_format(db.league_format_hint(L)); season = rdb.season_projections_from_capture()
def f(x):
    try: return float(x)
    except: return None
IDX = 204                                    # board before pick 205
THIN = [{"player_id": q["player_id"], "roster_id": q["roster_id"]} for q in D[:IDX]]
FULL = [{"pick_no": i + 1, "round": i // 12 + 1, "roster_id": q["roster_id"],
         "player_id": q["player_id"]} for i, q in enumerate(D[:IDX])]

for label, picks in (("THIN {player_id, roster_id}", THIN),
                     ("FULL {pick_no, round, roster_id, player_id}", FULL)):
    rows = dr.compute_draft_board(m, players_db, picks, "12", L,
                                  sleeper_projections=season,
                                  sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    priced = sorted([r for r in rows if f(r.get("final_score")) is not None],
                    key=lambda r: -f(r["final_score"]))
    lemon = next((r for r in rows if str(r.get("name")) == "Makai Lemon"), None)
    print(f"{label}")
    print(f"   rows={len(rows)}  priced={len(priced)}  "
          f"top5={[(r['position'], round(f(r['final_score']), 2)) for r in priced[:5]]}")
    if lemon is not None:
        print(f"   Makai Lemon final_score={f(lemon.get('final_score')):.2f}  "
              f"bpa={f(lemon.get('bpa')):.2f}  "
              f"growth={lemon.get('growth_signal')}  mode-sensitive fields above")
    print()

# Which field drives it? round detection for upside mode.
print("upside-mode round detection, both shapes, explicit:")
for label, picks in (("THIN", THIN), ("FULL", FULL)):
    for mode in ("balanced", "upside"):
        rows = dr.compute_draft_board(m, players_db, picks, "12", L, mode=mode,
                                      sleeper_projections=season,
                                      sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        priced = sorted([r for r in rows if f(r.get("final_score")) is not None],
                        key=lambda r: -f(r["final_score"]))
        print(f"   {label:5} mode={mode:9} top row = {priced[0]['position']} "
              f"{f(priced[0]['final_score']):.2f}  {str(priced[0].get('name'))[:20]}")
