"""Did pushing K and DST to the back of the draft leave anyone unable to field a lineup?

THE RISK THE REPAIR CREATES. Median DEF moved to round 15 and median K to 14.5 in a SIXTEEN
round draft. A chair that keeps deferring a position it only ever needs one of can run out of
picks holding none -- which is #154's defect exactly ("10T_half_ppr roster 2 empty QB 7/8"),
and the one failure mode that makes a roster undraftable rather than merely suboptimal.

feasibility_first survives as _acting_now_order's leading term, so the backstop still binds --
but it binds only when a roster has as few picks LEFT as it has unfillable named slots, so a
roster can drift most of the way there before anything fires.

Uses the battery's own unfilled_starting_slots (the real assignment solve, not a positional
tally -- a naive count gets FLEX chains wrong) against both cached trajectories.

Run from the REPO ROOT.
"""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
import json, types, collections
import draft_battery as dbat, run_draft_battery as rdb, player_universe as pu

SC = "/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/"
players_db, _ = rdb.build_players_db_from_capture()
scoring = rdb.scoring_settings_from_capture()
arm = next(a for a in dbat.league_matrix(scoring) if a["label"] == "12T_ppr_K_DEF")
league = arm["league"]

for name, label in (("traj_control.json", "before"), ("traj_treatment.json", "after")):
    picks = json.load(open(SC + name))
    # unfilled_starting_slots reads trajectory.picks[*].roster_id / .chosen_player_id, so a
    # light stand-in carrying exactly those is honest here; the solve is the battery's own.
    # final_rosters is a plain derived read of .picks in the real class; reuse DraftTrajectory's
    # own method rather than reimplementing the derivation here (#126).
    import draft_simulation as dsim
    traj = types.SimpleNamespace(
        picks=[types.SimpleNamespace(roster_id=str(p["roster_id"]),
                                     chosen_player_id=str(p["chosen"]),
                                     pick_no=p["pick_no"], round=p["round"])
               for p in picks])
    traj.final_rosters = dsim.DraftTrajectory.final_rosters.__get__(traj)
    holes = dbat.unfilled_starting_slots(traj, league, players_db)
    counts = collections.Counter(pu.player_position(players_db.get(str(p["chosen"])) or {})
                                 for p in picks)
    rosters = collections.defaultdict(collections.Counter)
    for p in picks:
        rosters[str(p["roster_id"])][
            pu.player_position(players_db.get(str(p["chosen"])) or {})] += 1
    no_def = [r for r, c in rosters.items() if c["DEF"] == 0]
    no_k = [r for r, c in rosters.items() if c["K"] == 0]
    print("=== %s ===" % label)
    print("  UNFILLED STARTING SLOTS: %d" % len(holes))
    for h in holes[:8]:
        print("     %s" % h)
    print("  chairs with NO defense: %d %s" % (len(no_def), sorted(no_def)))
    print("  chairs with NO kicker : %d %s" % (len(no_k), sorted(no_k)))
    print("  DEF drafted %d, K drafted %d (12 chairs)" % (counts["DEF"], counts["K"]))
