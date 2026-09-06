"""Track B -- four directions for surfacing the engine quantities no screen reads today
(horizon_basis / horizon_floor as a three-state, depth_exposure, waiting_cost, coverage and
the unpriced count), on the recommendation panel and the row.

Each variant renders the same recommendation (the leader) and the same four contract rows.
The unit vocabulary is design_system.DISPLAY_CONTRACT, carried in the payload.
"""

from __future__ import annotations

from c_variants import TIER_JS

PANEL_JS = TIER_JS + r"""
const U = PAYLOAD.valueUnitShort, CT = PAYLOAD.contract;
function rec() { return candidates[0]; }
function alt() { return candidates[1]; }
function deferral(c) {
  // The three-state, as one sentence. Measured/estimated floors carry the number; the
  // unavailable state carries no number at all -- and says why.
  const h = horizon(c);
  if (c.waitNote) return { word: h ? h.word : "", cls: h ? h.cls : "", value: c.waitNote.label, text: c.waitNote.title };
  if (h) return { word: h.word, cls: h.cls, value: null, text: h.text };
  return { word: "not carried", cls: "unavailable", value: null, text: "This snapshot does not carry a draft-end floor for him." };
}
"""

# ---------------------------------------------------------------------------------------
# B1 CHIPS -- the incumbent's metric cards, finished: units in every label, a help tooltip,
# a Deferral card whose value is the three-state, and coverage as a chip in the header.
# ---------------------------------------------------------------------------------------
B1_CSS = r"""
.panel { border: 1px solid var(--line); border-radius: 10px; padding: 1rem 1.2rem; background: var(--surface-2); margin-bottom: 1rem; }
.panel h2 { margin: 0; font-size: 1.5rem; letter-spacing: .05em; display: flex; gap: .6rem; align-items: baseline; flex-wrap: wrap; }
.hdr { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; flex-wrap: wrap; margin-bottom: .8rem; }
.chips { display: flex; gap: .4rem; flex-wrap: wrap; }
.chip { font-family: "JetBrains Mono", monospace; font-size: .64rem; letter-spacing: .05em; text-transform: uppercase; padding: .15rem .5rem; border-radius: 4px; border: 1px solid var(--line-2); color: var(--muted); cursor: help; }
.chip.notice { color: var(--amber-b); border-color: var(--amber); }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(10.5rem, 1fr)); gap: .6rem; }
.card { border: 1px solid var(--line); border-radius: 8px; padding: .6rem .75rem; background: color-mix(in srgb, var(--surface) 85%, transparent); position: relative; }
.card .l { font-size: .68rem; color: var(--muted); letter-spacing: .02em; display: flex; justify-content: space-between; gap: .3rem; }
.card .l .q { cursor: help; color: var(--dim); border: 1px solid var(--line-2); border-radius: 50%; width: 1rem; height: 1rem; display: inline-grid; place-items: center; font-size: .6rem; flex-shrink: 0; }
.card .v { font-family: "JetBrains Mono", monospace; font-size: 1.55rem; font-weight: 700; margin-top: .15rem; font-variant-numeric: tabular-nums; }
.card .v.neg { color: var(--crimson-b); }
.card .v .unit { font-size: .6rem; font-weight: 500; }
.card .s { font-size: .68rem; color: var(--muted); margin-top: .2rem; }
.card.wide { grid-column: span 2; }
.card .sw { margin-left: .3rem; }
.alt { margin-top: .7rem; font-size: .9rem; }
.rows { margin-top: 1rem; }
.row { display: grid; grid-template-columns: 2rem 1fr auto auto auto; gap: .8rem; align-items: center; padding: .45rem .6rem; border-bottom: 1px solid var(--line); }
.row .n { font-weight: 600; display: flex; gap: .4rem; align-items: baseline; flex-wrap: wrap; }
.row .v { font-family: "JetBrains Mono", monospace; font-weight: 700; text-align: right; min-width: 5rem; }
.row .v.neg { color: var(--crimson-b); }
.fixture { font-family: "JetBrains Mono", monospace; font-size: .56rem; letter-spacing: .08em; color: var(--muted); border: 1px dashed var(--line-2); padding: 0 .3rem; border-radius: 3px; cursor: help; }
.h3 { font-family: "JetBrains Mono", monospace; font-size: .62rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin: 1rem 0 .3rem; }
"""
B1_BODY = r"""<div id="panel"></div>"""
B1_JS = PANEL_JS + r"""
function card(q, valueHtml, sub, wide) {
  const e = CT[q];
  return `<div class="card${wide ? " wide" : ""}"><div class="l"><span>${e.label}</span><span class="q" title="${esc(e.help)}">?</span></div><div class="v">${valueHtml}</div>${sub ? `<div class="s">${sub}</div>` : ""}</div>`;
}
function vcard(q, x, d) {
  const neg = num(x) && x < 0;
  return card(q, `<span class="${neg ? "neg" : ""}">${num(x) ? x.toFixed(d) : `<span class="absent" title="Not measured -- never computed for him; not zero.">${ABSENT}</span>`}</span>`);
}
function render() {
  const r = rec(), a = alt(), d = deferral(r), dp = depth(r);
  const cov = coverage(candidates);
  document.getElementById("panel").innerHTML = `<div class="panel">
    <div class="hdr"><h2 class="display">Recommendation: ${r.name} ${pillPos(r)}${fixtureTag(r)}</h2>
      <div class="chips"><span class="chip" title="${esc(PAYLOAD.valueUnit)}; signed and unbounded; not fantasy points">values in ${U}</span><span class="chip ${cov.startsWith("every") ? "" : "notice"}" title="Coverage of the candidate list: an unpriced candidate has no replacement level at his position and no acquisition value.">${cov}</span><span class="chip" title="Necessity, the engine's own 0-100 urgency score">${r.necessity} · ${fmt(r.pick_necessity, 0)}/100</span></div></div>
    <div class="cards">
      ${vcard("universal_value", r.uv, 0)}${vcard("projected_points", r.proj, 0)}${vcard("team_acquisition_value", r.tav, 0)}
      ${card("survival_probability", pct(r.survival))}
      ${card("positional_cliff", r.cliffTier ? r.cliffTier : `<span class="absent" title="No cliff could be measured for him.">${ABSENT}</span>`)}
      <div class="card"><div class="l"><span>${r.pos} ${CT.position_run.label}</span><span class="q" title="${esc(CT.position_run.help)}">?</span></div><div class="v">NONE</div><div class="s">a measured no-run, not a missing value</div></div>
    </div>
    <div class="h3">By your next turn</div>
    <div class="cards">${vcard("opportunity_cost", r.opportunity_cost, 1)}${vcard("expected_value_of_waiting", r.expected_value_of_waiting, 1)}${vcard("denial_value", r.denial_value, 1)}</div>
    <div class="h3">To the end of the draft — the quantities no card showed before</div>
    <div class="cards">
      <div class="card wide"><div class="l"><span>Cost of deferring ${r.pos} (season pts/week)</span><span class="q" title="${esc(d.text)}">?</span></div><div class="v">${d.value ? d.value : `<span class="absent" title="${esc(d.text)}">${ABSENT}</span>`}<span class="state-word ${d.cls} sw" title="${esc(d.text)}">floor ${d.word}</span></div><div class="s">${esc(d.text)}</div></div>
      <div class="card wide"><div class="l"><span>Depth insurance (${U})</span><span class="q" title="${esc(dp.text)}">?</span></div><div class="v">${num(r.depth_exposure) ? r.depth_exposure.toFixed(1) : `<span class="absent" title="Not measured">${ABSENT}</span>`}</div><div class="s">${dp.text}</div></div>
      <div class="card"><div class="l"><span>Priced against</span><span class="q" title="Which replacement anchor this price rests on. A position whose starter demand is exhausted is priced against its PRE-DRAFT level, a weaker claim than live demand.">?</span></div><div class="v" style="font-size:1rem">${r.replacementBasis ? (r.replacementBasis === "predraft_anchor" ? "pre-draft anchor" : "live starter demand") : `<span class="absent">${ABSENT}</span>`}</div></div>
      <div class="card"><div class="l"><span>Projection source · confidence</span></div><div class="v" style="font-size:1rem">${r.bpa_source ? r.bpa_source : `<span class="absent">${ABSENT}</span>`} · ${fmt(r.confidence, 0)}</div></div>
    </div>
    <div class="alt"><b>Best alternative:</b> ${a.name} — acquisition value ${num(a.tav) ? `${a.tav.toFixed(0)} ${U}` : `<span class="absent" title="Unpriced">unpriced</span>`} · survival ${pct(a.survival)}</div>
  </div>
  <div class="h3">The same chips on the row</div>
  <div class="rows">${candidates.slice(0, 6).concat(candidates.filter(c => c.source !== "real" || c.pos === "LB")).filter((c, i, arr) => arr.indexOf(c) === i).map((c, i) => { const dd = deferral(c); return `<div class="row"><span class="mono" style="color:var(--muted);font-size:.7rem">${candidates.indexOf(c) + 1}</span><span class="n">${c.name} ${pillPos(c)}${fixtureTag(c)}</span><span class="chips"><span class="chip ${dd.cls === "imputed" ? "notice" : ""}" title="${esc(dd.text)}">wait ${dd.value ? dd.value : ABSENT} · ${dd.word}</span>${num(c.depth_exposure) && c.depth_exposure > 0 ? `<span class="chip">depth +${c.depth_exposure.toFixed(1)}</span>` : ""}${c.replacementBasis === "predraft_anchor" ? `<span class="chip notice" title="Priced against the pre-draft anchor: starter demand at his position is exhausted.">pre-draft anchor</span>` : ""}</span><span class="necessity-pill ${c.necClass}" style="font-size:.58rem">${c.necessity}</span><span class="v ${num(c.tav) && c.tav < 0 ? "neg" : ""}">${fmt(c.tav, 0, U)}</span></div>`; }).join("")}</div>`;
}
"""

