# v4 FREEZE RECORD — what it rests on, what it does not claim, and what stays open

> **EVERY GATE IS GREEN ON THE ENGINE THIS RECORD DESCRIBES.** The blind pass is dispositioned,
> both batteries ran to their full matrices, the suite is green at 4,152 tests, four independent
> reviews were run AFTER all of that and their findings are repaired or stated below, and the
> mutation gate passes — re-run on `7e54821` rather than inherited from `7984b1d`, because twelve
> repairs landed in between and a verdict about superseded source is evidence about nothing.
>
> `v2`'s record was written once as a freeze, reversed, and rewritten as a candidate because a
> battery had not run. The ordering that episode established — a finding sends work back BEFORE
> the tag, never after — is why this file was a candidate for the last three hours and is not one
> now. **The tag is the owner's to push.**

`POST_AUDIT_PLAN.md` remains the numbered record and wins over any status flag anywhere (`#292`).
Written to be read cold.

---

## 1. What the freeze covers

The v4 cycle ran the gate defined in `V4_GATE_CRITERIA.md` against `v3-freeze` (`eac7491`):
five blind adversarial lenses, worktree-isolated, unbriefed, none able to see another's findings.

* **26 findings** from the blind pass, of which five were convergences found independently by
  lenses that could not see each other — **plus 32 more from four independent reviews run after
  every gate was already green**, of which twelve were repaired and the rest are stated in §5.
* **4,152 tests OK** at `7e54821`. The suite has grown by 76 tests this cycle, every one of them
  written because something was found to be undefended.
* **Every finding dispositioned** under §5 of the gate criteria — recorded in
  `evidence/blind_pass_v4/TRIAGE_V4.md`.
* **Nine blocking findings repaired**, plus one owner-ruled feature (D10).
* **Two owner decisions closed** — D9 and D10.

### The count I got wrong, recorded because the record wins

I opened the triage saying 21 findings remained. It was **25**: I had subtracted five repaired
ITEMS from 26 FINDINGS, and four of those items were convergences carrying two or three IDs each.
Enumerated mechanically: 34 distinct IDs, 9 belonging to the five repaired items, 25 remaining.

---

## 2. The nine blocking repairs

| finding | what was wrong | verification |
|---|---|---|
| `D-F1` | `assertion_execution` had never reached a verdict — `store_io.read` called with one argument where it has always required two | born broken; unnoticed for its whole life |
| `A-F2`/`B-F1` | an injury designation UNPRICED a trade-value-priced row (regression introduced by D8) | the absent-projection branch returned NaN; now 0.0 |
| `C-F1`/`E-F1` | the chair was told a health discount applied when none was | `pick_debate` now branches three ways on `risk_adj`, not two on the basis |
| `B-F2`/`A-F3`/`E-F4` | "a ceiling" was the label on a 0.0 | label now describes the number it is attached to |
| `E-F2` | an absent number displayed as "withheld" | `presentable_text` checks absence first |
| `D-F4` | `assertion_floors`' per-method floor keyed on the bare method name, so two classes sharing a test name collided | five such names exist; every key now `Class.method` |
| `D-F5` | the capture-path guard skipped any module mentioning `CAPTURE_PATH`, and the one real offender was such a module | guard now names it; its literal is `rdb.CAPTURE_PATH` |
| `D-F2` | `prose_names`' history shield was block-scoped, exempting 45% of the corpus and 75% of module docstrings | paragraph-scoped; four real dead names found and fixed |
| `D-F3` | the test measuring that shield read raw source, so 18 of 19 comparisons were values compared to themselves | reads the prose corpus; 2 real comparisons, and a guard that the comparison is reached at all |
| `E-F5` | a failed season fetch priced the board from the vendor with NO warning | all four branches exercised; pre-sync stays silent |
| `D-F6` | a magnitude test recomputed its own definition — IR 4→8 passed | literals pinned; MUTATION-CHECKED, fails under IR 4→8 |
| `A-F1` | D8's "the two paths agree exactly" holds only at `gp == SEASON_GAMES` | claim scoped in three places; no engine change — see §5 |
| `B-F4` | `feasibility_first` read eligibility for the roster and the primary bucket for the candidate | DL/LB dual now promoted for an LB hole; DL-only still is not |
| `C-F3` | eligibility never crossed the snapshot boundary, so the LB view hid 8 eligible candidates | `eligible_positions` travels; stored boards replay on their primary bucket |

