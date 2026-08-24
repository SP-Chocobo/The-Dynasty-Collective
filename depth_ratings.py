"""Peer-relative depth rating -- Strong/Average/Weak/None, shared by every surface that needs
to say "how does this team's depth at this position compare to the rest of the league."

First built inside the Trade Calculator (app.py's own `_depth_label` closure); extracted here
(per Fable's League design review, finding F3) so the League Depth Map consumes the exact same
judgment instead of growing a second, independently-tuned opinion that could quietly drift
from this one. Thresholds are unchanged from the original -- relocated, not re-derived or
re-validated.
"""

from __future__ import annotations

from typing import Optional

# Unchanged from the original Trade Calculator closure: >=1.3x the league-average at this
# position is Strong, <=0.7x is Weak, otherwise Average. Not re-tuned here.
_STRONG_RATIO = 1.3
_WEAK_RATIO = 0.7


def depth_label(cell: dict, peer_cells: list[dict]) -> Optional[str]:
    """cell: {"count": int, "value": Optional[float]} for the team/position being rated.
    peer_cells: the same shape for every team at this position (include the team's own cell,
    matching the original's "average over every team, self included" behavior).

    Returns "Strong" / "Average" / "Weak" / "None -- no rostered players here" (the team has
    zero players at this position) / None (no peer data exists to compare against at all --
    an absolute cutoff means nothing, since a 2-team best-ball league and a 14-team dynasty
    league have very different "normal" depth)."""
    if not peer_cells:
        return None
    if cell["count"] == 0:
        return "None — no rostered players here"
    use_value = cell["value"] is not None and all(c["value"] is not None for c in peer_cells)
    avg = (sum(c["value"] for c in peer_cells) if use_value else sum(c["count"] for c in peer_cells)) / len(peer_cells)
    if not avg:
        return None
    ratio = (cell["value"] if use_value else cell["count"]) / avg
    return "Strong" if ratio >= _STRONG_RATIO else "Weak" if ratio <= _WEAK_RATIO else "Average"
