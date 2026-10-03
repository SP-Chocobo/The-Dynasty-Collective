# Adversarial review, set B (fableB), by Sonnet

Evidence: all 16 PNGs in `_shots/` read. I re-rendered all 12 variant×state combinations at 1440×900 and measured type size and contrast. I generated the prose for 10 to 12 different players per state by clicking through V1 and V4, and checked the cliff and bpa claims against `states.json`.

## What passed (one line each)

- The contract mostly holds.
  - No `0.0` depth digit appears anywhere on a default render.
  - Exactly three rows (Vele 7.1, Concepcion 7.1, Mason 7.2) show depth at `late`, and none show it at `early` or `mid`.
  - The cliff neighbour really is bpa-ordered. McMillan→McLaurin is 3.24 and Allen→Burrow is 3.44, both matching the payload.
  - No variant re-bases the negative scale.
  - Nothing needs an LLM.
- Minimum resident type is 12.0px, so round 1's 9.9px failure is fixed.
- Position slots are stable in lineup order in V2, V3's sheet and V4's strip. The shifting cost ordering therefore never reorders anything under the drafter.

## 1. Verdict per variant

**V4 Four cells: the only one that survives as a base.**
- It is the only variant a drafter could read in 30 seconds. It has four labelled areas, the largest type in the set, and a four-cell position strip. At `late` it is calm and legible.
- It still carries the set's shared defects, listed in section 2.
- Its own weak spots:
  - The strip's loudest numbers are the amber forfeit costs. That puts a cross-position forfeit ranking (`most` / `least`) in the persistent layer.
  - WHO and WHY repeat each other: the rival appears twice, the pick count appears twice, and 5.5 appears four times on one `mid` screen.
  - At `late` the WHY cell is half empty.

**V1 Ledger: salvageable parts, not a concept.**
- It has the most text per square inch of any non-trio variant.
- Its rail's YOUR NEXT box is clipped at the right edge in `mid` and `late`, even though the rationale says it is "anchored at the right edge".
- Its INSTEAD heading, "ALSO DEFENSIBLE, AT WHAT COST", is false for most of the rows under it (finding 3).
- The `late` screen contradicts itself (finding 6).
- The side list truncates names (`K. Conce…`, `T. Lawren…`, `T. Hocke…`) while 150px of the main column sits empty.

**V2 Doors: kill.**
- It is the most visibly broken at `late`. Three of four doors hold one name each inside fixed-height boxes about 70% empty.
- Its "across" cells are 5-line, 12px sentences that nobody will parse on a clock.
- The pool strip is cut mid-row at the bottom in every state. At `late` the 7th, last candidate (Hockenson) is half-sliced.
- At `early` the WR door's "THEN, BY VALUE" row is sliced in half by the cell below it, and the TE door's row is fully hidden. I confirmed this in a zoomed crop. The rationale says "no clipped region", which is false.
- The persistent forfeit headline lives here: `skip now: about 48.1 · most` in orange on a door that is not the board's first (finding 2).

**V3 Trio: densest, kill the grid, keep one thing (section 3).**
- At `late` it has about 7,500 characters on screen, 62% more than at `early`. The board has the least to say and the screen says the most.
- A six-row grid, each row with a two-tier label ("Value to your roster / board's order", "Drop behind him / within his position"), is followed by three pairwise sentences of 25 to 30 words each.
- The default A/B/C is just "best at the first three positions", the same trio as the strip. Changing it costs several clicks on a 24-row pool.
- Rail:
  - Ticks read `R7 R8 R9 R10…`, which means roster numbers but looks like round numbers.
  - It reads as a row of small boxes with labels, as the rationale admits.

## 2. Findings, most severe first

### F1. "Order" is the forfeit ranking that §16a measured as a loser, relabelled and given equal billing (all four; V3 and V4 worst)

**What is wrong.**
- `compare()` sets `orderEdge = forfeit[B.pos] − forfeit[A.pos]`.
  - That is exactly the `acting_now_value` difference, the ordering that lost 6.09% of lineup points (§16a). ADJ §1 says it may inform and may not decide.
