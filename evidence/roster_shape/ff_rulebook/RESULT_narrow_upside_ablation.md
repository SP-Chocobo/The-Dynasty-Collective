# RESULT — the narrow arm: FORK B, rejected, and it isolates the counterweight exactly

Pre-registered in `PREREG_narrow_upside_ablation.md` (`086939f`) before the probe existed.
One 312-pick draft, real universe, #201/#204 recipe, 891s. **No engine source modified** — the arm
is an in-process patch of `dr.compute_draft_board`, reverted in a `finally`.

**CONTROL PASSES: 168 of 168.** Rounds 1–14 match the baseline player-for-player, so the
instrument toggles exactly one thing. Patch stats: 169 boards passed through balanced, 143 boards
adjusted, 33,033 rows adjusted, 0 rows skipped for an absent adjustment.

---

## The result

| arm | QB | RB | WR | TE | TE r15–26 | largest pile | seats ≥12 | thin pairs |
|---|---|---|---|---|---|---|---|---|
| AUTO baseline | 10.3 | 26.9 | 30.4 | **32.4** | **52.1** | 12 | 3 | 0 |
| **NARROW (displacement only)** | 10.3 | 25.3 | **42.0** | **22.1** | **29.9** | **17** | **11** | **4** |
| force balanced (already rejected) | 10.3 | 25.6 | **42.0** | 21.8 | 29.2 | 19 | 7 | 7 |
| twelve real managers | 20.0 | 27.4 | 37.1 | 15.5 | — | — | — | — |

Pre-registered bars: WR whole-draft < 40.0, largest pile ≤ 12, seats ≥12 at one position ≤ 3,
thin pairs ≤ 0. **TE fell as Fork A required and every one of the four guardrails breached.**
FORK B.

## What the arm isolates, and this is the real yield

**Restoring `displacement_adj` alone reproduces force-balanced's positional composition almost
exactly.** WR is identical to the first decimal (42.0 vs 42.0); TE differs by 0.3 whole-draft and
0.7 in rounds 15–26; RB by 0.3; QB by 0.0.

The only difference between the two arms is `need_bonus`, `eligibility_bonus` and
`depth_exposure`. **Those three terms contribute essentially nothing to the back half's positional
composition.** `displacement_adj` carries the whole effect, on its own, measured.

That sharpens #222's mechanism from "the mode boundary is causally active" to something much
tighter: **the mode boundary matters because of one term, and the other three are along for the
ride as far as composition goes.**

## And it exposes a second pair, from the opposite direction

The three terms do nothing for composition and a great deal for **shape**. Restoring the
counterweight *without* them:

- **seats holding ≥12 at one position: 3 → 11.** Eleven of twelve seats finish with a 12-plus pile
  somewhere. Force-balanced, which keeps the three terms, has 7.
- per-seat TE goes `[5,8,7,9,10,7,8,6,10,8,11,12]` → `[3,12,3,1,16,3,2,1,4,4,3,17]`. Maximum 12 → **17**.
- largest pile 12 → 17 (force-balanced 19); thin pairs 0 → 4 (force-balanced 7).

So on shape the narrow arm is **worse than AUTO on every measure, and worse than force-balanced on
the seat count** while better on the other two.

**This is #87's ruling confirmed from the other side.** #87 established by ablation that
`need_bonus` is a POSITIONAL GATE — *"load-bearing, and not correlation-testable"*. Removing it
made the engine draft four quarterbacks in a one-QB league. Here it is not removed but *left out
while a large positional push is restored*, and the result is the same failure mode: the
composition moves and nothing stops the piling.

**`displacement_adj` and `need_bonus` are themselves a matched pair** — one moves positional
composition, the other prevents stacking — and that is the second such pair this investigation has
found. The first was `bpa` and `displacement_adj`. Restoring either member of either pair alone
produces a worse engine than leaving both alone.

## The bottom line, and it is not the one I expected

**Both roster-aware arms land on WR 42.0% against a human 37.1%, and neither reaches the human TE
number.** Humans take 15.5% tight ends; AUTO takes 32.4%, force-balanced 21.8%, the narrow arm
22.1%. **No configuration measured reaches the human distribution.**

The TE excess is therefore *not removable by restoring roster awareness in the back half*. Turning
roster awareness on trades a TE overshoot for a WR overshoot of almost exactly the same size, and
costs roster shape both times.

**AUTO's 32.4% TE and the roster-aware arms' 42.0% WR are two faces of one fact about how this pool
is priced, and the mode boundary only chooses which face you see.** That points back where the
contract investigation already pointed — cross-position comparability below starter depth (#229) —
and away from the mode switch entirely.

## What this run establishes and what it does not

**Establishes:** the narrow change is measured and rejected on its own evidence, by its own
pre-registered bars; `displacement_adj` alone carries the composition effect; the three bounded
nudges carry the shape protection; and no arm tested reaches the human distribution.

**Does not establish:** anything about other leagues, rulebooks, pools or pick orders — one draft,
one format. And it is not evidence about whether the *pricing* is desirable, which remains the
owner's question and is untouched by this arm.

**Nothing is proposed and no engine source changes.** Two candidate repairs have now been measured
and both are rejected; that is the evidence half of "evidence before repair" doing its job.
