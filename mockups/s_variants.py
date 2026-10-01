"""Round 2 -- three dialled-in syntheses on one spine.

THE SPINE is C1 Reliquary: the engine's order, value-led rows, a fold for the tail, the unit
legend in `muted` at rest. Every synthesis adds the shared fixes the owner and the critic
converged on:

  EARNED PROSE. `earned()` emits a sentence only when the fact it asserts is present and
    non-obvious. No sentence about an absent number; no sentence that is true of every row
    (depth insurance's caveat lives in the receipt, not the prose); no "the floor is 0 so
    there is no QB left after the draft" -- a draft-end floor of 0 says nothing a drafter
    does not already know, so the deferral sentence needs a floor above zero to exist.
  CONTIGUOUS TIERS. Necessity is not monotonic in value (it carries survival, cliff and run
    terms), so a raw per-row mapping printed "THE DECISION" twice and sized an 11-point row
    above an 85-point one. `tiers()` lets a tier only DESCEND from the top: once the engine's
    urgency drops a band, no later row rises above it. Size therefore never contradicts rank.
  NECESSITY IS READABLE: the engine's own urgency word, coloured, >= .74rem, on every row.
  DECISION REGIME is stated in the clock bar at a readable size, on every board.
  KEYBOARD: roving tabindex, ArrowUp/Down, Enter/Space toggle, Escape closes; the focus ring
    is `ink`, visually distinct from the gold open-row rail (user state, per the ruling).
  EXPANDED BODY = B4's receipt: value · unit · basis · coverage per quantity, each cell
    carrying data-field so the gate asserts per field on the fixture rows.
  COVERAGE CHIP (B1) in the clock bar; B2's absence clauses as title text on every mark.
  GOLD marks the open row and brand chrome only. No tier band, no leader frame, no plate.
  HEIGHT under the production iframe's 1,400px cap at rest -- measured by the gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import design_system as ds  # noqa: E402

# ---------------------------------------------------------------------------------------
# Spine JS: tiers, earned prose, receipt, keyboard, and the shared row.
# ---------------------------------------------------------------------------------------
SPINE_JS = r"""
const U = PAYLOAD.valueUnitShort, CT = PAYLOAD.contract;
const NEC_CLS = { "MUST TAKE": "must", "STRONG ACTION": "strong", "PREFERRED": "pref", "CLOSE CALL": "close", "LOW URGENCY": "low", "DOESN'T MATTER MUCH": "low" };
const ORDER = { decide: 0, context: 1, tail: 2 };
function rawTier(c) {
  if (["MUST TAKE", "STRONG ACTION", "PREFERRED"].includes(c.necessity) || c.forces.includes("tie")) return "decide";
  if (c.necessity === "CLOSE CALL") return "context";
  return "tail";
}
// Contiguous from the top: a tier can only descend. The leader is always `decide`.
function tiers(cands) {
  let cur = "decide";
  return cands.map((c, i) => { const r = i === 0 ? "decide" : rawTier(c); if (ORDER[r] > ORDER[cur]) cur = r; return cur; });
}
function pillPos(c) { return `<span class="pill pill-${c.pos}">${c.pos}</span>`; }
function rival(c) { return c.denialTeam ? (/^\d+$/.test(String(c.denialTeam)) ? `Roster ${c.denialTeam}` : c.denialTeam) : null; }
function fixtureTag(c) { return c.source === "real" ? "" : `<span class="fixture" title="${esc(c.source)}">FIXTURE</span>`; }
function absent(why) { return `<span class="absent" title="${esc(why)}">${ABSENT}</span>`; }
const WHY = {
  tav: "No acquisition value exists for him: his position has no replacement level left to price against. An absence, not a zero.",
  uv: "No universal value exists for him: no replacement level at his position. An absence, not a zero.",
  proj: "No season projection is carried for him.",
  survival: "Survival to your next turn was not estimable for him.",
  need: "The roster-need term was not computed for him.", elig: "The lineup-flexibility term was not computed for him.",
  depth: "Depth insurance was not measured for him.", floor: "No draft-end floor exists for his position: the loaded pool ends before the draft does.",
  oc: "Opportunity cost needs an acquisition value and a survival estimate; one is absent.",
  evw: "Expected value if you wait needs a universal value and a survival estimate; one is absent.",
  denial: "Denial value was not measured for him.", forfeit: "The cost of skipping his position by your next turn was not measured.",
};
function v(field, x, d, suffix) {
  return num(x) ? `<span data-field="${field}"${x < 0 ? ' class="neg"' : ''}>${x.toFixed(d)}${suffix || ""}</span>` : `<span data-field="${field}">${absent(WHY[field])}</span>`;
}
function survivalCell(c) { return num(c.survival) ? `<span data-field="survival" title="Chance he is still on the board at your next turn">${Math.round(c.survival * 100)}%</span>` : `<span data-field="survival">${absent(WHY.survival)}</span>`; }
function horizonWord(c) { const h = horizon(c); return h ? `<span class="state-word ${h.cls}" title="${esc(h.text)}">${h.word}</span>` : ""; }
function waitCell(c) {
  const h = horizon(c);
  if (c.waitNote) return `<span data-field="wait" class="chip ${h ? h.cls : ""}" title="${esc(c.waitNote.title)}${h && h.cls === "imputed" ? " " + esc(h.text) : ""}">${c.waitNote.label}${h && h.cls === "imputed" ? " · est." : ""}</span>`;
  return `<span data-field="wait" class="chip unavailable" title="${esc(h ? h.text : WHY.floor)}">${absent(h ? h.text : WHY.floor)} not measurable</span>`;
}
function ticks(c) { return c.forces.map(f => `<span class="tick" data-force="${f}" title="${forceTitle(f)}">${GLYPH[f]}</span>`).join(""); }
function necWord(c) { return `<span class="nec ${NEC_CLS[c.necessity] || ""}" title="${esc(c.necessity)}: the engine's own urgency tier${num(c.pick_necessity) ? ` (${c.pick_necessity.toFixed(0)}/100)` : ""}">${c.necessity}</span>`; }

