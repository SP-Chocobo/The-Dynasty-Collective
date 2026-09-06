"""Round 3 -- the owner's direction: H2's split field as three bands of decreasing weight.

    BAND 1  the leader: one full-width plate that is itself a row (keyboard-reachable, opens
            to the receipt). Fuller than S1's plate, still EARNED: the verdict now states the
            two engine inputs that make the regime what it is (margin over the second priced
            candidate against the noise band; survival against the decisive bar), then at
            most four sentences each about a fact that is present and non-obvious for HIM --
            a consensus reach, the roster terms that lift his price above his raw value, the
            forces that fired with their sizes. Nothing about an absent number, nothing true
            of every row.
    BAND 2  the rest of the engine's CONTIGUOUS decide tier. Derived, never hard-coded: the
            grid's capacity (two rows of two in R1, two rows of three in R2 and R3) is a CAP,
            not a count. A tier of two shows two cards and band 3 starts early; a tier that
            outruns the grid shows the cap as cards and the remainder as full-weight decide
            rows, and the band label says which is which. On the real 3.03 board the tier
            holds 8 (the 14-row slice) and 11 (the 33-row board), so the cap binds here and
            the label reads "7 more the engine holds live . 4 as cards, 3 as rows".
    BAND 3  "keep an eye on". R1 and R2: strict engine order, and the reason a row deserves
            eyes is a MARK -- the next man at each position after the tier (a filter over
            engine order, the same concept the app's position view already uses), context
            elevating his price, fills a required slot. No sort key of this module's own
            (G6). R3: the same rows, grouped into position LANES, each lane in engine order
            with the overall rank on every row, lanes ordered by their first member's engine
            rank -- a lens, not a ranking, and the page says so. The tail folds below.

THE CLIFF IS A NUMBER (#175). A third of every priced row clears the engine's materiality
floor (CLIFF_MIN_MATERIAL_GAP, which is the 2.0-point noise band), so the boolean is chrome.
Here the cliff never gets a coloured glyph: on the plate and the cards it is a factor line
that leads with its SIZE (the drop-off behind him against the position's typical gap, and
the positional forfeit by your next turn); on rows it is "◣ 12" in muted mono -- the
magnitude, at the weight of a detail. Block, pure value and near-tie keep their colour
because they remain rare. R3's lane header carries the position's forfeit and draft-end
floor once, because they are positional facts that every row of a position repeats.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from s_variants import CARD_JS, H1_BODY, MATERIAL_CSS, S1_CSS, SPINE_CSS, SPINE_JS  # noqa: E402

BAND_JS = SPINE_JS + CARD_JS + r"""
const BAND = PAYLOAD.nearTieBand, DECISIVE_SURV = PAYLOAD.decisiveSurvival, CLIFF_MIN = PAYLOAD.cliffMinGap;
function titleCase(s) { return String(s).toLowerCase().replace(/^\w/, ch => ch.toUpperCase()); }
function survWord(c) { const p = c.survival * 100; return p > 0 && p < 0.5 ? "under 1%" : `${Math.round(p)}%`; }

