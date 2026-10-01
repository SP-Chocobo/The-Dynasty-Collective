# v4 mutation gate — the run on the tree that is frozen

**Status: PASSES. 8 of 8 arms caught, 0 survived, 0 inconclusive.**

Two harnesses, because one of them structurally cannot judge the other's arms. Both verdicts are
needed and neither substitutes for the other.

- **Commit under test:** `740482f` (board arms); the behaviour arms were scored on the same tree
- **Branch:** `claude/fantasy-football-control-center-ff6qlu`
- **Raw logs:** `v4_frozen_tree_raw.log`, `V4_BEHAVIOUR_ARMS_raw.log`

## Why this run exists at all

The gate had already passed twice — at `7984b1d`, then at `7e54821` on the repaired engine. The
production-hardening pass changed the engine again, which made `7e54821` a verdict about code that
no longer exists. That is the same reason the second run existed, and it applies a third time: a
gate must describe the code being frozen.

## Half one — the five board arms (`invariant_confirmation.py`)

| # | arm | verdict | sites | runtime |
|---|---|---|---|---|
| — | anchors module on the clean tree (precondition) | **green** | — | 61.4s |
| 0 | *baseline — no mutation, clean tree* | **green** | — | **1573.9s** |
| 1 | `feasibility_first never binds` | **caught** | 2 | 509.4s |
| 2 | `board order ignores feasibility` | **caught** | 1 | 496.5s |
| 3 | `board order ignores fieldability` | **caught** | 1 | 488.0s |
| 4 | `upside board order ignores feasibility` | **caught** | 1 | 494.2s |
| 5 | `upside board order ignores fieldability` | **caught** | 1 | 500.5s |

`sources restored cleanly: yes`. No arm read `ANCHOR FAILED`, `MUTANT DOES NOT PARSE`,
`MUTANT CANNOT BUILD A BOARD`, `MUTATION IS INERT` or `*** SURVIVED ***`.

**The fixture binds**, which is what makes a `caught` verdict mean anything: feasibility on 619 of
964 rows, fieldability on 131, and the two branch digests differ (`9f5cc3af014e8e9a` balanced,
`427c40010c69c32c` upside) so neither upside arm could read inert.

**One incidental confirmation.** The summary line prints
`reference board (balanced): 9f5cc3af...`, which is the FIRST branch digest. Before this pass
closed the leaked loop variables it would have printed the upside branch's `427c4001` under that
label — so the repair is observable in this run's own output, not merely asserted.

## Half two — the three behaviour arms (`behaviour_arms.py`)

The hardening pass changed behaviour in exactly three places. **None of them is a board
invariant**, and `invariant_confirmation` decides whether a mutation is inert by comparing a BOARD
fingerprint — deliberately, since that needs no per-mutation knowledge and a later arm inherits
the guard. That design is right for board invariants and cannot judge these three:

* the `team_count` coercion is unreachable whenever `total_rosters` is present, which every board
  fixture has, so no board moves;
* the eligibility row the empty-answer repair governs is filtered out of the pool before any board
  is built (0 of 6,594);
* the snapshot default sits on the debate boundary and touches no board at all.

All three would have read `MUTATION IS INERT`, which is in that harness's `INCONCLUSIVE` set, so
the gate would have exited 2 — **passing nothing while looking rigorous**. Bending that harness to
admit them would have cost it the property that makes it trustworthy, so they are scored
separately, each arm carrying its own witness. That is the bespoke cost `#126` warns about, and it
is unavoidable here: a non-board invariant cannot be witnessed by a board.

| # | arm | witness on clean tree | witness under mutation | caught by | verdict |
|---|---|---|---|---|---|
| 6 | `team_count`'s picks rule stops coercing `roster_id` | REPAIRED | DEFECTIVE | `test_one_league_one_team_count` | **caught** |
| 7 | the composed eligibility rule falls back on the empty ANSWER again | REPAIRED | DEFECTIVE | `test_one_eligibility_reader` | **caught** |
| 8 | the snapshot's eligibility default goes back to an empty set | REPAIRED | DEFECTIVE | `test_one_eligibility_vocabulary_everywhere` | **caught** |

Each arm proves three things in order and needs all three. The anchor applied at exactly one site.
The witness read `DEFECTIVE`, so the mutated code answers the governed question differently —
without which a `caught` verdict can come from a mutation that changed nothing (`#245`), which is
how this project's first gate produced two useless verdicts. And the named module failed.

**A precondition pass requires every witness to read `REPAIRED` on the clean tree before any
mutation is applied**, so a `caught` verdict cannot come from a witness that is simply wrong. All
three did.

### Scope, stated rather than implied

Each behaviour arm runs the **designated module**, not the full suite. The claim is therefore
"a named test defends this repair", **not** "no other test depends on it". The full suite was run
separately against the same tree and the board gate's own baseline is a second full run.

### What arm 8 incidentally established

Mutating the snapshot default back to `frozenset()` fails three tests, and one of them is the
**pre-existing** compatibility test — `test_a_stored_board_without_the_field_replays_on_its_primary_bucket`.
So the two halves of that repair are provably coupled: the `None` default is *required* by the view
filter's `is None` branch rather than being an independent stylistic choice. Before this run, the
only thing bounding that change was an enumeration of readers done by hand.

### The arm that would not have existed without asking this question

Arm 7 had **no test at all** when the repair shipped. It had been verified by hand against the real
row and by reading the three call sites it replaced, and neither of those is a test — a hand check
does not run again. Asking what the gate could catch is what surfaced it, and eleven tests now
cover the rule on both sides of the boundary.
