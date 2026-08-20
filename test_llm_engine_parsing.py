import unittest

import llm_engine


class ParseModeratorVerdictTests(unittest.TestCase):
    def test_parses_known_fields(self):
        text = (
            "Some reasoning here.\n\n"
            "RECOMMENDATION: BUY\n"
            "CONVICTION: Majority\n"
            "REASON: Undervalued relative to production\n"
            "RISK: Age curve\n"
        )
        verdict = llm_engine.parse_moderator_verdict(text)
        self.assertEqual(verdict["recommendation"], "BUY")
        self.assertEqual(verdict["conviction"], "Majority")
        self.assertEqual(verdict["reason"], "Undervalued relative to production")
        self.assertEqual(verdict["risk"], "Age curve")
        self.assertNotIn("dissent", verdict)

    def test_fails_soft_on_plain_prose(self):
        self.assertEqual(llm_engine.parse_moderator_verdict("Just talking it through, no verdict here."), {})

    def test_ignores_bullet_and_markdown_prefixes(self):
        verdict = llm_engine.parse_moderator_verdict("- RECOMMENDATION: HOLD\n* CONVICTION: Split\n# REASON: mixed signals")
        self.assertEqual(verdict["recommendation"], "HOLD")
        self.assertEqual(verdict["conviction"], "Split")


class ParseTodoDirectivesTests(unittest.TestCase):
    def test_parses_update_and_likely_resolved(self):
        text = (
            "TODO UPDATE: 3 | Revised: target a 2027 1st instead | market shifted\n"
            "TODO LIKELY RESOLVED: 5 | trade completed per roster sync\n"
        )
        directives = llm_engine.parse_todo_directives(text)
        self.assertEqual(len(directives["updates"]), 1)
        self.assertEqual(directives["updates"][0]["id"], 3)
        self.assertEqual(directives["updates"][0]["text"], "Revised: target a 2027 1st instead")
        self.assertEqual(len(directives["likely_resolved"]), 1)
        self.assertEqual(directives["likely_resolved"][0]["id"], 5)

    def test_drops_malformed_line_without_crashing(self):
        directives = llm_engine.parse_todo_directives("TODO UPDATE: not-a-number | text | reason")
        self.assertEqual(directives["updates"], [])

    def test_no_directives_returns_empty_lists(self):
        directives = llm_engine.parse_todo_directives("Nothing to see here.")
        self.assertEqual(directives, {"updates": [], "likely_resolved": []})


class ParseSourceFindingsTests(unittest.TestCase):
    def test_parses_finding_with_rank(self):
        text = "SOURCE FINDING: Maxx Crosby | ESPN | ranked #1 dynasty-relevant DL | 1"
        findings = llm_engine.parse_source_findings(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0], {
            "player_name": "Maxx Crosby", "source": "ESPN",
            "claim": "ranked #1 dynasty-relevant DL", "rank": 1,
        })

    def test_parses_finding_without_rank(self):
        text = "SOURCE FINDING: Maxx Crosby | ESPN | trending up lately |"
        findings = llm_engine.parse_source_findings(text)
        self.assertEqual(findings[0]["rank"], None)

    def test_non_numeric_rank_field_treated_as_no_number(self):
        text = "SOURCE FINDING: Player | Source | some claim | not-a-number"
        findings = llm_engine.parse_source_findings(text)
        self.assertIsNone(findings[0]["rank"])

    def test_multiple_findings_all_parsed(self):
        text = (
            "SOURCE FINDING: A | ESPN | claim one | 1\n"
            "SOURCE FINDING: B | FantasyPros | claim two | 2\n"
        )
        findings = llm_engine.parse_source_findings(text)
        self.assertEqual(len(findings), 2)

    def test_missing_required_fields_dropped(self):
        text = "SOURCE FINDING:  | ESPN | claim |"
        self.assertEqual(llm_engine.parse_source_findings(text), [])

    def test_no_findings_returns_empty_list(self):
        self.assertEqual(llm_engine.parse_source_findings("Just a normal verdict, no findings."), [])


class ParseSourceComparisonsTests(unittest.TestCase):
    def test_parses_valid_comparison(self):
        text = "SOURCE COMPARISON: Maxx Crosby | Aidan Hutchinson | > | ESPN | IDP/DL | ranked ahead in every ballot"
        comparisons = llm_engine.parse_source_comparisons(text)
        self.assertEqual(len(comparisons), 1)
        self.assertEqual(comparisons[0], {
            "subject": "Maxx Crosby", "compared_to": "Aidan Hutchinson", "direction": ">",
            "source": "ESPN", "context": "IDP/DL", "evidence": "ranked ahead in every ballot",
        })

    def test_all_three_directions_accepted(self):
        for direction in (">", "<", "~"):
            text = f"SOURCE COMPARISON: A | B | {direction} | ESPN | ctx | evidence"
            comparisons = llm_engine.parse_source_comparisons(text)
            self.assertEqual(len(comparisons), 1, direction)
            self.assertEqual(comparisons[0]["direction"], direction)

    def test_invalid_direction_token_dropped(self):
        text = "SOURCE COMPARISON: A | B | ? | ESPN | ctx | evidence"
        self.assertEqual(llm_engine.parse_source_comparisons(text), [])

    def test_missing_pipe_fields_dropped(self):
        text = "SOURCE COMPARISON: A | B | >"
        self.assertEqual(llm_engine.parse_source_comparisons(text), [])

    def test_no_comparisons_returns_empty_list(self):
        self.assertEqual(llm_engine.parse_source_comparisons("Nothing relative here."), [])


if __name__ == "__main__":
    unittest.main()
