"""#30: what does a round-5 defense ACTUALLY cost, in real points? Run from the repo root.

THE QUESTION the projected ruler cannot answer. Across three drafts whose first DEF ranged from
round 5 to round 10, the projected league total moved -0.16%/+0.08% -- noise. It solves one lineup
over season totals with no absences, so it cannot see what a bench is for and cannot price when a
defense is taken. `realized_ruler` can.

THE METHOD, and why it is surgery rather than a redraft. A redraft per arm costs ~730s and changes
every seat at once (self-play), which is how the projected ruler ended up indifferent. Instead:
draft ONCE on 2024 projections, then for each seat that took a K or DEF early, build a
counterfactual roster identical except that pick is replaced by the best skill player still on the
board at that exact pick. Score both on 2024 REALIZED weekly stats.

That isolates one decision. It measures the direct cost of spending a round-5 pick on a defense
instead of a skill player, for the seat that spent it.

WHAT IT DOES NOT MODEL, and these are real:
  - SECOND-ORDER EFFECTS. The skill player taken in the counterfactual was actually drafted by
    someone else later; giving him to this seat does not remove him from theirs here. So this is
    an UPPER bound on the gain from deferring, not an estimate of it.
  - The seat still needs a defense eventually. The counterfactual roster is short one DEF, and if
    the league's roster requires one, its weekly solve simply leaves that slot empty -- which is
    the honest reading of "I never drafted one", and is itself part of the cost being measured.
  - No waivers. A real manager would stream a defense into that empty slot, which is exactly the
    thing this engine has no model for. So the counterfactual is PESSIMISTIC about deferring, in
    the opposite direction to the second-order effect above. Both bounds are stated because
    neither can be removed.

The draft is on 2024 PROJECTIONS so the decisions are period-correct: the board sees what a
drafter in 2024 would have seen, and the season then happens to it.
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
import realized_ruler as rr
import run_draft_battery as rdb

TEAMS, ROUNDS, ARM, SEASON = 12, 16, "12T_ppr_K_DEF", "2024"
SKILL = ("QB", "RB", "WR", "TE")
#: A pick is "early" for a streamed position if it lands before the owner's target window, which
#: is the bottom 25-30% of the draft. DERIVED from ROUNDS, not chosen.
EARLY_BEFORE_ROUND = int(ROUNDS * 0.75) + 1
OUT = Path("evidence/kdst_streaming/COUNTERFACTUAL_COST.json")


def season_sums(season: str, scoring: dict) -> dict[str, dict]:
    totals = collections.defaultdict(lambda: collections.defaultdict(float))
    for _week, lines in cwl.load_season(season, "projections").items():
        for pid, stats in lines.items():
            for key, value in stats.items():
                try:
                    totals[pid][key] += float(value)
                except (TypeError, ValueError):
                    continue
    return {pid: dict(v) for pid, v in totals.items()}


def main() -> int:
    scoring = rdb.scoring_settings_from_capture()
    players_db, _ = rdb.build_players_db_from_capture()
    arm = next(a for a in db.league_matrix(scoring) if a["label"] == ARM)
    league = arm["league"]
    projections = season_sums(SEASON, scoring)
    realized = rr.weekly_points(cwl.load_season(SEASON, "stats"), scoring)
    slots = rr.slots_for(league)

    merger = dm.DataMerger()
    merger.set_league_format(db.league_format_hint(league))
    order = [str(s) for s in ds.generate_pick_order(
        [str(i) for i in range(1, TEAMS + 1)], ROUNDS, "snake")]

    picks, alternatives = [], {}
    started = time.time()
    for index in range(TEAMS * ROUNDS):
        snap = ps.build_snapshot(
            merger, players_db, picks, order, index, order[index], league,
            pick_label=f"{index // TEAMS + 1}.{index % TEAMS + 1:02d}", top_n=40,
            sleeper_projections=projections, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        if not snap.candidates:
            break
        chosen = snap.candidates[0]
        # The best SKILL player on this exact board, kept only for picks we may counterfactual.
        best_skill = next((c for c in snap.candidates
                           if pu.player_position(players_db.get(str(c.player_id)) or {}) in SKILL),
                          None)
        alternatives[index] = str(best_skill.player_id) if best_skill else None
        picks.append({"player_id": str(chosen.player_id), "roster_id": order[index],
                      "round": index // TEAMS + 1, "pick_no": index + 1, "_index": index})
        if index % 48 == 0:
            print(f"  ... {index}/{TEAMS * ROUNDS}  {time.time() - started:.0f}s", file=sys.stderr)

    by_seat = collections.defaultdict(list)
    for pick in picks:
        by_seat[pick["roster_id"]].append(pick)

    rows = []
    for seat, seat_picks in sorted(by_seat.items(), key=lambda kv: int(kv[0])):
        ids = [p["player_id"] for p in seat_picks]
        early = [p for p in seat_picks
                 if p["round"] < EARLY_BEFORE_ROUND
                 and pu.player_position(players_db.get(p["player_id"]) or {}) in ("K", "DEF")]
        if not early:
            continue
        actual = rr.score_roster_realized(ids, players_db, realized, slots)
        for pick in early:
            swap = alternatives.get(pick["_index"])
            if not swap or swap in ids:
                continue
            counter = [swap if pid == pick["player_id"] else pid for pid in ids]
            alt = rr.score_roster_realized(counter, players_db, realized, slots)
            rows.append({
                "seat": seat,
                "round": pick["round"],
                "position": pu.player_position(players_db.get(pick["player_id"]) or {}),
                "drafted": pu.player_name(players_db.get(pick["player_id"]) or {}, pick["player_id"]),
                "instead": pu.player_name(players_db.get(swap) or {}, swap),
                "actual_total": actual["total"],
                "counterfactual_total": alt["total"],
                "delta": round(alt["total"] - actual["total"], 2),
            })

    report = {
        "_comment": ("#30: realized cost of an early K/DEF pick, by counterfactual surgery on one "
                     "draft. UPPER bound on the gain from deferring (the swapped-in player is not "
                     "removed from whoever really drafted him) and PESSIMISTIC about deferring "
                     "(no waivers, so the vacated slot stays empty). See counterfactual_cost.py."),
        "arm": ARM, "season": SEASON, "teams": TEAMS, "rounds": ROUNDS,
        "early_before_round": EARLY_BEFORE_ROUND,
        "early_kdst_picks_found": len(rows),
        "rows": rows,
    }
    if rows:
        deltas = [r["delta"] for r in rows]
        report["mean_delta"] = round(sum(deltas) / len(deltas), 2)
        report["helped_by_deferring"] = sum(1 for d in deltas if d > 0)
        report["hurt_by_deferring"] = sum(1 for d in deltas if d < 0)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(f"\n=== realized cost of an early K/DEF pick ({SEASON}, {ARM}) ===")
    print(f"early = before round {EARLY_BEFORE_ROUND} (bottom 25% of {ROUNDS})\n")
    if not rows:
        print("NO early K/DEF picks found -- nothing to counterfactual. That is a result, not an "
              "empty run: it would mean the engine already defers them.")
        return 0
    print(f"{'seat':>5}{'rd':>4}{'pos':>5}  {'drafted':<22}{'instead':<22}"
          f"{'actual':>10}{'counter':>10}{'delta':>9}")
    for r in rows:
        print(f"{r['seat']:>5}{r['round']:>4}{r['position']:>5}  {r['drafted'][:21]:<22}"
              f"{r['instead'][:21]:<22}{r['actual_total']:>10.1f}"
              f"{r['counterfactual_total']:>10.1f}{r['delta']:>9.1f}")
    print(f"\nmean delta from deferring: {report['mean_delta']:+.1f} realized points")
    print(f"deferring helped {report['helped_by_deferring']} of {len(rows)}, "
          f"hurt {report['hurt_by_deferring']}")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
