# #216 — adversarial review of the trace, and design options with measured blast radius

Reviewer: Fable. Commit measured: `f580c11` (the commit that published the trace). Instrument:
`run_216_review_probe.py` (repo root), result sets and tables in `evidence/roster_shape/review_216/`.
Nothing in valuation was changed. Every arm below ran in one process on one code version; the
only thing toggled per arm is the thing named. Six seats (1, 6, 12) x two formats (`12T_ppr`,
`12T_ppr_SF`), real rulebook, shared pool of 481, `set_league_format` called per format,
`build_players_db_from_capture()`.

**Replay gate.** My CURRENT arm reads `compute_draft_board`'s own first row instead of
`build_snapshot`'s. It reproduced the published #216 sequence pick-for-pick in **6 of 6 seats**
(87 of 87 engine picks), so everything below is about the engine the item measured.

---

## 0. Headline: the two receivers and the quarterback are the legality backstop, not the board

`feasibility_first` (#154 tier 3) is a 0/1 sort key (`_feasible`, emitted as
`fills_required_slot`) that leads the sort in `compute_draft_board` **and** in
`pick_synthesis._board_order`. It filters nothing and substitutes nothing: it partitions the board
into "fills one of my unfilled DEDICATED slots" first, and `final_score` still orders inside each
partition. It binds only when `picks_remaining <= unfilled dedicated slots`. In a 14-round 1QB
roster with WR, WR, QB unfilled that is pick 12 — which is exactly where every 1QB seat's
receivers and quarterback appear.

Ablation (`feasibility_first` returns all-1s; nothing else touched):

| format | seat | CURRENT | picks CURRENT forced (`fills_required_slot`) | backstop OFF | lineup pts ON / OFF |
|---|---|---|---|---|---|
| 12T_ppr | 1 | TE8 RB3 **WR2 QB1** | r12 WR, r13 WR, r14 QB | **TE11 RB3 — 0 WR, 0 QB** | 1987 / 1528 |
| 12T_ppr | 6 | TE8 RB3 **WR2 QB1** | r12 WR, r13 QB, r14 WR | **TE11 RB3 — 0 WR, 0 QB** | 1899 / 1465 |
| 12T_ppr | 12 | RB9 TE2 **WR2 QB1** | r12 WR, r13 WR, r14 QB | RB9 TE3 WR1 QB1 (WR at r13, QB at r14 with bpa 0.00) | 1884 / 1704 |
| 12T_ppr_SF | 1 | TE6 QB4 RB3 **WR2** | r15 WR | TE7 QB4 RB3 WR1 | 2469 / 2335 |
| 12T_ppr_SF | 6 | TE7 QB4 RB2 **WR2** | r14 WR, r15 WR | **TE9 QB4 RB2 — 0 WR** | 2357 / 2097 |
| 12T_ppr_SF | 12 | TE5 QB5 RB3 **WR2** | r15 WR | TE6 QB5 RB3 WR1 | 2277 / 2158 |

With the backstop off, seats 1 and 6 in 1QB finish with **eleven tight ends and no quarterback**,
and the board's own tail never "falls through": at pick 14 it still prefers Greg Dulcich (TE,
124.3) to K.C. Concepcion (WR, 165.1) and Michael Penix (QB, 129.0). The forced rows carry bpa
4.18, 4.24 and 0.00. So the published correction — receivers "arrive at rounds 12-13 once every
other position's tail has fallen through" — is wrong. They arrive because the legality backstop
promotes them, at the last picks where a legal roster is still reachable, and the value board is
**inert for WR and QB in this format**.

What this makes `need_bonus`: a tiebreak inside a ~9-point band. It can gate a position only
against candidates whose VOR tail is already inside that band (QB in 1QB after round 2 is the one
case: 0.00 + 4.00 beats a negative field). It cannot gate against any position whose best
remaining VOR exceeds 8.67. The backstop is the only roster-aware mechanism that changes a WR or
QB pick in this format. (#72's exact text I could not locate in the register; its claim as quoted
— the boundary, not need_bonus, is the real override — is what this measures.)

---

## 1. Does the trace survive? Step by step

