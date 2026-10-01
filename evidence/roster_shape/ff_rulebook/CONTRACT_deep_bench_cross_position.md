# The semantic contract of cross-position VOR in the deep-bench regime

A documentary investigation. **No engine source read for behaviour, no probe run, no measurement
taken.** Every citation below is from a production docstring, `CDME_CONTRACTS.md`, or a committed
test. Two mechanical facts are confirmed by reading call sites, and are marked as such.

The 101-TE result is used ONLY to say WHERE the aggregate is decided (established at 1abbd37 and
authorized). It is not used anywhere below as evidence that anything is wrong.

---

## Q1 — what does the contract say the positional replacement level is intended to MEAN?

One definition, stated twice, consistently.

`CDME_CONTRACTS.md` ("Proposed contract — replacement at demand exhaustion", since implemented):

> **Domain.** `replacement_levels[p]` is defined only while position `p` has at least one
> unfilled league-wide starter slot. Inside that domain it means: *the value of the `D`-th best
> player in the pre-draft field*, `D = round(num_teams × starter_slot_counts[p])` — **the player
> a team is guaranteed to be able to start without spending a premium pick.**

`draft_room.replacement_levels`' live docstring:

> Per position, this pool's value_col at the player sitting at replacement rank within the
> REMAINING pool. **The rank target is remaining_starter_demand** — how many starting slots at
> that position are still unfilled ACROSS THE LEAGUE, summed per team.

**The level is a STARTER quantity end to end, and that is not incidental — it is the definition.**

*Mechanical confirmation (read, not measured):* `compute_draft_board` calls
`replacement_levels(proj_pool, "_points", roster_positions, num_teams, starter_demand, ...)` at
`draft_room.py:2916`, where `starter_demand = remaining_starter_demand(...)` (`:2844`). The
module DOES have bench-demand machinery — `positional_bench_appetite` (`:1724`),
`estimated_bench_demand` (`:1781`) — and **none of it reaches the level.** Those feed
`horizon_replacement` and `expected_positional_consumption` only. There is no bench term in the
anchor by construction.

## Q2 — does the contract authorize comparing VOR ACROSS positions?

**Yes — explicitly, deliberately, and with evidence.** This is not an accident of implementation.

> **The correct normalization is a common cross-positional reference: each position's own
> PRE-DRAFT replacement level** — the D-th best player in the full field, D = this league's
> starting slots at that position.

> What makes it cross-positionally valid is the same thing that makes VOR valid: **a
> per-position zero set at league starter depth.**

