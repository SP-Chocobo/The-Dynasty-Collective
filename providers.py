"""The socket: what a provider must supply, declared in one place.

WHAT WAS WRONG. Role-to-provider routing was already neutral -- any chair could run on any
vendor, user-configurable, and llm_engine's docstring said so. The PROVIDER SET was not. Adding
a fourth meant editing six files with nothing anywhere declaring that six was the list:

    llm_engine        a new _call_* function, and PROVIDER_CALLERS
    llm_engine        is_*_configured, and LIST_MODELS_BY_PROVIDER
    bot_config        PROVIDERS, PROVIDER_LABELS, SUGGESTED_MODELS
    provider_meter    _EXTRACTORS (completion state AND usage paths)
    provider_meter    _SOURCE_EXTRACTORS, and the per-SDK limit helpers
    app               PROVIDER_KEY_FIELD, IS_PROVIDER_CONFIGURED

You found that list by archaeology. This module is the declaration, so a fourth provider is an
interface fill instead.

WHAT IS DELIBERATELY *NOT* ABSTRACTED, because it is the part that must stay vendor-specific.

The three SDKs' response shapes genuinely differ, and provider_meter's own docstring already
argues the point: "one function per SDK family, because the three shapes genuinely differ and a
single 'find the tokens' heuristic would be guessing." You cannot read Gemini's
grounding_metadata with Anthropic's web_search_tool_result shape. A lowest-common-denominator
wrapper would fabricate exactly the class of number this codebase spent an audit removing. So
the adapters stay per-vendor; what this module removes is having to FIND them.

THE HONEST COST OF PLUGGING SOMETHING IN, and why capabilities are declared rather than assumed.

Calling a model is the easy half. This app now depends on four things a response can report:

    completion state   did it truncate?              (#99 -- annotates the chair's report)
    usage              input/output tokens           (#100 -- cost, still open)
    model reported     what actually served          (#109 -- the ids are floating aliases)
    retrieved sources  grounding / citations         (#97 -- a finding's evidence snapshot)

A generic adapter -- a local model, an OpenAI-compatible endpoint, some vendor with no SDK --
can make the call and report NONE of those. That is fine, and the machinery already degrades
correctly: describe() returns UNKNOWN for a provider it has no extractor for, sources() returns
[], and bot_research records the finding as `unattributed`. Nothing lies.

What was missing is that nothing SAID SO. A user plugging in a local model would see every
finding come back unattributed and every completion state unknown, with no way to tell "this
provider does not report that" from "this provider reported nothing this time". That is the
never-checked-versus-checked-and-absent distinction #112 left open at the board, arriving here.
So a Provider declares what it can report, and `capability_gaps()` turns that into a sentence
the UI can show.

Registering a provider is therefore an honest act: you say what it does, including what it
cannot do.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class Provider:
    """One provider, and everything the rest of the app needs to know about it.

    `id` is the short key used everywhere (config files, ledger records, saved role
    assignments), so it is the one field that must never change for an existing provider --
    a rename silently orphans every saved role assignment pointing at it.
    """

    id: str
    label: str

    #: (system_prompt, user_prompt, api_key, model) -> str. MUST fail soft: every caller in
    #: this app relies on a "⚠️ ..." string rather than an exception, so one dead provider
    #: cannot take out a panel. A caller that raises breaks DEGRADE_NEVER_ABORT.
    call: Callable[[str, str, Optional[str], Optional[str]], str]

    #: (api_key) -> bool. Whether this provider is reachable at all.
    is_configured: Callable[[Optional[str]], bool]

    #: The credential name this provider's key travels under -- ".env" vocabulary, which is
    #: deliberately not the same as `id` ("claude" is served by ANTHROPIC_API_KEY).
    key_field: str

    #: (api_key) -> (ids, error). Optional: a provider with no discovery endpoint is fine,
    #: and the model picker falls back to free text, which it already supports.
    list_models: Optional[Callable[[Optional[str]], Any]] = None

    #: Autocomplete only, never a quality claim. A RECOMMENDATION -- "this model is good for
    #: this chair" -- is a different thing and may only ship with the benchmark run behind it;
    #: see bot_config's own note on why the per-role vendor picks were removed.
    suggested_models: tuple[str, ...] = ()

    # -- what this provider's responses can actually report ------------------------------------
    #
    # Declared, not detected. A provider that reports none of these still works; it simply
    # cannot participate in truncation annotation, cost metering, served-model identity, or a
    # finding's evidence snapshot -- and the app can now SAY that instead of showing a blank.
    reports_completion: bool = False
    reports_usage: bool = False
    reports_model: bool = False
    reports_sources: bool = False

    #: Free-text, shown to a user weighing a provider. Empty for a first-class one.
    caveat: str = ""

    def capability_gaps(self) -> tuple[str, ...]:
        """What this provider cannot tell the app, in the app's own vocabulary."""
        gaps = []
        if not self.reports_completion:
            gaps.append("whether a reply was cut off at its output cap")
        if not self.reports_usage:
            gaps.append("how many tokens a call used")
        if not self.reports_model:
            gaps.append("which model actually served the call")
        if not self.reports_sources:
            gaps.append("which pages it retrieved, so findings from it stay unattributed")
        return tuple(gaps)


_REGISTRY: dict[str, Provider] = {}


def register(provider: Provider) -> Provider:
    """Add a provider. Later registration of the same id replaces the earlier one, which is
    what lets a deployment override a built-in adapter without editing this file."""
    _REGISTRY[provider.id] = provider
    return provider


def get(provider_id: str) -> Optional[Provider]:
    return _REGISTRY.get(provider_id)


def ids() -> tuple[str, ...]:
    """Every registered provider id, in registration order.

    Registration order is the app's only ordering, and one place depends on it being stable:
    the round-robin that deals chairs across available providers. That deal is arbitrary and
    says so -- but it must be arbitrary the SAME WAY on every run, or a user's assignment
    would shuffle between launches.
    """
    return tuple(_REGISTRY)


def labels() -> dict[str, str]:
    return {pid: p.label for pid, p in _REGISTRY.items()}


def available(key_lookup: Callable[[str], Optional[str]]) -> list[str]:
    """The providers this user can actually reach, given a way to look up a key by key_field.

    Takes a lookup rather than a dict so callers do not have to materialise every credential
    to ask the question -- app.py's own api_key_for reads session state.
    """
    return [pid for pid, p in _REGISTRY.items() if p.is_configured(key_lookup(p.key_field))]
