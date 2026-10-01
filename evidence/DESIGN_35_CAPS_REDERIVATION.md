# `#35` — what holds about `displacement_adj` if slot alternatives are capped (Formulation C), and what that does to `TEAM_SPECIFIC_CAPS`

*A derivation, checked against the engine by read-only probes. No engine code was edited, nothing is
committed, nothing is implemented (`#184`). Every number below names the fixture and the arm that
produced it. The previous contemplation (`DESIGN_35_FABLE_CONTEMPLATION.md`) is treated as a
colleague's argument and checked, not cited as authority; where it is wrong this document says so.*

## Verdict

**(b) — the registered invariant does not survive C as specified, and it has an exact replacement.**
The replacement is a bound, derived, with the same shape as the existing "one bound that covers both
populations", and it collapses to the shipped `<= 0.0` wherever the level is a live reading:

    single-position probe at p:   displacement_adj <= max(0, L(p) - b(p))          =: stale(p)
    any probe, anchored on a:     displacement_adj <= L(a) - min over reachable s of min(alt(s), B(s))

where `L` is the level `bpa` was anchored on, `b(p)` is the best remaining projection at `p`, `alt(s)`
is the shipped slot alternative and `B(s)` is the best remaining player eligible for slot `s`. Measured
over 71,994 priced rows on 156 real board states: zero violations of either bound, 8,500 single-position
rows lifted (all at the one stale position), maximum lift 18.45 against a maximum staleness of 43.25.

**Two riders, and they are the substance of this document.**

1. **The caps cannot be re-derived as constants under C — a (c)-shaped result for
   `TEAM_SPECIFIC_CAPS`.** The lift is bounded by `stale(p)`, a board-state quantity with no supremum
   (the docstring's own 26-round measurement puts it at 142.68 for tight ends at the last pick). No
   constant bounds it, `#56` forbids choosing one, and `NECESSITY_DENIAL_SATURATION` is a constant.
   Under C it can only become a per-board derived quantity (precedent: `_forfeit_scale`), or the
   premium it saturates must be redefined. Both are valuation changes for the owner. The cost of C
   as specified is therefore explicit: **it moves a universal correction into a team-specific column**,
   and every consumer that reads the two columns apart — the denial ramp first — sees a roster-fit
   premium that is not one.

2. **The sign invariant is a truth about roster context and an artifact of the term's bookkeeping.**
   Decomposed, the lift under C is entirely the anchor's staleness as exposed by the roster; the
   roster-dependent half keeps its sign. Roster context never lifts a single-position candidate, under
   C or otherwise. What C does is route a pool fact through the team term. The variant that caps
   `bpa`'s anchor with the SAME quantity prices every row identically to C (`team_acquisition_value`
   equal to 0.00 on all 388 rows at the documented state), restores `displacement_adj <= 0.0` for every
   single-position row, and puts the premium back inside the caps — leaving the caps' claim exactly as
   false as it is today (multi-eligible rows only). That is a different proposal with its own cost
   (`universal_value` moves; upside mode moves), recorded here for the owner and not recommended by me.

3. **The suite cannot see C.** All 39 tests in the four classes that pin the premise stay green with C
   patched in memory (334 boards built; the cap bound on 2 of them; no measured premium crossed 24.0),
   and the registry census counts positions, which C does not change. Shipping C would reproduce the
   `#52` failure shape with the ratchet built to catch it standing silent.

---

## 0. Fixture, instruments, provenance

- Capture `data/fixtures/sleeper_capture.json` (season 2026, 6,595 players via
  `build_players_db_from_capture`), season projections from the same capture, `SLEEPER_BASIS_SEASON_SUM`,
  `set_league_format(league_format_hint(league))`. Arm `12T_ppr_K_DEF` (16 rounds, roster
  `QB RB RB WR WR TE FLEX FLEX BN×6 K DEF`), every seat sharp, drafted by `simulate_full_draft` in the
  previous pass (821 s) and replayed here from its raw dump `d35_raw.json` — the same 192 picks, so the
  documented Barner/Shaheed state is this fixture's and reproduces to the cent.
