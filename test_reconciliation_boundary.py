"""Reconciliation and schema invariants (repair boundaries R6 + R7, combined).

The failure class: reconciliation was `drop_duplicates(keep="last")` -- the winning ROW
replaced the loser wholesale, with no per-field precedence anywhere and nothing recorded.
Measured on the committed baseline: 706 players appear in more than one file, 51 fields were
silently dropped where the winner was null and a loser had a value, and 1084 field-level
conflicts were resolved every load with none recorded. Precedence itself came down to
(source_date, filename), and load_all's own comment calls that filename tiebreak "an arbitrary
string comparison", explicitly not a semantic rule.

Two things the obvious repair would break, both measured, both asserted here:

  * CROSS-BASIS RATIO. K's proj_3yr lives in the vendor file; the season projection that won
    the merge came from a screenshot-transcribed file for an unrelated league. Pairing them
    inflates every kicker's apparent trajectory by a median 1.43x.
  * CROSS-BASIS MIXTURE. A field-level merge across bases would give K a pool of 13 players
    averaging 153 points beside 24 averaging 88 -- a 1.43x step INSIDE one position. VOR reads
    spread as positional separation, so that lands directly on the anchor.

Hence single-basis-per-position, chosen by COVERAGE first: taking the higher-confidence basis
instead would drop K from 37 players to 13 and re-break the supply defect that was measured to
overstate the best K/DEF's VOR by ~45%. A missing horizon nudge is the smaller loss, and it is
recorded rather than silent.
"""
import tempfile
import unittest
from pathlib import Path

import pandas as pd

import data_merger as dm


class MeasurementBasisRegistryTests(unittest.TestCase):
    """The basis label is provenance-backed, not filename-guessed: those two CSVs are
    documented in data/baseline/sleeper_projection_provenance.json as "transcribed from
    Sleeper app screenshots (SEASON PROJ), not an API pull", from two DIFFERENT leagues,
    neither of them the one being drafted."""

    def test_the_transcribed_files_are_labelled_as_such(self):
        for filename in ("sleeper_kicker_projections.csv", "sleeper_dst_projections.csv"):
            self.assertEqual(dm.measurement_basis(filename), "sleeper_transcribed", filename)

    def test_vendor_rankings_are_labelled_vendor(self):
        for filename in ("dynasty_ppr_rankings.csv", "te_premium_dynasty_rankings.csv",
                         "dynasty_kicker_rankings.csv"):
            self.assertEqual(dm.measurement_basis(filename), "draftsharks_vendor", filename)

    def test_confidence_orders_vendor_above_transcribed(self):
        self.assertGreater(dm.BASIS_CONFIDENCE["draftsharks_vendor"],
                           dm.BASIS_CONFIDENCE["sleeper_transcribed"])


