"""Does the B1 ladder's non-monotonicity track the LEVEL'S BASIS rather than bodies held?

The published B1 ladder charged -51.7 at 2 TEs held, rose to -120.4 at 6, then RETURNED to
-51.7 at 7 and 8. I called that "a term whose every input has changed by a factor of five
cannot legitimately return the same number to the hundredth." Each rung sits at a DIFFERENT
PICK, so each may sit in a different replacement-level regime -- which the earlier probe
never recorded.

This re-runs the identical rung construction and additionally captures, per rung and from
PRODUCTION (never reconstructed): the TE level the board actually used, whether that level
came from the live call or the pre-draft anchor fill, and the displaced value the optimizer
returned. Run from the repo root with PYTHONPATH=.
"""
import json
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

CAP = json.load(open("data/league_captures/fourth_and_forever.json"))
RP = CAP["roster_positions"]
LEAGUE = {"roster_positions": RP,
          "scoring_settings": {k: v["value"] for k, v in CAP["scoring_settings_observed"].items()},
          "total_rosters": 12, "settings": {"type": 2}}
D = json.load(open("evidence/roster_shape/ff_rulebook/ff_draft.json"))["picks"]
merger = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
merger.set_league_format(db.league_format_hint(LEAGUE))
season = rdb.season_projections_from_capture()
def f(x):
    try: return float(x)
    except: return None

# ---- instruments: tagged by ARGUMENTS, and the fill set read from production's own return
STATE = {}
_rl = dr.replacement_levels
def rl_spy(pool, value_col, roster_positions, num_teams, remaining_demand=None,
           startable_floors=None, truncated_out=None, flex_occupancy=None):
    out = _rl(pool, value_col, roster_positions, num_teams, remaining_demand,
              startable_floors, truncated_out, flex_occupancy)
    if remaining_demand is not None and value_col == "_points":
        STATE["live_TE"] = out.get("TE")
        STATE["demand_TE"] = remaining_demand.get("TE")
    return out
_fill = dr._fill_omitted_from_anchor
def fill_spy(levels, present, floors, build_anchor):
    got = _fill(levels, present, floors, build_anchor)
    STATE["anchored"] = ("TE" in got)
    return got
_da = dr.displacement_adjustments
def da_spy(roster_players, roster_positions, levels, unpriced_eligible=None):
    STATE["level_TE_used"] = levels.get("TE")     # what the term ACTUALLY consumed
    out = _da(roster_players, roster_positions, levels, unpriced_eligible)
    # PRODUCTION'S OWN displaced and basis, not inverted from the adjustment (doctrine 1).
    STATE["disp_TE"] = (out.get("TE") or {}).get("displaced")
    STATE["disp_basis_TE"] = (out.get("TE") or {}).get("basis")
    return out
dr.replacement_levels = rl_spy
dr._fill_omitted_from_anchor = fill_spy
dr.displacement_adjustments = da_spy

seen = {}
for i, p in enumerate(D):
    prior = D[:i]; me = p["roster_id"]
    n_te = sum(1 for q in prior if q["roster_id"] == me and q["position"] == "TE")
    if n_te not in seen and 2 <= n_te <= 8 and p["position"] == "TE":
        seen[n_te] = (i + 1, me, prior)

print("TE displacement_adj by bodies held -- WITH the level and its basis\n")
print(f"{'held':>5}{'pick':>6}{'seat':>5}{'disp_adj':>10}{'TE level used':>15}"
      f"{'basis':>16}{'live TE':>10}{'demand':>9}{'displaced (prod)':>18}{'disp basis':>34}")
for n in sorted(seen):
    AT, me, prior = seen[n]
    STATE.clear()
    rows = dr.compute_draft_board(merger, players_db,
        [{"player_id": q["player_id"], "roster_id": q["roster_id"]} for q in prior], me, LEAGUE,
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    rows = [r for r in rows if f(r.get("final_score")) is not None]
    rows.sort(key=lambda r: -f(r["final_score"]))
    te = [r for r in rows if r["position"] == "TE"]
    if not te: continue
    adj = f(te[0].get("displacement_adj")) or 0.0
    lvl = STATE.get("level_TE_used")
    basis = te[0].get("replacement_basis")
    live = STATE.get("live_TE")
    dem = STATE.get("demand_TE")
    disp = STATE.get("disp_TE")          # production's own value, read from its return
    print(f"{n:>5}{AT:>6}{me:>5}{adj:>10.2f}"
          f"{(f'{lvl:.2f}' if lvl is not None else 'none'):>15}{str(basis):>16}"
          f"{(f'{live:.2f}' if live is not None else 'omitted'):>10}"
          f"{(f'{dem:.2f}' if dem is not None else '--'):>9}"
          f"{(f'{disp:.2f}' if disp is not None else '--'):>18}"
          f"{str(STATE.get('disp_basis_TE')):>34}")
dr.replacement_levels = _rl; dr._fill_omitted_from_anchor = _fill
dr.displacement_adjustments = _da
