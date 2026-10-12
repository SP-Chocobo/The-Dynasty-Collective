# Mobile review — the contract and the information design

Reviewed at `4210fa2` ("Add the phone hero: one door full width, the other doors as chips"), which
is the commit that settled all three designs. The tree moved twice while I read (`2af9c8a`,
`2c311f2`); `git diff --stat 4210fa2 HEAD -- ui_explore/round2/fableA/` shows the three templates
and the three built files unchanged, so everything below holds at HEAD. Only `MOBILE.md` and
`_shoot.py` moved — and one of those two moves is finding **F2**.

**How I looked.** Read `_src/v4_doors.tpl.html`, the three mobile templates, and the relevant
parts of `_src/shared.js` and `_shoot.py`. Looked at 16 renders, including the mandated set for
each variant plus `v4_doors_12T_ppr_mid.png`. Ran the gate myself at HEAD:
`python3 _shoot.py m1_stack.html`, then `m2_sheet.html`, then `m3_hero.html` — 324 renders plus
three name-stability lines, all `ok`. That run wrote 108 new PNGs into `_shots/` (the collapsed
pass for the four formats the directory had not kept images for); `_shots/` is gitignored and
`git status` is clean. I edited nothing and did not run `_build.py`.

**My own measured figures**, from that run, since they differ from the ones I was handed:

| variant | main display (`?collapsed`) | expanded (bare URL) | worst main-display case |
|---|---|---|---|
| `m1_stack` | **1.11 – 1.96** screens | 1.70 – 2.46 | HEAVY_IDP/late@360x800 |
| `m2_sheet` | **1.00 – 1.30** | 1.32 – 2.25 | HEAVY_IDP/late@360x800 |
| `m3_hero`  | **1.00 – 1.33** | 1.07 – 1.85 | HEAVY_IDP/late@360x800 |

Budgets are 2.0 (main) and 3.0 (expanded). Everything passes. m1 passes its main-display budget by
0.04 screens — about 32px at 360x800.

---

# Findings, ranked by severity

## F1 · HIGH · VERIFIED — m3's count line states a number of doors the screen contradicts
*(angle 1, 3, 5 — the surface telling the truth cleanly)*

`_src/m3_hero.tpl.html`, `countHTML` (the `showing ${w.length}` sentence) and `chipsHTML`
(`rest.map(chip) + hidden.map(chip) + held.map(chip)`).

`countHTML` prints the size of the **window**. `chipsHTML` then draws the window's chips *plus*
`hidden` *plus* `held` — i.e. every door the league can start. The sentence and the screen
disagree whenever the league has more than five startable positions or has K/DEF.

Two renders:

- `_shots/m3_hero_HEAVY_IDP_early_430x932.png` — "**7 positions** this league can start, **showing
  5** in the board's order: the window slides as the board changes" sits directly above a hero and
  **six** chips. Seven doors are on the screen.
- `_shots/m3_hero_12T_ppr_K_DEF_mid_430x932.png` — "**showing 4**" above a hero and **five** chips.
  Six doors on the screen. Worse, the row ends in a button reading **"show streamable"** while the
  two streamable doors sit beside it, already shown, with their names and their gaps to the leader
  (`DEF Rams first`, `K Dicker −18.4`). The button offers to do a thing that is already done.

The north star makes this line the thing that keeps the window honest. `v4_doors.tpl.html`
`countHTML` says "`showing 4`, in the board's order: the window slides as the board changes" and
then names the rest under the literal words **"not shown:"** — and exactly four doors are drawn.
m1 and m2 both kept that discipline; `_shots/m2_sheet_12T_ppr_K_DEF_mid_430x932.png` reads
"showing 4 … · **streamable positions set aside:** `DEF 1st door` `K 4th door` `show them`" above
exactly four tiles. The brief's hard requirement is "Same honesty … never print a number the
desktop declines to print." Printing a number your own screen refutes is the nearer relative of
that sin, and it is the one the engine's whole posture is built to avoid.

In m3 the window is in fact vestigial: it decides only which chips are dim. The sentence describing
it is the only thing left that treats it as real.