// THE CLIFF IS A NUMBER (#175). The engine's cliff entry from earned() led with the forfeit;
// this one leads with the drop-off behind him against the position's typical gap, and says
// what the forfeit is. An unmeasured size stays a labelled absence, never a sentence.
function earned3(c, i, cands) {
  return earned(c, i, cands).map(e => {
    if (e.k !== "cliff") return e;
    if (!num(c.cliffGap)) return { k: "cliff", label: "Cliff · size not measured", t: "" };
    const typ = num(c.cliffTypical) ? ` (typical ${c.pos} gap ${c.cliffTypical.toFixed(1)})` : "";
    const ff = num(c.forfeit) && c.forfeit > 0 ? `; skipping ${c.pos} until your next turn forfeits about ${c.forfeit.toFixed(1)} ${U}` : "";
    return { k: "cliff", label: `Drop-off behind him · ${c.cliffGap.toFixed(1)} ${U}${typ}`,
             t: `<b>${c.cliffGap.toFixed(1)} ${U}</b> of drop-off to the next best ${c.pos}${typ}${ff}.` };
  });
}
function cliffMag(c) {
  if (!c.forces.includes("cliff")) return "";
  const t = num(c.cliffGap)
    ? `Drop-off to the next best ${c.pos} behind him: ${c.cliffGap.toFixed(1)} ${U}${num(c.cliffTypical) ? ` against a typical ${c.pos} gap of ${c.cliffTypical.toFixed(1)}` : ""}. The engine calls any drop past its ${CLIFF_MIN.toFixed(1)}-point noise band material, and a third of the board clears that bar -- read the size, not the mark.`
    : "A positional cliff fired for him but its size was not measured.";
  return `<span class="gap" title="${esc(t)}">◣ ${num(c.cliffGap) ? c.cliffGap.toFixed(0) : absent("The cliff's size was not measured for him.")}</span>`;
}
function rareTicks(c) { return c.forces.filter(f => f !== "cliff").map(f => `<span class="tick" data-force="${f}" title="${forceTitle(f)}">${GLYPH[f]}</span>`).join(""); }
// The plate's chips: only a factor whose fact is NOT already a sentence above (a chip that
// restates a sentence is fluff). Today that is a force that fired without a measurable size.
function plateFactors(c, cands) {
  const order = ["required", "unpriced", "cliff", "block", "tie", "pure", "wait"];
  const fs = earned3(c, 0, cands).filter(e => !e.t).sort((a, b) => order.indexOf(a.k) - order.indexOf(b.k));
  const out = [];
  for (const f of fs) if (out.length < 3 && !out.some(o => o.k === f.k)) out.push(f);
  return out.map(f => `<span class="factor" data-k="${f.k}"><i>${GL[f.k] || "·"}</i>${f.label}</span>`).join("");
}
function factors3(c, i, cands, n) {
  const order = ["required", "unpriced", "cliff", "block", "tie", "pure", "wait"];
  const fs = earned3(c, i, cands).sort((a, b) => order.indexOf(a.k) - order.indexOf(b.k));
  const out = [];
  for (const f of fs) if (out.length < n && !out.some(o => o.k === f.k)) out.push(f);
  const sv = survivalFactor(c); if (out.length < n && sv) out.push(sv);
  return out.slice(0, n).map(f => `<span class="factor" data-k="${f.k}"><i>${GL[f.k] || "·"}</i>${f.label}</span>`).join("");
}
function detail3(c, i, cands) { const rs = earned3(c, i, cands).filter(x => x.t); return `<div class="detail"><div><div class="inner">${rs.map(r => `<p>${r.t}</p>`).join("")}${receipt(c, i)}</div></div></div>`; }
function legend3() {
  return `<div class="legend"><span title="${esc(CT.universal_value.help)}"><b>${U}</b> = ${PAYLOAD.valueUnit} · signed · not fantasy pts</span><span title="The wait chip is the cost of deferring the position until the draft ends, in season-projection points per week, with the floor's basis: measured, estimated, or not measurable."><b>pts/wk</b> = season pts per week to draft end</span><span title="The three rare decision forces, coloured; and the cliff as its size — a third of the board sits at a cliff the engine calls material, so it is drawn as the drop-off behind him in ${U}, at the weight of a detail, never as a coloured mark."><b>⊘ ◆ ≈</b> block · pure · near-tie · <b>◣ n</b> cliff as its size</span><span title="Tiers are contiguous from the top: once the engine's urgency drops a band, no later row rises above it, so row size never contradicts rank.">tiers descend only</span></div>`;
}

