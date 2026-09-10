"""Pre-registered in PREREG_aggregate_selection.md. Run from the REPO ROOT.

One opening board on Fourth and Forever's real rulebook, #201/#204 recipe. No draft, no
engine modification. Asks: what does the top 312 of the pool look like BEFORE any valuation
term has had a chance to reorder it?

INVOCATION: dr.compute_draft_board, pre-draft (picks=[]), mode not forced -- round 1, so
`auto` is balanced and this is the same call the first pick of run_ff_draft made.
"""
import json, collections, time, pathlib
import pandas as pd
import data_merger as dm, draft_room as dr, draft_battery as db
import run_draft_battery as rdb

OUT = pathlib.Path("evidence/roster_shape/ff_rulebook")
CAP = json.load(open("data/league_captures/fourth_and_forever.json"))
SCORING = {k: v["value"] for k, v in CAP["scoring_settings_observed"].items()}
LEAGUE = {"roster_positions": CAP["roster_positions"], "scoring_settings": SCORING,
          "total_rosters": 12, "settings": {"type": 2}}
N = 312


def main():
    t0 = time.time()
    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()
    merger.set_league_format(db.league_format_hint(LEAGUE))
    season = rdb.season_projections_from_capture()
    print("universe:", prov["players_in_pool"], "season:", len(season), flush=True)

    board = dr.compute_draft_board(
        merger, players_db, [], "1", LEAGUE,
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    print("board rows:", len(board), f"{time.time()-t0:.1f}s", flush=True)

    # SAVE RAW BEFORE DERIVING ANYTHING (#215), and save EVERY key rather than a guessed
    # subset. The first run of this probe asked for "_points" and "replacement_level" --
    # internal column names that compute_draft_board does not emit -- and got 1,119 nulls
    # that would have read as "no player has a projection". Do not name a production column
    # from memory; take the row's own keys.
    raw = [dict(r) for r in board]
    json.dump({"universe": prov, "n_rows": len(board), "rows": raw,
               "elapsed_s": round(time.time() - t0, 1)},
              open(OUT / "aggregate_selection_raw.json", "w"))
    print("RAW SAVED", flush=True)

    drafted = json.load(open(OUT / "ff_draft.json"))["picks"]
    dids = [p["player_id"] for p in drafted]

    # UNIVERSE ASSERTION (skill: board-vs-draft). If the board is not the population the
    # draft drew from, every number below is about a different question.
    bids = set(str(r["player_id"]) for r in board)
    missing = [i for i in dids if str(i) not in bids]
    if missing:
        raise RuntimeError(f"FIXTURE ERROR: {len(missing)} drafted ids absent from the board "
                           f"(e.g. {missing[:5]}). Nothing reported.")
    print(f"universe assertion OK: all 312 drafted ids are on the board")

    df = pd.DataFrame(board)
    print("\nEMITTED COLUMNS:", sorted(df.columns.tolist()))
    PTS = "projected_points"
    if PTS not in df.columns:
        raise RuntimeError(f"{PTS} absent; emitted columns are {sorted(df.columns)}")
    pos = {str(r["player_id"]): r.get("position") for r in board}

    def compo(ids):
        c = collections.Counter(pos.get(str(i)) for i in ids)
        tot = sum(c.values())
        return c, tot

    def show(label, ids):
        c, tot = compo(ids)
        line = "  ".join(f"{p} {c[p]:>4} ({100*c[p]/tot:>5.1f}%)"
                         for p in ("QB", "RB", "WR", "TE") )
        extra = sum(v for k, v in c.items() if k not in ("QB", "RB", "WR", "TE"))
        print(f"  {label:<34} {line}   other {extra}")
        return c

    # Count only rows that CARRY the quantity -- an absent _points is not a low _points.
    have_pts = df[df[PTS].notna()]
    have_fs = df[df["final_score"].notna()]
    print(f"\nrows with {PTS}: {len(have_pts)} of {len(df)};"
          f"  with final_score: {len(have_fs)} of {len(df)}")

    top_pts = have_pts.sort_values([PTS, "player_id"], ascending=[False, True]).head(N)
    top_fs = have_fs.sort_values(["final_score", "player_id"], ascending=[False, True]).head(N)

    print("\n" + "=" * 78)
    print("POSITIONAL COMPOSITION OF 312\n")
    show("ALL board rows (admitted)", df["player_id"].tolist())
    show("PRICED rows only (final_score)", have_fs["player_id"].tolist())
    show(f"rows carrying {PTS}", have_pts["player_id"].tolist())
    c_pts = show(f"TOP 312 by {PTS}", top_pts["player_id"].tolist())
    show("TOP 312 by opening final_score", top_fs["player_id"].tolist())
    show("ACTUALLY DRAFTED (auto arm)", dids)
    show("ACTUALLY DRAFTED (balanced arm)",
         [p["player_id"] for p in json.load(open(OUT / "ff_draft_balanced.json"))["picks"]])

    print("\noverlap with the drafted 312:")
    for label, sub in ((f"top312 by {PTS}", top_pts), ("top312 by final_score", top_fs)):
        ov = len(set(str(x) for x in sub["player_id"]) & set(str(i) for i in dids))
        print(f"  {label:<26} {ov}/312")

    print(f"\nFORK READ: T (tight ends in top 312 by {PTS}) = {c_pts['TE']}")
    print("  A (pool ordering)  T in [91,111]")
    print("  B (valuation adds) T <= 60")
    print("  C (both)           T in [61,90]")


if __name__ == "__main__":
    main()
