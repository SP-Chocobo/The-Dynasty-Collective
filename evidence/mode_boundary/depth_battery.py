"""Draft ten leagues under BOTH mode rules and compare the rosters. #261, the behavioural half.

#261 measured WHERE a replacement-crossing boundary would fire. It did not measure what
happens if you draft under it, and the entry says so in as many words: "nobody has drafted
with the rule in place." This does that.

WHY THE EXISTING BATTERY CANNOT ANSWER IT -- the finding that shaped every arm below. Across
all 34 matrix arms, bench depth is:

    BN slots -> arms:   {5: 1,  6: 32,  11: 1}

Thirty-two of thirty-four carry exactly `MOCK_BENCH_SLOTS = 6`, because `build_mock_league`
hardcodes it and `rounds = len(draftable_slots(roster_positions))` derives depth from the
roster. So the battery's DEPTH AXIS IS A CONSTANT, and the only genuinely deep arm in it is
CAPTURE_fourth_and_forever -- the one real captured rulebook, at 11 BN + 3 IR + 5 TAXI.

That is why three of #261's four probe arms never reached the zero. It is a property of the
SAMPLE, not of the rule. It also means the owner's own criterion -- "if a league never pulls
from the deep reserves, I don't mind it not reaching upside mode" -- has never been tested
against a league with deep reserves, except F&F. Real dynasty startups run 20-30 rounds
routinely; the matrix tops out at 15 outside F&F.

I had this number in hand during the Gate 1 bench analysis ("32 of 33 arms had identical bench
depth") and used it to withdraw a prediction without drawing the conclusion that the axis was
unvaried. Recorded because the miss is the useful part.

THE ARMS, chosen so the crossing CAN manifest rather than hoping it does:

  LADDER A -- depth sweep, everything else held (12 teams, ppr, 1QB, dynasty). BN 6 -> 26,
    which is rounds 14 -> 34. Arm 1 is the current matrix shape and is the NEGATIVE CONTROL:
    if the crossing fires there, the instrument is wrong, because #261 measured it not firing
    in any 14-round format.

  LADDER B -- rounds held at 26, teams swept 8/10/12/14. Ladder A varies rounds and picks
    together and cannot separate them. This line holds rounds fixed while total picks moves
    208 -> 364, which is exactly the owner's question: "total number of players taken would be
    a better threshold than round count, because it'd be ambivalent to settings." If the
    crossing lands at a similar PICK COUNT across this line, picks-taken is the real quantity;
    if it lands at a similar ROUND, the calendar is (and the crossing is round 15 in disguise).

  THE REAL ONE -- CAPTURE_fourth_and_forever, 26 rounds, a real rulebook at the same depth as
    12T_ppr_BN18. Anchors the synthetic ladder to something nobody designed for this question.

BOTH ARMS RUN IN ONE PROCESS ON ONE CODE VERSION, toggling `upside_rule` and nothing else --
the engine-measurement skill's rule, and the reason `upside_rule` was added as a defaulted
parameter rather than by patching the source. Never compare against a saved baseline from
different code.

Run from the repo root. NEVER cd first -- DataMerger resolves baselines against cwd.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/mode_boundary/depth_battery.py
Resumes from its own output; re-running after a kill picks up at the first unfinished arm.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_simulation as ds
import draft_strategy as dstrat
import league_config as lc
import run_draft_battery as rdb

OUT = Path("evidence/mode_boundary/depth_battery.json")
RULES = (dr.UPSIDE_RULE_ROUND, dr.UPSIDE_RULE_CROSSING)


def deep_league(teams: int, bench: int, base_scoring: dict) -> dict:
    """A mock league with a REAL bench depth, built from build_mock_league's own starters.

    The starters are taken from the shipped builder rather than restated here (#126: one home
    for a vocabulary, derived, never hand-listed) -- only the bench length is this function's
    own contribution, because that is the single axis under test.
    """
    league = dr.build_mock_league(teams=teams, superflex=False, scoring="ppr",
                                  te_premium=False, dynasty=True, base_scoring=base_scoring)
    starters = [s for s in league["roster_positions"] if s != "BN"]
    league["roster_positions"] = starters + ["BN"] * bench
    league["draft_rounds"] = len(lc.draftable_slots(league["roster_positions"]))
    return league


def arms(base_scoring: dict, matrix: dict) -> list[dict]:
    out = []
    for bench in (6, 10, 14, 18, 22, 26):          # LADDER A: depth, 12 teams
        lg = deep_league(12, bench, base_scoring)
        out.append({"label": f"12T_ppr_BN{bench}", "ladder": "A",
                    "league": lg, "teams": 12, "rounds": lg["draft_rounds"]})
    for teams in (8, 10, 14):                       # LADDER B: teams, depth held at BN18
        lg = deep_league(teams, 18, base_scoring)
        out.append({"label": f"{teams}T_ppr_BN18", "ladder": "B",
                    "league": lg, "teams": teams, "rounds": lg["draft_rounds"]})
    ff = matrix["CAPTURE_fourth_and_forever"]       # the real rulebook
    out.append({"label": ff["label"], "ladder": "real", "league": ff["league"],
                "teams": ff["teams"], "rounds": ff["rounds"]})
    return out


def summarize(traj, teams: int, players_db: dict, season: dict) -> dict:
    """Roster outcomes, per seat, plus where the mode actually turned over.

    HOW THE TURNOVER IS DETECTED, and the wrong answer I nearly shipped. The first draft read
    `snapshot.mode`. PickSnapshot HAS NO `mode` FIELD -- `compute_draft_board` sets
    `scored["mode"] = "upside"` on the BOARD ROW (draft_room.py:3109) and CandidateSnapshot
    does not carry it across. So that detector would have returned NEVER for all twenty
    drafts, and "the crossing never fires" is exactly the shape of result this battery exists
    to produce honestly. It would have looked like a finding.

    What is used instead: `PickRecord.chosen_growth_signal`. `growth_signal` is produced by
    `upside_score` and by nothing else (draft_room.py:2073), so a pick carrying one was scored
    by the upside branch. That is the engine's own output, not a rule restated here.

    THE DETECTOR CHECKS ITSELF. Under the ROUND rule the answer is known in advance -- upside
    must begin at exactly UPSIDE_MODE_DEFAULT_ROUND in any league long enough to reach it.
    `detector_selfcheck` reports whether it did. A mismatch means the detector is broken, not
    that the engine is, and it is reported as such rather than being read as a result.
    """
    per_seat: dict[str, list] = {}
    first_upside = None
    for p in traj.picks:
        rid = str(p.roster_id)
        row = players_db.get(str(p.chosen_player_id)) or {}
        pos = row.get("position")
        pts = (season.get(str(p.chosen_player_id)) or {}).get("pts")
        per_seat.setdefault(rid, []).append({
            "round": p.round, "pick_no": p.pick_no, "pid": str(p.chosen_player_id),
            "pos": pos, "regime": p.decision_regime,
        })
        if first_upside is None and p.chosen_growth_signal is not None:
            first_upside = {"round": p.round, "pick_no": p.pick_no}
    comp: dict[str, int] = {}
    for picks in per_seat.values():
        for e in picks:
            if e["pos"]:
                comp[e["pos"]] = comp.get(e["pos"], 0) + 1
    return {"n_picks": len(traj.picks), "first_upside_pick": first_upside,
            "positional_composition": dict(sorted(comp.items())), "per_seat": per_seat}


def selfcheck(rounds: int, res: dict) -> str:
    """Did the ROUND arm do the one thing it is guaranteed to do? See summarize's docstring."""
    fu = res["first_upside_pick"]
    if rounds < dr.UPSIDE_MODE_DEFAULT_ROUND:
        return "n/a (draft ends before the round rule could fire)"
    if fu is None:
        return "BROKEN DETECTOR -- round rule reported NEVER in a long enough draft"
    if fu["round"] != dr.UPSIDE_MODE_DEFAULT_ROUND:
        return f"BROKEN DETECTOR -- round rule turned over at r{fu['round']}, expected r{dr.UPSIDE_MODE_DEFAULT_ROUND}"
    return "ok"


