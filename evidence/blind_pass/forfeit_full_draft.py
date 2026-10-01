"""Does the quantity that WOULD fix K/DST placement already exist, and does it say the right thing?

positional_forfeits' docstring states exactly the question K/DST placement turns on: "if I take
the other position now and come back to this one next turn, how much worse is the best player
I'll realistically find there?"  For a defense in round 8 the honest answer is "barely worse --
nobody else wants one."  If the engine already computes that and merely does not let it reach
the ordering, the fix is a wiring ruling, not an invention.

THE TRAP.  estimate_survival and positional_forfeits both read the INTERVENING OPPONENTS' OWN
BOARDS, built by this same engine.  If the engine overvalues defenses then every rival board
overvalues them too, the model predicts the defense will be taken, forfeit comes back HIGH, and
the machinery CONFIRMS the error instead of correcting it.  That is the thing to measure.

Uses simulate_full_draft -- the battery's own path, build_snapshot + candidates[0] -- and reads
the forfeit/survival the engine itself recorded, rather than recomputing them beside it.

Run from the REPO ROOT.
"""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
import collections, statistics
import data_merger as dm, draft_room as dr, draft_battery as dbat, run_draft_battery as rdb
import draft_simulation as dsim, player_universe as pu

merger = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture(); scoring = rdb.scoring_settings_from_capture()
arm = next(a for a in dbat.league_matrix(scoring) if a["label"] == "12T_ppr_K_DEF")
league, teams, rounds = arm["league"], arm["teams"], arm["rounds"]
merger.set_league_format(dbat.league_format_hint(league))
order = [(i % teams) + 1 if (i // teams) % 2 == 0 else teams - (i % teams)
         for i in range(teams * rounds)]

traj = dsim.simulate_full_draft(merger, players_db, league, order, mode="auto",
                                sleeper_projections=season,
                                sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
import json, pathlib
CACHE = pathlib.Path("/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/traj_control.json")
CACHE.write_text(json.dumps([{"pick_no": p.pick_no, "round": p.round, "roster_id": p.roster_id,
                              "pick_label": p.pick_label, "chosen": p.chosen_player_id,
                              "snapshot": p.snapshot} for p in traj.picks]))
print("picks made: %d of %d   (trajectory cached: %s)\n" % (len(traj.picks), teams * rounds, CACHE.name))

pos_of = lambda pid: pu.player_position(players_db.get(str(pid)) or {}) or "?"

print("=== when each position actually went ===")
by = collections.defaultdict(list)
for p in traj.picks:
    by[pos_of(p.chosen_player_id)].append(p.round)
print("%-6s%8s%10s%12s%10s" % ("pos", "taken", "first_rd", "median_rd", "last_rd"))
for pos in ("QB","RB","WR","TE","K","DEF"):
    r = by.get(pos)
    if r:
        print("%-6s%8d%10d%12.1f%10d" % (pos, len(r), min(r), statistics.median(r), max(r)))

# ---- the engine's own recorded forfeit/survival, per position, by round ----
def cands(rec):
    s = rec.snapshot or {}
    for key in ("candidates", "rows", "board"):
        if isinstance(s.get(key), list):
            return s[key]
    return []

sample = cands(traj.picks[0])
print("\nserialized candidate keys: %s" % (sorted(sample[0].keys()) if sample else "(none)"))

print("\n=== THE TRAP CHECK: forfeit and survival the ENGINE recorded, by position ===")
print("    (top candidate at each position, averaged over rounds 6-12)")
acc = collections.defaultdict(lambda: {"f": [], "s": [], "n": 0})
for p in traj.picks:
    if not (6 <= p.round <= 12):
        continue
    seen = set()
    for c in cands(p):
        pos = c.get("pos") or "?"
        if pos in seen:
            continue
        seen.add(pos)
        f, s = c.get("forfeit"), c.get("survival")
        if f is not None:
            acc[pos]["f"].append(float(f))
        if s is not None:
            acc[pos]["s"].append(float(s))
        acc[pos]["n"] += 1
print("%-6s%12s%14s%10s" % ("pos", "mean forfeit", "mean survival", "rows"))
for pos in ("RB","WR","TE","QB","K","DEF"):
    a = acc.get(pos)
    if not a or not a["n"]:
        print("%-6s%12s%14s%10s" % (pos, "—", "—", 0)); continue
    mf = statistics.fmean(a["f"]) if a["f"] else None
    msv = statistics.fmean(a["s"]) if a["s"] else None
    print("%-6s%12s%14s%10d" % (
        pos, "—" if mf is None else "%.2f" % mf,
        "—" if msv is None else "%.0f%%" % (100 * msv), a["n"]))

print("\n=== THE ORDERING GAP: board's pick vs the position forfeit ranked highest ===")
print("%-8s%-22s%-6s%10s   %-8s%10s" % ("pick", "board took", "pos", "forfeit", "urgent", "forfeit"))
mismatch = 0
for p in traj.picks:
    rows = cands(p)
    if not rows:
        continue
    took = next((c for c in rows if str(c.get("id")) == str(p.chosen_player_id)), None)
    best = {}
    for c in rows:
        f, q = c.get("forfeit"), c.get("pos")
        if f is not None and q and q not in best:
            best[q] = float(f)
    if not took or took.get("forfeit") is None or not best:
        continue
    urgent = max(best, key=best.get)
    if urgent != took.get("pos"):
        mismatch += 1
        if p.round in (5, 7, 9, 11) and mismatch % 3 == 1:
            print("%-8s%-22s%-6s%10.2f   %-8s%10.2f" % (
                p.pick_label, (took.get("name") or "?")[:21], took.get("pos"),
                float(took["forfeit"]), urgent, best[urgent]))
print("picks where the board's position was NOT the most urgent one: %d of %d"
      % (mismatch, len(traj.picks)))

print("\n=== the round the first DEF/K went, and what the board said there ===")
for pos in ("DEF", "K"):
    first = next((p for p in traj.picks if pos_of(p.chosen_player_id) == pos), None)
    if first is None:
        print("  %s: never taken" % pos); continue
    row = next((c for c in cands(first)
                if str(c.get("id")) == str(first.chosen_player_id)),
               None)
    print("  %s taken at %s (round %d)" % (pos, first.pick_label, first.round))
    if row:
        for k in ("tav", "uv", "proj", "forfeit", "survival", "necessity", "necClass", "rivalPremium"):
            if k in row:
                print("      %-14s %s" % (k, row[k]))
