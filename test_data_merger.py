import unittest

import pandas as pd

import data_merger as dm


class NormalizeNameTests(unittest.TestCase):
    def test_strips_suffixes_and_punctuation(self):
        self.assertEqual(dm.normalize_name("A.J. Brown Jr."), "aj brown")

    def test_ligature_decomposes_instead_of_vanishing(self):
        # pypdf's Draft Sharks extraction commonly renders "fi" as a single ligature glyph --
        # confirmed this session with a real "Mayﬁeld" row. NFKD normalization must turn that
        # into plain "fi", not silently drop it (which would produce the wrong name "mayeld").
        self.assertIn("fi", dm.normalize_name("Mayﬁeld"))


class PositionGroupTests(unittest.TestCase):
    """_position_group is the fix for the real "Josh Allen the Bills QB vs. Josh Allen a DL"
    collision this baseline effort surfaced -- these tests exist to make sure that class of
    bug can't silently come back."""

    def test_broad_offense_positions(self):
        for pos in ("QB", "RB", "WR", "TE", "K", "DEF"):
            self.assertEqual(dm._position_group(pos), "offense", pos)

    def test_broad_and_granular_idp_positions_all_classify_as_idp(self):
        # LB/DL/DB are Draft Sharks' three broad buckets; DE/DT/S/CB are FantasyPros' more
        # granular split of the same real positions -- both schemes must land in "idp" or a
        # same-named offense/IDP collision slips back through undetected.
        for pos in ("LB", "DL", "DB", "DE", "DT", "S", "CB", "EDGE", "SS", "FS"):
            self.assertEqual(dm._position_group(pos), "idp", pos)

    def test_missing_or_non_string_position_is_neutral(self):
        self.assertEqual(dm._position_group(None), "")
        self.assertEqual(dm._position_group(float("nan")), "")
        self.assertEqual(dm._position_group(""), "")


class DedupByNameAndPositionTests(unittest.TestCase):
    def _empty(self):
        return pd.DataFrame(columns=["name", "norm_name"])

    def test_same_name_different_position_group_both_survive(self):
        # The real collision: a QB and a DL both named "Josh Allen" must not collapse into one
        # row just because they share a normalized name.
        qb = pd.DataFrame([{"name": "Josh Allen", "norm_name": "josh allen", "position": "QB", "trade_value": 45}])
        dl = pd.DataFrame([{"name": "Josh Allen", "norm_name": "josh allen", "position": "DL", "trade_value": 12}])
        combined = dm._dedup_by_name_and_position([qb, dl], self._empty())
        self.assertEqual(len(combined), 2)
        self.assertEqual(set(combined["position"]), {"QB", "DL"})

    def test_same_player_same_position_collapses_to_newest(self):
        old = pd.DataFrame([{"name": "Ja'Marr Chase", "norm_name": "jamarr chase", "position": "WR", "trade_value": 90}])
        new = pd.DataFrame([{"name": "Ja'Marr Chase", "norm_name": "jamarr chase", "position": "WR", "trade_value": 100}])
        combined = dm._dedup_by_name_and_position([old, new], self._empty())
        self.assertEqual(len(combined), 1)
        self.assertEqual(combined.iloc[0]["trade_value"], 100)

    def test_no_position_column_falls_back_to_name_only(self):
        # Trade Value Chart pick rows (asset_type=pick) carry no "position" column at all --
        # dedup still has to work without one, on name alone.
        old = pd.DataFrame([{"name": "2027 Early 1st", "norm_name": "2027 early 1st", "value": 50}])
        new = pd.DataFrame([{"name": "2027 Early 1st", "norm_name": "2027 early 1st", "value": 60}])
        combined = dm._dedup_by_name_and_position([old, new], self._empty())
        self.assertEqual(len(combined), 1)
        self.assertEqual(combined.iloc[0]["value"], 60)


class KeepTradeCutRowRegexTests(unittest.TestCase):
    """The regex half of parse_keeptradecut_pdf -- the digit-splitting itself is exercised
    end-to-end in CompositeScoreOnRealBaselineTests below via the real committed baseline."""

    def test_matches_a_real_player_row_shape(self):
        m = dm._KTC_ROW_RE.match("Jahmyr Gibbs RB1 T1 99981 2")
        self.assertIsNotNone(m)
        name, pos, tier, blob, rookie, trend = m.groups()
        self.assertEqual(name, "Jahmyr Gibbs")
        self.assertEqual(pos, "RB1")
        self.assertEqual(tier, "T1")
        self.assertEqual(blob, "99981")
        self.assertEqual(trend, "2")

    def test_matches_a_pick_row_shape(self):
        m = dm._KTC_ROW_RE.match("2027 Early 1st PICK T6 693822 2")
        self.assertIsNotNone(m)
        name, pos, tier, blob, rookie, trend = m.groups()
        self.assertEqual(name, "2027 Early 1st")
        self.assertEqual(pos, "PICK")

    def test_matches_rookie_flag(self):
        m = dm._KTC_ROW_RE.match("Jeremiyah Love RB4 T4 745714 R 1")
        self.assertIsNotNone(m)
        self.assertTrue(m.group(5))  # the " R" group is present


