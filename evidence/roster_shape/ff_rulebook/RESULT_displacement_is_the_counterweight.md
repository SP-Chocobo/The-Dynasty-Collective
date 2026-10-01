# RESULT — displacement is NOT order-neutral, and my previous headline is withdrawn

Pre-registered in `PREREG_aggregate_selection.md` (addendum, d1bda52) before the probe existed.
Two real mid-draft board states replayed from `ff_draft.json`, production shape, `mode` left at
its default (both states are rounds 1–14, where `auto` IS balanced, so this is production and
not a forced arm). No engine source changed. 17s.

**FORK Q. The fork I registered as "the one that would reopen the aggregate question."**

---

## The measurement

| state | pos | mean `displacement_adj` | `adj == 0.0` | top-K by `bpa` | top-K by `points − displaced` | delta |
|---|---|---|---|---|---|---|
| pick 100 | QB | −92.25 | 0 | 10 | 8 | −2 |
| K=212 | RB | −41.22 | 0 | 56 | 54 | −2 |
| | **WR** | **0.00** | **160 of 160** | 60 | 93 | **+33** |
| | **TE** | **−60.03** | 0 | 86 | 57 | **−29** |
| pick 150 | QB | −85.72 | 0 | 3 | 2 | −1 |
| K=162 | RB | −59.01 | 0 | 44 | 42 | −2 |
| | **WR** | **0.00** | **139 of 139** | 28 | 72 | **+44** |
| | **TE** | **−89.14** | 0 | 87 | 46 | **−41** |

Identity reconciliation `(bpa + displacement_adj) − (points − displaced)`: **max |gap| = 0.0000**
at both states, computed independently rather than restated.

**Displacement is the most position-differentiated term in the engine — a 0-to-−89 spread — and
it runs directly AGAINST the tight-end lead the opening board's level subtraction creates.**

**Why WR pays exactly nothing, on every row.** The shared flex alternative is `max(levels)`,
which in this league IS WR's level (217.75). A receiver evicting the flex phantom therefore has
`displaced == level_WR`, so `displacement_adj = level − displaced = 0` identically. That is
FINDING_03's "the position defining `max(level)` pays nothing", now measured on the real
universe: 160 of 160 and 139 of 139.

## The independent confirmation, from an artifact already on disk

Split the production draft at the mode boundary:

| | QB | RB | WR | **TE** |
|---|---|---|---|---|
| engine, **rounds 1–14 (BALANCED)** | 19.0% | 26.2% | 39.3% | **15.5%** |
| **twelve real managers, whole draft** | 20.0% | 27.4% | 37.1% | **15.5%** |
| engine, rounds 15–26 (UPSIDE) | 0.0% | 27.8% | 20.1% | **52.1%** |

**In balanced mode the engine drafts like the twelve humans — on every position, to within about
two points, and on tight ends to the first decimal.** The entire divergence lives in the 144
picks where upside mode runs. Two independent lines — a static top-K comparison at two board
states, and the finished draft's own regime split — agree on direction and magnitude.

## What this means, and it is a synthesis rather than a new suspect

The two positional anchors are a **matched pair**, and balanced mode applies both:

- `bpa = points − level` **favours** tight end, because TE's anchor is the lowest (149.17 against
  WR's 217.75).
- `displacement_adj = level − displaced` **charges** tight end (−60 to −89) and charges receivers
  nothing.

Composed, they produce the human numbers. **Upside mode removes one half of the pair and keeps
the other**: `compute_draft_board`'s upside branch zeroes every team-specific term, which deletes
the displacement charge while leaving the level subtraction untouched. That is not a neutral
simplification — it removes the counterweight and keeps the weight.

This is the first **mechanism** for PHASE4's measured result (the mode boundary carries 63% of
the excess). PHASE4 established that the boundary is causally active; it had no account of why.
The account is: the boundary is where the counterweight is switched off.

---

## WITHDRAWN — my own headline, the 19th withdrawal

`RESULT_aggregate_selection.md` was titled *"the aggregate composition is set by one subtraction,
before any pick."* **That causal claim is withdrawn.**

**What stands, unchanged.** Every number in that document. Top 312 by raw points = 67 TE; by
`bpa` = 101 TE; by `final_score` = 98 TE; drafted = 101 TE. The levels, the 94-point spread, the
7.4-vs-75.9 cut point, 101 of 115 priced tight ends. All measured, all reproducible, none
affected.

**What is withdrawn.** The reading that the opening `bpa` sort CAUSES the finished draft. It does
not. The draft's first 168 picks demonstrably do not follow that ordering — they follow
`points − displaced`, which this probe shows produces a very different composition, and which the
regime split confirms produces the human one. The opening `bpa` ordering describes what **upside
mode** implements, and upside mode governs 144 of 312 picks.

**What is now unexplained, and stated as unexplained.** The finished total (101) matches the
opening `bpa` top-312 (101) closely on every position, and the sets overlap 310/312. Since the
draft is a two-regime mixture — 26 tight ends from the balanced half, 75 from the upside half —
that match is either a coincidence of the mixture or a constraint of the pool's structure
(312 of 481 priced rows are consumed). **I do not know which, and I am no longer entitled to read
it as causation.**

**A second overclaim in the same document, corrected.** I reported the 310/312 set overlap
without a chance baseline. Taking 312 of 481 twice gives an expected overlap of **202/312** by
chance alone. 310 is far above that and the observation survives — but it is a weaker fact than
I presented, and the COMPOSITION match, not the set overlap, was doing the work in my argument.

## What this does NOT establish

- **Not that upside mode is defective.** Zeroing team-specific terms is upside mode's documented,
  intended behaviour ("no roster awareness of any kind"). What is newly visible is a *consequence*
  nobody had stated: that it breaks a matched pair rather than removing a whole layer.
- **Not that the level subtraction is wrong.** The contract investigation (76b17b3) stands
  unchanged: cross-position VOR is explicitly authorized, and the deep-bench case is undefined.
- **Not a repair, and specifically not "force balanced".** PHASE4 already measured and rejected
  that on its own evidence: forced balanced gives rounds 15–26 at TE 29.2% and WR 45.1%, worse
  monocultures, and no QB movement. The balanced half is human-like in rounds 1–14 at a roster
  state that no longer exists by round 15.
- **Not a merge of the allocation question.** The 1-vs-15 bifurcation stays separate (#226).

## Method note

The probe passes production-shaped picks — `{player_id, roster_id, round}` — because a pick
missing `round` silently flips `mode="auto"` to balanced. That is the 17th withdrawal's exact
mechanism, and this probe would have been its second victim without the schema clause now in the
measurement skill.
