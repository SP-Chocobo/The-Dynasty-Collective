"""roster_diagnostics must stay decomposable -- these tests pin that every field traces to an
existing mechanism (lineup_optimizer, depth_ratings, draft_room.replacement_levels), that it
never invents a single power score, and that it doesn't mutate its inputs.
"""

import copy
import unittest
from pathlib import Path

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
import run_draft_battery
from draft_simulation import simulate_full_draft
from roster_diagnostics import TeamDiagnostics, compute_team_diagnostics, coverage_statement


def _build_pool_players_db(positions=("QB", "RB", "WR", "TE")):
    merger = dm.DataMerger()
    proj = merger.projections
    players_db = {}
    pid = 0
    for pos in positions:
        sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False)
        for _, row in sub.iterrows():
            pid += 1
            parts = row["norm_name"].split()
            players_db[str(pid)] = {
                "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
            }
    return merger, players_db


class ComputeTeamDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        cls.league = dr.build_mock_league(teams=4, superflex=False, scoring="ppr", te_premium=False, dynasty=True)
        pick_order = ds.generate_pick_order(["1", "2", "3", "4"], total_rounds=3)  # 12 picks
        cls.trajectory = simulate_full_draft(cls.merger, cls.players_db, cls.league, pick_order)
        cls.league_before = {k: (v.copy() if isinstance(v, (list, dict)) else v) for k, v in cls.league.items()}
        cls.players_db_before = {k: dict(v) for k, v in cls.players_db.items()}
        cls.diagnostics = compute_team_diagnostics(cls.merger, cls.players_db, cls.league, cls.trajectory)

    def test_one_diagnostics_entry_per_team(self):
        self.assertEqual(set(self.diagnostics), {"1", "2", "3", "4"})

    def test_accumulated_value_is_the_plain_sum_of_uv(self):
        rid = "1"
        expected = round(sum(
            next(c for c in rec.snapshot["candidates"] if c["id"] == rec.chosen_player_id)["uv"]
            for rec in self.trajectory.picks if rec.roster_id == rid
        ), 2)
        self.assertAlmostEqual(self.diagnostics[rid].accumulated_value, expected, places=1)

    def test_starting_lineup_value_never_exceeds_accumulated_value(self):
        # A team can never start more value than it actually rostered -- the optimizer can only
        # select a subset (bounded by real slot counts), never invent extra value.
        for d in self.diagnostics.values():
            self.assertLessEqual(d.starting_lineup_value, d.accumulated_value + 1e-6)

    def test_bench_surplus_is_accumulated_minus_starting(self):
        for d in self.diagnostics.values():
            self.assertAlmostEqual(d.bench_surplus_value, round(d.accumulated_value - d.starting_lineup_value, 2), places=1)
            self.assertGreaterEqual(d.bench_surplus_value, -1e-6)

    def test_positional_counts_sum_to_total_picks_per_team(self):
        for rid, d in self.diagnostics.items():
            team_picks = sum(1 for rec in self.trajectory.picks if rec.roster_id == rid)
            self.assertEqual(sum(d.positional_counts.values()), team_picks)

    def test_thin_positions_only_named_from_positions_actually_rostered(self):
        for d in self.diagnostics.values():
            for pos in d.thin_positions:
                self.assertIn(pos, d.positional_counts)

    def test_structural_holes_are_usable_positions_with_zero_players(self):
        for d in self.diagnostics.values():
            for pos in d.structural_holes:
                self.assertNotIn(pos, d.positional_counts)

    def test_no_single_aggregate_power_score_field_exists(self):
        # The hard contract: every field is a named, decomposable measurement -- there must be
        # no field that reads as one rolled-up "team strength" number.
        fields = TeamDiagnostics.__dataclass_fields__.keys()
        for banned in ("power_score", "strength_score", "team_score", "overall_score", "rating"):
            self.assertNotIn(banned, fields)

    def test_does_not_mutate_league_or_players_db(self):
        self.assertEqual(self.league, self.league_before)
        self.assertEqual(self.players_db, self.players_db_before)



