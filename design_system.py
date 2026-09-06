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

import re

# One canonical hex value per named token, reused everywhere as a CSS custom property
# (--<key>). Semantic hues carry the SAME meaning on every surface: emerald = value
# surplus/good, gold = attention/taxi-bench-alert, crimson = risk/injury/negative, violet =
# highest urgency (must-take), sky = strong secondary signal, amber = system notice,
# cliff/block/pure/tie = the four decision-path forces first established in the Draft Room.
# A "-b" suffix is the identical hue brightened for foreground text/icon use against the dark
# surface tones -- never a different color standing in for the same name.
#
# THE PALETTE IS WARM AND THE ACCENTS ARE GEMSTONES, and the second half of that is the part
# that matters. The ground and chrome are the brand's: a warm near-black under a metallic gold.
# The accents are NOT the brand's, on purpose -- they encode meaning (which chair is speaking,
# how urgent a decision is, which of the four forces is driving a pick), so pulling them toward
# gold for visual unity would destroy information the interface exists to carry. What makes
# both possible at once is that emerald/ruby/amethyst/sapphire/topaz already ARE a hoard: the
# accents can stay maximally distinct from each other and still read as belonging here.
#
# The repaint was measured, not eyeballed, on the two properties that can regress:
#   CONTRAST -- every "-b" foreground token holds >= 6.2:1 on `surface`, all improved or held.
#     `dim` remains AA-large only (3.22:1 -> 3.39:1); it is a deliberate recede-into-the-page
#     role, and it got better rather than worse.
#   SEPARATION -- perceptual distance (CIE Lab dE) between the eight meaning-bearing accents.
#     Worst pair 16.4 -> 35.2. The old palette's tightest collision was crimson vs block
#     (dE 16.4) -- "this player is a risk" against one of the four decision-path forces, two
#     things a user must never confuse. Raw hue-degree separation was tried first and REJECTED
#     as the instrument: it called gold-vs-tie a collision at 2.9 degrees apart, when tie is a
#     near-neutral (saturation 0.28) that no one could mistake for the brand gold. dE accounts
#     for lightness and chroma together and judged the old palette by the same rule.
TOKENS: dict[str, str] = {
    "bg": "#15120b", "surface": "#1f1a11", "surface-2": "#1a1610",
    "line": "#2c2517", "line-2": "#3f3522",
    "ink": "#ece3d2", "muted": "#a79a83", "dim": "#776d5a",
    "emerald": "#1a9e4b", "emerald-b": "#4ee08c",
    "gold": "#d4a017", "gold-b": "#f7cf4a",
    "violet": "#9457d4", "violet-b": "#c9a4f0",
    "crimson": "#b0193c", "crimson-b": "#ff6b85",
    "sky": "#1466c4", "sky-b": "#6fb2f7",
    # amber was NOT a token before this pass: BADGE_ROLE_CSS's "notice" badge spelled out
    # #f59e0b/#fbbf24 by hand, a fourth color family with no entry here and nothing keeping it
    # honest. It is squeezed -- the measured best available separation is only dE 25.8 from
    # gold and dE 26.2 from block, against dE 35.2 for every other pair -- because gold is
    # carrying three jobs at once (brand chrome, the Beat chair, and "attention"). Narrowing
    # gold's semantic load is a decision about what the chairs MEAN, so it is recorded in the
    # register for the owner rather than settled here by choosing a hex.
    "amber": "#e07b0a", "amber-b": "#f9a828",
    "cliff": "#0d9488", "cliff-b": "#3ad9c8",
    "block": "#c2410c", "block-b": "#f9a05c",
    "pure": "#e2d8c3",
    "tie": "#7b7059", "tie-b": "#a99d84",
    "status-ok": "#4ee08c", "status-bad": "#7b7059",
}

