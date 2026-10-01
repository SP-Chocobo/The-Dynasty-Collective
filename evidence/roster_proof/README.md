# Roster-proof evidence — #205

> ## ⚠️ STILL VALID, BUT NO LONGER THE WHOLE ANSWER — read `README_FF.md` beside it
>
> Nothing in this file is withdrawn. Every number below was correctly measured and reproduces.
> What changed is that it is now **one of two** control-vs-engine results, and the other one
> disagrees:
>
> | run | league | rounds | seats | `points` wins | margin |
> |---|---|---:|---:|---:|---:|
> | **this file** (`#205`) | fixture, 6 formats | 14–15 | 68 | 1 of 68 | −5% to −11% |
> | `README_FF.md` (`#245`) | Fourth and Forever | 26 | 12 | 10 of 12 | +1.04% |
>
> Same harness — same `scoreable_pool`, `run_one`, `score_roster`, `RULERS`, `COMPARE_ON` — with
> only the LEAGUE swapped. The sign of the `points` difference is therefore a property of the
> league, not of the engine, and `#245`'s length cut proves it is not the round count either
> (F&F at a matched 15 rounds returns `points` identical to the cent).
>
> **So the deficit recorded below must not be cited as a property of the engine.** It is a
> property of the engine *in these six fixture formats*, none of which is the league the owner
> plays. Cite it that way, or cite both.


The control-vs-engine proof: does the engine build BETTER ROSTERS than a competent projection
ranking? Distinct from the #150 battery, which asks only whether the engine breaks its league's
rules. An engine that always drafts the highest-projected player available is perfectly legal
and completely pointless; both gates are needed and neither substitutes for the other.

