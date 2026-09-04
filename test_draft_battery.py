"""#150's audits, tested on synthetic trajectories that are CHEAP and WRONG on purpose.

The battery itself takes hours -- a full matrix is thousands of real board builds -- so its
value in a test suite is not "run it again". It is: does each audit actually FIRE on the defect
it names? An audit that silently returns [] for everything makes a battery report that says
"no findings" and means nothing, which is the failure this repository keeps finding in its own
instruments (a check that cannot fail is a check that is not running).

So every audit here gets a hand-built roster that violates exactly one thing, plus a clean
control. No DataMerger, no board builds: these tests are about the AUDITS, and mixing a real
draft into them would make a failure ambiguous between "the audit is broken" and "the engine
regressed" -- the same measurement/production separation the rest of this repo holds.
"""

import unittest

import draft_battery as batt
import draft_simulation


def _record(pick_no, roster_id, player_id, *, tav=10.0, candidates=None, regime="value",
            basis="live_starter_demand", growth=None, rounds_per=1):
    """One PickRecord with just enough retained board for the audits to read."""
    rows = candidates if candidates is not None else [
        {"id": player_id, "name": f"P{player_id}", "tav": tav},
        {"id": f"{player_id}-alt", "name": "alt", "tav": tav - 1.0},
    ]
    return draft_simulation.PickRecord(
        pick_no=pick_no, round=rounds_per, roster_id=roster_id,
        pick_label=f"{rounds_per}.{pick_no:02d}", chosen_player_id=player_id,
        decision_regime=regime, snapshot={"candidates": rows},
        chosen_replacement_basis=basis, chosen_growth_signal=growth)


def _trajectory(records, label="synthetic"):
    return draft_simulation.DraftTrajectory(config={"label": label}, picks=tuple(records))


#: One dedicated slot per position and nothing else, so "did it fill its starters" has an
#: unambiguous answer that this file did not invent -- roster_positions states it.
LEAGUE = {"roster_positions": ["QB", "RB", "WR", "TE", "BN"], "total_rosters": 1,
          "settings": {"type": 2}}
PLAYERS = {
    "q1": {"position": "QB", "fantasy_positions": ["QB"]},
    "r1": {"position": "RB", "fantasy_positions": ["RB"]},
    "w1": {"position": "WR", "fantasy_positions": ["WR"]},
    "t1": {"position": "TE", "fantasy_positions": ["TE"]},
    "q2": {"position": "QB", "fantasy_positions": ["QB"]},
    "k1": {"position": "K", "fantasy_positions": ["K"]},
}


class UnfilledStartingSlotsFiresTests(unittest.TestCase):
    """The audit that carries #150's actual question."""

    def test_a_roster_that_fills_every_slot_reports_nothing(self):
        traj = _trajectory([_record(i, "1", pid) for i, pid in enumerate(("q1", "r1", "w1", "t1", "q2"), 1)])
        self.assertEqual([], batt.unfilled_starting_slots(traj, LEAGUE, PLAYERS))

    def test_the_ablation_failure_mode_is_caught(self):
        """#87's measured result when need_bonus is removed: four QBs in a one-QB league. The
        roster is full and every pick is legal; it simply cannot field a lineup."""
        traj = _trajectory([_record(i, "1", pid) for i, pid in enumerate(("q1", "q2", "q1b", "q2b", "q3"), 1)])
        players = dict(PLAYERS, **{p: {"position": "QB", "fantasy_positions": ["QB"]}
                                   for p in ("q1b", "q2b", "q3")})
        findings = batt.unfilled_starting_slots(traj, LEAGUE, players)
        self.assertEqual(1, len(findings))
        self.assertEqual({"RB", "WR", "TE"}, set(findings[0]["empty_slots"]))

    def test_a_flex_chain_is_not_reported_as_a_hole(self):
        """Counting positions instead of solving the assignment gets this wrong: the spare RB
        legitimately fills FLEX, and a naive per-position tally would report a hole that the
        solver correctly does not find."""
        league = {"roster_positions": ["QB", "RB", "WR", "FLEX"], "total_rosters": 1,
                  "settings": {"type": 2}}
        traj = _trajectory([_record(i, "1", pid) for i, pid in enumerate(("q1", "r1", "w1", "r2"), 1)])
        players = dict(PLAYERS, r2={"position": "RB", "fantasy_positions": ["RB"]})
        self.assertEqual([], batt.unfilled_starting_slots(traj, league, players))


