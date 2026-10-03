# Fable A — round 2 rationale (revised after ADJUDICATION_R2)

Four variants, each rendering all three states (`early` 1.06 · `mid` 4.07 · `late` 11.06) with a
switcher in the review bar. One shared model (`_src/shared.js`) is rebuilt per state; the variants
differ in layout contract, not in data or vocabulary. `_build.py` injects `states.json` (withheld
values stripped at the boundary) and runs `node --check`; `_shoot.py` renders and asserts; the
PNGs in `_shots/` are what I looked at. `REVISION.md` records what changed and what was refused.

## The governing constraint, as built

**who · why · what else · at what cost**, with rank 1 never presented as the answer:

- The board's first name is called *first on the board* and nothing else. No "pick", "take",
  "recommended", "engine's pick".
- Every alternative is **costed, not graded**, with three real numbers across positions — **now**
  (value gap today, the board's order), **next turn** (what his position leaves at your next turn
  against what the subject's position leaves: `position_next_turn_value`), **plan** (both picks
  together) — and two within a position (**now** and the engine's drop between them). Nothing is
  collapsed, nothing is printed twice, and the sum the reader would compute is named.
- The alternatives header says it outright: *taking one of them is a choice, not an error.*
- No tie is asserted anywhere (`ambiguities` is empty in every state). Margins are rendered as
  margins: *Vele is 0.2 ahead of Concepcion* on a board whose rows span 18.9.
- At `late`, the one measured cause of the negative board is in bright type beside the number:
  *−33.7 of this is the displacement of a starting slot you have already filled — measured
  against your own starters. The player himself: −0.9.*
- The only ordering drawn as geometry anywhere is the board's value order. The next-turn
  quantity is printed as a value with its label; it positions nothing.

## Rulings applied in the shared layer

Board order = `team_acquisition_value`. `positional_forfeit` is shown as *waiting costs X* beside
*what #N leaves* (`position_next_turn_value`), never as the spatial order. `depth_exposure` digit
only under `measured` (the three `late` rows); otherwise the engine's own label verbatim.
`no_surplus` reads *measured, but …* under a **not charged** chip. `denial_value 0.0 / measured`
prints `0.0`. Measured horizons print `±0.0`; the only hidden rows are rows identical across the
names compared. Cliff = `cliff.tier` 1:1; neighbour from the bpa order, named only when the gap
reproduces; the no-neighbour case is scoped: *to a player off this board (measured order)*. No
name is read from a rail pick with `no > consumed`. Headshots: initials primary; the `<img>` is
attached only over http(s). 12px floor holds (12.0px minimum in all renders). `confidence` is
not rendered (R2 §3). Names: family-name collision key, particle kept (`A. St. Brown`).

## §1 change request — v2 has no rail

`DRAFT_ROOM_UI.md` §1 rules a rail across the top with named boxes, glowing own picks and a
re-center. v2 removes it and replaces the span with one sentence (*You pick again at 5.06 (#54),
after 10 picks — rosters 1, 2, 3, 4, 5 each pick twice*). The owner invited this (*"not having
the rail may be worth exploring too"*); it is a change request, not a defect, and **the cost is
named**: (1) §1's "who is on the clock is never ambiguous" is met by a clock sentence (*On the
clock: you (Roster 6) · next up: Roster 5 · last taken: J. Warren by Roster 7*), not by a box;
(2) the drafter's own picks are visible as the lineup strip, not in draft order — the draft board
tab carries that; (3) no emblem has a home on the primary surface until a pick is read back from
the board tab. Both defects R2 §10 named inside the exploration are fixed: the pool size is stated
(*the board: 7 names*) and the drafter is named.

## Cross-cutting findings

1. `early` has no QB and `mid` no TE in the top 24, so a persistent position layer always has an
   honest empty lane/door; its next-turn value is *not measured*, never zero.
2. `late` is all-bench; `displacement_adj` carries 82–100% of every value. Rendering only the
   round-4 board would never have exercised the displacement sentence or the depth digit.
3. Position-order instability measured on the three states (dearest to wait on: WR › RB › TE at
   `early`, RB › WR › QB at `mid`, WR › TE › RB › QB at `late`). v2 holds columns still; v4 sorts
   by the board's value order and states the next-turn order beside it in words.
4. The rail finding: named past + one marked span (v1) and slim seat tokens between named past and
   YOUR NEXT (v3) both keep the rail populated in every state; `early` has five past picks and any
   named-past design must tolerate a short left side.

---

## v1 · `v1_ledger.html` — the ledger, cut (now rail-less; `v1_ledger_rail.html` keeps the rail for comparison)

1. **Hypothesis.** Ledger B's delivery, cut to who / why / what else / at what cost, with
   everything else a gesture away, keeps what the owner liked and removes the density.
2. **Primary / secondary / hidden.** Primary: the ledger — name, slot (lit on the lineup), value,
   the displacement sentence at `late`, *Why* (his own drop; the margin; both next-turn values and
   the two-pick plan), *Also on the table* (up to four alternatives with now · next turn · plan).
   Secondary: lineup column with the wait sentence; the board strip with its scroll affordance.
   Hidden: numbers, the position table, rosters, draft board, debate.
3. **How the decision is communicated.** As a costed set: the first name is a fact of the order;
   each alternative's three numbers are the decision's inputs with the arithmetic done.
4. **Structural difference.** The only variant whose primary object is one player with his
   alternatives priced beneath him; position layer summoned; pool below; click a name.
5. **Roster / pool.** Vertical lineup with the lit slot; the whole board as a constant-row strip
   with a position filter and an honest "↓ scroll · N more".
6. **Rail.** Named past boxes (whole boxes only, newest nearest the clock), YOU ARE UP, one span
   of ticks, YOUR NEXT. Nothing blank in any state.
7. **LLM attachment.** "Debate" (billed, on the clock only) argues the subject against his
   comparator; a sheet describing shape and cost, no invented chair text.
8. **API contracts assumed.** `position_next_turn_value` per candidate (present), `fills_slot`
   (client guesses greedily), `next_turn_pick_no`, `seat.display_name`, `cliff.neighbour_id`,
   basis labels served with the payload rather than copied into the client.
9. **Reusable vs prototype-only.** Reusable: the costed alternatives row (now · next turn · plan),
   the summoned position table, the lit-slot lineup, the named-past + span rail. Prototype-only:
   the 238px side column; the four-alternative cap.

## v2 · `v2_lanes.html` — lanes, no rail

1. **Hypothesis.** Lanes in the lineup's fixed order with the focused lane widened into the
   within-position comparison, and the rail replaced by a clock sentence, tests the owner's two
   invitations at once.
2. **Primary / secondary / hidden.** Primary: four lane headers (what you hold, what waiting leaves
   and costs), each lane's lead with his cost against the first name, the focused lane's
   side-by-side table. Secondary: lineup strip with the lit slot and the pool size; the lanes'
   remaining names. Hidden: numbers, rosters, draft board, debate.
3. **Decision.** The first name is badged *board's first*; every other lead is costed against him
   inline; the focused lane's table shows only what differs within the position.
4. **Structural difference.** Persistent, stable-order position layer; the lanes are the pool;
   comparison always on; no rail.
5. **Roster / pool.** Chip strip with the lit slot; pool is the lanes; empty lanes narrow.
6. **Rail.** None — the §1 change request above.
7. **LLM.** Debate argues the focused lane against the board's first name.
8. **API.** Nothing beyond v1; the lane header object `{pos, held, open, next_turn_value,
   forfeit}` is already on the payload.
9. **Reusable.** The side-by-side within-position table; the clock sentence that names the
   drafter. Prototype-only: four columns at 1440.

## v3 · `v3_trio.html` — three slots (CUT by the owner; file left as-is)

1. **Hypothesis.** A three-slot comparison, defaulting to one name per position, in which the
   board's order is one boxed row and every later row ranks nothing, answers "compare three" and
   "it leans to the higher number" at once.
2. **Primary / secondary / hidden.** Primary: three heads; the board's order (with the
   displacement decomposition at `late`); B and C against A as now · next turn · plan; what each
   position leaves at your next turn; where each starts; the drop behind each; then only rows that
   differ. Secondary: the board (two-line rows, click to fill slot C), lineup strip lit for A.
   Hidden: numbers, rosters, draft board, debate.
3. **Decision.** One row ranks and says so; the rest are facts.
4. **Structural difference.** The drafter builds the comparison; position layer summoned ("by
   position" groups the board, in the board's own position order); rail with boxes both ways.
5. **Roster / pool.** Chip strip; resident board beside.
6. **Rail.** Named past, YOU ARE UP, slim seat tokens for the wait, YOUR NEXT, slim future tokens;
   scroll snaps to whole boxes with YOUR NEXT in frame.
7. **LLM.** Debate the three.
8. **API.** Nothing new; a served `compare(a, b, c)` would be a convenience.
9. **Reusable.** The "one row ranks" discipline; one-name-per-position default; the slim-token
   rail. Prototype-only: slot letters.

## v4 · `v4_doors.html` — doors in the board's order (polished; see REVISION.md › Polish pass)

1. **Hypothesis.** Doors that each do one thing — the position's best, his cost instead of the
   first name, what waiting leaves — sorted by the board's own value order and visibly re-sorted
   when it changes, with the next-turn order stated beside it in words.
2. **Primary / secondary / hidden.** Primary: the order line (both orders, agree/disagree in
   body ink); four doors; the open door's cards (only what differs; shared facts said once).
   Secondary: lineup chips lit for the open door's best; the pool size beside them; each door's
   §14 tank (whole priced pool, starter line, no bands, engine sample as of #N). Hidden: every
   name (two-line sheet), numbers, rosters as lineups with each roster's route for the open
   position, draft board, debate.
3. **Decision.** The first door is the board's first; every other door's best is costed inline
   (now · at #N · both picks); the dearest position to wait on is one amber line on that door.
4. **Structural difference.** Persistent, re-sorted position layer; pool summoned; comparison by
   opening a door; rail reduced to ticks.
5. **Roster / pool.** Chips in the clock line; the pool is a sheet with its count stated.
6. **Rail.** A marked span only: *Next turn 5.06 (#54) · 10 picks away* and ticks; the clock
   line names who is next up and what was last taken.
7. **LLM.** Debate the open door against the board's first name.
8. **API.** Nothing new; `seat.display_name` for the tick tooltips.
9. **Reusable.** The order line; the FLIP re-sort; the within-door cards that suppress shared
   facts. Prototype-only: four doors at fixed width.

## Verification

See `REVISION.md` §Verification: `node --check` ×4; 12 renders with every assertion green (errors,
page scroll, clipping, text overflow, occlusion, cut-off by the viewport, scroller affordances,
captioned counts, 12px floor, rail markers); interaction pass; rendered-text leak scan; all 20
PNGs looked at after the final build.
