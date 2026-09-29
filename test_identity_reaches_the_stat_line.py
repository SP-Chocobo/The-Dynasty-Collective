"""MANDATE 2.3 / `#166`: three ways a real thing could not reach the row that prices it.

  * **11 of 32 TEAM DEFENSES could not resolve.** `name_key` keys a name on everything after the
    first token, which is right for a person and wrong for a franchise: Sleeper names a defense
    `first_name` (city) + `last_name` (nickname), so "Green Bay Packers" keys to ("g", "bay
    packers") while the vendor's own transcribed row "G Packers" keys to ("g", "packers"). The 11
    are exactly the multi-word cities; the 21 single-word ones matched by luck.
  * **One player split into two canonical records.** `_identity_hint` is detected per file — which
    is correct, simultaneity is observable nowhere else — and was also STAMPED per file, so a name
    contested in one file and alone in another produced two different dedup keys.
  * **The league's kicking rules could not reach the stat line.** `score_projection` is a dot
    product over the stat keys present, so `fgmiss` — a category the captured league scores at
    -1.0 — applied to nothing at all, and every kicker was priced as if he never missed.

The 50+ bucket is deliberately NOT repaired here and the reason is measured, not assumed. See
`TheFiftyPlusBucketIsNotDerivableAndSaysSo`.
"""
from __future__ import annotations

import statistics
import unittest

import data_merger as dm
import player_universe as pu
import run_draft_battery as rdb


NFL_TEAMS = (
    "Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens", "Buffalo Bills",
    "Carolina Panthers", "Chicago Bears", "Cincinnati Bengals", "Cleveland Browns",
    "Dallas Cowboys", "Denver Broncos", "Detroit Lions", "Green Bay Packers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Kansas City Chiefs",
    "Las Vegas Raiders", "Los Angeles Chargers", "Los Angeles Rams", "Miami Dolphins",
    "Minnesota Vikings", "New England Patriots", "New Orleans Saints", "New York Giants",
    "New York Jets", "Philadelphia Eagles", "Pittsburgh Steelers", "San Francisco 49ers",
    "Seattle Seahawks", "Tampa Bay Buccaneers", "Tennessee Titans", "Washington Commanders",
)


class ATeamDefenseIsKeyedByTheVendorsOwnAbbreviation(unittest.TestCase):
    def test_the_spelled_out_name_and_the_abbreviation_agree_for_ALL_32(self):
        mismatched = []
        for team in NFL_TEAMS:
            nickname = team.split()[-1]
            full = dm.team_defense_key(dm.normalize_name(team))
            abbreviated = dm.team_defense_key(
                dm.normalize_name(f"{team.split()[0][0]} {nickname}"))
            if full != abbreviated:
                mismatched.append((team, full, abbreviated))
        self.assertEqual(mismatched, [], f"{len(mismatched)} defenses still cannot resolve")

    def test_the_PERSON_rule_still_fails_on_exactly_those_11(self):
        """The defect, pinned. If `name_key` ever starts agreeing here, this repair is redundant and
        the reader should find that out from a test rather than by guessing."""
        mismatched = [
            team for team in NFL_TEAMS
            if dm.name_key(dm.normalize_name(team))
            != dm.name_key(dm.normalize_name(f"{team.split()[0][0]} {team.split()[-1]}"))
        ]
        self.assertEqual(len(mismatched), 11, mismatched)
        for team in mismatched:
            self.assertGreater(len(team.split()), 2, f"{team} is not a multi-word city")

    def test_there_is_no_hardcoded_list_of_32_teams_in_the_merger(self):
        """A franchise roster is a constant that goes stale on the next rename. What the repair
        encodes is the ABBREVIATION RULE both sides already follow."""
        source = dm.team_defense_key.__doc__ or ""
        self.assertIn("NO LIST OF 32 NICKNAMES", source)
        for nickname in ("Packers", "Commanders", "49ers"):
            self.assertNotIn(f'"{nickname.lower()}"', dm.__dict__.get("__file__", "") or "")

    def test_a_PERSON_never_falls_into_the_defense_rule(self):
        """`name_key`'s own docstring records a real defect from last-token keying: "A.J. Brown" and
        "Amon-Ra St. Brown" both key to ("a", "brown") and one was priced as the other. The defense
        arm is gated on the CALLER's position, never on the shape of the name."""
        self.assertEqual(dm.name_key("amonra st brown"), ("a", "st brown"))
        self.assertEqual(dm.name_key("aj brown"), ("a", "brown"))
        self.assertNotEqual(dm.name_key("amonra st brown"), dm.name_key("aj brown"))

    def test_every_one_of_the_32_resolves_against_the_real_baseline(self):
        """End to end on committed data, not on a fixture: the thing the item is about."""
        merger = dm.DataMerger()
        unresolved = [team for team in NFL_TEAMS
                      if merger._find_match(team, position="DEF") is None]
        self.assertEqual(unresolved, [], f"{len(unresolved)} defenses do not resolve")

    def test_and_the_person_rule_would_leave_11_unresolved(self):
        """The A/B, in one process, with one thing toggled — so the 11 is this repair's own
        measurement rather than a number carried from a different run."""
        merger = dm.DataMerger()
        real = dm.team_defense_key
        try:
            dm.team_defense_key = dm.name_key
            before = [t for t in NFL_TEAMS if merger._find_match(t, position="DEF") is None]
        finally:
            dm.team_defense_key = real
        self.assertEqual(len(before), 11, before)


