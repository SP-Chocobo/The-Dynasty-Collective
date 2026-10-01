"""The two states `risk_adj` can be in that `pick_debate`'s new THREE-way branch does not name.

The comment says "THREE states, because there are three (`#187`)". `risk_adj` reaching a
`CandidateSnapshot` has five:

  charged                 a real negative                       -> "already inside the value"   OK
  rule_floor              0.0, basis RULE_FLOOR                 -> "already REMOVED"            OK
  unpriced designation    0.0, no rate for the status            -> "does not price it"          OK
  NaN                     `score_row` sets float("nan") when bpa is NaN -- an UNPRICED ROW, and
                          `pick_synthesis`' own comment says one reaches this formatter
  absent (None)           UPSIDE MODE never emits the column at all, by design:
                          "the per-position decomposition terms ... stay absent because
                           upside_score genuinely never computes them"

`_charged = risk_adj is not None and risk_adj != 0.0` puts NaN in the CHARGED branch and None in
the NOT-PRICED branch. This measures the upside population on a real board and reports what each
state is told.

Run from the repo root:
    PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 \
        evidence/blind_pass_v4/probes/probe_risk_adj_the_fourth_and_fifth_states.py
"""
import collections
import dataclasses

import pandas as pd

import data_merger as dm
import draft_battery as db
import draft_room as dr
import pick_debate as pdb
import pick_synthesis as ps
import run_draft_battery as rdb

merger = dm.DataMerger()
players_db, _ = rdb.build_players_db_from_capture()
base = rdb.scoring_settings_from_capture()
league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False,
                             dynasty=True, base_scoring=base)
merger.set_league_format(db.league_format_hint(league))
season = rdb.season_projections_from_capture()

