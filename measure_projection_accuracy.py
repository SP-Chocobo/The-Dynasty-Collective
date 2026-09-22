"""How well does a position's projection predict what actually happened? Needs a host allowed to
reach `api.sleeper.app`.

WHAT "CANNOT REACH SLEEPER" ACTUALLY MEANS, measured rather than assumed (#52 phase 8). The
Claude Code remote sandbox HAS outbound HTTPS -- through an agent proxy with a host allowlist --
and `api.sleeper.app` is not on it: the connection fails at `CONNECT tunnel failed, response
403`, not at DNS or at a missing route. So this is an ENVIRONMENT NETWORK POLICY setting, not an
absent capability, and the remedy is either adding that host to the environment's allowlist or
running this on the owner's own machine. The earlier wording sent a reader looking for a
different machine when a policy line would do.

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

IT MAY WELL BE A PROXY FOR K AND DST, AND THAT IS NOT ESTABLISHED. This claimed the opposite as
fact: "Those two are priced on Sleeper-seeded projections (draft_room.KDST_SEEDED_SOURCE_FILES),
which is exactly the source this reads -- so for the two positions that prompted the work, this
measures the actual input the board uses." Measured, the last clause is false. The board prices K
and DST from two committed CSVs; this reads /projections/nfl. Both are "Sleeper", and that is the
whole extent of what was ever checked:

    artifact                    DEF n  DEF r1  DEF gap   K n   K r1  K gap
    weekly-sum 2023                32   135.3     18.8    153  154.5   20.0
    weekly-sum 2024                32   121.5      6.7    153  159.9   29.8
    board CSV (2026-08-25)         32   111.0     13.0     37  116.0   11.0

SETTLED, on a 2026 capture -- the CSVs' own vintage, because a 2026 CSV against 2024 weekly
projections would report the gap between two seasons and call it the gap between two sources.
NEITHER is the same artifact, and the first guess at which one matched was BACKWARDS:

    joined player by player, 2026     top 12 r     whole pool r    top-12 scale
    DEF (by team)                       -0.226           0.583     1.081 +- 0.098
    K   (by last name, team)             0.708           0.598     1.284 +- 0.034

K is the closer match: inside the starting band its ordering agrees (0.708) at a scale factor of
1.284 with a standard deviation of 0.034, which is a rescale. DEF is the looser one, and in exactly
the band that matters: the twelve STARTING defenses, where a draft does all its discriminating,
show r = -0.226 -- indistinguishable from zero at se 0.33, and nowhere near the 1.0 two copies of
one artifact would give. Their LEVELS agree (1.081) while their ORDERING does not.

So read every K and DEF number here as a statement about Sleeper's weekly projections and NOT
about the board's input, for both positions rather than just one.

AND THE QUESTION #18 WAS REALLY ASKING has a different answer again. Does a projection predict
ORDERING inside the starting band, measured against seasons that finished (Spearman, se ~ 0.33 at
a twelve-player band)?

    QB 0.52 / 0.74    RB 0.68 / 0.87    WR 0.64 / 0.69
    TE 0.92 / 0.63    K  0.41 / 0.20    DEF 0.75 / 0.48

DEF ranks about as well as QB. K is the weak one, and its 2024 figure is within one se of zero.
#18's premise -- that DEF projections are the unreliable ones -- is not supported.
See evidence/w18_instrument/INSTRUMENT.md.

NOTHING HERE CHOOSES A CONSTANT. It reports ratios. Turning a ratio into a term in the engine is
a separate decision with its own derivation (#56: a bound is not a threshold, and a measurement
is not a tuning knob).

AND THE RATIOS IT REPORTS ARE NOT RATES -- read evidence/w18_instrument/INSTRUMENT.md before using
one. The estimator is a TWO-PLAYER DIFFERENCE, n = 1 pair per position per season, and the first
real run showed that resolution failing at exactly the two positions the work exists to fix: K
because integer kicker totals TIE at the replacement rank (three at 133.0 in 2024, so the ratio
was a coin flip among them), DEF because its projected gap was 6.7 points across eighteen weeks
and any realised spread divided into 5.26. Both failures are now printed beside the number rather
than left for a reader to notice. Neither is repaired by more seasons; each season adds one pair.
The repair is a population estimator over a position's whole pool, which needs the projections
arm captured offline -- see capture_weekly_lines.py.

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

#: A projected season gap at or under this is the projection saying the starters are
#: indistinguishable, so the ratio against it is a division by nearly zero rather than a
#: reliability measurement. DERIVED, not chosen (#56): it is one point per game over a
#: seventeen-game season, the smallest per-game difference this scoring can express at all --
#: below it there is no signal to be a share OF. It gates a WARNING, never a value.
NEGLIGIBLE_PROJECTED_GAP = 17.0


def _totals_from_captures(season: str, scoring: dict, *, log=print,
                          root=None) -> tuple[dict[str, float], dict[str, float]]:
    """The same two dicts as `_season_totals`, from committed captures instead of the API.

    WHY THIS EXISTS. `api.sleeper.app` is denied by the audit sandbox's egress policy, so every
    live run costs a round trip through the owner's machine. Repairing an estimator takes many
    passes over one season, and the first live run showed the estimator needs repairing
    (evidence/w18_instrument/INSTRUMENT.md). A file makes the next fifty passes free.

    IT SHARES accuracy_by_position WITH THE LIVE PATH -- only the fetch differs. An offline
    reimplementation that scored or summed differently would answer a different question while
    looking like a reproduction, which is the one thing this must not do: the first thing it was
    used for was checking that it reproduces the live table row for row.
    """
    import capture_weekly_lines as cwl

    projected: dict[str, float] = {}
    actual: dict[str, float] = {}
    proj_weeks = cwl.load_season(season, "projections", root)
    stat_weeks = cwl.load_season(season, "stats", root)
    for week in REGULAR_SEASON_WEEKS:
        proj = proj_weeks.get(str(week)) or {}
        stats = stat_weeks.get(str(week)) or {}
        if not proj and not stats:
            continue
        log(f"  {season} wk{week:02d}: {len(proj):5d} projected, {len(stats):5d} actual")
        for pid, line in proj.items():
            projected[pid] = projected.get(pid, 0.0) + pu.score_projection(line, scoring)
        for pid, line in stats.items():
            actual[pid] = actual.get(pid, 0.0) + pu.score_projection(line, scoring)
    return projected, actual


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
        # THE CLIENT'S OWN METHOD, not a hand-rolled URL. This read
        # `client._get(f"/stats/nfl/regular/{season}/{week}")` -- season_type in the PATH, which
        # 404s -- while get_weekly_projections three lines up already documented that it belongs
        # in the QUERY STRING. Measured on a networked machine: the path form returns 404/0 rows,
        # the query form 200 and a list of 2074. See SleeperClient._weekly_stat_lines.
        stats = client.get_weekly_stats(season, week) or {}
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
        # THE TWO NUMBERS THAT SAY WHETHER THE RATIO ABOVE MEANS ANYTHING, and their absence is
        # why the first real run was over-read (evidence/w18_instrument/INSTRUMENT.md).
        #
        # This estimator is a TWO-PLAYER DIFFERENCE: n = 1 pair per position per season. At K that
        # resolution is coarser than the effect, because kicker season totals are integers -- a
        # field goal is 3 and an extra point is 1 -- so they TIE. Measured on 2024, three kickers
        # finished at exactly 133.0 at the replacement rank, and which one the projection happened
        # to rank 12th decided the whole ratio. `K 2024 = 0.00` read as "no projected kicker
        # spread materialised"; it was a coin flip among three tied players.
        #
        # The other way it fails is a projected gap so small the ratio is a division by nearly
        # zero: DEF 2024 projected 6.7 points across eighteen weeks, about a third of a point a
        # week, and any realised spread at all divided into 5.26.
        #
        # Neither is repaired by more seasons -- each season adds one more pair. Reporting them
        # does not repair the estimator either; it stops the ratio being read as a rate. The real
        # fix is a population estimator over the whole positional pool, which needs the
        # projections arm offline (capture_weekly_lines.py).
        realised_ties = sum(1 for pid in actual
                            if pu.player_position(players_db.get(pid) or {}) == position
                            and pid in projected
                            and abs(actual[pid] - actual[repl_id]) < 1e-9)
        out[position] = {
            "measurable": True,
            "replacement_rank": rank,
            "pool": len(pool),
            "pairs": 1,
            "projected_gap": projected_gap,
            "realised_gap": realised_gap,
            "realised_ties_at_replacement_rank": realised_ties,
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
    parser.add_argument("--from-captures", action="store_true",
                        help="read committed captures instead of the API (capture_weekly_lines.py). "
                             "No network. Same estimator, same scoring, same ranks.")
    args = parser.parse_args(argv)

    import draft_battery as dbat
    import run_draft_battery as rdb
    import draft_room as dr

    scoring = rdb.scoring_settings_from_capture()
    players_db, _ = rdb.build_players_db_from_capture()
    arm = next(a for a in dbat.league_matrix(scoring) if a["label"] == "12T_ppr_K_DEF")
    starters = dr.starter_slot_counts(arm["league"]["roster_positions"], None, arm["teams"])

    client = None if args.from_captures else sc.SleeperClient()
    seasons = [s.strip() for s in args.seasons.split(",") if s.strip()]
    per_season = {}
    for season in seasons:
        print(f"{'reading' if args.from_captures else 'fetching'} {season} ...")
        try:
            projected, actual = (_totals_from_captures(season, scoring) if args.from_captures
                                 else _season_totals(client, season, scoring))
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
            ties = row["realised_ties_at_replacement_rank"]
            # The caveat travels WITH the number, on the same line, because a table of bare
            # ratios is what got over-read the first time.
            caveat = ""
            if ties > 1:
                caveat = (f"  <- {ties} players tie at the replacement rank; this ratio is a "
                          f"coin flip among them, not a rate")
            elif abs(row["projected_gap"]) < NEGLIGIBLE_PROJECTED_GAP:
                caveat = (f"  <- projected gap is {row['projected_gap']:.1f} over a whole season; "
                          f"the ratio is a division by nearly zero")
            print(f"{position:<5}{season:<9}{row['projected_gap']:>10.1f}"
                  f"{row['realised_gap']:>10.1f}"
                  f"{(f'{share:.2f}' if share is not None else 'n/a'):>9}{caveat}")

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
        "read_from": "committed captures" if args.from_captures else "api.sleeper.app",
        "per_season": per_season,
        "median_realised_share": {p: (round(statistics.median(v), 3) if v else None)
                                  for p, v in shares.items()},
    }
    store_io.write(Path(args.out), report)
    print(f"\n-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
