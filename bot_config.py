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

import llm_engine  # noqa: F401 - imported for its side effect: it registers the providers
import providers
import store_io


CONFIG_PATH = Path("data/bot_config.json")

ROLES = ("quant", "beat", "contrarian", "moderator")
# Derived from the registry (see providers.py), not written out here. A hand-kept copy is a
# list somebody has to remember to extend, which is how the extension surface got to six files
# in the first place.
PROVIDERS = providers.ids()
PROVIDER_LABELS = providers.labels()

ROLE_INFO = {
    "quant": {
        "label": "Quant / VORP Specialist",
        "default_name": "Quant",
        "description": "Runs the numbers -- VORP, positional scarcity, trade value math. No news, no opinions, just the math.",
    },
    "beat": {
        "label": "Beat / News Tracker",
        "default_name": "Beat Tracker",
        "description": "Pulls current injury reports, depth-chart changes, and market buzz via live web search.",
    },
    "contrarian": {
        "label": "Contrarian / Risk Analyst",
        "default_name": "Contrarian",
        "description": "Pressure-tests the Quant and Beat reports -- argues the other side, flags what could go wrong.",
    },
    "moderator": {
        "label": "Moderator / Executive Synthesizer",
        "default_name": "Moderator",
        "description": "Weighs all three reports and issues one final verdict with a clear recommendation.",
    },
}

# WHY THERE IS NO PER-ROLE VENDOR RECOMMENDATION HERE ANY MORE.
#
# There used to be: quant->claude, beat->gemini, contrarian->openai, moderator->claude, each
# with a hand-written `why`. Measured, that assignment is EXACTLY what cycling PROVIDERS in
# declaration order across ROLES produces -- it was arbitrary first and justified afterwards,
# which is why three of the four rationales argued for something other than the vendor they
# were attached to. One retracted itself in its own second sentence ("live search isn't a
# reason to prefer one provider over another for this role anymore"); one argued for
# DIFFERENCE from whatever runs Quant, which any non-Quant provider satisfies; one said the
# provider does not matter at all ("even when the same provider ends up running both").
#
# Nothing in this repository ever measured which family is better at which chair. A shipped
# recommendation with no measurement behind it is a claim the writing path cannot establish --
# the same defect this codebase repaired at the alias boundary (#89) and everywhere else.
#
# THE BAR FOR PUTTING ONE BACK, because recommendations are worth having and this is not a
# ban on them: a per-role or per-model recommendation may ship when it carries the benchmark
# run that produced it. bot_benchmark already fingerprints the battery, the rubric and the
# chair prompts, so such a claim is reproducible rather than editorial. Until then the honest
# state is "not measured", and the assignment below says so by being openly arbitrary.
ASSIGNMENT_RULE = (
    "Chairs are dealt round-robin across whichever providers you have a key for, in "
    "declaration order. That order is ARBITRARY and is not a claim that any family suits any "
    "chair better -- nothing here has measured that. With one key, all four chairs run on it."
)


def default_role_providers_for(roles, available: "tuple[str, ...] | list[str] | None" = None) -> dict[str, str]:
    """The round-robin rule itself, for any set of chairs. pick_debate's Draft Room panel has
    three of its own and had the identical hardcoded defect, so the rule lives in one place
    rather than being written twice and drifting."""
    pool = tuple(p for p in (available if available is not None else PROVIDERS) if p in PROVIDERS)
    if not pool:
        pool = PROVIDERS
    return {role: pool[i % len(pool)] for i, role in enumerate(roles)}


def default_role_providers(available: "tuple[str, ...] | list[str] | None" = None) -> dict[str, str]:
    """The starting assignment for a user who has not configured one, from the keys they have.

    ONE RULE COVERS BOTH CASES THAT MATTERED. Measured against the old hardcoded defaults: a
    user with only a Gemini key got 1 of 4 chairs, and a user with only an OpenAI key got 1 of 4
    -- and in both cases the dead one was the MODERATOR, the chair that writes the verdict, the
    action item, the to-do directives and the source findings. Dealing round-robin over the
    providers actually available degenerates to "all four on your one family" without a special
    case for it.

    `available=None` means "assume all of them", which reproduces the previous shipped
    assignment exactly -- so a user with all three keys sees no change whatsoever.

    An empty `available` also falls back to all providers rather than returning nothing: a
    config screen still has to render a selectable value before any key exists, and an empty
    assignment would be a different kind of lie than an unreachable one.
    """
    return default_role_providers_for(ROLES, available)


#: The all-keys case, kept as a module constant because callers and tests reference it. It is
#: derived from the same function rather than written out, so the two cannot disagree.
DEFAULT_ROLE_PROVIDERS = default_role_providers()

# Model choice is a separate layer from provider choice: two roles can share a
# provider (e.g. both on Claude) and still want different models -- a role that just
# needs cheap number-crunching doesn't need the same model as one doing the final
# synthesis. Not an enum: providers ship new models on their own schedule, and the
# per-role field is free text so a model this app doesn't know about yet still works.
# These are just autocomplete-style suggestions shown in the UI.
SUGGESTED_MODELS = {pid: list(providers.get(pid).suggested_models) for pid in providers.ids()}


def _load_raw() -> dict:
    # #102: atomic, locked, and no longer able to turn a torn read into an empty store
    # that the next write persists -- see store_io's own docstring for the measurement.
    return store_io.read(CONFIG_PATH, {})


def _save_raw(data: dict) -> None:
    store_io.write(CONFIG_PATH, data)


def load_role_providers(available: "tuple[str, ...] | list[str] | None" = None) -> dict[str, str]:
    """The saved assignment, with anything unset filled in from the keys the caller has.

    A SAVED CHOICE ALWAYS WINS, including one that points at a provider with no key -- that is
    the user's own decision and this is not the place to quietly overrule it. `available` only
    fills the gaps.
    """
    saved = _load_raw().get("providers", {})
    fallback = default_role_providers(available)
    return {role: saved.get(role, fallback[role]) for role in ROLES}


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
