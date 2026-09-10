"""#222: the cancellation identity, the exact handicap, and the mode asymmetry.

WHY THIS FILE EXISTS. #222 spent a long investigation locating why the engine drafts 32.4%
tight ends against twelve real managers' 15.5%. The answer is arithmetic, and NONE of the three
facts it rests on had a test:

  1. THE CANCELLATION. For a candidate whose reachable slots are all held, the flex phantom is
     `max(level over the positions that slot admits)`, so

         bpa + displacement_adj = (points - level) + (level - phantom) = points - phantom

     The candidate's own positional level CANCELS EXACTLY, and every flex-reachable candidate is
     compared on raw points against one common bar. That is "one slot, one alternative" working.

  2. THE EXACT HANDICAP. `displacement_adj` for such a candidate is `level - phantom`, so the
     quantity a caller removes by dropping the term is exactly `phantom - level`, per position.
     Measured on the owner's real rulebook: WR +0.00 (WR defines the phantom), RB +46.94,
     TE +68.58.

  3. THE MODE ASYMMETRY. `upside_score` is `bpa + UPSIDE_GROWTH_WEIGHT * growth` -- it retains
     bpa at FULL WEIGHT -- while the upside branch zeroes every team-specific term including
     `displacement_adj`. So upside mode removes the half of the pair that cancels the level and
     keeps the half that applies it. That is a composition fact, not a number to tune, and
     nothing pinned it.

These tests pin CURRENT behaviour. They are not a claim that the behaviour is right --
#222's contract investigation found the deep-bench cross-position comparison is UNDEFINED, and
whether a tight end should receive +68.58 over an identical receiver for a bench seat is an
owner's decision that has not been taken. INVERT THESE TESTS ON REPAIR. Do not delete them.

MUTATION RESULTS AT THE BOTTOM.
"""
import unittest

import draft_room as dr

#: The owner's real rulebook shape: ten starters, a dedicated TE, three flexes, one superflex.
FF_SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "FLEX", "SUPER_FLEX"]
#: The levels compute_draft_board actually produced on the real 6,595-player capture under this
#: league's own scoring (derived as projected_points - bpa, both emitted columns).
FF_LEVELS = {"QB": 243.29, "RB": 170.81, "WR": 217.75, "TE": 149.17}


def _held(position, value):
    """A roster body strong enough to hold its slot against the phantom."""
    return {"id": f"{position}-{value}", "value": value, "eligible": {position}}


#: The roster shape that produces the phantom case, and getting this wrong is instructive enough
#: to record: filling EVERY slot with someone strong does NOT produce it. A probe evicts the
#: CHEAPEST thing it can reach, so a roster whose flexes are all held by 370+ players evicts one
#: of those (measured on the first draft of this file: displaced came back 360.0, my own weakest
#: starter, not the 217.75 phantom).
#:
#: The phantom case needs a reachable flex that is OPEN or weakly held -- which is the ordinary
#: mid-draft state, and the dominant one on a real board: `displaced == 217.75` on 103 of 144
#: tight-end observations in the measured window. Here the six dedicated slots are held by players
#: above every phantom, and the three FLEX slots and the SUPER_FLEX are open, so each probe
#: reaches a flex and evicts its phantom.
FULL_ROSTER = [_held("QB", 400.0), _held("RB", 400.0), _held("RB", 390.0),
               _held("WR", 400.0), _held("WR", 390.0), _held("TE", 400.0)]


