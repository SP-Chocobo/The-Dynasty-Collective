# #18: the measurement ran, and the instrument is the wrong shape

`measure_projection_accuracy` executed against the live API for the first time on the owner's
machine, after the URL repair in `29ab259`. All 36 weeks returned actuals. It printed this:

| pos | season | proj gap | real gap | share |
|---|---|---|---|---|
| QB | 2023 | 166.9 | 42.7 | 0.26 |
| RB | 2023 | 214.1 | 240.9 | 1.12 |
| WR | 2023 | 151.1 | 149.0 | 0.99 |
| TE | 2023 | 173.5 | 115.9 | 0.67 |
| K | 2023 | 20.0 | 6.0 | 0.30 |
| DEF | 2023 | 18.8 | 34.0 | 1.81 |
| QB | 2024 | 86.7 | 169.9 | 1.96 |
| RB | 2024 | 187.4 | 219.6 | 1.17 |
| WR | 2024 | 143.9 | 245.6 | 1.71 |
| TE | 2024 | 133.1 | 74.5 | 0.56 |
| K | 2024 | 29.8 | 0.0 | 0.00 |
| DEF | 2024 | 6.7 | 35.0 | 5.26 |

**This does not say what the plan expected it to say,** and the plan should be read as falsified
rather than confirmed. `POST_AUDIT_PLAN.md` recorded the ruling as "a per-position forecast-
reliability shrink on `bpa`, DERIVED from `measure_projection_accuracy`", on the expectation that
K and DEF would come back well under 1.0 — a projected spread that does not materialise. DEF came
back at **1.81 and 5.26**: its realised gap EXCEEDS its projected gap in both seasons, which is
the opposite direction. A shrink derived from these numbers would *raise* DEF.

## Why the numbers are not about the positions

The estimator is a **two-player difference**. For each position it takes the player projected at
rank 1 and the player projected at replacement rank, and compares what those two specific players
actually scored. That is n = 1 pair per position per season — not a sample of a position's
forecast reliability, a sample of two careers.

At the positions the work exists to fix, the resolution is coarser than the effect. Measured on
the committed 2024 actuals (`realized_spread.py`):

```
K    ranks 9-16 realized: [137.0, 136.0, 133.0, 133.0, 133.0, 132.0, 126.0, 125.0]
DEF  ranks 9-16 realized: [137.0, 136.0, 136.0, 132.0, 128.0, 127.0, 119.0, 118.0]
QB   ranks 9-16 realized: [350.9, 345.4, 324.2, 322.6, 321.7, 318.9, 288.4, 264.7]
```

Kicker season totals are integers — field goals are 3 and extra points are 1 — so they tie. There
are **three kickers tied at exactly 133.0** at the replacement rank. `K 2024 = 0.00` is therefore
not "none of the projected kicker spread materialised"; it is "the projection happened to rank
12th one of three kickers who finished level with the top kicker's comparator". Which of the three
it picked decides the whole ratio, and nothing about the position does.

`DEF 2024 = 5.26` fails the other way. Its projected gap is **6.7 points across an eighteen-week
season** — about a third of a point a week, i.e. the projection says the twelve starting defenses
are indistinguishable. Any realised spread at all divides into a large ratio. The number is a
division by approximately zero, reported to two decimals.

A ratio is not more trustworthy for being printed. `K 2023 = 0.30` and `K 2024 = 0.00` are not two
measurements of one quantity; `QB 0.26` then `1.96` is the same instrument on a position with no
tie problem at all, which is the clearest sign that the spread in these numbers is the estimator's
and not the sport's. **More seasons will not fix this** — each season adds one more pair.

## What the actuals do support, in the direction the audit claimed

One comparison survives, and it needs no projections. Realized 2024 season totals at each
position's replacement rank in `12T_ppr_K_DEF`, scored with the engine's own
`player_universe.score_projection`:

