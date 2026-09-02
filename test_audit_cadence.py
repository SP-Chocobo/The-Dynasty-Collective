"""§19.9: the documented cadence and the configured one cannot drift apart.

WHY A TEST AND NOT JUST A SCHEDULE. §19.9's finding was that ENGINEERING_DOCTRINE states standing
rules and nothing ran them. Adding a `schedule:` fixes that. But a cadence that lives in two
places -- a paragraph a human reads and a cron a machine reads -- has a failure mode of its own,
and it is the worse one: when they disagree, **the document is the one that gets believed, and it
is the one that cannot run anything.** So the paragraph and the cron are held to each other here.
"""

import re
import unittest
from pathlib import Path

_HERE = Path(__file__).parent
_WORKFLOW = (_HERE / ".github/workflows/tests.yml").read_text()
_DOCTRINE = (_HERE / "ENGINEERING_DOCTRINE.md").read_text()

#: Weekly, Wednesdays, 13:00 UTC. Day-of-week 3 is Wednesday in cron's 0=Sunday numbering.
CRON = "0 13 * * 3"


class TheScheduleExistsAndIsTheRuledOneTests(unittest.TestCase):
    def test_the_workflow_has_a_schedule_trigger_at_all(self):
        """The whole finding: nothing ran the checks except a human pushing."""
        self.assertIn("schedule:", _WORKFLOW)

    def test_the_cron_is_weekly_on_wednesday(self):
        self.assertIn(f'cron: "{CRON}"', _WORKFLOW)
        minute, hour, dom, month, dow = CRON.split()
        self.assertEqual(dow, "3", "Wednesday")
        self.assertEqual((dom, month), ("*", "*"), "weekly, not monthly or seasonal")
        self.assertTrue(minute.isdigit() and hour.isdigit(),
                        "a fixed time, not a range or step -- one run, not several")

    def test_there_is_exactly_one_schedule_so_the_cadence_is_unambiguous(self):
        self.assertEqual(_WORKFLOW.count("cron:"), 1)


class TheDoctrineStatesTheSameCadenceTests(unittest.TestCase):
    def test_the_doctrine_names_the_day_and_the_hour(self):
        self.assertIn("weekly, Wednesdays, 13:00 UTC", _DOCTRINE)

    def test_the_doctrine_points_at_where_it_is_configured(self):
        """A stated cadence with no pointer to its implementation is how the two drift."""
        self.assertIn(".github/workflows/tests.yml", _DOCTRINE)
        self.assertIn("test_audit_cadence.py", _DOCTRINE)

    def test_the_doctrine_gives_the_reason_and_it_is_a_seasonal_one(self):
        """'Wednesdays' with no reason invites someone to move it to whatever is convenient. The
        reason is that the week of play concludes Monday night, so the numbers have settled."""
        for phrase in ("regular-season week of play concludes Monday night", "settled"):
            self.assertIn(phrase, _DOCTRINE, phrase)


class TheScheduledRunUsesTheSameChecksAsEverythingElseTests(unittest.TestCase):
    """A scheduled run with its own weaker or stronger standard would make 'green on Wednesday'
    mean something different from 'green on a pull request'. It runs what CI already runs."""

    def test_the_schedule_reaches_the_full_tier_and_not_only_the_fast_one(self):
        """The full job is gated `if: github.event_name != 'push'`, so a schedule event reaches
        it. If that guard is ever tightened to name events explicitly, this catches the schedule
        silently dropping to fast-only."""
        guard = re.search(r"if:\s*(.+)", _WORKFLOW)
        self.assertIsNotNone(guard)
        self.assertEqual(guard.group(1).strip(), "github.event_name != 'push'")

    def test_both_tiers_check_the_declared_input_set_and_the_assertion_floors(self):
        self.assertEqual(_WORKFLOW.count("baseline_manifest.py --check"), 2)
        self.assertEqual(_WORKFLOW.count("assertion_floors.py --check"), 2)

    def test_the_doctrine_names_the_three_things_the_run_does(self):
        for phrase in ("full suite", "baseline_manifest.py --check", "assertion_floors.py --check"):
            self.assertIn(phrase, _DOCTRINE, phrase)


if __name__ == "__main__":
    unittest.main()
