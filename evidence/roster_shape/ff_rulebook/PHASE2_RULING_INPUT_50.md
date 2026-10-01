# #50 RULING INPUT: live vs PRE-DRAFT anchor — the four questions, answered

> **PARTIALLY CORRECTED by `PHASE3_D3_GATE_FAILED.md`. Read that first.**
>
> Everything measured in this document stands. One CONCLUSION does not. This document says
> the anchor is "WRONG" at `displacement_level`'s `free_alternative` on that parameter's own
> contract, and recommends replacing it. The parameter does receive a stale value — but the
> D3 gate then measured that `bpa = points − level` exactly (`_scale_vor_to_bpa` is the
> identity), so `bpa + displacement_adj = points − displaced` and **the level cancels**. The
> term's output is invariant to the staleness wherever the term is non-zero, and replacing
> `free_alternative` alone would inject that staleness (−86.36 at TE, pick 205) as a real
> price. The parameter is MISNAMED, not mis-fed.
>
> The two-consumer split is still an accurate description of the code, and the owner's ruling
> on it stands. What changed is the consequence: consumer 2 does not consume the staleness.
> The one place it does reach a price is a position with an OPEN reachable slot, through
> `bpa` alone — consumer 1.
>
> This document was explicit that it claimed no net effect on price. It was right not to.
> It was wrong to conclude "legitimate modelling defect" from the contract alone without
> measuring the term's consumed effect first.

Method: every number below is a production return value, captured at the call. Every
`replacement_levels` observation is tagged by CALL IDENTITY derived from the arguments, never
from call order (the anchor is cached and does not fire on every build). All 312 picks are
observed — one board per pick, no sampling.

Probes: `phase2_crossing.py` (312 boards, raw in `phase2_crossing.json`),
`phase2_crossing_read.py`, `phase2_ladder_basis.py`, `phase2_what_is_available.py`.

Fourth and Forever, real rulebook, real universe (6,595), the FINDING_05 draft.

---

## Q3 first, because it is a SOURCE question

**Production selects the pre-draft anchor for position P on the points board iff all three
hold:**

1. P is present in the projected pool, AND
2. `replacement_levels` omitted P, AND
3. `startable_floors.get(P) is None` — P was not handed a startability floor.

`replacement_levels` omits P for two reasons. With no floor, the reason is
`_remaining_demand_rank(P, demand) is None`, i.e. `demand[P] < 1 − 1e-9`: **less than one whole
starting slot at P is still unfilled anywhere in the league.** The other omission path
(`at_pos.empty`) is UNREACHABLE on the points board — `present_positions` is derived from the
same frame `at_pos` is filtered from, so a present position always has a priced row. Checked,
not assumed; the `_fill_omitted_from_anchor` docstring's "EXHAUSTED DEMAND" is therefore exact.

Observed, from `_fill_omitted_from_anchor`'s own returned set — production's decision, not my
comparison of numbers:

| pos | first anchored | demand there | demand one pick before | board stamp |
|---|---|---|---|---|
| QB | **never** | — | — | has a startable floor → not eligible, by design |
| WR | after 104 picks | 0.30 | 1.30 | `predraft_anchor` |
| TE | after 192 picks | 0.10 | 1.10 | `predraft_anchor` |
| RB | after 204 picks | 0.05 | 1.05 | `predraft_anchor` |

The crossing is a single pick: demand falls by exactly 1.0 as one team fills its last slot.
QB never crosses because `_fill_omitted_from_anchor` declines floored positions — exactly what
`predraft_replacement_anchor`'s docstring says it must do. That is correct behaviour and it is
also why QB is simply *unpriced* from pick 168 on, which is B2's territory, not this ruling's.

## Q1 + Q2 — the live trajectory against the fixed anchor

anchor (production `predraft_replacement_anchor`): QB 243.29 · RB 170.81 · WR 217.75 · TE 149.17

| after picks | QB live | RB live | Δ vs anchor | WR live | Δ | TE live | Δ |
|---|---|---|---|---|---|---|---|
| 0 | 243.29 | 170.81 | +0.00 | 217.75 | +0.00 | 149.17 | +0.00 |
| 78 | 243.29 | 170.81 | +0.00 | 217.75 | +0.00 | 149.17 | +0.00 |
| 103 | 243.29 | 170.81 | +0.00 | **211.65** | −6.10 | 149.17 | +0.00 |
| 104 | 243.29 | 170.81 | +0.00 | **ANCHORED** | | 149.17 | +0.00 |
| 156 | 243.29 | 156.84 | −13.97 | ANCHORED | | 108.64 | −40.53 |
| 191 | omitted | 111.64 | −59.17 | ANCHORED | | **63.85** | **−85.32** |
| 192 | omitted | 111.64 | −59.17 | ANCHORED | | **ANCHORED** | |
| 203 | omitted | **68.23** | **−102.58** | ANCHORED | | ANCHORED | |
| 204 | omitted | **ANCHORED** | | ANCHORED | | ANCHORED | |

