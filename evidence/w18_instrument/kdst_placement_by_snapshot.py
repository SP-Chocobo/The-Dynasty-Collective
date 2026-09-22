"""Does the K/DST complaint survive the app's own projection snapshot? Run from the repo root.

THE QUESTION. Every K/DST finding in this programme -- "defenses go about five rounds too early",
KDST_VALUATION.md, and #17's turn-ending clustering -- was measured with
`run_draft_battery.season_projections_from_capture()`. Measured separately
(evidence/w18_instrument/CONFIGURATION.md), that snapshot prices DEF at 0.69 of a quarterback's
rank-1-to-replacement gap, while summing Sleeper's weekly projections for a season -- the shape
`app.py` passes -- prices the same position at 0.32 on the same board, same code, same league.
A 2.2x swing in the exact quantity the complaint is about.

So this drafts the SAME format twice, changing only the projection snapshot, and reports where K
and DEF actually land. If the complaint is about the engine it survives both arms. If it is about
the snapshot, it moves.

SELF-PLAY IS THE RIGHT INSTRUMENT HERE and not a blindness trap: this is a PLACEMENT question
about one engine's own behaviour ("where does it put K/DEF"), not a quality A/B against a field.
Both arms are one process, one commit, one second -- never a fresh run against a saved baseline.

12T_ppr_K_DEF and not build_mock_league: mock leagues have NO K and NO DEF slot, so a probe on one
reports "K and DEF never taken" and measures the format. That error has already been made here
once and is recorded in POST_AUDIT_PLAN.md.
"""

from __future__ import annotations

import collections
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import capture_weekly_lines as cwl
import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import pick_synthesis as ps
import player_universe as pu
import run_draft_battery as rdb

TEAMS, ROUNDS = 12, 16
ARM = "12T_ppr_K_DEF"
LIVE_SEASON = "2026"
OUT = Path("evidence/w18_instrument/KDST_PLACEMENT_BY_SNAPSHOT.json")


def season_sums(season: str) -> dict[str, dict]:
    totals = collections.defaultdict(lambda: collections.defaultdict(float))
    for _week, lines in cwl.load_season(season, "projections").items():
        for pid, stats in lines.items():
            for key, value in stats.items():
                try:
                    totals[pid][key] += float(value)
                except (TypeError, ValueError):
                    continue
    return {pid: dict(s) for pid, s in totals.items()}


def draft(label: str, projections: dict, players_db: dict, league: dict) -> dict:
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
            sleeper_projections=projections, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        if not snap.candidates:
            break
        picks.append({"player_id": str(snap.candidates[0].player_id),
                      "roster_id": pick_order[index], "round": index // TEAMS + 1,
                      "pick_no": index + 1})
        if index % 48 == 0:
            print(f"  [{label}] {index}/{TEAMS * ROUNDS}  {time.time() - started:.0f}s",
                  file=sys.stderr)

    position_of = lambda pid: pu.player_position(players_db.get(str(pid)) or {}) or "?"
    first: dict[str, float] = {}
    counts: collections.Counter = collections.Counter()
    for pick in picks:
        pos = position_of(pick["player_id"])
        counts[pos] += 1
        if pos not in first:
            # Round.pick-within-round, the same "3.09" notation #17's record uses.
            first[pos] = round(pick["round"] + (pick["pick_no"] - 1) % TEAMS / 100.0, 2)
    return {"picks": len(picks), "first_taken": first, "by_position": dict(counts),
            "kdst_by_round_12": sum(1 for p in picks
                                    if p["round"] <= 12 and position_of(p["player_id"]) in ("K", "DEF"))}


def main() -> int:
    scoring = rdb.scoring_settings_from_capture()
    players_db, _ = rdb.build_players_db_from_capture()
    league = next(a for a in db.league_matrix(scoring) if a["label"] == ARM)["league"]

    arms = {
        "battery_capture": rdb.season_projections_from_capture(),
        f"app_shaped_{LIVE_SEASON}": season_sums(LIVE_SEASON),
    }
    results = {name: draft(name, proj, players_db, league) for name, proj in arms.items()}

    report = {
        "_comment": ("Where K and DEF land, drafting the same format twice and changing ONLY the "
                     "projection snapshot. See kdst_placement_by_snapshot.py."),
        "arm": ARM, "teams": TEAMS, "rounds": ROUNDS, "results": results,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(f"\n=== K/DST placement, {ARM}, {TEAMS}x{ROUNDS}, snapshot is the ONLY difference ===")
    names = list(results)
    print(f"  {'':<14}" + "".join(f"{n:>22}" for n in names))
    for pos in ("K", "DEF", "QB", "TE"):
        cells = "".join(f"{str(results[n]['first_taken'].get(pos, '--')):>22}" for n in names)
        print(f"  first {pos:<8}{cells}")
    print(f"  {'K+DEF by rd12':<14}"
          + "".join(f"{results[n]['kdst_by_round_12']:>22}" for n in names))
    print(f"  {'picks':<14}" + "".join(f"{results[n]['picks']:>22}" for n in names))
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
