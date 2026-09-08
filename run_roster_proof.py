"""#205: does the engine actually build BETTER ROSTERS than a plain projection ranking?

    python3 run_roster_proof.py [--out PATH] [--formats N] [--rounds N]

THE BATTERY AND THIS ARE DIFFERENT QUESTIONS. The battery (#150) asks whether the engine breaks
its league's own rules -- a legality gate. This asks whether it is any GOOD, which no legality
gate can answer: an engine that always drafts the highest-projected player available is perfectly
legal and completely pointless. Both are freeze gates and neither substitutes for the other.

COMMITTED AS AN INSTRUMENT, and that is a repair rather than a convention. #177's harness lived
only in an ephemeral scratchpad and is GONE -- the freeze rests on numbers whose instrument no
longer exists, so they cannot be re-derived or challenged. Same defect as the battery reports
before evidence/batteries/, one layer worse: the tool, not just its output.

WHY #177'S NUMBERS CANNOT SIMPLY BE CITED. They predate #196 (identity partition, pool 2041 ->
2105, priced 329 -> 371), #172 (multi-position eligibility), #191/#202 (the availability
haircut) and #204 (the scoring-aware path reaching the simulation at all). Every one of those
changes what a chair drafts. Comparing a fresh engine arm against #177's saved control would be
the "new run vs old baseline" error that already cost this project a retracted finding (#176).

THE FIVE RULES THIS HARNESS EXISTS TO OBEY, each from a real incident:

1. ONE PROCESS, ONE CODE VERSION, ONE TOGGLE. Both arms are drafted here, back to back, from
   the same loaded merger. Never a fresh run against a saved baseline.
2. THE SAME POOL FOR BOTH ARMS. Restricted to players BOTH yardsticks can price. #176 came
   from an engine drafting players the scorer then excluded while the control drafted only
   players it could score -- the arms were not playing the same game. `pool` is reported
   unconditionally so a reader can see the restriction happened.
3. PRODUCTION PRICING ON BOTH ARMS (#204). sleeper_projections + SLEEPER_BASIS_SEASON_SUM. A
   control priced differently from the engine is not a control.
4. set_league_format BEFORE EVERY FORMAT. Scoring propagates by FILE SELECTION; a battery that
   skipped this drafted 32 formats from one export and reported byte-identical results as
   findings.
5. ABSENCE COUNTED SEPARATELY FROM ZERO. `is not None` and `> 0` are different questions, in
   the instrument as much as in the engine.
6. THE CONTROL MUST BE ONE SOMEBODY WOULD ACTUALLY PLAY. The first version of this file ranked
   purely on projected points and was measured taking 24 CONSECUTIVE QBs in a 1QB PPR league --
   every control team fielded one and benched the rest. The engine "beat" it 12 of 12 seats by
   a mean of +503%, which measured nothing but that one arm knew what a lineup was. A baseline
   nobody would ever play is a strawman and beating it is not evidence. See control_pick.
7. TWO RULERS, NEVER COLLAPSED. The engine maximises roughly `cdme`; the control maximises
   `points`; measured, the two correlate at only r=0.241 over the 475-player pool. Scoring on
   either one alone hands the win to whoever optimises it. Both are reported side by side, and
   this harness deliberately emits NO single verdict. See RULERS.

RULES 6 AND 7 ARE WHY #177 CANNOT BE TREATED AS SETTLED. Its harness is gone, so whether it had
either flaw is now unknowable -- but its headline (engine ahead in 7 of 8 arms, the single loss
superflex-on-projection) is exactly the pattern an unfair control would produce: a QB-hoarding
control is accidentally NEAR-OPTIMAL in superflex, which is the one place #177's engine lost.
That is a complete alternative explanation for #177's entire result, and it cannot be ruled out.
Registered as #208. This run supersedes #177 rather than confirming it.

SEAT CONTROL. Draft position is worth more than anything the engine does, so a comparison that
does not control for it measures the snake. Every format runs once per seat, with the engine in
that seat and the control everywhere else, so each arm holds every seat exactly once.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import lineup_optimizer as lo
import pick_synthesis
import resume_join
import run_draft_battery as rdb

REPORT_PATH = Path("ROSTER_PROOF.json")

#: Six boards, chosen so the result can be attributed rather than just observed.
#: - two superflex arms, because #177's single loss was superflex-on-projection and #184 says
#:   the startable floor overrides demand there. If the engine loses again, it loses in a place
#:   whose mechanism is already named.
#: - three 1QB arms, where SUPER_FLEX_QB_SHARE provably cannot reach (#178's blast radius), so
#:   any movement there is NOT that constant.
#: - one TE-premium arm, the other axis that propagates by file selection.
PROOF_FORMATS = [
    {"label": "12T_ppr",        "teams": 12, "superflex": False, "scoring": "ppr",      "te_premium": False},
    {"label": "12T_ppr_SF",     "teams": 12, "superflex": True,  "scoring": "ppr",      "te_premium": False},
    {"label": "10T_ppr",        "teams": 10, "superflex": False, "scoring": "ppr",      "te_premium": False},
    {"label": "10T_ppr_SF",     "teams": 10, "superflex": True,  "scoring": "ppr",      "te_premium": False},
    {"label": "12T_standard",   "teams": 12, "superflex": False, "scoring": "standard", "te_premium": False},
    {"label": "12T_ppr_TEP",    "teams": 12, "superflex": False, "scoring": "ppr",      "te_premium": True},
]


def scoreable_pool(merger, players_db, league, season):
    """The players BOTH arms can price, and nothing else (rule 2).

    The engine prices from the board; the control ranks by projected points. A player either
    yardstick cannot see would let one arm draft someone the other could not even consider,
    which is not a comparison. Returns {player_id: projected_points}.
    """
    board = dr.compute_draft_board(
        merger, players_db, [], my_roster_id=None, league=league, mode="balanced",
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    return {str(r["player_id"]): r["projected_points"] for r in board
            if r.get("universal_value") is not None and r.get("projected_points") is not None}


def unmet_slot_positions(my_player_ids, players_db, slots) -> set[str]:
    """Which positions would fill a starting slot this roster has not yet covered.

    Solved with THE SHIPPED OPTIMIZER at a flat value of 1.0, which turns it into a pure
    feasibility question -- exactly the idiom unfilled_starting_slots already uses. A second
    hand-rolled slot-filling rule here would be a second home for a vocabulary that has one
    (#126), and it would silently disagree with the solver that scores the result.

    Empty return means every starting slot is already coverable, i.e. the roster is on to depth.
    """
    entries = [{"id": pid, "value": 1.0,
                "eligible": set((players_db.get(pid) or {}).get("fantasy_positions")
                                or ([(players_db.get(pid) or {}).get("position")]
                                    if (players_db.get(pid) or {}).get("position") else []))}
               for pid in my_player_ids]
    filled = {a["slot_id"] for a in lo.optimize_lineup(entries, slots)["assignments"]}
    return {pos for sl in slots if sl["slot_id"] not in filled for pos in sl["eligible"]}


def control_pick(available, points, my_player_ids, players_db, slots) -> str:
    """The yardstick: best projected points AT A POSITION I STILL NEED TO START, else best
    available by projection. player_id is the deterministic tiebreak.

    THE POSITIONAL FILTER IS NOT A COURTESY TO THE CONTROL -- IT IS WHAT MAKES IT A CONTROL.
    The first version of this function ranked on projection alone, and it was measured doing
    the only thing that rule can do: in a 1QB PPR league it took **24 consecutive QBs**, because
    quarterbacks score the most raw points. Every control team then fielded one QB and benched
    the rest, the engine "won" 12 of 12 seats by a mean of +503%, and the number meant nothing
    except that one arm knew what a lineup was. No manager with a projection sheet drafts three
    QBs in three rounds; a baseline nobody would ever play is a strawman, and beating it is not
    evidence. Ranking by projection while covering your starters is what managers actually do,
    and it is the thing the engine has to beat to justify existing.
    """
    need = unmet_slot_positions(my_player_ids, players_db, slots)
    if need:
        eligible = [pid for pid in available
                    if (set((players_db.get(pid) or {}).get("fantasy_positions")
                            or ([(players_db.get(pid) or {}).get("position")]
                                if (players_db.get(pid) or {}).get("position") else []))
                        & need)]
        if eligible:
            available = eligible
    return min(available, key=lambda pid: (-points[pid], pid))


def run_one(merger, players_db, league, pick_order, engine_seat, points, season, rounds, slots):
    """One draft: the engine holds `engine_seat`, the control holds every other seat."""
    picks: list[dict] = []
    taken: set[str] = set()
    mine: dict[str, list[str]] = {}
    num_teams = len(set(str(r) for r in pick_order))
    for idx in range(min(len(pick_order), rounds * num_teams)):
        seat = str(pick_order[idx])
        round_no = idx // num_teams + 1
        if seat == engine_seat:
            snap = pick_synthesis.build_snapshot(
                merger, players_db, picks, pick_order, idx, seat, league,
                pick_label=f"{round_no}.{(idx % num_teams) + 1:02d}",
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
            chosen = next((c.player_id for c in snap.candidates
                           if str(c.player_id) in points and str(c.player_id) not in taken), None)
        else:
            free = [pid for pid in points if pid not in taken]
            chosen = (control_pick(free, points, mine.get(seat, []), players_db, slots)
                      if free else None)
        if chosen is None:
            break
        taken.add(str(chosen))
        mine.setdefault(seat, []).append(str(chosen))
        picks.append({"pick_no": idx + 1, "round": round_no, "roster_id": seat,
                      "player_id": str(chosen)})
    return picks


#: The two rulers this proof is scored on, and it is scored on BOTH, always, without ever
#: collapsing them into one verdict.
#:
#: WHY TWO. The engine maximises something very close to `cdme`; the control maximises `points`.
#: Whichever single ruler you pick, you have handed the win to whoever optimises it -- and the
#: first version of this harness picked `cdme` alone and duly reported the engine winning every
#: seat by +503%. Measured, the two rulers correlate at only r=0.241 across the 475-player pool,
#: so they are not two views of one quantity; they are different questions:
#:   cdme   -- what the roster is WORTH as dynasty assets (the engine's own objective)
#:   points -- what the roster is projected to SCORE this season (the control's objective)
#: A win on `cdme` alone is a tautology and must be reported as one. A win on `points` too is
#: the strong claim: the engine beat the control at the control's own game.
RULERS = ("cdme", "points")

#: WHICH QUANTITY EACH RULER IS COMPARED ON, and this mapping is the whole point of the entry.
#:
#: Measured, not assumed: 83.8% of the 475-player shared pool carries a NEGATIVE
#: universal_value (min −319.22, median −30.74, max +79.03), and `lineup_optimizer` has no
#: "leave it empty" move — `linear_sum_assignment` fills every slot it can, so a roster thin at
#: a position is FORCED to start a deeply negative player rather than start nobody. Verified
#: directly: one +50 WR and one −80 RB against a WR and an RB slot returns total −30, not +50.
#:
#: So a STARTING-LINEUP SUM OF universal_value IS A CATEGORY ERROR. universal_value is an asset
#: LEVEL — what a player is worth to OWN — not a weekly production rate that starting him
#: realises. Summing the started subset of it measures POSITIONAL BREADTH (who is forced to
#: start the fewest negatives), which is the control's design by construction and not a virtue
#: of anyone's roster. This is the same level-vs-rate distinction the owner ruled on in #55.
#: Under `points` the starting-lineup sum is exactly right — that IS what you field and score.
#:
#: Both quantities are reported for both rulers regardless; this only says which one the win
#: rate is computed on, so the choice is named rather than buried in an aggregate.
COMPARE_ON = {
    "cdme": "total_value",      # what you OWN
    "points": "starter_value",  # what you FIELD
}

#: A KNOWN CONTAMINATION, named rather than fixed. `total_value` sums deep negatives, which
#: assumes a below-replacement player is a LIABILITY you carry rather than someone you simply
#: drop. What a below-replacement player is actually worth to own is #155 ("a replacement-level
#: player prices at 0.00 tautologically") and #165, both RESERVED. Flooring the sum at zero here
#: would answer a reserved question by implementation and would be exactly the invented bound
#: #56 forbids. Both arms are contaminated identically, so the COMPARISON survives it; the
#: absolute cdme totals do not, and must not be quoted as roster worth.
CDME_TOTAL_CONTAMINATION = ("total_value sums below-replacement negatives; what such a player "
                            "is worth to own is reserved (#155/#165)")


def score_roster(picks, seat, players_db, rulers, slots):
    """starter_value under EVERY ruler for one seat, from one shared lineup solve per ruler.

    THE SAME LINEUP SOLVE THE BATTERY USES, deliberately -- lo.slots_from_roster_positions +
    lo.optimize_lineup, exactly as draft_battery.roster_strength calls them. Two arms of the
    freeze judged by two different solvers would not be comparable, and a second solver written
    here would be a second home for a vocabulary that already has one (#126).

    ELIGIBILITY COMES FROM fantasy_positions, not `position` (#172). A player listed RB/WR is
    eligible at both; collapsing him to his primary would bench him out of a FLEX he can legally
    fill and understate every roster holding one.

    UNPRICED PLAYERS ENTER THE SOLVE AT 0.0, and that is #168, not an oversight. It is the same
    thing roster_strength does and documents: choosing what an unpriced player is worth inside a
    lineup solve IS #165, which the owner reserved. Answering it here -- by dropping such players,
    or imputing a rank-based price -- would settle a reserved question by implementation, in an
    instrument built to inform the freeze. So the zero stands and the ABSENCE TRAVELS INSTEAD:
    `unpriced` counts it per ruler, `values_are_totals` says whether the totals are totals or
    floors (rule 5). Both arms are exposed identically, so the comparison survives the defect
    even though neither arm's absolute number does.
    """
    mine = [p["player_id"] for p in picks if str(p["roster_id"]) == str(seat)]
    eligible = {pid: set((players_db.get(pid) or {}).get("fantasy_positions")
                         or ([(players_db.get(pid) or {}).get("position")]
                             if (players_db.get(pid) or {}).get("position") else []))
                for pid in mine}
    out = {"players": len(mine)}
    for name in RULERS:
        values = rulers[name]
        entries = [{"id": pid, "value": values.get(pid) or 0.0, "eligible": eligible[pid]}
                   for pid in mine]
        solved = lo.optimize_lineup(entries, slots)
        starter = round(solved["total_value"], 2)
        total = round(sum(e["value"] for e in entries), 2)
        unpriced = sum(1 for pid in mine if values.get(pid) is None)
        out[name] = {
            "starter_value": starter,
            "bench_value": round(total - starter, 2),
            "total_value": total,
            "starters_filled": len(solved["assignments"]),
            "starting_slots": len(slots),
            "unpriced": unpriced,
            "values_are_totals": unpriced == 0,
        }
    return out


def compare(runs, ruler):
    """Engine vs the mean of the controls it actually sat against, under ONE ruler.

    The quantity compared is COMPARE_ON[ruler] -- see that mapping for why it is not
    starter_value for both.

    Counted, not imputed (rule 5): a run enters the rate only if BOTH sides produced a number,
    and `comparable_runs` is reported so nobody quotes a rate over an empty set.

    A PERCENTAGE IS ONLY REPORTED WHEN ITS DENOMINATOR CAN CARRY ONE. These values legitimately
    sit near zero and legitimately go negative, and (eng - ctl)/|ctl| against a near-zero ctl
    manufactures a huge number out of a tiny difference -- the first full-depth run printed
    -171.7% for exactly that reason. Percentages are therefore computed only where the control
    mean is meaningfully non-zero, `advantage_population` says over how many runs, and the
    ABSOLUTE means are always reported so the percentage can never be read alone.
    """
    field = COMPARE_ON[ruler]
    comparable, wins, advantages, engs, ctls = [], 0, [], [], []
    for r in runs:
        eng = r["engine"][ruler][field]
        ctl = [c[ruler][field] for c in r["controls"]]
        if eng is None or any(v is None for v in ctl) or not ctl:
            continue
        comparable.append(r)
        mean_ctl = sum(ctl) / len(ctl)
        engs.append(eng)
        ctls.append(mean_ctl)
        if eng > mean_ctl:
            wins += 1
        # A denominator smaller than 1% of the engine's own magnitude cannot carry a ratio.
        if abs(mean_ctl) > max(1e-9, 0.01 * abs(eng)):
            advantages.append((eng - mean_ctl) / abs(mean_ctl) * 100)
    return {
        "compared_on": field,
        "comparable_runs": len(comparable),
        "engine_wins": wins,
        "win_rate": round(wins / len(comparable), 4) if comparable else None,
        # The absolutes. These are the primary numbers; the percentages are secondary.
        "engine_mean": round(sum(engs) / len(engs), 2) if engs else None,
        "control_mean": round(sum(ctls) / len(ctls), 2) if ctls else None,
        "mean_gap": round((sum(engs) - sum(ctls)) / len(engs), 2) if engs else None,
        "advantage_population": len(advantages),
        "mean_advantage_pct": round(sum(advantages) / len(advantages), 3) if advantages else None,
        "worst_advantage_pct": round(min(advantages), 3) if advantages else None,
        "best_advantage_pct": round(max(advantages), 3) if advantages else None,
    }


def console_line(block) -> str:
    """ABSOLUTES FIRST. A percentage against a near-zero denominator is exactly the "plausible
    number about something else" this project keeps catching, so eng/ctl are printed on every
    line and the ratio is shown only where one could be computed.

    One home (#126) so a CARRIED format prints identically to a freshly computed one -- with a
    marker, never a different shape. Two console vocabularies for one quantity is how a reader
    ends up believing a resumed run measured something a fresh run did not."""
    return (f"{block['label']:16s} pool={block['pool']:5d} rounds={block['rounds']:2d} "
            + "  ".join(
                f"[{name}/{block['by_ruler'][name]['compared_on'].split('_')[0]}] "
                f"eng={block['by_ruler'][name]['engine_mean']} "
                f"ctl={block['by_ruler'][name]['control_mean']} "
                f"gap={block['by_ruler'][name]['mean_gap']} "
                f"win={block['by_ruler'][name]['engine_wins']}/"
                f"{block['by_ruler'][name]['comparable_runs']}"
                for name in RULERS)
            + f"  {block['seconds']:7.1f}s"
            + ("  [carried from " + str(block.get("produced_at_commit")) + "]"
               if block.get("carried_forward") else ""))


def _write_report(args, commit, universe, season, scoring, results, started, *, complete):
    """One report shape for the mid-run and end-of-run writes, so a partial file is never a
    different document from a finished one -- `complete` says which it is, and a reader who
    finds `complete: false` knows the run did not reach its last format."""
    Path(args.out).write_text(json.dumps({
        "commit": commit,
        "complete": complete,
        "formats_done": len(results),
        # #215: a resumed report is a JOIN ACROSS PROCESSES, and says so. `commit` above is the
        # commit THIS process ran at; commits_present is every commit that contributed a block.
        # A reader who sees more than one entry there knows to check they agree before quoting
        # the report as a single result.
        "commits_present": resume_join.commits_present(results),
        "carried_forward": [b["label"] for b in results if b.get(resume_join.CARRIED)],
        "universe": universe,
        "rounds_requested": args.rounds or "derived from roster_positions",
        "pricing": {"priced_from": "vendor+sleeper",
                    "sleeper_basis": dr.SLEEPER_BASIS_SEASON_SUM,
                    "season_projections_supplied": len(season),
                    # #212: supplied counts dict entries; priceable counts entries carrying a
                    # stat line. ADP-only entries are supplied and cannot be priced.
                    "season_projections_priceable": rdb.priceable_projection_count(season),
                    "scoring_keys": len(scoring)},
        "control": "best projected points at an unfilled starting slot, else best available "
                   "by projection; player_id tiebreak",
        "rulers": {
            "cdme": "pre-draft board universal_value -- the engine's own objective",
            "points": "projected season points -- the control's objective",
        },
        "compared_on": dict(COMPARE_ON),
        "known_contamination": {"cdme": CDME_TOTAL_CONTAMINATION},
        # THIS PROCESS ONLY. On a resumed run the carried formats were timed in an earlier
        # process; their own per-format `seconds` are the authority for those. Summing this
        # field across a join would invent a wall clock that never elapsed.
        "seconds_this_process": round(time.time() - started, 1),
        "formats": results,
    }, indent=2, default=str), encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(REPORT_PATH))
    ap.add_argument("--formats", type=int, default=len(PROOF_FORMATS))
    #: 0 = DERIVE from the league's own roster_positions (the default, and the only setting
    #: that produces a legal draft). A hand-set round count is a second source of truth about
    #: roster size and can silently disagree with the league it drafts -- 15 rounds into this
    #: repo's 14-slot mock roster drafts a player nobody can roster. A SHORT count is worse than
    #: illegal, it is misleading: measured at 8 rounds of a 14-slot roster the engine had filled
    #: 5 of 8 starting slots to the control's 8, and the points ruler read -43% -- but that
    #: compares who FRONT-LOADS starters, not who ends up with the better roster. Only override
    #: this for a smoke test, and never report a short run as an answer to #205.
    ap.add_argument("--rounds", type=int, default=0)
    #: #215: reuse the completed format blocks already in --out instead of recomputing them.
    #: OFF by default: a silent resume would let a stale file masquerade as a fresh measurement.
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args(argv)

    commit = resume_join.head_commit()
    scoring = rdb.scoring_settings_from_capture()          # #213, before anything is drafted
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    print(f"commit {commit} | universe {universe['players_in_pool']} players "
          f"| captured {universe['captured_at']}", flush=True)

    specs = PROOF_FORMATS[:args.formats]
    # Keyed by label and consumed IN SPEC ORDER below, so a resumed report lists its formats in
    # the same order as a fresh one. Appending the carried blocks first would silently reorder
    # the document between two runs that measured the same thing.
    carried = {b["label"]: b for b in (
        resume_join.carry_forward(args.out, [sp["label"] for sp in specs], units_key="formats")
        if args.resume else [])}
    results = []
    started = time.time()
    for spec in specs:
        if spec["label"] in carried:
            block = carried[spec["label"]]      # already stamped carried_forward by the join
            results.append(block)
            print(console_line(block), flush=True)
            continue
        # #213: the REAL rulebook, with this arm's rec/te-premium overlaid. Without it every
        # board here priced quarterbacks at zero and receivers at one point per catch, and
        # BOTH arms of the proof were then compared inside a league nobody plays.
        league = dr.build_mock_league(teams=spec["teams"], superflex=spec["superflex"],
                                      scoring=spec["scoring"], te_premium=spec["te_premium"],
                                      dynasty=True, base_scoring=scoring)
        merger.set_league_format(db.league_format_hint(league))          # rule 4
        points = scoreable_pool(merger, players_db, league, season)      # rule 2
        values = db.reference_values(merger, players_db, league,
                                     sleeper_projections=season,
                                     sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        seats = [str(i) for i in range(1, spec["teams"] + 1)]
        rounds = args.rounds or len(league.get("roster_positions") or [])
        pick_order = ds.generate_pick_order(seats, rounds, "snake")
        # Built ONCE per format and handed to both arms. Solving the same league's lineup from
        # two separately-built slot lists is how two arms end up judged by different rulers.
        slots = lo.slots_from_roster_positions(league.get("roster_positions") or [])

        rulers = {"cdme": values, "points": points}

        runs = []
        t0 = time.time()
        for seat in seats:                                               # seat control
            picks = run_one(merger, players_db, league, pick_order, seat,
                            points, season, rounds, slots)
            engine = score_roster(picks, seat, players_db, rulers, slots)
            controls = [score_roster(picks, s, players_db, rulers, slots)
                        for s in seats if s != seat]
            runs.append({"engine_seat": seat, "engine": engine, "controls": controls})

        block = {
            # #215: the commit this block's numbers were PRODUCED at. A resumed report joins
            # blocks from more than one process, and each block has to carry its own provenance
            # -- a single top-level commit on a joined document would be a false claim about
            # every block the current process did not compute.
            resume_join.PRODUCED_AT: commit,
            resume_join.CARRIED: False,
            "label": spec["label"], "teams": spec["teams"], "superflex": spec["superflex"],
            "scoring": spec["scoring"], "te_premium": spec["te_premium"],
            "pool": len(points),
            "rounds": rounds,
            "roster_slots": len(league.get("roster_positions") or []),
            "runs": len(runs),
            "by_ruler": {name: compare(runs, name) for name in RULERS},
            # PER-SEAT DETAIL IS RETAINED ON PURPOSE. #177's aggregates survived and its
            # instrument did not, so its numbers can neither be re-derived nor challenged.
            # Aggregates alone reproduce that failure one level down: a win rate cannot show
            # that every seat returned an identical advantage, which is exactly the artifact
            # signature that has to stay visible to a reader.
            "per_seat": [
                {"engine_seat": r["engine_seat"],
                 **{name: {
                     "compared_on": COMPARE_ON[name],
                     "engine": r["engine"][name][COMPARE_ON[name]],
                     "control_mean": round(
                         sum(c[name][COMPARE_ON[name]] for c in r["controls"])
                         / len(r["controls"]), 2) if r["controls"] else None,
                     "engine_starter_value": r["engine"][name]["starter_value"],
                     "engine_total_value": r["engine"][name]["total_value"],
                     "engine_starters_filled": r["engine"][name]["starters_filled"],
                     "starting_slots": r["engine"][name]["starting_slots"],
                 } for name in RULERS}}
                for r in runs],
            "engine_unpriced_total": {
                name: sum(r["engine"][name]["unpriced"] for r in runs) for name in RULERS},
            "seconds": round(time.time() - t0, 1),
        }
        results.append(block)
        # WRITTEN AFTER EVERY FORMAT, not once at the end. A 45-minute run whose output lands
        # only on the final line is the durability hole this whole item exists to close
        # (#177's harness, the battery reports before evidence/batteries/) reproduced one layer
        # in: a crash, a kill, or an unreadable intermediate result and there is nothing to
        # inspect. Each write is a complete, self-describing report of the formats done so far.
        _write_report(args, commit, universe, season, scoring, results, started, complete=False)
        print(console_line(block), flush=True)

    _write_report(args, commit, universe, season, scoring, results, started, complete=True)
    print("", flush=True)
    for name in RULERS:
        ahead = sum(1 for b in results if (b["by_ruler"][name]["win_rate"] or 0) > 0.5)
        print(f"  ruler {name:7s}: engine ahead in {ahead} of {len(results)} formats", flush=True)
    # Deliberately NOT reduced to a single pass/fail. The two rulers ask different questions
    # (see RULERS); a reader who wants one number has to say which question they meant.
    print(f"-> {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
