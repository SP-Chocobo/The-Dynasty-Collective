"""WHY each of the four newly-silent full-tier tests asserts nothing.

`assertion_execution` says a test ran and executed no assertion. It does not say whether that is
legitimate (the contract IS "does not raise") or a hole (the assertion sits behind a condition
the fixture never reaches). The record `ASSERTION_EXECUTION.json` exists to carry that judgement
per test, and holds 14 entries -- none of these four.

This prints the SUBPOPULATION each test's guard is gated on, so the judgement is measured rather
than read off the source.

Run from the repo root (full tier -- builds real boards, minutes):
  PYTHONPATH=. python3 evidence/blind_pass_v4/probes/probe_silent_tests_why.py
"""
import collections
import unittest


def arm_a() -> None:
    """test_a_roster_the_solver_never_saw_whole: the assertion is gated on
    `before["basis"] == EXPOSURE_MEASURED`. The registered invariant for EXPOSURE_ROSTER_PARTIAL
    states its evidence as "32 cells relabelled ... and 2 from `measured`". If this fixture has
    none, the test pinning those 2 has never examined one."""
    import lineup_optimizer as lo
    import test_a_roster_the_solver_never_saw_whole as m
    cls = m.OnRealDataItMovesNoPriceTests
    cls.setUpClass()
    rows = list(cls._relabelled(cls))
    census = collections.Counter(before["basis"] for _r, _p, before, _a in rows)
    print(f"  relabelled cells                : {len(rows)}")
    print(f"  their PREVIOUS basis, counted   : {dict(census)}")
    print(f"  gated subpopulation (== {lo.EXPOSURE_MEASURED!r}): "
          f"{census.get(lo.EXPOSURE_MEASURED, 0)}")


def arm_d() -> None:
    """test_one_percentile_pair_one_conversion_rate: the assertion is gated on a tied block that
    contains a row with an absent projection. Its SIBLING test carries an explicit
    `assertGreater(checked, 0)` non-vacuity floor; this one does not."""
    import test_one_percentile_pair_one_conversion_rate as m
    cls = m.TheFlatRegionHasAStatedConventionTests
    cls.setUpClass()
    blocks = sum(len(list(cls._tied_blocks(board))) for _r, board in cls.boards)
    with_absent = 0
    for _rounds, board in cls.boards:
        for block in cls._tied_blocks(board):
            if any((row.get("projected_points") is None
                    or row.get("projected_points") != row.get("projected_points"))
                   for row in block):
                with_absent += 1
    print(f"  tied blocks across the boards   : {blocks}")
    print(f"  blocks holding an ABSENT value  : {with_absent}  (the gated subpopulation)")


for name, fn in (("A  test_the_cells_that_WERE_measured_carried_a_false_label_at_no_point", arm_a),
                 ("D  test_an_absent_projection_does_not_jump_the_queue", arm_d)):
    print(f"\n{name}")
    try:
        fn()
    except Exception as exc:                 # an arm that cannot run is reported, never skipped
        print(f"  COULD NOT MEASURE: {type(exc).__name__}: {exc}")
