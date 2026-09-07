"""The live-app baseline probe page. NOT run from this tree: copy the repository to a scratch
directory (tar, excluding .git), seed data/chats/dockprobe_history.json, data/todos/dockprobe.json,
data/pins/dockprobe.json and data/sleeper_snapshots/dockprobe_latest.json from
mockups/dock_transcript.json (see the seeding block in the session record), put this file beside
app.py there, and run `streamlit run dock_probe.py --server.port 8765 --server.headless true`.
Then `node mockups/dock_probe_asis.cjs` measures the app's own dock at 1,400 x 1,400.
It seeds session_state so app.py renders a league (a stub client, no network), then runs app.py
in place. ?level=collapsed|partial|full sets the dock tier; ?n=8 cuts the history after the
Moderator's block-less follow-up."""

import json, runpy
import streamlit as st
from sleeper_client import SleeperClient, SleeperAPIError
from screen_context import ScreenContext

class StubClient(SleeperClient):
    def get_players(self, force_refresh=False): return {}
    def _get(self, *a, **k): raise SleeperAPIError("offline probe")

P = json.load(open("mockups/dock_transcript.json"))  # copied beside the scratch app
if "sleeper_client" not in st.session_state:
    st.session_state.sleeper_client = StubClient()
st.session_state.setdefault("username", "")
st.session_state.setdefault("auto_sync_attempted", True)
st.session_state.setdefault("selected_league_id", "dockprobe")
st.session_state.setdefault("league_snapshot", json.load(open("data/sleeper_snapshots/dockprobe_latest.json")))
n = int(st.query_params.get("n", "0") or 0)
st.session_state.setdefault("chat_history", P["history"][:n] if n else P["history"])
a = P["attached"]
st.session_state.setdefault("debate_attached_context", ScreenContext(surface=a["surface"], looking_at=a["looking_at"], decision=a["decision"], evidence=a["evidence"], entities=tuple(a["entities"])))
st.session_state.setdefault("debate_dock_level", st.query_params.get("level", "partial"))
runpy.run_path("app.py", run_name="__main__")
