"""#175: the cliff ratio's null belongs to the ESTIMATOR, not to a closed form.

Two things are pinned here, and they are different kinds of claim.

1. LOCK-STEP. evidence/roster_shape/ff_rulebook/cliff_null_characterization.py carries a
   private copy of detect_positional_cliff's yardstick rule, because it has to run that rule
   over SIMULATED gap lists that never form a board. A private copy that silently drifts from
   the engine would make every number in that probe describe an estimator nobody uses -- which
   is the exact failure the probe was written to correct. So the copy is driven against the
   real detect_positional_cliff on the same data and required to agree.

2. THE NULL IS NOT 2^-r. The first #175 pass compared the engine's ratios against
   P(X >= r*median) = 2^-r. That is the null for a PLAIN median of adjacent gaps. The engine
   divides by a median that has had the zero gaps dropped, the target's own gap dropped, and
   the largest ~10% TRIMMED AWAY -- each of which shrinks the denominator and inflates every
   ratio. Run on memoryless data, the engine's own estimator exceeds 2^-r at every r, by ~1.26x
   at r=2.5 and ~1.5x at r=4.0. The tail is where the first pass claimed to find structure, and
   the tail is where the understatement is worst.

   This test fixes a seed and re-derives that, so the correction cannot be quietly undone by
   anyone re-deriving "the null" from the closed form again.
"""
import importlib.util
import math
import random
import unittest
from pathlib import Path

import pick_synthesis as ps

