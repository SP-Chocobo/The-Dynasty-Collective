"""Whether two chairs agreeing is two opinions or one, said out loud.

THE CLAIM THIS EXISTS TO STOP. "The Moderator and the Contrarian both agreed" reads as
corroboration. It is only corroboration if they are two voices, and after the neutrality pass
they very often are not: chairs are dealt round-robin across whichever providers you have a key
for, so **with one API key all four chairs run on the same family** -- frequently the same model,
answering twice. ROADMAP already names the principle and this module is its enforcement:

    "multiple models agreeing is not, by itself, sufficient corroboration if they're all
     downstream of the same single source."

WHY IT IS FOUR STATES AND NOT A BOOLEAN. Two chairs' relationship is not "independent or not":

    SAME_VOICE      same provider, same model string       -- one opinion, counted twice
    SAME_FAMILY     same provider, two DIFFERENT models    -- two opinions, correlated
    INDEPENDENT     different providers                    -- two opinions
    INDETERMINATE   same provider, and at least one side is on the PROVIDER DEFAULT

The last is the one a boolean would destroy, and it is #17.2/#109 arriving at a new consumer:
a provider default is a floating alias, so a chair on "(provider default)" and a chair on an
explicit model of the same provider MIGHT be the same model and we cannot tell. Reporting that
as "different" would be inventing a distinction; reporting it as "same" would be inventing an
identity. It gets its own state, and the standing rule applies -- **absence is not a value**, so
INDETERMINATE never counts as corroboration.

WHAT THIS MODULE DOES NOT DECIDE. It reports the relationship; it does not set the bar. Different
consumers legitimately want different bars, and the bar is a product decision rather than a
property of the models:

    a provisional, one-install acceptance   -- blast radius 1; SAME_FAMILY is defensible
    a shared, canonical acceptance          -- blast radius N; INDEPENDENT or nothing

Encoding one of those here would bake a deployment choice into a measurement, which is the
accretion this project has already had to unwind once.
"""

from __future__ import annotations

from typing import Optional

SAME_VOICE = "same_voice"
SAME_FAMILY = "same_family"
INDEPENDENT = "independent"
INDETERMINATE = "indeterminate"

#: What a chair's model field holds when the user picked nothing. Both spellings occur: bot_config
#: stores "" for "no override", and callers pass None. Neither names a model.
_NO_MODEL = ("", None)


def voice(role: str, role_providers: dict, role_models: Optional[dict] = None) -> tuple[str, Optional[str]]:
    """(provider, model) for one chair -- the pair that identifies WHO answered.

    Provider alone is not an identity: two chairs on one provider running different models are
    two voices, and a provider-only record cannot see that. Same reason DebateResult carries both.
    """
    model = (role_models or {}).get(role)
    return role_providers.get(role, ""), (None if model in _NO_MODEL else model)


def relationship(role_a: str, role_b: str, role_providers: dict,
                 role_models: Optional[dict] = None) -> str:
    """How two chairs' answers relate as evidence. One of the four states above."""
    provider_a, model_a = voice(role_a, role_providers, role_models)
    provider_b, model_b = voice(role_b, role_providers, role_models)
    if provider_a != provider_b:
        return INDEPENDENT
    if model_a is None or model_b is None:
        # Same provider, and at least one side's served model is a floating alias (#109). If BOTH
        # are on the default they are almost certainly the same model -- but "almost certainly"
        # is not a fact this code can establish, and the honest states are the same either way:
        # not knowably distinct, so not corroboration.
        return INDETERMINATE
    return SAME_VOICE if model_a == model_b else SAME_FAMILY


def distinct_voices(roles, role_providers: dict, role_models: Optional[dict] = None) -> int:
    """How many genuinely different (provider, model) pairs answered across these roles.

    Counts a provider default as its own voice per provider rather than merging it into a named
    model of that provider -- the merge would be the same unprovable identity claim `relationship`
    refuses to make, and here it would UNDERCOUNT, which is the safe direction to be wrong in.
    """
    return len({voice(role, role_providers, role_models) for role in roles})


def counts_as_corroboration(state: str, *, require_cross_provider: bool) -> bool:
    """Apply a bar to a relationship. The bar is the CALLER's, and must be passed explicitly.

    `require_cross_provider=True` is the shared-acceptance bar: only INDEPENDENT counts, because
    two models from one vendor share training and often share retrieval, which is ROADMAP's
    "downstream of the same single source" at family scale. False is the provisional bar, where
    the blast radius is one install and one moment.

    There is deliberately no default. A caller that has not decided which bar it is applying has
    not decided the thing that matters.
    """
    if require_cross_provider:
        return state == INDEPENDENT
    return state in (INDEPENDENT, SAME_FAMILY)


def note(role_a: str, role_b: str, role_providers: dict,
         role_models: Optional[dict] = None, labels: Optional[dict] = None) -> str:
    """One sentence for a reader, or "" when there is nothing worth saying.

    Empty for INDEPENDENT: telling a user their chairs are on different providers every time they
    are would train them to ignore the line that matters. This speaks only when agreement is worth
    less than it looks.
    """
    labels = labels or {}
    name_a = labels.get(role_a, role_a.title())
    name_b = labels.get(role_b, role_b.title())
    state = relationship(role_a, role_b, role_providers, role_models)
    if state == SAME_VOICE:
        return (f"{name_a} and {name_b} are running the same model, so their agreement is one "
                f"opinion answering twice, not two.")
    if state == SAME_FAMILY:
        return (f"{name_a} and {name_b} run different models from the same provider. That is two "
                f"opinions, but correlated ones -- shared training, often shared retrieval.")
    if state == INDETERMINATE:
        return (f"{name_a} and {name_b} share a provider and at least one is on that provider's "
                f"default model, so whether they are the same model is unknown -- not known to "
                f"be different.")
    return ""
