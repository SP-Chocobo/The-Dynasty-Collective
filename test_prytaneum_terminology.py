"""Structural checks that The Prytaneum (the Dynasty Collective's multi-intelligence
deliberation capability) stays a single, consistently named product concept -- not a check on
its behavior, which is covered by test_pick_synthesis.py / llm_engine's own tests / etc.

Source-level checks in the same spirit as test_cdme_terminology.py: these exist to catch a
future edit that:
  - reintroduces stale pre-Prytaneum product terminology ("Debate Slab", "Debate Dock", "Full
    Squad Debate", "debate panel", "debate studio" as a surface name) as if it were still
    current, or
  - accidentally renames one of the four roles (Quant/Beat/Contrarian/Moderator) while touching
    Prytaneum-related copy, or
  - conflates Draft Room's own separate "Debate My Pick" system (Strategist/Skeptic/Caller)
    with The Prytaneum.
"""

import re
import unittest
from pathlib import Path

_README = Path(__file__).with_name("README.md").read_text()
_STALE_TERMS = ("debate slab", "debate dock", "full squad debate", "squad debate", "multi-bot debate")
# "debate panel" and "debate studio" as bare surface names are stale too, but "debate studio" is
# allowed to survive exactly once, in the README's own historical note.
_HISTORICAL_NOTE_ALLOWANCE = 1

_ROOT = Path(__file__).parent
_STALE_PATTERN = re.compile("|".join(re.escape(t) for t in _STALE_TERMS), re.IGNORECASE)

#: Directories that never hold product copy -- version control, caches, tool state, dependency
#: trees. Excluded because scanning them says nothing about what the product calls itself.
_NOT_PRODUCT_COPY = {".git", "__pycache__", ".claude", "node_modules", ".pytest_cache", ".venv"}

#: File types that can carry a product name a person reads. Data files are deliberately absent:
#: a stale term inside a captured league or a battery result is a fact about that capture, not a
#: use of the name.
_COPY_SUFFIXES = {".py", ".md", ".html", ".js", ".css"}


def _is_historical_record(path: Path) -> bool:
    """Audit records and evidence artifacts are EXEMPT BY RULE, not by name.

    These files record what was believed and written at a given time. FREEZE_CHECKLIST.md
    strikes through its own wrong headlines rather than deleting them, for exactly this reason:
    the superseded wording IS the record of the mistake. Rewriting "Debate Dock" out of a
    finding written when the surface was called that would destroy evidence to satisfy a
    linter. So the rule is stated as a rule -- audit plan, freeze checklist, anything under
    evidence/ -- and not as a list of filenames that would quietly grow.
    """
    rel = path.relative_to(_ROOT)
    if rel.parts[0] == "evidence":
        return True
    return rel.name in ("POST_AUDIT_PLAN.md", "FREEZE_CHECKLIST.md")


