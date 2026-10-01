# PRE-REGISTRATION — what determines whether a tight end enters the selected 312?

Written and committed BEFORE the probe is run. The forks below are stated before any number
is read. Nothing here proposes a fix, and no engine source is touched.

## Why this question and not the other one

RESIDUAL5 established that composition is invariant under pick-order permutation while
recipient assignment scrambles ~90%. The hoarder/starver bifurcation therefore cannot be the
cause of the aggregate 32.4% TE share, and is set aside as a separate roster-distribution
phenomenon unless something shows it feeding back into aggregate selection.

So the question is the aggregate one: **what decides that a tight end is among the 312 taken
at all?**

## State of the upstream evidence, before measuring

| document | status under the corrected doctrine |
|---|---|
| FINDING_01 | **RETRACTED.** Banner on the file: every figure computed over the 764-row vendor reconstruction, not the 6,595-player capture. Its headline was withdrawn twice over in CORRECTION_wrong_universe.md. Not usable. |
| FINDING_02 / 03 / 04 | **Numbers withdrawn**, same banner, same reason. Mechanisms "may survive re-measurement". |
| FINDING_05 | **Partly valid.** The engine-vs-human comparison (32.4% vs 15.5%) is measured on the real universe on both sides and stands. **But its own table's "priced pool offers" row is the withdrawn vendor pool** (TE 18.6%), and its headline "1.74x the pool's own share" is computed from it. CORRECTION_wrong_universe says "FINDING_05 is untouched" — that is true of the human comparison and FALSE of the pool row inside FINDING_05's table. |
| PHASE4_ABLATION_RESULT | **Valid.** Real universe, clean 168/168 control, one toggle. Its numbers stand. But it identifies a SCOPE mechanism (46% of this draft is roster-blind), not an aggregate-selection mechanism, and leaves 37% of the excess unattributed. |

**And one mechanism claim is now inconsistent with something established later.** FINDING_05
says the cause is that "TE's own replacement level COLLAPSES ... VOR measured against a
collapsed level stays positive for every remaining body." That was written before the
cancellation identity: `bpa + displacement_adj = points - displaced`, so the level cancels
inside each player wherever the displacement term is non-zero. A collapsed TE level raises
`bpa` and lowers `displacement_adj` by exactly the same amount. **FINDING_05's stated
mechanism cannot be the operative one for those candidates.**

What survives that identity is FINDING_04's mechanism, because it is a claim about
`displaced` rather than about the level: the non-positive rule caps a tight end's deduction at
`level_TE - my_own_TE` instead of letting it reach the flex alternative. In `displaced` terms,
TE's bar can be my own weak TE1 while a receiver's bar is the flex phantom. Observed in
`residual3_raw.json`: `displaced` is 217.75 (the phantom) on 103 of 144 rows and 200.90 /
209.20 / 211.65 / 212.03 / 213.93 on the rest — a bar up to **16.85 points lower**. That is a
candidate, not a finding, and its numbers are all from the withdrawn set.

**Conclusion: the existing evidence does NOT resolve the aggregate-selection mechanism.** It
names one surviving candidate whose figures must be re-measured.

## The experiment

The smallest thing that separates "the ordering the pool already has" from "something the
valuation stack adds" — one opening board build, no draft, no engine modification.

**Observable.** The positional composition of the **top 312 rows of the opening priced board,
ranked by production's own `_points` column** — the season projection under this league's
scoring that `bpa = points - level` is built from. Reported beside the same cut ranked by
opening `final_score`, and beside the 312 actually drafted.

**Population.** The #201/#204 recipe exactly: `build_players_db_from_capture()` (6,595),
`season_projections_from_capture()`, `league_format_hint` derived from the league,
`SLEEPER_BASIS_SEASON_SUM`, no picks. Universe assertion: every one of the 312 drafted
player_ids must appear on this board, or the fixture is wrong and nothing is reported.

**Forks, stated now.** Let T = tight ends in the top 312 by `_points`. Drafted was 101;
twelve humans took 48.

