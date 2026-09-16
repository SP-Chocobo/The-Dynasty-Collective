"""
Strategic layer on top of draft_room.py's board: not just "who's the best player available"
but "should I take him now, or will he survive to my next pick, and what does an opponent
gain if I let him go." Same zero-LLM, deterministic philosophy as draft_room.py (see its own
module docstring) -- no LLM in this critical path.

CORE IDEA: universal_value (draft_room.py's own bpa-based score) answers "how good is this
player, full stop." It does NOT answer "how urgently do I need to take him THIS pick" -- that
depends on whether he'd still be there next time. This module estimates that survival
probability from data this app already has (draft order, every intervening team's own roster
and needs, recent pick history) and turns it into three real, separate numbers per candidate:

  survival_probability   -- P(still on the board when it's my turn again)
  opportunity_cost       -- universal_value * (1 - survival_probability): the expected value
                             LOST by not taking him now, if he doesn't survive
  denial_value           -- the best VALUE AN OPPONENT WOULD HAVE GOTTEN from him, weighted by
                             how likely that specific opponent actually was to take him -- what
                             the user's own pick prevents someone else from getting, not a
                             number this player's ranking already implies for the user

SURVIVAL MODEL: for each roster picking between now and the user's next turn, this looks at
THAT roster's own compute_draft_board (their own needs, their own board -- a player scarce for
one team isn't necessarily scarce for another). Where the target player ranks on THAT team's
board maps to a bounded, documented take-probability (RANK_TAKE_PROBABILITY) -- a rank-1 guy
is likely gone, a rank-15 guy on their board is not, regardless of how he ranks on the user's
own board. Multiplying (1 - p_take) across every intervening pick gives the compound survival
probability.

PERFORMANCE, and the real bug this shape fixes: an earlier version recomputed
compute_draft_board once per intervening PICK POSITION (not per unique team) AND once per
CANDIDATE separately, with each intervening step simulating a hypothetical removal to feed
the next -- confirmed live, this took 40+ seconds against a modest 212-player pool for a
worst-case 22-pick gap, unusable against any real pick clock. Every opponent board this
module needs is now computed exactly ONCE, off the actual current pool (no hypothetical
sequential removals), and shared across every candidate being analyzed and every later use of
that same roster's board. That's a deliberate precision-for-speed tradeoff: a team that picks
twice in the same intervening window is scored from the same snapshot board both times rather
than a resimulated one accounting for their own first pick -- acceptable given every number
here is already a labeled approximation, not an empirical one, and the alternative was too
slow to use at all.

None of RANK_TAKE_PROBABILITY, POSITIONAL_RUN_BOOST, or the run-detection thresholds are
empirically backtested against real draft behavior -- they are principled, bounded, clearly
labeled starting points, the same honesty this app applies to every other constant that isn't
a real number pulled from a real source (see draft_room.py's own constants for the identical
pattern). A rank-1 take-probability of 55%, not 95%, is a deliberate choice: real drafts have
real variance (reaches, unexpected runs, a team simply preferring someone else) that a
confident-sounding single number would misrepresent as certainty.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Optional

from data_merger import DataMerger
from draft_room import SLEEPER_BASIS_WEEKLY, compute_draft_board
from player_universe import player_position

# How likely a team is to take the player sitting at a given rank on THEIR OWN board (not the
# user's) -- bounded, deliberately not near-certain even at rank 1, since real drafts have
# real variance a single confident number would misrepresent. Never backtested; see module
# docstring.
RANK_TAKE_PROBABILITY = {1: 0.55, 2: 0.32, 3: 0.18, 4: 0.10, 5: 0.06}
RANK_TAKE_PROBABILITY_FLOOR = 0.02

# A real, observable signal from the picks list itself (not an invented one): if most of the
# last few picks concentrated on one position, that position is "running" -- teams tend to
# follow a run rather than let a whole position group evaporate around them. Boosts the
# take-probability for players at that position specifically while a run is active.
RUN_LOOKBACK = 4
RUN_THRESHOLD = 3
RUN_TAKE_PROBABILITY_BOOST = 1.6
RUN_TAKE_PROBABILITY_CAP = 0.90

# A genuine MARKET-CONVENTION PRIOR, not something this module's own VOR math derived: in a
# 12-team superflex dynasty startup, real drafting behavior consistently sees roughly 6 QBs
# gone by the end of round 1, another 3-4 by the end of round 2 (~9-10 cumulative), another
# ~4 through rounds 3-4 (~13-14 cumulative) -- a well-established structural pattern (SF
# demands two startable QBs per team or a roster is genuinely worse off, elite passers are a
# hard-capped scarce resource across all 32 NFL teams, and a real "take a cliff-edge QB3 just
# to deny a rival a good QB2" denial dynamic is common), not a superstition and not something
# this app should let its own first-pass VOR ranking talk it out of. This exists specifically
# because a pure board-EVIDENCE estimate can't be trusted to reproduce it on its own: the same
# per-league VOR ranking that can underrate elite QBs in universal_value (see draft_room.py's
# SUPER_FLEX_QB_SHARE) also underrates them on every INTERVENING TEAM's own board, understating
# how likely a rival is to take one. Convention establishes the prior; the board still gets to
# override it (see _pace_deficit_boost -- ahead-of-pace positions get no boost at all, and this
# is capped, never treated as certainty). Anchored on cumulative PICKS MADE, not a pick_index
# array position -- (0 picks, 0 QBs) to (12 picks, 6 QBs) to (24 picks, 9.5) to (48 picks,
# 13.5), linearly interpolated between anchors and held flat beyond the last one (there's no
# real documented convention past round 4 to extrapolate a slope from).
SUPERFLEX_QB_PACE_ANCHORS = [(0, 0.0), (12, 6.0), (24, 9.5), (48, 13.5)]
# How many upcoming picks a CURRENT pace deficit gets spread across -- roughly half a round in
# a 12-team league. A bounded, principled starting point (not empirically backtested, same
# honesty as every other unproven constant here): the deficit right now is real; how quickly the
# market corrects it is the part nobody's handed this app real numbers for.
PACE_CATCH_UP_WINDOW = 6.0


def generate_pick_order(round_1_order: list, total_rounds: int, draft_type: str = "snake") -> list:
    """The full roster_id sequence for every pick in the draft. Snake reverses the order on
    even rounds (standard fantasy draft convention); "linear" (auction-style leagues sometimes
    draft this way for supplemental rounds) repeats the same order every round.

    "3rr" is snake with 3rd Round Reversal, a real, live format feature (Sleeper exposes it as
    settings.reversal_round == 3 on the draft object): round 3 REPEATS round 2's reversed
    order instead of snaking back, compensating the back half of round 1 for never getting a
    turn-adjacent double pick, then normal alternation resumes from round 4. Rounds run
    F, R, R, F, R, F, R... -- reverse when round == 2, or round >= 3 and odd. This is a
    structural correctness issue, not a preference: pick order feeds intervening_roster_ids,
    which feeds survival/opportunity-cost/denial/necessity, and treating a 3RR draft as plain
    snake mis-sizes the round-2-to-3 waits worst of all -- a turn-slot team's wait there is 0
    intervening picks under snake but a full 11 (12-team) under 3RR, the single largest
    possible error in the whole survival model."""
    order: list = []
    for round_num in range(1, total_rounds + 1):
        if draft_type == "3rr":
            reverse = round_num == 2 or (round_num >= 3 and round_num % 2 == 1)
        else:
            reverse = draft_type == "snake" and round_num % 2 == 0
        order.extend(reversed(round_1_order) if reverse else round_1_order)
    return order


def find_next_pick_index(pick_order: list, roster_id, after_index: int) -> Optional[int]:
    """The next index in pick_order, after after_index, where this roster picks again --
    None if they have no more picks left in the draft (e.g. near the very end)."""
    target = str(roster_id)
    for i in range(after_index + 1, len(pick_order)):
        if str(pick_order[i]) == target:
            return i
    return None


def intervening_roster_ids(pick_order: list, current_index: int, my_next_index: Optional[int]) -> list:
    """Every roster_id picking strictly between the current pick and the user's own next pick
    -- empty if there's no next pick to wait for (my_next_index is None) or nothing between
    them (back-to-back picks, e.g. the turn of a snake round)."""
    if my_next_index is None or my_next_index <= current_index:
        return []
    return list(pick_order[current_index + 1: my_next_index])


def detect_positional_run(picks: list[dict], players_db: dict[str, dict]) -> Optional[str]:
    """The fantasy position of the last RUN_LOOKBACK picks, if at least RUN_THRESHOLD of them
    landed at the same one -- a real, observable signal straight from the picks already made,
    not a modeled guess. None if there's no real run happening (or too few picks yet to tell)."""
    recent = picks[-RUN_LOOKBACK:]
    if len(recent) < RUN_THRESHOLD:
        return None
    positions = [player_position(players_db.get(str(p.get("player_id")), {})) for p in recent]
    positions = [p for p in positions if p]
    if not positions:
        return None
    top_position, count = Counter(positions).most_common(1)[0]
    return top_position if count >= RUN_THRESHOLD else None