// EARNED PROSE. Each entry: {k, label, t} -- k names the fact class (for the plate's factor
// list), label is the short form, t the sentence. Nothing here is emitted for an absent
// number, and nothing that is true of every row.
function earned(c, i, cands) {
  const s = [];
  if (c.fillsRequiredSlot) s.push({ k: "required", label: "Fills a required slot", t: "<b>Fills a required slot.</b> Ranked above higher-scoring candidates because your roster cannot otherwise still be filled legally." });
  if (!num(c.tav)) s.push({ k: "unpriced", label: "Unpriced", t: `<b>Unpriced.</b> ${WHY.tav}` });
  if (c.forces.includes("cliff")) {
    const gap = num(c.cliffGap) && c.cliffGap > 0 ? `${c.cliffGap.toFixed(1)} ${U} of drop-off to the next best ${c.pos}${num(c.cliffTypical) ? ` (typical ${c.cliffTypical.toFixed(1)})` : ""}` : null;
    if (num(c.forfeit) && c.forfeit > 0) s.push({ k: "cliff", label: `Cliff · ${c.forfeit.toFixed(1)} ${U} forfeit by your next turn`, t: `Waiting costs about <b>${c.forfeit.toFixed(1)} ${U}</b> by your next turn${c.cliffTier ? ` — a ${c.cliffTier} positional cliff` : ""}${gap ? ` (${gap})` : ""}.` });
    else if (gap) s.push({ k: "cliff", label: `Cliff · ${c.cliffGap.toFixed(1)} ${U} drop-off behind him`, t: `${c.cliffTier ? c.cliffTier + " p" : "P"}ositional cliff: <b>${gap}</b>.` });
    else s.push({ k: "cliff", label: "Cliff · fired, size not measured", t: "" });
  }
  if (c.forces.includes("block") && rival(c)) {
    const prem = num(c.rivalPremium) && c.rivalPremium > 0 ? ` — a rival premium of ${c.rivalPremium.toFixed(1)} ${U}` : "";
    s.push({ k: "block", label: `Denial · ${rival(c)}${num(c.rivalPremium) && c.rivalPremium > 0 ? `, +${c.rivalPremium.toFixed(1)} ${U}` : ""}`, t: `<b>${rival(c)}</b> has a real hole here${prem}. Taking him is value and denial at once.` });
  }
  if (c.forces.includes("tie") && i > 0 && num(cands[0].tav) && num(c.tav)) {
    const off = (cands[0].tav - c.tav).toFixed(1);
    s.push({ k: "tie", label: `Near-tie · ${off} ${U} off the leader`, t: `Within the measured noise band of the leader — <b>${off} ${U}</b> off; preference is a legitimate tiebreaker.` });
  }
  if (c.forces.includes("pure") && num(c.uv)) s.push({ k: "pure", label: `Pure value · UV ${c.uv.toFixed(0)} ${U}`, t: `His raw universal value (<b>${c.uv.toFixed(1)} ${U}</b>) is the best in this field — context, not quality, holds his acquisition rank down.` });
  // Deferral to the draft's end: only when a real floor exists. A floor of 0 says only that
  // nobody at the position is expected to survive the draft, which is no news to a drafter.
  if (c.waitNote && num(c.horizon_floor) && c.horizon_floor > 0 && num(c.waiting_cost) && num(c.proj)) {
    const h = horizon(c);
    if (c.waiting_cost <= 0) s.push({ k: "wait", label: "Waiting is free", t: `The best ${c.pos} expected to go undrafted projects <b>${c.horizon_floor.toFixed(0)}</b> season points, ahead of his ${c.proj.toFixed(0)} — waiting is free.${h && h.cls === "imputed" ? " That floor is an estimate." : ""}` });
    else s.push({ k: "wait", label: `Deferral · ${(c.waiting_cost / PAYLOAD.weeksFactor).toFixed(2)} season pts/wk`, t: `Deferring ${c.pos} to the end of the draft costs <b>${(c.waiting_cost / PAYLOAD.weeksFactor).toFixed(2)} season pts/wk</b> against a floor of ${c.horizon_floor.toFixed(0)} season points${h ? ` (floor ${h.word})` : ""}.` });
  }
  return s;
}
function survivalFactor(c) { return num(c.survival) ? { k: "survival", label: `Survival · ${Math.round(c.survival * 100)}% to your next turn` } : null; }

// B4's receipt, the expanded body. value · unit · basis · coverage, per quantity.
function receipt(c, i) {
  const h = horizon(c) || { word: "not carried", cls: "unavailable" };
  const anchor = c.replacementBasis ? { word: c.replacementBasis === "predraft_anchor" ? "pre-draft anchor" : "live starter demand", cls: c.replacementBasis === "predraft_anchor" ? "imputed" : "measured" } : { word: "not carried", cls: "unavailable" };
  const src = c.bpa_source ? `${c.bpa_source}${num(c.confidence) ? ` · conf ${c.confidence.toFixed(0)}` : ""}` : "source not carried";
  const M = { word: "measured", cls: "measured" };
  const line = (label, field, x, d, unit, basis, cov) =>
    `<span class="q">${label}</span><span class="val">${v(field, x, d)}</span><span class="u">${unit}</span><span class="b ${basis.cls}">${basis.word}</span><span class="c">${cov}</span>`;
  const depthBasis = num(c.depth_exposure) ? (c.depth_exposure > 0 ? M : { word: "0.0 — basis not carried", cls: "imputed" }) : { word: "not measured", cls: "unavailable" };
  return `<div class="receipt" role="table" aria-label="Every quantity with its unit, basis and coverage">
    <span class="h">quantity</span><span class="h r">value</span><span class="h">unit</span><span class="h">basis</span><span class="h">coverage · source</span>
    ${line("Acquisition value", "tav", c.tav, 1, PAYLOAD.valueUnit, anchor, src)}
    ${line("Universal value", "uv", c.uv, 1, PAYLOAD.valueUnit, anchor, src)}
    ${line("Roster need term", "need", c.needBonus, 1, PAYLOAD.valueUnit, M, "this roster's unfilled slots")}
    ${line("Lineup flexibility term", "elig", c.eligBonus, 1, PAYLOAD.valueUnit, M, "multi-position eligibility")}
    ${line("Depth insurance term", "depth", c.depth_exposure, 1, PAYLOAD.valueUnit, depthBasis, "one lineup re-solve per starter")}
    <span class="rule"></span>
    ${line("Projected points", "proj", c.proj, 0, "season fantasy points", M, src)}
    ${line(`Draft-end floor for ${c.pos}`, "floor", c.horizon_floor, 0, "season fantasy points", h, num(c.horizon_sensitivity) ? `± ${c.horizon_sensitivity.toFixed(0)} across a realistic positional run` : "no error bar")}
    ${line(`Cost of deferring ${c.pos}`, "waitcost", num(c.waiting_cost) ? c.waiting_cost / PAYLOAD.weeksFactor : null, 2, "season pts per week", h, "to the end of the draft")}
    <span class="rule"></span>
    ${line("Survival to your next turn", "survival", num(c.survival) ? c.survival * 100 : null, 0, "percent", num(c.intervening) ? { word: `${c.intervening} picks`, cls: "measured" } : { word: "no pick context", cls: "unavailable" }, "each intervening roster's own board")}
    ${line("Opportunity cost of waiting", "oc", c.opportunity_cost, 1, PAYLOAD.valueUnit, M, "acq value × (1 − survival)")}
    ${line("Expected value if you wait", "evw", c.expected_value_of_waiting, 1, PAYLOAD.valueUnit, M, "universal value × survival")}
    ${line("Denial value", "denial", c.denial_value, 1, PAYLOAD.valueUnit, M, num(c.denial_value) && c.denial_value === 0 ? "a measured 0: no rival positioned to gain" : "best rival's gain × their take probability")}
    ${line(`Cost of skipping ${c.pos} by your next turn`, "forfeit", c.positional_forfeit, 1, PAYLOAD.valueUnit, M, "next-turn horizon")}
  </div>`;
}
// WHY-map keys the receipt uses that the row does not.
WHY.waitcost = WHY.floor;

