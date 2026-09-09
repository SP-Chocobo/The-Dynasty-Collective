"""Does the SHIPPED displacement correction neutralise the drain bias?

FINDING_02 measured raw VOR. The engine does not rank on raw VOR -- displacement_adj
(#216, wired at #221) deducts what the league anchor over-credits a player whose slots
this roster already holds. So the honest question is whether the WR flatness survives
the correction that exists.

Roster: the ten starting slots filled from the top of the board, which is what a real
roster looks like by the time bench picks begin. Run from repo root.
"""
import json, collections, pandas as pd
import data_merger as dm, draft_room as dr, lineup_optimizer as lo

CAP = json.load(open("data/league_captures/fourth_and_forever.json"))
RP = CAP["roster_positions"]
rows = json.load(open("/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/ff/ff_board.json"))
df = pd.DataFrame(rows)
df["projected_points"] = pd.to_numeric(df["projected_points"], errors="coerce")
df = df.dropna(subset=["projected_points"]).sort_values("projected_points", ascending=False)

def take(d, pos, n, used):
    got = []
    for _, r in d[d["position"] == pos].iterrows():
        if r["player_id"] in used: continue
        got.append(r); used.add(r["player_id"])
        if len(got) == n: break
    return got

print("A roster with all TEN starting slots filled, then bench picks. Value by position:\n")
print(f"{'drained':>8}" + "".join(f"{p:>26}" for p in ("QB","RB","WR","TE")))
print(f"{'each':>8}" + "".join(f"{'rawVOR':>8}{'dispAdj':>9}{'NET':>9}" for p in ("QB","RB","WR","TE")))
for k in (0, 10, 20, 30, 40):
    keep = pd.concat([g.iloc[k:] for _, g in df.groupby("position")]) if k else df
    keep = keep.sort_values("projected_points", ascending=False)
    used = set()
    mine = (take(keep,"QB",2,used) + take(keep,"RB",3,used)
            + take(keep,"WR",3,used) + take(keep,"TE",2,used))   # 10 starters
    roster = [{"id": str(r["player_id"]), "value": float(r["projected_points"]),
               "eligible": {r["position"]}} for r in mine]
    avail = keep[~keep["player_id"].isin({r["player_id"] for r in mine})]
    lv = dr.replacement_levels(avail, "projected_points", RP, 12)
    adj = dr.displacement_adjustments(roster, RP, lv)
    line = f"{k:>8}"
    for p in ("QB","RB","WR","TE"):
        sub = avail[avail["position"] == p]
        if p in lv and len(sub):
            raw = sub["projected_points"].max() - lv[p]
            a = adj.get(p, {}).get("adjustment", 0.0) or 0.0
            line += f"{raw:>8.0f}{a:>9.0f}{raw+a:>9.0f}"
        else: line += f"{'--':>8}{'--':>9}{'--':>9}"
    print(line)
