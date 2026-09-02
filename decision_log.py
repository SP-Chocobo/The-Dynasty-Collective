"""
Per-league record of every Moderator verdict — a plain audit trail so the
user can look back later and see whether the front office's calls actually
held up, rather than trusting the panel's track record from memory.

Kept dead simple: one JSON list per league, newest entries appended.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import store_io


DECISIONS_DIR = Path("data/decisions")
OUTCOME_LABELS = ("Worked", "Didn't Work", "Mixed", "Too Early To Tell")


def _path(league_id: str) -> Path:
    return DECISIONS_DIR / f"{league_id}.json"


def _load(league_id: str) -> list[dict]:
    # #102: atomic, locked, and no longer able to turn a torn read into an empty store that the
    # next write persists -- see store_io's own docstring for the measurement.
    return store_io.read(_path(league_id), [])


@store_io.atomic(lambda league_id, *a, **k: _path(league_id))
def log_decision(
    league_id: str, question: str, verdict: dict, moderator_text: str,
    provider: str = "", model: str = "",
) -> None:
    """Append one decision. No-op if there's no league selected or no verdict to record
    (e.g. the Moderator errored, or didn't follow the structured format at all).

    provider/model record what actually produced this verdict, by the same rule
    app.append_message already applies to every chat message: a role can be reassigned to a
    different provider or model later, and an old record must keep showing who answered it
    rather than whatever is currently configured. Both default to empty so a caller that
    does not know (and every row written before this existed) stays valid -- absent means
    "not recorded", never "the default model".
    """
    if not league_id or not verdict:
        return
    DECISIONS_DIR.mkdir(parents=True, exist_ok=True)
    entries = _load(league_id)
    entries.append(
        {
            "ts": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "question": question,
            "recommendation": verdict.get("recommendation", ""),
            "conviction": verdict.get("conviction", ""),
            "reason": verdict.get("reason", ""),
            "dissent": verdict.get("dissent", ""),
            "risk": verdict.get("risk", ""),
            "recon": verdict.get("recon", ""),
            "price_ceiling": verdict.get("price_ceiling", ""),
            "alternative": verdict.get("alternative", ""),
            "moderator_text": moderator_text,
            "provider": provider,
            "model": model,
            "outcome": "",
            "outcome_note": "",
            "outcome_date": None,
        }
    )
    store_io.write(_path(league_id), entries)


@store_io.atomic(lambda league_id, *a, **k: _path(league_id))
def set_outcome(league_id: str, ts: float, outcome: str, note: str = "") -> bool:
    """Record how a past call actually played out — the missing piece that turns this
    from a pure audit trail into something the bots can learn from. `ts` identifies the
    entry (decisions have no separate int id; timestamp is already unique per entry)."""
    entries = _load(league_id)
    entry = next((e for e in entries if e.get("ts") == ts), None)
    if not entry:
        return False
    entry["outcome"] = outcome
    entry["outcome_note"] = note.strip()
    entry["outcome_date"] = datetime.now().strftime("%Y-%m-%d")
    store_io.write(_path(league_id), entries)
    return True


def search_decisions_with_outcomes(league_id: str, query: str, limit: int = 5) -> list[dict]:
    """Keyword-overlap search over decisions that actually have a recorded outcome — an
    unrated decision has nothing to teach a future one, so it's excluded rather than
    surfaced as if "no outcome yet" were itself informative."""
    if not query or not query.strip():
        return []
    query_words = {w for w in re.findall(r"[a-zA-Z0-9']+", query.lower()) if len(w) > 2}
    if not query_words:
        return []
    scored = []
    for entry in _load(league_id):
        if not entry.get("outcome"):
            continue
        haystack = f"{entry.get('question', '')} {entry.get('reason', '')}".lower()
        entry_words = set(re.findall(r"[a-zA-Z0-9']+", haystack))
        overlap = len(query_words & entry_words)
        if overlap:
            scored.append((overlap, entry))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [entry for _, entry in scored[:limit]]


def load_decisions(league_id: str) -> list[dict]:
    return _load(league_id)


def forget_decisions(league_id: str) -> None:
    """Delete this league's decision log entirely (used by hard league delete)."""
    path = _path(league_id)
    if path.exists():
        path.unlink()