class EspnIdpRowRegexTests(unittest.TestCase):
    def test_matches_glued_team_and_status_flag(self):
        m = dm._ESPN_IDP_ROW_RE.match("2.\xa0Myles Garrett, LARQ 2 3 2 2.3")
        self.assertIsNotNone(m)
        rank, name, team, status, a1, a2, a3, avg = m.groups()
        self.assertEqual(team, "LAR")
        self.assertEqual(status, "Q")

    def test_matches_space_separated_status_flag(self):
        # Confirmed on a real file: 2 of 120 real rows print "PHI O" with a space instead of
        # the usual glued "PHIO" -- the \s? in the regex exists specifically for this.
        m = dm._ESPN_IDP_ROW_RE.match("15.\xa0Jonathan Greenard, PHI O 15 15 16 15.3")
        self.assertIsNotNone(m)
        rank, name, team, status, a1, a2, a3, avg = m.groups()
        self.assertEqual(team, "PHI")
        self.assertEqual(status, "O")

    def test_matches_no_status_flag(self):
        m = dm._ESPN_IDP_ROW_RE.match("1.\xa0Maxx Crosby, LV 1 1 1 1.0")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(4), "")


class FantasyProsRowRegexTests(unittest.TestCase):
    def test_dynasty_row(self):
        m = dm._FP_DYNASTY_ROW_RE.match("1 Ja'Marr Chase (CIN) WR1 26 1 2 1.0 0.2")
        self.assertIsNotNone(m)

    def test_dynasty_row_dst_with_dash_age(self):
        m = dm._FP_DYNASTY_ROW_RE.match("258 Denver Broncos (DEN) DST1 - 225 248 232.4 6.0")
        self.assertIsNotNone(m)

    def test_seasonal_row(self):
        m = dm._FP_SEASONAL_ROW_RE.match("1 Jahmyr Gibbs (DET) RB1 6")
        self.assertIsNotNone(m)

    def test_idp_row_with_trailing_sos_dash(self):
        m = dm._FP_IDP_ROW_RE.match("1 Jordyn Brooks (MIA) LB1 6 -")
        self.assertIsNotNone(m)


class RecencyWeightTests(unittest.TestCase):
    def test_today_is_full_weight(self):
        from datetime import date
        self.assertAlmostEqual(dm._recency_weight(date.today().isoformat()), 1.0, places=6)

    def test_one_halflife_ago_is_half_weight(self):
        from datetime import date, timedelta
        stale = (date.today() - timedelta(days=dm.COMPOSITE_RECENCY_HALFLIFE_DAYS)).isoformat()
        self.assertAlmostEqual(dm._recency_weight(stale), 0.5, places=6)

    def test_missing_date_gets_middling_weight(self):
        self.assertEqual(dm._recency_weight(None), 0.5)
        self.assertEqual(dm._recency_weight("not-a-date"), 0.5)


class RecencyGradeTests(unittest.TestCase):
    def test_grade_boundaries(self):
        self.assertEqual(dm._recency_grade(0), "Fresh")
        self.assertEqual(dm._recency_grade(7), "Fresh")
        self.assertEqual(dm._recency_grade(8), "Recent")
        self.assertEqual(dm._recency_grade(30), "Recent")
        self.assertEqual(dm._recency_grade(31), "Aging")
        self.assertEqual(dm._recency_grade(90), "Aging")
        self.assertEqual(dm._recency_grade(91), "Stale")

    def test_missing_age_is_unknown(self):
        self.assertEqual(dm._recency_grade(None), "Unknown")


class CompositeScoreOnRealBaselineTests(unittest.TestCase):
    """Exercises the real committed baseline data (data/baseline/**) end to end -- this is
    the actual fixture data the app ships with, so these tests double as a regression check
    that a future edit to any baseline CSV or parser doesn't silently break matching."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    def test_baseline_loads_nonempty(self):
        self.assertTrue(self.merger.is_loaded)
        self.assertTrue(self.merger.is_external_values_loaded)

    def test_known_qb_and_dl_sharing_a_name_resolve_independently(self):
        # The exact real-world collision this session's _position_group fix exists for.
        qb = self.merger.merge_player("Josh Allen", position="QB")
        dl = self.merger.merge_player("Josh Allen", position="DL")
        self.assertTrue(qb.get("matched"))
        self.assertTrue(dl.get("matched"))
        self.assertEqual(qb.get("position"), "QB")
        self.assertEqual(dl.get("position"), "DL")
        self.assertNotEqual(qb.get("trade_value"), dl.get("trade_value"))

    def test_composite_score_is_none_for_a_nonexistent_player(self):
        self.assertIsNone(self.merger.composite_player_score("Definitely Not A Real Nfl Player Xyz"))

    def test_composite_score_never_exceeds_100_or_drops_below_0(self):
        for name, pos in (("Ja'Marr Chase", "WR"), ("Josh Allen", "QB"), ("Bijan Robinson", "RB")):
            result = self.merger.composite_player_score(name, position=pos)
            self.assertIsNotNone(result, name)
            self.assertGreaterEqual(result["score"], 0)
            self.assertLessEqual(result["score"], 100)

    def test_composite_components_only_drawn_from_dynasty_sources(self):
        # FantasyPros' best_ball_rankings.csv and idp_redraft_rankings.csv, and ESPN's
        # idp_redraft_rankings.csv, are redraft-scope and must never appear as a composite
        # component -- only dynasty-scope sources belong in _EXTERNAL_PERCENTILE_RULES.
        result = self.merger.composite_player_score("Maxx Crosby", position="DL")
        sources = {c["source"] for c in result["components"]} if result else set()
        self.assertTrue(sources.issubset({"draftsharks", "dynastyprocess", "fantasypros", "keeptradecut", "bot_research"}))


if __name__ == "__main__":
    unittest.main()
