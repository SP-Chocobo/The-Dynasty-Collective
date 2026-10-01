# Pre-registration — the upside-mode gap between C and C-prime

Written and committed BEFORE any arm of this run was read. Owner's instruction: *"measure the upside
mode gap, implement as you think best."*

Commit the run starts at: **`a7ad787`**. Instrument `evidence/design_35/phantom_cap_experiment.py`.
Arms `control`, `capped_floor_exempt`, `c_prime`, 12 seats, `12T_ppr_K_DEF`, `--streaming`, realized
ruler, one process per season.

## What is being measured, and why it is the only thing left open on C

C as specified cannot ship: it inverts a registered invariant and refutes `TEAM_SPECIFIC_CAPS`'
exemption with no constant available to re-derive. **C-prime** — cap `bpa`'s anchor at the best
remaining player instead of capping the slot alternative, keeping C's slot alternatives — is the one
admissible form, and the equivalence is a **derived identity**, not a coincidence:

    L'(p) = min(L(p), b(p))     bpa' = bpa + stale(p)     adj' = adj - stale(p)
    bpa' + adj' = points - X = bpa + adj

`point_replacement` is read at exactly four places in `compute_draft_board` and nothing else reads
it — not `need_bonus`, not `depth_exposure` — so every other term in `team_acquisition_value` is
untouched and the sum is identical row for row, for both the single-position and multi-eligible
populations.

**Upside mode is the one place it breaks.** `upside_score = bpa + 0.5 * growth` carries no
displacement term at all, so the cancellation has nothing to cancel against: C-prime's score exceeds
C's by exactly `stale(p)`, a non-negative per-position constant, which therefore **re-orders
positions against each other** in the rounds this format scores under upside mode.

## Pre-flight, run before the arms and recorded here

One drained board (top 168 drafted by league-scored season projection), both arms in one process:

| mode | rows | `max ǀfinal_score(C′) − final_score(C)ǀ` | `bpa′ − bpa` by position |
|---|---:|---:|---|
| balanced | 1034 | **0.0** | QB +13.33, every other position 0.00 |
| upside | 1034 | **13.33** | QB +13.33, every other position 0.00 |

`levels_capped` 2 (QB only at this state), `max_level_reduction` 13.33, `pool_missing` 0. The
identity holds where derived and breaks by exactly the derived amount where derived. **The
implementation is faithful, and this was checked before the arms ran rather than after.**

## The reading, fixed in advance

Paired by seat, `c_prime` − `capped_floor_exempt`:

* **The gap is immaterial** if both seasons land inside ±25 points per seat. Then C-prime inherits
  C's measured value (+21.7 and +43.7 a seat) essentially intact, and the choice between them is
  settled entirely by admissibility — which already favours C-prime. This is the outcome the
  derivation predicts, since the divergence is confined to the last rounds of a 16-round draft.
* **C-prime is BETTER than C** if positive on both seasons beyond that band. Then the upside-mode
  re-ordering is itself worth something, and the reason would be that `stale(p)` correctly demotes
  positions the pool has drained past — a second, independent argument for the same correction.
* **C-prime is WORSE than C** if negative on either season beyond the band. That would not rescue C,
  which is inadmissible regardless; it would mean the admissible form costs part of C's measured
  gain, and the size of that cost is what the owner is choosing against.

Whatever the sign, `c_prime` − `control` is the number that matters for shipping, because control is
what is shipped today. It is reported alongside.

## Non-vacuity, asserted before the results are read

* `cap_stats.levels_capped` must be > 0 in the `c_prime` arm, or the anchor cap never fired and the
  arm is `capped_floor_exempt` under another name.
* `cap_stats.pool_missing` must be 0.
* `level_capped_by_position` must be non-empty, and is reported so the reader can see WHICH
  positions' anchors were stale enough to bite.
* The `control` arm must reproduce 2024 11/12 +82.9 and 2023 4/12 −49.9. It ran at `6cd3be0` before
  and this run is at `a7ad787`; the only engine change between them stamps a LABEL on rows whose
  `bpa` is already absent, so the values must be identical. If they are not, something else moved
  and every number in this run is suspect.

## What this still will not settle

`startable_floors` is exempted from the anchor cap by the same derivation that exempts the streaming
floors — a startability threshold is not a pool reading either. This format produces no
`startable_floors`, so that half of the exemption is **untested here** and needs a superflex arm.
