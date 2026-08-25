"""The production port of the validated "merged board" interaction model (see the design
thread: three concept explorations -> a merged model -> a polish pass, all reviewed and
approved before this file existed) -- a canonical ranked list (A) with an inline causal
explanation on focus (C) and quiet, synchronized force-tick highlighting (B, subordinated
to A, never zones). Rendered via st.components.v1.html as a genuinely separate document
(an iframe, not inline DOM) specifically so its hover/keyboard/expand/motion interactions
never trigger a Streamlit rerun -- those are pure client-side presentation states over data
Python already computed once; nothing here should cost a full app.py re-execution just to
expand a row or move a keyboard focus ring.

This module is the Draft Room's own presentation layer over CDME (the Contextual Decision
Matrix Engine -- see README.md's "The Draft Engine" section): it translates an already-frozen
PickSnapshot into HTML, never a second ranking authority.

This module does two things and nothing else:
  serialize_snapshot -- PickSnapshot -> a plain, JSON-able dict. Every field is read
    directly off CandidateSnapshot; nothing here computes, re-derives, or classifies a new
    value. decision_regime and the four decision-path flags (near_tie_with_leader,
    cliff_protection, block_opportunity, pure_value, context_elevated) already exist on the
    engine's own output -- this only reshapes field NAMES for the JS side, never their
    VALUES.
  render_board_html -- the payload -> a complete, self-contained HTML document (CSS + JS
    inlined, no external requests) built on design_system's shared tokens and badge-
    necessity-* CSS (the same source app.py's own <style> block reads from), so the
    embedded iframe reads as the same product, not a bolted-on component with its own
    palette that could quietly drift from app.py's.

Known, deliberate scope limit: the design pass's "Simulate: top pick taken" FLIP transition
demonstrated board-level continuity across a real draft-state change, but that demo ran
within one page load's persistent DOM. st.components.v1.html remounts a fresh iframe on
every Streamlit rerun (a real pick landing included), so there is no "before" DOM to FLIP
from without separately persisting row positions across reruns -- out of scope for this
pass; the board still updates correctly, it just doesn't slide rows into their new rank the
way the standalone mockup did. Worth a real component (not st.components.v1.html) later if
that continuity turns out to matter in practice.
"""

from __future__ import annotations

import json
from typing import Optional

import design_system
from pick_synthesis import CandidateSnapshot, PickSnapshot

# The class NAMES the necessity badges use in the embedded HTML below -- the CSS itself
# comes from design_system.BADGE_NECESSITY_CSS, the same source app.py's own <style> block
# reads from, so the two can't quietly diverge the way two hardcoded copies could.
_NECESSITY_CLASS = {
    "MUST TAKE": "badge-necessity-must-take",
    "STRONG ACTION": "badge-necessity-strong",
    "PREFERRED": "badge-necessity-preferred",
    "CLOSE CALL": "badge-necessity-close-call",
    "LOW URGENCY": "badge-necessity-low",
    "DOESN'T MATTER MUCH": "badge-necessity-low",
}


def _forces(c: CandidateSnapshot) -> list[str]:
    forces = []
    if c.near_tie_with_leader:
        forces.append("tie")
    if c.cliff_protection:
        forces.append("cliff")
    if c.block_opportunity:
        forces.append("block")
    if c.pure_value:
        forces.append("pure")
    return forces


def _context_gap(c: CandidateSnapshot) -> Optional[str]:
    """"elevated" / "suppressed" / None -- the two directions from pick_synthesis's own
    decision_path_flags, renamed for the UI layer only. context_elevated and pure_value are
    NOT mutually exclusive by construction (see decision_path_flags' own docstring), but
    context_elevated is checked first here since it's the simpler, always-computable
    per-candidate fact; a candidate satisfying both still only shows one glyph (this is a
    presentation choice -- the pure-value force tick is a separate, additional signal that
    still renders regardless of which direction wins here)."""
    if c.context_elevated:
        return "elevated"
    if c.pure_value:
        return "suppressed"
    return None


