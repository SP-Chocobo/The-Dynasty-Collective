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

## What this ledger does NOT yet contain

Wave 2 is running. Its findings will be added with the same verdict vocabulary before anything is
repaired. The stopping condition is **three consecutive waves producing no NEW finding that
survives verification** — not three waves producing no findings, which a pass could satisfy by
re-reporting known items.