def _interpolate_pace(anchors: list[tuple[float, float]], picks_made: int) -> float:
    if picks_made <= anchors[0][0]:
        return anchors[0][1]
    if picks_made >= anchors[-1][0]:
        return anchors[-1][1]  # flat beyond the last anchor -- no documented convention to slope from
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
        if x0 <= picks_made <= x1:
            frac = (picks_made - x0) / (x1 - x0)
            return y0 + frac * (y1 - y0)
    return anchors[-1][1]


def expected_position_pace(position: str, picks_made: int, roster_positions: list[str]) -> Optional[float]:
    """The expected CUMULATIVE count of this position drafted leaguewide by picks_made, from a
    real, named market convention -- None when no such convention is documented for this
    position/format (the honest default: don't invent a pace curve for a case nobody's actually
    given real numbers for). Currently only QB in a SUPER_FLEX league -- see
    SUPERFLEX_QB_PACE_ANCHORS' own comment for the real domain reasoning behind it."""
    if position == "QB" and "SUPER_FLEX" in (roster_positions or []):
        return _interpolate_pace(SUPERFLEX_QB_PACE_ANCHORS, picks_made)
    return None


def _pace_based_take_probability(
    position: str, target_player_id: str, board: dict, picks_made_now: int,
    picks: list[dict], players_db: dict[str, dict], roster_positions: list[str],
) -> Optional[float]:
    """The probability THIS SPECIFIC intervening pick takes target_player_id, driven directly by
    the market-convention pace (SUPERFLEX_QB_PACE_ANCHORS) rather than this team's own VOR
    ranking -- built for exactly the case a rank-based estimate structurally cannot handle.
    Confirmed directly: an elite QB can rank outside RANK_TAKE_PROBABILITY's top-5 keys on
    EVERY intervening team's own board (the same per-league VOR math that can underrate him in
    universal_value does so on every opponent's board too), at which point the rank-based
    estimate floors out at RANK_TAKE_PROBABILITY_FLOOR (0.02) regardless of position -- and
    multiplying a near-zero floor by any bounded boost can never produce a meaningfully large
    probability (confirmed: even at a 2x cap, 0.02 -> 0.04, nowhere near enough to move survival
    across a real intervening gap). This function ignores that floor entirely and computes a
    probability straight from the convention instead.

    Two steps: (1) how far behind the documented convention this position is RIGHT NOW
    (expected_position_pace's own cumulative curve, minus how many have actually been drafted),
    spread over a fixed near-term catch-up window (PACE_CATCH_UP_WINDOW) -- gives the
    probability ANY upcoming pick goes to this position; (2) divide by target_player_id's own
    rank AMONG REMAINING PLAYERS AT THIS POSITION on this specific opponent's own board --
    narrows "some QB gets taken" down to "THIS QB gets taken." The consensus best remaining
    player at a position running far behind pace gets nearly the full step-1 probability; the
    5th-best remaining shares it roughly five ways. Treating the remaining pool as roughly
    equally likely (not modeling name-level preference beyond rank) is a real simplifying
    assumption, not a claim of precision -- same honesty as every other unproven constant here.

    Deliberately NOT "spread the deficit over the picks remaining until the next documented
    anchor" -- an earlier version of this function did exactly that, and it produced a real,
    confirmed bug: probability climbed smoothly toward 1.0 approaching an anchor, then DROPPED
    right as picks_made_now crossed into the next anchor's window, because the deficit
    recomputed against a suddenly wider remaining-picks denominator. A real hazard shouldn't
    reset downward the moment a deadline passes without being met -- if anything the reverse.
    Spreading against a small FIXED window instead keeps this continuous: expected_position_pace
    itself is a continuous (if kinked) curve, so the deficit against it never jumps, and neither
    does this.

    None whenever no convention is documented for this position/format, or once picks_made_now
    is past the last documented anchor (no real convention to extrapolate a rate from)."""
    expected_now = expected_position_pace(position, picks_made_now, roster_positions)
    if expected_now is None:
        return None
    if picks_made_now >= SUPERFLEX_QB_PACE_ANCHORS[-1][0]:
        return None
    actual_now = sum(
        1 for p in picks if player_position(players_db.get(str(p.get("player_id")), {})) == position
    )
    deficit_now = max(expected_now - actual_now, 0.0)
    any_pick_probability = min(deficit_now / PACE_CATCH_UP_WINDOW, 1.0)

    # Priced rows only, for the same reason rank_by_id is built that way (see
    # _build_opponent_boards): this rank is a VALUATION ordinal -- it narrows "some QB gets
    # taken" down to "THIS QB gets taken" by how good the board says he is. An unpriced row
    # carries NaN in universal_value, and every comparison against NaN is False, so including
    # one makes this sort NON-TOTAL: the resulting "rank" depends on the order the rows arrived
    # in. Demonstrated directly on a constructed board in test_survival_evidence -- the best
    # QB's returned probability moved from 1.0 to 0.111, a 9x swing, purely from reversing the
    # dict's insertion order. Latent rather than live on today's data (this prior returns None
    # past 48 picks and the real board's first unpriced row appears in round 15, so the two
    # never overlap), and closed here rather than left as a landmine behind that coincidence.
    unpriced_ids = board.get("unpriced_ids", ())
    position_rows = [r for r in board["by_id"].values()
                     if r["position"] == position and r["player_id"] not in unpriced_ids]
    position_rows.sort(key=lambda r: r["universal_value"], reverse=True)
    target_rank = next(
        (i + 1 for i, r in enumerate(position_rows) if r["player_id"] == str(target_player_id)), None,
    )
    if target_rank is None:
        return None  # unpriced, or not at this position -- no valuation ordinal, no estimate
    return any_pick_probability / target_rank


# positional_forfeits: how many of an opponent's top-N board ranks are consulted when
# estimating "will this opponent's next pick go to position P" -- matches
# RANK_TAKE_PROBABILITY's own depth (ranks past it carry only the floor probability, which
# would add noise, not signal, to a position-level estimate).
FORFEIT_OPPONENT_BOARD_DEPTH = 5