def serialize_candidate(c: CandidateSnapshot) -> dict:
    """One CandidateSnapshot -> the plain dict the board's JS expects. Field-for-field off
    the real snapshot; the only computed value here is _forces/_context_gap, both pure
    renamings of booleans the engine already produced."""
    cliff = c.positional_cliff or {}
    return {
        "id": c.player_id,
        "name": c.name,
        "pos": c.position,
        "team": c.team or "",
        "uv": c.universal_value,
        "tav": c.team_acquisition_value,
        "necessity": c.necessity_label,
        "necClass": _NECESSITY_CLASS.get(c.necessity_label, "badge-necessity-low"),
        "survival": c.survival_probability,
        "intervening": c.intervening_picks,
        "cliffTier": cliff.get("tier"),
        "cliffGap": cliff.get("gap"),
        "cliffTypical": cliff.get("typical_gap"),
        "forfeit": c.positional_forfeit,
        "rivalPremium": c.rival_premium,
        "denialTeam": c.denial_team,
        "needBonus": c.need_bonus,
        "eligBonus": c.eligibility_bonus,
        "forces": _forces(c),
        "contextGap": _context_gap(c),
        "flagged": False,  # set by serialize_snapshot against user_selected_player_id
    }


def serialize_snapshot(
    snap: PickSnapshot, *, pick_header: str, state_tags: list[str | dict],
) -> dict:
    """The full board payload: every candidate (in the snapshot's own order -- callers
    must not re-sort; ranking is the engine's, not this module's) plus the header/tag
    strings app.py already builds from real draft-state values (pick label, 3RR status,
    intervening-picks-to-next-turn, league format). decision_regime rides along
    unchanged from the snapshot -- this module never recomputes it.

    Each entry in state_tags is either a plain string (rendered as-is) or
    {"label": str, "title": str} -- title becomes a native HTML tooltip on that one tag,
    for a secondary explanation that shouldn't have to sit inline as permanent prose
    elsewhere on the page."""
    candidates = [serialize_candidate(c) for c in snap.candidates]
    if snap.user_selected_player_id is not None:
        for cand in candidates:
            if cand["id"] == str(snap.user_selected_player_id):
                cand["flagged"] = True
    return {
        "pickHeader": pick_header,
        "stateTags": state_tags,
        "decisionRegime": snap.decision_regime,
        "candidates": candidates,
    }


# ---------------------------------------------------------------------------------------
# HTML template. A single placeholder token, replaced via plain str.replace (not .format
# or an f-string): the CSS and JS below are full of literal `{`/`}`, which would need
# escaping everywhere under either of those -- a plain token substitution sidesteps that
# entirely rather than fighting it.
# ---------------------------------------------------------------------------------------

_PAYLOAD_TOKEN = "__DRAFT_BOARD_PAYLOAD_JSON__"
_ROOT_TOKENS_TOKEN = "__DESIGN_SYSTEM_ROOT_TOKENS__"
_BADGE_NECESSITY_TOKEN = "__DESIGN_SYSTEM_BADGE_NECESSITY__"

_TEMPLATE_SOURCE = r"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
__DESIGN_SYSTEM_ROOT_TOKENS__
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  background: var(--bg); color: var(--ink); padding: .2rem .1rem 1rem;
  font-family: "Segoe UI", system-ui, sans-serif; line-height: 1.5; font-size: 15px;
}
.mono { font-family: "JetBrains Mono", "DejaVu Sans Mono", monospace; }

.state-bar {
  display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
  background: var(--surface); border: 1px solid var(--line); border-radius: 8px;
  padding: .7rem 1rem; margin: 0 0 .9rem;
  background-image: linear-gradient(90deg, var(--emerald), var(--gold), var(--violet), var(--crimson));
  background-size: 100% 2px; background-repeat: no-repeat; background-position: top;
}
.state-bar .clock { font-weight: 700; font-size: .98rem; }
.state-tags { display: flex; gap: .5rem; flex-wrap: wrap; font-size: .76rem; }
.tag { font-family: "JetBrains Mono", monospace; padding: .2rem .55rem; border-radius: 4px; background: var(--surface-2); border: 1px solid var(--line-2); color: var(--muted); letter-spacing: .03em; }
.tag.hot { color: var(--crimson-b); border-color: var(--crimson); background: rgba(185,28,28,.14); }

__DESIGN_SYSTEM_BADGE_NECESSITY__
.necessity-pill { font-family: "JetBrains Mono", monospace; font-size: .68rem; font-weight: 700; padding: .18rem .5rem; border-radius: 4px; letter-spacing: .03em; white-space: nowrap; }

