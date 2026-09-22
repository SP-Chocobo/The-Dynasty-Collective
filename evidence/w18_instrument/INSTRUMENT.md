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

---

# CORRECTION AND SECOND PASS: the 3.1x above was measured against a board that no longer exists

Everything above the line stands except the number I put most weight on. This section supersedes
it, and the direction of the correction is against my own finding.

## The 3.1x is wrong. Measured live, it is 1.3x and 1.5x

The comparison above took the board's DEF and QB gaps from `evidence/blind_pass/KDST_VALUATION.md`
(QB 43.9, DEF 30.5) because that table is what the audit finding was written against. That was the
error: those numbers predate changes to both the seed CSVs and the engine. Measured on the board
the code builds **today** (`12T_ppr_K_DEF`, no picks), reading `bpa` off the rows rather than
quoting a document:

| pos | rank | board `bpa` gap | realized 2023 | realized 2024 |
|---|---|---|---|---|
| QB | 12 | 55.0 | 163.6 | 257.4 |
| RB | 32 | 194.0 | 240.9 | 253.3 |
| WR | 32 | 155.0 | 223.2 | 263.8 |
| TE | 20 | 112.0 | 136.8 | 152.3 |
| K | 12 | 13.0 | 37.0 | 55.0 |
| DEF | 12 | 18.0 | 42.0 | 58.0 |

Normalised to QB:

| pos | board / QB | real 2023 / QB | real 2024 / QB | overstated 2023 | overstated 2024 |
|---|---|---|---|---|---|
| RB | 3.53 | 1.47 | 0.98 | 2.4x | 3.6x |
| WR | 2.82 | 1.36 | 1.02 | 2.1x | 2.7x |
| TE | 2.04 | 0.84 | 0.59 | 2.4x | 3.4x |
| **K** | 0.24 | 0.23 | 0.21 | **1.0x** | **1.1x** |
| **DEF** | 0.33 | 0.26 | 0.23 | **1.3x** | **1.5x** |

**K and DEF are the two BEST-scaled positions on this board, not the worst.** RB, WR and TE are
overstated relative to QB by 2.1x to 3.6x. That is the reverse of what the section above concluded,
and the reverse of what #18 was set up to find.

## And that table cannot be trusted either, for a reason that applies to both of them

The hindsight-inflation argument above is correct as far as it goes and I then over-spent it. It
establishes that K and DEF are inflated MORE than QB, which is why normalising to QB was supposed
to be safe. It does not establish that the inflation is the same for RB, WR and TE — and measured,
it is not remotely:

| pos | sd/gap |
|---|---|
| RB, WR, TE | 0.08 – 0.09 |
| QB | 0.17 |
| K, DEF | 0.38 – 0.39 |

Three tiers, spanning nearly 5x. Normalising to QB imports QB's own inflation into every row, so a
position whose inflation differs from QB's picks up a spurious factor in whichever direction it
differs. RB/WR/TE have a fifth of K/DEF's noise-to-gap, which is almost certainly most of the
"2.1x to 3.6x overstatement" the table attributes to them. **The whole board-vs-realized comparison
is contaminated, for every position, in a direction that varies by position.** It can bound a
comparison between two positions with similar `sd/gap`; it cannot rank six.

So both of my numbers — the 3.1x and the 1.3x/1.5x that corrected it — are the wrong shape. The
estimator that is not is the slope (`materialisation_slope.py`), because it never ranks by outcome:

| pos | slope 2023 | slope 2024 |
|---|---|---|
| QB | 1.00 | 1.05 |
| RB | 1.05 | 1.07 |
| WR | 1.01 | 1.01 |
| TE | 0.99 | 1.00 |
| K | 1.00 | 1.03 |
| DEF | **1.80** | **2.84** |

Every offensive position and K sit at 1.0: their projected spread materialises, and there is no
reliability shrink to derive because there is nothing to shrink. DEF sits at 1.8–2.8: Sleeper's
weekly projections **compress** defenses, and reality widens the spread by nearly 3x. The
ruled shrink would have moved DEF in the direction the data already says it is over-compressed.

