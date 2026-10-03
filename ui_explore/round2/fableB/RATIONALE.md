# Fable B — round 2, synthesis — revised after ADJUDICATION_R2

Four variants, one shared core (`_core.css`, `_core.js`), one build (`_build.py` inlines
`states.json` verbatim), three states each (`#early` / `#mid` / `#late`, or the buttons in the top
bar). Sources `v*_src.html` stay beside the builds.

**Verification (all twelve variant×state renders at 1440×900, Chromium):** `node --check` on
every built script; `_shot.py` asserts no page scroll, no self-clipping, no console errors, minimum
resident font 12.0px, **no text overflow in any text leaf (truncated names count as failures), no
occlusion (every visible text element hit-tests to itself), and at `late` no list scrolls at all**;
`_interact.py` clicks through alternatives, doors, slots, sheets and state switches with zero
errors. The occlusion and overflow assertions are new this round — the previous probe could not see
either, which is how V2's `early` doors and V1's `late` names shipped broken. Every PNG in
`_shots/` was then read as an image.

| file | one-sentence hypothesis |
|---|---|
| `v1_ledger.html` | The round-1 Ledger's delivery survives being cut to **who · why · three alternatives, each with its cost · if you wait**, and the position layer only needs to appear when asked. |
| `v2_doors.html` | Across positions the honest 3-way **is** the position layer, so keep it resident in stable lineup order, open one door to its names, and let the wait be a count instead of a rail. |
| `v3_trio.html` | The drafter arrives with names in mind and wants three compared, not two — three slots, rows only for what is comparable across them, value as the row the board orders on. |
| `v4_cells.html` | The owner's four words are the whole layout — **who · why · instead at his position · instead at another position**, each alternative with its cost — and nothing else needs to be resident. |

---

## Revision notes — what changed in all four, what was refused

### Applied everywhere (ADJUDICATION_R2 §1, §3, §5, §6, §7, §8)

- **The `late` negativity sentence (§1).** `displacementHTML(c)` renders once per variant, in
  bright type with an amber rule, beside the number it explains: *"Your starters are set, so he
  would sit — **−33.7** of his −34.6 is the measured cost of displacing a starter you already have;
  the rest of him is **−0.9**."* It fires only when `displacement_adj` is non-zero under basis
  `measured`, so `early` and `mid` (measured zeros) show nothing. V1: under the header. V2: inside
  the open door. V3: one spanning row *"Why below zero"* under the value row, with all three
  displacements and remainders (said once, not once per column). V4: inside WHO.
- **No tie, anywhere (§3).** `tiedWith` and the tie chip are deleted; `forces` is not read for
  display. The board's evidence that not taking #1 is defensible is now the **margin**, printed
  beside the value on every header: *"the board's first by value · K. Concepcion 0.2 behind"*
  (and *"Q. Judkins 2.7 behind"* at `mid`, *"A. St. Brown 9.8 behind"* at `early`). The
  `Math.abs(dv) < 0.05 → "level with"` constant is gone too.
- **Measured values never render as absences (§5).** Every hand-picked visibility cut-point is
  removed from `_core.js`: `|horizon| >= 2` (two places), `|projToBest| >= 2`, `|dproj| >= 2`,
  `takeProb >= 0.01`, `dv < 0.05`. `time_horizon_adj` prints its number at any magnitude in the
  working and in V3's row (Allen `0.0`, McMillan `−0.3`, St. Brown `−0.9`). `denial_value` prints
  in the working as *"Kept from rivals (measured against every rival board that could price him):
  0.0"* and in V3's rival row as *"0.0 kept"* — a measured zero as a number with its basis. The
  rival line reads *"none"* only when `denial_team` is null, which is a null, not a threshold; the
  take probability prints `takeText` at any value ("under 1%" is rounding language, not a gate).
