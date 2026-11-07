# CRITIQUE — FRONT 1 (design adversary) — "The Threshold"

Target: `desktop.html` (quiet, primary), `mobile.html` (quiet), `desktop_loud.html`.
Charges: **usable**, **distinctive**, **coherent across desktop and mobile**. A pass on one does not
excuse a failure on another.

Method: all three files rendered with the repo's Chromium (`browser_binary.find_chromium()`,
`--no-sandbox`) at **1280×800** and **390×664**, first viewport-height screenshotted separately
from the full page. Contrast figures below are computed from **rendered pixels of the actual
page**, not from declared tokens — the lamp and the gradients mean the declared values are not
what lands on screen. Pre-measured facts I was told to take as given (scrollH 1500 / 1795 / 1299,
min font 12.0px, min tap 44px, zero console errors) were re-observed and **all hold**.

The designer's NOTES are treated as claims throughout. Three of them are wrong; one is wrong in
the design's favour and I say so.

---

## 1. The page has no "I don't know" state, so it will tell the user "Nothing needs you." on top of five unmeasured checks. — SEVERE

**Where:** `desktop.html` / `mobile.html`, `h1#verdict` + `.eyebrow`, against `.ledger .row .v`.

**What is wrong:** the design has exactly two faces — metal at rest and metal lit — and *both of
them assert knowledge*. There is no third face for "the engine could not look." The all-clear is
therefore produced by the absence of a claim rather than by the presence of a measurement, and it
is produced at 96px.

