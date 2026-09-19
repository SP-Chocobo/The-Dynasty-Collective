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


def _record_root(root: Optional[Path]) -> Path:
    """`root`, or the module's own directory resolved AT CALL TIME.

    These took `root: Path = RECORD_DIR`, which binds the directory when the function is
    DEFINED. Reassigning `outcome_record.RECORD_DIR` -- the only way a test can point this
    module at a temp directory -- then changed nothing, so `main --list` could not be exercised
    at all. That is why its crash on a damaged record (`TypeError: 'NoneType' object is not
    subscriptable`, which took down the listing of every healthy week with it) shipped with no
    test: not an oversight in the test suite, an untestable signature (#52 phase 7.5).
    """
    return RECORD_DIR if root is None else root


def record_path(season: str, week: int, root: Optional[Path] = None) -> Path:
    return _record_root(root) / f"outcomes_{season}_wk{int(week):02d}.json"


def capture(stats: dict[str, dict], season: str, week: int, *,
            root: Optional[Path] = None) -> dict:
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
    existing, readable = load_state(season, week, root)
    if not readable:
        # REFUSED, in the same voice as the empty-stats refusal above and for the same reason:
        # the alternative is a silent loss. A damaged record still holds the revision trail in
        # its bytes; capturing over it would write `revisions=[]` and call the result a
        # correction. store_io would now decline the write anyway (load_state armed the mark),
        # so without this the caller would be told nothing at all.
        raise ValueError(
            f"refusing to capture over a DAMAGED outcome record for {season} week {week} "
            f"({path}). It exists and does not parse, so whatever revision history it holds "
            f"cannot be read -- and writing a fresh record here would report a correction "
            f"while destroying the trail of every correction before it. Move or repair the "
            f"file, then capture again."
        )
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


def load_state(season: str, week: int,
               root: Optional[Path] = None) -> tuple[Optional[dict], bool]:
    """(record, readable) -- the three states this week can be in, kept apart.

    ABSENT is (None, True): nobody captured this week, and that is a fact.
    DAMAGED is (None, False): somebody did, and the bytes will not parse.
    PRESENT is (record, True).

    Those first two used to be one answer (#52 phase 7.5 / L-05). `load` did its own
    `json.loads` beside store_io and returned `None` for both, and the cost was not the
    ambiguity itself -- it was that the hand-rolled read NEVER ARMED THE DAMAGE MARK. store_io
    refuses to overwrite a store it has found unparseable, but it can only refuse what it has
    been asked to read, and this module asked nothing. Measured end to end on a truncated
    record holding one real correction: `load` returned None, `capture` therefore read
    `existing=None`, wrote `revisions=[]`, and `store_io.write` -- seeing no mark -- replaced
    the damaged file. The trail went from one revision to zero, under a module whose own
    guarantee is that "a correction is VISIBLE rather than silent".

    Reading through store_io fixes both halves at once, and that is why this is a re-route
    rather than a third state bolted onto the old parser.
    """
    path = record_path(season, week, root)
    if not path.exists():
        return None, True
    record, readable = store_io.read_state(path, None)
    return (record if readable else None), readable


def load(season: str, week: int, root: Optional[Path] = None) -> Optional[dict]:
    """The record, or None for a week that is absent OR damaged.

    Fail-soft on purpose, and unchanged in shape so every reader keeps working. What changed
    is underneath: the read now goes through store_io, so a damaged record arms the mark that
    stops the next write destroying it, and shows up in `store_io.unreadable_stores()` instead
    of being invisible. A caller that must tell the two apart asks `load_state`.
    """
    return load_state(season, week, root)[0]


def weeks(season: Optional[str] = None,
          root: Optional[Path] = None) -> list[tuple[str, int]]:
    """(season, week) pairs on disk, in order."""
    root = _record_root(root)
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
               root: Optional[Path] = None) -> dict[str, float]:
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
            record, readable = load_state(season, week)
            if record is None:
                # Named, not skipped and not crashed. This used to raise
                # `TypeError: 'NoneType' object is not subscriptable` -- a damaged file took
                # the whole listing down, including every healthy week after it.
                print(f"  {season} wk{week:02d}  "
                      + ("DAMAGED -- exists and does not parse; left untouched"
                         if not readable else
                         "listed on disk but could not be read"))
                continue
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
