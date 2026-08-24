"""screen_context is a pure assembly layer -- these tests pin that every field is a direct
reshaping of already-computed arguments, and that to_prompt_seed never drops or reorders the
evidence a surface handed over."""

import unittest

from pick_synthesis import CandidateSnapshot, PickSnapshot
from screen_context import (
    DRAFT_ROOM_PICK_DEBATE_HELP, UNIVERSAL_DEBATE_HELP,
    ScreenContext, build_draft_room_context, build_free_agents_context, build_league_context,
    build_matchup_context, build_trade_context,
)


def _candidate(**overrides) -> CandidateSnapshot:
    base = dict(
        player_id="123", name="J. Gibbs", position="RB", team="DET",
        bpa=88.5, bpa_source="points_vor_draftsharks", confidence=80.0,
        universal_value=88.5, need_bonus=6.0, eligibility_bonus=2.9,
        team_acquisition_value=97.4, survival_probability=0.31, intervening_picks=11,
        opportunity_cost=67.2, expected_value_of_waiting=27.4,
        denial_value=8.4, denial_team="Roster 9", rival_premium=8.4,
        positional_forfeit=77.9, position_expected_taken=2.4,
        positional_cliff={"tier": "HIGH", "gap": 22.4, "typical_gap": 6.1},
        position_run_detected=False, pick_necessity=88.0, necessity_label="STRONG ACTION",
        near_tie_with_leader=True, cliff_protection=True, block_opportunity=True,
        pure_value=False, context_elevated=False,
        consensus_rank=None, consensus_tier=None, reach_label=None, projected_points=250.0,
    )
    base.update(overrides)
    return CandidateSnapshot(**base)


def _snapshot(candidates, **overrides) -> PickSnapshot:
    base = dict(
        pick_label="3.04", round=3, my_roster_id="1", candidates=tuple(candidates),
        decision_regime="contested",
    )
    base.update(overrides)
    return PickSnapshot(**base)


class ScreenContextToPromptSeedTests(unittest.TestCase):
    def test_includes_surface_looking_at_decision_and_evidence(self):
        ctx = ScreenContext(
            surface="Trade Calculator", looking_at="Evaluating a trade.",
            decision="You send: X\nYou receive: Y", evidence="Favorable.",
        )
        seed = ctx.to_prompt_seed()
        self.assertIn("Current context: Trade Calculator", seed)
        self.assertIn("Evaluating a trade.", seed)
        self.assertIn("You send: X", seed)
        self.assertIn("Favorable.", seed)

    def test_entities_are_appended_when_present(self):
        ctx = ScreenContext(
            surface="X", looking_at="l", decision="d", evidence="e",
            entities=("Ja'Marr Chase", "Bijan Robinson"),
        )
        self.assertIn("Involved: Ja'Marr Chase, Bijan Robinson", ctx.to_prompt_seed())

    def test_no_entities_produces_no_involved_line(self):
        ctx = ScreenContext(surface="X", looking_at="l", decision="d", evidence="e")
        self.assertNotIn("Involved:", ctx.to_prompt_seed())

    def test_guidance_appended_last_when_present(self):
        ctx = ScreenContext(surface="X", looking_at="l", decision="d", evidence="e", guidance="Watch the bye weeks.")
        seed = ctx.to_prompt_seed()
        self.assertIn("Watch the bye weeks.", seed)
        self.assertTrue(seed.strip().endswith("Watch the bye weeks."))

    def test_no_guidance_by_default(self):
        ctx = ScreenContext(surface="X", looking_at="l", decision="d", evidence="e")
        self.assertIsNone(ctx.guidance)


