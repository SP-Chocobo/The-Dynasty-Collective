"""Step 2/3: what does the engine's OWN denominator say round 15 is?

The constant's comment calls the trigger state "a deep bench/waiver-fringe pick".
lineup_optimizer.bench_capacity counts this league's BN slots straight from roster_positions --
the denominator that phrase needs. This asks, per league available in the repo, where the
starters end, where the bench ends, and where round 15 falls between them.

Pure arithmetic over roster_positions and production's own two functions. No draft, no board,
no tuning. Run from the repo root with PYTHONPATH=.
"""
import json
import draft_room as dr, lineup_optimizer as lo

FF = json.load(open("data/league_captures/fourth_and_forever.json"))["roster_positions"]
# The league the repo's own upside-mode test uses, verbatim from
# test_draft_room.test_auto_mode_switches_to_upside_exactly_at_the_documented_round.
TESTL = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX"] + ["BN"] * 13
# A battery format, built by production's own builder.
BAT = dr.build_mock_league(base_scoring={}, teams=12, superflex=False, scoring="ppr",
                           te_premium=False, dynasty=True)["roster_positions"]

print(f"UPSIDE_MODE_DEFAULT_ROUND = {dr.UPSIDE_MODE_DEFAULT_ROUND}\n")
print(f"{'league':22}{'starting':>9}{'bench':>7}{'other':>7}{'rounds':>8}"
      f"{'bench spans rounds':>20}{'round 15 is':>26}")
for label, rp in (("Fourth and Forever", FF), ("repo upside-mode test", TESTL),
                  ("battery 12T_ppr", BAT)):
    starting = len(lo.slots_from_roster_positions(rp))
    bench = lo.bench_capacity(rp)
    other = len(rp) - starting - bench
    rounds = len(rp)                      # draft_battery sets rounds = len(roster_positions)
    lo_r, hi_r = starting + 1, starting + bench
    k = dr.UPSIDE_MODE_DEFAULT_ROUND
    if k <= starting:
        where = f"starter #{k}"
    elif k <= hi_r:
        where = f"bench body {k - starting} of {bench}"
    elif k <= rounds:
        where = f"past the bench (IR/taxi)"
    else:
        where = "NEVER REACHED"
    print(f"{label:22}{starting:>9}{bench:>7}{other:>7}{rounds:>8}"
          f"{f'{lo_r}-{hi_r}':>20}{where:>26}")

print("\nthe same question asked as a FRACTION of the bench this league gives you:")
for label, rp in (("Fourth and Forever", FF), ("repo upside-mode test", TESTL),
                  ("battery 12T_ppr", BAT)):
    starting = len(lo.slots_from_roster_positions(rp))
    bench = lo.bench_capacity(rp)
    k = dr.UPSIDE_MODE_DEFAULT_ROUND
    if bench and starting < k <= starting + bench:
        frac = (k - starting) / bench
        print(f"   {label:22} round 15 sits {frac:5.0%} of the way through the bench")
    else:
        print(f"   {label:22} round 15 is not a bench pick in this league")
