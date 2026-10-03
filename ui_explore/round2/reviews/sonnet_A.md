# Adversarial review, set A (fableA) — Sonnet

Method: read all 12 state PNGs plus the extra shots, re-rendered all four variants in all three states at 1440x900, clicked through every candidate in v1 (55 subject-states) and dumped the prose, and recomputed the displayed numbers from `states.json`. Findings below are things I measured or saw, not things I took from RATIONALE.

## 1. Verdict per variant

**v1 Ledger.** Survives as the base, and only because the rest of the set is worse. The "Also on the table" rows (each alternative priced against the subject, with a caption that taking one is a choice) are the best delivery of who / why / what else / at what cost in the set. The rail is the only one that works with no explanation (named past, one span, YOU ARE UP, YOUR NEXT, nothing blank, all three states). But its "Why" block does not say why: it is one tautological sentence ("X is N ahead of Y in value, the board's order") plus a cost subtraction. For every non-leader it explains why the *leader* beats him. Late is handled best of the four, with an honest sentence, though it still headlines a 36px "−34.6".

**v2 Lanes.** Reject the layout. The stable-column answer to position-order instability is correct, and the side-by-side within-position table is real new value. But at `late` about 65–70% of the fold is dark and the variant explains none of it. It says nothing about why every number is negative (RATIONALE claims every variant does; v2 does not). It also deletes the ruled rail outright: no boxes, no names, no glowing own picks, no re-center, only a sentence in the clock line. The one interaction the variant depends on (switch lane) is a 12px dim "click to open QB" at the very bottom of each lane.

**v3 Trio.** Reject. It is the densest surface in the set: roughly 900–1,100 words and 390–440 numeric tokens on screen against about 470–600 words and 50–120 numbers for v1/v2/v4, with 55–80% of the text at 12–13px and about half of it in the dimmest ink. That is the round-1 failure again. The "one row that ranks, the rest rank nothing" idea is good. The surface then breaks its own rule (finding 8).

**v4 Doors.** Reject the structure. The doors are sorted by the wait-cost aid, the quantity that lost 6.09% of lineup points when it was used to order (§16a) and that ADJ §1 says may inform but never decide. The leftmost, first-read door is therefore not the engine's first on `early` or `mid`. At `late` the four doors are four giant negatives with no explanation, and the worst-valued name on the board (T.J. Hockenson, −53.5) takes the second slot.

## 2. Findings, most severe first

**F1. The value gap and the "wait cost favours him by X" line are printed as two separate, opposing numbers, but the second already contains the first. (v1 alternatives and Why; v2 lane leads; v3 wait-cost row; v4 door cards. Seen in `early` and `mid`; present in `late`.)**
- Algebra, checked against the data: `forfeit_a − forfeit_b ≡ (tav_a − tav_b) + (next_turn_b − next_turn_a)`.
- Early, Taylor vs St. Brown: 176.28 + 118.43 = 294.71 against 166.51 + 138.11 = 304.62, so St. Brown first wins the two-pick plan by **9.9 net**. That 9.9 is *after* Taylor's 9.8 value lead.
- The screen shows "−9.8 value · wait cost favours him first by 9.9" (v1 `early` alt row 1; v3 `early`: "Taylor first by 9.8" then "St. Brown → Taylor (by 9.9)"). Any reader nets them to about zero, which is wrong.
- Mid has the same shape: "−2.7 value · favours him by 2.2" is really Judkins +2.2 net, not McMillan +0.5.
- The reconcile sentence ("Value and wait cost point different ways") announces a disagreement and does not resolve it.
- Aggravating factor: v3's three-name "Judkins → McMillan → Allen" extends a quantity the engine measures only "by your next turn" into a three-turn sequence the engine never computed.
- Fixed means: one number per alternative, stated as a two-pick plan ("take A now and B next turn vs B now and A next turn: +9.9 for B-first"), with the value gap labelled as already inside it or not shown. No three-way sequencing.

