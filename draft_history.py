"""Per-league, append-only, content-addressed record of what the Draft Room actually showed.

WHAT THIS IS FOR. A PickSnapshot is frozen but has always been ephemeral -- rebuilt every
rerun, never named, never stored. That made three things unbuildable: binding a record to the
exact board it came from, showing a historical result against the board it was generated on
rather than today's, and letting the Prytaneum see which snapshots exist at all. This module
is the substrate for all three (#92), and nothing more.

THE ARCHITECTURAL RULE, which is not negotiable and is enforced by a test:

    This store is OBSERVATIONAL HISTORY, never an engine input.

It records what was shown. It must never be read back into valuation, candidate selection or
scarcity. `test_cdme_ingestion_boundary.py` lists this module among those CDME may never
import, for the same reason bot_research.py is on that list: a persisted record flowing back
into the computation that produced it is a feedback loop, and a stored number acquires
authority it was never granted just by having been written down.

WHY FILE-PER-RECORD, KEYED BY CONTENT. §11.4b (#102) demonstrated a cross-session lost update
in every existing per-league store, and the mechanism is always the same: load the whole list,
append, write the whole list back. Two sessions interleave and one session's entry is gone.
This store cannot express that bug, because it never reads before it writes. One record is one
file, named by its own content hash:

  * two sessions storing DIFFERENT snapshots write different files -- both survive;
  * two sessions storing the SAME snapshot write the same bytes to the same name -- idempotent;
  * nothing is ever rewritten, so nothing can be overwritten.

Append-only is a property of the layout here, not a convention someone has to remember.

RETENTION (the operator's storage policy, recorded so the code and the policy cannot drift):
completed snapshot records belong to the draft/league history and are NOT cleared when a draft
concludes -- only transient session state and in-progress generation are, and neither of those
lives here, so this module has nothing to do at draft conclusion. Records leave only by
explicit user or league-lifecycle deletion (`forget_league`). Nothing regenerates a stored
record because player data, rankings, models or engine logic later changed: that is the entire
point of storing what was shown rather than how to recompute it.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import fields as dataclass_fields
from datetime import datetime
from pathlib import Path
from typing import Optional

HISTORY_DIR = Path("data/draft_history")

# Bumped only when the projection's SHAPE changes. A record written under an older shape stays
# readable and keeps its own number -- a reader can then tell "this field was never captured"
# from "this field was captured as absent", which §18/#112 named as the distinction the board
# currently cannot make. Never renumber an existing record.
EVIDENCE_SCHEMA_VERSION = 1

# The candidate fields retained per row. Chosen to answer "why is this one above that one" --
# the value layer, the two bonuses that separate universal from team-acquisition value, the
# scarcity and urgency terms, and the anchor provenance.
#
# bpa_source and confidence are here deliberately. §24/#119 measured that the board UI drops
# both, so a stored record built only from what the board shows would be unable to say what
# anchored a number or how much to trust it -- and an evidence projection that cannot answer
# that is not auditable. Storing them locally does NOT pre-empt #119: that item is about what
# the BOARD SURFACE ships to a client, which is a display and exfiltration question (§24.4)
# and stays open. This is a local file the user already owns.
#
# Raw `bpa`, `time_horizon_adj` and `risk_adj` are deliberately NOT here. They are the
# decomposition whose disclosure is exactly what #119 leaves undecided, and the projection is
# fully intelligible without them: bpa_source names the anchor, confidence grades it.
_CANDIDATE_EVIDENCE_FIELDS = (
    "player_id", "name", "position", "team",
    "universal_value", "need_bonus", "eligibility_bonus", "team_acquisition_value",
    "bpa_source", "confidence",
    "pick_necessity", "necessity_label",
    "survival_probability", "intervening_picks",
    "positional_forfeit", "rival_premium", "denial_team",
    "positional_cliff", "position_run_detected",
    "near_tie_with_leader", "cliff_protection", "block_opportunity", "pure_value",
    "context_elevated", "reach_label", "projected_points", "waiting_cost",
)

_SAFE_SCOPE = re.compile(r"[^A-Za-z0-9_.-]")


def _scope_dir(league_id: str) -> Path:
    """One league's directory. The league id becomes a path component, so it is sanitized
    rather than trusted: a league id is user-supplied via the Sleeper import, and a value
    containing a separator or `..` would otherwise write outside this store."""
    safe = _SAFE_SCOPE.sub("_", str(league_id or "").strip()) or "_unscoped"
    if set(safe) <= {"."}:                      # ".", ".." and friends collapse to a literal
        safe = "_" + safe
    return HISTORY_DIR / safe / "snapshots"


def _atomic_write(path: Path, payload: dict) -> None:
    """Write-if-absent, atomically. The temp file is created in the SAME directory so
    os.replace stays a rename within one filesystem, which is what makes it atomic: a reader
    at any instant sees either no file or a complete one, never a half-written record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True))
    os.replace(tmp, path)


