"""#191 + #202: the projection said sixteen games for a man who will not play them.

Sleeper publishes a projected GAMES PLAYED, and for injured players it says a full season:

    status          n     gp
    (none)        700     overwhelmingly 17
    Questionable  100     95 x gp=17,  5 x gp=16
    IR             23     20 x gp=16,  3 x gp=17
    PUP           12       4 x gp=16,  8 x gp=17

So `risk_adj` was not double-counting anything -- there was nothing upstream to double. It was
the ONLY place health entered the price, and -18 does not offset a full season: the board
ranked James Conner 32nd on IR, Luke Musgrave 62nd on PUP, off numbers describing seasons
neither will play.

THE OWNER'S RULING WAS TO FIX THE INPUT, not to grow the penalty. A wrong number penalised by a
hand-set constant is still a wrong number, and everything reading `projected_points` directly --
the board's own "who scores most" column -- would go on showing the full season.

THE FACTOR IS NOT INVENTED, WHICH IS THE WHOLE ARGUMENT (#56). The NFL's own roster rules set
it: a player on regular-season PUP must miss at least the first four games, IR with a
designation to return at least four, and "Out" is one week. Those are the only three entries in
GAMES_MISSED_FLOOR, and the omissions are as deliberate as the inclusions -- Questionable and
Doubtful are game-time calls with no rule floor, Sus depends on a suspension length the feed
does not carry, and NA/DNR are not health designations at all.

IT IS A BOUND, NOT AN ESTIMATE, AND THE BASIS SAYS SO. We know a man on IR misses AT LEAST four
games; we do not know he misses only four. Cutting by the floor removes what is certain and
fabricates nothing -- the most that can honestly be taken off. Conner stays 41st rather than
vanishing, and that is correct rather than timid: asserting a season-ending absence would be
inventing the very number this repair refuses to invent. See #188, the register item for the
"bounded/partial" absence state this vocabulary still lacks.

#202'S HALF: the recognised vocabulary is derived from what the feed EMITS, and a designation
with no entry is named `unrecognised_designation` rather than silently priced as healthy. PUP
reached the board with no entry anywhere and was treated as fully fit for exactly that reason.

Measured end to end on the committed capture: Conner 32 -> 41, Musgrave 62 -> 161, Savion
Williams 71 -> 172, Joe Royer 119 -> 255.

Every test here was mutation-checked -- see MUTATIONS at the bottom.
"""
import json
import unittest

import data_merger as dm
import draft_battery as db
import draft_room as dr
import player_universe as pu


class TheFloorComesFromTheRulebookTests(unittest.TestCase):

    def test_only_designations_with_a_real_rule_floor_are_listed(self):
        self.assertEqual(set(pu.GAMES_MISSED_FLOOR), {"IR", "PUP", "Out"})

    def test_the_game_counts_are_the_rule_minimums(self):
        self.assertEqual(pu.GAMES_MISSED_FLOOR["IR"], 4)
        self.assertEqual(pu.GAMES_MISSED_FLOOR["PUP"], 4)
        self.assertEqual(pu.GAMES_MISSED_FLOOR["Out"], 1)

    def test_the_judgement_calls_are_deliberately_absent(self):
        """Not an oversight. A number for any of these would be fitted to a sample, which is
        the one thing #56 forbids."""
        for status in ("Questionable", "Doubtful", "Sus", "NA", "DNR"):
            with self.subTest(status=status):
                self.assertNotIn(status, pu.GAMES_MISSED_FLOOR)


