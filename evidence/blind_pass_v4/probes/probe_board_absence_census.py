import pandas as pd, data_merger as dm, draft_battery as db, draft_room as dr, run_draft_battery as rdb
merger = dm.DataMerger()
players_db, _ = rdb.build_players_db_from_capture()
league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False,
                             dynasty=True, base_scoring=rdb.scoring_settings_from_capture())
merger.set_league_format(db.league_format_hint(league))
for tag, kw in (("NO season projections", {}),
                ("WITH season projections", {"sleeper_projections": rdb.season_projections_from_capture(),
                                             "sleeper_basis": dr.SLEEPER_BASIS_SEASON_SUM})):
    board = dr.compute_draft_board(merger, players_db, [], my_roster_id=None, league=league,
                                   mode="balanced", **kw)
    f = pd.DataFrame(board)
    print("===", tag, " n =", len(f))
    print("  bpa_source census:", f["bpa_source"].value_counts(dropna=False).to_dict())
    print("  bpa notna:", int(f["bpa"].notna().sum()),
          " projected_points notna:", int(f["projected_points"].notna().sum()),
          " final_score notna:", int(f["final_score"].notna().sum()))
    tv = f[f["bpa"].notna() & f["projected_points"].isna()]
    print("  bpa notna & projected_points ISNA  n =", len(tv))
    if len(tv):
        print("    injury_status census:", tv["injury_status"].value_counts(dropna=False).to_dict())
        print("    risk_adj values:", sorted(set(tv["risk_adj"].fillna(-999).tolist()))[:10])
        print(tv[["name","position","injury_status","bpa","risk_adj","universal_value","final_score","absence_kind","availability_basis"]].head(10).to_string())
    print("  injury_status census (all):", f["injury_status"].value_counts(dropna=False).to_dict())
    pr = f[f["final_score"].notna() & f["injury_status"].notna()]
    print("  priced rows WITH a designation n =", len(pr),
          " risk_adj == 0.0 among them:", int((pr["risk_adj"] == 0.0).sum()),
          " risk_adj isna:", int(pr["risk_adj"].isna().sum()))
    if len(pr):
        print("    designation census on priced rows:", pr["injury_status"].value_counts().to_dict())
        z = pr[pr["risk_adj"] == 0.0]
        print("    designations with risk_adj EXACTLY 0.0:", z["injury_status"].value_counts().to_dict())
        print("    basis on those:", z["availability_basis"].value_counts(dropna=False).to_dict())
