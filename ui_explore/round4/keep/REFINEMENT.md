# The Keep — refinement pass

Inputs: `CRITIQUE_DESIGN.md` (12 findings), `CRITIQUE_PRODUCT.md` (20 findings + 6 brief
corrections), `VOICE.md` (binding), the corrected `BRIEF.md`, and the coordinator's seven
priorities plus the cross-cutting chart-contrast finding. `desktop.html` and `mobile.html` are
rebuilt in place; `NOTES.md` is patched where it was wrong.

Everything below is either **taken** (with what changed), **rejected** (with the argument), or
**deferred** (with the rule that will govern it). Re-measured numbers are at the end.

---

## The voice (VOICE.md) — taken, throughout

- `NEEDS YOU` is gone. The first band is labelled **`OPEN · 1`**, the second **`CAN WAIT · 2`**
  (VOICE's own replacement). The ledger and the rooms keep their names.
- `Nothing needs you.` → **`Nothing is open.`** The kicker above it names the checks
  (`Checks · holes · depth · byes · starters`, rule 5) instead of repeating the headline.
- The summons kicker is `Bye collision · measured` — a basis, not a summons. The headline
  `Week 6 is the one that hurts.` is kept, as VOICE rules it (indicative; the week is the
  subject). Every "you/your/this week/your schedule" is gone: grep for `this week`,
  `your schedule`, `needs you` returns nothing in either file.
- The app is never the subject anywhere; no sentence congratulates; every figure carries a
  basis word (`measured` / `≥` / `CONSTRUCTED` / `— absent · reason`).

## The false sentence — taken

`"Bottom of this league at the position"` (×4) is deleted. Each thin claim now says the label
and the branch it was earned on, which `depth_ratings.depth_label` actually returns:

- DEF: **Weak** — at or below 0.7× this league's average DEF room, **by count**. Three peers are
  unpriced, so value was not compared. (mobile: `Weak — ≤0.7× league mean, by count.`)
- TE: **Weak** — at or below 0.7× this league's average TE room, **by value**. One of the two
  could not be priced, so the room's value is a floor. Floor chip: **`≥ 23 · 1 of 2 priced`** —
  the `≥` now sits on the value it qualifies, not on the exact count (product 11).

This also closes product 10 (two measurements in identical frames): the frames are still
identical, but the branch is printed in bold inside each one.

## Coordinator's seven, in order

**1. Frame hierarchy inverted (design 1) — taken.** The rod's downward `box-shadow` is gone
(`0 -1px 0 #000` only); the gonfalon's skin is a brighter gradient (`--metal-hi`, peak `#fff4ce`)
with a faint outer glow, and the cut-stone blocks dropped to `--metal-lo` (peak `#ba9561`).
Measured at the top-edge centre of each frame on the 1× render: **gonfalon L255, block L186,
tablet L3** (desktop) and **L255 / L186 / L4** (mobile). Edge brightness now runs in the same
order as the shapes.

**2. TE shield on an RB claim (product 2) — taken, and the "who" is filled.** The badge is
**RB**. The line under the headline reads *"Jahmyr Gibbs, RB, sits in week 6. No bench player
fills the slot, so it stays empty."* Source: `roster[].bye == worst_week` ∩ `starters` gives
exactly Gibbs (`9221`, value 95.0); `worst_week_detail.bench_used = 0` and `starters_out = 1`
support "no bench player fills the slot". The name is set in Source Serif at 18px/15px under the
headline, not in the Cinzel kicker, which design 8 showed cannot carry a proper noun. The hero
unit now reads `trade-value points lost — his whole value` (95.0 = Gibbs's entire value,
`bench_value_used = 0`). This also takes product 18 in the stronger form the adversary asked
for: the summons now says the slot is empty, and the ledger's Holes row says *"every slot has a
body; week 6's bye leaves one empty"*.

**3. Futurity (product 3) — taken in copy; the frame is kept, with an argument.**
`current_week` is null, so the page no longer asserts a deadline anywhere. The summons carries
its own absence line in the four-state grammar: *"— now: not in this capture. A replayed draft
has no point in a season, so nothing here says week 6 is still ahead. This is the season's
shape, not a deadline."* "your schedule", "this week" and "a starter sits [now]" are gone.

What I did **not** do is demote the bye claim to a cut-stone block when `ahead_only` is false.
`front_claims.LADDER` ranks `bye` above `thin` without consulting `ahead_only`, and `compose()`
on this fixture still returns the bye claim first. The gonfalon is defined, from this pass on,
as **the frame of the first rung the ladder returned** — not "urgent" and not "deadline". The
caveat line is what makes that honest in a replay; in a live league with a known week the same
line reads `now: week N · the worst week still ahead is …` from `byes_ahead`. If the owner wants
the frame itself to change with `ahead_only`, it is one class on the article; the rule is
written in NOTES.md's component inventory.

**4. The hem below the desktop fold (design 2) — partly taken, partly rejected.** The crest wall
shrank from 186px to 104px (crests 42px with names beside them, design 6's half-measure), which
moved the whole column up ~90px: the headline is now at y=344 (was 442), the hero at 464, the
button at 675, and the chart's first pixel at **787, above the 800 fold** (was 807). The hem is
at y≈1050 and is still below the fold. I am not moving the shape cue to the top of the panel:
the design adversary measured that what ranks the summons above the fold is width, headline size,
the 64px numeral and now the edge brightness, and conceded those work; the hem is the signature
when the page scrolls, not the rank cue, and on mobile the whole gonfalon (y 93–634) is inside
the first 664px with its hem. Severity-by-shape is a claim I now state more narrowly in
NOTES.md: shapes carry *kind* (summons / standing / fact / gate); rank above the fold is carried
by size, width and edge brightness in the same order.

**5. Mobile deleted the absence grammar (design 4, product 8) — taken, fully, inside budget.**
The mobile ledger now has the same six rows as desktop — Lineup, Holes, Hurt, Record, Picks,
Fresh — each with its em dash and reason, and the Lineup row stamps only the constructed value
(`[CONSTRUCTED] 10 of 10 · none submitted`); Holes is its own unstamped row. The chart's method
caption is back on mobile. Every door has its sub-line on mobile. The mobile legend names every
basis class it has, in the same words as desktop. This cost 170px, found by: the lollipop strip
(−30 vs bars), one-line ledger rows, the demo toggle moved into the lintel as a 44px control,
the rooms' section header dropped (the rail is the header), shorter claim lines. Mobile live
is **1294px** against the 1328 budget.

**6. Door sub-lines (product 13) — taken, checked against `app.py`.** Matchup → *lineup
readiness · projections* (no "this week"); Roster Maintenance → *depth · free agents · trade
calculator* (the calculator lives there, ~4171); Draft Room → *boards · mock drafts* ("pick
counts" is gone — nothing in that branch calls `build_pick_ledger`); League → *standings · depth
map · picks acquired* ("trades" is gone; the depth map and the picks-acquired block are there);
Import Audit → *what Sleeper returned* ("freshness" is gone — it is a global band, not that
view). Mobile carries shorter forms of the same five.

**7. The footer's false claim about the engine (product 5) — taken.** The sentence now reads
*"No team rating, no letter grade, no odds — none is computed; the depth label behind 'thin' is
four named steps, never a score."* It names the three things prior mocks faked and claims
nothing general. The basis legend also **toggles with the state** (product 4): the quiet
legend says the bye line is constructed.

## Cross-cutting: the chart (design 5 + all three designs)

**Taken, by changing the mark, not the hex.** Gold-on-near-black cannot carry a 4-point bar at
3:1 without becoming a slab, so the six bars are now a **lollipop strip**: a 2px stem on the
`--axis` colour (`#6a6052`, measured **3.19:1** against the stone, as is the baseline) and a
**10px ivory dot** (`--mark #d8cfbb`, measured **12.69:1**) whose height carries the value; the
worst week is a 16px gilded diamond — the brand's own rule ornament — with a glow. The thing
the eye reads, the marker, is now the highest-contrast non-text object on the page, and a
4-point week is a dot sitting on the axis rather than a 3px sliver. Values stay labelled in
mono above each marker (the NOTES.md argument for labelling all six stands; the adversary's
"table in a chart's clothes" charge was about marks that did not render, and these do).
The quiet state's invented chart is gone entirely (design 11 and product 7 both close):
the gate carries one stamped sentence instead.

## Other findings taken

- **The Prytaneum is a dock, not a door** (brief correction, product B6). Five crests and one
  **hearth sill** — a wide, low shape, clearly not an escutcheon — labelled *dock · under every
  room*. On desktop it sits past a mortar divider at the end of the rail.
- Quiet-state "at or above its league peers" (product 6) → *"No position room is thin against
  this league · no label at or below 0.7× the league mean; Average is not 'above peers'"*.
- Quiet-state "worth a move" and the 19% that was 19.3% (product 14) → *"no week carries more
  than a fifth of the season's bye cost, so no week stands out"*, stamped CONSTRUCTED.
- Quiet-state frame grammar (design 3): the "no position is thin" panel is a **tablet** (facts,
  no claim), not a cut-stone block.
- `Seat 5` → **Seat 1 · Team 1** from `_provenance.seat` (product 12); the seat no longer wears
  a CONSTRUCTED stamp, because it is in the file.
- Hurt reason (product 9) → *"the lineup is constructed, so 'on starters' has no measured
  referent"*.
- Picks (product 16) → *"— not in this capture · picks acquired or given away, never priced"*.
- Freshness (product 15) is a sixth ledger row, absent with its reason and its vocabulary:
  *"— not in this capture · reachable; Fresh / Recent / Aging / Stale per source"*. The capture
  does not carry the manifest, and I write only inside `keep/`, so the row states the absence
  rather than drawing a grade the fixture does not hold.
- "Pool 5,357 players" → *"5,357 players ranked for this league"* (product 20).
- Thin claims route to **League · depth map**, as the claim object says (product 19).
- `1 of 1` → `1`; the CAN WAIT count has a `+N hidden` slot (`.more`), rendered only when
  `front_claims.hidden` is non-empty — on this fixture it is empty and the element is `hidden`
  (product 17).
- Unknown position codes fall back to `--pos-none` (`--c:var(--pos-xx,var(--pos-none))`), and
  the badge clips at three characters (design 9).
- Every mobile crest hangs from a rail: one rail per grid row (design 10).
- Rod finials no longer touch the pilasters: 8px rod overhang, 36px hall padding (design 12).
- `:focus-visible` rules on every link and button; `:active` feedback on mobile doors, claims
  and the button (design 12). Heading levels are h1 → h2.
- The lineup stamp is first in its cell so it never orphans a fragment (design 12).
- Chart `aria-label` carries all six values and the total (237).

## Rejected, with arguments

- **Move the crest wall below the content on desktop (design 6).** The compact rail returns
  most of what the adversary asked for (first claim pixel at 258 instead of 354; chart above
  the fold) while keeping the composition. The mobile page keeps the rooms last because its
  fold is 136px shorter; the two files differ on purpose and the measurement now favours both.
- **Make the gonfalon a block when `ahead_only` is false (product 3).** See item 3: the ladder
  does not demote the bye rung, so the frame follows the ladder and the caveat carries the
  absence. Demoting the frame would make the page disagree with `compose()`'s order.
- **Cut the desktop chart (design 5's alternative).** It is above the fold now and it is the
  only place the 237 is decomposed; the sentence names the top two weeks, the strip shows the
  other four.
- **Label only the worst week (dataviz guidance).** Six values, each the answer to "what does
  week N cost", stay labelled. The marks now render, so the labels supplement rather than
  replace them.

## Deferred, with the rule

- **A claim whose cost was not measured (design 7).** Rule recorded in NOTES.md: the gonfalon
  may not render without its number; when `partial` is true the number carries `≥`, and when the
  worst-week loss is null the bye claim renders as a cut-stone block with `— not priced · reason`
  and no route. Not drawn here because the fixture has no such state and I will not invent one.
- **`count: 0` thin variant (product 10).** Rule: the block prints the engine's own string
  `None — no rostered players here` in place of the numeral; never a `0`.
- **A third standing claim on mobile (design 8).** Rule: the third claim collapses into
  `+1 hidden` on the CAN WAIT band, which is now built; the budget holds for two blocks.

## Re-measured (Chromium via Playwright, Google Fonts loaded)

| | desktop 1280×800 | mobile 390×664 |
|---|---|---|
| computed minimum font size | **12px** | **12px** |
| horizontal overflow | none | none (`scrollWidth` 390; `overflow-x:hidden` is not set on mobile this time) |
| scroll height, live | 1475 | **1294** (budget 1328) |
| scroll height, quiet | 1099 | 998 |
| tap targets under 44px | none | none |
| digits outside the mono face | 0 | 0 |
| top-edge peak luminance: gonfalon / block / tablet | **255 / 186 / 3** | **255 / 186 / 4** |
| chart marks vs their ground | dots **12.69:1**, worst-week diamond 12.2:1 | dots 12.69:1, diamond 14.2:1 |
| stems and baseline vs ground | **3.19:1** | **3.19:1** |
| first claim pixel / headline / hero / button | y 258 / 344 / 464 / 675 | y 93 / 150 / 233 / 397 |
| chart first pixel | **787** (fold 800) | 481 |
| gonfalon hem | 1050 (below fold) | 634 (inside the first screen) |

Text contrast is unchanged from NOTES.md (`--ink` 15.5:1, `--ink-2` 8.8:1, `--ink-3` 5.1:1,
gold label 7.1:1, RB `#0ca89c` on stone 5.6:1, DEF 7.9:1, TE 6.6:1, black-on-gold 7.6:1).
