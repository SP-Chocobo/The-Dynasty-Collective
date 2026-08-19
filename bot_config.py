"""
Which LLM provider answers for each debate persona -- configurable, not hardcoded.

Technically any provider can fill any role: a role is just a system prompt plus
whatever prior reports it's given to react to, and any of the three providers can
run that. The defaults below reflect which provider's own strengths suit each role
(Gemini's live search for the news-tracking role, a distinct "voice" for the
contrarian, etc.), not a technical requirement -- so they're a starting point,
fully overridable, not a constraint.
"""

from __future__ import annotations

import json
from pathlib import Path

CONFIG_PATH = Path("data/bot_config.json")

ROLES = ("quant", "beat", "contrarian", "moderator")
PROVIDERS = ("claude", "gemini", "openai")
PROVIDER_LABELS = {"claude": "Claude", "gemini": "Gemini", "openai": "ChatGPT"}

DEFAULT_ROLE_PROVIDERS = {
    "quant": "claude",
    "beat": "gemini",
    "contrarian": "openai",
    "moderator": "claude",
}

ROLE_INFO = {
    "quant": {
        "label": "Quant / VORP Specialist",
        "default_name": "Quant",
        "description": "Runs the numbers -- VORP, positional scarcity, trade value math. No news, no opinions, just the math.",
        "recommended": "claude",
        "why": "Strong at holding one consistent analytical framework across a long, structured answer.",
    },
    "beat": {
        "label": "Beat / News Tracker",
        "default_name": "Beat Tracker",
        "description": "Pulls current injury reports, depth-chart changes, and market buzz via live web search.",
        "recommended": "gemini",
        "why": (
            "Native Google Search grounding -- real live results, not just what the model happened to learn "
            "in training. ChatGPT gets its own web search tool if reassigned here too; Claude has no live "
            "search wired into this app, so it would answer from training data alone."
        ),
    },
    "contrarian": {
        "label": "Contrarian / Risk Analyst",
        "default_name": "Contrarian",
        "description": "Pressure-tests the Quant and Beat reports -- argues the other side, flags what could go wrong.",
        "recommended": "openai",
        "why": "A distinct \"voice\" from whichever provider runs Quant keeps the debate from reading like one model quietly agreeing with itself.",
    },
    "moderator": {
        "label": "Moderator / Executive Synthesizer",
        "default_name": "Moderator",
        "description": "Weighs all three reports and issues one final verdict with a clear recommendation.",
        "recommended": "claude",
        "why": "Synthesis and judgment is a different task from Quant's number-crunching, even when the same provider ends up running both.",
    },
}


def _load_raw() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_raw(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2))


def load_role_providers() -> dict[str, str]:
    saved = _load_raw().get("providers", {})
    return {role: saved.get(role, DEFAULT_ROLE_PROVIDERS[role]) for role in ROLES}


def set_role_provider(role: str, provider: str) -> bool:
    if role not in ROLES or provider not in PROVIDERS:
        return False
    data = _load_raw()
    data.setdefault("providers", {})[role] = provider
    _save_raw(data)
    return True


def load_role_names() -> dict[str, str]:
    """Display name per role -- defaults to the role's own label (e.g. "Contrarian /
    Risk Analyst") but can be personalized (e.g. "Mike"). The name is an identity
    layer on top of the role, independent of which provider currently does the work
    — renaming or reassigning one never touches the other."""
    saved = _load_raw().get("names", {})
    return {role: saved.get(role, ROLE_INFO[role]["default_name"]) for role in ROLES}


def set_role_name(role: str, name: str) -> bool:
    if role not in ROLES or not name.strip():
        return False
    data = _load_raw()
    data.setdefault("names", {})[role] = name.strip()
    _save_raw(data)
    return True


def reset_role_providers() -> None:
    data = _load_raw()
    data.pop("providers", None)
    _save_raw(data)


def reset_role_names() -> None:
    data = _load_raw()
    data.pop("names", None)
    _save_raw(data)