.board { display: flex; flex-direction: column; gap: .4rem; }
.row {
  background: var(--surface); border: 1px solid var(--line); border-radius: 8px;
  padding: .8rem 1rem; cursor: pointer;
  transition: border-color .15s ease, opacity .2s ease;
}
.row:hover { border-color: var(--line-2); }
.row.expanded { border-color: var(--sky); cursor: default; }
.row:focus { outline: none; }
.row:focus-visible { outline: 2px solid var(--gold); outline-offset: -1px; }

.row-head { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
.row-id { display: flex; align-items: baseline; gap: .6rem; min-width: 0; }
.rank { color: var(--dim); font-size: .78rem; width: 1.3rem; flex-shrink: 0; }
.name { font-size: .95rem; font-weight: 600; }
.posteam { color: var(--muted); font-size: .8rem; }
.considering { font-size: .62rem; font-weight: 700; color: var(--gold-b); letter-spacing: .05em; }
.row-metrics { display: flex; align-items: center; gap: .6rem; flex-wrap: wrap; }
.tav { font-size: 1rem; font-weight: 700; min-width: 3.1rem; text-align: right; }
.chevron { color: var(--dim); font-size: .7rem; transition: transform .15s ease; }
.row.expanded .chevron { transform: rotate(180deg); }

.context-gap { font-size: .72rem; opacity: .62; cursor: help; }
.context-gap.ctx-up { color: var(--tie-b); }
.context-gap.ctx-down { color: var(--pure); }

.ticks { display: flex; gap: .3rem; align-items: center; }
.tick {
  font-size: .76rem; opacity: .28; filter: grayscale(.6); border-radius: 4px; padding: 0 .15rem;
  transition: opacity .15s ease, filter .15s ease, background .15s ease;
}
.tick.active { opacity: 1; filter: none; }
.tick[data-force="tie"] { color: var(--tie-b); }
.tick[data-force="cliff"] { color: var(--cliff-b); }
.tick[data-force="block"] { color: var(--block-b); }
.tick[data-force="pure"] { color: var(--pure); }
.tick.anchor[data-force="tie"] { background: rgba(100,116,139,.18); }
.tick.anchor[data-force="cliff"] { background: rgba(13,148,136,.18); }
.tick.anchor[data-force="block"] { background: rgba(194,65,12,.18); }
.tick.anchor[data-force="pure"] { background: rgba(203,213,225,.14); }

.hover-note {
  font-size: .78rem; color: var(--muted); margin-top: .4rem; padding-top: .4rem;
  border-top: 1px dashed var(--line-2); display: none;
}
.row.hover-active .hover-note { display: block; }

.focus-wrap { display: grid; grid-template-rows: 0fr; transition: grid-template-rows .22s ease; }
.row.expanded .focus-wrap { grid-template-rows: 1fr; }
.focus-inner { overflow: hidden; min-height: 0; }
.focus-body {
  margin-top: .75rem; padding-top: .75rem; border-top: 1px solid var(--line-2);
  opacity: 0; transition: opacity .15s ease;
}
.row.expanded .focus-body { opacity: 1; transition-delay: .05s; }
.focus-sentence { font-size: .87rem; color: var(--ink); margin: 0 0 .5rem; line-height: 1.5; max-width: 68ch; }
.focus-sentence:last-of-type { margin-bottom: 0; }
.focus-sentence b { font-weight: 700; }
.focus-sentence.tie-note { color: var(--muted); }
.focus-metrics { display: flex; gap: 1rem; flex-wrap: wrap; margin-top: .65rem; font-family: "JetBrains Mono", monospace; font-size: .72rem; color: var(--dim); }
.focus-metrics b { color: var(--ink); }

.empty-state { color: var(--muted); font-size: .88rem; padding: 1rem; text-align: center; }

__DESIGN_SYSTEM_REDUCED_MOTION__
</style></head>
<body>
  <div class="state-bar" id="state-bar"></div>
  <div class="board" id="board" role="listbox" aria-label="Draft candidates, ranked by acquisition value"></div>

<script>
const PAYLOAD = __DRAFT_BOARD_PAYLOAD_JSON__;
const ordered = PAYLOAD.candidates; // already in the engine's own order -- never re-sorted here

const TICK_GLYPH = { tie: "≈", cliff: "🛡", block: "⚔", pure: "💎" };
const NEC_TEXT = {
  "MUST TAKE": "a genuine must-take", "STRONG ACTION": "a strong action",
  "PREFERRED": "a preferred, defensible", "CLOSE CALL": "a real close call",
  "LOW URGENCY": "low urgency", "DOESN'T MATTER MUCH": "not one that matters much",
};

document.getElementById("state-bar").innerHTML = `
  <div class="clock">${PAYLOAD.pickHeader}</div>
  <div class="state-tags">${(PAYLOAD.stateTags || []).map(t => {
    // A tag is either a plain string (unchanged) or {label, title} -- title becomes a
    // native HTML title attribute (a real, if plain, browser tooltip on hover), for a
    // secondary explanation that shouldn't sit inline as permanent prose (see app.py's own
    // Draft Room caption, moved into a "?" tag this way instead of running on every render).
    const label = typeof t === "string" ? t : t.label;
    const tooltip = typeof t === "string" ? "" : (t.title || "");
    const titleAttr = tooltip ? ` title="${tooltip.replace(/"/g, "&quot;")}"` : "";
    return `<span class="tag${/3RR/.test(label) ? ' hot' : ''}"${titleAttr}>${label}</span>`;
  }).join("")}</div>`;

function tickRow(c) {
  return ["tie", "cliff", "block", "pure"].map(f =>
    c.forces.includes(f) ? `<span class="tick" data-force="${f}" data-owner="${c.id}">${TICK_GLYPH[f]}</span>` : ""
  ).join("");
}

function contextGapGlyph(c) {
  if (c.contextGap === "elevated") {
    const gap = (c.tav - c.uv).toFixed(1);
    return `<span class="context-gap ctx-up" title="Context Gap: roster fit is elevating his acquisition value well beyond his raw talent (+${gap}).">▲</span>`;
  }
  if (c.contextGap === "suppressed") {
    const leaderUv = ordered[0].uv;
    const gap = (c.uv - leaderUv).toFixed(1);
    return `<span class="context-gap ctx-down" title="Context Gap: his raw talent exceeds the board leader's own value by ${gap} -- he trails only on acquisition rank.">▽</span>`;
  }
  return "";
}

function connectionSentence(c) {
  const partners = f => ordered.filter(o => o.id !== c.id && o.forces.includes(f)).map(o => o.name);
  const parts = [];
  if (c.forces.includes("tie")) {
    const p = partners("tie");
    if (p.length) parts.push(`Within the near-tie band: ${p.join(", ")}.`);
  }
  if (c.forces.includes("cliff")) {
    const p = partners("cliff");
    if (p.length) parts.push(`Same positional cliff as ${p.join(", ")} — the tier is closing for both.`);
  }
  if (c.forces.includes("block")) {
    parts.push(`Denies ${c.denialTeam || "a rival"}, who has nothing comparable behind him.`);
  }
  return parts.join(" ");
}

function focusSentences(c) {
  const s = [];
  const isLeader = ordered[0].id === c.id;

  if (PAYLOAD.decisionRegime === "decisive" && isLeader) {
    s.push(`<p class="focus-sentence"><b>Best-in-class talent, full stop.</b> ${c.survival != null ? Math.round(c.survival * 100) + '% survival to your next turn — ' : ''}he is not walking back to this roster. Take the elite asset.</p>`);
    const support = [];
    if (c.forces.includes("cliff") && c.forfeit != null) support.push(`the position is thinning fast behind him (≈${c.forfeit.toFixed(0)} pts if you wait)`);
    if (c.forces.includes("block")) support.push(`it also denies ${c.denialTeam || "a rival"} a real need`);
    if (c.needBonus > 0) support.push(`it fills a genuine roster gap`);
    if (support.length) {
      s.push(`<p class="focus-sentence tie-note">For context: ${support.join(", and ")}. None of that is why he's the pick — it's just additional reasons the pick was never close.</p>`);
    }
    return s.join("");
  }

  const survivalBit = c.survival != null
    ? `${Math.round(c.survival * 100)}% survival to your next turn${c.intervening != null ? ` across ${c.intervening} intervening pick(s)` : ''}`
    : `survival to your next turn isn't estimable right now`;
  s.push(`<p class="focus-sentence">This is <b>${NEC_TEXT[c.necessity] || c.necessity.toLowerCase()}</b> pick — ${survivalBit}.</p>`);

  if (c.forces.includes("cliff") && c.forfeit != null) {
    s.push(`<p class="focus-sentence">Waiting on him costs about <b>${c.forfeit.toFixed(1)} universal-value points</b> by your next turn — a ${c.cliffTier} positional cliff${c.cliffGap != null ? ` (${c.cliffGap.toFixed(1)}-point gap to the next best ${c.pos}, vs. a typical ${(c.cliffTypical || 0).toFixed(1)})` : ''}.</p>`);
  }
  if (c.forces.includes("block")) {
    s.push(`<p class="focus-sentence"><b>${c.denialTeam || "A rival"}</b> has a real hole here${c.rivalPremium != null ? ` — a ${c.rivalPremium.toFixed(1)}-point rival premium, not routine need` : ''}. Taking him is value and denial at once.</p>`);
  }
  if (c.forces.includes("pure")) {
    s.push(`<p class="focus-sentence">His raw universal value (<b>${c.uv}</b>) is the best in this field — context, not quality, is what's holding his acquisition rank down.</p>`);
  }
  if (c.forces.includes("tie")) {
    const partners = ordered.filter(o => o.id !== c.id && o.forces.includes("tie")).map(o => o.name);
    s.push(isLeader
      ? `<p class="focus-sentence tie-note">${partners.join(", ")} sit within the measured noise band of him — a real group, not a clear lead. Their preference for someone else here isn't a disagreement with the model.</p>`
      : `<p class="focus-sentence tie-note">He's <b>${(ordered[0].tav - c.tav).toFixed(1)}</b> point(s) off the board leader — inside the measured noise band, so preference is a legitimate tiebreaker here, not a disagreement with the model.</p>`);
  }
  if (c.contextGap === "elevated") {
    s.push(`<p class="focus-sentence tie-note">A meaningful share of his acquisition value here is roster fit, not raw talent — about <b>${(c.tav - c.uv).toFixed(1)} points</b> of context lift. Worth knowing if your read on him leans on talent alone.</p>`);
  }
  if (c.contextGap === "suppressed" && !isLeader) {
    s.push(`<p class="focus-sentence tie-note">His raw talent (UV <b>${c.uv}</b>) arguably exceeds the board leader's own (${ordered[0].uv}) — he trails only because of roster-fit context, not quality.</p>`);
  }
  if (c.needBonus > 0 || c.eligBonus > 0) {
    const bits = [];
    if (c.needBonus > 0) bits.push(`+${c.needBonus.toFixed(1)} for an unfilled roster need`);
    if (c.eligBonus > 0) bits.push(`+${c.eligBonus.toFixed(1)} for multi-position flexibility`);
    s.push(`<p class="focus-sentence tie-note">Fills a real roster gap: ${bits.join(" and ")}.</p>`);
  }
  if (c.flagged) {
    s.push(`<p class="focus-sentence tie-note">You flagged him specifically — nothing here argues for taking him now, and nothing here argues you're wrong to like him for later.</p>`);
  }
  return s.join("");
}