**Evidence:** I replaced all five ledger values with `— not measured — no capture for this check`
(the page's own absence grammar, applied to every row) and re-rendered `desktop.html` at 1280×800.
The first screen is **byte-for-byte unchanged**: eyebrow `week 7 · every check the engine can run
came back clean.`, headline **`Nothing needs you.`**, one control, `CLOSE THE APP`. The five em
dashes begin at y=821 — **784px below the fold**, 1.03 viewport-heights down. A user taking the
three-second test gets a confident all-clear built on zero measurements, and the eyebrow actively
reinforces it.

The contradicting evidence exists and is the quietest object on the page: `synced 11 min ago ·
sources Fresh` is 12.5px JetBrains Mono in `--ink-3`, top-right corner, 5.25:1. When the data is
stale, the page's loudest statement and its quietest statement disagree and the loud one wins by a
factor of ~7.7 in type size.

BRIEF.md's standing rule is "a value that was not measured renders as an em dash carrying its
reason, never as a reassuring default." The ledger obeys it row by row. **The headline is the
reassuring default**, and the headline is the only thing the three-second test reads. Every
individual element here is honest; the composition is not. This is the finding a product-only
reviewer will miss, because no single mark is fabricated.

**Cost to fix:** moderate, and it costs the design nothing it values. A third state, same gesture:
metal unlit (flat `--ink-3`, no gradient, no drop-shadow), verdict `The engine could not look.`,
eyebrow naming which sources are missing, primary control becomes `OPEN IMPORT AUDIT` with
`CLOSE FOR NOW` beside it. ~40 lines of CSS and one more HTML file. The one-sentence-at-display-size
idea is what makes it cheap — it extends, it doesn't need redrawing. The structural half of the
fix is free: the verdict's lighting is currently a one-bit channel carrying a three-valued state,
so a third lighting level is the design's own logic finished rather than overridden.

---

## 2. The headline moves 108px between quiet and loud, and the two headline boxes do not overlap at all. — SEVERE

**Where:** `.threshold { min-height:calc(100vh - 96px); justify-content:center }` in both desktop
files; compare `desktop.html` and `desktop_loud.html` at 1280×800.

**What is wrong:** the three-second test is a glance at a *place*. The place changes — and it
changes in exactly the week that matters.

**Evidence** (document coordinates, 1280×800):

| element | quiet | loud | Δ |
|---|---|---|---|
| `.eyebrow` top | 306 | 198 | **−108** |
| `h1` top → bottom | **355 → 452** | **247 → 345** | **−108** |
| `.rule` top | 486 | 509 | +23 |
| `.controls` top | 544 | 561 | +17 |

Loud bottom (345) < quiet top (355): **the two headline boxes share zero pixels of vertical
overlap.** The displacement (108px) is larger than the headline's own height (98px) and is 13.5%
of the viewport. Stacked crops of the two first screens are in
`/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/adv_thr_design/v_lurch.png`
— the jump is obvious by eye, not a measurement artifact.

NOTES asserts: *"Same header, same headline slot (one line, same size), same rule, same control
row... Nothing moves that was already there; things are added beneath. That is the 'no lurch'
argument, and it holds on desktop."* **It does not hold.** Four of the five named elements move.
The cause is structural and is visible in one line of CSS: a flex column with
`justify-content:center` and a viewport-height floor cannot grow downward — adding the dek and the
figure pushes the whole group *up*.

Do they read as one *design*? Yes — same metal, same forged rule, same button recipe, same
hallmark, same ledger. Do they read as one *frame*? No. The quiet verdict sits at the optical
centre of the viewport; the loud verdict sits in the upper third. If the user learns "the answer
is in the middle," the learning is wrong precisely when it costs something.

**Cost to fix:** cheap, and it pays for finding 5 at the same time. Replace
`min-height:calc(100vh - 96px); justify-content:center` with a fixed top offset
(`padding:200px 0 72px; min-height:0`) so the eyebrow and headline pin to the same y in every
state and the dek/figure grow downward into space the quiet state leaves empty — which is the
argument NOTES already makes for the figure column, just applied to the vertical axis too. It
costs the quiet page its vertical centring, which finding 5 says it should lose anyway.

---

## 3. The one-sentence verdict slot cannot hold a plural verdict. It clips, and at three claims it breaks the page horizontally. — SEVERE

**Where:** `h1 { font-size:96px; white-space:nowrap }`, both desktop files.

**What is wrong:** the headline is sized for one specific string. The design's whole editorial
posture — promote one claim, demote everything else to "can wait" — is enforced by a
`white-space:nowrap`, not chosen.

**Evidence** (96px Cinzel, measured against the 1040px content box at 1280 viewport):

| verdict | needs | result |
|---|---|---|
| `Nothing needs you.` | 1033.95px | fits — **6.05px of slack on 1040. 0.58%.** |
| `Week 6 needs you.` | 916.6px | fits |
| `Week 10 needs you.` | 955.8px | fits |
| `Two things need you.` | 1125.5px | **overflows its box by 86px** |
| `Three things need you.` | 1209.1px | **overflows by 169px; document scrollWidth 1329 at a 1280 viewport → horizontal page scroll** |

Rendered: the headline reads `Three things need y` and runs off the right edge
(`v_s_h1.png`). Not a wrap, not an ellipsis — `white-space:nowrap` with default overflow, so it
paints past the container and drags a scrollbar onto the whole document.

Secondary, same root: the breakpoint is off by 13px. `@media (max-width:1100px)` releases the
96px size, but the headline stops fitting at **1114px**. Measured at vw=1110: `h1.scrollWidth`
1034 vs `clientWidth` 1030 — the quiet headline overflows its box across the whole 1101–1113px
band. The breakpoint was placed at a round number rather than against the type.

And 6px of slack at the design width means this breaks on a Cinzel metric revision, a user
stylesheet, or one more word. It is not a margin; it is a coincidence.

**Cost to fix:** cheap and worth it. Drop `nowrap`, reserve a two-line slot in all states (the
mobile file already proves a two-line verdict reads fine), or `clamp()` the size against the
measured string. Cost: the one-line gesture on long verdicts. Keep the one-line form for `Nothing`
and `Week N` — which is 90% of weeks — and let the plural case wrap. The alternative is a product
whose copywriter cannot say "two things."

---

## 4. There is no loud mobile, and the only artifact that shows the loud state at phone width is broken by ~4× on the brief's own budget. — SEVERE (coherence)

**Where:** missing `mobile_loud.html`; `desktop_loud.html` rendered at 390×664.

**What is wrong:** the pair is complete only in the state that required the least design. The
brief's real replayed data *is* the loud state; the quiet state is explicitly constructed. So the
phone has a finished design for the fabricated week and none for the measured one.

**Evidence** at 390×664:

- `desktop_loud.html`: **scrollHeight 5210px** against the brief's hard 1328px two-screen budget —
  **3.9× over, 7.8 screens**.
- **scrollWidth 506 vs viewport 390 → 116px (30%) of horizontal scroll.**
- The dek is clipped mid-word at the right edge; the wordmark wraps `GOLD` / `WYRM`; the seat line
  wraps to three lines (`v_desktop_loud_mob_FIRST.png`).
- The `95` figure — "exactly one number gets this size on a page, ever" — lands at y=949, **1.4
  viewport-heights below the fold**, after the buttons that ask you to act on it.

NOTES says "I did not build loud mobile (not asked) so I cannot claim it there." BRIEF.md asks for
"a **paired** desktop + mobile front page... Two files that are obviously the same product," and
hands over the week-6 data as the thing to draw. Declining the loud mobile is declining the
pairing on the half of the product that has a claim in it.

**Related, same root — the loud desktop inverts its own hierarchy below 1100px.** `.hero` collapses
to one column at `max-width:1100px`, and measured at 1100 and 1024 the `95` moves from top 381
(above the controls at 561) to top **647 — below the controls at 541**. At 1024×768, a real laptop
and iPad-landscape size, the figure is entirely below the fold (647–782 vs vh 768) and the page
grows 1795 → 2061. So at 1024 the page asks you to `OPEN MATCHUP` before it has shown you why.

**Cost to fix:** a fourth file, but most of it is already written. `.hero` → one column, the
`.row` three-column grid → one column, the strip → full width: all three overrides exist verbatim
in `mobile.html`. The hierarchy inversion is a reorder, not a redesign — move `.figure` before the
`.controls` in the collapsed grid (`order:-1`).

---

## 5. The desktop quiet page is 58% padding where the same design on mobile is 17%, and that padding slices the fold through a bordered object. — MAJOR

**This is the central risk the brief names: "too sterile, and that makes it ugly."**

**Where:** `desktop.html`, `.threshold` padding and `min-height`; the 800px fold.

**What is wrong:** the emptiness is not the idea. It is the desktop file's padding, and the
designer's own mobile file proves it, because mobile keeps every single piece of craft and is not
empty.

**Evidence** (document coordinates):

| | desktop quiet | mobile quiet |
|---|---|---|
| `.threshold` section height | **704px** (47% of the page) | **330.8px** (25%) |
| verdict group inside it (eyebrow→controls) | 299.0px | 274.8px |
| **padding, i.e. nothing** | **405px = 58% of the section** | **56px = 17%** |
| gap hallmark → eyebrow | **225.5px** | 34.0px |
| gap button → next block | **179.5px** | 22.0px |
| first-screen leaf-box area (generous upper bound) | **≤13% of 1280×800** | ≤31% of 390×664 |
| words on the first screen | 64 | 70 |

The small screen carries **more words in a quarter of the area**, with the identical components.
That is the whole argument: the desktop page is not restrained, it is under-filled, and the
content that would fill it is already written and already below the fold.

Two consequences, both visible in the render:

1. **The 800px fold cuts horizontally through the ledger head.** `.ledger-head` spans 784–821;
   `h2 "What was checked"` 784–807; the bordered `quiet state · constructed seat` stamp 785–808.
   Measured `cutBy800: True` for all three. On a default 1280×800 laptop the first screen ends with
   a half-sliced heading and **a half-sliced bordered box** in the bottom-right corner
   (`v_desktop_desk_FIRST.png`). A framed object cut in two by the viewport edge is the single
   most damaging detail on the page for an owner who already said "sterile, and that makes it
   ugly" — it does not read as a deliberate tease, it reads as a page that did not fit.
2. **The ledger's right column is 260px — 25% of the content width — and is empty on 3 of 5 rows.**
   Only `Starters` (the `constructed` stamp) and `Byes` (the strip) use it. So the ledger is drawn
   as a three-column grid with a mostly-vacant third column, which reads as structure that failed
   rather than as air. Worse in the loud state, where the same column holds *actions* (the
   `ROSTER MAINTENANCE` doors) above and *disclaimers* (`constructed`) below, so one scan column
   interleaves two incompatible kinds of object.

**Ruling on the brief's central question:** *restraint reads as luxury in the craft and as
evacuation in the desktop layout.* This is **not** a repeat of the earlier sterile page — that one
was flat colour, one type size, nothing with mass; this one has a four-stop measured gradient with
a struck shadow, a lamp, grain, a forged rule and a weighted control, and it is genuinely handsome
(see finding A below). But `desktop.html`'s first screen is ≤13% occupied with a 225px void above
the only sentence, and *that* is how this page earns "ugly" from the same person, for a new reason.
`mobile.html` is the proof that the idea survives being given enough to hold.

**Cost to fix:** the cheapest major fix here. `.threshold { padding:118px 0 72px }` → ~`90px 0 56px`
and `min-height:calc(100vh - 96px)` → `min-height:0` (which finding 2 wants anyway). That pulls the
ledger head up ~110px, clears the fold cleanly with a full first row visible, and drops total page
height from 1500 toward ~1300. Collapse the ledger's dead third column to `180px` and let the
sentence column breathe. **Costs nothing the design values.**

On the designer's own worry — *"the quiet desktop is 1500px tall for a page that says go away"* —
**that is not the defect.** 1500px is a reasonable receipt: 47% verdict, 34% ledger, 5% nav, 8%
basis. The defect is that 405px of the 704 is padding placed exactly where it bisects the ledger
head. Fix the padding and the total fixes itself.

---

## 6. Demoting navigation is defensible as an idea and botched as a desktop execution — and it is a different component on each device. — MAJOR

**Where:** `nav.rooms` in all three files.

**What is wrong:** not that the six destinations are unreachable — they are links, 44px tall,
keyboard-focusable, with a `:focus-visible` ring. The problem is that on desktop they carry **zero
affordance**, and that desktop and mobile answer "what is a destination?" with two different
components.

**Evidence:**

- **Quiet desktop first screen offers exactly 2 interactive elements**: the wordmark (`href="#"`)
  and `CLOSE THE APP`. **Zero destinations.** Same on mobile.
- First destination link: **y=1294 on desktop = 1.62 viewport-heights down**; y=926 on mobile =
  1.39. In the loud state, y=1590 = 1.99.
- Desktop `.rooms a` computed: `text-decoration: none`, `border-bottom-color: rgba(0,0,0,0)`,
  `color: rgb(169,157,135)`, `17px`. No underline, no border, no chevron, no background — six words
  in a row, immediately above a three-line italic fine-print paragraph. Rendered, it reads as a
  credits line (`v_desktop_desk_FULL.png`).
- Mobile `.rooms a` computed: `border-bottom: rgba(186,149,97,.22)` plus a `::after` chevron, full
  width, one per row. Rendered, it reads unmistakably as navigation.
- Weight given to navigation: **desktop 80px of 1500 = 5%. Mobile 270px of 1299 = 21%.** A
  four-fold difference in the same product.

So the designer demonstrably knows what a destination list should look like — it is in
`mobile.html`. The desktop colophon is the weaker half of a split the NOTES declares but whose
consequence it never states: the phone makes the doors obvious and the desktop hides them.

**Is it defensible or merely bold?** Defensible as a thesis — a page whose message is "you can
leave" should not end in a hallway of six equal doors, and removing the grid is the single boldest
and best structural decision in this design. **Merely bold as executed**, because the desktop
version removes the grid *and* the affordance, and leaves nothing in between. A dynasty player who
opens the app specifically to go to Draft Room gets a first screen whose only offer is to go away.

**Cost to fix:** cheap. Give the desktop line the mobile grammar at desktop scale: a hairline above
the row, `border-bottom: var(--hair)` on each link at rest, and a small-caps gold `rooms` label
opposite — the ledger-head pattern the page already owns. Keeps "a colophon, not a grid"; buys
back "these are doors."

---

## 7. Five of the six bye bars are below the non-text contrast floor, and two of them are not visible at all. — MAJOR

**Where:** `.strip g[fill="#755024"]` (quiet, both files) and `.strip-lg g[fill="#755024"]` (loud).

**What is wrong:** the component carrying the brief's single most important real quantity — bye
damage per week — encodes five of its six values below the threshold at which a graphic is legible.

**Evidence** (rendered pixels, against the rendered page ground beside the strip; WCAG 1.4.11 floor
for a graphical object required to understand content is **3:1**):

| strip | bar | rendered fill | CR vs ground |
|---|---|---|---|
| quiet (`desktop.html`) | wk 6, 7, 9, 10, 11 | `(101,69,32)` | **2.28 – 2.30** |
| quiet | wk 8 (the lit one) | `(186,149,97)` | 7.17 ✓ |
| loud (`desktop_loud.html`) | wk 7, 8, 9, 10, 11 | `(94–96,64–65,29–30)` | **2.10 – 2.14** |
| loud | wk 6 (the lit one) | `(230,200,136)` | 12.23 ✓ |

The quiet strip carries **no value labels at all** (shape-only, by design), so those five bars are
the *sole* carrier of their information, at 2.3:1.

And the encoding fails outright at the small end: in the loud strip **week 9's bar is 3px tall and
week 7's is 6px**, both at ~2.1:1 — effectively invisible. That is the actual reason all six bars
needed direct labels. NOTES attributes the "selective direct labels" violation to a judgement call
about the reader wanting to see 56; the measured cause is that the bars do not carry their own
values, so the labels are load-bearing, not redundant. The sentence in the `Byes` ledger row then
restates all five a third time (`the other five carry 8, 51, 4, 56 and 23`), so the same six
numbers appear three times on one page.

**Cost to fix:** cheap. Raise the non-worst fill to ~`#8a6230` (≈3.2:1) or keep `--gold-deep` and
add a 1px `--gold` top edge on every bar so a 3px bar still has a mark. Costs one notch of "one
hue, one bright thing" — and buys the rule back honestly, because once the bars are visible the
five redundant labels can come off, which is the dataviz rule the NOTES knows it broke.

---

## 8. An unknown position code renders as nothing at all. — MODERATE

**Where:** `desktop_loud.html` line 127, `.row .k .pos { background: var(--c) }`.

**What is wrong:** `var(--c)` has no fallback. Injecting a row whose `--c` is unset (a position code
nobody has styled — `IDP`, `SUPER_FLEX`, anything new from `league_usable_positions`) gives
computed `background-color: rgba(0, 0, 0, 0)`. The diamond **vanishes**, and the key is left
misaligned against the row above it, with 22px of blank where the colour chip belongs
(`v_s_pos.png` — the `DEF` row has its pink diamond, the `IDP` row has nothing).

BRIEF.md names the token for exactly this case: `absent/unknown #b0a28a`. The design never uses it.
This is the project's own red line in the CSS layer: an unknown value rendering as silence rather
than as a marked absence.

**Cost to fix:** **one character class.** `background: var(--c, #b0a28a)`. Free.

---

## 9. The only action in the "Can wait" rows is styled identically to the section headings. — MODERATE

**Where:** `.door` (line 129) vs `.ledger-head h2` (line 86), `desktop_loud.html`.

**What is wrong:** `ROSTER MAINTENANCE` — the one clickable thing in the band — and `CAN WAIT` /
`WHAT WAS CHECKED` are the same object to the eye.

**Evidence:** both are EB Garamond, `font-variant:small-caps`, `text-transform:lowercase`,
`font-weight:600`, `font-size:15px`, `color:var(--gold)`. They differ only in letter-spacing
(.18em vs .26em) and a `border-bottom:1px solid var(--gold-deep)` on the door — a hairline that
renders at roughly the same **1.3:1** as the ledger's row separators (measured `(44,36,24)` vs
`(6,6,6)` = 1.32:1). In the rendered band, four gold small-caps strings sit in one 280px section;
two are labels and two are the only doors, and nothing distinguishes them at a glance.

