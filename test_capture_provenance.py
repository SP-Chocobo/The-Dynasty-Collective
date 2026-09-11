"""A league capture reads as observation. Two of its fields are not, and this file proves it.

THE HAZARD. `data/league_captures/*.json` declare a capture_method of "transcribed from Sleeper
screenshots supplied by the owner". A reader -- or an instrument -- takes the whole file as
evidence about the league. For `starter_slot_counts` and `league_starters` that is false: both
are this repository's OWN engine output, written into the file. The engine can then read back
its own hand-set SUPER_FLEX_QB_SHARE as though the league had confirmed it. #56 forbids exactly
that shape; #216 owns the constant. What this file adds is that the leak cannot go quiet.

THE LABELS ARE NOT TRUSTED. Every classification in draft_math.PROVENANCE is re-derived here:
a "derived_cached" field is recomputed from the capture's own primary fields, and an
"engine_derived" field is reproduced by CALLING THE ENGINE. A label that is merely asserted is
a comment; a label a test can reproduce is a fact.

WHEN THE ENGINE_DERIVED GUARD FAILS -- because someone changed SUPER_FLEX_QB_SHARE -- the
correct repair is to DELETE the field from the capture, not to refresh it. Refreshing it
re-entrenches an engine constant inside a file that claims to be observation. That instruction
lives in the capture too, so it travels with the data rather than only with this test.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import draft_room as dr
import league_config as lc

CAPTURES = sorted(Path("data/league_captures").glob("*.json"))


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _with_draft_math():
    for path in CAPTURES:
        cap = _load(path)
        if isinstance(cap.get("draft_math"), dict):
            yield path.name, cap


class EveryCaptureFieldIsClassified(unittest.TestCase):
    def test_there_is_at_least_one_capture_to_check(self):
        """A rate over an empty set is not a rate."""
        self.assertGreaterEqual(len(list(_with_draft_math())), 2)

    def test_no_draft_math_field_is_unclassified(self):
        """Derived, not hand-listed: the check walks the FILE's keys, so a field added later
        without a classification fails here instead of being silently assumed observed."""
        for name, cap in _with_draft_math():
            dm = cap["draft_math"]
            fields = dm["PROVENANCE"]["fields"]
            for key in dm:
                self.assertIn(key, fields, f"{name}: draft_math.{key} carries no provenance")

    def test_every_classification_is_one_of_the_declared_classes(self):
        for name, cap in _with_draft_math():
            prov = cap["draft_math"]["PROVENANCE"]
            for key, cls in prov["fields"].items():
                self.assertIn(cls, prov["_CLASSES"], f"{name}: {key} -> unknown class {cls!r}")


class DerivedCachedFieldsStillRecompute(unittest.TestCase):
    """These are cached copies of arithmetic over the primary fields. Cached values go stale.

    Every guard in this file skips a field that is ABSENT. Deleting a leaked field is the
    documented correct repair, so it must PASS -- an earlier version of this file failed it,
    which would have pushed a future reader toward refreshing the number instead. What stays
    caught is the field being PRESENT and wrong.
    """

    def test_draftable_slots_per_team(self):
        for name, cap in _with_draft_math():
            dm = cap["draft_math"]
            if "draftable_slots_per_team" not in dm:
                continue          # correctly removed; absence is not a failure
            if dm["PROVENANCE"]["fields"].get("draftable_slots_per_team") != "derived_cached":
                continue
            self.assertEqual(dm["draftable_slots_per_team"],
                             len(lc.draftable_slots(cap["roster_positions"])), name)

    def test_total_picks_if_startup(self):
        for name, cap in _with_draft_math():
            dm = cap["draft_math"]
            if "total_picks_if_startup" not in dm:
                continue
            if dm["PROVENANCE"]["fields"].get("total_picks_if_startup") != "derived_cached":
                continue
            self.assertEqual(dm["total_picks_if_startup"],
                             dm["draftable_slots_per_team"] * cap["total_rosters"], name)


class TheEngineDerivedFieldsAreReallyTheEngines(unittest.TestCase):
    """The load-bearing half. This does not assert the label -- it reproduces the number by
    running the engine, which is what makes "an engine constant in disguise" a measurement."""

    def test_starter_slot_counts_is_reproduced_by_draft_room(self):
        checked = 0
        for name, cap in _with_draft_math():
            dm = cap["draft_math"]
            if "starter_slot_counts" not in dm:
                continue
            if dm["PROVENANCE"]["fields"].get("starter_slot_counts") != "engine_derived":
                continue
            engine = dr.starter_slot_counts(cap["roster_positions"])
            for pos, stored in dm["starter_slot_counts"].items():
                self.assertAlmostEqual(stored, engine[pos], places=6,
                                       msg=f"{name}: {pos} no longer matches the engine")
            checked += 1
        self.assertGreater(checked, 0, "no capture exercised this guard")

    def test_the_stored_superflex_share_IS_the_engines_hand_set_constant(self):
        """The specific leak, named rather than implied. QB's count above its literal slot count
        is exactly SUPER_FLEX_QB_SHARE per SUPER_FLEX slot -- a number nothing in these leagues
        was ever observed to confirm."""
        for name, cap in _with_draft_math():
            dm = cap["draft_math"]
            if "starter_slot_counts" not in dm:
                continue
            if dm["PROVENANCE"]["fields"].get("starter_slot_counts") != "engine_derived":
                continue
            rp = cap["roster_positions"]
            sf = rp.count("SUPER_FLEX")
            if not sf:
                continue
            excess_per_sf = (dm["starter_slot_counts"]["QB"] - rp.count("QB")) / sf
            self.assertAlmostEqual(excess_per_sf, dr.SUPER_FLEX_QB_SHARE, places=6, msg=name)

    def test_league_starters_is_that_same_engine_output_times_the_league_size(self):
        for name, cap in _with_draft_math():
            dm = cap["draft_math"]
            if "league_starters" not in dm:
                continue
            if dm["PROVENANCE"]["fields"].get("league_starters") != "engine_derived":
                continue
            for pos, stored in dm["league_starters"].items():
                self.assertAlmostEqual(
                    stored, dm["starter_slot_counts"][pos] * cap["total_rosters"],
                    places=6, msg=f"{name}: {pos}")


class TheLabelCannotDemoteItself(unittest.TestCase):
    """The gap the mutation pass found, closed.

    Every guard above is GATED ON THE LABEL: relabel `starter_slot_counts` from
    "engine_derived" to "observed" and all of them quietly skip it. That is precisely the move
    someone makes to turn a red test green, and it would restore the original defect -- an
    engine constant sitting in a capture, now with a label saying it was observed.

    So this test does not read the label first. It asks the ENGINE what it would produce, finds
    any draft_math field that matches, and requires THAT field to be labelled engine_derived.
    Reproducibility by the engine is the evidence; the label has to agree with it.
    """

    def _engine_shapes(self, cap: dict) -> dict:
        counts = dr.starter_slot_counts(cap["roster_positions"])
        teams = cap["total_rosters"]
        return {
            "counts": counts,
            "times_teams": {k: v * teams for k, v in counts.items()},
        }

    @staticmethod
    def _matches(stored, engine) -> bool:
        if not isinstance(stored, dict) or not stored:
            return False
        return all(
            isinstance(v, (int, float))
            and k in engine
            and abs(v - engine[k]) < 1e-6
            for k, v in stored.items()
        )

    def test_anything_the_engine_reproduces_must_be_labelled_engine_derived(self):
        flagged = 0
        for name, cap in _with_draft_math():
            dm = cap["draft_math"]
            shapes = self._engine_shapes(cap)
            for key, value in dm.items():
                if key == "PROVENANCE":
                    continue
                for shape_name, engine in shapes.items():
                    if self._matches(value, engine):
                        self.assertEqual(
                            dm["PROVENANCE"]["fields"].get(key), "engine_derived",
                            f"{name}: draft_math.{key} is reproduced exactly by the engine "
                            f"({shape_name}) but is not labelled engine_derived",
                        )
                        flagged += 1
        self.assertGreaterEqual(flagged, 2, "the engine reproduced nothing -- guard is vacuous")


class TheRepairInstructionTravelsWithTheData(unittest.TestCase):
    def test_the_capture_says_delete_not_refresh(self):
        """If this guidance lived only in this test file, a future reader fixing a red test would
        never see it -- and refreshing the number is the wrong repair."""
        for name, cap in _with_draft_math():
            guidance = cap["draft_math"]["PROVENANCE"]["_IF_THE_GUARD_FAILS"]
            self.assertIn("DELETE", guidance, name)


if __name__ == "__main__":
    unittest.main()
