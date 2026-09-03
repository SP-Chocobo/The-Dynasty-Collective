"""#52 / #49 / #88: the forward record -- can this engine's beliefs ever meet reality?

Every other validation in this repo asks whether the engine agrees with itself. This module
covers the one artifact that asks whether it agrees with the world, and the properties that
make such an artifact worth anything at all.

A prediction file is only evidence if it demonstrably predates what it is scored against.
Nothing about a file on disk establishes that by itself -- a JSON file written yesterday and a
JSON file written after the season looks identical. So the guarantees have to be structural:
it cannot be overwritten, and it carries a hash of its own contents. Both are tested here,
because both are the entire reason the file is worth keeping.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import prediction_record as pr

_HERE = Path(__file__).parent

ROWS = [
    {"player_id": "1", "name": "A Player", "position": "RB", "universal_value": 88.0},
    {"player_id": "2", "name": "B Player", "position": "WR", "universal_value": 71.5},
]


class WriteOnceTests(unittest.TestCase):
    """The refusal is the mechanism, not a convenience."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def test_a_record_can_be_written(self):
        record = pr.capture(ROWS, as_of="2026-01-01", root=self.root)
        self.assertEqual(record["n_players"], 2)
        self.assertTrue(pr.record_path("2026-01-01", self.root).exists())

    def test_a_second_write_for_the_same_date_is_refused(self):
        pr.capture(ROWS, as_of="2026-01-01", root=self.root)
        with self.assertRaises(FileExistsError):
            pr.capture(ROWS, as_of="2026-01-01", root=self.root)

    def test_the_refusal_explains_why_rather_than_just_failing(self):
        """Someone will hit this months from now with no memory of the reasoning, and the
        obvious reaction to an unexplained refusal is to delete the file and move on."""
        pr.capture(ROWS, as_of="2026-01-01", root=self.root)
        with self.assertRaises(FileExistsError) as caught:
            pr.capture(ROWS, as_of="2026-01-01", root=self.root)
        self.assertIn("not a prediction", str(caught.exception))

    def test_a_different_date_is_a_different_record(self):
        """Write-once is per as-of date, not per directory -- a second season's record must
        not be blocked by the first."""
        pr.capture(ROWS, as_of="2026-01-01", root=self.root)
        pr.capture(ROWS, as_of="2027-01-01", root=self.root)
        self.assertEqual(pr.records(self.root), ["2026-01-01", "2027-01-01"])


class TamperingIsVisibleTests(unittest.TestCase):
    """Write-once stops the honest mistake. The hash is what makes the dishonest edit show."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        pr.capture(ROWS, as_of="2026-01-01", root=self.root)

    def test_an_untouched_record_verifies(self):
        self.assertEqual(pr.verify("2026-01-01", self.root)["state"], "intact")

    def test_an_edited_prediction_is_caught(self):
        path = pr.record_path("2026-01-01", self.root)
        record = json.loads(path.read_text())
        record["predictions"][0]["universal_value"] = 99.9   # the flattering revision
        path.write_text(json.dumps(record))
        self.assertEqual(pr.verify("2026-01-01", self.root)["state"], "ALTERED")

    def test_editing_the_METADATA_does_not_cry_wolf(self):
        """The hash covers the rows only, on purpose. A record re-serialized with a new comment
        is the same prediction, and a fingerprint that moved for a cosmetic reason would train
        its reader to ignore it -- which is worse than not having one."""
        path = pr.record_path("2026-01-01", self.root)
        record = json.loads(path.read_text())
        record["_comment"] = "rewritten prose, same predictions"
        record["league_shape"] = "reworded"
        path.write_text(json.dumps(record))
        self.assertEqual(pr.verify("2026-01-01", self.root)["state"], "intact")

    def test_a_missing_record_says_missing_rather_than_intact(self):
        """Absence must not read as verification. 'Nothing to check' and 'checked and fine'
        are different answers, and only one of them means the record exists."""
        self.assertEqual(pr.verify("1999-01-01", self.root)["state"], "missing")


class TheRecordStatesItsOwnScopeTests(unittest.TestCase):
    """A prediction file reporting its count without its coverage overstates itself by
    omission, and the reader who most needs the scope is the one scoring it months from now."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def test_coverage_names_the_positions_actually_predicted(self):
        record = pr.capture(ROWS, as_of="2026-01-01", pool_size=900, root=self.root)
        self.assertEqual(record["coverage"]["positions"], ["RB", "WR"])
        self.assertEqual(record["coverage"]["by_position"], {"RB": 1, "WR": 1})

    def test_the_source_pool_size_is_recorded_so_the_gap_is_visible(self):
        record = pr.capture(ROWS, as_of="2026-01-01", pool_size=900, root=self.root)
        self.assertEqual(record["coverage"]["source_pool_size"], 900)
        self.assertLess(record["n_players"], record["coverage"]["source_pool_size"])

    def test_it_says_that_absent_positions_are_absent_and_not_wrong(self):
        """The distinction a scorer must not collapse: a position with no slot in this league
        was never predicted, so counting it as a miss would manufacture error out of absence --
        the same defect this codebase repaired in the pricing and horizon layers."""
        record = pr.capture(ROWS, as_of="2026-01-01", root=self.root)
        self.assertIn("NOT predicted-and-wrong", record["coverage"]["excluded"])

    def test_the_input_source_dates_are_carried(self):
        """What the prediction was made FROM, so a later reader can check the inputs predate
        the outcomes too -- a fresh prediction built on contaminated inputs is still
        contaminated."""
        record = pr.capture(ROWS, as_of="2026-01-01", root=self.root,
                            source_dates=["2026-08-18", "2026-08-25", None])
        self.assertEqual(record["input_source_dates"], ["2026-08-18", "2026-08-25"])