let openId = null, focusedId = null, tailOpen = false, refocus = false;
// render() replaces the board's DOM, which drops focus to <body>. Any state change that came
// from the keyboard asks the next render to put focus back on the row it was on.
function toggleRow(id, fromKeyboard) { openId = openId === id ? null : id; focusedId = id; refocus = !!fromKeyboard; render(); }
function bandLabel(t) { return { decide: "the decision", context: "context", tail: "tail — low urgency" }[t]; }

function rowHtml(c, i, t, cands, extraCols) {
  const rs = earned(c, i, cands).filter(x => x.t);
  const isOpen = openId === c.id;
  return `<div class="row ${t}${isOpen ? " open" : ""}" role="option" aria-expanded="${isOpen}" tabindex="${(focusedId ? focusedId === c.id : i === 0) ? 0 : -1}" data-id="${c.id}" data-index="${i}">
    <div class="head">
      <span class="rank">${i + 1}</span>
      <span class="who"><span class="name">${c.name}</span>${pillPos(c)}<span class="team">${c.team}</span>${c.fillsRequiredSlot ? '<span class="required" title="Ranked above higher-scoring candidates because your roster cannot otherwise still be filled legally.">FILLS REQUIRED SLOT</span>' : ""}${fixtureTag(c)}</span>
      <span class="ticks">${ticks(c)}</span>
      ${necWord(c)}
      ${extraCols(c)}
      <span class="value" title="Acquisition value in ${PAYLOAD.valueUnit} — signed, unbounded, not fantasy points">${num(c.tav) ? `<span data-field="tav"${c.tav < 0 ? ' class="neg"' : ''}>${c.tav.toFixed(0)}</span><span class="unit">${U}</span>` : `<span data-field="tav">${absent(WHY.tav)}</span>`}</span>
    </div>
    <div class="detail"><div><div class="inner">
      ${rs.length ? rs.map(r => `<p>${r.t}</p>`).join("") : ""}
      ${receipt(c, i)}
    </div></div></div>
  </div>`;
}
function boardHtml(cands, extraCols) {
  const T = tiers(cands);
  const tail = cands.filter((c, i) => T[i] === "tail");
  let last = null;
  return cands.map((c, i) => {
    const t = T[i];
    let band = "";
    if (t !== last) { band = `<div class="band ${t}">${bandLabel(t)}</div>`; last = t; }
    if (t === "tail" && !tailOpen) {
      if (tail[0].id === c.id) return band + `<div class="fold" role="button" tabindex="0" onclick="tailOpen=true;render()" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();tailOpen=true;render()}">${tail.length} low-urgency row${tail.length === 1 ? "" : "s"} folded — values ${valueRange(tail)} · show</div>`;
      return "";
    }
    return band + rowHtml(c, i, t, cands, extraCols);
  }).join("");
}
function valueRange(rows) {
  const vals = rows.map(c => c.tav).filter(num);
  if (!vals.length) return "all unpriced";
  const lo = Math.min(...vals), hi = Math.max(...vals);
  return lo === hi ? `${lo.toFixed(0)} ${U}` : `${lo.toFixed(0)} to ${hi.toFixed(0)} ${U}`;
}
function wireBoard() {
  const rows = [...document.querySelectorAll(".row[role=option]")];
  rows.forEach((el, k) => {
    el.addEventListener("click", () => toggleRow(el.dataset.id, false));
    el.addEventListener("focus", () => { focusedId = el.dataset.id; });
    el.addEventListener("keydown", e => {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        const n = rows[Math.max(0, Math.min(rows.length - 1, k + (e.key === "ArrowDown" ? 1 : -1)))];
        rows.forEach(r => r.setAttribute("tabindex", r === n ? "0" : "-1")); n.focus();
      } else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleRow(el.dataset.id, true); }
      else if (e.key === "Escape" && openId === el.dataset.id) { e.preventDefault(); openId = null; focusedId = el.dataset.id; refocus = true; render(); }
    });
  });
  if (refocus && focusedId) { const el = rows.find(r => r.dataset.id === focusedId); if (el) el.focus(); }
  refocus = false;
}
function clockBar(extra) {
  const cov = coverage(candidates), unpriced = !cov.startsWith("every");
  return `<div class="clock-bar"><div><div class="h display">${PAYLOAD.pickHeader}</div><div class="meta">${PAYLOAD.league} · ${PAYLOAD.intervening} picks to your next turn</div></div>
    <div class="chips"><span class="regime" title="The engine's own read of how contested this pick is: decisive, contested, or exhausted.">regime · ${PAYLOAD.decisionRegime}</span><span class="chip cov ${unpriced ? "notice" : ""}" title="Coverage of the candidate list. An unpriced candidate has no replacement level at his position and no acquisition value; he is ordered last, not scored.">${cov}</span>${extra || ""}</div></div>`;
}
function legend() {
  return `<div class="legend"><span title="${esc(CT.universal_value.help)}"><b>${U}</b> = ${PAYLOAD.valueUnit} · signed · not fantasy points</span><span title="The wait chip is the cost of deferring the position until the draft ends, in season-projection points per week, with the floor's basis: measured, estimated, or not measurable."><b>pts/wk</b> = season points per week to draft end</span><span title="The four decision forces the engine can fire"><b>◣ ⊘ ◆ ≈</b> cliff · block · pure value · near-tie</span><span title="Tiers are contiguous from the top: once the engine's urgency drops a band, no later row rises above it, so row size never contradicts rank.">tiers descend only</span></div>`;
}
"""

# ---------------------------------------------------------------------------------------
# Spine CSS. Gold: the open-row rail and the clock bar's hairline only.
# ---------------------------------------------------------------------------------------
SPINE_CSS = (r"""
.clock-bar { display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap; padding: .75rem 1.1rem; border: 1px solid var(--line); border-radius: 10px; margin-bottom: .6rem;
  background: linear-gradient(180deg, color-mix(in srgb, var(--surface) 80%, transparent), color-mix(in srgb, var(--surface-2) 92%, transparent)); border-top: 1px solid color-mix(in srgb, var(--gold) 40%, var(--line)); }
