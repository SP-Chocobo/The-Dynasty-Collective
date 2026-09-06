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


class TheFormatReachesTheMergerTests(unittest.TestCase):
    """The gap that made the first full run's scoring axis vacuous.

    `rec` and `bonus_rec_te` do NOT propagate through scoring_settings into offensive
    valuation -- Draft Sharks' season projection is a static pre-computed number. They
    propagate by FILE SELECTION: DataMerger.set_league_format picks a different Dynasty
    Rankings export, which app.py calls every rerun. A battery that never calls it drafts
    every format from whichever export happened to load, and reports "32 formats" while
    holding scoring constant -- measured: standard, half_ppr and ppr produced BYTE-IDENTICAL
    drafts in all eight size/superflex combinations.
    """

    def test_the_hint_is_derived_from_the_league_not_carried_beside_it(self):
        """A hint stored alongside each entry could disagree with the league it describes --
        two sources of truth for one fact. It is computed from roster_positions and
        scoring_settings by the same rules sleeper_client.league_format_summary uses."""
        self.assertEqual(
            {"scoring": "ppr", "superflex": False, "te_premium": True},
            batt.league_format_hint({"roster_positions": ["QB", "RB", "WR"],
                                     "scoring_settings": {"rec": 1.0, "bonus_rec_te": 0.5}}))
        self.assertEqual(
            {"scoring": "half_ppr", "superflex": True, "te_premium": False},
            batt.league_format_hint({"roster_positions": ["QB", "SUPER_FLEX"],
                                     "scoring_settings": {"rec": 0.5}}))
        self.assertEqual(
            {"scoring": "standard", "superflex": False, "te_premium": False},
            batt.league_format_hint({"roster_positions": ["QB", "RB"], "scoring_settings": {}}))

    def test_two_qbs_counts_as_superflex_without_a_superflex_slot(self):
        """sleeper_client's own rule: a league starting two QBs IS a superflex league however
        it spells the slot. Mirrored here rather than reinvented."""
        hint = batt.league_format_hint({"roster_positions": ["QB", "QB", "RB"],
                                        "scoring_settings": {}})
        self.assertTrue(hint["superflex"])

    def test_every_matrix_format_yields_a_usable_hint(self):
        for entry in batt.league_matrix():
            with self.subTest(label=entry["label"]):
                hint = batt.league_format_hint(entry["league"])
                self.assertIn(hint["scoring"], {"standard", "half_ppr", "ppr"})
                self.assertIsInstance(hint["superflex"], bool)
                self.assertIsInstance(hint["te_premium"], bool)

    def test_the_matrix_actually_varies_the_scoring_axis(self):
        """Non-vacuity: if every format resolved to the same hint, calling set_league_format
        would change nothing and the axis would still be untested."""
        hints = {tuple(sorted(batt.league_format_hint(e["league"]).items()))
                 for e in batt.league_matrix()}
        scorings = {dict(h)["scoring"] for h in hints}
        self.assertEqual({"standard", "half_ppr", "ppr"}, scorings)
        self.assertTrue(any(dict(h)["te_premium"] for h in hints))
        self.assertTrue(any(dict(h)["superflex"] for h in hints))


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

    def test_every_fill_audited_format_drafts_a_full_roster(self):
        """Rounds equal roster slots wherever the fill audit runs, which is what makes "did it
        fill its starters" a fair question -- a short draft would fail that audit for a reason
        that is not the engine's, and that reasoning is still right.

        WHAT CHANGED, AND WHY IT IS #161's SHARPEST FORM. This assertion used to apply to EVERY
        format, so the battery did not merely happen to share feasibility_first's
        `rounds == len(roster_positions)` assumption -- a test FORBADE anyone from varying it.
        #150 could not falsify #161 because the harness had a guard against the only
        configuration that would have. The protection for one audit had become a constraint on
        what the instrument could ever measure.

        Narrowed rather than deleted: the audit's own precondition is preserved where it runs,
        and the format that exists to break the assumption is exempted from that audit alone."""
        for entry in batt.league_matrix():
            if not entry.get("audit_roster_fill", True):
                continue
            with self.subTest(label=entry["label"]):
                self.assertEqual(entry["rounds"], len(entry["league"]["roster_positions"]))

    def test_the_matrix_carries_a_format_where_rounds_differ_from_slots(self):
        """Without this arm the repair to #161 is correct and untestable at scale. Pinned as a
        requirement so the battery cannot quietly return to measuring one relationship."""
        differing = [e["label"] for e in batt.league_matrix()
                     if e["rounds"] != len(e["league"]["roster_positions"])]
        self.assertTrue(differing, "the battery can no longer falsify #161")
        for label in differing:
            entry = next(e for e in batt.league_matrix() if e["label"] == label)
            self.assertFalse(entry.get("audit_roster_fill", True),
                             "a short draft must opt out of the fill audit, not fail it")

    def test_every_league_tells_the_engine_its_round_count(self):
        """#161: the engine cannot know the round count unless the league says so, and a
        battery that does not say so measures the fallback rather than the repair."""
        for entry in batt.league_matrix():
            with self.subTest(label=entry["label"]):
                self.assertEqual(entry["league"].get("draft_rounds"), entry["rounds"])


