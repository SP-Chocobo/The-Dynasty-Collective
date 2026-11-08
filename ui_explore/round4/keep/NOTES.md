# The Keep — notes

> **Refined after the adversary pass.** `REFINEMENT.md` records what was taken, rejected and
> deferred, with re-measured numbers. Where this file was wrong (attributions below, the
> "bottom of league" sentence, the TE badge, `Seat 5`, the footer's claim about the engine, the
> bar chart, the quiet chart) it has been corrected in place; the measured table at the end is
> the refined one.

Pair: `desktop.html` (1280 wide, two columns) and `mobile.html` (390 × 664, one column).
Both carry a `View a quiet week` toggle in the plinth that swaps the live roster for the
quiet state, so the four screens (live/quiet × desktop/mobile) are in two files.

## The one decision everything else follows from

The place is carried by **joinery, not scenery**. There is no photograph, no painted hall, no
dragon silhouette behind the text. The world lives in:

- **forged rules** — a 2–3px brushed-gold gradient with a dark line under it and a faint
  specular line below that, so it reads as a bar in relief, not a border;
- **pilasters** (desktop only) — two thin vertical gold rails with capital and base diamonds
  that make the 1232px column a bay in a wall;
- **four frame shapes** that carry severity (below);
- **a wall of six heraldic crests on a rail**, hung by rings, as the navigation.

Everything inside a frame is near-black stone (`#0d0b09` → `#141109`), ivory ink, and gold
only for inscriptions, the one hero number, and the worst-week bar. The castle photograph
behind mock_60's headline is the thing I most wanted to beat: here the headline sits on a
flat 15.5:1 surface and the atmosphere is in the edge of the panel it sits in.

## The KIND of a panel is carried by the shape of its frame; its rank by size and edge

| frame | shape | edge | used for |
|---|---|---|---|
| **gonfalon** | hung from a rod with two finials, pointed hem | brightest (`--metal-hi`, L255) | the first rung the claim ladder returned |
| **cut-stone block** | chamfered corners, flat base | dimmer (`--metal-lo`, L186) | standing claims that can wait |
| **carved tablet** | plain joinery, inset mortar edge | mortar (L3) | the ledger — facts, no claim |
| **gate** | arched top, open base | — | the quiet state: nothing is open, go |

(Refined: the first pass claimed the shapes ranked by themselves. The design adversary measured
that they do not, and that the rod's own shadow had made the subordinate blocks brighter than
the summons. Rank is now carried by width, headline size, the hero numeral and edge brightness,
all in the same order as the shapes; the shapes carry the *kind* of thing a panel holds.)

So the page has no coloured severity stripe and no red/amber/green. The position tokens
(`TE #ff6042`, `DEF #ef7fc0`) are the only non-gold hues on the page and they appear only in
the small heraldic position badge, where they mean *which position*, never *how bad*. A
greyscale print of this page still ranks its claims.

The gonfalon's pointed hem on desktop is 28px deep across ~770px, which reads as a banner
hem rather than a shield point; on mobile it is 18px. The shapes are two stacked `clip-path`
polygons (a gold layer and a stone layer inset 2px), so the frame is CSS, not an image, and
resizes with content.

## Type

- **Cinzel** only for inscriptions: the wordmark, section labels, the two headlines, door
  names, ledger keys, button labels. Letterspaced `.14em–.22em`, 12–34px, never more than
  six words at a time, never a number.
- **JetBrains Mono** for every numeral a reader must read: the hero `95`, the bar values,
  `WK 6`, `10 of 10`, `1 of 2 priced`, the pool size, the seat number. The `6` in the headline
  is set in mono inside the Cinzel line so "WEEK 6" cannot render as "WEEK G" or Roman.
- **Source Serif 4** for prose. Deviation from `design_system.FONT_SANS` (Segoe UI); a
  system sans next to Cinzel is what made the current page "sterile". A sturdy text serif at
  15–17px carries the warmth without pretending to be the display face.

## What the page says, and where each thing comes from

Everything drawn traces to the BRIEF's *Real* table:

