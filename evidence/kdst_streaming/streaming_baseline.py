"""#30: what a STREAMER actually got, measured, against what the engine assumes they got.

Run from the repo root. No network.

THE QUESTION. `draft_room.replacement_levels` prices a position against `live_starter_demand` --
the (teams x slots)-th best player by projection, carried for the WHOLE SEASON. For a streamed
position that is the wrong alternative. Nobody who skips a defense owns DEF12 for seventeen weeks;
they own whoever is best on the wire, re-chosen every week.

THE TWO QUANTITIES, and the only honest way to compare them is to score BOTH on realized points:

  SEASON-LONG HOLD   the realized season total of the player who was (teams x slots)-th best
                     BY PROJECTION. That is the engine's current alternative, scored on what
                     actually happened rather than on what was projected.

  STREAMING          for each week, the best REALIZED score among players at that position who
                     are NOT in the projected top (teams x slots) -- i.e. the wire. Summed.

Both use the same realized data and the same rostered set, so the difference is the POLICY and
nothing else.

WHY THE ROSTERED SET IS DEFINED BY PROJECTION. A draft rosters players it believes will be good,
so the unrostered pool is "everyone the projection ranked below the starters' demand". Defining it
by realized rank instead would hand the streamer hindsight -- he would be picking from a wire
stocked by a season nobody had seen. That is the same hindsight error that made a rank-1-to-
replacement gap look inflated, and it is avoided here in the same way: RANKS COME FROM THE
PROJECTION, OUTCOMES COME FROM THE SEASON.

WHAT THIS DOES NOT MODEL, stated so no one reads more into it than it carries:
  - Waiver priority, FAAB, and the fact that rivals stream too. A real wire is contested, so this
    is an UPPER BOUND on streaming, not an estimate of it. A bound is not a threshold (#56).
  - Bye weeks and injuries on the rostered side.
  - That the streamer must decide BEFORE the week, not after. Picking the week's best in
    hindsight is the optimistic end; the pessimistic end is the median, so both are printed.

THE ARM TO ARGUE FROM IS `stream_projected`, AND THE OTHER TWO ARE ITS BOUNDS.

  stream_projected   each week, take the wire player with the highest WEEKLY PROJECTION, and
                     score what he ACTUALLY did. This is what streaming IS -- you read this
                     week's projections, you pick, and the game happens to you. No hindsight
                     enters the choice; hindsight only scores it.
  stream_best        each week's realized maximum over the wire. Pure hindsight, an UPPER BOUND
                     on any streamer, reported so the projected arm can be read against it.
  stream_median      the wire's median realized score. Reported and then largely ignored: it was
                     measured at 0.0 for QB/RB/WR/TE, because a 1,331-player wire is mostly
                     players who did not play. It measures wire DEPTH, not streaming, and it is
                     kept only so that fact is visible rather than rediscovered.

A FIRST VERSION OF THIS FILE HAD ONLY THE LAST TWO, and it could not have answered the question:
one arm was hindsight and the other was junk. The projections were sitting in the same directory.
"""

from __future__ import annotations

import collections
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import capture_weekly_lines as cwl
import draft_battery as db
import draft_room as dr
import player_universe as pu
import run_draft_battery as rdb

SEASONS = ("2023", "2024")
ARM = "12T_ppr_K_DEF"
#: Positions to measure. K and DEF are the streamed ones this item is about; the others are the
#: CONTROL -- if every position showed the same gap, this would be measuring the instrument
#: rather than streaming.
POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")
OUT = Path("evidence/kdst_streaming/STREAMING_BASELINE.json")


def totals(season: str, kind: str, scoring: dict) -> dict[str, float]:
    out: dict[str, float] = collections.defaultdict(float)
    for _week, lines in cwl.load_season(season, kind).items():
        for pid, stats in lines.items():
            out[pid] += pu.score_projection(stats, scoring)
    return dict(out)


def weekly(season: str, kind: str, scoring: dict) -> dict[str, dict[str, float]]:
    """{week: {player_id: points}} -- kept per week, because a streaming baseline is a sum of
    weekly choices and collapsing to a season total first destroys exactly the thing being
    measured."""
    return {week: {pid: pu.score_projection(stats, scoring) for pid, stats in lines.items()}
            for week, lines in cwl.load_season(season, kind).items()}


