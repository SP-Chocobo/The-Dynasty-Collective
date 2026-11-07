"""The front page's UNSYNCED state: what the app can honestly say before any league is synced.

ONE HOME FOR THE SPLIT, AND NO STREAMLIT IN IT. The ruling this module carries -- that a
freshness manifest's absent rows mean two different things depending on whether a league has been
synced -- was spelled only inside `ui_explore/capture_empty_fixture.py`, a script whose job is to
write a JSON file for a prototype. `app.py` could not reach it, so production's empty state
stayed two lines of `st.title` and `st.info` while a far better answer sat in a fixture generator.

This is the third lift in the same family and the pattern is now explicit:

    `#297`  positional_depth   OUT of `app.py`, the one module nothing can import
    `#333`  the claim band     OUT of a prototype's HTML emitter
    `#334`  this split         OUT of a prototype's fixture generator

NO STREAMLIT IMPORT HERE, deliberately. `app.py` writes the sentences; this returns the values
and the basis flags that qualify them. That is `#333`'s ruling applied again, and it has a second
payoff here: a module that imported Streamlit could not be called by the capture script, so the
fixture and production would drift into two compositions of the same thing -- the exact `#126`
defect all three of these lifts exist to close.

THE SPLIT ITSELF, which is the whole design decision. The manifest returns four rows and two of
them are absent, but the two absences do NOT mean the same thing as the two ages:

  * `Draft Sharks *` are ON DISK NOW. An age is a judgement about them -- 76 days is Aging.
  * The two `Sleeper *` rows are absent because nothing has been synced yet. That is the EXPECTED
    state of a machine with no league, not a deficiency.

So they sort into `have` and `on_sync` rather than into one list with holes in it. A page that
rendered all four as one table with two dashes would make the second pair look like damage.
After a sync the same two absences WOULD be damage -- which is why the split is keyed on the
state and lives here, not in a renderer.
"""
from data_merger import recency_grade

#: `sleeper_client` writes the reason INTO the label, after an em dash.
_EM_DASH = "—"

STATE_UNSYNCED = "no_league_synced"


def split_reason(label):
    """(source name, why it is absent) out of one manifest label.

    FRAGILE ON PURPOSE, AND SAID SO. `sleeper_client` writes the reason into the label after an
    em dash ("Sleeper player database - never fetched on this machine"), so parsing it back out
    is the only way to show the name and the reason in different places. There is no second field
    to read instead: `build_freshness_manifest` returns (label, as-of, days) and the reason lives
    in the first.

    If the em dash ever goes away this returns the whole label as BOTH halves rather than
    inventing a reason it does not have -- a wrong reason reads as reassurance, which is worse
    than a clumsy one (`#140`'s argument about the staleness number, applied to prose).
    """
    if _EM_DASH not in label:
        return label, label
    name, _, reason = label.partition(_EM_DASH)
    return name.strip(), reason.strip() or name.strip()


def reason_of(stamp):
    """The half of a basis stamp a reader should see, with the engineering token stripped.

    ONE HOME, because `app.py` now renders these stamps too. This was `build_front.reason_of`,
    reachable only by the prototypes; a second spelling of the parse rule in `app.py`
    (`split("ABSENT -- ")`) would have been `#126` in miniature, and the kind that rots quietly
    because both copies look obviously correct. `build_front` imports it from here now, and
    `front.html` rebuilds byte-identical, which is how that move was checked rather than assumed.
    """
    body = (stamp or "").split("--", 1)
    return (body[1] if len(body) > 1 else body[0]).strip() or "No reason recorded."


def compose_unsynced(rows):
    """The unsynced front page, from `freshness.build_freshness_manifest`'s own rows.

    A PURE FUNCTION OF THE ROWS, not of the clock or the disk. The caller does the measuring --
    `build_freshness_manifest({}, merger)` -- and this does the judging. That split is what makes
    the composition testable at all: the ages it sorts on move every day, so a function that read
    the disk itself could only ever be checked against whatever today happens to be, and a test
    written against today's numbers is stale tomorrow by construction (`#305`'s defect exactly).
    """
    have, on_sync = [], []
    for label, as_of, days in rows:
        if days is None:
            name, reason = split_reason(label)
            on_sync.append({"label": name, "basis": f"ABSENT -- {reason}"})
        else:
            have.append({"label": label, "as_of": as_of, "days": days,
                         "basis": f"measured -- read off the file on disk, as-of {as_of}"})
    have.sort(key=lambda r: r["days"])

    ages = [r["days"] for r in have]
    worst = max(ages) if ages else None
    return {
        "state": STATE_UNSYNCED,
        "state_basis": "measured -- DataMerger loaded from disk with an empty snapshot, the "
                       "same call app.py makes above its only st.stop()",
        # recency_grade is design_system's neighbour in spirit: ONE home for the grading bands,
        # so the front page cannot become a second opinion about what "Aging" means.
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
