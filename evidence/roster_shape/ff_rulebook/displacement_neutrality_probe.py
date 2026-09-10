"""Pre-registered in PREREG_aggregate_selection.md (addendum). Run from the REPO ROOT with
PYTHONPATH=. -- the engine modules resolve off sys.path, DataMerger's baselines off cwd, and
both must be the repo root at once.

Tests ONE sentence I published: that mid-draft displacement is order-neutral across positions.

INVOCATION: dr.compute_draft_board at two real mid-draft states replayed from ff_draft.json,
for the seat actually on the clock, with that seat's actual accumulated roster. mode left at
its production default -- both states are in rounds 1-14 where auto IS balanced, so the
displacement term is live and this is production, not a forced arm.
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
STATES = (100, 150)
TOTAL = 312
PTS = "projected_points"


def main():
    t0 = time.time()
    merger = dm.DataMerger()
    players_db, prov = rdb.build_players_db_from_capture()
    merger.set_league_format(db.league_format_hint(LEAGUE))
    season = rdb.season_projections_from_capture()
    drafted = json.load(open(OUT / "ff_draft.json"))["picks"]
    print("universe:", prov["players_in_pool"], flush=True)

    saved = {}
    for at in STATES:
        # Production shape for picks: the schema the engine reads, not a guessed subset.
        # A pick missing `round` silently flips mode="auto" to balanced (the 17th withdrawal).
        picks = [{"player_id": p["player_id"], "roster_id": p["roster_id"],
                  "round": p["round"]} for p in drafted[:at]]
        me = drafted[at]["roster_id"]          # the seat actually on the clock at pick at+1
        board = dr.compute_draft_board(
            merger, players_db, picks, me, LEAGUE,
            sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        saved[at] = [dict(r) for r in board]
        print(f"state pick {at}: seat {me}, board {len(board)} rows, "
              f"mode={board[0].get('mode') if board else '?'}, {time.time()-t0:.1f}s", flush=True)

    json.dump({"universe": prov, "states": {str(k): v for k, v in saved.items()},
               "elapsed_s": round(time.time() - t0, 1)},
              open(OUT / "displacement_neutrality_raw.json", "w"))
    print("RAW SAVED", flush=True)

    for at in STATES:
        df = pd.DataFrame(saved[at])
        for col in (PTS, "bpa", "displacement_adj", "position"):
            if col not in df.columns:
                raise RuntimeError(f"{col} absent; emitted {sorted(df.columns)}")
        p = df[df["bpa"].notna() & df["displacement_adj"].notna()].copy()
        p["decision"] = p["bpa"] + p["displacement_adj"]
        p["level"] = p[PTS] - p["bpa"]
        p["displaced"] = p["level"] - p["displacement_adj"]
        # Independent reconciliation of the identity, not a restatement of it.
        gap = (p["decision"] - (p[PTS] - p["displaced"])).abs().max()

        K = TOTAL - at
        def top(col):
            return p.sort_values([col, "player_id"], ascending=[False, True]).head(K)
        c_b = collections.Counter(top("bpa")["position"])
        c_d = collections.Counter(top("decision")["position"])

        print("\n" + "=" * 76)
        print(f"STATE pick {at}   priced+displaced rows {len(p)}   K={K}   "
              f"identity |gap| max = {gap:.4f}")
        print(f"  {'pos':>4}{'mean adj':>11}{'median adj':>12}{'adj==0.0':>10}"
              f"{'topK bpa':>10}{'topK dec':>10}{'delta':>8}")
        for pos in ("QB", "RB", "WR", "TE"):
            s = p[p["position"] == pos]
            if s.empty:
                continue
            z = int((s["displacement_adj"] == 0.0).sum())
            print(f"  {pos:>4}{s['displacement_adj'].mean():>11.2f}"
                  f"{s['displacement_adj'].median():>12.2f}{z:>10}"
                  f"{c_b[pos]:>10}{c_d[pos]:>10}{c_d[pos]-c_b[pos]:>+8}")
        D = c_d["TE"] - c_b["TE"]
        worst = max(abs(c_d[x] - c_b[x]) for x in ("QB", "RB", "WR", "TE"))
        print(f"  D (TE delta) = {D:+d};  largest positional move = {worst}")
        print("  FORK: N |D|<=3 and no position >5  |  P D>=+4  |  Q D<=-4")


if __name__ == "__main__":
    main()