class AnUnpricedPickDoesNotKillTheInstrumentTests(unittest.TestCase):
    """#165. `uv` is Optional -- None exactly when the position had no replacement level, a
    state the engine is CONTRACTUALLY REQUIRED to produce -- and three sites summed it
    unguarded, so one unpriced pick anywhere in a trajectory raised TypeError and took the
    whole diagnostic down.

    That matters more than "harness-only" suggests: app.py never imports this module, but the
    BATTERY does, and the battery is the instrument behind #150. It died on precisely the
    regime it most needed to measure. Read with #161, that is two independent blind spots in
    the same harness, both found from outside it.

    WHAT THIS FIXTURE DOES AND DOES NOT PROVE. It blanks one candidate's `uv` WITHOUT also
    removing that position from the replacement levels, because that is the cheap way to reach
    the summing code. In production the two co-occur -- uv is None exactly when bpa is, which
    is exactly when the position has no replacement level -- so for the three unguarded sums
    this reproduces a REACHABLE crash, while for `replacement_level_surplus` (whose filter
    already excluded positions with no level) it pins ROBUSTNESS against a coincidence rather
    than a reachable production failure. Writing that down because the distinction is exactly
    the kind this register exists to keep straight, and because the surplus guard was added
    only after this test caught it."""

    @classmethod
    def setUpClass(cls):
        merger, players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        league = dr.build_mock_league(teams=4, superflex=False, scoring="ppr",
                                      te_premium=False, dynasty=True)
        order = ds.generate_pick_order(["1", "2", "3", "4"], total_rounds=3)
        cls.merger, cls.players_db, cls.league = merger, players_db, league
        cls.clean = simulate_full_draft(merger, players_db, league, order)
        cls.baseline = compute_team_diagnostics(merger, players_db, league, cls.clean)

        # Blank ONE chosen candidate's uv, exactly as an unpriced position produces.
        cls.holed = copy.deepcopy(cls.clean)
        rec = cls.holed.picks[0]
        cls.holed_team = rec.roster_id
        for c in rec.snapshot["candidates"]:
            if c["id"] == rec.chosen_player_id:
                cls.removed_uv = c["uv"]
                c["uv"] = None
        cls.result = compute_team_diagnostics(merger, players_db, league, cls.holed)

    def test_it_returns_instead_of_raising(self):
        # The whole point: before the repair this raised TypeError on the first `+=`.
        self.assertEqual(set(self.result), {"1", "2", "3", "4"})

    def test_the_unpriced_player_is_counted_not_silently_absorbed(self):
        self.assertEqual(self.result[self.holed_team].unpriced_players, 1)
        for other in set(self.result) - {self.holed_team}:
            self.assertEqual(self.result[other].unpriced_players, 0)

    def test_his_value_is_excluded_rather_than_treated_as_zero(self):
        """Excluding and coercing-to-zero produce the SAME accumulated_value, so that number
        alone cannot tell them apart -- which is exactly why the count above has to exist. What
        this pins is that the value really did drop by his uv, so nothing invented a price."""
        self.assertIsNotNone(self.removed_uv)
        self.assertAlmostEqual(
            self.result[self.holed_team].accumulated_value,
            round(self.baseline[self.holed_team].accumulated_value - self.removed_uv, 2),
            places=2)

    def test_the_roster_still_says_it_holds_him(self):
        # count includes him, value does not: the roster really does hold the player, so a
        # depth cell must not pretend he is absent.
        self.assertEqual(sum(self.result[self.holed_team].positional_counts.values()),
                         sum(self.baseline[self.holed_team].positional_counts.values()))

    def test_every_other_team_is_untouched(self):
        for other in set(self.result) - {self.holed_team}:
            self.assertEqual(self.result[other].accumulated_value,
                             self.baseline[other].accumulated_value)

    def test_the_statement_calls_the_holed_teams_value_a_floor_and_the_others_totals(self):
        # The comment at the lineup solve has said "a FLOOR, not a total" since #165; this is
        # the first time a reader can see it beside the number.
        holed = self.result[self.holed_team]
        statement = holed.starting_lineup_statement()
        self.assertIn(f"{holed.starting_lineup_value:.2f}", statement)
        self.assertIn("1 player unpriced", statement)
        self.assertIn("floor", statement)
        for other in set(self.result) - {self.holed_team}:
            with self.subTest(roster=other):
                clean = self.result[other].starting_lineup_statement()
                self.assertIn(f"{self.result[other].starting_lineup_value:.2f}", clean)
                self.assertIn("total", clean)
                self.assertNotIn("floor", clean)


class TheNumberStatesItsOwnCoverageTests(unittest.TestCase):
    """coverage_statement is the one phrasing every surface that shows a roster value uses, and
    the absence contract is absolute in it: a count nobody measured is words, never 0, never a
    dash, never blank -- and never the same words as a measured zero. Those are two different
    facts about the world, and a reader must not be able to confuse them."""

    def test_an_unmeasured_count_is_words_with_no_digit_in_them(self):
        text = coverage_statement(None)
        self.assertIn("not measured", text)
        self.assertNotRegex(text, r"\d")
        self.assertNotIn("—", text)
        self.assertNotEqual(text.strip(), "")

    def test_a_measured_zero_and_an_unmeasured_count_never_read_the_same(self):
        self.assertNotEqual(coverage_statement(0), coverage_statement(None))
        self.assertIn("total", coverage_statement(0))
        self.assertNotIn("floor", coverage_statement(0))
        self.assertNotIn("not measured", coverage_statement(0))

    def test_a_positive_count_names_itself_and_calls_the_values_floors(self):
        self.assertIn("2 players unpriced", coverage_statement(2))
        self.assertIn("floor", coverage_statement(2))
        self.assertNotIn("total", coverage_statement(2).replace("not totals", ""))
        self.assertIn("1 player unpriced", coverage_statement(1))