class SingleBasisPerPositionTests(unittest.TestCase):
    """The canonical table must never price one position off two scales."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    def test_every_position_resolves_to_exactly_one_basis(self):
        proj = self.merger.projections
        self.assertIn("measurement_basis", proj.columns)
        for position, rows in proj.groupby("position"):
            bases = set(rows["measurement_basis"].dropna())
            self.assertLessEqual(len(bases), 1, f"{position} priced on {bases}")

    def test_coverage_wins_so_kicker_supply_is_not_cut_to_the_vendor_subset(self):
        kickers = self.merger.projections[self.merger.projections["position"] == "K"]
        self.assertGreater(len(kickers), 13,
                           "choosing the vendor basis would re-break the K/DEF supply defect")

    def test_the_chosen_basis_for_kicker_is_the_one_that_covers_it(self):
        kickers = self.merger.projections[self.merger.projections["position"] == "K"]
        self.assertEqual(set(kickers["measurement_basis"]), {"sleeper_transcribed"})

    def test_no_player_is_lost_by_excluding_the_other_basis(self):
        # The vendor rows excluded at K and DEF are a subset of the covering basis's players,
        # so single-basis costs coverage nowhere. If a future source breaks that, this fails.
        for position, expected_minimum in (("K", 37), ("DEF", 32)):
            rows = self.merger.projections[self.merger.projections["position"] == position]
            self.assertGreaterEqual(len(rows), expected_minimum, position)


class FieldLevelMergeTests(unittest.TestCase):
    """Within one basis, a field the winning row lacks is taken from a same-basis row that has
    it -- rather than the winning row replacing the loser wholesale."""

    def _frames(self):
        older = pd.DataFrame([{"name": "A One", "position": "WR", "team": "CIN",
                               "projection": 200.0, "proj_3yr": 600.0, "trade_value": 40.0,
                               "source_date": "2026-08-01", "source_file": "b_older.csv"}])
        newer = pd.DataFrame([{"name": "A One", "position": "WR", "team": "CIN",
                               "projection": 210.0, "proj_3yr": None, "trade_value": None,
                               "source_date": "2026-08-20", "source_file": "a_newer.csv"}])
        for frame in (older, newer):
            frame["norm_name"] = frame["name"].map(dm.normalize_name)
            frame["measurement_basis"] = "draftsharks_vendor"
        return [older, newer]

    def test_a_field_the_winner_lacks_is_taken_from_a_same_basis_row(self):
        merged = dm._reconcile_rows(self._frames())
        row = merged.iloc[0]
        self.assertEqual(row["projection"], 210.0)      # newer wins where both have a value
        self.assertEqual(row["proj_3yr"], 600.0)        # older supplies what newer lacks
        self.assertEqual(row["trade_value"], 40.0)

    def test_recency_decides_before_the_filename_does(self):
        # "a_newer.csv" sorts before "b_older.csv", so a filename tiebreak would pick the wrong
        # one. Precedence is basis confidence, then source_date; filename is a last resort only.
        merged = dm._reconcile_rows(self._frames())
        self.assertEqual(merged.iloc[0]["projection"], 210.0)

    def test_every_field_carries_the_source_that_produced_it(self):
        merged = dm._reconcile_rows(self._frames())
        row = merged.iloc[0]
        self.assertEqual(row["projection_source"], "a_newer.csv")
        self.assertEqual(row["proj_3yr_source"], "b_older.csv")


class ConflictLedgerTests(unittest.TestCase):
    """A merge that silently discards a value has not succeeded. 1084 field-level conflicts
    were being resolved every load with no record of any of them."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    def test_the_merger_exposes_what_it_resolved(self):
        self.assertTrue(hasattr(self.merger, "reconciliation_conflicts"))
        self.assertIsInstance(self.merger.reconciliation_conflicts, list)

    def test_a_recorded_conflict_names_the_field_the_player_and_both_sources(self):
        for conflict in self.merger.reconciliation_conflicts[:20]:
            for key in ("player", "field", "chosen_source", "chosen_value",
                        "discarded_source", "discarded_value", "reason"):
                self.assertIn(key, conflict)

    def test_a_filename_tiebreak_is_recorded_as_arbitrary_when_it_decides(self):
        arbitrary = [c for c in self.merger.reconciliation_conflicts
                     if c.get("reason") == "filename"]
        for conflict in arbitrary:
            self.assertIn("arbitrary", conflict.get("note", "").lower())