| on the page | source |
|---|---|
| "Week 6 is the one that hurts", 95, the six marks, 237 | `lineup_optimizer.bye_collision` (`bye_profile.weeks`, `total_loss`) |
| "40% of the season's bye cost" | `bye_concentration` (0.401) |
| "Jahmyr Gibbs, RB, sits … no bench player fills the slot" | `roster[].bye == worst_week` ∩ `starters`; `worst_week_detail.starters_out = 1`, `bench_used = 0` |
| "— now: not in this capture" | `current_week: null`, `front_claims.byes_ahead` |
| Thin at DEF (1) Weak by count; Thin at TE (2) Weak by value | `depth_chart.positional_depth` + `depth_ratings.depth_label` (a ratio band, ≤ 0.7× the mean; **no rank exists**) |
| `≥ 23 · 1 of 2 priced` | `valued_count` / `depth_value_label` — the floor is on the value, the count is exact |
| Lineup 10 of 10, stamped CONSTRUCTED | `optimize_lineup` + `slots_from_roster_positions` in this fixture (`compute_readiness` only in production) |
| Holes: none; "week 6's bye leaves one empty" | `lineup_optimizer.slot_coverage` (**not** `league_usable_positions`); `bench_used = 0` |
| Record: — absent, with its reason | `league_standings` — no capture holds it |
| Picks: — not in this capture, "acquired or given away, never priced" | `build_pick_ledger` is diffs only; prices withheld |
| Hurt: — not measured | `is_material_injury_status` needs `slot == "Starter"`, which a constructed lineup lacks |
| Fresh: — not in this capture | `build_freshness_manifest` / `recency_grade`, reachable, not captured |
| Seat 1 · Team 1; 5,357 players ranked | `_provenance.seat`, `_provenance.universe_rows` |

The absence grammar is on the page in all four states: a measured value (95), a floor
(`≥`), a constructed value (`CONSTRUCTED` stamp on the seat, the lineup and the quiet
bye profile), and absence (`—` followed by its reason, in the same cell, never a `0`).

No grade, no rating, no odds, no meter, no ownership, no Questionable, no pick price.

## Where I challenged the brief, and what it bought

1. **The doors are the navigation, not a footer.** The brief's lineage (mock_60/61) and
   `claude_c_brand` put the six doors at the bottom as a "quick access" grid after the
   content. On desktop I hung them on a rail directly under the lintel. An app needs its
   rooms reachable before the scroll, and a wall of crests under the lintel is exactly the
   place a keep hangs its arms. Cost: the headline starts at y≈455 instead of ≈300. It is
   still fully inside the first 800px with the hero number, the sentence and the button,
   so the three-second test holds. On mobile the wall goes to the end of the scroll — see
   weaknesses.
2. **The wordmark is a lintel inscription, not a hero.** 30px Cinzel, 74px mark, 110px of
   header on desktop; 19px / 44px / 64px on mobile. mock_60 spends ~250px on it. The brand
   is carried by the metal and the crests, not by a billboard.
3. **No sidebar, no league switcher, no search/bell/gear.** Those were in mock_60/61; none
   is a destination that exists, and the front page is a triage surface, not a shell.
4. **Hero number in mono, not Cinzel, and gradient-gilded.** Numbers never in the display
   face; but the gilding keeps the one number on the page that is the claim's cost inside
   the brand's metal.
5. **The quiet state is a different frame, not an empty version of the live one.** The
   gate arch + `CLOSE THE KEEP` (mock_64's one good idea, rebuilt without the fabricated
   health ring and positional meters) makes "nothing needs you" a thing the page *says*,
   with a control, in the same slot the summons occupies.
6. **The bye chart labels every bar.** The dataviz guidance says label selectively. Six
   values that *are* the data, in a chart whose job is "where does the cost land", are a
   table in disguise; hiding four of them behind hover on a page meant to be read in three
   seconds would be worse. The worst week is the only one in primary ink; the rest recede.
7. **Bars are 24px / 20px thick with air around them** rather than mock_60's slab columns.
   They read as a measured series rather than a rampart.

