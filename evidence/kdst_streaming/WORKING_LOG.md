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


---

# UPDATE — the grade is in, the shape is not reachable by valuation, and the ruler is built

## Settled

- **The engine drafts competitively.** `run_smoke_seats` at `a761d1c`: wins 5 of 6 formats on the
  independent `points` ruler (+2.131 / +0.505 / +1.927 / −0.883 / +5.151 / +2.565), reproducing
  recorded v1 to three decimals on three of them. The `#22` regression is fully unwound.
- **The streaming math is right and insufficient.** DEF1's realized edge over a streamer is ~0
  against a board price of 22–30 — a real valuation error. Correcting it moves first DEF from
  round 5.09 to 7.02; driving `bpa` to −24.5 reaches 10.01. Round 12 needs DEF12 **+59**; no
  streaming construction exceeds +40, and the board's own vintage gives **+16**.
- **The binding constraint is the COMPARATOR, not DEF's price.** The best remaining skill row falls
  +32 → −30 between rounds 5 and 14 because deep pools are priced against a starter-band level with
  zero bench value. DEF-side leverage is ~1/5 of a round per point and is exhausted by round 10.
- **The gate could not validate a fix.** The projected ruler solves one lineup with no absences and
  no waivers; across three drafts spanning DEF at rounds 5–10 the league total moved −0.16%/+0.08%.
  It is indifferent to K/DST timing.

## Built, in response

`realized_ruler.py` — scores a roster on WHAT HAPPENED, as the sum of each week's best legal
lineup over realized stats. Rewards depth by construction: a player with no line that week is not
offered to the solve (absent ≠ zero, `#187`), so the bench fills real absences. Measured absence
rates on the starting band make this material: RB 0.14/0.12, WR 0.11/0.14, TE 0.15/0.16 against
0.06 for K and DEF, which is the bye alone.

Smoke-tested: a 17-player roster scores 3900.0 over 18 weeks against 2768.6 for a 9-player one.
(That gap overstates depth — 9 players cannot fill 10 slots — but the mechanism works.)

Limits, stated: no waivers or trades, so it is a LOWER bound on a streaming strategy; the weekly
solve is an ORACLE lineup, so absolute totals are ceilings. Both arms of any comparison get the
same advantage.

## Next, in order

1. **Counterfactual roster surgery** (cheap, decisive): take a drafted roster, swap its early DEF
   for the best skill player available at that pick, score both on 2024 realized. Measures the
   direct cost of a round-5 defense without redrafting. Second-order effects (the displaced
   player) are unmodelled and will be stated.
2. Tests for `realized_ruler`, full suite.
3. If the cost is real and material: the insurance term on the comparator side, derived from
   measured absence rates.
4. VDS battery on K/DEF-bearing formats.

## How far off

| | now | target |
|---|---|---|
| first DEF | round 5.08 | 12–16 |
| best reachable by valuation alone | round 10.01 (at `bpa` −24.5, beyond any streaming basis) | — |
| quality vs field | **wins 5 of 6** | meet or beat — MET |


---

# UPDATE 2 — THE COST IS REAL AND MEASURED. The gate was the blind spot.

## The headline

**An early K/DST pick costs ~81 real points.** Counterfactual surgery on a 2024 draft, scored on
2024 realized outcomes: 42 early K/DEF picks, deferring gained a mean of **+81.4** (median +95.8)
and helped **34 of 42**. K +82.9, DEF +80.1.

The projected ruler's verdict on the same question was **−0.16% / +0.08%** — indifferent.

So the behaviour is not an aesthetic preference. It is money, and the freeze gate could not see it.

## What changed in my understanding

I had been treating "K/DST go too early" as a shape problem to be argued about. It is a **cost**
problem, and now it has a number. That also reframes the gate: the owner's condition ("no quality
drop-off") was to be measured on the projected `points` ruler, which is *structurally* incapable of
detecting a regression of this shape. **The realized ruler must be in the gate.**

## What is still NOT known

- **The size of the fix.** Two bounds run opposite ways and neither can be removed here: the
  swapped-in player is not taken from whoever really drafted him (upper bound on the gain), and the
  vacated K/DEF slot stays empty for want of waivers (lower bound). n = 42 picks, ONE draft, ONE
  season, sd 83.2.
- **Which lever closes it.** The streaming basis is a real valuation correction but saturates at
  round 10. The comparator side (bench insurance, derived from measured absence rates) has the
  leverage but is unbuilt and unmeasured.
- Whether 8-of-42 going the other way — worst a round-7 Denver at −105.3, the best realized defense
  of 2024 — means the fix should be *selective* rather than positional. The projection ranked Denver
  third behind a Philadelphia that returned 153.0, which is `#18`'s DEF ordering skill (0.48)
  showing up as money.

## Next, in order

1. Full suite with `realized_ruler` — in flight.
2. Wire the realized ruler into the gate alongside the projected one, so a K/DST change is
   certifiable at all. **This is the blocker on any fix, not the fix itself.**
3. Wire `12T_ppr_K_DEF` into the quality grader (its six formats have zero K/DEF slots).
4. Only then attempt the comparator-side term, pre-registered.

## How far off

| | now | target |
|---|---|---|
| first DEF | round 5.08 | 12–16 |
| measured cost of that | **~81 real points per pick** | ~0 |
| reachable by valuation alone | round 10.01 | — |
| quality vs field (projected ruler) | wins 5 of 6 | MET |
| quality vs field (realized ruler) | **not yet measured** | — |
