# The Threshold — refinement record

What changed after `CRITIQUE_DESIGN.md`, `CRITIQUE_PRODUCT.md`, `VOICE.md` and the corrected `BRIEF.md`;
what was taken, what was rejected and why, and what was measured. `NOTES.md` is the round-1 record and is
superseded where this file says so.

Files now: `desktop.html` / `mobile.html` (quiet, constructed seat), `desktop_loud.html` / `mobile_loud.html`
(the real week-6 seat), `desktop_unknown.html` / `mobile_unknown.html` (no league synced — the committed
`empty_fixture.json`). All six are emitted from one generator (one stylesheet, one content table, a
`pick(long, short)` for the phone), so the copy drift the design critique found cannot recur.

## The three states, and what tells them apart on the FIRST SCREEN

The design adversary's severest finding: replacing every ledger value with "not measured" left the first
screen byte-for-byte unchanged, because the page had two faces for a three-valued condition. It now has
three, and the difference is above the fold in four places at once:

| | quiet | loud | unknown |
|---|---|---|---|
| **verdict** (96px Cinzel, same slot, same y=199) | *Nothing is open.* | *Week 6 costs 95.* | *No check ran.* |
| **the metal** | `--metal-rest` (bright → body → deep) | `--metal` (specular → bright → body → deep) | **unlit**: flat `--ink-2`, no gradient, no struck shadow; the rule and its diamond go `--ink-3` and the lamp drops to 12% |
| **eyebrow** | *Four checks ran, all clean — starters, holes, depth, byes. Three could not run, and say why below.* | *One thing is open. Two can wait. Four checks ran; three could not …* | *No league is synced on this machine, so none of the seven checks could run.* |
| **primary control** | CLOSE THE APP (alone) | OPEN MATCHUP, with CLOSE FOR NOW beside | OPEN IMPORT AUDIT, with CLOSE FOR NOW beside |
| **header, right** | `Team 1 [constructed]` · `— league not named · — no sync` | same | `— no team: no league synced on this machine` |

The verdict is no longer the absence of a claim. It is derived, in copy, from the count of checks that ran:
"Four checks ran, all clean" (quiet), "One thing is open" (loud), "No check ran" (unknown). The adversary's
experiment — blank the ledger — now changes the eyebrow's count, the headline, the lighting, and the primary
control. The unknown state's only lit thing is the one row that *did* run (Sources: Aging, 76 d), marked
`.live`, so a reader scanning the ledger sees one gold key and six em dashes.

The lighting is now a three-level channel for a three-valued condition, which is what the design critique
called "the design's own logic finished rather than overridden."

## Taken

**Voice (`VOICE.md`, binding).** Every headline and label rewritten to the indicative with the week or the
roster as subject. `Nothing needs you.` → **Nothing is open.** (I did not use the table's "this week" because
`current_week` is ABSENT on a replayed seat and the week would be a fabrication; the sentence is
otherwise the table's). `Week 6 needs you.` → **Week 6 costs 95.** (rule 1's literal example; the two
numerals are set in JetBrains Mono inside the Cinzel line, because the brief's numerals rule has no
headline exemption). `every check the engine can run came back clean` → **Four checks ran, all clean —
starters, holes, depth, byes. Three could not run** (rule 5 licenses naming, not completeness). `CLOSE THE
APP` kept exactly. "needs you", "the app", "all clean" as a pronouncement — gone.

**Design 1 / Product "fourth tone" — the unknown state.** Built, both devices, from the repo's own committed
measurement (`empty_fixture.json`: `state: no_league_synced`, grade Aging, worst 76 d, two sources never
fetched). Nothing on it is constructed. It is the state this design previously got wrong at 96px.

**Design 2 + 5 — the lurch and the 58% padding.** `.threshold` is `padding:72px 0 36px; min-height:0;
display:block` in every state. Measured: eyebrow top **152** and verdict top **199** in quiet, loud and
unknown — zero displacement (was 108px). Quiet desktop went 1500 → **1356** (1329 before the ledger's right
column was allowed to wrap so a stamp and a strip never overlap the sentence); the ledger head is at 478 and
the first three rows are above the 800 fold; the fold now falls in the Byes row's text, not through a
bordered stamp (the Byes stamp sits 767–790; an earlier padding put it at 787–810 and I moved it).

