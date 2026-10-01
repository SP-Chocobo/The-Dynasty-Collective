"""Which of this engine's quantities cross to a third-party model provider.

Gate C of the post-freeze roadmap asks for a disclosure posture: *what may the provider see?*
That question has a factual half and a policy half, and they are not the same work. The policy
half is the owner's. This module answers the factual half, executably, so the posture is set
against a measurement rather than against an assumption -- and so the answer cannot change
quietly afterwards.

ONE HOME FOR "WHAT THE ENGINE PRODUCES" (`#126`). The population is
`quantity_readers.produced_quantities()` -- 103 quantities drawn from the engine's declared
output surfaces. This module does not enumerate quantities. A second enumeration would be the
defect this codebase has found in six different costumes: two readers for one question, and the
stale one easier to reach.

WHY THE READ SET IS AN UPPER BOUND, AND WHY THAT IS SAID OUT LOUD. The scan below reports what
the prompt-construction path READS off the snapshot. Reading is not sending.
`pick_debate.py:577` gates the survival family's emission on `survival_is_presentable()`, so
three quantities are read and then deliberately not printed -- what reaches the model instead is
a sentence saying the number is withheld. A census that called those three "exposed" would
contradict a repair made specifically to stop them crossing, and would be reporting a plausible
number about something else. So the answer has three parts, not one:

    READ        the prompt path touches it                                       (upper bound)
    WITHHELD    read, then gated off by a policy flag -- CONDITIONALLY exposed
    EMITTED     actually reaches the provider today                              READ - WITHHELD

THE MIDDLE CLASS IS THE POINT. A withheld quantity is one flag away from crossing with no code
diff at all: the day `SURVIVAL_IS_CALIBRATED` flips, three quantities begin reaching a third
party and no diff records it. For a disclosure posture that is exactly the population you must
enumerate in advance, which is why it is a named class here instead of being folded into either
neighbour.

WHY THE NAMES ARE NOT SEARCHED FOR IN THE EMITTED TEXT. The formatters emit human labels --
`Pick necessity: 73.3/100`, `Universal value: 217.89 = bpa ...` -- so scanning the prompt for
field names finds almost nothing and concludes almost nothing is exposed. Measured: the prompt
is 41,237 characters over 363 lines on a 44-candidate board, and the literal string
`pick_necessity` appears in it zero times. The prompt builder's only source of engine facts is
the snapshot object, so the honest question is which ATTRIBUTES of it the builder reads, which
is a question about code and is answered over the AST.

COVERS ONE OF THE TWO PROVIDER-CALLING MODULES, and says which. `pick_debate.py` builds its
prompts from a snapshot object, so what crosses is answerable off that object. `llm_engine.py`
calls the same three providers for the Prytaneum panel, and its facts arrive through conversation
and `screen_context` rather than off a snapshot -- the technique here would not answer the same
question about it, so it is NOT in this census. That limit is stated here, in the contract a
reader reads, rather than only beside the constant: an unstated scope limit is how a census comes
to be read as covering more than it does (`#133`).

SCOPED TO THE PROVIDER BOUNDARY, deliberately, and not to the browser. `quantity_readers`
already records which UI modules read each quantity, so a browser census would be nearly free --
and it would weaken this one. Widening to a browser is a product-design change on the user's own
data; widening to a provider sends someone's league to a third party. Only the second is the
kind of boundary where "it grew and nobody noticed" is a harm, so only the second gets a
ratchet. The browser column belongs to the Surface Specification, with the product decisions.

Cited register items: `#126` (one home for the population), `#133` (a docstring overclaiming its
coverage is the defect -- hence the upper-bound paragraph), `#166`/`#174` (a number crosses with
its companion: the basis fields are in the census because they cross too), `#187` (absence is
not zero), `#254` (a guard that catches nothing is not a guard), `#292` (the record wins).
"""
from __future__ import annotations

import ast
import collections
import pathlib
import sys

import pick_synthesis as ps
import quantity_readers as qr

#: The module that calls the three providers for a pick debate. `llm_engine.py` is the OTHER
#: provider-calling module (the Prytaneum panel path); it is not scanned here, because its facts
#: arrive through conversation and `screen_context`, not off a snapshot object, so the same
#: technique would not answer the same question about it. Named rather than silently omitted --
#: an unstated scope limit is how a census comes to be read as covering more than it does.
PROMPT_MODULE = pathlib.Path("pick_debate.py")

#: The entry points whose call graph builds what a provider receives. `debate_pick` assembles the
#: three prompts; the rest are the formatters it reaches. Listed rather than discovered so that a
#: NEW provider-bound entry point does not quietly join the scan and change the census's meaning
#: without a reader noticing.
PROMPT_ROOTS = ("debate_pick", "format_snapshot_for_llm", "_format_candidate",
                "_report_for_handoff")

#: The local names that hold a snapshot or a candidate inside those functions. Derived from
#: reading the real parameter names; a holder spelled some other way would be MISSED, which is
#: the scan's known blind spot and is covered behaviourally by the planted-widening tests rather
#: than by hoping this list is complete.
HOLDERS = frozenset({"candidate", "snapshot", "snap", "c"})

