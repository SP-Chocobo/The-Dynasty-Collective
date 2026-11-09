"""`#355`: every item number cited in the tree resolves to the register, or the build fails.

WHAT `#353` COST, AND WHY THE RULE ALONE WAS NOT ENOUGH. Four items -- `#345`, `#349`, `#350`,
`#351` -- carried commits and code citations with no register entry. One was worse than missing:
`test_priced_travels_with_value.py` told its reader a finding was "recorded as `#351`" when no
entry existed. A committed test asserting its own provenance MANUFACTURES it; the next reader goes
looking, finds nothing, and cannot tell whether the record was lost or the claim was false.

`HANDOFF.md`'s own header already stated the rule it broke -- *"The register holds the reasoning;
this holds the STATE and the NEXT ACTIONS"* -- and the drift happened anyway, because nothing
checked it. A rule enforced only by prose is the weak form (`#352`). This is the instrument.

WHY IT COUNTS MENTIONS AND NOT HEADINGS, which is the mistake this file exists because I made.
Sizing the gap took three instruments and two gave confident wrong answers:

    1. headings only, read off a `| head`-truncated grep   -- the one row that mattered was cut
       off a 47-row result.
    2. heading present / absent                 -> 80 unrecorded.  WRONG. It measured the
       CONVENTION, not the record: per-item headings are RECENT, and early items are recorded in
       prose and in tables. `#187` is cited in 97 files and appears 30 times in the register --
       with no heading anywhere. Eighty was published before it was corrected.
    3. mentioned anywhere, bounded to 1-3 digits -> 9 unrecorded, of 221 cited.

So the test is MENTION, not heading. An item recorded in a paragraph is recorded. And the digit
bound is not cosmetic: `#755024`, `#141109` and `#171309` are HEX COLOURS in design documents, and
a 6-digit match reads every one of them as a register item that does not exist.

A FOURTH VARIANT WAS MEASURED AND REJECTED, and the reason is the same error in a new costume.
Requiring the register to cite back in BACKTICKS -- symmetric with how this file reads citations --
gives 17 rather than 0, and that looked like the stricter, better rule. It is not: THE REGISTER
USES BOTH FORMS. Its headings carry `` `#348` `` and its prose carries a bare `#187`, `#166`,
`#174`. So a backtick requirement measures the register's internal formatting inconsistency, not
whether a record exists -- attempt 2's mistake exactly, which is how close it stays to the surface.
The 17 are items the register discusses without backticking them; that is worth tidying and is not
this instrument's business.

THE BASELINE IS ZERO, AND ITS PROVENANCE MATTERS. When `#353b` was written it listed the nine
then-unmentioned items BY NUMBER while explaining that they were unmentioned -- so documenting the
gap closed the gap as this instrument measures it. That observer effect is real and is recorded at
`#355`. It is a legitimate closure rather than an accident that hid something: a reader who looks
up `#34` now reaches `#353b`, which states what `#34` is and why it has no entry, and traceability
was the requirement `#353` set. But the number must be read knowing how it got there.

WHICH MEANS THE OBVIOUS LIMIT, STATED PLAINLY: this cannot tell a RECORD from a MENTION-AS-GAP.
Naming an item in a list of things that lack entries satisfies it. No text-matching instrument can
make that distinction, so it is not a defect to be fixed here -- it is the boundary of what this
check is evidence for. What it DOES hold, with a zero baseline, is strong and worth having: a
citation of an item the register has never named anywhere cannot enter the tree quietly.

WHY GROWTH AND NOT ZERO. Nine items are cited and unmentioned today, and driving that to zero
would mean INVENTING ENTRIES for items that may not be items at all -- `#3` and `#7` appear only
in `ui_explore/round2/fableA/REVISION.md` and are almost certainly revision numbers, and `#218`
appears only in a skill file. Writing a register entry to satisfy a counter is the exact defect
`#351` records. So this takes `skip_gates`' bargain rather than `assertion_floors`': the baseline
is recorded, GROWTH fails the build, and shrinkage is free. A new unmentioned citation must either
get its entry or be argued for in the commit.

BARE INVOCATION RUNS THE CHECK. `skip_gates.py` with no arguments printed its help text and exited
0, which at the call site is indistinguishable from a pass -- and that is precisely how "all 8
ratchets PASS" came to be published about a ratchet that had examined nothing (`#352`). A
verification tool must not have a zero-exit path that verifies nothing, so here the check is the
DEFAULT and the listing and the re-baseline are the flags.

WHAT IT CANNOT SEE, stated because a check whose limits are unstated gets trusted past them:

  * It cannot tell a RECORD from a MENTION, nor either from a MENTION-AS-GAP. An item named
    once in passing counts as recorded. That is deliberate -- both alternatives were measured and
    are wrong -- but it means this cannot catch a citation whose entry is a stub.
  * It only reads BACKTICKED `#NNN`. A bare `#351` in prose is invisible to it. That is the
    repo's own convention and keeps hex colours and issue-tracker numbers out, but a citation
    written without backticks is uncounted.
  * It says nothing about whether an entry is TRUE, only that it exists.
  * It does not read `HANDOFF.md` differently from any other document. `#353` assigns HANDOFF the
    STATE, and a HANDOFF row referencing an item is a legitimate citation -- so an item recorded
    ONLY in HANDOFF still counts as cited-and-unmentioned here, which is the case that started
    this.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import subprocess

import store_io

#: Backticked, one to three digits, optional letter suffix (`#345b`). The digit bound is what
#: keeps six-digit hex colours out; see the docstring.
ITEM = re.compile(r"`#(\d{1,3})[a-z]?`")

REGISTER = pathlib.Path("POST_AUDIT_PLAN.md")
BASELINE = pathlib.Path("REGISTER_INDEX.json")

#: Documents that are HISTORY, not live record. An item cited only in a frozen evidence file is
#: not a claim about the current tree. Kept narrow and explicit: a wildcard here would silently
#: swallow new citations, which is the failure this whole file exists to prevent.
HISTORY_PREFIXES = ("evidence/",)


def _tracked(*globs: str) -> list[pathlib.Path]:
    """Git-tracked files only, so an untracked scratch file cannot fail somebody's build."""
    out = subprocess.run(["git", "ls-files", "-z", *globs],
                         capture_output=True, text=True, check=True)
    return [pathlib.Path(p) for p in out.stdout.split("\0") if p]


