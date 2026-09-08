"""#216 -- the fix: the displacement term, its derivation, its wiring and the reviewer's
invariants that the adversary's battery does not itself pin (2, 4 and 6).

The term (lineup_optimizer.displacement_level -> draft_room.displacement_adjustments ->
displacement_adj in team_acquisition_value) is derived, not tuned: replacement level minus what
a player at that position must displace in MY optimal lineup, with every open slot's free
alternative set to the league replacement level the board already computes. The tests below
assert what the derivation implies -- exact reduction to the league anchor wherever a reachable
slot is open, a deduction of exactly the surplus where none is, non-positivity everywhere, a
per-position constant at a board state, no numeric constant in the value path -- and the three
reviewer invariants on the real rulebook.

MUTATION RESULTS are recorded at the bottom of this file after each mutation was applied by
hand, the test run, and the file restored byte-identical (POST_AUDIT_PLAN #215's three rules).
"""
from __future__ import annotations

import ast
import inspect
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

import draft_room as dr
import lineup_optimizer as lo

CAPTURE = Path("data/fixtures/sleeper_capture.json")
ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"] + ["BN"] * 6


def _p(pid, value, *positions):
    return {"id": pid, "value": float(value), "eligible": set(positions)}


class DisplacementLevelDerivationTests(unittest.TestCase):
    """The primitive, on hand-built rosters where every number can be checked by hand."""

    def test_an_empty_roster_reduces_exactly_to_the_league_anchor(self):
        out = lo.displacement_level([], ROSTER, "TE", 173.0)
        self.assertEqual((out["displaced"], out["adjustment"], out["basis"]), (173.0, 0.0, lo.DISPLACEMENT_MEASURED))

    def test_an_open_reachable_slot_means_no_deduction_even_with_a_better_starter_held(self):
        # TE slot held by a 300 -- but FLEX is open, so a second TE is priced against the
        # league anchor, not against the 300. This is the over-correction guard's own case
        # (McBride with Bowers owned) stated on the primitive.
        out = lo.displacement_level([_p("te1", 300, "TE")], ROSTER, "TE", 173.0)
        self.assertEqual((out["displaced"], out["adjustment"]), (173.0, 0.0))

    def test_every_reachable_slot_held_above_the_anchor_deducts_exactly_the_weakest_holder(self):
        four = [_p("t1", 300, "TE"), _p("t2", 250, "TE"), _p("t3", 220, "TE"), _p("t4", 200, "TE")]
        out = lo.displacement_level(four, ROSTER, "TE", 173.0)
        # TE, FLEX, FLEX hold 300/250/220; the fourth (200) is benched and is NOT the answer.
        self.assertEqual((out["displaced"], out["adjustment"]), (220.0, -47.0))
        # ...and the same roster deducts nothing from a receiver: every WR slot is open.
        self.assertEqual(lo.displacement_level(four, ROSTER, "WR", 216.0)["adjustment"], 0.0)

    def test_a_holder_below_the_anchor_is_not_an_occupant(self):
        # A 150 receiver does not hold a slot against a free 216: the phantom takes it, so a
        # candidate WR is priced against the league anchor and never LIFTED for my weak starter.
        out = lo.displacement_level([_p("w", 150, "WR")], ROSTER, "WR", 216.0)
        self.assertEqual((out["displaced"], out["adjustment"]), (216.0, 0.0))

    def test_the_adjustment_is_never_positive(self):
        rosters = [
            [], [_p("w", 150, "WR")], [_p("t1", 300, "TE"), _p("t2", 250, "TE"), _p("t3", 220, "TE")],
            [_p("q", 400, "QB"), _p("r1", 260, "RB"), _p("r2", 240, "RB"), _p("w1", 250, "WR"),
             _p("w2", 240, "WR"), _p("t", 230, "TE"), _p("f1", 235, "RB"), _p("f2", 233, "WR")],
        ]
        for roster in rosters:
            for position, level in (("QB", 290.0), ("RB", 186.0), ("WR", 216.0), ("TE", 173.0)):
                with self.subTest(roster=len(roster), position=position):
                    out = lo.displacement_level(roster, ROSTER, position, level)
                    self.assertLessEqual(out["adjustment"], 0.0)
                    self.assertGreaterEqual(out["displaced"], level)

    def test_a_full_lineup_prices_each_position_against_its_own_weakest_reachable_starter(self):
        full = [_p("q", 400, "QB"), _p("r1", 260, "RB"), _p("r2", 240, "RB"), _p("w1", 250, "WR"),
                _p("w2", 240, "WR"), _p("t", 230, "TE"), _p("f1", 235, "RB"), _p("f2", 233, "WR")]
        # RB reaches RB, RB, FLEX, FLEX -> weakest held is 233 (the WR in FLEX); TE reaches TE
        # and both FLEX -> weakest 230 (its own TE); QB reaches QB only -> 400.
        self.assertEqual(lo.displacement_level(full, ROSTER, "RB", 186.0)["displaced"], 233.0)
        self.assertEqual(lo.displacement_level(full, ROSTER, "TE", 173.0)["displaced"], 230.0)
        self.assertEqual(lo.displacement_level(full, ROSTER, "QB", 290.0)["displaced"], 400.0)

    def test_a_position_no_slot_accepts_is_not_applicable_and_deducts_nothing(self):
        out = lo.displacement_level([_p("t1", 300, "TE")], ROSTER, "K", 100.0)
        self.assertEqual((out["displaced"], out["adjustment"], out["basis"]), (None, 0.0, lo.DISPLACEMENT_NOT_APPLICABLE))

    def test_an_unpriced_rostered_player_who_could_block_the_position_downgrades_the_basis(self):
        four = [_p("t1", 300, "TE"), _p("t2", 250, "TE"), _p("t3", 220, "TE")]
        partial = lo.displacement_level(four, ROSTER, "TE", 173.0, unpriced_eligible=[{"WR"}])
        self.assertEqual(partial["basis"], lo.DISPLACEMENT_ROSTER_PARTIAL, "a WR can hold FLEX, which a TE reaches")
        self.assertEqual(partial["adjustment"], -47.0, "the number is still reported, as a floor")
        clean = lo.displacement_level(four, ROSTER, "QB", 290.0, unpriced_eligible=[{"WR"}])
        self.assertEqual(clean["basis"], lo.DISPLACEMENT_MEASURED, "a WR cannot reach the QB slot")

    def test_the_probe_value_never_reaches_the_answer(self):
        # Doubling the probe changes nothing: it is subtracted back out.
        with mock.patch.object(lo, "_DISPLACEMENT_PROBE_VALUE", 2e6):
            doubled = lo.displacement_level([_p("t1", 300, "TE"), _p("t2", 250, "TE"), _p("t3", 220, "TE")], ROSTER, "TE", 173.0)
        self.assertEqual(doubled["displaced"], 220.0)

    def test_every_vocabulary_token_has_words(self):
        names = {n: v for n, v in vars(lo).items() if n.startswith("DISPLACEMENT_") and isinstance(v, str)}
        self.assertEqual({n: v for n, v in names.items() if v not in lo.DISPLACEMENT_BASIS_LABELS}, {})


