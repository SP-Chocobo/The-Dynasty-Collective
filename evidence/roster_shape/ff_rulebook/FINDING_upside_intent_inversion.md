> **FRAMING WITHDRAWN (20th) — see CONTRACT_what_upside_mode_is_meant_to_drop.md.**
> The facts below are correct and stand: upside mode zeroes every team-specific term, retains
> `bpa` at full weight as the base of `upside_score`, and the constant's comment names two things
> as no longer mattering. **The FRAMING — "half the stated intent is implemented and the other
> half inverted" — is withdrawn.** It weighed one uncommitted comment against the founding
> architecture (`universal_value` is team-agnostic and explicitly includes "league-wide scarcity"),
> four contract statements, and a pinned test, all of which say retaining the anchor is deliberate.
> The contract DOES answer the semantic question and the answer is "roster fit only". The code is
> not violating an intent; one comment describes the code wrongly. The real gap is narrower and
> sharper: `displacement_adj` is classified BOTH as a team-specific term (so upside zeroes it) AND
> as a correction to the universal anchor (so it alone carries no cap), and nothing reconciles the
> two.

# Upside mode drops half its stated intent and inverts the other half

Documentary. **No engine source changed, no probe run for this document.** Every quotation is
verbatim from the working tree. The one supporting measurement (Fork Q, 42ecbac) is used to say
the difference is *material*, never to argue that VOR is undesirable.

---

## What the mode says it is for

`draft_room.py:223-226`, `UPSIDE_MODE_DEFAULT_ROUND`'s own comment:

> Round at which the engine switches from the balanced formula to upside-only scoring, absent an
> explicit override — matches the "War Room" idea this was modeled on. A deep bench/waiver-fringe
> pick is about finding a league-winning outlier, **not filling a need or respecting positional
> scarcity that barely matters by then.**

**Two things are named as no longer mattering: (1) filling a need, and (2) respecting positional
scarcity.** The module docstring says the same in other words — "the real value is finding a
league-winner, not optimizing safe positional value."

## What the mode actually does

**(1) is implemented, exactly.** The upside branch zeroes every team-specific term. Its own
comment states the layer identity holds "with all three team-specific terms at 0.0", and
`depth_exposure` "is additionally never even COMPUTED on this path". `feasibility_first`'s comment
adds: "this branch has **no roster awareness of any kind**." Need is gone. Correct.

**(2) is not implemented. It is retained at full weight, as the base of the score.**

```python
value = round(bpa + UPSIDE_GROWTH_WEIGHT * growth, 2)     # draft_room.py:2043
UPSIDE_GROWTH_WEIGHT = 0.5                                # draft_room.py:508
```

`upside_score` returns `bpa` plus half a bounded percentile difference. `bpa = points − level`,
and `level` is `replacement_levels` — the positional anchor. So the positional subtraction is not
merely present in upside mode; **it is the base of the upside score, undiminished.**

Under the contract's own vocabulary the positional content of `bpa` is two things, and upside
mode keeps both:

| the contract's name | definition | in upside mode |
|---|---|---|
| production margin | `points − pre_draft_level[pos]` — the per-position structural baseline | **retained, full weight** |
| scarcity movement | `pre_draft_level − live_level` — "how the live market has moved this position" | **retained** (bpa uses the LIVE level) |

Whichever of the two the comment means by "positional scarcity," upside mode does not stop
respecting it.

## And the two are a matched pair

Fork Q (`RESULT_displacement_is_the_counterweight.md`) measured what the zeroed term was doing:
`displacement_adj` is **0.00 on every receiver row** (160 of 160, 139 of 139) and **−60 to −89 on
tight ends**. It was the counterweight to the low tight-end anchor. Composed, the pair produces
the humans' own numbers in rounds 1–14 (TE 15.5% against 15.5%). Upside mode deletes the charge
and keeps the subtraction, and rounds 15–26 run TE 52.1%.

**So the inversion is not cosmetic.** The half of the stated intent that IS implemented is the
half that was holding the other half in check.

## What this is

**A stated-intent-versus-implementation mismatch in a constant's own comment.** Not a measurement
claim about whether VOR is the right metric — that question is the owner's and is untouched by
this document (see `CONTRACT_deep_bench_cross_position.md`, 76b17b3).

Three fair points on the other side, recorded so this is not read as heavier than it is:

- **The engine is not silent about the mode change.** `mode="upside"` is emitted on every row,
  `universal_value` is documented as "deliberately NOT the same NUMBER as a balanced board's" and
  "must never be compared across modes". The doctrine's requirement — *"must not let a downstream
  term silently become the whole decision … without the board declaring that it has"* — is
  **satisfied**. The declaration exists.
- **Nothing states that `bpa` and `displacement_adj` are a pair.** `displacement_level`'s
  docstring explains what the term corrects and why; nothing says the correction must travel with
  the thing it corrects, or that removing one alone changes the meaning of the other. That is the
  gap, and it is the same shape as the one in `CONTRACT_deep_bench_cross_position.md`: a
  correction whose scope of application is never stated.
- **The comment is a comment, not a contract.** It is the only statement of upside mode's
  purpose anywhere in the repo, which is itself worth noting — but it was never ratified as a
  contract clause and no test pins it.
  `test_auto_mode_switches_to_upside_exactly_at_the_documented_round` pins the NUMBER 15 and, in
  its own words, *"the boundary itself is a calibration decision"* — a change-detector, not a
  meaning.

## A suspicion I raised and cleared, recorded because it looks like a defect and is not

`upside_score` opens `bpa = row.get("bpa") or 0.0`, which reads as an absence-contract violation —
an unpriced row given a fabricated 0.0 and thereby ranked above every priced row with negative
`bpa` (the 312 cut sits near −142, so that would be most of the board).

**It does not fire.** In a float column absence is `NaN`, and `bool(NaN)` is `True`, so
`NaN or 0.0` returns `NaN`; `round(NaN + w·growth, 2)` is `NaN`; and `final_score` IS in
`_records_with_normalized_nan`'s column list, so it reaches the board as `None` and sorts last.
Verified directly, and confirmed against the draft: **all 312 drafted players were priced on the
opening board, 168 of 168 in the balanced rounds and 144 of 144 in the upside rounds.** No
unpriced row was ever selected.

**It remains a latent hazard, not a live defect.** The guard is accidental — it depends on the
column being float-typed so that absence is `NaN` rather than `None`. A `None` in that column
WOULD be converted to 0.0 and would rank an unpriced player above most of the priced board. The
absence contract elsewhere in this module is explicit rather than incidental.

## Not established, and not proposed

Not that upside mode is defective; not that 15 is the wrong round (tuning it is forbidden and
would be a calibrated constant under #56); not that the retained term should be removed. Naming a
mismatch between a comment and an implementation is not authorization to change either. **The
owner's question, stated plainly: is upside mode meant to drop roster fit only, or roster fit AND
the positional anchor? The comment says both. The code does one.**
