"""Shared pieces for the Draft Room mockups: the design tokens (from design_system, never a
second copy), the real-data slice every variant renders, and the JS helpers that make the
absence contract impossible to get wrong by accident.

Run `python3 mockups/build.py` from the repo root to regenerate every `*.html` here. The HTML
files are the deliverable and are committed; this module is how they stay consistent.

THE DATA IS REAL. `_slice.json` was cut from pick_synthesis.build_snapshot against the
committed baseline (a 12-team superflex dynasty league, on the clock at 3.03 with 16 picks to
the next turn; a 12-team IDP-flex league for the horizon-unavailable rows; a 1QB league whose
kicker slots were all filled, for the negative-value row). Names, magnitudes, forces, wait
notes and basis states are the engine's own. Two rows are CONSTRUCTED and say so on screen:
the unpriced position-best with every Optional null (the engine now re-anchors an exhausted
position to its pre-draft level, so a genuinely unpriced row did not occur in the probe), and
a row of measured zeros. Both are the contract's own fixture, not a claim about the baseline.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import design_system as ds  # noqa: E402
from draft_room import SLEEPER_WEEKLY_TO_SEASON_FACTOR  # noqa: E402  the engine's own factor, never a literal
from pick_synthesis import (  # noqa: E402  the engine's own thresholds, never literals
    CLIFF_MIN_MATERIAL_GAP, DECISIVE_SURVIVAL_THRESHOLD, NEAR_TIE_BAND,
)

SLICE = json.loads((HERE / "_slice.json").read_text())

#: The two constructed rows, labelled as such in the data so a variant can show the label.
UNPRICED_FIXTURE = {
    "id": "fx-unpriced", "name": "H Butker", "pos": "K", "team": "KC",
    "uv": None, "tav": None, "proj": None, "necessity": "CLOSE CALL",
    "necClass": "badge-necessity-close-call", "survival": None, "intervening": None,
    "cliffTier": None, "cliffGap": None, "cliffTypical": None, "forfeit": None,
    "rivalPremium": None, "denialTeam": None, "needBonus": None, "eligBonus": None,
    "forces": ["cliff", "pure"], "contextGap": "elevated", "waitNote": None,
    "replacementBasis": None, "growthSignal": None, "fillsRequiredSlot": True, "flagged": False,
    "waiting_cost": None, "horizon_floor": None, "horizon_basis": "unavailable",
    "horizon_sensitivity": None, "depth_exposure": None, "pick_necessity": 50.0,
    "opportunity_cost": None, "expected_value_of_waiting": None, "denial_value": None,
    "positional_forfeit": None, "consensus_rank": None, "consensus_tier": None,
    "reach_label": None, "bpa_source": None, "confidence": None,
    "source": "fixture: unpriced position-best, every Optional field absent, promoted by the feasibility backstop",
}
ZEROS_FIXTURE = {
    "id": "fx-zeros", "name": "C Boswell", "pos": "K", "team": "PIT",
    "uv": 0.0, "tav": 0.0, "proj": 0.0, "necessity": "LOW URGENCY",
    "necClass": "badge-necessity-low", "survival": 0.0, "intervening": 16,
    "cliffTier": "LOW", "cliffGap": 0.0, "cliffTypical": 0.0, "forfeit": 0.0,
    "rivalPremium": 0.0, "denialTeam": None, "needBonus": 0.0, "eligBonus": 0.0,
    "forces": [], "contextGap": None,
    "waitNote": {"tone": "cheap", "label": "free",
                 "title": "Waiting is better than free here. The best K expected to go undrafted projects 0 season points, ahead of C Boswell's 0 -- this pick buys nothing you won't have anyway."},
    "replacementBasis": "live_starter_demand", "growthSignal": None, "fillsRequiredSlot": False,
    "flagged": False, "waiting_cost": 0.0, "horizon_floor": 0.0, "horizon_basis": "measured",
    "horizon_sensitivity": 0.0, "depth_exposure": 0.0, "pick_necessity": 0.0,
    "opportunity_cost": 0.0, "expected_value_of_waiting": 0.0, "denial_value": 0.0,
    "positional_forfeit": 0.0, "consensus_rank": None, "consensus_tier": None,
    "reach_label": None, "bpa_source": "weekly projection, seeded", "confidence": 50.0,
    "source": "fixture: every quantity a measured 0.0 -- each must render as a number",
}


#: bpa_source arrives in `_slice.json` already said without naming anyone -- the probe that cut
#: the slice mapped the engine's source identifiers to WHAT KIND of number anchored the price
#: ("season projection", "weekly projection, seeded", ...), which is what a person needs.


def rows() -> list[dict]:
    real = [dict(r) for r in SLICE["rows"]]
    for r in real:
        r["source"] = "real"
    # Unpriced row sits after the priced rows, where _board_order puts it; ZEROS last.
    return real[:9] + [UNPRICED_FIXTURE] + real[9:] + [ZEROS_FIXTURE]


def payload() -> dict:
    return {
        "pickHeader": SLICE["header"],
        "league": SLICE["league"],
        "intervening": SLICE["intervening"],
        "decisionRegime": SLICE["regime"],
        "valueUnit": ds.VALUE_UNIT,
        "valueUnitShort": ds.VALUE_UNIT_SHORT,
        "contract": ds.DISPLAY_CONTRACT,
        "weeksFactor": SLEEPER_WEEKLY_TO_SEASON_FACTOR,
        # Round 3 reads these so the plate can say WHY the regime is what it is, in the
        # engine's own numbers: the noise band that decides "clear of the field", the survival
        # bar that decides "decisive", and the materiality floor behind the cliff mark (#175).
        "nearTieBand": NEAR_TIE_BAND,
        "decisiveSurvival": DECISIVE_SURVIVAL_THRESHOLD,
        "cliffMinGap": CLIFF_MIN_MATERIAL_GAP,
        "candidates": rows(),
        "nextPicks": ["Roster 5", "Roster 6", "Roster 7", "Roster 8", "Roster 9", "Roster 10",
                      "Roster 11", "Roster 12", "Roster 12", "Roster 11", "Roster 10", "Roster 9",
                      "Roster 8", "Roster 7", "Roster 6", "Roster 5"],
    }


def safe_json(obj) -> str:
    return json.dumps(obj).replace("<", "\\u003c")


# ---------------------------------------------------------------------------------------
# Shared CSS: tokens, motion policy, focus ring, the necessity ramp, position pills, the
# absent mark, and the spec card every mockup opens with.
# ---------------------------------------------------------------------------------------

def pill_css() -> str:
    out = []
    for pos in ds.POSITION_PILL_TOKENS:
        bg, fg = ds.position_pill_color(pos)
        out.append(f".pill-{pos} {{ background: {bg}; color: {fg}; }}")
    for pos in ("DL", "LB", "DB"):
        bg, fg = ds.position_pill_color(pos)
        out.append(f".pill-{pos} {{ background: {bg}; color: {fg}; }}")
    return "\n".join(out)


BASE_CSS = f"""
{ds.root_css_block()}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{ background: var(--bg); color: var(--ink); font-family: {ds.FONT_SANS}; font-size: 15px; line-height: 1.5; }}
.mono {{ font-family: {ds.FONT_MONO}; }}
.display {{ font-family: {ds.FONT_DISPLAY}; letter-spacing: .06em; }}
{ds.FOCUS_VISIBLE_CSS}
{ds.BADGE_NECESSITY_CSS}
{pill_css()}
.pill {{ display: inline-block; font-family: {ds.FONT_MONO}; font-size: .66rem; font-weight: 700; padding: .1rem .4rem; border-radius: 4px; letter-spacing: .04em; }}
.necessity-pill {{ font-family: {ds.FONT_MONO}; font-size: .66rem; font-weight: 700; padding: .16rem .5rem; border-radius: 4px; letter-spacing: .03em; white-space: nowrap; }}
.unit {{ color: var(--muted); font-size: .68em; letter-spacing: .02em; margin-left: .2em; }}
/* ABSENCE. One mark, everywhere: muted, hatched, with a title. It can never be mistaken for a
   small number, an empty cell, or a zero-length bar. */
