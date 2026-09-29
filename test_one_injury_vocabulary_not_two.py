"""MANDATE 4 / `#126` / `#56` -- two hand-listed injury vocabularies with different membership.

`draft_room.RISK_ADJ` listed `{IR, Out, Doubtful}`. `player_universe.GAMES_MISSED_FLOOR` lists
`{IR: 4, PUP: 4, Out: 1}`. Same subject, two homes, and they did not agree: PUP was in one and not
the other, and `app.INJURY_OK_STATUSES` was a third copy of the playable/unavailable split.

THE GAP HAD A MEASURED CONSEQUENCE AT EXACTLY ONE INPUT -- a player with a season line and no
games-played, where the haircut cannot be computed and `RISK_ADJ` is the whole discount:

    status   gp=17                      gp=None
    IR       0.765 haircut, penalty 0    factor 1.0, penalty -18.0
    PUP      0.765 haircut, penalty 0    factor 1.0, penalty   0.0   <- priced FULLY FIT
    Out      0.941 haircut, penalty 0    factor 1.0, penalty -10.0

With `gp` present the two layers agree, because `availability_factor` applies the rule floor and
`health_penalty` stands down to avoid double-counting (`#191`). With `gp` absent PUP fell through
both, and an identical IR player took 18 points.

DERIVED, NOT CHOSEN (`#56`). PUP is not given a new magnitude. It takes IR's, because
GAMES_MISSED_FLOOR gives them the same four-game floor on the same reading of the same NFL rule --
two designations the engine already treats as identically severe cannot carry different penalties
for the same player. That rule is what this module pins, so the next designation added to either
home has to satisfy it rather than pass silently.

WHAT IS NOT REPAIRED HERE, and it is recorded rather than quietly accepted: `Doubtful` is priced
at -5 while `availability_factor` calls it `unrecognised_designation`, because it carries no rule
floor at all. That magnitude WAS chosen, which is `#56` territory and D8's subject, and
RISK_ADJ's own comment already concedes it ("NOT a statement that the remaining magnitudes are
right"). The test below names it as the single licensed exception, so a second chosen magnitude
cannot be added without tripping something.
"""

from __future__ import annotations

import unittest

import draft_room as dr
import player_universe as pu
import ui_source


class TheTwoHomesAgreeOnMembershipTests(unittest.TestCase):
    def test_every_designation_with_a_rule_floor_is_priced(self):
        """The gap PUP fell through. A designation the engine knows costs games must cost value."""
        unpriced = sorted(set(pu.GAMES_MISSED_FLOOR) - set(dr.RISK_ADJ))
        self.assertEqual(unpriced, [],
                         f"{unpriced} carry a rule floor on games missed and no health penalty, so "
                         f"a player with no games-played reported is priced fully fit")

    def test_the_only_priced_designation_without_a_floor_is_the_one_known_to_be_chosen(self):
        """`Doubtful`. Naming it here is what stops a SECOND invented magnitude arriving quietly."""
        chosen = sorted(set(dr.RISK_ADJ) - set(pu.GAMES_MISSED_FLOOR))
        self.assertEqual(chosen, ["Doubtful"],
                         f"{chosen} are priced with no rule floor to derive the number from, which "
                         f"is a chosen magnitude and needs the owner (see D8)")

    def test_both_vocabularies_are_inside_the_recognised_set(self):
        for designation in tuple(dr.RISK_ADJ) + tuple(pu.GAMES_MISSED_FLOOR):
            self.assertIn(designation, pu.RECOGNISED_DESIGNATIONS,
                          f"{designation} is acted on without being declared recognised")


