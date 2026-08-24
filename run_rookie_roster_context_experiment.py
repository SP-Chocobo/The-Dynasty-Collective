"""Validation experiment proposed directly by the user (with a second model's design input):
run the EXACT SAME rookie board against wildly different real roster states, using
compute_draft_board's new demand_picks parameter (see draft_room.py's own module docstring for
the bug this fixes) to correctly isolate "does roster context change the recommendation" from
the unrelated replacement-level distortion a naive multi-phase history would introduce.

The claim under test: roster context should mostly decide BETWEEN comparably-valued rookies
(near-tier, within NEAR_TIE_BAND / a modest universal_value gap) and should rarely or never flip
the TAV-argmax recommendation across a REAL tier gap (a standout leader with real separation).
If the top recommendation changes dramatically between roster states even when the original,
roster-agnostic board shows a clear standout, that's a red flag -- the contextual layer would be
manufacturing a preference the market's own consensus already rejected. If it changes mainly
within tiers or right at tier breaks, that's the intended, healthy behavior.

Three real roster states are built from real veteran players (never touching the rookie pool
candidates), each isolated via demand_picks=[] so replacement-level accounting stays correctly
scoped to "nothing drafted in this rookie phase yet" regardless of roster size:
  - balanced: a reasonably even positional mix.
  - wr_stacked: heavy WR depth already rostered (low WR need).
  - wr_starved: zero WRs rostered at all (high WR need).

Measurement only; no production code changed beyond draft_room.py's already-committed
demand_picks parameter.
"""

from __future__ import annotations

import json
from pathlib import Path

import data_merger as dm
import draft_room as dr

OUT_PATH = Path("data/draft_simulation_trials") / "rookie_roster_context_experiment.json"
POSITIONS = ("QB", "RB", "WR", "TE")
LEAGUE = {
    "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "BN", "BN", "BN", "BN", "BN", "BN"],
    "total_rosters": 12, "settings": {"type": 2},
}


def _build_players_db(merger: dm.DataMerger) -> dict[str, dict]:
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


def _veteran_ids_by_position(merger: dm.DataMerger, players_db: dict[str, dict]) -> dict[str, list[str]]:
    """Real veteran (non-rookie) player_ids per position, best-value first -- used to build
    each roster scenario's own history without ever touching the rookie candidate pool."""
    board = dr.compute_draft_board(
        merger, players_db, [], my_roster_id="00", league=LEAGUE, mode="balanced", pool_scope="veterans_only",
    )
    by_pos: dict[str, list[str]] = {}
    for row in board:
        by_pos.setdefault(row["position"], []).append(row["player_id"])
    return by_pos


def _roster_history(roster_id: str, picks_by_position: dict[str, int], veteran_ids: dict[str, list[str]]) -> list[dict]:
    picks = []
    pick_no = 1
    for pos, n in picks_by_position.items():
        for pid in veteran_ids.get(pos, [])[:n]:
            picks.append({"pick_no": pick_no, "round": 1, "roster_id": roster_id, "player_id": pid})
            pick_no += 1
    return picks


ROSTER_SCENARIOS = {
    "balanced": {"WR": 3, "RB": 3, "TE": 1, "QB": 1},
    "wr_stacked": {"WR": 6, "RB": 2, "TE": 1, "QB": 1},
    "wr_starved": {"WR": 0, "RB": 4, "TE": 2, "QB": 1},
    "qb_desperate": {"WR": 3, "RB": 3, "TE": 1, "QB": 0},
}


def main() -> None:
    merger = dm.DataMerger(league_format={"scoring": "ppr", "superflex": False, "te_premium": False})
    players_db = _build_players_db(merger)
    veteran_ids = _veteran_ids_by_position(merger, players_db)

    # The roster-agnostic ground truth: the rookie board with NO roster history at all (need
    # bonus neutral for every candidate) -- this is what defines "real tier gap" vs "near tie"
    # for every scenario below.
    baseline_board = dr.compute_draft_board(
        merger, players_db, [], my_roster_id="test", league=LEAGUE, mode="balanced",
        pool_scope="rookies_only", demand_picks=[],
    )
    baseline_board = sorted(baseline_board, key=lambda r: -r["universal_value"])
    baseline_top = baseline_board[0]
    baseline_second = baseline_board[1] if len(baseline_board) > 1 else None
    tier_gap = (baseline_top["universal_value"] - baseline_second["universal_value"]) if baseline_second else None

    print(f"Roster-agnostic top rookie: {baseline_top['name']} ({baseline_top['position']}) uv={baseline_top['universal_value']}")
    if baseline_second:
        print(f"  #2: {baseline_second['name']} ({baseline_second['position']}) uv={baseline_second['universal_value']}  gap={tier_gap:.2f}")

    results = {
        "baseline_top": baseline_top["name"], "baseline_top_position": baseline_top["position"],
        "baseline_top_uv": baseline_top["universal_value"],
        "baseline_second": baseline_second["name"] if baseline_second else None,
        "baseline_gap": round(tier_gap, 2) if tier_gap is not None else None,
        "scenarios": {},
    }

    for label, mix in ROSTER_SCENARIOS.items():
        history = _roster_history("test", mix, veteran_ids)
        board = dr.compute_draft_board(
            merger, players_db, history, my_roster_id="test", league=LEAGUE, mode="balanced",
            pool_scope="rookies_only", demand_picks=[],
        )
        board = sorted(board, key=lambda r: -r["final_score"])  # TAV-argmax -- what the engine would actually pick
        top = board[0]
        top_uv_rank = next(i for i, r in enumerate(sorted(board, key=lambda r: -r["universal_value"])) if r["player_id"] == top["player_id"])
        flipped_from_baseline = top["player_id"] != baseline_top["player_id"]
        print(f"\n{label} (history={mix}): TAV-top = {top['name']} ({top['position']}) "
              f"tav={top['final_score']} need_bonus={top['need_bonus']}  "
              f"flipped_from_baseline={flipped_from_baseline}  uv_rank_among_uv_sorted={top_uv_rank}")
        results["scenarios"][label] = {
            "roster_mix": mix,
            "tav_top": top["name"], "tav_top_position": top["position"],
            "tav_top_final_score": top["final_score"], "tav_top_need_bonus": top["need_bonus"],
            "flipped_from_baseline_top": flipped_from_baseline,
            "tav_tops_universal_value_rank": top_uv_rank,  # 0 = still the true best rookie by raw value
            "top6_by_tav": [
                {"name": r["name"], "position": r["position"], "tav": r["final_score"], "need_bonus": r["need_bonus"]}
                for r in board[:6]
            ],
        }

    OUT_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {OUT_PATH}")
    print("\n=== VERDICT ===")
    any_flip = any(s["flipped_from_baseline_top"] for s in results["scenarios"].values())
    if not any_flip:
        print("No roster scenario flipped the top recommendation -- context stayed within the standout's own tier "
              "(if a real gap exists) or never had a chance to matter (if the top of board was already tied).")
    else:
        max_rank_when_flipped = max(
            (s["tav_tops_universal_value_rank"] for s in results["scenarios"].values() if s["flipped_from_baseline_top"]),
            default=0,
        )
        print(f"Some roster scenario(s) flipped the top recommendation. The new top's own universal_value rank "
              f"(0=truly best) among the roster-agnostic ordering was as low as {max_rank_when_flipped} -- "
              f"a small number means it only ever won against near-tied alternatives (healthy); a large number "
              f"would mean context overrode a real tier gap (the failure mode both you and the second model flagged).")


if __name__ == "__main__":
    main()
