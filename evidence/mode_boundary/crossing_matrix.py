"""#274 follow-up 2: WHICH axis moves the holdout? FFCL changed five things at once.

#274's scope correction says the holdout -- the position that never falls below its replacement
level, and which the global crossing rule therefore waits for -- is set by ROSTER SHAPE. The
evidence was two leagues: a 1QB/TE-slot control (holdout TE) and FFCL Group A (holdout QB+RB,
TE crossing first).

THAT COMPARISON IS CONFOUNDED, AND I SHOULD HAVE SAID SO LOUDER. FFCL differs from the control
on FIVE axes simultaneously -- superflex, no dedicated TE slot, a 0.5 TE premium, 3RR, and
redraft. "Roster shape starves a position of demand relative to supply" is a mechanism that
predicts the inversion, but the measurement alone cannot say WHICH of the five did it, and the
correction stated the mechanism with more confidence than a two-point comparison earns.

This decomposes it on the battery's own matrix, one axis at a time against a shared control:

  12T_ppr              1QB, TE slot, no TEP        -- CONTROL
  12T_ppr_SF           superflex ALONE (TE slot kept, no TEP)
  12T_ppr_TEP_dynasty  TE premium ALONE (1QB, TE slot kept)
  4WR_TE_PREMIUM       TE premium + a fourth WR slot
  LIGHT_IDP            IDP added
  HEAVY_IDP            IDP added, deeper

IDP is also the open item #274 named: every league measured so far is offence-only, and three
defensive positions are three more candidate holdouts.

PREDICTIONS, pre-registered before the run, so a confirmation is worth something:
  1. 12T_ppr_SF's holdout is QB (superflex doubles QB starter demand -> deeper replacement).
     If SF alone flips the holdout to QB, superflex is sufficient and the no-TE-slot axis is
     not needed to explain FFCL.
  2. 12T_ppr_TEP_dynasty keeps TE as holdout, possibly harder (a premium raises every TE's
     points without adding a TE slot).
  3. The IDP arms have an IDP holdout, because #210 records that Sleeper supplies IDP without
     stat lines -- so IDP rows may be UNMEASURABLE rather than above replacement. If so the
     "--" (nothing measurable) state, not a crossing, is what those arms show, and that is a
     supply fact rather than a demand one. Recorded now so it cannot be retrofitted either way.

Each arm is simulated under the CROSSING rule and then probed the same way #274 probed the
replayed drafts -- probe_board is imported, never restated (#126: one home for the reading).

Run from the repo root. NEVER cd first -- DataMerger resolves baselines against cwd.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/mode_boundary/crossing_matrix.py
Resumes from its own output; re-running after a kill picks up at the first unfinished arm.
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
from crossing_mechanism import probe_board

OUT = Path("evidence/mode_boundary/crossing_matrix.json")
STRIDE = 5
ARMS = ("12T_ppr", "12T_ppr_SF", "12T_ppr_TEP_dynasty", "4WR_TE_PREMIUM",
        "LIGHT_IDP", "HEAVY_IDP", "12T_ppr_NO_TE_SLOT")


#: #277 named its own weakness: the TE-slot attribution was reached by ELIMINATION across five
#: axes, never by removing the slot and watching. This is that direct test, and it is the only
#: arm here the battery matrix cannot supply.
#:
#: THE SWAP IS TE -> FLEX, NOT TE -> NOTHING. Deleting the slot would change the starter count
#: (8 -> 7) and therefore the round count, the pick total, and every other position's share of
#: the draft -- four axes moving to test one, which is the confound #277 was written to escape.
#: Replacing TE with a FLEX holds slot count, round count and pick total EXACTLY fixed and moves
#: only where tight-end demand lives: from a dedicated slot into the shared pool. That is also
#: precisely what FFCL Group A does (FLEX FLEX WRRB_FLEX SUPER_FLEX, no TE), so the arm is the
#: real league's distinguishing feature in isolation rather than an invented shape.
#:
#: PREDICTION, pre-registered: if the dedicated TE slot is the operative axis, TE STOPS being a
#: holdout here and crosses at a finite pick, while the control (identical but for that one
#: slot) keeps TE as holdout forever. If TE remains a holdout, the TE slot is NOT sufficient,
#: #277's conclusion is wrong, and whatever inverts FFCL is still unidentified.
CONSTRUCTED = {
    "12T_ppr_NO_TE_SLOT": {
        "from": "12T_ppr",
        "swap": ("TE", "FLEX"),
    },
}


def constructed_league(spec: dict, matrix: dict) -> tuple[dict, int, int]:
    """Build the arm by EDITING the control's own league, so nothing else can drift.

    Derived from the matrix entry rather than restated (#126): if build_mock_league's starters
    change, this arm changes with them instead of silently testing a stale shape.
    """
    base_arm = matrix[spec["from"]]
    league = json.loads(json.dumps(base_arm["league"]))          # deep copy, no shared state
    old_slot, new_slot = spec["swap"]
    rp = league["roster_positions"]
    assert old_slot in rp, f"{spec['from']} has no {old_slot} slot to swap"
    rp[rp.index(old_slot)] = new_slot                            # ONE slot, first occurrence
    league["roster_positions"] = rp
    return league, base_arm["teams"], base_arm["rounds"]


def main() -> int:
    t0 = time.time()
    report = json.loads(OUT.read_text()) if OUT.exists() else {"arms": {}, "stride": STRIDE}

    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    base = rdb.scoring_settings_from_capture()
    matrix = {e["label"]: e for e in db.league_matrix(base)}
    print(f"universe {prov['players_in_pool']}  season {len(season)}", flush=True)

    for label in ARMS:
        if label in report["arms"]:
            print(f"[skip] {label}", flush=True)
            continue
        if label in CONSTRUCTED:
            league, teams, rounds = constructed_league(CONSTRUCTED[label], matrix)
        else:
            arm = matrix[label]
            league, teams, rounds = arm["league"], arm["teams"], arm["rounds"]
        rp = league["roster_positions"]
        t1 = time.time()
        print(f"\n== {label}  teams={teams} rounds={rounds} picks={teams*rounds}  "
              f"SF={rp.count('SUPER_FLEX')} TEslot={int('TE' in rp)} "
              f"tep={league['scoring_settings'].get('bonus_rec_te', 0)}", flush=True)

        merger.set_league_format(db.league_format_hint(league))          # NEVER SKIP
        order = dstrat.generate_pick_order([str(i) for i in range(1, teams + 1)],
                                           rounds, "snake")
        traj = ds.simulate_full_draft(
            merger, players_db, league, order, config_label=label,
            sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
            upside_rule=dr.UPSIDE_RULE_CROSSING)
        engine_fire = next(({"round": p.round, "pick_no": p.pick_no} for p in traj.picks
                            if p.chosen_growth_signal is not None), None)
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
            samples.append({
                "after_picks": n, "by_pos": by_pos, "any_measurable": any_meas,
                "would_fire": bool(any_meas and not any(s["positive"] for s in by_pos.values()))})

        first_fire = next((s["after_picks"] for s in samples if s["would_fire"]), None)
        per_pos, never_measurable = {}, {}
        for pos in sorted({p for s in samples for p in s["by_pos"]}):
            per_pos[pos] = next((s["after_picks"] for s in samples
                                 if pos in s["by_pos"] and s["by_pos"][pos]["positive"] is False),
                                None)
            # #210: a position can be absent from the crossing not because it stays above
            # replacement but because it was NEVER PRICEABLE. Those are different facts and the
            # absence contract forbids reporting them as one.
            never_measurable[pos] = not any(
                s["by_pos"].get(pos, {}).get("measurable") for s in samples)

        rec = engine_fire["pick_no"] if engine_fire else None
        ok = ("ok (both NEVER)" if rec is None and first_fire is None
              else "ok (within stride)"
              if None not in (rec, first_fire) and abs(rec - first_fire) <= STRIDE
              else f"MISMATCH -- engine {rec}, probe {first_fire}")

        report["arms"][label] = {
            "teams": teams, "rounds": rounds, "total_picks": len(picks),
            "superflex": rp.count("SUPER_FLEX"), "te_slot": "TE" in rp,
            "te_premium": league["scoring_settings"].get("bonus_rec_te", 0),
            "engine_detector_fire": engine_fire, "reconstructed_first_fire": first_fire,
            "selfcheck": ok,
            "per_position_first_cross": per_pos,
            "never_measurable": never_measurable,
            "samples": samples,
        }
        OUT.write_text(json.dumps(report, indent=1))
        holdouts = [p for p, v in per_pos.items() if v is None and not never_measurable[p]]
        unpriced = [p for p, v in never_measurable.items() if v]
        print(f"   cross {per_pos}", flush=True)
        print(f"   HOLDOUT(S) {holdouts or '(none)'}   never-priceable {unpriced or '(none)'}",
              flush=True)
        print(f"   global {first_fire or 'NEVER'}  selfcheck {ok}  ({time.time()-t1:.1f}s)",
              flush=True)

    print("\n=== HOLDOUT BY AXIS ===", flush=True)
    for label, a in report["arms"].items():
        pp, nm = a["per_position_first_cross"], a["never_measurable"]
        holds = [p for p, v in pp.items() if v is None and not nm.get(p)]
        print(f"  {label:<22} SF={a['superflex']} TEslot={int(a['te_slot'])} "
              f"tep={a['te_premium']:<4} holdout={holds or ['(none)']} "
              f"global={a['reconstructed_first_fire'] or 'NEVER'}", flush=True)
    print(f"\nwrote {OUT}  ({time.time()-t0:.1f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
