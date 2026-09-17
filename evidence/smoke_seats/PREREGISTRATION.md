# PRE-REGISTRATION — the smoke-seat quality pass

> **Status: PRE-REGISTERED. Written before the runner existed and before any number was
> produced.** Committed ahead of the measurement so the acceptance criteria cannot be fitted to
> the result afterwards. If a criterion below turns out to be wrong, it is struck in place with
> the reason, never edited away.

## The question, stated so it cannot quietly become a different one

**Is the engine GOOD at drafting** — against a field of several non-engine seats running
*different* sane styles, judged on the control's own ruler?

This is NOT what Gate 1 (`#284`) answered. Gate 1 proved the engine never produces a structural
failure across 34 formats — legality, not quality. A draft can be perfectly legal and badly
played. `#205` and `#245` asked the quality question and **disagree with each other** (1 of 68
seats on points vs 10 of 12), which `FREEZE_CHECKLIST.md` still carries as unresolved.

**The specific gap this closes.** Both prior runs put the engine against ONE uniform control in
every other seat. A homogeneous field is unrealistic, and it is the same artifact `#206` named
when it found the simulated chairs producing twelve straight QBs in round one. A field of one
policy is one opponent copied eleven times, not a league.

## What is reused, not rebuilt (#126)

`run_roster_proof.py` — its pool restriction (rule 2), production pricing on every arm (rule 3),
`set_league_format` per format (rule 4), absence counted separately from zero (rule 5), the two
rulers (rule 7), the shared lineup solve, and the seat-control discipline. Imported, not copied.
**Its control already drafts from the FULL undrafted pool**, which is the property that makes it
a fair control; `evidence/survival_calibration/calibrate.py`'s policies do NOT have that property
(they choose from `build_snapshot`'s narrowed shortlist) and are therefore NOT reused here.

## The styles, and why each is grounded rather than invented

Every style drafts from the **full undrafted pool**, is deterministic and seedless, and is
something a person would actually do.

| style | rule | grounding |
|---|---|---|
| `points_need` | best projection at an unmet starting slot, else best projection | the incumbent control from `run_roster_proof`; kept so this run is comparable to `#205`/`#245` |
| `adp` | best real market ADP (`adp_dd_ppr`), unmet-starter floor | **market consensus, not my invention** — the single most common real behaviour |
| `need_first` | fill every required starting slot before any depth, then projection | the roster-construction-first manager |
| `run_follower` | take the position just taken, unmet-starter floor | positional-run herd behaviour, which real drafts visibly exhibit |

**`adp` gets the same unmet-starter floor as the incumbent control, deliberately.** Pure ADP is
PPR-shaped and would under-draft QBs in superflex; a real ADP drafter still checks they have a
starter. Recorded as a CHOICE, not an oversight.

**The `18000.0` ADP sentinel is excluded.** 4,506 of 5,346 capture entries carry only an ADP
field, frequently that "undrafted" marker. Ranking on it would make undrafted players look elite.

## THE ANTI-STRAWMAN GATE — mechanical, not a judgment call

`run_roster_proof`'s rule 6 was earned the hard way: a projection-only control took **24
consecutive QBs** in a 1QB league, the engine "won" 12 of 12 by +503%, and the number meant
nothing. **A baseline nobody would ever play is a strawman and beating it is not evidence.**

Every style must therefore pass this gate BEFORE its results count:

> In an **all-same-style league** (that style in all 12 seats, no engine), every seat must fill
> **100% of its starting slots**.

A style that cannot field a legal lineup against itself is excluded from the measurement, and its
exclusion is REPORTED rather than silently dropped. This is derived from the roster's own slot
list, so it is a mechanical admission test, not my opinion about what is sane.

## Seat control — unchanged from the harness being extended

The engine holds **exactly one seat per run**, and the format runs **once per seat**, so the
engine holds every seat exactly once. Draft position is worth more than anything the engine does;
a comparison that does not control for it measures the snake. Non-engine seats are assigned
styles deterministically by cycling, and `style_by_seat` is reported for every run.

> This also settles the seat-mix question I had put to the owner. I proposed "3 engine seats, 9
> control" before reading the harness. That was **wrong** — it breaks the one-engine-seat-per-run
> discipline that makes seat control work, and it would have made this run non-comparable to
> `#205`/`#245`. One engine seat, cycled through all of them, is correct.

## Acceptance criteria, fixed in advance

1. **PRIMARY — the `points` ruler.** The engine's win rate against the mean of the styled seats
   it actually sat against. This is the strong claim: *the engine beat the field at the field's
   own game.*
2. **`cdme` is reported and is a TAUTOLOGY.** The engine maximises approximately `cdme`; a win
   there carries no information by construction and must be labelled as such. The two rulers
   correlate at only r=0.241, so they are different questions, not two views of one.
3. **NO SINGLE VERDICT IS EMITTED.** Both rulers, side by side, always — the same refusal the
   harness being extended already makes.
4. **PER-STYLE BREAKDOWN IS REQUIRED.** "The engine beat the field" is far less informative than
   which styles it beat and which it lost to. An aggregate that hides a loss to one style is the
   result hiding its own most interesting part.
5. **NON-VACUITY.** Report `n` for every rate, the pool size, and the styles actually admitted.
   A rate over an empty set is not a rate.

## What this run will NOT do

**No engine constant will be tuned on this result, in either direction.** `#56` forbids
calibrating a constant, and the capture LIMITS forbid fitting to one league. If the engine loses,
that is a FINDING to register, not a trigger to adjust a number until it wins. Recorded here, in
advance, because the temptation arrives only after the numbers do.

## A byproduct, deliberately captured

Picks are recorded **by round**, which yields the round-1 positional composition for free. That
bears directly on `#184`'s explicit reopen trigger — *"`#206` resolving in a way that changes
`#177`'s numbers"* — whose premise is that the simulated chairs behave unrealistically by taking
twelve straight QBs in round one. This run either reproduces that artifact or it does not, at no
extra cost.
