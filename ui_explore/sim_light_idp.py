"""LIGHT_IDP has no recorded VDS sequence, and it is the ONE format that tests the
compound-vs-split IDP rule (it rosters IDP_FLEX, not named DL/LB/DB). So it gets a real
simulated draft rather than a replay of a sequence drafted under different demand -- replaying
HEAVY_IDP's sequence here would be a board state that never happened.

Writes only the pick sequence; capture_fixture.py turns it into states, so the capture logic
keeps one home."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path.cwd()))
import data_merger as dm, draft_room as dr, draft_battery as db, draft_strategy as ds
import draft_simulation as dsim, run_draft_battery as rdb

OUT = pathlib.Path("ui_explore/_sim_sequences.json")
players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture(); scoring = rdb.scoring_settings_from_capture()
arm = next(a for a in db.league_matrix(scoring) if a["label"] == "LIGHT_IDP")
league, teams, rounds = arm["league"], arm["teams"], arm["rounds"]
merger = dm.DataMerger(); merger.set_league_format(db.league_format_hint(league))
order = ds.generate_pick_order([str(i) for i in range(1, teams+1)], rounds, "snake")
print(f"simulating LIGHT_IDP: {teams}T x {rounds}r = {len(order)} picks", flush=True)
print(f"  slots: {' '.join(league.get('roster_positions', []))}", flush=True)

traj = dsim.simulate_full_draft(merger, players_db, league, order, mode="auto",
    sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
    config_label="LIGHT_IDP_uifixture")

picks = getattr(traj, "picks", traj)
seq = [{"chosen_player_id": getattr(p, "chosen_player_id", None) or
        (p.get("chosen_player_id") if isinstance(p, dict) else None)} for p in picks]
assert sum(1 for p in seq if p["chosen_player_id"]) > len(order) * 0.9, "sequence came back mostly empty"
pos = {}
for p in seq:
    i = players_db.get(str(p["chosen_player_id"])) or {}
    pos[i.get("position", "?")] = pos.get(i.get("position", "?"), 0) + 1
print(f"  drafted by position: {dict(sorted(pos.items(), key=lambda x: -x[1]))}", flush=True)

prev = json.loads(OUT.read_text()) if OUT.exists() else {}
prev["LIGHT_IDP"] = seq
OUT.write_text(json.dumps(prev))
print(f"wrote {OUT} with {len(seq)} picks", flush=True)
