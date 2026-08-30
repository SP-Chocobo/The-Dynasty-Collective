"""
Deterministic synthesis layer for "Debate My Pick" -- turns draft_room.py's board and
draft_strategy.py's survival/opportunity-cost/denial analysis into ONE frozen, fully
decomposed snapshot for the LLM debate layer (pick_debate.py) to reason over. Nothing in this
module asks an LLM anything; it exists specifically so the debate layer downstream never has
to compute or guess a single number -- see pick_debate.py's own module docstring for why that
boundary is a hard architectural requirement, not a style preference.

Together with draft_room.py, this module is the Contextual Decision Matrix Engine (CDME) --
see README.md's "The Draft Engine" section for the canonical definition. This is CDME's
contextual layer (necessity, positional cliff, survival/denial, decision_regime,
narrow_candidates); PickSnapshot below is CDME's frozen decision artifact, and its
candidates carry CDME's Decision Forces (near-tie, cliff protection, block opportunity,
pure value) as interpretable flags.

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
        the debate layer it is correctly defined as is. A moderate RESIDUAL correlation
        between the survival and rival-premium components (~0.6 measured across controlled
        backtest states) is an ACCEPTED property, not an oversight: the two formulas share no
        term, but both respond to the same real market fact (a genuinely in-demand player has
        lower survival AND higher rival value) through independent pathways -- shared cause,
        not shared measurement. Orthogonalizing further would mean residualizing one real
        signal against the other, making both less interpretable to remove a correlation that
        reflects reality.
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

# Position-view depth ceiling (see narrow_candidates' own docstring): the board's real,
# league-aware replacement rank per position (draft_room.replacement_ranks) is the right
# SOURCE for how much positional depth exists, but replacement rank alone can run to 30+ at
# a deep position in a real league -- far more than anyone wants displayed, and far more than
# draft_strategy.pick_analysis's per-candidate cost can absorb every rerun. This is a UI/
# compute ceiling on top of that real signal, not a valuation constant -- it never changes
# what a position's actual replacement demand is, only how much of it gets surfaced and fully
# analyzed at once. A thin position (real demand below this) is never artificially truncated;
# only a genuinely deep one gets capped.
POSITION_VIEW_DEPTH_CAP = 12


def _board_order(row: dict) -> tuple:
    """Sort key for a board row: highest final_score first, UNPRICED rows last, player_id as
    the tiebreak.

    Two things this deliberately does not do. It does not substitute a number for an absent
    score -- a row whose position has no replacement level has no team_acquisition_value, and
    treating that as 0.0 would rank it exactly where "worth nothing" ranks, which is a claim.
    And it does not decide what the board SHOULD do once nothing on it can be priced; that is
    an open product decision, and all this settles is that an unpriced row never outranks a
    priced one and that the resulting order is deterministic.

    The player_id tiebreak also closes a real determinism gap: sorting on final_score alone
    left rows with equal scores in whatever order the board happened to arrive in, and
    survived only on Python's sort being stable -- while draft_room's own board sort has
    carried an explicit player_id tiebreak for exactly this reason since the players_db
    iteration-order bug."""
    score = row.get("final_score")
    return (score is None, -score if score is not None else 0.0, str(row.get("player_id")))


def position_view_depth(replacement_rank: Optional[int]) -> int:
    """Position View Depth = min(this league's real replacement-rank demand for the position,
    POSITION_VIEW_DEPTH_CAP). A thin position (replacement_rank at or below the cap) is never
    truncated below its own real demand; a deep one is capped, not expanded, at the ceiling.
    Named and isolated specifically so the cap is one obvious, tunable constant rather than a
    number buried inside build_snapshot's own wiring.

    A position with no remaining starter demand (draft_room.replacement_ranks returns None,
    not a rank) shows its single best player. That is a DISPLAY decision made here, on purpose:
    once no starting slot is unfilled there is no starter-relevant depth to surface, and one
    row is the honest amount. It deliberately does not read as "demand is 1" -- the engine no
    longer has a rank to give, and this layer chooses what to show without inventing one."""
    if replacement_rank is None:
        return 1
    return min(replacement_rank, POSITION_VIEW_DEPTH_CAP)

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

# Credible-rival-path floor for the human-facing block_opportunity ("denies a rival") flag --
# the premium-driving rival's own real take_probability must clear this before the label
# fires. Same pre-declared bar (roughly rank-4-or-better under draft_strategy's own
# RANK_TAKE_PROBABILITY) used and validated in the denial-semantics audit / leave-one-force-
# out ablation experiment: filtering block_opportunity on this exact condition removed most
# of the flag's measured false-positive churn (candidates with no real rival path) while
# preserving the argmax flips that survive scrutiny, especially in superflex. Deliberately
# scoped to this ONE flag -- rival_premium's own continuous contribution to pick_necessity
# (NECESSITY_DENIAL_WEIGHT above) is untouched by this threshold; only the label a UI is
# allowed to display "DENIAL" for is gated.
CREDIBLE_RIVAL_PATH_THRESHOLD = 0.10

LATE_ROUND_THRESHOLD = dr.UPSIDE_MODE_DEFAULT_ROUND  # same round draft_room switches to upside mode
LATE_ROUND_NECESSITY_CAP = 30.0

# A team_acquisition_value gap at or below this is field noise, not ordering signal --
# DATA-DERIVED, not an invented percentage: on a real fresh 12-team superflex dynasty board,
# adjacent tav gaps in the top 40 ran median 1.23 / p75 2.26 / p90 3.53, so 2.0 sits right at
# the "most adjacent pairs are inside it" line (72% measured). Candidates this close to the
# LEADER form a tie group where the deterministic ordering must not be presented as a real
# preference -- this is exactly where the user's own player preference legitimately decides,
# and the debate layer needs the boundary handed to it as a computed number (an LLM inventing
# its own "feels close" threshold is precisely what this module's frozen-snapshot architecture
# exists to prevent). Distinct from NECESSITY_STANDOUT_REFERENCE_GAP (15.0), which measures a
# CUMULATIVE lead over the whole field -- that reference sits above the largest adjacent gap
# ever observed (10.6) on purpose, since full standout credit should demand something rare.
NEAR_TIE_BAND = 2.0

# A cliff is a RATIO ("this drop is unusually large for this position"), which silently
# assumes the position has enough dispersion for a ratio to mean anything. On a genuinely
# FLAT position it doesn't: as typical_gap collapses toward 0, an arbitrarily tiny drop
# divides out to an enormous ratio -- at exactly 0 the original code returned float("inf"),
# so EVERY positive gap became a HIGH cliff. Measured on the real Draft Sharks kicker
# projections (34 season points of spread across the whole ranked list, with several EXACT
# ties), that produced HIGH cliffs worth +12 necessity on gaps of ~7 season points -- 0.4
# points a WEEK, between two functionally interchangeable streamers -- on a player whose
# entire bpa was 19.7, so the phantom cliff was worth more than half his total board value.
# The ratio was never wrong; it was being asked a question it cannot answer without real
# dispersion to measure against.
#
# The tier is therefore gated on ABSOLUTE materiality as well as ratio: below this, an
# adjacent drop is not a cliff no matter how it compares to its neighbours. Deliberately
# derived from NEAR_TIE_BAND rather than independently invented -- that constant is already
# this module's own data-derived answer to "below this, an ordering difference is field
# noise rather than signal," which is exactly the judgement needed here. Kept under its own
# name because the two express genuinely different concepts (one bounds a tie GROUP measured
# against the leader, one bounds a single ADJACENT drop) and could legitimately diverge
# later -- same concept-representation discipline applied everywhere else in this engine.
#
# Validated against the three cases that actually matter: a genuine 35-point structural
# cliff still reports HIGH (35.0 >> 2.0); a spurious 0.1-point kicker cliff is suppressed;
# and -- the case a naive "flat position => never a cliff" guard would have silently broken
# -- a flat position carrying one real standout still reports HIGH (45.0 >> 2.0).
CLIFF_MIN_MATERIAL_GAP = NEAR_TIE_BAND

# The survival half of "this is basically decided" (see decision_regime): a principled
# starting point, not empirically backtested -- same honesty this app applies to every other
# unproven constant (CLIFF_HIGH_RATIO, NECESSITY_STANDOUT_REFERENCE_GAP itself, and others,
# were all introduced exactly this way and only later validated or revised against real data).
# Paired with NECESSITY_STANDOUT_REFERENCE_GAP as the margin half: a leader only reads as a
# clear, conviction-first standout when he is BOTH far ahead of the field AND unlikely to be
# there next turn regardless -- either alone (a big lead with real survival risk, or a
# marginal lead that's still probably safe) stays in the ordinary tiebreaker-prose regime.
DECISIVE_SURVIVAL_THRESHOLD = 0.15

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
        # The standout term asks how far ahead of the REST OF THE FIELD this candidate is.
        # Rows the board could not price are not part of that field and must not enter max():
        # they have no value to be ahead of or behind. A candidate who is himself unpriced has
        # no margin to compute, so his standout term is the neutral 0.0 -- and that is this
        # function's own existing rule, not a number substituted for absence. It already
        # assigns exactly 0.0 for an absent survival, an absent cliff and an absent rival
        # premium, and the comment below argues the standout floor is neutral rather than a
        # penalty. His survival, cliff and run components stay real evidence.
        others = [v for j, v in enumerate(values) if j != i and v is not None]
        mine = c["team_acquisition_value"]
        if mine is None:
            standout_component = 0.0
        elif not others:
            standout_component = NECESSITY_STANDOUT_WEIGHT  # no alternative exists at all
        else:
            margin = mine - max(others)
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
    QB consensus for a 1QB league would silently misrepresent that league's real market.

    CDME's ingestion trust boundary, made explicit: merger.external_values also carries
    bot_research.json's own LLM-originated findings (source_name == "bot_research", see
    data_merger.load_bot_research_as_external), sharing this same DataFrame. The
    source_name == "keeptradecut" filter below is what keeps that data out of consensus_reach
    -- proven, not just asserted, by test_cdme_ingestion_boundary.py's adversarial injection
    tests. Loosening this filter would reopen that boundary."""
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


