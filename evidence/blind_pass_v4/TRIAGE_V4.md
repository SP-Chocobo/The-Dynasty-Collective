# v4 blind pass — triage of the findings that were not repaired on arrival

Five findings were repaired at `5fbf0ff` / `cdc48d3` (the blocking set: `D-F1`, `A-F2`/`B-F1`,
`C-F1`/`E-F1`, `B-F2`/`A-F3`/`E-F4`, `E-F2`). This file dispositions **every remaining finding**
under `V4_GATE_CRITERIA.md` §5, and applies §Purpose's blocking question to each:

> Would repairing this later force a change to something a production build already rests on?

**THE REMAINING SET IS 25 FINDINGS, NOT 21.** The "21" I used when opening this work came from
subtracting five repaired *items* from 26 *findings*; four of the five repaired items are
convergences carrying two or three IDs each, so the subtraction was against the wrong unit.
Enumerated mechanically from the findings file: 34 distinct IDs, 9 belong to the repaired five,
25 remain.

---

## A — CONFIRMED DEFECT, BLOCKING. Repair before v4.

| id | one line | why it blocks |
|---|---|---|
| **A-F5 / C-F2** | `team_count` has three live derivations; the screen says 10 where the engine says 12 | `num_teams` is the denominator of every replacement level and the multiplier of `remaining_starter_demand`'s bound. A production build rests on every one of those numbers. |
| **B-F6** | one `None`-roster pick makes `len(filled) = num_teams + 1` and **the board build raises** | same surface as A-F5, and it is a crash on real input, not a discrepancy |
| **B-F4** | `feasibility_first` promotes by PRIMARY BUCKET while its mirror `unfieldable_last` reads eligibility | it decides `_feasible`, which is the first sort key of every board. A DL/LB dual gets promoted for a slot he cannot fill; a pure LB who can fill it does not. Changing the candidate side later moves boards. |
| **C-F3** | eligibility never crosses the snapshot boundary, so an LB view hides T.J. Watt | the fix adds a field to `CandidateSnapshot`, which the UI, the picker and the stored-board replay all read. Deferring it means changing that shape after production rests on it. |
| **D-F2** | `prose_names`' history shield exempts 45% of the corpus; three dead names sit behind it | the instrument certifies "0 dead names" **at the freeze**. The v3 freeze record already quotes that zero and it is wrong. |
| **D-F3** | the test measuring that shield's reach compares 18 of 19 constants to their own definitions | same surface as D-F2, and it is the check the freeze record's "costs nothing" claim rests on |
| **D-F4** | `assertion_floors`' per-method floor is keyed on the bare method name, so same-named methods in two classes collide | this is the ratchet **every future certification in this repo rests on**, and the collision reopens precisely the hole the v3 range's repair claims to have closed |
| **D-F5** | the hand-written-capture-path guard exempts any module that mentions `CAPTURE_PATH` anywhere, and one real offender hides there | a Tier 0 instrument reporting a false zero; cheap, and everything downstream quotes it |
| **E-F5** | when the season fetch fails outright the Draft Room renders **no warning while the board is vendor-priced** | person-facing silent fallback — the exact defect the surrounding prose names. A production build shipping this prices a board for a manager with no indication the season data never arrived. |
| **A-F1** (second half) | the two priced paths disagree for the population the feed actually reports (`gp=16`), 0 of 13 rule-floor IR rows satisfy the claimed equality | `#126`, one fact one answer. Making them agree requires choosing which denominator is authoritative, and both are live in production pricing today. |
| **D-F6** | `test_the_magnitudes_are_unchanged_by_this_experiment` recomputes `-(games / SEASON_GAMES)` and compares it to itself; changing IR from 4 to 8 games passes | my own work at A2. Coverage is not lost (two siblings pin literals) but the range's stated verification of D8's magnitudes is not a verification. Same shape in two `test_one_injury_vocabulary_not_two` methods. |

## A — CONFIRMED DEFECT, NOT BLOCKING, repaired anyway because each is minutes

Every one is a false or stale *statement* rather than a wrong number. They do not block — repairing
a comment later forces nothing — but `#292` (the record wins) and `#133` (a docstring that
overclaims its own coverage is the defect) both make them cheap debts worth clearing in the cycle
that found them.

