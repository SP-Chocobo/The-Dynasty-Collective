# `#30` working log — read this first after a container reclaim

Updated continuously. If a session died, this is the state.

## What I am looking for

A DERIVED correction that puts K and DST in rounds 12–16 of 16 **without** the quality
drop-off `#16` caused (−6.09 on the independent `points` ruler, seat wins 11/12 → 2/12).
"Derived" means it falls out of league structure or measured outcomes — never a chosen constant
(`#56`). The engine must still build good rosters *including bench and depth*, which is why the
roster-worth ruler is `total_value` (what the chair OWNS), not `starter_value` (`#211`).

## THE MATH — found, measured, and it is NOT the hypothesis I started with

### What was wrong with my first hypothesis

I proposed: replacement level for a streamed position should be the streaming baseline, because
the real alternative to drafting a defense is the best one on the wire each week, not DEF12 held
all season.

**Measured, the naive form of that points the WRONG WAY.** The premium of streaming over holding
the replacement-rank player, realized:

| pos | 2023 | 2024 | mean |
|---|---:|---:|---:|
| QB | +51.4 | +16.7 | +34 |
| RB | +69.0 | +127.9 | **+98** |
| WR | −31.9 | +74.5 | +21 |
| TE | +56.0 | +42.3 | +49 |
| K | −37.0 | +11.0 | **−13** |
| DEF | +12.0 | +50.0 | +31 |

Streaming beats holding-replacement at *every* position, and by MORE at RB than at DEF. Raising
every replacement level by its streaming premium would lower RB's `bpa` most and K's least —
pushing K and DST **earlier**. The hypothesis as stated is falsified.

### The quantity that IS right

Not "how much better is streaming than the replacement player", but **how much does drafting the
top one buy you OVER streaming** — because streaming is what you actually do instead.

Projected #1 at each position, scored on realized points, minus the streaming baseline:

| pos | 2023 edge | 2024 edge | as a share of WR's edge |
|---|---:|---:|---|
| WR | 180.9 | 171.1 | 1.00 / 1.00 |
| RB | 171.9 | 91.7 | 0.95 / 0.54 |
| QB | −8.7 | 153.1 | −0.05 / 0.90 |
| TE | 59.9 | 32.2 | 0.33 / 0.19 |
| **K** | 43.0 | −11.0 | **0.24 / −0.06** |
| **DEF** | 22.0 | −15.0 | **0.12 / −0.09** |

**Drafting the best defense buys approximately nothing over streaming, and in 2024 it was
NEGATIVE.** The projection's top defense (Philadelphia, 121.5 projected) returned 153.0; streaming
returned 168.0. The actually-best defense (Denver, 190.0) was ranked third by the projection.

Against that, the engine prices the top defense at `bpa` **30.5** (battery snapshot) or **22.0**
(app snapshot) — over DEF12 held all season. The real edge over the real alternative averages
**3.5**. That is the over-valuation, and it is roughly an order of magnitude.

### Why it is position-dependent, which is the whole point

Wire quality *relative to rostered quality* varies enormously with pool depth:

- WR's wire is **1,331** players, almost all of whom did not play. The 32nd WR held all season is
  genuinely about as good as anything you could stream, so the engine's replacement basis is
  roughly RIGHT there.
- DEF's wire is **20** defenses that are nearly as good as the 12 rostered. Streaming is almost as
  good as drafting, so the engine's basis is wildly wrong there.

So this is not a uniform correction. It is a replacement-BASIS error that happens to be near-zero
for deep positions and severe for shallow ones — which explains why four projection-side levers
and a reliability measurement all came back clean. They were all correcting a numerator.

## How far off the mark we are

| | now | target |
|---|---|---|
| first DEF | round **5.08** | 12–16 |
| first K | round **7.00** | 12–16 |
| K+DEF gone before round 12 | **47 of 192** | ~0 |
| top-DEF `bpa` | 22.0–30.5 | ~3.5 (measured edge over streaming) |

## THE IMPLEMENTATION CONSTRAINT I have hit

The streaming baseline is a sum of **weekly** choices: each week, the best wire player by THAT
WEEK's projection. It cannot be recovered from a season total, because the whole point is that a
streamer re-picks every week and never eats a bad matchup twice.

Production passes `sleeper_projections` as per-category **season sums** (`app.py` →
`SLEEPER_BASIS_SEASON_SUM`). Per-week projections are not currently in the board's inputs, though
`SleeperClient.get_weekly_projections` exists and the capture files hold them.

So a real implementation needs one of:
- **(a)** weekly projections reaching `replacement_levels` — principled, more plumbing; or
- **(b)** a per-league streaming baseline computed offline and shipped as data — rejected, that is
  a fitted constant per league and `#56` forbids it; or
- **(c)** a derivation of the streaming baseline from the season-summed pool. NOT obviously
  possible: measured, DEF's streaming baseline (168.0 in 2024) sits ABOVE the 13th defense's
  season total, because weekly re-picking beats any single hold. It is not an order statistic.

**(a) is the route.** Not yet built.

## Plan, in order

1. ~~Measure the streaming baseline~~ — DONE, above.
2. ~~Identify the decision-relevant quantity~~ — DONE: edge over streaming, not premium over held.
3. Wire `12T_ppr_K_DEF` into the quality grader. **Its six formats have ZERO K/DEF slots**, so the
   gate cannot currently see the positions under repair.
4. Pre-register the candidate change before running it.
5. Implement (a): weekly projections into the replacement basis for streamable positions.
6. VDS battery on K/DEF-bearing formats + the field grader, against HEAD.
7. Full suite. Only then contemplate freeze.

## Standing risks

- **Container reclaim.** It already cost a full grader run and 33 of 36 battery arms. Checkpoint
  and push after every meaningful step; never leave a long run unattended.
- **My own record tonight: eight withdrawn conclusions**, every one measured, every one measuring
  the wrong object. Three were the same fixture class (a league with no K/DEF slot, then no K/DEF
  scoring, then a grader with no K/DEF slots). Pre-register, print `n`, and state which
  configuration produced every number.
