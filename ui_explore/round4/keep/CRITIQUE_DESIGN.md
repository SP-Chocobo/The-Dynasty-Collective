# CRITIQUE — FRONT 1 (design adversary) — "The Keep"

Target: `ui_explore/round4/keep/desktop.html`, `mobile.html`, both states.
Method: rendered myself in Chromium via Playwright at 1280×800 and 390×664, first-viewport and
full-page captured separately, pixel-sampled from the 2× renders, plus six injected stress states.
Scratch artefacts (screenshots, measurement JSON, probe scripts) are in
`/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/adv_keep_design/`.

Everything below is measured off a render. Where `NOTES.md` made the same claim, I say whether the
measurement agrees — several of its numbers are right and two are wrong.

---

## 1. The frame hierarchy is inverted at render. The two subordinate claims are more brightly framed than the summons.

**Where** — `desktop.html`, `.gonfalon>.rod` (line 120) against `.frame>.skin` (line 113); visible
at 1280×800 as the summons vs the two `.block` cards in the right column.

**What is wrong** — The design's whole thesis is that frame shape carries severity. The channel a
reader actually uses at a glance — how brightly a panel is outlined — runs the opposite way.

**Evidence** — Sampled from `d_live_fold.png` at 2×, top edge, horizontal centre of each frame:

| frame | role | top-edge peak luminance |
|---|---|---|
| gonfalon (summons) | "the one thing that needs you" | **L123** (y+1), L164 (y+2) |
| cut-stone block (DEF) | standing claim | **L222** |
| cut-stone block (TE) | standing claim | **L222** |
| carved tablet (ledger) | facts, no claim | L37 |

Cause is mechanical: `.gonfalon>.rod` carries `box-shadow:0 1px 0 #000,0 2px 3px rgba(0,0,0,.8)`,
and the rod sits at `top:-6px` with `height:5px`, so its own 2px/3px-blur shadow lands exactly on
the frame's top gold edge and darkens it by 45%. The rod itself measures L222 at y−4 and y−2; the
edge it is meant to hang goes dull immediately beneath it.

The squint test (`squint_d_live_fold.png`, 7px Gaussian on the 1× fold) shows the consequence: at
low frequency the right column reads as two brightly-framed lit objects and the summons reads as an
unframed dark field with text in it.

**Cost to fix** — One declaration. Replace the rod's downward shadow with an upward one
(`0 -1px 0 #000`) and let the frame's own skin reach full brightness, or give `.gonfalon>.skin` a
brighter gradient than `.block`'s. Costs the design nothing; it is currently paying for a shadow
with its own hierarchy.

---

## 2. Severity-by-shape does not rank on its own, and on desktop the one unambiguous shape cue is below the fold.

**Where** — the four frames in both files; `s_shapes_1x.png` is the controlled test.

**What is wrong** — Stripped of their contents and given identical copy at identical width, the four
shapes do not produce the intended order, and the one shape cue that is genuinely unambiguous — the
gonfalon's pointed hem — is not on screen when the three-second test happens on desktop.

**Evidence** —

- Controlled test (`s_shapes_1x.png`): four frames, same width, same sentence. The chamfered block
  (B, "standing claim") reads as the most finished and most lit object. The gonfalon (A) reads as
  *ceremonial*, not urgent — a banner is what a herald hangs, not an alarm. The arch (D) at panel
  width is a dome that crowds its own first line. Only the tablet (C) does its job unambiguously:
  it is plainly the quietest.
- Geometry: on desktop the gonfalon spans y=353.9→1111.0. Its hem occupies y=1057→1111. The fold is
  at 800. **The hem is 257px below the first screen.** Above the fold the gonfalon's only shape
  cue is the rod, a 5px horizontal gold bar — and the first 360px of the page already contains four
  other horizontal gold bars (`.rule.fade` at y≈110, `.wall .rail` at y≈142, two `.sect i` hairlines
  at y≈333). The rod does not read as "this one is hung"; it reads as the fifth rule.
- What actually ranks the summons above the fold is conventional: panel width (772 vs 372), headline
  size (34px vs 16px) and a 64px gold numeral. Those work. The shape system is not doing the job
  claimed for it.
- The inverse holds on mobile, which is the interesting part: the mobile gonfalon ends at y=584.3
  inside a 664px viewport, so the hem *is* visible, and there the banner reads. **The shape grammar
  works on the small screen and fails on the large one.**

