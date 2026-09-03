"""#139 / #115 / #62: depth_exposure -- what a hole costs, and the four states of knowing.

Depth demand is not "a slot exists, so fill it." Nobody needs a fourth TE because their league
has one TE slot. Depth is insurance, and it is worth what the hole would actually cost -- which
depends on who is already rostered and on whether anything else can cover the slot.

Every claim depth_exposure's docstring makes is pinned here, because two of them were WRONG on
first measurement and were only caught by running them. The self-limiting property does not
hold on a roster with no bench (every body is on the field, so nothing can backfill and every
loss costs full value), and that turned out to be a real domain boundary rather than a bug --
now carried as EXPOSURE_NO_SURPLUS instead of being left for a reader to rediscover from a
number that looks measured and is not.
"""

from __future__ import annotations

import unittest

import lineup_optimizer as lo

#: A conventional 12-team dynasty lineup: one QB, two RB, two WR, one TE, two FLEX, five bench.
LEAGUE = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX",
          "BN", "BN", "BN", "BN", "BN"]


def _p(pid: str, value: float, position: str) -> dict:
    return {"id": pid, "value": float(value), "eligible": {position}}


#: Eleven players against eight starting slots -- a genuine bench, which is the only state in
#: which depth is a meaningful question at all.
DEEP = [
    _p("qb1", 30, "QB"), _p("qb2", 14, "QB"),
    _p("rb1", 25, "RB"), _p("rb2", 20, "RB"), _p("rb3", 19, "RB"), _p("rb4", 11, "RB"),
    _p("wr1", 28, "WR"), _p("wr2", 22, "WR"), _p("wr3", 18, "WR"), _p("wr4", 17, "WR"),
    _p("te1", 15, "TE"),
]

#: Seven players against eight slots -- everyone starts, so nothing can backfill.
SHALLOW = [
    _p("qb1", 30, "QB"),
    _p("rb1", 25, "RB"), _p("rb2", 20, "RB"),
    _p("wr1", 28, "WR"), _p("wr2", 22, "WR"), _p("wr3", 18, "WR"),
    _p("te1", 15, "TE"),
]


def _worst(roster, league=LEAGUE) -> dict[str, float]:
    return {pos: d["worst_loss"] for pos, d in lo.depth_exposure(roster, league).items()
            if d["starters"]}


class BenchCapacityTests(unittest.TestCase):
    """Sleeper states bench size directly and nothing in this app had ever counted it."""

    def test_it_counts_the_leagues_own_bench_slots(self):
        self.assertEqual(lo.bench_capacity(LEAGUE), 5)

    def test_a_league_with_no_bench_is_zero_not_a_default(self):
        self.assertEqual(lo.bench_capacity(["QB", "RB", "WR", "TE", "FLEX"]), 0)

    def test_absent_roster_positions_do_not_raise(self):
        self.assertEqual(lo.bench_capacity([]), 0)
        self.assertEqual(lo.bench_capacity(None), 0)

    def test_taxi_and_ir_are_not_bench(self):
        """They hold players, but not ones available to cover a hole this week."""
        self.assertEqual(lo.bench_capacity(["QB", "BN", "TAXI", "IR", "BN"]), 2)


class SelfLimitingByDepthTests(unittest.TestCase):
    """The claim that makes this a depth model rather than a slot-counter: a position stops
    being urgent once it is genuinely covered, without any rule saying so."""

    def test_a_competent_backup_collapses_the_exposure(self):
        bare = _worst(DEEP)["TE"]
        covered = _worst(DEEP + [_p("te2", 13, "TE")])["TE"]
        self.assertEqual(bare, 15.0)
        self.assertLess(covered, 3.0,
                        "a TE2 within 2 points of TE1 should leave almost nothing exposed")

    def test_a_BAD_backup_does_not_insure(self):
        """The number has to track the quality of the cover, not merely its existence --
        otherwise 'roster any warm body' would read as safety."""
        covered = _worst(DEEP + [_p("te2", 3, "TE")])["TE"]
        self.assertGreater(covered, 10.0)

    def test_the_third_tight_end_buys_nothing(self):
        """The user's own framing: just because there is a TE slot does not mean four TEs.
        Stated as a test rather than a rule in the code, because the arithmetic is what says
        it -- and if that ever stops being true, this fails rather than the belief persisting."""
        two = _worst(DEEP + [_p("te2", 13, "TE")])["TE"]
        three = _worst(DEEP + [_p("te2", 13, "TE"), _p("te3", 12, "TE")])["TE"]
        self.assertEqual(two, three)


