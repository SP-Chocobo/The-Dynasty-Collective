"""§7.4: the allowlist gates a NUMBER, and nothing else.

The ruling this file holds the code to: **allowlist what feeds the composite; prose stays free.**
Two failure directions matter and they are not symmetric.

  A false ACCEPT is the one §7.4 measured -- a fabricated or paywalled citation carrying a rank
  into composite_player_score. That is the defect.

  A false REJECT is quieter and still real: a genuine panel-vetted finding losing its number
  because a model wrote "Keep Trade Cut" instead of "KeepTradeCut". So the spelling variants
  below are not politeness, they are the other half of the requirement.
"""

import re
import unittest
from pathlib import Path

import source_policy

_HERE = Path(__file__).parent


class TheCitationsTheAuditMeasuredAsAcceptedTests(unittest.TestCase):
    """Verbatim from ARCHITECTURE_AUDIT.md 7.4, which ran these through the real parser and
    recorded both as accepted with a rank attached."""

    def test_a_fabricated_paywalled_domain_cannot_move_a_number(self):
        self.assertFalse(source_policy.feeds_composite(
            "totally-not-a-real-site.example/paywalled"))

    def test_an_anonymous_forum_post_cannot_move_a_number(self):
        self.assertFalse(source_policy.feeds_composite("an anonymous forum post"))


class RealCitationsAreNotLostToSpellingTests(unittest.TestCase):
    def test_every_documented_source_is_admitted_in_the_shapes_a_model_writes(self):
        for citation, expected in [
            ("ESPN", "espn"),
            ("ESPN's Field Yates", "espn"),
            ("espn.com fantasy staff", "espn"),
            ("FantasyPros", "fantasypros"),
            ("per FantasyPros ECR", "fantasypros"),
            ("Fantasy Pros consensus", "fantasypros"),
            ("KeepTradeCut", "keeptradecut"),
            ("Keep Trade Cut", "keeptradecut"),
            ("KTC", "keeptradecut"),
            ("DynastyProcess", "dynastyprocess"),
            ("Dynasty Process values", "dynastyprocess"),
            ("Sleeper", "sleeper"),
        ]:
            with self.subTest(citation=citation):
                self.assertEqual(source_policy.admits(citation), expected)


class TheMatchIsOnTokensNotSubstringsTests(unittest.TestCase):
    """A substring test would admit any domain containing an allowlisted name, which is exactly
    how a lookalike gets through. These are the cases that separate the two designs."""

    def test_a_name_glued_into_a_larger_token_is_refused(self):
        """What token matching actually buys: 'espn' is not admitted merely because those four
        letters appear inside a longer word. A substring test would accept all of these."""
        for citation in ("espnfake.example", "notespn.com", "myespn", "fantasyprosy",
                         "unkeeptradecut"):
            with self.subTest(citation=citation):
                self.assertFalse(source_policy.feeds_composite(citation))

    def test_scattered_words_are_not_a_citation(self):
        """('keep','trade','cut') must appear consecutively -- a sentence that happens to contain
        all three words is not a citation of KeepTradeCut."""
        self.assertIsNone(source_policy.admits(
            "keep the pick, trade the other one, and cut nobody"))

    def test_an_empty_or_missing_citation_admits_nothing(self):
        for citation in ("", "   ", None):
            with self.subTest(citation=citation):
                self.assertFalse(source_policy.feeds_composite(citation))


