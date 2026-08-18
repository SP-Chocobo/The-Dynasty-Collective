"""
Per-league record of every Moderator verdict — a plain audit trail so the
user can look back later and see whether the front office's calls actually
held up, rather than trusting the panel's track record from memory.

Kept dead simple: one JSON list per league, newest entries appended.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

DECISIONS_DIR = Path("data/decisions")


def _path(league_id: str) -> Path:
    return DECISIONS_DIR / f"{league_id}.json"


def _load(league_id: str) -> list[dict]:
    path = _path(league_id)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []


def log_decision(league_id: str, question: str, verdict: dict, moderator_text: str) -> None:
    """Append one decision. No-op if there's no league selected or no verdict to record
    (e.g. the Moderator errored, or didn't follow the structured format at all)."""
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
            "moderator_text": moderator_text,
        }
    )
    _path(league_id).write_text(json.dumps(entries, indent=2))


def load_decisions(league_id: str) -> list[dict]:
    return _load(league_id)


def forget_decisions(league_id: str) -> None:
    """Delete this league's decision log entirely (used by hard league delete)."""
    path = _path(league_id)
    if path.exists():
        path.unlink()