**Design 3 — the plural verdict.** `white-space:nowrap` removed; `font-size:clamp(54px, 7.5vw, 96px)`,
`text-wrap:balance`. Measured at 1280: "Two things are open." and "Three things are open." wrap to two lines,
`h1.scrollWidth` = box width, document scrollWidth stays 1280. At 1110 (the band the critique found
overflowing) and 1024: one or two lines, no overflow. The 1100px breakpoint is gone; the clamp replaces it.

**Design 4 — loud mobile.** Built. Order on the phone: eyebrow, verdict, dek, **figure (95 + strip) before
the controls**, rule, controls, Can wait, receipt, rooms, basis. The 95 is on the first screen (its top at
~y=560 of 664). Full-width buttons (an inherited `align-items:start` had left them at 237px; fixed).

**Design 6 — desktop navigation affordance.** The colophon now wears the ledger's grammar: a `ROOMS` head
with a one-line note, each door a 50px link with a gold chevron and a hairline underline, hover brightens.
Mobile: a two-column grid of 44px cells with chevrons. Same component, two densities. The note says, as the
product critique asked, that the Prytaneum is a dock under every view and where Trade Calculator, Free
Agents and Standings live.

**Design 7 / cross-cutting — chart bars below 3:1.** Solved at the palette level, not by nudging a hex: a
recede bar is a **struck outline** in `--gold` (1.5px stroke, `vector-effect:non-scaling-stroke`), never a
dark fill; only the worst week is solid, in the lit metal. Measured from rendered pixels of the actual pages,
mark against the ground beside it: loud rest bars **6.37–7.34:1**, worst week 18.18:1; quiet rest bars
**6.45–7.34:1**, worst 18.27:1. A 2.9px bar is now a visible loop rather than an invisible smear. Six labels
stay on the loud strip (the chart is now the *only* place the six numbers appear — the ledger's Byes row no
longer recites them); the quiet strip is still shape-only with the number in the sentence.

**Design 8** — `background: var(--c, var(--unknown))` with `--unknown: #b0a28a`, the brief's ruled token.
**Design 9** — `.door` is now 17px, `--gold-bright`, gold underline, chevron, `:focus-visible` ring; no longer
confusable with section heads. **Design 10** — aside shown on mobile; `Seen 11:41 pm` (short label, wraps
allowed); hairlines raised to `.32`/`.5`; eyebrow copy generated, not hand-maintained.

**Product 1 — the false injury sentence.** Deleted from the quiet pages (an empty flag list is silence, per
`app.py:3857`). On the loud page the row now says the measured thing, verified by me against
`sleeper_capture.json` (`12484` Jayden Higgins, WR, `IR`; `is_material_injury_status("IR")` → True):
*"10 of 10 filled. The optimizer ignores injuries, and it started Jayden Higgins, WR, who is on IR."*
Wan'Dale Robinson (Questionable) stays unmentioned. The flag is reported in the ledger, not promoted to the
verdict, because `front_claims.LADDER` has no injury rung — the ladder's ruling stands.

**Product 2 — completeness.** The eyebrow counts what ran. Two rows added to the ledger on every page, both
absent with reason: **Clock** (*no draft clock reaches this page yet; a pick on the clock would outrank every
row here* — `LADDER`'s top rung, unwired) and **Sources** (*not captured on this seat* on the replayed pages;
the real Aging/76 d on the unknown page). Seven rows, the same seven, every state.

**Product 3 — `synced 11 min ago · sources Fresh`.** Deleted. The header carries `Team 1 [constructed]` and
two em dashes with reasons; freshness lives in the Sources row where it can be absent honestly.

**Product 4 + 6 + 7 — "measured" above the fold on fabricated rows; unstamped rows; byte-identical Holes.**
The quiet aside now says *A constructed seat: the four figures below are fabricated … and each carries the
stamp for it. Nothing here is measured.* Holes, Depth and Byes each wear `constructed` on their own row (tooltip
names it a demo figure); the ledger head wears `quiet state · constructed`; mobile hides none of them. The
quiet strip's `aria-label` says "Constructed bye profile … fabricated for the quiet state." The loud Holes row
is identical text with no stamp — which is now the distinction, as the product critique asked.

**Product 5 / brief correction — "bottom of the league".** Struck. DEF: *Weak — 1 rostered, under 0.7× the
league's average at the position, counted on bodies.* TE: *Weak on priced depth — 2 rostered; only 1 of 2
could be priced, so the comparison is a floor, not a total* + `≥ floor`. The label, never the rank.

