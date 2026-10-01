"""The live-app baseline probe page for the panel group. NOT run from this tree: copy the
repository to a scratch directory (tar, excluding .git), run `python3 mockups/panels_data.py
<scratch>` to seed data/decisions, data/todos, data/pins, data/chats, data/baseline and a
snapshot under it, put this file beside app.py there, and run
`streamlit run panels_probe_app.py --server.port 8766 --server.headless true`.
Then `node mockups/panels_probe_asis.cjs` measures the app's own four panels at 1,400 x 1,400.

Seeds session_state so app.py renders a league (a stub client, no network) on the Import Audit
view -- the lightest host, with no roster demands -- and the dock collapsed, so what is measured
is the panel group in normal page flow. Same technique as mockups/dock_probe_app.py."""

import json
import runpy

import streamlit as st

from sleeper_client import SleeperAPIError, SleeperClient


class StubClient(SleeperClient):
    def get_players(self, force_refresh=False):
        return {}

    def _get(self, *a, **k):
        raise SleeperAPIError("offline probe")


LEAGUE = "panelprobe"
if "sleeper_client" not in st.session_state:
    st.session_state.sleeper_client = StubClient()
st.session_state.setdefault("username", "")
st.session_state.setdefault("auto_sync_attempted", True)
st.session_state.setdefault("selected_league_id", LEAGUE)
st.session_state.setdefault("league_snapshot", json.load(open(f"data/sleeper_snapshots/{LEAGUE}_latest.json")))
st.session_state.setdefault("chat_history", json.load(open(f"data/chats/{LEAGUE}_history.json")))
st.session_state.setdefault("debate_dock_level", st.query_params.get("level", "collapsed"))
if "main_view" not in st.session_state and not st.session_state.get("pending_main_view"):
    st.session_state["pending_main_view"] = st.query_params.get("view", "🔌 Import Audit")
runpy.run_path("app.py", run_name="__main__")