| claim in the trace | verdict | evidence |
|---|---|---|
| `final_score = universal_value + need_bonus + eligibility_bonus` | **incomplete** — a fourth term, `depth_exposure`, is in the sum (`draft_room.py:2698`) | measured on the chosen TE at r7 (Pitts): depth_exposure **+6.24**; positive on 195-209 rows from r7; max 11.4. It is 0.0 for a position I hold nobody at (`vacant` basis), and positive for positions I already start — it rewards insurance at the hoarded position and cannot counteract |
| `universal_value = bpa + time_horizon_adj + risk_adj` | **holds** | `score_row` |
| `bpa = projected_points − replacement_level(position)`, no normalisation | **holds** | `_scale_vor_to_bpa` is `vor.astype(float)`. The "72x drift" in #74-76 was the old `clip(vor / max(vor) * 100)` scaler, removed by those items |
| replacement constant across a position's rows | **holds** | min = max at every state, 4 positions, 481 rows |
| replacement is "derived from the POOL, not the roster", roster-blind | **wrong as stated** | `replacement_levels` takes `remaining_starter_demand`, which is per-team and roster-derived (every roster, clipped at its slot count). The rank is demand; the level is the pool value at that rank. The level moves only when picks at a position exceed the slot counts of the teams making them — bench picks drain the pool without reducing demand |
| the TE-WR gap widens as I feed it (43.5 → 51.1 → 52.2) | **holds, and is the hoarder's own doing** | seat 1: 43.6 → 59.3 at r11 with 7 TEs owned; 17 TEs drafted league-wide at r10 against 12.7 slots of demand consumed = 4.3 ranks of slide. Seat 12, where the engine hoards RBs instead, the TE gap **shrinks** 43.6 → 7.6 → −2.3 by r13. It is not a TE property; it is a property of whichever position is being bench-hoarded |
| this is #60's "algebraically inert" subtraction | **same arithmetic, opposite regime, different defect** | #60 measured starter-filling picks, where rank shrinkage and pool drain cancel exactly. Bench picks do not cancel. #60 says the dynamism was fictional; #216 says the dynamism that does exist runs in the hoarder's favour |
| `NEED_BONUS_MAX = 12 < 43.5`, so roster state can never reorder | **conclusion holds, mechanism named is wrong** | the cap never binds: rows at `NEED_BONUS_MAX` = **0** across all 87 states; the largest reachable need is 8.67 (1QB) / 8.72 (SF) because the operative constants are `NEED_BONUS_PER_DEDICATED_SLOT = 4.0` and `..._FLEX_SHARE = 1.0`. NEEDCAP arm (`NEED_BONUS_MAX = 1e9`) is **pick-for-pick identical to CURRENT in 6 of 6 seats** |
| need_bonus is the only roster-aware term | **wrong** | `feasibility_first` and `depth_exposure` both read the roster; only the first changes a WR/QB pick |
| propagation via the widening gap is THE mechanism | **secondary** | at r2, gap 43.6, zero TEs owned, the board already prefers Bowers (137.5) to Jefferson (99.4) and to Mahomes (0.0). The primary mechanism is roster-blind VOR deciding every pick, with a ≤ 8.67 nudge and a last-three-picks backstop as the only corrections. The feedback loop makes the stack deeper, not possible |

---

## 2. The QB half: the engine cannot value a quarterback in 1QB, by construction

Best remaining QB's bpa and league QB starter demand, CURRENT, 12T_ppr:

| seat | r1 | r2 | r3 | r4 … r13 | r14 |
|---|---|---|---|---|---|
| 1 | 43.9 (demand 12) | **0.00** (demand 1.0) | 0.00 | 0.00 x 10 | 0.00 |
| 6 | 43.9 (12) | 12.7 (6) | **0.00** (1.0) | 0.00 x 10 | −233.4 (demand 0, pre-draft anchor) |
| 12 | 24.3 (9) | 24.3 (9) | **0.00** (1.0) | 0.00 x 10 | 0.00 |

Mechanism: every control seat opens with a QB (highest raw points), so by my second or third pick
league-wide QB starter demand is exactly **my own unfilled slot**. `_remaining_demand_rank` → 1,
and the replacement at rank 1 is **the best remaining QB himself**. He prices at 0.00 for the rest
of the draft (13 consecutive rounds), every other QB negative, and his `final_score` is
0.00 + 4.00. Any tight end with VOR > 4 outranks him. Penix at pick 14 is `fills_required_slot`.

