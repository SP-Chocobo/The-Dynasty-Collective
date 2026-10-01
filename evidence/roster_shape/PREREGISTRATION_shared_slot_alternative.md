# The shared-slot alternative — pre-registered acceptance criterion

Written BEFORE any line of the change exists and before any measurement of it. Implementer: Opus,
on the owner's delegation of the #50 calls ("proceed per your recommendation"). Base:
`worktree-agent-ab5e1af412aeb9182` @ 80088cc (Fable's `displacement_adj` + the flex-share
measurement, stranded).

## The defect, stated exactly

`lineup_optimizer.displacement_level` pre-fills EVERY starting slot with a phantom worth
`free_alternative` — the candidate's OWN positional replacement level. That is right for a
dedicated slot, whose only free alternative is a free player at that position. **It is wrong for
a FLEX**, where the free alternative is the best freely-available player among every position the
slot admits — the same slot, one alternative, whoever is competing for it.

The consequence is measured, in both directions, and is #216:

* **Owner's league (no dedicated TE slot, three flexes).** TE's own level sits at rank 9 (a good
  tight end, because the even split gives TE only 0.717 of a slot) and RB's at rank 39 (a poor
  one). At the SAME open flex the engine prices a tight end against a top-10 TE and a running
  back against RB39. Running backs win all three flexes and the seat fields **zero tight ends**
  where the owner's own roster carries two.
* **12T_ppr (one dedicated TE slot).** TE's level sits at rank 20, WR's at 32. A FOURTH tight end
  competing for a flex is priced against TE20 while the receiver beside him is priced against
  WR32 — the ~30-point half of the bias that survives the displacement term, because the term
  reports exactly 0.0 whenever the slot is merely open.

## What I intend to build (hypothesis, NOT yet measured)

One change, inside the existing term, introducing no new quantity and no constant:

    the phantom in slot s is worth   max over p in s.eligible of replacement_level(p)

instead of `free_alternative` for every slot. `free_alternative` keeps its meaning — it is what
the candidate's `bpa` was anchored on — so `adjustment = free_alternative - displaced` becomes
NEGATIVE exactly when a position can only reach slots whose real alternative is better than its
own positional anchor. Every level in that `max` is one the board already computes
(`point_replacement`); nothing new is derived and nothing is chosen.

`displacement_level` gains an optional `slot_alternatives` argument. Omitted, it behaves exactly
as today, so every existing caller and test is untouched and the rollout has a single seam.

**A stated consequence, so it is not discovered later as a surprise.** The current docstring says
the term "reduces to the league anchor exactly on an empty roster". That will no longer hold for
a position with NO dedicated slot: a tight end in a TE-less league reaches only shared slots, so
his alternative is the shared one from the first pick. That is the point of the change, not a
side effect, and the invariant is restated rather than quietly broken: **the term is exactly 0.0
for any position with an OPEN DEDICATED slot, on any roster.**

Rejected before measuring: moving the anchor globally (that was the flex share; it failed four of
nine gates at 86efdce and is stranded); a per-slot price at score time (a second ordering
authority, #155); any hand-set share or weight (#56).

## Gates. Fable's probes unedited, 3 seats x 3 formats = 18 drafts, one variable toggled

- **J1 — dedicated slots are untouched.** For every position with an open dedicated slot, on any
  roster, `adjustment` is exactly 0.0 and the row's `final_score` is byte-identical to the
  displacement-only arm. Unit-provable; if it fails the construction is wrong.
- **J2 — the owner's league fields a tight end, and does not hoard one.** At least one TE in no
  fewer than 2 of 3 seats (his own roster carries two), AND no seat above the derived band's
  ceiling of 2. **Two-sided on purpose: a four-tight-end seat is a FAILURE**, exactly as it was
  for the flex share.
- **J3 — lineup points.** Must RISE in at least 6 of the 9 seats and the total across all 9 must
  rise, against the displacement-only arm. Stated as a majority-plus-total rather than
  "never falls anywhere" because #219 showed a single seat can move on one pick's tie-break; that
  relaxation is written HERE, before the numbers, and is not available afterwards.
- **J4 — legality survives.** `feasibility_first` binds ZERO picks and no starting slot is
  unfillable, 18 of 18, both arms.
- **J5 — the owner's ordering.** `WR >= RB > TE` (using the de-facto-receiver reading where the
  rulebook says there is no dedicated TE slot) passes in no fewer seats than the
  displacement-only arm, in each of the three formats separately.
- **J6 — the derived band.** Closer to Fable's band (sum of |actual - target| over the four
  positions) in at least 6 of 9 seats, and NOT worse in all three seats of any one format.
- **J7 — no new constant.** No numeric literal enters the value path. If one turns out to be
  needed I stop and say so.
- **J8 — suite green**, mutation-checked with survivors recorded, and every test whose PREMISE
  this changes listed with the premise and why it no longer holds. `test_216_displacement`'s
  empty-roster invariant is expected to be one of them; it will be RESTATED, never deleted.
- **J9 — the asset ruler, reported.** `total` / `floored` / `starter`, engine-vs-engine and
  engine-vs-control. A NEW reversal against the control that the displacement-only arm did not
  already carry is a failure and is reported as one.
- **J10 — the quarterback is untouched.** This term cannot fix defect (b) and must not appear to.
  The best remaining QB's `bpa` at the states `run_216_qb_price_probe` records must be unchanged.
  If it moves, something is reaching further than it should.

## What makes me reject my own change

- J2 fails toward MORE tight ends than the band, or the owner's league still fields none -> the
  change missed in one direction or over-shot in the other -> rejected.
- J1 or J4 fails -> the construction is wrong -> rejected, not tuned.
- J7 fails -> stop.
- J3, J5 and J6 all failing -> rejected even if J2 passes: fixing one seat's composition while
  the lineups, the ordering and the band all move away is not a repair.

## What partial success looks like, and how it will be reported

- J2 passes and J3 fails: the roster is the right SHAPE and worth fewer points. Reported as
  exactly that, per seat, and NOT called a fix — that is the trade #50 exists to price, and it
  would mean the shared alternative is right about the slot and wrong about the magnitude.
- J1 passes but nothing else moves: the term is firing nowhere it did not already, which would
  contradict the whole trace above and would be reported as a contradiction of my own account.

## The thing I must not do

Five confident single-sentence diagnoses on this item have already been withdrawn. No claim about
what this change DOES belongs in any report, commit message or reply until a probe has produced
the number.