class TheCommittedRecordTests(unittest.TestCase):
    """Non-vacuity for everything above: the real record has to exist and be sound, or this
    module is testing a mechanism nobody used."""

    def test_at_least_one_real_record_is_committed(self):
        self.assertGreater(len(pr.records()), 0,
                           "no prediction record exists -- the forward test is unarmed, and "
                           "the window for an uncontaminated one closes when the season starts")

    def test_every_committed_record_verifies(self):
        for as_of in pr.records():
            with self.subTest(as_of=as_of):
                self.assertEqual(pr.verify(as_of)["state"], "intact")

    def test_the_committed_record_carries_real_predictions(self):
        """Guards against an empty or placeholder record satisfying the check above."""
        for as_of in pr.records():
            with self.subTest(as_of=as_of):
                record = pr.load(as_of)
                self.assertGreater(record["n_players"], 100)
                priced = [r for r in record["predictions"]
                          if r.get("universal_value") is not None]
                self.assertEqual(len(priced), record["n_players"],
                                 "a record row without a value is not a prediction")

    def test_its_inputs_predate_it(self):
        """The property the whole exercise rests on. If a record's source data is newer than
        the record, something has been regenerated and the ordering claim is void."""
        for as_of in pr.records():
            with self.subTest(as_of=as_of):
                record = pr.load(as_of)
                for source_date in record.get("input_source_dates", []):
                    self.assertLessEqual(source_date, as_of,
                                         f"input dated {source_date} is newer than the record")


class TheScorerIsDeliberatelyAbsentTests(unittest.TestCase):
    """Scoring needs realized outcomes this repo does not have. Writing the scorer now would
    mean writing it against imagined data -- the trap that voided four instruments earlier in
    this project. Its absence is a decision, and this is where the decision is recorded."""

    def test_no_scorer_exists_yet(self):
        """Checked against what the module DEFINES, not its prose. A first version of this
        test scanned raw source and failed on the docstring sentence explaining why the scorer
        is absent -- a guard tripping over its own rationale, which is the second time that
        exact shape has appeared in this suite."""
        import ast
        tree = ast.parse((_HERE / "prediction_record.py").read_text())
        defined = {n.name for n in ast.walk(tree)
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        for name in sorted(defined):
            with self.subTest(name=name):
                self.assertFalse(
                    name.startswith("score") or "realized" in name or "actual" in name,
                    f"{name}() looks like a scorer -- scoring needs outcomes this repo does "
                    f"not have, so writing one means writing it against imagined data")

    def test_and_the_module_says_why(self):
        """So the gap reads as a stated boundary rather than an oversight someone should
        helpfully close."""
        source = (_HERE / "prediction_record.py").read_text()
        self.assertIn("It scores nothing", source)


if __name__ == "__main__":
    unittest.main()
