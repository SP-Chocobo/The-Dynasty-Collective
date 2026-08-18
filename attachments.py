"""
Reference material — screenshots of notifications, articles, injury news,
or anything else worth having on hand to prompt the debate panel, but that
isn't structured player-projection data. Nothing here is parsed or
auto-matched to player records; a user-written caption is the only text
that reaches the LLM context (see app.build_context()'s REFERENCE MATERIAL
section) — the raw file itself is just stored for the user to view.

Global rather than per-league: a screenshot of real-world injury news isn't
tied to any fantasy scoring format or roster, unlike Draft Sharks' data.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

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


def save_attachment(filename: str, data: bytes, caption: str = "") -> str:
    """Save an uploaded file, returning the stored filename (deduped if one already exists)."""
    ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = ATTACHMENTS_DIR / filename
    if dest.exists():
        dest = ATTACHMENTS_DIR / f"{dest.stem}_{int(time.time())}{dest.suffix}"
    dest.write_bytes(data)

    captions = _load_captions()
    captions[dest.name] = {"caption": caption, "uploaded_at": time.time()}
    _save_captions(captions)
    return dest.name


def set_caption(filename: str, caption: str) -> None:
    captions = _load_captions()
    captions.setdefault(filename, {})["caption"] = caption
    captions[filename].setdefault("uploaded_at", time.time())
    _save_captions(captions)


def list_attachments() -> list[dict]:
    """[{filename, path, caption, uploaded_at, is_image}], newest first."""
    if not ATTACHMENTS_DIR.exists():
        return []
    captions = _load_captions()
    items = []
    for p in ATTACHMENTS_DIR.iterdir():
        if p.suffix.lower() not in ATTACHMENT_EXTENSIONS:
            continue
        meta = captions.get(p.name, {})
        items.append({
            "filename": p.name,
            "path": p,
            "caption": meta.get("caption", ""),
            "uploaded_at": meta.get("uploaded_at", p.stat().st_mtime),
            "is_image": p.suffix.lower() in IMAGE_EXTENSIONS,
        })
    items.sort(key=lambda i: i["uploaded_at"], reverse=True)
    return items


def delete_attachment(filename: str) -> None:
    (ATTACHMENTS_DIR / filename).unlink(missing_ok=True)
    captions = _load_captions()
    if captions.pop(filename, None) is not None:
        _save_captions(captions)
