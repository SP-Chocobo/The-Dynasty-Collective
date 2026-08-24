"""Lineup readiness -- "is there a problem with my active lineup right now," answered from
facts this app already computes. Explicitly NOT a recommendation: it never says who to start,
never invents a per-player "should start" score, and never touches sleeper_proj as anything
but one more fact alongside the others. See the Matchup concept merge (readiness strip →
decomposed roster) and the parked "Lineup Recommendation" concept, which is the separate,
later, harder question this module deliberately does not answer.

Three facts, each read from something that already exists:
  1. Are all real starting slots filled? (lineup_optimizer.slots_from_roster_positions already
     knows how many starting slots this league's own roster_positions define.)
  2. Is a STARTER (not bench) flagged with a real injury_status?
  3. Is this team's own positional depth Weak/None anywhere, per the same depth_ratings
     judgment the Trade Calculator and League Depth Map already use -- never a second opinion.
"""

from __future__ import annotations

from typing import Optional

import depth_ratings

_THIN_LABELS = ("Weak", "None — no rostered players here")


def compute_readiness(
    roster_table: list[dict], depth: dict, my_team_label: Optional[str], total_starting_slots: int,
) -> dict:
    """roster_table: this app's own per-player rows (slot/position/injury_status already set).
    depth: positional_depth(player_universe, merger)'s own output -- team_label -> position ->
    {"count", "value"}. my_team_label: this team's key into `depth`, or None if unresolved.
    total_starting_slots: len(lineup_optimizer.slots_from_roster_positions(...)) -- the
    league's own real starting-slot count, not re-derived here.

    Returns {"total_starting_slots", "filled_starting_slots", "starter_injury_flags",
    "thin_positions"} -- every field a direct read or a reuse of an existing judgment."""
    filled_starting_slots = sum(1 for r in roster_table if r.get("slot") == "Starter")
    starter_injury_flags = [
        {"name": r["name"], "position": r["position"], "injury_status": r["injury_status"]}
        for r in roster_table if r.get("slot") == "Starter" and r.get("injury_status")
    ]
    thin_positions = []
    if my_team_label and my_team_label in depth:
        for position in sorted(depth[my_team_label]):
            peer_cells = [teams[position] for teams in depth.values() if position in teams]
            cell = depth[my_team_label].get(position, {"count": 0, "value": None})
            label = depth_ratings.depth_label(cell, peer_cells)
            if label in _THIN_LABELS:
                thin_positions.append({"position": position, "label": label})
    return {
        "total_starting_slots": total_starting_slots,
        "filled_starting_slots": filled_starting_slots,
        "starter_injury_flags": starter_injury_flags,
        "thin_positions": thin_positions,
    }