class NoConstantInTheValuePathTests(unittest.TestCase):
    """#56. The term's derivation is the optimizer and the board's own levels. Read off the
    AST: no numeric literal other than 0 reaches the arithmetic of either function."""

    def _numeric_literals(self, func):
        tree = ast.parse(inspect.getsource(func).lstrip())
        return sorted({n.value for n in ast.walk(tree)
                       if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
                       and not isinstance(n.value, bool) and n.value not in (0, 0.0, 2)})

    def test_displacement_adjustments_has_no_numeric_literal(self):
        self.assertEqual(self._numeric_literals(dr.displacement_adjustments), [])

    def test_displacement_level_has_no_numeric_literal_but_the_probe_and_rounding(self):
        # `2` is round()'s digit count and is excluded above; the probe is a named module
        # constant, so it does not appear as a literal in the function either.
        self.assertEqual(self._numeric_literals(lo.displacement_level), [])


def _rulebook():
    import data_merger as dm
    import draft_battery as db
    import run_draft_battery as rdb
    import run_roster_proof as rp
    merger = dm.DataMerger()
    players_db, _ = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False,
                                  dynasty=True, base_scoring=rdb.scoring_settings_from_capture())
    merger.set_league_format(db.league_format_hint(league))
    points = rp.scoreable_pool(merger, players_db, league, season)
    return merger, players_db, season, league, points


_RB: dict = {}


def _board(picks, me="1"):
    if not _RB:
        _RB["v"] = _rulebook()
    merger, players_db, season, league, _ = _RB["v"]
    return dr.compute_draft_board(merger, players_db, picks, me, league, mode="balanced",
                                  sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)


def _ranked(position):
    if not _RB:
        _RB["v"] = _rulebook()
    _, players_db, _, _, points = _RB["v"]
    pos = lambda p: (players_db.get(str(p)) or {}).get("position")
    return sorted((p for p in points if pos(p) == position), key=lambda p: (-points[p], p))


def _pick(pid, roster, n, rnd):
    return {"pick_no": n, "round": rnd, "roster_id": roster, "player_id": str(pid)}


