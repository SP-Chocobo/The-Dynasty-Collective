"""W1-07 candidate scales, profiled. Structural -- reads only the pick order, no engine.

A: intervening / (2*(teams-1))        -- REJECTED by w107_scale.py: 46 > 22 on a traded order,
                                         so it is a snake-shape ASSUMPTION, not a bound.
B: intervening / this seat's own longest wait in this draft
C: intervening / picks remaining in the draft at this turn

Both B and C are bounded [0,1] by construction for ANY order. They differ in SHAPE, and the
shape is the decision: B is flat across the draft, C rises. Necessity already has a
LATE_ROUND_NECESSITY_CAP, so a term that rises late is not obviously wanted.
"""
import draft_strategy as ds

teams, rounds = 12, 16
seats = [str(i) for i in range(1, teams + 1)]
order = [str(s) for s in ds.generate_pick_order(seats, rounds, "snake")]
total = len(order)

turns = []   # (round, seat, intervening, picks_remaining_after_this_turn)
for i, s in enumerate(order):
    nxt = next((j for j in range(i + 1, total) if order[j] == s), None)
    if nxt is None:
        continue
    turns.append((i // teams + 1, s, nxt - i - 1, total - i - 1))

seat_max = {}
for s in seats:
    seat_max[s] = max(g for (_, ss, g, _) in turns if ss == s)

print(f"{'round':>6}{'n':>4}{'intervening':>13}{'B mean':>9}{'B max':>8}{'C mean':>9}{'C max':>8}")
for r in (1, 2, 4, 8, 12, 15):
    rows = [(g, rem, ss) for (rr, ss, g, rem) in turns if rr == r]
    if not rows:
        continue
    b = [g / seat_max[ss] for g, rem, ss in rows]
    c = [g / rem for g, rem, ss in rows if rem > 0]
    gm = sum(g for g, _, _ in rows) / len(rows)
    print(f"{r:>6}{len(rows):>4}{gm:>13.1f}{sum(b)/len(b):>9.3f}{max(b):>8.3f}"
          f"{sum(c)/len(c):>9.3f}{max(c):>8.3f}")

allb = [g / seat_max[ss] for (_, ss, g, _) in turns]
allc = [g / rem for (_, ss, g, rem) in turns if rem > 0]
print(f"\nB over all {len(allb)} turns: min {min(allb):.3f}  max {max(allb):.3f}")
print(f"C over all {len(allc)} turns: min {min(allc):.3f}  max {max(allc):.3f}")
print(f"\nB is bounded by construction: {max(allb) <= 1.0}")
print(f"C is bounded by construction: {max(allc) <= 1.0}")