**The live level is NOT constant while in domain.** Max |live − anchor| before crossing:
RB 102.58, TE 85.32, WR 6.10, QB 6.12.

## Q4 — what changes at the crossing

The jump, at the exact pick, from the last live level to the anchor that replaces it:

| pos | last live level | anchor | jump | as % of live |
|---|---|---|---|---|
| RB | 68.23 | 170.81 | **+102.58** | **+150.3%** |
| TE | 63.85 | 149.17 | **+85.32** | **+133.6%** |
| WR | 211.65 | 217.75 | +6.10 | +2.9% |

WR is small because WR crossed early (pick 104), while its pool was barely drained. RB and TE
cross late, after ~90 and ~80 further picks of drain, and the level snaps back over its whole
accumulated fall in one pick.

**And it stays snapped back for the rest of the draft while the pool keeps draining.** What the
anchor asserts is freely available, against the best player actually left (read out of the pool
production handed `replacement_levels`):

| after picks | RB anchor says / best left | WR | TE |
|---|---|---|---|
| 104 | 170.81 / 214.39 | 217.75 / 208.64 | 149.17 / 195.60 |
| 204 | 170.81 / **65.69** | 217.75 / **131.18** | 149.17 / **62.81** |
| 311 | 170.81 / **27.21** | 217.75 / **75.10** | 149.17 / **6.49** |

At the last pick of the draft the board is pricing every remaining tight end against a freely
available tight end worth **149.17 points who does not exist** — the best one left is worth
**6.49**. The overstatement grows monotonically to **+143** because the anchor is a constant
and the pool is not.

---

## What this explains — and it is B1's phenomenon, mechanically

The published B1 ladder charged −51.7 at two tight ends held, rose to −120.4 at six, then
**returned to −51.7 at seven and eight**. I called that impossible: "a term whose every input
has changed by a factor of five cannot legitimately return the same number to the hundredth."

Re-run with the level and its basis captured (`phase2_ladder_basis.py`). `displaced` and its
basis are production's own returned values, not inverted from the adjustment:

| held | pick | disp_adj | TE level used | basis | live TE | demand | displaced | disp basis |
|---|---|---|---|---|---|---|---|---|
| 2 | 109 | −51.73 | **149.17** | live_starter_demand | 149.17 | 11.60 | 200.90 | measured |
| 3 | 132 | −55.92 | 144.98 | live_starter_demand | 144.98 | 6.50 | 200.90 | measured |
| 4 | 156 | −91.92 | 108.98 | live_starter_demand | 108.98 | 5.45 | 200.90 | measured |
| 5 | 180 | −119.41 | 81.49 | live_starter_demand | 81.49 | 2.25 | 200.90 | measured |
| 6 | 181 | −120.37 | 80.53 | live_starter_demand | 80.53 | 2.25 | 200.90 | measured |
| 7 | 205 | **−51.73** | **149.17** | **predraft_anchor** | omitted | 0.10 | 200.90 | measured |
| 8 | 229 | **−51.73** | **149.17** | **predraft_anchor** | omitted | 0.00 | 200.90 | measured |

`displacement_adj = level − displaced` exactly, at every rung. `displaced` is 200.90 and
`basis` is "measured" at all seven — the optimizer never moves, as Fork A already established
by identity. **Every bit of the ladder's movement is the level's movement, and the return to
−51.73 is the level returning to 149.17 by changing BASIS.** Two different bases, one number.

So the number was never impossible. It was one constant reached twice: live-equals-anchor
early, anchor-filled late.

### A correction I owe

`PHASE1_B1_WITHDRAWN.md` offered a mechanism for the return: *"an exact return to the hundredth
is a rank landing on the same player: as tight ends are taken league-wide, remaining demand
shrinks, the rank walks UP the thinning list, and it arrives back at the player who sat at that
rank when the pool was full."*

**That is false, and this measurement falsifies it.** At seven and eight held the live call
does not return a TE level at all — TE demand is 0.10 and 0.00, the position is OMITTED, and
149.17 arrives from `_fill_omitted_from_anchor`. No rank walks anywhere. The document flagged
this exact item as "not yet read out"; it is now read out, and the plausible story was wrong.
Corrected in place.

---

## THE RULING QUESTION: is the anchor semantically the correct quantity here?

Not "does it correlate with the tight-end shape." The argument below does not use the roster
shape at all, and the correlation runs in **both** directions on different terms — the anchor
makes VOR *worse* for a remaining tight end (level up 85 → VOR down 85) while making the
displacement deduction *weaker* (−120 → −52). I am not claiming a net effect, and no part of
this ruling rests on one.

**The answer splits by consumer, and that is the finding.**

**Consumer 1 — `_vor` / bpa, pricing and ORDERING a demand-exhausted position. The anchor is
CORRECT here.** This is what it was built for: without it, a position whose league starter
demand is satisfied has no level, `final_score` is None, `_board_order` sorts None last, and
every remaining player at that position falls below every kicker. The anchor is a
*normalisation reference* that keeps those players on the board. It does not need to be a
claim about current availability to do that job, and a stable reference is a virtue for it.