def _curve_at(curve: list[float], taken: float) -> float:
    """The value of a position's curve after `taken` players have gone, read at a FRACTIONAL
    index instead of a rounded one (#86).

    WHAT THIS REPLACES, AND WHY IT IS NOT A CALIBRATION. The previous form was
    `curve[min(round(expected_taken), len(curve) - 1)]`. `expected_taken` is continuous -- a sum
    of per-opponent probabilities -- so rounding quantised it to a whole player and two
    indistinguishable inputs named different players. Measured on Fourth and Forever's own board
    (evidence/forfeit_knife_edge/): at WR, `expected_taken` of 0.48 reported a forfeit of 0.00
    and 0.60 reported 9.44. Interpolating INTRODUCES NO CONSTANT -- it removes the arbitrary
    choice already present (why round-half-even, rather than floor or ceil?) -- so #56's bar is
    not engaged. A bound is not a threshold, and this is neither.

    THE DEFECT IT ACTUALLY FIXES IS AN ABSENCE-CONTRACT ONE, not an aesthetic one. Rounding down
    manufactured a forfeit of exactly 0.00 for a position the model expected to lose a fraction
    of a player. 0.00 in this engine reads as "measured, and the cost is nothing", so that is
    the `#187` defect class, reached by arithmetic rather than by a substituted default. It has
    a named downstream victim: `pick_debate` renders an exactly-zero forfeit as the STRONGEST
    EVIDENCE FOR WAITING, so the manufactured zero was handed to the debate as an affirmative
    claim.

    THREE CORRECTIONS TO THE EVIDENCE THIS DOCSTRING USED TO CITE (2026-09-16, after an
    independent review):

      * "4 of 44 measured observations" is ONE pre-draft board state read at 11 gap lengths,
        not 44 independent observations. Every nonzero `expected_taken` on it is 0.06n or 0.9n,
        so "4 of 44, all WR" is arithmetic (0.06n < 0.5 for n <= 8). The claim is true; its
        evidentiary weight was overstated.
      * "the true statement was about 4.5 points" is NOT the true statement. Interpolation reads
        the curve at the MEAN count, curve[E[N]]; the honest expectation is E[curve[N]], and on a
        non-linear curve those differ. Exact Poisson-binomial on the same fixture: 5.48 against
        the shipped 4.53, max divergence 3.55 across 44 rows, P(no WR taken) = 0.61. This is a
        better approximation than 0.00, not the truth. The exact expectation is equally
        constant-free and remains available if the approximation ever needs to go.
      * Interpolation is CHOSEN, not forced. Ceil would also remove every manufactured zero
        without adding a constant, and so would the exact expectation. What the contract forces
        is that a fractional expectation must not report a measured zero; which of the three
        satisfies that is a modelling choice, and this one was made for monotonicity and for
        not inventing a player who was not expected to go.

    Clamped to the curve's own ends: a position cannot lose more players than it has, and the
    last entry is the worst player actually priced there. No extrapolation past the data."""
    if not curve:
        return 0.0
    last = len(curve) - 1
    t = max(0.0, min(float(taken), float(last)))
    lo = int(math.floor(t))
    hi = min(lo + 1, last)
    return curve[lo] + (curve[hi] - curve[lo]) * (t - lo)


def positional_forfeits(
    position_curves: dict[str, list[float]], opponent_boards: dict, intervening: list,
) -> dict[str, dict]:
    """Per position: the expected POSITION-LEVEL cost of delaying that position entirely
    until the user's next pick -- {"expected_taken", "forfeit", "best_now"} -- the one
    question survival (per-player), positional_cliff (adjacent-gap-only), and
    opportunity_cost (per-player) each individually cannot answer: "if I take the other
    position now and come back to this one next turn, how much worse is the best player
    I'll realistically find there?" That two-position swap is a real, recurring decision
    (measured directly in the committed baseline: RB projections decay 2-3x faster than WR
    in every rank window past 12, so delaying RB genuinely costs more than delaying WR --
    the market's mid-round behavior across the collected real boards agrees), and it's a
    DIFFERENT number from any single player's survival.

    Two steps per position P, both from data this module already computes:
      1. expected_taken: for each intervening pick, the probability it goes to position P at
         all -- the sum of RANK_TAKE_PROBABILITY over the P-players in that opponent's own
         top FORFEIT_OPPONENT_BOARD_DEPTH board ranks (their board, their needs -- same
         principle as estimate_survival), capped at RUN_TAKE_PROBABILITY_CAP per pick;
         summed across every intervening pick.
      2. forfeit: walk position P's own remaining curve (universal_value, deliberately
         team-agnostic -- this measures the POSITION's market decay, not the user's fit)
         down by expected_taken players -- read at a FRACTIONAL index, see _curve_at -- and
         report best-now minus expected-best-at-next-turn.

    WHERE THIS NUMBER ACTUALLY GOES (corrected 2026-09-16 -- this paragraph used to say
    "deliberately NOT an input to pick_necessity", and that has been FALSE since `7655fb1`).

    It IS a pick_necessity input. `pick_analysis` emits it, `build_snapshot` carries it, and
    `compute_pick_necessity` reads `positional_forfeit` and folds `forfeit_component` into
    `raw_score` (weight 10 of a 100-point scale). From there it reaches `necessity_label`, the
    Draft Room display, and the debate prompt, where an exactly-zero forfeit is rendered as the
    STRONGEST EVIDENCE FOR WAITING. `quantity_readers.scan()` has been reporting this correctly
    the whole time -- verdict `decision`, `scoring_readers=['pick_synthesis.py']` -- while this
    docstring said the opposite. The original double-count concern is real and is handled where
    it belongs (necessity's denial component, `#M3`); it was never a reason this quantity did
    not reach necessity.

    WHAT REMAINS TRUE, and is the part that matters: it has NO SELECTION AUTHORITY. The pick is
    `_board_order`, which sorts on `(fills_required_slot, final_score, player_id)` only, and
    `final_score` is computed by `compute_draft_board` BEFORE forfeits exist. `#55` ruled
    necessity observable. So this changes what the app SAYS and what the LLM is told -- not
    which player the engine picks.

    Empty dict when there are no intervening picks (back-to-back turn, or no next pick at
    all) -- a forfeit of 0 everywhere is real information the caller can state, but per-pick
    probabilities against zero picks are not."""
    if not intervening:
        return {}
    results: dict[str, dict] = {}
    for position, curve in position_curves.items():
        if not curve:
            continue
        expected_taken = 0.0
        for roster_id in intervening:
            board = opponent_boards.get(str(roster_id))
            if not board:
                continue
            rank_by_id = board["rank_by_id"]
            by_id = board["by_id"]
            p_position = 0.0
            for player_id, rank in rank_by_id.items():
                if rank > FORFEIT_OPPONENT_BOARD_DEPTH:
                    continue
                row = by_id.get(player_id)
                if row is not None and row.get("position") == position:
                    p_position += RANK_TAKE_PROBABILITY.get(rank, 0.0)
            expected_taken += min(p_position, RUN_TAKE_PROBABILITY_CAP)
        results[position] = {
            "expected_taken": round(expected_taken, 2),
            "forfeit": round(curve[0] - _curve_at(curve, expected_taken), 2),
            "best_now": round(curve[0], 2),
        }
    return results


