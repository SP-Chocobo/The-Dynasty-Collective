"""Structural checks that CDME (Contextual Decision Matrix Engine) stays a single, consistently
named architectural concept -- not a check on CDME's behavior, which is covered by
test_draft_room.py / test_pick_synthesis.py / test_draft_counterfactual.py / etc.

Source-level checks in the same spirit as test_debate_chip_wiring.py: app.py/README.md aren't
meaningfully unit-testable for this, so these assert against the raw text instead. They exist
to catch a future edit that:
  - introduces a second, conflicting "## The Draft Engine"-style canonical definition instead
    of updating the one in README.md, or
  - drops the CDME cross-reference from the two modules that actually make up the engine
    (draft_room.py, pick_synthesis.py), silently decoupling the name from the code again, or
  - reintroduces stale pre-CDME terminology ("master formula", "master algorithm", "draft
    formula", "acquisition formula") as if it were still the current name for this system.
"""

import re
import unittest
from pathlib import Path

_README = Path(__file__).with_name("README.md").read_text()
_STALE_TERMS = ("master formula", "master algorithm", "draft formula", "acquisition formula")


class CDMECanonicalDefinitionTests(unittest.TestCase):
    def test_readme_has_exactly_one_draft_engine_section_header(self):
        self.assertEqual(_README.count("## The Draft Engine"), 1)

    def test_readme_spells_out_the_full_name_before_using_the_acronym(self):
        idx = _README.index("Contextual Decision Matrix Engine")
        # The parenthesized acronym must appear on first mention, establishing CDME as
        # shorthand rather than assuming the reader already knows it.
        self.assertIn("(CDME)", _README[idx:idx + 60])

    def test_readme_names_tav_and_picksnapshot_as_cdmes_outputs(self):
        section_start = _README.index("## The Draft Engine")
        section_end = _README.index("## Setup")
        section = _README[section_start:section_end]
        self.assertIn("Team Acquisition Value (TAV)", section)
        self.assertIn("PickSnapshot", section)
        self.assertIn("Decision Forces", section)
        self.assertIn("Decision Regime", section)

    def test_no_stale_pre_cdme_terminology_anywhere_in_the_readme(self):
        lowered = _README.lower()
        for term in _STALE_TERMS:
            self.assertNotIn(term, lowered, f"stale term {term!r} found in README.md")


class CDMESourceCrossReferenceTests(unittest.TestCase):
    def test_draft_room_module_docstring_names_cdme(self):
        text = Path(__file__).with_name("draft_room.py").read_text()
        docstring = " ".join(text[:text.index('"""', 3)].split())
        self.assertIn("Contextual Decision Matrix Engine (CDME)", docstring)

    def test_pick_synthesis_module_docstring_names_cdme(self):
        text = Path(__file__).with_name("pick_synthesis.py").read_text()
        docstring = " ".join(text[:text.index('"""', 3)].split())
        self.assertIn("Contextual Decision Matrix Engine (CDME)", docstring)

    def test_no_stale_pre_cdme_terminology_in_any_committed_python_source(self):
        # This file itself is exempt -- it's the definition of what counts as stale, not a use
        # of it.
        stale_pattern = re.compile("|".join(re.escape(t) for t in _STALE_TERMS), re.IGNORECASE)
        offenders = []
        for path in Path(__file__).parent.glob("*.py"):
            if path.name == Path(__file__).name:
                continue
            if stale_pattern.search(path.read_text()):
                offenders.append(path.name)
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
