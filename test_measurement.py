"""The instrument standard's executable half. Each test pins the failure it exists to prevent."""
import json, os, tempfile, unittest
import measurement as m


class ARateCannotBeFormattedWithoutItsPopulationTests(unittest.TestCase):
    """M4/M9: '34%' is unreadable; '34% of all priced rows' is a finding."""

    def test_a_rate_carries_hits_population_and_scope(self):
        self.assertEqual(m.rate(34, 100, "all priced board rows, 3 formats"),
                         "34/100 = 34.0% of all priced board rows, 3 formats")

    def test_an_empty_population_raises_rather_than_reporting_zero_percent(self):
        # #172's shape: a term structurally incapable of being non-zero, measured at 0.0%
        # across five formats and nearly reported as a property of the engine.
        with self.assertRaises(m.VacuousPopulation):
            m.rate(0, 0, "rows carrying a dual-eligibility bonus")

    def test_scope_is_not_optional(self):
        with self.assertRaises(ValueError):
            m.rate(1, 2, "   ")


class AbsenceAndMeasuredZeroAreCountedSeparatelyTests(unittest.TestCase):
    """M6: `if value:` conflates never-computed with a real zero."""

    def test_a_measured_zero_is_present_and_not_matching(self):
        got = m.counted([0.0, 1.0, None, 2.0])
        self.assertEqual(got, {"n": 4, "present": 3, "absent": 1, "matching": 2})

    def test_all_absent_is_distinguishable_from_all_zero(self):
        self.assertEqual(m.counted([None, None])["present"], 0)
        self.assertEqual(m.counted([0.0, 0.0])["present"], 2)


class PartialResultsSurviveADeathTests(unittest.TestCase):
    """M3: #176 attempt 1 lost seven completed runs to a per-format write.

    WHAT THESE TESTS DO AND DO NOT PIN, stated because a mutation check caught them
    overclaiming. The behavioural test below proves the PREVIOUS GOOD FILE SURVIVES A FAILED
    WRITE. It does NOT prove atomicity: replacing os.replace with a non-atomic
    shutil.copyfile leaves it green, because a truncated destination cannot be produced
    deterministically in-process. So atomicity is pinned separately, on the mechanism, by
    asserting the primitive -- an implementation-coupled test, chosen deliberately over a
    behavioural one that cannot see the property it claims to check.
    """

    def test_the_write_uses_an_atomic_replace_not_a_copy(self):
        import inspect
        src = inspect.getsource(m.persist_each)
        self.assertIn("os.replace(", src,
                      "persist_each must land the file with an atomic replace; a copy can be "
                      "interrupted halfway and leave a truncated report")
        self.assertNotIn("copyfile", src)

    def test_each_write_replaces_atomically_and_the_previous_file_survives_a_failure(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "out.json")
            m.persist_each(p, {"runs": [1]})
            m.persist_each(p, {"runs": [1, 2]})
            self.assertEqual(json.load(open(p)), {"runs": [1, 2]})
            cycle = {}
            cycle["self"] = cycle                    # json cannot serialise a cycle, and
            with self.assertRaises(ValueError):      # default=str cannot rescue one either
                m.persist_each(p, cycle)
            self.assertEqual(json.load(open(p)), {"runs": [1, 2]}, "the good file was clobbered")
            self.assertEqual([f for f in os.listdir(d) if f.endswith(".part")], [])


class AFindingMustReproduceBeforeItIsReturnedTests(unittest.TestCase):
    """M1: #176 was published on a single run and failed its first reproduction."""

    def test_a_stable_measurement_passes_through(self):
        self.assertEqual(m.reproduced(lambda: {"filled": [8, 8, 8]}), {"filled": [8, 8, 8]})

    def test_a_measurement_that_disagrees_with_itself_raises(self):
        seq = iter([[7, 7, 8], [8, 8, 8]])       # exactly #176's contradiction
        with self.assertRaises(m.NotReproduced):
            m.reproduced(lambda: next(seq))

    def test_key_lets_wall_clock_vary_without_defeating_the_check(self):
        seq = iter([{"v": 1, "secs": 9.1}, {"v": 1, "secs": 9.4}])
        self.assertEqual(m.reproduced(lambda: next(seq), key=lambda r: r["v"])["v"], 1)


if __name__ == "__main__":
    unittest.main()