class BuildTradeContextTests(unittest.TestCase):
    def test_partner_named_when_specified(self):
        ctx = build_trade_context(
            trade_partner="Roster 9", send_description="  - Chase", receive_description="  - Bijan",
            entities=["Chase", "Bijan"], raw_line=None, fit_line=None, overall=None,
        )
        self.assertIn("Roster 9", ctx.looking_at)

    def test_not_specified_partner_omitted_from_looking_at(self):
        ctx = build_trade_context(
            trade_partner="Not specified", send_description="x", receive_description="y",
            entities=[], raw_line=None, fit_line=None, overall=None,
        )
        self.assertNotIn("Not specified", ctx.looking_at)

    def test_send_and_receive_descriptions_pass_through_unmodified(self):
        ctx = build_trade_context(
            trade_partner="Not specified",
            send_description="  - Ja'Marr Chase (value: 92)",
            receive_description="  - Bijan Robinson (value: 88)",
            entities=[], raw_line=None, fit_line=None, overall=None,
        )
        self.assertIn("Ja'Marr Chase (value: 92)", ctx.decision)
        self.assertIn("Bijan Robinson (value: 88)", ctx.decision)

    def test_empty_side_reads_as_nothing_added_yet_not_blank(self):
        ctx = build_trade_context(
            trade_partner="Not specified", send_description="", receive_description="",
            entities=[], raw_line=None, fit_line=None, overall=None,
        )
        self.assertIn("nothing added yet", ctx.decision)

    def test_all_three_verdict_lines_included_when_present(self):
        ctx = build_trade_context(
            trade_partner="Not specified", send_description="x", receive_description="y", entities=[],
            raw_line="Raw: favorable", fit_line="Fit: neutral", overall="Overall: depends",
        )
        self.assertIn("Raw: favorable", ctx.evidence)
        self.assertIn("Fit: neutral", ctx.evidence)
        self.assertIn("Overall: depends", ctx.evidence)

    def test_no_verdicts_reads_as_no_priced_assets_yet(self):
        ctx = build_trade_context(
            trade_partner="Not specified", send_description="", receive_description="",
            entities=[], raw_line=None, fit_line=None, overall=None,
        )
        self.assertIn("No priced assets to compare yet", ctx.evidence)

    def test_entities_pass_through_as_a_tuple(self):
        ctx = build_trade_context(
            trade_partner="Not specified", send_description="x", receive_description="y",
            entities=["A", "B", "C"], raw_line=None, fit_line=None, overall=None,
        )
        self.assertEqual(ctx.entities, ("A", "B", "C"))

    def test_surface_is_always_trade_calculator(self):
        ctx = build_trade_context(
            trade_partner="Not specified", send_description="x", receive_description="y",
            entities=[], raw_line=None, fit_line=None, overall=None,
        )
        self.assertEqual(ctx.surface, "Trade Calculator")

    def test_full_round_trip_reads_naturally_through_to_prompt_seed(self):
        ctx = build_trade_context(
            trade_partner="Roster 9", send_description="  - Ja'Marr Chase (value: 92)",
            receive_description="  - Bijan Robinson (value: 88)\n  - Puka Nacua (value: 79)",
            entities=["Ja'Marr Chase", "Bijan Robinson", "Puka Nacua"],
            raw_line="🟢 Materially favorable — you'd be receiving 45% more value.",
            fit_line="⚪ Roughly neutral — no meaningful shift in positional depth either way.",
            overall="↔️ Depends on your objective — Raw Value and Roster Fit point in different directions.",
        )
        seed = ctx.to_prompt_seed()
        self.assertIn("Current context: Trade Calculator", seed)
        self.assertIn("Roster 9", seed)
        self.assertIn("Ja'Marr Chase (value: 92)", seed)
        self.assertIn("Materially favorable", seed)
        self.assertIn("Depends on your objective", seed)
        self.assertIn("Involved: Ja'Marr Chase, Bijan Robinson, Puka Nacua", seed)


