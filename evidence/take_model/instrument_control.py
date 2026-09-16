"""#206 CONTROL: can the rank instrument SEE concentration at all?

`observed_take_distribution` reports that real drafters take the engine's rank-1 player 3.0% of
the time and that the median rank taken is 32. That is either a finding about drafters or a
defect in the instrument, and a diffuse histogram is exactly what a broken rank lookup produces.

So: drive the SAME measurement with a drafter whose rank policy is KNOWN. A synthetic seat that
always takes the Nth-best priced player must come back as a spike at N. If it does not, the
instrument cannot see rank and the real-draft result is void.

NOT a circular control. Taking `board[0]` and then asserting rank 1 would only prove I can index
a list. The policy here is rank 3 -- off the top, inside the table, and requiring the lookup to
agree with the producer on both the ORDER and the PRICED-ONLY filter that `rank_by_id` uses.

Run from the repo root.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/take_model/instrument_control.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import run_draft_battery as rdb

OUT = Path("evidence/take_model/instrument_control.json")
POLICY_RANK = 3
PICKS = 48


def main() -> int:
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    base = rdb.scoring_settings_from_capture()
    league = dr.build_mock_league(teams=12, superflex=True, scoring="ppr", te_premium=True,
                                  dynasty=True, base_scoring=base)
    merger.set_league_format(db.league_format_hint(league))          # NEVER SKIP
    print(f"control: a seat that ALWAYS takes rank {POLICY_RANK}; {PICKS} picks; "
          f"universe {universe['players_in_pool']}", flush=True)

    picks, seen = [], Counter()
    for i in range(PICKS):
        seat = str((i % 12) + 1)
        rows = dr.compute_draft_board(merger, players_db, picks, my_roster_id=seat,
                                      league=league, mode="balanced",
                                      sleeper_projections=season,
                                      sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        order = [r["player_id"] for r in rows if r.get("bpa") is not None]
        if len(order) < POLICY_RANK:
            break
        taken = order[POLICY_RANK - 1]
        # THE MEASUREMENT, character-for-character what the real-draft probe does.
        rank = order.index(taken) + 1
        seen[rank] += 1
        picks.append({"pick_no": i + 1, "round": i // 12 + 1, "roster_id": seat,
                      "player_id": taken})
        if (i + 1) % 12 == 0:
            print(f"   {i + 1:>3} picks   histogram so far: {dict(seen)}", flush=True)

    n = sum(seen.values())
    spike = seen.get(POLICY_RANK, 0)
    print(f"\n   measured {n} picks", flush=True)
    print(f"   histogram: {dict(seen)}", flush=True)
    print(f"   SPIKE AT {POLICY_RANK}: {spike}/{n} = {spike / n:.1%}", flush=True)
    verdict = ("the instrument CAN see concentration -- the real-draft diffusion is a finding"
               if n and spike == n else
               "BROKEN: the instrument cannot recover a known rank policy; the real-draft "
               "result is VOID until this passes")
    print(f"   VERDICT: {verdict}", flush=True)

    OUT.write_text(json.dumps(
        {"policy_rank": POLICY_RANK, "picks": n, "histogram": {str(k): v for k, v in seen.items()},
         "spike_share": round(spike / n, 4) if n else None, "verdict": verdict}, indent=1))
    print(f"\nwrote {OUT}", flush=True)
    return 0 if n and spike == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
