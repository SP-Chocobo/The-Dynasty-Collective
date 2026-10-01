"""Track C -- five directions for the Draft Room page. Each answers "what does hierarchy mean
here" differently; none fades data to make it. The relevance tier every variant reads is the
engine's OWN decision vocabulary (necessity_label), never a threshold invented here:

    decide  -- MUST TAKE / STRONG ACTION / PREFERRED, and any near-tie partner of the leader
    context -- CLOSE CALL
    tail    -- LOW URGENCY / DOESN'T MATTER MUCH

The leader is always `decide`, priced or not: an unpriced leader is still the row a person
must read first, so it renders at full size with the absent mark, never demoted for lacking
a number.
"""

from __future__ import annotations

TIER_JS = r"""
function tier(c, i) {
  if (i === 0) return "decide";
  if (["MUST TAKE", "STRONG ACTION", "PREFERRED"].includes(c.necessity) || c.forces.includes("tie")) return "decide";
  if (c.necessity === "CLOSE CALL") return "context";
  return "tail";
}
function pillPos(c) { return `<span class="pill pill-${c.pos}">${c.pos}</span>`; }
function ticks(c) {
  return c.forces.map(f => `<span class="tick mono" data-force="${f}" title="${forceTitle(f)}">${GLYPH[f]}</span>`).join("");
}
// denial_team arrives as Sleeper's roster id; a person reads "Roster 6", not "6".
function rival(c) { return c.denialTeam ? (/^\d+$/.test(String(c.denialTeam)) ? `Roster ${c.denialTeam}` : c.denialTeam) : null; }
function fixtureTag(c) {
  return c.source === "real" ? "" : `<span class="fixture" title="${esc(c.source)}">FIXTURE</span>`;
}
function reasons(c, leader) {
  const s = [];
  const h = horizon(c);
  if (c.forces.includes("cliff")) s.push(`${num(c.forfeit) ? `Waiting costs about <b>${c.forfeit.toFixed(1)} ${PAYLOAD.valueUnitShort}</b> by your next turn` : `Waiting has a cost this board could not measure`} — ${c.cliffTier ? `a ${c.cliffTier} positional cliff` : `a positional cliff`}${num(c.cliffGap) ? ` (${c.cliffGap.toFixed(1)} ${PAYLOAD.valueUnitShort} of drop-off to the next best ${c.pos}${num(c.cliffTypical) ? `, typical ${c.cliffTypical.toFixed(1)}` : ""})` : ""}.`);
  if (c.forces.includes("block")) s.push(`<b>${rival(c) || "A rival"}</b> has a real hole here${num(c.rivalPremium) ? ` — a rival premium of ${c.rivalPremium.toFixed(1)} ${PAYLOAD.valueUnitShort}` : ""}. Value and denial at once.`);
  if (c.forces.includes("pure")) s.push(`His raw universal value${num(c.uv) ? ` (<b>${c.uv.toFixed(1)} ${PAYLOAD.valueUnitShort}</b>)` : ""} is the best in this field — context, not quality, holds his acquisition rank down.`);
  if (c.forces.includes("tie") && !leader) s.push(`${num(leader) ? "" : ""}Inside the measured noise band of the leader${num(candidates[0].tav) && num(c.tav) ? ` — <b>${(candidates[0].tav - c.tav).toFixed(1)} ${PAYLOAD.valueUnitShort}</b> off` : ""}; preference is a legitimate tiebreaker.`);
  if (c.waitNote) s.push(`${esc(c.waitNote.title)}`);
  else if (h && h.cls === "unavailable") s.push(h.text);
  if (h && h.cls === "imputed" && !c.waitNote) s.push(h.text);
  if (c.fillsRequiredSlot) s.push(`<b>Fills a required slot.</b> Ranked above higher-scoring candidates because your roster cannot otherwise still be filled legally.`);
  if (!num(c.tav)) s.push(`<b>Unpriced.</b> His position has no replacement level left to price against, so no acquisition value exists for him. That is an absence, not a zero.`);
  return s;
}
"""


