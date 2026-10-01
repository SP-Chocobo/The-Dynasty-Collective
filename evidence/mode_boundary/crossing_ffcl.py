"""#274 follow-up: does the TE account survive the league built to break it?

#274 found the global crossing rule is a tight-end detector: QB and WR fall below replacement
around pick 55-100 and the board keeps recommending them in balanced mode for another two
hundred picks, because TE's VOR rebounds instead of decaying and the rule waits for it.

EVERY ARM THAT FOUND THAT IS 1QB, PPR, te_premium=False, WITH A DEDICATED TE SLOT. TE is
exactly the position a TE premium or a missing TE slot changes most, so the account is
untested where it matters most. FFCL Group A is both at once -- 0.5 TE premium AND no dedicated
TE slot, so a tight end is a flex body priced with a bonus -- plus superflex and 3RR. If TE
still never crosses here, the account generalises; if it crosses, #274 is scoped to
TE-slot leagues and says so.

THIS ARM IS NOT A REPLAY. #274 reused pick sequences depth_battery.json already held; no such
draft exists for FFCL Group A, so this one is simulated here and then probed the same way. The
12-team dedicated-TE-slot arm from #274 is the control and is NOT re-run -- it is read back out
of crossing_mechanism.json, so the comparison is against the recorded number rather than a
fresh draft that could differ for unrelated reasons.

Run from the repo root. NEVER cd first -- DataMerger resolves baselines against cwd.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/mode_boundary/crossing_ffcl.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_simulation as ds
import draft_strategy as dstrat
import run_draft_battery as rdb
from crossing_mechanism import probe_board          # one home for the reading (#126)

CAPTURE = Path("data/league_captures/ffcl_group_a.json")
CONTROL = Path("evidence/mode_boundary/crossing_mechanism.json")
OUT = Path("evidence/mode_boundary/crossing_ffcl.json")
STRIDE = 5


def ffcl_league(base_scoring: dict) -> dict:
    """The captured rulebook as a Sleeper-shaped league.

    Scoring is the capture's own 42 observed values laid OVER the battery's base settings, not
    instead of them: the capture records what the owner could read off five screenshots, and a
    key it does not mention is a key Sleeper is running at its default, not a key set to zero.
    Dropping the base would silently rescore every position (#213: a ONE-KEY rulebook).
    """
    cap = json.loads(CAPTURE.read_text())
    scoring = dict(base_scoring)
    for key, entry in cap["scoring_settings_observed"].items():
        scoring[key] = entry["value"]
    return {
        "roster_positions": list(cap["roster_positions"]),
        "scoring_settings": scoring,
        "total_rosters": cap["total_rosters"],
        "settings": {"type": 0},                     # redraft, per the capture
    }, cap


def main() -> int:
    t0 = time.time()
    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    base = rdb.scoring_settings_from_capture()
    league, cap = ffcl_league(base)

    teams = league["total_rosters"]
    draftable = [s for s in league["roster_positions"] if s not in ("BN", "IR")]
    bench = league["roster_positions"].count("BN")
    rounds = len(draftable) + bench
    print(f"universe {prov['players_in_pool']}  season {len(season)}")
    print(f"FFCL Group A: {teams} teams, {len(draftable)} starters + {bench} bench "
          f"= {rounds} rounds = {teams * rounds} picks")
    print(f"  roster: {league['roster_positions']}")
    print(f"  rec={league['scoring_settings'].get('rec')}  "
          f"bonus_rec_te={league['scoring_settings'].get('bonus_rec_te')}  "
          f"dedicated TE slot: {'TE' in league['roster_positions']}", flush=True)

    merger.set_league_format(db.league_format_hint(league))          # NEVER SKIP
    roster_ids = [str(i) for i in range(1, teams + 1)]
    order = dstrat.generate_pick_order(roster_ids, rounds, "3rr")    # the league's real type
    print(f"\nsimulating under the crossing rule ({len(order)} picks)...", flush=True)
    traj = ds.simulate_full_draft(
        merger, players_db, league, order, config_label="FFCL_GROUP_A",
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
        upside_rule=dr.UPSIDE_RULE_CROSSING)

    engine_fire = next(({"round": p.round, "pick_no": p.pick_no} for p in traj.picks
                        if p.chosen_growth_signal is not None), None)
    print(f"engine's own detector (growth_signal): {engine_fire or 'NEVER'}", flush=True)

    picks = [{"player_id": str(p.chosen_player_id), "roster_id": str(p.roster_id)}
             for p in sorted(traj.picks, key=lambda p: p.pick_no)]

    samples = []
    for n in range(0, len(picks) + 1, STRIDE):
        prefix = picks[:n]
        rows = dr.compute_draft_board(
            merger, players_db, prefix, "1", league,
            sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
            upside_rule=dr.UPSIDE_RULE_CROSSING)
        by_pos = probe_board(rows, league, teams, prefix, players_db)
        any_meas = any(s["measurable"] for s in by_pos.values())
        samples.append({"after_picks": n, "by_pos": by_pos, "any_measurable": any_meas,
                        "would_fire": bool(any_meas and not any(s["positive"] for s in by_pos.values()))})
        if n % 40 == 0:
            print("   pick %4d  " % n + "  ".join(
                f"{p}:{'--' if s['top'] is None else format(s['top'], '.1f')}"
                for p, s in sorted(by_pos.items())), flush=True)

    first_fire = next((s["after_picks"] for s in samples if s["would_fire"]), None)
    per_pos = {}
    for pos in sorted({p for s in samples for p in s["by_pos"]}):
        per_pos[pos] = next((s["after_picks"] for s in samples
                             if pos in s["by_pos"] and s["by_pos"][pos]["positive"] is False), None)

    control = json.loads(CONTROL.read_text())["arms"]["12T_ppr_BN18"]
    report = {
        "league": cap["league"], "teams": teams, "rounds": rounds, "total_picks": len(picks),
        "draft_type": "3rr", "te_premium": league["scoring_settings"].get("bonus_rec_te"),
        "dedicated_te_slot": "TE" in league["roster_positions"],
        "engine_detector_fire": engine_fire,
        "reconstructed_first_fire": first_fire,
        "per_position_first_cross": per_pos,
        "control_12T_ppr_BN18": {
            "per_position_first_cross": control["per_position_first_cross"],
            "reconstructed_first_fire": control["reconstructed_first_fire"]},
        "samples": samples,
    }
    OUT.write_text(json.dumps(report, indent=1))

    rec = engine_fire["pick_no"] if engine_fire else None
    ok = ("ok (both NEVER)" if rec is None and first_fire is None
          else "ok (within stride)" if None not in (rec, first_fire) and abs(rec - first_fire) <= STRIDE
          else f"MISMATCH -- engine {rec}, probe {first_fire}")
    print(f"\nSELF-CHECK engine={rec} probe={first_fire}  {ok}")
    print(f"FFCL per-position first cross : {per_pos}  global {first_fire or 'NEVER'}")
    print(f"12T control (dedicated TE)    : {control['per_position_first_cross']}  "
          f"global {control['reconstructed_first_fire'] or 'NEVER'}")
    print(f"\nwrote {OUT}  ({time.time()-t0:.1f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