// BAND 1. The verdict states the regime AND its inputs. The regime is the engine's; the two
// numbers under it (margin against the noise band, survival against the decisive bar) are the
// engine's own predicates, quoted rather than re-derived.
function verdict3(L, cands) {
  const second = cands.find(c => c.id !== L.id && num(c.tav));
  const margin = num(L.tav) && second ? L.tav - second.tav : null;
  const surv = num(L.survival) ? `<b>${survWord(L)}</b> chance he is still here at your next turn` : "survival to your next turn is not estimable";
  if (!num(L.tav)) return `<b>No price exists for him.</b> He leads for roster legality, not value; ${surv}. Read the reasons before you commit.`;
  if (PAYLOAD.decisionRegime === "exhausted") return `<b>Nothing left can be priced.</b> The ordering below carries no value basis; read the reasons before you commit.`;
  const clear = margin === null ? null
    : `<b>${margin.toFixed(1)} ${U}</b> ${margin >= 0 ? "clear of" : "behind"} ${second.name}, ${Math.abs(margin) > BAND ? "outside" : "inside"} the ${BAND.toFixed(1)}-point noise band`;
  if (PAYLOAD.decisionRegime === "decisive") return `<b>Best-in-class, full stop.</b> ${clear ? clear + "; " : ""}${surv}. Both together are what make this pick decisive rather than a case to argue.`;
  const why = margin !== null && Math.abs(margin) <= BAND ? "the field is inside the noise band, so preference is a legitimate tiebreaker"
    : num(L.survival) && L.survival > DECISIVE_SURV ? "he may well still be here, so the case below has to be made"
    : "the case below has to be made";
  return `<b>Contested.</b> ${clear ? clear + "; " : ""}${surv} — ${why}.`;
}
// The fuller description. Every sentence is about a fact that is PRESENT for this candidate
// and not true of every row; the receipt carries the rest.
function plateProse(L, cands) {
  const s = [];
  if (L.reach_label && L.reach_label !== "WITHIN CONSENSUS BAND" && num(L.consensus_rank))
    s.push(`<b>${titleCase(L.reach_label)}.</b> Consensus ranks him #${L.consensus_rank}${num(L.consensus_tier) ? `, tier ${L.consensus_tier}` : ""}.`);
  const terms = [["need", L.needBonus], ["flexibility", L.eligBonus], ["depth insurance", L.depth_exposure]].filter(([, x]) => num(x) && x > 0);
  if (terms.length && num(L.uv)) s.push(`Your roster adds <b>+${terms.reduce((a, [, x]) => a + x, 0).toFixed(1)} ${U}</b> to his raw ${L.uv.toFixed(1)}: ${terms.map(([k, x]) => `${k} ${x.toFixed(1)}`).join(", ")}.`);
  for (const e of earned3(L, 0, cands)) if (e.t) s.push(e.t);
  return s.slice(0, 4);
}
function plate(L, cands) {
  const rs = plateProse(L, cands);
  return `<div class="row plate decide${cardOpen(L) ? " open" : ""}" ${cardAttrs(L, 0)}>
    <div class="pl">
      <div class="eyebrow">the pick · ${necWord(L)}${num(L.pick_necessity) ? ` ${L.pick_necessity.toFixed(0)}/100` : ""} · regime ${PAYLOAD.decisionRegime}</div>
      <h2 class="display">${L.name} ${pillPos(L)} <span class="team">${L.team}</span>${L.fillsRequiredSlot ? '<span class="required" title="Ranked above higher-scoring candidates because your roster cannot otherwise still be filled legally.">FILLS REQUIRED SLOT</span>' : ""}${fixtureTag(L)}</h2>
      <p class="verdict">${verdict3(L, cands)}</p>
      ${rs.length ? `<div class="why">${rs.map(r => `<p>${r}</p>`).join("")}</div>` : ""}
      ${(f => f ? `<div class="factors">${f}</div>` : "")(plateFactors(L, cands))}
    </div>
    <div class="nums"><span class="big">${num(L.tav) ? `<span data-field="tav"${L.tav < 0 ? ' class="neg"' : ""}>${L.tav.toFixed(0)}</span>` : `<span data-field="tav">${absent(WHY.tav)}</span>`} <span class="unit">${U} acquisition</span></span><span>UV <b>${num(L.uv) ? L.uv.toFixed(0) : absent(WHY.uv)}</b> ${U}</span><span>proj <b>${num(L.proj) ? L.proj.toFixed(0) : absent(WHY.proj)}</b> season pts</span><span>survive <b>${survivalCell(L)}</b></span><span>${waitCell(L)}</span></div>
    ${detail3(L, 0, cands)}
  </div>`;
}
// BAND 2. A card carries the same two facts as H2's (its two named factors, survive, wait);
// R1's extra width goes to measure, not to content, so the 2-vs-3 measurement is about the
// grid and nothing else.
function bandCard(c, i, cands) {
  return `<div class="row card big decide${cardOpen(c) ? " open" : ""}" ${cardAttrs(c, i)}>
    <div class="ch"><span class="rank">${i + 1}</span>${whoHtml(c)}</div>
    <div class="cn">${necWord(c)}<span class="ticks">${rareTicks(c)}</span></div>
    <div class="cv" title="Acquisition value in ${PAYLOAD.valueUnit} — signed, unbounded, not fantasy points">${valueHtml(c)}</div>
    <div class="cf">${factors3(c, i, cands, 2)}</div>
    <div class="cb"><span class="col">survive ${survivalCell(c)}</span><span class="col">${waitCell(c)}</span></div>
    ${detail3(c, i, cands)}
  </div>`;
}
// A row, for the tier's overflow (decide weight), band 3 (context) and the tail.
function bandRow(c, i, t, cands, marks) {
  return `<div class="row ${t}${cardOpen(c) ? " open" : ""}" ${cardAttrs(c, i)}>
    <div class="head eyes">
      <span class="rank">${i + 1}</span>
      ${whoHtml(c)}
      <span class="marks">${marks || ""}</span>
      <span class="ticks">${rareTicks(c)}${cliffMag(c)}</span>
      ${necWord(c)}
      <span class="col">${survivalCell(c)}</span><span class="col">${waitCell(c)}</span>
      <span class="value" title="Acquisition value in ${PAYLOAD.valueUnit} — signed, unbounded, not fantasy points">${valueHtml(c)}</span>
    </div>
    ${detail3(c, i, cands)}
  </div>`;
}
// "Keep an eye on" is a MARK, not a sort. The next man at each position after the tier is
// the first row of that position at or past `start` -- a filter over the engine's order.
function eyeMarks(c, i, start, cands) {
  const m = [];
  const firstAt = cands.findIndex(x => x.pos === c.pos);
  const firstBelow = cands.findIndex((x, k) => k >= start && x.pos === c.pos);
  if (i === firstBelow) m.push(firstAt < start
    ? `<span class="eye" title="The next ${c.pos} after the decision tier, in the engine's order: the best ${c.pos} still available if you pass on the tier.">next ${c.pos}</span>`
    : `<span class="eye" title="The best ${c.pos} on this board; none sits in the decision tier.">top ${c.pos}</span>`);
  if (c.contextGap === "elevated") m.push(`<span class="eye" title="Roster fit lifts his acquisition value well above his universal value.">context ▲</span>`);
  return m.join("");
}
function foldHtml(tail) {
  return `<div class="fold" role="button" tabindex="0" onclick="tailOpen=true;render()" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();tailOpen=true;render()}">${tail.length} low-urgency row${tail.length === 1 ? "" : "s"} folded — values ${valueRange(tail)} · show</div>`;
}
function tierLabel(others, cardN, overflow, cap) {
  if (others === 0) return "the decision tier · the engine holds nobody else live — band three starts here";
  return `the decision tier · ${others} more the engine holds live · ${cardN} as card${cardN === 1 ? "" : "s"}${overflow ? `, ${overflow} as row${overflow === 1 ? "" : "s"}` : ""}${cardN < cap ? ` · the grid holds ${cap}` : ""}`;
}

