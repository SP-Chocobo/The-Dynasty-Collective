"""THE COUNTERFACTUAL that decides whether the forfeit model is circular.

forfeit_fast.py measured DEF forfeit at 1.16 -- the right answer -- but in a state where the
engine had ALREADY taken 11 of 32 defenses, so league demand was nearly exhausted and no
opponent wanted one. Low forfeit there proves nothing about the model: it could be reading
"nobody needs a defense any more" rather than "nobody ever wants one here".

So run the same turn from a state where NO kicker or defense has been taken: all 32 defenses
on the board, all 12 teams still needing one. If forfeit for DEF comes back LOW there, the
model genuinely knows deferring is cheap and the circularity fear is unfounded. If it comes
back HIGH, every rival board wants the defense because every rival board is this same engine,
and the model confirms the error it was meant to correct.

Board state is generated the cheap way (compute_draft_board top-1, skipping K and DEF) rather
than through build_snapshot; the MEASUREMENT still goes through build_snapshot.

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
    # THE COUNTERFACTUAL: no chair may take a K or a DEF, so both pools arrive untouched and
    # league demand at both is still full when the turn below is measured.
    pick = next((r for r in b if pos_of(r["player_id"]) not in ("K", "DEF")), None)
    if pick is None:
        break
    picks.append({"player_id": pick["player_id"], "roster_id": order[i], "pick_no": i + 1})

i, rnd, gap = STOP
taken = collections.Counter(pos_of(p["player_id"]) for p in picks)
print("state: %d picks in, round %d, %d intervening picks AHEAD of this turn" % (len(picks), rnd, gap))
print("positions already gone: %s" % dict(sorted(taken.items())))
print("K/DEF suppressed -- both pools untouched, league demand at both still full\n")

snap = ps.build_snapshot(merger, players_db, picks, order, i, ME, league,
                         pick_label="%d.01" % rnd, mode="auto",
                         sleeper_projections=season,
                         sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)

print("=== the FULL decomposition of the new ordering key ===")
print("%-22s%-5s%9s%9s%9s%9s%9s%9s%10s" % (
    "player", "pos", "actNOW", "tav", "uv", "need", "elig", "forfeit", "best_now"))
f = lambda v: "—" if v is None else "%.2f" % v
for c in snap.candidates[:20]:
    print("%-22s%-5s%9s%9s%9s%9s%9s%9s%10s" % (
        (c.name or "?")[:21], pos_of(c.player_id), f(c.acting_now_value),
        f(c.team_acquisition_value), f(c.universal_value), f(c.need_bonus),
        f(c.eligibility_bonus), f(c.positional_forfeit), f(c.position_best_now)))

print()
print("=== what the team-specific terms are doing, by position ===")
print("%-6s%10s%10s%10s%10s" % ("pos", "n", "mean need", "mean elig", "mean depth"))
import collections, statistics
agg = collections.defaultdict(lambda: {"need": [], "elig": [], "depth": []})
for c in snap.candidates:
    p = pos_of(c.player_id)
    agg[p]["need"].append(c.need_bonus or 0.0)
    agg[p]["elig"].append(c.eligibility_bonus or 0.0)
    if c.depth_exposure is not None:
        agg[p]["depth"].append(c.depth_exposure)
for p in ("RB","WR","TE","QB","K","DEF"):
    a = agg.get(p)
    if not a or not a["need"]:
        continue
    m = lambda xs: "—" if not xs else "%.2f" % statistics.fmean(xs)
    print("%-6s%10d%10s%10s%10s" % (p, len(a["need"]), m(a["need"]), m(a["elig"]), m(a["depth"])))

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
