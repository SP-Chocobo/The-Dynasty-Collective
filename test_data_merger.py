import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

import bot_research
import data_merger as dm


class NormalizeNameTests(unittest.TestCase):
    def test_strips_suffixes_and_punctuation(self):
        self.assertEqual(dm.normalize_name("A.J. Brown Jr."), "aj brown")

    def test_ligature_decomposes_instead_of_vanishing(self):
        # pypdf's Draft Sharks extraction commonly renders "fi" as a single ligature glyph --
        # confirmed this session with a real "Mayﬁeld" row. NFKD normalization must turn that
        # into plain "fi", not silently drop it (which would produce the wrong name "mayeld").
        self.assertIn("fi", dm.normalize_name("Mayﬁeld"))


class NameKeyTests(unittest.TestCase):
    """The exact bug this class exists to prevent regressing: a (first-initial, LAST TOKEN)
    key can't distinguish two different people whose last token happens to collide -- "A.J.
    Brown" ("aj brown") and "Amon-Ra St. Brown" ("amonra st brown") both end in "brown".
    Confirmed live: the Trade Value Chart's exact "aj brown" row (tv=37) was discarded in
    favor of "amonra st brown" (tv=83) for BOTH players. name_key() fixes this by keying on
    everything after the first token, not just the last one."""

    def test_multi_word_last_names_no_longer_collide_with_a_shared_final_token(self):
        self.assertNotEqual(
            dm.name_key(dm.normalize_name("A.J. Brown")),
            dm.name_key(dm.normalize_name("Amon-Ra St. Brown")),
        )

    def test_same_person_different_full_name_forms_still_match(self):
        self.assertEqual(
            dm.name_key(dm.normalize_name("Amon-Ra St. Brown")),
            dm.name_key(dm.normalize_name("A St Brown")),  # Draft Sharks' own abbreviated form
        )

    def test_genuine_same_key_collision_still_recognized(self):
        # Two real people who really do share a (first-initial, last-name) key -- this isn't
        # a false collision, so name_key must still treat them as one key (position/team
        # disambiguation downstream is what actually tells them apart).
        self.assertEqual(dm.name_key("josh allen"), dm.name_key("jaylen allen"))

    def test_single_token_name_does_not_crash(self):
        self.assertEqual(dm.name_key("madonna"), ("m", "madonna"))

    def test_empty_or_non_string_is_neutral(self):
        self.assertEqual(dm.name_key(""), ("", ""))
        self.assertEqual(dm.name_key(None), ("", ""))