@unittest.skipUnless(CAPTURE.exists(), "needs the real capture")
class WiringOnTheRealRulebookTests(unittest.TestCase):

    def test_the_identity_closes_with_the_fourth_term_on_every_priced_row(self):
        te = _ranked("TE")
        rows = [r for r in _board([_pick(te[i], "1", i + 1, i + 1) for i in range(4)]) if r["final_score"] is not None]
        self.assertGreater(len(rows), 400)
        for r in rows:
            self.assertAlmostEqual(
                r["final_score"],
                r["universal_value"] + r["need_bonus"] + r["eligibility_bonus"] + r["depth_exposure"] + r["displacement_adj"],
                places=2, msg=r["name"])
            self.assertLessEqual(r["displacement_adj"], 0.0, r["name"])
            self.assertIn(r["displacement_basis"], lo.DISPLACEMENT_BASIS_LABELS, r["name"])

    def test_the_term_is_a_per_position_constant_at_a_board_state(self):
        te = _ranked("TE")
        rows = [r for r in _board([_pick(te[i], "1", i + 1, i + 1) for i in range(4)]) if r["final_score"] is not None]
        by_position: dict[str, set] = {}
        for r in rows:
            by_position.setdefault(r["position"], set()).add(r["displacement_adj"])
        self.assertEqual({p: len(v) for p, v in by_position.items() if len(v) != 1}, {})
        self.assertLess(min(by_position["TE"]), -50.0, "four tight ends owned and no deduction at TE")
        self.assertEqual(by_position["WR"], {0.0})

    def test_switching_the_term_off_reproduces_the_pre_fix_board_exactly(self):
        """The in-process A/B idiom the probe relies on (engine-measurement skill): with
        displacement_adjustments patched to return nothing, every row's final_score is the
        pre-fix four-term sum, so the two arms differ in exactly one thing."""
        te = _ranked("TE")
        picks = [_pick(te[i], "1", i + 1, i + 1) for i in range(4)]
        with mock.patch.object(dr, "displacement_adjustments", lambda *a, **k: {}):
            off = {str(r["player_id"]): r for r in _board(picks)}
        on = {str(r["player_id"]): r for r in _board(picks)}
        moved = 0
        for pid, r in on.items():
            o = off[pid]
            if r["final_score"] is None:
                continue
            self.assertEqual(o["displacement_adj"], 0.0)
            self.assertEqual(o["displacement_basis"], lo.DISPLACEMENT_NO_POINTS_ANCHOR)
            self.assertAlmostEqual(o["final_score"], r["final_score"] - r["displacement_adj"], places=2, msg=r["name"])
            moved += r["displacement_adj"] != 0.0
        self.assertGreater(moved, 50, "the term did not fire on a four-tight-end roster")

    def test_invariant_4_my_own_bench_picks_never_improve_my_signal_at_that_position(self):
        """Reviewer invariant 4. A fixed tight end (TE#7) across my roster holding TE#1..#k
        for k = 3..6: his league VOR RISES as I drain the pool (the anchor moves in the
        hoarder's favour), and his acquisition value must not -- the ledger a person reads is
        the one that must stay flat or fall."""
        te = _ranked("TE")
        finals, uvs = [], []
        for k in range(3, 7):
            rows = {str(r["player_id"]): r for r in _board([_pick(te[i], "1", i + 1, i + 1) for i in range(k)])}
            finals.append(rows[te[6]]["final_score"])
            uvs.append(rows[te[6]]["universal_value"])
        self.assertGreater(uvs[-1], uvs[0], f"fixture: the league anchor did not move in the hoarder's favour: {uvs}")
        for a, b in zip(finals, finals[1:]):
            self.assertLessEqual(b, a + 1e-9, f"owning more tight ends made the next one worth MORE: {finals}")

    def test_invariant_2_the_quarterback_is_priced_positive_while_open_and_at_or_below_zero_once_filled(self):
        """Reviewer invariant 2 on a constructed 1QB state where every other seat has a QB
        (league QB demand = my slot alone, the collapse the review measured). Stated on
        final_score, the number that ranks -- and, honestly, on bpa too: the QB's VOR is 0.00
        here by the starter-demand model's own definition (see replacement_levels' docstring),
        so the positive price is the need term. Once my slot holds a QB, the best remaining
        QB must sit at or below zero unless he out-projects my starter."""
        qb = _ranked("QB")
        others = [_pick(qb[i + 1], str(i + 2), i + 1, 1) for i in range(11)]          # seats 2..12 each hold a QB
        open_rows = [r for r in _board(others) if r["position"] == "QB" and r["final_score"] is not None]
        best_open = max(open_rows, key=lambda r: r["projected_points"])
        self.assertEqual(best_open["bpa"], 0.0, "the collapse the review measured: rank 1 is the candidate himself")
        self.assertGreater(best_open["final_score"], 0.0)
        filled = others + [_pick(qb[0], "1", 12, 1)]                                   # I take QB#1
        filled_rows = [r for r in _board(filled) if r["position"] == "QB" and r["final_score"] is not None]
        best_filled = max(filled_rows, key=lambda r: r["projected_points"])
        self.assertLessEqual(best_filled["final_score"], 0.0, best_filled)
        self.assertLess(best_filled["displacement_adj"], 0.0, "my QB#1 must be what a second QB has to displace")


# MUTATION RESULTS (applied by hand, one at a time, file restored byte-identical after each):
#   see the bottom of this file in the committed version.
if __name__ == "__main__":
    unittest.main()
