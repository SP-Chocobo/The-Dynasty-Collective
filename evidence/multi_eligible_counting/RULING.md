# 2.6's counting half, BUILT — and the blast radius is larger than the ruling was sized on

The owner ruled **assignment-based** demand, having been told it "reprices every IDP board". Built and
measured, it reprices **every board**, including offence-only ones, and on `12T_ppr_SF` it **changes the
engine's own top pick at the start of round 5** — a board holding zero multi-eligible players.

That is not a reason to unpick the ruling: the mechanism is the one that was ruled on, and both halves
of what it corrects are the same defect (a census cannot say which slot a pick occupies). It is a reason
the owner should see this page before anything re-certifies prices over it, and a revert is one commit.

## How it was measured

`probe_ruling_ab.py`: ONE process, ONE code version, one thing toggled. The "before" arm rebuilds the
label formula this repair replaced — still computable, because `team_filled_by_position` survives as the
census — and patches it into `compute_draft_board`, so the two boards differ by the counting and by
nothing else. Both arms read the even-split flex share, on both sides, because the split is not what
changed. Checkpoints are at the START of rounds 5, 10 and 15 (48 / 108 / 168 picks in a 12-team draft).

Note against the earlier sizing on this page: the **−7.0 LB** figure was the BY-ELIGIBILITY reading,
which the ruling rejected. What follows is the assignment reading, and it moves demand LESS at LB, in
both directions, and far MORE at the flex positions.

## HEAVY_IDP — the multi-eligibility half

| at | duals held | demand, by label → by assignment | board rows moved (top 40) | top pick |
|---|---|---|---|---|
| round 5 | 1 | *no difference at all* | 0 | unchanged |
| round 10 | 13 | DB **12.0 → 13.0**, LB 10.0 → 9.0, RB 4.0 → 3.33, TE 6.0 → 5.33 | 40 of 40 | unchanged |
| round 15 | 21 | RB 3.33 → **0.0**, TE 3.67 → **0.0**, WR 0.67 → **0.0** | 0 | unchanged |

**DB demand RISES**, and that is the repair working. A `DB/LB` dual counted by label paid down a DB slot
he does not occupy; solved, he sits in an LB slot and the DB slot goes back to being open. The label
reading moved demand in the wrong direction at one of his two positions and the right direction at the
other, which is exactly what a label cannot get right.

Prices: every LB in the top 40 loses **1.00** of `final_score`, every DB gains **1.15**, and
`universal_value` moves by the same amounts — so it is the replacement anchor, not a team term. Order
reshuffles inside the IDP block by at most three places. The top pick never changed on this arm.

## 12T_ppr_SF — the half nobody had sized, and it is the bigger one

Zero multi-eligible players are held at any checkpoint, and the boards still move:

| at | demand, by label → by assignment | rows moved | top pick |
|---|---|---|---|
| round 5 | RB 19.6 → 19.1, TE 17.6 → 17.1, WR 22.6 → 22.1 | 40 of 40 | **Breece Hall → Rashee Rice** |
| round 10 | RB **7.17 → 0.0**, TE **8.60 → 0.0** | 0 | unchanged |
| round 15 | RB 2.87 → 0.0, TE 3.58 → 0.0 | 0 | unchanged |

**A FILLED FLEX SLOT USED TO GO ON DEMANDING.** The label formula asked, per team,
`max(capacity at this position − picks at this position, 0)`, and capacity includes the position's share
of every flex appearance. So a team whose FLEX and SUPER_FLEX were already occupied by a WR and a QB
still reported RB demand for those same slots, because it held fewer RBs than its RB-inclusive capacity.
After nine rounds of a 12-team draft every team can cover every starting slot, and the label formula
still declared **7.17 RB slots and 8.60 TE slots open league-wide**. The assignment says zero, which is
the true answer: the slots are occupied.

That is a second defect inside the same subtraction, with nothing to do with multi-eligibility, and it is
larger. At round 5 the price movement is **RB −8.66, TE −10.04, WR −1.20** of `final_score` across the
whole top 40 — an order of magnitude past the IDP effect — and the engine's top pick flips from Breece
Hall to Rashee Rice (Rice 4th → 1st, Hall 1st → 2nd, Tyler Warren 2nd → 5th).

## What still has to happen

The suite certifies that nothing contradicts itself. It cannot certify that a board which drafts
differently drafts BETTER. **The battery is the instrument for that** — unfilled required slots, points
per seat, the guard bounds — and it has not been run over this. Until it has, this is a correctness
repair with a measured price change and an unmeasured quality effect, and it is stated that way rather
than dressed up.