class SubstitutabilityIsDiscoveredNotEncodedTests(unittest.TestCase):
    """A FLEX can cover an RB hole; nothing covers a mandatory TE slot. That asymmetry is the
    reason TE depth behaves unlike RB depth, and it comes out of the assignment solve."""

    def test_a_spare_flex_eligible_body_helps_every_flex_position(self):
        before, after = _worst(DEEP), _worst(DEEP + [_p("s", 19, "RB")])
        self.assertLess(after["RB"], before["RB"])
        self.assertLess(after["WR"], before["WR"], "the FLEX slot is shared, so WR benefits too")

    def test_but_it_does_nothing_for_the_position_it_cannot_fill(self):
        before, after = _worst(DEEP), _worst(DEEP + [_p("s", 19, "RB")])
        self.assertEqual(after["TE"], before["TE"],
                         "an RB cannot start in a mandatory TE slot, so TE stays fully exposed")

    def test_a_spare_tight_end_helps_only_tight_end_and_helps_it_enormously(self):
        before, after = _worst(DEEP), _worst(DEEP + [_p("s", 13, "TE")])
        self.assertEqual(after["RB"], before["RB"])
        self.assertEqual(after["WR"], before["WR"])
        self.assertLess(after["TE"], before["TE"] / 5)


class TheFourStatesOfKnowingTests(unittest.TestCase):
    """basis is read before the numbers. They are returned in every state and only one state
    makes them evidence."""

    def test_a_roster_with_no_bench_reports_no_surplus(self):
        result = lo.depth_exposure(SHALLOW, LEAGUE)
        for position in ("QB", "RB", "WR", "TE"):
            with self.subTest(position=position):
                self.assertEqual(result[position]["basis"], lo.EXPOSURE_NO_SURPLUS)

    def test_and_in_that_state_the_number_is_just_the_players_own_value(self):
        """The measurement that turned a suspected bug into a stated domain boundary. Every
        loss costs full value because nothing can backfill -- so the number is real arithmetic
        that carries no depth information, which is exactly why it needs a label."""
        worst = _worst(SHALLOW)
        self.assertEqual(worst["QB"], 30.0)
        self.assertEqual(worst["TE"], 15.0)
        self.assertEqual(worst["RB"], 25.0)

    def test_adding_a_backup_to_a_slotless_roster_changes_nothing(self):
        """Non-vacuity for the state above: it must be the SURPLUS that matters, not the
        headcount. An eighth player fills the empty eighth slot; he does not become depth."""
        self.assertEqual(_worst(SHALLOW)["TE"],
                         _worst(SHALLOW + [_p("te2", 13, "TE")])["TE"])

    def test_a_real_bench_reports_measured(self):
        result = lo.depth_exposure(DEEP, LEAGUE)
        self.assertEqual(result["TE"]["basis"], "measured")

    def test_a_position_this_roster_does_not_start_is_vacant_not_zero(self):
        """Absence is not a value. Reporting 0.0 would rank an empty slot as safely covered --
        the most dangerous possible wrong answer here, and the same defect shape this codebase
        has already had to repair in the pricing and horizon layers."""
        no_te = [p for p in DEEP if p["id"] != "te1"]
        result = lo.depth_exposure(no_te, LEAGUE)
        self.assertEqual(result["TE"]["basis"], lo.EXPOSURE_VACANT)
        self.assertIsNone(result["TE"]["exposure"])
        self.assertIsNone(result["TE"]["worst_loss"])

    def test_a_position_the_league_does_not_field_is_not_applicable(self):
        result = lo.depth_exposure(DEEP, LEAGUE)
        for position in ("K", "DEF", "LB"):
            with self.subTest(position=position):
                self.assertEqual(result[position]["basis"], lo.EXPOSURE_NOT_APPLICABLE)
                self.assertIsNone(result[position]["exposure"])

    def test_the_three_absent_states_are_distinguishable_from_each_other(self):
        """Collapsing them would rebuild the exact defect the horizon layer already carries:
        'we cannot say' and 'there is nothing here' arriving as the same value."""
        self.assertEqual(len({lo.EXPOSURE_VACANT, lo.EXPOSURE_NOT_APPLICABLE,
                              lo.EXPOSURE_NO_SURPLUS, "measured"}), 4)


