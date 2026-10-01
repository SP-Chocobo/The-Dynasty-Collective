"""Is the replacement BAND tight in the wrong unit?

The earlier claim: three candidate replacements for DEF all sit inside a six-point band,
therefore WHICH player is replacement does not matter.  Six points is tight only relative to
the values at that position.  So measure the curve instead -- how many RANKS does a six-point
band cover at each position?  A band that is tight in points but loose in ranks means
replacement is ill-determined exactly where it looked settled.

Run from the REPO ROOT.
"""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
import collections
import data_merger as dm, draft_room as dr, draft_battery as dbat, run_draft_battery as rdb
import player_universe as pu

merger = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture(); scoring = rdb.scoring_settings_from_capture()
arm = next(a for a in dbat.league_matrix(scoring) if a["label"] == "12T_ppr_K_DEF")
league = arm["league"]
merger.set_league_format(dbat.league_format_hint(league))

board = dr.compute_draft_board(merger, players_db, [], my_roster_id=1, league=league,
                               mode="balanced", sleeper_projections=season,
                               sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
print("board rows: %d" % len(board))
print("columns carrying a projection: %s" % sorted(
    k for k in board[0] if "proj" in k.lower() or "point" in k.lower()))

COL = "projected_points" if "projected_points" in board[0] else None
if COL is None:
    COL = next(k for k in board[0] if "proj" in k.lower() and
               isinstance(board[0][k], (int, float)))
print("reading the curve from: %s\n" % COL)

curves = {}
for row in board:
    pos = pu.player_position(players_db.get(str(row["player_id"])) or {})
    v = row.get(COL)
    if pos is None or v is None:
        continue
    curves.setdefault(pos, []).append(float(v))
for p in curves:
    curves[p].sort(reverse=True)

POS = [p for p in ("RB", "WR", "TE", "QB", "K", "DEF") if p in curves]

print("=== the curve at each position: projected points by within-position rank ===")
print("%-5s%9s%9s%9s%9s%9s%9s%12s" % ("pos","r1","r5","r12","r20","r32","last","r1-r12"))
for p in POS:
    s = curves[p]
    at = lambda i: s[min(i, len(s) - 1)]
    print("%-5s%9.1f%9.1f%9.1f%9.1f%9.1f%9.1f%12.1f" % (
        p, at(0), at(4), at(11), at(19), at(31), s[-1], at(0) - at(11)))

print()
print("=== FLATNESS around replacement: points lost per rank, ranks 10-20 ===")
print("%-5s%16s%15s%17s" % ("pos", "slope r10-r20", "r1-r12 gap", "gap as % of r1"))
slopes = {}
for p in POS:
    s = curves[p]
    lo, hi = min(9, len(s) - 1), min(19, len(s) - 1)
    slopes[p] = (s[lo] - s[hi]) / max(hi - lo, 1)
    gap = s[0] - s[min(11, len(s) - 1)]
    print("%-5s%16.2f%15.1f%16.1f%%" % (p, slopes[p], gap, 100 * gap / s[0]))

print()
print("=== how many RANKS of slack does a 6-point band cover at each position? ===")
for p in POS:
    print("  %-5s a 6-point band spans %5.1f ranks  (pool of %d)" % (
        p, 6.0 / slopes[p] if slopes[p] else float("inf"), len(curves[p])))