**Three of these were defects in my own work from this same session** (`D-F6`'s tautology, and
the `prose_names` and `assertion_floors` instruments I had certified as sound). One more, D10,
shipped a bug that its own test then caught — see §4.

---

## 3. The dominant defect class: one question, two readers

Almost nothing repaired here was an arithmetic error. Full write-up:
`evidence/semantic_duplication/ONE_QUESTION_TWO_READERS.md`. Five instances in one cycle
(`team_count`'s four spellings, a rosterless pick meaning two things, `feasibility_first`'s two
sides, eligibility at the snapshot boundary, and D10's starting-slot count), and an inverse pair
that must NOT be deduplicated (`availability_factor`'s mixed denominators, `depth_exposure`'s two
bases) because they answer different questions on different scales.

The transferable rule: **an expectation derived from the authority catches a disagreement between
readers; a literal expectation cannot.**

---

## 4. Owner rulings

### D10 — price it, and scale the warning to the consequence

Ruled by the owner. The refusal machinery `league_config` described (`admits_decision`,
`decision_config`) has no production caller. **The module STILL claims one** — the docstring reads
"ambiguity is enforced", and nothing enforces it because nothing calls it. That is `C-F4`, open and
deferred as non-blocking; a D10 commit message claimed it had been corrected and that claim was
false. The board is always priced regardless, which is what D10 ruled. Three bands, which are what
the engine can DETERMINE rather than a severity scale — no threshold appears anywhere (`#56`):
normalises to a non-playing slot → consequence exactly zero → asterisk; normalises to a starting
slot → names the slot lost and counts what remains → loud; normalises to nothing → may start a
player, error unbounded → loud, and says the bound is what is missing.

Normalisation is typography only. `RES`, `PS`, `OUT`, `SUSP` stay in the loud band and a test
keeps them there: they probably do mean non-playing slots elsewhere, and this app has not measured
that.

**D10 shipped a bug and its own test found it.** `parsed_starting` used `starting_slots()`, which
counts any label not in `NON_STARTING_SLOTS` — so it counted the unrecognised label itself and
every message claimed one more starting slot than the solver had parsed. Fixed by composing two
existing readers. The test now asks `slots_from_roster_positions` for the number; a literal would
have passed, because the fixture and the bug agreed.

### D9 / `#50` — the replacement equation

Ruled (1), and (1) was already the engine's behaviour. Full record:
`evidence/d9_replacement_equation/D9_RULING.md`. The owner challenged the framing twice and was
right both times; I gave two wrong answers before the measurement settled it, and all three of my
errors had one shape — reasoning about a term from its own prose instead of its output.

`#21` and `D7(a)` are unblocked by this. Both remain out of scope per §8.

---

## 5. What this freeze does NOT claim

* **The mutation gate PASSED at `7984b1d`, and the repairs postdate that verdict.** This was
  the larger of the two things an earlier draft of this record did not claim, and it is now a
  claim: baseline green in 1,718.8s over 229 scored modules, five of five mutations caught, tree
  restored clean with `sources_dirty_after` empty and `draft_room.py` identical to HEAD.

  **What makes it mean something.** Two of the five arms had read `MUTATION IS INERT` for their
  entire existence — they mutate the upside branch while the fixture only ever built a balanced
  board, so no mutation of theirs could change anything. The fixture now builds both, and the
  proof is not the censuses but the DIGESTS: `217c138c6b0e5d37` balanced against
  `427c40010c69c32c` upside. Both arms cleared a preflight that requires the mutant to build a
  board AND to differ from the reference, and both were then caught. A binding census alone would
  not have shown this — the two censuses are identical on both branches by construction, because
  neither backstop reads the mode.

  **IT CERTIFIES AN ENGINE THAT HAS SINCE CHANGED.** Twelve repairs landed after that run. A
  verdict about code that no longer exists is not evidence about this freeze, which is why the
  gate was re-run on the repaired engine before the tag. **IT PASSES AT `7e54821`**: anchors
  precondition green in 54.0s, baseline green in 1,351.0s, and all five arms caught in 437.4s,
  440.6s, 440.5s, 438.9s and 443.7s. `sources restored cleanly: yes`, `sources_dirty_after`
  empty. Both upside arms — the two that were inert for their whole prior existence — cleared a
  preflight whose two branch digests differ (`9f5cc3af014e8e9a` balanced, `427c40010c69c32c`
  upside) and were then caught.

  **AND THAT VERDICT WAS SUPERSEDED IN TURN.** The production-hardening pass changed the engine
  again, so `7e54821` became another verdict about code that no longer exists. The gate was re-run
  a third time, on the tree this record freezes: anchors precondition green in 61.4s, **baseline
  green in 1,573.9s**, and all five arms caught in 509.4s, 496.5s, 488.0s, 494.2s and 500.5s.
  `sources restored cleanly: yes`. The fixture binds on 619 of 964 rows (feasibility) and 131
  (fieldability), and the two branch digests still differ, so neither upside arm could read inert.

  **THREE FURTHER ARMS COVER WHAT THIS HARNESS STRUCTURALLY CANNOT.** The hardening pass changed
  behaviour in three places, and none of them is a board invariant, so all three would have read
  `MUTATION IS INERT` here — see the explanation at the end of this section. They are scored by
  `evidence/mutation_gate/behaviour_arms.py` and all three are caught. **The tree therefore stands
  at 8 of 8 mutation arms caught, 0 survived, 0 inconclusive.**
* **`A-F1`'s two paths still diverge below a full slate**, by design, up to 2.25 points measured.
  What is pinned is the direction and the bound.
* **`depth_exposure` does not price contingency for a demand-exhausted position** — 0 of 703 such
  rows across rounds 12–20 carry a positive value, and that is correct: the uncharged quantity is
  the starter's whole value, already in `universal_value`.
* **Performance** — no stated requirement exists, and the 5.4x regression this record almost
  carried does not exist either: measured serially, v4 is **1.0062x** v3 with identical call
  counts. What IS real and deliberately unfixed: **25.9% of a pick is accidental repeated work**
  (fingerprint memo ~20.7%, pool memo ~7%). A speed change during a freeze is the thing this
  process exists to prevent, so it is recorded and left.

### Instrument defects found by the independent reviews — repaired

Every item the reviews raised against the instruments is closed in code, not stated. The owner's
instruction was that this build be as close to production as it can be, so "latent, nothing says
anything untrue today" stopped being a sufficient disposition.

* **`assertion_execution --check` could not tell 359 measurements from zero** — proved by making
  `pandas` unimportable, which errors every test, which empties the silent list, which read as a
  clean pass. Now: errored tests are reported before the comparison (the module docstring always
  promised "the error is the finding"); `--write` records the swept population and `--check` fails
  a full sweep that runs fewer tests than the record was written over; the success line prints the
  RECORD's size where it printed this run's hit count under the word "known"; the damaged-record
  path reads through `store_io.read_state`, because `read` is fail-soft and the `try/except` that
  stood there could not fire; and `--write` refuses a partial sweep, which would have written a
  smaller record and called it a correction.
* **`prose_names.misquoted_constants` was shielded at BLOCK scope** where its neighbour had moved
  to paragraph scope, so one history marker anywhere in a long docstring exempted every quotation
  in it. Now paragraph-scoped, and the walk has ONE home that `misquoted_constants`, the census and
  the mutation test's oracle all read — the oracle re-derived it, disagreed by four quotations, and
  reported the repair as a regression. Measured: 58 quotations compared where 54 were, none wrong.
* **The eligibility repair had no test of its own, and that was found by asking what the mutation
  gate could catch.** The composed rule was verified by hand against the real row and by reading the
  three call sites; neither is a test, and neither runs again. Eleven tests now cover it — seven on
  the producer side (`test_one_eligibility_reader`) and four on the consumer side
  (`test_one_eligibility_vocabulary_everywhere`), including the pair that IS the repair: an absent
  field replays on its label, an empty answer appears in no view. The gap existed because the
  repair's three former call sites had each re-expressed the rule and each got it wrong the same
  way, which is the kind of agreement an untested rule produces.
* **Two `invariant_registry` enumerators counted only the CONFORMING function**, so a
  reimplementation moved no census — against population texts that say "call sites of the take
  model" and "sites that resolve a player onto a vendor record". Both now count what their own text
  claims, with the two kinds prefixed so they cannot be read as one number: the take model reports
  its raw-shape consumers and flags any unnormalised call, and the vendor census reports the direct
  `merge_player` resolutions with a verdict on each.
* **`test_ui_source`'s guard exempted 52 of 230 modules whole** — any module naming `ui_source`
  anywhere, which is the construct `D-F5` removed from its twin. The escape is gone. It could not
  simply be deleted, because three modules carry `"app.py"` as a label or a dispatch key and read
  through `ui_source` correctly, so the rule now asks what the literal is USED FOR: an operand of
  `/`, or an argument to a path builder. The rule also had two spellings claiming to be one.
* **`constant_axes` was blind to the configured half of the matrix** (A3). The definition said to
  be missing — which provenance keys are axes — was not needed: the two populations are reported
  separately, so no key has to be called an axis for both numbers to be true. Configured constants
  are DISCLOSED, not gated, because one `seed` across every arm is the point of a reproducible run,
  while a constant league axis is a coverage hole. The 53-arm run published `constant_axes: []` and
  said nothing about `upside_rule=round` on all 53 arms; it now says it.
* **The VDS report's `seed`, `top_k_swept`, `strategies` and `formats` described the code at report
  time** (A6). They keep those names — they are this code's tables, which is what comparing two runs
  needs — and `ARM_CONFIGURATION` now reads each arm's own `provenance`, naming the arms whose
  recorded config disagrees with today's tables. That named list is the payload, and a resumed run
  is where it matters. Measured on the committed 36-arm run: 36 of 36 arms carry `provenance`, 0
  disagree, 24 ran with no opponent noise and the 12 noisy ones split 6/6 across `top_k`. The review
  reported "0 of 36" — true of an earlier VDS report, not of the one this freeze rests on, and
  corrected rather than repeated.
* **`picks_by_mode` was recorded on every arm and read by nothing** (A2), while half the `auto`
  arms — the shipped default — never entered the upside branch. The report now carries
  `valuation_mix`, and it separates "never fired" from "could not fire": an arm whose upside rule
  triggers after the last round it drafts is named as UNREACHABLE, derived from the arm's own
  recorded trigger against its own round count. Arms whose split is unknown under the crossing rule
  are their own bucket, not zero upside.
* **`invariant_confirmation` printed the UPSIDE digest under the label "reference board"** — loop
  variables leaking from the branch loop. Repaired. It was deliberately left alone last cycle
  because fixing it would edit the harness that had just certified the tree; the gate is being
  re-run against these repairs, so that reason has expired.

### Repairs from earlier this cycle, now finished

* **`B-F6`** — the two readers agreed a rosterless pick is `None` and disagreed on TYPE.
  `team_count`'s picks rule now coerces `roster_id` the way its own seats rule four lines up and
  `team_slots_filled` always did, so `0` and `"0"` are one team rather than two. Its agreement test
  asserted `len(census) == count`, which is not a property of the two functions — the census also
  skips a pick whose player the pool cannot resolve — so it has been replaced by tests that ask the
  question, plus the control that measures why general equality is the wrong assertion.
* **`B-F4`/`C-F3`** — the composed rule "eligibility, with the primary bucket as a fallback" was
  spelled at three sites, all three added by that repair, and all three fell back on an EMPTY SET
  where `player_eligible_positions` is explicit that empty is an ANSWER: Sleeper saying this man
  starts nowhere. One home now owns it (`player_universe.eligible_positions_for`), falling back on
  the RECORD's absence and never on the answer's emptiness. The snapshot field's default moved from
  `frozenset()` to `None` for the same reason — an empty default was indistinguishable from the
  producer's empty answer, which is what forced the view filter to resurrect the raw `position` for
  both. Population on the committed capture: one row of 6,595, filtered out before any board is
  built, so this was latent; the next capture is not this one.

### Decisions recorded in the course of these repairs

Each is written down at the point of use, and each is the owner's to overturn.

* **The roster depth chart stays on the primary bucket.** Widening the vendor census surfaced seven
  direct `merge_player` sites. Six need no change (two are the merger's own internals, two are free
  text with no position to widen across, two are single-position Sleeper rows). The seventh,
  `app.py`'s `positional_depth`, prices a two-way player at his first-listed position only where
  the board prices him across all of them. Left as it is because of what the cell ASKS: it means
  "the value of this team's DB room", and pricing it from a man's wide receiver row answers a
  different question. Blast radius if the other reading is preferred: one player on the committed
  capture (Travis Hunter), one display cell with no number in it, nothing untrue.
* **Configured constants are disclosed, not gated** — above, under `constant_axes`.
* **The 25.9% per-pick cost stays stated, not optimised.** The owner's call: no performance
  requirement exists, and a speed change during a freeze is what the process exists to prevent.

### Why the behaviour-changing repairs got their own three arms

The v4 gate (`invariant_confirmation`) decides whether a mutation is INERT by comparing a BOARD
fingerprint, and its own docstring says that is deliberate: comparing whole boards needs no
per-mutation knowledge, so a later arm inherits the guard. That is right for board invariants and
cannot judge the three repairs of this pass that change behaviour — the `team_count` coercion is
unreachable whenever `total_rosters` is present, which every board fixture has; the eligibility row
is filtered out of the pool before any board is built; and the snapshot default touches no board at
all. All three would have read `MUTATION IS INERT`, which is in that harness's `INCONCLUSIVE` set,
so the gate would have exited 2 — passing nothing while looking rigorous.

So they are scored by a separate three-arm check, each arm carrying its own witness. That is the
bespoke cost `#126` warns about and it is unavoidable here: a non-board invariant cannot be
witnessed by a board. Each arm proves three things in order, and needs all three to mean anything —
the anchor applied at exactly one site, the mutated code answers the governed question differently
(without which a `caught` verdict can come from a mutation that changed nothing, `#245`), and the
named test module fails. Scope stated rather than implied: each arm runs the DESIGNATED module, not
the full suite, so the claim is "a named test defends this repair", not "no other test depends on
it". The full suite is run separately against the same tree, and the five-arm board gate re-runs on
the frozen commit because a gate must describe the code being frozen.

## 6. Out of scope, named rather than argued later

`D9(d)` (depth priced against a healthy starter's expected absence — needs an injury base rate
this app does not have), `#21`, `D7(a)`, `D1(b)`, `D2(c)`, `D4(b)`, `D8(a)`, the 16 board
inversions, every chosen magnitude (`#56`), performance, and vendor/season data changes.

Findings recorded as valid-but-out-of-scope: `A-F6`, `B-F3`, `E-F6` — see the triage for each
one's reasoning.

---

## 7. The evidence this freeze rests on

| gate | result |
|---|---|
| blind pass, five lenses | 26 findings, all 34 IDs dispositioned |
| full suite | **4,155 tests OK** at `5ed19aa` (2 skipped, 1 expected failure, 1,645.8s) |
| 53-arm format battery | **complete** — 9,336 picks, 2 findings, both `unfieldable_depth` on IDP groups |
| 36-arm VDS battery | **complete, the full matrix for the first time** — 6,264 picks, 11.0h of summed arm compute |
| board mutation gate | **PASSED on the frozen tree** — baseline green 1,573.9s, **5 of 5 arms caught**, sources restored cleanly |
| behaviour mutation arms | **PASSED** — **3 of 3 caught**, 0 survived, 0 inconclusive, every witness verified on the clean tree first |
| four independent reviews | delivered, merged with history, every branch fetched |
| every §5 item | **closed in code**, not stated — see section 5 |

The two mutation rows are one claim in two halves and both halves are needed: 5 arms over the
board invariants, 3 over the behaviour this pass changed, **8 of 8 caught**. The suite row is the
run that licensed the push of the repairs; the board gate's own baseline is a second full run, on
the later tree that added the tests, and it was green too.

### The VDS, read the only way it can be read

**The engine's own ledger is three findings.** All `unfieldable_depth`, all on `HEAVY_IDP`, under
`crossing`, `sharp_auto` and `sharp_balanced`. `sharp_upside` is clean, so this is a strategy
signal and not purely a format property. **Zero offence findings. Zero unfilled starting slots.
Zero unpriced picks on any arm that uses the engine.**

The other 32 of the 35 sit in arms where NO SEAT uses the engine (`noisy_k8`; `noisy_k3` produced
nothing). Every `unfilled_starting_slots` and every `unpriced_picks` case in the entire run is
there. Uncorrected, the report credited all 32 to `noisy_k8` as a strategy property — see V4-I1.

### The mutation gate, and why its verdict means something

| # | invariant | branch | verdict | runtime |
|---|---|---|---|---|
| 0 | baseline, clean tree | — | **green** | 1718.8s |
| 1 | `feasibility_first never binds` | both | **caught** | 557.8s |
| 2 | `board order ignores feasibility` | balanced | **caught** | 579.6s |
| 3 | `board order ignores fieldability` | balanced | **caught** | 571.7s |
| 4 | `upside board order ignores feasibility` | upside | **caught** | 557.1s |
| 5 | `upside board order ignores fieldability` | upside | **caught** | 563.8s |

The baseline is what makes the five verdicts mean anything: a "caught" is only `rc != 0` with a
mutant present, which says nothing unless the identical run is green without it. Arms 4 and 5 are
the two that read `MUTATION IS INERT` for their entire prior existence, because the fixture built
one board and they mutated the branch it never built. Both cleared preflight — the mutant builds a
board AND differs from the reference — before either suite ran.

**THAT VERDICT WAS ABOUT `7984b1d`, AND THE REPAIRS BELOW POSTDATE IT — SO IT WAS RE-RUN.**
The gate passes again on `7e54821`, the tree this record describes: baseline green 1,351.0s,
five of five caught, tree restored clean. The re-run also reproduced run 1's preflight
bit-identically before starting, and aborted its own first attempt on a red baseline it had
caused itself rather than report a verdict over it.

### On the VDS specifically

The prior VDS gate was satisfied on a PARTIAL run — `POST_AUDIT_PLAN.md:14644` records `#29`
stopped at 13 of 36, the committed report holds 3 arms, and the interim record covers 7. It was
ruled sufficient because the formats that mattered had finished. This cycle runs all 36. Whatever
it returns is new evidence and not a confirmation of an earlier number; no figure from the prior
run is quoted here.

---

## 7a. The twelve findings repaired after the reviews

Every one reproduced in this tree before any code moved. Both reviewers graded their own findings
and said in writing not to treat those grades as verdicts, so these were re-triaged here against
one question: **does it make the app, or a committed artifact, say something untrue?**

| | what was untrue | now |
|---|---|---|
| `R3`/`R18` | the chair was told "this engine does not price this designation" about rows discounted 23.5% | `health_basis` travels beside `health_penalty`; four causes, four sentences |
| `R1` | an unreachable Sleeper silently vendor-priced the board | the guard asks `season_sum_is_complete`, not for an `error` key the soft-fail path never writes |
| `A1` | `independent_formats: 53` in committed evidence | **52**, regenerated from the shards; `duplicate_arms` recovers its only live finding |
| `I1` | the figure census fired on compliance and was silent on the violation | counts the bypass route too; 8 -> 9, with a live offender named |
| `R2` | D10 told a manager the league declares 10 starting slots where it declares 12 | asked of `starting_slots` over the raw list |
| `A5` | "No inert arms: every strategy changed the draft in every format", said from missing evidence | formats with no control are named UNDETERMINED |
| `R12` | the wide `A-F1` claim survived in an owner-facing document | scoped to a full slate, divergence stated and bounded |
| `R5` | a restraint claim citing "four rather than nought" where the report says zero | cites the three names that are the real evidence |
| `I2` | "0 misquoted over 18,347 blocks" -- a denominator two orders of magnitude off what was checked | prints the checkable population: 153 quotations, 54 compared |
| `R14` | "four quantities, one pair per branch" where two are identical by construction | states the redundancy; prints the digests, which are what the second board buys |
| `R17` | my own write-up claiming all five instances repaired | three are; the other two are named with what still disagrees |
| `R19(a)` | the eligibility producer was a closure nothing could test | hoisted as `snapshot_eligibility`; four tests, one per undefended repair |
| `V4-I2` | **new** -- evidence transcripts vouched for the dead names they reported | fenced code from `evidence/` is a transcript, not a definition |

### Three of my own errors, caught by instruments rather than by me

Recorded because the clean final commit was not inevitable:

* I imported `draft_room` into `pick_debate`, crossing a boundary the repo enforces precisely so
  a formatter cannot re-price a candidate. The repo's own answer sat two lines below the test that
  caught it: `pick_synthesis` re-exports the constants as the same objects.
* I invented a dead name, promising a test in a docstring under a name I had not used -- in the
  commit repairing `prose_names`.
* I wrote a test asserting the literal key value appears in `app.py`. It would have passed **only
  on the defect** it was written to catch; the true assertion is the inverse.

The first repair batch also produced nine suite failures, every one a real consequence of the
repairs rather than an artifact. Two censuses were signed for by hand rather than absorbed by a
`--write`, because this registry's whole subject is populations moving without anyone noticing.

---

## 7b. The four independent reviews, and what they cost to buy

After every gate was green, four sessions in separate containers attacked this candidate: the
mutation gate end to end, an adversarial review of the nine repairs, an adversarial review of the
Tier 0 instruments, and a measurement of the 5.4x cost figure. Roughly $125 and about three hours.

**They were worth it, and the reason is independence rather than parallelism.** Two of the four
could not have run here at all — the mutation harness mutates `draft_room.py` on disk and the VDS
was in flight; profiling under contention measures the contention. The other two could have run
sequentially in this container. What made those two valuable is that they attacked work this
session had already pronounced clean: nine self-certified repairs, and six instruments reported
green four hours earlier.

**Four things would have entered this freeze without them:**

* the chair told "this engine does not price this designation" about rows discounted 23.5%
* `independent_formats: 53` in committed evidence where the answer is 52
* a silently vendor-priced board whenever Sleeper is unreachable
* **a 5.4x performance regression that does not exist**

The last is the one to dwell on, because it was mine and it was confident. 6.03 s/pick was six
shard processes' wall clocks summed; the v3 figure of 1.12 came from a report whose `seconds` was
truncated by a resume covering 2 of 53 arms, and cannot be re-derived at all because that JSON is
gitignored. Measured serially, both arms alone on the box, same arm: **v4/v3 = 1.0062x**, with
identical call counts function for function. The standing attribution named `depth_exposure` and
MANDATE 2.6 — two features that are IDENTICAL on both sides of the comparison and appear nowhere
in the diff. `depth_exposure` is 0.05% of a warm board. The real finding is that **25.9% of a pick
is accidental repeated work** (fingerprint memo ~20.7%, pool memo ~7%), which is recorded here and
deliberately not fixed during a freeze.

**Both reviewers graded their own findings and both said so in writing** — "treat my HIGH/MEDIUM/
LOW as a reading order, not as a verdict on what blocks the freeze". Every finding below was
re-triaged here against one question: does it make the app, or a committed artifact, say something
untrue? And nothing was repaired on report alone; each was reproduced in this tree first.

**The best finding of the cycle cost nothing.** V4-I1 — 91% of the VDS findings misattributed —
came out of an ordinary cleanliness audit in this container, not from spawning anything.

---

## 8. Freeze condition

v4 is complete only when all of: the blind pass is complete across every lens; every finding has
a recorded disposition; every confirmed in-scope defect is repaired; the full suite passes; the
format battery passes; the VDS battery passes over its full matrix; and the owner pushes the tag.

**THREE CONDITIONS WERE ADDED AFTER THE GATE WAS ALREADY GREEN, and they are the reason this
record is worth more than the one it would have been.** Every original condition above was
satisfied before the independent reviews ran. Had the tag been cut then, it would have carried a
false sentence to the chair, a wrong number in committed evidence, a silently vendor-priced board,
and a performance regression that does not exist.

So, also required:

* **the mutation gate passes on the engine BEING FROZEN**, not on an earlier one. It passed at
  `7984b1d`; twelve repairs postdate that, so it is re-run. A gate that certifies superseded code
  is a gate about nothing.
* **every finding from an independent review is dispositioned** — repaired, or stated in section 5
  with its measured consequence. Not silently carried.
* **no finding is accepted on report alone.** Each was reproduced here first. Three of this
  cycle's wrong turns came from accepting a plausible claim, and one review's own illustrative
  arm list turned out to describe a different dataset than this freeze's — both correct, neither
  reconcilable, and only reproduction tells them apart.

**What is NOT a condition:** that nothing remains open. Section 5 lists what this freeze does not
claim, and that list is longer than v3's because more was looked at, not because less was fixed. A
freeze that honestly names its limits is worth more than one that quietly guarantees everything.

**The tag is the owner's to push.** Cut locally, published by him, as at `v2` and `v3`.
