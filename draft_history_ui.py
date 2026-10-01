"""Reading a stored draft board back — the MINIMAL reader mandate 1.7 asked for, and no more.

`draft_history` has had `load_snapshot_record`, `list_snapshot_records` and `snapshot_ids` since it
was written, and they work. What never existed was a surface that CALLS them: `app.py` recorded
boards and read none, so the store was write-only in the product and the mandate's own text said
closing it properly was a feature call rather than a defect fix.

WHAT THIS IS, AND WHAT IT DELIBERATELY IS NOT. It lists the boards a league has stored, each with
the staleness verdict for THIS moment, and shows one board's candidate table on request. It does not
replay a panel, re-run a debate, or offer a stored board as a basis for a decision now. That was the
open product question — whether a replayed board may look like a live one — and the answer this
module implements is NO, unconditionally: every stored board carries `STORED_BOARD_NOTICE` and its
own staleness reason, whether or not the world has moved.

THREE THINGS IT REFUSES TO GUESS, all of them the absence contract (`#187`) applied to a record
rather than to a candidate:

  * THE STALENESS VERDICT IS NOT REIMPLEMENTED HERE. It comes from
    `pick_synthesis.stamp_is_current`, which exists precisely so a restored record can ask the
    question a live snapshot asks. A second copy of a staleness rule that is meant to agree with the
    first is the drift class this app keeps finding.
  * A RECORD CAN BE UNABLE TO ANSWER. `evidence_schema_version` 1 and 2 carry only two of the
    stamp's four fields, so those records cannot be asked whether the pool scope or the player
    universe moved. `stamp_is_current` correctly skips a comparison it has no live counterpart for,
    which means silence — and silence here would read as "nothing changed". Every summary therefore
    carries `unanswerable`: the questions this record's schema cannot be put to, named.
  * AN UNREADABLE RECORD IS COUNTED, NOT DROPPED. `list_snapshot_records` skips a file that will not
    parse, which is right (a damaged history file must not take down a live draft) and invisible
    (the caller sees a shorter list, not a problem). `unreadable_count` is that difference, from
    `snapshot_ids` against the records that actually loaded.

A WITHHELD QUANTITY STAYS WITHHELD when it comes back off disk. `presentable_text` is keyed on
TODAY's withheld set, not the set in force when the record was written, which is the correct
direction: a figure withdrawn from presentation since must not reappear because it is old.
"""
from __future__ import annotations

from typing import Optional

import draft_history
import pick_synthesis


#: Shown with every stored board, unconditionally — not only when it is stale. The product question
#: 1.7 left open was whether a replayed board may look live; this is the answer, in one string.
STORED_BOARD_NOTICE = (
    "A STORED BOARD. This is what was on the screen when it was recorded, not advice for now — "
    "no debate is replayed and no figure here has been recomputed."
)

#: The absence contract's own mark, the same one the Draft Room's cards use. Never for a WITHHELD
#: figure: `presentable_text` has its own text for that, and collapsing the two is `#187`.
ABSENT = "—"

#: Stamp field -> the question it lets a reader ask. Named so a record that lacks the field can say
#: which question it cannot be put to, rather than answering it by omission.
STAMP_QUESTIONS = {
    "picks_consumed": "whether picks have been made since",
    "data_freshest_date": "whether the data has moved since",
    "pool_scope": "whether the candidate population was the same",
    "players_db_stamp": "whether the player universe was the same",
}


def _evidence(record: dict) -> dict:
    return (record or {}).get("evidence") or {}


