"""`duplicate_arms` lost its only live finding when `provenance` joined the arm row.

`_FINGERPRINT_EXCLUDES` exists so that fields describing the RUN rather than the arm's content
cannot make two identical arms fingerprint differently. Its own comment records both occasions
that was learned: `seconds` ("including it would make every arm unique and the check vacuous")
and then `produced_at_commit`/`carried_forward` ("they describe the RUN, not the arm's content").

`audit_trajectory` now also records `provenance` -- the whole `DraftTrajectory.config` minus the
label, i.e. mode, pool_scope, opponent_noise, sleeper_basis, priced_from, upside_rule,
upside_from_round, picks_by_mode and pick_order. That is a run descriptor by the same definition,
and it is NOT excluded.

Measured here against the committed reports, and then re-run in process with `provenance`
excluded, so the cause is demonstrated rather than argued.

Run from the repo root:
  PYTHONPATH=. python3 evidence/blind_pass_v4/probes/probe_battery_duplicate_arms.py
"""
import collections
import glob
import json

import draft_battery as db


def main() -> None:
    print("THE RECORD, oldest first -- `provenance` arrives with the current run:\n")
    files = sorted(glob.glob("evidence/batteries/BATTERY_*.json")) + ["BATTERY_REPORT.json"]
    for f in files:
        try:
            r = json.load(open(f))
        except Exception as exc:
            print(f"  {f}: unreadable ({exc})")
            continue
        rows = r.get("results", [])
        if not rows:
            continue
        dupes = [f"{d['label']} == {d['duplicates']}" for d in (r.get("duplicate_arms") or [])]
        print(f"  {f.split('/')[-1]:52s} formats={r.get('formats'):>3} "
              f"independent={r.get('independent_formats'):>3}  "
              f"provenance_on_rows={sum(1 for x in rows if 'provenance' in x):>3}/{len(rows):<3} "
              f"dupes={dupes or '[]'}")

    rows = json.load(open("BATTERY_REPORT.json"))["results"]

    print("\n\nARE ANY TWO ARMS STILL IDENTICAL IN WHAT WAS MEASURED?")
    by_seq = collections.defaultdict(list)
    for x in rows:
        by_seq[tuple(x["pick_sequence"])].append(x["label"])
    pairs = [v for v in by_seq.values() if len(v) > 1]
    print(f"  arms sharing a byte-identical pick_sequence: {pairs}")
    for group in pairs:
        a = next(x for x in rows if x["label"] == group[0])
        b = next(x for x in rows if x["label"] == group[1])
        differing = sorted(k for k in set(a) | set(b)
                           if json.dumps(a.get(k), sort_keys=True, default=str)
                           != json.dumps(b.get(k), sort_keys=True, default=str))
        print(f"  {group[0]} vs {group[1]}: the ONLY keys that differ are {differing}")
        pa, pb = a.get("provenance", {}), b.get("provenance", {})
        for k in sorted(set(pa) | set(pb)):
            if pa.get(k) != pb.get(k) and k != "pick_order":
                print(f"      provenance.{k}: {pa.get(k)!r}  vs  {pb.get(k)!r}")

    print("\n\nTHE DETECTOR, AS SHIPPED AND WITH `provenance` EXCLUDED (one process, one code")
    print("version, toggling the single thing under test):")
    real = db._FINGERPRINT_EXCLUDES
    print(f"  as shipped   excludes={sorted(real)}")
    print(f"               duplicate_arms -> {db.duplicate_arms(rows)}")
    try:
        db._FINGERPRINT_EXCLUDES = frozenset(real | {"provenance"})
        print(f"  + provenance excludes={sorted(db._FINGERPRINT_EXCLUDES)}")
        print(f"               duplicate_arms -> {db.duplicate_arms(rows)}")
    finally:
        db._FINGERPRINT_EXCLUDES = real
    print(f"  restored     duplicate_arms -> {db.duplicate_arms(rows)}")


if __name__ == "__main__":
    main()
