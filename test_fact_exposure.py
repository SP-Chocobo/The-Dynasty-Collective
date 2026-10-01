"""The disclosure ratchet, tested for the failure that would make it decorative (`#254`).

A census that cannot detect a new crossing is a comment. The tests that carry this module's value
are the ones that PLANT a quantity crossing to a provider and require it caught -- not the one
that observes today's prompt path passing, which would also pass if the scan matched nothing at
all.

The second thing tested here is the distinction the census exists for: READ is not EMITTED.
`pick_debate` reads the survival family and then gates it off, and a census that collapsed those
two states would report three quantities as reaching a third party when a repair was made
specifically to stop them.

Cited register items: `#126` (one home for the walk -- every arm calls `reads`/`classify` rather
than restating the rule), `#133`, `#187`, `#254`, `#245` (a count nobody can move is a broken
instrument until proven otherwise).
"""

from __future__ import annotations

import pathlib
import tempfile
import unittest

import fact_exposure as fx
import pick_synthesis as ps
import quantity_readers as qr


def _module(body: str) -> pathlib.Path:
    """A synthetic prompt module.

    NOT named `pick_debate.py`: `reads()` parses whatever path it is handed and the filename
    reaches no branch of it, so the name would carry no information while inviting confusion with
    the real module.
    """
    path = pathlib.Path(tempfile.mkdtemp()) / "synthetic_prompt_path.py"
    path.write_text(body, encoding="utf-8")
    return path


class TheScanSeesBothAccessShapesTests(unittest.TestCase):
    """`candidate.x` AND `getattr(candidate, "x", None)`. Missing the second loses `risk_basis`,
    which is the companion `#166` exists to keep beside `risk_adj` -- so the number would be
    recorded as crossing and its basis would not, which is the `#174` defect exactly."""

    def test_an_attribute_read_is_counted(self):
        found = fx.reads(_module("def debate_pick(candidate):\n    return candidate.risk_adj\n"),
                         roots=("debate_pick",))
        self.assertEqual(1, found["risk_adj"])

    def test_a_getattr_read_is_counted(self):
        found = fx.reads(_module(
            'def debate_pick(candidate):\n'
            '    return getattr(candidate, "risk_basis", None)\n'), roots=("debate_pick",))
        self.assertEqual(1, found["risk_basis"])

    def test_a_read_through_a_called_formatter_is_followed(self):
        """The call graph, not one function. The real evidence block is assembled across twelve
        functions and a scan that read only the entry point would see almost nothing."""
        found = fx.reads(_module(
            "def _fmt(candidate):\n    return candidate.universal_value\n"
            "def debate_pick(snapshot):\n    return [_fmt(c) for c in snapshot.candidates]\n"),
            roots=("debate_pick",))
        self.assertEqual(1, found["universal_value"])
        self.assertEqual(1, found["candidates"])

    def test_a_read_on_an_UNRELATED_object_is_not_counted(self):
        """Non-vacuity in the other direction: a scan that counted every attribute access in the
        file would pass every test above while saying nothing about what crosses."""
        found = fx.reads(_module(
            "def debate_pick(cfg):\n    return cfg.universal_value\n"), roots=("debate_pick",))
        self.assertEqual(0, sum(found.values()))

    def test_a_function_the_roots_cannot_reach_is_not_counted(self):
        """Reachability is load-bearing. `pick_debate` holds functions that read a candidate for
        purposes that never reach a prompt, and counting them would overstate the boundary."""
        found = fx.reads(_module(
            "def _orphan(candidate):\n    return candidate.survival_probability\n"
            "def debate_pick(candidate):\n    return candidate.bpa\n"), roots=("debate_pick",))
        self.assertEqual(1, found["bpa"])
        self.assertEqual(0, found["survival_probability"])


