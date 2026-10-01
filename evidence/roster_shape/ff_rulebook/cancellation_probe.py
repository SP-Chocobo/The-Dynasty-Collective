"""Does the anchor CANCEL for every flex-eligible position, leaving raw projection?

The #221 memo says it does for the pair it measured. If it holds generally, then on a
roster whose flex slots are the binding constraint, the engine ranks flex-eligible
candidates by PROJECTION MINUS ONE SHARED NUMBER -- i.e. by projection. That is a
testable identity, not an interpretation:

    universal_value + displacement_adj  ==  projection - shared_flex_alternative

Run from repo root.
"""
import json, pandas as pd
import draft_room as dr, lineup_optimizer as lo

CAP = json.load(open("data/league_captures/fourth_and_forever.json"))
RP = CAP["roster_positions"]
rows = json.load(open("/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/ff/ff_board.json"))
df = pd.DataFrame(rows)
df["projected_points"] = pd.to_numeric(df["projected_points"], errors="coerce")
df = df.dropna(subset=["projected_points"]).sort_values("projected_points", ascending=False)

def take(d, pos, n, used):
    got=[]
    for _, r in d[d["position"]==pos].iterrows():
        if r["player_id"] in used: continue
        got.append(r); used.add(r["player_id"])
        if len(got)==n: break
    return got

for k in (0, 20, 40):
    keep = pd.concat([g.iloc[k:] for _, g in df.groupby("position")]) if k else df
    keep = keep.sort_values("projected_points", ascending=False)
    used=set()
    mine = take(keep,"QB",2,used)+take(keep,"RB",3,used)+take(keep,"WR",3,used)+take(keep,"TE",2,used)
    roster=[{"id":str(r["player_id"]),"value":float(r["projected_points"]),"eligible":{r["position"]}} for r in mine]
    avail = keep[~keep["player_id"].isin({r["player_id"] for r in mine})]
    lv  = dr.replacement_levels(avail,"projected_points",RP,12)
    adj = dr.displacement_adjustments(roster, RP, lv)
    alts = dr.shared_slot_alternatives(lv, RP)
    flex_alt = max((v for s,v in alts.items() if s.startswith("FLEX")), default=None)
    print(f"\n=== drained {k}   levels " + " ".join(f"{p}={lv[p]:.0f}" for p in sorted(lv))
          + f"   FLEX alternative={flex_alt:.0f}")
    print(f"{'pos':4}{'proj':>8}{'VOR':>8}{'dispAdj':>9}{'VOR+adj':>9}{'proj-flexAlt':>14}{'match?':>8}")
    for p in ("RB","WR","TE"):
        sub = avail[avail["position"]==p]
        if p not in lv or not len(sub): continue
        top = sub.iloc[0]
        proj = float(top["projected_points"])
        vor  = proj - lv[p]
        a    = adj.get(p,{}).get("adjustment",0.0) or 0.0
        lhs, rhs = vor + a, proj - flex_alt
        print(f"{p:4}{proj:>8.0f}{vor:>8.1f}{a:>9.1f}{lhs:>9.1f}{rhs:>14.1f}{'YES' if abs(lhs-rhs)<0.5 else 'no':>8}")