**Cost to fix** — Keep the shapes; stop asking them to carry rank alone. Cheapest honest fix: put
the gonfalon's distinguishing geometry at the *top* of the panel (a shaped head under the rod)
rather than 750px down at the bottom, so the cue and the claim arrive together. That costs the
banner silhouette, which is the design's prettiest single gesture — a real loss, worth arguing about.
Fixing finding 1 first may buy enough rank that this can be left alone.

---

## 3. The quiet state breaks the design's own shape grammar.

**Where** — `desktop.html:395` and `mobile.html:302`: `<article class="frame block q">` wrapping
"No position is thin".

**What is wrong** — `.block` is defined in `NOTES.md` as "cut-stone block … standing claims (thin
positions)". The quiet state uses that exact frame to say **there are no standing claims**. The
shape asserts the presence of the thing its contents deny.

**Evidence** — The table in `NOTES.md` ("Severity is carried by the SHAPE of the frame") assigns one
shape per severity, four shapes, and the quiet state has five things to say. Rendered side by side
in `d_quiet_fold_1x.png`, the "No position is thin" panel is the same chamfered cut-stone block as
"Thin at DEF" in `d_live_fold_1x.png` — same corners, same edge, same 12px chamfer, same L222 edge.
A reader who learned the rule from the live page learns the wrong thing from the quiet one.

**Cost to fix** — Free. Use the tablet (facts, no claim), which is exactly what "no position is thin"
is. Or make it a laurel on bare ground with no frame at all, which would also stop the quiet state
looking like a page of cards with their contents removed.

---

## 4. Mobile deletes most of the absence grammar and three of five ledger rows, unannounced.

**Where** — `mobile.html:309–314` (the ledger), `mobile.html:319–324` (door names),
`mobile.html:227–233` (lintel), `mobile.html:247–258` (the chart), `mobile.html:290` (the DEF claim).

**What is wrong** — This is the coherence charge, and it is the sharpest failure in the pair. The two
files give materially different accounts of what the engine knows, and mobile gives the weaker one
on precisely the axis this project says it cares about most.

**Evidence** — Element inventory taken from both live renders:

| | desktop | mobile |
|---|---|---|
| ledger rows | 5 — Lineup, Holes, Hurt, Record, Picks | **2** — Lineup, Record |
| em-dash absence markers | 3 | **1** |
| absence "why" clauses | 5 | **1** |
| door sub-lines ("standings · trades" …) | 6 | **0** |
| chart provenance caption | 1 | **0** |
| DEF claim's consequence sentence | present | **deleted** |
| lintel "League · — name not in this capture" | present | **deleted** |

Two specific consequences, not just a count:

- **A measured fact is pulled under a CONSTRUCTED stamp.** Desktop renders `Holes · None · every slot
  has a rostered body who can fill it` as its own unstamped row. Mobile folds it into
  `Lineup · 10 of 10 filled, no holes [CONSTRUCTED]`. On mobile, "no holes" now sits inside the
  stamp's scope. The design's own rule ("a constructed value is stamped where it is shown") makes
  that read as "no holes is constructed too". Desktop says it is measured.
- **The door sub-lines are the design's entire answer to a question it was asked.** `NOTES.md`
  component 8: "the sub-line names what lives *inside* (trades, free agents, standings) so those do
  not need doors of their own." That is the justification for having six doors instead of thirteen.
  Mobile deletes all six sub-lines, so on mobile there is no indication anywhere that Standings
  lives inside League or Free Agents inside Roster Maintenance. The stated reason is unmet on half
  the product.

`NOTES.md` has a section naming what does not survive compression. It names the pilasters and the
lintel-at-size. It does not name any of the seven rows above. The designer's honesty list omits the
single largest difference between the two files.

**Cost to fix** — The three missing ledger rows cost ~105px of mobile scroll against a 32px budget,
so they cannot simply be restored (see finding 8). The honest fix is a collapsed "three more facts,
all absent, with reasons" disclosure row at ~40px, or moving the ledger behind a tap. Either costs
one interaction; neither costs the look. The door sub-lines can return as a single line under the
grid rather than six.

---

## 5. Five of the six chart bars fail non-text contrast by roughly half. The chart is a table wearing a chart's clothes.

