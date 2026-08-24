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
module already scores correctly. Unlike need_bonus it is NOT capped -- it's a real marginal-
value number, self-limiting because a candidate can never contribute more than his own value
(the best case is unlocking a genuinely empty slot outright), not a heuristic nudge that needs
an artificial ceiling.

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

UPSIDE_GROWTH_WEIGHT = 0.5

# confidence is now a direct, cheap encoding of which anchor a row actually used -- see
# module docstring on why this replaced a composite-score cross-source-agreement lookup.
CONFIDENCE_BY_SOURCE = {
    "points_vor_draftsharks": 80.0,
    "points_vor_sleeper_extrapolated": 60.0,
    "position_relative_trade_value_vor": 35.0,
}


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
    position so far -- what replacement_levels needs to know REMAINING demand, not static
    league-wide demand (see module docstring's replacement-level section)."""
    counts: dict[str, int] = {}
    for pick in picks:
        info = players_db.get(str(pick.get("player_id")))
        if not info:
            continue
        position = player_position(info)
        if position:
            counts[position] = counts.get(position, 0) + 1
    return counts


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
    """One row per undrafted, fantasy-relevant player Draft Sharks actually has a value
    for -- joined from Sleeper's player_id-keyed database (drafts speak player_id, Draft
    Sharks speaks name) the same way player_universe.py already bridges the two elsewhere
    in this app. A player with no Draft Sharks match is dropped, not scored at 0 -- there's
    no honest BPA to rank them by, same "don't fabricate a number" rule as everywhere else.

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
        if not match.get("matched") or match.get("trade_value") is None:
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
        })
    if not rows:
        return pd.DataFrame(columns=[
            "player_id", "name", "position", "team", "injury_status", "trade_value",
            "projection", "proj_3yr", "sleeper_points", "bpa",
        ])
    return pd.DataFrame(rows)


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
    drafted_counts: Optional[dict[str, int]] = None,
    startable_floors: Optional[dict[str, float]] = None,
) -> dict[str, float]:
    """Per position, this pool's value_col at the player currently sitting at "replacement
    rank" within the REMAINING pool -- not the original full-field rank. The rank target is
    league-wide demand for this position (num_teams x its starter_slot_counts share) MINUS
    however many have already been drafted league-wide (drafted_counts) -- REMAINING demand,
    not static demand. That's what makes this genuinely dynamic in the right direction: drain
    a position past its real demand and the target collapses to 1 (replacement = the best
    player still on the board), correctly driving everyone left there toward ~0 VOR, instead
    of the target staying fixed and replacement level collapsing toward the bottom of an
    ever-thinning pool as an artifact of scarcity that no longer actually exists (a real bug
    the first pass had -- see module docstring). drafted_counts defaults to "nobody drafted
    yet" when omitted, which recovers the original static behavior for callers (this
    module's own unit tests) that only care about the pool-shape math in isolation, not a
    live draft's remaining-demand state.

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
    slot_counts = starter_slot_counts(roster_positions)
    drafted = drafted_counts or {}
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
            rank = max(int((at_pos[value_col] >= floor).sum()), 1)
        else:
            remaining_demand = max(num_teams * slot_counts.get(position, 0) - drafted.get(position, 0), 0)
            rank = max(1, round(remaining_demand))
        idx = min(rank - 1, len(at_pos) - 1)
        levels[position] = float(at_pos.iloc[idx][value_col])
    return levels


def _team_starters_filled(picks: list[dict], players_db: dict[str, dict], roster_id) -> dict[str, int]:
    """How many of THIS roster's picks so far landed at each fantasy position -- the raw
    count, not weighed against slot capacity yet (need_bonus does that separately).
    Bench-vs-starter isn't distinguishable mid-draft (nothing's been assigned to a lineup
    slot yet), so every pick counts toward "already have one of these" for need purposes."""
    filled: dict[str, int] = {}
    for pick in picks:
        if str(pick.get("roster_id")) != str(roster_id):
            continue
        info = players_db.get(str(pick.get("player_id")))
        if not info:
            continue
        position = player_position(info)
        if position:
            filled[position] = filled.get(position, 0) + 1
    return filled


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
    if season_pct is not None and proj3yr_pct is not None:
        growth = max(0.0, proj3yr_pct - season_pct)
    value = round(bpa + UPSIDE_GROWTH_WEIGHT * growth, 2)
    return {"final_score": value, "growth_signal": round(growth, 1), "confidence": _confidence(row.get("bpa_source"))}


def _scale_vor_to_bpa(vor: pd.Series) -> pd.Series:
    """Linear scaling against the single largest VOR gap in the pool -- the fix for
    percentile-ranking the anchor (see module docstring's ARCHITECTURE section). A player
    below replacement level (negative VOR) clips to 0, not a negative score: they'd make a
    roster worse than not drafting anyone there, which the rest of this module's additive,
    0-100-scale adjustments aren't built to represent as a further negative swing."""
    reference = vor.max()
    if reference is None or reference <= 0:
        return pd.Series(0.0, index=vor.index)
    return (vor / reference * 100).clip(lower=0, upper=100)


def _records_with_normalized_nan(df: pd.DataFrame, column: str) -> list[dict]:
    """.to_dict("records") with one column's NaN normalized to real None -- pandas leaves a
    missing float as NaN (a non-None float, `nan is not None`), not the "missing" convention
    every consumer of this board (pick_synthesis.py, the Draft Room UI) actually expects.
    Fixed here, once, at the source, rather than every downstream caller re-guarding against
    NaN on its own."""
    records = df.to_dict("records")
    for record in records:
        if pd.isna(record.get(column)):
            record[column] = None
    return records


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

    pool["_vor"] = 0.0
    pool["_season_proj_pct"] = 50.0
    pool["_proj3yr_pct"] = 50.0

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
            proj_pool, "_points", roster_positions, num_teams, drafted_counts,
            startable_floors=startable_floors,
        )
        pool.loc[has_proj, "_vor"] = proj_pool.apply(
            lambda r: r["_points"] - point_replacement.get(r["position"], r["_points"]), axis=1,
        ).values
        pool.loc[has_proj, "_season_proj_pct"] = _percentile_map(proj_pool["_points"]).values
        pool.loc[has_proj, "_proj3yr_pct"] = _percentile_map(
            proj_pool["proj_3yr"].fillna(proj_pool["proj_3yr"].min() if proj_pool["proj_3yr"].notna().any() else 0)
        ).values

    if (~has_proj).any():
        no_proj_pool = pool[~has_proj].copy()
        tv_replacement = replacement_levels(no_proj_pool, "trade_value", roster_positions, num_teams, drafted_counts)
        pool.loc[~has_proj, "_vor"] = no_proj_pool.apply(
            lambda r: r["trade_value"] - tv_replacement.get(r["position"], r["trade_value"]), axis=1,
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
            "growth_signal", "confidence", "final_score", "mode", "projected_points",
        ]], "projected_points")

    my_filled = _team_starters_filled(picks, players_db, my_roster_id)
    slot_counts = starter_slot_counts(roster_positions)
    dedicated_counts = dedicated_slot_counts(roster_positions)
    my_roster_players = _team_roster_players(picks, players_db, my_roster_id, merger)

    def score_row(row: pd.Series) -> pd.Series:
        position = row["position"]
        bpa = row["bpa"]

        time_horizon_adj = 0.0
        if is_dynasty:
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
        eb = lo.eligibility_bonus(
            my_roster_players, candidate_id=row["player_id"], candidate_value=row["trade_value"],
            candidate_full_eligible=player_eligible_positions(players_db.get(str(row["player_id"])) or {}),
            candidate_primary_position=position, roster_positions=roster_positions,
        )
        eligibility_bonus_value = eb["eligibility_bonus"]

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
    # player_id tiebreaker + kind="stable" -- see the identical sort in the upside-mode branch
    # above for the full reasoning (input-order-independent tiebreaking among exact ties).
    results = scored.sort_values(["final_score", "player_id"], ascending=[False, True], kind="stable")
    return _records_with_normalized_nan(results[[
        "player_id", "name", "position", "team", "injury_status", "bpa", "bpa_source",
        "time_horizon_adj", "risk_adj", "universal_value",
        "need_bonus", "eligibility_bonus", "confidence", "final_score", "mode", "projected_points",
    ]], "projected_points")


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
