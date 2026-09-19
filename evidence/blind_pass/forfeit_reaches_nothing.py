"""PRELIMINARY. Same question as forfeit_says.py, one turn instead of a whole draft.

The board STATE here is generated the cheap way (compute_draft_board top-1 per pick) rather
than through build_snapshot, so this is NOT the battery's draft and must not be reported as
one. The MEASUREMENT at the target turn still goes through build_snapshot, because forfeit and
survival are properties of the remaining pool and the intervening opponents, which a slightly
different route to a similar state does not move much. The authoritative number is the full
simulate_full_draft run; this exists to fail fast if the answer is obvious.

Run from the REPO ROOT.
"""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
import collections
import data_merger as dm, draft_room as dr, draft_battery as dbat, run_draft_battery as rdb
import pick_synthesis as ps, player_universe as pu

merger = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture(); scoring = rdb.scoring_settings_from_capture()
arm = next(a for a in dbat.league_matrix(scoring) if a["label"] == "12T_ppr_K_DEF")
league, teams, rounds = arm["league"], arm["teams"], arm["rounds"]
merger.set_league_format(dbat.league_format_hint(league))
order = [(i % teams) + 1 if (i // teams) % 2 == 0 else teams - (i % teams)
         for i in range(teams * rounds)]
pos_of = lambda pid: pu.player_position(players_db.get(str(pid)) or {}) or "?"

ME, STOP = 1, None
picks = []
for i in range(teams * rounds):
    if order[i] == ME and i // teams + 1 >= 8:
        nxt = next((j for j in range(i + 1, len(order)) if order[j] == ME), None)
        if nxt is not None and nxt - i > 1:
            STOP = (i, i // teams + 1, nxt - i - 1)
            break
    b = dr.compute_draft_board(merger, players_db, picks, my_roster_id=order[i], league=league,
                               mode="auto", sleeper_projections=season,
                               sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    if not b:
        break
    picks.append({"player_id": b[0]["player_id"], "roster_id": order[i], "pick_no": i + 1})

i, rnd, gap = STOP
taken = collections.Counter(pos_of(p["player_id"]) for p in picks)
print("state: %d picks in, round %d, %d intervening picks AHEAD of this turn" % (len(picks), rnd, gap))
print("positions already gone: %s\n" % dict(sorted(taken.items())))

snap = ps.build_snapshot(merger, players_db, picks, order, i, ME, league,
                         pick_label="%d.01" % rnd, mode="auto",
                         sleeper_projections=season,
                         sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)

print("=== what the engine is choosing between at this turn ===")
print("%-24s%-6s%10s%12s%12s" % ("player", "pos", "final", "forfeit", "survival"))
for c in snap.candidates[:14]:
    f = lambda v: "—" if v is None else "%.2f" % v
    pct = lambda v: "—" if v is None else "%.0f%%" % (100 * v)
    print("%-24s%-6s%10s%12s%12s" % ((c.name or "?")[:23], pos_of(c.player_id),
          f(getattr(c, "team_acquisition_value", None)), f(c.positional_forfeit),
          pct(c.survival_probability)))

print("\n=== THE TRAP CHECK: forfeit per position (best candidate at each) ===")
print("%-6s%12s%12s   %s" % ("pos", "forfeit", "survival", "top candidate"))
seen = {}
for c in snap.candidates:
    p = pos_of(c.player_id)
    if p not in seen:
        seen[p] = c
for pos in ("RB", "WR", "TE", "QB", "K", "DEF"):
    c = seen.get(pos)
    if c is None:
        print("%-6s%12s%12s   %s" % (pos, "—", "—", "(not among candidates)")); continue
    print("%-6s%12s%12s   %s" % (
        pos, "—" if c.positional_forfeit is None else "%.2f" % c.positional_forfeit,
        "—" if c.survival_probability is None else "%.0f%%" % (100 * c.survival_probability),
        c.name))
