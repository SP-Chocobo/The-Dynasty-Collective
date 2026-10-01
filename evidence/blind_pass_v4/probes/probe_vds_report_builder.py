"""`run_vds_battery._report`, field by field: can each one fire, and does it mean its name?

Five questions, each measured against the LAST COMMITTED VDS RUN'S OWN SERIALIZED ARMS rather
than a hand-built dict -- because the hand-built dict is itself one of the findings below
(engine-measurement: "A probe that hand-builds an input must build it the way production builds
it. A missing key is not a missing value").

Run from the repo root:
  PYTHONPATH=. python3 evidence/blind_pass_v4/probes/probe_vds_report_builder.py
"""
import copy
import glob
import json
import time

import draft_battery as db
import resume_join
import run_vds_battery as rvb
import test_report_fields_mean_their_names as t
import vds_battery as vb

COMMITTED = sorted(glob.glob("evidence/batteries/VDS_*.json"))[-1]
RAW = json.load(open(COMMITTED))
ROWS = RAW["results"]


def h(n, s):
    print(f"\n{'='*78}\n{n}. {s}\n{'='*78}")


def q1_control_absent():
    h(1, 'INERT_ARMS when a format\'s CONTROL arm is not in `results`')
    print("`controls` is keyed off the control arm's row; a format with no control arm is")
    print("`continue`d, so no arm in it can be judged inert -- and main() then prints")
    print('"No inert arms: every strategy changed the draft in every format."\n')
    full = rvb._report(RAW["universe"], copy.deepcopy(ROWS), time.time(), complete=True)
    print(f"  all 36 arms          INERT_ARMS = {full['INERT_ARMS']}")
    print(f"                       inert_arm_count={full['inert_arm_count']}  "
          f"effective_arms={full['effective_arms']}")

    no_ctrl = [r for r in ROWS if r.get("strategy") != vb.CONTROL_STRATEGY]
    rep = rvb._report(RAW["universe"], copy.deepcopy(no_ctrl), time.time(), complete=True)
    print(f"\n  the SAME arms, controls dropped ({len(no_ctrl)} arms, "
          f"including both arms the full run calls inert):")
    print(f"                       INERT_ARMS = {rep['INERT_ARMS']}")
    print(f"                       inert_arm_count={rep['inert_arm_count']}  "
          f"effective_arms={rep['effective_arms']}  (= arms_run)")
    print(f"  -> main() would print: "
          f'"{"INERT ARMS -- ..." if rep["INERT_ARMS"] else "No inert arms: every strategy changed the draft in every format."}"')
    print("  The two arms the full run proves inert are STILL in this set. The absence of a")
    print("  control is reported as the presence of an effect.")


def q2_code_table_not_the_run():
    h(2, "`seed`, `top_k_swept`, `strategies` and `formats` describe the CODE, not the run")
    rep = rvb._report(RAW["universe"], copy.deepcopy(ROWS), time.time(), complete=True)
    print(f"  as shipped: seed={rep['seed']}  top_k_swept={rep['top_k_swept']}")
    real_seed, real_k = vb.VDS_SEED, vb.VDS_TOP_K
    try:
        vb.VDS_SEED, vb.VDS_TOP_K = 11111111, (99, 100)
        moved = rvb._report(RAW["universe"], copy.deepcopy(ROWS), time.time(), complete=True)
        print(f"  constants changed, THE SAME ARMS re-reported: "
              f"seed={moved['seed']}  top_k_swept={moved['top_k_swept']}")
        print(f"  arms identical? {moved['results'] == rep['results']}")
    finally:
        vb.VDS_SEED, vb.VDS_TOP_K = real_seed, real_k
    print("\n  Every noisy arm's REAL seed and top_k are now on the row itself, under")
    print("  `provenance.opponent_noise` (draft_battery.audit_trajectory copies the whole")
    print("  DraftTrajectory.config). The report quotes the module constants instead.")
    print(f"  rows in the committed run carrying `provenance`: "
          f"{sum(1 for r in ROWS if 'provenance' in r)} of {len(ROWS)}   "
          f"(that run predates the provenance repair)")


