"""WHY does superflex QB get deferred? Two candidate mechanisms, and they need different fixes.

The repair costs 2.4% of lineup points in 10T_ppr_SF (vs 0.5% in 12T_ppr), and rosters finish
with one QB where they used to finish with two or three. acting_now_value defers QB because
positional_forfeit is small. forfeit = best_now - curve_at(expected_taken), so it is small for
exactly one of two reasons:

  (1) EXPECTED_TAKEN IS TOO LOW -- the take model does not know that a superflex league wants
      two QBs per team, so it predicts few QBs will go before my next turn. Then the defect is
      in the survival/take model, not in acting_now, and the fix is there.
  (2) EXPECTED_TAKEN IS FINE AND THE CURVE IS JUST FLAT -- the model correctly predicts many
      QBs will go, and walking down that many still costs little because QB1..QB20 spans only
      ~68 points. Then acting_now is reading a true fact and the defect is that a flat curve
      cannot express "you may end up with NONE", which is a different repair.

These are distinguishable by measurement, so measure rather than pick.

Run from the REPO ROOT.
"""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
import collections
import data_merger as dm, draft_room as dr, draft_battery as dbat, run_draft_battery as rdb
import pick_synthesis as ps, player_universe as pu

merger = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture(); scoring = rdb.scoring_settings_from_capture()
arm = next(a for a in dbat.league_matrix(scoring) if a["label"] == "10T_ppr_SF")
league, teams, rounds = arm["league"], arm["teams"], arm["rounds"]
merger.set_league_format(dbat.league_format_hint(league))
print("roster_positions: %s" % " ".join(league["roster_positions"]))
slots = dr.starter_slot_counts(league["roster_positions"], None, teams)
print("starter slots per team: %s" % {k: v for k, v in slots.items() if v})
print("LEAGUE-WIDE QB starter demand: %.1f" % (teams * slots.get("QB", 0)))

order = [(i % teams) + 1 if (i // teams) % 2 == 0 else teams - (i % teams)
         for i in range(teams * rounds)]
ME = 1
picks = []
for i in range(teams * rounds):
    if order[i] == ME and i // teams + 1 in (3, 5, 7):
        nxt = next((j for j in range(i + 1, len(order)) if order[j] == ME), None)
        if nxt is None or nxt - i <= 1:
            continue
        snap = ps.build_snapshot(merger, players_db, picks, order, i, ME, league,
                                 pick_label="%d.x" % (i // teams + 1), mode="auto",
                                 sleeper_projections=season,
                                 sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        gone = collections.Counter(pu.player_position(players_db.get(str(p["player_id"])) or {})
                                   for p in picks)
        seen = {}
        for c in snap.candidates:
            pos = pu.player_position(players_db.get(str(c.player_id)) or {})
            if pos and pos not in seen:
                seen[pos] = c
        print("\n=== round %d, %d intervening picks ahead, QBs already gone: %d ==="
              % (i // teams + 1, nxt - i - 1, gone.get("QB", 0)))
        print("  %-5s%14s%12s%12s%14s" % ("pos", "expected_taken", "forfeit", "best_now", "acting_now"))
        for pos in ("QB", "RB", "WR", "TE"):
            c = seen.get(pos)
            if not c:
                continue
            f = lambda v: "-" if v is None else "%.2f" % v
            print("  %-5s%14s%12s%12s%14s" % (pos, f(c.position_expected_taken),
                  f(c.positional_forfeit), f(c.position_best_now), f(c.acting_now_value)))
    b = dr.compute_draft_board(merger, players_db, picks, my_roster_id=order[i], league=league,
                               mode="auto", sleeper_projections=season,
                               sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    if not b:
        break
    picks.append({"player_id": b[0]["player_id"], "roster_id": order[i], "pick_no": i + 1})
