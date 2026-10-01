"""Does the level CANCEL between VOR and displacement_adj?

  price ~ universal_value(points - level) + displacement_adj(level - displaced)

If the SAME level appears in both, it cancels algebraically and the basis switch has no net
effect on the candidate's price. universal_value is NOT raw VOR (bpa is normalised, #74/#76)
and the team terms are capped, so the cancellation may or may not survive. Measured, not
assumed. Run from the repo root with PYTHONPATH=.
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

STATE = {}
_da = dr.displacement_adjustments
def da_spy(rp, rpos, levels, unpriced=None):
    STATE["level_TE"] = levels.get("TE")
    return _da(rp, rpos, levels, unpriced)
dr.displacement_adjustments = da_spy

seen = {}
for i, p in enumerate(D):
    prior = D[:i]; me = p["roster_id"]
    n = sum(1 for q in prior if q["roster_id"] == me and q["position"] == "TE")
    if n not in seen and 2 <= n <= 8 and p["position"] == "TE":
        seen[n] = (i + 1, me, prior)

print("The TOP TE row at each rung -- every column read off the production board row\n")
print(f"{'held':>5}{'pick':>6}{'level':>9}{'proj_pts':>10}{'bpa':>9}{'disp_adj':>10}"
      f"{'need':>7}{'elig':>7}{'depth':>8}{'TAV':>9}{'pts-lvl':>9}{'sum chk':>9}")
for n in sorted(seen):
    AT, me, prior = seen[n]
    STATE.clear()
    # PRODUCTION-SHAPED PICKS. mode="auto" resolves upside-vs-balanced from the picks' own
    # `round` field; a thin {player_id, roster_id} dict silently lands in the OTHER mode
    # (measured in phase4_picks_shape_check.py). Build inputs in production's shape.
    rows = dr.compute_draft_board(m, players_db,
        [{"pick_no": j + 1, "round": j // 12 + 1, "roster_id": q["roster_id"],
          "player_id": q["player_id"]} for j, q in enumerate(prior)], me, L,
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    rows = [r for r in rows if f(r.get("final_score")) is not None]
    rows.sort(key=lambda r: -f(r["final_score"]))
    te = [r for r in rows if r["position"] == "TE"]
    if not te: continue
    t = te[0]
    lvl = STATE.get("level_TE")
    pts = f(t.get("projected_points"))
    bpa = f(t.get("bpa")) or 0.0
    adj = f(t.get("displacement_adj")) or 0.0
    nb = f(t.get("need_bonus")) or 0.0
    eb = f(t.get("eligibility_bonus")) or 0.0
    dx = f(t.get("depth_exposure")) or 0.0
    tav = f(t.get("team_acquisition_value"))
    print(f"{n:>5}{AT:>6}{(lvl if lvl is not None else float('nan')):>9.2f}"
          f"{(pts if pts is not None else float('nan')):>10.2f}{bpa:>9.2f}{adj:>10.2f}"
          f"{nb:>7.2f}{eb:>7.2f}{dx:>8.2f}"
          f"{(tav if tav is not None else float('nan')):>9.2f}"
          f"{((pts - lvl) if (pts is not None and lvl is not None) else float('nan')):>9.2f}"
          f"{bpa + adj + nb + eb + dx:>9.2f}")
    print(f"       ^ {t.get('name','?')}")
dr.displacement_adjustments = _da
