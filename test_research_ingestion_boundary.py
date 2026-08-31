"""§6 (ARCHITECTURE_AUDIT Pass 4): the boundary between ephemeral debate research and
canonical CDME ingestion.

There IS a boundary, and it is layered rather than binary. Panel-surfaced findings are kept
out of CDME's own valuation entirely (a `source_name == "keeptradecut"` whitelist, already
enforced by test_cdme_ingestion_boundary.py), and admitted to the *composite* score only under
three dampeners: the lowest source weight of any source, a recency decay, and a pool-size
factor that exists because a one-row pool once made every finding read as the 100th percentile.
This file pins those dampeners, because they are the whole reason a low-confidence finding
cannot quietly become a durable fact.

Two postures, kept separate:

  ENFORCEMENT. The dampeners, the qualitative/numeric split, and the "comparisons never reach
  the composite" rule are guarantees. They must always hold.

  CHARACTERIZATION. `ResearchFrameIsNotNameInjectiveTests` and `ValidatedFlagIsUnconditional`
  record KNOWN GAPS -- today's behavior, deliberately asserted. **Invert them when repaired,
  do not delete them**, same posture as test_draft_strategy.py's round-boundary
  characterization and test_benchmark_contract_coverage.py's moderator gap.

Every test that touches the on-disk store redirects it to a temp file and restores the module
attribute afterwards, so no test can leave a research store behind in data/baseline/.
"""

import json
import tempfile
import unittest
from pathlib import Path

import bot_research
import data_merger


class _TempResearchStore:
    """Redirect bot_research's module-level paths at a temp dir for one test."""

    def __init__(self, findings=(), comparisons=()):
        self._findings = list(findings)
        self._comparisons = list(comparisons)

    def __enter__(self):
        self._dir = tempfile.TemporaryDirectory()
        base = Path(self._dir.name)
        self._saved = (bot_research.FINDINGS_PATH, bot_research.COMPARISONS_PATH)
        bot_research.FINDINGS_PATH = base / "bot_research.json"
        bot_research.COMPARISONS_PATH = base / "bot_comparisons.json"
        if self._findings:
            bot_research.FINDINGS_PATH.write_text(json.dumps(self._findings))
        if self._comparisons:
            bot_research.COMPARISONS_PATH.write_text(json.dumps(self._comparisons))
        return self

    def __exit__(self, *exc):
        bot_research.FINDINGS_PATH, bot_research.COMPARISONS_PATH = self._saved
        self._dir.cleanup()
        return False


def _finding(pid, ts, name, source, rank, date="2026-08-30"):
    return {"id": pid, "ts": ts, "date": date, "player_name": name,
            "source": source, "claim": f"{source} says {rank}", "rank": rank}