# ---------------------------------------------------------------------------------------
# B2 SENTENCES -- no cards. Every quantity is a sentence, absence is a clause, the three
# states are words in running text. The Caller's voice, with the numbers inside it.
# ---------------------------------------------------------------------------------------
B2_CSS = r"""
.prose { border: 1px solid var(--line); border-radius: 12px; padding: 1.3rem 1.6rem; background: linear-gradient(180deg, var(--surface), var(--surface-2)); max-width: 78ch; font-size: 1.02rem; line-height: 1.65; }
.prose h2 { margin: 0 0 .6rem; font-size: 1.6rem; letter-spacing: .05em; }
.prose p { margin: 0 0 .7rem; }
.prose .n { font-family: "JetBrains Mono", monospace; font-weight: 700; color: var(--ink); }
.prose .n.neg { color: var(--crimson-b); }
.prose .u { font-family: "JetBrains Mono", monospace; font-size: .74em; color: var(--muted); }
.prose .lead { font-size: 1.12rem; }
.prose .nb { color: var(--muted); font-size: .92rem; border-left: 2px solid var(--line-2); padding-left: .8rem; }
.h3 { font-family: "JetBrains Mono", monospace; font-size: .62rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin: 1.2rem 0 .4rem; }
.rows .row { max-width: 78ch; padding: .5rem 0; border-bottom: 1px solid var(--line); font-size: .92rem; }
.rows .row b.nm { font-size: 1rem; }
.fixture { font-family: "JetBrains Mono", monospace; font-size: .56rem; letter-spacing: .08em; color: var(--muted); border: 1px dashed var(--line-2); padding: 0 .3rem; border-radius: 3px; cursor: help; }
"""
B2_BODY = r"""<div id="prose"></div><div class="h3">Each candidate as one sentence</div><div class="rows" id="rows"></div>"""
B2_JS = PANEL_JS + r"""
function n(x, d, unit) { return num(x) ? `<span class="n${x < 0 ? " neg" : ""}">${x.toFixed(d)}</span>${unit ? `${unit === "%" ? "" : " "}<span class="u">${unit}</span>` : ""}` : null; }
function sentence(c, leader) {
  const parts = [];
  const acq = n(c.tav, 0, U), uv = n(c.uv, 0, U), proj = n(c.proj, 0, "season pts");
  parts.push(acq ? `${c.name} is worth ${acq} to this roster` : `${c.name} carries <b>no acquisition value</b> — his position has no replacement level left to price against (an absence, not a zero)`);
  if (acq && uv) parts.push(`of which ${uv} is universal value and ${n(c.tav - c.uv, 0, U)} is roster context`);
  if (proj) parts.push(`on a projection of ${proj}`);
  const s = num(c.survival) ? `he has a ${n(c.survival * 100, 0, "%")} chance of still being here at your next turn` : `his survival to your next turn is not estimable`;
  const d = deferral(c);
  const dtext = d.value ? `deferring ${c.pos} to the end of the draft costs ${d.value.replace(" pts/wk", "")} <span class="u">season pts/wk</span> and that floor is <b>${d.word}</b>` : `the cost of deferring ${c.pos} to the end of the draft is <b>${d.word}</b>`;
  const dp = depth(c);
  const dptext = dp.val === null ? `depth insurance was not measured` : dp.val > 0 ? `holding him insures ${n(dp.val, 1, U)} of lineup depth` : `depth insurance reads 0.0 <span class="u">${U}</span> (measured or not measured — the snapshot cannot say)`;
  const den = num(c.denial_value) ? (c.denial_value === 0 ? `no rival was positioned to gain from him (denial value a measured <span class="n">0.0</span>)` : `taking him denies a rival ${n(c.denial_value, 1, U)}`) : `denial value was not measured`;
  return `${parts.join(", ")}. ${s[0].toUpperCase() + s.slice(1)}; ${dtext}; ${dptext}; ${den}.${c.fillsRequiredSlot ? " <b>He is ranked above higher-scoring candidates because your roster cannot otherwise still be filled legally.</b>" : ""}`;
}
function render() {
  const r = rec(), a = alt();
  document.getElementById("prose").innerHTML = `<div class="prose"><h2 class="display">${r.name} ${pillPos(r)}${fixtureTag(r)}</h2>
    <p class="lead">${sentence(r, true)}</p>
    ${reasons(r, true).map(x => `<p>${x}</p>`).join("")}
    <p class="nb">${coverage(candidates)[0].toUpperCase() + coverage(candidates).slice(1)}. Values are ${PAYLOAD.valueUnit} (${U}), signed and unbounded — not fantasy points; deferral costs are season-projection points per week. Best alternative: ${a.name}, ${num(a.tav) ? `${a.tav.toFixed(0)} ${U}` : "unpriced"}, survival ${pct(a.survival)}.</p></div>`;
  document.getElementById("rows").innerHTML = candidates.map((c, i) => `<div class="row"><span class="mono" style="color:var(--muted);font-size:.7rem">${i + 1} </span><b class="nm">${c.name}</b> ${pillPos(c)}${fixtureTag(c)} — ${sentence(c, i === 0)}</div>`).join("");
}
"""