**F2. v4 puts the forfeit ordering in the structural lead. (v4, all states.)**
- `early`: leftmost door is Receiver / St. Brown (the board's #2) with "wait cost favours him first by 9.9" in amber. The board's first, Taylor, is in door 2.
- `mid`: RB door first, McMillan in door 2.
- The "two orders disagree at this pick" banner, in right-aligned dim 12px, appears in **all three states** (I checked the three order pairs), so it is a permanent banner and carries no information.
- The order line asks the drafter to diff two sequences of four coloured chips. That is a legend by another name.
- Fixed means: doors ordered by the board (or fixed order), with wait cost as a per-door attribute.

**F3. `late` negativity is explained in v1 and v3 only. (v2, v4 `late`.)**
- Confirmed by text search of the rendered rooms: v2 and v4 contain no "negative" or "gaps" sentence anywhere. RATIONALE cross-cutting finding 2 says every variant adds one; two do not.
- v4 `late` leads each door with −34.6 / −53.5 / −43.7 / −36.4 at 20px+ and bold.
- v1 and v3 do state it, but v1 sets it in orange 12.8px under a 36px "−34.6", and v3 buries it in the second line of the gold box.
- The level is still the loudest number in every variant. In v1's board strip the level is bold white and the gap is small grey, which inverts "read the gaps".
- Credit: nobody re-bases the scale. v1's alternative rows ("−0.2, −1.8, −9.1, −18.9") make the gaps the biggest numbers in that section.
- Fixed means: the gap is the visual unit at `late`, and the sentence is present and legible in every variant.

**F4. Generated prose differs in decimals, not substance, wherever it is read most. (v1 Why, v1 `late`, v1 `early`.)**
- v1 across all three states: 55 subject-states collapse to about 20 templates after replacing numbers and names. Two of those templates cover 29 subjects.
- `late`: Lawrence, Darnold and Murray receive the byte-identical second sentence ("Waiting on WR costs about 9.4… Vele first is the cheaper order by 8.6"). Only the value gap in sentence 1 moves.
- `early`: ten WRs get "wait cost favours X first by 9.9". Every sentence 1 ends in "— the board's order", which restates the rank as its own reason.
- The Why for the leader omits the one fact that actually separates him: Taylor's cliff is 37.8 (HIGH) against Achane at 0.28 (LOW). It is absent from v1's default `early` ledger and appears only if you click Achane. v2, v3 and v4 show it, because their within-position tables carry it.
- Within-position differentiation works in v2, v3 and v4 (cliff, horizon, injury, depth). Cross-position differentiation is one template per position pair.
- Fixed means: a Why sentence that names something specific to the subject (his own cliff, his slot), and for a non-leader the case *for* him, not the case for the leader.

**F5. Tier word and raw gap contradict each other in plain view. (v3 `mid` row, v1 `mid` strip, v2 `mid` lanes.)**
- `mid`, v3 "Drop behind him" row: "a sharp drop 3.2" (McMillan) next to "no cliff 3.4" (Allen). v1's strip lists Allen "no cliff (3.4)" above Etienne "a sharp drop (3.1)".
- v3's caption "not comparable across positions" is 12px dim under the row label.
- The tier is engine-correct (per-position typical gap), but printing the raw number beside it invites exactly the cross-position read ADJ §3 forbids.
- Also, in the `early` board 19 of 24 candidates carry HIGH, so "a sharp drop behind him" appears on about 80% of rows and stops discriminating. v2's RB lane at `early` repeats it on ten rows in a column.
- Fixed means: show the tier alone on the resident surface (or the gap alone within one position), not both across positions.

**F6. The governing sentences are in the faintest ink, and the colour says the opposite. (v1, v2, v3, v4.)**
- "Taking one of them is a choice, not an error" is a `.note`. The reconcile line is `.rule`. Both are `--dim` #776d5a at 12–12.8px on #1f1a11, a contrast of about 3.4:1 (below 4.5).
- Meanwhile every alternative's value gap is crimson (v1, v2, v4), so every option other than the first is red by default.
- At desk distance on a 60-second clock the reader gets red numbers and no legible caveat.
- Fixed means: the caveat is at body size and body contrast, and gaps are not red unless something is actually wrong.

**F7. `late` ignores the engine's own tie and substitutes an invented threshold. (all four.)**
- `forces` is `['cliff','tie']` for Vele and `['tie']` for Concepcion, and Lawrence is `['pure','tie']`. In the engine's bpa order Concepcion (−7.93) is ahead of Vele (−7.99).
- Yet v2 hangs a gold "board's first" badge on Vele and v4 a gold outline, on a 0.23 lead (0.7% of a −34.6 level).
- The only tie language in the set is `shared.js` line 168, a hand-picked 0.05 coin-flip threshold. It fires on exact ties (Allen / McLaurin at `mid`) and not on 0.2.
- Fixed means: use `tie` from the payload, and say in words that these two are level.

**F8. v3 contradicts its own organising claim and has several smaller defects. (v3, all states.)**
- The footer says "none of them ranks". The wait-cost row two inches above prints an ordered sequence ("St. Brown → Taylor", "Judkins → McMillan → Allen") that is a ranking.
- Slot colours collide with position colours: slot A is blue and Taylor's pill is RB green, B is green and St. Brown's pill is WR blue, C is orange and TE is orange (`early`).
- The compare pane overflows. Dynasty horizon and depth sit below the 900px fold in all three states (`late`: depth row is only reachable by scrolling; confirmed in a scrolled render).
- The "where he starts" row at `late` reads "bench / bench / bench" in full sentences. The depth row for Lawrence reads "a starter here has no cover…", which sounds like a roster alarm when it means "not measured".
- Rail: the left-edge past boxes are sliced mid-glyph ("lenry", "inson"). The orange-outlined between-boxes (mid R3, R3) have no legend at all. "R7" means Roster 7 here and Round 7 on the draft-board sheet.
- 24 rows × three A/B/C buttons is 72 controls in the pool column.

**F9. v2 `late` and the ruled rail. (v2.)**
- Four lanes holding 3/1/2/1 names leave most of the fold empty. RATIONALE admits it. The honest answer to "does this layout survive seven names" is no.
- The §1 RULED rail (boxes carrying the drafter's name, own picks glowing, re-center) is replaced by one sentence in the clock line. If the owner approved the experiment, that is fine, but the page should then say so. U1's "marks my next turn" is met in words only.
- Name truncation in the comparison table itself ("Jameson ..." at `mid`) and a row ending "TreVeyon Henderson NE · 2…".
- Lists are clipped mid-row at the fold (`early` WR and RB lanes), so scroll is implied without an affordance.

**F10. v4 states something untrue about the pool. (v4 `early` QB door, `mid` TE door.)**
- "The position is not gone; the board has no rated name at it." The candidate list is the top 24; QBs and TEs exist and are rated, and a QB appears in `late`'s 7. v2 says it correctly ("in the board's top 24").
- Also the neighbour fallback "to a player below this board" is printed whenever the neighbour is not reproduced. For Malik Nabers at `mid` it is false: the 11.08 gap lands on a player who is between Nabers and Adams in measured order but off the candidate list.

**F11. Rival markers imply a threat the data denies. (v1 rail ticks, v3 between-boxes.)**
- Ticks and outlines flag seats the engine "weighed": seat 7 at `early`, seats 3 and 5 at `mid`. The take probabilities behind them are 2.7%, 2.6% and 2.4%.
- RATIONALE says rival probabilities were removed from resident surfaces. Their only visible trace is a mark that reads as a warning.
- v1 explains it in 12px dim ("marked: the rivals the engine weighed"). v3 does not explain it at all.

**F12. The first appearance of a depth digit is unexplained and non-discriminating. (v2 `late` WR table, v3 `late`, v4 `late` WR door.)**
- "DEPTH INS. 7.1 / 7.1" is the only positive number on an all-negative board, labelled with an abbreviation, with no unit and identical for both players (7.08 and 7.08).
- Contract compliance is correct: digit only under `measured`, none shown elsewhere, no stray 0.0 in any state. That deserves a line of credit. But the digit as shown says nothing a drafter can act on.

## 3. The one idea worth keeping

v1's **"also on the table" rows**: one alternative per position, each priced against the subject in a single line, under a caption that taking any of them is a choice. Keep it at body size and body contrast, with the F1 fix so the line is one honest net number. Runner-up: the within-position table's plain admission that wait cost is identical inside a position ("Same position, same wait cost, it says nothing between them. What follows is what does."), shown in v3's same-position render.

## 4. What the set as a whole gets wrong

- **Every variant pre-selects, enlarges and gilds engine rank 1.** v1's default subject is the leader. v2's default lane and "board's first" badge sit on him. v3's A / B / C are ranks 1 / 2 / 3. v4's gold door is his. The caption says "not an error" while the layout is a podium.
- **Core derived arithmetic is misframed (F1)**, and the thing it is placed beside is a rank the engine itself calls a tie at `late`.
- **The per-player explanation does not exist where players are not different.** Cross-position, there is one sentence per position pair. Within a position the data is real, but at `late` the within-position differences are horizon −0.3 and depth 7.1 against 7.1, which is noise dressed as a table.
- **The owner's central sentence is in the dimmest ink at the smallest size.** "12px floor" is satisfied and the legibility is not: 40–80% of resident characters are under 13px in these renders.
- **RATIONALE claims that did not survive checking.** "Every variant adds the all-bench sentence" is false for v2 and v4. "The alternatives are priced, not graded" is contradicted by red on every alternative. The v1 numbers shot in `_shots/` is stale and still shows a "NOT PRICED" chip the current build no longer renders.
