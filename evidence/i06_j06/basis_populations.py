"""I-06/J-06: what population does each exposure basis actually hold?

The ruling is "separate basis token with its own scale", executed in two steps: introduce the
token carrying the measured uncovered quantity, PRICE NOTHING. Before designing the token,
measure which cells sit in which state and what quantity each carries.

Key question: is EXPOSURE_NO_SURPLUS reachable for any reason OTHER than "at least one starter
here had no cover"? Its label says "you hold no backup here, so there is no surplus to value",
but the code returns it whenever `not all(covered)`.
"""
import collections, statistics
import data_merger as dm, draft_room as dr, draft_battery as db
import run_draft_battery as rdb, lineup_optimizer as lo

merger = dm.DataMerger()
players_db, _prov = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()
league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr",
                              te_premium=False, dynasty=True)
merger.set_league_format(db.league_format_hint(league))
slots = [s for s in (league.get("roster_positions") or [])]

opening = dr.compute_draft_board(merger, players_db, [], my_roster_id="1", league=league,
                                 mode="balanced", sleeper_projections=season,
                                 sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
NUM_TEAMS = 12

cells = collections.Counter()
worst_by_basis = collections.defaultdict(list)
rows = []
for rounds in (1, 2, 3, 4, 6, 8, 10, 12):
    taken = rounds * NUM_TEAMS
    picks = [{"player_id": r["player_id"], "roster_id": str((i % NUM_TEAMS) + 1),
              "round": (i // NUM_TEAMS) + 1, "pick_no": i + 1}
             for i, r in enumerate(opening[:taken])]
    # PRODUCTION'S OWN BUILDER, not a hand-rolled one -- the first attempt rolled its own
    # and produced an EMPTY roster (n=0), which the engine-measurement rule about printing n
    # is exactly there to catch.
    roster_players = dr._team_roster_players(picks, players_db, "1", merger, set())
    exp = lo.depth_exposure(roster_players, slots)
    for position, d in exp.items():
        b = d.get("basis")
        cells[b] += 1
        if d.get("worst_loss") is not None:
            worst_by_basis[b].append(d["worst_loss"])
        rows.append((rounds, position, b, d.get("worst_loss"), d.get("starters")))

print(f"roster size at last state: {len(roster_players)}")
print(f"\ncells by basis (position x board state):")
total = sum(cells.values())
for b, n in cells.most_common():
    print(f"   {str(b):<18} {n:>4}  ({n/total*100:.1f}%)")
print(f"   {'TOTAL':<18} {total:>4}")

print(f"\nworst_loss by basis:")
for b, vals in worst_by_basis.items():
    if vals:
        print(f"   {str(b):<18} n={len(vals):>3}  min {min(vals):>8.2f}  "
              f"median {statistics.median(vals):>8.2f}  max {max(vals):>8.2f}")

print(f"\nno_surplus cells with a NON-ZERO worst_loss (the measured uncovered quantity):")
ns = [(r, p, w, s) for r, p, b, w, s in rows if b == lo.EXPOSURE_NO_SURPLUS and w]
print(f"   {len(ns)} of {cells[lo.EXPOSURE_NO_SURPLUS]}")
for r, p, w, s in ns[:8]:
    print(f"      round {r:>2}  {p:<4} worst_loss {w:>8.2f}  starters {s}")
