"""#188, ruled: one place to ask "is this number a bound?" -- without collapsing WHY it is one.

THE RULING. The bounded/partial state was invented five times across the codebase under five
names. `partial` is adopted as the shared CONCEPT; `rule_floor` stays distinct because it is a
different fact; `provider_meter.TRUNCATED` stays out because it describes a payload rather than
the epistemic status of a computed quantity.

WHY THIS IS A READER AND NOT A RENAME. "Adopt `partial`" could have meant making every
bounded-input basis emit the literal string `'partial'`. That was rejected, and the reason is
#187: its repair was MORE tokens, not fewer, because `denial_value`'s single `0.0` had been
three different facts. `roster_partially_priced` and `pool_truncated` each say WHICH input was
incomplete, and collapsing them to `'partial'` would destroy exactly the information #187 was
built to preserve. A rename would also be a data-format change -- these tokens are keys in the
label maps shipped across the Python/JS boundary (#186) and they participate in snapshot
identity (#92) -- for no gain a classification cannot deliver.

So nothing here declares a string or moves a constant. This module READS the vocabularies that
already exist and answers the one question no single vocabulary could: *is this basis telling me
the number is a bound rather than the quantity, and of which kind?*

THE AXIS, which is behavioural rather than taxonomic: **would more evidence sharpen this number?**

  BOUNDED_INPUT   the computation ran on INCOMPLETE INPUTS, so the result is a bound.
                  More evidence would sharpen it. A consumer may legitimately re-check it
                  later, and a surface may honestly say "still resolving".

  BOUNDED_BY_RULE the evidence is COMPLETE and the RULEBOOK only yields a bound. More evidence
                  would NOT sharpen it -- this is already the most that can be said. A consumer
                  must never re-check it hoping for a sharper answer, and a surface should say
                  "this is the limit of what is knowable", not "still resolving".

An IR designation is not partially known: we know it exactly, and the rule says "at least four
games". That is a different fact from "some byes are unknown, so this week's number is a floor",
even though both produce a bound -- and the difference changes what a consumer should DO.

REACHABILITY IS PART OF THE DECLARATION (the condition this ruling was made subject to). A
vocabulary does not get a state it cannot emit; that is the unreachable-predicate shape the 18th
withdrawal was. Every token below is recorded with how it was established, and the two kinds of
"not seen in today's output" are kept apart:

  exercised          driven into the state and observed, by the tests in
                     test_basis_semantics.py -- not inferred from reading the code.
  dormant_by_design  a real, wired code path that today's DATA never triggers. Not dead: its
                     wiring is separately guarded so it cannot be quietly removed. Recording
                     this distinction is the point -- a dormant guard that reads as dead is
                     exactly what someone "cleans up".
"""
from __future__ import annotations

from typing import Optional

import draft_room as dr
import lineup_optimizer as lo
import player_universe as pu

#: How each member's reachability was established. Keyed by the token's VALUE, since that is
#: what a consumer actually holds.
REACHABILITY: dict[str, str] = {
    lo.BYE_PARTIAL: "exercised",
    lo.DISPLACEMENT_ROSTER_PARTIAL: "exercised",
    # The clamp binds at no position on the real rulebook today (86 DL, 85 LB, 130 DB price in
    # an IDP league). The path is live and wired, and test_replacement_basis_vocabulary asserts
    # the `truncated_out` collector is passed ON THE CALL NODE -- precisely because behaviour
    # cannot cover a branch that real data never enters.
    dr.REPLACEMENT_BASIS_POOL_TRUNCATED: "dormant_by_design",
    pu.RULE_FLOOR: "exercised",
}

#: Incomplete inputs -> the result is a bound. More evidence would sharpen it.
BOUNDED_INPUT: frozenset[str] = frozenset({
    lo.BYE_PARTIAL,                          # some rostered byes unknown; the week is a FLOOR
    lo.DISPLACEMENT_ROSTER_PARTIAL,          # roster only partly priced
    dr.REPLACEMENT_BASIS_POOL_TRUNCATED,     # the priced list ran out before the anchor
})

#: Complete evidence, bounded RULE. More evidence would not sharpen it.
BOUNDED_BY_RULE: frozenset[str] = frozenset({
    pu.RULE_FLOOR,                           # "misses AT LEAST four games", per the rulebook
})

#: Deliberately OUT, with the reason recorded so it is not re-litigated or quietly folded in.
#: `provider_meter.TRUNCATED` marks a response payload that was cut short. That is a fact about
#: a transport, not about the epistemic status of a computed quantity, and admitting it would be
#: the category error this split exists to prevent.
EXCLUDED_WITH_REASON: dict[str, str] = {
    "truncated": "provider_meter: describes a cut-off PAYLOAD, not a bounded computed quantity",
}

BOUND_KIND_INPUT = "bounded_input"
BOUND_KIND_RULE = "bounded_by_rule"


def bound_kind(basis: Optional[str]) -> Optional[str]:
    """Which kind of bound this basis declares, or None if it declares no bound.

    None is the honest answer for a measured basis AND for an absence basis alike: neither is
    a bound. A caller wanting to distinguish those two reads the quantity's own vocabulary --
    that is what it is for, and this module deliberately does not duplicate it (#126)."""
    if basis is None:
        return None
    if basis in BOUNDED_INPUT:
        return BOUND_KIND_INPUT
    if basis in BOUNDED_BY_RULE:
        return BOUND_KIND_RULE
    return None


def is_bounded(basis: Optional[str]) -> bool:
    """True when the number this basis explains is a BOUND rather than the quantity itself."""
    return bound_kind(basis) is not None


def would_more_evidence_sharpen(basis: Optional[str]) -> Optional[bool]:
    """The axis itself, as a question a consumer can actually act on.

    True  -- bounded because inputs were incomplete; more data would sharpen it.
    False -- bounded by the rulebook; this is already the most that can be said.
    None  -- not a bound, so the question does not apply. Three-state on purpose: collapsing
             "not a bound" into False would tell a caller that a measured number cannot be
             improved, which is a different and much stronger claim than the one being made.
    """
    kind = bound_kind(basis)
    if kind is None:
        return None
    return kind == BOUND_KIND_INPUT
