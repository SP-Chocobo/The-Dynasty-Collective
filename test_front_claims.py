"""The claim band's judgment, tested where it now lives instead of through a page's HTML.

BEFORE THIS, every one of these rulings could only be exercised by building a whole page and
reading strings out of it. `test_front_renders_its_basis` still does that, and should -- it is
the RENDERING contract. These are the RANKING contract, and the difference matters because
production will render the same judgment completely differently and must inherit the rulings
without inheriting the markup.
"""
import sys
import pathlib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import front_claims as fc
import lineup_optimizer as lo


def _fx(**over):
    base = {"structural_holes": [], "thin_positions": [], "bye_profile": {}, "current_week": None}
    base.update(over)
    return base


def _bye(**over):
    b = {"weeks": {"6": 95.0, "7": 8.0, "9": 4.0}, "worst_week": 6, "worst_week_loss": 95.0,
         "concentration": 0.401, "basis": lo.BYE_MEASURED, "worst_week_detail": {"starters_out": 1}}
    b.update(over)
    return b


class TheLadderRanksAcrossIncomparableUnitsTests(unittest.TestCase):
    def test_a_hole_outranks_a_bye_which_outranks_a_thin_position(self):
        """The whole reason the band is a fixed ladder and not a score."""
        out = fc.compose(_fx(structural_holes=["K"], bye_profile=_bye(),
                             thin_positions=[{"position": "TE", "count": 2}]))
        self.assertEqual(["hole", "bye", "thin"], [c["kind"] for c in out["shown"]])

    def test_the_band_caps_at_three_and_names_what_it_hid(self):
        """A capped list is a ranked list; an uncapped one is a feed."""
        out = fc.compose(_fx(structural_holes=["K"], bye_profile=_bye(), thin_positions=[
            {"position": "TE", "count": 2}, {"position": "QB", "count": 1}]))
        self.assertEqual(3, len(out["shown"]))
        self.assertEqual(1, len(out["hidden"]))
        # Hidden, NOT dropped: the surface still says "Also: ...".
        self.assertEqual("thin", out["hidden"][0]["kind"])

    def test_compose_never_emits_a_kind_the_ladder_cannot_rank(self):
        """`rank[c["kind"]]` is a KeyError waiting to happen if a rung is ever added to the
        producers without being added to the ladder. This pins the two lists together."""
        rungs = {k for k, _ in fc.LADDER}
        out = fc.compose(_fx(structural_holes=["K"], bye_profile=_bye(),
                             thin_positions=[{"position": "TE", "count": 2}]))
        for c in out["shown"] + out["hidden"]:
            self.assertIn(c["kind"], rungs)

    def test_the_clock_rung_is_declared_and_deliberately_unreachable(self):
        """`clock` is the only rung carrying a real deadline and NOTHING produces it -- no
        fixture key supplies it. That is a known absence, not a bug, and pinning it here means
        wiring the draft clock later has to come past this test rather than silently satisfy it."""
        self.assertIn("clock", [k for k, _ in fc.LADDER])
        self.assertNotIn("clock", fc.RUNGS_PRODUCED_HERE)
        self.assertEqual(("hole", "bye", "thin"), fc.RUNGS_PRODUCED_HERE)


class FuturityIsTheByeRungsWholeReasonTests(unittest.TestCase):
    def test_a_known_week_re_picks_the_worst_week_STILL_AHEAD(self):
        """Week 6 is the season's worst; from week 7 onward the worst ahead is week 7."""
        out = fc.compose(_fx(bye_profile=_bye(), current_week=7))
        bye = next(c for c in out["shown"] if c["kind"] == "bye")
        self.assertEqual(7, bye["worst_week"])
        self.assertEqual(8.0, bye["worst_week_loss"])
        self.assertTrue(bye["ahead_only"])

    def test_a_week_already_played_is_dropped_from_the_profile_entirely(self):
        out = fc.compose(_fx(bye_profile=_bye(), current_week=7))
        self.assertEqual({"7", "9"}, set(out["bye_profile"]["weeks"]))

    def test_with_every_bye_behind_us_the_claim_does_not_fire_at_all(self):
        """A season-shape fact is not a deadline, and must not be drawn as one."""
        out = fc.compose(_fx(bye_profile=_bye(), current_week=20))
        self.assertEqual([], [c for c in out["shown"] if c["kind"] == "bye"])
        self.assertIsNone(out["bye_profile"]["worst_week"])

    def test_without_a_known_week_nothing_claims_futurity(self):
        out = fc.compose(_fx(bye_profile=_bye()))
        bye = next(c for c in out["shown"] if c["kind"] == "bye")
        self.assertFalse(bye["ahead_only"])
        self.assertEqual(6, bye["worst_week"])

    def test_the_resolved_profile_comes_back_even_when_the_claim_does_not_fire(self):
        """The page's week strip draws the SAME reduced profile. Re-deriving it in the renderer
        is how one quantity acquires two answers (`#126`)."""
        out = fc.compose(_fx(bye_profile=_bye(worst_week=None, worst_week_loss=None)))
        self.assertEqual([], [c for c in out["shown"] if c["kind"] == "bye"])
        self.assertIn("weeks", out["bye_profile"])

    def test_a_non_numeric_week_key_does_not_take_the_band_down(self):
        out = fc.compose(_fx(bye_profile=_bye(weeks={"6": 95.0, "bye": 1.0}), current_week=6))
        self.assertEqual(6, out["bye_profile"]["worst_week"])


