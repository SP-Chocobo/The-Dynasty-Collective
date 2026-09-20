# The take model weights a position by HOW MANY players it has left, not by how wanted they are

*Found chasing a regression the `acting_now` ordering caused in superflex. It is not a
superflex defect and it is not new — it is a pre-existing property of `RANK_TAKE_PROBABILITY`
that the ordering repair made load-bearing.*

## What was being chased

The ordering repair (`#52` phase 8) costs **2.4% of lineup points in superflex** against 0.5%
in standard formats, and rosters finish with one quarterback in a format that starts two:

| `10T_ppr_SF` | QB mean | QB min | starters | median | worst chair |
|---|---:|---:|---:|---:|---:|
| before (tav order) | 3.20 | **2** | 2583.6 | 2579.1 | 2544.1 |
| after (`acting_now`) | 2.40 | **1** | 2522.3 | 2538.5 | 2404.2 |

One process, one code version, toggling only the ordering key (`superflex_qb_ab.py`). Minimum
QB per roster was 2 in **every** superflex arm of the battery before, and is 1 in nine of eleven
after.

## The measurement that found the cause

At a real superflex turn, 18 intervening picks ahead, with **league-wide QB starter demand of
18.5** and **ten quarterbacks already gone in the first twenty picks** (`take_mass_bias.py`):

| pos | `expected_taken` | `forfeit` | `acting_now` |
|---|---:|---:|---:|
| **QB** | **0.84** | **0.43** | **0.43** |
| RB | 2.75 | 23.42 | 23.35 |
| WR | 3.20 | 19.36 | 19.39 |
| TE | 1.81 | 32.91 | 32.85 |

The fastest-moving position on the board is predicted to lose **fewer than one player** in
eighteen picks. By round 7, with twenty QBs gone, the prediction falls to **0.35**.

So the defect is not in `acting_now_value`, which is reading `expected_taken` correctly. It is
in `expected_taken`.

## The cause, in one line

`RANK_TAKE_PROBABILITY` names **five** ranks — 0.55, 0.32, 0.18, 0.10, 0.06, totalling 1.21 —
and every other row on the board carries a flat floor of **0.02**.

| priced rows on the board | named-rank mass | tail mass | tail share |
|---:|---:|---:|---:|
| 50 | 1.21 | 0.90 | 43% |
| 200 | 1.21 | 3.90 | 76% |
| 600 | 1.21 | 11.90 | 91% |
| **1100** | 1.21 | **21.90** | **95%** |

The floor does not decay, so the tail's mass **scales with board size**. `#206` then normalises
the total to 1.0 — correctly, since an opponent makes one pick — and normalising a wrong shape
yields a wrong distribution:

> **On a 1,100-row board the model says an opponent has a 2.4% chance of taking the best player
> on their own board.** It should be about 55%. `#206` fixed the arithmetic violation (a total of
> 23.49 against a constraint of 1.0) and left the SHAPE untouched, which moved the error from
> "sums to 23" to "the head is crushed by a tail of players nobody would take".

And because `expected_taken` for a position is the **sum over that position's rows**, the
consequence is structural:

> **A position is weighted by how many players it has left, not by how much anyone wants them.**
> WR with 200 remaining rows accumulates tail mass; QB with 15 remaining rows cannot, however
> certain it is that each will go. Scarcity — the exact thing `forfeit` exists to price —
> **reduces** a position's predicted losses.

## What this does to the K/DST repair, stated against my own interest

The ordering repair works in standard formats and the roster measurement supports it
(−0.5% lineup points for correct K/DST placement). But its central evidence — DEF forfeit 1.05,
K 0.85 — comes from this same estimator, and K and DEF are **low-row-count positions**. The
estimator is biased toward low forfeit for exactly those positions.

**The repair got the right answer for K and DST partly for the wrong reason.** The independent
justification survives — the flatness measurement is real, DEF13 genuinely is worth what DEF1 is,
and the roster outcome was measured rather than inferred — but the forfeit number that headlines
the diagnosis is produced by an estimator that would have said "low" regardless.

That is the difference between a result and a lucky result, and it belongs in the record next to
the repair rather than in a footnote.

## RESOLVED FOR THE CASE THAT BIT — and how, which changes the options below

*Added after this document's own conclusion.*

The superflex QB victim is **fixed**, and not by reshaping the distribution. The repo had
already built a market-convention override (`_pace_based_take_probability`) for exactly this
failure — its docstring names the 0.02 floor as the thing it exists to bypass — and had wired it
into `estimate_survival` alone. `positional_forfeits` now reads the same convention through a
shared `position_pace_probability` (`#52` phase 8, POST_AUDIT_PLAN). QB per roster recovers from
2.40/min 1 to 3.20/min 2, exactly matching the tav-order control.

So the bias described below is **real, unchanged, and no longer has a known live victim.** It
still applies to every position with no documented pace convention, which today is all of them
except superflex QB.

That adds a fourth option the three below did not contain, and it may be the cheapest:

4. **Document pace anchors for a second position.** The repo's own chosen remedy for this defect
   is a market convention, not a redistributed tail; it simply has anchors for one case. This
   needs real market data rather than a chosen shape, which is the opposite of `#56` exposure —
   but it needs data that does not exist in the repository today.

## Not fixed here, and why

A decaying tail is a new shape for a distribution nobody has argued for — `#56`'s prohibition
exactly, and the module's own docstring already says these constants "are not empirically
backtested against real draft behavior [and] are principled, bounded, clearly labeled starting
points". Choosing a decay now, with the superflex regression as the thing to make go away, is
fitting a constant to a result.

Three directions, for the owner:

1. **Truncate the tail.** Rows past the named ranks contribute nothing rather than a floor.
   Derived (the named table IS the model; the floor is an extrapolation past it) and it makes
   normalisation a no-op on the head. Risk: a genuine long-shot take becomes impossible, and the
   floor exists because real drafts reach past rank 5.
2. **Make the floor a share of the named mass rather than a constant per row**, so total tail
   mass is board-size-independent. No new magnitude is chosen; the existing 1.21 sets the scale.
3. **Leave it and gate the ordering repair**, accepting superflex as a known-worse format until
   the take model is addressed on its own evidence.

`W1-07` is adjacent and should be read with this: it also turns on whether a per-player quantity
or a per-turn one carries urgency.
