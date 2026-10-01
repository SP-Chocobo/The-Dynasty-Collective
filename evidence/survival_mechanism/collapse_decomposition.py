"""#206: the 0.00, end to end, and what each of its two causes contributes.

`rank_agreement.py` (beside this file) established the MECHANISM: every opponent board is built
by the same CDME valuation, so one player is rank 1 on all twelve at once. This file closes the
loop in three steps that the mechanism probe deliberately did not take.

1. REPRODUCE THE NUMBER THROUGH THE PRODUCTION FUNCTION. `estimate_survival` itself, at a real
   turn with real intervening picks -- not `0.45 ** 12` computed by hand in a probe. A hand
   multiply proves the arithmetic; it does not prove the engine takes that path.

2. DECOMPOSE. Survival is a product, so its logarithm is a SUM over the intervening teams and
   each team's contribution is separable. Report the per-team factors, not one opaque collapse.

3. COUNTERFACTUALS, each one a DERIVED constraint rather than a tuned replacement (#56).
   (a) MASS: a team makes exactly one pick, so the probabilities it assigns across the whole
       board must sum to at most 1. #244 measured 6.23. Renormalising by the realised sum is
       arithmetic forced by "one team, one pick" -- no constant is chosen, so this is a bound,
       not a threshold. What survival does it give?
   (b) AGREEMENT: hold the table exactly as it ships and vary only HOW MANY of the intervening
       boards rank the target first. This isolates the second cause from the first and says
       what degree of rival disagreement the observed survival would require.

NOTHING HERE IS WIRED. This measures; the repair is #50's (see the register entry).

Run from the repo root. NEVER cd first -- DataMerger resolves baselines against cwd.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/survival_mechanism/collapse_decomposition.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import league_config as lc
import run_draft_battery as rdb

OUT = Path("evidence/survival_mechanism/collapse_decomposition.json")
LABEL = "CAPTURE_fourth_and_forever"


def board_mass(board: dict) -> tuple[float, float, float, int]:
    """What one opponent's take probabilities sum to across its OWN whole board: the head (the
    ranks RANK_TAKE_PROBABILITY actually names) and the tail (everything the floor catches)."""
    ranks = sorted(board["rank_by_id"].values())
    head = sum(ds.RANK_TAKE_PROBABILITY.get(r, 0.0) for r in ranks)
    tail = sum(ds.RANK_TAKE_PROBABILITY_FLOOR for r in ranks
               if r not in ds.RANK_TAKE_PROBABILITY)
    return head, tail, head + tail, len(ranks)


def main() -> int:
    battery = json.loads(Path("evidence/mode_boundary/depth_battery.json").read_text())["arms"]
    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    base = rdb.scoring_settings_from_capture()
    matrix = {e["label"]: e for e in db.league_matrix(base)}
    entry = battery[LABEL]
    lg = dr.build_mock_league(teams=entry["teams"], superflex=False, scoring="ppr",
                              te_premium=False, dynasty=True, base_scoring=base)
    st = [s for s in lg["roster_positions"] if s != "BN"]
    lg["roster_positions"] = st + ["BN"] * (entry["rounds"] - len(lc.draftable_slots(st)))
    league = matrix[LABEL]["league"] if LABEL in matrix else lg
    merger.set_league_format(db.league_format_hint(league))            # NEVER SKIP

    teams, rounds = entry["teams"], entry["rounds"]
    roster_ids = [str(i) for i in range(1, teams + 1)]
    pick_order = ds.generate_pick_order(roster_ids, rounds)
    me = roster_ids[0]                       # seat 1: the longest wait ahead of any turn
    current_index = 0                        # the opening pick; 22 intervening in a snake
    nxt = ds.find_next_pick_index(pick_order, me, current_index)
    intervening = ds.intervening_roster_ids(pick_order, current_index, nxt)
    print(f"universe {prov['players_in_pool']}   {teams}T x {rounds}R   seat {me}   "
          f"turn {current_index} -> {nxt}   intervening {len(intervening)}", flush=True)
    if not intervening:
        print("NO INTERVENING PICKS -- the population is vacuous, reporting nothing.")
        return 1

    boards = ds._build_opponent_boards(merger, players_db, [], league, roster_ids,
                                       sleeper_projections=season,
                                       sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    mine = boards[me]
    target = min(mine["rank_by_id"], key=lambda p: mine["rank_by_id"][p])
    print(f"   target = the engine's own #1, player {target}\n", flush=True)

    # ---- 1. the production function, not a hand multiply ------------------------------
    got = ds.estimate_survival([], players_db, pick_order, current_index, me, target,
                               boards, league=league)
    print(f"1. estimate_survival -> {got['survival_probability']}   "
          f"over {got['intervening_picks']} picks, "
          f"{got['unevidenced_picks']} unevidenced", flush=True)

    # ---- 2. the per-team decomposition ------------------------------------------------
    factors = [r["take_probability"] for r in got["risk_by_team"]]
    ranks_seen = [r["rank_on_their_board"] for r in got["risk_by_team"]]
    exact = math.prod(1 - p for p in factors)
    top5 = sum(1 for r in ranks_seen if r is not None and r in ds.RANK_TAKE_PROBABILITY)
    print(f"2. risk rows {len(factors)}   distinct take_probability {sorted(set(factors))}   "
          f"ranked inside the table on {top5} of {len(ranks_seen)} boards", flush=True)
    print(f"   unrounded product {exact:.6f}   log10 {math.log10(exact) if exact else float('-inf'):.2f}",
          flush=True)

    # ---- 3a. MASS: one team, one pick -------------------------------------------------
    head, tail, total, rows = board_mass(boards[intervening[0]])
    scaled = {n: (sum(ds.RANK_TAKE_PROBABILITY.get(r, 0.0) for r in range(1, n + 1))
                  + ds.RANK_TAKE_PROBABILITY_FLOOR
                  * max(0, n - len(ds.RANK_TAKE_PROBABILITY)))
              for n in (50, 128, 256, rows, 500)}
    norm_factors = [p / total for p in factors]
    normalised = math.prod(1 - p for p in norm_factors)
    print(f"\n3a. one opponent board: {rows} priced rows   head {head:.2f}  tail {tail:.2f}  "
          f"TOTAL {total:.2f} expected picks for a team that makes 1", flush=True)
    for n, s in sorted(scaled.items()):
        print(f"      pool {n:>4} -> {s:.2f}", flush=True)
    print(f"    renormalised by {total:.2f}: rank-1 take {factors[0]:.3f} -> "
          f"{norm_factors[0]:.4f}, survival {got['survival_probability']} -> "
          f"{round(normalised, 3)}", flush=True)

    # ---- 3b. AGREEMENT: vary only how many boards rank him first ----------------------
    p1 = ds._take_probability(1, False)
    floor = ds.RANK_TAKE_PROBABILITY_FLOOR
    n = len(factors)
    print(f"\n3b. table unchanged; k of {n} boards rank him 1, the rest carry the floor:",
          flush=True)
    agreement = {}
    for k in range(0, n + 1):
        v = (1 - p1) ** k * (1 - floor) ** (n - k)
        agreement[k] = round(v, 4)
        if k in (0, 1, 2, 3, 4, 6, 8, n):
            print(f"      k={k:<3} survival {v:.4f}  (reported {round(v, 3)})", flush=True)

    OUT.write_text(json.dumps({
        "league": LABEL, "teams": teams, "rounds": rounds, "seat": me,
        "turn_index": current_index, "next_turn_index": nxt,
        "universe": prov["players_in_pool"], "target_player_id": target,
        "survival_reported": got["survival_probability"],
        "survival_unrounded": exact,
        "intervening_picks": got["intervening_picks"],
        "risk_rows": len(factors),
        "boards_ranking_him_inside_the_table": top5,
        "distinct_take_probabilities": sorted(set(factors)),
        "one_board_mass": {"priced_rows": rows, "head": round(head, 4),
                           "tail": round(tail, 4), "total": round(total, 4)},
        "mass_by_pool_size": {str(k): round(v, 4) for k, v in sorted(scaled.items())},
        "survival_if_mass_normalised": round(normalised, 4),
        "survival_by_agreement_count": agreement,
    }, indent=1))
    print(f"\nwrote {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
