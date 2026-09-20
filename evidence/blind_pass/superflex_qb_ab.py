"""Does the superflex QB drop COST POINTS, or only change roster shape?

Measured: minimum QB per roster was 2 in every superflex arm before the acting_now ordering
and is 1 in nine of eleven after. That is a shape change. Whether it is a REGRESSION depends
on the lineup those rosters can field, and SUPER_FLEX accepts a skill player -- so a roster
with one QB is legal and might be fine.

ONE PROCESS, ONE CODE VERSION, toggling only the ordering key -- the only honest A/B (see the
engine-measurement skill). The control arm restores the previous order by making every
candidate's acting_now_value absent, which drops every row into _acting_now_order's unmeasured
block where it is ranked by team_acquisition_value: exactly the key this repair replaced.

Ruler is projected POINTS over the optimal legal lineup, not universal_value -- roster_strength's
own docstring records why summing an asset LEVEL ranks positional breadth rather than quality.

Run from the REPO ROOT.
"""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
import collections, statistics
import data_merger as dm, draft_room as dr, draft_battery as dbat, run_draft_battery as rdb
import draft_simulation as dsim, pick_synthesis as ps, player_universe as pu
import lineup_optimizer as lo

ARM = sys.argv[1] if len(sys.argv) > 1 else "10T_ppr_SF"
merger = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture(); scoring = rdb.scoring_settings_from_capture()
arm = next(a for a in dbat.league_matrix(scoring) if a["label"] == ARM)
league, teams, rounds = arm["league"], arm["teams"], arm["rounds"]
merger.set_league_format(dbat.league_format_hint(league))
order = [(i % teams) + 1 if (i // teams) % 2 == 0 else teams - (i % teams)
         for i in range(teams * rounds)]
slots = lo.slots_from_roster_positions(league["roster_positions"])
print("arm %s  teams=%d rounds=%d  slots=%d\n" % (ARM, teams, rounds, len(slots)))

real = ps.acting_now_value
def run(label, disabled):
    ps.acting_now_value = (lambda *a, **k: None) if disabled else real
    traj = dsim.simulate_full_draft(merger, players_db, league, order, mode="auto",
                                    sleeper_projections=season,
                                    sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    ps.acting_now_value = real
    return label, traj

runs = [run("BEFORE (tav order)", True), run("AFTER (acting_now)", False)]

# ONE ruler, built from both arms' stored snapshots, applied identically to each.
points = {}
for _, traj in runs:
    for rec in traj.picks:
        for c in (rec.snapshot.get("candidates") or []):
            if c.get("proj") is not None:
                points.setdefault(str(c["id"]), float(c["proj"]))

print("%-22s%10s%10s%12s%14s%12s" % ("arm", "QB mean", "QB min", "starters", "median", "worst"))
for label, traj in runs:
    rosters = collections.defaultdict(list)
    for rec in traj.picks:
        rosters[str(rec.roster_id)].append(str(rec.chosen_player_id))
    qbs, totals, missing = [], [], 0
    for rid, pids in rosters.items():
        entries = []
        n_qb = 0
        for pid in pids:
            pos = pu.player_position(players_db.get(pid) or {})
            if not pos:
                continue
            n_qb += pos == "QB"
            if pid not in points:
                missing += 1
            entries.append({"id": pid, "value": points.get(pid, 0.0), "eligible": {pos}})
        qbs.append(n_qb)
        totals.append(lo.optimize_lineup(entries, slots)["total_value"])
    print("%-22s%10.2f%10d%12.1f%14.1f%12.1f" % (
        label, statistics.fmean(qbs), min(qbs), statistics.fmean(totals),
        statistics.median(totals), min(totals)))
    if missing:
        print("      (%d rostered players carry no projection -- entered at 0.0)" % missing)

d = statistics.fmean([t for _, tr in [runs[1]] for t in [0]]) if False else None
