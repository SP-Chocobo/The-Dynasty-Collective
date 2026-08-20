"""
Fantasy Football Multi-LLM Command Center — Streamlit UI.

Sleeper Meets Claude: a dark, minimalist dashboard (Claude) accented with
functional sports-data color coding (Sleeper) — emerald for value surplus,
gold for taxi/bench alerts, crimson for injury flags — plus a four-persona
debate studio (Quant/Claude, Beat/Gemini, Contrarian/ChatGPT, Moderator/Claude).
"""

from __future__ import annotations

import base64
import html
import json
import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st
from PIL import Image

import bot_benchmark
import bot_config
import bot_research
import decision_log
import pinned_messages
import todo_log
import llm_engine
from attachments import ATTACHMENTS_DIR, list_attachments, save_attachment, set_caption, set_scope, delete_attachment
from data_merger import GLOBAL_PROJECTIONS_DIR, PROJECTIONS_DIR, DataMerger, load_projection_file, normalize_name, save_alias
from league_format import FORMAT_GUIDANCE, FORMAT_OPTIONS, STANDARD, get_format_override, set_format_override
from league_prefs import forget_league, get_prefs, move_league, sorted_leagues, toggle_archive
from player_universe import available_players, build_player_universe, league_usable_positions, matching_players
from sleeper_client import SleeperAPIError, SleeperClient, compute_points_from_stats, find_roster_for_user, league_format_summary

CHATS_DIR = Path("data/chats")
CHATS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTIONS_DIR.mkdir(parents=True, exist_ok=True)
GLOBAL_PROJECTIONS_DIR.mkdir(parents=True, exist_ok=True)
ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

ASSETS_DIR = Path("assets")


@st.cache_resource
def _page_icon():
    # Falls back to the plain emoji if the asset's ever missing -- a decorative brand
    # mark going missing shouldn't be able to take the whole app down with it.
    path = ASSETS_DIR / "icon_mark.png"
    try:
        return Image.open(path)
    except (FileNotFoundError, OSError):
        return "🏈"


@st.cache_resource
def _header_banner_data_uri() -> Optional[str]:
    path = ASSETS_DIR / "header_banner.jpg"
    try:
        return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode("ascii")
    except (FileNotFoundError, OSError):
        return None