for mode in ("balanced", "upside"):
    board = dr.compute_draft_board(merger, players_db, [], my_roster_id=None, league=league,
                                   mode=mode, sleeper_projections=season,
                                   sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    f = pd.DataFrame(board)
    print("=" * 78)
    print(f"mode={mode}  rows={len(f)}  emitted mode={f['mode'].iloc[0]!r}  "
          f"risk_adj column present={'risk_adj' in f.columns}")
    if "risk_adj" in f.columns:
        unpriced = f[f["bpa"].isna() & f["injury_status"].notna()]
        print(f"  UNPRICED rows carrying a designation: n={len(unpriced)}"
              f"   risk_adj all NaN: {bool(unpriced['risk_adj'].isna().all()) if len(unpriced) else 'n/a'}")
        print(f"  designations on them: {unpriced['injury_status'].value_counts().to_dict()}")
    else:
        with_status = f[f["injury_status"].notna()]
        print(f"  rows carrying a designation: n={len(with_status)}"
              f"  -> every one reaches the snapshot with risk_adj None")
        print(f"  designations: {with_status['injury_status'].value_counts().to_dict()}")

# The snapshot, so the object pick_debate actually receives is production's own.
snap = ps.build_snapshot(merger, players_db, [], [str(i) for i in range(1, 13)], 0, "1", league,
                         pick_label="1.01", mode="upside",
                         sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
cands = [c for c in snap.candidates if c.injury_status]
print()
print("=" * 78)
print(f"UPSIDE snapshot at pick 1.01: {len(snap.candidates)} candidates, "
      f"{len(cands)} carrying a designation")
print("  risk_adj census on them:",
      dict(collections.Counter(repr(c.risk_adj) for c in cands)))
for c in cands[:6]:
    line = next(l for l in pdb._format_candidate(c, None).splitlines()
                if "Injury designation" in l)
    rate = dr.HEALTH_DISCOUNT_RATE.get(c.injury_status)
    print(f"  {c.name:<22} {c.injury_status:<13} risk_adj={c.risk_adj!r:<6} "
          f"rate={rate}")
    print(f"      ->{line.rstrip()[len('  Injury designation:'):]}")

# The NaN state, with the value taken from the balanced board.
print()
print("=" * 78)
print("the NaN state (an unpriced row, which `#183` says reaches this formatter):")
bal = pd.DataFrame(dr.compute_draft_board(merger, players_db, [], my_roster_id=None,
                                         league=league, mode="balanced",
                                         sleeper_projections=season,
                                         sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM))
unpriced = bal[bal["bpa"].isna() & bal["injury_status"].notna()]
print("  unpriced rows with a designation:", len(unpriced))
if len(unpriced):
    row = unpriced.iloc[0]
    cand = dataclasses.replace(
        snap.candidates[0], player_id=str(row["player_id"]), name=row["name"],
        position=row["position"], injury_status=row["injury_status"],
        risk_adj=row["risk_adj"], universal_value=row["universal_value"],
        bpa=row["bpa"], team_acquisition_value=row["final_score"],
        availability_basis=(None if pd.isna(row["availability_basis"])
                            else row["availability_basis"]))
    line = next(l for l in pdb._format_candidate(cand, None).splitlines()
                if "Injury designation" in l)
    print(f"  {row['name']} {row['injury_status']} risk_adj={row['risk_adj']!r} "
          f"universal_value={row['universal_value']!r}")
    print(f"      ->{line.rstrip()[len('  Injury designation:'):]}")

# --- is a PRICED designation ever in a narrowed UPSIDE candidate set? --------------------
# The 1.01 snapshot above narrowed only `Questionable` rows, for which the sentence is
# accidentally true. The board carries 63 IR and 7 PUP rows, which the engine DOES price. Drain
# the board and ask again at a mid-draft turn, with the picks in PRODUCTION'S SHAPE
# ({pick_no, round, roster_id, player_id}) so `mode` resolution and round detection are not
# silently changed by the input shape.
print()
print("=" * 78)
print("a drained UPSIDE board: is a PRICED designation ever narrowed in?")
up = pd.DataFrame(dr.compute_draft_board(merger, players_db, [], my_roster_id=None, league=league,
                                        mode="upside", sleeper_projections=season,
                                        sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM))
priced_status = {s for s, r in dr.HEALTH_DISCOUNT_RATE.items() if r is not None}
print("  board rows carrying a designation the engine PRICES:",
      int(up["injury_status"].isin(priced_status).sum()),
      dict(up.loc[up["injury_status"].isin(priced_status), "injury_status"].value_counts()))

order = up.dropna(subset=["final_score"]).sort_values("final_score", ascending=False)
taken = [str(p) for p in order["player_id"].head(144)]
seats = [str(i) for i in range(1, 13)]
picks = [{"pick_no": i + 1, "round": i // 12 + 1, "roster_id": seats[i % 12],
          "player_id": pid} for i, pid in enumerate(taken)]
pick_order = [seats[i % 12] for i in range(len(seats) * 15)]
snap2 = ps.build_snapshot(merger, players_db, picks, pick_order, len(picks), "1", league,
                          pick_label="13.01", mode="upside",
                          sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
hit = [c for c in snap2.candidates if c.injury_status in priced_status]
print(f"  snapshot at 13.01: {len(snap2.candidates)} candidates, "
      f"{sum(1 for c in snap2.candidates if c.injury_status)} with any designation, "
      f"{len(hit)} with a PRICED one")
for c in hit[:5]:
    line = next(l for l in pdb._format_candidate(c, None).splitlines()
                if "Injury designation" in l)
    print(f"  {c.name:<22} {c.injury_status:<5} risk_adj={c.risk_adj!r:<6} "
          f"rate={dr.HEALTH_DISCOUNT_RATE.get(c.injury_status)}")
    print(f"      ->{line.rstrip()[len('  Injury designation:'):]}")
if not hit:
    print("  none narrowed in at this turn -- the falsehood is reachable on the BOARD but was "
          "not observed in a narrowed set here")