This is not #155's exhausted-position collapse — QB is not exhausted, it is exactly one slot short
of exhausted, and that slot is mine. The definition "replacement = the demand-th best remaining"
degenerates for the last unfilled slot into "replacement = the candidate", which is the definition
of zero value. No roster-relative term downstream can repair it, because any such term prices a
QB against the same replacement (measured: the RF-MLV arms below still take Penix at r14, forced).

Stated limitation: the demand drop to 1.0 by round 2 is driven by the control's raw-points opening
pick. Human 1QB rooms take QBs slower. But QB1's VOR at r1 is only 43.9 (the 1QB QB curve is flat
above QB12), which loses to 20+ RB/WR/TE rows on pure VOR, so the engine would not take a QB
before round 3-4 in any room; by then demand has fallen and the same collapse begins. The exact
round is simulation-dependent; the mechanism is not.

SF is different: SUPER_FLEX demand keeps QBs priced (bpa 165 → 57) through round 9, after which
QB rows are **unpriced entirely** (`None`; the startable-floor branch declines and the pre-draft
anchor is by ruling not a fallback for it). That is #165/#155 territory, recorded here, not
mine.

---

## 3. What the trace missed — every term that could have counteracted, and why none does

| term | reaches the pick? | what it does here |
|---|---|---|
| `feasibility_first` | **yes — the only one** | partitions the board; binds at the last N picks. The entire WR/QB presence in 1QB (section 0) |
| `need_bonus` | yes, as ≤ 8.67 | zero within-position variance (#87); gates only inside its own band |
| `depth_exposure` | yes, ≤ 11.4 | additive insurance at positions I already start; 0.0 where I am vacant; reinforces the stack (+6.24 on Pitts as TE #4) |
| `eligibility_bonus` | yes | 0.0 for every single-position row |
| `waiting_cost` / `horizon_floor` | **no** — observable-only by ruling (#48) | roster-blind; at r6 Kittle's waiting cost (135) exceeds Coker's (53), so wiring it would not reverse the pick |
| `positional_forfeit`, `survival`, `rival_premium` | **no** | live inside `pick_necessity`, which has zero selection authority (#55 ruling) |
| upside mode | no | `UPSIDE_MODE_DEFAULT_ROUND = 15`; `build_snapshot` forces `balanced` anyway |
| `narrow_candidates` / `_board_order` | yes, neutrally | re-sorts on (`fills_required_slot`, `final_score`) — the same order; why the 6/6 and 87/87 gates hold |
| `marginal_lineup_value` (#84) | **no — built, contract-pinned, stranded** | see below |

**#84's ruling is falsified on the engine's own trajectory.** The contract stranded
`marginal_lineup_value` because "in the displacement regime it agrees with the ranking the engine
already produces", and in the empty-slot regime it equals raw points. Measured at CURRENT's own
states with the replacement-filled variant (section 4):

| format | seat | states | RF-MLV top row == board top row | board's top row's rank under RF-MLV, per round | of the board's top-10 rows, how many change rank |
|---|---|---|---|---|---|
| 12T_ppr | 1 | 14 | **4** | 1,0,10,0,9,6,6,5,2,2,2,1,0,0 | 2,8,9,9,8,10,10,7,10,10,8,4,0,0 |
| 12T_ppr | 6 | 14 | **5** | 0,0,0,0,4,7,5,2,2,2,2,0,1,1 | 2,8,4,9,9,10,10,10,10,10,9,3,3,2 |
| 12T_ppr | 12 | 14 | **6** | 0,0,0,1,2,9,4,4,2,2,3,0,0,0 | 2,6,6,9,9,10,10,10,9,8,10,7,0,0 |
| 12T_ppr_SF | 1 | 15 | 5 | 1,0,0,4,10,0,0,4,4,2,2,1,1,1,0 | 4,4,9,10,10,7,7,10,10,8,8,7,9,5,0 |
| 12T_ppr_SF | 6 | 15 | 6 | 0,0,18,0,5,0,0,6,2,2,2,2,2,2,0 | 2,7,9,4,10,8,8,10,10,8,9,10,8,3,0 |
| 12T_ppr_SF | 12 | 15 | 7 | 0,0,0,0,4,0,12,1,2,2,2,2,0,1,0 | 3,6,3,7,10,9,9,10,9,9,10,10,5,9,0 |

The two rankings agree on the top row in roughly a third of states, and in the hoarding rounds
(5-11) the board's own top row sits 5th-10th under the lineup-marginal ruler while 8-10 of the
visible top ten reorder. #84's "no decision waiting for it" was measured on states where the
roster was sane; on the roster the engine actually builds there is a decision at nearly every
pick. Whether the raw quantity is the *right* ruler is a separate question, answered no below.

---

## 4. Design options, with measured blast radius

All alternative arms keep `feasibility_first` (it is legality, not valuation), keep every
non-engine seat on the control rule, and introduce **no constant**.

**RF-MLV (replacement-filled marginal lineup value)** — Opus's "make replacement roster-relative"
made exact. Pre-fill every empty starting slot with a phantom valued at that slot's replacement
level (argmax position over the slot's eligible set, eligible only at that position; the board
already computes the levels), then score = `lineup(R + phantoms + X) − lineup(R + phantoms)` in
projected points. For an empty slot this is **exactly VOR** (Bowers 137.49, Jefferson 99.44 —
reconciled by hand); for a held slot it is the displacement value; for a candidate the lineup
cannot use it is 0. `_LEX` orders by (RF-MLV, then `universal_value`); `_ADD` by their sum.

**RAW-MLV** — #84's function as built (no phantoms), then `universal_value`.

| format | seat | arm | composition | lineup pts | vs CURRENT | forced picks | QB (round, bpa) |
|---|---|---|---|---|---|---|---|
| 12T_ppr | 1 | CURRENT | TE8 RB3 WR2 QB1 | 1987 | — | 3 | r14, 0.00 |
| | | RFMLV_LEX | **RB9** TE2 WR2 QB1 | 2128 | +141 | 1 | r14, 0.00 |
| | | RFMLV_ADD | **RB10** WR2 TE1 QB1 | 2017 | +30 | 3 | r14, 0.00 |
| | | RAWMLV_LEX | **TE7** RB3 WR3 QB1 | 2236 | +249 | 0 | r2, 0.00 |
| | | control | RB6 WR5 QB2 TE1 | 2211 | | | |
| 12T_ppr | 6 | CURRENT | TE8 RB3 WR2 QB1 | 1899 | — | 3 | r13, 0.00 |
| | | RFMLV_LEX | RB6 TE4 WR3 QB1 | 2043 | +144 | 1 | r14, 0.00 |
| | | RFMLV_ADD | **TE9** RB2 WR2 QB1 | 1920 | +21 | 3 | r14, 0.00 |
| | | RAWMLV_LEX | **TE9** WR2 RB2 QB1 | 2199 | +300 | 0 | r2, 12.7 |
| | | control | WR6 QB3 RB3 TE2 | 2187 | | | |
| 12T_ppr | 12 | CURRENT | RB9 TE2 WR2 QB1 | 1884 | — | 3 | r14, 0.00 |
| | | RFMLV_LEX | TE5 RB4 WR4 QB1 | 2021 | +137 | 1 | r14, 0.00 |
| | | RFMLV_ADD | **RB8** TE3 WR2 QB1 | 1884 | 0 | 2 | r14, 0.00 |
| | | RAWMLV_LEX | **TE7** WR4 RB2 QB1 | 2144 | +260 | 0 | r1, 24.3 |
| | | control | WR7 RB4 QB2 TE1 | 2232 | | | |
| 12T_ppr_SF | 1 | CURRENT | TE6 QB4 RB3 WR2 | 2469 | — | 1 | r6-9 |
| | | RFMLV_LEX | **TE7** WR4 RB2 QB2 | **2550** (> control 2530) | +81 | 0 | r4, r5 |
| | | RFMLV_ADD | RB5 TE4 QB4 WR2 | 2471 | +2 | 0 | r4,6,8,9 |
| | | RAWMLV_LEX | RB5 TE5 WR3 QB2 | 2532 | +63 | 0 | r3, r4 |
| 12T_ppr_SF | 6 | CURRENT | TE7 QB4 RB2 WR2 | 2357 | — | 2 | r6-9 |
| | | RFMLV_LEX | **TE7** RB3 WR3 QB2 | 2457 | +100 | 0 | r4, r5 |
| | | RFMLV_ADD | TE7 QB4 RB2 WR2 | 2327 | −30 | 2 | r5,6,8,9 |
| | | RAWMLV_LEX | TE6 WR4 RB3 QB2 | 2480 | +123 | 0 | r2, r3 |
| 12T_ppr_SF | 12 | CURRENT | TE5 QB5 RB3 WR2 | 2277 | — | 1 | r2,6,7,9,10 |
| | | RFMLV_LEX | **TE7** QB3 RB3 WR2 | 2442 | +165 | 0 | r2,5,10 |
| | | RFMLV_ADD | TE5 QB5 RB3 WR2 | 2339 | +62 | 0 | r2,5,7,9,10 |
| | | RAWMLV_LEX | **TE7** QB3 WR3 RB2 | 2463 | +186 | 0 | r1,2,10 |

What the measurement says about each option:

**A / C — roster-relative replacement ≡ RF-MLV.** Fixes the *starters*: lineup points up in
6/6 seats under `_LEX` (+137..+165), and in SF seat 1 it beats the control. Board blast radius:
top pick changes in 8-10 of 14 states; 8-10 of the top-10 rows reorder through rounds 2-11 —
that is the whole visible board, in exactly the rounds a user looks at it. **It does not fix the
roster shape.** Once the eight starters are above replacement every candidate's marginal is 0
and the order falls to `universal_value` — the same VOR ordering that hoards — so the bench is
RB9, RB10, TE9, TE7. This is the "starters-full collapse" (#62/#115) made concrete: a
roster-relative starter term has nothing to say from about round 6, and the bench needs a ruler of
its own before any option here yields a sane roster. `_ADD` is worse than `_LEX` because adding
VOR back in re-admits the bias on every pick. **It does not fix QB in 1QB** (section 2): the
phantom QB *is* the best remaining QB, so the QB still arrives at pick 14, forced.

What breaks, by count: the layer identity `TAV = UV + need + elig + depth` and its tests
(53 references in `test_draft_room.py`, 26 in `test_pick_synthesis.py`, 19 in
`test_feasibility_backstop.py`, 17 in `test_threshold_reachability.py`);
`test_need_bonus_cannot_flip_a_large_universal_value_gap` becomes false *by design* (a roster
term that can flip a gap is the point); `TEAM_SPECIFIC_CAPS` and everything derived from it in
`pick_synthesis` (`NECESSITY_DENIAL_SATURATION`, `CONTEXT_ELEVATED_THRESHOLD`,
`NECESSITY_DENIAL_CEILING`, `roster_fit_component`) lose their derivation; `rival_premium =
final_score − universal_value` in `draft_strategy` changes meaning to "the rival's lineup
marginal"; `draft_history` / `draft_board_ui` column contracts. Units: rostered players must be
priced in **projected points** — #84 clause 2 measured that `trade_value` drops rostered players
and reorders the bench; `_team_roster_players` prices in trade_value today and
`build_available_pool` discards drafted ids, so wiring needs a roster-side points lookup. The
data exists (the season projections cover every drafted player; this probe used them) — "stranded
for want of data" is now "stranded for want of a lookup".

**B — scale the roster-aware term with the bias.** No derivation exists; any multiplier is a
#56 violation, and the proxy that is derivable — removing the cap — changes nothing (NEEDCAP
identical, 6/6). To matter the term would need to reach the hoarded position's VOR tail
(20-60 points in rounds 5-11), i.e. become a value term of VOR's own order with an invented
shape. A/C is that term with a derived shape. Not recommended.

**RAW-MLV (#84 as built).** Best lineups of every arm (2236 / 2199 / 2144; SF 2532 / 2480 /
2463) — and for an accidental reason: it takes the QB on raw points at r1-2, which is the same
thing the control does, and the only way to get a 328-point QB past a replacement level that
prices him at 0. Its early ordering is raw points (Purdy r1, Mahomes r2 over Bowers/Jefferson),
which is the "confident wrong ordering" the contract recorded, and its bench is TE7/TE9/TE7 for
the same fallback reason as RF-MLV. Not a fix; an instructive control.

**D — repair the QB half at the source (hypothesis, not measured as an arm).** For a slot *I*
have not filled, the free alternative is not the demand-th best remaining (which for the last
slot is the candidate himself) but what will still be available when the draft ends — the
existing `horizon_floor` behind `waiting_cost`. On the recorded states that would price Mahomes
at +46.7 at r2 and +39.0 at r6 instead of 0.00. Two caveats measured on the same states: (i) it is
still below Bowers 137 / Kittle 62, so alone it moves the QB from pick 14 to perhaps pick 7-9,
not to where a manager takes one; (ii) the floor's own error is large here — it predicted a
289.6-point QB would remain at r6 while the QB actually left at r14 was Penix, 129.0 — because
`estimated_bench_demand` under-predicts a room that drafts QBs on raw points. Belongs with #50;
recorded so the implementer knows the quantity already exists and what it would say.

**E — a bench ruler.** Out of scope for this item, but every option above needs it, and it is the
single biggest reason none of them yields a sane roster. #62/#115.

---

## 5. What must be true of the board after a fix, independent of any backstop

For the implementer and the falsification battery. Each is a measurement the probe already
takes; none introduces a threshold.

1. **The backstop must never bind.** With `feasibility_first` disabled, every seat's composition
   must equal its composition with it enabled, and `fills_required_slot` must be True on
   **0** picks across all seats (today: 3 per 1QB seat, 1-2 per SF seat). A fix that still
   needs tier 3 to produce a receiver has not fixed the board.
2. **The last unfilled slot must not price its own candidate at zero.** While my QB slot is
   unfilled in 1QB, the best remaining QB must carry a positive price, and it must fall to ≤ 0
   once the slot is filled (today: 0.00 for 13 consecutive rounds regardless of my roster).
3. **A candidate the lineup cannot use must not outrank one that fills an empty slot with
   positive VOR.** Kittle 55.5 over Coker 11.2 at r6 with three TEs owned is the concrete
   inversion; #84's contract already pins the monotonicity (`marginal_never_rises_as_the_position_fills`).
4. **My own bench picks must not improve my selection signal at that position.** The WR−TE gap
   must not grow with my TE count (today 43.6 → 59.3 at seven TEs); a position's price on MY
   board may fall as the league consumes it, never rise because I did.
5. **The bench regime needs a ruler that is not universal VOR.** Report, per seat with the
   backstop off, the count of bench picks at the single most-drafted position and its trajectory
   against that position's replacement gap. Today (and under every option measured here) the two
   are monotone together. This is the observable that says whether E exists, and no fix to A-D
   makes it move.
6. **Replay gate.** Any battery must show its instrument's pick equals the board's own first row
   at every state (this review: 87/87), or it is measuring something adjacent.

---

## 6. Corrections to the published record, stated plainly

- "The two receivers arrive at rounds 12-13 once every other position's tail has fallen
  through": **wrong**. They are promoted by `feasibility_first`; with it off the board takes
  zero receivers and zero quarterbacks in two of three 1QB seats.
- "`need_bonus` is the only roster-aware term" and "`NEED_BONUS_MAX = 12` is what caps it below
  the bias": **wrong on both**. The cap never binds (0 rows at cap; NEEDCAP identical 6/6); the
  per-slot rates bound it at 8.67; and `feasibility_first` is the roster-aware term that actually
  moves a pick.
- "Replacement is derived from the pool, not the roster": **imprecise**. It is rank-by-demand
  over the pool, and demand is every roster's unfilled starter slots. The level moves only on
  bench picks, which is why the hoarder moves it.
- The widening-gap propagation: **survives as measured, demoted to secondary**. The board is
  already inert for WR/QB at round 2 with the gap at its opening value and zero TEs owned.
- `final_score` decomposition: **omits `depth_exposure`**, which is positive on ~200 rows from
  round 7 and reinforces the stack.
- #84's "correctly stranded because it agrees with the engine in the displacement regime":
  **falsified on the engine's own trajectory** (agreement on the top row in 4-7 of 14-15 states).
  Its second reason — raw points in the empty-slot regime — stands, and the phantom construction
  removes it.

Population sizes: 6 seats, 87 CURRENT states, 481-player pool (WR 197, RB 126, TE 115, QB 42,
DB 1), 30 full drafts across five arms plus 6 re-recorded CURRENT drafts for the static metric.
