"""
Real lineup optimization -- the actual fix for the Travis-Hunter-style gap: a player eligible
at multiple positions (WR/DB, TE/FLEX, whatever a league's own roster_positions and Sleeper's
fantasy_positions actually allow) isn't worth more just for HAVING multiple eligible
positions. He's worth more only when that eligibility lets a roster build a genuinely better
starting lineup than it could without him -- filling a scarce or high-scoring slot a
single-position player couldn't reach. This module computes that directly, as a real
assignment problem, rather than approximating it with a bonus multiplier keyed off "number of
eligible positions."

optimize_lineup solves the actual problem: given a roster of players (each with a value and
an eligible-position set) and a league's real starting slots (dedicated positions PLUS flex
slots expanded to whatever they accept -- see slots_from_roster_positions), find the
assignment of players to slots that maximizes total starting value. This is the classic
assignment problem (maximum-weight bipartite matching) -- solved exactly via
scipy.optimize.linear_sum_assignment, not a greedy heuristic. Greedy (assign each player to
their single best-value slot in descending order) is a well-known trap here: it can strand a
flexible player in a mediocre slot early and leave a genuinely better global assignment
undiscovered, especially exactly in the multi-eligible cases this module exists to get right.

marginal_lineup_value is the number draft_room.py actually needs: optimize_lineup(roster +
candidate) - optimize_lineup(roster) -- literally "best lineup with him minus best lineup
without him," the same formulation this app's design conversation asked for directly. Calling
it once with the candidate's FULL eligible-position set and once with ONLY his single primary
position (player_position()'s existing bucket) and taking the difference isolates the
eligibility bonus specifically -- see eligibility_bonus's own docstring. A single-position
player's bonus is exactly 0 by construction (both calls solve the identical problem), so this
never touches a player whose value the existing engine already gets right.
"""

from __future__ import annotations

from typing import Optional

from typing import Optional

import numpy as np
from scipy.optimize import linear_sum_assignment

from player_universe import FLEX_SLOT_POSITIONS, FANTASY_POSITIONS

# Effectively-infinite cost for an ineligible (player, slot) pairing in the assignment matrix
# -- large enough that the solver will only ever pick it when there is truly no valid
# alternative (more slots of a kind than eligible players, or vice versa), and even then the
# result is filtered back out afterward (see optimize_lineup) rather than trusted as a real
# assignment.
_INELIGIBLE_COST = 1e9


def slots_from_roster_positions(roster_positions: list[str]) -> list[dict]:
    """This league's real roster_positions, expanded into one dict per STARTING slot (bench/
    taxi/IR excluded -- they don't hold a lineup value, a benched player contributes nothing
    either way). Each slot carries its own eligible-position set, so a FLEX slot competes for
    RB/WR/TE and an IDP_FLEX for DL/LB/DB, exactly as the league itself defines them -- no
    generic assumption about what "FLEX" means baked in here beyond what player_universe.py's
    FLEX_SLOT_POSITIONS already documents for the rest of this app."""
    slots = []
    for i, raw in enumerate(roster_positions or []):
        if raw in FANTASY_POSITIONS:
            slots.append({"slot_id": f"{raw}_{i}", "label": raw, "eligible": {raw}})
        elif raw in FLEX_SLOT_POSITIONS:
            slots.append({"slot_id": f"{raw}_{i}", "label": raw, "eligible": set(FLEX_SLOT_POSITIONS[raw])})
        # BN/TAXI/IR/anything else: not a lineup slot, intentionally excluded.
    return slots