- **`no_surplus` captioned with the engine's own words (§6).** `DEPTH_LABEL` holds all five
  `EXPOSURE_BASIS_LABELS` verbatim; the surface prints the label for whichever basis the row
  carries, and a digit only under `measured` (still exactly the three `late` rows).
- **`A. St. Brown` (§7).** `short()` keeps name particles (St., Van, De, Mc…), so Amon-Ra St.
  Brown and A.J. Brown no longer collide on the `early` board.
- **"The last receiver this board rates" (§7).** Now *"No receiver behind him in the order the
  drop was measured (K. Concepcion is ahead of him there); the drop measured behind him (a sharp
  drop, 4.2) is to a player below this board."* V1's wait column says *"nobody behind him in that
  order — K. Concepcion is ahead of him there"*.
- **The second edge is no longer "order", and carries its magnitudes (§2, §8).** `compare()` now
  computes the **two-turn totals** from `position_next_turn_value`, which is on every candidate:
  *him now + the other position at #NEXT* against the reverse. `edgeHTML` prints value **now**
  bright (`+2.7 now, T. McMillan`) and the two-turn difference quiet (`+2.2 over two turns,
  Q. Judkins`), with the totals in the hover and written out in V2's across cells, V3's pair lines
  and V4's alternative sentences (`T. McMillan now + RB at #54 ≈ 94.4 · Q. Judkins now + WR at #54
  ≈ 96.7`). The AGREE / SPLIT badge, the word "order", the word "defensible" as a per-row verdict,
  and the "first by" leader are all gone; the reader sees two magnitudes and no second ranking.
  Verified: `tav − next_turn == forfeit` to ±0.03 for every position in every state, so the
  difference of the totals is exactly the ADJ §6 subtraction.
- **Cross-position forfeit superlatives removed.** No `most` / `least` anywhere; the position
  layer says *"≈ 47.0 at #54 · 5.5 less if you wait"* (V4), *"wait: about 5.5 less at #54"* (V2),
  or *"at #54 this position gives ≈ 47.0, about 5.5 less than now"* (V3 sheet). Scope is in every
  sentence ("on this board", "among the 24 this board rates here").
- **Hierarchy, not footnotes (§8).** The ▲/▽ valence glyphs and their legend are deleted (a legend
  that did not hold). Every footnote that explained the design to the reviewer is deleted ("the
  span is one marked count, not 12 empty boxes", "rows appear only where they can differ", "wait
  costs inform the order and never rank it"). What remains is one short "how to read" line where
  the two figures need naming (V1's INSTEAD column). The word "engine" does not appear on any
  surface; "priced" does not appear.
- **`confidence` is never rendered** (it never was; noted per §3).
- **Position facts said once.** The wait cost appears as a labelled position line ("AT WR ·
  …") in V1 and V4, not as a per-player reason; the run / none-drafted facts live on the position
  layer only.
- **Lists never show a half row.** `snapList()` snaps every list to whole rows and the caption
  says *"showing 10 of 24 · scroll for the rest"* or *"all 7"* — the resident count is stated out
  loud. At `late` every list shows all seven, fully named.

### V1 · Ledger, cut
- **Changed.** Side column widened to 310px and rows leaned so all seven `late` names render
  unabbreviated; roster rows now carry the subject (gold "←") **and the three alternatives as
  numbered chips 1·2·3 on the slot each would fill** (the lettered-strip idea, vertical); the
  INSTEAD heading is neutral ("the next names, at what cost"); the rail caption no longer talks to
  the reviewer; `YOUR NEXT` sits 48px inside the right edge with the right-hand mask fade removed.
- **Refused.** Opus B's suggestion to fold the rail into V4's clock sentence: V1 is the variant
  that tests the span rail, and it is the only rail in either set that shows eight named past
  boxes and zero blank ones. The "WITHHELD" row stays in the wait column: the brief says withheld
  ≠ missing, and the wait column is exactly where a reader would otherwise assume a survival number.

### V2 · Doors
- **Changed.** Doors are sized by the open door's content, never taller (no fixed height, no
  occlusion — asserted). **One baseline for every gap on the screen**: the open door's best,
  named in the pool header and in every closed door (*"−4.6 vs T. McMillan"*). "All three" is
  computed from the rendered column. The open card carries the slot line via the frame ("bench")
  and the displacement sentence inside the door. The QB absence at `early` is said twice (pool line
  + body), not four times. Across cells print the two-turn totals. The roster strip lights each
  door's best on the slot he would fill, the open door's in gold. Closed-door names wrap instead of
  truncating.
- **Refused.** Both reviewers' "kill it". The adjudication does not rule on which variant is best,
  and the structural failures named (occlusion, the cut row, two baselines, no bench line) were
  defects of execution, now fixed and asserted. The closed doors still carry some empty space at
  `late` (one name per door); that is the honest cost the brief anticipated and it is visible, not
  hidden.

### V3 · Trio
- **Changed.** The **"Drop behind him" row is gone** (F4 / ADJ §3): each head carries its own drop,
  measured within its position, with its own neighbour, and no row offers a left-to-right reading
  of a per-position quantity. Rows that remain are comparable across positions: value now, what
  his position gives at #NEXT (with the wait cost as the difference), rival named + value kept,
  dynasty horizon (every measured value), depth insurance (digit only where measured, the engine's
  label otherwise), the board's read. The "Why below zero" row spans the three. Pair lines carry the
  two-turn totals and both magnitudes, no verdict word. Rail ticks are 66px and read "Roster 7";
  the orange legend appears only when a rival is named (none at `late`).
- **Refused.** Replacing the tick rail with V1's span (Opus F14): V3 is the only variant testing
  axis 4's "boxes both directions" and the ticks now carry a name per box. Default A/B/C being the
  strip's trio (Sonnet): it is the honest default; the sheet and the A/B/C buttons change it in one
  click.

### V4 · Four cells
- **Changed.** The position strip's loudest number is now the value (bright) with the wait cost
  quiet and phrased as what the position gives at #NEXT; no superlatives. A **roster strip** sits
  under it with the subject lit and each other position's best on its own slot. WHO carries the
  displacement sentence, the margin, the board's read on the sub line, the slot and the rival; the
  withheld chance and the horizon moved to the working. WHY no longer repeats WHO. "Instead at his
  position" shows his two nearest neighbours by value, labelled *next below him* / *just above
  him* (one rule for every subject). Rows are `auto` / `1fr` so three alternatives fit at `late`.
- **Refused.** Removing the WITHHELD row entirely (Sonnet F9): it is in the working, where the
  survival quantity would otherwise be assumed.

### What I judged to be layout opinion and left alone
- "V4 is first / V2 should die" — not scored, per §11.
- "Resident characters should be fewer at `late` than at `mid`" — `late` now carries fewer words
  than `mid` in V1, V2 and V4 (the facts that exist are fewer); V3 carries slightly more because the
  displacement row only exists at `late`, which is the one sentence the adjudication requires.
- Sonnet's "SPLIT only when edges are comparable": overtaken by the adjudication — there is no
  verdict word at all now, and both magnitudes are always printed.

---

## The nine points

### 1. Hypotheses
As in the table above. The shared bet underneath all four: the owner's sentence — who · why ·
other valid options · at what cost — is a layout, and the honest unit of "at what cost" is the
two-turn total (him now + the other position at my next turn), not a second ranking.

### 2. Primary / secondary / hidden-until-asked
| | primary | secondary | hidden until asked |
|---|---|---|---|
| V1 | header (name, margin, read), WHY, INSTEAD ×3 with costs, IF YOU WAIT | roster with lit + numbered slots; the board beside | position strip (toggle), the working, rosters, draft board, Debate/Insight |
| V2 | four doors in lineup order, the open one with its names side by side; across cells | roster strip with each door's best on its slot; the board below | the working (none resident), rosters, draft board, Debate |
| V3 | three heads with their own drop; comparable rows; pair totals | lettered roster strip; the board with A/B/C | position sheet, rosters, draft board, Debate |
| V4 | WHO · WHY · INSTEAD AT HIS POSITION · INSTEAD AT ANOTHER POSITION | position strip; roster strip | the board (sheet), the working, rosters, draft board, Debate/Insight |

### 3. How the decision is communicated
The subject is *the board's first by value* with the margin to the next name beside it, and the
board's own read (necessity label) as a word. Alternatives carry value **now** (bright) and the
two-turn difference (quiet) with the totals written out. Within a position the comparison is value
and the measured drop between neighbours, with the sentence that waiting costs the same. At `late`
the displacement sentence explains the sign once, in bright type. Nothing says "take", nothing
ranks on wait cost, nothing asserts a tie.

### 4. How the variants differ structurally (the four axes)
| | position layer | pool | within-position comparison | rail |
|---|---|---|---|---|
| V1 | summoned (toggle under the ledger) | beside | click a name; three alternatives recompute around him | named past + one marked span |
| V2 | persistent doors, lineup order, never re-sorted | below | always-on inside the open door | none — the clock bar names the drafter and the wait; the past is one sentence |
| V3 | summoned (bottom sheet with → A/B/C) | below | A / B / C slots | boxes both directions, future as named roster ticks |
| V4 | persistent compact strip | summoned | always-on in a cell (nearest neighbours) | none — as V2 |

### 5. Roster / pool treatment
Every variant now has the lettered-slot device in some form: V1 numbers the alternatives on the
roster list, V2 and V4 put each position's best on the slot he would fill, V3 letters A/B/C. The
pool is beside (V1), below (V2, V3) or summoned (V4), always captioned with how many of how many
are visible, never a half row, and at `late` always all seven. No pool gauge is drawn: the payload
carries none.

### 6. Rail treatment, and the §1 change request
V1 and V3 keep a rail that satisfies §1 (boxes carry the drafter — as "Roster N", the display name
being a proposed field — mine glow, YOU ARE UP and YOUR NEXT marked, re-centre and "my last"
buttons). **V2 and V4 have no rail.** That drops four RULED §1 items — the rail, name boxes, the
glow, re-centre — and this is an explicit change request to §1, not a layout preference:

- *What is kept of §1's promise.* "Who is on the clock is never ambiguous": the clock bar reads
  **PICK 4.07 — YOU ARE UP** with the drafter's name set as a lit chip (here "YOU"; a seat's
  display name for anyone else), and *"10 picks until you choose again · your next turn is #54"*.
  The past is one sentence (*"since your last turn (#30): 5 WR · 5 RB · 2 TE left the board"*).
  The full board is one click away.
- *What is lost, named.* The shape of the wait as a picture (§2's argument); the named sequence of
  who picks between my turns (available in the draft-board sheet, not resident); the glow on my
  past picks; the emblem slot for a verdict on a past pick (no verdict exists yet). In a league
  where picks are traded, §2's necessity argument for the next-turn marker applies — the clock
  sentence still names #54, so the marker survives as a number if not as a box.
- *What it buys.* ~120px of height given to the doors (V2) or to type size (V4), and the removal
  of the one element the owner raised three times and never positively.

The owner invited this; it is his call.

### 7. Where the LLM attaches
Debate and Insight are billed buttons in the header / ledger foot, marked *billed · on the clock*,
with the contract-only sheet (what a debate does, where it lands, no invented chair text). The call
lock chip states its honest state (not set). The base surface needs no provider.

### 8. API contracts assumed (nothing faked)
1. `position_next_turn_value` and `positional_forfeit` per position — on the payload; used for
   the two-turn totals. Proposed: emit them per lineup position **including positions with no
   rated candidate**, so an empty door can state its wait cost.
2. `displacement_adj` + `displacement_basis` — on the payload; the `late` sentence reads them.
3. `cliff.tier`, `positional_cliff.gap` — 1:1; proposed `cliff.neighbour_id` so the client need
   not re-derive the bpa order.
4. `necessity_label` — rendered 1:1 as the board's read. `ambiguities[]` — read for ties; empty
   here, so no tie is shown. `confidence` — not rendered (§3).
5. `depth_exposure` / `depth_basis`, `denial_value` / `denial_basis` / `denial_team`,
   `rival_premium_take_probability`, `time_horizon_adj` — all rendered with the engine's basis
   labels; measured zeros print as `0.0`.
6. Proposed: `seat.display_name` (§1), `next_turn_pick_no`, `pool_gauge` per state (§14, absent
   here), `withheld[]` honoured by stripping values at the boundary.

### 9. Reusable vs prototype-only
Reusable: the core's `compare()` with two-turn totals; `displacementHTML`; `marginHTML`; the
verbatim basis-label tables; `short()` with particles; the lettered/numbered roster devices in both
orientations; `snapList` + caption; the span rail; the occlusion / overflow assertions in
`_shot.py`. Prototype-only: the state switcher and top bar; the 2×2 proportions (V4); the door
column ratio (V2); client-side `slotRoster` (the lineup optimiser owns it).

---

## What `late` and `early` taught this round, beyond the first pass
1. The `late` board's sign has one named measured cause and it was on the payload all along;
   every variant now says it in one sentence, and the "value" headline reads as a value again.
2. A class name collision (`.alt` on both a roster row and a ledger row) truncated the roster
   marks to "2.." — visible only in the image, not in any metric, and only once the alternatives
   were drawn on the roster. The overflow assertion now catches it.
3. Occlusion by a sibling and a half-cut final row are invisible to a self-clipping probe; both
   are asserted now and both failed on the first run of the new probe.
4. Seven names in two columns need exactly four whole rows; the list snaps to whole rows and says
   "all 7", and at `late` no list scrolls in any variant.

---

# Polish pass — Four Cells only (owner: "super-polish these into submission")

`v1_ledger`, `v2_doors` and `v3_trio` are cut and were not touched; they still build from the shared
core so the directory stays consistent. Everything below is `v4_cells.html`.

Verified: six renders (`#early` / `#mid` / `#late`, each with and without tanks via `-notank`) pass
every assertion — no page scroll, no clipping, no console errors, min font 12.0px, **zero text
overflow, zero occlusion**, no list scroll at `late` — plus the interaction pass. All six PNGs read.