def decision_path_flags(candidates: list[dict]) -> list[dict]:
    """Per candidate, the three deterministic decision-path booleans a downstream decision
    surface needs but must never invent thresholds for itself (the exact precedent
    NEAR_TIE_BAND set: an LLM or UI inventing its own "feels material" boundary is what the
    frozen-snapshot architecture exists to prevent). Every boundary here REUSES an existing,
    already-justified engine constant -- no new number was introduced for presentation's sake:

      cliff_protection -- positional_forfeit >= NECESSITY_STANDOUT_REFERENCE_GAP: delaying
        this candidate's position until the next pick forfeits at least a standout-sized
        value gap, the same absolute gap this module already treats as "a genuine standout"
        when it separates candidates.
      block_opportunity -- rival_premium >= 2 x NEED_BONUS_PER_DEDICATED_SLOT AND that same
        premium-driving rival's own take_probability clears CREDIBLE_RIVAL_PATH_THRESHOLD:
        at least one intervening rival values him at a MULTIPLE-unfilled-dedicated-starters
        premium over his universal value -- a rival with a genuinely gaping hole (the real
        observed case: a superflex rival with no QB1 at all), not routine need -- AND that
        specific rival has a credible real chance of actually taking him if we pass. One
        slot's worth (4.0) was measured first and rejected as a boundary: 73% of candidates
        across the M13 backtest states cleared it -- mid-draft, SOMEONE nearly always has a
        single-slot need for any good player, so the flag carried no information.
        NEED_BONUS_MAX (12.0) never fired at all (premiums top out near 8.7 in practice). Two
        slots' worth (8.0) fires for the top ~28% -- an actual opportunity signal. The
        credible-path condition was added second, after a real audit found premium magnitude
        ALONE still let block_opportunity fire on candidates whose premium-driving rival had
        no real path to the player (~1 in 5 flags, both trial formats) -- exactly the
        "labeled DENIAL when it was just a good pick" failure mode this flag exists to avoid.
        Filtering on the credible-path condition removed most of that churn while preserving
        the necessity-argmax flips that survive scrutiny (see run_denial_ablation_experiment.
        py's FILTERED condition, the exact boundary applied here). Distinct from denial_value
        (an expected-value number, take-probability included) and from rival_premium alone
        (which still flows into pick_necessity's continuous denial_component untouched by
        this threshold -- only this human-facing label is gated); this flags rival NEED with
        a credible PATH, deliberately, not need alone.
      pure_value -- this candidate holds the narrowed field's best universal_value while NOT
        being its team_acquisition_value leader, by a UV margin over the leader's UV
        exceeding NEAR_TIE_BAND (beyond measured ordering noise, same band, same scale):
        the board's best raw asset is being outranked by contextual terms -- real, worth
        surfacing explicitly so context never silently buries a materially better player.
      context_elevated -- this candidate's own (team_acquisition_value - universal_value)
        meets or exceeds NEED_BONUS_MAX: the maximum a single roster slot can ever contribute
        to acquisition value. Unlike pure_value (a cross-candidate comparison -- TAV can never
        fall below UV for any one candidate, since need_bonus/eligibility_bonus are both
        non-negative by construction, so "his own TAV dipping under his own UV" is structurally
        impossible), this is a real per-candidate quantity: a large, meaningful share of his
        rank here is roster fit, not raw talent. The two are the Context Gap signal's two
        directions -- pure_value is "buried despite excellent talent," context_elevated is
        "ranked highly substantially because of fit" -- and a UI is expected to surface them as
        one indicator with two readings, never as competing scores.

    Classification over existing numbers, never new scoring: nothing here feeds necessity,
    ranking, or any value -- same rule as near_tie_flags below. Expects each candidate dict
    to carry universal_value, team_acquisition_value, positional_forfeit, rival_premium,
    rival_premium_take_probability."""
    if not candidates:
        return []
    # Both cross-candidate comparisons below are over VALUES, so rows the board could not price
    # are excluded from them: an unpriced row cannot be the acquisition leader and cannot hold
    # the field's best universal_value, because it holds no value at all. With no priced
    # candidate there is no leader and no best to compare against, and every flag is a claim
    # this function then cannot support -- all four go False rather than being invented.
    priced = [i for i, c in enumerate(candidates)
              if c.get("team_acquisition_value") is not None
              and c.get("universal_value") is not None]
    if priced:
        tav_leader_idx = max(priced, key=lambda i: candidates[i]["team_acquisition_value"])
        leader_uv = candidates[tav_leader_idx]["universal_value"]
        best_uv = max(candidates[i]["universal_value"] for i in priced)
    else:
        tav_leader_idx, leader_uv, best_uv = None, None, None

    flags = []
    for i, c in enumerate(candidates):
        forfeit = c.get("positional_forfeit")
        premium = c.get("rival_premium") or 0.0
        take_prob = c.get("rival_premium_take_probability")
        credible_rival_path = take_prob is not None and take_prob >= CREDIBLE_RIVAL_PATH_THRESHOLD
        measurable = i in priced
        flags.append({
            # cliff_protection and block_opportunity read forfeit and rival_premium, which carry
            # their own absence handling and are not this row's own value -- unchanged.
            "cliff_protection": forfeit is not None and forfeit >= NECESSITY_STANDOUT_REFERENCE_GAP,
            "block_opportunity": premium >= 2 * dr.NEED_BONUS_PER_DEDICATED_SLOT and credible_rival_path,
            "pure_value": (
                measurable
                and i != tav_leader_idx
                and c["universal_value"] == best_uv
                and c["universal_value"] - leader_uv > NEAR_TIE_BAND
            ),
            "context_elevated": (
                measurable
                and (c["team_acquisition_value"] - c["universal_value"]) >= dr.NEED_BONUS_MAX
            ),
        })
    return flags


