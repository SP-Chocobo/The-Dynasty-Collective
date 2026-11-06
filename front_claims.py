"""The front page's claim band: WHICH claims fire, with what values, and in WHAT ORDER.

ONE HOME FOR THE JUDGMENT, AND NO HTML IN IT. Every ruling this module carries was previously
spelled only inside `ui_explore/round3/build_front.build()`, interleaved with the f-strings that
draw the page -- so the ladder, the cap, the futurity rule and all four rung conditions were
reachable by exactly one caller: a prototype that emits a static file. `app.py` could not reach
any of it, which left production two options, both bad: re-implement the ranking (a second source
of truth, which `#126` forbids) or text-extract it from a builder (what `test_positional_depth_
coverage` had to do before `#297` lifted `positional_depth` out of `app.py`).

This is that same lift, in the opposite direction. `#297` moved a quantity OUT of the one module
nothing can import; this moves a judgment OUT of the one module only a prototype calls.

WHAT STAYS BEHIND, DELIBERATELY: the prose. A claim here carries the measured values and the
basis flags that qualify them -- never a sentence. Two surfaces say the same thing differently
(a static page writes "1 of your starters sits that week"; Streamlit may not), and a module that
shipped copy would make the page's voice a thing production had to override rather than write.
The rule is the same one `depth_ratings` follows: the engine returns the label, the surface
writes the sentence.

THE PROOF THIS LIFT IS BEHAVIOUR-PRESERVING is byte-identity: rebuilding `front.html` after it
must reproduce the committed file's sha256 exactly. That check only became possible in `#332`,
which found both committed front pages painted in a palette `design_system` had abandoned and
shipped the guard that now holds them. Doing this refactor first would have had no baseline to
stand on -- the baseline was already broken and nothing said so.
"""
import lineup_optimizer as lo

#: The claim ladder, highest cost-to-ignore first, with the reason each rung outranks the next.
#: A FIXED LADDER RATHER THAN A SCORE, because these units are incomparable -- a pick clock in
#: minutes, a bye in trade-value, a thin position in a peer label -- and a computed ranking would
#: imply they had been put on one scale. The reason is written beside each rung so the order can
#: be argued with rather than merely obeyed.
LADDER = [
    ("clock",  "a deadline you can actually miss; everything else keeps until tomorrow"),
    ("hole",   "you cannot field a legal lineup at all, which no amount of value fixes"),
    ("bye",    "a known future week with a measured cost, and planning only works in advance"),
    ("thin",   "a standing weakness with no deadline attached"),
]

#: At most three cards. A capped list is a ranked list; an uncapped one is a feed, which weights
#: every claim equally and therefore makes none of them urgent. The cost is that a genuinely
#: four-problem week hides one, and `more` names what was hidden rather than dropping it.
CAP = 3

#: `clock` is DECLARED AND UNREACHABLE, and that is worth stating rather than discovering.
#: No fixture key supplies it and no rung below produces it, so the band's top rung -- the only
#: one carrying an actual deadline -- has never once fired, and the ordering has only ever been
#: exercised on three of its four rungs. It is a placeholder for draft-clock integration, not a
#: dead branch to delete: when the app knows you are on the clock, that claim outranks everything
#: here and the ladder already says so. `RUNGS_PRODUCED_HERE` pins the gap so it stays a known
#: absence instead of quietly becoming a surprise.
RUNGS_PRODUCED_HERE = ("hole", "bye", "thin")


def byes_ahead(bye_profile, current_week):
    """Reduce a bye profile to the weeks STILL AHEAD, or report that futurity is unknowable.

    THE RUNG'S REASON IS FUTURITY, so a claim that cannot establish futurity must not borrow the
    urgency. With a known current week this re-picks the worst week from those at or after it;
    with none, the same numbers are a season-shape fact and the caller says that instead of
    implying a deadline. The first version of the page had no concept of now and would happily
    have put a week already played second on the band -- the one thing a triage surface must
    never do, because it spends the reader's trust in every other claim on it.

    Returns the profile with `_ahead_only` set when a week was known. `worst_week` is None when
    every bye is behind us, which is a real answer and not a missing one.
    """
    bp = dict(bye_profile or {})
    if current_week is None:
        return bp
    weeks = bp.get("weeks") or {}
    ahead = {w: v for w, v in weeks.items()
             if str(w).lstrip("-").isdigit() and int(w) >= int(current_week)}
    if not ahead:
        return {**bp, "worst_week": None, "_ahead_only": True}
    worst = max(ahead, key=lambda w: ahead[w])
    return {**bp, "worst_week": int(worst), "worst_week_loss": ahead[worst],
            "weeks": ahead, "_ahead_only": True}