# ---------------------------------------------------------------------------------------
# C1 RELIQUARY -- the incumbent's shape, argued with. Value leads. Row scale tracks the tier.
# ---------------------------------------------------------------------------------------
C1_CSS = r"""
.clock-bar {
  position: relative; overflow: hidden; display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; flex-wrap: wrap;
  padding: .9rem 1.2rem .8rem; border: 1px solid var(--line); border-radius: 10px; margin-bottom: .9rem;
  background: linear-gradient(180deg, color-mix(in srgb, var(--surface) 70%, transparent), color-mix(in srgb, var(--surface-2) 90%, transparent));
  backdrop-filter: blur(10px);
  border-top: 1px solid color-mix(in srgb, var(--gold) 45%, var(--line));
}
.clock-bar::after { content: ""; position: absolute; inset: 0 auto 0 -40%; width: 40%; pointer-events: none;
  background: linear-gradient(105deg, transparent, color-mix(in srgb, var(--gold-b) 12%, transparent) 50%, transparent);
  animation: sheen 12s ease-in-out infinite; }
@keyframes sheen { 0%, 60% { transform: translateX(0); } 100% { transform: translateX(350%); } }
.clock-bar .h { font-size: 1.15rem; letter-spacing: .08em; color: var(--ink); }
.clock-bar .meta { font-family: "JetBrains Mono", monospace; font-size: .7rem; color: var(--muted); letter-spacing: .04em; }
.legend { font-family: "JetBrains Mono", monospace; font-size: .64rem; letter-spacing: .05em; text-transform: uppercase; color: var(--muted); margin: 0 .2rem .7rem; display: flex; gap: 1rem; flex-wrap: wrap; }
.legend b { color: var(--muted); }
.board { display: flex; flex-direction: column; gap: .4rem; position: relative; }
.board::before { content: ""; position: absolute; inset: -6% -4% auto -4%; height: 45%; pointer-events: none;
  background: radial-gradient(60% 100% at 50% 0%, rgba(212,160,23,.07), transparent 70%); }
.row { position: relative; border: 1px solid var(--line); border-radius: 9px; cursor: pointer;
  background: linear-gradient(180deg, color-mix(in srgb, var(--surface) 84%, transparent), color-mix(in srgb, var(--surface-2) 90%, transparent));
  border-top-color: color-mix(in srgb, var(--gold) 20%, var(--line)); transition: border-color .15s ease, box-shadow .15s ease; }
.row:hover { box-shadow: inset 3px 0 0 color-mix(in srgb, var(--gold) 70%, transparent); border-color: var(--line-2); }
.row.open { border-color: color-mix(in srgb, var(--gold) 55%, var(--line-2)); box-shadow: inset 3px 0 0 var(--gold), 0 8px 26px rgba(0,0,0,.35); }
.head { display: grid; grid-template-columns: 2.2rem 1fr auto auto auto; align-items: center; gap: .9rem; }
/* SIZE, not opacity, carries the hierarchy. */
.row.decide { padding: .95rem 1.1rem; }
.row.decide .name { font-size: 1.12rem; font-weight: 700; }
.row.decide .value { font-size: 1.7rem; }
.row.context { padding: .55rem 1.1rem; }
.row.context .name { font-size: .95rem; font-weight: 600; }
.row.context .value { font-size: 1.15rem; }
.row.tail { padding: .3rem 1.1rem; border-color: color-mix(in srgb, var(--line) 60%, transparent); background: transparent; }
.row.tail .name { font-size: .86rem; font-weight: 500; }
.row.tail .value { font-size: .95rem; }
.row.tail .ticks, .row.tail .nec, .row.tail .chip { display: none; }
.rank { font-family: "JetBrains Mono", monospace; color: var(--muted); font-size: .74rem; }
.row.decide .rank { font-size: 1rem; color: var(--muted); }
.who { display: flex; align-items: baseline; gap: .55rem; min-width: 0; flex-wrap: wrap; }
.team { color: var(--muted); font-size: .8rem; }
.ticks { display: flex; gap: .3rem; }
.tick { font-size: .85rem; padding: 0 .2rem; border-radius: 4px; cursor: help; }
.tick[data-force="tie"] { color: var(--tie-b); } .tick[data-force="cliff"] { color: var(--cliff-b); }
.tick[data-force="block"] { color: var(--block-b); } .tick[data-force="pure"] { color: var(--pure); }
/* The badge is demoted to a mono word: the value is the loud thing, the tier is its caption. */
.nec { font-family: "JetBrains Mono", monospace; font-size: .62rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.nec.must { color: var(--violet-b); } .nec.strong { color: var(--sky-b); } .nec.pref { color: var(--emerald-b); } .nec.close { color: var(--amber-b); } .nec.low { color: var(--crimson-b); }
.value { font-family: "JetBrains Mono", monospace; font-weight: 700; text-align: right; min-width: 4.4rem; font-variant-numeric: tabular-nums; }
.value.neg { color: var(--crimson-b); }
.value .unit { font-size: .58rem; }
.chip { font-family: "JetBrains Mono", monospace; font-size: .64rem; padding: .05rem .35rem; border-radius: 3px; border: 1px solid var(--line-2); color: var(--muted); cursor: help; }
.chip.imputed { border-color: var(--amber); color: var(--amber-b); }
.chip.unavailable { border-style: dashed; }
.required { font-size: .6rem; font-weight: 700; color: var(--amber-b); border: 1px solid var(--amber); border-radius: 9px; padding: 1px 6px; letter-spacing: .05em; }
.fixture { font-family: "JetBrains Mono", monospace; font-size: .58rem; letter-spacing: .08em; color: var(--muted); border: 1px dashed var(--line-2); padding: 0 .35rem; border-radius: 3px; cursor: help; }
.detail { display: grid; grid-template-rows: 0fr; transition: grid-template-rows .22s ease; }
.row.open .detail { grid-template-rows: 1fr; }
.detail > div { overflow: hidden; min-height: 0; }
.detail .inner { margin-top: .7rem; padding-top: .7rem; border-top: 1px solid var(--line-2); font-size: .88rem; max-width: 70ch; }
.detail p { margin: 0 0 .45rem; }
.metrics { display: flex; gap: 1.1rem; flex-wrap: wrap; font-family: "JetBrains Mono", monospace; font-size: .72rem; color: var(--muted); margin-top: .5rem; }
.metrics b { color: var(--ink); }
.fold { text-align: center; font-family: "JetBrains Mono", monospace; font-size: .68rem; letter-spacing: .06em; color: var(--muted); padding: .5rem; cursor: pointer; border: 1px dashed var(--line-2); border-radius: 8px; }
"""

C1_BODY = r"""
<div class="clock-bar"><div><div class="h display" id="clock"></div><div class="meta" id="meta"></div></div><div class="meta" id="coverage"></div></div>
<div class="legend" id="legend"></div>
<div class="board" id="board"></div>
"""

C1_JS = TIER_JS + r"""
let openId = null, tailOpen = false;
function toggleRow(id) { openId = openId === id ? null : id; render(); }
const NEC_CLS = { "MUST TAKE": "must", "STRONG ACTION": "strong", "PREFERRED": "pref", "CLOSE CALL": "close", "LOW URGENCY": "low", "DOESN'T MATTER MUCH": "low" };
function render() {
  document.getElementById("clock").textContent = PAYLOAD.pickHeader;
  document.getElementById("meta").textContent = `${PAYLOAD.league} · ${PAYLOAD.intervening} picks to your next turn · regime ${PAYLOAD.decisionRegime}`;
  document.getElementById("coverage").textContent = coverage(candidates);
  document.getElementById("legend").innerHTML = `<span><b>${PAYLOAD.valueUnitShort}</b> = ${PAYLOAD.valueUnit} · signed · not fantasy points</span><span><b>PTS/WK</b> = season points per week to draft end</span><span><b>◣ ⊘ ◆ ≈</b> cliff · block · pure value · near-tie</span>`;
  const b = document.getElementById("board");
  const tailCount = candidates.filter((c, i) => tier(c, i) === "tail").length;
  b.innerHTML = candidates.map((c, i) => {
    const t = tier(c, i);
    if (t === "tail" && !tailOpen && candidates.findIndex((x, j) => tier(x, j) === "tail") === i)
      return `<div class="fold" onclick="tailOpen=true;render()">${tailCount} low-urgency rows folded — values ${fmtRange(candidates.filter((x, j) => tier(x, j) === "tail"))} · show</div>`;
    if (t === "tail" && !tailOpen) return "";
    const h = horizon(c);
    const wait = c.waitNote ? `<span class="chip ${h ? h.cls : ""}" title="${esc(c.waitNote.title)}${h ? " " + esc(h.text) : ""}">${c.waitNote.label}${h && h.cls === "imputed" ? " · est." : ""}</span>`
               : (h ? `<span class="chip ${h.cls}" title="${esc(h.text)}">wait ${ABSENT} · ${h.word}</span>` : "");
    return `<div class="row ${t}${openId === c.id ? " open" : ""}" tabindex="0" onclick="toggleRow('${c.id}')" onkeydown="if(event.key==='Enter'){this.click()}">
      <div class="head">
        <span class="rank">${i + 1}</span>
        <span class="who"><span class="name">${c.name}</span>${pillPos(c)}<span class="team">${c.team}</span>${c.fillsRequiredSlot ? '<span class="required" title="Ranked above higher-scoring candidates because your roster cannot otherwise still be filled legally.">FILLS REQUIRED SLOT</span>' : ""}${fixtureTag(c)}</span>
        <span class="ticks">${ticks(c)}</span>
        <span style="display:flex;gap:.6rem;align-items:center">${wait}<span class="nec ${NEC_CLS[c.necessity] || ""}">${c.necessity}</span></span>
        <span class="value ${num(c.tav) && c.tav < 0 ? "neg" : ""}" title="Acquisition value in ${PAYLOAD.valueUnit}">${fmt(c.tav, 0, PAYLOAD.valueUnitShort)}</span>
      </div>
      <div class="detail"><div><div class="inner">
        ${reasons(c, i === 0).map(r => `<p>${r}</p>`).join("") || "<p>No force fired for him; he is here on value alone.</p>"}
        <div class="metrics"><span>UV <b>${fmt(c.uv, 0)}</b> ${PAYLOAD.valueUnitShort}</span><span>PROJ <b>${fmt(c.proj, 0)}</b> season pts</span><span>SURV <b>${pct(c.survival)}</b></span><span>OPP COST <b>${fmt(c.opportunity_cost, 1)}</b> ${PAYLOAD.valueUnitShort}</span><span>DENIAL <b>${fmt(c.denial_value, 1)}</b> ${PAYLOAD.valueUnitShort}</span><span>${depth(c).text}</span></div>
      </div></div></div>
    </div>`;
  }).join("");
}
function fmtRange(rows) {
  const v = rows.map(c => c.tav).filter(num);
  if (!v.length) return "all unpriced";
  return `${Math.min(...v).toFixed(0)} to ${Math.max(...v).toFixed(0)} ${PAYLOAD.valueUnitShort}`;
}
"""

