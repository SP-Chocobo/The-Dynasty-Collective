"""Pure formatting/data-shaping helpers for the Trade Calculator's roster-aware production UI
(app.py's Roster Maintenance view, "Comparison / Balance" paradigm per the design-language
reference). No Streamlit import here and no widget code -- exactly draft_board_ui.py's role
for the Draft Room: this module never prices an asset, computes a verdict, or reads roster
depth itself, it only shapes already-computed values into the small HTML fragments and CSS
app.py embeds via st.markdown(unsafe_allow_html=True). Real interactivity (buttons, columns,
session-state toggling) lives in app.py, not here -- Streamlit widgets can't be meaningfully
wrapped behind a plain-data return value the way an iframe payload can (see draft_board_ui.py),
so app.py itself owns the render loop and calls into these functions just for formatting.
"""

from __future__ import annotations

from typing import Optional

import design_system

# Component-level CSS specific to this surface. Shared color/type tokens come from
# design_system's :root block, which app.py's own global stylesheet already injects once at
# page load -- native Streamlit, unlike Draft Room's iframe, shares that one stylesheet scope,
# so there's no need to re-declare the tokens here, only the classes built on top of them.
# The type stack is NOT a CSS custom property (the :root block is the colour palette), so it is
# substituted from design_system.FONT_MONO below rather than hand-copied into each rule -- two
# of the app's eight hand-copied stacks had already lost the DejaVu Sans Mono fallback.
TRADE_LEDGER_CSS = """
<style>
.tl-pill {
  display: inline-block; font-family: __DESIGN_SYSTEM_FONT_MONO__;
  font-size: .76rem; padding: .2rem .6rem; border-radius: 4px; letter-spacing: .03em;
}
.tl-pill.fresh { color: var(--emerald-b); border: 1px solid var(--emerald); background: color-mix(in srgb, var(--emerald) 12%, transparent); }
/* Unknown age is its own state, deliberately NOT green and deliberately not amber: it is
   neither a positive "current" assertion nor a measured problem, it is "we do not know."
   Muted/neutral is the app's existing channel for that. */
.tl-pill.unknown { color: var(--muted); border: 1px dashed var(--line-2); background: transparent; }
/* amber = attention, the shared meaning of that token: a ruler that has gone stale, and (the
   EST badge below) a pick value that is an estimate. Both were gold until the 2026-09-06
   ruling took gold out of the semantic channel -- design_system.TOKENS["amber"] records it.
   The tint is mixed from the token rather than written as an rgb triplet, so it cannot drift
   from TOKENS on its own the way a hand-copied literal can. */
.tl-pill.stale { color: var(--amber-b); border: 1px solid var(--amber); background: color-mix(in srgb, var(--amber) 12%, transparent); }

.tl-postag { color: var(--muted); font-size: .8rem; }
.tl-value { font-family: __DESIGN_SYSTEM_FONT_MONO__; font-weight: 700; font-size: .92rem; text-align: right; }
.tl-value.tl-dim { color: var(--dim); font-weight: 400; font-style: italic; font-size: .78rem; }
.tl-pickbadge { font-size: .62rem; color: var(--amber-b); border: 1px solid var(--amber); border-radius: 4px; padding: 0 .3rem; margin-left: .35rem; }

.tl-selected-send { color: var(--crimson-b); font-weight: 700; font-size: .68rem; letter-spacing: .04em; margin-right: .4rem; }
.tl-selected-receive { color: var(--emerald-b); font-weight: 700; font-size: .68rem; letter-spacing: .04em; margin-right: .4rem; }
</style>
""".strip().replace("__DESIGN_SYSTEM_FONT_MONO__", design_system.FONT_MONO)


#: The three freshness states, named once. "Unknown" is a state in its own right -- see below.
FRESHNESS_UNKNOWN_TEXT = "Value age unknown — no source date"


def freshness_pill(is_stale: bool, age_days: Optional[int]) -> str:
    """"Values current" / "Values Nd stale" / "Value age unknown" -- the one shared freshness
    phrasing every priced/ranked surface uses (see the design-language reference's Source of
    Truth & Freshness section), rendered as the small pill span app.py embeds. Never names a
    vendor -- that stays one level down, same as a role's LLM provider stays secondary to the
    role.

    THREE STATES, NOT TWO. data_merger._compute_freshness returns (None, None, False) when the
    frame is empty or carries no source_date column -- "we do not know how old this is." That
    is the ONLY way age_days arrives as None (a frame with any parseable date always yields a
    day count), so an absent age is read here as unknown rather than falling through to the
    green "Values current" pill. The old fall-through turned an absence into a positive
    assertion about the world, on two surfaces whose own captions tell the reader to check
    this pill when something looks off."""
    if age_days is None:
        return f'<span class="tl-pill unknown">{FRESHNESS_UNKNOWN_TEXT}</span>'
    if is_stale:
        return f'<span class="tl-pill stale">Values {age_days}d stale</span>'
    return '<span class="tl-pill fresh">Values current</span>'


def asset_label_html(name: str, pos: str, team: Optional[str], is_pick: bool) -> str:
    tag = pos if is_pick else (f"{pos} · {team}" if team else pos)
    badge = '<span class="tl-pickbadge">EST</span>' if is_pick else ""
    return f'<b>{name}</b> <span class="tl-postag">{tag}{badge}</span>'


def value_html(value: Optional[float]) -> str:
    if value is None:
        return '<div class="tl-value tl-dim">—</div>'
    return f'<div class="tl-value">{value:.0f}</div>'


def selected_tag_html(side: str) -> str:
    return (
        '<span class="tl-selected-send">→ SENDING</span>' if side == "send"
        else '<span class="tl-selected-receive">← RECEIVING</span>'
    )


_DIRECTIONAL = {"favorable", "unfavorable"}


def overall_synthesis(raw_verdict: Optional[str], fit_verdict: Optional[str]) -> Optional[str]:
    """Raw Value and Roster Fit are computed independently in app.py -- this only describes
    the RELATIONSHIP between two already-decided verdicts, never re-derives either one.
    Neither verdict is subordinate to the other by construction: a real disagreement between
    them says "depends on your objective," not "here's the real answer." Returns None when
    there isn't enough signal on at least one side to say anything meaningful."""
    if not raw_verdict or not fit_verdict:
        return None
    raw_directional = raw_verdict in _DIRECTIONAL
    fit_directional = fit_verdict in _DIRECTIONAL
    if raw_directional and fit_directional:
        if raw_verdict != fit_verdict:
            return "↔️ Depends on your objective — Raw Value and Roster Fit point in different directions."
        return f"Both reads agree — {raw_verdict}."
    if raw_verdict == "Balanced" and fit_verdict == "neutral":
        return "Both reads are essentially even — no strong case either way."
    if raw_directional and fit_verdict == "neutral":
        return f"Raw Value is {raw_verdict}; Roster Fit is neutral — the case for this trade rests on the numbers alone."
    if fit_directional and raw_verdict == "Balanced":
        return f"Raw Value is essentially even; Roster Fit is {fit_verdict} — the case for this trade rests on roster construction alone."
    return None
