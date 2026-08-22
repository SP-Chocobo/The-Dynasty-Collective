"""
Covers pick_debate.py's real contract: the LLM roles run in the right order with the right
context, the structured verdict block parses correctly (including the repeatable DISAGREE
lines), and -- the hard architectural requirement this module exists to enforce -- the
recommendation the app actually displays is always looked up from the snapshot's own real
numbers, never parsed out of the LLM's own prose, even when that prose is wrong.
"""

import unittest

import pick_debate as pd
from pick_synthesis import CandidateSnapshot, PickSnapshot


def _candidate(player_id, name, position="QB", universal_value=90.0, team_acquisition_value=100.0,
                survival_probability=0.5, positional_cliff=None, position_run_detected=False,
                pick_necessity=75.0, necessity_label="PREFERRED", near_tie_with_leader=False,
                consensus_rank=None, consensus_tier=None, reach_label=None, projected_points=None):
    return CandidateSnapshot(
        player_id=player_id, name=name, position=position, team="SF",
        bpa=universal_value, bpa_source="points_vor_draftsharks", confidence=80.0,
        universal_value=universal_value, need_bonus=6.0, eligibility_bonus=4.0,
        team_acquisition_value=team_acquisition_value,
        survival_probability=survival_probability, intervening_picks=2,
        opportunity_cost=round(universal_value * (1 - survival_probability), 2),
        expected_value_of_waiting=round(universal_value * survival_probability, 2),
        denial_value=30.0, denial_team="4", rival_premium=6.0,
        positional_forfeit=None, position_expected_taken=None,
        positional_cliff=positional_cliff,
        position_run_detected=position_run_detected,
        pick_necessity=pick_necessity, necessity_label=necessity_label,
        near_tie_with_leader=near_tie_with_leader,
        consensus_rank=consensus_rank, consensus_tier=consensus_tier, reach_label=reach_label,
        projected_points=projected_points,
    )


def _snapshot(candidates, user_selected_player_id=None):
    return PickSnapshot(
        pick_label="3.07", round=3, my_roster_id="1", candidates=tuple(candidates),
        user_selected_player_id=user_selected_player_id,
    )


class FormatSnapshotForLLMTests(unittest.TestCase):
    def test_includes_every_candidates_real_numbers(self):
        snap = _snapshot([_candidate("1", "Brock Purdy")])
        text = pd.format_snapshot_for_llm(snap)
        self.assertIn("Brock Purdy", text)
        self.assertIn("Universal value: 90.0", text)
        self.assertIn("Team acquisition value: 100.0", text)
        self.assertIn("Survival probability to your next pick: 50%", text)

    def test_flags_the_user_selected_player(self):
        snap = _snapshot([_candidate("1", "Brock Purdy"), _candidate("2", "Backup Guy")], user_selected_player_id="2")
        text = pd.format_snapshot_for_llm(snap)
        self.assertIn("Backup Guy", text.split("USER-FLAGGED")[0].split("CANDIDATE:")[-1])
        purdy_block = text.split("Brock Purdy")[1].split("CANDIDATE:")[0]
        self.assertNotIn("USER-FLAGGED", purdy_block)

    def test_includes_a_positional_cliff_line_when_present(self):
        snap = _snapshot([_candidate("1", "Brock Purdy", positional_cliff={"tier": "HIGH", "gap": 8.49, "typical_gap": 2.36})])
        text = pd.format_snapshot_for_llm(snap)
        self.assertIn("Positional cliff: HIGH", text)

    def test_includes_a_run_detected_line_when_flagged(self):
        snap = _snapshot([_candidate("1", "Brock Purdy", position_run_detected=True)])
        text = pd.format_snapshot_for_llm(snap)
        self.assertIn("QB run currently detected", text)

    def test_omits_the_run_line_when_not_flagged(self):
        snap = _snapshot([_candidate("1", "Brock Purdy", position_run_detected=False)])
        text = pd.format_snapshot_for_llm(snap)
        self.assertNotIn("run currently detected", text)

    def test_includes_a_what_changed_section_when_diffs_are_given(self):
        snap = _snapshot([_candidate("1", "Brock Purdy")])
        diffs = [{"player_id": "1", "name": "Brock Purdy", "entered": None, "rank_delta": -5, "deltas": {"survival_probability": -0.2}}]
        text = pd.format_snapshot_for_llm(snap, diffs)
        self.assertIn("WHAT CHANGED", text)
        self.assertIn("rank moved by -5", text)