- The surface renders it as "+9.9 order A. Brown first" next to "+9.8 value J. Taylor" with an orange SPLIT. The footer defines it as "order is which to take first".
  - That is deciding language.
  - Nowhere does the surface say this ordering has a measured record.
- The persistent layers rank positions on it (`most` / `least`):
  - V2 door frames.
  - V4 strip.
  - V1 and V4 WHY: "the most of any position here".
- ADJ §1's actual defect, "a reader sees the biggest number in the RB lane and the pick in the WR lane", is back. In the V4 `early` strip, the loudest amber figure is WR 48.1 `most`, while the subject is the RB.

**Why it hurts.** The drafter is nudged from J. Taylor toward St. Brown by a number the owner's own measurements say should not steer.

**Fixed when:** forfeit appears only as "if you wait, this position costs X". It is never named an order and never gets a `first by` leader. No cross-position `most` / `least` ranking appears in a resident layer.

### F2. SPLIT is a sign test with no magnitude, and "both defensible" is therefore unearned (V1, V3, V4 shown; V2's across cells too)

**What is wrong.**
- Pairwise labelling is binary: if the forfeit-order leader differs from the value leader, the pair is SPLIT, whatever the sizes.
- Examples:
  - V4 `mid`, subject Dowdle (value 37.9): McMillan is +14.6 on value and Dowdle +2.2 on "order". That prints SPLIT, "either pick is defensible". Allen is +10.0 on value and "Etienne first" by 6.1, also SPLIT.
  - V3 `late` default screenshot, B·C: "order favours J. Mason first by 1.0; value favours T. Lawrence by 7.3 — SPLIT — BOTH DEFENSIBLE".
  - V4 `late`, Hockenson (−53.5) against Lawrence: value +17.1, order +3.3, SPLIT.

**Why it hurts.**
- The owner said not taking #1 is not inherently wrong. He did not say anything within a 14.6-point value gap is.
- This swings from "frames disagreement as error" to "frames anything as fine", and both are overclaims about a statistical tie.

**Fixed when:** SPLIT is shown only when the two edges are of comparable size, using a rule the surface can state. Otherwise the pair shows both numbers with no verdict word.

### F3. V1's heading "INSTEAD — ALSO DEFENSIBLE, AT WHAT COST" sits over rows that both measures say are worse

**What is wrong.**
- V1 `late`: Lawrence and Mason are tagged AGREE, meaning value and order both favour Vele. Mason is −43.7, which is 9.1 behind. The heading still says "also defensible".
- V4 uses a neutral heading, "Instead, at another position", and V3 gates the phrase on SPLIT.
- V4 `late` also lists Hockenson (−53.5, +18.9 behind) as an alternative with AGREE.

**Why it hurts.** An unconditional endorsement of every row from the list is a false claim.

**Fixed when:** the heading is neutral, or each row earns "defensible" only through a stated test.

### F4. At `late` nothing explains the negatives, and every variant headlines the level (all four)

**What is wrong.**
- V1 and V4 headline a 30px "−34.6 VALUE TO YOUR ROSTER". V2 and V3 show it in a bold column, and V4's strip shows −36.4 and −53.5.
- The only help is one row, "Bench · your starters are set".
- No variant says "your lineup is full; every name left is bench depth, so every value is below zero".
- The gap is the real signal at `late` (0.2, 1.8, 9.1, 18.9), and it is the small gray element in V2's and V3's pool rows and in V1's list.
  - V1's and V4's alternatives rows do promote it, as bold "+0.2 value D. Vele".
- The `late` state is also self-contradictory about urgency.
  - The headline says nothing helps (−34.6).
  - Green ▲ glyphs, which the legend reads as "take now", sit on "depth insurance measured at 7.1" and "skip receivers now costs 9.4 — the most of any position".
  - That is a bench piece with a full lineup.

**Fixed when:** at `late` the subject's header shows the gap to the next as primary and the level as secondary (not re-based), with one plain sentence on why values are below zero. No ▲ sits on a cost for a player who won't start.

