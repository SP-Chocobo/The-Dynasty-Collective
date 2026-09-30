"""D10 / `C-F4` -- the owner's ruling: price it, and make the warning as loud as the consequence.

> *Price it, but modulate how loudly the warning is to the impact that that missing data has on
> the decision ... telling on ourselves extra loud may be undercutting our authority when an
> asterisk may be enough.*

`league_config` described refusal machinery -- AMBIGUOUS as "the only blocking state", ambiguity
"enforced" -- that has **no production caller**. Nothing refused, and the warning that did run said
the same thing at the same volume whether the unparsed label cost a starting slot or nothing at all.

THE THREE BANDS ARE WHAT IS KNOWABLE, not a severity scale someone picked (`#56`). Dropping a slot
label matters exactly insofar as that slot starts a player, and the engine can settle that in two
cases and not in the third:

  * normalises to BN/TAXI/IR -> the solver excludes those anyway, so the consequence is **zero**;
  * normalises to a position or flex slot -> the engine can name the slot lost and count what is
    left, so it is loud AND specific;
  * normalises to nothing -> it may start a player, the error cannot be bounded, and saying so is
    the loud case.

`#56` is why no threshold appears anywhere here: a band is a fact about what the engine can
determine, never a number chosen to make a message feel proportionate.
"""

from __future__ import annotations

import unittest

import league_config as lc
import ui_source

#: A clean league. Nine starting slots, a bench, an IR.
CLEAN = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF", "BN", "BN", "IR"]


def _kinds(roster_positions):
    league = {"roster_positions": roster_positions, "total_rosters": 12,
              "settings": {"type": 2}, "scoring_settings": {"rec": 1.0}}
    return {item["kind"]: item["detail"] for item in lc.ambiguities(league)}


class TheThreeBandsAreDistinctTests(unittest.TestCase):

    def test_the_kinds_are_three_different_strings(self):
        kinds = {lc.AMBIGUITY_UNKNOWN_SLOT, lc.AMBIGUITY_UNKNOWN_SLOT_NONPLAYING,
                 lc.AMBIGUITY_UNKNOWN_SLOT_STARTER}
        self.assertEqual(len(kinds), 3)

    def test_only_the_zero_consequence_band_is_immaterial(self):
        """The set a consumer scales on. If the unresolvable kind ever joined it, the loudest case
        in the vocabulary would render as an asterisk."""
        self.assertEqual(lc.IMMATERIAL_AMBIGUITY_KINDS,
                         frozenset({lc.AMBIGUITY_UNKNOWN_SLOT_NONPLAYING}))
        self.assertNotIn(lc.AMBIGUITY_UNKNOWN_SLOT, lc.IMMATERIAL_AMBIGUITY_KINDS)
        self.assertNotIn(lc.AMBIGUITY_UNKNOWN_SLOT_STARTER, lc.IMMATERIAL_AMBIGUITY_KINDS)


class NormalisationDoesNotInventKnowledgeTests(unittest.TestCase):
    """The one place this repair could overreach: deciding that an unknown label "obviously means"
    a known one. Case and separators are typography; `RES` -> `IR` would be a claim about the
    vendor's vocabulary that nothing here measured."""

    def test_case_and_separators_are_the_same_label(self):
        for spelled in ("bn", "Bn", " BN ", "B_N", "B-N", "B.N"):
            with self.subTest(spelled=spelled):
                self.assertEqual(lc.normalised_slot(spelled), "BN")

    def test_a_separator_variant_of_a_flex_slot_resolves(self):
        self.assertEqual(lc.normalised_slot("super-flex"), lc.normalised_slot("SUPER_FLEX"))

    def test_an_industry_abbreviation_is_NOT_silently_equated(self):
        """`RES`, `PS`, `OUT` are real labels in other products and may well mean a non-playing
        slot. This app has not measured that, so it must not act as though it had -- they stay
        unresolvable, which is the LOUD band."""
        for guess in ("RES", "PS", "OUT", "SUSP"):
            with self.subTest(guess=guess):
                self.assertNotIn(lc.normalised_slot(guess),
                                 {lc.normalised_slot(s) for s in lc.NON_PLAYING_SLOTS})


