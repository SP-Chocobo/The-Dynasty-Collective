"""One mutation at a time, against ONE target, with a backup path of its own.

The three rules this obeys are the ones written down after a mutation harness silently replaced
a source file with another module's backup (#215's process note):

  1. ONE BACKUP PATH PER TARGET, named after the target. Two batches sharing /tmp/mut_backup.py
     is how a file gets restored from the wrong module's contents.
  2. VERIFY THE PATTERN IS PRESENT BEFORE, and that the file is BYTE-IDENTICAL AFTER. An
     unapplied mutation reads exactly like a survivor; a bad restore reads like nothing at all.
  3. NEVER TWO BATCHES AT ONCE, and read the FULL output, not a grep for OK/FAILED.

Patterns live in a JSON file rather than inline in a shell heredoc, because \\x27 opening a
Python string inside a heredoc is what made three mutations report OK without ever applying.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

MUTATIONS = json.loads(Path(sys.argv[1]).read_text())
TESTS = sys.argv[2:] or ["test_216_flex_share"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    for m in MUTATIONS:
        target = Path(m["file"])
        backup = Path(f"/tmp/claude-0/mut_backup__{target.name}")
        before = digest(target)
        shutil.copy2(target, backup)
        source = target.read_text()
        if m["old"] not in source:
            print(f"{m['id']} {m['what']} :: PATTERN ABSENT -- NOT APPLIED, NOT A SURVIVOR")
            continue
        if source.count(m["old"]) != 1:
            print(f"{m['id']} {m['what']} :: PATTERN AMBIGUOUS ({source.count(m['old'])}x)")
            continue
        target.write_text(source.replace(m["old"], m["new"], 1))
        try:
            proc = subprocess.run([sys.executable, "-m", "unittest", *TESTS],
                                  capture_output=True, text=True, timeout=900)
            tail = (proc.stderr or proc.stdout).strip().splitlines()
            verdict = "CAUGHT" if proc.returncode != 0 else "SURVIVED"
            print(f"{m['id']} {m['what']} :: {verdict} :: {tail[-1] if tail else '?'}")
        finally:
            shutil.copy2(backup, target)
            after = digest(target)
            if after != before:
                print(f"{m['id']} :: RESTORE FAILED -- file is not byte-identical; STOPPING")
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