// THE THREE BANDS. `cap` is the grid's capacity; `lanes` swaps band 3's flat rows for R3's
// position lanes. Band 3 begins exactly where the engine's contiguous tier drops.
function bandsHtml(cands, cap, lanes) {
  const T = tiers(cands);
  const decideN = T.filter(t => t === "decide").length;
  const others = decideN - 1, cardN = Math.min(cap, others), overflow = others - cardN, start = decideN;
  const tail = cands.filter((c, i) => T[i] === "tail");
  const ctxN = cands.length - start - tail.length;
  let out = plate(cands[0], cands);   // the plate's own eyebrow says "the pick"; no band label above it
  out += `<div class="band">${tierLabel(others, cardN, overflow, cap)}</div>`;
  if (cardN) out += `<div class="cards" data-cap="${cap}">${cands.slice(1, 1 + cardN).map((c, k) => bandCard(c, k + 1, cands)).join("")}</div>`;
  for (let i = 1 + cardN; i < start; i++) out += bandRow(cands[i], i, "decide", cands, "");
  out += `<div class="band eyeband">keep an eye on · ${ctxN} below the tier${lanes ? " · by position, each lane in engine order, the overall rank on every row" : " · engine order · the next man at each position is marked"}${tail.length ? ` · ${tail.length} low-urgency ${tailOpen ? "below" : "folded"}` : ""}</div>`;
  if (lanes) out += lanesHtml(cands, start, T);
  else for (let i = start; i < cands.length; i++) if (T[i] === "context") out += bandRow(cands[i], i, "context", cands, eyeMarks(cands[i], i, start, cands));
  if (tail.length) {
    if (!tailOpen) out += foldHtml(tail);
    else { out += `<div class="band sub">tail — low urgency · engine order</div>`; for (let i = start; i < cands.length; i++) if (T[i] === "tail") out += bandRow(cands[i], i, "tail", cands, ""); }
  }
  return out;
}