# ---------------------------------------------------------------------------------------
# C2 LEDGER -- density and comparison. A real table with unit headers; the decision band is
# bracketed; the tail folds; evidence slides in from the right.
# ---------------------------------------------------------------------------------------
C2_CSS = r"""
.wrap { display: grid; grid-template-columns: 1fr 0fr; gap: 0; transition: grid-template-columns .25s ease; }
.wrap.open { grid-template-columns: 1fr 24rem; }
.ledger { border: 1px solid var(--line); border-radius: 8px; overflow: hidden; background: var(--surface-2); }
.lh { display: grid; grid-template-columns: 2rem 1.3fr 3.2rem 5.2rem 5.2rem 5.2rem 4rem 5.4rem 6.2rem 7rem; gap: .5rem; align-items: baseline;
  padding: .55rem .8rem; font-family: "JetBrains Mono", monospace; font-size: .62rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted);
  background: var(--surface); border-bottom: 1px solid var(--line-2); position: sticky; top: 0; }
.lh .u { display: block; color: var(--muted); letter-spacing: .02em; text-transform: none; font-size: .6rem; }
.lr { display: grid; grid-template-columns: 2rem 1.3fr 3.2rem 5.2rem 5.2rem 5.2rem 4rem 5.4rem 6.2rem 7rem; gap: .5rem; align-items: baseline;
  padding: .42rem .8rem; border-bottom: 1px solid color-mix(in srgb, var(--line) 70%, transparent); font-family: "JetBrains Mono", monospace; font-size: .8rem; cursor: pointer; }
.lr:hover { background: color-mix(in srgb, var(--surface) 70%, transparent); }
.lr.sel { background: color-mix(in srgb, var(--gold) 9%, var(--surface)); box-shadow: inset 3px 0 0 var(--gold); }
.lr .n { font-family: "Segoe UI", system-ui, sans-serif; font-weight: 600; display: flex; gap: .4rem; align-items: baseline; flex-wrap: wrap; }
.lr.decide .n { font-size: .98rem; }
.lr.decide { font-size: .9rem; padding: .55rem .8rem; }
.lr.context .n { font-weight: 500; }
.lr.tail { font-size: .74rem; padding: .22rem .8rem; }
.lr.tail .n { font-weight: 400; font-size: .8rem; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.num.neg { color: var(--crimson-b); }
.band { grid-column: 1 / -1; font-family: "JetBrains Mono", monospace; font-size: .6rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); padding: .45rem .8rem .2rem; border-bottom: 1px solid var(--line); }
.band.decide { color: var(--muted); border-left: 3px solid var(--gold); }
.nec { font-size: .6rem; letter-spacing: .06em; text-transform: uppercase; }
.nec.must { color: var(--violet-b); } .nec.strong { color: var(--sky-b); } .nec.pref { color: var(--emerald-b); } .nec.close { color: var(--amber-b); } .nec.low { color: var(--crimson-b); }
.tick { padding: 0 .1rem; cursor: help; }
.tick[data-force="tie"] { color: var(--tie-b); } .tick[data-force="cliff"] { color: var(--cliff-b); } .tick[data-force="block"] { color: var(--block-b); } .tick[data-force="pure"] { color: var(--pure); }
.st { font-size: .6rem; letter-spacing: .04em; text-transform: uppercase; }
.st.imputed { color: var(--amber-b); } .st.unavailable { color: var(--muted); } .st.measured { color: var(--muted); }
.fold { grid-column: 1 / -1; text-align: center; font-family: "JetBrains Mono", monospace; font-size: .66rem; letter-spacing: .06em; color: var(--muted); padding: .45rem; cursor: pointer; }
.drawer { border-left: 1px solid var(--line-2); background: linear-gradient(180deg, color-mix(in srgb, var(--surface) 92%, transparent), var(--surface-2)); overflow: hidden; min-width: 0; }
.drawer .in { padding: 1rem 1.1rem; width: 24rem; font-size: .86rem; }
.drawer h3 { margin: 0 0 .2rem; font-size: 1.15rem; letter-spacing: .05em; }
.drawer .k { font-family: "JetBrains Mono", monospace; font-size: .62rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-top: .8rem; }
.drawer p { margin: .3rem 0; }
.kv { display: grid; grid-template-columns: 1fr auto; gap: .2rem .8rem; font-family: "JetBrains Mono", monospace; font-size: .74rem; }
.kv .v { text-align: right; color: var(--ink); }
.top { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: .6rem; font-family: "JetBrains Mono", monospace; font-size: .72rem; color: var(--muted); }
.top .h { font-size: 1.1rem; color: var(--ink); letter-spacing: .08em; }
.fixture { font-size: .56rem; letter-spacing: .08em; color: var(--muted); border: 1px dashed var(--line-2); padding: 0 .3rem; border-radius: 3px; cursor: help; font-family: "JetBrains Mono", monospace; }
"""
C2_BODY = r"""
<div class="top"><span class="h display" id="clock"></span><span id="coverage"></span></div>
<div class="wrap" id="wrap"><div class="ledger" id="ledger"></div><div class="drawer" id="drawer"><div class="in" id="drawer-in"></div></div></div>
"""
C2_JS = TIER_JS + r"""
let sel = null, tailOpen = false;
const NEC_CLS = { "MUST TAKE": "must", "STRONG ACTION": "strong", "PREFERRED": "pref", "CLOSE CALL": "close", "LOW URGENCY": "low", "DOESN'T MATTER MUCH": "low" };
function n(x, d) { return num(x) ? `<span class="num${x < 0 ? " neg" : ""}">${x.toFixed(d)}</span>` : `<span class="num"><span class="absent" title="Not measured">${ABSENT}</span></span>`; }
function render() {
  document.getElementById("clock").textContent = PAYLOAD.pickHeader;
  document.getElementById("coverage").textContent = `${PAYLOAD.league} · ${PAYLOAD.intervening} picks to your turn · ${coverage(candidates)}`;
  const U = PAYLOAD.valueUnitShort;
  const head = `<div class="lh"><span>#</span><span>Candidate</span><span>Forces</span><span class="num">Acq value<span class="u">${U}, signed</span></span><span class="num">Univ value<span class="u">${U}</span></span><span class="num">Proj<span class="u">season pts</span></span><span class="num">Survive<span class="u">to your turn</span></span><span class="num">Wait cost<span class="u">season pts/wk</span></span><span>Floor<span class="u">basis</span></span><span>Necessity<span class="u">engine tier</span></span></div>`;
  let lastTier = null;
  const tail = candidates.filter((c, i) => tier(c, i) === "tail");
  const rows = candidates.map((c, i) => {
    const t = tier(c, i);
    let band = "";
    if (t !== lastTier) { band = `<div class="band ${t}">${{decide: "the decision", context: "context", tail: "tail — low urgency"}[t]}</div>`; lastTier = t; }
    if (t === "tail" && !tailOpen) {
      if (tail[0].id === c.id) return band + `<div class="fold" onclick="tailOpen=true;render()">${tail.length} rows folded · show</div>`;
      return "";
    }
    const h = horizon(c);
    const wait = c.waitNote ? (c.waitNote.label === "free" ? `<span class="num" title="${esc(c.waitNote.title)}">free</span>` : `<span class="num" title="${esc(c.waitNote.title)}">${c.waitNote.label.replace(" pts/wk", "")}</span>`) : `<span class="num"><span class="absent" title="${h ? esc(h.text) : "Not carried"}">${ABSENT}</span></span>`;
    return band + `<div class="lr ${t}${sel === c.id ? " sel" : ""}" onclick="sel='${c.id}';render()">
      <span>${i + 1}</span>
      <span class="n">${c.name} ${pillPos(c)}${c.fillsRequiredSlot ? '<span class="st imputed" title="Ranked above higher-scoring candidates for roster legality">req. slot</span>' : ""}${fixtureTag(c)}</span>
      <span>${ticks(c)}</span>
      ${n(c.tav, 0)}${n(c.uv, 0)}${n(c.proj, 0)}
      <span class="num">${pct(c.survival)}</span>
      ${wait}
      <span class="st ${h ? h.cls : ""}" title="${h ? esc(h.text) : ""}">${h ? h.word : ""}</span>
      <span class="nec ${NEC_CLS[c.necessity]}">${c.necessity}</span>
    </div>`;
  }).join("");
  document.getElementById("ledger").innerHTML = head + rows;
  const c = candidates.find(x => x.id === sel);
  document.getElementById("wrap").classList.toggle("open", !!c);
  document.getElementById("drawer-in").innerHTML = c ? drawer(c, candidates.indexOf(c) === 0) : "";
}
function drawer(c, leader) {
  const d = depth(c), h = horizon(c);
  return `<h3 class="display">${c.name}</h3><div style="color:var(--muted);font-size:.8rem">${c.pos} · ${c.team} · rank ${candidates.indexOf(c) + 1} · ${c.necessity} (${fmt(c.pick_necessity, 0)}/100)</div>
    <div class="k">Why</div>${reasons(c, leader).map(r => `<p>${r}</p>`).join("") || "<p>No force fired; on value alone.</p>"}
    <div class="k">Numbers, each with its unit</div>
    <div class="kv">
      <span>Acquisition value</span><span class="v">${fmt(c.tav, 1)} ${PAYLOAD.valueUnitShort}</span>
      <span>Universal value</span><span class="v">${fmt(c.uv, 1)} ${PAYLOAD.valueUnitShort}</span>
      <span>Projected points</span><span class="v">${fmt(c.proj, 0)} season</span>
      <span>Survival to your turn</span><span class="v">${pct(c.survival)}</span>
      <span>Opportunity cost of waiting</span><span class="v">${fmt(c.opportunity_cost, 1)} ${PAYLOAD.valueUnitShort}</span>
      <span>Expected value if you wait</span><span class="v">${fmt(c.expected_value_of_waiting, 1)} ${PAYLOAD.valueUnitShort}</span>
      <span>Denial value</span><span class="v">${fmt(c.denial_value, 1)} ${PAYLOAD.valueUnitShort}</span>
      <span>Priced against</span><span class="v">${c.replacementBasis ? (c.replacementBasis === "predraft_anchor" ? "pre-draft anchor" : "live starter demand") : `<span class="absent">${ABSENT}</span>`}</span>
      <span>Draft-end floor</span><span class="v">${h ? `<span class="st ${h.cls}">${h.word}</span>` : `<span class="absent">${ABSENT}</span>`}</span>
    </div>
    <div class="k">Depth</div><p>${d.text}</p>`;
}
"""