Compounding: `.door` has `:hover` but **no `:focus-visible`**, while `.btn` and `.rooms a` both
have the designed gold ring (`grep "focus" desktop_loud.html` → two rules, neither for `.door`).
So the one affordance the loud state relies on to keep people out of the colophon is the one with
the weakest resting state and the inconsistent focus state.

Also: `Roster Maintenance` appears **three times** on the loud page (two doors plus the colophon),
and none of the three looks like a control.

**Cost to fix:** cheap. Give `.door` the chevron the mobile colophon already uses, raise its
underline to `--gold`, and add `.door:focus-visible` to the existing rule.

---

## 10. Smaller things that are still defects

- **`.aside` is `display:none` on mobile** (`mobile.html` line 126) — the sentence *"Five checks,
  named below. Byes, holes and depth are measured against this league's own rosters"* exists on
  desktop and not on mobile. NOTES does not mention dropping it. This is the brief's "present on
  one and missing on the other without a stated reason" exactly. Low cost: it fits — mobile's
  threshold section has 22px of slack below the button and 532px of ledger beneath it.
- **The `Seen at …` label overflows the mobile button for most times of day.** Measured at 390:
  `Seen at 4:31 pm — you can go` fits in 348px exactly; `Seen at 11:41 pm — you can go` overflows
  by 1px; `Seen at 12:08 am — you can go` by 5px. The fallback was evidently only looked at once,
  at one time. Free to fix (drop the 20px side padding in that state, or shorten to `Seen 11:41 pm`).
