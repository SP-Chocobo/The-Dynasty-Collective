"""
Per-league to-do list — active league objectives, not a bare checklist. An
open item is structured, referenceable context (by a stable small id, not a
float timestamp) that future debates can be given so what the team is still
trying to accomplish can shape a recommendation, not just be a record of past
verdicts. Bots can create these (from a Moderator ACTION ITEM), revise one
when new information changes the objective, and flag one as likely done —
but never silently close or delete one. The user has final say on actually
finishing an item; a bot can only propose "Likely Resolved" with a reason,
pending confirmation. Resolved/dismissed items are archived (kept, with a
reason and date), never destroyed, so they remain useful as history.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

TODOS_DIR = Path("data/todos")

ACTIVE_STATUSES = ("active", "likely_resolved")
ARCHIVED_STATUSES = ("resolved", "dismissed")


def _path(league_id: str) -> Path:
    return TODOS_DIR / f"{league_id}.json"


def _load(league_id: str) -> list[dict]:
    path = _path(league_id)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save(league_id: str, entries: list[dict]) -> None:
    TODOS_DIR.mkdir(parents=True, exist_ok=True)
    _path(league_id).write_text(json.dumps(entries, indent=2))


def _next_id(entries: list[dict]) -> int:
    return (max((e.get("id", 0) for e in entries), default=0)) + 1


def _find(entries: list[dict], todo_id: int) -> Optional[dict]:
    return next((e for e in entries if e.get("id") == todo_id), None)


def add_todo(
    league_id: str, text: str, *, source: str = "manual", question: str = "",
    decision_ts: Optional[float] = None,
) -> Optional[int]:
    """Create one active objective. Returns its id, or None if there was nothing to track
    (blank text/league) — a no-op, not an error, since a blank ACTION ITEM is expected
    whenever the Moderator genuinely has nothing new worth tracking."""
    if not league_id or not text.strip():
        return None
    entries = _load(league_id)
    new_id = _next_id(entries)
    entries.append(
        {
            "id": new_id,
            "ts": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "text": text.strip(),
            "source": source,  # "moderator" or "manual"
            "question": question,
            "decision_ts": decision_ts,
            "status": "active",
            "resolution_reason": "",
            "resolution_date": None,
            "revisions": [],
            "notes": [],
        }
    )
    _save(league_id, entries)
    return new_id


def add_note(league_id: str, todo_id: int, text: str) -> bool:
    """A free-form note the user attaches to an objective — distinct from `revisions`
    (which tracks the objective's own text changing) and `resolution_reason` (why it
    closed). Notes persist on the entry regardless of status, so anything added while
    it was still open travels with it into the archive once resolved/dismissed."""
    if not text.strip():
        return False
    entries = _load(league_id)
    entry = _find(entries, todo_id)
    if not entry:
        return False
    entry.setdefault("notes", []).append(
        {"ts": time.time(), "date": datetime.now().strftime("%Y-%m-%d"), "text": text.strip()}
    )
    _save(league_id, entries)
    return True


def revise_todo(league_id: str, todo_id: int, new_text: str, reason: str = "") -> bool:
    """Update an active objective's text when new information changes it — the old text
    is kept in `revisions`, not overwritten silently. No-op (returns False) if the item
    isn't found or isn't active (a resolved/dismissed item is archived, not editable)."""
    if not new_text.strip():
        return False
    entries = _load(league_id)
    entry = _find(entries, todo_id)
    if not entry or entry.get("status") not in ACTIVE_STATUSES:
        return False
    entry.setdefault("revisions", []).append(
        {"ts": time.time(), "date": datetime.now().strftime("%Y-%m-%d"), "text": entry["text"], "reason": reason}
    )
    entry["text"] = new_text.strip()
    _save(league_id, entries)
    return True


def mark_likely_resolved(league_id: str, todo_id: int, reason: str) -> bool:
    """A bot's proposal that an objective looks done — pending, not final. Only valid
    from "active"; doesn't touch resolution_date, since nothing is actually resolved yet."""
    entries = _load(league_id)
    entry = _find(entries, todo_id)
    if not entry or entry.get("status") != "active":
        return False
    entry["status"] = "likely_resolved"
    entry["resolution_reason"] = reason.strip()
    _save(league_id, entries)
    return True


