"""
Manual league format override — Best Ball and Chopped mode.

Sleeper's public API reliably exposes dynasty/keeper/redraft via
settings.type (see sleeper_client.league_format_summary), which has been
used since early in this project without issue. Best Ball and "Chopped"
(a newer, elimination-style Sleeper mode: no 1v1 matchups, the whole field
competes each week, the lowest scorer is eliminated and their roster hits
waivers, trades disabled) are a different matter — their exact API
encoding hasn't been verified against a live league in this dev environment,
so rather than guess a field name and risk silent misdetection, this is a
manual, explicit, per-league override the user sets themselves. Always
correct regardless of what Sleeper's actual field turns out to be.

Keyed by league_id (a property of the league itself), not by Sleeper user
like league_prefs.py's display ordering/archiving.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
import store_io


FORMATS_PATH = Path("data/league_formats.json")

STANDARD = "Standard"
BEST_BALL = "Best Ball"
CHOPPED = "Chopped"
FORMAT_OPTIONS = (STANDARD, BEST_BALL, CHOPPED)

# Strategic guidance injected into the debate context when a league is marked
# as one of these — not just a label, since the reasoning genuinely differs.
FORMAT_GUIDANCE = {
    BEST_BALL: (
        "This league is BEST BALL: your highest-scoring eligible lineup is selected automatically "
        "each week — there is no start/sit decision, and typically no waivers or trades either "
        "(rosters are usually locked after the draft). Most week-to-week roster-management questions "
        "don't apply here. If asked one anyway, say so plainly rather than inventing a start/sit call "
        "that doesn't exist in this format, and redirect toward what's actually decidable: draft-day "
        "roster construction, depth at each position, and bye-week/stacking coverage across your "
        "*whole* roster (since every rostered player can produce a scoring week, not just starters)."
    ),
    CHOPPED: (
        "This league is CHOPPED: there are no 1v1 matchups — every team competes against the entire "
        "field each week, and the single lowest scorer is ELIMINATED, their full roster dumped onto "
        "waivers. Trades are disabled in this format — never suggest or evaluate a trade here. "
        "Start/sit calls should weight floor and safety over ceiling more than in a normal league: "
        "surviving one bad week against the whole field matters more than a boom week against one "
        "opponent, since elimination is about not being dead last, not about outscoring a specific "
        "team. Treat 'standing' as distance from the elimination cutoff, not win-loss record. Because "
        "eliminated teams' full rosters hit waivers at once (not a gradual drip), the free-agent pool "
        "can shift sharply week to week — weigh that when reasoning about pickups."
    ),
}


def _load_all() -> dict:
    # #102: atomic, locked, and no longer able to turn a torn read into an empty store
    # that the next write persists -- see store_io's own docstring for the measurement.
    return store_io.read(FORMATS_PATH, {})


def _save_all(data: dict) -> None:
    store_io.write(FORMATS_PATH, data)


def get_format_override(league_id: str) -> Optional[str]:
    """None means no override — treat the league as standard (normal week-to-week management)."""
    return _load_all().get(league_id)


@store_io.atomic(lambda *a, **k: FORMATS_PATH)
def set_format_override(league_id: str, format_value: Optional[str]) -> None:
    """Pass None or STANDARD to clear the override."""
    data = _load_all()
    if not format_value or format_value == STANDARD:
        data.pop(league_id, None)
    else:
        data[league_id] = format_value
    _save_all(data)
