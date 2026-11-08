# standing — what if nothing scrolls?

**Question.** The base runs 1283px tall on a 900px desktop and 2746px on a 664px phone. What if the
whole answer stands on one screen at 1280×900 *and* 390×664, and every further layer is a popover?

**Answer, measured.** It fits, in both states, at both viewports, with no horizontal overflow. The
margins in the loud state are thin — 11px on desktop, 7px on the phone — and that is the finding:
the front page as the owner ruled it (claim band, what was checked, one freshness stamp) fits one
screen with almost nothing to spare, which means the ruling was drawn exactly at the edge of what a
screen holds. Anything added to the front would scroll.

```
build     /usr/bin/python3.13 ui_explore/round6/standing/build_standing.py
measure   /usr/bin/python3.13 ui_explore/round6/standing/measure_standing.py
```
(`python3` on PATH is 3.11 and has neither numpy nor Playwright; `front_claims` imports
`lineup_optimizer` which imports numpy, so the base builder has the same requirement.)

## Measured gates

| | loud 1280×900 | loud 390×664 | quiet 1280×900 | quiet 390×664 |
|---|---|---|---|---|
| natural page height | 889 | 657 | 746 | 650 |
| slack under the fold | **11px** | **7px** | 154px | 14px |
| vertical scroll | none | none | none | none |
| scrollWidth / clientWidth | 1280 / 1280 | 390 / 390 | 1280 / 1280 | 390 / 390 |
| min computed font size | 12.0px (`.constructed` tag) | 12.0px | 12.0px | 12.0px |
| min tap target | 44px | 44px | 44px | 44px |
| console errors | 0 | 0 | 0 | 0 |

"Natural height" is the body's rendered height with `min-height:100vh` and the `1fr` band row
switched off, so the slack is the real distance to overflow and not a stretched grid reporting
itself as full. The first version of this probe read `documentElement.scrollHeight`, which
`html{height:100%}` pins to the viewport, and reported 0px slack on every page — a number that
looked like a perfect fit and meant nothing. The script now says which it measured.

**Non-text contrast**, every mark, sampled from the rendered colour against the ground it sits on
(the build also asserts each token against `bg`, `surface` and `surface-2` and fails under 3:1):

| mark | token / hex | ratio |
|---|---|---|
| clean glyph, quiet tile rail | `status-ok` | 11.64 |
| raised glyph | `gold-b` | 12.53 |
| bye tile rail, mid bar | `gold` | 7.40 |
| recede bar | `dim` | 4.82 on bg, 4.51 on surface |
| DEF rail / chip | `#ef7fc0` | 7.97 |
| TE rail / chip | `#ff6042` | 6.59 |
| RB chip | `#0ca89c` | 6.68 |
| lowest position pill (QB) on surface | `#2a81fc` | 4.97 |
| absent glyph | `muted` | 7.38 |

Body text tokens asserted ≥ 4.5:1 on all three grounds: `ink` 15.45, `muted` 7.38, `gold` 6.92,
`gold-b` 11.72, `pure` 14.76 (worst case, on `surface`). The hero headline is gradient text and is
asserted stop by stop at the large-text floor: `#ba9561` 6.66, `#f9de99` 14.04, `#fff4ce` 16.81.
The logo's darkest stop `#755024` measures **2.58 on surface** and is therefore not in the
headline gradient; the wordmark keeps it as brand chrome, same as the base and deck.

Type floor: declared in `rem` throughout, `em` refused by the build, 0.75rem minimum. Computed
scale on desktop: 12 · 12.5 · 12.8 · 13.4 · 14.7 · 16.3 · 20.8 · 24.8 · 44 · 67 · 80 · 128px. That is
a 10.7:1 range against the base's 1.97:1 first pass, and the jumps are real: eyebrow → headline →
hero → figure → lead figure.

## What moved, and the argument for each move

The constraint was used as the brief asked: when something did not fit, the question was whether
it belonged on the front, and the owner's rulings had mostly already answered.

