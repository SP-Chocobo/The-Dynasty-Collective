> **Superseded in part by `REFINEMENT.md` (2026-11-08).** These are the round-1 notes, kept as the record of
> what was decided and why. Three claims below were measured wrong by the adversaries and are corrected in
> REFINEMENT.md: the "no lurch" assertion (it did not hold — the headline moved 108px; it is pinned now), the
> headline-gradient contrast confession (rendered glyphs measure 4.42:1 / 5.21:1, not 2.9:1 — keep the bevel),
> and the primary button's "6.8:1 at the darkest stop" (wrong reason, right outcome: 6.98:1 under the glyphs).
> The copy has since been rewritten to `VOICE.md`; the headlines quoted below ("Nothing needs you.",
> "Week 6 needs you.") no longer appear on any page. The component inventory at the end still holds, with the
> additions listed in REFINEMENT.md.

# The Threshold — notes

Files: `desktop.html` (quiet, primary), `mobile.html` (quiet, primary), `desktop_loud.html` (the
real week-6 claim in the same frame). Standalone HTML, inline CSS, inline SVG, Google Fonts only.

## The one decision everything else follows from

The brief's test is "in three seconds, can I close this?" Most weeks the answer is yes. So the
quiet state is the page, not the fallback, and it was designed first. The page says one sentence
at display size — **Nothing needs you.** — and puts a real control under it: **CLOSE THE APP**.
Everything below the rule is evidence for anyone who stays.

The loud state is the same page with the light turned up. Same header, same headline slot (one
line, same size), same rule, same control row, same ledger. What changes: the sentence
("Week 6 needs you."), the metal gradient gains its specular stop, a figure column appears to the
right of the dek, a "Can wait" band appears above the ledger, and the primary control becomes
OPEN MATCHUP with CLOSE FOR NOW beside it. Nothing moves that was already there; things are added
beneath. That is the "no lurch" argument, and it holds on desktop. I did not build loud mobile
(not asked) so I cannot claim it there.

## How restraint avoids sterility (the thing the owner rejected)

The previous spare page was flat: flat colour, one type size, nothing with mass. The materials
here are all physical:

- **The metal is a gradient everywhere it appears.** The headline is Cinzel clipped to a
  four-stop gradient measured off the logo (specular → bright → body → deep) with a struck
  shadow beneath, so the glyphs read as relief, not paint. At rest (quiet) the gradient starts
  at `bright`; under claim (loud) it starts at `specular`. Same metal, more light.
- **One forged rule** under the verdict: a 1px line that fades right, struck from a four-point
  diamond — the logo's own ornament, used asymmetrically because the page is left-aligned.
- **Ground, not void.** Pure black like the logo card, with a radial lamp of `deep` at 30%
  alpha behind the headline, a 5.5% grain overlay (SVG feTurbulence, inline) so the black has
  tooth, and one faint forged coil — a 46px-stroke arc at ≤16% alpha, bleeding off the right
  edge, the only ornament allowed to be large. It is a suggestion of the wyrm's body, not a
  drawing of the wyrm.
- **Real typographic contrast.** 96px Cinzel against 19px EB Garamond against 12–17px JetBrains
  Mono. Three faces, three jobs: voice, copy, numerals. Cinzel never touches a numeral.
- **The control has weight.** A 1px gradient-metal frame around a near-black fill with a long
  drop shadow; the primary (loud) is the same frame filled with the metal and inked black.

## What I deliberately challenged in the brief

1. **The six-door grid is gone.** A page whose message is "you can leave" should not end in a
   hallway of six equal doors. The six real destinations are a single line of text at the foot
   (desktop) or a six-row list on screen two (mobile) — a colophon, not a grid. Each is still a
   ≥44px tap target. The door that matters in the loud state is inside the claim itself
   (OPEN MATCHUP; ROSTER MAINTENANCE on each thin-position row), so nobody has to go looking.
   What it bought: the first screen on both devices holds only the verdict, the rule and the
   control.
2. **The wordmark is a hallmark, not a masthead.** 17px Cinzel top-left, like a maker's stamp on
   silver. The brand's voice at size is the headline itself, set in the brand's display face
   and the brand's metal. I think this is more cohesive than a logo lockup above a page in a
   different voice, and it gives the top of the page to the only thing that matters. A 36px
   dashed ring beside the wordmark is the crest slot for the 512px transparent mark — obviously
   a placeholder, holding the diamond for now.
3. **The verdict is a sentence, not a card, not a shield, not a tick.** mock_64's green shield
   and checkmark are generic status iconography from another product. The all-clear here is
   typographic and the only colour on the page is the brand's.
