# `#52` findings ledger — triage, provenance, and interweaving

> **NOTHING IS FIXED FROM THIS LEDGER UNTIL THE WAVES STOP.** Two reasons. The frozen artifact
> must stay frozen or later waves are not attacking the same target, and the owner's instruction
> stands: build the whole list first, because several of these are larger-scoped or interwoven
> than they look one at a time.
>
> Verdicts are mine, not the passes'. A finding in `wave1/PASS_*.md` is a CLAIM; this file says
> what survived checking.

## Verdict vocabulary

| verdict | meaning |
|---|---|
| **REPRODUCED** | I re-ran it myself and got the reported result |
| **CONFIRMED** | I verified the structural claim directly (read the code / grepped the caller) |
| **CORROBORATED** | both passes found it independently with separate measurements; I have not re-run it |
| **UNVERIFIED** | single pass, plausible, not yet checked |

Novelty is **NEW** or **KNOWN-#nnn**. A KNOWN finding is not worthless — an independent blind
pass reaching a registered item is corroboration that it is real and still live.

## Wave 1 — the ledger

| id | finding | verdict | novelty | class |
|---|---|---|---|---|
| **W1-01** | `displacement_adj` goes **POSITIVE** (+79.44, Travis Hunter) on an IDP league, against a contract that calls it non-positive *by construction*; the pinning test uses `superflex=False` with no IDP slot | **REPRODUCED** | **NEW** | correctness + vacuous pin |
| **W1-02** | `time_horizon_adj` differences percentiles taken over two **different populations**; 225–256 priced rows carry no `proj_3yr` | **CORROBORATED** (A and B, separate numbers) | **NEW** | correctness |
| **W1-03** | Anchor / roster-points cache fingerprint omits `injury_status`, `status`, `years_exp`, names and aliases; stale levels served | **CONFIRMED** (fingerprint block has none of them) | **NEW** | correctness |
| **W1-04** | `test_need_bonus_cannot_flip_a_large_universal_value_gap` is a **tautology** — asserts `top−bottom > MAX` then `top−(bottom+MAX) > 0`, never reads a row's `need_bonus` or `final_score` | **CONFIRMED** (read it) | **NEW** | vacuous test |
| **W1-05** | `prose_names` history shield exempts ~40% of prose blocks carrying a backticked name (`was` alone ~30%); 15–19 dead names hidden; `numeric_constants()` misses derived constants it claims to read | **CORROBORATED** (A 43%/15, B 39.5%/19) | **NEW** | instrument |
| **W1-06** | `test_missing_proj_3yr_is_neutral_not_a_penalty`, cited at `draft_room.py:3137` as proof of W1-02's premise, **does not exist** | **CONFIRMED** (only the citation exists) | **NEW** | false claim |
| **W1-07** | `survival_is_presentable` gates nothing in `app.py` (**0 occurrences**); `pick_necessity` carries a 20% survival weight and is displayed | **CONFIRMED** (grep) | **NEW** | contract breach |
| **W1-08** | `league_config`'s `admits_decision` / `confirmation_state` blocking contract has **no production caller**; and as written would mark the certified fixture league AMBIGUOUS | **CONFIRMED** (no caller) | **NEW** | dead contract |
| **W1-09** | `quantity_readers` classifies `displacement_adj`, `time_horizon_adj`, `risk_adj` as OBSERVABLE though each is an addend of `universal_value` | **UNVERIFIED** | **NEW** | instrument |
| **W1-10** | Two incompatible take models feed one necessity score; `expected_taken` sums to 23.32 over 22 picks | **UNVERIFIED** | KNOWN-`#244`/`#245` family | correctness |
| **W1-11** | Adjustment constants sized for a 0–100 scale now applied to raw points; the prose still describes the old unit | **CORROBORATED** | KNOWN-`#75` | stale prose + sizing |
| **W1-12** | `sleeper_points = scored if scored != 0 else None` collapses a measured zero into "unmeasured", then labels it a coverage gap | **CORROBORATED** | KNOWN-`#187` family | absence contract |
| **W1-13** | `feasibility_first` uses `len(roster_positions)` (includes IR) where `draft_rounds` is absent; mock path reachable | **UNVERIFIED** | **NEW** | correctness |
| **W1-14** | `starter_slot_counts` docstring says the measured flex share is "always supplied"; the seam returns `None`; `slot_share_basis` reaches no production surface | **UNVERIFIED** | KNOWN-`#178` adjacent | false claim |
| **W1-15** | Day-resolution freshness subtraction still shipped where the docstring calls it a fixed defect | **UNVERIFIED** | **NEW** | stale claim |
| **W1-16** | Two homes for the undrafted-slot vocabulary (`HORIZON_UNDRAFTED_SLOTS` vs `league_config.UNDRAFTED_SLOTS`) | **UNVERIFIED** | **NEW** (`#126` class) | duplication |
| **W1-17** | Banker's rounding in `_remaining_demand_rank`; half-share flex leagues land on round-half-even, not a derived rule | **UNVERIFIED** | KNOWN-`#86` | knife-edge |
| **W1-18** | `replacement_levels` end-of-list clamp contradicts `horizon_replacement`'s refusal of the same case | **UNVERIFIED** | KNOWN-`#155` adjacent | inconsistency |
| **W1-19** | `test_one_pricing_universe` asserts a literal source string; correct `**pricing` forwarding would fail it, a comment passes it | **UNVERIFIED** | **NEW** (`#200` class) | instrument |
| **W1-20** | Multi-eligible bucket inconsistency: priced at the vendor position, counted for demand at the first listed | **UNVERIFIED** | KNOWN-`#172` family | inconsistency |

