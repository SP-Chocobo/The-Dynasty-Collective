"""The docks' gate and density instrument: `python3 mockups/dock_smoke.py` from the repo root.
Runs dock_gate.cjs, then dock_density.cjs, in a real Chromium via Playwright (NODE_PATH set so
the global `playwright` resolves), then rebuilds dock_index.html so its table carries the
fresh numbers. Exit code is the gate's."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
PAGES = sorted(HERE.glob("dock_[0-9]_*.html"))


def main() -> int:
    node = shutil.which("node")
    if node is None:
        print("node not found; the gate cannot run")
        return 1
    root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
    env = dict(os.environ, NODE_PATH=root)
    if not PAGES:
        print("no dock pages built; run mockups/dock_build.py first")
        return 1
    run = subprocess.run([node, str(HERE / "dock_gate.cjs"), *map(str, PAGES)], env=env, text=True)
    print("\ndensity at 1400 x 1400 (dock_density.cjs):")
    subprocess.run([node, str(HERE / "dock_density.cjs"), *map(str, PAGES)], env=env, text=True)
    subprocess.run([sys.executable, str(HERE / "dock_build.py")], text=True, capture_output=True)
    return run.returncode


if __name__ == "__main__":
    sys.exit(main())
