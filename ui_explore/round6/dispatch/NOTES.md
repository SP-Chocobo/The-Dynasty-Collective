# dispatch — the page as something READ, not parsed

**Question:** what if the page is a written dispatch with figures set into it, rather than a set
of labelled cards and a table the eye parses?

Files: `build_dispatch.py` (the builder), `dispatch.html` (from `front_fixture.json`, the loud
week), `dispatch_quiet.html` (from `quiet_fixture.json`, the quiet week — the primary state).
Run with `python3.13 ui_explore/round6/dispatch/build_dispatch.py` from the repo root (the
default `python3` here lacks numpy, which `front_claims` imports through `lineup_optimizer`).

## What changed about the COMMUNICATION, and why

**The lede is a paragraph, not a list of cards.** The base's hero said "Three things are open"
and then a sentence; everything else was cells. Here the whole situation is stated in one
paragraph at reading scale (21.6px serif): *Week 6 costs 95 in trade value, the largest of six
weeks measured, with 1 starter out. DEF and TE rate Weak against this league's own rosters; TE
on a priced floor, 1 of 2 priced. No current week is on file, so none of this carries a
deadline.* Every clause is a composer function of one fixture field (`bye_sentence`,
`thin_sentence`, `week_on_file`); there is no free text anywhere in the builder.

**The figure is pulled out of the lede, broadsheet-style.** The one number the page is about
(95, or 3 checks when quiet) sits at 72px mono in the right margin with its unit, the currency
stamp, and its provenance line under it. It is the same hero the deck has, but it belongs to the
sentence beside it rather than to a box.

**The bye weeks are written entries, not a table with bars.** Each week is a labelled entry:
`WEEK 6` / `95` / *Jahmyr Gibbs (RB · 95) is away. One starter out; the lineup that week is
worth 220.* The peak week's figure is 38px against 26px for the others, on a gold-railed tint —
the size and tone carry what the base's bars carried, so there is no severity ramp to fail
contrast. The names are a filter on `roster[].bye`; the two extra facts on the peak week are
`worst_week_detail.starters_out` and `.lineup_value`, which only exist for that week, which is
why only that week gets them.

**The checks are sentences that name what was examined.** *Holes — Nothing found. No slot the
league defines is left empty by the solver.* / *Byes — Raised. Week 6, above.* / *Depth —
Nothing found. No position rates Weak against this league's own rosters, and none is empty.*
The names, the count and the order come from `front_claims.checks_run`; the page never counts.

**Absences are stated once, in the dateline.** `no league name —` and `no week on file —` sit on
the masthead rule with their reasons on hover, and are not repeated per row. On the quiet page
the clock reads `week 15 CONSTRUCTED`, because the fixture's basis says the week is chosen, not
read. "Behind" is said once in the bye intro (*Weeks before 15 have passed*) and shown by tone
on the rows, not repeated seven times — the first build repeated it and it read as noise.

**A zero the base prints that is not a zero.** `capture_front_fixture.py:157` writes a roster
value as `trade_value or 0.0`, so 0.0 is "unpriced or priced at exactly zero", collapsed. The
base's ledger prints `Tyler Bass 0` and `Dawson Knox 0` while its TE card on the same page says
"1 of 2 priced" about Pitts (23) and Knox (0). Those cannot both be read as written. This page
renders a roster value of exactly 0.0 as `—` carrying that reason (`player_value`). This is an
inference from the capture's own code and the TE room's count, not from a field that says
"unpriced"; the right fix is for the capture to carry `None`, and that is recorded here rather
than silently papered over. A measured zero from `bye_collision` (week 6 costs 0 in the quiet
fixture; bench promoted 0) still prints as `0`, because that one is a measurement.

**Small counts are words.** *the largest of six weeks measured*; *Three checks ran*. This is
deliberately narrow: it applies to the SCOPE of a sentence (how many weeks, how many checks),
never to a measured figure. The first build had "the largest of the **6** weeks" two words after
"Week **6**", and a sentence opening with a numeral. Costs, week numbers, roster counts, shares
and starters-out are always mono (`b.n`), so the two kinds of number stay visibly distinct.

