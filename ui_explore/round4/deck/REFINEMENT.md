# The Deck — refinement pass

Inputs: `CRITIQUE_DESIGN.md` (14 findings), `CRITIQUE_PRODUCT.md` (13 findings + 2 brief
corrections), `VOICE.md` (binding), the corrected `BRIEF.md`. Both adversaries said "worth
refining"; the design one said the pass must cut, not tune. It cut.

Every number below was re-measured in this container after the last edit (Chromium via
`browser_binary.find_chromium()`, `--no-sandbox`, 1280×800 and 390×664, both states).

## Measured, after

| | desktop live | desktop quiet | mobile live | mobile quiet |
|---|---|---|---|---|
| scroll height | 1660 | **1477** (shorter than live) | **1213** | **1155** (shorter than live) |
| min computed font | 12 px | 12 px | 12 px | 12 px |
| document overflow | none | none | none | none |
| **in-panel spill** (new probe: every element's right edge against its panel's padding box) | none | none | none | none |
| clipped cells (`scrollWidth > clientWidth` on th/td/pos/slot names) | none | — | none | — |

Mobile budget 1328. Under the adversary's own loads: **long surnames (Smith-Njigba, St. Brown,
Harrison Jr., Pittman Jr., Vanderschaaf, Westbrook-Ikhine) 1243; full names 1243; every value
absent 1213.** Headroom is now 85–115 px, against −30 before. Desktop at 1260 / 1200 / 1024 /
768 no longer overflows horizontally (three breakpoints added). Fixed bar top on mobile is 608;
the first screen holds the verdict, the whole bye ledger, the IR item and the ladder's first rows.

Desktop grew from 1312 to 1660. That is the cost of three honest additions — an engine-fields
column pair in the bye ledger, a real injury flag with its own card, and the Prytaneum dock — and
of the Cleared list moving out of a side column into a full-width strip so row 1 could shrink.
Quiet is shorter than live on both devices, which it was not before.

## Taken

**1. Depth ladder spill (design 1).** Gone, by redesign rather than clipping: the four cells and
the ratio column are deleted (below), the table is `table-layout:fixed` with explicit columns, and
the new in-panel probe reports zero spill on both files in both states.

**2. The bye attribution sentence (product 8, design "what survives").** Deleted. *"RB room is two
deep for two RB slots: nothing backfills him, so his whole price is the loss"* was true for week 6
and a template that is false by 5× on week 9. In its place the ledger prints the engine's own
per-week fields, which `bye_collision` returns for every week and which I re-ran to get:

| week | lost | out · starting | promoted · value |
|---|---|---|---|
| 6 | 95 | 1 · 1 | 0 · 0 |
| 7 | 8 | 4 · 2 | 2 · 16 |
| 8 | 51 | 3 · 3 | 2 · 31 |
| 9 | 4 | 1 · 1 | 1 · 16 |
| 10 | 56 | 3 · 2 | 1 · 15 |
| 11 | 23 | 4 · 1 | 1 · 0 |

Week 6 now reads `1 · 1 — 0 · 0` beside Gibbs 95: one starter out, nobody promoted, and the reader
draws the inference the page used to draw for them. Week 9 reads `1 · 1 — 1 · 16` beside Robinson
20 and a loss of 4, which is the substitution chain made visible without naming it. This needs
`capture_front_fixture.py` to persist the full per-week dicts, not just `worst_week_detail`;
flagged below as a fixture gap.

