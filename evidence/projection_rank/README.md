# Does the engine ignore projection as a rule? — measured, both arms

**The question.** #205 established a 5-11% projected-points deficit against a pure-points
drafter. That is a statement about an ACCUMULATED TOTAL and says nothing about the shape of the
individual decisions. Two very different engines produce the same figure: one that routinely
takes a far worse available scorer than any sane drafter would, and one that lands close and
occasionally trades down. Only the first is a defect.

**The trap this instrument was built to avoid, and nearly fell into.** Raw projected points are
NOT comparable across positions — a quarterback out-projects a running back in most scoring, so
a list of "available, ordered by projected points" is quarterback-heavy at the top and a drafter
who correctly takes the best WIDE RECEIVER can sit at rank 16 while doing nothing wrong. The
first version of this probe reported the engine's rank ALONE. Its first seat returned a median
rank of 16, which reads damning and means nothing. **The control's rank on the identical measure
is what makes either number readable**, and it is recorded here at the control's own picks.

## Result: the deviation is real, format-dependent, and concentrated

| | engine median rank | control median rank | engine forgone/pick | control forgone/pick |
|---|---|---|---|---|
| `12T_ppr` (1QB), rounds 1-5 | 5-22 | 1-17 | **46.9** | 33.0 |
| `12T_ppr` (1QB), rounds 6+ | 2-35 | 1-22 | **66.8** | 37.5 |
| `12T_ppr_SF`, rounds 1-5 | 5-11 | 1-4 | **17.1** | 4.8 |
| `12T_ppr_SF`, rounds 6+ | 1-11 | 1-16 | **4.8** | 18.9 |

**IT IS NOT A RULE.** In superflex the engine tracks projection at least as tightly as the
control, and over rounds 6+ it forgoes FEWER points per pick than the control does (4.8 vs 18.9)
— the control is the one reaching there, because its unfilled starting slots force it to.

**IN 1QB THE DEVIATION IS LARGE, AND IT CONCENTRATES IN TWO PLACES.** Rounds 1-3, where the
engine gives up 20-38 points a pick against the control's 0-19; and **rounds 9-10, where the
engine forgoes 132.0 and 75.1 points a pick while the control forgoes ZERO.** By round 9 the
control has filled every starting slot and simply takes the best remaining producer; the engine
is still taking something else. Those two rounds alone are the largest single block of the 1QB
gap.

## What this does NOT establish

Whether the round 9-10 behaviour is CORRECT. Taking a dynasty asset over the best remaining
producer on a bench pick is the engine's stated philosophy, and it is also exactly what a
mis-firing positional gate or a bad survival estimate (#206) would look like. This instrument
locates the deviation; it does not adjudicate it. That is #50/Phase 3.

Nor does it establish anything about WINS. `points_forgone` is projected points against the
best available at that moment, not games.