### F5. Position-level facts are printed as per-player reasons, so "why" differs only in a few sentences (V1, V2, V4; same core in V3)

**What is wrong.**
- I dumped the WHY for 10 to 12 players per state.
  - "Skip receivers now and it costs about 5.5 by #54" is verbatim identical for McMillan, McLaurin, Williams, Burden and Watson.
  - "the most of any position here" is verbatim identical for every RB at `mid` and every WR at `early`.
  - "The board sees a run on running backs: 4 of the last six picks" appears under Dowdle (5th RB, −11.9 behind the best), with the same green ▲ it has under Judkins.
- The player-specific content is a rank sentence, a cliff sentence naming the neighbour, and sometimes a horizon. That is real but thin: McLaurin versus Williams versus Watson differ mostly in a name and a decimal.
- Position facts at least do not differ by decimals alone. Within a position the explanations still collapse to a few templates.

**Fixed when:** position facts appear once, in the position layer. A player's WHY holds only what differs from his neighbours.

### F6. The `late` board contradicts itself in prose (V1 shown; V2, V3, V4 share the sentences)

**What is wrong.**
- V1 `late`, WHY: "the last receiver this board rates; the drop behind him (a sharp drop, 4.2) is to a player below this list".
- On the same screen, IF YOU WAIT says "nobody rated behind him on this board".
- Both are the same fact, and they are incoherent. A "last receiver" cannot have a player below him.
- The same sentence is printed for Vele, Mason and Hockenson, three of the seven `late` candidates.
- Concepcion appears on the same V1 screen as "next WR · 0.1 no cliff between".
  - In bpa order Concepcion (−7.93) is ahead of Vele (−7.99), so Vele is last and Concepcion is not behind him.
  - Value order and measured order are mixed on one screen without saying which is which. The "next WR" label is wrong in the order the cliff was measured.
- In V1's "the working" at `late`, the engine's read says "preferred" for Vele while the chip beside him says "a tie with K. Concepcion and T. Lawrence".

**Fixed when:** each sentence names one ordering and the screen never labels the same player both "next" and "ahead".

### F7. Cliff tier words contradict the raw numbers printed beside them (V2 `mid` visibly, V3 `mid`, V1)

**What is wrong.**
- V2 `mid` shows QB door "No cliff behind him: J. Burrow is 3.4 lower" next to WR door "sharp drop · 3.2".
  - V3 `mid` has "3.2 sharp drop" next to "3.4 no cliff" in adjacent columns.
- The engine tiers are correct. Allen is LOW because the typical QB step is 3.33, and McMillan is HIGH because the typical WR step is 0.62.
- The surface prints the two raw gaps without saying the tier is relative to the position. This is ADJ §3's cross-position trap in disguise: the reader compares the raw numbers and sees a bug.
- At `early`, "sharp drop" is on about 17 of 24 pool rows. It carries 2.3 (Lamb) and 38.5 (Chase) as the same word. It discriminates nothing.

**Fixed when:** the tier word stands alone, or reads "steep for a receiver". No raw gap is printed beside a tier word from a different position.

### F8. ▲ / ▽ is a legend that does not mean what it says, and it is on every variant

**What is wrong.**
- The legend reads "▲ take now ▽ wait · context".
- In the WHY rows the glyphs are used as pro/con of the player:
  - ▽ "Second receiver on the board, 4.6 behind".
  - ▽ "The dynasty horizon takes 2.7 of his value".
  - ▲ "Depth insurance measured at 7.1".
  - ▲ "Roster 7 … about 3% to take him before #19".
- A 3% rival is not a reason to act now.
- The drafter has to learn a legend, then discover the legend does not hold.

**Fixed when:** the glyphs are removed, or each means one thing and is only used for that.

### F9. Dead rows and doc-speak on the product surface (V1, V4 most)

**What is wrong.**
- "Chance he is still there at #54 — WITHHELD" is a purple-chip row on every subject, in V1 and V4. It carries no information and reads as a gap in the product.
  - Withheld is not missing, but it does not need a row to say so.
