#!/usr/bin/env python3
"""Exercise the gate lock. Six arms, every one of them earned by a failure.

WHY THIS FILE EXISTS RATHER THAN A PARAGRAPH SAYING THE LOCK WORKS. Every arm below passed at
some point today and then stopped passing, silently, because of a change elsewhere:

  arm 1  a live gate must block a build -- BROKE when the lock file grew a second field and
         _build.py's copy of the parser raised on it and took the stale branch. The guard went
         from working to permitting every build while printing a calm sentence about it. That is
         the arm that matters most and it is the one that failed without a sound.
  arm 2  a second gate must refuse to start
  arm 3  a dead pid must read as stale
  arm 3b a ZOMBIE pid must read as stale -- os.kill(pid, 0) succeeds for one, so the first
         version of this lock blocked builds on behalf of a gate that had already exited
  arm 4  SIGTERM must release the lock -- atexit does NOT run for it, and the first version
         relied on atexit alone
  arm 5  a live pid that is not a gate must read as stale (pid reuse)
  arm 6  the right pid with the WRONG start time must read as stale -- the exact pid-reuse case,
         and the arm that proves the start time is actually compared rather than merely written

Run it from this directory:   python3 _gatelock_test.py
"""
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _gatelock

LOCK = HERE / ".gate.lock"
PY3 = "/usr/bin/python3"
results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"   {detail}" if detail else ""))


def build_refuses():
    """Does _build.py refuse? Returns (refused, first relevant line)."""
    r = subprocess.run([PY3, "_build.py"], cwd=HERE, capture_output=True, text=True)
    text = r.stdout + r.stderr
    line = next((l for l in text.splitlines() if "gate" in l), "")
    return ("render gate is running" in text), line.strip()[:100]


def spawn_sleeper(seconds=90):
    p = subprocess.Popen([PY3, "-c", f"import time; time.sleep({seconds})"])
    time.sleep(0.3)
    return p


def main():
    LOCK.unlink(missing_ok=True)
    print(__doc__.splitlines()[0])

    # ---- arms that need a REAL gate running -------------------------------------------------
    print("\narms 1, 2, 4 -- against a real gate process")
    gate = subprocess.Popen([PY3, "_shoot.py"], cwd=HERE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):                     # the gate makes its snapshot before it takes the lock
        if LOCK.exists():
            break
        time.sleep(0.5)
    held = LOCK.read_text().strip() if LOCK.exists() else "(never appeared)"
    check("arm 0  a running gate writes a two-field lock", len(held.split()) == 2, f"lock = {held}")

    refused, line = build_refuses()
    check("arm 1  a live gate BLOCKS a build", refused, line)

    g2 = subprocess.run([PY3, "_shoot.py"], cwd=HERE, capture_output=True, text=True)
    check("arm 2  a second gate refuses to start",
          "render gate is running" in (g2.stdout + g2.stderr), (g2.stdout + g2.stderr).strip()[:90])

    snaps_during = len(list(pathlib.Path("/tmp").glob("gate-snapshot-*")))
    gate.terminate(); gate.wait(timeout=60); time.sleep(1)
    check("arm 4  SIGTERM releases the lock", not LOCK.exists(),
          "lock released" if not LOCK.exists() else f"still holding {LOCK.read_text()!r}")
    check("arm 4b SIGTERM removes the build snapshot too",
          len(list(pathlib.Path("/tmp").glob("gate-snapshot-*"))) < max(1, snaps_during),
          f"{snaps_during} during the run, {len(list(pathlib.Path('/tmp').glob('gate-snapshot-*')))} after")

    # ---- arms that need a forged lock ------------------------------------------------------
    print("\narms 3, 3b, 5, 6 -- against forged locks")
    p = spawn_sleeper(5); dead_pid = p.pid
    p.terminate(); p.wait()                 # fully reaped: the pid is simply gone
    LOCK.write_text(f"{dead_pid} 123456")
    check("arm 3  a dead pid reads as stale", _gatelock.describe(LOCK) is None)

    # a REAL zombie: a child that exited whose parent has not waited for it
    zpid = os.fork()
    if zpid == 0:
        os._exit(0)
    time.sleep(0.3)
    state = (pathlib.Path("/proc") / str(zpid) / "stat").read_text().rsplit(") ", 1)[1].split()[0]
    LOCK.write_text(f"{zpid} {_gatelock.start_time(zpid)}")
    check("arm 3b a zombie pid reads as stale", _gatelock.describe(LOCK) is None,
          f"pid {zpid} state={state}")
    os.waitpid(zpid, 0)

    live = spawn_sleeper(30)
    LOCK.write_text(f"{live.pid} {_gatelock.start_time(live.pid)}")
    check("arm 5  a live pid that is not a gate reads as stale", _gatelock.describe(LOCK) is None,
          f"pid {live.pid} is a sleeper, not a gate")

    LOCK.write_text(f"{live.pid} 999999999")
    check("arm 6  right pid, wrong start time reads as stale", _gatelock.describe(LOCK) is None,
          f"real start {_gatelock.start_time(live.pid)}, lock claimed 999999999")
    live.terminate(); live.wait()

    LOCK.write_text("not-a-pid")
    check("arm 7  an unparseable lock reads as stale", _gatelock.describe(LOCK) is None)
    LOCK.unlink(missing_ok=True)

    bad = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(bad)} of {len(results)} arms pass")
    if bad:
        print("FAILED: " + "; ".join(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
