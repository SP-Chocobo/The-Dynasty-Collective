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

from collections import Counter
from typing import Optional

from data_merger import DataMerger
from draft_room import compute_draft_board
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

    position_rows = [r for r in board["by_id"].values() if r["position"] == position]
    position_rows.sort(key=lambda r: r["universal_value"], reverse=True)
    target_rank = next(
        (i + 1 for i, r in enumerate(position_rows) if r["player_id"] == str(target_player_id)), None,
    )
    if target_rank is None:
        return None
    return any_pick_probability / target_rank


def _take_probability(rank: int, is_run_position: bool) -> float:
    p = RANK_TAKE_PROBABILITY.get(rank, RANK_TAKE_PROBABILITY_FLOOR)
    if is_run_position:
        p = min(p * RUN_TAKE_PROBABILITY_BOOST, RUN_TAKE_PROBABILITY_CAP)
    return p


def _build_opponent_boards(
    merger: DataMerger, players_db: dict[str, dict], picks: list[dict], league: dict,
    roster_ids: list, *, mode: str = "auto", pool_scope: str = "all",
) -> dict:
    """One compute_draft_board call per UNIQUE roster_id, off the actual current pool -- see
    module docstring's PERFORMANCE section for why this replaced per-pick-position,
    per-candidate recomputation. Shared by every caller in this module within one analysis
    pass, never recomputed twice for the same roster."""
    boards = {}
    for roster_id in set(str(r) for r in roster_ids):
        board_list = compute_draft_board(
            merger, players_db, picks, my_roster_id=roster_id, league=league,
            mode=mode, pool_scope=pool_scope,
        )
        boards[roster_id] = {
            "by_id": {r["player_id"]: r for r in board_list},
            "rank_by_id": {r["player_id"]: i + 1 for i, r in enumerate(board_list)},
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

    Returns {"survival_probability", "intervening_picks", "risk_by_team": [...]}. An empty
    risk_by_team with survival_probability=1.0 means either no one picks before the user's
    next turn (back-to-back picks) or the user has no more picks left to wait for."""
    my_next_index = find_next_pick_index(pick_order, my_roster_id, current_index)
    intervening = intervening_roster_ids(pick_order, current_index, my_next_index)
    if not intervening:
        return {"survival_probability": 1.0, "intervening_picks": 0, "risk_by_team": []}

    run_position = detect_positional_run(picks, players_db)
    info = players_db.get(str(target_player_id))
    target_position = player_position(info) if info else None

    survival = 1.0
    risk_by_team: list[dict] = []
    for i, roster_id in enumerate(intervening):
        board = opponent_boards.get(str(roster_id))
        if not board:
            continue
        rank = board["rank_by_id"].get(str(target_player_id))
        if rank is None:
            continue  # not even in this team's usable-position pool -- no risk from them
        is_run = bool(run_position and target_position == run_position)
        rank_based_p_take = _take_probability(rank, is_run)

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
            "take_probability": round(p_take, 3), "run_boosted": is_run, "pace_driven": pace_driven,
        })

    return {
        "survival_probability": round(survival, 3),
        "intervening_picks": len(intervening),
        "risk_by_team": risk_by_team,
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
    my_board = {r["player_id"]: r for r in compute_draft_board(
        merger, players_db, picks, my_roster_id=my_roster_id, league=league, mode=mode, pool_scope=pool_scope,
    )}
    my_next_index = find_next_pick_index(pick_order, my_roster_id, current_index)
    intervening = intervening_roster_ids(pick_order, current_index, my_next_index)
    opponent_boards = _build_opponent_boards(
        merger, players_db, picks, league, intervening, mode=mode, pool_scope=pool_scope,
    )

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
        opportunity_cost = round(team_acquisition_value * (1 - survival["survival_probability"]), 2)

        denial_value = 0.0
        denial_team = None
        for risk in survival["risk_by_team"]:
            opp_board = opponent_boards.get(str(risk["roster_id"]), {})
            opp_row = opp_board.get("by_id", {}).get(str(player_id))
            if opp_row is None:
                continue
            weighted = opp_row["final_score"] * risk["take_probability"]
            if weighted > denial_value:
                denial_value = weighted
                denial_team = risk["roster_id"]

        results.append({
            "player_id": player_id,
            "name": my_row.get("name"),
            "position": my_row.get("position"),
            "team_acquisition_value": team_acquisition_value,
            "survival_probability": survival["survival_probability"],
            "intervening_picks": survival["intervening_picks"],
            "opportunity_cost": opportunity_cost,
            "denial_value": round(denial_value, 2),
            "denial_team": denial_team,
        })
    results.sort(key=lambda r: r["opportunity_cost"], reverse=True)
    return results