# ---------------------------------------------------------------------------------------
# B3 SIGNED AXIS -- the UV-scale quantities as points on a signed number line with a marked
# zero and a negative direction (G3), season points on their own axis with the draft-end
# floor as a bracket, and absence as a hatched gap where the point would sit.
# ---------------------------------------------------------------------------------------
B3_CSS = r"""
.fig { border: 1px solid var(--line); border-radius: 10px; padding: 1rem 1.2rem; background: var(--surface-2); margin-bottom: .8rem; }
.fig h2 { margin: 0 0 .2rem; font-size: 1.4rem; letter-spacing: .05em; }
.fig .cap { font-family: "JetBrains Mono", monospace; font-size: .64rem; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); margin-bottom: .5rem; }
.axis { position: relative; height: 3.2rem; margin: .6rem 0 .4rem; }
.axis .line { position: absolute; left: 0; right: 0; top: 1.5rem; height: 1px; background: var(--line-2); }
.axis .zero { position: absolute; top: .9rem; width: 2px; height: 1.3rem; background: var(--ink); }
.axis .zero::after { content: "0"; position: absolute; top: 1.4rem; left: -.2rem; font-family: "JetBrains Mono", monospace; font-size: .62rem; color: var(--muted); }
.axis .t { position: absolute; top: 1.2rem; width: 1px; height: .6rem; background: var(--line-2); }
.axis .t::after { content: attr(data-v); position: absolute; top: .8rem; left: -.6rem; font-family: "JetBrains Mono", monospace; font-size: .58rem; color: var(--muted); }
.axis .neg { position: absolute; left: 0; top: .2rem; font-family: "JetBrains Mono", monospace; font-size: .58rem; color: var(--crimson-b); letter-spacing: .06em; }
.axis .pos { position: absolute; right: 0; top: .2rem; font-family: "JetBrains Mono", monospace; font-size: .58rem; color: var(--muted); letter-spacing: .06em; }
.pt { position: absolute; top: 1.05rem; width: .9rem; height: .9rem; border-radius: 50%; transform: translateX(-50%); border: 2px solid var(--sky-b); background: var(--bg); cursor: help; }
.pt.uv { border-color: var(--muted); }
.pt.tav { border-color: var(--sky-b); background: var(--sky-b); }
.pt.den { border-color: var(--block-b); }
.pt.oc { border-color: var(--violet-b); }
.pt .lb { position: absolute; top: -1.15rem; left: 50%; transform: translateX(-50%); font-family: "JetBrains Mono", monospace; font-size: .6rem; color: var(--ink); white-space: nowrap; }
.gap { position: absolute; top: .95rem; height: 1.1rem; width: 3.2rem; transform: translateX(-50%); border-radius: 3px; cursor: help;
  background: repeating-linear-gradient(135deg, transparent 0 3px, color-mix(in srgb, var(--line-2) 80%, transparent) 3px 4px); border: 1px dashed var(--line-2); }
.gap .lb { position: absolute; top: -1.15rem; left: 50%; transform: translateX(-50%); font-family: "JetBrains Mono", monospace; font-size: .6rem; color: var(--muted); white-space: nowrap; }
.legend { display: flex; gap: 1rem; flex-wrap: wrap; font-family: "JetBrains Mono", monospace; font-size: .64rem; color: var(--muted); }
.legend i { display: inline-block; width: .7rem; height: .7rem; border-radius: 50%; border: 2px solid; vertical-align: middle; margin-right: .3rem; }
.bracket { position: absolute; top: .7rem; height: 1.6rem; border-left: 2px solid var(--amber-b); }
.bracket.measured { border-color: var(--emerald-b); }
.bracket.unavailable { border: none; }
.bracket .lb { position: absolute; top: -.85rem; left: .3rem; font-family: "JetBrains Mono", monospace; font-size: .58rem; color: var(--muted); white-space: nowrap; }
.rows .row { display: grid; grid-template-columns: 2rem 11rem 1fr; gap: .8rem; align-items: center; padding: .3rem .4rem; border-bottom: 1px solid var(--line); }
.rows .row .n { font-weight: 600; display: flex; gap: .4rem; align-items: baseline; flex-wrap: wrap; }
.rows .axis { height: 2rem; margin: 0; }
.rows .axis .line { top: .95rem; } .rows .axis .zero { top: .4rem; height: 1.1rem; } .rows .axis .zero::after { top: 1.1rem; } .rows .pt { top: .5rem; } .rows .gap { top: .4rem; }
.h3 { font-family: "JetBrains Mono", monospace; font-size: .62rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin: 1rem 0 .3rem; }
.fixture { font-family: "JetBrains Mono", monospace; font-size: .56rem; letter-spacing: .08em; color: var(--muted); border: 1px dashed var(--line-2); padding: 0 .3rem; border-radius: 3px; cursor: help; }
"""
B3_BODY = r"""<div id="fig"></div><div class="h3">Every candidate's acquisition value on the same signed axis</div><div class="rows" id="rows"></div>"""
B3_JS = PANEL_JS + r"""
// Domain from the DATA, symmetric about zero so the negative direction is always drawn:
// the axis is a ruler for signed, unbounded values, never a 0-100 band.
function domain(vals) { const m = Math.max(10, ...vals.filter(num).map(Math.abs)); return [-m * 0.25, m * 1.1]; }
function x(v, dom) { return `${(v - dom[0]) / (dom[1] - dom[0]) * 100}%`; }
function point(v, cls, label, dom, title) {
  return num(v) ? `<span class="pt ${cls}" style="left:${x(v, dom)}" title="${esc(title)}: ${v.toFixed(1)} ${U}"><span class="lb">${label} ${v.toFixed(0)}</span></span>`
                : `<span class="gap" style="left:${x(0, dom)}" title="${esc(title)}: not measured. There is no point to place; this hatched slot is the absence."><span class="lb">${label} ${ABSENT}</span></span>`;
}
function valueAxis(c, dom, labels) {
  const ticks = []; for (let v = Math.ceil(dom[0] / 25) * 25; v <= dom[1]; v += 25) if (v !== 0) ticks.push(`<span class="t" style="left:${x(v, dom)}" data-v="${v}"></span>`);
  return `<div class="axis"><span class="neg">← negative</span><span class="pos">${U} →</span><div class="line"></div>${ticks.join("")}<span class="zero" style="left:${x(0, dom)}"></span>
    ${labels ? point(c.uv, "uv", "UV", dom, CT.universal_value.label) + point(c.tav, "tav", "ACQ", dom, CT.team_acquisition_value.label) + point(c.denial_value, "den", "DENIAL", dom, CT.denial_value.label) + point(c.opportunity_cost, "oc", "OPP", dom, CT.opportunity_cost.label) : point(c.tav, "tav", "", dom, CT.team_acquisition_value.label)}</div>`;
}
function seasonAxis(c) {
  const dom = [0, Math.max(50, ...[c.proj, c.horizon_floor].filter(num)) * 1.15];
  const h = horizon(c);
  const floor = num(c.horizon_floor) ? `<span class="bracket ${h ? h.cls : ""}" style="left:${x(c.horizon_floor, dom)}" title="${h ? esc(h.text) : ""}"><span class="lb">draft-end floor ${c.horizon_floor.toFixed(0)} · ${h ? h.word : ""}</span></span>`
        : `<span class="gap" style="left:${x(dom[1] * .5, dom)};width:7rem" title="${h ? esc(h.text) : "Not carried"}"><span class="lb">floor ${ABSENT} · ${h ? h.word : "not carried"}</span></span>`;
  const proj = num(c.proj) ? `<span class="pt tav" style="left:${x(c.proj, dom)}" title="${esc(CT.projected_points.help)}"><span class="lb">PROJ ${c.proj.toFixed(0)}</span></span>` : `<span class="gap" style="left:${x(dom[1] * .25, dom)}" title="Projected points not carried for him."><span class="lb">PROJ ${ABSENT}</span></span>`;
  return `<div class="axis"><span class="pos">season pts →</span><div class="line"></div><span class="zero" style="left:0"></span>${floor}${proj}</div>`;
}
function render() {
  const r = rec(), dom = domain([r.uv, r.tav, r.denial_value, r.opportunity_cost, r.expected_value_of_waiting]);
  const d = deferral(r), dp = depth(r);
  document.getElementById("fig").innerHTML = `<div class="fig"><h2 class="display">${r.name} ${pillPos(r)}${fixtureTag(r)}</h2>
    <div class="cap">value scale · ${PAYLOAD.valueUnit} · signed, unbounded, zero marked · ${coverage(candidates)}</div>
    ${valueAxis(r, dom, true)}
    <div class="legend"><span><i style="border-color:var(--muted)"></i>universal value</span><span><i style="border-color:var(--sky-b);background:var(--sky-b)"></i>your acquisition value</span><span><i style="border-color:var(--block-b)"></i>denial value</span><span><i style="border-color:var(--violet-b)"></i>opportunity cost by your next turn</span><span>survival ${pct(r.survival)} · necessity ${fmt(r.pick_necessity, 0)}/100</span></div>
    <div class="cap" style="margin-top:1rem">season scale · projected points and the draft-end floor · ${d.value ? `deferring ${r.pos} costs ${d.value}` : `deferral cost ${ABSENT}`} · floor <span class="state-word ${d.cls}" title="${esc(d.text)}">${d.word}</span></div>
    ${seasonAxis(r)}
    <div class="cap">${esc(dp.text)}</div></div>`;
  const all = domain(candidates.map(c => c.tav));
  document.getElementById("rows").innerHTML = candidates.map((c, i) => `<div class="row"><span class="mono" style="color:var(--muted);font-size:.7rem">${i + 1}</span><span class="n">${c.name} ${pillPos(c)}${fixtureTag(c)}</span>${valueAxis(c, all, false)}</div>`).join("");
}
"""