let hoveredId = null, focusedId = null, expandedId = null, rovingIndex = 0;
function anchorId() { return hoveredId || focusedId || expandedId || null; }

function render() {
  const boardEl = document.getElementById("board");
  if (!ordered.length) {
    boardEl.innerHTML = `<div class="empty-state">No candidates available in the current player pool/scope.</div>`;
    return;
  }
  boardEl.innerHTML = ordered.map((c, i) => `
    <div class="row${expandedId === c.id ? ' expanded' : ''}" role="option"
         tabindex="${i === rovingIndex ? 0 : -1}" aria-expanded="${expandedId === c.id}"
         data-id="${c.id}" data-index="${i}">
      <div class="row-head">
        <div class="row-id">
          <span class="rank mono">${i + 1}</span>
          <span class="name">${c.name}</span>
          <span class="posteam">${c.pos}${c.team ? ' · ' + c.team : ''}</span>
          ${c.flagged ? '<span class="considering">★ CONSIDERING</span>' : ''}
        </div>
        <div class="row-metrics">
          <div class="ticks">${tickRow(c)}</div>
          ${contextGapGlyph(c)}
          <span class="necessity-pill ${c.necClass}">${c.necessity}</span>
          <span class="tav mono">${c.tav}</span>
          <span class="chevron mono">▾</span>
        </div>
      </div>
      <div class="hover-note">${connectionSentence(c) || "No shared forces with another candidate right now."}</div>
      <div class="focus-wrap"><div class="focus-inner"><div class="focus-body">${focusSentences(c)}
        <div class="focus-metrics">
          <span>UV <b>${c.uv}</b></span><span>TAV <b>${c.tav}</b></span>
          <span>SURV <b>${c.survival != null ? Math.round(c.survival * 100) + '%' : '—'}</b></span>
          <span>CLIFF <b>${c.cliffTier || '—'}</b></span>
        </div>
      </div></div></div>
    </div>`).join("");

  document.querySelectorAll(".row").forEach((el, i) => {
    const c = ordered[i];
    el.addEventListener("click", () => toggleExpand(c.id));
    el.addEventListener("mouseenter", () => { hoveredId = c.id; syncTicks(); });
    el.addEventListener("mouseleave", () => { hoveredId = null; syncTicks(); });
    el.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") { e.preventDefault(); moveFocus(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); moveFocus(-1); }
      else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleExpand(c.id); }
      else if (e.key === "Escape" && expandedId === c.id) { e.preventDefault(); expandedId = null; render(); }
    });
  });

  boardEl.onfocusin = (e) => {
    const row = e.target.closest(".row");
    if (row) { focusedId = row.dataset.id; syncTicks(); }
  };
  boardEl.onfocusout = (e) => {
    if (!boardEl.contains(e.relatedTarget)) { focusedId = null; syncTicks(); }
  };

  syncTicks();
}

