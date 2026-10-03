# Adversarial review — set A (round 2)

Method: read all 20 PNGs in `fableA/_shots/`, re-rendered all four variants in all three states at
1440×900 with the Chromium at `/opt/pw-browsers`, instrumented the DOM for minimum resident font,
below-fold content and overflow clipping, and checked every claim in `RATIONALE.md` against
`states.json` rather than against the prose.

**Credit where it is owed, once, then I stop being nice.** The 12px floor holds — measured minimum
resident font is exactly 12.0px in all twelve renders. No page scroll anywhere. No re-based scale,
no invented field, no rival take-probability, no necessity badge, no `0.0` printed for an unmeasured
`depth_exposure`, and the measured depth digit (7.1 / 7.1) appears at `late` and nowhere else —
correct. Most importantly, **the subtraction from `ADJUDICATION.md` §6 actually gets performed**:
"wait cost favours him first by 2.2" is the arithmetic four round-1 variants rendered the inputs to
and never did. I verified the numbers: WR 5.55 / RB 7.78 → 2.23 at `mid`; WR 48.06 / RB 38.17 → 9.89
at `early`; WR 9.36 / QB 0.77 → 8.59 at `late`. All correct. This set is materially better than
round 1.

Now the problems.

---

## 1 · Verdict per variant

### v1 `ledger` — **survives, and is the only one I would build from.**
It is the one variant where I can answer who, why, what else and at what cost in under five seconds
at every state. The rail is solved: 5–7 named past boxes, YOU ARE UP, a tick span, YOUR NEXT, with
nothing blank — this is the round-1 twelve-empty-boxes finding genuinely dissolved rather than
restyled. The summoned position table (`which position?`) is the best object in either set. The
`late` headline is still wrong — a 48px `−34.6` sitting directly above an amber sentence that says
"read the gaps, not the levels", which is a surface arguing with itself — and the board strip at
`late` silently drops the only RB and the only TE below the fold while captioned "7 NAMES". Both are
fixable without touching the concept. Survives.

### v2 `lanes` — **concept survives, this execution does not.**
The no-rail answer is the best thing in the set and the four-equal-lanes pool is the worst. One
sentence — "You pick again at 12.07 (#139), after 12 picks — rosters 7, 8, 9, 10, 11, 12 each pick
twice" — carries more than any rail in either round at a twentieth of the pixels. It is also the
only variant that hands a whole quarter of the viewport to a position that has no candidates
(`early` QB, `mid` TE), tells the drafter twice in 100px that there is no quarterback, truncates the
*name* in the third comparison column at `mid` ("Jameson …"), and at `late` renders a one-column
table captioned "THE ONE AT TE, **SIDE BY SIDE**". Keep the clock sentence and the within-position
table; throw the lanes away.

### v3 `trio` — **does not survive.**
It is the densest surface in the set and the owner rejected round 1 for density. Twenty-four rows
each carrying three identical A/B/C buttons is 72 buttons down the right third of which three are
ever lit. The rail reintroduces exactly the defect the brief said was free to avoid: twelve
future boxes carrying a coordinate and a seat label and no name, against two-and-a-bit legible past
names, the leftmost sliced mid-word. And the three-column body repeatedly tabulates numbers it then
disclaims in 12px gutter text — at `late` it prints projected points **165 / 165 / 308** side by
side with "different scales" in the gutter, which is the owner's verbatim Duel objection ("it feels
like it's just going to lean in favor of the higher overall number by default") reproduced, not
answered. Its one great line — "Taking the dearest-to-wait-on position first is the cheaper order:
St. Brown → Taylor (by 9.9). That disagrees with the board's order." — belongs in v1.

### v4 `doors` — **concept is in serious trouble; the order line survives it.**
Sorting the primary layout by `positional_forfeit` makes the aid the spatial rank, and a right-
aligned 12px caption cannot undo spatial precedence. At `late` the consequence is concrete: the
second door the eye reaches is Tight End, holding T.J. Hockenson at **−53.5**, the worst value on
the board, because TE's wait cost (4.05) is second-highest. `ADJUDICATION.md` §1 permits forfeit to
inform and forbids it to decide. Reading order is a decision. Meanwhile the one pool view v4 has —
the "Every name" sheet — truncates the cliff clause on **7 of 7 rows at `late`** while 500px of the
sheet below is empty. The order line itself ("by cost of waiting: WR › TE › RB › QB | the board's
value order by position: WR › QB › RB › TE — the two orders disagree at this pick") is excellent and
should be lifted out before the doors are binned.

---

## 2 · Findings, most severe first

**F1 · v4, door sort, all three states — the layout is ranked by the aid.**
Doors are ordered by `positional_forfeit`, dearest-first. `early`: the board's first name (Taylor,
176.3) sits in door 2 while door 1 holds St. Brown. `late`: door 2 is Tight End / Hockenson −53.5,
the single worst candidate available, promoted above the RB and QB doors because TE's wait cost is
4.05. *Why it hurts:* a drafter with 30 seconds reads left to right and stops. He will read the two
leftmost doors and never reach the third-best-but-second-worst distinction the caption is making.
*What counts as fixed:* sort the doors by something that is allowed to rank (value by position, or
lineup order), and express the wait-cost ordering as the order line already does — as a stated
sequence, not as geometry. The order line survives intact under that change.