* **A-F4 / C-F5** — `Doubtful` is priced by `HEALTH_DISCOUNT_RATE` but `availability_factor`
  consults `GAMES_MISSED_FLOOR`, not `GAMES_MISSED_PRICED`, and returns `unrecognised_designation`
  for it. One vocabulary, two answers (`#126`). Dormant only because `Doubtful` is absent from the
  feed — which is luck, not design.
* **B-F5** — stale invariant comment in `unfieldable_last.demoted`: "a flex-reachable position never
  enters `saturated`". Since D7 it does. It is the comment that justifies the subset test.
* **C-F7** — `superflex_disagreement` tells the user "every consumer keying off SUPER_FLEX will
  score it as 1QB" while `league_format_hint`, `league_format_summary` and `starter_slot_counts` all
  treat it as superflex. False in the direction of alarm.
* **C-F8** — `GAME_TIME_CALL_DESIGNATIONS`' docstring says unrecognised in both directions; the pill
  paints every non-member crimson, which is the stronger claim "unavailable".
* **C-F4** (the prose half) — `decision_config`, `admits_decision` and `confirmation_state` have
  **zero production callers**, so the contract's "ambiguity is enforced" describes nothing that
  runs. The sentence is repaired now; *whether refusal should exist* is E below.
* **D-F7** — `tav_margin_profile` counts a pick a backstop **deliberately demoted** (margin −90)
  under `zero_margin_picks`, a name meaning "the ordering stopped carrying information". In the very
  module repaired so that report fields mean their names.
* **E-F7** — `unanswerable` is computed from `evidence.get(field) is None`, conflating "key absent"
  with "captured as None", so one row can carry a staleness verdict AND say the question cannot be
  asked. `#187`'s absence contract, in the instrument that reports absence.
* **E-F3** — for schema-4 columns, "key never existed" and "captured as absent" both render `—` and
  the picker label does not show the schema version. Same root as E-F7; repaired with it.

## B — VALID, OUT OF SCOPE. Recorded, not repaired.

* **A-F6** — `TIME_HORIZON_SLOPE`'s stale unit premise. Predeclared: `D4(b)` is out of scope and
  `#56` routes every chosen magnitude to **E**. The finding is right that D4 reused an
  un-re-derived slope and called the result derived; that is D4(b)'s own territory, already the
  owner's. **The unreachable lower clamp** (`growth = max(0.0, ...)` makes `TIME_HORIZON_CLAMP[0]`
  dead) is separable and is repaired with the prose group above.
* **B-F3** — the fieldability exemption conflates "flex-reachable" with "the league starts nobody
  there". Real: measured 2 of 173 priced DL/LB rows. Recorded as **B** under §5's own clause —
  repairing it later *adds* demotions in a class that is currently silent, and forces no change to
  anything production rests on. It is also adjacent to `D7(a)`, predeclared.
* **E-F6** — the universe stamp hashes `search_rank`, which churns. Argued from code only: the
  committed capture is trimmed to 10 fields, **so the churn rate cannot be measured offline**, and
  §5(D) forbids changing behaviour on a finding whose magnitude no instrument here can establish.
  Recorded with what it would take to measure it.

## C — EXPECTED / ALREADY CLOSED

* **C-F6** — "`health_penalty` returns 0.0 where its contract says NaN". **Closed by the `A-F2`
  repair, not by an argument**: that repair replaced the absent-projection `float("nan")` with
  `0.0` deliberately, so both branches now return `0.0` by design and there is no contradiction
  left to fix. Verified against the current source, not inferred from the commit message.

## E — OWNER'S CALL. Not decided during the gate.

* **C-F4** (the behaviour half) — **should an unrecognised slot code refuse to price the board?**
  `league_config`'s contract says AMBIGUOUS is "the only blocking state" and that ambiguity is
  "enforced"; nothing enforces it, and today an unknown slot is silently dropped while the warning
  text says "The board below was priced anyway". No established requirement settles which is
  wanted: refusing protects a manager from prices computed on a config nobody parsed, and also
  takes the board away from him mid-draft over one unrecognised label. Several behaviours are
  reasonably intended, so §5(E) says escalate rather than choose. Filed as **D10**.