# ---------------------------------------------------------------------------------------
# B4 RECEIPT -- numbers stay small on the row; a provenance layer slides up from the bottom
# for the selected candidate: every quantity as value · unit · basis · coverage · source.
# ---------------------------------------------------------------------------------------
B4_CSS = r"""
.list { border: 1px solid var(--line); border-radius: 10px; overflow: hidden; background: var(--surface-2); margin-bottom: 14rem; }
.row { display: grid; grid-template-columns: 2rem 1fr 6rem 5rem 5rem 2rem; gap: .8rem; align-items: center; padding: .55rem .9rem; border-bottom: 1px solid var(--line); cursor: pointer; }
.row:hover { background: color-mix(in srgb, var(--surface) 70%, transparent); }
.row.sel { box-shadow: inset 3px 0 0 var(--gold); background: color-mix(in srgb, var(--gold) 8%, var(--surface)); }
.row .n { font-weight: 600; display: flex; gap: .4rem; align-items: baseline; flex-wrap: wrap; }
.row .v { font-family: "JetBrains Mono", monospace; font-weight: 700; text-align: right; }
.row .v.neg { color: var(--crimson-b); }
.row .s { font-family: "JetBrains Mono", monospace; font-size: .62rem; text-align: right; color: var(--muted); }
.row .prov { text-align: right; color: var(--dim); font-size: .7rem; }
.row .prov.flag { color: var(--amber-b); }
.sheet { position: fixed; left: 0; right: 0; bottom: 0; z-index: 5; transform: translateY(100%); transition: transform .28s ease; max-height: 62vh; overflow: auto;
  background: linear-gradient(90deg, var(--emerald), var(--gold), var(--violet), var(--crimson)) top / 100% 2px no-repeat, color-mix(in srgb, var(--bg) 96%, transparent); backdrop-filter: blur(10px);
  border-top: 1px solid var(--line-2); box-shadow: 0 -10px 40px rgba(0,0,0,.5); }
.sheet.open { transform: none; }
.sheet .in { max-width: 1100px; margin: 0 auto; padding: 1rem 1.4rem 1.4rem; }
.sheet h3 { margin: 0; font-size: 1.3rem; letter-spacing: .05em; display: flex; justify-content: space-between; align-items: baseline; }
.sheet h3 button { font-family: "JetBrains Mono", monospace; font-size: .64rem; background: transparent; color: var(--muted); border: 1px solid var(--line-2); border-radius: 6px; padding: .2rem .6rem; cursor: pointer; }
.receipt { display: grid; grid-template-columns: 1.4fr 6rem 8rem 1fr 1fr; gap: .25rem 1rem; font-family: "JetBrains Mono", monospace; font-size: .74rem; margin-top: .7rem; }
.receipt .h { font-size: .58rem; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); border-bottom: 1px solid var(--line-2); padding-bottom: .2rem; }
.receipt .q { color: var(--muted); }
.receipt .v { text-align: right; color: var(--ink); font-weight: 700; }
.receipt .v.neg { color: var(--crimson-b); }
.receipt .u { color: var(--muted); }
.receipt .b { color: var(--muted); }
.receipt .b.imputed { color: var(--amber-b); }
.receipt .b.unavailable { color: var(--muted); font-style: italic; }
.receipt .c { color: var(--muted); }
.receipt .rule { grid-column: 1 / -1; border-top: 1px dashed var(--line-2); margin: .3rem 0; }
.top { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: .5rem; font-family: "JetBrains Mono", monospace; font-size: .7rem; color: var(--muted); }
.fixture { font-family: "JetBrains Mono", monospace; font-size: .56rem; letter-spacing: .08em; color: var(--muted); border: 1px dashed var(--line-2); padding: 0 .3rem; border-radius: 3px; cursor: help; }
.hd { display: grid; grid-template-columns: 2rem 1fr 6rem 5rem 5rem 2rem; gap: .8rem; padding: .3rem .9rem; font-family: "JetBrains Mono", monospace; font-size: .56rem; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); border-bottom: 1px solid var(--line-2); }
.hd .r { text-align: right; }
"""
B4_BODY = r"""<div class="top"><span id="clock"></span><span id="coverage"></span></div><div class="list" id="list"></div><div class="sheet" id="sheet"><div class="in" id="sheet-in"></div></div>"""
B4_JS = PANEL_JS + r"""
let sel = null;
function line(q, v, d, unit, basis, cov) {
  const val = num(v) ? `<span class="v${v < 0 ? " neg" : ""}">${v.toFixed(d)}</span>` : `<span class="v"><span class="absent" title="Not measured">${ABSENT}</span></span>`;
  return `<span class="q">${q}</span>${val}<span class="u">${unit}</span><span class="b ${basis.cls || ""}">${basis.word}</span><span class="c">${cov}</span>`;
}
function render() {
  document.getElementById("clock").textContent = `${PAYLOAD.pickHeader} · ${PAYLOAD.league}`;
  document.getElementById("coverage").textContent = coverage(candidates);
  document.getElementById("list").innerHTML = `<div class="hd"><span>#</span><span>candidate</span><span class="r">acq · ${U}</span><span class="r">survive</span><span class="r">wait · pts/wk</span><span></span></div>` + candidates.map((c, i) => {
    const d = deferral(c);
    const flags = [c.replacementBasis === "predraft_anchor" ? "anchor" : "", d.cls === "imputed" ? "est." : "", d.cls === "unavailable" ? "no floor" : "", !num(c.tav) ? "unpriced" : ""].filter(Boolean);
    return `<div class="row${sel === c.id ? " sel" : ""}" onclick="sel='${c.id}';render()"><span class="mono" style="color:var(--muted);font-size:.7rem">${i + 1}</span><span class="n">${c.name} ${pillPos(c)}${fixtureTag(c)}</span><span class="v ${num(c.tav) && c.tav < 0 ? "neg" : ""}">${fmt(c.tav, 0)}</span><span class="s">${pct(c.survival)}</span><span class="s" title="${esc(d.text)}">${d.value ? d.value.replace(" pts/wk", "") : `<span class="absent">${ABSENT}</span>`}</span><span class="prov ${flags.length ? "flag" : ""}" title="${flags.length ? "provenance flags: " + flags.join(", ") : "no provenance flags"}">${flags.length ? "◌" : "○"}</span></div>`;
  }).join("");
  const c = candidates.find(x => x.id === sel);
  document.getElementById("sheet").classList.toggle("open", !!c);
  if (!c) return;
  const h = horizon(c) || { word: "not carried", cls: "unavailable" }, d = deferral(c), dp = depth(c);
  const anchor = c.replacementBasis ? { word: c.replacementBasis === "predraft_anchor" ? "pre-draft anchor" : "live starter demand", cls: c.replacementBasis === "predraft_anchor" ? "imputed" : "" } : { word: "not carried", cls: "unavailable" };
  const src = c.bpa_source ? `${c.bpa_source} · conf ${fmt(c.confidence, 0)}` : "source not carried";
  const M = { word: "measured", cls: "" };
  document.getElementById("sheet-in").innerHTML = `<h3 class="display">${c.name} ${pillPos(c)} <span style="font-size:.8rem;letter-spacing:0;color:var(--muted)">rank ${candidates.indexOf(c) + 1} · ${c.necessity} ${fmt(c.pick_necessity, 0)}/100</span><button onclick="sel=null;render()">close</button></h3>
    <div class="receipt">
      <span class="h">quantity</span><span class="h" style="text-align:right">value</span><span class="h">unit</span><span class="h">basis</span><span class="h">coverage / source</span>
      ${line(CT.team_acquisition_value.label.split(" (")[0], c.tav, 1, PAYLOAD.valueUnit, anchor, src)}
      ${line("Universal value", c.uv, 1, PAYLOAD.valueUnit, anchor, src)}
      ${line("Roster need term", c.needBonus, 1, PAYLOAD.valueUnit, M, "this roster's unfilled slots")}
      ${line("Lineup flexibility term", c.eligBonus, 1, PAYLOAD.valueUnit, M, "multi-position eligibility")}
      ${line("Depth insurance term", c.depth_exposure, 1, PAYLOAD.valueUnit, num(c.depth_exposure) ? { word: c.depth_exposure > 0 ? "measured" : "0.0 — basis not carried", cls: c.depth_exposure > 0 ? "" : "imputed" } : { word: "not measured", cls: "unavailable" }, "one lineup re-solve per starter")}
      <span class="rule"></span>
      ${line("Projected points", c.proj, 0, "season fantasy points", M, src)}
      ${line("Draft-end floor for " + c.pos, c.horizon_floor, 0, "season fantasy points", h, num(c.horizon_sensitivity) ? `± ${c.horizon_sensitivity.toFixed(0)} across a realistic positional run` : "no error bar")}
      ${line("Cost of deferring " + c.pos, num(c.waiting_cost) ? c.waiting_cost / PAYLOAD.weeksFactor : null, 2, "season pts per week", h, "to the end of the draft")}
      <span class="rule"></span>
      ${line("Survival to your next turn", num(c.survival) ? c.survival * 100 : null, 0, "percent", num(c.intervening) ? { word: `${c.intervening} picks`, cls: "" } : { word: "no pick context", cls: "unavailable" }, "each intervening roster's own board")}
      ${line("Opportunity cost of waiting", c.opportunity_cost, 1, PAYLOAD.valueUnit, M, "acq value × (1 − survival)")}
      ${line("Expected value if you wait", c.expected_value_of_waiting, 1, PAYLOAD.valueUnit, M, "universal value × survival")}
      ${line("Denial value", c.denial_value, 1, PAYLOAD.valueUnit, M, num(c.denial_value) && c.denial_value === 0 ? "a measured 0: no rival positioned to gain" : "best rival's gain × their take probability")}
      ${line("Cost of skipping " + c.pos + " by your next turn", c.positional_forfeit, 1, PAYLOAD.valueUnit, M, "next-turn horizon")}
    </div>
    <p style="font-size:.86rem;color:var(--muted);margin:.7rem 0 0">${esc(d.text)} ${esc(dp.text)}</p>`;
}
"""

