"""The UI surface, as one searchable text, so source-scanning tests survive the hull extraction.

WHY THIS EXISTS. Sixteen test modules read `app.py` off disk and assert against its text --
65 `assertIn`s and 8 `assertNotIn`s. `app.py` is a 6,000-line top-level Streamlit script that
cannot be imported (it runs straight into session-dependent state), so source scanning is the
only coverage those contracts have. It is about to be cut apart by view.

The two directions fail differently when a view leaves `app.py`, and only one of them is loud:

  - `assertIn("...", app_source)`  -- FAILS. The text is no longer in the file. Noisy, safe,
    self-announcing. The real cost is hand-repairing 65 of them mid-refactor, which is exactly
    the condition under which someone points a test at the wrong file.

  - `assertNotIn("...", app_source)` -- PASSES. Forever. It asserts a forbidden pattern is
    absent, and after the move the pattern IS absent from `app.py` -- because the code it was
    written to police now lives somewhere else, unexamined. The guard is still green and no
    longer guards anything.

The second is why this module has to land BEFORE the first view moves rather than alongside
it. A correct guard that can never execute is the defect class this repo keeps finding; doing
it to ourselves during the one operation that most needs the guards working would be careless.

WHAT IT DOES. `text()` returns every UI module's source joined into one string, so `in` and
`not in` keep meaning "somewhere in the UI" rather than "in this particular file".

THE MODULE LIST IS DERIVED, NOT ENUMERATED. A hand-kept list is a list someone has to remember
to extend, which is the same failure one level up: extract a view, forget the list, and this
module quietly narrows back to `app.py` while every caller still believes it is searching the
whole surface. So the surface is defined by a property instead -- a module is UI if it imports
Streamlit. A view that renders calls `st.*`; to call `st.*` it imports streamlit. Today that
set is exactly `{app.py}`, so `text()` is byte-identical to the old `read_text()` and this
whole module is a no-op. It starts paying the moment the first view moves.

STATED LIMITATION: a view module that took `st` as a parameter instead of importing it would
not be detected. Nothing does that today, and nothing should -- but the rule is a property of
how views are written, not something enforced here.

POSITION IS A PER-FILE QUESTION. Several tests slice (`source[start:end]`, "the block after
this anchor"). Across a concatenation those offsets stop meaning anything, so slicing callers
use `unit_containing()` and get the single file that holds their anchor. `test_ui_source`
forbids subscripting `text()` directly, because a slice that silently spans two files is the
kind of green nonsense this module exists to prevent.
"""

from __future__ import annotations

import re
from pathlib import Path

_HERE = Path(__file__).parent

#: Filename prefixes that are never part of the shipped UI surface, matching the convention
#: `test_store_io`'s scan already uses: tests and developer-run scripts.
_NOT_PRODUCTION = ("test_", "run_", "compare_")

#: Module-level `import streamlit` / `from streamlit import ...`. Anchored to column zero on
#: purpose: a deferred import inside a function is not what makes a module a UI surface, and
#: matching one would pull in modules that merely touch Streamlit in a fallback path.
_IMPORTS_STREAMLIT = re.compile(r"^(?:import streamlit|from streamlit\b)", re.MULTILINE)

#: Inserted between concatenated modules. Two jobs. It labels which file the following text
#: came from, so a failure message can say where to look. And it makes false adjacency
#: impossible: a multi-line needle can only match across a boundary by containing this line,
#: which no assertion in the suite does or could plausibly do.
_BOUNDARY = "\n\n# ==================== ui_source boundary: {name} ====================\n\n"


def modules(root: Path = _HERE) -> list[str]:
    """Filenames of the UI surface, sorted, with `app.py` first if present.

    `app.py` leads because it is the hull every other UI module is being carved out of, and a
    concatenation that starts anywhere else would make the diffs harder to read for no reason.
    """
    found = []
    for path in sorted(root.glob("*.py")):
        if path.name.startswith(_NOT_PRODUCTION) or path.name == Path(__file__).name:
            continue
        if _IMPORTS_STREAMLIT.search(path.read_text()):
            found.append(path.name)
    return sorted(found, key=lambda n: (n != "app.py", n))


