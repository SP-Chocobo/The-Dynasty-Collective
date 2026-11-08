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

#: THE CHECKS THIS MODULE ACTUALLY RUNS, each as (name, the fixture key it reads, the rung it
#: can raise). In ladder order. ONE HOME (`#126`): the names, the count and the order all come
#: from here, so no surface may number them itself.
#:
#: `VOICE.md` rule 5 -- "name the checks, not the conclusion" -- is the reason this exists, and
#: writing it down immediately corrected the spec that asked for it. That file says "Five checks,
#: all clean -- starters, holes, depth, byes, record"; two independent designers drew "Four
#: checks"; and nothing computed either number (`#338`). THE HONEST NUMBER IS THREE, because
#: three is what this function evaluates. `starters` and `record` are NOT checked here: readiness
#: and standings never reach `compose`, and `#341`/the dashboard ruling puts record off the front
#: page entirely as true-but-inert. A page claiming five checks would have been overclaiming by
#: two, in the very sentence meant to make it auditable.
CHECKS = (
    ("holes", "structural_holes", "hole"),
    ("byes",  "bye_profile",      "bye"),
    ("depth", "thin_positions",   "thin"),
)

#: A check has THREE states and collapsing any two of them is the defect this guards against.
#: `clean` ran and found nothing; `fired` ran and raised a claim; `absent` never ran, and carries
#: why. "Ran and found nothing" and "was never measured" are the distinction `#187` exists to
#: protect, applied to a CHECK rather than to a figure -- and a page that reports an unmeasured
#: check as clean is telling the reader their roster was examined when it was not.
CHECK_CLEAN, CHECK_FIRED, CHECK_ABSENT = "clean", "fired", "absent"


def checks_run(fx, claims):
    """`[{"name", "state", "reason"}]` -- what was examined, in ladder order.

    DERIVED FROM WHAT `compose` ALREADY READ, never re-evaluated. The state comes from the same
    `fx` key the rung reads plus the claims already built, so a check cannot report clean while
    its rung fired, and nothing here computes a second opinion (`#126`, `#338`).

    ABSENCE IS DECIDED BY THE REPO'S OWN GRAMMAR, not by a new convention. `#187`: a value that
    was not measured is `None`, never an empty default. So `[]` is a measured empty result --
    holes were counted, there were none -- while a missing key or `None` never ran. A caller that
    hands `[]` for something it did not measure has broken the absence contract at the producer,
    and that is its defect to fix, not this function's to guess around.

    `bye_profile` is the one that is not a list: `{}` carries no weeks and no basis, so it is
    treated as absent rather than as a measured empty profile. `bye_collision` stamps a real
    profile with its `basis`, which is the evidence that it ran.
    """
    fired_kinds = {c.get("kind") for c in (claims or ())}
    out = []
    for name, key, rung in CHECKS:
        value = (fx or {}).get(key)
        if value is None or (key == "bye_profile" and not value):
            out.append({"name": name, "state": CHECK_ABSENT,
                        "reason": f"no {key} in the data this page was built from"})
        elif rung in fired_kinds:
            out.append({"name": name, "state": CHECK_FIRED, "reason": None})
        else:
            out.append({"name": name, "state": CHECK_CLEAN, "reason": None})
    return out


def checks_summary(checks):
    """The counts and names a surface needs, so the SURFACE never derives them (`#338`).

    `#336b` is the precedent that makes this a function rather than a note: when `compose`
    dropped a quantity, the renderer invented a replacement. A page that had to count its own
    checks would be one `len()` away from the same failure -- and the number it would most want
    is `ran`, which is NOT `len(CHECKS)` whenever anything is absent.
    """
    checks = list(checks or ())
    by = lambda st: [c["name"] for c in checks if c["state"] == st]
    clean, fired, absent = by(CHECK_CLEAN), by(CHECK_FIRED), by(CHECK_ABSENT)
    return {
        "ran": len(clean) + len(fired), "clean": clean, "fired": fired, "absent": absent,
        # TRUE ONLY IF SOMETHING RAN. With every check absent, `not fired` is vacuously true and
        # "all clean" would be the most dishonest sentence this page could print.
        "all_clean": bool(clean) and not fired and not absent,
    }


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
        # `#346` DEFECT 2: this cleared `worst_week` and left `worst_week_loss` and
        # `worst_week_detail` behind, so the reduced profile carried a LOSS FOR A WEEK IT HAD
        # JUST SAID DOES NOT EXIST -- `worst_week: None` beside `worst_week_loss: 68.0`.
        # `compose` happens to guard on both keys, so no claim was built from it; but `compose`
        # RETURNS this profile as `band["bye_profile"]` and surfaces read it directly, which is
        # where the orphaned figure was reachable. A quantity whose subject has been removed is
        # not a smaller truth, it is a number with nothing to be about.
        #
        # `weeks` is deliberately NOT emptied here, and the asymmetry is the point: with weeks
        # ahead, `weeks` is reduced to them; with none ahead, the caller still needs the season
        # shape to be able to say "all seven are behind week 15" instead of showing an empty
        # ledger. So `_ahead_only` means "a current week was known and applied", not "weeks has
        # been filtered". Stated because the two branches genuinely differ and a reader is owed
        # the reason rather than left to infer one.
        return {**bp, "worst_week": None, "worst_week_loss": None,
                "worst_week_detail": None, "_ahead_only": True}
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
            # THE LABEL IS THE QUANTITY (`#336b`). `depth_ratings.depth_label` returns exactly
            # Strong / Average / Weak / None, a RATIO BAND against the league mean -- and nothing
            # in the tree ranks teams within a position. Dropping it here is what left the
            # renderer with nothing true to say, so it invented "bottom of this league at the
            # position": a rank the engine never computes, and false on this very roster, where
            # DEF is a five-way tie at count 1 AND the joint-highest PRICED DEF room in the
            # league. A composition that discards the measured quantity invites the surface to
            # fabricate a replacement.
            "label": t.get("label"),
            # The comparison is a floor whenever some of the room could not be priced.
            "priced_floor": not (covered is None or covered >= count),
        })

    rank = {k: i for i, (k, _) in enumerate(LADDER)}
    # Stable sort, so the within-rung order `thin_sort_key` established survives the ranking.
    claims.sort(key=lambda c: rank[c["kind"]])
    return {"shown": claims[:CAP], "hidden": claims[CAP:], "bye_profile": bp,
            # WHAT WAS EXAMINED, not only what was found (`#338`). Most weeks the band
            # is empty and this is the ENTIRE content of the page, so it is the quiet
            # state's only claim to having looked at anything.
            "checks": checks_run(fx, claims)}
