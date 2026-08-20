"""
Rookie-draft-specific valuation: makes a traded pick's price team- and time-aware instead of
a single flat number everyone gets regardless of who actually owns it.

Draft Sharks' own Trade Value Chart already prices exact upcoming-draft slots (1.01-4.12+)
individually, and its rookie_pick_slot values already carry SOME class-strength signal (a
strong class's 1.01 prices higher than a weak class's, on the same 0-100 scale as a real
player -- see parse_draftsharks_trade_value_chart_pdf's own comment) -- that part isn't
missing. What IS missing, and what this module adds: a FUTURE pick (e.g. "2027 1st", a round
with no team assigned to a specific slot yet) currently prices at one flat, generic number
regardless of whose pick it actually is -- a last-place team's next 1st and a championship
team's next 1st get the identical value. There is no rookie/prospect database in this app at
all (Draft Sharks' Dynasty Rankings only cover players already on NFL rosters), so this
module does NOT attempt to model "how strong is next year's incoming class" or "what specific
players will be available at this slot" -- that would mean fabricating a number with no real
source behind it. It only uses data this app already has: a team's actual current record.

estimate_pick_slot maps a team's current win percentage onto an expected draft slot (worse
record -> earlier, more valuable slot -- standard reverse-standings rookie draft order),
then interpolates that fractional slot against Draft Sharks' own real per-slot pricing for
that round. The estimate is deliberately blended back toward the flat, generic future-pick
price as the target draft gets further away -- a team's CURRENT record says a lot about where
they'll likely finish THIS season, much less about two seasons from now -- via
FUTURE_YEAR_RECORD_DISCOUNT, a labeled, bounded approximation like every other non-empirically-
backtested constant in this app (see draft_room.py's own constants for the same pattern).
"""

from __future__ import annotations

from typing import Optional

from data_merger import DataMerger

# How much a team's CURRENT record should count toward estimating a FUTURE pick's slot, by
# how many seasons away that draft is. 1.0 = fully trust current record (this year's pick);
# further out, blend toward the flat generic future-pick price instead, since standings are
# much less predictive of a finish 2+ seasons away. Never backtested -- a principled,
# documented, bounded starting point, same honesty this app applies to every other constant
# that isn't a real number pulled from a real source.
FUTURE_YEAR_RECORD_DISCOUNT = {0: 1.0, 1: 0.6, 2: 0.3}
FUTURE_YEAR_RECORD_DISCOUNT_FLOOR = 0.15  # 3+ seasons out: mostly flat price, a little signal


def estimate_pick_slot(wins: int, losses: int, ties: int, num_teams: int) -> float:
    """Expected draft slot (1.0-num_teams, fractional) from a team's current record --
    reverse-standings order (worse record -> earlier, more valuable slot), the way a real
    rookie draft actually orders. No games played yet: no signal to use, so this returns the
    league-average middle slot rather than guessing either direction."""
    total_games = wins + losses + ties
    if total_games == 0:
        return (num_teams + 1) / 2
    win_pct = (wins + 0.5 * ties) / total_games
    return 1 + win_pct * (num_teams - 1)


def _interpolate_slot_value(merger: DataMerger, round_num: int, slot: float, num_teams: int) -> Optional[float]:
    """Draft Sharks prices exact slots (e.g. "1.03"), not fractional ones -- linearly
    interpolate between the two real, priced slots the estimated fractional slot falls
    between, rather than rounding to one and losing the rest of the estimate's precision."""
    lower = max(1, min(int(slot), num_teams))
    upper = min(lower + 1, num_teams)
    lower_value = merger.pick_value(f"{round_num}.{lower:02d}")
    upper_value = merger.pick_value(f"{round_num}.{upper:02d}")
    if lower_value is None:
        return upper_value
    if upper_value is None or upper == lower:
        return float(lower_value)
    frac = min(max(slot - lower, 0.0), 1.0)
    return lower_value + frac * (upper_value - lower_value)


def estimate_future_pick_value(
    merger: DataMerger, wins: int, losses: int, ties: int, num_teams: int,
    round_num: int, seasons_until_draft: int, generic_future_value: Optional[float] = None,
) -> Optional[dict]:
    """A specific team's future pick, priced from their CURRENT record rather than one flat
    number every future pick of that round/year gets. Blends the record-based estimate with
    the flat generic price (from Draft Sharks' own "20XX Random Rd N" future_pick row, when
    given) by FUTURE_YEAR_RECORD_DISCOUNT -- fully trusted for this year's pick, mostly
    discounted for a pick two-plus seasons out. Returns None only when Draft Sharks' rookie
    pick slot chart isn't loaded at all -- there's nothing to interpolate against.

    estimated_slot and value are both labeled outputs, never presented as more certain than
    they are: a record-based projection this far from an actual draft is a real approximation,
    not a precise price."""
    slot = estimate_pick_slot(wins, losses, ties, num_teams)
    record_value = _interpolate_slot_value(merger, round_num, slot, num_teams)
    if record_value is None:
        return None
    weight = FUTURE_YEAR_RECORD_DISCOUNT.get(seasons_until_draft, FUTURE_YEAR_RECORD_DISCOUNT_FLOOR)
    if generic_future_value is not None:
        blended = weight * record_value + (1 - weight) * generic_future_value
    else:
        blended = record_value
    return {
        "estimated_slot": round(slot, 2),
        "record_based_value": round(record_value, 1),
        "generic_value": generic_future_value,
        "record_weight": weight,
        "value": round(blended, 1),
    }
