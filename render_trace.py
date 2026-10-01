"""The before/after instrument for moving UI code out of app.py.

WHY A GREEN SUITE IS NOT ENOUGH HERE. app.py is 6,267 lines of Streamlit script -- mostly
top-level statements that execute in order, reading whatever the statements above them built
(session_state, `merger`, the current league, open column handles). Extracting a section turns
an IMPLICIT dependency (a name in scope) into an EXPLICIT one (a parameter), and Python will not
tell you when that list is wrong: a missed argument becomes a default, a stale value gets
captured, a widget key silently collides. The result runs. It just renders something else.

And the tests cannot catch it, because most of app.py's coverage is SOURCE SCANNING -- assertions
that a string appears in the file. Move the code and those either fail for the wrong reason or,
far worse, keep passing while covering nothing. That already happened once in miniature: a test
sliced `app.py[start:start + 2000]` and silently stopped reaching the row it guarded when the
block above it grew.

So the reference has to be BEHAVIOURAL. This runs app.py against a recording stand-in for
Streamlit and writes down every call it makes, in order, with the shape of its arguments. That
trace is the "before". Extract, re-run, diff. A byte-identical trace is real evidence the
refactor preserved behaviour; a green suite is not.

#151, FIXED, AND THE OTHER OPTION IS STRUCTURALLY IMPOSSIBLE HERE. This trace used to record
long strings as `str[97]` -- a length, which is a VALUE, contradicting the paragraph directly
below. It went stale overnight with a single diff, `str[97]` -> `str[98]`, because the Data
Sources caption reads "(9d ago)" one day and "(10d ago)" the next. No UI changed. That is the
worst failure an instrument can have: it teaches its reader to regenerate without looking, and
a trace regenerated without looking is evidence of nothing.

Of the two options, FREEZING THE CLOCK CANNOT WORK IN THIS PROCESS -- measured, not assumed,
and this is why the first attempt failed rather than carelessness. Both available seams break
identically:

    RuntimeWarning: datetime.datetime size changed, may indicate binary incompatibility.
                    Expected 48 from C header, got 56 from PyObject

Any C extension imported during a capture runs `PyDateTime_IMPORT`, which validates the type's
binary layout. A `datetime` subclass is a different size, so it trips whether the class is
swapped at the source (`datetime.datetime = Frozen`) or hidden behind a `sys.modules` shim --
and app.py's import graph pulls in C extensions on every capture. That is what the earlier
"swapped the class but `now()` still returned real time" was a symptom of. Freezing the clock
here needs either a third-party dependency or an injectable clock seam through app.py and
data_merger's six `datetime.now()` call sites -- the hull pass's territory, not a patch.

So the fix is the other option: long strings record as `str[long]`, with no length. That is what
the paragraph below already promised. The cost is real and worth stating: 147 of 491 calls (30%)
carried a length, and dropping it loses the ability to notice a refactor that swaps two
same-shaped adjacent calls without changing path or order. Position in the sequence still
separates everything else, and "is the copy identical" was never a question this trace answered.
An instrument that emits a false diff every time a day counter ticks is worth less than one that
is slightly less sensitive and never lies.

WHAT IT RECORDS AND WHAT IT DELIBERATELY DOES NOT. Call path, ordering, and argument SHAPES --
`st.columns(3)`, `st.button('Retract', key=...)`. Not the full argument values: a caption
containing a computed number would make the trace churn on every data change and stop being a
refactor instrument. The question it answers is "does the same UI get built in the same order
from the same inputs", not "is the copy identical".

WHAT IT CANNOT SEE, stated so it is not trusted past its reach: anything behind a widget that
returns an interactive value. Every button reads False, every checkbox False, every selectbox
its first option -- so this traces the DEFAULT render path only. Branches behind a click are
invisible to it, and an extraction that breaks one of those will not show up here. Those still
need eyes.
"""

from __future__ import annotations

import argparse
import builtins
import json
import re
import sys
import types
from datetime import date, datetime
from pathlib import Path
from unittest import mock

