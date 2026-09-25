# `#35` — the two Fable passes, my own measurement, and what actually changed

Written after both derivation passes handed back and after the floor finding below. The arms that
grade C on realized outcomes were still running when this was written; the reading for them is
pre-registered in `PREREGISTRATION_C.md` and is not revised here.

---

## 1. The finding that reshapes the problem: C files a UNIVERSAL correction in a TEAM column

`DESIGN_35_CAPS_REDERIVATION.md` decomposes the lift C introduces:

    adj = [ L − min over reachable s of capped alt(s) ]  +  [ that min − displaced ]
          \_____________ >= 0, roster-INDEPENDENT ____/     \___ <= 0, the roster's own ___/

The first bracket is the pre-draft anchor's **staleness**, `stale(p) = max(0, L(p) − b(p))`. It is
the same number on every seat's board. The second is the real roster deduction and keeps its sign.

So the substantive claim the shipped design makes — *roster context never lifts a single-position
candidate* — **survives C**. What fails is the registered form of it, `displacement_adj <= 0`,
because C makes the term carry two things and one of them is not about the roster at all.

That is not a technicality. `rival_premium` is `TAV − UV`, and the denial ramp reads it as *how
much more this rival's ROSTER makes him worth*. Under C that quantity becomes "roster fit plus
however much of the pool's staleness this roster's openness exposes" — measured at pick 164, every
receiver on seat 5's board carries **18.45 of anchor correction with nothing to do with seat 5**.

**The exemption is refuted, and there is no constant to reach for.** `TEAM_SPECIFIC_CAPS` says the
fourth term is "non-positive by construction … so it cannot raise the sum these caps bound".
Today that is false only for multi-eligible rows — a population that is EMPTY in this format.
Under C it is false for **8,500 rows across 56 of 156 board states, every receiver from round 10
on**. And the lift's bound is `stale(p)`, a board-state quantity with **no supremum** (43.25 at
round 14 here; the docstring's own 26-round measurement gives 142.68 for tight ends at the last
pick). `NECESSITY_DENIAL_SATURATION = sum(TEAM_SPECIFIC_CAPS) = 24.0` is a constant. **A constant
cannot bound a quantity with no constant bound, and `#56` forbids choosing one.** Measured
consequence of leaving the constants alone: 295 rows clipped at an identical 20.0 — the flat spot
`#144` was closed to remove — and 2,238 rows past one term's cap.

### And the same prices are available in the right column

Cap **`bpa`'s anchor** with the same quantity, `L'(p) = min(L(p), b(p))`, and keep C's slot
alternatives. Then `bpa' = bpa + stale(p)` and `adj' = adj − stale(p)`, so
`team_acquisition_value` is **algebraically unchanged** — the level cancels between the two terms.
Measured: `max |TAV(variant) − TAV(C)| = 0.00` over all 388 priced rows at pick 164. And because
every slot admitting `p` still prices at or above `L'(p)`, the shipped derivation of `<= 0` holds
**verbatim**: single-position rows with a positive adjustment go 144 → **0**, and the premium goes
back inside the caps (max −10.13, rows over 24.0: zero).

So C and the anchor-capped variant **draft identically in balanced mode** and differ only in what
`universal_value` says. Its cost is real and is not hidden: `universal_value` moves by `stale(p)`
at a drained position — the best remaining receiver's `bpa` becomes exactly 0.00 — and **upside
mode, which scores on `bpa` alone, changes under the variant and does not under C**.

That last line is why my arms measure C and not the variant: the format's last rounds are upside
mode, so the two are identical up to the switch and diverge after it.

### Three formulations converge

`bpa` at a drained position going to 0.00 is **formulation B's behaviour** ("prices DEF3+/QB4/TE5
at zero") reached from the opposite direction, and it is the answer to the owner's own question —
*what is the replacement unit for a bench player's value?* The best player actually still
available, not a pre-draft rank. E (raw projection) was rejected, A (a count bound) is shipped, and
B and C turn out to be one mechanism seen from two ends: **the pre-draft anchor is stale, and
`bpa` should stop using it once the pool has drained past it.** That is `#35`'s real shape.

---

## 2. What I found that the derivation could not: C reverts `#30`

The derivation lists this as undetermined, because its capture carries no weekly lines
(`weekly_weeks: 0`) and so cannot exercise the streaming branch:

> under C a slot at a floored position could be capped below its floor and lift a single-position
> probe whose level is a floor, not an anchor.

My instrument runs with `--streaming`, so it can. **Measured, 2024, `12T_ppr_K_DEF`, on the
OPENING board before a single pick:**

| position | `#30` floor | best remaining | under C |
|---|---:|---:|---|
| DEF | 146.05 | 121.49 | capped to 121.49 — **24.56 of `#30` gone** |
| K | 164.50 | 159.88 | capped to 159.88 — 4.62 gone |

Not late in the draft. **Pick one, and every pick after it.** C as specified silently reverts `#30`
for exactly the two positions `#30` was derived for, and `#30` was worth +328 on 2024 and +85 on
2023.

