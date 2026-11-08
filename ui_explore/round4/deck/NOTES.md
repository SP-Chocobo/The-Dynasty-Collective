# The Deck — notes

> **Round-1 record.** These notes describe the first pass as it was reviewed in
> `CRITIQUE_DESIGN.md` and `CRITIQUE_PRODUCT.md`. The refined files differ in several places
> (bar column deleted, `×LG` deleted, tally replaced, IR flag added, voice rewritten); see
> `REFINEMENT.md` for what was taken, what was rejected, the `×LG` ruling and the re-measured
> numbers. The component inventory below still describes the pieces, with these changes:
> component 3 (depth ladder) now encodes its four states in the label word, not in four cells;
> component 2 (bye ledger) has no bars and carries `out · starting` / `promoted · value` from
> `bye_collision`.

Angle: information-forward. A manager with six leagues and four minutes. The problem this angle
carries is that the two densest prior mocks (`mock_62`, `mock_65`) got their density from
quantities that do not exist. Strip the Team Index, the letter grades, the odds and the 0–100
meters and roughly half their surface is empty. The assignment was to find what honestly fills
that space.

Files: `desktop.html` (1280-wide), `mobile.html` (390 × 664). Both carry a **live** state (the
replayed seat from the brief) and a **quiet** state (nothing needs you), switched by a dashed
"review" control that is a design-review affordance, not product UI.

## What fills the space, and where every number comes from

Everything drawn traces to a call in the Real table, and most of it to the actual fixture at
`ui_explore/front_fixture.json`. The one thing I computed myself is noted.

