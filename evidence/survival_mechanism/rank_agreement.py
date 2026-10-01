"""#206: does a top player sit at rank 1 on EVERY opponent board at once?

#244 established what the 0.00 is NOT: the 0.02 floor compounds to 0.30 over 60 picks, so the
floor cannot produce it. Reaching 0.00 needs HIGH table ranks -- 0.45^8 is already 0.0017, which
rounds to 0.00 at the three decimals `estimate_survival` reports. The hypothesis #244 left
untested is that every opponent board is built by the SAME valuation, so the player the engine
likes best is simultaneously rank 1 everywhere, and survival multiplies 0.55 by itself.

This measures the rank AGREEMENT directly rather than inferring it: for the top candidates, what
rank does each opponent board give them, and how often is it the same rank on all of them?

Run from the repo root. NEVER cd first -- DataMerger resolves baselines against cwd.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/survival_mechanism/rank_agreement.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import league_config as lc
import run_draft_battery as rdb

OUT = Path("evidence/survival_mechanism/rank_agreement.json")


def main() -> int:
    battery = json.loads(Path("evidence/mode_boundary/depth_battery.json").read_text())["arms"]
    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    base = rdb.scoring_settings_from_capture()
    matrix = {e["label"]: e for e in db.league_matrix(base)}
    label = "CAPTURE_fourth_and_forever"
    entry = battery[label]
    lg = dr.build_mock_league(teams=entry["teams"], superflex=False, scoring="ppr",
                              te_premium=False, dynasty=True, base_scoring=base)
    st = [s for s in lg["roster_positions"] if s != "BN"]
    lg["roster_positions"] = st + ["BN"] * (entry["rounds"] - len(lc.draftable_slots(st)))
    league = matrix[label]["league"] if label in matrix else lg
    merger.set_league_format(db.league_format_hint(league))            # NEVER SKIP

    roster_ids = [str(i) for i in range(1, entry["teams"] + 1)]
    boards = ds._build_opponent_boards(merger, players_db, [], league, roster_ids,
                                       sleeper_projections=season,
                                       sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    print(f"universe {prov['players_in_pool']}   opponent boards built: {len(boards)}", flush=True)

    # Each board's own top-10 by its valuation ordinal.
    ranks = {}
    for rid, board in boards.items():
        by_id = board.get("rank_by_id") if isinstance(board, dict) else None
        if not by_id:
            print(f"   roster {rid}: no rank_by_id -- shape is {type(board).__name__}", flush=True)
            continue
        ranks[rid] = by_id

    if not ranks:
        print("NO RANK MAPS -- cannot measure. Not reporting a number.", flush=True)
        return 1

    any_board = next(iter(ranks.values()))
    top = sorted(any_board, key=lambda p: any_board[p])[:10]
    print(f"\n   measuring the top {len(top)} of one board across all {len(ranks)} boards\n",
          flush=True)
    print(f"   {'player':<12} " + "  ".join(f"r{r:<3}" for r in sorted(ranks)) + "   distinct",
          flush=True)
    rows, identical = [], 0
    for pid in top:
        per = {rid: ranks[rid].get(pid) for rid in sorted(ranks)}
        distinct = len({v for v in per.values() if v is not None})
        identical += 1 if distinct == 1 else 0
        rows.append({"player_id": pid, "rank_by_roster": per, "distinct_ranks": distinct})
        print(f"   {pid:<12} " + "  ".join(
            f"{(per[rid] if per[rid] is not None else '-'):<4}" for rid in sorted(ranks))
            + f"   {distinct}", flush=True)

    print(f"\n   IDENTICAL on every board: {identical} of {len(top)}", flush=True)
    r1 = Counter()
    for rid, by_id in ranks.items():
        best = min(by_id, key=lambda p: by_id[p])
        r1[best] += 1
    print(f"   rank-1 players across the {len(ranks)} boards: {len(r1)} distinct "
          f"-- {dict(r1)}", flush=True)
    top_p = ds._take_probability(1, False)
    n_same = max(r1.values())
    print(f"\n   If ONE player is rank 1 on {n_same} boards, and each is an intervening pick,")
    print(f"   survival = (1 - {top_p})^{n_same} = {(1 - top_p) ** n_same:.4f} "
          f"-> rounds to {round((1 - top_p) ** n_same, 3)}", flush=True)
    OUT.write_text(json.dumps(
        {"boards": len(ranks), "top_examined": len(top), "identical_on_every_board": identical,
         "distinct_rank1_players": len(r1), "rank1_counts": dict(r1), "rows": rows}, indent=1))
    print(f"\nwrote {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
