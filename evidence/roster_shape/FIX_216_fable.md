# #216 — the fix: a fourth team-specific term, derived, and what it does and does not repair

Implementer: Fable. Base: `ui-authority-pass` @ 2f5f304. Pre-registration:
`PREREGISTRATION_216_fix.md` (written before any measurement of the fix). Instrument:
`run_216_fix_probe.py` (repo root); result sets in `fix_216/`. Battery: the adversary's three
files from b66c051, taken verbatim; the only edits to them are the ones the room-integrity file
itself instructs the implementer to make (the identity pin and its two "today" partners),
each marked in place.

## 1. What I chose

**`displacement_adj`** — the league replacement anchor's over-credit for a slot THIS roster
cannot offer a player:

    displacement_adj(position) = replacement_level(position) − displacement_level(position)  ≤ 0

`displacement_level` (lineup_optimizer) is what a player at that position must out-score to
start for this roster: every starting slot is pre-filled with a phantom worth the league
replacement level for that position, the roster is solved against the phantoms, then a probe at
the position with an overwhelming value is added and the lineup re-solved; the value the probe
evicts is the level. It equals the league level wherever a slot the position can reach is open
(or held below the league alternative), and equals my weakest reachable starter otherwise.
Chains through multi-eligible players are the optimizer's business, not a rule's.

    team_acquisition_value = universal_value + need_bonus + eligibility_bonus + depth_exposure
                             + displacement_adj

`universal_value` is untouched and stays team-agnostic. The term is per position at a board
state (one solve pair per position, not per row), non-positive by construction, unbounded by
construction (its magnitude IS the measured over-credit), and introduces **no constant**: its
inputs are the optimizer and the levels the board already computes. A multi-eligible candidate
is deducted by the LEAST of the deductions at the positions his full eligibility reaches, so an
open slot his flexibility unlocks is not taken away by this term while `eligibility_bonus`
pays for it.

Why this and not the options measured by the review:

| option | why not |
|---|---|
| RAW-MLV (#84 as built) | an accidental raw-points ruler (Purdy at r1); "an instructive control, not a fix" — agreed, not shipped |
| replacement-filled MLV as the sort key (`_LEX`) | a lexicographic key is not a number; the room would display one order and rank another (the display contract, and the C-class guard names exactly this failure) |
| replacement-filled MLV replacing bpa | makes `universal_value` roster-relative, and eight consumers read it as team-agnostic |
| scaling `need_bonus` | no derivation; the cap does not bind (1e9 identical, 6/6) |
| horizon-floor replacement for the QB half | ruled observable-only (#48); its own error is large here (predicted a 289.6 QB would remain; Penix 129.0 did) |
| rank N+1 ("the first player who starts nowhere") for the QB half | principled off-by-one, but it moves every level on the board by one rank for a gain of QB1−QB2 ≈ 11 points at the collapsed state; not worth the blast radius for this item — recorded below as the open half |

The displacement term is the replacement-filled marginal's DISPLACEMENT half, phrased as a
level rather than a marginal. Phrased that way it (a) reduces exactly to VOR where a slot is
open, so the board is byte-identical to today's wherever it was right; (b) stays a per-position
constant, so a difference of two rows' prices is still a difference of anchors; (c) is a
non-positive addend, so every cap-derived quantity in `pick_synthesis` keeps its upper bound.

## 2. Pre-registered gates, and the result against each

Six seats (1, 6, 12 × `12T_ppr`, `12T_ppr_SF`), real rulebook, shared pool of 481, one process,
one code version, four arms: BASE_ON (term off, backstop as shipped — the pre-fix engine),
BASE_OFF, FIX_ON, FIX_OFF. Every non-engine seat is `run_roster_proof.control_pick`.

| gate | result |
|---|---|
| G1 value board alone drafts a legal roster | **PASS 6/6.** FIX_OFF: missing dedicated {} and unfillable [] in every seat; FIX_ON: `fills_required_slot` True on **0** picks, pure-argmax overridden on **0** picks; FIX_ON composition == FIX_OFF composition in 6/6 |
| G2 the quarterback is priced, not forced | **PASS on `final_score`, with a caveat stated in §4.** 1QB: best remaining QB's final > 0 at every turn while my slot is open (4.0 = need_bonus; his bpa is still 0.00), ≤ 0 at every turn once filled (−11.2, −22.0, −39.1 at the first filled turn); taken at r8 unforced in 3/3 seats (SF: r6/r7 or r2/r6) |
| G3 lineup never worse | **PASS 6/6.** +309, +340, +325 (1QB), +123, +163, +165 (SF) lineup points over BASE_ON |
| G4 over-correction | **PASS.** Battery class E 6/6 unedited; no 1QB seat opens with a QB; second/third tight ends and third/fourth running backs still taken by value at open FLEX slots |
| G5 no new constant | **PASS.** AST-checked: no numeric literal in `displacement_adjustments` or `displacement_level` beyond the probe's named module constant and `round`'s digit count |
| G6 replay gate | **PASS.** BASE_ON reproduces the recorded #216 sequences pick-for-pick, 6/6 seats; at every state of every arm the instrument's pick is `compute_draft_board`'s first row after `_board_order` (0 order-gate failures in 24 drafts) |
| G7 the room | **PASS.** Identity closes with the fifth term on every priced row; the term and its basis reach `CandidateSnapshot`, `serialize_candidate`, the JS sentence, `DISPLAY_CONTRACT` and a fourth metric card; room-integrity battery executed in Chromium — see §6 |
| G8 suite | see §7 |

### 2.1 Compositions and lineup points, backstop OFF and ON

| format | seat | arm | composition | lineup pts | vs BASE_ON | control | forced | overrode | missing | QB rounds | replay |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 12T_ppr | 1 | BASE_ON | TE8 RB3 WR2 QB1 | 1987 | — | 2211 | 3 | 3 | – | [14] | MATCH |
| 12T_ppr | 1 | BASE_OFF | TE11 RB3 | 1528 | −459 | 2211 | 0 | 0 | WR2 QB1 | [] | |
| 12T_ppr | 1 | FIX_ON | WR7 TE3 RB2 QB2 | 2296 | +309 | 2234 | 0 | 0 | – | [8, 9] | |
| 12T_ppr | 1 | FIX_OFF | WR7 TE3 RB2 QB2 | 2296 | +309 | 2234 | 0 | 0 | – | [8, 9] | |
| 12T_ppr | 6 | BASE_ON | TE8 RB3 WR2 QB1 | 1899 | — | 2187 | 3 | 3 | – | [13] | MATCH |
| 12T_ppr | 6 | BASE_OFF | TE11 RB3 | 1465 | −434 | 2187 | 0 | 0 | WR2 QB1 | [] | |
| 12T_ppr | 6 | FIX_ON | WR8 TE3 RB2 QB1 | 2239 | +340 | 2187 | 0 | 0 | – | [8] | |
| 12T_ppr | 6 | FIX_OFF | WR8 TE3 RB2 QB1 | 2239 | +340 | 2187 | 0 | 0 | – | [8] | |
| 12T_ppr | 12 | BASE_ON | RB9 TE2 WR2 QB1 | 1884 | — | 2232 | 3 | 1 | – | [14] | MATCH |
| 12T_ppr | 12 | BASE_OFF | RB9 TE3 WR1 QB1 | 1704 | −180 | 2232 | 0 | 0 | WR1 | [14] | |
| 12T_ppr | 12 | FIX_ON | WR8 RB4 TE1 QB1 | 2209 | +325 | 2227 | 0 | 0 | – | [8] | |
| 12T_ppr | 12 | FIX_OFF | WR8 RB4 TE1 QB1 | 2209 | +325 | 2227 | 0 | 0 | – | [8] | |
| 12T_ppr_SF | 1 | BASE_ON | TE6 QB4 RB3 WR2 | 2469 | — | 2530 | 1 | 1 | – | [6, 7, 8, 9] | MATCH |
| 12T_ppr_SF | 1 | BASE_OFF | TE7 QB4 RB3 WR1 | 2335 | −135 | 2530 | 0 | 0 | WR1 | [6, 7, 8, 9] | |
| 12T_ppr_SF | 1 | FIX_ON | WR8 RB3 TE2 QB2 | 2592 | +123 | 2530 | 0 | 0 | – | [6, 7] | |
| 12T_ppr_SF | 1 | FIX_OFF | WR8 RB3 TE2 QB2 | 2592 | +123 | 2530 | 0 | 0 | – | [6, 7] | |
| 12T_ppr_SF | 6 | BASE_ON | TE7 QB4 RB2 WR2 | 2357 | — | 2466 | 2 | 2 | – | [6, 7, 8, 9] | MATCH |
| 12T_ppr_SF | 6 | BASE_OFF | TE9 QB4 RB2 | 2097 | −260 | 2466 | 0 | 0 | WR2 | [6, 7, 8, 9] | |
| 12T_ppr_SF | 6 | FIX_ON | WR8 TE3 RB2 QB2 | 2520 | +163 | 2466 | 0 | 0 | – | [6, 7] | |
| 12T_ppr_SF | 6 | FIX_OFF | WR8 TE3 RB2 QB2 | 2520 | +163 | 2466 | 0 | 0 | – | [6, 7] | |
| 12T_ppr_SF | 12 | BASE_ON | TE5 QB5 RB3 WR2 | 2277 | — | 2548 | 1 | 1 | – | [2, 6, 7, 9, 10] | MATCH |
| 12T_ppr_SF | 12 | BASE_OFF | TE6 QB5 RB3 WR1 | 2158 | −119 | 2548 | 0 | 0 | WR1 | [2, 6, 7, 9, 10] | |
| 12T_ppr_SF | 12 | FIX_ON | WR7 RB4 TE2 QB2 | 2442 | +165 | 2547 | 0 | 0 | – | [2, 6] | |
| 12T_ppr_SF | 12 | FIX_OFF | WR7 RB4 TE2 QB2 | 2442 | +165 | 2547 | 0 | 0 | – | [2, 6] | |

Against the roster-proof control (the seat after mine, drafting best projection at a position
it still needs): the fixed engine beats it in 4/6 seats (1QB seat 1 +63, SF seats 1 +62 and 6
+54; 1QB seat 6 +52) and trails it in 1QB seat 12 (−18) and SF seat 12 (−105). The pre-fix
engine trailed the control in 6/6 (−224 to −271). Not a gate; recorded.

### 2.2 How a fixed seat drafts (1QB seat 1, FIX_ON — every pick unforced)

    r1 RB Gibbs 232.9 | r2 TE Bowers 142.0 | r3 TE McBride 129.0 (FLEX open: full VOR, the guard's own case)
    r4 RB J. Williams 79.0 | r5 TE Warren 70.6 (second FLEX open: 245 pts beats the best WR's 222)
    r6 WR Coker 11.2   -- first pick where TE is deducted: TE −82.4, RB −68.1 (every reachable slot held)
    r7 WR Metcalf 5.5  | r8 QB Mahomes 4.0 (bpa 0.00 + need 4.0; every other row negative)
    r9 QB Love −11.2   | r10-14 WR ×5 at −18 … −84 (the bench regime, §4)

Three tight ends START in this format (TE, FLEX, FLEX), and by projected points they should:
the lineup total says so. The fourth never comes.

## 3. The invariants

1. **Backstop never binds** — 0 forced picks in 6/6 seats, OFF == ON compositions. Battery class A 7/7.
2. **QB priced positive while open, ≤ 0 once filled** — on `final_score`, every turn, 3/3 1QB seats; see §4 for what carries the positive price.
3. **A candidate the lineup cannot use never outranks one filling an open slot at positive VOR** — battery D 6/6 pairs (LaPorta −35.6 under Adams 21.0; every pair), C 2/2 (separation 98 against bias 58.5 in 1QB).
4. **My own bench picks never improve my signal at that position** — the ledger gap (WR−TE on `universal_value + displacement_adj`) is FLAT across every bench pick in every seat (−28.02 for six picks in seat 1; −16.94 in seat 12; −9.44 in SF seat 12) while the league gap the pre-fix board ordered on widens 53.6 → 94.0 as the pool drains. One residual survives, on `final_score` not on the ledger: `depth_exposure` (#139) lifts a hoarded position by ≤ `DEPTH_EXPOSURE_MAX` at the pick where a bench first exists (+3.72 on TE#7 going from three to four owned). Pinned as a residual in `test_216_displacement`, not smoothed; see §5.
5. **Most-drafted bench position, backstop OFF** — see §4.
6. **Replay gate** — 6/6 recorded sequences reproduced by the term-off arm; 0 order-gate failures in 24 drafts.

## 4. What is NOT fixed, stated exactly

**(b) The quarterback's own price.** With the term on, the QB is taken at r8 unforced in every
1QB seat — but not because he is priced. His bpa is 0.00 at every open turn from r2/r3 (rank 1 =
himself, the collapse the review measured), and the 4.0 that ranks him is `need_bonus`. He wins
at r8 because the displacement term has priced every surplus row BELOW 4.0 by then; in a room
where a positive upgrade at RB/WR remains available late, he would wait, and the backstop could
still bind at the last pick. The term repairs the competition, not the quantity. Repairing the
quantity means either the horizon floor (ruled observable, #48/#50) or an off-by-one
redefinition of replacement (rank demand+1); both belong with #50 and neither is in this
change. `replacement_levels`' docstring now says this in so many words.

**The bench.** Starters are fixed; the bench has a ruler now, and it is not the one a person
would choose unaided. Once every starting slot is held above the league alternative, every
candidate is priced against my weakest reachable starter, so the bench is ordered by
"nearest to cracking my lineup". On this pool that is receivers: bench picks (the six after the
eight starters, backstop OFF) were **TE6** / **RB3 TE1 WR1 QB1** / **TE4 QB1 WR1** before and
are **WR5 QB1** / **WR6** / **WR5 RB1** after (1QB seats 1 and 12, SF seat 12). Invariant 5's
observable: the most-drafted bench position count (5-6 WR) rises while the LEDGER gap it is
ordered on stays flat — the two are no longer monotone together, which is what "my picks do
not improve my signal" means. But six receivers is not insurance at RB or TE, and nothing here
claims it is; a bench ruler (insurance value against `depth_exposure`'s measured loss, or an
asset ruler) is #62/#115 and remains open. Reported as: **starters fixed, shape of the bench
changed from a hoard the board reinforced to a hoard the board does not, not to a balanced
bench.**

**A second quarterback in 1QB seat 1 (r9, Love, −11.2).** Once my QB slot holds Mahomes
(328.6) and league QB demand is 0, QB rows are priced against the PRE-DRAFT anchor (QB12 =
328.6 — Mahomes himself was that anchor), so Love at 317 is only −11 and the least-negative row
on the board. That is #165/#155's exhausted-demand anchor, not this term; the term deducts
nothing because my starter equals the anchor exactly. Recorded, not repaired.

**`depth_exposure`'s direction** (the adversary's B-class observation): +≤12 at a position I am
stacked at, 0 where I am vacant. Survives this fix at its bounded size; the 43-60 point bias it
sat beside is gone.

## 5. Tests

New: `test_216_displacement.py` (17 tests: the derivation on hand-built rosters, the no-constant
AST check, the wiring on the real rulebook, and reviewer invariants 2, 4 and 6's in-process
toggle). Battery: `test_216_value_board_falsification.py` 19/19 and `test_216_room_integrity.py`
20/20 (executed in Chromium), unedited except where instructed (§6).

Existing tests whose PREMISE the change alters, each updated in place with the reason:

| test | premise | why it no longer holds |
|---|---|---|
| `test_depth_exposure…test_the_layer_identity_holds` | four-term identity | fifth term |
| `test_draft_room…test_multi_eligible_candidate_gets_a_positive_bonus…` | three-term identity ("documented three-term sum") | five terms; and the WR-only control on that roster is now displaced (WR, WR, FLEX held) while the WR/DB candidate is not (his DB eligibility reaches the open IDP_FLEX) — asserted, both ways |
| `test_display_contract_boundary…schema_is_pinned` | 45 fields | 47; both questions the pin asks are answered in the comment |
| `test_threshold_reachability…cliff_protection_fires_for_most_candidates` | fires 73.6% (top six rows dominated by a hoarded position's steep tail) | 35.4% (17/48) on the same states; the constant did not move, the population did; pinned to the new neighbourhood, CDME_CONTRACTS corrected |
| `test_216_room_integrity…no_roster_term_is_negative_on_todays_board` | no deduction exists today | rewritten as the contract: every negative roster term is a `measured` `displacement_adj` accounting for the whole difference |
| `test_216_room_integrity…snapshot_identity_includes_the_depth_term` | four-term identity | fifth term, and asserted non-vacuous on the four-TE state |
| `test_216_room_integrity…identity_has_the_three_named_roster_terms` | the pin the file tells the implementer to bump | bumped, with the four carriers it names each tested |

Mutation results: §8.

## 6. The room

`serialize_candidate` now carries `depthExposure`/`depthBasis` (which never reached the JS
before — the adversary's finding) and `displacementAdj`/`displacementBasis`; the payload carries
both label tables from Python (`pick_synthesis` re-exports them; the UI imports no valuation
module). The focus panel states a displacement deduction with its magnitude and its basis
words, states a depth lift with its basis, and states any remaining deduction it cannot name
(#187's shape). An unknown basis token renders as itself. The Streamlit recommendation panel
gets a fourth card on its second row, rendered under a `measured` basis only (dash otherwise,
"(floor)" under the partial basis), label and help from `DISPLAY_CONTRACT`. The stale
"scaled against the largest gap left in the pool" prose (metric help, legend tooltip,
design_system's vocabulary note, draft_room's ARCHITECTURE paragraph) is corrected: the
pricing layer is the identity. `pick_debate`'s evidence line names the fifth term, qualified by
its basis like depth.

## 7. Full suite

(filled in after the run — see the bottom of this file)

## 8. Mutation results

(filled in after the run — see the bottom of this file)

## 9. The loose thread: `test_the_board_is_not_the_projection_control`

Classified **(b′)**: not a bug in the guard and not a finding about the engine — the reported
failure does not reproduce. Run on the UNFIXED engine (ui-authority-pass @ 2f5f304, which
carries zero engine changes since f580c11 — `git diff f580c11 HEAD -- '*.py'` touches only the
four #216 instrument/test files) the committed guard PASSES (1 test, 14.0s, OK), and passes
again with the fix (population non-vacuous: >5 QB/WR pairs where the QB out-projects the WR by
more than horizon+risk could move a row and the board still prices the WR higher; 0 inverted).
The adversary's own docstring records two earlier drafts of this test that were vacuous under
the real rulebook; the interrupted run's "FAILING" almost certainly belongs to one of them, and
the committed third form is the over-correction guard it was meant to be (class E: passes
today, must still pass on a fix). It belongs in the "passes on unfixed code" set. It did not
inform the design.