class AbsenceAndFloorsSurviveTheLiftTests(unittest.TestCase):
    def test_a_null_concentration_stays_null_and_never_becomes_zero(self):
        """`bye_concentration` returns None, never 0.0: a roster with nothing to lose has no
        shape, and 0.0 would rank it as maximally staggered."""
        out = fc.compose(_fx(bye_profile=_bye(concentration=None)))
        self.assertIsNone(next(c for c in out["shown"] if c["kind"] == "bye")["concentration"])

    def test_a_partial_bye_basis_marks_the_claim_as_a_floor(self):
        out = fc.compose(_fx(bye_profile=_bye(basis="partial", unknown_byes=2)))
        bye = next(c for c in out["shown"] if c["kind"] == "bye")
        self.assertTrue(bye["partial"])
        self.assertEqual(2, bye["unknown_byes"])

    def test_the_depth_LABEL_is_carried_because_dropping_it_invited_a_fabrication(self):
        """`#336b`. `depth_label` returns a RATIO BAND -- Strong / Average / Weak / None -- and
        nothing in this tree ranks teams within a position. `compose` used to drop the label, so
        the renderer had no true thing to say about depth and invented "bottom of this league at
        the position": a rank that does not exist, and false on the shipped fixture, where DEF is
        a five-way tie at count 1 AND the joint-highest PRICED DEF room in the league.

        Carrying the measured quantity is the repair. A composition that discards it invites the
        surface to fabricate a replacement, and no test here could have caught that because every
        test checked numbers and the fabrication was prose.
        """
        out = fc.compose(_fx(thin_positions=[
            {"position": "TE", "count": 2, "label": "Weak"},
            {"position": "DEF", "count": 1, "label": "None \u2014 no rostered players here"}]))
        got = {c["position"]: c["label"] for c in out["shown"] + out["hidden"]}
        self.assertEqual({"TE": "Weak", "DEF": "None \u2014 no rostered players here"}, got)

    def test_a_thin_row_with_no_label_carries_None_rather_than_a_guess(self):
        """The fixture is hand-maintainable. A missing label must arrive as None so the surface
        can fall silent, not as a default the reader would read as measured."""
        out = fc.compose(_fx(thin_positions=[{"position": "TE", "count": 2}]))
        self.assertIsNone(out["shown"][0]["label"])

    def test_priced_floor_is_set_only_when_some_of_the_room_could_not_be_priced(self):
        out = fc.compose(_fx(thin_positions=[
            {"position": "TE", "count": 2, "valued_count": 1},
            {"position": "WR", "count": 2, "valued_count": 2},
            {"position": "RB", "count": 2}]))
        got = {c["position"]: c["priced_floor"] for c in out["shown"] + out["hidden"]}
        self.assertEqual({"TE": True, "WR": False, "RB": False}, got)


class TheRungsOwnOrderingAndToleranceTests(unittest.TestCase):
    def test_thin_positions_rank_by_how_empty_the_room_is_not_by_the_alphabet(self):
        """A one-man room is an injury away from the rung above; a two-man room is not.

        THE FIXTURE HAS TO DISTINGUISH THE TWO ORDERS, and the first version of this test did
        not. It used TE(2) and QB(1), where ranking by count and ranking alphabetically BOTH
        give [QB, TE] -- so it asserted the right answer for the wrong reason and passed against
        either implementation. It was caught by a mutation panel: replacing the count in the sort
        key with a constant broke no test, which is how a test that tests nothing announces
        itself. Here QB holds two and TE holds one, so count order is [TE, QB] while the alphabet
        would say [QB, TE], and only one of those can pass.
        """
        out = fc.compose(_fx(thin_positions=[
            {"position": "QB", "count": 2}, {"position": "TE", "count": 1}]))
        self.assertEqual(["TE", "QB"], [c["position"] for c in out["shown"]])

    def test_mixed_types_in_the_sort_key_do_not_raise(self):
        """A crash introduced BY the fix for the alphabetical-ordering defect."""
        out = fc.compose(_fx(thin_positions=[
            {"position": "TE", "count": "2"}, {"position": "QB", "count": 1},
            {"position": "WR", "count": None}]))
        self.assertEqual(3, len(out["shown"]) + len(out["hidden"]))

    def test_all_holes_collapse_into_exactly_one_claim(self):
        """Two cards for one problem with one remedy and one route is the failure the standing
        constraint names -- and in a real league it pushed the bye claim off the band."""
        out = fc.compose(_fx(structural_holes=["K", "DEF", "TE"]))
        holes = [c for c in out["shown"] if c["kind"] == "hole"]
        self.assertEqual(1, len(holes))
        self.assertEqual(["K", "DEF", "TE"], holes[0]["positions"])

    def test_every_top_level_key_can_be_missing(self):
        """The fixture is hand-maintainable; a missing key must not be a traceback."""
        for drop in ("structural_holes", "thin_positions", "bye_profile", "current_week"):
            with self.subTest(missing=drop):
                fx = _fx(structural_holes=["K"], bye_profile=_bye(),
                         thin_positions=[{"position": "TE", "count": 2}])
                fx.pop(drop)
                fc.compose(fx)   # must not raise

    def test_an_entirely_empty_roster_produces_an_empty_band(self):
        """"Nothing needs you" is the feature, not a gap to fill."""
        out = fc.compose(_fx())
        self.assertEqual([], out["shown"])
        self.assertEqual([], out["hidden"])


if __name__ == "__main__":
    unittest.main()