VARIANTS = [
    ("quantities_v1_chips", "B1 · Chips", "the incumbent's metric cards finished, plus a Deferral card and coverage chips",
     "Every card label carries its unit and a ? tooltip; the three quantities no card ever showed get their own row -- deferral cost with the floor's state as a word, depth insurance with its caveat, the replacement anchor -- and coverage is a chip in the header that turns amber when a candidate is unpriced. The same chips repeat on the row so the panel and the board agree.",
     "It is the busiest of the four: fourteen tiles. The three-state reads as a chip beside a number, which a hurried eye can skip; the caveat text under each new card is what carries the honesty and it is small.",
     B1_CSS, B1_BODY, B1_JS),
    ("quantities_v2_sentences", "B2 · Sentences", "no cards: every quantity is a clause, every absence is a clause, every state is a word",
     "The Caller's voice with the numbers inside it. Absence cannot be mistaken for a value because it is a sentence ('carries no acquisition value -- an absence, not a zero'); a measured zero is named as measured; the floor's state is a bold word in running text. Units sit beside every number as a small mono suffix.",
     "Slow to scan and impossible to compare across candidates at a glance. Sentences are long for the unpriced row by construction. It needs the board beside it; it cannot be the board.",
     B2_CSS, B2_BODY, B2_JS),
    ("quantities_v3_axis", "B3 · Signed axis", "the value quantities as points on a signed number line with a marked zero; season points on their own axis with the floor as a bracket",
     "The one geometric treatment the scale permits: a ruler, symmetric about a marked zero, its domain taken from the data, never a 0-100 band. Universal value, acquisition value, denial and opportunity cost sit on it as labelled points so the roster-context lift is a visible distance. Projected points and the draft-end floor share a second axis, the floor bracket coloured by its basis. An absence is a hatched slot where the point would be; a negative value is simply left of zero.",
     "Two axes per candidate cost height; the per-row version shows acquisition value only. Points close together overlap their labels. It shows relationships better than any other direction and raw magnitudes worse than a numeral.",
     B3_CSS, B3_BODY, B3_JS),
    ("quantities_v4_receipt", "B4 · Receipt", "small numbers on the row; a provenance sheet slides up with value · unit · basis · coverage for every quantity",
     "The row shows three numbers and a provenance ring (◌ when any quantity rests on an estimate, an anchor, a missing floor or no price). Selecting a row slides a sheet up from the bottom listing every quantity with its unit, its basis word and its coverage note -- the only direction where depth_exposure's 'basis not carried' gap and the floor's ± error bar are visible.",
     "Everything that matters most is one click away. The sheet is a table of fourteen lines, dense and mono; a drafter on a clock will read the row and skip the receipt. The provenance ring is a single glyph carrying four different flags.",
     B4_CSS, B4_BODY, B4_JS),
]
