# The draft room UI: where it stands, what is decided, and what Doors A needs

Written 2026-10-04, at the point where the owner named Doors A the build target. This is the
durable record of two design rounds, a polish pass, four adversarial reviews, two adjudications
and an engine investigation. Engine-side findings live in `FLEX_AND_POSITION_DOORS.md` and are
cross-referenced rather than restated (`#126`).

---

## 1. Status

| round | what happened | outcome |
|---|---|---|
| 1 | 6 variants, 2 Fable builders, 4 adversarial reviewers (2 Opus / 2 Sonnet) | headline failure: every variant rendered all inputs to the decision and **none performed the subtraction** |
| 2 | 8 synthesis variants (2 sets x 4), same review structure, adjudicated before feedback | subtraction performed by all 8; 12px floor; no fabricated ties |
| polish | owner cut 4, two Fables polished the rest | 4 survivors published |

**Owner verdict:** Doors A and Ledger A are the finalists. **Doors A is the build target** --
"genuinely intuitive", with the tank called "immaculate". Ledger A is retained because its
reasoning panel is the engine's actual intellectual product.

**Cut:** Trio A, Gold Wyrm Ledger, Gold Wyrm Trio ("no"), Gold Wyrm Doors ("ok. meh").

Published: Doors A `VGgNqGjCogxrCKmhZjo3YF` · Ledger A `DAcnmwrb71tCX9joojABxS` ·
Ledger A with rail `R5nZf8JBCDpzLHMyi2p5zB` · Lanes A `HsjCmNW3vGAjacYvbrboM3` ·
Four Cells `HVpaGjgL9i8UKoH6i12rfy`.

---

## 2. The governing constraint (owner, standing, overrides design taste)

> Emphasize clean dissemination of information over just having as much on the screen as you can
> fit. I dont need all the variables, i dont need every everything. clean who, why, and other
> valid options, at what cost. for any pick you make, there are going to be multiple valid
> options, which means that not taking the engine's #1 isn't inherently *wrong*

Plus: game-ish aesthetic, clean, polished, functional.

---

## 3. Binding rulings -- do not relitigate