# ---------------------------------------------------------------------------------------
# C3 VERDICT -- the reason leads. The leader is a verdict plate; every other candidate is a
# sentence card whose numbers are a small footer. Forces are the organising principle.
# ---------------------------------------------------------------------------------------
C3_CSS = r"""
.plate { position: relative; overflow: hidden; border-radius: 14px; padding: 1.4rem 1.6rem 1.2rem; margin-bottom: 1rem;
  border: 1px solid color-mix(in srgb, var(--gold) 40%, var(--line));
  background: radial-gradient(120% 140% at 0% 0%, color-mix(in srgb, var(--gold) 9%, transparent), transparent 55%), linear-gradient(180deg, var(--surface), var(--surface-2)); }
.plate::before { content: ""; position: absolute; inset: 0; pointer-events: none; background: linear-gradient(120deg, transparent 30%, color-mix(in srgb, var(--gold-b) 6%, transparent) 50%, transparent 70%); background-size: 300% 100%; animation: facet 14s linear infinite; }
@keyframes facet { from { background-position: 100% 0; } to { background-position: -100% 0; } }
.plate .eyebrow { font-family: "JetBrains Mono", monospace; font-size: .64rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
.plate h2 { margin: .15rem 0 .4rem; font-size: 2rem; letter-spacing: .05em; display: flex; gap: .7rem; align-items: baseline; flex-wrap: wrap; }
.plate .verdict { font-size: 1.05rem; max-width: 72ch; }
.plate .verdict p { margin: 0 0 .5rem; }
.plate .foot { display: flex; gap: 1.4rem; flex-wrap: wrap; margin-top: .8rem; font-family: "JetBrains Mono", monospace; font-size: .74rem; color: var(--muted); }
.plate .foot b { color: var(--ink); font-size: 1rem; }
.plate .foot .neg b { color: var(--crimson-b); }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(21rem, 1fr)); gap: .7rem; }
.card { border: 1px solid var(--line); border-radius: 10px; padding: .9rem 1rem; background: color-mix(in srgb, var(--surface) 88%, transparent); display: flex; flex-direction: column; gap: .4rem; }
.card.context { padding: .65rem .9rem; }
.card.tail { padding: .45rem .8rem; grid-column: span 1; }
.card .t { display: flex; justify-content: space-between; align-items: baseline; gap: .5rem; }
.card .n { font-weight: 700; font-size: 1rem; display: flex; gap: .45rem; align-items: baseline; flex-wrap: wrap; }
.card.tail .n { font-weight: 500; font-size: .86rem; }
.card .rank { font-family: "JetBrains Mono", monospace; color: var(--muted); font-size: .7rem; }
.card .lead { font-size: .9rem; }
.card.tail .lead, .card.tail .foot { display: none; }
.card .lead p { margin: 0 0 .3rem; }
.card .foot { font-family: "JetBrains Mono", monospace; font-size: .68rem; color: var(--muted); display: flex; gap: .9rem; flex-wrap: wrap; }
.card .foot b { color: var(--muted); }
.card .foot .neg b { color: var(--crimson-b); }
.forcebar { display: flex; gap: .35rem; align-items: center; }
.force { font-family: "JetBrains Mono", monospace; font-size: .64rem; letter-spacing: .06em; text-transform: uppercase; padding: .08rem .4rem; border-radius: 3px; border: 1px solid; cursor: help; }
.force[data-force="tie"] { color: var(--tie-b); border-color: var(--tie); } .force[data-force="cliff"] { color: var(--cliff-b); border-color: var(--cliff); }
.force[data-force="block"] { color: var(--block-b); border-color: var(--block); } .force[data-force="pure"] { color: var(--pure); border-color: var(--tie); }
.nec { font-family: "JetBrains Mono", monospace; font-size: .58rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.section { font-family: "JetBrains Mono", monospace; font-size: .62rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin: 1rem 0 .4rem; }
.fixture { font-family: "JetBrains Mono", monospace; font-size: .56rem; letter-spacing: .08em; color: var(--muted); border: 1px dashed var(--line-2); padding: 0 .3rem; border-radius: 3px; cursor: help; }
.top { display: flex; justify-content: space-between; margin-bottom: .6rem; font-family: "JetBrains Mono", monospace; font-size: .7rem; color: var(--muted); }
"""
C3_BODY = r"""<div class="top"><span id="clock"></span><span id="coverage"></span></div><div id="plate"></div><div id="cards"></div>"""
C3_JS = TIER_JS + r"""
function forces(c) { return `<span class="forcebar">${c.forces.map(f => `<span class="force" data-force="${f}" title="${forceTitle(f)}">${GLYPH[f]} ${f}</span>`).join("")}</span>`; }
function foot(c) {
  const U = PAYLOAD.valueUnitShort;
  return `<span class="${num(c.tav) && c.tav < 0 ? "neg" : ""}">acq <b>${fmt(c.tav, 0)}</b> ${U}</span><span>uv <b>${fmt(c.uv, 0)}</b> ${U}</span><span>proj <b>${fmt(c.proj, 0)}</b> season</span><span>survive <b>${pct(c.survival)}</b></span><span>denial <b>${fmt(c.denial_value, 1)}</b> ${U}</span>`;
}
function render() {
  document.getElementById("clock").textContent = `${PAYLOAD.pickHeader} · ${PAYLOAD.league} · ${PAYLOAD.intervening} picks to your turn`;
  document.getElementById("coverage").textContent = coverage(candidates);
  const L = candidates[0];
  const lr = reasons(L, true);
  const survivalLine = num(L.survival) ? `${Math.round(L.survival * 100)}% survival to your next turn — ` : "survival to your next turn isn't estimable — ";
  document.getElementById("plate").innerHTML = `<div class="plate">
    <div class="eyebrow">the pick · ${PAYLOAD.decisionRegime} regime · ${L.necessity}${num(L.pick_necessity) ? ` ${L.pick_necessity.toFixed(0)}/100` : ""}</div>
    <h2 class="display">${L.name} ${pillPos(L)} <span style="font-size:.9rem;color:var(--muted);letter-spacing:0">${L.team}</span>${fixtureTag(L)}</h2>
    <div class="verdict"><p>${PAYLOAD.decisionRegime === "decisive" && num(L.tav) ? `<b>Best-in-class, full stop.</b> ${survivalLine}he is not walking back to this roster.` : `<b>The board's leader.</b> ${survivalLine}read the reasons before you commit.`}</p>${lr.map(r => `<p>${r}</p>`).join("")}</div>
    ${forces(L)}
    <div class="foot">${foot(L)}<span>${depth(L).text}</span></div>
  </div>`;
  let last = null;
  document.getElementById("cards").innerHTML = candidates.slice(1).map((c, j) => {
    const i = j + 1, t = tier(c, i);
    let sec = "";
    if (t !== last) { sec = `<div class="section" style="grid-column:1/-1">${{decide: "also in the decision", context: "context", tail: "tail — low urgency, shown as names and values only"}[t]}</div>`; last = t; }
    const rs = reasons(c, false);
    return sec + `<div class="card ${t}"><div class="t"><span class="n"><span class="rank">${i}</span>${c.name} ${pillPos(c)}${fixtureTag(c)}</span><span class="nec">${c.necessity}${t === "tail" ? ` · <b style="color:${num(c.tav) && c.tav < 0 ? "var(--crimson-b)" : "var(--muted)"}">${fmt(c.tav, 0)}</b> ${PAYLOAD.valueUnitShort}` : ""}</span></div>
      ${t !== "tail" ? forces(c) : ""}
      <div class="lead">${(rs.length ? rs : ["No force fired for him; he is here on value alone."]).slice(0, 2).map(r => `<p>${r}</p>`).join("")}</div>
      <div class="foot">${foot(c)}</div></div>`;
  }).join("");
}
"""

