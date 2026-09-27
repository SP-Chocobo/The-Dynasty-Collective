"""Grade the engine's VDS rosters against two best-available chairs, on the PROJECTED weekly ruler.

Pre-registered in evidence/design_35/PREREGISTRATION_VDS_READING.md. Read that first: this cannot
show the engine picks better players than a best-available chair (both draft off the same
projections). It shows whether the engine turns the same numbers into a more fieldable, higher-
scoring season of lineups.

THE RULER is realized_ruler.score_roster_realized fed PROJECTED weekly lines instead of realized
ones -- the same optimizer production fields, solved per week so a bye or a hole is covered from
the bench rather than assumed away. One difference from the realized case, stated because it
changes what the absence contract means here: a bye week in the projection lines is a PRESENT
line worth 0.0, not an absent one. It does not change the solve, which maximises: a positive
backup is started over a 0.0 starter either way. It does mean "weeks_scored" is 18 for everyone.

THE POOL both chairs draft from is the engine's own pool at pick 1 (build_available_pool with no
picks), so a baseline can never take a player the engine could not see -- the anachronism guard
(#31) and _admits_to_pool's five clauses apply to all three chairs identically.
"""
import json, collections, os, sys
assert os.path.basename(os.getcwd()) == "The-Dynasty-Collective", os.getcwd()
sys.path.insert(0, os.getcwd())
import run_draft_battery as rdb, draft_battery as db, vds_battery as vb
import data_merger as dm, draft_room as dr, draft_strategy as ds
import lineup_optimizer as lo, player_universe as pu, realized_ruler as rr

SHARP = ["sharp_auto", "sharp_balanced", "sharp_upside", "crossing"]

scoring = rdb.scoring_settings_from_capture()
players_db, _ = rdb.build_players_db_from_capture()
season_projections = rdb.season_projections_from_capture()
weekly = rr.weekly_points(rdb.weekly_projections_from_capture(), scoring)
merger = dm.DataMerger()
rep = json.load(open("evidence/batteries/VDS_2026-09-26_varied_drafting_strategy_04bccb5.json"))
arms = {a["label"]: a for a in rep["results"]}
# league_matrix, not vds_matrix: the latter is keyed by ARM (format__strategy). Keying a
# format lookup off arm labels is what raised KeyError on the first run.
matrix = {e["label"]: e for e in db.league_matrix(scoring)}


def eligible_of(pid):
    info = players_db.get(str(pid)) or {}
    return set(info.get("fantasy_positions") or
               ([info["position"]] if info.get("position") else []))