## Things this design wanted that the engine does not have (findings, not drawings)

- **Who sits in week 6.** The summons says "a starter sits"; it would be twice as strong
  with the name and position of the starter whose bye causes the 95. `bye_collision` solves
  the lineup with byes removed — whether it exposes *which* starter was removed is not in
  the brief's data, so the headline stays anonymous. If the engine can name the starter,
  that name belongs in the kicker where "Bye collision · a starter sits" is now.
- **"Other valid options, at what cost."** The owner's standing constraint asks for
  alternatives. The front page has no alternatives data; the only honest form is "what it
  costs to ignore" (95). Options live in Matchup / Roster Maintenance. A front page that
  showed "cheapest cover for week 6 costs N" would be better, and that quantity does not
  exist on this surface.
- **Freshness grade and per-source ages** are real (`build_freshness_manifest`) but the
  replayed capture carries none, so the page does not draw them. The ledger has an obvious
  sixth row for them when a live roster is behind the page.
- **Depth labels for the non-thin positions** (`Strong / Average / Weak / None`) are real
  and are not on the page: the brief's roster only names the two thin ones, and drawing
  the other labels without data would be invention. The cut-stone block is the natural
  frame for a four-step discrete depth row if the owner wants it; it must never become a bar.

## Measured (Chromium via Playwright, fonts loaded from Google Fonts) — refined pass

| | desktop 1280×800 | mobile 390×664 |
|---|---|---|
| computed minimum font size | **12px** (DYNASTY, stamps, section labels) | **12px** (DYNASTY, week labels, stamps) |
| horizontal overflow | none (`scrollWidth` 1280) | none (`scrollWidth` 390, no `overflow-x:hidden`) |
| total scroll height, live | 1475px | **1294px** (budget 1328 — 34px to spare) |
| total scroll height, quiet | 1099px | 998px |
| tap targets under 44px | none | none |
| digits outside the mono face | 0 | 0 |
| frame top-edge peak luminance, summons / block / tablet | 255 / 186 / 3 | 255 / 186 / 4 |
| chart marks (ivory dots) vs ground; stems and axis | 12.7:1; 3.2:1 | 12.7:1; 3.2:1 |
| fonts resolved | Cinzel, Source Serif 4, JetBrains Mono | same |

Contrast, computed from the hex values:
`--ink #ece4d2` 15.5:1 on stone · `--ink-2 #b8ac96` 8.8:1 · `--ink-3 #8c806d` 5.1:1 (the
one recede role, used only at 12–14px for bar values and door sub-lines) · gold label
`#ba9561` 7.1:1 · TE `#ff6042` 6.6:1 · DEF `#ef7fc0` 7.9:1 · button text `#000` on
`#ba9561` 7.6:1. Nothing on the page is below 4.5:1.

What is in the first mobile screen (0–664px): lintel, "Needs you", the TE badge and
kicker, the headline, 95 and its unit, the sentence, OPEN MATCHUP, and the top of the
chart. The claim and its route are both above the fold.

## What is wrong or weak — honestly

- **The wyrm is a stand-in.** It is a hand-built SVG coil with blade spikes and a head; it
  reads as a dragon at 44–74px and as a decent crest, but next to the real brushed-relief
  raster it is a cartoon. The symbol is isolated (`#wyrm`) so the raster drops in with no
  layout change. I would not ship this mark.
- **Mobile puts the rooms at the bottom.** The six crests survive the compression well
  (3 × 2, 46px crests, names at 12px Cinzel), but they are 1050px down. The alternative — a
  fixed bottom rail of six nameless crests — would steal 56px of a 664px viewport and
  present six hieroglyphs. I chose the scroll. A real app will probably want a persistent
  rail anyway, and at that point the names should come back as a label under the active
  crest only.
- **32px of mobile budget to spare is thin.** One more ledger row or a wrapped headline
  on a longer league name breaks the two-screen rule. The page has no slack for a third
  standing claim; if three positions are thin, the third should collapse into "+1 more"
  inside the second block rather than a third block.