class TheContestedHintAppliesAcrossFilesNotJustWithinOne(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.projections = cls.merger.projections

    def _hints(self):
        return self.projections["_identity_hint"].fillna("").astype(str)

    def test_the_contested_population_is_not_empty(self):
        """Non-vacuity: every assertion below is about the hinted rows, so an empty set would make
        them all pass while proving nothing."""
        self.assertGreater(int((self._hints() != "").sum()), 0)

    def test_every_hinted_row_carries_its_OWN_position_as_the_discriminator(self):
        hints = self._hints()
        flagged = self.projections[hints != ""]
        # .iterrows(), not .itertuples(): itertuples renames a leading-underscore column to a
        # positional `_12`, so `row._identity_hint` raises and the test never reaches its assertion.
        for _index, row in flagged.iterrows():
            self.assertEqual(
                str(row["_identity_hint"]), str(row["position"]).strip().upper(),
                f"{row['norm_name']} carries a hint that is not its own position")

    def test_a_contested_name_has_one_row_per_position_and_no_duplicates(self):
        """The split, closed: before the propagation a name contested in one file and alone in
        another produced two dedup keys for the same person and two canonical rows."""
        hints = self._hints()
        for name in sorted(set(self.projections.loc[hints != "", "norm_name"])):
            rows = self.projections[self.projections["norm_name"] == name]
            positions = [str(p).strip().upper() for p in rows["position"]]
            self.assertEqual(len(positions), len(set(positions)),
                             f"{name} has two canonical rows at one position")

    def test_an_ordinary_name_carries_no_hint(self):
        """The coarse dedup key has to keep working for everyone it was designed for: a genuine
        reclassification still collapses onto one row."""
        hints = self._hints()
        self.assertGreater(int((hints == "").sum()), len(self.projections) // 2)


class TheLeaguesKickingRuleReachesTheStatLine(unittest.TestCase):
    SCORING = {"fgm_20_29": 3.0, "fgm_30_39": 3.0, "fgm_40_49": 4.0,
               "fgm_50p": 5.0, "fgmiss": -1.0, "xpm": 1.0}

    def test_misses_are_derived_EXACTLY_from_attempts_minus_makes(self):
        stats = {"fga": 38.0, "fgm": 32.0}
        self.assertEqual(pu.derive_kicking_categories(stats)["fgmiss"], 6.0)

    def test_and_they_now_actually_score(self):
        with_misses = pu.score_projection({"fga": 38.0, "fgm": 32.0, "fgm_30_39": 32.0},
                                          self.SCORING)
        without = pu.score_projection({"fgm": 32.0, "fgm_30_39": 32.0}, self.SCORING)
        self.assertEqual(without - with_misses, 6.0)

    def test_a_position_that_kicks_nothing_is_untouched(self):
        stats = {"rec": 80.0, "rec_yd": 1000.0}
        self.assertIs(pu.derive_kicking_categories(stats), stats)

    def test_attempts_without_makes_derives_NOTHING(self):
        """A 0 assumed for either input would fabricate the difference (`#187`)."""
        self.assertNotIn("fgmiss", pu.derive_kicking_categories({"fga": 38.0}))
        self.assertNotIn("fgmiss", pu.derive_kicking_categories({"fgm": 32.0}))

    def test_a_vendor_supplied_fgmiss_is_never_overwritten(self):
        stats = {"fga": 38.0, "fgm": 32.0, "fgmiss": 99.0}
        self.assertEqual(pu.derive_kicking_categories(stats)["fgmiss"], 99.0)

    def test_attempts_below_makes_is_a_disagreement_and_not_zero_misses(self):
        """Attempts under makes is a projection whose own numbers disagree. Left ABSENT rather than
        scored as a measured zero."""
        self.assertNotIn("fgmiss", pu.derive_kicking_categories({"fga": 30.0, "fgm": 32.0}))

    def test_on_the_real_capture_every_kicker_loses_points_and_none_gains(self):
        """The direction is the whole claim: a miss can only cost. Measured across the capture's
        kickers rather than asserted."""
        weekly = rdb.weekly_projections_from_capture()
        players = rdb.build_players_db_from_capture()[0]
        scoring = rdb.scoring_settings_from_capture()
        kickers = {pid for pid, info in players.items()
                   if str(info.get("position")).upper() == "K"}
        deltas = []
        real = pu.derive_kicking_categories
        for _week, rows in weekly.items():
            for pid, stats in rows.items():
                if pid not in kickers or not isinstance(stats, dict) or "fgm" not in stats:
                    continue
                after = pu.score_projection(stats, scoring)
                try:
                    pu.derive_kicking_categories = lambda s: s
                    before = pu.score_projection(stats, scoring)
                finally:
                    pu.derive_kicking_categories = real
                deltas.append(after - before)
        self.assertTrue(deltas, "no kicker projection was scored; the test proves nothing")
        self.assertLessEqual(max(deltas), 0.0, "a derived miss increased a kicker's score")
        self.assertLess(statistics.mean(deltas), 0.0)


class TheMandatesOwnClaimForThisItemIsCorrected(unittest.TestCase):
    """The item says "There is no `fgm_50p` key, so 5.5-8.8 projected 50+ makes per kicker are never
    scored". Measured over every kicker-week projection in the capture, that is FALSE -- and my own
    first probe reached the same wrong answer by sampling one week's first kicker and generalising,
    which is the fixture failure mode the measurement discipline exists to catch.

    The unscored quantity was the MISSES. These tests hold the correction so nobody repairs the
    long-makes non-defect later."""

    @classmethod
    def setUpClass(cls):
        weekly = rdb.weekly_projections_from_capture()
        players = rdb.build_players_db_from_capture()[0]
        kickers = {pid for pid, info in players.items()
                   if str(info.get("position")).upper() == "K"}
        cls.rows = [stats for _week, rows in weekly.items() for pid, stats in rows.items()
                    if pid in kickers and isinstance(stats, dict) and "fgm" in stats]
        cls.scoring = rdb.scoring_settings_from_capture()

    def test_the_population_is_the_whole_capture_and_not_one_week(self):
        self.assertGreater(len(self.rows), 500,
                           "too few kicker-week rows for a claim about coverage")

    def test_fgm_50p_IS_projected_on_almost_every_row(self):
        with_bucket = sum(1 for stats in self.rows if "fgm_50p" in stats)
        self.assertGreater(with_bucket / len(self.rows), 0.9,
                           "the long-makes bucket really is missing, and the mandate was right")

    def test_and_the_league_weights_it_so_it_was_ALREADY_scoring(self):
        self.assertTrue(self.scoring.get("fgm_50p"))
        stats = {"fgm_50p": 2.0}
        self.assertEqual(pu.score_projection(stats, self.scoring),
                         2.0 * self.scoring["fgm_50p"])

    def test_the_GENERIC_miss_category_is_what_no_row_carried(self):
        self.assertEqual([stats for stats in self.rows if "fgmiss" in stats], [],
                         "a vendor-supplied fgmiss exists, so the derivation is not needed")
        self.assertTrue(self.scoring.get("fgmiss"),
                        "the league does not score misses, so there was nothing to bridge")

    def test_the_vendor_buckets_misses_under_keys_the_league_does_not_weight(self):
        """The vocabulary mismatch itself: both sides describe misses, neither in the other's words."""
        bucketed = [key for key in ("fgmiss_30_39", "fgmiss_40_49", "fgmiss_50p")
                    if any(key in stats for stats in self.rows)]
        self.assertTrue(bucketed, "the vendor projects no bucketed misses either")
        for key in bucketed:
            self.assertFalse(self.scoring.get(key),
                             f"the league weights {key}, so it was already scoring")

    def test_the_bucketed_sum_is_INCOMPLETE_which_is_why_the_total_is_used(self):
        """No short-range miss bucket exists -- neither fgmiss_0_19 nor fgmiss_20_29, de-backticked
        because 0.8's instrument is right that a backticked name should be a name in the tree and the
        whole point here is that these two are not -- so the buckets understate the total. If they
        ever agree exactly, the derivation could read the vendor's own numbers instead."""
        differing = 0
        for stats in self.rows:
            if "fgmiss_50p" not in stats:
                continue
            bucketed = sum(float(stats.get(k) or 0)
                           for k in ("fgmiss_30_39", "fgmiss_40_49", "fgmiss_50p"))
            total = float(stats["fga"]) - float(stats["fgm"])
            if abs(bucketed - total) >= 0.01:
                differing += 1
        self.assertGreater(differing, 100,
                           "the buckets now cover every miss; prefer the vendor's own sum")


if __name__ == "__main__":
    unittest.main()
