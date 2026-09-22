"""#18: prove the capture path works by replaying the REAL payload through it. No network.

Run from the repo root.

WHY A REPLAY RATHER THAN A UNIT TEST. The unit tests around `capture_weekly_lines` hand `thin`
synthetic lines, and the first draft of that function passed all of them while being broken: it
stored a position read off Sleeper's embedded `player` blob, which `SleeperClient` strips before a
caller ever sees it, so the field would have been None for every player in every week. The file
would have round-tripped perfectly and measured nothing. A fixture error, not a reasoning error --
which is the failure mode the engine-measurement checklist says to fear.

What closes that hole is feeding the capture path the bytes a live call actually produces. The
committed 2024 actuals are those bytes, so this stubs `_get` with them and runs the whole path:
client normalisation, thinning, gzip write, read back, score, and join to players_db for position.
If the capture were unjoinable or unscoreable this prints it.

It is not in the test suite because it loads a 40MB file and builds the player universe; the suite
is already 800 seconds.
"""

from __future__ import annotations

import collections
import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path.cwd()))

import capture_weekly_lines as cwl
import player_universe as pu
import run_draft_battery as rdb
import sleeper_client as sc

ACTUALS = Path("sleeper_weekly_2024.json")


def main() -> int:
    raw = json.loads(ACTUALS.read_text())
    client = sc.SleeperClient(cache_dir=tempfile.mkdtemp())
    # The stub answers on the URL the client builds, so the week is parsed back out of the path
    # rather than passed in -- if the URL shape ever changes this stops answering instead of
    # quietly returning week 1 forever.
    client._get = mock.Mock(
        side_effect=lambda path, **kw: raw.get(path.split("/")[4].split("?")[0], []))

    record = cwl.capture_season(client, "2024", "stats", log=lambda *a: None, spacing=0.0)
    root = Path(tempfile.mkdtemp())
    path = cwl.write(record, cwl.capture_path("2024", "stats", root))
    back = cwl.read(path)
    print(f"weeks captured : {back['n_weeks']}")
    print(f"raw            : {ACTUALS.stat().st_size / 1e6:.1f} MB")
    print(f"captured       : {path.stat().st_size / 1e6:.2f} MB")

    scoring = rdb.scoring_settings_from_capture()
    players_db, _ = rdb.build_players_db_from_capture()
    totals: dict[str, float] = collections.defaultdict(float)
    for _week, lines in back["weeks"].items():
        for pid, stats in lines.items():
            totals[pid] += pu.score_projection(stats, scoring)

    by_position = collections.Counter(
        pu.player_position(players_db.get(pid) or {}) for pid in totals)
    print("\npositions joined from players_db (None = OL, coaches, non-fantasy):")
    for position, count in by_position.most_common():
        print(f"  {str(position):<6}{count:>6}")

    # BY EYE, which is the instruction outcome_record's CLI gives its first runner and the only
    # check that catches a capture that is internally consistent and wrong.
    print("\ntop three, to be checked against a real 2024 leaderboard:")
    for position in ("K", "DEF", "QB"):
        top = sorted(((v, pid) for pid, v in totals.items()
                      if pu.player_position(players_db.get(pid) or {}) == position),
                     reverse=True)[:3]
        named = [f"{pu.player_name(players_db.get(pid) or {}, pid)} {v:.0f}" for v, pid in top]
        print(f"  {position:<5}{', '.join(named)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