4. **"Checked" is named, not scored.** The all-clear lists the five things the engine actually
   ran — starters, holes, depth, byes, record — and says what each returned, including the one
   that returned nothing (record: an em dash carrying its reason). No "100% healthy", no
   "all systems green". The eyebrow says "every check the engine can run came back clean", which
   is the only honest form of that sentence.
5. **The loud state's cost is a sentence with one number in it**, with the figure 95 set as the
   single large object on the page. I did not build a claim card. The six-week bye profile is
   drawn as a bar strip, but it supports the sentence rather than replacing it.
6. **No red.** The loud state is louder gold, not a different colour. One world. I think an alarm
   colour would have made the quiet state feel like the absence of alarm; this way the quiet
   state is the metal at rest.

## Substance: what every mark traces to

| on the page | engine source |
|---|---|
| 95 / 8 / 51 / 4 / 56 / 23 by week (loud) | `lineup_optimizer.bye_collision` — `value_lost` per week |
| "40% of the season's bye damage", "worst week 6" | `bye_concentration` — `concentration`, `worst_week` |
| "1 starter out" | `bye_collision` — `starters_out` |
| "Thin. 1 rostered / 2 rostered — bottom of the league" | `compute_readiness.thin_positions` ← `depth_ratings.depth_label` (WEAK) |
| "only 1 of 2 could be priced, so a floor" + `≥ floor` stamp | the brief's own caveat on the TE cell |
| "Average or Strong" | the literal `depth_label` strings (`Strong` / `Average` / `Weak` / `None — …`) |
| "10 of 10 filled" + `constructed` stamp | `compute_readiness` filled/total; replayed seat, per the brief |
| "No material injury on a starter" | `starter_injury_flags` gated by `is_material_injury_status` — Questionable is never mentioned anywhere |
| "Holes: none" | set difference against `league_usable_positions` |
| "Record — no capture holds a roster's result" | absent; drawn as an em dash with its reason |
| "synced 11 min ago · sources Fresh" | `league_config.describe_config_age` phrase + `recency_grade` vocabulary (Fresh/Recent/Aging/Stale/Unknown) |
| "5,357 players in the pool" | the brief's pool count |
| DEF `#ef7fc0`, TE `#ff6042` diamonds | `POSITION_PILL_TOKENS` |

Nothing is drawn as a meter. Nothing is graded. Nothing mentions ownership, odds, pick prices,
or Questionable.

**Quiet-state figures are constructed and stamped.** The brief's real seat is never quiet (DEF
and TE are thin on it), so the quiet pages draw a fabricated clean week: byes 31/26/38/22/29/20,
worst week 8 at 23%, no thin positions. Those pages carry a `quiet state · constructed seat`
stamp on the ledger head (desktop) and a `constructed` stamp in the basis line (mobile), plus
the `constructed` stamp on the lineup row that the real seat also carries. On the loud page the
only stamp is the lineup's, because everything else there is measured.

**What this design would be better with, and does not exist:** a per-source age for each of the
five checks (the manifest has source ages, not check ages — I show one sync age and one grade);
a "next week that costs anything" line (derivable from the bye profile only with a threshold the
engine has not ruled on, so I did not invent one); and a way to say "nothing changed since you
last looked" after the close control is pressed (no diff capability exists, so the button only
says "Seen at <time> — you can go").

## Measured

Rendered with the repo's Chromium (`browser_binary.find_chromium()`), `--no-sandbox`, DPR 2,
after `document.fonts.ready` with all three Google faces confirmed loaded.

| file | viewport | min computed font | horizontal overflow | scroll width | scroll height | taps < 44px | console errors |
|---|---|---|---|---|---|---|---|
| desktop.html | 1280 × 800 | 12.0px (`DYNASTY` sub-mark) | none | 1280 | 1500 | none | none |
| desktop_loud.html | 1280 × 800 | 12.0px (same) | none | 1280 | 1795 | none | none |
| mobile.html | 390 × 664 | 12.0px (same) | none | 390 | **1299** (budget 1328) | none | none |

One fault the probe could not see and only looking caught: an intermediate version rendered the
wordmark as a solid gold bar, because a `background` shorthand on `.wm` silently reset
`background-clip: text`. Every number above was green on that version. Fixed with
`background-image`; the final renders were looked at again after the fix.

Mobile first screen (0–664px) holds: hallmark, eyebrow, the two-line verdict, the rule, the
CLOSE THE APP control, and the ledger heading. The three-second test is answered without a scroll.

