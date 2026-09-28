"""MANDATE 2.1(a) / `#180`: a truncated season sum outranked the vendor's complete one.

`season_projection_coverage` is written by `sleeper_client` and was read by no module that prices --
`grep -c season_projection_coverage app.py` returned 0, and its only consumers were a CLI. Meanwhile
`_derive_points_and_source` gives a season-summed total precedence over the vendor EVERYWHERE, which
is right when the total is a season and wrong when it is eleven weeks of one.

`_sum_weeks`' own docstring had already framed the repair: "a caller that wants to reject thin
coverage can; one that drops the second element has made that choice visibly rather than by
accident." Every caller that priced dropped it.

MEASURED HERE, not quoted: the board-level class below sums weeks 1-9 of the committed capture's own
weekly lines and prices a superflex board from the result. 30 of the top 40 rows move 3+ places, the
leader changes (Jahmyr Gibbs 241.66 -> Bijan Robinson 113.93), and quarterbacks in the top ten go
from 3 to 0 -- with `bpa_source`, `replacement_basis` and `absence_kind` unchanged on every row.

REFUSE RATHER THAN RE-RANK. Placing a partial sum in the confidence order would need a number for
what a truncated season is worth, and nobody has derived one (`#56`). Refusing returns the board to
what it was before `#180` -- a defensible number from a complete vendor projection -- and the reason
travels with the refusal, because a board that quietly stops being league-scored is the other half of
this same defect.
"""
from __future__ import annotations

import unittest

import sleeper_client as sc
import ui_source


def _coverage(answered, failed=(), requested=18, error=None):
    return {"season": "2026", "season_type": "regular", "weeks_requested": requested,
            "weeks_answered": list(answered), "weeks_failed": list(failed),
            "players": 800, "error": error}


SUMS = {"1": {"pass_yd": 4000.0}}


class CompletenessIsReadOffTheRecordTests(unittest.TestCase):
    def test_a_whole_season_of_answers_is_complete(self):
        self.assertTrue(sc.season_sum_is_complete(_coverage(range(1, 19))))

    def test_one_failed_week_is_not(self):
        self.assertFalse(sc.season_sum_is_complete(
            _coverage(range(1, 18), failed=[18])))

    def test_an_outright_error_is_not(self):
        self.assertFalse(sc.season_sum_is_complete(
            _coverage([], error="ConnectionError: boom")))

    def test_an_absent_record_is_not_complete(self):
        """#187 applied to a completeness claim: nothing established that the sum is whole."""
        self.assertFalse(sc.season_sum_is_complete(None))
        self.assertFalse(sc.season_sum_is_complete({}))

    def test_a_failed_week_counts_even_when_nothing_says_how_many_were_wanted(self):
        """The arm that makes the failed-week check load-bearing rather than redundant.

        A mutation removing that check survived my first ratchet, because
        `len(answered) == requested` catches the ordinary case by itself. It does NOT catch a record
        with no `weeks_requested` -- an older or hand-assembled one -- and there the failed list is
        the only thing that knows. Found by mutation, covered here."""
        self.assertFalse(sc.season_sum_is_complete(
            {"weeks_answered": [1, 2, 3], "weeks_failed": [4], "weeks_requested": None}))
        self.assertFalse(sc.season_sum_is_complete(
            {"weeks_answered": [1, 2, 3], "weeks_failed": [4]}))
        # And the same record with nothing failed IS complete, or the assertion above would hold
        # for a reason that has nothing to do with the failed list.
        self.assertTrue(sc.season_sum_is_complete(
            {"weeks_answered": [1, 2, 3], "weeks_failed": [], "weeks_requested": None}))

    def test_completeness_is_relative_to_what_was_REQUESTED(self):
        """Deliberately, so this does not need the open question about whether a season is 17
        weeks or 18 settled before it can say whether a fetch finished."""
        self.assertTrue(sc.season_sum_is_complete(_coverage(range(1, 15), requested=14)))
        self.assertFalse(sc.season_sum_is_complete(_coverage(range(1, 15), requested=18)))


class TheRefusalCarriesItsReasonTests(unittest.TestCase):
    def test_a_complete_sum_prices_untouched(self):
        projections, reason = sc.priceable_season_projections(
            {"season_projections": SUMS, "season_projection_coverage": _coverage(range(1, 19))})
        self.assertIs(SUMS, projections, "a whole season must reach the board unchanged")
        self.assertIsNone(reason)

    def test_a_truncated_sum_is_refused_and_the_weeks_are_named(self):
        projections, reason = sc.priceable_season_projections(
            {"season_projections": SUMS,
             "season_projection_coverage": _coverage(range(1, 10), failed=range(10, 19))})
        self.assertIsNone(projections)
        self.assertIn("10", reason)
        self.assertIn("9 weeks, not a season", reason)
        self.assertIn("NOT scored under your league's own rules", reason)
        self.assertIn("Re-sync", reason, "a refusal a person cannot act on is half a message")

    def test_sums_with_no_coverage_record_at_all_are_refused(self):
        projections, reason = sc.priceable_season_projections({"season_projections": SUMS})
        self.assertIsNone(projections)
        self.assertIn("nothing establishes that they are whole", reason)

    def test_no_sums_is_silence_not_a_refusal(self):
        """NON-VACUITY in the other direction. A league that was never synced for season sums has
        nothing refused, and a warning there would be noise about a state that is normal."""
        self.assertEqual((None, None), sc.priceable_season_projections({}))
        self.assertEqual((None, None), sc.priceable_season_projections(None))


