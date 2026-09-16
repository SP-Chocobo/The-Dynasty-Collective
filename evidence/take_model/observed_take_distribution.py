"""#206: what rank does a REAL drafter actually take? Measured, never chosen.

THE QUESTION THE FORK NEEDS ANSWERED. `RANK_TAKE_PROBABILITY` says a team takes the best player
on its own board with p=0.55, and the tail carries a 0.02 floor. Summed over a 481-row board that
is 10.73 expected takes when a team picks ONCE, and the two ways to restore the mass disagree
violently: normalise the whole 10.73 and rank-1 falls to 0.051, or drop the floor from the
distribution and rank-1 is 0.455. Choosing the one that makes `#206`'s symptom go away is
calibrating to a desired answer, which `#56` forbids.

So this asks the drafters. FOR EACH REAL PICK, in order, rebuild the PICKING TEAM's board from
the picks that had actually happened, and record where the player they took sat on it. The
distribution of those ranks IS P(rank R taken | a pick occurs) -- it sums to one BY CONSTRUCTION,
which is exactly the mass constraint the model violates.

WHY THIS IS NOT CIRCULAR, and the trap it avoids. The battery drafts every seat with CDME, so
measuring ranks there would ask the engine what the engine does -- it takes its own rank 1 by
construction, and the answer would be 1.0 with no information in it. These are HUMAN picks from a
completed startup (`greatest_show_on_paper_2_board.json`, 360 picks, its own provenance checks).

WHAT IT MAY AND MAY NOT CONCLUDE. The capture's own LIMITS are binding: *"ONE league ... a data
point for testing, NOT a benchmark. No engine constant may be calibrated to it."* So this can test
the five constants and show a DIRECTION; it may not set them. The output is evidence for `#50`,
not a patch.

KNOWN POPULATION LIMITS, stated before the numbers so they cannot be read past:
  * 224 of 305 real picks resolve to the engine's universe (`join_decomposition.py`). The failures
    are 72 players absent from the resolver and 9 position mismatches, concentrated R15-R30 --
    a 30-round superflex draft outruns the vendor universe. R1-R3 resolve 34 of 34.
  * Unresolved picks still REMOVE the player from later boards where they can be identified; where
    they cannot, that pick is invisible and the board is very slightly too full. Counted, reported.
  * The board is a January draft; vendor rows are the 2026 season, so team is not a join key here
    (it rejects 36 real players who changed clubs).

Run from the repo root. NEVER cd first.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/take_model/observed_take_distribution.py
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import run_draft_battery as rdb

BOARD = Path("evidence/real_drafts/extracted/greatest_show_on_paper_2_board.json")
RULEBOOK = Path("data/league_captures/greatest_show_on_paper_2.json")
OUT = Path("evidence/take_model/observed_take_distribution.json")
SUFFIX = re.compile(r"\s+(jr|sr|ii|iii|iv|v)\.?$", re.IGNORECASE)


def resolve_picks(picks_all: list, players_db: dict) -> tuple[dict, int, list]:
    """Resolve every real pick to a players_db id ONCE, up front, so a draft loop does no
    matching. Returns (resolved {pick_no: player_id}, ambiguous_count, unmatched_names).

    Extracted for #206's REAL calibration arm (evidence/survival_calibration/calibrate.py), which
    must resolve the SAME picks the SAME way -- a second resolver would be a second source of
    truth for which player each real pick was (#126). Placeholders, illegible picks and picks
    with no raw name are skipped, exactly as before.

    INDEXED OVER players_db, NOT over merger.projections, and the difference is 77 picks. The
    first version resolved through `_find_match`, whose rows come from the 764-row VENDOR table
    and carry no Sleeper `player_id` at all -- it resolved 0, which is the kind of zero that
    looks like a finding. The board's ids live in players_db (6,595 rows, the capture's whole
    universe), so that is what the index is built from.

    AMBIGUITY IS A REJECTION (#82): a (name, position) key holding more than one id resolves
    nothing rather than picking the first."""
    index: dict[tuple, list] = {}
    for pid, info in players_db.items():
        nm = dm.normalize_name(f"{info.get('first_name', '')} {info.get('last_name', '')}".strip())
        index.setdefault((nm, (info.get("position") or "").upper()), []).append(pid)

    resolved: dict[int, str] = {}
    ambiguous, unmatched = 0, []
    for p in picks_all:
        if p.get("is_rookie_pick_placeholder") or p.get("illegible") or not p.get("raw_player"):
            continue
        pos = (p.get("position") or "").upper()
        cand = (index.get((dm.normalize_name(p["raw_player"]), pos))
                or index.get((dm.normalize_name(SUFFIX.sub("", p["raw_player"].replace(".", "")
                                                            .replace("'", ""))), pos)))
        if not cand:
            unmatched.append(p["raw_player"])
        elif len(cand) > 1:
            ambiguous += 1
        else:
            resolved[p["pick_no"]] = str(cand[0])
    return resolved, ambiguous, unmatched


def main() -> int:
    board = json.loads(BOARD.read_text())
    rules = json.loads(RULEBOOK.read_text())
    picks_all = sorted(board["picks"], key=lambda p: p["pick_no"])

    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    base = rdb.scoring_settings_from_capture()

    # THE LEAGUE IS BUILT FROM THE CAPTURE, the way draft_battery's own CAPTURE arm builds it.
    # It previously came from `build_mock_league`, which is the #248 hazard: that helper
    # overwrites `rec`, and `rec` is what selects the rankings EXPORT -- so an arm can silently
    # read a different file than it reports. The capture's observed settings are the rulebook;
    # nothing here should be asserting a format the league did not actually use.
    league = {
        "roster_positions": list(rules["roster_positions"]),
        "scoring_settings": {k: v["value"] for k, v in rules["scoring_settings_observed"].items()},
        "total_rosters": rules["total_rosters"],
        "settings": {"type": 2},
    }
    merger.set_league_format(db.league_format_hint(league))          # NEVER SKIP
    print(f"league {rules['league']}  teams {rules['total_rosters']}  "
          f"slots {len(rules['roster_positions'])}  universe {universe['players_in_pool']}",
          flush=True)

    resolved, ambiguous, unmatched = resolve_picks(picks_all, players_db)

    r1 = [p for p in picks_all if p["round"] == 1 and p["pick_no"] in resolved]
    print(f"resolved {len(resolved)} picks to player ids "
          f"(ambiguous {ambiguous}, unmatched {len(unmatched)}: {unmatched[:6]})", flush=True)
    print(f"   CONTROL round 1: {len(r1)}/12 -- the twelve most famous players in a superflex "
          f"draft; short of twelve means the INDEX is broken, not the data\n", flush=True)

    # THE SEAT IS THE TEAM THAT ACTUALLY PICKED, NOT THE SLOT.
    #
    # This read `str(p["slot"])`, which is the slot's ORIGINAL owner. In a league with traded
    # picks those are different teams, and the whole measurement is "how did the PICKING team's
    # own board rank the player they took" -- so keying on the slot evaluated the wrong team's
    # roster, the wrong needs and the wrong board. Measured on this draft: the picker differs
    # from the round-1 owner of that slot on 135 of 360 picks, 37.5%. Every rank in the
    # published histogram drew on that population, which is why the figures it produced
    # (rank-1 share 3.0%, top-5 13.7%, 31/301 unpriced) were withdrawn rather than adjusted.
    #
    # THE SEAT IS THE TEAM NAME ITSELF. `picked_by` is already a unique, stable identifier and
    # the engine only needs roster ids to be consistent, so there is nothing to map.
    #
    # The first version of this repair derived seat numbers from round one, on the reasoning
    # that every team picks from its own slot exactly once there. IT DOES NOT: a round-1 pick
    # was itself traded, so Snoopking51 picks twice in round 1 and one team not at all, and the
    # derivation produced 11 seats for 12 rosters. The guard below caught that rather than
    # silently collapsing two teams onto one roster -- which is the same class of defect this
    # whole repair exists to remove, reached by a different route. Derived from the data, never
    # hand-listed (#126), and now derived from a property that actually holds.
    seats_seen = {p["picked_by"] for p in picks_all}
    if len(seats_seen) != int(rules["total_rosters"]):
        raise RuntimeError(
            f"board names {len(seats_seen)} distinct teams for {rules['total_rosters']} rosters "
            "-- seat identity is not derivable from this board, and guessing it is what this "
            "repair exists to stop")
    unseated = 0
    ranks: list[dict] = []
    engine_picks: list[dict] = []
    not_on_board = 0

    for p in picks_all:
        pid = resolved.get(p["pick_no"])
        seat = p.get("picked_by")
        if not seat:
            unseated += 1
            continue
        if pid is not None:
            rows = dr.compute_draft_board(merger, players_db, engine_picks, my_roster_id=seat,
                                          league=league, mode="balanced",
                                          sleeper_projections=season,
                                          sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
            # VALUATION_RANK over PRICED rows, the same register RANK_TAKE_PROBABILITY is keyed on
            # (ordinals.py: rank_by_id is built over priced rows only).
            order = [r["player_id"] for r in rows if r.get("bpa") is not None]
            rank = order.index(pid) + 1 if pid in order else None
            if rank is None:
                not_on_board += 1
            ranks.append({"pick_no": p["pick_no"], "round": p["round"], "seat": seat,
                          "player": p["raw_player"], "position": p.get("position"),
                          "rank": rank, "priced_pool": len(order)})
            engine_picks.append({"pick_no": p["pick_no"], "round": p["round"],
                                 "roster_id": seat, "player_id": pid})
            if len(ranks) % 25 == 0:
                print(f"   {len(ranks):>4} measured   (pick {p['pick_no']}, pool {len(order)})",
                      flush=True)

    got = [r for r in ranks if r["rank"] is not None]
    hist = Counter(r["rank"] for r in got)
    n = len(got)
    print(f"\n   MEASURED {n} picks; {not_on_board} taken players were not on the picking team's "
          f"priced board at all (unpriced or filtered)\n", flush=True)
    print(f"   {'rank':<6} {'picks':>6} {'share':>8}   cumulative", flush=True)
    cum = 0
    for rk in sorted(hist)[:15]:
        cum += hist[rk]
        print(f"   {rk:<6} {hist[rk]:>6} {hist[rk]/n:>7.1%}   {cum/n:>6.1%}", flush=True)
    top5 = sum(hist[r] for r in (1, 2, 3, 4, 5))
    print(f"\n   TOP-5 SHARE: {top5}/{n} = {top5/n:.1%}   "
          f"(the model's five keys sum to 1.21 of a mass that must be 1.00)", flush=True)
    print(f"   RANK-1 SHARE: {hist.get(1,0)}/{n} = {hist.get(1,0)/n:.1%}   "
          f"(model says 0.55; full-mass normalisation would say 0.051)", flush=True)

    OUT.write_text(json.dumps(
        {"league": rules["league"], "picks_measured": n, "not_on_priced_board": not_on_board,
         "rank_histogram": {str(k): v for k, v in sorted(hist.items())},
         "rank1_share": round(hist.get(1, 0) / n, 4) if n else None,
         "top5_share": round(top5 / n, 4) if n else None,
         "model_rank1": 0.55, "full_mass_rank1": 0.051, "head_only_rank1": 0.455,
         "LIMITS": "ONE league. Tests the constants and shows a direction; may not set them.",
         "rows": ranks}, indent=1))
    print(f"\nwrote {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