- **The ledger's row separators render at 1.32:1** (`--hair` = `rgba(186,149,97,.22)` → `(44,36,24)`
  on `(6,6,6)`). Decorative rather than informational, so no rule is broken, but they are what makes
  five paragraphs read as a ledger. In a bright room they are gone and the ledger is five floating
  sentences. Cheap to raise to `.32`.
- **The eyebrow copy drifts between files**: `every check the engine can run came back clean.`
  (desktop, lowercase) vs `Every check…` (mobile, capitalised). Trivial, but it is two files
  maintained by hand rather than one design.

---

## What survives the attack, precisely

Not a courtesy list — these are the things I tried to break and could not.

**A. The metal headline is legible, and the designer's own worst-case figure is wrong *in the
design's favour*.** NOTES confesses *"the headline gradient's lowest ~12% dips to 2.9:1."* It does
not. Measured from rendered pixels, band by band down the h1 box, brightest glyph pixel per band:

| | top of the glyphs | middle | **lowest band with glyph mass** |
|---|---|---|---|
| quiet (`.gilt-rest`) | 13.61:1 | 7.29:1 | **4.42:1** |
| loud (`.gilt`) | 18.21:1 | 10.29:1 | **5.21:1** |

The gradient's 100% stop (`#755024`, 2.9:1) lands *below the baseline* — line-height 1.02 on 96px
puts the box bottom past the glyph bottoms, so **no glyph pixel ever reaches the deep stop.** The
AA-large floor for 96px/46px display type is 3:1; the worst measured value clears it by 47%. The
bevel is paid for and the bill is 1.5 points smaller than the designer thinks. **Keep the bevel.**

