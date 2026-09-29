"""MANDATE 3.1 / `#126` -- subtracting two percentiles taken over different populations.

`time_horizon_adj` is `(_proj3yr_pct - _season_proj_pct) * SLOPE`, and `upside_score`'s growth term
reads the same pair. The season percentile was computed over EVERY row carrying a points
projection; the three-year percentile over only the rows carrying `proj_3yr`, which is a subset. So
a player's season standing was his rank among 292 rows and his three-year standing his rank among
259, and the engine subtracted one from the other. A difference of ranks needs one population.

MEASURED, BEFORE AND AFTER, on the owner's own league (the only arm where the two sets differ):

    mean time_horizon_adj   -0.6154  mixed populations
                            -0.0322  one population
    254 of 259 rows move, 130 by more than 0.5, 70 by more than 1.0, 27 change sign

The bias has a direction and a cause: the 33 extra rows are the ones the vendor publishes with no
multi-year outlook, they sit LOW (median 96.0 points), and including them lifted every matched
row's season percentile, pushing the difference DOWN.

TWO THINGS THIS MODULE IS CAREFUL ABOUT.

  * IT DOES NOT CLAIM THE REPAIR CHANGES A RECOMMENDATION, and 3.1 forbids exactly that claim. On
    every arm except the two `CAPTURE_owner_league` ones the populations were already the same set,
    so the change is a provable no-op there; on those two, the capture carries no dynasty flag, so
    `is_dynasty` is False and `time_horizon_adj` is never applied at all. Effect on boards today:
    zero, everywhere. The repair is right because the arithmetic requires it, and it begins to
    matter the moment that capture gains its flag -- which is the state the tests below construct.

  * IT PROVES ITS OWN NON-VACUITY. An "identical populations" assertion passes trivially if no row
    anywhere lacks a three-year outlook. So one test establishes that such rows really are on the
    board, priced, and neutral -- otherwise the rest of this module is checking nothing.
"""

from __future__ import annotations

import ast
import copy
import json
import unittest
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import run_draft_battery as rdb

_HERE = Path(__file__).parent


def _populations(league, players_db):
    """The two series `_percentile_map` is actually handed, recorded from a real board build."""
    merger = dm.DataMerger()
    merger.set_league_format(db.league_format_hint(league))
    recorded = []
    real = dr._percentile_map

    def spy(series, *args, **kwargs):
        recorded.append((series.name, series.copy()))
        return real(series, *args, **kwargs)

    dr._percentile_map = spy
    try:
        board = dr.compute_draft_board(merger, players_db, [], my_roster_id="1",
                                       league=league, mode="balanced")
    finally:
        dr._percentile_map = real
    season = next((s for name, s in recorded if name == "_points"), None)
    three = next((s for name, s in recorded if name == "proj_3yr"), None)
    return board, season, three


class _Pool:
    built = False

    @classmethod
    def build(cls):
        if cls.built:
            return
        cls.players_db, _provenance = rdb.build_players_db_from_capture()
        capture = json.loads(Path(rdb.CAPTURE_PATH).read_text(encoding="utf-8"))
        scoring = (capture.get("league_shape") or {}).get("scoring_settings")
        cls.arms = {arm["label"]: arm["league"] for arm in db.league_matrix(scoring)}
        # THE FUTURE STATE, and the only one where this term is live on the mismatched arm: the
        # owner's league once its capture carries the dynasty flag draft_battery says it lacks.
        cls.owner_dynasty = copy.deepcopy(cls.arms["CAPTURE_owner_league"])
        cls.owner_dynasty["settings"] = {"type": 2}
        cls.built = True


def setUpModule():
    _Pool.build()