def main() -> int:
    scoring = rdb.scoring_settings_from_capture()
    players_db, _ = rdb.build_players_db_from_capture()
    arm = next(a for a in db.league_matrix(scoring) if a["label"] == ARM)
    starters = dr.starter_slot_counts(arm["league"]["roster_positions"], None, arm["teams"])
    teams = arm["teams"]

    report: dict = {
        "_comment": ("#30: the realized season total of a season-long hold at replacement rank, "
                     "against what a streamer got from the wire. Ranks come from the PROJECTION, "
                     "outcomes from the season. Streaming arms are BOUNDS, not estimates -- the "
                     "wire is uncontested here. See streaming_baseline.py."),
        "arm": ARM, "teams": teams, "seasons": list(SEASONS), "per_season": {},
    }

    for season in SEASONS:
        proj = totals(season, "projections", scoring)
        proj_weekly = weekly(season, "projections", scoring)
        real_weekly = weekly(season, "stats", scoring)
        real_season = totals(season, "stats", scoring)
        if not proj or not real_season:
            print(f"  {season}: no capture; skipped", file=sys.stderr)
            continue

        rows = {}
        for position in POSITIONS:
            demand = max(1, int(round(teams * starters.get(position, 0.0))))
            pool = sorted((pid for pid in proj
                           if pu.player_position(players_db.get(pid) or {}) == position),
                          key=lambda p: -proj[p])
            if len(pool) <= demand:
                rows[position] = {"measurable": False,
                                  "why": f"pool {len(pool)} <= demand {demand}"}
                continue
            rostered = set(pool[:demand])
            wire = [pid for pid in pool[demand:]]

            # The engine's current alternative: the player AT replacement rank, held all season,
            # scored on what he actually did. None, never 0.0, if he never recorded a week.
            held_id = pool[demand - 1]
            held = real_season.get(held_id)

            best_weeks, median_weeks, projected_weeks, covered, blind = [], [], [], 0, 0
            for week, points in sorted(real_weekly.items(), key=lambda kv: int(kv[0])):
                scores = [points[pid] for pid in wire if pid in points]
                if not scores:
                    # A week with nobody on the wire is ABSENT, not a zero-point week. Counted
                    # separately so a short season cannot masquerade as a bad streamer (#187).
                    continue
                covered += 1
                best_weeks.append(max(scores))
                median_weeks.append(statistics.median(scores))
                # THE HONEST ARM. Choose on THIS WEEK'S projection, score on what happened.
                # A wire player with a realized line but no projection that week cannot be
                # chosen -- the streamer could not have seen him -- so he is excluded from the
                # choice rather than treated as projecting zero.
                week_proj = proj_weekly.get(week) or {}
                choosable = [(week_proj[pid], pid) for pid in wire
                             if pid in week_proj and pid in points]
                if not choosable:
                    blind += 1
                    continue
                projected_weeks.append(points[max(choosable)[1]])

            rows[position] = {
                "measurable": True,
                "demand_rank": demand,
                "pool": len(pool),
                "wire": len(wire),
                "weeks_with_a_wire": covered,
                "held_at_replacement": round(held, 2) if held is not None else None,
                "held_player": pu.player_name(players_db.get(held_id) or {}, held_id),
                "stream_best_weekly": round(sum(best_weeks), 2) if best_weeks else None,
                "stream_median_weekly": round(sum(median_weeks), 2) if median_weeks else None,
                "stream_projected": round(sum(projected_weeks), 2) if projected_weeks else None,
                "weeks_chosen_on_projection": len(projected_weeks),
                "weeks_with_no_projected_wire": blind,
            }
            for key in ("stream_best_weekly", "stream_median_weekly", "stream_projected"):
                value, base = rows[position][key], rows[position]["held_at_replacement"]
                rows[position][key + "_over_held"] = (
                    round(value - base, 2) if value is not None and base is not None else None)
        report["per_season"][season] = rows

    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print("What a SEASON-LONG HOLD at replacement rank actually scored, against THE WIRE.")
    print("Both scored on realized points. Ranks from the projection. Streaming arms are BOUNDS.\n")
    head = (f"{'pos':<5}{'season':<8}{'rank':>5}{'wire':>6}{'held':>9}"
            f"{'STREAM(proj)':>14}{'vs held':>9}{'wks':>5}{'best(hind)':>12}")
    print(head)
    for season, rows in report["per_season"].items():
        for position in POSITIONS:
            row = rows.get(position) or {}
            if not row.get("measurable"):
                print(f"{position:<5}{season:<8}  {row.get('why','')}")
                continue
            def cell(value, width, places=1):
                """A number, or '--' for ABSENT. Never 0.0 for absent (#187)."""
                return (f"{value:>{width}.{places}f}" if value is not None
                        else f"{'--':>{width}}")
            print(f"{position:<5}{season:<8}{row['demand_rank']:>5}{row['wire']:>6}"
                  + cell(row["held_at_replacement"], 9)
                  + cell(row["stream_projected"], 14)
                  + cell(row["stream_projected_over_held"], 9)
                  + f"{row['weeks_chosen_on_projection']:>5}"
                  + cell(row["stream_best_weekly"], 12))
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
