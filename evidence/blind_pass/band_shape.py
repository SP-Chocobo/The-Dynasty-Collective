"""What per-position bands would actually LOOK like -- and whether widening one changes anything.

Two questions, in order:
  1. For any error bar you believe in the projection, how many ranks wide is each position's
     band?  Reported as a function of that error bar, because the error bar is the one number
     this repo does not have yet (measure_projection_accuracy.py, pending a networked run).
  2. THE NULL CHECK.  If replacement became the band MEAN instead of the band POINT, how far
     does each position's replacement level actually move?  A symmetric band on a locally
     straight curve moves it by nothing, and if that is what happens, band width is the wrong
     lever and no ruling should be built on it.

Run from the REPO ROOT.
"""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
import statistics
import data_merger as dm, draft_room as dr, draft_battery as dbat, run_draft_battery as rdb
import player_universe as pu

merger = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture(); scoring = rdb.scoring_settings_from_capture()
arm = next(a for a in dbat.league_matrix(scoring) if a["label"] == "12T_ppr_K_DEF")
league, teams = arm["league"], arm["teams"]
merger.set_league_format(dbat.league_format_hint(league))

board = dr.compute_draft_board(merger, players_db, [], my_roster_id=1, league=league,
                               mode="balanced", sleeper_projections=season,
                               sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
curves = {}
for row in board:
    pos = pu.player_position(players_db.get(str(row["player_id"])) or {})
    v = row.get("projected_points")
    if pos and v is not None:
        curves.setdefault(pos, []).append(float(v))
for p in curves:
    curves[p].sort(reverse=True)

slots = dr.starter_slot_counts(league["roster_positions"], None, teams)
POS = [p for p in ("RB", "WR", "TE", "QB", "K", "DEF") if p in curves]
demand = {p: int(round(teams * slots.get(p, 0.0))) for p in POS}

SES = [1, 2, 5, 10, 15, 20]
print("=== BAND WIDTH IN RANKS, as a function of the projection's error bar ===")
print("    (ranks whose projection sits within +/- SE of the demand-rank player's)")
print("%-5s%9s" % ("pos", "demand") + "".join("%10s" % ("SE=%d" % e) for e in SES))
bands = {}
for p in POS:
    s, d = curves[p], demand[p]
    if not (1 <= d < len(s)):
        continue
    v = s[d - 1]
    row = []
    for e in SES:
        lo = d
        while lo > 1 and s[lo - 2] - v <= e:
            lo -= 1
        hi = d
        while hi < len(s) and v - s[hi] <= e:
            hi += 1
        bands.setdefault(p, {})[e] = (lo, hi)
        row.append(hi - lo + 1)
    print("%-5s%9d" % (p, d) + "".join("%10d" % n for n in row))

print()
print("=== THE NULL CHECK: does a band-MEAN replacement differ from the band POINT? ===")
print("    (if these are ~0, band width is the wrong lever and nothing should rest on it)")
print("%-5s%10s" % ("pos", "point") + "".join("%12s" % ("d@SE=%d" % e) for e in SES))
for p in POS:
    s, d = curves[p], demand[p]
    if p not in bands:
        continue
    v = s[d - 1]
    row = []
    for e in SES:
        lo, hi = bands[p][e]
        row.append(statistics.fmean(s[lo - 1:hi]) - v)
    print("%-5s%10.1f" % (p, v) + "".join("%+12.2f" % x for x in row))

print()
print("=== and what that movement is WORTH: shift in the top player's VOR, SE=10 ===")
print("%-5s%12s%12s%12s%10s" % ("pos", "r1", "VOR now", "VOR banded", "change"))
for p in POS:
    s, d = curves[p], demand[p]
    if p not in bands:
        continue
    lo, hi = bands[p][10]
    now, banded = s[0] - s[d - 1], s[0] - statistics.fmean(s[lo - 1:hi])
    print("%-5s%12.1f%12.1f%12.1f%+10.2f" % (p, s[0], now, banded, banded - now))
