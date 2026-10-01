# `#17` — turn-ending picks leak exactly the positions the repair exists to place

> **SUPERSEDED 2026-09-21. RE-MEASURED AGAINST THE REVERTED ENGINE, as ruled.** Everything below
> was measured on the v2 `acting_now_value` ordering and cites `_acting_now_order`, which `#22`
> deleted. Kept unedited; read the re-measurement first.
>
> Probe: `turn_ending_remeasured.py`. Rulebook `12T_ppr_K_DEF`, 192 picks, self-play on HEAD.
>
> ```
> pos     all  turn-ending  expected   ratio
> WR       65            0      5.08    0.00
> RB       42            4      3.28    1.22
> K        26            1      2.03    0.49
> TE       23            3      1.80    1.67
> DEF      21            6      1.64    3.66
> QB       15            1      1.17    0.85
>
> first K   of the draft: pick 46 (4.10), turn-ending: False
> first DEF of the draft: pick 33 (3.09), turn-ending: False
> K/DEF taken by round 12: 37, of which turn-ending: 6 (16%)
> ```
>
> **THE CLUSTERING SURVIVES FOR DEF AND VANISHED FOR K.** DEF is **3.66x** its share, up from the
> 2.95x recorded below. K is **0.49x** — under-represented, against 2.74x below. So the effect is
> not an artifact of the reverted ordering, but it is not the effect this file described either:
> it was a K-and-DEF finding and it is now a DEF-only one.
>
> **THE PROPOSED MECHANISM CAN NO LONGER WORK, and that is the decisive change.** The repair below
> is "point `positional_forfeits` at the gap after *N+1* instead of the empty gap after *N*".
> Post-`#22`, `positional_forfeits` **has no selection authority at all** — the board ranks on
> `team_acquisition_value`, and the forfeit reaches only necessity's display term. Pointing it at
> a different gap therefore cannot change which player is taken. Whatever now drives the 3.66x is
> not the forfeit, and this file's mechanism does not address it.
>
> **AND THE FRAMING IS PROBABLY WRONG ANYWAY.** The first defense of the draft now lands at
> **pick 33 — round 3.09** — two rounds earlier than the 7.12 below and earlier than the round-5
> figure in `KDST_VALUATION.md`, because the `#16` repair that placed K/DEF correctly is the thing
> `#22` reverted. Arguing about *where within a round* defenses cluster is arguing about the
> distribution of an already-wrong behaviour. The round-3 defense is the defect; `#18`'s
> forecast-reliability shrink is the fix, and it is likely to dissolve this question rather than
> leave it to be answered separately.
>
> **A FIRST RUN OF THE RE-MEASUREMENT WAS VACUOUS AND IS RECORDED AS SUCH.** It used
> `build_mock_league`, whose starters are `QB/RB/RB/WR/WR/TE/FLEX/FLEX` with **no K and no DEF
> slot**, so those positions never entered `usable_positions` and the probe reported "K and DEF
> never taken" — measuring the FORMAT, not the engine. `n=0` for the population the item is about.
> Caught by the engine-measurement rule on printing `n`.
>
> **STATUS: not closed, but this file's mechanism is withdrawn.** What survives for the owner is a
> narrower question, and it should wait on `#18`: does DEF clustering at 3.66x still matter once
> defenses are priced correctly?

---


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
