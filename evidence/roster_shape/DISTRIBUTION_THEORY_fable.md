# What a correct roster distribution is, as a function of the league — a derivation, and where it runs out

*Fable, 2026-09-09. Read-only pass over the 98 wave drafts (1,128 final rosters: 1,030 control seats,
49 engine SELF, 49 engine SHARED) plus board-only rebuilds of all 33 formats from the repo root.
Scripts and raw output: scratchpad `shape_theory.py`, `tiers.py`, `deadweight.py`. Nothing in
source was touched.*

## The verdict first

1. **The band's supply side is right and is not the problem.** The league-optimal fielded load it
   starts from matches a pool-only rebuild (`fielded_flex_occupancy`, never looks at a drafter)
   within ~0.3 bodies at every position in every format. The one defect on that side is that
   `derived_band` reads the load off the DRAFTED rosters — the circularity `fielded_flex_occupancy`'s
   own docstring forbids — and it drifts by up to 0.5 bodies where the control hoards (12T_ppr_SF
   RB 4.17 drafted vs 3.89 pool; WR 5.62 vs 6.11). Same quantity, second home; read the board's.

2. **The band's allocation rule is an assumption, not a derivation, and it is the part that
   disagrees with everything.** `target = R × share` allocates the bench so every position is
   rostered to the SAME TIER DEPTH (R/S tiers deep — 1.75 in the 14-slot formats). That is
   correct only if a backup is worth the same at every position and is needed in proportion to
   the starters there. Neither holds; the arithmetic in §3 shows what does.

3. **Your revealed-distribution analysis is measuring the control's rule, and only that.** The
   control's bench phase is "best raw season projection, position-blind." The signature of that
   rule is that it drives the end-of-draft free agent to the SAME per-game level at every
   position — measured: 12T_ppr QB 7.59 / RB 7.42 / WR 7.63 / TE 7.31 pts/gm — so its bench
   composition is nothing but the count of players per position projecting above one common
   number. That number is why it holds 3 QBs in a 1-QB league (QB13-30 all clear it) and 2-5
   tight ends. The distribution supports one claim — the fielded load — and that claim the pool
   already makes without any drafter. It cannot support anything about insurance or ceilings.
   Its RB-heaviness is not insurance; it is RB25-48 projecting above the common level.

4. **By every quantity the engine holds, WR 10 is not wrong.** Priced against the band-consistent
   free alternative, engine SHARED rosters carry a mean 0.16 pts/gm of "dead weight" (bodies
   projecting below the free agent at their position); the 8T/10T/12T superflex WR-9/10 rosters
   carry 0.0-1.2. The control carries 2.26, almost all of it QB. The WR surplus is wrong only
   under a quantity the engine does not have: the probability those bodies are ever fielded.
   §3 shows that its DIRECTION is derivable without that quantity and its MAGNITUDE is not.

5. **The ceiling's location is endogenous to the room; its hardness is not.** What you can
   derive from the league alone is how much it COSTS to exceed the self-consistent boundary at
   each position, and that cost differs by an order of magnitude: QB (1QB) 12-15 pts/gm per
   extra body, TE 3-4, RB 1.2-2.4, WR 0.9-1.5. Cliff positions have hard ceilings; plateau
   positions have soft ones. Two hard ceilings fall out with no constant at all (§4).

6. **Both of the owner's strategic claims terminate in one missing input** — the shape of the
   per-player outcome distribution (floor for the TE claim, right tail for the RB claim) — and
   the insurance derivation terminates in a second one, the per-position absence rate. §6 names
   both precisely and what supplies them. Nothing here proposes a constant.

---

## 1. The population, and what it can and cannot say

`run_roster_proof.control_pick` is two rules in sequence: best projection at a position the
roster still needs to start, then best projection full stop. Measured across all 1,030 control
rosters the cut between the two lands at pick 8.0-9.0 in every format, so 5-6 of every control
roster's 14-15 bodies come from a rule that never looks at a slot.

**What that rule does, mechanically.** A position-blind best-projection bench equalises the
marginal raw projection across positions — the last body taken at each position is worth the
same, so the first body LEFT at each position is worth the same. Measured end-of-draft free agent,
per game:

| format | QB | RB | WR | TE |
|---|---|---|---|---|
| 12T_ppr | 7.59 | 7.42 | 7.63 | 7.31 |
| 12T_ppr_SF | 5.60 | 6.19 | 6.77 | 6.13 |
| 10T_standard | 5.60 | 6.49 | 7.01 | 7.02 |
| 14T_half_ppr | (QB pool exhausted) | 3.5 | 3.9 | 6.6 |

So the control's per-position count is `#{players at p projecting above W*} / T`, with W* set
by total roster capacity. Its bench-phase picks confirm it: QB is 29-56% of control bench picks
in 1-QB leagues (55% in 8-team, where QB9-30 all clear W*), 8-24% in superflex where the QB
pool is drained by starters; TE is 0-1% in 8-team and 14-25% at 12-14 teams. None of that is
a preference; all of it is where the projection curves cross one horizontal line.

**What it can support.** The fielded load. Every control roster covers its starters first, with
the real optimizer, so the league-wide fielded load on final rosters is the one thing about the
population that is not the bench rule — and it agrees with the pool-only solve to within 0.3.

**What it cannot support.** Any claim about depth. "RB ≥ 4 in 50.9%" is the control taking RB25-48
over WR49+ because standard/half-PPR projections rank them that way; "TE-first 0%" is the control
never needing to; "TE ≥ 4 in 13.2%" is TE13-25 clearing W* in PPR. The revealed p50/p90/max per
slot are not managers, and the owner is right that the control sits below his room's floor —
2.26 pts/gm of its roster is below the free agent at that position, versus 0.06-0.16 for the
engine. Population consensus here is a control in the literal sense, and the vault's warning
applies with extra force: this population is one rule.

A confound you asked about: the wave-exposure effect (seat 1/12 turn-adjacent, 4/8 middle) does
not touch anything above, because every number here pools all seats. It does touch the per-seat
rows in `waves_all.txt` — seat 1 vs seat 4 there is seat AND exposure — but nothing in this memo
rests on a seat-to-seat difference.

---

## 2. Question 1 — the dimensions

The data's first limit: 29 of 33 formats share ONE slot template (QB/RB/RB/WR/WR/TE/FLEX/FLEX,
±SUPER_FLEX, 6 BN). "Dedicated slots per position" varies only in 4WR_TE_PREMIUM, the two IDP
formats and the owner's league. So team count, scoring and superflex are measured on a grid;
slot layout is measured at four points.

What actually moves the fielded load per team (pool-optimal, string 1):

| dimension | effect on fielded load L_p | size |
|---|---|---|
| **Scoring** (standard → PPR, 12T) | RB 2.75 → 2.33, WR 3.25 → 3.67 | ~0.4 body moves RB→WR through the flexes |
| **Team count** (8 → 14, PPR) | RB 2.75 → 2.29, WR 3.25 → 3.71 | ~0.45 body RB→WR: the RB curve is steeper, so deeper leagues run out of flex-worthy RBs first |
| **Superflex** | QB 1 → 2, everything else unchanged | exactly +1; QB wins 100% of SUPER_FLEX at every size |
| **TE slot count** | 1 slot: TE = 1.000 in 33/33 formats — TE13+ wins ZERO first-string flexes anywhere; 0 slots (owner): 1.5; 2 slots: 2.0; TE-premium with 1 slot: 1.5 | discrete, rulebook-driven |
| **Flex count** | sets the fractional parts above; each FLEX goes RB/WR only at string 1 | |
| **Bench depth** | does not touch L; sets how many insurance TIERS exist (§3) | |
| **IDP slots** | remove RB/WR flex capacity (HEAVY_IDP: one FLEX, L_RB 2.17 / L_WR 2.83) | |
| **Dynasty vs redraft, mode** | inert on L and on the tiers (identical numbers) | |

Two things the table settles about the demoted ordering rule. `WR ≥ RB` in the fielded load is
a consequence of two facts — dedicated slots are 2/2 and WR wins the flexes — and it inverts
exactly where the second fact inverts: 8T_standard (L_RB 3.25 > L_WR 2.75) and ties at
10T_standard / 8T_half. The owner's remark that "in deeper leagues there's no reason WR > RB has
to hold" is true of the rule's status and false of the measured direction: WR's share GROWS with
depth (14T PPR 3.71 vs 8T 3.25) because RB decays faster. Where deeper leagues do favour RB is
the bench, and for a different reason (§3: the free RB is worst there — 2.4-3.9 pts/gm at 14
teams).