## What changed, on my judgement — so he can push back on taste

1. **Each cell answers one question, and only that.**
   - WHO: name, team, points, the board's read, value, margin to the next name, the `late`
     displacement sentence, the slot he fills, copy / Insight / the working. *Removed:* the rival
     line (it is WHY's sentence, said once) and the "since your last turn" fragment (moved to the
     clock bar, which is about the draft's time).
   - WHY: only what separates him from the others at his position (rank, the measured drop and
     its neighbour, the named rival, designation, depth where measured). *Removed:* the position's
     wait-cost line — it is the strip's number, and saying it twice was the owner's "volume".
   - INSTEAD AT HIS POSITION: his two nearest neighbours by value, each with **one sentence**
     ("4.6 behind T. McMillan today · neighbours in the measured order, a sharp drop (3.2) between
     them"). *Removed:* the two-figure edge line that said the same thing in symbols.
   - INSTEAD AT ANOTHER POSITION: each position's best, each with **one sentence that performs
     the arithmetic the reader was holding in their head**: "Two picks: Q. Judkins now + a receiver
     at #54 ≈ 96.7 · T. McMillan now + a running back ≈ 94.4 → Q. Judkins first by 2.2; today
     T. McMillan by 2.7." Both magnitudes, both totals, no verdict word, nothing to net.
2. **The position strip carries the value bright and the wait quiet:** "J. Allen 47.9 · slot open ·
   46.2 at #54 · wait: −1.7". The strip is the only place the position's wait cost lives.
3. **The clock bar carries the whole of the draft's time:** pick, who is up (lit), the wait, the
   next turn, and "gone since your last turn: 5 WR · 5 RB · 2 TE". Shortened until it fits at
   `late` without wrapping or truncating (the probe refuses ellipsis).
4. Hover text and footers that explained the design are gone; the only resident explanations
   are the two cell sub-captions ("his neighbours by value · same wait cost", "two picks: now +
   #54").

## What I refused
- Adding a fifth region or any resident list: the owner asked for clean dissemination, not more.
- Re-basing the `late` scale or softening the negative numbers: the displacement sentence is the
  honest explanation and it stays, bright, beside the number.
- Collapsing the two-pick sentence to one number: ADJ-R2 §2 — the totals are the information.

## The gas tank — tried on Four Cells, verdict: keep it, small, as a state marker; it is not a gauge at this size

**Built:** one vertical tank per offensive position, 16×42px, inside each position cell of the
strip, between the position letter and the name. Full at the position's own opening count
(`frame.json` gauge: QB 42 · RB 126 · TE 115 · WR 198 — the same draft, rail identical), drained
by the picks on the rail (a coordinate; the fill is `1 − drafted/opening`), with the **replacement
bar as a line inside** at `starterRank/opening` from the top (QB 12 · RB 32 · TE 20 · WR 32). No
bands, no counts, no percentage on screen (the hover gives the percentage and the sentence).
When the fill is below the bar the fill dims and the bar turns amber: *this position is past its
starter line; a player taken here is a bench piece.* Toggle in the top bar (`#late-notank`)
shows the screen both ways; `_shots/v4_cells_{state}.png` and `_shots/v4_cells_{state}-notank.png`.

**What it displaces:** nothing — it takes 22px of width in each strip cell, paid for by shortening
the cell's status text ("slot open", "RB2 open", "bench") and the wait figure ("wait: −5.5").

**What it says that the sentence cannot:** at `late` three of four tanks are below their line
(WR 72% left vs a line at 84%; RB 73% vs 75%; QB 62% vs 71%; TE 83% at its line), so the screen
shows *why* every candidate is a bench piece before the reader reaches the displacement sentence.
At `mid` all four are above their lines (QB untouched at 100%), and at `early` all four are full.
The two facts — my starters are set (roster), the league's pool is past its starter line (tank) —
are now both visible, and they are the same fact as `displacement_adj` at two scales.

**What it cannot do at this size, said plainly (§14):** §14 derives that per-pick checkability
holds only while the tank spans at least one unit per player; at 42px the WR tank moves 0.2px per
pick and RB 0.3px. It reads as a level and a state (above / at / below the line), not as a gauge a
drafter can verify pick by pick. A §14-faithful gauge (≥198px for WR) would need its own region;
the only honest candidate is the empty lower half of WHY, which is the wrong question for it. I did
not build that; the small marker is what earns its place on this layout.

**Two approximations, disclosed:** (a) the drain counts every drafted player at the position as a
departure from the rated pool; on this draft that is exact through pick 80 (verified against the
gauge history) and may overstate the drain by a few players later, which can only move a tank
*toward* "below the line" — at `late` the three below-line tanks are below by 12, 2 and 9 players,
so the WR and QB readings are safe and RB is the marginal one; (b) with no bands the tank makes the
ordering claim `#282b`'s per-band draining avoided (that the players who left came off the top);
for an engine-made draft that is true by construction, for a human draft it is approximate. Both
go away when the API ships §14's per-state gauge (`left` per band, as the `frame.json` gauge
already does at pick 40).

**Owner's three critiques, answered:** too large → 16×42px; horizontal is counterintuitive →
vertical, full at the top, drains down; "do we need meh?" → no bands at all, only the starter bar.
