"""Calibration experiment "D" -- authorized explicitly as an ISOLATED EXPERIMENTAL COMPARISON,
not a permanent calibration decision, and NOT wired into draft_room.py. Flat (pre-A), A
(uniform dynasty softening, already live), and D (trajectory-aware softening) are all computed
HERE, independently, over the same real 250-player offense pool -- draft_room.py is only used
to get each player's real universal_value/time_horizon_adj/risk_adj (as A already computes it);
D's own formula is reimplemented in this script alone, exactly the same "recompute rather than
touch production" discipline used throughout this session's other experiments.

INDEPENDENCE PRECONDITION, checked before any of this was written (per explicit instruction --
"establish that time_horizon_adj is genuinely independent of the injury signal before letting
it modulate risk_adj"): confirmed by direct inspection of draft_room.py -- _season_proj_pct/
_proj3yr_pct (which feed time_horizon_adj) are computed ONLY from proj_3yr/_points (projection
data), inside the has_proj/no_proj_pool branches (draft_room.py:755-767), well before
injury_status is read at all (only inside score_row, for risk_adj alone, draft_room.py:800+).
No shared computation, no loop: an injury never changes time_horizon_adj, and time_horizon_adj
never depends on injury_status. D can safely use one to modulate the other without a
double-counting feedback path.

D's formula: risk_adj_D = RISK_ADJ[status] * d_scale, where
  d_scale = 1.0                                                    if time_horizon_adj <= 0
  d_scale = 1.0 - (1.0 - D_MIN_SCALE) * (time_horizon_adj / 10.0)   if time_horizon_adj > 0
D_MIN_SCALE = 0.3 (a floor, not zero -- an injury must still cost SOMETHING even for a maximally
forward-looking player; per the explicit caution that "young/forward trajectory -> injury
doesn't matter" would itself be a bad outcome to discover, not a good one).
A flat-or-declining-trajectory player (time_horizon_adj <= 0) gets the FULL, unscaled flat
penalty -- never MORE than history, only relief for a genuinely forward-looking asset. This
keeps D from amplifying the penalty beyond the existing RISK_ADJ magnitudes for anyone.
"""

from __future__ import annotations

import json
from pathlib import Path

import data_merger as dm
import draft_room as dr

OUT_PATH = Path("data/draft_simulation_trials") / "risk_adj_experiment_D_comparison.json"
OFFENSE_POSITIONS = ("QB", "RB", "WR", "TE")
DYNASTY_LEAGUE = {
    "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "BN", "BN", "BN", "BN"],
    "total_rosters": 12, "settings": {"type": 2},
}
STATUSES = ("Questionable", "Doubtful", "Out", "IR")
D_MIN_SCALE = 0.3
# Experiment A's own scale, hardcoded here since D superseded it in draft_room.py -- this
# script's whole point is comparing against A's historical behavior, not re-deriving it.
EXPERIMENT_A_SCALE = 0.5


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


def _d_scale(time_horizon_adj: float) -> float:
    if time_horizon_adj <= 0:
        return 1.0
    return 1.0 - (1.0 - D_MIN_SCALE) * (time_horizon_adj / dr.TIME_HORIZON_CLAMP[1])


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
        "d_min_scale": D_MIN_SCALE,
        "dynasty_risk_adj_scale_A": EXPERIMENT_A_SCALE,
        "independence_precondition_confirmed": (
            "time_horizon_adj is computed purely from proj_3yr/_points percentiles, before "
            "injury_status is read at all for risk_adj -- verified by direct code inspection, "
            "not assumed"
        ),
        "by_status": {},
    }

    for status in STATUSES:
        flat_penalty = dr.RISK_ADJ[status]
        a_penalty = flat_penalty * EXPERIMENT_A_SCALE
        crossed = {"flat": 0, "A": 0, "D": 0}
        for pid, row in healthy_board.items():
            uv = row["universal_value"]
            th = row["time_horizon_adj"]
            d_penalty = flat_penalty * _d_scale(th)
            if uv >= 0 > uv + flat_penalty:
                crossed["flat"] += 1
            if uv >= 0 > uv + a_penalty:
                crossed["A"] += 1
            if uv >= 0 > uv + d_penalty:
                crossed["D"] += 1
        report["by_status"][status] = {"zero_crossings": crossed}

    # THE MATCHED-PAIR TEST the user specifically wants: real players with similar healthy UV
    # but opposite time_horizon_adj, same injury status (IR, the harshest -- most legible).
    # For each such pair, report flat/A/D side by side.
    rows = list(healthy_board.values())
    matched_pairs = []
    UV_BAND = 3.0
    TH_GAP_MIN = 8.0
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if abs(a["universal_value"] - b["universal_value"]) > UV_BAND:
                continue
            if abs(a["time_horizon_adj"] - b["time_horizon_adj"]) < TH_GAP_MIN:
                continue
            forward, declining = (a, b) if a["time_horizon_adj"] > b["time_horizon_adj"] else (b, a)
            flat_p, a_p = dr.RISK_ADJ["IR"], dr.RISK_ADJ["IR"] * EXPERIMENT_A_SCALE
            forward_d = dr.RISK_ADJ["IR"] * _d_scale(forward["time_horizon_adj"])
            declining_d = dr.RISK_ADJ["IR"] * _d_scale(declining["time_horizon_adj"])
            matched_pairs.append({
                "forward_player": forward["name"], "forward_time_horizon_adj": forward["time_horizon_adj"],
                "forward_healthy_uv": forward["universal_value"],
                "declining_player": declining["name"], "declining_time_horizon_adj": declining["time_horizon_adj"],
                "declining_healthy_uv": declining["universal_value"],
                "post_ir_flat": {
                    "forward": round(forward["universal_value"] + flat_p, 2),
                    "declining": round(declining["universal_value"] + flat_p, 2),
                },
                "post_ir_A": {
                    "forward": round(forward["universal_value"] + a_p, 2),
                    "declining": round(declining["universal_value"] + a_p, 2),
                },
                "post_ir_D": {
                    "forward": round(forward["universal_value"] + forward_d, 2),
                    "declining": round(declining["universal_value"] + declining_d, 2),
                },
            })
    matched_pairs.sort(key=lambda p: -abs(p["forward_time_horizon_adj"] - p["declining_time_horizon_adj"]))
    report["matched_pairs_similar_healthy_value_opposite_trajectory"] = {
        "n_pairs_found": len(matched_pairs),
        "band_definition": f"|healthy_uv delta| <= {UV_BAND}, |time_horizon_adj delta| >= {TH_GAP_MIN}",
        "examples": matched_pairs[:10],
    }

    # Sanity check against the caution explicitly raised: does D go so far that injury becomes
    # NEARLY IRRELEVANT for a strongly forward-looking player? Report the real min/max d_scale
    # actually realized on the real pool (not just the theoretical D_MIN_SCALE floor).
    d_scales = [_d_scale(r["time_horizon_adj"]) for r in healthy_board.values()]
    report["d_scale_realized_on_real_pool"] = {
        "min": round(min(d_scales), 3), "max": round(max(d_scales), 3),
        "mean": round(sum(d_scales) / len(d_scales), 3),
    }

    OUT_PATH.write_text(json.dumps(report, indent=2, default=str))
    print(f"Wrote {OUT_PATH}")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
