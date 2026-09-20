"""6.1d.1: can a threshold DERIVED from the sum's own ceiling ever light context_elevated?

The flag fires on `tav - uv` = need_bonus + depth_exposure + displacement_adj.

Structural facts already established in the tree:
  * need_bonus      <= NEED_BONUS_MAX      (12.0)
  * depth_exposure  <= DEPTH_EXPOSURE_MAX  (12.0)
  * displacement_adj <= 0 for a SINGLE-POSITION probe (lineup_optimizer, THE SIGN), and is
    positive only for a MULTI-eligible one.

So for the single-position population -- which is every row of a non-IDP rulebook -- the
ceiling of the gap IS sum(TEAM_SPECIFIC_CAPS) = 24.0, and the shipped threshold is its MEAN,
12.0. The badge nonetheless fires 0.0%: max gap 8.33.

THE HYPOTHESIS UNDER TEST: the ceiling is structurally unreachable, because the two capped
terms measure OPPOSITE roster states. need_bonus is large when a slot is EMPTY; depth_exposure
is large when the roster has SURPLUS at that position. If they cannot be large together, no
threshold derived from their sum can be live, and 6.1d.1's ruling cannot be executed as
written.
"""
import statistics
import data_merger as dm, draft_room as dr, draft_battery as db
import run_draft_battery as rdb, draft_strategy as ds
import pick_synthesis as ps

merger = dm.DataMerger()
players_db, _prov = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()

SPECS = [
    ("12T_ppr",      dict(teams=12, superflex=False, scoring="ppr",      te_premium=False)),
    ("12T_ppr_SF",   dict(teams=12, superflex=True,  scoring="ppr",      te_premium=False)),
    ("12T_standard", dict(teams=12, superflex=False, scoring="standard", te_premium=False)),
    ("10T_ppr_TEP",  dict(teams=10, superflex=False, scoring="ppr",      te_premium=True)),
]
NUM_TEAMS = 12


print(f"CONTEXT_ELEVATED_THRESHOLD = {ps.CONTEXT_ELEVATED_THRESHOLD}")
print(f"sum(TEAM_SPECIFIC_CAPS)    = {sum(ps.TEAM_SPECIFIC_CAPS)}  {ps.TEAM_SPECIFIC_CAPS}")
print()
print(f"{'format':<13}{'rnd':>4}{'n':>6}{'max gap':>9}{'p99':>8}{'>=12':>7}"
      f"{'max nb':>8}{'max de':>8}{'max nb+de':>11}{'both>4':>8}")

rows_all = []
for label, kw in SPECS:
  league = dr.build_mock_league(**kw, dynasty=True)
  merger.set_league_format(db.league_format_hint(league))
  NUM_TEAMS = kw["teams"]
  opening = dr.compute_draft_board(merger, players_db, [], my_roster_id="1", league=league,
                                   mode="balanced", sleeper_projections=season,
                                   sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
  for rounds in (0, 2, 4, 6, 8, 10, 12, 14):
      taken = rounds * NUM_TEAMS
      picks = [{"player_id": r["player_id"], "roster_id": str((i % NUM_TEAMS) + 1),
                "round": (i // NUM_TEAMS) + 1, "pick_no": i + 1}
               for i, r in enumerate(opening[:taken])]
      board = dr.compute_draft_board(merger, players_db, picks, my_roster_id="1", league=league,
                                     mode="balanced", sleeper_projections=season,
                                     sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
      rows = [r for r in board
              if r.get("universal_value") is not None and r.get("final_score") is not None]
      if not rows:
          continue
      gaps = [r["final_score"] - r["universal_value"] for r in rows]
      nb = [r.get("need_bonus") or 0.0 for r in rows]
      de = [r.get("depth_exposure") or 0.0 for r in rows]
      both = sum(1 for a, b in zip(nb, de) if a > 4.0 and b > 4.0)
      rows_all += list(zip(gaps, nb, de))
      print(f"{label[:12]:<13}{rounds:>4}{len(rows):>6}{max(gaps):>9.2f}"
            f"{sorted(gaps)[int(len(gaps)*0.99)]:>8.2f}"
            f"{sum(1 for g in gaps if g >= 12.0)/len(gaps)*100:>6.1f}%"
            f"{max(nb):>8.2f}{max(de):>8.2f}{max(a+b for a,b in zip(nb,de)):>11.2f}{both:>8}")

g = [x[0] for x in rows_all]
print(f"\nALL {len(rows_all)} priced rows across 8 board states")
print(f"  gap: min {min(g):.2f}  max {max(g):.2f}  mean {statistics.mean(g):.2f}")
print(f"  share >= CONTEXT_ELEVATED_THRESHOLD ({ps.CONTEXT_ELEVATED_THRESHOLD}): "
      f"{sum(1 for x in g if x >= ps.CONTEXT_ELEVATED_THRESHOLD)/len(g)*100:.2f}%")
print(f"  rows where need_bonus AND depth_exposure both > 4.0: "
      f"{sum(1 for _, a, b in rows_all if a > 4 and b > 4)} of {len(rows_all)}")
nz = [(a, b) for _, a, b in rows_all if a > 0 or b > 0]
print(f"  rows where EITHER is nonzero: {len(nz)}")
if nz:
    print(f"  of those, both nonzero: {sum(1 for a,b in nz if a>0 and b>0)}")
