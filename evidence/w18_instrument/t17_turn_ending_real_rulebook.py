"""#17 re-measured under a rulebook that can actually SCORE kickers and defenses. Repo root.

WHY THIS EXISTS, and it is the third vacuity in the same probe's history.

`evidence/blind_pass/turn_ending_remeasured.py` builds its league with
`db.league_matrix(merger.base_scoring_settings() if hasattr(...) else None)`. `DataMerger` has no
`base_scoring_settings`, so that argument is always `None`, and `league_matrix(None)` yields a
rulebook whose scoring_settings is exactly `{'rec': 1.0}` -- ONE key. The `12T_ppr_K_DEF` arm it
then selects HAS a K slot and a DEF slot, and **none of the 22 K/DEF scoring keys**: no `fgm_*`,
no `xpm`, no `pts_allow_*`, no `def_td`, no `sack`, no `safe`, no `blk_kick`.

So #17's numbers -- first DEF 3.09, first K 4.10, DEF turn-ending ratio 3.66x -- describe where the
engine puts kickers and defenses in a league where kickers and defenses cannot score.

That probe already carries a recorded correction for exactly this class: its first run used
`build_mock_league`, which has no K or DEF SLOT, and reported "K and DEF never taken". The fix
supplied the slots and left the SCORING vacuous. Half a fix, and the half that was missing is the
half that prices the positions the item is about.

THIS RUN passes `rdb.scoring_settings_from_capture()` -- the 64-key rulebook the battery and the
app both price against -- and is otherwise the same measurement: same arm, same teams, same
rounds, same self-play, same turn-ending definition.

Self-play is the right instrument for a PLACEMENT question about one engine's own behaviour. It
would be the wrong one for a quality A/B against a field.
"""

from __future__ import annotations

import collections
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import pick_synthesis as ps
import player_universe as pu
import run_draft_battery as rdb

TEAMS, ROUNDS = 12, 16
ARM = "12T_ppr_K_DEF"
OUT = Path("evidence/w18_instrument/T17_REAL_RULEBOOK.json")


def main() -> int:
    scoring = rdb.scoring_settings_from_capture()
    players_db, _ = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    league = next(a for a in db.league_matrix(scoring) if a["label"] == ARM)["league"]

    kd_keys = [k for k in (league.get("scoring_settings") or {})
               if k.startswith(("fgm", "xpm", "pts_allow", "def_", "sack", "safe", "blk"))]
    # NON-VACUITY, ASSERTED BEFORE THE MEASUREMENT RUNS, because that is the failure this probe
    # exists to correct. A run that reports K/DEF placement under a rulebook that cannot score
    # them is not a weaker measurement -- it is a measurement of something else.
    if not kd_keys:
        print("REFUSING TO RUN: this rulebook has no K/DEF scoring keys, so any placement it "
              "reports is about a league where kickers and defenses cannot score.", file=sys.stderr)
        return 1
    print(f"rulebook: {len(league.get('scoring_settings') or {})} scoring keys, "
          f"{len(kd_keys)} of them K/DEF", file=sys.stderr)

    merger = dm.DataMerger()
    merger.set_league_format(db.league_format_hint(league))
    seats = [str(i) for i in range(1, TEAMS + 1)]
    pick_order = [str(s) for s in ds.generate_pick_order(seats, ROUNDS, "snake")]

    picks: list[dict] = []
    started = time.time()
    for index in range(TEAMS * ROUNDS):
        snap = ps.build_snapshot(
            merger, players_db, picks, pick_order, current_index=index,
            my_roster_id=pick_order[index], league=league,
            pick_label=f"{index // TEAMS + 1}.{index % TEAMS + 1:02d}", top_n=12,
            sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        if not snap.candidates:
            break
        picks.append({"player_id": str(snap.candidates[0].player_id),
                      "roster_id": pick_order[index], "round": index // TEAMS + 1,
                      "pick_no": index + 1})
        if index % 48 == 0:
            print(f"  ... {index}/{TEAMS * ROUNDS}  {time.time() - started:.0f}s", file=sys.stderr)

    position_of = lambda pid: pu.player_position(players_db.get(str(pid)) or {}) or "?"
    seats_seq = [p["roster_id"] for p in picks]
    # A pick is TURN-ENDING when the same seat picks again immediately -- the snake turn, where
    # there is no intervening pick to lose a player to.
    ending = {i for i in range(len(picks) - 1) if seats_seq[i] == seats_seq[i + 1]}

    all_counts = collections.Counter(position_of(p["player_id"]) for p in picks)
    end_counts = collections.Counter(position_of(picks[i]["player_id"]) for i in ending)
    rows = {}
    for pos, total in all_counts.most_common():
        expected = total * len(ending) / len(picks)
        rows[pos] = {
            "all": total, "turn_ending": end_counts.get(pos, 0),
            "expected": round(expected, 2),
            # None, never 0.0, when there is nothing to divide by (#187).
            "ratio": round(end_counts.get(pos, 0) / expected, 2) if expected else None,
        }

    first = {}
    for pick in picks:
        pos = position_of(pick["player_id"])
        if pos not in first:
            first[pos] = {"pick_no": pick["pick_no"],
                          "label": round(pick["round"] + (pick["pick_no"] - 1) % TEAMS / 100.0, 2)}

    report = {
        "_comment": ("#17 re-measured under the 64-key capture rulebook. The blind_pass probe "
                     "passed None to league_matrix and measured a {'rec': 1.0} league with no "
                     "K/DEF scoring keys at all. See t17_turn_ending_real_rulebook.py."),
        "arm": ARM, "teams": TEAMS, "rounds": ROUNDS, "picks": len(picks),
        "scoring_keys": len(league.get("scoring_settings") or {}),
        "kdst_scoring_keys": len(kd_keys),
        "turn_ending_picks": len(ending),
        "by_position": rows, "first_taken": first,
        "kdst_by_round_12": sum(1 for p in picks if p["round"] <= 12
                                and position_of(p["player_id"]) in ("K", "DEF")),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(f"\n=== #17 re-measured, REAL rulebook ({report['scoring_keys']} keys, "
          f"{report['kdst_scoring_keys']} K/DEF) ===")
    print(f"picks: {len(picks)}   turn-ending: {len(ending)} "
          f"({100 * len(ending) / len(picks):.1f}%)\n")
    print(f"{'pos':<6}{'all':>5}{'turn-ending':>13}{'expected':>10}{'ratio':>8}")
    for pos, row in rows.items():
        ratio = f"{row['ratio']:.2f}" if row["ratio"] is not None else "n/a"
        print(f"{pos:<6}{row['all']:>5}{row['turn_ending']:>13}{row['expected']:>10.2f}{ratio:>8}")
    print()
    for pos in ("K", "DEF"):
        got = first.get(pos)
        print(f"first {pos:<4}: pick {got['pick_no']} ({got['label']})" if got
              else f"first {pos:<4}: NEVER TAKEN")
    print(f"K/DEF by round 12: {report['kdst_by_round_12']}")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
