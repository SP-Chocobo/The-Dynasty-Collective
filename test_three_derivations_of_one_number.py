"""MANDATE 4 / `#126` -- the team count, the round number, and the transcribed-file set.

Three vocabularies that AGREED on every input in hand, which is the hardest kind to justify
repairing and the reason Tier 4 names the input that would split each one:

  * THE TEAM COUNT had three derivations and only one had a fallback: `len(round_1_order)` in the
    Draft Room, `league.get("total_rosters")` a few lines from it, and
    `total_rosters or len({roster_id}) or 1` in the engine. The input that splits them is a draft
    with fewer seats than the league has rosters -- at which point the screen and the engine price
    the same board against different counts, and every replacement level with them.

  * THE ROUND NUMBER had three copies of `n // teams + 1`. `#52` phase 6 records a version that
    lagged by one at every round boundary: `mode="auto"` switched to upside scoring a pick late, and
    a battery reported a 168/132 split the trajectory did not produce. One copy drifting is enough.

  * THE TRANSCRIBED-FILE SET had two literals, byte-identical. The input that splits them is a
    third transcribed file: added to one, it changes provenance and leaves the board's confidence
    tier behind, or the reverse.

WHAT THE TEAM-COUNT REPAIR DOES NOT DO, stated because the difference is easy to mistake for a
remaining defect. `team_count` gives ONE derivation with a stated order of authority; it does not
give both callers the same INPUTS. The Draft Room has the draft's own seats and passes them; the
engine is not handed a pick order and passes the league and its picks. Where both are available they
agree, because a Sleeper draft's round-one order has one seat per roster. What has changed is that
the rule for resolving a disagreement now exists, in one place, and is testable.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

import data_merger as dm
import draft_room as dr
import league_config as lc
import ui_source

_HERE = Path(__file__).parent


def _source(module):
    return (_HERE / module).read_text(encoding="utf-8")


class TheTeamCountHasOneDerivationTests(unittest.TestCase):
    def test_the_draft_own_seats_win_over_the_league_record(self):
        """The case that splits the old three: a ten-seat draft in a twelve-roster league."""
        self.assertEqual(
            lc.team_count({"total_rosters": 12}, pick_order=[str(i) for i in range(1, 11)]), 10)

    def test_the_league_record_answers_when_no_draft_is_in_hand(self):
        self.assertEqual(lc.team_count({"total_rosters": 12}), 12)

    def test_a_repeated_seat_is_counted_once(self):
        """`pick_order` is the whole snake, not round one -- every seat appears many times."""
        order = ["1", "2", "3"] * 14
        self.assertEqual(lc.team_count({"total_rosters": 12}, pick_order=order), 3)

    def test_the_picks_fallback_is_a_floor_and_is_kept(self):
        """Dropping a fallback is a behaviour change dressed as a cleanup. A roster that has not
        picked yet is invisible here, which is why the docstring calls it a floor."""
        self.assertEqual(lc.team_count({}, picks=[{"roster_id": "a"}, {"roster_id": "b"},
                                                  {"roster_id": "a"}]), 2)

    def test_the_last_resort_is_one_and_not_zero(self):
        """Not a team count -- what the arithmetic needs to not divide by zero, preserved from the
        engine's own reading rather than improved, because a one-team league puts every replacement
        level at its position's best player and that is worth leaving visible."""
        self.assertEqual(lc.team_count({}), 1)
        self.assertEqual(lc.team_count(None), 1)

    def test_neither_consumer_derives_it_itself_any_more(self):
        self.assertNotIn("num_teams = len(round_1_order)", ui_source.text())
        self.assertNotIn('league.get("total_rosters") or len({p.get("roster_id")', _source("draft_room.py"))

    def test_both_consumers_call_the_one_function(self):
        for module_source, label in ((_source("draft_room.py"), "draft_room"),
                                     (ui_source.text(), "the UI")):
            calls = {node.func.attr for node in ast.walk(ast.parse(module_source))
                     if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
            self.assertIn("team_count", calls, f"{label} does not ask for the team count")


class TheRoundNumberHasOneDerivationTests(unittest.TestCase):
    def test_the_next_pick_after_n_completed(self):
        self.assertEqual(lc.round_of(0, 12), 1)
        self.assertEqual(lc.round_of(11, 12), 1)
        self.assertEqual(lc.round_of(12, 12), 2)

    def test_the_round_boundary_that_used_to_lag(self):
        """`#52` phase 6: with 168 picks complete in a 12-team draft the next pick is 15.01, and the
        old reading said 14."""
        self.assertEqual(lc.round_of(168, 12), 15)
        self.assertEqual(lc.round_of(167, 12), 14)

    def test_no_team_count_returns_None_rather_than_a_guess(self):
        """A caller with another way to answer should use it; one without should not be handed a
        number derived from nothing."""
        self.assertIsNone(lc.round_of(24, 0))
        self.assertIsNone(lc.round_of(24, None))

    def test_the_arithmetic_is_spelled_nowhere_else(self):
        for module in ("draft_room.py", "pick_synthesis.py", "draft_strategy.py"):
            self.assertNotIn("// num_teams + 1", _source(module),
                             f"{module} spells the round arithmetic again")
        self.assertNotIn("// num_teams + 1", ui_source.text(),
                         "the UI spells the round arithmetic again")

    def test_the_engine_keeps_its_own_fallback_at_its_own_site(self):
        """Reading a pick's recorded round is a DIFFERENT source and is not round_of's business --
        so the fallback stays where the caller that has it lives."""
        self.assertIn('max((p.get("round") or 1) for p in demand_source)', _source("draft_room.py"))


class TheTranscribedFileSetHasOneDefinitionTests(unittest.TestCase):
    def test_the_two_names_are_the_same_object(self):
        self.assertIs(dr.KDST_SEEDED_SOURCE_FILES, dm.TRANSCRIBED_SOURCE_FILES,
                      "an alias is not a second home; a second literal was")

    def test_the_filenames_are_spelled_once(self):
        for filename in ("sleeper_kicker_projections.csv", "sleeper_dst_projections.csv"):
            occurrences = _source("draft_room.py").count(f'"{filename}"')
            self.assertEqual(occurrences, 0,
                             f"{filename} is spelled in draft_room again ({occurrences}x)")
            self.assertEqual(_source("data_merger.py").count(f'"{filename}"'), 1,
                             f"{filename} is spelled more than once in its own home")

    def test_the_set_still_holds_both_files(self):
        """Non-vacuity: an alias to an empty set would satisfy everything above."""
        self.assertEqual(dr.KDST_SEEDED_SOURCE_FILES,
                         {"sleeper_kicker_projections.csv", "sleeper_dst_projections.csv"})

    def test_the_private_name_is_gone_rather_than_left_as_a_shim(self):
        self.assertFalse(hasattr(dm, "_TRANSCRIBED_SOURCE_FILES"),
                         "the old private name survives, so a reader can still pick the wrong one")


class TheUndraftedSlotSetHasOneDefinitionTests(unittest.TestCase):
    """`draft_room.HORIZON_UNDRAFTED_SLOTS` held ("IR",) and `league_config.UNDRAFTED_SLOTS` holds
    the same one for the same reason, so `draftable_slots_per_team` was a reimplementation of
    `len(draftable_slots(...))` around a second copy of its slot set."""

    ROSTERS = (
        ["QB", "RB", "WR", "TE", "FLEX", "K", "BN", "BN", "IR", "TAXI"],
        ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "SUPER_FLEX", "K", "IDP_FLEX"] + ["BN"] * 6,
        ["QB", "RB", "WR", "BN"],
        [],
    )

    def test_the_second_copy_is_gone_rather_than_aliased(self):
        self.assertFalse(hasattr(dr, "HORIZON_UNDRAFTED_SLOTS"),
                         "the old name survives, so a reader can still pick the wrong one")
        self.assertNotIn("HORIZON_UNDRAFTED_SLOTS", _source("draft_room.py").replace(
            "# HORIZON_UNDRAFTED_SLOTS WAS HERE", ""),
            "the name is still referenced outside the note recording its removal")

    def test_the_two_functions_agree_on_every_roster_shape(self):
        for roster in self.ROSTERS:
            with self.subTest(roster=roster):
                self.assertEqual(dr.draftable_slots_per_team(roster),
                                 len(lc.draftable_slots(roster)))

    def test_IR_is_excluded_and_TAXI_is_not(self):
        """The distinction the set exists for: rookie picks land on the taxi squad, so a draft does
        fill those; nobody drafts onto injured reserve."""
        self.assertEqual(dr.draftable_slots_per_team(["QB", "TAXI"]), 2)
        self.assertEqual(dr.draftable_slots_per_team(["QB", "IR"]), 1)

    def test_it_is_not_just_the_roster_length(self):
        """Non-vacuity: if no roster in the set carried an IR slot, delegation would be untestable
        and `len(roster_positions)` would pass every assertion above."""
        with_ir = [r for r in self.ROSTERS if "IR" in r]
        self.assertTrue(with_ir, "no fixture carries an IR slot, so nothing here is being excluded")
        for roster in with_ir:
            self.assertLess(dr.draftable_slots_per_team(roster), len(roster))


if __name__ == "__main__":
    unittest.main()
