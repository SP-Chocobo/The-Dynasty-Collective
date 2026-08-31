"""
Fantasy Football Multi-LLM Command Center — Streamlit UI.

Sleeper Meets Claude: a dark, minimalist dashboard (Claude) accented with
functional sports-data color coding (Sleeper) — emerald for value surplus,
gold for taxi/bench alerts, crimson for injury flags — plus The Prytaneum, a
four-persona deliberation chamber (Quant, Beat, Contrarian, Moderator) — each
role's LLM provider is independently configurable, not fixed to a given brand.
"""

from __future__ import annotations

import base64
import dataclasses
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

import streamlit.components.v1 as components

import bot_benchmark
import bot_config
import bot_research
import decision_log
import depth_ratings
import design_system
import draft_board_ui
import draft_room
import draft_strategy
import league_standings
import lineup_optimizer
import lineup_readiness
import pick_debate
import pick_synthesis
import pinned_messages
import screen_context
import todo_log
import llm_engine
import trade_ledger_ui
from attachments import ATTACHMENTS_DIR, list_attachments, save_attachment, set_caption, set_scope, delete_attachment
from data_merger import (
    EXTERNAL_VALUES_DIR, GLOBAL_PROJECTIONS_DIR, PROJECTIONS_DIR, DataMerger, external_upload_targets,
    load_projection_file, recency_grade, remove_alias, save_alias,
)
from league_format import FORMAT_GUIDANCE, FORMAT_OPTIONS, STANDARD, get_format_override, set_format_override
from league_prefs import forget_league, get_prefs, move_league, sorted_leagues, toggle_archive
from player_universe import FLEX_SLOT_POSITIONS, available_players, build_player_universe, league_usable_positions, matching_players, player_name, player_position
from sleeper_client import SleeperAPIError, SleeperClient, compute_points_from_stats, find_roster_for_user, league_format_summary

# Friendly display labels for pick_synthesis.diff_snapshots' real field names -- presentation
# only, a straight lookup over an already-computed dict key, never a re-derivation of the
# number itself. See the Draft Room view's "What changed?" drawer.
_DRAFT_ROOM_DIFF_LABELS = {
    "universal_value": "Universal value", "need_bonus": "Roster need",
    "eligibility_bonus": "Lineup flexibility", "team_acquisition_value": "Acquisition value",
    "survival_probability": "Survival probability", "opportunity_cost": "Opportunity cost",
    "expected_value_of_waiting": "Value of waiting", "denial_value": "Denial value",
    "pick_necessity": "Pick necessity",
}

# Pure display lookups over pick_synthesis's already-computed necessity_label -- never a new
# tier boundary decided here (those live in pick_synthesis.NECESSITY_LABEL_THRESHOLDS).
_NECESSITY_COLOR_EMOJI = {
    "MUST TAKE": "🟣", "STRONG ACTION": "🔵", "PREFERRED": "🟢",
    "CLOSE CALL": "🟡", "LOW URGENCY": "🔴", "DOESN'T MATTER MUCH": "🔴",
}
_NECESSITY_BADGE_CLASS = {
    "MUST TAKE": "badge-necessity-must-take", "STRONG ACTION": "badge-necessity-strong",
    "PREFERRED": "badge-necessity-preferred", "CLOSE CALL": "badge-necessity-close-call",
    "LOW URGENCY": "badge-necessity-low", "DOESN'T MATTER MUCH": "badge-necessity-low",
}

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

_GLOBAL_CSS = """
    <style>
    __DESIGN_SYSTEM_ROOT_TOKENS__
    .stApp { background-color: #16171a; }
    __DESIGN_SYSTEM_BADGE_ROLE__
    /* Pick Necessity's own color ramp (Draft Room view) -- distinct classes from the debate
       personas above even though the colors are reused from that same palette, so a necessity
       tier is never visually confusable with a Quant/Beat/Contrarian/Moderator badge. Low to
       high necessity: red -> gold -> green -> blue -> purple. */
    __DESIGN_SYSTEM_BADGE_NECESSITY__
    .agent-block {
        border-radius: 8px; padding: 10px 14px; margin-bottom: 10px;
        background: #202124; border: 1px solid #2f3033;
    }
    /* Reasoning prose reads as an actual chat reply -- proportional font, not the
       monospace/pre-wrap treatment every message used to get regardless of whether it was
       free-flowing analysis or a fixed-format block. pre-line (not pre-wrap) still respects
       the LLM's own paragraph breaks without the typewriter look. */
    .agent-prose {
        white-space: pre-line;
        line-height: 1.55;
    }
    /* The structured verdict recap (RECOMMENDATION through any trailing SOURCE FINDING/
       COMPARISON lines) keeps the old monospace/pre-wrap "form" treatment, but now only for
       that fixed-format tail -- set apart from the conversational prose above it by a
       divider, instead of the two reading as one undifferentiated wall of typewriter text. */
    .agent-verdict {
        font-family: 'JetBrains Mono', 'DejaVu Sans Mono', monospace;
        white-space: pre-wrap;
        font-size: 0.9rem;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px dashed #3a3c42;
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

    /* The universal "Debate" doorway (render_debate_chip) -- reuses the exact understated
       treatment above rather than inventing a second "quiet secondary action" style, since
       the point here is the same: this control must never read as a peer to a surface's own
       primary/specialized actions (Moderator Review, Full Prytaneum, Debate This Pick).
       [class*="st-key-debate_chip_"] (not an exact match) is deliberate -- render_debate_chip
       is called from multiple surfaces with a different container key each time
       (debate_chip_trade_calculator, debate_chip_draft_room, ...), and this one rule has to
       cover all of them without a new CSS block per call site. The left border stands in for
       a literal divider between it and whatever primary actions sit in the same row. */
    [class*="st-key-debate_chip_"] .stButton button {
        background: transparent;
        border-color: #2a2b2e !important;
        border-left: 1px solid #3a3c42 !important;
        border-radius: 0 8px 8px 0 !important;
        color: #9ca3af;
        font-weight: 500;
    }
    [class*="st-key-debate_chip_"] .stButton button:hover {
        color: #7dd3fc;
        border-color: #0ea5e9 !important;
        background: rgba(14,165,233,0.06);
    }

    /* Sidebar defaults to a width that crowds the Manage Leagues row and the
       credentials paste box — widen it out of the box instead of making everyone
       drag it wider by hand every time. Still resizable from here if you want more.
       Scoped to aria-expanded="true" only: min-width beats max-width per the CSS
       spec, so an unscoped rule here fights Streamlit's own collapse (which sets
       max-width: 0 on the same element) and leaves a chunk of dead space and a
       sliver of visible sidebar even when "collapsed".
       Also scoped to a wide-enough viewport: at 700px this leaves 300px for actual
       content, still workable; on a real phone (~390px) this forced the sidebar WIDER
       than the entire screen -- confirmed live, an open sidebar's own content became
       unreachable, and (see .st-key-debate_dock below) the fixed dock's hardcoded
       "shift right by 400px when the sidebar's open" offset put it entirely off-screen
       too (x=400 on a 390px viewport). Below the breakpoint, Streamlit's own native
       responsive sidebar width (which adapts to the viewport) takes over instead. */
    @media (min-width: 700px) {
        [data-testid="stSidebar"][aria-expanded="true"] { min-width: 400px; }
    }

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
    /* Popover triggers never got the 44px touch-target sizing above -- they're a different
       component (stPopoverButton, not .stButton), so the app-wide rule never reached them even
       though the league switcher is a popover trigger sitting right next to a plain st.button
       (Refresh) that already got it. */
    [data-testid="stPopoverButton"] {
        min-height: 44px;
    }
    /* Same gap for the main Matchup/Roster Maintenance/League page nav specifically -- it's a
       segmented_control, rendered through stButtonGroup rather than .stButton, so it's stayed
       at Streamlit's smaller default this whole time despite being the single most-tapped
       control in the app. Scoped to this one control (not every segmented_control) since the
       others are occasional secondary settings, not primary navigation. */
    .st-key-main_view [data-testid="stButtonGroup"] button {
        min-height: 44px;
        font-weight: 600;
    }
    /* Draft Room UI-authority pass. Both Player Pool controls (Live + Mock) use
       st.segmented_control (same single-select semantics as the old st.radio, same
       options/default) styled as a compact filter bar in the board's own idiom: small
       mono-caps buttons, quiet until selected. Selected state uses --sky (the same "this
       control is engaged" signal the embedded board already uses for its own expanded-row
       state), deliberately never --emerald, which the necessity pills on the very same
       screen already use to mean "this candidate is a good value" -- one UI-state color,
       one analytical-signal color, never sharing a hue on a screen where both appear.
       segmented_control specifically because it's already this app's idiom for "exactly one
       of a few named exclusive choices" (main nav, Draft Room mode toggle). */
    .st-key-draft_room_pool_scope_control [data-testid="stButtonGroup"],
    .st-key-mock_draft_pool_scope_control [data-testid="stButtonGroup"] {
        gap: 6px;
        row-gap: 6px;
    }
    .st-key-draft_room_pool_scope_control button[data-variant="segmented_control"],
    .st-key-mock_draft_pool_scope_control button[data-variant="segmented_control"] {
        min-height: 30px;
        min-width: 0;
        padding: 4px 12px;
        font-family: 'JetBrains Mono', 'DejaVu Sans Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        background: #1b1c1f;
        border: 1px solid #2a2b2e !important;
        color: #6b7076;
        border-radius: 6px;
        transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease;
    }
    .st-key-draft_room_pool_scope_control button[data-variant="segmented_control"]:hover,
    .st-key-mock_draft_pool_scope_control button[data-variant="segmented_control"]:hover {
        border-color: #3a3c42 !important;
        color: #9ca3af;
    }
    .st-key-draft_room_pool_scope_control button[data-variant="segmented_control"][data-selected="true"],
    .st-key-mock_draft_pool_scope_control button[data-variant="segmented_control"][data-selected="true"] {
        background: rgba(14,165,233,0.10);
        border-color: #0ea5e9 !important;
        color: #7dd3fc;
    }
    /* Refresh Picks previously had no styling of its own -- a bare st.button, so it fell back
       to the app-wide default (full container width, generic large touch-target box), making
       it read as the loudest thing in the toolbar despite being a secondary, occasional sync
       action next to the quiet Player Pool segmented control. Restyled as a sibling of that
       same control (identical height/font/border/radius language) rather than a big CTA box,
       and no longer stretched to its column's full width. */
    .st-key-draft_room_refresh_btn button {
        width: auto !important;
        min-height: 30px;
        padding: 4px 12px;
        font-family: 'JetBrains Mono', 'DejaVu Sans Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        background: #1b1c1f;
        border: 1px solid #2a2b2e !important;
        color: #6b7076;
        border-radius: 6px;
        transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease;
    }
    /* Quiet at rest, same sky-blue language ALL PLAYERS' selected state uses on hover/focus
       (a shared visual family), but never a PERSISTENT blue outline -- Refresh is a
       one-shot action, not a selected state, and an always-on blue border would incorrectly
       imply it's "currently active" the way a segmented-control selection is. A stronger,
       briefly-held blue on :active gives real press feedback (the app-wide button
       :active scale/brightness rule only reaches stButtonGroup/popover triggers, not a bare
       .stButton like this one, so it needs its own). */
    .st-key-draft_room_refresh_btn button:hover,
    .st-key-draft_room_refresh_btn button:focus-visible {
        background: rgba(14,165,233,0.10);
        border-color: #0ea5e9 !important;
        color: #7dd3fc;
    }
    .st-key-draft_room_refresh_btn button:active {
        background: rgba(14,165,233,0.24);
        border-color: #0ea5e9 !important;
        color: #bae6fd;
        transform: scale(0.96);
    }
    /* Position filter, round 3: the multi-select itself was rejected -- a user can only ever
       be looking at one meaningful board view at a time (a real position, a real flex-slot
       view, or everything), never an arbitrary hand-picked SET of positions. Concept 1/3:
       the view control is the board's own title row ("CANDIDATES" ... current value),
       directly above the board, not grouped with Player Pool. No border, no chevron, no
       pill shape anywhere -- the current value's own typography (bold, brighter than the
       muted label beside it) is the only affordance that it's interactive. */
    .drv-board-title {
        font-family: 'JetBrains Mono', 'DejaVu Sans Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6b7076;
        white-space: nowrap;
        line-height: 1.5;
    }
    .drv-board-title .dot {
        color: #3a3c42;
        padding: 0 0.4em;
        font-weight: 400;
    }
    .st-key-draft_room_board_title_row,
    .st-key-mock_draft_board_title_row {
        margin-bottom: 2px;
    }
    .st-key-draft_room_board_title_row [data-testid="stColumn"],
    .st-key-mock_draft_board_title_row [data-testid="stColumn"] {
        margin-top: 0 !important;
    }
    /* This row is only ever two short words ("CANDIDATES" + the current view) -- it should
       never need Streamlit's default narrow-viewport behavior of stacking st.columns into a
       vertical list, which otherwise breaks the "one phrase" reading entirely below ~640px. */
    .st-key-draft_room_board_title_row [data-testid="stHorizontalBlock"],
    .st-key-mock_draft_board_title_row [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
    }
    .st-key-draft_room_board_title_row [data-testid="stColumn"]:nth-child(1),
    .st-key-mock_draft_board_title_row [data-testid="stColumn"]:nth-child(1),
    .st-key-draft_room_board_title_row [data-testid="stColumn"]:nth-child(2),
    .st-key-mock_draft_board_title_row [data-testid="stColumn"]:nth-child(2) {
        width: auto !important;
        min-width: 0 !important;
        flex: 0 0 auto !important;
    }
    .st-key-draft_room_view_toggle,
    .st-key-mock_draft_view_toggle {
        margin: 0 !important;
    }
    /* Round 3 refinement, take 2: a bordered tag box (matching draft_board_ui.py's .tag
       language) read as its own separate pill sitting apart from "CANDIDATES" instead of
       one continuous phrase with it -- explicit, but disjointed. Dropped the box entirely:
       the current value is now bare bold text picking up the same bright ink as the
       "CANDIDATES" label is muted, directly abutting the bullet with no gap of its own, so
       "CANDIDATES • ALL" reads as a single unit and only the brightness/weight signals
       "this part is interactive." No border, no background, no chevron. */
    .st-key-draft_room_view_toggle button,
    .st-key-mock_draft_view_toggle button {
        min-height: 0 !important;
        width: auto !important;
        display: inline-flex !important;
        align-items: baseline !important;
        padding: 0 !important;
        margin: 0 !important;
        background: transparent !important;
        border: none !important;
        font-family: 'JetBrains Mono', 'DejaVu Sans Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        line-height: 1.5;
        color: #e5e7eb;
        text-align: left;
        justify-content: flex-start !important;
        border-bottom: 2px solid transparent;
        border-radius: 0;
        transition: color 0.15s ease, border-color 0.15s ease;
    }
    .st-key-draft_room_view_toggle button:hover,
    .st-key-mock_draft_view_toggle button:hover {
        color: #7dd3fc;
        border-bottom-color: #0ea5e9;
    }
    /* The button's own visible text sits inside Streamlit's stMarkdownContainer -> <p>,
       which carries its own hardcoded 14px/21px line box that does NOT inherit the
       font-size/line-height set on the <button> above -- left alone, that mismatched taller
       line box is exactly what put "ALL" a few px below the "CANDIDATES" baseline despite
       both elements sharing the same top edge. Match it explicitly so the two truly share
       one line. */
    .st-key-draft_room_view_toggle button p,
    .st-key-mock_draft_view_toggle button p {
        font-size: 0.72rem !important;
        line-height: 1.5 !important;
        font-weight: 700 !important;
        letter-spacing: 0.03em !important;
        margin: 0 !important;
    }
    /* Concept 3, refined: the expanded surface is a single horizontal row of bare-text
       options (never boxed pills, never a vertical list stacking the whole page down) that
       unfolds directly beneath the title row in normal document flow, and collapses back to
       just the tag the instant an option is picked -- so the at-rest state is always only
       "CANDIDATES - ALL", never a lingering open panel. */
    .st-key-draft_room_view_menu,
    .st-key-mock_draft_view_menu {
        border-top: 1px solid #2a2b2e;
        margin-top: 8px;
        padding-top: 10px;
        margin-bottom: 10px;
    }
    .st-key-draft_room_view_menu button,
    .st-key-mock_draft_view_menu button {
        width: auto !important;
        min-height: 0;
        padding: 4px 2px;
        background: transparent !important;
        border: none !important;
        font-family: 'JetBrains Mono', 'DejaVu Sans Mono', monospace;
        font-size: 0.8rem;
        font-weight: 500;
        letter-spacing: 0.03em;
        color: #8b8f98;
        text-align: left;
        justify-content: flex-start !important;
        border-radius: 0;
        transition: color 0.15s ease;
    }
    .st-key-draft_room_view_menu button:hover,
    .st-key-mock_draft_view_menu button:hover {
        color: #e5e7eb;
    }
    .st-key-draft_room_view_menu [class*="st-key-draft_room_view_opt_active_"] button,
    .st-key-mock_draft_view_menu [class*="st-key-mock_draft_view_opt_active_"] button {
        color: #7dd3fc;
        font-weight: 700;
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

    /* The Prytaneum's dock: fixed to the bottom of the viewport (not "sticky" — sticky
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
       rendered width, tracking its expanded/collapsed state via :has().
       Matches the sidebar's own min-width breakpoint above: below 700px the sidebar
       is back to Streamlit's native (narrower, viewport-responsive) width, so a fixed
       400px offset would push the dock off-screen on a real phone -- confirmed live,
       x=400 on a 390px viewport, completely unreachable. Below the breakpoint the dock
       just stays flush left regardless of sidebar state; a brief visual overlap with an
       open sidebar on a narrow phone is a real tradeoff, but strictly better than the
       dock being categorically unusable. */
    @media (min-width: 700px) {
        body:has([data-testid="stSidebar"][aria-expanded="true"]) .st-key-debate_dock { left: 400px; }
    }
    body:has([data-testid="stSidebar"][aria-expanded="false"]) .st-key-debate_dock { left: 0; }
    @media (max-width: 699.98px) {
        .st-key-debate_dock { left: 0 !important; }
    }


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
    """

