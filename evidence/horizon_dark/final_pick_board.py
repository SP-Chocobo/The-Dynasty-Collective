"""What does a person actually SEE at the one board where the horizon is genuinely dark?

The owner ruled: before deciding whether to place a carried floor at the zero-measurable state,
measure what absence there costs. This is that measurement.

The state is narrow and now precisely located. On Draft Room pricing, Fourth and Forever
(26 rounds, 312 picks) is the only cell of three that reaches it, and it reaches it at pick
**312 — the final pick of the draft**. Every earlier sample has at least two measurable
positions, and `positional_bench_appetite` imputes the rest from their mean, so a floor IS
placed. Only when NOTHING is measurable does `if not rates` return all-`None`.

So the question is not "is absence correct here" -- `#62` settled that, and with no measured
position there is no mean to impute FROM. The question is whether absence at THIS board costs
a decision. Three things decide that:

  1. WHOSE PICK IS IT. Pick 312 of 312 is the last pick of the draft. If the board is empty of
     decisions, absence costs nothing whatever the contract says.
  2. WHAT IS STILL ON IT. `horizon_floor` and `waiting_cost` are OBSERVABLE ONLY -- they reach
     no valuation (`_attach_waiting_cost` runs after `team_acquisition_value` is rounded, and
     the module docstring pins the separation). So absence cannot change the ranking. What it
     can do is leave a rendered column blank where a person is reading.
  3. HOW MANY ROWS. If the last pick has one legal candidate, "what does waiting cost" is not
     a question anyone is asking.

Measured at three boards for contrast, not one: the final pick, the pick before the layer's
last live sample, and the opening board.

NOT A REPAIR. Reports what is on the board; changes nothing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import lineup_optimizer as lo
import run_draft_battery as rdb
import run_roster_proof as rp

FF_CAPTURE = Path("data/league_captures/fourth_and_forever.json")


def ff_league() -> dict:
    cap = json.loads(FF_CAPTURE.read_text(encoding="utf-8"))
    league = {"roster_positions": cap["roster_positions"],
              "scoring_settings": {k: v["value"] for k, v in cap["scoring_settings_observed"].items()},
              "total_rosters": 12, "settings": {"type": 2}}
    league["draft_rounds"] = dr.draftable_slots_per_team(league["roster_positions"])
    return league


def main() -> int:
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    league = ff_league()
    merger.set_league_format(db.league_format_hint(league))     # rule 3, never skip
    rounds = int(league["draft_rounds"])
    slots = lo.slots_from_roster_positions(league["roster_positions"])
    seats = [str(i) for i in range(1, 13)]
    pick_order = ds.generate_pick_order(seats, rounds, "snake")
    points = rp.scoreable_pool(merger, players_db, league, season)
    print(f"Fourth and Forever  rounds={rounds}  picks={len(pick_order)}  priceable={len(points)}\n")

    # The same control board the carried-rate probe measured, rebuilt here.
    picks, taken, mine = [], set(), {}
    for idx in range(min(len(pick_order), rounds * 12)):
        seat = str(pick_order[idx])
        free = [pid for pid in points if pid not in taken]
        chosen = rp.control_pick(free, points, mine.get(seat, []), players_db, slots) if free else None
        if chosen is None:
            break
        taken.add(str(chosen))
        mine.setdefault(seat, []).append(str(chosen))
        picks.append({"pick_no": idx + 1, "round": idx // 12 + 1,
                      "roster_id": seat, "player_id": str(chosen)})

    # 311 is the board the LAST REAL DECISION faces; len(picks) is the state after the draft
    # is over, which is where the carried-rate probe's zero-measurable sample actually sits. The
    # difference between those two is the whole question -- a state nobody is on the clock for
    # costs no decision, whatever its floor says.
    for at in (0, 300, len(picks) - 1, len(picks)):
        sofar = picks[:at]
        on_clock = str(pick_order[at]) if at < len(pick_order) else None
        board = dr.compute_draft_board(
            merger, players_db, sofar, my_roster_id=(on_clock or seats[0]), league=league,
            sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        floors = {r["position"]: r.get("horizon_floor") for r in board}
        placed = {p: v for p, v in floors.items() if v is not None}
        waiting = [r for r in board if r.get("waiting_cost") is not None]
        label = ("OPENING BOARD" if at == 0 else
                 f"pick {at + 1} of {len(pick_order)}" if at < len(pick_order) else
                 "AFTER THE LAST PICK (no turn exists)")
        print(f"--- {label}   picks made={at}")
        print(f"    on the clock : {on_clock or 'nobody -- the draft is over'}")
        print(f"    board rows   : {len(board)}")
        print(f"    horizon_floor placed for {len(placed)} positions: {sorted(placed)}")
        print(f"    waiting_cost present on {len(waiting)} of {len(board)} rows")
        print(f"    basis values : "
              f"{sorted({r.get('horizon_basis') for r in board if r.get('horizon_basis')})}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