## The finding that actually blocks #18, and it is structural

**The board does not price K and DEF from the projections this instrument measures.**
`draft_room.KDST_SEEDED_SOURCE_FILES` names two committed CSVs, and
`measure_projection_accuracy`'s docstring says of them: *"which is exactly the source this reads --
so for the two positions that prompted the work, this measures the actual input the board uses."*

Measured, that sentence is false:

| artifact | DEF n | DEF r1 | DEF gap | K n | K r1 | K gap |
|---|---|---|---|---|---|---|
| Sleeper weekly-sum 2023 | 32 | 135.3 | 18.8 | 153 | 154.5 | 20.0 |
| Sleeper weekly-sum 2024 | 32 | 121.5 | 6.7 | 153 | 159.9 | 29.8 |
| **board CSV (2026-08-25)** | 32 | 111.0 | 13.0 | **37** | **116.0** | 11.0 |

DEF is plausibly the same kind of artifact — same pool size, same scale, spread inside the
season-to-season range. **K is not**: a 37-player curated pool against 153, and a top kicker 40
points lower. So for one of the two positions #18 exists to fix, this instrument has been measuring
something else the whole time, and the docstring asserted otherwise as fact.

This is the same failure as the URL bug banked in `29ab259`, one level up. There the wrong belief
was about a system we do not control and was pinned by a test. Here the wrong belief is about
**our own data lineage** — which file feeds which number — and was pinned by a docstring. Neither
could be caught by reasoning; both needed a measurement of the thing itself.

## What #18 now needs

1. **Same-season comparison of the CSV against Sleeper's weekly sum.** The CSVs are dated
   2026-08-25. Comparing them to 2024 proves nothing about lineage. A capture of **2026** weekly
   projections settles it: if the CSV is the weekly sum, the slopes above are valid for the board's
   input and DEF's 1.8–2.8 is the answer. If it is not, the board's K/DEF input has no measured
   reliability at all and #18 needs a different source.
2. **If they are different artifacts:** the board's K/DEF input can only be validated against a
   season that has finished, which means a CSV of 2023 or 2024 vintage. None was kept. Whether one
   can be re-obtained is a question for the owner, not something to infer.

## Register, revised

- The `POST_AUDIT_PLAN.md` entry written before this section reports the 3.1x. It is corrected
  there too; this file is the authority.
- **No shrink, and now for a stronger reason than "the estimator is wrong":** measured over the
  population, five of six positions have a slope of 1.0 and nothing to shrink, and the sixth is
  compressed rather than inflated.