- **FORK A — the pool's own ordering.** T in [91, 111] (within ~10% of 101). The aggregate
  composition is essentially the projection ordering; every valuation term is a near-no-op at
  the aggregate. The seam is UPSTREAM OF THE WHOLE VALUATION STACK — in projections and
  scoring. Every valuation-side hypothesis for the aggregate dies, including FINDING_04's.
- **FORK B — valuation adds it.** T <= 60. The projection ordering does not produce the excess;
  the valuation stack does. FINDING_04's surviving candidate is promoted to prime suspect and
  gets its own pre-registered re-measurement.
- **FORK C — both.** T in [61, 90]. Report the split as measured; neither account is sufficient
  alone.

**What this does NOT establish, whatever it returns.** A composition match is not proof of
mechanism — twelve seats also remove players from the pool, so the drafted 312 is not the
top-312 of anything by identity. The claim on offer is about COMPOSITION only, and the overlap
count `|top312_by_points ∩ drafted312|` is reported beside it so the difference is visible.

**And it does not license calling anything defective.** A scoring rulebook that ranks tight
ends highly is this league's actual rulebook (0.75/reception TE premium, first-down scoring).
If FORK A lands, the finding is "the aggregate is the pool's ordering" — an explanation, not
a verdict. Whether a superflex league with a TE premium SHOULD yield 101 tight ends is the
owner's question, not a measurement's.

---

# ADDENDUM — pre-registration for the open inference in RESULT_aggregate_selection.md

Written before the probe exists. Testing MY OWN published claim, which I explicitly marked as
an inference rather than a measurement.

## The claim under test

`RESULT_aggregate_selection.md` states, and flags as unmeasured:

> The cancellation identity says `bpa + displacement_adj = points - displaced`, so mid-draft, on
> a filled roster, the level cancels and the decision is `points - displaced`. Yet the final
> composition matches the *opening* bpa ranking, where the level does not cancel, to within three
> players. Those two facts are compatible — `displaced >= level` always, so the displacement term
> can only lower a candidate below his bpa, and the ordering survives if it lowers each position
> by a similar amount — **but that compatibility is an inference and has not been measured.**

If that inference is wrong, the "one subtraction decides it" account is incomplete: something
mid-draft would have to be restoring an ordering that displacement had disturbed.

## The experiment

Two mid-draft board states from the production draft already on disk (`ff_draft.json`), rebuilt
with the #201/#204 recipe: **pick 100 and pick 150**. Both are in rounds 1–14, so `mode="auto"`
is BALANCED there and the displacement term is live — this is production, not a forced arm.
The board is built for the seat actually on the clock, from that seat's actual accumulated
roster. Raw saved first; emitted columns asserted.

**Observable.** At each state, take K = the number of picks remaining in the draft, and compare
the positional composition of the top K by `bpa` against the top K by
`bpa + displacement_adj` (= `points - displaced`, the mid-draft decision quantity), over the
priced rows still available.

**Forks, stated now.** Let D = (TE count in the top-K by `points - displaced`) − (TE count in
the top-K by `bpa`), at each state.

- **FORK N — order-neutral, my inference holds.** |D| <= 3 at both states, and no position moves
  by more than 5. Displacement lowers positions comparably; the opening-board ordering survives
  it; the published account stands as written.
- **FORK P — displacement AMPLIFIES the TE lead.** D >= +4 at either state. Then the opening
  subtraction is not the whole story: a second, roster-side effect pushes the same way, and the
  RESULT document understates the mechanism.
- **FORK Q — displacement OPPOSES the TE lead.** D <= −4 at either state. Then mid-draft
  valuation partially corrects what the opening board did, and something not yet identified
  restores the 101. The published account would need a correction, and this fork is the one that
  would reopen the aggregate question.

**Reported regardless of fork:** the per-position mean and median `displacement_adj`, the count
of rows where it is exactly 0.0, and the reconciliation `bpa + displacement_adj` against
`points - displaced` computed independently.

**This does not license a repair whatever it returns**, and it does not bear on whether the
contract is desirable — it only checks whether a sentence I published is true.
