# Mobile review r1 — angle: a thumb, a clock, and a hostile real world

Reviewer: Sonnet (thumb angle). Reviewed commit: started at `4210fa2`; HEAD moved to `e1da302` while I read.
`git diff 4210fa2 e1da302` touches only MOBILE.md, DOC_INDEX.md, `_shoot.py` (one job-list change) and another
review file, so `_src/m*.tpl.html` and the built `m*.html` I read are the ones at HEAD. I did not read the other
reviewer's file or MOBILE.md.

My captures and probe scripts are in `/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/rv/out/`
(file names are cited below).

How I looked. I read the three templates in full, `shared.js` where cited, and `REVIEW/ANGLE/BRIEF`. The shipped
renders in `_shots/` are viewport-only (`_shoot.py` calls `screenshot(full_page=False)`), so they cannot show what
is below the first screen. I therefore drove the built files myself with Playwright/Chromium (touch enabled) from
my scratchpad, took full-page captures, and tapped like a thumb: real `touchscreen.tap` at element centres,
reading back `scrollY` and bounding boxes. I wrote nothing into the repo and did not run `_build.py`. Where I cite
a coordinate it is from one of those runs, 390x844 unless stated. The review bar (36px) is included in every
"% of screen" figure; subtract about 4 points for the product.

Labels: VERIFIED = I measured or rendered it and say where. SUSPECTED = inference I could not exercise.

Board facts that matter: HEAVY_IDP has **7** doors, not nine (`M.DOOR_ORDER.length`, VERIFIED by probe), 5 in the
window and 2 held as chips. 12T_ppr_K_DEF has 6 doors; K and DEF are streamable and set aside, so in the late state
the board's first name (Cam Little, a kicker) is on no visible door and every cost line says "instead of Little".
That is the same as desktop (v4_doors_12T_ppr_K_DEF_late.png), so I do not count it against the phone.

---

## Findings, ranked

### 1. [m1] The landing screen shows one recommendation, and the "compact rows" are not compact — VERIFIED
- `m1_stack.tpl.html` line 274 opens the leader's door on load, and the open door is ~0.6 to 1.1 screens tall.
  Probe (names fully inside the first viewport, late state, 360x800 and 390x844): **1 of 4-5 in every format**.
  Doors 2-4 start at document y=1101, 1306, 1484 in 12T_ppr/mid (info calls on `[data-door]`), i.e. 1.3 screens down.