class TheOtherStructuralAuditsFireTests(unittest.TestCase):
    def test_an_unpriced_pick_is_caught(self):
        traj = _trajectory([_record(1, "1", "q1", candidates=[{"id": "q1", "name": "Q", "tav": None}])])
        findings = batt.unpriced_picks(traj)
        self.assertEqual(1, len(findings))
        self.assertIn("tav=None", findings[0]["reason"])

    def test_a_pick_missing_from_its_own_board_is_caught(self):
        """A retained record that cannot explain its own pick is worse than a wrong pick."""
        traj = _trajectory([_record(1, "1", "q1", candidates=[{"id": "other", "name": "X", "tav": 5.0}])])
        self.assertEqual(1, len(batt.unpriced_picks(traj)))

    def test_a_priced_pick_reports_nothing(self):
        self.assertEqual([], batt.unpriced_picks(_trajectory([_record(1, "1", "q1")])))

    def test_a_position_the_league_cannot_start_is_caught(self):
        traj = _trajectory([_record(1, "1", "k1")])
        findings = batt.undraftable_positions(traj, LEAGUE, PLAYERS)
        self.assertEqual([("1", "K")], [(f["roster_id"], f["position"]) for f in findings])

    def test_a_startable_position_reports_nothing(self):
        self.assertEqual([], batt.undraftable_positions(_trajectory([_record(1, "1", "q1")]),
                                                        LEAGUE, PLAYERS))

    def test_a_duplicate_pick_is_caught(self):
        traj = _trajectory([_record(1, "1", "q1"), _record(2, "2", "q1")])
        self.assertEqual(1, len(batt.duplicate_picks(traj)))

    def test_distinct_picks_report_nothing(self):
        traj = _trajectory([_record(1, "1", "q1"), _record(2, "2", "r1")])
        self.assertEqual([], batt.duplicate_picks(traj))


