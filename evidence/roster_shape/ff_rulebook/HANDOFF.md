# #222 -- the engine's roster shape, measured against twelve real managers

Overnight pass, 2026-09-09. **No engine source was changed.** `git diff --name-only`
against the session start shows evidence and league captures only. Nothing can have
regressed; the full suite was not re-run because nothing it covers moved.

## The finding

A complete 12x26 startup on Fourth and Forever's real rulebook -- production engine on
every chair, real Sleeper universe (6,595), real season projections (5,346) scored under
this league's own settings -- against the same league's twelve real managers.

| | QB | RB | WR | **TE** |
|---|---|---|---|---|
| twelve real managers | 20.0% | 27.4% | 37.1% | **15.5%** |
| **the engine** | **10.3%** | **26.9%** | **30.4%** | **32.4%** |

**Two defects, and they are the same defect wearing two faces.**

1. **The engine drafts 101 tight ends out of 312 picks** -- more than double what a human
   takes. Every seat finishes with 5 to 12; humans took 3 to 6. The back half of the draft
   is half tight ends (50.0% and 47.4% in the third and fourth quarters).
2. **Nine of twelve seats finish with exactly two quarterbacks**, in a SUPERFLEX league
   where QB and SUPER_FLEX both start every week. Two is the starting requirement with zero
   backup. 10.3% against the humans' 20.0%.

Running backs are correct (26.9% against 27.4%). Receivers are UNDER-drafted, not over.

The unifying cause: **a body that cannot improve today's optimal lineup is priced at
nothing.** For quarterbacks that produces too few (a third QB can never be promoted, so it
is never worth taking). For tight ends it produces too many -- TE's own replacement level
collapses early, VOR measured against a collapsed level stays positive for every remaining
body, and the displacement correction is bounded by my own roster so it cannot claw the
credit back. This is #155 ("a replacement-level player prices at 0.00 tautologically")
surfacing as a live selection defect rather than a pricing curiosity.

## What I got wrong, and it matters for whoever picks this up

- **The WR over-allocation does not exist on the real rulebook.** I chased it all night
  because the 49-seat battery produced 48.9% WR. Those are mostly 1QB formats with other
  rosters and other scoring. Thirteenth withdrawal of the session.
- **FINDING_01 through FINDING_04 measured the wrong player universe** -- the 764-row vendor
  reconstruction rather than the 6,595-player capture. See `CORRECTION_wrong_universe.md`.
  All four are marked at the top; their mechanisms may survive re-measurement, none of
  their numbers may be quoted. Sixth fixture error of this class in this repo.
- **There is no supply shortfall.** The real board carries 1,119 priced rows against 312
  picks. My "32 picks with no priced player" was the wrong universe too.

## What is trustworthy

`FINDING_05_it_is_tight_ends.md` and `ff_draft.json` / `ff_draft.txt`. One draft, one
league, one seat order -- but measured end to end on the universe production uses, against
twelve real managers in that same league.

`data/league_captures/fourth_and_forever.json` -- scoring (4 of 6 tabs; K and DST are
uncaptured and this league rosters neither), the real 29-slot roster, starter demand
derived with the engine's own function, and six rulebook categories flagged as having no
stat data behind them.

## Next, in order

1. **Re-run FINDING_02/03/04's probes on the capture universe.** The mechanism they describe
   is the best lead on the TE half; their numbers are void. `build_ff_board.py` is already
   corrected and is the template.
2. **A second draft at a different seat order**, to separate "the engine does this" from
   "this seat order does this". One draft cannot.
3. **Only then** design the repair. The standing order is evidence before repair, and the
   evidence now names a target that is not the one this session started with.
4. Do NOT fit a tight-end penalty. The 15.5% belongs to twelve managers in one league and
   #56 forbids calibrating to it. The repair has to come from what a bench body is worth
   when no slot is at stake -- a question the engine currently answers with a number
   computed for a different question.

## Cost

Roughly two hours of engine time: two 312-pick drafts (the first was lost to an attribute
error in the reporting block after all 312 picks had run, which is #215 restated and is now
prevented by saving raw before any analysis), plus board builds and probes.