import store_io

TRACE_PATH = Path("RENDER_TRACE.json")


def _shape(value) -> str:
    """A stable description of one argument. Values are deliberately blurred to keep the trace
    a record of STRUCTURE -- a trace that churned whenever a projection changed would be
    measuring the data, not the refactor."""
    if isinstance(value, str):
        # Short literals are kept: they are usually labels and keys, which ARE the structure.
        # Long ones are almost always computed prose, which is not -- and their LENGTH is prose
        # too, not structure (#151). Recording it made this trace churn on the calendar; see the
        # module docstring for why freezing the clock instead is not available here.
        return f"str:{value}" if len(value) <= 60 else "str[long]"
    if isinstance(value, bool):
        return f"bool:{value}"
    if isinstance(value, (int, float)):
        return type(value).__name__
    if isinstance(value, (list, tuple)):
        return f"{type(value).__name__}[{len(value)}]"
    if isinstance(value, dict):
        return f"dict[{len(value)}]"
    return type(value).__name__


class _Recorder:
    def __init__(self):
        self.calls: list[str] = []

    #: A recorded value that CHANGES WITH THE CALENDAR, not with the code. The freshness grade is
    #: `recency_grade(now - oldest_source_date)`, so as real time passes it crosses Fresh ->
    #: Recent -> Aging -> Stale against a fixed set of committed baseline dates. The recorded
    #: fixture carried the grade verbatim, which means this instrument was scheduled to go red on
    #: a date with no UI change behind it -- and it had already churned once inside an unrelated
    #: commit. An instrument that emits a false diff on a timer trains its readers to regenerate
    #: without looking, which costs more than the check is worth.
    #: THE WHOLE SPAN, not just the grade word. The first version of this blurred
    #: "Data Freshness: Aging" -> "Data Freshness: <grade>" and left `class="status-bad"` and the
    #: ⚠️ icon in place -- both derived from the same grade, so both still turn over on the same
    #: calendar date. A half-blur would have moved the scheduled false diff without removing it.
    #: AND IT ESCAPED A SECOND TIME, in a different surface, which is why this is now a LIST.
    #: `trade_ledger_ui.freshness_pill_html` renders "Values 34d stale" -- a raw day count, so it
    #: turns over EVERY DAY rather than at a grade boundary, and `--check` went red at midnight UTC
    #: with no code behind it. One pattern for one surface was the same half-measure the note above
    #: describes: the rule is that NOTHING wall-clock-derived reaches the recorded trace verbatim,
    #: and a rule needs a list, not a special case. A new calendar-derived string on a new surface
    #: belongs here, and the day it appears is the day this check goes red for no reason.
    _CALENDAR_DEPENDENT = (
        (re.compile(r'<span class="status-\w+">\S+ Data Freshness: \w+</span>'),
         '<span class="status-<grade>">&lt;icon&gt; Data Freshness: &lt;grade&gt;</span>'),
        (re.compile(r'<span class="tl-pill stale">Values \d+d stale</span>'),
         '<span class="tl-pill stale">Values &lt;n&gt;d stale</span>'),
    )

    def record(self, path: str, args, kwargs):
        shown = [_shape(a) for a in args]
        shown += [f"{k}={_shape(v)}" for k, v in sorted(kwargs.items())]
        line = f"{path}({', '.join(shown)})"
        # BLURRED, NOT DROPPED. The call still has to happen, and its shape is still compared --
        # only the grade WORD is replaced, so removing the freshness strip is still a diff while
        # the passage of time is not.
        for pattern, blurred in self._CALENDAR_DEPENDENT:
            line = pattern.sub(blurred, line)
        self.calls.append(line)


class _Selection:
    """What a selectable st.dataframe returns: `.selection.rows` / `.selection.columns`.

    Empty, because the trace covers the DEFAULT render -- nothing clicked. A generic stub
    returned something truthy here and app.py went on to subscript it, which is the same class
    of mistake the instrument exists to catch: a permissive stand-in that lets code run down a
    path the real thing never takes.
    """

    rows: list = []
    columns: list = []

    def __init__(self):
        self.selection = self


