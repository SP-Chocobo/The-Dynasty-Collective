"""Where would a REPLACEMENT-CROSSING mode boundary fire, against where round 15 fires?

THE QUESTION, in the owner's words: "if a league never pulls from the deep reserves, then I
don't mind it not reaching for upside mode. If you're still pulling valid decent depth, who
cares." That is a rule about the MARGINAL PICK, not about the calendar -- upside mode should
begin when the best thing left stops being depth and starts being a reserve.

Round 15 fails that rule by its own evidence. Measured across the 34-arm Gate 1 battery
(2026-09-13), bench value per bench seat against whether upside fires:

    8T_standard_SF   +8.8/seat   FIRES      <- bench is ABOVE replacement
    8T_half_ppr_SF   +3.8/seat   FIRES
    8T_ppr_SF        +2.9/seat   FIRES
    14T_ppr         -47.8/seat   never      <- 3rd deepest in the matrix
    14T_half_ppr    -42.7/seat   never
    F&F capture     -86.8/seat   FIRES

Arms that fire average -27.0/seat; arms that never fire average -33.4. The leagues entering
upside mode have SHALLOWER reserves than the ones that do not. The mechanism is mundane:
superflex rosters carry one more starting slot, so superflex drafts run 15 rounds and 1QB run
14 -- round 15 is close to a superflex detector, and superflex benches are better because the
extra starting slot absorbs a premium player.

WHAT THIS PROBE MEASURES. For one seat, in each format, a REAL draft is simulated (not a
synthetic picks array -- #221 was withdrawn because a fixture-shaped picks list faked the
drain). At each of that seat's turns the board is rebuilt from `picks[:i]`, so the board state
matches the turn, and we record:

  max_bpa       the best `bpa` on the board -- points minus that position's LIVE replacement
                level. This is the candidate quantity the owner's rule is about.
  n_above       how many candidates price above replacement at all.
  round15       what the current switch would say at this turn.

CAVEAT THE PROBE CANNOT ESCAPE, stated because it bounds the answer: `bpa` is points minus a
per-position replacement level, and the replacement-level player prices at 0.00 TAUTOLOGICALLY
(#155). So `max_bpa < 0` may be rare or unreachable by construction -- if it never fires, that
is a finding about the quantity, not a null result about the rule, and the rule would need a
different observable. Reported either way; `n_above` is printed separately from `max_bpa` so
"no candidate above replacement" and "a candidate at exactly 0.00" stay distinguishable.

Run from the repo root:  PYTHONPATH=. python3 evidence/mode_boundary/where_would_it_fire.py
"""
from __future__ import annotations

import json
import sys
import time

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_simulation as ds
import draft_strategy as dstrat
import run_draft_battery as rdb

# Four formats spanning the measured depth range, so the answer is not read off one league.
WANTED = ("8T_standard_SF",              # +8.8/seat  -- shallowest, currently FIRES
          "12T_ppr",                     # -37.4/seat -- middle, never fires
          "14T_ppr",                     # -47.8/seat -- deep, never fires
          "CAPTURE_fourth_and_forever")  # -86.8/seat -- deepest, fires
SEAT = "1"


def main() -> int:
    t0 = time.time()
    merger = dm.DataMerger()
    # NOT build_players_db: that is the VENDOR RECONSTRUCTION (764 rows, no injury_status, an
    # id space that only coincidentally overlaps the real one) and run_draft_battery REFUSES it
    # for new work while the capture exists (#201/#204/#222). The first draft of this probe
    # called it and the guard caught it -- not because the engine-measurement skill is stale
    # (SKILL.md:26 and :39-47 already say exactly this) but because the author worked from a
    # remembered fixture instead of reading the file. The guard is doing the job the skill's
    # prose alone could not.
    players_db, prov = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    print(f"universe: {prov['players_in_pool']}  season projections: {len(season)}", flush=True)
    matrix = {e["label"]: e for e in db.league_matrix(rdb.scoring_settings_from_capture())}

    report = {}
    for label in WANTED:
        entry = matrix[label]
        league, teams, rounds = entry["league"], entry["teams"], entry["rounds"]
        merger.set_league_format(db.league_format_hint(league))   # NEVER SKIP (#150)

        roster_ids = [str(i) for i in range(1, teams + 1)]
        order = dstrat.generate_pick_order(roster_ids, rounds, "snake")
        traj = ds.simulate_full_draft(
            merger, players_db, league, order, config_label=label,
            sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)

        picks = [{"roster_id": str(p.roster_id), "player_id": str(p.chosen_player_id),
                  "round": i // teams + 1} for i, p in enumerate(traj.picks)]

        turns = []
        for i, p in enumerate(picks):
            if p["roster_id"] != SEAT:
                continue
            board = dr.compute_draft_board(
                merger, players_db, picks[:i], my_roster_id=SEAT, league=league,
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
            # compute_draft_board returns a LIST OF RECORDS (draft_room.py:3401
            # `_records_with_normalized_nan`), not a DataFrame. The first draft of this probe
            # called .empty/.columns on it and crashed -- assumed shape, did not check.
            rows = board or []
            bpa = [r["bpa"] for r in rows
                   if isinstance(r, dict) and r.get("bpa") is not None]
            # #240/skill: count `is not None` and `> 0` SEPARATELY. "nothing measurable" and
            # "measured at or below zero" are different facts and must not collapse.
            turns.append({"round": p["round"],
                          "max_bpa": round(float(max(bpa)), 2) if bpa else None,
                          "n_rows": len(rows),
                          "n_priced": len(bpa),
                          "n_above": sum(1 for v in bpa if v > 0)})

        report[label] = {"teams": teams, "rounds": rounds, "turns": turns}
        crossing = next((t["round"] for t in turns
                         if t["max_bpa"] is not None and t["max_bpa"] <= 0), None)
        r15 = 15 if rounds >= 15 else None
        print(f"{label:<28} rounds={rounds:>3}  round15->{str(r15):>5}  "
              f"replacement-crossing->{str(crossing):>5}", flush=True)
        for t in turns:
            print(f"    r{t['round']:>2}  max_bpa={str(t['max_bpa']):>9}  "
                  f"above_replacement={str(t.get('n_above')):>5} of {str(t.get('n_priced')):>5}",
                  flush=True)

    report["elapsed_s"] = round(time.time() - t0, 1)
    with open("evidence/mode_boundary/where_would_it_fire.json", "w") as fh:
        json.dump(report, fh, indent=1)
    print(f"\nwrote evidence/mode_boundary/where_would_it_fire.json  "
          f"({report['elapsed_s']}s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
