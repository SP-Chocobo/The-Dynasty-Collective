"""Per-position replacement bands, derived the way this repo already accepts (#56).

QB_STARTABLE_FLOOR_FRACTION's own comment states the test: a constant is legitimate when it
sits in a STABILITY BASIN -- "a 48-point-wide band of threshold values all producing the same
replacement rank" -- and illegitimate when its plausible range straddles a boundary.

That test has a closed form. The startable-floor model sets the boundary at
    boundary(t) = #{players projecting >= t}
so boundary(t) == r exactly when s[r] < t <= s[r-1].  The stability basin of rank r IS the
marginal gap s[r-1] - s[r].  No sweep, no grid, no chosen constant.

So: measure the marginal gap at each position's own demand rank, against the gaps around it.
A position whose demand rank sits on a real cliff has a determinate replacement.  A position
whose demand rank sits on a smooth flat stretch does not, and the band is however wide the
flat stretch is.

Run from the REPO ROOT.
"""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
import statistics
import data_merger as dm, draft_room as dr, draft_battery as dbat, run_draft_battery as rdb
import player_universe as pu

merger = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture(); scoring = rdb.scoring_settings_from_capture()
arm = next(a for a in dbat.league_matrix(scoring) if a["label"] == "12T_ppr_K_DEF")
league = arm["league"]; teams = arm["teams"]
merger.set_league_format(dbat.league_format_hint(league))

# ---------------------------------------------------------------- calibration against QB
# Reproduce the ONE basin this repo has already measured and accepted, on the same data
# qb_startable_floor reads (the committed baseline, not the board).  If the instrument cannot
# find the cliff that is documented to be there, nothing it says about K or DEF is worth
# reading.
proj = merger.projections
qb = sorted(proj[(proj["position"] == "QB") & proj["projection"].notna()]["projection"]
            .astype(float), reverse=True)
anchor = qb[dr.QB_STARTABLE_ANCHOR_RANK - 1]
floor = dr.QB_STARTABLE_FLOOR_FRACTION * anchor
rank_at = lambda s, t: sum(1 for v in s if v >= t)
print("=== calibration: the QB cliff this repo already accepts ===")
print("  QB%d = %.1f   floor = %.2f x anchor = %.1f   -> startable rank %d"
      % (dr.QB_STARTABLE_ANCHOR_RANK, anchor, dr.QB_STARTABLE_FLOOR_FRACTION, floor,
         rank_at(qb, floor)))
lo, hi = 0.45 * anchor, 0.60 * anchor
print("  the documented fraction range 0.45-0.60 spans %.1f points (%.1f to %.1f)"
      % (hi - lo, lo, hi))
print("  ranks it identifies across that range: %s"
      % sorted({rank_at(qb, lo + i * (hi - lo) / 200) for i in range(201)}))
r = rank_at(qb, floor)
print("  basin of rank %d = QB%d - QB%d = %.1f - %.1f = %.1f points"
      % (r, r, r + 1, qb[r - 1], qb[r], qb[r - 1] - qb[r]))
print("  neighbourhood gaps QB24..QB32: %s"
      % " ".join("%.0f" % (qb[i] - qb[i + 1]) for i in range(23, min(32, len(qb) - 1))))

# ---------------------------------------------------------------- the live board
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

print()
print("=== each position's demand rank, and the basin it sits in ===")
print("%-5s%8s%10s%12s%14s%14s%12s" % (
    "pos", "demand", "value", "basin@d", "median gap", "max gap", "at rank"))
summary = {}
for p in POS:
    s = curves[p]
    d = int(round(teams * slots.get(p, 0.0)))
    if d < 1 or d >= len(s):
        print("%-5s  demand rank %s outside the priced list (%d)" % (p, d, len(s)))
        continue
    gaps = [s[i] - s[i + 1] for i in range(len(s) - 1)]
    region = gaps[:min(2 * d, len(gaps))]          # ranks 1 .. 2*demand, the startable half
    basin = gaps[d - 1]
    med = statistics.median(region)
    mx = max(region); mx_at = region.index(mx) + 1
    summary[p] = (d, s[d - 1], basin, med, mx, mx_at)
    print("%-5s%8d%10.1f%12.2f%14.2f%14.2f%12d"
          % (p, d, s[d - 1], basin, med, mx, mx_at))

print()
print("=== is the demand rank a CLIFF, or a point on a smooth stretch? ===")
print("%-5s%16s%20s" % ("pos", "basin / median", "reading"))
for p, (d, v, basin, med, mx, mx_at) in summary.items():
    ratio = basin / med if med else float("inf")
    print("%-5s%16.2f   %s" % (p, ratio, "cliff" if ratio >= 3 else
                               ("edge" if ratio >= 1.5 else "smooth -- no boundary here")))

print()
print("=== the band: ranks within the position's own largest local gap of demand rank ===")
print("%-5s%12s%14s%16s" % ("pos", "demand", "band (ranks)", "band (points)"))
for p, (d, v, basin, med, mx, mx_at) in summary.items():
    s = curves[p]
    lo = d
    while lo > 1 and (s[lo - 2] - s[d - 1]) < mx:
        lo -= 1
    hi = d
    while hi < len(s) and (s[d - 1] - s[hi]) < mx:
        hi += 1
    print("%-5s%12d   %-14s%16.1f" % (p, d, "%d - %d  (%d wide)" % (lo, hi, hi - lo + 1),
                                      s[lo - 1] - s[hi - 1]))