class HorizonStateTests(unittest.TestCase):
    """Three states, not two. _has_3yr collapsed "not applicable" and "unknown" into one False;
    both correctly get a zero adjustment, but the engine could not say whether a position was
    structurally horizon-free or merely unmeasured -- the distinction that decides whether
    restoring data is even possible."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    def test_a_team_defense_is_not_applicable_by_declared_domain(self):
        rows = self.merger.projections[self.merger.projections["position"] == "DEF"]
        self.assertFalse(rows.empty)
        self.assertEqual(set(rows["proj_3yr_state"]), {"not_applicable"})

    def test_a_kicker_is_unknown_not_not_applicable(self):
        # A kicker has a career arc. The figure exists -- on the vendor basis, which does not
        # price this position -- so it is unmeasured here, not inapplicable.
        rows = self.merger.projections[self.merger.projections["position"] == "K"]
        self.assertFalse(rows.empty)
        self.assertEqual(set(rows["proj_3yr_state"]), {"unknown"})

    def test_an_offensive_player_with_a_figure_is_known(self):
        rows = self.merger.projections[
            (self.merger.projections["position"] == "WR")
            & self.merger.projections["proj_3yr"].notna()
        ]
        self.assertFalse(rows.empty)
        self.assertEqual(set(rows["proj_3yr_state"]), {"known"})

    def test_every_non_known_state_carries_a_reason(self):
        proj = self.merger.projections
        unexplained = proj[(proj["proj_3yr_state"] != "known")
                           & (proj["proj_3yr_reason"].isna() | (proj["proj_3yr_reason"] == ""))]
        self.assertTrue(unexplained.empty)

    def test_known_implies_a_value_and_the_converse(self):
        proj = self.merger.projections
        self.assertTrue((proj[proj["proj_3yr_state"] == "known"]["proj_3yr"].notna()).all())
        self.assertTrue((proj[proj["proj_3yr_state"] != "known"]["proj_3yr"].isna()).all())


class NoCrossBasisHorizonTests(unittest.TestCase):
    """The measured 1.43x: a horizon figure may only sit beside a season figure from its own
    basis. This is the invariant that makes "restore the missing field" the wrong repair."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    def test_projection_and_proj_3yr_always_share_a_basis(self):
        proj = self.merger.projections
        both = proj[proj["projection"].notna() & proj["proj_3yr"].notna()]
        self.assertFalse(both.empty)
        for _, row in both.iterrows():
            self.assertEqual(dm.measurement_basis(row["projection_source"]),
                             dm.measurement_basis(row["proj_3yr_source"]),
                             row["name"])

    def test_no_kicker_carries_a_vendor_horizon_beside_a_transcribed_season(self):
        kickers = self.merger.projections[self.merger.projections["position"] == "K"]
        self.assertTrue(kickers["proj_3yr"].isna().all())


if __name__ == "__main__":
    unittest.main()


