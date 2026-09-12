"""DOC_INDEX.md is DERIVED. A derived artifact that can go stale is a liability, not an asset.

The index exists so a cold reader can tell live evidence from retracted history without opening
a hundred files. That only works if it matches the tree; a stale index is worse than none,
because it looks authoritative.
"""

from __future__ import annotations

import unittest

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

    def test_every_document_lands_in_exactly_one_bucket(self):
        buckets = doc_index.index()
        counted = sum(len(v) for v in buckets.values())
        self.assertEqual(counted, len(doc_index.docs()))


if __name__ == "__main__":
    unittest.main()