**F2 · v1, board strip, `late` — "THE BOARD · 7 NAMES" renders five.**
Measured: rows 6 (Jordan Mason, −43.7) and 7 (T.J. Hockenson, −53.5) have `top: 889px` and `923px`
in a 900px viewport. The two names below the fold are **the only running back and the only tight end
left on the board**. `RATIONALE.md` v1 `late` claims "the strip holds every name without scrolling".
That is false and I verified it. *Why it hurts:* with ten rostered and six bench slots, position
scarcity is the whole remaining question, and the two positions with exactly one name each are the
two the drafter cannot see. They do appear in "Also on the table" above the fold, so this is a
caption-versus-content contradiction rather than data loss — but a labelled count that does not
match what is drawn is how round 1 shipped twelve blank boxes. *Fixed:* the strip fits 7 rows, or
the caption says "5 of 7 shown".

**F3 · v4, "Every name" sheet, all states — every row truncates its only distinguishing clause.**
At `late`: "a sharp dro…", "no cliff behi…", "no cliff be…", "no cliff behind…", "a sharp drop …",
"a sharp dro…" — 7 of 7. At `early` and `mid` the same element (`.tk`) overflows on 11+ rows
(scrollWidth 204 vs clientWidth 134 on "RB1 · a sharp drop behind (37.8)"). Below the clipped rows
sit roughly 500 vertical pixels of empty sheet. *Why it hurts:* v4's pool is summoned, so this sheet
is the only place the drafter can scan the board, and the cliff word is the one thing differentiating
the rows. *Fixed:* the sheet is 520px wide and 880px tall with seven rows in it; wrap or widen.

**F4 · v3, comparison body, `late` and `early` — it builds the cross-position comparison and then
prints a disclaimer under it.**
`late`, PROJECTED POINTS row: `165 · 165 · 308`, gutter label "season · different scales". The
308 belongs to Trevor Lawrence, the *worst value* of the three (−36.4). DROP BEHIND HIM row: three
gaps side by side under "not comparable across positions". WAIT COST row: three numbers under "an
aid, never the order". *Why it hurts:* three times on one screen the surface renders a comparison in
the most comparable form available — adjacent cells in a shared row — and relies on 12px grey text
in a left gutter to prevent the reader making it. On a draft clock the cells are read and the gutter
is not. This is the mechanism by which "not taking the engine's #1 is wrong" gets re-implied through
a different number. *Fixed:* a row that cannot be compared across columns must not be laid out as a
row across columns — fold it into each column's own prose, or group the trio by position.

