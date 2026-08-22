"""
Deterministic synthesis layer for "Debate My Pick" -- turns draft_room.py's board and
draft_strategy.py's survival/opportunity-cost/denial analysis into ONE frozen, fully
decomposed snapshot for the LLM debate layer (pick_debate.py) to reason over. Nothing in this
module asks an LLM anything; it exists specifically so the debate layer downstream never has
to compute or guess a single number -- see pick_debate.py's own module docstring for why that
boundary is a hard architectural requirement, not a style preference.

Five real signals this module adds that didn't exist anywhere in the engine before:

  * positional_cliff -- whether a real, computable bpa gap sits between this player and the
    next-best REMAINING player at his position, big enough that waiting risks a genuine tier
    drop rather than "a slightly worse player." Same gap-detection principle draft_room.py's
    own _scale_vor_to_bpa already relies on (comparing a real gap's SIZE, never a percentile
    rank) -- applied one level down, comparing this player's bpa to the very next player at his
    position against how big gaps typically run in that position's own remaining pool.

  * expected_value_of_waiting -- survival_probability x universal_value: the flip side of
    draft_strategy.py's own opportunity_cost (team_acquisition_value x (1 -
    survival_probability)). Exposed directly, in the same units as universal_value, so "what do
    I realistically keep if I wait" is a real, already-computed number the debate can point to
    rather than something a model has to derive on the fly.

  * position_run_detected -- whether this candidate's own position is the one currently
    "running" (draft_strategy.detect_positional_run's own real, observable signal from recent
    picks), computed once per snapshot and attached per candidate rather than left for the LLM
    debate layer to notice or re-derive on its own.

  * pick_necessity / necessity_label -- NOT another player-value score (universal_value and
    team_acquisition_value already answer "how good is he"). This answers a genuinely different
    question: "how badly do I need to make THIS selection right now, given what happens if I
    wait." 100 does not mean "best player" -- it means "there is effectively no reasonable
    alternative to taking him now." A worse player facing a real cliff and heavy competing
    demand can and should outscore a better player sitting in a deep, uncontested position.

    Built additively from real signals already in this snapshot, never a new invented number:
      - standout margin: how far this candidate's team_acquisition_value LEADS the best OTHER
        narrowed candidate, normalized against a fixed ABSOLUTE reference gap (see
        NECESSITY_STANDOUT_REFERENCE_GAP), not the observed field's own min/max range -- a real
        standout pushes this up; a tightly bunched field of several legitimate directions keeps
        every candidate near the neutral baseline. Floored at 0, not a symmetric penalty, when
        this candidate trails instead: "not the single best option right now" is neutral, not
        itself a reason to call a pick low-urgency -- the other signals below do that work.
        Without the floor, any two non-leaders more than one reference gap behind the leader
        collapsed to the identical maximum penalty regardless of how far behind each actually
        was. The sole candidate in a single-candidate snapshot gets full credit here (there is,
        literally, no alternative to compare against).
      - survival_probability: (1 - survival) scaled up -- the core "what do you lose by
        waiting" signal.
      - positional_cliff: HIGH/MEDIUM add real points; LOW adds none.
      - position_run_detected: a real, observed signal, not a guess.
      - rival_premium (NOT denial_value): how much more the best-positioned intervening rival's
        own roster makes this player worth to them than his team-agnostic universal_value --
        their need/eligibility premium, normalized against draft_room's own NEED_BONUS_MAX
        scale. Deliberately the p_take-FREE half of the denial signal: denial_value is
        (opponent value x take-probability), and that same take-probability already compounds
        into survival_probability above, so using denial_value here counted the identical
        underlying probability twice -- measured at r = +0.82 between the survival and denial
        components across simulated draft states before this was split. Probability enters
        necessity exactly once (survival); rival-gain magnitude exactly once (this term). The
        snapshot's denial_value field itself is unchanged -- as an expected-value number for
        the debate layer it is correctly defined as is.
      - need_bonus + eligibility_bonus (this roster's own fit) -- applied directly, the same
        additive-nudge treatment draft_room.py already gives these two terms.
      - round: late-round picks (round >= draft_room's own UPSIDE_MODE_DEFAULT_ROUND) get the
        WHOLE score rescaled proportionally into a low band (see LATE_ROUND_NECESSITY_CAP), not
        forced to one identical flat number -- deliberately NOT the same shape as the
        market_adj/IDP-percentile bug draft_room.py's own docstring documents (several unrelated
        players landing on an identical normalized score purely as a normalization artifact, not
        because they were actually equal). A late-round pick still keeps whatever real relative
        signal it has, just compressed toward "this barely matters" -- a materially more honest
        claim than "these are all identical," and it lets the engine genuinely say "take
        whichever of these you prefer" without pretending a profound decision exists where one
        doesn't.

    Two signals from the original ten-factor list are deliberately NOT separate additive terms,
    each for a specific, real reason rather than an oversight:
      - next-pick distance (intervening_picks) is already fully absorbed into
        survival_probability itself (survival_probability IS the calibrated function of
        intervening_picks and every opponent's own board) -- adding it again as its own term
        would double-count the identical underlying signal.
      - opportunity_cost is mathematically team_acquisition_value * (1 - survival_probability):
        normalizing it back out reduces to survival_probability alone, and using it
        UNnormalized would leak the candidate's own value magnitude into a score this module
        deliberately keeps value-orthogonal (a expensive player and a cheap one facing the
        identical survival risk should score the identical necessity contribution from that
        risk, not a bigger one for the pricier player).

  * consensus_reach -- how far this candidate's real-world MARKET CONSENSUS standing sits from
    where he's being taken right now, and whether that's a normal deviation or a real reach.
    Built from KeepTradeCut's own crowd-sourced dynasty rankings (already loaded elsewhere in
    this app -- see draft_room.py's _rookie_lookup for the same source used a different way):
    real rank + real tier, not this engine's own VOR math validating itself. This exists
    specifically to guard against the engine "fighting the market" -- recommending a player
    nobody drafts this early without a real, board-specific reason (a genuine survival/cliff/
    denial case), versus quietly assuming its own valuation should just override established
    consensus. Deliberately does NOT block or penalize a deviation -- it's informational
    evidence for the debate layer, not a hard rule (a justified reach is a normal, legitimate
    outcome; the point is making the debate account for it explicitly, not suppressing it).
    Uses KTC's own TIER boundaries to size how big a deviation is, not a raw rank-number gap --
    a tight cluster of similarly-valued players tolerates a big rank swing with no real
    justification needed, while crossing an actual tier line the market itself drew is a bigger
    deal regardless of the raw rank distance. IMPORTANT DISTINCTION worth stating plainly:
    KTC's rank/tier reflect dynasty TRADE-VALUE consensus, not literal startup-draft ADP --
    those correlate strongly for established players but are not the same measurement, so this
    is a real, sourced, useful PROXY for draft-position expectation, never presented as an
    actual ADP number. Only meaningful for superflex leagues right now: this app's committed
    baseline only carries KTC's superflex-format export, and using that data for a 1QB league
    would silently misrepresent 1QB market consensus with superflex-inflated QB values --
    returns None entirely for a 1QB league rather than use mismatched data.

narrow_candidates does the field-narrowing a live debate actually needs: never hand an LLM the
full 100+ player board -- only the top few genuinely live candidates (plus anything the user
has specifically flagged), so the debate argues about the decision, not about rediscovering
the whole remaining pool.

build_snapshot assembles all of the above into one frozen PickSnapshot (a real frozen
dataclass, not a mutable dict a later step could quietly edit), pulling universal_value/
need_bonus/eligibility_bonus straight from draft_room's own board rows and survival_
probability/opportunity_cost/denial_value from draft_strategy.pick_analysis -- each module
stays responsible for the numbers it already owns; this one only merges and packages them.

diff_snapshots computes the literal audit trail the user asked for: given a previous and a
current snapshot, the structured, per-component delta for every candidate present in both --
not prose describing what changed, real numbers per term (universal_value, need_bonus,
eligibility_bonus, survival_probability, opportunity_cost, denial_value, rank) so a UI or an
LLM can answer "why did this guy move from 8th to 3rd" by pointing at exactly which terms moved
and by how much.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import draft_room as dr
import draft_strategy as ds
from data_merger import DataMerger, name_key, normalize_name

DEFAULT_NARROW_COUNT = 5

# How much bigger this player's own gap to the next-best remaining player at his position has
# to be than that position's own TYPICAL adjacent gap (median, robust to one already-huge
# outlier skewing a mean) before it counts as a real cliff -- HIGH/MEDIUM/LOW, never a bare
# number the rest of this app would have to interpret itself. Principled starting points, not
# empirically backtested -- same honesty this app applies to every other unproven constant
# (see draft_room.py's and draft_strategy.py's own docstrings on this exact point).
CLIFF_HIGH_RATIO = 2.5
CLIFF_MEDIUM_RATIO = 1.5

# A position needs at least this many players still on the board for "typical gap" to mean
# anything -- below it, there's no real distribution to compare against.
CLIFF_MIN_POOL_SIZE = 3

# Pick necessity -- see the module docstring's full account of why each weight exists and why
# two of the originally-considered ten factors were deliberately folded rather than added as
# their own terms. All principled starting points, not empirically backtested -- same honesty
# this app applies to every other unproven constant.
NECESSITY_BASELINE = 50.0            # "close call" / multiple legitimate paths -- the floor
NECESSITY_STANDOUT_WEIGHT = 30.0     # normalized margin over the best OTHER narrowed candidate
# A team_acquisition_value gap of roughly this size counts as a genuine standout -- an ABSOLUTE
# reference (same idea as draft_room._scale_vor_to_bpa anchoring to a real gap size), not a
# relative one against the observed field's own min/max range. A relative anchor is a real trap
# here: in a small or tightly-bunched field, even a modest gap IS the field's entire range, which
# would stretch it to fill the whole +/-30 swing regardless of how big the gap actually is in real
# points -- confirmed directly: a 3-candidate field spanning only 1.0 point (100/99.5/99) drove the
# leader's standout component to the full 15.0 (half the weight) under a relative anchor, when a
# genuinely tiny 0.5-point edge should barely move the needle at all.
NECESSITY_STANDOUT_REFERENCE_GAP = 15.0
NECESSITY_SURVIVAL_WEIGHT = 20.0     # (1 - survival_probability) scaled up
NECESSITY_CLIFF_POINTS = {"HIGH": 12.0, "MEDIUM": 6.0, "LOW": 0.0}
NECESSITY_RUN_BONUS = 6.0
NECESSITY_DENIAL_WEIGHT = 10.0       # rival_premium normalized against draft_room.NEED_BONUS_MAX
NECESSITY_ROSTER_FIT_WEIGHT = 0.8    # applied directly to (need_bonus + eligibility_bonus)

LATE_ROUND_THRESHOLD = dr.UPSIDE_MODE_DEFAULT_ROUND  # same round draft_room switches to upside mode
LATE_ROUND_NECESSITY_CAP = 30.0

# Checked top-down; the first threshold this score meets or exceeds wins.
NECESSITY_LABEL_THRESHOLDS = [
    (98.0, "MUST TAKE"),
    (85.0, "STRONG ACTION"),
    (65.0, "PREFERRED"),
    (50.0, "CLOSE CALL"),
    (30.0, "LOW URGENCY"),
    (0.0, "DOESN'T MATTER MUCH"),
]


def _necessity_label(score: float) -> str:
    for threshold, label in NECESSITY_LABEL_THRESHOLDS:
        if score >= threshold:
            return label
    return NECESSITY_LABEL_THRESHOLDS[-1][1]


def compute_pick_necessity(raw_candidates: list[dict], round_num: int) -> list[tuple[float, str]]:
    """(pick_necessity, necessity_label) per candidate, in the same order as raw_candidates --
    see the module docstring for the full reasoning behind every term. Each entry in
    raw_candidates needs: team_acquisition_value, need_bonus, eligibility_bonus,
    survival_probability (or None), positional_cliff (dict or None), position_run_detected,
    rival_premium (or None/0)."""
    values = [c["team_acquisition_value"] for c in raw_candidates]

    results = []
    for i, c in enumerate(raw_candidates):
        others = [v for j, v in enumerate(values) if j != i]
        if not others:
            standout_component = NECESSITY_STANDOUT_WEIGHT  # no alternative exists at all
        else:
            margin = c["team_acquisition_value"] - max(others)
            normalized_margin = margin / NECESSITY_STANDOUT_REFERENCE_GAP
            # Floored at 0, not -1: "not the single best option on the board right now" is
            # neutral, not itself evidence of low urgency -- the other real signals below
            # (survival, cliff, run, denial, roster fit) are what should differentiate among
            # non-leaders. Confirmed live: a -1 floor let ANY two candidates more than one
            # reference gap behind the leader collapse to the identical -30 penalty regardless
            # of how far behind each actually was -- a real Superflex QB1 sitting ~40
            # acquisition points behind the board's best RB, and a clearly-worse TE sitting
            # ~60 points behind it, landed within a few necessity points of each other despite
            # being genuinely different picks. Uncapped on the positive side still: a true
            # standout is real signal and keeps rewarding proportionally up to the +1 cap.
            standout_component = max(0.0, min(1.0, normalized_margin)) * NECESSITY_STANDOUT_WEIGHT

        survival = c.get("survival_probability")
        survival_component = (1 - survival) * NECESSITY_SURVIVAL_WEIGHT if survival is not None else 0.0

        cliff = c.get("positional_cliff")
        cliff_component = NECESSITY_CLIFF_POINTS.get(cliff["tier"], 0.0) if cliff else 0.0

        run_component = NECESSITY_RUN_BONUS if c.get("position_run_detected") else 0.0

        # p_take-free by design -- see the module docstring's rival_premium bullet for why
        # the p_take-weighted denial_value double-counted survival's own probability here.
        rival_premium = c.get("rival_premium") or 0.0
        denial_component = (min(rival_premium / dr.NEED_BONUS_MAX, 1.0) * NECESSITY_DENIAL_WEIGHT) if rival_premium > 0 else 0.0

        roster_fit_component = (c.get("need_bonus", 0.0) + c.get("eligibility_bonus", 0.0)) * NECESSITY_ROSTER_FIT_WEIGHT

        raw_score = (
            NECESSITY_BASELINE + standout_component + survival_component
            + cliff_component + run_component + denial_component + roster_fit_component
        )
        raw_score = max(0.0, min(100.0, raw_score))

        if round_num >= LATE_ROUND_THRESHOLD:
            score = round(raw_score * (LATE_ROUND_NECESSITY_CAP / 100.0), 1)
        else:
            score = round(raw_score, 1)
        results.append((score, _necessity_label(score)))
    return results


# Reach labels by TIER GAP (candidate's own KTC tier minus whichever tier is normally occupied
# at the current overall pick) -- see consensus_reach's own docstring for why tier gap, not a
# raw rank-number gap, is the right unit here (a market-drawn tier boundary is a real signal;
# an arbitrary rank-count threshold isn't).
CONSENSUS_REACH_LABELS = {0: "WITHIN CONSENSUS BAND", 1: "MODEST REACH"}
CONSENSUS_REACH_LABEL_DEFAULT = "SIGNIFICANT REACH"


def _consensus_lookup(merger: DataMerger, is_superflex: bool) -> dict[tuple[str, str], dict]:
    """name_key -> {"rank", "tier", "value"} from KeepTradeCut's own crowd-sourced dynasty
    rankings -- real market consensus, never this engine's own VOR math. Real players only
    (KTC's export also lists draft PICKS as rows -- "2026 Early 1st" etc -- with no position,
    which this filters out entirely, not just ignores incidentally: those rows are also where
    essentially all of this fuzzy name_key scheme's real collisions with actual players turned
    up during testing). On a genuine name_key collision between two real players (a known,
    accepted limitation of the first-initial+last-name scheme, same exposure _rookie_lookup
    already has), keeps whichever entry has the BETTER (lower) rank -- the more prominent
    player is the more likely one actually being looked up.

    Empty entirely (not partial/mismatched data) unless is_superflex is True: this app's
    committed baseline only carries KTC's superflex-format export, and using superflex-inflated
    QB consensus for a 1QB league would silently misrepresent that league's real market."""
    if not is_superflex:
        return {}
    ev = merger.external_values
    if ev.empty:
        return {}
    ktc = ev[
        (ev["source_name"] == "keeptradecut") & ev["rank"].notna() & ev["position"].notna()
    ]
    if ktc.empty:
        return {}
    lookup: dict[tuple[str, str], dict] = {}
    for _, row in ktc.iterrows():
        key = row["_name_key"]
        entry = {"rank": row["rank"], "tier": row.get("tier"), "value": row.get("value")}
        if key not in lookup or row["rank"] < lookup[key]["rank"]:
            lookup[key] = entry
    return lookup


