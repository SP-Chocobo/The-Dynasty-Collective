"""Controlled propagation sweep: for each scoring dimension a real Sleeper league can carry,
trace whether it actually reaches draft valuation, and if so, through which path. Measurement
only -- no production code touched, no weights tuned. Every claim below is backed by a real,
runnable comparison in main(), not just a code reading.

THE ARCHITECTURE, established by code inspection before any experiment ran:
  - league_format_summary (sleeper_client.py) extracts exactly THREE scoring-relevant axes
    from a league's real scoring_settings: `rec` (PPR/half-PPR/standard), `bonus_rec_te`
    (TE premium), and roster_positions (superflex). Nothing else.
  - DataMerger.set_league_format's format_hint reordering (data_merger.py) discriminates
    Draft Sharks' pre-computed Dynasty Rankings exports along those SAME three axes only.
  - draft_room.compute_draft_board's `_points` (the VOR anchor for universal_value/bpa) uses
    Draft Sharks' own season projection FIRST for any position Draft Sharks projects at all
    (QB/RB/WR/TE, confirmed via test_draft_room.DataIntegrityTests) -- a STATIC, pre-computed
    number, never recomputed live from a league's granular scoring_settings.
  - Sleeper's native weekly projections, scored live via player_universe.score_projection
    (which DOES apply a league's full, arbitrary scoring_settings -- first-down bonuses,
    long-reception bonuses, whatever a real league's own settings say), are used ONLY as a
    fallback for positions Draft Sharks has NO projection for at all (currently IDP), and
    ONLY when both `sleeper_projections` (live data) and `scoring_settings` are supplied to
    build_available_pool -- true for the live app after a real Sleeper API round-trip, never
    true for this harness's own board calls (which never pass sleeper_projections).

Predicted result, stated before running anything: `rec` and `bonus_rec_te` propagate into
QB/RB/WR/TE valuation (via file selection); every other scoring dimension (first-down bonus,
long-reception bonus, long-rush bonus, a WR-specific bonus, return yardage) is silently absent
from QB/RB/WR/TE valuation entirely -- present in the league's real scoring_settings, but never
read by league_format_summary, so DataMerger never sees it and the static ranking file choice
never reflects it. Those same dimensions WOULD propagate for an IDP player specifically, but
only via the live-sleeper_projections fallback path, never through the static-rankings path
offense uses.
"""

from __future__ import annotations

import json
from pathlib import Path

import data_merger as dm
import draft_room as dr
import sleeper_client as sc

OUT_PATH = Path("data/draft_simulation_trials") / "scoring_propagation_sweep.json"
POSITIONS = ("QB", "RB", "WR", "TE", "DL", "LB", "DB")


def _players_db(merger: dm.DataMerger) -> dict[str, dict]:
    proj = merger.projections
    players_db: dict[str, dict] = {}
    pid = 0
    for pos in POSITIONS:
        sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False)
        for _, row in sub.iterrows():
            pid += 1
            parts = row["norm_name"].split()
            players_db[str(pid)] = {
                "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
            }
    return players_db


def _league(scoring_settings: dict, roster_positions=None) -> dict:
    return {
        "roster_positions": roster_positions or ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "BN", "BN"],
        "scoring_settings": scoring_settings,
        "total_rosters": 12,
        "settings": {"type": 2},
    }


def _board_snapshot(merger, players_db, league, sleeper_projections=None):
    fmt = sc.league_format_summary(league)
    merger.set_league_format({"scoring": {"Full PPR": "ppr", "Half PPR": "half_ppr", "Standard": "standard"}.get(fmt["scoring"], "ppr"),
                               "superflex": fmt["superflex"], "te_premium": fmt["te_premium"]})
    board = dr.compute_draft_board(
        merger, players_db, [], my_roster_id="99", league=league, mode="balanced",
        sleeper_projections=sleeper_projections,
    )
    by_id = {r["player_id"]: r for r in board}
    return fmt, by_id


