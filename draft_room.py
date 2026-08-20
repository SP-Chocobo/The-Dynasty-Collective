"""
Live draft pick recommendations -- a zero-LLM, deterministic valuation engine for an
in-progress Sleeper draft, modeled on (not a clone of) Draft Sharks' War Room "3D Value"
concept: a dynamic form of Value-Based Drafting that recalculates as the draft happens,
not a static pre-draft ranking.

Deliberately has no LLM in its critical path -- a live draft has a pick clock (often
30s-2min), and a multi-role debate with live web search is nowhere near fast enough to be
the primary recommendation there. Everything here is pandas/dict math over data this app
already has (the composite score, Draft Sharks' own season/3yr projections, Sleeper's live
picks and roster settings), sub-second to compute. The existing Quant/Beat/Contrarian/
Moderator panel remains available for a genuine toss-up between finalists -- see app.py's
Draft Room view -- but it is never the default path for "who do I take right now."

ARCHITECTURE -- additive and layered, not multiplicative. An earlier version of this module
multiplied BPA x ScarcityMult x NeedMult x SeasonProjMult x DynastyMult x HealthMult
together. Reviewed and rejected: several of those factors partially describe the same
underlying "how much does this player help a lineup" question, so multiplying them stacks
correlated effects rather than combining independent ones, and a team's own need for a
position could inflate a mediocre player's score high enough to outrank an objectively
better one -- conflating "how good is this player" (comparable across every team watching
the draft) with "how good is this player FOR THIS ROSTER" (inherently team-specific) into
one irrecoverable number. Fixed by keeping two explicit numbers instead of one:

    universal_value = BPA + market_adj + time_horizon_adj + risk_adj
    team_acquisition_value = universal_value + need_bonus

BPA itself is Value Over Replacement computed in raw projected POINTS (Draft Sharks' own
season projection), not Draft Sharks' trade_value/composite scale -- confirmed directly
against real data that the latter doesn't work as a cross-positional anchor: Draft Sharks
caps IDP trade_value far below offense by design (a correct signal for DYNASTY TRADING
scarcity), and the app's OTHER composite sources don't cover elite IDP at all, so composite
degrades to that same capped solo number for a player like Myles Garrett or Maxx Crosby --
no bounded adjustment on top of a ~30-point ceiling could ever close a 70-point gap to an
average WR's trade_value. Points are a genuinely shared unit across every position, so VOR
computed from them (this player's projection minus their position's own replacement-level
projection, both from the REMAINING draft pool -- see replacement_levels) is fair to
percentile-rank across the whole board at once, unlike trade_value is. market_adj folds
trade_value/composite back in as a small, WITHIN-POSITION-normalized corroborating nudge
(does the community's read agree with the pure-stats VOR anchor?) rather than the anchor
itself, on the same reasoning.

universal_value is what every manager watching this draft would compute for this player --
league-wide replacement-level scarcity (baked into BPA itself), market corroboration,
season-vs-long-term trajectory, a health discount. need_bonus is the ONLY team-specific
term, added on top rather than multiplied in, and capped low enough that it can nudge a
close call but can never flip a large universal-value gap (see NEED_BONUS_MAX and
test_draft_room.py's invariant tests). Every adjustment term is small and additive on the
same 0-100 BPA scale, not a multiplier -- deliberately, so no single factor can swing the
result by blowing past the others in raw units the way a multiplier stacked against raw
projected points would (see composite_player_score's own percentile-not-raw-value reasoning
in data_merger.py for the same principle applied there first).

confidence is a SEPARATE number from value entirely -- how many sources actually weighed in
on this player and how much they agree. High disagreement or a thin data pool means "we
don't know," which is not the same claim as "this player has upside," and RiskAdj/
universal_value never treats it as such (that conflation was the exact upside-mode mistake
an earlier version of this module made -- see upside_score's docstring).

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

import statistics
from typing import Optional

import pandas as pd

from data_merger import DataMerger
from player_universe import FLEX_SLOT_POSITIONS, FANTASY_POSITIONS, league_usable_positions, player_name, player_position, score_projection

# Sleeper's projection endpoint is per-week, not season-long (see sleeper_client.py's
# get_weekly_projections) -- for positions Draft Sharks doesn't project at all (currently
# every IDP position, see build_available_pool's docstring), a single week's total is
# extrapolated to a rough season-equivalent by this factor purely so it lands on the same
# ORDER OF MAGNITUDE as Draft Sharks' real season projections for offense, which is what
# makes a shared cross-positional VOR percentile meaningful at all. This is a labeled
# approximation, not a real season projection (no bye week, no matchup variance, no
# injury-game-missed adjustment) -- it exists to fix "no real points data at all", not to
# be mistaken for Draft Sharks' own season, methodology.
SLEEPER_WEEKLY_TO_SEASON_FACTOR = 17

# Round at which the engine switches from the balanced formula to upside-only scoring,
# absent an explicit override -- matches the "War Room" idea this was modeled on. A deep
# bench/waiver-fringe pick is about finding a league-winning outlier, not filling a need or
# respecting positional scarcity that barely matters by then.
UPSIDE_MODE_DEFAULT_ROUND = 15

# universal_value's additive adjustment terms, each bounded well below a typical gap between
# two clearly-different-tier players on the 0-100 BPA scale, so no single term can reorder a
# real tier gap on its own -- only nudge within one.
MARKET_ADJ_SLOPE = 0.30           # applied to (within-position market percentile - BPA)
MARKET_ADJ_CLAMP = (-15.0, 15.0)
TIME_HORIZON_SLOPE = 0.20         # applied, dynasty leagues only, to (3yr-proj percentile -
TIME_HORIZON_CLAMP = (-10.0, 10.0)  # season-proj percentile)

# Current-status discount, not a predictive injury-likelihood model -- see module docstring.
# Additive and one-directional: an injury can only ever subtract from universal_value, never
# add (a hard invariant -- see test_draft_room.py), so a thin-data variance side-effect can
# never turn a health flag into a value boost.
RISK_ADJ = {"IR": -18.0, "O": -10.0, "D": -5.0, "Q": -1.5}

# The ONLY team-specific term. Added on top of universal_value, never multiplied into it, and
# capped low enough that it can tip a genuinely close call but can never manufacture enough
# points to flip a large universal-value gap -- see test_draft_room.py's invariant tests.
NEED_BONUS_PER_SLOT = 3.0
NEED_BONUS_MAX_SLOTS = 3
NEED_BONUS_MAX = NEED_BONUS_PER_SLOT * NEED_BONUS_MAX_SLOTS  # = 9.0

UPSIDE_GROWTH_WEIGHT = 0.5


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


def _percentile_map(values: pd.Series) -> pd.Series:
    """0-100 percentile within this exact Series, higher-is-better -- the same convention
    composite_player_score and data_merger._compute_percentiles use throughout, so every
    factor here stays comparable on the same scale (see module docstring)."""
    return values.rank(pct=True) * 100


def build_available_pool(
    merger: DataMerger,
    players_db: dict[str, dict],
    drafted_player_ids: set[str],
    usable_positions: set[str],
    sleeper_projections: Optional[dict[str, dict]] = None,
    scoring_settings: Optional[dict] = None,
) -> pd.DataFrame:
    """One row per undrafted, fantasy-relevant player Draft Sharks actually has a value
    for -- joined from Sleeper's player_id-keyed database (drafts speak player_id, Draft
    Sharks speaks name) the same way player_universe.py already bridges the two elsewhere
    in this app. A player with no Draft Sharks match is dropped, not scored at 0 -- there's
    no honest BPA to rank them by, same "don't fabricate a number" rule as everywhere else.

    sleeper_projections (player_id -> raw stat category -> projected value, from
    SleeperClient.get_weekly_projections) and scoring_settings (this league's real
    Sleeper scoring rules), when both given, are scored into sleeper_points via
    player_universe.score_projection -- NEVER a pre-computed point total handed over by an
    external site. That distinction matters here specifically: this app can then answer
    "this DB is projected for 7 sacks, and this league gives 8 points per sack" instead of
    blindly trusting someone else's number, which is what actually lets an unusual scoring
    rule (a big sack bonus, IDP tackle premiums, whatever this league's own settings say)
    change which players matter -- see compute_draft_board's docstring for where this feeds
    the VOR anchor for positions Draft Sharks doesn't project at all (currently IDP).
    """
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
        match = merger.merge_player(name, position=position, team=info.get("team"))
        if not match.get("matched") or match.get("trade_value") is None:
            continue
        composite = merger.composite_player_score(name, position=position, team=info.get("team"))
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
            "composite_score": composite.get("score") if composite else None,
            "composite_components": composite.get("components") if composite else None,
        })
    if not rows:
        return pd.DataFrame(columns=[
            "player_id", "name", "position", "team", "injury_status", "trade_value",
            "projection", "proj_3yr", "sleeper_points", "composite_score",
            "composite_components", "bpa",
        ])
    pool = pd.DataFrame(rows)
    return pool


def replacement_levels(pool: pd.DataFrame, value_col: str, roster_positions: list[str], num_teams: int) -> dict[str, float]:
    """Per position, this pool's value_col at the player currently sitting at "replacement
    rank" within the REMAINING pool -- not the original full-field rank. That's what makes
    this dynamic: as the top of a position gets drafted away, the player who'd now be the
    Nth-best left is a worse player than before, so replacement level actually drops and
    everyone still on the board at that position becomes more valuable relative to it. The
    rank itself comes from starter_slot_counts, which already reflects this exact league's
    real roster construction (SF, 2-TE, etc.), not a generic per-position constant.
    Recomputed fresh every time this module is asked for a board, never cached across
    picks."""
    slot_counts = starter_slot_counts(roster_positions)
    levels: dict[str, float] = {}
    for position in FANTASY_POSITIONS:
        at_pos = pool[pool["position"] == position].sort_values(value_col, ascending=False)
        if at_pos.empty:
            continue
        rank = max(1, round(num_teams * slot_counts.get(position, 0)))
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


def _confidence(row: pd.Series) -> float:
    """0-100: how much to trust this player's value, separate from the value itself. Built
    from real signal already collected for the composite score -- how many sources actually
    had an opinion (a lone-source read is inherently less certain than five sources
    agreeing) and how much they agree (cross-source spread) -- never folded into the value
    number itself. See module docstring on why conflating uncertainty with upside was
    rejected."""
    components = row.get("composite_components")
    if not components:
        return 40.0  # BPA fell back to Draft Sharks alone -- one source, no cross-check.
    pcts = [c["percentile"] for c in components if c.get("percentile") is not None]
    if len(pcts) <= 1:
        return 55.0
    agreement = max(0.0, 100.0 - 2.0 * statistics.pstdev(pcts))
    coverage = min(100.0, 40.0 + 15.0 * len(pcts))  # more corroborating sources, more trust
    return round((agreement + coverage) / 2, 1)


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
    return {"final_score": value, "growth_signal": round(growth, 1), "confidence": _confidence(row)}


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
) -> list[dict]:
    """The live recommendation board: every undrafted, Draft-Sharks-valued player, ranked
    best pick first, with every scoring layer broken out separately -- universal_value
    (what any manager at this draft would compute), need_bonus (the only team-specific
    term), the final team_acquisition_value used to rank, and confidence (never folded into
    either value). See module docstring for why value is split into two numbers instead of
    one. mode: "auto" switches to upside scoring once the current round reaches
    upside_round, "balanced" or "upside" force one or the other regardless of round (the
    toggle this was built for -- see app.py's Draft Room view)."""
    roster_positions = league.get("roster_positions") or []
    usable_positions = league_usable_positions(roster_positions)
    is_dynasty = (league.get("settings") or {}).get("type") == 2

    drafted_ids = {str(p.get("player_id")) for p in picks if p.get("player_id")}
    scoring_settings = league.get("scoring_settings")
    pool = build_available_pool(
        merger, players_db, drafted_ids, usable_positions,
        sleeper_projections=sleeper_projections, scoring_settings=scoring_settings,
    )
    if pool.empty:
        return []

    num_teams = league.get("total_rosters") or len({p.get("roster_id") for p in picks}) or 1
    current_round = (max((p.get("round") or 1) for p in picks) if picks else 1)
    use_upside = mode == "upside" or (mode == "auto" and current_round >= upside_round)

    # bpa anchor: Value Over Replacement in raw projected POINTS, not Draft Sharks' own
    # trade_value/composite scale. Points are a genuinely shared unit across every position;
    # trade_value is not -- confirmed directly (see draft_room.py's module docstring and the
    # real Myles Garrett/Maxx Crosby check that motivated this): Draft Sharks caps IDP
    # trade_value far below offense by design (a real, correct scarcity signal for DYNASTY
    # TRADING), and the other composite sources don't cover elite IDP at all, so composite
    # degrades to that same capped solo number. No bounded adjustment on top of a 25-30
    # ceiling could ever close a 70-point gap to an average WR's trade_value -- the anchor
    # itself has to be on a fair cross-positional scale, which points-based VOR actually is.
    #
    # But points-VOR needs real projected points to work from, and confirmed directly: Draft
    # Sharks' baseline currently has ZERO projection values for any IDP position (0/171 DL,
    # 0/91 LB, 0/153 DB) while offense is well-covered. Filling that with a pool-wide
    # fallback constant made every player at an unprojected position numerically identical --
    # caught live (a real bug, not graceful degradation): Myles Garrett, Maxx Crosby, and
    # every other IDP name in a test all landed on the exact same score.
    #
    # Two real points sources, tried in order, both scored under THIS league's actual
    # scoring_settings rather than trusting either vendor's own pre-computed point total:
    #   1. Draft Sharks' own season projection (offense; already the app's trusted number).
    #   2. Sleeper's native weekly projection (covers IDP too), extrapolated to a rough
    #      season-equivalent -- see SLEEPER_WEEKLY_TO_SEASON_FACTOR's own docstring for why
    #      this is a labeled approximation, not treated as equal in precision to #1.
    # Only when NEITHER source has anything for a position does this fall back to
    # trade_value's WITHIN-POSITION percentile -- real, differentiating data, just not on
    # the points-VOR scale. Flagged via bpa_source, never silently presented as equivalent.
    pool["_points"] = pool["projection"].astype(float)
    pool["bpa_source"] = "points_vor_draftsharks"
    no_ds_proj = pool["_points"].isna()
    has_sleeper = pool["sleeper_points"].notna()
    use_sleeper = no_ds_proj & has_sleeper
    # Guarded rather than assigning unconditionally: when sleeper_points is entirely absent
    # (no live sync passed one in -- the common case outside an actual draft), use_sleeper is
    # all-False and the right-hand side collapses to an empty object-dtype Series, which
    # pandas refuses to assign into an existing float64 column even though there's nothing to
    # assign -- a real pandas gotcha, not a meaningful "no rows" case worth its own branch.
    if use_sleeper.any():
        pool.loc[use_sleeper, "_points"] = pool.loc[use_sleeper, "sleeper_points"] * SLEEPER_WEEKLY_TO_SEASON_FACTOR
        pool.loc[use_sleeper, "bpa_source"] = "points_vor_sleeper_extrapolated"

    has_proj = pool["_points"].notna()
    pool.loc[~has_proj, "bpa_source"] = "position_relative_trade_value"

    pool["bpa"] = 0.0
    pool["_season_proj_pct"] = 50.0
    pool["_proj3yr_pct"] = 50.0

    if has_proj.any():
        proj_pool = pool[has_proj].copy()
        proj_pool["_projection_filled"] = proj_pool["_points"]
        point_replacement = replacement_levels(proj_pool, "_projection_filled", roster_positions, num_teams)
        proj_pool["_vor_points"] = proj_pool.apply(
            lambda r: r["_projection_filled"] - point_replacement.get(r["position"], r["_projection_filled"]), axis=1,
        )
        pool.loc[has_proj, "bpa"] = _percentile_map(proj_pool["_vor_points"]).values
        pool.loc[has_proj, "_season_proj_pct"] = _percentile_map(proj_pool["_projection_filled"]).values
        pool.loc[has_proj, "_proj3yr_pct"] = _percentile_map(
            proj_pool["proj_3yr"].fillna(proj_pool["proj_3yr"].min() if proj_pool["proj_3yr"].notna().any() else 0)
        ).values

    if (~has_proj).any():
        pool.loc[~has_proj, "bpa"] = pool.loc[~has_proj].groupby("position")["trade_value"].transform(lambda s: s.rank(pct=True) * 100)

    # Market read (composite/trade_value), also within-position so it can't reintroduce the
    # same cross-positional compression as a small corroborating nudge instead of the anchor.
    ds_pct_fallback = pool.groupby("position")["trade_value"].transform(lambda s: s.rank(pct=True) * 100)
    pool["_market_pct"] = pool["composite_score"].where(pool["composite_score"].notna(), ds_pct_fallback)
    pool["_market_pct"] = pool.groupby("position")["_market_pct"].transform(lambda s: s.rank(pct=True) * 100)

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

    def score_row(row: pd.Series) -> pd.Series:
        position = row["position"]
        bpa = row["bpa"]

        # Market corroboration: does the community's own (within-position) read agree with
        # the pure-stats VOR anchor? Bounded small -- this is a supporting signal (catches
        # role/opportunity context stats alone might miss), not a second scarcity term --
        # see module docstring on why stacking correlated scarcity signals was rejected.
        market_adj = min(max((row["_market_pct"] - bpa) * MARKET_ADJ_SLOPE, MARKET_ADJ_CLAMP[0]), MARKET_ADJ_CLAMP[1])

        time_horizon_adj = 0.0
        if is_dynasty:
            time_horizon_adj = min(max((row["_proj3yr_pct"] - row["_season_proj_pct"]) * TIME_HORIZON_SLOPE, TIME_HORIZON_CLAMP[0]), TIME_HORIZON_CLAMP[1])

        risk_adj = RISK_ADJ.get(row.get("injury_status"), 0.0)

        universal_value = round(bpa + market_adj + time_horizon_adj + risk_adj, 2)

        still_needed = max(slot_counts.get(position, 0) - my_filled.get(position, 0), 0)
        need_bonus = round(min(NEED_BONUS_PER_SLOT * still_needed, NEED_BONUS_MAX), 2)

        team_acquisition_value = round(universal_value + need_bonus, 2)

        return pd.Series({
            "market_adj": round(market_adj, 2),
            "time_horizon_adj": round(time_horizon_adj, 2),
            "risk_adj": risk_adj,
            "universal_value": universal_value,
            "need_bonus": need_bonus,
            "final_score": team_acquisition_value,
        })

    scored = pool.join(pool.apply(score_row, axis=1))
    scored["confidence"] = pool.apply(_confidence, axis=1)
    scored["mode"] = "balanced"
    results = scored.sort_values("final_score", ascending=False)
    return results[[
        "player_id", "name", "position", "team", "injury_status", "bpa", "bpa_source",
        "market_adj", "time_horizon_adj", "risk_adj", "universal_value",
        "need_bonus", "confidence", "final_score", "mode",
    ]].to_dict("records")
