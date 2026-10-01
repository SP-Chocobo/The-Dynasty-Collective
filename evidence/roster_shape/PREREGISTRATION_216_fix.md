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

## G9 -- ADDED BY THE OWNER MID-RUN, before it was measured

Added after G1-G8 had been measured (the tables in FIX_216_fable.md §2 existed) and BEFORE any
asset, age or horizon number was read. The concern: a lineup fix that sells off the dynasty
asset character. A SIGN TEST plus a reported delta; no threshold is derived or chosen.

- **G9a -- the asset ruler must survive.** `run_roster_proof`'s `cdme` ruler
  (`total_value` = sum of the pre-draft board's `universal_value` over the finished roster --
  what the roster is worth to OWN, the engine's own objective; #205 reports the engine winning
  it 68/68 against the control), per seat, both formats, term ON vs OFF, engine vs the same
  control seat. **A REVERSAL is rejection**: any seat the engine won before and loses after fails
  G9 outright, whatever the lineup gained. Magnitudes are reported for the owner (#50 holds the
  exchange rate); I do not resolve a lineup-vs-asset trade myself.
- **G9b -- age and horizon character.** Mean age (Sleeper's `age`, 5949 of 6595 players carry
  one) and mean `time_horizon_adj` (read off the chosen row at the state it was chosen) of the
  drafted roster, ON vs OFF, per seat. Systematically older or lower-horizon rosters under the
  fix are reported as win-now creep even if every other gate passes.
- Stated expectation, to be contradicted by the measurement if it disagrees: the term is <= 0,
  fires only on displacement, and leaves `universal_value` (which carries `time_horizon_adj`)
  untouched, so the asset result should be largely preserved. If it is not, that is the finding.
- The control's known defect (once its starting slots are covered it drafts best projection
  regardless of position -- three QBs in a 1QB league, five TEs on one seat) does not
  invalidate the asset COMPARISON, and is stated rather than presented as a sound control.

## SECOND PASS — roster shape. Pre-registered before any bench-ruler arm was measured

The owner's criterion, as relayed: the ordering `WR >= RB > TE`, a QB ceiling, a per-league
BAND derived from bench width, starting requirements, league size and pool depth, computed on
FIELDED LOAD (dedicated slots plus the flex share a position actually wins, read off the
optimizer) — a tendency over the roster as a whole, not a quota; at shallow bench depth
`RB == TE` is acceptable.

**What is scored, stated.** The FULL ROSTER (14 picks in 1QB, 15 in SF), because the owner's
own examples are full rosters and a 14-man roster carrying WR7 RB2 is thin at running back
whichever way it is counted. Scored a second way — bench only — where it changes a verdict.

**The band, derived (no literal enters it).** At the end of a draft every roster's optimal
lineup on the season projections is solved (`lineup_optimizer`, the flex assignments observed
rather than assumed). `share_p` = the league's fielded load at position p / the league's total
fielded starters. A seat's target total at p is `roster_size x share_p`; its bench target is
that minus its OWN fielded load at p (so a seat whose flexes are receivers is asked for fewer
bench receivers — the owner's refinement). The band is the integer neighbourhood of the
target (floor..ceil), and the ordering check compares targets, so `WR >= RB > TE` is DERIVED
per format from what the league actually fields and may disagree with the owner's ordering —
if it does, that is reported, not forced. The QB ceiling is the same quantity at QB: with one
QB slot per team `share_QB` is 1/8 of fielded load in this format, target 14 x 1/8 = 1.75, so
"at most one benched QB" falls out; superflex derives its own from how many SUPER_FLEX slots
quarterbacks actually win. Pool depth enters through the flexes: which positions win them is a
property of this pool's supply at those ranks. This band is an EVALUATION instrument; the
engine never reads it (a quota would be the over-correction the owner named).

**The regime the engine can detect exactly.** A board state is PURE-BENCH when no priced row
can crack my lineup: `max(bpa + displacement_adj) <= 0` over priced rows. In that state every
candidate is a bench candidate, so an ordering among them needs no exchange rate against
lineup points (there is nothing to exchange against) and the number shown can be a bench
number with its own basis. In any MIXED state the board stays as it is (lineup first). This is
a fact about the assignment, like #84's regimes, not a constant.

**Why a bench PRICE is not derivable, recorded before measuring so it is not re-derived.** A
bench body's expected contribution is (probability a starter he covers is out) x (his points
over what would otherwise fill in). The engine's own uniform "any one starter out" model
(depth_exposure) gives the second factor exactly via the optimizer and puts the first at
1/|starters| per starter — summed over the 5 of 8 fielded slots an RB can cover that is ~5/8
of his projection, starter-sized: measured on paper at 1QB seat 1 round 6 it prices a 200-point
bench RB at +125 against a 40-point lineup upgrade at +55, which is the raw-points regime the
E-guards forbid. Any smaller weight is an injury rate this repository does not have (#56). So
the second pass looks for an ORDERING inside the pure-bench regime, not a price across regimes.

**Arms (measured post hoc on the FIX_ON trajectories, one process; only an arm that passes is
implemented):**
- B0 today: distance to my lineup (`final_score` as shipped).
- B1 coverage: rank by the number of my fielded starters whose absence opens a slot the
  candidate can fill (optimizer, one-out, after re-optimisation), then points. Derived; encodes
  "bench follows fielded load" directly.
- B2 horizon: rank by `projected_points − horizon_floor(position)` (`waiting_cost`, already on
  every row) — value over the end-of-draft free alternative, the pool's own consumption model
  and the only quantity here that encodes "fewer useful running backs exist". CROSSES #48's
  observable-only ruling for this regime; if it wins, that is said loudly and the owner decides.
- B3 coverage x horizon: B1's coverable-load share times B2's margin.

**Enforcement constraint (owner, the handcuff).** No arm may cap a position's count: every arm
above is an ORDERING among bench candidates, and the band is an evaluation instrument the
engine never reads. A rule that made a correlated backup (a handcuff to a starter I own)
unbuyable for being the fourth running back would be a new defect; whether any arm can
suppress one, and under what roster conditions, is reported. Term inventory, answered from
code before measuring: no existing term can raise a player's value on the basis of a specific
teammate -- `team` is read only for identity resolution and emitted as a column; lineup rows
carry id/value/eligibility only; `eligibility_bonus` and `depth_exposure` are keyed to the
candidate's own eligibility and to positions, never to who else is owned.

**Gates.** The arm must (a) pass the ordering on the FULL roster in more seats than today
(3/6) with `WR >= RB` regressing nowhere; (b) leave G1, G3 (starters are untouched by
construction in the pure-bench regime — asserted, not assumed), G4, G6 and G7 intact; (c) add
no constant; (d) not collapse compositions to one template (report the spread across seats).
The QB's own 0.00 bpa is NOT touched by any arm (a bench ruler runs only after the QB slot is
filled); stated in the report either way. If no arm passes, the finding is "the bench shape is
not derivable without an exchange rate" and I stop.

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