def main() -> int:
    t0 = time.time()
    report = json.loads(OUT.read_text()) if OUT.exists() else {"arms": {}}

    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()   # #201/#204: never build_players_db
    season = rdb.season_projections_from_capture()
    base = rdb.scoring_settings_from_capture()
    matrix = {e["label"]: e for e in db.league_matrix(base)}
    print(f"universe {prov['players_in_pool']}  season {len(season)}", flush=True)

    todo = arms(base, matrix)
    print(f"{len(todo)} arms x {len(RULES)} rules = {len(todo) * len(RULES)} drafts\n", flush=True)
    for a in todo:
        print(f"  {a['label']:<26} ladder {a['ladder']:<4} teams={a['teams']:>3} "
              f"rounds={a['rounds']:>3} picks={a['teams'] * a['rounds']:>4}", flush=True)
    print(flush=True)

    for a in todo:
        entry = report["arms"].setdefault(a["label"], {
            "ladder": a["ladder"], "teams": a["teams"], "rounds": a["rounds"],
            "total_picks": a["teams"] * a["rounds"], "rules": {}})
        for rule in RULES:
            if rule in entry["rules"]:
                print(f"[skip] {a['label']} / {rule}", flush=True)
                continue
            t1 = time.time()
            merger.set_league_format(db.league_format_hint(a["league"]))   # NEVER SKIP (#150)
            roster_ids = [str(i) for i in range(1, a["teams"] + 1)]
            order = dstrat.generate_pick_order(roster_ids, a["rounds"], "snake")
            traj = ds.simulate_full_draft(
                merger, players_db, a["league"], order, config_label=a["label"],
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
                upside_rule=rule)
            res = summarize(traj, a["teams"], players_db, season)
            res["elapsed_s"] = round(time.time() - t1, 1)
            entry["rules"][rule] = res
            if rule == dr.UPSIDE_RULE_ROUND:
                res["detector_selfcheck"] = selfcheck(a["rounds"], res)
                if res["detector_selfcheck"].startswith("BROKEN"):
                    print(f"!! {a['label']}: {res['detector_selfcheck']}", flush=True)
            fu = res["first_upside_pick"]
            print(f"[done] {a['label']:<26} {rule:<9} upside_from="
                  f"{('r%d p%d' % (fu['round'], fu['pick_no'])) if fu else 'NEVER':<10} "
                  f"{res['elapsed_s']}s", flush=True)
            OUT.write_text(json.dumps(report, indent=1))       # checkpoint EVERY arm (#215)

    # #276. THIS BATTERY PUBLISHED SIX ARMS THAT WERE ONE DRAFT SAMPLED AT SIX LENGTHS, and
    # nothing here said so. `draft_battery` already carried two derived self-checks and this
    # instrument called neither -- which is the proximate reason a prefix-nested ladder reached
    # a published entry as "none of the six". The report now names its own nested arms, so the
    # next reader sees the dependence without having to suspect it.
    #
    # Read from the report the battery just wrote rather than from the trajectories, so the
    # check applies to the EVIDENCE a reader will actually have, including on a resumed run
    # whose earlier arms this process never simulated.
    sequences = {}
    for label, entry in report["arms"].items():
        rule = entry["rules"].get(dr.UPSIDE_RULE_CROSSING)
        if rule is None:
            continue
        flat = [(e["pick_no"], e["pid"]) for picks in rule["per_seat"].values() for e in picks]
        flat.sort()
        sequences[label] = [pid for _, pid in flat]
    report["nested_arms"] = db.prefix_arms(sequences)
    report["independent_arms"] = len(sequences) - len(report["nested_arms"])
    if report["nested_arms"]:
        print("\n!! NESTED ARMS -- these add no observation the container does not already hold:",
              flush=True)
        for row in report["nested_arms"]:
            print(f"   {row['label']:<26} is the first {row['picks']} picks of "
                  f"{row['prefix_of']} ({row['container_picks']})", flush=True)
        print(f"   {report['independent_arms']} of {len(sequences)} arms are independent "
              f"evidence.", flush=True)

    report["elapsed_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(report, indent=1))
    print(f"\nwrote {OUT}  ({report['elapsed_s']}s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