def _take_weight(rank: Optional[int], is_run_position: bool) -> float:
    """The RELATIVE weight of one board row, before normalisation. `rank=None` is an unpriced
    row, which carries the floor and no run boost -- the boost is a rank-relative notion and
    there is no rank to relate it to."""
    if rank is None:
        return RANK_TAKE_PROBABILITY_FLOOR
    w = RANK_TAKE_PROBABILITY.get(rank, RANK_TAKE_PROBABILITY_FLOOR)
    if is_run_position:
        w = min(w * RUN_TAKE_PROBABILITY_BOOST, RUN_TAKE_PROBABILITY_CAP)
    return w


def board_take_mass(board: dict, run_position: Optional[str] = None) -> dict:
    """The total take-weight of one opponent board, and where that weight sits (`#206`).

    WHY NORMALISATION IS REQUIRED, AND WHY IT IS NOT A CALIBRATION. `estimate_survival` asks,
    per intervening opponent, "what is the chance THIS team takes THIS player at their next
    pick?" A team makes exactly ONE pick, so across their board the events are MUTUALLY
    EXCLUSIVE and the probabilities must sum to <= 1.0. That needs no league data to state,
    which is why `#56` is not engaged: the constraint is arithmetic, not a tuned number.

    MEASURED BEFORE REPAIR (`evidence/take_mass/`): on Fourth and Forever's real captured
    universe the total was **23.49**, against a constraint of 1.0 -- the model said one opponent
    takes 23 players with one pick. `#244` reached the same defect from the other end. And 95%
    of it was the FLOOR, not the five named keys: named 1.21, tail 9.52, unpriced 12.76. So
    renormalising the five keys -- the obvious reading of "make them sum to 1" -- would have
    moved 1.21 to 1.00 and left 22.28 in place.

    THE RUN BOOST IS APPLIED TO THE WEIGHT, BEFORE NORMALISING, and that is forced rather than
    chosen: boosting an already-normalised probability would re-break the mass it was just made
    to respect. Applied here it REDISTRIBUTES mass toward the running position, which is what a
    run means -- rivals are likelier to take that position and correspondingly less likely to
    take anything else.

    THE UNPRICED SHARE IS REPORTED, not silently folded in (owner ruling 2026-09-16). Unpriced
    rows keep the floor weight rather than dropping to zero, because zeroing them would assert
    "unpriced means safe" and the real-draft measurement refutes that: 31 of 301 resolved picks
    took a player who was not on the picking team's priced board at all. Substituting a number
    for an absence is the `#187` breach this engine forbids everywhere else. But over half the
    mass then sits on rows the engine could not value, so a consumer is told how much."""
    priced = board.get("rank_by_id") or {}
    by_id = board.get("by_id") or {}
    unpriced_ids = board.get("unpriced_ids") or ()

    priced_weight = 0.0
    for player_id, rank in priced.items():
        row = by_id.get(player_id)
        is_run = bool(run_position and row is not None and row.get("position") == run_position)
        priced_weight += _take_weight(rank, is_run)
    unpriced_weight = len(unpriced_ids) * RANK_TAKE_PROBABILITY_FLOOR
    total = priced_weight + unpriced_weight
    return {
        "total_weight": total,
        "priced_weight": priced_weight,
        "unpriced_weight": unpriced_weight,
        "unpriced_share": (unpriced_weight / total) if total > 0 else None,
        "priced_rows": len(priced),
        "unpriced_rows": len(unpriced_ids),
    }


#: The take model's shape is a VALUE SHARE over the opponent's own board, not a lookup on the
#: candidate's ordinal. `#206` measured why: the rank table cannot express the difference
#: between an opponent scoring their top two 265.11 / 262.54 (a coin flip) and 265.11 / 199.00
#: (a lock), because both are "rank 1 and rank 2". Calibration showed the consequence -- across
#: the whole board-rank range the model moved 0.84 -> 0.96 while reality moved 0.09 -> 0.91.
#: Sign right everywhere, magnitude wrong everywhere.
#:
#: The opponent's own `final_score` already carries what the owner asked this to represent:
#: their roster's needs (measured -- an RB-loaded seat marks every RB down by 9.00 while a
#: WR-loaded seat marks WRs down by the same, on boards that are otherwise identical), and pool
#: depletion, since the board is rebuilt off the live pool. None of it reached survival before,
#: because `estimate_survival` read `rank_by_id` and discarded the valuations that produced it.


def board_contention_scale(board: dict, contention_size: int) -> Optional[float]:
    """The value distance at which two rows on THIS board are meaningfully different, derived
    from the board being read rather than imported from elsewhere.

    WHY THIS IS NOT `NEAR_TIE_BAND`, WHICH IS THE OBVIOUS THING TO REACH FOR. That constant is
    2.0, derived from adjacent `team_acquisition_value` gaps in the top 40 of ONE board, and
    `#160` already caught it being applied to populations it was never measured on -- its own
    comment records that working on them "was, until #160, luck this comment was claiming as
    design". An opponent's full board in `final_score` units is a FIFTH population. Importing
    2.0 here would repeat the documented mistake rather than learn from it.

    WHY A RUNTIME STATISTIC AND NOT A CONSTANT (`#56`, and the capture's LIMITS). Concentration
    differs by format, by round and by board -- a fresh superflex board and a round-14 board are
    not the same distribution. A single number could only be right for one of them, and picking
    the one that makes calibration look best against a single league is exactly what the LIMITS
    forbid. Derived per board, this introduces no constant at all.

    THE STATISTIC, CHOSEN A PRIORI AND THEN MEASURED -- never searched for. The scale is the
    dispersion among the players actually IN CONTENTION for the next pick, and "in contention"
    is one round's worth of picks: `contention_size`, the league's team count. That is a league
    fact, not a tuned number. Standard deviation over that set answers "how far apart are the
    players who could plausibly go next", which is precisely the question a concentration scale
    asks. It was fixed before any calibration was run against it, and `#206`'s harness measures
    it rather than tuning it -- if it calibrates badly, that is reported, not adjusted away.

    None -- not a substituted default -- when the board cannot support the statistic: fewer than
    two priced rows in contention leaves nothing to measure a spread over, and a zero spread
    (every contender identical) has no scale either. `#187`: absence is not zero."""
    priced = board.get("rank_by_id") or {}
    by_id = board.get("by_id") or {}
    if contention_size < 2:
        return None
    scores = []
    for player_id, rank in priced.items():
        if rank <= contention_size:
            row = by_id.get(player_id)
            if row is not None and not _is_absent(row.get("final_score")):
                scores.append(float(row["final_score"]))
    if len(scores) < 2:
        return None
    mean = sum(scores) / len(scores)
    var = sum((x - mean) ** 2 for x in scores) / (len(scores) - 1)
    scale = var ** 0.5
    return scale if scale > 0 else None


def _value_take_weight(score: Optional[float], leader: float, scale: float,
                       is_run_position: bool) -> float:
    """One priced row's UNNORMALISED take weight, from its value distance behind the leader.

    exp((score - leader) / scale): the leader weighs 1.0, a row one scale behind weighs 1/e, and
    rows inside a scale of each other are near-equals -- which is the owner's own statement of
    the case this exists to get right ("if there are 3 equally valued players going into a curve
    and you're in seat 11, then at worst all 3 should have a 1/3 chance"). Three rows inside one
    scale split the mass roughly evenly; a leader a long way clear takes nearly all of it. The
    rank table could express neither.

    The run boost multiplies the WEIGHT, before normalisation, for the reason
    `board_take_mass` already records: boosting an already-normalised probability would
    re-break the mass it was just made to respect."""
    if score is None:
        return RANK_TAKE_PROBABILITY_FLOOR
    w = math.exp((float(score) - leader) / scale)
    if is_run_position:
        w = w * RUN_TAKE_PROBABILITY_BOOST
    return w