st.set_page_config(page_title="Fantasy Football Command Center", layout="wide", page_icon=_page_icon())

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
    /* A verdict with the full panel behind it (Quant/Beat/Contrarian all weighed in) is a
       heavier claim than a quick follow-up reply -- same badge-moderator family/color so it's
       still obviously "the Moderator," just visibly more substantial via a glow, not a
       different hue that would read as a different persona entirely. */
    .badge-moderator-verdict { background: rgba(185,28,28,0.18); color: #f87171; border: 1px solid #b91c1c; box-shadow: 0 0 0 1px rgba(248,113,113,0.35), 0 0 8px rgba(185,28,28,0.45); }
    .badge-user { background: rgba(148,163,184,0.18); color: #cbd5e1; border: 1px solid #64748b; }
    .badge-summary { background: rgba(56,189,248,0.18); color: #7dd3fc; border: 1px solid #0ea5e9; }
    .badge-notice { background: rgba(245,158,11,0.18); color: #fbbf24; border: 1px solid #f59e0b; }
    .agent-block {
        border-radius: 8px; padding: 10px 14px; margin-bottom: 10px;
        background: #202124; border: 1px solid #2f3033;
        font-family: 'JetBrains Mono', 'DejaVu Sans Mono', monospace;
        white-space: pre-wrap;
    }
    .status-ok { color: #4ade80; }
    .status-bad { color: #64748b; }

    /* A persistent brand mark for the platform itself -- once a league loads, its own
       name takes over the big st.title() below (correctly; knowing which league you're
       looking at matters most), but that shouldn't mean the app's own identity vanishes
       entirely into a caption line easy to skim past. Small, quiet, and always in the
       same spot regardless of which league is focused. */
    .brand-eyebrow {
        font-size: 0.78rem; font-weight: 600; letter-spacing: 0.09em; text-transform: uppercase;
        color: #94a3b8; margin-bottom: 2px;
    }

    /* The header's own background art (see _header_banner_data_uri) -- the source image
       is near-black on the left fading into a lit football on the right, so the text
       block (left-aligned, see below) sits on its darkest region already. The linear-
       gradient layered on top is still needed for the narrower/mid-width case where the
       art's midtones creep further left than the text can safely sit on. Falls back to
       the plain flat color already used elsewhere (#202124-ish dark surfaces) with no
       image layer if the asset failed to load, so a missing file just means "no banner",
       never a broken header. */
    .st-key-app_header {
        border-radius: 10px;
        padding: 1.1rem 1.4rem 1rem;
        margin-bottom: 0.5rem;
        background-color: #0b0d12;
        background-size: cover;
        background-position: center;
        border: 1px solid #23262e;
    }
    .st-key-app_header h1 { margin-bottom: 0; }

    /* League switcher trigger: it shares a row with the Refresh action button, and
       Streamlit's default centered-label style made it read as just another action
       rather than a picker. Left-align the label, right-align the chevron (like a
       real <select>), and give it its own subtle background/border so it visually
       reads as "pick a league" rather than "do a thing". */
    [data-testid="stPopoverButton"] {
        background: #1b1c1f !important;
        border: 1px solid #2a2b2e !important;
        border-radius: 8px !important;
    }
    [data-testid="stPopoverButton"] > div {
        justify-content: space-between !important;
        width: 100%;
    }
    [data-testid="stPopoverButton"] p {
        font-weight: 600;
    }

    /* Refresh sits right next to the league switcher, but it's a secondary
       maintenance action, not a peer to "which league am I even looking at" — same
       heavy bordered-box treatment as the switcher made them read as two equally
       important controls. Understating Refresh (transparent, muted, no bold) lets the
       switcher read as the one thing this row is actually for. */
    .st-key-league_switcher_row .stButton button {
        background: transparent;
        border-color: #2a2b2e !important;
        color: #9ca3af;
        font-weight: 500;
    }
    .st-key-league_switcher_row .stButton button:hover {
        color: #e5e7eb;
        border-color: #3a3c42 !important;
        background: rgba(255,255,255,0.03);
    }

    /* Sidebar defaults to a width that crowds the Manage Leagues row and the
       credentials paste box — widen it out of the box instead of making everyone
       drag it wider by hand every time. Still resizable from here if you want more.
       Scoped to aria-expanded="true" only: min-width beats max-width per the CSS
       spec, so an unscoped rule here fights Streamlit's own collapse (which sets
       max-width: 0 on the same element) and leaves a chunk of dead space and a
       sliver of visible sidebar even when "collapsed". */
    [data-testid="stSidebar"][aria-expanded="true"] { min-width: 400px; }

    /* Default Streamlit buttons read as understated on a dark theme — thin,
       low-contrast border, flat background that barely lifts off the page. Give
       every button (including icon-only ones like the reorder arrows) a bigger
       tap target and enough visual weight to look clickable at a glance, closer
       to how Sleeper's own controls feel. */
    .stButton button, .stFormSubmitButton button, .stDownloadButton button {
        min-height: 44px;
        min-width: 44px;
        padding: 10px 18px;
        font-weight: 600;
        border-width: 1.5px !important;
        transition: transform 0.05s ease, filter 0.05s ease, background 0.15s ease,
            border-color 0.15s ease, color 0.15s ease;
    }
    /* A bigger, bolder button needs an equally clear "yes, that registered" moment —
       without this the only click feedback was whatever the browser does by default,
       easy to miss at this size/weight. A quick press-down (not just a hover tint)
       reads as tactile regardless of what color the button happens to be. */
    .stButton button:active, .stFormSubmitButton button:active, .stDownloadButton button:active {
        transform: scale(0.96);
        filter: brightness(0.9);
    }
    /* Popover triggers (league switcher, Attach, revision history) and the segmented-
       control tabs are buttons under the hood but don't match the selector above --
       give them the same pressed cue so every clickable control in the app responds
       the same way. */
    [data-testid="stPopoverButton"]:active,
    [data-testid="stButtonGroup"] button:active {
        transform: scale(0.96);
        filter: brightness(0.9);
    }

    /* The Free Agents table's clickable sort header (real st.button()s, since a
       static HTML <th> can't call back into Python) needs to read as a table
       header row, not a row of big CTA buttons — shrink just this one back down
       and drop the visual weight the rule above intentionally adds everywhere else. */
    .st-key-fa_sort_header .stButton button {
        min-height: 30px;
        min-width: 0;
        padding: 4px 10px;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600;
        color: #8b8f98;
        background: #1b1c1f;
        border: 1px solid #2a2b2e !important;
        border-radius: 6px;
    }
    .st-key-fa_sort_header .stButton button:hover {
        color: #e5e7eb;
        border-color: #3a3c42 !important;
    }

    /* Archive/reorder/delete per league — frequent-but-minor list-management actions,
       not primary calls to action. At the app's default 44px/bold weight, four of them
       repeated per league was most of what made "League Controls" feel cluttered. */
    .st-key-manage_leagues_list .stButton button {
        min-height: 32px;
        padding: 4px 10px;
        font-size: 0.8rem;
        font-weight: 500;
    }

    /* Debate Studio dock: fixed to the bottom of the viewport (not "sticky" — sticky
       only engages once its own container scrolls into range, which for the last
       block on the page means "not until you've scrolled everything else past it".
       Fixed pins it regardless of scroll position on either tab's content, which is
       the actual ask. */
    .st-key-debate_dock {
        position: fixed;
        left: 0;
        /* Streamlit's own block-container CSS sets an explicit width on this element
           with higher specificity than a bare .st-key-* class, which silently wins over
           `right: 0` and forces the dock to the full viewport width regardless of the
           sidebar-offset `left` below — confirmed live: with the sidebar expanded
           (left: 400px) the dock still measured 1600px wide on a 1600px viewport, 400px
           of it past the right edge, taking every column split beyond roughly the
           three-quarter mark with it. !important forces the intended auto-computed
           width (viewport minus left minus right) to actually apply. */
        right: 0 !important;
        width: auto !important;
        bottom: 0;
        z-index: 999;
        /* A flat 1px border read as just "more page," not a distinct always-on
           analytical layer over the workspace. Layering a thin accent gradient
           (blending the four persona colors the chat badges already use) on top of
           the solid background reads as its own thing without needing a heavier
           treatment — and unlike a pseudo-element, a background-image layer isn't at
           risk of being clipped by this element's own overflow-y: auto below. */
        background: linear-gradient(90deg, #16a34a, #d4a017, #8b5cf6, #b91c1c) top / 100% 2px no-repeat, #16171a;
        border-top: 1px solid #2a2b2e;
        padding: 10px 24px 18px;
        /* max-height wasn't in here, so switching collapsed/partial/full tiers just
           snapped the dock to its new size instantly — jarring for what's supposed to
           read as a bottom sheet sliding open, the same interaction the Sleeper app
           itself animates. */
        transition: left 0.2s ease, max-height 0.25s ease;
        box-shadow: 0 -4px 16px rgba(0,0,0,0.45);
        /* The "full" tier's content can exceed a short viewport's height — without a
           cap, a position:fixed/bottom:0 element just grows upward past the top of the
           screen (unlike normal flow, nothing pushes back), taking the collapse button
           with it and leaving no way to reach it. Confirmed live: it became unclickable,
           hidden above y=0, under the browser-chrome toolbar. Capping height and letting
           the dock scroll internally keeps every control reachable regardless of tier
           or viewport size. */
        max-height: 94vh;
        overflow-y: auto;
    }
    /* position:fixed ignores the sidebar entirely (it's relative to the viewport, not
       the document flow) — left:0 above would span full width including underneath
       the sidebar, which then paints over the dock's left edge and hides whatever
       text happens to land there. Only start the dock after the sidebar's actual
       rendered width, tracking its expanded/collapsed state via :has(). */
    body:has([data-testid="stSidebar"][aria-expanded="true"]) .st-key-debate_dock { left: 400px; }
    body:has([data-testid="stSidebar"][aria-expanded="false"]) .st-key-debate_dock { left: 0; }


    /* Delete confirmations are the one genuinely irreversible action in the sidebar —
       give them a visibly different (red-leaning) treatment instead of the same
       neutral gray as every other button, so "Confirm Delete" doesn't blend in with
       "Sync Leagues" a few pixels away. Streamlit has no built-in danger button type,
       so this targets the key-derived class directly; the key varies per league id,
       hence the attribute-substring match rather than an exact class name. */
    [class*="st-key-confirm_del_"] button {
        border-color: #b91c1c !important;
        color: #f87171 !important;
    }
    [class*="st-key-confirm_del_"] button:hover {
        background: rgba(185,28,28,0.12) !important;
    }
    [class*="st-key-del_"] button:hover {
        border-color: #b91c1c !important;
        color: #f87171 !important;
    }

    /* Every transition/animation added above respects a system-level "please don't
       move things" preference instead of overriding it -- motion is a nice-to-have
       polish, not something to force on someone who's told their OS they don't want it. */
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            transition-duration: 0.001ms !important;
            animation-duration: 0.001ms !important;
        }
    }

    /* This was only ever tuned against a laptop-width viewport. Confirmed live at
       phone width (390px): the hero title wrapped to 3 lines at full desktop size,
       eating most of the screen before any real content. clamp() scales it down
       smoothly with viewport width instead of a hard breakpoint jump. */
    [data-testid="stMainBlockContainer"] h1 {
        font-size: clamp(1.5rem, 4vw + 0.6rem, 2.5rem);
    }

    /* Confirmed live at tablet width (820px): the sidebar stays persistent (unlike
       phone width, where Streamlit collapses it), leaving columns narrow enough that
       button labels wrapped ugly onto 2-3 lines -- "Refresh" as "Re/fre/sh". Tap
       targets stay at the full 44px min-height (mobile is exactly where that matters
       most); only the font/padding shrink to fit the label on one line. */
    @media (max-width: 900px) {
        .stButton button, .stFormSubmitButton button, .stDownloadButton button {
            font-size: 0.82rem;
            padding: 8px 8px;
        }
    }
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
    "activity_log": [],  # persistent record of one-shot events (sync, upload, delete, ...) -- see notify()
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


def append_message(role: str, content: str, provider: Optional[str] = None, model: Optional[str] = None) -> None:
    # `provider`/`model` (which actually answered) are stamped on the message itself,
    # not derived from live bot_config at render time -- a role can be reassigned to a
    # different provider or model later, and an old message must keep showing who/what
    # actually answered it, not whatever's currently configured.
    msg = {"role": role, "content": content, "ts": time.time()}
    if provider:
        msg["provider"] = provider
    if model:
        msg["model"] = model
    st.session_state.chat_history.append(msg)
    if st.session_state.selected_league_id:
        save_chat_history(st.session_state.selected_league_id, st.session_state.chat_history)


def process_moderator_output(moderator_text: str, trigger_question: str) -> None:
    """Shared post-processing for any Moderator response that might carry the structured
    verdict block -- both a fresh debate and a lighter follow-up (see
    llm_engine.ask_moderator_followup) can produce one. No-ops cleanly on plain conversational
    text: parse_moderator_verdict returns {} for that, and every consumer below is already a
    safe no-op on an empty/falsy input, so a "just talking it through" follow-up doesn't spam
    the decision log or to-do list with nothing."""
    verdict = llm_engine.parse_moderator_verdict(moderator_text) if not moderator_text.startswith("⚠️") else {}
    decision_log.log_decision(st.session_state.selected_league_id, trigger_question, verdict, moderator_text)
    action_item = verdict.get("action_item")
    if action_item:
        todo_log.add_todo(
            st.session_state.selected_league_id, action_item, source="moderator", question=trigger_question,
        )
    directives = llm_engine.parse_todo_directives(moderator_text)
    for update in directives["updates"]:
        todo_log.revise_todo(st.session_state.selected_league_id, update["id"], update["text"], update["reason"])
    for proposal in directives["likely_resolved"]:
        todo_log.mark_likely_resolved(st.session_state.selected_league_id, proposal["id"], proposal["reason"])
    # See MODERATOR_SYSTEM_PROMPT's own SOURCE FINDING instructions: only written when the
    # whole panel (Contrarian included) didn't dispute it, so persisting every parsed line here
    # is trusting the Moderator's own gate, not re-verifying it a second time in code -- the
    # actual trust bar is upstream, in the debate itself.
    for finding in llm_engine.parse_source_findings(moderator_text):
        bot_research.add_finding(
            finding["player_name"], finding["source"], finding["claim"], rank=finding["rank"],
            conviction=verdict.get("conviction", ""), question=trigger_question,
            league_id=st.session_state.selected_league_id,
        )
    # Same trust posture as SOURCE FINDING above -- a relative claim between two players, kept
    # in its own structured store (never the composite's inputs) since it carries no absolute
    # number. See bot_research.py's own docstring on why and when that could eventually change.
    for comparison in llm_engine.parse_source_comparisons(moderator_text):
        bot_research.add_comparison(
            comparison["subject"], comparison["compared_to"], comparison["direction"], comparison["source"],
            context=comparison["context"], evidence=comparison["evidence"], question=trigger_question,
            league_id=st.session_state.selected_league_id,
        )
    # "Referenced" is a lighter signal than an actual UPDATE/LIKELY RESOLVED directive -- just
    # the Moderator citing an objective by id (e.g. "per #3, ...") while reasoning about
    # something else. Regex over the active ids rather than another LLM directive, since this
    # is purely a UI hint, not something that should shape the model's own output format.
    mentioned_ids = {int(n) for n in re.findall(r"#(\d+)", moderator_text)}
    for active_item in todo_log.load_todos(st.session_state.selected_league_id, statuses=todo_log.ACTIVE_STATUSES):
        if active_item["id"] in mentioned_ids:
            todo_log.mark_referenced(st.session_state.selected_league_id, active_item["id"])


def find_last_debate(chat_history: list[dict]) -> Optional[dict[str, str]]:
    """The most recent Full Debate round's four reports, if any -- lets a follow-up talk to
    the Moderator with something real to reference instead of answering blind. A Full Debate
    always appends exactly [quant, beat, contrarian, moderator] back to back (see the trigger
    block below), so that exact role run is the signature to scan for, most recent first."""
    for i in range(len(chat_history) - 4, -1, -1):
        if [chat_history[i + k]["role"] for k in range(4)] == ["quant", "beat", "contrarian", "moderator"]:
            return {
                "quant": chat_history[i]["content"], "beat": chat_history[i + 1]["content"],
                "contrarian": chat_history[i + 2]["content"], "moderator": chat_history[i + 3]["content"],
            }
    return None


ACTIVITY_LOG_MAX = 50


def notify(level: str, text: str) -> None:
    """Show the normal one-shot st.success/warning/error/info toast AND persist it to the
    sidebar's Activity Log, since the toast itself vanishes on the very next rerun -- anyone
    who glanced away for a second (or triggered another action right after) otherwise has no
    way to see what an upload, sync, or delete actually did. Only call this for a genuine
    one-shot event (something just happened), never for a persistent conditional warning that
    would re-render -- and re-log -- on every single rerun while some ongoing state is true.
    """
    getattr(st, level)(text)
    st.session_state.setdefault("activity_log", [])
    st.session_state.activity_log.insert(0, {"ts": time.time(), "level": level, "text": text})
    del st.session_state.activity_log[ACTIVITY_LOG_MAX:]


def api_key_for(provider: str) -> Optional[str]:
    """The session's own pasted/uploaded key for this provider, if any, else None (meaning
    "fall back to whatever llm_engine already loaded from .env")."""
    return st.session_state.get(f"{provider}_api_key_override") or None


# bot_config's short provider ids ("claude") vs. api_key_for's credential-field names
# ("anthropic") -- two different vocabularies that predate each other, kept apart
# rather than unified since api_key_for's names mirror the .env vars directly.
PROVIDER_KEY_FIELD = {"claude": "anthropic", "gemini": "gemini", "openai": "openai"}
IS_PROVIDER_CONFIGURED = {
    "claude": llm_engine.is_claude_configured,
    "gemini": llm_engine.is_gemini_configured,
    "openai": llm_engine.is_openai_configured,
}


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
    st.session_state.chat_scoped_attachments = []
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


SLOT_SORT_ORDER = {"Starter": 0, "Bench": 1, "TAXI": 2, "IR": 3}
INJURY_OK_STATUSES = ("Questionable", "Doubtful")

# Free Agents position filter: ordered the way a manager actually scans a roster
# (offense skill positions first, then the flex-style umbrella options, then
# kicker/D-ST, then IDP broken out individually with its own umbrella last).
# `None` means "no positions to intersect" i.e. the unfiltered "All" option.
FA_POSITION_FILTERS = [
    ("All", None),
    ("QB", {"QB"}), ("WR", {"WR"}), ("RB", {"RB"}), ("TE", {"TE"}),
    ("FLEX", {"WR", "RB", "TE"}), ("SUPERFLEX", {"QB", "WR", "RB", "TE"}),
    ("K", {"K"}), ("D/ST", {"DEF"}),
    ("DL", {"DL"}), ("LB", {"LB"}), ("DB", {"DB"}), ("IDP", {"DL", "LB", "DB"}),
]

TABLE_COLUMN_LABELS = {
    "name": "Player", "position": "Pos", "team": "Team", "slot": "Slot",
    "tier": "Tier", "vorp": "VORP", "projection": "Proj", "sleeper_proj": "Sleeper Proj",
    "proj_3yr": "3yr Proj", "trade_value": "Trade Val", "pos_rank": "Pos Rank",
    "fa_ros_proj": "ROS Proj", "fa_ceiling": "Ceiling", "fa_value": "3D Value+",
    "injury_status": "Status", "search_rank": "Sleeper Rank",
    # The Sleeper-canonical free agent table prefixes every Draft Sharks enrichment
    # field with ds_ (see the fa_rows build below) so it never collides with the
    # native Sleeper fields on the same row — these are the display labels for those.
    "ds_rank": "DS Rank", "ds_fa_rank": "FA Rank", "ds_projection": "DS Proj", "ds_trade_value": "DS Trade Val",
    "ds_proj_3d": "DS 3D Proj", "ds_ros_3d": "DS ROS Proj", "ds_ceiling": "DS Ceiling",
    "ds_value_3d": "DS 3D Value+",
}


def sleeper_proj_label(snapshot: dict) -> str:
    """Column label for Sleeper's native weekly projection, naming the actual week.

    A static "Sleeper Proj" doesn't say what it's projecting or for when — and the
    week it reflects isn't always "this week" (during preseason it falls back to
    regular week 1, see sleeper_client.sync_league), so it has to be computed from
    the snapshot's own resolved projection_request, not hardcoded.
    """
    req = snapshot.get("projection_request") or snapshot.get("nfl_state") or {}
    return f"Wk{req.get('week', '?')} Proj"


def _injury_pill_color(val: str) -> tuple[str, str]:
    if val in INJURY_OK_STATUSES:
        return ("rgba(212,160,23,0.18)", "#facc15")
    return ("rgba(185,28,28,0.18)", "#f87171")  # Out/IR/PUP/etc.


# Position was rendering as plain gray text in every table — every row required reading
# to find what you were looking for, where a color-coded badge lets it register at a
# glance instead. Not a copy of Sleeper's own QB/RB/WR color mapping (their choices
# aren't inherently "correct," just one reference point) — chosen instead to stay clear
# of hues this app already uses to MEAN something. Gold and crimson are the injury pills
# (Questionable/Out), and a Questionable TE would otherwise show a gold position pill
# right next to a gold injury pill in the same row, saying two different things with the
# same color. Persona colors (green/gold/purple/red) are chat badges, a different
# context, but avoided anyway for a fully distinct set.
_POSITION_PILL_COLORS = {
    "QB": ("rgba(129,140,248,0.18)", "#818cf8"),   # indigo
    "RB": ("rgba(45,212,191,0.18)", "#2dd4bf"),    # teal
    "WR": ("rgba(56,189,248,0.18)", "#38bdf8"),    # sky blue
    "TE": ("rgba(251,146,60,0.18)", "#fb923c"),    # orange
    "K": ("rgba(148,163,184,0.18)", "#94a3b8"),    # neutral gray
    "DEF": ("rgba(244,114,182,0.18)", "#f472b6"),  # pink
    "DST": ("rgba(244,114,182,0.18)", "#f472b6"),
}


def _position_pill_color(val: str) -> tuple[str, str]:
    return _POSITION_PILL_COLORS.get(val, ("rgba(148,163,184,0.18)", "#94a3b8"))


def render_styled_table(
    df: pd.DataFrame, pill_columns: Optional[dict] = None, group_column: Optional[str] = None,
    render_header: bool = True, column_labels: Optional[dict] = None,
) -> None:
    """Render a DataFrame as a custom HTML table instead of the native st.dataframe grid.

    st.dataframe renders through a canvas-based grid component — it's fundamentally a
    flat spreadsheet look, and page CSS/fonts don't reach into it at all (confirmed by
    inspecting the live DOM). This trades the native grid's column-sort/cell-selection
    for full control over typography, spacing, and per-column pill badges, matching the
    rest of the app's visual language instead of looking like a bare data dump.

    `pill_columns` maps a column name to a `value -> (background, text_color)` function;
    any other column just renders as text, right-aligned with tabular numerals if numeric.

    `column_labels` overrides/extends TABLE_COLUMN_LABELS for this call only — for a
    label that depends on runtime state (e.g. "sleeper_proj" meaning a specific,
    currently-resolved week, not a fixed name every session).

    `render_header=False` skips the built-in `<th>` row entirely — for a caller that
    renders its own clickable sort-header row (real Streamlit buttons, since static
    HTML can't call back into Python) directly above this table instead.

    `group_column`, if given, must already be sorted (this never reorders rows) — a
    full-width section header row is inserted every time that column's value changes,
    and the column itself is dropped from display since the header now conveys it (e.g.
    grouping the roster by "slot" into Starters/Bench/TAXI/IR sections, Sleeper-style,
    instead of one flat list with a slot pill on every row).
    """
    if df.empty:
        return
    pill_columns = pill_columns or {}
    labels = {**TABLE_COLUMN_LABELS, **(column_labels or {})}
    display_cols = [c for c in df.columns if c != group_column] if group_column else list(df.columns)
    numeric_cols = {c for c in display_cols if pd.api.types.is_numeric_dtype(df[c])}

    def _cell_html(col: str, val) -> str:
        if pd.isna(val) or val in (None, ""):
            return '<span style="color:#4b5563;">—</span>'
        if col in pill_columns:
            bg, color = pill_columns[col](val)
            text = html.escape(str(val))
            return (
                f'<span style="display:inline-block;background:{bg};color:{color};'
                f'padding:2px 10px;border-radius:999px;font-size:0.78rem;font-weight:600;'
                f'white-space:nowrap;">{text}</span>'
            )
        text = html.escape(f"{val:.1f}" if isinstance(val, float) else str(val))
        if col == "name":
            return f'<span style="font-weight:600;white-space:nowrap;">{text}</span>'
        if col in ("position", "team"):
            return f'<span style="color:#9ca3af;">{text}</span>'
        if col in numeric_cols:
            return f'<span style="font-variant-numeric: tabular-nums;">{text}</span>'
        return text

    headers = "".join(
        f'<th style="text-align:left;padding:9px 14px;font-size:0.7rem;text-transform:uppercase;'
        f'letter-spacing:0.07em;color:#8b8f98;font-weight:600;border-bottom:1px solid #2a2b2e;'
        f'background:#1b1c1f;white-space:nowrap;">'
        f'{html.escape(labels.get(c, c.replace("_", " ").title()))}</th>'
        for c in display_cols
    ) if render_header else ""

    row_parts = []
    last_group = object()  # sentinel that can never equal a real group value
    for _, row in df.iterrows():
        if group_column:
            group_val = row[group_column]
            if group_val != last_group:
                row_parts.append(
                    f'<tr><td colspan="{len(display_cols)}" style="padding:10px 14px 5px;'
                    f'font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;'
                    f'color:#6b7280;font-weight:700;background:#141517;'
                    f'border-top:1px solid #2a2b2e;">'
                    f'{html.escape(str(group_val))}</td></tr>'
                )
                last_group = group_val
        cells = "".join(f'<td style="padding:9px 14px;border-bottom:1px solid #202124;">{_cell_html(c, row[c])}</td>' for c in display_cols)
        row_parts.append(f"<tr>{cells}</tr>")

    # The conditional thead has to stay on the same line as <table ...> — a
    # standalone blank line here (which is what render_header=False produces,
    # since the whitespace-only line has no visible content) terminates
    # CommonMark's raw-HTML-block parsing early, and everything after gets
    # re-parsed as an indented code block instead of rendered HTML.
    thead_html = f"<thead><tr>{headers}</tr></thead>" if render_header else ""
    st.markdown(
        f"""
        <div style="overflow-x:auto;overflow-y:auto;max-height:600px;
                    border:1px solid #2a2b2e;border-radius:10px;">
          <table style="width:100%;border-collapse:collapse;font-size:0.88rem;">{thead_html}
            <tbody>{''.join(row_parts)}</tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sort_rows_by_column(rows: list[dict], col: str, direction: str) -> list[dict]:
    """Sort dicts by one column, clicked-header style — missing values always last.

    A row missing this column entirely means "unknown," not "worst value," so it
    shouldn't get shoved to one end on ascending and the other on descending —
    it sorts after every row that actually has a value, regardless of direction.
    """
    present = [r for r in rows if r.get(col) not in (None, "")]
    missing = [r for r in rows if r.get(col) in (None, "")]
    numeric = all(isinstance(r.get(col), (int, float)) for r in present) if present else True
    key = (lambda r: r[col]) if numeric else (lambda r: str(r[col]).lower())
    present.sort(key=key, reverse=(direction == "desc"))
    missing.sort(key=lambda r: r.get("name", "").lower())
    return present + missing


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
    (never the shared global rankings pool), chat history + compaction backups, decisions,
    objectives, pinned messages, its format override, and any attachment scoped exclusively
    to it (one scoped to this league among others just has this league_id dropped from its
    scope, not deleted).

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
    todo_log.forget_todos(league_id)
    pinned_messages.forget_pins(league_id)

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


def roster_owner_names(snapshot: dict) -> dict[int, str]:
    """roster_id -> display name, for resolving Sleeper's traded-picks data (which speaks in
    roster_id, not names or user_id directly)."""
    user_names = {
        str(u.get("user_id")): u.get("display_name") or (u.get("metadata") or {}).get("team_name")
        for u in (snapshot.get("users") or [])
    }
    return {
        r.get("roster_id"): user_names.get(str(r.get("owner_id"))) or f"Roster {r.get('roster_id', '?')}"
        for r in (snapshot.get("rosters") or [])
    }


def build_pick_ledger(snapshot: dict) -> dict[int, dict[str, list[dict]]]:
    """roster_id -> {"acquired": [...], "given_away": [...]}, built only from Sleeper's own
    traded_picks (the authoritative source for who owns what -- Draft Sharks' own pick imports
    can be unreliable, per direct report). Sleeper only lists a pick here once it's actually
    moved from its original roster; an untouched pick is assumed to still belong to its
    original roster and isn't worth listing, so this ledger is deliberately just the diffs,
    not a full inventory of every hypothetical future pick."""
    ledger: dict[int, dict[str, list[dict]]] = {}
    for pick in snapshot.get("traded_picks") or []:
        original, current = pick.get("roster_id"), pick.get("owner_id")
        if original is None or current is None or original == current:
            continue
        ledger.setdefault(current, {"acquired": [], "given_away": []})["acquired"].append(pick)
        ledger.setdefault(original, {"acquired": [], "given_away": []})["given_away"].append(pick)
    return ledger


def positional_depth(player_universe: list[dict], merger: DataMerger) -> dict[str, dict[str, dict]]:
    """team -> position -> {"count": n, "value": sum or None}.

    Count alone treats a pile of backups the same as three stacked stars at the same
    position -- real depth is about quality, not just bodies. `value` sums each
    player's Draft Sharks trade_value (Dynasty Rankings) where a match exists, so a
    QB room with Mahomes/Dak/Lamar reads very differently from three replacement-level
    arms even though both are "3 QBs." Only computed when merger.is_loaded -- with no
    Draft Sharks data at all, value stays None for every cell and callers fall back to
    count alone, per this app's usual "work with whatever is loaded" rule.
    """
    depth: dict[str, dict[str, dict]] = {}
    for row in player_universe:
        if row.get("ownership") != "ROSTERED":
            continue
        team_label = row.get("owner_name") or f"Roster {row.get('roster_id', '?')}"
        position = row["position"]
        cell = depth.setdefault(team_label, {}).setdefault(position, {"count": 0, "value": None})
        cell["count"] += 1
        if merger.is_loaded:
            match = merger.merge_player(row["name"], position=position, team=row.get("team"))
            trade_value = match.get("trade_value")
            if trade_value is not None:
                cell["value"] = (cell["value"] or 0) + trade_value
    return depth


def build_freshness_manifest(snapshot: dict, merger: DataMerger) -> list[tuple[str, Optional[str], Optional[int]]]:
    """(label, as-of date, days old) for every dated source in this context, freshest first."""
    entries = []
    if merger.is_loaded:
        entries.append(("Draft Sharks Dynasty Rankings", merger.freshest_date, merger.staleness_days))
    if merger.is_free_agents_loaded:
        entries.append(("Draft Sharks Free Agent Finder", merger.free_agents_freshest_date, merger.free_agents_staleness_days))
    if merger.is_trade_values_loaded:
        entries.append(("Draft Sharks Trade Value Chart", merger.trade_values_freshest_date, merger.trade_values_staleness_days))
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


# Shown wherever DataMerger.composite_player_score() returns None -- every loaded source
# (Draft Sharks baseline included) was checked and none of them had a usable number for this
# player, so this is a deliberate, honest state, not a blank/missing field to explain away.
# Never a placeholder score -- see composite_player_score's own docstring on not fabricating one.
INCOMPLETE_PLAYER_PROFILE = "Incomplete Player Profile"


def describe_external_value(ext: dict) -> str:
    """One compact 'source/list detail' string for a single DataMerger.external_player_values()
    row. Different sources shape their numbers differently (DynastyProcess: a 1QB/2QB point
    value on its own ~0-10000 scale; KeepTradeCut: a single crowdsourced 0-9999ish value plus
    rank/tier; FantasyPros: rank/tier only, off an expert panel, no point value at all), so
    this picks whichever fields that row actually has rather than assuming one shape -- new
    sources with yet another shape still degrade to *something* readable instead of a blank
    or wrong field lookup."""
    if ext.get("source_name") == "bot_research":
        # A panel-vetted live-search/reference-material finding (see bot_research.py), not a
        # static export -- label by the source it actually cites (e.g. "ESPN"), not the
        # generic bucket name, and carry the claim itself since that's the point of this one.
        cited = ext.get("cited_source") or "?"
        rank_part = f" (rank={ext['rank']:.0f})" if ext.get("rank") is not None else ""
        claim = ext.get("claim")
        return f"{cited} via panel research{rank_part}: {claim}" if claim else f"{cited} via panel research{rank_part}"
    label = ext.get("source_name", "?")
    source_file = ext.get("source_file")
    if source_file:
        label += f"/{Path(source_file).stem}"
    tier = f" tier{ext['tier']:.0f}" if ext.get("tier") is not None else ""
    rank = f" rank={ext['rank']:.0f}" if ext.get("rank") is not None else ""
    if "value_1qb" in ext or "value_2qb" in ext:
        detail = f"1QB={ext.get('value_1qb', '-')}/2QB={ext.get('value_2qb', '-')}"
    elif "value" in ext:
        detail = f"value={ext['value']:.0f}{rank}{tier}"
    elif "rank" in ext:
        detail = f"rank={ext['rank']:.0f}{tier}"
    else:
        detail = "(no comparable number)"
    return f"{label} {detail}"


def build_context(snapshot: dict, roster_table: list[dict], player_universe: list[dict], question: str = "") -> str:
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

    active_todos = todo_log.load_todos(league_id, statuses=todo_log.ACTIVE_STATUSES) if league_id else []
    if active_todos:
        lines.append(
            "\nOPEN TO-DO ITEMS — this league's active objectives, each with a small numeric id. Don't "
            "re-suggest one of these as if it were new; check in on it if the question is related, and use "
            "ACTION ITEM again only for something genuinely new. To revise one when new information changes "
            "it, or to propose it looks done, use TODO UPDATE: / TODO LIKELY RESOLVED: lines as described "
            "in your instructions:"
        )
        for item in active_todos:
            if item["status"] == "likely_resolved":
                proposed = item.get("resolution_reason") or ""
                lines.append(
                    f"  - #{item['id']}: {item['text']} (since {item['date']}) — proposed as likely "
                    f"resolved: {proposed} (awaiting user confirmation)"
                )
            else:
                lines.append(f"  - #{item['id']}: {item['text']} (since {item['date']})")

    relevant_history = todo_log.search_archived(league_id, question, limit=5) if league_id and question else []
    if relevant_history:
        lines.append(
            "\nRELEVANT PAST OBJECTIVES — resolved/dismissed items that look related to this question. This "
            "is strategic memory: if a similar trade/waiver/roster idea was already explored, use the "
            "resolution note to understand why it ended the way it did, and weigh whether anything material "
            "has changed since before treating this as a brand-new investigation:"
        )
        for item in relevant_history:
            outcome = "Completed" if item["status"] == "resolved" else "Dismissed"
            reason = item.get("resolution_reason") or "(no reason recorded)"
            lines.append(f"  - {item['text']} — {outcome} {item.get('resolution_date', '')}: {reason}")

    past_outcomes = (
        decision_log.search_decisions_with_outcomes(league_id, question, limit=5) if league_id and question else []
    )
    if past_outcomes:
        lines.append(
            "\nPAST DECISION OUTCOMES — earlier verdicts related to this question, with how they actually "
            "played out (user-recorded, not a guess). Weigh whether the panel's read has a track record on "
            "this kind of call before repeating the same reasoning that already worked or already missed:"
        )
        for d in past_outcomes:
            note = f" — {d['outcome_note']}" if d.get("outcome_note") else ""
            lines.append(f"  - \"{d['question']}\" ({d['date']}): called {d['recommendation']}. Outcome: {d['outcome']}{note}")

    # Retrieved only when this question actually seems to relate to one -- never injected by
    # default. Pinning something once and having it silently color every future debate forever
    # would be a real anchoring problem (a stale Quant observation quietly biasing months of
    # later questions about that player); the user pins to keep something findable, not to
    # instruct the panel going forward.
    relevant_pins = (
        pinned_messages.find_relevant(
            st.session_state.chat_history, pinned_messages.load_pinned_ts(league_id), question, limit=5,
        ) if league_id and question else []
    )
    if relevant_pins:
        lines.append(
            "\nPINNED — the user manually flagged these messages as worth keeping handy, and this "
            "question seems to relate to at least one. Reference it if it's actually useful, but "
            "pinning doesn't mean elevated priority — weigh it like anything else here, not as a "
            "standing instruction or a settled conclusion:"
        )
        for pm in relevant_pins:
            lines.append(f"  - [{pm.get('role', '?')}] {pm.get('content', '')[:400]}")

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
    lines.append(
        f"  - Draft Sharks Trade Value Chart (rookie pick slot values, future pick values, player values): "
        f"{'loaded' if merger.is_trade_values_loaded else 'NOT LOADED — if a question needs a specific pick or player price, say so and suggest uploading it (Tools > Trade Value Chart on draftsharks.com)'}"
    )
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
        projection_request = snapshot.get("projection_request") or snapshot.get("nfl_state") or {}
        lines.append(
            f"\nSleeper's own native {projection_request.get('season_type', 'regular')}-season week-"
            f"{projection_request.get('week', '?')} stat-category projections are also "
            "included below as 'sleeper_proj', scored under this league's real scoring_settings. NOTE: this "
            "is a SINGLE-WEEK number, not a season or 3-year total like Draft Sharks' — don't compare them "
            "at face value without accounting for that timeframe difference. Treat it as a second independent "
            "quantitative source to weigh against Draft Sharks, not a tiebreaker by default."
        )
    # "DS" = Draft Sharks throughout. A trailing "other sources" column, where present, is
    # never Draft Sharks and never blended into the DS figures beside it -- same posture as
    # Sleeper's own native projection above (a second independent read to weigh, not a
    # tiebreaker by default) -- so Draft Sharks isn't the only word on a player's value here.
    lines.append(
        "Roster (name | pos | team | DS tier | DS VORP | DS 1yr proj | Sleeper native week proj | "
        "DS 3yr proj | DS 3D/trade value | DS pos rank | composite score | other sources):"
    )
    for row in roster_table:
        other = "; ".join(describe_external_value(ext) for ext in row.get("external_values") or [])
        composite = row.get("composite")
        composite_str = (
            f"{composite['score']:.0f}/100 ({composite['recency_grade']})" if composite else INCOMPLETE_PLAYER_PROFILE
        )
        lines.append(
            f"  {row['name']} | {row['position']} | {row['team']} | "
            f"{row.get('tier', '-')} | {row.get('vorp', '-')} | {row.get('projection', '-')} | "
            f"{row.get('sleeper_proj', '-')} | {row.get('proj_3yr', '-')} | "
            f"{row.get('trade_value', '-')} | {row.get('pos_rank', '-')} | {composite_str} | {other or '-'}"
        )
    if any(row.get("composite") for row in roster_table):
        lines.append(
            "  'composite score' is this app's own single blended read across every loaded "
            "source (see COMPOSITE_SOURCE_WEIGHTS in data_merger.py: Draft Sharks weighted a "
            "bit higher, KeepTradeCut a bit lower as a crowd-vote average, fresher-dated "
            "sources counting for more) -- a starting-point number for convenience, never a "
            "substitute for weighing the actual per-source disagreement in 'other sources' below."
        )
    if merger.is_external_values_loaded:
        lines.append(
            "  'other sources' are each on their OWN scale, none of them Draft Sharks' 0-100 and "
            "none directly comparable to each other either: DynastyProcess (1QB/2QB) runs "
            "roughly 0-10000, a documented formula off FantasyPros' expert consensus rankings; "
            "FantasyPros itself (rank/tier) is that same panel's raw overall rank and tier, not "
            "a point value at all -- and its dynasty_ppr_rankings list is dynasty, its "
            "best_ball_rankings list is a SEASON-LONG/redraft read, not a dynasty valuation, so "
            "never treat that one as a long-term value opinion. Compare RELATIVE standing within "
            "one source's own column, never one source's number against another's directly -- "
            "and note where sources disagree on which of two players is worth more, since that's "
            "more informative than any single number alone."
        )

    # The canonical Sleeper pool is intentionally separate from the optional
    # Draft Sharks free-agent export.  Include player(s) named in the question
    # plus the best currently projected available Sleeper players, so the
    # panel can reason about a waiver target even with no vendor data loaded.
    mentioned = matching_players(player_universe, question)
    available = available_players(player_universe)
    projected_available = sorted(
        (row for row in available if row.get("sleeper_proj") is not None),
        key=lambda row: row["sleeper_proj"], reverse=True,
    )[:15]
    canonical_rows = {row["player_id"]: row for row in mentioned + projected_available}
    if canonical_rows:
        lines.append(
            "\nSleeper canonical player pool (identity and league ownership come from Sleeper; "
            "Draft Sharks fields, if present elsewhere, are optional enrichment; "
            "name | pos | team | ownership | roster slot | native week projection):"
        )
        for row in canonical_rows.values():
            lines.append(
                f"  {row['name']} | {row['position']} | {row['team']} | {row['ownership']} | "
                f"{row.get('roster_slot', '-')} | {row.get('sleeper_proj', 'unavailable')}"
            )

    # Every other team's roster — for trade scouting. Full detail costs real tokens on a
    # 10-14 team league, so only the team(s)/player(s) the question actually names get the
    # full breakdown; everyone else gets a cheap one-line starters summary for ambient
    # awareness of who has what. Ask about a team by name to pull its full roster in.
    own_user_id = st.session_state.get("user_id")

    # League-wide positional depth (every team, including yours) -- computed straight from
    # Sleeper's own roster data, not parsed off Draft Sharks' League Analyzer positional-rank
    # table (that PDF's flat text can't be reliably reattributed to the right team). Gives the
    # Moderator/Contrarian a scarcity signal across the whole league without a separate
    # question per team.
    depth = positional_depth(player_universe, merger)
    if depth:
        has_values = merger.is_loaded
        lines.append(
            "\nLEAGUE-WIDE POSITIONAL DEPTH (per team: rostered player COUNT at each position"
            + (", with total Draft Sharks trade value in parens where matched -- weigh the value "
               "figure over the count: three replacement-level backups and three stacked stars both "
               "read as \"3\" by count alone, but are not remotely the same depth." if has_values else
               " -- no Draft Sharks data loaded, so this is body count only; two teams with the same "
               "count here can still differ hugely in actual talent")
            + "):"
        )
        for team_label, positions in depth.items():
            parts = []
            for pos, cell in sorted(positions.items()):
                value_label = f" ({cell['value']:.0f})" if cell["value"] is not None else ""
                parts.append(f"{pos} {cell['count']}{value_label}")
            lines.append(f"  {team_label}: " + ", ".join(parts))

    rosters_by_owner: dict[str, list[dict]] = {}
    for row in player_universe:
        if row.get("ownership") != "ROSTERED" or row.get("owner_id") == own_user_id:
            continue
        owner_label = row.get("owner_name") or f"Roster {row.get('roster_id', '?')}"
        rosters_by_owner.setdefault(owner_label, []).append(row)
    if rosters_by_owner:
        question_lower = question.lower()
        lines.append(
            "\nLEAGUE ROSTERS — every other team in this league, for trade scouting (Sleeper ownership "
            "data, not Draft-Sharks-enriched). Full roster shown only for a team or player the question "
            "actually names, to control length — everyone else is just their current starters:"
        )
        for owner_label, rows in rosters_by_owner.items():
            named = owner_label.lower() in question_lower or any(r["name"].lower() in question_lower for r in rows)
            if named:
                lines.append(f"  {owner_label} (full roster):")
                for r in rows:
                    lines.append(f"    {r['name']} | {r['position']} | {r['team']} | {r.get('roster_slot', '-')}")
            else:
                starters = [r["name"] for r in rows if r.get("roster_slot") == "Starter"]
                lines.append(f"  {owner_label}: {', '.join(starters) or '(no starters set)'}")

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

    if merger.is_trade_values_loaded:
        tv = merger.trade_values
        rookie_slots = tv[tv["asset_type"] == "rookie_pick_slot"]
        future_picks = tv[tv["asset_type"] == "future_pick"]
        if not rookie_slots.empty or not future_picks.empty:
            lines.append(
                "\nPICK VALUES per Draft Sharks' Trade Value Chart — same 0-100 scale as player trade "
                "value above, so a pick and a player are directly comparable. A rookie pick slot's own "
                "value already reflects how strong this year's incoming rookie class is judged to be "
                "(no separate class-grade source exists or is needed). This is PRICE ONLY — which team "
                "actually owns a given future pick comes from Sleeper's own traded-picks data elsewhere "
                "in this context, never from Draft Sharks, whose pick-ownership imports can be unreliable."
            )
            # The chart's own title states which format toggle was active when it was exported
            # (e.g. "Dynasty PPR") -- flag it plainly when that doesn't match this league rather
            # than let a Non-PPR chart's numbers pass as this league's Full-PPR values. It never
            # states 1QB vs Superflex at all, so that gap always gets called out, unconditionally.
            source_league_type = tv["source_league_type"].iloc[0] if "source_league_type" in tv.columns else None
            source_scoring = tv["source_scoring"].iloc[0] if "source_scoring" in tv.columns else None
            mismatches = []
            if source_league_type and source_league_type != fmt["type"]:
                mismatches.append(f"exported for {source_league_type}, this league is {fmt['type']}")
            if source_scoring:
                def _canon_scoring(s: str) -> str:
                    s = s.lower()
                    if "half" in s:
                        return "half_ppr"
                    if "non-ppr" in s or "non ppr" in s or "standard" in s:
                        return "standard"
                    if "ppr" in s:
                        return "full_ppr"
                    return s.strip()
                if _canon_scoring(source_scoring) != _canon_scoring(fmt["scoring"]):
                    mismatches.append(f"exported for {source_scoring} scoring, this league is {fmt['scoring']}")
            caveat = (
                f" MISMATCH — {'; '.join(mismatches)}: don't treat these as exact, but they're still useful "
                "as relative/directional value (who's worth more than whom) even off-format." if mismatches
                else ""
            )
            lines.append(
                f"  Format: {source_league_type or 'unknown'} {source_scoring or ''}. The file never states "
                f"1QB vs Superflex (this league is {'Superflex' if fmt['superflex'] else '1QB'}), which "
                "materially moves QB and pick value, so weigh that unverified gap regardless."
                + caveat
            )
            if not rookie_slots.empty:
                lines.append(
                    "  This year's rookie draft slots: "
                    + ", ".join(f"{r['name']}={r['value']}" for r in rookie_slots.to_dict("records"))
                )
            if not future_picks.empty:
                lines.append(
                    "  Future picks (generic, by round/year): "
                    + ", ".join(f"{r['name']}={r['value']}" for r in future_picks.to_dict("records"))
                )

    # Ownership is Sleeper's to say, independent of whether Draft Sharks' price list above is
    # even loaded -- a pick that's changed hands matters to a trade question either way, priced
    # or not. Only picks that have actually moved appear (see build_pick_ledger's own docstring).
    pick_ledger = build_pick_ledger(snapshot)
    if pick_ledger:
        owner_names = roster_owner_names(snapshot)
        lines.append(
            "\nTRADED PICK OWNERSHIP per Sleeper (authoritative on who holds what -- an untraded "
            "pick is still just its original roster's normal Nth-round pick and isn't listed here). "
            "Value in parens, where shown, is Draft Sharks' generic price for that round/year from "
            "PICK VALUES above, if loaded:"
        )
        for roster_id, moves in sorted(pick_ledger.items(), key=lambda kv: owner_names.get(kv[0], "")):
            acquired = moves["acquired"]
            if not acquired:
                continue
            parts = []
            for p in acquired:
                label = f"{p.get('season')} Rd {p.get('round')}"
                original_owner = owner_names.get(p.get("roster_id"), f"Roster {p.get('roster_id')}")
                value = merger.pick_value(f"{p.get('season')} Random Rd {p.get('round')}") if merger.is_trade_values_loaded else None
                parts.append(f"{label} (originally {original_owner}'s{f', valued {value}' if value is not None else ''})")
            lines.append(f"  {owner_names.get(roster_id, f'Roster {roster_id}')} holds via trade: " + "; ".join(parts))

    captioned = [a for a in list_attachments(league_id=st.session_state.selected_league_id) if a["caption"].strip()]
    if captioned:
        lines.append(
            "\nREFERENCE MATERIAL the user uploaded (screenshots/articles, captioned by hand — you're only "
            "given the caption text, not the actual file, so treat it as a claim to weigh, not verified fact):"
        )
        for a in captioned[:20]:
            lines.append(f"  - {a['caption']}")

    findings = bot_research.findings_for_context()
    if findings:
        lines.append(
            "\nPANEL-VETTED FINDINGS from past debates (see MODERATOR_SYSTEM_PROMPT's SOURCE FINDING rule — "
            "each already survived scrutiny from the whole panel, Contrarian included, when it was first "
            "surfaced, whether that was a bot's live search or the user's own reference material). The ones "
            "with a rank number already feed the composite score above at a low weight (this is still an "
            "LLM's own read, not a deterministic parser's) — don't double-count them by also treating this "
            "prose as independent corroboration. Newer findings on the same player supersede older ones:"
        )
        for f in findings:
            rank_part = f" (rank {f['rank']})" if f.get("rank") is not None else ""
            lines.append(f"  - [{f['date']}] {f['player_name']} — {f['source']}{rank_part}: {f['claim']}")

    comparisons = bot_research.comparisons_for_context()
    if comparisons:
        lines.append(
            "\nPANEL-VETTED PLAYER COMPARISONS from past debates (see MODERATOR_SYSTEM_PROMPT's SOURCE "
            "COMPARISON rule). A relative claim only — which of two players a source rates higher, never by "
            "how much or where either lands on any scale — so these carry NO composite weight at all and "
            "never will unless enough of them accumulate to support a real relative-valuation model later "
            "(not attempted yet). Useful as a cross-check on ordering against the numeric composite above, "
            "not a competing number:"
        )
        for c in comparisons:
            verb = {">": "rated ahead of", "<": "rated behind", "~": "rated about even with"}[c["direction"]]
            ctx = f" [{c['context']}]" if c.get("context") else ""
            lines.append(
                f"  - [{c['date']}] {c['subject']} {verb} {c['compared_to']}{ctx}, per {c['source']}: {c['evidence']}"
            )

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
            notify("error", f"Couldn't reach Sleeper: {exc}")
        else:
            st.caption("Couldn't restore your last session automatically — click Sync Leagues to retry.")
        return False

    if not user:
        if announce:
            notify("error", f"No Sleeper user found for '{username}'")
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
            notify("error", f"Found your Sleeper account, but couldn't fetch its leagues: {exc}")
        return False
    fresh_ids = {lg["league_id"] for lg in st.session_state.leagues}
    newly_left = previously_tracked - fresh_ids
    if newly_left:
        st.session_state.left_league_ids = sorted(newly_left)

    if announce:
        if not st.session_state.leagues:
            notify("warning", "No leagues found for this user in the current season.")
        else:
            notify("success", f"Found {len(st.session_state.leagues)} league(s).")
    return True


with st.sidebar:
    # First thing in the sidebar, not buried behind config sections -- the whole point is
    # that a sync/upload/delete result should be checkable after the one-shot toast that
    # announced it has already scrolled away on a later rerun.
    with st.expander(f"🔔 Activity Log ({len(st.session_state.activity_log)})", expanded=False, key="sb_group_activity"):
        st.caption(
            "Every sync, upload, save, and delete this session, newest first — stays here "
            "after the toast that announced it is gone."
        )
        if not st.session_state.activity_log:
            st.caption("Nothing yet.")
        else:
            _activity_icon = {"success": "✅", "warning": "⚠️", "error": "🛑", "info": "ℹ️"}
            with st.container(height=min(320, 44 * len(st.session_state.activity_log) + 8)):
                for entry in st.session_state.activity_log:
                    _at = datetime.fromtimestamp(entry["ts"]).strftime("%H:%M:%S")
                    st.caption(f"{_activity_icon.get(entry['level'], '•')} {_at} — {entry['text']}")
            if st.button("Clear log", key="clear_activity_log", use_container_width=True):
                st.session_state.activity_log = []
                st.rerun()

    with st.expander("🔑 Connections & Models", expanded=False, key="sb_group_connections"):
        st.caption(
            "Paste your keys in .env format (or upload a .txt/.env/.pdf with them), then click "
            "Apply. This writes them into your local .env automatically, so it's a one-time step — "
            "not something typed in every session."
        )
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
                notify("warning", "Didn't recognize any keys or a username in that — check the format and try again.")
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
                notify("success", f"Applied: {', '.join(found)}.")
                st.rerun()

        st.markdown("**Available Models**")
        st.caption(
            "What each configured provider can actually call right now — the canonical list "
            "that 🤖 Roles & Routing (including its benchmark) reads from. Fetch it once here; "
            "nothing downstream fetches its own separate copy."
        )
        _conn_configured = [p for p in bot_config.PROVIDERS if IS_PROVIDER_CONFIGURED[p](api_key_for(PROVIDER_KEY_FIELD[p]))]
        if not _conn_configured:
            st.caption("No provider keys configured yet — paste at least one above.")
        else:
            if st.button("🔄 Refresh available models for every configured provider", key="conn_refresh_models", use_container_width=True):
                for _p in _conn_configured:
                    _ids, _err = llm_engine.LIST_MODELS_BY_PROVIDER[_p](api_key_for(PROVIDER_KEY_FIELD[_p]))
                    if _err:
                        notify("warning", f"Couldn't fetch {bot_config.PROVIDER_LABELS[_p]} models: {_err}")
                    else:
                        st.session_state[f"available_models_{_p}"] = sorted(_ids)
                st.rerun()
            for _p in _conn_configured:
                _models = st.session_state.get(f"available_models_{_p}")
                if _models:
                    st.caption(f"**{bot_config.PROVIDER_LABELS[_p]}** — {len(_models)} model(s): {', '.join(_models)}")
                else:
                    st.caption(f"{bot_config.PROVIDER_LABELS[_p]}: not fetched yet.")

        st.markdown("**Sleeper Username**")
        username_input = st.text_input(
            "Sleeper Username", value=st.session_state.username, label_visibility="collapsed"
        )
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
                notify("success", f"Deleted local data for {league_name}.")
                st.rerun()
            if lc3.button("Keep as-is", key=f"leftleague_dismiss_{lid}"):
                st.session_state.left_league_ids.remove(lid)
                st.rerun()

    with st.expander("🤖 Roles & Routing", expanded=False, key="sb_group_bots"):
        st.caption(
            "Which provider actually answers for each role, and what to call it. Any provider can "
            "technically fill any role — a role is just a system prompt plus which prior reports it "
            "reacts to — so the defaults below are a starting point tuned to each provider's own "
            "strengths, not a requirement. Point every role at one key if that's all you have. Each "
            "role also has an optional benchmark: let candidate models actually audition for the job "
            "instead of picking one by reputation."
        )
        _role_providers_cfg = bot_config.load_role_providers()
        _role_names_cfg = bot_config.load_role_names()
        _role_models_cfg = bot_config.load_role_models()
        _moderator_personality_cfg = bot_config.load_moderator_personality()
        _provider_options = list(bot_config.PROVIDERS)
        # Discovery itself lives in 🔑 Connections & Models now -- this section only reads
        # the `available_models_{provider}` cache it populates, the same single source both
        # the manual model picker below and every role's benchmark candidate list draw from.
        _bots_configured = [p for p in bot_config.PROVIDERS if IS_PROVIDER_CONFIGURED[p](api_key_for(PROVIDER_KEY_FIELD[p]))]
        if not _bots_configured:
            st.warning("No provider keys configured yet — add at least one in 🔑 Connections & Models first.")
        elif not any(st.session_state.get(f"available_models_{p}") for p in _bots_configured):
            st.caption("No models fetched yet — use 🔑 Connections & Models above to see what each key can call.")

        for _role in bot_config.ROLES:
            _info = bot_config.ROLE_INFO[_role]
            _toggle_key = f"show_bot_config_{_role}"
            st.session_state.setdefault(_toggle_key, False)
            _summary = f"{'▾' if st.session_state[_toggle_key] else '▸'} {_info['label']}"
            if st.button(_summary, key=f"toggle_bot_{_role}", use_container_width=True):
                st.session_state[_toggle_key] = not st.session_state[_toggle_key]
                st.rerun()
            # Always visible, even collapsed -- "what's actually running this role" is
            # the one fact worth surfacing without a click, per Provider • Model.
            _subtitle_model = _role_models_cfg[_role] or "(provider default)"
            st.caption(f"{bot_config.PROVIDER_LABELS[_role_providers_cfg[_role]]} • {_subtitle_model}")
            if st.session_state[_toggle_key]:
                st.caption("ROLE / DESCRIPTION")
                st.caption(_info["description"])
                # Visible labels, not collapsed -- a text box next to a dropdown read as
                # two similar-looking controls with no cue for which does what. "DISPLAY
                # NAME" vs "MODEL PROVIDER" makes the role/provider split self-explanatory
                # instead of something you have to already understand the architecture to read.
                st.caption("DISPLAY NAME")
                _name_input = st.text_input(
                    "Display name", value=_role_names_cfg[_role], key=f"bot_name_input_{_role}",
                    label_visibility="collapsed",
                )
                st.caption("MODEL PROVIDER")
                _current_provider = _role_providers_cfg[_role]
                _provider_choice = st.selectbox(
                    "Provider", options=_provider_options, index=_provider_options.index(_current_provider),
                    format_func=lambda p: bot_config.PROVIDER_LABELS[p], key=f"bot_provider_input_{_role}",
                    label_visibility="collapsed",
                )
                _recommended = _info["recommended"]
                # The "why" always shows now, matched or not -- "recommended fit" alone
                # was a dead end; the reasoning is what actually helps someone decide
                # whether to override it, so it shouldn't disappear the moment they agree.
                _rec_prefix = "✓ Using the recommended provider" if _provider_choice == _recommended else f"Recommended: {bot_config.PROVIDER_LABELS[_recommended]}"
                st.caption(f"{_rec_prefix} — {_info['why']}")
                # Model is a layer below provider, not a peer to it -- two roles can share
                # a provider and still want different models (the Moderator's synthesis
                # doesn't need the same model as Quant's number-crunching). Free text by
                # default (not a locked dropdown -- hardcoding a catalog here is exactly
                # how the old CLAUDE_MODEL default ended up pointing at a retired
                # snapshot); the shared "Refresh available models" button above offers a
                # real picker built from whatever that key can actually call. Blank means
                # "no override, use this provider's own default."
                st.caption(f"MODEL (optional — e.g. {', '.join(bot_config.SUGGESTED_MODELS[_provider_choice])})")
                _fetched = st.session_state.get(f"available_models_{_provider_choice}")
                _current_model = _role_models_cfg[_role]
                if _fetched:
                    _options = ["(provider default)"] + [m for m in _fetched if m]
                    if _current_model and _current_model not in _options:
                        _options.append(_current_model)
                    _default_idx = _options.index(_current_model) if _current_model in _options else 0
                    _model_choice = st.selectbox(
                        "Model", options=_options, index=_default_idx, key=f"bot_model_select_{_role}",
                        label_visibility="collapsed",
                    )
                    _model_input = "" if _model_choice == "(provider default)" else _model_choice
                else:
                    _model_input = st.text_input(
                        "Model", value=_current_model, key=f"bot_model_input_{_role}",
                        label_visibility="collapsed", placeholder="Leave blank to use the provider's default",
                    )
                # Scoped to the Moderator only -- the debate view now leads with its synthesis
                # by default, so it's the one voice the user actually reads most of the time.
                # The other three roles' prompts are deliberately narrow (Quant: "no news, no
                # opinions, just the math") and a tone knob would fight that narrowness.
                if _role == "moderator":
                    st.caption("RESPONSE PERSONALITY")
                    _personality_options = ["(default tone)"] + list(bot_config.MODERATOR_PERSONALITIES)
                    _personality_index = (
                        _personality_options.index(_moderator_personality_cfg)
                        if _moderator_personality_cfg in _personality_options else 0
                    )
                    _personality_choice = st.selectbox(
                        "Response personality", options=_personality_options, index=_personality_index,
                        key="bot_personality_input_moderator", label_visibility="collapsed",
                    )
                    if _personality_choice != "(default tone)":
                        st.caption(bot_config.MODERATOR_PERSONALITIES[_personality_choice])
                else:
                    _personality_choice = None
                if st.button("Save", key=f"bot_save_{_role}", use_container_width=True):
                    if _name_input.strip() and _name_input.strip() != _role_names_cfg[_role]:
                        bot_config.set_role_name(_role, _name_input)
                    if _provider_choice != _current_provider:
                        bot_config.set_role_provider(_role, _provider_choice)
                    if _model_input.strip() != _role_models_cfg[_role]:
                        bot_config.set_role_model(_role, _model_input)
                    if _role == "moderator":
                        _new_personality = "" if _personality_choice == "(default tone)" else _personality_choice
                        if _new_personality != _moderator_personality_cfg:
                            bot_config.set_moderator_personality(_new_personality)
                    st.rerun()

                # Benchmarking lives inside the same card as the manual controls it can
                # override, one more toggle-button deep -- Streamlit can't nest a real
                # st.expander inside this one, and it belongs here rather than as a
                # separate top-level section since it writes to the exact same two
                # settings (provider, model) the fields above do.
                _bench_toggle_key = f"show_bench_{_role}"
                st.session_state.setdefault(_bench_toggle_key, False)
                if st.button(
                    f"{'▾' if st.session_state[_bench_toggle_key] else '▸'} 🧪 Benchmark this role",
                    key=f"toggle_bench_{_role}", use_container_width=True,
                ):
                    st.session_state[_bench_toggle_key] = not st.session_state[_bench_toggle_key]
                    st.rerun()
                if st.session_state[_bench_toggle_key]:
                    st.caption(
                        "Runs every model you select through the same fixed scenario battery for "
                        "this role, then a judge call scores each answer blind to which model "
                        "produced it. Real, billed API calls — nothing runs until you press Run."
                    )
                    if not _bots_configured:
                        st.caption("No provider keys configured yet.")
                    else:
                        _bench_candidates: list[tuple[str, str]] = []
                        for _p in _bots_configured:
                            _p_fetched = st.session_state.get(f"available_models_{_p}")
                            if not _p_fetched:
                                st.caption(f"{bot_config.PROVIDER_LABELS[_p]}: no models fetched yet — use Refresh above.")
                                continue
                            st.caption(f"{bot_config.PROVIDER_LABELS[_p]} candidates")
                            _chosen = st.multiselect(
                                f"{bot_config.PROVIDER_LABELS[_p]} models", options=_p_fetched, default=_p_fetched,
                                key=f"bench_models_{_role}_{_p}", label_visibility="collapsed",
                            )
                            _bench_candidates.extend((_p, m) for m in _chosen)

                        _judge_options = _bots_configured
                        _judge_default = _judge_options.index("claude") if "claude" in _judge_options else 0
                        _judge_provider = st.selectbox(
                            "Judge (scores every answer, blind to which model produced it)",
                            options=_judge_options, index=_judge_default,
                            format_func=lambda p: bot_config.PROVIDER_LABELS[p], key=f"bench_judge_{_role}",
                        )

                        if st.button(
                            f"▶ Run Benchmark ({len(_bench_candidates)} model(s) × {len(bot_benchmark.BENCHMARK_BATTERY[_role])} scenarios)",
                            key=f"bench_run_{_role}", type="primary", use_container_width=True,
                            disabled=len(_bench_candidates) < 1,
                        ):
                            _bench_api_keys = {p: api_key_for(PROVIDER_KEY_FIELD[p]) for p in bot_config.PROVIDERS}
                            _progress = st.empty()
                            with st.spinner("Running benchmark — this calls every selected model and then a judge model per answer…"):
                                _report = bot_benchmark.run_benchmark(
                                    _role, _bench_candidates, _bench_api_keys,
                                    judge_provider=_judge_provider, judge_api_key=_bench_api_keys.get(_judge_provider),
                                    on_progress=lambda msg: _progress.caption(msg),
                                )
                            _progress.empty()
                            bot_benchmark.save_report(_role, _report)
                            notify("success", f"Benchmark complete for {_info['label']}.")
                            st.rerun()

                    _bench_report = bot_benchmark.load_report(_role)
                    if _bench_report:
                        _ran_at = datetime.fromtimestamp(_bench_report["ran_at"]).strftime("%Y-%m-%d %H:%M")
                        _judge_label = bot_config.PROVIDER_LABELS.get(_bench_report.get("judge_provider"), _bench_report.get("judge_provider", "?"))
                        st.caption(f"Last run {_ran_at} · judged by {_judge_label}")
                        _medals = ["🥇", "🥈", "🥉"]
                        for _idx, _cand in enumerate(_bench_report["candidates"]):
                            _medal = _medals[_idx] if _idx < len(_medals) else f"{_idx + 1}."
                            _model_label = _cand["model"] or "(provider default)"
                            _warn = " ⚠️ one or more calls failed" if _cand["any_failed"] else ""
                            st.caption(
                                f"{_medal} {bot_config.PROVIDER_LABELS[_cand['provider']]} · {_model_label} — "
                                f"**{_cand['score']}**/100, {_cand['avg_latency']}s avg{_warn}"
                            )
                            if _idx == 0 and st.button(
                                f"Apply {_model_label} to {_info['label']}",
                                key=f"bench_apply_{_role}_{_idx}", use_container_width=True,
                            ):
                                bot_config.set_role_provider(_role, _cand["provider"])
                                bot_config.set_role_model(_role, _cand["model"])
                                notify("success", f"Applied — {_info['label']} now runs on {_model_label}.")
                                st.rerun()

                st.markdown("<hr style='margin:6px 0;opacity:0.15'>", unsafe_allow_html=True)
        # Three separate resets, not one combined "reset everything" -- provider
        # routing, display names, and model overrides are independent settings, so
        # someone who just wants the recommended routing back shouldn't lose a custom
        # name like "Freddy" or a deliberately-picked model as a side effect of that.
        reset_provider_col, reset_name_col, reset_model_col = st.columns(3)
        if reset_provider_col.button("Use recommended providers", key="reset_bot_providers", use_container_width=True):
            bot_config.reset_role_providers()
            st.rerun()
        if reset_model_col.button("Clear model overrides", key="reset_bot_models", use_container_width=True):
            bot_config.reset_role_models()
            st.rerun()
        if reset_name_col.button("Reset display names", key="reset_bot_names", use_container_width=True):
            bot_config.reset_role_names()
            st.rerun()

    with st.expander("📊 Data Uploads", expanded=False, key="sb_group_uploads"):
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
            notify("warning", "Select at least one league above, or switch back to Global.")
        elif submitted and uploaded is None:
            notify("warning", "Choose a file before clicking Upload.")
        elif submitted and uploaded is not None:
            data = bytes(uploaded.getbuffer())
            note = note.strip()
            suffix = Path(uploaded.name).suffix.lower()
            recognized = False
            note_scope = scope_league_ids if scope_mode == "Specific league(s)" else None

            if suffix in (".pdf", ".csv", ".json"):
                import pypdf

                staging_dir = PROJECTIONS_DIR / "_staging"
                staging_dir.mkdir(parents=True, exist_ok=True)
                staging_path = staging_dir / uploaded.name
                staging_path.write_bytes(data)
                parse_error = None
                parsed_df = None
                try:
                    parsed_df, kind = load_projection_file(staging_path)
                except Exception as exc:
                    kind, parse_error = None, str(exc)

                # A PDF that parses cleanly as "rankings" (the default/catch-all bucket -- see
                # _sniff_pdf_kind) might still not actually BE Dynasty Rankings; that bucket has
                # no positive-match check of its own, just elimination of the other three known
                # tools. Draft Sharks' own PDFs plainly self-label DYNASTY vs REDRAFT in their
                # title text (confirmed against a real "Redraft > IDP" export that parsed
                # without error yet silently mislabeled two columns) -- catching that here is
                # cheap (local text, no API call) and catches exactly the case a keyword-based
                # sniff can't: a real table, just the wrong dynasty-vs-redraft product.
                suspicious_excerpt = None
                example_row = None
                if kind == "rankings" and suffix == ".pdf":
                    try:
                        first_page = pypdf.PdfReader(str(staging_path)).pages[0].extract_text() or ""
                    except Exception:
                        first_page = ""
                    upper = first_page.upper()
                    if "REDRAFT" in upper and "DYNASTY" not in upper:
                        suspicious_excerpt = first_page[:1500]
                        # A concrete row from the parser's OWN output, not anything the Moderator
                        # is asked to restate from memory -- the numbers stay exactly what the
                        # deterministic parser already extracted; only their labeling is ever in
                        # question, so this is what actually gets shown/confirmed, not an LLM's
                        # potentially-misremembered echo of them.
                        if parsed_df is not None and not parsed_df.empty:
                            _ex = parsed_df.iloc[0]
                            example_row = (
                                f"{_ex.get('name', '?')} ({_ex.get('team', '?')} {_ex.get('position', '?')}): "
                                f"parsed as rank={_ex.get('rank')}, \"1yr projection\"={_ex.get('projection')}, "
                                f"\"3yr projection\"={_ex.get('proj_3yr')}, trade_value={_ex.get('trade_value')}"
                            )

                if kind == "free_agents" and not st.session_state.selected_league_id:
                    staging_path.unlink(missing_ok=True)
                    notify("error", "This looks like a Free Agent Finder export, tied to one league's roster — select a league above first, then re-upload.")
                    recognized = True  # handled (as a rejection), don't also file it as an attachment
                elif suspicious_excerpt:
                    # The parser flagged real, recoverable data as ambiguous -- try to self-heal
                    # via the Moderator automatically, before ever bothering the user with it.
                    # Optically, whether the fix came from the parser alone or with the
                    # Moderator's help doesn't matter -- only that the right data lands and the
                    # user isn't interrupted for something the app could sort out on its own.
                    _mod_provider = bot_config.load_role_providers()["moderator"]
                    _mod_key = api_key_for(PROVIDER_KEY_FIELD[_mod_provider])
                    auto_opinion, auto_alignment = None, None
                    if IS_PROVIDER_CONFIGURED[_mod_provider](_mod_key):
                        with st.spinner("Parser flagged this file as ambiguous — checking with the Moderator..."):
                            auto_opinion = llm_engine.classify_unknown_upload(
                                uploaded.name, suspicious_excerpt, example_row=example_row, provider=_mod_provider,
                                api_key=_mod_key, model=bot_config.load_role_models().get("moderator") or None,
                            )
                        auto_alignment = llm_engine.parse_alignment_verdict(auto_opinion)

                    if auto_alignment is True:
                        # False alarm -- the parser's own mapping actually held up. Proceed
                        # exactly like any other recognized upload; the question's resolved.
                        dest_dir = GLOBAL_PROJECTIONS_DIR
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        staging_path.replace(dest_dir / uploaded.name)
                        st.session_state.data_merger.reload()
                        notify("success", "Recognized as Draft Sharks data — the Moderator double-checked an ambiguous label and it held up.")
                        recognized = True
                        if note:
                            save_attachment(f"{uploaded.name}.note.txt", note.encode(), caption=note, league_ids=note_scope)
                    elif auto_alignment is False:
                        # Confirmed mislabeled. Drop only the specific fields whose meaning is in
                        # question (never invent a replacement value for them) and keep what's
                        # still valid -- identity fields and trade_value, which for a Trade Value
                        # Chart / Dynasty Rankings PDF sits in the same column position either
                        # way. Written out as a CSV, not the raw PDF, so a future reload parses
                        # the already-corrected data directly instead of re-deriving the same
                        # wrong labels from the PDF's raw text every time.
                        corrected_cols = [c for c in ("name", "team", "position", "rank", "trade_value") if c in parsed_df.columns]
                        corrected_name = Path(uploaded.name).stem + ".corrected.csv"
                        dest_dir = GLOBAL_PROJECTIONS_DIR
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        parsed_df[corrected_cols].to_csv(dest_dir / corrected_name, index=False)
                        staging_path.unlink(missing_ok=True)
                        st.session_state.data_merger.reload()
                        notify(
                            "success",
                            "Recognized as Draft Sharks data, with the Moderator's help — this file's own "
                            "projection columns didn't mean what our schema expected (it looks like a "
                            "single-season export, not a dynasty one), so those were left out rather than "
                            "shown under the wrong label. Its trade value still applies.",
                        )
                        recognized = True
                        if note:
                            save_attachment(f"{uploaded.name}.note.txt", note.encode(), caption=note, league_ids=note_scope)
                    else:
                        # Couldn't self-heal -- no key configured to even ask, or the Moderator
                        # itself wasn't confident. This is the one case that actually needs a
                        # human decision, not a second automated guess dressed up as one.
                        st.session_state.pending_upload = {
                            "staging_path": str(staging_path), "name": uploaded.name, "kind": kind,
                            "parse_error": None, "excerpt": suspicious_excerpt, "data": data,
                            "note": note, "note_scope": note_scope,
                            "moderator_opinion": auto_opinion, "alignment": auto_alignment,
                            "example_row": example_row,
                        }
                        recognized = True  # held for a decision below, not silently filed either way
                elif parse_error:
                    # Nothing usable parsed at all -- no data to align, so there's nothing for
                    # the Moderator to fix here. Falls through to reference material below,
                    # same as it always has.
                    staging_path.unlink(missing_ok=True)
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
                    notify("success", f"Recognized as Draft Sharks data — saved to {location_label}.")
                    recognized = True
                    if note:
                        # The data went into the projections pool, not the attachment store — but the
                        # note is still worth surfacing to the panel, so it gets a small text-only entry.
                        save_attachment(f"{uploaded.name}.note.txt", note.encode(), caption=note, league_ids=note_scope)

            if not recognized:
                save_attachment(uploaded.name, data, caption=note, league_ids=note_scope)
                notify("info", f"Didn't match a known Draft Sharks format — saved '{uploaded.name}' as reference material below for the panel to consider when you ask about it.")

        pending = st.session_state.get("pending_upload")
        if pending:
            # This is only ever reached once self-healing has already been tried and failed (see
            # above) -- either no Moderator key was configured to even attempt it, or the
            # Moderator itself wasn't confident either way. Either way, this genuinely needs a
            # human call, not another automated guess.
            st.warning(
                f"⚠️ \"{pending['name']}\" parsed as table data, but its own text says \"Redraft\" "
                "rather than \"Dynasty\", which would give the wrong signal if silently merged "
                "into dynasty rankings — and "
                + ("the Moderator wasn't confident either way." if pending["moderator_opinion"]
                   else "no Moderator API key is configured to check it automatically.")
                + " Decide below."
            )
            if pending.get("example_row"):
                # Deterministic -- the parser's own actual output, not anything the Moderator is
                # trusted to restate. Shown up front, no API call needed to see it.
                st.caption(f"Example of how it's currently being parsed: {pending['example_row']}")
            if pending["moderator_opinion"]:
                # The trailing ALIGNMENT line is a machine-readable suffix for
                # parse_alignment_verdict, not part of what a human should read as prose --
                # stripped here for display only; the stored/parsed text is untouched.
                _opinion_lines = pending["moderator_opinion"].strip().splitlines()
                if _opinion_lines and _opinion_lines[-1].strip().upper() in ("ALIGNMENT: CORRECT", "ALIGNMENT: WRONG"):
                    _opinion_lines = _opinion_lines[:-1]
                st.info(f"**Moderator:** {chr(10).join(_opinion_lines).strip()}")
                if pending.get("alignment") is True:
                    st.caption("✅ The Moderator thinks this labeling looks right for this document.")
                elif pending.get("alignment") is False:
                    st.caption("❌ The Moderator thinks this labeling is wrong for this document.")
            # Button wording stays fixed and neutral regardless of what the Moderator said --
            # NOT relabeled to echo its verdict ("Yes, that's right"). A parser that silently
            # mislabels a column and a Moderator opinion that gets rubber-stamped without real
            # scrutiny fail the same way: nothing catches the error. The point of holding this
            # for a human decision is a genuinely independent judgment call, weighed against the
            # deterministic example row above -- not a second automated opinion the first one's
            # own suggested button text talks the user into agreeing with.
            import_label = "Import as Dynasty Rankings anyway"
            reference_label = "Save as reference material instead"
            ask_label = "🤔 Ask the Moderator again" if pending["moderator_opinion"] else "🤔 Ask the Moderator"
            pu_cols = st.columns(3)
            with pu_cols[0]:
                if st.button(ask_label, key="pending_upload_ask", use_container_width=True):
                    _pu_provider = bot_config.load_role_providers()["moderator"]
                    _pu_model = bot_config.load_role_models().get("moderator") or None
                    _pu_key = api_key_for(PROVIDER_KEY_FIELD[_pu_provider])
                    if not IS_PROVIDER_CONFIGURED[_pu_provider](_pu_key):
                        notify("error", f"No API key configured for {bot_config.PROVIDER_LABELS[_pu_provider]} (the Moderator's current provider) — add one under Connections & Models.")
                    else:
                        with st.spinner("Asking the Moderator..."):
                            opinion = llm_engine.classify_unknown_upload(
                                pending["name"], pending["excerpt"], example_row=pending.get("example_row"),
                                provider=_pu_provider, api_key=_pu_key, model=_pu_model,
                            )
                        pending["moderator_opinion"] = opinion
                        pending["alignment"] = llm_engine.parse_alignment_verdict(opinion)
                        st.rerun()
            with pu_cols[1]:
                if st.button(import_label, key="pending_upload_import", use_container_width=True):
                    dest_dir = GLOBAL_PROJECTIONS_DIR
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    Path(pending["staging_path"]).replace(dest_dir / pending["name"])
                    st.session_state.data_merger.reload()
                    if pending["note"]:
                        save_attachment(f"{pending['name']}.note.txt", pending["note"].encode(), caption=pending["note"], league_ids=pending["note_scope"])
                    notify("success", f"Saved \"{pending['name']}\" to the shared Dynasty Rankings pool.")
                    st.session_state.pending_upload = None
                    st.rerun()
            with pu_cols[-1]:
                if st.button(reference_label, key="pending_upload_reference", use_container_width=True):
                    Path(pending["staging_path"]).unlink(missing_ok=True)
                    save_attachment(pending["name"], pending["data"], caption=pending["note"], league_ids=pending["note_scope"])
                    notify("info", f"Saved \"{pending['name']}\" as reference material for the panel to consider when asked about it.")
                    st.session_state.pending_upload = None
                    st.rerun()

        global_files = sorted(p.name for p in GLOBAL_PROJECTIONS_DIR.glob("*") if p.suffix in (".csv", ".json", ".pdf"))
        if global_files:
            st.caption("Shared rankings (any league): " + ", ".join(global_files))
        if st.session_state.selected_league_id:
            league_proj_dir = league_projections_dir(st.session_state.selected_league_id)
            league_files = sorted(p.name for p in league_proj_dir.glob("*") if p.suffix in (".csv", ".json", ".pdf")) if league_proj_dir.exists() else []
            if league_files:
                st.caption("This league only (roster-specific): " + ", ".join(league_files))

    if st.session_state.leagues:
        with st.expander("⚙️ League Controls", expanded=False, key="sb_group_league"):
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

            # This list (name + 4 buttons, repeated per league) was the bulk of what made
            # "League Controls" feel cluttered — every visit surfaced a full wall of
            # reorder/archive/delete buttons for a task that's actually rare (most visits
            # are just checking or switching leagues, handled above and by the main-panel
            # switcher). Tucking it behind its own toggle, collapsed by default, means
            # opening League Controls for the common case doesn't dump the whole list.
            st.session_state.setdefault("show_manage_leagues", False)
            toggle_label = (
                f"{'▾' if st.session_state.show_manage_leagues else '▸'} "
                f"Manage league list ({len(st.session_state.leagues)})"
            )
            if st.button(toggle_label, key="toggle_manage_leagues", use_container_width=True):
                st.session_state.show_manage_leagues = not st.session_state.show_manage_leagues
                st.rerun()

            if st.session_state.show_manage_leagues:
                st.caption(
                    "Archive leagues you don't want on the front dashboard, or reorder them. Delete "
                    "permanently purges all locally cached data for a league (snapshots, its own Draft "
                    "Sharks uploads, chat history) — it doesn't leave the Sleeper league itself, so if "
                    "you're still a member it'll just reappear fresh next time you sync."
                )
                # Smaller/lighter than the app's default 44px bold buttons — these four
                # are frequent-but-minor list-management actions, not primary calls to
                # action, and at full weight per league they were most of the clutter.
                with st.container(key="manage_leagues_list"):
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
                            st.rerun()
                        if up_col.button("▲", key=f"up_{lid}", disabled=idx == 0, help="Move up", use_container_width=True):
                            move_league(st.session_state.user_id, st.session_state.leagues, lid, -1)
                            st.rerun()
                        if down_col.button(
                            "▼", key=f"down_{lid}", disabled=idx == len(ordered) - 1, help="Move down",
                            use_container_width=True,
                        ):
                            move_league(st.session_state.user_id, st.session_state.leagues, lid, 1)
                            st.rerun()

                        if st.session_state.get("pending_delete_league_id") == lid:
                            if del_col.button("Cancel", key=f"cancel_del_{lid}", use_container_width=True):
                                st.session_state.pending_delete_league_id = None
                                st.rerun()
                        elif del_col.button("🗑️", key=f"del_{lid}", help="Delete permanently", use_container_width=True):
                            st.session_state.pending_delete_league_id = lid
                            st.rerun()

                        if st.session_state.get("pending_delete_league_id") == lid:
                            st.warning(
                                f"Permanently delete all local data for **{lg['name']}**? This can't be undone "
                                "(no in-app undo — only whatever backups your OS/filesystem might keep)."
                            )
                            if st.button("Confirm Delete", key=f"confirm_del_{lid}", use_container_width=True):
                                removed = delete_league_completely(lid)
                                st.session_state.pending_delete_league_id = None
                                notify("success", f"Deleted local data for {lg['name']} ({len(removed)} item(s) removed).")
                                st.rerun()
                        st.markdown("<hr style='margin:6px 0;opacity:0.15'>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Status")
    def status_line(label: str, ok: bool) -> str:
        # ❌ is an intrinsically red emoji glyph — CSS `color` can't retint it, so
        # "not loaded yet" (routine, most of these are optional) always read as a
        # stack of alarms regardless of the muted .status-bad text color next to it.
        # A plain circle actually respects the class's color.
        icon = "✅" if ok else "○"
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
    projection_request = (snap.get("projection_request") or snap.get("nfl_state") or {}) if snap else {}
    proj_week = projection_request.get("week")
    proj_type = projection_request.get("season_type", "regular")
    proj_label = f"Sleeper Native Projections ({proj_type} week {proj_week})" if has_sleeper_proj else "Sleeper Native Projections"
    st.markdown(status_line(proj_label, has_sleeper_proj), unsafe_allow_html=True)
    if snap and not has_sleeper_proj:
        st.caption("Unofficial endpoint returned nothing this sync — Draft Sharks/market data still work fine without it.")
    # Which roles say "(Quant/Moderator)" etc. next to a provider's name isn't fixed
    # anymore -- it depends on the current Configure Bots assignment, not a hardcoded
    # persona list.
    _role_providers_for_status = bot_config.load_role_providers()
    _role_names_for_status = bot_config.load_role_names()
    _roles_using = {
        provider: [
            _role_names_for_status[role] for role in bot_config.ROLES if _role_providers_for_status[role] == provider
        ]
        for provider in bot_config.PROVIDERS
    }
    st.markdown(
        status_line(f"Claude ({'/'.join(_roles_using['claude']) or 'unassigned'}) Connected", llm_engine.is_claude_configured(api_key_for("anthropic"))),
        unsafe_allow_html=True,
    )
    st.markdown(
        status_line(f"Gemini ({'/'.join(_roles_using['gemini']) or 'unassigned'}) Connected", llm_engine.is_gemini_configured(api_key_for("gemini"))),
        unsafe_allow_html=True,
    )
    st.markdown(
        status_line(f"ChatGPT ({'/'.join(_roles_using['openai']) or 'unassigned'}) Connected", llm_engine.is_openai_configured(api_key_for("openai"))),
        unsafe_allow_html=True,
    )

    missing_keys = [
        (var, provider) for var, provider, ok in (
            ("ANTHROPIC_API_KEY", "claude", llm_engine.is_claude_configured(api_key_for("anthropic"))),
            ("GEMINI_API_KEY", "gemini", llm_engine.is_gemini_configured(api_key_for("gemini"))),
            ("OPENAI_API_KEY", "openai", llm_engine.is_openai_configured(api_key_for("openai"))),
        ) if not ok and _roles_using[provider]
    ]
    if missing_keys:
        affected = ", ".join(f"{var} (needed for {'/'.join(_roles_using[provider])})" for var, provider in missing_keys)
        st.caption(
            f"Missing: {affected}. Paste them into 🔑 Connections & Models above, or copy "
            "`.env.example` to `.env` in the project folder, fill in the key(s), and restart `streamlit run app.py`."
        )

# ------------------------------------------------------------------ main ----

# The league switcher itself lives here, front and center, rather than buried in the
# sidebar — this is the one control most likely to get used every single visit. A
# popover instead of always-visible pills: with more than a handful of leagues, a
# segmented control wraps into a multi-row wall of buttons every visit whether you're
# switching or not — the popover collapses that down to one button showing the
# current league, opened only when you actually want to switch.
if st.session_state.leagues:
    visible_leagues, archived_leagues = sorted_leagues(st.session_state.user_id, st.session_state.leagues)
    league_options = {lg["league_id"]: lg["name"] for lg in visible_leagues}
    if league_options:
        option_ids = list(league_options.keys())
        current = st.session_state.selected_league_id
        if current not in option_ids:
            current = option_ids[0]

        with st.container(key="league_switcher_row"):
            switch_col, refresh_col = st.columns([5, 1])
            with switch_col:
                # No leading icon — a folder glyph read as "open a folder," not "this is
                # the league you're looking at." The name plus the popover's own chevron
                # already reads as a picker on its own, the way a real <select> does.
                with st.popover(league_options[current], use_container_width=True):
                    st.caption("Switch which league the dashboard and debate panel below are showing.")
                    picked = st.radio(
                        "Switch to",
                        options=option_ids,
                        format_func=lambda lid: league_options[lid],
                        index=option_ids.index(current),
                        label_visibility="collapsed",
                    )
            if picked != st.session_state.selected_league_id:
                activate_league(picked)
                st.rerun()
            with refresh_col:
                # Deliberately understated (see the .st-key-league_switcher_row rule
                # above) — Refresh is a secondary maintenance action next to the primary
                # league picker, not a peer to it, and the icon was only repeating what
                # the word already said.
                if st.button(
                    "Refresh", use_container_width=True,
                    help="Re-pull this league's rosters/scoring/taxi/traded picks from Sleeper.",
                ):
                    client: SleeperClient = st.session_state.sleeper_client
                    try:
                        with st.spinner("Syncing..."):
                            st.session_state.league_snapshot = client.sync_league(picked, client.get_players())
                        notify("success", "League synced.")
                    except SleeperAPIError as exc:
                        notify("error", f"Couldn't reach Sleeper: {exc}")

snapshot = st.session_state.league_snapshot
if not snapshot:
    st.title("Fantasy Football Command Center")
    st.info("Sync a Sleeper username and select a league in the sidebar to get started.")
    st.stop()

# The active league's own name carries the page title once one is loaded — it's the
# single most important thing to make obvious, since the sidebar list can otherwise
# make it unclear which league is actually being viewed. The brand eyebrow above it
# keeps the platform's own identity visible in the same spot regardless of which
# league that is, rather than the league fully taking over the header.
league = snapshot["league"]
fmt = league_format_summary(league)
_banner_uri = _header_banner_data_uri()
if _banner_uri:
    # A second, narrower <style> block layered on top of the base .st-key-app_header
    # rule above rather than folded into it -- the image is only available once this
    # data URI is computed, so the two-layer background (gradient + art) has to be
    # conditional on that, while the flat fallback color from the base rule always
    # applies underneath it either way.
    st.markdown(
        f"<style>.st-key-app_header {{ background-image: "
        f"linear-gradient(90deg, rgba(11,13,18,0.94) 0%, rgba(11,13,18,0.75) 32%, "
        f"rgba(11,13,18,0.25) 62%, rgba(11,13,18,0.05) 100%), url('{_banner_uri}'); }}</style>",
        unsafe_allow_html=True,
    )
with st.container(key="app_header"):
    st.markdown('<div class="brand-eyebrow">🏈 Fantasy Football Command Center</div>', unsafe_allow_html=True)
    st.title(fmt["name"])
    st.caption(
        f"{fmt['type']} · {fmt['teams']}-team · "
        f"{'Superflex' if fmt['superflex'] else '1QB'} · {fmt['scoring']} · Taxi: {fmt['taxi_slots']}"
    )

if st.session_state.data_merger.is_stale:
    days = st.session_state.data_merger.staleness_days
    st.warning(
        f"Draft Sharks projections are {days} days old. They don't need refreshing every session — "
        "roughly once a week keeps the Quant analysis current — but it's been a while.",
        icon="⚠️",
    )

MATCHUP_VIEW = "🏈 Matchup"
MAINTENANCE_VIEW = "🔧 Roster Maintenance"
LEAGUE_VIEW = "👥 League"
main_view = st.segmented_control(
    "Dashboard view",
    options=[MATCHUP_VIEW, MAINTENANCE_VIEW, LEAGUE_VIEW],
    default=MATCHUP_VIEW,
    key="main_view",
    label_visibility="collapsed",
    help="Matchup: your lineup, projections, and the debate studio for start/sit calls. "
    "Roster Maintenance: free agents/waivers and reference material for trade and pickup research. "
    "League: every other team's roster, for trade scouting.",
)
st.markdown("---")

# Build this from Sleeper on every render, regardless of whether the user has
# uploaded Draft Sharks data.  The client serves its daily cached /players/nfl
# copy here, so this is a local join rather than another network request.
players_db = st.session_state.sleeper_client.get_players()
player_universe = build_player_universe(
    players_db,
    snapshot.get("rosters") or [],
    users=snapshot.get("users") or [],
    projections=snapshot.get("projections") or {},
    scoring_settings=league.get("scoring_settings") or {},
)

roster = find_roster_for_user(snapshot["rosters"], st.session_state.user_id) if st.session_state.user_id else None
merger: DataMerger = st.session_state.data_merger
roster_table: list[dict] = []
if roster:
    all_ids = roster.get("players") or []
    starters_list = roster.get("starters") or []  # order matters: Sleeper returns this
    # in actual lineup-slot order (QB, RB, RB, WR, ... FLEX, IDP slots, etc.) — keep the
    # list around for sorting, not just a set, or that order is thrown away.
    starters = set(starters_list)
    starters_order = {pid: i for i, pid in enumerate(starters_list)}
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

    # Starters first (who's actually playing), then bench, then taxi/IR (stashed away).
    # Within Starters, use Sleeper's own lineup-slot order (QB, RB, RB, WR, ... FLEX,
    # IDP slots) rather than whatever incidental order build_roster_table produced —
    # a stable sort, so Bench/TAXI/IR keep their original relative order untouched.
    roster_table.sort(
        key=lambda r: (SLOT_SORT_ORDER.get(r["slot"], 99), starters_order.get(r["player_id"], 0))
    )

# roster_table is built unconditionally above (regardless of which tab is active) —
# the persistent Debate Studio band below needs it too, not just the Matchup view.
if main_view == MATCHUP_VIEW:
    st.subheader("Roster Summary")
    if not roster:
        st.warning("Couldn't find a roster owned by this user in this league.")
    else:
        df = pd.DataFrame(roster_table)
        display_cols = [c for c in [
            "name", "position", "team", "slot", "tier", "vorp",
            "projection", "sleeper_proj", "proj_3yr", "trade_value", "pos_rank",
            "fa_ros_proj", "fa_ceiling", "fa_value", "injury_status",
        ] if c in df.columns]
        render_styled_table(
            df[display_cols],
            pill_columns={"injury_status": _injury_pill_color, "position": _position_pill_color},
            group_column="slot",
            column_labels={"sleeper_proj": sleeper_proj_label(snapshot)},
        )
        if "sleeper_proj" in df.columns:
            projection_request = snapshot.get("projection_request") or snapshot.get("nfl_state") or {}
            st.caption(
                f"'sleeper_proj' = Sleeper's own {projection_request.get('season_type', 'regular')} "
                f"week-{projection_request.get('week', '?')} stat projections, "
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
                            notify("success", f"Mapped '{sel_name}' → '{ds_name_input.strip()}'.")
                            st.rerun()
                        else:
                            notify("error", "Enter the name as Draft Sharks printed it first.")
        else:
            st.caption("No Draft Sharks/War Room projections loaded yet — upload a CSV in the sidebar.")

elif main_view == MAINTENANCE_VIEW:
    # ------------------------------------------------------------------ free agents --

    st.markdown("---")
    st.subheader("Free Agents")

    merger = st.session_state.data_merger

    # A league with no K/DEF/IDP slots has nowhere to start those players — never
    # suggest them at all, regardless of position filter or search.
    league_positions = league_usable_positions(league.get("roster_positions") or [])
    canonical_fa = [row for row in available_players(player_universe) if row["position"] in league_positions]

    fcol1, fcol2 = st.columns([1, 3])
    fa_search = fcol1.text_input("Find a Sleeper player", placeholder="Search by name")
    visible_filters = {
        label: wanted for label, wanted in FA_POSITION_FILTERS
        if wanted is None or wanted & league_positions
    }
    fa_position_filter = fcol1.selectbox("Position", options=list(visible_filters))
    wanted_positions = visible_filters[fa_position_filter]
    if wanted_positions:
        canonical_fa = [row for row in canonical_fa if row["position"] in wanted_positions]
    if fa_search.strip():
        search_term = fa_search.strip().lower()
        canonical_fa = [row for row in canonical_fa if search_term in row["name"].lower()]

    st.caption(
        f"Sleeper canonical pool: {len(canonical_fa)} matching free agents. "
        "Draft Sharks data below is optional enrichment; it never determines whether a player appears."
    )
    if merger.free_agents_is_stale:
        st.warning(
            f"Free Agent Finder data is {merger.free_agents_staleness_days} days old — waiver values shift "
            "week to week more than dynasty rankings do, so this is worth refreshing more often.",
            icon="⚠️",
        )

    # Attach either Draft Sharks source only when it actually has a matching
    # row.  The Sleeper record survives unchanged when neither source does.
    fa_rows = []
    for sleeper_row in canonical_fa:
        row = dict(sleeper_row)
        ranking = merger.merge_player(row["name"], position=row["position"], team=row["team"])
        if ranking.get("matched"):
            for field in ("rank", "projection", "vorp", "tier", "trade_value", "proj_3yr", "pos_rank"):
                if field in ranking:
                    row[f"ds_{field}"] = ranking[field]
        finder = merger.merge_player(row["name"], position=row["position"], team=row["team"], df=merger.free_agents)
        if finder.get("matched"):
            # Free Agent Finder's own rank is a distinct column from Dynasty Rankings'
            # (ds_rank, above) — it's specifically a waiver-relevance rank for this
            # exact pool, so it wins as the ADP-proxy sort key when both are present.
            if "rank" in finder:
                row["ds_fa_rank"] = finder["rank"]
            for field in ("roster_status", "proj_3d", "ros_3d", "ceiling", "value_3d"):
                if field in finder:
                    row[f"ds_{field}"] = finder[field]
        fa_rows.append(row)

    # search_rank stays out of the visible columns on purpose — it's a search-popularity
    # signal (see the sort key below), not a fantasy-relevance one, so surfacing it as a
    # column reads as more authoritative than it actually is. It still drives the silent
    # last-resort tiebreak in the default sort, just never as something to visibly chase.
    fa_display_cols = [c for c in [
        "name", "team", "position", "injury_status",
        "ds_fa_rank", "ds_rank", "sleeper_proj", "ds_ros_3d", "ds_projection", "ds_proj_3d",
        "ds_trade_value", "ds_ceiling", "ds_value_3d",
    ] if any(c in row for row in fa_rows)]

    if "fa_sort" not in st.session_state:
        # Highlight the current week's native Sleeper projection by default — it's
        # the one signal here guaranteed to exist without any Draft Sharks upload,
        # and (usefully) a genuinely retired/off-roster player almost never has a
        # real native projection at all (nothing to project), so this also pushes
        # them toward the bottom on its own even when the retirement heuristic in
        # player_universe.py doesn't catch a specific stale row.
        st.session_state.fa_sort = ("sleeper_proj", "desc") if "sleeper_proj" in fa_display_cols else None
    fa_sort = st.session_state.fa_sort  # (col, "asc"/"desc") — a header click overrides this default
    if fa_sort and fa_sort[0] in fa_display_cols:
        fa_rows = sort_rows_by_column(fa_rows, *fa_sort)
    else:
        # Neither Sleeper nor Draft Sharks expose real ADP, so this uses the closest
        # available proxy: Draft Sharks' own rank for this exact free-agent pool
        # (falling back to its broader Dynasty Rankings rank), then rest-of-season
        # projected points (falling back to the 1-year dynasty projection) as the
        # second category. Sleeper's search_rank — a search-popularity signal, not a
        # fantasy-relevance one (this is why retired stars used to outrank real
        # sleepers here) — is demoted to a silent last-resort tiebreak, not a driver.
        # An unloaded Draft Sharks pool falls all the way through to that tiebreak,
        # which still beats plain alphabetical.
        def _fa_default_sort_key(row: dict):
            adp = row.get("ds_fa_rank", row.get("ds_rank"))
            points = row.get("ds_ros_3d", row.get("ds_projection"))
            return (
                adp is None, adp if adp is not None else 0,
                points is None, -(points if points is not None else 0),
                row.get("search_rank") if row.get("search_rank") is not None else float("inf"),
                row["name"],
            )

        fa_rows.sort(key=_fa_default_sort_key)

    with fcol2:
        if fa_rows:
            fa_column_labels = {"sleeper_proj": sleeper_proj_label(snapshot)}
            with st.container(key="fa_sort_header"):
                header_cols = st.columns(len(fa_display_cols))
                for header_col, col in zip(header_cols, fa_display_cols):
                    label = fa_column_labels.get(col) or TABLE_COLUMN_LABELS.get(col, col.replace("_", " ").title())
                    if fa_sort and fa_sort[0] == col:
                        label += " ▲" if fa_sort[1] == "asc" else " ▼"
                    if header_col.button(label, key=f"fa_sort_btn_{col}", use_container_width=True):
                        if fa_sort and fa_sort[0] == col:
                            new_dir = "asc" if fa_sort[1] == "desc" else "desc"
                        else:
                            # Rank-like columns read naturally low-to-high; everything else high-to-low.
                            new_dir = "asc" if col in ("name", "team", "position", "search_rank", "ds_rank", "ds_fa_rank") else "desc"
                        st.session_state.fa_sort = (col, new_dir)
                        st.rerun()
            fa_df = pd.DataFrame(fa_rows[:25])
            render_styled_table(
                fa_df[fa_display_cols],
                pill_columns={"injury_status": _injury_pill_color, "position": _position_pill_color},
                render_header=False,
                column_labels=fa_column_labels,
            )
            if "sleeper_proj" in fa_df.columns:
                proj_req = snapshot.get("projection_request") or snapshot.get("nfl_state") or {}
                st.caption(
                    f"'Sleeper Proj' = Sleeper's native {proj_req.get('season_type', 'regular')} week-"
                    f"{proj_req.get('week', '?')} projection (unofficial endpoint). 'DS ROS Proj' = Draft "
                    "Sharks' rest-of-season number, when that data is loaded."
                )
        else:
            st.caption("No Sleeper free agents match that filter.")

    # ------------------------------------------------------------------ trade calculator --
    # Dashboard data -> rough trade math -> AI debate, not a standalone valuation tool bolted
    # on next to the panel. Everything below runs on data already loaded here (Trade Value
    # Chart or, failing that, Dynasty Rankings' own trade_value column; positional depth) and
    # needs no API key at all -- the LLMs only enter once the anvil buttons ask for
    # interpretation: does an apparent value gap actually matter given roster construction,
    # is there news the raw numbers can't see, etc.

    st.markdown("---")
    st.subheader("Trade Calculator")
    st.caption(
        "One player or pick per line, either side. Runs entirely on data already loaded here — "
        "no API key needed for the numbers below. Dynasty trades aren't algebra, so treat this as "
        "a rough read, not a verdict: what it can't see (roster fit, a coach's usage pattern, next "
        "week's injury news) is exactly what the panel is for."
    )

    owner_labels = roster_owner_names(snapshot)
    my_team_label = owner_labels.get(roster["roster_id"]) if roster else None
    depth = positional_depth(player_universe, merger)
    other_team_labels = sorted({v for k, v in owner_labels.items() if v != my_team_label})
    trade_partner = st.selectbox(
        "Trading with (optional)", options=["Not specified"] + other_team_labels, key="trade_calc_partner",
        help="Adds their positional need to the context below — purely optional, the calculator "
        "still works without it.",
    ) if other_team_labels else "Not specified"

    tccol1, tccol2 = st.columns(2)
    trade_send_text = tccol1.text_area(
        "You send", key="trade_calc_send", height=110,
        placeholder="One player or pick per line, e.g.\nJa'Marr Chase\n2027 Random Rd 1",
    )
    trade_receive_text = tccol2.text_area(
        "You receive", key="trade_calc_receive", height=110, placeholder="One player or pick per line",
    )

    # merge_player's fuzzy matcher keys on (first-initial, last-token) -- built for player
    # names, where that's a reasonable identity shortcut. Pick labels break that assumption:
    # "2027 Random Rd 1" and "2028 Random Rd 1" both reduce to the same ("2", "1") key, so
    # matching a pick label against the *unfiltered* Trade Value Chart (players and picks
    # together) can silently return a different year's pick at the same slot. Restricting the
    # player match to just the player rows keeps pick labels out of that matcher entirely --
    # pick_value() below does its own exact-normalized-name lookup instead, immune to this.
    _tvc_players = (
        merger.trade_values[merger.trade_values["asset_type"] == "player"]
        if merger.is_trade_values_loaded and "asset_type" in merger.trade_values.columns
        else merger.trade_values
    )

    def _match_key(name: str) -> tuple[str, str]:
        tokens = normalize_name(name).split()
        return (tokens[0][0], tokens[-1]) if tokens else ("", "")

    # merge_player's own key-match silently picks the first candidate when several players
    # share a (first-initial, last-name) key and no position/team was given to disambiguate
    # (confirmed live: a same-keyed "Jaylen Allen" resolved to "Josh Allen"'s value instead of
    # its own) -- fine for callers that always have a position in hand (the free-agent/roster
    # tables), but the trade calculator's free-text input never does. Recomputing the same key
    # here to count real candidates catches that specific gap without touching merge_player's
    # own contract, which plenty of other call sites already depend on staying as-is.
    _tvc_player_keys = _tvc_players["norm_name"].map(lambda n: _match_key(n)) if not _tvc_players.empty else None

    # FAAB dollars and waiver-priority swaps are common lopsided-piece-count sweeteners in a
    # real trade, but Draft Sharks has no market value for either -- a league's FAAB budget can
    # be $100 or $1000, so there's no defensible universal "$1 FAAB = X trade value" conversion
    # to invent (same "shouldn't pretend to be precise" reasoning as everywhere else here).
    # Flagged as its own category rather than falling through to "not found in loaded Draft
    # Sharks data", which reads as a typo/error when it's actually just a real asset type this
    # pricing tool was never going to cover.
    _CONSIDERATION_RE = re.compile(r"\$\d|faab|waiver|priority", re.IGNORECASE)

    def _price_trade_side(text: str) -> list[dict]:
        """One resolved row per non-empty line: {label, value, position, source, external}. Tries
        the Trade Value Chart first — players and picks priced on one comparable 0-100 scale, the
        closest this app has to an actual trade-pricing tool — then falls back to whatever a
        player's own Dynasty Rankings trade_value says (a different, rougher scale: format-
        based overall rank, not built for pricing a trade) rather than leaving a line unpriced
        just because the one dedicated tool for this isn't loaded. Picks only ever price off
        the Trade Value Chart -- Dynasty Rankings has no pick data at all. Never dropped even
        when nothing matches -- an unpriced line still belongs in what gets sent to the panel.

        external carries any secondary-source opinions (see DataMerger.external_player_values)
        on the same named player, purely as a side-by-side annotation -- it never feeds `value`
        or the anvil math below, which stays Draft-Sharks-scaled throughout, so a second source
        with a wildly different scale can't silently skew a number this app treats as pricing.

        composite is this app's own single blended read (DataMerger.composite_player_score) --
        shown in the calculator UI as one clean number rather than every source at once (that
        full breakdown is what `external` is for, and what still reaches the panel/bots via
        _describe_trade_side below); also never feeds `value`, same reasoning as external."""
        rows = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if _CONSIDERATION_RE.search(line):
                rows.append({"label": line, "value": None, "position": None, "source": None, "consideration": True})
                continue
            external = merger.external_player_values(line) if merger.is_external_values_loaded else []
            composite = merger.composite_player_score(line)
            tvc_player = merger.merge_player(line, df=_tvc_players) if merger.is_trade_values_loaded else {}
            if tvc_player.get("matched") and _tvc_player_keys is not None:
                candidates = int((_tvc_player_keys == _match_key(line)).sum())
                if candidates > 1:
                    rows.append({
                        "label": line, "value": None, "position": None, "source": None,
                        "ambiguous": True, "external": external, "composite": composite,
                    })
                    continue
            # The Trade Value Chart's own column is "value", not "trade_value" -- it's the one
            # table that skips the CSV/JSON header-alias renaming (see merge_player's own note).
            tvc_price = tvc_player.get("trade_value", tvc_player.get("value"))
            if tvc_player.get("matched") and tvc_price is not None:
                rows.append({
                    "label": line, "value": float(tvc_price),
                    "position": tvc_player.get("position"), "source": "Trade Value Chart",
                    "external": external, "composite": composite,
                })
                continue
            pick_val = merger.pick_value(line) if merger.is_trade_values_loaded else None
            if pick_val is not None:
                rows.append({
                    "label": line, "value": float(pick_val), "position": None,
                    "source": "Trade Value Chart", "external": external, "composite": composite,
                })
                continue
            rankings_player = merger.merge_player(line)
            if rankings_player.get("matched") and rankings_player.get("trade_value") is not None:
                # Same free-text-without-a-position-hint exposure as the Trade Value Chart
                # path above, against the (larger) Dynasty Rankings pool this time.
                # Series == tuple broadcasts elementwise as intended; Series.eq(tuple) does not
                # -- pandas treats a tuple RHS as array-like for .eq() and raises on the length
                # mismatch instead of comparing each element against it. Confirmed the hard way.
                candidates = int(
                    (merger.projections["norm_name"].map(_match_key) == _match_key(line)).sum()
                ) if not merger.projections.empty else 1
                if candidates > 1:
                    rows.append({
                        "label": line, "value": None, "position": None, "source": None,
                        "ambiguous": True, "external": external, "composite": composite,
                    })
                    continue
                rows.append({
                    "label": line, "value": float(rankings_player["trade_value"]),
                    "position": rankings_player.get("position"), "source": "Dynasty Rankings",
                    "external": external, "composite": composite,
                })
                continue
            rows.append({
                "label": line, "value": None, "position": None, "source": None,
                "external": external, "composite": composite,
            })
        return rows

    def _depth_label(team_label: Optional[str], position: str, override_cell: Optional[dict] = None) -> Optional[str]:
        """Strong/Average/Weak/None for one team's depth at one position, relative to the rest
        of the league at that position -- an absolute cutoff means nothing (a 2-team best-ball
        league and a 14-team dynasty league have very different "normal" depth), but "better or
        worse than everyone else in this exact league at this exact position" always does.
        override_cell lets a caller ask "what would this label be AFTER the trade" by passing a
        simulated {count, value} instead of the team's actual current one -- same peer
        comparison, just a hypothetical instead of the real cell."""
        if not team_label:
            return None
        cells = [teams[position] for teams in depth.values() if position in teams]
        if not cells:
            return None
        cell = override_cell if override_cell is not None else depth.get(team_label, {}).get(position, {"count": 0, "value": None})
        if cell["count"] == 0:
            return "None — no rostered players here"
        use_value = cell["value"] is not None and all(c["value"] is not None for c in cells)
        avg = (sum(c["value"] for c in cells) if use_value else sum(c["count"] for c in cells)) / len(cells)
        if not avg:
            return None
        ratio = (cell["value"] if use_value else cell["count"]) / avg
        return "Strong" if ratio >= 1.3 else "Weak" if ratio <= 0.7 else "Average"

    trade_send_rows = _price_trade_side(trade_send_text)
    trade_receive_rows = _price_trade_side(trade_receive_text)
    sources_used = {r["source"] for r in trade_send_rows + trade_receive_rows if r["source"]}

    if not sources_used and not (trade_send_rows or trade_receive_rows):
        st.caption(
            "No Draft Sharks data loaded, so there's nothing to price either side against yet — "
            "upload Dynasty Rankings or a Trade Value Chart under Data Uploads. The buttons below "
            "still work without it; the panel can reason about a trade from market judgment alone."
        )
    elif trade_send_rows or trade_receive_rows:
        if not sources_used:
            st.caption(
                "No Draft Sharks data loaded yet, so nothing below is priced — upload Dynasty "
                "Rankings or a Trade Value Chart under Data Uploads to get numbers."
            )
        elif len(sources_used) > 1:
            st.caption(
                "⚠️ Mixing value scales (Trade Value Chart + Dynasty Rankings, per-line below) — "
                "the totals are directionally useful, not precise."
            )
        if any(r.get("consideration") for r in trade_send_rows + trade_receive_rows):
            st.caption(
                "💰 FAAB/waiver considerations don't have a market value (league budgets vary too "
                "much to invent one) — included below and sent to the panel, just not in the totals."
            )

        def _composite_suffix(row: dict) -> str:
            # This app's own single blended read (DataMerger.composite_player_score) -- shown
            # here as one clean number, not every source stacked up (that full breakdown still
            # reaches the panel/bots via _describe_trade_side below, per "external" on this same
            # row). Never blended into row["value"] above -- side note, not part of the price.
            composite = row.get("composite")
            if not composite:
                return f"  ·  {INCOMPLETE_PLAYER_PROFILE}"
            return f"  ·  Composite {composite['score']:.0f}/100 ({composite['recency_grade']})"

        def _render_trade_side(rows: list[dict]) -> None:
            for row in rows:
                if row.get("consideration"):
                    st.caption(f"💰 {row['label']} — not priced")
                elif row.get("ambiguous"):
                    st.caption(f"❓ \"{row['label']}\" — matches more than one player; add a position or full name")
                elif row["value"] is None:
                    st.caption(f"⚠️ \"{row['label']}\" — not found in loaded Draft Sharks data{_composite_suffix(row)}")
                else:
                    tag = " (DR)" if row["source"] == "Dynasty Rankings" else ""
                    st.caption(f"{row['label']} — {row['value']:.0f}{tag}{_composite_suffix(row)}")

        rrcol1, rrcol2 = st.columns(2)
        with rrcol1:
            _render_trade_side(trade_send_rows)
        with rrcol2:
            _render_trade_side(trade_receive_rows)

        trade_send_total = sum(r["value"] for r in trade_send_rows if r["value"] is not None)
        trade_receive_total = sum(r["value"] for r in trade_receive_rows if r["value"] is not None)
        larger_total = max(trade_send_total, trade_receive_total)
        delta = trade_receive_total - trade_send_total
        delta_pct = (abs(delta) / larger_total * 100) if larger_total else 0.0
        favorable = delta > 0

        mcol1, mcol2, mcol3 = st.columns(3)
        mcol1.metric("You send", f"{trade_send_total:.0f}")
        mcol2.metric("You receive", f"{trade_receive_total:.0f}")
        mcol3.metric("Balance", f"{'+' if delta >= 0 else ''}{delta_pct if delta >= 0 else -delta_pct:.0f}%")

        # Two independent reads, not one number with a caveat bolted on. A real Draft Sharks
        # trade evaluation (checked directly against this app's own vendor, not a competitor)
        # scores each side against ITS OWN roster -- both sides of a real trade can legitimately
        # come back positive at once, because "I gave up more raw value" and "this trade fits my
        # roster" are different questions with different answers. Raw value below stays simple,
        # zero-sum arithmetic (it has to be -- a value pool can't hand both sides a surplus at
        # once); roster fit is the second, independently-computed read, not a footnote on the
        # first. Four tiers on the raw side, not two -- validated against a broad calibration
        # pass (durable dynasty principles plus WebSearch-confirmed 2026 consensus anchors: 1.01
        # ~= a top-tier young RB, the 1.02-1.05 superflex range being one interchangeable tier)
        # rather than tuned to match any one external site's own cutoffs.
        raw_verdict = None
        raw_line = None
        if larger_total:
            if delta_pct < 5:
                raw_verdict = "Balanced"
                raw_line = f"🟢 Essentially even — within {delta_pct:.0f}% either way."
            else:
                raw_verdict = "favorable" if favorable else "unfavorable"
                who = "receiving" if favorable else "sending"
                if delta_pct < 10:
                    raw_line = f"🟡 Slight edge, {raw_verdict} — you'd be {who} {delta_pct:.0f}% more value."
                elif delta_pct < 20:
                    raw_line = f"🟠 Meaningful edge, {raw_verdict} — you'd be {who} {delta_pct:.0f}% more value."
                else:
                    emoji = "🟢" if favorable else "🔴"
                    raw_line = f"{emoji} Materially {raw_verdict} — you'd be {who} {delta_pct:.0f}% more value."

        # Positions actually changing hands -- picks carry no position, so only priced player
        # rows can ever touch this.
        sent_positions = [r["position"] for r in trade_send_rows if r["position"]]
        received_positions = [r["position"] for r in trade_receive_rows if r["position"]]
        touched_positions = sorted(set(sent_positions) | set(received_positions))

        fit_verdict, fit_line = None, None
        _DEPTH_RANK = {"None — no rostered players here": 0, "Weak": 1, "Average": 2, "Strong": 3}
        position_detail: list[str] = []
        if touched_positions and my_team_label:
            fit_score = 0
            improved, worsened = [], []
            for pos in touched_positions:
                before_cell = depth.get(my_team_label, {}).get(pos, {"count": 0, "value": None})
                value_sent_here = sum(r["value"] for r in trade_send_rows if r.get("position") == pos and r["value"] is not None)
                value_received_here = sum(r["value"] for r in trade_receive_rows if r.get("position") == pos and r["value"] is not None)
                after_count = before_cell["count"] - sent_positions.count(pos) + received_positions.count(pos)
                # before_cell["value"] is None whenever the team owns zero players here (nothing
                # to sum) -- that's "no players", not "no price data", so treat it as 0 rather
                # than letting a None short-circuit the whole after-value to None even when a
                # priced asset is moving in. A trade-calculator row only ever carries a position
                # once merge_player/pick_value already priced it, so value_sent_here/
                # value_received_here are never contaminated by an unpriced line here.
                after_value = (before_cell["value"] or 0) - value_sent_here + value_received_here
                before_label = _depth_label(my_team_label, pos)
                after_label = _depth_label(my_team_label, pos, override_cell={"count": after_count, "value": after_value})
                before_rank = _DEPTH_RANK.get(before_label, 2)
                after_rank = _DEPTH_RANK.get(after_label, 2)
                fit_score += after_rank - before_rank
                if after_rank > before_rank:
                    improved.append(pos)
                elif after_rank < before_rank:
                    worsened.append(pos)

                line = f"Your {pos} depth: {before_label or 'unknown'}"
                if after_count != before_cell["count"]:
                    line += f" → {after_label or 'unknown'} post-trade ({before_cell['count']} → {after_count}" + (", zero left)" if after_count == 0 else ")")
                if trade_partner != "Not specified":
                    theirs = _depth_label(trade_partner, pos)
                    if theirs:
                        line += f" · {trade_partner}'s {pos} depth: {theirs}"
                position_detail.append(line)

            if fit_score > 0:
                fit_verdict = "favorable"
                fit_line = f"🟢 Favorable — improves your depth at {', '.join(improved)}."
            elif fit_score < 0:
                fit_verdict = "unfavorable"
                fit_line = f"🔴 Unfavorable — thins your depth at {', '.join(worsened)}."
            else:
                fit_verdict = "neutral"
                fit_line = "⚪ Roughly neutral — no meaningful shift in positional depth either way."

        if raw_line or fit_line:
            vcol1, vcol2 = st.columns(2)
            with vcol1:
                st.markdown("**Raw value**")
                st.caption(raw_line or "No priced assets to compare.")
            with vcol2:
                st.markdown("**Roster fit**")
                st.caption(fit_line or "No player positions involved, or no team on file to check depth against.")
            if raw_verdict in ("favorable", "unfavorable") and fit_verdict in ("favorable", "unfavorable") and raw_verdict != fit_verdict:
                st.caption(
                    "↔️ These two disagree — the raw numbers and your roster fit point opposite "
                    "ways. Worth digging into which one actually matters more for this decision "
                    "before trusting either alone."
                )

        if position_detail:
            with st.expander("Positional depth detail"):
                for line in position_detail:
                    st.caption(line)

    def _describe_trade_side(rows: list[dict]) -> str:
        def _line(r: dict) -> str:
            base = (
                f"  - {r['label']} (value: {r['value']:.0f}{', ' + r['source'] if r['source'] else ''})"
                if r["value"] is not None else f"  - {r['label']}"
            )
            # Own scale, not Draft Sharks' -- see external_player_values' docstring -- so this
            # is a side note for the panel to weigh, never something to add to the value above.
            extra = "; ".join(describe_external_value(ext) for ext in r.get("external") or [])
            if extra:
                base += f" [other sources (own scale): {extra}]"
            # The composite is one more data point for the panel, same as every raw source
            # above it -- never a substitute for them. See composite_player_score's docstring.
            composite = r.get("composite")
            if composite:
                base += (
                    f" [composite: {composite['score']:.0f}/100, {composite['recency_grade']} "
                    f"data (avg {composite['avg_age_days']}d old), from "
                    f"{len(composite['components'])} source(s)]"
                )
            elif r["value"] is not None or r.get("external"):
                # Only worth stating explicitly when *something* else resolved for this line --
                # a totally blank line (no value, no external hits) already says enough on its own.
                base += f" [composite: {INCOMPLETE_PLAYER_PROFILE}]"
            return base
        return "\n".join(_line(r) for r in rows)

    _trade_ready = bool(trade_send_text.strip() and trade_receive_text.strip())
    trade_question = (
        "Evaluate this trade for me:\nYou send:\n" + _describe_trade_side(trade_send_rows) +
        "\nYou receive:\n" + _describe_trade_side(trade_receive_rows)
    )
    if trade_partner != "Not specified":
        trade_question += f"\nTrading with: {trade_partner}"

    bcol1, bcol2 = st.columns(2)
    with bcol1:
        ask_moderator = st.button(
            "⚖️ Moderator Review", use_container_width=True, disabled=not _trade_ready,
            help="Given the calculated balance and all available roster/context data, is this "
            "actually a good trade? A fresh full debate if there's no prior conversation in this "
            "chat to react to, otherwise a lightweight follow-up off it.",
        )
    with bcol2:
        ask_full_squad = st.button(
            "🔥 Full Squad Debate", type="primary", use_container_width=True, disabled=not _trade_ready,
            help="Forces a fresh full panel run (Quant → Beat Tracker → Contrarian → Moderator) on "
            "this exact trade, regardless of any prior conversation in this chat.",
        )
    if ask_moderator:
        st.session_state["question_input"] = (
            trade_question + "\n\nGiven the calculated balance and all available roster/context "
            "data above, is this actually a good trade?"
        )
    elif ask_full_squad:
        st.session_state["question_input"] = "/debate " + trade_question

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
                        notify("warning", "Select at least one league, or switch to Global.")
                    else:
                        set_scope(item["filename"], edit_league_ids if edit_mode == "Specific league(s)" else None)
                        st.rerun()

else:
    # ------------------------------------------------------------------ league rosters --

    st.markdown("---")
    st.subheader("League Rosters")

    # League-wide positional depth -- every team including your own (unlike the per-team
    # drill-down below, which excludes yours since it has its own tab). Computed straight
    # from Sleeper's own roster data rather than parsed off Draft Sharks' League Analyzer
    # positional-rank table: that PDF's flat text loses its row/column structure and can't
    # be reliably reattributed to the right team, so this is the same underlying fact
    # (how deep is each team at each position) derived from a source that's actually safe
    # to parse instead of guessed from one that isn't.
    _depth = positional_depth(player_universe, st.session_state.data_merger)
    if _depth:
        st.markdown("**League-Wide Positional Depth**")
        _has_values = st.session_state.data_merger.is_loaded
        st.caption(
            "How many rostered players (starters + bench + taxi/IR) each team has at each "
            "position — a scan for who's thin or stacked somewhere, without asking the bots "
            + (
                "team-by-team. Value in parens is that position's total Draft Sharks trade "
                "value — weigh it over the raw count: a pile of backups and three stacked "
                "stars can both show \"3.\""
                if _has_values else
                "team-by-team. This is body count only (no Draft Sharks data loaded) — two "
                "teams tied here can still differ hugely in actual talent."
            )
        )
        _position_order = ["QB", "RB", "WR", "TE", "K", "DEF", "LB", "DL", "DB"]
        _positions_present = [p for p in _position_order if any(p in positions for positions in _depth.values())]
        _rows = []
        for team_label, positions in sorted(_depth.items()):
            row = {"team": team_label}
            for pos in _positions_present:
                cell = positions.get(pos, {"count": 0, "value": None})
                row[pos] = f"{cell['count']} ({cell['value']:.0f})" if cell["value"] is not None else cell["count"]
            _rows.append(row)
        depth_df = pd.DataFrame(_rows)[["team"] + _positions_present]
        render_styled_table(depth_df)

    st.caption(
        "Every other team's roster in this league, straight from Sleeper — for trade scouting. "
        "Not enriched with Draft Sharks data here; just who owns whom."
    )

    rosters_by_owner: dict[str, list[dict]] = {}
    for row in player_universe:
        if row.get("ownership") != "ROSTERED" or row.get("owner_id") == st.session_state.user_id:
            continue  # your own roster already has its own tab
        owner_label = row.get("owner_name") or f"Roster {row.get('roster_id', '?')}"
        rosters_by_owner.setdefault(owner_label, []).append(row)

    if not rosters_by_owner:
        st.info("No other rostered teams found in this league's synced data.")
    else:
        selected_owner = st.selectbox("Team", options=sorted(rosters_by_owner))
        team_rows = rosters_by_owner[selected_owner]
        team_df = pd.DataFrame([
            {
                "name": r["name"], "position": r["position"], "team": r["team"],
                "slot": r.get("roster_slot") or "Bench", "injury_status": r.get("injury_status"),
                "sleeper_proj": r.get("sleeper_proj"),
            }
            for r in team_rows
        ])
        team_df["_sort"] = team_df["slot"].map(SLOT_SORT_ORDER).fillna(99)
        team_df = team_df.sort_values("_sort").drop(columns="_sort")
        display_cols = [c for c in ["name", "position", "team", "slot", "sleeper_proj", "injury_status"] if c in team_df.columns]
        render_styled_table(
            team_df[display_cols],
            pill_columns={"injury_status": _injury_pill_color, "position": _position_pill_color},
            group_column="slot",
            column_labels={"sleeper_proj": sleeper_proj_label(snapshot)},
        )
        st.caption(
            "Ask the Debate Studio about this team by name (or a specific player on it) for a full trade "
            "read — it can see any team's roster, not just the one selected above."
        )

# ------------------------------------------------------------------ pinned messages --
# The Decision Log below is "what the system decided" -- this is "what someone in this
# conversation thought was worth preserving," the user's own curation rather than the
# Moderator's. Kept in normal page flow for the same reason as Decision Log (see below).
pinned_ts_panel = pinned_messages.load_pinned_ts(st.session_state.selected_league_id)
if pinned_ts_panel:
    pinned_msgs_panel = [m for m in st.session_state.chat_history if m.get("ts") in pinned_ts_panel]
    with st.expander(f"📌 Pinned Messages ({len(pinned_msgs_panel)})"):
        st.caption(
            "Messages you've flagged as worth keeping handy, newest first. Available for the "
            "bots to reference if a later question actually relates to one — pinning doesn't "
            "weight a message more heavily than anything else in context by itself."
        )
        _panel_role_names = bot_config.load_role_names()
        _panel_role_word = {"quant": "Quant", "beat": "Beat Tracker", "contrarian": "Contrarian", "moderator": "Moderator", "user": "You"}
        for pm in sorted(pinned_msgs_panel, key=lambda m: m.get("ts", 0), reverse=True):
            who = _panel_role_names.get(pm["role"], _panel_role_word.get(pm["role"], pm["role"]))
            st.markdown(f"**{who}**")
            st.caption(pm.get("content", "")[:500])
            if st.button("Unpin", key=f"unpin_panel_{pm.get('ts')}"):
                pinned_messages.toggle_pin(st.session_state.selected_league_id, pm["ts"])
                st.rerun()
            st.markdown("<hr style='margin:6px 0;opacity:0.15'>", unsafe_allow_html=True)

# ------------------------------------------------------------------ decision log / objectives --
# Reference/historical content, not the live chat interface -- kept in normal page flow (not the
# fixed-position debate dock below) since deeply nested columns inside that fixed container were
# confirmed to compute their width against the wrong basis and push buttons off-screen entirely.
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
                    "Outcome": d.get("outcome") or "—",
                }
                for d in reversed(decisions)
            ]
        )
        st.dataframe(log_df, use_container_width=True, hide_index=True)

        st.caption(
            "Record how a call actually played out — the bots weigh this on related future "
            "questions instead of re-deriving the same reasoning cold each time."
        )
        outcome_options = {
            f"{d['date']} — {d['question'][:70]}"
            + (f" [{d['outcome']}]" if d.get("outcome") else ""): d["ts"]
            for d in reversed(decisions)
        }
        picked_label = st.selectbox("Decision", options=list(outcome_options), key="outcome_pick_decision")
        rate_col, note_col = st.columns(2)
        rating = rate_col.selectbox("Outcome", options=decision_log.OUTCOME_LABELS, key="outcome_rating")
        note = note_col.text_input("Note (optional)", key="outcome_note", placeholder="What actually happened…")
        if st.button("Save outcome", key="save_decision_outcome"):
            decision_log.set_outcome(st.session_state.selected_league_id, outcome_options[picked_label], rating, note)
            st.rerun()

todo_league_id = st.session_state.selected_league_id
active_items = todo_log.load_todos(todo_league_id, statuses=todo_log.ACTIVE_STATUSES)
with st.expander(f"🎯 Active Objectives ({len(active_items)})", expanded=bool(active_items)):
    st.caption(
        "League objectives the bots are tracking (🤖) or you added yourself (✍️) — selectively "
        "given to the bots as context in future debates, not just a checklist. A 🔎 tag means a "
        "bot proposed it looks done; confirm it or keep it open. A resolution note you add when "
        "closing one persists permanently in the Archive below, so the bots can recall *why* it "
        "ended the way it did if the same idea comes up again."
    )
    manual_col, add_col = st.columns([4, 1])
    manual_text = manual_col.text_input(
        "Add an objective", key="manual_todo_text", label_visibility="collapsed",
        placeholder="Add a new objective…",
    )
    if add_col.button("Add", key="add_manual_todo", use_container_width=True) and manual_text.strip():
        todo_log.add_todo(todo_league_id, manual_text, source="manual")
        st.rerun()

    if not active_items:
        st.caption("Nothing active right now.")
    else:
        for item in active_items:
            with st.container(border=True):
                source_tag = "🤖" if item.get("source") == "moderator" else "✍️"
                referenced = (
                    f" · 👁 referenced {item['last_referenced']}" if item.get("last_referenced") else ""
                )
                header = (
                    f"{source_tag} **#{item['id']}** {item['text']}  \n"
                    f"<span style='color:#6b7280;font-size:0.78rem;'>{item['date']}{referenced}</span>"
                )
                st.markdown(header, unsafe_allow_html=True)

                if item.get("revisions"):
                    with st.popover("📝 Revision history"):
                        for rev in item["revisions"]:
                            reason_suffix = f" — {rev['reason']}" if rev.get("reason") else ""
                            st.caption(f"{rev['date']}: was \"{rev['text']}\"{reason_suffix}")

                for note in item.get("notes", []):
                    st.caption(f"🗒️ {note['date']}: {note['text']}")

                note_col, note_btn_col = st.columns([4, 1])
                note_text = note_col.text_input(
                    "Add note", key=f"todo_note_{item['id']}", label_visibility="collapsed",
                    placeholder="Add a note while this is still active…",
                )
                if note_btn_col.button("Add", key=f"todo_note_add_{item['id']}", use_container_width=True) and note_text.strip():
                    todo_log.add_note(todo_league_id, item["id"], note_text)
                    st.rerun()

                if item["status"] == "likely_resolved":
                    st.markdown(f"🔎 **Proposed as likely resolved:** {item.get('resolution_reason', '')}")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Confirm Done", key=f"todo_confirm_{item['id']}", use_container_width=True):
                        todo_log.resolve_todo(todo_league_id, item["id"])
                        st.rerun()
                    if c2.button("↩️ Keep Open", key=f"todo_reopen_{item['id']}", use_container_width=True):
                        todo_log.reopen_todo(todo_league_id, item["id"])
                        st.rerun()
                else:
                    resolution_note = st.text_input(
                        "Resolution note (optional)", key=f"todo_resolve_note_{item['id']}",
                        placeholder="What happened, so this stays useful as history later…",
                    )
                    d1, d2, d3 = st.columns(3)
                    if d1.button("✓ Mark Done", key=f"todo_done_{item['id']}", use_container_width=True):
                        todo_log.resolve_todo(todo_league_id, item["id"], resolution_note)
                        st.rerun()
                    if d2.button("✕ Dismiss", key=f"todo_dismiss_{item['id']}", use_container_width=True):
                        todo_log.dismiss_todo(todo_league_id, item["id"], resolution_note or "Dismissed by user")
                        st.rerun()
                    if d3.button("🗑️ Delete", key=f"todo_delete_{item['id']}", use_container_width=True):
                        todo_log.delete_todo(todo_league_id, item["id"])
                        st.rerun()

archived_items = todo_log.load_todos(todo_league_id, statuses=todo_log.ARCHIVED_STATUSES)
with st.expander(f"🗄️ Archive ({len(archived_items)})"):
    st.caption(
        "Resolved and dismissed objectives — kept as strategic memory, not deleted. The bots "
        "draw on the resolution note here to avoid re-investigating something that already "
        "failed, or to recognize when it's worth trying again."
    )
    if not archived_items:
        st.caption("Nothing archived yet.")
    else:
        archive_query = st.text_input(
            "Search the archive", key="archive_search", placeholder="Filter by player, team, or topic…",
        )
        if archive_query.strip():
            needle = archive_query.strip().lower()
            visible_archived = [
                e for e in archived_items
                if needle in e.get("text", "").lower() or needle in e.get("resolution_reason", "").lower()
            ]
            if not visible_archived:
                st.caption(f"No archived objectives match \"{archive_query.strip()}\".")
        else:
            visible_archived = archived_items
        for item in sorted(visible_archived, key=lambda e: e.get("ts", 0), reverse=True):
            outcome = "✅ Completed" if item["status"] == "resolved" else "✕ Dismissed"
            with st.container(border=True):
                st.markdown(
                    f"**#{item['id']}** {item['text']}  \n"
                    f"<span style='color:#6b7280;font-size:0.78rem;'>{item['date']} → {outcome} "
                    f"{item.get('resolution_date', '')}</span>",
                    unsafe_allow_html=True,
                )
                if item.get("resolution_reason"):
                    st.markdown(f"**Resolution note:** {item['resolution_reason']}")
                for note in item.get("notes", []):
                    st.caption(f"🗒️ {note['date']}: {note['text']}")
                if item.get("revisions"):
                    with st.popover("📝 Revision history"):
                        for rev in item["revisions"]:
                            reason_suffix = f" — {rev['reason']}" if rev.get("reason") else ""
                            st.caption(f"{rev['date']}: was \"{rev['text']}\"{reason_suffix}")

                a1, a2 = st.columns(2)
                if a1.button("🔄 Revisit as new objective", key=f"todo_revisit_{item['id']}", use_container_width=True):
                    todo_log.add_todo(
                        todo_league_id, item["text"], source="manual",
                        question=f"Revisit of #{item['id']}",
                    )
                    st.rerun()
                if a2.button("🗑️ Delete permanently", key=f"todo_archive_delete_{item['id']}", use_container_width=True):
                    todo_log.delete_todo(todo_league_id, item["id"])
                    st.rerun()

# ------------------------------------------------------------------ debate studio --
# A fixed dock at the bottom of the viewport, not just "below the tab content" —
# regardless of which tab is active AND regardless of scroll position on that
# tab's own content, so a question can be asked without hunting for the panel
# first. Collapsible down to a slim bar for when it's not in use.

DOCK_LEVELS = ["collapsed", "partial", "full"]
if "debate_dock_level" not in st.session_state:
    st.session_state.debate_dock_level = "partial"  # visible but not dominating, by default
dock_level = st.session_state.debate_dock_level
dock_level_idx = DOCK_LEVELS.index(dock_level)
# "Partial" is meant to feel like working *alongside* the bots, not a popup stealing
# the screen — genuinely ~40% of the viewport, not the ~55-60% it drifted to when the
# clearance below was just a rough guess. "Full" is closer to working *inside* it.
# Compact/text_area sizing per tier lives right where each is used, further down.
# collapsed uses max(...) rather than a bare vh value -- on a short viewport, 9vh alone
# could clip below the Expand button's own rendered height (button + container padding),
# which is exactly how it went missing in the first place. The px floor guarantees the
# button always fits regardless of viewport height; vh still wins on anything reasonably tall.
DOCK_HEIGHT_BY_LEVEL = {"collapsed": "max(9vh, 64px)", "partial": "40vh", "full": "94vh"}
CHAT_HEIGHT_BY_LEVEL = {"partial": 130, "full": 480}
QUESTION_HEIGHT_BY_LEVEL = {"partial": 90, "full": 200}

# The dock is position:fixed (see the <style> block up top), which takes it out of
# normal page flow. Its height is now authoritatively capped per tier (below), so the
# same value drives both the cap itself and how much room normal page content needs
# to leave clear — no more guessing a clearance number independent of actual height.
#
# padding-bottom alone only guarantees room to scroll past the dock at the very
# bottom of the page — it doesn't stop the browser's own scroll-into-view (Tab
# focus, an anchor jump, Playwright's scroll_into_view_if_needed) from landing an
# element's scroll position right underneath the fixed dock mid-page, since that
# algorithm has no idea the dock is there covering part of the viewport. Confirmed
# live: a Decision Log / Objectives control scrolled to did exactly that, genuinely
# unclickable at the position the browser chose. scroll-padding-bottom on the real
# scroll container (stMain, not the window — Streamlit scrolls its own <section>)
# tells that same algorithm to always leave the dock's height clear, so anything
# scrolled to lands above it instead.
_dock_h = DOCK_HEIGHT_BY_LEVEL[dock_level]
st.markdown(
    f"<style>"
    f"[data-testid='stMain'] {{ padding-bottom: {_dock_h}; scroll-padding-bottom: {_dock_h}; }}"
    f".st-key-debate_dock {{ max-height: {_dock_h}; }}"
    f"</style>",
    unsafe_allow_html=True,
)

with st.container(key="debate_dock"):
    st.session_state.setdefault("chat_scoped_attachments", [])
    league_id_for_header = st.session_state.get("selected_league_id")

    # Collapsed gets its own compact layout: the box is capped to a sliver (see
    # DOCK_HEIGHT_BY_LEVEL) with overflow-y: auto, and the title+caption+button stack
    # below used to add up to more than that sliver's height on most viewports — the
    # Expand button scrolled out of the visible area inside its own tiny box, exactly
    # the "covers the expand button" report this fixes. Putting the button first
    # (nothing above it to push it out of frame) and dropping the title/caption
    # entirely at this tier — redundant chrome once collapsed — keeps it reachable
    # regardless of viewport height instead of just shrinking the odds of clipping it.
    if dock_level == "collapsed":
        if st.button("▲ Expand", key="dock_expand", use_container_width=True):
            st.session_state.debate_dock_level = DOCK_LEVELS[dock_level_idx + 1]
            st.rerun()
        # Collapsing is for getting the dock out of the way, not for losing track of
        # the last call the bots made — the most recent verdict stays visible as a
        # one-line summary right here instead of disappearing until re-expanded.
        last_verdict_msg = next(
            (m for m in reversed(st.session_state.get("chat_history", [])) if m.get("role") == "moderator"),
            None,
        )
        if last_verdict_msg:
            last_verdict = llm_engine.parse_moderator_verdict(last_verdict_msg.get("content", ""))
            rec = last_verdict.get("recommendation")
            if rec:
                st.caption(f"Last call: **{rec}** — {last_verdict.get('reason', '')[:120]}")
    else:
        # A skewed-ratio st.columns([6, 1]) here (title next to the tier buttons) measured
        # its width against the container's pre-CSS-shift size instead of its actual fixed-
        # position width, pushing the second column entirely off-screen — confirmed live,
        # not a guess. Equal-ish column ratios don't hit it, so title/buttons get their own
        # rows instead of sharing one, sidestepping the bug rather than fighting it further.
        st.subheader("Multi-Model Debate Studio")
        active_count = len(todo_log.load_todos(league_id_for_header, statuses=todo_log.ACTIVE_STATUSES)) if league_id_for_header else 0
        attach_count = len(st.session_state.chat_scoped_attachments)
        st.caption(
            f"📂 **{league.get('name', 'Unknown League')}** working context — "
            f"🎯 {active_count} active objective(s)"
            + (f" · 📎 {attach_count} file(s) attached to this chat" if attach_count else "")
        )

        # One tier per press, not a straight open/closed toggle — collapsed shows only
        # "expand", full shows only "collapse", partial (the middle tier) shows both. Four
        # equal narrow slots (not stretched to the button count) keep the buttons a
        # consistent width across all three tiers instead of one button going full-width
        # whenever it's alone.
        tier_cols = st.columns(4)
        tier_col_idx = 0
        if dock_level != "full":
            if tier_cols[tier_col_idx].button("▲ Expand", key="dock_expand", use_container_width=True):
                st.session_state.debate_dock_level = DOCK_LEVELS[dock_level_idx + 1]
                st.rerun()
            tier_col_idx += 1
        if tier_cols[tier_col_idx].button("▼ Collapse", key="dock_collapse", use_container_width=True):
            st.session_state.debate_dock_level = DOCK_LEVELS[dock_level_idx - 1]
            st.rerun()

    role_providers = bot_config.load_role_providers()
    role_names = bot_config.load_role_names()
    role_models = bot_config.load_role_models()
    moderator_personality_key = bot_config.load_moderator_personality()
    moderator_personality = bot_config.MODERATOR_PERSONALITIES.get(moderator_personality_key)
    api_keys = {"claude": api_key_for("anthropic"), "gemini": api_key_for("gemini"), "openai": api_key_for("openai")}
    PERSONA_DOTS = {"quant": "🟢", "beat": "🟡", "contrarian": "🟣", "moderator": "🔴"}
    # A plain follow-up defaults to the Moderator alone once a debate has already run in this
    # chat -- not every next message deserves the whole panel reconvened, same as not every
    # message in a normal conversation needs a deep dive. /debate still forces a fresh full
    # re-run explicitly, any time.
    last_debate = find_last_debate(st.session_state.chat_history)
    default_trigger_mode = "followup" if last_debate else "debate"

    if dock_level != "collapsed":
        def _persona_caption(role: str) -> str:
            name = role_names[role]
            # A rename must never obscure which role it is -- "Freddy" alone six
            # months from now tells nobody he's the Quant.
            default = bot_config.ROLE_INFO[role]["default_name"]
            shown_name = f"{name} · {default}" if name != default else name
            # Prefer the actual model string over a generic provider-tier label --
            # "claude-opus-5" says more than "(Claude)" once a role has a specific
            # model set, and unlike a provider-name lookup table it stays meaningful
            # regardless of how many providers this app ends up supporting.
            powered_by = role_models.get(role) or bot_config.PROVIDER_LABELS[role_providers[role]]
            return f"{PERSONA_DOTS[role]} {shown_name} ({powered_by})"

        st.caption("Personas: " + " · ".join(_persona_caption(role) for role in bot_config.ROLES))

        # The attach control used to sit up in the header, a full row away from the box
        # it actually affects — moved here, right against the input it attaches to, so
        # the relationship reads at a glance instead of having to be inferred. Text box
        # gives up a little width to it rather than the button floating off on its own.
        btn_col, input_col, attach_col = st.columns([1, 2.7, 0.3])
        with btn_col:
            quick_debate = st.button("Full Debate", use_container_width=True, type="primary")
            # Contrarian and Moderator both need prior reports to react to -- asking
            # either alone means asking them to do their job with nothing to work
            # with, which produced structurally hollow answers. Quant and Beat are
            # each a legitimate standalone lookup (pure numbers, pure news), so only
            # those two get a solo quick-ask. Labeled by whoever currently holds the
            # role, not a fixed persona name -- rename Quant to "Freddy" and this
            # button says "Ask Freddy".
            quick_quant = st.button(
                f"Ask {role_names['quant']}", use_container_width=True,
                help=f"{bot_config.ROLE_INFO['quant']['label']} — numbers only, no news or risk framing.",
            )
            quick_beat = st.button(
                f"Ask {role_names['beat']}", use_container_width=True,
                help=f"{bot_config.ROLE_INFO['beat']['label']} — news/injury lookup only, no analysis.",
            )
        with input_col:
            # A text_area sized to roughly match the 4-button stack's height, not a
            # single-line text_input — the mismatched heights looked off. Trade-off:
            # text_area submits on Ctrl+Enter or losing focus, not a plain Enter. Shorter
            # at "partial" so the tier actually fits its ~40vh cap without the transcript
            # getting squeezed to nothing.
            question = st.text_area(
                (
                    "Continue the conversation with the Moderator, or type /debate for a fresh full panel run "
                    "(prefix with /quant or /beat to route explicitly)"
                    if last_debate else
                    "Ask about a start/sit, trade, or waiver decision "
                    "(prefix with /debate, /quant, or /beat to route explicitly)"
                ),
                key="question_input",
                height=QUESTION_HEIGHT_BY_LEVEL[dock_level],
            )
        with attach_col:
            # Blank line to drop the button below the text_area's own label, roughly
            # level with the top of the box itself rather than floating above it.
            st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
            attach_label = f"📎{attach_count}" if attach_count else "➕"
            with st.popover(attach_label, use_container_width=True, help="Attach a file to this chat"):
                st.caption(
                    "Ephemeral — only used to answer questions in this chat session, not saved to "
                    "the Reference Material library below."
                )
                chat_file = st.file_uploader(
                    "Add a file", type=["txt", "csv", "pdf"], key="chat_attach_uploader",
                    label_visibility="collapsed",
                )
                if chat_file is not None and not any(
                    a["name"] == chat_file.name for a in st.session_state.chat_scoped_attachments
                ):
                    if chat_file.name.lower().endswith(".pdf"):
                        import pypdf

                        reader = pypdf.PdfReader(chat_file)
                        text = "\n".join(page.extract_text() or "" for page in reader.pages)
                    else:
                        text = chat_file.read().decode("utf-8", errors="ignore")
                    if text.strip():
                        st.session_state.chat_scoped_attachments.append({"name": chat_file.name, "text": text})
                        st.rerun()
                for i, att in enumerate(list(st.session_state.chat_scoped_attachments)):
                    if st.button(f"✕ {att['name']}", key=f"remove_chat_attach_{i}", use_container_width=True):
                        st.session_state.chat_scoped_attachments.pop(i)
                        st.rerun()

        def resolve_command(text: str, default_mode: str) -> tuple[str, str]:
            for prefix, mode in (("/debate", "debate"), ("/quant", "quant"), ("/beat", "beat")):
                if text.strip().lower().startswith(prefix):
                    return mode, text.strip()[len(prefix):].strip()
            return default_mode, text.strip()

        trigger_mode = None
        trigger_question = None
        if quick_debate and question:
            trigger_mode, trigger_question = "debate", question
        elif quick_quant and question:
            trigger_mode, trigger_question = "quant", question
        elif quick_beat and question:
            trigger_mode, trigger_question = "beat", question
        elif question and st.session_state.get("_last_submitted") != question:
            mode, cleaned = resolve_command(question, default_trigger_mode)
            trigger_mode, trigger_question = mode, cleaned

        if trigger_mode and trigger_question:
            st.session_state["_last_submitted"] = question
            context = build_context(snapshot, roster_table if roster else [], player_universe, trigger_question)
            if st.session_state.get("chat_scoped_attachments"):
                context += "\n\nATTACHED TO THIS CHAT (this session only, not part of the permanent Reference Material library):\n" + "\n\n".join(
                    f"--- {a['name']} ---\n{a['text'][:4000]}" for a in st.session_state.chat_scoped_attachments
                )
            append_message("user", trigger_question)
            maybe_nudge_stale_free_agents(st.session_state.selected_league_id, st.session_state.data_merger)

            with st.spinner("Consulting the front office..."):
                if trigger_mode == "quant":
                    provider = role_providers["quant"]
                    append_message(
                        "quant",
                        llm_engine.ask_quant(
                            context, trigger_question, provider=provider, api_key=api_keys[provider],
                            model=role_models.get("quant") or None,
                        ),
                        provider=provider, model=role_models.get("quant") or None,
                    )
                elif trigger_mode == "beat":
                    provider = role_providers["beat"]
                    append_message(
                        "beat",
                        llm_engine.ask_beat(
                            context, trigger_question, provider=provider, api_key=api_keys[provider],
                            model=role_models.get("beat") or None,
                        ),
                        provider=provider, model=role_models.get("beat") or None,
                    )
                elif trigger_mode == "followup":
                    # A plain follow-up after a debate talks to the Moderator alone, using that
                    # debate's own reports and verdict as established context -- not every next
                    # message deserves the whole panel reconvened. The Moderator can recommend
                    # /debate in its own reply when a follow-up genuinely calls for it, but it
                    # never triggers that itself; only the user typing /debate does.
                    provider = role_providers["moderator"]
                    followup_text = llm_engine.ask_moderator_followup(
                        context, trigger_question,
                        last_debate["quant"], last_debate["beat"], last_debate["contrarian"], last_debate["moderator"],
                        provider=provider, api_key=api_keys[provider], model=role_models.get("moderator") or None,
                        personality=moderator_personality,
                    )
                    append_message("moderator", followup_text, provider=provider, model=role_models.get("moderator") or None)
                    process_moderator_output(followup_text, trigger_question)
                else:
                    result = llm_engine.run_debate(
                        context, trigger_question, role_providers=role_providers, api_keys=api_keys,
                        role_models=role_models, moderator_personality=moderator_personality,
                    )
                    append_message("quant", result.quant, provider=role_providers["quant"], model=role_models.get("quant") or None)
                    append_message("beat", result.beat, provider=role_providers["beat"], model=role_models.get("beat") or None)
                    append_message("contrarian", result.contrarian, provider=role_providers["contrarian"], model=role_models.get("contrarian") or None)
                    append_message("moderator", result.moderator, provider=role_providers["moderator"], model=role_models.get("moderator") or None)
                    process_moderator_output(result.moderator, trigger_question)
            # Without this, the question box's label (now dependent on whether a debate has
            # happened -- see default_trigger_mode above), the persona captions, and everything
            # else derived from chat_history keep showing what they were at the START of this
            # run until some later, unrelated interaction happens to trigger the next one.
            st.rerun()

        VERDICT_FIELD_LABELS = (
            "RECOMMENDATION", "CONVICTION", "REASON", "DISSENT", "RISK", "RECON",
            "PRICE CEILING", "ACTION ITEM", "TODO UPDATE", "TODO LIKELY RESOLVED",
        )

        def format_agent_content(role: str, content: str) -> str:
            """Escape first -- this was going straight into unsafe_allow_html unescaped,
            so a literal '<', '>', or '&' anywhere in an LLM response (plausible in
            ordinary analysis prose, e.g. "if X < Y") could silently break the block's
            rendering. For the Moderator specifically, also bold the structured verdict
            field labels so the fixed-format block reads as a scannable form instead of
            an undifferentiated wall of monospace text -- this is the single most-read
            piece of content in the app."""
            escaped = html.escape(content)
            if role == "moderator":
                pattern = r"(?m)^(" + "|".join(VERDICT_FIELD_LABELS) + r"):"
                escaped = re.sub(pattern, r"<strong>\1:</strong>", escaped)
            return escaped

        # Base label uses the role's *current* display name (a rename applies to its
        # whole history, same as a real name change) — the "(Provider)" suffix uses
        # whatever provider is stamped on THIS message, so a role reassigned to a
        # different provider later doesn't rewrite who actually answered past messages.
        # A custom name never REPLACES the role in the badge, only adds to it — "Dave"
        # renamed as Contrarian six months from now is meaningless on its own; the
        # role has to stay visible too.
        # "MODERATOR VERDICT" is reserved for a message with the full panel behind it (see
        # is_full_debate below) -- a quick follow-up reply is still the Moderator, but it isn't
        # a fresh verdict from Quant/Beat/Contrarian all weighing in, and shouldn't visually
        # claim to be one.
        _ROLE_BADGE_WORD = {"quant": "QUANT ANALYST", "beat": "BEAT TRACKER", "contrarian": "CONTRARIAN", "moderator": "MODERATOR"}
        def _badge_base(role: str) -> str:
            word = _ROLE_BADGE_WORD[role]
            name = role_names[role]
            return f"{word} · {name}" if name != bot_config.ROLE_INFO[role]["default_name"] else word
        ROLE_BADGE_BASE = {
            "quant": (_badge_base("quant"), "badge-quant"),
            "beat": (_badge_base("beat"), "badge-beat"),
            "contrarian": (_badge_base("contrarian"), "badge-contrarian"),
            "moderator": (_badge_base("moderator"), "badge-moderator"),
        }
        badge_map = {
            "user": ("You", "badge-user"),
            "summary": ("🧠 MEMORY SUMMARY", "badge-summary"),
            "notice": ("⚠️ NOTICE", "badge-notice"),
        }
        pinned_ts = pinned_messages.load_pinned_ts(st.session_state.selected_league_id) if st.session_state.selected_league_id else set()
        def _render_agent_msg(msg: dict, is_full_debate: bool = False) -> None:
            if msg["role"] in ROLE_BADGE_BASE:
                base_label, cls = ROLE_BADGE_BASE[msg["role"]]
                if msg["role"] == "moderator" and is_full_debate:
                    base_label = base_label.replace("MODERATOR", "MODERATOR VERDICT", 1)
                    cls = "badge-moderator-verdict"
                # Prefer the actual model string over the provider tier label -- more
                # informative, and doesn't assume only Claude/Gemini/ChatGPT ever exist.
                powered_by = msg.get("model") or (bot_config.PROVIDER_LABELS.get(msg.get("provider")) if msg.get("provider") else None)
                label = f"{base_label} · {powered_by}" if powered_by else base_label
            else:
                label, cls = badge_map.get(msg["role"], (msg["role"], "badge-user"))
            st.markdown(f'<span class="badge {cls}">{label}</span>', unsafe_allow_html=True)
            # A real st.button, not clickable HTML in the badge markup above -- raw HTML has no
            # bridge back into Python without a custom component. Deliberately not st.columns to
            # sit it next to the badge: nested columns inside this fixed-position dock container
            # are confirmed to compute width against the wrong basis and push content off-screen
            # (see the .st-key-debate_dock CSS notes) -- a small icon-only button on its own line
            # avoids that entirely instead of fighting it.
            ts = msg.get("ts")
            if ts is not None and st.session_state.selected_league_id:
                is_pinned = ts in pinned_ts
                if st.button(
                    "📍 Pinned" if is_pinned else "📌 Pin", key=f"pin_toggle_{ts}",
                    help="Unpin this message" if is_pinned else "Pin this message to keep it easy to find later",
                ):
                    pinned_messages.toggle_pin(st.session_state.selected_league_id, ts)
                    st.rerun()
            st.markdown(
                f'<div class="agent-block">{format_agent_content(msg["role"], msg["content"])}</div>',
                unsafe_allow_html=True,
            )

        # A Full Debate always appends exactly [quant, beat, contrarian, moderator] back to
        # back (see the trigger block above) -- group that run into one unit so the Moderator's
        # synthesis reads as the one answer, with the reports that fed it tucked behind a
        # toggle instead of three more full-size bubbles of equal visual weight. One visible
        # analyst, inspectable reasoning underneath, not a four-way transcript by default.
        display_units: list[dict] = []
        recent = st.session_state.chat_history[-40:]
        i = 0
        while i < len(recent):
            if (
                i + 3 < len(recent)
                and [recent[i + k]["role"] for k in range(4)] == ["quant", "beat", "contrarian", "moderator"]
            ):
                display_units.append({"kind": "debate", "detail": recent[i:i + 3], "moderator": recent[i + 3]})
                i += 4
            else:
                display_units.append({"kind": "single", "msg": recent[i]})
                i += 1

        # Bounded, independently-scrolling — a fixed dock can't just grow with the
        # transcript or it eats the whole screen. use_container_width on the block
        # below isn't a thing; st.container(height=...) is Streamlit's own native
        # scroll-region primitive, so lean on that instead of another CSS hack.
        with st.container(height=CHAT_HEIGHT_BY_LEVEL[dock_level]):
            for unit in reversed(display_units):
                if unit["kind"] == "single":
                    _render_agent_msg(unit["msg"])
                    continue
                _render_agent_msg(unit["moderator"], is_full_debate=True)
                detail_key = f"show_debate_detail_{unit['moderator']['ts']}"
                st.session_state.setdefault(detail_key, False)
                if st.button(
                    f"{'▾' if st.session_state[detail_key] else '▸'} Show the analysis behind this "
                    "(Quant / Beat Tracker / Contrarian)",
                    key=f"toggle_{detail_key}", use_container_width=True,
                ):
                    st.session_state[detail_key] = not st.session_state[detail_key]
                    st.rerun()
                if st.session_state[detail_key]:
                    for detail_msg in unit["detail"]:
                        _render_agent_msg(detail_msg)

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
                    notify("success", message)
                    st.rerun()
                else:
                    notify("warning", message)

