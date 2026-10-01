"""#216 B4 -- board rank is not pick order: three ordinals, three names.

Three different "position of a thing in a list" quantities move through this engine. They are all
small positive integers, they all print identically, and NOTHING IN THE TYPE SYSTEM STOPS ONE
BEING PASSED WHERE ANOTHER IS EXPECTED. `#70` already found and repaired eleven sites where they
crossed. This module exists so the distinction has a home instead of living in eleven docstrings.

    VALUATION_RANK   "the consensus best player still available, on ONE team's board"
    DRAFT_POSITION   "which pick of the draft this is"
    VENDOR_RANK      "where an outside source placed this player in its own list"

WHY THESE THREE AND NOT MORE. They are separated by what CHANGES them, which is the only
distinction that matters to a consumer:

  * VALUATION_RANK changes when the POOL changes -- a player comes off the board and everyone
    below moves up. It is recomputed per team, because each team's board is its own valuation.
  * DRAFT_POSITION changes when the CLOCK changes. It is a fact about the draft's schedule, and
    it is identical for every team.
  * VENDOR_RANK changes when the VENDOR republishes. It is an input, not a derivation, and it
    survives unchanged across every pick of a draft.

A quantity that would be a fourth entry -- a display row number in a filtered view -- is
deliberately ABSENT, and its absence is the rule: a filtered view must not renumber (DRAFT_ROOM_UI
§12). If filtering WR-only produced rows 1, 2, 3, that would be a fourth ordinal wearing
VALUATION_RANK's clothes, and the filter would silently become a re-recommendation.

NOT A TYPE SYSTEM, AND NOT PRETENDING TO BE. Python will still let any int go anywhere. What this
buys is a checkable statement of each one's DOMAIN, so a producer that starts emitting the wrong
shape fails a test instead of being read as the wrong quantity (test_ordinal_registers.py).
"""
from __future__ import annotations

from typing import Optional

#: The three registers. `origin` names what recomputes the value, which is the discriminator.
ORDINALS: dict[str, dict] = {
    "VALUATION_RANK": {
        "means": "the consensus best player still available, on ONE team's board",
        "origin": "the pool -- recomputed per team, per pick",
        "one_based": True,
        "carriers": ("rank_by_id", "rank_on_their_board"),
        "consumers": ("RANK_TAKE_PROBABILITY", "positional_forfeits"),
    },
    "DRAFT_POSITION": {
        "means": "which pick of the draft this is",
        "origin": "the clock -- identical for every team",
        "one_based": True,
        "carriers": ("pick_no",),
        "consumers": ("generate_pick_order", "intervening_roster_ids"),
    },
    "VENDOR_RANK": {
        "means": "where an outside source placed this player in its own list",
        "origin": "the vendor -- an input, unchanged across a draft",
        "one_based": True,
        "carriers": ("consensus_rank", "ds_rank", "ds_fa_rank", "search_rank", "pos_rank"),
        "consumers": ("data_merger reconciliation",),
    },
}


def register_of(carrier: str) -> Optional[str]:
    """Which register a field name belongs to, or None when the name is not an ordinal this
    module claims. None is the honest answer for an unknown name -- guessing a register for it
    would be the exact substitution this module exists to prevent."""
    for name, spec in ORDINALS.items():
        if carrier in spec["carriers"]:
            return name
    return None


def carriers() -> dict[str, str]:
    """Every claimed field name mapped to its register. DERIVED from ORDINALS rather than
    written out a second time (#126): a hand-maintained inverse is a second source of truth that
    drifts the first time someone adds a carrier to only one of them."""
    out: dict[str, str] = {}
    for name, spec in ORDINALS.items():
        for c in spec["carriers"]:
            out[c] = name
    return out


def domain_violations(register: str, values) -> list:
    """Values that cannot belong to `register`, given what the register says about itself.

    Only ONE property is checked, and that is deliberate: every register here is one-based, so a
    0 or a negative is a category error in all three. Upper bounds are NOT checked, because each
    register's ceiling is a different runtime fact -- the priced pool, the draft length, the
    vendor's list -- and inventing a shared one would be the substitution this module rejects."""
    spec = ORDINALS[register]
    bad = []
    for v in values:
        if v is None:
            continue                      # absence is not a domain violation (the absence contract)
        if not isinstance(v, int) or isinstance(v, bool):
            bad.append(v)
        elif spec["one_based"] and v < 1:
            bad.append(v)
    return bad
