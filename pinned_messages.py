"""
Per-league record of chat messages the user has manually pinned.

Distinct from the Decision Log (only ever the Moderator's own structured
verdicts) and Objectives (only the Moderator's own action items) -- this is
personal curation, independent of what the panel itself thought was worth
recording. A pinned message stays available for the bots to reference if a
later question calls for it (see app.py's build_context wiring), but pinning
is never treated as elevating a message's importance above anything else
already in context -- it's a findability aid, not a priority signal.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

PINS_DIR = Path("data/pins")


def _path(league_id: str) -> Path:
    return PINS_DIR / f"{league_id}.json"


def load_pinned_ts(league_id: str) -> set[float]:
    """The set of chat message timestamps -- each message's stable id within one
    league's chat_history -- the user has pinned."""
    path = _path(league_id)
    if path.exists():
        try:
            return set(json.loads(path.read_text()))
        except (json.JSONDecodeError, OSError):
            return set()
    return set()


def toggle_pin(league_id: str, ts: float) -> bool:
    """Flip one message's pinned state. Returns the new state (True = now pinned)."""
    pinned = load_pinned_ts(league_id)
    if ts in pinned:
        pinned.discard(ts)
        now_pinned = False
    else:
        pinned.add(ts)
        now_pinned = True
    PINS_DIR.mkdir(parents=True, exist_ok=True)
    _path(league_id).write_text(json.dumps(sorted(pinned)))
    return now_pinned


def forget_pins(league_id: str) -> None:
    """Delete this league's pins entirely (used by hard league delete)."""
    path = _path(league_id)
    if path.exists():
        path.unlink()


def find_relevant(messages: list[dict], pinned_ts: set[float], query: str, limit: int = 5) -> list[dict]:
    """Keyword-overlap match against pinned message content -- pins are retrieved only when
    the current question actually seems to relate to one, never injected into every context by
    default. Automatic injection would let an old, once-useful observation quietly bias every
    future debate forever (pin a stale take on a player once, have it silently color every
    debate about him for the rest of the season) -- retrieval-on-relevance avoids that; pinning
    means "don't let this get lost," not "always weigh this." Same technique as
    decision_log.search_decisions_with_outcomes.
    """
    if not query or not query.strip() or not pinned_ts:
        return []
    # No apostrophe in the character class -- "Golden's" tokenizing to "golden's" (rather
    # than "golden") would silently fail to overlap with a query that just says "Golden",
    # which is exactly the kind of miss this feature can't afford at an overlap>=2 bar.
    query_words = {w for w in re.findall(r"[a-zA-Z0-9]+", query.lower()) if len(w) > 2}
    if not query_words:
        return []
    scored = []
    for msg in messages:
        if msg.get("ts") not in pinned_ts:
            continue
        content_words = set(re.findall(r"[a-zA-Z0-9]+", msg.get("content", "").lower()))
        overlap = len(query_words & content_words)
        # >=2, not just any overlap (decision_log's own search accepts a single word) -- a pin
        # is meant to surface on an actual reference, and one shared common word ("week",
        # "team") produces exactly the false-positive-topic-drift this feature exists to avoid.
        if overlap >= 2:
            scored.append((overlap, msg))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [msg for _, msg in scored[:limit]]
