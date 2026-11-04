#!/usr/bin/env python3
"""One home for the gate lock: its file format, and the question "is that gate still alive".

WHY THIS IS A MODULE AND NOT TWELVE LINES IN EACH FILE. It was twelve lines in each file for
about an hour, and in that hour the format changed on one side only. `_shoot.py` started writing
`"<pid> <starttime>"` where it had written `"<pid>"`; `_build.py`'s copy still did
`int(text.strip())`, which raises on the two-field form and lands in the stale branch -- so the
build guard went from working to treating EVERY lock as dead, while printing a reassuring
sentence about it. A guard that protects nothing and says so politely is worse than no guard,
and the only reason it was caught is that the test arm for "a real live gate blocks a build"
was re-run after the format change.

Two implementations of one contract is the defect (#126). This is the one implementation. The
format is written here, read here, and interpreted here, and neither caller knows what is in
the file.

WHAT MAKES A LOCK LIVE, and why each check is in it:

  the pid exists          -- /proc/<pid>; the obvious one, and on its own not enough
  it is not a zombie      -- os.kill(pid, 0) succeeds for a process that has exited and not been
                             reaped, so the first version of this lock went on blocking builds
                             for a gate that was already dead
  its start time matches  -- field 22 of /proc/<pid>/stat. Pids are reused; a pid plus its start
                             time is unique for the life of the boot, so this is the exact answer
                             to "is this the process that wrote the lock"
  its cmdline says _shoot -- the friendlier version of the same question, kept for a lock written
                             before start times were recorded, which has none to compare

Release is belt and braces, because neither half covers the other: atexit handles a normal
finish and an exception, and does NOT run on SIGTERM, which is how `timeout` ends a run and how
this gate is usually stopped by hand. The signal handler does the rest by hand rather than
trusting that a SystemExit raised inside a handler reaches a normal interpreter shutdown.
"""
from __future__ import annotations

import atexit
import os
import pathlib
import shutil
import signal
import sys

#: Extra paths a holder wants removed when it releases -- the gate's build snapshot, in practice.
_ALSO_REMOVE: list[pathlib.Path] = []


def _stat_fields(pid):
    """/proc/<pid>/stat past the comm field, which can itself contain spaces and parentheses."""
    return (pathlib.Path("/proc") / str(pid) / "stat").read_text().rsplit(") ", 1)[1].split()


def start_time(pid="self"):
    try:
        return _stat_fields(pid)[19]          # field 22 overall; 20th after comm and state
    except (OSError, IndexError):
        return "?"


def read(lock: pathlib.Path):
    """(pid, start_time) from a lock file, or (None, None) if it says nothing usable."""
    try:
        parts = lock.read_text().split()
        return int(parts[0]), (parts[1] if len(parts) > 1 else None)
    except (OSError, ValueError, IndexError):
        return None, None


def alive(pid, start=None) -> bool:
    if pid is None or not (pathlib.Path("/proc") / str(pid)).exists():
        return False
    try:
        fields = _stat_fields(pid)
        if fields[0] == "Z":
            return False
        if start is not None and start != "?" and fields[19] != start:
            return False
        cmd = (pathlib.Path("/proc") / str(pid) / "cmdline").read_bytes()
        return "_shoot" in cmd.decode("utf8", "replace")
    except (OSError, IndexError):
        return False


def describe(lock: pathlib.Path) -> str | None:
    """None when no live gate holds `lock`; otherwise a sentence naming the holder."""
    pid, start = read(lock)
    if alive(pid, start):
        return f"a render gate is running as pid {pid}"
    return None


def take(lock: pathlib.Path, also_remove=()):
    """Claim `lock` for this process, or exit with a sentence. Releases on exit and on signal."""
    held = describe(lock)
    if held:
        raise SystemExit(f"{held} and is reading these builds; two readers of one set of built "
                         f"files see each other's renders. Wait for it, or remove {lock} if you "
                         f"know it is dead.")
    if lock.exists():
        pid, _ = read(lock)
        print(f"removing a stale gate lock ({lock}): no live gate at pid {pid}")
    lock.write_text(f"{os.getpid()} {start_time()}")
    _ALSO_REMOVE.extend(pathlib.Path(p) for p in also_remove)

    def release():
        lock.unlink(missing_ok=True)
        for extra in _ALSO_REMOVE:
            shutil.rmtree(extra, ignore_errors=True)

    atexit.register(release)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, lambda n, fr: (release(), sys.exit(128 + n)))
    return release


def also_remove(path):
    """Add a path to what release() cleans up, after take() has already run."""
    _ALSO_REMOVE.append(pathlib.Path(path))