class TheBatteryRunnerStatesCoverageTests(unittest.TestCase):
    """run_draft_battery's per-format line is the one place roster strength reaches a person,
    and until 2026-09-06 it printed the starter-value range with nothing beside it -- while
    draft_battery.roster_strength had been carrying a per-roster unpriced_players count into the
    JSON that no line ever read out. strength_coverage is that read-out, and it has three
    absences to keep apart from a zero, not one."""

    def test_no_strength_at_all_is_its_own_sentence_never_none_or_zero(self):
        text = run_draft_battery.strength_coverage(None)
        self.assertIn("not measured", text)
        self.assertNotIn("None", text)
        self.assertNotRegex(text, r"\d")

    def test_a_roster_with_no_count_is_unmeasured_not_zero(self):
        text = run_draft_battery.strength_coverage({"per_roster": {"1": {"starter_value": 1.0}}})
        self.assertEqual(text, coverage_statement(None))

    def test_counts_are_summed_across_rosters_and_a_zero_sum_says_totals(self):
        """Substring rather than equality since #170: the sentence now names the ruler it was
        measured against. coverage_statement is still the ONE place the phrasing is written,
        which is what this pins -- the reference is asserted separately below."""
        floors = run_draft_battery.strength_coverage(
            {"per_roster": {"1": {"unpriced_players": 2}, "2": {"unpriced_players": 1}}})
        self.assertIn(coverage_statement(3), floors)
        totals = run_draft_battery.strength_coverage(
            {"per_roster": {"1": {"unpriced_players": 0}, "2": {"unpriced_players": 0}}})
        self.assertIn(coverage_statement(0), totals)

    def test_the_coverage_sentence_names_the_ruler_it_was_measured_against(self):
        """#170. The count behind this sentence is 0 by construction -- reference_values prices
        against the PRE-DRAFT board, and every drafted player is on it -- so unqualified it
        reads as a claim about the engine and is a property of the ruler's timing. I misread it
        that way in the register on the day it was written."""
        text = run_draft_battery.strength_coverage(
            {"per_roster": {"1": {"unpriced_players": 0}}})
        self.assertEqual(
            text, f"{run_draft_battery.PREDRAFT_RULER}: {coverage_statement(0)}",
            "the reference leads and the shared phrasing follows it, unchanged",
        )
        floors = run_draft_battery.strength_coverage(
            {"per_roster": {"1": {"unpriced_players": 4}}})
        self.assertEqual(
            floors, f"{run_draft_battery.PREDRAFT_RULER}: {coverage_statement(4)}")

    def test_the_pick_time_clause_is_a_separate_sentence_from_the_predraft_one(self):
        """The two coverage numbers have different references, and merging them is how the
        first one came to be misread. Absence keeps its own sentence in the new clause too."""
        unmeasured = run_draft_battery.decision_coverage(None)
        nothing_to_measure = run_draft_battery.decision_coverage({"picks_examined": 0})
        self.assertIn("not measured", unmeasured)
        self.assertIn("measurable", nothing_to_measure)
        self.assertNotEqual(
            unmeasured, nothing_to_measure,
            "a record that never carried this block and a draft with no candidate sets are "
            "different absences and must not collapse into one sentence",
        )
        for text in (unmeasured, nothing_to_measure):
            self.assertNotIn("0 of", text, "absence must never be reported as a rate of zero")
        clean = run_draft_battery.decision_coverage(
            {"picks_examined": 168, "picks_with_an_unpriced_candidate": 0,
             "picks_that_took_an_unpriced_candidate": 0})
        self.assertEqual(clean, "no unpriced candidate reached any of the 168 decisions")
        hit = run_draft_battery.decision_coverage(
            {"picks_examined": 168, "picks_with_an_unpriced_candidate": 12,
             "picks_that_took_an_unpriced_candidate": 3})
        self.assertEqual(
            hit, "an unpriced candidate reached 12 of 168 decisions and won 3",
            "both halves are stated: contending and winning are different facts",
        )
        self.assertNotEqual(clean, hit)

    def test_nobody_to_price_is_not_the_same_as_unmeasured(self):
        empty = run_draft_battery.strength_coverage({"per_roster": {}})
        self.assertNotEqual(empty, coverage_statement(None))
        self.assertNotEqual(empty, coverage_statement(0))
        self.assertNotRegex(empty, r"\d")

    def test_the_printed_line_reads_the_raw_strength_through_it(self):
        # The runner coerces a None strength to {} for its min/max reads; the coverage clause
        # must see the raw value or the None-vs-empty distinction above is lost before it starts.
        source = Path(run_draft_battery.__file__).read_text()
        self.assertIn("strength_coverage(audited.get('strength'))", source)


if __name__ == "__main__":
    unittest.main()
