"""§18 — data semantics: what does the system know, and can it say which kind of not-knowing?

The one-bit absence contract (a value is present or it is not) is already implemented end to
end and defended by test_absence_survives_consumers.py: EXCLUDE / PROPAGATE / ORDER LAST, no
consumer substituting a number for absence. §18 asks the second bit -- WHICH absence -- and this
file covers the one place the codebase answers it.

  ENFORCED
    * data_merger's three horizon states survive their own producer (R16). merge_player carries
      proj_3yr_state and proj_3yr_reason, and horizon_gap_lines turns them into context the
      panel actually receives. Before R16 both states arrived at every consumer as the same
      missing key: "a team defense has no career arc to project" and "this player has one and
      nothing loaded publishes it" were indistinguishable on 500 of 764 canonical rows.
    * horizon_gap_lines says nothing when nothing is absent, never re-words the engine's own
      reason strings, and never counts a row that has no state to report.
    * The state never disagrees with the value: every "known" row has a multi-year figure and
      every non-known row has none, with a reason on all of them.
    * An AI-generated claim reaches the composite as a LABELLED, weight-throttled component --
      never silently, and never with force. Measured: a planted finding lands at weight 0.025
      against 0.61-0.87 for the structured sources, moving a real composite by 0.0.

  CHARACTERIZED (pinned, not endorsed; each cites its register item)
    * The board carries WHICH anchor produced a value (bpa_source) but no reason for any input
      it lacked, so the kind-of-absence distinction stops before the decision boundary (#112).
    * "unchecked" -- information nobody has looked for yet -- has no representation anywhere
      in production (#112).
"""

import ast
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

import bot_research
import data_merger as dm
import draft_room
import llm_engine


_APP_SOURCE = Path(__file__).with_name("app.py").read_text()

_NOT_APPLICABLE_REASON = "a team defense has no career arc to project; no source publishes one"


def _app_function(name: str) -> str:
    for node in ast.parse(_APP_SOURCE).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(_APP_SOURCE, node) or ""
    raise AssertionError(f"app.py has no top-level function named {name!r}")


class HorizonGapLinesTests(unittest.TestCase):
    """The pure reporting half of R16, exercised on hand-built rows so the assertions do not
    move with a baseline refresh."""

    KNOWN = {"name": "A", "proj_3yr": 900.0, "proj_3yr_state": "known", "proj_3yr_reason": ""}
    DEF = {"name": "D", "proj_3yr": None, "proj_3yr_state": "not_applicable",
           "proj_3yr_reason": _NOT_APPLICABLE_REASON}
    IDP = {"name": "B", "proj_3yr": None, "proj_3yr_state": "unknown",
           "proj_3yr_reason": "no multi-year figure from any source carrying this player"}
    KICKER = {"name": "K", "proj_3yr": None, "proj_3yr_state": "unknown",
              "proj_3yr_reason": "no multi-year figure on the sleeper_transcribed basis that prices this position"}
    UNMATCHED = {"name": "U", "proj_3yr": None}

    def test_nothing_absent_says_nothing(self):
        self.assertEqual(dm.horizon_gap_lines([self.KNOWN, self.KNOWN]), [])

    def test_an_empty_roster_says_nothing(self):
        self.assertEqual(dm.horizon_gap_lines([]), [])

    def test_the_two_opposite_states_are_counted_and_labelled_separately(self):
        text = "\n".join(dm.horizon_gap_lines([self.KNOWN, self.DEF, self.IDP, self.KICKER]))
        self.assertIn("NOT APPLICABLE (1)", text)
        self.assertIn("UNKNOWN (2)", text)
        self.assertIn("3 player(s)", text)

    def test_the_engines_own_reason_strings_are_used_verbatim(self):
        # Re-wording a reason here would put this module's paraphrase in front of the panel
        # instead of what the engine actually determined.
        text = "\n".join(dm.horizon_gap_lines([self.DEF, self.IDP]))
        self.assertIn(_NOT_APPLICABLE_REASON, text)
        self.assertIn("no multi-year figure from any source carrying this player", text)

    def test_two_different_reasons_in_one_state_both_survive(self):
        text = "\n".join(dm.horizon_gap_lines([self.IDP, self.KICKER]))
        self.assertIn("carrying this player", text)
        self.assertIn("sleeper_transcribed", text)

    def test_a_repeated_reason_is_not_repeated(self):
        text = "\n".join(dm.horizon_gap_lines([self.IDP, dict(self.IDP, name="B2")]))
        self.assertEqual(text.count("no multi-year figure from any source carrying this player"), 1)
        self.assertIn("UNKNOWN (2)", text)   # ...but both players are still counted

    def test_a_row_with_no_state_at_all_is_never_counted(self):
        # An unmatched player has no horizon state to report. Counting it would invent one.
        self.assertEqual(dm.horizon_gap_lines([self.UNMATCHED]), [])
        text = "\n".join(dm.horizon_gap_lines([self.DEF, self.UNMATCHED]))
        self.assertIn("1 player(s)", text)

    def test_a_known_row_with_a_missing_value_is_never_counted(self):
        # Contradictory input (state says known, value absent) is not this function's to
        # resolve -- it reports states it can trust, and stays silent otherwise.
        self.assertEqual(dm.horizon_gap_lines([dict(self.KNOWN, proj_3yr=None)]), [])

    def test_the_indent_is_a_parameter_not_a_hardcoded_context_shape(self):
        self.assertTrue(dm.horizon_gap_lines([self.DEF], indent="")[0].startswith("A blank"))


