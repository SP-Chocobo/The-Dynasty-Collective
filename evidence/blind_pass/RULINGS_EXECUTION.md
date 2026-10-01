# Executing the seven owner rulings

One file per ruling as it is worked, with the measurement taken BEFORE the change. The rulings
themselves and the measurements they were made against are in `CDME_CONTRACTS.md`; this is the
record of carrying them out.

---

## `6.1b` — unify the multi-eligibility price *(measurement complete; removal pending)*

The ruling: **unify** `displacement_adj`'s lift and `eligibility_bonus` into one derived price.
Before designing anything, the premise was measured, because *"these two may both be pricing
multi-eligibility"* is a claim and not an observation.

### What the two terms actually are

The code already states the division of labour, at the call site:

> *"the open slot is his, and `eligibility_bonus` prices what that flexibility GAINS him; this
> term must not take it away."*

So `displacement_adj` is meant to be a **deduction** (the league anchor's over-credit) and
`eligibility_bonus` the **lift**. W1-01 found that on a multi-eligible row `displacement_adj`
goes **positive** — at which point it has stopped removing over-credit and started paying for
flexibility, which is what the other term already pays for.

The lift is not arbitrary. `test_216_displacement` argues it well: a WR/DB anchored on a WR
level of 216 whose cheapest reachable slot is worth 104 was **over-penalised** by his own
anchor, *"so passing on him costs 104, not 216 — and the term says so with a LIFT."* It is the
anchor correction running in the other direction.

### Measured — 36 board states, 3 rulebooks, 4 roster depths, 3 seats, 46,020 rows

| | |
|---|---:|
| single-position rows with `displacement_adj > 0` | **0 of 45,255** |
| multi-eligible rows with `displacement_adj > 0` | 12 of 765 |
| distinct players lifted | **1** (Travis Hunter, IDP only) |
| lift — mean / max | 118.31 / **129.40** |
| `eligibility_bonus` on those same rows — mean / max | 0.28 / 0.84 |
| `eligibility_bonus`'s share of the multi-eligibility credit | **0.24%** |
| lifted rows exceeding `ELIGIBILITY_BONUS_MAX` (12.00) | **12 of 12** |
| rows where `eligibility_bonus` pays and the lift does not | **1**, at 0.24 |

The stated non-positive contract holds perfectly over the population it was written for, and
the lift does essentially all of the multi-eligibility pricing where both terms fire.

### The non-vacuity check that changed the conclusion

The first reading of those numbers was *"`eligibility_bonus` is a vestigial term"*. That would
have been wrong, and the check that caught it is the one this programme keeps relearning:
**print the population.**

Broken down by rulebook, the multi-eligible population on a board is **2 rows** in both
non-IDP leagues — both `DB/WR`. So the measurement said nothing at all about those formats.
And `draft_room`'s own comment names the case the term was built for: *"WR/TE dual eligibility,
a common real Sleeper listing"*, once measured at an 82.00 bonus.

Counted over the capture rather than over a board:

| | |
|---|---:|
| players carrying more than one fantasy position | **178** |
| of those, offence-only (the term's intended population) | **8** |
| of those 8, reaching a board | **0 — every one is retired** |

Kelvin Benjamin, Vince Mayle, Marcus and Tyler Thigpen, B.J. Daniels, Richie Brockel, Will
Johnson, David Johnson. The live population is IDP cross-family — `DL/LB` 127, `DB/LB` 37 —
plus Travis Hunter at `DB/WR`, and flexibility between two IDP slots at similar levels rarely
moves an optimal lineup.

**So the term is inert because its population is empty, not because the term is wrong.** That
distinction decides how it is retired: the ruling was made against an empty population, and a
vendor refresh could refill it.

### Registered before anything is removed

`invariant_registry` gains a ninth entry counting that population, with the census at **178**.
This is the registry watching a population **shrink** — the direction nobody checks. Every
other entry guards against a population growing past a claim proven over a smaller one; this
one fires if an active offence dual-eligibility listing ever returns, because the ruling that
retired the term was made against a population that has none.

That guard is the thing whose absence let the term go inert unnoticed in the first place.

### Still to do

Retire `eligibility_bonus` from `team_acquisition_value`, `TEAM_SPECIFIC_TERMS` (census 4 → 3),
`TEAM_SPECIFIC_CAPS`, and `ELIGIBILITY_BONUS_MAX`. It is named in **31 test files**, so the
removal is its own pass rather than a tail on this one. `lineup_optimizer.eligibility_bonus`
itself stays — it is a correct, general-purpose function with a second consumer; what is
retired is its wiring into the board's sum.

Expected effect on today's boards, stated in advance so it can be checked rather than asserted:
**five rows change by at most 0.84**, and no row changes by more than that.

### The removal was written, measured, and staged rather than shipped

The production-side change is complete and kept at `evidence/blind_pass/6_1b_removal.patch`
(209 lines, six sites: the computation, the sum, the emitted row, `TEAM_SPECIFIC_TERMS`,
`TEAM_SPECIFIC_CAPS`, `ELIGIBILITY_BONUS_MAX`, plus the `CandidateSnapshot` field, the necessity
roster-fit component, the board payload's `eligBonus` and `pick_debate`'s arithmetic line). It
is staged, not merged, because the measured blast radius says this is its own pass.

**The predicted effect was confirmed exactly** — but only after the A/B was fixed, and the
first version of it lied:

> Two runs reported **0 of 5,790 rows moved**. Both were the new code measured against itself.
> The shadow directory holding the old `draft_room.py` was inserted at `sys.path[0]` and then
> the repo root was inserted at `sys.path[0]` *after* it, putting the real module back in
> front. `dr.__file__` was identical in both arms. This is the engine-measurement skill's own
> warning arriving in practice: *the failure mode to fear is not a crash, it is a plausible
> number about something else* — and "no row moved" is the most comfortable plausible number
> there is. The arm that caught it was asking each run to print which file it had loaded.

With the path order corrected, on the IDP board state where the term was measured at 0.84:

| | |
|---|---:|
| rows compared | 1,889 |
| rows whose `final_score` moved | **1** |
| Travis Hunter | −24.63 → **−25.47** (delta **−0.84**) |

Exactly the predicted magnitude, on exactly the row that carried the term.

### Measured blast radius — why this is its own pass

Full suite with the removal applied: **3,263 tests, 275 failures across 26 modules**, and they
split cleanly:

| kind | count | what it is |
|---|---:|---|
| `TypeError: CandidateSnapshot.__init__() got an unexpected keyword argument` | 152 | fixtures constructing the dataclass |
| `AttributeError: 'CandidateSnapshot' object has no attribute` | 67 | reads off a snapshot |
| `KeyError: 'eligibility_bonus'` | 39 | dict access on a board row |
| `AttributeError: module 'draft_room' has no attribute 'ELIGIBILITY_BONUS_MAX'` | 3 | the retired constant |
| **`AssertionError`** | **14** | **the real ones — assertions that encode the old behaviour** |

261 of 275 are mechanical references to a field that no longer exists; 14 need judgement. The
mechanical ones are deletions of references rather than weakenings of assertions, so they are
low-risk — but 26 files of them beside 14 judgement calls is a full pass, and doing it in the
tail of another one is how a guard gets quietly weakened. That is the failure this programme
exists to catch, so the tree was restored rather than left half-cut.

Next pass starts from the patch and works the 14 `AssertionError`s first, since those are the
ones that decide whether the ruling has been implemented or merely applied.

---

## `W1-07` — substitute `intervening_picks` *(implemented, measured, STAGED — the ruling forces a second derivation it did not cover)*

The ruling: replace `NECESSITY_SURVIVAL_WEIGHT`'s withheld input with `intervening_picks`, the
measured substitute every surface already shows in survival's place.

Implemented faithfully and kept at `evidence/blind_pass/w1_07_substitute.patch` (129 lines).
The derivation half works. The consequence does not, and it is a consequence the ruling was not
made against.

### The substitute is a property of the TURN, not of the player

Measured across seven turns of a 12-team superflex snake, counting DISTINCT values across the
candidates at each turn:

| turn | `intervening_picks` | `survival_probability` |
|---|---|---|
| 13 | **1** value (20) | 18 values |
| 20 | **1** value (6) | 7 values |
| 24 | **1** value (22) | 7 values |
| 35 | **1** value (0) | 1 value |

`(1 − survival)` separates the player who will not last from the one who will. `intervening_picks`
cannot: it is identical for every candidate on the board. So the substitution does not
re-source the same signal — it **removes a per-candidate discriminator and adds a uniform
per-turn offset**. Relative order among candidates is untouched; every absolute label moves.

### The scale IS derivable — that half is sound

`max_intervening_gap` reads the largest gap between two of my selections from the **real pick
order**, not from `2*(teams − 1)`, so a third-round reversal or any other commissioner shape is
normalised by the order it actually has. For a standard 12-team snake the two agree at **22**,
which is a check on the derivation rather than its source. No constant was chosen.

### And then the measurement, against the one the ruling was made on

| | ruling's measurement | measured after implementing it |
|---|---:|---:|
| label flips | 12 of 384 — **3.1%** | **421 of 679 — 62.0%** |
| necessity delta, mean | — | **12.09** |
| necessity delta, max | **8.50** | **19.70** |
| direction | mixed | **every flip upward** |

`PREFERRED → STRONG ACTION` ×223, `CLOSE CALL → PREFERRED` ×143, `PREFERRED → MUST TAKE` ×46,
`STRONG ACTION → MUST TAKE` ×9. Distinct necessity values per turn collapse from 13–22 to a flat
**10**.

**Why**, and it is the whole finding: the two quantities normalise to the same `[0, 1]` but
occupy **opposite ends of it**. Most candidates survive, so `(1 − survival)` sat near the
bottom and contributed ~2 of its 20 points. A snake's gaps are bimodal — my probe's turns ran
20, 6, 22, 0, 22, 0, 22 — so `gap / max_gap` sits near the **top** at most turns and contributes
the full 20. Keeping the weight at 20.0 to "preserve the term's share" does not preserve it;
nominal share and realised contribution are different things, and only the first was preserved.

### What that means, stated rather than patched around

The label thresholds (`MUST TAKE` 98, `STRONG ACTION` 85, `PREFERRED` 65, `CLOSE CALL` 50,
`LOW URGENCY` 30) were set against a score distribution this changes. Implementing W1-07 as
ruled therefore **forces a re-derivation of the necessity label thresholds** — a second
`#56` exercise the ruling did not cover, and exactly the dependency shape the displacement lift
has with `context_elevated`.

Picking a weight that reproduces today's labels instead would be calibration: the thing `#56`
forbids, and the thing the ruling's own record already warned against — *"the 12 label flips are
the BEFORE measurement it gets checked against, never the target it is fitted to."*

So the work is staged rather than shipped, and the choice returns to the owner:

1. **Accept the shift** and re-derive the five label thresholds against the new distribution.
2. **Take reading 1 instead** (remove the term outright) — now knowing that reading 3 costs a
   discriminator either way, so the difference between them is only the per-turn offset.
3. **Keep a per-candidate urgency signal** from some quantity that is not withheld and does vary
   by player — which is a new derivation nobody has proposed, not a choice among the three.

---

## `J-13` — raise instead of an empty player universe *(closed)*

The ruling: **raise**. Two defects that compound, repaired together because neither is safe alone.

**The write.** `get_players` cached ~10 MB with `write_text`, the exact pattern `store_io`'s own
docstring measures at **91,956 empty reads of 98,405** under one concurrent writer — `write_text`
truncates before it writes. `app.py` calls `get_players()` at top level on every rerun and
Streamlit serves many tabs from one process, so the concurrent reader is not hypothetical. Both
snapshot writes had the same shape, and a torn read of `_latest.json` looks exactly like a
league that was never synced.

**The read.** When the fetch failed *and* the cache was unusable, it returned `{}` — a player
universe indistinguishable from a league with no players, handed to callers that build boards
from it. Compounded: a torn read forces a refetch, the refetch fails, and every surface computes
against nothing and reports the result as an answer.

### The distinction that shaped the repair

The cache does **not** get `store_io.write`'s protection, and that is deliberate. A store's
damaged bytes are the only copy, so refusing to overwrite them is right. A cache is
re-fetchable by definition, so the same refusal would make a corrupt cache **permanently
un-refreshable** — a worse bug than the one being fixed, installed by the fix. So the atomicity
was published on its own as `store_io.replace_atomically`: the mechanism, none of the semantics.
Pinned by a test that arms the damage mark and checks the store refuses while the cache does not.

### Collateral: a guard that had stopped pointing at anything

Extracting the mechanism broke `test_the_temp_file_is_written_in_the_same_directory_as_its_target`,
which read `_write_unlocked`'s source for `path.with_name(`. It **failed loudly only because the
remaining body was a one-liner** — a larger one would have passed while scanning a function that
no longer contained the mechanism. Re-derived: the guard now *finds* the function that performs
the replace and asserts there is exactly one, since two writers would mean two places the rule
must hold and only one of them checked.

Five mutants, all killed: the empty universe returning, each of the two write sites reverting to
`write_text`, the temp file moving to the system temp directory, and the cache primitive
inheriting the store's refusal.

Full suite: **3,285 tests, 0 failures.**

---

## `J-12` — wire `draft_history` narrowly *(closed)*

The ruling: **wire it narrowly** — record a snapshot only when a debate actually ran on it.

The module called itself *"the substrate for all three (`#92`)"* and had **no writer at all**:
`grep -l draft_history *.py` over non-test files returned only itself. It also had no test
module of its own, which is consistent — there was nothing to exercise.

### The part that makes this more than a missing call

`test_cdme_ingestion_boundary._NEVER_IMPORTED` lists this module among those CDME must never
import, and the reason is sound: a stored record read back into the computation that produced
it is a feedback loop, and a number acquires authority purely by having been written down. But
that assertion was **trivially true of a store nothing wrote** — a guard passing because its
subject is absent, which is the same shape as an absence assertion passing because the quantity
was never computed. Wiring a writer is what makes that guard a constraint rather than a
tautology, so the two files are now a pair and each says so.

### Why narrow, in one measurement anyone can repeat

The Draft Room rebuilds a snapshot on **every rerun**, including reruns caused by an unrelated
button elsewhere on the page — the Prytaneum dock's own Expand/Collapse calls a bare
`st.rerun()` purely to change a CSS height. Recording each one fills the store with boards
nobody looked at. A board someone put to the debate is a decision; a board that merely rendered
is not. The wiring test asserts **exactly one** call site, so the broad rule cannot creep back
in beside the narrow one.

The write is wrapped, because the module's own contract is that a damaged history file must not
take down a live draft — and the same has to hold for a failed write. A draft in progress is
not the place to discover the disk is full.

### Mutants

Three, all killed: the writer unwired again, the board filed under a name nothing else uses
(`id(snap)` instead of `snapshot_identity`), and the write left unguarded.

**One of them exposed a defect in the test rather than the code.** The unwired mutant first
died in `setUpClass`, because `ui_source.unit_containing` RAISES when its needle is missing —
so the test written to say *"no UI surface writes to draft_history"* never ran, and a reader
got a lookup error instead of the sentence. A guard whose failure does not name the problem is
half a guard. The suite now parses each UI unit separately, so an absent writer is an empty
result rather than an exception, and all three affected tests fail with that same sentence.

(The first attempt at that mutant was also wrong in a way worth recording: commenting the call
out with `if False:` orphaned its `except` clause and produced a **SyntaxError**, so what was
being tested was the parser, not the wiring. Re-run as a clean removal.)

Full suite: **3,294 tests, 0 failures.**