def consensus_reach(
    player_name: str, current_overall_pick: int, consensus_by_key: dict[tuple[str, str], dict],
) -> Optional[dict]:
    """{"consensus_rank", "consensus_tier", "tier_gap", "reach_label"} for this candidate, or
    None when he isn't in the loaded consensus data at all (a real player KTC doesn't cover --
    common for deep bench/practice-squad-tier players -- gets no reach signal rather than a
    guessed one). tier_gap is the candidate's own KTC tier MINUS whichever tier is normally
    occupied at current_overall_pick (found by nearest consensus rank to that pick number) --
    0 or negative (his tier is the same as or BETTER than what's normally happening here) means
    no reach at all; the bigger the positive gap, the more this pick deviates from what the
    market itself would consider a comparable-tier player at this spot. See module docstring
    for why this is a real, sourced PROXY for draft-position expectation (KTC's own rank/tier
    reflect trade-value consensus, not literal ADP) and why it's informational evidence for the
    debate layer, never a block or a penalty applied here."""
    if not consensus_by_key:
        return None
    key = name_key(normalize_name(player_name))
    candidate = consensus_by_key.get(key)
    if candidate is None or candidate.get("tier") is None:
        return None
    nearest = min(consensus_by_key.values(), key=lambda c: abs(c["rank"] - current_overall_pick))
    if nearest.get("tier") is None:
        return None
    tier_gap = max(int(candidate["tier"] - nearest["tier"]), 0)
    return {
        "consensus_rank": int(candidate["rank"]), "consensus_tier": int(candidate["tier"]),
        "tier_gap": tier_gap, "reach_label": CONSENSUS_REACH_LABELS.get(tier_gap, CONSENSUS_REACH_LABEL_DEFAULT),
    }


