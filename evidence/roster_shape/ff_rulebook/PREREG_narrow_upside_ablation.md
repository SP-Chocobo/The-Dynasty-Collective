# PRE-REGISTRATION — does upside mode keeping ONLY the displacement counterweight help?

Written and committed BEFORE the probe exists. Forks and guardrails stated before any number is
read. **No engine source is modified**; the arm is an in-process patch of `dr.compute_draft_board`,
the same technique the engine-measurement skill prescribes for an honest A/B.

## The question, and why it has never been asked

PHASE4 measured **"force balanced for all 26 rounds"** and rejected it on its own evidence: TE
rounds 15–26 fell 52.1% → 29.2%, but whole-draft WR went 30.4% → 42.0% against a human 37.1%, the
largest single-position pile went 12 → 19, and seats holding ≥12 at one position went 3 → 7. It
relocated the excess and made roster shape worse.

**That is a much bigger change than the mechanism requires.** Forcing balanced restores four
team-specific terms. The mechanism identified in #222 is one of them: `displacement_adj` is the
counterweight that makes the positional level cancel, and upside mode drops it along with the
other three.

**The narrow arm has never been run:** upside mode keeping `displacement_adj` and nothing else.
`need_bonus`, `eligibility_bonus` and `depth_exposure` stay zeroed, `upside_score`'s growth term
stays, `bpa` stays. One term, restored.

## The instrument

`dr.compute_draft_board` is wrapped. For each call the wrapper invokes the REAL function **twice**
with identical arguments — once as production would (`mode` as passed), once with
`mode="balanced"` — and adds the balanced board's own per-row `displacement_adj` to the upside
board's `final_score`. Rows are then re-sorted on production's own key
(`_feasible`, `final_score` desc, `player_id`).

**Every quantity is production-computed. Nothing is reconstructed.** In particular
`displacement_adj` is taken from a real balanced board, so multi-eligible candidates (#172) carry
the per-eligibility-set solve `score_row` does for them, not a per-primary-position approximation.

When the board is already balanced (rounds 1–14 under `mode="auto"`) the two calls agree and the
addition would double-count, so the wrapper **passes those through untouched**. That makes rounds
1–14 a control, below.

Cost: two board builds per pick, so roughly twice the baseline draft's ~1,016s.

## The control, which must pass or nothing is reported

`mode="auto"` is balanced for rounds 1–14, and the wrapper passes those through. **All 168 picks
of rounds 1–14 must match `ff_draft.json` player-for-player.** If they do not, the instrument is
toggling more than one thing and no result is reported — the same gate PHASE4's ablation passed
168/168.

## Forks, stated now

Baseline (AUTO, `ff_draft.json`) and the rejected arm (force balanced) give the bar:

| measure | AUTO baseline | force balanced (rejected) | humans |
|---|---|---|---|
| TE, rounds 15–26 | 52.1% | 29.2% | — |
| WR, whole draft | 30.4% | **42.0%** | 37.1% |
| largest single-position pile | 12 | **19** | — |
| seats with ≥12 at one position | 3 | **7** | — |
| (seat, position) pairs at ≤2 bodies across RB/WR/TE | 0 | **7** | — |

- **FORK A — SUPPORTED as a candidate.** TE in rounds 15–26 falls below 52.1%, **and** every
  guardrail holds at or better than AUTO's own value: whole-draft WR < 40.0%, largest pile ≤ 12,
  seats with ≥12 at one position ≤ 3, thin (seat, position) pairs ≤ 0. The narrow change improves
  the TE share without the relocation that sank the wide one.
- **FORK B — SAME TRADE, REJECTED.** TE falls, but any guardrail breaches. Then the narrow arm is
  the wide arm in miniature and goes the same way PHASE4's did.
- **FORK C — NOT THE LEVER.** TE in rounds 15–26 stays ≥ 50.0%. Then restoring the counterweight
  alone does not carry the effect, and something else in the mode switch does.

**Reported regardless of fork:** the full four-position composition for the whole draft and for
rounds 15–26, all four roster-shape measures, the control's pick-for-pick match count, and the
per-seat TE distribution.

## What this run cannot establish, stated now

**One league, one rulebook, one pool, one pick order.** A fork-A result would make the narrow
change a *candidate*, not a decision — it would still need the roster-shape measures replicated
and an owner ruling on whether upside mode is permitted roster awareness at all, which is the
question #223 and #229 both terminate in.

**And a fork-A result is not permission to ship it.** No engine source changes on the strength of
one draft. The standing order is evidence before repair; this is evidence.