**Where** — `.bar .f` in both files (`desktop.html:169`, `mobile.html:115`),
`background:linear-gradient(180deg,#4a4237,#2e2921)`; `.bars` bottom rule at `var(--mortar)`.

**What is wrong** — WCAG 2.1 SC 1.4.11 requires **3:1** for graphical objects needed to understand
content. The bars are the content. They measure 1.28:1 to 1.93:1.

**Evidence** — Sampled from `m_live_full.png` at the vertical midpoint of each bar against its own
background in the same column:

| bar | WK | height | measured RGB | contrast vs ground |
|---|---|---|---|---|
| 1 | 6 (worst) | 63.0px | (172,135,85) | **5.24:1** |
| 2 | 7 | 7.0px | (55,49,40) | **1.53:1** |
| 3 | 8 | 44.6px | (60,53,44) | **1.63:1** |
| 4 | 9 | 3.5px | (48,43,35) | **1.40:1** |
| 5 | 10 | 48.9px | (59,53,43) | **1.62:1** |
| 6 | 11 | 20.1px | (59,52,43) | **1.60:1** |

Top-of-bar samples run 1.28:1 – 1.93:1. The axis line (`--mortar #2a241b` on `--stone #0d0b09`)
computes to 1.28:1 — the chart's baseline is invisible too. `NOTES.md`'s contrast table lists only
text roles and omits every graphical element on the page.

The design consequence is larger than the compliance one. `NOTES.md` §6 argues at length for
labelling all six bars because "hiding four of them behind hover … would be worse". The page has in
fact become the table the note was arguing against — not as a chosen trade, but because the marks
do not render. Confirm it in `squint_m_live_fold.png`: at 4px blur, one gold column and six numbers
survive; the five grey bars are gone. Desktop spends 299.5px of panel height (and mobile 142.8px)
on a comparison the sentence two lines above already makes in words: "the next worst week costs 56".

**Cost to fix** — Lift the recede fill to ≥3:1 (around `#5a5247`) and the axis with it. That costs
some of the hush, which is a genuine part of why this page looks good — a real trade, and I would
still make it. The alternative, defensible on desktop where the chart is 100% below the fold
anyway, is to cut the desktop chart and keep the mobile one.

---

## 6. Desktop spends 44% of its first screen before the first pixel of the claim; the crest wall costs 186px to present six 12px words.

**Where** — `desktop.html`, `nav.wall` (lines 297–307) and `.lintel` (286–293).

**What is wrong** — The three-second test is about the first screen, and on desktop the first 354px
of it — 44% — carry no triage information at all.

**Evidence** — Measured y-extents at 1280×800:

```
0    –  110   lintel (brand)
112  –  298   wall of six crests            186px, 23% of the fold
298  –  354   section-label band
442  –  484   the headline finally appears
502  –  566   "95"
807            first chart pixel — 7px BELOW the fold
```

Gold-pixel distribution in the first screen (hue 24°–58°, S≥0.22, V≥0.30, counted per 50px band):
the crest band (y 100–200) holds **≈11,200** gold pixels; the "95" band holds ≈2,100 after
subtracting frame edges. **The navigation emits roughly five times the gold of the hero number and
sits 370px above it.** 45% of all gold ink above the fold is spent on brand plus crests.

What that 186px buys: six 12px Cinzel words and six engraved charges that are not labelled anywhere
except by those words. A plain 44px name rail would present the same six destinations and return
142px — which is almost exactly the 150px the bye chart needs to clear the fold.

The pair contains its own proof. `NOTES.md` §1 says the brief's lineage put the doors at the bottom
and that this design rejected that on desktop because "an app needs its rooms reachable before the
scroll". Its own mobile file puts the doors at the bottom (`nav.wall` at y=947.6) and gets the
better first screen: mobile shows the badge, kicker, headline, 95, unit, sentence, button **and the
complete bye chart with its week labels** inside 664px. Desktop, with 136px more viewport height and
890px more width, shows no chart at all. The layout the designer argued against wins on measurement,
on their own page.

**Cost to fix** — Moving the crest wall below the main grid on desktop costs the design the single
most distinctive composition it has (a lintel, then a wall of arms, then the hall). That is a real
loss and I would not pretend otherwise. The cheaper half-measure — drop the crests to 44px and put
names beside rather than beneath them — returns ~120px and keeps the wall. Either is worth doing;
leaving the desktop first screen as it is is not.

