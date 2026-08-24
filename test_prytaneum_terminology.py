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
        stale_pattern = re.compile("|".join(re.escape(t) for t in _STALE_TERMS), re.IGNORECASE)
        offenders = []
        for path in Path(__file__).parent.glob("*.py"):
            if path.name == Path(__file__).name:
                continue
            if stale_pattern.search(path.read_text()):
                offenders.append(path.name)
        self.assertEqual(offenders, [])

    def test_the_four_roles_are_unrenamed_in_llm_engine(self):
        text = Path(__file__).with_name("llm_engine.py").read_text()
        for role in ("Quant", "Beat", "Contrarian", "Moderator"):
            self.assertIn(role, text)

    def test_draft_rooms_own_pick_debate_system_keeps_its_distinct_role_names(self):
        text = Path(__file__).with_name("pick_debate.py").read_text()
        for role in ("Strategist", "Skeptic", "Caller"):
            self.assertIn(role, text)


if __name__ == "__main__":
    unittest.main()