// R3. Position lanes for the context tier. Lanes are ordered by their first member's engine
// rank; rows inside a lane keep the engine's order and carry the overall rank. The lane
// header states the two POSITIONAL facts every row of a position repeats -- the forfeit for
// skipping the position until your next turn and the draft-end floor with its basis -- once.
function lanesHtml(cands, start, T) {
  const lanes = [];
  for (let i = start; i < cands.length; i++) {
    if (T[i] !== "context") continue;
    let l = lanes.find(x => x.pos === cands[i].pos);
    if (!l) { l = { pos: cands[i].pos, rows: [] }; lanes.push(l); }
    l.rows.push(i);
  }
  return `<div class="lanes">${lanes.map(l => laneHtml(l, cands, start)).join("")}</div>`;
}
function rangeOrOne(vals, d) { const lo = Math.min(...vals), hi = Math.max(...vals); return lo === hi ? lo.toFixed(d) : `${lo.toFixed(d)}–${hi.toFixed(d)}`; }
function laneHtml(l, cands, start) {
  const members = l.rows.map(i => cands[i]), first = members[0];
  const firstAt = cands.findIndex(x => x.pos === l.pos);
  const anyOpen = members.some(c => openId === c.id);
  const ffs = members.map(c => c.positional_forfeit).filter(num);
  const ff = ffs.length ? `<span title="The engine's cost of skipping ${l.pos} until your next turn, in ${PAYLOAD.valueUnit}. Computed per candidate; ${ffs.length === members.length ? (ffs.every(x => x === ffs[0]) ? "identical across this lane" : "a range across this lane") : `carried by ${ffs.length} of this lane's ${members.length}`}.">skip to next turn <b>${rangeOrOne(ffs, 1)}</b> ${U}</span>`
    : `<span>skip to next turn ${absent(WHY.forfeit)}</span>`;
  const withFloor = members.find(c => num(c.horizon_floor)), h = horizon(withFloor || first);
  const fl = withFloor ? `<span title="${esc(h ? h.text : "")}">draft-end floor <b>${withFloor.horizon_floor.toFixed(0)}</b> season pts${h ? ` · ${h.word}` : ""}</span>`
    : `<span title="${esc(h ? h.text : WHY.floor)}">draft-end floor ${absent(h ? h.text : WHY.floor)}</span>`;
  return `<section class="lane${anyOpen ? " open" : ""}" aria-label="${l.pos} below the decision tier">
    <header class="lh"><span class="lt">${pillPos(first)} <b>${firstAt < start ? "next" : "top"} ${l.pos}</b> · ${members.length}</span><span class="lf">${ff}${fl}</span></header>
    ${l.rows.map(i => laneRow(cands[i], i, cands)).join("")}
  </section>`;
}
function laneRow(c, i, cands) {
  return `<div class="row context lrow${cardOpen(c) ? " open" : ""}" ${cardAttrs(c, i)}>
    <div class="head lane-head">
      <span class="rank">${i + 1}</span>
      ${whoHtml(c)}${c.contextGap === "elevated" ? `<span class="eye" title="Roster fit lifts his acquisition value well above his universal value.">context ▲</span>` : ""}
      <span class="ticks">${rareTicks(c)}${cliffMag(c)}</span>
      ${necWord(c)}
      <span class="col">${survivalCell(c)}</span>
      <span class="value" title="Acquisition value in ${PAYLOAD.valueUnit} — signed, unbounded, not fantasy points">${valueHtml(c)}</span>
    </div>
    ${detail3(c, i, cands)}
  </div>`;
}
"""

R_CSS = SPINE_CSS + MATERIAL_CSS + S1_CSS + r"""
/* No gold on engine state: the material's gold-tinted top edge would mark the decide tier
   (only cards carry it), so cards take the plain line. Gold stays on the open row (user
   state) and the clock bar (chrome). */