**What I would do:** drop the window from m3 and say "showing all 7"; or draw only the window's
chips and put the rest behind one "+2 more doors" chip, restoring the "not shown" words. Either
way, never draw a "show streamable" button in the same row as the streamable doors it offers to
show.

## F2 · HIGH · VERIFIED — `MOBILE.md`'s measurement paragraphs describe a gate that no longer exists
*(the record of what was measured — REVIEW.md's "say where you read it")*

All three sections of `MOBILE.md` say "**73 of 73 renders ok**" and "collapsed **on the two formats
the collapsed pass covers**", and each then reports the hardest board as a separate measurement
"**by hand**" on "the hardest format **the collapsed pass does not cover**".

`_shoot.py` `_jobs_for()` now returns `[(f, "", FORMATS), (f, "collapsed", FORMATS)]`, and its own
comment in the same file says: *"EVERY format collapsed, not a sample of two. … sampling two
formats left it unmeasured on the hardest board in the fixture."* My run at HEAD produced **108
renders per surface** (54 open + 54 collapsed), 324 in all plus three summary lines.

So, in each of three sections: the render count is wrong, the coverage claim is wrong, and the
"measured by hand because the pass does not cover it" sentences describe work the gate now does.
m1's headline collapsed range, "1.11 to 1.64", is the stale two-format figure; measured across all
six formats it is **1.11 to 1.96** (the right number is in the note, but only as the hand
measurement the note no longer needs).

This matters here more than it would elsewhere: `MOBILE.md` is the artifact that tells a reader
what was proven, and REVIEW.md's standard is "a plausible claim about the wrong thing is the
failure mode this repo fears most." These claims are plausible, specific, and wrong.

**What I would do:** regenerate the three `Measured:` paragraphs from a gate run and delete the
"by hand" sentences. This is a documentation fix, not a design one — it does not move the ranking
below.

## F3 · HIGH · VERIFIED — m2's default screen draws the same recommendation twice
*(angle 2 — "I dont need all the variables, i dont need every everything")*

`_src/m2_sheet.tpl.html`: `draw()` renders `tileHTML` for every door *and* `panelHTML` for the open
one. On the bare URL a door is open, so the open door is drawn twice.

`_shots/m2_sheet_12T_ppr_mid_390x844.png`. The RB tile carries: `RUNNING BACK` · `1st of 4` ·
`Travis Etienne +` · `NO · 232 pts · RB2` · `45.5` · `Taylor · 1 slot open`. The panel immediately
below carries: `RUNNING BACK` · `1st of 4 · open` · `Taylor · 1 slot open` · `Travis Etienne +` ·
`NO · 232 pts · RB2` · `45.5 to your roster now`. Six facts, drawn twice, inside 300 vertical
pixels, on the surface whose brief is "the main display fits one screen with nothing below it."

The owner's sentence is the standard: "Emphasize clean dissemination of information over just
having as much on the screen as you can fit." This is the clearest instance in the three variants
of something on screen that earns nothing.

**What I would do:** see the verdict. Landing m2 on the bare grid removes it outright.

## F4 · MEDIUM-HIGH · VERIFIED — m1's main display puts one recommendation near the top, not four or five
*(angle 1)*

- `_shots/m1_stack_12T_ppr_mid_390x844.png`: the open RB door fills the entire first screen. WR, QB
  and TE are below the fold.
- `_shots/m1_stack_HEAVY_IDP_late_360x800.png`: the single open door does not itself fit — the
  screen ends mid-door, at the demand line.
- Collapsed is better but not enough: `_shots/m1_stack_collapsed_12T_ppr_mid_390x844.png` shows 3
  of 4 doors; `_shots/m1_stack_collapsed_HEAVY_IDP_late_360x800.png` shows 1.5 of 5;
  `_shots/m1_stack_collapsed_12T_ppr_SF_late_360x800.png` shows 2 of 4.

Against the owner's own words — "I'm thinking the 4-5 main recommendations near the top" and "not
excessive scrolling" — this is the variant that does least of what was asked, and it is also the
one with the least measured headroom (main 1.11–1.96 against 2.0; expanded 1.70–2.46 against 3.0,
both the worst of the three).

I want to be fair about what m1 buys with that: it is the most structurally faithful of the three
(every door is a `.door` with a `.who .nm` inside `#doors`, which is the brief's hard requirement
stated literally), its count line is correct in every case I checked, and its X is the best of the
three (F10). But the cost is the owner's stated shape, and it is not recoverable without turning
m1 into m2.

## F5 · MEDIUM · VERIFIED — m3's main display prints the forfeit, and its superlative, with no route to the one qualification
*(angle 7)*

In `_src/m3_hero.tpl.html` `heroHTML`, the `.ctx2` block — demand, the wait line, the
dearest-position mark, the pool — is drawn **unconditionally**, while the `.acts` row (copy name,
**numbers**) is gated on `open`.

`_shots/m3_hero_collapsed_12T_ppr_mid_390x844.png` draws "If you wait, the best left at **#67**
nets about **39.5**, which is **6.0** less than taking one now." and no buttons.
`_shots/m3_hero_collapsed_HEAVY_IDP_late_360x800.png` adds "**The dearest position to wait on right
now.**" — a superlative that is a ranking *over* forfeits.

The qualification exists exactly once in the codebase, `_src/shared.js` line 501: *"Its expected
takes measured about one player per position low against replayed drafts, so read it as a **floor
rather than an estimate**."* It is a `b:` basis inside `M.working(c)` — reachable only through the
numbers sheet, i.e. through the button the unopened hero does not draw.

Scoped honestly: m1's and m2's collapsed states print **no** forfeit at all, so they have nothing
to qualify; and v4's *closed* doors print the same wait line with no local numbers button either,
so this is not pure mobile invention. What is mobile-specific is that here the collapsed state **is
the main display** and is where the X returns the reader.

**What I would do:** keep `.acts` on the hero in both states — it costs ~50px against 0.67 screens
of unused budget — or move `.ctx2` behind `open` so the forfeit and the route to its basis arrive
together.

## F6 · MEDIUM · VERIFIED — the "instead of" sentence now has four homes, and has already diverged
*(angle 4 — second sources of truth)*

`_src/v4_doors.tpl.html` writes `Instead of ${M.short(L.name)}:`. Each of `m1_stack`, `m2_sheet` and
`m3_hero` writes `instead of ${M.short(L.name)}` — lower case, no colon. One sentence, four copies,
already disagreeing.

Visible in the pixels: `_shots/v4_doors_12T_ppr_mid.png` reads "**Instead of Etienne:**" in the QB
and TE doors; `_shots/m1_stack_collapsed_12T_ppr_mid_390x844.png` reads "**instead of Etienne**
now −9.1 at #67 −10.4".

The whole `vsLeader()` function is copied verbatim into all three mobile templates, including the
leader's sentence "`First on the board`: X ahead of Y (POS)." So are `demandLine`, `noneText`,
`windowDoors`, `defaultOpen` and `altsHTML`. The repo states the rule against exactly this, in
`_src/shared.js` above `DOOR_SHORT`: *"Copying them into three more templates would have made four
homes for DOOR_SHORT and for the tank's prose, and the vocabulary rule gives each one (#126)."* And:
*"A SECOND POSITION VOCABULARY once lived in v4, and it disagreed with the first… Nothing made them
agree, so they drifted."*

Credit where it is due: the builder **did** hoist `DOOR_SHORT`, `doorLabel`, `doorHold`, `doorTank`
and `doorTankCap` into `shared.js` rather than copy them, and said so. That is the right instinct,
applied to the words and not to the sentences.

The divergence here is probably the *better* typography — "instead of X" is a cell lead on the
phone, not a sentence lead. The finding is not that the lower case is wrong. It is that nothing
makes the four agree, which is the state #126 describes as "right before it drifts", except that
this one already has.

## F7 · MEDIUM · VERIFIED — "lasts to #N?" is a hand-written name for a withheld quantity, and this work made three more copies
*(angle 4, 5)*

`_src/shared.js` keeps the one home for the three withheld names, with a comment saying so:
`WITHHELD_LABEL = {survival_probability: "Chance he lasts to your next turn", …}` — *"this
surface's plain-English names for the three, in one place."*

All four templates instead hand-write `lasts to #${M.NEXT_NO}?` beside the withheld word
(`m1_stack.tpl.html:211`, `m2_sheet.tpl.html:233`, `m3_hero.tpl.html:253`, `v4_doors.tpl.html:243`).
So `survival_probability` has two names on this surface, and the hand-written one is now in four
files instead of one.

**Credit, and it is real:** the three mobile templates use `${WITHHELD_WORD}` where **v4 itself
still hard-codes the literal string `withheld`** (`_src/v4_doors.tpl.html:243`). On the brief's rule
4 the phones are stricter than the north star they were measured against. And
`test_withheld_values_never_reach_the_prototype.py` only globs for the *reason* sentence
("it failed calibration against real drafts"), so neither the word nor the label is caught by a
test — this is a review matter, which is why it is here.

**What I would do:** read the label from `WITHHELD_LABEL.survival_probability`, or give "lasts to
#N?" a home in `shared.js` as that label's short form. Fix v4's literal in the same pass.

## F8 · MEDIUM · VERIFIED — m3 draws a bare ordinal beside a signed value
*(angle 6 — ordinals)*

`_src/m3_hero.tpl.html` `chipsHTML` appends `<span class="g">${ordinal(idx + 1)}</span>` to a dim
chip — the **same class** as the gap it sits beside.

`_shots/m3_hero_HEAVY_IDP_early_430x932.png`: `DL Hutchinson −112.6 6th` and
`DB Hamilton −114.1 7th`, under a header that reads "THE OTHER DOORS · AGAINST TAYLOR, THE BOARD'S
FIRST NAME". Two numbers side by side, one signed and one ordinal, under a heading about cost.
Nothing on screen says the "6th" is the door's place in the board's order rather than the player's
place on the board or his rank among remaining — the three claims this engine makes and has
confused before.

The desktop does not do this. `v4_doors.tpl.html` writes `${ordinal(…)} door`, and so do
`m1_stack.tpl.html` and `m2_sheet.tpl.html` — their chips read "**TE 6th door**", visible in
`_shots/m1_stack_HEAVY_IDP_late_360x800.png` and `_shots/m2_sheet_collapsed_HEAVY_IDP_late_360x800.png`.
m3 is the only one that dropped the noun.

**What I would do:** write "6th door". It costs about 30px of chip width, and m3 has the most
vertical headroom of the three.

## F9 · MEDIUM · VERIFIED — m3's hero is not always the board's first name, while its X says it is
*(angle 1, 8)*

`defaultOpen()` returns the leader's door unless that door is streamable, in which case it returns
the first non-streamable door. In `12T_ppr_K_DEF` the board's first name is the Rams (DEF), so the
hero is the **second** door.

`_shots/m3_hero_12T_ppr_K_DEF_mid_430x932.png`: the hero header reads "QUARTERBACK … **2nd of 6**",
Dak Prescott; the chip row carries "**DEF Rams first**" in gold. The behaviour is correct and
matches v4. What is wrong is what m3 *says* about it. The X's accessible name is
`Close the ${d.label} door and return to the board's first name` — and pressing it returns the
reader to the quarterback door. m3's stated contract ("one hero recommendation at the top, the
board's first name"; "The X returns to the board's leader") is false in this format, and m3 is the
only variant whose entire design rests on that contract.

**What I would do:** label the X for what it does — "back to the top door" — and let the hero's own
"2nd of 6" carry the explanation.

## F10 · LOW-MEDIUM · VERIFIED — what the X costs, per variant
*(angle 8)*

- **m1 — the best X of the three.** It collapses the row in place and **reveals more doors**:
  compare `_shots/m1_stack_12T_ppr_mid_390x844.png` (one door on screen) with
  `_shots/m1_stack_collapsed_12T_ppr_mid_390x844.png` (three). The reader loses demand, the wait
  line, the pool, the dearest mark, the alternative cards and the two action buttons, and keeps
  position, ordinal, hold, name, sub, value and the full three cost cells for every door. A
  collapse that gives something back will be used.
- **m2 — a clean trade.** The grid never moves; the panel clears. Lost: the wait line, demand, the
  pool, the face, the three cost cells. Kept: who, value, the signed gap and the hold line for
  every door. Collapsed still answers who / what else / at what cost; "why" thins to the hold line
  and "first".
- **m3 — a collapse that takes and gives nothing, in the state the bare URL lands in.** Compare
  `_shots/m3_hero_12T_ppr_mid_390x844.png` with `_shots/m3_hero_collapsed_12T_ppr_mid_390x844.png`:
  the hero's content is **identical**. What changes is that the gold border, the X, the
  "copy name" and "numbers" buttons and the alternatives block are gone, and a `▾` appears. The
  reader presses the only ✕ on the screen, the recommendation does not move, and the two actions
  they had are gone. (It is recoverable — tapping the hero reopens it — but that is not what a ✕
  teaches.)

**What I would do on m3:** draw the X only when the hero is not the default door.

## F11 · LOW-MEDIUM · VERIFIED — m3 is the only variant that identifies most of its doors by key alone
*(angle 3 — two sides of the same UI)*

`doorLabel` / `DOOR_SHORT` exist in `shared.js` precisely so a door's position has one spoken form,
and the comment there explains that the header's Title Case is load-bearing in Cinzel. m3's chips
draw `<span class="k2">${d.key}</span>` and put `doorLabel(d)` only in `data-tip`.

`_shots/m3_hero_LIGHT_IDP_mid_430x932.png`: "QB Hurts", "WR Watson", "**IDP** Campbell", "RB
Etienne". m1's rows and m2's tiles both spell it — "D-BACK", "D-LINE" in
`_shots/m2_sheet_HEAVY_IDP_late_360x800.png` — as every v4 door does.

The `data-tip` does not rescue this on a phone. `shared.js` binds the tip to `mouseover` and
`focusin`, and click-to-pin applies only to tips over 170 characters; the chip's tip is far shorter
and the chip is a button that does something else when tapped. So four to six of the league's doors
are identified on the main surface by a two- or three-letter key, with the word nowhere on screen.

## F12 · LOW · VERIFIED — the one number a tile or chip carries is recomputed rather than read from the model
*(angle 4)*

`_src/m2_sheet.tpl.html` `tileHTML`: `sgn(best.team_acquisition_value - L.team_acquisition_value)`.
`_src/m3_hero.tpl.html` `chipsHTML`: `sgn(b.team_acquisition_value - L.team_acquisition_value)`.

Both reproduce by hand what the model already computes as its "now" cost cell: `M.costOf` pushes
`{k:"now", v:sgn(r.dv)}` where `r.dv = a.team_acquisition_value - b.team_acquisition_value`
(`M.compare`). On the *same screen*, the panel (m2) and the hero (m3) print the model's version of
that cell. If `costOf` ever changes what "now" means, the tile and the panel will disagree in
silence.

Scoped honestly: `v4_doors.tpl.html`'s drawer row does exactly the same thing, so this is a pattern
the repo already tolerates rather than one the phone invented. I raise it because the tile and the
chip are the *only* place these two variants state a cost, which makes a silent divergence there
more expensive than in a drawer.

## F13 · LOW · VERIFIED — the compound door's label says "defense" where the engine's word is "defender"
*(angle 4 — the DOOR_LABEL shape, now in the shared layer)*

`_src/shared.js`, where the doors are built: `label: "defense (" + idpFlexOnly.join(" / ") + ")"`.
But `POS.DEF` is "defense" — the team unit, its own separate door in a K_DEF league — while
`POS.IDP` is "defender" and `DOOR_SHORT.IDP` is "Defenders". Three words for one thing, and the one
chosen for `d.label` is the word that belongs to a *different* door.

This is pre-existing and shared with v4, so it is not a mobile defect. I record it under this angle
because it is the literal `DOOR_LABEL`-says-"Receiver" shape the angle asks me to hunt, it survived
the hoist that fixed its sibling, and the mobile work gives it a louder home: `m3_hero.tpl.html`
puts `d.label` into `aria-label="Close the defense (DB / DL / LB) door and return to the board's
first name"`, which a screen reader speaks aloud.

---

# The absence contract, and what the phones do not print — checked, and clean

Recording these as checked rather than as findings, because the angle asks and because a clean
answer is worth as much as a defect:

- **No mobile template mentions `survival_probability`, `opportunity_cost` or
  `expected_value_of_waiting`.** A grep over `_src/m*.tpl.html` returns nothing.
- **Every withheld draw goes through `WITHHELD_WORD`.** A grep for a hand-written `withheld` in the
  three mobile templates returns nothing — the only hand-written copy in the directory is v4's
  (F7).
- **No `—` is swapped for "withheld" or the reverse** anywhere I could find. The only em dashes the
  three phones author are the two chip cases for a door with no name on the board, all inherited
  verbatim from `v4_doors.tpl.html`; m3's draws "no name" beside it so the claim reads. I did not
  find that path exercised in any of the 656 renders on disk, so I am **not** asserting it is wrong
  — only recording that it is the one `—` the phones author.
- **No phone prints a quantity the desktop declines to print.** I compared every `f1()` and `sgn()`
  expression in the three mobile templates against v4's. The phones draw team acquisition value,
  the positional cliff gap, the leader's margin over `M.C[1]`, and signed gaps to the leader — all
  of which v4 draws.
- **The phones drop three things v4's cards carry** — dynasty horizon, depth insurance, and the
  shared-facts line — keeping them in the numbers sheet. That is "I dont need all the variables"
  executed properly, and it is the best thing about all three card strips.

**One referent change the owner should be told about rather than discover.** v4 prices each
alternative against the **door's own best** (`sgn(c.tav - best.tav)` in the then-list;
`"−5.7 vs Etienne"` on the cards). All three phones price against the **board's first name**
instead, and drop the door's-best gap entirely except where the two coincide. Both sides label
their referent on screen, and the phone's choice is the better fit to the owner's sentence about
the engine's #1 — "not taking the engine's #1 isn't inherently wrong" means the cost a reader needs
is the cost of not taking it. But it is the same structural slot meaning a different thing on the
two sides of a UI that is required to feel like one. `MOBILE.md` flags it under "what a reviewer
should argue with"; I am arguing that it is right, and that it should be a decision the owner makes
rather than a difference he finds.

