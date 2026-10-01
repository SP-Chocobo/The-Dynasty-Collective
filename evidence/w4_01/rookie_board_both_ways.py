"""W4-01, the product consequence: the rookie draft board under each definition.

Not the raw universe -- the BOARD, after _admits_to_pool and position eligibility, which is
what a person running a rookie draft actually sees.
"""
import collections, statistics
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

merger = dm.DataMerger()
players_db, _prov = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()
league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr",
                              te_premium=False, dynasty=True)
merger.set_league_format(db.league_format_hint(league))

def board(scope, promote_years_exp=False):
    if promote_years_exp:
        real = dr._rookie_lookup
        def patched(m):
            out = {}
            for pid, info in players_db.items():
                nm = dr.player_name(info, pid)
                key = (dr.name_key(dr.normalize_name(nm)),
                       dr.identity_namespace(dr.player_position(info)))
                out[key] = (info.get("years_exp") == dr.ROOKIE_YEARS_EXP)
            return out
        dr._rookie_lookup = patched
    try:
        return dr.compute_draft_board(
            merger, players_db, [], my_roster_id="1", league=league, mode="balanced",
            sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
            pool_scope=scope)
    finally:
        if promote_years_exp:
            dr._rookie_lookup = real

ktc = board("rookies_only", False)
yex = board("rookies_only", True)
print(f"rookie board, KTC flag      : {len(ktc)}")
print(f"rookie board, years_exp == 0: {len(yex)}\n")

by_id_k = {str(r['player_id']) for r in ktc}
entrants = [r for r in yex if str(r['player_id']) not in by_id_k]
leavers = [r for r in ktc if str(r['player_id']) not in {str(x['player_id']) for x in yex}]
print(f"enter: {len(entrants)}   leave: {len(leavers)}\n")

def prof(label, rows):
    ages, teams, priced = [], 0, 0
    for r in rows:
        info = players_db.get(str(r["player_id"]), {})
        a = info.get("age")
        try:
            if a is not None: ages.append(float(a))
        except (TypeError, ValueError): pass
        if info.get("team"): teams += 1
        if r.get("projected_points") is not None: priced += 1
    print(f"{label} n={len(rows)}")
    print(f"   age reported {len(ages)}/{len(rows)}" + (
        f"  median {statistics.median(ages):.0f}  max {max(ages):.0f}  "
        f">=25 {sum(1 for a in ages if a>=25)}" if ages else ""))
    print(f"   on an NFL team {teams} ({teams/max(len(rows),1)*100:.0f}%)   "
          f"carrying a projection {priced} ({priced/max(len(rows),1)*100:.0f}%)")
    print(f"   positions: {dict(collections.Counter(r.get('position') for r in rows).most_common(8))}")

prof("ENTRANTS", entrants)
print()
prof("LEAVERS", leavers)
print("\noldest entrants:")
aged = []
for r in entrants:
    info = players_db.get(str(r["player_id"]), {})
    try:
        aged.append((float(info["age"]), r.get("name"), r.get("position"), info.get("team")))
    except (TypeError, ValueError, KeyError): pass
for a, n, p, t in sorted(aged, reverse=True)[:6]:
    print(f"   age {a:.0f}  {n}  ({p}, team={t})")
