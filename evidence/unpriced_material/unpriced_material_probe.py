"""Is there ANY observed material to place an unpriced player with? Measured, not assumed.

`#255`. The owner's question, by example: given players grading `70/112/26` and `68/107/24`,
a third at `69/109/???` should be placeable -- his two observed dimensions bracket him, so the
missing third is constrained rather than unknown. The proposal was a bracketing holdout to test
whether that generalises.

**It does not apply here, and this is the measurement that says so before the holdout was
built.** The bracketing idea needs a player with SOME observed dimensions. On the F&F board the
unpriced carry none at all -- `???/???/???`, not `69/109/???`. So there is nothing to bracket
against, and a holdout run on the priced population would have returned a confident number
about a question the unpriced population cannot ask.

The consequence for the engine contract is the opposite of what it looks like: ORDER LAST is
NOT an arbitrary 404 for these rows. The engine is not declining to use information it holds;
it holds none. What is wrong is only that the board cannot SAY so -- "no evidence of any kind
exists for this player" is a different claim from "sorts last", and only the first points at a
remedy.

The remedy it points at is SUPPLY, and part of it is already sitting in the repo: 50 of the 638
are findable by name in the KeepTradeCut export and simply are not joined to the pool.

Run from the repo root (rule 1). Reports counts only; changes nothing.
"""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
import json
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb
merger = dm.DataMerger()
players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()
cap = json.loads(open("data/league_captures/fourth_and_forever.json").read())
league = {"roster_positions": cap["roster_positions"],
          "scoring_settings": {k: v["value"] for k, v in cap["scoring_settings_observed"].items()},
          "total_rosters": 12, "settings": {"type": 2},
          "draft_rounds": dr.draftable_slots_per_team(cap["roster_positions"])}
merger.set_league_format(db.league_format_hint(league))
pool = dr.build_available_pool(merger, players_db, set(),
                               dr.league_usable_positions(league["roster_positions"]),
                               sleeper_projections=season,
                               scoring_settings=league.get("scoring_settings"),
                               pool_scope="all", sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
dr._derive_points_and_source(pool)
priced = pool["_points"].notna()
P, U = pool.loc[priced], pool.loc[~priced]
print(f"priced {len(P)}   unpriced {len(U)}\n")
print(f"{'metric':16s} {'priced non-null':>16s} {'UNPRICED non-null':>18s}")
for c in ("proj_3yr", "trade_value", "projection", "sleeper_points"):
    print(f"{c:16s} {int(P[c].notna().sum()):>16d} {int(U[c].notna().sum()):>18d}")

# How many unpriced players have ANY of the three correlates?
any3 = U[["proj_3yr", "trade_value"]].notna().any(axis=1)
print(f"\nunpriced with at least one correlate (proj_3yr or trade_value): {int(any3.sum())} of {len(U)}")

# Does the KTC external frame know them by name, even unjoined?
ev = merger.external_values
ktc = ev[ev["source_name"] == "keeptradecut"] if "source_name" in ev.columns else ev
print(f"\nmerger.external_values keeptradecut rows: {len(ktc)}")
import re
def key(n): return re.sub(r"[^a-z]", "", str(n).lower())
ktc_keys = {key(n) for n in ktc["name"].dropna()}
u_hit = sum(1 for n in U["name"] if key(n) in ktc_keys)
p_hit = sum(1 for n in P["name"] if key(n) in ktc_keys)
print(f"UNPRICED players findable by name in the KTC frame: {u_hit} of {len(U)}")
print(f"priced   players findable by name in the KTC frame: {p_hit} of {len(P)}")
