"""MANDATE 2.2 / #126 -- a gate that refuses every league it governs is not a gate.

`league_config.ambiguities` refused **53 of the 53 production-shaped leagues**
`draft_battery.league_matrix` builds, and would have refused the owner's own real league too. A
refusal on every input carries no information: wire it to the app as it was and the app stops
working; leave it unwired and the checks it performs are decoration. That is why 2.2 read as "the
gate is unwired" -- the gate could not be wired.

Two of its four required keys were wrong, in two DIFFERENT ways, and this module pins both repairs
plus the three checks that were right all along.

  * THE TEAM COUNT WAS ASKED FOR UNDER A NAME NOTHING READS (#126, one home for a vocabulary).
    The gate wanted `num_teams` in `scoring` or `settings`. Sleeper sends `total_rosters` at the
    top level, and that is what every production reader takes. `num_teams` absent in 53 of 53;
    `total_rosters` present in 53 of 53.

  * AN OMITTED SCORING KEY WAS READ AS AN UNKNOWN (#187, absence has a contract). Sleeper returns
    a complete scoring dict and omits what the league does not score, so a key absent from a
    POPULATED dict is a declared zero -- which is exactly the conclusion `league_format_hint`
    draws from it. `bonus_rec_te` absent in 47 of 53, all with populated dicts.

What still blocks, and should: an absent dynasty flag, an absent team count, and a league that
brought no scoring dict at all."""

import unittest, json
import league_config as lc
import draft_battery as db
import run_draft_battery as rdb


def _full_league(**over):
    """A league with nothing missing, so each test can remove exactly one thing."""
    league = {
        "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "BN", "BN"],
        "scoring_settings": {"rec": 1.0, "bonus_rec_te": 0.5, "pass_yd": 0.04},
        "settings": {"type": 2},
        "total_rosters": 12,
    }
    league.update(over)
    return league


class TheGateAdmitsTheLeaguesItGovernsTests(unittest.TestCase):
    """Over the real matrix, not a hand-built league, because the false refusal was 100% and a
    fixture chosen after the fact could have hidden that."""

    @classmethod
    def setUpClass(cls):
        capture = json.loads(open(rdb.CAPTURE_PATH, encoding="utf-8").read())
        cls.arms = db.league_matrix((capture.get("league_shape") or {}).get("scoring_settings"))

    def test_the_matrix_is_big_enough_for_a_rate_over_it_to_mean_anything(self):
        self.assertGreater(len(self.arms), 40,
                           "vacuous: too few arms for 'refused N of N' to be a measurement")

    def test_the_only_leagues_still_refused_are_the_ones_missing_a_dynasty_flag(self):
        refused = {arm["label"]: lc.ambiguities(arm["league"])
                   for arm in self.arms if lc.ambiguities(arm["league"])}
        no_flag = {arm["label"] for arm in self.arms
                   if (arm["league"].get("settings") or {}).get("type") is None}
        self.assertEqual(set(refused), no_flag,
                         f"the gate and the dynasty flag disagree about which arms are readable: "
                         f"refused={sorted(refused)} flagless={sorted(no_flag)}")
        for label, found in refused.items():
            self.assertEqual([item["kind"] for item in found], ["missing_format_keys"], label)
            self.assertIn("type", found[0]["detail"], label)

    def test_the_arms_the_gate_refuses_are_the_ones_the_battery_itself_calls_redraft(self):
        """An independent cross-check. `draft_battery` states, in its own comment and in an arm
        field, that the capture carries no dynasty flag and that those arms draft as redraft. The
        gate reaches the same verdict from the league dict alone, so two separately written
        judgements agree arm for arm."""
        stated = {arm["label"] for arm in self.arms
                  if arm.get("dynasty_flag_present_in_capture") is False}
        self.assertTrue(stated, "vacuous: no arm states its dynasty flag is absent")
        for label in stated:
            arm = next(a for a in self.arms if a["label"] == label)
            self.assertTrue(lc.ambiguities(arm["league"]),
                            f"{label} says its dynasty flag is absent but the gate admits it")


