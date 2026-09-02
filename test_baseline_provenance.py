"""§7.10: the provenance record is checkable against the files it describes.

WHY THIS EXISTS AT ALL. §7.10's finding was that provenance coverage was INVERTED -- the
secondary sources documented, the primary valuation input not. Writing a record closes that, but
a record nobody checks decays into exactly the thing this repository keeps repairing: prose that
was true once, still sitting there, believed. So the row counts and dates below are read off the
real CSVs and compared, and the coverage set is derived rather than restated.

WHAT IT DOES NOT CHECK, said plainly: nothing here can verify that the numbers in those CSVs are
correct, only that the record describing them still matches them.
"""

import json
import unittest
from pathlib import Path

import data_merger

_HERE = Path(__file__).parent
_BASELINE = _HERE / "data/baseline"
_RECORD_PATH = _BASELINE / "baseline_provenance.json"


def _record() -> dict:
    return json.loads(_RECORD_PATH.read_text())


def _rows(path: Path) -> int:
    return sum(1 for _ in path.read_text().splitlines()) - 1


class CoverageIsCompleteAndDerivedTests(unittest.TestCase):
    def test_every_ranking_csv_is_covered_by_exactly_one_record(self):
        """The two Sleeper projection files have their own record (they carry the scoring rules
        that make their points meaningful); everything else in the directory belongs here. A file
        in neither is the §7.10 gap reopening, and a file in BOTH is two records that can
        disagree."""
        on_disk = {p.name for p in (_BASELINE / "rankings").glob("*.csv")}
        here = set(_record()["data/baseline/rankings/"]["files"])
        sleeper = set(json.loads((_BASELINE / "sleeper_projection_provenance.json").read_text()))
        sleeper = {name for name in sleeper if name.endswith(".csv")}
        self.assertEqual(here & sleeper, set(), "covered by two records that can disagree")
        self.assertEqual(on_disk - (here | sleeper), set(), "a committed CSV with no provenance")
        self.assertEqual((here | sleeper) - on_disk, set(), "a record for a file that is gone")

    def test_the_trade_value_chart_is_covered(self):
        self.assertIn("data/baseline/trade_value/dynasty_ppr_trade_value_chart.csv", _record())


class TheRecordStillMatchesTheFilesTests(unittest.TestCase):
    def test_every_recorded_row_count_matches_the_csv(self):
        for name, entry in _record()["data/baseline/rankings/"]["files"].items():
            with self.subTest(file=name):
                self.assertEqual(entry["rows"], _rows(_BASELINE / "rankings" / name))

    def test_every_recorded_source_date_matches_the_csv(self):
        """source_date is the date the EXPORT carried, and it is the only thing standing between
        a reader and treating a fixed baseline as current (§19.11.2). If the record and the file
        ever disagree about it, the record is the one that will be believed."""
        for name, entry in _record()["data/baseline/rankings/"]["files"].items():
            with self.subTest(file=name):
                path = _BASELINE / "rankings" / name
                dates = {line.rsplit(",", 1)[-1].strip()
                         for line in path.read_text().splitlines()[1:] if line.strip()}
                self.assertEqual(dates, {entry["source_date"]})

    def test_the_trade_charts_composition_matches(self):
        entry = _record()["data/baseline/trade_value/dynasty_ppr_trade_value_chart.csv"]
        path = _BASELINE / "trade_value" / "dynasty_ppr_trade_value_chart.csv"
        lines = [line for line in path.read_text().splitlines()[1:] if line.strip()]
        counted: dict[str, int] = {}
        for line in lines:
            counted[line.split(",", 1)[0]] = counted.get(line.split(",", 1)[0], 0) + 1
        self.assertEqual(entry["rows"], len(lines))
        self.assertEqual(entry["composition"], counted)

    def test_the_two_idp_files_are_recorded_as_carrying_no_projection(self):
        """#51's supply defect is a property of these files, not of the arithmetic, and the
        record is where a future reader learns that before re-deriving it."""
        for name in ("ppr_idp_rankings.corrected.csv", "superflex_idp_rankings.corrected.csv"):
            with self.subTest(file=name):
                header = (_BASELINE / "rankings" / name).read_text().splitlines()[0]
                self.assertNotIn("projection", header)
                entry = _record()["data/baseline/rankings/"]["files"][name]
                self.assertIn("columns_differ", entry)


class TheVendorStaysUnnamedTests(unittest.TestCase):
    """The §7.10 ruling, enforced rather than merely intended: state origins where not
    pay-locked, and leave the paid vendor unnamed IN THIS RECORD.

    The forbidden token is read out of `data_merger.COMPOSITE_SOURCE_WEIGHTS` rather than typed
    here, so this test never spells the name it is keeping out of that file -- and so it follows
    a rename instead of pinning one.
    """

    def _vendor_key(self) -> str:
        weights = set(data_merger.COMPOSITE_SOURCE_WEIGHTS)
        return max(weights, key=lambda k: data_merger.COMPOSITE_SOURCE_WEIGHTS[k])

    def test_the_record_does_not_name_the_paid_vendor(self):
        key = self._vendor_key()
        text = _RECORD_PATH.read_text().lower()
        self.assertNotIn(key, text)
        # Also the spaced spelling, which the key's own concatenation hides.
        self.assertNotIn(" ".join([key[:5], key[5:]]), text)

    def test_the_record_says_the_omission_is_deliberate(self):
        """An unexplained absence reads as an oversight and gets 'fixed'. The record has to carry
        its own reason, or the next reader copies the name across from README."""
        text = _RECORD_PATH.read_text()
        self.assertIn("deliberately unnamed", text)
        self.assertIn("README", text)

    def test_it_still_states_what_is_not_pay_locked(self):
        """The other half of the ruling. A record that omitted everything would satisfy the
        constraint and defeat the purpose."""
        entry = _record()["data/baseline/rankings/"]["files"]["dynasty_ppr_rankings.csv"]
        self.assertEqual(set(entry), {"rows", "scope", "source_date"})
        common = _record()["_common"]
        self.assertIn("ingest_method", common)
        self.assertIn("known_limitations", common)
        self.assertIs(common["origin_public"], False)


class TheRecordIsDocumentationNotAnInputTests(unittest.TestCase):
    def test_no_production_module_reads_it(self):
        """Same posture as sleeper_projection_provenance.json: nothing consumes this at runtime,
        so a prose edit cannot change a price. Its only reader is this test."""
        for path in sorted(_HERE.glob("*.py")):
            if path.name.startswith("test_"):
                continue
            with self.subTest(module=path.name):
                self.assertNotIn("baseline_provenance", path.read_text())


if __name__ == "__main__":
    unittest.main()