**Product 8 — futurity.** The dek carries the baseline's disclosure: *The whole season is counted, played
weeks included: today's week is not known on this seat.* The quiet eyebrow no longer invents a week.

**Product 9 — the unpriced zeros.** The figure now wears two stamps beneath it, `measured` and
`3 of 16 unpriced`, with the sentence *Week 6 holds: the one starter out is priced and no bench body covers
him. The other five weeks can move either way.* — verified against `worst_week_detail` (`players_out 1`,
`starters_out 1`, `bench_used 0`, `value_lost 95` = Gibbs's 95). The right vocabulary is now on the
largest number, not only on the smaller one.

**Product 10 + 11** — "Every position rates Average or Strong" is gone; the row says *Nothing you roster is
thin*, which is safe by construction. **Product 12** — the `constructed` tooltip on Starters says the
construction forecloses any other reading. **Product 13** — `Team 1` + stamp, league as an em dash; "battery
seat" jargon removed from the page. **Product 14** — thin rows route to **League**, as `front_claims.compose`
rules; my round-1 override is withdrawn. **Product 16** — "entire" dropped; "every *starting* slot"; "player
universe" not "pool"; the Prytaneum marked as a dock.

## Rejected, with the argument

1. **"Keep the bevel" — the headline gradient contrast.** My NOTES confessed the gradient's bottom dips to
   2.9:1. The design adversary measured rendered glyphs at **4.42:1 (quiet) and 5.21:1 (loud)**: with
   line-height 1.04 the `--gold-deep` stop lands below the baseline and no glyph pixel reaches it. I was wrong
   in my own disfavour. The gradient is unchanged; the confession is withdrawn here so nobody re-flags it.

2. **The primary button's justification.** NOTES said "6.8:1 at the darkest stop." The darkest stop is
   `#755024`, on which the ink is 2.64:1 — the figure I quoted was against `--gold` at the 64% stop. The
   rendered outcome under the glyph band is **6.98:1 minimum**, so the button is right and the reason was
   wrong. Button unchanged; the record corrected.

3. **Folding the loud-mobile receipt.** The design critique's rule is "present on one device and missing on
   the other without a stated reason." On the loud phone the full seven-row ledger does not fit the 1328px
   budget alongside the claim, the figure, two controls and the two can-wait rows; I tried, at 1634px. It is
   now a `<details>` whose 44px summary reads *WHAT WAS CHECKED — four ran, three could not — open the
   receipt*. The reason is stated here: the loud phone's two screens belong to the claim; the receipt is one
   tap away and its counts are in the summary. Quiet and unknown phones keep the ledger open, because there
   the ledger *is* the content.

4. **"Nothing open this week."** `VOICE.md`'s table offers it; I used *Nothing is open.* because
   `current_week` is ABSENT on every replayed seat and "this week" would be the only fabricated word on the
   first screen. In production, where Sleeper's NFL state supplies the week, the table's string is the
   better one and should be used.

5. **Promoting the IR flag to a claim.** The product critique noted threading `compute_readiness` would make
   "a better page, because the quiet state stops being quiet for a real reason." I report the flag in the
   ledger but do not promote it, because `front_claims.LADDER` (clock, hole, bye, thin) has no injury rung
   and the module exists so that no surface grows a second ranking. If the ladder gains a rung, the page
   should follow it; it should not lead.

6. **Hover tooltips on the strip.** The dataviz guidance wants a per-mark tooltip. The six values are
   direct-labelled and the page has no other interaction; a hover layer on a 44px bar on a page whose thesis
   is "leave" is weight without a job. Not built; stamps carry `title` tooltips where the basis needs a
   longer sentence than the row can hold (desktop only — they do not fire on touch, which is a real gap
   noted below).

7. **Matchup cannot show the bye profile (Product 15).** True and upstream: `bye_collision` has no `app.py`
   call site. The route stays `Matchup` because `front_claims` rules it; the page makes that wiring
   load-bearing rather than optional, and says so here.

## Measured (final)

Repo Chromium via `browser_binary.find_chromium()`, `--no-sandbox`, DPR 2, after `document.fonts.ready`,
Cinzel / EB Garamond / JetBrains Mono confirmed loaded.

| file | viewport | min font | overflow-x | scrollW | scrollH | taps < 44 | console | eyebrow / verdict top |
|---|---|---|---|---|---|---|---|---|
| desktop.html | 1280×800 | 12.0 | none | 1280 | **1356** (was 1500) | none | 0 | 152 / **199** |
| desktop_loud.html | 1280×800 | 12.0 | none | 1280 | 1920 | none | 0 | 152 / **199** |
| desktop_unknown.html | 1280×800 | 12.0 | none | 1280 | 1431 | none | 0 | 152 / **199** |
| mobile.html | 390×664 | 12.0 | none | 390 | **1280** | none | 0 | 78 / 134 |
| mobile_loud.html | 390×664 | 12.0 | none | 390 | **1308** | none | 0 | 78 / 110 |
| mobile_unknown.html | 390×664 | 12.0 | none | 390 | **1261** | none | 0 | 83 / 115 |

Budget 1328 on mobile: met on all three, with 48 / 20 / 67 px of margin. The mobile verdict is not pinned
across states (eyebrow lengths differ); the desktop one is.

Rendered-pixel contrast, chart marks (mark vs the ground beside it): loud rest bars 6.37–7.34:1, loud worst
18.18:1; quiet rest 6.45–7.34:1, quiet worst 18.27:1. Headline glyphs (adversary's measurement, accepted):
4.42:1 quiet, 5.21:1 loud; the unknown headline is flat `--ink-2` at 7.9:1 on black. Primary button ink
under the glyph band: 6.98:1 minimum.

## Still wrong or weak, honestly

- **Stamp tooltips do not fire on touch.** The long bases (`constructed — the optimizer's best legal lineup …`,
  `a floor from incomplete pricing …`) live in `title` attributes, so a phone reader sees the stamp word
  only. The phone pages compensate with shorter sentences on the rows, but the full reason is desktop-only.
- **The loud phone hides the receipt behind a tap.** Defended above, but it is a real asymmetry: the one
  device where the ledger is a tap away is the one where the data is real.
- **Mobile loud has 20px of budget margin.** A Cinzel metric revision or a longer player name in the Starters
  row would push it over. The quiet and unknown phones have 48 and 67.
- **"OPEN IMPORT AUDIT" is my routing.** `empty_fixture.action` says "Sync a Sleeper username in the sidebar";
  the rewrite has no sidebar, and Import Audit is the data room that exists. If the sync lives elsewhere in
  the real front end, the label should follow it.
- **The unknown page's header stacks three em dashes** (`— no team`, `— league not synced`, `— never
  synced`), which is correct grammar and a little grim. A page with nothing on it has nothing else to say.
- **Both desktop "rooms" notes are long** (two lines of italic at 1280). They say true things the colophon
  owes the reader, but a sharper editor would halve them.
- **The quiet state is still entirely constructed**, now with seven stamps on the desktop page. It is the
  honest version of a demo of a state the real seat cannot produce; it is not serene any more, and the
  product critique was right that this is the correct trade.
- **The `measured` stamp on the loud figure overstates** in one respect the product critique raised: the
  basis token cannot record the three substituted zeros, so `measured` sits beside `3 of 16 unpriced` rather
  than being qualified by it. That is the truth of the engine today; `basis_semantics.BOUNDED_INPUT` is the
  token this should wear once something reports pricing coverage.

## Component inventory — additions and changes

The ten components in `NOTES.md` stand, with these changes:

- **Verdict (2)** now has three faces — rest, lit, unlit — and wraps; the clamp replaces the one-line rule.
  Dependency added: the eyebrow directly above it must carry the count of checks that ran, or the verdict is
  a pronouncement again.
- **Close control (3)** unchanged in form; in the unknown state it is secondary to OPEN IMPORT AUDIT.
- **Ledger (4)** is seven rows and has a fourth row kind, `.absent`, plus `.live` for the one measured row on
  an otherwise-absent page. On the loud phone it folds; folding is a property of the phone layout, not of the
  component.
- **Bye strip (5)** recede marks are outlines; this is the portable rule — *a recede bar is a stroke in the
  body gold, never a dark fill* — and it is what makes the strip legal on any dark ground in the system.
- **Colophon (8)** now has one grammar on both devices (hairline, chevron) at two densities.
- **New: the unknown face.** Not a component so much as a rule every component obeys: when nothing ran, the
  metal is unlit, the rule is grey, the lamp is dimmed, and the only gold is on the row that did run. Lift
  the rule, not the CSS.

If only one thing survives, it is still the close control — and now the eyebrow count that licenses it.
