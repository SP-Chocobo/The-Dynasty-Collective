"""Which Draft Room session values belong to ONE league, and what a league switch must drop.

#52 phase 7.4d / L-06. `activate_league` reset chat history, the league snapshot and the
merger, and left every `draft_room_*` key in place -- and nothing else in the app ever set
`draft_room_debate_result`, `draft_room_last_snapshot` or `draft_room_snapshot_cache` back to
None. Three keys with no reset path anywhere.

The scenario: league A at 2.03 with 14 picks, run the debate, switch to league B also at 2.03
with 14 picks. A's debate renders under B's board with no staleness note, and A's snapshot
feeds B's next diff. Nothing downstream catches it -- the Draft Room's result guard compares
`pick_label`, which cannot tell two boards at one label apart, and the staleness note compares
a pick COUNT and a data date, both of which two leagues routinely share.

WHY THIS IS ITS OWN MODULE. The function has to be exercised to be worth anything: a source
scan asserting `activate_league` clears these would pass on a clearing function that is never
called, and a reset nothing calls is the same defect with a nicer name. `app.py` is a
top-level Streamlit script that runs into session-dependent state on import, so nothing in a
test can call a function that lives inside it. This takes the state MAPPING as an argument and
imports nothing -- same dependency-free posture as content_hash.py, for the same reason.
"""

from __future__ import annotations

from typing import MutableMapping

#: Session keys the Draft Room and Mock Draft own. Everything under these prefixes is dropped
#: on a league switch except the allowlist below.
DRAFT_STATE_PREFIXES = ("draft_room_", "mock_draft")

#: The exceptions: display preferences, which describe how a person likes to LOOK at a board
#: rather than anything computed from one league's data. Nothing here holds a snapshot, a
#: debate, a pick list or a cached board, and that is the test for belonging on this list.
DRAFT_STATE_PREFERENCES = frozenset({
    # `draft_room_mode` is deliberately NOT here: it is a local variable in app.py, not a
    # session key, so listing it would exempt nothing and misdescribe what this sweep does.
    # The widget behind it is keyed `draft_room_mode_radio`, and that is the real key.
    "draft_room_mode_radio",
    "draft_room_pool_scope", "draft_room_pool_scope_control",
    "draft_room_position_view", "draft_room_position_view_open",
    "mock_draft_pool_scope", "mock_draft_pool_scope_control",
    "mock_draft_position_view", "mock_draft_position_view_open",
})


def league_derived_keys(state) -> list[str]:
    """The keys in `state` that hold something computed from the league being left.

    `list(state)` is INSURANCE, not a fix, and it is recorded as such because a mutation pass
    says so: replacing it with a bare `state` survives every test in this file. It survives
    honestly -- the comprehension is fully materialised before clear_league_derived deletes
    anything, so nothing mutates during iteration today. It is kept because the caller passes
    Streamlit's SessionStateProxy rather than a dict, and because the failure it guards against
    appears the moment someone fuses these two loops into one. An untested line claimed as
    tested is worth less than one whose limits are written down.
    """
    return [key for key in list(state)
            if key.startswith(DRAFT_STATE_PREFIXES) and key not in DRAFT_STATE_PREFERENCES]


def clear_league_derived(state: MutableMapping) -> list[str]:
    """Drop them, and return what was dropped so a caller can log or assert on it.

    FAIL-SAFE BY DEFAULT, and that is the whole design. A list of keys to DELETE is a second
    statement of what the Draft Room keeps, and it falls behind the first time a key is added
    -- which is precisely how three keys came to have no reset path at all. Clearing by prefix
    with a preference allowlist inverts the default: a key added tomorrow is cleared without
    anyone remembering this file. The cost of being wrong then runs the harmless way -- a
    person re-picks a filter, rather than league A's board being priced into league B's draft.

    Safe to call where activate_league calls it: all three of its call sites run before the
    Draft Room instantiates any of these widgets in script order, and two rerun immediately.
    Streamlit only objects to mutating a widget key AFTER its widget exists in the same run.
    """
    dropped = league_derived_keys(state)
    for key in dropped:
        del state[key]
    return dropped
