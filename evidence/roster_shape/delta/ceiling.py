"""The owner: "the guy going rb heavy, perhaps he just wanted heavier insurance there. it's not
like anyone took 4 te". Is that true of the 515 control rosters, and is the CEILING the thing
that actually discriminates?"""
import collections, json, pathlib, sys
import run_draft_battery as rdb
players_db, _ = rdb.build_players_db_from_capture()

comps = []
for root in sys.argv[1:]:
    for f in sorted(pathlib.Path(root).glob("*.json")):
        d = json.load(open(f))
        for r in d["drafts"]:
            if r["arm"] != "SHARED":
                continue
            rp = d["roster_positions"]
            ded = collections.Counter(p for p in rp if p in ("QB", "RB", "WR", "TE"))
            for seat, ids in (r.get("all_rosters") or {}).items():
                if str(seat) == str(r["seat"]):
                    continue                     # engine seat excluded: this is the CONTROL norm
                c = collections.Counter((players_db.get(str(i)) or {}).get("position") for i in ids)
                comps.append((d["format"], ded, {p: c.get(p, 0) for p in ("QB", "RB", "WR", "TE")}))

print(f"{len(comps)} control rosters\n")
print(f"{'pos':5}{'min':>5}{'p50':>5}{'p90':>5}{'p99':>5}{'max':>5}   how often at or above 4")
for pos in ("QB", "RB", "WR", "TE"):
    v = sorted(c[pos] for _, _, c in comps)
    n = len(v)
    ge4 = sum(1 for x in v if x >= 4)
    print(f"{pos:5}{v[0]:>5}{v[n//2]:>5}{v[int(n*0.9)]:>5}{v[int(n*0.99)]:>5}{v[-1]:>5}"
          f"   {ge4:>5} ({100*ge4/n:5.1f}%)")

print("\nPER DEDICATED SLOT -- the same counts divided by how many slots that position actually has,")
print("which is the only way the four are comparable across formats:")
print(f"{'pos':5}{'slots':>7}{'p50/slot':>10}{'p90/slot':>10}{'max/slot':>10}")
by = collections.defaultdict(list)
for _, ded, c in comps:
    for pos in ("QB", "RB", "WR", "TE"):
        s = ded.get(pos, 0)
        if s:
            by[pos].append(c[pos] / s)
for pos in ("QB", "RB", "WR", "TE"):
    v = sorted(by[pos]); n = len(v)
    print(f"{pos:5}{'':>7}{v[n//2]:>10.2f}{v[int(n*0.9)]:>10.2f}{v[-1]:>10.2f}")

print("\nTHE TAIL, stated as the owner framed it:")
for pos in ("RB", "TE"):
    four = [(f, c) for f, _, c in comps if c[pos] >= 4]
    five = [(f, c) for f, _, c in comps if c[pos] >= 5]
    print(f"  {pos}: >=4 in {len(four):>4} of {len(comps)} rosters ({100*len(four)/len(comps):4.1f}%),"
          f"  >=5 in {len(five)} ({100*len(five)/len(comps):4.1f}%)")
    if four[:1]:
        f, c = four[0]
        print(f"      example: {f} {c}")
