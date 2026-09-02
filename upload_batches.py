"""An upload is a SET of files with one story, and that story is worth storing once.

WHAT WAS MISSING. Uploaded files landed in a directory as anonymous individuals. Nothing recorded
that six of them came out of one export session, nothing recorded when that session's data was
from, and nothing recorded what the user thought they were handing over. Three consequences, all
of them measured elsewhere in this audit rather than hypothesised:

  * PRECEDENCE GUESSED. `load_projection_file` filled an absent source_date from the file's mtime
    -- "when this landed on my disk", not "when this data was true". §19.4's own note records
    mtime breaking real numbers twice, and `_negated_date` already has the correct branch for an
    undated file ("sorts after any digit-complement, so undated rows lose to dated ones") which
    the mtime fallback made UNREACHABLE. Nothing was ever undated, so the safe path never ran.
  * CONTEXT LOST. A chair reading `export(3).csv` learns nothing. The user knew what it was at
    the moment they uploaded it, and that was the only moment anybody asked.
  * NO UNDO UNIT. Removing "that thing I uploaded last Tuesday" meant finding six files by hand.

WHY THE BATCH AND NOT THE FILE is the unit. You export four format variants from one tool in one
sitting: same source, same as-of date, same intent. That is ONE fact, and asking for it four
times produces four chances to answer inconsistently. The batch is also the only thing that can
carry an identity -- a file already has a name, a set of files had nothing.

WHAT IS DELIBERATELY *NOT* BATCH-LEVEL. **Format.** The whole reason ten ranking files exist is
that they cover the same players under different format assumptions -- Bowers' trade_value ranges
36-96 across them, a ~2.7x swing decided purely by which one wins a tiebreak. A batch-level
format field would assert that dynasty-ppr and dynasty-superflex uploaded together are the same
thing, when differing is their entire purpose. Format stays per file, and is asked AFTER parsing
rather than before -- only about the files whose format could not be worked out, so the question
is earned rather than a slot on a form.

THE NAME AND NOTE ARE PROSE AND GATE NOTHING. They are for the user's own reference and for
debate context. They are never parsed for meaning and never feed precedence: a display name that
happened to contain "superflex" must not quietly become a format claim, or a user would have to
guess a regex's vocabulary to be understood. Stated facts (the as-of date) go in their own field
where they can be shown, checked, and marked as stated.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import store_io

BATCHES_PATH = Path("data/projections/_uploads.json")

#: Where an as-of date came from. Three states, and the third is why this is not a bare string:
#: a date the user typed and a date the file declared are both real, but only one of them is a
#: claim somebody made, and only one can be wrong in a way a human could correct.
DATE_STATED = "stated"        # the user told us at upload time
DATE_DECLARED = "declared"    # the file carried its own source_date column
DATE_UNKNOWN = "unknown"      # nobody said, and we are NOT inventing one from mtime


def _load() -> list[dict]:
    return store_io.read(BATCHES_PATH, [])


@store_io.atomic(lambda *a, **k: BATCHES_PATH)
def record(*, name: str, note: str = "", as_of: Optional[str] = None,
           files: Optional[list[str]] = None,
           league_ids: Optional[list[str]] = None) -> str:
    """Store one upload batch and return its id.

    `as_of` is the date the DATA is from, not the date it was uploaded -- those are different
    facts and the repo has already been bitten by conflating them (see DynastyProcess's own
    ATTRIBUTION distinguishing its scrape_date from the pull date). `uploaded_at` records the
    second one for free, since it is simply now.

    A batch with no `as_of` is recorded anyway and stays honest about it. Refusing the upload
    would make the field required, and a required date field gets typed through -- a wrong date
    is worse than an absent one, because precedence acts on it and is then confidently wrong.
    """
    batches = _load()
    batch_id = uuid.uuid4().hex[:12]
    batches.append({
        "id": batch_id,
        "name": (name or "").strip() or "Untitled upload",
        "note": (note or "").strip(),
        "as_of": (as_of or "").strip() or None,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d"),
        "ts": time.time(),
        "files": list(files or []),
        "league_ids": list(league_ids or []),
    })
    store_io.write(BATCHES_PATH, batches)
    return batch_id


def batches() -> list[dict]:
    """Newest first -- the review section's own order."""
    return sorted(_load(), key=lambda b: b.get("ts", 0), reverse=True)


def for_file(relative_path: str) -> Optional[dict]:
    """The batch a given file arrived in, or None.

    Newest wins if a path somehow appears twice: re-uploading the same filename is a real thing
    users do, and the later upload is the one that describes what is on disk now.
    """
    for batch in batches():
        if relative_path in batch.get("files", []):
            return batch
    return None


def stated_as_of(relative_path: str) -> Optional[str]:
    """The as-of date the user gave for this file's batch, or None. The one thing precedence
    reads out of this module."""
    batch = for_file(relative_path)
    return (batch or {}).get("as_of")


def date_basis(stated: Optional[str], declared: Optional[str]) -> str:
    """Which of the three states a file's source_date is in.

    Order is stated > declared, and that is deliberate: a person looking at the file and saying
    when it is from outranks a column, because the column can be a template default, a copy of a
    neighbouring export's header, or simply wrong -- and the person is the one who can be asked.
    """
    if stated:
        return DATE_STATED
    if declared:
        return DATE_DECLARED
    return DATE_UNKNOWN


def resolve_source_date(stated: Optional[str], declared: Optional[str]) -> Optional[str]:
    """The date precedence should use, or None.

    None is a real answer and the caller must not fill it in. `_negated_date` already knows what
    to do with it -- an undated row loses every tie rather than winning one on an accident -- and
    that branch only becomes reachable once something stops inventing a date first.
    """
    return stated or declared or None


@store_io.atomic(lambda *a, **k: BATCHES_PATH)
def forget(batch_id: str) -> Optional[dict]:
    """Drop the batch RECORD and return it, so a caller can delete the files it names.

    Deliberately does not touch the filesystem: this module owns a record, not a directory, and
    a store that deletes data on another layer's behalf is the kind of coupling that makes an
    undo hard to reason about. The caller removes the files it was just handed the list of.
    """
    batches_now = _load()
    for index, batch in enumerate(batches_now):
        if batch.get("id") == batch_id:
            removed = batches_now.pop(index)
            store_io.write(BATCHES_PATH, batches_now)
            return removed
    return None
