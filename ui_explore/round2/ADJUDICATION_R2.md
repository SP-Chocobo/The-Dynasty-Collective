# Round 2 adjudication — Opus, sole authority

I checked every load-bearing claim in all four reviews against `states.json` and the engine
source before any of it reached you. Reviews are evidence, not verdicts. Three findings are
overturned below; where a reviewer was right, I say so and often the finding got bigger.

Read this file as binding alongside `$S/explore/ADJUDICATION.md` (round 1, still binding).

---

## 1. THE HEADLINE — both Opus reviewers found this independently, and it is bigger than either said

**The `late` board's negativity has exactly one cause, it is already on the payload, and not one
of the eight variants renders it.**

`displacement_adj`, `displacement_basis: "measured"` in all three states:

| state | n | displacement_adj | tav range |
|---|---|---|---|
| early | 24 | `0.00` on all 24 (a MEASURED zero) | +82.10 … +176.28 |
| mid | 24 | `0.00` on all 24 (a MEASURED zero) | +16.54 … +52.47 |
| late | 7 | **−33.70 … −44.05** | −53.46 … −34.61 |

How much of each `late` value it IS:

```
Devaughn Vele    WR  tav  -34.61 = displacement -33.70 + rest -0.91   ( 97.4%)
KC Concepcion    WR  tav  -34.84 = displacement -33.70 + rest -1.14   ( 96.7%)
Trevor Lawrence  QB  tav  -36.37 = displacement -36.37 + rest  0.00   (100.0%)
Sam Darnold      QB  tav  -37.90 = displacement -36.37 + rest -1.53   ( 96.0%)
Kyler Murray     QB  tav  -38.68 = displacement -36.37 + rest -2.31   ( 94.0%)
Jordan Mason     RB  tav  -43.68 = displacement -40.88 + rest -2.80   ( 93.6%)
T.J. Hockenson   TE  tav  -53.46 = displacement -44.05 + rest -9.41   ( 82.4%)
```

Strip the displacement term and Vele is −0.91, not −34.61. Lawrence is **exactly 0.00**.

This is the one state where the screen looks broken and isn't, and the owner's standing
constraint is *clean who, why, and other valid options, at what cost*. The **why** at `late` is
a single named measured quantity. It needs one sentence, not a new field, not a re-based scale,
and not the flat offset I already modelled and rejected.

**Required of every variant:** at `late`, one sentence that attributes the negative value to the
displacement of an already-filled starting slot. Say it once, in the bright type, next to the
number it explains — not in a numbers sheet, not in a footnote.

---

## 2. OVERTURNED — the "double counting" finding (Sonnet A)

Sonnet A reported that `−9.8 value` and `+9.9 wait cost` are one quantity printed twice, and that
"readers will net the two to zero."

**Right that they are not independent. Wrong that they duplicate. And the true relation is more
useful than either the claim or the complaint.**

Verified, 6 of 6 cross-position pairs, to ±0.05:

```
positional_forfeit(best at P) == tav(P) - position_next_turn_value(P)      (exact, ±0.03)
value_edge + order_edge       == (A_next_turn - B_next_turn)
```

So the order edge carries the value edge inside it **with the opposite sign**. Dependent: yes.
Duplicates: no —

```
early  RB/WR   value  +9.77   order  +9.89     <- looks like a duplicate
early  RB/TE   value +33.57   order -15.09     <- nothing like one
early  WR/TE   value +23.80   order -24.98
mid    WR/RB   value  +2.73   order  +2.23
mid    RB/QB   value  +1.88   order  -6.12
```

Sonnet A generalised from the single pair where the next-turn gap happened to be ≈2× the value
edge. On RB/TE the two numbers are 48.7 apart.

**What all four reviewers missed:** the sum of the two printed numbers is not noise and is not
zero — **it is the next-turn gap**, i.e. how these two positions compare *at my next turn*. A
reader who nets them is not making an error; they are computing a real decision-relevant third
quantity, and no variant names it.

So Sonnet A's implied remedy — print one number instead of two — destroys information. **Do not
do that.** Either name the sum for what it is, or print value-now beside value-at-next-turn and
let the gap be the visible thing. `position_next_turn_value` is already on every candidate.

---

## 3. OVERTURNED — the `late` "tie" is not in the payload at all

Sonnet A disputed the tie's *threshold*; Opus B disputed its *membership* (`tiedWith` inventing a
rank-1 anchor, so V3 column A says "a tie with Concepcion and Lawrence" while column B says "a
tie with Vele"). Both assumed the tie was engine-reported.