def units(root: Path = _HERE) -> dict[str, str]:
    """{filename: source} for every UI module, in `modules()` order."""
    return {name: (root / name).read_text() for name in modules(root)}


def text(root: Path = _HERE) -> str:
    """Every UI module's source as one string, boundary-separated.

    Use for `assertIn` / `assertNotIn`. Do not subscript the result -- see `unit_containing`.
    """
    parts = units(root)
    if len(parts) == 1:
        # Byte-identical to the old `(_HERE / "app.py").read_text()`. No boundary marker is
        # inserted for a single module, so today's migration changes no assertion's meaning.
        return next(iter(parts.values()))
    out = []
    for name, source in parts.items():
        out.append(_BOUNDARY.format(name=name))
        out.append(source)
    return "".join(out)


def unit_containing(needle: str, root: Path = _HERE) -> str:
    """The source of the single UI module containing `needle`, for positional work.

    Raises rather than returning the first hit when two modules both contain it: an anchor that
    is not unique across the surface cannot identify a block, and silently picking one would
    hand the caller offsets into a file it did not mean.
    """
    hits = [name for name, source in units(root).items() if needle in source]
    if not hits:
        raise AssertionError(
            f"no UI module contains {needle!r} -- searched {', '.join(modules(root))}"
        )
    if len(hits) > 1:
        raise AssertionError(
            f"{needle!r} appears in {len(hits)} UI modules ({', '.join(hits)}); it cannot "
            f"anchor a block. Use an anchor unique to the module you mean."
        )
    return units(root)[hits[0]]


def unit_name_containing(needle: str, root: Path = _HERE) -> str:
    """Which UI module holds `needle`. Same uniqueness rule as `unit_containing`."""
    hits = [name for name, source in units(root).items() if needle in source]
    if len(hits) != 1:
        unit_containing(needle, root)  # raises with the right message
    return hits[0]


def block(anchor: str, until: str | None = None, *, chars: int | None = None,
          root: Path = _HERE) -> str:
    """The span of one UI module starting at `anchor`.

    Every slicing caller in the suite was the same three lines -- find an anchor, find a
    terminator after it, slice between -- written out eight times against a raw `app.py`
    string. Collected here so the slice is taken from the file that actually holds the anchor
    rather than from a concatenation, where the offsets would mean nothing.

    `until` ends the span at the next occurrence of that text (searched AFTER the anchor, so
    an anchor that is also a terminator does not end its own block). `chars` takes a
    fixed-width window instead. Neither: the rest of the file.

    A span that reaches the end of its module is returned as-is. It cannot silently continue
    into the next module, which is the entire reason this is not a slice of `text()`.
    """
    if until is not None and chars is not None:
        raise TypeError("block() takes `until` or `chars`, not both")
    source = unit_containing(anchor, root)
    start = source.index(anchor)
    if chars is not None:
        return source[start:start + chars]
    if until is None:
        return source[start:]
    try:
        return source[start:source.index(until, start + len(anchor))]
    except ValueError:
        # The terminator is missing, which usually means the block moved or was renamed. Say
        # so, rather than letting `.index` raise a bare ValueError with no anchor in it.
        raise AssertionError(
            f"found {anchor!r} in {unit_name_containing(anchor, root)} but no {until!r} "
            f"after it -- the block's end marker moved or was renamed"
        ) from None


def offsets(*needles: str, root: Path = _HERE) -> tuple[int, ...]:
    """Positions of several anchors, guaranteed to be within one UI module.

    For the ordering checks ("this consume happens before that widget"). Comparing offsets
    from two different files would be arithmetic on unrelated rulers -- a comparison that
    still returns True or False and means nothing -- so this refuses instead.
    """
    homes = {n: unit_name_containing(n, root) for n in needles}
    if len(set(homes.values())) > 1:
        placed = "; ".join(f"{n!r} in {h}" for n, h in homes.items())
        raise AssertionError(
            f"cannot compare positions across UI modules ({placed}). Ordering is only "
            f"meaningful within one file."
        )
    source = units(root)[next(iter(homes.values()))]
    return tuple(source.index(n) for n in needles)
