# `#17` — turn-ending picks leak exactly the positions the repair exists to place

*Evidence for a ruling, not a ruling. The mechanism below introduces no constant, so this is
decision-ready rather than blocked.*

## The gap

At a turn-ending pick — the last of a round in a snake, where the same seat picks again
immediately — there are **no intervening picks**. `positional_forfeits` correctly returns
nothing, `acting_now_value` is absent, and the row falls into `_acting_now_order`'s unmeasured
block, ranked by `team_acquisition_value`: the exact order the ordering repair replaced.

That is the absence contract behaving correctly. "What does waiting cost" has no answer when you
are not waiting.

## It is not harmless

Measured over the post-repair 192-pick draft (`turn_ending_leak.py`):

| pos | all picks | turn-ending | expected | ratio |
|---|---:|---:|---:|---:|
| RB | 49 | 2 | 3.83 | 0.52 |
| WR | 58 | 3 | 4.53 | 0.66 |
| TE | 40 | 1 | 3.12 | 0.32 |
| **QB** | 18 | 3 | 1.41 | **2.13** |
| **K** | 14 | 3 | 1.09 | **2.74** |
| **DEF** | 13 | 3 | 1.02 | **2.95** |

Turn-ending picks are **7.8%** of all picks and carry roughly **three times** their share of K
and DEF. Skill positions are correspondingly under-represented.

- The **first defense of the whole draft** goes at **7.12 — a turn-ending pick.**
- Of K and DEF taken by round 12, **40% are turn-ending**, against a 7.8% base rate.

The positions this repair exists to place correctly are leaking through the one gap where it
cannot apply, and they are leaking at three times the rate chance would give.

## The mechanism, and it needs no new constant

The framing "defer to the round AFTER next" is the wrong shape, and the data shows why. A
turn-ending pick is not a pick with no horizon — **it is the first of two consecutive picks.**

At pick *N* (turn-ending) the seat also holds *N+1*. Pick *N+1* has a real gap ahead of it: every
other team picks before that seat's next turn. So the pair is one decision with one horizon, and
the correct question at *N* is not "what does waiting cost" but **"which of these two do I take
first?"** — take the one that will not survive, and use *N+1* on the one that will.

That is exactly the quantity `positional_forfeits` already computes, measured against the gap
after *N+1* rather than the empty gap after *N*. No new term, no chosen magnitude: the same
function, pointed at the next real gap instead of at a gap of zero.

It also predicts the observed data. K and DEF survive 22 intervening picks comfortably; the skill
players do not. A pair evaluated jointly takes the skill player at *N* and the defense at *N+1* —
which is the placement the repair produces everywhere else, and precisely what the 2.95× ratio
says is not happening today.

## What this does NOT establish

That the resulting rosters are worse. The clustering is a **placement** measurement, not an
outcome one — the same distinction that made the roster-outcome A/B necessary for the ordering
repair itself. A pair-aware rule should be A/B'd on lineup points before it ships, exactly as
that one was, and the 7.8% population means the effect on totals will be small even if the
placement effect is large.

## Status

`#184`: this changes what the board ranks on at a class of picks, which is the owner's call.
It is decision-ready — the evidence is here, the mechanism is derived, and implementing it is
roughly the size of the pace-convention wiring.