.absent {{
  color: var(--muted); font-weight: 500; cursor: help; border-radius: 3px; padding: 0 .3em;
  background: repeating-linear-gradient(135deg, transparent 0 3px, color-mix(in srgb, var(--line-2) 75%, transparent) 3px 4px);
}}
.state-word {{ font-family: {ds.FONT_MONO}; font-size: .64rem; letter-spacing: .05em; text-transform: uppercase; padding: .08rem .4rem; border-radius: 3px; border: 1px solid var(--line-2); color: var(--muted); }}
.state-word.measured {{ color: var(--muted); }}
.state-word.imputed {{ color: var(--amber-b); border-color: var(--amber); }}
.state-word.unavailable {{ color: var(--muted); border-style: dashed; }}

/* The spec card: closed by default so the board's own height is what the gate measures. */
.spec {{ margin: 0 0 .5rem; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-2); font-size: .82rem; color: var(--muted); }}
.spec summary {{ cursor: pointer; padding: .55rem .9rem; list-style: none; }}
.spec summary::-webkit-details-marker {{ display: none; }}
.spec summary .hint {{ color: var(--muted); font-size: .74rem; }}
.spec b {{ color: var(--ink); }}
.spec .k {{ font-family: {ds.FONT_MONO}; font-size: .66rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }}
.spec .specbody {{ padding: .2rem .9rem .8rem; display: grid; grid-template-columns: auto 1fr; gap: .25rem .9rem; align-items: baseline; }}
.controls {{ display: flex; gap: .6rem; flex-wrap: wrap; margin: 0 0 .7rem; }}
.controls button {{
  font-family: {ds.FONT_MONO}; font-size: .68rem; letter-spacing: .04em; text-transform: uppercase;
  background: var(--surface); color: var(--muted); border: 1px solid var(--line-2); border-radius: 6px;
  padding: .3rem .7rem; cursor: pointer;
}}
.controls button[aria-pressed="true"] {{ color: var(--ink); border-color: var(--ink); }}
.controls button:focus-visible {{ outline: 2px solid var(--ink); outline-offset: 2px; }}
{ds.REDUCED_MOTION_CSS}
"""

SPEC_HTML = """
<details class="spec">
  <summary><span class="k">Variant</span> <b>{title}</b> — {tagline} <span class="hint">· open for assertion, sacrifice and data</span></summary>
  <div class="specbody">
  <span class="k">Asserts</span><span>{asserts}</span>
  <span class="k">Sacrifices</span><span>{sacrifices}</span>
  <span class="k">Data</span><span>Real snapshot: 12-team superflex dynasty, on the clock at 3.03, 16 picks to the next turn; two real IDP rows from an IDP-flex league (horizon <i>unavailable</i>); one real negative-value kicker priced against the pre-draft anchor. Two rows are <b>constructed fixtures</b> and are marked on screen: an unpriced position-best with every Optional field absent, and a row of measured zeros.</span>
  </div>