class BuildDraftRoomContextTests(unittest.TestCase):
    def test_surface_is_always_draft_room(self):
        ctx = build_draft_room_context(_snapshot([_candidate()]))
        self.assertEqual(ctx.surface, "Draft Room")

    def test_looking_at_names_the_pick_label(self):
        ctx = build_draft_room_context(_snapshot([_candidate()], pick_label="1.07"))
        self.assertIn("1.07", ctx.looking_at)

    def test_decision_names_the_regime(self):
        ctx = build_draft_room_context(_snapshot([_candidate()], decision_regime="decisive"))
        self.assertIn("decisive", ctx.decision)

    def test_evidence_reflects_real_candidate_fields_unmodified(self):
        c = _candidate(name="Ja'Marr Chase", position="WR", team_acquisition_value=97.4, necessity_label="MUST TAKE")
        ctx = build_draft_room_context(_snapshot([c]))
        self.assertIn("Ja'Marr Chase (WR)", ctx.evidence)
        self.assertIn("MUST TAKE", ctx.evidence)
        self.assertIn("97", ctx.evidence)

    def test_survival_probability_rendered_as_a_percent(self):
        c = _candidate(survival_probability=0.31)
        ctx = build_draft_room_context(_snapshot([c]))
        self.assertIn("31%", ctx.evidence)

    def test_missing_survival_probability_reads_as_unknown_not_a_crash(self):
        c = _candidate(survival_probability=None)
        ctx = build_draft_room_context(_snapshot([c]))
        self.assertIn("unknown", ctx.evidence)

    def test_empty_candidates_reads_as_none_available_not_blank(self):
        ctx = build_draft_room_context(_snapshot([]))
        self.assertIn("No candidates available", ctx.evidence)

    def test_candidate_list_is_capped_with_a_remainder_note(self):
        candidates = [_candidate(player_id=str(i), name=f"Player {i}") for i in range(12)]
        ctx = build_draft_room_context(_snapshot(candidates))
        self.assertIn("4 more candidate(s)", ctx.evidence)
        self.assertEqual(len(ctx.entities), 8)

    def test_never_re_sorts_the_engines_own_candidate_order(self):
        # The snapshot's own order is the engine's ranking -- this module must never
        # second-guess it, including by accident via a set/dict somewhere along the way.
        names = ["Z. Last", "A. First", "M. Middle"]
        candidates = [_candidate(player_id=str(i), name=n) for i, n in enumerate(names)]
        ctx = build_draft_room_context(_snapshot(candidates))
        self.assertEqual(ctx.entities, tuple(names))

    def test_to_prompt_seed_reads_naturally(self):
        c = _candidate(name="Ja'Marr Chase", position="WR", necessity_label="MUST TAKE", team_acquisition_value=97.4)
        ctx = build_draft_room_context(_snapshot([c], pick_label="1.07", decision_regime="decisive"))
        seed = ctx.to_prompt_seed()
        self.assertIn("Current context: Draft Room", seed)
        self.assertIn("1.07", seed)
        self.assertIn("decisive", seed)
        self.assertIn("Ja'Marr Chase", seed)


class BuildLeagueContextTests(unittest.TestCase):
    def _row(self, **overrides) -> dict:
        base = dict(
            name="Justin Jefferson", position="WR", team="MIN", slot="Starter",
            injury_status=None, sleeper_proj=18.4,
        )
        base.update(overrides)
        return base

    def test_surface_is_always_league(self):
        ctx = build_league_context("Team Rocket", [self._row()])
        self.assertEqual(ctx.surface, "League")

    def test_looking_at_names_the_team(self):
        ctx = build_league_context("Team Rocket", [self._row()])
        self.assertIn("Team Rocket", ctx.looking_at)

    def test_decision_counts_rostered_and_starting_players(self):
        rows = [self._row(name="A", slot="Starter"), self._row(name="B", slot="Bench")]
        ctx = build_league_context("X", rows)
        self.assertIn("2 rostered player(s)", ctx.decision)
        self.assertIn("1 in starting slots", ctx.decision)

    def test_evidence_reflects_real_row_fields_unmodified(self):
        row = self._row(name="Justin Jefferson", position="WR", team="MIN", sleeper_proj=18.4)
        ctx = build_league_context("X", [row])
        self.assertIn("Justin Jefferson (WR, MIN)", ctx.evidence)
        self.assertIn("18.4", ctx.evidence)

    def test_injury_status_included_when_present(self):
        row = self._row(injury_status="Questionable")
        ctx = build_league_context("X", [row])
        self.assertIn("Questionable", ctx.evidence)

    def test_no_injury_status_omits_it_cleanly(self):
        row = self._row(injury_status=None)
        ctx = build_league_context("X", [row])
        self.assertNotIn("None", ctx.evidence)

    def test_missing_slot_defaults_to_bench_in_evidence(self):
        row = self._row(slot=None)
        ctx = build_league_context("X", [row])
        self.assertIn("Bench", ctx.evidence)

    def test_empty_roster_reads_as_none_found_not_blank(self):
        ctx = build_league_context("X", [])
        self.assertIn("No rostered players found", ctx.evidence)

    def test_never_computes_a_strength_score(self):
        # The whole point of this builder: it's a roster listing, never a verdict. No field
        # should contain anything that reads as a computed strength/power number.
        ctx = build_league_context("X", [self._row(), self._row(name="B", slot="Bench")])
        for banned in ("strength", "power score", "rating", "grade"):
            self.assertNotIn(banned, ctx.evidence.lower())
            self.assertNotIn(banned, ctx.decision.lower())

    def test_entities_preserve_row_order(self):
        rows = [self._row(name="Z"), self._row(name="A"), self._row(name="M")]
        ctx = build_league_context("X", rows)
        self.assertEqual(ctx.entities, ("Z", "A", "M"))


