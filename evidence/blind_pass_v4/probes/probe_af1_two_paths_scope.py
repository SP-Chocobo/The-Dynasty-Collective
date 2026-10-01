"""A-F1: is the NARROWED claim true, and does anything still assert the WIDE one?

`draft_room`'s comment was scoped to "AGREE EXACTLY AT A FULL SLATE (`gp == SEASON_GAMES`)".
This reproduces the two paths the way `test_one_fact_two_paths_one_answer` does and reports the
gap at every `gp` the real feed reports, so the scope can be read off the numbers.

Run from the repo root:
    PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 \
        evidence/blind_pass_v4/probes/probe_af1_two_paths_scope.py
"""
import draft_room as dr
import player_universe as pu

REPLACEMENT, TH, POINTS = 100.0, 3.0, 173.0


def universal(status, points, gp):
    """The module's own helper, same shape: haircut path when gp is known, penalty path when not."""
    if gp is None:
        adjusted, basis = points, pu.NO_GAMES_PLAYED if hasattr(pu, "NO_GAMES_PLAYED") else None
        factor, basis = 1.0, None
    else:
        factor, basis = pu.availability_factor(status, gp)
        adjusted = points * factor
    return adjusted - REPLACEMENT + TH + dr.health_penalty(status, basis, adjusted)


print(f"SEASON_GAMES = {pu.SEASON_GAMES}   GAMES_MISSED_PRICED = {pu.GAMES_MISSED_PRICED}")
print()
print(f"{'status':<10}{'gp':>6}{'factor':>10}{'basis':<30}{'universal':>12}{'gap vs gp absent':>18}")
for status in sorted(pu.GAMES_MISSED_PRICED):
    absent = universal(status, POINTS, None)
    for gp in (17.0, 16.0, 15.0, 14.0, 13.0, 12.0):
        factor, basis = pu.availability_factor(status, gp)
        value = universal(status, POINTS, gp)
        print(f"{status:<10}{gp:>6}{factor:>10.4f}{str(basis):<30}{value:>12.2f}"
              f"{value - absent:>18.2f}")
    print(f"{status:<10}{'None':>6}{'--':>10}{'(penalty path)':<30}{absent:>12.2f}{0.0:>18.2f}")
    print()
print("NARROWED CLAIM -- exact agreement at gp == SEASON_GAMES:")
for status in sorted(pu.GAMES_MISSED_PRICED):
    gap = universal(status, POINTS, pu.SEASON_GAMES) - universal(status, POINTS, None)
    print(f"   {status:<10} gap = {gap:+.10f}  {'HOLDS' if abs(gap) < 1e-6 else 'FAILS'}")
print()
print("the gp value the feed actually reports most often for IR is 16; the gap there is the")
print("number the unscoped claim asserts is 0.000.")