.clock-bar .h { font-size: 1.15rem; letter-spacing: .08em; color: var(--ink); }
.clock-bar .meta { font-family: "JetBrains Mono", monospace; font-size: .7rem; color: var(--muted); letter-spacing: .04em; }
.chips { display: flex; gap: .45rem; flex-wrap: wrap; align-items: center; }
.regime { font-family: "JetBrains Mono", monospace; font-size: .78rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ink); border: 1px solid var(--line-2); border-radius: 6px; padding: .25rem .6rem; background: var(--surface-2); cursor: help; }
.chip { font-family: "JetBrains Mono", monospace; font-size: .66rem; letter-spacing: .04em; padding: .12rem .45rem; border-radius: 4px; border: 1px solid var(--line-2); color: var(--muted); cursor: help; white-space: nowrap; }
.chip.cov { text-transform: uppercase; }
.chip.notice, .chip.imputed { color: var(--amber-b); border-color: var(--amber); }
.chip.unavailable { border-style: dashed; }
.legend { font-family: "JetBrains Mono", monospace; font-size: .64rem; letter-spacing: .05em; text-transform: uppercase; color: var(--muted); margin: 0 .2rem .5rem; display: flex; gap: 1rem; flex-wrap: wrap; }
.legend span { cursor: help; } .legend b { color: var(--ink); }
.board { display: flex; flex-direction: column; gap: .25rem; position: relative; }
.board::before { content: ""; position: absolute; inset: -6% -4% auto -4%; height: 40%; pointer-events: none; background: radial-gradient(60% 100% at 50% 0%, __GOLD07__, transparent 70%); }
.band { font-family: "JetBrains Mono", monospace; font-size: .62rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); padding: .35rem .3rem .05rem; }
.row { position: relative; border: 1px solid var(--line); border-radius: 9px; cursor: pointer; background: linear-gradient(180deg, color-mix(in srgb, var(--surface) 84%, transparent), color-mix(in srgb, var(--surface-2) 90%, transparent)); transition: border-color .15s ease, box-shadow .15s ease; }
.row:hover { border-color: var(--line-2); }
.row.open { border-color: color-mix(in srgb, var(--gold) 55%, var(--line-2)); box-shadow: inset 3px 0 0 var(--gold), 0 8px 26px rgba(0,0,0,.35); cursor: default; }
.row:focus { outline: none; }
.row:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }
.head { display: grid; grid-template-columns: 2rem minmax(0, 1fr) 4.4rem 8.6rem 4rem 9.6rem 6.2rem; align-items: center; gap: .7rem; }
.row.decide { padding: .55rem 1rem; }
.row.decide .name { font-size: 1.05rem; font-weight: 700; }
.row.decide .value { font-size: 1.45rem; }
.row.context { padding: .45rem 1rem; }
.row.context .name { font-size: .95rem; font-weight: 600; }
.row.context .value { font-size: 1.15rem; }
.row.tail { padding: .3rem 1rem; background: transparent; }
.row.tail .name { font-size: .88rem; font-weight: 500; }
.row.tail .value { font-size: 1rem; }
.rank { font-family: "JetBrains Mono", monospace; color: var(--muted); font-size: .74rem; }
.who { display: flex; align-items: baseline; gap: .5rem; min-width: 0; flex-wrap: wrap; }
.team { color: var(--muted); font-size: .78rem; }
.ticks { display: flex; gap: .3rem; }
.tick { font-family: "JetBrains Mono", monospace; font-size: .85rem; padding: 0 .15rem; cursor: help; }
.tick[data-force="tie"] { color: var(--tie-b); } .tick[data-force="cliff"] { color: var(--cliff-b); } .tick[data-force="block"] { color: var(--block-b); } .tick[data-force="pure"] { color: var(--pure); }
.nec { font-family: "JetBrains Mono", monospace; font-size: .74rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; cursor: help; white-space: nowrap; }
.nec.must { color: var(--violet-b); } .nec.strong { color: var(--sky-b); } .nec.pref { color: var(--emerald-b); } .nec.close { color: var(--amber-b); } .nec.low { color: var(--crimson-b); }
.col { font-family: "JetBrains Mono", monospace; font-size: .8rem; color: var(--ink); text-align: right; font-variant-numeric: tabular-nums; }
.col .chip { font-size: .66rem; }
.value { font-family: "JetBrains Mono", monospace; font-weight: 700; text-align: right; font-variant-numeric: tabular-nums; }
.value .unit { font-size: .58rem; margin-left: .25rem; }
.neg { color: var(--crimson-b); }
.required { font-size: .6rem; font-weight: 700; color: var(--amber-b); border: 1px solid var(--amber); border-radius: 9px; padding: 1px 6px; letter-spacing: .05em; }
.fixture { font-family: "JetBrains Mono", monospace; font-size: .58rem; letter-spacing: .08em; color: var(--muted); border: 1px dashed var(--line-2); padding: 0 .35rem; border-radius: 3px; cursor: help; }
.detail { display: grid; grid-template-rows: 0fr; transition: grid-template-rows .22s ease; }
.row.open .detail { grid-template-rows: 1fr; }
.detail > div { overflow: hidden; min-height: 0; }
.detail .inner { margin-top: .6rem; padding-top: .6rem; border-top: 1px solid var(--line-2); font-size: .88rem; }
.detail p { margin: 0 0 .4rem; max-width: 72ch; }
.receipt { display: grid; grid-template-columns: 1.4fr 5.5rem 9rem 1fr 1fr; gap: .18rem .9rem; font-family: "JetBrains Mono", monospace; font-size: .72rem; margin-top: .5rem; }
.receipt .h { font-size: .58rem; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); border-bottom: 1px solid var(--line-2); padding-bottom: .15rem; }
.receipt .h.r { text-align: right; }
.receipt .q { color: var(--muted); } .receipt .val { text-align: right; color: var(--ink); font-weight: 700; } .receipt .u { color: var(--muted); }
.receipt .b.measured { color: var(--muted); } .receipt .b.imputed { color: var(--amber-b); } .receipt .b.unavailable { color: var(--muted); font-style: italic; }
.receipt .c { color: var(--muted); } .receipt .rule { grid-column: 1 / -1; border-top: 1px dashed var(--line-2); margin: .2rem 0; }
.fold { text-align: center; font-family: "JetBrains Mono", monospace; font-size: .68rem; letter-spacing: .06em; color: var(--muted); padding: .45rem; cursor: pointer; border: 1px dashed var(--line-2); border-radius: 8px; }
.fold:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }
"""
).replace("__GOLD07__", ds.token_rgba("gold", 0.07))


# ---------------------------------------------------------------------------------------
# S1 VERDICT-LED. C3's plate above C1's list: framed in line-2, no sheen, no gold; the
# conditional verdict sentence; 2-3 NAMED driving factors, not prose.
# ---------------------------------------------------------------------------------------
S1_CSS = r"""
.plate { border: 1px solid var(--line-2); border-radius: 12px; padding: .8rem 1.2rem .8rem; margin-bottom: .6rem; background: linear-gradient(180deg, var(--surface), var(--surface-2)); display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: .6rem 1.4rem; align-items: start; }
.plate .eyebrow { font-family: "JetBrains Mono", monospace; font-size: .64rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
.plate h2 { margin: .1rem 0 .3rem; font-size: 1.7rem; letter-spacing: .05em; display: flex; gap: .6rem; align-items: baseline; flex-wrap: wrap; }
.plate .verdict { font-size: 1rem; max-width: 66ch; margin: 0 0 .5rem; }
.factors { display: flex; gap: .5rem; flex-wrap: wrap; }
.factor { font-family: "JetBrains Mono", monospace; font-size: .74rem; padding: .3rem .6rem; border-radius: 6px; border: 1px solid var(--line-2); background: var(--surface-2); color: var(--ink); display: flex; gap: .45rem; align-items: baseline; }
.factor i { font-style: normal; font-size: .9rem; }
.factor[data-k="cliff"] i { color: var(--cliff-b); } .factor[data-k="block"] i { color: var(--block-b); } .factor[data-k="pure"] i { color: var(--pure); } .factor[data-k="tie"] i { color: var(--tie-b); }
.factor[data-k="required"], .factor[data-k="unpriced"] { border-color: var(--amber); }
.factor[data-k="required"] i, .factor[data-k="unpriced"] i { color: var(--amber-b); }
.plate .nums { text-align: right; font-family: "JetBrains Mono", monospace; font-size: .74rem; color: var(--muted); display: grid; gap: .2rem; }
.plate .nums b { color: var(--ink); font-size: 1.05rem; }
.plate .nums .big b { font-size: 2.2rem; line-height: 1; }
.plate .nums .neg { color: var(--crimson-b); }
"""
S1_BODY = r"""<div id="clock"></div><div id="plate"></div><div id="legend"></div><div class="board" id="board" role="listbox" aria-label="Draft candidates in the engine's order"></div>"""
S1_JS = SPINE_JS + r"""
function verdict(L) {
  const surv = num(L.survival) ? `${Math.round(L.survival * 100)}% survival to your next turn` : null;
  if (!num(L.tav)) return `<b>No price exists for him.</b> He leads for roster legality, not value — ${surv ? surv + "; " : "survival is not estimable; "}read the reasons before you commit.`;
  if (PAYLOAD.decisionRegime === "decisive") return `<b>Best-in-class, full stop.</b>${surv ? ` ${surv} — he is not walking back to this roster.` : " Survival isn't estimable — read the reasons before you commit."}`;
  if (PAYLOAD.decisionRegime === "exhausted") return `<b>Nothing left can be priced.</b> The ordering below carries no value basis; read the reasons before you commit.`;
  return `<b>Contested.</b>${surv ? ` ${surv}.` : " Survival isn't estimable."} The rows inside the noise band are a real group, not a clear lead.`;
}
function factors(L) {
  const order = ["required", "unpriced", "cliff", "block", "tie", "pure", "wait"];
  const fs = earned(L, 0, candidates).sort((a, b) => order.indexOf(a.k) - order.indexOf(b.k));
  const sv = survivalFactor(L);
  const out = [];
  for (const f of fs) { if (out.length < 3 && !out.some(o => o.k === f.k)) out.push(f); }
  if (out.length < 3 && sv) out.push(sv);
  return out.slice(0, 3);
}
function render() {
  document.getElementById("clock").innerHTML = clockBar();
  const L = candidates[0];
  const GL = { cliff: "◣", block: "⊘", pure: "◆", tie: "≈", required: "!", unpriced: "—", wait: "⏳", survival: "◔" };
  document.getElementById("plate").innerHTML = `<div class="plate"><div>
    <div class="eyebrow">the pick · ${necWord(L)}${num(L.pick_necessity) ? ` ${L.pick_necessity.toFixed(0)}/100` : ""}</div>
    <h2 class="display">${L.name} ${pillPos(L)} <span class="team">${L.team}</span>${fixtureTag(L)}</h2>
    <p class="verdict">${verdict(L)}</p>
    <div class="factors">${factors(L).map(f => `<span class="factor" data-k="${f.k}"><i>${GL[f.k] || "·"}</i>${f.label}</span>`).join("") || `<span class="factor">No driving factor measured beyond rank.</span>`}</div>
    </div><div class="nums"><span class="big">${num(L.tav) ? `<b${L.tav < 0 ? ' class="neg"' : ''}>${L.tav.toFixed(0)}</b>` : absent(WHY.tav)} ${U} acquisition</span><span>UV <b>${num(L.uv) ? L.uv.toFixed(0) : absent(WHY.uv)}</b> ${U}</span><span>proj <b>${num(L.proj) ? L.proj.toFixed(0) : absent(WHY.proj)}</b> season pts</span><span>survive <b>${num(L.survival) ? Math.round(L.survival * 100) + "%" : absent(WHY.survival)}</b></span></div></div>`;
  document.getElementById("legend").innerHTML = legend();
  document.getElementById("board").innerHTML = boardHtml(candidates, c => `<span class="col">${survivalCell(c)}</span><span class="col">${waitCell(c)}</span>`);
  wireBoard();
}
"""

# ---------------------------------------------------------------------------------------
# S2 LEDGER-LED. C1 rows under C2's sticky unit-headed column header. Two key details per
# row: SURVIVE and WAIT -- the only two row facts a drafter cannot derive from the value
# column, and the two that change the decision (will he be here; what deferring costs).
# ---------------------------------------------------------------------------------------
S2_CSS = r"""
.colhead { position: sticky; top: 0; z-index: 3; display: grid; grid-template-columns: 2rem minmax(0, 1fr) 4.4rem 8.6rem 4rem 9.6rem 6.2rem; gap: .7rem; padding: .45rem 1rem .35rem; margin: 0 0 .3rem;
  background: color-mix(in srgb, var(--bg) 94%, transparent); backdrop-filter: blur(6px); border: 1px solid var(--line-2); border-radius: 8px;
  font-family: "JetBrains Mono", monospace; font-size: .62rem; letter-spacing: .08em; text-transform: uppercase; color: var(--ink); }
.colhead .u { display: block; color: var(--muted); letter-spacing: .02em; text-transform: none; font-size: .6rem; }
.colhead .r { text-align: right; }
"""
S2_BODY = r"""<div id="clock"></div><div id="legend"></div><div class="colhead" id="colhead"></div><div class="board" id="board" role="listbox" aria-label="Draft candidates in the engine's order"></div>"""
S2_JS = SPINE_JS + r"""
function render() {
  document.getElementById("clock").innerHTML = clockBar();
  document.getElementById("legend").innerHTML = legend();
  document.getElementById("colhead").innerHTML = `<span>#</span><span>candidate</span><span>forces</span><span>necessity<span class="u">engine tier</span></span><span class="r">survive<span class="u">to your turn</span></span><span class="r">wait<span class="u">season pts/wk · floor basis</span></span><span class="r">acq<span class="u">${U}, signed</span></span>`;
  document.getElementById("board").innerHTML = boardHtml(candidates, c => `<span class="col">${survivalCell(c)}</span><span class="col">${waitCell(c)}</span>`);
  wireBoard();
}
"""

# ---------------------------------------------------------------------------------------
# THE CARD TRACK (H1-H3). The owner's original intent was cards; the critic scored the
# round-1 artifact. What survives of Hoard as MATERIAL is shared by all three: bevelled stone
# plates, a neutral facet glint, boxed force marks, depth and air. What does not survive, by
# constraint: size encodes nothing (every card in a tier is one size; tiers only descend, so
# size never contradicts rank); no position tint on a background; no gold on the leader or a
# tier. The three differ on ONE axis -- how they buy density under a pick clock -- and the
# density instrument (density.cjs) decides between them and the list spine.
# ---------------------------------------------------------------------------------------
MATERIAL_CSS = (r"""
body { background: radial-gradient(90% 50% at 50% -10%, #221c10, var(--bg) 60%); }
.row.card { border-radius: 12px; border: 1px solid var(--line-2); border-top-color: color-mix(in srgb, var(--gold) 18%, var(--line-2));
  background: linear-gradient(165deg, color-mix(in srgb, var(--surface) 92%, transparent), var(--surface-2) 75%);
  box-shadow: inset 0 1px 0 __WHITE05__, 0 10px 24px rgba(0,0,0,.38); overflow: hidden; }
.row.card::before { content: ""; position: absolute; inset: 0; pointer-events: none; background: linear-gradient(115deg, transparent 42%, __WHITE04__ 50%, transparent 58%); }
.row.card.open { box-shadow: inset 3px 0 0 var(--gold), inset 0 1px 0 __WHITE05__, 0 16px 36px rgba(0,0,0,.45); }
.row.card .name { font-family: "Cinzel", "Trajan Pro", Georgia, serif; letter-spacing: .03em; }
.row.card .tick { width: 1.45rem; height: 1.45rem; display: grid; place-items: center; border-radius: 5px; border: 1px solid; padding: 0; font-size: .82rem; }
.tick[data-force="tie"] { border-color: var(--tie); } .tick[data-force="cliff"] { border-color: var(--cliff); } .tick[data-force="block"] { border-color: var(--block); } .tick[data-force="pure"] { border-color: var(--tie); }
.clock-bar { position: relative; overflow: hidden; border-radius: 999px; padding: .7rem 1.4rem; box-shadow: 0 0 0 5px __GOLD06__, 0 16px 40px rgba(0,0,0,.45); }
.clock-bar::after { content: ""; position: absolute; inset: 0 auto 0 -40%; width: 40%; pointer-events: none; background: linear-gradient(105deg, transparent, __GOLDB10__ 50%, transparent); animation: sheen 12s ease-in-out infinite; }
@keyframes sheen { 0%, 60% { transform: translateX(0); } 100% { transform: translateX(350%); } }
.factor { font-family: "JetBrains Mono", monospace; font-size: .7rem; color: var(--ink); display: flex; gap: .4rem; align-items: baseline; }
.factor i { font-style: normal; }
.factor[data-k="cliff"] i { color: var(--cliff-b); } .factor[data-k="block"] i { color: var(--block-b); } .factor[data-k="pure"] i { color: var(--pure); } .factor[data-k="tie"] i { color: var(--tie-b); }
.factor[data-k="required"] i, .factor[data-k="unpriced"] i { color: var(--amber-b); }
.band, .fold { grid-column: 1 / -1; }
"""
).replace("__WHITE05__", "rgba(255,255,255,.05)").replace("__WHITE04__", "rgba(255,255,255,.04)") \
 .replace("__GOLD06__", ds.token_rgba("gold", 0.06)).replace("__GOLDB10__", ds.token_rgba("gold-b", 0.10))

CARD_JS = r"""
const GL = { cliff: "◣", block: "⊘", pure: "◆", tie: "≈", required: "!", unpriced: "—", wait: "⏳", survival: "◔" };
function topFactors(c, i, cands, n) {
  const order = ["required", "unpriced", "cliff", "block", "tie", "pure", "wait"];
  const fs = earned(c, i, cands).sort((a, b) => order.indexOf(a.k) - order.indexOf(b.k));
  const out = [];
  for (const f of fs) if (out.length < n && !out.some(o => o.k === f.k)) out.push(f);
  const sv = survivalFactor(c); if (out.length < n && sv) out.push(sv);
  return out.slice(0, n);
}
function factorsHtml(c, i, cands, n) { return topFactors(c, i, cands, n).map(f => `<span class="factor" data-k="${f.k}"><i>${GL[f.k] || "·"}</i>${f.label}</span>`).join(""); }
function valueHtml(c) { return num(c.tav) ? `<span data-field="tav"${c.tav < 0 ? ' class="neg"' : ''}>${c.tav.toFixed(0)}</span><span class="unit">${U}</span>` : `<span data-field="tav">${absent(WHY.tav)}</span>`; }
function detailHtml(c, i, cands) { const rs = earned(c, i, cands).filter(x => x.t); return `<div class="detail"><div><div class="inner">${rs.map(r => `<p>${r.t}</p>`).join("")}${receipt(c, i)}</div></div></div>`; }
function cardOpen(c) { return openId === c.id; }
function cardAttrs(c, i) { return `role="option" aria-expanded="${cardOpen(c)}" tabindex="${(focusedId ? focusedId === c.id : i === 0) ? 0 : -1}" data-id="${c.id}" data-index="${i}"`; }
function whoHtml(c) { return `<span class="who"><span class="name">${c.name}</span>${pillPos(c)}<span class="team">${c.team}</span>${c.fillsRequiredSlot ? '<span class="required" title="Ranked above higher-scoring candidates because your roster cannot otherwise still be filled legally.">FILLS REQUIRED SLOT</span>' : ""}${fixtureTag(c)}</span>`; }
function fieldHtml(cands, cardFn) {
  const T = tiers(cands);
  const tail = cands.filter((c, i) => T[i] === "tail");
  let last = null;
  return cands.map((c, i) => {
    const t = T[i];
    let band = "";
    if (t !== last) { band = `<div class="band ${t}">${bandLabel(t)}</div>`; last = t; }
    if (t === "tail" && !tailOpen) {
      if (tail[0].id === c.id) return band + `<div class="fold" role="button" tabindex="0" onclick="tailOpen=true;render()" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();tailOpen=true;render()}">${tail.length} low-urgency row${tail.length === 1 ? "" : "s"} folded — values ${valueRange(tail)} · show</div>`;
      return "";
    }
    return band + cardFn(c, i, t, cands);
  }).join("");
}
"""

# H1 DENSE CARDS -- how small can a card get and still be an object? Two columns, a stacked
# two-line composition (identity line over a facts line), the value as a numeral spanning
# both lines. An open card spans the full width.
H1_CSS = MATERIAL_CSS + r"""
.board { display: grid; grid-template-columns: 1fr 1fr; gap: .4rem; }
.row.card.dense { display: grid; grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: "ch cv" "cb cv" "cd cd"; column-gap: .8rem; row-gap: .15rem; padding: .5rem .8rem .5rem .9rem; align-items: center; }
.row.card.dense.open { grid-column: 1 / -1; }
.row.card.dense .ch { grid-area: ch; display: flex; align-items: baseline; gap: .5rem; min-width: 0; }
.row.card.dense .ch .name { font-size: 1rem; font-weight: 700; }
.row.card.dense .cb { grid-area: cb; display: flex; align-items: center; gap: .7rem; flex-wrap: wrap; }
.row.card.dense .cv { grid-area: cv; font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 1.5rem; text-align: right; font-variant-numeric: tabular-nums; align-self: center; }
.row.card.dense .cv .unit { font-size: .58rem; }
.row.card.dense .detail { grid-area: cd; }
.row.card.dense.context .ch .name { font-size: .92rem; font-weight: 600; }
.row.card.dense.context .cv { font-size: 1.2rem; }
.row.card.dense.tail .ch .name { font-size: .86rem; font-weight: 500; }
.row.card.dense.tail .cv { font-size: 1rem; }
.row.card.dense .ticks { margin-left: auto; }
"""
H1_BODY = S2_BODY.replace('<div class="colhead" id="colhead"></div>', "")
H1_JS = SPINE_JS + CARD_JS + r"""
function denseCard(c, i, t, cands) {
  return `<div class="row card dense ${t}${cardOpen(c) ? " open" : ""}" ${cardAttrs(c, i)}>
    <div class="ch"><span class="rank">${i + 1}</span>${whoHtml(c)}<span class="ticks">${ticks(c)}</span></div>
    <div class="cb">${necWord(c)}<span class="col">${survivalCell(c)}</span><span class="col">${waitCell(c)}</span></div>
    <div class="cv" title="Acquisition value in ${PAYLOAD.valueUnit} — signed, unbounded, not fantasy points">${valueHtml(c)}</div>
    ${detailHtml(c, i, cands)}
  </div>`;
}
function render() {
  document.getElementById("clock").innerHTML = clockBar();
  document.getElementById("legend").innerHTML = legend();
  document.getElementById("board").innerHTML = fieldHtml(candidates, denseCard);
  wireBoard();
}
"""

# H2 SPLIT FIELD -- large cards for the contiguous top tier (three across), the spine's rows
# for everything below. Cards where the decision is, rows where the reference is.
H2_CSS = MATERIAL_CSS + r"""
.board { display: grid; grid-template-columns: repeat(3, 1fr); gap: .5rem; }
.board .row:not(.card) { grid-column: 1 / -1; }
.row.card.big { display: grid; grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: "ch cv" "cn cv" "cf cf" "cb cb" "cd cd"; column-gap: .6rem; row-gap: .25rem; padding: .7rem .9rem; align-items: start; }
.row.card.big.open { grid-column: 1 / -1; }
.row.card.big .ch { grid-area: ch; display: flex; align-items: baseline; gap: .45rem; flex-wrap: wrap; min-width: 0; }
.row.card.big .ch .name { font-size: 1.05rem; font-weight: 700; }
.row.card.big .cn { grid-area: cn; display: flex; align-items: center; gap: .5rem; }
.row.card.big .cv { grid-area: cv; font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 1.9rem; line-height: 1; text-align: right; font-variant-numeric: tabular-nums; }
.row.card.big .cv .unit { display: block; font-size: .56rem; margin: .15rem 0 0; }
.row.card.big .cf { grid-area: cf; display: flex; flex-direction: column; gap: .15rem; min-height: 2.1rem; }
.row.card.big .cb { grid-area: cb; display: flex; gap: .6rem; align-items: center; border-top: 1px dashed var(--line-2); padding-top: .35rem; }
.row.card.big .detail { grid-area: cd; }
"""
H2_BODY = H1_BODY
H2_JS = SPINE_JS + CARD_JS + r"""
function bigCard(c, i, t, cands) {
  return `<div class="row card big ${t}${cardOpen(c) ? " open" : ""}" ${cardAttrs(c, i)}>
    <div class="ch"><span class="rank">${i + 1}</span>${whoHtml(c)}</div>
    <div class="cn">${necWord(c)}<span class="ticks">${ticks(c)}</span></div>
    <div class="cv" title="Acquisition value in ${PAYLOAD.valueUnit} — signed, unbounded, not fantasy points">${valueHtml(c)}</div>
    <div class="cf">${factorsHtml(c, i, cands, 2)}</div>
    <div class="cb"><span class="col">survive ${survivalCell(c)}</span><span class="col">${waitCell(c)}</span></div>
    ${detailHtml(c, i, cands)}
  </div>`;
}
function render() {
  document.getElementById("clock").innerHTML = clockBar();
  document.getElementById("legend").innerHTML = legend();
  document.getElementById("board").innerHTML = fieldHtml(candidates, (c, i, t, cands) => t === "decide" ? bigCard(c, i, t, cands) : rowHtml(c, i, t, cands, x => `<span class="col">${survivalCell(x)}</span><span class="col">${waitCell(x)}</span>`));
  wireBoard();
}
"""

# H3 STACKED DECK -- density by overlap, not by shrinking. Every card carries the whole row
# line at rest (identity, forces, necessity, survive, wait, value) in its top band; the cards
# overlap so only that band shows, like a hand of cards. Hover or focus LIFTS a card -- the
# next card slides down -- to reveal its two driving factors; Enter opens the receipt.
H3_CSS = MATERIAL_CSS + r"""
.board { display: flex; flex-direction: column; gap: 0; }
/* The hand: each card overlaps the one above by a fixed 1.1rem so the stack reads as stacked
   plates. The factor line is COLLAPSED at rest (not hidden under the next card, which clipped
   it) and unfolds on lift or open; the cards below move down in normal flow. */
.row.card.deck { margin-top: -1.1rem; padding: .45rem 1rem .6rem; transition: transform .18s ease, box-shadow .18s ease; }
.band + .row.card.deck, .row.card.deck:first-child, .fold + .row.card.deck { margin-top: 0; }
.row.card.deck .ch { display: grid; grid-template-columns: 2rem minmax(0, 1fr) 4.4rem 8.6rem 4rem 9.6rem 6.2rem; align-items: center; gap: .7rem; }
.row.card.deck .ch .name { font-size: 1.02rem; font-weight: 700; }
.row.card.deck .lift-body { display: flex; gap: 1rem; flex-wrap: wrap; max-height: 0; opacity: 0; overflow: hidden; margin-top: 0; transition: max-height .18s ease, opacity .15s ease, margin-top .18s ease; }
.row.card.deck.lift .lift-body, .row.card.deck.open .lift-body { max-height: 3rem; opacity: 1; margin-top: .4rem; }
/* A lifted card's shadow stays tight so it never washes the band of the card beneath it --
   a shadow that dims a neighbour's text is a fade over data. */
.row.card.deck.lift, .row.card.deck.open { transform: translateY(-2px); box-shadow: inset 0 1px 0 rgba(255,255,255,.05), 0 6px 14px rgba(0,0,0,.4); z-index: 5; }
.row.card.deck.open { box-shadow: inset 3px 0 0 var(--gold), inset 0 1px 0 rgba(255,255,255,.05), 0 6px 14px rgba(0,0,0,.4); }
.row.card.deck.context .ch .name { font-size: .95rem; font-weight: 600; }
.row.card.deck.tail .ch .name { font-size: .88rem; font-weight: 500; }
.band { margin-top: .3rem; }
"""
H3_BODY = H1_BODY
H3_JS = SPINE_JS + CARD_JS + r"""
function deckCard(c, i, t, cands) {
  return `<div class="row card deck ${t}${cardOpen(c) ? " open" : ""}" ${cardAttrs(c, i)}>
    <div class="ch"><span class="rank">${i + 1}</span>${whoHtml(c)}<span class="ticks">${ticks(c)}</span>${necWord(c)}<span class="col">${survivalCell(c)}</span><span class="col">${waitCell(c)}</span><span class="value" title="Acquisition value in ${PAYLOAD.valueUnit} — signed, unbounded, not fantasy points">${valueHtml(c)}</span></div>
    <div class="lift-body">${factorsHtml(c, i, cands, 2)}</div>
    ${detailHtml(c, i, cands)}
  </div>`;
}
function render() {
  document.getElementById("clock").innerHTML = clockBar();
  document.getElementById("legend").innerHTML = legend();
  document.getElementById("board").innerHTML = fieldHtml(candidates, deckCard);
  wireBoard();
  document.querySelectorAll(".row.card.deck").forEach(el => {
    el.addEventListener("mouseenter", () => el.classList.add("lift"));
    el.addEventListener("mouseleave", () => el.classList.remove("lift"));
    el.addEventListener("focus", () => el.classList.add("lift"));
    el.addEventListener("blur", () => el.classList.remove("lift"));
  });
}
"""

VARIANTS = [
    ("synthesis_s1_verdict", "S1 · Verdict-led", "C3's plate over C1's list: a conditional verdict sentence and 2–3 named driving factors, no prose, no gold",
     "The pick is stated as a claim whose honesty changes with the data (priced and decisive → 'best-in-class, full stop'; unpriced → 'no price exists for him — read the reasons'), followed by at most three named factors with their one number each. The list below is the spine: engine order, value-led rows, survival and wait as the two row details, the receipt on expand.",
     "The plate spends ~170px of the 1,400 on one candidate; with the fold that still fits. A drafter who disagrees with the leader must open a row to see a rival's factors. The plate never shows prose beyond one sentence — the receipt carries the rest.",
     SPINE_CSS + S1_CSS, S1_BODY, S1_JS),
    ("synthesis_s2_ledger", "S2 · Ledger-led", "C1 rows under C2's sticky unit-headed column header; two key details per row",
     "Every number on the page is read under a column whose header IS its unit (acq · UV pts, signed; survive · to your turn; wait · season pts/wk with the floor's basis). The two row details are survival and deferral cost because they are the only row facts a drafter cannot derive from the value column, and both change the decision. No plate: the leader is simply row one at full size.",
     "Nothing above the list says WHY the leader leads until a row is opened — the header is a unit ruler, not an argument. The sticky header costs 44px of every scroll position.",
     SPINE_CSS + S2_CSS, S2_BODY, S2_JS),
    ("synthesis_h1_dense", "H1 · Dense cards", "how small can a card get and still be an object: two columns, a stacked two-line composition, the value spanning both lines",
     "A card stays an object by composition, not by area: an identity line over a facts line, a numeral that spans both, a bevelled boundary and boxed force marks. Two across at 1,400px. Every card in a tier is the same size; tiers only descend. The measurement decides whether this is still a card or a row wearing a border.",
     "Two columns break the single reading column a list gives — rank runs left-to-right then down, and the rank numeral has to carry that. Each card holds the same two facts as a row (survive, wait), so the card form buys objectness, not information.",
     SPINE_CSS + H1_CSS, H1_BODY, H1_JS),
    ("synthesis_h2_split", "H2 · Split field", "large cards for the contiguous top tier, the spine's rows for everything below",
     "Cards where the decision is, rows where the reference is: the top tier gets three-across cards with a 1.9rem numeral and its two driving factors named on the face; context and tail are ordinary rows. The seam is the tier boundary the engine already draws, so the representation change means something.",
     "Two representations of one field: the eye has to re-learn the layout at the seam, and eight decide-tier cards at three across is three rows of cards before the first plain row. Rank inside the card grid reads row-major.",
     SPINE_CSS + H2_CSS, H2_BODY, H2_JS),
    ("synthesis_h3_deck", "H3 · Stacked deck", "density by overlap: every card carries the whole row line at rest; hover or focus lifts it to show its factors",
     "The swing. Cards overlap like a held hand, so at rest each shows only its top band — which carries everything the list row carries (identity, forces, necessity, survive, wait, value), so nothing is hidden that the list would show. Lifting a card (pointer or focus) slides the next one down and reveals two driving factors; Enter opens the receipt. Objects with depth at the list's density.",
     "The factors are one interaction away: a reader who never hovers or focuses sees a list of stacked plates. Under reduced motion the lift still happens, without easing. The overlap is fixed and small, so the density gain over the list is modest and the objectness rests on the shadows.",
     SPINE_CSS + H3_CSS, H3_BODY, H3_JS),
]
