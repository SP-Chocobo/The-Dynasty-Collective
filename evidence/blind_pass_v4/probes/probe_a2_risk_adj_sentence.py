"""A-F2/C-F6 x the pick_debate three-way health sentence: do they agree on real rows?

Two repairs in this range interact:

  * `draft_room.health_penalty` now returns 0.0 (was NaN) when `projected_points` is absent,
    for exactly the rows its comment names -- "a row priced on the TRADE-VALUE branch has a
    real `bpa` and `_points` of NaN ... Harold Landry (PUP, bpa 2.0) and DeShon Elliott (IR,
    bpa 15.0), reachable from any board built without season projections."
  * `pick_debate._format_candidate` now decides its injury sentence from `risk_adj`, with a
    third branch reading "NO discount was applied for it -- this engine does not price this
    designation, so his value below is the value of a fully fit player."

This probe builds the board those named rows live on, takes `risk_adj` from the board (the
PRODUCTION quantity -- no reconstruction), and asks the production formatter what it says.

Run from the repo root:
    PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 evidence/blind_pass_v4/probes/probe_a2_risk_adj_sentence.py
"""
import math

import pandas as pd

import data_merger as dm
import draft_battery as db
import draft_room as dr
import pick_debate as pd_mod
import player_universe as pu
import run_draft_battery as rdb
from pick_synthesis import CandidateSnapshot

merger = dm.DataMerger()                                    # from the REPO ROOT
players_db, prov = rdb.build_players_db_from_capture()
print("universe rows:", len(players_db))
league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False,
                             dynasty=True, base_scoring=rdb.scoring_settings_from_capture())
merger.set_league_format(db.league_format_hint(league))      # NEVER SKIP

# The board the health_penalty comment names: "reachable from any board built WITHOUT season
# projections". No sleeper_projections, so _points is NaN wherever only trade value exists.
board = dr.compute_draft_board(merger, players_db, [], my_roster_id=None, league=league,
                               mode="balanced")
frame = pd.DataFrame(board)
print("EMITTED COLUMNS:", sorted(frame.columns.tolist()))
print("board rows:", len(frame), " priced (final_score notna):", int(frame["final_score"].notna().sum()))


def isna(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


# The population the health_penalty repair is about: a real bpa, no projection.
bpa = frame["projected_points"] - 0  # not the authority; use the emitted pair below instead
trade = frame[frame["projected_points"].isna() & frame["final_score"].notna()
              & frame["injury_status"].notna()]
print()
print("ROWS WITH A DESIGNATION, NO PROJECTION, AND A PRICE  n =", len(trade))
if len(trade) == 0:
    print("  population empty -- the claim cannot be checked on this board")

for _, row in trade.head(8).iterrows():
    cand = CandidateSnapshot(
        player_id=str(row["player_id"]), name=row["name"], position=row["position"],
        team=row.get("team"), pick_necessity=50, necessity_label="CLOSE CALL",
        universal_value=row.get("universal_value"), team_acquisition_value=row.get("final_score"),
        risk_adj=row.get("risk_adj"), injury_status=row.get("injury_status"),
        availability_basis=row.get("availability_basis"),
        depth_exposure=row.get("depth_exposure"), depth_basis=row.get("depth_basis"),
    )
    text = pd_mod._format_candidate(cand, None)
    line = next(l for l in text.splitlines() if "Injury designation" in l)
    print(f"  {row['name']:<24} {row['injury_status']:<14} "
          f"risk_adj={row.get('risk_adj')!r:<8} basis={row.get('availability_basis')!r}")
    print(f"      -> {line.strip()}")

# And the states the new three-way branch does NOT enumerate: risk_adj ABSENT.
print()
print("--- the states `risk_adj` can be in that the three-way branch does not name ---")
for label, value in (("NaN  (unpriced row: score_row sets float('nan'))", float("nan")),
                     ("None (upside-mode board: the column is never emitted)", None),
                     ("0.0  (Questionable: #191 immaterial, genuinely not priced)", 0.0),
                     ("-18.0 (charged)", -18.0)):
    cand = CandidateSnapshot(player_id="x", name="N", position="WR", pick_necessity=1,
                             necessity_label="L", injury_status="IR",
                             availability_basis="games_missed_priced", risk_adj=value)
    line = next(l for l in pd_mod._format_candidate(cand, None).splitlines()
                if "Injury designation" in l)
    print(f"  risk_adj {label}")
    print(f"      -> {line.strip()}")