# ---------------------------------------------------------------------------------------
# C4 HOARD -- the departure. Candidates are cut gems on a dark cloth: size is relevance, facet
# tint is position, the clock is an orb, the tail is a strip of small stones in a tray.
# Layers slide with the pointer (parallax), and stop dead under reduced motion.
# ---------------------------------------------------------------------------------------
C4_CSS = r"""
body { background: radial-gradient(90% 60% at 50% -10%, #221c10, var(--bg) 60%); }
.orb { position: relative; margin: 0 auto 1.2rem; width: min(100%, 44rem); border-radius: 999px; padding: .8rem 1.8rem; text-align: center;
  border: 1px solid color-mix(in srgb, var(--gold) 50%, var(--line)); background: linear-gradient(180deg, color-mix(in srgb, var(--surface) 60%, transparent), color-mix(in srgb, var(--surface-2) 90%, transparent));
  backdrop-filter: blur(12px); box-shadow: 0 0 0 6px color-mix(in srgb, var(--gold) 7%, transparent), 0 20px 50px rgba(0,0,0,.5); }
.orb .h { font-size: 1.3rem; letter-spacing: .12em; color: var(--ink); }
.orb .m { font-family: "JetBrains Mono", monospace; font-size: .66rem; letter-spacing: .06em; color: var(--muted); text-transform: uppercase; }
.gems { display: grid; grid-template-columns: repeat(12, 1fr); gap: .8rem; perspective: 1200px; }
.gem { position: relative; border-radius: 14px; padding: 1rem 1.1rem; overflow: hidden; cursor: pointer; will-change: transform; transition: transform .25s ease, box-shadow .25s ease;
  background: linear-gradient(160deg, color-mix(in srgb, var(--facet) 16%, var(--surface)), var(--surface-2) 70%);
  border: 1px solid color-mix(in srgb, var(--facet) 35%, var(--line)); box-shadow: 0 12px 30px rgba(0,0,0,.4), inset 0 1px 0 color-mix(in srgb, var(--facet) 40%, transparent); }
.gem::before { content: ""; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(115deg, transparent 40%, color-mix(in srgb, white 7%, transparent) 50%, transparent 60%), conic-gradient(from 210deg at 85% 15%, transparent 0 70%, color-mix(in srgb, var(--facet) 22%, transparent) 78%, transparent 86%); }
.gem:hover { transform: translateY(-4px) rotateX(2deg); box-shadow: 0 22px 44px rgba(0,0,0,.5); }
.gem.decide { grid-column: span 6; min-height: 11rem; }
.gem.decide.leader { grid-column: span 12; min-height: 13rem; border-color: color-mix(in srgb, var(--gold) 55%, var(--line)); box-shadow: 0 0 0 1px color-mix(in srgb, var(--gold) 25%, transparent), 0 24px 60px rgba(0,0,0,.55); }
.gem.context { grid-column: span 4; padding: .8rem .9rem; }
.tray { grid-column: 1 / -1; display: flex; gap: .5rem; flex-wrap: wrap; padding: .8rem; border-radius: 12px; border: 1px dashed var(--line-2); background: color-mix(in srgb, var(--surface-2) 60%, transparent); }
.tray .label { flex-basis: 100%; font-family: "JetBrains Mono", monospace; font-size: .6rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
.stone { font-family: "JetBrains Mono", monospace; font-size: .74rem; padding: .3rem .6rem; border-radius: 8px; border: 1px solid color-mix(in srgb, var(--facet) 35%, var(--line)); background: color-mix(in srgb, var(--facet) 8%, var(--surface)); display: flex; gap: .5rem; align-items: baseline; }
.stone .v { font-weight: 700; }
.stone .v.neg { color: var(--crimson-b); }
.gem .name { font-size: 1.35rem; font-weight: 700; letter-spacing: .03em; display: flex; gap: .6rem; align-items: baseline; flex-wrap: wrap; }
.gem.leader .name { font-size: 2rem; }
.gem.context .name { font-size: 1rem; }
.gem .rank { font-family: "JetBrains Mono", monospace; font-size: .7rem; color: var(--muted); }
.gem .big { position: absolute; right: 1.1rem; top: .9rem; text-align: right; font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 2.4rem; line-height: 1; font-variant-numeric: tabular-nums; }
.gem.leader .big { font-size: 3.4rem; }
.gem.context .big { font-size: 1.5rem; }
.gem .big.neg { color: var(--crimson-b); }
.gem .big .unit { display: block; font-size: .6rem; font-weight: 500; letter-spacing: .06em; text-transform: uppercase; margin: .2rem 0 0; }
.gem .marks { display: flex; gap: .4rem; margin: .4rem 0; }
.mark { font-family: "JetBrains Mono", monospace; font-size: .9rem; width: 1.6rem; height: 1.6rem; display: grid; place-items: center; border-radius: 6px; border: 1px solid; cursor: help; }
.mark[data-force="tie"] { color: var(--tie-b); border-color: var(--tie); } .mark[data-force="cliff"] { color: var(--cliff-b); border-color: var(--cliff); }
.mark[data-force="block"] { color: var(--block-b); border-color: var(--block); } .mark[data-force="pure"] { color: var(--pure); border-color: var(--tie); }
.gem .why { font-size: .9rem; max-width: 62ch; margin-top: .3rem; }
.gem .why p { margin: 0 0 .3rem; }
.gem.context .why { font-size: .82rem; }
.gem .strip { display: flex; gap: 1rem; flex-wrap: wrap; font-family: "JetBrains Mono", monospace; font-size: .7rem; color: var(--muted); margin-top: .5rem; }
.gem .strip b { color: var(--ink); }
.nec { font-family: "JetBrains Mono", monospace; font-size: .6rem; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }
.fixture { font-family: "JetBrains Mono", monospace; font-size: .56rem; letter-spacing: .08em; color: var(--muted); border: 1px dashed var(--line-2); padding: 0 .3rem; border-radius: 3px; cursor: help; }
@media (max-width: 800px) { .gem.decide, .gem.context { grid-column: span 12; } }
"""
C4_BODY = r"""<div class="orb"><div class="h display" id="clock"></div><div class="m" id="meta"></div></div><div class="gems" id="gems"></div>"""
C4_JS = TIER_JS + r"""
const FACET = { QB: "#8f86f0", RB: "#17bfa0", WR: "#4aa8ef", TE: "#e8683f", K: "#a09480", DEF: "#ef7fc0", DL: "#a09480", LB: "#a09480", DB: "#a09480" };
function render() {
  document.getElementById("clock").textContent = PAYLOAD.pickHeader;
  document.getElementById("meta").textContent = `${PAYLOAD.league} · ${PAYLOAD.intervening} picks to your turn · ${coverage(candidates)} · ${PAYLOAD.valueUnitShort} = ${PAYLOAD.valueUnit}, not fantasy points`;
  const tail = [];
  const html = candidates.map((c, i) => {
    const t = tier(c, i);
    if (t === "tail") { tail.push(c); return ""; }
    const rs = reasons(c, i === 0);
    return `<div class="gem ${t}${i === 0 ? " leader" : ""}" style="--facet:${FACET[c.pos] || FACET.K}" tabindex="0" data-i="${i}">
      <div class="big ${num(c.tav) && c.tav < 0 ? "neg" : ""}" title="Acquisition value in ${PAYLOAD.valueUnit}">${num(c.tav) ? c.tav.toFixed(0) : `<span class="absent" title="Unpriced: no replacement level at his position. An absence, not a zero.">${ABSENT}</span>`}<span class="unit">acq · ${PAYLOAD.valueUnitShort}</span></div>
      <div class="name display"><span class="rank">${i + 1}</span>${c.name} ${pillPos(c)}${fixtureTag(c)}</div>
      <div class="nec">${c.necessity}${c.fillsRequiredSlot ? " · fills required slot" : ""}</div>
      <div class="marks">${c.forces.map(f => `<span class="mark" data-force="${f}" title="${forceTitle(f)}">${GLYPH[f]}</span>`).join("")}</div>
      <div class="why">${(rs.length ? rs : ["On value alone."]).slice(0, i === 0 ? 4 : 2).map(r => `<p>${r}</p>`).join("")}</div>
      <div class="strip"><span>uv <b>${fmt(c.uv, 0)}</b> ${PAYLOAD.valueUnitShort}</span><span>proj <b>${fmt(c.proj, 0)}</b> season pts</span><span>survive <b>${pct(c.survival)}</b></span>${c.waitNote ? `<span title="${esc(c.waitNote.title)}">wait <b>${c.waitNote.label}</b></span>` : (horizon(c) ? `<span title="${esc(horizon(c).text)}">wait <b><span class="absent">${ABSENT}</span></b> ${horizon(c).word}</span>` : "")}<span>denial <b>${fmt(c.denial_value, 1)}</b></span></div>
    </div>`;
  }).join("");
  const trayHtml = tail.length ? `<div class="tray"><span class="label">the tray · ${tail.length} low-urgency stones · names and values only</span>${tail.map(c => `<span class="stone" style="--facet:${FACET[c.pos] || FACET.K}" title="${c.necessity}">${c.name} ${pillPos(c)} <span class="v ${num(c.tav) && c.tav < 0 ? "neg" : ""}">${num(c.tav) ? c.tav.toFixed(0) : `<span class="absent">${ABSENT}</span>`}</span>${fixtureTag(c)}</span>`).join("")}</div>` : "";
  document.getElementById("gems").innerHTML = html + trayHtml;
  document.querySelectorAll(".gem").forEach(g => {
    g.addEventListener("mousemove", e => {
      if (document.documentElement.classList.contains("reduced-motion") || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const r = g.getBoundingClientRect(); const x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
      g.style.transform = `translateY(-4px) rotateX(${-y * 4}deg) rotateY(${x * 5}deg)`;
    });
    g.addEventListener("mouseleave", () => { g.style.transform = ""; });
  });
}
"""

