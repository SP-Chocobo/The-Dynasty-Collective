# CRITIQUE — The Deck, design adversary (FRONT 1)

Charges: **usable**, **distinctive**, **coherent across desktop and mobile**. A pass on one does not
excuse a failure on another.

Everything below was rendered and measured in this container (Chromium via
`browser_binary.find_chromium()`, `--no-sandbox`), at 1280×800 and 390×664, in **both** the `live`
and `quiet` states, with the first viewport-height captured separately from the full page. Where I
cite a number it came out of a probe, not out of `NOTES.md`.

**Confirmed and set aside, as instructed:** the wordmark link is the only sub-44px target
(`.brand` 194.3 × **40** desktop, 153.3 × **32** mobile). Also confirmed against the designer's
claims: scrollH 1312 / 1316 desktop live/quiet, 1298 / 1303 mobile live/quiet, minimum computed
font 12.0px, zero console errors, zero viewport overflow at either specified width, and **0 of 80
distinct non-gradient text styles below 4.5:1** on desktop live. Those claims are true.

---

## 1. SEVERE — The depth ladder renders outside its own panel, on both files, in both states, at the specified viewports

**Where:** `desktop.html` `.panel[aria-label="Depth ladder"] > table.ladder`; `mobile.html`
`.panel[aria-label="Depth ladder and standing claims"] > table.ladder`.

**What is wrong:** the seven-column table is wider than the panel that contains it. The `Strong`
header and the Strong column's cells draw on top of and past the panel's right border, breaking the
frame and the rounded corner.

**Evidence:** measured against each panel's padding box —

| | table right edge | panel inner right edge | spill |
|---|---|---|---|
| desktop (live and quiet) | 438.0px | 415.0px | **23.0px** |
| mobile (live and quiet) | 379.0px | 367.0px | **12.0px** |