def _board_take_mass_cached(board: dict, run_position: Optional[str]) -> dict:
    """`board_take_mass` memoised ON THE BOARD ITSELF, keyed by run position.

    The normaliser is a property of the whole board, so computing it per candidate would turn
    survival from a handful of dict lookups into a full pass over ~1,100 rows per opponent per
    candidate. `_build_opponent_boards` already builds each board exactly once per analysis and
    the same dict is passed to every `estimate_survival` call, so caching here is computed once
    per (board, run position) and dies with the analysis -- no module-level state to invalidate,
    and a fresh board is a fresh dict."""
    cache = board.setdefault("_take_mass_by_run", {})
    key = run_position or ""
    if key not in cache:
        cache[key] = board_take_mass(board, run_position)
    return cache[key]


def _take_probability(rank: Optional[int], is_run_position: bool,
                      total_weight: Optional[float] = None) -> float:
    """P(this opponent takes the row at `rank` with their single next pick).

    With `total_weight` this is a genuine probability from a distribution that sums to 1.0 over
    the board. Without it -- the pre-`#206` form, kept only so a caller that has no board still
    gets the raw shape -- it returns an unnormalised WEIGHT, which is what made the mass 23.49.
    Production passes the total; nothing should call this without one."""
    w = _take_weight(rank, is_run_position)
    if total_weight is None or total_weight <= 0:
        return w
    return w / total_weight


def _is_absent(value) -> bool:
    """The board's own absence convention: a row the engine could not price carries None or
    NaN, never 0.0 and never a substituted default (see draft_room's absence contract)."""
    return value is None or (isinstance(value, float) and math.isnan(value))


def _board_take_probability(board: dict, target_key: str, rank: Optional[int],
                            unpriced: bool, is_run: bool,
                            run_position: Optional[str]) -> tuple:
    """P(this opponent takes THIS row with their single next pick), and the board's unpriced
    mass share. Returns `(p_take, unpriced_share)`.

    THIS IS A SEAM, NOT A SWITCH, and the distinction is the whole reason it exists. There is
    exactly ONE take model in production and this is its only home (`#126`) -- the body below
    is what `estimate_survival` did inline before, moved without a behaviour change. What the
    seam buys is that an ALTERNATIVE model can be substituted for the duration of one
    measurement process, so a calibration arm scores the real `estimate_survival` against a
    different take model instead of re-implementing survival beside it. The engine-measurement
    rule is that both arms must run the same code and toggle one thing; without a seam the
    only toggle available was a hundred-line copy of this function, which is a second source
    of truth for what survival means.

    A substitution that OUTLIVES a measurement process is the defect this docstring exists to
    forbid. Nothing in production may patch it, and nothing may read a module flag to decide
    which model to be -- when a model wins, it REPLACES this body rather than joining it."""
    mass = _board_take_mass_cached(board, run_position)
    total_weight = mass["total_weight"]
    if unpriced:
        return _take_probability(None, False, total_weight), mass["unpriced_share"]
    return _take_probability(rank, is_run, total_weight), mass["unpriced_share"]


def _build_opponent_boards(
    merger: DataMerger, players_db: dict[str, dict], picks: list[dict], league: dict,
    roster_ids: list, *, mode: str = "auto", pool_scope: str = "all",
    sleeper_projections: Optional[dict[str, dict]] = None,
    sleeper_basis: str = SLEEPER_BASIS_WEEKLY,
) -> dict:
    """One compute_draft_board call per UNIQUE roster_id, off the actual current pool -- see
    module docstring's PERFORMANCE section for why this replaced per-pick-position,
    per-candidate recomputation. Shared by every caller in this module within one analysis
    pass, never recomputed twice for the same roster."""
    boards = {}
    for roster_id in set(str(r) for r in roster_ids):
        # #214/F2: PRICED THE SAME WAY MY OWN BOARD IS. A rival board built vendor-only while
        # the snapshot beside it is scoring-aware makes survival, denial and rival_premium
        # answers about a different set of prices than the universal_value they sit next to.
        board_list = compute_draft_board(
            merger, players_db, picks, my_roster_id=roster_id, league=league,
            mode=mode, pool_scope=pool_scope,
            sleeper_projections=sleeper_projections, sleeper_basis=sleeper_basis,
        )
        # rank_by_id is a VALUATION ordinal and is built over priced rows only. Both consumers
        # of it -- estimate_survival and expected_positional_forfeit -- read the number through
        # RANK_TAKE_PROBABILITY, whose keys mean "the consensus best player available", "the
        # second best", and so on. compute_draft_board sorts unpriced rows last in a stable,
        # deterministic tiebreak, which keeps the board readable but is not a valuation; a
        # position with no replacement level left to measure against produces nothing but
        # tiebreak ordinals. Numbering those rows too and handing the result to that table is
        # the same register error this codebase repaired at the identity and horizon
        # boundaries. They are declared separately instead, so a consumer that cannot value a
        # player has to say so rather than read a rank that means something else.
        priced = [r for r in board_list if not _is_absent(r.get("final_score"))]
        boards[roster_id] = {
            "by_id": {r["player_id"]: r for r in board_list},
            "rank_by_id": {r["player_id"]: i + 1 for i, r in enumerate(priced)},
            "unpriced_ids": {r["player_id"] for r in board_list
                             if _is_absent(r.get("final_score"))},
        }
    return boards