</details>
<div class="controls">
  <button id="btn-leader" aria-pressed="false" onclick="toggleLeader(this)">Unpriced row as leader</button>
  <button id="btn-motion" aria-pressed="false" onclick="toggleMotion(this)">Simulate reduced motion</button>
</div>
"""

# ---------------------------------------------------------------------------------------
# Shared JS: the guards, the three-state words, and the two test toggles.
# ---------------------------------------------------------------------------------------

BASE_JS = r"""
const ABSENT = "—";
function num(x) { return typeof x === "number" && Number.isFinite(x); }
function fmt(x, d, unit) {
  if (!num(x)) return `<span class="absent" title="Not measured. This quantity was never computed for him; it is not zero.">${ABSENT}</span>`;
  return `${x.toFixed(d)}${unit ? `<span class="unit">${unit}</span>` : ""}`;
}
function pct(x) { return num(x) ? `${Math.round(x * 100)}%` : `<span class="absent" title="Survival to your next turn was not estimable.">${ABSENT}</span>`; }
function signed(x, d) { return num(x) ? (x > 0 ? "+" : "") + x.toFixed(d) : ABSENT; }
function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;"); }

// The three-state horizon, as WORDS. `measured` / `imputed` / `unavailable` are the engine's
// own vocabulary (pick_synthesis.HORIZON_BASIS_*); a fourth state -- the field not carried at
// all -- renders as nothing rather than as a guess.
function horizon(c) {
  if (c.horizon_basis === "measured") return { word: "measured", cls: "measured",
    text: `Draft-end floor for ${c.pos} is measured from ${c.pos}'s own remaining depth.` };
  if (c.horizon_basis === "imputed") return { word: "estimated", cls: "imputed",
    text: `Draft-end floor for ${c.pos} is an estimate: ${c.pos}'s remaining pool is too thin to measure its own depth decay, so the average of the positions that still can be measured is assumed.` };
  if (c.horizon_basis === "unavailable") return { word: "not measurable", cls: "unavailable",
    text: `The cost of deferring ${c.pos} to the end of the draft is not measurable: the loaded pool for ${c.pos} ends before the draft does, so no draft-end floor exists.` };
  return null;
}
// depth_exposure: the snapshot carries the NUMBER but not its basis (depth_basis is dropped at
// the snapshot boundary), and the engine writes 0.0 for both "measured, no exposure" and "not
// measured" -- so a 0.0 here is rendered as a number with that caveat, never as "safe".
function depth(c) {
  if (!num(c.depth_exposure)) return { text: "Depth insurance: not measured.", val: null };
  if (c.depth_exposure > 0) return { text: `Depth insurance: +${c.depth_exposure.toFixed(1)} UV pts — what one backup at ${c.pos} is worth to your lineup.`, val: c.depth_exposure };
  return { text: "Depth insurance: 0.0 UV pts (the snapshot does not say whether this was measured as zero or not measured at all).", val: 0 };
}
function coverage(cands) {
  const n = cands.filter(c => !num(c.tav)).length;
  if (n === 0) return `every candidate priced`;
  return `${n} of ${cands.length} unpriced · no replacement level · ordered last, not scored`;
}
function forceTitle(f) {
  return { tie: "Near-tie: inside the measured noise band of the board leader",
           cliff: "Cliff protection: the position thins sharply behind him",
           block: "Block opportunity: a rival with a real hole here was positioned to take him",
           pure: "Pure value: his raw universal value is the best in this field" }[f];
}
const GLYPH = { tie: "≈", cliff: "◣", block: "⊘", pure: "◆" };