class TheVolumeFollowsTheConsequenceTests(unittest.TestCase):

    def test_a_misspelled_bench_slot_is_the_QUIET_band(self):
        kinds = _kinds(CLEAN + ["Bn"])
        self.assertIn(lc.AMBIGUITY_UNKNOWN_SLOT_NONPLAYING, kinds)
        self.assertNotIn(lc.AMBIGUITY_UNKNOWN_SLOT, kinds)
        detail = kinds[lc.AMBIGUITY_UNKNOWN_SLOT_NONPLAYING]
        self.assertIn("costs nothing", detail)
        self.assertIn("9 starting slots", detail,
                      "the quiet message does not state the lineup it was priced on, so a reader "
                      "cannot check the claim that nothing moved")

    def test_a_misspelled_STARTING_slot_is_loud_AND_names_the_damage(self):
        kinds = _kinds(CLEAN + ["super-flex"])
        self.assertIn(lc.AMBIGUITY_UNKNOWN_SLOT_STARTER, kinds)
        detail = kinds[lc.AMBIGUITY_UNKNOWN_SLOT_STARTER]
        self.assertIn("SUPER_FLEX", detail, "the message does not say which slot was lost")
        self.assertIn("9 starting slots", detail)
        self.assertIn("10", detail, "the message does not say what the league actually declares")

    def test_an_UNRESOLVABLE_label_is_loud_and_says_it_cannot_bound_the_error(self):
        kinds = _kinds(CLEAN + ["WIZARD"])
        self.assertIn(lc.AMBIGUITY_UNKNOWN_SLOT, kinds)
        detail = kinds[lc.AMBIGUITY_UNKNOWN_SLOT]
        self.assertIn("cannot bound", detail,
                      "the loudest case must say that the SIZE of the error is what is unknown, "
                      "rather than implying a size")

    def test_a_clean_league_raises_none_of_the_three(self):
        """NON-VACUITY. A gate that always fires teaches the reader to close it."""
        kinds = _kinds(CLEAN)
        for kind in (lc.AMBIGUITY_UNKNOWN_SLOT, lc.AMBIGUITY_UNKNOWN_SLOT_NONPLAYING,
                     lc.AMBIGUITY_UNKNOWN_SLOT_STARTER):
            self.assertNotIn(kind, kinds)

    def test_the_bands_are_reported_SEPARATELY_when_both_occur(self):
        """One roster can carry both a harmless misspelling and a real one, and folding them into
        one message would make the loud one quiet or the quiet one loud."""
        kinds = _kinds(CLEAN + ["Bn", "WIZARD"])
        self.assertIn(lc.AMBIGUITY_UNKNOWN_SLOT_NONPLAYING, kinds)
        self.assertIn(lc.AMBIGUITY_UNKNOWN_SLOT, kinds)


class TheBoardIsStillPricedTests(unittest.TestCase):
    """The ruling's first word. C-F4's contract claimed AMBIGUOUS was "the only blocking state";
    nothing blocked, and the owner ruled that nothing should."""

    def test_ambiguities_reports_rather_than_raising(self):
        for roster in (CLEAN + ["WIZARD"], CLEAN + ["Bn"], ["WIZARD"]):
            with self.subTest(roster=roster):
                found = lc.ambiguities({"roster_positions": roster, "total_rosters": 12,
                                        "settings": {"type": 2}, "scoring_settings": {"rec": 1.0}})
                self.assertIsInstance(found, list)


class BothSurfacesScaleThroughTheSameSetTests(unittest.TestCase):
    """Read through `ui_source`, never off `app.py` directly -- `test_ui_source`'s own rule, and
    it applies here because this is a claim about the UI surface."""

    def setUp(self):
        self.source = ui_source.text()

    def test_the_UI_splits_on_the_shared_set_and_not_on_kind_strings(self):
        self.assertIn("IMMATERIAL_AMBIGUITY_KINDS", self.source,
                      "the UI does not scale through league_config's set, so a kind added later "
                      "is loud on one surface and quiet on another")
        for literal in ('"unknown_slot_nonplaying"', "'unknown_slot_nonplaying'"):
            self.assertNotIn(literal, self.source,
                             "the UI matches a kind string by hand instead of reading the set")

    def test_a_stored_record_with_no_kind_is_treated_as_LOUD(self):
        """A board stored before D10 was never classified, and presenting an unclassified
        ambiguity as harmless is the single error this whole item exists to prevent."""
        self.assertIn('i.get("kind")', self.source,
                      "the replay surface reads `kind` in a way that would KeyError or "
                      "mis-default on a record written before this field existed")


if __name__ == "__main__":
    unittest.main()
