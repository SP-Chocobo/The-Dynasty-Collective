"""#50 RULING INPUT, the four questions -- live vs PRE-DRAFT anchor, at every pick.

    1. At each relevant pick, what is the LIVE level?
    2. What is the PREDRAFT anchor level?
    3. Which basis does production actually SELECT, and under what exact condition?
    4. What information changes when production crosses from live to anchor?

Method notes, both of them load-bearing.

OBSERVE PRODUCTION, NEVER RECONSTRUCT (#222 doctrine clause 1). Every number below is a
production return value captured at the call. Nothing is recomputed from board output rows.
Question 3 in particular is answered by spying on _fill_omitted_from_anchor -- production's
own selection decision, the SET it returns -- rather than by comparing numbers and guessing
which one the board used.

CALL IDENTITY FROM THE ARGUMENTS (#222 doctrine clause 2). replacement_levels runs up to
three times per board build. The tag is derived from remaining_demand/value_col, never from
call order, because the anchor is CACHED and therefore does not fire on every build.

Every pick is observed: 0..311 inclusive, one board each, ~0.5s warm. No sampling, so no
question about which picks were chosen. Run from the repo root with PYTHONPATH=.
"""
import json, time, sys
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

OUT = "evidence/roster_shape/ff_rulebook/phase2_crossing.json"
CAP = json.load(open("data/league_captures/fourth_and_forever.json"))
RP = CAP["roster_positions"]
SC = {k: v["value"] for k, v in CAP["scoring_settings_observed"].items()}
L = {"roster_positions": RP, "scoring_settings": SC, "total_rosters": 12, "settings": {"type": 2}}
D = json.load(open("evidence/roster_shape/ff_rulebook/ff_draft.json"))["picks"]

m = dm.DataMerger()
players_db, prov = rdb.build_players_db_from_capture()
m.set_league_format(db.league_format_hint(L))
season = rdb.season_projections_from_capture()
POS = ("QB", "RB", "WR", "TE")

# ---- instruments -------------------------------------------------------------------------
CALLS = []
_real_rl = dr.replacement_levels
def rl_spy(pool, value_col, roster_positions, num_teams, remaining_demand=None,
           startable_floors=None, truncated_out=None, flex_occupancy=None):
    out = _real_rl(pool, value_col, roster_positions, num_teams, remaining_demand,
                   startable_floors, truncated_out, flex_occupancy)
    # THE TAG IS DERIVED FROM THE ARGUMENTS. remaining_demand is None at exactly one call
    # site -- predraft_replacement_anchor (draft_room.py:2359) -- and that is what makes it
    # the anchor: no live draft state reaches it.
    if remaining_demand is None:
        tag = "ANCHOR(predraft, full pool)"
    elif value_col == "_points":
        tag = "LIVE(_points, remaining pool)"
    elif value_col == "trade_value":
        tag = "LIVE(trade_value, remaining pool)"
    else:
        tag = f"UNCLASSIFIED(col={value_col})"
    CALLS.append({"tag": tag, "col": value_col, "n_pool": int(len(pool)),
                  "demand": (dict(remaining_demand) if remaining_demand is not None else None),
                  "floors": (dict(startable_floors) if startable_floors else None),
                  "out": {k: float(v) for k, v in out.items()}})
    return out

FILLED = []
_real_fill = dr._fill_omitted_from_anchor
def fill_spy(levels, present_positions, startable_floors, build_anchor):
    before = set(levels)
    got = _real_fill(levels, present_positions, startable_floors, build_anchor)
    FILLED.append({"present": sorted(present_positions), "had_live": sorted(before),
                   "filled": sorted(got),
                   "floored": sorted((startable_floors or {}).keys())})
    return got

dr.replacement_levels = rl_spy
dr._fill_omitted_from_anchor = fill_spy

# The anchor as a production value, obtained by calling the production function directly.
# Tagged as such: this is the same cached object _fill_omitted_from_anchor receives.
FLOORS = ({"QB": dr.qb_startable_floor(m)} if "SUPER_FLEX" in RP else None)
ANCHOR = dr.predraft_replacement_anchor(
    m, players_db, set(POS), RP, 12, "_points",
    sleeper_projections=season, scoring_settings=SC,
    sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM, startable_floors=FLOORS)

rows_out = []
t0 = time.time()
for k in range(0, len(D)):
    CALLS.clear(); FILLED.clear()
    prior = [{"player_id": q["player_id"], "roster_id": q["roster_id"]} for q in D[:k]]
    rows = dr.compute_draft_board(m, players_db, prior, "12", L,
                                  sleeper_projections=season,
                                  sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    basis = {}
    for r in rows:
        basis.setdefault(r["position"], r.get("replacement_basis"))
    live = next((c for c in CALLS if c["tag"].startswith("LIVE(_points")), None)
    fill = FILLED[0] if FILLED else None
    rows_out.append({
        "board_after_picks": k,                 # the board the drafter at pick k+1 sees
        "tags": [c["tag"] for c in CALLS],
        "demand": (live["demand"] if live else None),
        "live": (live["out"] if live else None),
        "live_pool_n": (live["n_pool"] if live else None),
        "filled_from_anchor": (fill["filled"] if fill else None),
        "floored": (fill["floored"] if fill else None),
        "present": (fill["present"] if fill else None),
        "basis": {p: basis.get(p) for p in POS},
    })
    if k % 26 == 0:
        print(f"  ...board after {k} picks ({time.time()-t0:.0f}s)", flush=True)

dr.replacement_levels = _real_rl
dr._fill_omitted_from_anchor = _real_fill

# RAW FIRST, before a single derived number (#215).
json.dump({"anchor": ANCHOR, "floors": FLOORS, "universe": prov, "boards": rows_out},
          open(OUT, "w"), indent=1)
print(f"RAW SAVED: {len(rows_out)} boards -> {OUT}  ({time.time()-t0:.0f}s)", flush=True)
