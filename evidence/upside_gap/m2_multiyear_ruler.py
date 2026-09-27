"""M2 — does sharp_upside improve the multi-year metric it claims to target?

Pre-registered in evidence/upside_gap/PREREGISTRATION.md. Run from the REPO ROOT. No re-drafting:
the rosters are reconstructed from the committed VDS arms' own `pick_sequence`.

THE RULER is `proj_3yr` -- Draft Sharks' own three-year outlook, the number `upside_score`'s growth
term is derived from (as a percentile) and the only multi-year quantity this repository has. Two
readings per roster, because "a better starting lineup three years out" and "better assets held" are
different claims and an upside strategy might mean either:

  - `lineup_3yr`  -- the best legal STARTING lineup under proj_3yr, one solve.
  - `roster_3yr`  -- the sum over every player held, fieldable or not.

LIMITS, stated rather than discovered later:
  - proj_3yr is season-total-shaped. There are no weekly three-year lines, so this is ONE solve, not
    a weekly one: it cannot see absences and therefore cannot reward depth the way the realized
    weekly ruler does. It is not the projected weekly ruler with a different column; it is a
    different, coarser ruler.
  - proj_3yr is a VENDOR column and the vendor does not cover K, DEF or IDP. A player without one is
    ABSENT from the solve, never 0.0 (#187) -- so on IDP and K/DEF formats these numbers are about
    the offensive core only, and coverage is reported per arm so a reader can see that rather than
    infer it.
  - proj_3yr comes from the rankings export `set_league_format` selects, so it is read per format.
"""
import collections, json, os, sys

assert os.path.basename(os.getcwd()) == "The-Dynasty-Collective", os.getcwd()
sys.path.insert(0, os.getcwd())

import run_draft_battery as rdb, draft_battery as db, vds_battery as vb
import data_merger as dm, draft_room as dr, draft_strategy as ds
import lineup_optimizer as lo, player_universe as pu

SHARP = ["sharp_auto", "sharp_balanced", "sharp_upside", "crossing"]

scoring = rdb.scoring_settings_from_capture()
players_db, _ = rdb.build_players_db_from_capture()
season_projections = rdb.season_projections_from_capture()
merger = dm.DataMerger()
rep = json.load(open("evidence/batteries/VDS_2026-09-26_varied_drafting_strategy_04bccb5.json"))
arms = {a["label"]: a for a in rep["results"]}
matrix = {e["label"]: e for e in db.league_matrix(scoring)}


def eligible_of(pid):
    info = players_db.get(str(pid)) or {}
    return set(info.get("fantasy_positions") or
               ([info["position"]] if info.get("position") else []))


out = {"_doc": __doc__, "formats": {}}
for fmt in vb.FORMATS:
    entry = matrix[fmt]
    league = entry["league"]
    merger.set_league_format(db.league_format_hint(league))
    usable = pu.league_usable_positions(league.get("roster_positions") or [])
    pool = dr.build_available_pool(
        merger, players_db, set(), usable, sleeper_projections=season_projections,
        scoring_settings=league.get("scoring_settings"),
        sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    three = {str(pid): float(v) for pid, v in zip(pool["player_id"], pool["proj_3yr"]) if v == v}
    slots = lo.slots_from_roster_positions(league.get("roster_positions") or [])
    rids = [str(i) for i in range(1, entry["teams"] + 1)]
    order = ds.generate_pick_order(rids, entry["rounds"], "snake")

    rec = {"pool_rows": int(len(pool)), "pool_with_proj_3yr": len(three), "arms": {}}
    for strat in SHARP:
        seq = arms[f"{fmt}__{strat}"]["pick_sequence"]
        rosters = collections.defaultdict(list)
        for rid, pid in zip(order, seq):
            rosters[rid].append(str(pid))
        per_seat_lineup, per_seat_roster, covered = {}, {}, {}
        for rid, ids in rosters.items():
            avail = [{"id": p, "value": three[p], "eligible": eligible_of(p)}
                     for p in ids if p in three]
            covered[rid] = len(avail)
            per_seat_lineup[rid] = round(lo.optimize_lineup(avail, slots)["total_value"], 2) if avail else None
            per_seat_roster[rid] = round(sum(a["value"] for a in avail), 2) if avail else None
        rec["arms"][strat] = {
            "lineup_3yr_per_seat": per_seat_lineup,
            "roster_3yr_per_seat": per_seat_roster,
            "lineup_3yr_mean": round(sum(per_seat_lineup.values()) / len(per_seat_lineup), 2),
            "roster_3yr_mean": round(sum(per_seat_roster.values()) / len(per_seat_roster), 2),
            "players_with_proj_3yr_mean": round(sum(covered.values()) / len(covered), 2),
            "players_held": entry["rounds"],
        }
    base = rec["arms"]["sharp_auto"]
    for strat in SHARP:
        a = rec["arms"][strat]
        dl = {rid: round(a["lineup_3yr_per_seat"][rid] - base["lineup_3yr_per_seat"][rid], 2)
              for rid in rids}
        dr_ = {rid: round(a["roster_3yr_per_seat"][rid] - base["roster_3yr_per_seat"][rid], 2)
               for rid in rids}
        a["vs_sharp_auto"] = {
            "lineup_mean_delta": round(sum(dl.values()) / len(dl), 2),
            "lineup_seats_ahead": sum(1 for v in dl.values() if v > 0),
            "roster_mean_delta": round(sum(dr_.values()) / len(dr_), 2),
            "roster_seats_ahead": sum(1 for v in dr_.values() if v > 0),
        }
    out["formats"][fmt] = rec
    print(f"{fmt:22} pool={rec['pool_rows']} with_3yr={rec['pool_with_proj_3yr']}", flush=True)
    for strat in SHARP:
        a = rec["arms"][strat]
        v = a["vs_sharp_auto"]
        print(f"   {strat:15} lineup {a['lineup_3yr_mean']:>9.1f} ({v['lineup_mean_delta']:>+8.1f}, "
              f"{v['lineup_seats_ahead']}/{entry['teams']})   roster {a['roster_3yr_mean']:>9.1f} "
              f"({v['roster_mean_delta']:>+8.1f}, {v['roster_seats_ahead']}/{entry['teams']})   "
              f"covered {a['players_with_proj_3yr_mean']:>5.2f}/{a['players_held']}", flush=True)

path = "evidence/upside_gap/M2_MULTIYEAR_RULER.json"
with open(path, "w") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
print("wrote", path)