class ReportedDistributionsDescribeRatherThanJudgeTests(unittest.TestCase):
    """These deliberately return no findings -- they are the half of the battery that reports a
    number for a person to read, because judging them needs a threshold nobody has argued for."""

    def test_a_zero_margin_pick_is_counted_not_flagged(self):
        """#114's late-draft collapse. Two candidates priced identically means the ordering
        carried no information -- worth SEEING, not automatically wrong."""
        tied = [{"id": "a", "name": "A", "tav": 4.0}, {"id": "b", "name": "B", "tav": 4.0}]
        traj = _trajectory([_record(1, "1", "a", candidates=tied), _record(2, "2", "r1")])
        profile = batt.tav_margin_profile(traj)
        self.assertEqual(2, profile["picks_measured"])
        self.assertEqual(1, profile["zero_margin_picks"])
        self.assertAlmostEqual(0.5, profile["zero_margin_share"])
        self.assertNotIn("findings", profile)

    def test_roster_shape_counts_by_position(self):
        traj = _trajectory([_record(1, "1", "q1"), _record(2, "1", "q2"), _record(3, "2", "r1")])
        self.assertEqual({"1": {"QB": 2}, "2": {"RB": 1}}, batt.roster_shape(traj, PLAYERS))

    def test_the_qualifier_profile_separates_the_two_kinds_of_price(self):
        """#138's carried fields, doing the job they were carried for: a pick resting on the
        pre-draft anchor is a weaker claim than one resting on live demand, and a report that
        cannot tell them apart is the blindness that repair removed."""
        traj = _trajectory([
            _record(1, "1", "q1", basis="live_starter_demand"),
            _record(2, "2", "r1", basis="predraft_anchor", growth=12.5),
        ])
        profile = batt.qualifier_profile(traj)
        self.assertEqual({"live_starter_demand": 1, "predraft_anchor": 1},
                         profile["replacement_basis"])
        self.assertEqual(1, profile["picks_with_growth_measured"])
        self.assertEqual(12.5, profile["max_growth"])

    def test_a_measured_growth_of_zero_is_not_reported_as_no_growth(self):
        """The absence contract, in the battery's OWN reporting -- and it failed here first.
        A truthiness test read an upside pick that legitimately measured 0.0 as if growth had
        never been computed, which is the same conflation the engine is held to everywhere
        else. Balanced picks carry None (never computed); an upside pick can carry 0.0
        (computed, and this player has no trajectory). Those are different facts."""
        traj = _trajectory([
            _record(1, "1", "q1", growth=0.0),    # upside, measured, genuinely zero
            _record(2, "2", "r1", growth=None),   # balanced, never computed
            _record(3, "3", "w1", growth=4.0),
        ])
        profile = batt.qualifier_profile(traj)
        self.assertEqual(2, profile["picks_with_growth_measured"])
        self.assertEqual(1, profile["picks_with_growth_above_zero"])

    def test_the_matrix_varies_mode_explicitly(self):
        """Modes are one of the axes #150 names, and auto alone does not vary it: auto switches
        to upside only at UPSIDE_MODE_DEFAULT_ROUND, which most formats never reach. Measured
        before this was added -- 0 picks carried a growth_signal across 280 picks."""
        entries = {e["label"]: e for e in batt.league_matrix()}
        modes = {e.get("mode") for e in entries.values()}
        self.assertIn("upside", modes, "no format runs upside mode, so growth_signal and the "
                                       "whole upside scoring path go unexercised")
        self.assertIn("balanced", modes)
        upside = next(e for e in entries.values() if e.get("mode") == "upside")
        self.assertGreater(upside["rounds"], 0)

    def test_first_round_taken_reports_absence_as_none(self):
        traj = _trajectory([_record(1, "1", "q1")])
        self.assertEqual(1, batt.first_round_taken(traj, PLAYERS, "QB"))
        self.assertIsNone(batt.first_round_taken(traj, PLAYERS, "TE"))


class TheMatrixIsWideAndCarriesItsNamedFormatsTests(unittest.TestCase):
    def test_it_spans_the_axes_a_real_league_varies_on(self):
        matrix = batt.league_matrix()
        self.assertGreater(len(matrix), 25)
        self.assertGreater(len({e["teams"] for e in matrix}), 3)
        labels = {e["label"] for e in matrix}
        self.assertTrue(any("_SF" in l for l in labels), "no superflex format")
        self.assertTrue(any("redraft" in l for l in labels), "no redraft format")
        self.assertTrue(any("TEP" in l for l in labels), "no TE-premium format")

    def test_the_two_register_driven_formats_are_present(self):
        """Carried for a named prediction rather than for coverage -- #153 should show in
        4WR_TE_PREMIUM's WR counts and nowhere else, and #152 predicts HEAVY_IDP takes IDP
        late. If either format is dropped, the battery stops being able to see its item."""
        labels = {e["label"] for e in batt.league_matrix()}
        self.assertIn("4WR_TE_PREMIUM", labels)
        self.assertIn("HEAVY_IDP", labels)

    def test_every_format_drafts_a_full_roster(self):
        """Rounds equal roster slots, which is what makes "did it fill its starters" a fair
        question -- a short draft would fail that audit for a reason that is not the engine's."""
        for entry in batt.league_matrix():
            with self.subTest(label=entry["label"]):
                self.assertEqual(entry["rounds"], len(entry["league"]["roster_positions"]))


if __name__ == "__main__":
    unittest.main()