- **A/B sweep** (`d35_caps_probe.py` → `d35_caps_sweep.json`, `d35_caps_sweep.log`): every seat's turn in
  rounds 2–14 (156 states; rounds 15–16 are upside mode, where the term is zeroed by construction), each
  built twice in one process: OFF = shipped; ON = `draft_room.board_slot_alternatives` replaced by
  `slot -> min(shipped alternative, best remaining player eligible for the slot)`. Both call sites
  (`displacement_adjustments` and `score_row`'s multi-eligible seam) go through that one name, so the
  toggle is one thing. The levels the term actually used were captured by wrapping
  `displacement_adjustments` and copying its `levels` argument (the production quantity, never
  recomputed); the alternatives each arm used were captured by wrapping the seam; `b(p)` is the maximum
  `projected_points` at `p` on the board, which is the remaining pool (asserted: no drafted id on it).
  `mode="auto"` with production-shaped picks (`pick_no, round, roster_id, player_id`) resolved to
  `balanced` on all 156 states.
- **Test arms** (`d35_caps_tests.py` → `d35_caps_tests_control.log`, `d35_caps_tests_C.log`): the four
  classes that pin the premise, run in-process on the shipped code and again with C patched in memory
  (`compute_draft_board` wrapped to build the shipped board, read `b(p)` off it, rebuild capped;
  `draft_strategy.compute_draft_board` re-pointed too, since it binds the name at import). No disk
  mutation, `PYTHONDONTWRITEBYTECODE=1`.
- **Anchor-capped variant** (`d35_cplus_probe.py`): pick 164, seat 5, three arms in one process.
- Scratchpad: `/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/`.
  Not committed; ordinary measurement scripts.

Ordinals below are labelled: `rank_on_board(final_score)` is the board's own order, not the pick — the
pick goes through `pick_synthesis._board_order` (backstops first) and was not measured here.

---

## 1. The two shipped constants, precisely

The `THE SIGN` docstring says `TEAM_SPECIFIC_CAPS` "hand-exempts this term from the bound two shipped
constants derive from". At the time that was written the two were `NECESSITY_DENIAL_SATURATION` and
`CONTEXT_ELEVATED_THRESHOLD`. The second was retired with its flag at `#25` (2026-09-21) — the registry
entry says so and `pick_synthesis` records it at the constant's old site. Today the tuple feeds:

| constant | derivation (`pick_synthesis.py`) | value | read by |
|---|---|---:|---|
| `TEAM_SPECIFIC_CAPS` | `(dr.NEED_BONUS_MAX, dr.DEPTH_EXPOSURE_MAX)` | (12.0, 12.0) | the two below; `test_probability_bounds.TheCapsTupleBoundsWhatItActuallyBounds` |
| `NECESSITY_DENIAL_SATURATION` | `sum(TEAM_SPECIFIC_CAPS)` | 24.0 | `denial_component` (line ~840): `min(rival_premium / SATURATION, 1.0) * CEILING` for `rival_premium > 0` |
| `NECESSITY_DENIAL_CEILING` | `SATURATION * (NECESSITY_DENIAL_WEIGHT / dr.NEED_BONUS_MAX)` | 20.0 | the same line |

So there are still two shipped constants downstream of the tuple; the second is now the ceiling, which
is pinned to the saturation point as one slope (`test_removing_the_flat_spot_did_not_re_weight_the_term`:
`CEILING / SATURATION == WEIGHT / NEED_BONUS_MAX`).

**The exemption, quoted from the tuple's own comment:**

> #216 added a FOURTH term, displacement_adj, and it is deliberately NOT here: it is non-positive by
> construction (draft_room.displacement_adjustments -- it only ever removes credit the league anchor
> gave for a slot the roster cannot offer), so it cannot raise the sum these caps bound.

followed, in the same comment, by its own correction ("THAT PREMISE IS FALSE ... Travis Hunter ...
+79.44") which confines the falsity to the multi-eligible population and leaves the values in place
under `#56`. `rival_premium` is `opp_row["final_score"] - opp_row["universal_value"]` on the rival's own
board (`draft_strategy.py` ~1223) — the SUM of `TEAM_SPECIFIC_TERMS`, including the fourth.

**What the two members are derived from, and why C does not touch them.** `NEED_BONUS_MAX = 12.0` is
the cap on `need_bonus`; `DEPTH_EXPOSURE_MAX = NEED_BONUS_MAX` by the "same class, same bound" argument
in `draft_room.py` (~565). Neither reads `displacement_adj`. The pinned test derives both sides of the
tuple (`*_MAX` names in `draft_room` intersected with `TEAM_SPECIFIC_TERMS`) and asserts that
`displacement_adj` has no cap. Under C the tuple's MEMBERS remain exactly right. What C breaks is the
CLAIM about the sum, on a population where today it happens to hold.

**What breaks numerically.** Nothing crashes. The ramp clips: every premium above 24.0 receives the same
denial contribution, 20.0 — the "flat spot" `#144` was closed for. Measured, sweep, per-row `TAV − UV`
over all 156 boards (each board is a rival's board from some other seat's point of view, so this is the
population `rival_premium` draws from):

| | OFF (shipped) | ON (C) |
|---|---:|---:|
| max premium | 10.20 | **28.65** |
| rows with premium > 24.0 (saturation) | 0 | **295** (2 states: seat 5, picks 149 and 164) |
| rows with premium > 12.0 (one term's cap) | 0 | **2,238** |
| unclipped denial the ramp would have given at 28.65 | — | 23.9, clipped to 20.0 |

At pick 164 the 145 rows past saturation are every receiver on the board, at an identical 28.65
(`depth_exposure` 10.20 + lift 18.45): the ramp cannot tell any two of them apart. Two tests assert this
cannot happen — `test_the_flat_spot_is_gone` and `test_the_saturation_point_is_derived_from_every_term_it_sums`
— and both stay green under C, because their `_RealBoards` (vendor reconstruction, opening board drained
from the top, seat 1's `pick_analysis`) never reach a state where the anchor is stale (§6).

---

## 2. The derivation

### 2.1 Notation

- Positions `p` with a level `L(p)`: `point_replacement[p]` after `_fill_omitted_from_anchor`, the
  `free_alternative` handed to `displacement_level`. Within a position's demand domain it is the
  rank-`N` remaining player; below it, the pre-draft anchor.
- `b(p)`: the best remaining projected points at `p` (a pool property; the same for every roster).
- Slots `s` with eligibility `E(s)`. Shipped: `alt(s) = max{L(q) : q ∈ E(s), L(q) defined}`
  (`shared_slot_alternatives`). Under C: `B(s) = max{b(q) : q ∈ E(s)}` and `alt_C(s) = min(alt(s), B(s))`.
  A slot whose eligible positions carry no level is OMITTED in both, and `displacement_level` then falls
  back to `free_alternative` for it (absence travels; `#187`).
- A probe with eligibility set `P` anchored on `a ∈ P` reaches `R(P) = {s : P ∩ E(s) ≠ ∅}`.
- `displacement_level` returns `displaced = max(solve eviction, min{alt_C(s) : s ∈ R(P)})` and
  `adjustment = L(a) − displaced`.

### 2.2 The one bound, unchanged in form

**Lemma 1.** `adjustment <= L(a) − min{alt_C(s) : s ∈ R(P)}` for any probe. *Proof:* the clamp. This is
the existing "one invariant" verbatim with `alt_C` for `alt`; C changes the VALUE of the right-hand
side, not the statement, and since `alt_C <= alt` the bound can only rise.

### 2.3 The single-position population

**Theorem.** For `P = {p}`: `adjustment <= stale(p) := max(0, L(p) − b(p))`, with equality whenever a
dedicated `p` slot is held by its phantom under C and `L(p) >= b(p)`.

*Proof.* Every `s ∈ R({p})` admits `p`, so `alt(s) >= L(p)` (the shipped premise, still true of `alt`)
and `B(s) >= b(p)`. Hence `alt_C(s) = min(alt(s), B(s)) >= min(L(p), b(p))`, and by Lemma 1
`adjustment <= L(p) − min(L(p), b(p)) = max(0, L(p) − b(p))`. For tightness: the dedicated slot's
alternative is `min(L(p), b(p)) = b(p)`; every other reachable slot is held either by a phantom
`>= b(p)` or by a real player who beat such a phantom; so the cheapest eviction is that phantom,
`displaced = b(p)`, `adjustment = L(p) − b(p)`. ∎

**Corollary (where the lift can live).** `stale(p) > 0` requires `L(p) > b(p)`. On the demand-rank
branch `L(p)` is the rank-`N` remaining player with `N >= 1`, so `L(p) <= b(p)` and the shipped
`<= 0.0` holds verbatim. A single-position lift is therefore possible only where the level is NOT a
reading of the remaining pool: the pre-draft anchor once the pool has drained past it, or a floor
(`startable_floors`, `streaming_floors`) — see §6 for the second.

**Decomposition (the fact §3 rests on).** With `alt_C* = min{alt_C(s) : s ∈ R({p})}`:

    adjustment = [L(p) − alt_C*]  +  [alt_C* − displaced]
                  >= 0, a property of the pool and the slot structure, identical for every roster
                                     <= 0, the roster's own deduction (the clamp)

For a position with a dedicated slot, `alt_C* = min(L(p), b(p))` exactly, so the first bracket IS
`stale(p)`. The lift never exceeds the first bracket; the roster can only reduce it.

### 2.4 The multi-eligible population

`min{alt_C(s)} = min( min{alt(s)}, min{B(s)} )` over `R(P)`, so

    adjustment <= max( L(a) − min{alt(s) : s ∈ R(P)},   L(a) − min{B(s) : s ∈ R(P)} )

the shipped multi-eligible bound OR "anchor minus the best remaining player for the cheapest slot the
second eligibility reaches", whichever is larger. The second term is not bounded by `stale(a)` — the
reachable slot may belong to a different, more-drained position — so the multi-eligible lift, already
unbounded by any constant today (+79.44 on the owner's IDP board), is weakly larger under C.

### 2.5 No lower bound

Unchanged and open: `displaced` is whatever my own weakest reachable starter is worth. `−67.00` in the
existing record; `−50.43` for running backs at pick 164 here.

### 2.6 Measured against the derivation

Sweep, 156 states, 71,994 priced rows (71,838 single-position, 156 multi — one row, Travis Hunter, whose
DB half reaches nothing in this rulebook):

| quantity | OFF | ON (C) |
|---|---:|---:|
| violations of Lemma 1's bound (any row) | 0 | **0** |
| violations of `stale(p)` (single-position) | 0 | **0** |
| rows where `adj_ON < adj_OFF` | — | **0** (the cap never deepens a deduction) |
| single-position rows with `adj > 0` | 0 | **8,500**, all WR, all at a stale position (0 at a non-stale one) |
| states where the cap binds at any slot | — | 65 of 156; first at pick 104 (round 9) |
| max single-position lift | 0.00 | **18.45** (seat 5, picks 149 and 164) |
| max `stale(p)` on any board | — | WR 43.25, QB 24.03, DEF 8.72, K 8.28 (round 14) |

QB is stale by 24.03 at round 14 and no quarterback is ever lifted: the only slot a QB reaches is held
above 328.6 on every roster, so the second bracket swallows the first. That is the decomposition
working, not an exception to it. By round:

| round | states where cap binds | max stale (L − b) | max single lift | max premium ON | rows > 24 ON |
|---|---:|---|---:|---:|---:|
| 2–8 | 0 | — | 0.00 | 8.67 | 0 |
| 9 | 5 | QB 11.24, DEF 2.34 | 0.00 | 4.00 | 0 |
| 10 | 12 | QB 11.24, WR 5.53, DEF 5.21, K 2.49 | 5.53 | 6.20 | 0 |
| 11 | 12 | QB 12.62, WR 11.88, DEF 7.16, K 5.03 | 11.88 | 12.55 | 0 |
| 12 | 12 | WR 18.45, QB 13.45, DEF 8.72, K 8.28 | 13.89 | 14.56 | 0 |
| 13 | 12 | WR 36.06, QB 20.45, DEF 8.72, K 8.28 | 18.45 | 28.65 | 150 |
| 14 | 12 | WR 43.25, QB 24.03, DEF 8.72, K 8.28 | 18.45 | 28.65 | 145 |

The documented state, pick 164, seat 5, single-position rows (per-position constants, as the term is):

| pos | n | L | b | stale | adj OFF | adj ON | mechanism |
|---|---:|---:|---:|---:|---:|---:|---|
| WR | 144 | 216.25 | 173.00 | 43.25 | 0.00 | **+18.45** | evicts Deebo Samuel 197.80, a real occupant, who now holds FLEX_7 against a capped phantom of 179.46 |
| RB | 94 | 165.82 | 176.98 | 0 | −50.43 | −31.98 | same eviction; anchor live, so still a deduction |
| TE | 98 | 151.44 | 179.46 | 0 | −38.83 | −38.83 | evicts Ferguson 190.27 either way |
| QB | 24 | 328.60 | 305.69 | 22.91 | −15.92 | −15.92 | QB slot held by Prescott 344.5 |
| K | 15 | 121.78 | 113.50 | 8.28 | −1.85 | −1.85 | held |
| DEF | 12 | 107.95 | 99.23 | 8.72 | −19.12 | −19.12 | held |

At pick 140 the WR lift is 13.89 against a `stale` of 18.45: the receiver evicts the capped FLEX phantom
(202.36, the best remaining running back), not the dedicated WR phantom, because both WR slots are held.
The Theorem's bound is tight only at an open dedicated slot; elsewhere the roster reduces it.

---

## 3. Should the invariant survive?

**The question.** Is "my flex occupant is weak, so this receiver is worth more to me" a fact the board
should price, or double-counting? The shipped argument (`displacement_adjustments`):

> the league says a free player at that level is coming, and the candidate's VOR already prices him
> against it. Lifting him again for my own weak starter would be paying twice for one fact.

**The answer, from the decomposition.** That argument is conditional on its premise: a free player at
`L(p)` is coming. C caps a slot only where that is false — where nobody left in the pool at any
position the slot admits is worth `L(p)`. The lift under C is bounded by `stale(p) = L(p) − b(p)`, which
is precisely the size of the falsehood, and the roster-dependent bracket is still `<= 0`. So under C
the term never pays for "my weak starter"; it pays back, at most, what the anchor over-charged. For
Shaheed at pick 164 the price is `points − displaced = 170.24 − 197.80 = −27.56` — the distance to
unseating Deebo, a real player. The shipped price, `−46.01`, is the distance to unseating a receiver who
does not exist. The sign of `adjustment` merely reports which side of a stale anchor the real reference
object sits on.

**So the substantive claim survives and the registered claim does not.** "Roster context never lifts a
single-position candidate" is true of the engine under C: the roster's own contribution is the second
bracket, and it is non-positive by the same clamp as today. "`displacement_adj <= 0` for a single-position
candidate" is false under C, because C makes the term carry two things — a roster deduction and an
anchor correction — and the second is a universal quantity (the same `stale(p)` on every seat's board)
that has been filed in a team-specific column. The non-positivity was an artifact of the uncapped
design's choice of floor for the phantom (`alt(s) >= L(p)`, which C removes), not a fact about rosters.

**Is the lift double-counting anywhere?** Not against `bpa`: `bpa + adj = points − displaced` in both
designs, and under C `displaced` is a real occupant or an obtainable player. Where it IS a
double-count is downstream: `rival_premium` reads `TAV − UV` as "how much more this rival's ROSTER makes
him worth" and feeds the denial ramp with it. Under C, at pick 164, every receiver's premium on seat 5's
board carries 18.45 of anchor correction that has nothing to do with seat 5's roster fit (a seat with an
open dedicated WR slot would carry the full 43.25; a seat with every reachable slot held above 216.25
would carry none). The premium becomes "roster fit plus however much of the pool's staleness this
roster's openness exposes", which is not the quantity the ramp was derived for.

**The same prices, in the right column.** Cap `bpa`'s anchor with the same quantity — `L'(p) = min(L(p),
b(p))` — and keep C's slot alternatives. Then `bpa' = bpa + stale(p)`, `adj' = adj − stale(p)`, and
`team_acquisition_value` is unchanged on every row; and since `alt_C(s) >= min(L(p), b(p)) = L'(p)` for
every slot admitting `p`, the shipped derivation of `<= 0.0` holds verbatim. Measured
(`d35_cplus_probe.py`, pick 164, seat 5, 388 priced rows, three arms in one process):

| | OFF | C | anchor-capped variant |
|---|---:|---:|---:|
| max `|TAV(variant) − TAV(C)|` | — | — | **0.00** (388 of 388 rows) |
| single-position rows with `adj > 0` | 0 | 144 | **0** (max −10.13) |
| rows where `UV(variant) − UV(C) ≠ stale(p)` | — | — | 0 |
| max premium `TAV − UV` | 10.20 | 28.65 | **−10.13**; rows > 24.0: 0 |
| Shaheed `bpa / adj / UV / TAV` | −46.01 / 0.00 / −48.48 / −38.28 | −46.01 / +18.45 / −48.48 / −19.83 | −2.76 / −24.80 / −5.23 / −19.83 |
| Barner (TE4) | 28.02 / −38.83 / 18.02 / −20.21 | unchanged | unchanged |

So C and the variant draft identically (the pick reads `final_score`) and differ only in what
`universal_value` and the team terms say — which is exactly what the caps, the denial ramp,
`pure_value`, `expected_value_of_waiting` and the positional-forfeit curves read. Its costs, so the
owner is not sold half of it: `universal_value` moves by `stale(p)` on every row at a drained position
(the best remaining receiver's `bpa` becomes 0.00 — the "rank-1" shape the contemplation warned about,
confined to positions whose anchor the pool has already drained past); and upside mode, which scores on
`bpa` alone, would change under the variant and does not under C. The contemplation set the variant
aside with "leave `bpa`'s anchor alone"; on the evidence here that choice is what manufactures the lift.

---

## 4. If the invariant changes, what replaces it

Following `invariant_registry.py`'s own conventions (a claim in one sentence as the code states it; a
population enumerated by derivation, never listed; a census moved only after re-verification, and
signed for in the population text rather than absorbed by a `--write`, as the 29 → 30 entry was).

**Claim.**
> For a single-position probe at `p`, `displacement_adj <= max(0, L(p) − b(p))` — the shipped `<= 0.0`
> wherever the level is a reading of the remaining pool, and the anchor's staleness where it is not;
> the roster-dependent half of the term, `min(reachable alternative) − displaced`, is non-positive on
> every roster. For any probe, `adjustment <= L(a) − min over reachable slots of min(alt(s), B(s))`,
> and the clamp in `displacement_level` makes it exact.

**Population — and this is the correction the current entry needs whether or not C ships.** The
registered population, `_positions_with_a_level` (census 9), cannot move under C: C adds no position.
What C changes is the DOMAIN of the alternatives — what `board_slot_alternatives` is a function of.
Today that is `(levels, roster_positions)`; under C it must also take the pool. So the population to
count is the seam's inputs, derived from the code (the same way `_take_model_consumers` and
`_python_rendered_figure_sites` are derived by AST):

```python
def _slot_alternative_inputs() -> list[str]:
    """What a slot's free alternative is a function of. Today: the levels and the roster shape,
    so every alternative is a level and the shipped sign derivation holds. A THIRD input -- the
    remaining pool -- is exactly the event that breaks the single-position bound, and it does
    not change the position count the previous census watched."""
    import inspect, draft_room as dr
    return sorted(inspect.signature(dr.board_slot_alternatives).parameters)
# census: 2
```

Keep the position census beside it if the owner wants both; the point is that ONE of them must be able
to move when C lands, and the existing one cannot. The entry's `population` text should say so: "the
`#216` per-slot alternatives admitted multi-eligible probes without moving this count; a pool-capped
alternative admits single-position lifts without moving it either — two expansions, zero notifications."

**Tests that would pin it.**

1. *Unit, both populations, cap exercised.* `test_216_displacement.DisplacementLevelDerivationTests`
   with a synthetic `B(s)` below `LEVELS` for at least one position (e.g. WR 216 → best remaining 173):
   assert `adjustment <= stale(p)` on the same grid as `test_a_single_position_candidate_is_never_lifted`,
   `== stale(p)` with the dedicated slot open, `<= 0` with every reachable slot held above `L`, and the
   grid's population stated and counted as that test does.
2. *Non-vacuity, in the direction that matters.* At least one single-position probe in the grid is
   lifted — otherwise the new bound re-pins the old vacuity, exactly as the docstring says the
   predecessor did.
3. *Real board.* `WiringOnTheRealRulebookTests.test_the_identity_closes_with_the_fourth_term_on_every_priced_row`
   currently asserts `displacement_adj <= 0.0` per row on a four-tight-end board at pick 5, where no
   anchor is stale. Under C it should assert `<= max(0, (projected_points − bpa) − max projected_points at p)`
   — both terms emitted — AND build a state where the cap binds (this fixture's does not: `binds []` on
   every board before pick 104 here), asserting that it bound, or the test measures nothing about C.
4. *The premise the caps cite.* `TheCapsTupleBoundsWhatItActuallyBounds` keeps its structural
   assertions; `TheDenialNormalizerSaturatesAtItsOwnBoundTests` must sample a drained state or its two
   saturation assertions are vacuous under C (they passed 39/39 with C patched in).

---

## 5. `TEAM_SPECIFIC_CAPS` under the cap: the exemption refuted, and what could replace it

**Refuted.** The exemption's sentence — "non-positive by construction ... so it cannot raise the sum
these caps bound" — is false under C for the single-position population, which is every row on a
non-IDP board. Today the falsity lives in a population that is EMPTY in this format (one multi-eligible
row, lifted 0.00 because his second eligibility reaches nothing); under C it is 8,500 rows across 56 of
156 states and every receiver from round 10 on. The tuple's members stay correct; the sentence goes.

**Can the constants be re-derived?** A cap on the fourth term's lift would have to be `stale(p)`, and:

- it is a board-state quantity, roster-independent but pool-dependent, with no supremum — 43.25 at
  round 14 of a 16-round draft here, and the `displacement_level` docstring's own 26-round measurement
  (TE level 149.17 against a best remaining 6.49) gives 142.68 at the last pick of a startup;
- so no constant bounds the premium under C, and `#56` forbids choosing one;
- `NECESSITY_DENIAL_SATURATION` is a module constant read as a divisor. A constant derived from a
  tuple of constants cannot bound a quantity that has no constant bound. **This is the (c) result for
  the caps: under C as specified there is no constant to derive.**

**What is derivable, and what each costs.** None of these is a repair; each is an owner ruling.

| option | what changes | derivable? | cost |
|---|---|---|---|
| (i) leave the constants | nothing | — | the flat spot `#144` closed for returns: 295 rows in 2 of 156 states clipped at an identical 20.0; 2,238 rows past one term's cap; the two tests that assert otherwise stay green because they never sample the state (vacuous) |
| (ii) per-board saturation: `SAT(state) = sum(caps) + max_p stale(p)` (+ the multi term), ceiling derived from it so the slope holds | `denial_component`'s divisor becomes a measured quantity | yes — precedent `_forfeit_scale`, which replaced `FORFEIT_SCALE_MAX` with "the spread of the pool the candidates came from"; measured to cover the max premium on all 156 states | the denial ceiling becomes state-dependent (0.8333 × (24 + 43.25) ≈ 56 necessity points at pick 164 against 20 today); `stale(p)` is universal, so a "roster-fit" saturation would be derived from a non-roster quantity — the misfiling of §3 propagated one layer up |
| (iii) the anchor-capped variant | `bpa`'s level capped at `b(p)`; C's slot alternatives kept | yes — no new quantity; the shipped derivation of `<= 0.0` holds verbatim and the caps' claim is exactly as sound as today | `universal_value` moves by `stale(p)` at drained positions; upside mode changes; it is not the proposal on the table |
| (iv) redefine `rival_premium` as the sum of the CAPPED terms | `draft_strategy` ~1223 | yes, trivially | the premium stops carrying the rival's real over-credit (the negative half is already clipped to 0 by the ramp, so the loss is the positive multi-eligible half and, under C, the lift); a change in what the quantity measures |

Under (ii), (iii) or (iv) `TEAM_SPECIFIC_CAPS` itself does not change. What changes is either the claim
about the sum (ii, iv) or the term's contents (iii). The one thing that cannot be done under any of them
is to keep `NECESSITY_DENIAL_SATURATION` as a constant derived from the tuple AND have it bound the
premium under C. That was already untrue for multi-eligible rows and the record says so; C makes it
untrue for the common case, and there is no constant to reach for.

---

## 6. What I could not determine

- **Whether the pick flips.** `final_score` at pick 164 under C: Shaheed −19.83, Barner −20.21; under
  the shipped board the top row by `final_score` at 18 of 156 states changes from a kicker or defense to
  a receiver. The pick goes through `_board_order` (feasibility and fieldability backstops first) and
  `narrow_candidates`; I did not run `pick_synthesis.build_snapshot`, so these are `rank_on_board`
  readings, not pick order.
- **`rival_premium` proper.** I measured `TAV − UV` on every seat's own board, which is the population
  the rival premium is the maximum over; the premium at a given turn is the max across the intervening
  rivals' boards, so "2 states with rows past 24.0" is a count of boards, not of turns whose denial
  ramp would clip. Any turn with seat 5 intervening at rounds 13–14 would.
- **Floors.** The Corollary in §2.3 covers the demand-rank branch. `startable_floors` (superflex QB)
  and `streaming_floors` (`#30`, K/DEF) are by construction not pool readings and can sit above the best
  remaining player; under C a slot at a floored position could be capped below its floor and lift a
  single-position probe whose level is a floor, not an anchor. The Theorem's bound holds regardless
  (it assumes nothing about the level's basis); the statement "only anchor-basis positions lift" needs
  those two branches checked on a superflex arm and on a capture with weekly lines. This capture has
  none (`weekly_weeks: 0`), so the streaming branch was not exercised here.
- **Other formats and startups.** One draft, one 16-round K/DEF format, balanced mode only. The
  142.68 tight-end figure is quoted from the docstring, not re-measured. Staleness grows with pool
  drain, so a 26-round startup is the state where the lift is largest and where every reachable slot
  is most likely to be held above it; which effect wins there was not measured.
- **Whether the anchor-capped variant is right.** It restores the invariant and the caps' status and
  prices every row as C does. I have not measured its effect on upside mode, on the positional-forfeit
  curves (which walk `universal_value`), or across formats, and the contemplation's "rank-1" hazard is
  a real change in what `universal_value` means at a drained position. It is recorded, not recommended.
- **The `#216` pre-registered gates.** `run_216_shared_slot_probe` patches exactly the seam C would
  patch, so C can be gated by the existing harness (18 drafts, nine gates, the two-sided over-correction
  guard). Not run here — it is a multi-hour battery and this task was derivation.
