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
import store_io


CONFIG_PATH = Path("data/bot_config.json")

ROLES = ("quant", "beat", "contrarian", "moderator")
PROVIDERS = ("claude", "gemini", "openai")
PROVIDER_LABELS = {"claude": "Claude", "gemini": "Gemini", "openai": "ChatGPT"}

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
            "in training. ChatGPT and Claude both get their own web search tool if reassigned here too, so "
            "live search isn't a reason to prefer one provider over another for this role anymore -- pick "
            "whichever's answers you find most useful."
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

# Derived from ROLE_INFO, not a separately maintained dict -- a "recommended" value
# changed in one place without the other would make "Use recommended providers" (the
# button that resets to this) silently lie about what it just did.
DEFAULT_ROLE_PROVIDERS = {role: ROLE_INFO[role]["recommended"] for role in ROLES}

# Model choice is a separate layer from provider choice: two roles can share a
# provider (e.g. both on Claude) and still want different models -- a role that just
# needs cheap number-crunching doesn't need the same model as one doing the final
# synthesis. Not an enum: providers ship new models on their own schedule, and the
# per-role field is free text so a model this app doesn't know about yet still works.
# These are just autocomplete-style suggestions shown in the UI.
SUGGESTED_MODELS = {
    "claude": ["claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5"],
    "gemini": ["gemini-2.0-flash", "gemini-2.0-pro"],
    "openai": ["gpt-4o", "gpt-4.5-mini", "o3"],
}


def _load_raw() -> dict:
    # #102: atomic, locked, and no longer able to turn a torn read into an empty store
    # that the next write persists -- see store_io's own docstring for the measurement.
    return store_io.read(CONFIG_PATH, {})


def _save_raw(data: dict) -> None:
    store_io.write(CONFIG_PATH, data)


def load_role_providers() -> dict[str, str]:
    saved = _load_raw().get("providers", {})
    return {role: saved.get(role, DEFAULT_ROLE_PROVIDERS[role]) for role in ROLES}


@store_io.atomic(lambda *a, **k: CONFIG_PATH)
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


@store_io.atomic(lambda *a, **k: CONFIG_PATH)
def set_role_name(role: str, name: str) -> bool:
    if role not in ROLES or not name.strip():
        return False
    data = _load_raw()
    data.setdefault("names", {})[role] = name.strip()
    _save_raw(data)
    return True


def load_role_models() -> dict[str, str]:
    """Specific model override per role -- empty string means "no override, use
    whatever model the assigned provider defaults to" (llm_engine.py's own
    CLAUDE_MODEL/GEMINI_MODEL/OPENAI_MODEL constants). Unlike names/providers, the
    default here is genuinely "nothing set," not a value drawn from ROLE_INFO --
    there's no single "recommended model" the way there's a recommended provider,
    since the right model depends on cost/quality tradeoffs specific to the user."""
    saved = _load_raw().get("models", {})
    return {role: saved.get(role, "") for role in ROLES}


@store_io.atomic(lambda *a, **k: CONFIG_PATH)
def set_role_model(role: str, model: str) -> bool:
    if role not in ROLES:
        return False
    data = _load_raw()
    data.setdefault("models", {})[role] = model.strip()
    _save_raw(data)
    return True


@store_io.atomic(lambda *a, **k: CONFIG_PATH)
def reset_role_providers() -> None:
    data = _load_raw()
    data.pop("providers", None)
    _save_raw(data)


@store_io.atomic(lambda *a, **k: CONFIG_PATH)
def reset_role_models() -> None:
    data = _load_raw()
    data.pop("models", None)
    _save_raw(data)


@store_io.atomic(lambda *a, **k: CONFIG_PATH)
def reset_role_names() -> None:
    data = _load_raw()
    data.pop("names", None)
    _save_raw(data)


# -- Moderator response personality -------------------------------------------
#
# Scoped to the Moderator only, not all four roles: since the debate view now leads
# with the Moderator's synthesis by default (the other three collapse behind a
# toggle), the Moderator's voice is the one the user actually reads most of the
# time -- "how should it talk to me" only has one obvious answer to attach to. The
# other three roles' prompts are deliberately narrow (Quant: "no news, no opinions,
# just the math") and a tone directive would work against that narrowness rather
# than add anything.
MODERATOR_PERSONALITIES = {
    "Direct": "Be terse and direct. Lead with the verdict, then the minimum reasoning needed to support it -- short sentences, minimal hedging.",
    "Analytical": "Favor thorough, precise reasoning over brevity -- show the work, not just the conclusion.",
    "Conversational": "Write like you're talking to a friend who already knows fantasy football -- natural phrasing, not a clinical report.",
    "Blunt": "Don't soften bad news or a weak trade. If it's bad, say so plainly, with no diplomatic hedging.",
    "Warm": "Be warm and encouraging even when the news is bad -- engaged with the user as a person, not just a data source. Supportive, not sycophantic: warmth is in how you deliver the call, never a reason to soften what the call actually is.",
}


def load_moderator_personality() -> str:
    """Which MODERATOR_PERSONALITIES key is active, or '' for the prompt's own default
    tone (no directive appended)."""
    return _load_raw().get("moderator_personality", "")


@store_io.atomic(lambda *a, **k: CONFIG_PATH)
def set_moderator_personality(personality: str) -> bool:
    if personality and personality not in MODERATOR_PERSONALITIES:
        return False
    data = _load_raw()
    if personality:
        data["moderator_personality"] = personality
    else:
        data.pop("moderator_personality", None)
    _save_raw(data)
    return True