def decision_regime(candidates: list[dict]) -> str:
    """"decisive" or "contested" -- which register a decision surface's explanatory prose
    should use for the CURRENT leader, never a per-candidate flag (only the leader can be
    "the elite asset"; nobody else's situation determines whether this pick is genuinely
    close). Reads only margin-to-second-place and the leader's own survival_probability --
    deliberately NOT round number or pick label. A leader clearing both bars gets read as
    conviction-first regardless of whether that happens in round 1 or round 8; a bunched
    field in round 1 stays "contested." The two thresholds are independent, real signals:
    margin alone (a big lead that still might not survive) or survival alone (safe, but
    only marginally ahead of the next-best option) each leave real ambiguity a "just take
    him" framing would misrepresent -- only both together mean there is no actual decision
    left to explain, just a fact to state.

    "contested" (not "messy" or "close") on purpose: plenty of contested picks aren't
    messy at all (a real cliff, a real denial case) -- what makes the enumerated,
    tiebreaker-style prose the right register there isn't disorder, it's that a genuine
    ranking case still has to be made, unlike a decisive pick where making the case would
    be manufacturing a decision that doesn't exist. Returns "contested" for an empty or
    single-candidate list -- a lone or empty field has no SECOND place to measure a margin
    against, so "decisive" (a claim this module can actually support) is never assumed by
    default. Expects each candidate dict to carry team_acquisition_value and
    survival_probability, sorted or not -- this function does its own ranking."""
    # Unpriced candidates are excluded from the ranking rather than ordered into it: the regime
    # is decided by a MARGIN between the best and second-best measurable option, and a row with
    # no team_acquisition_value is neither. Once they are out, the function's own existing rule
    # for a field with fewer than two members applies unchanged -- a field with nothing to
    # measure a second place against is "contested", never "decisive".
    priced = [c for c in candidates if c.get("team_acquisition_value") is not None]
    if len(candidates) < 2 or len(priced) < 2:
        return "contested"
    ranked = sorted(priced, key=lambda c: c["team_acquisition_value"], reverse=True)
    leader, second = ranked[0], ranked[1]
    margin = leader["team_acquisition_value"] - second["team_acquisition_value"]
    survival = leader.get("survival_probability")
    if margin >= NECESSITY_STANDOUT_REFERENCE_GAP and survival is not None and survival <= DECISIVE_SURVIVAL_THRESHOLD:
        return "decisive"
    return "contested"
    return flags