| panel | what it draws | source |
|---|---|---|
| Verdict | "One thing needs you" / "Nothing needs you"; tally 1 · 2 · 5 | counts of claims below; nothing else |
| Bye ledger | six weeks × value lost (95 · 8 · 51 · 4 · 56 · 23), season 237, worst-week share 40 %, 1 starter out, unknown byes 0, **who is on bye each week with their trade value** | `bye_collision` / `bye_concentration` (fixture `bye_profile`); the per-week names and values are the fixture's `roster` list (each player carries `bye` and `value`) |
| Depth ladder | six positions × one of four discrete labels; bodies; priced value; `≥23` floor; ratio vs league average | `depth_label`. The fixture retains only the two *thin* rows; I ran the fixture's own loop (`capture_front_fixture.py` lines 95–116) unfiltered in a scratch script and got QB Average (44 vs 43.3 avg → 1.02×), RB Average (137 vs 120.6 → 1.14×), WR Average (162 vs 167.3 → 0.97×), TE Weak (23 vs 39.2 → 0.59×, 1 of 2 priced), K Average on bodies (2 vs 1.67 → 1.20×, nobody priced), DEF Weak on bodies (1 vs 1.58 → 0.63×, peers unpriced). Same code path, same seat. |
| Standing | DEF thin (1 rostered), TE thin (2 rostered, `≥23`) | fixture `thin_positions` |
| Cleared | structural holes none; QB/RB/WR/K at league-average; weeks 7 and 9 ≤ 8 pts; lineup 10/10; unknown byes 0 | each row carries its own basis stamp (`measured` / `constructed`) |
| Lineup | the ten slots with names and values, bench of six, injuries `—` | fixture `starters` (CONSTRUCTED — optimizer's lineup, stamped as such); injuries absent with reason |
| Data age | three ages on a real axis with the real 7 / 30 / 90-day bands; two absences with reasons; grade Aging | `build_freshness_manifest` + `recency_grade`. Ages recomputed for today (2026-11-07) from the as-of dates the fixtures carry: trade values 2026-08-20 → 79 d, rankings 2026-08-25 → 74 d, player capture 2026-09-07 → 61 d. League sync and season-projection coverage are absent for a replayed seat. |
| Record · Picks | six em dashes and one shared reason | `team_standings` / `build_pick_ledger` both absent for this seat |
| Pool | 5,357 | `_provenance.universe_rows` |

The quiet state's bye series (41 · 36 · 44 · 39 · 42 · 35, same 237 total) and its ladder are
**constructed** and stamped so in the panel, because no capture holds a quiet roster. The three
Draft Sharks / Sleeper ages and the record/pick absences are shared between states because they
are properties of the machine, not the week.

## Where I disagreed with the brief, and what it bought

1. **The six doors are not content; they are chrome.** The brief's spine ends in a door grid and
   every prior mock spends 15–25 % of its height on six tiles. I moved the doors into the top bar
   on desktop and a fixed bottom bar on mobile. That bought the entire second row of the desktop
   deck and ~200 px of the mobile budget, and it is also simply where navigation lives in an app
   you open between two other things. The cost: the doors are small and lose the emblem-tile
   warmth of `mock_65`. I think that trade is right for a front page whose test is "can I close
   it in three seconds"; a tile grid is a lobby, and nobody wants a lobby six times a day.

2. **The wordmark is small.** `claude_c_brand` spends ~350 px on the mark before any
   information. Here the brand is 40 px in the corner and is carried instead by material: the
   brushed-gold gradient on every heading and bar, the gold rule with a bright centre over the
   verdict, Cinzel for headings only, position colours used as the only saturated hue. I believe
   this is closer to what "cohesion to the logo" means than a large logo is. The crest slot is a
   dashed ring with a drawn placeholder glyph so nobody mistakes it for the real art.

3. **Three bands became two.** Claim / week / doors is a reading order; the deck wants a
   *verdict* and a *ledger*. The verdict band answers the three-second question in one line plus
   a 1 · 2 · 5 tally. Everything beneath is the ledger, ranked: the claim (bye ledger) sits
   beside what stands (thin positions + cleared), and the rows below hold what can wait. On
   mobile the two thin claims are folded *into* the ladder as note rows under their own
   positions, because a separate Standing panel repeated the ladder's two Weak rows in prose.

4. **"What can wait" is a list of measured negatives, with their basis.** Every prior mock
   rendered the quiet state as a green checkmark and a sentence. The densest honest version is
   the list of checks the engine actually ran and passed — holes, four Average positions, two
   weeks under 8 pts, unknown byes 0 — each stamped `measured` or `constructed`. That list is what
   makes the quiet state look like a working page rather than an empty one. I also took
   `mock_64`'s **CLOSE THE APP** control; in the quiet state it replaces the tally on mobile.

5. **Direct labels beat an axis for six bars; an axis beats direct labels for three ages.** The
   bye profile became a *row ledger* — week, bar, number, who — rather than a column chart. Six
   values at this size do not need an axis; they need to be read, and a row carries the names of
   who is out beside the number that explains it. The one reference I kept is a dashed line at the
   even-spread mean (237 / 6 = 39.5), which is real arithmetic and is what "40 % in one week"
   looks like. Data age went the other way: three dots on one axis with the real 7 / 30 / 90-day
   bands, because the bands *are* the meaning (Aging is a threshold, not a number).

6. **The ratio column is a judgement call I want flagged.** The ladder shows `1.02`, `0.59`,
   `1.20·n`. That ratio is exactly what `depth_label` computes before it thresholds, and it is the
   "why" behind the label — the owner asked for why. It is not a 0–100 meter and is not drawn as
   one. But it is a continuous number next to a categorical label, and a reviewer could read it as
   a score. If the panel of judges thinks it crosses the line, delete the column; the ladder
   stands without it.

## The mobile answer

A desktop grid stacked is what I built first and it measured **2078 px**. Two passes got it to
1298 by changing the shape rather than the type size:

- Standing claims folded into the ladder's thin rows (−120 px).
- Lineup folded into its own *cleared* row as position-coloured chips (−90 px). The slot grid
  survives only on desktop.
- Five freshness rows became one axis with three marks and a legend line (−90 px).
- Bench names collapsed to "+2 bench" per bye row; notes cut to one line.
- Record and picks are one four-cell strip with one shared reason.

The fold (first 664 px) shows: verdict, tally, the whole bye ledger, and the top of the ladder.
The three-second test passes on the fold alone.

## Measured

| | desktop live | desktop quiet | mobile live | mobile quiet |
|---|---|---|---|---|
| min computed font | 12 px (`DYNASTY` wordmark line) | 12 px | 12 px | 12 px |
| horizontal overflow | none (scrollW 1280) | none | none (scrollW 390) | none |
| scroll height | 1312 px | 1316 px | **1298 px** | **1303 px** |

Mobile budget is 1328 (2 × 664). Live is 30 px under, quiet 25 px under. That is tight; a longer
player name or a localised string would break it. See "wrong or weak".

Contrast, every text colour on every surface it sits on: `--ink` ≥ 14.0:1, `--ink-2` ≥ 7.8:1,
`--ink-3` (the recede role) ≥ 4.7:1, `--absent` ≥ 7.1:1, gold body ≥ 6.4:1. The recede role
clears 4.5 everywhere, so nothing relies on the AA-large allowance.

Tap targets: all six doors 44 px (desktop) / 56 px (mobile bar); seat chip 44; review buttons 44.

Fonts: Cinzel (wordmark, h1, panel headings, tally labels, eyebrows — never a number), Source
Serif 4 (prose and labels), JetBrains Mono (every numeral, every basis stamp). Google Fonts is
the only external host. All marks are inline SVG; the bars and tracks are SVG with percentage
widths, not scaled viewBoxes, so their text never shrinks below the CSS size.

## What this design would be better with, and does not have

- **A lineup a human submitted.** The slot grid is the optimizer's lineup, stamped CONSTRUCTED.
  On a live league it is Sleeper's `starters` and the stamp goes away.
- **Material injuries on starters.** `compute_readiness` produces it; the fixture does not carry
  it for a replayed seat, so it is an em dash with its reason.
- **A populated pick ledger.** `build_pick_ledger` is diffs-only and this seat has no
  `traded_picks`. The strip is drawn in its absent state; the live version shows acquired / sent
  per year. I did not fake one.
- **All six depth labels in the fixture.** `capture_front_fixture.py` keeps only the thin rows.
  The ladder needs every row, and I had to recompute the other four. That is a finding: the
  fixture should retain `label`, `count`, `value`, `valued_count` for every position.
- **Season-projection coverage** (weeks of 18). The manifest row exists; the fixture lacks it.

Nothing on the page needs a quantity that the engine does not compute.

## What I believe is wrong or weak

- **The mobile budget is held by copy length, not by structure.** 25–30 px of headroom is a
  rounding error. The honest fix is one fewer panel on the phone, probably the record/picks strip
  moving into the data-age panel as two more dashes. I did not do it because the strip is where
  the absence grammar is most legible.
- **The verdict copy is hand-written.** "One thing needs you" with the week-6 sentence is prose I
  composed; the engine returns numbers, not sentences. A real page needs a sentence template per
  claim type, and the template is where fabrication would creep in.
- **The review toggle is in the footer.** On desktop it was fixed bottom-left and covered the
  ladder; in-flow it is honest but easy to miss. It should not ship at all.
- **The crest is a stand-in.** The drawn wyrm glyph is a 30 px curve with a head; it is obviously
  not the mark and I kept it inside a dashed ring so it reads as a slot. The page will look
  different with the real 512 px asset and I have not designed for how the gold relief will sit
  next to flat panels.
- **Density on desktop is uneven.** Row 1 (bye ledger + standing) is the richest thing on the
  page; the record/picks strip is six dashes in a row. The strip is honest but it is the one
  place that reads as wallpaper. A live league fills it.
- **"Standing" is used for two things.** The thin-position panel is "Standing" (standing claims)
  and the record section was also "Standings" in a draft; I renamed the latter to Record but the
  word is still doing semantic work it should not.
- **The ratio column** (see disagreement 6).
- **The bye ledger's dashed mean line over the bright week-6 bar is faint.** I chose bright gold
  on gold rather than a contrasting colour to keep one saturated hue per panel; it costs
  legibility right where the reference matters most.

## Component inventory

What this page is built from, so it can be taken apart. "Portable" means it can be lifted into a
different layout with its CSS block and nothing else; "load-bearing" means it only works here.

**1. Verdict band**
- *What*: one Cinzel line that answers "can I close this?", one serif sentence of why, and a
  tally of claims by strength (needs you / standing / cleared). In the quiet state the tally
  gives way to CLOSE THE APP.
- *Rule*: the headline is a count, never an adjective. "One thing needs you" / "Nothing needs
  you" — never "All systems green". The tally's three numbers must equal the rows below.
- *Depends on*: the gold rule token (`--gold-rule`) and Cinzel; otherwise portable. The
  sentence is hand-written and needs a template per claim type before it can be generated.

**2. Bye row-ledger**
- *What*: six rows of week · SVG bar · number · who sits, with a dashed line at the even-spread
  mean and a totals line (season, worst-week share, starters out, unknown byes).
- *Rule*: bars are value lost, names are bodies, and both are shown so the reader sees the
  difference (week 7: four bodies, 8 points). Bars are percentage-width SVG rects at 1:1 so
  labels never scale. The hot row is the only bright-gold fill.
- *Depends on*: the player roster with `bye` and `value` per player, the position colour tokens,
  a mono numeral face. Needs ~340 px of width for the who-column to hold two names; below that
  bench collapses to "+n bench" (as on mobile). Portable.

**3. Depth ladder**
- *What*: one row per position; bodies · priced value · ratio; then four discrete cells (None /
  Weak / Avg / Strong) with exactly one marked.
- *Rule*: four cells, never a bar, never interpolated, because `depth_label` has exactly four
  values and a fifth visual state would be a lie. A floor renders `≥`; an unpriced room renders
  `—` and its ratio is tagged `·n` (on bodies). Thin rows are tinted, and on narrow layouts carry
  their claim as a note row beneath them.
- *Depends on*: all six labels, which the fixture does not currently retain (finding above); the
  position pill tokens; ~300 px of width for seven columns. Portable; drop the ratio column if
  the judges rule it out.

**4. Basis stamps and the four-state value grammar**
- *What*: `95` measured (plain mono), `≥23` floor (gold with the ≥ generated by CSS so it cannot
  be forgotten), `—` absent followed by an italic reason, and a hatched outlined `CONSTRUCTED`
  chip. Every panel also ends in a mono basis line naming the call.
- *Rule*: the four states must be distinguishable at a glance and no value may appear without
  one. A dash never stands alone.
- *Depends on*: nothing but the colour roles and the mono face. The most portable thing on the
  page and the one I would keep if I could keep only one — it is what lets a dense page be dense
  without lying.

**5. Cleared list**
- *What*: rows of check · measured negative · basis stamp. On mobile it also hosts the lineup
  as a chip row.
- *Rule*: only checks the engine actually ran. Each row's stamp is independent (holes are
  measured, lineup is constructed) and the list is what the quiet state is made of.
