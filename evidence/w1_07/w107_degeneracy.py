"""Does candidate B carry INFORMATION, or is it near-constant for most seats?

A term that barely moves is a term that cannot differentiate -- the same shape this repo
already flagged on the necessity tag (95.4% of rows in two of five bands). B normalises each
seat's gap by that seat's OWN longest wait, so a seat whose gaps are all similar saturates.
"""
import statistics
import draft_strategy as ds

for teams in (12, 10):
    rounds = 16
    seats = [str(i) for i in range(1, teams + 1)]
    order = [str(s) for s in ds.generate_pick_order(seats, rounds, "snake")]
    total = len(order)
    per_seat = {}
    for s in seats:
        idxs = [i for i, x in enumerate(order) if x == s]
        per_seat[s] = [idxs[k+1] - idxs[k] - 1 for k in range(len(idxs) - 1)]

    print(f"=== {teams} teams x {rounds} rounds, snake ===")
    print(f"{'seat':>5}{'gaps (first 6)':>26}{'seat max':>10}{'B mean':>9}{'B sd':>8}{'B range':>10}")
    for s in seats:
        g = per_seat[s]
        m = max(g)
        b = [x / m for x in g]
        print(f"{s:>5}{str(g[:6]):>26}{m:>10}{statistics.mean(b):>9.3f}"
              f"{statistics.pstdev(b):>8.3f}{max(b)-min(b):>10.3f}")
    # How many seats have B effectively pinned?
    flat = [s for s in seats if statistics.pstdev([x / max(per_seat[s]) for x in per_seat[s]]) < 0.10]
    print(f"seats where B's sd < 0.10 (term is near-constant): {len(flat)} of {teams} -> {flat}\n")