**F5 · v3, rail, all states — twelve coordinate boxes is twelve copies of the number twelve.**
Between YOU ARE UP and YOUR NEXT: `1.07 R7`, `1.08 R8`, `1.09 R9` … twelve boxes, no names, because
no names exist. To the left, two-and-a-half past boxes, the leftmost sliced mid-word ("…inson /
…r 3" at `early`, "…lenry / …r 3" at `late`). *Why it hurts:* the brief handed this one over for
free — "the wait ahead is a *count*" — and v1 and v4 both took it. v3 spent its horizontal budget on
placeholders and starved the named past that the rail exists for. *Fixed:* v1's rail, which is in
the same repository.

**F6 · shared layer (`costWord`), `early` — "the least here" names the wrong position.**
`M.POS_BY_COST` is built only from positions that have candidates. At `early` no QB appears in the
top 24, so TE (23.08) is labelled "the least here" — in v2's TE lane header, in v4's TE door, and in
v1's position table. QB's real wait cost at `early` is **1.82**, about one-thirteenth of TE's. The
same screen simultaneously says "no wait cost measured here" for QB. *Why it hurts:* the drafter's
honest read of "no wait cost measured" is *unknown*, and the honest read of "TE · the least here" is
*TE is the cheapest to defer*. Both are wrong and they are wrong in the same direction. *Fixed:*
suppress the superlative whenever a position is excluded for lack of a row, or say "the least of the
three the board has names at".

**F7 · all four variants, resident surfaces, `early` and `mid` — bare amber "Questionable".**
Four rows at `early` (Chase, Love, Jeanty, Hall), five at `mid`. Every one of them carries
`availability_basis: immaterial_designation` and `risk_basis: designation_not_priced`. The engine
looked at the designation and explicitly declined to charge it. The resident surfaces print the word
in amber with no qualifier; the explanation ("the designation is carried and not charged against his
value — this is not 'no risk'") lives only in the numbers sheet, one gesture away. *Why it hurts:*
Ja'Marr Chase is rank 3 at `early` and the only visual warning on the board sits on his row. A
drafter on a clock downgrades him for a reason the engine refused to price. This is `§16c`'s family —
a non-charge wearing a decision's clothes. *Fixed:* either the word carries its kind inline, or it
does not appear on the resident surface.

**F8 · v2 and v4, `late` — the sentence that makes the negative board legible is missing, and the
rationale says otherwise.**
`RATIONALE.md` cross-cutting finding 2: *"every variant adds one sentence — your starting slots are
full, so every name lands on your bench and the values run negative; read the gaps"*. Grepped: that
string exists in `v1_ledger.tpl.html` (`.allbench`) and `v3_trio.tpl.html` only. v2 and v4 have
nothing but a repeated "· bench" token. *Why it hurts:* v2's `late` fold shows `−34.6`, `−36.4`,
`−43.7`, `−53.5` with no stated cause anywhere on screen. v4 shows the same four numbers as door
headlines. A number that looks like an error with no sentence saying why is worse than no number.
*Fixed:* the sentence v1 already wrote, in all four. Better: put the measured cause on screen — see
F13.

**F9 · v2, `late` — the empty fold is ambiguous, and that, not the darkness, is what kills it.**
I measured it: content stops around y≈600 in a 900px viewport, so roughly the lower 40% is dark
(the author's self-reported "~70%" is harsher than reality, but the problem is not proportion).
Nothing anywhere on v2 states how many names are left. v1 says "THE BOARD · 7 NAMES"; v4's sheet
says "7 names"; v2 says nothing in any state. *Why it hurts:* four short columns over a large dark
area reads identically to a render that failed. The drafter cannot distinguish "the board is
exhausted" from "the lanes did not fill". *Fixed:* one count. With a count the dark fold becomes an
honest and even useful statement; without it, it is indistinguishable from a bug.

**F10 · v3 and v4, within-position comparison — the new instrument prints the same sentence in
every column.**
v4 `mid`, WR door open: "starts at WR2 beside London" appears in all three cards verbatim. v3
`late`: "bench — your starting slots are full" in all three columns, and "9.4 at WR · the most here"
in two. v3 `early`: "starts at WR1 — you hold no receiver" twice and "48.1 at WR · the most here"
twice. *Why it hurts:* `ADJUDICATION.md` §7 found differentiation collapses inside a position; the
brief then identified within-position comparison as the genuinely new thing this round. Both v3 and
v4 spend their new real estate on it and reproduce the collapse in a layout that puts the duplicates
side by side where they cannot be missed. *Fixed:* a row that is identical across all columns is not
a comparison row — suppress it, as v2's table already does for most rows and v4's `.tk` does not.

**F11 · v3, default trio, all states — the default is ranks 1, 2, 3.**
`early` Taylor / St. Brown / Chase; `mid` McMillan / Judkins / Allen; `late` Vele / Concepcion /
Lawrence. At `early` and `late` two of the three share a position, and the surface's own copy then
says the wait cost "cannot separate them". *Why it hurts:* the owner asked for *other valid options*,
which across positions means the best RB, the best WR, the best TE. v3's untouched default presents
the engine's top three — the closest thing in the set to "rank 1 and its two runners-up" — and burns
a third of a three-wide instrument on a duplicate position. *Fixed:* default the trio to one name
per position.

**F12 · v3, "by position", `mid` — summoning the position layer pushes the board's first name off
the bottom.**
Groups render in lineup order (QB, RB, WR), so seven quarterbacks and six running backs precede the
WR group, and McMillan — rank 1, 52.5 — sits at y≈885 clipped by the fold. *Fixed:* order the groups
by something the drafter is looking for, or pin the board's first name.

**F13 · all four, `late` — the one measured number that explains the negativity is hidden.**
`displacement_adj` is −33.70 for Vele, −44.05 at worst, `displacement_basis: measured` on all seven
rows, and it is the term that takes Vele from `−7.99` of general value to `−34.61` to *your* roster.
It is on the payload. All four variants put it in the numbers sheet behind a gesture and explain the
negativity in prose instead (v1, v3) or not at all (v2, v4). *Why it hurts:* the brief's live
question is whether the level is noise and the gap is the signal. The level is not noise — it is one
large measured term about *this roster*, and showing it would convert "−34.6, alarming" into "−7.99
of player, −33.7 because your slots are full", which is the honest decomposition. *Fixed:* surface
it at `late` where it dominates.

**F14 · v1, numbers sheet — a measured zero rendered as an absence, with the caption denying it.**
At `late`, `denial_value: 0.0` with `denial_basis: "measured"` on all seven rows. The sheet prints
`Kept from a rival —` tagged MEASURED, with the blurb "a 0 is a measurement". It says a zero is a
measurement and then refuses to print the zero. *Fixed:* print `0.0`. This field's contract is the
opposite of `depth_exposure`'s, and the code applies the same rule to both.

**F15 · v1, ledger card, `mid` and `late` — the subject's own cliff never appears.**
Row 1 of the board strip reads "in the ledger" where every other row carries its cliff clause, and
the "Why" block uses the *runner-up's* cliff. At `late` that means Devaughn Vele — the board's first
name, `forces: ["cliff","tie"]`, `cliff.tier: HIGH`, `gap 4.18` — is the one candidate on screen
whose cliff is never stated. *Fixed:* v2 and v4 already have the correct sentence for this exact
row: "a sharp drop behind him 4.2 to a player below this board".

**F16 · all four, hypothesis/numbers overlays — "priced" on a user surface.**
`_src/shared.js:232` ships "the designation is carried and **not priced** against his value" in the
numbers sheet, and v2's hypothesis panel says alternatives "are **priced**, not ranked as errors".
The shared `KIND` map one line above already uses "not charged". Named friction, rejected once,
still present. *Fixed:* use "not charged" consistently; rewrite the hypothesis string.

**F17 · v2 and v3, truncation the probe did not catch.**
`v2/mid`: the third comparison column's header reads "Jameson …" (`.nm`, 142px of content in 91px)
— on a three-way comparison, the name is the key. Same state, RB lane: "TreVeyon Henderson NE · 2…"
cuts a projected-points value mid-digit. `v3/mid`: "Questi…". `v2/early` and `v2/mid`: the bottom
lane row is sliced by the viewport edge (Saquon Barkley at `early`, Jayden Reed at `mid`) with no
scroll affordance drawn. *Why it hurts:* the `RATIONALE.md` verification section claims "no
clipping" from `_shoot.py`. It checked regions, not text overflow. This is round 1's lesson, one
layer down.

**F18 · v3, pool strip, `early`/`mid` — 72 A/B/C buttons.**
Three identical 22px buttons on each of 24 rows, of which three are ever lit. *Why it hurts:*
"information overload is jarring" was the round-1 rejection and this is its visual form — a repeated
control grid competing with the data it sits beside.

**F19 · cosmetic, v2 and v4.** v2 `late`: the RB lane header is the bare string "RB" while QB's
reads "Prescott · next → bench" — looks unfinished. v2 `late`/`early`: a "copy name / numbers"
button pair repeats in every lane, up to four visible at once. v4 all states: ~130px of blank between
each door's lead card and its "THEN AT…" rule. v4 `late`: "Devaughn / Vele" wraps to two lines in
door 1 while the other three doors' names do not.

---

## 3 · The one idea worth keeping

**v1's summoned position table** (`which position?`, seen at `mid` in `v1_posgrid.png`):

```
          YOUR SLOT              BEST LEFT · VALUE       COST OF WAITING ON IT
QB    QB open — none held        Allen 47.9              1.7 by #54 · the least here
RB    RB2 open                   Judkins 49.7            7.8 by #54 · the most here
WR    WR2 open                   McMillan 52.5           5.5 by #54
TE    FLEX only                  none in the board's     not measured
                                 top 24
```

Four rows, fixed in lineup order, answering "which position?" with the drafter's own slot, the best
name there, and what deferring it costs — and saying `not measured` for the position the board has
no name at rather than inventing a zero or omitting the row. It is the brief's whole governing
sentence (who · why · what else · at what cost) in four lines, it dissolves the position-ordering
instability by holding the slots still and letting the contents move, it costs nothing when nobody
asks for it, and it is the only place in either variant set where the empty position is rendered as
a *state* rather than as a gap in the layout.

Runner-up, and it should be lifted too: **v4's order line** — two orderings printed as explicit
sequences with "the two orders disagree at this pick · the board ranks on value; the doors are
sorted by an aid beside it". That is the visible reconciliation `ADJUDICATION.md` §1 demanded. But
the table beats it, because the table states the second ordering without making it the layout, which
is precisely where v4 goes wrong (F1).

Honourable mention, one line: **"a sharp drop behind him 4.2 to a player below this board"** (v2,
v4, `late`). Vele's `bpa` is −7.99 and Concepcion's is −7.93, so the display order inverts the
ordering the cliff was measured in and the real neighbour is off the candidate list entirely. Three
of the four variants get this exactly right and say so in plain language. That is `ADJUDICATION.md`
§5 fully discharged.

---

## 4 · What the set as a whole gets wrong

**Everything that keeps the surface legal is set in the dimmest, smallest, most peripheral type on
the screen.** "Value and wait cost point different ways. The board ranks on value; the wait cost is
an aid beside it, not a second ranking" (v1, grey, below two bright lines). "an aid, never the
order" / "not comparable across positions" / "season · different scales" (v3, 12px, left gutter).
"the two orders disagree at this pick" (v4, 12px, right-aligned, 60px above the doors). Meanwhile
the bright amber text says "wait cost favours him first by 9.9" and the spatial layout says WR
first. **The set asserts in bright type and retracts in grey.** On a 30-second clock only the
assertion is read, and the assertion is the thing the owner's ruling forbids. This is one design
problem, not four, and it is the most important thing in this review: the reconciliation has to be
*structural* — in ordering, grouping, and what gets drawn adjacent to what — or it is not a
reconciliation.

**The within-position comparison is the round's stated new thing and it is the weakest part of every
variant that has one.** The measurement says that across positions the honest unit is the position,
and within a position the comparison must rest on value, cliff, horizon, designation and depth. Both
v3 and v4 built a three-column table for exactly that and then filled two to four of its rows with
byte-identical strings. v2 built the only table that suppresses the identical rows — and then
captioned the n=1 case "THE ONE AT TE, SIDE BY SIDE". Nobody in this set has made two same-position
players look different yet.

**`late` is handled as a copy problem, not a data problem.** Two variants write a sentence about
full starting slots; two write nothing; none shows `displacement_adj`, which is measured, on the
payload, between −33.7 and −44.1, and is the entire reason the board reads negative. The brief asked
whether the variants make the negative board legible, alarming or meaningless. The honest answer:
v1 and v3 make it legible in words while the biggest glyph on the screen still contradicts them;
v2 and v4 make it alarming.

**Nobody states the size of what is left except v1 and v4's hidden sheet.** At `late` the pool is 7
and that fact changes behaviour more than any value on screen. v2 never says it in any state.

**The automated verification repeated round 1's failure at one level of detail down.** `_shoot.py`
checked font size, page scroll, clipped *regions* and rail markers — all of which pass — and missed
text overflow on four surfaces, a labelled count that does not match what is drawn (F2), and a
seven-row sheet that truncates all seven rows (F3). Three of those are visible in the PNGs the
author says he read. The lesson from round 1 was not "add assertions"; it was "assertions find what
they were told to find".

**Two rationale claims do not survive checking**, and both are about `late`, which is where the brief
said to look hardest: "every variant adds one sentence" about the bench (true for two of four), and
v1's "the strip holds every name without scrolling" (it holds five of seven, and loses the only RB
and the only TE).

### On v2's missing rail, since I was asked to rule

**The dark fold does not kill the concept; the missing count does.** Removing the rail is the single
highest-value cut anyone has made in two rounds — "You pick again at 12.07 (#139), after 12 picks —
rosters 7, 8, 9, 10, 11, 12 each pick twice" is one line of 12px text that carries strictly more
than twelve boxes and does not fight the fold. Keep it.

Two honest costs, and only one of them is acceptable. The acceptable one is the empty fold *provided
the board's size is stated* — a short board honestly drawn short is a true statement, and at `late`
it is the most important true statement on the screen. The unacceptable one is that **§1 is RULED
and the sentence does not replace what the rail was ruled in for**: "rail boxes carry the drafting
user's name, so who is up is never ambiguous", and "your own picks glow". v2 says which rosters pick
during the wait but never who is on the clock, and shows none of the drafter's own picks in draft
order. The owner invited this exploration ("Not having the rail may be worth exploring too"), so this
is a tension to put in front of him, not a defect to score — but it should go to him as *"the
sentence replaces the span, and nothing yet replaces the named next-on-the-clock"*, not as "no rail,
no cost".
