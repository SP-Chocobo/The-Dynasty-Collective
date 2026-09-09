"""SATURATION. Does the max-level position EVER get deducted at a shared slot?

The claim under test, recorded in DIALLED_IN.md and NOT yet verified past four held:
"the position whose replacement level is the maximum is NEVER deducted at a shared slot,
on any roster state, no matter how many of that position are already held."

Four held against five reachable slots leaves an OPEN slot, so +0.00 there proves nothing
about saturation. This adds receivers until every WR-reachable slot is held by a real
player who beats the alternative, and reads the adjustment at each step.
"""
import draft_room as dr, lineup_optimizer as lo, run_roster_proof as rp

spec = next(s for s in rp.PROOF_FORMATS if s["label"] == "12T_ppr_SF")
league = dr.build_mock_league(teams=spec["teams"], superflex=spec["superflex"], scoring=spec["scoring"],
                              te_premium=spec["te_premium"], dynasty=True)
rp_pos = league["roster_positions"]
print("roster_positions:", rp_pos)
slots = lo.slots_from_roster_positions(rp_pos)
print("slots:", [(s["slot_id"], sorted(s["eligible"])) for s in slots])

LEVELS = {"QB": 207.5, "RB": 177.0, "WR": 215.1, "TE": 162.7}
alts = dr.shared_slot_alternatives(LEVELS, rp_pos)
print("shared alternatives:", alts)
print()

# Real receivers, every one comfortably above the shared alternative (215.1).
wr_values = [320.0, 300.0, 285.0, 270.0, 260.0, 250.0, 240.0, 235.0, 230.0, 225.0]
base = [{"id": "QB1", "value": 330.0, "eligible": {"QB"}},
        {"id": "QB2", "value": 300.0, "eligible": {"QB"}},
        {"id": "RB1", "value": 310.0, "eligible": {"RB"}},
        {"id": "RB2", "value": 290.0, "eligible": {"RB"}},
        {"id": "TE1", "value": 280.0, "eligible": {"TE"}}]

print(f"{'#WR held':>8} | {'WR adj':>8} {'WR disp':>8} | {'RB adj':>8} | {'TE adj':>8}")
for n in range(0, len(wr_values) + 1):
    roster = base + [{"id": f"WR{i+1}", "value": v, "eligible": {"WR"}} for i, v in enumerate(wr_values[:n])]
    row = []
    for pos in ("WR", "RB", "TE"):
        r = lo.displacement_level(roster, rp_pos, pos, LEVELS[pos], slot_alternatives=alts)
        row.append(r)
    print(f"{n:>8} | {row[0]['adjustment']:>8.2f} {row[0]['displaced']:>8.2f} | "
          f"{row[1]['adjustment']:>8.2f} | {row[2]['adjustment']:>8.2f}")