def optimize_lineup(players: list[dict], slots: list[dict]) -> dict:
    """Exact maximum-total-value assignment of players to starting slots.

    players: [{"id": ..., "value": float, "eligible": set[str]}, ...]
    slots: [{"slot_id": ..., "eligible": set[str]}, ...] (see slots_from_roster_positions)

    Returns {"total_value", "assignments": [{"slot_id","player_id","value"}], "benched": [id,...]}.
    Solved via scipy's Hungarian-algorithm implementation on a cost matrix (negated value,
    with an effectively-infinite cost for ineligible pairs) -- see module docstring for why a
    greedy assignment isn't trustworthy here. Any (player, slot) pair the solver was forced
    into despite ineligibility (only possible when there's a genuine surplus with no valid
    alternative on one side) is filtered back out rather than counted -- an unfillable slot
    stays empty and that player stays benched, never a fabricated invalid start.
    """
    if not players or not slots:
        return {"total_value": 0.0, "assignments": [], "benched": [p["id"] for p in players]}

    cost = np.full((len(players), len(slots)), _INELIGIBLE_COST)
    for i, player in enumerate(players):
        for j, slot in enumerate(slots):
            if player["eligible"] & slot["eligible"]:
                cost[i, j] = -player["value"]

    row_idx, col_idx = linear_sum_assignment(cost)

    assignments = []
    assigned_player_ids = set()
    for i, j in zip(row_idx, col_idx):
        if cost[i, j] >= _INELIGIBLE_COST:
            continue  # forced pairing with no real eligibility -- not a valid assignment
        assignments.append({
            "slot_id": slots[j]["slot_id"], "player_id": players[i]["id"], "value": players[i]["value"],
        })
        assigned_player_ids.add(players[i]["id"])

    total_value = sum(a["value"] for a in assignments)
    benched = [p["id"] for p in players if p["id"] not in assigned_player_ids]
    return {"total_value": round(total_value, 2), "assignments": assignments, "benched": benched}


def marginal_lineup_value(
    roster_players: list[dict], candidate: dict, roster_positions: list[str],
) -> dict:
    """The real "best lineup with him minus best lineup without him" number. candidate is
    {"id", "value", "eligible"} same shape as roster_players' entries. Returns
    {"with_candidate", "without_candidate", "marginal_value"} -- never just the delta alone,
    so a caller (or a human auditing a recommendation) can see both lineups' actual totals,
    not just trust a single subtracted number."""
    slots = slots_from_roster_positions(roster_positions)
    without = optimize_lineup(roster_players, slots)
    with_candidate = optimize_lineup(roster_players + [candidate], slots)
    return {
        "with_candidate": with_candidate["total_value"],
        "without_candidate": without["total_value"],
        "marginal_value": round(with_candidate["total_value"] - without["total_value"], 2),
    }


def eligibility_bonus(
    roster_players: list[dict], candidate_id, candidate_value: float,
    candidate_full_eligible: set[str], candidate_primary_position: Optional[str],
    roster_positions: list[str],
) -> dict:
    """The value created SPECIFICALLY by a candidate's multi-position eligibility -- the
    actual number this module exists to produce. Computes marginal_lineup_value twice: once
    with the candidate's full eligible-position set, once as if he could only play his single
    primary position (the bucket the rest of this app already uses) -- the difference is
    value his flexibility alone unlocks, isolated from his raw value (which both calls solve
    identically, so a single-position player's bonus is exactly 0.0, never a guess).

    Genuinely roster-dependent, not universal -- the same player's eligibility bonus differs
    by team, since it depends on what's already rostered and which slots are actually tight.
    That's why this lives alongside need_bonus in draft_room.py's team_acquisition_value, not
    folded into universal_value (see draft_room.py's own module docstring on that split).

    Naturally bounded IN ITS OWN CURRENCY: a candidate's marginal contribution can never
    exceed his own value (the best he can ever do is fill a genuinely empty slot outright),
    so no artificial cap is applied here the way NEED_BONUS_MAX exists for a heuristic
    overlay -- this is a real, self-limiting economic quantity, not a nudge. This function
    deliberately stays general-purpose and returns that value in whatever currency its caller
    supplied (draft_room.py passes trade_value; see _team_roster_players' own docstring for
    why). draft_room.py's own consumer rescales this raw number into universal_value's bpa
    scale and applies a SEPARATE bound (ELIGIBILITY_BONUS_MAX) before it ever reaches
    team_acquisition_value -- a real bug was found and fixed there (see draft_room.py's module
    docstring, "CORRECTION") after this function's own currency-neutral self-limit turned out
    not to be a bpa-scale bound at all. Nothing here needed to change to fix that; the fix
    belongs entirely at the point where the two different scales actually meet."""
    primary_only = {candidate_primary_position} if candidate_primary_position else set()
    if candidate_full_eligible <= primary_only:
        # Nothing beyond his one primary bucket -- the bonus is exactly 0 by construction
        # regardless of what the assignment problem says, so skip solving it twice (this is
        # the common case -- most players are single-position -- and draft_room.py calls this
        # once per candidate across a full live-draft board, so the redundant second solve
        # isn't free at that scale).
        only_result = marginal_lineup_value(roster_players, {"id": candidate_id, "value": candidate_value, "eligible": primary_only}, roster_positions)
        return {
            "eligibility_bonus": 0.0,
            "marginal_value_full_eligibility": only_result["marginal_value"],
            "marginal_value_primary_position_only": only_result["marginal_value"],
        }

    full_candidate = {"id": candidate_id, "value": candidate_value, "eligible": candidate_full_eligible}
    full_result = marginal_lineup_value(roster_players, full_candidate, roster_positions)

    primary_candidate = {"id": candidate_id, "value": candidate_value, "eligible": primary_only}
    primary_result = marginal_lineup_value(roster_players, primary_candidate, roster_positions)

    bonus = round(full_result["marginal_value"] - primary_result["marginal_value"], 2)
    return {
        "eligibility_bonus": bonus,
        "marginal_value_full_eligibility": full_result["marginal_value"],
        "marginal_value_primary_position_only": primary_result["marginal_value"],
    }