class TheFlexPhantomIsTheHighestAdmittedLevel(unittest.TestCase):
    """Fact 1's premise. Already pinned for the construction in test_216_shared_slot; pinned here
    against the REAL levels, because the identity's arithmetic depends on which position wins."""

    def test_the_flex_phantom_is_the_best_level_among_RB_WR_TE(self):
        alts = dr.shared_slot_alternatives(FF_LEVELS, FF_SLOTS)
        flex = [v for slot, v in alts.items() if slot.startswith("FLEX")]
        self.assertTrue(flex, "the rulebook has FLEX slots; the seam returned none")
        for v in flex:
            self.assertAlmostEqual(v, max(FF_LEVELS[p] for p in ("RB", "WR", "TE")), places=2)
            self.assertAlmostEqual(v, FF_LEVELS["WR"], places=2)

    def test_the_superflex_phantom_admits_QB_and_so_is_higher(self):
        alts = dr.shared_slot_alternatives(FF_LEVELS, FF_SLOTS)
        sflex = [v for slot, v in alts.items() if slot.startswith("SUPER_FLEX")]
        self.assertTrue(sflex)
        for v in sflex:
            self.assertAlmostEqual(v, FF_LEVELS["QB"], places=2)
            self.assertGreater(v, FF_LEVELS["WR"], "SUPER_FLEX admits QB, so it cannot be WR's")


class TheLevelCancelsAtTheFlex(unittest.TestCase):
    """Fact 1. The load-bearing identity of #222."""

    def setUp(self):
        self.adj = dr.displacement_adjustments(FULL_ROSTER, FF_SLOTS, FF_LEVELS)

    def test_adjustment_is_exactly_level_minus_displaced(self):
        for pos, e in self.adj.items():
            self.assertAlmostEqual(e["adjustment"], FF_LEVELS[pos] - e["displaced"], places=6,
                                   msg=f"{pos}: the term is not level - displaced")

    def test_bpa_plus_adjustment_is_points_minus_displaced_for_any_projection(self):
        """The cancellation, stated as the engine composes it. `points` is arbitrary because the
        identity is about the two anchors, not about any player."""
        for points in (7.4, 75.9, 200.0, 420.0):
            for pos, e in self.adj.items():
                bpa = points - FF_LEVELS[pos]
                self.assertAlmostEqual(bpa + e["adjustment"], points - e["displaced"], places=6,
                                       msg=f"{pos} at {points}: the level did not cancel")

    def test_a_flex_reachable_candidate_is_measured_against_the_CHEAPEST_flex_phantom(self):
        """RB/WR/TE reach both FLEX (phantom 217.75) and SUPER_FLEX (243.29) here. The probe
        evicts the cheaper one, so all three land on the FLEX phantom -- one common bar."""
        phantom = max(FF_LEVELS[p] for p in ("RB", "WR", "TE"))
        for pos in ("RB", "WR", "TE"):
            self.assertAlmostEqual(self.adj[pos]["displaced"], phantom, places=2,
                                   msg=f"{pos} should evict the flex phantom on a full roster")


class TheHandicapIsExactAndDerived(unittest.TestCase):
    """Fact 2. The quantity a caller removes by dropping the term, per position.

    These numbers are DERIVED -- differences of this league's own replacement levels -- not
    chosen. #56: a bound is not a threshold, and neither of these is either.
    """

    def test_the_position_defining_the_phantom_pays_exactly_nothing(self):
        adj = dr.displacement_adjustments(FULL_ROSTER, FF_SLOTS, FF_LEVELS)
        self.assertAlmostEqual(adj["WR"]["adjustment"], 0.0, places=2,
                               msg="WR's level IS the flex phantom, so its charge must be 0.00")

    def test_QB_pays_nothing_too_because_it_defines_the_SUPER_FLEX_phantom(self):
        """The same structure one slot up, and the reason this is a property of the ENGINE rather
        than of receivers: whichever position tops a slot's admitted set pays zero for it."""
        adj = dr.displacement_adjustments(FULL_ROSTER, FF_SLOTS, FF_LEVELS)
        self.assertAlmostEqual(adj["QB"]["adjustment"], 0.0, places=2)

    def test_the_charge_each_position_carries_is_phantom_minus_its_own_level(self):
        adj = dr.displacement_adjustments(FULL_ROSTER, FF_SLOTS, FF_LEVELS)
        phantom = max(FF_LEVELS[p] for p in ("RB", "WR", "TE"))
        for pos, expected in (("WR", 0.00), ("RB", 46.94), ("TE", 68.58)):
            self.assertAlmostEqual(-adj[pos]["adjustment"], phantom - FF_LEVELS[pos], places=2)
            self.assertAlmostEqual(-adj[pos]["adjustment"], expected, places=2,
                                   msg=f"{pos}'s derived handicap moved")

    def test_the_lowest_level_position_carries_the_largest_charge(self):
        """Structural, and the whole point: the position the anchor is most generous to in `bpa`
        is the position charged most by the displacement term. They are a matched pair."""
        adj = dr.displacement_adjustments(FULL_ROSTER, FF_SLOTS, FF_LEVELS)
        by_level = sorted(("RB", "WR", "TE"), key=lambda p: FF_LEVELS[p])
        charges = [-adj[p]["adjustment"] for p in by_level]
        self.assertEqual(charges, sorted(charges, reverse=True),
                         "lowest level must carry the largest charge, or the pair is broken")


