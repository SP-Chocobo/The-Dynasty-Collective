# `ledger` — the ledger is the spine

> What if the LEDGER is the spine — one continuous, scannable record rather than a set of panels?

Files: `build_ledger.py` (the builder; renders both fixtures), `ledger.html` (loud,
`front_fixture.json`), `ledger_quiet.html` (quiet, `quiet_fixture.json`). Build with
`python3 ui_explore/round6/ledger/build_ledger.py` from the repo root — the interpreter needs
`numpy` because `front_claims` imports `lineup_optimizer`; in this container that is
`/usr/bin/python3`, not `/usr/local/bin/python3`.

## What changed about the communication

**One container instead of four.** The base is a hero, a two-column body (bye ledger | open
claims) and a cleared strip. Each box has its own header, border and basis caption, and the
reader learns the page by learning the boxes. Here there is one `<ol class="register">`, one
rail down its left, and every fact is a ROW: the verdict, each open claim, each bye week, the
season total, each check, and the provenance. Nothing has a header of its own; the fixed left
margin column IS the header, and it says what KIND of row you are looking at.

**Seven row kinds, and four signals that tell them apart at once.** This is the answer to the
risk in the question — that an undifferentiated list is worse than panels. A row is told apart
by its margin label (Cinzel, the kind word), its rail marker (a 13px diamond for the answer, 9px
gold dot for an open claim, 5px dim dot for a week, 7px bright dot for the worst week, hollow
green ring for a clean check, gold dot for a fired one, nothing for dividers), its figure scale
(48 / 28 / 17–21 / none) and its weight (a bordered gradient box only for the rows that ask
something — the answer and the open claims; everything else is bare, separated by fading gold
hairlines). The screenshot test I set myself was: with the text blurred, can you still see where
the open items end and the record begins? At 1280 you can — three boxes, then rhythm.

**The checks row lists all three checks, not only the clean one.** The base's "Cleared" strip
shows checks that passed; on the loud fixture that is one tile ("Holes: nothing found"), and the
other two checks exist only by implication. Here `byes` and `depth` appear as fired rows that
read `raised — week 6, above` and `raised — DEF, TE, above`, each with its basis. VOICE rule 5
("name the checks, not the conclusion") wants the audit to be complete, and a ledger of what was
examined that omits the entries that found something is the complement of an audit, not an
audit. The head row states `3 of 3 checks ran` from `checks_summary`, never from `len()`.

**Weeks behind the current week collapse to one row.** On the quiet fixture `current_week` is
15 and all seven bye weeks are behind it. The base draws seven rows of played weeks with the
worst one un-highlighted — nothing says they are over except the absence of a highlight. The
brief: "an absence identical on every row is noise — state it once." So this page prints one
row — `All 7 bye weeks are behind week 15.` — with an `Each week` popover carrying the seven
weeks and who was away (ruling 1: a popover, not inline). The rule is general: ahead weeks are
rows, behind weeks are one row; a mid-season fixture would show both. This single change is why
the quiet page is 955px at 1280 against the base's 1164, and it is the main reason the quiet
page reads as *quiet* rather than as *short*.

**The bye popover is `worst_week_detail`, not the week table again.** The base's "What it is
made of" for the bye claim re-draws the week strip that is already on the page beside it. Here
the weeks are rows of the register, so the popover shows what the engine computes separately and
the base never surfaces: value lost, that week's lineup value (220), starters out, players out,
bench promoted and the value promoted, share of the season. Every field is a key of
`bye_profile.worst_week_detail` or `bye_profile`; nothing is summed or derived.