def cited(include_history: bool = False) -> dict[int, set[str]]:
    """item number -> the files citing it, excluding the register itself."""
    found: dict[int, set[str]] = collections.defaultdict(set)
    for path in _tracked("*.py", "*.md"):
        name = path.as_posix()
        if name == REGISTER.name:
            continue
        if not include_history and name.startswith(HISTORY_PREFIXES):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for num in ITEM.findall(text):
            found[int(num)].add(name)
    return dict(found)


def mentions(register_text: str | None = None) -> set[int]:
    """Every item number the register mentions ANYWHERE -- heading, table, or paragraph."""
    text = REGISTER.read_text(encoding="utf-8") if register_text is None else register_text
    return {int(m) for m in re.findall(r"#(\d{1,3})\b", text)}


def unrecorded(register_text: str | None = None,
               include_history: bool = False) -> dict[int, list[str]]:
    """Items cited in the tree that the register never mentions. The quantity under ratchet."""
    known = mentions(register_text)
    return {item: sorted(files)
            for item, files in sorted(cited(include_history).items())
            if item >= 1 and item not in known}


def load() -> dict:
    if not BASELINE.exists():
        return {}
    try:
        return json.loads(BASELINE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def write() -> dict[int, list[str]]:
    """Through `store_io`, like every other baseline in this repo.

    The first draft wrote the file directly and `test_store_io` caught it -- correctly: an
    atomic replace is the house rule for anything on disk, and `store_io.write` RETURNS A BOOL
    because it can decline to overwrite a damaged store (`#52` phase 7.5). A caller that ignores
    that bool reports success for bytes that never landed, so this one does not ignore it.
    """
    gap = unrecorded()
    landed = store_io.write(BASELINE, {
        "_comment": (
            "Items cited in tracked .py/.md that POST_AUDIT_PLAN.md never mentions -- see "
            "register_index.py. GROWTH is the regression: a new unmentioned citation must either "
            "get a register entry or be argued for in the commit message. Shrinkage is free. "
            "This is NOT a to-do list -- driving it to zero would mean inventing entries for "
            "items that may not be items. Regenerate with `python3 register_index.py --write`."),
        "total": len(gap),
        "items": {str(k): v for k, v in gap.items()},
    })
    if not landed:
        raise SystemExit(f"{BASELINE} was NOT written -- store_io declined, which it does to "
                         f"avoid overwriting a damaged store. Inspect the file by hand.")
    return gap


def appeared() -> list[str]:
    """Citations unmentioned NOW that the baseline did not record. Growth only."""
    recorded = {int(k) for k in (load().get("items") or {})}
    return [f"#{item} is cited in {', '.join(files)} and the register never mentions it"
            for item, files in unrecorded().items() if item not in recorded]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="re-record the current baseline")
    parser.add_argument("--check", action="store_true",
                        help="exit non-zero if a new unmentioned citation appeared (THE DEFAULT)")
    parser.add_argument("--list", action="store_true",
                        help="print every cited item and whether the register mentions it")
    args = parser.parse_args(argv)

    if args.list:
        known = mentions()
        for item, files in sorted(cited().items()):
            mark = "   " if item in known else ">> "
            print(f"{mark}#{item:<4} {len(files):>3} file(s)  {', '.join(files[:3])}")
        return 0

    if args.write:
        gap = write()
        print(f"wrote {BASELINE} -- {len(gap)} cited item(s) the register never mentions, "
              f"of {len(cited())} cited")
        return 0

    # NO FLAG RUNS THE CHECK. There is deliberately no zero-exit path that verifies nothing;
    # that path is what let "all 8 ratchets PASS" be published about a ratchet that ran its
    # help text (`#352`).
    recorded = load()
    if not recorded:
        print(f"{BASELINE} records no baseline (missing or damaged). This check is holding "
              f"NOTHING, which is not the same as no citation having appeared. Run --write.")
        return 1
    grew = appeared()
    if grew:
        print("An item is cited in the tree and the register never mentions it. Write the entry, "
              "or -- if it is not a register item at all -- say so in the commit and rerun with "
              "--write so the baseline change lands in the diff:\n")
        for line in grew:
            print(f"  {line}")
        return 1
    gap = unrecorded()
    print(f"every cited item resolves to the register, or is a recorded exception "
          f"({len(gap)} exception(s) across {len(cited())} cited items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
