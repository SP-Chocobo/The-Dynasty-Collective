"""Does expected_taken predict what actually gets taken? Per position, in a NON-superflex
league -- the case the pace convention does NOT cover. (#21)

The row-count bias is established. Superflex QB, where it bit hardest, is corrected by the
market-convention override. The open question is whether it misleads anywhere else, and that
is answerable directly: the model states an expectation for each position over the gap ahead,
and the draft then says what really happened over that same gap.

A ratio near 1.0 is calibrated. ABOVE 1.0 means the model UNDER-predicts that position's losses
-- the direction that makes forfeit too small and defers the position, which is the failure the
superflex QB case was.

`position_expected_taken` is on CandidateSnapshot but not on the serialized payload, so this
re-runs rather than reading the cached trajectories.

Run from the REPO ROOT.
"""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
import collections
import data_merger as dm, draft_room as dr, draft_battery as dbat, run_draft_battery as rdb
import pick_synthesis as ps, player_universe as pu

merger = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture(); scoring = rdb.scoring_settings_from_capture()
arm = next(a for a in dbat.league_matrix(scoring) if a["label"] == "12T_ppr")
league, teams, rounds = arm["league"], arm["teams"], arm["rounds"]
merger.set_league_format(dbat.league_format_hint(league))
order = [(i % teams) + 1 if (i // teams) % 2 == 0 else teams - (i % teams)
         for i in range(teams * rounds)]
pos_of = lambda pid: pu.player_position(players_db.get(str(pid)) or {}) or "?"
ME = 1

# Predictions are recorded at MY turns; the draft then proceeds and supplies the truth.
pending, pred, act = [], collections.defaultdict(float), collections.defaultdict(int)
picks = []
for i in range(teams * rounds):
    if order[i] == ME:
        nxt = next((j for j in range(i + 1, len(order)) if order[j] == ME), None)
        if nxt is not None and nxt - i > 1 and i // teams + 1 <= 12:
            snap = ps.build_snapshot(merger, players_db, picks, order, i, ME, league,
                                     pick_label="%d.x" % (i // teams + 1), mode="auto",
                                     sleeper_projections=season,
                                     sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
            seen = {}
            for c in snap.candidates:
                p = pos_of(c.player_id)
                if p and p not in seen and c.position_expected_taken is not None:
                    seen[p] = float(c.position_expected_taken)
            pending.append((i, nxt, seen))
            print("  recorded turn at round %d (%d picks ahead): %s"
                  % (i // teams + 1, nxt - i - 1,
                     {k: round(v, 2) for k, v in sorted(seen.items())}), flush=True)
    b = dr.compute_draft_board(merger, players_db, picks, my_roster_id=order[i], league=league,
                               mode="auto", sleeper_projections=season,
                               sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    if not b:
        break
    picks.append({"player_id": b[0]["player_id"], "roster_id": order[i], "pick_no": i + 1})

for i, nxt, seen in pending:
    really = collections.Counter(pos_of(picks[j]["player_id"]) for j in range(i + 1, min(nxt, len(picks))))
    for p, e in seen.items():
        pred[p] += e
        act[p] += really.get(p, 0)

print("\n=== CALIBRATION over %d turns, 12T_ppr (no pace convention applies) ===" % len(pending))
print("%-6s%14s%12s%10s   %s" % ("pos", "predicted", "actual", "ratio", "reading"))
for p in ("RB", "WR", "TE", "QB", "K", "DEF"):
    if p not in pred:
        continue
    P, A = pred[p], act[p]
    r = (A / P) if P else None
    note = ("under-predicts losses" if r and r >= 1.5 else
            "over-predicts losses" if r is not None and r <= 0.67 else "calibrated")
    print("%-6s%14.2f%12d%10s   %s" % (p, P, A, "%.2f" % r if r is not None else "-", note))