---

## 7. There is no state for "a claim exists and its cost was not measured."

**Where** — the `.gonfalon` summons in both files; the absence grammar is implemented only in
`.tablet .row`.

**What is wrong** — The page has two states, live and quiet. The third real state — the engine has a
claim but could not price it — degrades into a broken live state that still asserts urgency.

**Evidence** — Injected: hero value → `—`, bar values → `—`, bar heights → 0
(`s_m_absent_1x.png`). The result still reads `NEEDS YOU · 1 of 1`, still reads `Week 6 is the one
that hurts.`, still prints `TRADE-VALUE POINTS LOST THAT WEEK` beside a 48px gilded em dash that
renders as a short gold rule rather than a value, still gilds the `WK 6` label as the worst week,
and still offers `OPEN MATCHUP`. Six bars sit at their 3px `min-height` floor under six em dashes.

The brief's absence grammar is implemented where it is cheap — five ledger rows, each with its
reason — and not implemented at all on the one panel that makes a claim. That is the defect in
miniature: absence handled where it costs nothing, skipped where it costs a layout.

**Cost to fix** — One more frame state and a rule that the gonfalon cannot render without its
number. Small, but not free; it needs a sentence written for it.

---

## 8. There is no slack, and the two most likely additions both break something.

**Where** — `mobile.html`, whole page.

**Evidence** — measured, not claimed:

| injected state | mobile scrollH | vs 1328 budget |
|---|---|---|
| as shipped, live | 1296 | −32 |
| one more thin position (3 claims) | **1370** | **+42 over** |
| two more (4 claims) | 1444 | +116 over |
| five more (8 claims, as the brief asks) | **1740** | **+412 over, 31%** |