#: What `depth_exposure` reports when a position is in the league's slots but this roster has
#: nobody starting there. NOT zero exposure -- the opposite. A vacancy is a hole that already
#: exists, and reporting 0.0 would rank an empty slot as safely covered, which is the same
#: "absence read as a value" defect this codebase has already had to repair repeatedly.
EXPOSURE_VACANT = "vacant"

#: The position isn't in this league's starting slots at all (no TE slot in a TE-less format,
#: no IDP slots in an offense-only league). Nothing to be exposed to.
EXPOSURE_NOT_APPLICABLE = "not_applicable"

#: Every rostered player is starting -- there is no bench yet, so nothing can backfill a hole
#: and every loss costs that player's whole value. The arithmetic still runs and still returns
#: a number, and that number is NOT depth information: it is just each starter's own value
#: wearing a depth-shaped label. Measured directly -- a 7-player roster against 8 slots reports
#: QB 30 / RB 25 / WR 28 / TE 15, which is exactly the four players' values, and adding a TE2
#: moves nothing because the TE2 merely fills the empty eighth slot.
#:
#: Marked rather than suppressed, because the consumer that most needs this signal is the one
#: drafting in round 3 -- and a plausible-looking number it cannot distinguish from a measured
#: one is worse than an honest refusal. It is also the exact complement of the round-10
#: collapse in marginal_lineup_value: that quantity is informative while slots are empty and
#: degenerate once they fill, and this one is the reverse.
EXPOSURE_NO_SURPLUS = "no_surplus"


