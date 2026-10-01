"""Does the new ordering produce rosters that SCORE MORE, or only rosters shaped as asked?

The treatment arm gives up a mean 35 tav per pick. That is expected in direction -- tav is the
key this repair deprecated -- but the magnitude has to answer for itself, and the only answer
that counts is the lineup a chair can actually field.

THE RULER, and why it is not the battery's own starter_value. roster_strength's docstring says
plainly that starter_value over universal_value ranks POSITIONAL BREADTH, not quality: an asset
LEVEL is not a rate, 83.8% of a pool's universal_value is negative, and optimize_lineup has no
"leave it empty" move, so a thin roster is forced to start deep negatives. Summing projected
POINTS over the optimal legal lineup asks the quality question that number cannot.

Uses the engine's own optimizer rather than a hand-rolled lineup solve.

Run from the REPO ROOT.
"""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
import json, statistics
import draft_battery as dbat, run_draft_battery as rdb, player_universe as pu
import lineup_optimizer as lo

SC = "/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/"
players_db, _ = rdb.build_players_db_from_capture()
scoring = rdb.scoring_settings_from_capture()
arm = next(a for a in dbat.league_matrix(scoring) if a["label"] == "12T_ppr_K_DEF")
league = arm["league"]
slots = lo.slots_from_roster_positions(league["roster_positions"])

# The same projected_points the curves were read from, taken off the stored snapshots so both
# arms are scored on ONE ruler built from the pre-draft pool, never from each arm's own board.
points = {}
for name in ("traj_control.json", "traj_treatment.json"):
    for p in json.load(open(SC + name)):
        for c in (p["snapshot"].get("candidates") or []):
            if c.get("proj") is not None:
                points.setdefault(str(c["id"]), float(c["proj"]))

print("one shared ruler: %d players carry a projection\n" % len(points))
print("%-12s%14s%14s%14s%12s" % ("arm", "mean starters", "median", "worst chair", "best chair"))
out = {}
for name, label in (("traj_control.json", "before"), ("traj_treatment.json", "after")):
    picks = json.load(open(SC + name))
    rosters = {}
    for p in picks:
        rosters.setdefault(str(p["roster_id"]), []).append(str(p["chosen"]))
    totals = []
    for rid, pids in rosters.items():
        entries = []
        for pid in pids:
            pos = pu.player_position(players_db.get(pid) or {})
            if not pos:
                continue
            entries.append({"id": pid, "value": points.get(pid, 0.0), "eligible": {pos}})
        totals.append(lo.optimize_lineup(entries, slots)["total_value"])
    out[label] = totals
    print("%-12s%14.1f%14.1f%14.1f%12.1f" % (
        label, statistics.fmean(totals), statistics.median(totals), min(totals), max(totals)))

d = statistics.fmean(out["after"]) - statistics.fmean(out["before"])
print("\nmean starting-lineup projection, after minus before: %+.1f points (%.1f%%)"
      % (d, 100 * d / statistics.fmean(out["before"])))
print("chairs improved: %d of 12" % sum(1 for a, b in zip(sorted(out["after"]), sorted(out["before"])) if a > b))