So the two-screen rule holds for exactly two standing claims. `NOTES.md` says this ("The page has no
slack for a third standing claim") and the measurement agrees — credit where due. What the note
does not say is that each claim costs 74px, so the failure is not an edge case: a third thin
position is an ordinary week.

Second likely addition, from `NOTES.md`'s own list of things it wants: naming the starter who sits.
A normal name reflows fine (`Amon-Ra St. Brown` in the kicker keeps it at one line, 35px, scrollH
unchanged at 1296 — genuinely robust). But the proposed slot is wrong. The kicker is 12px Cinzel,
uppercase, `.18em` tracked — the design's own type rule says Cinzel is for inscriptions, "never more
than six words at a time". A proper noun in letterspaced small caps is harder to read than the 22px
headline beside it, and a long one wraps to two lines
(`s_m_longname_1x.png`: "BYE COLLISION · CHRISTIAN / MCCAFFREY-WILLIAMSON SITS"). The owner's
standing constraint asks for "clean who, why". **The page currently names no player anywhere, and
the slot the designer nominates for the "who" is the one slot on the page that cannot carry a name.**

**Cost to fix** — The name wants the headline or a line in Source Serif directly under it, not the
inscription band. Finding a 74px-per-claim saving on mobile is the harder half.

---

## 9. Unknown or unstyled position codes have no drawn state, and the ruled token for them is dead.

**Where** — `.pos` / `#posshield` in both files; `--pos-none:#b0a28a` at `:root`.

**Evidence** — `grep -c pos-none` returns **1** in each file: the declaration. Nothing consumes it.
Only `--pos-te` and `--pos-def` are referenced in markup (4 and 2 times each); the other eight ruled
tokens are declared and unused, which is fine, but the *absent/unknown* one having no consumer is
not — it is the one the brief rules for a case the design will certainly meet.

Injected `SFLEX` with `--c:var(--pos-flex)` (undefined):

```
badge text width   36.0px   inside a 30px shield   -> overflows both edges
computed colour    rgb(236,228,210)   (= --ink, inherited)
svg stroke colour  rgb(236,228,210)
```

`color:var(--c)` with `--c` undefined is invalid-at-computed-value, so it inherits ivory. The result
(`s_m_unstyledpos_1x.png`) is an ivory shield with text spilling past its outline that looks like a
legitimate position token rather than an unknown one. A design whose first rule is "absence must
carry its reason" renders an unknown position as if it were known.

**Cost to fix** — Trivial: `--c: var(--pos-xx, var(--pos-none))` plus a 3-character cap on the badge
and an overflow rule.

---

## 10. On mobile, three of the six crests hang from nothing.

**Where** — `mobile.html`, `.wall .rail` (line 144): one absolutely-positioned bar at `top:12px`
over a `repeat(3,1fr)` grid of six.

**Evidence** — `crop_m_wall.png`. Row one hangs from the rail. Row two has its three rings and no
rail above them; they float in black. The conceit `NOTES.md` calls the navigation's whole idea —
"escutcheons hung by rings from a forged rail" — is half-true on the platform where it costs the
most (214.4px of a 1296px page, 17%).

**Cost to fix** — Trivial: a rail per grid row, or draw it as a repeating row background.

---

## 11. The quiet state hands you 300px of invented chart under a button that says CLOSE THE KEEP.

**Where** — `desktop.html:348–360`, `mobile.html:269–281`.

**Evidence** — Desktop quiet: gate spans y=353.9→967.0 (613.1px). `CLOSE THE KEEP` is at y=583.5.
Below it, from ~680 to 967, sits a six-bar chart of numbers the page itself stamps CONSTRUCTED,
plus a caption. `NOTES.md` §5 names mock_64's close-the-app affordance as "the best single idea in
all six" and rebuilds it — then puts the largest fabricated object on the page directly underneath
it. The control says go; the layout says stay and read 300px.

This also means the quiet state's dominant content element is the only wholly invented one. It is
stamped, which is the grammar working. But "honest about being fabricated" and "the biggest thing
on the screen" should not be the same object.

**Cost to fix** — Free, and it improves the idea: delete the quiet chart, or put it behind a
"show me why" link under the button. The quiet state should be shorter than the live one; today
desktop quiet is 1146px against live's 1413px, which is the right direction but 613px of it is one
mostly-empty arch.

---

## 12. Craft defects — small, each visible at render

- **The left finial touches the pilaster.** `NOTES.md` says "the gonfalon rod's finials sit 6px from
  the desktop pilasters". Measured gold runs at y=348.5 along x: finial **32.5→49.0**, pilaster
  **30.0→32.5**. The gap is **0px**; they are adjacent and the crop (`crop_d_finial.png`) shows the
  rail meeting the diamond's tip. The self-report is wrong by its own metric.
- **The CONSTRUCTED stamp wraps on desktop too**, not only mobile as `NOTES.md` admits.
  `crop_d_ledger.png`: the Lineup row runs three lines, with `· a replayed` orphaned after the
  stamp box and `seat, not a live roster` on a third. The stamp mid-paragraph reads as a button.
- **The Picks absence reason is not a sentence**: "— not in this capture · counts only, never
  prices, when it is". On a page whose premise is legible honesty, one of five absence reasons is
  ungrammatical.
- **The triage counts are the weakest ink on the page.** `.sect .count` is `--ink-3` at 13px/12px —
  the designer's declared "one recede role", which `NOTES.md` says is "used only at 12–14px for bar
  values and door sub-lines". It is also on `1 of 1` and `2`, the two tokens that directly answer
  "does anything need me". And `1 of 1` has no readable denominator; it parses as "page 1 of 1".
- **Zero `:focus` rules in either file** (`grep -c ':focus'` → 0, 0), against 12 and 11 interactive
  elements. `NOTES.md` says "The crests hover-lift and glow; that is the entire interaction model" —
  `mobile.html` contains **zero** `:hover` or `:active` rules, so on mobile that model does not
  exist and a tapped crest gives no feedback at all.
- `h1 → h3`, no `h2`, in both files.
- The quiet chart's `role="img"` label is `"Constructed even bye profile"` — the six values are not
  in the accessible name, where the live chart's are. A screen-reader user gets a chart with no data
  in exactly the state the page claims to be most careful about.

---

## What survives attack

Not nits — these are the things I tried to break and could not.

- **Text contrast, recomputed independently against the grounds the text actually sits on** (not
  `#000`, which is what a naive check would use — the stone is painted by `.skin:after`):
  `--ink` 15.5:1, `--ink-2` 8.8:1, `--ink-3` **5.07:1** on stone and **4.78:1** on the gonfalon's
  lighter top (`#171309`), gold label 7.07:1, TE 6.55:1, DEF 7.92:1, black-on-gold button 7.56:1.
  Every text role clears 4.5:1 on its worst ground. `NOTES.md`'s figures are accurate.
- **The mono-numeral rule holds absolutely.** I walked every text node containing a digit in all
  four states and read its computed `font-family`: 30 / 19 / 25 / 19 nodes, **zero** non-mono. The
  `6` inside the Cinzel headline is mono. This is the hardest rule in the brief and it is kept
  without exception.
- **No horizontal overflow, and it is not an artifact of suppression.** `mobile.html` sets
  `body{overflow-x:hidden}`, which would normally make a no-overflow claim unfalsifiable. Removing
  it leaves `scrollWidth` at **390** and no element with a right edge past 390. The claim is real.
- **Reflow under long strings is sound.** A 54-character league name in the desktop lintel reflows
  to two right-aligned lines with no overflow and no scrollH change (`s_d_longleague_1x.png`).
- **The mobile first screen is genuinely good**, and better than the desktop's: lintel, section
  label, position badge, kicker, headline, 95, unit, sentence, button, and the entire bye chart with
  week labels, inside 664px, with the gonfalon's hem visible to mark it. `m_live_fold_1x.png` is the
  strongest single artefact in this pair.
- **Distinctiveness holds, but by craft, not by palette.** Measured hue distribution of the desktop
  first screen: **92.8% near-black, 6.0% gold, 1.1% ivory, 0.129% every other hue combined** (1,319
  pixels — the two position badges). By pixel count this *is* "one accent colour on near-black", the
  cliché the brief names. What rescues it is the carving: a 74px engraved wyrm, a gilded Cinzel
  lintel with a rule-and-diamond, gradient metal that is actually a gradient, four distinct panel
  silhouettes, and a hard display/mono/text split. Strip the wordmark and you would still not
  mistake this for any other dark sports product. The `NOTES.md` defence — "the position tokens are
  the only non-gold hues and they mean *which position*, never *how bad*" — is true and should be
  read for what it is: a 1,319-pixel exception, carrying a real rule.
- **The things the designer flagged as their own worst problems are not the worst problems.** The
  SVG wyrm is a perfectly serviceable 44–74px crest and nothing on either page depends on the raster
  arriving. Mobile's crests at the bottom is the *right* call, and the measured position is y=947.6,
  not the 1050 claimed. Both admissions are safe ones. The expensive findings are the ones above:
  the inverted frame brightness, the shape system that does not rank, the seven content classes
  mobile drops silently, and the bars that do not render.

---

## The single most important change

**Make the summons the brightest-edged object on the page.** Today its two subordinates are
(L222 vs L123, measured at the top-edge centre), because the rod's own drop shadow falls on the
frame it hangs — and the gonfalon's one unambiguous severity cue, the hem, sits 257px below the
desktop fold where nobody sees it during the three seconds the whole design is built around. One
declaration fixes the brightness. Fix it before touching anything else, because it is cheap, because
it is the only defect that actively points the reader at the wrong panel, and because the entire
claimed idea — severity carried by the frame — is currently being contradicted by the frames
themselves.

## Verdict

**Worth refining.** Not close.

The reasons are measured, not atmospheric: every text role clears 4.5:1 on its real ground, every
numeral in all four states is mono, the 12px floor holds, there is no overflow and it is not hidden,
the mobile first screen carries the claim and the whole chart inside 664px, and the page is
genuinely unmistakable with the wordmark removed. That is a better measured baseline than anything
in `_ref/`, and `mock_60`'s castle-behind-the-headline and `claude_c_brand`'s 9.6px type are both
beaten outright.

The defects are mostly cheap. Findings 1, 3, 9, 10 and 11 are a few lines each and cost the design
nothing it should want to keep. Finding 5 costs some hush. Findings 4, 6 and 8 are the expensive
ones, and they share a single shape: **the desktop page is the weaker half of this pair, and the
mobile page already contains the fix.** Mobile puts the claim first and the doors last and gets more
substance above the fold than desktop does with 136 more pixels of height. Desktop's 354px of
ceremony before the first claim pixel is the one decision in `NOTES.md` defended on taste
("an app needs its rooms reachable before the scroll") that the designer's own other file disproves.

The thing I would protect through any revision is the carved lintel and the mono/Cinzel discipline.
The thing I would stop defending is the idea that four frame shapes rank anything by themselves.
They are good flavour. They are not a hierarchy, and the page is currently relying on them to be one.
