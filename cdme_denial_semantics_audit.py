"""Denial-semantics audit: does the current denial mechanism actually represent strategic
denial, per a stricter definition, or does it conflate "this player is generically valuable
and some rival could plausibly want him" with genuine opponent-specific leverage?

The stricter definition (the refinement requested mid-investigation): a real denial play
requires evidence that (1) a SPECIFIC rival has a materially elevated incentive/need for the
player, (2) the player is particularly relevant to that rival relative to their alternatives,
(3) that rival has a CREDIBLE PATH to actually selecting the player if we pass, and
(4) preventing that outcome creates meaningful strategic value for us. Ordinary acquisition
("he's the best player, so we take him") and incidental blocking ("someone else happens to
lose access") must stay distinct from strategic denial ("we specifically identified this
rival's elevated need and a credible path for them to act on it").

The CURRENT mechanism, precisely characterized (never changed by this file):
  - rival_premium (draft_strategy.pick_analysis) = max over intervening teams of
    (opp_row["final_score"] - opp_row["universal_value"]) -- i.e., whichever intervening
    rival's OWN need_bonus/eligibility_bonus premium for this player is largest. This is
    deliberately probability-FREE (see pick_synthesis.py's own docstring on the M13
    double-count fix) -- it captures criterion (1)/(2)-ish territory (a specific rival's own
    elevated valuation) but carries NO reference to whether that rival could actually get the
    player (criterion 3).
  - block_opportunity (pick_synthesis.decision_path_flags) = rival_premium >=
    2 * NEED_BONUS_PER_DEDICATED_SLOT -- the literal "⚔ denies a rival" UI flag. Fires purely
    off premium magnitude, with NO reference to that same rival's own take_probability at all.

This module reuses draft_strategy's own real functions (_build_opponent_boards,
estimate_survival) rather than reimplementing survival/take-probability math -- it only adds
the bookkeeping needed to identify WHICH intervening team drives the max rival_premium for
each candidate, and that specific team's own take_probability (already computed by
estimate_survival, just not surfaced against the premium-winning team specifically anywhere
today).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import draft_room as dr
import draft_strategy as ds
from data_merger import DataMerger


@dataclass(frozen=True)
class DenialAudit:
    player_id: str
    rival_premium: float
    block_opportunity: bool  # current UI flag, recomputed via the real threshold
    premium_team: Optional[str]  # which intervening roster_id drove the max premium
    premium_team_take_probability: Optional[float]  # that SAME team's own take_probability
    survival_probability: float
    need_bonus: float
    eligibility_bonus: float


def audit_candidates(
    merger: DataMerger, players_db: dict[str, dict], picks: list[dict], pick_order: list,
    current_index: int, my_roster_id, league: dict, candidate_player_ids: list[str],
    *, mode: str = "auto", pool_scope: str = "all",
) -> list[DenialAudit]:
    """One DenialAudit per candidate, in the same order as candidate_player_ids. Real
    functions only -- draft_strategy._build_opponent_boards and .estimate_survival compute
    everything; this only tracks which team drove the max premium and looks up that team's
    own take_probability from estimate_survival's own risk_by_team output."""
    my_board = {r["player_id"]: r for r in dr.compute_draft_board(
        merger, players_db, picks, my_roster_id=my_roster_id, league=league, mode=mode, pool_scope=pool_scope,
    )}
    my_next_index = ds.find_next_pick_index(pick_order, my_roster_id, current_index)
    intervening = ds.intervening_roster_ids(pick_order, current_index, my_next_index)
    opponent_boards = ds._build_opponent_boards(
        merger, players_db, picks, league, intervening, mode=mode, pool_scope=pool_scope,
    )

    results = []
    for pid in candidate_player_ids:
        my_row = my_board.get(str(pid))
        if my_row is None:
            continue
        survival = ds.estimate_survival(
            picks, players_db, pick_order, current_index, my_roster_id, pid, opponent_boards, league=league,
        )
        take_prob_by_team = {r["roster_id"]: r["take_probability"] for r in survival["risk_by_team"]}

        rival_premium = 0.0
        premium_team = None
        for roster_id in intervening:
            opp_board = opponent_boards.get(str(roster_id), {})
            opp_row = opp_board.get("by_id", {}).get(str(pid))
            if opp_row is None or "universal_value" not in opp_row:
                continue
            premium = opp_row["final_score"] - opp_row["universal_value"]
            if premium > rival_premium:
                rival_premium = premium
                premium_team = roster_id

        results.append(DenialAudit(
            player_id=str(pid),
            rival_premium=round(rival_premium, 2),
            block_opportunity=rival_premium >= 2 * dr.NEED_BONUS_PER_DEDICATED_SLOT,
            premium_team=premium_team,
            premium_team_take_probability=take_prob_by_team.get(premium_team) if premium_team else None,
            survival_probability=survival["survival_probability"],
            need_bonus=my_row.get("need_bonus", 0.0),
            eligibility_bonus=my_row.get("eligibility_bonus", 0.0),
        ))
    return results