- Even collapsed (`?collapsed`, the X state) a closed row is 149-217px tall (RB 149, WR 200, QB 174, TE 217 at
  390x844), so the "stack of compact rows" is 4 full cards: 1.49 screens in 12T_ppr/late at 390x844, 1.96 in HEAVY_IDP/late at
  360 (my measure agrees with the builder's 1.96 against a 2.0 gate). Landing (leader open) peaks at 2.46 screens
  (HEAVY_IDP/early/360), the largest in the set.
- Against the brief: "I'm thinking the 4-5 main recommendations near the top." In m1 a reader at the first
  screen sees the leader and a stack of text, and has to scroll to learn there are other valid doors. That is the
  owner's own point ("not taking the engine's #1 isn't inherently wrong") hidden below the fold.
- Instead: a closed row is name + value + one cost, about 64px; the three cost cells and the displacement line
  belong to the open row.
- Evidence: `_shots/m1_stack_12T_ppr_mid_390x844.png` (only the open RB door), my `m1_stack_12T_ppr_mid_390x844_full.png`,
  `m1_stack_c_HEAVY_IDP_late_360x800_full.png`.

### 2. [m2, m3] After one tap, the reveal throws the grid, the clock and the X to the top edge — VERIFIED
- `m2_sheet.tpl.html` line 295 / 316: `reveal()` is `scrollIntoView({block:"start", behavior:"smooth"})` on `#panel`.
  Tapping the WR tile (centre y=481) scrolls the page 727px. After it: all four tiles are above the viewport (WR
  tile y=-323..-168), the panel's X sits at y=5..49 (centre 27 of 844, 3% down), and `.clk` is off-screen.
  To try QB the reader flicks up ~727px, taps, and is thrown down 727px again.
- `m3_hero.tpl.html` line 291 / 311: chip tap scrolls 364px; the hero X is at y=5..49 and `.clk` is at y=-224.
  m3 survives this because its chips stay on screen (y=409..502), so the X is rarely needed.
- `.clk` is `position:static` (computed style read back in m3; `grep -c sticky` on all three m templates is 0). On desktop the clock never scrolls
  (`.room{height:100vh;overflow:hidden}`, shared.css line 51), so "two sides of the same UI" is broken exactly where
  the drafter needs it: the pick timer is out of sight every time they read an alternative.
- Against the angle: "an X in a corner a thumb cannot reach without a grip change". The builder's own scroll
  handler parks it there.
- Instead: do not align the panel to y=0. See the single change at the end.

### 3. [all three, shared CSS] The doors begin 46-67% of the way down — VERIFIED
- Probe, late state, `.door` top / viewport height: m1 46-62%, m2 51-67%, m3 46-56%. Worst: HEAVY_IDP and K_DEF at
  360x800, first door at y=495 (m1), 535 (m2), 447 (m3).
- Cause, measured block heights (m2 collapsed, `getBoundingClientRect`): at 390x844 12T_ppr/mid review bar 36 +
  header 104 + clock 92 + lineup 79 + count line 76 = 387px; at 360x800 HEAVY_IDP/late 36 + 120 + 92 + 127 + 143 =
  518px (lineup wraps to five rows; the count line is four lines plus the two held-door chips). K_DEF/late is
  36 + 120 + 92 + 103 + 143.
- The four sheet buttons (Every name, Rosters, Draft board, Debate) sit at y=85-131 (10-15% down, measured on
  `.hdr .r`), the one band a thumb cannot reach. The doors, used every pick, are in the middle.
- Against the brief: "4-5 main recommendations near the top" and "clean dissemination of information over just
  having as much on the screen as you can fit." The lineup strip is the costliest block per useful pixel and largely
  restates each door's own hold line ("Taylor · 1 slot open" against the `RB Taylor` chip); the `← Etienne` chip is
  the one new fact.
- Instead: a one-line lineup, the four buttons in a bottom bar, the count line folded to one line. By arithmetic from
  the block heights above that puts the first door near y=200 in the product (SUSPECTED, not built).

### 4. [m1] Tapping a lower door lands the reader at an arbitrary offset, with its header and X off-screen — VERIFIED
- `m1_stack.tpl.html` line 293 opens a door with `draw()` and no `reveal()` (only the count chips at line 291
  scroll). The door above collapses and everything below shifts up by its height.
- Run A: scrolled to 600, tapped WR at y=601. After: the WR door is at y=-83 (845px tall), its X at y=-78. The
  reader sees alternatives but not the position name or the X.
- Run B: scrolled to 400, tapped WR at y=801. After: door header at y=117. Same tap, two different landings; the
  outcome depends on where the thumb happened to have scrolled, which is not controllable.
- The brief's m1 promise, "The reader never loses their place in the list", is untrue in the one case that
  matters: switching from an open door to another.
- Instead: `scrollIntoView({block:"start"})` on the tapped door after the redraw (what `reveal()` already does for
  chips), or collapse the previous door without moving the new one under the thumb.

### 5. [m2, m3] At a glance the cost is one cell, and it is the cell the engine disagrees with — VERIFIED (display), judgment on top
- `m2_sheet.tpl.html` line 218 and `m3_hero.tpl.html` line 236 print only `sgn(best.value - leader.value)`, the
  "now" cell. `M.costOf` (`shared.js` ~475-486) has three: now, at #NEXT, **both picks**, and flags "both picks"
  favourable when `planEdge > 0` (line 479, `fav:r.planEdge > 0`).
- 12T_ppr/mid (m1's closed rows, my full-page capture): WR now -9.1, at #67 -10.4, both picks **+1.3** (amber).
  TE now -58.3, at #67 -65.2, both picks **+6.9** (amber), and the desktop labels TE "The dearest position to wait
  on right now" (v4_doors_12T_ppr_mid.png). m2's TE tile and m3's Fannin chip say only `-58.3`. A glancing reader
  reads TE as a catastrophe and does not open it.
- Also in m2: the tile prints value then gap with no word between them ("-12.7  -58.3" for TE), two adjacent
  negatives, decoded by a 3-line sentence in the count line above the grid (m2 line 263). That sentence is the
  legend and it has scrolled away by the time the panel is open.
- Against the brief: "clean who, why, and other valid options, at what cost." I would not add cells. Show the
  decisive one: "both picks" when it flips sign, "now" otherwise, with its word ("both +1.3").
- SUSPECTED only on how the owner would weigh it; the displayed-versus-computed facts are VERIFIED.

### 6. [m3] The other doors are thin, and sometimes below the fold — VERIFIED
- A chip is position + last name + one gap (m3 line 236-237). No value, no hold line ("you hold none, slot open"),
  so "why" is absent for every door but the hero. m2 tiles carry the hold line.
- HEAVY_IDP/late/360x800: hero 447-~800, first chip at y=913, six chips in four rows, alts at y=1112. The first
  screen answers who and why and nothing about what else is valid.
- LIGHT_IDP early and mid at 390x844 (builder's own `_shots/m3_hero_LIGHT_IDP_early_390x844.png` and `_mid_`):
  the first screen ends at the bottom edge of the chip row, 8px from the fold, with the alternatives block starting
  exactly below it. It looks like a finished page. The owner's "other positional options populate the lower end"
  is there, but nothing says so.
- The leader's own alternatives sit under the chips, not under the hero. A reader scanning down meets
  "Etienne / the other doors / Burden Purdy Fannin / THEN AT RB" and can read the RB cards as belonging to the
  TE chip above them. SUSPECTED (association is judgment); the order is VERIFIED in m3_hero_12T_ppr_mid_390x844_full.png.
- Tapping the collapsed hero opens the alternatives with no reveal (line 311 calls `reveal()` only for `.dchip`).
  At 390x844 12T_ppr/mid they begin at y=825: the reader taps and sees an X appear and a 19px sliver. VERIFIED
  (info `#alts` y=825; screenshot m3c_after).

### 7. [m2] Tiles are too narrow at 360: orphaned marks and three-line names — VERIFIED
- 360px gives a tile ~133px of text width. In **12T_ppr/mid at 360x800** three of four tiles wrap the availability
  mark onto its own line: "Travis Etienne / +", "Luther Burden / +", "Harold Fannin / +" (`_shots/m2_sheet_12T_ppr_mid_360x800.png`).
  HEAVY_IDP/late shows "Michael Wilson / +" and "George / Karlaftis +".
- "Jacory Croskey-Merritt ✓" is three lines ("Jacory / Croskey- / Merritt ✓") in a tile that grows to ~215px and
  stretches its row neighbour (my `m2_sheet_c_4WR_TE_PREMIUM_late_360x800_full.png`).
  m3's hero wraps the same name to two lines with the ✓ orphaned on the second (m3 hero at 360).
- m2 tile heights follow name length, so the grid's height moves between draft states of one format: 4WR_TE_PREMIUM at
  360 is 352 / 319 / 369px (early / mid / late), HEAVY_IDP 496 / 480 / 496, everything beneath it shifts. Type itself does not
  breathe (I read computed font sizes for 8 selectors per variant across 3 formats x 3 states x 360px: one value each).
- Instead: put the mark in the sub line, and let the name take the tile's full width (drop the position pill that
  duplicates the Cinzel title), or go to a single column for the odd tile.

### 8. [all three] Nothing at the fold says "more", and about 1 render in 12 ends in a gutter — VERIFIED
- No variant has a "↓ more", fade, or peek treatment. The page cue is the content being cut mid-block.
- I tested whether the fold (y = viewport height) lands inside any block (door, chip, card, panel, count) for
  3 variants x open/collapsed x 6 formats x 3 states x 2 viewports (216 renders). In **17** the fold falls in a gutter
  of at most 9px with real content below, i.e. the first screen looks complete. Examples: m1 collapsed HEAVY_IDP
  early/mid 360x800 (fold in the gutter between two doors, 544px of page below it); m3 open LIGHT_IDP early/mid 390x844 (finding 6).
  Two collapsed renders (m3 HEAVY_IDP/mid/390; m2 12T_ppr/late/360) scroll 6-7px past a finished layout.
- There are no internal scrollers in the page itself (`data-list="cards"` hosts are plain blocks), so the "↓ N more"
  rule has nothing to attach to; the page-level fold is the whole problem.
- The Draft board sheet is a horizontal scroller (788px content in 388px, `dbHost`, overflow-x auto) with no
  affordance; the 6th column (your own, gold) is clipped at the right edge. It is in a sheet, so the gate cannot see it.
  VERIFIED in `m2_board.png`. The drafter's own column is the one that matters.

### 9. [all three] The action that closes a pick, copy name, is a top-of-screen control, and the alternatives are two sheets deep — VERIFIED
- Positions (390x844): m2 after a tile tap, "copy name" centre y=219; m3 after a chip tap y=224; m1 landing y=531.
- Alternatives have no copy button. To take Bucky Irving (the #2 RB, a legitimate pick per the owner): tap the card
  (y~484), the numbers sheet opens, "copy name" is at (65,58), then "close" at (338,58). Two controls in the top 7%.
- Every sheet's close is top-right. The sheets are full-width (`.sheet.right{width:100%}`), so there is no scrim to
  tap; the close button's centre drifts with the note's wrap (y=58 drawer and numbers, 80 draft board, 98 rosters, ~30 debate). The only exit is a grip change.
- Against the angle: "A primary action parked at the top of a scrolled page is a real problem."
- Instead: copy lives on the alternative card (the desktop cards carry it), and sheets close from a 44px bar at the bottom.

### 10. [all three] Touch fires the desktop hover layer — VERIFIED in emulation, SUSPECTED on real devices
- `shared.js` line 734 shows a tooltip on `mouseover`, which touch browsers synthesise on tap. Tapping a closed door
  on its position title strands a tooltip in the corner after the door re-renders: m1, tap on WR's title, a lower-case
  "wide receiver" box at (8px, 6px) over the review bar (`m1_tiptap.png`); m3, tap on the collapsed hero title
  leaves "running back" at the same spot (`.tip.on`). m2 hides it because its auto-scroll dismisses tips.
- Tapping Debate left "Billed, and only while you are on the clock." over the sheet's first paragraph (`m2_debate.png`).
  The billing warning exists nowhere else on a phone.
- The only on-screen meaning of the ✚ / ✓ / ◌ marks is in these tooltips; there is no legend in the m templates
  (grep). The ✚ glyph, a plus, next to the recommended name means "has missed weeks", on a 15x20px target that the
  tap-target gate does not cover. The tooltip it opens ends "click again, or Esc, to dismiss", with no Esc on a phone.
- Instead: gate tooltips to `(hover:hover)`, and print a one-line legend where the marks first appear.

### 11. [all three] `min-height:100vh` — SUSPECTED
- Line 15 of each m template. m2's collapsed page is exactly 1.00 screens at 390x844 only because of this floor:
  the grid ends at y=719, the rest is padding. On iOS Safari `100vh` is the toolbar-retracted height, which is taller
  than what is visible, so the "one screen, nothing below it" promise becomes a scrollable strip of dark nothing.
  `100dvh` is the usual fix. I could not test it in headless Chromium.

### 12. [all three] The open door does not survive a state or format switch — VERIFIED, low
- `load()` resets `openKey = COLLAPSED ? null : defaultOpen()` (m1 274, m2 297, m3 293), identical to v4 line 284.
  The state/format buttons are harness, and `fillCommon` says the board is not re-read while the page is open, so no
  product path hits this. It does not move scroll position, so after a switch from a deep scroll you may be left
  below a shorter page. Not worth work; recorded because the angle asked.
- Pressing X in K_DEF moves the stack up 24px (the lineup strip loses its "← White" chip row; probe,
  `doorsTop` 495 open vs 471 collapsed in m1; 535 vs 511 in m2). Cosmetic.

### 13. Legibility, low
- `--dim` #7d7259 on `--surface` #17130d is 3.9:1 (computed from `shared.css` line 24), under AA for 12-13px text.
  It sets the m3 chip legend ("THE OTHER DOORS · AGAINST ETIENNE...", the line that explains every chip number),
  the demand line, and the nth-of-N label on closed rows. It is the north star's own token, so I would not change
  the colour, but I would not use it for the one sentence that decodes a number. Smallest type in use is 12.16px
  (m2 tile sub line and hold line), which is at the floor for a reader glancing at arm's length.

---

## The thumb walk (390x844, 12T_ppr / mid), one task: see the recs, open one, read the alternatives, collapse, open another

| | m1 stack | m2 grid | m3 hero |
|---|---|---|---|
| recs fully on the first screen | 1 of 4 | 4 of 4 | hero + 3 chips |
| to open WR | flick to find it, 1 tap | 1 tap | 1 tap |
| after the tap | RB collapses, WR lands at an unpredictable offset (finding 4) | page auto-scrolls 727px, panel fills the screen | page auto-scrolls 364px, hero WR at top, chips still on screen |
| read the alternatives | 1 flick | 0 flicks in 12T_ppr; panel is ~1.0 screen | 1 flick |
| collapse | flick up + X, or just tap the next door | X at y=27 | not needed; tap another chip, or the leader chip |
| open another | flick to find it, 1 tap | 1 tap, then another 727px scroll | flick back up, 1 tap |
| total, first switch | ~4 flicks, 2-3 taps | 0-1 flicks, 3 taps | ~2 flicks, 2 taps |

Fewest taps: m3. Fewest flicks: m2. Fewest is not the best. m3 gets there by demoting the other doors to chips with
no value or hold line; m2 gets there by showing everything at once and then punishing the second tap.

Worst formats, 360x800, late (probe `metrics.py`, doc height / viewport):

| | m1 open / collapsed | m2 open / collapsed | m3 open / collapsed |
|---|---|---|---|
| HEAVY_IDP | 2.33 / 1.96 | 1.99 / 1.30 | 1.53 / 1.33 |
| 12T_ppr_K_DEF | 2.14 / 1.74 | 1.88 / 1.14 | 1.50 / 1.30 |
| recs fully visible, first screen (HEAVY_IDP) | 1 of 5 / 2 of 5 | 4 of 5 / 4 of 5 | hero only; chips start y=913 |
| recs fully visible, first screen (K_DEF) | 1 of 4 / 2 of 4 | 2 of 4 / 4 of 4 | hero only |

Across all 54 format/state/viewport combos: m1 open max 2.46 (HEAVY_IDP/early/360), collapsed max 1.96; m2 open max
2.25, collapsed max 1.30; m3 open max 1.85, collapsed max 1.33. The brief says 2.5; `_shoot.py` enforces 2.0 main /
3.0 open. m1's main display is 0.04 under its budget.

Break attempts: Jacory Croskey-Merritt (4WR_TE_PREMIUM/late, the board's first name) fits one line in m1, two lines
in m3's hero with an orphaned ✓, three lines in m2's tile (finding 7). A door with no name: no format in the fixture
produces one (probe over 6 formats x 3 states), so `.door.none` is never rendered by the gate. I forced one by
overriding `M.doorBest` for QB and redrawing at 360x800: all three lay out without error and without clipping
(`montage_none.png`). That run is a monkeypatch, so SUSPECTED as a stand-in for real data. Nine doors: there are
seven (see above). A position the reader holds none of: "you hold none, slot open" in amber, fine in all three,
though in the early state every tile says it, so it stops discriminating.

What holds up, so it is not re-found: tap targets are 44px+ everywhere I measured; type does not breathe between
states; the open door's body is 0.57-1.17 screens in all three (so the X is never more than a screen from the
reader); the gate's no-clip claims held in everything I looked at; `?collapsed` is honoured by all three.

---

## Verdicts

**Survives a real draft: m2_sheet.** It is the only variant whose landing screen is the whole decision (four names,
four values, four holds, one gold border) at 390x844 in five of six formats and 4 of 5 in HEAVY_IDP at 360. The bare
grid is one screen, which is the owner's "main display" read literally, and in the late state the open panel is also
one screen. It is the closest match to "4-5 recommendations near the top, click one door, the others populate the lower
end, X in corner." It survives the three-second test; m3 does too for "who" but not for "what else" at 360; m1 needs
thirty seconds.

**Drop: m1_stack.** One recommendation on the first screen, rows that are not compact, the largest page of the three,
a tap that lands you wherever the collapse happens to put you, and an in-place model whose one real advantage ("never
lose your place") does not hold when you switch doors. Its single good idea, the full three-cell cost on every closed
row, belongs in the m2 panel's header, where it already is.

**m3_hero is the credible runner-up** and I would keep it if the league could only have one thing graftable: chips
that stay under the hero are the best door-switching in the set. It loses on the standing constraint because a chip
has no value or hold line, and because the leader's own alternatives sit under the chips.

### The single change that would most improve m2

**Dock a one-row door switcher at the bottom of the viewport while a panel is open** (4-5 tabs, 44px, position +
last name + the decisive cost cell, the open one lit; tapping the lit tab closes the panel). It does four jobs at
once: the 727px flick back up disappears, the X's job moves into the thumb zone (it is now at y=27), you can compare
doors without losing the panel, and the second tap stops costing a second scroll. It leaves `reveal()` alone and adds
no information to the screen, which is what the owner asked for.

Second in line, and cheaper if only one thing is possible before the beta: cut the chrome above the grid (finding 3)
so the grid is at y~150 and the panel needs a 300px scroll rather than 727.

---

## What I did not check
Real devices (iOS toolbar/`100vh`, synthetic mouseover on touch are inferred from Chromium emulation); live scroll
physics; the 430x932 renders beyond the metrics table; the full `_shoot.py` gate (I used my own probes and trust its
pass); anything below the first screen in the shipped PNGs, since they are viewport-only.