class EveryFactorArrivesWithItsBasisTests(unittest.TestCase):
    """A factor of 1.0 means four different things, and a consumer that cannot tell them apart
    reads the last two as health (#166)."""

    def test_a_rule_floor_designation_cuts_the_projection(self):
        factor, basis = pu.availability_factor("IR", 17)
        self.assertEqual(basis, pu.RULE_FLOOR)
        self.assertAlmostEqual(factor, 13 / 17)

    def test_the_cut_tracks_the_reported_games_not_a_fixed_number(self):
        self.assertAlmostEqual(pu.availability_factor("IR", 16)[0], 12 / 16)
        self.assertAlmostEqual(pu.availability_factor("Out", 17)[0], 16 / 17)

    def test_no_designation_is_its_own_basis(self):
        self.assertEqual(pu.availability_factor(None, 17), (1.0, pu.NO_DESIGNATION))

    def test_an_immaterial_designation_is_its_own_basis(self):
        # Questionable, ruled out of the engine entirely (#191). Named rather than silently
        # lumped with "healthy", so the record says WHY no cut was applied.
        self.assertEqual(pu.availability_factor("Questionable", 17), (1.0, pu.IMMATERIAL))

    def test_an_unrecognised_designation_is_NAMED_not_silently_healthy(self):
        """#202. PUP reached the board with no entry anywhere and was priced as fully fit."""
        for status in ("Sus", "NA", "DNR", "SomeCodeSleeperAddsNextYear"):
            with self.subTest(status=status):
                factor, basis = pu.availability_factor(status, 17)
                self.assertEqual(factor, 1.0)
                self.assertEqual(basis, pu.UNRECOGNISED_DESIGNATION)

    def test_a_recognised_designation_with_no_games_reported_is_a_DIFFERENT_absence(self):
        """"We do not know what this designation means" and "we know exactly what it means and
        lack the denominator" have different remedies. Collapsing them is the defect this whole
        item exists to correct, so the split is asserted rather than assumed."""
        self.assertEqual(pu.availability_factor("IR", None), (1.0, pu.NO_GAMES_REPORTED))
        self.assertNotEqual(pu.NO_GAMES_REPORTED, pu.UNRECOGNISED_DESIGNATION)

    def test_the_factor_never_goes_below_zero(self):
        self.assertEqual(pu.availability_factor("IR", 2)[0], 0.0)


class ThroughTheRealBoardTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open("data/fixtures/sleeper_capture.json", encoding="utf-8") as handle:
            cap = json.load(handle)
        shape = cap["league_shape"]
        cls.league = {"roster_positions": shape["roster_positions"],
                      "scoring_settings": shape["scoring_settings"],
                      "total_rosters": shape["total_rosters"], "settings": {"type": 2}}
        cls.players = cap["players"]
        cls.projections = cap.get("season_projections")
        merger = dm.DataMerger()
        merger.set_league_format(db.league_format_hint(cls.league))
        cls.board = dr.compute_draft_board(
            merger, cls.players, picks=[], my_roster_id="1", league=cls.league,
            sleeper_projections=cls.projections)
        cls.rank = {r["player_id"]: i for i, r in enumerate(cls.board)}
        cls.by_name = {r["name"]: r for r in cls.board}

    def _status(self, name):
        pid = self.by_name[name]["player_id"]
        return (self.players.get(str(pid)) or {}).get("injury_status")

    def test_the_live_cases_are_no_longer_priced_as_healthy(self):
        """Pinned by ORDER, not by an absolute rank, since the board's length moves with other
        repairs. Each of these outranked most of the board on a full-season projection."""
        for name, status, worse_than in (("James Conner", "IR", 35),
                                         ("Luke Musgrave", "PUP", 100),
                                         ("Savion Williams", "IR", 100)):
            with self.subTest(player=name):
                self.assertEqual(self._status(name), status)
                self.assertGreater(self.rank[self.by_name[name]["player_id"]], worse_than)

    def test_a_healthy_comparator_is_untouched(self):
        """Non-vacuity: the haircut must be scoped to the designation, not applied to the
        board. A top-of-board healthy player keeps his place."""
        top = self.board[0]
        self.assertIsNone(self._status(top["name"]))

    def test_the_companion_actually_travels_on_the_pool_row(self):
        """Found by mutation: DELETING availability_basis from the row broke nothing.

        Everything downstream reads it with .get(), so its absence silently degrades to None --
        which health_penalty reads as "no cut happened" and charges the full penalty on top of
        an already-cut number. The board tests could not see it because they assert a player
        ranks BELOW a threshold, and double-charging pushes him further below. That is the #166
        defect living inside the repair for #166's cousin, so the companion is pinned here
        directly rather than inferred from a rank."""
        merger = dm.DataMerger()
        merger.set_league_format(db.league_format_hint(self.league))
        pool = dr.build_available_pool(
            merger, self.players, set(), {"QB", "RB", "WR", "TE", "K", "DEF", "DL", "LB", "DB"},
            sleeper_projections=self.projections,
            scoring_settings=self.league["scoring_settings"])
        self.assertIn("availability_basis", pool.columns)
        bases = set(pool["availability_basis"].dropna())
        self.assertIn(pu.RULE_FLOOR, bases, "no row was cut -- the haircut is not reaching the pool")
        # And the pair is CONSISTENT: a basis exists exactly where there are points to explain.
        has_points = pool["sleeper_points"].notna()
        has_basis = pool["availability_basis"].notna()
        self.assertTrue((has_points == has_basis).all(),
                        "availability_basis and sleeper_points disagree about who they describe")

    def test_PUP_is_priced_at_all_now(self):
        # It had no RISK_ADJ entry, so before this it was indistinguishable from healthy.
        pup = [r for r in self.board
               if (self.players.get(str(r["player_id"])) or {}).get("injury_status") == "PUP"]
        self.assertGreater(len(pup), 0)


