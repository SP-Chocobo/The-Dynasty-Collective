"""Does `doc_index` spend its 12-line header budget on the house banner?

`classify` does `_without_boilerplate(header(path))`, and `header` truncates to HEADER_LINES
FIRST. So for a document carrying the shared `WHERE CURRENT STATE LIVES` blockquote, the budget
is spent on the banner and only what is left is examined -- while a document without the banner
gets all 12 lines of its own prose. `body()` already fixes exactly this for YAML frontmatter
("Frontmatter also eats most of the header budget"); the banner is stripped in the other order.

This measures the consequence on the real corpus: documents in the UNDECLARED bucket that WOULD
classify if the 12 lines were counted after the banner came out, as `body()` does for
frontmatter. UNDECLARED is the bucket the tool's own docstring calls "the output that matters".

Run from the repo root:
  PYTHONPATH=. python3 evidence/blind_pass_v4/probes/probe_doc_index_header_budget.py
"""
import re
from pathlib import Path

import doc_index as di


def classify_banner_first(path: Path) -> str:
    """`classify`, with the two steps in the other order: strip the banner, THEN take 12 lines."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    whole = "\n".join(di.body(text))
    head = "\n".join(di._without_boilerplate(whole).splitlines()[:di.HEADER_LINES])
    for name, pattern, _ in di.CLASSES:
        if re.search(pattern, head, re.IGNORECASE | re.MULTILINE):
            return name
    return "UNDECLARED"


def main() -> None:
    buckets = di.index()
    total = sum(len(v) for v in buckets.values())
    print(f"documents classified          : {total}")
    for name in list(buckets):
        print(f"  {name:12s} {len(buckets[name]):3d}")

    bannered = [p for p in di.docs() if p != di.OUTPUT
                and di._BOILERPLATE_BANNER in "\n".join(di.body(
                    p.read_text(encoding='utf-8', errors='replace')))]
    print(f"\ndocuments carrying the house banner anywhere: {len(bannered)}")

    moved = []
    for p in buckets["UNDECLARED"]:
        other = classify_banner_first(p)
        if other != "UNDECLARED":
            moved.append((p, other))
    print(f"UNDECLARED today that WOULD classify if the banner were stripped "
          f"before the 12-line cut: {len(moved)}")
    for p, other in moved:
        print(f"   {other:11s} {p.as_posix()}")

    # And the reverse direction, for completeness: anything that classifies today only because
    # the budget is spent differently.
    lost = []
    for name in ("WITHDRAWN", "SUPERSEDED", "DECLARED"):
        for p in buckets[name]:
            if classify_banner_first(p) == "UNDECLARED":
                lost.append((p, name))
    print(f"\nclassified today but UNDECLARED under the other order: {len(lost)}")
    for p, name in lost:
        print(f"   was {name:11s} {p.as_posix()}")


if __name__ == "__main__":
    main()