- **The CONSTRUCTED stamp wraps onto its own line in the mobile ledger** because 12px mono
  letterspaced caps cannot be made narrower without going under 12px. It costs 26px and
  looks slightly like a button. Acceptable, not good.
- **The gonfalon rod's finials sit 6px from the desktop pilasters**, and the "NEEDS YOU"
  section rule runs under the left finial. It is a near-collision that reads as intentional
  only because it is symmetric. Tightening the hall by 10px would fix it.
- **Doors are inert.** No active state, no counts (e.g. "2 thin" on Roster Maintenance),
  because the only counts I could truthfully put there are the two already on the page.
  The crests hover-lift and glow; that is the entire interaction model.
- **The quiet bye profile is invented** (24 21 26 19 23 22) and stamped CONSTRUCTED on
  the page, as the grammar requires. It is still a drawn number; a real quiet week should
  be replayed from a real roster before this goes anywhere near a user.
- **The chart has no hover layer and no table view.** On a static mock that is fine; in
  the real front end each bar wants a tooltip ("WK 8 · 51 pts · which starters") and the
  `role="img"` label should become a real table.
- **Cinzel at 12px** for section labels and door names is at the floor the brief sets. It
  is legible because it is caps and letterspaced, but it is the size I would raise first
  if the floor were 13.

## Component inventory

Each piece as it would be lifted into an assembled version. "Depends on" is honest.

**1. Forged rule** (`.rule`, `.wall .rail`, the gonfalon rod)
- A 2–3px horizontal gold gradient with a black line beneath and a faint specular line
  beneath that; optional centre diamond. Separates bands and hangs things.
- Rule: it is *relief*, not a border — the shadow pair is what makes it metal; a 1px
  `#ba9561` line is a different, flatter object.
- Depends on: the five gold stops and a black ground. Fully portable; works at any width.

**2. Heraldic frame set** (`.frame` + `.gonfalon` / `.block` / `.tablet` / `.gate`)
- Two stacked `clip-path` layers (gold skin, stone skin inset 2px) and a content body.
  Four shapes carry four severities.
- Rule: severity is carried by frame shape, never by a coloured stripe, so it survives
  greyscale and spends no hue the position tokens need. Only one gonfalon per page.
- Depends on: the gold gradient and stone gradient tokens; a container ≥ 320px (the hem
  and chamfers are fixed px, so below that the chamfers eat the padding). The gonfalon
  rod is positioned 12px outside its box and needs that outside room. Lifts cleanly.

**3. Summons** (the gonfalon's content: kicker, Cinzel headline with mono numeral, gilded
hero number + unit, one sentence, one route)
- Carries the one thing that needs the user, its cost in one number, and where to go.
- Rule: exactly one, exactly one number, exactly one route, and it is the first rung
  `front_claims.compose` returned — not "urgent". The sentence must contain the share (40%)
  and the runner-up (56); the "who" line names the starter from `roster ∩ starters`; the
  `— now:` line renders `current_week`'s absence in the four-state grammar. The gonfalon may
  not render without its number: a `partial` basis puts `≥` on the figure, and a null loss
  demotes the claim to a cut-stone block reading `— not priced · reason`, with no route.
- Depends on: Cinzel + a mono face; the hero number must be a mono digit; needs the
  `.pos` badge. It works outside the gonfalon but loses its rank without it.

**4. Bye profile** (`.bye`: six-column lollipop strip — 2px stems on `--axis`, 10px ivory
dots on `--mark`, a gilded diamond for the worst week, mono values and week labels)
- Shows where in the season the bye cost lands.
- Rule: the marker, not the stem, carries the value, so a 4-point week is a dot on the axis
  and still reads at 12:1; the worst week is the only gold; every number is mono. Never a
  meter, never a 0–100 scale — the axis is the max marker. Gold-on-near-black cannot carry a
  low bar at 3:1, which is why this is not a bar chart.
- Depends on: `--p` per week as a percent of the max; `--axis` (≥ 3:1 on stone) and `--mark`
  tokens; ≥ 300px wide. Portable; it is self-contained CSS grid.