class TheRatchetCatchesAWideningTests(unittest.TestCase):
    """The three arms that make this a guard. Each plants a real widening; each must be caught."""

    def test_a_newly_crossing_quantity_is_reported(self):
        quantity = next(iter(sorted(set(qr.produced_quantities()) - fx.CENSUS)))
        grew = fx.widened(_module(
            f"def debate_pick(candidate):\n    return candidate.{quantity}\n"),
            roots=("debate_pick",))
        self.assertTrue(any(quantity in line and "NEWLY CROSSES" in line for line in grew),
                        f"a new crossing of {quantity} was not reported: {grew}")

    def test_a_quantity_crossing_through_a_getattr_is_reported(self):
        """The shape a formatter actually uses for a field that may be absent -- so the easiest
        way to widen this boundary by accident is the one the scan must not miss."""
        quantity = next(iter(sorted(set(qr.produced_quantities()) - fx.CENSUS)))
        grew = fx.widened(_module(
            f'def debate_pick(candidate):\n    return getattr(candidate, "{quantity}", None)\n'),
            roots=("debate_pick",))
        self.assertTrue(any(quantity in line for line in grew))

    def test_a_name_the_engine_does_not_produce_is_reported_as_a_DISAGREEMENT(self):
        """Not as a crossing. If the prompt path reads something `quantity_readers` has never
        heard of, the two instruments disagree about the engine's vocabulary and one is wrong --
        which is a different problem from the boundary growing, and is reported as one."""
        grew = fx.widened(_module(
            "def debate_pick(candidate):\n    return candidate.not_a_real_quantity\n"),
            roots=("debate_pick",))
        self.assertTrue(any("disagree about the engine's vocabulary" in line for line in grew))

    def test_a_prompt_path_that_reads_nothing_does_not_report_a_widening(self):
        """Shrinkage is a repair, never a failure. A check that failed on repairs gets disabled."""
        self.assertEqual([], fx.widened(_module("def debate_pick(x):\n    return 1\n"),
                                        roots=("debate_pick",)))


class ReadIsNotEmittedTests(unittest.TestCase):
    """The distinction the census exists for, and the one a simpler instrument would lose."""

    def test_the_withheld_family_is_read_but_not_emitted(self):
        found = fx.classify()
        withheld = frozenset(ps.withheld_fields())
        self.assertTrue(withheld, "nothing is withheld today -- this arm would be vacuous; if "
                                  "the survival family became presentable, that is a disclosure "
                                  "change and CENSUS's classes must be re-read, not this test "
                                  "deleted")
        for name in withheld & found["read"]:
            with self.subTest(name=name):
                self.assertIn(name, found["withheld"])
                self.assertNotIn(name, found["emitted"])

    def test_emitted_and_withheld_partition_the_read_set(self):
        """No quantity may be in neither class, and none in both -- the `suite_taxonomy` property:
        a classification with a silent third bucket is not a classification."""
        f = fx.classify()
        known = f["read"]
        self.assertEqual(known, f["emitted"] | (f["withheld"] & known))
        self.assertEqual(frozenset(), f["emitted"] & f["withheld"])

    def test_every_recorded_crossing_is_a_quantity_the_engine_produces(self):
        """`CENSUS` is a claim about the engine's own vocabulary. A name in it that the engine
        does not produce is a stale record, and the record is what later readers trust (`#292`)."""
        produced = frozenset(qr.produced_quantities())
        self.assertEqual(frozenset(), fx.CENSUS - produced,
                         "CENSUS names something quantity_readers does not produce")


class TheRealBoundaryTests(unittest.TestCase):
    """Over the real module, so the census is about this engine and not about a fixture."""

    def test_the_boundary_has_not_widened(self):
        self.assertEqual([], fx.widened())

    def test_the_scan_actually_finds_reads_in_the_real_prompt_path(self):
        """Non-vacuity for the check above, which would pass just as well on a scan that matched
        nothing (`#245`). The real evidence block is 41k characters of labelled engine numbers; a
        scan reporting a handful of reads has broken, not improved."""
        found = fx.classify()
        self.assertGreater(len(found["read"]), 30,
                           "the scan found almost nothing in the prompt path -- suspect the scan")
        self.assertEqual(frozenset(), found["unknown"])

    def test_the_reachable_population_has_not_COLLAPSED(self):
        """A scan whose population shrank to its entry points would report a shrinking boundary
        as good news. Pins the count so that losing the call graph is a failure, not a quiet
        improvement."""
        functions = fx._functions(fx.PROMPT_MODULE)
        reach = fx._reachable(functions, fx.PROMPT_ROOTS)
        self.assertGreaterEqual(len(reach), 8,
                                f"only {len(reach)} functions reachable from {fx.PROMPT_ROOTS}; "
                                f"the call graph is not being followed")

    def test_the_other_provider_module_is_named_rather_than_silently_omitted(self):
        """`llm_engine.py` also calls providers. This census does not cover it, and the limit is
        stated in the module docstring -- an unstated scope limit is how a census comes to be read
        as covering more than it does (`#133`)."""
        self.assertIn("llm_engine.py", fx.__doc__)
        self.assertTrue(pathlib.Path("llm_engine.py").exists(),
                        "the docstring names a module that no longer exists")


if __name__ == "__main__":
    unittest.main()