def depth_exposure(roster_players: list[dict], roster_positions: list[str]) -> dict[str, dict]:
    """Per position, what this roster loses if one of its starters there becomes unavailable.

    THE QUESTION THIS ANSWERS. Depth demand is not "a slot exists, so fill it." Nobody needs a
    fourth TE because their league has one TE slot. Depth is INSURANCE, and what it is worth
    is what a hole would actually cost -- which depends on who else is already rostered, and on
    whether anything else can cover the slot.

    Both of those fall out of the assignment solve rather than being encoded as rules:

      - SELF-LIMITING BY DEPTH. Remove TE1 from a roster that already has a competent TE2 and
        the lineup only drops by (TE1 - TE2), because the solver promotes TE2. So exposure at
        TE falls as soon as TE2 exists, and demand for a TE3 collapses on its own. No rule
        says "you don't need four tight ends"; the arithmetic says it.

      - SUBSTITUTABILITY IS FREE. Pull RB1 and the solver may slide a FLEX-eligible WR up, so
        the hole is cheap. Pull the only TE and a mandatory TE slot goes empty, so the hole is
        expensive. That asymmetry is the whole reason TE depth behaves differently from RB
        depth, and it is discovered here, not asserted.

    WHY IT CARRIES NO PROBABILITY. "Any one starter could become unavailable" is a uniform,
    stated assumption -- deliberately not a per-position injury rate, because this app does not
    have one. RISK_ADJ is a CURRENT-STATUS penalty (this player is Questionable today), not a
    prospective rate, and inventing "RBs get hurt 1.4x more than WRs" would be exactly the kind
    of unmeasured constant that has already had to be removed from this codebase once. A caller
    that acquires real base rates can weight these numbers; until then they are pure severity,
    and the docstring says so instead of the number implying otherwise.

    Returns {position: {"exposure", "worst_loss", "starters", "basis"}}:
      exposure    -- summed loss across every starter at that position: total value at risk.
      worst_loss  -- the single largest loss: what ONE backup would have to cover.
      starters    -- how many of this roster's starters sit at that position.
      basis       -- "measured", or EXPOSURE_NO_SURPLUS / EXPOSURE_VACANT /
                     EXPOSURE_NOT_APPLICABLE. Read it before reading the numbers: they are
                     returned in every state, and only "measured" makes them depth evidence.

    Both aggregates are returned rather than one, for the reason marginal_lineup_value returns
    both lineup totals: they answer genuinely different questions (total risk carried vs. what
    a single backup buys), and picking one here would make that choice invisible to the caller.
    """
    slots = slots_from_roster_positions(roster_positions)
    slot_positions = set().union(*(s["eligible"] for s in slots)) if slots else set()

    out: dict[str, dict] = {}
    for position in sorted(slot_positions):
        out[position] = {
            "exposure": None, "worst_loss": None, "starters": 0, "basis": EXPOSURE_VACANT,
        }
    for position in FANTASY_POSITIONS:
        if position not in slot_positions:
            out[position] = {
                "exposure": None, "worst_loss": None, "starters": 0,
                "basis": EXPOSURE_NOT_APPLICABLE,
            }

    if not roster_players or not slots:
        return out

    baseline = optimize_lineup(roster_players, slots)
    starting_ids = {a["player_id"] for a in baseline["assignments"]}
    by_id = {p["id"]: p for p in roster_players}
    # Depth cannot exist while every body is needed on the field. Compared against the players
    # who actually START, not len(roster_players), so a roster carrying someone ineligible for
    # every slot is not mistaken for having depth it cannot use.
    has_surplus = len(roster_players) > len(starting_ids)

    losses: dict[str, list[float]] = {}
    for player_id in starting_ids:
        player = by_id[player_id]
        # The player's OWN eligibility decides which position bears this exposure. A WR
        # starting in a FLEX slot is still WR depth: losing him is a WR-shaped hole, and the
        # roster covers it by rostering another WR (or another FLEX-eligible body), not by
        # rostering "a FLEX". Multi-eligible players count toward every position they can
        # actually fill, because a hole at any of them is a hole this player was covering.
        without = optimize_lineup([p for p in roster_players if p["id"] != player_id], slots)
        loss = round(baseline["total_value"] - without["total_value"], 2)
        for position in player["eligible"] & slot_positions:
            losses.setdefault(position, []).append(loss)

    for position, values in losses.items():
        out[position] = {
            "exposure": round(sum(values), 2),
            "worst_loss": round(max(values), 2),
            "starters": len(values),
            "basis": "measured" if has_surplus else EXPOSURE_NO_SURPLUS,
        }
    return out


#: What `bye_collision` reports for a week when some rostered players carry no known bye. The
#: solve still runs over the ones that do, but the answer is a FLOOR rather than the cost: a
#: player whose bye is unknown might also be out that week, and treating unknown as "available"
#: would understate every collision by exactly the players nobody could resolve.
BYE_PARTIAL = "partial"

#: No rostered player has a known bye week. Not "no collisions" -- nothing was measured.
BYE_UNKNOWN = "unknown"