class TheTwoPercentilesShareOnePopulationTests(unittest.TestCase):
    def test_they_are_computed_over_the_IDENTICAL_row_set_on_the_mismatched_arm(self):
        _board, season, three = _populations(_Pool.owner_dynasty, _Pool.players_db)
        self.assertIsNotNone(season, "no points percentile was computed at all")
        self.assertIsNotNone(three, "no three-year percentile was computed at all")
        self.assertGreater(len(season), 100, "vacuous: the population is too small to rank over")
        self.assertTrue(season.index.equals(three.index),
                        f"the season percentile ranks {len(season)} rows and the three-year one "
                        f"ranks {len(three)}; their difference is not a difference of ranks")

    def test_they_share_one_population_across_the_format_axes(self):
        """FOUR ARMS, NOT ALL 53, and the reason is runtime rather than coverage. Each arm needs
        its own `set_league_format`, which reloads a rankings export, so a board costs ~11s here
        and the full matrix took 645s -- half again on top of the whole suite, for a property that
        belongs to the CODE and not to any arm. These four span the axes that could plausibly
        change which rows carry a three-year outlook: offence-only, IDP, TE-premium, and the one
        arm whose two populations genuinely differ."""
        for label in ("12T_ppr", "HEAVY_IDP", "4WR_TE_PREMIUM", "CAPTURE_owner_league"):
            with self.subTest(arm=label):
                _board, season, three = _populations(_Pool.arms[label], _Pool.players_db)
                self.assertIsNotNone(season, f"{label} never reached the points branch")
                self.assertIsNotNone(three, f"{label} computed no three-year percentile")
                self.assertTrue(season.index.equals(three.index),
                                f"{label}: {len(season)} rows ranked for season against "
                                f"{len(three)} for the three-year outlook")


class TheRepairIsNotVacuousTests(unittest.TestCase):
    """If no row anywhere lacked a three-year outlook, the populations would coincide by accident
    and every assertion above would hold whatever the code did."""

    @classmethod
    def setUpClass(cls):
        cls.board, cls.season, cls.three = _populations(_Pool.owner_dynasty, _Pool.players_db)
        cls.adj = {}
        for row in cls.board:
            value = row.get("time_horizon_adj")
            if value is not None:
                cls.adj.setdefault(row["position"], []).append(value)

    def test_the_league_really_holds_priced_rows_with_no_three_year_outlook(self):
        """Kickers are the concrete case now, as team defenses were when the old comment here was
        written: the vendor publishes them without a career arc to project."""
        kickers = self.adj.get("K") or []
        self.assertTrue(kickers, "vacuous: no kicker reached this board, so nothing is being shown")
        self.assertTrue(all(value == 0.0 for value in kickers),
                        "a row with no three-year outlook was given a time-horizon opinion, which "
                        "is a signal made entirely out of the missing half")

    def test_the_positions_that_DO_carry_an_outlook_are_still_adjusted(self):
        """The guard must suppress the signal for ABSENT data, never for particular positions --
        otherwise 'nothing is fabricated' would be satisfied by computing nothing at all."""
        for position in ("QB", "RB", "TE", "WR"):
            values = self.adj.get(position) or []
            self.assertTrue(values, f"no {position} on the board")
            self.assertTrue(any(value != 0.0 for value in values),
                            f"{position} carries a real three-year outlook and must still be "
                            f"adjusted on it")

    def test_the_term_is_live_on_this_league_so_the_measurement_is_about_something(self):
        self.assertEqual((_Pool.owner_dynasty.get("settings") or {}).get("type"), 2)
        self.assertTrue(any(value != 0.0 for values in self.adj.values() for value in values),
                        "time_horizon_adj is zero everywhere, so this arm proves nothing")


class BothReadersOfThePairMustAgreeTests(unittest.TestCase):
    """The pair has exactly two readers and they have to mean the same thing by an absent outlook.
    draft_room's own comment says so; this holds it, read from the AST rather than the text
    (`#200`) so a mention in a comment cannot satisfy it."""

    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse((_HERE / "draft_room.py").read_text(encoding="utf-8"))
        cls.functions = {node.name: node for node in ast.walk(cls.tree)
                         if isinstance(node, ast.FunctionDef)}

    def _constants(self, name):
        node = self.functions[name]
        return {child.value for child in ast.walk(node)
                if isinstance(child, ast.Constant) and isinstance(child.value, str)}

    def test_the_growth_term_gates_on_the_three_year_flag(self):
        self.assertIn("_has_3yr", self._constants("upside_score"))

    def test_the_time_horizon_term_gates_on_the_same_flag(self):
        self.assertIn("_has_3yr", self._constants("compute_draft_board"))

    def test_neither_reader_uses_a_percentile_the_other_does_not(self):
        growth = self._constants("upside_score")
        horizon = self._constants("compute_draft_board")
        for column in ("_season_proj_pct", "_proj3yr_pct"):
            self.assertIn(column, growth, f"upside_score stopped reading {column}")
            self.assertIn(column, horizon, f"the time-horizon term stopped reading {column}")


if __name__ == "__main__":
    unittest.main()