**B. The primary button's ink is fine, though the NOTES' justification is not.** NOTES says
"6.8:1 at the darkest stop." The darkest stop is `#755024`, and `#15100a` on it is **2.64:1** —
the 6.8:1 figure is against `--gold` at the 64% stop, not the darkest. But the rendered reality is
sound: sampling the actual metal under the glyph band (38–64% of the 58px button) gives
`(188,151,99)` worst → **6.98:1 minimum**, `(230,200,136)` best → 11.69:1. No defect; a wrong
reason for a right outcome.

**C. The lamp costs real contrast and nothing crosses a floor.** The designer computed everything
against `#000`; the lamp means the ground under the hero is `(30,23,14)`, not black. Measured
degradation: `.eyebrow` 7.56 → **6.38**, `.eyebrow .note` 7.86 → **6.41**, `.dek` 16.01 → **13.68**,
`.wm-sub` 7.56 → **6.57**, `.row .k` 5.41 → **5.25**, `.basis` 5.41 → **5.19**. Every body-text
element stays above 4.5:1 and the 12px/12.5px recede roles stay above it too. The headroom absorbed
the error. No finding.

**D. It is genuinely distinctive.** Strip the logo and you would not confuse this for another
dark-mode sports product. It avoids every cliché the brief names: no uniform rounded cards (there
are no cards at all), no single flat accent on near-black (a four-stop measured gradient), no
gradient *background* hero, no emoji or icon-font section markers, nothing centred. 96px Cinzel
clipped to brushed metal with a struck shadow, a forged rule carrying the logo's own diamond
ornament asymmetrically, and a ledger instead of a dashboard is **one real idea**, not an assembly
of safe choices. The brand is doing structural work: the display face *is* the verdict, not a
wordmark sitting on top of a generic layout.

