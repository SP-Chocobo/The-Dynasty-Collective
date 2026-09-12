"""DOC_INDEX.md is DERIVED. A derived artifact that can go stale is a liability, not an asset.

The index exists so a cold reader can tell live evidence from retracted history without opening
a hundred files. That only works if it matches the tree; a stale index is worse than none,
because it looks authoritative.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import doc_index


class TheIndexMatchesTheTree(unittest.TestCase):
    def test_doc_index_is_not_stale(self):
        self.assertEqual(doc_index.main(["--check"]), 0,
                         "DOC_INDEX.md is stale -- run `python3 doc_index.py`")


class TheClassifierIsNotVacuous(unittest.TestCase):
    def test_it_finds_the_documents_it_exists_to_find(self):
        """Non-vacuity: if every file landed in one bucket the index would say nothing."""
        buckets = doc_index.index()
        self.assertGreater(len(buckets["WITHDRAWN"]), 0)
        self.assertGreater(len(buckets["SUPERSEDED"]), 0)
        self.assertGreater(len(buckets["UNDECLARED"]), 0)

    def test_it_matches_stems_not_whole_words(self):
        """The defect the first version had: "withdrawn" does not match a file whose own H1 says
        WITHDRAWAL, and "corrected" does not match one that says CORRECTION. Both exist here."""
        buckets = doc_index.index()
        names = {p.name for p in buckets["WITHDRAWN"]} | {p.name for p in buckets["SUPERSEDED"]}
        for expected in ("WITHDRAWAL_18_residual3_detector.md", "CORRECTION_wrong_universe.md"):
            self.assertIn(expected, names,
                          f"{expected} announces its status in its own H1 and must not read as undeclared")

    def test_worktree_checkouts_are_not_counted_as_documents(self):
        """The defect its own staleness guard caught. A git worktree under `.claude/worktrees/`
        is a CHECKOUT of this repository, not documents belonging to it. Walking them counts
        every file two or three times and makes the index depend on where the tool runs from --
        it was built inside a worktree, where they are absent, and went red the first time the
        full suite ran from the main checkout."""
        for path in doc_index.docs():
            self.assertNotIn("worktrees", path.parts,
                             f"{path} is a worktree copy, not a document of this repo")

    def test_the_document_set_is_exactly_what_git_tracks(self):
        """The rule, stated where it can fail. `docs()` asks git rather than walking and
        subtracting a hand-kept skip list -- the list needed a new entry every time a tool
        invented a new cache directory, and the fourth one it missed (pytest's own generated
        `.pytest_cache/README.md`) had been sitting in the UNDECLARED bucket, counted as a
        document of this repository."""
        tracked = subprocess.run(["git", "ls-files", "-z", "*.md"],
                                 capture_output=True, text=True, check=True)
        expected = sorted(Path(name) for name in tracked.stdout.split("\0") if name)
        self.assertEqual(doc_index.docs(), expected)

    def test_an_untracked_markdown_file_is_not_a_document(self):
        """Non-vacuity for the rule above: prove the exclusion by creating the case. Without
        this, `docs()` could return every .md file in the tree and the equality test would still
        pass on a clean checkout that happens to have no untracked ones."""
        intruder = Path(tempfile.mkdtemp(dir=".", prefix=".doc_index_probe_")) / "README.md"
        try:
            intruder.write_text("# not a document of this repository\n", encoding="utf-8")
            self.assertTrue(intruder.exists())
            self.assertNotIn(intruder, doc_index.docs())
        finally:
            shutil.rmtree(intruder.parent, ignore_errors=True)

    def test_every_document_lands_in_exactly_one_bucket(self):
        buckets = doc_index.index()
        counted = sum(len(v) for v in buckets.values())
        self.assertEqual(counted, len(doc_index.docs()))


if __name__ == "__main__":
    unittest.main()
