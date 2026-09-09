"""Two candidate CEILING derivations, tested on all 33 formats and both arms.

The owner's anchor: in 8T_half_ppr_SF (fieldable WR5/RB5, 6 bench) 10 WR / 2 RB is out of
balance and 7 / 4 is the lower edge of acceptable.

  A) fieldable + 2          -- fits the anchor exactly (ceiling 7), but the 2 IS A FITTED
                               CONSTANT, calibrated to a single stated point. Honest about it.
  B) fieldable + ceil(bench / positions)
                            -- no free constant: a position may carry the slots it could ever
                               occupy, plus its even share of the bench. In 8T_half_ppr_SF that
                               is 5 + ceil(6/4) = 5 + 2 = 7, so it reproduces the anchor WITHOUT
                               being told it.

Floor for both: dedicated slots + 1 (one body of insurance behind every named slot), which is
what rejects the 2-RB and 0-TE rosters.
"""
import collections, json, math, pathlib, sys
import lineup_optimizer as lo, run_216_bench_probe as bench, run_draft_battery as rdb
import run_roster_proof as rp
players_db, _ = rdb.build_players_db_from_capture()
POS = ("QB", "RB", "WR", "TE")

def bounds(roster_positions, kind):
    slots = lo.slots_from_roster_positions(roster_positions)
    bn = sum(1 for p in roster_positions if p == "BN")
    fieldable = {p: sum(1 for s in slots if p in s["eligible"]) for p in POS}
    ded = collections.Counter(s["label"] for s in slots if len(s["eligible"]) == 1)
    k = 2 if kind == "A" else math.ceil(bn / len(POS))
    return {p: (ded.get(p, 0) + 1, fieldable[p] + k) for p in POS}, fieldable

out = collections.defaultdict(lambda: collections.Counter())
detail = collections.defaultdict(list)
for root in sys.argv[1:]:
    for f in sorted(pathlib.Path(root).glob("*.json")):
        d = json.load(open(f))
        for kind in ("A", "B"):
            bd, fieldable = bounds(d["roster_positions"], kind)
            for r in d["drafts"]:
                comp = r.get("composition") or {}
                bad = [(p, comp.get(p, 0), bd[p]) for p in POS
                       if not (bd[p][0] <= comp.get(p, 0) <= bd[p][1])]
                out[(kind, r["arm"])]["rosters"] += 1
                out[(kind, r["arm"])]["violations"] += len(bad)
                if bad:
                    out[(kind, r["arm"])]["bad_rosters"] += 1
                    detail[(kind, r["arm"])].append((d["format"], r["seat"], bad))

print(f"{'rule':32}{'arm':8}{'rosters':>9}{'clean':>8}{'violating cells':>17}")
for kind, name in (("A", "fieldable + 2 (fitted)"), ("B", "fieldable + ceil(bench/4) (derived)")):
    for arm in ("SELF", "SHARED"):
        c = out[(kind, arm)]
        clean = c["rosters"] - c["bad_rosters"]
        print(f"{name:32}{arm:8}{c['rosters']:>9}{clean:>8}{c['violations']:>17}")

print("\n\nWHAT RULE B FLAGS IN THE WIRED ENGINE (SHARED), all of it:")
seen = collections.Counter()
for fmt, seat, bad in detail[("B", "SHARED")]:
    for p, n, (lo_, hi) in bad:
        seen[(fmt, p, n, lo_, hi)] += 1
for (fmt, p, n, lo_, hi), _ in sorted(seen.items(), key=lambda kv: -abs(kv[0][2] - kv[0][4])):
    side = "OVER" if n > hi else "under"
    print(f"  {fmt:22}{p:5} held {n:>3}   allowed [{lo_}-{hi}]   {side}")
print("\nAND IN THE SHIPPED ENGINE (SELF), for comparison:")
seen2 = collections.Counter()
for fmt, seat, bad in detail[("B", "SELF")]:
    for p, n, (lo_, hi) in bad:
        seen2[(fmt, p, n, lo_, hi)] += 1
print(f"  {len(seen2)} distinct violating (format, position, count) combinations vs {len(seen)} for SHARED")