class UpsideModeKeepsTheWeightAndDropsTheCounterweight(unittest.TestCase):
    """Fact 3. A COMPOSITION test, deliberately not a test of the number 15 -- the boundary is a
    calibration decision and test_draft_room already pins the literal."""

    def test_upside_score_is_bpa_at_full_weight_plus_growth(self):
        import pandas as pd
        row = pd.Series({"bpa": 40.0, "_has_3yr": False,
                         "_season_proj_pct": None, "_proj3yr_pct": None,
                         "bpa_source": dr.POINTS_VOR_DRAFTSHARKS
                         if hasattr(dr, "POINTS_VOR_DRAFTSHARKS") else None})
        out = dr.upside_score(row)
        self.assertAlmostEqual(out["final_score"], 40.0, places=2,
                               msg="with no growth, upside IS bpa -- unreduced, uncorrected")
        self.assertAlmostEqual(out["growth_signal"], 0.0, places=2)

    def test_growth_enters_at_its_declared_weight_and_bpa_at_one(self):
        """The literal 0.5 is deliberate, and the first draft of this test got it wrong: written
        as `40.0 + dr.UPSIDE_GROWTH_WEIGHT * 20.0` it read the constant from the module, so
        doubling the constant moved BOTH sides and the mutation went uncaught. Same idiom as
        test_auto_mode_switches_to_upside_exactly_at_the_documented_round pinning the literal 15 --
        change it here, on purpose, or not at all."""
        import pandas as pd
        row = pd.Series({"bpa": 40.0, "_has_3yr": True,
                         "_season_proj_pct": 10.0, "_proj3yr_pct": 30.0, "bpa_source": None})
        out = dr.upside_score(row)
        self.assertAlmostEqual(dr.UPSIDE_GROWTH_WEIGHT, 0.5, places=6,
                               msg="UPSIDE_GROWTH_WEIGHT moved; decide that deliberately")
        self.assertAlmostEqual(out["final_score"], 40.0 + 0.5 * 20.0, places=2)
        self.assertAlmostEqual(out["growth_signal"], 20.0, places=1)

    def test_an_absent_bpa_does_not_become_a_number(self):
        """THE LATENT HAZARD. `upside_score` opens `bpa = row.get("bpa") or 0.0`. That is only
        safe because absence in a float column is NaN and bool(NaN) is True, so the NaN
        propagates and `final_score` is NaN-normalized to None downstream. If that column ever
        carried a literal None, an unpriced player would score 0.0 + growth and outrank every
        priced row with negative bpa -- and the real 312-pick cut sits near -142, i.e. almost the
        whole board. Pinned so the accident is visible if it stops holding."""
        import math
        import pandas as pd
        row = pd.Series({"bpa": float("nan"), "_has_3yr": False,
                         "_season_proj_pct": None, "_proj3yr_pct": None, "bpa_source": None})
        out = dr.upside_score(row)
        self.assertTrue(math.isnan(out["final_score"]),
                        "an unpriced row must not leave upside_score carrying a real score")


if __name__ == "__main__":
    unittest.main()
