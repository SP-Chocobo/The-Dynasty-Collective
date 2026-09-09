# ABLATION RESULT: the mode boundary IS causally active — and is NOT the whole cause

Pre-registered in `PHASE4_WITHDRAWAL_AND_THE_MODE_BOUNDARY.md` **before** the run. One arm,
`mode="balanced"` forced for all 26 rounds, everything else identical — same fixture, same
universe, same seats, same pick order. No engine source changed. 1,016s.

---

## The control passes

`mode="auto"` IS balanced for rounds 1–14, so the two arms must be identical there or the
ablation is toggling more than one thing.

**168 of 168 picks match, player for player.** The arms diverge at exactly pick 169 — round 15,
`UPSIDE_MODE_DEFAULT_ROUND`. The instrument is clean.

## The pre-registered test

> *"If the TE share in rounds 15–26 collapses toward the balanced-mode 15.5%, the mode boundary
> is causally active... If it does not collapse, the boundary is a coincidence of this draft and
> the mode hypothesis dies with it."*

| rounds 15–26 | QB | RB | WR | **TE** |
|---|---|---|---|---|
| AUTO (upside) | 0.0% | 27.8% | 20.1% | **52.1%** |
| ABLATION (balanced) | 0.0% | 25.0% | 45.1% | **29.2%** |

**TE 52.1% → 29.2%.** It moved 22.9 points and closed **63%** of the gap to the human number.
That is not noise and not a coincidence of sampling: it is one toggle, one boundary, and a
23-point swing in the half of the draft the toggle governs.

**The mode boundary is causally active. That is now demonstrated, not hypothesised.**

## And it is NOT the whole cause — three ways

**1. A large residual survives.** 29.2% is still nearly double the humans' 15.5%. Something
other than upside mode is putting tight ends on these rosters in the back half.

**2. It trades one over-allocation for another.** Whole draft:

| | QB | RB | WR | TE |
|---|---|---|---|---|
| AUTO | 10.3% | 26.9% | 30.4% | **32.4%** |
| ABLATION | 10.3% | 25.6% | **42.0%** | 21.8% |
| twelve real managers | **20.0%** | 27.4% | 37.1% | 15.5% |

TE improves by 10.6 points; WR gets *worse* by 4.9 (30.4 → 42.0 against a human 37.1). Forcing
balanced everywhere is not a fix — it relocates the excess.

**3. Roster shape gets WORSE, not better.** Per-seat concentration:

| | largest single-position pile | seats with ≥12 at one position | (seat, position) pairs at ≤2 bodies across RB/WR/TE |
|---|---|---|---|
| AUTO | 12 | 3 | **0** |
| ABLATION | **19** | **7** | **7** |

The balanced arm builds monocultures the auto arm does not: seat 3 finishes 19 WR / 1 TE, seat
6 finishes 18 WR / 2 RB, seat 12 finishes 15 TE. Upside mode's late-round variety is doing real
work, and removing it is a regression on the dimension #154's backstop exists to protect.

## A claim of mine that this KILLS

I wrote that the zero QBs in rounds 15–26 were "the same fact" as the TE shape — floor stops
clearing, position unpriced, unpriced sorts last, all downstream of the mode boundary.

**Wrong.** QB is **0.0% in rounds 15–26 in BOTH arms**, and 10.3% overall in both. The mode
toggle does not move quarterbacks by a single pick. B2 (the engine cannot value a backup
quarterback) is untouched by this boundary and remains its own unexplained defect, exactly where
it was.

---

## Where this leaves #216

**The largest single identified contributor is now measured**, and it is not a valuation defect.
It is the scope of a documented design choice: from round 15 the engine stops being roster-aware,
and in a 26-round startup that is 46% of the draft. Five components stayed exonerated through
this — `replacement_levels`, `displacement_level`/the optimizer, the anchor's provenance,
`narrow_candidates`/`_board_order`, and the feasibility backstop.

**What this does NOT license:**

- **Not a fix.** "Force balanced" is measured and rejected on its own evidence: worse WR
  allocation, worse monocultures, no QB movement. Do not ship it.
- **Not a licence to tune `UPSIDE_MODE_DEFAULT_ROUND`.** Moving 15 to some other integer that
  makes this league's numbers nicer is precisely the calibrated constant #56 forbids, and it
  would be fitted to one draft in one format.
- **Not a closed question.** 37% of the excess is still unattributed.

**What it does support**, as a question for the owner rather than an action:

`UPSIDE_MODE_DEFAULT_ROUND` is a fixed ROUND INDEX. It buys 26% of a 19-round draft and 46% of
this 26-round one — the same constant means a different fraction of every format, and nothing
derives it from the draft's own length or from when starter demand is actually satisfied. That
is a #56-shaped question that stands on its own, independent of whether it would improve this
draft's numbers, and it should be answered as a derivation, not a tuning.

The residual — what puts tight ends at 29.2% in a balanced back half — is the next question,
and it has no suspect yet.
