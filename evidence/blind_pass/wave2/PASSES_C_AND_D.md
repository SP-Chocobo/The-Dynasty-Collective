# `#52` Wave 2 — passes C and D, condensed from the raw reports

> Both declared **no contamination**, and both verified the `git archive --exclude` before reading
> — the structural denial Wave 2 adopted from Pass B's own improvisation. Target
> `origin/claude/...ff6qlu`. C: 1,432s / 110 tool uses. D: 1,456s / 100 tool uses.
> Condensed for length; measurements preserved verbatim. Claims until the ledger says otherwise.

## Pass C

**C-1 (HIGH, NEW) — the contested-identity guard is a function of the REMAINING pool.**
`draft_room.py:1420-1478`, applied at `:1415` to the *undrafted* pool only; `:2061-2068`
(`_team_roster_players`) never applies it at all. Two players resolving onto one vendor record
are both blanked — until one is drafted, at which point the survivor inherits the whole record.
Measured (12T_ppr): with nobody drafted, Brian Robinson and Bijan Robinson both carry
`trade_value NaN, projection NaN, proj_3yr NaN`. **Draft Bijan and Brian's row becomes
`trade_value 99.0, projection 346.0, proj_3yr 840.0, _match_verified True,
identity_basis "matched"`** — `time_horizon_adj 0.0 → +6.51`, `universal_value −96.23 → −89.72`.
Bijan's three-year outlook applied to an 89-point player and labelled a clean match. On the
roster side it is unconditional: `_team_roster_players([Brian])` returns `value 99.0` with Bijan
still in the pool.

**C-2 (HIGH) — `time_horizon_adj` population mismatch.** Independent confirmation of W1-02.
Shipped mean −3.70, 86% negative; same-population −0.02, 48% negative. By position RB −6.59,
TE −6.31, WR −2.13, QB +0.37. Adds: the adjustment *moves when other players are drafted*
(169 undrafted players shift across 6 rounds) — "a player property that moves because other
players were drafted". Also notes `d_scale` injury relief requires `adj > 0`, so it essentially
never applies to RB/TE.

**C-3 (HIGH, NEW) — `qb_startable_floor` is in VENDOR units, compared against league-scored
points.** `draft_room.py:1480-1497` reads `merger.projections`; `:1623-1629` compares to
`_points`, which since `#180` is Sleeper season-sum under the league's rules. Holds on the
fixture by coincidence (163.5 vs 164.3 → same rank). Re-scored with `pass_td=4, pass_yd=0.025`:
the vendor floor lands on the plateau, rank 26 vs 33, level 171.37 vs 128, **QBs in the overall
top-24 go from 11 to 0.** Exactly the "rank on the far side of the cliff" failure the docstring
says the floor makes impossible.

**C-4 — anchor cache key incomplete.** Confirms W1-03 with new numbers: top 30 RBs to IR → key
unchanged, anchor served 185.64 vs rebuilt 163.82; `roster_points_lookup` serves Gibbs at 411.89
after IR, rebuilt 314.97.

**C-5 (HIGH, NEW) — superflex: once the startable QB tier is drafted, every remaining QB is
unpriced AND carries no absence kind.** 12T_ppr_SF, 32 startable QBs drafted (3/team, routine in
SF startups): remaining QBs 116, **priced 0**. Michael Penix — 129 projected points, real
`bpa_source` — has `final_score None, absence_kind None`, board rank **469 of 1034**, below all
439 priced rows. **10 rows with real projections carry `absence_kind=None` while unpriced**,
breaching the invariant stated at `:2331-2336`. The engine's own autodraft stops at 24 QBs, so
the battery cannot reach this state.

**C-6 (MEDIUM, NEW) — `block_opportunity` is unreachable in production.** Since the `#206`
normalisation, p_take at a rival's rank 1 is 0.025. Across **10 real board states, 460
candidates: fired 0 times**; 192 cleared the premium bar, none the path bar. Docstring says it
fires for "the top ~28%". The tests that cover it hand-feed `take_prob`.

**C-9 (MEDIUM, NEW) — round is the round of the last pick MADE, not the pick being decided.**
`draft_room.py:3004-3005`. `test_draft_room.py:2121-2132` pins the off-by-one: it builds 14
complete rounds (board is for 15.01) and asserts `"balanced"`. `PickSnapshot.round` disagrees
with `pick_label` at every x.01.

**C-11 — `prose_names` shield.** 283 of 625 checkable blocks (45%) exempt, `was` alone 194.
Shield off exposes `test_the_seam_is_load_bearing` (real name `..._not_decorative`) and
`remaining_league_picks` (renamed `remaining_draft_capacity`). Notes
`test_missing_proj_3yr_is_neutral_not_a_penalty` is **not backticked**, so it was never even a
candidate.

**C-11b (NEW) — thirteen fixtures encode the pre-`#201` universe**, including
`test_replacement_anchor_boundary`, `test_threshold_reachability`, `test_cdme_metamorphic`.
`TradeValueBranchIsAnchoredToo` says "measurement says that branch IS the IDP path"; production
records the trade_value branch at **0 of 1,119 rows**.

## Pass D