def estimate_survival(
    picks: list[dict],
    players_db: dict[str, dict],
    pick_order: list,
    current_index: int,
    my_roster_id,
    target_player_id: str,
    opponent_boards: dict,
    *,
    league: Optional[dict] = None,
) -> dict:
    """Survival probability for ONE specific player between now and the user's next pick, plus
    the per-team breakdown that produced it (never a single opaque number -- same transparency
    principle as every other score in this app). Takes already-computed opponent_boards (see
    _build_opponent_boards) rather than recomputing anything itself -- this function is now a
    cheap lookup + probability multiply, not a simulation.

    league, when given, enables the market-convention pace prior (see
    SUPERFLEX_QB_PACE_ANCHORS/_pace_based_take_probability): for each intervening pick, the
    ACTUAL take-probability used is whichever is higher, the normal per-team rank-based
    estimate or the pace-driven one -- never lower than the rank-based estimate alone (the
    prior only ever pushes probability up when the board evidence understates it, it can't push
    down against real evidence). This exists because the rank-based estimate alone cannot be
    trusted for a position running far behind a well-established real-world convention: it
    looks at each intervening team's OWN board ranking, which uses the same per-league VOR math
    that can underrate elite QBs in universal_value in the first place (see draft_room.py's
    SUPER_FLEX_QB_SHARE) -- confirmed directly, an elite QB can rank outside the rank-based
    table's top 5 on every single intervening team's own board, at which point that estimate
    floors out near zero regardless of how far behind pace the position actually is. Optional
    (defaults to the rank-based estimate alone, this function's behavior before this existed)
    since not every caller has a league dict to hand, and no convention is documented for most
    position/format combinations anyway. Applies uniformly to every QB candidate in a superflex
    league regardless of his own tier, a real simplification: the convention specifically
    describes the ELITE tier, and this module doesn't compute an explicit tier boundary to gate
    on -- a deep bench QB gets the same pace-driven consideration as a true elite one (though his
    own rank-among-QBs term in _pace_based_take_probability already dilutes this somewhat, since
    a low-ranked QB shares the pace probability across many peers). Worth fixing with a real
    tier detector later; not pretending it's already handled.

    Returns {"survival_probability", "survival_basis", "intervening_picks", "risk_by_team"}.

    THREE STATES, and they used to be two (owner's ruling, 2026-09-16). This docstring
    previously said an empty risk_by_team with survival_probability=1.0 meant "either no one
    picks before the user's next turn (back-to-back picks) or the user has no more picks left
    to wait for" -- two different facts sharing one number, which is the #187 breach. Now:

      None  + SURVIVAL_NO_NEXT_PICK         no further pick exists, so the question does not
                                            arise. NOT 1.0: a forced 1.0 made opportunity_cost
                                            render 0.00, "waiting costs you nothing", at the
                                            one moment waiting costs you the player forever.
      1.0   + SURVIVAL_NO_INTERVENING_PICKS back-to-back; survives by arithmetic, not estimate.
      p     + SURVIVAL_MEASURED             estimated against every intervening rival's board.

    `intervening_picks` is None in the first state for the same reason -- there is no gap to
    count. Consumers already guarded it as Optional; the producer was the only thing here
    manufacturing certainty."""
    my_next_index = find_next_pick_index(pick_order, my_roster_id, current_index)
    #: NO NEXT SELECTION IS NOT CERTAINTY. Owner's ruling, 2026-09-16: when there is physically
    #: no further pick, saying so is the valid answer -- not a probability. None, with a basis,
    #: exactly as every other unmeasurable quantity in this engine (#187).
    if my_next_index is None:
        return {"survival_probability": None,
                "survival_basis": SURVIVAL_NO_NEXT_PICK,
                "intervening_picks": None, "risk_by_team": [],
                "unevidenced_picks": 0, "unpriced_mass_share": None}
    intervening = intervening_roster_ids(pick_order, current_index, my_next_index)
    if not intervening:
        # A REAL 1.0, and the only one: this seat picks again with nobody in between, so every
        # candidate survives by arithmetic rather than by estimate.
        return {"survival_probability": 1.0,
                "survival_basis": SURVIVAL_NO_INTERVENING_PICKS,
                "intervening_picks": 0, "risk_by_team": [],
                "unevidenced_picks": 0, "unpriced_mass_share": None}

    run_position = detect_positional_run(picks, players_db)
    info = players_db.get(str(target_player_id))
    target_position = player_position(info) if info else None

    survival = 1.0
    risk_by_team: list[dict] = []
    #: How much of each consulted board's take-mass sits on rows the engine could not price.
    #: Reported rather than folded in silently -- see board_take_mass's docstring for why the
    #: floor is kept at all (owner ruling 2026-09-16).
    unpriced_shares: list = []
    for i, roster_id in enumerate(intervening):
        board = opponent_boards.get(str(roster_id))
        if not board:
            continue
        # Three cases, and they must stay distinct. (1) No entry at all: the player is not in
        # this team's usable-position pool, so they cannot take him and contribute no risk --
        # unchanged. (2) On their board but unpriced: they CAN take him, but the board holds no
        # valuation for him, so there is no ordinal to read and no evidence of elevated risk.
        # He gets the module's own floor -- which is exactly what he already received, via a
        # tiebreak ordinal falling past the table's five keys -- and the row is labelled so no
        # consumer can present the result as a measurement. (3) Priced: unchanged.
        #
        # What deliberately is NOT decided here: whether an unpriced-but-draftable player
        # should instead count as zero risk. That is a product question with no evidence in
        # this repository to settle it, and picking an answer would be inventing behaviour.
        # The floor keeps every number identical to what production already produced.
        target_key = str(target_player_id)
        rank = board["rank_by_id"].get(target_key)
        unpriced = target_key in board.get("unpriced_ids", ())
        if rank is None and not unpriced:
            continue  # not even in this team's usable-position pool -- no risk from them
        is_run = bool(run_position and target_position == run_position)
        # #206: NORMALISE OVER THE BOARD. A team makes one pick, so their take probabilities
        # are mutually exclusive and must sum to <= 1.0 across the board. Unnormalised they
        # summed to 23.49 on a real board. Computed once per (board, run position) and cached
        # on the board -- see _board_take_mass_cached for why that is safe here.
        p_seam, unpriced_share = _board_take_probability(
            board, target_key, rank, unpriced, is_run, run_position)
        unpriced_shares.append(unpriced_share)
        if unpriced:
            p_unpriced = p_seam
            survival *= (1 - p_unpriced)
            risk_by_team.append({
                "roster_id": roster_id, "rank_on_their_board": None,
                "take_probability": round(p_unpriced, 6), "run_boosted": is_run,
                "pace_driven": False, "evidenced": False,
            })
            continue
        rank_based_p_take = p_seam

        # i (this pick's position within THIS survival computation, not the real, current pick
        # count alone) is what makes hazard rise the deeper we go without a resolution: the
        # documented anchor deadline is the same real point in the draft regardless of how many
        # of these hypothetical intervening picks have already passed, so each one that doesn't
        # take him concentrates the SAME remaining deficit over fewer remaining picks --
        # mechanically the "he's survived further than expected, so the next pick is even more
        # likely to be the one" run-momentum effect, not a separately invented boost. actual_now
        # (how many of this position are REALLY drafted) still comes only from the real `picks`
        # list -- this module doesn't simulate what the OTHER intervening teams hypothetically
        # did before this one, same performance/precision tradeoff already documented for
        # _build_opponent_boards.
        pace_p_take = None
        if league is not None and target_position is not None:
            pace_p_take = _pace_based_take_probability(
                target_position, str(target_player_id), board, len(picks) + i, picks, players_db,
                league.get("roster_positions") or [],
            )
        pace_driven = pace_p_take is not None and pace_p_take > rank_based_p_take
        p_take = pace_p_take if pace_driven else rank_based_p_take

        survival *= (1 - p_take)
        risk_by_team.append({
            "roster_id": roster_id, "rank_on_their_board": rank,
            "take_probability": round(p_take, 3), "run_boosted": is_run,
            "pace_driven": pace_driven, "evidenced": True,
        })

    measured_shares = [s for s in unpriced_shares if s is not None]
    return {
        "survival_probability": round(survival, 3),
        "survival_basis": SURVIVAL_MEASURED,
        "intervening_picks": len(intervening),
        "risk_by_team": risk_by_team,
        "unevidenced_picks": sum(1 for r in risk_by_team if not r["evidenced"]),
        # #206 disclosure: how much of the take-mass this answer rests on sat on rows the
        # engine could not price. None when no board was consulted -- absent, not zero.
        "unpriced_mass_share": (round(sum(measured_shares) / len(measured_shares), 4)
                                if measured_shares else None),
    }


def _position_curves(my_board: dict) -> dict[str, list[float]]:
    """Each position's remaining team-agnostic value curve, highest first.

    UNPRICED ROWS ARE EXCLUDED, and that is the whole point of factoring this out. A curve is a
    list of values; a row the board could not price has no value, and appending None then
    sorting is not a wrong number, it is a TypeError. Measured on a real 12-team dynasty
    startup: unpriced rows appear at round 15, and from that round on this sort raised

        TypeError: '<' not supported between instances of 'NoneType' and 'NoneType'

    all the way up through pick_analysis into pick_synthesis.build_snapshot -- the call the
    Draft Room makes to build the Prytaneum's pick debate -- the last quarter of every
    20-round draft.

    A position with nothing priced left gets no key at all rather than an empty list, which is
    the same absence-not-zero rule the board itself follows: positional_forfeits already skips
    a position it has no curve for."""
    curves: dict[str, list[float]] = {}
    for row in my_board.values():
        position = row.get("position")
        value = row.get("universal_value")
        if not position or value is None:
            continue
        curves.setdefault(position, []).append(value)
    for curve in curves.values():
        curve.sort(reverse=True)
    return {position: curve for position, curve in curves.items() if curve}