And `RB > TE` is L_RB > L_TE, which holds in every format including the owner's (2.17 vs 1.5);
so as an observable it is just "how many of each the league fields", reported directly.

---

## 3. Question 2 — the derivation

A roster body at position p is one of three things, and the three have different derivations:

    n_p  =  F_p  +  I_p  +  U_p
            fielded   insurance   speculation

**F_p — exact.** The per-team optimal fielded load, `starter_slot_counts(roster_positions,
fielded_flex_occupancy(pool), T)`. Rulebook plus projection curve, no drafter. It is the band's
supply side. A team can field up to `ceil(F_p)` at p (the fractional part is the flex the
position sometimes wins), and at most `maxfield_p` (every slot admitting p) in any world.

**I_p — needs one input the engine lacks, but its ordering does not.** The k-th body at p beyond
`ceil(F_p)` is fielded only when enough higher-ranked bodies are absent. Under the one-absence
model `depth_exposure` already commits to ("any one starter could become unavailable — a uniform,
stated assumption"), with per-body absence rate `a`:

    E[insurance value of the (F_p + j)-th body]
      ≈ P(at least j of the F_p starters at p are out) × (its projection − the free alternative at p)
      ≈ C(F_p, j) · a^j · VOW_p(j)

The second factor is what the projection curve supplies. Against the band-consistent free
alternative (the (T·target_p + 1)-th player at p — the boundary the band itself defines, so it
is room-independent), the worst body of each per-team tier is worth, in pts/gm:

| 12T_ppr | tier 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| QB (F=1) | +1.7 | −0.6 | **−15.6** | — | | | | |
| RB (F=2.33) | +10.5 | +7.7 | **+4.0** | **+0.5** | −1.9 | −3.0 | −4.0 | −4.8 |
| WR (F=3.67) | +11.0 | +8.4 | +6.6 | +5.5 | **+3.2** | **+1.0** | −0.3 | −1.8 |
| TE (F=1) | +1.9 | **−0.6** | −4.2 | −5.7 | −6.9 | −7.7 | | |

| OWNER_3RR_SF_noTE | tier 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| QB (F=2) | +17.6 | +15.3 | +0.2 | (pool ends at ~40) | |
| RB (F=2.17) | +7.5 | +4.7 | **+1.0** | −2.5 | −4.9 |
| WR (F=3.33) | +8.8 | +6.2 | +4.4 | **+3.3** | **+1.0** |
| TE (F=1.5) | +6.0 | **+2.8** | −1.3 | −3.1 | −4.5 |

(Bold = the first bench tier(s) at that position. The head of tier k is roughly the tail of tier
k−1, so a tier has SOME positive bodies while the previous tail is positive.)

Now the arithmetic the band does not do. First bench body at each position, 12T_ppr, one
absence, `a` common:

    QB2:  1    × a × (+1.7 → −0.6)   ≈ 0.5a     needed when the one QB is out
    TE2:  1    × a × (+1.9 → −0.6)   ≈ 0.7a
    RB3:  2.33 × a × (+7.7 → +4.0)   ≈ 13.6a    any of 2.33 RB starters out
    WR5:  3.67 × a × (+5.5 → +3.2)   ≈ 16.0a
    WR6:  C(3.67,2) a² × (+1.0)      ≈ 4.9a²    needs TWO WR starters out
    WR7:  C(3.67,3) a³ × (−0.3)      < 0        below the free agent even when needed
    RB4:  C(2.33,2) a² × (+0.5)      ≈ 0.8a²

`a` cancels within a tier, so the ORDER of first-tier bodies is derived with no constant:
WR5 ≈ RB3 ≫ TE2 ≈ QB2. Across tiers each level carries one more factor of `a < 1`, so any
tier-2 body ranks below any positive tier-1 body FOR EVERY `a` in (0,1) — the direction of the
engine's WR surplus (WR7-10 at absence-order 3-6, over RB3-4 at absence-order 1) is wrong under
every absence rate; only its size depends on `a`. That is exactly the split you asked for: the
band's target is not what to fix; the engine's bench ORDER is, and the ordering half is
derivable today. The B1 "coverage" arm in `run_216_bench_probe.choose` is this quantity
(starters whose single absence the candidate covers, re-solved with the optimizer); I could
find no recorded verdict for it under `evidence/roster_shape/shared_slot/bench/`, so I am
naming it as built-but-unmeasured rather than as new.

What the band's proportional rule assumes, stated: `R × share_p` is the allocation where
insurance is worth the same per body at every position and is needed in proportion to F_p — and
it assumes it at every tier. The one-absence arithmetic agrees with it about the first tier
(need ∝ F_p) and disagrees about everything past it (need ∝ a^j, not F_p). It also puts the
band's QB 3.33 in 14-team superflex past the END of the QB pool: the band-consistent free QB
there is rank 48 in a pool of ~40 (`W = None`). That cell is not `SUPER_FLEX_QB_SHARE` — the
measured branch never consults it — it is proportional allocation asking for bodies that do not
exist. A ceiling of `pool_p / T` closes it with no constant.

**Where the body-aware differentiation belongs, checked against the rulings.** The severity
half of insurance is `lineup_optimizer.depth_exposure.worst_loss` — what one backup would have
to cover on THIS roster — and it self-limits with depth exactly as the arithmetic above does.
What it lacks is the rate; the module says so in its own docstring. The reverted
depth_exposure→necessity wiring fell under a level-versus-rate ruling, and this is consistent
with that ruling rather than against it: the missing quantity IS the rate. With `a_p` supplied,
`P(needed) × worst_loss` is an expected-points term in the board's own units and the 12.0 cap —
which exists because the term has no probability to bound it — would no longer be doing the
bounding. I am not proposing to lift the cap; I am saying what the cap is standing in for.
`need_bonus` (positional gate), the additive-on-one-anchor rule, `pick_necessity` reading
`positional_forfeit`, and the observable-only status of `horizon_floor`/`waiting_cost` are all
untouched by anything here.

**U_p — not derivable from anything on disk.** See §6.

---

## 4. Question 3 — the ceiling

The owner's intuition is right that the ceiling is the discriminating fact, and the data say
why: the median control roster and the median engine roster differ by one body per position,
but the COST of the last body differs by 10× between positions.

**Location.** The free alternative at p in-season is whatever the ROOM leaves on waivers, and the
room's depth is not a league parameter. The only room-independent reference is the
self-consistent boundary — every position rostered to the same tier depth, i.e. the band — and
against it the sign of tier-k value is fixed by construction (k > target ⇒ ≤ 0). So a count
ceiling "derived" from the sign is the band again, circular. What is NOT circular is the slope.

**Hardness — derived, per league, no constant.** Points/gm lost per further league-tier past the
boundary (`tiers.json`, slope_out):

| format | QB | RB | WR | TE |
|---|---|---|---|---|
| 12T_ppr | 12.0 | 1.9 | 1.3 | 4.0 |
| 14T_ppr | 14.9 | 1.2 | 1.1 | 3.8 |
| 8T_ppr | 1.2 | 2.9 | 1.6 | 1.9 |
| 4WR_TE_PREMIUM | 5.7 | 1.9 | 1.5 | 1.7 |
| OWNER (no TE slot, SF) | pool ends | 3.5 | 1.4 | 2.1 |

An extra QB in a 12-team 1-QB league is 12 pts/gm below the free QB; an extra WR is 1.3 below
the free WR. The ceiling is hard where the curve cliffs and soft where it plateaus, and that is
why the same "+1 over band" reading in `waves_all.txt` is a real defect at QB/TE and noise at WR.
This also explains the control's QB hoard being its dominant dead weight (1.9 of 2.26 pts/gm)
while its RB/WR excess costs 0.01/0.06.

**Two hard ceilings that need nothing but the rulebook.** At a position where the team fields
exactly one body (`F_p = 1`: QB in 1-QB, TE with one TE slot), a THIRD body can never be promoted
by an absence at his own position — there is only one starter to lose. He is fielded only by
winning a flex, and against the free alternative the third tier is −4 (TE) and −15 (QB) pts/gm.
So `n_QB ≤ 2` (1-QB) and `n_TE ≤ 2` (one TE slot) are structural, not fitted, and hold in all
33 formats' curves. In superflex the QB ceiling is 3 and soft (tier 3 = +2.0 at 12 teams, and
the pool ends at ~40, so `pool/T` binds at 14). With two TE slots or none (owner's league,
4WR_TEP) TE is 3, soft (tier 3 = +0.7 / −1.3).