Measured and recorded in the contract: agreement with CDME's own cross-positional ordering runs
**94–100%** against **69–82%** for raw points. And the alternatives were considered and rejected
by name — within-position normalization ("the best QB and the best TE both normalize to the top
of their own list and become indistinguishable") and percentile-ranking ("a real bug").

It is carried into the live invariants:

> **59.** `bpa` carries production surplus over a positional baseline, on the league's production
> horizon, **expressed so that positions are comparable.** It carries nothing else.

> **Rule 1.** BPA is the stable, **cross-positional** production/value signal over the league's
> horizon.

**A trap I nearly walked into, recorded so nobody else does.** `CDME_CONTRACTS.md` contains a
passage that reads exactly like a scope limit on this:

> That contract holds **only above the floor** and only within one board state.

with "the floor" defined as `VOR ≤ 0`. **That passage is STALE and must not be cited as a live
limit.** It describes the 0–100 max-normalization clip, and the document annotates its own quote:
*"the 0-100 scale was removed outright (#74/#75 — `bpa` is now raw signed VOR) … it is not a live
claim about current code."* The floor was a property of the clip; the clip is gone. Consistent
with that, `bpa` on the current opening board runs continuously to −141 with gaps intact. There
is no live "above zero only" scope limit on cross-position comparison.

**So the answer to Q2's first half is an unambiguous YES.** The answer to the half the question
actually turns on — *does it authorize the comparison when the candidates will not start?* — is
below, and it is different.

## Q3 — does anything say whether VOR remains the correct ACQUISITION metric once starting demand is satisfied?

**Yes. It is answered, it is ruled, and the ruling is DECLINE.**

> ## The deepest point
>
> **No "best available" anchor can produce VOR at exhaustion — including a correct one.** …
> The collapse is inherent to the question, not to the estimator. Which means the repair is not
> a better anchor. It is **admitting that VOR has a domain of validity and declining outside
> it.**

> **VOR inherits the domain.** Where replacement is undefined, VOR is undefined for every player
> at that position, and `bpa` — a normalization of VOR — inherits it.

> **Outside the domain the engine declines and says so.** It must not clamp, must not substitute
> a different anchor under the same name, and must not let a downstream term silently become the
> whole decision.

This was not left as a proposal. It shipped: it is `replacement_levels`' live DOMAIN paragraph
("the position's key is OMITTED, and callers must read absence as 'no starter-demand replacement
exists here', never as zero and never as rank 1"), and `test_pricing_exhaustion_boundary.py` pins
the resulting behaviour with the instruction *"INVERT these tests on repair. Do not delete them."*

**So the doctrine's position on "is VOR still the right metric past its domain" is: no, and the
engine must refuse rather than substitute.** That is a settled ruling, not an open question.

---

## THE GAP

The domain of validity exists, is well-stated, and is enforced. **But it is defined over the
ANCHOR, never over the CANDIDATE.**

The domain test asks one question: *does this POSITION still have an unfilled league-wide starter
slot?* It never asks: *is THIS PLAYER a plausible starter?* Four consequences, all structural,
none of which requires any outcome measurement:

**1. The test cannot fire where the aggregate is decided.** The composition is fixed at the
opening board (measured at 1abbd37; used here only for location). At that moment nobody has
drafted, every position carries its full pre-draft starter demand, and every position is
maximally in-domain. The entire exhaustion apparatus — built precisely for this class of
problem — has nothing to decline at the moment the answer is determined.

**2. A legitimately-defined level prices the whole pool, without restriction.** Nothing in the
contract says which players a defined level may price. TE's level is the projection of the ~25th
tight end; it is applied to the 115th. The contract defines *when* the anchor exists. It never
defines *how far down* it may be applied.

**3. The bar is a starter bar and most of the picks are not starter picks.** This league starts
10 (`starter_slot_counts` sums to exactly 10.0: QB 1.85, TE 2.05, RB 3.05, WR 3.05), so 120
starting seats exist league-wide against a 312-pick startup. **192 of 312 picks — 62% — are bench,
IR and taxi seats**, every one of them priced against a quantity whose stated meaning is *"the
player a team is guaranteed to be able to start."* No document states whether that is intended.

**4. The one term that corrects an over-credit corrects a different one.** `replacement_levels`'
own docstring names the problem the fourth team term exists for: *"the rank is LEAGUE demand, so
a player is priced against the league's free alternative even when the drafter's own slots at his
position are already held by better players — the league anchor credits him for a slot that roster
cannot offer."* That is a **roster-relative** correction. It does not address the
starter-versus-bench category question, and its docstring does not claim to.

### Stated as the deliverable

> **The contract does not define the deep-bench cross-position comparison.**
>
> It authorizes cross-position VOR comparison explicitly and on evidence (Q2). It rules that VOR
> must be declined outside its domain (Q3). But it keys that domain on league starter demand at
> the position, so the rule is silent in exactly the regime where 62% of a startup's picks are
> made and where the aggregate composition is settled. **Whether "value over replacement" is the
> right acquisition metric for a player who will not start is not answered anywhere — not
> affirmed, not forbidden, not identified as a question.**

## What this does NOT establish

- **Not a defect.** Nothing here shows the normalization is implemented wrongly, that the levels
  are miscomputed, or that the cross-position bar is invalid where the contract claims it. Every
  citation above says the current behaviour follows the design.
- **Not a verdict from the roster shape.** The 101 result is not used as evidence about
  desirability anywhere in this document, per instruction. A superflex league with a 0.75/rec TE
  premium taking a lot of tight ends may be entirely correct; this document takes no position.
- **Not a proposed repair.** No level tuned, no penalty added, no threshold moved, no
  normalization altered. Naming a gap is not authorization to fill it, and the material for
  filling it (a candidate-side domain test) would be a new concept requiring its own derivation
  under #56.

## Related register items

**#155** reserved "cross-position VOR comparison is the real question" — this is that question,
now located precisely: not comparability in general, but comparability below starter depth.
**#50** (VOR/replacement/horizon redefinition, Phase 3) is where a successor anchor would live.
**#61** ruled what the board does when bpa is undefined; the gap here is the mirror case — what
the board does when bpa is DEFINED but the candidate is not a starter. **#59/#122** (saturation,
bench appetite) hold the only bench-side demand machinery, none of which reaches the level.

## Preserved separately, NOT merged

The **1-vs-15 TE allocation phenomenon** remains its own open question (#226, RESIDUAL5, and the
neighbour-contention observation). RESIDUAL5 demoted it from the aggregate account: composition
is conserved under pick-order permutation while recipients scramble ~90%, so it is a
roster-distribution phenomenon, not an aggregate-selection one. It is not folded back in here and
nothing above depends on it.
