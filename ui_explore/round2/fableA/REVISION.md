# Fable A — round 2 revision (after ADJUDICATION_R2)

Read in this order: `ADJUDICATION_R2.md` (binding, overrides the reviews), `reviews/opus_A.md`,
`reviews/sonnet_A.md`. All four variants revised; none discarded. Rebuilt and re-rendered in all
three states; every PNG in `_shots/` was looked at after the last build.

## Applied to all four (shared layer)

| ruling | what was done |
|---|---|
| **R2 §1 — the `late` negativity has one measured cause** | `displacement_adj` (basis `measured`) is named in bright amber type beside the number it explains, on every surface where a value headline appears: v1 a bar under the ledger head; v2 under each lane lead's value and inside the comparison table; v3 inside the board's-order cells; v4 under each door's value and on the cards. Wording: *"−33.7 of this is the displacement of a starting slot you have already filled — measured against your own starters. The player himself: −0.9."* Lawrence prints *himself 0.0*. The round-1 "read the gaps, not the levels" sentence is gone — the level is now explained, not argued with. |
| **R2 §2 — "double counting" overturned; name the third quantity** | Every cross-position cost now prints three real numbers, none collapsed: **now** (value gap, the board's order), **next turn** (`position_next_turn_value` of his position minus the subject's position — what each leaves at your next turn), and **plan** (both picks together). Verified on the payload: plan edge == forfeit edge, and now + next turn == plan. The "Why" sentence spells it out: *"Wait on RB and the best running back left at your next turn is worth 42.0; wait on WR and the best receiver left is worth 47.0. Both picks together: Judkins now is the better two-pick plan by 2.2."* The second edge is no longer labelled "order"; nothing is labelled "wait cost favours". |
| **R2 §3 — no tie is in the payload** | Every `0.05` constant and every "level / coin flip / dead even" string deleted from `shared.js`. The margin is rendered as a margin: *"Vele is 0.2 ahead of Concepcion in value to your roster now."* v2's "board's first" badge and v4's gold door remain, because "first on the board" is a fact of the board's order; nothing calls it right. |
| **R2 §4 — superlative scope** | `costWord` now reads *"most of 3 measured"* / *"least of 3 measured"* (the count is the number of positions the board has names at), so TE at `early` is "least of 3 measured", never "the least here". Arithmetic unchanged. |
| **R2 §5 — measured values never render as absences** | `denial_value 0.0 / measured` prints `0.0` with the engine's basis label and *"a zero is a measurement"* (verified in all four `late` numbers sheets). Horizon: the only remaining visibility rule anywhere is *identical across the names being compared → row not shown*; when a horizon row is shown, a measured `±0.0` prints (v3 `late` shows `±0.0 · ±0.0 · −10.0`). Audit of client cut-points: the former `Math.abs(x) < 0.05` tie tests (3 sites) and v4's `f1(h) !== "0.0"` horizon gate are gone; what remains is `cliffNext`'s 0.02 reproduction tolerance (a check that the payload reproduces the engine's gap, not a visibility threshold). |
| **R2 §6 — basis labels verbatim** | `DEPTH_LABEL`, `DISP_LABEL`, `DENIAL_LABEL` carry the engine's own strings; `no_surplus` now reads *"measured, but it is a starter's whole value rather than a backup's job -- some starter here has no cover, so this is not a depth price and is not charged as one"* under a **not charged** kind chip, never "not measured". |
| **R2 §7 — names** | Collision key is the family name, the particle is kept: `A. St. Brown`, `A. Brown`, `C. Brown` on the `early` board. |
| **R2 §7 — "last receiver this board rates"** | Scoped to the measured order everywhere: *"a sharp drop (4.2, to a player off this board (measured order))"*. |
| **R2 §7 — clipping, occlusion, scrollers** | `_shoot.py` now asserts on text overflow (any text box wider or taller than its clip), occlusion (centre of a text element resolving to an unrelated element), **cut-off by the viewport** (a text box past the fold with no scroller above it — the check that caught v4's cards), scrollers without a visible affordance, and captioned counts that exceed drawn + "more". Every list that overflows renders *"↓ scroll · N more"* (`markScrollers`), so a short list over a dark fold cannot be mistaken for a failed render and a count never silently differs from what is drawn. v4's "Every name" sheet rows are two-line, so the cliff clause never truncates. |
| **R2 §8 — bright asserts, grey retracts** | The grey retraction lines ("the board ranks on value; the wait cost is an aid…") are deleted. What replaces them is structural: the board's order is the only thing that orders anything (v4's doors included), and the next-turn quantity is printed as a value with a plain label, not as a rival ranking. The one legend that survives (now / next turn / plan) is body-size muted text and defines terms; it retracts nothing. |
| "priced" | Gone from every string including the numbers sheet and the hypothesis panels; rendered-text scan of all 12 states finds none. "Questionable" on resident surfaces now reads *Questionable · not charged* (Opus A F7). |

## Per variant

### v1 `v1_ledger.html`
**Changed.** Displacement bar under the ledger head at `late`. "Why" opens with the subject's own
drop (Opus F15 / Sonnet F4) and then the value margin and the two-pick plan with both next-turn
values named. Alternatives carry now · next turn · plan as inline cells, capped at four so the
only RB and the only TE on the `late` board are both on the table above the fold (Opus F2). The
board strip is captioned honestly: at `late` it draws 4 of 7 and says *"↓ scroll · 2 more (one cut
off)"*; the three names below the fold are the three already costed in "Also on the table". Rival
ticks are no longer coloured (Sonnet F11: a ≤2.8% rival drawn as a warning). The summoned position
table is kept as it was, with the scope wording fixed and the cost definition stated in full.
**Refused.** Sonnet F1's "one number per alternative": overturned by R2 §2 — the three numbers are
three quantities and the sum is named. Sonnet §4 "the layout is a podium": the subject defaults to
the board's first name because the board's order is the one order allowed to rank; the surface
says "first on the board", costs every alternative, and says taking one is a choice. I did not
move the default off rank 1 — an unranked default would be a hidden ranking of my own.