class FindMatchExactNameTests(unittest.TestCase):
    """Integration coverage against the real committed baseline for the same bug --
    NameKeyTests covers the key function in isolation, this confirms _find_match's exact-match
    fast path actually resolves the two real, differently-priced players correctly end to end."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    def test_aj_brown_and_amonra_st_brown_resolve_to_different_trade_value_chart_prices(self):
        tvc_players = self.merger.trade_values[self.merger.trade_values["asset_type"] == "player"]
        aj = self.merger.merge_player("A.J. Brown", df=tvc_players)
        amonra = self.merger.merge_player("Amon-Ra St. Brown", df=tvc_players)
        self.assertTrue(aj.get("matched"))
        self.assertTrue(amonra.get("matched"))
        self.assertNotEqual(aj.get("value"), amonra.get("value"))


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
        self.assertEqual(dm.recency_grade(0), "Fresh")
        self.assertEqual(dm.recency_grade(7), "Fresh")
        self.assertEqual(dm.recency_grade(8), "Recent")
        self.assertEqual(dm.recency_grade(30), "Recent")
        self.assertEqual(dm.recency_grade(31), "Aging")
        self.assertEqual(dm.recency_grade(90), "Aging")
        self.assertEqual(dm.recency_grade(91), "Stale")

    def test_missing_age_is_unknown(self):
        self.assertEqual(dm.recency_grade(None), "Unknown")


class CompositePoolSizeDampeningTests(unittest.TestCase):
    """The exact bug this class exists to prevent regressing: with a single bot_research
    finding on the books, EVERY finding read as the 100th percentile regardless of its actual
    rank (confirmed live -- a rank-1 claim and a rank-15 claim were indistinguishable), because
    a pool of one always ranks its only member first. COMPOSITE_MIN_TRUSTED_POOL_SIZE exists to
    stop a source that thin from swinging the composite as if its percentile were fully earned."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_findings_path = bot_research.FINDINGS_PATH
        bot_research.FINDINGS_PATH = Path(self._tmpdir) / "bot_research.json"
        self.bot_research = bot_research
        self.addCleanup(lambda: shutil.rmtree(self._tmpdir, ignore_errors=True))
        self.addCleanup(setattr, bot_research, "FINDINGS_PATH", self._orig_findings_path)

    def test_single_finding_barely_moves_the_composite(self):
        baseline_only = dm.DataMerger().composite_player_score("Maxx Crosby", position="DL")
        self.bot_research.add_finding("Maxx Crosby", "ESPN", "ranked #1 DL", rank=1)
        with_one_finding = dm.DataMerger().composite_player_score("Maxx Crosby", position="DL")
        # A single, thin-pool finding should nudge the score, not swing it -- well under half
        # of the gap between draftsharks' own trade_value-as-score reading and a naive 100th
        # percentile reading of the untrusted single-row pool.
        self.assertLess(with_one_finding["score"] - baseline_only["score"], 3.0)

    def test_weight_ramps_back_up_as_pool_grows_to_the_trusted_threshold(self):
        self.bot_research.add_finding("Maxx Crosby", "ESPN", "ranked #1 DL", rank=1)
        # bot_research's percentile pool is segmented by offense/IDP position group (see
        # _compute_percentiles), so fillers need to land in Crosby's own "idp" group to grow
        # HIS pool -- an unpositioned dummy name would just form its own separate one-off group.
        # Each of these shares a (first-initial, last-name) key with a real IDP row in the
        # baseline (Draft Sharks stores first-initial-only names), which is how that grouping
        # resolves a finding's position at all.
        idp_fillers = [
            "Cole Schwesinger", "Chase Gray", "Zack Baun", "Robert Spillane", "Jake Campbell",
            "Will Anderson", "Aidan Hutchinson", "Jamie Sherwood", "Brandon Burns",
            "Andrew Van Ginkel", "Devin Lloyd", "Quinn Walker", "Fred Warner", "Eli Cooper",
            "Ben Cashman", "Roman Smith", "Cole Conner", "Nick Bonitto", "Felix Oluokun",
        ]
        self.assertEqual(len(idp_fillers), dm.COMPOSITE_MIN_TRUSTED_POOL_SIZE - 1)
        for i, name in enumerate(idp_fillers):
            self.bot_research.add_finding(name, "ESPN", "filler", rank=i + 2)
        result = dm.DataMerger().composite_player_score("Maxx Crosby", position="DL")
        bot_component = next(c for c in result["components"] if c["source"] == "bot_research")
        self.assertEqual(bot_component["pool_size"], dm.COMPOSITE_MIN_TRUSTED_POOL_SIZE)
        self.assertAlmostEqual(
            bot_component["weight"],
            dm.COMPOSITE_SOURCE_WEIGHTS["bot_research"] * dm._recency_weight(bot_component["source_date"]),
            places=4,
        )

    def test_structured_sources_are_unaffected_by_a_thin_bot_research_pool(self):
        # Draft Sharks/DynastyProcess/etc. already have hundreds of rows -- their own weight
        # should be untouched by bot_research separately having only one entry.
        baseline_only = dm.DataMerger().composite_player_score("Ja'Marr Chase", position="WR")
        self.bot_research.add_finding("Some Unrelated Player", "ESPN", "unrelated claim", rank=1)
        after = dm.DataMerger().composite_player_score("Ja'Marr Chase", position="WR")
        ds_before = next(c for c in baseline_only["components"] if c["source"] == "draftsharks")
        ds_after = next(c for c in after["components"] if c["source"] == "draftsharks")
        self.assertAlmostEqual(ds_before["weight"], ds_after["weight"], places=6)