class EveryPricingCallSiteAsksTests(unittest.TestCase):
    """`app.py` passed the raw sums at four call sites -- the live board, two Mock Draft paths and
    the opponent simulation. One home for the question, asked once for the page."""

    def setUp(self):
        self.app = ui_source.text()

    def test_no_call_site_reads_the_raw_sums_any_more(self):
        self.assertNotIn('sleeper_projections=(snapshot.get("season_projections") or None)',
                         self.app, "a call site still prices from an unchecked sum")

    def test_all_four_price_from_the_guarded_value(self):
        self.assertEqual(4, self.app.count("sleeper_projections=_priceable_season_sums"),
                         "a pricing call site was added or removed -- read it")

    def test_the_question_is_asked_once_at_page_scope(self):
        self.assertEqual(1, self.app.count("sleeper_client.priceable_season_projections(snapshot)"))

    def test_the_refusal_is_shown_and_not_swallowed(self):
        self.assertIn("if _season_sum_refusal:", self.app)
        self.assertIn("st.warning(_season_sum_refusal)", self.app)


class ThisActuallyChangesTheBoardTests(unittest.TestCase):
    """NON-VACUITY at board level, which is what makes the refusal worth having: if a truncated sum
    priced roughly the same board, refusing it would be ceremony. Slow -- three real board builds on
    the committed capture -- and the numbers in this file's docstring come from here."""

    @classmethod
    def setUpClass(cls):
        import data_merger as dm, draft_battery as dbat, draft_room as dr, run_draft_battery as rdb
        cls.dr = dr
        cls.merger = dm.DataMerger()
        cls.players_db, _ = rdb.build_players_db_from_capture()
        cls.season = rdb.season_projections_from_capture()
        cls.weekly = rdb.weekly_projections_from_capture()
        cls.league = dr.build_mock_league(
            teams=12, superflex=True, scoring="ppr", te_premium=False, dynasty=True,
            base_scoring=rdb.scoring_settings_from_capture())
        cls.merger.set_league_format(dbat.league_format_hint(cls.league))

    def _truncated(self, weeks):
        out: dict[str, dict] = {}
        for week in weeks:
            for pid, stats in (self.weekly.get(str(week)) or {}).items():
                bucket = out.setdefault(pid, {})
                for category, value in (stats or {}).items():
                    try:
                        bucket[category] = bucket.get(category, 0.0) + float(value)
                    except (TypeError, ValueError):
                        continue
        return out

    def _board(self, projections):
        return self.dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id=None, league=self.league,
            mode="balanced", sleeper_projections=projections,
            sleeper_basis=self.dr.SLEEPER_BASIS_SEASON_SUM)

    def test_a_truncated_sum_prices_a_materially_different_board(self):
        self.assertTrue(self.weekly, "the capture carries no weekly lines, so nothing is measured")
        full = self._board(self.season)
        partial = self._board(self._truncated(range(1, 10)))
        full_rank = {r["player_id"]: i + 1 for i, r in enumerate(full)}
        partial_rank = {r["player_id"]: i + 1 for i, r in enumerate(partial)}
        moved = sum(1 for r in full[:40]
                    if abs(partial_rank.get(r["player_id"], 10 ** 6) - full_rank[r["player_id"]]) >= 3)
        self.assertGreaterEqual(moved, 20, f"only {moved} of the top 40 moved 3+ places")
        self.assertNotEqual(full[0]["player_id"], partial[0]["player_id"],
                            "the leader is unchanged, so this truncation demonstrates nothing")

    def test_the_truncation_empties_the_top_of_a_superflex_board_of_quarterbacks(self):
        """The shape that makes it dangerous rather than merely wrong: the rows lost are the ones
        whose projections are largest, and nothing on any row says so."""
        full = self._board(self.season)
        partial = self._board(self._truncated(range(1, 10)))
        self.assertGreater(len([r for r in full[:10] if r["position"] == "QB"]), 0)
        self.assertEqual(0, len([r for r in partial[:10] if r["position"] == "QB"]))

    def test_refusing_gives_back_exactly_the_vendor_board(self):
        """What the refusal actually costs and does not cost: the board is the pre-#180 one, not a
        third thing."""
        refused, reason = __import__("sleeper_client").priceable_season_projections(
            {"season_projections": self._truncated(range(1, 10)),
             "season_projection_coverage": _coverage(range(1, 10), failed=range(10, 19))})
        self.assertIsNone(refused)
        self.assertIsNotNone(reason)
        self.assertEqual([r["player_id"] for r in self._board(None)[:25]],
                         [r["player_id"] for r in self._board(refused)[:25]])


if __name__ == "__main__":
    unittest.main()