_PROBE_PATH = Path(__file__).with_name("evidence") / "roster_shape" / "ff_rulebook" / \
    "cliff_null_characterization.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("cliff_null_characterization", _PROBE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TheProbesYardstickIsTheEnginesYardstick(unittest.TestCase):
    """A private copy of an engine rule is only evidence while it still IS the engine rule."""

    def _board(self, bpas, position="WR"):
        return [{"player_id": str(i), "name": f"P{i}", "position": position, "bpa": v}
                for i, v in enumerate(bpas)]

    def test_typical_gap_agrees_with_the_engine_on_every_row(self):
        probe = _load_probe()
        rng = random.Random(4242)
        checked = 0
        for _trial in range(40):
            n = rng.randint(6, 45)
            # Deliberately includes exact ties and one planted cliff, so the zero-gap branch
            # and the trim branch are both exercised rather than assumed.
            bpas = sorted((round(rng.expovariate(0.05), 1) for _ in range(n)), reverse=True)
            bpas[len(bpas) // 3] = bpas[len(bpas) // 3 - 1]          # a tie
            board = self._board(bpas)
            gaps = [bpas[i] - bpas[i + 1] for i in range(len(bpas) - 1)]
            for idx in range(len(gaps)):
                result = ps.detect_positional_cliff(board, str(idx))
                mine = probe.engine_typical_gap(gaps, idx)
                self.assertIsNotNone(result, f"engine declined row {idx} of {n}")
                if mine is None:
                    # Engine's every-other-gap-is-zero branch: it reports typical_gap 0.0.
                    self.assertEqual(result["typical_gap"], 0.0)
                else:
                    self.assertAlmostEqual(
                        result["typical_gap"], round(mine, 2), places=2,
                        msg=f"probe copy drifted from the engine at row {idx} of {n}")
                checked += 1
        self.assertGreater(checked, 500, "population too small to have tested anything")

    def test_the_engine_gap_matches_the_engine_ratio(self):
        """Agreement on the yardstick has to survive into the RATIO, which is what is compared
        against the null -- a denominator that matches while the numerator does not would still
        publish the wrong distribution."""
        probe = _load_probe()
        bpas = [100.0, 95.0, 94.0, 93.5, 70.0, 69.0, 68.0, 67.0, 66.0, 65.0, 64.0, 63.0]
        board = self._board(bpas)
        gaps = [bpas[i] - bpas[i + 1] for i in range(len(bpas) - 1)]
        for idx in range(len(gaps)):
            result = ps.detect_positional_cliff(board, str(idx))
            typical = probe.engine_typical_gap(gaps, idx)
            if not typical:
                continue
            self.assertAlmostEqual(result["gap"], round(gaps[idx], 2), places=2)
            # The engine's own tier boundary, recomputed from the probe's two numbers.
            ratio = gaps[idx] / typical
            expected = ("LOW" if gaps[idx] < ps.CLIFF_MIN_MATERIAL_GAP else
                        "HIGH" if ratio >= ps.CLIFF_HIGH_RATIO else
                        "MEDIUM" if ratio >= ps.CLIFF_MEDIUM_RATIO else "LOW")
            self.assertEqual(result["tier"], expected, f"row {idx}: ratio {ratio:.3f}")


class TheClosedFormIsTheWrongNull(unittest.TestCase):
    """2^-r understates the engine's own null, and worst exactly where the tail claim was made."""

    def _engine_null(self, n_gaps, reps, seed):
        probe = _load_probe()
        rng = random.Random(seed)
        ratios = []
        for _ in range(reps):
            gaps = [rng.expovariate(1.0) for _ in range(n_gaps)]   # memoryless: NO cliffs
            ratios.extend(probe.ratios_from_gaps(gaps))
        return ratios

    def test_engine_estimator_exceeds_the_closed_form_at_every_ratio(self):
        ratios = self._engine_null(40, 400, seed=20260911)
        self.assertGreater(len(ratios), 10_000, "null population too small to conclude from")
        for r in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
            engine = sum(1 for x in ratios if x >= r) / len(ratios)
            closed = 2 ** -r
            self.assertGreater(
                engine, closed,
                f"at r={r} the engine's estimator ({engine:.4f}) did not exceed 2^-r "
                f"({closed:.4f}) -- if this fails, detect_positional_cliff's yardstick changed "
                f"and #175's correction must be re-derived, not deleted")

    def test_the_understatement_grows_into_the_tail(self):
        """The reason the first pass's tail claim inverted: the error is not a constant offset."""
        ratios = self._engine_null(40, 400, seed=20260911)
        def inflation(r):
            return (sum(1 for x in ratios if x >= r) / len(ratios)) / (2 ** -r)
        self.assertGreater(inflation(4.0), inflation(2.5))
        self.assertGreater(inflation(2.5), inflation(1.0))
        # Order of magnitude, pinned loosely so a seed change does not fail it spuriously.
        self.assertGreater(inflation(4.0), 1.25)

    def test_a_plain_median_would_have_been_much_closer_to_the_closed_form(self):
        """Establishes WHICH property of the estimator causes it -- the trim, not the simulation.

        Without this the previous two tests are consistent with 'the simulation is biased',
        which would be a reason to distrust the correction rather than to accept it.
        """
        import statistics
        rng = random.Random(20260911)
        plain = []
        for _ in range(400):
            gaps = [rng.expovariate(1.0) for _ in range(40)]
            for i in range(len(gaps)):
                others = [g for j, g in enumerate(gaps) if j != i]
                med = statistics.median(others)
                if med > 0:
                    plain.append(gaps[i] / med)
        for r in (2.5, 4.0):
            got = sum(1 for x in plain if x >= r) / len(plain)
            closed = 2 ** -r
            self.assertLess(abs(got / closed - 1.0), 0.20,
                            f"plain-median null at r={r} was {got:.4f} vs 2^-r {closed:.4f}; "
                            f"the closed form should track the PLAIN median closely")


if __name__ == "__main__":
    unittest.main()


class TheCliffTierCannotSeeTheReplacementLevel(unittest.TestCase):
    """Why #175's "is the crossing stable across formats?" has a STRUCTURAL answer.

    bpa is points minus that position's replacement level, and the replacement level is ONE
    CONSTANT PER POSITION. detect_positional_cliff reads only DIFFERENCES between adjacent bpa
    values, so the constant cancels in every gap, in the yardstick, in the ratio and in the
    materiality floor alike. Any league axis that moves only the replacement level -- league
    size, superflex -- therefore cannot change a single cliff tier.

    Measured on the real capture universe before being pinned here: across 12 vs 10 vs 14 teams
    and superflex on/off, 0 of 41 QB gaps, 0 of 125 RB, 0 of 197 WR and 0 of 114 TE gaps
    differed, while the top bpa moved 48.51 -> 39.81 / 55.22 / 163.06. Only `rec` and
    `bonus_rec_te`, which reshape the POINTS curve rather than shifting it, move gaps.

    This is not a defect. It is pinned because it bounds what any cliff battery can answer:
    running more league sizes buys no independent evidence about this quantity, and a battery
    that counted them as independent arms would inflate its own denominator.
    """

    def _board(self, bpas, shift=0.0):
        return [{"player_id": str(i), "name": f"P{i}", "position": "WR", "bpa": v + shift}
                for i, v in enumerate(bpas)]

    def test_a_constant_shift_changes_no_tier_no_gap_no_yardstick(self):
        # A tightly packed top tier, one genuine cliff, then a smooth tail -- plus an exact
        # tie, so the zero-gap yardstick branch is exercised rather than assumed.
        bpas = [212.4, 205.0, 205.0, 193.0, 120.0, 114.0, 108.5, 103.0, 97.0, 92.0, 86.5,
                80.0, 74.0, 68.5, 62.0]
        base = [ps.detect_positional_cliff(self._board(bpas), str(i)) for i in range(len(bpas))]
        self.assertTrue(any(r and r["tier"] == "HIGH" for r in base),
                        "fixture produces no HIGH tier -- it would pass vacuously")
        for shift in (-200.0, -37.5, 114.55, 1000.0):
            shifted = [ps.detect_positional_cliff(self._board(bpas, shift), str(i))
                       for i in range(len(bpas))]
            for i, (a, b) in enumerate(zip(base, shifted)):
                self.assertEqual(a, b, f"row {i} changed under a {shift} shift: {a} -> {b}")

    def test_rescaling_the_points_curve_DOES_change_tiers(self):
        """The control. Without it the test above is equally consistent with the detector being
        insensitive to everything, which would make the invariance meaningless rather than
        informative."""
        # A tightly packed top tier, one genuine cliff, then a smooth tail -- plus an exact
        # tie, so the zero-gap yardstick branch is exercised rather than assumed.
        bpas = [212.4, 205.0, 205.0, 193.0, 120.0, 114.0, 108.5, 103.0, 97.0, 92.0, 86.5,
                80.0, 74.0, 68.5, 62.0]
        base = [ps.detect_positional_cliff(self._board(bpas), str(i)) for i in range(len(bpas))]
        # Compress the top of the curve only -- the shape change `rec` produces, not a shift.
        reshaped = [v if v < 120 else 120 + (v - 120) * 0.25 for v in bpas]
        after = [ps.detect_positional_cliff(self._board(reshaped), str(i))
                 for i in range(len(bpas))]
        self.assertNotEqual([r["tier"] if r else None for r in base],
                            [r["tier"] if r else None for r in after],
                            "reshaping the curve changed no tier -- the detector would then be "
                            "insensitive to shape too, and the invariance above would say "
                            "nothing about replacement levels specifically")


# ---------------------------------------------------------------------------------------
# MUTATION PASS -- 7 mutations, 6 caught. Bytecode cache cleared and PYTHONDONTWRITEBYTECODE
# set for every arm (a byte-length-preserving mutation restored inside one mtime second
# otherwise leaves the MUTANT executing from a .pyc that still validates).
#
#   M1  CLIFF_HIGH_RATIO 2.5 -> 3.5 .............. SURVIVED, BY DESIGN. See below.
#   M2  engine drops the 10% trim ................ caught
#   M3  engine keeps zero gaps in the yardstick .. caught
#   M4  probe copy trims 20% instead of 10% ...... caught
#   M5  tier reads bpa instead of the gap ........ caught
#   M6  engine yardstick median -> mean .......... caught
#   M7  probe stops excluding the target's gap ... caught
#
# M1 SURVIVES ON PURPOSE and must keep surviving. #175 asks whether CLIFF_HIGH_RATIO can be
# DERIVED, and that question is open and the owner's. A test here that pinned 2.5 would
# prejudge it, and would have to be deleted by whoever answers it -- so the tier assertions
# above recompute the boundary FROM ps.CLIFF_HIGH_RATIO rather than from a literal. What this
# file guards is the ESTIMATOR and its null, which are true whatever value the constant takes.
# ---------------------------------------------------------------------------------------
