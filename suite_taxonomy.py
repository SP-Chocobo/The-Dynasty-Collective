"""What the test suite is made of -- one place that can answer questions ABOUT the tests.

Two independent classifications, deliberately kept apart because they answer different
questions and have different failure modes if they drift.

TIER -- how expensive is this module?
    Detected, never declared: a module that constructs a real DataMerger loads and parses the
    committed source data and costs seconds; everything else costs milliseconds. Detection
    means the tier cannot silently disagree with reality the way a hand-maintained list would.
    Measured at the time of writing: 53 fast modules, 845 tests, 1.5 seconds. 27 full modules
    carry the rest, and the whole suite is ~17 minutes.

    The tiers exist so CI can run the fast one on EVERY push. They are NOT a mechanism for
    deciding which tests a given change needs -- that would be a map from touched files to
    relevant tests, and such a map rots SILENTLY: it would skip the test that mattered and
    still report green. Both tiers always run; only their trigger differs.

SUBJECT -- which production module does this test cover?
    Detected by name: test_draft_room.py covers draft_room.py. This suite has two genuinely
    different kinds of test and encoding only one of them was the first draft's mistake --
    roughly half the modules are conventional per-module coverage that cites no audit section
    at all, and calling those "unlabelled" said more about the taxonomy than about the tests.

CONTRACT -- which audit section or register item is this module about?
    EXTRACTED from the module's own docstring, not assigned here. This suite already labels
    itself: modules cite the audit section (§14) or the register item (#114, R1-R3, D4) they
    exist for, in their first paragraph. Reading those markers means the label travels with
    the test and cannot be forgotten in a table somewhere else.

    Why this is worth having: answering "which tests exercise the absence contract?" cost a
    13-minute bespoke instrumented double-run during the pre-draft-anchor work, and the answer
    (10) mattered -- it decided whether that repair shipped or was reverted. That should be a
    query, not an investigation.

    Contract labels are for DIAGNOSIS and COVERAGE, never for selecting what to run.
"""
from __future__ import annotations

import ast
import glob
import os
import re

TIER_FAST = "fast"
TIER_FULL = "full"

# Modules whose docstring carries no marker. Kept deliberately short: the fix for a new
# unlabelled module is normally a docstring, not a row here. test_suite_taxonomy.py fails
# when a module resolves to nothing, so this cannot silently fall behind.
_UNMARKED: dict[str, tuple[str, ...]] = {
    # Cross-cutting suites that cover no single production module and cite no audit section.
    # Each label below is an editorial judgment read off the module's own docstring, so it is
    # the one part of this file that a human must keep true. test_suite_taxonomy fails when a
    # module resolves to nothing at all, which is what stops this list falling behind.
    "cdme_certification": ("certification",),
    "cdme_metamorphic": ("certification",),
    "cdme_threshold_fuzzing": ("certification",),
    "cdme_ingestion_boundary": ("ingestion",),
    "cdme_terminology": ("terminology",),
    "prytaneum_terminology": ("terminology",),
    "debate_chip_wiring": ("ui-wiring",),
    "league_view_wiring": ("ui-wiring",),
    "maintenance_view_wiring": ("ui-wiring",),
    "matchup_view_wiring": ("ui-wiring",),
    "mock_draft_wiring": ("ui-wiring",),
    "denial_ablation_experiment": ("harness-fidelity",),
    "dependency_audit": ("harness-fidelity",),
    "harness_league_format_hygiene": ("harness-fidelity",),
    "demand_decomposition": ("valuation",),
    "draft_horizon": ("valuation",),
    "kdst_integration": ("valuation",),
    "lineup_marginal_contract": ("valuation",),
    "scoring_functions_parity": ("valuation",),
    "llm_engine_parsing": ("provider",),
    "downstream_contracts": ("absence",),
    "replacement_anchor_boundary": ("absence",),
}

_SECTION = re.compile(r"§\s?(\d{1,2})(?:\.\d+)?")
_REGISTER = re.compile(r"#(\d{1,3})\b")
_REPAIR = re.compile(r"\b(R\d(?:\s?[-+]\s?R?\d)?|D\d{1,2}|A\(#\d+\)|B\(#[\d/#]+\))")


def modules() -> list[str]:
    """Every test module, by import name, in a stable order."""
    return sorted(f[:-3] for f in glob.glob("test_*.py"))


def _source(module: str) -> str:
    path = f"{module}.py"
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def tier_of(module: str) -> str:
    """Detected, not declared -- see the module docstring."""
    return TIER_FULL if "DataMerger()" in _source(module) else TIER_FAST


def subject_of(module: str) -> str | None:
    """The production module this test covers, or None for a cross-cutting boundary suite.

    Detected by filename, so it cannot drift: if the production module is renamed and the test
    is not, this returns None and test_suite_taxonomy notices.
    """
    name = module[5:]
    return name if os.path.exists(f"{name}.py") else None


def contracts_of(module: str) -> tuple[str, ...]:
    """The audit sections / register items this module cites, plus any fallback label.

    Returns markers in the form they appear (`§14`, `#114`, `R1-R3`), so a reader can go
    straight to the record rather than decoding a category name invented here.
    """
    try:
        doc = ast.get_docstring(ast.parse(_source(module))) or ""
    except SyntaxError:
        doc = ""
    found: list[str] = []
    for match in _SECTION.finditer(doc):
        label = f"§{match.group(1)}"
        if label not in found:
            found.append(label)
    for match in _REGISTER.finditer(doc):
        label = f"#{match.group(1)}"
        if label not in found:
            found.append(label)
    for match in _REPAIR.finditer(doc):
        label = match.group(1).replace(" ", "")
        if label not in found:
            found.append(label)
    if not found:
        found.extend(_UNMARKED.get(module[5:], ()))
    return tuple(found)


def by_tier(tier: str) -> list[str]:
    return [m for m in modules() if tier_of(m) == tier]


def coverage() -> dict[str, list[str]]:
    """{contract marker: [modules that cite it]} -- the query this file exists for."""
    out: dict[str, list[str]] = {}
    for module in modules():
        for label in contracts_of(module):
            out.setdefault(label, []).append(module)
    return out


def _main(argv: list[str]) -> int:
    if len(argv) > 1 and argv[1] == "--tier":
        print(" ".join(by_tier(argv[2])))
        return 0
    if len(argv) > 1 and argv[1] == "--coverage":
        cov = coverage()
        for label in sorted(cov, key=lambda s: (s[0], len(s), s)):
            print(f"{label:<10} {len(cov[label]):>2} module(s)  {', '.join(m[5:] for m in cov[label])}")
        return 0
    fast, full = by_tier(TIER_FAST), by_tier(TIER_FULL)
    unlabelled = [m for m in modules() if not contracts_of(m) and not subject_of(m)]
    subjects = [m for m in modules() if subject_of(m)]
    print(f"{len(modules())} test modules: {len(fast)} fast, {len(full)} full")
    print(f"{len(subjects)} cover a named production module; "
          f"{len(coverage())} distinct contract markers cited")
    print(f"{len(unlabelled)} resolve to NEITHER: {[m[5:] for m in unlabelled] or 'none'}")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv))