# ---------------------------------------------------------------------------------------
# C5 CLOCK -- time leads. The picks between now and your next turn are a strip across the
# top; each candidate's survival is a marker on that strip, in the engine's order, never
# re-sorted. The leader is a hero; rows are compact and widen with relevance.
# ---------------------------------------------------------------------------------------
C5_CSS = r"""
.hero { display: grid; grid-template-columns: 1fr auto; gap: 1.2rem; align-items: end; padding: 1.2rem 1.4rem; border-radius: 12px; margin-bottom: .8rem;
  border: 1px solid var(--line); border-bottom: 1px solid color-mix(in srgb, var(--gold) 45%, var(--line));
  background: linear-gradient(180deg, color-mix(in srgb, var(--surface) 75%, transparent), color-mix(in srgb, var(--surface-2) 95%, transparent)); backdrop-filter: blur(8px); }
.hero .eyebrow { font-family: "JetBrains Mono", monospace; font-size: .64rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
.hero h2 { margin: .1rem 0; font-size: 1.9rem; letter-spacing: .05em; display: flex; gap: .6rem; align-items: baseline; flex-wrap: wrap; }
.hero .why { font-size: .95rem; max-width: 70ch; }
.hero .why p { margin: .2rem 0; }
.hero .val { text-align: right; font-family: "JetBrains Mono", monospace; }
.hero .val .n { font-size: 3rem; font-weight: 700; line-height: 1; }
.hero .val .n.neg { color: var(--crimson-b); }
.hero .val .u { display: block; font-size: .64rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-top: .3rem; }
.strip { position: sticky; top: 0; z-index: 2; margin: .2rem 0 .6rem; padding: .5rem .8rem .3rem; border-radius: 8px; background: color-mix(in srgb, var(--bg) 92%, transparent); backdrop-filter: blur(6px); border: 1px solid var(--line); }
.strip .lbl { font-family: "JetBrains Mono", monospace; font-size: .6rem; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); display: flex; justify-content: space-between; }
.axis { position: relative; height: 1.4rem; margin: .2rem 0; }
.axis .line { position: absolute; left: 0; right: 0; top: .65rem; height: 1px; background: var(--line-2); }
.axis .p { position: absolute; top: .35rem; width: 1px; height: .6rem; background: var(--line-2); }
.axis .p::after { content: attr(data-n); position: absolute; top: .7rem; left: -.5rem; font-family: "JetBrains Mono", monospace; font-size: .52rem; color: var(--muted); }
.axis .me { position: absolute; right: -1px; top: .15rem; width: 2px; height: 1rem; background: var(--gold); }
.row { display: grid; grid-template-columns: 2rem 12rem 1fr 5rem 5.2rem; gap: .8rem; align-items: center; padding: .38rem .8rem; border-bottom: 1px solid color-mix(in srgb, var(--line) 70%, transparent); }
.row.decide { padding: .6rem .8rem; }
.row.decide .name { font-size: 1.02rem; font-weight: 700; }
.row.context .name { font-weight: 600; font-size: .92rem; }
.row.tail { padding: .2rem .8rem; }
.row.tail .name { font-weight: 400; font-size: .82rem; }
.row.tail .track { opacity: 1; }
.rank { font-family: "JetBrains Mono", monospace; font-size: .7rem; color: var(--muted); }
.name { display: flex; gap: .4rem; align-items: baseline; flex-wrap: wrap; min-width: 0; }
.track { position: relative; height: 1.2rem; }
.track .base { position: absolute; left: 0; right: 0; top: .58rem; height: 1px; background: color-mix(in srgb, var(--line-2) 60%, transparent); }
.track .dot { position: absolute; top: .18rem; width: .85rem; height: .85rem; border-radius: 50%; border: 2px solid var(--sky-b); background: var(--bg); transform: translateX(-50%); }
.track .dot.gone { border-color: var(--crimson-b); background: var(--crimson-b); }
.track .dot.safe { border-color: var(--emerald-b); }
.track .lab { position: absolute; top: -.05rem; font-family: "JetBrains Mono", monospace; font-size: .62rem; color: var(--muted); transform: translateX(.6rem); white-space: nowrap; }
.track .none { position: absolute; left: 0; right: 0; top: .1rem; text-align: center; font-family: "JetBrains Mono", monospace; font-size: .62rem; }
.val { text-align: right; font-family: "JetBrains Mono", monospace; font-weight: 700; font-variant-numeric: tabular-nums; }
.val.neg { color: var(--crimson-b); }
.row.decide .val { font-size: 1.15rem; }
.f { display: flex; gap: .3rem; justify-content: flex-end; }
.f .tick { cursor: help; font-family: "JetBrains Mono", monospace; }
.tick[data-force="tie"] { color: var(--tie-b); } .tick[data-force="cliff"] { color: var(--cliff-b); } .tick[data-force="block"] { color: var(--block-b); } .tick[data-force="pure"] { color: var(--pure); }
.nec { font-family: "JetBrains Mono", monospace; font-size: .56rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.fixture { font-family: "JetBrains Mono", monospace; font-size: .56rem; letter-spacing: .08em; color: var(--muted); border: 1px dashed var(--line-2); padding: 0 .3rem; border-radius: 3px; cursor: help; }
.head { display: grid; grid-template-columns: 2rem 12rem 1fr 5rem 5.2rem; gap: .8rem; padding: .2rem .8rem; font-family: "JetBrains Mono", monospace; font-size: .58rem; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }
.head .r { text-align: right; }
"""
C5_BODY = r"""<div id="hero"></div><div class="strip" id="strip"></div><div class="head"><span>#</span><span>candidate</span><span>survival to your next turn, across the picks between</span><span class="r">acq · UV pts</span><span class="r">forces</span></div><div id="rows"></div>"""
C5_JS = TIER_JS + r"""
function render() {
  const L = candidates[0], N = PAYLOAD.intervening;
  document.getElementById("hero").innerHTML = `<div class="hero"><div>
    <div class="eyebrow">${PAYLOAD.pickHeader} · ${PAYLOAD.league} · ${N} picks before you choose again · ${coverage(candidates)}</div>
    <h2 class="display">${L.name} ${pillPos(L)}${fixtureTag(L)}</h2>
    <div class="why">${(reasons(L, true).length ? reasons(L, true) : ["The board's leader on value alone."]).slice(0, 3).map(r => `<p>${r}</p>`).join("")}</div>
    </div><div class="val"><span class="n ${num(L.tav) && L.tav < 0 ? "neg" : ""}">${num(L.tav) ? L.tav.toFixed(0) : `<span class="absent" title="Unpriced: no replacement level at his position. An absence, not a zero.">${ABSENT}</span>`}</span><span class="u">acquisition value · ${PAYLOAD.valueUnitShort}</span><span class="u">${L.necessity} · survive ${pct(L.survival)}</span></div></div>`;
  document.getElementById("strip").innerHTML = `<div class="lbl"><span>now</span><span>${N} intervening picks</span><span>your next turn</span></div><div class="axis"><div class="line"></div>${PAYLOAD.nextPicks.slice(0, N).map((r, k) => `<span class="p" style="left:${(k + 1) / (N + 1) * 100}%" data-n="${k + 1}" title="${r}"></span>`).join("")}<span class="me" title="your next turn"></span></div>`;
  document.getElementById("rows").innerHTML = candidates.map((c, i) => {
    const t = tier(c, i);
    // Survival is a MARKER on the strip: its x is the probability, read against the picks it
    // spans. It is not a bar -- nothing is filled from zero -- and absence is a word in the lane.
    const marker = num(c.survival)
      ? `<div class="base"></div><span class="dot ${c.survival <= 0.05 ? "gone" : c.survival >= 0.6 ? "safe" : ""}" style="left:${c.survival * 100}%" title="${Math.round(c.survival * 100)}% chance he is still here at your next turn"></span><span class="lab" style="left:${c.survival * 100}%">${Math.round(c.survival * 100)}%</span>`
      : `<span class="none"><span class="absent" title="Survival to your next turn was not estimable for him.">not estimable</span></span>`;
    return `<div class="row ${t}"><span class="rank">${i + 1}</span><span class="name">${c.name} ${pillPos(c)}${fixtureTag(c)}<span class="nec">${t === "tail" ? "" : c.necessity}</span></span><div class="track">${marker}</div><span class="val ${num(c.tav) && c.tav < 0 ? "neg" : ""}" title="${PAYLOAD.valueUnit}">${num(c.tav) ? c.tav.toFixed(0) : `<span class="absent" title="Unpriced">${ABSENT}</span>`}</span><span class="f">${c.forces.map(f => `<span class="tick" data-force="${f}" title="${forceTitle(f)}">${GLYPH[f]}</span>`).join("")}</span></div>`;
  }).join("");
}
"""

