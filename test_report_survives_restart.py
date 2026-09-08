"""#213b: a multi-hour instrument must not lose everything to a container restart.

MEASURED, TWICE, TODAY. The container restarted mid-run. The roster proof writes its report
after every format and survived with 5 of 6 intact. The battery wrote only on its last line and
lost all 11 completed arms -- roughly 80 minutes of drafting, gone, with nothing on disk to show
which arms had passed.

That is the durability hole `evidence/batteries/` was created to close, reproduced one layer in:
the earlier fix made the OUTPUT durable once written, and left the WRITING itself to a single
point at the end of a four-hour run.
"""

from __future__ import annotations

import inspect
import unittest

import run_draft_battery as rdb
import run_roster_proof as rp


class BothLongRunningInstrumentsWriteIncrementallyTests(unittest.TestCase):

    def test_the_battery_writes_after_every_arm(self):
        src = inspect.getsource(rdb.main)
        loop = src[src.index("for entry in matrix:"):src.index("total_findings =")]
        self.assertIn("store_io.write", loop,
                      "a four-hour run that writes only on its last line loses everything to a "
                      "restart -- measured today, 11 arms destroyed")
        self.assertIn("complete=False", loop)

    def test_the_roster_proof_writes_after_every_format(self):
        src = inspect.getsource(rp.main)
        self.assertIn("complete=False", src)

    def test_the_battery_report_actually_carries_the_flag(self):
        """Asserted on the RETURNED DOCUMENT, not on the source text.

        The first version grepped the function source for "complete" -- which still appears in
        its own signature and docstring, so it passed a mutation that deleted the key from the
        dict. Second time today a substring check was satisfied by the subject's own prose.
        """
        for complete in (False, True):
            report = rdb._battery_report({"x": 1}, [], 0.0, complete=complete)
            self.assertIn("complete", report,
                          "a reader must tell a partial file from a finished one without "
                          "counting rows")
            self.assertIs(report["complete"], complete)

    def test_the_roster_proof_report_carries_it_too(self):
        src = inspect.getsource(rp._write_report)
        self.assertIn('"complete": complete', src,
                      "the same flag, written into the document rather than implied")

    def test_the_battery_report_is_built_in_one_place(self):
        """Mid-run and end-of-run must be the SAME document shape, or a partial file is a
        different kind of thing from a finished one and nothing can read both."""
        src = inspect.getsource(rdb.main)
        self.assertEqual(src.count("_battery_report("), 2,
                         "one builder, two call sites -- not two hand-built dicts that drift")

    def test_the_finished_battery_report_says_complete(self):
        src = inspect.getsource(rdb.main)
        self.assertIn("complete=True", src)


if __name__ == "__main__":
    unittest.main()