def bye_collision(roster_players: list[dict], roster_positions: list[str]) -> dict[int, dict]:
    """Per bye week, what this roster's lineup is actually worth with everyone on that bye out.

    THE DIFFERENCE FROM depth_exposure, which is the reason this is not the same function.
    depth_exposure removes ONE starter and re-solves. A bye removes EVERY player on that team's
    bye at once, and simultaneous losses are not the sum of separate ones: the bench covers the
    first hole and then has nothing left for the second, so two collisions in one week can cost
    far more than twice one. That non-additivity is precisely what a headcount ("3 starters
    out") cannot express and an assignment solve gets for free.

    IT MEASURES VALUE LOST, NOT BODIES LOST, and that distinction is the whole point. A roster
    losing three starters it can fully cover from the bench loses nothing that week. A roster
    losing one irreplaceable starter loses a great deal. Counting heads would rank those two
    backwards.

    WHY THIS IS AN OBSERVABLE AND NOT A VALUATION TERM. Measured before building it, on the
    committed baseline: across 12 engine-drafted 8-starter rosters the worst week costs a
    median of 2 starters and a maximum of 3, against a chance baseline whose mean is 2.62 --
    the engine is not clustering byes, it simply is not avoiding them, and the two are the same
    number here. The top-value legal starting eight already sits at the pigeonhole floor, and
    no swap within 10 universal_value points improves it. So the reachable gain is roughly one
    starter in one KNOWN week of a season, which does not justify a fourth term competing for
    magnitude with three that measurably move picks (#56).

    The collision does grow with lineup depth -- simulated against the real 32-team spread, a
    12-starter shape averages 3.49 and a 20-starter IDP shape 5.12, where the pigeonhole floor
    is itself 3 -- so this is built to be read at any shape, and the decision not to score it
    is recorded with its measurement rather than as a silence.

    Returns {week: {"value_lost", "lineup_value", "players_out", "starters_out", "basis"}}:
      value_lost   -- baseline lineup value minus the value of the best lineup without them.
      lineup_value -- what the lineup is worth that week, so the loss has something to be a
                      fraction OF; a 12-point loss means different things at 200 and at 30.
      players_out  -- rostered players on that bye, starters and bench alike (the bench ones
                      are why the loss is often smaller than the headcount suggests).
      starters_out -- how many of them were in the baseline starting lineup.
      bench_used   -- how many bench bodies this week promotes into the lineup at once. This
                      is the quantity that makes stacking worse than its headcount: three
                      absences in one week consume three bodies, while the same three spread
                      across three weeks consume one each time and the bench refills in
                      between.
      bench_value_used -- their total value, since consuming your best body and your worst are
                      not the same depletion. No depth RANK is reported; FLEX substitution
                      chains leave that undefined (see the note in the body).
      basis        -- "measured", or BYE_PARTIAL / BYE_UNKNOWN. Read it first: a week's numbers
                      are a FLOOR under BYE_PARTIAL, not the cost.

    Reads each player's own "bye" (see DataMerger.bye_week_by_team, which derives it from team
    rather than per player). A player without one is kept in every lineup -- he is genuinely on
    the roster -- but his presence is what downgrades the basis, so the caller can tell a clean
    measurement from a floor.
    """
    slots = slots_from_roster_positions(roster_positions)
    if not roster_players or not slots:
        return {}

    unknown = [p for p in roster_players if p.get("bye") is None]
    weeks = sorted({int(p["bye"]) for p in roster_players if p.get("bye") is not None})
    if not weeks:
        return {}

    baseline = optimize_lineup(roster_players, slots)
    starting_ids = {a["player_id"] for a in baseline["assignments"]}
    # NO DEPTH RANK IS REPORTED, and the reason is worth keeping. Two were built and both were
    # wrong, because FLEX substitution makes "how far down the bench" ill-defined:
    #
    #   A WR goes out. The naive reading promotes the best bench WR. What the solver actually
    #   does -- verified on a real fixture -- is slide the WR already in FLEX up into the WR
    #   slot and drop a BENCH RB into the vacated FLEX. The hole at WR was covered by an RB,
    #   through a chain, and it cost 5 instead of the 16 the naive reading predicts.
    #
    # A per-position rank then calls that RB "depth 1 among RBs", which is the right number for
    # the wrong reason -- he is not covering an RB hole. A global rank calls him "depth 2"
    # whenever a better bench body was not used, implying waste the optimal solve did not
    # commit. Both are plausible numbers with no sound definition behind them.
    #
    # What survives contact is the COUNT of bodies consumed and their total value, neither of
    # which depends on routing. value_lost already carries the exact cost, chain included.
    bench_ids = {p["id"] for p in roster_players if p["id"] not in starting_ids}
    bench_value = {p["id"]: p.get("value", 0.0) for p in roster_players if p["id"] in bench_ids}

    out: dict[int, dict] = {}
    for week in weeks:
        out_this_week = [p for p in roster_players
                         if p.get("bye") is not None and int(p["bye"]) == week]
        available = [p for p in roster_players if p not in out_this_week]
        without = optimize_lineup(available, slots)
        promoted = [a["player_id"] for a in without["assignments"]
                    if a["player_id"] in bench_ids]
        out[week] = {
            "value_lost": round(baseline["total_value"] - without["total_value"], 2),
            "lineup_value": round(without["total_value"], 2),
            "players_out": len(out_this_week),
            "starters_out": sum(1 for p in out_this_week if p["id"] in starting_ids),
            # HOW MUCH BENCH THIS WEEK CONSUMES, which is the mechanism concentration proxies
            # for. Spread your byes and every week you field starters plus your first-up depth;
            # stack them and one week consumes two or three bodies at once. That is worse than
            # the same absences spread out, because bench value decays -- your best bench
            # player is nearly a starter and your third is not -- and because the bench can
            # simply run out, which is what makes simultaneous loss superadditive.
            #
            # A count and a sum, deliberately, rather than a depth RANK: see the note above the
            # loop on why FLEX chains leave no sound definition of "how far down".
            "bench_used": len(promoted),
            "bench_value_used": round(sum(bench_value[p] for p in promoted), 2),
            # Unknown byes are a property of the ROSTER, not of one week: any of those players
            # could be out in any week, so every week's number is equally a floor. Marking only
            # the weeks that happen to have a collision would imply the clean-looking weeks
            # were verified, and they were not.
            "basis": BYE_PARTIAL if unknown else "measured",
        }
    if not out and unknown:
        return {}
    return out


