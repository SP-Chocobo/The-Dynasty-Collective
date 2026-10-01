"""Second-pass shape tables from run_216_bench_probe.py output: per seat and arm, raw composition,
conditional picks IDENTIFIED by the derivable rule (same NFL team + same position + the team's
top-projected player at that position is owned -- by me: self-insurance handcuff; by another
manager: workload lottery), independent-depth composition, verdicts both ways, the derived band,
lineup, forced, G9."""
import json, sys, collections
from pathlib import Path
import run_draft_battery as rdb
import run_roster_proof as rp
import data_merger as dm, draft_battery as db, draft_room as dr
from run_216_bench_probe import build_league, ordering_verdict

d = Path(sys.argv[1])
players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()
scoring = rdb.scoring_settings_from_capture()
merger = dm.DataMerger()
pos = lambda p: (players_db.get(str(p)) or {}).get("position")
team = lambda p: (players_db.get(str(p)) or {}).get("team")
name = lambda p: " ".join(x for x in ((players_db.get(str(p)) or {}).get("first_name"), (players_db.get(str(p)) or {}).get("last_name")) if x)


def conditional_picks(my_ids, all_rosters, points):
    owner_of = {pid: s for s, ids in all_rosters.items() for pid in ids}
    out = []
    for pid in my_ids:
        p, t = pos(pid), team(pid)
        # RB and QB only: the positions where an NFL team's workload is exclusive, so "behind"
        # means conditional. Applied to WR/TE the same rule labels every NFL WR2 (Coker behind
        # McMillan) a conditional piece, which is not the owner's concept -- measured, first draft.
        if p not in ("RB", "QB") or not t:
            continue
        # the team's top-projected player at this position across the WHOLE pool
        mates = [q for q in points if pos(q) == p and team(q) == t]
        if not mates:
            continue
        top = max(mates, key=lambda q: points[q])
        if top == pid or points[pid] >= points[top]:
            continue
        holder = owner_of.get(top)
        if holder is None:
            continue
        kind = "self_insurance" if holder == owner_of.get(pid) else "workload_lottery"
        out.append({"player": name(pid), "position": p, "team": t, "behind": name(top), "holder": holder, "kind": kind,
                    "points": round(points[pid], 1), "starter_points": round(points[top], 1)})
    return out


print("| format | seat | arm | raw composition | conditional picks (kind) | independent-depth composition | strict raw / independent | tendency raw / independent | bench (pick order) | derived target totals | lineup | forced | cdme eng vs ctl |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for f in sorted(d.glob("*.json")):
    r = json.loads(f.read_text())
    league, _ = build_league(r["format"], scoring)
    merger.set_league_format(db.league_format_hint(league))
    points = rp.scoreable_pool(merger, players_db, league, season)
    for x in r["drafts"]:
        cond = conditional_picks(x["my_ids"], x["all_rosters"], points)
        comp = collections.Counter(x["composition"])
        indep = collections.Counter(comp)
        for c in cond:
            indep[c["position"]] -= 1
        v_raw, v_ind = x["verdict_full_roster"], ordering_verdict(dict(indep))
        fmt = lambda c: " ".join(f"{p}{n}" for p, n in sorted(c.items(), key=lambda kv: -kv[1]) if n)
        cond_text = "; ".join("%s %s behind %s (%s)" % (c["player"], c["position"], c["behind"], c["kind"]) for c in cond) or "-"
        print(f"| {r['format']} | {x['seat']} | {x['arm']} | {fmt(comp)} | {cond_text} | {fmt(indep)} | "
              f"{v_raw['pass_strict']} / {v_ind['pass_strict']} | {v_raw['pass_tendency']} / {v_ind['pass_tendency']} | {fmt(collections.Counter(x['bench_composition_by_pick_order']))} | "
              f"{ {p: v for p, v in sorted(x['band']['target_total'].items())} } | {x['lineup_points']:.0f} | {x['forced']} | {x['g9_engine']['cdme_total_value']} vs {x['g9_control']['cdme_total_value']} |")