**E. `CLOSE THE APP` earns the designer's claim that it is the component to keep.** It is the
product's thesis as a pressable object, it is honest in both states, it is 58px tall with a
designed focus ring, and the degraded "Seen at…" fallback is the right answer to a real browser
limitation rather than a fake one.

**F. Graceful degradation under load is better than expected.** Eight claims in the "Can wait"
band instead of two: page grows 1795 → **2329px** (+534), nothing overflows, nav lands 2.7
viewports down. A 73-character player name in a claim row: row grows to 100px, no overflow,
`docScrollWidth` stays 1280. `SUPER_FLEX` fits the 150px key column exactly. The ledger shape is
robust; it is the headline (finding 3) that is brittle, not the body.

**G. Every number the NOTES reports as measured, I re-measured and confirmed.** Min computed font
12.0px (`.wm-sub`) in all six renders; min SVG text 12px; **no interactive element below 44px in any
render**; zero console errors and zero page errors; `mobile.html` scrollHeight 1299 ≤ 1328 budget
with scrollWidth 390 = viewport (no horizontal overflow). The `background-image` fix on `.wm`
holds — Cinzel resolves correctly (`600 96px Cinzel` → true; Cinzel-rendered "Nothing needs you."
is 1033.95px vs Georgia 790.14px, so the display face is really loading, not falling back).

