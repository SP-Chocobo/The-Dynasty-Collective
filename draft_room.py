"""
Live draft pick recommendations -- a zero-LLM, deterministic valuation engine for an
in-progress Sleeper draft, modeled on (not a clone of) Draft Sharks' War Room "3D Value"
concept: a dynamic form of Value-Based Drafting that recalculates as the draft happens,
not a static pre-draft ranking.

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
    team_acquisition_value = universal_value + need_bonus

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

from data_merger import DataMerger, name_key, normalize_name
from player_universe import FLEX_SLOT_POSITIONS, FANTASY_POSITIONS, league_usable_positions, player_name, player_position, score_projection

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

# time_horizon_adj and risk_adj are both small, bounded, additive nudges on the same linear
# 0-100 BPA scale -- deliberately incapable of overriding a real VOR gap on their own (see
# module docstring's ARCHITECTURE section and test_draft_room.py's invariant tests).
TIME_HORIZON_SLOPE = 0.20         # applied, dynasty leagues only, to (3yr-proj percentile -
TIME_HORIZON_CLAMP = (-10.0, 10.0)  # season-proj percentile)

# Current-status discount, not a predictive injury-likelihood model -- see module docstring.
# Additive and one-directional: an injury can only ever subtract from universal_value, never
# add (a hard invariant -- see test_draft_room.py), so a thin-data variance side-effect can
# never turn a health flag into a value boost.
RISK_ADJ = {"IR": -18.0, "O": -10.0, "D": -5.0, "Q": -1.5}

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
    positional constant: a superflex league's SUPER_FLEX slots inflate QB's own count
    automatically, a 2-TE league's second TE slot inflates TE's, etc. -- no separate
    per-format branching needed, it falls out of actually reading this league's own
    roster_positions."""
    counts: dict[str, float] = {p: 0.0 for p in FANTASY_POSITIONS}
    for slot in roster_positions or []:
        if slot in FANTASY_POSITIONS:
            counts[slot] += 1.0
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
    that goes stale the moment a new class debuts."""
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


def replacement_levels(
    pool: pd.DataFrame, value_col: str, roster_positions: list[str], num_teams: int,
    drafted_counts: Optional[dict[str, int]] = None,
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

    Recomputed fresh every time this module is asked for a board, never cached across
    picks."""
    slot_counts = starter_slot_counts(roster_positions)
    drafted = drafted_counts or {}
    levels: dict[str, float] = {}
    for position in FANTASY_POSITIONS:
        at_pos = pool[pool["position"] == position].sort_values(value_col, ascending=False)
        if at_pos.empty:
            continue
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
) -> list[dict]:
    """The live recommendation board: every undrafted, Draft-Sharks-valued player, ranked
    best pick first, with every scoring layer broken out separately -- universal_value
    (what any manager at this draft would compute), need_bonus (the only team-specific
    term), the final team_acquisition_value used to rank, and confidence (never folded into
    either value). See module docstring for why value is split into two numbers instead of
    one. mode: "auto" switches to upside scoring once the current round reaches
    upside_round, "balanced" or "upside" force one or the other regardless of round (the
    toggle this was built for -- see app.py's Draft Room view). pool_scope: "all" (default),
    "rookies_only" (the annual rookie draft), or "veterans_only" -- see
    build_available_pool's docstring; who counts as a rookie is detected from KeepTradeCut's
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
    current_round = (max((p.get("round") or 1) for p in picks) if picks else 1)
    use_upside = mode == "upside" or (mode == "auto" and current_round >= upside_round)
    drafted_counts = _drafted_counts_by_position(picks, players_db)

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

    if has_proj.any():
        proj_pool = pool[has_proj].copy()
        point_replacement = replacement_levels(proj_pool, "_points", roster_positions, num_teams, drafted_counts)
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
        results = scored.sort_values("final_score", ascending=False)
        return results[[
            "player_id", "name", "position", "team", "injury_status", "bpa", "bpa_source",
            "growth_signal", "confidence", "final_score", "mode",
        ]].to_dict("records")

    my_filled = _team_starters_filled(picks, players_db, my_roster_id)
    slot_counts = starter_slot_counts(roster_positions)
    dedicated_counts = dedicated_slot_counts(roster_positions)

    def score_row(row: pd.Series) -> pd.Series:
        position = row["position"]
        bpa = row["bpa"]

        time_horizon_adj = 0.0
        if is_dynasty:
            time_horizon_adj = min(max((row["_proj3yr_pct"] - row["_season_proj_pct"]) * TIME_HORIZON_SLOPE, TIME_HORIZON_CLAMP[0]), TIME_HORIZON_CLAMP[1])

        risk_adj = RISK_ADJ.get(row.get("injury_status"), 0.0)

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

        team_acquisition_value = round(universal_value + need_bonus, 2)

        return pd.Series({
            "time_horizon_adj": round(time_horizon_adj, 2),
            "risk_adj": risk_adj,
            "universal_value": universal_value,
            "need_bonus": need_bonus,
            "final_score": team_acquisition_value,
        })

    scored = pool.join(pool.apply(score_row, axis=1))
    scored["confidence"] = pool["bpa_source"].map(_confidence)
    scored["mode"] = "balanced"
    results = scored.sort_values("final_score", ascending=False)
    return results[[
        "player_id", "name", "position", "team", "injury_status", "bpa", "bpa_source",
        "time_horizon_adj", "risk_adj", "universal_value",
        "need_bonus", "confidence", "final_score", "mode",
    ]].to_dict("records")