The `th.c` containing the text "Strong" spills the full 23px / 12px; the rightmost `.cell` spills
12px / 0.7px. On mobile the folded standing-claim row (`tr.thin.note`, *"Thin — bottom of league;
≥23 is a floor…"*) also spills 12px. `.panel` has `overflow:visible`, so nothing clips it — the
content simply crosses the border. Crops at 5× are in the scratch dir
(`/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/adv_deck_design/spill_desktop.png`
and `spill_mobile.png`); the "G" of STRONG sits on the border and the dotted row rules run out
through it.

This is invisible to the test the designer ran. `document.documentElement.scrollWidth` is 1280 and
390 because the spill lands in the 12px grid gap and over the neighbouring panel — so "horizontal
overflow: none (scrollW 1280)" is a true statement that misses a visible rendering defect at the
one width the file was built for. A self-reported measurement being *true* is not the same as it
being *sufficient*.

**Cost to fix:** 20 minutes if you only want it to stop spilling (`table-layout:fixed`, or 28px
cells). But the honest reading is that seven columns do not fit the space allotted, and the column
to delete is the `×LG` ratio — see finding 9. Fixing it that way costs the design nothing it should
want to keep.

---

## 2. SEVERE — The 1·2·5 tally is not a hierarchy. The only thing separating "needs you" from "cleared" is a 1.03:1 colour shift

**Where:** `.verdict .tally` in both files. This is the component `NOTES.md` nominates to carry the
three-second answer.

**What is wrong:** the three numbers are identical in size, weight, face, cell width and label
treatment. The *only* differentiator is hue, and the two hues have essentially the same lightness.
The largest digit on screen is always the least actionable one.

**Evidence:** measured computed styles —

| | value | font-size | colour | cell width | label |
|---|---|---|---|---|---|
| desktop | `1` | 30px | `rgb(249,222,153)` | 125.7 | NEEDS YOU, 12px Cinzel, `--ink-2` |
| desktop | `2` | 30px | `rgb(236,227,210)` | 119.2 | STANDING, 12px Cinzel, `--ink-2` |
| desktop | `5` | 30px | `rgb(236,227,210)` | 112.0 | CLEARED, 12px Cinzel, `--ink-2` |
| mobile | all three | 18px | same pair | 112.7 each | same |

Luminance contrast **between** `#f9de99` and `#ece3d2` is **1.03:1**. (Against the panel they are
14.91:1 and 15.42:1 — both maximally bright, which is the problem.) In the **desktop quiet** state
all three numbers are `rgb(236,227,210)`: `0 · 0 · 8` is three literally identical numbers, and the
one with any magnitude is CLEARED.

The headline is also 30px, so the tally's numbers are the same size as the sentence that is supposed
to outrank them. The 4× crop (`crop_desktop_tally.png`) shows the result: because `1` is a narrow
glyph, it reads as the *smallest* of the three despite `tabular-nums` giving it equal advance.

**Cost to fix:** small and worth it. One size step (e.g. 34 / 22 / 22), or demote CLEARED to a line
of prose and keep two numbers. The component is portable per `NOTES.md`; nothing else depends on its
current proportions.

---

## 3. SEVERE — The page's only chart is decorative: five of six bars render below the 3:1 minimum for meaningful graphics, while the reference line that annotates them sits at 7.07:1

**Where:** `.bye .bar svg rect` in both files; `fill="url(#dimH)"` (`#2a2219` → `#4a3b2a`) for every
row but the hot one, with `<line stroke="#ba9561" stroke-dasharray="2 3">` over the top.

**What is wrong:** the bars cannot be compared to each other or seen against the panel. The dashed
even-spread reference is brighter than four of the five bars it references — the annotation outshines
the data.

**Evidence:** computed contrast against `--panel` `#0d0b09`:

| mark | contrast vs panel | WCAG 1.4.11 needs |
|---|---|---|
| `dimH` left stop `#2a2219` | **1.25:1** | 3:1 |
| `dimH` right stop `#4a3b2a` | **1.82:1** | 3:1 |
| dashed mean line `#ba9561` | 7.07:1 | — |
| hot row `goldH` right stop `#f9de99` | 14.91:1 | — |

And the geometry makes it worse. The mobile bar column is **84px** wide, so the rendered bars are:
WK6 84px, WK7 **7.1px**, WK8 45.1px, WK9 **3.5px**, WK10 49.5px, WK11 20.3px. WK8 (51) and WK10 (56)
differ by 4.4px at 1.82:1 — indistinguishable. WK9 (4) is a 3.5px sliver narrower than its own `rx=2`
corner radius. In the **quiet** state all six mobile bars fall between 30.9px and 38.9px: six
identical grey blobs, where the brightest thing in each cell is the reference line running through it.

A 1:1 crop of the desktop bar column is at `bars_1x.png`. At true size it conveys exactly one fact —
"week 6 is big" — which the 95 beside it already said, in a brighter colour, in less space.

The bar column costs **206px of the 722px bye panel (28.5%) on desktop** and **84px of 342px (25%)
on mobile**, and duplicates the number sitting immediately to its right. The owner asked for
"graphs or charts or something". A chart that is not readable does not discharge that request; it
spends the budget and returns the appearance of having spent it.

**Cost to fix:** two options, both cheap. (a) Raise the dim fill to ≥3:1 — about `#5a4833`→`#7a6446`
— which keeps the bars and costs the "one saturated hue per panel" rule nothing, since these are
already brown. (b) Delete the bar column entirely and let the number and the who-list carry the row.
(b) is better and pays for finding 4 — see the closing recommendation.

---

## 4. SEVERE — The mobile budget fails on ordinary data, by 2–4× the headroom the designer estimated

**Where:** `mobile.html`, whole page. Hard constraint: ≤1328px (2 × 664).

**What is wrong:** the 30px of headroom is held by the fixture happening to contain unusually short
surnames. It does not survive real ones, and it does not survive a worse week.

**Evidence:** measured `scrollHeight` at 390×664 under four conditions.

| condition | mobile scrollH | vs 1328 budget | desktop scrollH |
|---|---|---|---|
| as shipped (Gibbs / McLaurin / Pitts) | 1298 | −30 | 1312 |
| **realistic long surnames** (Smith-Njigba, St. Brown, Harrison Jr., Pittman Jr., Vanderschaaf, Westbrook-Ikhine) | **1380** | **+52 OVER** | 1322 |
| **full names** (`Marvin Harrison Jr.`) | **1416** | **+88 OVER** | 1366 |
| **eight standing claims instead of two** | **1381** | **+53 OVER** | **1797** |
| every value absent | 1298 | −30 | 1298 |

Three of the four ordinary variations break the one constraint the brief calls non-negotiable. The
overrun comes from the `.who` column wrapping to a second line.

Two compounding details:

- **Desktop lineup slots truncate.** `.slot .n` has `clientWidth` **63px** against a 12px face.
  "Smith-Njigba" needs 77px, "Vanderschaaf" 79px, "Harrison Jr." 68px — **6 of 10 slots clip to
  ellipsis**, with no `title` attribute, so the name is simply unrecoverable. With full names all ten
  slots read "Marvin …". The brief's ask is "clean **who**"; the who is the first thing cut.
- **Eight claims is the backwards direction.** `.stand` is a fixed 2-column grid with no cap, so the
  worse the week, the more you must scroll to see what is wrong. Desktop goes to 1797px — 2.25
  screens — for the week that most needs a one-screen answer.

**Cost to fix:** the structural fix the designer already named (one fewer mobile panel) plus a
sensible cap on claim cards. Verified partial remedy: removing the bar column (finding 3) under the
long-surname load takes mobile from 1380 → **1338**, recovering 42 of the 52px. Still 10px over, so
the bar column is where the headroom lives but it is not the whole answer on its own.

---

## 5. SEVERE — Four of the ten ruled position tokens are undefined. An IDP position pill computes to black text on a transparent background

**Where:** the `:root` token block in both files.

**What is wrong:** `BRIEF.md` publishes ten position colours plus an absent/unknown fallback and says
"one home, do not invent others". Both files define six and omit `DL`, `LB`, `DB`, `IDP`. Because
`.pos{background:var(--c);color:#000}` resolves `var(--LB)` to nothing, `background` becomes invalid
at computed-value time and falls back to `transparent` while `color` stays black.

**Evidence:** probed in both files, identically —

```
--QB #2a81fc  --RB #0ca89c  --WR #4aa8ef  --TE #ff6042  --K #fab87e  --DEF #ef7fc0
--DL (UNDEFINED)  --LB (UNDEFINED)  --DB (UNDEFINED)  --IDP (UNDEFINED)
--absent #b0a28a   <- defined, and never used as a fallback

.pos with --c:var(--LB)  ->  background rgba(0,0,0,0)   color rgb(0,0,0)
.pos with --c:var(--IDP) ->  background rgba(0,0,0,0)   color rgb(0,0,0)
.pl i  with --c:var(--LB) -> background rgba(0,0,0,0)
```

Black on `#0d0b09` is **1.0:1**. In an IDP league every position pill in the depth ladder and every
colour swatch in the bye ledger, the lineup grid and the mobile chip row disappears — not degrades,
disappears. The colour-coding that three separate components depend on is silently gone.

**Cost to fix:** four token lines and one `var(--c, var(--absent))`. Ten minutes. There is no design
argument on the other side; `--absent` is already in the file for exactly this.

---

## 6. MAJOR — The four-state value grammar, which the designer nominates as the one component to keep, is violated five times in the shipped desktop live state

**Where:** `desktop.html` bye ledger `.pl .v` (Bass, Knox, Borregales), `.slot .v.dash` (Bass),
`.ladder td.num .dash` (K row). `mobile.html` ladder K row.

**What is wrong:** `NOTES.md` component 4 states the rule: *"`—` absent followed by an italic reason
… A dash never stands alone."* On the page as shipped, five value dashes stand alone, and four of
them are not even painted in the absence role — they render in `--ink-3`, the recede role, which on
this page means "less important", not "not measured". That is basis collapse: an unmeasured value
drawn identically to a de-emphasised measured one.

**Evidence:** every value em-dash on the page, classified by computed colour and by whether a reason
is attached:

| file | value dashes | fail the design's own rule | not using `--absent` |
|---|---|---|---|
| desktop live | 15 | **5** | **4** (all `rgb(141,129,112)` = `--ink-3`) |
| mobile live | 8 | 1 | 0 |

The failures: `Bass —`, `Knox —`, `Borregales —` in the bye ledger's who-column; `Bass —` in the
Lineup grid; `2 · — 0 of 2` in the depth ladder K row ("0 of 2" is a count, not a reason). The reason
for the first three exists — "— unpriced" — but it is in the legend four rows and ~300px below.

The footer on the same screen reads *"— absent, carrying its reason"*. The legend is the indictment.

Mobile is markedly better here (1 of 8), which is itself a coherence problem: the same grammar is
enforced to two different standards on the two devices.

**Cost to fix:** trivial — add `class="dash"` and a `.why` to four spans. Worth doing precisely
because this component is the best idea on the page and the one thing a dense page needs to be
allowed to be dense.

---

## 7. MAJOR — The quiet state reports a different number of cleared checks on each device, with no stated reason

**Where:** `.cleared` / `.ok` rows and `.tally` / verdict prose, quiet state, both files.

**What is wrong:** the same quiet week says 8 on desktop and 6 on mobile.

**Evidence:** rendered row counts and the number each page states —

| | cleared `.ok` rows rendered | number the page states |
|---|---|---|
| desktop live | 5 | tally `1 · 2 · 5` ✓ |
| mobile live | 5 | tally `1 · 2 · 5` ✓ |
| desktop quiet | **8** | tally `0 · 0 · 8` ✓ |
| mobile quiet | **6** | prose "0 need you, 0 standing, **6** cleared below" ✓ |

Each page is internally consistent — the designer's stated rule, *"the tally's three numbers must
equal the rows below"*, holds within each file. It does not hold **between** them. Mobile silently
drops two checks: *"Picks: every original round still held, nothing moved"* and *"Thin positions:
none"*. Neither the page nor `NOTES.md` mentions the omission, and `NOTES.md`'s mobile section lists
five deliberate cuts — these two are not among them.

This matters more than a row count. The cleared list is the design's answer to "what did the engine
actually check", and the answer differs by device.

**Cost to fix:** either restore the two rows (+~34px, which the budget in finding 4 cannot absorb) or
state the cut on the page. The second is free and honest.

---

## 8. MAJOR — The quiet state is longer than the live state. The page tells you to close the app and then hands you more page

**Where:** both files, `body[data-state="quiet"]`.

**What is wrong:** the brief's thesis is *"most weeks the honest answer is 'nothing needs you' — and
that is the feature."* The design's response to a quiet week is to show you **three more rows and
four more pixels** than the week something needed you.

**Evidence:**

| | live | quiet | delta |
|---|---|---|---|
| desktop scrollH | 1312 | **1316** | +4 |
| mobile scrollH | 1298 | **1303** | +5 |
| cleared rows (desktop) | 5 | **8** | +3 |

The CLOSE THE APP control — lifted from `mock_64` and correctly identified in `NOTES.md` as the best
single idea in the prior round — is placed at the top of a 1316px wall of ledger. On desktop quiet it
also sits beside the tally rather than replacing it, so the page offers a dismissal and a
three-number scoreboard in the same breath (`desktop_quiet_fold.png`).

The designer's defence — *"the densest honest version is the list of checks the engine actually
ran"* — is a good argument for *having* the list. It is not an argument for the quiet state being the
longer of the two. Collapse it behind the CLOSE control and the idea gets stronger, not weaker.

**Cost to fix:** moderate; a disclosure on the cleared list in the quiet state. It costs the "look at
all the work the engine did" demonstration, which is a real loss — but it buys the product's own
thesis, which is worth more.

---

## 9. MAJOR — The depth ladder encodes severity by horizontal position only, and spends 45% of its width doing it

**Where:** `.ladder td.c .cell` / `.cell.on` / `.cell.on.weak`, both files.

**What is wrong:** you cannot tell Weak from Strong by looking at a row. You must find the lit box,
count which of four columns it is in, and read a 12px `--ink-3` header several rows above. There is
no redundant encoding — no valence, no label echo, no directional cue. The one visual difference the
design *did* build between Weak and Average is below the threshold of perception.

**Evidence:**

| mark | contrast vs panel | note |
|---|---|---|
| empty `.cell` border `rgba(186,149,97,.22)` | **1.38:1** | 18 of 24 cells on screen |
| `.cell.on` fill (Average) | **2.11:1** | below the 3:1 non-text minimum |
| `.cell.on.weak` fill | 3.69:1 | |
| `.on` vs `.on.weak` **against each other** | **1.75:1** | the Weak/Average distinction |
| border `.on` `#ba9561` vs `.on.weak` `#f9de99` | 2.11:1 | |

Geometry: the four-cell block is **169.6px of the 381px table (44.5%)** on desktop and **154.2px of
356px (43.3%)** on mobile. So the largest graphic element in the panel is 18 near-invisible empty
rectangles plus 6 lit ones that cannot be told apart by appearance. The 4× crop
(`crop_desktop_ladder.png`) shows TE's Weak cell and QB's Average cell as visually the same object.

**On the `×LG` column, which the designer asked to have ruled on:** it is doing real work and it is
in the wrong place. `0.59` versus `1.02` is the only mark on the row that actually distinguishes TE
from QB at a glance — and it is painted in `--ink-3`, the dimmest role on the page (5.15:1 on panel,
4.88:1 on the tinted thin rows), at 12px, 49.2px wide. The brightest 45% of the panel can't
discriminate; the dimmest column can. That is a priority inversion, not a precision overclaim. My
ruling: **keep the ratio, cut four cells to two or restyle them.** It does not read as a 0–100 score —
it is tagged `·n` when it falls back to bodies and the footnote states the thresholds — and deleting
it would leave the panel with nothing legible in it.

**Cost to fix:** this is the one finding that costs the design something. The four-cells-never-a-meter
rule is the right instinct and deleting it would be wrong. But four boxes is not the only honest way
to draw four discrete states — a four-step notch on a short track, or the label word itself set in the
position colour, is equally discrete, legible at a glance, and ~90px narrower. Rebuilding that cell is
half a day, and it also resolves finding 1.

---

## 10. MODERATE — `desktop.html` has no responsive behaviour at all and begins overflowing horizontally at 1260px

**Where:** both files. `grep -c '@media'` returns **0** for each.

**Evidence:**

| viewport width | `scrollWidth` | horizontal overflow |
|---|---|---|
| 1440 | 1440 | — |
| 1280 | 1280 | — |
| **1260** | 1261 | **+1px** |
| 1200 | 1251 | +51px |
| 1152 | 1251 | +227px… (1024) |
| 768 | 1251 | +483px |

The top bar's six doors are a 740px fixed-width `flex` row with `white-space:nowrap`, so nothing can
compress; below `.wrap`'s 1240px max-width the whole page gains a horizontal scrollbar. `NOTES.md`
anticipates this (*"below ~1180 the labels need to go icon-only"*) and ships no breakpoint; the real
failure point is **1260**, 80px higher than estimated and 20px below the one width tested.

I am ranking this moderate because the brief specified two fixed targets and the pair meets them. But
the third charge is *one product across devices*, and there are ~870px of viewport between 390 and
1260 with no design in them — a 1194px iPad in landscape, a 1152px laptop, a half-screen window. Two
fixed-width artefacts that share a palette is exactly the failure mode the charge names.

**Cost to fix:** one breakpoint collapsing door labels to icons, plus letting `.row-1` / `.row-2`
stack. A few hours. Nothing conceptual is at risk.

---

## 11. MODERATE — The desktop freshness axis is 93px away from the tracks it scales, with two track-less rows in between

**Where:** `desktop.html` `.panel[aria-label="Data age"]`, `.fr` rows and `.axis`.

**Evidence:** last track bottom edge y=783; `.axis` top edge y=876; **gap 93px**; the two rows between
are *"League sync — nothing synced for a replayed seat"* and *"Season proj. sums — coverage not
carried by this fixture"*, neither of which has a track. The `7d / 30d / 90d` labels therefore sit
directly beneath a row that has no axis, and read as belonging to it (`desktop_quiet_fold.png`).

Mobile's single-track variant — three marks on one axis with labels drawn inside the SVG — does not
have this problem. That the compressed version is the correct one and the roomy version is the broken
one suggests the five-row form should be retired rather than repaired.

**Cost to fix:** small — move the two absent rows below the axis, or adopt the mobile single-axis form
on desktop too, which would also make the two files more obviously one product.

---

## 12. MODERATE — Mobile's usable first screen is 608px, not 664, and one of the two "standing" claims is under the nav bar at load

**Where:** `mobile.html` `nav.doors`, `position:fixed; bottom:0; height:56px`.

**Evidence:** the bar's top edge is at y=**608** in a 664px viewport. **13 text elements** are
occluded by it at first paint, among them the TE depth row (`TE`, `23`, `1/2`, `0.59`) and the
beginning of its folded claim note (`Thin`, `23`). So on the phone, at the moment the three-second
test is running, one of the two things the verdict band calls *standing* is half-buried under the
navigation.

The 1328px budget is a page-height budget and still holds as stated. But the *first screen* — the only
thing the three-second test is about — is 608px of readable content, 8.4% less than the number the
design was planned against.

**Cost to fix:** `padding-bottom:60px` already exists on `body`; the issue is only that the fold
boundary was computed as 664. Re-plan the fold at 608 and the ladder's first thin row moves up. Low
cost, but it changes which panel the fold cuts through.

---

## 13. MINOR — The contrast self-report measures a colour no element on the page is painted in

**Where:** `.gold` (`-webkit-background-clip:text`) on `.wordmark .wm`, `.verdict h1`, `.ph h2`.

**What is wrong:** `NOTES.md` reports *"gold body ≥ 6.4:1"*. That measures the flat `--g-body`
token. No `.gold` element is painted in `--g-body` — every one is painted with
`linear-gradient(180deg, #fff4ce 0%, #f9de99 28%, #ba9561 62%, #755024 100%)`, whose terminal stop is
`#755024` at **2.74:1** against `--panel`.

**Evidence:** computed and bisected —

| gradient stop | contrast vs `--panel` |
|---|---|
| `#fff4ce` (0%) | 17.85:1 |
| `#f9de99` (28%) | 14.91:1 |
| `#ba9561` (62%) | 7.07:1 |
| `#755024` (100%) | **2.74:1** |

The gradient crosses 4.5:1 at **81% of glyph height** and 3:1 at **97%**. The 30px `h1` has the
large-text allowance; the **14px `.ph h2` panel headings do not** — at 14px bold the threshold is
4.5:1 throughout, and the bottom fifth of every panel heading is beneath it.

In practice the area-weighted perception is fine and the headings are legible (I could read every one
in every render). I am ranking this minor because of that. It is listed because the reported number
is not a measurement of the thing on the page, and this review was commissioned on the premise that
self-reported numbers are claims.

**Cost to fix:** move the terminal stop to ~`#8f6630` and nothing visible changes. Minutes.

---

## 14. MINOR — The review toggle leaves the reader at the bottom of the page

Switching `live` → `quiet` from the in-flow footer control keeps scroll position, so the state you
just asked to see opens at its last panel. My first quiet captures came back mid-page because of it.
`NOTES.md` already says the control should not ship. Noted for completeness only.

---

## What survives the attack, and why

This section is not politeness. These are the expensive parts and they are done.

**Strip the logo and it is still this product.** I rendered desktop with `.brand` hidden
(`nologo_desktop.png`). Cinzel in a brushed-gold gradient for every panel heading, Source Serif 4 for
prose, mono for every single numeral, and gold plus the position pills as the only saturated hues —
that combination is not what any other dark-mode sports product looks like. Competitors are
sans-throughout with one accent. The brand is doing material work, not sticker work, and the
designer's trade (40px corner mark instead of a 350px hero) is the right one. **This passes the test
properly, which is rarer than it sounds.**

The caveat, stated as hostilely as it deserves: the *structure* underneath is still seven uniform
`border-radius:10px` 1px-bordered cards on near-black, which is on the brief's own cliché list. The
distinctiveness lives entirely in the type and palette layer. Swap Cinzel for Inter and the gold for
cyan and this is `mock_62`. That is a real limit, not a fatal one.

**The four-state value grammar is a genuine idea.** `≥` generated by `.floor::before` so it cannot be
forgotten is a good mechanic — the kind of thing that survives being handed to someone else. The
absence strip (six dashes, one shared reason, drawn in the same frame and type as a measured block)
is the right answer to "absent, not zero" and it reads correctly. Finding 6 is a failure *of
application*, not of the idea.

**The row-ledger shape beats a column chart, and the WK 6 row is the best thing on either page.**
Week · number · *who sits, with what they are worth* answers the owner's "clean who, why, at what
cost" in one line. The note — *"RB room is two deep for two RB slots: nothing backfills him, so his
whole price is the loss"* — explains why 95 is 95 without asserting a cause the engine cannot
support. That is the hardest sentence on the page to write and it is written correctly.

**Every-value-absent survives.** scrollH 1298 → 1298 (mobile) / 1312 → 1298 (desktop), no overflow,
layout intact, nothing collapses. Most dense layouts fall over here. This one does not. (It does
expose that `.floor::before` and `.dash` are not mutually exclusive — an absent floor renders `≥—`,
"at least unmeasured" — but that is a guard to add, not a structure to rebuild.)

**On the three-second test, specifically.** It passes at one bit and fails beyond it. Measured on the
first screen alone:

| | verdict band height | share of fold | numerals in the verdict | numerals competing below it | visible text runs | characters |
|---|---|---|---|---|---|---|
| desktop live | 166px | 20.7% | 7 | **64** | 182 | 1,910 |
| mobile live | 185px | 27.8% | 7 | **47** | 101 | 732 |

The verdict band has **not** been swallowed — it is top, framed, gold-ruled, and "One thing needs
you." at 30px Cinzel is unambiguously the most prominent object on the page. In three seconds you can
decide whether to close the app, which is the literal test and it passes.

What you cannot do in three seconds is anything else. The *why* is a three-line 16px serif paragraph
(reading, not scanning). The *how much* is a tally with a 1.03:1 internal hierarchy. 90% of the
numerals on the first screen are outside the band that is supposed to triage them. The one element
that genuinely rewards scanning is the hot WK 6 row — full-bright bar, 15px gold `95`, tinted row —
and it works. So the page rewards scanning in exactly one place and demands reading everywhere else.

---

## The single most important change

**Move the magnitude into the verdict band, and pay for it by deleting the bar column.**

One trade, and it closes four findings at once. The verdict band currently holds seven numerals of
which none is at display size except a tally that cannot rank itself; the bar column holds six marks
of which five are below the legibility floor and all six duplicate the number beside them. Put `95`
and `40%` into the band at the size the tally numbers currently occupy, give the tally a real size
step or drop CLEARED to prose, and take the 206px desktop / 84px mobile back from the bars and give
it to the who-column.

Measured consequence of the second half alone: under the realistic-surname load, mobile goes
**1380 → 1338**, recovering 42 of the 52px budget overrun. The first half is what turns a
three-second *headline* into a three-second *answer*.

## Verdict

**Worth refining** — but the refinement is not cosmetic, and I would not call this close to done.

The case for refining: the two expensive things are already right. A type and colour system that is
identifiable with the logo removed, and an absence grammar that lets a dense page be dense without
lying, are the parts that take taste and cannot be specified. Both are here. The row-ledger is a
better shape than any of the six prior mocks found.

The case against complacency, which is the finding I would put in front of whoever decides: **roughly
a third of this page's graphic area currently carries information a person cannot read.** Five bars
at 1.25–1.82:1, eighteen empty cells at 1.38:1, three tally numbers separated by 1.03:1, and a
Weak/Average distinction at 1.75:1. Density is only a defensible bet if every pixel pays, and these
do not — they spend the budget and return the *appearance* of having spent it, which is the same
failure mode as a fabricated panel wearing a different coat. Add to that a page that overflows its
own panel at the width it was built for, a mobile budget that breaks on six ordinary surnames, four
missing position tokens that make an entire league format invisible, and a quiet state that is longer
than the loud one, and this is not a design one pass from shipping.

Every one of those is fixable without touching the two things worth keeping. That is why the answer
is refine and not abandon. But the next pass needs to cut, not tune: the bar column, two of the four
depth cells, and the quiet state's length. The designer's own instinct in `NOTES.md` — *"the mobile
budget is held by copy length, not by structure"* — is correct and understated by a factor of two to
four. Structure is what has to give.
