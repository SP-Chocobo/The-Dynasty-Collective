"""
Fantasy Football Multi-LLM Command Center — Streamlit UI.

Sleeper Meets Claude: a dark, minimalist dashboard (Claude) accented with
functional sports-data color coding (Sleeper) — emerald for value surplus,
gold for taxi/bench alerts, crimson for injury flags — plus a four-persona
debate studio (Quant/Claude, Beat/Gemini, Contrarian/ChatGPT, Moderator/Claude).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import streamlit as st

import llm_engine
from data_merger import PROJECTIONS_DIR, DataMerger
from league_prefs import move_league, sorted_leagues, toggle_archive
from sleeper_client import SleeperClient, find_roster_for_user, league_format_summary

CHATS_DIR = Path("data/chats")
CHATS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTIONS_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Fantasy Football Command Center", layout="wide", page_icon="🏈")

# ------------------------------------------------------------------ styling --

st.markdown(
    """
    <style>
    :root {
        --emerald: #16a34a;
        --gold: #d4a017;
        --crimson: #b91c1c;
        --charcoal: #1e1e1e;
    }
    .stApp { background-color: #16171a; }
    .badge {
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: 0.75rem; font-weight: 600; margin-bottom: 6px; letter-spacing: 0.02em;
    }
    .badge-quant { background: rgba(22,163,74,0.18); color: #4ade80; border: 1px solid #16a34a; }
    .badge-beat { background: rgba(212,160,23,0.18); color: #facc15; border: 1px solid #d4a017; }
    .badge-contrarian { background: rgba(139,92,246,0.18); color: #c4b5fd; border: 1px solid #8b5cf6; }
    .badge-moderator { background: rgba(185,28,28,0.18); color: #f87171; border: 1px solid #b91c1c; }
    .badge-user { background: rgba(148,163,184,0.18); color: #cbd5e1; border: 1px solid #64748b; }
    .agent-block {
        border-radius: 8px; padding: 10px 14px; margin-bottom: 10px;
        background: #202124; border: 1px solid #2f3033; font-family: monospace;
        white-space: pre-wrap;
    }
    .status-ok { color: #4ade80; }
    .status-bad { color: #64748b; }
    table, .stDataFrame { font-family: 'DejaVu Sans Mono', monospace; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ state ---

for key, default in {
    "sleeper_client": SleeperClient(),
    "data_merger": DataMerger(),
    "user_id": None,
    "username": "",
    "leagues": [],
    "selected_league_id": None,
    "league_snapshot": None,
    "chat_history": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def load_chat_history(league_id: str) -> list[dict]:
    path = CHATS_DIR / f"{league_id}_history.json"
    if path.exists():
        return json.loads(path.read_text())
    return []


def save_chat_history(league_id: str, history: list[dict]) -> None:
    path = CHATS_DIR / f"{league_id}_history.json"
    path.write_text(json.dumps(history, indent=2))


def append_message(role: str, content: str) -> None:
    msg = {"role": role, "content": content, "ts": time.time()}
    st.session_state.chat_history.append(msg)
    if st.session_state.selected_league_id:
        save_chat_history(st.session_state.selected_league_id, st.session_state.chat_history)


def build_context(snapshot: dict, roster_table: list[dict]) -> str:
    league = snapshot["league"]
    fmt = league_format_summary(league)
    merger: DataMerger = st.session_state.data_merger
    lines = [
        f"League: {fmt['name']} ({fmt['season']}) — {fmt['type']}, {fmt['teams']} teams, "
        f"{'Superflex' if fmt['superflex'] else '1QB'}, {fmt['scoring']}, taxi slots: {fmt['taxi_slots']}",
    ]
    if merger.is_loaded:
        lines.append(
            f"Draft Sharks data as of {merger.freshest_date} "
            f"({merger.staleness_days} days old{' — STALE, treat with caution' if merger.is_stale else ''})"
        )
    lines.append(
        "Roster (name | pos | team | DS tier | DS VORP | DS 1yr proj | DS 3yr proj | DS 3D/trade value | DS pos rank):"
    )
    for row in roster_table:
        lines.append(
            f"  {row['name']} | {row['position']} | {row['team']} | "
            f"{row.get('tier', '-')} | {row.get('vorp', '-')} | {row.get('projection', '-')} | "
            f"{row.get('proj_3yr', '-')} | {row.get('trade_value', '-')} | {row.get('pos_rank', '-')}"
        )
    return "\n".join(lines)


# ------------------------------------------------------------------ sidebar --

with st.sidebar:
    st.markdown("### 🏈 Sleeper Sync")
    username_input = st.text_input("Sleeper Username", value=st.session_state.username)

    if st.button("Sync Leagues", use_container_width=True):
        client: SleeperClient = st.session_state.sleeper_client
        user = client.get_user(username_input)
        if not user:
            st.error(f"No Sleeper user found for '{username_input}'")
        else:
            st.session_state.username = username_input
            st.session_state.user_id = user["user_id"]
            st.session_state.leagues = client.get_user_leagues(user["user_id"])
            if not st.session_state.leagues:
                st.warning("No leagues found for this user in the current season.")
            else:
                st.success(f"Found {len(st.session_state.leagues)} league(s).")

    if st.session_state.leagues:
        visible_leagues, archived_leagues = sorted_leagues(st.session_state.user_id, st.session_state.leagues)
        league_options = {lg["league_id"]: lg["name"] for lg in visible_leagues}

        if league_options:
            option_ids = list(league_options.keys())
            current = st.session_state.selected_league_id
            if current not in option_ids:
                current = option_ids[0]
            selected = st.selectbox(
                "League",
                options=option_ids,
                format_func=lambda lid: league_options[lid],
                index=option_ids.index(current),
            )
            if selected != st.session_state.selected_league_id:
                st.session_state.selected_league_id = selected
                st.session_state.chat_history = load_chat_history(selected)
                st.session_state.league_snapshot = st.session_state.sleeper_client.load_latest_snapshot(selected)

            if st.button("🔄 Refresh This League", use_container_width=True):
                client = st.session_state.sleeper_client
                players_db = client.get_players()
                st.session_state.league_snapshot = client.sync_league(selected, players_db)
                st.success("League synced.")
        else:
            st.info("All discovered leagues are archived — unarchive one below to select it.")

        with st.expander(f"Manage Leagues ({len(st.session_state.leagues)})"):
            st.caption("Archive leagues you don't want on the front dashboard, or reorder them.")
            for lg in visible_leagues + archived_leagues:
                lid = lg["league_id"]
                is_archived = lid in {a["league_id"] for a in archived_leagues}
                name_col, arch_col, up_col, down_col = st.columns([5, 2, 1, 1])
                name_col.write(("🗄️ " if is_archived else "") + lg["name"])
                if arch_col.button("Unarchive" if is_archived else "Archive", key=f"arch_{lid}"):
                    toggle_archive(st.session_state.user_id, lid)
                    st.rerun()
                if up_col.button("▲", key=f"up_{lid}"):
                    move_league(st.session_state.user_id, st.session_state.leagues, lid, -1)
                    st.rerun()
                if down_col.button("▼", key=f"down_{lid}"):
                    move_league(st.session_state.user_id, st.session_state.leagues, lid, 1)
                    st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Draft Sharks / War Room Data")
    st.caption(
        "Draft Sharks has no public export API — save its rankings page as a PDF "
        "(or drop in a CSV/JSON from another vendor) and upload it here."
    )
    uploaded = st.file_uploader("Upload projections PDF/CSV/JSON", type=["pdf", "csv", "json"])
    if uploaded is not None:
        dest = PROJECTIONS_DIR / uploaded.name
        dest.write_bytes(uploaded.getbuffer())
        st.session_state.data_merger.reload()
        st.success(f"Saved {uploaded.name} to {PROJECTIONS_DIR}/")

    existing_files = sorted(p.name for p in PROJECTIONS_DIR.glob("*") if p.suffix in (".csv", ".json", ".pdf"))
    if existing_files:
        st.caption("Loaded files: " + ", ".join(existing_files))

    st.markdown("---")
    st.markdown("### Status")
    def status_line(label: str, ok: bool) -> str:
        icon = "✅" if ok else "❌"
        cls = "status-ok" if ok else "status-bad"
        return f'<span class="{cls}">{icon} {label}</span>'

    merger: DataMerger = st.session_state.data_merger
    if merger.is_loaded:
        age = merger.staleness_days
        age_label = f"updated {merger.freshest_date} ({age}d ago)" if age is not None else "updated (unknown date)"
        ds_cls = "status-bad" if merger.is_stale else "status-ok"
        ds_icon = "⚠️" if merger.is_stale else "✅"
        st.markdown(f'<span class="{ds_cls}">{ds_icon} DS Projections Loaded — {age_label}</span>', unsafe_allow_html=True)
        if merger.is_stale:
            st.caption(f"Data is {age}+ days old — consider re-exporting from Draft Sharks (weekly is plenty).")
    else:
        st.markdown(status_line("DS Projections Loaded", False), unsafe_allow_html=True)

    st.markdown(status_line("Sleeper Synced", st.session_state.league_snapshot is not None), unsafe_allow_html=True)
    st.markdown(status_line("Claude (Quant/Moderator) Connected", llm_engine.is_claude_configured()), unsafe_allow_html=True)
    st.markdown(status_line("Gemini (Beat Tracker) Connected", llm_engine.is_gemini_configured()), unsafe_allow_html=True)
    st.markdown(status_line("ChatGPT (Contrarian) Connected", llm_engine.is_openai_configured()), unsafe_allow_html=True)

# ------------------------------------------------------------------ main ----

st.title("Fantasy Football Command Center")

snapshot = st.session_state.league_snapshot
if not snapshot:
    st.info("Sync a Sleeper username and select a league in the sidebar to get started.")
    st.stop()

league = snapshot["league"]
fmt = league_format_summary(league)
st.caption(
    f"**{fmt['name']}** · {fmt['type']} · {fmt['teams']}-team · "
    f"{'Superflex' if fmt['superflex'] else '1QB'} · {fmt['scoring']} · Taxi: {fmt['taxi_slots']}"
)

if st.session_state.data_merger.is_stale:
    days = st.session_state.data_merger.staleness_days
    st.warning(
        f"Draft Sharks projections are {days} days old. They don't need refreshing every session — "
        "roughly once a week keeps the Quant analysis current — but it's been a while.",
        icon="⚠️",
    )

roster = find_roster_for_user(snapshot["rosters"], st.session_state.user_id) if st.session_state.user_id else None

col_roster, col_studio = st.columns([1, 1.4])

with col_roster:
    st.subheader("Roster Summary")
    if not roster:
        st.warning("Couldn't find a roster owned by this user in this league.")
        roster_table = []
    else:
        players_db = st.session_state.sleeper_client.get_players()
        merger: DataMerger = st.session_state.data_merger
        all_ids = roster.get("players") or []
        starters = set(roster.get("starters") or [])
        taxi = set(roster.get("taxi") or [])
        reserve = set(roster.get("reserve") or [])

        roster_table = merger.build_roster_table(all_ids, players_db)
        for row in roster_table:
            pid = row["player_id"]
            row["slot"] = "TAXI" if pid in taxi else ("IR" if pid in reserve else ("Starter" if pid in starters else "Bench"))

        df = pd.DataFrame(roster_table)
        display_cols = [c for c in [
            "name", "position", "team", "slot", "tier", "vorp",
            "projection", "proj_3yr", "trade_value", "pos_rank", "injury_status",
        ] if c in df.columns]
        st.dataframe(df[display_cols] if not df.empty else df, use_container_width=True, hide_index=True)

        if merger.is_loaded:
            matched = sum(1 for r in roster_table if r.get("matched"))
            st.caption(f"Draft Sharks match rate: {matched}/{len(roster_table)} players")
        else:
            st.caption("No Draft Sharks/War Room projections loaded yet — upload a CSV in the sidebar.")

with col_studio:
    st.subheader("Multi-Model Debate Studio")
    st.caption("Personas: 🟢 Quant (Claude) · 🟡 Beat Tracker (Gemini) · 🟣 Contrarian (ChatGPT) · 🔴 Moderator (Claude)")

    b1, b2, b3, b4 = st.columns(4)
    quick_debate = b1.button("Run Debate", use_container_width=True)
    quick_claude = b2.button("Ask Claude", use_container_width=True)
    quick_gemini = b3.button("Ask Gemini", use_container_width=True)
    quick_gpt = b4.button("Ask ChatGPT", use_container_width=True)

    question = st.text_input(
        "Ask about a start/sit, trade, or waiver decision "
        "(prefix with /debate, /claude, /gemini, or /gpt to route explicitly)",
        key="question_input",
    )

    def resolve_command(text: str) -> tuple[str, str]:
        for prefix, mode in (("/debate", "debate"), ("/claude", "claude"), ("/gemini", "gemini"), ("/gpt", "gpt")):
            if text.strip().lower().startswith(prefix):
                return mode, text.strip()[len(prefix):].strip()
        return "debate", text.strip()

    trigger_mode = None
    trigger_question = None
    if quick_debate and question:
        trigger_mode, trigger_question = "debate", question
    elif quick_claude and question:
        trigger_mode, trigger_question = "claude", question
    elif quick_gemini and question:
        trigger_mode, trigger_question = "gemini", question
    elif quick_gpt and question:
        trigger_mode, trigger_question = "gpt", question
    elif question and st.session_state.get("_last_submitted") != question:
        mode, cleaned = resolve_command(question)
        trigger_mode, trigger_question = mode, cleaned

    if trigger_mode and trigger_question:
        st.session_state["_last_submitted"] = question
        context = build_context(snapshot, roster_table if roster else [])
        append_message("user", trigger_question)

        with st.spinner("Consulting the front office..."):
            if trigger_mode == "claude":
                append_message("quant", llm_engine.ask_quant(context, trigger_question))
            elif trigger_mode == "gemini":
                append_message("beat", llm_engine.ask_beat(context, trigger_question))
            elif trigger_mode == "gpt":
                beat_reply = ""
                quant_reply = ""
                append_message("contrarian", llm_engine.ask_contrarian(context, trigger_question, quant_reply, beat_reply))
            else:
                result = llm_engine.run_debate(context, trigger_question)
                append_message("quant", result.quant)
                append_message("beat", result.beat)
                append_message("contrarian", result.contrarian)
                append_message("moderator", result.moderator)

    st.markdown("---")
    badge_map = {
        "user": ("You", "badge-user"),
        "quant": ("QUANT ANALYST · Claude", "badge-quant"),
        "beat": ("BEAT TRACKER · Gemini", "badge-beat"),
        "contrarian": ("CONTRARIAN · ChatGPT", "badge-contrarian"),
        "moderator": ("MODERATOR VERDICT · Claude", "badge-moderator"),
    }
    for msg in reversed(st.session_state.chat_history[-40:]):
        label, cls = badge_map.get(msg["role"], (msg["role"], "badge-user"))
        st.markdown(f'<span class="badge {cls}">{label}</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="agent-block">{msg["content"]}</div>', unsafe_allow_html=True)

    if st.session_state.chat_history and st.button("Clear Chat History"):
        st.session_state.chat_history = []
        save_chat_history(st.session_state.selected_league_id, [])
        st.rerun()
