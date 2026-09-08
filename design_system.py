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

LEGIBILITY POLICY -- a written design requirement, deliberately not a build gate.

  Every foreground token (each "-b" brightening, plus ink, muted and pure) and every position
  pill colour is held to WCAG 2.x AA for normal text: >= 4.5:1 against `surface`, the tone
  text actually sits on. `dim` is the one recede-into-the-page role and is held to AA-large
  instead (>= 3.0:1); it is meant to stay BELOW 4.5:1, because raising it would make it
  indistinguishable from `muted`. Measured today: every "-b" token >= 6.34:1 (crimson-b is the
  lowest), ink 13.58, muted 6.25, pure 12.23, dim 3.39, every pill >= 4.5.

  Until 2026-09-06 that floor was asserted by test_design_system, so a token dipping under it
  failed the build. RULED by the owner: "Keep the contrast floor as written policy, not a hard
  code ratchet. A documented design requirement, not an immutable code-law ratchet." The bar a
  ratchet has to meet here is that it prevents a DEMONSTRATED class of failure; no contrast
  failure has ever been demonstrated in this palette, so that check encoded a preference in a
  defect ratchet's clothing, and every future visual adjustment would have had to clear it or
  break the build. What survives is the standard (this paragraph), the instrument
  (contrast_ratio, legibility_report) and the visibility: `python3 design_system.py` prints
  every name against its floor, and the suite runs warn_if_out_of_policy() once, uncaught, so
  a shortfall appears in the run's output as a LegibilityWarning without failing it. A palette
  edit that drops below the floor is therefore seen, not stopped, and whoever makes it is
  expected to say why in the commit.