class AnOmittedKeyIsNotTheSameAsAnUnreadOneTests(unittest.TestCase):
    def test_a_populated_scoring_dict_missing_a_zero_valued_key_is_admitted(self):
        """The 47-of-53 case. A league that does not pay a TE bonus omits the key; concluding
        "no TE premium" from that is right, and it is what league_format_hint concludes."""
        league = _full_league(scoring_settings={"rec": 1.0, "pass_yd": 0.04})
        self.assertEqual(lc.ambiguities(league), [])
        self.assertTrue(lc.admits_decision(league)[0])

    def test_a_league_scoring_no_receptions_at_all_is_admitted_as_standard(self):
        league = _full_league(scoring_settings={"pass_yd": 0.04, "rush_yd": 0.1})
        self.assertEqual(lc.ambiguities(league), [])

    def test_a_league_with_NO_scoring_dict_is_still_refused(self):
        """The distinction the repair turns on: an empty dict is an unread config, not a league
        that scores nothing."""
        found = lc.ambiguities(_full_league(scoring_settings={}))
        self.assertEqual([item["kind"] for item in found], ["missing_format_keys"])
        for key in lc.FORMAT_DECIDING_SCORING_KEYS:
            self.assertIn(key, found[0]["detail"])


class TheTeamCountIsAskedForUnderItsRealNameTests(unittest.TestCase):
    def test_a_league_carrying_total_rosters_and_no_num_teams_is_admitted(self):
        """The 53-of-53 case, and the shape of every league Sleeper actually sends."""
        league = _full_league()
        self.assertNotIn("num_teams", league.get("settings") or {})
        self.assertEqual(lc.ambiguities(league), [])

    def test_num_teams_alone_does_NOT_satisfy_the_gate(self):
        """Positive statement of the vocabulary rule: the gate follows the ENGINE's name, so a
        count the engine cannot read is not a count. Without this the repair could be "accept
        either", which would admit a league whose replacement levels are built on one team."""
        league = _full_league(total_rosters=None)
        league["settings"] = {"type": 2, "num_teams": 12}
        found = lc.ambiguities(league)
        self.assertTrue(found, "a league the engine cannot read a team count from was admitted")
        self.assertIn(lc.TEAM_COUNT_KEY, found[0]["detail"])

    def test_an_absent_team_count_blocks_because_the_fallback_is_one_team(self):
        league = _full_league()
        del league["total_rosters"]
        found = lc.ambiguities(league)
        self.assertEqual([item["kind"] for item in found], ["missing_format_keys"])
        self.assertIn(lc.TEAM_COUNT_KEY, found[0]["detail"])

    def test_the_count_is_read_from_the_TOP_LEVEL_not_from_settings(self):
        league = _full_league(total_rosters=None)
        league["settings"] = {"type": 2, "total_rosters": 12}
        self.assertTrue(lc.ambiguities(league),
                        "a team count buried in settings satisfied a top-level check")


class TheChecksThatWereRightAreUntouchedTests(unittest.TestCase):
    def test_an_absent_dynasty_flag_still_blocks(self):
        league = _full_league(settings={})
        found = lc.ambiguities(league)
        self.assertEqual([item["kind"] for item in found], ["missing_format_keys"])
        self.assertIn("type", found[0]["detail"])

    def test_a_clean_league_is_INFERRED_and_admitted(self):
        self.assertEqual(lc.confirmation_state(_full_league()), lc.INFERRED)
        self.assertTrue(lc.admits_decision(_full_league())[0])
        self.assertIs(lc.decision_config(_full_league()) is None, False)

    def test_num_teams_is_no_longer_declared_anywhere_in_the_vocabulary(self):
        self.assertNotIn("num_teams", lc.FORMAT_DECIDING_KEYS)
        self.assertNotIn("num_teams", lc.FORMAT_DECIDING_SCORING_KEYS)
        self.assertNotIn("num_teams", lc.FORMAT_DECIDING_SETTINGS_KEYS)
        self.assertEqual(lc.TEAM_COUNT_KEY, "total_rosters")

    def test_the_union_is_exactly_its_two_halves(self):
        """#126: the whole-vocabulary name must not drift from the parts it is built out of."""
        self.assertEqual(set(lc.FORMAT_DECIDING_KEYS),
                         set(lc.FORMAT_DECIDING_SCORING_KEYS)
                         | set(lc.FORMAT_DECIDING_SETTINGS_KEYS))


if __name__ == "__main__":
    unittest.main()
