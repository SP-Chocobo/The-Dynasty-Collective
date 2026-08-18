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

import decision_log
import llm_engine
from attachments import ATTACHMENTS_DIR, list_attachments, save_attachment, set_caption, set_scope, delete_attachment
from data_merger import GLOBAL_PROJECTIONS_DIR, PROJECTIONS_DIR, DataMerger, load_projection_file, save_alias
from league_format import FORMAT_GUIDANCE, FORMAT_OPTIONS, STANDARD, get_format_override, set_format_override
from league_prefs import forget_league, get_prefs, move_league, sorted_leagues, toggle_archive
from sleeper_client import SleeperAPIError, SleeperClient, compute_points_from_stats, find_roster_for_user, league_format_summary

CHATS_DIR = Path("data/chats")
CHATS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTIONS_DIR.mkdir(parents=True, exist_ok=True)
GLOBAL_PROJECTIONS_DIR.mkdir(parents=True, exist_ok=True)
ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

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
    .badge-notice { background: rgba(245,158,11,0.18); color: #fbbf24; border: 1px solid #f59e0b; }
    .agent-block {
        border-radius: 8px; padding: 10px 14px; margin-bottom: 10px;
        background: #202124; border: 1px solid #2f3033; font-family: monospace;
        white-space: pre-wrap;
    }
    .status-ok { color: #4ade80; }
    .status-bad { color: #64748b; }
    table, .stDataFrame { font-family: 'DejaVu Sans Mono', monospace; }

    /* Sidebar defaults to a width that crowds the Manage Leagues row and the
       credentials paste box — widen it out of the box instead of making everyone
       drag it wider by hand every time. Still resizable from here if you want more. */
    [data-testid="stSidebar"] { min-width: 400px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ state ---

def league_projections_dir(league_id: str) -> Path:
    """Draft Sharks data is tied to one league's roster/format — never share it across leagues."""
    return PROJECTIONS_DIR / league_id


LAST_SESSION_PATH = Path("data/last_session.json")


def load_last_username() -> str:
    """Sleeper needs no password, just a username, so remembering the last one used lets a
    page refresh restore the session automatically instead of losing it — Streamlit's own
    session_state resets on every browser reload, it isn't persisted to disk on its own."""
    if LAST_SESSION_PATH.exists():
        try:
            return json.loads(LAST_SESSION_PATH.read_text()).get("username", "")
        except (json.JSONDecodeError, OSError):
            return ""
    return ""


def save_last_username(username: str) -> None:
    LAST_SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAST_SESSION_PATH.write_text(json.dumps({"username": username}))


ENV_PATH = Path(".env")
ENV_VAR_FOR_OVERRIDE = {
    "anthropic_api_key_override": "ANTHROPIC_API_KEY",
    "gemini_api_key_override": "GEMINI_API_KEY",
    "openai_api_key_override": "OPENAI_API_KEY",
}


def save_parsed_keys_to_env(overrides: dict[str, str]) -> None:
    """Persist keys applied from the Connect Your Accounts box into .env, so a local
    `streamlit run app.py` picks them up automatically next time without re-pasting.
    Only rewrites the specific KEY= lines involved — every other line is left untouched.
    This app is meant to run locally (see README), where .env is private to you; it's not
    used for the (unsupported) case of a shared public deployment.
    """
    updates = {ENV_VAR_FOR_OVERRIDE[k]: v for k, v in overrides.items() if k in ENV_VAR_FOR_OVERRIDE}
    if not updates:
        return
    lines = ENV_PATH.read_text().splitlines() if ENV_PATH.exists() else []
    seen: set[str] = set()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        key = stripped.split("=", 1)[0].strip() if "=" in stripped and not stripped.startswith("#") else None
        if key in updates:
            new_lines.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            new_lines.append(line)
    for key, value in updates.items():
        if key not in seen:
            new_lines.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(new_lines) + "\n")


for key, default in {
    "sleeper_client": SleeperClient(),
    "data_merger": DataMerger(),
    "user_id": None,
    "username": load_last_username(),
    "auto_sync_attempted": False,  # only try to restore a remembered session once per browser session
    "leagues": [],
    "selected_league_id": None,
    "league_snapshot": None,
    "chat_history": [],
    "fa_staleness_nudged": set(),  # (league_id, freshest_date) already nudged about this session
    "left_league_ids": [],  # tracked leagues no longer returned by Sleeper's last sync, awaiting archive/delete/dismiss
    "manage_leagues_expanded": False,  # keeps the expander open across the reruns its own buttons trigger
    # API keys applied via the sidebar's "Connect Your Accounts" section. Take effect
    # immediately for this session and also get written into .env (see
    # save_parsed_keys_to_env), so they're picked up automatically on the next launch too.
    # A blank string means "not set here", falling back to whatever .env already had.
    "anthropic_api_key_override": "",
    "gemini_api_key_override": "",
    "openai_api_key_override": "",
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


def api_key_for(provider: str) -> Optional[str]:
    """The session's own pasted/uploaded key for this provider, if any, else None (meaning
    "fall back to whatever llm_engine already loaded from .env")."""
    return st.session_state.get(f"{provider}_api_key_override") or None


CREDENTIAL_FIELD_ALIASES = {
    "anthropic_api_key_override": ("ANTHROPIC_API_KEY", "ANTHROPIC", "CLAUDE_API_KEY", "CLAUDE"),
    "gemini_api_key_override": ("GEMINI_API_KEY", "GEMINI", "GOOGLE_API_KEY", "GOOGLE"),
    "openai_api_key_override": ("OPENAI_API_KEY", "OPENAI", "CHATGPT_API_KEY", "CHATGPT", "GPT"),
    "username": ("SLEEPER_USERNAME", "SLEEPER", "USERNAME"),
}


def parse_credentials_blob(text: str) -> dict[str, str]:
    """Pull API keys and a Sleeper username out of a pasted/uploaded blob — a real .env file
    (KEY=value lines) works directly since it's the same format .env.example already uses;
    a looser "label: value" style also works. Falls back to sniffing bare, unlabeled key
    values by their provider-specific prefix (sk-ant-, AIza..., sk-...) for a blob that's
    just a few pasted strings with no labels at all. Only returns what it actually found —
    never guesses or fabricates a field.
    """
    found: dict[str, str] = {}
    unlabeled_tokens: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            label, _, value = line.partition("=")
        elif ":" in line:
            label, _, value = line.partition(":")
        else:
            unlabeled_tokens.extend(line.split())
            continue
        label = label.strip().upper().replace(" ", "_")
        value = value.strip().strip('"').strip("'")
        if not value:
            continue
        for field, aliases in CREDENTIAL_FIELD_ALIASES.items():
            if label in aliases and field not in found:
                found[field] = value
                break
        else:
            unlabeled_tokens.append(value)

    for token in unlabeled_tokens:
        if token.startswith("sk-ant-") and "anthropic_api_key_override" not in found:
            found["anthropic_api_key_override"] = token
        elif token.startswith("AIza") and "gemini_api_key_override" not in found:
            found["gemini_api_key_override"] = token
        elif token.startswith("sk-") and "openai_api_key_override" not in found:
            found["openai_api_key_override"] = token

    return found


def activate_league(league_id: str) -> None:
    """Make this league the one shown across the dashboard and debate panel — loads its
    cached snapshot, chat history, and per-league Draft Sharks data. Shared by the main-panel
    league switcher and the sidebar's own first-load fallback so both stay in sync.

    A league that's never been individually synced (just discovered via Sync Leagues, never
    actually pulled) has no cached snapshot at all — auto-fetch one right here rather than
    making the user separately go find "Refresh This League" in the sidebar after switching
    to it. Already-cached leagues are left alone; use the (co-located) Refresh button for
    those when you actually want fresher data, not on every switch.
    """
    st.session_state.selected_league_id = league_id
    st.session_state.chat_history = load_chat_history(league_id)
    st.session_state.league_snapshot = st.session_state.sleeper_client.load_latest_snapshot(league_id)
    # Free Agent Finder is tied to one league's actual roster and must never leak between
    # leagues, so it only ever loads from this league's own subdirectory. Dynasty Rankings is
    # format-based (not roster-based) so it's read from the shared global pool too — DataMerger
    # merges both automatically.
    st.session_state.data_merger = DataMerger(league_dir=league_projections_dir(league_id))

    if st.session_state.league_snapshot is None:
        client: SleeperClient = st.session_state.sleeper_client
        try:
            st.session_state.league_snapshot = client.sync_league(league_id, client.get_players())
        except Exception:  # noqa: BLE001 - never block switching leagues on a sync hiccup
            pass  # dashboard falls back to its usual "sync a league" empty state


def maybe_nudge_stale_free_agents(league_id: str, merger: DataMerger) -> None:
    """Ask (once per data state, not every question) for a fresher Free Agent Finder export.

    Waiver/roster value shifts week to week more than dynasty rankings do, so
    stale Free Agent Finder data is the case most worth a proactive nudge
    rather than just a quiet caveat in the answer. Deterministic, not left to
    the LLM to track "did I already mention this" turn to turn — keyed by the
    file's own freshest_date, so it re-nudges only if that date changes (a
    newer, still-stale re-upload) or in a fresh session, not every message.
    """
    if not (merger.is_free_agents_loaded and merger.free_agents_is_stale):
        return
    key = (league_id, merger.free_agents_freshest_date)
    if key in st.session_state.fa_staleness_nudged:
        return
    st.session_state.fa_staleness_nudged.add(key)
    append_message(
        "notice",
        f"Your Free Agent Finder data is {merger.free_agents_staleness_days} days old "
        f"(as of {merger.free_agents_freshest_date}). Waiver/roster value shifts week to week, so if this "
        "question is about a current decision, a fresh export would likely be more accurate — upload one "
        "in the sidebar when you get a chance. Answering with what's loaded for now."
    )


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
    # "notice" messages (stale-data nudges) are ephemeral UI bookkeeping — never worth summarizing
    # into permanent memory, and don't need to survive a compaction pass either.
    old_messages = [m for m in history if m.get("role") not in ("summary", "notice") and m.get("ts", 0) < cutoff]
    recent_messages = [m for m in history if m.get("role") not in ("summary", "notice") and m.get("ts", 0) >= cutoff]

    if not old_messages:
        return False, f"Nothing older than {max_age_days} days to compact."

    new_summary = llm_engine.summarize_history(old_messages, prior_summary=prior_summary, api_key=api_key_for("anthropic"))
    if new_summary.startswith("⚠️"):
        return False, f"Compaction aborted, history untouched: {new_summary}"

    backup_path = CHATS_DIR / f"{league_id}_history.pre_compact_{int(time.time())}.json"
    backup_path.write_text(json.dumps(history, indent=2))

    new_history = [{"role": "summary", "content": new_summary, "ts": time.time()}] + recent_messages
    save_chat_history(league_id, new_history)
    return True, f"Compacted {len(old_messages)} messages older than {max_age_days} days into a memory block."


def delete_league_completely(league_id: str) -> list[str]:
    """Purge every local cache for one league: snapshots, its own Draft Sharks uploads
    (never the shared global rankings pool), chat history + compaction backups, its
    format override, and any attachment scoped exclusively to it (one scoped to this
    league among others just has this league_id dropped from its scope, not deleted).

    This never touches Sleeper itself — it's a local-cache purge only. If the user is
    still actually a member, the league will simply reappear, unsynced, next time they
    click Sync Leagues; that's expected, not a bug.
    """
    removed: list[str] = []

    for p in st.session_state.sleeper_client.cache_dir.glob(f"{league_id}_*.json"):
        p.unlink(missing_ok=True)
        removed.append(p.name)

    league_dir = league_projections_dir(league_id)
    if league_dir.exists():
        shutil.rmtree(league_dir)
        removed.append(f"{league_dir}/")

    for p in CHATS_DIR.glob(f"{league_id}_history*.json"):
        p.unlink(missing_ok=True)
        removed.append(p.name)

    decision_log.forget_decisions(league_id)

    set_format_override(league_id, None)

    for item in list_attachments():
        if not item["league_ids"]:
            continue
        if set(item["league_ids"]) == {league_id}:
            delete_attachment(item["filename"])
            removed.append(item["filename"])
        elif league_id in item["league_ids"]:
            set_scope(item["filename"], [lid for lid in item["league_ids"] if lid != league_id])

    if st.session_state.user_id:
        forget_league(st.session_state.user_id, league_id)

    st.session_state.leagues = [lg for lg in st.session_state.leagues if lg["league_id"] != league_id]
    if st.session_state.selected_league_id == league_id:
        st.session_state.selected_league_id = None
        st.session_state.league_snapshot = None
        st.session_state.chat_history = []
        st.session_state.data_merger = DataMerger()

    return removed


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


def format_scoring_settings(scoring_settings: dict) -> str:
    """Every non-zero Sleeper scoring category, compact — the exact rules, not a PPR/superflex summary."""
    if not scoring_settings:
        return ""
    pairs = sorted((k, v) for k, v in scoring_settings.items() if v)
    return ", ".join(f"{k}={v}" for k, v in pairs)


def build_context(snapshot: dict, roster_table: list[dict]) -> str:
    league = snapshot["league"]
    fmt = league_format_summary(league)
    merger: DataMerger = st.session_state.data_merger
    league_id = st.session_state.get("selected_league_id")
    special_format = get_format_override(league_id) if league_id else None
    lines = [
        f"League: {fmt['name']} ({fmt['season']}) — {fmt['type']}"
        + (f", {special_format}" if special_format else "")
        + f", {fmt['teams']} teams, {'Superflex' if fmt['superflex'] else '1QB'}, {fmt['scoring']}, "
        f"taxi slots: {fmt['taxi_slots']}",
    ]

    if special_format and special_format in FORMAT_GUIDANCE:
        lines.append(f"\n{FORMAT_GUIDANCE[special_format]}")

    if fmt["type"] != "Dynasty":
        lines.append(
            f"\nThis is a {fmt['type']} league, not dynasty — Draft Sharks' 3yr/5yr multi-year projections "
            "and rookie-pick trade value don't apply here; the roster doesn't persist to next season, so "
            "only this-season production matters. Discount or ignore the long-horizon numbers rather than "
            "reasoning from them by default; lean on 1yr projection, rest-of-season Free Agent Finder data, "
            "and current-season VORP instead."
        )

    scoring_str = format_scoring_settings(league.get("scoring_settings") or {})
    if scoring_str:
        lines.append(
            "\nFULL SCORING SETTINGS for this exact league (Sleeper's own stat-category weights, not a "
            "PPR/superflex label): " + scoring_str + ". A Draft Sharks tier list assumes ITS OWN scoring "
            "model, which may not match this league in the details — a different reception value, a TE "
            "premium bonus, bonus thresholds, IDP weighting, etc. Use this list to judge where a player's "
            "loaded tier/value might be off for this specific league, not just accept it at face value."
        )

    history = st.session_state.get("chat_history", [])
    summary_msgs = [m for m in history if m.get("role") == "summary"]
    # "notice" messages (e.g. stale-data nudges) are UI bookkeeping, not part of the analytical
    # discussion — replaying them back as if they were a prior debate turn would be noise.
    recent_msgs = [m for m in history if m.get("role") not in ("summary", "notice")][-RECENT_TURNS_IN_CONTEXT:]
    if summary_msgs or recent_msgs:
        lines.append("\nCONVERSATION MEMORY — prior debates in this league (older-to-newer):")
        if summary_msgs:
            lines.append(f"  [compacted memory of older history]\n{summary_msgs[-1]['content']}")
        for m in recent_msgs:
            lines.append(f"  [{m.get('role', '?')}] {m.get('content', '')}")

    lines.append(
        "\nDATA AVAILABILITY — work with whatever is actually loaded; none of this is required to answer. "
        "Missing data is never a reason to refuse or stall — reason from positional scarcity, roster "
        "construction, market consensus (Beat Tracker's live search), and general dynasty football judgment "
        "instead, and say plainly in your answer what wasn't available rather than quietly working around it. "
        "Only call special attention to it if it's genuinely material to the question (e.g. no numeric grounding "
        "at all for a close trade call) — don't caveat every single response with the same boilerplate."
    )
    lines.append(f"  - Draft Sharks Dynasty Rankings: {'loaded' if merger.is_loaded else 'NOT LOADED'}")
    lines.append(f"  - Draft Sharks Free Agent Finder: {'loaded' if merger.is_free_agents_loaded else 'NOT LOADED'}")
    lines.append(f"  - Sleeper native weekly projections: {'loaded' if snapshot.get('projections') else 'NOT AVAILABLE this sync'}")

    freshness = build_freshness_manifest(snapshot, merger)
    if freshness:
        lines.append(
            "\nDATA FRESHNESS (freshest first, loaded sources only). The Beat Tracker's and Contrarian's own "
            "live web search is always fresher than anything below, since it runs at the moment of the "
            "question — treat it as the top entry implicitly. When sources conflict, lean toward the more "
            "recently updated one, but weigh what kind of claim it is: a fresher injury/depth-chart/news "
            "signal should outweigh a staler one fairly decisively, while a fresher season-long dynasty "
            "valuation is only a mild edge over an older one, since long-term value doesn't go stale as fast "
            "as situational facts."
        )
        for label, date, age in freshness:
            age_label = f"{age}d old" if age is not None else "date unknown"
            if age is not None and age >= 30:
                stale_flag = " — EGREGIOUSLY OUTDATED: say so plainly in your answer, don't use quietly"
            elif age is not None and age >= 7:
                stale_flag = " — STALE"
            else:
                stale_flag = ""
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

    captioned = [a for a in list_attachments(league_id=st.session_state.selected_league_id) if a["caption"].strip()]
    if captioned:
        lines.append(
            "\nREFERENCE MATERIAL the user uploaded (screenshots/articles, captioned by hand — you're only "
            "given the caption text, not the actual file, so treat it as a claim to weigh, not verified fact):"
        )
        for a in captioned[:20]:
            lines.append(f"  - {a['caption']}")

    return "\n".join(lines)


# ------------------------------------------------------------------ sidebar --

def sync_leagues(username: str, *, announce: bool = True) -> bool:
    """Look up a Sleeper username and (re)populate leagues from it. Returns success.

    `announce=False` is used for the on-refresh auto-restore: it stays quiet on success
    (no need to tell the user their own remembered session loaded) and on failure shows a
    soft, retry-oriented note rather than "No Sleeper user found" — a stale/unreachable
    lookup right after a page load isn't necessarily proof the username is wrong.
    """
    client: SleeperClient = st.session_state.sleeper_client
    try:
        user = client.get_user(username)
    except SleeperAPIError as exc:
        if announce:
            st.error(f"Couldn't reach Sleeper: {exc}")
        else:
            st.caption("Couldn't restore your last session automatically — click Sync Leagues to retry.")
        return False

    if not user:
        if announce:
            st.error(f"No Sleeper user found for '{username}'")
        else:
            st.caption("Couldn't restore your last session automatically — click Sync Leagues to retry.")
        return False

    st.session_state.username = username
    st.session_state.user_id = user["user_id"]
    save_last_username(username)
    # Sleeper's league list is a full replacement, not incremental — anything we
    # were tracking that's no longer in it means the user left/was removed/the
    # league was deleted. Diff against what's persisted, not just this session's
    # in-memory list, so this still catches it on a user's very first sync of a
    # fresh browser session.
    prior_prefs = get_prefs(user["user_id"])
    previously_tracked = set(prior_prefs.get("order", [])) | set(prior_prefs.get("archived", []))

    try:
        st.session_state.leagues = client.get_user_leagues(user["user_id"])
    except SleeperAPIError as exc:
        if announce:
            st.error(f"Found your Sleeper account, but couldn't fetch its leagues: {exc}")
        return False
    fresh_ids = {lg["league_id"] for lg in st.session_state.leagues}
    newly_left = previously_tracked - fresh_ids
    if newly_left:
        st.session_state.left_league_ids = sorted(newly_left)

    if announce:
        if not st.session_state.leagues:
            st.warning("No leagues found for this user in the current season.")
        else:
            st.success(f"Found {len(st.session_state.leagues)} league(s).")
    return True


with st.sidebar:
    st.markdown("### 🔑 Connect Your Accounts")
    st.caption(
        "Paste your keys in .env format (or upload a .txt/.env/.pdf with them), then click "
        "Apply. This writes them into your local .env automatically, so it's a one-time step — "
        "not something typed in every session."
    )
    with st.expander(
        "Paste or upload keys + Sleeper username",
        expanded=not llm_engine.is_claude_configured(api_key_for("anthropic")),
    ):
        creds_text = st.text_area(
            "Paste keys (one per line)",
            key="creds_paste_box",
            placeholder=(
                "ANTHROPIC_API_KEY=sk-ant-...\n"
                "GEMINI_API_KEY=...\n"
                "OPENAI_API_KEY=...\n"
                "SLEEPER_USERNAME=yourname"
            ),
            height=120,
        )
        creds_file = st.file_uploader(
            "...or upload a file with the same content", type=["txt", "env", "pdf"], key="creds_file_upload"
        )
        if st.button("Apply", key="apply_credentials", use_container_width=True):
            blob = creds_text or ""
            if creds_file is not None:
                if creds_file.name.lower().endswith(".pdf"):
                    import pypdf

                    reader = pypdf.PdfReader(creds_file)
                    blob += "\n" + "\n".join(page.extract_text() or "" for page in reader.pages)
                else:
                    blob += "\n" + creds_file.read().decode("utf-8", errors="ignore")

            parsed = parse_credentials_blob(blob)
            if not parsed:
                st.warning("Didn't recognize any keys or a username in that — check the format and try again.")
            else:
                key_updates = {k: v for k, v in parsed.items() if k != "username"}
                if key_updates:
                    for field, value in key_updates.items():
                        st.session_state[field] = value
                    save_parsed_keys_to_env(key_updates)

                found = [
                    label for field, label in (
                        ("anthropic_api_key_override", "Anthropic"),
                        ("gemini_api_key_override", "Gemini"),
                        ("openai_api_key_override", "OpenAI"),
                    ) if field in parsed
                ]
                if "username" in parsed:
                    found.append("Sleeper username")
                    sync_leagues(parsed["username"])
                st.success(f"Applied: {', '.join(found)}.")
                st.rerun()

    st.markdown("### 🏈 Sleeper Sync")
    username_input = st.text_input("Sleeper Username", value=st.session_state.username)

    if st.button("Sync Leagues", use_container_width=True):
        sync_leagues(username_input)

    if (
        st.session_state.username
        and st.session_state.user_id is None
        and not st.session_state.auto_sync_attempted
    ):
        st.session_state.auto_sync_attempted = True
        with st.spinner(f"Restoring session for {st.session_state.username}..."):
            sync_leagues(st.session_state.username, announce=False)

    if st.session_state.get("left_league_ids"):
        st.warning(
            "No longer showing as a member of these leagues (left, removed, or the league was "
            "deleted) — their local data is still cached. Archive to just hide them, or delete to "
            "purge their data (snapshots, Draft Sharks uploads, chat history) permanently."
        )
        for lid in list(st.session_state.left_league_ids):
            cached_snapshot = st.session_state.sleeper_client.load_latest_snapshot(lid)
            league_name = cached_snapshot["league"]["name"] if cached_snapshot else lid
            st.caption(league_name)
            lc1, lc2, lc3 = st.columns(3)
            if lc1.button("Archive", key=f"leftleague_archive_{lid}"):
                toggle_archive(st.session_state.user_id, lid)
                st.session_state.left_league_ids.remove(lid)
                st.rerun()
            if lc2.button("Delete", key=f"leftleague_delete_{lid}"):
                delete_league_completely(lid)
                st.session_state.left_league_ids.remove(lid)
                st.success(f"Deleted local data for {league_name}.")
                st.rerun()
            if lc3.button("Keep as-is", key=f"leftleague_dismiss_{lid}"):
                st.session_state.left_league_ids.remove(lid)
                st.rerun()

    if st.session_state.leagues:
        visible_leagues, archived_leagues = sorted_leagues(st.session_state.user_id, st.session_state.leagues)
        league_options = {lg["league_id"]: lg["name"] for lg in visible_leagues}

        if league_options:
            option_ids = list(league_options.keys())
            selected = st.session_state.selected_league_id
            if selected not in option_ids:
                # First load this session, or the previously-active league just got archived/
                # deleted out from under it — fall back to the first visible one. The actual
                # switcher lives at the top of the main panel now, not here.
                selected = option_ids[0]
                activate_league(selected)
            st.caption(f"📂 Active league: **{league_options[selected]}** — switch it above the dashboard.")

            current_override = get_format_override(selected) or STANDARD
            format_choice = st.selectbox(
                "Special format",
                options=list(FORMAT_OPTIONS),
                index=list(FORMAT_OPTIONS).index(current_override),
                help="Dynasty/Keeper/Redraft are detected automatically from Sleeper. Best Ball and "
                "Chopped aren't reliably auto-detectable, so set this manually if this league is one — "
                "it changes how the panel reasons (e.g. no trades or floor-first start/sit in Chopped, "
                "no week-to-week management in Best Ball).",
            )
            if format_choice != current_override:
                set_format_override(selected, format_choice)
                st.rerun()
        else:
            st.info("All discovered leagues are archived — unarchive one below to select it.")

        with st.expander(
            f"Manage Leagues ({len(st.session_state.leagues)})",
            expanded=st.session_state.manage_leagues_expanded,
        ):
            st.caption(
                "Archive leagues you don't want on the front dashboard, or reorder them. Delete "
                "permanently purges all locally cached data for a league (snapshots, its own Draft "
                "Sharks uploads, chat history) — it doesn't leave the Sleeper league itself, so if "
                "you're still a member it'll just reappear fresh next time you sync."
            )
            ordered = visible_leagues + archived_leagues
            for idx, lg in enumerate(ordered):
                lid = lg["league_id"]
                is_archived = lid in {a["league_id"] for a in archived_leagues}
                # Name gets its own full-width line — a name plus four buttons never
                # fit in one row without wrapping mid-word, so don't compete for space.
                st.markdown(f"**{'🗄️ ' if is_archived else ''}{lg['name']}**")
                arch_col, up_col, down_col, del_col = st.columns([2.2, 1, 1, 1])
                if arch_col.button(
                    "Unarchive" if is_archived else "Archive", key=f"arch_{lid}", use_container_width=True,
                ):
                    toggle_archive(st.session_state.user_id, lid)
                    st.session_state.manage_leagues_expanded = True
                    st.rerun()
                if up_col.button("▲", key=f"up_{lid}", disabled=idx == 0, help="Move up", use_container_width=True):
                    move_league(st.session_state.user_id, st.session_state.leagues, lid, -1)
                    st.session_state.manage_leagues_expanded = True
                    st.rerun()
                if down_col.button(
                    "▼", key=f"down_{lid}", disabled=idx == len(ordered) - 1, help="Move down",
                    use_container_width=True,
                ):
                    move_league(st.session_state.user_id, st.session_state.leagues, lid, 1)
                    st.session_state.manage_leagues_expanded = True
                    st.rerun()

                if st.session_state.get("pending_delete_league_id") == lid:
                    if del_col.button("Cancel", key=f"cancel_del_{lid}", use_container_width=True):
                        st.session_state.pending_delete_league_id = None
                        st.session_state.manage_leagues_expanded = True
                        st.rerun()
                elif del_col.button("🗑️", key=f"del_{lid}", help="Delete permanently", use_container_width=True):
                    st.session_state.pending_delete_league_id = lid
                    st.session_state.manage_leagues_expanded = True
                    st.rerun()

                if st.session_state.get("pending_delete_league_id") == lid:
                    st.warning(
                        f"Permanently delete all local data for **{lg['name']}**? This can't be undone "
                        "(no in-app undo — only whatever backups your OS/filesystem might keep)."
                    )
                    if st.button("Confirm Delete", key=f"confirm_del_{lid}", use_container_width=True):
                        removed = delete_league_completely(lid)
                        st.session_state.pending_delete_league_id = None
                        st.session_state.manage_leagues_expanded = True
                        st.success(f"Deleted local data for {lg['name']} ({len(removed)} item(s) removed).")
                        st.rerun()
                st.markdown("<hr style='margin:6px 0;opacity:0.15'>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 Draft Sharks / War Room Data")
    st.caption(
        "Draft Sharks has no public export API — save a tool page as a PDF and upload it here. The kind "
        "is auto-detected from its content, not the filename or which league is selected: **Dynasty "
        "Rankings** is format-based (PPR/standard, superflex/1QB, TE premium), not tied to any roster, so "
        "it goes into a shared pool used by every league of that format. **Free Agent Finder** is tied to "
        "one league's actual roster and only ever applies to the league currently selected above. Anything "
        "that isn't recognized as one of those — a screenshot, an article, an unsupported export — is kept "
        "as reference material instead (see below) rather than being discarded."
    )
    # Scope has to live outside the form: a form only releases its widgets' values on
    # submit, so a selector inside one can't reactively reveal the league picker.
    scope_mode = st.segmented_control(
        "Note/attachment applies to",
        options=["Global (all leagues)", "Specific league(s)"],
        default="Global (all leagues)",
        key="upload_scope_mode",
        help="Only matters for the comment/note and for anything that falls through to Reference "
        "Material — Draft Sharks data itself already routes by its own rules regardless of this.",
    )
    scope_league_ids: list[str] = []
    if scope_mode == "Specific league(s)" and st.session_state.leagues:
        league_name_map = {lg["league_id"]: lg["name"] for lg in st.session_state.leagues}
        default_scope = [st.session_state.selected_league_id] if st.session_state.selected_league_id in league_name_map else []
        scope_league_ids = st.multiselect(
            "Which league(s)", options=list(league_name_map.keys()), default=default_scope,
            format_func=lambda lid: league_name_map[lid], key="upload_scope_leagues",
        )

    with st.form("upload_form", clear_on_submit=True):
        uploaded = st.file_uploader(
            "Upload Draft Sharks PDF/CSV/JSON, or any other file as reference material",
            type=["pdf", "csv", "json", "png", "jpg", "jpeg", "webp", "gif", "txt"],
        )
        note = st.text_area(
            "Comments, questions, or labels for this upload (optional)",
            placeholder="e.g. \"ignore this ranking, Bijan tweaked his hamstring in preseason\" or "
            "\"is this article's injury report still accurate?\"",
            height=80,
        )
        submitted = st.form_submit_button("Upload")

    if submitted and scope_mode == "Specific league(s)" and not scope_league_ids:
        st.warning("Select at least one league above, or switch back to Global.")
    elif submitted and uploaded is None:
        st.warning("Choose a file before clicking Upload.")
    elif submitted and uploaded is not None:
        data = bytes(uploaded.getbuffer())
        note = note.strip()
        suffix = Path(uploaded.name).suffix.lower()
        recognized = False
        note_scope = scope_league_ids if scope_mode == "Specific league(s)" else None

        if suffix in (".pdf", ".csv", ".json"):
            staging_dir = PROJECTIONS_DIR / "_staging"
            staging_dir.mkdir(parents=True, exist_ok=True)
            staging_path = staging_dir / uploaded.name
            staging_path.write_bytes(data)
            try:
                _, kind = load_projection_file(staging_path)
            except Exception:
                staging_path.unlink(missing_ok=True)  # not parseable — falls through to reference material below
            else:
                if kind == "free_agents" and not st.session_state.selected_league_id:
                    staging_path.unlink(missing_ok=True)
                    st.error("This looks like a Free Agent Finder export, tied to one league's roster — select a league above first, then re-upload.")
                    recognized = True  # handled (as a rejection), don't also file it as an attachment
                else:
                    if kind == "free_agents":
                        dest_dir = league_projections_dir(st.session_state.selected_league_id)
                        location_label = "this league only (roster-specific)"
                    else:
                        dest_dir = GLOBAL_PROJECTIONS_DIR
                        location_label = "the shared pool (applies to any league using this format)"
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    staging_path.replace(dest_dir / uploaded.name)
                    st.session_state.data_merger.reload()
                    st.success(f"Recognized as Draft Sharks data — saved to {location_label}.")
                    recognized = True
                    if note:
                        # The data went into the projections pool, not the attachment store — but the
                        # note is still worth surfacing to the panel, so it gets a small text-only entry.
                        save_attachment(f"{uploaded.name}.note.txt", note.encode(), caption=note, league_ids=note_scope)

        if not recognized:
            save_attachment(uploaded.name, data, caption=note, league_ids=note_scope)
            st.info(f"Didn't match a known Draft Sharks format — saved '{uploaded.name}' as reference material below for the panel to consider when you ask about it.")

    global_files = sorted(p.name for p in GLOBAL_PROJECTIONS_DIR.glob("*") if p.suffix in (".csv", ".json", ".pdf"))
    if global_files:
        st.caption("Shared rankings (any league): " + ", ".join(global_files))
    if st.session_state.selected_league_id:
        league_proj_dir = league_projections_dir(st.session_state.selected_league_id)
        league_files = sorted(p.name for p in league_proj_dir.glob("*") if p.suffix in (".csv", ".json", ".pdf")) if league_proj_dir.exists() else []
        if league_files:
            st.caption("This league only (roster-specific): " + ", ".join(league_files))

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
    st.markdown(status_line("Claude (Quant/Moderator) Connected", llm_engine.is_claude_configured(api_key_for("anthropic"))), unsafe_allow_html=True)
    st.markdown(status_line("Gemini (Beat Tracker) Connected", llm_engine.is_gemini_configured(api_key_for("gemini"))), unsafe_allow_html=True)
    st.markdown(status_line("ChatGPT (Contrarian) Connected", llm_engine.is_openai_configured(api_key_for("openai"))), unsafe_allow_html=True)

    missing_keys = [
        var for var, ok in (
            ("ANTHROPIC_API_KEY", llm_engine.is_claude_configured(api_key_for("anthropic"))),
            ("GEMINI_API_KEY", llm_engine.is_gemini_configured(api_key_for("gemini"))),
            ("OPENAI_API_KEY", llm_engine.is_openai_configured(api_key_for("openai"))),
        ) if not ok
    ]
    if missing_keys:
        st.caption(
            f"Missing: {', '.join(missing_keys)}. Paste them into 🔑 Connect Your Accounts above, or copy "
            "`.env.example` to `.env` in the project folder, fill in the key(s), and restart `streamlit run app.py`."
        )

# ------------------------------------------------------------------ main ----

# The league switcher itself lives here, front and center, rather than buried in the
# sidebar — this is the one control most likely to get used every single visit. The
# Refresh button sits right next to it, not off in the sidebar, since re-pulling data
# for the league you just switched to is the natural next thing you'd want to do.
if st.session_state.leagues:
    visible_leagues, archived_leagues = sorted_leagues(st.session_state.user_id, st.session_state.leagues)
    league_options = {lg["league_id"]: lg["name"] for lg in visible_leagues}
    if league_options:
        option_ids = list(league_options.keys())
        current = st.session_state.selected_league_id
        if current not in option_ids:
            current = option_ids[0]

        st.caption("📂 Active League — switches the dashboard and debate panel below")
        switch_col, refresh_col = st.columns([5, 1])
        with switch_col:
            picked = st.segmented_control(
                "Active League",
                options=option_ids,
                format_func=lambda lid: league_options[lid],
                default=current,
                label_visibility="collapsed",
            )
        if picked is None:
            # segmented_control allows clicking the active pill to deselect it — never
            # leave nothing active, just fall back to whatever was already selected.
            picked = current
        if picked != st.session_state.selected_league_id:
            activate_league(picked)
            st.rerun()
        with refresh_col:
            if st.button(
                "🔄 Refresh", use_container_width=True,
                help="Re-pull this league's rosters/scoring/taxi/traded picks from Sleeper.",
            ):
                client: SleeperClient = st.session_state.sleeper_client
                try:
                    with st.spinner("Syncing..."):
                        st.session_state.league_snapshot = client.sync_league(picked, client.get_players())
                    st.success("League synced.")
                except SleeperAPIError as exc:
                    st.error(f"Couldn't reach Sleeper: {exc}")

snapshot = st.session_state.league_snapshot
if not snapshot:
    st.title("Fantasy Football Command Center")
    st.info("Sync a Sleeper username and select a league in the sidebar to get started.")
    st.stop()

# The active league's own name carries the page title once one is loaded — it's the
# single most important thing to make obvious, since the sidebar list can otherwise
# make it unclear which league is actually being viewed.
league = snapshot["league"]
fmt = league_format_summary(league)
st.title(f"🏈 {fmt['name']}")
st.caption(
    f"Fantasy Football Command Center · {fmt['type']} · {fmt['teams']}-team · "
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
        maybe_nudge_stale_free_agents(st.session_state.selected_league_id, st.session_state.data_merger)

        with st.spinner("Consulting the front office..."):
            if trigger_mode == "claude":
                append_message("quant", llm_engine.ask_quant(context, trigger_question, api_key=api_key_for("anthropic")))
            elif trigger_mode == "gemini":
                append_message("beat", llm_engine.ask_beat(context, trigger_question, api_key=api_key_for("gemini")))
            elif trigger_mode == "gpt":
                beat_reply = ""
                quant_reply = ""
                append_message("contrarian", llm_engine.ask_contrarian(
                    context, trigger_question, quant_reply, beat_reply, api_key=api_key_for("openai")
                ))
            else:
                result = llm_engine.run_debate(
                    context, trigger_question,
                    claude_key=api_key_for("anthropic"),
                    gemini_key=api_key_for("gemini"),
                    openai_key=api_key_for("openai"),
                )
                append_message("quant", result.quant)
                append_message("beat", result.beat)
                append_message("contrarian", result.contrarian)
                append_message("moderator", result.moderator)
                decision_log.log_decision(
                    st.session_state.selected_league_id, trigger_question, result.verdict, result.moderator
                )

    st.markdown("---")
    badge_map = {
        "user": ("You", "badge-user"),
        "quant": ("QUANT ANALYST · Claude", "badge-quant"),
        "beat": ("BEAT TRACKER · Gemini", "badge-beat"),
        "contrarian": ("CONTRARIAN · ChatGPT", "badge-contrarian"),
        "moderator": ("MODERATOR VERDICT · Claude", "badge-moderator"),
        "summary": ("🧠 MEMORY SUMMARY", "badge-summary"),
        "notice": ("⚠️ NOTICE", "badge-notice"),
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

    decisions = decision_log.load_decisions(st.session_state.selected_league_id)
    if decisions:
        with st.expander(f"📋 Decision Log ({len(decisions)})"):
            st.caption(
                "Every Moderator verdict this league has gotten, newest first — "
                "the record to check back against once picks are made or a trade lands."
            )
            log_df = pd.DataFrame(
                [
                    {
                        "Date": d["date"],
                        "Question": d["question"],
                        "Call": d.get("recommendation", ""),
                        "Conviction": d.get("conviction", ""),
                        "Reason": d.get("reason", ""),
                        "Risk": d.get("risk", ""),
                        "Recon": d.get("recon", ""),
                        "Price Ceiling": d.get("price_ceiling", ""),
                    }
                    for d in reversed(decisions)
                ]
            )
            st.dataframe(log_df, use_container_width=True, hide_index=True)

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

# ------------------------------------------------------------------ reference material --

st.markdown("---")
st.subheader("Reference Material")
st.caption(
    "Screenshots, articles, injury notifications — anything worth having on hand for a debate that isn't "
    "structured Draft Sharks data. Give each one a short caption; captions (not the raw file) are what the "
    "panel actually sees when you ask about it."
)

attachments = list_attachments()  # unfiltered — this is a management view, show everything regardless of scope
if not attachments:
    st.caption("Nothing uploaded yet — drop a file above that isn't recognized as Draft Sharks data.")
else:
    league_name_map = {lg["league_id"]: lg["name"] for lg in st.session_state.leagues}
    for item in attachments:
        acol1, acol2, acol3 = st.columns([1, 3, 1])
        if item["is_image"]:
            acol1.image(str(item["path"]), use_container_width=True)
        else:
            acol1.markdown(f"📄 **{item['filename']}**")
        new_caption = acol2.text_input(
            "Caption", value=item["caption"], key=f"caption_{item['filename']}", label_visibility="collapsed",
            placeholder="What is this? (e.g. 'ESPN: Chase questionable for Sunday')",
        )
        scope_label = (
            "🎯 " + ", ".join(league_name_map.get(lid, lid) for lid in item["league_ids"])
            if item["league_ids"] else "🌐 Global (all leagues)"
        )
        acol2.caption(f"Applies to: {scope_label}")
        if new_caption != item["caption"] and acol2.button("Save Caption", key=f"save_caption_{item['filename']}"):
            set_caption(item["filename"], new_caption)
            st.rerun()
        if acol3.button("Delete", key=f"delete_{item['filename']}"):
            delete_attachment(item["filename"])
            st.rerun()

        with st.expander(f"Change scope — {item['filename']}"):
            edit_mode = st.segmented_control(
                "Applies to", options=["Global (all leagues)", "Specific league(s)"],
                default="Specific league(s)" if item["league_ids"] else "Global (all leagues)",
                key=f"scope_mode_{item['filename']}",
            )
            edit_league_ids: list[str] = []
            if edit_mode == "Specific league(s)" and st.session_state.leagues:
                edit_league_ids = st.multiselect(
                    "Which league(s)", options=list(league_name_map.keys()),
                    default=item["league_ids"] or [], format_func=lambda lid: league_name_map[lid],
                    key=f"scope_leagues_{item['filename']}",
                )
            if st.button("Save Scope", key=f"save_scope_{item['filename']}"):
                if edit_mode == "Specific league(s)" and not edit_league_ids:
                    st.warning("Select at least one league, or switch to Global.")
                else:
                    set_scope(item["filename"], edit_league_ids if edit_mode == "Specific league(s)" else None)
                    st.rerun()