class ParseCallerVerdictTests(unittest.TestCase):
    def test_parses_every_standard_field(self):
        text = (
            "Some reasoning here.\n\n"
            "RECOMMENDATION: Brock Purdy\n"
            "CONFIDENCE: Lean\n"
            "WHY: He's the last QB before a real cliff.\n"
            "DISSENT: The WR alternative has higher survival odds.\n"
            "KEY FACTOR: 19% survival with a QB run detected.\n"
        )
        verdict = pd.parse_caller_verdict(text)
        self.assertEqual(verdict["recommendation"], "Brock Purdy")
        self.assertEqual(verdict["confidence"], "Lean")
        self.assertEqual(verdict["why"], "He's the last QB before a real cliff.")
        self.assertEqual(verdict["dissent"], "The WR alternative has higher survival odds.")
        self.assertEqual(verdict["key_factor"], "19% survival with a QB run detected.")
        self.assertEqual(verdict["disagreements"], [])

    def test_parses_repeatable_disagree_lines(self):
        text = (
            "RECOMMENDATION: Brock Purdy\n"
            "DISAGREE: survival_probability for Player X | The run signal looks like noise, not a real pattern.\n"
            "DISAGREE: positional_cliff for Player Y | This gap looks like a scoring quirk, not a real tier break.\n"
        )
        verdict = pd.parse_caller_verdict(text)
        self.assertEqual(len(verdict["disagreements"]), 2)
        self.assertEqual(verdict["disagreements"][0]["term"], "survival_probability for Player X")

    def test_fails_soft_on_missing_or_malformed_fields(self):
        verdict = pd.parse_caller_verdict("Just some free-text reasoning with no structured block at all.")
        self.assertNotIn("recommendation", verdict)
        self.assertEqual(verdict["disagreements"], [])
        malformed = pd.parse_caller_verdict("DISAGREE: only one part, no pipe\n")
        self.assertEqual(malformed["disagreements"], [])


class MatchCandidateTests(unittest.TestCase):
    def setUp(self):
        self.snap = _snapshot([_candidate("1", "Brock Purdy"), _candidate("2", "Justin Fields")])

    def test_exact_match(self):
        self.assertEqual(pd._match_candidate(self.snap, "Brock Purdy").player_id, "1")

    def test_case_insensitive_and_substring_match(self):
        self.assertEqual(pd._match_candidate(self.snap, "brock purdy").player_id, "1")
        self.assertEqual(pd._match_candidate(self.snap, "Purdy").player_id, "1")

    def test_no_match_returns_none_rather_than_guessing(self):
        self.assertIsNone(pd._match_candidate(self.snap, "Someone Not In The Snapshot"))

    def test_empty_recommendation_returns_none(self):
        self.assertIsNone(pd._match_candidate(self.snap, None))
        self.assertIsNone(pd._match_candidate(self.snap, ""))


class BestAlternativeTests(unittest.TestCase):
    def test_picks_the_highest_acquisition_value_candidate_other_than_the_recommended_one(self):
        snap = _snapshot([
            _candidate("1", "Brock Purdy", team_acquisition_value=104.0),
            _candidate("2", "Best Alt", team_acquisition_value=95.0),
            _candidate("3", "Worse Alt", team_acquisition_value=80.0),
        ])
        recommended = snap.candidates[0]
        alt = pd._best_alternative(snap, recommended)
        self.assertEqual(alt.player_id, "2")

    def test_none_when_no_other_candidate_exists(self):
        snap = _snapshot([_candidate("1", "Brock Purdy")])
        self.assertIsNone(pd._best_alternative(snap, snap.candidates[0]))

    def test_falls_back_to_the_top_candidate_when_nothing_was_recommended(self):
        snap = _snapshot([_candidate("1", "Brock Purdy", team_acquisition_value=104.0), _candidate("2", "Backup", team_acquisition_value=95.0)])
        alt = pd._best_alternative(snap, None)
        self.assertEqual(alt.player_id, "1")


class DebatePickOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self._orig_callers = dict(pd.PROVIDER_CALLERS)
        self.addCleanup(lambda: pd.PROVIDER_CALLERS.update(self._orig_callers))

    def test_skeptic_sees_the_strategists_report_and_caller_sees_both(self):
        def _caller(system_prompt, user_prompt, api_key, model):
            if system_prompt == pd.STRATEGIST_SYSTEM_PROMPT:
                return "STRATEGIST_MARKER"
            if system_prompt == pd.SKEPTIC_SYSTEM_PROMPT:
                return "SKEPTIC_MARKER" if "STRATEGIST_MARKER" in user_prompt else "MISSING STRATEGIST REPORT"
            if system_prompt == pd.CALLER_SYSTEM_PROMPT:
                saw_both = "STRATEGIST_MARKER" in user_prompt and "SKEPTIC_MARKER" in user_prompt
                return "RECOMMENDATION: Brock Purdy\nCONFIDENCE: Unanimous\n" if saw_both else "MISSING A REPORT"
            return "unexpected role"

        pd.PROVIDER_CALLERS.update({"claude": _caller, "gemini": _caller, "openai": _caller})
        snap = _snapshot([_candidate("1", "Brock Purdy")])
        result = pd.debate_pick(snap, api_keys={"claude": "x", "openai": "x", "gemini": "x"})

        self.assertEqual(result.strategist_report, "STRATEGIST_MARKER")
        self.assertEqual(result.skeptic_report, "SKEPTIC_MARKER")
        self.assertEqual(result.confidence, "Unanimous")

    def test_the_recommended_candidates_numbers_come_from_the_real_snapshot_not_llm_text(self):
        # The hard architectural guarantee: even if the Caller's own prose stated a wrong
        # number for Purdy, the returned `recommended` object must still carry the SNAPSHOT's
        # real universal_value (90.0), never anything invented in the model's own text.
        def _caller(system_prompt, user_prompt, api_key, model):
            if system_prompt == pd.CALLER_SYSTEM_PROMPT:
                return (
                    "Purdy's universal value is actually 250 in my opinion.\n"
                    "RECOMMENDATION: Brock Purdy\nCONFIDENCE: Split\n"
                )
            return "some report"

        pd.PROVIDER_CALLERS.update({"claude": _caller, "gemini": _caller, "openai": _caller})
        snap = _snapshot([_candidate("1", "Brock Purdy", universal_value=90.0)])
        result = pd.debate_pick(snap, api_keys={"claude": "x", "openai": "x", "gemini": "x"})

        self.assertEqual(result.recommended_player_id, "1")
        self.assertEqual(result.recommended.universal_value, 90.0)

    def test_errors_are_collected_when_a_role_fails(self):
        def _caller(system_prompt, user_prompt, api_key, model):
            if system_prompt == pd.STRATEGIST_SYSTEM_PROMPT:
                return "⚠️ Claude request failed: boom"
            return "fine"

        pd.PROVIDER_CALLERS.update({"claude": _caller, "gemini": _caller, "openai": _caller})
        snap = _snapshot([_candidate("1", "Brock Purdy")])
        result = pd.debate_pick(snap, api_keys={"claude": "x", "openai": "x", "gemini": "x"})
        self.assertTrue(any("strategist" in e for e in result.errors))

    def test_diff_against_a_previous_snapshot_is_included_in_the_evidence(self):
        seen_prompts = []

        def _caller(system_prompt, user_prompt, api_key, model):
            seen_prompts.append(user_prompt)
            if system_prompt == pd.CALLER_SYSTEM_PROMPT:
                return "RECOMMENDATION: Brock Purdy\nCONFIDENCE: Unanimous\n"
            return "report"

        pd.PROVIDER_CALLERS.update({"claude": _caller, "gemini": _caller, "openai": _caller})
        before = _snapshot([_candidate("1", "Brock Purdy", survival_probability=0.8)])
        after = _snapshot([_candidate("1", "Brock Purdy", survival_probability=0.2)])
        result = pd.debate_pick(after, previous_snapshot=before, api_keys={"claude": "x", "openai": "x", "gemini": "x"})

        self.assertTrue(result.diff, "expected a real delta between the two survival probabilities")
        self.assertIn("WHAT CHANGED", seen_prompts[0])


if __name__ == "__main__":
    unittest.main()