**What "no more than can ever be fielded, plus insurance proportional to how thin the pool is"
becomes when both halves are derived:**

    ceiling_p  =  ceil(F_p)  +  (number of tiers j with C(F_p, j) · a^j · VOW_p(j) > opportunity cost)
    bounded by  pool_p / T

The first term and VOW_p(j) come from the league; the tier count needs `a`. Without `a` you get
the two hard ceilings above and the hardness table; you do not get a count for RB and WR, and
you should not pretend to.

**A better instrument than a count.** Per roster, sum over bodies of `max(0, W_p − proj)/17`
where `W_p` is the band-consistent free alternative — "points per game this roster carries
below what waivers offer." It is exact where the tier table is an approximation (a WR-10 roster
holding WR5/15/30/…/74 has zero dead weight; the tier table calls it three over), it is
zero for both a WR-heavy and an RB-heavy roster that hold real bodies (the vault's "strategy
distribution" survives it), and it needs no constant. Measured: control mean 2.26, p90 5.42,
max 24.6 (a 5-QB roster); engine SELF 0.06; engine SHARED 0.16, max 3.18 (14T_ppr_SF seat 1,
a second TE below the free TE). It reports; it does not select — `horizon_floor` is observable
by ruling and this is the same kind of number.

---

## 5. Question 4 — slope, and whether it is read anywhere

Where the engine reads a LEVEL: `replacement_levels` (the value at demand rank; selection
authority through `bpa`). Where it reads a SLOPE:

- `horizon_replacement.sensitivity` — drop across ±6 ranks around the end-of-draft floor.
  Observable only, by ruling.
- `_bench_appetite_rates` — `1 − value[2·demand] / value[demand]`, the retention across the
  tier past starter demand. Feeds `positional_bench_appetite` → `estimated_bench_demand`, a
  behavioural prior for the debate layer, forbidden from valuation by design and by test. Two
  defects worth naming: its demand is `starter_slot_counts(roster_positions)` with NO occupancy —
  the even split the module elsewhere calls measured-false — so its slope is read at the wrong
  rank for every flex-eligible position (#126, the board reads one occupancy and this reads
  another); and its own docstring records it "known wrong at the tail" for superflex QB.
- `depth_exposure.worst_loss` — a roster-relative level gap (starter minus the body the solver
  promotes), which is the integral of the slope from the roster's own depth to its starter. It is
  the severity half of insurance and the only slope-shaped quantity with selection authority
  (via `team_acquisition_value`, capped 12.0).

So the vault's #07 ("should be an emergent read off replacement-level slope; replacement_levels
and positional_cliff are structurally already this") is true of the observables and false of
selection: the anchor that decides picks is a level, and after today's shared alternative it is
ONE common level for every flex-eligible candidate. Positional differentiation now comes only
from the two capped body-aware terms, which is why the deepest high-projection tail (WR) wins
the bench.

**Is insurance a slope quantity?** Yes, but as the shape of the curve BETWEEN the roster's last
body and the free alternative, not as a local derivative. `VOW_p(j)` in §3 is that integral. The
RB story the owner tells is visible in it: RB has the steepest curve into the boundary in every
12-14 team format (slope_in 3.5-4.4 vs WR 1.4-2.0) and the worst free agent in deep standard
leagues (2.4-3.9 pts/gm at 14 teams), so an RB3 is worth 4-8 pts/gm over waivers in the week he
plays while a WR5 is worth 2-3. That is what "insurance" means in points, and the engine can
compute it today. What it cannot compute is how often that week comes.

---

## 6. Question 5 — what cannot be derived from what exists

**Gap 1 — the per-position absence rate `a_p`.** Needed to size (not order) insurance and to
count tiers in the ceiling. Two components. *Byes* are deterministic and the engine already has
the home (`lineup_optimizer.bye_collision`, fed by `data_merger.bye_week_by_team`) — but the
battery fixture carries `bye_week` on 0 of 6,595 players, so every wave draft was priced in a
world with no byes. That is the cheapest gap on this list: the input exists in production and
is absent from the measurement universe. *Injury absence* needs a historical games-missed rate
by position (or per player); `risk_adj` is current status, not a rate, and the docstring in
`depth_exposure` already refuses to invent one. The input: per-position expected games missed
per 17, from prior seasons.

**Gap 2 — the shape of the per-player outcome distribution.** You identified this and it is the
important one. The owner has now made two independent claims that both need it:

- "TE is a pressure release valve — decent FLOORS": a claim about the LEFT side of the weekly
  distribution. In point estimates the release-valve claim is only half-visible: the
  second-string pool solve does send 6-8 of 24 flexes to TE in every 12-14 team format (TE13-19
  beat WR45-56 by 0.4-1.3 pts/gm on season totals), but a 1-pt/gm edge on the mean cannot
  distinguish a 9-point TE scoring 7/9/11 from a 9-point WR scoring 1/4/22. The claim is that
  the TE is the better BENCH body because his bad week is less bad; nothing on disk can test it.
- "RB pop-offs are rarer, so hold upside/handcuffs/rookie bets in RB": a claim about the RIGHT
  tail of the SEASON distribution — a handcuff worth 4 pts/gm in expectation is really 15% of a
  16-pt RB1 season and 85% of nothing, and a point estimate of 4 prices those identically to a
  steady WR5. This is the `U_p` term in §3 and it is not derivable at all without the tail.

What supplies it: per-player weekly quantiles (p10/p50/p90, or μ and σ) for the floor claim,
and a per-player probability-weighted season scenario (or at minimum a "breakout probability"
field) for the tail claim. Draft Sharks–style projection vendors publish floor/ceiling ranges;
week-to-week variance by position can also be estimated from prior-season actuals the merger
may already hold. Either way it is a NEW COLUMN, not a re-weighting, and the absence contract
applies: until it exists, floor and tail are `None` with a basis, and any term that would read
them contributes nothing rather than 0.0.

Once it exists the two questions above change shape: the ceiling becomes "bodies beyond which
the expected-max-over-absences gain is below the free alternative", and insurance allocation
becomes `P(needed) × E[max(0, own − free)]` — the same formula with a distribution where §3
has a point.

**Gap 3 — the room's in-season rostering depth.** The actual free alternative is what eleven
real managers leave on waivers. Observable in-season through `horizon_replacement`; not a draft-
time league parameter. Any ceiling stated as a count is conditional on the room's depth, which
is why §4 gives hardness rather than counts.

**Gap 4 — a roster-shape ruler that sees the bench.** `lineup_points` (the wave ruler) scores
starters only, so a bench of ten receivers and a bench of RB insurance score identically. Every
"the change cost/gained X points" claim in the waves is about starters. A bench-visible ruler
is the absence-simulated season: `lineup_points` re-solved per week with byes (available in
production now) and injuries (Gap 1) applied. That is the ruler on which any shape criterion
should be measured before it is wired.

**Not a gap, but a demotion the data support:** `WR ≥ RB > TE` and `WR + TE ≥ RB` are the
fielded load's ordering by another name. Reporting `F_p` reports them; the rule adds nothing.

---

## 7. What I would do with the band, concretely, and what I would not

- Keep `target_total`; compute its supply side from `fielded_flex_occupancy` (pool) rather than
  from drafted rosters — one home for one quantity, and it removes the only contamination the
  band actually has.
- Report beside it, per position, `slope_out` at the boundary (hardness) and `pool_p / T`
  (existence). Both fall out of `tiers.py`-style arithmetic on the board's own curve.
- Replace the count-breach summary in `summarise.py` with the dead-weight number (§4) and,
  per bench body, its absence order (the smallest number of starters whose removal fields him —
  `run_216_bench_probe.coverage` already solves this). Both are observables. Neither is a gate.
- Do NOT read the control's p50/p90 into anything. Do NOT fit a receiver penalty. Do NOT add a
  tier constant — the tier count is `a_p`'s job and `a_p` is Gap 1.
- When byes reach the fixture, re-run the waves on the absence-simulated ruler (Gap 4) before
  any selection-side change; the +0.57% lineup-points result is a starters-only number and the
  shape question is a bench question.

The honest one-line answer to "is there a better derivation": the band's supply side is already
the right derivation; the correct bench allocation is `P(needed) × value over the free
alternative`, of which the engine has the second factor and the ordering of the first, and lacks
the rate. Everything that looks like a shape defect today — the control's QB hoard, the engine's
WR tail — is that one factor, and no amount of arithmetic on season point estimates will produce
it.
