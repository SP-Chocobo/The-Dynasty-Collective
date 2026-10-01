import json, collections, os, sys
assert os.path.basename(os.getcwd()) == "The-Dynasty-Collective", os.getcwd()
sys.path.insert(0, os.getcwd())
import run_draft_battery as rdb, draft_battery as db, draft_strategy as ds
import lineup_optimizer as lo, player_universe as pu

players_db, _ = rdb.build_players_db_from_capture()
rep = json.load(open('evidence/batteries/VDS_2026-09-26_varied_drafting_strategy_04bccb5.json'))
mat = {a['label']: a for a in db.league_matrix()}

def geometry(league):
    ded, flex = collections.Counter(), set()
    for s in lo.slots_from_roster_positions(league.get('roster_positions') or []):
        el = set(s.get('eligible') or ())
        if len(el) == 1: ded[next(iter(el))] += 1
        else: flex |= el
    return ded, flex

print(f"{'arm':34} {'reported':>8} {'survives_bucket':>16} {'artifact':>9}")
survivors = []
for arm in rep['results']:
    fnd = [f for f in (arm['findings'] or []) if f['audit'] == 'unfieldable_depth']
    if not fnd: continue
    entry = mat[arm['format']]
    league = entry['league']
    ded, flex = geometry(league)
    rids = [str(i) for i in range(1, entry['teams'] + 1)]
    order = ds.generate_pick_order(rids, entry['rounds'], 'snake')
    rosters = collections.defaultdict(list)
    for rid, pid in zip(order, arm['pick_sequence']):
        rosters[rid].append(pid)
    kept = []
    for f in fnd:
        pids = rosters[f['roster_id']]
        held_bucket = sum(1 for p in pids
                          if pu.player_position(players_db.get(p) or {}) == f['position'])
        ceiling = ded[f['position']] + 1
        if held_bucket > ceiling:
            kept.append(dict(f, held_bucket=held_bucket, arm=arm['label']))
    survivors.extend(kept)
    print(f"{arm['label']:34} {len(fnd):>8} {len(kept):>16} {len(fnd)-len(kept):>9}")
print()
print(f"TOTAL unfieldable_depth reported: {sum(1 for a in rep['results'] for f in (a['findings'] or []) if f['audit']=='unfieldable_depth')}")
print(f"TOTAL surviving a bucket recount: {len(survivors)}")
print()
for s in survivors:
    print(' SURVIVES:', s['arm'], s['roster_id'], s['position'],
          'raw_held', s['held'], 'bucket_held', s['held_bucket'], 'ceiling', s['ceiling'])
