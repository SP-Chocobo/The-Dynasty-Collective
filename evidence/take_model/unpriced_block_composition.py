"""#206 CORRECTION + #168 SHARPENED: what the unpriced block is made of, and when QB pricing dies.

WHY THIS EXISTS: A PUBLISHED CLAIM OF MINE WAS TOO STRONG. `VALUE_MODEL_RESULT.md` concluded
that the unpriced block "is the shadow of a pricing gap", citing that 17 of the 31 real picks
which took an unpriced player took a quarterback. That evidence is about WHICH unpriced players
get TAKEN. It was used to characterise WHAT THE BLOCK IS, which is a different population -- a
claim about 638 rows resting on evidence about 31. This file measures the block directly.

THE BLOCK IS TWO POPULATIONS, NOT ONE, and only the smaller one is the QB gap:

    round 0   481 priced, 638 unpriced    WR 254 (39.8%)  TE 141 (22.1%)  RB 130 (20.4%)  QB 113 (17.7%)
    round 14  303 priced, 648 unpriced    WR 254 (39.2%)  TE 141 (21.8%)  RB 130 (20.1%)  QB 123 (19.0%)
    round 26  161 priced, 646 unpriced    WR 254 (39.3%)  TE 141 (21.8%)  RB 130 (20.1%)  QB 121 (18.7%)

  * NEVER-PRICED (525 rows: 254 WR + 141 TE + 130 RB). CONSTANT at every depth -- these rows do
    not become unpriced as the draft drains, they were never priceable. That is a vendor
    COVERAGE gap and it has nothing to do with the startable floor. It is 82% of the block.
  * BECAME-UNPRICED (QB). Priced QBs fall 42 -> 0 as the draft proceeds. This is the startable
    floor, and it is 18% of the block.

SO THE CORRECTION IS: the block's SIZE is mostly vendor coverage; the block's TAKE RATE is
mostly QB. Both are true and they are different facts. Per row, a QB in the block was taken
roughly five times as often as a non-QB in it (17 takes from ~120 QB rows against 14 takes from
~525 non-QB rows), which is why the picks looked like a QB story while the block is not.

AND THE SHARPENED FINDING, which is the part that matters for `#168`. That item records the
behaviour as "bounded to superflex QB tails". Measured here, "tails" understates it:

    rnd  picks   QB priced   QB unpriced   QB drafted
      0      0          42           113            0
     10    120          12           113           30
     12    144           0           123           32
     26    312           0           121           34

**From round 12 of a 30-round superflex draft, the engine can price ZERO quarterbacks** -- for
18 of 30 rounds, 60% of the draft, at the position the format makes most valuable. The mechanism
is exact and not in dispute: 39 baseline QBs carry a projection, 28 clear the startable floor
(0.5 x QB12 = 162.00), and by round 12 thirty-two QBs have been drafted, so every remaining QB
is below the floor. Every priced QB carries `startable_floor` as its replacement basis until
there are none left; no row is mislabelled.

WHAT THIS DOES NOT CLAIM. It does not say the floor's constant is wrong -- `QB_STARTABLE_FLOOR_FRACTION`
has a documented stability-basin derivation and `#56` is not engaged by anything here. The open
question it raises is narrower and is a DESIGN question, not an arithmetic one: the floor asks
"is this QB startable AS A QB", while the slot that makes a superflex QB draftable is
SUPER_FLEX, whose occupant competes against flex-eligible non-QBs. That is a cross-position
comparison the floor does not make and `#229` has already authorised in principle. Deciding it
is Phase 3 (`#50`), and this file does not decide it.

LIMITS: ONE league's capture. The composition and the round-12 cliff are properties of this
board and this baseline; a different QB universe moves the cliff. Sets nothing.

Run from the repo root. NEVER cd first.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/take_model/unpriced_block_composition.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import run_draft_battery as rdb

RULES = Path("data/league_captures/greatest_show_on_paper_2.json")
OUT = Path("evidence/take_model/unpriced_block_composition.json")
COMPOSITION_DEPTHS = (0, 14, 26)
CLIFF_DEPTHS = tuple(range(0, 27, 2))


def _fixture():
    rules = json.loads(RULES.read_text())
    league = {
        "roster_positions": list(rules["roster_positions"]),
        "scoring_settings": {k: v["value"] for k, v in rules["scoring_settings_observed"].items()},
        "total_rosters": rules["total_rosters"], "settings": {"type": 2},
    }
    merger = dm.DataMerger()
    players_db, _ = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    merger.set_league_format(db.league_format_hint(league))          # NEVER SKIP
    teams = int(rules["total_rosters"])
    roster_ids = [str(i) for i in range(1, teams + 1)]
    opening = dr.compute_draft_board(merger, players_db, [], my_roster_id="1", league=league,
                                     mode="balanced", sleeper_projections=season,
                                     sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    return (rules, league, merger, players_db, season, teams, roster_ids,
            [r["player_id"] for r in opening])


def _board_at(depth, merger, players_db, league, season, teams, roster_ids, order):
    taken = depth * teams
    picks = [{"player_id": pid, "roster_id": roster_ids[i % teams],
              "round": (i // teams) + 1, "pick_no": i + 1}
             for i, pid in enumerate(order[:taken])]
    boards = ds._build_opponent_boards(merger, players_db, picks, league, roster_ids,
                                       mode="balanced", sleeper_projections=season,
                                       sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    return boards["1"], picks


def main() -> int:
    rules, league, merger, players_db, season, teams, roster_ids, order = _fixture()
    floor = dr.qb_startable_floor(merger)
    proj = merger.projections
    qb_proj = proj[(proj["position"] == "QB") & proj["projection"].notna()]["projection"].astype(float)
    report = {
        "league": rules["league"],
        "LIMITS": ("ONE league's capture. Composition and the cliff round are properties of this "
                   "board and baseline. Sets nothing."),
        "qb_startable_floor": round(floor, 2) if floor is not None else None,
        "qb_anchor_rank": dr.QB_STARTABLE_ANCHOR_RANK,
        "qb_floor_fraction": dr.QB_STARTABLE_FLOOR_FRACTION,
        "qbs_with_a_projection": int(len(qb_proj)),
        "qbs_clearing_the_floor": int((qb_proj >= floor).sum()) if floor is not None else None,
        "composition": {}, "qb_cliff": [],
    }
    print(f"QB startable floor = {dr.QB_STARTABLE_FLOOR_FRACTION} x "
          f"QB{dr.QB_STARTABLE_ANCHOR_RANK} = {floor:.2f}")
    print(f"{report['qbs_with_a_projection']} projected QBs, "
          f"{report['qbs_clearing_the_floor']} clear the floor\n", flush=True)

    print("BLOCK COMPOSITION -- a constant non-QB core plus a QB population that collapses")
    for depth in COMPOSITION_DEPTHS:
        board, _ = _board_at(depth, merger, players_db, league, season, teams, roster_ids, order)
        by_id = board["by_id"]
        unpriced = list(board.get("unpriced_ids") or ())
        priced = list((board.get("rank_by_id") or {}).keys())
        cu = Counter((by_id[p] or {}).get("position") for p in unpriced)
        report["composition"][str(depth)] = {
            "priced": len(priced), "unpriced": len(unpriced),
            "unpriced_by_position": {str(k): v for k, v in sorted(cu.items())},
            "non_qb_unpriced": sum(v for k, v in cu.items() if k != "QB"),
        }
        share = {k: f"{v/len(unpriced):.1%}" for k, v in sorted(cu.items(), key=lambda x: -x[1])}
        print(f"  round {depth:>2}: {len(priced):>4} priced, {len(unpriced):>4} unpriced   {share}",
              flush=True)

    print("\nQB PRICING CLIFF")
    print(f"  {'rnd':>4}{'picks':>7}{'QB priced':>11}{'QB unpriced':>13}{'QB drafted':>12}")
    for depth in CLIFF_DEPTHS:
        board, picks = _board_at(depth, merger, players_db, league, season, teams, roster_ids, order)
        by_id = board["by_id"]
        pq = [p for p in (board.get("rank_by_id") or {}) if (by_id[p] or {}).get("position") == "QB"]
        uq = [p for p in (board.get("unpriced_ids") or ()) if (by_id[p] or {}).get("position") == "QB"]
        drafted = sum(1 for pk in picks
                      if (players_db.get(pk["player_id"]) or {}).get("position") == "QB")
        report["qb_cliff"].append({"round": depth, "picks": len(picks), "qb_priced": len(pq),
                                   "qb_unpriced": len(uq), "qb_drafted": drafted})
        print(f"  {depth:>4}{len(picks):>7}{len(pq):>11}{len(uq):>13}{drafted:>12}", flush=True)

    blind = [r["round"] for r in report["qb_cliff"] if r["qb_priced"] == 0]
    report["first_round_with_no_priceable_qb"] = min(blind) if blind else None
    rounds = max(p["round"] for p in json.loads(
        Path("evidence/real_drafts/extracted/greatest_show_on_paper_2_board.json").read_text())["picks"])
    report["draft_rounds"] = rounds
    report["VERDICT"] = (
        f"Zero QBs are priceable from round {report['first_round_with_no_priceable_qb']} of "
        f"{rounds}. '#168: bounded to superflex QB tails' understates it -- the engine is blind "
        f"to QB for the majority of a superflex draft. Separately, 82% of the unpriced block is "
        f"a never-priced non-QB core (vendor coverage), NOT the startable floor."
        if blind else "No depth sampled reached zero priceable QBs -- re-read before citing.")
    print(f"\nVERDICT: {report['VERDICT']}")
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