Contrast on `#000` (computed, WCAG 2.x): ink `#e9e0cd` 16.0:1 · ink-2 `#a99d87` 7.9:1 · ink-3
`#8a8071` 5.4:1 (captions, chart labels, ledger keys — still above 4.5) · gold `#ba9561` 7.6:1 ·
bright `#f9de99` 15.9:1 · DEF pill 8.5:1 · TE pill 7.0:1 · button ink `#15100a` on the metal
6.8:1 at the darkest stop. `deep #755024` is 2.9:1 and is used only for borders, bar fills and the
bottom stop of the large-headline gradient (see "wrong or weak"). The 17px wordmark got its own
gradient that bottoms out at `gold` so no small text runs through the deep stop.

## What is wrong or weak, honestly

- **The headline gradient's lowest ~12% dips to 2.9:1.** On a 96px (desktop) or 46px (mobile)
  glyph the average colour is far above AA-large, but the bottom edge of each letter is a deep
  bronze on black. It reads as relief, which is the point, but a strict per-pixel reading would
  flag it. The fix is to end the gradient at `gold` and lose some of the bevel; I kept the bevel.
- **The coil is a hedge.** It is faint enough not to be scenery, which also means on some
  screens it will barely register, and then the right half of the quiet desktop is just dark. I
  believe the darkness is correct for this state, but I cannot prove a first-time viewer feels
  "generous" rather than "empty" there. The loud state fills that side with the figure, which is
  one argument that the slot is real and waiting.
- **The quiet desktop is 1500px tall for a page that says "go away".** The threshold section is
  sized to the viewport so the ledger sits under the fold by design, but a cynic could call the
  ledger a second page the user never asked for. I think it is the receipt that makes the
  verdict trustworthy; the brief's "names what was checked" requirement needs it.
- **The close control cannot close the app.** Browsers only let a script close a window it
  opened. The fallback (label becomes "Seen at 8:41 pm — you can go" and the button disables)
  is honest but is a weaker gesture than the one promised. In the real front end this should
  mark the session seen server-side and, in a PWA/wrapper, actually close.
- **Six labelled bars** on the loud strip violates the "selective direct labels" rule in the
  dataviz guidance. I kept all six because the brief's data is six numbers and the reader will
  want to see that 56 (week 10) is the next-worst; the quiet strip, by contrast, is shape-only
  with the worst week named in the sentence. Hover tooltips were not built.
- **"Week 7" is an assumption.** The engine knows which week it is only through Sleeper's state;
  the quiet state needed a week to name and I chose 7 (the week after the real claim). The eyebrow
  should read the real week; nothing else on the page depends on it.
- **The thin-position doors go to Roster Maintenance.** The fix for "thin" is adding a body,
  which lives under Roster Maintenance (Free Agents is inside it). An argument exists for League
  (where the peer comparison lives). I picked the room where the action is, not the evidence.
- **The seat line is small and in mono** (`synced 11 min ago · sources Fresh`). It is the one
  place the page talks about itself; at 12.5px on desktop it is deliberately the quietest thing
  on the page, and the brief's own freshness grade is in it. If the owner wants freshness to be
  louder, this is the wrong treatment.
- **The quiet state is entirely constructed**, and I could not make that fact pretty. Two stamps
  on desktop, one on mobile. They are the correct grammar; they also sit on the page I most
  wanted to be flawless.
- **EB Garamond at 17px on black is on the light side** for people who prefer sans body copy.
  The weight is 400 and the colour is `#e9e0cd`, which is fine by the numbers, but Garamond's
  thin hairlines on pure black can sparkle on low-DPI monitors. A 500 weight would be the safe
  fallback.

## Component inventory

Named pieces, in the order they appear. For each: what it is and does; the rule that makes it
work; what it depends on, and whether it survives being lifted.

**1. The hallmark** (header: crest slot + wordmark + seat line)
- What: the brand struck small, top-left, with the roster/seat and the sync age + freshness grade
  opposite. Says whose page this is and how old the data is, without taking the top of the page.
- Rule: the mark is a stamp, not a masthead; it must never be taller than ~56px or it becomes the
  subject again.
- Depends on: Cinzel at 17/12px, the small-text gradient (never the deep stop), the 36px crest
  slot staying a placeholder until the 512px mark exists. Lifts cleanly into any layout; it is
  the most portable piece here.

**2. The verdict** (eyebrow + one-line display sentence + forged rule)
- What: the answer to the three-second test, as a sentence in the brand's display face and the
  brand's metal — "Nothing needs you." / "Week 6 needs you." The eyebrow names the week and
  carries the one honest all-clear sentence. The rule closes it.
- Rule: one sentence, one line on desktop (two on mobile), never a card, never a status icon.
  The metal's lighting (rest vs lit) is the only thing that signals quiet vs loud — not colour,
  not layout.
