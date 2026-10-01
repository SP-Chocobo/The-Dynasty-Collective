# One slot, one alternative — measured. RIGHT ABOUT THE SLOT, WRONG ABOUT THE MAGNITUDE.

`run_216_shared_slot_probe.py`, 18 drafts, one process per format, one variable toggled
(`draft_room.shared_slot_alternatives` patched to `{}` for the SELF arm), both anchor caches
dropped at every arm boundary. Gates pre-registered at `fc5ca5d`, before the change existed.

**This is the pre-registration's own "partial success" case, verbatim: J2 passes and J3 fails.
So it is reported as exactly that and NOT called a fix.**

| format | seat | SELF (QB RB WR TE) | SHARED | band distance | lineup | engine−control asset |
|---|---|---|---|---|---|---|
| 12T_ppr | 1 | 2 2 7 3 | **2 4 7 1** | 4.46 → **2.26** | 2296 → **2332** (+36) | +115 → +137 |
| 12T_ppr | 6 | 1 2 8 3 | **1 3 8 2** | 5.96 → **3.96** | 2239 → 2235 (−3) | +135 → +197 |
| 12T_ppr | 12 | 1 4 8 1 | 1 3 8 2 | 3.76 → 3.96 | 2209 → **2221** (+11) | −13 → **+16** |
| 12T_ppr_SF | 1 | 2 3 8 2 | 2 2 10 1 | 4.73 → 8.61 | 2592 → 2549 (−43) | +115 → **−63 REVERSAL** |
| 12T_ppr_SF | 6 | 2 2 8 3 | **2 3 8 2** | 6.73 → **4.73** | 2520 → 2487 (−33) | −15 → −19 |
| 12T_ppr_SF | 12 | 2 4 7 2 | 2 5 6 2 | 2.73 → **2.67** | 2442 → 2436 (−6) | −57 → −17 |
| owner's | 1 | 2 6 6 **0** | 4 6 3 **1** | 6.36 → **6.26** | 2562 → 2549 (−13) | +174 → +262 |
| owner's | 6 | 2 6 6 **0** | **3 5 4 2** | 6.36 → **2.48** | 2525 → 2518 (−6) | +237 → +159 |
| owner's | 12 | 2 6 6 **0** | 3 6 4 **1** | 6.36 → **4.48** | 2564 → 2505 (−60) | +148 → **−46 REVERSAL** |

## The gates

| gate | verdict | evidence |
|---|---|---|
| **J1** dedicated slots untouched | **PASS** | Unit-proven: `adjustment` is exactly 0.0 for every position with an open dedicated slot, on every roster tried; omitting `slot_alternatives` reproduces the shipped numbers exactly. |
| **J2** owner's league fields a TE, and does not hoard one | **PASS, both halves** | **0 tight ends becomes 1 / 2 / 1**, at least one in 3 of 3, and **no seat above the band ceiling of 2**. This is the first and only change measured in this whole pass that clears the two-sided gate — the flex share failed it with a four-tight-end seat. |
| **J3** lineup points | **FAIL** | Rises in **2 of 9** (needed 6); total **21950 → 21832, −118** (needed a rise). Systematic, not noise: 7 of 9 seats down. |
| **J4** legality survives | **PASS** | `forced` 0 and `unfillable` empty in 18 of 18, both arms. |
| **J5** the owner's ordering | **FAIL in one format** | 12T_ppr **1/3 → 3/3**; 12T_ppr_SF **2/3 → 3/3**; owner's league 3/3 → 1/3 on the de-facto-receiver reading — and the two failures there are **RB-heaviness, not tight ends** (RB 6 against a band of 3.76 while WR falls to 3-4 against 5.06). |
| **J6** the derived band | **PASS** | Closer in **7 of 9** seats, and not worse in all three of any one format. |
| **J7** no new constant | **PASS** | One `max` over levels the board already computes. |
| **J8** suite | running at time of writing; 9 tests here, mutation pass pending |
| **J9** asset ruler | **FAIL** | **Two new reversals** (12T_ppr_SF seat 1, owner's seat 12) that the displacement-only arm did not carry. |
| **J10** the quarterback untouched | **VIOLATED, and the reason is legitimate** | QB counts move 2 → 3/4 in the owner's league. The SUPER_FLEX phantom is `max` over everything it admits, which is the QB level, so non-quarterbacks competing for a superflex are now priced against a quarterback's alternative and lose it. That is arguably correct — a superflex is a quarterback's slot — but it is the term reaching further than the gate allowed, and it is recorded as a violation rather than reasoned away. `bpa` itself is unchanged; what moved is who wins the slot. |

## The verdict, and why it is not "ship it"

**Right about the slot.** The construction is sound and J1/J2/J6 say so: at one open flex the engine
now prices every eligible position against one alternative instead of three different ones, the
owner's league fields tight ends for the first time without hoarding them, and seven of nine
rosters move toward the band. In both lab formats the owner's ordering goes to 3/3.

**Wrong about the magnitude.** −118 lineup points across nine seats is 0.5%, but it is systematic
(7 of 9 down), and two seats reverse on the asset ruler. A change that is only correcting a
mis-stated alternative should not cost points in seven of nine seats. **Something downstream is
now double-counting**, and shipping before finding it would be shipping a trade I cannot name.

**So it is NOT wired.** `board_slot_alternatives` is the seam and returns `{}`, so every
phantom keeps the candidate's own positional level and every board is byte-identical to the
shipped one. `shared_slot_alternatives` stays beside it — correct, tested, measured — and the
decision waits on the measurement named below.

## The mechanism of the −118 is NOT known, and my first hypothesis is already dead

I reached for one immediately: `need_bonus` still awards a per-flex-SHARE bonus keyed to the
candidate's OWN position, so under the shared alternative it would be paying twice for a slot
`displacement_adj` now prices. **Its own arithmetic kills it before any measurement.** That term is
`NEED_BONUS_PER_FLEX_SHARE * min(flex_remaining, 1)` with the constant at **1.0** — at most a
single point, against a 118-point swing. It cannot be the cause. Recorded rather than deleted,
because reaching for a mechanism before checking its magnitude is the same move that produced five
withdrawn diagnoses on this item, and this time the check happened first.

What IS visible in the identity, stated as structure and not as a diagnosis:

    final_score = universal_value + need_bonus + eligibility_bonus + depth_exposure + displacement_adj

The three older team-specific terms are each capped at 12.0. `displacement_adj` is uncapped, and
the shared alternative makes it far larger — −140 on a running back in the worked example in
`test_216_shared_slot`, against a ±12 ceiling on everything else. So the change does not merely
correct the term, it **changes which term decides the ordering**. Whether that is the cause of the
lineup cost, and whether it is right, is the open question. It is NOT answered here and no claim
about it belongs anywhere until an ablation produces the number.

The measurement that would settle it: hold the shared alternative on and ablate the three capped
terms one at a time, against the same 18 drafts. That is the named next step.

## A probe defect in the PREVIOUS pass, found while reading these numbers

The flex-share probe's `reference_values` ruler was built OUTSIDE its arm patch, so both arms were
scored on a ruler computed with the fielded anchor ACTIVE while the EVEN arm drafted with it off —
`#204`'s "the ruler and the draft must be priced the same way", in my own instrument. The
engine-vs-control reversal test and the EVEN-vs-FIELDED deltas both used one ruler for both arms,
so **#219's conclusions stand**; what does not survive is comparing that run's absolute `cdme`
numbers against any other run's. This probe is clean on that point — `universal_value` does not
contain `displacement_adj`, so its ruler matches both of its arms.