let candidates = PAYLOAD.candidates.slice();
function toggleLeader(btn) {
  const on = btn.getAttribute("aria-pressed") !== "true";
  btn.setAttribute("aria-pressed", on);
  const fx = PAYLOAD.candidates.find(c => c.id === "fx-unpriced");
  candidates = on ? [fx, ...PAYLOAD.candidates.filter(c => c.id !== "fx-unpriced")] : PAYLOAD.candidates.slice();
  render();
}
function toggleMotion(btn) {
  const on = btn.getAttribute("aria-pressed") !== "true";
  btn.setAttribute("aria-pressed", on);
  document.documentElement.classList.toggle("reduced-motion", on);
}
"""

# A class-based twin of the media query, so the spec card's toggle can demonstrate it.
REDUCED_MOTION_CLASS_CSS = ".reduced-motion *, .reduced-motion *::before, .reduced-motion *::after { transition-duration: .001ms !important; animation-duration: .001ms !important; }"


def page(title: str, tagline: str, asserts: str, sacrifices: str, css: str, body: str, js: str,
         width: str = "1180px") -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc_title(title)} — Draft Room mockup</title>
<style>
{BASE_CSS}
{REDUCED_MOTION_CLASS_CSS}
.page {{ max-width: {width}; margin: 0 auto; padding: 1.2rem 1.2rem 4rem; }}
{css}
</style></head>
<body>
<div class="page">
{SPEC_HTML.format(title=title, tagline=tagline, asserts=asserts, sacrifices=sacrifices)}
{body}
</div>
<script>
const PAYLOAD = {safe_json(payload())};
{BASE_JS}
{js}
render();
</script>
</body></html>
"""


def esc_title(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;")