class BothAggregatesAreReportedTests(unittest.TestCase):
    """exposure and worst_loss answer different questions and the caller has to choose."""

    def test_two_starters_carry_more_total_risk_than_one(self):
        result = lo.depth_exposure(DEEP, LEAGUE)
        self.assertEqual(result["QB"]["starters"], 1)
        self.assertGreaterEqual(result["RB"]["starters"], 2)
        self.assertGreater(result["RB"]["exposure"], result["RB"]["worst_loss"],
                           "summed exposure across several starters must exceed the worst one")

    def test_a_single_starter_makes_the_two_identical(self):
        result = lo.depth_exposure(DEEP, LEAGUE)
        self.assertEqual(result["QB"]["exposure"], result["QB"]["worst_loss"])

    def test_an_empty_roster_answers_without_raising(self):
        result = lo.depth_exposure([], LEAGUE)
        self.assertEqual(result["RB"]["basis"], lo.EXPOSURE_VACANT)


class NoInventedProbabilityTests(unittest.TestCase):
    """This model carries severity only. A per-position injury rate would be an unmeasured
    constant, and one has already had to be removed from this codebase once."""

    def test_two_positions_with_identical_shape_get_identical_exposure(self):
        """If any per-position risk weighting had crept in, these would differ."""
        roster = [_p("a1", 20, "RB"), _p("a2", 10, "RB"),
                  _p("b1", 20, "WR"), _p("b2", 10, "WR")]
        league = ["RB", "WR", "BN", "BN"]
        result = lo.depth_exposure(roster, league)
        self.assertEqual(result["RB"]["worst_loss"], result["WR"]["worst_loss"])

    def test_the_module_states_no_position_specific_risk_constant(self):
        """A guard on the intent, not just today's behaviour: the moment someone adds a
        POSITION_INJURY_RATE table here, this fails and the constants contract gets read."""
        source = __import__("pathlib").Path(lo.__file__).read_text()
        for banned in ("INJURY_RATE", "POSITION_RISK", "AVAILABILITY_RATE"):
            with self.subTest(constant=banned):
                self.assertNotIn(banned, source)


if __name__ == "__main__":
    unittest.main()