---

# Angle 1: who, why, what else, at what cost — at rest, nothing tapped

`?collapsed` is the main display the X returns to; the bare URL lands with a door open. Both are
shown, because both are states a drafter sits in.

| | who | why | what else is valid | at what cost |
|---|---|---|---|---|
| **m1** bare URL | ✓ the open door's name | ✓ **the fullest of the six states** — first-on-board, demand + basis, the wait line, the pool | ✗ **scroll** — one door fills the screen at 390x844; the open door does not itself fit at HEAVY_IDP/late@360x800 | ✗ scroll |
| **m1** collapsed | ✓ | ~ hold + first-on-board / instead-of; no wait line, demand or pool anywhere | ~ 3 of 4 at 390x844; **1.5 of 5** at HEAVY_IDP/late@360x800 | ✓ full three cells, for the doors on screen |
| **m2** bare URL | ✓ | ~ full, for the open door only | ✓ every tile sits above the panel | ✓ one signed cell per tile, unit stated once on the count line |
| **m2** collapsed | ✓ | ~ hold + "first" / gap; the wait line, demand and pool are nowhere | ✓ **best of the six states** — 4 of 5 doors begin on the first screen even at HEAVY_IDP/late@360x800 | ✓ |
| **m3** bare URL | ✓ | ✓ full, for the hero | ✓ at 390x844 (chip row on screen) · ✗ at HEAVY_IDP/late@360x800 (chips below the fold) | ✓ / ✗ with it |
| **m3** collapsed | ✓ | ✓ full, for the hero — **but see F5** | ✓ / ✗ as above | ✓ / ✗ |