class BotResearchPercentilePositionSegmentationTests(unittest.TestCase):
    """bot_research findings carry whatever rank the source itself used, which is very often
    POSITION-RELATIVE ("#1 DL", "#1 RB") rather than a cross-position overall rank. Confirmed
    live: an offense "#1" claim and an IDP "#1" claim landed on the identical percentile
    (75.0) when pooled together, even though a #1 RB is worth far more than a #1 DL in real
    dynasty terms -- the same scarcity gap Draft Sharks' own trade_value already reflects.
    _compute_percentiles segments bot_research's pool by offense/IDP group to fix that."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_findings_path = bot_research.FINDINGS_PATH
        bot_research.FINDINGS_PATH = Path(self._tmpdir) / "bot_research.json"
        self.bot_research = bot_research
        self.addCleanup(lambda: shutil.rmtree(self._tmpdir, ignore_errors=True))
        self.addCleanup(setattr, bot_research, "FINDINGS_PATH", self._orig_findings_path)

    def test_number_one_offense_and_number_one_idp_claims_stay_in_separate_pools(self):
        self.bot_research.add_finding("Bijan Robinson", "FantasyPros", "ranked #1 RB", rank=1)
        self.bot_research.add_finding("Maxx Crosby", "ESPN", "ranked #1 DL", rank=1)
        merger = dm.DataMerger()
        bijan = merger.composite_player_score("Bijan Robinson", position="RB")
        crosby = merger.composite_player_score("Maxx Crosby", position="DL")
        bijan_bot = next(c for c in bijan["components"] if c["source"] == "bot_research")
        crosby_bot = next(c for c in crosby["components"] if c["source"] == "bot_research")
        # Each is alone in its own offense/IDP group now, not pooled together as a group of two.
        self.assertEqual(bijan_bot["pool_size"], 1)
        self.assertEqual(crosby_bot["pool_size"], 1)

    def test_a_weak_offense_claim_does_not_borrow_an_idp_players_percentile(self):
        # A #1 IDP claim shouldn't inflate/deflate based on an unrelated offense player's rank,
        # and vice versa -- confirms the two groups' percentiles are computed independently.
        self.bot_research.add_finding("Maxx Crosby", "ESPN", "ranked #1 DL", rank=1)
        self.bot_research.add_finding("Some Bench WR", "ESPN", "ranked #40 WR", rank=40)
        merger = dm.DataMerger()
        crosby = merger.composite_player_score("Maxx Crosby", position="DL")
        crosby_bot = next(c for c in crosby["components"] if c["source"] == "bot_research")
        self.assertEqual(crosby_bot["percentile"], 100.0)
        self.assertEqual(crosby_bot["pool_size"], 1)


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

    def test_draft_sharks_own_scarcity_gap_between_offense_and_idp_survives_the_composite(self):
        # The bug this test exists to prevent regressing: computing a percentile of
        # trade_value against the WHOLE pool (offense and IDP mixed, heavily bottom-loaded
        # with bench/depth players) made a clear NFL QB1 (Joe Burrow) and a solid-but-
        # unspectacular LB (Zack Baun) come out at nearly identical composite scores (83.3 vs
        # 81.1), even though Draft Sharks' own raw trade_value already says they aren't close
        # (32 vs 28 on a scale where elite offense reaches 100 and elite IDP tops out ~35-45).
        # Using trade_value directly (already 0-100, already scarcity-adjusted) instead of
        # re-deriving a percentile from it should keep them clearly separated.
        burrow = self.merger.composite_player_score("Joe Burrow", position="QB")
        baun = self.merger.composite_player_score("Zack Baun", position="LB")
        self.assertIsNotNone(burrow)
        self.assertIsNotNone(baun)
        self.assertGreater(burrow["score"] - baun["score"], 20)

    def test_single_source_idp_composite_equals_its_own_trade_value(self):
        # With only Draft Sharks contributing (no dynasty-scope IDP externals exist), the
        # composite should read as exactly what Draft Sharks itself said -- not a percentile
        # transform of it -- since trade_value is already on the composite's own 0-100 scale.
        crosby = self.merger.merge_player("Maxx Crosby", position="DL")
        composite = self.merger.composite_player_score("Maxx Crosby", position="DL")
        self.assertIsNotNone(composite)
        self.assertEqual(len(composite["components"]), 1)
        self.assertEqual(composite["components"][0]["source"], "draftsharks")
        self.assertAlmostEqual(composite["score"], crosby["trade_value"], places=4)

    def test_composite_capable_source_names_excludes_redraft_only_espn(self):
        # ESPN's only baseline file is redraft-scope and structurally excluded from the
        # composite entirely -- confirmed live, the sidebar's "Composite Sources Loaded" used
        # to count it anyway just because its rows existed in external_values at all.
        names = self.merger.composite_capable_source_names()
        self.assertNotIn("espn", names)
        # FantasyPros' dynasty file DOES feed the composite (only its best-ball/IDP-redraft
        # files are excluded), so the source name itself should still show as capable.
        self.assertIn("fantasypros", names)
        self.assertIn("dynastyprocess", names)
        self.assertIn("keeptradecut", names)

    def test_composite_components_only_drawn_from_dynasty_sources(self):
        # FantasyPros' best_ball_rankings.csv and idp_redraft_rankings.csv, and ESPN's
        # idp_redraft_rankings.csv, are redraft-scope and must never appear as a composite
        # component -- only dynasty-scope sources belong in _EXTERNAL_PERCENTILE_RULES.
        result = self.merger.composite_player_score("Maxx Crosby", position="DL")
        sources = {c["source"] for c in result["components"]} if result else set()
        self.assertTrue(sources.issubset({"draftsharks", "dynastyprocess", "fantasypros", "keeptradecut", "bot_research"}))


if __name__ == "__main__":
    unittest.main()
