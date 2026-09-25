# The upside-mode gap, measured: it is ZERO — identical pick for pick, on both seasons

`PREREGISTRATION_CPRIME.md` fixed the reading before these arms ran. Commit `a7ad787`, instrument
`phantom_cap_experiment.py`, three arms per season in one process, 12 seats, `12T_ppr_K_DEF`,
`--streaming`, realized ruler.

## The result

| | C (`capped_floor_exempt`) | C′ (anchor-capped) | seats differing | rosters identical |
|---|---|---|---:|---|
| **2024** | 10/12, mean +97.74 | 10/12, mean +97.74 | **0 of 12** | **12 of 12, pick for pick** |
| **2023** | 4/12, mean +1.00 | 4/12, mean +1.00 | **0 of 12** | **12 of 12, pick for pick** |

Paired against the shipped engine, both arms: **+21.7/seat** (2024) and **+43.69/seat** (2023).
`max |C′ − C|` per seat is `0.0` on both seasons.

The roster-level identity is the stronger claim and the one to quote: C′ did not merely score the
same, it took **the same 192 players in the same order at all twelve seats, on both seasons**.

## It is not vacuous — the cap was live on every board

| | anchor cap firings | by position | largest single reduction | `pool_missing` |
|---|---:|---|---:|---:|
| 2024 C′ | **1,461** | QB 748, WR 713 | 225.49 | 0 |
| 2023 C′ | **1,392** | QB 751, WR 633, RB 8 | 160.84 | 0 |
| either other arm | 0 | — | — | 0 |

And the pre-flight had already shown the divergence is real in the **scores**: on a drained board,
`bpa′ − bpa` was `+13.33` for QB and exactly `0.00` for every other position, with balanced-mode
`final_score` identical to the cent and upside-mode `final_score` differing by exactly that 13.33.

So the anchor cap fired ~1,400 times per season, reduced levels by up to 225 points, changed
upside-mode scores by exactly `stale(p)` — **and moved no pick.**

## Why zero is the expected shape, not a surprise

Three facts compose:

1. The divergence exists **only in upside mode**, which a 16-round draft enters at the end, so the
   population exposed to it is the last rounds.
2. `stale(p)` is a **per-position constant**. A constant added to every row at a position re-orders
   positions against one another but **never re-orders rows within a position**.
3. So a pick changes only where the best remaining player at a drained position sat within `stale(p)`
   of the leader at some other position, at one of those late picks.

Across 384 picks (192 × 2 seasons) that never happened. The mechanism is real and its reach is
narrow — and "narrow" is now measured rather than asserted.

## What this settles, and what it does not

**Settles:** the choice between C and C′ is decided **entirely by admissibility**, because their
outcomes are indistinguishable — not within noise, identical. Admissibility already favours C′
decisively: C inverts a registered invariant and refutes `TEAM_SPECIFIC_CAPS`' exemption with no
constant available to re-derive, while C′ restores the invariant verbatim and puts the premium back
inside the caps. **C′ carries C's full measured value at none of C's cost.**

Both arms' value against the shipped engine stands as measured: **+21.7/seat on 2024 and
+43.69/seat on 2023**, 9 of 12 and 8 of 12 seats improved.

**Does not settle:**

* ~~**`startable_floors` is untested.**~~ **CLOSED, and it corrects my own derivation.** See the
  section below.
* **`universal_value` moves, and that is the real cost of C′.** At a drained position the best
  remaining player's `bpa` becomes 0.00. Nothing in the draft loop noticed — the rosters prove that —
  but `universal_value` is read by `pick_synthesis` for context elevation, by `draft_strategy` to rank
  a rival's pool, by `draft_counterfactual` as its BPA argmax, and by `roster_diagnostics`, which
  passes its NAME into `replacement_levels`. None of those consumers was measured here.
* **Other formats, rounds and modes.** Two seasons, one format, 16 rounds. A 26-30 round startup is
  where `stale(p)` is largest (the docstring's own measurement puts it at 142.68 for tight ends at the
  last pick) and is exactly where fact 3 above is most likely to bind.

## The recommendation, which is the owner's to accept or refuse

If C ships at all, it ships as **C′**. The outcome evidence is identical, the admissibility case is
one-sided, and the remaining work is bounded and named: a superflex arm for the `startable_floors`
exemption, and a pass over the four `universal_value` consumers above.

---

# The `startable_floors` hole is closed, and my derivation of it was WRONG

I exempted `startable_floors` from the anchor cap "by the same derivation that exempts the streaming
floors — a startability threshold is not a pool reading", and recorded it as the one untested half of
C′. **The conclusion is right, the reason was wrong, and the true reason is stronger.**

## What the branch actually returns

`replacement_levels`, the startable-floor branch:

```python
rank = int((at_pos[value_col] >= floor).sum()) or None   # how many REMAINING players clear it
idx  = min(rank - 1, len(at_pos) - 1)
levels[position] = float(at_pos.iloc[idx][value_col])    # a REMAINING player's own points
```

`at_pos` is the remaining pool at that position, sorted best first. So the level is **the points of
the last remaining player who clears the floor** — and since `idx >= 0`,

    L(p) = at_pos.iloc[rank-1]  <=  at_pos.iloc[0]  =  b(p)

**`L(p) <= b(p)` always, on this branch, by construction.** Therefore `min(L(p), b(p)) = L(p)` and the
anchor cap is provably a **no-op** there. The exemption is not wrong — it is unnecessary.

Measured on a real `12T_ppr_SF` board, draining QB pick by pick (board builds only, no drafts):

| QBs drafted | QB level | basis | best remaining QB | cap would bite? |
|---:|---:|---|---:|---|
| 0 | 207.50 | `startable_floor` | 372.46 | no |
| 24 | 207.50 | `startable_floor` | 281.89 | no |
| 30 | 207.50 | `startable_floor` | 215.37 | no |
| **31** | 207.50 | `startable_floor` | **207.50** | no — *exactly equal* |
| 32+ | *(declined)* | — | — | no level to cap |

The bound is tight and never crossed: the best remaining QB descends to exactly the level, and one
pick later the branch declines entirely and there is no level at all. **The situation the exemption
guards against cannot arise.**

## Why the streaming floor is genuinely different

    streaming:  levels[position] = float(floor)        # an ASSIGNED value no player need have
    startable:  levels[position] = at_pos.iloc[idx]    # a REMAINING player's own points

`#30`'s floor is the season sum of each week's best wire option, assigned raise-only as a value. No
single player has it, so it can and does exceed `b(p)` — measured on the 2024 opening board at DEF
146.05 against a best remaining defense of 121.49. That is why its exemption is load-bearing and
worth +53 to +54 a seat.

**So the distinction that matters is not "threshold versus pool reading" but HOW THE LEVEL IS
PRODUCED: assigned as a value, or selected as a rank within the remaining pool.** A rank selection
can never exceed the pool's own best. Only an assignment can. That is the general statement, and it
is the right one to carry into any future level that gets added:

> C′'s anchor cap must exempt exactly those levels that are ASSIGNED a value rather than SELECTED
> from the remaining pool. Today that is `streaming_floors` and nothing else.

The exemption for `startable_floors` stays in the instrument — it costs nothing and removing it would
be a change with no measured cause — but it is now documented as redundant rather than as untested.

## What remains unmeasured on C′

Only the consumer boundary: `universal_value` moves at drained positions, and `pick_synthesis`,
`draft_strategy`, `draft_counterfactual` and `roster_diagnostics` all read it. The draft loop is
proven indifferent (identical rosters, both seasons); those four are not.