**Nobody taps for "who."** The hard failure the brief names does not occur in any of the six states
I looked at, which is worth saying plainly.

The pattern that decides the verdict: **m1 and m3 answer "why" deeply for one door and make you
scroll for "what else"; m2 answers "what else" and "at what cost" completely and makes you tap for
"why".** The owner's sentence names four things and leads with "clean dissemination … over just
having as much on the screen as you can fit." Four partial answers on one screen beat one complete
answer plus a scroll, because the thing a drafter on a clock is deciding is *which door*, and that
decision needs all four names side by side. m2 is the only one that puts them there at every
viewport and every format.

---

# Verdicts

## Ship to the 72-person beta: **`m2_sheet`**

It is the only one of the three that does the thing the owner actually described. His words were
"the 4-5 main recommendations near the top. click one door, and the other positional options
populate the lower end. X in corner to collapse back to main display." m2 is that sentence,
literally: a grid of the recommendations at the top, a panel that fills below the grid, an X in the
panel's corner. m1 puts *one* recommendation near the top; m3 puts one near the top and compresses
the rest into a chip strip. REVIEW.md says where my instinct and the brief disagree, the brief
wins — and here they do not even disagree.

It also has the best numbers and the best worst case. Main display 1.00–1.30 screens, against m1's
1.11–1.96 and a 2.0 budget. At the hardest board and the smallest phone
(`_shots/m2_sheet_collapsed_HEAVY_IDP_late_360x800.png`) four of five doors begin on the first
screen, two of them complete; m1 shows 1.5 and m3 shows one.