**Absences are gathered into one provenance row at the foot.** The base puts `no league name —
no week —` in the top bar beside the team name. Here the masthead carries only `Team 1`, and a
`PROVENANCE` row at the end of the register lists seat (with its `CONSTRUCTED` tag), league
(dash with reason), week (dash with reason on the loud page; `15 CONSTRUCTED` on the quiet one,
because the quiet fixture's own basis says the week was chosen), the players-capture date read
off `_provenance.players_db`, the battery arm, and `record — off this page, why`. Each absence
is labelled with the quantity it is an absence OF, so it reads as information and not as a
broken template.

**The bye claim's body no longer says "still ahead" when it cannot.** With no `current_week`,
`byes_ahead` cannot establish futurity, and the base's card still reads "The largest of the weeks
still ahead." Here `ahead_only` decides the sentence: `The largest of the 6 weeks still ahead.`
when a week is on file, otherwise `The largest of 6 measured weeks; no current week is on file,
so whether it is ahead is not known.` The 6 is `len(weeks)`, a count of real things.

## What is kept from the base, and why

- `front_claims.compose` is the only judgment on the page. Shown/hidden, order, cap, checks and
  the resolved bye profile all come from it; the builder arranges and never computes.
- The figure is the hero, in mono, with negative tracking; Cinzel never carries a numeral. The
  week rows set `WEEK` in Cinzel and the number in mono beside it, because `WEEK 11` in
  letterspaced Cinzel reads as Week II.
- The currency stamp on every bye figure (`trade value`, dotted gold underline, reason on hover),
  including inside the popover and on the season total.
- Popovers for expansion (ruling 1), with the same "what expands must be computed separately"
  rule — the bye, thin and hole popovers each show a separately computed layer; there is no
  injury row and so no popover that would have to invent severity.
- The severity ramp `dim → gold → gold-b`, brightness rising with severity, asserted visible at
  build time; the same three tokens are reused for the rail markers so one gate covers both.
- Small type in `rem` throughout, asserted ≥ 0.75rem at build time, `em` refused.
- `design_system.root_css_block()` and `position_pill_css_block()` as the only palette source;
  the gold gradient hexes measured off the logo are the one exception, as in the base and
  `deck`.
- Five rooms in the masthead and the Prytaneum as a dock under the register, not a sixth room.
- Record off the front page, and the page says where it went and why.
- The verdict's grammar: headline statement, then prose that collects the thin rooms into one
  clause, then the deadline caveat.

## Gates — measured, not assumed

Rendered with Playwright on the container's Chromium (`browser_binary.find_chromium()`,
`--no-sandbox`), viewports 1280×800 and 390×844, after the last edit. The probe walks every
element with a direct text node and reads `getComputedStyle().fontSize`.

| | loud 1280 | loud 390 | quiet 1280 | quiet 390 |
|---|---|---|---|---|
| min computed font | 12.16px (`DYNASTY` wordmark line) | 12.16px | 12.16px | 12.16px |
| horizontal overflow | none (scrollWidth 1280) | **none (390)** | none (1280) | **none (390)** |
| scroll height | 1722px | 3132px | 955px | 1761px |
| interactive targets < 44px | 0 | 0 | 0 | 0 |
| console errors / page errors | 0 | 0 | 0 | 0 |

Base, same probe, for comparison: loud 1283 / 2746, quiet 1164 / 2136. The quiet page is shorter
than the base on both devices; the loud page is longer on both, and that cost is discussed below.

Computed font-size set on the loud page at 1280 (px): 12.16, 12.48, 12.8, 13.12, 13.44, 13.76,
14.4, 15.2, 16.8, 17.92, 20.8, 21.12, 28, 37.6, 48. The scale spans 12 → 48 with real jumps at the
top (21 → 28 → 37.6 → 48); the phone drops the hero to 40 and the headline to 27.5.

Interactive targets: every `button` and `a` is ≥ 44px tall at both widths (doors, the two buttons
on each open row, `Each week`, `Close`, the dock). The dotted-underline help spans (`absent`,
`currency`, `tag`, `why`) are 17px inline text with `tabindex="0"` and a `title`; they are not
tap targets and are not counted — the same convention the base uses.

### Non-text contrast, every mark, against every ground it can sit on

`design_system.contrast_ratio` is the instrument; `_assert_marks_visible` fails the build under
3.0:1 on any of `bg`, `surface`, `surface-2`. Both open-row boxes and the caption run a
`surface → surface-2` gradient; everything else sits on `bg`.

| mark | token | on bg | on surface | on surface-2 |
|---|---|---|---|---|
| rail (the spine) | dim | 4.82:1 | 4.51:1 | 4.66:1 |
| marker: week | dim | 4.82:1 | 4.51:1 | 4.66:1 |
| marker: open claim | gold | 7.40:1 | 6.92:1 | 7.16:1 |
| marker: the answer | gold-b | 12.53:1 | 11.72:1 | 12.12:1 |
| marker: check clean (ring) | status-ok | 11.64:1 | 10.89:1 | 11.26:1 |
| marker: check fired | gold | 7.40:1 | 6.92:1 | 7.16:1 |
| bar: recede | dim | 4.82:1 | 4.51:1 | 4.66:1 |
| bar: mid | gold | 7.40:1 | 6.92:1 | 7.16:1 |
| bar: hot | gold-b | 12.53:1 | 11.72:1 | 12.12:1 |
| check tick | status-ok | 11.64:1 | 10.89:1 | 11.26:1 |
| chip square QB | #2a81fc | 5.31:1 | 4.97:1 | 5.14:1 |
| chip square RB | #0ca89c | 6.68:1 | 6.25:1 | 6.46:1 |
| chip square WR | #4aa8ef | 7.66:1 | 7.17:1 | 7.41:1 |
| chip square TE | #ff6042 | 6.59:1 | 6.17:1 | 6.38:1 |
| chip square K | #fab87e | 11.51:1 | 10.76:1 | 11.13:1 |
| chip square DEF | #ef7fc0 | 7.97:1 | 7.46:1 | 7.71:1 |
| chip square DL / LB / DB / IDP | — | 12.63 / 6.90 / 11.95 / 7.60 | ≥ 6.45 | ≥ 6.67 |

