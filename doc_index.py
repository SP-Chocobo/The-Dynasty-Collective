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
import subprocess
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

#: WHICH FILES ARE DOCUMENTS OF THIS REPOSITORY -- asked of git, not of a hand-kept skip list.
#:
#: The first version walked the tree and subtracted a literal set, {".git", "node_modules",
#: "__pycache__", "worktrees"}. Every entry in that set was added after something went wrong:
#: a git worktree under `.claude/worktrees/` is a CHECKOUT of this repository rather than a set
#: of documents belonging to it, so walking them counted every file two or three times and made
#: the index depend on which directory the tool ran from -- it was built inside a worktree, where
#: they are absent, and went red the first time it ran from the main checkout. Then pytest's own
#: generated `.pytest_cache/README.md` appeared in the UNDECLARED bucket, and the list needed a
#: fifth entry it had no way to anticipate.
#:
#: That is a hand-maintained vocabulary standing in for a question something else already answers
#: (#126). `git ls-files` IS the answer: a file this repository tracks is a document of this
#: repository, and a file it does not track is not. Caches, vendored trees, build output and
#: worktree checkouts all fall out of scope without being named, including the ones nobody has
#: created yet. Run this from the repository root; it is a repo-level tool and writes a repo-level
#: artifact.
#:
#: ONE CONSEQUENCE, AND IT BITES ONCE: a brand-new document is INVISIBLE HERE UNTIL IT IS
#: STAGED, because git does not track it yet. Regenerate AFTER `git add`, not before -- the
#: staleness guard caught exactly this on the commit that added
#: `evidence/CERTIFICATION_DESIGN.md`, which had been written and the index regenerated in the
#: other order. That is the derivation being honest rather than a defect: an untracked file is
#: not yet a document of this repository, and the guard says so.
TRACKED_DOCS = ["git", "ls-files", "-z", "*.md"]


#: YAML FRONTMATTER IS METADATA ABOUT A FILE, NOT PROSE THE FILE ASSERTS.
#:
#: A skill file opens with a `---` fenced block whose `description:` is one long sentence
#: summarising everything the file covers. `engine-measurement/SKILL.md` says it encodes rules
#: "earned by withdrawing published findings in #222" -- an accurate description of a LIVE
#: checklist, and the classifier read the word "withdrawing" and filed the checklist itself as a
#: retracted claim. Frontmatter also eats most of the header budget, so the real opening line
#: ("This file is the checklist that would have caught them") never got looked at.
FRONTMATTER_FENCE = "---"


def body(text: str) -> list[str]:
    """The document's own lines, with a leading YAML frontmatter block removed. An unterminated
    fence is not frontmatter -- a document that happens to open with a horizontal rule keeps all
    of its lines rather than silently losing the rest of the file."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_FENCE:
        return lines
    for i in range(1, len(lines)):
        if lines[i].strip() == FRONTMATTER_FENCE:
            return lines[i + 1:]
    return lines


def header(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return "\n".join(body(text)[:HEADER_LINES])


def classify(path: Path) -> str:
    head = header(path)
    for name, pattern, _ in CLASSES:
        if re.search(pattern, head, re.IGNORECASE | re.MULTILINE):
            return name
    return "UNDECLARED"


def docs(root: Path = Path(".")) -> list[Path]:
    """Every markdown file this repository tracks, sorted. Raises rather than degrading: if git
    cannot answer, an index built from a tree walk would be a DIFFERENT index wearing the same
    filename, and the staleness guard would then fail for a reason that has nothing to do with
    the documents."""
    proc = subprocess.run(TRACKED_DOCS[:1] + ["-C", str(root)] + TRACKED_DOCS[1:],
                          capture_output=True, text=True, check=True)
    return sorted(Path(name) for name in proc.stdout.split("\0") if name)


#: The file this tool writes. It is excluded from its own input -- not as a curated exception
#: but because a tool classifying its own output is a loop, and this one closed badly: the
#: rendered legend ("| WITHDRAWN | 22 | a published claim taken back...") sits inside the first
#: twelve lines, so the index read its own vocabulary table as a status banner and listed itself
#: among the retracted findings. The index is not a document of the record; it is a view OF the
#: record.
OUTPUT = Path("DOC_INDEX.md")


def index(root: Path = Path(".")) -> dict[str, list[Path]]:
    buckets: dict[str, list[Path]] = {name: [] for name, _, _ in CLASSES}
    buckets["UNDECLARED"] = []
    for p in docs(root):
        if p == OUTPUT:
            continue
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
