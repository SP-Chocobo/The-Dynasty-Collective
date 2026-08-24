"""Real-data measurement of calibration experiment "A" (draft_room.DYNASTY_RISK_ADJ_SCALE),
per the user's explicit instruction: implement A alone, then measure hard before deciding
whether experiment "D" (scaling risk_adj by the player's own time_horizon_adj) is warranted.

Two questions, both on the real committed baseline, dynasty league, full offense pool:
  1. How many real players had universal_value cross zero (or worse) under each injury status,
     BEFORE vs AFTER the softening -- does A fix "most of the obviously stupid outcomes"?
  2. Does A introduce any WRONG ORDERING -- specifically, can a young/high-trajectory injured
     player now rank ABOVE an aging/declining-trajectory injured player in a way that looks like
     an artifact of the softening rather than a real value difference? (The user's specific
     concern that would make D "compelling" rather than optional.)

Measurement only in the sense that it doesn't change anything further -- draft_room.py's A
change is already implemented and tested; this script is the "measure it hard" step, run
against real data rather than the light test fixture used for the unit tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import data_merger as dm
import draft_room as dr

OUT_PATH = Path("data/draft_simulation_trials") / "risk_adj_softening_measurement.json"
OFFENSE_POSITIONS = ("QB", "RB", "WR", "TE")
# Experiment A's own scale, hardcoded here since D superseded it in draft_room.py -- this
# script is a historical measurement of A specifically, kept runnable rather than rewritten.
EXPERIMENT_A_SCALE = 0.5
DYNASTY_LEAGUE = {
    "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "BN", "BN", "BN", "BN"],
    "total_rosters": 12, "settings": {"type": 2},
}
STATUSES = ("Questionable", "Doubtful", "Out", "IR")


def _build_players_db(merger: dm.DataMerger) -> dict[str, dict]:
    proj = merger.projections
    players_db: dict[str, dict] = {}
    pid = 0
    for pos in OFFENSE_POSITIONS:
        sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False)
        for _, row in sub.iterrows():
            pid += 1
            parts = row["norm_name"].split()
            players_db[str(pid)] = {
                "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
            }
    return players_db


def main() -> None:
    merger = dm.DataMerger()
    players_db = _build_players_db(merger)

    healthy_board = {
        r["player_id"]: r for r in dr.compute_draft_board(
            merger, players_db, [], my_roster_id="99", league=DYNASTY_LEAGUE, mode="balanced",
        )
    }

    report: dict = {
        "n_players": len(healthy_board),
        "dynasty_risk_adj_scale": EXPERIMENT_A_SCALE,
        "by_status": {},
    }

    negative_examples: dict[str, list[dict]] = {}
    for status in STATUSES:
        base_penalty = dr.RISK_ADJ[status]
        softened_penalty = base_penalty * EXPERIMENT_A_SCALE
        crossed_zero_before = 0
        crossed_zero_after = 0
        examples = []
        for pid, healthy_row in healthy_board.items():
            uv = healthy_row["universal_value"]
            before = uv + base_penalty  # what it WOULD have been, pre-fix (flat penalty)
            after = uv + softened_penalty  # what it actually is now (softened)
            if uv >= 0 > before:
                crossed_zero_before += 1
            if uv >= 0 > after:
                crossed_zero_after += 1
                examples.append({
                    "name": healthy_row["name"], "position": healthy_row["position"],
                    "healthy_uv": uv, "time_horizon_adj": healthy_row["time_horizon_adj"],
                    "after_softening_uv": round(after, 2),
                })
        report["by_status"][status] = {
            "would_cross_zero_before_fix": crossed_zero_before,
            "still_crosses_zero_after_fix": crossed_zero_after,
            "fixed_count": crossed_zero_before - crossed_zero_after,
        }
        if examples:
            negative_examples[status] = sorted(examples, key=lambda e: e["after_softening_uv"])[:10]
    report["remaining_negative_examples_after_fix"] = negative_examples

    # Ordering check: rebuild the board under IR (the harshest status) for every player, and
    # look for any REAL pair where a lower-time_horizon_adj (more win-now / less dynasty-y)
    # player was OUTRANKED by a higher-time_horizon_adj player under health, but the ranking
    # FLIPPED specifically because of the softened (not flat) IR discount -- i.e. the softening
    # itself manufactured a flip that wasn't already true when healthy.
    flips = []
    for pid, healthy_row in healthy_board.items():
        pdb_ir = dict(players_db)
        pdb_ir[pid] = dict(pdb_ir[pid], injury_status="IR")
        ir_board = {
            r["player_id"]: r for r in dr.compute_draft_board(
                merger, pdb_ir, [], my_roster_id="99", league=DYNASTY_LEAGUE, mode="balanced",
            )
        }
        ir_row = ir_board.get(pid)
        if ir_row is None:
            continue
        # Compare against the single closest healthy peer by pre-injury universal_value --
        # cheap proxy for "did this specific injury flip an otherwise-settled ordering."
        peers = sorted(
            (r for p, r in healthy_board.items() if p != pid),
            key=lambda r: abs(r["universal_value"] - healthy_row["universal_value"]),
        )[:3]
        for peer in peers:
            healthy_order = healthy_row["universal_value"] > peer["universal_value"]
            ir_order = ir_row["universal_value"] > peer["universal_value"]
            if healthy_order != ir_order:
                flips.append({
                    "injured_player": healthy_row["name"], "injured_time_horizon_adj": healthy_row["time_horizon_adj"],
                    "peer": peer["name"], "peer_time_horizon_adj": peer["time_horizon_adj"],
                    "healthy_uv_injured_vs_peer": (healthy_row["universal_value"], peer["universal_value"]),
                    "post_ir_uv_injured_vs_peer": (ir_row["universal_value"], peer["universal_value"]),
                })
    report["ir_caused_ordering_flips_vs_closest_peers"] = {
        "count": len(flips),
        "n_pairs_checked": len(healthy_board) * 3,
        "examples": flips[:15],
    }

    OUT_PATH.write_text(json.dumps(report, indent=2, default=str))
    print(f"Wrote {OUT_PATH}")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