It is not:

```
early  ambiguities: []     mid  ambiguities: []     late  ambiguities: []
```

Empty in all three states. Every "tie", "coin flip" and "too close to call" on these surfaces is
**client-invented from a hand-picked constant** (Sonnet A located `0.05` in `shared.js`). That is
register `#56` — a chosen constant doing a derived constant's job — and it is a worse finding
than either reviewer made it, because the self-disagreement Opus B documented is a *symptom* of
there being no authority to disagree with.

**Ruling:** no variant may assert a tie. The board's own evidence that not taking #1 is
defensible is the *margin* — Vele −34.61 vs Concepcion −34.84 is **0.23 apart on a scale whose
rows span 18.9**. Render the margin and let the reader draw the conclusion. That satisfies the
owner's constraint honestly; a fabricated "tie" badge does not.

Separately, for the owner and not for you: `confidence` is `85.0` for every candidate in all
three states. Identical numbers are a broken instrument until proven otherwise (`#245`). That is
an engine question I will take up; do not render `confidence` at all until it is answered.

---

## 4. OVERTURNED ON THE NUMBER, UPHELD ON THE WORDING — the `costWord` superlative (Opus A #4)

Opus A reported TE labelled "the least here" at `early` while "QB's real forfeit is 1.82",
calling it an inverted positional read.

There is no QB `positional_forfeit` at `early` anywhere in the payload. I searched: no value
≈1.82 under `early`, no payload-level forfeit map, and the candidate positions at `early` are
`['RB','TE','WR']` only. The 1.82 came from my own earlier session notes, computed over a
different population — not from the board you consume. The companion line Opus A read as a
contradiction ("no wait cost measured for QB") is also correct.

**What survives:** scope. "The least here" reads as a claim about positions while being a claim
about *this board*, on the one state where the board holds no QB at all. Fix the wording so the
scope is in the sentence. Do not change the arithmetic.

---

## 5. UPHELD AND BROADENED — measured numbers rendered as absences (`#187`)

The engine's absence contract is that `None` never becomes `0.0`. You are breaking it in the
other direction: taking a **measured** value and presenting it as an absence. Two confirmed
instances, and I am treating them as one systemic defect:

