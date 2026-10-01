"""#24 / W1-07: what removing necessity's survival term actually costs. Run from the repo root.

THE A/B IS ONE PROCESS, ONE TOGGLE, AND THE SAME INPUTS. `compute_pick_necessity` is spied on
during a real 12-team draft so the EXACT raw candidate dicts it saw are kept, then replayed twice
-- once with NECESSITY_SURVIVAL_WEIGHT at its shipped value, once at 0.0. Reconstructing candidate
dicts from the snapshot instead would risk dropping a field, which would zero some other term in
BOTH arms and quietly understate the difference; spying cannot.

WHY NOT COMPARE AGAINST A SAVED BASELINE. Because that is the mistake this repo already paid for:
a Tier 3 improvement of "2 findings -> 0" turned out to be a scoring repair that had landed between
the two runs. Both arms here are the same commit, the same process, the same second.

12T_ppr_K_DEF and not build_mock_league: mock leagues have no K or DEF slot, so a probe on one
measures the format. Necessity is not position-specific, but the board that feeds it is.
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
import run_draft_battery as rdb

TEAMS, ROUNDS = 12, 16
ARM = "12T_ppr_K_DEF"
OUT = Path("evidence/w1_07/REMOVE_SURVIVAL_COST.json")


def main() -> int:
    merger = dm.DataMerger()
    players_db, _ = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    scoring = rdb.scoring_settings_from_capture()
    arm = next(a for a in db.league_matrix(scoring) if a["label"] == ARM)
    league = arm["league"]
    merger.set_league_format(db.league_format_hint(league))

    seats = [str(i) for i in range(1, TEAMS + 1)]
    pick_order = [str(s) for s in ds.generate_pick_order(seats, ROUNDS, "snake")]

    # THE SPY. Keeps the raw dicts by value -- `dict(c)` -- because the caller is free to mutate
    # them afterwards and a shallow reference would replay whatever they became.
    seen: list[tuple[list[dict], int]] = []
    real = ps.compute_pick_necessity

    def spy(raw_candidates, round_num):
        seen.append(([dict(c) for c in raw_candidates], round_num))
        return real(raw_candidates, round_num)

    ps.compute_pick_necessity = spy
    picks: list[dict] = []
    started = time.time()
    try:
        for index in range(TEAMS * ROUNDS):
            seat = pick_order[index]
            snap = ps.build_snapshot(
                merger, players_db, picks, pick_order, current_index=index, my_roster_id=seat,
                league=league, pick_label=f"{index // TEAMS + 1}.{index % TEAMS + 1:02d}",
                top_n=12, sleeper_projections=season,
                sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
            if not snap.candidates:
                print(f"no candidates at index {index}; stopping", file=sys.stderr)
                break
            picks.append({"player_id": str(snap.candidates[0].player_id), "roster_id": seat,
                          "round": index // TEAMS + 1, "pick_no": index + 1})
            if index % 24 == 0:
                print(f"  ... {index}/{TEAMS * ROUNDS}  {time.time() - started:.0f}s",
                      file=sys.stderr)
    finally:
        ps.compute_pick_necessity = real

    # REPLAY. Both arms on the captured inputs, in this process, toggling one constant.
    def replay() -> list[tuple[float, str]]:
        out = []
        for raw, round_num in seen:
            out.extend(real([dict(c) for c in raw], round_num))
        return out

    shipped_weight = ps.NECESSITY_SURVIVAL_WEIGHT
    before = replay()
    ps.NECESSITY_SURVIVAL_WEIGHT = 0.0
    try:
        after = replay()
    finally:
        ps.NECESSITY_SURVIVAL_WEIGHT = shipped_weight

    assert len(before) == len(after), "the two arms saw different populations"
    rows = len(before)
    moves = [abs(b[0] - a[0]) for b, a in zip(before, after)]
    flips = [(b[1], a[1]) for b, a in zip(before, after) if b[1] != a[1]]
    # SEPARATELY, always: a score that moved by exactly 0.0 is a measurement, and counting it as
    # "did not move" via `if move:` is the #187 breach in a reporting function.
    moved = sum(1 for m in moves if m > 0.0)
    unchanged = sum(1 for m in moves if m == 0.0)

    report = {
        "_comment": ("#24/W1-07: cost of removing necessity's survival term. One process, one "
                     "toggle, identical inputs captured by spying on compute_pick_necessity "
                     "during a real draft. See remove_survival_cost.py."),
        "arm": ARM, "teams": TEAMS, "rounds": ROUNDS,
        "picks_made": len(picks),
        "necessity_rows_scored": rows,
        "rows_whose_score_moved": moved,
        "rows_unchanged": unchanged,
        "max_score_move": round(max(moves), 2) if moves else None,
        "mean_score_move": round(sum(moves) / rows, 3) if rows else None,
        "label_flips": len(flips),
        "label_flip_rate": round(len(flips) / rows, 4) if rows else None,
        "label_flip_kinds": dict(collections.Counter(f"{b} -> {a}" for b, a in flips)),
        "component_budget_before": 157.6,
        "component_budget_after": 137.6,
        "clamp": 100.0,
        "must_take_threshold": 98.0,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(f"\n=== #24: removing necessity's survival term, {ARM} ===")
    print(f"  necessity rows scored : {rows}")
    print(f"  score moved           : {moved}  ({100 * moved / rows:.1f}%)")
    print(f"  score unchanged       : {unchanged}")
    print(f"  max move              : {report['max_score_move']}")
    print(f"  mean move             : {report['mean_score_move']}")
    print(f"  LABEL FLIPS           : {len(flips)}  ({100 * len(flips) / rows:.2f}%)")
    for kind, count in sorted(report["label_flip_kinds"].items(), key=lambda kv: -kv[1]):
        print(f"      {count:>5}  {kind}")
    print(f"\n  component budget 157.6 -> 137.6 against a CLAMP of 100.0, so MUST TAKE (98.0)")
    print(f"  stays reachable. The 100 was never a budget to free 20 from.")
    print(f"  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