VARIANTS = [
    ("draft_room_v1_reliquary", "C1 · Reliquary", "the incumbent's shape, argued with: value leads, size carries hierarchy",
     "The acquisition value is the loudest element on every row and its type size tracks decision relevance (decide / context / tail), so the eye lands on the top six before it reads a word. The necessity badge is demoted to a mono caption. The tail folds into one line that states its value range. Glass plates, a gold hairline and a slow chrome sheen carry the brand; no data fades.",
     "Comparison across rows is by scanning one column; the reasons live behind a click. A candidate outside the decision tier gets less room even when a drafter wants to argue for him.",
     C1_CSS, C1_BODY, C1_JS),
    ("draft_room_v2_ledger", "C2 · Ledger", "density and comparison: a real table with unit headers and a sliding evidence drawer",
     "Every quantity is a column with its unit in the header, so nothing on the page is a bare number; the decision band is bracketed, the tail folds. Selecting a row slides a drawer in from the right with the reasons and the full numbers-with-units list. Hierarchy is row height and type size only.",
     "It reads as a spreadsheet. The prose explanation is one click away instead of in the row, and the page is wide -- on a phone the table must scroll horizontally.",
     C2_CSS, C2_BODY, C2_JS),
    ("draft_room_v3_verdict", "C3 · Verdict", "the reason leads: a verdict plate for the pick, sentence cards for the field",
     "The pick is a plate whose text is the argument, with the numbers as a footer; every other candidate is a card that leads with its forces and two sentences. Hierarchy is the amount of text: decision cards get reasons, context cards get one line, the tail gets a name and a value.",
     "Column comparison is gone -- to compare two numbers you read two cards. It is the most honest about WHY and the least efficient about HOW MUCH, and it needs more vertical space than any other direction.",
     C3_CSS, C3_BODY, C3_JS),
    ("draft_room_v4_hoard", "C4 · Hoard", "the departure: candidates as cut gems on a cloth, the clock as an orb, the tail in a tray",
     "A striking, spatial board: card size is relevance, facet tint is position, the leader spans the width with a 3.4rem numeral, and the cards tilt slightly under the pointer (dead under reduced motion). The tail is a tray of small stones with names and values only. Gold is the orb's ring and the leader's border -- chrome, never a value.",
     "Rank as a strict vertical order is weakened by the grid; the eye reads size before rank number. It is the most expensive layout to keep legible on narrow screens and the least like a drafting tool people already know.",
     C4_CSS, C4_BODY, C4_JS),
    ("draft_room_v5_clock", "C5 · Clock", "time leads: survival is a marker on a strip of the picks between now and your next turn",
     "The one quantity a drafter cannot recover from -- will he still be here -- is the widest column, drawn as a marker on the actual intervening picks (16 of them, from the snapshot), colour-coded gone / coin-flip / safe with a percentage beside it. The leader is a hero with its reasons; rows stay in the engine's order and grow with relevance. An unestimable survival is a word in the lane, not a marker at zero.",
     "Value is a narrow column on the right; the forces are glyphs only. A drafter who thinks in value first has to read across. The strip is a probability marker, not a timeline of who picks when -- it must not be read as 'he goes at pick 9'.",
     C5_CSS, C5_BODY, C5_JS),
]
