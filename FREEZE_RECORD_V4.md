# v4 FREEZE RECORD — what it rests on, what it does not claim, and what stays open

> **CANDIDATE, NOT A FREEZE. ONE GATE IS STILL RUNNING.** Both batteries are complete and the
> full suite is green at `7e54821`, but the mutation gate's passing verdict was measured at
> `7984b1d` and twelve repairs postdate it. It is being re-run on the engine this record is about;
> until that lands, the two `<<PENDING>>` markers are numbers this file must not carry.
>
> `v2`'s record was written once as a freeze, reversed, and rewritten as a candidate because a
> battery had not run. The ordering that episode established — a finding sends work back BEFORE
> the tag, never after — is inherited here rather than re-earned. **No tag is cut against this
> file while a `<<PENDING>>` remains in it.**

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
  gate is re-run on the repaired engine before the tag. `<<PENDING: the re-run's verdict table>>`
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

### Open instrument defects, each with its measured consequence

Found by the independent reviews, reproduced here, and NOT repaired — stated instead, because
none of them currently makes the app or an artifact say something untrue:

* **`assertion_execution --check` cannot tell 359 measurements from zero.** It returns the same
  green line either way. Its sibling `assertion_floors` closed this exact hole and documented it.
* **`invariant_registry` has three more enumerators with the inverted shape** found at I1
  (`_take_model_consumers`, `_vendor_record_resolutions`, and the figure census now repaired).
  Each counts call sites of the CONFORMING function, so a reimplementation moves no census.
  `_surfaces_consulting_the_withholding_policy` states that limit in its own docstring and is the
  model the others should follow.
* **`test_ui_source`'s app.py-read guard carries a module-wide escape** that `D-F5`'s repair
  removed from its twin — 52 of 230 modules exempted whole. Latent: no live offender today.
* **`prose_names` can still be fooled at block scope on four quotations**, all in probe and test
  files. The markdown corpus is clean at paragraph scope (75 of 75 shielded in their own
  paragraph). The summary line that invited a much larger claim is repaired.
* **`constant_axes` sees only league-derived axes** (A3) and **the VDS report's `seed`,
  `top_k_swept`, `strategies` and `formats` describe the code at report time, not the arms** (A6).
  Both scoped in prose at the point of use; neither is false about the committed runs.
* **`picks_by_mode` is recorded on every arm and read by nothing**, and half the `auto` arms never
  entered the upside branch at all (A2).

### Repairs this cycle that are still only partly done

* **`B-F6`** — the two readers agree a rosterless pick is `None`, and disagree on TYPE:
  `team_count`'s picks rule does not coerce `roster_id` while its seats rule and
  `team_slots_filled` both do, so `0` and `"0"` are two teams to one and one roster to the other.
* **`B-F4`/`C-F3`** — eligibility is now asked on both sides, and the composed rule is spelled at
  three sites, all three added by that repair. One of them is now hoisted and named
  (`snapshot_eligibility`); the other two still re-express it locally.

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
| full suite | **4,152 tests OK** at `7e54821` (2 skipped, 1 expected failure) |
| 53-arm format battery | **complete** — 9,336 picks, 2 findings, both `unfieldable_depth` on IDP groups |
| 36-arm VDS battery | **complete, the full matrix for the first time** — 6,264 picks, 11.0h of summed arm compute |
| mutation gate, end to end | **PASSED** — baseline green 1,718.8s, **5 of 5 arms caught**, tree restored clean |
| four independent reviews | delivered, merged with history, every branch fetched |

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

**THIS VERDICT IS ABOUT `7984b1d` AND THE REPAIRS BELOW POSTDATE IT.** `<<PENDING: re-run on the
repaired engine>>`

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
