"""`#339` -- the thin-positions shape, across the interface neither side's tests crossed.

THE DEFECT. `lineup_readiness.compute_readiness` returned `thin_positions` entries of
`{"position", "label"}`. `front_claims.compose` reads `count` and `valued_count` as well, so it
substituted 0 and None, and `build_front`'s claim prose printed "<b>0</b> rostered." about a room
holding two tight ends -- a false figure AND an absence rendered as a zero, which `#187` exists
to forbid. Quieter and worse: `thin_sort_key` is `(count, position)`, so with every count 0 the
band's within-rung order collapsed to the ALPHABET, the exact defect that function was written to
prevent and whose docstring records what it cost (a one-QB room hidden below the cap behind a
two-man TE room).

WHY NOTHING CAUGHT IT, which is the reason this file is at the top level rather than beside
either module. Three test modules exercise `compute_readiness`; NONE imports `front_claims`. Every
claim-band test feeds the FIXTURE shape, which carries `count`. So both sides passed their own
tests, agreed with themselves, and disagreed with each other. These tests cross the interface on
purpose -- production producer, production composer, production renderer, one assertion chain.

Same family as the interface hazards `engine-measurement` records: `optimize_lineup` taking `id`
and returning `player_id`, a pick record missing `round` selecting a different scoring mode. A
key-absence mismatch across an interface produces no crash and no warning. It produces a
plausible number about something else.
"""
from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ui_explore" / "round3"))

import build_front
import depth_ratings
import front_claims
import lineup_readiness


def _cell(count, value, valued_count=None):
    """The shape `depth_chart.positional_depth` actually builds."""
    return {"count": count, "value": value,
            "valued_count": count if valued_count is None else valued_count}


# Me weak at both, by VALUE, against richer peers. DEF count 3 / WR count 1 is chosen so that
# count order and alphabetical order DISAGREE -- see the ordering test for why that matters.
SPLIT_DEPTH = {
    "Me":     {"DEF": _cell(3, 10.0), "WR": _cell(1, 5.0, valued_count=0)},
    "Rival1": {"DEF": _cell(3, 120.0), "WR": _cell(6, 300.0)},
    "Rival2": {"DEF": _cell(3, 130.0), "WR": _cell(6, 320.0)},
}

TWO_TE_DEPTH = {
    "Me":     {"TE": _cell(2, 30.0, valued_count=1)},
    "Rival1": {"TE": _cell(5, 150.0)},
    "Rival2": {"TE": _cell(5, 160.0)},
}


class TheProducerCarriesWhatTheCellMeasuredTests(unittest.TestCase):
    def test_count_and_valued_count_travel_with_the_label(self):
        out = lineup_readiness.compute_readiness([], TWO_TE_DEPTH, "Me", 10)
        self.assertEqual(
            [{"position": "TE", "label": depth_ratings.WEAK, "count": 2, "valued_count": 1}],
            out["thin_positions"])

    def test_valued_count_is_not_count_when_the_room_is_partly_unpriced(self):
        """`#190`. Every rostered player raises count; only priced ones raise valued_count."""
        entry = lineup_readiness.compute_readiness([], TWO_TE_DEPTH, "Me", 10)["thin_positions"][0]
        self.assertEqual(2, entry["count"])
        self.assertEqual(1, entry["valued_count"])
        self.assertNotEqual(entry["count"], entry["valued_count"])

    def test_a_fully_priced_room_reports_valued_count_equal_to_count(self):
        entry = lineup_readiness.compute_readiness(
            [], SPLIT_DEPTH, "Me", 10)["thin_positions"]
        by_pos = {e["position"]: e for e in entry}
        self.assertEqual(3, by_pos["DEF"]["count"])
        self.assertEqual(3, by_pos["DEF"]["valued_count"])


class TheComposerReceivesATrueCountTests(unittest.TestCase):
    """The interface itself. Production producer -> production composer."""

    def test_a_two_man_room_does_not_reach_the_band_as_zero(self):
        readiness = lineup_readiness.compute_readiness([], TWO_TE_DEPTH, "Me", 10)
        claim = front_claims.compose({"thin_positions": readiness["thin_positions"]})["shown"][0]
        self.assertEqual("TE", claim["position"])
        self.assertEqual(2, claim["count"], "the band was handed 0 for a room holding two")

    def test_a_partly_unpriced_room_reaches_the_band_as_a_FLOOR(self):
        """`priced_floor` is derived from valued_count < count, so dropping valued_count made
        every comparison look like a total. The marker is the `>=` in the absence grammar."""
        readiness = lineup_readiness.compute_readiness([], TWO_TE_DEPTH, "Me", 10)
        claim = front_claims.compose({"thin_positions": readiness["thin_positions"]})["shown"][0]
        self.assertTrue(claim["priced_floor"])

    def test_the_label_survives_the_whole_trip(self):
        """`#336b`: the composer dropping the label is what let the renderer invent a rank."""
        readiness = lineup_readiness.compute_readiness([], TWO_TE_DEPTH, "Me", 10)
        claim = front_claims.compose({"thin_positions": readiness["thin_positions"]})["shown"][0]
        self.assertEqual(depth_ratings.WEAK, claim["label"])


