"""Replay ONE noisy arm, recording the rank the noise draw took on every pick.

The question: under `noisy_k8` every seat draws uniformly from its own top 8
(`sharp_seats: []`), so a roster that ends over its fieldability ceiling may have got there
by the DRAW rather than by the engine's ranking. `snap.candidates` is the engine's own order
with surplus bodies sorted last (`unfieldable_last`), so the two are distinguishable: rank 0
means the engine itself ranked that player first, rank > 0 means the draw reached past the
engine's choice.

Determinism is the check that this replay is the same draft: the seed is fixed and the battery
contains no other randomness, so the reproduced pick_sequence must equal the report's. Asserted,
not assumed.
"""
import json, collections, os, sys, random
assert os.path.basename(os.getcwd()) == "The-Dynasty-Collective", os.getcwd()
sys.path.insert(0, os.getcwd())

ARM = sys.argv[1] if len(sys.argv) > 1 else "12T_ppr_K_DEF__noisy_k8"
DRAWS: list[int] = []

class RecordingRandom(random.Random):
    def randrange(self, *a, **k):
        r = super().randrange(*a, **k)
        DRAWS.append(r)
        return r

random.Random = RecordingRandom          # draft_simulation does `import random as _random`

import run_draft_battery as rdb, draft_battery as db, vds_battery as vb
import data_merger as dm, draft_simulation, draft_strategy as ds
import player_universe as pu, lineup_optimizer as lo

scoring = rdb.scoring_settings_from_capture()
players_db, _prov = rdb.build_players_db_from_capture()
season_projections = rdb.season_projections_from_capture()
weekly_projections = rdb.weekly_projections_from_capture()
merger = dm.DataMerger()
import draft_room as dr

entry = {e["label"]: e for e in vb.vds_matrix(scoring)}[ARM]
merger.set_league_format(db.league_format_hint(entry["league"]))
rids = [str(i) for i in range(1, entry["teams"] + 1)]
order = ds.generate_pick_order(rids, entry["rounds"], "snake")

traj = draft_simulation.simulate_full_draft(
    merger, players_db, entry["league"], order,
    mode=entry.get("mode", "auto"), config_label=entry["label"],
    upside_rule=entry.get("upside_rule", dr.UPSIDE_RULE_ROUND),
    opponent_noise=entry.get("opponent_noise"),
    sleeper_projections=season_projections, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
    weekly_projections=weekly_projections)

rep = json.load(open("evidence/batteries/VDS_2026-09-26_varied_drafting_strategy_04bccb5.json"))
arm = [x for x in rep["results"] if x["label"] == ARM][0]
got = [str(p.chosen_player_id) for p in traj.picks]
same = got == arm["pick_sequence"]
print(f"replay reproduces the report's pick_sequence: {same}  ({len(got)} picks, {len(DRAWS)} draws)")
if not same:
    first = next(i for i, (a, b) in enumerate(zip(got, arm["pick_sequence"])) if a != b)
    print(f"  FIRST DIVERGENCE at pick {first+1}: replay {got[first]} vs report {arm['pick_sequence'][first]}")
    raise SystemExit("replay is not the same draft -- nothing below is about the reported arm")

ded = collections.Counter(); flex = set()
for s in lo.slots_from_roster_positions(entry["league"].get("roster_positions") or []):
    el = set(s.get("eligible") or ())
    if len(el) == 1: ded[next(iter(el))] += 1
    else: flex |= el

held = collections.defaultdict(collections.Counter)
over = []
for i, pick in enumerate(traj.picks):
    pos = pu.player_position(players_db.get(str(pick.chosen_player_id)) or {})
    rid = pick.roster_id
    held[rid][pos] += 1
    if pos in flex or pos not in ded:
        continue
    ceiling = ded[pos] + 1
    if held[rid][pos] > ceiling:
        over.append({"pick": pick.pick_label, "round": pick.round, "roster": rid,
                     "position": pos, "now_held": held[rid][pos], "ceiling": ceiling,
                     "drawn_rank": DRAWS[i], "candidates": len(pick.snapshot.get("candidates") or [])})

print()
print(f"picks that took a roster PAST its ceiling: {len(over)}")
for o in over:
    print(f"  {o['pick']:>6} R{o['round']:<3} roster {o['roster']:>2} {o['position']:<4} "
          f"held {o['now_held']} > ceiling {o['ceiling']}   drawn_rank={o['drawn_rank']}  "
          f"candidates={o['candidates']}")
print()
byrank = collections.Counter(o["drawn_rank"] for o in over)
print("drawn_rank histogram over those picks:", dict(sorted(byrank.items())))
print("rank 0 (the ENGINE's own first choice):", byrank.get(0, 0), "of", len(over))
