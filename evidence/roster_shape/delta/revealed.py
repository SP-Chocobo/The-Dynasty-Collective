"""Can the shape criterion be READ OFF the twelve chairs instead of asserted? (#221 / #217)

`WR >= RB > TE` is the owner's rule for the owner's FORMAT, and the waves just showed it does
not transfer: it fails a two-TE-slot league and a TE-premium league for reasons that have
nothing to do with the change under test. The alternative is a REVEALED distribution -- what the
seats in a draft actually end up holding -- with a robust centre so that hero-RB / zero-RB /
hero-WR tails are admitted as tails instead of setting the criterion.

Every draft record already carries `all_rosters` for all twelve seats. 98 drafts x 12 seats.

READ THE CAVEAT BEFORE THE NUMBERS. Eleven of the twelve seats are ONE deterministic control
rule (run_roster_proof.control_pick: best projection at a position I still need to start).
They are not twelve managers with twelve strategies. So this measures ONE strategy sampled at
eleven draft positions -- which is a real and useful thing, but it is NOT a population of
humans and it CANNOT contain hero-RB or zero-RB, because no chair here plays them.
"""
import collections, json, pathlib, statistics, sys
import run_draft_battery as rdb

players_db, _ = rdb.build_players_db_from_capture()

def pos_of(pid):
    info = players_db.get(str(pid)) or {}
    return info.get("position")

rows = collections.defaultdict(lambda: collections.defaultdict(list))   # (fmt, arm) -> pos -> [counts]
engine_rows = collections.defaultdict(lambda: collections.defaultdict(list))
bands = {}
for root in sys.argv[1:]:
    for f in sorted(pathlib.Path(root).glob("*.json")):
        d = json.load(open(f))
        fmt = d["format"]
        for r in d["drafts"]:
            arm = r["arm"]
            bands.setdefault(fmt, (r.get("band") or {}).get("target_total") or {})
            for seat, ids in (r.get("all_rosters") or {}).items():
                comp = collections.Counter(p for p in (pos_of(i) for i in ids) if p)
                target = engine_rows if str(seat) == str(r["seat"]) else rows
                for pos in ("QB", "RB", "WR", "TE"):
                    target[(fmt, arm)][pos].append(comp.get(pos, 0))

def quart(v):
    v = sorted(v)
    n = len(v)
    return v[n // 4], statistics.median(v), v[(3 * n) // 4]

print("CONTROL SEATS (11 per draft): median [p25-p75] per position, vs the DERIVED band target\n")
print(f"{'format':22}{'arm':7}{'n':>5}  " + "".join(f"{p:>22}" for p in ("QB", "RB", "WR", "TE")))
agree = disagree = 0
for key in sorted(rows):
    fmt, arm = key
    if arm != "SHARED":
        continue
    band = bands.get(fmt, {})
    cells = []
    for pos in ("QB", "RB", "WR", "TE"):
        v = rows[key][pos]
        lo, med, hi = quart(v)
        t = band.get(pos)
        mark = ""
        if t is not None:
            if lo <= t <= hi:
                mark = "="; agree += 1
            else:
                mark = "!"; disagree += 1
        cells.append(f"{med:>4.0f} [{lo}-{hi}] t{t if t is None else round(t,1)}{mark}")
    n = len(rows[key]["QB"])
    print(f"{fmt:22}{arm:7}{n:>5}  " + "".join(f"{c:>22}" for c in cells))
print(f"\nderived band target inside the control seats' interquartile range: {agree} of {agree+disagree}")

print("\n\nORDERING, as the control seats actually reveal it (share of seats, SHARED arm):")
tot = collections.Counter(); n_all = 0
for key in rows:
    if key[1] != "SHARED":
        continue
    per = rows[key]
    for i in range(len(per["QB"])):
        order = sorted(("QB", "RB", "WR", "TE"), key=lambda p: -per[p][i])
        tot[">".join(order)] += 1
        n_all += 1
for k, v in tot.most_common(8):
    print(f"  {k:22} {v:>5}  {100*v/n_all:5.1f}%")
print(f"  ({n_all} control rosters)")
