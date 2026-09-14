"""#281. WHAT THE MODE RULE DOES TO THE ROSTERS -- the question #261 asked and nobody answered.

Everything measured so far -- #271, #274, #276, #277, #278 -- is about WHEN the crossing rule
fires. Not one of those entries says what the drafted teams look like afterwards. #261 put it in
as many words: "nobody has drafted with the rule in place." depth_battery DID draft all ten arms
under BOTH rules and recorded every pick; the comparison was simply never run.

NO NEW DRAFTS. This reads depth_battery.json's recorded picks. A fresh simulation would be a
DIFFERENT draft and could not answer "what did THESE two rules produce on the same league".

WHY NOT starter_value, WHICH THE BATTERY ALREADY COMPUTES. #211: summing `universal_value` over
the started subset is a CATEGORY ERROR -- universal_value is an asset LEVEL (what a player is
worth to own), not a rate a start realises, and 83.8% of a pool's values are negative, so a thin
roster is forced to start deep negatives and the number ranks POSITIONAL BREADTH rather than
quality. Using it here would produce a confident ranking of the wrong thing.

WHAT IS USED INSTEAD: season PROJECTED POINTS of the optimal legal lineup. That is what a season
actually pays, it is the harder of the two bases #205 reported (asset 68/68, points 1/68), and it
is immune to #211 because points are a rate on the same scale for every position.

ABSENCE IS COUNTED, NEVER ZEROED. A drafted player with no season projection is UNPRICED, not
worth 0.0 -- zeroing him would silently reward a rule for drafting unpriceable players. Unpriced
picks are excluded from the lineup pool and REPORTED per arm, so a result resting on a lopsided
unpriced count declares itself instead of hiding.

THE BUILT-IN CONTROL. 12T_ppr_BN6 is 14 rounds, so NEITHER rule fires (the round rule needs
round 15). Its two drafts must be pick-for-pick identical and its outcome delta must be exactly
0.00. If it is not, the instrument is measuring something other than the mode switch and says so
rather than letting the other nine arms stand.

Run from the repo root. NEVER cd first -- DataMerger resolves baselines against cwd.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/mode_boundary/mode_outcomes.py
"""
from __future__ import annotations

import json
from pathlib import Path

import draft_room as dr
import lineup_optimizer as lo
import player_universe as pu
import run_draft_battery as rdb

IN = Path("evidence/mode_boundary/depth_battery.json")
OUT = Path("evidence/mode_boundary/mode_outcomes.json")


def seat_lineups(per_seat: dict, league: dict, players_db: dict, season: dict) -> dict:
    """Per seat: optimal legal lineup by PROJECTED POINTS, plus how many picks were unpriced.

    POINTS ARE SCORED AGAINST THIS LEAGUE'S OWN RULEBOOK, not read off a field. `season` maps a
    player id to Sleeper's raw SEASON STAT LINE; there is no precomputed total in it. The first
    draft of this function did `season[pid].get("pts")`, got None for every pick in every arm,
    and reported a tidy +0.00 delta across all ten -- with the control self-check PASSING,
    because zero equals zero. That is the engine-measurement failure mode in its purest form: a
    plausible number about nothing, wearing a green tick.

    Scoring per league is also correct rather than merely convenient (#213): the same stat line
    is worth different points under different rulebooks, so a TE premium or a PPR setting has to
    reach the outcome through the same path production uses.
    """
    scoring = league.get("scoring_settings") or {}
    slots = lo.slots_from_roster_positions(league["roster_positions"])
    out = {}
    for rid, picks in per_seat.items():
        entries, unpriced = [], 0
        for e in picks:
            pid = str(e["pid"])
            stats = season.get(pid)
            pts = pu.score_projection(stats, scoring) if stats else None
            if pts is None:                       # UNPRICED -- excluded and counted, never 0.0
                unpriced += 1
                continue
            info = players_db.get(pid) or {}
            entries.append({"id": pid, "value": float(pts),
                            "eligible": set(pu.player_eligible_positions(info))})
        solved = lo.optimize_lineup(entries, slots)
        started = {a["player_id"] for a in solved["assignments"]}
        pick_no = {str(e["pid"]): e["pick_no"] for e in picks}
        out[rid] = {"starting_points": solved["total_value"],
                    "slots_filled": len(solved["assignments"]), "slots": len(slots),
                    "unpriced_picks": unpriced, "picks": len(picks),
                    # WHERE THE STARTERS CAME FROM. A zero delta is only meaningful alongside
                    # this: if every starter was drafted before the rules diverged, the zero is
                    # EXPLAINED (the switch touched only bench picks) rather than suspicious.
                    "latest_starter_pick": max((pick_no.get(p, 0) for p in started), default=0)}
    return out