- **`denial_value: 0.0` with `denial_basis: "measured"` on 7 of 7 `late` rows**, printed as `—`.
  Not one row. Every row. (Opus A #8 — and V1's own sheet tags it MEASURED with the blurb "a 0
  is a measurement" while printing the dash.)
- **A `|x| >= 2` cut-point hides measured values.** Opus B named the wrong field: it is
  **`time_horizon_adj`**, not `horizon_sensitivity`. Confirmed values — St. Brown `-0.90`,
  Bowers `+0.55`, McMillan `-0.28`, Allen `0.00`. (`horizon_sensitivity` is 18–44 everywhere and
  is not gated by anything. Use the right field name when you fix this.)

A measured zero is a fact about the league. It renders as `0.0` with its basis, or it does not
render — it never renders as a dash that means "we have nothing".

Audit every hand-picked visibility cut-point in your client code against this rule. Opus B counted
five of them.

---

## 6. UPHELD VERBATIM — `no_surplus` is captioned with the opposite of its own label

The engine's label, verbatim from `lineup_optimizer.EXPOSURE_BASIS_LABELS`:

```
'no_surplus':  "measured, but it is a starter's whole value rather than a backup's job --
                some starter here has no cover, so this is not a depth price and is not
                charged as one"
```

Rendering that as **"not measured"** states the opposite of the engine's first word. Two of the
five bases *do* begin "not measured" (`vacant`, `not_applicable`) — so the right template was
applied to the wrong basis. Copy the engine's own words; do not paraphrase a basis label.

---

## 7. UPHELD — three more, all confirmed against the payload

- **"A. Brown" collides.** `Amon-Ra St. Brown` and `A.J. Brown` both abbreviate to `A. Brown`
  and **both are in the same 24-candidate `early` board**. Round 1's ADJ §8 listed this; it is
  still unfixed in all eight variants. Keep the particle: `A. St. Brown`.
- **"The last receiver this board rates" is false of the list it sits on.** Vele's bpa (−7.99)
  sits *below* Concepcion's (−7.93), so Vele is last among WRs **in bpa order** — but the list is
  tav-ordered and Concepcion is on screen above him. ADJ §5's repair reached which neighbour gets
  named, not the sentence asserting there is none. Scope the sentence to the ordering it is true in.
- **Clipping and occlusion, in both sets.** V1-A's `late` strip captioned "7 NAMES" renders 5
  (rows at `top: 889px`/`923px` in a 900px viewport) with ~500px spare; V1-A truncates three of
  seven names; V2-B paints five player names *underneath* an opaque sibling at `early`; V4-A
  truncates the cliff clause on 7 of 7 rows with ~500px of empty sheet below. Your `_shot.py`
  checks regions and self-clipping under `overflow:hidden` — it cannot see text overflow or
  occlusion by an opaque sibling, and it prints `r.scrollers` without ever asserting on it. That
  is round 1's failure repeated one level down. **Assert on text overflow and on occlusion, then
  look at the images again.**

---

## 8. THE STRUCTURAL READ — both Opus reviewers reached it independently, in different words

> "The set asserts in bright and retracts in grey." — Opus A
> "It solved the comparison and then buried the answer in a second ranking vocabulary." — Opus B

Everything that keeps these surfaces *legal* is set in the smallest, dimmest, most peripheral
type, while the bright type and the spatial layout assert the thing the rulings forbid. Two
concrete instances, both confirmed:

- **V4-A sorts the layout by `positional_forfeit`.** §16a measured ordering on that aid at
  **−6.090%**, and round 1's ADJ §1 ruled it *informs, never decides*. Making it the spatial rank
  is that violation by geometry — at `late` the second door the eye reaches is Hockenson at
  **−53.46**, the worst value on the board, because TE's forfeit is 4.05.
- **The second edge is labelled "order"** while the footnote says value is what the board orders
  on. It is a forfeit difference. The prose obeys the ruling; the type weight does not.

Fix the hierarchy, not the footnote. If a caveat is load-bearing it belongs in the bright type;
if it is not load-bearing, delete it.

---

## 9. CREDIT — verified, not taken on trust

12px floor holds exactly (12.0px minimum across all 24 renders). No page scroll. No re-based
scales. No invented fields. `depth_exposure` prints a digit only under `measured` — exactly the
three `late` rows (7.1 / 7.1 / 7.2) — with absence-and-reason elsewhere and no stray `0.0`.
Cliff neighbours taken from **bpa** order and said so. `cliff.tier` used 1:1 with no invented
thresholds. `YOUR NEXT` on screen in both rail variants. And the ADJ §6 subtraction is now
actually **performed**, with correct arithmetic in every state — that was round 1's headline
failure across all six variants, and both sets fixed it.

Two ideas the reviewers singled out, which I endorse and which are not mine:

- **V1-A's summoned position table** — four rows in fixed lineup order: your slot · best left +
  value · cost of waiting, with `not measured` for a position the board has no name at. It is the
  governing sentence in four lines, it dissolves the ordering instability by holding the slots
  still, and it is the only place in either set that renders an empty position as a *state*
  rather than a hole.
- **V3-B's lettered roster strip** — A/B/C lighting the slot each candidate would fill, captioned
  "letters mark the slot each would fill". Answers "which position?" with no number, no legend and
  no comparison; costs one line; survives the position reordering by construction.

---

## 10. WHAT GOES TO THE OWNER AS A QUESTION, NOT SCORED AS A DEFECT

V2-A has **no rail**; V2-B and V4-B drop four RULED §1 items (rail, name boxes, glow, re-center).
The owner wrote §1 as binding — *and* wrote "honestly, not having the rail may be worth exploring
too", and §2 hedges that "the rail earns its space or it does not get any".

So this is a ruling the owner invited you to challenge, and I will not score it either way.
State it plainly in your rationale as an explicit §1 change request with the cost named, and let
him decide. Two things do remain defects inside that exploration: nothing on V2-A states the
**pool size** in any state, so short columns over a dark fold are indistinguishable from a failed
render; and §1's guarantee that *who is on the clock is never ambiguous* is a separate promise
from the span the rail drew — a clock sentence can replace the span, but something must still name
the drafter.

---

## 11. WHAT I AM NOT RULING ON

Layout taste, palette, which variant is best, and whether a given surface "sings". The owner is
taking all eight to human reviewers and has said explicitly: **do not pick a winner.** I am
ruling on contracts, arithmetic and prior rulings only. Where a reviewer gave you a layout
opinion, it is theirs, not binding, and you may disregard it with a sentence saying why.