.row.card, .row.plate { border-top-color: var(--line-2); }
/* Band 1: the plate is a row. */
.row.plate { display: grid; grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: "pl nums" "cd cd"; gap: .5rem 1.4rem; padding: .65rem 1.2rem .7rem; margin-top: .3rem; border: 1px solid var(--line-2); border-radius: 12px; margin-bottom: .2rem; }
.row.plate .pl { grid-area: pl; min-width: 0; }
.row.plate .nums { grid-area: nums; }
.row.plate .detail { grid-area: cd; }
.row.plate .eyebrow .nec { font-size: .74rem; }
.row.plate .verdict { font-size: .96rem; max-width: 92ch; margin: 0 0 .35rem; }
.row.plate .why { font-size: .9rem; max-width: 96ch; color: var(--ink); margin: 0; }
.row.plate .factors { margin-top: .45rem; }
.row.plate h2 { margin: .05rem 0 .2rem; font-size: 1.55rem; }
.row.plate .why p { margin: 0 0 .15rem; }
.row.plate .nums .big { display: flex; align-items: baseline; gap: .4rem; justify-content: flex-end; }
.row.plate .nums .big > span:first-child { font-size: 2.2rem; line-height: 1; font-weight: 700; color: var(--ink); }
.row.plate .nums .unit { font-size: .64rem; }
.row.plate .nums .chip { font-size: .64rem; }
/* Band 2: the card grid. data-cap is the CAPACITY the grid states, never the count shown. */
.cards { display: grid; gap: .35rem; margin-bottom: .25rem; }
.row.card .factor { border: 0; background: transparent; padding: .04rem 0; }
.cards[data-cap="4"] { grid-template-columns: repeat(2, 1fr); }
.cards[data-cap="6"] { grid-template-columns: repeat(3, 1fr); }
.row.card.big { display: grid; grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: "ch cv" "cn cv" "cf cf" "cb cb" "cd cd"; column-gap: .6rem; row-gap: .22rem; padding: .55rem .85rem; align-items: start; }
.row.card.big.open { grid-column: 1 / -1; }
.row.card.big .ch { grid-area: ch; display: flex; align-items: baseline; gap: .45rem; flex-wrap: wrap; min-width: 0; }
.row.card.big .ch .name { font-size: 1.05rem; font-weight: 700; }
.row.card.big .cn { grid-area: cn; display: flex; align-items: center; gap: .5rem; }
.row.card.big .cv { grid-area: cv; font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 1.9rem; line-height: 1; text-align: right; font-variant-numeric: tabular-nums; }
.row.card.big .cv .unit { display: block; font-size: .56rem; margin: .15rem 0 0; }
.row.card.big .cf { grid-area: cf; display: flex; flex-direction: column; gap: .1rem; min-height: 1.6rem; }
.row.card.big .cb { grid-area: cb; display: flex; gap: .6rem; align-items: center; border-top: 1px dashed var(--line-2); padding-top: .3rem; }
.row.card.big .detail { grid-area: cd; }
/* Rows: the spine's grid with a marks column. */
.head.eyes { grid-template-columns: 2rem minmax(0, 1fr) auto 5.4rem 8.6rem 4rem 9.6rem 6.2rem; }
.marks { display: flex; gap: .3rem; flex-wrap: wrap; }
.eye { font-family: "JetBrains Mono", monospace; font-size: .62rem; letter-spacing: .05em; text-transform: uppercase; color: var(--muted); border: 1px solid var(--line-2); border-radius: 3px; padding: .05rem .35rem; cursor: help; white-space: nowrap; }
.band.eyeband { margin-top: .3rem; color: var(--ink); }
.legend { gap: .8rem; letter-spacing: .02em; }
.row.decide:not(.card):not(.plate) { padding: .4rem 1rem; }
.band.sub { padding-top: .35rem; }
/* THE CLIFF IS A NUMBER (#175): its size in muted mono, no force colour, no box. */
.gap { font-family: "JetBrains Mono", monospace; font-size: .74rem; color: var(--muted); cursor: help; white-space: nowrap; font-variant-numeric: tabular-nums; }
.gap .absent { padding: 0 .2em; }
.factor[data-k="cliff"] i { color: var(--muted); }
/* R3: position lanes for band 3. */
.lanes { display: grid; grid-template-columns: 1fr 1fr; gap: .5rem; align-items: start; }
.lane { display: flex; flex-direction: column; gap: .2rem; border: 1px solid var(--line); border-radius: 10px; padding: .45rem .5rem .5rem; background: color-mix(in srgb, var(--surface-2) 60%, transparent); }
.lane.open { grid-column: 1 / -1; }
.lh { display: flex; justify-content: space-between; align-items: baseline; gap: .6rem; flex-wrap: wrap; padding: 0 .4rem .3rem; border-bottom: 1px solid var(--line-2); margin-bottom: .15rem; }
.lt { font-family: "JetBrains Mono", monospace; font-size: .7rem; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); display: flex; gap: .4rem; align-items: baseline; }
.lt b { color: var(--ink); }
.lf { font-family: "JetBrains Mono", monospace; font-size: .66rem; color: var(--muted); display: flex; gap: .9rem; flex-wrap: wrap; }
.lf b { color: var(--ink); }
.lf span { cursor: help; }
.head.lane-head { grid-template-columns: 1.6rem minmax(0, 1fr) 3.6rem 6.8rem 2.8rem 4.4rem; gap: .4rem; }
.row.lrow .name { white-space: nowrap; }
.row.lrow { padding: .4rem .6rem; }
.row.lrow .name { font-size: .92rem; font-weight: 600; }
.row.lrow .value { font-size: 1.1rem; }
.row.lrow .nec { font-size: .7rem; }
.row.lrow .col { font-size: .76rem; }
.lane .fold { grid-column: auto; }
"""

R_BODY = H1_BODY


def r_js(cap: int, lanes: bool) -> str:
    return BAND_JS + f"""