**Consumer 2 — `displacement_adjustments` → `displacement_level(free_alternative=...)`. The
anchor is WRONG here, on that parameter's own contract.** `displacement_level`'s docstring:

> *"That is the right anchor for a slot this roster has not filled — **the free alternative is
> what the slot gets otherwise** — and the wrong one for a slot it has filled with someone
> better than that alternative."*

"What the slot gets otherwise" is a claim about what is **actually available now**. At pick 205
the anchor tells that term a free tight end is worth 149.17. The best tight end in the pool is
worth 62.81. The term then charges the roster only 51.73 for stacking a ninth tight end,
because it believes a 149-point tight end is still there for the taking. **The quantity is
being read as an availability claim by a consumer that needs one, while its justification is an
ordering claim.** That is the #55 / #185 / #186 shape exactly: one quantity, two meanings,
failing toward the stronger claim.

**So: legitimate modelling defect — but NOT in the anchor.** The anchor is fine. The defect is
that `displacement_level` is handed the anchor when its contract asks for live availability.
Do not change `predraft_replacement_anchor`. Do not change `_fill_omitted_from_anchor`.

### A second, smaller finding: the anchor's stated justification cites a superseded claim

`predraft_replacement_anchor`'s docstring argues:

> *"replacement_levels' own docstring records that while demand stays positive, rank shrinkage
> and pool drain cancel exactly, so the live level is algebraically identical to the static
> pre-draft one. **The last live level is therefore the pre-draft level** — verified directly
> here, not assumed: ... every position's **first** observed live level equals its pre-draft
> level to within 1e-9."*

Two problems, both checkable:

1. `replacement_levels`' docstring no longer records that. **#216 corrected it:** *"that
   cancellation holds ONLY for starter-filling picks ... A BENCH pick at a position drains the
   pool without reducing any team's starter demand, so it moves the level."* The anchor cites
   the pre-#216 wording.
2. The verification offered tests the **first** observed live level; the conclusion drawn is
   about the **last**. Both halves are now measured here: first live *does* equal the anchor
   exactly (+0.00 at board 0, all four positions — the cited check reproduces), and last live
   is 68.23 / 63.85 / 211.65 against anchors of 170.81 / 149.17 / 217.75.

This is a prose defect, not a behaviour defect — the anchor still does its own job. But the
sentence a future reader would rely on to justify feeding the anchor to a *live* consumer is
the false one, so it is load-bearing for exactly the decision at hand.

---

## Defining the proper quantity BEFORE any fix

Per #56, whatever replaces the anchor at `free_alternative` must be DERIVED. Naming it:

> **`live_free_alternative[P]`** — the projected points of the player who would occupy this
> slot if the candidate did not, given the pool as it stands now.

Three precise candidate definitions. **This is the owner's choice; I am not implementing one.**

- **D1 — best remaining player at P.** Simple, fully live, no constant. Assumes the slot is
  filled immediately at no opportunity cost, which is false: you must spend a pick.
  At pick 205 this gives TE 62.81, and the ninth-tight-end deduction becomes −138.09 instead
  of −51.73.
- **D2 — the demand-rank level with the domain gate removed.** **Not available.** Below one
  whole slot the rank is undefined, and floor-to-rank-1 is precisely the conflation
  `_remaining_demand_rank` returns None to prevent (#73, #114). Listed so it is visibly
  rejected rather than silently unconsidered.
- **D3 — the value at P at a rank derived from the picks between now and this roster's next
  turn.** This is what the phantom actually means ("what will still be there when I next take
  one"), and the ingredient already exists and is already derived — the same intervening-picks
  count `positional_forfeit` and `survival_probability` use. Costs no new constant. Costs a
  real modelling commitment about rival behaviour, which #206 says the engine currently gets
  wrong.

**Recommendation, stated as a recommendation:** D3 is the semantically right quantity and D1 is
the honest interim. If D3's rival model is not trustworthy enough today (#206 says it may not
be), D1 is defensible *and* strictly closer to the contract than the anchor, because the
anchor's error grows to +143 while D1's error is bounded by one pick's worth of drain.

**Whatever is chosen: the anchor must keep feeding consumer 1 unchanged, and the two consumers
must stop sharing one number.** That separation is the fix; the choice of D1 vs D3 is the
tuning of it.

## What must NOT happen

- Do not modify the anchor because it correlates with the tight-end shape. It is not the
  argument here and the correlation is not even single-signed.
- Do not touch the stranded flex-anchor candidate. It remains frozen: it was derived while
  replacement behaviour was believed malformed, and that belief is now dead twice over.
- Do not run the 33-format battery. There is no repair to test yet.

## Next action

A **ruling**, not a measurement: (a) confirm the two-consumer split, and (b) choose D1 or D3.