def main() -> int:
    report = {"arms": {}}
    battery = json.loads(IN.read_text())["arms"]
    players_db, prov = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    base = rdb.scoring_settings_from_capture()
    import draft_battery as db
    import league_config as lc
    matrix = {e["label"]: e for e in db.league_matrix(base)}
    print(f"universe {prov['players_in_pool']}  season {len(season)}\n", flush=True)

    def league_for(label, entry):
        if label in matrix:
            return matrix[label]["league"]
        lg = dr.build_mock_league(teams=entry["teams"], superflex=False, scoring="ppr",
                                  te_premium=False, dynasty=True, base_scoring=base)
        starters = [s for s in lg["roster_positions"] if s != "BN"]
        bench = entry["rounds"] - len(lc.draftable_slots(starters))
        lg["roster_positions"] = starters + ["BN"] * bench
        return lg

    print(f"{'arm':<28}{'round pts':>11}{'crossing pts':>13}{'delta':>10}{'delta %':>9}"
          f"{'unpr r/c':>10}{'1st diff':>9}{'last st':>9}", flush=True)
    for label, entry in battery.items():
        rules = entry["rules"]
        if not {"round", "crossing"} <= set(rules):
            continue
        league = league_for(label, entry)
        per_rule = {r: seat_lineups(rules[r]["per_seat"], league, players_db, season)
                    for r in ("round", "crossing")}
        tot = {r: round(sum(s["starting_points"] for s in per_rule[r].values()), 2)
               for r in per_rule}
        unp = {r: sum(s["unpriced_picks"] for s in per_rule[r].values()) for r in per_rule}
        # The pick at which the two rules first chose differently, from the recorded sequences.
        sr = sorted((x["pick_no"], x["pid"]) for ps in rules["round"]["per_seat"].values() for x in ps)
        sc = sorted((x["pick_no"], x["pid"]) for ps in rules["crossing"]["per_seat"].values() for x in ps)
        first_diff = next((i + 1 for i in range(min(len(sr), len(sc))) if sr[i][1] != sc[i][1]), None)
        latest_starter = max(s["latest_starter_pick"] for r in per_rule for s in per_rule[r].values())
        delta = round(tot["crossing"] - tot["round"], 2)
        pct = round(100.0 * delta / tot["round"], 2) if tot["round"] else None
        report["arms"][label] = {
            "teams": entry["teams"], "total_picks": entry["total_picks"],
            "round_points": tot["round"], "crossing_points": tot["crossing"],
            "delta": delta, "delta_pct": pct,
            "first_divergent_pick": first_diff,
            "latest_starter_pick": latest_starter,
            "switch_touches_a_starter": bool(first_diff and latest_starter >= first_diff),
            "unpriced": unp, "per_seat": per_rule,
        }
        pct_txt = f"{pct:+.2f}%" if pct is not None else "--"
        unp_txt = "{}/{}".format(unp["round"], unp["crossing"])
        print(f"{label:<28}{tot['round']:>11.1f}{tot['crossing']:>13.1f}{delta:>+10.1f}"
              f"{pct_txt:>9}{unp_txt:>10}{str(first_diff):>9}{latest_starter:>9}", flush=True)

    # NON-VACUITY GATE, earned the hard way (see seat_lineups). A control that compares 0.0 to
    # 0.0 reports "ok" while measuring nothing, so the population is checked BEFORE the control
    # is believed: if most picks are unpriced or no arm scored any points, this run is void.
    total_picks = sum(a["total_picks"] for a in report["arms"].values())
    total_unpriced = sum(a["unpriced"]["round"] for a in report["arms"].values())
    any_points = any(a["round_points"] or a["crossing_points"] for a in report["arms"].values())
    unpriced_rate = (total_unpriced / total_picks) if total_picks else 1.0
    print(f"\nPOPULATION  picks={total_picks}  unpriced={total_unpriced} "
          f"({unpriced_rate:.1%})  any_points={any_points}", flush=True)
    if not any_points or unpriced_rate > 0.5:
        report["verdict"] = "VOID -- vacuous population, no result may be read from this run"
        print("VOID -- vacuous population. No result may be read from this run.", flush=True)
        OUT.write_text(json.dumps(report, indent=1))
        return 1

    touched = [l for l, a in report["arms"].items() if a["switch_touches_a_starter"]]
    print(f"\nDOES THE MODE SWITCH EVER CHANGE A STARTER?  "
          f"{'YES in ' + ', '.join(touched) if touched else 'NO -- in every arm, every starting-lineup player was drafted BEFORE the rules diverged'}",
          flush=True)
    report["switch_touches_a_starter_in"] = touched

    ctrl = report["arms"].get("12T_ppr_BN6")
    if ctrl is not None:
        ok = abs(ctrl["delta"]) < 0.005
        print(f"\nCONTROL 12T_ppr_BN6 (neither rule fires) delta={ctrl['delta']:+.2f}  "
              f"{'ok -- the instrument measures the mode switch and nothing else' if ok else 'BROKEN -- a nonzero delta where no rule fired means this measures something else'}",
              flush=True)
        report["control_selfcheck"] = "ok" if ok else "BROKEN"
    OUT.write_text(json.dumps(report, indent=1))
    print(f"\nwrote {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
