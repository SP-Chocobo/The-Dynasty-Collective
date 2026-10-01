"""The F&F opening board, on the REAL capture universe (#201).

CORRECTED. The first version of this file used rdb.build_players_db -- the VENDOR
RECONSTRUCTION, 764 players, id space "16"/"291" -- while run_ff_draft.py used
rdb.build_players_db_from_capture -- the real Sleeper universe, 6,595 players, id space
"13384". Two different populations with only coincidental id overlap, so every number
FINDING_01..04 drew off the old board described a pool the engine never drafts from.
#201 exists for exactly this reason and made the reconstruction a raise-on-missing
forbidden fallback for the battery; this probe was still calling the old function.

Run from the repo root.
"""
import json, collections
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

CAP = json.load(open("data/league_captures/fourth_and_forever.json"))
LEAGUE = {"roster_positions": CAP["roster_positions"],
          "scoring_settings": {k: v["value"] for k, v in CAP["scoring_settings_observed"].items()},
          "total_rosters": 12, "settings": {"type": 2}}

merger = dm.DataMerger()
players_db, prov = rdb.build_players_db_from_capture()      # THE REAL UNIVERSE
merger.set_league_format(db.league_format_hint(LEAGUE))
season = rdb.season_projections_from_capture()
print("universe:", prov["players_in_pool"], "season projections:", len(season))

rows = dr.compute_draft_board(merger, players_db, [], "1", LEAGUE,
                              sleeper_projections=season,
                              sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
json.dump(rows, open("/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/ff/ff_board_real.json","w"), default=str)
c = collections.Counter(r["position"] for r in rows); N = sum(c.values())
print("\nPRICED BOARD on the real universe:", N, "rows for a 312-pick startup")
print("composition:", {p: f"{c[p]} ({c[p]/N:.1%})" for p in ("QB","RB","WR","TE") if c[p]})