class TheInstrumentStatesItsOwnCoverageTests(unittest.TestCase):
    """#159. league_matrix() crosses four sizes x three scorings x two QB modes and the report
    named that count as though every arm were independent evidence. Measured against a real
    33-arm run: NINE arms reproduce another byte for byte, so the honest coverage is 24.

    Eight of the nine are the half_ppr family. There is no half-PPR export in
    data/baseline/rankings/, so set_league_format resolves a half_ppr league to the PPR file --
    scored 0.5 rather than 1.0 by data_merger._rankings_format_match_score, and disclosed to
    the user in app.py. The ENGINE is behaving correctly; the report was the thing overstating.

    The ninth was not predicted and is why this is derived rather than hand-listed:
    12T_ppr_mode_balanced reproduces 12T_ppr because UPSIDE_MODE_DEFAULT_ROUND is 15 and those
    arms draft 14 rounds, so "auto" never reaches its upside switch and IS "balanced" there.
    Benign -- 14 of 33 arms do run >= 15 rounds, so auto's upside branch is exercised elsewhere
    -- but a hand-written list naming half_ppr would have missed it entirely."""

    def _arm(self, label, **over):
        base = {"label": label, "picks": 10, "findings": [], "seconds": 1.0,
                "strength": {"starter_value_min": 1.0}, "teams": 12, "rounds": 14}
        base.update(over)
        return base

    def test_two_arms_with_identical_content_are_reported_as_one_duplicating_the_other(self):
        arms = [self._arm("a"), self._arm("b")]
        self.assertEqual(batt.duplicate_arms(arms), [{"label": "b", "duplicates": "a"}])

    def test_arms_that_differ_in_any_measured_field_are_not_duplicates(self):
        """Non-vacuity: a checker that called everything a duplicate would pass the test above."""
        self.assertEqual(batt.duplicate_arms([self._arm("a"), self._arm("b", picks=11)]), [])
        self.assertEqual(
            batt.duplicate_arms([self._arm("a"), self._arm("b", findings=[{"audit": "x"}])]), [])

    def test_wall_clock_does_not_make_every_arm_look_unique(self):
        """The bug this check was FIRST written with. A fingerprint including `seconds` reported
        zero duplicates against a matrix that has nine -- a plausible number about the wrong
        question, which is this repo's dominant measurement failure."""
        arms = [self._arm("a", seconds=1.0), self._arm("b", seconds=99.9)]
        self.assertEqual(batt.duplicate_arms(arms), [{"label": "b", "duplicates": "a"}])

    def test_the_label_itself_never_makes_two_arms_differ(self):
        arms = [self._arm("zzz"), self._arm("aaa")]
        self.assertEqual(len(batt.duplicate_arms(arms)), 1)

    def test_three_identical_arms_all_point_at_the_first(self):
        arms = [self._arm("a"), self._arm("b"), self._arm("c")]
        self.assertEqual([d["duplicates"] for d in batt.duplicate_arms(arms)], ["a", "a"])

    def test_an_empty_or_single_arm_run_reports_no_duplicates(self):
        self.assertEqual(batt.duplicate_arms([]), [])
        self.assertEqual(batt.duplicate_arms([self._arm("only")]), [])