- *Depends on*: the stamp grammar (4). Portable.

**6. Freshness axis**
- *What*: a track with the real 7 / 30 / 90-day bands and one mark per loaded source; absent
  sources as dashes with reasons; the grade in the header.
- *Rule*: the bands are `recency_grade`'s thresholds, not decoration; marks are ages in days,
  which are a real continuous quantity, so an axis is honest here.
- *Depends on*: ~200 px of track width before three marks collide (they nearly do at 61/74/79).
  Portable as one axis; the five-row variant needs ~360 px.

**7. Absence strip**
- *What*: a row of label-over-dash cells sharing one reason.
- *Rule*: an absent block is drawn with the same frame and type as a measured one — the dash is
  the information. One reason per strip, not per cell.
- *Depends on*: the grammar in (4). Portable, and the first thing to cut if a budget is short.

**8. Door bar**
- *What*: the six real destinations, icon + label, horizontal in the desktop top bar, fixed at
  the bottom on mobile with the current one in bright gold.
- *Rule*: six and only six; a door to an unbuilt room is a fabrication like any other.
- *Depends on*: the brand bar's width on desktop (the seat chip and the doors compete at
  1280; below ~1180 the labels need to go icon-only). Load-bearing on desktop; the mobile bar is
  portable.

**9. Brand corner and gold material**
- *What*: 40 px dashed crest slot, Cinzel wordmark with the measured gold gradient, DYNASTY
  letterspaced beneath; the same gradient on headings, bars and the verdict rule.
- *Rule*: Cinzel for words only; every number goes in mono. Gold is a gradient from the five
  measured stops, never a flat fill. One saturated family (position colours) besides gold.
- *Depends on*: the token block at the top of either file. Portable as a token set; the crest
  slot is a placeholder and will need re-sizing when the real mark lands.

**10. Seat chip**
- *What*: "Team 1" with a CONSTRUCTED stamp and a chevron, in the top bar.
- *Rule*: the seat name carries its own basis because a replayed seat is not an owner's team.
- *Depends on*: (4). Trivially portable.

If only one survives: **the four-state value grammar (4)**. Every other component is a layout
of it.
