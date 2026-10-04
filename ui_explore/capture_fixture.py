"""Board states across FIVE formats, so a design can be judged against the rosters it will meet.

Replays recorded VDS pick sequences -- no draft simulation -- so each format costs seconds.
Fixture discipline is the engine-measurement skill's: repo root, build_players_db_from_capture,
season projections on SLEEPER_BASIS_SEASON_SUM, set_league_format PER FORMAT, pick records
carrying {pick_no, round, roster_id, player_id} because mode="auto" reads `round`, and turns
chosen on the gap AHEAD."""
import json, pathlib, dataclasses, sys
sys.path.insert(0, str(pathlib.Path.cwd()))  # script lives in ui_explore/; engine is at root
import data_merger as dm, draft_room as dr, draft_battery as db, draft_strategy as ds
import pick_synthesis as ps, run_draft_battery as rdb

OUT = pathlib.Path("ui_explore/fixture.json")
VDS = pathlib.Path("evidence/batteries/VDS_2026-10-01_varied_drafting_strategy_dd4ade7.json")
WANT = ["12T_ppr", "12T_ppr_SF", "HEAVY_IDP", "12T_ppr_K_DEF", "4WR_TE_PREMIUM"]

players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture(); scoring = rdb.scoring_settings_from_capture()
arms = {a["label"]: a for a in db.league_matrix(scoring)}
vds = json.loads(VDS.read_text())
seqs = {(r.get("format"), r.get("strategy")): r.get("pick_sequence")
        for r in vds["results"] if r.get("pick_sequence")}
pid_of = lambda p: p.get("chosen_player_id") if isinstance(p, dict) else p

def nm(pid):
    i = players_db.get(str(pid)) or {}
    return {"name": " ".join(x for x in (i.get("first_name"), i.get("last_name")) if x) or f"#{pid}",
            "pos": i.get("position") or "?", "team": i.get("team") or ""}

FORCES = {"cliff_protection":"cliff","block_opportunity":"block","pure_value":"pure","near_tie_with_leader":"tie"}
KEEP = ("player_id","name","position","team","bpa","bpa_source","confidence","universal_value",
 "need_bonus","team_acquisition_value","survival_probability","intervening_picks","opportunity_cost",
 "expected_value_of_waiting","denial_value","denial_basis","denial_team","rival_premium",
 "rival_premium_take_probability","positional_forfeit","position_expected_taken","position_best_now",
 "position_next_turn_value","positional_cliff","position_run_detected","pick_necessity",
 "necessity_label","projected_points","depth_exposure","depth_basis","time_horizon_adj","risk_adj",
 "risk_basis","injury_status","availability_basis","displacement_adj","displacement_basis",
 "waiting_cost","horizon_floor","horizon_sensitivity","replacement_basis","absence_kind",
 "fills_required_slot","cannot_be_fielded","growth_signal","consensus_rank","consensus_tier")

out, failures = {}, []
for label in WANT:
    arm = arms.get(label); seq = seqs.get((label, "sharp_auto"))
    if not arm or not seq:
        failures.append(f"{label}: {'no arm' if not arm else 'no sharp_auto sequence'}"); continue
    league, teams, rounds = arm["league"], arm["teams"], arm["rounds"]
    merger = dm.DataMerger()                       # fresh per format -- format is FILE SELECTION
    merger.set_league_format(db.league_format_hint(league))
    seats = [str(i) for i in range(1, teams + 1)]
    order = ds.generate_pick_order(seats, rounds, "snake")
    ME = "6"
    # turns where ME is on the clock AND real picks intervene before my NEXT turn (gap AHEAD)
    mine = [i for i in range(min(len(seq), len(order))) if order[i] == ME]
    usable = [i for n, i in enumerate(mine)
              if n + 1 < len(mine) and mine[n + 1] - i > 1]
    if len(usable) < 3:
        failures.append(f"{label}: only {len(usable)} usable turns"); continue
    picks_idx = [usable[0], usable[len(usable) // 3], usable[int(len(usable) * 0.78)]]

    rail = []
    for i in range(teams * rounds):
        e = {"no": i+1, "rnd": i//teams+1, "inr": i%teams+1, "seat": order[i], "mine": order[i] == ME}
        if i < len(seq) and pid_of(seq[i]): e.update(nm(pid_of(seq[i])))
        rail.append(e)

    states = {}
    for idx, key in zip(picks_idx, ("early", "mid", "late")):
        picks = [{"pick_no": i+1, "round": i//teams+1, "roster_id": order[i], "player_id": pid_of(seq[i])}
                 for i in range(idx)]
        if picks:
            missing = {"pick_no","round","roster_id","player_id"} - set(picks[0])
            assert not missing, f"pick records missing {missing}; mode='auto' reads `round`"
        snap = ps.build_snapshot(merger, players_db, picks, order, idx, ME, league,
            pick_label=f"{idx//teams+1}.{idx%teams+1:02d}", mode="auto",
            sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        cs = [dataclasses.asdict(c) for c in snap.candidates]
        cs.sort(key=lambda c: -(c["team_acquisition_value"] or -1e9))
        rows = []
        for r, c in enumerate(cs[:24]):
            row = {k: c.get(k) for k in KEEP}; row["rank"] = r+1
            row["forces"] = [v for k, v in FORCES.items() if c.get(k)]
            rows.append(row)
        states[key] = {"pick": snap.pick_label, "index": idx, "round": snap.round,
          "seat": snap.my_roster_id, "teams": teams, "rounds": rounds,
          "regime": snap.decision_regime, "pool": snap.pool_scope,
          "consumed": snap.picks_consumed, "intervening": cs[0]["intervening_picks"],
          "fresh": snap.data_freshest_date, "stamp": snap.players_db_stamp,
          "slots": league.get("roster_positions", []),
          "slot_share_basis": dr.slot_share_basis(None, teams),
          "demand": {p: round(v, 4) for p, v in
                     dr.starter_slot_counts(league.get("roster_positions", [])).items() if v},
          "ambiguities": [list(a) for a in (snap.config_ambiguities or ())],
          "withheld": sorted(ps.withheld_fields()),
          "myPicks": [x for x in rail[:idx] if x["mine"] and x.get("name")],
          "candidates": rows}
    out[label] = {"slots": league.get("roster_positions", []), "teams": teams,
                  "rounds": rounds, "rail": rail, "states": states}

    # VERIFY before anything downstream trusts it
    slot_pos = {s for s in league.get("roster_positions", []) if s in dr.FANTASY_POSITIONS}
    for key, st in out[label]["states"].items():
        seen = sorted({c["position"] for c in st["candidates"]})
        print(f"  {label:18s} {key:5s} {st['pick']:>6s} cands={len(st['candidates']):2d} "
              f"roster={len(st['myPicks']):2d} positions={seen}")
    miss = slot_pos - {c["position"] for st in out[label]["states"].values() for c in st["candidates"]}
    if miss: print(f"     NOTE {label}: slotted positions never on a board: {sorted(miss)}")

OUT.write_text(json.dumps(out, default=str))
print(f"\nwrote {OUT}  {OUT.stat().st_size/1024:.0f}KB  formats={list(out)}")
if failures: print("SKIPPED:"); [print("   ", f) for f in failures]