class DesignationsSharingAFloorSharePenaltyTests(unittest.TestCase):
    def test_the_rule_is_not_vacuous(self):
        """It says something only if two designations actually share a floor. IR and PUP do."""
        floors = list(pu.GAMES_MISSED_FLOOR.values())
        self.assertLess(len(set(floors)), len(floors),
                        "no two designations share a rule floor, so the rule below is vacuous and "
                        "PUP's penalty would have had to be chosen after all")

    def test_equal_floors_carry_equal_penalties(self):
        by_floor: dict[int, set] = {}
        for designation, floor in pu.GAMES_MISSED_FLOOR.items():
            if designation in dr.RISK_ADJ:
                by_floor.setdefault(floor, set()).add(dr.RISK_ADJ[designation])
        for floor, penalties in sorted(by_floor.items()):
            self.assertEqual(len(penalties), 1,
                             f"designations with a {floor}-game floor carry different penalties "
                             f"{sorted(penalties)} -- the engine treats them as identically severe "
                             f"and cannot then charge them differently")

    def test_a_steeper_floor_never_costs_less(self):
        """Derived ordering, not a chosen one: more guaranteed games missed cannot be worth more."""
        priced = sorted(((floor, dr.RISK_ADJ[d]) for d, floor in pu.GAMES_MISSED_FLOOR.items()
                         if d in dr.RISK_ADJ), key=lambda pair: pair[0])
        for (small, light), (large, heavy) in zip(priced, priced[1:]):
            if small == large:
                continue
            self.assertLessEqual(heavy, light,
                                 f"a {large}-game floor costs {heavy} while a {small}-game floor "
                                 f"costs {light}")

    def test_PUP_and_IR_are_priced_identically_in_both_states(self):
        """The regression, end to end through the two functions that decide it."""
        for games_played in (17.0, None):
            with self.subTest(gp=games_played):
                ir_factor, ir_basis = pu.availability_factor("IR", games_played)
                pup_factor, pup_basis = pu.availability_factor("PUP", games_played)
                self.assertEqual(ir_factor, pup_factor)
                self.assertEqual(ir_basis, pup_basis)
                self.assertEqual(dr.health_penalty("IR", ir_basis),
                                 dr.health_penalty("PUP", pup_basis))

    def test_a_PUP_player_with_no_games_reported_is_no_longer_priced_fully_fit(self):
        """Stated as its own test because it is the defect, not a corollary of one."""
        _factor, basis = pu.availability_factor("PUP", None)
        self.assertEqual(basis, pu.NO_GAMES_REPORTED)
        self.assertLess(dr.health_penalty("PUP", basis), 0.0,
                        "PUP with a season line and no games-played takes no discount at all")

    def test_the_penalty_still_stands_down_where_the_haircut_already_applied(self):
        """`#191`: the two must not both charge for the same designation."""
        for designation in ("IR", "PUP", "Out"):
            _factor, basis = pu.availability_factor(designation, 17.0)
            self.assertEqual(basis, pu.RULE_FLOOR)
            self.assertEqual(dr.health_penalty(designation, basis), 0.0,
                             f"{designation} is charged twice when games-played is known")


class ThePlayablePillHasOneHomeTests(unittest.TestCase):
    def test_the_ui_reads_the_vocabulary_rather_than_re_listing_it(self):
        """Through ui_source, so the check survives the view being extracted."""
        source = ui_source.text()
        self.assertIn("INJURY_OK_STATUSES = GAME_TIME_CALL_DESIGNATIONS", source,
                      "the UI has gone back to spelling the injury vocabulary itself")
        self.assertNotIn('INJURY_OK_STATUSES = ("Questionable", "Doubtful")', source)

    def test_no_game_time_call_designation_carries_a_rule_floor(self):
        """The two sets are complements within the recognised vocabulary, which is what lets the
        pill ask one question and get an answer about the other."""
        for designation in pu.GAME_TIME_CALL_DESIGNATIONS:
            self.assertNotIn(designation, pu.GAMES_MISSED_FLOOR)

    def test_an_unrecognised_designation_is_NOT_playable(self):
        """Why the set is listed rather than derived as "not in the floor table": that derivation
        is true of every string the feed invents next, and painting an unknown as playable is the
        absence-contract failure UNRECOGNISED_DESIGNATION exists to prevent."""
        for designation in ("Sus", "DNR", "NA", "Cromulent"):
            self.assertNotIn(designation, pu.GAME_TIME_CALL_DESIGNATIONS)
            self.assertNotIn(designation, pu.RECOGNISED_DESIGNATIONS)

    def test_the_immaterial_ruling_sits_inside_the_game_time_calls(self):
        """`Questionable` is immaterial (`#191`) AND a game-time call. If it ever left this set the
        pill would paint it crimson while the engine ignores it entirely."""
        for designation in pu.IMMATERIAL_INJURY_STATUSES:
            self.assertIn(designation, pu.GAME_TIME_CALL_DESIGNATIONS)


if __name__ == "__main__":
    unittest.main()