def bye_concentration(roster_players: list[dict], roster_positions: list[str]) -> dict:
    """Is this roster's bye damage STAGGERED across weeks or LAYERED into one?

    Same total, different shape, and the shape is the part a headcount cannot see. Measured on
    twelve fully-drafted rosters from one league: worst-week losses ran 41 to 127 in
    trade_value units while every roster sat at the pigeonhole FLOOR for starters-out. The
    bodies were spread; the value was not. Roster 3 lost 127 in a single week with a
    floor-level headcount, purely because the wrong players shared it.

    `concentration` is the share of a roster's total bye damage landing in its single worst
    week -- deliberately a RATIO, so shape is separated from severity. Two rosters can lose the
    same total and be in completely different trouble: 0.25 means the damage is spread thin
    enough that no week is decisive, 0.62 means most of a season's bye cost arrives at once, in
    a league where each week is an independent matchup.

    It is None, never 0.0, when the roster carries no bye damage at all. A roster with nothing
    to lose has no shape; reporting 0.0 would rank it as maximally staggered, which is a claim
    about a distribution that does not exist.

    Returns {"concentration", "worst_week", "worst_week_loss", "total_loss", "weeks", "basis"}.
    `weeks` is the full profile, zeros included, so a reader can say WHICH week and by how much
    rather than only how bad the shape is -- the traceability is the point, not the ratio.
    """
    weeks = bye_collision(roster_players, roster_positions)
    if not weeks:
        return {"concentration": None, "worst_week": None, "worst_week_loss": None,
                "total_loss": None, "weeks": {}, "basis": BYE_UNKNOWN}
    losses = {week: row["value_lost"] for week, row in weeks.items()}
    total = sum(losses.values())
    worst_week = max(losses, key=lambda w: losses[w])
    basis = weeks[worst_week]["basis"]
    return {
        "concentration": round(losses[worst_week] / total, 3) if total > 0 else None,
        "worst_week": worst_week if total > 0 else None,
        "worst_week_loss": round(losses[worst_week], 2),
        "total_loss": round(total, 2),
        "weeks": {week: round(value, 2) for week, value in sorted(losses.items())},
        "basis": basis,
    }


def bench_capacity(roster_positions: list[str]) -> int:
    """How many bench spots this league gives each team.

    Sleeper states it directly -- roster_positions carries its own "BN" entries -- and nothing
    in this app had ever counted them. slots_from_roster_positions drops them correctly, for
    ITS purpose (a benched player contributes no lineup value), and the number was then simply
    never read anywhere else: the only other "BN" in the tree synthesizes a hardcoded count for
    MOCK drafts. So depth was unbounded in an engine whose real leagues bound it.

    It matters because depth exposure is a RANKING of where insurance is worth buying, and
    bench capacity is the budget: a 5-bench league cannot insure everything a 12-bench league
    can, and the cutoff is the difference between a useful recommendation and a wish list.
    """
    return sum(1 for slot in (roster_positions or []) if slot == "BN")