def _pick_with(candidates, chosen, pick_no=1):
    """A pick whose snapshot carries exactly the candidate rows given -- the shape
    draft_board_ui.serialize_candidate produces, which is what PickRecord actually retains."""
    return draft_simulation.PickRecord(
        pick_no=pick_no, round=1, roster_id="1", pick_label=f"1.{pick_no:02d}",
        chosen_player_id=chosen, decision_regime="balanced",
        snapshot={"candidates": list(candidates)})


class UnpricedAtDecisionTests(unittest.TestCase):
    """#170. roster_strength's `unpriced_players` measures against the PRE-DRAFT ruler, where
    every row is priced and every drafted player is present -- so it is 0 by construction and
    reported as "every player priced" it reads like a statement about the engine. I made
    exactly that misreading in the register on the day it was written.

    This counter reads the board AS IT WAS AT THE PICK, off the snapshot the record already
    keeps, so it can come out non-zero. These tests pin the three things that make it worth
    having: it sees an unpriced candidate, it separates contending from winning, and it does
    NOT fold a missing key into a present None."""

    def test_a_priced_candidate_set_reports_no_absence(self):
        traj = _trajectory([_pick_with(
            [{"id": "a", "uv": 12.0}, {"id": "b", "uv": 3.5}], "a")])
        got = batt.unpriced_at_decision(traj)
        self.assertEqual(got["picks_examined"], 1)
        self.assertEqual(got["picks_with_an_unpriced_candidate"], 0)
        self.assertEqual(got["picks_that_took_an_unpriced_candidate"], 0)

    def test_an_unpriced_candidate_that_only_contends_is_not_counted_as_taken(self):
        traj = _trajectory([_pick_with(
            [{"id": "a", "uv": 12.0}, {"id": "b", "uv": None}], "a")])
        got = batt.unpriced_at_decision(traj)
        self.assertEqual(got["picks_with_an_unpriced_candidate"], 1)
        self.assertEqual(got["picks_that_took_an_unpriced_candidate"], 0)

    def test_an_unpriced_candidate_that_wins_the_pick_is_counted_as_taken(self):
        traj = _trajectory([_pick_with(
            [{"id": "a", "uv": 12.0}, {"id": "b", "uv": None}], "b")])
        got = batt.unpriced_at_decision(traj)
        self.assertEqual(got["picks_with_an_unpriced_candidate"], 1)
        self.assertEqual(got["picks_that_took_an_unpriced_candidate"], 1)

    def test_a_missing_uv_key_is_its_own_state_and_never_read_as_unpriced(self):
        """The defect a mutation found in this counter's first version. A row with no `uv` key
        is schema drift -- the field was never emitted -- and a row carrying None is the engine
        declining to price a player it did emit. Folding the first into the second would report
        an absence the engine never claimed, which is the same conflation the absence contract
        exists to prevent, committed inside the instrument that checks it."""
        traj = _trajectory([_pick_with(
            [{"id": "a", "uv": 12.0}, {"id": "b", "name": "no uv field at all"}], "a")])
        got = batt.unpriced_at_decision(traj)
        self.assertEqual(got["candidate_rows_missing_the_uv_key"], 1)
        self.assertEqual(got["picks_with_an_unpriced_candidate"], 0,
                         "a row with no uv key must not be reported as an unpriced candidate")

    def test_a_pick_with_no_candidate_set_is_not_examined_rather_than_counted_clean(self):
        """An empty candidate set is a pick nothing can be said about. Counting it as examined
        would put it in the denominator of a rate it was never eligible for."""
        traj = _trajectory([_pick_with([], "a"), _pick_with([{"id": "b", "uv": None}], "b", 2)])
        got = batt.unpriced_at_decision(traj)
        self.assertEqual(got["picks_examined"], 1)
        self.assertEqual(got["picks_with_an_unpriced_candidate"], 1)


if __name__ == "__main__":
    unittest.main()
