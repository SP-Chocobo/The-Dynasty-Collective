"""W4-01: is `years_exp == 0` really "this year's rookie class"?

ROOKIE_YEARS_EXP's comment asserts it: "A player with zero completed NFL seasons -- this
year's rookie class." The ruling `promote years_exp` rests on that assertion, and it moves a
rookie draft from 95 players to 718.

A real rookie class is age ~21-24. If `years_exp == 0` carries materially older players, it is
not the rookie class -- it is "never accrued an NFL season", which includes practice-squad
bodies and camp arms from earlier years, and is a different population wearing the same name.

AGE IS THE DISCRIMINATOR, and it is in the capture.
"""
import collections, statistics
import data_merger as dm, draft_room as dr, run_draft_battery as rdb

merger = dm.DataMerger()
players_db, _prov = rdb.build_players_db_from_capture()

ktc = dr._rookie_lookup(merger)
ktc_true = {k for k, v in ktc.items() if v}
print(f"KTC rookie lookup: {len(ktc)} keys, {len(ktc_true)} flagged rookie\n")

def age_of(info):
    a = info.get("age")
    try:
        return float(a) if a is not None else None
    except (TypeError, ValueError):
        return None

ye0, ktcr, both, placeholder = [], [], 0, 0
for pid, info in players_db.items():
    if (info.get("first_name"), info.get("last_name")) == dr.PLACEHOLDER_NAME:
        placeholder += 1
        continue
    name = dr.player_name(info, pid)
    key = (dr.name_key(dr.normalize_name(name)),
           dr.identity_namespace(dr.player_position(info)))
    is_ktc = bool(ktc.get(key, False))
    is_ye0 = info.get("years_exp") == dr.ROOKIE_YEARS_EXP
    if is_ye0:
        ye0.append((name, age_of(info), info.get("team"), info.get("status")))
    if is_ktc:
        ktcr.append((name, age_of(info), info.get("team"), info.get("status")))
    if is_ye0 and is_ktc:
        both += 1

def summarize(label, rows):
    ages = [a for _, a, _, _ in rows if a is not None]
    print(f"{label:<28} n={len(rows):>5}  with age={len(ages):>5}")
    if ages:
        ages.sort()
        print(f"{'':<28} age min {min(ages):.0f}  p25 {ages[len(ages)//4]:.0f}  "
              f"median {statistics.median(ages):.0f}  p75 {ages[3*len(ages)//4]:.0f}  "
              f"max {max(ages):.0f}  mean {statistics.mean(ages):.1f}")
        print(f"{'':<28} age >= 25: {sum(1 for a in ages if a >= 25)} "
              f"({sum(1 for a in ages if a >= 25)/len(ages)*100:.1f}%)   "
              f"age >= 27: {sum(1 for a in ages if a >= 27)}")
    with_team = sum(1 for _, _, t, _ in rows if t)
    print(f"{'':<28} on an NFL team: {with_team} ({with_team/max(len(rows),1)*100:.1f}%)")
    print()

print(f"placeholders excluded: {placeholder}\n")
summarize("years_exp == 0", ye0)
summarize("KTC rookie == True", ktcr)
print(f"in BOTH populations: {both}")
print(f"years_exp==0 only:   {len(ye0) - both}")
print(f"KTC-rookie only:     {len(ktcr) - both}")