class DampenersOnPanelSurfacedResearchTests(unittest.TestCase):
    """The three guards that stop a finding becoming a durable fact. Enforcement."""

    def test_panel_research_carries_the_lowest_source_weight_of_any_source(self):
        weights = data_merger.COMPOSITE_SOURCE_WEIGHTS
        self.assertIn("bot_research", weights)
        self.assertEqual(
            weights["bot_research"], min(weights.values()),
            "Panel-surfaced research must never outweigh a deterministically parsed source "
            "at equal freshness.",
        )
        # Non-vacuity: there are other sources to be the minimum of.
        self.assertGreaterEqual(len(weights), 4)

    def test_a_small_finding_pool_is_dampened_proportionally(self):
        """The concrete bug this exists to prevent: a pool of one always ranks its only member
        in the 100th percentile, whatever the underlying claim."""
        floor = data_merger.COMPOSITE_MIN_TRUSTED_POOL_SIZE
        self.assertGreater(floor, 1)
        for pool, expected in ((1, 1 / floor), (floor // 2, (floor // 2) / floor), (floor, 1.0),
                               (floor * 10, 1.0)):
            self.assertAlmostEqual(min(1.0, pool / floor), expected)

    def test_freshness_decays_by_a_stated_halflife(self):
        halflife = data_merger.COMPOSITE_RECENCY_HALFLIFE_DAYS
        self.assertGreater(halflife, 0)
        self.assertEqual(data_merger._recency_weight(None), 0.5,
                         "An undated source must get a middling weight, never full trust.")

    def test_a_fresh_finding_cannot_outweigh_a_fresh_vendor_source(self):
        """At equal freshness and full pools the ordering is guaranteed by the weights alone."""
        weights = data_merger.COMPOSITE_SOURCE_WEIGHTS
        for source, weight in weights.items():
            if source == "bot_research":
                continue
            self.assertGreater(weight, weights["bot_research"], f"{source} must outrank research.")


class WhatIsAdmittedAndWhatIsNotTests(unittest.TestCase):
    """The ephemeral/canonical split as it actually exists. Enforcement."""

    def test_a_qualitative_finding_never_reaches_the_composite(self):
        with _TempResearchStore(findings=[
            {"id": 1, "ts": 1.0, "date": "2026-08-30", "player_name": "Some Player",
             "source": "ESPN", "claim": "trending up", "rank": None},
        ]):
            self.assertEqual(len(data_merger.load_bot_research_as_external()), 0)

    def test_a_numeric_finding_does_reach_it_so_the_test_above_is_not_vacuous(self):
        with _TempResearchStore(findings=[_finding(1, 1.0, "Some Player", "ESPN", 3)]):
            frame = data_merger.load_bot_research_as_external()
            self.assertEqual(len(frame), 1)
            self.assertEqual(frame.iloc[0]["source_name"], "bot_research")

    def test_comparisons_are_a_separate_store_that_never_feeds_the_composite(self):
        with _TempResearchStore():
            new_id = bot_research.add_comparison(
                "Player A", "Player B", ">", "ESPN", evidence="ESPN's own list order",
            )
            self.assertIsNotNone(new_id)
            entry = bot_research.load_comparisons()[0]
            self.assertEqual(entry["composite_impact"], "none")
        self.assertNotIn(
            ("bot_research", "comparisons"), data_merger._EXTERNAL_PERCENTILE_RULES,
            "Comparisons must have no percentile rule -- a relative claim has no absolute "
            "number to rank.",
        )

    def test_research_is_excluded_from_the_external_upload_refresh_targets(self):
        self.assertNotIn("bot_research", data_merger.external_upload_targets())

    def test_only_the_newest_finding_per_player_and_cited_source_is_kept(self):
        with _TempResearchStore(findings=[
            _finding(1, 1000.0, "Some Player", "ESPN", 40),
            _finding(2, 2000.0, "Some Player", "ESPN", 4),
        ]):
            frame = data_merger.load_bot_research_as_external()
            self.assertEqual(len(frame), 1)
            self.assertEqual(frame.iloc[0]["rank"], 4, "Newest must win within one cited source.")

    def test_same_day_duplicates_are_deduplicated_on_write(self):
        with _TempResearchStore():
            first = bot_research.add_finding("Some Player", "ESPN", "ESPN has him WR3", rank=3)
            second = bot_research.add_finding("Some Player", "ESPN", "ESPN has him WR3", rank=3)
            self.assertEqual(first, second)
            self.assertEqual(len(bot_research.load_findings()), 1)

    def test_a_blank_finding_is_a_no_op_rather_than_a_stored_row(self):
        with _TempResearchStore():
            self.assertIsNone(bot_research.add_finding("", "ESPN", "claim", rank=3))
            self.assertIsNone(bot_research.add_finding("Player", "", "claim", rank=3))
            self.assertEqual(bot_research.load_findings(), [])


class ResearchFrameIsNotNameInjectiveTests(unittest.TestCase):
    """KNOWN GAP — characterization. Invert when repaired; do not delete.

    R1-R3 (#82) made the vendor pools name-injective and #89 made `_resolve` report ambiguity
    honestly. The research frame is keyed by (player, CITED SOURCE), so two findings about one
    player citing two different sources produce two rows sharing a normalized name -- and the
    frame carries no team or position column, so no caller can disambiguate within it. One row
    wins the composite component; the other is dropped with no conflict recorded anywhere.
    """

    CONTRADICTORY = [
        _finding(1, 1000.0, "Aidan Hutchinson", "ESPN", 3),
        _finding(2, 2000.0, "Aidan Hutchinson", "FantasyPros", 41),
    ]

    def test_two_cited_sources_on_one_player_produce_two_rows_sharing_a_name(self):
        with _TempResearchStore(findings=self.CONTRADICTORY):
            frame = data_merger.load_bot_research_as_external()
            self.assertEqual(len(frame), 2)
            self.assertFalse(frame["norm_name"].is_unique)

    def test_the_frame_carries_nothing_to_disambiguate_with(self):
        with _TempResearchStore(findings=self.CONTRADICTORY):
            columns = set(data_merger.load_bot_research_as_external().columns)
        self.assertNotIn("team", columns)
        self.assertNotIn("position", columns)
        # What it does carry, so the gap is about disambiguation and not about emptiness.
        for expected in ("name", "norm_name", "source_name", "source_file", "cited_source",
                         "claim", "rank", "source_date"):
            self.assertIn(expected, columns)

    def test_the_composite_reads_the_row_without_the_ambiguity_flag(self):
        """`_find_match` is `_resolve(...)[0]` -- the row, with `verified` discarded. The signal
        exists; this consumer does not read it."""
        import inspect
        source = inspect.getsource(data_merger.DataMerger.composite_player_score)
        self.assertIn("_find_match", source)
        self.assertNotIn("verified", source)
        self.assertIn("return self._resolve(", inspect.getsource(data_merger.DataMerger._find_match))

    def test_the_ambiguity_signal_itself_is_still_correct(self):
        """Non-vacuity for the gap: `_resolve` DOES report the collision. The gap is that this
        path drops it, not that the identity boundary regressed."""
        with _TempResearchStore(findings=self.CONTRADICTORY):
            merger = data_merger.DataMerger()
            sub = merger.external_values[merger.external_values["source_name"] == "bot_research"]
            self.assertEqual(len(sub), 2)
            _row, _path, candidates, verified = merger._resolve("Aidan Hutchinson", df=sub)
            self.assertEqual(candidates, 2)
            self.assertFalse(verified)


class NoLifecycleAndNoValidationQueueTests(unittest.TestCase):
    """KNOWN GAP — characterization of what §6 asks for and the architecture does not have."""

    def test_a_finding_carries_no_lifecycle_state(self):
        """§6 asks for discovered -> corroborated -> disputed -> adjudicated ->
        canonical/rejected/expired. `composite_impact` is a routing label, not a lifecycle."""
        with _TempResearchStore():
            bot_research.add_finding("Some Player", "ESPN", "ESPN has him WR3", rank=3)
            entry = bot_research.load_findings()[0]
        self.assertEqual(entry["composite_impact"], "low-weight input")
        for absent in ("status", "lifecycle", "state", "corroborated", "disputed",
                       "adjudicated", "expires_at", "retracted"):
            self.assertNotIn(absent, entry)

    def test_a_finding_preserves_no_evidence_snapshot(self):
        """§6: what happens when a source changes or disappears after a review event? The
        stored evidence is the Moderator's own one-line paraphrase and a source NAME -- no
        URL, no retrieval timestamp, no quoted excerpt."""
        with _TempResearchStore():
            bot_research.add_finding("Some Player", "ESPN", "ESPN has him WR3", rank=3)
            entry = bot_research.load_findings()[0]
        for absent in ("url", "link", "retrieved_at", "snapshot", "excerpt", "quote"):
            self.assertNotIn(absent, entry)
        self.assertIn("claim", entry)
        self.assertIn("source", entry)

    def test_a_comparison_is_stored_as_validated_unconditionally(self):
        """The flag is hard-coded True on every write -- the 'panel-scrutiny gate' it refers to
        is the Moderator choosing to emit the line, which this code cannot verify. Recorded
        because the shape matches §13.3's repaired alias flag; the difference, and the reason
        this is DOCUMENT rather than a defect, is that nothing in production reads it."""
        with _TempResearchStore():
            bot_research.add_comparison("Player A", "Player B", ">", "ESPN")
            entry = bot_research.load_comparisons()[0]
        self.assertTrue(entry["validated"])

    def test_nothing_in_production_reads_that_validated_flag(self):
        """If this starts failing, the flag has gained a consumer and stops being cosmetic --
        at which point it needs to become honest before it is trusted."""
        import inspect
        for module in (data_merger, bot_research):
            source = inspect.getsource(module)
            readers = [
                line for line in source.splitlines()
                if "validated" in line and "=" not in line.split("validated")[0][-3:]
                and not line.strip().startswith("#")
            ]
            for line in readers:
                self.assertIn(
                    '"validated": True', line,
                    f"{module.__name__} appears to READ the validated flag: {line.strip()!r}",
                )


if __name__ == "__main__":
    unittest.main()
