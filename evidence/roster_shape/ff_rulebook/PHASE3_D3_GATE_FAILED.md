# D3 GATE: the derivation proof holds — but it disconfirmed D3's PREMISE. Not implemented.

The owner authorised D3 "subject to the production-state derivation proof above." The proof
ran. It passed on its own terms and then, in the course of passing, falsified the reason for
doing the fix at all. **No engine source has been changed.**

---

## What the gate asked for, and what it found

### 1. state → intervening picks → derived rank → actual player at that rank — WORKS

`generate_pick_order(round_1_order, 26, "snake")` reproduces the recorded draft's roster
sequence on **312 of 312 picks**. From there `find_next_pick_index` → `intervening_roster_ids`
gives a real intervening count per state (6 at pick 105, 22 at picks 157/193/205/241, 14 at
281), and a rank derived from it lands on a real, named player with a real value. Worked at
all six sampled states. Full table in `phase3_D3_derivation_proof.py`'s output.

### 2. Is it accidentally reusing the anchor? — YES, for the rival-model estimator

The check the owner asked for, both arms in one process, toggling only `_fill_omitted_from_anchor`:

| at pick 241 | top-10 priced board rows |
|---|---|
| with the anchor fill | 10 rows, all WR |
| without it | **zero priced rows at all** |

Without the anchor fill the board at pick 241 prices **nothing** — every position is either
floored-and-omitted (QB) or demand-exhausted (RB/WR/TE). So the anchor is not merely an
influence on rival-board ranks, it is the entire reason a late board exists. Any `k` estimated
from `positional_forfeits`' `expected_taken` (which reads opponent boards → `compute_draft_board`
→ `final_score` → `_vor` → the anchor-filled level) is **100% downstream of the quantity we
were trying to escape.** Rejected on exactly the ground the owner named.

Two consequences worth recording:
- `expected_position_pace`, the other existing pace model, returns `None` for RB/WR/TE — it is
  documented only for QB in a superflex league. It cannot supply `k` for the positions at issue.
- The only anchor-free estimator available is the observed positional share of the picks already
  made × the intervening count. That touches no valuation at all. It is also **new machinery**,
  which is what the owner said not to build.

### 3. The architectural fact — `compute_draft_board` never receives `pick_order`

Its parameters are `merger, players_db, picks, my_roster_id, league` plus keywords. `pick_order`
appears in `draft_room.py` exactly once, as a parameter of `simulate_opponent_picks`. Deriving
it inside the board would mean assuming `draft_type`, and this repo has already recorded that
assuming snake where a draft is 3RR is "the single largest possible error in the whole survival
model." So D3 would require threading a new input through the board's signature — larger than
"change the input to `free_alternative`."

That alone would not have stopped the work. What follows did.

---

## THE PREMISE IS FALSE: the level CANCELS

`displacement_adj = replacement_level − displacement_level`, and `bpa = points − replacement_level`.
Same `L` in both. So for a candidate whose reachable slots are all held:

```
bpa + displacement_adj  =  (points − L) + (L − displaced)  =  points − displaced
```

**The level drops out entirely.** This is structural, not a coincidence of scale:
`_scale_vor_to_bpa` is the identity — *"bpa IS vor: real projected points above this position's
replacement level. No reference, no rescale, no clip"* (the #74–76 repair removed the rescaling).

Measured on the B1 ladder, every column read off the production board row:

| held | pick | level | basis | proj_pts | bpa | disp_adj | bpa+adj+need+elig+depth |
|---|---|---|---|---|---|---|---|
| 2 | 109 | 149.17 | live | 195.60 | 46.43 | −51.73 | **−5.25** |
| 3 | 132 | 144.98 | live | 168.72 | 23.74 | −55.92 | **−32.18** |
| 4 | 156 | 108.98 | live | 149.17 | 40.19 | −91.92 | **−50.29** |
| 5 | 180 | 81.49 | live | 91.18 | 9.69 | −119.41 | **−108.28** |
| 6 | 181 | 80.53 | live | 81.49 | 0.96 | −120.37 | **−117.97** |
| 7 | 205 | **149.17** | **anchor** | 62.81 | **−86.36** | **−51.73** | **−136.65** |
| 8 | 229 | **149.17** | **anchor** | 43.02 | **−106.15** | **−51.73** | **−156.44** |

