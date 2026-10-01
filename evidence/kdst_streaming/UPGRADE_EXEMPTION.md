# The upgrade exemption: a successful experiment that settled the question NO

Built, measured, and reverted in one sitting. Recorded because it answered something worth
knowing and because the machinery in it is worth having later.

## The question

Can a purely DERIVED upgrade exemption capture the dynasty-QB3 intuition — "I don't want a hard
ceiling blocking a genuinely valuable third quarterback in a deep league" — without inventing a
preference the engine has no information about?

## The rule

Demote a candidate at a saturated position only when he would **not** improve on the worst player
already held there. If he is better, taking him is an upgrade and the surplus body is whoever he
displaces, so leave him alone and price him normally.

Arithmetically clean: his projected points against my own rostered players' projected points,
both already computed on the same basis (`roster_points_lookup`, `#216`). **No constant enters.**

And it cannot reopen the hole it was built for. The nine defenses were monotonically decreasing —
121.5, 120.4, 119.9, 112.3, 112.2, 112.1, 111.3, 109.3, 109.1 — so every one after the second is
still demoted.

## The answer: NO, and one roster shows why

2024 seat 1: **identical to the hard ceiling, +168.4, roster byte-for-byte the same.** The
exemption never fired — no third quarterback was an upgrade — so it was free.

2023 seat 1 is where it fired:

```
rd  6 QB Derek Carr        proj 272.4      <- QB1
rd  9 QB Matthew Stafford  proj 264.6      <- QB2, roster now at the ceiling
rd 10 QB Geno Smith        proj 267.0      <- ADMITTED: "an upgrade" on Stafford by 2.4
```

Delta −161.0 against the hard ceiling's −84.9. **Cost: 76 realized points on that seat.**

**The 76 points are not what settles it. The 2.4 is.** Nobody designing a dynasty draft engine
means "take a third quarterback whenever he is 2.4 points better than your second." The rule is
mathematically coherent and semantically wrong: it exploits the arithmetic definition of
*upgrade* rather than expressing an intent. A hair's-breadth third quarterback spends a roster
spot and buys nothing, because you still start one.

Making it express the intent needs a notion of **meaningfully** better, which is a chosen
magnitude, which is `#56`. So it was reverted rather than tuned — a threshold picked because it
tested well is exactly how the first K/DST repair got brute-forced into shape and unwound.

## What the engine commits to instead

> The engine does not independently value surplus roster slots for dynasty-specific purposes such
> as insurance, trade liquidity, or developmental stashes unless those preferences are explicitly
> modelled.

A one-season projected-points ruler contains no information about what a stashed third
quarterback is worth. The hard ceiling is blunt but **honest**: it says only that the modelled
roster depth at a position is full. That is a structural constraint, not a secretly calibrated
preference.

The clean separation, which is where this lands:

| layer | owns |
|---|---|
| **Core CDME** | valuation of the player, and roster consequences of taking him |
| **Roster-construction constraint** | the fieldability ceiling — surplus-position logic |
| **Owner preference** | whether to carry extra depth for insurance, liquidity, development |

The third layer does not exist yet, and when it does it should be a user-set concept rather than
a points threshold — asking an owner to translate "meaningfully better" into a number of
projected points is the same defect one level up.

## The machinery, kept

The one piece worth preserving: the engine **can** distinguish "this is merely another body" from
"this player actually displaces someone on the roster." That comparison is cheap and needs no
constant, and it is the natural primitive for an explicit roster-preference layer. It was
implemented as `unfieldable_last(..., my_points_players=...)`:

```python
# The weakest thing already held at each saturated position, in projected points.
weakest_held: dict[str, float] = {}
for row in (my_points_players or []):
    value = row.get("value")
    if value is None:
        continue
    for position in (row.get("eligible") or ()):
        if position in saturated:
            weakest_held[position] = (value if position not in weakest_held
                                      else min(weakest_held[position], value))

# ... then, per candidate, after the subset test:
mine = values.get(str(player_id))
if mine is None:
    return 1                      # unpriced: fall back to the count alone
for position in eligible:
    floor = weakest_held.get(position)
    if floor is not None and mine > floor:   # strictly greater: equal is a second copy
        return 0                  # an UPGRADE at a position he can reach -- not surplus
return 1
```

`_my_points_players` is already computed inside `compute_draft_board` for `displacement_adj`, so
wiring it costs nothing. Full implementation and its six tests are in commit `923de13`, reverted
by the commit that added this file.