def pick1_pool(entry):
    merger.set_league_format(db.league_format_hint(entry["league"]))
    usable = pu.league_usable_positions(entry["league"].get("roster_positions") or [])
    pool = dr.build_available_pool(
        merger, players_db, set(), usable,
        sleeper_projections=season_projections, scoring_settings=entry["league"].get("scoring_settings"),
        sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    # `_points` is not a pool column -- it is derived downstream, and the first run of this
    # instrument died on KeyError('_points') for assuming otherwise. Derived here through the
    # board's OWN function so a baseline ranks on exactly the number the engine priced from,
    # rather than on a second reading of `projection` vs `sleeper_points` that could drift (#180).
    dr._derive_points_and_source(pool)
    return pool


def bpa_draft(pool, entry, order, need_aware: bool):
    """raw_bpa: highest projection, position-blind. sane_bpa: best player at a position whose
    STARTING slot this roster has not covered yet, else best available overall."""
    slots = lo.slots_from_roster_positions(entry["league"].get("roster_positions") or [])
    # NOT itertuples: it renames a leading-underscore column to a positional name, so
    # `r._points` raised AttributeError('_points') on a frame that has the column. Zip the two
    # series instead. NaN is dropped rather than treated as 0.0 (#187): an unpriced row is a row
    # no best-available rule can rank, not a row worth nothing.
    ordered = pool.sort_values("_points", ascending=False)
    ranked = [(str(pid), float(pts))
              for pid, pts in zip(ordered["player_id"], ordered["_points"])
              if pts == pts]
    taken, rosters = set(), collections.defaultdict(list)
    demand = {}
    for rid in set(order):
        demand[rid] = [set(s.get("eligible") or ()) for s in slots]
    for rid in order:
        chosen = None
        if need_aware and demand[rid]:
            for pid, _pts in ranked:
                if pid in taken:
                    continue
                elig = eligible_of(pid)
                hit = next((i for i, need in enumerate(demand[rid]) if elig & need), None)
                if hit is not None:
                    demand[rid].pop(hit)
                    chosen = pid
                    break
        if chosen is None:
            chosen = next(pid for pid, _ in ranked if pid not in taken)
        taken.add(chosen)
        rosters[rid].append(chosen)
    return rosters


def score(rosters, entry):
    slots = lo.slots_from_roster_positions(entry["league"].get("roster_positions") or [])
    return {rid: rr.score_roster_realized(ids, players_db, weekly, slots)
            for rid, ids in rosters.items()}


out = {"_doc": __doc__, "formats": {}}
for fmt, entry in [(f, matrix[f]) for f in vb.FORMATS]:
    rids = [str(i) for i in range(1, entry["teams"] + 1)]
    order = ds.generate_pick_order(rids, entry["rounds"], "snake")
    pool = pick1_pool(entry)
    base = {}
    for name, need_aware in (("raw_bpa", False), ("sane_bpa", True)):
        r = bpa_draft(pool, entry, order, need_aware)
        base[name] = {"rosters": {k: list(v) for k, v in r.items()}, "scored": score(r, entry)}
    rec = {"teams": entry["teams"], "rounds": entry["rounds"], "baselines": {}, "engine": {}}
    for name in ("raw_bpa", "sane_bpa"):
        s = base[name]["scored"]
        rec["baselines"][name] = {"per_seat": {k: v["total"] for k, v in s.items()},
                                  "mean": round(sum(v["total"] for v in s.values()) / len(s), 2)}
    for strat in SHARP:
        label = f"{fmt}__{strat}"
        arm = arms[label]
        eng = collections.defaultdict(list)
        for rid, pid in zip(order, arm["pick_sequence"]):
            eng[rid].append(str(pid))
        s = score(eng, entry)
        rec["engine"][strat] = {
            "per_seat": {k: v["total"] for k, v in s.items()},
            "mean": round(sum(v["total"] for v in s.values()) / len(s), 2),
            "never_started_mean": round(sum(v["players_who_never_started"]
                                            for v in s.values()) / len(s), 2),
            "identical_to_raw_bpa": {k: list(v) for k, v in eng.items()} == base["raw_bpa"]["rosters"],
            "identical_to_sane_bpa": {k: list(v) for k, v in eng.items()} == base["sane_bpa"]["rosters"],
        }
        for name in ("raw_bpa", "sane_bpa"):
            b = base[name]["scored"]
            deltas = {rid: round(s[rid]["total"] - b[rid]["total"], 2) for rid in s}
            rec["engine"][strat][f"vs_{name}"] = {
                "per_seat_delta": deltas,
                "mean_delta": round(sum(deltas.values()) / len(deltas), 2),
                "seats_ahead": sum(1 for d in deltas.values() if d > 0),
                "seats_behind": sum(1 for d in deltas.values() if d < 0),
                "seats_tied": sum(1 for d in deltas.values() if d == 0),
            }
    rec["baselines"]["raw_bpa"]["never_started_mean"] = round(
        sum(v["players_who_never_started"] for v in base["raw_bpa"]["scored"].values()) / entry["teams"], 2)
    rec["baselines"]["sane_bpa"]["never_started_mean"] = round(
        sum(v["players_who_never_started"] for v in base["sane_bpa"]["scored"].values()) / entry["teams"], 2)
    out["formats"][fmt] = rec
    print(f"{fmt:22} raw_bpa {rec['baselines']['raw_bpa']['mean']:>9.1f}  "
          f"sane_bpa {rec['baselines']['sane_bpa']['mean']:>9.1f}", flush=True)
    for strat in SHARP:
        e = rec["engine"][strat]
        print(f"   {strat:16} {e['mean']:>9.1f}  vs_raw {e['vs_raw_bpa']['mean_delta']:>+9.1f} "
              f"({e['vs_raw_bpa']['seats_ahead']}/{entry['teams']})  "
              f"vs_sane {e['vs_sane_bpa']['mean_delta']:>+9.1f} "
              f"({e['vs_sane_bpa']['seats_ahead']}/{entry['teams']})", flush=True)

path = "evidence/design_35/VDS_BPA_PROJECTED_RULER.json"
with open(path, "w") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
print("wrote", path)