class HorizonStateSurvivesTheMergerTests(unittest.TestCase):
    """R16's carrying half, against the real committed baseline."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.pool = cls.merger.projections

    def _one(self, state: str) -> dict:
        rows = self.pool[self.pool["proj_3yr_state"] == state]
        self.assertFalse(rows.empty, f"the baseline carries no {state} row to test with")
        row = rows.iloc[0]
        return self.merger.merge_player(row["name"], position=row["position"], team=row.get("team"))

    def test_every_state_reaches_a_consumer(self):
        for state in ("known", "unknown", "not_applicable"):
            with self.subTest(state=state):
                self.assertEqual(self._one(state).get("proj_3yr_state"), state)

    def test_a_non_known_state_arrives_with_its_reason(self):
        for state in ("unknown", "not_applicable"):
            with self.subTest(state=state):
                self.assertTrue(self._one(state).get("proj_3yr_reason"))

    def test_the_two_opposite_absences_are_now_distinguishable_downstream(self):
        # This is the assertion that failed before R16: both arrived as the same missing key.
        na, unknown = self._one("not_applicable"), self._one("unknown")
        self.assertIsNone(na.get("proj_3yr"))
        self.assertIsNone(unknown.get("proj_3yr"))
        self.assertNotEqual(na["proj_3yr_state"], unknown["proj_3yr_state"])

    def test_a_table_with_no_such_column_gains_no_invented_state(self):
        # The Free Agent Finder and the Trade Value Chart have no multi-year figure to have a
        # state about. Built here rather than read off a baseline that may or may not carry a
        # free-agent export, so this asserts the guard rather than skipping when it matters.
        stateless = pd.DataFrame([{
            "name": "A Star", "norm_name": dm.normalize_name("A Star"),
            "position": "WR", "team": "CIN", "value": 100.0,
        }])
        out = self.merger.merge_player("A Star", df=stateless)
        self.assertTrue(out["matched"])
        self.assertNotIn("proj_3yr_state", out)
        self.assertNotIn("proj_3yr_reason", out)

    def test_the_state_vocabulary_is_closed(self):
        self.assertEqual(set(self.pool["proj_3yr_state"]), {"known", "unknown", "not_applicable"})

    def test_the_state_never_disagrees_with_the_value(self):
        known = self.pool[self.pool["proj_3yr_state"] == "known"]
        absent = self.pool[self.pool["proj_3yr_state"] != "known"]
        self.assertTrue(known["proj_3yr"].notna().all())
        self.assertTrue(absent["proj_3yr"].isna().all())

    def test_every_non_known_row_states_why(self):
        absent = self.pool[self.pool["proj_3yr_state"] != "known"]
        unexplained = absent[absent["proj_3yr_reason"].isna() | (absent["proj_3yr_reason"] == "")]
        self.assertTrue(unexplained.empty, f"{len(unexplained)} rows absent with no reason")

    def test_the_distinction_covers_a_material_share_of_the_pool(self):
        # Non-vacuity for everything above: if the baseline were all-known this file would be
        # passing on an empty set.
        non_known = (self.pool["proj_3yr_state"] != "known").sum()
        self.assertGreater(non_known, len(self.pool) * 0.25)


class ContextConsumesTheStateTests(unittest.TestCase):
    """app.py is a Streamlit script and cannot be imported (see test_debate_chip_wiring.py);
    checked AST-scoped to build_context rather than by scanning the whole file."""

    def test_build_context_reports_the_gap_rather_than_leaving_a_blank(self):
        self.assertIn("horizon_gap_lines(roster_table)", _app_function("build_context"))

    def test_the_helper_is_imported_from_the_module_that_computes_the_state(self):
        self.assertIn("horizon_gap_lines", _APP_SOURCE.split("from league_format")[0])


class AiClaimsCannotSilentlyBecomeAuthoritativeTests(unittest.TestCase):
    """§18's last question, measured end to end rather than argued."""

    @classmethod
    def setUpClass(cls):
        cls.baseline = dm.DataMerger()
        priced = cls.baseline.projections[cls.baseline.projections["proj_3yr_state"] == "known"]
        cls.target = priced.iloc[0]["name"]

    def setUp(self):
        self._real = bot_research.FINDINGS_PATH
        self._tmp = tempfile.TemporaryDirectory()
        bot_research.FINDINGS_PATH = Path(self._tmp.name) / "bot_research.json"

    def tearDown(self):
        bot_research.FINDINGS_PATH = self._real
        self._tmp.cleanup()

    def _plant(self, name, source, claim, rank):
        """Plant a claim that actually reaches the composite.

        7.4 and 6.2a now gate a finding's NUMBER on an allowlisted cited source plus a second
        adjudication. Every test in this class is about what happens to a claim ONCE IT IS IN
        the blend -- how it is labelled, how much weight it carries -- so the fixture has to get
        it there, or the class would silently be measuring the gate instead and passing on an
        empty components list.
        """
        finding_id = bot_research.add_finding(name, source, claim, rank=rank)
        bot_research.confirm_finding(finding_id)
        return finding_id

    def test_a_planted_claim_arrives_labelled_as_research_never_as_a_source(self):
        self._plant(self.target, "ESPN", "ESPN has him #1 overall", 1)
        after = dm.DataMerger().composite_player_score(self.target)
        sources = [c["source"] for c in after["components"]]
        self.assertIn("bot_research", sources)
        self.assertNotIn("ESPN", sources)   # the cited outlet never becomes a composite source

    def test_a_planted_claim_carries_far_less_weight_than_any_structured_source(self):
        self._plant(self.target, "ESPN", "ESPN has him #1 overall", 1)
        after = dm.DataMerger().composite_player_score(self.target)
        weights = {c["source"]: c["weight"] for c in after["components"]}
        research = weights.pop("bot_research")
        self.assertTrue(weights, "no structured source to compare against")
        self.assertLess(research * 10, min(weights.values()))

    def test_the_record_states_the_claims_own_impact_rather_than_leaving_it_inferable(self):
        """The property is that the record SAYS what its impact is, never that a reader has to
        infer it from whether `rank` happens to be null. 6.2a widened that from two answers to
        four, and each one still names its own reason -- which is the point, not an exception
        to it: "not counting because nobody has confirmed it" and "not counting because it has
        no number" are different facts about a row."""
        unconfirmed = bot_research.add_finding(self.target, "ESPN", "ranked #1", rank=1)
        confirmed = self._plant("A Other", "ESPN", "ranked #2", 2)
        unlisted = bot_research.add_finding("C Third", "some blog", "ranked #3", rank=3)
        qualitative = bot_research.add_finding("B Backup", "ESPN", "likes the usage trend")
        by_id = {f["id"]: f for f in bot_research.load_findings()}
        self.assertEqual(by_id[confirmed]["composite_impact"], "low-weight input")
        self.assertEqual(by_id[unconfirmed]["composite_impact"],
                         "none -- awaiting a second adjudication")
        self.assertEqual(by_id[unlisted]["composite_impact"],
                         "none -- cited source is not on the composite allowlist")
        self.assertEqual(by_id[qualitative]["composite_impact"], "none")

    def test_a_qualitative_claim_never_reaches_the_composite_at_all(self):
        bot_research.add_finding(self.target, "ESPN", "looks like a breakout", rank=None)
        after = dm.DataMerger().composite_player_score(self.target)
        self.assertNotIn("bot_research", [c["source"] for c in after["components"]])

    def test_a_relative_comparison_is_structurally_barred_from_the_composite(self):
        self.assertNotIn(
            "bot_comparisons",
            {source for source, _ in dm._EXTERNAL_PERCENTILE_RULES},
        )

    def test_every_composite_component_keeps_origin_time_and_trust(self):
        c = None
        for name in self.baseline.projections["name"].dropna().unique()[:300]:
            c = self.baseline.composite_player_score(name)
            if c and len(c["components"]) > 1:
                break
        self.assertIsNotNone(c, "no multi-source composite in the baseline to check")
        for component in c["components"]:
            for field in ("source", "percentile", "source_date", "pool_size", "weight"):
                self.assertIn(field, component)

    def test_no_opinion_at_all_returns_absence_rather_than_a_fabricated_score(self):
        self.assertIsNone(self.baseline.composite_player_score("Nobody Whatsoever Xyz"))


