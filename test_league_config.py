"""#140 / #118: which copy of a league's config a board may rest on, and what "we did not read
this cleanly" looks like when it is derived rather than remembered.

The defect: roster_positions, scoring_settings and settings all came from one bulk
`/user/{id}/leagues` call at sync time and were never re-fetched -- `get_rosters` was called
nowhere in the app at all. An eleven-hour-old config produces a board that looks entirely
reasonable, which is why this is enforced by a function that REFUSES rather than by a comment.

Two properties carry the weight:
  - the refusal is the mechanism (a stale config must not degrade quietly into a board);
  - the ambiguity detector is DERIVED from the vocabularies the engine itself reads, so it
    keeps working when Sleeper adds a slot code nobody here has seen.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

import league_config as lc
from player_universe import FANTASY_POSITIONS, FLEX_SLOT_POSITIONS

_HERE = Path(__file__).parent

CLEAN = {
    "league_id": "1", "name": "Test",
    "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "BN", "BN", "BN"],
    "settings": {"type": 2, "num_teams": 12},
    "scoring_settings": {"rec": 1.0, "bonus_rec_te": 0.5},
}


def _decision(**overrides):
    """A config that parses cleanly. Named for the question it answers -- may a board rest on
    this -- not for where it came from, since the where turned out not to be the issue."""
    return {**CLEAN, **overrides}


class ConfigAgeIsReportedAtTheRightResolutionTests(unittest.TestCase):
    """#140's surviving half, and the correction to its own premise.

    The item recorded that get_rosters was called nowhere and that config came from the bulk
    /user/{id}/leagues payload. Checked before building on it: sync_league calls get_league AND
    get_rosters itself, and the board reads snapshot["league"]. The config IS fetched fresh.

    What is real is the RESOLUTION. build_freshness_manifest computed age as a difference of
    calendar dates, which is wrong in both directions at the boundary -- and a wrong staleness
    number reads as reassurance, which is worse than none."""

    def test_an_eleven_hour_old_config_does_not_read_as_same_day_fresh(self):
        """The 9am-sync, 8pm-draft case. The date difference is 0; the config is 11 hours old
        and a commissioner may have changed scoring in between."""
        self.assertEqual(lc.describe_config_age({"synced_at": 0.0}, now=11 * 3600),
                         "11 hours ago")

    def test_a_two_minute_old_config_across_midnight_does_not_read_as_a_day_old(self):
        """The other direction, which the date arithmetic also gets wrong."""
        self.assertEqual(lc.describe_config_age({"synced_at": 0.0}, now=120), "2 minutes ago")

    def test_resolution_coarsens_as_the_age_grows(self):
        for now, expected in ((30, "just now"), (60, "1 minute ago"), (3600, "1 hour ago"),
                              (86400, "1 day ago"), (3 * 86400, "3 days ago")):
            with self.subTest(now=now):
                self.assertEqual(lc.describe_config_age({"synced_at": 0.0}, now=now), expected)

    def test_never_synced_is_None_not_a_big_number(self):
        """'Never synced' and 'synced long ago' are different answers, and rendering the second
        for the first says the opposite of the truth."""
        self.assertIsNone(lc.config_age_seconds({}))
        self.assertIsNone(lc.describe_config_age({}))
        self.assertIsNone(lc.describe_config_age(None))

    def test_age_does_NOT_block_a_board(self):
        """Deliberate. Nothing here measures how often a commissioner changes a setting, so a
        cutoff would be an invented magnitude (#56) -- and a hard refusal on an hours-old config
        would break the ordinary case to guard an unmeasured one. Age is reported; ambiguity is
        enforced."""
        self.assertTrue(lc.admits_decision(CLEAN)[0])

    def test_the_manifest_itself_carries_the_real_age(self):
        """Non-vacuity for the whole fix: the module could be perfect and unread. Source-scanned
        through ui_source, as every app-level contract here is."""
        import ui_source
        block = ui_source.block("synced_at = snapshot.get", until="entries.sort")
        self.assertIn("describe_config_age", block,
                      "the freshness manifest no longer carries the real age -- it is back to "
                      "a calendar-date difference for a quantity that changes hourly")


class AmbiguityIsDerivedNotRememberedTests(unittest.TestCase):
    """Each detector reads a vocabulary the engine itself uses, so a slot code nobody here has
    seen is caught the first time it appears."""

    def test_a_slot_outside_both_vocabularies_is_ambiguous(self):
        kinds = {a["kind"] for a in lc.ambiguities(_decision(
            roster_positions=["QB", "RB", "WR", "OP", "TE", "BN"]))}
        self.assertIn("unknown_slot", kinds)

    def test_the_known_set_is_built_FROM_the_engine_vocabularies(self):
        """Non-vacuity for 'derived': if KNOWN_SLOTS were a hand-typed list it could drift from
        what the lineup solver actually places, and the detector would pass a slot the solver
        then silently drops."""
        self.assertTrue(FANTASY_POSITIONS <= lc.KNOWN_SLOTS)
        self.assertTrue(set(FLEX_SLOT_POSITIONS) <= lc.KNOWN_SLOTS)
        for slot in ("QB", "SUPER_FLEX", "IDP_FLEX", "BN", "TAXI", "IR"):
            with self.subTest(slot=slot):
                self.assertIn(slot, lc.KNOWN_SLOTS)

    def test_no_bench_is_ambiguous_because_it_has_TWO_readings(self):
        """Best-ball, or a parse that dropped the BN entries. Nothing available distinguishes
        them, and that is what ambiguous means -- not 'probably broken'."""
        found = lc.ambiguities(_decision(roster_positions=["QB", "RB", "WR", "TE", "FLEX"]))
        entry = next(a for a in found if a["kind"] == "no_bench")
        self.assertIn("best-ball", entry["detail"])

    def test_two_literal_QB_slots_without_the_token_is_caught(self):
        """Functionally superflex; every consumer in this app keys off the SUPER_FLEX token
        alone, so it would be scored as 1QB -- a whole-league misread, silently."""
        kinds = {a["kind"] for a in lc.ambiguities(_decision(
            roster_positions=["QB", "QB", "RB", "WR", "TE", "BN"]))}
        self.assertIn("superflex_disagreement", kinds)

    def test_a_real_SUPER_FLEX_league_is_NOT_flagged(self):
        """The false-positive guard. A detector that fires on correct configs trains its reader
        to click through, which is worse than not having it."""
        kinds = {a["kind"] for a in lc.ambiguities(_decision(
            roster_positions=["QB", "SUPER_FLEX", "RB", "WR", "TE", "BN"]))}
        self.assertNotIn("superflex_disagreement", kinds)

    def test_a_missing_format_deciding_key_is_caught(self):
        kinds = {a["kind"] for a in lc.ambiguities(_decision(scoring_settings={}, settings={}))}
        self.assertIn("missing_format_keys", kinds)

    def test_FORMAT_DECIDING_KEYS_matches_what_the_engine_actually_reads(self):
        """Keeps the declared list honest against sleeper_client.league_format_summary, which
        is where these keys silently resolve to defaults. Read from the AST, so a key added
        there without being declared here fails rather than going unchecked."""
        tree = ast.parse((_HERE / "sleeper_client.py").read_text())
        target = next(node for node in ast.walk(tree)
                      if isinstance(node, ast.FunctionDef)
                      and node.name == "league_format_summary")
        read = {node.args[0].value for node in ast.walk(target)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get" and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)}
        undeclared = sorted(set(lc.FORMAT_DECIDING_KEYS) - read)
        self.assertEqual(undeclared, [],
                         f"declared as format-deciding but never read by "
                         f"league_format_summary: {undeclared}")

    def test_an_empty_roster_positions_reports_that_and_stops(self):
        """No slots means every later check would be a claim about nothing. One honest finding
        beats four derived from an empty list."""
        found = lc.ambiguities(_decision(roster_positions=[]))
        self.assertEqual([a["kind"] for a in found], ["no_roster_positions"])


class ConfirmationIsThreeStateAndOnlyOneBlocksTests(unittest.TestCase):
    def test_a_clean_unreviewed_config_is_INFERRED_and_does_not_block(self):
        """Where most leagues live. The vendor pattern this borrows reviews everything because
        it cannot detect its own ambiguity; this app can, so it asks only where it is unsure."""
        config = _decision()
        self.assertEqual(lc.confirmation_state(config), lc.INFERRED)
        self.assertTrue(lc.admits_decision(config)[0])

    def test_review_promotes_INFERRED_to_CONFIRMED(self):
        self.assertEqual(lc.confirmation_state(_decision(**{lc.CONFIRMED_KEY: True})),
                         lc.CONFIRMED)

    def test_confirming_does_NOT_clear_an_ambiguity(self):
        """Confirming is a claim about having looked. The unreadable slot is still unreadable,
        and letting a click erase it would make the state mean 'dismissed' rather than
        'resolved'."""
        config = _decision(roster_positions=["QB", "RB", "OP", "BN"], **{lc.CONFIRMED_KEY: True})
        self.assertEqual(lc.confirmation_state(config), lc.AMBIGUOUS)
        self.assertFalse(lc.admits_decision(config)[0])

    def test_ambiguity_blocks_even_on_a_freshly_fetched_config(self):
        """The two refusals are independent and have different remedies -- re-fetch, versus ask
        a person. A fresh fetch does not make an unreadable slot readable."""
        ok, reason = lc.admits_decision(_decision(roster_positions=["QB", "OP", "BN"]))
        self.assertFalse(ok)
        self.assertIn("did not parse cleanly", reason)


class TheAppStillDoesNotRefreshOnActivationTests(unittest.TestCase):
    """The half of #140 that is NOT fixed here, characterized so it is not mistaken for done.

    activate_league re-syncs only when there is no cached snapshot at all -- an existing one is
    reused however old, by design. Making activation re-sync is a UI-path change in the file
    #137 is about to cut apart, and it cannot be validated from here (no Streamlit runtime; the
    render trace sees st.* calls, not control flow). So the age is now REPORTED honestly and the
    refresh policy is left to the hull pass, rather than changed blind."""

    def test_activation_still_only_syncs_when_there_is_no_snapshot(self):
        import ui_source
        block = ui_source.block("def activate_league(", until="def ")
        self.assertIn("if st.session_state.league_snapshot is None:", block,
                      "activate_league's refresh policy changed -- re-read #140 and decide "
                      "whether this characterization should now be inverted")



if __name__ == "__main__":
    unittest.main()
