"""First board build on Fourth and Forever's REAL rulebook. Run from repo root."""
import json, collections, sys
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

CAP = json.load(open("data/league_captures/fourth_and_forever.json"))
SCORING = {k: v["value"] for k, v in CAP["scoring_settings_observed"].items()}
LEAGUE = {
    "roster_positions": CAP["roster_positions"],
    "scoring_settings": SCORING,
    "total_rosters": 12,
    "settings": {"type": 2},          # dynasty
}

merger = dm.DataMerger()                                    # 1. repo root
players_db = rdb.build_players_db(merger)                   # 2. full pool
hint = db.league_format_hint(LEAGUE)                        # 3. derived, never carried
merger.set_league_format(hint)                              # NEVER SKIP
print("format hint:", hint)
print("pool:", len(players_db))

rp = LEAGUE["roster_positions"]
print("starter_slot_counts:", {k: round(v,3) for k,v in dr.starter_slot_counts(rp).items() if v})

rows = dr.compute_draft_board(merger, players_db, [], "1", LEAGUE)
print("\nboard rows:", len(rows))
print("columns:", sorted(rows[0].keys()))
json.dump(rows, open("/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/ff/ff_board.json","w"), default=str)
print("saved.")