| pos | rank | r1 | r@rank | gap | pool |
|---|---|---|---|---|---|
| QB | 12 | 580.0 | 322.6 | 257.4 | 112 |
| RB | 32 | 398.3 | 145.0 | 253.3 | 191 |
| WR | 32 | 468.0 | 204.2 | 263.8 | 343 |
| TE | 20 | 273.7 | 121.4 | 152.3 | 185 |
| K | 12 | 188.0 | 133.0 | 55.0 | 50 |
| DEF | 12 | 190.0 | 132.0 | 58.0 | 32 |

Verified by eye before anything was read off it: the top realized defenses come out DEN, MIN, PIT,
GB, PHI, which is the real 2024 order. The scorer handles K and DEF stat lines — 527 and 525
non-zero player-weeks — so none of this is a dead-scorer artifact.

Against the board's own projected gaps at the same ranks, as recorded in
`evidence/blind_pass/KDST_VALUATION.md` (QB 43.9, K 12.6, DEF 30.5):

| pos | board's share of QB's gap | realized share of QB's gap | overstated by |
|---|---|---|---|
| K | 0.29 | 0.21 | 1.3x |
| DEF | **0.69** | **0.23** | **3.1x** |

The board believes a defense's rank-1-to-replacement spread is 69% of a quarterback's. The season
paid 23%. That is the original complaint — defenses taken about five rounds early — showing up as
a *relative spread* error rather than a level error.

### The objection that would kill that, and why it does not

Ranking by outcome is hindsight, and a hindsight-ranked gap is inflated for every position,
because the best realized scorer is a maximum over noise. So the table above is **not** any
position's true spread, and the between-position comparison only holds if hindsight inflates QB at
least as much as it inflates K and DEF. If it inflated DEF *less*, the 3.1x could be an artifact
or could even reverse.

Measured, not assumed. Inflation rides on how much of a season total is week-to-week noise, so:
the median player's weekly standard deviation, carried to a season total as `sd * sqrt(18)`,
against the gap it would have to inflate.

| pos | weekly sd | season sd | gap | sd/gap |
|---|---|---|---|---|
| QB | 10.37 | 44.0 | 257.4 | 0.17 |
| RB | 4.67 | 19.8 | 253.3 | 0.08 |
| WR | 5.07 | 21.5 | 263.8 | 0.08 |
| TE | 3.10 | 13.2 | 152.3 | 0.09 |
| K | 4.87 | 20.7 | 55.0 | **0.38** |
| DEF | 5.40 | 22.9 | 58.0 | **0.39** |

K and DEF carry **more than twice** QB's noise as a fraction of the gap being measured. Hindsight
therefore inflates them harder than QB, so the true DEF share is *below* the measured 0.23 and the
**3.1x is a floor, not an estimate**. The objection points the same way as the finding.

`sd/gap` near 0.4 is also the plainer statement of what is wrong with drafting a defense early:
about two fifths of the gap you are paying for is next season's coin flips.

## What this does not license

**No constant is derived here, and none should be** (#56: a bound is not a threshold). A floor of
3.1x on a relative overstatement is not a shrink factor, and the estimator that could produce one
has just been shown to be the wrong shape. Turning this into a term in `bpa` needs a population
estimator — projected against realized across a position's whole pool, not two endpoints of it —
and that needs the projections arm, which lives behind a host the audit sandbox denies
(`api.sleeper.app`, CONNECT 403, re-measured today and still denied).

`capture_weekly_lines.py` exists for that: one command on a networked machine writes a season of
projections to a committed file, and the instrument repair can then be iterated offline instead of
costing a round trip through the owner per hypothesis.

## Register

- **#18 is not closed.** It was blocked on reaching the API; it is now blocked on the estimator.
  The live path works and the URL repair is verified by 36 non-empty weeks.
- **The ruling recorded in `POST_AUDIT_PLAN.md` is superseded by measurement.** The shrink it
  authorised cannot be derived from this instrument, and if it were derived from these numbers it
  would move DEF the wrong way.
- **#17 stays parked behind #18**, for the same reason as before.
- Generalising the lesson already banked under #18: a test that asserts what our own code
  constructs is not evidence about a system we do not control. Its sibling, earned here: a ratio
  computed over two data points is not a rate, however many decimal places it is printed to. The
  engine-measurement checklist already says "print n". `n` here was 1.