**The bye ledger left the front.** It was the owner's favourite panel and the base drew it twice
(as a panel and again in the popover). It is the *second layer of one claim* — eighteen rows
elaborating "Week 6 costs 95" — and the ruling says expansions are popovers. It is now the bye
tile's popover only, content unchanged: weeks, value lost, severity bar, who is away, season total,
concentration, unknown byes. Weeks behind the current week are tagged `behind` and dimmed when a
week is known. On the phone the popover scrolls inside itself; the page does not.

**"Cleared — can wait" became the checks ledger inside the hero.** What was checked is a front
item by ruling, and three rows is what it is: name in Cinzel, a state glyph (clean / raised /
absent, each a different shape-and-colour, with the word beside it so colour never carries the
state alone), and one button to a popover that gives each check its basis line. In the loud state
the raised rows say "raised — below", pointing at the tiles.

**The statbox was dissolved into the lead tile.** The base repeated the lead figure beside the
headline. Here ladder order *is* type scale: the lead claim's figure is set at 8rem (128px), the
others at 4.2rem, quiet tiles at 5rem. The rung that outranks is the one you read first, and the
hero needs no second copy of the number.

**The freshness stamp is on the front.** The base's docstring names it as the third front item
and the base never rendered it. It is rendered here as a *date* — `player database captured
2026-09-07` — read by regex out of `_provenance.players_db` (the fixture stores that field as a
truncated repr). It is deliberately not an age or a grade: `recency_grade` grades an average age
in days, an age needs today's clock, and a built file has none. The popover says so, and lists
source, season, players in capture and in pool. A fixture with no readable date renders the dash
with its reason (exercised with a synthetic fixture, below).

**The whoami moved from the top bar to the hero's eyebrow row.** In the top bar it overflowed the
viewport at 1280px (1411px scrollWidth in the first render) because `Team 1 · CONSTRUCTED · no
league name — · no week —` plus five rooms plus a crest is wider than 1232px. The hero's left
column has 900px. Two grammar points applied there: the absences are *labelled* (`no week —`, not
a bare dash), and `CONSTRUCTED` is stamped **once** for the group of constructed values rather
than once per value — in the quiet fixture both the team label and week 15 are constructed, and
two identical tags on one short line is the "absence identical on every row" noise the brief
forbids. The one tag's hover carries both reasons.

**The phone folds the rooms into a popover** behind a 44px `Rooms` button, with the Prytaneum
listed there as the dock. The foot's dock button is hidden on the phone; this is the one place the
"persistent dock" is a tap further away than the ruling might want, and it is recorded here as a
cost rather than hidden.

## The quiet state, which is the primary design

With no claim standing, the three checks become the band, each with a *real figure*:

| tile | figure | what it is |
|---|---|---|
| Holes · clean | **10** starting slots | `league.starting_slots`, a field. Headline: every slot has a body. Popover: the slot shape from `league.roster_positions`, each slot in its position colour, bench greyed |
| Byes · clean | **7** bye weeks | `len(bye_profile.weeks)`, a count of fixture rows. Headline: all behind week 15. Popover: the same week ledger, every row tagged `behind` |
| Depth · clean | **16** rostered | `len(roster)`, a count of fixture rows. Headline: no room rates Weak. Popover: the roster by room with each man's priced value; the note says the full label table is not in this capture, so none is drawn |

Three zeros (`0 holes · 0 weeks ahead · 0 thin rooms`) were considered and rejected: they are
measured zeros, not absences, but a band of three large zeros reads as a broken template, which is
the rejection the brief records. Each figure above is a field or a count, never a computation, and
each carries its provenance line.

## What was kept from the base, and why

- `front_claims.compose` as the only source of claims, checks and their order. The builder adds
  no judgment; it arranges.
- `claim_parts` / `verdict_prose` structure, the ladder-ordered tiles, the currency stamp with the
  `#341` wording, the absence helper, the severity ramp (`dim` → `gold` → `gold-b`) and its
  build-time assertion, the type-floor assertion, the position-pill colouring via
  `design_system.position_pill_color`, the wyrm crest, the `.door` nav, the popover styling.
