"""The shared fixture for the v4 cost characterization. Definitions only at import time.

Built to the `engine-measurement` skill's five-line fixture, NOT to the hand-rolled variant:

  - `build_players_db_from_capture`, never `build_players_db`. The task brief for this pass
    named `build_players_db`; that is the VENDOR RECONSTRUCTION (764 rows, no `injury_status`,
    no `fantasy_positions`) and the skill names using it the sixth fixture error of its class.
    The battery whose 1.12s/6.03s figures this pass is characterizing calls
    `build_players_db_from_capture`, so that is the only population whose cost is the cost
    under investigation.
  - `season_projections_from_capture` + `SLEEPER_BASIS_SEASON_SUM`, because the battery passes
    them and the scoring-aware path is not free.
  - `set_league_format(league_format_hint(league))` before every format.
  - Run from the REPO ROOT. `DataMerger()` resolves `data/baseline` relative to cwd.
    `PYTHONPATH=. python3 evidence/performance/probes/<probe>.py` from the root.
"""
import os
import sys
import time

if os.environ.get("PYTHONDONTWRITEBYTECODE") is None:
    sys.dont_write_bytecode = True

import data_merger as dm
import draft_room as dr
import draft_battery as db
import run_draft_battery as rdb
import draft_strategy as ds


def fixture(verbose=True):
    """(merger, players_db, season, universe). Prints n for every population it builds."""
    t0 = time.time()
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    if verbose:
        print(f"FIXTURE cwd={os.getcwd()}", flush=True)
        print(f"FIXTURE capture={universe['source']} captured_at={universe['captured_at']}",
              flush=True)
        print(f"FIXTURE n_players_in_capture={universe['players_in_capture']} "
              f"n_players_in_pool={universe['players_in_pool']} "
              f"n_season_projections={len(season)} "
              f"n_priceable={rdb.priceable_projection_count(season)}", flush=True)
        print(f"FIXTURE injury_statuses_present={universe['injury_statuses_present']}", flush=True)
        print(f"FIXTURE merger_rows={len(merger.projections)} setup={time.time()-t0:.2f}s",
              flush=True)
    return merger, players_db, season, universe


def arm(label):
    """One entry of the battery's own 53-arm matrix, by label. Never a hand-built league."""
    matrix = db.league_matrix(rdb.scoring_settings_from_capture())
    for entry in matrix:
        if entry["label"] == label:
            return entry
    raise KeyError(f"{label} not in matrix; labels are {[e['label'] for e in matrix]}")


def labels():
    return [(e["label"], e["teams"], e["rounds"], e["teams"] * e["rounds"])
            for e in db.league_matrix(rdb.scoring_settings_from_capture())]


def board_inputs(merger, players_db, season, entry, upto=0):
    """Production's shape for a board build at pick index `upto`.

    picks carry {pick_no, round, roster_id, player_id} because `mode="auto"` resolves
    upside-vs-balanced off `round`, and a pick record missing it silently selects the other
    valuation (the #222 shape error).
    """
    merger.set_league_format(db.league_format_hint(entry["league"]))
    roster_ids = [str(i) for i in range(1, entry["teams"] + 1)]
    pick_order = ds.generate_pick_order(roster_ids, entry["rounds"], "snake")
    return {
        "merger": merger,
        "players_db": players_db,
        "league": entry["league"],
        "pick_order": pick_order,
        "sleeper_projections": season,
        "sleeper_basis": dr.SLEEPER_BASIS_SEASON_SUM,
    }