- "Picks before you choose again 12" repeats the clock bar printed one inch above (V1, V4).
- Explanations of the design are printed on the surface:
  - "the span is one marked count, not 12 empty boxes" (V1 rail caption).
  - "Rows appear only where they can differ" (V3, top-left cell).
  - "wait costs inform the order, never rank it" and "the drop is the engine's own, measured within WR" (V4, in every cell footer).
  - "D. Vele is the open door's best and the board's first by value. Each closed door shows…" (V2, across).
- "Engine" appears 1 to 3 times per screen: "the rival the engine names for him", "the engine judged it immaterial". That is implementation language the brief bans.
- The cross-position sentence is hard to parse: "J. Taylor now, receiver at #19: 48.1 · A. Brown now, running back at #19: 38.2". It reads as if Taylor were a receiver.

**Fixed when:** every footnote that explains the design to the designer is gone. The rest is rephrased as "If you take X now, Y's position will cost about N at #19."

### F10. Text volume and legibility are still high, and `late` is not lighter than `mid`

**What is wrong.**
- On screen at 1440×900, resident text ranges from 3,600 to 7,500 characters.
  - V4 is lowest at about 3,700 to 4,300.
  - V3 `late` is 7,490.
  - V1 `late` is 7,113.
- 70 to 92% of characters are set below 13.5px. For V1 and V3 at `late`, 36 to 37% are under 12.5px.
  - V4 is the best at 10 to 12% under 12.5px.
- 19 to 41% of visible characters are under 4.5:1 contrast. V2 and V4 have no rail and still land at 19 to 26% and 20 to 23%.
- Seven candidates should mean less to read. Here the board has less to say and the screens say more.

**Fixed when:** `late` carries fewer words than `mid`, and body text is at least 13px at 4.5:1.

### F11. Smaller items

- Neighbour rule inconsistent. In V4, "INSTEAD AT HIS POSITION" shows the next two worse players for Etienne (Irving, Swift) and omits the better Judkins. For Dowdle it shows Henderson (worse) and Judkins (best).
- V2's door frame says "D. Prescott · no slot", which reads as "no slot for QB". It means "no open slot".
- The `time_horizon` number saturates at −10.0 for Mason and Dowdle and is shown as a measured quantity.
- "The working" at `mid` prints "47.8 + 4.7", and at `late` "−8.0 + 0.0". The `0.0` is a real zero, not a depth non-measurement, and it is behind a gesture, so I do not count it as a violation.
- Avatar initials collide with position tags: Travis Etienne reads "TE".
- V3's rail ticks `R7 R8…` have no roster names and no explanation.

## 3. The one idea worth keeping

**V4's strip of four stable-order cells (slot state · best name · value), lit for the subject's position, with the best name as the click target.**
- It is the only persistent position layer that survives the QB→RB→WR→TE cost reordering with zero re-sorting, and it takes 52px.
- Keep it with forfeit demoted and no `most` / `least`.

Runner-up, from V3: lettering the roster slots A / B / C, so the drafter sees which slot each candidate would fill. At `mid` the three land in WR2, RB2 and QB, which draws the position decision itself.

## 4. What the set gets wrong as a whole

1. **The "order" axis.** The set invented a second ranking, the forfeit difference, and gave it parity with the engine's value ranking. ADJ §6 asked for the subtraction. It did not ask for a ranking with a leader, a gold SPLIT, and the word "defensible" attached.
2. **Resident detail.** Every variant prints 3,600+ characters. The owner said clean, not complete.
3. **Late was designed as a rendering problem, not a meaning problem.** Variants were adapted to 7 names but the negative level is still the headline, and none says why.
4. **Per-player reasons that are not per-player.** The WHY sentences for same-position players are the same sentence with different decimals.
5. **Self-referential copy.** The surfaces explain their own rules to the user, which is the clearest sign they are still defending their logic to a reviewer.
6. **The rationale's "verified" is wrong in checkable ways.**
   - V2's clipping is plainly visible at `early`.
   - V1's rail clips YOUR NEXT.
   - V2's pool is cut at the bottom.
   - The rationale says "every PNG was looked at". These defects are all in the PNGs.
