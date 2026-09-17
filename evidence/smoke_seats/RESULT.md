# `#285` smoke seats — the result

> Runs against `evidence/smoke_seats/PREREGISTRATION.md`, committed at `9273a2c` **before** the
> runner existed. Nothing below was added to the acceptance criteria after seeing the numbers.

Produced by `run_smoke_seats.py` at commit `9273a2c`. Universe 6,595 players, priced pool 481,
ADP table 840 ranked (4,506 undrafted-sentinel rows excluded). **6 formats, 68 seat runs**, one
draft per seat per format, 2,720.3s.

**Reproduced.** The run was repeated after `composition_by_style` was added to the report, and all
six formats returned **byte-identical** `by_ruler` results on both rulers. The instrument is
deterministic and the added recording changed nothing about the drafting — which is what makes
identical numbers the expected outcome here rather than the `#245` alarm.

| format | teams | superflex | scoring | TE premium | rounds | seat runs |
|---|---|---|---|---|---|---|
| `12T_ppr` | 12 | no | ppr | no | 14 | 12 |
| `12T_ppr_SF` | 12 | **yes** | ppr | no | 15 | 12 |
| `10T_ppr` | 10 | no | ppr | no | 14 | 10 |
| `10T_ppr_SF` | 10 | **yes** | ppr | no | 15 | 10 |
| `12T_standard` | 12 | no | **standard** | no | 14 | 12 |
| `12T_ppr_TEP` | 12 | no | ppr | **yes** | 14 | 12 |

**The admission gate excluded `run_follower` in all six formats** — it could not fill 100% of
its starting slots, so it never sat. The field was `adp`, `need_first` and `points_need`,
dealt round-robin across the eleven (or nine) non-engine seats.

## The aggregate — and why it is the least useful number here

| format | `cdme` (TAUTOLOGY) | `points` (strong claim) |
|---|---|---|
| `12T_ppr` | 12/12, +50.63% | 11/12, **+2.13%** |
| `12T_ppr_SF` | **4/12, −3.56%** | 6/12, +0.51% |
| `10T_ppr` | 10/10, +61.62% | 10/10, **+2.02%** |
| `10T_ppr_SF` | **1/10, −18.75%** | **5/10, −0.90%** |
| `12T_standard` | 12/12, +158.91% | 12/12, **+5.15%** |
| `12T_ppr_TEP` | 12/12, +57.03% | 12/12, **+2.63%** |

Read alone, that table says *the engine wins the strong claim in five of six formats*. Criterion
4 of the pre-registration said in advance not to read it alone: *"an aggregate that hides a loss
to one style is the result hiding its own most interesting part."* It does.

## THE FINDING: the engine does not beat the market, it beats the naive drafters

`points` ruler, engine against each style separately, pooled over every seat run:

| format | vs `adp` (market) | vs `need_first` | vs `points_need` |
|---|---|---|---|
| `12T_ppr` | **5/12, −0.35%** | 12/12, +3.63% | 12/12, +3.56% |
| `12T_ppr_SF` | **4/12, −1.13%** | 11/12, +1.66% | 9/12, +1.19% |
| `10T_ppr` | **2/10, −0.63%** | 10/10, +3.31% | 10/10, +3.48% |
| `10T_ppr_SF` | **0/10, −2.42%** | 6/10, −0.19% | 5/10, −0.06% |
| `12T_standard` | 12/12, +1.79% | 12/12, +7.09% | 12/12, +7.28% |
| `12T_ppr_TEP` | 7/12, +0.51% | 12/12, +3.73% | 12/12, +4.08% |

**Against market-consensus ADP the engine is behind in four of six formats, level in a fifth,
and ahead only in standard scoring — and that one win is against a mis-specified control (see
below).** Against the two projection-led styles it wins almost everywhere, by three to seven
percent.

The aggregate is arithmetic over a field in which eight of eleven seats are projection-led. It
is not wrong; it is answering *"does the engine beat this particular mixture"*, and the mixture
is doing most of the work. On the question the owner asked — **is it good at drafting** — the
honest reading is: **better than a naive projection-plus-need drafter, not better than the
market.**

This is RULE 6 arriving in a subtler form than the one it was written for. The rule was written
after a projection-only control took 24 consecutive QBs and the engine "won" by +503%. Nothing
that crude happens here — every admitted style fills a legal lineup, which is what the gate is
for. But `adp` is the only style in the field that encodes what humans actually do, and it is
the only one the engine cannot beat.

## The round-one attribution — who actually took those QBs

Recorded per style (`composition_by_style`), pooled over every seat run. The pooled counter used
to say only *"7 of 12 round-one picks were QBs"*, which cannot distinguish a finding about the
engine from a strawman field:

| format | `adp` | ENGINE | `need_first` | `points_need` |
|---|---|---|---|---|
| `12T_ppr` | 0% QB | 0% QB | 50% | 47% |
| `12T_ppr_SF` | 0% QB | 8% | 50% | 44% |
| `10T_ppr` | 0% QB | 0% QB | 33% | 50% |
| `10T_ppr_SF` | 0% QB | **60%** | 33% | 47% |
| `12T_standard` | 0% QB | 0% QB | **100%** | **100%** |
| `12T_ppr_TEP` | 0% QB | 0% QB | 38% | 33% |