FONT_SANS = '"Segoe UI", system-ui, sans-serif'
FONT_MONO = '"JetBrains Mono", "DejaVu Sans Mono", monospace'
# Brand voice, for the wordmark and top-level headings ONLY -- never for data. The fallback
# chain ends at Georgia deliberately: it ships nearly everywhere, so a machine with no webfont
# access still renders a classical serif rather than dropping to the sans and losing the
# brand's one typographic gesture.
FONT_DISPLAY = '"Cinzel", "Trajan Pro", Georgia, "Times New Roman", serif'

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
    the badge blocks below spell out literal rgb triplets rather than var(--token). This is
    that literal triplet's one source of truth instead of a second hand-copied hex value
    drifting from TOKENS over time -- the exact drift found between the Depth Map's own
    hand-rolled 0.28/0.24 alphas and every other badge surface's shared 0.18 convention
    (BADGE_ROLE_CSS, BADGE_NECESSITY_CSS)."""
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
# before this module existed; centralizing them here is what made that impossible.
#
# THEY ARE NOW DERIVED FROM TOKENS RATHER THAN HAND-WRITTEN, because centralizing the text of
# the block never stopped the hex values INSIDE it from drifting, and two had already drifted
# by the time this was checked:
#
#   1. "summary" and "necessity-strong" tinted with #38bdf8 while bordering with #0ea5e9 --
#      two different skies inside one badge, dE 10.6 apart. Neither was the sky token by
#      accident; only the border happened to match.
#   2. "notice" used #f59e0b/#fbbf24, a color family absent from TOKENS entirely, which is
#      how it ended up dE 9.6 from gold-b -- i.e. all but indistinguishable from the "beat"
#      and "close-call" badges it is supposed to contrast with.
#
# Every badge now follows ONE rule, no exceptions: tint = base token at 0.18, text = the
# "-b" brightening of that same token, border = the base token. "user" previously deviated on
# two of the three (tinting with tie-b, texting with pure) and is normalized here; a badge
# family whose whole job is to be told apart at a glance cannot afford per-badge exceptions
# that no rule predicts.
# ---------------------------------------------------------------------------------------

#: Which token carries each badge's meaning, and whether it gets the emphasis glow. The glow
#: is reserved for the two "this is the top of the scale" states (a Moderator VERDICT, and a
#: MUST TAKE necessity) -- it is emphasis, not decoration, and adding a third would dilute it.
_ROLE_BADGES: tuple[tuple[str, str, bool], ...] = (
    ("badge-quant", "emerald", False),
    ("badge-beat", "gold", False),
    ("badge-contrarian", "violet", False),
    ("badge-moderator", "crimson", False),
    ("badge-moderator-verdict", "crimson", True),
    ("badge-user", "tie", False),
    ("badge-summary", "sky", False),
    ("badge-notice", "amber", False),
)

_NECESSITY_BADGES: tuple[tuple[str, str, bool], ...] = (
    ("badge-necessity-must-take", "violet", True),
    ("badge-necessity-strong", "sky", False),
    ("badge-necessity-preferred", "emerald", False),
    ("badge-necessity-close-call", "gold", False),
    ("badge-necessity-low", "crimson", False),
)


def _badge_rule(selector: str, token: str, glow: bool) -> str:
    """One badge's CSS, built from TOKENS. Literal hex rather than var(--token) so the rule
    stays correct in any context that hasn't injected root_css_block() -- same reasoning as
    token_rgba's. Derivation, not indirection, is what removes the drift."""
    parts = [
        f"background: {token_rgba(token, 0.18)}",
        f"color: {TOKENS[f'{token}-b']}",
        f"border: 1px solid {TOKENS[token]}",
    ]
    if glow:
        parts.append(
            f"box-shadow: 0 0 0 1px {token_rgba(f'{token}-b', 0.35)}, "
            f"0 0 8px {token_rgba(token, 0.45)}"
        )
    return f".{selector} {{ " + "; ".join(parts) + "; }"


BADGE_ROLE_CSS = "\n".join(
    [".badge { display: inline-block; padding: 2px 10px; border-radius: 12px; "
     "font-size: 0.75rem; font-weight: 600; margin-bottom: 6px; letter-spacing: 0.02em; }"]
    + [_badge_rule(sel, tok, glow) for sel, tok, glow in _ROLE_BADGES]
)