function render() {{
  document.getElementById("clock").innerHTML = clockBar();
  document.getElementById("legend").innerHTML = legend3();
  document.getElementById("board").innerHTML = bandsHtml(candidates, {cap}, {"true" if lanes else "false"});
  wireBoard();
}}
"""


SHARED_ASSERTS = ("Band 2 is DERIVED from the engine's contiguous decide tier and the grid is a cap, not a count: on this real board "
                  "the tier holds seven more after the leader, so the label reads how many are cards and how many continue as "
                  "full-weight rows. The plate's description is fuller and still earned: the verdict quotes the two engine inputs "
                  "that make the regime (margin against the noise band, survival against the decisive bar), then at most four "
                  "sentences about facts present for HIM — the consensus reach, the roster terms that lift his price, the forces with "
                  "their sizes. The cliff is drawn as its size, never as a coloured mark.")

VARIANTS = [
    ("synthesis_r1_2across", "R1 · Three bands, 2 across", "plate · decide tier as cards two across (cap 4) · rows below in engine order, the next man at each position marked",
     "Two across gives each card a comfortable measure — the same two named factors as R2, unwrapped. " + SHARED_ASSERTS +
     " Band 3 is strict engine order; 'keep an eye on' is a mark (next QB / next RB …, context ▲), never a re-sort.",
     "Four cards is the smallest band 2: on this board three decision-tier candidates render as rows, so the seam sits inside the tier, "
     "and fewer candidates clear the 1,400px line than R2. The plate spends ~230px of the fold on one candidate.",
     R_CSS, R_BODY, r_js(4, False)),
    ("synthesis_r2_3across", "R2 · Three bands, 3 across", "plate · decide tier as cards three across (cap 6) · rows below in engine order, the next man at each position marked",
     "Three across covers six of the tier's seven before the seam, with the same card content as R1 so the measurement is about the grid alone. " + SHARED_ASSERTS,
     "Narrower cards wrap a long factor label; the 1.9rem numeral crowds a long name at 1,400px and stacks on a phone. A tier of two "
     "leaves the third column empty rather than asserting a third live candidate.",
     R_CSS, R_BODY, r_js(6, False)),
    ("synthesis_r3_lanes", "R3 · Three bands, position lanes", "the swing on ordering: band 3 as position lanes, each in engine order, the overall rank on every row",
     "'The ones to keep eyes on' is a positional question in a draft — who is the next man at each position and what does the position "
     "cost to skip — so band 3 answers it structurally: one lane per position, ordered by the lane's first member's engine rank, rows "
     "inside a lane in engine order with the overall rank shown, and the lane header stating once the two facts every row of a position "
     "repeats (the forfeit for skipping it until your next turn; the draft-end floor with its basis). No sort key of this page's own: it "
     "is the app's position view laid side by side. Bands 1 and 2 are R2's, so the density delta against R2 is the lanes' alone.",
     "It is a lens, not the engine's list, and the eye must read the rank numerals to recover the overall order across lanes — the G6 "
     "question is put to the owner on the page rather than settled here. Lanes of unequal length leave air under the short ones. An "
     "open lane row widens its lane to the full width so the receipt fits.",
     R_CSS, R_BODY, r_js(6, True)),
]
