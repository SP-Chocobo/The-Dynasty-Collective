"""#184 CLASS MEASUREMENT: how far down does a change in starter demand actually reach?

READ-ONLY. Nothing here changes the engine; every perturbation is an in-process monkeypatch
applied to a copy of the committed behaviour and restored afterwards. Safe to run during a
VERIFICATION WINDOW -- the phase where the engine is held still so that the judgment "this is
ready to freeze" can be tested, which is not the same as having certified it frozen. That
distinction is the whole point of this instrument: it exists to find out whether the engine is
actually ready, and #184 is what it found when the answer was no.

THE QUESTION. #184 found that SUPER_FLEX_QB_SHARE moves starter demand, and that the demand
answer for QB is then never computed at all -- replacement_levels forks on startable_floors
BEFORE any price exists, so the cliff sets QB's price and demand sets nobody's. That is one
instance. This asks whether it is a CLASS: for each way of perturbing starter demand, how far
down the chain does the change survive?

    starter_slot_counts  ->  replacement_levels (real path)  ->  board bpa
         (demand)                  (the ruler)                    (the price)

A perturbation that moves demand but not bpa is a dead wire, whatever the reason. This reports
the depth each one reaches; it does NOT assume the cause is a floor.

CONTAMINATION CONTROLS, all three of the ones that already bit this investigation:
  * _ANCHOR_CACHE is cleared between arms -- anchor_cache_key covers every ARGUMENT but no
    module-level constant, so an unclear-ed in-process A/B serves arm 2 arm 1's anchor.
  * replacement_levels is called on the REAL path, with the startable_floors compute_draft_board
    would actually pass, not with floors=None (measuring the no-floor path is what made the
    first version of this look like the constant was live).
  * set_league_format before every format -- rec/bonus_rec_te propagate by FILE SELECTION, not
    through scoring_settings.
Absence is counted separately from zero throughout: a position with no rows is `n/a`, never 0.
"""
import collections, json, os, sys

import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

OUT = os.environ.get("DEMAND_REACH_OUT", "DEMAND_REACH_AUDIT.json")
POSITIONS = ("QB", "RB", "WR", "TE")


# ---------------------------------------------------------------- perturbations
# Each returns (label, apply_fn, restore_fn). apply_fn mutates module state; restore_fn undoes
# it exactly. None of them touch a file.

def perturb_sf_share(lo=0.85, hi=1.0):
    def make(v):
        def apply():
            dr.SUPER_FLEX_QB_SHARE = v
        return apply
    orig = dr.SUPER_FLEX_QB_SHARE
    return (f"SUPER_FLEX_QB_SHARE {lo} -> {hi}", make(lo), make(hi),
            lambda: setattr(dr, "SUPER_FLEX_QB_SHARE", orig))


def perturb_flex_split(skew_to="RB", heavy=0.80):
    """The FLEX even split (1/len(eligible)) has no named constant at all -- it is written
    inline. Perturbing it means replacing starter_slot_counts with a version that skews the
    plain-FLEX family toward one position, leaving SUPER_FLEX and named slots untouched."""
    real = dr.starter_slot_counts

    def build(skewed):
        def counts(roster_positions):
            out = {p: 0.0 for p in dr.FANTASY_POSITIONS}
            for slot in roster_positions or []:
                if slot in dr.FANTASY_POSITIONS:
                    out[slot] += 1.0
                elif slot == "SUPER_FLEX" and "QB" in dr.FLEX_SLOT_POSITIONS[slot]:
                    elig = dr.FLEX_SLOT_POSITIONS[slot]
                    non_qb = [p for p in elig if p != "QB"]
                    out["QB"] += dr.SUPER_FLEX_QB_SHARE
                    rest = (1.0 - dr.SUPER_FLEX_QB_SHARE) / len(non_qb) if non_qb else 0.0
                    for p in non_qb:
                        out[p] += rest
                elif slot in dr.FLEX_SLOT_POSITIONS:
                    elig = dr.FLEX_SLOT_POSITIONS[slot]
                    if skewed and skew_to in elig:
                        others = [p for p in elig if p != skew_to]
                        out[skew_to] += heavy
                        for p in others:
                            out[p] += (1.0 - heavy) / len(others) if others else 0.0
                    else:
                        for p in elig:
                            out[p] += 1.0 / len(elig)
            return out
        def apply():
            dr.starter_slot_counts = counts
        return apply

    return (f"FLEX split even -> {skew_to} {heavy}", build(False), build(True),
            lambda: setattr(dr, "starter_slot_counts", real))


# ---------------------------------------------------------------- the three layers

def demand_layer(league, teams):
    return dr.remaining_starter_demand(league.get("roster_positions") or [], teams, [], {})