def near_tie_flags(team_acquisition_values: list[float]) -> list[bool]:
    """Which candidates sit inside NEAR_TIE_BAND of the leader's team_acquisition_value --
    True for every member of the tie group INCLUDING the leader, but only when the group has
    at least two members: a leader nobody is close to isn't 'in a tie' with anyone, and
    flagging him alone would hand the debate layer a false 'these are tied' claim. Same order
    as the input.

    An UNPRICED entry (None) is never flagged and never becomes the leader. A row the board
    could not price has no measured separation from anything, so it is not "close to" the
    leader -- and letting it into max() either raised on the comparison or, worse, would have
    made every real row look far behind a leader that was not a value at all.
    """
    if not team_acquisition_values:
        return []
    priced = [v for v in team_acquisition_values if v is not None]
    if not priced:
        return [False] * len(team_acquisition_values)
    leader = max(priced)
    in_band = [v is not None and leader - v <= NEAR_TIE_BAND for v in team_acquisition_values]
    if sum(in_band) < 2:
        return [False] * len(team_acquisition_values)
    return in_band


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
    # A cliff is a drop measured in bpa against that position's own gap distribution, so rows
    # the board could not price are not in the distribution -- and if the target himself has no
    # bpa there is no drop of his to measure. Excluding them is the same rule the curve and the
    # near-tie band follow; sorting them in was a TypeError, not a mis-ranking.
    #
    # The early return is REDUNDANT GIVEN THE FILTER BELOW, and that is recorded rather than
    # left for someone to rediscover: an unpriced target is excluded from same_position, so
    # `idx` comes back None and the function returns None by that route anyway. Verified across
    # 112 unpriced rows on real rounds 16 and 18 -- none would reach the body without it. It is
    # kept because it states the intent at the top where a reader looks for it, but the FILTER
    # is what actually enforces the rule, so removing the filter is not made safe by this line.
    if row.get("bpa") is None:
        return None
    same_position = sorted(
        (r for r in board if r["position"] == row["position"] and r.get("bpa") is not None),
        key=lambda r: r["bpa"], reverse=True,
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
        # Every OTHER adjacent gap at this position is zero -- a perfectly tied field, where
        # there is no dispersion whatsoever to compare against. Same materiality gate as the
        # ratio path below: a real standout sitting above a tied block is still a genuine
        # cliff, but a hairline separation inside one is not.
        tier = "HIGH" if this_gap >= CLIFF_MIN_MATERIAL_GAP else "LOW"
        return {"tier": tier, "gap": round(this_gap, 2), "typical_gap": 0.0}

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
    # Absolute-materiality gate, applied BEFORE the ratio decides a tier -- see
    # CLIFF_MIN_MATERIAL_GAP for the measured failure this closes. A drop smaller than the
    # band this app already calls ordering noise cannot be a tier break, however unusual it
    # looks against an essentially flat position's own neighbours.
    if this_gap < CLIFF_MIN_MATERIAL_GAP:
        tier = "LOW"
    else:
        tier = "HIGH" if ratio >= CLIFF_HIGH_RATIO else "MEDIUM" if ratio >= CLIFF_MEDIUM_RATIO else "LOW"
    return {"tier": tier, "gap": round(this_gap, 2), "typical_gap": round(typical_gap, 2)}


def expected_value_of_waiting(universal_value: float, survival_probability: Optional[float]) -> Optional[float]:
    """The flip side of draft_strategy.py's opportunity_cost -- what you'd expect to walk away
    with, in universal_value's own units, if you pass on this player now and gamble on him
    surviving to your next pick. None when survival_probability itself isn't known (no
    intervening-pick context available), same "don't fabricate a number" posture as everywhere
    else in this app rather than silently assuming certainty."""
    if universal_value is None or survival_probability is None:
        return None
    return round(universal_value * survival_probability, 2)


def narrow_candidates(
    board: list[dict], top_n: int = DEFAULT_NARROW_COUNT, user_selected_player_id: Optional[str] = None,
    position_depth: Optional[dict[str, int]] = None,
) -> list[dict]:
    """The top top_n rows by team_acquisition_value (final_score, draft_room's own ranking),
    PLUS the best remaining players at every position this board actually covers, plus the
    user's own explicitly-flagged player if there is one -- none of these three are optional,
    and the second one specifically closes a real blind spot, not a cosmetic addition.

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
    alone recommended. Always including at least the best-at-position player means the
    strategic layer gets a fair look at him regardless of where a pure VOR ranking places him;
    if he genuinely isn't urgent, pick_necessity says so honestly (a LOW/CLOSE-CALL score, not
    exclusion from the conversation entirely).

    position_depth: optional {position: how many of that position's best remaining players to
    include}, keyed by the SAME "position" strings this board itself uses. None (the default)
    preserves this function's original behavior exactly -- exactly one (the single best) per
    position, nothing more. Passing a real per-league depth map (see
    draft_room.replacement_ranks, capped by app.py's own POSITION_VIEW_DEPTH_CAP before it
    ever reaches here) is what turns a UI position VIEW from "whichever of the top_n happened
    to be a WR" into an actually-useful WR board -- a position with real replacement demand
    gets real depth, a thin one still gets just its one best player, and every player included
    this way still goes through the exact same downstream necessity/survival/denial analysis
    as the original top_n slice, not a lesser "board-only" pass. This never changes any
    player's own bpa/universal_value/final_score -- those are already fixed on `board` before
    this function ever runs; it only changes which rows get selected for the heavier
    contextual analysis build_snapshot layers on afterward.

    The user_selected_player_id addition still exists on top of this for the same reason it
    always did: a live debate is never blind to a player the user is specifically considering
    (a dynasty stash, a personal favorite, a punt pick) just because the deterministic board
    doesn't currently rank him near the top OR at the top of his own position."""
    ranked = sorted(board, key=_board_order)
    candidates = list(ranked[:top_n])
    included_ids = {r["player_id"] for r in candidates}

    by_position: dict[str, list[dict]] = {}
    for row in ranked:
        by_position.setdefault(row["position"], []).append(row)

    for position, rows_at_position in by_position.items():
        depth = 1 if position_depth is None else max(1, position_depth.get(position, 1))
        for row in rows_at_position[:depth]:
            if row["player_id"] not in included_ids:
                candidates.append(row)
                included_ids.add(row["player_id"])

    if user_selected_player_id is not None and str(user_selected_player_id) not in included_ids:
        extra = _find_row(board, user_selected_player_id)
        if extra is not None:
            candidates.append(extra)

    # Re-sorted after every addition above -- rank order has to stay meaningful (rank_delta
    # in diff_snapshots depends on it) even once best-at-position/user-flagged rows get
    # appended out of value order.
    candidates.sort(key=_board_order)
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
    positional_forfeit: Optional[float]
    position_expected_taken: Optional[float]
    positional_cliff: Optional[dict]
    position_run_detected: bool
    pick_necessity: float
    necessity_label: str
    near_tie_with_leader: bool
    cliff_protection: bool
    block_opportunity: bool
    pure_value: bool
    context_elevated: bool
    consensus_rank: Optional[int]
    consensus_tier: Optional[int]
    reach_label: Optional[str]
    projected_points: Optional[float]
    # The premium-driving rival's own real take_probability -- see CREDIBLE_RIVAL_PATH_
    # THRESHOLD and decision_path_flags' block_opportunity, the one consumer. Defaulted so
    # existing hand-built CandidateSnapshot fixtures that predate this field still construct.
    rival_premium_take_probability: Optional[float] = None
    # What deferring this position actually costs: this player's projected points minus the
    # points of the best player at his position expected to be STILL UNDRAFTED when the draft
    # ends (draft_room.horizon_replacement). OBSERVABLE ONLY -- read by nothing that scores,
    # so team_acquisition_value above is byte-identical with or without it.
    #
    # None, never 0.0, when the loaded pool ends before the horizon: an unknown waiting cost
    # is not a free one, and zero would read as "wait, it's fine" at exactly the positions
    # whose data is thinnest. Consumers must render absence as absence.
    waiting_cost: Optional[float] = None
    horizon_floor: Optional[float] = None
    # How far that floor moves across a realistic miss in positional consumption. A point
    # estimate is only as good as the curve it sits on: +/-6 ranks moves DEF by 12 points and
    # QB by 63, because QB falls off a cliff just past its horizon. Consumers must not state
    # a waiting cost more confidently than this allows.
    horizon_sensitivity: Optional[float] = None


@dataclass(frozen=True)
class PickSnapshot:
    """The full frozen state a single "Debate My Pick" run reasons over. candidates is a tuple,
    not a list -- genuine immutability, not just a convention, since this snapshot is meant to
    be handed to an LLM debate and then diffed against later, and a caller quietly mutating it
    mid-debate would silently break both.

    picks_consumed / data_freshest_date are the snapshot's INPUT-STATE STAMP: which world this
    frozen state was computed from -- how many picks had been made, and the freshest source
    date of the data behind it. A frozen snapshot is only as valid as the inputs it froze; the
    stamp is what lets any later consumer (a debate still running, a UI panel held open, a
    stored decision log) cheaply ask "is this still the current state?" via snapshot_is_current
    instead of either trusting staleness blindly or rebuilding defensively on every
    interaction. Deliberately minimal: an identity check, not a change-magnitude model -- no
    invalidation daemon, no delta calculus, nothing recomputed. None on both means the
    snapshot predates stamping (or was hand-built); snapshot_is_current treats that as
    not-certifiable rather than silently current."""
    pick_label: str
    round: int
    my_roster_id: str
    candidates: tuple
    user_selected_player_id: Optional[str] = None
    picks_consumed: Optional[int] = None
    data_freshest_date: Optional[str] = None
    decision_regime: str = "contested"


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
    # Real per-league positional depth for narrow_candidates' position_depth -- the same
    # remaining-demand rank replacement_levels itself uses for VOR (num_teams matches
    # compute_draft_board's own derivation above), capped at POSITION_VIEW_DEPTH_CAP so a deep
    # position (WR/RB can run 30+ replacement rank in a real league) never balloons the
    # candidate set past what's actually useful to display or affordable to fully analyze.
    num_teams = league.get("total_rosters") or len({p.get("roster_id") for p in picks}) or 1
    replacement_ranks = dr.replacement_ranks(
        league.get("roster_positions") or [], num_teams, picks, players_db)
    position_depth = {pos: position_view_depth(rank) for pos, rank in replacement_ranks.items()}
    narrowed = narrow_candidates(
        board, top_n=top_n, user_selected_player_id=user_selected_player_id, position_depth=position_depth,
    )
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
        # Read strictly, no default: compute_draft_board owns the board's shape and now emits
        # universal_value in BOTH modes (see its upside branch for what the column means
        # there). A default here would only re-create the situation that broke this line --
        # every consumer quietly deciding for itself what an absent column meant -- and would
        # swallow a genuinely new third shape instead of failing where it was introduced.
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
            "rival_premium_take_probability": a.get("rival_premium_take_probability"),
            "positional_forfeit": a.get("positional_forfeit"),
            "position_expected_taken": a.get("position_expected_taken"),
            "positional_cliff": detect_positional_cliff(board, pid),
            "position_run_detected": (run_position is not None and row["position"] == run_position),
            "consensus_rank": reach["consensus_rank"] if reach else None,
            "consensus_tier": reach["consensus_tier"] if reach else None,
            "reach_label": reach["reach_label"] if reach else None,
            "projected_points": row.get("projected_points"),
            # Straight off the board row -- computed once per board in draft_room, not
            # recomputed per candidate here (see _attach_waiting_cost).
            "waiting_cost": row.get("waiting_cost"),
            "horizon_floor": row.get("horizon_floor"),
            "horizon_sensitivity": row.get("horizon_sensitivity"),
        })

    round_num = (max((p.get("round") or 1) for p in picks) if picks else 1)
    necessity_by_candidate = compute_pick_necessity(raw_candidates, round_num)
    tie_flags = near_tie_flags([c["team_acquisition_value"] for c in raw_candidates])
    path_flags = decision_path_flags(raw_candidates)

    candidates = [
        CandidateSnapshot(**c, pick_necessity=necessity, necessity_label=label,
                          near_tie_with_leader=tie, **paths)
        for c, (necessity, label), tie, paths in zip(
            raw_candidates, necessity_by_candidate, tie_flags, path_flags)
    ]

    return PickSnapshot(
        pick_label=pick_label,
        round=round_num,
        my_roster_id=str(my_roster_id),
        candidates=tuple(candidates),
        user_selected_player_id=(str(user_selected_player_id) if user_selected_player_id is not None else None),
        picks_consumed=len(picks),
        data_freshest_date=merger.freshest_date,
        decision_regime=decision_regime(raw_candidates),
    )


