# The two displacement charges — vocabulary, defined and not wired

**RULING (owner, this session): SPLIT IT — vocabulary first.** `displacement_adj` carries two
corrections with different natures, and the dual classification that blocks #222's last question
(*is it in scope of upside mode's "zero every team-specific term" rule?*) exists because one name
covers both. This document defines the two concepts. **No engine source is changed by it, no
constant is chosen, and no threshold moves.** It is the naming step the ruling asked for; wiring
is a separate, later decision.

---

## What the single term is today

```
displacement_adj = level_pos − displaced        (≤ 0 by construction, never positive)
```

where `displaced` is what the candidate would evict from this roster's own optimal lineup —
`lineup_optimizer.displacement_level`, an exact assignment solve against a roster pre-filled with
one phantom per slot. Each slot's phantom is worth the best free player among the positions that
slot admits (`shared_slot_alternatives`), so a FLEX phantom is `max(level over {RB, WR, TE})`.

**Three regimes, all observed on real boards:**

| `displaced` is | charge | what it means |
|---|---|---|
| **the candidate's own `level_pos`** | **0.00** | a reachable slot's alternative *is* his own position's free player — his dedicated slot is open, or he is the position that defines the flex phantom |
| **another slot's phantom** | `level_pos − phantom` | the slot he would occupy is **SHARED**, and a better-supplied position sets its free alternative |
| **one of my own starters** | `level_pos − my_player` | the slot he would occupy is **TAKEN** by someone of mine the free alternative would not beat |

The probe evicts the **cheapest** thing it can reach, so which regime fires is a property of the
roster, at every board state.

## The two concepts

**1. `shared_slot_adj` — the slot is SHARED.**
The candidate is priced by `bpa` against *his own position's* replacement level, but the slot he
would actually occupy is contested by other positions, whose free alternative is better than his.
The charge is the difference between the two alternatives for **one slot**:

```
shared_slot_adj = level_pos − phantom_reached          (≤ 0)
```

This is #216's "ONE SLOT, ONE ALTERNATIVE" doctrine, already implemented in
`shared_slot_alternatives`, given its own name. Its **magnitude comes from league structure and
the live pool** — which positions a slot admits, and where each position's replacement level
currently sits. It contains no information about *who is on my roster*.

**2. `displacement_adj` — the slot is TAKEN** (the existing name, narrowed to the case it actually
describes).
Beyond the shared-slot charge, the candidate must displace a real player of mine who is better
than that slot's free alternative:

```
displacement_adj = phantom_reached − displaced         (≤ 0)
```

This is irreducibly roster-specific: it names one of my players and its size is that player's
value.

## The decomposition is exact — there is no residual

```
shared_slot_adj + displacement_adj = (level_pos − phantom) + (phantom − displaced)
                                   =  level_pos − displaced
                                   =  today's displacement_adj
```

**Applying both reproduces today's number exactly, at every board state and in every regime.**
Each half is independently non-positive. In the "slot taken" regime the second half is non-zero;
in the "slot shared" regime it is exactly 0.0; in the zero regime both are 0.0. The split is
therefore behaviour-preserving by construction, which is what makes it a vocabulary change rather
than a valuation change.

## Why this resolves the dual classification

The two readings that could not be reconciled were:

- **A — a team-specific term**, so upside mode's rule zeroes it.
- **B — a correction to the universal anchor**, which is the stated reason it alone carries no cap
  (*"only ever removes credit the league anchor gave for a slot the roster cannot offer"*).

Under the split each reading attaches to a different quantity and neither is strained.
`displacement_adj` (narrowed) is **A** — it reads my roster, and a roster-blind mode should drop
it. `shared_slot_adj` is **B** — it retracts credit `bpa` gave for a slot whose alternative is set
by a different position, and that over-credit exists whether or not anyone has drafted.

The caps follow the same seam: `TEAM_SPECIFIC_CAPS` bounds the three roster-preference nudges and
would continue to exclude both of these, for the reason already on the record — neither adds
credit, so neither can flip a gap upward.

## What the ruling does NOT settle, stated plainly

**Which phantom a candidate reaches is roster-conditioned.** `shared_slot_adj`'s *magnitude* is
free of roster information, but *which slot he would occupy* — and therefore which phantom applies
— depends on which of his slots are open or weakly held. A genuinely roster-blind mode cannot
evaluate `shared_slot_adj` exactly; it would need a stated rule for which slot a candidate is
assumed to reach when the roster is unknown.

**That is the next decision, and it is a real one, not a detail.** It is also exactly where the
#229 gap lives (the domain of validity is keyed on the anchor, never the candidate). This document
does not take it.

**And the charge is not a constant.** The levels drain as the draft runs, so `phantom − level_pos`
is recomputed at every board state. Measured on the real rulebook: the tight-end charge is 68.58
at the opening board, 60.03 at pick 100, 89.14 at pick 150; the receiver charge is 0.00 at every
state, because WR's *live* level defines the FLEX phantom at every one of them. Any statement of
the form "the handicap is X points" must name the state.

## What implementing this would touch, named and not done

`draft_room.displacement_adjustments` (returns one dict per position — would return both halves),
`lineup_optimizer.displacement_level` (already computes `displaced` and the phantom set; the split
is a reporting change there, not a solver change), `score_row`'s composition and the emitted column
list, the `team_acquisition_value` identity in the module docstring and `CDME_CONTRACTS` invariant
1, `displacement_basis`'s vocabulary, and the upside branch's layer-identity comment.

**None of that is authorized by this ruling**, which was to name the concepts. The wiring decision
needs the roster-blind question above answered first, or it will hard-code an answer to it by
accident.

## Evidence this rests on

`RESULT_displacement_is_the_counterweight.md` (Fork Q, two live board states),
`RESULT_the_handicap_is_exact.md` (the identity and its 21st-withdrawal correction),
`residual3_raw.json` (the phantom is the evictee on 103 of 144 tight-end observations),
`displacement_neutrality_raw.json` (per-position charges and live levels at picks 100 and 150),
and `CONTRACT_what_upside_mode_is_meant_to_drop.md` (the dual classification, with sources).
