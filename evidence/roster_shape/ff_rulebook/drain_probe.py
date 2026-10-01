"""Does the replacement anchor move DIFFERENTLY for RB and WR under identical bench drain?

RB and WR have identical starter demand in this league (3.05 each, 36.6 league-wide), so
under the starter-demand model they should behave identically. They do not, and the only
thing that differs is POOL DEPTH: 79 priced RB vs 109 priced WR.

No draft needed -- this drains the pool synthetically and reads the anchor. Run from root.
"""
import json, collections, pandas as pd
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

CAP = json.load(open("data/league_captures/fourth_and_forever.json"))
LEAGUE = {"roster_positions": CAP["roster_positions"],
          "scoring_settings": {k: v["value"] for k, v in CAP["scoring_settings_observed"].items()},
          "total_rosters": 12, "settings": {"type": 2}}
rows = json.load(open("/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/ff/ff_board.json"))
df = pd.DataFrame(rows)
df["projected_points"] = pd.to_numeric(df["projected_points"], errors="coerce")
df = df.dropna(subset=["projected_points"]).sort_values("projected_points", ascending=False)
rp = LEAGUE["roster_positions"]
demand = {p: 12 * v for p, v in dr.starter_slot_counts(rp).items() if v}
print("league starter demand:", {k: round(v,1) for k,v in demand.items()})
print("priced pool depth  :", dict(collections.Counter(df["position"])))
print()
print("Drain the TOP of every position by the same NUMBER of players, then read the anchor.")
print("Identical demand + identical drain -> any divergence is pool depth alone.\n")
print(f"{'drained':>8}" + "".join(f"{p:>22}" for p in ("QB","RB","WR","TE")))
print(f"{'each':>8}" + "".join(f"{'level':>11}{'maxVOR':>11}" for p in ("QB","RB","WR","TE")))
for k in (0, 10, 20, 25, 30, 35, 40, 45):
    keep = pd.concat([g.iloc[k:] for _, g in df.groupby("position")]) if k else df
    lv = dr.replacement_levels(keep, "projected_points", rp, 12)
    line = f"{k:>8}"
    for p in ("QB","RB","WR","TE"):
        sub = keep[keep["position"] == p]
        if p in lv and len(sub):
            line += f"{lv[p]:>11.1f}{sub['projected_points'].max()-lv[p]:>11.1f}"
        else:
            line += f"{'--':>11}{'--':>11}"
    print(line)