`bpa` equals `proj_pts − level` to the hundredth at all seven rungs. The sum is **monotonically
decreasing** — −5.25, −32.18, −50.29, −108.28, −117.97, −136.65, −156.44 — with **no jump at the
crossing.** The deduction's return to −51.73 at rung 7 is exactly offset by `bpa` collapsing to
−86.36. Both are the same 149.17, once added and once subtracted.

### What this does to the fix

Substituting a live `free_alternative` into `displacement_level` while `bpa` keeps the anchor
would give:

```
bpa + adj  =  (points − L_anchor) + (L_live − displaced)  =  points − displaced − (L_anchor − L_live)
```

That last term is **the anchor's staleness, injected as a price** — at TE, pick 205, a flat
**−86.36** on every surplus tight end. There is no semantic justification for charging a roster
the size of a valuation error. It is a positional penalty with a derivation attached, which is
the thing #56 exists to forbid, and it is exactly the "43–60 point bias" magnitude
`displacement_adjustments`' own docstring says no bounded nudge should try to span.

**So: do not implement D3 as specified.** `free_alternative` does receive a stale value; the
term's *output* is invariant to it wherever the term is non-zero. The parameter is misnamed, not
mis-fed.

### Where the level does NOT cancel — and it is consumer 1's territory

When a reachable slot is **open**, `displacement_level` returns `free_alternative` unchanged, so
`adj = L − L = 0` and the price is `points − L`. Measured, exactly zero:

| pick | pos | adj | displaced | level | zero? |
|---|---|---|---|---|---|
| 205 | WR | **0.00** | 217.75 | 217.75 | YES |
| 241 | WR | **0.00** | 217.75 | 217.75 | YES |
| 281 | WR | **0.00** | 217.75 | 217.75 | YES |
| 205 | TE | −51.73 | 200.90 | 149.17 | no |
| 241 | RB | −46.94 | 217.75 | 170.81 | no |

So the anchor's staleness bites in exactly one place: positions with an open reachable slot,
through `bpa` alone. That is `_vor`/bpa — **consumer 1, which the ruling left authoritative.**

---

## AND THE PHENOMENON IS SOMEWHERE ELSE ENTIRELY

While confirming the above I checked what actually wins those picks. `simulate_full_draft` takes
`pick_synthesis.build_snapshot(...).candidates[0]` — **not** `compute_draft_board`'s row 0.

| pick | recorded pick | board's top 5 rows | `candidates[0]` | matches recorded | same as board row 0 |
|---|---|---|---|---|---|
| 193 | RB | WR WR WR WR WR | **RB** Tyler Allgeier | **yes** | no |
| 205 | TE | WR WR WR WR WR | **TE** Elijah Higgins | **yes** | no |
| 229 | TE | WR WR WR WR WR | **TE** Jackson Hawes | **yes** | no |
| 241 | WR | WR WR WR WR WR | **WR** Caleb Douglas | **yes** | no |
| 281 | TE | WR WR WR WR WR | **TE** Durham Smythe | **yes** | no |

`candidates[0]` reproduces the recorded pick **5 of 5**. It is the board's top row **0 of 5**.
At pick 205 the board's five best priced rows are all receivers and the engine takes a tight
end. 267 priced rows narrow to 7 candidates.

**The tight ends are not selected by `compute_draft_board`'s price. They are selected by the
narrowing in `pick_synthesis`.** That is B4 — "board rank is not pick order" — and it is not a
methodology footnote, it is where the phenomenon lives.

I am NOT claiming a defect in `narrow_candidates`. Five picks is five picks, and the last two
times something looked like a defect in this investigation it was correct. This is a location,
not a verdict.

---

## What I did not do

- **Did not implement D3.** The gate the owner set is what caught this; implementing anyway
  would defeat the point of having set it.
- **Did not touch the anchor, the fill, the optimizer, or `displacement_adjustments`.**
- **Did not touch the flex candidate.** Still frozen.
- **Did not run the battery.**

## What needs a revised ruling

1. **D3 is withdrawn as specified.** Does the owner want it re-scoped to consumer 1 — where
   the staleness demonstrably does reach the price through `bpa` on open-slot positions — or
   dropped entirely for now? Re-scoping it means reopening the half of the split the ruling
   just closed, so it is a real change of direction, not a detail.
2. **`free_alternative` is misnamed rather than mis-fed.** A prose repair (say what the
   parameter is actually used for, and that the term is invariant to it wherever it is
   non-zero) is available and cheap. Worth doing regardless of 1.
3. **The next investigation is `pick_synthesis.narrow_candidates`,** on the evidence above.