**3. The tally (design 2, product 5).** Replaced. The `1 · 2 · 5` row is gone. The verdict band
now carries one display-size number — `95 pts`, the largest open cost, 44 px on desktop — with
its caption (week 6 bye · 40 % · 1 starter out · *season shape, not a deadline*), and a secondary
line `4 OPEN · bye · starter on IR · TE · DEF` at half the size. The CLEARED count is deleted: no
check inventory exists in the engine, so the Cleared list is a list, not a number. The 4 is the
count of claims actually drawn (compose()'s bye + two thin, plus one starter_injury_flag).

**4. Mobile budget (design 4).** Structural, as the adversary said it had to be: bar column
deleted; the two thin claims live in the ladder's Weak rows instead of a separate panel; the IR
item is one row; bench names on bye collapse to `+n`; lineup, record, picks and data age are two
panels instead of four; footer is one line. Numbers above.

**5. IDP tokens (design 5).** `--DL --LB --DB --IDP` defined from the brief's table in both files,
and every `var(--c)` now falls back to `var(--absent)`.

**6. Dash grammar (design 6).** Every value dash is `.dash` (`--absent`) and carries a reason:
`Bass — unpriced` in the bye ledger and the lineup slot; the K row reads `2 · —` with the footnote
naming "0 of 2 priced". `.dash.floor` is guarded so an absent floor can never render `≥—`.

**7. Quiet longer than live (design 8, product 12).** Quiet is now 1477 / 1155 against 1660 /
1213. The "Also open" panel does not render in quiet; the bye ledger takes the full row; the
Lineup panel is state-gated and the quiet lineup withholds names (ten slots with dashes and a
stated reason) so the quiet ladder's four RBs no longer contradict a two-RB lineup. CLOSE THE APP
replaces the tally on desktop too.

**8. Voice (VOICE.md).** *One thing needs you* → **Four things are open.** *Nothing needs you* →
**Nothing open this week.** `NEEDS YOU` / `STANDING` labels deleted; the panel is "Also open ·
no deadline attached". *"Everything else was measured and cleared"* → *"The rest is listed below,
each row with its basis"* (product 4). No sentence has the app as its subject.

**9. "Bottom of this league" (product 2, brief correction).** Deleted on both files. DEF now reads
*"one of five single-DEF rooms against a league average of 1.6 bodies; the 9 is a complete price;
the label fell to bodies because three rooms are unpriced"*. TE reads *"≥23 against a league
average of 39; only Pitts could be priced, so the figure is a floor"*. Both sentences are the
engine's own cells.

**10. Higgins on IR (product 3, the product adversary's single most important change).** Drawn.
I verified it on the capture: `injury_status='IR'` on Jayden Higgins, `is_material_injury_status('IR')
→ True`, Robinson `Questionable → False`. The FLEX slot is outlined, a flag card names him, and
he is the fourth open item. The false reason ("no live injury feed") is gone. In the quiet state
the page does not say "none" — per the corrected brief, an empty flag list is silence; the
Checked strip says so in those words.

**11. Freshness (product 10, design 11).** Desktop adopts the mobile single-axis form (three
marks, real 7/30/90 bands). The two non-age rows are split out under their own headings: *"No
day-age by design — Season projection sums 2026 · 18 of 18 weeks"* (verified on the capture:
`weeks_answered` 1–18) and *"Arrives with a sync — League rosters and scoring —"*. "5,357 players
priced" → **"5,357 in the pool, 347 of them priced"**, which I measured (347 rows with a
trade_value).

**12. Picks row (product 11).** The quiet "every original round still held" row is deleted; the
strip says "diffs, never an inventory, never a price".

**13. K cleared row (product 13).** Split: *"QB · RB · WR at league-average value"* and *"K at
league-average bodies; no K is priced league-wide"*.

**14. The Prytaneum (brief correction).** Not a door. Desktop has five doors and a dock bar at
the foot of the page; mobile has five doors and a dashed-off "Dock" tab in the fixed bar.
`Matchup` is no longer marked current — the front page is its own location.

**15. Smaller:** gradient terminal stop `#755024 → #8f6630` (design 13); `≥23` legend says
"partial sum" not "partial count"; `constructed` legended on mobile; review toggle scrolls to top
on switch; `Current week —` is on the mobile page (merged into the Data panel).

## Rejected, with reasons

**Restyle the four depth cells rather than delete them (design 9).** I deleted them. The label
word itself is now the state — `WEAK` as black-on-bright-gold, `STRONG` as gold-on-tint,
`AVERAGE` as an outlined word, `NONE` dashed — which is four discrete visual states keyed on the
engine's four strings, with no spatial encoding to misread as a scale. The adversary's own point
was that 45 % of the panel's width carried a distinction below perception; the fix is to spend
that width on the *why* (this room's bodies · priced value beside the league average, in the
same units) rather than on a better-lit grid. Deleting the cells also made the spill fix free.

**Keep a legible bar column (design 3, option a).** Rejected in favour of option (b), deletion,
on both devices — for coherence, for the 84 px it returned to the who-column, and because the
magnitude now sits in the verdict band at display size where the adversary asked for it. The
page lost its only bar chart. What remains as a drawn quantity is the freshness axis (real axis,
real bands) and the typographic hierarchy of the ledger. I think that is right for this product
and I think the owner, who asked for "graphs or charts or something", will feel the loss; it is
recorded as a loss.