## Every sentence, traced

| sentence | field(s) |
|---|---|
| Week 6 costs 95 in trade value | `shown[bye].worst_week`, `.worst_week_loss`, currency stamp per `#341` |
| the largest of six weeks measured / still ahead | `len(bye_profile.weeks)`; "ahead" only when `ahead_only` |
| with 1 starter out | `shown[bye].starters_out` |
| DEF and TE rate Weak against this league's own rosters | `thin.label` grouped by label; never a rank |
| TE on a priced floor, 1 of 2 priced | `thin.priced_floor`, `.valued_count`, `.count` |
| No current week is on file, so none of this carries a deadline | `current_week is None` |
| Week 15 is on file CONSTRUCTED and the last measured bye week was 14, so every bye is behind it | `current_week`, basis stamp, `max(weeks)`, resolved `worst_week is None` + `_ahead_only` |
| Three checks ran — holes, byes, depth — and none raised a claim | `checks_summary(checks)` |
| X (RB · 95) is away | filter `roster[].bye == week`; value via `player_value` |
| One starter out; the lineup that week is/was worth 220 | `worst_week_detail`, tense from `current_week` |
| Across the season the byes cost 237; week 6 carries 40% of it. Unknown byes: 0 | raw `bye_profile.total_loss`, `.worst_week`, `.concentration` (None → dash with reason), `.unknown_byes` |
| Nothing found. No slot the league defines is left empty by the solver | `structural_holes == []` |
| Nothing ahead. Every measured bye week is behind week 15 | byes clean + `_ahead_only` + weeks present |
| Nothing found. No position rates Weak..., and none is empty | `thin_positions == []` (thin = WEAK + NO_PLAYERS) |
| Underlined names are in the lineup CONSTRUCTED by optimize_lineup | `starters` list, basis stamp |
| popover: lineup value / value lost / players away / of them starters / bench promoted / their value | the six `bye_collision` fields on `worst_week_detail` |

Nothing on the page says "worst", "best", "hurts", "strong roster", or anything about rank.

## What was kept from the base, and why

- `front_claims.compose` as the only judgment; the builder adds grammar, not quantities.
- Expansions as **popovers** (owner ruling 1): "What week 6 is made of" opens the six measured
  fields; each thin room opens rostered / priced / band with the not-a-rank note. Verified open
  in Chromium.
- Record off the front (ruling 2). Five rooms as a section nav line, one dock (ruling 3).
- The currency stamp on every bye figure (ruling 4).
- The quiet state as primary (ruling 5): it carries a full lede, the 3-checks figure, CLOSE THE
  APP (the one control `VOICE.md` says to keep), the season's bye account in past tense, and the
  three checks written out with their bases. It does not read as three small lines.
- `design_system.root_css_block()` / `position_pill_css_block()` for the palette; position colour
  on every name; the gold gradient on the wordmark measured off the logo; the provenance line in
  mono under every figure; fading gold tint on the peak row.

## Measured gates

Rendered with Playwright/Chromium (`browser_binary.find_chromium()`, `--no-sandbox`), fonts
from Google Fonts. Numbers below are from the final build.

| gate | dispatch.html | dispatch_quiet.html |
|---|---|---|
| minimum computed font size | **12.0px** (`.stamp`, declared .75rem) | **12.0px** |
| horizontal overflow at 390px | **none** (scrollWidth 390 = clientWidth 390) | **none** |
| scroll height at 1280px | 1710px | 1697px |
| scroll height at 390px | 3304px | 2877px |
| console errors / page errors | **0** | **0** |
| popover opens on click | yes (`pop-bye`) | yes (`pop-bye`) |

For comparison the base measures 1283 / 2746 (loud) and 1164 / 2136 (quiet) at the same widths.
This page is ~33% taller at 1280 and ~20% taller at 390: sentences take more room than cells.
That is the cost of the direction and I am not hiding it.

