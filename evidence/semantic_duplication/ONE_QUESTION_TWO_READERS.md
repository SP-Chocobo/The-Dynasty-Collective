# One question, two readers — the defect class that dominated the v4 cycle

**Almost nothing repaired in this cycle was an arithmetic error.** The dangerous defects were
SEMANTIC DUPLICATION: two pieces of code answering what sounds like one question, using
definitions that differ just enough to disagree on real input. Written up as a class because it
recurred five times in one session across unrelated surfaces, and because the fix is not the
obvious one.

## The five, with what each pair disagreed about

| # | the question both claimed to answer | reader A | reader B | what split them |
|---|---|---|---|---|
| `A-F5`/`C-F2` | how many teams are drafting | `team_count(pick_order=…)` on the screen | `team_count(league, picks=…)` in the engine, plus a third spelling inline in `pick_synthesis` and a fourth in `_round_being_decided` | the seats. Only the screen could pass them, so one function ran two rules: 10 on the caption, 12 on every replacement level |
| `B-F6` | what does a pick with no roster mean | `team_count` filtered `None` out | `team_slots_filled` keyed it as the STRING `"None"` | one rosterless pick made the census cover more rosters than the league had teams, and the board build RAISED |
| `B-F4` | can this man fill the open slot | the roster side read `player_eligible_positions` | the candidate side read `scored["position"]` | a DL/LB dual labelled DL scored `_feasible = 1` for an LB-only hole while a pure LB scored 0 |
| `C-F3` | which positions can this candidate start at | `need_bonus` priced him against every eligible slot | the view filter had only `position` | the LB view hid 8 eligible candidates, T.J. Watt among them |
| `D10` | how many starting slots was this board priced on | `starting_slots()` = "not in `NON_STARTING_SLOTS`" | `slots_from_roster_positions()` = "in the position or flex vocabulary" | the first COUNTED THE UNRECOGNISED LABEL ITSELF, so the warning claimed 10 where the solver parsed 9 |

## Why the suite does not catch these on its own

Each reader is individually correct and individually tested. `starting_slots` answers its own
question exactly right; so does `slots_from_roster_positions`. Nothing is broken until someone
asks one of them a question the OTHER one owns — and no test of either reader can see that,
because the defect lives in the choice of reader, not in either implementation.

They also survive mutation testing for the same reason: mutate reader A and A's tests fail
honestly. The bug is that B should have been called.

## THE TRAP: the inverse case, which looks identical and must NOT be "fixed"

Two readers that disagree are sometimes answering two different questions, and collapsing them
would be the defect. Both examples from this same cycle:

* **`A-F1`.** `availability_factor` divides a season-anchored numerator by `gp`;
  `HEALTH_DISCOUNT_RATE` divides by `SEASON_GAMES`. They disagree below a full slate, and I went
  in expecting a units error. The mixed denominators are DELIBERATE: the naive `(gp - missed)/gp`
  keeps removing the same four games forever, so once Sleeper zeroes the weeks already missed the
  engine would charge that absence twice. The committed form is self-limiting. **Nothing needed
  deduplicating; the overstated CLAIM needed scoping.**
* **`depth_exposure`'s two bases.** Under `EXPOSURE_MEASURED` the loss is marginal (`TE1 - TE2`);
  under `EXPOSURE_NO_SURPLUS` it is the starter's whole value. Those are different quantities on
  different scales, and the second is already carried by `universal_value`. Charging it would
  DOUBLE COUNT — so the engine measures its largest exposure exactly where it refuses to price it,
  and that refusal is correct.

**So the test is never "are there two readers?" but "do they answer the same question?"** Two
readers of one question is a defect. One reader forced onto two questions is also a defect. Only
the question distinguishes them, and only reading both definitions answers it.

## How each one was actually found

Not by inspection. Every one came from a specific instrument:

* `A-F5`, `B-F4`, `C-F3`, `B-F6` — the v4 blind pass, by lenses that could not see each other.
* `D10`'s — **by the test written for D10 itself**, which asked what the solver means by "starting
  slot" instead of asserting a literal. A hardcoded `9` would have passed on the buggy code,
  because the fixture and the bug agreed.

That last one is the transferable lesson: **an expectation derived from the authority catches a
disagreement between readers; a literal expectation cannot.** The repaired test asks
`lo.slots_from_roster_positions(roster)` for the number and asserts the message does not include
the unrecognised label — and it would have failed on the first run.

## What to do when the next one appears

1. Name the question in words before touching code. If two call sites would phrase it differently,
   they are different questions and need different names.
2. Find every reader. `grep` the concept, not the identifier — `team_count` had four spellings and
   only one of them used the function.
3. Decide which reader OWNS the question, and make the others call it. Composing existing readers
   beats re-expressing a rule locally: D10's fix is `starting_slots(labels in KNOWN_SLOTS)`, two
   readers this module already had, and no new definition.
4. Write the test against the owning reader's own output, never a literal.
5. If the readers turn out to answer different questions, say so in prose at both sites and leave
   the arithmetic alone — see the two inverse cases above.

## Status

**THREE REPAIRED CLEANLY; TWO STILL HAVE A READER THAT DISAGREES.** An earlier version of this
section said all five, and an independent review of the repairs disproved it. The correction is
kept here rather than quietly applied, because a write-up about readers that silently disagree is
the last document that should carry one.

| | state |
|---|---|
| `A-F5`/`C-F2` team_count | **repaired** -- one function, one rule, `team_count_with_basis` returns which fired |
| `D10` starting slots | **repaired on the number the finding was about**; see the caveat below |
| `B-F4` candidate eligibility | **repaired in substance**, see 2 |
| `B-F6` rosterless pick | **partially** -- see 1 |
| `C-F3` snapshot boundary | **repaired in substance**, see 2 |

1. **`B-F6` agrees on the VALUE and not on the TYPE.** Both readers now treat a rosterless pick
   as `None`, which was the finding. But `team_count`'s picks rule does not coerce `roster_id`
   while its own seats rule and `team_slots_filled` both do, so `0` and `"0"` are two teams to one
   reader and one roster to the other. The same question, two readers, one axis over.

2. **`B-F4`/`C-F3` ask eligibility on both sides now, which was the finding** -- but the composed
   rule, eligibility with a primary-bucket fallback, is spelled at THREE sites, all three added by
   that repair. Step 3 of the method above says to decide which reader owns the question and make
   the others call it. The owning reader exists; three sites wrap it in a locally re-expressed
   fallback instead. That is this very class, introduced by its own repair.

3. **`D10` remains the exemplar for the lesson, with one scope.** The number the test derived from
   the authority is right and would have failed on the first run. The SAME message carries a
   second number, `parsed_starting + len(starters)`, pinned against no authority at all and wrong
   whenever an unrecognised starting label repeats. The lesson holds exactly as stated -- a
   derived expectation catches what a literal cannot -- and the counter-example sits in the same
   sentence as the example.

`#126` (one home for a vocabulary) is the register item this class belongs to, and `#166` (the
companion returned with the number) is what stops a repaired version from drifting again:
`team_count_with_basis` returns the rule that fired, so a caller can tell a real count of one from
a floor of one.

**THE LESSON THIS CORRECTION ADDS.** Four of the five repairs were made by the author of this
document, who then wrote that all five were done. Each repair closed the disagreement it was aimed
at; two opened a narrower one in the same place. An author checking their own repair looks for the
defect they already named, which is exactly the blind spot the class describes -- one reader,
asked twice, agreeing with itself.
