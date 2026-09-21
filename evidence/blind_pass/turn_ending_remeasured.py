"""#17 RE-MEASURED against the reverted engine (ruled 2026-09-21).

The original measurement ran on the v2 `acting_now_value` ordering and its evidence file cites
`_acting_now_order`, which no longer exists. Its premise was that turn-ending picks
DIFFERENTIALLY fall back to the tav order. Post-#22 every pick uses the tav order, so the
question is whether the 3x K/DEF clustering survives.

Self-play is the right instrument here and not a blindness trap: this is a PLACEMENT question
about one engine's own behaviour ("where in the draft does it put K/DEF"), not a quality A/B
against a field.
"""
import collections, json, sys, time
import data_merger as dm, draft_room as dr, draft_battery as db
import run_draft_battery as rdb, draft_strategy as ds, pick_synthesis as ps
import player_universe as pu

TEAMS, ROUNDS = 12, 16
merger = dm.DataMerger()
players_db, _prov = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()
# 12T_ppr_K_DEF, NOT build_mock_league. THE FIRST RUN OF THIS PROBE WAS VACUOUS: mock leagues
# start QB/RB/RB/WR/WR/TE/FLEX/FLEX with NO K and NO DEF slot, so those positions never enter
# usable_positions and "K/DEF were never taken" measured the FORMAT, not the engine. #17 is
# entirely about where K and DEF land, so the rulebook has to have slots for them.
_mx = db.league_matrix(merger.base_scoring_settings()
                       if hasattr(merger, "base_scoring_settings") else None)
_entry = next(x for x in _mx if x["label"] == "12T_ppr_K_DEF")
league = _entry.get("league", _entry)
merger.set_league_format(db.league_format_hint(league))
seats = [str(i) for i in range(1, TEAMS + 1)]
pick_order = [str(s) for s in ds.generate_pick_order(seats, ROUNDS, "snake")]

picks, t0 = [], time.time()
for idx in range(TEAMS * ROUNDS):
    seat = pick_order[idx]
    snap = ps.build_snapshot(
        merger, players_db, picks, pick_order, current_index=idx, my_roster_id=seat,
        league=league, pick_label=f"{idx//TEAMS+1}.{idx%TEAMS+1:02d}", top_n=12,
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    if not snap.candidates:
        print(f"no candidates at index {idx}; stopping", file=sys.stderr)
        break
    chosen = str(snap.candidates[0].player_id)
    picks.append({"player_id": chosen, "roster_id": seat,
                  "round": idx // TEAMS + 1, "pick_no": idx + 1})
    if idx % 24 == 0:
        print(f"  ... {idx}/{TEAMS*ROUNDS}  {time.time()-t0:.0f}s", file=sys.stderr)

json.dump(picks, open("/tmp/claude-0/-home-user-The-Dynasty-Collective/"
                      "90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/t17_picks.json", "w"))

pos_of = lambda pid: pu.player_position(players_db.get(str(pid)) or {}) or "?"
seq = [p["roster_id"] for p in picks]
ending = {i for i in range(len(picks) - 1) if seq[i] == seq[i + 1]}

print(f"\n=== #17 re-measured, HEAD (tav ordering restored), 12T_ppr_K_DEF ===")
print(f"picks: {len(picks)}   turn-ending: {len(ending)} "
      f"({100*len(ending)/len(picks):.1f}%)\n")
all_pos = collections.Counter(pos_of(p["player_id"]) for p in picks)
end_pos = collections.Counter(pos_of(p["player_id"])
                              for i, p in enumerate(picks) if i in ending)
share = len(ending) / len(picks)
print(f"{'pos':<5}{'all':>6}{'turn-ending':>13}{'expected':>10}{'ratio':>8}")
for pos, n in all_pos.most_common():
    exp = n * share
    r = (end_pos[pos] / exp) if exp else float('nan')
    print(f"{pos:<5}{n:>6}{end_pos[pos]:>13}{exp:>10.2f}{r:>8.2f}")

for pos in ("K", "DEF"):
    first = next((i + 1 for i, p in enumerate(picks) if pos_of(p["player_id"]) == pos), None)
    if first:
        print(f"\nfirst {pos} of the draft: pick {first} "
              f"({(first-1)//TEAMS+1}.{(first-1)%TEAMS+1:02d}), "
              f"turn-ending: {(first-1) in ending}")
    else:
        print(f"\nfirst {pos} of the draft: NEVER TAKEN")
early = [i for i in ending if (i // TEAMS) + 1 <= 12 and pos_of(picks[i]["player_id"]) in ("K","DEF")]
kdef_12 = [i for i, p in enumerate(picks)
           if (i // TEAMS) + 1 <= 12 and pos_of(p["player_id"]) in ("K", "DEF")]
print(f"\nK/DEF taken by round 12: {len(kdef_12)}, of which turn-ending: {len(early)}"
      + (f" ({100*len(early)/len(kdef_12):.0f}%)" if kdef_12 else ""))