- **NEW, and it is an engine-design question, so it goes to the owner rather than into a repair
  (#184):** the board puts `points_vor_draftsharks` (QB, RB, WR, TE) and
  `points_vor_sleeper_seeded` (K, DEF) on ONE `bpa` scale and compares them directly. Two vendors,
  one number, and nothing establishes that their point scales agree. `bpa_source` already records
  which row came from which. That is the structural candidate for the K/DEF mispricing, and it is
  upstream of every reliability question asked so far.

---

# THIRD PASS: lineage settled on a 2026 capture, and #18's premise does not survive it

`lineage.py`, run against the owner's 2026 projections capture — the CSVs' own vintage, because a
2026 CSV against 2024 weekly projections reports the gap between two seasons and calls it the gap
between two sources.

## The CSVs are not the weekly projections, for EITHER position

| joined player by player, 2026 | top-12 r | se | whole-pool r | se | top-12 scale |
|---|---|---|---|---|---|
| DEF (joined on team) | **−0.226** | 0.33 | 0.583 | 0.19 | 1.081 ± 0.098 |
| K (joined on last name, team) | **0.708** | 0.33 | 0.598 | 0.18 | 1.284 ± 0.034 |

**And the second pass had the two positions backwards.** It concluded "DEF is plausibly the same
artifact for a different season. K plainly is not," reasoning from pool sizes and top-of-pool
levels. Measured player by player, K is the closer match: inside the starting band its ordering
agrees at 0.708 and its scale factor is 1.284 with a standard deviation of 0.034, which is a
rescale of one underlying number. DEF is the looser one, and in the band that matters — the twelve
**starting** defenses, where a draft does all its discriminating, r is **−0.226**. Their *levels*
agree (1.081); their *ordering* does not.

At n=12, se ≈ 0.33, so −0.226 is indistinguishable from zero. What it is distinguishable from is
1.0. Two copies of one artifact cannot do this.

The pool-size argument that produced the backwards call was not wrong about the pool sizes — K's
CSV really is 37 players against 153. It was wrong to treat a pool-size difference as the thing
that decides lineage, when the curated 37 are simply the 37 kickers anyone would draft. **A
difference in what a file CONTAINS is not evidence about where its NUMBERS came from.**

## The question #18 was actually asking, answered

Lineage is a question about our files. The engine question is whether a projection predicts
**ordering** inside the starting band, which is the only band a draft discriminates in. Spearman,
projected against realized, on the two seasons that have finished:

| pos | band | 2023 | 2024 | se |
|---|---|---|---|---|
| QB | 12 | 0.52 | 0.74 | 0.33 |
| RB | 32 | 0.68 | 0.87 | 0.19 |
| WR | 32 | 0.64 | 0.69 | 0.19 |
| TE | 20 | 0.92 | 0.63 | 0.24 |
| **K** | 12 | **0.41** | **0.20** | 0.33 |
| **DEF** | 12 | **0.75** | **0.48** | 0.33 |

**DEF ranks about as well as QB.** K is the weak one, and its 2024 figure sits within one standard
error of zero.

So **#18's founding premise is not supported**: the position whose projections fail to order the
starting band is K, not DEF — and DEF, the position the whole investigation was opened for, is
middling rather than broken. Every earlier pass in this file, mine included, was looking for a DEF
reliability defect. The measurement does not find one.

Say the limits plainly: a twelve-player band has se ≈ 0.33 and there are two seasons, so this
separates K's 0.20 from RB's 0.87 and separates nothing else. DEF 0.48 against QB 0.52 is one draw
each of the same number. **No constant is derivable from this** (#56), and four numbers spanning
two seasons at se 0.33 is not a population for one.

## What is now established, and what it costs

1. **The ruled `bpa` shrink is dead three times over.** The estimator was n=1; the population slope
   says five of six positions have nothing to shrink and DEF is *compressed*; and the ordering
   measurement says DEF is not the unreliable position in the first place.
2. **Every K and DEF reliability number this instrument has ever produced is about Sleeper's weekly
   projections, not about the board's input** — for both positions, now measured rather than
   assumed. The board's actual K/DEF input has **never been validated against a result**, and
   cannot be from data that exists: validating it needs a CSV of 2023 or 2024 vintage, and none was
   kept.
3. **One actionable, cheap possibility**, offered as a candidate and not a conclusion: the weekly
   projections the app already fetches have *measured* ordering skill for DEF (0.75 / 0.48). The
   CSV's has never been measured and cannot be. Pricing DEF off the measured source rather than the
   unmeasurable one is a change with an argument behind it — but it is an engine-design change, so
   it goes to the owner (#184), and it must not be read as established that it would be better.
4. **`#28` stands unchanged and is now the strongest remaining candidate**: two vendors,
   `points_vor_draftsharks` and `points_vor_sleeper_seeded`, compared directly on one `bpa` scale
   with nothing establishing their point scales agree. Three passes of reliability measurement have
   found no DEF reliability defect, which makes an unmeasured scale offset the more likely
   explanation for defenses going five rounds early.

## The lesson this pass earned

The first two passes each reached a confident conclusion from a quantity that was *adjacent* to the
question: a two-player ratio for a population question, a stale document for a live board, pool
sizes for a lineage question. Each was checkable and none was checked before being written down.
The pattern is not carelessness about arithmetic — every number was correct. It is **answering with
the nearest available measurement instead of the one the question asks for**, and the tell is the
same every time: the quantity is cheap to get and the question is not.
