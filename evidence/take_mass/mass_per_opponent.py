"""#206 (mass half): how much probability mass does ONE opponent's ONE pick actually carry?

THE CONSTRAINT, which needs no league data to state. `estimate_survival` asks, for each
intervening opponent, "what is the chance THIS team takes THIS player at their next pick?" and
answers with `_take_probability(rank_on_their_board)`. A team makes exactly ONE pick. The events
"they take the rank-1 player", "they take the rank-2 player", ... are therefore MUTUALLY
EXCLUSIVE, so summed over that opponent's whole board the probabilities must be <= 1.0.

`RANK_TAKE_PROBABILITY`'s five named keys sum to 1.21 before the floor tail is counted at all.
This measures the REAL total on real boards, which is the number that matters, because the tail
is as long as the board is deep.

CONTROL, so this is not just arithmetic restated. A board with exactly five priced rows must
report exactly 1.21 -- no tail, five keys. If the instrument cannot reproduce that by
construction it is summing something other than what it claims.

Run from the REPO ROOT. Writes mass_per_opponent.json beside this file.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import run_draft_battery as rdb

OUT = Path(__file__).with_name("mass_per_opponent.json")
CAPTURE = Path("data/league_captures/fourth_and_forever.json")


def board_mass(board: dict) -> dict:
    """Total take-probability mass over one opponent board, split by where it comes from."""
    ranks = board["rank_by_id"]
    unpriced = set(board.get("unpriced_ids", ()) or ())
    named = 0.0
    tail = 0.0
    for _pid, rank in ranks.items():
        p = ds._take_probability(rank, False)
        if rank in ds.RANK_TAKE_PROBABILITY:
            named += p
        else:
            tail += p
    floor_mass = len(unpriced) * ds.RANK_TAKE_PROBABILITY_FLOOR
    return {
        "priced_rows": len(ranks),
        "unpriced_rows": len(unpriced),
        "named_key_mass": round(named, 4),
        "tail_mass": round(tail, 4),
        "unpriced_floor_mass": round(floor_mass, 4),
        "total_mass": round(named + tail + floor_mass, 4),
    }


def main() -> int:
    # Built EXACTLY as draft_battery builds its CAPTURE_fourth_and_forever arm (draft_battery
    # .py:171-182) rather than reconstructed here. #248 is what happens when a capture is
    # rebuilt by hand: build_mock_league overwrote `rec` from its own argument, so an arm read
    # a different rankings export than it reported while claiming to carry F&F's rulebook.
    cap = json.loads(CAPTURE.read_text())
    league = {
        "roster_positions": cap["roster_positions"],
        "scoring_settings": {k: v["value"] for k, v in cap["scoring_settings_observed"].items()},
        "total_rosters": cap.get("total_rosters", 12),
        "settings": {"type": 2},
    }
    league_name = cap.get("league")
    merger = dm.DataMerger()
    # The REAL captured universe and the season sums production prices from (#201/#204) --
    # build_players_db is the vendor reconstruction and its own guard refuses new work.
    players_db, provenance = rdb.build_players_db_from_capture()
    projections = rdb.season_projections_from_capture()
    merger.set_league_format(db.league_format_hint(league))

    roster_ids = [str(i) for i in range(1, int(league.get("total_rosters", 12)) + 1)]
    boards = ds._build_opponent_boards(
        merger, players_db, [], league, roster_ids,
        sleeper_projections=projections, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
    )

    per_board = {rid: board_mass(b) for rid, b in sorted(boards.items(), key=lambda kv: int(kv[0]))}
    totals = [v["total_mass"] for v in per_board.values()]

    # CONTROL: five priced rows and nothing else must give exactly the five named keys.
    five = {"rank_by_id": {f"p{i}": i for i in range(1, 6)}, "unpriced_ids": ()}
    control = board_mass(five)
    expected = round(sum(ds.RANK_TAKE_PROBABILITY.values()), 4)
    control_ok = abs(control["total_mass"] - expected) < 1e-9

    # DISCRIMINATING ARM. Every board above reports the SAME total, which #245 says to treat as
    # a broken instrument until proven otherwise. Here it is derivable rather than suspicious:
    # mass = 1.21 + floor*(priced - 5) + floor*unpriced depends ONLY on row COUNTS, and at an
    # empty board every opponent draws from the same pool, so the counts coincide while the
    # ORDERINGS differ by roster need. The proof that the instrument is live, not stuck, is that
    # the number MOVES when the pool drains -- so drain it and watch.
    depth_arm = []
    picks: list[dict] = []
    pick_order = ds.generate_pick_order(roster_ids, 26, "snake")
    for depth in (0, 40, 80, 120):
        while len(picks) < depth:
            i = len(picks)
            rid = str(pick_order[i])
            b = ds._build_opponent_boards(
                merger, players_db, picks, league, [rid],
                sleeper_projections=projections, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
            )[rid]
            take = next(iter(b["rank_by_id"]), None)
            if take is None:
                break
            picks.append({"player_id": take, "roster_id": rid})
        probe_rid = str(pick_order[len(picks) % len(pick_order)])
        b = ds._build_opponent_boards(
            merger, players_db, picks, league, [probe_rid],
            sleeper_projections=projections, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
        )[probe_rid]
        m = board_mass(b)
        m["picks_made"] = len(picks)
        depth_arm.append(m)

    masses = [a["total_mass"] for a in depth_arm]
    responds = len(set(masses)) > 1

    report = {
        "league": league_name,
        "universe_provenance": provenance,
        "constraint": "one opponent makes one pick, so mass over their board must be <= 1.0",
        "named_keys": ds.RANK_TAKE_PROBABILITY,
        "named_keys_sum": expected,
        "floor": ds.RANK_TAKE_PROBABILITY_FLOOR,
        "control_five_priced_rows": control,
        "control_expected_total": expected,
        "control_passes": control_ok,
        "per_board": per_board,
        "boards": len(per_board),
        "min_total_mass": min(totals) if totals else None,
        "max_total_mass": max(totals) if totals else None,
        "mean_total_mass": round(sum(totals) / len(totals), 4) if totals else None,
        "identical_across_boards_is_derivable": (
            "mass depends only on row counts, and at an empty board every opponent draws from "
            "the same pool -- see depth_arm for the proof the instrument is not stuck"),
        "depth_arm": depth_arm,
        "depth_arm_responds": responds,
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n")

    print(f"league {league_name}   boards {len(per_board)}")
    print(f"  CONTROL five priced rows -> {control['total_mass']} "
          f"(expected {expected}) {'OK' if control_ok else 'BROKEN INSTRUMENT'}")
    if not control_ok:
        return 1
    any_board = next(iter(per_board.values()))
    print(f"  a real board: {any_board['priced_rows']} priced, {any_board['unpriced_rows']} unpriced")
    print(f"     named keys {any_board['named_key_mass']}  tail {any_board['tail_mass']}  "
          f"unpriced floor {any_board['unpriced_floor_mass']}")
    print(f"  TOTAL MASS per opponent pick: min {report['min_total_mass']}  "
          f"mean {report['mean_total_mass']}  max {report['max_total_mass']}")
    print(f"  the constraint says this must be <= 1.0")
    print("  WHERE THE MASS IS: named keys are the small part --")
    print(f"     named {any_board['named_key_mass']} / tail {any_board['tail_mass']} / "
          f"unpriced floor {any_board['unpriced_floor_mass']}  "
          f"=> the floor carries "
          f"{round(100 * (any_board['tail_mass'] + any_board['unpriced_floor_mass']) / any_board['total_mass'], 1)}%")
    print("  DEPTH ARM (does the number move as the pool drains?):")
    for a in depth_arm:
        print(f"     {a['picks_made']:4d} picks -> priced {a['priced_rows']:4d}  "
              f"unpriced {a['unpriced_rows']:4d}  mass {a['total_mass']}")
    print(f"     instrument responds to depth: {responds}"
          f"{'' if responds else '   <-- STUCK, the identical boards above are NOT explained'}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