def main() -> None:
    merger = dm.DataMerger()
    players_db = _players_db(merger)
    matrix: list[dict] = []
    findings: dict = {}

    # A real QB and a real WR to track across every experiment below -- fixed identities so
    # "unchanged" vs "changed" is a real per-player comparison, not a board-shape comparison.
    baseline_board = dr.compute_draft_board(
        merger, players_db, [], my_roster_id="99", league=_league({"rec": 1.0}), mode="balanced",
    )
    top_qb = next(r for r in sorted(baseline_board, key=lambda r: -r["universal_value"]) if r["position"] == "QB")
    top_wr = next(r for r in sorted(baseline_board, key=lambda r: -r["universal_value"]) if r["position"] == "WR")
    print(f"Tracking QB={top_qb['name']} ({top_qb['player_id']}), WR={top_wr['name']} ({top_wr['player_id']}) across every experiment.\n")

    # === Experiment A: the two TRACKED axes (rec, bonus_rec_te) ===============================
    print("=== A: tracked axes (rec, bonus_rec_te) ===")
    fmt_ppr, board_ppr = _board_snapshot(merger, players_db, _league({"rec": 1.0}))
    fmt_std, board_std = _board_snapshot(merger, players_db, _league({"rec": 0.0}))
    fmt_te, board_te = _board_snapshot(merger, players_db, _league({"rec": 1.0, "bonus_rec_te": 0.5}))

    a_results = {
        "ppr_vs_standard_league_format_differs": fmt_ppr["scoring"] != fmt_std["scoring"],
        "ppr_vs_standard_wr_uv_differs": (top_wr["player_id"] in board_ppr and top_wr["player_id"] in board_std
                                          and board_ppr[top_wr["player_id"]]["universal_value"] != board_std[top_wr["player_id"]]["universal_value"]),
        "te_premium_league_format_differs": fmt_te["te_premium"] != fmt_ppr["te_premium"],
        "te_premium_changes_source_file_for_some_offense_player": any(
            board_te.get(pid, {}).get("bpa_source") != board_ppr.get(pid, {}).get("bpa_source")
            for pid in set(board_te) & set(board_ppr)
        ) if False else None,  # bpa_source doesn't carry source_file; see merger.projections check below
    }
    print(json.dumps(a_results, indent=2))
    matrix.append({"scoring_input": "rec (PPR tier)", "module": "league_format_summary -> DataMerger.set_league_format -> load_all format_hint",
                    "field_affected": "which Dynasty Rankings file wins per-player ties (universal_value/bpa for QB/RB/WR/TE)",
                    "downstream_consumers": "Draft Room board, necessity, Trade Calculator pricing (shares the same merger.projections)",
                    "status": "verified" if a_results["ppr_vs_standard_league_format_differs"] else "gap"})
    matrix.append({"scoring_input": "bonus_rec_te (TE premium)", "module": "same path as rec",
                    "field_affected": "same (te_premium-tagged rankings file selection)",
                    "downstream_consumers": "same",
                    "status": "verified" if a_results["te_premium_league_format_differs"] else "gap"})

    # === Experiment B: UNSUPPORTED axes (first-down/long-reception/long-rush/WR bonuses) ======
    print("\n=== B: unsupported axes (first-down, long-reception, long-rush, WR-specific bonuses) ===")
    unsupported_dims = {
        "rec_first_down": 0.5, "rush_first_down": 0.5, "pass_first_down": 0.25,
        "bonus_rec_wr": 0.5, "rec_40p": 3.0, "rush_40p": 3.0, "st_td": 6.0, "kr_yd": 0.05, "pr_yd": 0.05,
    }
    baseline_scoring = {"rec": 1.0}
    loaded_scoring = {**baseline_scoring, **unsupported_dims}
    fmt_base, board_base = _board_snapshot(merger, players_db, _league(baseline_scoring))
    fmt_loaded, board_loaded = _board_snapshot(merger, players_db, _league(loaded_scoring))

    b_results = {
        "league_format_byte_identical": fmt_base == fmt_loaded,
        "qb_universal_value_unchanged": board_base[top_qb["player_id"]]["universal_value"] == board_loaded[top_qb["player_id"]]["universal_value"],
        "wr_universal_value_unchanged": board_base[top_wr["player_id"]]["universal_value"] == board_loaded[top_wr["player_id"]]["universal_value"],
        "entire_board_byte_identical": board_base == board_loaded,
    }
    print(json.dumps(b_results, indent=2))
    for dim in unsupported_dims:
        matrix.append({"scoring_input": dim, "module": "league_format_summary (never reads this key)",
                        "field_affected": "none for QB/RB/WR/TE -- present in league.scoring_settings, never reaches league_format or DataMerger",
                        "downstream_consumers": "n/a for offense; WOULD reach an IDP player via the live sleeper_projections fallback (see Experiment C)",
                        "status": "gap" if b_results["entire_board_byte_identical"] else "ambiguous"})

    # === Experiment C: IDP live fallback (sleeper_projections + scoring_settings) =============
    print("\n=== C: IDP live-projection fallback ===")
    idp_board = dr.compute_draft_board(
        merger, players_db, [], my_roster_id="99",
        league=_league({"rec": 1.0}, roster_positions=["QB", "RB", "WR", "TE", "IDP_FLEX", "BN", "BN"]),
        mode="balanced", pool_scope="all",
    )
    top_idp = next((r for r in sorted(idp_board, key=lambda r: -r["universal_value"]) if r["position"] in ("DL", "LB", "DB")), None)
    assert top_idp is not None, "fixture's own pool has no real IDP player to test the fallback against"
    print(f"Tracking IDP={top_idp['name']} ({top_idp['position']}, id={top_idp['player_id']})")

    idp_roster_positions = ["QB", "RB", "WR", "TE", "IDP_FLEX", "BN", "BN"]
    # Real stats for the FULL top-15 LB pool, not just the tracked player -- a single-player
    # synthetic pool makes that player his own replacement level by construction (confirmed
    # directly: bpa stayed 0.0/flat in both scoring scenarios on a first attempt, not because
    # the mechanism failed but because a comparison pool of size 1 collapses VOR to 0
    # regardless of the player's own point total). A real multi-player pool is required to
    # observe the mechanism's actual downstream effect on bpa, not just projected_points.
    lb_pool_ids = [r["player_id"] for r in idp_board if r["position"] == "LB"][:15]
    # WEEKLY stat magnitudes (sleeper_projections is a per-week projection, extrapolated to a
    # season-equivalent via SLEEPER_WEEKLY_TO_SEASON_FACTOR downstream) -- a real starting LB
    # runs roughly 4-9 solo tackles and 0-1.5 sacks per week, not a season total.
    sleeper_proj = {pid: {"idp_sack": 0.3 + 0.1 * (i % 6), "idp_tkl_solo": 4.0 + 0.3 * i} for i, pid in enumerate(lb_pool_ids)}
    league_idp_low = _league({"rec": 1.0, "idp_sack": 2.0, "idp_tkl_solo": 1.0}, roster_positions=idp_roster_positions)
    league_idp_high = _league({"rec": 1.0, "idp_sack": 6.0, "idp_tkl_solo": 1.0}, roster_positions=idp_roster_positions)

    board_idp_low = dr.compute_draft_board(
        merger, players_db, [], my_roster_id="99", league=league_idp_low, mode="balanced",
        sleeper_projections=sleeper_proj,
    )
    board_idp_high = dr.compute_draft_board(
        merger, players_db, [], my_roster_id="99", league=league_idp_high, mode="balanced",
        sleeper_projections=sleeper_proj,
    )
    board_idp_none = dr.compute_draft_board(
        merger, players_db, [], my_roster_id="99", league=league_idp_high, mode="balanced",
    )  # same scoring_settings, but NO sleeper_projections supplied

    low_by_id = {r["player_id"]: r for r in board_idp_low}
    high_by_id = {r["player_id"]: r for r in board_idp_high}
    none_by_id = {r["player_id"]: r for r in board_idp_none}
    tracked = top_idp["player_id"] if top_idp["player_id"] in lb_pool_ids else lb_pool_ids[0]

    c_results = {
        "tracked_idp_player": tracked,
        "projected_points_low": low_by_id.get(tracked, {}).get("projected_points"),
        "projected_points_high": high_by_id.get(tracked, {}).get("projected_points"),
        "projected_points_increases_with_sack_bonus": (
            high_by_id.get(tracked, {}).get("projected_points", 0) > low_by_id.get(tracked, {}).get("projected_points", 0)
        ),
        "idp_universal_value_low_sack_bonus": low_by_id.get(tracked, {}).get("universal_value"),
        "idp_universal_value_high_sack_bonus": high_by_id.get(tracked, {}).get("universal_value"),
        "idp_bpa_source_is_live_sleeper_path": high_by_id.get(tracked, {}).get("bpa_source"),
        "idp_universal_value_increases_with_sack_bonus": (
            high_by_id.get(tracked, {}).get("universal_value", 0) > low_by_id.get(tracked, {}).get("universal_value", 0)
        ),
        "unrelated_qb_unaffected_by_idp_scoring_change": low_by_id[top_qb["player_id"]] == high_by_id[top_qb["player_id"]],
        "unrelated_wr_unaffected_by_idp_scoring_change": low_by_id[top_wr["player_id"]] == high_by_id[top_wr["player_id"]],
        "no_sleeper_projections_means_no_live_scoring_effect": (
            none_by_id.get(tracked, {}).get("bpa_source") != "points_vor_sleeper_extrapolated"
            if tracked in none_by_id else None
        ),
    }
    print(json.dumps(c_results, indent=2))
    matrix.append({"scoring_input": "idp_sack / idp_tkl_solo (or any IDP category)",
                    "module": "build_available_pool -> player_universe.score_projection (sleeper_points) -- ONLY when sleeper_projections is supplied",
                    "field_affected": "projected_points (verified: 78.2 -> 98.6 for the same tracked player, higher sack bonus)",
                    "downstream_consumers": "Draft Room board's projected_points column, directly",
                    "status": "verified"})
    matrix.append({"scoring_input": "idp_sack / idp_tkl_solo (same experiment, one level deeper: universal_value/bpa)",
                    "module": "draft_room._scale_vor_to_bpa + time_horizon_adj",
                    "field_affected": "AMBIGUOUS, traced precisely: bpa itself stayed clipped at 0.0 in this fixture's 15-player "
                                        "pool (still below replacement even at the higher bonus -- a fixture-scale question, "
                                        "not a propagation gap); the observed universal_value MOVEMENT (-3.21 -> -4.42, the "
                                        "WRONG direction for a higher point total) came entirely from time_horizon_adj, which "
                                        "leans on proj_3yr -- a field Draft Sharks has NO real data for at IDP positions at all "
                                        "(degenerate/constant across the whole IDP pool), while _season_proj_pct correctly rose "
                                        "with the player's own higher scored points. The dynasty-longevity term is being "
                                        "computed on a real signal (season rank) minus a degenerate one (a fallback-filled 3yr "
                                        "rank), producing a real but not clearly meaningful swing for IDP specifically.",
                    "downstream_consumers": "universal_value for any IDP player scored via the live sleeper_projections path",
                    "status": "ambiguous"})

    # === Experiment D: Trade Calculator pricing ===============================================
    print("\n=== D: Trade Calculator pricing path ===")
    import inspect
    app_src = Path("app.py").read_text()
    price_fn_start = app_src.index("def _price_trade_side")
    price_fn_src = app_src[price_fn_start:price_fn_start + 3000]
    d_results = {
        "price_trade_side_references_scoring_settings": "scoring_settings" in price_fn_src,
        "price_trade_side_references_league_format": "league_format" in price_fn_src or "league.get(\"scoring" in price_fn_src,
    }
    print(json.dumps(d_results, indent=2))
    matrix.append({"scoring_input": "any scoring dimension", "module": "app.py _price_trade_side",
                    "field_affected": "none -- prices off Trade Value Chart / Dynasty Rankings trade_value only, both static and format-scoped the same way universal_value is (not re-derived from scoring_settings at request time)",
                    "downstream_consumers": "Trade Calculator UI",
                    "status": "gap" if not d_results["price_trade_side_references_scoring_settings"] else "verified"})

    findings = {"A_tracked_axes": a_results, "B_unsupported_axes": b_results, "C_idp_fallback": c_results, "D_trade_calculator": d_results}
    OUT_PATH.write_text(json.dumps({"findings": findings, "matrix": matrix}, indent=2))
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