class ReconciliationIsScopedToRankingsTests(unittest.TestCase):
    """Caught by the regression suite, and the failure class is worth pinning: a reconciliation
    built for one schema was applied to another.

    The rankings reconciliation assumes every row is a player with a position and a possible
    multi-year outlook. The trade-value chart holds rookie pick slots ("1.01") and future picks
    ("2027 Random Rd 1") that have no position at all, and no horizon dimension anywhere.
    Routing it through _merge_rankings dropped all 58 non-player assets -- pick_value() went to
    None and every future-pick price in the rookie draft tool died with it -- and stamped a
    proj_3yr_state onto a table that has no proj_3yr to have a state about."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    def test_non_player_assets_survive_the_load(self):
        assets = set(self.merger.trade_values["asset_type"])
        self.assertIn("rookie_pick_slot", assets)
        self.assertIn("future_pick", assets)

    def test_a_rookie_pick_slot_is_still_priceable(self):
        self.assertIsNotNone(self.merger.pick_value("1.01"))

    def test_the_chart_does_not_acquire_a_horizon_it_has_no_dimension_for(self):
        leaked = [c for c in self.merger.trade_values.columns
                  if c.startswith("proj_3yr") or c == "measurement_basis"]
        self.assertEqual(leaked, [])


class APositionlessRowIsNotADuplicateOfEveryOtherOneTests(unittest.TestCase):
    """#52 phase 6. The within-file identity key NA-collapsed every row that has no position.

    load_all deduplicates inside each file on `norm_name + "|" + position`. `position` arrives
    as pandas' `str` dtype, where `astype(str)` leaves a missing value as NA rather than turning
    it into the string "nan" -- and NA propagates through `+`, so every positionless row got the
    SAME null key. `drop_duplicates` treats nulls as equal to one another, so they all collapsed
    onto one row.

    The trade-value chart is exactly that table: 48 rookie pick slots and 10 future picks carry
    no position at all. All 58 became 1. `pick_value("1.01")` kept working only because the one
    surviving row happened to be a rookie slot, and every future-pick price in the rookie draft
    tool returned None -- the same damage the class above documents from an earlier cause, which
    is why that class's tests did not catch this one: they assert the ASSET TYPES survive, and
    one row of each type did.

    It reproduces only through the real loader. Reading the same CSV with a bare pd.read_csv
    gives an object-dtype column, where astype(str) does produce "nan" and the keys stay
    distinct -- a probe built that way reports the code is fine. So these build through
    load_all, and one asserts the dtype directly so the premise cannot rot silently.
    """

    def _load(self, rows: str):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "chart.csv"
            path.write_text(
                "asset_type,name,position,value,source_league_type,source_scoring,source_date\n" + rows)
            _, _, tvc = dm.load_all(Path(tmp), default_kind="trade_value_chart")
            return tvc

    def test_positionless_rows_with_distinct_names_all_survive(self):
        tvc = self._load(
            "rookie_pick_slot,1.01,,83,Dynasty,PPR,2026-08-20\n"
            "rookie_pick_slot,1.02,,40,Dynasty,PPR,2026-08-20\n"
            "rookie_pick_slot,1.03,,35,Dynasty,PPR,2026-08-20\n"
            "future_pick,2027 Random Rd 1,,29,Dynasty,PPR,2026-08-20\n"
            "future_pick,2028 Random Rd 1,,27,Dynasty,PPR,2026-08-20\n")
        self.assertEqual(len(tvc), 5, "positionless rows collapsed onto one another")
        self.assertEqual(sorted(tvc["name"]),
                         ["1.01", "1.02", "1.03", "2027 Random Rd 1", "2028 Random Rd 1"])

    def test_the_premise_holds_a_missing_position_really_is_NA_not_the_string_nan(self):
        # If this ever fails, the defect above became unreproducible for a reason worth knowing
        # about rather than because the key was fixed -- so it is asserted, not assumed.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "chart.csv"
            path.write_text(
                "asset_type,name,position,value,source_league_type,source_scoring,source_date\n"
                "rookie_pick_slot,1.01,,83,Dynasty,PPR,2026-08-20\n")
            df, _ = dm.load_projection_file(path, default_kind="trade_value_chart")
        self.assertTrue(df["position"].isna().all())
        self.assertTrue(pd.isna(df["position"].astype(str).iloc[0]),
                        "astype(str) now yields a real string; the NA-propagation premise moved")

    def test_a_genuine_within_file_duplicate_still_collapses(self):
        # The key was made null-SAFE, not null-blind: two rows that really are the same asset
        # still collapse, or the repair would have traded one defect for its opposite.
        tvc = self._load(
            "rookie_pick_slot,1.01,,83,Dynasty,PPR,2026-08-20\n"
            "rookie_pick_slot,1.01,,84,Dynasty,PPR,2026-08-20\n"
            "future_pick,2027 Random Rd 1,,29,Dynasty,PPR,2026-08-20\n")
        self.assertEqual(len(tvc), 2)

    def test_the_committed_chart_keeps_every_asset_its_own_file_declares(self):
        # Derived from the file rather than pinned as a census number, so it tracks the data.
        raw = pd.read_csv("data/baseline/trade_value/dynasty_ppr_trade_value_chart.csv")
        loaded = dm.DataMerger().trade_values
        for kind, expected in raw["asset_type"].value_counts().items():
            with self.subTest(asset_type=kind):
                self.assertEqual(int((loaded["asset_type"] == kind).sum()), int(expected))