def candidate_evidence(candidate) -> dict:
    """One candidate, projected to the fields that explain its placement.

    Absent stays absent: a None is stored as null, never coerced to 0.0 -- the absence contract
    this app applies everywhere else (see pick_synthesis.CandidateSnapshot.waiting_cost on why
    a zero would read as reassurance at exactly the positions whose data is thinnest).

    `getattr` is called WITHOUT a default on purpose. With one, renaming a field on
    CandidateSnapshot would quietly start writing null into every stored record and the history
    would keep looking well-formed while silently losing a column -- the exact
    silent-meaning-change class §17.5/#110 demonstrated, and the "one read short" pattern this
    audit found ten times. Here a rename raises immediately, and a test pins the field list
    against the dataclass so it fails at test time rather than mid-draft.
    """
    return {name: getattr(candidate, name) for name in _CANDIDATE_EVIDENCE_FIELDS}


def evidence_projection(snapshot, snapshot_id: str) -> dict:
    """The compact, immutable projection of one frozen board -- enough to make a historical
    result intelligible and auditable later, without retaining the player pool it was drawn
    from. Every value here is copied from the snapshot; nothing is recomputed, so this cannot
    disagree with the board it describes."""
    return {
        "evidence_schema_version": EVIDENCE_SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "pick_label": snapshot.pick_label,
        "round": snapshot.round,
        "my_roster_id": snapshot.my_roster_id,
        "decision_regime": snapshot.decision_regime,
        "user_selected_player_id": snapshot.user_selected_player_id,
        # The input-state stamp, carried verbatim. This is what lets a reader ask
        # snapshot_is_current of a RESTORED record, not just a live one.
        "picks_consumed": snapshot.picks_consumed,
        "data_freshest_date": snapshot.data_freshest_date,
        "candidate_count": len(snapshot.candidates),
        "candidates": [candidate_evidence(c) for c in snapshot.candidates],
    }


def record_snapshot(
    league_id: str, snapshot, snapshot_id: str, *, draft_id: Optional[str] = None,
) -> str:
    """Store one frozen board under its own content identity. Returns the snapshot_id.

    Idempotent by construction: storing the same snapshot twice writes the same bytes to the
    same path, so a rerun that rebuilds an identical board adds nothing and loses nothing. The
    caller passes snapshot_id rather than this module computing it, so that the identity a
    record is filed under is provably the same one the caller bound its own result to.
    """
    path = _scope_dir(league_id) / f"{snapshot_id}.json"
    if path.exists():
        return snapshot_id
    _atomic_write(path, {
        "snapshot_id": snapshot_id,
        "league_id": str(league_id or ""),
        "draft_id": draft_id,
        "ts": time.time(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "evidence": evidence_projection(snapshot, snapshot_id),
    })
    return snapshot_id


def load_snapshot_record(league_id: str, snapshot_id: str) -> Optional[dict]:
    """One stored record, or None. A record that will not parse returns None rather than
    raising: a damaged history file must not be able to take down a live draft."""
    path = _scope_dir(league_id) / f"{snapshot_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def list_snapshot_records(league_id: str, limit: Optional[int] = None) -> list[dict]:
    """This league's stored boards, newest first. This is what gives the Prytaneum explicit
    visibility of which Draft PickSnapshots exist -- a list of real records, not a claim that
    some exist."""
    directory = _scope_dir(league_id)
    if not directory.exists():
        return []
    records = []
    for path in directory.glob("*.json"):
        try:
            records.append(json.loads(path.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    records.sort(key=lambda r: r.get("ts", 0), reverse=True)
    return records[:limit] if limit is not None else records


def snapshot_ids(league_id: str) -> set[str]:
    """Just the identities present, without reading every record body."""
    directory = _scope_dir(league_id)
    if not directory.exists():
        return set()
    return {p.stem for p in directory.glob("*.json")}


def forget_league(league_id: str) -> int:
    """Delete this league's stored draft history entirely, returning how many records went.

    The ONLY removal path, by policy: history is not cleared at draft conclusion and does not
    expire on its own. It leaves when the user or the league lifecycle explicitly says so.
    """
    directory = _scope_dir(league_id)
    if not directory.exists():
        return 0
    removed = 0
    for path in directory.glob("*.json"):
        try:
            path.unlink()
            removed += 1
        except OSError:
            continue
    return removed