def _opportunity_cost(team_acquisition_value: Optional[float],
                      survival_probability: Optional[float]) -> Optional[float]:
    """value x (1 - survival): what waiting costs if he does not last until the next pick.

    None when either operand is absent. With no acquisition value there is no loss to state,
    and 0.0 would claim there is none -- the same rule expected_value_of_waiting already
    applies to its own absent survival."""
    if team_acquisition_value is None or survival_probability is None:
        return None
    return round(team_acquisition_value * (1 - survival_probability), 2)


def _opportunity_cost_order(row: dict) -> tuple:
    """Sort key: highest opportunity_cost first, rows with no cost last, player_id as the
    tiebreak. Mirrors pick_synthesis._board_order exactly -- absence is ordered, never compared
    as a number, and the result does not depend on the order the rows arrived in."""
    cost = row.get("opportunity_cost")
    return (cost is None, -cost if cost is not None else 0.0, str(row.get("player_id")))


#: WHY survival_probability is what it is -- the vocabulary, with one home (#187/#126).
#:
#: `estimate_survival` returned 1.0 for TWO DIFFERENT FACTS, and its own docstring said so:
#: "either no one picks before the user's next turn (back-to-back picks) OR the user has no
#: more picks left to wait for". The first genuinely is 1.0. The second has NO ANSWER -- the
#: question "does he make it back to my next selection" does not arise when there is no next
#: selection -- and 1.0 is the most wrong value available for it, because every consumer reads
#: it as "certain to be there".
#:
#: The downstream reading INVERTS: opportunity_cost is team_acquisition_value * (1 - survival),
#: so a forced 1.0 renders 0.00 -- "waiting costs you nothing" -- at the one moment waiting
#: costs you the player permanently.
#:
#: NOT A RARE EDGE. Measured on the real Greatest Show on Paper 2 board: every team reaches it
#: at its own final pick (12 turns minimum), and a team that trades its late picks away reaches
#: it far earlier -- TAmedic27 stops picking at 308 of 360, so 52 picks of falsely-free waiting.
#: Traded picks are what make it common, which is why it surfaced when the owner asked whether
#: nonstandard orders and traded picks still compute the gap correctly.
SURVIVAL_NO_NEXT_PICK = "no_next_pick"
SURVIVAL_NO_INTERVENING_PICKS = "no_intervening_picks"
SURVIVAL_MEASURED = "measured"

#: token -> the words a person reads. Every return from estimate_survival carries one.
SURVIVAL_BASIS_LABELS = {
    SURVIVAL_NO_NEXT_PICK: ("you have no further pick in this draft, so there is no next "
                            "selection for him to survive to"),
    SURVIVAL_NO_INTERVENING_PICKS: "you pick again immediately -- nobody picks in between",
    SURVIVAL_MEASURED: "measured against every rival board that picks before your next turn",
}


#: WHY denial_value is what it is -- the vocabulary, with one home (#187). The UI used to
#: promise "a measured 0 means no rival was positioned to gain" for every zero it saw, which
#: was true of one of these three states and false of another.
DENIAL_NO_INTERVENING_RIVAL = "no_intervening_rival"
DENIAL_NO_RIVAL_PRICED = "no_rival_priced"
DENIAL_MEASURED = "measured"

#: token -> the words a person reads. Absence of the BASIS itself is not a key: every candidate
#: that reaches pick_analysis gets one of the three.
DENIAL_BASIS_LABELS = {
    DENIAL_NO_INTERVENING_RIVAL: "no rival had a pick before your next turn",
    DENIAL_NO_RIVAL_PRICED: "no rival's board could price him, so nothing was measured",
    DENIAL_MEASURED: "measured against every rival board that could price him",
}