class KindOfAbsenceStopsAtTheBoardTests(unittest.TestCase):
    def test_CHARACTERIZATION_the_board_says_which_anchor_but_never_why_an_input_was_missing(self):
        """#112. compute_draft_board emits bpa_source (which of four anchors produced the
        value) and confidence (derived from it), so a candidate can say where its number came
        from. It emits no reason for anything it did NOT have -- proj_3yr_state included -- so
        the kind-of-absence distinction R16 carried as far as the roster context does not reach
        the decision boundary or the Draft Room debate.

        Pinned, not endorsed: adding it changes the PickSnapshot candidate schema, the same
        frozen boundary #107 is parked on. Delete this test when #112 is settled; do not loosen
        it.
        """
        tree = ast.parse(Path(__file__).with_name("draft_room.py").read_text())
        board = next(n for n in ast.walk(tree)
                     if isinstance(n, ast.FunctionDef) and n.name == "compute_draft_board")
        emitted = set()
        for node in ast.walk(board):
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.List):
                emitted.update(e.value for e in node.slice.elts
                               if isinstance(e, ast.Constant) and isinstance(e.value, str))
        self.assertIn("bpa_source", emitted)      # non-vacuity: this really is the column list
        self.assertIn("confidence", emitted)
        self.assertNotIn("proj_3yr_state", emitted)
        self.assertNotIn("proj_3yr_reason", emitted)

    def test_the_anchor_label_is_always_one_of_the_four_it_scores(self):
        # _confidence falls back to 35.0 for an unrecognised label; that branch is unreachable
        # only while every assignment stays inside the known set. Checked rather than assumed.
        source = Path(__file__).with_name("draft_room.py").read_text()
        assigned = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
                    and isinstance(node.value.value, str) and node.value.value.startswith(
                        ("points_vor", "position_relative")):
                assigned.add(node.value.value)
        self.assertTrue(assigned)
        self.assertTrue(assigned <= set(draft_room.CONFIDENCE_BY_SOURCE))

    def test_CHARACTERIZATION_unchecked_has_no_representation_anywhere(self):
        """#112. Of the eight states §18 names, "never checked" is the one with no
        representation at all: unknown, not-applicable, unavailable, stale and intentionally
        omitted each have at least one implementation, and disputed is resolved or excluded
        rather than carried. Nothing anywhere can say "nobody has looked for this yet".

        Pinned, not endorsed -- introducing it means deciding what would ever set it.
        Delete this test when #112 is settled.
        """
        here = Path(__file__).parent
        hits = []
        for path in sorted(here.glob("*.py")):
            if path.name.startswith(("test_", "run_", "compare_", "verify_", "cdme_")):
                continue
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                        and node.value.strip().lower() in ("unchecked", "not_checked", "never_checked"):
                    hits.append(f"{path.name}:{node.lineno}")
        self.assertEqual(hits, [], f"an 'unchecked' state now exists -- settle #112: {hits}")