- `DRAFT_ROOM_UI.md` **§1** (RULED: rail, name boxes, glow, re-centre, debate on the clock, no
  automatic paid API calls, must function with no API), **§14** (the pool gauge), **§16a**
  (ordering on `acting_now_value` measured at **-6.090%**; it is "a decision AID beside the rank,
  never as the rank's explanation").
- `ADJUDICATION_R1.md` and `round2/ADJUDICATION_R2.md` -- my rulings, binding, and they overrode
  reviewers in five places after checking against the engine.

The load-bearing few:

- **Forfeit informs, never decides.** Making it the spatial rank is that violation by geometry.
- **No fabricated ties.** `ambiguities` is `[]` in all three captured states. Every "tie" or
  "coin flip" on a round-2 surface was client-invented from a hand-picked `0.05` (`#56`). Render
  the **margin** instead -- Vele is 0.23 ahead of Concepcion on a scale spanning 18.9.
- **A measured value never renders as an absence** (`#187`). Two confirmed instances were
  repaired: `denial_value 0.0 / basis measured` on 7 of 7 `late` rows shown as an em-dash, and a
  `|x| >= 2` gate hiding `time_horizon_adj`.
- **Basis labels verbatim from the engine.** `no_surplus` begins "measured, but..." -- rendering
  it "not measured" states the opposite.
- `confidence` is `85.0` for every candidate in all three states. Identical numbers are a broken
  instrument until proven otherwise (`#245`). **Do not render it** until that is answered.

---

## 4. The round-2 headline: why the late board is negative

Found independently by both Opus reviewers, then verified. `displacement_adj` is `measured` in
all three states, `0.00` for all 24 candidates at early and mid, and at `late`:

```
Devaughn Vele    WR  tav  -34.61 = displacement -33.70 + rest -0.91   ( 97.4%)
Trevor Lawrence  QB  tav  -36.37 = displacement -36.37 + rest  0.00   (100.0%)
T.J. Hockenson   TE  tav  -53.46 = displacement -44.05 + rest -9.41   ( 82.4%)
```

Strip it and Vele is -0.91. **The one state where the screen looks broken has exactly one cause,
it is already on the payload, and it needs one sentence.** All four survivors now carry it.

This also answered the owner's flat-value-offset question: the late board does not need a
re-based scale, it needs the invisible term named. The offset was modelled and rejected -- it
does not fix late (leader still negative), swings k by 35.3, and creates an unnamed third
quantity.

---

## 5. The two-number relation (a reviewer finding, overturned)

Sonnet A reported that the value edge and the wait-cost edge are one quantity printed twice.
Verified across 6 of 6 cross-position pairs to +/-0.05:

```
positional_forfeit(best at P) == tav(P) - position_next_turn_value(P)   (exact, +/-0.03)
value_edge + order_edge       == the next-turn gap
```

**Dependent, not duplicated.** They look identical on RB/WR at early (+9.77 / +9.89) and nothing
alike on RB/TE (+33.57 / -15.09). The reviewer generalised from one pair.

What everyone missed: **the sum is the next-turn gap** -- how the two positions compare at my
next turn, a real quantity nothing names. So collapsing to one number destroys information.
`position_next_turn_value` is already on every candidate.

---

## 6. Door architecture -- decided in this session

**The model (owner's, and better than the capped-set version I proposed):** all 9 position doors
exist; **4-5 surface**, ordered by the board's recommendation; the window slides, so a kicker or
linebacker door rises late when the math supports it. Nothing is hidden by category -- only by
rank.

| rule | decision |
|---|---|
| when a position earns a door | **distinct demand OR distinct scarcity** ("named slot -> door" is too simple and breaks on TE) |
| TE with no TE slot | **always its own door** -- see `FLEX_AND_POSITION_DOORS.md` §1, where it is urgent rather than stylistic |
| IDP with only `IDP_FLEX` | **compound** into one door -- neither distinct demand nor meaningful drain |
| IDP with named DL/LB/DB slots | **split** into three doors -- named slots create distinct demand |
| a compound defensive door | **no tank.** One bar across three positions is the shared scale §14 calls load-bearing to avoid |
| tanks generally | **offense-only, permanently.** §14's supply reason holds even in heavy IDP: ~72 IDP starters out of several hundred rated bodies never visibly drains |
| doors that slide off | **no per-door affordance.** One count line on the main surface ("9 positions · showing 5"), and the all-list with a filter is the override surface |
| the drawer | must carry **per-position decision context** (defer cost, tank) when filtered, or disagreeing with the engine becomes blind -- a trapdoor, not an escape hatch |
| reorder churn | anchor **position identity** (colour, glyph) so the eye re-finds a door the window has moved |

**Derived, not chosen:** the grouping comes from the league's own `roster_positions`, never a
user toggle. A toggle would let the display disagree with the league about what the league is --
two sources of truth for one fact.

**Verified at full complexity.** The maximal roster
(`QB RB RB WR WR TE FLEX SUPER_FLEX DL LB DB K DEF IDP_FLEX`) resolves cleanly: all 9 positions
known, all 3 flex labels resolve, demand conserves to exactly 14.000 across 14 slots. And the
useful negative: **demand does not separate these positions** (spread 1.00-2.38, `TE 1.383`
beside `LB 1.333`), so **doors must rank on value order, not demand** -- which is what they
already do.

---

## 7. What Doors A still needs

Already done in the polish pass: order line cut (it was a constant dressed as a conditional with
no consequence, `#254`); card wording; clock/roster bar rebuilt; bottom doors content-sized;
rosters sheet rebuilt. Since: the held-back chips' ordinal (`indexOf` against an array of
door objects, so every chip read "0th door"); the `.rev` bar's overflow once a sixth format
button existed; and the hover boxes.

**The hover boxes (owner, this session).** Every one was a native `title=` -- the only surface
in the build that nothing designed. OS chrome on a dark page, ~1s to appear, auto-dismissed
after ~5s, no line breaks, nothing on keyboard focus, nothing on touch. The one that mattered
is the tank gauge's: **540 characters**, ten times the next longest, carrying three separate
facts (pool, what the gold line means, what the engine could price) as one unbroken paragraph
in a container that un-renders itself mid-read. That is the governing constraint in §2 --
clean dissemination of the why -- losing to a browser default.

Replaced by one delegated `[data-tip]` tooltip in `shared.css` / `shared.js`, so all four
variants get it: themed to the Obsidian tokens, hover **and** keyboard focus, first line as a
heading, remaining lines as paragraphs, edge-aware placement, Escape and scroll to dismiss.
Anything over 170 characters **pins on click**, so a long explanation can be read without
holding the pointer still -- short labels keep the plain hover so a click on a chip still does
what the click is for. Tip text is set as `textContent`, never `innerHTML`: some of these
strings interpolate vendor data, and a hover string must not be able to carry markup. The
newline convention is the only structure available under that rule, and it is enough.

Outstanding:

| # | item | why |
|---|---|---|
| a | **9-door model with the sliding window** | §6; cannot be built or verified without the fixture |
| b | **Count line on the main surface** | a window that does not say it is a window is hiding things -- same defect as the no-rail variant never stating pool size |
| c | **Drawer carries per-position context when filtered** | otherwise the override surface punishes disagreement |
| d | **Render `slot_share_basis`** | `FLEX_AND_POSITION_DOORS.md` §3 -- an assumed share must never pass for a measured one, and every board today is assumed |
| e | **Replace `FLEXIBLE = ["RB","WR","TE"]`** with engine-derived eligibility | wrong in superflex (QB is flex-eligible), wrong for `IDP_FLEX`; `#126` |
| f | **Position identity anchoring** | reorder churn versus spatial memory |
| g | *(optional, unruled)* Ledger A's reasoning panel as Doors A's depth layer | both occupy the same slot in the information architecture; composition rather than compromise |

---

## 8. Engine findings

See **`FLEX_AND_POSITION_DOORS.md`** -- the flex split, TE's understated demand in slotless
leagues (assumed 1.0 against an optimal 1.5, with the shipped board drafting **zero tight ends in
3 of 3 seats**), `SUPER_FLEX_QB_SHARE` understating QB at 1.850 against a measured 2.000 in the
owner's own format, the `slot_share_basis` contract, and a docstring claiming coverage the seam
denies (`#133`).

---

## 9. The fixture, which gates everything in §7

Six formats x three states (early / mid / late), same payload shape as `states.json`:

| # | format | roster_positions |
|---|---|---|
| 1 | control | `QB RB RB WR WR TE FLEX FLEX` |
| 2 | superflex | `QB RB RB WR WR TE FLEX SUPER_FLEX` |
| 3 | no TE slot | `QB RB RB WR WR FLEX FLEX FLEX` |
| 4 | heavy IDP | `QB RB RB WR WR TE FLEX DL DL LB LB DB DB` |
| 5 | maximal | `QB RB RB WR WR TE FLEX SUPER_FLEX DL LB DB K DEF IDP_FLEX` |
| 6 | light IDP | `QB RB RB WR WR TE FLEX IDP_FLEX` |

Format 6 is the one case the other five cannot reach: a single `IDP_FLEX` slot with DL, LB and
DB all live on the board, which is the only shape that exercises the compound-door rule in
S6. **Its draft sequence is SIMULATED, not recorded.** Formats 1-5 replay a recorded VDS
`sharp_auto` arm; no such arm exists for this roster, so `sim_light_idp.py` drafted one with
the engine against itself and `capture_fixture.py` merges it only where no recorded arm exists
(`setdefault`, never overriding one). A simulated sequence is evidence about the engine's own
behaviour, not about a draft that happened -- weigh anything read off format 6 accordingly.

Capture discipline is the `engine-measurement` skill's, without exception: run from the repo
root, `build_players_db_from_capture()` **not** `build_players_db`, season projections with
`SLEEPER_BASIS_SEASON_SUM`, `set_league_format(db.league_format_hint(league))` per format, pick
records carrying `{pick_no, round, roster_id, player_id}` because `mode="auto"` reads `round`,
and the turn chosen on the gap **ahead**.

**Verify each board reports the positions it is supposed to before any of it reaches a Fable.**
Three rounds of this project have now failed the same way -- an agent passing its own checks
while measuring the wrong thing -- and every time the repair was a better fixture, not a better
reviewer.

---

## 9b. What the fixture does and does not establish

Two readings to refuse, both raised in review and both easy to drift into later.

**"The sliding window is validated" -- no.** It is exercised against **six shapes, five of them observed** (see the provenance note in S9: format 6's sequence is simulated).
`HEAVY_IDP` proves the window can rank a genuinely crowded surface (7 positions on one board) and
`12T_ppr_K_DEF` proves K/DEF can arrive late rather than squat permanently. Neither tests the
**compound-vs-split rule**, because that rule turns on `IDP_FLEX`, and `LIGHT_IDP` has no recorded
sequence in the VDS corpus. **The one architectural decision invented in this session is the one
with no board to check it against.** It needs a simulated draft, not a replay.

**The demand figures are not ground truth.** `fixture.json` records `QB 1.850` in superflex and
`TE 1.667` with a TE slot. Those are **what the current engine produces**, and therefore what
Doors A must render -- not what is correct. `FLEX_AND_POSITION_DOORS.md` measures both as
questionable: `SUPER_FLEX_QB_SHARE` is hand-set at 0.85 against a measurement returning 1.00, and
the even TE split is false in every format tried. A reader six months from now must not mistake a
captured value for a verified one. That is exactly what `slot_share_basis` is in the payload for.

The separation the fixture buys, stated once:

| layer | claim |
|---|---|
| engine | here is what I believe |
| fixture | here is what the engine actually produced across real board states |
| Doors A | here is how we choose to manifest it |
| human reviewers | can a person understand and use that manifestation |

The question the next phase answers is not "which mockup looks best" but **which information
contract stays intuitive when the league gets weird.**

## 10. Open, not decided

- **The rail.** §1 rules it; the owner twice floated dropping it and both builds are published
  (3 more board rows without it at mid: 9 of 24 against 6). **His call, unmade.**
- **Ledger A's reasoning panel as Doors A's depth layer** -- my proposal, unruled.
- **`#50`** blocks the flex-share repair. The measurement exists, failed four of nine
  pre-registered gates, and stays an instrument. Until then the UI's obligation is to **label the
  basis**, not to fix the number.
- **Rail-less Ledger A** reports `MISSING .row[data-id='12526']` in its own interaction pass while
  its hand-back claimed error-free. Small, in a secondary variant.
- `confidence` uniform at 85.0 -- an engine question, unraised as a register item.