Two things fall out of it, and both change how the numbers above should be read.

**`12T_standard` is a strawman and now it is proven, not inferred.** `need_first` opens with a QB
**48 times out of 48** and `points_need` **36 out of 36** — 100% of round-one picks, in a **one-QB
league**. That is RULE 6's original failure mode exactly, reproduced by two of the three styles.
The engine opens RB 12/12 there, which is sane. Its +7.09% and +7.28% margins over those two
styles measure the gap between a sane drafter and a broken one, and nothing else.

**CORRECTION — `adp` IS PPR-ONLY, AND THAT REACHES FURTHER THAN FIRST REPORTED.** The table is
built from a single field, `adp_dd_ppr`. There is no superflex variant and **no standard
variant**. The first version of this section flagged only the two superflex arms; it should also
have flagged `12T_standard`, where the market control drafts a **PPR-ordered board in a standard
league** and over-weights receptions that score nothing. That is the one format in which the
engine beats `adp`, so **that win is against a mis-specified control too**.

Stated plainly, because it is the load-bearing consequence: **the engine does not cleanly beat a
correctly-specified market control in any format measured here.**

**The superflex half of the same gap.** It takes **0% QB in
round one in every format, superflex included** — a single static consensus table applied
unchanged to a format where the real human market moves QBs sharply up. In `10T_ppr_SF` the
engine goes QB 6/10 in round one, so **the engine responds to superflex and the control does
not**. The engine still loses to it 0/10 on `points` there, which is a real result, but against a
control that is mis-specified for the format.

**This leaves three clean comparisons** — the 1QB PPR formats, the only ones where `adp` is on
its home ground: `12T_ppr` (5/12, −0.35%), `10T_ppr` (2/10, −0.63%), `12T_ppr_TEP` (7/12,
+0.51%). Against market consensus on its own terms the engine is **at parity — neither ahead nor
behind by a margin this run can resolve.**

**And parity on `points` is not a null result that further sampling will resolve.** It is
ambiguous between two readings this instrument cannot separate: the engine correctly trading
present-season points for future asset value, which is what a dynasty engine *should* do, and the
engine having no edge. The only other ruler available is `cdme`, where a win is a tautology by
construction. `FREEZE_CHECKLIST.md` already states the reason — there is no established exchange
rate between present-season points and dynasty asset value. **Separating the two readings needs a
ruler on a dynasty horizon, which `#288` establishes cannot be built from anything in this
repository; it is not a matter of more formats or more leagues.**

## Two qualifications that cut AGAINST the engine

**1. `12T_standard`'s +5.15% is the weakest result in the set, not the strongest.** Its field
collapses: `need_first` averages 10.94 on `cdme` and `points_need` averages **−2.90** — a
negative asset total. Standard scoring inverts the projection-led styles' ordering (raw QB
projections dominate when receptions score nothing) and they draft accordingly, at a 100%
round-one rate as the attribution table above shows. The engine's largest margin is measured
against the most broken field, which is the definition of the strawman this pre-registration set
out to avoid. Treat `12T_standard` as uninformative about quality.

**2. The engine loses on `cdme` — its own objective — in both superflex formats.** `4/12` at
−3.56% and `1/10` at −18.75%. A `cdme` win is a tautology because the engine approximately
maximises `cdme`; a `cdme` **loss** is therefore not a tautology, it is the engine being beaten
at the thing it is trying to do. Per style, in `10T_ppr_SF` it is `0/10` against `need_first`
(−26.91%) and `0/10` against `points_need` (−30.39%). This is the same region `#184` names as a
bounded limitation — where the startable floor overrides the demand model — and the same region
`#177`'s single loss lived in. **This run makes that limitation larger and better evidenced than
`#184` currently records it.**

## Acceptance criteria, discharged

1. **PRIMARY, `points` ruler** — reported above, per format and per style.
2. **`cdme` reported and labelled a TAUTOLOGY** — done, in every table and in the console output.
3. **No single verdict emitted** — both rulers side by side throughout; no composite score exists.
4. **Per-style breakdown** — the section above. It carries the finding.
5. **Non-vacuity** — `n` on every rate (68 seat runs; 30–48 style-seats faced per cell), pool 481
   stated, styles admitted stated, the excluded style named.

## What this does NOT establish

- **Not a benchmark.** These are simulated fields on one capture. The owner's standing caveat
  applies: league settings vary enormously, and **no engine constant may be calibrated to this
  result.** Nothing here is a tuning target — that refusal was pre-registered and is kept.
- **Not a verdict on the market.** `adp` here is a static consensus table, not live human
  drafters reacting to a board — and it carries no superflex variant, so it is a valid control
  only in the 1QB formats.
- **Not a replacement for Gate 1 (`#284`)**, which answered legality across 34 formats. This
  answers quality across 6.