def q3_the_guard_cannot_see_the_real_shape():
    h(3, "The guard policing these fields hand-builds a 5-key arm; the real row has 18")
    fixture = t.TheVDSReportDoesNotCreditInertArms._three_arms_two_inert(None)
    print(f"  fixture arm keys : {sorted(fixture[0])}")
    print(f"  real arm keys    : {sorted(ROWS[0])}")
    print(f"  missing from the fixture: {sorted(set(ROWS[0]) - set(fixture[0]))}")
    print("\n  So no case in that class carries `provenance`, and none uses a NOISY strategy:")
    print(f"  fixture strategies: {[a['strategy'] for a in fixture]}")
    noisy = sorted(n for n, c in vb.STRATEGIES.items()
                   if (c.get('opponent_noise') or {}).get('sharp_seats') == [])
    print(f"  the strategies the sharp_seats exclusion exists for: {noisy}")
    import subprocess
    hits = subprocess.run(["git", "grep", "-l", "sharp_seats", "--", "test_*.py"],
                          capture_output=True, text=True).stdout.split()
    print(f"  test modules mentioning `sharp_seats` at all: {hits or 'NONE'}")


def q4_fingerprint_excludes_is_hand_listed():
    h(4, "`duplicate_arms`' guard asserts a HAND-LIST of four fields, and its arm has 5 keys")
    print(f"  _FINGERPRINT_EXCLUDES          : {sorted(db._FINGERPRINT_EXCLUDES)}")
    print(f"  the guard's synthetic ARM keys : "
          f"{sorted(t.DuplicateArmsSurvivesAResume.ARM)}")
    print(f"  a REAL format-battery arm's keys: "
          f"{sorted(json.load(open('BATTERY_REPORT.json'))['results'][0])}")
    print("\n  The guard's two behavioural cases build arms with no `provenance`, so they pass")
    print("  whatever `provenance` does to the fingerprint. Run them:")
    import unittest
    res = unittest.TextTestRunner(verbosity=0, stream=open("/dev/null", "w")).run(
        unittest.TestLoader().loadTestsFromTestCase(t.DuplicateArmsSurvivesAResume))
    print(f"    DuplicateArmsSurvivesAResume: ran={res.testsRun} "
          f"failures={len(res.failures)} errors={len(res.errors)}")
    real_rows = json.load(open("BATTERY_REPORT.json"))["results"]
    print(f"    ...while duplicate_arms over the real 53 rows -> {db.duplicate_arms(real_rows)}")
    print("    and the pair 12T_ppr / 12T_ppr_mode_balanced is byte-identical in every")
    print("    audited quantity (see probe_battery_duplicate_arms.py).")


def q5_two_readers_of_which_strategy():
    h(5, "Two readers of 'which strategy is this arm' inside one function")
    print("  `inert` reads row['strategy'] / row['format'];")
    print("  every findings block reads row['label'].partition('__').")
    disagree = [r["label"] for r in ROWS
                if r.get("strategy") != r["label"].partition("__")[2]
                or r.get("format") != r["label"].partition("__")[0]]
    print(f"  arms where the two readers disagree today: {disagree or 'none'}")
    # An arm carried from a report written before audit_trajectory stamped format/strategy.
    older = copy.deepcopy(ROWS)
    for r in older:
        r.pop("format", None)
        r.pop("strategy", None)
        r[resume_join.CARRIED] = True
    rep = rvb._report(RAW["universe"], older, time.time(), complete=True)
    print("\n  the same arms with `format`/`strategy` removed -- the shape a resume carries from")
    print("  a report written before audit_trajectory stamped them:")
    print(f"    INERT_ARMS                 = {rep['INERT_ARMS']}")
    print(f"    findings_by_strategy keys  = {sorted(rep['findings_by_strategy'])}")
    print(f"    STRATEGY_SPECIFIC_FINDINGS = {rep['STRATEGY_SPECIFIC_FINDINGS']}")
    print("  The label-based reader still works; the inert detector goes silent, and the")
    print("  report says 'No inert arms' rather than 'I could not tell'.")


for fn in (q1_control_absent, q2_code_table_not_the_run, q3_the_guard_cannot_see_the_real_shape,
           q4_fingerprint_excludes_is_hand_listed, q5_two_readers_of_which_strategy):
    try:
        fn()
    except Exception as exc:
        print(f"\n  ARM FAILED: {type(exc).__name__}: {exc}")
