"""W1-07: what bound does `intervening_picks` have, derived rather than chosen?

NECESSITY_SURVIVAL_WEIGHT scales `(1 - survival_probability)`, which is bounded [0,1] BECAUSE
IT IS A PROBABILITY. The substitute is a COUNT, so it needs a bound of its own or the 20-point
term has no scale. CDME_CONTRACTS is explicit that picking a mapping which reproduces today's
labels is #56's prohibition.

Candidate bound: the LONGEST WAIT THIS SEAT FACES IN THIS DRAFT, read off the pick order the
engine was already handed. No constant, no league-shape assumption -- and specifically not a
snake formula, because the #52 evidence notes a real draft with 135 TRADED seats, where a snake
bound would be wrong.

Measures the distribution over every seat of every turn, for a snake order and for a traded one.
"""
import random
import draft_strategy as ds

def gaps(pick_order, seat):
    """Intervening picks before each of `seat`'s turns -- the engine's own definition:
    len(picks strictly between this turn and the next one)."""
    idxs = [i for i, s in enumerate(pick_order) if str(s) == str(seat)]
    return [idxs[k + 1] - idxs[k] - 1 for k in range(len(idxs) - 1)]

for teams, rounds in ((12, 16), (10, 16)):
    seats = [str(i) for i in range(1, teams + 1)]
    snake = [str(s) for s in ds.generate_pick_order(seats, rounds, "snake")]

    # A traded order: same multiset of seats, some picks swapped between owners.
    rng = random.Random(1707)
    traded = list(snake)
    for _ in range(135):
        a, b = rng.randrange(len(traded)), rng.randrange(len(traded))
        traded[a], traded[b] = traded[b], traded[a]

    for name, order in (("snake", snake), ("traded(135)", traded)):
        allg = [g for s in seats for g in gaps(order, s)]
        per_seat_max = {s: max(gaps(order, s)) for s in seats}
        print(f"{teams}T x{rounds} {name:<12} n={len(allg):>4}  "
              f"min={min(allg):>3}  max={max(allg):>3}  "
              f"2*(T-1)={2*(teams-1):>3}  "
              f"per-seat max range={min(per_seat_max.values())}-{max(per_seat_max.values())}")
    print()