def _stale_carriers() -> list[tuple[Path, str]]:
    """Every (file, retired term) pair in committed product copy.

    ONE scanner, so the whole-repo check and the top-level-Python check cannot drift apart into
    two different definitions of "stale". Historical records are excluded here, at the source,
    rather than subtracted by each caller.

    PAIRS, not files, and the difference is a defect this test had for about ten minutes. A
    file-count ratchet cannot see a term reintroduced into a file that was ALREADY dirty:
    writing "Debate Slab" into a mockup that already said "Debate Dock" left the count at 13 and
    the guard silent. Counting distinct (file, term) pairs catches that, while still ignoring a
    second copy of a term the file already carries -- which is duplication, not reintroduction.
    """
    found = []
    for path in sorted(_ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in _COPY_SUFFIXES:
            continue
        rel = path.relative_to(_ROOT)
        if any(part in _NOT_PRODUCT_COPY for part in rel.parts):
            continue
        if path.name == Path(__file__).name or _is_historical_record(path):
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for term in sorted({m.group(0).lower() for m in _STALE_PATTERN.finditer(text)}):
            found.append((path, term))
    return found


#: The mockups are the DESIGN WORKSPACE for the very surface that was renamed, so they carry the
#: old name throughout. Their copy belongs to #181 (the owner's standing UI pass across every
#: surface), not to this terminology guard -- renaming it here would be a UI decision taken by a
#: test. Pinned as a COUNT rather than a filename list: the number cannot grow without someone
#: answering for it, and it drops on its own as #181 works through them.
_MOCKUP_DEBT = 13


class PrytaneumCanonicalDefinitionTests(unittest.TestCase):
    def test_readme_has_exactly_one_prytaneum_section_header(self):
        self.assertEqual(_README.count("## The Prytaneum"), 1)

    def test_readme_states_the_three_tier_relationship(self):
        section_start = _README.index("## The Prytaneum")
        section_end = _README.index("This project also maintains a separate, offline")
        section = _README[section_start:section_end]
        self.assertIn("CDME computes.", section)
        self.assertIn("The Prytaneum deliberates.", section)
        self.assertIn("The user decides.", section)

    def test_readme_names_all_four_roles_in_the_prytaneum_section(self):
        section_start = _README.index("## The Prytaneum")
        section_end = _README.index("This project also maintains a separate, offline")
        section = _README[section_start:section_end]
        for role in ("Quant", "Beat", "Contrarian", "Moderator"):
            self.assertIn(role, section)

    def test_readme_distinguishes_draft_rooms_own_separate_system(self):
        section_start = _README.index("## The Prytaneum")
        section_end = _README.index("This project also maintains a separate, offline")
        section = _README[section_start:section_end]
        self.assertIn("Strategist", section)
        self.assertIn("part of The Prytaneum", section)
        self.assertIn("not**", section)

    def test_no_stale_pre_prytaneum_terminology_anywhere_in_the_readme(self):
        lowered = _README.lower()
        for term in _STALE_TERMS:
            self.assertNotIn(term, lowered, f"stale term {term!r} found in README.md")
        # "debate studio" is allowed exactly once -- the deliberate "formerly labeled" note.
        self.assertLessEqual(lowered.count("debate studio"), _HISTORICAL_NOTE_ALLOWANCE)


class PrytaneumSourceCrossReferenceTests(unittest.TestCase):
    def test_screen_context_module_docstring_names_the_prytaneum(self):
        text = Path(__file__).with_name("screen_context.py").read_text()
        docstring = " ".join(text[:text.index('"""', 3)].split())
        self.assertIn("The Prytaneum", docstring)

    def test_no_stale_pre_prytaneum_terminology_in_any_committed_python_source(self):
        # This file itself is exempt -- it's the definition of what counts as stale, not a use
        # of it.
        offenders = sorted({p.name for p, _ in _stale_carriers()
                            if p.parent == _ROOT and p.suffix == ".py"})
        self.assertEqual(offenders, [])

    def test_the_four_roles_are_unrenamed_in_llm_engine(self):
        text = Path(__file__).with_name("llm_engine.py").read_text()
        for role in ("Quant", "Beat", "Contrarian", "Moderator"):
            self.assertIn(role, text)

    def test_draft_rooms_own_pick_debate_system_keeps_its_distinct_role_names(self):
        text = Path(__file__).with_name("pick_debate.py").read_text()
        for role in ("Strategist", "Skeptic", "Caller"):
            self.assertIn(role, text)


class TheGuardCoversTheWholeRepositoryNotJustItsOwnDirectory(unittest.TestCase):
    """#182: this guard used to scan `Path(__file__).parent.glob("*.py")` -- top-level Python
    only. It was not vacuous (writing a stale term into a top-level module did fail it), but of
    the 16 committed files then carrying a retired term, exactly ONE sat inside that scan, and
    that one was this file, which is explicitly exempt as the definition of what counts as
    stale. So the guard's live population was ZERO. It could fire; there was nothing in range
    for it to fire at. A docstring promising to catch "a future edit that reintroduces stale
    terminology" was describing a domain fifteen files wider than the one it looked at.
    """

    def test_the_scan_reaches_outside_the_top_level_directory(self):
        # The vacuity guard for the widening itself. If some future refactor quietly narrows
        # _stale_carriers back to one directory, this fails before the counts below go green
        # for the wrong reason.
        scanned = set()
        for path in _ROOT.rglob("*"):
            if not path.is_file() or path.suffix not in _COPY_SUFFIXES:
                continue
            rel = path.relative_to(_ROOT)
            if any(part in _NOT_PRODUCT_COPY for part in rel.parts):
                continue
            scanned.add(rel.parts[0] if len(rel.parts) > 1 else "")
        self.assertIn("mockups", scanned)
        self.assertGreater(len(scanned), 1, "the scan collapsed back to a single directory")

    def test_every_remaining_carrier_is_a_mockup_and_the_count_cannot_grow(self):
        carriers = _stale_carriers()
        outside = sorted(f"{p.relative_to(_ROOT)}: {term!r}" for p, term in carriers
                         if p.relative_to(_ROOT).parts[0] != "mockups")
        # A NEW stale term anywhere that is not a mockup and not a historical record is a
        # regression, and this is the assertion that says so.
        self.assertEqual(outside, [], f"retired terminology in live product copy: {outside}")
        self.assertEqual(len(carriers), _MOCKUP_DEBT,
                         "the mockup terminology debt moved; if #181 cleaned some, lower "
                         "_MOCKUP_DEBT, and if it grew, that is the regression this pins")

    def test_historical_records_are_exempt_by_rule_and_the_rule_is_narrow(self):
        # Exempt: the two audit documents and everything under evidence/.
        self.assertTrue(_is_historical_record(_ROOT / "POST_AUDIT_PLAN.md"))
        self.assertTrue(_is_historical_record(_ROOT / "FREEZE_CHECKLIST.md"))
        self.assertTrue(_is_historical_record(_ROOT / "evidence" / "anything" / "note.md"))
        # NOT exempt: live product copy, including the mockups the debt above tracks. Without
        # this half the rule could widen to "everything" and the guard would pass by covering
        # nothing -- the same failure it was just repaired for.
        self.assertFalse(_is_historical_record(_ROOT / "README.md"))
        self.assertFalse(_is_historical_record(_ROOT / "app.py"))
        self.assertFalse(_is_historical_record(_ROOT / "mockups" / "dock_1_ledger.html"))

    def test_the_retired_name_and_the_surviving_one_are_not_confused(self):
        """"Debate Dock" is retired; the SURFACE it named is now "Debate My Pick", and the bare
        word "Dock" survives as shorthand in working notes. The stale list must catch the
        two-word product name without catching the shorthand, or every working note becomes a
        violation and the guard gets switched off.
        """
        self.assertTrue(_STALE_PATTERN.search("the Debate Dock shows"))
        self.assertIsNone(_STALE_PATTERN.search("six absence breaks in the Dock"))
        self.assertIsNone(_STALE_PATTERN.search("test_dock_absence_contract.py"))
        # And the current name is not itself on the stale list.
        self.assertIsNone(_STALE_PATTERN.search("Debate My Pick"))


if __name__ == "__main__":
    unittest.main()
