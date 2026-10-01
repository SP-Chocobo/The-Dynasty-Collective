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

# THE LABEL VOCABULARY, BOUND ONCE. Every one of these strings used to be hand-copied at each
# consumer -- the "no rostered players" one in four separate places (this module, two app.py
# sites, lineup_readiness) -- and they failed ASYMMETRICALLY under a rename: the two membership
# tests would go quietly silent (nothing matches, no thin position ever flagged again) while
# the Trade Calculator's own _DEPTH_RANK lookup would silently RECLASSIFY every empty position
# room as "Average", i.e. as measured mid-league depth. A rename must break loudly or not at
# all, so the producer names the vocabulary and every consumer imports it. Note the docstring
# above this module's own code wrote the em dash as an ASCII "--" and so already disagreed
# with the string it was describing; that is exactly the drift this closes.
STRONG = "Strong"
AVERAGE = "Average"
WEAK = "Weak"
NO_PLAYERS_LABEL = "None — no rostered players here"

#: Every label depth_label can return. None is NOT in here on purpose -- it is the absence
#: state ("cannot be measured"), not a rating, and a consumer that maps it to a rating is the
#: defect this vocabulary exists to make visible.
LABELS = (STRONG, AVERAGE, WEAK, NO_PLAYERS_LABEL)

#: The two labels that mean "this position room is a problem" -- shared by every surface that
#: flags thin positions, so "thin" cannot come to mean different things on two screens.
THIN_LABELS = (WEAK, NO_PLAYERS_LABEL)


def depth_label(cell: dict, peer_cells: list[dict]) -> Optional[str]:
    """cell: {"count": int, "value": Optional[float]} for the team/position being rated.
    peer_cells: the same shape for every team at this position (include the team's own cell,
    matching the original's "average over every team, self included" behavior).

    Returns STRONG / AVERAGE / WEAK / NO_PLAYERS_LABEL (the team has zero players at this
    position) / None (no peer data exists to compare against at all --
    an absolute cutoff means nothing, since a 2-team best-ball league and a 14-team dynasty
    league have very different "normal" depth)."""
    if not peer_cells:
        return None
    if cell["count"] == 0:
        return NO_PLAYERS_LABEL
    use_value = cell["value"] is not None and all(c["value"] is not None for c in peer_cells)
    avg = (sum(c["value"] for c in peer_cells) if use_value else sum(c["count"] for c in peer_cells)) / len(peer_cells)
    if not avg:
        return None
    ratio = (cell["value"] if use_value else cell["count"]) / avg
    return STRONG if ratio >= _STRONG_RATIO else WEAK if ratio <= _WEAK_RATIO else AVERAGE