**D-1 (HIGH) — `time_horizon_adj`, independently again.** Season-pct shift RB +23.0, TE +27.3,
WR +23.5, QB +10.5. 206 of 256 rows move ≥2 points; **45 rows sit at the −10 clamp** (38% of RB,
34% of TE) against 2 at +10. Worked case: Stribling production −3.3 vs matched +4.5, **sign
flipped**; his upside `growth` is 0.0 in production and 22.6 matched — **+11.3 `final_score` in
the rounds where growth "DECIDES late picks"**.

**D-2 (HIGH) — the two take models, quantified at 3.01.** One rival board: total take mass 41.19,
of which **58.7% is 1,208 unpriced rows at the 0.02 floor**. Rank-1 player gets p=0.0134. So
Chase Brown gets `survival 0.746` and **every other candidate (81 of 82) gets 0.989** —
`survival_component` 5.08 vs 0.22 against a nominal weight of 20: **the term is dead on
production boards while "individually reachable" on synthetic ones.** Over the same 22 rival
boards the survival model expects 1.62 RBs taken; the forfeit model expects **14.78**. Per rival
pick the forfeit model assigns RB 0.65 + WR 0.56 = **1.21 probability** — the mutual-exclusivity
violation `board_take_mass`'s own docstring says "needs no league data to state". And every QB
carries `positional_forfeit = 0.00` in a superflex league where 11 QBs went in 24 picks, which
`pick_debate` renders as "the STRONGEST EVIDENCE FOR WAITING" — while the pace prior
simultaneously drives Jordan Love's survival to 0.53.

**D-3 (MEDIUM, NEW) — the trade_value branch clamps to the bottom of a 2-row list and stamps it
`live_starter_demand`.** `draft_room.py:3149` omits `truncated_out=` where the points branch at
`:3111` passes it. Measured: `replacement_levels(trade_value, 1210 rows) -> {'LB': 0.0}
TRUNCATED={'LB'}`, LB demand rank 8 against **2 priced rows**. Board rows carry `bpa 0.0,
universal_value 0.0, replacement_basis live_starter_demand`. The constant's comment says the
clamp "binds at NO position in either a 1QB or an IDP league"; **it binds on the owner's own
league**, on the branch the fix never reached, failing toward the strongest claim.

**D-4 (MEDIUM-HIGH, NEW) — the QB floor and the shared-slot alternative compose into a live
−17.99, and DL/DB are docked on an EMPTY roster.** SUPER_FLEX's phantom is
`max(level over QB/RB/WR/TE)` = WR 225.49 against a cliff-anchored QB level 207.5 → −17.99 for a
roster holding one QB. Measured at 3.01: **246 of 796 priced rows have TAV < UV**; all 30 priced
QBs −17.99 (Love UV 109.86 → TAV 92.72, below Lamb 102.27 → 110.65); **all 130 DB −28.28 and all
86 DL −32.87 on an empty roster.** Contradicts three docstrings including
"TAV can never fall below UV … structurally impossible". `test_216_displacement`'s empty-roster
test pins it on a roster with a dedicated TE slot and no `slot_alternatives` — again the one
shape where it cannot fail. Knock-on: `denial_component` dead for QB/DB/DL; `block_opportunity`
unreachable for QB/TE/K/IDP by construction.

**D-5 (HIGH) — the `need_bonus` test, mutation-proven.** Wrapped `compute_draft_board` to set
`need_bonus = 999.0` and `final_score = universal_value + 999.0` on every row: **"MUTANT
SURVIVED"**.

**D-6 (MEDIUM, NEW) — thirteen test modules including the certification battery run on the
fixture the repo declares non-production.** `test_cdme_certification.py`'s docstring says "All
tests run against REAL committed-baseline data … never a synthetic fixture", while it and twelve
others build from `_build_pool_players_db` (4 positions, no `injury_status`, no `years_exp`) via
`build_mock_league` **with no `base_scoring`** — the one-key dict `#213` calls "a league in which
quarterbacks score nothing". On that universe every priced row has `proj_3yr` (D-1 invisible),
there are no IDP rows (D-4 invisible), ~0 unpriced rows (D-2 invisible), and `risk_adj` is 0
everywhere. **This is why the suite cannot see most of this wave.**

**D-7 (MEDIUM, NEW) — `CDME_CONTRACTS.md` §1–§3, banner-marked "the live contracts … cited as
authority", is false in four places.** "bpa-anchored 0–100-ish scale, linearly rescaled" (the
rescale is the identity); "Valid domain −9.12 to 97.90" (measured **−319 to +220**);
"`universal_value` … never `None` on a well-formed board … its absence is a schema violation"
(**None on 1,208 of 2,028 rows, 60%, by design since `#193`**); the composition list omits
`forfeit_component`, weight 10.

**D-8/D-9 (LOW)** — multi-eligible bucket divergence (1 of 178); `feasibility_first` IR fallback;
`remaining_starter_demand` treats `roster_id=None` as a phantom 13th team and raises on the whole
board; `need_bonus` up to 8.38 on unpriced rows.

## Null results (both passes)

`lineup_optimizer` in full; `replacement_levels` domain and tolerance; `_derive_points_and_source`
precedence and the 17× guard; the availability haircut's self-limiting form; absence
normalisation at the board edge (0 priced rows without `replacement_basis`, `confidence` None on
all 1,208 unpriced); `near_tie_flags` / `decision_regime` three-state; identity resolution's
rejection rules; `assertion_floors --check` clean on 172 modules; battery ruler consistency
(`#204`) holds.