### v2 `v2_lanes.html`
**Changed.** The clock line now names the drafter: *On the clock: you (Roster 6) · next up: Roster
5 · last taken: J. Warren by Roster 7* (R2 §10's second defect), and the lineup line states the
pool size: *the board: 24 names* (the first). The `late` displacement sentence is under every lane
lead and inside the side-by-side table. Empty lanes narrow to 0.55fr (they hold one sentence).
The n = 1 lane no longer says "side by side"; it says *Only one tight end on this board*. Lane rows
wrap instead of truncating; every lane list carries the scroll affordance. The side-by-side table
suppresses identical rows (it already did) and prints measured zeros when a row is shown.
**Refused.** "Throw the lanes away" (Opus) — a layout opinion; the owner called Lanes clean and
the within-position table is the only resident one in the set, so the lanes stay as the pool.
The rail: kept absent as the explicit §1 change request (see RATIONALE).

### v3 `v3_trio.html`
**Changed.** Default trio is one name per position (Opus F11): Taylor / St. Brown / Bowers at
`early`, McMillan / Judkins / Allen at `mid`, Vele / Lawrence / Mason at `late`. The 72 A/B/C
buttons are gone: click a name to fill slot C (or the first empty slot), click a lit letter to
remove (Opus F18, Sonnet F8). The three-way "cheaper order X → Y → Z" sequence is gone (Sonnet F1,
upheld on that point: the engine measures one turn ahead); B and C are each costed against A as
now · next turn · plan. Projected points no longer sit in a cross-position row (Opus F4): they are
on each head. The drop row prints each position's own tier and gap with no grey disclaimer.
Slot letters are gold / ink / crimson, none of which is a position colour (Sonnet F8). The rail's
between-boxes are 36px seat tokens so five named past boxes fit left of YOU ARE UP, and the scroll
snaps to a whole box so nothing is sliced mid-word (Opus F5, Sonnet F8). Pool rows are two-line.
**Refused.** Sonnet F5 "tier alone or gap alone": the tier is the engine's per-position ordinal
and the gap is in engine units (round-1 ADJ §3 compared raw gaps across positions itself); printing
both, each inside its own position's column, is honest. Opus's verdict that v3 "does not survive"
is a density opinion; the surface is now ~40% fewer tokens (no button grid, no cross-position
points row, no three-way sequence) and the owner can judge it.

### v4 `v4_doors.html`
**Changed.** Doors are sorted by the **board's value order by position** (R2 §8, Opus F1, Sonnet
F2); the re-sort-with-a-slide stays, now driven by an order that is allowed to rank. The order
line prints both orders and its verdict in body-weight ink, inline with the orders. Each door
states what waiting on it leaves at your next turn and what that costs, as attributes; no door is
ever positioned by it. At `late` Hockenson is the fourth door the eye reaches. The displacement
sentence is under every door's value and on every card. Cards show only what differs within the
position; shared facts are said once in the caption (Opus F10). The "Every name" sheet rows wrap
(Opus F3). "The position is not gone; the board has no rated name at it" is replaced by *No
quarterback in the board's top 24* (Sonnet F10). The doors were compacted until the open door's
cards fit at `late` with no scroller.
**Refused.** Nothing adjudicated. Sonnet F2's "the order line is a legend by another name" is a
layout opinion; the line is two sequences and one sentence, and it is the visible reconciliation
round-1 ADJ §1 asked for.

## Reviewer findings I did not act on, and why (per ADJUDICATION_R2)

- **Sonnet A F1 (double counting)** — overturned by R2 §2; implemented as "name the third
  quantity", not "print one number".
- **Opus A F6 (QB forfeit 1.82 inverted)** — overturned on the number by R2 §4; only the scope
  wording changed.
- **Sonnet A F7 (use the engine's tie)** — overturned by R2 §3; `ambiguities` is empty, so the
  margin is rendered and no tie is asserted anywhere.
- **Opus B's `horizon_sensitivity`** — wrong field (R2 §5); the audit covered `time_horizon_adj`.

## Verification

`python3 _build.py` → `node --check` ok ×4. `python3 _shoot.py` → 12 renders at 1440×900, every
assertion green: no page or console errors, no page scroll, no clipping, no text overflow, no
occlusion, nothing cut off by the viewport, every scroller carries its affordance, every captioned
count matches, minimum resident type 12.0px, YOU ARE UP and YOUR NEXT in frame where a rail
exists. `python3 _interact.py` → in-page state switching, the position table, lane focus, "by
position", door re-sort across states, the sheets and the numbers sheet, no errors. Rendered-text
scan of all 12 states (with the numbers sheet open): no "priced", no "UV", no field names, no
"tie" / "coin flip" / "level with"; the `late` denial row prints `0.0` on all four. I looked at
all 20 PNGs after the final build. What I saw and shipped: v1 `late` draws 4 of 7 board rows with
the affordance (the three below the fold are all on the table above); v3's comparison pane scrolls
by one or two "only where they differ" rows in every state; v2's `late` fold is still mostly dark
and now says *the board: 7 names* so it reads as a short board rather than a failed render.
