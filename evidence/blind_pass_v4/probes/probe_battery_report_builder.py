"""`run_draft_battery._battery_report`, field by field: what it counts and what it cannot see.

Measured against the committed BATTERY_REPORT.json and the live matrix.

Run from the repo root:
  PYTHONPATH=. python3 evidence/blind_pass_v4/probes/probe_battery_report_builder.py
"""
import collections
import json
import subprocess

import draft_battery as db
import run_draft_battery as rdb

R = json.load(open("BATTERY_REPORT.json"))
ROWS = R["results"]


def h(n, s):
    print(f"\n{'='*78}\n{n}. {s}\n{'='*78}")


h(1, "`formats` and `independent_formats` are ARM counts, not format counts")
matrix = db.league_matrix(rdb.scoring_settings_from_capture())
by_league = collections.defaultdict(list)
for e in matrix:
    by_league[json.dumps(e["league"], sort_keys=True, default=str)].append(e["label"])
shared = [v for v in by_league.values() if len(v) > 1]
print(f"  report: formats={R['formats']}  independent_formats={R['independent_formats']}")
print(f"  console: \"{R['formats']} formats ({R['independent_formats']} independent), "
      f"{R['picks']} picks, {R['total_findings']} structural findings\"")
print(f"\n  arms in the matrix        : {len(matrix)}")
print(f"  DISTINCT leagues in it    : {len(by_league)}")
print(f"  arms sharing a league with another arm: {sum(len(v) for v in shared)} "
      f"in {len(shared)} groups")
for v in shared[:6]:
    print(f"      {v}")
print(f"      ... ({len(shared)} groups in all)")
print("\n  _battery_report's own comment says so -- \"`formats` is how many arms RAN\" -- but")
print("  the FIELD NAME and the console line both say 'formats', and the number is the")
print("  denominator under every rate the battery produces.")

h(2, "`picks_by_mode` is recorded per arm and read by nothing")
tot = collections.Counter()
zero_up_auto, auto = [], 0
for x in ROWS:
    p = x["provenance"]
    pbm = p.get("picks_by_mode") or {}
    tot["balanced"] += pbm.get("balanced", 0)
    tot["upside"] += pbm.get("upside", 0)
    if p.get("mode") == "auto":
        auto += 1
        if not pbm.get("upside", 0):
            zero_up_auto.append((x["label"], x["rounds"], p.get("upside_from_round")))
print(f"  picks across the run: balanced={tot['balanced']}  upside={tot['upside']}  "
      f"(report `picks`={R['picks']})")
print(f"  upside share: {tot['upside'] / (tot['balanced'] + tot['upside']):.1%}")
print(f"  arms with ANY upside pick: {sum(1 for x in ROWS if (x['provenance'].get('picks_by_mode') or {}).get('upside', 0))} of {len(ROWS)}")
print(f"\n  arms running mode='auto' (the SHIPPED default): {auto}")
print(f"  of those, arms that made ZERO upside picks     : {len(zero_up_auto)}")
for lbl, rd, ufr in zero_up_auto:
    print(f"      {lbl:24s} rounds={rd:<3} upside_from_round={ufr}  -> unreachable")
print("\n  Every one is a draft SHORTER than upside_from_round, so the round-triggered rule")
print("  cannot fire. vds_battery's FORMATS table already states this property for the")
print("  8-round arm (\"the round-triggered upside rule NEVER fires\"); it holds for every")
print("  14-round arm too, and no field of this report says so.")
grep = subprocess.run(["git", "grep", "-l", "picks_by_mode", "--",
                       "run_draft_battery.py", "run_vds_battery.py"],
                      capture_output=True, text=True).stdout.split()
print(f"\n  report builders that read `picks_by_mode`: {grep or 'NONE'}")

h(3, "`constant_axes` cannot see the axes `provenance` records")
fa = R["format_axes"]
print(f"  constant_axes = {fa['constant_axes']}   axes_source={fa['axes_source']}  "
      f"arms={fa['arms']}")
print(f"  axes it ranges over ({len(fa['axes'])}): {sorted(fa['axes'])}")
print("\n  advertised_format_axes(league) = league_format_hint(league) + roster_shape_axes(league)")
print("  -- purely league-derived. The per-ARM parameters run_battery forwards are not in it:")
for key in ("mode", "upside_rule", "opponent_noise", "pool_scope", "priced_from",
            "sleeper_basis", "upside_from_round"):
    dist = collections.Counter(str(x["provenance"].get(key)) for x in ROWS)
    flag = "  <-- CONSTANT across every arm" if len(dist) == 1 else ""
    print(f"      provenance.{key:18s} {dict(dist)}{flag}")
print("\n  #241's lesson was \"an axis that fails to vary is also a coverage hole ... a constant")
print("  axis should announce itself the way a duplicate arm does\". Two of the three strategy")
print("  axes are constant across all 53 arms and `constant_axes` is [].")