**H. One honest acquittal on the mobile page: this is the better of the two quiet renders.** Mobile
passes the three-second test *and* shows the first three ledger rows on screen one. It is the
design working. Every finding above about emptiness, fold-slicing and invisible navigation is a
desktop finding.

---

## The single most important change

**Build the third state.** The design signals its condition with exactly one variable — how lit the
metal is — and that variable has two values for a condition that has three: *clear*, *claim*, and
*could not look*. Until the third exists, the page's largest, most confident, most beautifully
set object will announce `Nothing needs you.` on top of five checks that returned nothing, with the
only contradicting evidence at 12.5px in the corner and the receipt 784px below the fold. This
project has withdrawn published findings rather than keep a number it could not defend; a 96px
all-clear derived from five em dashes is the same failure wearing better typography.

If you want the most repair per line changed, it is the two-line `.threshold` edit — `min-height:0`
and smaller top padding — which simultaneously stops the 108px headline lurch (2), stops the fold
bisecting a bordered stamp (5), closes the 58%-vs-17% padding gap against the designer's own mobile
file (5), and shortens the page the designer is already uneasy about. But that is craft. The third
state is correctness.

## Verdict

**Worth refining.** Not close to abandon.

The bet in the brief — that restraint can read as luxury rather than sterility — **is won on the
craft and lost on the desktop layout, and those are separable.** The materials are real: a
four-stop gradient measured off the mark, a struck shadow, a lamp, grain, a forged rule, three
faces doing three jobs with Cinzel never touching a numeral. That is not the earlier flat, muted,
technically-correct page with better type; it is a different thing, and at 46px on a phone it is
convincing. What fails is that `desktop.html` spends 405 of its 704 hero pixels on nothing, puts
zero destinations and one leave-button on its first screen, and ends that screen on a half-sliced
disclaimer box. The owner would not call this sterile for the old reason. They might call it empty
for a new one — and `mobile.html`, with the identical components at 17% padding instead of 58%,
is the counter-proof sitting in the same folder.

Findings 1, 3, 4 and 8 are correctness. Findings 2, 5, 6 and 7 are the difference between a page
that is admired and a page that is used. Six of the ten are cheap; one is a single character. The
expensive one — loud mobile — is expensive only because it was skipped, and three-quarters of its
CSS is already written.

Refine it. Then re-run the three-second test against the state where the engine knows nothing,
because that is the state this design currently gets wrong at display size.