- Depends on: Cinzel 600 at ≥46px, the gilt gradient + struck shadow, ≥1040px of width for the
  one-line desktop form, black ground so the gradient reads as metal. **Only partially
  portable:** the sentence and rule survive anywhere, but at under ~60px or on a lit background
  the metal reads as yellow text and the whole gesture dies. Do not drop it into a dense layout.

**3. The close control** (the button, with its "Seen" fallback)
- What: the three-second test as a control. Quiet: CLOSE THE APP alone. Loud: it steps back to
  secondary ("Close for now") beside the one real door (OPEN MATCHUP).
- Rule: it is always present, in both states, and it never carries a claim it cannot back (I
  rejected "close anyway · costs 95" because ignoring a bye does not cost exactly the solved
  loss). The primary slot belongs to the one action the claim needs, nothing else.
- Depends on: the gradient-frame button recipe (1px metal, near-black fill, long shadow), Cinzel
  15px letterspaced label, ≥56px height. Portable into any layout; this is the component to keep
  if only one is kept.

**4. The ledger** ("What was checked")
- What: five rows, the same five every week — starters, holes, depth, byes, record — each with
  what it returned. In the loud state the rows that fired point upward ("— above") rather than
  repeating themselves. Carries the absence grammar: em dash with reason, `≥ floor`,
  `constructed`.
- Rule: name the check, state its result in a sentence, never a score; a row for a check that
  returned nothing is still a row.
- Depends on: a three-column grid (150px key / text / 260px right) on desktop, which collapses
  to one column on mobile; EB Garamond small caps for keys; JetBrains Mono for every numeral;
  the stamp component. Portable, and the shape most likely to survive assembly — but it needs
  ~22px of row padding to read as a ledger rather than a table, and it should sit under a fold,
  not beside the verdict.

**5. The bye strip** (six bars; shape-only in quiet, labelled in loud)
- What: the six-week bye profile as a small bar strip anchored to a hairline baseline, worst
  week in the lit metal, others in `deep`.
- Rule: one hue; the worst week is the only bright thing; the number lives in the sentence
  (quiet) or in the figure (loud), not in the chart's title.
- Depends on: ≤360px wide, mono 12px labels, black ground. Portable as a glyph; it does not
  scale up — at card size it becomes a chart, and the page has no chart in it on purpose.

**6. The figure** (loud only: 95 + caption + strip + two facts)
- What: the one enormous number, 150px JetBrains Mono 300 in lit metal, captioned in small caps,
  with the strip and "1 starter out · 40% of the season's bye damage" beneath.
- Rule: exactly one number gets this size on a page, ever; it is the cost of the claim and
  nothing else.
- Depends on: a 372px column beside a 25px dek, the headline above spanning both. **Not
  portable as-is:** it only works because the quiet state leaves that column empty, so the figure
  arrives into space that was already there. In a dense layout it becomes a KPI tile, which is
  the thing it exists to not be.

**7. The "Can wait" band** (loud only)
- What: the two thin positions as rows: position diamond in its pill colour, the position in
  mono, the sentence, the `≥ floor` stamp where it applies, and the one door that fixes it.
- Rule: "can wait" items get a door, never a primary button; the floor caveat is drawn, not
  footnoted.
- Depends on: the ledger's row grid and the stamp; position pill tokens. Portable with the
  ledger.

**8. The colophon** (six rooms as a line / a list)
- What: the six real destinations as plain text links with diamond separators (desktop) or a
  hairline list with chevrons (mobile), followed by the basis line.
- Rule: destinations recede on this page; nothing here is a card. Every link is ≥44px tall.
- Depends on: nothing structural. Portable; also the piece most likely to be rejected by anyone
  who wants the doors to be visible from across the room.

**9. The stamp** (`constructed`, `≥ floor`, `quiet state · constructed seat`)
- What: a 12px mono, letterspaced, hairline-bordered tag in `gold` on `deep`.
- Rule: one grammar for every "this number is not what it looks like" state; absence is an em
  dash with its reason, never a stamp.
- Depends on: JetBrains Mono. Fully portable.

**10. The ground** (lamp + grain + coil)
- What: black with a radial lamp of `deep`, 5.5% grain, one faint forged arc.
- Rule: the ground may have tooth and light; it may never have scenery, and the coil never
  exceeds ~16% alpha.
- Depends on: pure black and the metal palette. Portable as CSS, but the coil's placement
  assumes a left-aligned page with an empty right half; centred layouts should drop it.

**If only one survives: the close control (3).** It is the product's thesis turned into a thing
you can press, it is honest in both states, and it is the only component here that would make
any other team's page better by being added to it.
