"""Which of this repository's documents are live, and which are history kept for the record?

WHY THIS EXISTS. There are over a hundred markdown files here and most are EVIDENCE -- a finding,
a pre-registration, a result, a withdrawal. Several state things that were true when written and
are not true now. The repo's discipline is that a superseded claim is struck and explained IN
PLACE rather than deleted, which is right, but it means a reader cannot tell from a filename
whether `FINDING_the_battery_never_varies_te_premium.md` is a live finding or a retracted one.
(It is retracted. Nothing in its name says so.)

DERIVED, NOT HAND-LISTED (#126). This walks the files and reads what each one says about itself.
There is no curated list of "the withdrawn ones" to go stale -- add a document tomorrow and it
appears here tomorrow, classified by its own opening lines or flagged as undeclared.

THE OUTPUT THAT MATTERS IS THE UNDECLARED LIST. A document with a status banner is doing its job
whatever the status says. A document with none is asking every reader to work it out alone.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

#: How far into a file a status declaration has to appear to count. A banner buried on line 200
#: is not a banner -- the reader has already believed the opening by then.
HEADER_LINES = 12

#: The vocabularies, in precedence order: a file that says both "withdrawn" and "status" is
#: withdrawn. Each pattern is matched case-insensitively against the header block.
#:
#: MATCH ON STEMS, NOT WHOLE WORDS. The first version used "withdrawn" and "corrected", and
#: sorted WITHDRAWAL_18_residual3_detector.md and CORRECTION_wrong_universe.md -- both of which
#: announce exactly what they are in their own H1 -- into UNDECLARED. A classifier that misses
#: the plainest cases inflates the bucket it exists to draw attention to.
CLASSES: list[tuple[str, str, str]] = [
    ("WITHDRAWN", r"withdraw|retract|⛔",
     "a published claim taken back. Kept, unedited, beneath its banner."),
    ("SUPERSEDED", r"supersede|no longer the whole answer|replaces an earlier version|"
                   r"\bstale\b|correct(ed|ion)",
     "still valid or partly valid, but something later changed what it means."),
    ("DECLARED", r"^\s*>?\s*\*?\*?status\b|this (file|document) is|what this is|"
                 r"vision document|session log|standing doctrine|pre-?registrat",
     "says what kind of document it is before making claims."),
]

SKIP_DIRS = {".git", "node_modules", "__pycache__"}


def header(path: Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[:HEADER_LINES])


def classify(path: Path) -> str:
    head = header(path)
    for name, pattern, _ in CLASSES:
        if re.search(pattern, head, re.IGNORECASE | re.MULTILINE):
            return name
    return "UNDECLARED"


def docs(root: Path = Path(".")) -> list[Path]:
    out = []
    for p in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        out.append(p)
    return out


def index(root: Path = Path(".")) -> dict[str, list[Path]]:
    buckets: dict[str, list[Path]] = {name: [] for name, _, _ in CLASSES}
    buckets["UNDECLARED"] = []
    for p in docs(root):
        buckets[classify(p)].append(p)
    return buckets


def render(buckets: dict[str, list[Path]]) -> str:
    total = sum(len(v) for v in buckets.values())
    lines = [
        "# Document index — derived, not curated",
        "",
        f"`python3 doc_index.py` regenerates this. {total} markdown documents.",
        "",
        "Classified by what each file says about ITSELF in its first "
        f"{HEADER_LINES} lines. Nothing here is a judgement about whether a document is *good* — "
        "only about whether it tells a cold reader what it is before it starts making claims.",
        "",
        "| class | count | meaning |",
        "|---|---:|---|",
    ]
    meanings = {name: why for name, _, why in CLASSES}
    meanings["UNDECLARED"] = ("no status banner in its opening. Not necessarily wrong — most are "
                              "simply current — but a reader cannot tell without reading it all.")
    for name in [n for n, _, _ in CLASSES] + ["UNDECLARED"]:
        lines.append(f"| {name} | {len(buckets[name])} | {meanings[name]} |")
    for name in [n for n, _, _ in CLASSES] + ["UNDECLARED"]:
        lines += ["", f"## {name}", ""]
        if not buckets[name]:
            lines.append("_none_")
            continue
        for p in buckets[name]:
            lines.append(f"- `{p.as_posix()}`")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    buckets = index()
    text = render(buckets)
    if "--check" in argv:
        existing = Path("DOC_INDEX.md")
        if not existing.exists() or existing.read_text(encoding="utf-8") != text:
            print("DOC_INDEX.md is stale -- run `python3 doc_index.py`")
            return 1
        print("DOC_INDEX.md current")
        return 0
    Path("DOC_INDEX.md").write_text(text, encoding="utf-8")
    for name, items in buckets.items():
        print(f"{name:12s} {len(items):3d}")
    print("-> DOC_INDEX.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