class WiredIntoTeamAcquisitionValueTests(unittest.TestCase):
    """#139: the term reaches a decision, and does so under the same contract as its two
    siblings. Built after run_need_bonus_ablation established that need_bonus is a POSITIONAL
    GATE rather than a depth signal, so the two are not double-counting."""

    @classmethod
    def setUpClass(cls):
        import data_merger as dm, draft_room as dr
        from run_asset_character_measurement import OFFENSE_POSITIONS
        cls.dr = dr
        cls.league = {"roster_positions": LEAGUE, "total_rosters": 12, "settings": {"type": 2}}
        merger = dm.DataMerger()
        proj, db, pid = merger.projections, {}, 0
        for pos in OFFENSE_POSITIONS:
            sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False)
            for _, row in sub.iterrows():
                pid += 1
                parts = str(row["norm_name"]).split()
                db[str(pid)] = {"first_name": (parts[0] if parts else "").upper(),
                                "last_name": " ".join(parts[1:]).title(),
                                "position": pos, "fantasy_positions": [pos],
                                "team": row.get("team")}
        cls.merger, cls.db = merger, db
        # A deep roster: depth only becomes a measurable question once a bench exists, so an
        # empty-board fixture would exercise only the vacant branch.
        cls.picks = []
        for rnd in range(1, 13):
            board = dr.compute_draft_board(merger, db, cls.picks, my_roster_id="1",
                                           league=cls.league, mode="balanced")
            order = list(range(1, 13)) if rnd % 2 else list(range(12, 0, -1))
            for slot, row in zip(order, board[:12]):
                cls.picks.append({"player_id": row["player_id"], "roster_id": str(slot),
                                  "round": rnd})
        cls.board = dr.compute_draft_board(merger, db, cls.picks, my_roster_id="1",
                                           league=cls.league, mode="balanced")

    def test_the_term_reaches_the_board(self):
        self.assertIn("depth_exposure", self.board[0])
        self.assertIn("depth_basis", self.board[0])

    def test_it_is_actually_non_zero_somewhere(self):
        """Non-vacuity. A term wired but always 0.0 would pass every other test here and be
        exactly the write-only quantity this whole pass exists to stop creating."""
        self.assertTrue(any((row.get("depth_exposure") or 0) > 0 for row in self.board),
                        "depth_exposure is 0.0 on every row -- it is wired but inert")

    def test_the_layer_identity_holds(self):
        """team_acquisition_value is a SUM of named parts, and a reader must be able to
        reconstruct it. final_score is that sum for a balanced board."""
        for row in self.board[:30]:
            with self.subTest(player=row["name"]):
                parts = (row["universal_value"] + row["need_bonus"]
                         + row["eligibility_bonus"] + row["depth_exposure"])
                self.assertAlmostEqual(parts, row["final_score"], places=1)

    def test_only_a_measured_basis_contributes(self):
        """The other three states each return real arithmetic that carries no depth
        information. Spending one would be claiming a measurement that was not made."""
        for row in self.board:
            with self.subTest(player=row["name"], basis=row["depth_basis"]):
                if row["depth_basis"] != "measured":
                    self.assertEqual(row["depth_exposure"], 0.0)

    def test_zero_means_not_measured_and_never_this_position_is_safe(self):
        """The distinction the basis exists to carry: a vacant position is the WORST case, not
        a covered one, and it reports 0.0 because nothing was measured."""
        vacant = [r for r in self.board if r["depth_basis"] == lo.EXPOSURE_VACANT]
        if vacant:
            self.assertTrue(all(r["depth_exposure"] == 0.0 for r in vacant))

    def test_it_is_bounded_by_its_own_constant(self):
        for row in self.board:
            with self.subTest(player=row["name"]):
                self.assertLessEqual(row["depth_exposure"], self.dr.DEPTH_EXPOSURE_MAX)

    def test_it_cannot_flip_a_large_universal_value_gap(self):
        """The same invariant need_bonus and eligibility_bonus each carry. A contextual term
        that can override a real value gap has stopped being a nudge -- an uncapped
        eligibility_bonus did exactly that once, at 6.8x NEED_BONUS_MAX."""
        top, bottom = self.board[0], self.board[-1]
        spread = top["universal_value"] - bottom["universal_value"]
        self.assertGreater(spread, self.dr.DEPTH_EXPOSURE_MAX,
                           "fixture's value spread is too small to exercise this invariant")
        self.assertGreater(top["universal_value"] - (bottom["universal_value"]
                                                     + self.dr.DEPTH_EXPOSURE_MAX), 0)

    def test_the_bound_matches_the_other_roster_specific_terms(self):
        """All three answer 'how good is this player FOR THIS ROSTER'. A different magnitude
        would be inventing one the evidence does not support (#56)."""
        self.assertEqual(self.dr.DEPTH_EXPOSURE_MAX, self.dr.NEED_BONUS_MAX)

    def test_upside_mode_does_not_fabricate_the_term(self):
        """upside_score never computes it, and emitting 0.0 there would invent a measurement --
        the rule already stated for time_horizon_adj and risk_adj on that path."""
        upside = self.dr.compute_draft_board(self.merger, self.db, self.picks,
                                             my_roster_id="1", league=self.league, mode="upside")
        self.assertNotIn("depth_exposure", upside[0])
        self.assertNotIn("depth_basis", upside[0])