**Type scale** (declared, rem at 16px root): 12 · 12.5 · 12.8 · 14.4 · 16 · 17.6 · 20.8 · 21.6 ·
25.6 · 38.4 · 44 · 72. Range 6:1, with the jumps where they matter: body 17.6 → lede 21.6 →
headline 44 → pulled figure 72.

**Non-text contrast, every mark, against every ground it sits on** (`design_system.contrast_ratio`
and `_contrast_hex` for pill hexes; floor 3:1; asserted at build):

| mark | vs `bg` | vs `surface` |
|---|---|---|
| gold (eyebrows, underline) | 7.40 | 6.92 |
| gold-b (pulled figure, peak rail, raised bullet) | 12.53 | 11.72 |
| status-ok (clean tick) | 11.64 | 10.89 |
| muted (absent dash, stamp border) | 7.89 | 7.38 |
| dim (provenance) | 4.82 | 4.51 |
| QB / RB / WR / TE / K / DEF squares | 5.31 / 6.68 / 7.66 / 6.59 / 11.51 / 7.97 | 4.97 / 6.25 / 7.17 / 6.17 / 10.76 / 7.46 |
| DL / LB / DB / IDP (unused here, still asserted) | 12.63 / 6.90 / 11.95 / 7.60 | 11.81 / 6.45 / 11.18 / 7.11 |

`line` (1.27) and `line-2` (1.73) are used only as decorative rules and carry no information.

**Body text ≥ 4.5:1**: ink 16.52 / muted 7.89 / dim 4.82 on `bg`; asserted at build
(`_assert_text_legible`). `dim` is used only for provenance and the legend.

**Tap targets:** every `.btn` and `.door` is ≥ 44px tall (doors 44, buttons 44, CLOSE THE APP
48). The elements under 44px are the inline glossary spans (`.stamp`, `.absent`, `.currency`),
which carry `tabindex=0` and a `title` — the same device the base uses. They are not controls,
but **their reasons are unreachable on touch**, where `title` tooltips do not show. That is a
real gap shared with the base and the deck, and it is the right place for the popover ruling to
extend next.

## What I believe is wrong with this result

1. **It is taller.** 1710 vs 1283 at desktop. A dispatch is longer than a ledger by nature. The
   three-column body mitigates it at 1280; at 390 the reader scrolls 3300px. If the owner wants
   the three-second answer AND the ledger above the fold, the base's table wins on density.
2. **The reading face is not a token.** `FONT_TEXT` (Source Serif 4, the deck's own text face) is
   declared once in the builder with a comment saying so. If this direction is taken it belongs
   in `design_system` beside the other three faces — one home, `#126` — and the builder should
   import it. I did not add it to `design_system` because the brief confines me to this directory.
3. **The 0.0-as-unpriced rendering is an inference**, defended above, but an inference. The
   fixture should carry `None`. Until it does, this page and the base disagree about Bass, Knox
   and Borregales, and one of them is wrong; I believe it is the base.
4. **The right two columns run short.** On the loud page "Checked" ends 600px above "The bye
   weeks"; on the quiet page there are two columns and the right one ends at half height. A
   broadsheet has this too, but it is empty ground on a 1280 screen.
5. **The quiet bye account is inert by the owner's own test.** Seven past weeks ask nothing of
   the reader. I kept it because the brief says to communicate the SAME information as the base,
   whose quiet page keeps the ledger, and because without it the quiet page is the lede and three
   checks. It is dimmed and written in the past tense, but it is the one block on the page that
   fails "does it ask anything of me?", and if ruling 2 is applied strictly it goes.
6. **Hidden claims are built but unexercised.** Neither fixture produces more than `CAP` claims,
   so the "Also standing" line in the Checked column has never rendered. It is one `join_names`
   over the hidden claims' own fields; it needs a four-claim fixture before it is trusted.
7. **The "(RB · 95)" parenthetical is the one place the sentence still parses.** It is a chip in
   prose clothing. I tried the names bare and lost the position colour the direction requires;
   this was the smaller loss.