class WhatThisCheckCannotDoIsStatedTests(unittest.TestCase):
    """A check whose limits are unstated gets trusted past them -- the pattern this repository
    keeps repairing. These tests pin the limits so they cannot be quietly forgotten."""

    def test_a_hostile_string_containing_a_real_source_name_as_a_token_still_passes(self):
        """The honest boundary, and it is wider than it first looks. Once a real source name
        appears as its OWN token, the citation is admitted -- a mirror domain, a leak site, or a
        plain fabrication that names ESPN all get through:

            'fantasypros-mirror.example'      -> fantasypros
            'keeptradecut.fake.example/leaked'-> keeptradecut
            'ESPN (fabricated)'               -> espn

        Tightening this would mean heuristics over free text, and those fail in the direction
        that costs more here: a genuine finding silently losing its number. So this check answers
        exactly one question -- *does this citation name an allowlisted source* -- and never
        *is this citation truthful*. What stands against the strings above is the panel gate
        upstream and 6.2a's second adjudication downstream, which is why the two were built
        together rather than either being treated as sufficient alone."""
        for citation in ("fantasypros-mirror.example", "keeptradecut.fake.example/leaked",
                         "ESPN (fabricated)"):
            with self.subTest(citation=citation):
                self.assertTrue(source_policy.feeds_composite(citation))

    def test_the_module_filters_nothing_and_deletes_nothing(self):
        """'Prose stays free' as a property of the code, not just of the docstring: this module
        exposes only predicates. If it ever grows a function that drops, rewrites or hides a
        finding, that is a different policy than the one that was ruled."""
        source = (_HERE / "source_policy.py").read_text()
        for forbidden in (" del ", ".pop(", ".remove(", "unlink", "rewrite"):
            self.assertNotIn(forbidden, source, forbidden)


class TheListMatchesThisRepositorysOwnProvenanceRecordsTests(unittest.TestCase):
    """The rule that keeps the allowlist from being an opinion: a source earns composite
    authority by having its origin documented HERE. Checked in both directions, because each
    direction fails differently -- an undocumented entry is an unearned promotion, and an
    undeclared documented source is a silent demotion."""

    def _documented_sources(self) -> set[str]:
        external = {path.name for path in (_HERE / "data/baseline/external").iterdir()
                    if path.is_dir() and (path / "ATTRIBUTION.md").exists()}
        if (_HERE / "data/baseline/sleeper_projection_provenance.json").exists():
            external.add("sleeper")
        return external

    def test_every_allowlisted_source_has_a_provenance_record(self):
        self.assertEqual(set(source_policy.COMPOSITE_ALLOWLIST) - self._documented_sources(),
                         set(), "allowlisted with no provenance record in this repo")

    def test_every_documented_source_is_on_the_allowlist(self):
        self.assertEqual(self._documented_sources() - set(source_policy.COMPOSITE_ALLOWLIST),
                         set(), "documented here but silently unable to feed the composite")

    def test_the_paid_vendor_is_not_on_this_list_and_does_not_need_to_be(self):
        """It reaches the composite as a FILE, through the loader's own source table (7.3's code
        allowlist), never as a model's citation -- so its absence here is correct, not an
        oversight. Asserted on the shape rather than the name, per the 7.10 ruling."""
        for canonical in source_policy.COMPOSITE_ALLOWLIST:
            self.assertNotIn("shark", canonical)


class TheSpellingsAreWellFormedTests(unittest.TestCase):
    def test_every_spelling_is_a_tuple_of_bare_lowercase_tokens(self):
        """A spelling containing punctuation or a capital could never match, since `tokens`
        lowercases and splits -- so it would be a dead entry that looks like coverage."""
        for canonical, spellings in source_policy.COMPOSITE_ALLOWLIST.items():
            with self.subTest(source=canonical):
                self.assertTrue(spellings, "a source with no spellings can never match")
                for spelling in spellings:
                    self.assertIsInstance(spelling, tuple)
                    for token in spelling:
                        self.assertTrue(re.fullmatch(r"[a-z0-9]+", token), token)

    def test_the_canonical_name_is_itself_one_of_its_spellings(self):
        for canonical in source_policy.COMPOSITE_ALLOWLIST:
            with self.subTest(source=canonical):
                self.assertEqual(source_policy.admits(canonical), canonical)


if __name__ == "__main__":
    unittest.main()
