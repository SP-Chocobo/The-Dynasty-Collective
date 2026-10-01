"""#215: joining a long instrument's output across processes, without inventing provenance.

WHY THIS EXISTS. The container this repo's instruments run in is reclaimed on OPERATOR
inactivity, not on the job's -- a backgrounded run does not hold it open. Measured three times
on 2026-09-08. Two independent full-depth runs of the roster proof were killed 67s and 45s into
their SIXTH format, having already spent 45 and 30 minutes on the first five; the 33-arm battery
was killed twice, most recently 8 arms in.

#213b made those partial results SURVIVABLE by writing after every unit. It did not make the run
FINISHABLE, because the next process started again from unit one. A ~3-hour battery cannot fit
inside the reclaim window at all, so without a join it can never complete no matter how many
times it is launched.

WHAT MAKES THE JOIN LEGITIMATE. Only determinism, and only because it is MEASURED here rather
than assumed: the two roster-proof runs above ran at DIFFERENT COMMITS (ef98dd9 and cf0b283) and
produced byte-identical numbers for all five formats they shared. A joined report is still a
report about more than one process, so every carried unit keeps the commit that PRODUCED it and
the document names every commit that contributed. A single top-level commit on a joined document
would be a false claim about every unit the last process did not compute.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

#: Marks a unit that this process did not compute. Present and False on every unit a process
#: DID compute -- an absent flag would make "not carried" and "predates the flag" the same
#: reading, which is the absence contract broken in the instrument that reports on it.
CARRIED = "carried_forward"

#: The commit a unit's numbers were produced at. One home for the key (#126), because the
#: battery and the roster proof both write it and a drifted spelling would silently split the
#: provenance of a joined document in two.
PRODUCED_AT = "produced_at_commit"


def head_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=10).stdout.strip() or "unknown"
    except Exception:                                   # noqa: BLE001 -- provenance, never fatal
        return "unknown"


def commits_present(units) -> list:
    """Every commit that contributed a unit to this document, sorted.

    More than one entry is not an error -- it is the document telling a reader to check that the
    contributing commits agree before quoting it as a single result."""
    return sorted({u.get(PRODUCED_AT) for u in units or [] if u.get(PRODUCED_AT)})


def carry_forward(path, wanted_labels, *, units_key, label_key="label") -> list:
    """The units in `path` this run would otherwise recompute, each stamped with its origin.

    Returns [] for every reason a prior report might be unusable -- absent, unreadable, truncated
    mid-write -- because a resume that cannot read the old file must recompute, never guess.

    A report written BEFORE this module has no per-unit stamp, but it also cannot be a join:
    nothing could resume into it, so every unit in it came from the one process that wrote it, at
    the one commit that process recorded. That is the ONLY case where the report-level commit is
    a sound answer for a unit, and it is recognised by the absence of this module's own keys --
    never assumed. A joined report missing a stamp is refused, because there the report-level
    commit describes the last process only.
    """
    if not path or not Path(path).exists():
        return []
    try:
        prior = json.loads(Path(path).read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []
    if not isinstance(prior, dict):
        return []

    single_process = "commits_present" not in prior and CARRIED not in prior
    inherited = prior.get("commit") if single_process else None

    wanted = set(wanted_labels)
    out = []
    for unit in prior.get(units_key) or []:
        if not isinstance(unit, dict) or unit.get(label_key) not in wanted:
            continue
        stamp = unit.get(PRODUCED_AT) or inherited
        if not stamp:
            continue
        unit[PRODUCED_AT] = stamp
        unit[CARRIED] = True
        out.append(unit)
    return out


# ---------------------------------------------------------------------------------------------
# A PROCESS NOTE, kept next to the code it nearly destroyed (#215).
#
# While this module was being mutation-tested, two mutation batches ran CONCURRENTLY and shared
# one backup path, /tmp/mut_backup.py. Batch A backed up run_roster_proof.py to it; batch B then
# "restored" run_draft_battery.py FROM it. The battery's source was replaced wholesale with the
# roster proof's, and a leftover `if False:` was left sitting in the proof's resume branch.
#
# Neither failure announced itself. The battery still imported (it was valid Python, just the
# wrong module), and the proof's disabled branch surfaced only because a test asserted on the
# real source text. Two mutations in the same batch reported OK purely because their patch
# scripts had died with a SyntaxError and never applied -- an unapplied mutation reads exactly
# like a surviving one.
#
# The three rules that came out of it, for any future mutation pass in this repo:
#   1. One backup path PER TARGET FILE, never one shared path.
#   2. Verify the pattern is PRESENT before mutating, and verify the file is BYTE-IDENTICAL to
#      the original after restoring. A restore that silently wrote the wrong bytes is the whole
#      failure.
#   3. Never run two mutation batches at once, and read the batch's FULL output -- grepping only
#      for OK/FAILED hides the SyntaxError that means nothing was tested.
