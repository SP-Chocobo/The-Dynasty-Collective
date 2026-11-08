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
import player_universe

# The producer names this vocabulary (depth_ratings.THIN_LABELS) -- copying the two literals
# here again is how a rename to the label goes SILENT rather than loud: nothing would match,
# and this module would simply stop ever flagging a thin position.
_THIN_LABELS = depth_ratings.THIN_LABELS


def compute_readiness(
    roster_table: list[dict], depth: dict, my_team_label: Optional[str], total_starting_slots: int,
) -> dict:
    """roster_table: this app's own per-player rows (slot/position/injury_status already set).
    depth: positional_depth(player_universe, merger)'s own output -- team_label -> position ->
    {"count", "value"}. my_team_label: this team's key into `depth`, or None if unresolved.
    total_starting_slots: len(lineup_optimizer.slots_from_roster_positions(...)) -- the
    league's own real starting-slot count, not re-derived here.

    Returns {"total_starting_slots", "filled_starting_slots", "starter_injury_flags",
    "thin_positions"} -- every field a direct read or a reuse of an existing judgment.

    EACH `thin_positions` ENTRY IS `{"position", "label", "count", "valued_count"}`, and that
    shape is part of this function's contract rather than an implementation detail (`#339`).
    `front_claims.compose` reads all four; when this returned only the first two it substituted
    0 for the count, the renderer printed "0 rostered" about a two-man room, and the band's
    ordering silently fell back to the alphabet. Both sides had passing tests and neither
    crossed the interface, so nothing caught it. A consumer may ignore a field; it may not be
    handed a quantity the cell already measured and then be blamed for inventing one."""
    filled_starting_slots = sum(1 for r in roster_table if r.get("slot") == "Starter")
    # "a REAL injury_status" -- the docstring's own word, now enforced rather than assumed
    # (#191). A Questionable starter is not a lineup problem, and raising him as one spends a
    # person's attention on a designation the engine has measured as carrying nothing.
    starter_injury_flags = [
        {"name": r["name"], "position": r["position"], "injury_status": r["injury_status"]}
        for r in roster_table
        if r.get("slot") == "Starter" and player_universe.is_material_injury_status(r.get("injury_status"))
    ]
    thin_positions = []
    if my_team_label and my_team_label in depth:
        for position in sorted(depth[my_team_label]):
            peer_cells = [teams[position] for teams in depth.values() if position in teams]
            # DIRECT, not `.get(position, {...})`. The loop iterates the keys of this very
            # dict, so the default was unreachable -- and it declared `{"count": 0,
            # "value": None}`, which is NOT the cell `positional_depth` builds
            # (`{"count", "value", "valued_count"}`). A dead default that disagrees with the
            # real shape is a miniature of the defect `#339` is about: had it ever fired it
            # would have emitted an entry missing `valued_count`.
            cell = depth[my_team_label][position]
            label = depth_ratings.depth_label(cell, peer_cells)
            if label in _THIN_LABELS:
                # COUNT AND VALUED_COUNT TRAVEL WITH THE LABEL (`#339`). The cell already
                # holds both at this moment and this function used to return only the label,
                # so `front_claims.compose` -- which reads `count` and `valued_count` --
                # substituted 0 and None, and the renderer printed "0 rostered" for a room
                # holding two tight ends. Worse quietly: `thin_sort_key` is
                # `(count, position)`, so with every count 0 the band's order collapsed to
                # the ALPHABET, the exact defect that function was written to prevent.
                #
                # `valued_count` IS NOT `count` (`#190`): every rostered player raises count,
                # only the priced ones raise valued_count, so the two describe different sets
                # and a consumer holding both can say "at least" instead of "is". Measured
                # there on a real capture: 33 of 96 cells had 0 < valued_count < count.
                thin_positions.append({
                    "position": position, "label": label,
                    "count": cell["count"], "valued_count": cell.get("valued_count"),
                })
    return {
        "total_starting_slots": total_starting_slots,
        "filled_starting_slots": filled_starting_slots,
        "starter_injury_flags": starter_injury_flags,
        "thin_positions": thin_positions,
    }
