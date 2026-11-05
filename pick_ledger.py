"""`#315` / `#137`: who owns which future pick, lifted out of the hull so it can be READ
without Streamlit.

WHY THIS ONE, AND WHY IT WAS NEARLY MISSED. A documentation review reported pick ownership as
"the single dynasty fact the product most needs ... one already-written call away and UNCALLED",
citing `MAIN_PAGE.md`'s "This is the gap worth building, and it is cheap". That was false twice
over: `sleeper_client.get_traded_picks` is called from the snapshot builder, and `app.py` has
read the result through this very function, at three call sites, the whole time. Acting on the
report would have rebuilt something that existed.

The REAL defect was invisible to the instrument that should have caught it. `api_surface.py`
counts the calls the hull makes OUT to other modules; a function the hull DEFINES is hull, so a
census of reaches cannot see it. That is a stated limit of that census and not a bug in it -- but
it means "what would a non-Streamlit client have to reproduce?" is a larger question than "what
does `app.py` call?", by exactly the set of functions `app.py` declares. This is one of them, and
it is the one `#85`'s future-pick valuation waits on (`run_fixture_validation.py:6`).

WHAT THIS MODULE DOES NOT DO. It does not price a pick. `estimate_future_pick_value` is recorded
as "wired to nothing but its own test", and what a pick is WORTH is a separate ruling. This
answers only who holds it, which is the fact the ledger can state without arguing.
"""

from __future__ import annotations

def build_pick_ledger(snapshot: dict) -> dict[int, dict[str, list[dict]]]:
    """roster_id -> {"acquired": [...], "given_away": [...]}, built only from Sleeper's own
    traded_picks (the authoritative source for who owns what -- Draft Sharks' own pick imports
    can be unreliable, per direct report). Sleeper only lists a pick here once it's actually
    moved from its original roster; an untouched pick is assumed to still belong to its
    original roster and isn't worth listing, so this ledger is deliberately just the diffs,
    not a full inventory of every hypothetical future pick."""
    ledger: dict[int, dict[str, list[dict]]] = {}
    for pick in snapshot.get("traded_picks") or []:
        original, current = pick.get("roster_id"), pick.get("owner_id")
        if original is None or current is None or original == current:
            continue
        ledger.setdefault(current, {"acquired": [], "given_away": []})["acquired"].append(pick)
        ledger.setdefault(original, {"acquired": [], "given_away": []})["given_away"].append(pick)
    return ledger