def replacement_layer(merger, players_db, league, teams):
    """Exactly what compute_draft_board does, floors included."""
    rpos = league.get("roster_positions") or []
    up = dr.league_usable_positions(rpos)
    pool = dr.build_available_pool(merger, players_db, set(), up,
                                   scoring_settings=league.get("scoring_settings"),
                                   pool_scope="all")
    has = dr._derive_points_and_source(pool)
    proj = pool[has].copy()
    floors = None
    if "SUPER_FLEX" in rpos:
        f = dr.qb_startable_floor(merger)
        if f is not None:
            floors = {"QB": f}
    dem = dr.remaining_starter_demand(rpos, teams, [], {})
    return dr.replacement_levels(proj, "_points", rpos, teams, dem,
                                 startable_floors=floors), floors


def price_layer(merger, players_db, league):
    rows = dr.compute_draft_board(merger, players_db, [], "1", league)
    out = collections.defaultdict(list)
    for r in rows:
        if r.get("bpa") is not None:
            out[r.get("position")].append((str(r["player_id"]), r["bpa"]))
    return {p: dict(v) for p, v in out.items()}


def arm(merger, players_db, league, teams, apply):
    apply()
    dr._ANCHOR_CACHE.clear()
    d = demand_layer(league, teams)
    dr._ANCHOR_CACHE.clear()
    rep, floors = replacement_layer(merger, players_db, league, teams)
    dr._ANCHOR_CACHE.clear()
    price = price_layer(merger, players_db, league)
    return {"demand": d, "replacement": rep, "price": price, "floors": floors}


def compare(label, fmt, a, b):
    print(f"\n=== {label}   [{fmt}]   floors={a['floors']}", flush=True)
    print(f"{'pos':<5}{'demand':>18}{'replacement':>22}{'bpa rows moved':>18}", flush=True)
    rec = {}
    for p in POSITIONS:
        da, dbv = a["demand"].get(p), b["demand"].get(p)
        ra, rb = a["replacement"].get(p), b["replacement"].get(p)
        pa, pb = a["price"].get(p, {}), b["price"].get(p, {})
        shared = [k for k in pa if k in pb]
        moved = sum(1 for k in shared if pa[k] != pb[k])
        dmov = (da is not None and dbv is not None and da != dbv)
        rmov = (ra is not None and rb is not None and ra != rb)
        def show(x, y, mv):
            if x is None or y is None:
                return "n/a"                       # absence, not zero
            return f"{x:.2f}->{y:.2f}{'*' if mv else ''}"
        print(f"{p:<5}{show(da,dbv,dmov):>18}{show(ra,rb,rmov):>22}"
              f"{f'{moved}/{len(shared)}':>18}", flush=True)
        rec[p] = {"demand_moved": dmov, "replacement_moved": rmov,
                  "price_moved": moved, "price_n": len(shared),
                  "demand": [da, dbv], "replacement": [ra, rb]}
    # the verdict this instrument exists to produce
    for p in POSITIONS:
        r = rec[p]
        if r["demand_moved"] and r["price_n"] and r["price_moved"] == 0:
            print(f"  DEAD WIRE at {p}: demand moved, price did not "
                  f"(replacement {'moved' if r['replacement_moved'] else 'did NOT move'})",
                  flush=True)
    return rec


def main():
    merger = dm.DataMerger()
    # recorded_universe=True: this audit's published numbers are stated against the vendor
    # reconstruction, and re-pointing it at the capture would make a recorded experiment
    # describe something else under the same name (#201, #222's guard).
    players_db = rdb.build_players_db(merger, recorded_universe=True)
    matrix = {m["label"]: m for m in db.league_matrix()}
    report = {}

    plan = [
        ("12T_ppr_SF", perturb_sf_share()),      # control: the known dead wire
        ("12T_ppr",    perturb_flex_split()),    # 1QB + FLEX: does the split reach price?
        ("12T_ppr_SF", perturb_flex_split()),    # same split, alongside a floor
    ]
    for fmt, (label, lo, hi, restore) in plan:
        spec = matrix[fmt]
        league, teams = spec["league"], spec["teams"]
        merger.set_league_format(db.league_format_hint(league))   # never skip
        try:
            a = arm(merger, players_db, league, teams, lo)
            b = arm(merger, players_db, league, teams, hi)
            report[f"{fmt} :: {label}"] = compare(label, fmt, a, b)
        finally:
            restore()
            dr._ANCHOR_CACHE.clear()

    with open(OUT, "w") as fh:
        json.dump(report, fh, indent=2, default=str)
    print(f"\nwrote {OUT}", flush=True)


if __name__ == "__main__":
    main()
