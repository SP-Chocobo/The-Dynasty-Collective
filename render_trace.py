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
import sys
import types
from datetime import date
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

    def record(self, path: str, args, kwargs):
        shown = [_shape(a) for a in args]
        shown += [f"{k}={_shape(v)}" for k, v in sorted(kwargs.items())]
        self.calls.append(f"{path}({', '.join(shown)})")


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

    def __init__(self, recorder: _Recorder, path: str = "st", view: str | None = None):
        object.__setattr__(self, "_recorder", recorder)
        object.__setattr__(self, "_path", path)
        object.__setattr__(self, "_view", view)

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _Stub(self._recorder, f"{self._path}.{name}", self._view)

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
            return list(options)[0] if options else None
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


def _streamlit_module(recorder: _Recorder, view: str | None = None):
    module = types.ModuleType("streamlit")
    stub = _Stub(recorder, "st", view)
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

    league = draft_room.build_mock_league(teams=12, superflex=False, scoring="ppr",
                                          te_premium=False, dynasty=True)
    league = dict(league)
    league.setdefault("league_id", "trace")
    league.setdefault("name", "Trace League")
    state = _SessionState()
    state["league_snapshot"] = {
        "synced_at": 0.0, "league": league, "rosters": [], "users": [],
        "traded_picks": [], "nfl_state": {}, "projection_request": {},
        "projection_attempts": [], "projections": {}, "matchups": [],
    }
    state["selected_league_id"] = "trace"
    return state


#: Every top-level view, by its own label in app.py. Kept as literals rather than imported from
#: app, because importing app is the thing under test -- a view that disappeared should show up
#: as a trace that stops covering it, not as a list that quietly shrank to match.
VIEWS = ("🏈 Matchup", "🔧 Roster Maintenance", "📋 Draft Room", "👥 League")


def capture(seeded: bool = True, view: str | None = None) -> list[str]:
    """Import app.py under the stand-in and return the calls it made, in order."""
    recorder = _Recorder()
    st_module, components, v1 = _streamlit_module(recorder, view)
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

    traces = {view: capture(view=view) for view in VIEWS}
    calls = [f"[{view}] {call}" for view in VIEWS for call in traces[view]]
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
        print(f"wrote {TRACE_PATH} -- {len(calls)} calls across {len(VIEWS)} views")
        for view in VIEWS:
            print(f"  {len(traces[view]):5} {view}")
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