st.markdown(
    _GLOBAL_CSS
    .replace("__DESIGN_SYSTEM_ROOT_TOKENS__", design_system.root_css_block())
    .replace("__DESIGN_SYSTEM_BADGE_ROLE__", design_system.BADGE_ROLE_CSS)
    .replace("__DESIGN_SYSTEM_BADGE_NECESSITY__", design_system.BADGE_NECESSITY_CSS),
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


# SleeperClient()/DataMerger() are real work (DataMerger() alone measured ~115ms -- it loads
# and merges every baseline/external CSV) -- a dict literal's values are all evaluated eagerly
# before the loop below even checks whether the key is already set, so this used to construct
# fresh instances of both on literally every single rerun (every button click, every widget
# interaction) and immediately throw them away when the key already existed. Constructed
# directly, guarded individually, before the cheap-default loop.
if "sleeper_client" not in st.session_state:
    st.session_state.sleeper_client = SleeperClient()
if "data_merger" not in st.session_state:
    st.session_state.data_merger = DataMerger()

for key, default in {
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
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        # Written on every single message (see append_message/save_chat_history below), so
        # this is the single most write-frequent file in the app -- an interrupted write
        # (browser closed mid-save, disk full) leaving invalid JSON here used to crash the
        # whole app on next load, with no way back in short of manually deleting the file.
        # Back the corrupt file up (never overwrite silently) before treating history as
        # empty, so a whole league's chat/decision/objective trail isn't just gone -- the
        # very next save would otherwise overwrite it with a fresh empty history.
        backup = path.with_name(f"{path.stem}_corrupt_{int(time.time())}{path.suffix}")
        try:
            path.rename(backup)
        except OSError:
            pass
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


def process_moderator_output(
    moderator_text: str, trigger_question: str, provider: str = "", model: str = "",
) -> None:
    """Shared post-processing for any Moderator response that might carry the structured
    verdict block -- both a fresh debate and a lighter follow-up (see
    llm_engine.ask_moderator_followup) can produce one. No-ops cleanly on plain conversational
    text: parse_moderator_verdict returns {} for that, and every consumer below is already a
    safe no-op on an empty/falsy input, so a "just talking it through" follow-up doesn't spam
    the decision log or to-do list with nothing."""
    verdict = llm_engine.parse_moderator_verdict(moderator_text) if not moderator_text.startswith("⚠️") else {}
    decision_log.log_decision(
        st.session_state.selected_league_id, trigger_question, verdict, moderator_text,
        provider=provider, model=model,
    )
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
    #
    # A bare #(\d+) scan also matches a source's own rank citation ("ranked #1 DL", "#3 WR",
    # "#1 overall RB") -- confirmed live, that pattern is everywhere in SOURCE FINDING lines
    # and ordinary prose discussing where a source ranks a player -- which would mark an
    # unrelated objective "referenced" just because its id happened to equal someone's rank
    # number. SOURCE FINDING/SOURCE COMPARISON lines are skipped entirely (their whole point is
    # a source's own rank), and both rank-citation shapes ("ranked #N" and "#N <position>",
    # optionally with "at/in/overall" between them) are stripped from every other line before
    # scanning, so only an actual bare "#N" reference is left to match.
    _rank_mention_re = re.compile(
        r"(?i)\brank(?:ed)?\s+#\d+\b|#\d+\s+(?:at\s+|in\s+|overall\s+)?"
        r"(?:QB|RB|WR|TE|K|DEF|LB|DL|DB)\b"
    )
    mentioned_ids: set[int] = set()
    for line in moderator_text.splitlines():
        if line.strip().upper().startswith(("SOURCE FINDING:", "SOURCE COMPARISON:")):
            continue
        mentioned_ids.update(int(n) for n in re.findall(r"#(\d+)", _rank_mention_re.sub("", line)))
    for active_item in todo_log.load_todos(st.session_state.selected_league_id, statuses=todo_log.ACTIVE_STATUSES):
        if active_item["id"] in mentioned_ids:
            todo_log.mark_referenced(st.session_state.selected_league_id, active_item["id"])


def find_last_debate(chat_history: list[dict]) -> Optional[dict[str, str]]:
    """The most recent Full Prytaneum round's four reports, if any -- lets a follow-up talk to
    the Moderator with something real to reference instead of answering blind. A Full Prytaneum
    run always appends exactly [quant, beat, contrarian, moderator] back to back (see the trigger
    block below), so that exact role run is the signature to scan for, most recent first.

    A round where any of the four calls actually failed (a missing/invalid API key, a provider
    outage -- see llm_engine's fail-soft "⚠️ ..." convention) is skipped entirely rather than
    handed to a follow-up as real context: the Moderator's own verdict is only as good as the
    reports underneath it, and an error string standing in for a "report" isn't something a
    follow-up should be built on. Falls through to an earlier valid round if one exists, or
    None (a fresh full debate) if every round on record was broken."""
    for i in range(len(chat_history) - 4, -1, -1):
        if [chat_history[i + k]["role"] for k in range(4)] == ["quant", "beat", "contrarian", "moderator"]:
            contents = [chat_history[i + k]["content"] for k in range(4)]
            if any(c.startswith("⚠️") for c in contents):
                continue
            return {
                "quant": contents[0], "beat": contents[1],
                "contrarian": contents[2], "moderator": contents[3],
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
    """Make this league the one shown across the dashboard and The Prytaneum — loads its
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
        # table-layout:fixed (render_header=False, see below) gives every column an equal,
        # often narrow share of the width -- without truncation a long value just overflows
        # its cell and visually overlaps its neighbor instead of respecting that width, so
        # clip it with an ellipsis there. Auto layout (render_header=True) sizes each column
        # to its content already, so nothing to truncate in that case.
        cell_overflow_style = "overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" if not render_header else ""
        cells = "".join(
            f'<td style="padding:9px 14px;border-bottom:1px solid #202124;{cell_overflow_style}">{_cell_html(c, row[c])}</td>'
            for c in display_cols
        )
        row_parts.append(f"<tr>{cells}</tr>")

    # The conditional thead has to stay on the same line as <table ...> — a
    # standalone blank line here (which is what render_header=False produces,
    # since the whitespace-only line has no visible content) terminates
    # CommonMark's raw-HTML-block parsing early, and everything after gets
    # re-parsed as an indented code block instead of rendered HTML.
    thead_html = f"<thead><tr>{headers}</tr></thead>" if render_header else ""
    # render_header=False means the caller already laid down its own header row as real
    # st.columns(len(display_cols)) buttons directly above this table (the Free Agents
    # sort row is the one caller that does this) -- st.columns splits that row into
    # exactly equal widths. Left on the default 'auto' table-layout, this table's own
    # <td> widths are sized by cell content instead, and the two independently-computed
    # column grids drift apart (confirmed: a wide "name" column here vs. a padding-only
    # header button pushed everything after it out of alignment). table-layout:fixed
    # forces this table's columns equal too, matching the header row above it exactly.
    # Skipped when this table renders its own <th> row (render_header=True) -- there,
    # header and body share one table already, so they can never misalign, and forcing
    # equal widths would just squeeze a genuinely wide column like "name" for no reason.
    table_style = "width:100%;border-collapse:collapse;font-size:0.88rem;"
    if not render_header:
        table_style += "table-layout:fixed;"
    st.markdown(
        f"""
        <div style="overflow-x:auto;overflow-y:auto;max-height:600px;
                    border:1px solid #2a2b2e;border-radius:10px;">
          <table style="{table_style}">{thead_html}
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


def render_debate_chip(context: "screen_context.ScreenContext", key: str) -> None:
    """The universal, quiet "💬 Debate" doorway (see the design-language reference's
    Contextual Debate section) -- attaches `context` as the dock's current ScreenContext and
    reveals the dock (collapsed -> partial) if it's currently collapsed. Deliberately does
    NOT write question_input and does NOT run a debate itself: opening and asking are two
    separate actions on purpose, so a user can see what the panel already knows before
    deciding whether to ask it anything. Visually a quiet utility control (see the
    [class*="st-key-debate_chip_"] CSS rule), never a peer to whatever specialized
    escalation buttons (Moderator Review, Full Prytaneum, Debate This Pick) a surface
    already has -- `key` just needs to be unique per call site (one per surface)."""
    with st.container(key=f"debate_chip_{key}"):
        if st.button(
            "💬 Debate", key=f"debate_chip_btn_{key}",
            help=screen_context.UNIVERSAL_DEBATE_HELP,
        ):
            st.session_state.debate_attached_context = context
            if st.session_state.get("debate_dock_level", "partial") == "collapsed":
                st.session_state.debate_dock_level = "partial"
            st.rerun()


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


def build_context(
    snapshot: dict, roster_table: list[dict], player_universe: list[dict], question: str = "",
    conversation_window: Optional[list[dict]] = None,
) -> str:
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
    if conversation_window is not None:
        # A caller centering context on one specific past message (the 🎯 "Add as objective"
        # action) needs messages surrounding THAT message -- both what led into it and what
        # came after -- not necessarily the tail end of the whole conversation, which wouldn't
        # even include anything after an older message at all. See that handler below for how
        # this window gets built.
        recent_msgs = [m for m in conversation_window if m.get("role") not in ("summary", "notice")]
    else:
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
    # Dynasty Rankings and the Trade Value Chart both ship as a committed baseline (see
    # DataMerger/GLOBAL_PROJECTIONS_DIR) -- is_loaded/is_trade_values_loaded are unconditionally
    # true now regardless of any live upload, so those two never actually read NOT LOADED here
    # anymore. Free Agent Finder has no baseline (it's tied to one league's live roster), so
    # that one's still a real either/or.
    lines.append("  - Draft Sharks Dynasty Rankings: loaded")
    lines.append(f"  - Draft Sharks Free Agent Finder: {'loaded' if merger.is_free_agents_loaded else 'NOT LOADED'}")
    lines.append(
        "  - Draft Sharks Trade Value Chart (rookie pick slot values, future pick values, player values): loaded"
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
        # merger.is_loaded is unconditionally true now (the committed baseline covers Dynasty
        # Rankings regardless of any live upload -- see DataMerger/GLOBAL_PROJECTIONS_DIR), so
        # this no longer needs a body-count-only fallback branch for the case where it isn't.
        lines.append(
            "\nLEAGUE-WIDE POSITIONAL DEPTH (per team: rostered player COUNT at each position, with "
            "total Draft Sharks trade value in parens where matched -- weigh the value figure over "
            "the count: three replacement-level backups and three stacked stars both read as \"3\" "
            "by count alone, but are not remotely the same depth):"
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

        st.markdown("**Add a League by ID**")
        st.caption(
            "Sync Leagues only lists what Sleeper's own `/user/.../leagues` endpoint returns for "
            "this account -- a league where you're rostered but haven't formally accepted the "
            "invite in the Sleeper app yet (common for a freshly-created, still-pre-draft league) "
            "can be a real member without showing up there. Paste the league ID directly (the "
            "number in its Sleeper URL, after /leagues/) to add it regardless."
        )
        manual_league_id = st.text_input(
            "League ID", key="manual_league_id_input", label_visibility="collapsed",
            placeholder="e.g. 1191596293294161920",
        )
        if st.button("Add League", key="add_league_by_id", use_container_width=True):
            manual_league_id = manual_league_id.strip()
            if not manual_league_id:
                notify("warning", "Paste a league ID first.")
            else:
                client: SleeperClient = st.session_state.sleeper_client
                try:
                    found_league = client.get_league(manual_league_id)
                except SleeperAPIError as exc:
                    notify("error", f"Couldn't reach Sleeper: {exc}")
                    found_league = None
                if found_league is None:
                    notify("error", f"No league found for ID '{manual_league_id}'.")
                else:
                    if not any(lg["league_id"] == manual_league_id for lg in st.session_state.leagues):
                        st.session_state.leagues.append(found_league)
                    activate_league(manual_league_id)
                    notify("success", f"Added {found_league.get('name', manual_league_id)}.")
                    st.rerun()

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
                _fetched = st.session_state.get(f"available_models_{_provider_choice}")
                _current_model = _role_models_cfg[_role]
                if _fetched:
                    st.caption("MODEL (optional)")
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
                    # SUGGESTED_MODELS is just an illustrative hint (Claude's own entries are
                    # kept current; Gemini/OpenAI's are whatever this app shipped with, since
                    # there's no live-verified way to know their current lineup without an API
                    # call) -- shown only here, before that call has actually happened for this
                    # provider. Once "Refresh available models" above has run, the real fetched
                    # list becomes the selectbox itself, so repeating a possibly-stale example
                    # alongside accurate live data would be redundant at best, wrong at worst.
                    st.caption(f"MODEL (optional — e.g. {', '.join(bot_config.SUGGESTED_MODELS[_provider_choice])})")
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
                            # Recorded by run_benchmark but deliberately NOT scored (see
                            # bot_benchmark.MACHINE_CONTRACT_PARSERS): a candidate can win this
                            # rubric and still fail the structured block four production
                            # consumers depend on. Surfaced here so it is visible to whoever
                            # presses Apply, rather than discovered later as four systems
                            # quietly doing nothing.
                            if _cand.get("any_contract_failure"):
                                _warn += " ⚠️ did not emit the required structured verdict block"
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

    # DynastyProcess/FantasyPros/KeepTradeCut only ever ship as the committed baseline export --
    # unlike Draft Sharks' own data above, this app had no path at all for a user to refresh
    # them short of a code change. external_upload_targets() names the exact filename each
    # source's composite rule expects (see _EXTERNAL_PERCENTILE_RULES) -- overwriting that
    # exact file keeps it reading as one continuous source rather than an untracked second
    # copy that would double-count it. ESPN isn't offered here: its baseline export is
    # redraft-scope and deliberately excluded from the composite already (same reasoning as
    # FantasyPros' best_ball_rankings.csv), so there's nothing for an upload to feed.
    _EXT_SOURCE_LABELS = {"dynastyprocess": "DynastyProcess", "fantasypros": "FantasyPros", "keeptradecut": "KeepTradeCut"}
    with st.expander("🔄 External Valuation Sources", expanded=False, key="sb_group_external"):
        st.caption(
            "DynastyProcess, FantasyPros, and KeepTradeCut all ship a committed baseline export "
            "that only ever updates via a code change today. Refresh one here with a fresher CSV "
            "from that same source, in the same column shape as the baseline file — it replaces "
            "that source's data outright rather than adding a second copy alongside it."
        )
        _ext_targets = external_upload_targets()
        _ext_source = st.selectbox(
            "Source", options=list(_ext_targets.keys()),
            format_func=lambda s: _EXT_SOURCE_LABELS.get(s, s.title()), key="ext_source_pick",
        )
        _ext_filename = _ext_targets[_ext_source]
        _ext_file = st.file_uploader(
            f"{_EXT_SOURCE_LABELS.get(_ext_source, _ext_source)} CSV", type=["csv"], key="ext_source_upload",
            help=f"Must have the same columns as the baseline export (saved as {_ext_filename}) -- "
            "at minimum a 'name' column, since that's all load_external_values assumes universally.",
        )
        if _ext_file is not None and st.button("Update this source", key="ext_source_apply"):
            try:
                _ext_df = pd.read_csv(_ext_file)
            except Exception as exc:
                notify("error", f"Couldn't read that as a CSV: {exc}")
            else:
                if "name" not in _ext_df.columns:
                    notify("error", f"That file has no 'name' column — doesn't look like a {_EXT_SOURCE_LABELS.get(_ext_source, _ext_source)} export.")
                else:
                    dest_dir = EXTERNAL_VALUES_DIR / _ext_source
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    (dest_dir / _ext_filename).write_bytes(_ext_file.getvalue())
                    st.session_state.data_merger.reload()
                    notify("success", f"Updated {_EXT_SOURCE_LABELS.get(_ext_source, _ext_source)}'s data — the composite score will use it from here on.")

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

    # One glanceable overall read before the per-source breakdown below -- baseline data (or
    # whatever's live) keeps driving every answer regardless of this grade, so it's informational
    # only, not a gate. Reuses build_freshness_manifest, already computed for the Moderator's own
    # DATA FRESHNESS context, rather than a second staleness calculation living only in the UI.
    _freshness_entries = build_freshness_manifest(st.session_state.league_snapshot or {}, merger)
    if _freshness_entries:
        _worst_age = max((age for _, _, age in _freshness_entries if age is not None), default=None)
        _grade = recency_grade(_worst_age)
        _grade_ok = _grade in ("Fresh", "Recent")
        _grade_icon = "✅" if _grade_ok else ("⚠️" if _grade in ("Aging", "Stale") else "○")
        _grade_cls = "status-ok" if _grade_ok else "status-bad"
        st.markdown(f'<span class="{_grade_cls}">{_grade_icon} Data Freshness: {_grade}</span>', unsafe_allow_html=True)
        st.caption("Oldest of everything loaded below sets this grade — update on your own schedule, nothing here blocks the app.")

    # Free agent pool staleness is its own glanceable line, separate from the overall grade
    # above -- it's the one staleness read that's specifically about who's actually available
    # on waivers right now, not the rankings data behind player values.
    if merger.is_free_agents_loaded:
        fa_age = merger.free_agents_staleness_days
        fa_ok = not merger.free_agents_is_stale
        fa_age_label = f"({fa_age}d ago)" if fa_age is not None else ""
        st.markdown(status_line(f"Free Agent Pool {fa_age_label}", fa_ok), unsafe_allow_html=True)
    else:
        st.markdown(status_line("Free Agent Pool", False), unsafe_allow_html=True)

    with st.expander("Data Sources & Connections", expanded=False):
        if merger.is_loaded:
            age = merger.staleness_days
            age_label = f"updated {merger.freshest_date} ({age}d ago)" if age is not None else "updated (unknown date)"
            ds_cls = "status-bad" if merger.is_stale else "status-ok"
            ds_icon = "⚠️" if merger.is_stale else "✅"
            # The committed baseline (data/baseline/rankings/) means this is ALWAYS true now, even
            # with zero live uploads -- a checkmark that's permanently green regardless of anything
            # the user does carries no real signal. Checking GLOBAL_PROJECTIONS_DIR directly (rather
            # than adding a new DataMerger flag for a purely cosmetic distinction) says which state
            # this actually is: your own fresher upload, or still running on baseline alone.
            has_live_upload = GLOBAL_PROJECTIONS_DIR.exists() and any(
                p.suffix.lower() in (".csv", ".json", ".pdf") for p in GLOBAL_PROJECTIONS_DIR.iterdir()
            )
            source_note = "" if has_live_upload else " (baseline)"
            st.markdown(f'<span class="{ds_cls}">{ds_icon} DS Projections Loaded{source_note} — {age_label}</span>', unsafe_allow_html=True)
            if merger.is_stale:
                st.caption(f"Data is {age}+ days old — consider re-exporting from Draft Sharks (weekly is plenty).")
            elif not has_live_upload:
                st.caption("Running on the committed baseline — upload your own export anytime for fresher or format-specific numbers.")
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

        # Draft Sharks status above covers only that one vendor -- the composite score draws on up
        # to 4 more (see COMPOSITE_SOURCE_WEIGHTS), so this line is the only place their load state
        # is visible at all rather than something a user has to trust is working silently.
        SOURCE_DISPLAY_NAMES = {
            "dynastyprocess": "DynastyProcess", "fantasypros": "FantasyPros",
            "keeptradecut": "KeepTradeCut", "espn": "ESPN", "bot_research": "Bot Research",
        }
        # composite_capable_source_names() (not just every source_name present in
        # external_values) -- confirmed live, ESPN's only baseline file is redraft-scope and
        # structurally excluded from the composite entirely, yet this line used to count it as
        # one of the "N composite sources loaded" just because its rows existed at all.
        composite_sources = merger.composite_capable_source_names() if merger.is_external_values_loaded else []
        if composite_sources:
            names = [SOURCE_DISPLAY_NAMES.get(s, s.title()) for s in composite_sources]
            st.markdown(status_line(f"Composite Sources Loaded ({len(names)})", True), unsafe_allow_html=True)
            st.caption(", ".join(names))
        else:
            st.markdown(status_line("Composite Sources Loaded", False), unsafe_allow_html=True)

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

        st.markdown("---")
        # Role is the primary read here, not the provider -- which model backs which role is a
        # Configure Bots assignment that can change at any time, so leading with "Claude Connected"
        # would describe today's wiring as if it were permanent. The provider only shows up as a
        # secondary "via <name>" caption, for whoever's troubleshooting a missing key.
        _role_providers_for_status = bot_config.load_role_providers()
        _role_names_for_status = bot_config.load_role_names()
        _roles_using = {
            provider: [
                _role_names_for_status[role] for role in bot_config.ROLES if _role_providers_for_status[role] == provider
            ]
            for provider in bot_config.PROVIDERS
        }
        for _role in bot_config.ROLES:
            _provider = _role_providers_for_status[_role]
            _ok = IS_PROVIDER_CONFIGURED[_provider](api_key_for(PROVIDER_KEY_FIELD[_provider]))
            st.markdown(status_line(f"{_role_names_for_status[_role]} Connected", _ok), unsafe_allow_html=True)
            st.caption(f"via {bot_config.PROVIDER_LABELS[_provider]}")

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
                    st.caption("Switch which league the dashboard and The Prytaneum below are showing.")
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
# Several Draft Sharks Dynasty Rankings exports cover the SAME players under different format
# assumptions (PPR/standard, superflex/1QB, TE premium) -- without this, DataMerger has no way
# to know which one applies to THIS league, and silently let whichever file sorted last by
# mtime win for everyone (confirmed: one real player's trade_value swung ~2.7x purely on that
# accident). Cheap no-op when nothing's changed since the last rerun -- see set_league_format.
_scoring_key = {"Full PPR": "ppr", "Half PPR": "half_ppr", "Standard": "standard"}.get(fmt["scoring"], "ppr")
st.session_state.data_merger.set_league_format(
    {"scoring": _scoring_key, "superflex": fmt["superflex"], "te_premium": fmt["te_premium"]}
)
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
    if fmt["scoring"] == "Half PPR":
        # Real, disclosed data limitation (not a bug): the committed Draft Sharks baseline has
        # no dedicated Half-PPR rankings export -- only Standard, Full PPR, and their
        # superflex/TE-premium variants exist (see data/baseline/rankings/). set_league_format
        # above already picks the closest available file rather than leaving the league
        # unscored, and _rankings_format_match_score's own docstring has always documented that
        # choice -- this is just making it visible here too, not changing what the engine does.
        # Confirmed directly: a Half-PPR and a Full-PPR board are byte-identical today (same
        # file wins the match every time), so a Half-PPR league is quietly getting Full-PPR
        # valuations rather than something built for its own scoring.
        st.caption(
            "ℹ️ No dedicated Half PPR rankings source exists yet — using Full PPR as the "
            "closest available approximation. Values may run slightly high for this league's "
            "actual scoring."
        )

MATCHUP_VIEW = "🏈 Matchup"
MAINTENANCE_VIEW = "🔧 Roster Maintenance"
DRAFT_VIEW = "📋 Draft Room"
LEAGUE_VIEW = "👥 League"
# A cross-surface crosslink (e.g. League's "Open in Trade Calculator", F6) can't set
# st.session_state.main_view directly from inside another view's branch -- that branch runs
# AFTER this segmented_control has already been instantiated this run, and Streamlit forbids
# writing a widget's key post-instantiation. So a crosslink stashes the destination here instead
# (a plain, non-widget key) and reruns; this is the one place that consumes it, before the
# widget below is created, which is exactly when setting it is safe.
if st.session_state.get("pending_main_view"):
    st.session_state.main_view = st.session_state.pop("pending_main_view")
main_view = st.segmented_control(
    "Dashboard view",
    options=[MATCHUP_VIEW, MAINTENANCE_VIEW, DRAFT_VIEW, LEAGUE_VIEW],
    default=MATCHUP_VIEW,
    key="main_view",
    label_visibility="collapsed",
    # Primary navigation, not a filter -- clicking the already-active pill must not be able to
    # deselect it into None. Without this, main_view could go None (confirmed: segmented_control
    # allows a single-select to be toggled off), and the four view branches below being a plain
    # if/elif/elif/elif chain (rather than the implicit-else catch-all it used to be) means a
    # None main_view would now render nothing at all instead of silently falling into League.
    required=True,
    help="Matchup: your lineup, projections, and The Prytaneum for start/sit calls. "
    "Roster Maintenance: free agents/waivers and reference material for trade and pickup research. "
    "Draft Room: live startup/rookie draft pick recommendations. "
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
# the persistent Prytaneum band below needs it too, not just the Matchup view.
if main_view == MATCHUP_VIEW:
    # Readiness strip (front door, "is there a problem?") over a position-grouped roster
    # (body, "where, and what's there?") -- the settled Matchup concept merge. This is
    # deliberately NOT a start/sit recommendation: lineup_readiness only ever states facts
    # already computed elsewhere (filled slots, starter injury flags, this team's own
    # depth_ratings judgment) -- see that module's own docstring for why the harder
    # "what should I actually do" question stays a separate, parked concept.
    st.subheader("Lineup Readiness")
    if not roster:
        st.warning("Couldn't find a roster owned by this user in this league.")
    else:
        depth = positional_depth(player_universe, merger)
        owner_labels = roster_owner_names(snapshot)
        my_team_label = owner_labels.get(roster["roster_id"])
        total_starting_slots = len(lineup_optimizer.slots_from_roster_positions(league.get("roster_positions") or []))
        readiness = lineup_readiness.compute_readiness(roster_table, depth, my_team_label, total_starting_slots)

        def _readiness_chip(label: str, tone: str) -> str:
            color = {"ok": "var(--emerald-b)", "warn": "var(--gold-b)", "bad": "var(--crimson-b)"}[tone]
            icon = {"ok": "✅", "warn": "⚠️", "bad": "⚠️"}[tone]
            return (
                f'<span style="display:inline-flex;align-items:center;gap:.35rem;'
                f"font-family:'JetBrains Mono',monospace;font-size:.78rem;border-radius:5px;"
                f'padding:.3rem .6rem;margin:0 .5rem .5rem 0;color:{color};'
                f'border:1px solid {color};background:rgba(255,255,255,.03);">{icon} {label}</span>'
            )

        slots_ok = readiness["filled_starting_slots"] >= readiness["total_starting_slots"]
        chips = [_readiness_chip(
            f"{readiness['filled_starting_slots']}/{readiness['total_starting_slots']} starting slots filled",
            "ok" if slots_ok else "bad",
        )]
        if readiness["starter_injury_flags"]:
            names = ", ".join(f["name"] for f in readiness["starter_injury_flags"][:3])
            extra = len(readiness["starter_injury_flags"]) - 3
            label = f"{len(readiness['starter_injury_flags'])} starter(s) flagged: {names}"
            if extra > 0:
                label += f" +{extra} more"
            chips.append(_readiness_chip(label, "warn"))
        if readiness["thin_positions"]:
            pos_list = ", ".join(p["position"] for p in readiness["thin_positions"])
            chips.append(_readiness_chip(f"Thin at {pos_list}", "warn"))
        st.markdown(f'<div>{"".join(chips)}</div>', unsafe_allow_html=True)

        st.markdown(trade_ledger_ui.TRADE_LEDGER_CSS, unsafe_allow_html=True)
        st.markdown(trade_ledger_ui.freshness_pill(merger.is_stale, merger.staleness_days), unsafe_allow_html=True)
        st.caption(
            "Tier, VORP, and the thin-position read above come from your loaded Draft Sharks "
            "data — check the freshness pill if something here looks off."
        )

        st.markdown("---")
        st.markdown("**Your Roster**")
        _position_order = ["QB", "RB", "WR", "TE", "K", "DEF", "LB", "DL", "DB"]
        positions_present = [p for p in _position_order if any(r["position"] == p for r in roster_table)]
        for r in roster_table:
            if r["position"] not in positions_present:
                positions_present.append(r["position"])

        flagged_positions = {p["position"] for p in readiness["thin_positions"]} | {
            f["position"] for f in readiness["starter_injury_flags"]
        }
        default_position = next((p for p in positions_present if p in flagged_positions), positions_present[0] if positions_present else None)
        st.session_state.setdefault("matchup_expanded_position", default_position)

        any_sleeper_proj = False
        for position in positions_present:
            group_rows = [r for r in roster_table if r["position"] == position]
            n_starters = sum(1 for r in group_rows if r["slot"] == "Starter")
            n_bench = len(group_rows) - n_starters
            is_open = st.session_state.matchup_expanded_position == position
            flag_marker = " ⚠️" if position in flagged_positions else ""
            arrow = "▾" if is_open else "▸"
            if st.button(
                f"{arrow} {position} ({n_starters} starting, {n_bench} bench){flag_marker}",
                key=f"matchup_group_btn_{position}", use_container_width=True,
            ):
                st.session_state.matchup_expanded_position = None if is_open else position
                st.rerun()
            if is_open:
                group_df = pd.DataFrame(group_rows)
                display_cols = [c for c in [
                    "name", "position", "team", "slot", "tier", "vorp",
                    "projection", "sleeper_proj", "proj_3yr", "trade_value", "pos_rank",
                    "fa_ros_proj", "fa_ceiling", "fa_value", "injury_status",
                ] if c in group_df.columns]
                render_styled_table(
                    group_df[display_cols],
                    pill_columns={"injury_status": _injury_pill_color, "position": _position_pill_color},
                    group_column="slot",
                    column_labels={"sleeper_proj": sleeper_proj_label(snapshot)},
                )
                any_sleeper_proj = any_sleeper_proj or "sleeper_proj" in group_df.columns

        matchup_chip_col, _ = st.columns([0.6, 2.4])
        with matchup_chip_col:
            render_debate_chip(
                screen_context.build_matchup_context(
                    roster_table, focus_position=st.session_state.matchup_expanded_position,
                ),
                key="matchup",
            )
        if any_sleeper_proj:
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

            # save_alias had no counterpart in the UI at all -- once set, an alias was
            # permanent short of manually editing data/player_aliases.json by hand, with no way
            # to even see what was currently mapped. remove_alias already existed in
            # data_merger.py for exactly this but was never wired to anything.
            if merger.aliases:
                with st.expander(f"Manual Aliases ({len(merger.aliases)})"):
                    st.caption("Overrides automatic matching for these players. Remove one to go back to auto-matching.")
                    for sleeper_name, ds_name in sorted(merger.aliases.items()):
                        alias_col, remove_col = st.columns([4, 1])
                        alias_col.markdown(f"**{sleeper_name}** → {ds_name}")
                        if remove_col.button("Remove", key=f"remove_alias_{sleeper_name}", use_container_width=True):
                            remove_alias(sleeper_name)
                            merger.reload()
                            notify("success", f"Removed the alias for '{sleeper_name}'.")
                            st.rerun()

elif main_view == MAINTENANCE_VIEW:
    # ------------------------------------------------------------------ attention ledger --
    # The settled Maintenance concept: N-C is the baseline (one lightweight strip, the existing
    # Free Agents / Trade Calculator / Reference Material sections completely unchanged
    # beneath it) -- deliberately not a restructure, since these three workflows share no
    # underlying data the way League's two lenses do. Every chip below is a direct read of a
    # fact some other part of this app already computes; this must never grow into a second
    # opinion/ranking engine (the concept doc's own guardrail on "top FA by need" -- resolved
    # here by reusing Matchup's exact "Thin at X" phrasing off the shared depth_ratings
    # judgment, rather than ranking free agents at all).
    _attn_chips: list[tuple[str, str]] = []
    if merger.is_free_agents_loaded and merger.free_agents_is_stale:
        _attn_chips.append(("warn", f"⚠️ FA data {merger.free_agents_staleness_days}d old"))
    _attn_uncaptioned = sum(1 for a in list_attachments() if not a["caption"].strip())
    if _attn_uncaptioned:
        _attn_chips.append(("info", f"📎 {_attn_uncaptioned} uncaptioned attachment(s)"))
    _attn_depth = positional_depth(player_universe, merger)
    _attn_my_team = roster_owner_names(snapshot).get(roster["roster_id"]) if roster else None
    if _attn_my_team and _attn_my_team in _attn_depth:
        _attn_thin = [
            pos for pos in sorted(_attn_depth[_attn_my_team])
            if depth_ratings.depth_label(
                _attn_depth[_attn_my_team].get(pos, {"count": 0, "value": None}),
                [teams[pos] for teams in _attn_depth.values() if pos in teams],
            ) in ("Weak", "None — no rostered players here")
        ]
        if _attn_thin:
            _attn_chips.append(("warn", f"Thin at {', '.join(_attn_thin)}"))

    if _attn_chips:
        _attn_tone_color = {"warn": "var(--gold-b)", "info": "var(--sky-b)"}
        _attn_chip_html = "".join(
            f'<span style="display:inline-flex;align-items:center;gap:.35rem;'
            f"font-family:'JetBrains Mono',monospace;font-size:.78rem;border-radius:5px;"
            f'padding:.3rem .6rem;margin:0 .5rem .5rem 0;color:{_attn_tone_color[tone]};'
            f'border:1px solid {_attn_tone_color[tone]};background:rgba(255,255,255,.03);">{text}</span>'
            for tone, text in _attn_chips
        )
        st.markdown(f"<div>{_attn_chip_html}</div>", unsafe_allow_html=True)
        st.caption("A quick read before you dig in below — everything here traces to a fact the sections beneath it already compute.")

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
            fa_chip_col, _ = st.columns([0.6, 2.4])
            with fa_chip_col:
                render_debate_chip(
                    screen_context.build_free_agents_context(fa_rows, fa_position_filter, fa_search),
                    key="free_agents",
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
    hcol1, hcol2 = st.columns([3, 1])
    hcol1.subheader("Trade Calculator")
    # Trade Value Chart first, Dynasty Rankings as the fallback -- same source-preference
    # order _price_trade_side below actually prices with, so this pill can never claim
    # "current" off a source the calculator isn't really using for a given asset.
    _tl_is_stale = merger.trade_values_is_stale if merger.is_trade_values_loaded else merger.is_stale
    _tl_age = merger.trade_values_staleness_days if merger.is_trade_values_loaded else merger.staleness_days
    hcol2.markdown(
        f'<div style="text-align:right;padding-top:.4rem">{trade_ledger_ui.freshness_pill(_tl_is_stale, _tl_age)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(trade_ledger_ui.TRADE_LEDGER_CSS, unsafe_allow_html=True)
    st.caption(
        "Browse both rosters below to build a trade, or just type freely — either way prices "
        "off data already loaded here. Dynasty trades aren't algebra, so treat this as a rough "
        "read, not a verdict: what it can't see (roster fit, a coach's usage pattern, next "
        "week's injury news) is exactly what the panel is for."
    )

    owner_labels = roster_owner_names(snapshot)
    my_team_label = owner_labels.get(roster["roster_id"]) if roster else None
    depth = positional_depth(player_universe, merger)
    other_team_labels = sorted({v for k, v in owner_labels.items() if v != my_team_label})
    trade_partner = st.selectbox(
        "Trading with (optional)", options=["Not specified"] + other_team_labels, key="trade_calc_partner",
        help="Adds their positional need to the context below, and lets you browse their roster "
        "below — purely optional, the calculator still works without it.",
    ) if other_team_labels else "Not specified"

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

    # Ambiguity used to be recomputed here: merge_player silently picked the first candidate
    # when several players shared a name_key and no position/team was given to disambiguate
    # (confirmed live -- a same-keyed "Jaylen Allen" resolved to "Josh Allen"'s value instead
    # of its own), and it returned nothing a caller could read, so this one caller counted
    # candidates itself. It reports match_verified now, so the count is gone and both branches
    # below read the resolution instead. Ambiguity is a property of the resolution, and a
    # consumer that has to re-derive it is a consumer that can forget to.

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
            if tvc_player.get("matched") and not tvc_player.get("match_verified", True):
                # external/composite above were resolved from the same unresolvable free
                # text as `value` -- whichever candidate merge_player/composite_player_score
                # silently picked is exactly as uncertain as the price the UI already hides
                # here (confirmed: an ambiguous line still had a specific player's real
                # composite score reach the panel's context, undermining the point of
                # flagging it as ambiguous at all). Drop both, same as value.
                #
                # This used to recompute name_key over the whole table to count candidates
                # itself, because merge_player returned no ambiguity at all. It does now, and
                # the returned flag is the better signal: it reflects the path the resolution
                # actually took, so an exact single-row hit is no longer flagged just because
                # some other row shares its key, and a fuzzy hit with several survivors IS
                # flagged where a key count saw nothing.
                rows.append({
                    "label": line, "value": None, "position": None, "source": None,
                    "ambiguous": True, "external": [], "composite": None,
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
                # path above, against the (larger) Dynasty Rankings pool this time -- read
                # off the resolution rather than recounted here, same as the branch above.
                if not rankings_player.get("match_verified", True):
                    # Same reasoning as the Trade Value Chart branch above -- don't leak a
                    # specific, unresolvable candidate's external/composite data either.
                    rows.append({
                        "label": line, "value": None, "position": None, "source": None,
                        "ambiguous": True, "external": [], "composite": None,
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

    # ---------------------------------------------------------- roster browse & select --
    # Click a roster row to add/remove it from the free-text box below -- the box (and
    # _price_trade_side above) stays the single source of truth for what's actually in the
    # trade; this is purely a "type this for me" convenience layered on top. Nothing here
    # re-implements pricing or matching: every asset's value comes from one call into
    # _price_trade_side itself, the exact same path a hand-typed line goes through.
    pick_ledger = build_pick_ledger(snapshot)

    def _roster_assets(team_label: Optional[str], roster_id: Optional[int]) -> list[dict]:
        if not team_label:
            return []
        assets: list[dict] = []
        for p in player_universe:
            if p.get("owner_name") != team_label or p.get("ownership") != "ROSTERED":
                continue
            priced = _price_trade_side(p["name"])[0]
            assets.append({
                "id": p["player_id"], "line": p["name"], "name": p["name"],
                "pos": p["position"], "team": p.get("team"), "value": priced["value"], "is_pick": False,
            })
        # Only picks this roster has ACQUIRED via trade are enumerable -- an untouched pick is
        # still just "their normal Nth-round pick" (see build_pick_ledger's own docstring),
        # with no modeled inventory of how many future rounds/years to list. Those stay
        # reachable through the free-text box below (e.g. "2027 Random Rd 1"), same as today.
        if roster_id is not None:
            for pick in pick_ledger.get(roster_id, {}).get("acquired", []):
                line = f"{pick.get('season')} Random Rd {pick.get('round')}"
                value = merger.pick_value(line) if merger.is_trade_values_loaded else None
                original = owner_labels.get(pick.get("roster_id"), f"Roster {pick.get('roster_id')}")
                assets.append({
                    "id": f"pick_{pick.get('season')}_{pick.get('round')}_{pick.get('roster_id')}",
                    "line": line, "name": f"{pick.get('season')} Rd {pick.get('round')} (via {original})",
                    "pos": "PICK", "team": None, "value": value, "is_pick": True,
                })
        assets.sort(key=lambda a: (a["value"] is None, -(a["value"] or 0)))
        return assets

    def _render_roster_panel(title: str, assets: list[dict], side: str, state_key: str) -> None:
        st.markdown(f"**{title}**")
        if not assets:
            st.caption("Nothing rostered here yet.")
            return
        filter_options = ["ALL"] + sorted({a["pos"] for a in assets})
        chosen = st.segmented_control(
            f"Filter — {title}", options=filter_options, default="ALL",
            key=f"tl_filter_{side}", label_visibility="collapsed",
        ) or "ALL"
        visible = assets if chosen == "ALL" else [a for a in assets if a["pos"] == chosen]
        current_lines = [ln.strip() for ln in st.session_state.get(state_key, "").splitlines() if ln.strip()]
        with st.container(height=280):
            for a in visible:
                is_added = a["line"] in current_lines
                bcol, ncol, vcol = st.columns([0.14, 0.58, 0.28])
                if bcol.button(
                    "✕" if is_added else "+", key=f"tl_btn_{side}_{a['id']}",
                    help="Remove from the trade" if is_added else "Add to the trade",
                ):
                    if is_added:
                        current_lines.remove(a["line"])
                    else:
                        current_lines.append(a["line"])
                    st.session_state[state_key] = "\n".join(current_lines)
                    st.rerun()
                label_html = trade_ledger_ui.asset_label_html(a["name"], a["pos"], a.get("team"), a["is_pick"])
                if is_added:
                    label_html = trade_ledger_ui.selected_tag_html(side) + label_html
                ncol.markdown(label_html, unsafe_allow_html=True)
                vcol.markdown(trade_ledger_ui.value_html(a["value"]), unsafe_allow_html=True)

    rp1, rp2 = st.columns(2)
    with rp1:
        _render_roster_panel(
            "Your Roster", _roster_assets(my_team_label, roster["roster_id"] if roster else None),
            "send", "trade_calc_send",
        )
    with rp2:
        if trade_partner != "Not specified":
            partner_roster_id = next((k for k, v in owner_labels.items() if v == trade_partner), None)
            _render_roster_panel(
                f"{trade_partner}'s Roster", _roster_assets(trade_partner, partner_roster_id),
                "receive", "trade_calc_receive",
            )
        else:
            st.markdown("**Their Roster**")
            st.caption("Pick a trading partner above to browse their roster.")
    st.caption("Click a row above to add or remove it below, or just type freely — both stay in sync.")

    tccol1, tccol2 = st.columns(2)
    trade_send_text = tccol1.text_area(
        "You send", key="trade_calc_send", height=110,
        placeholder="One player or pick per line, e.g.\nJa'Marr Chase\n2027 Random Rd 1",
    )
    trade_receive_text = tccol2.text_area(
        "You receive", key="trade_calc_receive", height=110, placeholder="One player or pick per line",
    )

    def _depth_label(team_label: Optional[str], position: str, override_cell: Optional[dict] = None) -> Optional[str]:
        """Strong/Average/Weak/None for one team's depth at one position, relative to the rest
        of the league at that position. override_cell lets a caller ask "what would this label
        be AFTER the trade" by passing a simulated {count, value} instead of the team's actual
        current one -- same peer comparison, just a hypothetical instead of the real cell.
        The judgment itself lives in depth_ratings.depth_label (shared with the League Depth
        Map, per Fable's F3 finding) so this stays a thin lookup, not a second opinion."""
        if not team_label:
            return None
        cells = [teams[position] for teams in depth.values() if position in teams]
        cell = override_cell if override_cell is not None else depth.get(team_label, {}).get(position, {"count": 0, "value": None})
        return depth_ratings.depth_label(cell, cells)

    trade_send_rows = _price_trade_side(trade_send_text)
    trade_receive_rows = _price_trade_side(trade_receive_text)
    sources_used = {r["source"] for r in trade_send_rows + trade_receive_rows if r["source"]}
    # Defaults for the "nothing typed yet" branch below, which never touches these -- the
    # ScreenContext build after this whole if/elif needs them defined in every path, not
    # just the branch that actually has rows to verdict on.
    raw_line = fit_line = overall = None

    if not sources_used and not (trade_send_rows or trade_receive_rows):
        # Draft Sharks data itself is never actually missing (the committed baseline covers
        # Dynasty Rankings and the Trade Value Chart regardless of any live upload) -- an empty
        # state here just means nothing's typed in either box yet.
        st.caption("Type a player or pick on either side above to see it priced.")
    elif trade_send_rows or trade_receive_rows:
        if not sources_used:
            st.caption(
                "Nothing below matched loaded data, so it's unpriced — check for a typo, or it's "
                "a player/pick not in what's loaded. The buttons below still work without a price; "
                "the panel can reason about a trade from market judgment alone."
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
            # Neither verdict is subordinate to the other -- this describes the RELATIONSHIP
            # between the two already-decided reads above, it never re-derives or averages
            # them into a single "real" answer. See trade_ledger_ui.overall_synthesis.
            overall = trade_ledger_ui.overall_synthesis(raw_verdict, fit_verdict)
            if overall:
                st.caption(f"**Overall:** {overall}")

        if position_detail:
            with st.expander("Positional depth detail"):
                for line in position_detail:
                    st.caption(line)

    def _describe_trade_side(rows: list[dict]) -> str:
        def _line(r: dict) -> str:
            if r.get("ambiguous"):
                # Distinct from a plain unmatched line -- the panel should know THIS one
                # matched multiple players/picks (so external/composite were deliberately
                # withheld, not just absent) rather than reading it as "not found at all."
                return f"  - {r['label']} (ambiguous -- matches multiple players/picks, unpriced)"
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
    # Built via the shared ScreenContext contract (see screen_context.py and the design-
    # language reference's "Contextual Debate" section) rather than a hand-concatenated
    # string, so the panel is handed the exact same Raw Value/Roster Fit/Overall reads the
    # UI just displayed above -- not just the raw priced lines with the verdicts re-derived
    # blind. raw_line/fit_line/overall are None whenever nothing above them fired (e.g.
    # nothing priced, or no touched positions); build_trade_context already treats that as
    # "no priced assets to compare yet" rather than requiring a caller-side guard here.
    trade_context = screen_context.build_trade_context(
        trade_partner=trade_partner,
        send_description=_describe_trade_side(trade_send_rows),
        receive_description=_describe_trade_side(trade_receive_rows),
        entities=[r["label"] for r in trade_send_rows + trade_receive_rows],
        raw_line=raw_line, fit_line=fit_line, overall=overall,
    )
    trade_question = trade_context.to_prompt_seed()

    bcol1, bcol2, bcol3 = st.columns([1, 1, 0.6])
    with bcol1:
        ask_moderator = st.button(
            "⚖️ Moderator Review", use_container_width=True, disabled=not _trade_ready,
            help="Fast interpretation of the deterministic evidence above — given the calculated "
            "balance and all available roster/context data, is this actually a good trade? A fresh "
            "Full Prytaneum run if there's no prior conversation in this chat to react to, otherwise "
            "a lightweight follow-up off it.",
        )
    with bcol2:
        ask_full_squad = st.button(
            "🔥 Full Prytaneum", type="primary", use_container_width=True, disabled=not _trade_ready,
            help="Deeper escalation — forces a fresh full deliberation (Quant → Beat Tracker → "
            "Contrarian → Moderator) on this exact trade, regardless of any prior conversation "
            "in this chat.",
        )
    with bcol3:
        render_debate_chip(trade_context, key="trade_calculator")
    if ask_moderator:
        # The Raw Value/Roster Fit/Overall reads are already IN trade_question (see
        # build_trade_context above) -- no need to ask the panel to re-derive them, just to
        # react to them.
        st.session_state["question_input"] = trade_question + "\n\nGiven everything above, is this actually a good trade?"
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

elif main_view == DRAFT_VIEW:
    # ------------------------------------------------------------------ draft room --
    # This view is deliberately a CONSOLE, not a chat -- the deterministic engine
    # (draft_room.py/draft_strategy.py/pick_synthesis.py) is the source of truth and this
    # block only ever renders numbers it already computed. The one exception worth naming
    # explicitly: percentage/string formatting of an already-computed number (e.g.
    # round(survival_probability * 100)) is presentation, not calculation -- the same
    # transformation pick_debate.py's own evidence formatting already applies. This view
    # never re-ranks, re-scores, or recomputes anything a backend module didn't already hand
    # it, including the positional filter below (a pure display filter over an already-built
    # snapshot's candidates -- it never changes what pick_synthesis narrowed to or what
    # pick_debate actually reasons over).
    st.subheader("Draft Room")
    st.session_state.setdefault("draft_room_picks_by_draft", {})
    st.session_state.setdefault("draft_room_last_snapshot", None)
    st.session_state.setdefault("draft_room_debate_result", None)
    st.session_state.setdefault("draft_room_pool_scope", "all")
    st.session_state.setdefault("mock_draft", None)
    st.session_state.setdefault("mock_draft_pool_scope", "all")
    st.session_state.setdefault("mock_draft_debate_result", None)
    st.session_state.setdefault("mock_draft_last_snapshot", None)
    st.session_state.setdefault("mock_draft_editing_index", None)

    # One header row for "what am I looking at" (Live/Mock) and "which draft" together --
    # the draft selector used to sit in its own full-width row much further down (only
    # reachable once roster/drafts data was already fetched), reading as an unexplained,
    # disconnected structural break between the mode toggle and the Refresh/Player Pool
    # controls below it (see REVIEW_LOG.md). mode_col is filled immediately below;
    # draft_picker_col stays an open placeholder -- a DeltaGenerator column handle stays
    # writable no matter when later in the script it's used -- and gets filled once the
    # Live Draft branch further down actually has drafts to offer, so both still render in
    # this same visual row.
    # Grouped tightly on the left (small gap between the two), trailing empty space absorbing
    # the rest of the row -- not edge-justified/spread across the full row width, which just
    # opens a dead gap in the middle at real screen widths. Same "group tight, let whitespace
    # trail" language the position-view tag and Refresh/Player Pool row already use.
    mode_col, draft_picker_col, _header_spacer_col = st.columns([3, 2, 5])
    with mode_col:
        draft_room_mode = st.radio(
            "Draft Room mode", options=["Live Draft (Sleeper)", "🧪 Mock Draft"],
            horizontal=True, key="draft_room_mode_radio", label_visibility="collapsed",
        )

    if draft_room_mode == "🧪 Mock Draft":
        # -------------------------------------------------------------- mock draft --
        # A practice draft entirely independent of any real Sleeper league/draft -- for
        # rehearsing strategy under a chosen format, or one that hasn't even been created
        # on Sleeper's side yet. Reuses the exact same engine calls as the live flow below
        # (compute_draft_board/build_snapshot/debate_pick) unchanged -- see
        # draft_room.build_mock_league's docstring for why a synthetic league dict slots in
        # with zero special-casing anywhere downstream.
        md = st.session_state.mock_draft
        if md is None:
            st.caption(
                "Set the format below and start a sandbox draft -- every other roster is "
                "auto-drafted by this same engine (each one's own best team_acquisition_value "
                "pick), so you only ever make your own picks."
            )
            _fmt_scoring_index = {"Standard": 0, "Half PPR": 1, "Full PPR": 2}.get(fmt["scoring"], 2)
            # Defaults mirror the currently-displayed league's own settings (team count, roster
            # size, scoring, superflex/TE premium/dynasty below) so a sandbox run starts as a
            # realistic stand-in for THIS league rather than a generic 12-team guess -- every
            # field stays a plain, editable widget, never locked to the league's actual value.
            _default_teams = min(max(int(fmt["teams"]), 4), 16)
            _default_rounds = min(max(len(league.get("roster_positions") or []) or 15, 1), 30)
            with st.form("mock_draft_settings_form"):
                st.markdown("**Mock Draft Settings**")
                s1, s2, s3 = st.columns(3)
                # Explicit keys throughout -- cfg_slot's max_value depends on cfg_teams's own
                # live value, and an auto-generated widget key (the default when key= is
                # omitted) is derived partly from a widget's own constructor args, so it can
                # shift out from under a pending value the moment a DEPENDENT widget's value
                # changes in the same render. Confirmed live: changing Teams from 12 to 4 in
                # the same submission silently dropped a staged "Your draft slot" edit back to
                # its default. An explicit, teams-independent key removes that fragility.
                cfg_teams = s1.number_input(
                    "Teams", min_value=4, max_value=16, value=_default_teams, step=1, key="mock_cfg_teams",
                )
                cfg_slot = s2.number_input(
                    "Your draft slot", min_value=1, max_value=int(cfg_teams), value=1, step=1, key="mock_cfg_slot",
                )
                cfg_rounds = s3.number_input(
                    "Rounds", min_value=1, max_value=30, value=_default_rounds, step=1, key="mock_cfg_rounds",
                )
                s4, s5 = st.columns(2)
                cfg_scoring_label = s4.radio(
                    "Scoring", ["Standard", "Half PPR", "Full PPR"], index=_fmt_scoring_index, horizontal=True,
                    key="mock_cfg_scoring",
                    help="Half PPR has no dedicated rankings source yet — the engine uses Full "
                    "PPR as the closest available approximation, so Half PPR and Full PPR "
                    "boards come out identical today.",
                )
                cfg_draft_type_label = s5.radio(
                    "Draft type", ["Snake", "Snake (3RR)", "Linear"], index=0, horizontal=True,
                    key="mock_cfg_draft_type",
                    help="3RR = 3rd Round Reversal: round 3 repeats round 2's reversed order, then normal alternation resumes.",
                )
                s6, s7, s8 = st.columns(3)
                cfg_superflex = s6.checkbox("Superflex", value=fmt["superflex"], key="mock_cfg_superflex")
                cfg_te_premium = s7.checkbox("TE Premium", value=fmt["te_premium"], key="mock_cfg_te_premium")
                cfg_dynasty = s8.checkbox(
                    "Dynasty rules (long-horizon adj.)", value=fmt["type"] == "Dynasty", key="mock_cfg_dynasty",
                )
                start_clicked = st.form_submit_button(
                    "🏁 Start Mock Draft", type="primary", use_container_width=True,
                )
            if start_clicked:
                cfg_scoring_key = {"Standard": "standard", "Half PPR": "half_ppr", "Full PPR": "ppr"}[cfg_scoring_label]
                cfg_draft_type_key = {"Snake": "snake", "Snake (3RR)": "3rr", "Linear": "linear"}[cfg_draft_type_label]
                mock_league = draft_room.build_mock_league(
                    teams=int(cfg_teams), superflex=cfg_superflex, scoring=cfg_scoring_key,
                    te_premium=cfg_te_premium, dynasty=cfg_dynasty,
                )
                round_1_order = [str(i) for i in range(1, int(cfg_teams) + 1)]
                st.session_state.mock_draft = {
                    "settings": {
                        "teams": int(cfg_teams), "my_slot": int(cfg_slot), "superflex": cfg_superflex,
                        "scoring_key": cfg_scoring_key, "scoring_label": cfg_scoring_label,
                        "te_premium": cfg_te_premium, "dynasty": cfg_dynasty, "rounds": int(cfg_rounds),
                        "draft_type": cfg_draft_type_key,
                    },
                    "league": mock_league,
                    "my_roster_id": str(int(cfg_slot)),
                    "pick_order": draft_strategy.generate_pick_order(
                        round_1_order, total_rounds=int(cfg_rounds), draft_type=cfg_draft_type_key,
                    ),
                    "picks": [],
                    "owner_names": {
                        str(i): ("You" if i == int(cfg_slot) else f"Team {i}") for i in range(1, int(cfg_teams) + 1)
                    },
                }
                st.rerun()
        else:
            settings = md["settings"]
            st.caption(
                f"{settings['teams']}-team · slot {settings['my_slot']} · "
                f"{'Superflex' if settings['superflex'] else '1QB'} · {settings['scoring_label']} · "
                f"{'TE Premium · ' if settings['te_premium'] else ''}{settings['rounds']} rounds · "
                f"{'Dynasty' if settings['dynasty'] else 'Redraft'} rules · "
                f"{ {'snake': 'Snake', '3rr': 'Snake (3RR)', 'linear': 'Linear'}.get(settings['draft_type'], settings['draft_type'].title()) }"
            )
            reset_col, scope_col = st.columns([1, 2])
            with reset_col:
                if st.button("🔄 Reset Mock Draft", key="mock_draft_reset_btn", use_container_width=True):
                    st.session_state.mock_draft = None
                    st.session_state.mock_draft_debate_result = None
                    st.session_state.mock_draft_last_snapshot = None
                    st.rerun()
            with scope_col:
                _mock_scope_by_key = {"all": "All players", "rookies_only": "Rookies only", "veterans_only": "Veterans only"}
                mock_pool_scope_label = st.segmented_control(
                    "Player pool", options=["All players", "Rookies only", "Veterans only"],
                    default=_mock_scope_by_key[st.session_state.mock_draft_pool_scope],
                    required=True, key="mock_draft_pool_scope_control",
                )
                st.session_state.mock_draft_pool_scope = {
                    "All players": "all", "Rookies only": "rookies_only", "Veterans only": "veterans_only",
                }[mock_pool_scope_label]

            # The mock's chosen format can differ from whatever real league is active
            # elsewhere in the app -- re-point the shared DataMerger at it for this
            # render only; the real league's own format gets reasserted at the top of
            # every rerun (see set_league_format's call site above), so nothing else
            # this session reads ever sees the mock's format leak into it.
            st.session_state.data_merger.set_league_format({
                "scoring": settings["scoring_key"], "superflex": settings["superflex"],
                "te_premium": settings["te_premium"],
            })

            if len(md["picks"]) < len(md["pick_order"]):
                with st.spinner("Simulating opponent picks..."):
                    md["picks"] = draft_room.simulate_opponent_picks(
                        md["picks"], md["pick_order"], md["my_roster_id"], settings["teams"],
                        merger, players_db, md["league"], pool_scope=st.session_state.mock_draft_pool_scope,
                    )

            if md["picks"]:
                with st.expander(f"📋 Picks so far ({len(md['picks'])})"):
                    pick_rows = [{
                        "Pick": f"{p['round']}.{(i % settings['teams']) + 1:02d}",
                        "Team": md["owner_names"].get(str(p["roster_id"]), str(p["roster_id"])),
                        "Player": player_name(players_db.get(str(p["player_id"])) or {}, str(p["player_id"])),
                    } for i, p in enumerate(md["picks"])]
                    st.dataframe(pd.DataFrame(pick_rows), hide_index=True, use_container_width=True)

                # Your Roster So Far -- a pure display read over md["picks"] + players_db
                # (name/position lookups only, same as pick_rows above). No lineup-slot
                # assignment or other roster-construction logic lives here -- that's
                # lineup_optimizer's job, not this prototype's.
                my_picks_so_far = [p for p in md["picks"] if str(p["roster_id"]) == str(md["my_roster_id"])]
                if my_picks_so_far:
                    with st.expander(f"🧢 Your Roster So Far ({len(my_picks_so_far)})"):
                        roster_rows = [{
                            "Round": p["round"],
                            "Player": player_name(players_db.get(str(p["player_id"])) or {}, str(p["player_id"])),
                            "Pos": player_position(players_db.get(str(p["player_id"])) or {}) or "—",
                        } for p in my_picks_so_far]
                        st.dataframe(pd.DataFrame(roster_rows), hide_index=True, use_container_width=True)
                        pos_counts: dict[str, int] = {}
                        for row in roster_rows:
                            pos_counts[row["Pos"]] = pos_counts.get(row["Pos"], 0) + 1
                        st.caption(" · ".join(f"{pos} x{n}" for pos, n in sorted(pos_counts.items())))

                # Change a previous pick -- reuses build_snapshot at an earlier target_index,
                # exactly the same call every other board in this app makes, just pointed at a
                # past index. Everything after the edited pick is discarded and re-simulated
                # fresh (simulate_opponent_picks is a stateless, replay-safe function of "picks
                # so far" by its own design -- see its docstring), rather than trying to
                # reconcile which later picks would "still make sense," which would mean
                # inventing logic this app doesn't have. Only your OWN past picks are editable
                # here: rewriting an opponent's historical pick would need a different call path
                # (compute_draft_board directly, not build_snapshot, which is inherently scoped
                # to my_roster_id's own acquisition value) -- a real gap, left open rather than
                # worked around.
                if my_picks_so_far and st.session_state.mock_draft_editing_index is None:
                    with st.expander("✏️ Change a previous pick"):
                        edit_options = {
                            i: (
                                f"{p['round']}.{(i % settings['teams']) + 1:02d} — you took "
                                f"{player_name(players_db.get(str(p['player_id'])) or {}, str(p['player_id']))}"
                            )
                            for i, p in enumerate(md["picks"]) if str(p["roster_id"]) == str(md["my_roster_id"])
                        }
                        edit_choice = st.selectbox(
                            "Which pick?", options=list(edit_options.keys()),
                            format_func=lambda i: edit_options[i], key="mock_draft_edit_select",
                        )
                        st.caption(
                            "Changing this pick erases every pick made after it — yours and "
                            "every auto-drafted one — so the board re-simulates from this point "
                            "forward with the new player in place."
                        )
                        if st.button("Load this pick to edit", key="mock_draft_edit_load_btn"):
                            st.session_state.mock_draft_editing_index = edit_choice
                            st.session_state.mock_draft_debate_result = None
                            st.session_state.mock_draft_last_snapshot = None
                            st.rerun()

            editing_index = st.session_state.mock_draft_editing_index
            if editing_index is not None:
                # --------------------------------------------------- editing an earlier pick --
                edit_round = md["picks"][editing_index]["round"]
                edit_pick_label = f"{edit_round}.{editing_index % settings['teams'] + 1:02d}"
                try:
                    edit_snap = pick_synthesis.build_snapshot(
                        merger, players_db, md["picks"][:editing_index], md["pick_order"], editing_index,
                        md["my_roster_id"], md["league"], pick_label=edit_pick_label,
                        pool_scope=st.session_state.mock_draft_pool_scope,
                    )
                except Exception as exc:  # noqa: BLE001 -- surface, never crash the whole dashboard
                    edit_snap = None
                    notify("error", f"Couldn't rebuild the board at that pick: {exc}")

                if edit_snap is not None:
                    edit_payload = draft_board_ui.serialize_snapshot(
                        edit_snap, pick_header=f"EDITING — {edit_pick_label} (You)",
                        state_tags=["RE-DRAFTING FROM HERE"],
                    )
                    edit_height = min(180 + 92 * max(len(edit_snap.candidates), 1), 1400)
                    components.html(draft_board_ui.render_board_html(edit_payload), height=edit_height, scrolling=True)

                    edit_chip_col, _ = st.columns([0.6, 2.4])
                    with edit_chip_col:
                        render_debate_chip(screen_context.build_draft_room_context(edit_snap), key="mock_draft_edit")

                    edit_pick_options = {c.player_id: f"{c.name} ({c.position})" for c in edit_snap.candidates}
                    edit_chosen_pid = st.selectbox(
                        "Replace with", options=list(edit_pick_options.keys()),
                        format_func=lambda pid: edit_pick_options[pid], key="mock_draft_edit_pick_select",
                    )
                    edit_confirm_col, edit_cancel_col = st.columns(2)
                    with edit_confirm_col:
                        if st.button(
                            "✅ Confirm replacement", key="mock_draft_edit_confirm_btn",
                            type="primary", use_container_width=True,
                        ):
                            md["picks"] = md["picks"][:editing_index] + [{
                                "pick_no": editing_index + 1, "round": edit_round,
                                "roster_id": md["my_roster_id"], "player_id": edit_chosen_pid,
                            }]
                            st.session_state.mock_draft_editing_index = None
                            st.session_state.mock_draft_debate_result = None
                            st.session_state.mock_draft_last_snapshot = None
                            st.rerun()
                    with edit_cancel_col:
                        if st.button("✕ Cancel", key="mock_draft_edit_cancel_btn", use_container_width=True):
                            st.session_state.mock_draft_editing_index = None
                            st.rerun()

            if editing_index is None:
                current_index = len(md["picks"])
                if current_index >= len(md["pick_order"]):
                    st.success("Mock draft complete.")
                else:
                    mock_target_round = current_index // settings["teams"] + 1
                    mock_target_slot = current_index % settings["teams"] + 1
                    mock_pick_label = f"{mock_target_round}.{mock_target_slot:02d}"

                    try:
                        mock_snap = pick_synthesis.build_snapshot(
                            merger, players_db, md["picks"], md["pick_order"], current_index, md["my_roster_id"],
                            md["league"], pick_label=mock_pick_label, pool_scope=st.session_state.mock_draft_pool_scope,
                        )
                    except Exception as exc:  # noqa: BLE001 -- surface, never crash the whole dashboard
                        mock_snap = None
                        notify("error", f"Couldn't build the mock draft board: {exc}")

                    if mock_snap is not None and not mock_snap.candidates:
                        st.info("No candidates available in the current player pool/scope.")
                    elif mock_snap is not None:
                        mock_positions_present = sorted({c.position for c in mock_snap.candidates})
                        # Same board-view control as Live Draft (see REVIEW_LOG.md, round 3) --
                        # Mock Draft and Live Draft are two modes of the same Draft Room
                        # surface, so the control has to feel identical switching between them.
                        # Exactly ONE view active at a time (a real position, a real flex-slot
                        # view, or ALL) -- never an arbitrary hand-picked set.
                        mock_view_options = draft_board_ui.position_view_options(
                            set(mock_positions_present), md["league"].get("roster_positions") or [],
                        )
                        mock_current_view = st.session_state.get("mock_draft_position_view", "ALL")
                        if mock_current_view not in mock_view_options:
                            mock_current_view = "ALL"
                            st.session_state.mock_draft_position_view = "ALL"

                        with st.container(key="mock_draft_board_title_row"):
                            mock_title_col, mock_value_col, _mock_spacer_col = st.columns(
                                [0.85, 1.2, 7.95], gap="xxsmall", vertical_alignment="top",
                            )
                            with mock_title_col:
                                st.markdown(
                                    '<div class="drv-board-title">CANDIDATES<span class="dot">•</span></div>',
                                    unsafe_allow_html=True,
                                )
                            with mock_value_col:
                                if st.button(
                                    draft_board_ui.position_view_label(mock_current_view),
                                    key="mock_draft_view_toggle",
                                    help="Board view -- display only, never changes what's analyzed, ranked, or scored.",
                                ):
                                    st.session_state.mock_draft_position_view_open = not st.session_state.get(
                                        "mock_draft_position_view_open", False
                                    )
                                    st.rerun()

                        if st.session_state.get("mock_draft_position_view_open", False):
                            with st.container(key="mock_draft_view_menu"):
                                # ONE row at any option count -- columns weighted by label, so
                                # SUPER FLEX gets the width it needs without "K" claiming the
                                # same. The reveal opens in place of the current-view tag; a
                                # second row would turn a discreet inline control into a block.
                                mock_opt_cols = st.columns(draft_board_ui.view_option_widths(mock_view_options))
                                for opt, mock_opt_col in zip(mock_view_options, mock_opt_cols):
                                    opt_key = (
                                        f"mock_draft_view_opt_active_{opt}" if opt == mock_current_view
                                        else f"mock_draft_view_opt_{opt}"
                                    )
                                    with mock_opt_col:
                                        if st.button(draft_board_ui.position_view_label(opt), key=opt_key):
                                            st.session_state.mock_draft_position_view = opt
                                            st.session_state.mock_draft_position_view_open = False
                                            st.rerun()

                        mock_filtered = draft_board_ui.filter_candidates_by_view(mock_snap.candidates, mock_current_view)
                        # The same production board component Live Draft Room renders
                        # (draft_board_ui + components.html) -- proving the redesigned board
                        # survives real, repeated, stateful interaction was the whole point of
                        # greenlighting this mock, not a second, plainer table living only here.
                        mock_display_snap = dataclasses.replace(mock_snap, candidates=tuple(mock_filtered))
                        mock_board_payload = draft_board_ui.serialize_snapshot(
                            mock_display_snap, pick_header=f"ON THE CLOCK — {mock_pick_label} (You)",
                            state_tags=[f"{settings['teams']}-team mock"],
                        )
                        mock_board_height = min(180 + 92 * max(len(mock_filtered), 1), 1400)
                        components.html(
                            draft_board_ui.render_board_html(mock_board_payload),
                            height=mock_board_height, scrolling=True,
                        )

                        mock_debate_col, mock_chip_col, _ = st.columns([1, 0.6, 2.4])
                        with mock_debate_col:
                            mock_debate_clicked = st.button(
                                "🎙️ Debate This Pick", key="mock_draft_debate_btn", type="primary",
                                use_container_width=True, help=screen_context.DRAFT_ROOM_PICK_DEBATE_HELP,
                            )
                        with mock_chip_col:
                            render_debate_chip(screen_context.build_draft_room_context(mock_snap), key="mock_draft")
                        if mock_debate_clicked:
                            mock_debate_api_keys = {
                                "claude": api_key_for("anthropic"), "gemini": api_key_for("gemini"),
                                "openai": api_key_for("openai"),
                            }
                            with st.spinner("Strategist, Skeptic, and Caller are debating..."):
                                mock_debate_result = pick_debate.debate_pick(
                                    mock_snap, previous_snapshot=st.session_state.mock_draft_last_snapshot,
                                    api_keys=mock_debate_api_keys,
                                )
                            st.session_state.mock_draft_last_snapshot = mock_snap
                            st.session_state.mock_draft_debate_result = mock_debate_result
                            if mock_debate_result.errors:
                                notify("warning", "Debate finished with issues: " + "; ".join(mock_debate_result.errors))

                        mock_debate_result = st.session_state.mock_draft_debate_result
                        mock_current_debate = (
                            mock_debate_result
                            if (mock_debate_result is not None and mock_debate_result.pick_label == mock_pick_label)
                            else None
                        )
                        if mock_current_debate is not None:
                            st.markdown("---")
                            mock_rec = mock_current_debate.recommended
                            if mock_rec is None:
                                st.warning("The panel's recommendation didn't cleanly match a candidate -- see the raw reports below.")
                            else:
                                st.markdown(f"## Recommendation: {mock_rec.name}")
                                if mock_current_debate.confidence:
                                    st.caption(f"Confidence: {mock_current_debate.confidence}")
                                if mock_current_debate.why:
                                    st.markdown(f"**Why now?** {mock_current_debate.why}")

                                mock_necessity_class = _NECESSITY_BADGE_CLASS.get(mock_rec.necessity_label, "badge-necessity-close-call")
                                mock_necessity_emoji = _NECESSITY_COLOR_EMOJI.get(mock_rec.necessity_label, "")
                                mock_badge_col, mock_market_col = st.columns([1, 2])
                                with mock_badge_col:
                                    st.markdown(
                                        f'<span class="badge {mock_necessity_class}">{mock_necessity_emoji} PICK NECESSITY: '
                                        f'{mock_rec.pick_necessity:.0f}/100 — {mock_rec.necessity_label}</span>',
                                        unsafe_allow_html=True,
                                    )
                                if mock_rec.reach_label is not None:
                                    with mock_market_col:
                                        st.caption(
                                            f"Market consensus (KeepTradeCut, trade-value not literal ADP): "
                                            f"rank {mock_rec.consensus_rank}, tier {mock_rec.consensus_tier} — **{mock_rec.reach_label}**"
                                        )

                                mock_metric_row1 = st.columns(6)
                                mock_metric_row1[0].metric("Universal Value", f"{mock_rec.universal_value:.0f}")
                                mock_metric_row1[1].metric(
                                    "Projected Points", f"{mock_rec.projected_points:.0f}" if mock_rec.projected_points is not None else "—",
                                )
                                mock_metric_row1[2].metric("Your Acquisition Value", f"{mock_rec.team_acquisition_value:.0f}")
                                mock_metric_row1[3].metric(
                                    "Survival to Next Pick",
                                    f"{round(mock_rec.survival_probability * 100)}%" if mock_rec.survival_probability is not None else "—",
                                )
                                mock_metric_row1[4].metric("Positional Cliff", mock_rec.positional_cliff["tier"] if mock_rec.positional_cliff else "—")
                                mock_metric_row1[5].metric(f"{mock_rec.position} Run", "DETECTED" if mock_rec.position_run_detected else "—")

                                mock_metric_row2 = st.columns(3)
                                mock_metric_row2[0].metric("Opportunity Cost of Waiting", mock_rec.opportunity_cost if mock_rec.opportunity_cost is not None else "—")
                                mock_metric_row2[1].metric("Expected Value If You Wait", mock_rec.expected_value_of_waiting if mock_rec.expected_value_of_waiting is not None else "—")
                                mock_metric_row2[2].metric("Denial Value", mock_rec.denial_value if mock_rec.denial_value else "—")

                                mock_alt = mock_current_debate.best_alternative
                                if mock_alt is not None:
                                    st.markdown(f"**Best alternative:** {mock_alt.name} — {mock_alt.team_acquisition_value:.0f} acquisition value")

                            if mock_current_debate.disagreements:
                                for d in mock_current_debate.disagreements:
                                    st.warning(f"⚠️ Panel flagged a possible issue with an input: **{d['term']}** — {d['reason']}")

                        st.markdown("#### Make Your Pick")
                        mock_draft_options = {c.player_id: f"{c.name} ({c.position})" for c in mock_filtered}
                        mock_default_pid = None
                        if mock_current_debate is not None and mock_current_debate.recommended is not None:
                            mock_default_pid = mock_current_debate.recommended.player_id
                        if mock_default_pid not in mock_draft_options:
                            mock_default_pid = next(iter(mock_draft_options), None)
                        mock_option_ids = list(mock_draft_options.keys())
                        mock_chosen_pid = st.selectbox(
                            "Player to draft", options=mock_option_ids, format_func=lambda pid: mock_draft_options[pid],
                            index=mock_option_ids.index(mock_default_pid) if mock_default_pid in mock_option_ids else 0,
                            key="mock_draft_pick_select",
                        )
                        if st.button("✅ Draft This Player", key="mock_draft_confirm_btn", type="primary"):
                            md["picks"].append({
                                "pick_no": current_index + 1, "round": mock_target_round,
                                "roster_id": md["my_roster_id"], "player_id": mock_chosen_pid,
                            })
                            st.session_state.mock_draft_debate_result = None
                            st.session_state.mock_draft_last_snapshot = None
                            st.rerun()
    elif not roster:
        st.info("No roster found for your account in this league yet -- sync your username in the sidebar.")
    else:
        draft_client: SleeperClient = st.session_state.sleeper_client
        my_roster_id = str(roster.get("roster_id"))

        try:
            drafts = draft_client.get_drafts(st.session_state.selected_league_id)
        except SleeperAPIError as exc:
            drafts = []
            notify("error", f"Couldn't reach Sleeper for draft data: {exc}")

        if not drafts:
            st.info("No draft found for this league on Sleeper yet.")
        else:
            draft_options = {d["draft_id"]: d for d in drafts}
            ordered_draft_ids = sorted(
                draft_options, key=lambda did: draft_options[did].get("start_time") or 0, reverse=True,
            )

            def _draft_label(did: str) -> str:
                d = draft_options[did]
                return f"{d.get('season', '?')} · {d.get('type', 'draft')} · {d.get('status', '?')}"

            with draft_picker_col:
                draft_id = st.selectbox(
                    "Draft", options=ordered_draft_ids, format_func=_draft_label,
                    key="draft_room_draft_picker", label_visibility="collapsed",
                )
            active_draft = draft_options[draft_id]
            draft_type = active_draft.get("type")
            # Sleeper marks 3rd Round Reversal on the draft's own settings, not the type
            # string -- a "snake" draft with reversal_round == 3 is really a 3RR draft, and
            # treating it as plain snake poisons every pick-order-derived signal (survival,
            # opportunity cost, denial, necessity) worst in rounds 2-4. See
            # draft_strategy.generate_pick_order's own docstring.
            if draft_type == "snake" and (active_draft.get("settings") or {}).get("reversal_round") == 3:
                draft_type = "3rr"

            if draft_type not in ("snake", "linear", "3rr"):
                st.warning(
                    f"Draft Room currently supports snake/linear pick-order drafts only -- this "
                    f"draft is type '{draft_type}' (e.g. auction), where a fixed pick order doesn't apply."
                )
            else:
                total_rounds = (active_draft.get("settings") or {}).get("rounds")
                draft_order_map = active_draft.get("draft_order") or {}
                if not total_rounds or not draft_order_map:
                    st.info("This draft's pick order/round count isn't set on Sleeper's side yet.")
                else:
                    uid_to_roster_id = {
                        str(r.get("owner_id")): str(r.get("roster_id")) for r in (snapshot.get("rosters") or [])
                    }
                    slot_order = sorted(draft_order_map.items(), key=lambda kv: kv[1])
                    round_1_order = [uid_to_roster_id.get(str(uid)) for uid, _slot in slot_order]
                    if any(rid is None for rid in round_1_order):
                        st.caption("⚠️ Couldn't map every drafter to a roster in this league -- pick-order analysis may be incomplete.")
                        round_1_order = [rid for rid in round_1_order if rid is not None]

                    # Grouped tightly (Refresh, then Player Pool right after it), trailing empty
                    # space absorbing the rest of the row -- same "group tight, let whitespace
                    # trail" language the header row above already uses, rather than Player Pool
                    # starting wherever its wide column happened to begin.
                    top_row_col1, top_row_col2, _top_row_spacer_col = st.columns([1.5, 3.5, 5], vertical_alignment="center")
                    with top_row_col1:
                        if st.button("↻ Refresh Picks", key="draft_room_refresh_btn"):
                            try:
                                fetched_picks = draft_client.get_draft_picks(draft_id)
                                st.session_state.draft_room_picks_by_draft[draft_id] = fetched_picks
                                notify("success", f"Pulled {len(fetched_picks)} pick(s) from Sleeper.")
                            except SleeperAPIError as exc:
                                notify("error", f"Couldn't reach Sleeper: {exc}")
                    with top_row_col2:
                        # A separate "PLAYER POOL" label read as redundant -- the three options
                        # themselves (ALL PLAYERS / ROOKIES ONLY / VETERANS ONLY) already say
                        # what this control is without a caption naming it. Label collapsed
                        # entirely rather than replaced with an inline one.
                        _scope_by_key = {"all": "All players", "rookies_only": "Rookies only", "veterans_only": "Veterans only"}
                        pool_scope_label = st.segmented_control(
                            "Player pool", options=["All players", "Rookies only", "Veterans only"],
                            default=_scope_by_key[st.session_state.draft_room_pool_scope],
                            required=True, key="draft_room_pool_scope_control",
                            label_visibility="collapsed",
                            help="Rookies only / Veterans only is detected from KeepTradeCut's own source data, not a maintained list.",
                        )
                        st.session_state.draft_room_pool_scope = {
                            "All players": "all", "Rookies only": "rookies_only", "Veterans only": "veterans_only",
                        }[pool_scope_label]

                    draft_picks = st.session_state.draft_room_picks_by_draft.get(draft_id, [])
                    pick_order = draft_strategy.generate_pick_order(round_1_order, total_rounds=total_rounds, draft_type=draft_type)
                    num_teams = len(round_1_order)
                    current_index = len(draft_picks)

                    # This used to run on as a permanent inline caption between the toolbar and
                    # the board -- administrative prose about the draft's own state that
                    # interrupted the flow from controls straight to the candidates. Moved onto
                    # a "?" tag directly on the board's own state-tags row instead (see
                    # board_tags below), next to the "N pick(s) to your next selection" tag it's
                    # actually a caveat about -- available on hover, not permanently occupying
                    # the page.
                    draft_state_caveat = (
                        f"{len(draft_picks)} pick(s) made · {num_teams} teams · {total_rounds} rounds. "
                        "Pick order assumes no picks have been traded within this draft -- a traded "
                        "future pick may show the original owner's needs instead of the new owner's."
                    )

                    if current_index >= len(pick_order):
                        st.success("Draft complete.")
                    else:
                        target_index = draft_strategy.find_next_pick_index(pick_order, my_roster_id, current_index - 1)
                        if target_index is None:
                            st.info("You have no more picks remaining in this draft.")
                        else:
                            target_round = target_index // num_teams + 1
                            target_slot = target_index % num_teams + 1
                            pick_label = f"{target_round}.{target_slot:02d}"
                            is_live = target_index == current_index
                            owner_names_by_id = {str(k): v for k, v in roster_owner_names(snapshot).items()}

                            league_for_engine = {
                                "roster_positions": league.get("roster_positions"),
                                "scoring_settings": league.get("scoring_settings"),
                                "total_rosters": league.get("total_rosters"),
                                "settings": league.get("settings"),
                            }

                            # Flag a Player was removed (see REVIEW_LOG.md) -- Sleeper already has
                            # its own player-watchlist feature, and this control's real function
                            # (forcing one specific player into the fully-analyzed candidate set via
                            # user_selected_player_id, even if the board wouldn't otherwise surface
                            # him) had no UI trigger left to reach it once removed, so build_snapshot
                            # below is now always called with the default (None).

                            # build_snapshot is the single most expensive call in this view (a full
                            # board computation plus one opponent board per intervening roster) --
                            # unconditionally recomputing it on EVERY script rerun meant an
                            # unrelated action anywhere else on the page (the Prytaneum dock's own
                            # Expand/Collapse buttons, which call a bare st.rerun() purely to change
                            # a CSS height) paid that same cost for no reason. Cached in session
                            # state against exactly the inputs that can actually change the result --
                            # not a blanket st.cache_data, since draft_picks/merger/players_db aren't
                            # cheaply hashable and don't need to be; a plain equality check on a
                            # small key tuple is enough. picks length + the merger's own freshest
                            # source date are the same two staleness signals snapshot_is_current
                            # already uses elsewhere in this module -- reused here, not reinvented.
                            snapshot_cache_key = (
                                draft_id, target_index, str(my_roster_id),
                                st.session_state.draft_room_pool_scope,
                                len(draft_picks), merger.freshest_date,
                            )
                            cached = st.session_state.get("draft_room_snapshot_cache")
                            if cached is not None and cached[0] == snapshot_cache_key:
                                snap = cached[1]
                            else:
                                try:
                                    snap = pick_synthesis.build_snapshot(
                                        merger, players_db, draft_picks, pick_order, target_index, my_roster_id,
                                        league_for_engine, pick_label=pick_label,
                                        pool_scope=st.session_state.draft_room_pool_scope,
                                    )
                                    st.session_state.draft_room_snapshot_cache = (snapshot_cache_key, snap)
                                except Exception as exc:  # noqa: BLE001 -- surface, never crash the whole dashboard
                                    snap = None
                                    notify("error", f"Couldn't build the draft board: {exc}")

                            if snap is not None and not snap.candidates:
                                st.info("No candidates available in the current player pool/scope.")
                            elif snap is not None:
                                if not is_live:
                                    on_clock_id = str(pick_order[current_index])
                                    on_clock_name = owner_names_by_id.get(on_clock_id, f"Roster {on_clock_id}")
                                    st.caption(f"Not your turn yet -- {on_clock_name} is on the clock.")

                                positions_present = sorted({c.position for c in snap.candidates})
                                # Board-view control, round 3 (see REVIEW_LOG.md): the position
                                # filter is no longer a multi-select at all -- exactly ONE board
                                # view is active at a time (a single real position, a real
                                # flex-slot view like FLEX/IDP_FLEX using that slot's own actual
                                # eligible-position set, or ALL). Placed as the board's own
                                # title row, directly above the board itself, not grouped with
                                # Player Pool -- this is a property of the board ("what view am
                                # I looking at"), not a page-level filter.
                                view_options = draft_board_ui.position_view_options(
                                    set(positions_present), league_for_engine.get("roster_positions") or [],
                                )
                                current_view = st.session_state.get("draft_room_position_view", "ALL")
                                if current_view not in view_options:
                                    current_view = "ALL"
                                    st.session_state.draft_room_position_view = "ALL"

                                with st.container(key="draft_room_board_title_row"):
                                    title_col, value_col, _spacer_col = st.columns(
                                        [0.85, 1.2, 7.95], gap="xxsmall", vertical_alignment="top",
                                    )
                                    with title_col:
                                        st.markdown(
                                            '<div class="drv-board-title">CANDIDATES<span class="dot">•</span></div>',
                                            unsafe_allow_html=True,
                                        )
                                    with value_col:
                                        if st.button(
                                            draft_board_ui.position_view_label(current_view),
                                            key="draft_room_view_toggle",
                                            help="Board view -- display only, never changes what's analyzed, ranked, or scored.",
                                        ):
                                            st.session_state.draft_room_position_view_open = not st.session_state.get(
                                                "draft_room_position_view_open", False
                                            )
                                            st.rerun()

                                if st.session_state.get("draft_room_position_view_open", False):
                                    with st.container(key="draft_room_view_menu"):
                                        # See the mock path above: one row, columns weighted by
                                        # label width rather than split equally.
                                        opt_cols = st.columns(draft_board_ui.view_option_widths(view_options))
                                        for opt, opt_col in zip(view_options, opt_cols):
                                            opt_key = (
                                                f"draft_room_view_opt_active_{opt}" if opt == current_view
                                                else f"draft_room_view_opt_{opt}"
                                            )
                                            with opt_col:
                                                if st.button(draft_board_ui.position_view_label(opt), key=opt_key):
                                                    st.session_state.draft_room_position_view = opt
                                                    st.session_state.draft_room_position_view_open = False
                                                    st.rerun()

                                filtered = draft_board_ui.filter_candidates_by_view(snap.candidates, current_view)
                                display_snap = dataclasses.replace(snap, candidates=tuple(filtered))

                                board_header = f"ON THE CLOCK — {pick_label}" if is_live else f"YOUR NEXT PICK — {pick_label}"
                                is_superflex_fmt = "SUPER_FLEX" in (league_for_engine.get("roster_positions") or [])
                                is_dynasty_fmt = (league_for_engine.get("settings") or {}).get("type") == 2
                                board_tags = []
                                if draft_type == "3rr":
                                    board_tags.append("3RR ACTIVE")
                                first_intervening = next(
                                    (c.intervening_picks for c in filtered if c.intervening_picks is not None), None,
                                )
                                if first_intervening is not None:
                                    board_tags.append(f"{first_intervening} pick(s) to your next selection")
                                    board_tags.append({"label": "?", "title": draft_state_caveat})
                                board_tags.append(
                                    f"{num_teams}-team · {'Superflex' if is_superflex_fmt else '1QB'} · "
                                    f"{'Dynasty' if is_dynasty_fmt else 'Redraft'}"
                                )
                                board_payload = draft_board_ui.serialize_snapshot(
                                    display_snap, pick_header=board_header, state_tags=board_tags,
                                )
                                # A generous, content-driven height -- the iframe has no way to
                                # tell Streamlit how tall its own content grew (unlike a normal
                                # DOM element, it can't just push the page down), so this has to
                                # be sized up front. ~150px per row covers one expanded card
                                # comfortably; internal scrolling (baked into the component's own
                                # page, not this call) covers the rest for a long candidate list.
                                board_height = min(180 + 92 * max(len(filtered), 1), 1400)
                                components.html(
                                    draft_board_ui.render_board_html(board_payload),
                                    height=board_height, scrolling=True,
                                )

                                debate_btn_col, chip_col, _ = st.columns([1, 0.6, 2.4])
                                with debate_btn_col:
                                    run_debate_clicked = st.button(
                                        "🎙️ Debate This Pick", key="draft_room_debate_btn",
                                        type="primary", use_container_width=True,
                                        help=screen_context.DRAFT_ROOM_PICK_DEBATE_HELP,
                                    )
                                with chip_col:
                                    render_debate_chip(screen_context.build_draft_room_context(snap), key="draft_room")
                                if run_debate_clicked:
                                    debate_api_keys = {
                                        "claude": api_key_for("anthropic"), "gemini": api_key_for("gemini"),
                                        "openai": api_key_for("openai"),
                                    }
                                    with st.spinner("Strategist, Skeptic, and Caller are debating..."):
                                        debate_result = pick_debate.debate_pick(
                                            snap, previous_snapshot=st.session_state.draft_room_last_snapshot,
                                            api_keys=debate_api_keys,
                                        )
                                    st.session_state.draft_room_last_snapshot = snap
                                    st.session_state.draft_room_debate_result = debate_result
                                    if debate_result.errors:
                                        notify("warning", "Debate finished with issues: " + "; ".join(debate_result.errors))

                                debate_result = st.session_state.draft_room_debate_result
                                if debate_result is not None and debate_result.pick_label == pick_label:
                                    st.markdown("---")
                                    rec = debate_result.recommended
                                    if rec is None:
                                        st.warning("The panel's recommendation didn't cleanly match a candidate -- see the raw reports below.")
                                    else:
                                        st.markdown(f"## Recommendation: {rec.name}")
                                        conf_caption = f"Confidence: {debate_result.confidence}" if debate_result.confidence else ""
                                        st.caption(conf_caption)
                                        if debate_result.why:
                                            st.markdown(f"**Why now?** {debate_result.why}")

                                        necessity_class = _NECESSITY_BADGE_CLASS.get(rec.necessity_label, "badge-necessity-close-call")
                                        necessity_emoji = _NECESSITY_COLOR_EMOJI.get(rec.necessity_label, "")
                                        badge_col, market_col = st.columns([1, 2])
                                        with badge_col:
                                            st.markdown(
                                                f'<span class="badge {necessity_class}">{necessity_emoji} PICK NECESSITY: '
                                                f'{rec.pick_necessity:.0f}/100 — {rec.necessity_label}</span>',
                                                unsafe_allow_html=True,
                                            )
                                        if rec.reach_label is not None:
                                            with market_col:
                                                st.caption(
                                                    f"Market consensus (KeepTradeCut, trade-value not literal ADP): "
                                                    f"rank {rec.consensus_rank}, tier {rec.consensus_tier} — **{rec.reach_label}**"
                                                )

                                        metric_row1 = st.columns(6)
                                        metric_row1[0].metric("Universal Value", f"{rec.universal_value:.0f}")
                                        metric_row1[1].metric(
                                            "Projected Points", f"{rec.projected_points:.0f}" if rec.projected_points is not None else "—",
                                        )
                                        metric_row1[2].metric("Your Acquisition Value", f"{rec.team_acquisition_value:.0f}")
                                        metric_row1[3].metric(
                                            "Survival to Next Pick",
                                            f"{round(rec.survival_probability * 100)}%" if rec.survival_probability is not None else "—",
                                        )
                                        metric_row1[4].metric("Positional Cliff", rec.positional_cliff["tier"] if rec.positional_cliff else "—")
                                        metric_row1[5].metric(f"{rec.position} Run", "DETECTED" if rec.position_run_detected else "—")

                                        metric_row2 = st.columns(3)
                                        metric_row2[0].metric("Opportunity Cost of Waiting", rec.opportunity_cost if rec.opportunity_cost is not None else "—")
                                        metric_row2[1].metric("Expected Value If You Wait", rec.expected_value_of_waiting if rec.expected_value_of_waiting is not None else "—")
                                        metric_row2[2].metric("Denial Value", rec.denial_value if rec.denial_value else "—")

                                        alt = debate_result.best_alternative
                                        if alt is not None:
                                            st.markdown(f"**Best alternative:** {alt.name} — {alt.team_acquisition_value:.0f} acquisition value")
                                            alt_survival = f"{round(alt.survival_probability * 100)}%" if alt.survival_probability is not None else "—"
                                            st.caption(f"Survival: {alt_survival}")

                                    if debate_result.disagreements:
                                        for d in debate_result.disagreements:
                                            st.warning(f"⚠️ Panel flagged a possible issue with an input: **{d['term']}** — {d['reason']}")

                                    with st.expander("🗣️ Debate"):
                                        st.markdown("**Strategist** — why the numbers favor the pick")
                                        st.markdown(f'<div class="agent-block agent-prose">{html.escape(debate_result.strategist_report)}</div>', unsafe_allow_html=True)
                                        st.markdown("**Skeptic** — what could make waiting correct")
                                        st.markdown(f'<div class="agent-block agent-prose">{html.escape(debate_result.skeptic_report)}</div>', unsafe_allow_html=True)
                                        st.markdown("**Caller** — final synthesis")
                                        st.markdown(f'<div class="agent-block agent-prose">{html.escape(debate_result.why or debate_result.caller_report)}</div>', unsafe_allow_html=True)
                                        if debate_result.key_factor:
                                            st.caption(f"Key factor: {debate_result.key_factor}")
                                        st.markdown("**Dissent** — the strongest argument against the recommendation")
                                        st.markdown(
                                            f'<div class="agent-block agent-prose">{html.escape(debate_result.dissent) if debate_result.dissent else "None raised."}</div>',
                                            unsafe_allow_html=True,
                                        )

                                    if debate_result.diff:
                                        with st.expander("📊 What changed since your last debate?"):
                                            for d in debate_result.diff:
                                                if d.get("entered") is True:
                                                    st.markdown(f"🆕 **{d['name']}** entered the candidate pool at rank {d['rank']}")
                                                elif d.get("entered") is False:
                                                    st.markdown(f"❌ **{d['name']}** is no longer a live candidate (was rank {d['rank']})")
                                                elif d.get("deltas"):
                                                    delta_str = ", ".join(f"{_DRAFT_ROOM_DIFF_LABELS.get(k, k)}: {v:+}" for k, v in d["deltas"].items())
                                                    st.markdown(f"**{d['name']}**: rank moved {d['rank_delta']:+d} ({delta_str})")
                                elif debate_result is not None:
                                    st.caption("A prior debate result is available for a different pick -- click Debate This Pick to refresh for this one.")

    st.markdown("---")

elif main_view == LEAGUE_VIEW:
    # ------------------------------------------------------------------ league --
    # Standings Ladder + Depth Map are ONE decision surface with two lenses (Fable's League
    # design review, F1-F6), not two dashboards. The anti-two-dashboard contract this section
    # must keep satisfying: (1) asymmetry -- Standings is the governing home view, Depth Map is
    # entered/exited as a secondary lens, never a co-equal tab; (2) shared drill-down
    # destination -- selecting a team from EITHER lens resolves into the exact same roster
    # decomposition panel below; (3) state continuity -- the selected team survives switching
    # lenses. Neither lens computes a team-strength score; strength stays an entry point.

    st.markdown("---")
    st.subheader("League")

    merger = st.session_state.data_merger
    owner_labels = roster_owner_names(snapshot)
    my_team_label = owner_labels.get(roster["roster_id"]) if roster else None
    all_team_labels = sorted(set(owner_labels.values()))

    # Real record only -- league_standings.team_standings reads Sleeper's own settings.wins/
    # losses/ties/fpts fields directly, never a computed rating (see that module's own docstring).
    standings = league_standings.team_standings(snapshot.get("rosters") or [], owner_labels)
    games_played_total = sum(row["wins"] + row["losses"] + row["ties"] for row in standings)
    season_started = games_played_total > 0
    if not season_started:
        # 0-0 across the board makes "sorted by wins" a meaningless stable-sort tiebreak --
        # alphabetical is at least honestly arbitrary instead of quietly implying a real order.
        standings = sorted(standings, key=lambda row: row["team"])

    depth = positional_depth(player_universe, merger)

    LADDER_LENS, DEPTH_LENS = "🏆 Standings", "📊 Depth Map"
    # Home lens follows one real fact (has the league played any games) rather than becoming a
    # third mode -- F1. setdefault only takes effect the first time this key is ever set; a
    # user's own later lens choice is never overridden back.
    st.session_state.setdefault("league_lens", LADDER_LENS if season_started else DEPTH_LENS)
    st.session_state.setdefault("league_selected_team", my_team_label or (all_team_labels[0] if all_team_labels else None))
    st.session_state.setdefault("league_selected_position", None)

    lens = st.segmented_control(
        "League lens", options=[LADDER_LENS, DEPTH_LENS], key="league_lens", label_visibility="collapsed",
        help="Standings: the league's actual won-lost record -- the home view once games have "
        "been played. Depth Map: a secondary lens for scanning positional depth across every "
        "team. Selecting a team in either one carries over to the other, and both open the same "
        "team breakdown below. Neither is a computed team-strength score.",
    )
    if not season_started:
        st.caption(
            "No games played yet this season (0-0 across the board), so Standings isn't "
            "meaningful yet — Depth Map leads for now. Standings is still one tap away, and "
            "it's listing teams alphabetically rather than implying a fake early order."
        )

    if lens == LADDER_LENS:
        standings_df = pd.DataFrame([
            {"Team": row["team"], "W": row["wins"], "L": row["losses"], "T": row["ties"], "PF": row["points_for"]}
            for row in standings
        ])
        ladder_event = st.dataframe(
            standings_df, hide_index=True, use_container_width=True,
            on_select="rerun", selection_mode="single-row", key="league_ladder_grid",
        )
        selected_rows = ladder_event.selection.rows if ladder_event and ladder_event.selection else []
        if selected_rows:
            clicked_team = standings_df.iloc[selected_rows[0]]["Team"]
            if clicked_team != st.session_state.league_selected_team:
                st.session_state.league_selected_team = clicked_team
                st.rerun()
    else:
        _position_order = ["QB", "RB", "WR", "TE", "K", "DEF", "LB", "DL", "DB"]
        positions_present = [p for p in _position_order if any(p in positions for positions in depth.values())]
        st.caption(
            "How many rostered players (starters + bench + taxi/IR) each team has at each "
            "position, colored by how that team compares to the rest of the league at that "
            "position — the same Strong/Average/Weak judgment the Trade Calculator uses, not a "
            "separate opinion. Value in parens (where shown) is that position's total Draft "
            "Sharks trade value. Click a cell to load that team below."
        )
        depth_rows = []
        for team_label in all_team_labels:
            row = {"team": team_label}
            for pos in positions_present:
                cell = depth.get(team_label, {}).get(pos, {"count": 0, "value": None})
                row[pos] = f"{cell['count']} ({cell['value']:.0f})" if cell["value"] is not None else cell["count"]
            depth_rows.append(row)
        depth_map_df = pd.DataFrame(depth_rows)[["team"] + positions_present] if depth_rows and positions_present else pd.DataFrame()

        if depth_map_df.empty:
            st.info("No rostered players found in this league's synced data.")
        else:
            def _style_depth_column(col: pd.Series) -> list[str]:
                position = col.name
                peer_cells = [teams[position] for teams in depth.values() if position in teams]
                styles = []
                for team_label in depth_map_df["team"]:
                    cell = depth.get(team_label, {}).get(position, {"count": 0, "value": None})
                    label = depth_ratings.depth_label(cell, peer_cells)
                    if label == "Strong":
                        styles.append(f"background-color: {design_system.token_rgba('emerald', 0.18)}; color: #4ade80;")
                    elif label == "Weak":
                        styles.append(f"background-color: {design_system.token_rgba('crimson', 0.18)}; color: #f87171;")
                    else:
                        styles.append("")
                return styles

            styled_depth_df = depth_map_df.style.apply(_style_depth_column, subset=positions_present, axis=0)
            depth_event = st.dataframe(
                styled_depth_df, hide_index=True, use_container_width=True,
                on_select="rerun", selection_mode="single-cell", key="league_depth_map_grid",
            )
            cells = depth_event.selection.cells if depth_event and depth_event.selection else []
            if cells:
                row_idx, col_name = cells[0]
                clicked_team = depth_map_df.iloc[row_idx]["team"]
                clicked_position = col_name if col_name != "team" else None
                changed = clicked_team != st.session_state.league_selected_team or (
                    clicked_position and clicked_position != st.session_state.league_selected_position
                )
                if changed:
                    st.session_state.league_selected_team = clicked_team
                    if clicked_position:
                        st.session_state.league_selected_position = clicked_position
                    st.rerun()

    st.markdown("---")

    if not all_team_labels:
        st.info("No teams found in this league's synced data.")
    else:
        if st.session_state.league_selected_team not in all_team_labels:
            st.session_state.league_selected_team = all_team_labels[0]
        team_label = st.selectbox(
            "Team", options=all_team_labels,
            index=all_team_labels.index(st.session_state.league_selected_team),
            key="league_team_picker",
            help="Pick a team here, or click a row/cell in either lens above — both stay in sync.",
        )
        if team_label != st.session_state.league_selected_team:
            st.session_state.league_selected_team = team_label

        # Record-vs-asset-base divergence (F2): a rank comparison between two facts that
        # already exist (win-rank from Standings, positional-depth-value-rank) -- never blended
        # into a new composite score, and only shown once the record itself is meaningful.
        if season_started:
            win_rank_order = [row["team"] for row in standings]

            def _team_total_value(label: str) -> Optional[float]:
                values = [c["value"] for c in depth.get(label, {}).values() if c["value"] is not None]
                return sum(values) if values else None

            value_rank_order = sorted(
                all_team_labels,
                key=lambda t: _team_total_value(t) if _team_total_value(t) is not None else -1,
                reverse=True,
            )
            if team_label in win_rank_order and _team_total_value(team_label) is not None:
                win_rank = win_rank_order.index(team_label) + 1
                value_rank = value_rank_order.index(team_label) + 1
                n_teams = len(all_team_labels)
                threshold = max(1, n_teams // 3)
                if abs(win_rank - value_rank) > threshold:
                    if win_rank > value_rank:
                        st.caption(
                            f"⚠️ {team_label}'s record (rank {win_rank} of {n_teams}) trails its "
                            f"asset base (rank {value_rank} of {n_teams} by positional depth/"
                            "value) — a team that looks better on the roster than in the standings."
                        )
                    else:
                        st.caption(
                            f"⚠️ {team_label}'s record (rank {win_rank} of {n_teams}) is ahead of "
                            f"its asset base (rank {value_rank} of {n_teams} by positional depth/"
                            "value) — winning despite a thinner roster, worth watching for regression."
                        )

        # Draft-capital decomposition (F4) -- Sleeper-authoritative traded-pick ownership,
        # priced where Draft Sharks values are loaded. Untouched original picks have no ledger
        # entry by design (see build_pick_ledger's own docstring) -- not invented inventory.
        pick_ledger = build_pick_ledger(snapshot)
        team_roster_id = next((rid for rid, label in owner_labels.items() if label == team_label), None)
        acquired = pick_ledger.get(team_roster_id, {}).get("acquired", [])
        if acquired:
            parts = []
            for p in acquired:
                pick_label = f"{p.get('season')} Rd {p.get('round')}"
                original_owner = owner_labels.get(p.get("roster_id"), f"Roster {p.get('roster_id')}")
                value = merger.pick_value(f"{p.get('season')} Random Rd {p.get('round')}") if merger.is_trade_values_loaded else None
                parts.append(f"{pick_label} (from {original_owner}{f', valued {value}' if value is not None else ''})")
            st.caption("**Picks acquired via trade:** " + "; ".join(parts))
        else:
            st.caption("**Picks acquired via trade:** none.")

        # Shared drill-down destination (F6): the exact same roster rows either lens resolves
        # to, kept as pointers rather than player-detail cards -- name/position/team/slot/proj/
        # injury, the same shape screen_context.build_league_context already sends to Debate.
        team_rows = [
            r for r in player_universe
            if r.get("ownership") == "ROSTERED" and (r.get("owner_name") or f"Roster {r.get('roster_id', '?')}") == team_label
        ]
        if not team_rows:
            st.info(f"No rostered players found for {team_label}.")
        else:
            context_rows = [
                {
                    "name": r["name"], "position": r["position"], "team": r["team"],
                    "slot": r.get("roster_slot") or "Bench", "injury_status": r.get("injury_status"),
                    "sleeper_proj": r.get("sleeper_proj"),
                }
                for r in team_rows
            ]
            team_df = pd.DataFrame(context_rows)
            team_df["_sort"] = team_df["slot"].map(SLOT_SORT_ORDER).fillna(99)
            team_df = team_df.sort_values("_sort").drop(columns="_sort")
            display_cols = [c for c in ["name", "position", "team", "slot", "sleeper_proj", "injury_status"] if c in team_df.columns]
            render_styled_table(
                team_df[display_cols],
                pill_columns={"injury_status": _injury_pill_color, "position": _position_pill_color},
                group_column="slot",
                column_labels={"sleeper_proj": sleeper_proj_label(snapshot)},
            )
            league_chip_col, league_link_col, _ = st.columns([0.6, 1.0, 1.6])
            with league_chip_col:
                render_debate_chip(screen_context.build_league_context(team_label, context_rows), key="league")
            with league_link_col:
                # Exactly one contextual crosslink per decomposition (F6) -- reuses the Trade
                # Calculator's own partner selection, never a second handoff mechanism. Only
                # offered for teams other than the user's own -- you can't trade with yourself.
                if team_label != my_team_label and st.button("↔ Open in Trade Calculator", key="league_crosslink_trade"):
                    st.session_state.trade_calc_partner = team_label
                    st.session_state.pending_main_view = MAINTENANCE_VIEW
                    st.rerun()
            st.caption(
                "Ask The Prytaneum about this team by name (or a specific player on it) for a full trade "
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
# fixed-position Prytaneum dock below) since deeply nested columns inside that fixed container were
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
                    "Alternative": d.get("alternative", ""),
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

bot_findings = bot_research.load_findings()
bot_comparisons = bot_research.load_comparisons()
if bot_findings or bot_comparisons:
    with st.expander(f"🔬 Bot Research ({len(bot_findings)} findings, {len(bot_comparisons)} comparisons)"):
        st.caption(
            "Everything the panel has vetted across every league, newest first — see "
            "MODERATOR_SYSTEM_PROMPT's SOURCE FINDING/SOURCE COMPARISON rules for how an item "
            "gets in here (survives scrutiny from the whole panel, Contrarian included). "
            "Findings with a rank already feed the composite score at a low weight; "
            "comparisons never do — see the README for why."
        )
        if bot_findings:
            st.markdown("**Findings**")
            findings_df = pd.DataFrame(
                [
                    {
                        "Date": f["date"], "Player": f["player_name"], "Source": f["source"],
                        "Claim": f["claim"], "Rank": f.get("rank") if f.get("rank") is not None else "—",
                        "Composite impact": f.get("composite_impact", ""),
                    }
                    for f in reversed(bot_findings)
                ]
            )
            st.dataframe(findings_df, use_container_width=True, hide_index=True)
        if bot_comparisons:
            st.markdown("**Comparisons**")
            comparisons_df = pd.DataFrame(
                [
                    {
                        "Date": c["date"],
                        "Comparison": f"{c['subject']} {c['direction']} {c['compared_to']}",
                        "Source": c["source"], "Context": c.get("context") or "—", "Evidence": c.get("evidence", ""),
                    }
                    for c in reversed(bot_comparisons)
                ]
            )
            st.dataframe(comparisons_df, use_container_width=True, hide_index=True)

todo_league_id = st.session_state.selected_league_id
active_items = todo_log.load_todos(todo_league_id, statuses=todo_log.ACTIVE_STATUSES)
# Popped (read once, then cleared) rather than a persistent flag -- it should force this open
# for the one rerun right after a "🎯 Add as objective" click lands a suggestion in the text
# box below, not forever after.
_force_expand_todos = st.session_state.pop("_force_expand_todos", False)
with st.expander(f"🎯 Active Objectives ({len(active_items)})", expanded=bool(active_items) or _force_expand_todos):
    st.caption(
        "League objectives the bots are tracking (🤖) or you added yourself (✍️) — selectively "
        "given to the bots as context in future debates, not just a checklist. A 🔎 tag means a "
        "bot proposed it looks done; confirm it or keep it open. A resolution note you add when "
        "closing one persists permanently in the Archive below, so the bots can recall *why* it "
        "ended the way it did if the same idea comes up again."
    )
    if _force_expand_todos:
        st.caption("🎯 Seeded from that message below — edit it, hit Add, or ask the Moderator to expand it using context.")
    manual_col, expand_col, add_col = st.columns([3.2, 1, 1])
    manual_text = manual_col.text_input(
        "Add an objective", key="manual_todo_text", label_visibility="collapsed",
        placeholder="Add a new objective…",
    )
    # Only lit up right after a "🎯 Add as objective" click on a message seeded this box (see
    # _render_agent_msg) -- this button re-reads THAT message, not whatever's currently typed
    # above, and asks the Moderator to condense it using the surrounding conversation and this
    # league's existing objectives, same as the old per-message smart-condense button did. Kept
    # opt-in rather than automatic: most seeded text is already close enough to an objective
    # that a bot call would buy nothing.
    _seed_ts = st.session_state.get("_objective_seed_ts")
    if expand_col.button(
        "🤖 Ask Moderator", key="expand_objective_with_context", use_container_width=True,
        disabled=_seed_ts is None,
        help=(
            "Only available right after 🎯 Add as objective seeds this box from a message."
            if _seed_ts is None else
            "Ask the Moderator to rewrite the text above as a properly scoped objective, using "
            "the surrounding conversation and this league's existing objectives."
        ),
    ):
        seed_msg = next((m for m in st.session_state.chat_history if m.get("ts") == _seed_ts), None)
        if seed_msg is None:
            notify("warning", "That message isn't in this chat anymore -- edit the text above yourself instead.")
        else:
            obj_provider = bot_config.load_role_providers()["moderator"]
            obj_key = api_key_for(PROVIDER_KEY_FIELD[obj_provider])
            if not IS_PROVIDER_CONFIGURED[obj_provider](obj_key):
                notify("warning", f"{bot_config.PROVIDER_LABELS[obj_provider]} isn't configured -- add an API key to use this.")
            else:
                with st.spinner("Condensing into an objective..."):
                    # Centered on the seed message itself, both backward AND forward -- see
                    # build_context's conversation_window param.
                    full_history = st.session_state.chat_history
                    try:
                        msg_idx = next(i for i, m in enumerate(full_history) if m.get("ts") == _seed_ts)
                    except StopIteration:
                        msg_idx = len(full_history) - 1
                    half_window = RECENT_TURNS_IN_CONTEXT // 2
                    window = full_history[max(0, msg_idx - half_window): msg_idx + half_window + 1]
                    condense_context = build_context(
                        snapshot, roster_table if roster else [], player_universe, seed_msg["content"],
                        conversation_window=window,
                    )
                    condensed = llm_engine.ask_condense_to_objective(
                        condense_context, seed_msg["content"], provider=obj_provider,
                        api_key=obj_key, model=bot_config.load_role_models().get("moderator") or None,
                    )
                result = llm_engine.parse_condensed_objective(condensed)
                if result.get("objective"):
                    st.session_state["manual_todo_text"] = result["objective"]
                    st.session_state["_force_expand_todos"] = True
                    st.rerun()
                elif result.get("not_new_id") is not None:
                    notify("info", f"Already tracked as objective #{result['not_new_id']}: {result.get('reason', '')}")
                elif result.get("no_objective_reason"):
                    notify("info", f"Nothing actionable there: {result['no_objective_reason']}")
                else:
                    notify("warning", "Couldn't turn that into an objective -- edit the text above yourself instead.")
    if add_col.button("Add", key="add_manual_todo", use_container_width=True) and manual_text.strip():
        todo_log.add_todo(todo_league_id, manual_text, source="manual")
        st.session_state.pop("_objective_seed_ts", None)
        # Without this the text stays in the box after a successful add -- confirmed live, a
        # second click (habit, or just not noticing it worked) would silently create a
        # duplicate objective from the same leftover text.
        st.session_state["manual_todo_text"] = ""
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
                    # Same fix as the objective box above -- leftover text after a successful
                    # add invites an accidental duplicate note on the next click.
                    st.session_state[f"todo_note_{item['id']}"] = ""
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

# ------------------------------------------------------------------ the prytaneum --
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
        st.subheader("The Prytaneum")
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

    # Whatever a 💬 Debate chip (render_debate_chip) last attached -- the natural-language
    # "Considering" handoff, not a raw dump of the ScreenContext object. This is meant to read
    # as "Debate already understands what I was looking at," never as "here is the packet of
    # data that got passed" -- looking_at alone covers that read for most people; decision/
    # evidence/entities stay one click away in the expander for whoever wants the receipts.
    # Persists until a chip is clicked again (from this or another surface); nothing here
    # clears it automatically, since there's no signal yet for "the user is done with this."
    attached_context = st.session_state.get("debate_attached_context")
    if dock_level != "collapsed" and attached_context is not None:
        st.markdown(f"💬 **Considering:** {attached_context.looking_at}")
        with st.expander("Full evidence", expanded=False):
            st.text(f"{attached_context.decision}\n\n{attached_context.evidence}")
            if attached_context.entities:
                st.caption("Involved: " + ", ".join(attached_context.entities))

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
            quick_debate = st.button("Full Prytaneum", use_container_width=True, type="primary")
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
                    process_moderator_output(
                        followup_text, trigger_question,
                        provider=provider, model=role_models.get("moderator") or "",
                    )
                else:
                    result = llm_engine.run_debate(
                        context, trigger_question, role_providers=role_providers, api_keys=api_keys,
                        role_models=role_models, moderator_personality=moderator_personality,
                    )
                    append_message("quant", result.quant, provider=role_providers["quant"], model=role_models.get("quant") or None)
                    append_message("beat", result.beat, provider=role_providers["beat"], model=role_models.get("beat") or None)
                    append_message("contrarian", result.contrarian, provider=role_providers["contrarian"], model=role_models.get("contrarian") or None)
                    append_message("moderator", result.moderator, provider=role_providers["moderator"], model=role_models.get("moderator") or None)
                    process_moderator_output(
                        result.moderator, trigger_question,
                        provider=role_providers["moderator"],
                        model=role_models.get("moderator") or "",
                    )
                    # run_debate already collects which role(s) failed (a missing/invalid API
                    # key, a provider outage) -- this was computed and silently thrown away
                    # before, so a failed call just looked like a "⚠️ ..." chat message with no
                    # toast, no activity-log entry, and no visible sign anything went wrong.
                    if result.errors:
                        notify("warning", "Debate finished with issues: " + "; ".join(result.errors))
            # Without this, the question box's label (now dependent on whether a debate has
            # happened -- see default_trigger_mode above), the persona captions, and everything
            # else derived from chat_history keep showing what they were at the START of this
            # run until some later, unrelated interaction happens to trigger the next one.
            st.rerun()

        VERDICT_FIELD_LABELS = (
            "RECOMMENDATION", "CONVICTION", "REASON", "DISSENT", "RISK", "RECON",
            "PRICE CEILING", "ALTERNATIVE", "ACTION ITEM", "TODO UPDATE", "TODO LIKELY RESOLVED",
        )

        def format_agent_content(role: str, content: str) -> tuple[str, str]:
            """Escape first -- this was going straight into unsafe_allow_html unescaped,
            so a literal '<', '>', or '&' anywhere in an LLM response (plausible in
            ordinary analysis prose, e.g. "if X < Y") could silently break the block's
            rendering. Returns (prose_html, verdict_html): for a Moderator message that
            re-emitted the structured block, everything before the first RECOMMENDATION:
            line (always the block's first field -- see MODERATOR_SYSTEM_PROMPT) is prose,
            everything from there on is the verdict recap, with its field labels bolded so
            it still reads as a scannable form. A conversational follow-up that skipped the
            block (see MODERATOR_FOLLOWUP_ADDENDUM) has no such line, so it's all prose --
            same as every non-Moderator role, which never carries this block at all. Keeping
            the two halves separate is what lets _render_agent_msg show reasoning as an
            actual chat reply and the verdict as a distinct recap card below it, instead of
            one undifferentiated monospace wall."""
            if role != "moderator":
                return html.escape(content).strip(), ""
            match = re.search(r"(?m)^RECOMMENDATION:", content)
            if not match:
                return html.escape(content).strip(), ""
            prose = html.escape(content[:match.start()].strip())
            verdict = html.escape(content[match.start():].strip())
            pattern = r"(?m)^(" + "|".join(VERDICT_FIELD_LABELS) + r"):"
            verdict = re.sub(pattern, r"<strong>\1:</strong>", verdict)
            return prose, verdict

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
                # Bot messages only -- ACTION ITEM today only ever comes out of a Moderator
                # verdict, so a good Quant/Beat callout has no path to becoming a tracked
                # objective except retyping it yourself. One button here, free: just this
                # message's own text (whitespace-collapsed, truncated at 200 chars on a word
                # boundary) dropped straight into the objective box below. It also seeds
                # _objective_seed_ts so that box's own "🤖 Ask Moderator" button (see the
                # Active Objectives expander) can, on request, replace this with a version
                # condensed from the surrounding conversation -- most messages are already
                # phrased close enough to an objective that a bot call buys nothing, so that
                # stays opt-in rather than firing here on every click.
                if msg["role"] in ROLE_BADGE_BASE and st.button(
                    "🎯 Add as objective", key=f"objective_from_msg_{ts}",
                    help="Drop this message's own text into the objective box below -- no bot call. "
                    "That box has its own button to ask the Moderator to expand it using context, if you want that instead.",
                ):
                    quick_text = " ".join(msg["content"].split())
                    if len(quick_text) > 200:
                        quick_text = quick_text[:200].rsplit(" ", 1)[0] + "…"
                    st.session_state["manual_todo_text"] = quick_text
                    st.session_state["_force_expand_todos"] = True
                    st.session_state["_objective_seed_ts"] = ts
                    st.rerun()
            prose_html, verdict_html = format_agent_content(msg["role"], msg["content"])
            inner = f'<div class="agent-prose">{prose_html}</div>' if prose_html else ""
            if verdict_html:
                inner += f'<div class="agent-verdict">{verdict_html}</div>'
            st.markdown(f'<div class="agent-block">{inner}</div>', unsafe_allow_html=True)

        # A Full Prytaneum run always appends exactly [quant, beat, contrarian, moderator] back
        # to back (see the trigger block above) -- group that run into one unit so the Moderator's
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