## The interweaving — why these must not be fixed one at a time

Three clusters, and the first is the one that changes how the rest should be read.

### Cluster 1: THIS PROJECT'S OWN REPAIRS CREATED THE TWO WORST FINDINGS

- **`#172` recovered Travis Hunter** from the identity partition — correct, and it is what makes
  **W1-01** reachable. A multi-eligible player was the precondition for the positive
  `displacement_adj`; before that repair the population was empty.
- **`#180`/`#192` routed offence through the scoring-aware path** — correct, and it is what makes
  **W1-02** real. The comment at `draft_room.py:3135` asserting no priced row lacks `proj_3yr`
  was TRUE when written; the repair priced players the vendor never covered and silently falsified
  it.

Neither repair was wrong. Both widened a population that an older invariant had quietly assumed
away. **The lesson is not "be careful" — it is that this repository has no mechanism that
re-checks a stated invariant when the population it ranges over changes.** That is a structural
gap, and fixing W1-01 and W1-02 individually leaves it open.

### Cluster 2: THE INSTRUMENTS THAT SHOULD HAVE CAUGHT CLUSTER 1 WERE THEMSELVES BLIND

**W1-05** (prose shield hides ~40%), **W1-06** (a comment cites a test that does not exist),
**W1-04** (the invariant test is a tautology), **W1-09** (load-bearing terms classified as
observable), **W1-19** (a text-scan where an AST scan exists next door).

W1-06 is the join: the dead test name would have been caught by `prose_names`, except the history
shield exempted the block. **The instrument that would have flagged the stale claim was hiding
it.** And `#283`/`#286` extended that instrument during this session and reported the sweep clean
— a result that was a property of the filter, not of the prose.

Fixing the shield first would likely surface more of Cluster 1 for free. **That is an argument
for ordering, which is exactly what a one-at-a-time repair pass would miss.**

### Cluster 3: SURVIVAL IS WITHHELD AT THE HEADLINE AND LEAKS THROUGH THE DERIVATIVES

**W1-07** (necessity carries 20% survival and is displayed; the "derived fields" list omits it)
and **W1-10** (two take models, one of which manufactures the zeros `#187` forbids). `#206` chose
an enforced refusal; the refusal covers the number and not its consequences.

## Wave 2 — NOT clean, and not close

Eight new findings, plus convergence on Wave 1's core at a rate that settles those beyond doubt.