### The exemption is DERIVED, not chosen

C's premise is *the pool only drains, so no free player can be worth more than the best one
undrafted now*. A `#30` streaming floor is **not a claim about a player**: it is the season sum of
each week's best wire option, and it exceeds every individual's season projection **on purpose**,
because a manager streams. So C's premise is false wherever the level is a floor, by `#30`'s own
derivation — and capping there corrects nothing. It reverts.

`replacement_levels` applies a floor by ASSIGNMENT and raise-only, so `level == floor` identifies a
floor-set level **exactly**, with no second model of the engine's precedence (`#126`). Verified
exact and narrow: the exemption restores K and DEF to their floors and moves **nothing else**.

**Consequence for the pre-registered reading.** The `capped` arm measures C-as-specified, which is
C *and* a partial `#30` revert. A negative result there cannot be attributed to C. So
`capped_floor_exempt` is the arm that isolates C, and the `capped` arm's role is now to say how
much of any loss is the `#30` revert. Both are reported; neither substitutes for the other.

Not extended to `startable_floors` (superflex QB): that branch selects a RANK rather than assigning
the floor's value, so equality does not identify it. This format carries no SUPER_FLEX slot, so the
case is not exercised here — it is `#34`'s ground, and see below.

---

## 3. `#34` is not a new finding — it is `#168`, already pinned

`DESIGN_34_UNPRICED_SUPERFLEX_QB.md`: **(c) correct in the draft loop, a hazard at consumer
boundaries** — and a duplicate. The state is on the register as `#168`, sharpened, and pinned by
`test_qb_pricing_cliff.py` against `evidence/take_model/unpriced_block_composition.json` ("42 → 0
priced QBs by round 12 of 30" on the real superflex draft), with the design question deferred to
`#50`. Verified: both files exist and the test's own docstring says so. **`#34` closes as a
duplicate of `#168`; it does not block v2 on its own account.**

My provisional mechanism was right at all three lines, and it was understated in one way and
overstated in another:

* **Understated.** The floor is derived from the **vendor** projection column (0.5 × QB12 = 163.5
  ppr) but compared against the **league-scored Sleeper season sum** on the board. 29 QBs clear it
  on one scale, 32 on the other. The stability basin was derived on one ruler and cashed on
  another. That is a real defect of the `#166`/`#174` class and it is new.
* **Overstated.** "102 unpriced QBs" is two populations. **92 of 134** QB rows are
  `no_priceable_input` from pick 1 on **every** arm — nothing to do with the floor. The floor
  decline de-prices about **10**. My framing charged the floor with the vendor's coverage gap.

And it is **not** the K/DEF pathology in different clothes, on a distinction I had not drawn: the
K/DEF rows projected **above** their own pre-draft level and were sorted below everything, an
inversion the data contradicted. The floor-declined QBs project **below** the floor, and under an
anchor fill would carry `bpa` ≈ −44 to −80 — the same band as the round-15 anchor-priced WR/RB.
Declining is a defensible **stated limit**, not a defect. But it does refuse a comparison the data
could support, in the one format where QB is scarcest, and that is `#50`'s question.

### Three consumer-boundary gaps, one of which is a reachable crash

1. **`draft_counterfactual.regret_vs_bpa` is unguarded.** `round(engine_tav − bpa_tav, 3)` with
   both fields typed non-Optional `float`. An unpriced engine pick makes `engine_tav` absent and
   the subtraction raises `TypeError`. **This is reachable by the exact trajectory `#34` came
   from** — the noise arm that took Haener at 15.08 and Bennett at 15.10.
2. **`absence_kind` is never stamped `ABSENCE_NO_REPLACEMENT`.** The token and its label exist;
   only `no_input` is ever written. So a floor-declined QB reaches `pick_debate` carrying no *why*.
   `#112`'s iff-invariant test passes only because its population is an OPENING board.
3. **`roster_diagnostics.replacement_level_surplus` prices superflex QB off demand rank with no
   floor** — a second home for a level the board prices off the cliff (`#126`).

`#187` itself is honoured on every value path: NaN → None → JSON null, with no `0.0` coalescing.

---

## 4. Where this leaves v2

| item | state |
|---|---|
| `#35` — is C worth its cost | arms running; reading pre-registered |
| `#35` — is C ADMISSIBLE as specified | **no.** It inverts a registered invariant, refutes the caps' exemption, and needs a constant that cannot be derived |
| `#35` — is there an admissible shape | **yes, one:** cap `bpa`'s anchor, identical prices in balanced mode, invariant and caps intact, with a real cost in `universal_value` and upside mode |
| `#35` — C reverts `#30` | **measured, from pick one.** The exemption is derived and verified |
| `#34` | **closes as a duplicate of `#168`**, plus one new scale mismatch and three consumer gaps |
| `#34` gap 1 | a reachable `TypeError` on a trajectory that has already been produced |

Nothing here is implemented. Every one of these is a valuation or contract ruling for the owner
(`#184`) except gap 1, which is an absence-handling bug of the `#187` class.
