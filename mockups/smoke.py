"""The mockups' gate: `python3 mockups/smoke.py` from the repo root.

Round 1's version of this file was a DOM-stub crash test with a vendor grep, and the critic
took it apart correctly: its G1 check passed if ONE `.absent` existed anywhere on the page,
its G2 check matched any `0` anywhere (a "0%" survival satisfied it before the zeros row was
even considered), and the stub returned [] from querySelectorAll so nothing wired after
render ever ran. It proved the JS did not throw. It did not prove absence handling.

This version runs `gate.cjs` in a real Chromium through Playwright and asserts PER FIELD on
the fixture rows -- see the checklist at the top of gate.cjs. It gates the round-2 syntheses;
the round-1 pages are kept as the scored record and are not re-gated.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
GATED = sorted(HERE.glob("synthesis_*.html"))


def main() -> int:
    node = shutil.which("node")
    if node is None:
        print("node not found; the gate cannot run")
        return 1
    root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
    env = dict(os.environ, NODE_PATH=root)
    if not GATED:
        print("no synthesis pages built; run mockups/build.py first")
        return 1
    run = subprocess.run([node, str(HERE / "gate.cjs"), *map(str, GATED)], env=env, text=True)
    print("\ndensity at 1400 x 1400 (density.cjs):")
    subprocess.run([node, str(HERE / "density.cjs"), *map(str, GATED)], env=env, text=True)
    return run.returncode


if __name__ == "__main__":
    sys.exit(main())