"""

from __future__ import annotations

import re
import warnings

# One canonical hex value per named token, reused everywhere as a CSS custom property
# (--<key>). Semantic hues carry the SAME meaning on every surface: emerald = value
# surplus/good, amber = attention (a heads-up that is not an error: stale values, a
# Questionable status, thin depth, a legality promotion, the CLOSE CALL tier), crimson =
# risk/injury/negative, violet = highest urgency (must-take), sky = strong secondary signal,
# cliff/block/pure/tie = the four decision-path forces first established in the Draft Room.
# GOLD IS NOT ON THAT LIST. It is the brand's metal -- wordmark, rails, focus ring, gradient
# hairlines, the CONSIDERING star -- and it means nothing; the ruling that took it out of the
# semantic channel, and what that cost, is recorded at `amber` below.
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
    # amber was NOT a token before the repaint: BADGE_ROLE_CSS's "notice" badge spelled out
    # #f59e0b/#fbbf24 by hand, a fourth color family with no entry here and nothing keeping it
    # honest. When it was added it was squeezed -- dE 25.8 from gold and 26.2 from block,
    # against 35.2 for every other pair -- because gold was carrying three jobs at once (brand
    # chrome, the Beat chair, and "attention"), and narrowing that load was left to the owner.
    #
    # RULED (2026-09-06): "Gold may remain brand chrome/flourish, but do not ingest it into the
    # semantic UI/data channel where doing so creates a collision. Brand decoration is allowed;
    # semantic ambiguity isn't." Applied by moving every semantic use OFF gold and onto tokens
    # that already exist -- no new hex -- with each move measured in CIE Lab dE, the same
    # instrument the repaint used:
    #   "attention" (the Questionable injury pill, the warn chips, the stale-values pill, the
    #     EST pick badge) -> amber, which already meant "system notice": one hue, one meaning.
    #     amber-b sits >= 39.8 from every position pill it shares a roster row with (TE is the
    #     nearest; it was 57.2 from gold-b) and 69.0 from crimson-b, the other injury colour.
    #   Beat chair -> cliff. The role family's tightest pair moves from gold/amber 25.8 to
    #     violet/sky 36.7 (base tokens; 22.2 -> 30.8 on the "-b" text colours, and that 30.8
    #     is the pre-existing Contrarian/Summary pair, untouched here). Beat's own nearest
    #     neighbours are cliff/tie 40.2 and cliff/emerald 40.5. The cost, recorded rather than
    #     hidden: a Beat badge in the Prytaneum column and a cliff force tick in a board row
    #     now share a hue on the Draft Room page. They never share a visual unit, which is the
    #     co-occurrence POSITION_PILL_TOKENS' rule below was narrowed to, and User/tie is the
    #     existing precedent for a chair borrowing a force's token.
    #   CLOSE CALL tier -> amber, keeping the ramp's shape (red -> amber -> green -> blue ->
    #     purple; the family's tightest pair stays violet/sky). The cost, also recorded: inside
    #     a board row the pill's nearest tick is now block-b at 23.8 (it was 34.6 from gold-b),
    #     and it shares amber with the FILLS REQUIRED SLOT marker, which pick_synthesis sets on
    #     essentially no rows. Gold would have kept 34.6 from the tick and 22.2 from that
    #     marker -- and a gold pill inside a gold-railed, gold-starred row is exactly the
    #     ambiguity the ruling forbids: the most common tier reading as decoration.
    # Every home for CLOSE CALL collides with something in its own row; this one collides least
    # often. What is left is amber's squeeze against block (26.2), now the tightest pair in the
    # ladder. Re-deriving amber away from block, now that gold no longer hems it in on the
    # other side, is the remaining lever -- a palette decision, not settled here.
    "amber": "#e07b0a", "amber-b": "#f9a828",
    "cliff": "#0d9488", "cliff-b": "#3ad9c8",
    "block": "#c2410c", "block-b": "#f9a05c",
    "pure": "#e2d8c3",
    "tie": "#7b7059", "tie-b": "#a99d84",
    "status-ok": "#4ee08c", "status-bad": "#7b7059",
}

FONT_SANS = '"Segoe UI", system-ui, sans-serif'
FONT_MONO = '"JetBrains Mono", "DejaVu Sans Mono", monospace'
# The same stack, single-quoted, for the ONE context that cannot take the double-quoted
# form: an inline HTML style="..." attribute, where an inner double quote ends the
# attribute. Derived from FONT_MONO rather than retyped -- the two app.py chip builders
# that need it had each hand-written a shortened `'JetBrains Mono',monospace` and dropped
# the DejaVu fallback in the process, which is exactly the drift a derived constant closes.
FONT_MONO_ATTR = FONT_MONO.replace('"', "'")
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


# ---------------------------------------------------------------------------------------
# DISPLAY CONTRACT (#116). What each number a person is shown IS, and what unit it is in --
# one vocabulary shared by every surface that renders an engine quantity (app.py's metric
# cards, draft_board_ui's prose and focus metrics, screen_context's evidence lines), so the
# unit a card states cannot drift from the unit the board's sentence states.
#
# WHY IT IS NEEDED, measured (test_display_contract_boundary): universal_value and
# team_acquisition_value are SIGNED and UNBOUNDED -- 10.9% of the candidates a user is shown
# carry a negative acquisition value -- while projected_points is a season fantasy total that
# is never negative (0 of 48,708). The cards used to sit the two side by side, identically
# formatted, with only the points card naming its unit, so the value cards borrowed "points"
# in the fantasy sense. The scale is deliberately NOT normalised here (D10 option B waits on
# #58); the repair is to say what the number is, everywhere it appears.
#
# VOCABULARY. The engine's value quantities all live on one scale, universal_value's:
#   BPA (value over replacement, in projected points -- the pool-gap rescale that used to sit
#   here was removed by the bpa-unit repair; draft_room._scale_vor_to_bpa is the identity)
#   + dynasty-horizon and injury-risk adjustments = universal value;
#   + the roster's need, lineup-flexibility and depth-insurance terms, minus the league
#   anchor's over-credit for a slot the roster cannot offer (#216) = acquisition value.
# That scale is called "universal-value points", abbreviated "UV pts" where a label must stay
# short. Season fantasy points are always called that. Nothing here names a data vendor.
# ---------------------------------------------------------------------------------------

#: The long and short spelling of the engine's own value unit. The board's prose already said
#: "universal-value points" in its one fully qualified phrase; the abbreviation is derived from
#: it so a reader who hovers a short label finds the long form in the help text.
VALUE_UNIT = "universal-value points"
VALUE_UNIT_SHORT = "UV pts"
SEASON_POINTS_UNIT = "season fantasy points"

#: {quantity: {"label", "unit", "help"}} for every quantity a metric card renders. `label`
#: names the unit in parentheses so it is readable without a hover; `help` is the sentence a
#: hover shows (st.metric's `help=`), saying what the number is and what it is not.
DISPLAY_CONTRACT: dict[str, dict[str, str]] = {
    "universal_value": {
        "label": f"Universal Value ({VALUE_UNIT_SHORT})",
        "unit": VALUE_UNIT,
        "help": (
            "How good he is for ANY roster: his projected season points minus the replacement "
            "player's at his position (the league's free alternative at that position's "
            "remaining starter demand), plus dynasty-horizon and injury-risk adjustments. "
            "Universal-value points are signed and unbounded and are NOT fantasy points."
        ),
    },
    "displacement_adj": {
        "label": f"Slot Displacement ({VALUE_UNIT_SHORT})",
        "unit": VALUE_UNIT,
        "help": (
            "Never positive, in universal-value points. How much of his universal value YOUR "
            "lineup cannot use: when every starting slot he could fill is held by one of your "
            "own players who out-projects the league's free alternative, he is priced against "
            "that player instead. Zero when a slot he can reach is open; a dash when it was not "
            "measured -- an unmeasured zero is not room for him."
        ),
    },
    "projected_points": {
        "label": "Projected Points (season)",
        "unit": SEASON_POINTS_UNIT,
        "help": (
            "Projected season fantasy points under this league's scoring. Never negative -- a "
            "different unit from the value cards beside it."
        ),
    },
    "team_acquisition_value": {
        "label": f"Your Acquisition Value ({VALUE_UNIT_SHORT})",
        "unit": VALUE_UNIT,
        "help": (
            "Universal value plus what he is worth to YOUR roster specifically: the "
            "unfilled-need, lineup-flexibility and depth-insurance terms, minus the slot "
            "displacement -- credit the league anchor gave him for a slot your lineup cannot "
            "offer (see that card). Same universal-value points as the Universal Value card; "
            "the difference between the two is roster context, and it can be negative."
        ),
    },
    "survival_probability": {
        "label": "Survival to Next Pick (%)",
        "unit": "percent",
        "help": (
            "Chance he is still on the board at your next turn, compounded across every "
            "intervening pick from those rosters' own boards."
        ),
    },
    "positional_cliff": {
        "label": "Positional Cliff (tier)",
        "unit": "tier",
        "help": (
            "How steep the drop-off in best-player-available value is behind him at his "
            "position, relative to that position's typical gap: HIGH, MEDIUM or LOW. A dash "
            "means no cliff could be measured for him."
        ),
    },
    "position_run": {
        "label": "Run (recent picks)",
        "unit": "detected / none",
        "help": (
            "Whether the last few picks show a run on his position. NONE is a measured "
            "no-run, not a missing value."
        ),
    },
    "opportunity_cost": {
        "label": f"Opportunity Cost of Waiting ({VALUE_UNIT_SHORT})",
        "unit": VALUE_UNIT,
        "help": (
            "Acquisition value you expect to lose by passing: your acquisition value times the "
            "chance he does NOT survive to your next pick. Universal-value points, by your next "
            "turn -- not the whole-draft deferral cost the board states in season points per "
            "week."
        ),
    },
    "expected_value_of_waiting": {
        "label": f"Expected Value If You Wait ({VALUE_UNIT_SHORT})",
        "unit": VALUE_UNIT,
        "help": (
            "Universal value times his chance of surviving to your next pick: what you can "
            "expect to still have available if you pass now. Universal-value points."
        ),
    },
    "denial_value": {
        "label": f"Denial Value ({VALUE_UNIT_SHORT})",
        "unit": VALUE_UNIT,
        "help": (
            "The best acquisition value an intervening rival would have gotten from him, "
            "weighted by how likely that rival was to take him -- what your pick keeps from "
            "someone else. Universal-value points. A 0 is a measurement: either no rival held "
            "a pick before your next turn, or every rival who could be priced would have "
            "gained nothing. Absent (not 0) when no rival's board could price him at all, "
            "because then nothing was measured."
        ),
    },
}

#: The unit that follows a per-field delta in the "What changed?" drawer. The deltas are
#: rendered on one line, so a bare "+3.2" beside a "-0.1" would be two units read as one.
DIFF_UNITS: dict[str, str] = {
    "universal_value": VALUE_UNIT_SHORT, "need_bonus": VALUE_UNIT_SHORT,
    "eligibility_bonus": VALUE_UNIT_SHORT, "depth_exposure": VALUE_UNIT_SHORT,
    "displacement_adj": VALUE_UNIT_SHORT,
    "team_acquisition_value": VALUE_UNIT_SHORT,
    "survival_probability": "probability", "opportunity_cost": VALUE_UNIT_SHORT,
    "expected_value_of_waiting": VALUE_UNIT_SHORT, "denial_value": VALUE_UNIT_SHORT,
    "rival_premium": VALUE_UNIT_SHORT, "positional_forfeit": VALUE_UNIT_SHORT,
    "pick_necessity": "/100",
}


def metric_label(quantity: str) -> str:
    """The card label for one DISPLAY_CONTRACT quantity -- the unit is in the label itself."""
    return DISPLAY_CONTRACT[quantity]["label"]


def metric_help(quantity: str) -> str:
    """The hover sentence for one DISPLAY_CONTRACT quantity."""
    return DISPLAY_CONTRACT[quantity]["help"]


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
    # Was gold until 2026-09-06; the ruling and the dE it cost are recorded at TOKENS["amber"].
    ("badge-beat", "cliff", False),
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
    # Was gold until 2026-09-06 -- same ruling, same record at TOKENS["amber"].
    ("badge-necessity-close-call", "amber", False),
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


#: WCAG 2.x AA minimums for normal and for large text. External standards, not numbers fitted
#: to this palette -- the distinction #56 draws between a bound and a threshold. Which names are
#: held to which is legibility_scope(); why nothing FAILS on them is the LEGIBILITY POLICY in
#: the module docstring.
WCAG_AA_NORMAL_TEXT = 4.5
WCAG_AA_LARGE_TEXT = 3.0


class LegibilityWarning(UserWarning):
    """A name in legibility_scope() measured below its written floor. A warning and never an
    error, by ruling -- see LEGIBILITY POLICY."""


def _contrast_hex(hex_a: str, hex_b: str) -> float:
    def _channel(value: int) -> float:
        c = value / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    def _luminance(hex_value: str) -> float:
        h = hex_value.lstrip("#")
        r, g, b = (_channel(int(h[i:i + 2], 16)) for i in (0, 2, 4))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    la, lb = _luminance(hex_a), _luminance(hex_b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def contrast_ratio(token_a: str, token_b: str) -> float:
    """WCAG 2.x relative-luminance contrast ratio between two TOKENS entries, 1.0 to 21.0.

    Here so the design system can state its own legibility instead of asserting it in a
    comment. The 4.5:1 floor the LEGIBILITY POLICY holds every foreground token to is WCAG AA
    for normal text -- an external standard, not a number chosen to fit this palette, which is
    the whole distinction #56 draws between a bound and a threshold. A repaint that reads well
    to the person making it and falls short here is a repaint that lost information -- which is
    why the shortfall is REPORTED (legibility_report, warn_if_out_of_policy) rather than
    asserted: the standard stays external, the enforcement stays human."""
    return _contrast_hex(TOKENS[token_a], TOKENS[token_b])


def legibility_scope() -> dict[str, float]:
    """{name: floor} -- exactly what the written policy holds, and to what. Pills are keyed
    "pill:<POS>" so one report covers both families. Computed from TOKENS and
    POSITION_PILL_TOKENS at call time rather than listed once, so a token added later is
    inside the policy the moment it exists, not when somebody remembers to enrol it."""
    scope = {name: WCAG_AA_NORMAL_TEXT for name in TOKENS if name.endswith("-b")}
    scope.update({name: WCAG_AA_NORMAL_TEXT for name in ("ink", "muted", "pure") if name in TOKENS})
    if "dim" in TOKENS:
        scope["dim"] = WCAG_AA_LARGE_TEXT
    scope.update({f"pill:{position}": WCAG_AA_NORMAL_TEXT for position in POSITION_PILL_TOKENS})
    return scope


def legibility_report() -> list[dict]:
    """Every name in legibility_scope() measured on `surface`, the tone text sits on:
    [{"name", "hex", "ratio", "floor", "meets"}]. `ratio` is unrounded, so `meets` is the
    same comparison a reader would make from the row and never disagrees with it by a
    rounding. Measures and reports; never asserts."""
    rows = []
    for name, floor in legibility_scope().items():
        hex_value = POSITION_PILL_TOKENS[name[5:]] if name.startswith("pill:") else TOKENS[name]
        ratio = _contrast_hex(hex_value, TOKENS["surface"])
        rows.append({"name": name, "hex": hex_value, "ratio": ratio, "floor": floor,
                     "meets": ratio >= floor})
    return rows


def legibility_shortfalls() -> list[dict]:
    return [row for row in legibility_report() if not row["meets"]]


def warn_if_out_of_policy() -> list[dict]:
    """The whole of the policy's enforcement: ONE LegibilityWarning naming every shortfall,
    returned as well so a caller can print or log it. Visible in any run that calls this,
    fatal in none. Silent, returning [], when the palette is inside policy."""
    short = legibility_shortfalls()
    if short:
        detail = ", ".join(f"{row['name']} {row['ratio']:.2f}:1 < {row['floor']}:1" for row in short)
        warnings.warn(
            f"design_system LEGIBILITY POLICY: below the written floor on surface -- {detail}",
            LegibilityWarning, stacklevel=2,
        )
    return short


# ---------------------------------------------------------------------------------------
# Position identity is a SEPARATE semantic axis from value and urgency, and these colors are
# deliberately not the accents above: a position pill and an injury pill share a table row, so
# an amber TE pill beside an amber Questionable pill would say two different things in one
# color (the Questionable pill was gold until the ruling recorded at TOKENS["amber"]).
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


def main() -> int:
    """`python3 design_system.py`: the LEGIBILITY POLICY, measured, for a person to read.
    Exit 0 whether or not anything is short -- this is the report, not a gate."""
    for row in legibility_report():
        flag = "" if row["meets"] else "   <-- BELOW THE WRITTEN FLOOR"
        print(f"{row['name']:12s} {row['hex']}  {row['ratio']:6.2f}:1  floor {row['floor']}:1{flag}")
    short = legibility_shortfalls()
    print(f"\n{len(short)} of {len(legibility_scope())} below the written floor on `surface` "
          f"-- advisory by ruling (see LEGIBILITY POLICY), exit 0 either way")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