def thin_sort_key(entry):
    """Within the rung, rank by how close the room is to empty -- not by the alphabet.

    The capture emits positions in sorted() order, so without this the order was Q-before-T,
    which in one real league hid a ONE-quarterback room (an injury away from the rung above)
    below the cap while a two-man TE room held a card.

    COERCED, because a sort key is not a place to trust the fixture's types. Comparing `count`
    directly raised TypeError the moment one entry carried a string and another an int -- a crash
    introduced BY the fix for the alphabetical-ordering defect, and found only by re-running the
    adversarial fixtures against it.
    """
    try:
        n = int(entry.get("count") or 0)
    except (TypeError, ValueError):
        n = 0
    return (n, str(entry.get("position") or ""))


def compose(fx):
    """The claim band for one roster: `{"shown", "hidden", "bye_profile"}`.

    EVERY top-level read is tolerant. The fixture is hand-maintainable and the builder's own
    docstring invites editing it, so a missing key must not be a traceback: a page that fails to
    build is strictly worse than one that renders an honest absence.

    `bye_profile` comes back RESOLVED whether or not the bye claim fired, because the page's week
    strip draws the same reduced profile and must not re-derive it -- re-deriving is how one
    quantity acquires two answers.
    """
    claims = []

    # ONE CARD FOR ALL THE HOLES, not one per position. Two cards reading "No K on the roster"
    # and "No DEF on the roster" is two sentences for one problem with one remedy and one route,
    # and in the fixture's own league they ate two of the three slots and pushed the bye claim --
    # the best signal on this page -- to last while both thin positions fell off entirely. The
    # standing constraint on this project is "clean who, why, and other valid options, at what
    # cost... I dont need all the variables", and a band that spends itself enumerating one
    # problem is the failure that constraint names.
    holes = list(fx.get("structural_holes") or [])
    if holes:
        claims.append({"kind": "hole", "route": "Roster Maintenance", "positions": holes})

    bp = byes_ahead(fx.get("bye_profile") or {}, fx.get("current_week"))
    if bp.get("worst_week") is not None and bp.get("worst_week_loss") is not None:
        # A FLOOR IS NOT A TOTAL. `bye_collision` is explicit that under a partial basis EVERY
        # week's number is a floor, not only the weeks that happen to show a collision -- so the
        # flag belongs on the figure, and the surface puts the marker on the number itself.
        claims.append({
            "kind": "bye", "route": "Matchup",
            "worst_week": bp["worst_week"], "worst_week_loss": bp["worst_week_loss"],
            # concentration is None, NEVER 0.0 -- `bye_concentration` says so, because a roster
            # with nothing to lose has no shape and 0.0 would rank it as maximally staggered.
            "concentration": bp.get("concentration"),
            "partial": bp.get("basis") != lo.BYE_MEASURED,
            "unknown_byes": bp.get("unknown_byes"),
            "starters_out": (bp.get("worst_week_detail") or {}).get("starters_out"),
            "ahead_only": bool(bp.get("_ahead_only")),
        })

    for t in sorted(fx.get("thin_positions") or [], key=thin_sort_key):
        covered, count = t.get("valued_count"), t.get("count") or 0
        claims.append({
            "kind": "thin", "route": "League",
            "position": t.get("position"), "count": count, "valued_count": covered,
            # The comparison is a floor whenever some of the room could not be priced.
            "priced_floor": not (covered is None or covered >= count),
        })

    rank = {k: i for i, (k, _) in enumerate(LADDER)}
    # Stable sort, so the within-rung order `thin_sort_key` established survives the ranking.
    claims.sort(key=lambda c: rank[c["kind"]])
    return {"shown": claims[:CAP], "hidden": claims[CAP:], "bye_profile": bp}
