"""A full 12x26 startup on Fourth and Forever's REAL rulebook, all twelve chairs.

Prices the way production does (#201 real universe, #204 season sums under THIS league's
scoring), and records the composition drift round by round -- the question is not what the
opening board looks like but how the board's own composition changes as the pool drains.
Run from the repo root.
"""
import json, collections, sys, time, pathlib
import data_merger as dm, draft_room as dr, draft_battery as db
import draft_simulation as ds, draft_strategy as dstrat
import run_draft_battery as rdb

OUT = pathlib.Path("evidence/roster_shape/ff_rulebook")
CAP = json.load(open("data/league_captures/fourth_and_forever.json"))
SCORING = {k: v["value"] for k, v in CAP["scoring_settings_observed"].items()}
LEAGUE = {"roster_positions": CAP["roster_positions"], "scoring_settings": SCORING,
          "total_rosters": 12, "settings": {"type": 2}}

def main():
    t0 = time.time()
    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()
    merger.set_league_format(db.league_format_hint(LEAGUE))
    season = rdb.season_projections_from_capture()
    print("universe:", prov["players_in_pool"], "season projections:", len(season), flush=True)

    roster_ids = [str(i) for i in range(1, 13)]
    order = dstrat.generate_pick_order(roster_ids, 26, "3rr")
    print("picks:", len(order), flush=True)

    traj = ds.simulate_full_draft(
        merger, players_db, LEAGUE, order, config_label="FOURTH_AND_FOREVER_3RR",
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)

    # SAVE THE RAW RESULT BEFORE ANY ANALYSIS (#215). The first run of this script
    # completed all 312 picks and then threw in the reporting block, losing ~15 minutes
    # of engine time to a one-line attribute error. Nothing is derived above this line.
    picks = []
    for i, r in enumerate(traj.picks):
        pid = str(r.chosen_player_id)
        info = players_db.get(pid) or {}
        picks.append({"overall": i + 1, "round": i // 12 + 1, "roster_id": str(r.roster_id),
                      "player_id": pid, "position": info.get("position"),
                      "name": info.get("full_name")})
    json.dump({"league": "Fourth and Forever", "picks": picks,
               "universe": prov, "elapsed_s": round(time.time() - t0, 1)},
              open(OUT / "ff_draft_3rr.json", "w"), indent=1)
    print("RAW SAVED:", len(picks), "picks", flush=True)

    c = collections.Counter(p["position"] for p in picks)
    N = sum(c.values())
    print(f"\nCOMPLETED {N} picks in {time.time()-t0:.0f}s")
    print("overall:", {p: f"{c[p]} ({c[p]/N:.1%})" for p in ("QB","RB","WR","TE") if c[p]})
    print("\nby quarter of the draft (this is the drift):")
    for lo, hi in ((1,78),(79,156),(157,234),(235,312)):
        s = [p for p in picks if lo <= p["overall"] <= hi]
        cc = collections.Counter(p["position"] for p in s); n = sum(cc.values())
        if n: print(f"  picks {lo:3}-{hi:3}: " + "  ".join(f"{p} {cc[p]/n:5.1%}" for p in ("QB","RB","WR","TE")))
    print("\nper seat:")
    for rid in roster_ids:
        s = [p for p in picks if p["roster_id"] == rid]
        cc = collections.Counter(p["position"] for p in s)
        wr, rb = cc.get("WR",0), cc.get("RB",0)
        print(f"  seat {rid:>2}: QB {cc.get('QB',0):2} RB {rb:2} WR {wr:2} TE {cc.get('TE',0):2}  n={len(s):2}  WR:RB {wr/rb if rb else float('inf'):.2f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