class BuildMatchupContextTests(unittest.TestCase):
    def _row(self, **overrides) -> dict:
        base = dict(
            name="Justin Jefferson", position="WR", team="MIN", slot="Starter",
            injury_status=None, sleeper_proj=18.4, tier=1, vorp=42.0,
        )
        base.update(overrides)
        return base

    def test_surface_is_always_matchup(self):
        ctx = build_matchup_context([self._row()])
        self.assertEqual(ctx.surface, "Matchup")

    def test_decision_counts_rostered_and_starting_players(self):
        rows = [self._row(name="A", slot="Starter"), self._row(name="B", slot="Bench")]
        ctx = build_matchup_context(rows)
        self.assertIn("2 rostered player(s)", ctx.decision)
        self.assertIn("1 in starting slots", ctx.decision)

    def test_evidence_reflects_tier_vorp_and_projection_unmodified(self):
        row = self._row(tier=2, vorp=15.5, sleeper_proj=12.3)
        ctx = build_matchup_context([row])
        self.assertIn("tier 2", ctx.evidence)
        self.assertIn("VORP 15.5", ctx.evidence)
        self.assertIn("proj 12.3", ctx.evidence)

    def test_falls_back_to_projection_field_when_sleeper_proj_absent(self):
        row = self._row(sleeper_proj=None, projection=9.9)
        del row["sleeper_proj"]
        ctx = build_matchup_context([row])
        self.assertIn("proj 9.9", ctx.evidence)

    def test_missing_slot_defaults_to_bench_in_evidence(self):
        ctx = build_matchup_context([self._row(slot=None)])
        self.assertIn("Bench", ctx.evidence)

    def test_empty_roster_reads_as_none_found_not_blank(self):
        ctx = build_matchup_context([])
        self.assertIn("No rostered players found", ctx.evidence)

    def test_never_recommends_a_start_sit_decision(self):
        # This builder lists the roster -- it must never itself pick who to start.
        ctx = build_matchup_context([self._row(), self._row(name="B", slot="Bench")])
        for banned in ("start ", "sit ", "recommend"):
            self.assertNotIn(banned, ctx.evidence.lower())

    def test_entities_preserve_roster_table_order(self):
        rows = [self._row(name="Z"), self._row(name="A"), self._row(name="M")]
        ctx = build_matchup_context(rows)
        self.assertEqual(ctx.entities, ("Z", "A", "M"))

    def test_no_focus_position_is_the_default_and_unchanged(self):
        rows = [self._row(name="A", position="WR"), self._row(name="B", position="TE")]
        ctx = build_matchup_context(rows)
        self.assertEqual(ctx.entities, ("A", "B"))
        self.assertEqual(ctx.looking_at, "Looking at your roster.")

    def test_focus_position_narrows_to_that_group_only(self):
        rows = [self._row(name="A", position="WR"), self._row(name="B", position="TE")]
        ctx = build_matchup_context(rows, focus_position="TE")
        self.assertEqual(ctx.entities, ("B",))
        self.assertNotIn("A", ctx.evidence)

    def test_focus_position_names_its_lineage_in_looking_at(self):
        ctx = build_matchup_context([self._row(position="TE")], focus_position="TE")
        self.assertIn("TE", ctx.looking_at)
        self.assertIn("within your roster", ctx.looking_at)

    def test_focus_position_decision_counts_only_that_group(self):
        rows = [
            self._row(name="A", position="TE", slot="Starter"),
            self._row(name="B", position="TE", slot="Bench"),
            self._row(name="C", position="WR", slot="Starter"),
        ]
        ctx = build_matchup_context(rows, focus_position="TE")
        self.assertIn("2 rostered player(s) at TE", ctx.decision)
        self.assertIn("1 in starting slots", ctx.decision)

    def test_empty_focus_group_is_handed_over_as_itself_not_the_whole_roster(self):
        # Committed-object contract, "empty is still the object": zero players at the focused
        # position must never fall back to seeding the whole roster instead.
        rows = [self._row(name="A", position="WR")]
        ctx = build_matchup_context(rows, focus_position="TE")
        self.assertEqual(ctx.entities, ())
        self.assertIn("No rostered players in your TE group", ctx.evidence)
        self.assertNotIn("A", ctx.evidence)


