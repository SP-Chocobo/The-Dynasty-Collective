# Orchestrator adjudication — read this BEFORE acting on your reviews

Four reviews exist (two per Fable set). Several findings are **wrong or half-right**, and I
verified these against the engine source and the contracts myself. Where this file and a review
disagree, **this file wins**. Where this file is silent, judge the review on its merits.

Do not average the reviews. Reject what is wrong, and say why.

---

## 1. `positional_forfeit` — reviewers overshot. Do NOT simply drop it.

Sonnet B concluded "drop the forfeit as the door headline" because `§16a` measured it as a losing
ranking basis. **The measurement is real; the conclusion is too broad.**

`DRAFT_ROOM_UI.md` §16a, verbatim: ordering on `acting_now_value` lost **6.090%** of
starting-lineup points, winning 10 of 68 seats where value order won 56. **And**: for the best
player at a position, `acting_now_value` **equals** `positional_forfeit` exactly.

But the same section rules:

> still answers something the rank cannot: *does this position replace itself cheaply if I wait?*
> ... worth a person seeing — **but as a decision AID beside the rank, never as the rank's
> explanation.**

**The rule you must satisfy:** forfeit may *inform*; it may not *decide* or *explain the rank*.

Both Opus and Sonnet independently found the real defect underneath: your surfaces headline a
forfeit ordering while the engine's pick follows `team_acquisition_value`, and **nothing
reconciles the two**. A reader sees the biggest number in the RB lane and the engine's pick in
the WR lane. That is the finding to fix. Fix it by **reconciling visibly**, not by deleting the
term.

## 2. `depth_exposure` — BOTH reviewers got this half right. Here is the whole of it.

Sonnet A: "`no_surplus` is shown as measured; those rows carry no depth information." — wrong on
the second clause.
Opus A: quoted `CDME_CONTRACTS.md` correctly but did not reconcile it with the label.

The repo holds both statements on purpose:

- `lineup_optimizer.EXPOSURE_BASIS_LABELS[no_surplus]` = *"measured, but it is a starter's whole
  value rather than a backup's job — some starter here has no cover, so this is not a depth price
  and is not charged as one"*.
- `CDME_CONTRACTS.md` §6: contributes only under `measured`; the other three states contribute
  `0.0` and **that zero means "not measured here", never "safe"**.
- And the contract concedes the zero is itself a defect: *"The quantity is not unmeasurable...
  removing the starter returns his entire value... **zero is wrong: zero is a NUMBER, not an
  absence**"* — `#187`'s shape. The scale cannot be chosen yet (`#56`), so it ships as a two-step
  repair with step two outstanding.

**The display rule, which neither review stated:** render `depth_exposure` as a number **only**
when `depth_basis == "measured"`. Otherwise render the absence and its reason — never `0.0`.

**On this board that is 0 of 20 rows measured** (16 `no_surplus`, 4 `vacant`). So every
"Depth insurance 0.0" on every variant — and in my own baseline — is printing a non-measurement
as a number.

## 3. Cliff ratios are NOT comparable across positions. Opus A is right and this is severe.

Opus A caught a sentence arguing *"the drop behind McMillan is 5.2× the usual WR step; behind
Allen it is 1.0× — waiting on Allen gives up less."*

In engine units **Allen's drop is 3.44 and McMillan's is 3.24**. Allen's raw drop is the LARGER
one. The ratios diverge only because `typical_gap` is per-position (WR 0.62, QB 3.33). Dividing by
a position-specific denominator and then comparing across positions **inverts the real
magnitudes**. §14 forbids exactly this family of cross-position comparison for the gauge; it binds
here too.

That sentence also asserts the conclusion of `expected_value_of_waiting`, which is **withheld**.

## 4. Do not override the engine's `cliff.tier` with invented thresholds.

Both Opus reviewers found it: surfaces print "steep" for McLaurin (engine `tier: LOW`) and "steep"
for Etienne (`tier: HIGH`), and V3 shows the invented word and the engine's tier **simultaneously**
in one viewport. Hand-picked 5 / 2.5 / 1.5 cut-points in client code are `#56`'s prohibition.
`cliff.tier` already exists and §16d names it the card's one well-distributed ordinal. Use it.

## 5. The cliff names the WRONG PLAYER. Verified in the engine source.

`pick_synthesis` computes the cliff over a **`bpa`-sorted** same-position list:

```python
same_position = sorted((r for r in board if r["position"] == row["position"]
                        and r.get("bpa") is not None),
                       key=lambda r: r["bpa"], reverse=True)
```

Your boards are **displayed in `tav` order**. Naming "the next receiver down" from the display
list names a different player than the gap was measured against. Sonnet B listed four concrete
collisions (Etienne→Irving should be Dowdle, etc.).

Generalise it: **any sentence naming a neighbour must take that neighbour from the ordering the
quantity was computed in**, and say which ordering it means.

## 6. The strongest finding in the entire batch — treat it as the headline

Opus B: *"every input to the actual decision is on screen and the decision is never made. Take the
WR now and the QB later and you forfeit 1.7; the other order costs 5.5 — all four terms are
rendered on every variant and not one performs the subtraction. Twenty candidates, zero
comparisons between any two of them on any surface."*

Both sets render the inputs to a comparison and leave the arithmetic to the reader on a 90-second
clock. **This is the thing to fix.** Opus A's independent nomination points the same way: keep
`compare(a, b)` — prose generated from the **relation** rather than from either player, because it
structurally cannot degenerate into the same sentence twice.

## 7. Differentiation — confirmed by all four reviewers, with numbers

It works at the poles and collapses inside a position. Allen / Burrow / Purdy byte-identical
(Allen and Purdy are 20.4 `tav` apart); 9 of 20 share "second receiver, starts at WR2"; four
running backs share two verbatim sentences. Both RATIONALEs demonstrated differentiation by
comparing a QB to a WR — **the easy case**.

An open disagreement you must resolve yourselves, not split: Fable B nominated "serve a
per-candidate decision context" as the idea to keep; Opus B explicitly rejects that nomination,
arguing it is a serialization choice and is *what caused* the identical-QB failure. One of you is
wrong. Defend or concede with evidence.

## 8. Known-true, no defence needed

- The rail's "YOUR NEXT" box is off-screen on load in **all eight** variants. U1 is RULED and §2's
  entire argument depends on that marker being visible.
- `SEAT_TURNS` (a per-roster total) rendered into per-pick boxes reads as 20 picks, not 10.
- Last names collide on this exact board: Warren ×2 (the user's own TE and a rival's RB 60px
  away), Brown ×3, Williams ×3.
- Ages are joined by name from picks that **have not happened**; against a real API every age
  label goes blank. Remove or re-source.
- The gauge is sampled at pick 40 and shown as current at 42, undisclosed.
- "priced", "integrated over", `team_acquisition_value`, `positional_forfeit`, "UV" appear on user
  surfaces. Named friction, already rejected once.

---

## What to do now

1. Read both of your reviews in full (`../reviews/`).
2. Identify which criticisms are valid; **reject the ones that are not, in writing, with reasons**.
3. Reconcile where your two reviewers disagree — do not split the difference.
4. Revise your **strongest two concepts**. Discard the weak ones outright; a rejected variant
   deleted is a better outcome than four mediocre survivors.
5. Append a `REVISION.md`: what changed, what you refused to change and why, and which reviewer
   finding you judged wrong.

Keep the hypothesis-per-variant discipline. Same constraints as the original brief: real data
only, no invented engine fields, Obsidian palette, no LLM required for the base surface.