**Make the cleared count real by adding `CHECKS_RUN` to `front_claims` (product 5b).** Not mine
to do in a design pass and not something a page should assert ahead of the engine. The honest
answer today — a list, not a number — is what shipped.

**Two separate "have" / "on_sync" lists on mobile (product 10a).** Partly rejected for budget:
mobile merges them into one Data panel, but the absences are each a labelled line with its own
reason and the ages are on the axis; nothing reads as damage. Desktop has the full split.

**Keep "Record" as its own strip on mobile.** Rejected for budget; it is four lines in the Data
panel with the same dash-and-reason grammar. The six-cell absence strip survives on desktop.

**The claim cap (design 4, "eight claims").** Not rendered, because this seat has four. The rule is
`front_claims.CAP = 3` shown plus a `hidden` list; the "Also open" panel should show three cards
and a line *"+n more, in Roster Maintenance / League"*. This is written here as the rule and not
demonstrated on the page.

## The `×LG` ruling: delete

The design adversary is right that the ratio was the only legible discriminator in the old
ladder, and right that painting it in the dimmest role was a priority inversion. The product
adversary is right about everything else, and three of its points are decisive:

1. **It is a local.** `depth_label` computes `ratio` and returns one of four strings. `LABELS` is
   bound on purpose, and the module says why: the four labels are the product. Printing a number
   the function throws away is publishing an internal, and the brief's forbidden table names the
   shape exactly — "the LABEL is real; the continuous score is not."
2. **`·n` lied about what it marked.** The body-count fallback fires when any *peer* is unpriced,
   not when this room is. The DEF row's own 9 is a complete price; it was tagged as if the room
   were unpriced, and the footnote then said the label was "value against the league average",
   which for that row was false. A notation that misdescribes the fallback on the row that drives
   a claim is worse than no notation.
3. **The quiet state proved the harm.** Three of six hand-computed quiet ratios contradicted the
   formula printed one line beneath them, because changing the seat's cell changes the
   denominator. A continuous number that must be hand-maintained had already been got wrong in
   the state nobody checks.

What the ratio was doing — letting a reader see at a glance that TE is far from QB — is now done
by two real numbers in the engine's own units: `2 · ≥23` against `2.7 · 39`, and `1 · 9` against
`1.6 · —`, with an explicit `on value` / `on bodies` basis column. Two figures side by side cannot
change units mid-column, show the fallback honestly (the league `—` says which rooms could not be
priced), and are exactly the inputs `depth_label` compares. If the engine later returns
`{"label", "ratio", "basis"}`, the ratio can come back as a measured field; until then it is
reachable, not real, and it is gone.

## Fixture gaps this pass depends on (findings, not fabrications)

- `capture_front_fixture.py` keeps only the thin rows of the depth chart; the ladder needs all
  six (`label, count, value, valued_count` per position). Recomputed here through the same loop.
- It persists `worst_week_detail` for one week; the ledger needs `starters_out / players_out /
  bench_used / bench_value_used` for every week. Recomputed here with `lo.bye_collision`.
- It does not carry `injury_status` into `mine` or call `compute_readiness`; the IR flag was
  computed here from the capture with `is_material_injury_status`.
- Its `structural_holes` basis string names `league_usable_positions`; the code uses
  `slot_coverage`. The page cites `slot_coverage`.
- It writes `"value": priced.get("trade_value") or 0.0`, collapsing unpriced into zero; the page
  refuses the zero and prints `— unpriced`.

## Still wrong or weak

- Desktop is 1660 px. The information is honest and the first screen (verdict + row 1) fits in
  800, but a 1280×800 window scrolls twice. The cleared strip and the dock are the first things I
  would fold if a desktop budget is set.
- The page has no bar chart left. See the rejection above.
- The verdict sentence is still hand-written; it needs a template per claim type.
- The quiet-state bye ledger and ladder are constructed numbers, stamped as such, and the quiet
  "promoted · value" columns are illustrative. They follow the engine's arithmetic rules as
  written, but they were not produced by it.
- The mobile first screen puts the two Weak rows below the fold; the verdict names them, and the
  ladder header says `TE · DEF open`, but a reader who stops at the fold sees the IR item and not
  the thin rooms.
- The review toggle still ships in the footer. It should not exist in the product.