- The verdict prose is the base's; a second, shorter lede is rendered for the phone (same figures,
  fewer qualifying words) and CSS shows one or the other.
- Expansion rule 2 holds: every popover is something the engine computed separately or a filter
  on fixture rows. Nothing opens on a figure the page would have to compute.

## The hard law — where every figure comes from

`95` worst_week_loss · `237` total_loss · `6` worst_week · `1` starters_out · `6 measured weeks`
len(weeks) · `1`/`2 rostered` thin count · `1 of 2 priced` valued_count/count · `Weak` depth_label
· `40%` concentration · `0` unknown_byes · chips = `roster[]` filtered by `bye` or `position` ·
`10` starting_slots · `7` len(weeks) · `16` len(roster) · `2026-09-07` captured_at · `3` checks
= `checks_summary.ran`. The bye scope says "the largest of 6 measured weeks" when no current week
is on file and "the largest of the N weeks still ahead" only when `ahead_only` is set, so the
futurity claim is never borrowed. No rank, no grade, no bar for a label, nothing about record.

## What I believe is wrong with it

1. **The loud margins are 7px and 11px.** A different fallback font, a browser with a visible
   toolbar inside a 664px viewport, or one more thin position in the band would make the page
   scroll. The design holds the fold; it does not hold it comfortably. The quiet state, which is
   most weeks, has 154px on desktop and 14px on the phone.
2. **The phone whoami wraps to two lines** (`Team 1 CONSTRUCTED no week —` / `no league name —`).
   It costs 20px of the thinnest budget on the page. I did not shorten the absence labels to buy
   that back because a shorter label is a less honest one.
3. **The dock is a tap further away on the phone** (inside Rooms). The ruling calls it a
   persistent dock; this is a compromise, not an interpretation.
4. **"In the room" chips on thin tiles duplicate the popover's content** on desktop. They are
   there because a 488px-tall tile with an eyebrow and a figure reads as a void without them, and
   they are the roster's own vocabulary in position colour. The redundancy is deliberate and small.
5. **The quiet depth popover shows the roster, not the depth table.** The fixture carries only
   `thin_positions`; the per-position label table is not in it. The popover says so. A richer
   fixture would make that layer real; this one cannot.
6. **`dim` measures 4.51:1 on `surface`** — above the floor by 0.01. It is used only for the
   recede bar (non-text, 3:1 floor) and never for text on this page; all small text is `muted`.
7. **Two `<h1>`s** (wordmark and headline), inherited from the base.
8. **The hole and absent paths are exercised only by a synthetic fixture**, not a committed one:
   holes `["K","DEF"]`, `thin_positions: None`, `bye_profile.basis: "partial"`, unreadable
   `players_db`, `current_week: 7`. It built, fit both viewports (773 / 531 natural), rendered
   `≥56` on the lead figure, two absent glyphs, a dashed stamp, and a hole tile with two pills.
   Not committed, so not a gate. It also caught a real defect on its first render: the lead tile
   said "the largest of the **6** weeks still ahead" when five were — `claim_parts` was counting
   the fixture's full profile instead of the reduced profile `compose` returns for exactly this
   purpose. Fixed by passing `band["bye_profile"]` through; the two committed pages are
   unaffected (the loud fixture has no current week, so its profile is not reduced), which is why
   the committed fixtures alone would never have shown it.

## Screenshots looked at

`shots/standing_desk.png`, `shots/standing_phone.png`, `shots/standing_quiet_desk.png`,
`shots/standing_quiet_phone.png` (the four folds); `shots/standing_desk_pop_exp0.png` and
`shots/standing_phone_pop_exp0.png` (the bye ledger — this is where a class collision with the
header's `.top` rule was caught turning a paragraph into three flex columns); `shots/
standing_desk_pop_checks.png`, `shots/standing_desk_pop_fresh.png`, `shots/
standing_quiet_desk_pop_chk2.png`, `shots/standing_phone_pop_roomsp.png`. The measurement script
regenerates every popover shot on each run; the folder is pruned to these ten.
