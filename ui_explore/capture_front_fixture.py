#!/usr/bin/env python3
"""Front-page facts for one real roster, with each field's BASIS recorded beside it.

A front page fed invented numbers is the one thing this repo is built not to do, so this writes
what can be measured, declares what had to be constructed, and leaves absent what nothing here
can know. Those three are different claims and the output keeps them apart; a surface that cannot
tell them apart will render a demo as data.

WHAT IS MEASURED. Replay a recorded VDS pick sequence -- no simulation, seconds not minutes --
and real rosters fall out. From those:

    thin positions      depth_chart.positional_depth + depth_ratings.depth_label, the SAME
                        judgment the Trade Calculator and the League Depth Map use
    structural holes    lineup_optimizer.slots_from_roster_positions + slot_coverage.
                        NOT league_usable_positions -- see the argument at the call site,
                        which this line contradicted for months (`#336`)
    the bye signal      lineup_optimizer.bye_collision / bye_concentration -- value lost rather
                        than bodies lost, and the SHAPE of it (what share lands in one week)

WHAT HAD TO BE CONSTRUCTED, AND WHY IT IS LABELLED RATHER THAN HIDDEN. `compute_readiness` counts
`slot == "Starter"`, and `slot` is assigned in app.py from SLEEPER'S OWN `starters` array -- the
lineup a human submitted. A drafted roster has players and no submitted lineup, so "7 of 9
starters set" cannot be measured from a draft at all.

THE MATERIAL-INJURY CLAIM IS A DIFFERENT CASE, AND THIS FILE USED TO GET IT WRONG (`#336`). It
said the claim "cannot be measured from a draft at all", which is false: the capture carries
`injury_status` on 494 players (IR 126, Questionable 290, PUP 21 ...), and this fixture's own
starter `12484` is Jayden Higgins, on IR, which `is_material_injury_status` grades material. So
the data is here and the reason given for its absence was wrong -- and `front_page.split_reason`
says exactly why that is the worse failure: "a wrong reason reads as reassurance, which is worse
than a clumsy one."

What is genuinely missing is the SUBMITTED-STARTERS gate, not the injury feed. Rendering it also
needs a rung `front_claims.LADDER` does not have, so this is recorded rather than half-built: an
injury claim with nowhere to rank is not a repair. This builds a
starters list with `optimize_lineup` and then, for one scenario, leaves a slot deliberately open,
because a front page whose only state is "everything is fine" cannot be judged. Every such field
is stamped `constructed` and names what produced it. A reader who wants the real number has to
sync a league; that is the honest answer, not a number.

WHAT IS ABSENT. The record and the standings. `league_standings.team_standings` reads Sleeper's
own `settings.wins/losses`, and nothing in `data/league_captures/` holds a roster's contents or a
result -- those files capture a league's RULES, which is what they were built for. So `record` is
`None` with a reason attached, and the surface renders it per the absence contract (#187) rather
than inventing a 0-0.

Fixture discipline is the engine-measurement skill's, and every line of it is load-bearing: run
from the repo root (DataMerger resolves baselines relative to cwd), build_players_db_FROM_CAPTURE
(the 6,595-row population production receives, not the 764-row vendor reconstruction),
set_league_format BEFORE the format is used (rec/bonus_rec_te propagate by FILE SELECTION, not
through scoring_settings), and season projections on SLEEPER_BASIS_SEASON_SUM.

    python3 ui_explore/capture_front_fixture.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path.cwd()))

import data_merger as dm
import depth_chart
import depth_ratings
import draft_battery as db
import draft_strategy as ds
import lineup_optimizer as lo
import player_universe as pu
import run_draft_battery as rdb

OUT = pathlib.Path("ui_explore/front_fixture.json")
VDS = pathlib.Path("evidence/batteries/VDS_2026-10-01_varied_drafting_strategy_dd4ade7.json")
WANT = "12T_ppr_K_DEF"          # a full-shape league: named K and DEF slots, so holes are real
STRATEGY = "sharp_auto"
SEAT = 1                        # the roster the page is "mine"

# PARAMETERS, not a second generator. The quiet-state page needs a different SEAT and a CLOCK,
# and copying this file to get them would be a second home for every basis string in it (`#126`)
# -- the defect `#312` found when one palette turned out to have three homes. Overridden from
# argv by `_parse`; the defaults reproduce the fixture this file has always emitted, and a test
# asserts that.
#
# A SUPPLIED WEEK IS NOT A MEASURED ONE. A live app reads season/week from Sleeper's NFL state; a
# replayed draft has no point in a season, so a week passed here is a CHOSEN clock reading and
# the basis below says so rather than inheriting the measured stamp of the roster around it.
_seat, _clock, _out = SEAT, None, OUT


def main() -> int:
    players_db, prov = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    scoring = rdb.scoring_settings_from_capture()
    arms = {a["label"]: a for a in db.league_matrix(scoring)}
    arm = arms[WANT]
    league, teams, rounds = arm["league"], arm["teams"], arm["rounds"]
    roster_positions = league.get("roster_positions") or []

    merger = dm.DataMerger()
    merger.set_league_format(db.league_format_hint(league))   # BEFORE anything is priced

    vds = json.loads(VDS.read_text())
    seq = next(r["pick_sequence"] for r in vds["results"]
               if r.get("format") == WANT and r.get("strategy") == STRATEGY)
    order = ds.generate_pick_order(list(range(1, teams + 1)), rounds, "snake")
    assert len(seq) >= teams * rounds, f"sequence is {len(seq)} picks, need {teams * rounds}"

    # Replay. roster_id comes from the production pick order, not from a convention invented here.
    held: dict[int, list[str]] = {rid: [] for rid in range(1, teams + 1)}
    for i in range(teams * rounds):
        pid = seq[i]
        pid = pid.get("chosen_player_id") if isinstance(pid, dict) else pid
        held[order[i]].append(str(pid))

    rosters = [{"roster_id": rid, "owner_id": f"owner{rid}", "players": ids}
               for rid, ids in sorted(held.items())]
    users = [{"user_id": f"owner{rid}", "display_name": f"Team {rid}"} for rid in sorted(held)]
    universe = pu.build_player_universe(players_db, rosters, users=users,
                                        projections=season, scoring_settings=scoring)

    # ---- MEASURED -----------------------------------------------------------------------
    depth = depth_chart.positional_depth(universe, merger)
    me = f"Team {_seat}"
    # NOT .get(me, {}): positional_depth keys on `owner_name or f"Roster {roster_id}"`, so a
    # missed users->owner_id join silently yields {} -- which reads downstream as "no thin
    # positions and every slot unfillable", the most alarming page this surface can draw, from
    # a lookup miss. Fail loud on the key that selects whose roster the page is about.
    assert me in depth, f"{me} is not in the depth chart; keys are {sorted(depth)[:6]}"
    thin = []
    for position in sorted(depth.get(me, {})):
        peers = [cells[position] for cells in depth.values() if position in cells]
        label = depth_ratings.depth_label(depth[me][position], peers)
        if label in depth_ratings.THIN_LABELS:
            cell = depth[me][position]
            # valued_count travels WITH count, because they describe different sets: every
            # rostered player raises count, only the priced ones raise value. depth_label ranks
            # on `value` and never looks at valued_count, so a room that is weak only because
            # its coverage is partial is labelled weak all the same -- a consumer that holds
            # both numbers can say so, one that holds only `count` cannot.
            thin.append({"position": position, "label": label, "count": cell["count"],
                         "valued_count": cell.get("valued_count"),
                         "value_label": depth_chart.depth_value_label(cell)})

    # THE OPTIMIZER'S OWN SHAPE, which an earlier version of this file did not build and so
    # could never run: optimize_lineup, bye_collision and slot_coverage all index
    # player["eligible"] and (except slot_coverage) player["value"] directly, with no .get
    # tolerance. A dict of {id, name, position, team, bye, uv} raises KeyError on the first
    # player. `eligible` comes from player_eligible_positions, NOT player_position: MANDATE 2.6
    # / #172 put the full set behind that function precisely so a dual-eligible player is not
    # collapsed to one bucket in an assignment problem.
    byes = merger.bye_week_by_team()
    mine = []
    for pid in held[_seat]:
        info = players_db.get(pid) or {}
        team, name = info.get("team"), pu.player_name(info, pid)
        priced = merger.merge_player(name, position=pu.player_position(info), team=team)
        mine.append({"id": pid, "name": name, "position": pu.player_position(info),
                     "team": team, "bye": byes.get(team),
                     "value": priced.get("trade_value") or 0.0,
                     "eligible": set(pu.player_eligible_positions(info))})
    unknown_byes = sum(1 for m in mine if m["bye"] is None)
    shape = lo.bye_concentration(mine, roster_positions)
    weeks = lo.bye_collision(mine, roster_positions)

    # A HOLE IS A SLOT THE SOLVER LEAVES EMPTY, not a position missing from a free-agent
    # filter. league_usable_positions EXPANDS flex slots -- its docstring says so, because its
    # job is "never suggest a free agent in a position with nowhere to start him" -- and it
    # falls back to EVERY known position on empty roster_positions. Both behaviours are right
    # for that job and wrong for this one: in a standard FLEX league with no dedicated TE slot
    # it reports TE as a slot nobody can fill, and on a malformed league it reports all nine.
    # slot_coverage answers the counting question directly and takes no `value` by design.
    slots = lo.slots_from_roster_positions(roster_positions)
    cover = lo.slot_coverage(mine, slots)
    occupied = {a["slot_id"] for a in cover["occupied"]}
    unfilled = [sl for sl in slots if sl["slot_id"] not in occupied]
    holes = sorted({sl["label"] for sl in unfilled})

    # ---- CONSTRUCTED, and stamped so -----------------------------------------------------
    best = lo.optimize_lineup(mine, slots)
    starters = [a["player_id"] for a in best["assignments"]]

    out = {
        "_provenance": {
            "format": WANT, "strategy": STRATEGY, "seat": _seat, "teams": teams, "rounds": rounds,
            "players_db": prov if isinstance(prov, (str, int)) else str(prov)[:200],
            "universe_rows": len(universe),
            "basis": {
                "thin_positions": "measured -- positional_depth + depth_ratings.depth_label",
                "structural_holes": "measured -- slots_from_roster_positions + slot_coverage",
                "bye_profile": "measured -- lineup_optimizer.bye_collision / bye_concentration",
                "starters": "CONSTRUCTED -- optimize_lineup's best legal lineup. slot='Starter' "
                            "is assigned in app.py from Sleeper's own `starters` array, which is "
                            "a lineup a human submitted; a drafted roster has none, so this "
                            "cannot be measured from a draft and is not presented as if it were",
                "record": "ABSENT -- team_standings reads Sleeper's settings.wins/losses, and no "
                          "capture in data/league_captures/ holds a roster's contents or a "
                          "result. Rendered per the absence contract, never as 0-0",
                # WITHOUT THIS, THE BYE CLAIM CAN NAME A WEEK ALREADY PLAYED. The ladder's bye
                # rung justifies itself on futurity -- "a known FUTURE week with a measured cost,
                # and planning only works in advance" -- and nothing in the pipeline knew what
                # week it was, so the page could rank a dead week second-highest. A live app reads
                # it from Sleeper's NFL state (season/week/season_type); a replayed draft has no
                # point in a season at all, which is a genuine absence rather than an oversight.
                "current_week": (
                    "ABSENT -- a replayed draft has no point in the season. A live "
                    "league reads season/week from Sleeper's NFL state; without it "
                    "the bye claim cannot assert that a week is still ahead"
                    if _clock is None else
                    f"CONSTRUCTED -- week {_clock} is a CHOSEN clock reading, not a measured "
                    f"one. A replayed draft has no point in a season; a live league reads "
                    f"season/week from Sleeper's NFL state. The roster, byes, holes and depth "
                    f"around it are measured -- only the clock is chosen"),
                "team": "CONSTRUCTED -- the seat's label in a replayed battery, not an owner's "
                        "team name. A live league has the real one",
                "league_name": "ABSENT -- a format label is a battery arm, not a league's name",
            },
        },
        "league": {"roster_positions": roster_positions, "starting_slots": len(slots)},
        "thin_positions": thin,
        "structural_holes": holes,
        "bye_profile": {"concentration": shape.get("concentration"),
                        "worst_week": shape.get("worst_week"),
                        "worst_week_loss": shape.get("worst_week_loss"),
                        "total_loss": shape.get("total_loss"),
                        "weeks": shape.get("weeks"), "basis": shape.get("basis"),
                        # the floor's MAGNITUDE, which bye_collision computes and does not
                        # return: "a floor" without a count is weaker than "a floor, 2 players"
                        "unknown_byes": unknown_byes,
                        "worst_week_detail": weeks.get(shape.get("worst_week")) if shape.get("worst_week") else None},
        "starters": starters,
        "current_week": _clock,
        "team": me,
        "league_name": None,
        "roster": mine,
        "record": None,
    }
    _out.write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + "\n")
    print(f"{WANT}/{STRATEGY} seat {_seat}: {len(mine)} players, {len(universe)} universe rows")
    print(f"  thin: {[t['position'] + ' ' + t['label'] for t in thin] or 'none'}")
    print(f"  holes: {holes or 'none'}")
    print(f"  byes: worst week {shape.get('worst_week')} loses {shape.get('worst_week_loss')} "
          f"of {shape.get('total_loss')} total, concentration {shape.get('concentration')} "
          f"(basis {shape.get('basis')})")
    print(f"  starters CONSTRUCTED: {len(starters)} of {len(slots)} slots")
    print(f"  clock: {_clock if _clock is not None else 'absent (no season position)'}")
    print(f"-> {_out}")
    return 0


def _parse(argv):
    """`--seat N --week N --out PATH`. FLAGS rather than positional arguments, deliberately.

    `#332` cost a corrupted page when one builder's positional fixture path was handed to
    another, and THIS SESSION REPEATED IT: `build_empty.py` defaults to `empty_fixture.json` and
    was handed `front_fixture.json`, which silently rewrote its freshness grade from
    "Aging, 76 days" into "nothing on disk carries a date" -- a 699-byte diff that would have
    been committed had the diff not been read. A flag cannot be silently mistaken for a
    different flag's value."""
    global _seat, _clock, _out
    args = list(argv)
    while args:
        flag = args.pop(0)
        if flag == "--seat":
            _seat = int(args.pop(0))
        elif flag == "--week":
            _clock = int(args.pop(0))
        elif flag == "--out":
            _out = pathlib.Path(args.pop(0))
        else:
            raise SystemExit(f"unknown argument {flag!r}; use --seat N --week N --out PATH")


if __name__ == "__main__":
    _parse(sys.argv[1:])
    sys.exit(main())