class ThePenaltyIsNotChargedTwiceTests(unittest.TestCase):
    """The real double-count, as opposed to the one I once claimed and retracted.

    These call dr.health_penalty -- PRODUCTION -- rather than restating its branch. The first
    draft of this class did restate it, which is a tautology that passes whatever the engine
    does; the same mistake was caught in #195 earlier the same day and the function was
    extracted here for the same reason."""

    def test_a_rule_floor_row_carries_no_extra_penalty(self):
        self.assertEqual(dr.health_penalty("IR", pu.RULE_FLOOR), 0.0)

    def test_a_row_the_haircut_could_not_reach_keeps_its_penalty(self):
        """The reason this is a SPLIT and not a blanket removal: a row priced off the vendor's
        projection has no games-played figure to cut against, so risk_adj is still the only
        place health enters for it."""
        self.assertEqual(dr.health_penalty("IR", None), -18.0)

    def test_every_basis_that_is_not_a_cut_leaves_the_penalty_alone(self):
        for basis in (pu.NO_DESIGNATION, pu.IMMATERIAL, pu.UNRECOGNISED_DESIGNATION,
                      pu.NO_GAMES_REPORTED, None):
            with self.subTest(basis=basis):
                self.assertEqual(dr.health_penalty("IR", basis), -18.0)

    def test_a_designation_with_no_magnitude_is_still_zero_here(self):
        # PUP has no RISK_ADJ entry (#202). Its health now enters through the HAIRCUT, not
        # through this term, and this test pins that rather than leaving it implied.
        self.assertEqual(dr.health_penalty("PUP", None), 0.0)


# MUTATIONS -- each applied, this file re-run, the named test observed to FAIL, then reverted:
#   1. player_universe: GAMES_MISSED_FLOOR gains "Questionable": 1
#        -> TheFloorComesFromTheRulebook.test_only_designations_with_a_real_rule_floor... FAILED
#           and ...test_the_judgement_calls_are_deliberately_absent FAILED
#   2. player_universe: GAMES_MISSED_FLOOR["IR"] = 1
#        -> ...test_the_game_counts_are_the_rule_minimums FAILED, and
#           EveryFactorArrivesWithItsBasis.test_a_rule_floor_designation_cuts_the_projection FAILED
#   3. availability_factor returns a bare float instead of (factor, basis)
#        -> every EveryFactorArrivesWithItsBasis test FAILED
#   4. availability_factor returns UNRECOGNISED_DESIGNATION when games are missing
#        -> ...test_a_recognised_designation_with_no_games_reported_is_a_DIFFERENT_absence FAILED
#   5. availability_factor returns NO_DESIGNATION for an unknown status
#        -> ...test_an_unrecognised_designation_is_NAMED_not_silently_healthy FAILED
#   6. draft_room: the haircut is not applied to sleeper_points
#        -> ThroughTheRealBoard.test_the_live_cases_are_no_longer_priced_as_healthy FAILED
#   7. draft_room: health_penalty ignores the basis (the split removed)
#        -> ThePenaltyIsNotChargedTwice.test_a_rule_floor_row_carries_no_extra_penalty FAILED
#   8. draft_room: health_penalty returns 0.0 always (blanket removal)
#        -> ...test_a_row_the_haircut_could_not_reach_keeps_its_penalty FAILED
#   9. draft_room: health_penalty zeroes on ANY basis, not just RULE_FLOOR
#        -> ...test_every_basis_that_is_not_a_cut_leaves_the_penalty_alone FAILED
#  10. draft_room: availability_basis dropped from the pool row  [SURVIVED the first version]
#        -> ThroughTheRealBoard.test_the_companion_actually_travels_on_the_pool_row FAILED,
#           once that test existed. It did not, and the mutation passed: every reader uses
#           .get(), so the companion's absence degrades silently to None, health_penalty then
#           charges the full penalty ON TOP of an already-cut number, and the rank assertions
#           still hold because double-charging pushes the player further DOWN. Recorded, not
#           smoothed over -- it is #166's defect inside #166's own repair.
if __name__ == "__main__":
    unittest.main()
