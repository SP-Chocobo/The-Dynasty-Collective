"""How well does a position's projection predict what actually happened? Run this on a networked
machine; the audit sandbox cannot reach Sleeper.

WHY THIS EXISTS. The `12T_ppr_K_DEF` arm showed the engine drafting team defenses about five
rounds too early (evidence/blind_pass/KDST_VALUATION.md). Three candidate levers were measured
and none can fix it: positional_forfeit never reaches the board, waiting_cost points the wrong
way, and every sane replacement choice leaves VOR near 30. A discount multiplier cannot
substitute -- the factor required is negative.

What is missing is upstream of all three: EVERY VALUATION TERM TRUSTS THE PROJECTION. `bpa`,
`waiting_cost` and `horizon_replacement` all agree the top defense is ~30 points clear of the
alternative because the projection says so, and nothing measures whether a position's
projections come true. This measures that.

WHAT IT PRODUCES, and it is a MEASUREMENT not a recommendation: per position, the REALISED gap
between the players projected at rank 1 and at replacement rank, against the PROJECTED gap. Their
ratio is how much of a position's projected spread actually materialises. A position whose
projections hold keeps its VOR; one whose projections are noise does not.

IT IS NOT A PROXY FOR K AND DST. Those two are priced on Sleeper-seeded projections
(draft_room.KDST_SEEDED_SOURCE_FILES), which is exactly the source this reads -- so for the two
positions that prompted the work, this measures the actual input the board uses.

NOTHING HERE CHOOSES A CONSTANT. It reports ratios. Turning a ratio into a term in the engine is
a separate decision with its own derivation (#56: a bound is not a threshold, and a measurement
is not a tuning knob).

    python3 measure_projection_accuracy.py --seasons 2023,2024 --out PROJECTION_ACCURACY.json

Runtime is dominated by the API: two calls per week per season, ~18 weeks, so ~72 calls for two
seasons. Sleeper asks for courtesy; there is a delay between calls.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import player_universe as pu
import sleeper_client as sc
import store_io

#: Positions worth reporting. K and DEF are the reason this exists; the others are the control --
#: a measurement that showed every position equally unpredictable would be measuring the
#: instrument, not the positions.
POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")

#: Courtesy delay between API calls. Not a tuning knob: Sleeper asks that /players/nfl be pulled
#: at most once a day and does not publish a rate limit for the stats endpoints, so this is
#: politeness toward a free public API rather than a measured requirement.
REQUEST_SPACING_SECONDS = 0.4

#: Weeks of a regular season. Fetched individually because the endpoint is per-week; a season
#: that ran short simply returns empty weeks, which are skipped rather than counted as zeros --
#: a missing week and a week where nobody scored are different facts.
REGULAR_SEASON_WEEKS = range(1, 19)


def _season_totals(client: sc.SleeperClient, season: str, scoring: dict,
                   *, log=print) -> tuple[dict[str, float], dict[str, float]]:
    """(projected_total, actual_total) per player_id for one season, scored under `scoring`.

    Both sides are scored through player_universe.score_projection -- THE SAME FUNCTION the
    engine uses -- so the comparison cannot drift from how the app values a stat line. Scoring
    the actuals with the projection's own scorer is the point: it removes scoring settings as a
    variable and leaves only "did the player do what was predicted".
    """
    projected: dict[str, float] = {}
    actual: dict[str, float] = {}
    for week in REGULAR_SEASON_WEEKS:
        proj = client.get_weekly_projections(season, week) or {}
        time.sleep(REQUEST_SPACING_SECONDS)
        stats = client._get(f"/stats/nfl/regular/{season}/{week}", base=sc.ROOT_URL) or {}
        time.sleep(REQUEST_SPACING_SECONDS)
        if not proj and not stats:
            continue
        log(f"  {season} wk{week:02d}: {len(proj):5d} projected, {len(stats):5d} actual")
        for pid, line in proj.items():
            projected[pid] = projected.get(pid, 0.0) + pu.score_projection(line, scoring)
        for pid, line in stats.items():
            actual[pid] = actual.get(pid, 0.0) + pu.score_projection(line, scoring)
    return projected, actual


def accuracy_by_position(projected: dict[str, float], actual: dict[str, float],
                         players_db: dict[str, dict], num_teams: int,
                         starters_by_position: dict[str, float]) -> dict[str, dict]:
    """Per position: the PROJECTED spread from rank 1 to replacement rank, and what those same
    two players ACTUALLY scored.

    THE RANKS COME FROM THE PROJECTION, NOT FROM THE RESULT. That is the whole design. Ranking by
    outcome and then measuring the outcome gap would report a spread that is real but unownable:
    nobody drafts with hindsight. The question is what you got by believing the projection, so
    the projection picks the players and the season says what they were worth.
    """
    out: dict[str, dict] = {}
    for position in POSITIONS:
        rank = max(1, int(round(num_teams * starters_by_position.get(position, 0.0))))
        pool = [(pid, value) for pid, value in projected.items()
                if pu.player_position(players_db.get(pid) or {}) == position
                and pid in actual]
        if len(pool) <= rank:
            out[position] = {"measurable": False,
                             "why": f"{len(pool)} players with both a projection and a result, "
                                    f"against replacement rank {rank}"}
            continue
        pool.sort(key=lambda row: row[1], reverse=True)
        best_id, best_proj = pool[0]
        repl_id, repl_proj = pool[rank - 1]
        projected_gap = round(best_proj - repl_proj, 2)
        realised_gap = round(actual[best_id] - actual[repl_id], 2)
        out[position] = {
            "measurable": True,
            "replacement_rank": rank,
            "pool": len(pool),
            "projected_gap": projected_gap,
            "realised_gap": realised_gap,
            # None, never 0.0: a projected gap of zero makes the ratio undefined rather than
            # perfect, and a 0.0 here would read as "none of it materialised".
            "realised_share": (round(realised_gap / projected_gap, 3)
                               if projected_gap else None),
            "best": pu.player_name(players_db.get(best_id) or {}, best_id),
            "replacement": pu.player_name(players_db.get(repl_id) or {}, repl_id),
        }
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--seasons", default="2024",
                        help="comma-separated, e.g. 2023,2024. More seasons is a better "
                             "measurement; one season is one sample of a noisy process.")
    parser.add_argument("--out", default="PROJECTION_ACCURACY.json")
    args = parser.parse_args(argv)

    import draft_battery as dbat
    import run_draft_battery as rdb
    import draft_room as dr

    scoring = rdb.scoring_settings_from_capture()
    players_db, _ = rdb.build_players_db_from_capture()
    arm = next(a for a in dbat.league_matrix(scoring) if a["label"] == "12T_ppr_K_DEF")
    starters = dr.starter_slot_counts(arm["league"]["roster_positions"], None, arm["teams"])

    client = sc.SleeperClient()
    seasons = [s.strip() for s in args.seasons.split(",") if s.strip()]
    per_season = {}
    for season in seasons:
        print(f"fetching {season} ...")
        try:
            projected, actual = _season_totals(client, season, scoring)
        except sc.SleeperAPIError as exc:
            print(f"  {season}: unreachable -- {exc}", file=sys.stderr)
            continue
        if not projected or not actual:
            print(f"  {season}: no data returned; skipped", file=sys.stderr)
            continue
        per_season[season] = accuracy_by_position(
            projected, actual, players_db, arm["teams"], starters)

    if not per_season:
        print("no season produced data -- nothing written", file=sys.stderr)
        return 1

    print()
    print(f"{'pos':<5}{'season':<9}{'proj gap':>10}{'real gap':>10}{'share':>9}")
    for season, table in per_season.items():
        for position in POSITIONS:
            row = table.get(position) or {}
            if not row.get("measurable"):
                print(f"{position:<5}{season:<9}{'--':>10}{'--':>10}{'--':>9}  {row.get('why','')}")
                continue
            share = row["realised_share"]
            print(f"{position:<5}{season:<9}{row['projected_gap']:>10.1f}"
                  f"{row['realised_gap']:>10.1f}"
                  f"{(f'{share:.2f}' if share is not None else 'n/a'):>9}")

    shares = {p: [t[p]["realised_share"] for t in per_season.values()
                  if (t.get(p) or {}).get("measurable") and t[p]["realised_share"] is not None]
              for p in POSITIONS}
    report = {
        "_comment": ("Per position: how much of the PROJECTED rank-1-to-replacement gap actually "
                     "materialised. Ranks are assigned by projection, never by outcome. This is a "
                     "measurement, not a tuning knob -- turning it into an engine term is a "
                     "separate decision with its own derivation (#56)."),
        "seasons": seasons,
        "scoring_source": "data/fixtures/sleeper_capture.json",
        "per_season": per_season,
        "median_realised_share": {p: (round(statistics.median(v), 3) if v else None)
                                  for p, v in shares.items()},
    }
    store_io.write(Path(args.out), report)
    print(f"\n-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
