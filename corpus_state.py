"""Which body of data this session's numbers are computed from, said in one place.

THE QUESTION A USER CANNOT CURRENTLY ANSWER. Every price on the board is computed from whatever
files are in `data/` right now. That is sometimes only the committed baseline -- the set this
commit declares, that a fresh clone gets, and that every reproducibility claim rests on -- and
sometimes the baseline PLUS the user's own uploads. Those produce different numbers, and nothing
told anybody which one they were looking at.

WHY IT IS BOARD SCOPE AND NOT A PER-ROW MARK, which is the part that is easy to get wrong. An
uploaded projections file does not taint the rows it names. It changes REPLACEMENT LEVELS -- a
league-level quantity every player at that position is measured against -- so it moves prices for
players the file never mentions. `_drop_contested_identities`' own note already makes this exact
argument about phantom duplicates: "a second copy of a real player's points at his position moves
that position's replacement RANK". Marking uploads per row would therefore be a lie of scope: it
would clear rows the upload did in fact move.

WHAT IT IS NOT. Not a warning, and the wording matters. Uploading your own projections IS the
product -- most users are in `INCLUDES_LOCAL` essentially always. A state that is normal must
read as informative, or it becomes wallpaper and takes the genuinely loud marks down with it.
The loud ones are per-row and live elsewhere (draft_room.identity_basis, for an override that
moved one price).

THE DETECTOR IS BORROWED, DELIBERATELY. `baseline_manifest.diff()` already answers this: it was
built for #113/§19.4 so a CI run could say whether it was reproducible, and its own docstring
names the case verbatim -- "undeclared: present and not declared. The demonstrated case: a
user's own upload, or a planted file, silently entering the priced universe." One detector, two
consumers, and no second implementation to drift from the first.

ON "DOCTRINE". Today the committed baseline IS the shared set -- it is what every install gets
and what nobody's session has altered. When a server-maintained canonical set exists, it takes
that role and this module's states keep their meaning without renaming: the question is always
"is anything local in the mix", not "which host served it".
"""

from __future__ import annotations

from pathlib import Path

import baseline_manifest

#: Only the declared, committed set is loaded. Nothing local is in the mix.
DOCTRINE_ONLY = "doctrine_only"
#: The declared set plus files this install added. Normal, and the product working as intended.
INCLUDES_LOCAL = "includes_local"
#: The declared set is not intact -- files are missing or their bytes changed. NOT the same as
#: either state above: it means the baseline itself cannot be trusted to be the baseline, so
#: "am I on doctrine" has no answer rather than a negative one.
DIVERGED = "diverged"
#: No manifest to compare against. A FOURTH state, because "nothing is declared" and "nothing was
#: added" are opposite facts and defaulting to DOCTRINE_ONLY would claim the stronger one.
UNKNOWN = "unknown"


def assess(root: Path = Path("."), manifest_path: "Path | None" = None) -> dict:
    """{state, local_files, missing, changed} for the data this session computes from.

    `local_files` is the list itself rather than a count, because "which file" is the first thing
    a user asks and recomputing it at the call site would mean two detectors again.

    The manifest path is resolved from `baseline_manifest.MANIFEST_PATH` AT CALL TIME rather than
    taken as a default argument. `baseline_manifest.load`/`diff` bind theirs at def time, so a
    caller that repoints the module attribute -- which is how every test in this repo isolates
    itself from the real data directory -- would silently be answered about the real tree while
    believing it asked about its own. Found by exactly that test.
    """
    path = manifest_path or baseline_manifest.MANIFEST_PATH
    if not baseline_manifest.load(path):
        return {"state": UNKNOWN, "local_files": [], "missing": [], "changed": []}
    result = baseline_manifest.diff(root, path)
    if result["missing"] or result["changed"]:
        # Checked before INCLUDES_LOCAL: a baseline that is not intact is a different and worse
        # situation than a baseline with additions, and reporting the additions would bury it.
        state = DIVERGED
    elif result["undeclared"]:
        state = INCLUDES_LOCAL
    else:
        state = DOCTRINE_ONLY
    return {"state": state, "local_files": result["undeclared"],
            "missing": result["missing"], "changed": result["changed"]}


def light(assessment: dict) -> tuple[str, str]:
    """(icon, sentence) for one status line. Tone is part of the contract, not decoration.

    DOCTRINE_ONLY and INCLUDES_LOCAL are both NORMAL and both read calmly -- one is not a
    degraded version of the other, and dressing the common case as a caution is how a real
    caution stops being read. DIVERGED is the only one that raises its voice, because it is the
    only one where a number might not mean what the commit says it means.
    """
    state = assessment["state"]
    if state == DOCTRINE_ONLY:
        return ("🟢", "Computing from the shared baseline only — no local data in the mix.")
    if state == INCLUDES_LOCAL:
        count = len(assessment["local_files"])
        return ("🔵", f"Computing from the shared baseline **plus {count} file"
                      f"{'s' if count != 1 else ''} you added.** Your uploads change replacement "
                      f"levels, so they move prices league-wide, not only for the players they "
                      f"name — that is them working, not a problem.")
    if state == DIVERGED:
        broken = len(assessment["missing"]) + len(assessment["changed"])
        return ("🔴", f"The shared baseline is not intact — {broken} declared file"
                      f"{'s are' if broken != 1 else ' is'} missing or altered. Prices computed "
                      f"now may not mean what this version says they mean.")
    return ("⚪", "No input manifest, so what this session is computing from is unrecorded — "
                 "not the same as knowing it is clean.")
