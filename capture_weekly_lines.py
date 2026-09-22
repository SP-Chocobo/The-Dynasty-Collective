"""Capture a season of Sleeper weekly lines to a file, so a measurement can be re-run offline.

WHY THIS EXISTS AS A COMMITTED SCRIPT. The 2024 actuals in this repo were captured by an
ad-hoc command pasted into a shell on a networked machine. That worked once and is not
reproducible: nothing records which endpoint was read, under what season_type, or on what date,
and the next capture will be a differently-shaped paste. `api.sleeper.app` is denied by the
audit sandbox's egress policy (CONNECT 403, measured -- see measure_projection_accuracy.py), so
every capture has to happen on someone else's machine, which is exactly the situation that wants
one command instead of a paste.

WHY CAPTURE AT ALL, rather than measure live. A two-player-difference estimator turned out to be
the wrong instrument (K's replacement rank sat on a THREE-WAY exact tie at 133.0 realized points,
so its ratio was decided by which tied kicker the projection happened to rank 12th). Fixing an
instrument takes many passes over the same data. Refetching ~72 API calls per pass, on a machine
the author cannot reach, makes that impossible; a file makes it free.

RAW STAT LINES, NOT POINTS -- the same rule outcome_record.py states and for the same reason.
Fantasy points are a function of (stats, a league's scoring settings). Storing points would bake
in one league's rules. player_universe.score_projection converts when a specific league asks.

THINNED AND GZIPPED, LOSSLESSLY for the measurement's purposes. The ad-hoc 2024 capture is 40MB
of which the bulk is a repeated `player` blob -- name, injury notes, news timestamps, channel
ids. `SleeperClient` already drops all of it, so what is stored is the stat line and the player
id and nothing else. Every stat key is kept rather than filtered against a scoring vocabulary,
because `score_projection` sums over whatever keys a league's settings name, and a league this
capture has never seen may name one more. Position is NOT stored: it already lives in players_db,
and a capture-day copy of it would be a second source of truth that goes stale (#126, #26).

    python capture_weekly_lines.py --season 2024 --kind projections
    python capture_weekly_lines.py --season 2023 --kind projections,stats

Runtime is dominated by the API: one call per week per kind, 18 weeks, with a courtesy delay.
"""

from __future__ import annotations

import argparse
import gzip
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import sleeper_client as sc

CAPTURE_DIR = Path("data/fixtures")

#: Matches measure_projection_accuracy: politeness toward a free public API, not a measured
#: rate limit. Sleeper publishes none for the weekly endpoints.
REQUEST_SPACING_SECONDS = 0.4

#: Weeks of a regular season. An absent week is SKIPPED, never stored as an empty dict -- a week
#: that did not download and a week where nobody scored are different facts (#187).
REGULAR_SEASON_WEEKS = range(1, 19)


def capture_path(season: str, kind: str, root: Path | None = None) -> Path:
    return (CAPTURE_DIR if root is None else root) / f"weekly_{kind}_{season}.json.gz"


def thin(lines: dict[str, dict]) -> dict[str, dict]:
    """{player_id: {stat_category: value}} -- the stat line, and deliberately nothing else.

    NO POSITION FIELD, and the first draft of this had one. It read `line["player"]["position"]`
    off Sleeper's embedded player record, which is present in the RAW payload -- the ad-hoc 2024
    capture in this repo is full of them. It is not present in what
    `SleeperClient._weekly_stat_lines` returns: that normaliser reduces every entry to its bare
    stat dict and drops the `player` blob. So `pos` would have been None for every player in every
    week, the file would have round-tripped perfectly, and a measurement reading it would have
    found no position measurable -- a plausible file about nothing. The unit test did not catch it
    because it handed `thin` a raw line rather than the client's output, which is the vacuity the
    engine-measurement checklist warns about in its own words: a fixture error, not a reasoning
    error.

    Removing the field rather than re-fetching the raw payload is also the better answer on the
    merits. `measure_projection_accuracy` already buckets by `pu.player_position(players_db[pid])`,
    so position has a home; a second copy captured on some past day is a stale-metadata source this
    repo has already been bitten by once (#26, years_exp) and a second source of truth (#126).
    """
    out = {}
    for pid, line in (lines or {}).items():
        stats = line.get("stats") if isinstance(line.get("stats"), dict) else line
        out[str(pid)] = stats or {}
    return out


def write(record: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    with gzip.open(path, "wb") as handle:
        handle.write(payload)
    return path


def read(path: Path) -> dict:
    """The counterpart of `write`. A plain .json is accepted too, so the ad-hoc 2024 capture and
    anything this script produces can be read by one call."""
    if str(path).endswith(".gz"):
        with gzip.open(path, "rb") as handle:
            return json.loads(handle.read().decode())
    return json.loads(Path(path).read_text())


def capture_season(client: sc.SleeperClient, season: str, kind: str, *, log=print,
                   spacing: float = REQUEST_SPACING_SECONDS) -> dict:
    """One season of one kind. Raises if NOTHING downloaded, rather than writing an empty file.

    The refusal is outcome_record's, generalised: an empty capture is indistinguishable from a
    season in which nobody scored, and anything measured against it reports the engine as
    catastrophically wrong about a season that never downloaded.
    """
    fetch = (client.get_weekly_stats if kind == "stats" else client.get_weekly_projections)
    weeks: dict[str, dict] = {}
    for week in REGULAR_SEASON_WEEKS:
        lines = fetch(season, week) or {}
        time.sleep(spacing)
        if not lines:
            log(f"  {season} {kind} wk{week:02d}: empty -- skipped")
            continue
        weeks[str(week)] = thin(lines)
        log(f"  {season} {kind} wk{week:02d}: {len(lines):5d} lines")
    if not weeks:
        raise ValueError(
            f"refusing to write an EMPTY capture for {season} {kind}. Nothing downloaded, and a "
            f"file of zeros would be measured as a season in which nobody scored."
        )
    return {
        "_comment": ("Thinned Sleeper weekly lines: {week: {player_id: {stat_category: value}}}. "
                     "RAW STATS, not points -- see capture_weekly_lines.py. No position field: "
                     "bucket by players_db, which is where position already lives."),
        "season": str(season),
        "kind": kind,
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": f"sleeper /{kind}/nfl/{{season}}/{{week}}?season_type=regular",
        "n_weeks": len(weeks),
        "weeks": weeks,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--season", required=True, help="one season, e.g. 2024")
    parser.add_argument("--kind", default="projections",
                        help="projections, stats, or both comma-separated")
    parser.add_argument("--out-dir", default=str(CAPTURE_DIR))
    args = parser.parse_args(argv)

    client = sc.SleeperClient()
    root = Path(args.out_dir)
    written = []
    for kind in [k.strip() for k in args.kind.split(",") if k.strip()]:
        if kind not in ("projections", "stats"):
            print(f"unknown kind {kind!r}; expected projections or stats")
            return 1
        print(f"fetching {args.season} {kind} ...")
        try:
            record = capture_season(client, str(args.season), kind)
        except sc.SleeperAPIError as exc:
            print(f"  could not reach Sleeper: {exc}")
            return 1
        path = write(record, capture_path(str(args.season), kind, root))
        size = path.stat().st_size / 1e6
        print(f"  -> {path}  ({record['n_weeks']} weeks, {size:.1f} MB)")
        written.append(path)

    print("\nCommit these and push; the measurement re-runs from them with no network.")
    for path in written:
        print(f"  git add {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
