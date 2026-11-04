"""#299 / `#126`: one home for "where is the Chromium this container pre-provisioned?"

THE LESSON WAS ALREADY LEARNED HERE AND DID NOT PROPAGATE, which is the whole argument for this
file existing. `ui_explore/round2/fableA/_shoot.py:320` carries this comment:

    # `chrome-linux/chrome` on one and `chrome-linux64/chrome` on another, and a glob knowing
    # only [one] ...

and globs `chrome-linux*/chrome` accordingly. `_domdiff.py` and `_converge.py` learned it too.
The two modules that gate TESTS did not:

    test_216_room_integrity.py   glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
    test_board_renders_absence.py  CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

Measured 2026-11-04 in this container, where the provisioned browser is
`/opt/pw-browsers/chromium-1243/chrome-linux64/chrome`: the first misses by the `64`, the second
misses by the `64` AND by 49 versions. Both gates therefore read "no browser here" and **16
board-EXECUTING tests skip** -- 10 of 22 in the first, 6 of 8 in the second -- out of 17 skips in
the whole suite.

`requirements.txt` already warns about this in prose, in its `playwright` comment: "a reclaimed
container ran the suite 14 tests lighter and reported OK. A freeze must be licensed by a suite
that ran, not one that quietly stood down." That warning was live and nobody was looking, because
a skip is not a failure and the count it moves is one nobody holds to a floor. Same family as
`#298`: not a crash, a plausible number about something else.

WHAT THIS KNOWS THAT EACH SCATTERED COPY DID NOT:

  * **Both directory layouts.** Playwright renamed `chrome-linux` to `chrome-linux64`. A glob
    that spells either one in full is a hostage to which image it was written against.
  * **The headless-shell package is a different product, not a fallback spelling.**
    `chromium_headless_shell-*/chrome-linux*/headless_shell` cannot do everything a full
    `chrome` can, so it is ranked below one and never substituted silently.
  * **Version suffixes sort NUMERICALLY, not lexically.** Every copy in this repo reaches for
    `sorted(glob(...))[-1]`, which is correct for `chromium-1194` vs `chromium-1243` and wrong
    the moment a three-digit build is present: `"1243" < "999"`, so lexical `[-1]` would choose
    build 999 over build 1243. No copy here had hit that yet. It is cheaper to fix than to wait
    for.
  * **The stable symlink.** This image also provides `/opt/pw-browsers/chromium`, which points at
    the real binary and survives a version bump. It is tried first, which is what makes the
    version sort a fallback rather than the primary mechanism.

WHAT IT DELIBERATELY DOES NOT DO. It does not run `playwright install` and does not suggest it:
`requirements.txt` says not to, because the browsers are pre-provisioned and a second download
lands somewhere the pinned package will not look. It does not raise when nothing is found --
callers differ, and a test module wants to SKIP with a named reason while a render gate wants to
die loudly. It returns `None` and lets each caller decide, which is the absence contract `#187`
asks for: `None` means "not found", never a path that will fail later.
"""

from __future__ import annotations

import glob
import os
import re
import shutil
from pathlib import Path

#: Searched in order. The first is a stable symlink this image provides; the globs are the
#: package layouts, full browser before headless shell.
SYMLINK = "/opt/pw-browsers/chromium"
GLOBS = (
    "/opt/pw-browsers/chromium-*/chrome-linux*/chrome",
    str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux*/chrome"),
    "/opt/pw-browsers/chromium_headless_shell-*/chrome-linux*/headless_shell",
    str(Path.home() / ".cache/ms-playwright/chromium_headless_shell-*/chrome-linux*/headless_shell"),
)
#: Last resort, and genuinely a different thing: whatever the system calls a browser.
ON_PATH = ("chromium", "chromium-browser", "google-chrome", "chrome")


def _build(path: str) -> int:
    """The numeric build in `chromium-1243`, or -1 when there is none to read.

    Sorting on this rather than on the string is the difference between choosing build 1243 and
    choosing build 999 -- see the module docstring.
    """
    found = re.findall(r"-(\d+)/", path)
    return int(found[0]) if found else -1


def candidates() -> list[str]:
    """Every executable this container offers, best first, with no side effects."""
    out: list[str] = []
    if os.path.exists(SYMLINK) and os.access(SYMLINK, os.X_OK):
        out.append(SYMLINK)
    for pattern in GLOBS:
        hits = [h for h in glob.glob(pattern) if os.access(h, os.X_OK)]
        out += sorted(hits, key=_build, reverse=True)
    for name in ON_PATH:
        found = shutil.which(name)
        if found:
            out.append(found)
    seen, unique = set(), []
    for path in out:
        real = os.path.realpath(path)
        if real not in seen:
            seen.add(real)
            unique.append(path)
    return unique


def find_chromium() -> str | None:
    """The best Chromium on this box, or None -- never a path that does not exist (`#187`)."""
    found = candidates()
    return found[0] if found else None


def why_not() -> str:
    """One sentence a skip message or a crash can carry, naming where it looked.

    A gate that says "needs a browser" sends the reader hunting; one that says which four places
    were searched is actionable. `requirements.txt` is named because it holds the rule against
    running `playwright install` to fix this.
    """
    return ("no Chromium found -- looked at " + SYMLINK + ", " + ", ".join(GLOBS)
            + ", and " + "/".join(ON_PATH) + " on PATH. The browsers are pre-provisioned; do "
            "NOT run `playwright install` (see requirements.txt).")


if __name__ == "__main__":
    best = find_chromium()
    print(best or why_not())
    for path in candidates():
        print(f"    build {_build(path):>5}  {path}")
