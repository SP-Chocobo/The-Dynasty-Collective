"""What actually happened, fetched from Sleeper each week -- the other half of the forward test.

prediction_record.py writes down what the engine believed before Week 1. This fetches what
the world did about it. Neither is worth much alone.

WHY NOT AN LLM-FILLED TEMPLATE. The tempting shortcut is a spreadsheet a model fills in each
week. Weekly fantasy stats are precise numbers for hundreds of players, and a language model
will produce them fluently from memory whether or not it knows them. A hallucinated 22.4 where
the truth is 14.1 looks exactly like a real row -- there is no signature to catch it. And this
is GROUND TRUTH: poisoned ground truth does not fail loudly, it returns a confident verdict
about whether the engine works. Sleeper publishes the real numbers, free and structured, so
the transcription step buys nothing and risks everything.

RAW STATS, NOT POINTS. Fantasy points are a function of (stats, a league's scoring settings).
Storing points would bake in one league's rules and make the record useless for any other
format -- and this owner plays several. compute_points_from_stats converts at the moment a
specific league asks. One fetch serves every scoring format, forever.

NOT WRITE-ONCE, UNLIKE A PREDICTION -- and the difference is the point. A prediction that can
change is not a prediction, so prediction_record refuses to overwrite. An OUTCOME legitimately
changes: the NFL issues stat corrections days after a game, and a record that refused them
would be preserving a known-wrong number for the sake of a principle that does not apply here.
So re-capture is allowed, and every superseded version's fingerprint is kept in `revisions`.
The guarantee is not immutability, it is that a correction is VISIBLE rather than silent.

WHAT IS NOT VERIFIED. api.sleeper.app is unreachable from the container this was written in
(HTTP 000; see #88), so the live request path has never executed. The URL shape is mirrored
from get_weekly_projections' own hard-won comment, which records that the stats endpoint takes
season_type in the PATH where projections takes it in the query. The parsing is covered by
tests against mocked responses. The first real run should be checked by eye against a box
score before anything is scored from it -- and that instruction lives here, in the module, not
in a conversation someone will not find.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import store_io

RECORD_DIR = Path("data/outcomes")


def _fingerprint(stats: dict) -> str:
    payload = json.dumps(stats, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def record_path(season: str, week: int, root: Path = RECORD_DIR) -> Path:
    return root / f"outcomes_{season}_wk{int(week):02d}.json"


def capture(stats: dict[str, dict], season: str, week: int, *,
            root: Path = RECORD_DIR) -> dict:
    """Write (or revise) one week's realized stats.

    A re-capture keeps the prior fingerprint in `revisions` rather than replacing it silently,
    so a stat correction leaves a trail. `n_players` moving without a revisions entry would
    mean something rewrote the file outside this function.
    """
    if not stats:
        raise ValueError(
            f"refusing to record an EMPTY outcome for {season} week {week}. An empty record is "
            f"indistinguishable from 'nobody scored', and anything scored against it would "
            f"report the engine as catastrophically wrong about a week that never downloaded."
        )
    path = record_path(season, week, root)
    existing = load(season, week, root)
    revisions = list((existing or {}).get("revisions", []))
    if existing and existing.get("fingerprint") != _fingerprint(stats):
        revisions.append({
            "superseded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "fingerprint": existing.get("fingerprint"),
            "n_players": existing.get("n_players"),
        })
    record = {
        "_comment": (
            "Realized weekly stats from Sleeper. RAW STATS, not points -- points depend on a "
            "league's scoring settings, so compute_points_from_stats converts at read time. "
            "See outcome_record.py. Re-capture is allowed (stat corrections are real); every "
            "superseded version is listed in `revisions`."
        ),
        "season": str(season),
        "week": int(week),
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_players": len(stats),
        "source": "sleeper /stats/nfl",
        "fingerprint": _fingerprint(stats),
        "revisions": revisions,
        "stats": stats,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    store_io.write(path, record)
    return record


def load(season: str, week: int, root: Path = RECORD_DIR) -> Optional[dict]:
    path = record_path(season, week, root)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def weeks(season: Optional[str] = None, root: Path = RECORD_DIR) -> list[tuple[str, int]]:
    """(season, week) pairs on disk, in order."""
    if not root.exists():
        return []
    out = []
    for path in root.glob("outcomes_*_wk*.json"):
        try:
            _, captured_season, week_part = path.stem.split("_", 2)
            out.append((captured_season, int(week_part.replace("wk", ""))))
        except (ValueError, IndexError):
            continue
    if season is not None:
        out = [row for row in out if row[0] == str(season)]
    return sorted(out)


def points_for(season: str, week: int, scoring_settings: dict,
               root: Path = RECORD_DIR) -> dict[str, float]:
    """player_id -> fantasy points under THIS league's scoring, derived at read time.

    The reason the record stores stats: the same captured week answers a 0.5-PPR question and
    a TE-premium question and a superflex question, without refetching or storing three
    numbers that would then be free to disagree with each other.
    """
    from sleeper_client import compute_points_from_stats

    record = load(season, week, root)
    if record is None:
        return {}
    return {pid: compute_points_from_stats(stats, scoring_settings)
            for pid, stats in record.get("stats", {}).items()}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--week", type=int, help="week to fetch; default = the last COMPLETED week")
    parser.add_argument("--season", help="season; default = Sleeper's own current season")
    parser.add_argument("--list", action="store_true", help="show what is already captured")
    args = parser.parse_args(argv)

    if args.list:
        captured = weeks()
        for season, week in captured:
            record = load(season, week)
            revised = f"  ({len(record['revisions'])} revision(s))" if record.get("revisions") else ""
            print(f"  {season} wk{week:02d}  n={record['n_players']:5}  "
                  f"{record['fingerprint']}{revised}")
        if not captured:
            print("  (nothing captured yet)")
        return 0

    from sleeper_client import SleeperClient, SleeperAPIError

    client = SleeperClient()
    season, week = args.season, args.week
    if season is None or week is None:
        state = client.get_nfl_state() or {}
        season = season or state.get("season")
        if week is None:
            # The CURRENT week is still being played. Default to the one before it, because a
            # mid-week capture would record a partial result as though it were final -- and
            # the revision trail would then show a "correction" that was really just the rest
            # of Sunday happening.
            current = state.get("week")
            week = (current - 1) if isinstance(current, int) and current > 1 else None
    if not season or not week:
        print("could not determine season/week from Sleeper; pass --season and --week")
        return 1

    try:
        stats = client.get_weekly_stats(str(season), int(week))
    except SleeperAPIError as exc:
        print(f"could not reach Sleeper: {exc}")
        return 1

    record = capture(stats, str(season), int(week))
    print(f"captured {record['n_players']} players for {record['season']} week {record['week']}")
    print(f"  fingerprint : {record['fingerprint']}")
    if record["revisions"]:
        print(f"  revisions   : {len(record['revisions'])} (a stat correction changed this week)")
    print(f"  -> {record_path(record['season'], record['week'])}")
    print("\nFIRST RUN: check a few of these against a real box score before scoring anything "
          "from them. This request path has never executed against the live API.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
