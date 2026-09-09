# The derived flex share, measured against its pre-registered gates: REJECTED, NOT SHIPPED

Instrument: `run_216_flexshare_draft_probe.py`, 18 drafts, one process per format, one variable
toggled (`draft_room.board_flex_share` patched to the measurement for the FIELDED arm, untouched
for the EVEN arm), both anchor caches dropped at every arm boundary. Gates pre-registered at
86efdce, BEFORE the change existed. Base: Fable's `displacement_adj` fix.

**Verdict: four of nine gates fail. The change is rejected by its own criteria and is NOT
wired.** `fielded_flex_occupancy` stays as a tested instrument behind `board_flex_share`, which
returns None, so every board is byte-identical to the even split. See that function's comment.

## The 18 drafts

| format | seat | arm | QB RB WR TE | order | lineup | vs ctrl | cdme | vs ctrl |
|---|---|---|---|---|---|---|---|---|
| 12T_ppr | 1 | EVEN | 2 2 7 3 | F/F | 2296 | +63 | 417.0 | +143 |
| 12T_ppr | 1 | FIELDED | 2 3 7 2 | **T/T** | **2334** | **+117** | **441.7** | **+187** |
| 12T_ppr | 6 | EVEN | 1 2 8 3 | F/F | 2239 | +51 | 357.6 | +197 |
| 12T_ppr | 6 | FIELDED | 1 4 6 3 | **T/T** | **2256** | **+92** | **372.3** | **+231** |
| 12T_ppr | 12 | EVEN | 1 4 8 1 | T/T | 2209 | −18 | 288.4 | **+3** |
| 12T_ppr | 12 | FIELDED | 1 4 7 2 | T/T | 2198 | −32 | 298.8 | **−28 REVERSAL** |
| 12T_ppr_SF | 1 | EVEN | 2 3 8 2 | T/T | 2592 | +62 | 563.3 | +112 |
| 12T_ppr_SF | 1 | FIELDED | 2 2 9 2 | **F**/T | 2565 | +22 | 541.9 | +89 |
| 12T_ppr_SF | 6 | EVEN | 2 2 8 3 | F/F | 2520 | +54 | 480.8 | +77 |
| 12T_ppr_SF | 6 | FIELDED | 2 3 8 2 | **T/T** | 2491 | +4 | 431.3 | +4 |
| 12T_ppr_SF | 12 | EVEN | 2 4 7 2 | T/T | 2442 | −105 | 366.7 | −138 |
| 12T_ppr_SF | 12 | FIELDED | 2 3 7 3 | **F**/T | **2476** | −57 | **411.8** | −78 |
| owner's | 1 | EVEN | 2 6 6 **0** | T/T | 2562 | +15 | 556.2 | −29 |
| owner's | 1 | FIELDED | 2 6 4 **2** | F/F | **2578** | +25 | 532.8 | −69 |
| owner's | 6 | EVEN | 2 6 6 **0** | T/T | 2525 | −8 | 508.6 | −28 |
| owner's | 6 | FIELDED | 2 3 5 **4** | F/F | **2532** | +1 | 493.5 | −34 |
| owner's | 12 | EVEN | 2 6 6 **0** | T/T | 2564 | +16 | 543.5 | −31 |
| owner's | 12 | FIELDED | 2 5 6 **1** | T/T | 2527 | −25 | 471.3 | −114 |

## The gates

