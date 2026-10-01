"""Pre-registered in PREREG_narrow_upside_ablation.md. Run from the REPO ROOT with PYTHONPATH=.

THE NARROW ARM: upside mode keeping displacement_adj and NOTHING else. need_bonus,
eligibility_bonus and depth_exposure stay zeroed; bpa and the growth term stay.

INSTRUMENT. dr.compute_draft_board is wrapped (pick_synthesis reaches it through the module
attribute, so the whole draft picks this up). Each call invokes the REAL function twice with
identical arguments -- once as production would, once with mode="balanced" -- and adds the
BALANCED board's own per-row displacement_adj to the UPSIDE board's final_score. Every quantity
is production-computed; nothing is reconstructed, and multi-eligible rows (#172) carry the real
per-eligibility-set solve score_row does for them.

A board that is already balanced is passed through UNTOUCHED -- adding the term there would
double-count it. That makes rounds 1-14 the control.

NO ENGINE SOURCE IS MODIFIED. The patch is in-process and reverted in a finally block.
"""
import json, collections, time, pathlib
import data_merger as dm, draft_room as dr, draft_battery as db
import draft_simulation as ds, draft_strategy as dstrat
import run_draft_battery as rdb

OUT = pathlib.Path("evidence/roster_shape/ff_rulebook")
CAP = json.load(open("data/league_captures/fourth_and_forever.json"))
SCORING = {k: v["value"] for k, v in CAP["scoring_settings_observed"].items()}
LEAGUE = {"roster_positions": CAP["roster_positions"], "scoring_settings": SCORING,
          "total_rosters": 12, "settings": {"type": 2}}

_real = dr.compute_draft_board
STATS = collections.Counter()


def _patched(*args, **kwargs):
    rows = _real(*args, **kwargs)
    if not rows:
        return rows
    # Detect the branch from the ROWS, not from the mode kwarg -- "auto" resolves internally.
    if rows[0].get("mode") != "upside":
        STATS["passthrough_balanced"] += 1
        return rows
    STATS["adjusted_upside"] += 1
    bal = _real(*args, **{**kwargs, "mode": "balanced"})
    by_id = {str(r["player_id"]): r for r in bal}
    if set(by_id) != {str(r["player_id"]) for r in rows}:
        raise RuntimeError("FIXTURE ERROR: the two boards do not cover the same players")
    for r in rows:
        b = by_id[str(r["player_id"])]
        adj, fs = b.get("displacement_adj"), r.get("final_score")
        if fs is None:
            STATS["skipped_unpriced"] += 1
            continue
        if adj is None:                      # absence is not zero (#61)
            STATS["skipped_absent_adj"] += 1
            continue
        r["final_score"] = round(fs + float(adj), 2)
        r["universal_value"] = r["final_score"]   # upside's own layer identity
        STATS["rows_adjusted"] += 1
    # production's own upside sort key
    rows.sort(key=lambda r: (0 if r.get("fills_required_slot") else 1,
                             r.get("final_score") is None,
                             -(r["final_score"] if r.get("final_score") is not None else 0.0),
                             str(r.get("player_id"))))
    return rows


def main():
    t0 = time.time()
    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()
    merger.set_league_format(db.league_format_hint(LEAGUE))
    season = rdb.season_projections_from_capture()
    print("universe:", prov["players_in_pool"], "season:", len(season), flush=True)

    roster_ids = [str(i) for i in range(1, 13)]
    order = dstrat.generate_pick_order(roster_ids, 26, "snake")
    dr.compute_draft_board = _patched
    try:
        traj = ds.simulate_full_draft(
            merger, players_db, LEAGUE, order, config_label="FF_NARROW_UPSIDE_DISPLACEMENT",
            sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    finally:
        dr.compute_draft_board = _real

    # SAVE RAW BEFORE DERIVING ANYTHING (#215).
    picks = []
    for i, r in enumerate(traj.picks):
        pid = str(r.chosen_player_id)
        info = players_db.get(pid) or {}
        picks.append({"overall": i + 1, "round": i // 12 + 1, "roster_id": str(r.roster_id),
                      "player_id": pid, "position": info.get("position"),
                      "name": info.get("full_name")})
    json.dump({"league": "Fourth and Forever", "arm": "narrow_upside_displacement",
               "picks": picks, "universe": prov, "patch_stats": dict(STATS),
               "elapsed_s": round(time.time() - t0, 1)},
              open(OUT / "ff_draft_narrow.json", "w"), indent=1)
    print("RAW SAVED:", len(picks), "picks", dict(STATS), flush=True)
    print(f"COMPLETED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
