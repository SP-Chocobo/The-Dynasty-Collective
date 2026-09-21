"""Is the false premise ALREADY live? _admits_to_pool returns True on years_exp == 0
unconditionally, BEFORE the status gate -- the same clause #273 found letting placeholders
through. If `years_exp == 0` also covers retired players, they are on the normal board now.
"""
import collections
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

merger = dm.DataMerger()
players_db, _prov = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()
league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr",
                              te_premium=False, dynasty=True)
merger.set_league_format(db.league_format_hint(league))

board = dr.compute_draft_board(
    merger, players_db, [], my_roster_id="1", league=league, mode="balanced",
    sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
print(f"normal board (pool_scope='all'): {len(board)} rows\n")

NAMES = {"Kurt Warner", "Byron Leftwich", "Cedric Benson", "Kevin O'Connell", "Sean Ryan"}
for r in board:
    if r.get("name") in NAMES:
        info = players_db.get(str(r["player_id"]), {})
        print(f"  ON THE BOARD: {r['name']:<18} pos {r.get('position'):<4} "
              f"age {info.get('age')} years_exp {info.get('years_exp')} "
              f"team {info.get('team')} status {info.get('status')} "
              f"proj {r.get('projected_points')} uv {r.get('universal_value')}")

# How many board rows are admitted ONLY by the rookie clause?
only_rookie_clause = []
for r in board:
    info = players_db.get(str(r["player_id"]), {})
    if info.get("years_exp") != dr.ROOKIE_YEARS_EXP:
        continue
    if r.get("projected_points") is not None:
        continue          # clause 1 would have admitted him anyway
    if info.get("team"):
        continue          # clause 3 would have admitted him anyway
    only_rookie_clause.append((r, info))
print(f"\nrows on the board admitted ONLY by the years_exp==0 clause "
      f"(no projection, no team): {len(only_rookie_clause)}")
ages = []
for r, info in only_rookie_clause:
    try: ages.append(float(info["age"]))
    except (TypeError, ValueError, KeyError): pass
if ages:
    ages.sort()
    print(f"   of those, age reported for {len(ages)}: median {ages[len(ages)//2]:.0f}  "
          f"max {max(ages):.0f}   age>=27: {sum(1 for a in ages if a>=27)}")
print(f"   positions: {dict(collections.Counter(r.get('position') for r,_ in only_rookie_clause).most_common(8))}")
print(f"   statuses:  {dict(collections.Counter(i.get('status') for _,i in only_rookie_clause).most_common(8))}")
