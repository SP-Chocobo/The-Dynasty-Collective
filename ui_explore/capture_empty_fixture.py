"""Capture the EMPTY-STATE fixture: what the app can honestly say before any league is synced.

Run from the repo root (DataMerger resolves baseline paths against cwd -- engine-measurement
rule 1). Reads the real manifest through `freshness.py`, which #300 made reachable without
importing the app.

THE SPLIT THIS FILE ENCODES, and it is the whole design decision. The manifest returns four rows
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
from data_merger import DataMerger, recency_grade

OUT = pathlib.Path("ui_explore/empty_fixture.json")


def _split_reason(label: str) -> tuple[str, str]:
    """(source name, why it is absent) out of one manifest label.

    FRAGILE ON PURPOSE, AND SAID SO. `sleeper_client` writes the reason INTO the label, after an
    em dash ("Sleeper player database — never fetched on this machine"), so parsing it back out
    is the only way to show the name and the reason in different places. There is no second
    field to read instead; `build_freshness_manifest` returns (label, as-of, days) and the
    reason lives in the first.

    If the em dash ever goes away this returns the whole label as BOTH halves rather than
    inventing a reason it does not have -- a wrong reason reads as reassurance, which is worse
    than a clumsy one (`#140`'s argument about the staleness number, applied to prose).
    """
    if "\u2014" not in label:
        return label, label
    name, _, reason = label.partition("\u2014")
    return name.strip(), reason.strip() or name.strip()


def main(argv=None):
    out = pathlib.Path((argv or sys.argv[1:])[0]) if (argv or sys.argv[1:]) else OUT
    merger = DataMerger()
    rows = freshness.build_freshness_manifest({}, merger)
    assert rows, "the manifest is empty; it should always carry its two unconditional rows"

    have, on_sync = [], []
    for label, as_of, days in rows:
        if days is None:
            name, reason = _split_reason(label)
            on_sync.append({"label": name, "basis": f"ABSENT -- {reason}"})
        else:
            have.append({"label": label, "as_of": as_of, "days": days,
                         "basis": f"measured -- read off the file on disk, as-of {as_of}"})
    have.sort(key=lambda r: r["days"])

    ages = [r["days"] for r in have]
    worst = max(ages) if ages else None
    fx = {
        "state": "no_league_synced",
        "state_basis": "measured -- DataMerger loaded from disk with an empty snapshot, the "
                       "same call app.py makes above its only st.stop()",
        "grade": recency_grade(worst) if worst is not None else None,
        "grade_basis": (f"measured -- recency_grade over the oldest LOADED source ({worst}d)"
                        if worst is not None
                        else "ABSENT -- no loaded source carries a date, so there is nothing to grade"),
        "worst_days": worst,
        "have": have,
        "on_sync": on_sync,
        "action": "Sync a Sleeper username in the sidebar",
        "action_cost": "Until then the board cannot price to your league's rules: the player "
                       "universe and the league-scored projections both arrive with the sync.",
    }
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
