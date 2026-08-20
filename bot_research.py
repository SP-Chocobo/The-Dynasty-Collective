"""
Durable log of panel-vetted findings from the debate bots' own live web search -- see
llm_engine.MODERATOR_SYSTEM_PROMPT's SOURCE FINDING instructions for exactly when the
Moderator is allowed to write one (a specific, named-source claim about a player's value/
ranking/status that the whole panel, Contrarian very much included, did not successfully
dispute). Global and git-tracked, unlike decision_log/todo_log's per-league, gitignored
JSON -- a finding about a real player's value isn't scoped to one league, and the entire
point is for it to persist across sessions the same durable way the rest of data/baseline/
does: feeding future debates as reference context, and -- when it carries a real rank
number, not just a qualitative claim -- DataMerger's own composite score, not just the one
answer it came from.

Append-only: a later finding about the same player/source doesn't overwrite or delete an
earlier one here, it just outranks it at READ time (see DataMerger's newest-wins handling,
the same pattern every other baseline source already uses) -- the full log stays a real
record of what the panel has found over time, not just today's latest opinion.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

FINDINGS_PATH = Path("data/baseline/bot_research.json")


def load_findings() -> list[dict]:
    if FINDINGS_PATH.exists():
        try:
            return json.loads(FINDINGS_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save(entries: list[dict]) -> None:
    FINDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    FINDINGS_PATH.write_text(json.dumps(entries, indent=2))


def _next_id(entries: list[dict]) -> int:
    return (max((e.get("id", 0) for e in entries), default=0)) + 1


def add_finding(
    player_name: str, source: str, claim: str, *, rank: Optional[int] = None,
    conviction: str = "", question: str = "", league_id: Optional[str] = None,
) -> Optional[int]:
    """Persist one panel-vetted finding. Returns its id, or None if there's nothing real to
    record (blank player/source/claim) -- a no-op, not an error, since the Moderator's SOURCE
    FINDING line is optional and legitimately absent from most verdicts."""
    if not player_name.strip() or not source.strip() or not claim.strip():
        return None
    entries = load_findings()
    new_id = _next_id(entries)
    entries.append({
        "id": new_id,
        "ts": time.time(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "player_name": player_name.strip(),
        "source": source.strip(),
        "claim": claim.strip(),
        "rank": rank,
        "conviction": conviction,
        "question": question,
        "league_id": league_id,
    })
    _save(entries)
    return new_id


def findings_for_context(limit: int = 30) -> list[dict]:
    """Most recent findings first, capped -- for build_context's reference-material-style
    section in app.py, same cap-a-long-history posture as captioned reference material there
    already has, so accumulated findings don't balloon every context payload indefinitely."""
    return sorted(load_findings(), key=lambda e: e.get("ts", 0), reverse=True)[:limit]