def _find_row(board: list[dict], player_id) -> Optional[dict]:
    target = str(player_id)
    return next((r for r in board if str(r["player_id"]) == target), None)


def detect_positional_cliff(board: list[dict], player_id) -> Optional[dict]:
    """{"tier": "HIGH"/"MEDIUM"/"LOW", "gap", "typical_gap"} -- how much of a real bpa drop-off
    sits between this player and the next-best remaining player at his own position, relative
    to how big gaps ordinarily run in that position's remaining pool. None when this player
    isn't on the board, is the last one left at his position (no next player to fall off to --
    "cliff" isn't a meaningful question there), or the position has fewer than
    CLIFF_MIN_POOL_SIZE players remaining (not enough of a distribution to call anything
    "typical")."""
    row = _find_row(board, player_id)
    if row is None:
        return None
    same_position = sorted(
        (r for r in board if r["position"] == row["position"]), key=lambda r: r["bpa"], reverse=True,
    )
    if len(same_position) < CLIFF_MIN_POOL_SIZE:
        return None
    idx = next((i for i, r in enumerate(same_position) if str(r["player_id"]) == str(player_id)), None)
    if idx is None or idx == len(same_position) - 1:
        return None

    gaps = [same_position[i]["bpa"] - same_position[i + 1]["bpa"] for i in range(len(same_position) - 1)]
    this_gap = gaps[idx]
    other_gaps = sorted(g for i, g in enumerate(gaps) if i != idx and g > 0)
    if not other_gaps:
        return {"tier": "HIGH" if this_gap > 0 else "LOW", "gap": round(this_gap, 2), "typical_gap": 0.0}

    # TRIMMED median: drop the largest ~10% of gaps first (only when the pool carries enough
    # gaps for a trim to mean anything). A position with a genuine structural cliff has that
    # cliff's own giant gaps sitting in this list, inflating the "typical" yardstick the
    # cliff's edges are then measured against -- confirmed directly on the real committed
    # baseline: QB's median adjacent gap was pulled up by the cliff zone's own 71/51/30-point
    # drops, so the last-startable-tier boundary gaps read LOW (ratio ~1.2x) in front of a
    # collapse. The cliff must not get to contaminate the yardstick that detects it.
    if len(other_gaps) >= 10:
        trim = max(1, round(len(other_gaps) * 0.1))
        other_gaps = other_gaps[:len(other_gaps) - trim]

    typical_gap = other_gaps[len(other_gaps) // 2]  # median
    ratio = this_gap / typical_gap if typical_gap > 0 else float("inf") if this_gap > 0 else 0.0
    tier = "HIGH" if ratio >= CLIFF_HIGH_RATIO else "MEDIUM" if ratio >= CLIFF_MEDIUM_RATIO else "LOW"
    return {"tier": tier, "gap": round(this_gap, 2), "typical_gap": round(typical_gap, 2)}


def expected_value_of_waiting(universal_value: float, survival_probability: Optional[float]) -> Optional[float]:
    """The flip side of draft_strategy.py's opportunity_cost -- what you'd expect to walk away
    with, in universal_value's own units, if you pass on this player now and gamble on him
    surviving to your next pick. None when survival_probability itself isn't known (no
    intervening-pick context available), same "don't fabricate a number" posture as everywhere
    else in this app rather than silently assuming certainty."""
    if survival_probability is None:
        return None
    return round(universal_value * survival_probability, 2)


def narrow_candidates(
    board: list[dict], top_n: int = DEFAULT_NARROW_COUNT, user_selected_player_id: Optional[str] = None,
) -> list[dict]:
    """The top top_n rows by team_acquisition_value (final_score, draft_room's own ranking),
    PLUS the single best remaining player at every position this board actually covers, plus
    the user's own explicitly-flagged player if there is one -- none of these three are
    optional, and the second one specifically closes a real blind spot, not a cosmetic
    addition.

    universal_value/team_acquisition_value answer "how good is this player," a rational,
    single-team VOR question -- they were never meant to reproduce real-world ADP, which
    reflects a competitive, MULTI-TEAM equilibrium (scarcity anxiety, denial-driven runs on a
    thin position, "I'll take a cliff-edge QB3 purely to deny a rival a good QB2") that a
    smooth VOR curve doesn't and structurally can't fully capture on its own. That equilibrium
    behavior is exactly what draft_strategy.pick_analysis's survival_probability/denial_value
    and this module's own pick_necessity ARE built to reason about -- but only for whichever
    candidates actually make it into this list. Before this fix, a position with real scarcity
    pressure (superflex's QB demand is the concrete case that surfaced this) could have its
    single best remaining player rank outside the raw top_n on value alone, and he would then
    NEVER be handed to the strategic layer at all -- not undervalued, literally invisible to
    it, so a real "grab him now before he's gone" case could never even be considered, let
    alone recommended. Always including the best-at-position player means the strategic layer
    gets a fair look at him regardless of where a pure VOR ranking places him; if he genuinely
    isn't urgent, pick_necessity says so honestly (a LOW/CLOSE-CALL score, not exclusion from
    the conversation entirely).

    The user_selected_player_id addition still exists on top of this for the same reason it
    always did: a live debate is never blind to a player the user is specifically considering
    (a dynasty stash, a personal favorite, a punt pick) just because the deterministic board
    doesn't currently rank him near the top OR at the top of his own position."""
    ranked = sorted(board, key=lambda r: r["final_score"], reverse=True)
    candidates = list(ranked[:top_n])
    included_ids = {r["player_id"] for r in candidates}

    for position in {r["position"] for r in board}:
        best_at_position = next((r for r in ranked if r["position"] == position), None)
        if best_at_position is not None and best_at_position["player_id"] not in included_ids:
            candidates.append(best_at_position)
            included_ids.add(best_at_position["player_id"])

    if user_selected_player_id is not None and str(user_selected_player_id) not in included_ids:
        extra = _find_row(board, user_selected_player_id)
        if extra is not None:
            candidates.append(extra)

    # Re-sorted after every addition above -- rank order has to stay meaningful (rank_delta
    # in diff_snapshots depends on it) even once best-at-position/user-flagged rows get
    # appended out of value order.
    candidates.sort(key=lambda r: r["final_score"], reverse=True)
    return candidates


@dataclass(frozen=True)
class CandidateSnapshot:
    """One candidate's full decomposition, frozen at the moment the snapshot was built -- every
    field here is a real number this app already computed, never something the LLM debate
    layer is allowed to substitute its own guess for (see pick_debate.py)."""
    player_id: str
    name: str
    position: str
    team: Optional[str]
    bpa: float
    bpa_source: str
    confidence: float
    universal_value: float
    need_bonus: float
    eligibility_bonus: float
    team_acquisition_value: float
    survival_probability: Optional[float]
    intervening_picks: Optional[int]
    opportunity_cost: Optional[float]
    expected_value_of_waiting: Optional[float]
    denial_value: Optional[float]
    denial_team: Optional[str]
    rival_premium: Optional[float]
    positional_cliff: Optional[dict]
    position_run_detected: bool
    pick_necessity: float
    necessity_label: str
    consensus_rank: Optional[int]
    consensus_tier: Optional[int]
    reach_label: Optional[str]
    projected_points: Optional[float]


@dataclass(frozen=True)
class PickSnapshot:
    """The full frozen state a single "Debate My Pick" run reasons over. candidates is a tuple,
    not a list -- genuine immutability, not just a convention, since this snapshot is meant to
    be handed to an LLM debate and then diffed against later, and a caller quietly mutating it
    mid-debate would silently break both."""
    pick_label: str
    round: int
    my_roster_id: str
    candidates: tuple
    user_selected_player_id: Optional[str] = None


def build_snapshot(
    merger: DataMerger,
    players_db: dict[str, dict],
    picks: list[dict],
    pick_order: list,
    current_index: int,
    my_roster_id,
    league: dict,
    *,
    pick_label: str,
    mode: str = "balanced",
    pool_scope: str = "all",
    top_n: int = DEFAULT_NARROW_COUNT,
    user_selected_player_id: Optional[str] = None,
) -> PickSnapshot:
    """Build one frozen PickSnapshot: compute the real board, narrow to the live candidates,
    layer on survival/opportunity-cost/denial (draft_strategy.pick_analysis) and positional
    cliff (this module), and package it all as one immutable object. mode defaults to
    "balanced" (not draft_room's own "auto") -- upside-mode scoring drops universal_value/
    need_bonus/eligibility_bonus entirely (see draft_room.compute_draft_board's own docstring),
    and this snapshot's whole shape depends on those fields existing."""
    board = dr.compute_draft_board(
        merger, players_db, picks, my_roster_id=my_roster_id, league=league, mode=mode, pool_scope=pool_scope,
    )
    narrowed = narrow_candidates(board, top_n=top_n, user_selected_player_id=user_selected_player_id)
    candidate_ids = [row["player_id"] for row in narrowed]
    # A real, observable signal straight from the picks already made (see
    # draft_strategy.detect_positional_run's own docstring) -- computed once and shared across
    # every candidate here, not re-derived or guessed at per candidate.
    run_position = ds.detect_positional_run(picks, players_db)

    analysis_by_id: dict[str, dict] = {}
    if candidate_ids:
        analysis = ds.pick_analysis(
            merger, players_db, picks, pick_order, current_index=current_index, my_roster_id=my_roster_id,
            league=league, candidate_player_ids=candidate_ids, mode=mode, pool_scope=pool_scope,
        )
        analysis_by_id = {str(a["player_id"]): a for a in analysis}

    # Real market-consensus data (KeepTradeCut), not this engine's own valuation -- see
    # consensus_reach's own docstring for why this only ever applies to a superflex league.
    is_superflex = "SUPER_FLEX" in (league.get("roster_positions") or [])
    consensus_by_key = _consensus_lookup(merger, is_superflex)
    current_overall_pick = current_index + 1

    # First pass: gather every real per-candidate number EXCEPT pick_necessity, which needs the
    # whole narrowed set as context (a standout only means something relative to the field) --
    # see compute_pick_necessity's own docstring.
    raw_candidates = []
    for row in narrowed:
        pid = str(row["player_id"])
        a = analysis_by_id.get(pid, {})
        survival = a.get("survival_probability")
        universal_value = row["universal_value"]
        reach = consensus_reach(row["name"], current_overall_pick, consensus_by_key)
        raw_candidates.append({
            "player_id": pid, "name": row["name"], "position": row["position"], "team": row.get("team"),
            "bpa": row["bpa"], "bpa_source": row["bpa_source"], "confidence": row["confidence"],
            "universal_value": universal_value, "need_bonus": row.get("need_bonus", 0.0),
            "eligibility_bonus": row.get("eligibility_bonus", 0.0), "team_acquisition_value": row["final_score"],
            "survival_probability": survival, "intervening_picks": a.get("intervening_picks"),
            "opportunity_cost": a.get("opportunity_cost"),
            "expected_value_of_waiting": expected_value_of_waiting(universal_value, survival),
            "denial_value": a.get("denial_value"), "denial_team": a.get("denial_team"),
            "rival_premium": a.get("rival_premium"),
            "positional_cliff": detect_positional_cliff(board, pid),
            "position_run_detected": (run_position is not None and row["position"] == run_position),
            "consensus_rank": reach["consensus_rank"] if reach else None,
            "consensus_tier": reach["consensus_tier"] if reach else None,
            "reach_label": reach["reach_label"] if reach else None,
            "projected_points": row.get("projected_points"),
        })

    round_num = (max((p.get("round") or 1) for p in picks) if picks else 1)
    necessity_by_candidate = compute_pick_necessity(raw_candidates, round_num)

    candidates = [
        CandidateSnapshot(**c, pick_necessity=necessity, necessity_label=label)
        for c, (necessity, label) in zip(raw_candidates, necessity_by_candidate)
    ]

    return PickSnapshot(
        pick_label=pick_label,
        round=round_num,
        my_roster_id=str(my_roster_id),
        candidates=tuple(candidates),
        user_selected_player_id=(str(user_selected_player_id) if user_selected_player_id is not None else None),
    )


_DIFF_FIELDS = (
    "universal_value", "need_bonus", "eligibility_bonus", "team_acquisition_value",
    "survival_probability", "opportunity_cost", "expected_value_of_waiting", "denial_value",
    "rival_premium", "pick_necessity",
)


def diff_snapshots(previous: PickSnapshot, current: PickSnapshot) -> list[dict]:
    """The literal audit trail: for every candidate present in BOTH snapshots, the real,
    structured per-component delta -- not a prose description of what changed. rank_delta is
    each candidate's position in team_acquisition_value order within each snapshot's own
    candidate list (1 = top candidate); a player moving from rank 8 to rank 3 shows up here as
    rank_delta=-5 alongside exactly which underlying terms moved and by how much, the concrete
    answer to "why did this guy move" rather than a re-derived guess.

    A candidate only in one of the two snapshots (newly appeared, or fell out of the narrowed
    top_n) is reported with entered=True/False rather than silently dropped -- that's real,
    reportable information too (see pick_debate.py's use of this for "what changed" framing)."""
    prev_by_id = {c.player_id: c for c in previous.candidates}
    prev_rank = {c.player_id: i + 1 for i, c in enumerate(previous.candidates)}
    curr_by_id = {c.player_id: c for c in current.candidates}
    curr_rank = {c.player_id: i + 1 for i, c in enumerate(current.candidates)}

    diffs = []
    for player_id in set(prev_by_id) | set(curr_by_id):
        prev_c = prev_by_id.get(player_id)
        curr_c = curr_by_id.get(player_id)
        if prev_c is None:
            diffs.append({"player_id": player_id, "name": curr_c.name, "entered": True, "rank": curr_rank[player_id]})
            continue
        if curr_c is None:
            diffs.append({"player_id": player_id, "name": prev_c.name, "entered": False, "rank": prev_rank[player_id]})
            continue
        deltas = {}
        for attr in _DIFF_FIELDS:
            prev_val, curr_val = getattr(prev_c, attr), getattr(curr_c, attr)
            if prev_val is None or curr_val is None:
                continue
            delta = round(curr_val - prev_val, 2)
            if delta != 0:
                deltas[attr] = delta
        rank_delta = curr_rank[player_id] - prev_rank[player_id]
        if deltas or rank_delta:
            diffs.append({
                "player_id": player_id, "name": curr_c.name, "entered": None,
                "rank_delta": rank_delta, "deltas": deltas,
            })
    return diffs
