"""
Per-Sleeper-user league display preferences.

Sleeper has no concept of hiding or reordering leagues in its API — that's
purely a front-end convenience, so it's tracked here and persisted to
data/league_prefs.json, keyed by Sleeper user_id, independent of which
league is currently selected.
"""

from __future__ import annotations

import json
from pathlib import Path

PREFS_PATH = Path("data/league_prefs.json")


def _load_all() -> dict:
    if PREFS_PATH.exists():
        try:
            return json.loads(PREFS_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_all(data: dict) -> None:
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREFS_PATH.write_text(json.dumps(data, indent=2))


def get_prefs(user_id: str) -> dict:
    """{'order': [league_id, ...], 'archived': [league_id, ...]} for one Sleeper user."""
    return _load_all().get(user_id, {"order": [], "archived": []})


def _set_prefs(user_id: str, prefs: dict) -> None:
    data = _load_all()
    data[user_id] = prefs
    _save_all(data)


def _full_order(user_id: str, leagues: list[dict]) -> list[str]:
    """All discovered league ids, saved order first, newly-discovered ones appended."""
    prefs = get_prefs(user_id)
    discovered_ids = [lg["league_id"] for lg in leagues]
    ordered_ids = [lid for lid in prefs.get("order", []) if lid in discovered_ids]
    new_ids = [lid for lid in discovered_ids if lid not in ordered_ids]
    return ordered_ids + new_ids


def sorted_leagues(user_id: str, leagues: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split leagues into (visible, archived), both in the user's saved display order."""
    prefs = get_prefs(user_id)
    archived_ids = set(prefs.get("archived", []))
    by_id = {lg["league_id"]: lg for lg in leagues}

    visible, archived = [], []
    for lid in _full_order(user_id, leagues):
        (archived if lid in archived_ids else visible).append(by_id[lid])
    return visible, archived


def toggle_archive(user_id: str, league_id: str) -> None:
    prefs = get_prefs(user_id)
    archived = set(prefs.get("archived", []))
    archived.symmetric_difference_update({league_id})
    prefs["archived"] = list(archived)
    _set_prefs(user_id, prefs)


def move_league(user_id: str, leagues: list[dict], league_id: str, direction: int) -> None:
    """direction: -1 moves the league earlier in the display order, +1 moves it later."""
    order = _full_order(user_id, leagues)
    idx = order.index(league_id)
    new_idx = idx + direction
    if 0 <= new_idx < len(order):
        order[idx], order[new_idx] = order[new_idx], order[idx]
    prefs = get_prefs(user_id)
    prefs["order"] = order
    _set_prefs(user_id, prefs)