**5. Standing claim block** (`.block` + `.claim`)
- One peer-relative fact (thin at X, count rostered), its caveat (floor), its route.
- Rule: the number is a count, in mono, never a bar; the floor marker `≥ … priced` is
  part of the claim, not a footnote.
- Depends on: `.pos` badge, the block frame, a mono face. Portable.

**6. Position badge** (`.pos` + `#posshield`)
- A 30–34px heater shield outlined in the position's own token with the position in mono.
- Rule: hue means *which position*, never severity; one home for the ten tokens.
- Depends on: `POSITION_PILL_TOKENS` only. Fully portable; it is the piece most likely to
  be reused across the app.

**7. Ledger / carved tablet** (`.tablet` + `.row`)
- Facts that make no claim: lineup, holes, injuries, record, picks — each either a value
  or an em dash with its reason in the same cell.
- Rule: absence is `—` + reason, floors say `≥`, constructed values carry the stamp; no cell
  may contain a bare `0` or be blank. Keys in Cinzel, values in prose, numerals in mono.
- Depends on: the `.stamp` and the key/value grid; keys need ~110px. Portable.

**8. Wall of crests** (`.wall`, `.doors`, `#shield` + five `#c-*` charges, `#sill` for the dock)
- The five rooms that exist as escutcheons hung by rings from a forged rail, plus the
  Prytaneum as a hearth sill — a dock under every room, drawn as a different shape so it
  cannot be mistaken for a sixth door.
- Rule: a door exists only if the room exists; the charge is a drawn emblem, not a UI
  icon; the sub-line names what lives *inside*, checked against `app.py` (trade calculator
  and free agents in Roster Maintenance; standings, depth map and picks acquired in League;
  boards and mock drafts in Draft Room), so those do not need doors of their own.
- Depends on: the shield symbol with `viewBox="0 0 100 120"` on the crest svg (without
  it the charges drift — found and fixed in render), the rail rule, Cinzel at 12px. The
  3 × 2 mobile layout and the 6-across desktop layout are both just grid columns. Portable.

**9. Lintel** (mark + wordmark + rule-with-diamond, seat/league context at the sides)
- The brand, carved small, with the two context facts that frame everything (which seat,
  which league, how big the pool).
- Rule: the lintel is never taller than the summons' headline block; the wordmark is
  gilded Cinzel at ≤ 30px with DYNASTY letterspaced ≥ .5em beneath a rule-and-diamond.
- Depends on: the `#wyrm` symbol (replaceable by the raster), the gradient-text gild.
  Portable, but the three-column balance needs ≥ 900px; on mobile it collapses to one row.

**10. Gate / quiet state** (`.gate` + CLOSE THE KEEP)
- The "nothing needs you" verdict with a control that ends the visit.
- Rule: it occupies the summons' slot and uses a different frame, so the quiet week is a
  *different sentence*, not a missing one. The button is the only solid-gold fill on the
  page, so it reads as the one thing to press.
- Depends on: the frame set and the toggle class. Portable.

**11. Stamp** (`.stamp`, `.stamp.absent`)
- The CONSTRUCTED mark; mono 12px caps in a thin gold box.
- Rule: a constructed value is stamped where it is shown, not in a footnote.
- Depends on: nothing. Portable.

**12. Pilasters** (`.pilaster`, desktop only)
- Two vertical rails with capital/base diamonds that turn the column into a bay.
- Rule: they carry no information and must stay ≤ 3px and ≤ 75% opacity.
- Depends on: a fixed-width hall and ≥ 1100px. Only works in this layout; drop it on
  anything narrower. Not portable, and the design loses little without it.

**The one I would keep:** the **heraldic frame set (2)**. Severity-by-shape is the idea
that makes the Keep structural rather than wallpaper: it lets the world-building sit on
the *edge* of every panel while the inside stays a quiet, high-contrast reading surface,
and it frees every hue on the page for the position tokens. The forged rule and the
crests decorate; the frames rank.