| gate | verdict | evidence |
|---|---|---|
| **H1** the anchor lands where the instrument said | PASS, with a stated caveat | Live ranks 12T_ppr TE 20→12, WR 32→45, RB 32→27; owner's TE 9→17, RB 39→24, WR 39→43. Directionally exact; 1-3 ranks off the instrument's numbers because the board prices 256 players and `scoreable_pool` 481. Recorded, not smoothed. |
| **H2** owner's league fields a tight end, and does not hoard one | **FAIL** | The first half passes outright: 0 tight ends becomes **2, 4, 1** where his own roster carries 2. The second half fails: **seat 6 comes back with FOUR**, and the pre-registration names a four-tight-end seat as an over-correction and a failure. |
| **H3** lineup does not fall in any seat | **FAIL** | Falls in 4 of 9: 12T_ppr s12 −11, SF s1 −27, SF s6 −30, owner s12 −38. |
| **H4** legality survives | PASS | `forced` 0 and `unfillable` empty in 18 of 18 drafts, both arms. |
| **H5** ordering passes in no fewer seats | **FAIL as written**, see below | 12T_ppr 1/3 → 3/3; SF 2/3 → 1/3; owner's 3/3 → 1/3. |
| **H6** no new constant | PASS | The diff adds no numeric literal to the value path; `SUPER_FLEX_QB_SHARE` loses a consumer and gains no sibling. |
| **H7** no silent change to callers passing nothing | PASS | The even-split branch is byte-identical; 22 tests. |
| **H8** suite green | one RED canary | `test_the_premium_still_exceeds_one_terms_cap` — attributed in `rival_premium_attribution.md`, its cause is #216's fourth term, not repaired here, not edited. |
| **H9** asset ruler, reported not resolved | **FAIL** | One NEW reversal the displacement-only arm did not carry: 12T_ppr seat 12, +2.9 → −27.8. No other seat reverses in either direction. |

## H5 is failing on an instrument that rewards the defect

The ordering verdict is `WR >= RB > TE` on the full roster. In the owner's league the EVEN arm
scores 3/3 — **by drafting zero tight ends**, because `RB > TE` is trivially satisfied at TE 0.
His own roster carries two, and he said why before any of this was measured: *"with no TE slot,
but flex that can field them, the TE act as de-facto WR."* The optimal fielding of his league
uses 1.5 tight ends per team. So in a TE-slotless league the verdict as implemented cannot tell
a good roster from a roster with no tight ends at all, and it prefers the second.

That is a defect in the INSTRUMENT, recorded as one. It does not rescue the change: H2's ceiling
and H3 fail on their own terms.

## The derived band tells a different story, and both belong in the record

Distance to Fable's derived band (sum of |actual − target| over the four positions; the band is
the instrument that agrees with the owner's ordering and QB ceilings in all three formats):

| format | seat | EVEN | FIELDED | |
|---|---|---|---|---|
| 12T_ppr | 1 | 4.46 | **2.46** | closer |
| 12T_ppr | 6 | 5.96 | **2.20** | closer |
| 12T_ppr | 12 | 3.76 | **1.96** | closer |
| 12T_ppr_SF | 1 | **4.73** | 6.73 | further |
| 12T_ppr_SF | 6 | 6.73 | **4.73** | closer |
| 12T_ppr_SF | 12 | **2.73** | 4.73 | further |
| owner's | 1 | 6.36 | **4.48** | closer |
| owner's | 6 | 6.36 | **3.86** | closer |
| owner's | 12 | 6.36 | **4.36** | closer |

**Closer to the band in 7 of 9 seats**, and both misses are 12T_ppr_SF. Against the CONTROL the
fielded arm's lineup is better in 12T_ppr 3/3 and in the owner's league 2/3.

So the honest summary is not "it did nothing" and not "it worked". It is: **the derived share
moves eight of nine rosters toward the shape a person would build and one seat straight past
it**, at a cost in lineup points in four seats and one new asset reversal. That is not a repair;
it is evidence about what the anchor should be, which is #50.

## What is established, and what is not

**Established.** The even flex split is false. 24 FLEX slots go WR 20 / RB 4 / TE 0 with a
dedicated TE slot and TE 18 / WR 5 / RB 1 without; SUPER_FLEX goes to a quarterback 12 times out
of 12 against a hand-set 0.85. The direction holds at every league size from 8 to 16. This is
the strongest single piece of evidence yet that the replacement anchor is mis-specified, and it
explains #216 in BOTH of its observed directions from one derivation.

**Not established.** That replacing it with an optimal-league-wide-fielding share is the right
anchor. The measurement's counterfactual is a league that fields perfectly; the draft it has to
price is one where rivals do not, so it can over-state how deep a position will really be
consumed — which is the most plausible reading of the four-tight-end seat, and is exactly the
kind of thing #50 exists to settle rather than an implementer.

**A hypothesis for whoever continues, marked POST HOC and unmeasured:** every seat that got
worse is superflex, and superflex is the one format where the measurement also overrides
`SUPER_FLEX_QB_SHARE`. Whether the non-SUPER_FLEX half of the measurement passes the gates on
its own has NOT been run, and picking that variant because it is the one that survives would
need its own pre-registration written first.
