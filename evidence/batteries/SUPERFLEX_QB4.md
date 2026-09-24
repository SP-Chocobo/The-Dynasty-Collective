# SUPERSEDED — this document's conclusion was wrong

Its central comparison was RAW PROJECTED POINTS, which is the category error VOR exists to
correct. On the board's own value the margins are +0.40 to +5.55, not +60 to +73, and the
"valuation system working, not junk accumulating" conclusion does not hold — a live instance of
the same pathology is sitting at tight end.

**Read `SURPLUS_DEPTH_PRICING.md` instead.** This file is kept only so the mistake is on the
record.

---

# Why three superflex chairs took a fourth quarterback — and why the flex-inclusive ceiling would be a mistake

Read out of the VDS battery's own `12T_ppr_SF__sharp_auto` arm. **No drafting, no new arm** — the
pick sequence and the capture's projections were enough, which is why this answered a question
that was scoped as a ten-minute experiment.

## The proposed experiment

> QB ceiling = dedicated QB slots + flex-reachable QB slots + 1

In `12T_ppr_SF` that is `1 + 1 + 1 = 3`, which would bind on the three chairs that finished with
four quarterbacks (seats 7, 8, 9).

## The four-QB chairs

| seat | QB1 | QB2 | QB3 | **QB4** |
|---|---|---|---|---|
| 7 | Josh Allen 372.5 (r1) | Lawrence 308.1 (r4) | Rodgers 262.5 (r11) | **Geno Smith 239.1 (r13)** |
| 8 | Hurts 347.8 (r2) | Stroud 294.5 (r5) | D. Jones 281.9 (r9) | **Cam Ward 256.5 (r11)** |
| 9 | Burrow 369.0 (r1) | Willis 289.6 (r6) | Brissett 252.3 (r11) | **Watson 215.4 (r14)** |

## What else was on the board at those rounds

| round | QBs taken | best SKILL player available | gap |
|---|---|---:|---:|
| 11 | 265, 262, 256, **252** | 192.7 | **+60 to +73** |
| 13 | **239** | 165.8 | **+73** |
| 14 | **215** | 147.8 | **+68** |

In round 11 the **top three picks of the entire round were quarterbacks.** Every fourth QB was the
highest-projecting player available to that chair by sixty to seventy-three points.

## The finding

**This is the valuation system working, not junk accumulating.** The distinction the owner asked
for is settled in the second direction: the fourth quarterback has substantial standalone value,
and he has it for a structural reason — a superflex league **starts two quarterbacks**, which
inflates QB scoring relative to every skill position and gives the position real fielding capacity
beyond one slot.

**So the flex-inclusive ceiling would demote a 215-to-265-point player below a 148-to-192-point
one.** That is not a hypothesis about outcomes; it is what `_board_order` does with a demoted row.
The experiment would measure the consequence of a move whose mechanism is already unambiguous.

## What it vindicates

The flex exemption in `fieldable_ceiling` — a position reachable through ANY shared slot gets no
ceiling — was justified on the grounds that flex chains make per-position counting wrong. This is
that argument holding up on live data from the other direction: the temptation was to treat
SUPER_FLEX as guaranteed QB capacity and tighten the bound, and the pool says the looseness is
load-bearing. A `SUPER_FLEX` slot is **not a QB slot**; it is a slot a QB may occupy. Counting it
as QB capacity inflates the structural ceiling, and the semantic leak would have cost sixty points
a pick.

## What is NOT established

Whether those fourth quarterbacks are worth their roster spot on a REALIZED ruler. Under an oracle
weekly solve, four QBs give best-of-four at two slots, and a fourth receiver gives best-of-N at
the WR and FLEX slots; which wins is genuinely open and is not answered here. What is answered is
narrower and sufficient for the decision at hand: **the ceiling extension would block the best
available player, so it is not the fix it looked like.**

No core change was made, and none is proposed.
