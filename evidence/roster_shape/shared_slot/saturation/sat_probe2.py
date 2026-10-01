"""IS `displaced` COMMON ACROSS POSITIONS ONCE THE SHARED SLOTS SATURATE?

sat_probe refuted the recorded claim (the max-level position IS deducted, from 4 held).
The shape it showed instead: every position's adjustment moved by the SAME 54.90, which
would mean the term stops discriminating between positions the moment the flexes are held.
If that holds, then

    FINAL ~ bpa + adjustment = (proj - level_pos) + (level_pos - displaced) = proj - displaced

and the board prices on RAW PROJECTION with a common offset -- position-blind. Test it on
three different saturating rosters, and print `displaced` per position rather than inferring it.
"""
import draft_room as dr, lineup_optimizer as lo, run_roster_proof as rp

spec = next(s for s in rp.PROOF_FORMATS if s["label"] == "12T_ppr_SF")
league = dr.build_mock_league(teams=spec["teams"], superflex=spec["superflex"], scoring=spec["scoring"],
                              te_premium=spec["te_premium"], dynasty=True)
pos_list = league["roster_positions"]
LEVELS = {"QB": 207.5, "RB": 177.0, "WR": 215.1, "TE": 162.7}
alts = dr.shared_slot_alternatives(LEVELS, pos_list)

def p(pid, v, e):
    return {"id": pid, "value": v, "eligible": {e}}

ROSTERS = {
    "flexes held by WR": [p("QB1",330,"QB"), p("QB2",300,"QB"), p("RB1",310,"RB"), p("RB2",290,"RB"),
                          p("TE1",280,"TE"), p("WR1",320,"WR"), p("WR2",300,"WR"), p("WR3",285,"WR"),
                          p("WR4",270,"WR"), p("WR5",260,"WR")],
    "flexes held by RB": [p("QB1",330,"QB"), p("QB2",300,"QB"), p("RB1",310,"RB"), p("RB2",290,"RB"),
                          p("RB3",275,"RB"), p("RB4",268,"RB"), p("TE1",280,"TE"), p("WR1",320,"WR"),
                          p("WR2",300,"WR")],
    "flexes held by TE": [p("QB1",330,"QB"), p("QB2",300,"QB"), p("RB1",310,"RB"), p("RB2",290,"RB"),
                          p("TE1",280,"TE"), p("TE2",276,"TE"), p("TE3",272,"TE"), p("WR1",320,"WR"),
                          p("WR2",300,"WR")],
}
for label, roster in ROSTERS.items():
    print(f"\n{label}")
    print(f"  {'pos':<4} {'level':>8} {'displaced':>10} {'adjustment':>11}   proj-displaced for a 250.0 player")
    for pos in ("QB", "RB", "WR", "TE"):
        r = lo.displacement_level(roster, pos_list, pos, LEVELS[pos], slot_alternatives=alts)
        bpa = 250.0 - LEVELS[pos]
        print(f"  {pos:<4} {LEVELS[pos]:>8.2f} {r['displaced']:>10.2f} {r['adjustment']:>11.2f}"
              f"   {bpa + r['adjustment']:>10.2f}")
