"""The single source of truth for the application's shared visual language: color tokens,
typography, motion, and the handful of CSS snippets that must render identically wherever
they appear -- whether that's app.py's own <style> block for native Streamlit chrome, or a
self-contained HTML document embedded via st.components.v1.html (draft_board_ui.py, and any
future card-based surface built the same way).

This module holds tokens and ready-to-use CSS text only. It has no opinion about which
component uses which token and no Streamlit/HTML-structure code of its own -- that judgment
(which of the three interaction paradigms a given surface should follow: ranked list +
causal explanation, comparison/balance, or conversational verdict) lives in the published
design-language reference, not here.
"""

from __future__ import annotations

# One canonical hex value per named token, reused everywhere as a CSS custom property
# (--<key>). Semantic hues carry the SAME meaning on every surface: emerald = value
# surplus/good, gold = attention/taxi-bench-alert, crimson = risk/injury/negative, violet =
# highest urgency (must-take), sky = strong secondary signal, cliff/block/pure/tie = the four
# decision-path forces first established in the Draft Room. A "-b" suffix is the identical
# hue brightened for foreground text/icon use against the dark surface tones -- never a
# different color standing in for the same name.
TOKENS: dict[str, str] = {
    "bg": "#16171a", "surface": "#202124", "surface-2": "#1b1c1f",
    "line": "#2a2b2e", "line-2": "#3a3c42",
    "ink": "#e5e7eb", "muted": "#9ca3af", "dim": "#6b7076",
    "emerald": "#16a34a", "emerald-b": "#4ade80",
    "gold": "#d4a017", "gold-b": "#facc15",
    "violet": "#8b5cf6", "violet-b": "#c4b5fd",
    "crimson": "#b91c1c", "crimson-b": "#f87171",
    "sky": "#0ea5e9", "sky-b": "#7dd3fc",
    "cliff": "#0d9488", "cliff-b": "#2dd4bf",
    "block": "#c2410c", "block-b": "#fb923c",
    "pure": "#cbd5e1",
    "tie": "#64748b", "tie-b": "#94a3b8",
    "status-ok": "#4ade80", "status-bad": "#64748b",
}

FONT_SANS = '"Segoe UI", system-ui, sans-serif'
FONT_MONO = '"JetBrains Mono", "DejaVu Sans Mono", monospace'

# Two speeds only, on purpose (see the design-language reference's motion section). FAST is
# for a state that flips in place (hover, focus, tick lighting); EXPAND is for a size/space
# change (the 0fr->1fr expand panel), always paired with REDUCED_MOTION_CSS below.
TRANSITION_FAST = ".15s ease"
TRANSITION_EXPAND = ".22s ease"

REDUCED_MOTION_CSS = (
    "@media (prefers-reduced-motion: reduce) {\n"
    "  *, *::before, *::after { transition-duration: .001ms !important; animation-duration: .001ms !important; }\n"
    "}"
)

# The one keyboard-focus treatment every interactive row/control on every surface should
# share -- visually distinct from hover, never suppressed. Validated in the Draft Room
# polish pass; every new surface inherits it rather than re-deciding it.
FOCUS_VISIBLE_CSS = (
    ":focus { outline: none; }\n"
    ":focus-visible { outline: 2px solid var(--gold); outline-offset: -1px; }"
)


def token_rgba(token_name: str, alpha: float) -> str:
    """A TOKENS hex value as an alpha-blended `rgba(r,g,b,a)` string -- for the specific,
    recurring case of an inline `style="background-color: ..."` attribute (pandas Styler
    output, e.g.) where a CSS custom property can't be relied on to resolve, the same reason
    TRADE_LEDGER_CSS's own background rules spell out a literal rgb triplet next to a
    var(--token) border rather than using the token for both. This is that literal triplet's
    one source of truth instead of a second hand-copied hex value drifting from TOKENS over
    time -- the exact drift found between the Depth Map's own hand-rolled 0.28/0.24 alphas and
    every other badge surface's shared 0.18 convention (BADGE_ROLE_CSS, BADGE_NECESSITY_CSS)."""
    hex_value = TOKENS[token_name].lstrip("#")
    r, g, b = (int(hex_value[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def root_css_block() -> str:
    """Every TOKENS entry rendered as one `:root { --k: v; ... }` block -- the only place
    that ever spells out these hex values. Every consumer (app.py's native <style>
    injection, draft_board_ui.py's self-contained iframe template, and any future embedded
    surface) calls this instead of copying the block, so the palette can only drift by
    editing TOKENS itself, never by two copies quietly diverging."""
    lines = "\n".join(f"  --{k}: {v};" for k, v in TOKENS.items())
    return f":root {{\n{lines}\n}}"


# ---------------------------------------------------------------------------------------
# Shared badge vocabulary. Two families: role identity (who's speaking -- Quant/Beat/
# Contrarian/Moderator/User/system messages) and necessity (how urgent a decision is -- the
# Draft Room's own vocabulary, but the color ramp is the app's general low-to-high urgency
# scale, reusable by any future surface that needs to say "how urgent is this"). Both were
# duplicated verbatim across app.py's <style> block and draft_board_ui.py's iframe template
# before this module existed; centralizing them here is what makes that impossible now.
# ---------------------------------------------------------------------------------------

BADGE_ROLE_CSS = """
.badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; margin-bottom: 6px; letter-spacing: 0.02em; }
.badge-quant { background: rgba(22,163,74,0.18); color: #4ade80; border: 1px solid #16a34a; }
.badge-beat { background: rgba(212,160,23,0.18); color: #facc15; border: 1px solid #d4a017; }
.badge-contrarian { background: rgba(139,92,246,0.18); color: #c4b5fd; border: 1px solid #8b5cf6; }
.badge-moderator { background: rgba(185,28,28,0.18); color: #f87171; border: 1px solid #b91c1c; }
.badge-moderator-verdict { background: rgba(185,28,28,0.18); color: #f87171; border: 1px solid #b91c1c; box-shadow: 0 0 0 1px rgba(248,113,113,0.35), 0 0 8px rgba(185,28,28,0.45); }
.badge-user { background: rgba(148,163,184,0.18); color: #cbd5e1; border: 1px solid #64748b; }
.badge-summary { background: rgba(56,189,248,0.18); color: #7dd3fc; border: 1px solid #0ea5e9; }
.badge-notice { background: rgba(245,158,11,0.18); color: #fbbf24; border: 1px solid #f59e0b; }
""".strip()

BADGE_NECESSITY_CSS = """
.badge-necessity-must-take { background: rgba(139,92,246,0.18); color: #c4b5fd; border: 1px solid #8b5cf6; box-shadow: 0 0 0 1px rgba(196,181,253,0.35), 0 0 8px rgba(139,92,246,0.45); }
.badge-necessity-strong { background: rgba(56,189,248,0.18); color: #7dd3fc; border: 1px solid #0ea5e9; }
.badge-necessity-preferred { background: rgba(22,163,74,0.18); color: #4ade80; border: 1px solid #16a34a; }
.badge-necessity-close-call { background: rgba(212,160,23,0.18); color: #facc15; border: 1px solid #d4a017; }
.badge-necessity-low { background: rgba(185,28,28,0.18); color: #f87171; border: 1px solid #b91c1c; }
""".strip()
