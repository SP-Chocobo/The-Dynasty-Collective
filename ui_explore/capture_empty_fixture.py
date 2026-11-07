"""Capture the EMPTY-STATE fixture: what the app can honestly say before any league is synced.

Run from the repo root (DataMerger resolves baseline paths against cwd -- engine-measurement
rule 1). Reads the real manifest through `freshness.py`, which #300 made reachable without
importing the app.

THE SPLIT NO LONGER LIVES HERE (`#334`). It is `front_page.compose_unsynced`, so `app.py` can
reach the same judgment this fixture is built from -- a fixture generator was the only caller,
which meant production's empty state stayed two lines while a better answer sat in a prototype.
What this file still owns is the MEASURING: run from the repo root, read the real manifest, hand
the rows to the composition. Kept below because it is the reason the split exists. The manifest returns four rows
and two of them are absent, but the two absences do NOT mean the same thing as the two ages:

  * `Draft Sharks *` are ON DISK NOW. An age is a judgement about them -- 76 days is Aging.
  * The two `Sleeper *` rows are absent because nothing has been synced yet. That is the EXPECTED
    state of a machine with no league, not a deficiency, and the reason text says so in
    sleeper_client's own words ("never fetched on this machine").

So the fixture sorts them into `have` and `on_sync` rather than into one list with holes in it.
A page that rendered all four as one table with two dashes would be making the second pair look
like damage. After a sync the same two absences WOULD be damage -- which is why the split lives
here, keyed on the state, and not in the renderer.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path.cwd()))   # run from the repo root, as capture_front_fixture does

import freshness
import front_page
from data_merger import DataMerger

OUT = pathlib.Path("ui_explore/empty_fixture.json")


def main(argv=None):
    out = pathlib.Path((argv or sys.argv[1:])[0]) if (argv or sys.argv[1:]) else OUT
    merger = DataMerger()
    rows = freshness.build_freshness_manifest({}, merger)
    assert rows, "the manifest is empty; it should always carry its two unconditional rows"

    fx = front_page.compose_unsynced(rows)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(fx, indent=2, sort_keys=True) + "\n")
    print(f"wrote {out}")
    print(f"  state      {fx['state']}")
    print(f"  grade      {fx['grade']!r} over worst_days={fx['worst_days']}")
    print(f"  have       {len(have)} dated source(s)")
    for r in have:
        print(f"      {r['days']:>4}d  {r['as_of']}  {r['label']}")
    print(f"  on_sync    {len(on_sync)} row(s) that arrive with a sync")
    for r in on_sync:
        print(f"            {r['label']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