BADGE_NECESSITY_CSS = "\n".join(
    _badge_rule(sel, tok, glow) for sel, tok, glow in _NECESSITY_BADGES
)


def contrast_ratio(token_a: str, token_b: str) -> float:
    """WCAG 2.x relative-luminance contrast ratio between two TOKENS entries, 1.0 to 21.0.

    Here so the design system can state its own legibility instead of asserting it in a
    comment. The 4.5:1 floor the tests hold every foreground token to is WCAG AA for normal
    text -- an external standard, not a number chosen to fit this palette, which is the whole
    distinction #56 draws between a bound and a threshold. A repaint that reads well to the
    person making it and fails here is a repaint that lost information."""
    def _channel(value: int) -> float:
        c = value / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    def _luminance(token_name: str) -> float:
        hex_value = TOKENS[token_name].lstrip("#")
        r, g, b = (_channel(int(hex_value[i:i + 2], 16)) for i in (0, 2, 4))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    la, lb = _luminance(token_a), _luminance(token_b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ---------------------------------------------------------------------------------------
# Position identity is a SEPARATE semantic axis from value and urgency, and these colors are
# deliberately not the accents above: a position pill and an injury pill share a table row, so
# a gold TE pill beside a gold Questionable pill would say two different things in one color.
#
# THE ORIGINAL CLAIM WAS BROADER THAN THE CODE, AND FALSE. The old hand-written map said its
# colors were "chosen to stay clear of hues this app already uses to MEAN something", while two
# of the six WERE semantic token values copied verbatim -- RB was cliff-b exactly, TE was
# block-b exactly -- and WR was the same drifted #38bdf8 that had leaked into the summary badge.
# Nothing tested the claim, so nothing caught it.
#
# The claim is now narrowed to what actually constrains the design and CAN be checked: a pill
# must be perceptually separable from the two INJURY pill colors it can share a row with, and
# from the other five pills. That is the real co-occurrence; "distinct from every semantic hue
# at once" was never achievable alongside nine accents and was not what the row needed.
POSITION_PILL_TOKENS: dict[str, str] = {
    "QB": "#8f86f0", "RB": "#17bfa0", "WR": "#4aa8ef",
    "TE": "#e8683f", "K": "#a09480", "DEF": "#ef7fc0",
}
#: DEF and DST are the same slot under two spellings, never two different things.
POSITION_PILL_ALIASES: dict[str, str] = {"DST": "DEF"}
#: What a pill falls back to for a position with no entry -- the same neutral K uses, so an
#: unmapped position reads as "no positional claim" rather than borrowing another one's color.
POSITION_PILL_FALLBACK = "K"


def position_pill_color(position: str) -> tuple[str, str]:
    """(tinted background, foreground hex) for a position pill, derived from one map instead of
    a hand-written literal per position. Mirrors the badge convention: the same color at 0.18
    behind its full-strength self."""
    key = POSITION_PILL_ALIASES.get(position, position)
    if key not in POSITION_PILL_TOKENS:
        key = POSITION_PILL_FALLBACK
    hex_value = POSITION_PILL_TOKENS[key]
    h = hex_value.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},0.18)", hex_value


def expand_rgba_markers(css: str) -> str:
    """Expand `__RGBA_<token>_<percent>__` into a real rgba() string from TOKENS.

    CSS needs alpha-blended tints in places a bare custom property cannot supply one
    (`background: rgba(...)` for a 24%-opacity press state, say). Before this, those were
    hand-written triplets -- which is how four of them were still carrying the OLD palette's
    sky long after the token changed, invisible to any search for the token's name. A marker
    keeps the token as the single source while still emitting a literal."""
    return re.sub(
        r"__RGBA_([a-z0-9-]+)_(\d+)__",
        lambda m: token_rgba(m.group(1), int(m.group(2)) / 100.0),
        css,
    )
