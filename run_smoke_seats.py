"""Is the engine GOOD at drafting -- against a FIELD of varied sane styles, not one control?

Pre-registered in `evidence/smoke_seats/PREREGISTRATION.md`, committed before this file existed.

WHAT THIS IS NOT. Gate 1 (`#284`) proved the engine never produces a structural failure across
34 formats: 5,652 picks, 0 findings. That is LEGALITY, not quality -- a draft can be perfectly
legal and badly played. `#205` and `#245` asked the quality question and DISAGREE (1 of 68 seats
on points vs 10 of 12), which the freeze checklist still carries as unresolved.

WHAT IS NEW HERE, AND IT IS THE ONLY THING THAT IS NEW. Both prior runs put the engine against
ONE uniform control in every other seat. A homogeneous field is one opponent copied eleven
times, not a league -- and it is the same artifact `#206` named when it found simulated chairs
taking twelve straight QBs in round one. This run puts several DIFFERENT sane styles in the
other seats. Everything else is `run_roster_proof`'s, imported rather than copied (`#126`): the
pool restriction, production pricing on every arm, `set_league_format` per format, absence
counted separately from zero, the two rulers, the shared lineup solve, and seat control.

THE DESIGN TRAP THAT WAS AVOIDED, recorded because the wrong choice was available and cheaper.
`evidence/survival_calibration/calibrate.py` ALREADY has five varied policies and they look like
exactly what this needs. Its own scope limit says they choose from `build_snapshot`'s NARROWED
candidate set. That is harmless where it lives -- the question there is whether survival predicts
-- and FATAL here: opponents restricted to the engine's own shortlist can never punish it for
undervaluing someone, because the engine already removed everyone it judged not worth
considering. "Is the engine good at picking from its own shortlist" is very nearly a tautology.
`run_roster_proof`'s control draws from the FULL undrafted pool, so this extends that harness.

EVERY STYLE HERE DRAWS FROM THE FULL UNDRAFTED POOL. That is the property that makes them
controls at all, and it is asserted by a test rather than promised by this paragraph.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import data_merger as dm
import draft_battery as db
import league_config as lc
import draft_room as dr
import draft_strategy as ds
import lineup_optimizer as lo
import pick_synthesis
import resume_join
import run_draft_battery as rdb
import run_roster_proof as rp

REPORT_PATH = Path("SMOKE_SEATS.json")

#: Draft Sharks' "this player went undrafted" marker in `adp_dd_ppr`, not a draft slot.
#:
#: NAMED HERE BECAUSE THIS IS ITS FIRST REAL HOME. `run_draft_battery` documents it in prose --
#: "often the 18000.0 'undrafted' sentinel" -- while measuring that 4,506 of 5,346 capture
#: entries carry ONLY an ADP field. Ranking on it unfiltered would sort undrafted players as the
#: most desirable players in the draft, which is the single easiest way to build a strawman
#: opponent by accident. The count excluded is REPORTED per format, so if the feed ever stops
#: using this marker the number visibly moves instead of silently passing.
ADP_UNDRAFTED_SENTINEL = 18000.0


def _positions_of(pid, players_db) -> set:
    """Every slot this player can fill, multi-position included (#172)."""
    info = players_db.get(pid) or {}
    listed = info.get("fantasy_positions")
    if listed:
        return set(listed)
    one = info.get("position")
    return {one} if one else set()


def _cover_starters_first(available, mine, players_db, slots):
    """Restrict to players who fill a starting slot this roster has NOT yet covered.

    THIS IS THE ANTI-STRAWMAN FLOOR, and it is the same one `run_roster_proof.control_pick`
    already applies for the same measured reason: without it, a projection-ranked drafter took
    24 CONSECUTIVE QBs in a 1QB league, and the engine "beat" it by +503% while measuring
    nothing except that one arm knew what a lineup was.

    Returns the pool UNRESTRICTED when nothing is needed or nothing eligible remains, so the
    floor can never empty the board.
    """
    need = rp.unmet_slot_positions(mine, players_db, slots)
    if not need:
        return available
    eligible = [pid for pid in available if _positions_of(pid, players_db) & need]
    return eligible or available


def _by_points(pool, ctx):
    return min(pool, key=lambda pid: (-ctx["points"][pid], pid))


def _style_points_need(ctx):
    """The INCUMBENT control, delegated to rather than reimplemented.

    Kept in the field on purpose: it is the style `#205` and `#245` ran in every seat, so its
    presence here is what makes this run comparable to them rather than a fresh scale.
    """
    return rp.control_pick(ctx["available"], ctx["points"], ctx["mine"],
                           ctx["players_db"], ctx["slots"])


def _style_adp(ctx):
    """Market consensus: the lowest real ADP that covers an unmet starter.

    THE MOST REALISTIC OPPONENT IN THE FIELD, and the only one that is not something this
    repository invented -- `adp_dd_ppr` is what the market actually did. Players carrying the
    undrafted sentinel, or no ADP at all, are not ranked here; when none of the eligible pool
    has a real ADP this falls back to projection, which is what a drafter off the end of their
    cheat sheet actually does.
    """
    pool = _cover_starters_first(ctx["available"], ctx["mine"], ctx["players_db"], ctx["slots"])
    ranked = [pid for pid in pool if ctx["adp"].get(pid) is not None]
    if not ranked:
        return _by_points(pool, ctx)
    return min(ranked, key=lambda pid: (ctx["adp"][pid], pid))


def _style_need_first(ctx):
    """Roster construction first: every required starting slot filled before any depth."""
    pool = _cover_starters_first(ctx["available"], ctx["mine"], ctx["players_db"], ctx["slots"])
    return _by_points(pool, ctx)


def _style_run_follower(ctx):
    """Chases the position just taken -- the herd behaviour positional runs are made of.

    ITS FALLBACK IS POLICY-NATIVE, NOT THE ENGINE'S TOP CANDIDATE. `calibrate.py`'s equivalent
    falls back to `board[0]`, which is the engine's own pick; a control that defers to the thing
    under test whenever its own rule does not fire is partly the engine wearing a different hat,
    and it inflates agreement. When there is no run to chase this drafts like `points_need`.
    """
    last = ctx["last_position"]
    if last:
        pool = [pid for pid in ctx["available"] if last in _positions_of(pid, ctx["players_db"])]
        if pool:
            return _by_points(pool, ctx)
    return _style_points_need(ctx)


#: The field. Deterministic, seedless, reproducible, and every one of them drafts from the FULL
#: undrafted pool -- never from the engine's narrowed shortlist.
STYLES = {
    "points_need": _style_points_need,
    "adp": _style_adp,
    "need_first": _style_need_first,
    "run_follower": _style_run_follower,
}


def adp_table(season) -> tuple[dict, int]:
    """(player_id -> real ADP, count of rows excluded as the undrafted sentinel)."""
    table, excluded = {}, 0
    for pid, row in (season or {}).items():
        if not isinstance(row, dict):
            continue
        value = row.get("adp_dd_ppr")
        if value is None:
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        if value >= ADP_UNDRAFTED_SENTINEL:
            excluded += 1
            continue
        table[str(pid)] = value
    return table, excluded


def style_by_seat(seats, engine_seat, admitted=None) -> dict:
    """Styles dealt round-robin to every seat the engine does not hold.

    Deterministic and REPORTED with every run. Which style sits where changes who the engine is
    next to in the snake, so a reader who cannot see the assignment cannot check the result.

    `admitted` IS REQUIRED IN PRACTICE AND THE DEFAULT IS A TRAP THIS CODE ALREADY FELL INTO.
    The first version took no such argument and dealt from `sorted(STYLES)`, so the admission
    gate ran, printed its verdict, and was then ignored -- `run_follower` was excluded for being
    unable to field a legal lineup and sat in the field anyway, contaminating a measured 8/12
    with an opponent the gate had already rejected. A gate whose verdict nothing consumes is
    not a gate; it is a log line. Passing None keeps every style and is retained only so a
    caller can deliberately measure the ungated field, which is a different question.
    """
    names = sorted(admitted) if admitted is not None else sorted(STYLES)
    if not names:
        raise SystemExit("REFUSING TO RUN: the admission gate excluded every style, so there is "
                         "no field left to measure. That is a finding about the styles, not a "
                         "result about the engine.")
    assigned, i = {}, 0
    for seat in seats:
        if seat == engine_seat:
            continue
        assigned[seat] = names[i % len(names)]
        i += 1
    return assigned


def draft(merger, players_db, league, pick_order, points, adp, season, rounds, slots,
          assigned, engine_seat, weekly_projections=None):
    """One draft. `engine_seat` may be None, which is how the admission gate runs a field with
    no engine in it at all."""
    picks, taken, mine = [], set(), {}
    num_teams = len(set(str(r) for r in pick_order))
    last_position = None
    for idx in range(min(len(pick_order), rounds * num_teams)):
        seat = str(pick_order[idx])
        round_no = idx // num_teams + 1
        if seat == engine_seat:
            snap = pick_synthesis.build_snapshot(
                merger, players_db, picks, pick_order, idx, seat, league,
                pick_label=f"{round_no}.{(idx % num_teams) + 1:02d}",
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
                # #30. None for every caller that does not have them, which is the previous
                # behaviour exactly. The backtest passes the drafted season's own weekly lines,
                # so what it grades is the SHIPPED path rather than a monkey-patch.
                weekly_projections=weekly_projections)
            chosen = next((c.player_id for c in snap.candidates
                           if str(c.player_id) in points and str(c.player_id) not in taken), None)
            who = "cdme"
        else:
            available = [pid for pid in points if pid not in taken]
            who = assigned[seat]
            chosen = STYLES[who]({"available": available, "points": points, "adp": adp,
                                 "mine": mine.get(seat, []), "players_db": players_db,
                                 "slots": slots, "last_position": last_position}) \
                if available else None
        if chosen is None:
            break
        chosen = str(chosen)
        taken.add(chosen)
        mine.setdefault(seat, []).append(chosen)
        position = (players_db.get(chosen) or {}).get("position")
        last_position = position
        picks.append({"pick_no": idx + 1, "round": round_no, "roster_id": seat,
                      "player_id": chosen, "style": who, "position": position})
    return picks


def starters_filled(picks, seat, players_db, slots) -> tuple:
    """(filled, required) starting slots for one seat, via the harness's OWN lineup solve.

    Every ruler is handed an empty value map on purpose: the admission gate asks whether a
    lineup can be FILLED, never what it is worth, and slot occupancy does not depend on price.
    Both rulers must still be present because `score_roster` iterates `RULERS` -- the first
    draft of this function passed only `points` and would have raised `KeyError` on the first
    call, which is the sort of thing that looks like a gate while never running.
    """
    scored = rp.score_roster(picks, seat, players_db, {name: {} for name in rp.RULERS}, slots)
    block = (scored or {}).get("points") or {}
    return block.get("starters_filled"), block.get("starting_slots")


def round_one_positions(picks) -> dict:
    """#184's reopen trigger, captured as a byproduct rather than a separate run.

    Its premise is that the simulated chairs behave unrealistically by taking twelve straight
    QBs in round one. This either reproduces that or it does not, at no extra cost.
    """
    counts = {}
    for p in picks:
        if p["round"] != 1:
            continue
        counts[p["position"]] = counts.get(p["position"], 0) + 1
    return counts


def composition_by_style(picks) -> dict:
    """What each style actually DRAFTED, as {style: {round_one, all_rounds, picks}}.

    RULE 6 IS WHY THIS IS RECORDED. `round_one_positions` pools the whole league into one
    counter, which can say "7 of 12 round-one picks were QBs" but cannot say WHOSE. In a
    one-QB standard league that is the difference between a finding about the engine and a
    strawman field the engine is beating for free -- and the aggregate answers neither.

    Every pick already carries its `style` and `position`, so this costs nothing but the
    writing down. The engine's own picks carry the style name `cdme`, so it is attributed on
    the same footing as every control rather than being a special case here.
    """
    out: dict[str, dict] = {}
    for p in picks:
        rec = out.setdefault(p["style"], {"round_one": {}, "all_rounds": {}, "picks": 0})
        pos = p["position"]
        rec["picks"] += 1
        rec["all_rounds"][pos] = rec["all_rounds"].get(pos, 0) + 1
        if p["round"] == 1:
            rec["round_one"][pos] = rec["round_one"].get(pos, 0) + 1
    return out


def pool_composition(per_run) -> dict:
    """Sum per-run compositions into one table per style, across every seat run."""
    total: dict[str, dict] = {}
    for run in per_run:
        for style, rec in run.items():
            acc = total.setdefault(style, {"round_one": {}, "all_rounds": {}, "picks": 0})
            acc["picks"] += rec["picks"]
            for field in ("round_one", "all_rounds"):
                for pos, n in rec[field].items():
                    acc[field][pos] = acc[field].get(pos, 0) + n
    return total


def admission_gate(merger, players_db, league, pick_order, points, adp, season, rounds, slots,
                   seats) -> dict:
    """Can each style field a legal lineup AGAINST ITSELF? The anti-strawman test, mechanical.

    Rule 6 of `run_roster_proof` was earned: a projection-only control took 24 consecutive QBs
    in a 1QB league, the engine "beat" it 12 of 12 by a mean of +503%, and the number measured
    nothing except that one arm knew what a lineup was. A baseline nobody would ever play is a
    strawman and beating it is not evidence.

    So before any style's results are allowed to count, that style fills all 12 seats with NO
    ENGINE PRESENT and every seat must fill 100% of its starting slots. A style that cannot
    field a legal lineup against itself is EXCLUDED and its exclusion is reported -- never
    silently dropped, because a quietly missing opponent is how a field gets easier without
    anyone noticing.

    Derived from the roster's own slot list, so this is an admission TEST rather than an opinion
    about which styles are sane.
    """
    verdicts = {}
    for name in sorted(STYLES):
        assigned = {s: name for s in seats}
        picks = draft(merger, players_db, league, pick_order, points, adp, season,
                      rounds, slots, assigned, engine_seat=None)
        rows = []
        for seat in seats:
            filled, required = starters_filled(picks, seat, players_db, slots)
            rows.append({"seat": seat, "starters_filled": filled, "starting_slots": required})
        short = [r for r in rows if r["starters_filled"] != r["starting_slots"]]
        verdicts[name] = {
            "admitted": not short,
            "seats": len(rows),
            "seats_short_of_a_legal_lineup": len(short),
            "detail": short[:3],
            "round_one": round_one_positions(picks),
        }
    return verdicts


def compare_by_style(picks, runs_seat_styles, scored, ruler):
    """Engine vs EACH style separately, never only against the field's mean.

    Pre-registered as required: "the engine beat the field" hides its own most interesting part
    if one style beats it. An aggregate that can conceal a loss is not the whole answer.
    """
    out = {}
    engine = scored["engine"][ruler][rp.COMPARE_ON[ruler]]
    for seat, block in scored["by_seat"].items():
        style = runs_seat_styles.get(seat)
        if style is None:
            continue
        out.setdefault(style, []).append(block[ruler][rp.COMPARE_ON[ruler]])
    return {style: {"n": len(vals), "engine": engine,
                    "style_mean": round(sum(vals) / len(vals), 2) if vals else None,
                    "engine_ahead": (engine > sum(vals) / len(vals)) if vals else None}
            for style, vals in out.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(REPORT_PATH))
    ap.add_argument("--formats", type=int, default=len(rp.PROOF_FORMATS))
    #: 0 = DERIVE from the league's own roster_positions. A hand-set count is a second source of
    #: truth about roster size; a SHORT one is worse than illegal, it is misleading -- it
    #: compares who FRONT-LOADS starters, not who ends up with the better roster.
    ap.add_argument("--rounds", type=int, default=0)
    args = ap.parse_args(argv)

    commit = resume_join.head_commit()
    scoring = rdb.scoring_settings_from_capture()          # #213, before anything is drafted
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    adp, adp_excluded = adp_table(season)
    print(f"commit {commit} | universe {universe['players_in_pool']} players "
          f"| adp ranked {len(adp)} | adp sentinel excluded {adp_excluded}", flush=True)

    results, started = [], time.time()
    for spec in rp.PROOF_FORMATS[:args.formats]:
        league = dr.build_mock_league(teams=spec["teams"], superflex=spec["superflex"],
                                      scoring=spec["scoring"], te_premium=spec["te_premium"],
                                      dynasty=True, base_scoring=scoring)
        merger.set_league_format(db.league_format_hint(league))          # rule 4
        points = rp.scoreable_pool(merger, players_db, league, season)   # rule 2
        values = db.reference_values(merger, players_db, league,
                                     sleeper_projections=season,
                                     sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        seats = [str(i) for i in range(1, spec["teams"] + 1)]
        rounds = args.rounds or len(lc.draftable_slots(league.get("roster_positions")))
        pick_order = ds.generate_pick_order(seats, rounds, "snake")
        slots = lo.slots_from_roster_positions(league.get("roster_positions") or [])
        rulers = {"cdme": values, "points": points}

        t0 = time.time()
        gate = admission_gate(merger, players_db, league, pick_order, points, adp, season,
                              rounds, slots, seats)
        admitted = [n for n, v in gate.items() if v["admitted"]]
        print(f"{spec['label']:<16} gate: admitted {sorted(admitted)} "
              f"| excluded {sorted(n for n in gate if n not in admitted)}", flush=True)

        runs, round_one, composition = [], [], []
        for seat in seats:                                               # seat control
            assigned = style_by_seat(seats, seat, admitted)
            picks = draft(merger, players_db, league, pick_order, points, adp, season,
                          rounds, slots, assigned, engine_seat=seat)
            by_seat = {s: rp.score_roster(picks, s, players_db, rulers, slots)
                       for s in seats if s != seat}
            scored = {"engine": rp.score_roster(picks, seat, players_db, rulers, slots),
                      "by_seat": by_seat}
            runs.append({
                "engine_seat": seat,
                "style_by_seat": assigned,
                "engine": scored["engine"],
                "controls": [by_seat[s] for s in sorted(by_seat)],
                "by_style": {name: compare_by_style(picks, assigned, scored, name)
                             for name in rp.RULERS},
            })
            round_one.append(round_one_positions(picks))
            composition.append(composition_by_style(picks))

        block = {
            resume_join.PRODUCED_AT: commit,
            "label": spec["label"], "teams": spec["teams"], "superflex": spec["superflex"],
            "scoring": spec["scoring"], "te_premium": spec["te_premium"],
            "pool": len(points), "rounds": rounds, "runs": len(runs),
            "adp_ranked": len(adp), "adp_sentinel_excluded": adp_excluded,
            "admission_gate": gate,
            "styles_admitted": sorted(admitted),
            "by_ruler": {name: rp.compare(runs, name) for name in rp.RULERS},
            "round_one_positions": round_one,
            "composition_by_style": pool_composition(composition),
            "seat_runs": runs,
            "seconds": round(time.time() - t0, 1),
        }
        results.append(block)
        for name in rp.RULERS:
            c = block["by_ruler"][name]
            # ABSOLUTES FIRST, percentage second and only where it exists. These values sit near
            # zero and legitimately go negative, so a ratio against a near-zero control mean
            # manufactures a huge number out of a tiny difference -- `compare` reports the
            # percentage over `advantage_population` only, and this line must not imply
            # otherwise. Key names are read from `compare`'s own output rather than guessed: the
            # first draft of this line invented two key names that `compare` does not emit,
            # printed None for both, and read exactly like a run that had produced no data.
            # (The invented names are deliberately NOT backticked here: a backtick in this
            # codebase means "this is a name in the system", `prose_names` enforces that, and
            # it caught this very comment naming one that exists nowhere -- #283's lesson,
            # arriving again within a day.)
            pct = c.get("mean_advantage_pct")
            tag = "TAUTOLOGY" if name == "cdme" else "strong claim"
            print(f"  {spec['label']:<16} {name:<7} ({tag:<12}) wins "
                  f"{c.get('engine_wins')}/{c.get('comparable_runs')} "
                  f"| engine {c.get('engine_mean')} vs field {c.get('control_mean')} "
                  f"| gap {c.get('mean_gap')}"
                  + (f" | {pct}% over {c.get('advantage_population')}" if pct is not None else ""),
                  flush=True)
        Path(args.out).write_text(json.dumps(
            {"commit": commit, "complete": False, "universe": universe,
             "formats": len(results), "results": results,
             "seconds": round(time.time() - started, 1)}, indent=2), encoding="utf-8")

    Path(args.out).write_text(json.dumps(
        {"commit": commit, "complete": True, "universe": universe,
         "formats": len(results), "results": results,
         "seconds": round(time.time() - started, 1)}, indent=2), encoding="utf-8")
    print(f"{len(results)} formats -> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