#: TODAY'S ANSWER, recorded so it cannot move quietly. Not a target and not a budget: a
#: measurement, in the `boundary_census` shape. A quantity entering this set is a disclosure
#: change and must be a deliberate one.
CENSUS: frozenset[str] = frozenset({
    "absence_kind", "availability_basis", "bpa", "bpa_source", "candidates", "confidence",
    "config_ambiguities", "consensus_rank", "consensus_tier", "data_freshest_date",
    "denial_basis", "denial_team", "denial_value", "depth_basis", "depth_exposure",
    "displacement_adj", "displacement_basis", "expected_value_of_waiting", "injury_status",
    "intervening_picks", "my_roster_id", "name", "near_tie_with_leader", "necessity_label",
    "need_bonus", "opportunity_cost", "pick_label", "pick_necessity", "picks_consumed",
    "player_id", "players_db_stamp", "pool_scope", "position", "position_expected_taken",
    "position_run_detected", "positional_cliff", "positional_forfeit", "projected_points",
    "risk_adj", "risk_basis", "round", "survival_basis", "survival_probability", "team",
    "team_acquisition_value", "time_horizon_adj", "universal_value", "user_selected_player_id",
})


def _functions(path: pathlib.Path) -> dict[str, ast.AST]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {n.name: n for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _reachable(functions: dict[str, ast.AST], roots) -> set[str]:
    """Functions reachable from the roots WITHIN this module.

    Intra-module only, and that is a real limit rather than an oversight: a formatter that moved
    to another module would leave this scan, so `test_fact_exposure` pins the count of reachable
    functions. A scan whose population silently shrank to one function would otherwise report a
    shrinking census as good news.
    """
    seen, stack = set(), [r for r in roots if r in functions]
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Call):
                callee = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                if callee in functions and callee not in seen:
                    stack.append(callee)
    return seen


def reads(path: pathlib.Path = PROMPT_MODULE, roots=PROMPT_ROOTS) -> collections.Counter:
    """Every snapshot/candidate attribute the prompt path reads, counted by site.

    ONE HOME FOR THE WALK. The report, the `--check` guard and every test read this function --
    `prose_names` paid for the alternative: its mutation test re-derived the scope rule, then
    disagreed with the repaired code by four quotations and reported a real fix as a regression.

    Both access shapes, because the code uses both: `candidate.risk_adj` and the
    `getattr(candidate, "risk_basis", None)` that `_format_candidate` uses where the attribute
    may be absent. Counting only the first would have missed `risk_basis`, which is the companion
    `#166` exists to keep beside its number.
    """
    functions = _functions(path)
    found: collections.Counter = collections.Counter()
    for name in _reachable(functions, roots):
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
                    and node.value.id in HOLDERS:
                found[node.attr] += 1
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "getattr" \
                    and len(node.args) > 1 and isinstance(node.args[0], ast.Name) \
                    and node.args[0].id in HOLDERS and isinstance(node.args[1], ast.Constant):
                found[node.args[1].value] += 1
    return found


def classify(path: pathlib.Path = PROMPT_MODULE, roots=PROMPT_ROOTS) -> dict[str, frozenset[str]]:
    """The three classes, plus the two populations needed to tell whether the scan is honest.

    `unknown` is the non-vacuity arm pointing the other way: an attribute the prompt path reads
    that `quantity_readers` does not know as a produced quantity means the two instruments
    disagree about the engine's vocabulary, and one of them is wrong. It is 0 today, and a census
    that quietly tolerated a non-empty `unknown` would be measuring a vocabulary of its own.
    """
    produced = qr.produced_quantities()
    read = frozenset(reads(path, roots))
    withheld = frozenset(ps.withheld_fields())
    return {
        "read": frozenset(a for a in read if a in produced),
        "unknown": frozenset(a for a in read if a not in produced),
        "withheld": frozenset(a for a in read if a in withheld),
        "emitted": frozenset(a for a in read if a in produced and a not in withheld),
        "produced": frozenset(produced),
    }


def widened(path: pathlib.Path = PROMPT_MODULE, roots=PROMPT_ROOTS) -> list[str]:
    """What newly crosses to a provider, relative to `CENSUS`. Empty means nothing did.

    WIDENING ONLY, never shrinkage -- a quantity that stops crossing is a repair, and a check
    that failed on repairs would be trained away within a week. Reports the NAMES, not a boolean:
    `engine_baseline` returned a bare verdict first and then printed its regression prose over
    `0 behavioural difference(s)`, because a caller cannot act on True.
    """
    found = classify(path, roots)
    out = [f"{name}: NEWLY CROSSES to a provider (not in CENSUS)"
           for name in sorted(found["read"] - CENSUS)]
    out += [f"{name}: read by the prompt path but unknown to quantity_readers -- the two "
            f"instruments disagree about the engine's vocabulary"
            for name in sorted(found["unknown"])]
    return out


def main(argv: list[str]) -> int:
    found = classify()
    check = "--check" in argv

    print(f"{len(found['produced'])} produced quantities (quantity_readers)")
    print(f"{len(found['read'])} read by the prompt path in {PROMPT_MODULE} -- the upper bound")
    print(f"{len(found['withheld'])} of those are WITHHELD today and gated off before emission:")
    for name in sorted(found["withheld"]):
        print(f"    {name}")
    print(f"{len(found['emitted'])} actually reach a third-party provider today")

    if not check:
        for name in sorted(found["emitted"]):
            print(f"    {name}")
        return 0

    grew = widened()
    if grew:
        print(f"\nTHE PROVIDER BOUNDARY HAS WIDENED -- {len(grew)} change(s):")
        for line in grew:
            print(f"    {line}")
        print("\nIf this was intended, it is a disclosure change: record it in the Gate C "
              "posture and update CENSUS in the same commit. If it was not, this is what the "
              "census exists to catch.")
        return 1
    print(f"\nthe provider boundary has not widened: {len(found['read'])} quantities reach the "
          f"prompt path, census allows {len(CENSUS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
