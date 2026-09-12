"""A document that says "this was never built" has to keep being true.

`CDME_CONTRACTS.md` carries a superseded proposal beneath a banner rather than deleting it --
the repo's discipline, and the right one. But the banner makes a CHECKABLE CLAIM about the
codebase: that the interface it proposes was never implemented, and that the two constants it
derives exist nowhere. That claim was true when written. Nothing but this file stops it from
quietly becoming false, at which point the banner would be telling a reader the opposite of
what the code does.

This is the same shape as `#240` and the doc index's own staleness guard: a derived statement
with no reader is a statement that goes stale in silence.
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

CONTRACTS = Path("CDME_CONTRACTS.md")

#: The constants the superseded "Proposed Phase 2 interface" section derives. Their ABSENCE is
#: the evidence the banner offers, so their absence is what has to hold.
NEVER_IMPLEMENTED = ("WAITING_PRESSURE_REFERENCE", "NECESSITY_WAITING_WEIGHT")


#: This file names both constants in order to look for them, so it matches its own search. That
#: is not an implementation, and excluding it is not a loophole -- it is the same self-reference
#: the doc index hit when it classified its own output. Exactly one exclusion, stated here.
SELF = Path(__file__).name


def python_sources() -> list[Path]:
    """This repository's own Python, asked of git rather than walked -- the same rule
    `doc_index` uses, for the same reason: caches and worktree checkouts are not this repo.
    This file is excluded; see SELF."""
    out = subprocess.run(["git", "ls-files", "-z", "*.py"],
                         capture_output=True, text=True, check=True)
    return [Path(name) for name in out.stdout.split("\0") if name and Path(name).name != SELF]


class TheSupersededProposalStaysSuperseded(unittest.TestCase):
    def test_the_banner_is_still_there(self):
        """Non-vacuity. Every assertion below defends a specific banner; if the banner is gone,
        they are defending nothing and would pass on an empty file."""
        text = CONTRACTS.read_text(encoding="utf-8")
        self.assertIn("SUPERSEDED BY MEASUREMENT (#48 / #71)", text)
        self.assertIn("## Proposed Phase 2 interface", text)

    def test_neither_constant_was_ever_implemented(self):
        """The banner's own evidence. If one of these appears in the code, the proposal was
        implemented after all and the banner is now lying to its reader -- reopen #48 before
        making this test green."""
        for name in NEVER_IMPLEMENTED:
            found = [p for p in python_sources()
                     if re.search(rf"\b{name}\b", p.read_text(encoding="utf-8", errors="replace"))]
            self.assertEqual(found, [],
                             f"CDME_CONTRACTS.md states {name} exists nowhere; it now exists in "
                             f"{[str(p) for p in found]}")

    def test_the_search_would_actually_find_an_implementation(self):
        """Non-vacuity for the guard above: prove the search is live by pointing it at a name
        this repo really does define. Without this, a broken `python_sources()` returning nothing
        would pass the absence test forever."""
        found = [p for p in python_sources()
                 if re.search(r"\bNECESSITY_SURVIVAL_WEIGHT\b",
                              p.read_text(encoding="utf-8", errors="replace"))]
        self.assertIn(Path("pick_synthesis.py"), found)

    def test_this_files_own_mentions_do_not_count_as_an_implementation(self):
        """The one exclusion, pinned. This module names both constants to search for them, so it
        matches its own search -- the doc index's self-classification bug in a second place."""
        self.assertNotIn(Path(SELF), python_sources())
        self.assertTrue(any(name in Path(SELF).read_text(encoding="utf-8")
                            for name in NEVER_IMPLEMENTED),
                        "non-vacuity: the exclusion only matters because this file does match")

    def test_necessity_still_reads_the_cost_that_replaced_it(self):
        """The other half of the claim, and the one that could regress silently. #48's finding
        was not "do nothing" -- it was that necessity reads `positional_forfeit`, the NEXT-TURN
        cost, rather than `waiting_cost`, the end-of-draft one."""
        source = Path("pick_synthesis.py").read_text(encoding="utf-8")
        self.assertIn("WHY THIS TERM AND NOT waiting_cost", source,
                      "the rejection is recorded at the site; if that comment moved, so did the "
                      "decision, and CDME_CONTRACTS.md's banner needs re-checking")
        self.assertIn('c.get("positional_forfeit")', source)


class TheTopBannerDescribesTheDocumentsRealShape(unittest.TestCase):
    def test_the_live_sections_and_the_archive_are_both_named(self):
        """The document is ~9.5k lines: three contracts, then appendices recording
        investigations in place. A reader who takes the whole thing as current reads settled
        forks and refuted conclusions as live design."""
        text = CONTRACTS.read_text(encoding="utf-8")
        head = "\n".join(text.splitlines()[:20])
        self.assertIn("PART LIVE CONTRACT, PART ARCHIVED INVESTIGATION", head,
                      "the shape declaration must be in the opening, where it is read")
        self.assertIn("Appendix — the decision-path investigation", text,
                      "non-vacuity: the archive boundary the banner names must exist")

    def test_the_original_draft_banner_is_preserved_unedited(self):
        """Corrections are made in place and the original is kept. The DRAFT gate is the
        owner's to open; annotating around it must never look like lifting it."""
        text = CONTRACTS.read_text(encoding="utf-8")
        self.assertIn("**Status: DRAFT — awaiting sign-off.** No Phase 2 code is written "
                      "against these until the\n> project owner approves them.", text)


if __name__ == "__main__":
    unittest.main()
