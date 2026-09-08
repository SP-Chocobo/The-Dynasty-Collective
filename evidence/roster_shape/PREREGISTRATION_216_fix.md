# #216 fix — pre-registered acceptance criterion

Written BEFORE any measurement of any candidate fix (the only thing run so far on this branch
is the adversary's `test_the_board_is_not_the_projection_control` on unfixed code, to read its
failure body as the owner instructed; it passed, see the report). Implementer: Fable.
Base: `ui-authority-pass` @ 2f5f304. Battery: b66c051's three files, taken verbatim.

## What I intend to build (hypothesis, not yet measured)

A fourth team-specific term, derived from the shipped lineup optimizer and the replacement
levels the board already computes, with NO new constant:

    displacement_adj(position) = replacement_level(position) - own_replacement(position)   (<= 0)

where `own_replacement(position)` is the projected-points value of the weakest occupant a
player at that position would have to DISPLACE in MY optimal lineup, with every starting slot's
free alternative set to that position's league replacement level. When any slot the position
can fill is open (or held by someone below league replacement) the two levels coincide and the
term is exactly 0.0 -- the board is byte-identical to today's for that position. When every
slot he could fill is held by one of my players above league replacement, he is priced against
that player instead of against the league. Reduces to VOR exactly on an empty roster.

    team_acquisition_value = universal_value + need_bonus + eligibility_bonus + depth_exposure
                             + displacement_adj

`universal_value` stays team-agnostic (untouched). The QB half (defect b) is expected to be
reached by the same term only indirectly (surplus rows are deducted so the open QB slot wins
the comparison); whether that is sufficient is gate G2 below and is NOT assumed.

Rejected before measuring, with reasons in the report: RAW-MLV (an accidental raw-points
ruler); scaling need_bonus (no derivation; the cap does not bind); a lexicographic sort key
(breaks the display contract -- the room would show one order and rank another).

## Gates (measured with the battery's own instrument and my probe, 6 seats x 2 formats)

- **G1 -- the value board alone drafts a legal roster.** With `feasibility_first` disabled,
  every engine seat (1, 6, 12 in 12T_ppr and 12T_ppr_SF) finishes with every dedicated slot
  filled and a full starting lineup fillable by the shipped optimizer; with it enabled,
  `fills_required_slot` is True on ZERO of my picks and the composition equals the OFF arm's.
  (Battery class A + reviewer invariant 1.)
- **G2 -- the quarterback is priced, not forced.** In 1QB, at every one of my turns while my QB
  slot is unfilled, the best remaining QB's `final_score` is > 0; once filled, the best
  remaining QB's `final_score` is <= 0 UNLESS he out-projects my starter (then a positive price
  is an upgrade, which is correct, and I will report the case). The QB is taken at a pick where
  `fills_required_slot` is False.
- **G3 -- the lineup gets better, nowhere worse.** OFF-arm lineup points (optimizer over the
  season projections, the roster proof's ruler) >= CURRENT ON-arm lineup points in 6/6 seats.
  One seat lower = the fix is rejected outright.
- **G4 -- over-correction guards.** Battery class E passes unedited; additionally no 1QB seat
  opens with a QB (the projection control's signature); at least one seat still carries a second
  TE or a third RB taken by value (not by force) -- an engine that drafts exactly to slot counts
  has failed.
- **G5 -- no new constant.** The diff introduces no numeric literal into the value path. If a
  constant turns out to be needed, I stop and say so.
- **G6 -- replay gate.** In ONE process, with the new term switched off, the instrument
  reproduces the recorded #216 CURRENT sequences pick-for-pick (6/6 seats), and at every state
  of every arm the instrument's pick is `compute_draft_board`'s own first row after
  `_board_order`.
- **G7 -- the room.** The identity closes with the new term on every priced row; the term and
  its basis reach `CandidateSnapshot`, `serialize_candidate`, the JS sentence and the display
  contract; `test_216_room_integrity` (Chromium executed) passes unedited except the pin it
  tells the implementer to update.
- **G8 -- suite green** (~2650 tests). Every test whose PREMISE the fix changes is listed with
  the premise and the reason it no longer holds; none is deleted silently.

## What makes me reject my own fix

- G1 fails in any seat: the backstop still binds -> the fix did not fix the board. Reported as
  a finding, the term reverted or left off the sort.
- G3 fails in any seat: the term makes a lineup worse -> rejected, whatever G1 says.
- G4 fails: an over-correction -> rejected.
- G5 fails: -> stop, do not tune.
- Any battery E test fails and I cannot show with numbers that the TEST is wrong.

## What partial success looks like, and how it will be reported

- Starters fixed (G1-G3) but the bench still hoards (the most-drafted bench position count,
  backstop OFF, unchanged from today or still monotone with that position's replacement gap):
  reported as exactly that -- "starters fixed, shape not", with the counts per seat.
- `test_with_every_starter_filled_talent_still_orders_the_board` (E-5) fails because the term
  reorders a full roster on lineup improvement rather than on universal_value: I will NOT edit
  the test. I will report whether the reorder is on lineup points (defensible) or on noise, and
  leave the decision to the owner.