And its count line is the most careful of the three. In the format where m3 says "showing 4" over
six visible doors, m2 says "showing 4" over four tiles and names the other two under the words
"streamable positions set aside". That is the sentence this engine's posture is built on.

Its defects — F3 and the thin "why" on the bare grid — are the two most fixable things in this
review.

## Drop: **`m1_stack`**

Not because it is badly built — it is the most structurally faithful of the three, its count line
is correct everywhere I checked, and its X is the best of the three (F10). Drop it because its
central failure is the concept rather than the execution. A vertical stack of full-height doors on
a phone will always put the rest of the league below the fold; that is what a stack is. Its own
note concedes the point ("on m1 an open first door pushes the other four below the fold"), and the
fix — showing four or five recommendations at once — is the thing that turns it into m2. It is also
the variant with the least measured headroom in both states, passing its main-display budget by
0.04 screens.

**Keep `m3_hero` alive.** It has the strongest single screen in the common case — one screen that
answers all four questions with the full "why" for the top name — and the best scroll figures of
the three (main 1.00–1.33, expanded 1.07–1.85). Its problems are F1, F8 and F9, and all three are
small edits to text and conditions, not to the design. If F1 is fixed it is the strongest
second candidate, and it is the one I would put beside m2 in a two-variant beta.

## The single change that would most improve `m2_sheet`

**Land on the bare grid — make `COLLAPSED` the default state rather than the state `?collapsed`
reaches.**

One line in `load()`. It deletes F3 outright, because the duplication exists only while a tile and
its panel are drawn together. It makes the first screen the owner's sentence exactly: the
recommendations near the top with nothing below them, and the lower end populating on a tap. It
costs nothing measured — 1.00–1.30 screens instead of 1.32–2.25 — and it buys back about 0.7
screens of budget on the state a drafter spends most of his clock in. `MOBILE.md` already names
this as "a one-line change in each template, and if a reviewer prefers it… that is the right
argument to have." I prefer it, for m2 above all, because m2 is the variant whose whole case is
that the main display *is* the four or five doors.

And I will name what to spend that freed budget on next, since it is the one of the owner's four
that the bare grid does not answer: **one line of "why" per tile.** Right now the bare grid carries
the hold line and the gap and nothing from the engine about what waiting costs — the wait line, the
demand and the pool live only in the panel. With 0.7 screens in hand, a single short wait line per
tile would complete the owner's four on one screen with no tap at all, which no variant currently
does.