class AbsenceLabelsThatDoReachAConsumerTests(unittest.TestCase):
    """Five of the six absence-naming mechanisms in this codebase reach a consumer. Pinned so
    the ones that work keep working."""

    def test_a_failed_chair_report_is_relabelled_as_missing_for_the_next_chair(self):
        self.assertIn("MISSING information", llm_engine.UNAVAILABLE_REPORT)
        self.assertEqual(llm_engine._report_for_handoff("⚠️ boom"), llm_engine.UNAVAILABLE_REPORT)
        self.assertEqual(llm_engine._report_for_handoff("a real report"), "a real report")

    def test_a_position_with_no_starter_demand_is_omitted_rather_than_zeroed(self):
        doc = draft_room.replacement_levels.__doc__ or ""
        self.assertIn("OMITTED", doc)
        self.assertIn("never as zero", doc)

    def test_an_unmeasurable_waiting_cost_is_absent_rather_than_free(self):
        doc = draft_room._attach_waiting_cost.__doc__ or ""
        self.assertIn("None (not zero)", doc)

    def test_the_incomplete_profile_marker_is_a_named_constant_not_an_inline_blank(self):
        self.assertIn('INCOMPLETE_PLAYER_PROFILE = "Incomplete Player Profile"', _APP_SOURCE)
        self.assertIn("INCOMPLETE_PLAYER_PROFILE", _app_function("build_context"))


if __name__ == "__main__":
    unittest.main()