function moveFocus(delta) {
  rovingIndex = Math.max(0, Math.min(ordered.length - 1, rovingIndex + delta));
  const rows = document.querySelectorAll(".row");
  rows.forEach((r, i) => r.setAttribute("tabindex", i === rovingIndex ? "0" : "-1"));
  rows[rovingIndex].focus();
}

function toggleExpand(id) {
  const idx = ordered.findIndex(o => o.id === id);
  rovingIndex = idx;
  expandedId = expandedId === id ? null : id;
  render();
  document.querySelectorAll(".row")[idx].focus();
}

function syncTicks() {
  document.querySelectorAll(".tick").forEach(t => { t.classList.remove("active"); t.classList.remove("anchor"); });
  const id = anchorId();
  const c = id ? ordered.find(o => o.id === id) : null;
  if (!c) return;
  c.forces.forEach(f => {
    document.querySelectorAll(`.tick[data-force="${f}"]`).forEach(t => {
      t.classList.add("active");
      if (t.dataset.owner === id) t.classList.add("anchor");
    });
  });
}

render();
</script>
</body></html>
"""

# Substituted once at import time, not per-render -- these three blocks are static (design
# tokens, not per-request data), so there's no reason to redo the string work on every call
# the way render_board_html's own payload substitution has to.
_TEMPLATE = (
    _TEMPLATE_SOURCE
    .replace(_ROOT_TOKENS_TOKEN, design_system.root_css_block())
    .replace(_BADGE_NECESSITY_TOKEN, design_system.BADGE_NECESSITY_CSS)
    .replace("__DESIGN_SYSTEM_REDUCED_MOTION__", design_system.REDUCED_MOTION_CSS)
)


def render_board_html(payload: dict) -> str:
    """payload (from serialize_snapshot) -> a complete, self-contained HTML document ready
    for st.components.v1.html. json.dumps, not an f-string, injects the payload -- it's the
    only thing here that has to be arbitrary user/player data (names, team codes), so it's
    the only thing that needs real JSON escaping rather than trusted-literal template text.

    json.dumps alone is NOT enough to embed safely inside a <script> block: it does not
    escape "<", so a name/team string containing the literal substring "</script>" would
    prematurely close the tag and break out of the JSON into raw document HTML -- a real
    injection path, not a hypothetical one (confirmed: default json.dumps leaves
    "</script>" completely untouched). Escaping every "<" to its JSON-legal \\u003c form
    neutralizes "</script>", "<!--", and any other tag-like sequence identically, since a
    JSON string decodes \\u003c back to the same character -- the payload's actual VALUES
    are unaffected, only how the closing script tag could ever be spelled inside them."""
    safe_json = json.dumps(payload).replace("<", "\\u003c")
    return _TEMPLATE.replace(_PAYLOAD_TOKEN, safe_json)