The rail is deliberately `dim`, not a fading gold hairline: the brief names rails in the
non-text gate, and `line-2` at 1.73:1 would have been a spine nobody could see. The fading
hairlines between rows are decoration at ~22 % opacity and are not marks; nothing is encoded in
them.

### Body text ≥ 4.5:1

Also asserted at build time (`TEXT_TOKENS`, floor 4.5, all three grounds): ink 16.52 / 15.45 /
15.97, muted 7.89 / 7.38 / 7.63, **dim 4.82 / 4.51 / 4.66**, gold 7.40 / 6.92 / 7.16, gold-b
12.53 / 11.72 / 12.12, status-ok 11.64 / 10.89 / 11.26. `dim` carries the basis lines and margin
qualifiers, which a reader is expected to read, so it is held to 4.5 here rather than to
design_system's 3.0 recede-role floor; it clears `surface` by 0.01. If the palette ever darkens
`dim` by a hair, this build fails, which is the point.

### Gates confirmed to fire

Checked in a scratch run, not by reading: a `line-2` rail fails the marks gate (1.73:1), a
`.7rem` declaration fails the type gate, and a `1.2em` declaration fails the `em` refusal. The
real build passes all three.

## What I believe is wrong with this result

1. **The loud page is longer than the base** — 1722 vs 1283 at 1280, 3132 vs 2746 at 390. A
   register is sequential by construction: the base puts the week table beside the claim cards
   and gets both above the fold; this page puts the claims first and the weeks beneath them. On
   the loud fixture at 1280 the fold (800px) shows the answer and all three open rows but no
   week; the weeks begin at ~810. I think that order is right for a triage surface (what asks
   something before what explains it) but it is a real cost against the owner's "three seconds",
   and a two-up arrangement of the week rows on wide screens would recover ~300px without
   breaking the register. Not done here because it reintroduces a second column, which is the
   thing this exploration was asked to try living without.

2. **The 95 appears twice** — in the answer row and in the bye row beneath it. The base and
   `deck` both do this too (statbox + card). I kept the duplicate because the answer row's figure
   is "the three-second answer" and the bye row's is the record entry, but a reader who notices
   will ask why. The alternative — making the lead claim the first entry at hero scale and
   dropping the separate answer row — collapses the headline sentence into a claim box and I
   could not make it read as a verdict.

3. **The thin rows weigh as much as the bye row.** All three open rows are boxed at the same
   weight, distinguished only by the left rule colour (gold-b lead, gold bye, line-2 thin) and
   the figure colour. The ladder says thin is the lowest rung. A lighter treatment for thin rows
   — bare, no box — would honour the ladder but would also make them look like checks, which
   they are not. I left them boxed; the rail marker and margin still say `OPEN`.

4. **The phone's open rows are tall** (~340px each at 390). The header-line-plus-body layout
   gives the prose full width, but two 44px buttons stack into two lines when the route label is
   long. Shortening `What it is made of` to a glyph would help and would lose the owner's phrase.

5. **The provenance row is a tail, not a row.** It is the one place where the register's "margin
   names the kind" grammar is stretched: `PROVENANCE` is a kind of nothing in particular. It is
   where the absences had to go once I took them out of the masthead, and gathering them is
   better than scattering them, but it sits at the foot where few will read it.

6. **Only two fixtures were rendered.** No hole has ever fired in a fixture, so the `hole` open
   row and its popover are exercised by the code path only, never by a screenshot. The same is
   true of the `Also standing` overflow row (the loud fixture has exactly `CAP` claims) and of a
   mixed ahead/behind week state. The adversarial fixtures in `ui_explore/states.json` would be
   the next render.