Committed for the reason the instrument itself is committed: **#177's harness lived only in a
scratchpad and is gone**, so its numbers can be neither re-derived nor challenged (#208).

## Naming

    ROSTER_PROOF_<date>_<what-it-is>_<commit>.json

The commit is the one the run STARTED at.

## Runs

### ⛔ WITHDRAWN — THE RUN BELOW PREDATES #213

`run_roster_proof` builds its six boards with `build_mock_league`, which until `028b574` emitted
a ONE-KEY scoring dict. Both arms were therefore compared inside a league in which quarterbacks
score nothing and receivers are paid one point per catch.

**Both arms were equally affected, so this is not a broken comparison — it is a comparison of a
different question.** Worse for this instrument specifically: the CONTROL ranks by
`projected_points`, which under that rulebook is reception counts for RB/WR/TE and vendor points
for QB. The control's own ruler was a mixed unit, so the `points` column cannot be read at all.

The 44/44 vs 0/44 split below must NOT be quoted. Re-run in flight on the real rulebook.

---

### ROSTER_PROOF_2026-09-08_partial_4of6_3198a9e — PARTIAL, 4 of 6 formats

`complete: false`, `formats_done: 4`, 1,586s. **The process was killed at 04:13** — no error, no
traceback, no OOM (14.4 GB free) and no disk pressure; it coincides with an unrelated background
watcher exiting. The two unrun formats are `12T_standard` and `12T_ppr_TEP`.

**This file exists at all only because the report is written after every format.** That change was
made hours earlier for exactly this reason and had not yet been needed. Recorded here because a
protection that silently pays off is worth naming when it does.

    format        rounds  [cdme / total]                    [points / starter]
    12T_ppr         14    eng   -5.98  ctl -168.28  12/12   eng  610.76  ctl  840.61   0/12
    12T_ppr_SF      15    eng  440.99  ctl  150.95  12/12   eng 1077.09  ctl 1147.53   0/12
    10T_ppr         14    eng  -24.30  ctl -173.21  10/10   eng  663.82  ctl  863.90   0/10
    10T_ppr_SF      15    eng  578.00  ctl  186.28  10/10   eng  988.58  ctl 1203.87   0/10

**Every seat, every format, both directions.** The engine wins the asset ruler 44/44 and loses
the season-points ruler 0/44. That is pre-registration outcome 3, and it is not close or noisy.

READ THIS WITH THE PRE-REGISTRATION, NOT INSTEAD OF IT. In particular:

- The cdme totals for the 1QB arms are NEGATIVE for both sides (engine −5.98 against control
  −168.28). That is the named contamination: `total_value` sums below-replacement negatives, and
  what a below-replacement player is worth to own is RESERVED (#155/#165). The engine wins by
  being far less negative. Both arms are contaminated identically so the COMPARISON stands; the
  absolute figures are not roster worth and must not be quoted as such.
- The points deficit is much larger in 1QB (−230, −200 on ~840–860) than in superflex (−70 on
  1147). Whatever drives it is stronger where the engine cannot spend a pick on a second QB.
- 4 of 6 formats is not the ordered run. `12T_standard` and `12T_ppr_TEP` are absent, and the
  scoring axis they were chosen to test is therefore untested here.

### ROSTER_PROOF_2026-09-08_realrules_5of6_ef98dd9 — 5 of 6, REAL 64-key rulebook

The first roster proof measured against a league that exists. `scoring_keys: 64`,
`season_projections_priceable: 840` of 5,346 supplied, pool 481.

**Incomplete because the CONTAINER RESTARTED mid-run**, not because anything failed. It survives
at all only because the report is written after every format (#205's own durability fix). The
battery running beside it had no such fix and lost all 11 of its completed arms -- that gap is
closed in the same commit as this file.

| format | asset ruler | eng vs ctl | points ruler | points gap | starters filled |
|---|---|---|---|---|---|
| `12T_ppr` | 12/12 | 333.3 vs 188.0 | 0/12 | **-11.2%** | 8/8 |
| `12T_ppr_SF` | 12/12 | 791.5 vs 489.3 | 1/12 | **-5.0%** | 9/9 |
| `10T_ppr` | 10/10 | 358.3 vs 185.7 | 0/10 | **-9.7%** | 8/8 |
| `10T_ppr_SF` | 10/10 | 868.3 vs 541.2 | 0/10 | **-11.1%** | 9/9 |
| `12T_standard` | 12/12 | 316.5 vs 99.8 | 0/12 | **-9.8%** | 8/8 |

**Totals: asset ruler 56/56. Points ruler 1/56.**

THREE THINGS THIS ESTABLISHES, and one it does not.

1. **The engine builds materially higher-asset rosters, every seat, every format.** 56 of
   56, with control means it roughly doubles or better.
2. **It fields fewer projected points, by 5-11%.** Not the 27% an earlier summary quoted -- that
   figure came from the withdrawn stub-rulebook run and is void.
3. **The deficit is NOT a lineup artifact.** Every seat of every format fills its lineup
   completely (8/8 in 1QB, 9/9 in superflex). The engine is not failing to field a team; it is
   fielding a different one on purpose.

WHAT IT DOES NOT ESTABLISH: whether that trade is correct. There is no established exchange rate
between present-season points and dynasty asset value in this system, so "good dynasty
construction" and "systematic mispricing" both fit these numbers. That is #50/Phase 3, and it is
the owner's call, not a number this instrument can produce.

AND ONE HYPOTHESIS THIS KILLS: the earlier "the deficit is much worse in 1QB than superflex"
pattern does NOT survive. On the real rulebook the SF arms straddle the 1QB ones (-5.0% and
-11.1% against -11.2% and -9.7%). It was an artifact of a rulebook in which quarterbacks scored
zero, which is exactly where a 1QB/SF difference would be manufactured.


---

# COMPLETE, 6 of 6 -- `ROSTER_PROOF_2026-09-08_realrules_COMPLETE_6of6.json`

This SUPERSEDES the 5-of-6 partials above. It is the answer to #205.

**It is a JOIN ACROSS TWO PROCESSES** (#215), and says so in its own header:
`commits_present: ["8cee942", "cf0b283"]`, `carried_forward` naming the five formats the
second process did not recompute. That is legitimate here and the legitimacy is MEASURED, not
assumed -- the two 5-of-6 runs above ran at DIFFERENT COMMITS (ef98dd9, cf0b283) and produced
byte-identical numbers for all five shared formats, down to the per-seat detail. Zero
non-timing differences. `test_resume_join.py` reads both files and fails if that stops being
true.

Why a join at all: the container is reclaimed on OPERATOR inactivity, not the job's. Three runs
were killed today, twice at 67s and 45s into the SIXTH format after 45 and 30 minutes of work.
Writing after every format (#213b) made that survivable; it did not make it finishable.

| format | asset ruler | mean advantage | points ruler | points gap | starters filled |
|---|---|---|---|---|---|
| `12T_ppr` | 12/12 | +78.2% | 0/12 | **-11.2%** | 8/8 every seat |
| `12T_ppr_SF` | 12/12 | +61.8% | 1/12 | **-5.0%** | 9/9 every seat |
| `10T_ppr` | 10/10 | +93.2% | 0/10 | **-9.7%** | 8/8 every seat |
| `10T_ppr_SF` | 10/10 | +60.5% | 0/10 | **-11.1%** | 9/9 every seat |
| `12T_standard` | 12/12 | +217.9% | 0/12 | **-9.8%** | 8/8 every seat |
| `12T_ppr_TEP` | 12/12 | +54.1% | 0/12 | **-10.6%** | 8/8 every seat |

**TOTALS over 68 seats: asset ruler 68/68. Points ruler 1/68.**

The sixth format, TE premium, changes nothing. It lands inside the band the other five already
described (-10.6% points, +54.1% asset, every lineup full), so no format-specific effect
survives the completed set. The three conclusions and the one killed hypothesis recorded for the
5-of-6 partial stand unchanged on the full six, and the exchange-rate question they leave open is
still #50/Phase 3 and still the owner's.