class TheOrderingDoesNotFallBackToTheAlphabetTests(unittest.TestCase):
    """THE HOLLOW-TEST TRAP, AVOIDED DELIBERATELY.

    `#333`'s own record names this twice: a `TE(2)/QB(1)` fixture cannot distinguish count order
    from alphabetical order, because Q precedes T either way. So this fixture uses DEF(3) and
    WR(1), where the two orders DISAGREE -- alphabetically DEF then WR, by emptiness WR then DEF.
    A test that cannot tell the two states apart is worse than no test, because it is believed.
    """

    def test_the_fixture_can_actually_tell_the_two_orders_apart(self):
        """The vacuity guard for the guard. If a future edit makes count order and the alphabet
        agree on this fixture, this fails before the ordering test goes green for free."""
        readiness = lineup_readiness.compute_readiness([], SPLIT_DEPTH, "Me", 10)
        positions = [e["position"] for e in readiness["thin_positions"]]
        self.assertEqual(["DEF", "WR"], positions, "producer emits sorted(), i.e. the alphabet")
        counts = {e["position"]: e["count"] for e in readiness["thin_positions"]}
        self.assertNotEqual(sorted(counts, key=lambda p: counts[p]), sorted(counts),
                            "fixture is hollow: count order and the alphabet agree on it")

    def test_the_emptier_room_is_ranked_first_not_the_alphabetically_earlier_one(self):
        readiness = lineup_readiness.compute_readiness([], SPLIT_DEPTH, "Me", 10)
        shown = front_claims.compose({"thin_positions": readiness["thin_positions"]})["shown"]
        self.assertEqual(["WR", "DEF"], [c["position"] for c in shown],
                         "the band ordered by the alphabet, not by how close to empty")


class TheRenderedSentenceStatesTheRealCountTests(unittest.TestCase):
    """The consequence a reader would actually have seen."""

    def test_the_page_does_not_say_zero_rostered_about_a_two_man_room(self):
        readiness = lineup_readiness.compute_readiness([], TWO_TE_DEPTH, "Me", 10)
        claim = front_claims.compose({"thin_positions": readiness["thin_positions"]})["shown"][0]
        headline, body = build_front.claim_prose(claim)
        self.assertIn("TE", headline)
        self.assertIn("<b>2</b> rostered", body)
        self.assertNotIn("<b>0</b> rostered", body)

    def test_the_sentence_says_the_label_and_never_a_rank(self):
        """`#336b` guarded from the production path rather than the fixture path."""
        readiness = lineup_readiness.compute_readiness([], TWO_TE_DEPTH, "Me", 10)
        claim = front_claims.compose({"thin_positions": readiness["thin_positions"]})["shown"][0]
        _, body = build_front.claim_prose(claim)
        self.assertIn(depth_ratings.WEAK, body)
        for forbidden in ("bottom of", "worst at", "last in", "ranks "):
            self.assertNotIn(forbidden, body.lower())

    def test_a_partly_unpriced_room_says_so_in_the_sentence(self):
        readiness = lineup_readiness.compute_readiness([], TWO_TE_DEPTH, "Me", 10)
        claim = front_claims.compose({"thin_positions": readiness["thin_positions"]})["shown"][0]
        _, body = build_front.claim_prose(claim)
        self.assertIn("floor", body.lower())


class TheDeadDefaultIsGoneTests(unittest.TestCase):
    """The loop iterates the keys of the dict it reads, so the old `.get(position, {...})`
    default was unreachable -- and it declared a cell WITHOUT `valued_count`, disagreeing with
    the shape `positional_depth` builds. A dead default that lies about a shape is the same
    defect in miniature."""

    def test_every_position_the_loop_visits_has_a_real_cell(self):
        import test_source_scan
        code = test_source_scan.code_text(pathlib.Path(lineup_readiness.__file__))
        self.assertNotIn('.get(position, {', code,
                         "a default that can never fire can still disagree with the real cell")

    def test_a_team_absent_from_depth_is_still_not_a_crash(self):
        """Removing the default must not cost the tolerance that mattered."""
        self.assertEqual([], lineup_readiness.compute_readiness(
            [], TWO_TE_DEPTH, "Nobody", 10)["thin_positions"])
        self.assertEqual([], lineup_readiness.compute_readiness([], {}, "Me", 10)["thin_positions"])
        self.assertEqual([], lineup_readiness.compute_readiness(
            [], TWO_TE_DEPTH, None, 10)["thin_positions"])


if __name__ == "__main__":
    unittest.main()
