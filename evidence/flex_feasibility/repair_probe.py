"""#247: measure the proposed repair before proposing it (#162 -- evidence before repair).

CANDIDATE REPAIR. feasibility_first counts only DEDICATED slots as at-risk. Generalise it to ask
the same feasibility question of the WHOLE starting lineup -- solve the roster into its slots
exactly as the audit does, and let `unfilled` be every slot the solver could not fill, flex
included. A flex slot then counts as at risk precisely when the roster owns no spare eligible
body, which is the case the current scope was drawn to exclude and the one that fails.

The docstring's warning is the thing to disprove: counting flex naively would turn a backstop
into a preference. So this measures BOTH halves --

  does it fix the two failures?            (8T_standard, 14T_standard)
  what does it cost where nothing is wrong? (12T_ppr, 12T_standard -- both clean today)

and reports HOW OFTEN it binds, because a backstop that binds often is a preference whatever it
is called.

IN-MEMORY: patches draft_room.feasibility_first, never the file, so it is safe beside other runs.
"""
import collections, json
import pandas as pd
import data_merger as dm, draft_battery as db, draft_room as dr, draft_simulation
import draft_strategy as ds, lineup_optimizer as lo, run_draft_battery as rdb
from player_universe import player_position

ORIGINAL = dr.feasibility_first
BIND_LOG = collections.Counter()

def repaired(scored, picks, players_db, my_roster_id, roster_positions, draft_rounds=None):
    default = pd.Series(1, index=scored.index, dtype=int)
    if my_roster_id is None or not roster_positions or scored.empty:
        return default
    slots = lo.slots_from_roster_positions(roster_positions)
    mine_ids = [str(p.get("player_id")) for p in picks
                if str(p.get("roster_id")) == str(my_roster_id)]
    players = []
    for pid in mine_ids:
        info = players_db.get(str(pid)) or {}
        players.append({"id": str(pid), "value": 1.0,
                        "eligible": set(info.get("fantasy_positions")
                                        or ([info["position"]] if info.get("position") else []))})
    solved = lo.optimize_lineup(players, slots)
    assigned = {a["slot_id"] for a in solved["assignments"] if a.get("player_id")}
    unfilled_slots = [s for s in slots if s["slot_id"] not in assigned]
    unfilled = len(unfilled_slots)
    if unfilled <= 0:
        return default
    total_picks = draft_rounds if draft_rounds else len(roster_positions)
    picks_remaining = total_picks - len(mine_ids)
    if picks_remaining > unfilled:
        return default
    BIND_LOG["binds"] += 1
    wanted = set()
    for s in unfilled_slots:
        wanted |= set(s.get("eligible") or ())
    return scored["position"].map(lambda p: 0 if p in wanted else 1).astype(int)

merger = dm.DataMerger()
players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()
base = rdb.scoring_settings_from_capture()

ARMS = [("8T_standard", 8, "standard"), ("14T_standard", 14, "standard"),
        ("12T_standard", 12, "standard"), ("12T_ppr", 12, "ppr")]

def run(label, teams, scoring, fn):
    dr.feasibility_first = fn
    BIND_LOG.clear()
    league = dr.build_mock_league(teams=teams, superflex=False, scoring=scoring,
                                  te_premium=False, dynasty=True, base_scoring=base)
    rounds = len(league["roster_positions"])
    league["draft_rounds"] = rounds
    merger.set_league_format(db.league_format_hint(league))
    seats = [str(i) for i in range(1, teams + 1)]
    traj = draft_simulation.simulate_full_draft(
        merger, players_db, league, ds.generate_pick_order(seats, rounds, "snake"),
        mode="auto", config_label=label,
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    findings = db.unfilled_starting_slots(traj, league, players_db)
    rosters = {str(k): [player_position(players_db.get(str(p)) or {}) for p in v]
               for k, v in traj.final_rosters().items()}
    return findings, rosters, BIND_LOG["binds"], rounds * teams

for label, teams, scoring in ARMS:
    f0, r0, _, picks = run(label, teams, scoring, ORIGINAL)
    f1, r1, binds, _ = run(label, teams, scoring, repaired)
    changed = sum(1 for k in r0 if r0[k] != r1[k])
    print(f"\n===== {label}  ({picks} picks)", flush=True)
    print(f"  current  : {len(f0)} finding(s) {[x['empty_slots'] for x in f0]}", flush=True)
    print(f"  repaired : {len(f1)} finding(s) {[x['empty_slots'] for x in f1]}"
          f"   binds={binds} of {picks} picks ({100*binds/picks:.1f}%)", flush=True)
    print(f"  seats whose roster composition changed: {changed} of {len(r0)}", flush=True)
    for k in sorted(r0, key=int):
        if r0[k] != r1[k]:
            print(f"    seat {k:>2}: {dict(sorted(collections.Counter(r0[k]).items()))}"
                  f"  ->  {dict(sorted(collections.Counter(r1[k]).items()))}", flush=True)
dr.feasibility_first = ORIGINAL