def record_summary(
    record: dict, picks: list[dict], merger,
    *, live_pool_scope: Optional[str] = None, live_players_db_stamp: Optional[str] = None,
) -> dict:
    """One stored board as a row a reader can scan: what it was, and whether it still holds.

    `current` and `reason` are `stamp_is_current`'s own answer, unchanged. `unanswerable` names the
    stamp questions this record's schema cannot be put to — empty for a schema-3 record, two entries
    long for the schema-1 records written before the stamp was completed."""
    evidence = _evidence(record)
    unanswerable = [question for field, question in STAMP_QUESTIONS.items()
                    if evidence.get(field) is None]
    current, reason = pick_synthesis.stamp_is_current(
        evidence.get("picks_consumed"), evidence.get("data_freshest_date"), picks, merger,
        pool_scope=evidence.get("pool_scope"), live_pool_scope=live_pool_scope,
        players_db_stamp=evidence.get("players_db_stamp"),
        live_players_db_stamp=live_players_db_stamp,
    )
    return {
        "snapshot_id": record.get("snapshot_id") or evidence.get("snapshot_id"),
        "pick_label": evidence.get("pick_label"),
        "round": evidence.get("round"),
        "decision_regime": evidence.get("decision_regime"),
        "date": record.get("date"),
        "candidate_count": evidence.get("candidate_count"),
        "schema_version": evidence.get("evidence_schema_version"),
        "user_selected_player_id": evidence.get("user_selected_player_id"),
        "current": bool(current),
        "reason": reason,
        "unanswerable": unanswerable,
        # MANDATE 2.2. Three states preserved verbatim (`#187`): `None` for a record written before
        # schema 5, when nothing asked; `[]` for a record whose config was checked and clean; a
        # populated list for one priced on a config that did not parse. A reader that rendered
        # `None` and `[]` the same way would tell someone a board was fine when nobody had looked.
        "config_ambiguities": evidence.get("config_ambiguities"),
    }


def league_history(
    league_id: str, picks: list[dict], merger,
    *, live_pool_scope: Optional[str] = None, live_players_db_stamp: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict:
    """Every stored board for this league, newest first, plus how many would not parse.

    `unreadable_count` is the honest half: `list_snapshot_records` drops a damaged file silently, so
    without this a corrupted history is indistinguishable from a shorter one."""
    # READ ONCE. The unreadable count needs every identity that loaded, and `limit` is a display
    # concern -- reading the directory twice to serve both would let the two answers disagree about
    # a file written between them.
    records = draft_history.list_snapshot_records(league_id)
    identities = draft_history.snapshot_ids(league_id)
    loaded = {r.get("snapshot_id") for r in records}
    shown = records if limit is None else records[:limit]
    return {
        "rows": [record_summary(r, picks, merger, live_pool_scope=live_pool_scope,
                               live_players_db_stamp=live_players_db_stamp) for r in shown],
        "stored_count": len(identities),
        "unreadable_count": len([i for i in identities if i not in loaded]),
    }


def _rendered(value, digits: int) -> str:
    if value is None:
        return ABSENT
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


#: (stored field, column heading, digits). The columns that explain a placement, which is what
#: `candidate_evidence` stores — not every field it stores, because a table nobody can read is not a
#: reader. Everything omitted here is still in the record and still loadable.
CANDIDATE_COLUMNS = (
    ("name", "Player", None),
    ("position", "Pos", None),
    ("team", "Team", None),
    ("team_acquisition_value", "Acquisition value", 2),
    ("universal_value", "Universal value", 2),
    ("need_bonus", "Need", 2),
    ("pick_necessity", "Necessity", 1),
    ("necessity_label", "", None),
    ("survival_probability", "Survival", 3),
    ("positional_forfeit", "Forfeit", 2),
    ("rival_premium", "Rival premium", 2),
    ("confidence", "Confidence", None),
    #: MANDATE 2.5, schema 4. Shown because the stored price already carries its discount: a record
    #: with a health-adjusted universal_value and no designation beside it cannot be read back.
    ("injury_status", "Injury", None),
)


def stored_candidate_rows(record: dict) -> list[dict]:
    """One stored board's candidates as display rows, in the order they were recorded.

    Every numeric column goes through `presentable_text`, so a quantity withheld from presentation
    TODAY is withheld here too — and an absent one keeps the absence mark rather than becoming a
    zero. Order is the record's own: it is what was on the screen, and re-sorting it would make this
    a new board rather than a stored one."""
    rows = []
    for candidate in _evidence(record).get("candidates") or []:
        row = {}
        for field, heading, digits in CANDIDATE_COLUMNS:
            value = candidate.get(field)
            rendered = value if digits is None else _rendered(value, digits)
            if rendered is None:
                rendered = ABSENT
            row[heading or field] = pick_synthesis.presentable_text(field, str(rendered))
        rows.append(row)
    return rows