class _Stopped(Exception):
    """What st.stop() does: end the script run. Caught at the top of capture()."""


class _SessionState(dict):
    """Attribute AND item access, because app.py uses both spellings interchangeably."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        self.pop(name, None)


class _Stub:
    """One Streamlit-shaped object. Records every call, returns something permissive.

    Return values are chosen so the DEFAULT path renders: no button is pressed, no checkbox is
    ticked, every picker takes its first option. That is the path this instrument covers, and
    the module docstring says so rather than letting a reader assume otherwise.

    The ONE exception is the main navigation, which is steered deliberately -- see `_view`. A
    trace that only ever rendered the default view would cover a quarter of what is being
    extracted while looking like it covered all of it.
    """

    def __init__(self, recorder: _Recorder, path: str = "st", view: str | None = None,
                 choices: dict[str, str] | None = None):
        object.__setattr__(self, "_recorder", recorder)
        object.__setattr__(self, "_path", path)
        object.__setattr__(self, "_view", view)
        #: {widget key: the option to return}. The nav is steered by `view`; this steers any OTHER
        #: widget whose value selects a BRANCH rather than a display detail. Needed because
        #: `radio` returns options[0], and the Draft Room's mode radio lists
        #: "Live Draft (Sleeper)" first -- so the Mock Draft branch had never been traced at all,
        #: in any recording, including the view that ships a TypeError.
        object.__setattr__(self, "_choices", choices or {})

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _Stub(self._recorder, f"{self._path}.{name}", self._view, self._choices)

    def __call__(self, *args, **kwargs):
        self._recorder.record(self._path, args, kwargs)
        leaf = self._path.rsplit(".", 1)[-1]
        if leaf == "stop":
            # st.stop() HALTS the script in real Streamlit -- it raises, and everything below
            # it never runs. A stub that returned instead would trace a code path the app never
            # actually executes, which is worse than tracing nothing: it would look like
            # coverage. Found by app.py running 400 lines past its own no-league guard and
            # crashing on the state that guard exists to prevent reaching.
            raise _Stopped()
        if leaf in ("dataframe", "data_editor"):
            return _Selection()
        if leaf == "segmented_control":
            # The main nav. Steered rather than defaulted, so each view can be traced on its
            # own -- an extraction moves ALL of them, and a single default-view trace would be
            # silent about three quarters of the change.
            options = list(kwargs.get("options") or (args[1] if len(args) > 1 else []))
            if self._view and self._view in options:
                return self._view
            return kwargs.get("default") or (options[0] if options else None)
        if leaf == "columns":
            count = args[0] if args else 1
            count = len(count) if isinstance(count, (list, tuple)) else int(count)
            return [_Stub(self._recorder, f"{self._path}[{i}]") for i in range(count)]
        if leaf == "tabs":
            return [_Stub(self._recorder, f"{self._path}[{i}]") for i in range(len(args[0]))]
        if leaf in ("button", "form_submit_button", "checkbox", "toggle", "download_button"):
            return False
        if leaf in ("selectbox", "radio"):
            options = kwargs.get("options") or (args[1] if len(args) > 1 else None)
            options = list(options) if options else []
            # STEERED BY KEY when asked, defaulted otherwise. A branch-selecting widget left at
            # options[0] silently decides which half of a view is traced, and the untraced half is
            # invisible rather than reported: the Draft Room recorded 117 calls for years while its
            # Mock Draft branch was never entered once.
            wanted = self._choices.get(kwargs.get("key"))
            if wanted is not None and wanted in options:
                return wanted
            return options[0] if options else None
        if leaf == "multiselect":
            return list(kwargs.get("default") or [])
        if leaf in ("text_input", "text_area"):
            return ""
        if leaf == "file_uploader":
            return [] if kwargs.get("accept_multiple_files") else None
        if leaf == "date_input":
            return date(2026, 1, 1)
        if leaf in ("number_input", "slider"):
            return kwargs.get("value", 0)
        if leaf in ("cache_data", "cache_resource"):
            # Used both bare and called -- return a passthrough decorator either way.
            if args and callable(args[0]):
                return args[0]
            return lambda fn: fn
        return _Stub(self._recorder, self._path)

    # Context-manager shape, for `with st.expander(...)`, columns, forms, spinners.
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __bool__(self):
        return True

    def __iter__(self):
        return iter(())


def _streamlit_module(recorder: _Recorder, view: str | None = None,
                      choices: dict[str, str] | None = None):
    module = types.ModuleType("streamlit")
    stub = _Stub(recorder, "st", view, choices)
    module.__getattr__ = lambda name: getattr(stub, name)  # type: ignore[attr-defined]
    module.session_state = _SessionState()
    module.secrets = {}
    components = types.ModuleType("streamlit.components")
    v1 = types.ModuleType("streamlit.components.v1")
    v1.html = _Stub(recorder, "components.v1.html")
    components.v1 = v1
    return module, components, v1


def _seeded_session() -> _SessionState:
    """Session state with a synthetic league already selected.

    WITHOUT THIS the trace is worthless for its actual job. app.py guards on
    `st.session_state.league_snapshot` and calls st.stop() when it is empty, so an unseeded run
    records the 79 calls of the "sync a Sleeper username" screen and never reaches the Draft
    Room, the Trade Calculator, or any of the views this instrument exists to protect. That is
    coverage that looks like coverage -- the exact thing this repository keeps finding.

    The league is synthetic (draft_room.build_mock_league, already used by the test suite) and
    the roster/user lists are minimal but real-shaped. Nothing here needs a network: the point
    is to exercise the RENDER PATH, not to be a realistic league.
    """
    import draft_room
    import run_draft_battery as rdb
    import sleeper_client as sc

    league = draft_room.build_mock_league(teams=12, superflex=False, scoring="ppr",
                                          te_premium=False, dynasty=True)
    league = dict(league)
    league.setdefault("league_id", "trace")
    league.setdefault("name", "Trace League")
    # Built here rather than further down: the roster seed below needs real player ids from it.
    players_db, _ = rdb.build_players_db_from_capture()
    state = _SessionState()

    # THE SECOND HALF OF THE SAME INCOMPLETENESS, AND IT COST MORE THAN THE FIRST.
    #
    # `rosters` and `users` were `[]`, and app.py resolves the viewer's team with
    # `find_roster_for_user(snapshot["rosters"], st.session_state.user_id)` -- which returns None
    # over an empty list, so every view fell to its EMPTY STATE. Measured on the recorded
    # fixture: 620 strings, of which exactly 3 were empty-state guards
    # ("Couldn't find a roster owned by this user in this league.", "No teams found in this
    # league's synced data.", "Nothing rostered here yet.") and ZERO were board, candidate or
    # pick-synthesis strings. The Draft Room's recorded calls were a shared sidebar prefix plus
    # one st.warning. Break the live board and the trace was byte-identical -- an instrument
    # reporting "5 views, 619 calls" while covering the parts of them that render when there is
    # nothing to render.
    #
    # Twelve rosters because the league has twelve; the viewer owns the first. Players come from
    # the same committed capture as the universe above (#126: one home for that fact), taken from
    # the front of the pool so the roster is populated rather than plausible-looking-but-empty.
    owner_ids = [f"trace_user_{i}" for i in range(1, (league.get("total_rosters") or 12) + 1)]
    all_ids = [str(pid) for pid in list(players_db)[:len(owner_ids) * 14]]
    rosters = [
        {"roster_id": i + 1, "owner_id": owner, "league_id": "trace",
         # A real roster carries its players as `players`, its starters as `starters`. Both, or
         # the lineup views read as an empty team on a roster that exists -- a third empty state
         # rather than the coverage this seed is for.
         "players": all_ids[i * 14:(i + 1) * 14],
         "starters": all_ids[i * 14:(i * 14) + 9],
         "settings": {"wins": 1, "losses": 1, "ties": 0, "fpts": 100, "fpts_decimal": 0},
         }
        for i, owner in enumerate(owner_ids)
    ]
    users = [{"user_id": owner, "display_name": f"Trace Manager {i + 1}",
              "metadata": {"team_name": f"Trace Team {i + 1}"}}
             for i, owner in enumerate(owner_ids)]

    state["league_snapshot"] = {
        "synced_at": 0.0, "league": league, "rosters": rosters, "users": users,
        "traded_picks": [], "nfl_state": {}, "projection_request": {},
        "projection_attempts": [], "projections": {}, "matchups": [],
    }
    state["selected_league_id"] = "trace"
    # app.py guards the roster lookup on this being set, so an unset user_id reproduces the empty
    # state exactly as an empty roster list did.
    state["user_id"] = owner_ids[0]

    # THE SEED WAS INCOMPLETE, AND THAT MADE THIS INSTRUMENT NETWORK-DEPENDENT.
    #
    # Seeding `league_snapshot` gets past the sync screen, but app.py builds its player
    # universe from a SECOND source it reaches independently:
    #
    #     players_db = st.session_state.sleeper_client.get_players()
    #
    # Left unseeded, that is a live call. Where Sleeper is reachable it returns thousands of
    # players and the free-agent table renders its sort header; where Sleeper is refused it
    # returns nothing and the view falls to "No Sleeper free agents match that filter". Same
    # commit, two different traces -- so the recorded fixture only ever matched whichever
    # environment happened to record it, and CI (which has network) could not pass against a
    # fixture recorded without one. Every push went unchecked while the check looked present.
    #
    # Worse than the red: the recording was made with an EMPTY pool, so the twelve calls that
    # render the free-agent sort header and its debate chip were not covered at all. This
    # instrument exists to notice UI that moved. It was blind to that view.
    #
    # Seeded from the committed capture, which is the same universe the draft battery certifies
    # against (#126 -- one home for this fact, derived rather than a second hand-built pool).
    # `build_players_db_from_capture` RAISES on a missing capture rather than falling back, so
    # this cannot silently return to being a live call.
    #
    # Only `get_players` is overridden. Everything else on the client stays real, because
    # app.py also reads `cache_dir` off it and a hand-rolled double would have to keep pace
    # with every such use.
    client = sc.SleeperClient()
    client.get_players = lambda: players_db
    # A LIVE NETWORK CALL, inside the render this instrument exists to record. The Live Draft Room
    # calls `draft_client.get_drafts(league_id)` unconditionally (app.py ~5267), so tracing that
    # view reached out to api.sleeper.app -- refused here, which meant the branch fell to
    # "No draft found for this league on Sleeper yet." and the recorded fixture depended on whether
    # the recording environment had network. That is the SAME defect the get_players override above
    # was added to fix, in a second place, and it had the same consequence: the trace described
    # whichever environment happened to record it.
    client.get_drafts = lambda league_id: [{
        "draft_id": "trace_draft", "league_id": "trace", "status": "in_progress",
        "type": "snake", "start_time": 0,
        "settings": {"teams": league.get("total_rosters") or 12, "rounds": 14,
                     "slots_qb": 1, "slots_rb": 2, "slots_wr": 2, "slots_te": 1, "slots_flex": 1},
        "draft_order": {owner: i + 1 for i, owner in enumerate(owner_ids)},
    }]
    state["sleeper_client"] = client

    # PICKS ALREADY FETCHED. Seeded rather than fetched, so the recorded Live pass covers the same
    # board machinery the Mock pass does instead of the empty opening state twice. The view now
    # pulls them itself on load (mandate 1.4) -- this seeding also keeps that pull from firing,
    # since the trace's client is a stand-in and a trace should record a board, not a fetch.
    state["draft_room_picks_by_draft"] = {
        "trace_draft": [{"pick_no": i + 1, "round": (i // len(owner_ids)) + 1,
                         "roster_id": str((i % len(owner_ids)) + 1), "player_id": pid,
                         "draft_slot": (i % len(owner_ids)) + 1}
                        for i, pid in enumerate(all_ids[:11])]
    }
    # WHEN they were pulled (mandate 1.4). A FIXED instant, not datetime.now(): the view renders
    # this stamp onto the board, so a live clock here would put a changing string into the
    # recorded trace and schedule a false diff for every run -- the same hazard the freshness blur
    # above exists for, avoided at the source instead. Seeding it is also what the seeded picks
    # MEAN: picks in the store with no stamp are picks from nowhere, and the board is now entitled
    # to refuse to call itself live without one.
    state["draft_room_picks_fetched_at"] = {"trace_draft": datetime(2026, 1, 1, 12, 0, 0)}

    # A MOCK DRAFT ALREADY IN PROGRESS, because a roster alone does not reach the board.
    #
    # With rosters seeded, Matchup, Roster Maintenance and League all render substantively -- but
    # the Draft Room gained ONE call. Both of its modes need more than a synced league: Live needs
    # fetched picks (which nothing fetches automatically), and Mock needs `mock_draft`, which is
    # only ever set behind `st.form_submit_button`. Every widget stand-in returns falsy, so the
    # form never submits and the view records its configuration form and stops. That is why the
    # trace covered zero board, candidate or pick-synthesis calls while reporting 117 for this
    # view: the calls were real, they were just all upstream of the thing worth protecting.
    #
    # Built through THE APP'S OWN CONSTRUCTORS (`build_mock_league`, `generate_pick_order`) rather
    # than a hand-written dict, so a change to either reaches this fixture instead of leaving it
    # quietly describing a draft the app can no longer produce (#126).
    #
    # Mid-draft, not at 1.01: eleven picks in means the roster has state, the pool has been
    # reduced, and the backstops have something to say. An opening board exercises the same code
    # with every roster-aware term at its identity.
    import draft_strategy
    teams, rounds, my_slot = 12, 14, 1
    mock_league = draft_room.build_mock_league(teams=teams, superflex=False, scoring="ppr",
                                              te_premium=False, dynasty=True)
    mock_order = draft_strategy.generate_pick_order(
        [str(i) for i in range(1, teams + 1)], total_rounds=rounds, draft_type="snake")
    mock_taken = [str(pid) for pid in list(players_db)[:11]]
    state["mock_draft"] = {
        "settings": {"teams": teams, "my_slot": my_slot, "superflex": False,
                     "scoring_key": "ppr", "scoring_label": "Full PPR", "te_premium": False,
                     "dynasty": True, "rounds": rounds, "draft_type": "snake"},
        "league": mock_league,
        "my_roster_id": str(my_slot),
        "pick_order": mock_order,
        "picks": [{"pick_no": i + 1, "round": (i // teams) + 1,
                   "roster_id": str(mock_order[i]), "player_id": pid}
                  for i, pid in enumerate(mock_taken)],
        "owner_names": {str(i): ("You" if i == my_slot else f"Team {i}")
                        for i in range(1, teams + 1)},
    }
    return state


#: Every top-level view, by its own label in app.py. Kept as literals rather than imported from
#: app, because importing app is the thing under test -- a view that disappeared should show up
#: as a trace that stops covering it, not as a list that quietly shrank to match.
VIEWS = ("🏈 Matchup", "🔧 Roster Maintenance", "📋 Draft Room", "👥 League", "🔌 Import Audit")

#: (label, view, steered widgets). One pass per BRANCH worth protecting, not one per view.
#:
#: The Draft Room appears twice because it is two applications behind one radio, and the radio
#: lists "Live Draft (Sleeper)" first -- so every recording ever made traced Live and NONE traced
#: Mock. Measured: entering the Mock branch adds 22 calls that had never appeared in this fixture,
#: among them the board container, the candidate selectbox, and the Debate chip. It also raised
#: `TypeError: simulate_opponent_picks() got an unexpected keyword argument 'weekly_projections'`
#: on the first attempt -- a crash on a shipped path, sitting behind a default this instrument
#: never varied.
#:
#: A view whose branches are selected by a widget needs one pass per branch, or the untraced
#: branch is not reported as uncovered; it is simply absent.
TRACE_PASSES = (
    ("🏈 Matchup", "🏈 Matchup", None),
    ("🔧 Roster Maintenance", "🔧 Roster Maintenance", None),
    ("📋 Draft Room · Live", "📋 Draft Room",
     {"draft_room_mode_radio": "Live Draft (Sleeper)"}),
    ("📋 Draft Room · Mock", "📋 Draft Room", {"draft_room_mode_radio": "🧪 Mock Draft"}),
    ("👥 League", "👥 League", None),
    ("🔌 Import Audit", "🔌 Import Audit", None),
)


def capture(seeded: bool = True, view: str | None = None,
            choices: dict[str, str] | None = None) -> list[str]:
    """Import app.py under the stand-in and return the calls it made, in order."""
    recorder = _Recorder()
    st_module, components, v1 = _streamlit_module(recorder, view, choices)
    if seeded:
        st_module.session_state = _seeded_session()
    injected = {
        "streamlit": st_module,
        "streamlit.components": components,
        "streamlit.components.v1": v1,
    }
    saved = {name: sys.modules.get(name) for name in injected}
    sys.modules.pop("app", None)
    sys.modules.update(injected)
    try:
        __import__("app")
    except _Stopped:
        # A normal, expected end to a render -- the app stopping early because there is nothing
        # to show yet is one of its real states, and the trace up to that point is a real trace.
        recorder.calls.append("<st.stop>")
    finally:
        sys.modules.pop("app", None)
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
    return recorder.calls


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--write", action="store_true", help="record the current trace")
    parser.add_argument("--check", action="store_true", help="diff against the recorded trace")
    args = parser.parse_args(argv)

    traces = {label: capture(view=view, choices=choices)
              for label, view, choices in TRACE_PASSES}
    calls = [f"[{label}] {call}" for label, _, _ in TRACE_PASSES for call in traces[label]]
    if args.write:
        # store_io.write for its atomic replace (#102), the same reason baseline_manifest and
        # assertion_floors use it: an interrupted --write would otherwise leave a truncated
        # trace on disk, and the next CI run would fail against the truncation rather than
        # against a real UI change -- a false alarm indistinguishable from the true one.
        # The READ below is deliberately NOT store_io.read, for those same two modules'
        # reason: --write is how a damaged trace gets repaired, and store_io's
        # do-not-overwrite-damage guard would block the repair command.
        store_io.write(TRACE_PATH, {
            "_comment": (
                "Ordered Streamlit calls made by app.py's default render path -- the before/after "
                "reference for moving UI code out of it. See render_trace.py. Regenerate with "
                "`python3 render_trace.py --write` ONLY when a UI change is intended; a diff here "
                "during a refactor means the refactor changed behaviour."
            ),
            "calls": calls,
        })
        print(f"wrote {TRACE_PATH} -- {len(calls)} calls across "
              f"{len(TRACE_PASSES)} passes")
        for label, _, _ in TRACE_PASSES:
            print(f"  {len(traces[label]):5} {label}")
        return 0

    if not TRACE_PATH.exists():
        print("no recorded trace; run --write first")
        return 1
    before = json.loads(TRACE_PATH.read_text())["calls"]
    if before == calls:
        print(f"render trace unchanged ({len(calls)} calls)")
        return 0
    import difflib
    print(f"render trace CHANGED ({len(before)} -> {len(calls)} calls):\n")
    for line in list(difflib.unified_diff(before, calls, "recorded", "now", lineterm=""))[:60]:
        print(f"  {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
