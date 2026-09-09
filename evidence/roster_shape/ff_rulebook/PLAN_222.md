# #222 -- What fits, what's broken, and the plan

Measured on Fourth and Forever's real rulebook, real Sleeper universe (6,595 players),
real season projections (5,346) scored under this league's own settings, against the twelve
real managers who drafted that league. No engine source has been changed.

---

## PART 1 -- WHAT FITS

These were measured and came back correct. They are not the problem and should not be
touched while fixing what follows.

| | evidence |
|---|---|
| **Running back allocation** | 26.9% engine vs **27.4%** human. Essentially exact. |
| **The first quarter of the draft** | picks 1-78 run QB 30.8 / RB 29.5 / WR 25.6 / TE 14.1 -- a sane opening shape. The engine drafts starters well. |
| **Scoring propagation** | every offensive category in this league's rulebook has stat data behind it, including the three this league has and no battery format does (`pass_cmp`, `rush_fd`, `rec_fd`). Six rare categories have no data and are now declared. |
| **The displacement term, IN ITS WORKING RANGE** | the deduction charged to the next tight end grows correctly as a roster saturates: -51.7 at 2 held, -55.9 at 3, -91.9 at 4, -119.4 at 5, -120.4 at 6. The construction is sound. |
| **Determinism** | identical inputs reproduce identical drafts, byte for byte. |
| **The identity/provenance layer** | #77/#82/#196 repairs hold; no crossed wires or duplicate rows surfaced in 312 picks. |

---

## PART 2 -- WHAT IS BROKEN, RANKED

### B1. The saturation brake releases exactly when it is needed (BLOCKER)

The engine drafts **101 tight ends in 312 picks -- 32.4% against the humans' 15.5%.** Every
seat finishes with 5 to 12. The back half of the draft is half tight ends.

The cause is measured, not inferred. The deduction charged to the next tight end, by how
many that seat already holds:

| TEs held | 2 | 3 | 4 | 5 | 6 | **7** | **8** |
|---|---|---|---|---|---|---|---|
| `displacement_adj` | -51.7 | -55.9 | -91.9 | -119.4 | -120.4 | **-51.7** | **-51.7** |

It rises correctly to six, then **returns to its two-held value and sticks there**.
-51.73 appears identically at 2, 7 and 8 held -- board states where the TE replacement
level was 80.5, 29.3 and 16.6 respectively. A term whose every input has changed by a
factor of five cannot legitimately return the same number to the hundredth.

Reproduced in FRESH PROCESSES (not a cache artifact). Cause not yet isolated: candidates
are the non-positive rule in `displacement_level` capping the deduction at
`level - my_own_starter`, or a fallback to `free_alternative` when a reachable slot reads
open. **This is the single highest-value bug in the engine right now.**

### B2. The engine cannot value a backup quarterback (BLOCKER)

**Nine of twelve seats finish with exactly two quarterbacks**, in a SUPERFLEX league where
QB and SUPER_FLEX both start every week. 10.3% against the humans' 20.0%.

Two is the starting requirement with zero backup. Fable predicted this analytically --
"with F_p = 1 a third body can never be promoted by an absence" -- and it is now observed
live on the owner's own league.

**B1 and B2 are the same defect wearing two faces.** A body that cannot improve TODAY'S
optimal lineup is priced at nothing. That makes the engine take too few quarterbacks (a
third can never start) and too many tight ends (the term that should stop it releases).

### B3. Bench-phase picks are decided in the noise (HIGH)

At the round-15 board, the top three rows were **-85.3, -85.3, -85.4** -- three different
positions, component terms ranging from `bpa` +33.7 to -86.6 and `displacement_adj` 0.0 to
-113.3, all landing within 0.1 of each other.

That is the anchor cancelling, correctly, and leaving projection. But it means the entire
bench phase is decided at the 0.1-point level -- effectively by tiebreak ordering. #114
established that tiebreak-decided rounds were eliminated in the STARTER phase; nobody has
asked the question about the bench phase, and the answer here looks like "most of them".

### B4. Board rank is not pick order, and my probes assumed it was (HIGH, methodology)

`simulate_full_draft` selects through `pick_synthesis.build_snapshot` and takes
`candidates[0]`, which re-sorts through `narrow_candidates`' own key. **`final_score`
ordering on the board is NOT what gets picked.** Several probe readings this session
implicitly assumed it was. The engine-measurement skill already warns about this
("a decision expressed only as ROW ORDER is discarded before the pick"); it needs to be a
register item, not a footnote.