def pick_analysis(
    merger: DataMerger,
    players_db: dict[str, dict],
    picks: list[dict],
    pick_order: list,
    current_index: int,
    my_roster_id,
    league: dict,
    candidate_player_ids: list[str],
    *,
    mode: str = "auto",
    pool_scope: str = "all",
    sleeper_projections: Optional[dict[str, dict]] = None,
    sleeper_basis: str = SLEEPER_BASIS_WEEKLY,
) -> list[dict]:
    """The actual "should I take him now" answer for a shortlist of candidates (typically the
    top few from draft_room.compute_draft_board) -- team_acquisition_value plus the three
    strategic numbers from this module's docstring: survival_probability, opportunity_cost
    (expected value lost if he doesn't survive to the user's next pick), and denial_value (the
    best value an intervening opponent would get from him, weighted by how likely they
    actually were to take him -- what THIS pick prevents someone else from getting). Sorted by
    opportunity_cost descending: the highest number is the one where waiting costs the most,
    which is the actual "why take him now" case, not just "who's ranked highest."

    Deliberately anchored on team_acquisition_value (my_row["final_score"]), not universal_
    value: "what do I lose by waiting" is inherently a team-specific question (my roster's own
    fit matters, same reason denial_value below is likewise weighed against each OPPONENT's own
    team_acquisition_value, not a team-agnostic number) -- see draft_room.py's module docstring
    for why the two are kept as separate numbers in the first place. Earlier versions of this
    dict actually labeled this field "universal_value" while holding this exact team-specific
    number -- a real naming bug, not a semantic one (the math itself was always right), but one
    that would have propagated straight into pick_synthesis.py's audit-trail snapshot and
    misrepresented team_acquisition_value as universal_value in the very place the user most
    needs the two kept honestly distinct. Fixed by naming the field for what it actually is;
    callers wanting the true team-agnostic universal_value should read it directly off
    draft_room.compute_draft_board's own board rows instead (see pick_synthesis.build_snapshot).

    Every opponent board needed is computed exactly once (see _build_opponent_boards) and
    shared across every candidate here, not recomputed per candidate -- see module docstring's
    PERFORMANCE section for the real slowdown this replaced."""
    # #214/F2: THE SAME PRICES THE CALLER'S OWN BOARD USED. build_snapshot computes a
    # scoring-aware board and then called this function, which rebuilt one vendor-only and
    # returned strategic numbers derived from it -- the snapshot then presented both as one
    # decomposition of a single candidate. Measured before the repair, 47 of 48 round-one
    # candidates carried a different team_acquisition_value inside this function than the one
    # displayed beside it, and 35 of 48 a different bpa_source.
    my_board = {r["player_id"]: r for r in compute_draft_board(
        merger, players_db, picks, my_roster_id=my_roster_id, league=league, mode=mode,
        pool_scope=pool_scope,
        sleeper_projections=sleeper_projections, sleeper_basis=sleeper_basis,
    )}
    my_next_index = find_next_pick_index(pick_order, my_roster_id, current_index)
    intervening = intervening_roster_ids(pick_order, current_index, my_next_index)
    opponent_boards = _build_opponent_boards(
        merger, players_db, picks, league, intervening, mode=mode, pool_scope=pool_scope,
        sleeper_projections=sleeper_projections, sleeper_basis=sleeper_basis,
    )

    # Position-level cost of delaying each position entirely (see positional_forfeits' own
    # docstring) -- built from the SAME opponent boards computed above, no extra board work.
    # Curves are the user's own board's remaining players per position, team-agnostic values.
    #
    # Skipped entirely in upside mode. This used to read `if "universal_value" in row`, which
    # had that effect only because upside boards did not carry the column at all; now that
    # compute_draft_board emits it in both modes, the identical line would have silently
    # SWITCHED forfeits ON in upside mode. That is a valuation decision, not a shape fix --
    # an upside curve is a coherent team-agnostic curve, and computing forfeits off it is
    # arguably more correct than the zero it yields today -- but it changes a live decision
    # signal, so the existing behavior is preserved here explicitly and left open rather than
    # changed as a side effect of a crash fix.
    position_curves = {} if mode == "upside" else _position_curves(my_board)
    forfeits = positional_forfeits(position_curves, opponent_boards, intervening)

    results = []
    for player_id in candidate_player_ids:
        my_row = my_board.get(str(player_id))
        if my_row is None:
            continue
        survival = estimate_survival(
            picks, players_db, pick_order, current_index, my_roster_id, player_id, opponent_boards,
            league=league,
        )
        team_acquisition_value = my_row["final_score"]
        opportunity_cost = _opportunity_cost(team_acquisition_value,
                                             survival["survival_probability"])

        denial_value = 0.0
        denial_team = None
        # #207: rival_premium starts ABSENT, not at zero. It is the same quantity-with-no-
        # evidence that denial_value was: if no intervening rival exists, or no rival board
        # could price him, nothing was measured -- and 0.0 asserts "no rival wants him more",
        # which is the strongest of the three readings off the weakest evidence. #187 repaired
        # denial_value and left its sibling in the SAME LOOP untouched. It matters more here
        # than there, because rival_premium FEEDS pick_necessity.
        rival_premium = None
        rival_premium_take_probability = None
        # #187. THREE different facts used to leave denial_value at exactly 0.0, and the UI
        # promised, verbatim, that "a measured 0 means no rival was positioned to gain".
        # Counted here, where the difference is knowable, instead of being reconstructed
        # downstream from a number that no longer carries it.
        rivals_considered = 0
        rivals_priced = 0
        for risk in survival["risk_by_team"]:
            rivals_considered += 1
            opp_board = opponent_boards.get(str(risk["roster_id"]), {})
            opp_row = opp_board.get("by_id", {}).get(str(player_id))
            if opp_row is None:
                continue
            # An opponent whose own board cannot price him gains no measurable value from
            # taking him, and there is no premium of his over a universal_value that does not
            # exist either. Skipping is the same exclusion rule the curve above follows; it is
            # not a claim that the player is worthless to them.
            if opp_row.get("final_score") is None or opp_row.get("universal_value") is None:
                continue
            rivals_priced += 1
            weighted = opp_row["final_score"] * risk["take_probability"]
            if weighted > denial_value:
                denial_value = weighted
                denial_team = risk["roster_id"]
            # rival_premium: how much MORE this player is worth to the best-positioned
            # intervening rival than his team-agnostic universal_value -- their own
            # roster-fit premium, with NO take-probability in it. Whatever team-specific terms
            # compute_draft_board layers on, this subtraction picks up automatically, by
            # construction: since #139 that is three terms (need_bonus, eligibility_bonus,
            # depth_exposure) rather than two, which is correct here -- a rival's depth hole is
            # as real a reason for them to take this player as an empty starting slot is.
            #
            # ONE CONSEQUENCE, DOWNSTREAM, that this comment exists to make findable: the
            # necessity denial term normalizes this number by draft_room.NEED_BONUS_MAX, which
            # is the cap on ONE of those three terms. That divisor was never exceeded when the
            # gap had two terms (max 8.33). Measured 2026-09-03 with three: max 16.21, and
            # 21.9% of sampled candidates now clip at the divisor. See pick_synthesis's
            # denial_component and test_threshold_reachability. This exists as a
            # separate number specifically for pick_necessity's denial term: denial_value
            # above is (opponent value x p_take), and that same p_take already compounds
            # into survival_probability, so a necessity score using both counted the
            # identical underlying take-probability twice -- measured directly at r = +0.82
            # between the two components across simulated draft states, against this app's
            # own "don't double-count correlated scarcity signals" rule. Splitting the
            # magnitude (here) from the probability (survival) keeps each counted once.
            #
            # No mode guard: upside boards now carry universal_value too, and there it equals
            # final_score exactly (upside_score reads nothing off the roster), so this
            # subtraction is 0.0 for every player -- the true answer in that mode, not a
            # missing one. rival_premium stays 0.0 either way, so dropping the old
            # `if "universal_value" in opp_row` guard changes no behavior.
            premium = opp_row["final_score"] - opp_row["universal_value"]
            if rival_premium is None or premium > rival_premium:
                rival_premium = premium
                # THIS specific rival's own real take_probability -- kept alongside the
                # premium (not folded into it) so a downstream human-facing "denies a rival"
                # label can require a credible path (this rival actually being positioned to
                # take him), separately from premium magnitude. See
                # pick_synthesis.decision_path_flags' block_opportunity, the one consumer of
                # this field.
                rival_premium_take_probability = risk["take_probability"]

        # WHICH OF THE THREE (#187), and the absence made real where there was no measurement.
        #
        #   no_intervening_rival -- nobody had a pick between now and my next turn, so "no
        #       rival was positioned to gain" is TRUE and 0.0 is a measurement.
        #   measured             -- at least one opponent board priced him. 0.0 here means the
        #       best weighted value was <= 0, which is also a real finding: you cannot deny
        #       someone value they would not have got. The floor at 0.0 is deliberate and
        #       stays -- denial is a quantity of value KEPT FROM a rival, and a rival who
        #       values him negatively loses nothing when you take him.
        #   no_rival_priced      -- rivals existed and not one of their boards could price
        #       him. Nothing was measured, so there is no number, and 0.0 would assert the
        #       strongest of the three claims off the weakest evidence.
        if not rivals_considered:
            denial_basis = DENIAL_NO_INTERVENING_RIVAL
        elif not rivals_priced:
            denial_basis = DENIAL_NO_RIVAL_PRICED
            denial_value = None
        else:
            denial_basis = DENIAL_MEASURED

        results.append({
            "player_id": player_id,
            "name": my_row.get("name"),
            "position": my_row.get("position"),
            "team_acquisition_value": team_acquisition_value,
            "survival_probability": survival["survival_probability"],
            "survival_basis": survival["survival_basis"],
            "intervening_picks": survival["intervening_picks"],
            "opportunity_cost": opportunity_cost,
            "denial_value": (None if denial_value is None else round(denial_value, 2)),
            # The companion that says WHICH of the three produced that number, or its absence.
            # Read it before reading the value: 0.0 means "measured, nothing to keep from
            # anyone", never "not checked" (#187).
            "denial_basis": denial_basis,
            "denial_team": denial_team,
            "rival_premium": None if rival_premium is None else round(rival_premium, 2),
            # The companion, same vocabulary denial_basis uses -- a reader can tell "no rival
            # wanted him more" from "nobody was there to want him".
            "rival_premium_basis": denial_basis,
            "rival_premium_take_probability": rival_premium_take_probability,
            "positional_forfeit": (forfeits.get(my_row.get("position")) or {}).get("forfeit"),
            "position_expected_taken": (forfeits.get(my_row.get("position")) or {}).get("expected_taken"),
        })
    results.sort(key=_opportunity_cost_order)
    return results
