"""
Live draft pick recommendations -- a zero-LLM, deterministic valuation engine for an
in-progress Sleeper draft, modeled on (not a clone of) Draft Sharks' War Room "3D Value"
concept: a dynamic form of Value-Based Drafting that recalculates as the draft happens,
not a static pre-draft ranking.

This module and pick_synthesis.py together are the Contextual Decision Matrix Engine
(CDME) -- see README.md's "The Draft Engine" section for the canonical definition and
full architectural picture (CDME -> PickSnapshot -> presentation / debate escalation).
This module owns CDME's base valuation layer (universal_value, Team Acquisition Value);
pick_synthesis.py owns the contextual layer built on top of it.

Deliberately has no LLM in its critical path -- a live draft has a pick clock (often
30s-2min), and a multi-role debate with live web search is nowhere near fast enough to be
the primary recommendation there. Everything here is pandas/dict math over data this app
already has (Draft Sharks' own season/3yr projections, Sleeper's native weekly projections,
live picks, and roster settings). The existing Quant/Beat/Contrarian/Moderator panel remains
available for a genuine toss-up between finalists -- see app.py's Draft Room view -- but it
is never the default path for "who do I take right now."

This module went through a real adversarial audit after its first working version (see git
history) that found several genuine bugs in the math itself, not just missing polish -- the
architecture below reflects that second pass, not the first draft. Read the fixes here as
load-bearing, not decoration.

ARCHITECTURE -- additive and layered, not multiplicative (unchanged from the first pass):
several candidate factors partially describe the same underlying "how much does this player
help a lineup" question, so multiplying them stacks correlated effects, and a team's own
need for a position could inflate a mediocre player's score high enough to outrank an
objectively better one -- conflating "how good is this player" (comparable across every team
watching the draft) with "how good is this player FOR THIS ROSTER" (inherently team-
specific). Kept as two explicit numbers:

    universal_value = BPA + time_horizon_adj + risk_adj
    team_acquisition_value = universal_value + need_bonus + eligibility_bonus

BPA is Value Over Replacement in raw projected POINTS (never Draft Sharks' trade_value/
composite scale directly -- see build_available_pool's docstring on why IDP's real points
have to come from Sleeper's native projection instead), scaled LINEARLY against the single
largest VOR gap in the whole remaining pool -- NOT percentile-ranked. Percentile-ranking VOR
was the first pass's mistake: it threw away the actual size of the gap between players,
which is the entire reason VOR is the right anchor over a bounded score in the first place.
Confirmed live: a real 60-point VOR gap between the #1 and #8 remaining players compressed
to a 2.8-point percentile gap, while the additive adjustment terms below it could swing
several times that -- the adjustments were deciding the board, not the anchor. Linear scaling
against the pool's own largest gap keeps a blowout blowout and a toss-up a toss-up.

Replacement level itself is computed against REMAINING roster demand, not static league-wide
demand -- also a first-pass bug, also caught live: with a fixed target of "the Nth-best
remaining player" (N = num_teams x starters-at-position, held constant), draining a position
past its real demand made replacement level collapse toward the bottom of a thinning pool,
which made every remaining player at that position look artificially scarce right when
nobody actually needed one anymore (in a 12-team 1QB league, the engine ranked the 19th QB
drafted as the #9 pick on the whole board). Fixed by subtracting how many roster slots at
that position are ALREADY filled league-wide from the target before ranking the remaining
pool against it -- once demand is met, the target rank collapses to 1 (replacement = the best
player still on the board), correctly driving VOR there to ~0 for everyone left.

A position Draft Sharks has zero real projection data for at all (currently every IDP
position when Sleeper's projections aren't wired into a given call) falls back to a VOR
computed from trade_value instead of points, using the exact same remaining-demand
replacement-rank logic -- and is folded into the SAME shared linear scale as every points-
anchored player, not given its own separate 0-100 range. That separate range was the other
half of the first pass's IDP bug: ranking the fallback WITHIN each position individually gave
every position's own top player bpa=100 regardless of real demand, so three unrelated
positions' best remaining player all tied at the maximum score and landed in the top 25 of
the whole board on a pure normalization artifact, not real value. Sharing one linear scale
means a position with almost no real roster demand (an IDP_FLEX splitting 0.33 slots across
three positions) correctly can't compete with a well-projected offensive skill player just
because it's "the best of a locally re-normalized handful" -- it has to actually clear the
same bar. bpa_source on every row says which of the three anchors was actually used
(points_vor_draftsharks / points_vor_sleeper_extrapolated / position_relative_trade_value_vor)
-- never silently presented as equivalent precision.

There is no market_adj term. An earlier version folded the composite score back in as a
small corroborating nudge (does the wider market agree with the pure-stats anchor?), but it
turned out to be a systematic bug, not a nudge: comparing a WITHIN-position market percentile
against a CROSS-position VOR percentile meant the adjustment was really just re-measuring how
strong a position is overall, not whether the market disagreed with anything -- confirmed
live, QB (structurally low VOR in a 1QB league) got a mean adjustment 6-8x every other
position's, in the wrong direction (partially UNDOING the real scarcity signal BPA had just
computed correctly). It was also, by a wide margin, the most expensive part of this module
(composite_player_score's cross-source lookup, called once per player in the pool -- ~93% of
this module's total runtime against a full player database, measured directly). Removed
outright rather than patched: a corroboration signal correctly built later would need to
compare like units to like units, which the composite score doesn't currently give this
module without recomputing scarcity itself.

need_bonus is the ONLY team-specific term, added on top rather than multiplied in, and split
by urgency rather than a flat per-slot rate -- also a real fix, not a refinement: a flat rate
scaled with how many total roster slots a position has, which meant a team with ZERO QBs
scored a smaller bonus than a team wanting a fourth bench WR, since WR simply has more named/
flex slots than QB does. An unfilled DEDICATED starting slot (a named position, not a flex
share) is weighted well above remaining flex-only capacity, and flex demand only counts once
a team's dedicated slots are already filled -- see dedicated_slot_counts and the need_bonus
math in compute_draft_board. Still capped low enough that it nudges a close call without
flipping a large universal-value gap (see NEED_BONUS_MAX and test_draft_room.py's invariant
tests) -- that invariant was true and enforced in the first pass too; only the per-position
distribution of the bonus itself needed fixing.

eligibility_bonus is the other team-specific term, added alongside need_bonus rather than
replacing it -- they answer different questions. need_bonus asks "does this roster lack this
POSITION"; eligibility_bonus asks "does this specific player's multi-position eligibility
(WR/DB, TE/FLEX, whatever this league's own roster_positions and Sleeper's fantasy_positions
actually allow) unlock a genuinely better starting lineup than a single-position player of
identical value could." Computed via lineup_optimizer.py's exact assignment-problem solver
(scipy's linear_sum_assignment, not a greedy heuristic -- see that module's own docstring for
why greedy is a real trap here) against THIS roster's actual drafted players, comparing the
best lineup with the candidate's full eligible-position set against the best lineup with only
his single primary position. A single-position player's bonus is exactly 0 by construction
(both calls solve an identical problem), so this never touches a player the rest of this
module already scores correctly.

CORRECTION (a real third-pass bug, caught by an adversarial audit distinct from the first two
above -- see git history and TRADE_VALUE_SCALE_MAX/ELIGIBILITY_BONUS_MAX's own comment for the
full evidence trail): this section used to say eligibility_bonus was deliberately left
uncapped because it's a self-limiting real economic quantity. That reasoning had a real hole
in it -- "self-limiting" only means bounded by the candidate's own trade_value, a DIFFERENT
0-100 scale than the bpa-anchored universal_value/need_bonus sum it gets added into, and the
two scales are not interchangeable on real data (mean divergence 11.7, max 63.0). Left
unconverted, this was the one contextual term with no bpa-scale bound at all, and it could
override a real universal_value gap outright -- confirmed on the committed baseline, an 82.00
bonus (6.8x NEED_BONUS_MAX) flipping a 30+ point gap, reproduced in both a standard 1QB league
and an IDP league. It IS now rescaled into universal_value's own bpa scale and capped at
ELIGIBILITY_BONUS_MAX, same reasoning and same bound as need_bonus: both terms answer "how
good is this player FOR THIS ROSTER," and that class of question is deliberately capped so it
can inform a close call without ever overriding a real talent gap (see
EligibilityBonusWiringTests in test_draft_room.py, specifically
test_eligibility_bonus_cannot_flip_a_large_universal_value_gap, the missing mirror this bug
exposed of test_need_bonus_cannot_flip_a_large_universal_value_gap). The entire prior test
corpus was structurally blind to this: every fixture anywhere in this project built
single-position fantasy_positions, for which eligibility_bonus is exactly 0.0 by construction
-- a lesson worth remembering the next time a path looks covered because a large test suite
passes.

confidence is a SEPARATE number from value entirely, and now built from bpa_source directly
(cheap -- no extra per-player lookup) rather than composite-score cross-source agreement,
since removing market_adj also removed the only reason this module called
composite_player_score at all: points_vor_draftsharks is Draft Sharks' own trusted season
number; points_vor_sleeper_extrapolated is a real stat-based projection but only a single
week extrapolated to a season, genuinely less certain; position_relative_trade_value_vor
means neither source had anything, the lowest-confidence case. High or low, confidence never
feeds RiskAdj or universal_value -- "we don't know" is not the same claim as "this player has
upside," and upside_score's own docstring covers the exact mistake that conflation caused the
first time around.

UPSIDE MODE (round >= UPSIDE_MODE_DEFAULT_ROUND, or toggled on explicitly): late-round picks
rarely move a roster's outcome -- the real value is finding a league-winner, not optimizing
safe positional value. Scores on growth trajectory (Draft Sharks' own proj_3yr outlook
exceeding this season's projection, a real number Draft Sharks already computes) with
confidence surfaced separately, never folded into the score itself.

None of the weighting constants below are empirically backtested against real draft
outcomes -- they're principled, documented, bounded starting points (the same honesty this
app applies everywhere else to anything that isn't a real number pulled from a real source),
named and isolated here specifically so they're easy to find and retune later. The hard
invariants they're bounded to preserve are enforced as tests in test_draft_room.py, not just
asserted in a docstring.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

import lineup_optimizer as lo
from data_merger import DataMerger, name_key, normalize_name
from player_universe import FLEX_SLOT_POSITIONS, FANTASY_POSITIONS, league_usable_positions, player_eligible_positions, player_name, player_position, score_projection

# Sleeper's projection endpoint is per-week, not season-long (see sleeper_client.py's
# get_weekly_projections) -- for positions Draft Sharks doesn't project at all (currently
# every IDP position, see build_available_pool's docstring), a single week's total is
# extrapolated to a rough season-equivalent by this factor purely so it lands on the same
# ORDER OF MAGNITUDE as Draft Sharks' real season projections for offense, which is what
# makes a shared cross-positional VOR meaningful at all. This is a labeled approximation, not
# a real season projection (no bye week, no matchup variance, no injury-game-missed
# adjustment) -- it exists to fix "no real points data at all", not to be mistaken for Draft
# Sharks' own season methodology.
SLEEPER_WEEKLY_TO_SEASON_FACTOR = 17

# Round at which the engine switches from the balanced formula to upside-only scoring,
# absent an explicit override -- matches the "War Room" idea this was modeled on. A deep
# bench/waiver-fringe pick is about finding a league-winning outlier, not filling a need or
# respecting positional scarcity that barely matters by then.
UPSIDE_MODE_DEFAULT_ROUND = 15

# In real competitive superflex play, the SUPER_FLEX slot is filled by a second (or third) QB
# the vast majority of the time -- there isn't enough non-QB flex-caliber value to make
# starting an extra RB/WR/TE correct over a bench-caliber QB once a team already has one
# starter, which is exactly why "superflex" functions as a real QB-scarcity format at all.
# Splitting it EVENLY across QB/RB/WR/TE (this module's original, generic flex-slot logic --
# still correct for every OTHER flex type, where RB/WR/TE genuinely do compete roughly evenly
# for the slot) badly understated real superflex QB demand: confirmed directly, even the
# #1-projected QB by raw season points ranked outside the top 30 overall on a real superflex
# board before this constant existed, nowhere close to the real market's well-known "4-6 QBs
# typically go in round 1 of a 12-team superflex startup" behavior. Not empirically
# backtested to an exact percentage -- a principled, bounded starting point, same honesty this
# module applies to every other unproven constant. Even with this fix, pure points-based VOR
# still likely underrates elite QBs somewhat relative to real superflex market pricing: the
# market's real premium partly reflects a hard structural scarcity (only ~32 real starting-
# caliber NFL QBs exist leaguewide, a ceiling RB/WR/TE don't share) that a single season's
# point projection doesn't fully capture on its own -- worth knowing as a real limitation,
# not silently pretending this fix closes the whole gap.
SUPER_FLEX_QB_SHARE = 0.85

# Cliff-anchored superflex QB replacement (see qb_startable_floor and replacement_levels):
# "startable QB" is defined as projecting at least this FRACTION of the ANCHOR_RANK-th best
# QB's projection in the committed baseline. Chosen by STABILITY BASIN, not by tuning to any
# player's landing spot: real Draft Sharks QB projections are nearly flat from ~QB6 to ~QB24
# and then collapse (QB28 projects ~198, QB29 ~127, QB31 ~56 in the current baseline), so any
# fraction from 0.45 to 0.60 of QB12 lands inside that cliff and identifies the identical
# startable-tier boundary -- measured directly against the committed data, a 48-point-wide
# band of threshold values all producing the same replacement rank. Contrast the flat
# extra-bench-demand constant tried and reverted earlier (see replacement_levels' docstring):
# its plausible parameter range swung QB1's VOR from 132 to 351 because a demand COUNT can
# land on either side of the cliff, which is exactly the fragile magic-number-hunting this
# app's constants are supposed to avoid.
QB_STARTABLE_ANCHOR_RANK = 12
QB_STARTABLE_FLOOR_FRACTION = 0.5

# time_horizon_adj and risk_adj are both small, bounded, additive nudges on the same linear
# 0-100 BPA scale -- deliberately incapable of overriding a real VOR gap on their own (see
# module docstring's ARCHITECTURE section and test_draft_room.py's invariant tests).
TIME_HORIZON_SLOPE = 0.20         # applied, dynasty leagues only, to (3yr-proj percentile -
TIME_HORIZON_CLAMP = (-10.0, 10.0)  # season-proj percentile)

# Current-status discount, not a predictive injury-likelihood model -- see module docstring.
# Additive and one-directional: an injury can only ever subtract from universal_value, never
# add (a hard invariant -- see test_draft_room.py), so a thin-data variance side-effect can
# never turn a health flag into a value boost.
#
# Full-word keys, matching Sleeper's own real injury_status vocabulary and every other
# injury_status literal already in this codebase (app.py's INJURY_OK_STATUSES, every test
# fixture in test_lineup_readiness.py/test_screen_context.py). Previously kept single-letter
# codes ("O"/"D"/"Q") for everything but "IR" -- since player_universe.py and this module's
# own players_db construction both pass injury_status straight through from Sleeper's raw
# payload with zero transformation, those abbreviated keys never matched a real value, so
# Out/Doubtful/Questionable players silently got NO discount at all (confirmed directly: a
# real player set to injury_status="Out" lost exactly 0.0 universal_value pre-fix). "IR" was
# the one status this went unnoticed for, since it's already an abbreviation in Sleeper's own
# real vocabulary too -- see test_risk_adj_vocabulary_mismatch... in test_draft_room.py for
# the full evidence trail.
RISK_ADJ = {"IR": -18.0, "Out": -10.0, "Doubtful": -5.0, "Questionable": -1.5}

# Dynasty risk_adj calibration, history preserved for attribution (see
# test_draft_room.py's DynastyRiskAdjSofteningTests/RiskAdjTrajectoryScalingTests and
# run_risk_adj_softening_measurement.py / run_risk_adj_experiment_D_comparison.py /
# run_risk_adj_D_pathology_stress_test.py for the full evidence trail):
#
# Experiment "A" (uniform 0.5x dynasty scaling) shipped first as the safe, minimal fix for a
# real bug: RISK_ADJ was applied UNCONDITIONALLY, the same in dynasty as in redraft, even
# though time_horizon_adj (a few lines up) already gets its own is_dynasty gate for exactly the
# reason that a current-week health flag should matter less against a 3-year horizon. A fixed
# the flagship pathology (a thin-bpa, max-positive-trajectory real player crossing zero purely
# from an injury flag) but, being a uniform scale, could not express the actual claim in
# question: that an injury should matter less for a player whose value is genuinely
# forward-looking than for one whose value is already realized in current production.
#
# Experiment "D" (below) replaces A as the production model: the SAME four RISK_ADJ magnitudes,
# still unchanged, but now scaled by each player's OWN time_horizon_adj rather than by a flat
# dynasty-wide constant. Verified independent of the injury signal by direct inspection before
# use (time_horizon_adj is computed purely from proj_3yr/_points percentiles, entirely before
# injury_status is read anywhere) -- no double-counting loop. Stress-tested on the full real
# offense pool before promotion: zero D-only ordering reversals at any healthy-value-gap size
# (D never flips an order flat/A wouldn't already flip), and D never flips a pair with a 25+
# point healthy-value gap at all -- it only ever reorders genuinely close, contextual decisions,
# never overrides a real value gap. Median realized scale across the real pool is 0.994 (most
# players get no relief at all, since most trajectories aren't positive); even at the floor, a
# real, non-trivial penalty always remains (never "injury doesn't matter").
DYNASTY_RISK_ADJ_MIN_SCALE = 0.3  # floor: even max-positive trajectory keeps 30% of the flat penalty

# The ONLY team-specific term. Added on top of universal_value, never multiplied into it.
# Split by urgency, not a flat per-slot rate -- see module docstring's need_bonus section for
# the real bug this replaced. A dedicated (named, non-flex) unfilled starting slot is weighted
# far above remaining flex-only capacity, and flex demand only counts once dedicated slots are
# already filled, so "zero QBs" outweighs "wants a fourth bench-eligible WR" the way real
# draft urgency actually does.
NEED_BONUS_PER_DEDICATED_SLOT = 4.0
NEED_BONUS_PER_FLEX_SHARE = 1.0
NEED_BONUS_MAX = 12.0

# UNIT CONVERSION for the other team-specific term. lineup_optimizer.eligibility_bonus solves a
# real assignment problem and correctly returns its answer in whatever currency its caller fed
# it -- here that is Draft Sharks' trade_value (see _team_roster_players' docstring on why a
# roster's already-drafted players can only be priced that way). But team_acquisition_value is
# a bpa-scale sum: universal_value is bpa-anchored and need_bonus is a bpa-scale nudge capped
# at NEED_BONUS_MAX. Adding a trade_value-denominated number straight into that sum mixed two
# scales that are NOT interchangeable -- measured on the committed baseline, mean
# |bpa - trade_value| = 11.7 with a max divergence of 63.0 and a correlation of only 0.829
# (M Nabers: bpa 18.0 vs trade_value 81.0; C McCaffrey: bpa 85.6 vs trade_value 47.0). The
# mean units error alone was about the size of the entire NEED_BONUS_MAX cap.
#
# Left unconverted this was the one uncapped contextual term, and it could override real value
# gaps outright: reproduced on real data in BOTH a standard 1QB league (WR/TE dual eligibility,
# a common real Sleeper listing) and an IDP league (WR/DB, the Travis-Hunter case this module
# was built for) -- an 82.00 bonus, 6.8x NEED_BONUS_MAX, flipping a 35-point universal_value
# gap and lifting a #10 board player to #1. Worse, the SAME roster hole was priced ~19-248x
# differently depending on which term happened to price it (a genuine TE filling an empty TE
# slot earned need_bonus 4.33; a dual-eligible WR filling that identical slot earned 82.00).
#
# The conversion is a pure linear rescale by a documented ratio, applied here at the point of
# consumption rather than inside lineup_optimizer (which stays honest in its caller's currency,
# and whose other consumer, roster_diagnostics.py, genuinely wants trade_value units). It is
# dimensionally correct at EVERY magnitude, not just at the tail a clamp would catch, and it
# preserves the term's full within-term ordering. It needs no per-player division (so the 14
# real players with trade_value == 0.0 are not a hazard) and is bounded by construction:
# eligibility_bonus <= candidate trade_value <= TRADE_VALUE_SCALE_MAX, so the converted value
# can never exceed ELIGIBILITY_BONUS_MAX. Bound set equal to NEED_BONUS_MAX deliberately --
# both terms answer "how good is this player FOR THIS ROSTER", and the architecture already
# fixes the bound for that class; a different number would be inventing a magnitude the
# evidence does not support. The explicit min() below is a defensive guard against anomalous
# source data above the documented scale, not the mechanism that does the bounding.
TRADE_VALUE_SCALE_MAX = 100.0  # Draft Sharks' documented trade_value range (verified: real max is exactly 100.0)
ELIGIBILITY_BONUS_MAX = NEED_BONUS_MAX

UPSIDE_GROWTH_WEIGHT = 0.5

# confidence is now a direct, cheap encoding of which anchor a row actually used -- see
# module docstring on why this replaced a composite-score cross-source-agreement lookup.
CONFIDENCE_BY_SOURCE = {
    "points_vor_draftsharks": 80.0,
    "points_vor_sleeper_extrapolated": 60.0,
    "points_vor_sleeper_seeded": 50.0,
    "position_relative_trade_value_vor": 35.0,
}

# The committed baseline CSVs whose points are a season total TRANSCRIBED from a specific
# league's own Sleeper display (see sleeper_client.build_baseline_projection_rows and
# data/baseline/sleeper_projection_provenance.json) -- not Draft Sharks' season-long
# modeling, and not this module's own points_vor_sleeper_extrapolated path either (that one
# only ever fires for a LIVE Sleeper feed scored against THIS league's real settings; see
# TheBaselineIsScoringInertTests for the confirmed fact that nothing here re-scores these
# rows for any league). Every row carrying a "projection" used to be labeled
# points_vor_draftsharks unconditionally, which was simply false for these two files' 69
# rows (37 K + 32 DEF on the committed baseline) -- confirmed by cross-referencing every
# board row's bpa_source against the source_file it actually came from.
#
# Given CONFIDENCE_BY_SOURCE's own stated confidence tier: below Draft Sharks (80.0, a
# dedicated cross-league projection methodology) and below sleeper_extrapolated (60.0, which
# at least scores against the ACTUAL league being drafted) -- these are real season
# projections, but fixed to whichever unrelated league's scoring happened to produce them,
# and cannot adapt to the league actually being drafted the way either of those two can.
KDST_SEEDED_SOURCE_FILES = {"sleeper_kicker_projections.csv", "sleeper_dst_projections.csv"}


def starter_slot_counts(roster_positions: list[str]) -> dict[str, float]:
    """How many starting slots this league's roster_positions actually offers per fantasy
    position, expanding flex slots proportionally across whatever they're eligible for
    (e.g. a FLEX slot counts as +1/3 toward each of RB/WR/TE's own total) rather than
    ignoring flex capacity entirely -- a league heavy on flex slots genuinely has more
    starting demand at those positions than its named slots alone would suggest. This is
    also what makes replacement level genuinely league-specific rather than a generic
    positional constant: a 2-TE league's second TE slot inflates TE's count automatically,
    etc. -- no separate per-format branching needed for most flex types, it falls out of
    actually reading this league's own roster_positions.

    SUPER_FLEX is the one deliberate exception to "split evenly across every eligible
    position": see SUPER_FLEX_QB_SHARE's own comment for why an even split badly understates
    real superflex QB scarcity. Every other flex type (FLEX, WRRB_FLEX, REC_FLEX, IDP_FLEX)
    keeps the even split -- those genuinely do get filled by whichever eligible position is
    best roughly interchangeably in real drafting behavior, unlike SUPER_FLEX's real-world QB
    dominance."""
    counts: dict[str, float] = {p: 0.0 for p in FANTASY_POSITIONS}
    for slot in roster_positions or []:
        if slot in FANTASY_POSITIONS:
            counts[slot] += 1.0
        elif slot == "SUPER_FLEX" and "QB" in FLEX_SLOT_POSITIONS[slot]:
            eligible = FLEX_SLOT_POSITIONS[slot]
            non_qb = [pos for pos in eligible if pos != "QB"]
            counts["QB"] += SUPER_FLEX_QB_SHARE
            remaining_share = (1.0 - SUPER_FLEX_QB_SHARE) / len(non_qb) if non_qb else 0.0
            for pos in non_qb:
                counts[pos] += remaining_share
        elif slot in FLEX_SLOT_POSITIONS:
            eligible = FLEX_SLOT_POSITIONS[slot]
            for pos in eligible:
                counts[pos] += 1.0 / len(eligible)
    return counts


def dedicated_slot_counts(roster_positions: list[str]) -> dict[str, int]:
    """Named (non-flex) starting slots per position only -- e.g. the two literal "WR" slots
    in a roster that also has FLEX/WRRB_FLEX capacity, not the flex share too. This is the
    "must have one of these to start at all" number need_bonus weights heaviest -- see
    module docstring's need_bonus section."""
    counts: dict[str, int] = {p: 0 for p in FANTASY_POSITIONS}
    for slot in roster_positions or []:
        if slot in FANTASY_POSITIONS:
            counts[slot] += 1
    return counts


def _percentile_map(values: pd.Series) -> pd.Series:
    """0-100 percentile within this exact Series, higher-is-better. Used ONLY for the
    season-vs-3yr trajectory comparison feeding time_horizon_adj -- a small, bounded,
    additive nudge where relative ordering is the right comparison. NOT used for bpa itself
    (see module docstring on why percentile-ranking the VOR anchor was a real bug)."""
    return values.rank(pct=True) * 100


def _drafted_counts_by_position(picks: list[dict], players_db: dict[str, dict]) -> dict[str, int]:
    """How many picks, league-wide (every roster, not just one), have landed at each fantasy
    position so far. A plain census -- it is NOT remaining demand and must not be subtracted
    from league-wide slot capacity to produce one (see remaining_starter_demand for why that
    subtraction is wrong). Still the right number for anything that genuinely wants "how many
    of these have gone", e.g. positional-run detection."""
    counts: dict[str, int] = {}
    for pick in picks:
        info = players_db.get(str(pick.get("player_id")))
        if not info:
            continue
        position = player_position(info)
        if position:
            counts[position] = counts.get(position, 0) + 1
    return counts


def team_filled_by_position(
    picks: list[dict], players_db: dict[str, dict],
) -> dict[str, dict[str, int]]:
    """roster_id -> position -> how many that ONE roster has taken there. The per-team census
    remaining_starter_demand is built from, and the generalisation of _team_starters_filled
    (which answers the same question for a single roster and now delegates here, so there is
    one definition of "what has this team taken" rather than two)."""
    filled: dict[str, dict[str, int]] = {}
    for pick in picks:
        info = players_db.get(str(pick.get("player_id")))
        if not info:
            continue
        position = player_position(info)
        if not position:
            continue
        roster = filled.setdefault(str(pick.get("roster_id")), {})
        roster[position] = roster.get(position, 0) + 1
    return filled


def remaining_starter_demand(
    roster_positions: list[str], num_teams: int, picks: list[dict], players_db: dict[str, dict],
) -> dict[str, float]:
    """How many starting slots at each position are STILL UNFILLED across the league --
    summed per team, never subtracted league-wide.

        sum over teams of max(starter_slot_counts[position] - that team's own picks there, 0)

    EXACT and BOUNDED. It is computed entirely from roster_positions and the observed picks;
    it carries no prior, no estimate and no behavioural claim. It is bounded in
    [0, num_teams x slots], is monotone non-increasing as picks accumulate, reaches exactly
    zero when every team has filled its slots, and is invariant to the ORDER the picks
    arrived in. Those properties are what make it usable as the domain test for a valuation
    anchor -- see replacement_levels.

    WHY PER TEAM. The previous model computed `num_teams x slots - drafted_league_wide`, and
    that is not the same quantity, because max(., 0) does not distribute over a sum: one team
    hoarding at a position silently cancelled another team's unmet need at the same position.
    Measured on six completed 240-pick boards, the league-wide form declared a position
    exhausted 2.0 rounds early on average, ran as far as -71 (a "demand" that cannot exist),
    and for four board-positions declared exhaustion for a position that never satisfied its
    starter demand at all. The pathological case states it plainest: one team taking twelve
    quarterbacks reads as 12 - 12 = 0, "QB satisfied", while eleven teams still have none.

    TEAMS WITH NO PICKS YET count as needing all of their starters, which is correct for the
    case this actually runs in -- a live draft where a team simply has not reached its first
    selection. It is also exactly what the league-wide form implied, so nothing changes for a
    draft observed from its own beginning.

    ROSTER UNIVERSE. Because this makes a per-team claim, it is only meaningful when the pick
    history belongs to the league being modelled. A history carrying more distinct rosters
    than the league has teams did not come from this league, and is refused rather than
    modelled -- the league-wide form could not detect that at all, since it only ever summed a
    count. See compute_draft_board's `demand_picks` for the one caller that supplies a
    separate history, and why an EMPTY one is well defined while a foreign one is not."""
    slot_counts = starter_slot_counts(roster_positions)
    filled = team_filled_by_position(picks, players_db)
    if len(filled) > max(num_teams, 0):
        raise ValueError(
            f"demand history covers {len(filled)} rosters but the league has {num_teams} teams; "
            "per-team starter demand cannot be computed from a foreign roster universe"
        )
    rosters = list(filled.values()) + [{}] * (num_teams - len(filled))
    return {
        position: sum(max(slot_counts.get(position, 0.0) - roster.get(position, 0), 0.0)
                      for roster in rosters)
        for position in FANTASY_POSITIONS
    }


def remaining_draft_capacity(
    roster_positions: list[str], num_teams: int, picks: list[dict],
) -> float:
    """How many draft picks the league still has to spend, summed per team:

        sum over teams of max(draftable_slots_per_team - that team's picks so far, 0)

    EXACT and BOUNDED, reaching exactly zero when every roster is full. Counts EVERY pick a
    team has made, including one spent on a position this league cannot start -- that pick
    still consumed a roster spot, and excluding it would assert it never happened. (The
    previous accounting excluded exactly those picks from the count while still counting their
    slots in the total, so it believed the league had more picks left than it did.)"""
    per_team = draftable_slots_per_team(roster_positions)
    made: dict[str, int] = {}
    for pick in picks:
        roster = str(pick.get("roster_id"))
        made[roster] = made.get(roster, 0) + 1
    counts = list(made.values()) + [0] * max(num_teams - len(made), 0)
    return float(sum(max(per_team - n, 0) for n in counts))


def _rookie_lookup(merger: DataMerger) -> dict[tuple[str, str], bool]:
    """name_key -> is this player flagged a rookie, straight from KeepTradeCut's own export
    (its rankings visually tag current-class rookies, which its parser already captures --
    see parse_keeptradecut_pdf's "rookie" column). This is real, already-collected source
    data, not a guess: it's what lets pool_scope filter to "rookies only" or "veterans only"
    by DETECTING who's actually a rookie this season, rather than a manual per-player list
    that goes stale the moment a new class debuts.

    CDME's ingestion trust boundary, made explicit: merger.external_values also carries
    bot_research.json's own LLM-originated findings (source_name == "bot_research", see
    data_merger.load_bot_research_as_external), sharing this same DataFrame. The
    source_name == "keeptradecut" filter below is what keeps that data out of CDME's own
    computation -- proven, not just asserted, by test_cdme_ingestion_boundary.py's adversarial
    injection tests. Loosening this filter (or reading any other column off an unfiltered
    `ev`) would reopen that boundary."""
    ev = merger.external_values
    if ev.empty or "rookie" not in ev.columns:
        return {}
    ktc = ev[(ev["source_name"] == "keeptradecut") & ev["rookie"].notna()]
    if ktc.empty:
        return {}
    return dict(zip(ktc["_name_key"], ktc["rookie"]))


def build_available_pool(
    merger: DataMerger,
    players_db: dict[str, dict],
    drafted_player_ids: set[str],
    usable_positions: set[str],
    sleeper_projections: Optional[dict[str, dict]] = None,
    scoring_settings: Optional[dict] = None,
    pool_scope: str = "all",
) -> pd.DataFrame:
    """One row per undrafted, fantasy-relevant player this app has a real number for --
    joined from Sleeper's player_id-keyed database (drafts speak player_id, the ranking
    sources speak name) the same way player_universe.py already bridges the two elsewhere
    in this app. A player with no usable number at all is dropped, not scored at 0 --
    there's no honest BPA to rank them by, same "don't fabricate a number" rule as
    everywhere else.

    "A real number" means a season points projection OR a trade value. It used to mean a
    trade value alone, which was equivalent right up until points started arriving from a
    source that publishes no trade values (league-scored Sleeper projections -- see
    sleeper_client.build_baseline_projection_rows). After that the old rule silently
    conflated two different situations: "nothing is known about this player" and "we have
    real league-scored points, but one vendor's trade-value chart stopped early."

    Measured before the change, the second case was doing real damage at K/DEF:
      - Supply capped at 13 of 37 kickers and 13 of 32 defenses, with NO backfill: those
        13 were a permanent allowlist, so drafting them emptied the position to zero
        while real, projected players sat unused. A 12-team league where two managers
        take a second defense for bye/matchup coverage exhausts the position outright.
      - The admitted 13 were not the TOP 13 -- they were a vendor subset scattered
        through the field (Sleeper's K4 and DEF8 were both excluded while lower-projected
        players were admitted), so replacement level was computed on a distorted set and
        overstated the best K/DEF's VOR by ~45%.
    Widening the rule adds ZERO players at QB/RB/WR/TE (measured): Draft Sharks publishes
    a trade value for every offensive player it projects, so the two conditions are still
    equivalent there. The whole effect is confined to positions where points now arrive
    independently of a trade-value chart.

    sleeper_projections (player_id -> raw stat category -> projected value, from
    SleeperClient.get_weekly_projections) and scoring_settings (this league's real Sleeper
    scoring rules), when both given, are scored into sleeper_points via
    player_universe.score_projection -- NEVER a pre-computed point total handed over by an
    external site. That distinction matters here specifically: this app can then answer
    "this DB is projected for 7 sacks, and this league gives 8 points per sack" instead of
    blindly trusting someone else's number, which is what actually lets an unusual scoring
    rule (a big sack bonus, IDP tackle premiums, whatever this league's own settings say)
    change which players matter -- see compute_draft_board's docstring for where this feeds
    the VOR anchor for positions Draft Sharks doesn't project at all (currently IDP).

    pool_scope: "all" (default -- a startup/veteran draft, where a rookie who's already on
    an NFL roster is just as legitimately draftable as anyone else), "rookies_only" (this
    season's annual rookie draft), or "veterans_only" (a redraft/keeper league that excludes
    rookies entirely). Which players actually count as rookies comes from KeepTradeCut's own
    export (see _rookie_lookup) -- real source data, not a maintained list that goes stale
    every draft class. A player KTC doesn't cover at all is treated as "not a rookie" for
    veterans_only/all (the common case; excluding them by default would silently shrink the
    veteran pool for no real reason) and excluded from rookies_only (no positive evidence
    they belong there).

    No composite/cross-source lookup happens here -- an earlier version called
    composite_player_score per player to feed a market-corroboration adjustment that turned
    out to be both wrong (see module docstring) and, by a wide margin, this module's most
    expensive operation. Only merge_player's own (cheap) lookup remains.
    """
    rookie_by_key = _rookie_lookup(merger) if pool_scope in ("rookies_only", "veterans_only") else {}
    rows = []
    for player_id, info in players_db.items():
        if player_id in drafted_player_ids:
            continue
        position = player_position(info)
        if position not in usable_positions:
            continue
        if info.get("status") in ("Inactive", "Retired"):
            continue
        name = player_name(info, player_id)
        if pool_scope != "all":
            is_rookie = rookie_by_key.get(name_key(normalize_name(name)), False)
            if pool_scope == "rookies_only" and not is_rookie:
                continue
            if pool_scope == "veterans_only" and is_rookie:
                continue
        match = merger.merge_player(name, position=position, team=info.get("team"))
        if not match.get("matched"):
            continue
        if match.get("trade_value") is None and match.get("projection") is None:
            continue
        sleeper_points = None
        if sleeper_projections is not None and scoring_settings is not None:
            raw_stats = sleeper_projections.get(player_id)
            if raw_stats:
                scored = score_projection(raw_stats, scoring_settings)
                # A true zero here is indistinguishable from an empty/stale stat line --
                # IDP projections specifically have a known history of gaps (flagged
                # directly, unverified from this environment -- no live Sleeper access to
                # confirm current data quality). Treat it as "no real projection" rather
                # than "this player projects for zero," same as a missing entry entirely.
                sleeper_points = scored if scored != 0 else None
        rows.append({
            "player_id": player_id,
            "name": name,
            "position": position,
            "team": info.get("team"),
            "injury_status": info.get("injury_status"),
            "trade_value": match.get("trade_value"),
            "projection": match.get("projection"),
            "proj_3yr": match.get("proj_3yr"),
            "sleeper_points": sleeper_points,
            # Which committed file this row's projection actually came from -- not used for
            # anything about the player's VALUE, only so compute_draft_board can label bpa_source
            # honestly instead of assuming every non-live-sync "projection" came from Draft
            # Sharks (see KDST_SEEDED_SOURCE_FILES).
            "source_file": match.get("source_file"),
            # Which canonical row this player's numbers came from. Not a value, not displayed --
            # it exists so the pool can assert it never prices two different players off one
            # row (see the injectivity pass below), and so a caller can trace a pool row back
            # to the record it was joined from.
            "_canonical_key": match.get("match_canonical_key"),
            "_match_path": match.get("match_path"),
            "_match_verified": match.get("match_verified"),
        })
    if not rows:
        return pd.DataFrame(columns=[
            "player_id", "name", "position", "team", "injury_status", "trade_value",
            "projection", "proj_3yr", "sleeper_points", "source_file", "bpa",
            "_canonical_key", "_match_path", "_match_verified",
        ])
    return _drop_contested_identities(pd.DataFrame(rows))


def _drop_contested_identities(pool: pd.DataFrame) -> pd.DataFrame:
    """Two different Sleeper players resolving onto ONE canonical record is a contested
    identity, and at least one of them is a misidentification. Nothing here can tell which, so
    neither is priced -- declining is the only honest outcome, and it is the same rule this
    module already applies everywhere else absence turns up.

    Dropping BOTH costs the real player his row, which is a genuine loss and is the point: a
    phantom duplicate is not a local error. It is a second copy of a real player's points at
    his position, so it moves that position's replacement RANK -- a league-level quantity every
    player at that position is measured against. Measured before the identity guard landed:
    +1 to +8 real points of baseline error, cutting top-of-position VOR by 2-5%, and unbounded
    in principle depending on where in the curve the duplicate falls. Silently pricing two
    players off one row trades a visible missing row for an invisible wrong anchor.
    """
    if pool.empty or "_canonical_key" not in pool.columns:
        return pool
    keyed = pool["_canonical_key"].map(lambda k: k if isinstance(k, tuple) else None)
    counts = keyed.value_counts()
    contested = {k for k, n in counts.items() if n > 1}
    if not contested:
        return pool
    return pool[~keyed.isin(contested)].reset_index(drop=True)


def qb_startable_floor(merger: DataMerger) -> Optional[float]:
    """The absolute points threshold below which a QB no longer counts as startable --
    QB_STARTABLE_FLOOR_FRACTION x the QB_STARTABLE_ANCHOR_RANK-th best QB projection in the
    committed baseline (the FULL baseline, deliberately not the remaining draft pool: an
    anchor that drifted as elites were drafted would eventually slide the threshold below the
    cliff and start counting true backups as startable, the exact wrong direction). None when
    the baseline doesn't carry enough projected QBs to anchor against -- the honest "don't
    fabricate a threshold" default, which makes replacement_levels fall back to the
    starter-slot demand model unchanged."""
    proj = merger.projections
    if proj.empty:
        return None
    qb = proj[(proj["position"] == "QB") & proj["projection"].notna()]["projection"].astype(float)
    if len(qb) < QB_STARTABLE_ANCHOR_RANK:
        return None
    anchor = float(qb.nlargest(QB_STARTABLE_ANCHOR_RANK).iloc[-1])
    return QB_STARTABLE_FLOOR_FRACTION * anchor


def replacement_levels(
    pool: pd.DataFrame, value_col: str, roster_positions: list[str], num_teams: int,
    remaining_demand: Optional[dict[str, float]] = None,
    startable_floors: Optional[dict[str, float]] = None,
) -> dict[str, float]:
    """Per position, this pool's value_col at the player sitting at replacement rank within
    the REMAINING pool. The rank target is remaining_starter_demand -- how many starting slots
    at that position are still unfilled ACROSS THE LEAGUE, summed per team. remaining_demand
    defaults to "nobody has drafted yet" (full league-wide slot capacity) when omitted, which
    is the right anchor for a caller that wants the pre-draft level rather than a live draft's
    state.

    DOMAIN. This is defined only while a position has at least one whole starting slot still
    unfilled. Below that -- remaining demand under 1, or no remaining player clearing a
    startability floor -- the position's key is OMITTED, and callers must read absence as
    "no starter-demand replacement exists here", never as zero and never as rank 1.

    That omission replaces a clamp, and the clamp was the defect. Ranks used to be floored at
    1, so "no starter slot creates demand here any more" and "one slot still needs filling"
    produced the identical rank and therefore the identical level -- and at rank 1 the level
    resolves to THE BEST PLAYER STILL ON THE BOARD, which asserts that the scarcest thing left
    at that position is the freely available alternative. That is backwards, and it put every
    remaining player at or below replacement by construction: measured on a real 12x20 board,
    pool-wide maximum VOR reached exactly 0.0 at pick 108 and stayed there for the remaining
    55% of the draft, taking bpa with it.

    An earlier docstring here described that collapse as correct ("drain a position past its
    real demand and the target collapses to 1 ... correctly driving everyone left there toward
    ~0 VOR"). It is not correct, and the same audit found the claim of dynamism overstated
    too: while demand stays positive and picks come off the top, rank shrinkage and pool drain
    cancel exactly, so the level is algebraically identical to the static pre-draft one
    (measured: identical at 19 of 19 sample points for five of six positions across all 240
    picks). The real behaviour is a fixed anchor with a domain, which is what this now says.

    An extra flat per-team "bench QB demand" term for superflex leagues was tried and reverted
    here (see git history) -- real Draft Sharks QB projections have a genuine CLIFF around
    rank ~27-30 (a low-end starter still projects ~250 points; the next real backup falls to
    ~30-100), not a smooth gradient, so any fixed extra-demand constant either landed short of
    real market behavior or overshot straight past that cliff into "replacement = a
    non-fantasy-relevant scrub," making an elite QB's VOR swing wildly for a tiny, arbitrary
    change in the constant (confirmed: 0.3 vs 0.4 extra demand moved Josh Allen from 7th to
    4th overall). That's exactly the kind of fragile, magic-number-hunting this app's own
    constants are supposed to avoid.

    startable_floors is the successor that DID survive that scrutiny: for a position it
    covers (currently only QB in a superflex league -- see qb_startable_floor and
    compute_draft_board's wiring), the replacement rank is the count of REMAINING players at
    that position projecting at or above an absolute startability threshold, instead of a
    demand headcount. Keying off the projection curve's own discontinuity is what makes it
    stable where the flat constant wasn't: measured directly against the committed baseline,
    every threshold across a 48-point-wide band identifies the identical boundary (see
    QB_STARTABLE_FLOOR_FRACTION's comment), because the count model's failure mode -- landing
    a rank on the far side of the cliff -- can't happen when the cliff itself defines the
    boundary. The dynamics stay correct for free: drafted startable QBs leave the remaining
    pool, the above-floor count shrinks, replacement rises, and VOR compresses toward 0 once
    the startable tier is exhausted -- the same collapse behavior the remaining-demand model
    has. Positions without a floor (everything else, and every position in a 1QB league)
    keep the remaining-demand model unchanged.

    Recomputed fresh every time this module is asked for a board, never cached across
    picks."""
    demand = (
        remaining_demand if remaining_demand is not None
        else {p: num_teams * starter_slot_counts(roster_positions).get(p, 0.0)
              for p in FANTASY_POSITIONS}
    )
    levels: dict[str, float] = {}
    # player_id tiebreaker + kind="stable" -- see compute_draft_board's own sort_values calls
    # for the full reasoning (input-order-independent tiebreaking among exact ties). Only
    # added when the column is actually present: this function is also called directly, in
    # tests, against minimal hand-built pools that carry only "position" and value_col --
    # narrower than the real pool compute_draft_board itself always passes.
    sort_cols = [value_col, "player_id"] if "player_id" in pool.columns else [value_col]
    sort_ascending = [False, True] if len(sort_cols) == 2 else [False]
    for position in FANTASY_POSITIONS:
        at_pos = pool[pool["position"] == position].sort_values(
            sort_cols, ascending=sort_ascending, kind="stable",
        )
        if at_pos.empty:
            continue
        floor = (startable_floors or {}).get(position)
        if floor is not None:
            # No remaining player clears the startability threshold -> there is no startable
            # replacement at this position, which is a different fact from "the best one left
            # is the replacement". Declining here closes the second, independent copy of the
            # >= 1 clamp that used to live on this branch.
            rank = int((at_pos[value_col] >= floor).sum()) or None
        else:
            rank = _remaining_demand_rank(position, demand)
        if rank is None:
            continue  # outside the domain -- see this function's docstring
        idx = min(rank - 1, len(at_pos) - 1)
        levels[position] = float(at_pos.iloc[idx][value_col])
    return levels


def _remaining_demand_rank(
    position: str, remaining_demand: dict[str, float],
) -> Optional[int]:
    """How many players deep at `position` still carry unfilled starter demand -- the plain
    (non-startable-floor) half of replacement_levels' rank math, factored out so
    replacement_ranks() below reuses the identical rule rather than restating it.

    None, never 1, when less than one whole starting slot is still unfilled. A demand of 0.7
    is not a demand for one more player, and rounding it up to rank 1 is exactly the
    conflation this returns None to avoid -- see replacement_levels' own docstring."""
    demand = remaining_demand.get(position, 0.0)
    if demand < 1:
        return None
    return int(round(demand))


def replacement_ranks(
    roster_positions: list[str], num_teams: int,
    picks: Optional[list[dict]] = None, players_db: Optional[dict[str, dict]] = None,
) -> dict[str, Optional[int]]:
    """Per position, the same remaining-demand RANK replacement_levels resolves internally --
    exposed directly as an integer (not a value threshold against a scored pool), for callers
    that need "how many players deep at this position still carry real starter-relevant
    demand" without needing a scored pool at all. Used by pick_synthesis.narrow_candidates to
    give a position-filtered board view genuine positional depth instead of just its single
    best player (see that function's own docstring) -- the depth itself is real and
    league-aware (a thin position stays thin, a deep one stays deep, and it shrinks correctly
    as that position gets drafted out), it's simply the DISPLAY-facing sibling of the same
    number replacement_levels already uses for VOR.

    Deliberately does not include the QB startable-floor refinement (see qb_startable_floor/
    replacement_levels) -- that one only ever nudges VOR's own replacement anchor by a few
    ranks and needs an actual points-scored pool to evaluate against a threshold; the plain
    remaining-demand rank alone is already the same real, tested, per-league signal this
    module relies on everywhere else it doesn't apply.

    None for a position whose starter demand is exhausted -- the same domain
    replacement_levels declines on, reported the same way. A consumer that wants a display
    depth for such a position has to choose one deliberately (see
    pick_synthesis.position_view_depth); it cannot inherit "1" from a clamp that meant
    something else."""
    demand = remaining_starter_demand(roster_positions, num_teams, picks or [], players_db or {})
    return {
        position: _remaining_demand_rank(position, demand)
        for position in FANTASY_POSITIONS
    }


def drafted_counts_by_position(picks: list[dict], players_db: dict[str, dict]) -> dict[str, int]:
    """Public wrapper over _drafted_counts_by_position for callers outside this module (e.g.
    pick_synthesis.narrow_candidates, via replacement_ranks above) that need the same real
    per-position already-drafted counts replacement_levels itself uses."""
    return _drafted_counts_by_position(picks, players_db)


# -- draft-horizon consumption: what will still be here when the draft ENDS ---------------
#
# replacement_levels answers "what is this position worth over the guy at starter-demand rank
# RIGHT NOW". That prices replacement at draft day. It is the right question for a position
# you can only acquire by drafting, and the wrong one for a position whose replacement is
# still sitting there when the draft ends -- and the difference is measurable rather than
# rhetorical. Scored under one real league's settings, the best player still undrafted when
# the draft ends delivers 98% of a starting defense and 96% of a starting kicker, against 36%
# of a starting running back. Waiting costs 0.12 pts/week at DEF and 7.53 at RB.
#
# Nothing below knows what a kicker is. Every position goes through the identical arithmetic;
# the split above falls out of each position's own value decay, which is the point.

HORIZON_UNDRAFTED_SLOTS = ("IR",)  # slots a draft doesn't fill, so they aren't draft demand
# Ranks either side of the horizon to read the floor's error bar across. Sized to the scale
# of miss a real draft produces: a positional run moves consumption by roughly this much, so
# it asks "if this room drafts this position a little harder or softer than expected, how far
# does the floor actually move?" -- which is a question with a very different answer on a
# cliff than on a plateau.
HORIZON_SENSITIVITY_WINDOW = 6


def draftable_slots_per_team(roster_positions: list[str]) -> int:
    """How many roster slots a draft actually fills per team. TAXI counts (rookie picks land
    there); IR does not (nobody drafts onto injured reserve)."""
    return sum(1 for slot in roster_positions or [] if slot not in HORIZON_UNDRAFTED_SLOTS)


def positional_bench_appetite(
    pool: pd.DataFrame, value_col: str, roster_positions: list[str], num_teams: int,
) -> dict[str, Optional[float]]:
    """Relative appetite for drafting DEPTH at each position, derived from that position's own
    value decay rather than from any belief about the position.

    The reasoning: a team benches a player because the drop from their starter to the next one
    available is worth owning. Where a position holds its value just past starter demand, its
    backup is nearly free later and stocking one buys little; where it falls away sharply, the
    backup is worth a pick. So appetite tracks how much value is LOST across the tier past
    starter demand -- (1 - retention) -- not how much is retained.

    KNOWN WRONG AT THE TAIL, deliberately left in place. Checked against a real completed
    12-team superflex dynasty startup: ~52 QBs actually went; this says 80.6. It reads a cliff
    as depth-hunger, so superflex QB -- demand 22, QB44 holding 8.5% of QB22 -- scores the
    highest appetite of any position despite having maybe 35 draftable players.

    A replacement was tried and REVERTED: appetite as the share of a position's own total value
    sitting past starter demand. It fixed QB almost exactly (52.3 vs 52) and broke K and DEF,
    which it drove from ~15 and ~14 consumed to ~25 each, because a FLAT position necessarily
    holds a large share of its value past starter demand. Fitting one position's number while
    inverting two others is overfitting, and the existing tests caught it. Whatever replaces
    this has to satisfy both ends -- cliff positions and flat ones -- and that needs more than
    one draft to derive honestly.

    This is a PRIOR either way: expected_positional_consumption hands control to observed picks
    as soon as the draft produces any, which is what limits the damage in a live draft.
    A position whose loaded pool can't reach 2x starter demand has no decay to read. It does
    NOT get 0.0 -- that would assert "this position is never benched", which is a claim, not
    an absence, and it hands that position's bench picks to whichever positions happened to
    load deeper (measured: a 40-deep RB pool zeroed RB and drove TE's consumption to 66 of
    180 picks). Nor does it get a number read off the bottom of the short list, which is the
    original K/DST defect. It gets the mean rate of the positions that COULD be measured --
    "no evidence this one decays differently from average" -- the same missing-information
    rule time_horizon_adj follows for an absent multi-year outlook.
    """
    slot_counts = starter_slot_counts(roster_positions)
    demands, rates = {}, {}
    for position in FANTASY_POSITIONS:
        demand = round(num_teams * slot_counts.get(position, 0))
        demands[position] = demand
        if demand < 1:
            continue
        values = sorted(
            pool.loc[pool["position"] == position, value_col].dropna().astype(float),
            reverse=True,
        )
        if len(values) < 2 * demand or values[demand - 1] <= 0:
            continue  # unmeasurable here; filled in from the mean rate below
        rates[position] = max(0.0, 1.0 - values[2 * demand - 1] / values[demand - 1])

    # NOTHING measurable is a different state from "measurably flat", and the difference is
    # the whole point of the mean-rate fallback above. With rates empty there is no mean to
    # fall back TO, and the previous 0.0 default asserted "no position is ever benched" --
    # precisely the claim-not-an-absence this function's own reasoning rules out. It fires in
    # exactly the regime that matters: measured, from round 16 on one real 12x20 board and
    # round 18 on two more, no position has 2x its starter demand still on the board.
    if not rates:
        return {
            position: (0.0 if demands[position] < 1 else None)
            for position in FANTASY_POSITIONS
        }

    mean_rate = sum(rates.values()) / len(rates)
    return {
        position: demands[position] * rates.get(position, mean_rate) if demands[position] >= 1 else 0.0
        for position in FANTASY_POSITIONS
    }


def estimated_bench_demand(
    pool: pd.DataFrame, value_col: str, roster_positions: list[str], num_teams: int,
    picks: list[dict], players_db: dict[str, dict],
) -> dict[str, Optional[float]]:
    """How many further picks at each position are expected to go to BENCH spots -- the
    INFERRED half of remaining consumption, and the only half that rests on a claim about how
    rooms draft rather than on what the league's own roster_positions require.

    Bounded above by what the draft can still spend: remaining_draft_capacity minus the
    starting slots still owed (remaining_starter_demand), split across positions by
    positional_bench_appetite. Both bounds are exact and both reach zero, so this reaches zero
    too once rosters fill -- unlike the share-of-remaining-picks model it replaces, which was
    strictly positive for any position ever drafted and therefore could not express "this
    position is finished".

    None, position by position, when there is no bench-appetite evidence to split by. An
    unknown split is not a zero split, and it is not a confident one either; a consumer must
    render it as absence (see horizon_replacement, which stops claiming a floor).

    NEVER REACHES VALUATION. Nothing on the replacement_levels / VOR / bpa path reads this,
    by design and by test -- see the module docstring on why a behavioural prior is allowed to
    inform the debate layer and not the anchor.

    This replaces expected_positional_consumption, which fused this inferred quantity with the
    exact starter half into a single number that was neither exact nor honest about its
    uncertainty. Callers that want the total now add the two halves themselves, and can see
    which one is missing when one is."""
    starter = remaining_starter_demand(roster_positions, num_teams, picks, players_db)
    capacity = remaining_draft_capacity(roster_positions, num_teams, picks)
    bench_capacity = max(capacity - sum(starter.values()), 0.0)

    appetite = positional_bench_appetite(pool, value_col, roster_positions, num_teams)
    # A single unknown makes the SHARE undefined for every position, not just its own: shares
    # are normalised against the total, and a total with a hole in it cannot be normalised
    # against. Reporting the rest as though the split were known would be the same
    # manufactured confidence at one remove.
    if any(value is None for value in appetite.values()):
        return {position: None for position in FANTASY_POSITIONS}

    total = sum(appetite.values())
    if total <= 0:
        # Every position measurably holds its value past starter demand, so no position's
        # decay argues for stocking depth there. A real measured zero, not an absent one.
        return {position: 0.0 for position in FANTASY_POSITIONS}
    return {
        position: bench_capacity * appetite[position] / total
        for position in FANTASY_POSITIONS
    }


def horizon_replacement(
    pool: pd.DataFrame, value_col: str, roster_positions: list[str], num_teams: int,
    picks: Optional[list[dict]] = None, players_db: Optional[dict[str, dict]] = None,
) -> dict[str, dict]:
    """Per position, the best player expected to be STILL UNDRAFTED when the draft ends.

    {position: {"rank", "value", "pool_depth", "certain"}} against the CURRENT (undrafted)
    pool: if this position is expected to lose `n` more players, the best one left is the
    (n+1)th best still on the board.

    `value` is None and `certain` is False when the horizon rank falls past the end of the
    loaded pool, and equally when there is no bench-demand evidence to place the rank with. That case is reported as unknown rather than answered with the worst player
    we happen to have loaded -- the whole reason K/DST were mispriced for so long is that a
    truncated source's last row got treated as though it were a real replacement level, and
    a floor read off the bottom of a short list would rebuild that same defect one layer up.
    Callers must treat value=None as "no opinion", never as zero.

    `sensitivity` is the error bar the floor is worth stating with: how far the floor moves
    across +/-HORIZON_SENSITIVITY_WINDOW ranks around it. A point estimate is only as good as
    the curve it sits on, and positions do not share a curve -- measured on real data, +/-6
    ranks moves DEF by 12 points and QB by 63, because QB falls off a cliff a few ranks past
    its horizon while DEF is flat all the way down. Consumption is exactly the quantity a
    positional run shifts by that much, so a floor sitting on a cliff edge is a far weaker
    claim than one sitting on a plateau, even though both are single numbers. Callers that
    render a floor should say so when sensitivity is large next to the quantity being claimed
    (see draft_board_ui._waiting_note).

    The flat positions this whole mechanism was built for are the ones it estimates best,
    which is not a coincidence: flatness is simultaneously what makes waiting cheap and what
    makes the cost of waiting precisely measurable.
    """
    picks = picks or []
    players_db = players_db or {}
    starter = remaining_starter_demand(roster_positions, num_teams, picks, players_db)
    bench = estimated_bench_demand(pool, value_col, roster_positions, num_teams, picks, players_db)

    out: dict[str, dict] = {}
    for position in FANTASY_POSITIONS:
        values = sorted(
            pool.loc[pool["position"] == position, value_col].dropna().astype(float),
            reverse=True,
        )
        # The exact half alone is a LOWER BOUND on how many more will go: those starting slots
        # have to be filled, and bench picks land on top of them. rank is reported from that
        # bound because it is real information, but a floor read off a lower bound would be a
        # point estimate resting on a number we do not have, so `value` is withheld and
        # `certain` says so. Absent bench evidence used to resolve to still_to_go = 0, rank 1
        # and certain=True -- "this position is finished, and here is a confident floor",
        # neither of which was earned.
        bench_here = bench.get(position)
        still_to_go = starter.get(position, 0.0) + (bench_here or 0.0)
        rank = int(round(still_to_go)) + 1
        certain = bench_here is not None and 1 <= rank <= len(values)
        sensitivity = None
        if certain and values:
            window = HORIZON_SENSITIVITY_WINDOW
            high = values[max(rank - window, 1) - 1]
            low = values[min(rank + window, len(values)) - 1]
            sensitivity = round(high - low, 2)
        out[position] = {
            "rank": rank,
            "value": values[rank - 1] if certain else None,
            "pool_depth": len(values),
            "certain": certain,
            "sensitivity": sensitivity,
        }
    return out


def _team_starters_filled(picks: list[dict], players_db: dict[str, dict], roster_id) -> dict[str, int]:
    """How many of THIS roster's picks so far landed at each fantasy position -- the raw
    count, not weighed against slot capacity yet (need_bonus does that separately).
    Bench-vs-starter isn't distinguishable mid-draft (nothing's been assigned to a lineup
    slot yet), so every pick counts toward "already have one of these" for need purposes.

    One roster's row out of team_filled_by_position -- the same census
    remaining_starter_demand sums over every team, deliberately not a second implementation
    of "what has this team taken"."""
    return dict(team_filled_by_position(picks, players_db).get(str(roster_id), {}))


def _team_roster_players(
    picks: list[dict], players_db: dict[str, dict], roster_id, merger: DataMerger,
) -> list[dict]:
    """This roster's own drafted players as lineup_optimizer rows ({"id","value","eligible"})
    -- what eligibility_bonus needs to solve "best lineup with/without this candidate" for a
    REAL roster, not a hypothetical one. Value here is Draft Sharks' own trade_value (already
    a 0-100, scarcity-adjusted scale -- see data_merger.py's merge_player docstring), not bpa/
    VOR: bpa only exists for the currently AVAILABLE pool this call is scoring, and a roster's
    already-drafted players aren't in it. trade_value is real source data this module already
    trusts elsewhere (the IDP fallback VOR path), not a new number invented for this purpose --
    and using it for both the roster and the pool candidate (see compute_draft_board) keeps
    the assignment problem's units consistent on both sides."""
    players = []
    for pick in picks:
        if str(pick.get("roster_id")) != str(roster_id):
            continue
        player_id = str(pick.get("player_id"))
        info = players_db.get(player_id)
        if not info:
            continue
        name = player_name(info, player_id)
        match = merger.merge_player(name, position=player_position(info), team=info.get("team"))
        value = match.get("trade_value")
        if value is None:
            # He is on the roster and he occupies a slot; we simply cannot PRICE him. Those
            # are different facts, and dropping him conflates them -- the lineup CONSTRAINT
            # goes out with the missing value, so eligibility_bonus solves against a roster
            # one player emptier than it really is.
            #
            # ATTEMPTED AND REVERTED: admitting him at value 0.0. It reads like the right
            # separation -- no value claimed, slot still held -- and it does not work.
            # optimize_lineup maximises total value, so a zero-value player is always the
            # first benched and never holds a slot against contention, which is the only
            # regime where occupancy matters. Measured: a dual DL/LB candidate's
            # eligibility_bonus was 25.0 with him dropped and 25.0 with him at 0.0, and the
            # roster-only lineup value was 58.0 either way. Behaviourally identical to
            # dropping him, so it would have bought nothing but false confidence.
            #
            # Converting his projection into trade_value units is the other tempting repair
            # and is worse: that is precisely the scale contamination ELIGIBILITY_BONUS_MAX
            # exists to prevent (mean |bpa - trade_value| = 11.7, max divergence 63.0).
            #
            # A real repair has to model occupancy INDEPENDENTLY of value, which means
            # lineup_optimizer, not here. Two viable shapes, neither chosen yet:
            #   (a) pre-occupied slots -- remove the slot he holds from the assignment rather
            #       than adding him as a player. Expresses the constraint exactly and invents
            #       no value, but needs a rule for which slot a dual-eligible player holds.
            #   (b) decline to answer -- when the roster contains a player who cannot be
            #       priced, eligibility_bonus has no honest marginal to report, so return no
            #       opinion instead of a confidently wrong number. Matches the
            #       missing-information rule this engine follows everywhere else.
            #
            # Exposure if left as-is: 339 of 415 IDP rows in the baseline carry no trade
            # value, and IDP has no offline projections at all, so a live Sleeper feed sends
            # most of an IDP pool down this path. DL/LB dual listings are graded on the same
            # rubric, so flexibility is the ONLY thing that dual listing conveys -- and it is
            # exactly what gets discarded. Pinned by ProjectionOnlyRosterVisibilityTests.
            continue
        players.append({"id": player_id, "value": float(value), "eligible": player_eligible_positions(info)})
    return players


def _confidence(bpa_source: str) -> float:
    """0-100: how much to trust this player's value, separate from the value itself -- a
    direct encoding of which anchor actually produced bpa (see CONFIDENCE_BY_SOURCE and the
    module docstring on why this no longer calls composite_player_score)."""
    return CONFIDENCE_BY_SOURCE.get(bpa_source, 35.0)


def upside_score(row: pd.Series) -> dict:
    """Late-round scoring: growth trajectory (Draft Sharks' own proj_3yr outlook exceeding
    this season's, a number Draft Sharks already computes -- not an invented one) is the
    value driver. Cross-source disagreement is surfaced as confidence, a SEPARATE number,
    not added to the score -- an earlier version of this module added raw variance directly
    to the upside score, which rewards "we don't know" exactly as if it were "this player
    has tremendous upside." Those are different claims; only growth trajectory backs the
    second one. Deliberately does NOT use floor/ceiling data -- this app's Dynasty Rankings
    baseline has no such column (only Free Agent Finder does, which doesn't cover a full
    draft pool) -- see module docstring for why this proxy was chosen instead."""
    bpa = row.get("bpa") or 0.0
    growth = 0.0
    season_pct = row.get("_season_proj_pct")
    proj3yr_pct = row.get("_proj3yr_pct")
    # _has_3yr, exactly as time_horizon_adj gates on it -- the two are the only readers of
    # this percentile pair and they must agree on what an absent 3yr outlook means. Without
    # it, a row with real points and no proj_3yr keeps the neutral 50.0 default on the 3yr
    # side while the season side is a real (and, for such a row, usually LOW) percentile, so
    # this subtraction returns 50 - season_pct: a growth signal manufactured entirely out of
    # the missing half, and one that is LARGEST for the worst-projected player.
    #
    # Measured on a real 20-round board before this guard: mean growth 24.22 for K and 20.11
    # for DEF -- neither of which has a 3yr outlook from any committed source -- against
    # 0.57-1.63 for every position that carries both numbers. Because bpa collapses to 0.00
    # board-wide once positional demand is exhausted (every position, not just offense),
    # growth becomes the SOLE ranking term at that point, and the artifact took over the
    # board outright: rounds 16 and 17 of a 12x20 draft went 100% K/DEF, and the 22-point
    # kicker sitting last in the remaining pool ranked first overall.
    #
    # time_horizon_adj already had this guard (see its own comment for the +6.5 average it
    # was measured to remove). This function reads the same two columns and did not, which
    # is the entire defect -- the trigger arrived when K and DST moved onto league-scored
    # Sleeper projections, which publish points but no multi-year outlook.
    if row.get("_has_3yr", False) and season_pct is not None and proj3yr_pct is not None:
        growth = max(0.0, proj3yr_pct - season_pct)
    value = round(bpa + UPSIDE_GROWTH_WEIGHT * growth, 2)
    return {"final_score": value, "growth_signal": round(growth, 1), "confidence": _confidence(row.get("bpa_source"))}


def _scale_vor_to_bpa(vor: pd.Series) -> pd.Series:
    """Linear scaling against the single largest VOR gap in the pool -- the fix for
    percentile-ranking the anchor (see module docstring's ARCHITECTURE section). A player
    below replacement level (negative VOR) clips to 0, not a negative score: they'd make a
    roster worse than not drafting anyone there, which the rest of this module's additive,
    0-100-scale adjustments aren't built to represent as a further negative swing.

    A player with NO VOR AT ALL (NaN -- his position has no starter-demand replacement level,
    see replacement_levels' domain) keeps NaN here. That is a different statement from "his
    VOR is at or below replacement", and collapsing the two is what let an absent anchor read
    as a confident zero. The early return below used to hand 0.0 to every row including those,
    which is the one path where absence was destroyed rather than merely clipped."""
    measurable = vor.dropna()
    reference = measurable.max() if not measurable.empty else None
    if reference is None or pd.isna(reference) or reference <= 0:
        return vor.where(vor.isna(), 0.0)
    return (vor / reference * 100).clip(lower=0, upper=100)


def _records_with_normalized_nan(df: pd.DataFrame, *columns: str) -> list[dict]:
    """.to_dict("records") with the named columns' NaN normalized to real None -- pandas
    leaves a missing float as NaN (a non-None float, `nan is not None`), not the "missing"
    convention every consumer of this board (pick_synthesis.py, the Draft Room UI) actually
    expects. Fixed here, once, at the source, rather than every downstream caller re-guarding
    against NaN on its own."""
    records = df.to_dict("records")
    for record in records:
        for column in columns:
            if pd.isna(record.get(column)):
                record[column] = None
    return records


def _attach_waiting_cost(
    scored: pd.DataFrame, pool: pd.DataFrame, roster_positions: list[str], num_teams: int,
    picks: list[dict], players_db: dict[str, dict],
) -> None:
    """Attach horizon_floor and waiting_cost to a scored board, in place.

    waiting_cost = this player's own projected points MINUS the points of the best player at
    his position expected to still be undrafted when the draft ends (see horizon_replacement).
    It answers "what does deferring this position actually cost me", in season points, on the
    same footing for every position.

    OBSERVABLE ONLY. Nothing here feeds universal_value, team_acquisition_value, bpa, or
    necessity -- team_acquisition_value is computed and rounded before this runs and is
    byte-identical with these columns present or absent. That separation is deliberate: the
    raw quantity gets to be measured and argued with before it is allowed to move a decision.

    None (not zero) when horizon_replacement has no confident floor for that position. A
    position whose loaded pool ends before the horizon has an UNKNOWN waiting cost, and zero
    would read as "waiting is free" -- the most dangerous possible wrong answer here.
    """
    horizon = horizon_replacement(pool, "_points", roster_positions, num_teams, picks, players_db)
    floors = {position: data["value"] for position, data in horizon.items()}
    scored["horizon_floor"] = scored["position"].map(floors)
    scored["horizon_sensitivity"] = scored["position"].map(
        {position: data["sensitivity"] for position, data in horizon.items()}
    )
    scored["waiting_cost"] = (
        scored["projected_points"].astype(float) - scored["horizon_floor"].astype(float)
    ).round(2)


def compute_draft_board(
    merger: DataMerger,
    players_db: dict[str, dict],
    picks: list[dict],
    my_roster_id,
    league: dict,
    *,
    mode: str = "auto",
    upside_round: int = UPSIDE_MODE_DEFAULT_ROUND,
    sleeper_projections: Optional[dict[str, dict]] = None,
    pool_scope: str = "all",
    demand_picks: Optional[list[dict]] = None,
) -> list[dict]:
    """The live recommendation board: every undrafted, Draft-Sharks-valued player, ranked
    best pick first, with every scoring layer broken out separately -- universal_value
    (what any manager at this draft would compute), need_bonus and eligibility_bonus (the two
    team-specific terms), the final team_acquisition_value used to rank, and confidence (never
    folded into either value). See module docstring for why value is split into two numbers
    instead of one. projected_points is the raw season point projection universal_value's own
    VOR anchor is built from (see ARCHITECTURE section) -- exposed directly, independent of the
    scarcity-adjusted score, since "who's simply projected to score the most" is a real,
    separate question a manager may want to weigh on its own terms, not something that should
    only ever be visible after replacement-level math has already been applied to it. None
    when no real points source exists for that player (the trade_value-fallback case) -- never
    fabricated. mode: "auto" switches to upside scoring once the current round reaches
    upside_round, "balanced" or "upside" force one or the other regardless of round (the
    toggle this was built for -- see app.py's Draft Room view). pool_scope: "all" (default),
    "rookies_only" (the annual rookie draft), or "veterans_only" -- see
    build_available_pool's docstring; who counts as a rookie is detected from KeepTradeCut's

    demand_picks: an OPTIONAL separate pick history for replacement_levels' remaining-demand
    accounting (drafted_counts) and upside-mode round detection -- everything else (pool
    filtering via `picks`, and need_bonus/eligibility_bonus via my_filled/my_roster_players,
    both still read from `picks`) is unaffected. None (the default) reuses `picks` for this
    too, identical to every caller's behavior before this parameter existed.

    Exists specifically for a rookie draft run against a team's REAL pre-existing roster: pass
    the team's full history (veteran roster + rookie picks so far) as `picks`, so need_bonus/
    eligibility_bonus see the team's actual roster construction, but pass demand_picks scoped
    to ONLY the current rookie draft's own picks. Without this split, seeding `picks` with a
    real prior-season startup draft's full history collapses replacement_levels' remaining-
    demand model for whichever positions that EARLIER, separate draft phase happened to
    exhaust (WR/RB in a normal startup) while leaving a lightly-drafted position (QB in a 1QB
    league) with artificially high headroom -- confirmed directly: a backup-tier rookie QB
    outranked a legitimate rookie WR, and a real day-one rookie RB scored a negative
    universal_value, purely from this history-scope confusion, not from anything about the
    players themselves. replacement_levels' own remaining-demand math is correct FOR ONE
    CONTINUOUS DRAFT (see its own docstring); it was never built or validated for two separate
    draft phases sharing one drafted_counts tally, which is exactly the shape a real annual
    rookie draft run against a real veteran roster has.
    own source data, not a maintained list."""
    roster_positions = league.get("roster_positions") or []
    usable_positions = league_usable_positions(roster_positions)
    is_dynasty = (league.get("settings") or {}).get("type") == 2

    drafted_ids = {str(p.get("player_id")) for p in picks if p.get("player_id")}
    scoring_settings = league.get("scoring_settings")
    pool = build_available_pool(
        merger, players_db, drafted_ids, usable_positions,
        sleeper_projections=sleeper_projections, scoring_settings=scoring_settings,
        pool_scope=pool_scope,
    )
    if pool.empty:
        return []

    num_teams = league.get("total_rosters") or len({p.get("roster_id") for p in picks}) or 1
    demand_source = picks if demand_picks is None else demand_picks
    current_round = (max((p.get("round") or 1) for p in demand_source) if demand_source else 1)
    use_upside = mode == "upside" or (mode == "auto" and current_round >= upside_round)
    drafted_counts = _drafted_counts_by_position(demand_source, players_db)
    # The EXACT half, computed once per board and shared by both replacement anchors below.
    # Per-team, bounded, order-invariant, and able to reach exactly zero -- see
    # remaining_starter_demand. Nothing inferred is mixed in here.
    starter_demand = remaining_starter_demand(roster_positions, num_teams, demand_source, players_db)

    # bpa anchor -- see module docstring's ARCHITECTURE section in full for why this is VOR
    # in raw projected POINTS (never Draft Sharks' trade_value/composite scale directly),
    # scaled LINEARLY (never percentile-ranked) against the largest VOR gap actually present.
    #
    # Two real points sources, tried in order, both scored under THIS league's actual
    # scoring_settings rather than trusting either vendor's own pre-computed point total:
    #   1. Draft Sharks' own season projection (offense; already the app's trusted number).
    #   2. Sleeper's native weekly projection (covers IDP too), extrapolated to a rough
    #      season-equivalent -- see SLEEPER_WEEKLY_TO_SEASON_FACTOR's own docstring.
    # Only when NEITHER source has anything for a position does this fall back to a VOR
    # computed from trade_value instead of points -- using the exact same remaining-demand
    # replacement-rank logic, and folded into the SAME shared linear scale as the points-
    # anchored group below, not given its own separate range (see module docstring on why a
    # separate per-position range was the other half of the original IDP bug).
    pool["_points"] = pool["projection"].astype(float)
    pool["bpa_source"] = "points_vor_draftsharks"
    # Correct the default for rows whose "projection" didn't come from Draft Sharks at all --
    # see KDST_SEEDED_SOURCE_FILES for why this exists and what it does and doesn't affect
    # (a label and a confidence NUMBER, never bpa/universal_value/final_score).
    if "source_file" in pool.columns:
        pool.loc[pool["source_file"].isin(KDST_SEEDED_SOURCE_FILES), "bpa_source"] = "points_vor_sleeper_seeded"
    no_ds_proj = pool["_points"].isna()
    has_sleeper = pool["sleeper_points"].notna()
    use_sleeper = no_ds_proj & has_sleeper
    # Guarded rather than assigned unconditionally: when sleeper_points is entirely absent
    # (no live sync passed one in), use_sleeper is all-False and the right-hand side
    # collapses to an empty object-dtype Series, which pandas refuses to assign into an
    # existing float64 column even though there's nothing to assign -- a real pandas gotcha.
    if use_sleeper.any():
        pool.loc[use_sleeper, "_points"] = pool.loc[use_sleeper, "sleeper_points"] * SLEEPER_WEEKLY_TO_SEASON_FACTOR
        pool.loc[use_sleeper, "bpa_source"] = "points_vor_sleeper_extrapolated"

    has_proj = pool["_points"].notna()
    pool.loc[~has_proj, "bpa_source"] = "position_relative_trade_value_vor"

    # NaN, not 0.0: a row whose position has no starter-demand replacement level has no VOR,
    # and 0.0 would say "exactly at replacement" -- a claim, where there is an absence.
    pool["_vor"] = float("nan")
    pool["_season_proj_pct"] = 50.0
    pool["_proj3yr_pct"] = 50.0
    # Does this row carry a REAL multi-year outlook at all? time_horizon_adj is a DIFFERENCE
    # between two percentiles, and a "neutral" 50.0 standing in on one side of a difference is
    # not neutral -- against a genuinely low season percentile it reads as "this player's
    # future is far better than his present," manufacturing a growth signal from missing data.
    # (Measured: team defenses, whose season points sit far below offensive skill players,
    # picked up a spurious +6.5 average from exactly that.) Neutrality has to be expressed on
    # the ADJUSTMENT, not on one of its inputs -- see score_row.
    pool["_has_3yr"] = pool["proj_3yr"].notna()

    # Cliff-anchored QB replacement, superflex only (see qb_startable_floor/replacement_levels)
    # -- applied only to the points-anchored path: the startability threshold is in projected
    # points, so it means nothing against the trade_value fallback's different units.
    startable_floors = None
    if "SUPER_FLEX" in roster_positions:
        qb_floor = qb_startable_floor(merger)
        if qb_floor is not None:
            startable_floors = {"QB": qb_floor}

    if has_proj.any():
        proj_pool = pool[has_proj].copy()
        point_replacement = replacement_levels(
            proj_pool, "_points", roster_positions, num_teams, starter_demand,
            startable_floors=startable_floors,
        )
        pool.loc[has_proj, "_vor"] = proj_pool.apply(
            lambda r: (r["_points"] - point_replacement[r["position"]])
            if r["position"] in point_replacement else float("nan"),
            axis=1,
        ).values
        pool.loc[has_proj, "_season_proj_pct"] = _percentile_map(proj_pool["_points"]).values
        # Only rows that ACTUALLY carry a 3yr outlook get a real percentile here; everything
        # else keeps the neutral 50.0 default set above, which makes time_horizon_adj resolve
        # to ~0 (no opinion) rather than to a penalty.
        #
        # This previously fillna'd the missing values with the pool MINIMUM, which
        # percentile-maps to ~0 and therefore applied a systematic NEGATIVE time_horizon_adj
        # in dynasty leagues -- reading "we have no multi-year outlook for this player" as
        # "this player has a bad multi-year outlook." Those are different statements, and the
        # module's own rule everywhere else is that absent data must not be turned into a
        # fabricated signal. The 50.0 default a few lines above is already this module's
        # stated intent for an unknown outlook; the minimum-fill was the accident.
        #
        # Provably a no-op for every source committed at the time of this change: zero rows
        # in the real baseline carry a points projection WITHOUT a proj_3yr alongside it (see
        # test_missing_proj_3yr_is_neutral_not_a_penalty). It exists for sources that legitimately
        # have no multi-year dimension at all -- team defenses being the concrete case, since
        # Draft Sharks publishes DST only as a redraft table and a defense has no career arc
        # to project in the first place.
        has_3yr = proj_pool["proj_3yr"].notna()
        if has_3yr.any():
            pool.loc[proj_pool.index[has_3yr], "_proj3yr_pct"] = _percentile_map(
                proj_pool.loc[has_3yr, "proj_3yr"]
            ).values

    if (~has_proj).any():
        no_proj_pool = pool[~has_proj].copy()
        tv_replacement = replacement_levels(no_proj_pool, "trade_value", roster_positions, num_teams, starter_demand)
        pool.loc[~has_proj, "_vor"] = no_proj_pool.apply(
            lambda r: (r["trade_value"] - tv_replacement[r["position"]])
            if r["position"] in tv_replacement else float("nan"),
            axis=1,
        ).values

    # ONE shared linear scale across both groups -- the actual fix for the cross-positional
    # compression bug (see module docstring). A trade_value-based VOR is numerically much
    # smaller than a points-based one (different units), so sharing this reference means a
    # thin-demand IDP fallback correctly can't out-compete a well-projected offensive player
    # just because it locally looked like "the best of its own small group."
    pool["bpa"] = _scale_vor_to_bpa(pool["_vor"])

    if use_upside:
        scored = pool.join(pd.DataFrame(list(pool.apply(upside_score, axis=1))))
        scored["mode"] = "upside"
        scored["projected_points"] = scored["_points"]
        # universal_value is a ROLE, not a formula: "the team-agnostic value of this player,"
        # which is what every consumer outside this module reads it for (draft_strategy ranks
        # an opponent's remaining pool by it, draft_counterfactual takes its argmax as BPA,
        # roster_diagnostics passes the NAME of this column into replacement_levels,
        # pick_synthesis separates it from team_acquisition_value to detect context
        # elevation). In balanced mode that role is filled by bpa + time_horizon_adj +
        # risk_adj. In upside mode it is filled by final_score directly: upside_score reads
        # nothing off the roster -- it returns only {final_score, growth_signal, confidence}
        # from the row's own bpa and growth -- so there is no need_bonus or eligibility_bonus
        # separated out of it to subtract back off, and the layer identity
        # team_acquisition_value == universal_value + need_bonus + eligibility_bonus holds
        # with both bonuses at 0.0. It is deliberately NOT the same NUMBER as a balanced
        # board's universal_value for the same player, and must never be compared across
        # modes -- see this module's docstring on upside mode being a different valuation.
        #
        # Emitted here rather than defaulted at each read site because the two branches used
        # to return two different row schemas with nothing declaring that: five production
        # sites indexed row["universal_value"] unguarded, two guarded it inline with the same
        # reasoning duplicated, and the rest crashed. One owner of the shape is the fix; the
        # per-position decomposition terms (time_horizon_adj, risk_adj) stay absent because
        # upside_score genuinely never computes them and emitting 0.0 would fabricate them.
        scored["universal_value"] = scored["final_score"]
        _attach_waiting_cost(scored, pool, roster_positions, num_teams, demand_source, players_db)
        # kind="stable" + player_id as an explicit tiebreaker: without both, two players
        # landing on the exact same rounded final_score could rank in either relative order
        # depending on players_db's own dict iteration order (pool's own row order traces
        # straight back to that, via build_available_pool's `for player_id, info in
        # players_db.items()`) -- confirmed directly: reversing players_db's key order
        # reordered 37 of ~500 real-baseline rows, all of them exact final_score ties, before
        # this fix. player_id makes the tiebreak itself deterministic and independent of input
        # order; kind="stable" alone (pandas' default is unstable quicksort) only fixes
        # repeat-call determinism on a FIXED input order, not this. Never changes any
        # player's own computed values -- only which of several exactly-tied players a human
        # sees listed first.
        results = scored.sort_values(["final_score", "player_id"], ascending=[False, True], kind="stable")
        return _records_with_normalized_nan(results[[
            "player_id", "name", "position", "team", "injury_status", "bpa", "bpa_source",
            "growth_signal", "universal_value", "confidence", "final_score", "mode",
            "projected_points", "horizon_floor", "horizon_sensitivity", "waiting_cost",
        ]], "projected_points", "horizon_floor", "horizon_sensitivity", "waiting_cost",
            "bpa", "universal_value", "final_score")

    my_filled = _team_starters_filled(picks, players_db, my_roster_id)
    slot_counts = starter_slot_counts(roster_positions)
    dedicated_counts = dedicated_slot_counts(roster_positions)
    my_roster_players = _team_roster_players(picks, players_db, my_roster_id, merger)

    def score_row(row: pd.Series) -> pd.Series:
        position = row["position"]
        bpa = row["bpa"]

        time_horizon_adj = 0.0
        # No real multi-year outlook -> no opinion about the time horizon, which means an
        # adjustment of exactly zero rather than one computed against a stand-in percentile
        # (see _has_3yr above for the measured failure that guards against). A source with no
        # multi-year dimension at all -- Draft Sharks publishes DST only as a redraft table,
        # and a team defense has no career arc to project -- must neither be penalised for
        # the absence nor rewarded by it.
        if is_dynasty and row.get("_has_3yr", False):
            time_horizon_adj = min(max((row["_proj3yr_pct"] - row["_season_proj_pct"]) * TIME_HORIZON_SLOPE, TIME_HORIZON_CLAMP[0]), TIME_HORIZON_CLAMP[1])

        risk_adj = RISK_ADJ.get(row.get("injury_status"), 0.0)
        if is_dynasty:
            # Trajectory-aware scaling (experiment "D" -- see this constant's own docstring
            # above for the full evidence trail): a flat-or-declining trajectory
            # (time_horizon_adj <= 0) keeps the FULL flat penalty -- his value case is already
            # current-production-driven, so a health flag should hit at full strength, same as
            # it always has. Only a genuinely positive trajectory earns relief, scaled linearly
            # up to the floor at the +10 clamp -- never full forgiveness.
            if time_horizon_adj <= 0:
                d_scale = 1.0
            else:
                d_scale = 1.0 - (1.0 - DYNASTY_RISK_ADJ_MIN_SCALE) * (time_horizon_adj / TIME_HORIZON_CLAMP[1])
            risk_adj *= d_scale

        universal_value = round(bpa + time_horizon_adj + risk_adj, 2)

        # Need, split by urgency (see module docstring's need_bonus section for the bug this
        # replaced): an unfilled DEDICATED slot dominates; flex-only demand only counts once
        # dedicated slots are already covered, and contributes far less even then.
        filled = my_filled.get(position, 0)
        dedicated = dedicated_counts.get(position, 0)
        dedicated_needed = max(dedicated - filled, 0)
        flex_share = max(slot_counts.get(position, 0) - dedicated, 0)
        # Flex-eligible demand shrinks as picks beyond the dedicated slots consume it, not
        # just a binary "have I met dedicated yet" switch -- otherwise a small residual flex
        # share (e.g. two-thirds of a FLEX slot's worth) never actually reaches zero no
        # matter how many extra players at this position a team has already drafted.
        flex_already_used = max(filled - dedicated, 0)
        flex_remaining = max(flex_share - flex_already_used, 0)
        need_bonus = round(min(
            NEED_BONUS_PER_DEDICATED_SLOT * dedicated_needed + NEED_BONUS_PER_FLEX_SHARE * min(flex_remaining, 1),
            NEED_BONUS_MAX,
        ), 2)

        # The second (and only other) team-specific term -- what a real multi-position
        # optimal lineup, computed against THIS roster's actual players, says his flexibility
        # is worth beyond his raw value. Self-limiting rather than capped like need_bonus (see
        # eligibility_bonus's own docstring): it can never exceed his own trade_value, since
        # the best he can ever do is fill a genuinely open slot outright.
        #
        # A player admitted on a points projection alone carries no trade_value, and this
        # term is denominated in trade_value units -- so there is nothing to measure and the
        # honest answer is exactly 0.0, the same "missing information is not information"
        # rule time_horizon_adj follows for a missing 3yr outlook. Guarded here, where the
        # meaning of the absence is known, rather than inside the optimizer: passing the NaN
        # through reaches a Hungarian-algorithm cost matrix and raises outright ("matrix
        # contains invalid numeric entries"), and a value substituted down there would be a
        # fabricated flexibility premium rather than a declined one.
        candidate_value = row["trade_value"]
        if candidate_value is None or pd.isna(candidate_value):
            eligibility_bonus_value = 0.0
        else:
            eb = lo.eligibility_bonus(
                my_roster_players, candidate_id=row["player_id"], candidate_value=candidate_value,
                candidate_full_eligible=player_eligible_positions(players_db.get(str(row["player_id"])) or {}),
                candidate_primary_position=position, roster_positions=roster_positions,
            )
            # Converted from trade_value units into this sum's own bpa scale -- see
            # TRADE_VALUE_SCALE_MAX/ELIGIBILITY_BONUS_MAX above for the units defect this fixes
            # and the real-data evidence behind it. min() is a defensive guard for out-of-scale
            # source data, not the bounding mechanism (the rescale is already bounded by
            # construction).
            eligibility_bonus_value = min(
                round(eb["eligibility_bonus"] * (ELIGIBILITY_BONUS_MAX / TRADE_VALUE_SCALE_MAX), 2),
                ELIGIBILITY_BONUS_MAX,
            )

        team_acquisition_value = round(universal_value + need_bonus + eligibility_bonus_value, 2)

        return pd.Series({
            "time_horizon_adj": round(time_horizon_adj, 2),
            "risk_adj": risk_adj,
            "universal_value": universal_value,
            "need_bonus": need_bonus,
            "eligibility_bonus": eligibility_bonus_value,
            "final_score": team_acquisition_value,
        })

    scored = pool.join(pool.apply(score_row, axis=1))
    scored["confidence"] = pool["bpa_source"].map(_confidence)
    scored["mode"] = "balanced"
    scored["projected_points"] = pool["_points"]
    _attach_waiting_cost(scored, pool, roster_positions, num_teams, demand_source, players_db)
    # player_id tiebreaker + kind="stable" -- see the identical sort in the upside-mode branch
    # above for the full reasoning (input-order-independent tiebreaking among exact ties).
    results = scored.sort_values(["final_score", "player_id"], ascending=[False, True], kind="stable")
    return _records_with_normalized_nan(results[[
        "player_id", "name", "position", "team", "injury_status", "bpa", "bpa_source",
        "time_horizon_adj", "risk_adj", "universal_value",
        "need_bonus", "eligibility_bonus", "confidence", "final_score", "mode", "projected_points",
        "horizon_floor", "horizon_sensitivity", "waiting_cost",
    ]], "projected_points", "horizon_floor", "horizon_sensitivity", "waiting_cost",
        "bpa", "universal_value", "final_score")


# -- in-app Mock Draft sandbox (see app.py's Draft Room view) -------------------------------
#
# A practice draft entirely independent of any real Sleeper league/draft -- useful for
# rehearsing strategy under a chosen format before a real draft happens, or one that hasn't
# even been created on Sleeper's side yet. Reuses compute_draft_board/build_snapshot/
# debate_pick completely unchanged: a mock is just a synthetic league dict plus a plain
# picks list built up locally instead of pulled from Sleeper's API, and every deterministic
# module downstream never needed a real Sleeper league to begin with -- it always spoke in
# roster_positions/scoring_settings/picks, never in Sleeper-specific IDs or endpoints.

MOCK_SCORING_REC_VALUES = {"standard": 0.0, "half_ppr": 0.5, "ppr": 1.0}
# A common real-league TE-premium convention (extra points per TE reception on top of the
# base "rec" value above) -- a principled starting point, not empirically backtested, same
# honesty as every other unproven constant in this module.
MOCK_TE_PREMIUM_BONUS = 0.5
MOCK_BENCH_SLOTS = 6


def build_mock_league(*, teams: int, superflex: bool, scoring: str, te_premium: bool, dynasty: bool) -> dict:
    """A synthetic Sleeper-shaped league dict for the Mock Draft sandbox -- the exact same
    roster_positions/scoring_settings/settings shape compute_draft_board already expects from
    a real league, so nothing downstream (including narrow_candidates, pick_analysis, or
    debate_pick) needs a special case for "this isn't a real Sleeper league." scoring is one
    of MOCK_SCORING_REC_VALUES's keys ("standard"/"half_ppr"/"ppr"); an unrecognized value
    falls back to full PPR rather than silently scoring as standard."""
    starters = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"]
    if superflex:
        starters.append("SUPER_FLEX")
    roster_positions = starters + ["BN"] * MOCK_BENCH_SLOTS
    scoring_settings = {"rec": MOCK_SCORING_REC_VALUES.get(scoring, 1.0)}
    if te_premium:
        scoring_settings["bonus_rec_te"] = MOCK_TE_PREMIUM_BONUS
    return {
        "roster_positions": roster_positions,
        "scoring_settings": scoring_settings,
        "total_rosters": teams,
        "settings": {"type": 2 if dynasty else 0},
    }


def simulate_opponent_picks(
    picks: list[dict], pick_order: list, my_roster_id, num_teams: int,
    merger: DataMerger, players_db: dict[str, dict], league: dict, *, pool_scope: str = "all",
) -> list[dict]:
    """Auto-draft every pick between the current spot and the user's next turn (or the end of
    the draft) -- each one takes that roster's own top team_acquisition_value board pick, the
    same deterministic engine the user's own recommendation is built from, just pointed at
    whichever other roster is on the clock. Never mutates picks -- returns a new, extended
    list -- so the Mock Draft UI has a plain function to replay against after a Reset rather
    than something with hidden state of its own. Stops early (rather than raising) if the
    available pool ever comes up empty -- a very short mock with more rounds than rosterable
    players is a real, if unlikely, config a user could set up."""
    picks = list(picks)
    while True:
        idx = len(picks)
        if idx >= len(pick_order):
            break
        on_clock = str(pick_order[idx])
        if on_clock == str(my_roster_id):
            break
        board = compute_draft_board(merger, players_db, picks, on_clock, league, pool_scope=pool_scope)
        if not board:
            break
        picks.append({
            "pick_no": idx + 1, "round": idx // num_teams + 1, "roster_id": on_clock,
            "player_id": board[0]["player_id"],
        })
    return picks