### B5. The measurement recipe is stale (HIGH, methodology)

Six fixture errors of one class in this repo, one of them last night. The skill's five-line
fixture still names `rdb.build_players_db` -- the 764-row vendor reconstruction -- which
#201 superseded with `build_players_db_from_capture` (6,595) plus
`season_projections_from_capture` and `SLEEPER_BASIS_SEASON_SUM`. Any probe following the
documented recipe measures the wrong population and produces plausible numbers about it.

---

## PART 3 -- WHAT I CANNOT YET SAY

- **Whether B1/B2 generalise beyond this rulebook.** One league, one draft. A 3RR arm is
  running; other formats have never been drafted on the real universe.
- **Whether -51.73 is a bug or a surprising-but-correct consequence** of the non-positive
  rule. It has to be read out of `displacement_level` directly, not inferred.
- **A reversed-seat-order arm proved nothing.** Reversing `roster_ids` in a snake only
  relabels seats, so the aggregate must match, and it did -- byte for byte. Recorded as my
  error rather than as a replication.

---

## PART 4 -- THE PLAN

Sequenced so each phase can fail cheaply and stop the next. Standing order applies:
evidence before repair, repair before freeze, freeze before blind audit.

### Phase 0 -- Make the instrument trustworthy (half a day, no engine change)
0.1 Update the engine-measurement skill's fixture to the #201/#204 recipe. (B5)
0.2 Add a probe-level assertion that fails loudly if a board is built from the vendor
    reconstruction while a capture exists.
0.3 Register B4 and make every existing probe that reads board rank state whether it means
    rank or pick.
**Gate:** the skill's recipe reproduces FINDING_05's draft exactly.

### Phase 1 -- Isolate B1 (one day, no engine change yet)
1.1 Instrument `displacement_level` to return `displaced`, the slot it came from, and
    whether it was a phantom or one of my players -- as an observable, per #55.
1.2 Re-run the saturation ladder at 2..10 TEs held and read the mechanism out rather than
    inferring it from the difference.
1.3 Pre-register what a repair must move, and by how much, BEFORE writing one.
**Gate:** a one-sentence mechanical account of why -51.73 recurs. No repair without it.

### Phase 2 -- Repair B1 (one to two days)
2.1 Fix whatever 1.2 names. Constraint: the fix must be DERIVED (#56). No tight-end
    penalty, no tier constant, nothing calibrated to the humans' 15.5%.
2.2 Mutation-test the repair to this repo's standard before believing it.
2.3 Re-run the 12x26 on the real rulebook. **Success is the deduction becoming monotonic in
    bodies held** -- NOT the TE share hitting any particular number.
**Gate:** monotonic deduction, full suite green, and the RB/first-quarter numbers in PART 1
unchanged.

### Phase 3 -- B2, the backup-quarterback problem (two to three days)
This is a real modelling question, not a bug. The engine values a body by what it adds to
today's lineup; a backup adds nothing today and everything on the week the starter is out.
3.1 Decide whether absence-weighted lineup value becomes an INPUT or stays OBSERVABLE
    (#55's shape). **This is an owner decision, not mine.**
3.2 If input: derive it from the rulebook's own slot structure. Fable's memo has the
    derivation; it needs re-deriving on the corrected universe before use.
**Gate:** owner ruling at 3.1 before any code.

### Phase 4 -- Generalisation (one day, mostly compute)
4.1 Re-run the 33-format battery on the capture universe. Every battery number quoted this
    session predates that correction.
4.2 Add Fourth and Forever and Greatest Show on Paper 2 as real-rulebook battery formats.
    They share IDENTICAL starter demand and differ in scoring and depth, which is the
    cleanest contrast available.
**Gate:** B1/B2 either reproduce across formats or are scoped to the ones where they do.

### Phase 5 -- Then, and only then, the freeze sequence
#150 final gate, #52 blind adversarial pass, #53 reconciliation.

---

## PART 5 -- WHAT NOT TO DO

- **Do not fit a tight-end penalty.** 15.5% is twelve people in one league. #56 forbids it
  and it would paper over B1 rather than fix it.
- **Do not tune `NEED_BONUS_MAX` or any cap** to move the TE share. The measured bias is
  50-120 points; the whole reachable need bonus is 8.67. A cap cannot span it and reaching
  for one is how the magic-number failure mode starts.
- **Do not touch the RB path or the first quarter.** They are correct and are the control.
- **Do not trust any battery number** produced before Phase 4.1.