def mark_referenced(league_id: str, todo_id: int) -> bool:
    """Stamp that a debate turn actually engaged with this objective (mentioned it by id
    in the Moderator's response), not just that it was sitting in context unused. Purely
    informational — doesn't touch status — lets the UI show a "referenced" signal instead
    of leaving every active objective looking equally (un)used."""
    entries = _load(league_id)
    entry = _find(entries, todo_id)
    if not entry:
        return False
    entry["last_referenced"] = datetime.now().strftime("%Y-%m-%d")
    _save(league_id, entries)
    return True


def reopen_todo(league_id: str, todo_id: int) -> bool:
    """The user rejects a "Likely Resolved" proposal — back to active, proposal cleared."""
    entries = _load(league_id)
    entry = _find(entries, todo_id)
    if not entry or entry.get("status") not in ACTIVE_STATUSES:
        return False
    entry["status"] = "active"
    entry["resolution_reason"] = ""
    _save(league_id, entries)
    return True


def resolve_todo(league_id: str, todo_id: int, reason: Optional[str] = None) -> bool:
    """User confirms an objective is actually finished — from "active" directly (they
    just know it's done) or from "likely_resolved" (confirming the bot's proposal, in
    which case the existing proposed reason is kept unless a new one is explicitly given —
    `reason=None`, not just an empty string, is what means "don't override it")."""
    entries = _load(league_id)
    entry = _find(entries, todo_id)
    if not entry or entry.get("status") not in ACTIVE_STATUSES:
        return False
    entry["status"] = "resolved"
    if reason and reason.strip():
        entry["resolution_reason"] = reason.strip()
    elif not entry.get("resolution_reason"):
        entry["resolution_reason"] = "Marked done by user"
    entry["resolution_date"] = datetime.now().strftime("%Y-%m-%d")
    _save(league_id, entries)
    return True


def dismiss_todo(league_id: str, todo_id: int, reason: str = "Dismissed by user") -> bool:
    """User calls off an objective without it ever being 'done' (no longer relevant,
    was a bad idea, overtaken by events) — still archived with a reason, not deleted."""
    entries = _load(league_id)
    entry = _find(entries, todo_id)
    if not entry or entry.get("status") not in ACTIVE_STATUSES:
        return False
    entry["status"] = "dismissed"
    entry["resolution_reason"] = reason.strip() or "Dismissed by user"
    entry["resolution_date"] = datetime.now().strftime("%Y-%m-%d")
    _save(league_id, entries)
    return True


def delete_todo(league_id: str, todo_id: int) -> bool:
    """Full erasure — distinct from resolve/dismiss, which archive (kept for reference,
    with a reason/date) rather than remove. This actually drops the entry from the
    league's file; there's no undo. Meant for a mistaken/duplicate/spam entry, not for
    "this objective is done" — use resolve_todo or dismiss_todo for that."""
    entries = _load(league_id)
    remaining = [e for e in entries if e.get("id") != todo_id]
    if len(remaining) == len(entries):
        return False
    _save(league_id, remaining)
    return True


def load_todos(league_id: str, *, statuses: Optional[tuple[str, ...]] = None) -> list[dict]:
    entries = _load(league_id)
    if statuses:
        entries = [e for e in entries if e.get("status") in statuses]
    return entries


def search_archived(league_id: str, query: str, limit: int = 5) -> list[dict]:
    """Keyword-overlap search over resolved/dismissed objectives — the "queryable strategic
    memory" that lets a new question (about a player, a manager, a trade idea) surface why a
    similar objective was previously closed, instead of the bots treating it as a brand-new
    investigation every time. Not full-text search, just a plain word-overlap score, highest
    first, capped at `limit` — good enough to catch "Player X" showing up again."""
    if not query or not query.strip():
        return []
    query_words = {w for w in re.findall(r"[a-zA-Z0-9']+", query.lower()) if len(w) > 2}
    if not query_words:
        return []
    scored = []
    for entry in load_todos(league_id, statuses=ARCHIVED_STATUSES):
        haystack = f"{entry.get('text', '')} {entry.get('question', '')}".lower()
        entry_words = set(re.findall(r"[a-zA-Z0-9']+", haystack))
        overlap = len(query_words & entry_words)
        if overlap:
            scored.append((overlap, entry))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [entry for _, entry in scored[:limit]]


def forget_todos(league_id: str) -> None:
    """Delete this league's to-do list entirely (used by hard league delete)."""
    path = _path(league_id)
    if path.exists():
        path.unlink()
