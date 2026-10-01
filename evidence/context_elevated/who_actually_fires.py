"""The one population where context_elevated CAN fire: multi-eligible probes.

displacement_adj <= 0 for a SINGLE-position probe, so on a rulebook where every row is
single-position the gap can only ever be one capped term's worth. A MULTI-eligible probe can
be LIFTED (lineup_optimizer, THE SIGN). If the flag fires only there, then in practice it
does not mean "ranked highly because of fit" -- it means "multi-eligible".
"""
import data_merger as dm, draft_room as dr, draft_battery as db
import run_draft_battery as rdb, pick_synthesis as ps

merger = dm.DataMerger()
players_db, _prov = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()
matrix = db.league_matrix(merger.base_scoring_settings()
                          if hasattr(merger, "base_scoring_settings") else None)
by_label = {e["label"]: e for e in matrix}


for label in ("HEAVY_IDP", "LIGHT_IDP", "CAPTURE_owner_league", "CAPTURE_fourth_and_forever"):
    ent = by_label.get(label)
    if ent is None:
        print(f"{label}: not in league_matrix; skipped")
        continue
    league = ent.get("league", ent)
    merger.set_league_format(db.league_format_hint(league))
    board = dr.compute_draft_board(merger, players_db, [], my_roster_id="1", league=league,
                                   mode="balanced", sleeper_projections=season,
                                   sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    rows = [r for r in board
            if r.get("universal_value") is not None and r.get("final_score") is not None]
    gaps = [(r["final_score"] - r["universal_value"], r) for r in rows]
    fired = [(g, r) for g, r in gaps if g >= ps.CONTEXT_ELEVATED_THRESHOLD]
    multi = [(g, r) for g, r in fired
             if len(players_db.get(str(r["player_id"]), {}).get("fantasy_positions") or []) > 1]
    print(f"=== {label} ===  n={len(rows)}  max gap {max(g for g,_ in gaps):.2f}  "
          f"fired {len(fired)} ({len(fired)/len(rows)*100:.2f}%)  of which multi-eligible: {len(multi)}")
    for g, r in sorted(fired, key=lambda x: -x[0])[:5]:
        fp = players_db.get(str(r["player_id"]), {}).get("fantasy_positions")
        print(f"    {r.get('name','?'):<24} gap {g:>7.2f}  pos {r.get('position')}  "
              f"fantasy_positions {fp}  disp {r.get('displacement_adj')}")
