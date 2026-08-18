"""
Reference material — screenshots of notifications, articles, injury news,
or anything else worth having on hand to prompt the debate panel, but that
isn't structured player-projection data. Nothing here is parsed or
auto-matched to player records; a user-written caption is the only text
that reaches the LLM context (see app.build_context()'s REFERENCE MATERIAL
section) — the raw file itself is just stored for the user to view.

Each item has an explicit scope, chosen by the user at upload time (never
auto-inferred — a screenshot's text can't reliably reveal whether it's a
universal fact or one-league-specific commentary):
  * league_ids = None or [] -> global: a real-world fact (an injury report,
    a depth chart) that's true regardless of which league you're asking
    about, so it's included for every league's debate context.
  * league_ids = [id, ...] -> scoped to just those leagues: commentary tied
    to specific rosters/trade dynamics (e.g. "considering trading my 2nd for
    their WR1") that would be noise, or actively misleading, in an unrelated
    league's context.
The actual file always lives in one shared data/attachments/ directory
regardless of scope — only the metadata differs — so changing an item's
scope later never requires moving files around.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

ATTACHMENTS_DIR = Path("data/attachments")
CAPTIONS_PATH = ATTACHMENTS_DIR / "captions.json"

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")
ATTACHMENT_EXTENSIONS = IMAGE_EXTENSIONS + (".pdf", ".txt")


def _load_captions() -> dict:
    if CAPTIONS_PATH.exists():
        try:
            return json.loads(CAPTIONS_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_captions(captions: dict) -> None:
    ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
    CAPTIONS_PATH.write_text(json.dumps(captions, indent=2))


def save_attachment(filename: str, data: bytes, caption: str = "",
                     league_ids: Optional[list[str]] = None) -> str:
    """Save an uploaded file, returning the stored filename (deduped if one already exists)."""
    ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = ATTACHMENTS_DIR / filename
    if dest.exists():
        dest = ATTACHMENTS_DIR / f"{dest.stem}_{int(time.time())}{dest.suffix}"
    dest.write_bytes(data)

    captions = _load_captions()
    captions[dest.name] = {"caption": caption, "uploaded_at": time.time(), "league_ids": league_ids or None}
    _save_captions(captions)
    return dest.name


def set_caption(filename: str, caption: str) -> None:
    captions = _load_captions()
    captions.setdefault(filename, {})["caption"] = caption
    captions[filename].setdefault("uploaded_at", time.time())
    captions[filename].setdefault("league_ids", None)
    _save_captions(captions)


def set_scope(filename: str, league_ids: Optional[list[str]]) -> None:
    """league_ids=None (or []) makes an item global; a list scopes it to just those leagues."""
    captions = _load_captions()
    captions.setdefault(filename, {})["league_ids"] = league_ids or None
    captions[filename].setdefault("caption", "")
    captions[filename].setdefault("uploaded_at", time.time())
    _save_captions(captions)


def list_attachments(league_id: Optional[str] = None) -> list[dict]:
    """[{filename, path, caption, uploaded_at, is_image, league_ids}], newest first.

    Pass league_id to filter to what's visible from that league (global items
    plus anything scoped to include it). Omit it to see everything regardless
    of scope, e.g. for a management UI that lists all uploads.
    """
    if not ATTACHMENTS_DIR.exists():
        return []
    captions = _load_captions()
    items = []
    for p in ATTACHMENTS_DIR.iterdir():
        if p.suffix.lower() not in ATTACHMENT_EXTENSIONS:
            continue
        meta = captions.get(p.name, {})
        item_league_ids = meta.get("league_ids") or None
        if league_id is not None and item_league_ids is not None and league_id not in item_league_ids:
            continue
        items.append({
            "filename": p.name,
            "path": p,
            "caption": meta.get("caption", ""),
            "uploaded_at": meta.get("uploaded_at", p.stat().st_mtime),
            "is_image": p.suffix.lower() in IMAGE_EXTENSIONS,
            "league_ids": item_league_ids,
        })
    items.sort(key=lambda i: i["uploaded_at"], reverse=True)
    return items


def delete_attachment(filename: str) -> None:
    (ATTACHMENTS_DIR / filename).unlink(missing_ok=True)
    captions = _load_captions()
    if captions.pop(filename, None) is not None:
        _save_captions(captions)