class BuildFreeAgentsContextTests(unittest.TestCase):
    def _row(self, **overrides) -> dict:
        base = dict(name="Jaylen Warren", position="RB", team="PIT", injury_status=None, sleeper_proj=9.1)
        base.update(overrides)
        return base

    def test_surface_is_always_free_agents(self):
        ctx = build_free_agents_context([self._row()], None, None)
        self.assertEqual(ctx.surface, "Free Agents")

    def test_position_filter_named_in_looking_at_when_set(self):
        ctx = build_free_agents_context([self._row()], "RB", None)
        self.assertIn("position: RB", ctx.looking_at)

    def test_all_positions_filter_omitted_from_looking_at(self):
        ctx = build_free_agents_context([self._row()], "All Positions", None)
        self.assertNotIn("position:", ctx.looking_at)

    def test_search_term_named_in_looking_at_when_set(self):
        ctx = build_free_agents_context([self._row()], None, "warren")
        self.assertIn("search: 'warren'", ctx.looking_at)

    def test_blank_search_term_omitted_from_looking_at(self):
        ctx = build_free_agents_context([self._row()], None, "   ")
        self.assertNotIn("search:", ctx.looking_at)

    def test_decision_counts_total_matching_rows(self):
        rows = [self._row(name=f"Player {i}") for i in range(5)]
        ctx = build_free_agents_context(rows, None, None)
        self.assertIn("5 free agent(s)", ctx.decision)

    def test_evidence_reflects_real_row_fields_unmodified(self):
        row = self._row(name="Jaylen Warren", ds_fa_rank=4, sleeper_proj=9.1)
        ctx = build_free_agents_context([row], None, None)
        self.assertIn("Jaylen Warren (RB, PIT)", ctx.evidence)
        self.assertIn("FA rank 4", ctx.evidence)
        self.assertIn("proj 9.1", ctx.evidence)

    def test_ds_rank_used_only_when_fa_rank_absent(self):
        row = self._row(ds_rank=120)
        ctx = build_free_agents_context([row], None, None)
        self.assertIn("DS rank 120", ctx.evidence)

    def test_empty_rows_reads_as_none_match_not_blank(self):
        ctx = build_free_agents_context([], None, None)
        self.assertIn("No free agents match", ctx.evidence)

    def test_rows_beyond_the_cap_are_summarized_with_a_remainder_note(self):
        rows = [self._row(name=f"Player {i}") for i in range(12)]
        ctx = build_free_agents_context(rows, None, None)
        self.assertIn("4 more in the current filter", ctx.evidence)
        self.assertEqual(len(ctx.entities), 8)

    def test_never_re_sorts_the_callers_own_row_order(self):
        names = ["Z. Last", "A. First", "M. Middle"]
        rows = [self._row(name=n) for n in names]
        ctx = build_free_agents_context(rows, None, None)
        self.assertEqual(ctx.entities, tuple(names))


class DebateHelpTextDistinctnessTests(unittest.TestCase):
    """The two Debate-labeled controls that can share a screen (Draft Room's own "Debate This
    Pick" and the universal 💬 Debate chip) must never read as the same action -- pinned here
    so an edit that lets them converge (e.g. copy-pasting one help string into the other) is
    a failing test, not a silent regression."""

    def test_help_text_strings_are_different(self):
        self.assertNotEqual(UNIVERSAL_DEBATE_HELP, DRAFT_ROOM_PICK_DEBATE_HELP)

    def test_universal_help_promises_no_auto_submit(self):
        self.assertIn("Nothing is submitted automatically", UNIVERSAL_DEBATE_HELP)

    def test_pick_specific_help_names_its_own_dedicated_system(self):
        self.assertIn("Strategist", DRAFT_ROOM_PICK_DEBATE_HELP)
        self.assertIn("frozen snapshot", DRAFT_ROOM_PICK_DEBATE_HELP)

    def test_universal_help_never_claims_pick_specific_machinery(self):
        for banned in ("Strategist", "Skeptic", "Caller", "frozen snapshot"):
            self.assertNotIn(banned, UNIVERSAL_DEBATE_HELP)

    def test_pick_specific_help_never_repeats_the_universal_doorways_own_guarantee(self):
        # It's fine (expected, even) for this text to NAME "The Prytaneum" as a contrast --
        # what it must never do is borrow the universal chip's own "nothing submitted
        # automatically" promise, since Debate This Pick runs immediately on click.
        self.assertNotIn("Nothing is submitted automatically", DRAFT_ROOM_PICK_DEBATE_HELP)


if __name__ == "__main__":
    unittest.main()