| id | finding | verdict | novelty |
|---|---|---|---|
| **W2-01** | Contested-identity guard is a function of the REMAINING pool — drafting one twin hands the survivor the vendor record (`trade_value 99.0`, `proj_3yr 840.0`, `identity_basis "matched"`); the roster side never applies the rule at all | CORROBORATED (measured) | **NEW** |
| **W2-02** | `qb_startable_floor` is in VENDOR units, compared against league-scored points. Holds on the fixture by coincidence; on a 4-pt-pass-TD rulebook, QBs in the overall top-24 go **11 → 0** | CORROBORATED (measured) | **NEW** |
| **W2-03** | Superflex: once the startable QB tier is drafted, all 116 remaining QBs are unpriced, sorted below every priced row, and **10 carry `absence_kind=None`** against a stated invariant | CORROBORATED (measured) | **NEW** |
| **W2-04** | `block_opportunity` is **unreachable in production** — 0 fires across 10 board states / 460 candidates; docstring claims ~28% | CORROBORATED (measured) | **NEW** |
| **W2-05** | `trade_value` branch omits `truncated_out=`, clamps to the bottom of a 2-row list, stamps `live_starter_demand`. **Binds on the owner's own league**, on the branch the `#155` fix never reached | CORROBORATED (measured) | **NEW** |
| **W2-06** | QB floor + shared-slot alternative compose into −17.99 on every second QB; **DL −32.87 / DB −28.28 on an EMPTY roster**; 246 of 796 priced rows have TAV < UV against "structurally impossible" | CORROBORATED (measured) | **NEW** |
| **W2-07** | **Thirteen test modules, including `test_cdme_certification`, run on the fixture the repo declares non-production** — its own docstring says "never a synthetic fixture" | CORROBORATED | **NEW** |
| **W2-08** | `CDME_CONTRACTS.md` §1–§3, banner-marked the live authority, false in four places (domain −9.12..97.90 vs measured −319..+220; "never None" vs None on 60% of rows) | CORROBORATED | **NEW** |
| **W2-09** | `round` is the round of the last pick MADE, not the pick being decided; the test pins the off-by-one | UNVERIFIED | **NEW** |
| W2-10 | `remaining_starter_demand` treats `roster_id=None` as a phantom 13th team and raises on the whole board | UNVERIFIED | **NEW** |

### Convergence across all four passes

| finding | A | B | C | D |
|---|---|---|---|---|
| `time_horizon_adj` population mismatch (W1-02) | ✓ | ✓ | ✓ | ✓ |
| survival leaks through `pick_necessity` (W1-07) | ✓ | ✓ | ✓ | ✓ |
| anchor cache key incomplete (W1-03) | ✓ | ✓ | ✓ | — |
| two take models (W1-10) | ✓ | — | ✓ | ✓ |
| `prose_names` shield (W1-05) | ✓ | ✓ | ✓ | — |
| `need_bonus` test is a tautology (W1-04) | — | ✓ | — | ✓ (mutant survived) |

**Four independent passes, four hits on the same two defects.** Those are not opinions any more.

### What Wave 2 changes about the diagnosis

**Cluster 2 grew teeth.** W2-07 is the explanation the first wave was missing: thirteen modules
including the *certification battery* run on a universe with no IDP rows, no unpriced rows, and
`proj_3yr` on every priced row. That is precisely the universe in which W1-02, W2-06 and D-2
**cannot be observed**. The suite is not failing to catch these; it is structurally incapable of
seeing them.

**A new cluster: invariants pinned on the shape where they cannot fail.** W1-01
(`superflex=False`, no IDP slot), W2-06 (`test_an_empty_roster...` on a roster with a dedicated
TE slot and no `slot_alternatives`), W1-04 (algebraically trivial), W2-09 (the test asserts the
off-by-one). Four separate invariants, four pins that cannot fail. That is a *pattern*, not four
accidents, and it is the strongest argument in this ledger against repairing findings one at a
time.

## Stopping condition — status

**Wave 2: NOT clean.** Eight new, several measured on the owner's own league. The counter resets.

Three consecutive waves producing **no NEW finding that survives verification** — not three waves
producing no findings, which a pass could satisfy by re-reporting known items. **Current streak:
0.**