def snapshot_is_current(snapshot: PickSnapshot, picks: list[dict], merger: DataMerger) -> tuple[bool, Optional[str]]:
    """(is_current, reason) -- whether this frozen snapshot still describes the live state its
    consumer is about to act on, checked purely by INPUT IDENTITY (the stamp build_snapshot
    wrote), never by recomputing anything. False comes with a plain reason string a UI or
    debate layer can show verbatim. An unstamped snapshot (both stamp fields None -- hand-built,
    or predating stamping) is reported not-current rather than silently trusted: "unknown
    provenance" and "known current" are different claims, same don't-fabricate posture as
    everywhere else in this app."""
    if snapshot.picks_consumed is None and snapshot.data_freshest_date is None:
        return False, "snapshot carries no input-state stamp (built before stamping, or hand-assembled)"
    if snapshot.picks_consumed is not None and len(picks) != snapshot.picks_consumed:
        delta = len(picks) - snapshot.picks_consumed
        return False, (
            f"{delta} new pick(s) made since this snapshot was built" if delta > 0
            else "the picks list has fewer picks than this snapshot was built from"
        )
    if merger.freshest_date != snapshot.data_freshest_date:
        return False, "the underlying player data changed since this snapshot was built"
    return True, None


_DIFF_FIELDS = (
    "universal_value", "need_bonus", "eligibility_bonus", "team_acquisition_value",
    "survival_probability", "opportunity_cost", "expected_value_of_waiting", "denial_value",
    "rival_premium", "positional_forfeit", "pick_necessity",
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
