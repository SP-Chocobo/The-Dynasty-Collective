"""
Fantasy Football Multi-LLM Command Center — Streamlit UI.

Sleeper Meets Claude: a dark, minimalist dashboard (Claude) accented with
functional sports-data color coding (Sleeper) — emerald for value surplus,
gold for taxi/bench alerts, crimson for injury flags — plus a four-persona
debate studio (Quant/Claude, Beat/Gemini, Contrarian/ChatGPT, Moderator/Claude).
"""

from __future__ import annotations

import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

import llm_engine
from data_merger import PROJECTIONS_DIR, DataMerger, save_alias
from league_prefs import move_league, sorted_leagues, toggle_archive
from sleeper_client import SleeperClient, compute_points_from_stats, find_roster_for_user, league_format_summary

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
    .badge-summary { background: rgba(56,189,248,0.18); color: #7dd3fc; border: 1px solid #0ea5e9; }
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

def league_projections_dir(league_id: str) -> Path:
    """Draft Sharks data is tied to one league's roster/format — never share it across leagues."""
    return PROJECTIONS_DIR / league_id


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


def compact_league_history(league_id: str, max_age_days: int = 30) -> tuple[bool, str]:
    """Distill chat messages older than max_age_days into one memory block, pruning the raw turns.

    Never destructive on failure: the file is only overwritten after
    summarize_history() actually succeeds. A prior summary block (if any) is
    merged forward rather than discarded, so repeated compactions accumulate.
    A timestamped backup of the pre-compaction file is written first, since
    pruning raw history is otherwise unrecoverable.
    """
    history = load_chat_history(league_id)
    cutoff = time.time() - max_age_days * 86400

    prior_summary = next((m["content"] for m in reversed(history) if m.get("role") == "summary"), None)
    old_messages = [m for m in history if m.get("role") != "summary" and m.get("ts", 0) < cutoff]
    recent_messages = [m for m in history if m.get("role") != "summary" and m.get("ts", 0) >= cutoff]

    if not old_messages:
        return False, f"Nothing older than {max_age_days} days to compact."

    new_summary = llm_engine.summarize_history(old_messages, prior_summary=prior_summary)
    if new_summary.startswith("⚠️"):
        return False, f"Compaction aborted, history untouched: {new_summary}"

    backup_path = CHATS_DIR / f"{league_id}_history.pre_compact_{int(time.time())}.json"
    backup_path.write_text(json.dumps(history, indent=2))

    new_history = [{"role": "summary", "content": new_summary, "ts": time.time()}] + recent_messages
    save_chat_history(league_id, new_history)
    return True, f"Compacted {len(old_messages)} messages older than {max_age_days} days into a memory block."


def build_freshness_manifest(snapshot: dict, merger: DataMerger) -> list[tuple[str, Optional[str], Optional[int]]]:
    """(label, as-of date, days old) for every dated source in this context, freshest first."""
    entries = []
    if merger.is_loaded:
        entries.append(("Draft Sharks Dynasty Rankings", merger.freshest_date, merger.staleness_days))
    if merger.is_free_agents_loaded:
        entries.append(("Draft Sharks Free Agent Finder", merger.free_agents_freshest_date, merger.free_agents_staleness_days))
    synced_at = snapshot.get("synced_at")
    if synced_at:
        sync_dt = datetime.fromtimestamp(synced_at)
        entries.append((
            "Sleeper league sync (rosters + native weekly projections)",
            sync_dt.date().isoformat(),
            (datetime.now().date() - sync_dt.date()).days,
        ))
    entries.sort(key=lambda e: (e[2] is None, e[2]))
    return entries


RECENT_TURNS_IN_CONTEXT = 16  # ~3 debate rounds worth of raw messages fed back verbatim


def build_context(snapshot: dict, roster_table: list[dict]) -> str:
    league = snapshot["league"]
    fmt = league_format_summary(league)
    merger: DataMerger = st.session_state.data_merger
    lines = [
        f"League: {fmt['name']} ({fmt['season']}) — {fmt['type']}, {fmt['teams']} teams, "
        f"{'Superflex' if fmt['superflex'] else '1QB'}, {fmt['scoring']}, taxi slots: {fmt['taxi_slots']}",
    ]

    history = st.session_state.get("chat_history", [])
    summary_msgs = [m for m in history if m.get("role") == "summary"]
    recent_msgs = [m for m in history if m.get("role") != "summary"][-RECENT_TURNS_IN_CONTEXT:]
    if summary_msgs or recent_msgs:
        lines.append("\nCONVERSATION MEMORY — prior debates in this league (older-to-newer):")
        if summary_msgs:
            lines.append(f"  [compacted memory of older history]\n{summary_msgs[-1]['content']}")
        for m in recent_msgs:
            lines.append(f"  [{m.get('role', '?')}] {m.get('content', '')}")

    freshness = build_freshness_manifest(snapshot, merger)
    if freshness:
        lines.append(
            "\nDATA FRESHNESS (freshest first). The Beat Tracker's and Contrarian's own live web search "
            "is always fresher than anything below, since it runs at the moment of the question — treat it "
            "as the top entry implicitly. When sources conflict, lean toward the more recently updated one, "
            "but weigh what kind of claim it is: a fresher injury/depth-chart/news signal should outweigh a "
            "staler one fairly decisively, while a fresher season-long dynasty valuation is only a mild edge "
            "over an older one, since long-term value doesn't go stale as fast as situational facts."
        )
        for label, date, age in freshness:
            age_label = f"{age}d old" if age is not None else "date unknown"
            stale_flag = " — STALE" if age is not None and age >= 7 else ""
            lines.append(f"  - {label}: as of {date or 'unknown'} ({age_label}){stale_flag}")

    if snapshot.get("projections"):
        nfl_state = snapshot.get("nfl_state") or {}
        lines.append(
            f"\nSleeper's own native week-{nfl_state.get('week', '?')} stat-category projections are also "
            "included below as 'sleeper_proj', scored under this league's real scoring_settings. NOTE: this "
            "is a SINGLE-WEEK number, not a season or 3-year total like Draft Sharks' — don't compare them "
            "at face value without accounting for that timeframe difference. Treat it as a second independent "
            "quantitative source to weigh against Draft Sharks, not a tiebreaker by default."
        )
    lines.append(
        "Roster (name | pos | team | DS tier | DS VORP | DS 1yr proj | Sleeper native week proj | "
        "DS 3yr proj | DS 3D/trade value | DS pos rank):"
    )
    for row in roster_table:
        lines.append(
            f"  {row['name']} | {row['position']} | {row['team']} | "
            f"{row.get('tier', '-')} | {row.get('vorp', '-')} | {row.get('projection', '-')} | "
            f"{row.get('sleeper_proj', '-')} | {row.get('proj_3yr', '-')} | "
            f"{row.get('trade_value', '-')} | {row.get('pos_rank', '-')}"
        )

    if merger.is_free_agents_loaded:
        top_fa = merger.list_free_agents(exclude_mine=True, top_n=15)
        if top_fa:
            lines.append(
                "\nTop available free agents per Draft Sharks' Free Agent Finder "
                "(name | pos | team | status | 3D Proj | rest-of-season 3D Proj | ceiling | 3D Value+; "
                "'Add' = Draft Sharks' own suggested waiver pickup, blank = ordinary free agent):"
            )
            for fa in top_fa:
                lines.append(
                    f"  {fa.get('name', '-')} | {fa.get('position', '-')} | {fa.get('team', '-')} | "
                    f"{fa.get('roster_status') or '-'} | {fa.get('proj_3d', '-')} | {fa.get('ros_3d', '-')} | "
                    f"{fa.get('ceiling', '-')} | {fa.get('value_3d', '-')}"
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
                # Draft Sharks data (especially Free Agent Finder — it's tied to one
                # league's actual roster) must not leak between leagues, so each
                # league gets its own subdirectory rather than one shared pool.
                st.session_state.data_merger = DataMerger(projections_dir=league_projections_dir(selected))

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
    if not st.session_state.selected_league_id:
        st.caption("Select a league above first — Draft Sharks data (especially Free Agent Finder) is specific to one league's roster, so it's stored per league, not shared across all of them.")
    else:
        st.caption(
            "Draft Sharks has no public export API — save a tool page as a PDF "
            "(Dynasty Rankings, or the Free Agent Finder for roster+waiver data) "
            "and upload it here. The kind is auto-detected, no need to rename it. "
            "This applies only to the currently selected league."
        )
        league_proj_dir = league_projections_dir(st.session_state.selected_league_id)
        uploaded = st.file_uploader("Upload projections PDF/CSV/JSON", type=["pdf", "csv", "json"])
        if uploaded is not None:
            league_proj_dir.mkdir(parents=True, exist_ok=True)
            dest = league_proj_dir / uploaded.name
            dest.write_bytes(uploaded.getbuffer())
            st.session_state.data_merger.reload()
            st.success(f"Saved {uploaded.name} for this league.")

        existing_files = sorted(p.name for p in league_proj_dir.glob("*") if p.suffix in (".csv", ".json", ".pdf")) if league_proj_dir.exists() else []
        if existing_files:
            st.caption("Loaded for this league: " + ", ".join(existing_files))

            other_leagues = [lg for lg in st.session_state.leagues if lg["league_id"] != st.session_state.selected_league_id]
            if other_leagues:
                with st.expander("Copy this league's Draft Sharks files to another league"):
                    st.caption(
                        "Only do this if the target league genuinely shares the same scoring format "
                        "(PPR/standard, superflex, taxi, etc.) — Draft Sharks' rankings and values are "
                        "computed under specific scoring rules, so copying into a differently-scored league "
                        "will give inaccurate numbers there. The Free Agent Finder export is roster-specific "
                        "and almost never correct to copy, even between same-format leagues."
                    )
                    target_options = {lg["league_id"]: lg["name"] for lg in other_leagues}
                    targets = st.multiselect(
                        "Copy to", options=list(target_options.keys()), format_func=lambda lid: target_options[lid],
                    )
                    if st.button("Copy Files") and targets:
                        for target_id in targets:
                            target_dir = league_projections_dir(target_id)
                            target_dir.mkdir(parents=True, exist_ok=True)
                            for f in existing_files:
                                shutil.copy(league_proj_dir / f, target_dir / f)
                        st.success(f"Copied {len(existing_files)} file(s) to {len(targets)} league(s).")

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

    if merger.is_free_agents_loaded:
        fa_age = merger.free_agents_staleness_days
        fa_cls = "status-bad" if merger.free_agents_is_stale else "status-ok"
        fa_icon = "⚠️" if merger.free_agents_is_stale else "✅"
        fa_age_label = f"({fa_age}d ago)" if fa_age is not None else ""
        st.markdown(f'<span class="{fa_cls}">{fa_icon} Free Agent Data Loaded {fa_age_label}</span>', unsafe_allow_html=True)
    else:
        st.markdown(status_line("Free Agent Data Loaded", False), unsafe_allow_html=True)

    st.markdown(status_line("Sleeper Synced", st.session_state.league_snapshot is not None), unsafe_allow_html=True)
    snap = st.session_state.league_snapshot
    has_sleeper_proj = bool(snap and snap.get("projections"))
    proj_week = (snap.get("nfl_state") or {}).get("week") if snap else None
    proj_label = f"Sleeper Native Projections (week {proj_week})" if has_sleeper_proj else "Sleeper Native Projections"
    st.markdown(status_line(proj_label, has_sleeper_proj), unsafe_allow_html=True)
    if snap and not has_sleeper_proj:
        st.caption("Unofficial endpoint returned nothing this sync — Draft Sharks/market data still work fine without it.")
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
        sleeper_projections = snapshot.get("projections") or {}
        scoring_settings = league.get("scoring_settings", {}) or {}
        for row in roster_table:
            pid = row["player_id"]
            row["slot"] = "TAXI" if pid in taxi else ("IR" if pid in reserve else ("Starter" if pid in starters else "Bench"))
            stats = sleeper_projections.get(pid)
            if stats:
                row["sleeper_proj"] = compute_points_from_stats(stats, scoring_settings)

        df = pd.DataFrame(roster_table)
        display_cols = [c for c in [
            "name", "position", "team", "slot", "tier", "vorp",
            "projection", "sleeper_proj", "proj_3yr", "trade_value", "pos_rank",
            "fa_ros_proj", "fa_ceiling", "fa_value", "injury_status",
        ] if c in df.columns]
        st.dataframe(df[display_cols] if not df.empty else df, use_container_width=True, hide_index=True)
        if "sleeper_proj" in df.columns:
            nfl_state = snapshot.get("nfl_state") or {}
            st.caption(
                f"'sleeper_proj' = Sleeper's own week-{nfl_state.get('week', '?')} stat projections, "
                f"scored under this league's actual settings — an unofficial endpoint, cross-check it."
            )

        if merger.is_loaded:
            matched = sum(1 for r in roster_table if r.get("matched"))
            st.caption(f"Draft Sharks match rate: {matched}/{len(roster_table)} players")

            unmatched = [r for r in roster_table if not r.get("matched")]
            if unmatched:
                with st.expander(f"Unmatched Players ({len(unmatched)}) — fix with a manual alias"):
                    st.caption(
                        "These roster players didn't auto-match to your loaded Draft Sharks data. "
                        "Pick one, type the exact name Draft Sharks printed for them, and save — "
                        "this overrides automatic matching for that player from now on."
                    )
                    unmatched_names = [r["name"] for r in unmatched]
                    sel_name = st.selectbox("Unmatched player", options=unmatched_names, key="alias_select")
                    ds_name_input = st.text_input(
                        "Draft Sharks name (as printed, e.g. 'J Chase')", key="alias_ds_name"
                    )
                    if st.button("Save Alias", key="alias_save"):
                        if ds_name_input.strip():
                            save_alias(sel_name, ds_name_input.strip())
                            merger.reload()
                            st.success(f"Mapped '{sel_name}' → '{ds_name_input.strip()}'.")
                            st.rerun()
                        else:
                            st.error("Enter the name as Draft Sharks printed it first.")
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
        "summary": ("🧠 MEMORY SUMMARY", "badge-summary"),
    }
    for msg in reversed(st.session_state.chat_history[-40:]):
        label, cls = badge_map.get(msg["role"], (msg["role"], "badge-user"))
        st.markdown(f'<span class="badge {cls}">{label}</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="agent-block">{msg["content"]}</div>', unsafe_allow_html=True)

    if st.session_state.chat_history:
        hcol1, hcol2, hcol3 = st.columns([1, 1, 1])
        if hcol1.button("Clear Chat History"):
            st.session_state.chat_history = []
            save_chat_history(st.session_state.selected_league_id, [])
            st.rerun()
        compact_days = hcol2.number_input("Compact older than (days)", min_value=1, value=30, step=1, key="compact_days")
        if hcol3.button("🧹 Compact History"):
            with st.spinner(f"Summarizing turns older than {compact_days} days..."):
                ok, message = compact_league_history(st.session_state.selected_league_id, max_age_days=int(compact_days))
            if ok:
                st.session_state.chat_history = load_chat_history(st.session_state.selected_league_id)
                st.success(message)
                st.rerun()
            else:
                st.warning(message)

# ------------------------------------------------------------------ free agents --

st.markdown("---")
st.subheader("Free Agents")

merger = st.session_state.data_merger
if not merger.is_free_agents_loaded:
    st.caption(
        "No Free Agent Finder data loaded — export that page from Draft Sharks as a PDF "
        "and upload it in the sidebar alongside your rankings (auto-detected, no need to rename it)."
    )
else:
    if merger.free_agents_is_stale:
        st.warning(
            f"Free agent data is {merger.free_agents_staleness_days} days old — waiver values shift "
            "week to week more than dynasty rankings do, so this is worth refreshing more often.",
            icon="⚠️",
        )
    fa_positions = sorted(p for p in merger.free_agents["position"].dropna().unique()) if "position" in merger.free_agents.columns else []
    fcol1, fcol2 = st.columns([1, 3])
    fa_position_filter = fcol1.selectbox("Position", options=["All"] + fa_positions)
    show_mine = fcol1.checkbox("Include my own roster", value=False)
    fa_rows = merger.list_free_agents(
        exclude_mine=not show_mine,
        position=None if fa_position_filter == "All" else fa_position_filter,
        top_n=25,
    )
    if fa_rows:
        fa_df = pd.DataFrame(fa_rows)
        fa_df["roster_status"] = fa_df.get("roster_status", pd.Series(dtype=object)).fillna("Available")
        fa_display_cols = [c for c in ["name", "team", "position", "roster_status", "rank", "proj_3d", "ros_3d", "ceiling", "value_3d"] if c in fa_df.columns]
        fcol2.dataframe(fa_df[fa_display_cols], use_container_width=True, hide_index=True)
    else:
        fcol2.caption("No free agents match that filter.")
