"""Three docks, three different answers to "what is the unit?"

  D1 LEDGER   the unit is the DECISION. Collapsed is the standing call as one line (what the
              Moderator last decided, with what conviction, to which question, on how many
              chairs, how long ago). Partial is that call's receipt beside the ask panel and
              nothing else -- no transcript. Full adds the ledger: one row per decision or
              exchange, newest first, opening to the three reports and the follow-ups.
  D2 THREAD   the unit is the EXCHANGE (a question and its answer). Collapsed is the newest
              exchange as one line -- if the newest answer is a block-less follow-up, it says so
              and marks the call that still stands. Partial is the newest exchange above the ask
              box (which sits at the bottom, where a conversation's input belongs), with the
              three reports one tab-press away. Full is the whole thread, oldest to newest, the
              input pinned under it.
  D3 CHAIRS   the unit is the CHAIR. Collapsed is the panel's four seats and their state for the
              current debate -- reported, no report, and the Moderator's word. Partial is four
              columns, one per seat, each scrolling on its own, with a scrubber to move between
              debates. Full is the same four columns with room for the whole report, the
              follow-ups under the Moderator, and the session strip.

EVERY variant obeys the same fixes over the baseline (dock_common): the standing verdict is the
newest block-bearing Moderator message; a failed chair is an absence with a title; markdown is
rendered once, uniformly; the recommendation is a word, never a colour; conviction is a glyph
ladder that takes the one signal hue (amber) below Majority; gold is the primary button and
the focus ring only.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------------------
# D1 LEDGER
# ---------------------------------------------------------------------------------------
LEDGER_CSS = r"""
.bar { display: flex; align-items: center; gap: .7rem; min-height: 2.2rem; flex-wrap: nowrap; min-width: 0; }
.bar .grow { flex: 1; }
.bar .eyebrow, .bar .mark, .bar .conv, .bar .btn { flex: none; white-space: nowrap; }
.bar .mark.on { flex: 0 1 auto; min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.bar .q { font-size: .86rem; color: var(--muted); min-width: 18ch; flex: 1 1 auto; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar .q b { color: var(--ink); font-weight: 500; }
.bar .rec { font-size: .95rem; }
.bar .grow { flex: 0 0 .5rem; }
.dh { display: flex; align-items: center; gap: .8rem; flex: none; }
.dh .grow { flex: 1; }
.body2 { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); gap: 1.2rem; flex: 0 1 auto; min-height: 0; }
.body2 > * { min-height: 0; }
.verdict { border: 1px solid var(--line-2); border-radius: 10px; padding: .55rem .85rem .65rem; background: color-mix(in srgb, var(--surface) 80%, transparent); min-width: 0; overflow-y: auto; }
.verdict .top { display: flex; align-items: baseline; gap: .7rem; flex-wrap: wrap; margin: .15rem 0 .35rem; }
.verdict .rec { font-size: 1.5rem; line-height: 1; }
.verdict .conv { font-size: .8rem; }
.verdict .asked { font-size: .82rem; color: var(--muted); margin-bottom: .35rem; }
.verdict .asked b { color: var(--ink); font-weight: 500; }
.ask { display: flex; flex-direction: column; gap: .4rem; min-width: 0; }
.ask .chips { display: flex; gap: .4rem; flex-wrap: wrap; align-items: center; }
.ask textarea { height: 5.4rem; }
.ask .btns { display: flex; gap: .4rem; flex-wrap: wrap; }
.ask .hint { font-size: .72rem; color: var(--dim); }
.ledger { border: 1px solid var(--line); border-radius: 10px; flex: 1 1 auto; display: flex; flex-direction: column; min-height: 0; }
html[data-level="full"] .ledger { min-height: 14rem; }
.ledger .lh { display: flex; gap: .8rem; align-items: baseline; padding: .4rem .8rem; border-bottom: 1px solid var(--line-2); flex: none; }
.ledger .rows { overflow-y: auto; min-height: 0; }
.lrow { border-bottom: 1px solid var(--line); }
.lrow:last-child { border-bottom: 0; }
.lrow .head { display: grid; grid-template-columns: 4.2rem 1.2rem minmax(0, 1fr) 5.2rem 9.4rem 5.4rem auto; gap: .6rem; align-items: center; padding: .38rem .8rem; }
.lrow .head .q { font-size: .86rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lrow .head .q b { font-weight: 500; }
.lrow .head .rec { font-size: .8rem; }
.lrow .head .conv { font-size: .7rem; }
.lrow .kg { font-family: "JetBrains Mono", monospace; color: var(--muted); text-align: center; cursor: help; }
.lrow[aria-expanded="true"] { background: color-mix(in srgb, var(--surface) 70%, transparent); box-shadow: inset 3px 0 0 var(--gold); }
.lrow .detail { padding: .2rem .8rem .7rem 6.6rem; display: grid; gap: .55rem; }
.reports { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .5rem; }
.report { border: 1px solid var(--line-2); border-radius: 8px; padding: .45rem .65rem; min-width: 0; }
.report .rh { display: flex; gap: .45rem; align-items: center; margin-bottom: .3rem; }
.report .rh .who { font-family: "JetBrains Mono", monospace; font-size: .7rem; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); }
.report .prose { font-size: .82rem; }
.mod { border-left: 2px solid var(--crimson); padding-left: .7rem; }
.marks { display: inline-flex; gap: .3rem; }
"""

LEDGER_JS = r"""
function kindGlyph(u) {
  return { debate: ["●", "A Full Prytaneum run: three chairs, then the Moderator's verdict."], followup: ["↳", "A follow-up: the Moderator alone, on the same reports."],
           summary: ["▤", "A memory summary: older turns compacted into one block."], notice: ["!", "A system notice."], user: ["·", "A question with no answer recorded."],
           quant: ["Q", "The Quant alone."], beat: ["B", "The Beat Tracker alone."] }[u.kind] || ["·", u.kind];
}
function standingLine(S, V) {
  if (!S) return `<span class="q">No call stands yet — ask the panel.</span>`;
  return `${recHtml(V.fields)}${convHtml(V.fields)}<span class="q" data-fact="question">to <b>${trunc(questionOf(S) || "a question not recorded", 72)}</b></span>${reachedHtml(S)}${ago(S.ts)}`;
}
function askPanel(us) {
  const hasDebate = us.some(u => u.kind === "debate");
  return `<section class="ask" aria-label="ask the panel">
    <div class="chips">${considering()}<span class="mark" title="Open objectives; the panel reads them as standing context.">${openObjectives()} objectives open</span></div>
    <textarea class="ask" placeholder="${hasDebate ? "Continue with the Moderator, or /debate for a fresh full panel run (/quant, /beat route explicitly)" : "Ask about a start/sit, trade, or waiver decision (/debate, /quant, /beat route explicitly)"}"></textarea>
    <div class="btns"><button class="btn primary">${hasDebate ? "Ask the Moderator" : "Ask the panel"}</button><button class="btn quiet">Full Prytaneum</button><button class="btn quiet">Ask Quant</button><button class="btn quiet">Ask Beat Tracker</button><button class="btn icon quiet" title="Attach a file to this chat (this session only)">+</button></div>
  </section>`;
}
function verdictPanel(S, V) {
  if (!S) return `<section class="verdict"><div class="eyebrow">standing call</div><p class="asked">Nothing decided yet in this league's chat.</p></section>`;
  return `<section class="verdict scroll" aria-label="standing call">
    <div class="eyebrow">standing call · ${S.kind === "debate" ? "full panel" : "re-issued in a follow-up"} · ${ago(S.ts)} ${reachedHtml(S)} ${seatsHtml(S, true)}</div>
    <div class="top">${recHtml(V.fields)}${convHtml(V.fields, true)}</div>
    <div class="asked">to <b>${trunc(questionOf(S) || "a question not recorded", 150)}</b></div>
    ${receiptHtml(V, { extraChars: 110 })}
  </section>`;
}
function reportCard(c) {
  const name = PAYLOAD.roleNames[c.role];
  if (c.status === "failed") return `<div class="report absent-report" data-field="report" data-role="${c.role}"><b>${esc(name)}</b> · <span class="absent" title="${esc(failText(c.msg))}">no report reached the panel</span><br>Whether the call never ran, ran and was lost, or ran and could not be read is not known here. Missing information, never a finding.</div>`;
  return `<div class="report" data-field="report" data-role="${c.role}"><div class="rh">${seatHtml(c)}<span class="who">${esc(name)} · ${modelOf(c.msg)}</span></div><div class="prose">${md(c.msg.content)}</div></div>`;
}
function ledgerRow(u, i) {
  const g = kindGlyph(u), id = uid(u), open = openId === id;
  let mid = "", rec = "", conv = "", seats = "", marks = "";
  if (u.kind === "debate" || u.kind === "followup") {
    const V = parseVerdict(u.moderator.content);
    mid = `<span class="q"><b>${trunc(questionOf(u) || "(no question recorded)", 90)}</b>${u.kind === "followup" && !V.has ? ` <span class="mark" title="The Moderator talked it through and did not re-issue the block; the earlier call stands.">no new call</span>` : ""}</span>`;
    rec = V.has ? recHtml(V.fields) : `<span class="rec" style="color:var(--muted);font-weight:500">—</span>`;
    conv = V.has ? convHtml(V.fields) : "";
    seats = seatsHtml(u, true);
    marks = `<span class="marks">${pinned(u.moderator) ? '<span class="mark on" title="Pinned: kept easy to find in the Pinned Messages panel.">◉ pinned</span>' : ""}${V.fields.action_item && objectiveFor(V.fields.action_item) ? `<span class="mark on" title="This verdict's ACTION ITEM is tracked as objective #${objectiveFor(V.fields.action_item).id}.">→ #${objectiveFor(V.fields.action_item).id}</span>` : ""}</span>`;
  } else {
    mid = `<span class="q" style="color:var(--muted)">${trunc(u.msg.content, 110)}</span>`;
  }
  let detail = "";
  if (open) {
    if (u.kind === "debate") {
      const V = parseVerdict(u.moderator.content);
      detail = `<div class="detail"><div class="reports">${chairs(u).map(reportCard).join("")}</div>
        <div class="mod"><div class="rh eyebrow" style="margin-bottom:.3rem">Moderator · ${modelOf(u.moderator)} · ${ago(u.moderator.ts)}</div><div class="prose">${md(V.prose)}</div><div style="margin-top:.4rem">${receiptHtml(V)}</div></div></div>`;
    } else if (u.kind === "followup") {
      const V = parseVerdict(u.moderator.content);
      detail = `<div class="detail"><div class="mod"><div class="rh eyebrow" style="margin-bottom:.3rem">Moderator · ${modelOf(u.moderator)} · ${ago(u.moderator.ts)} · on the previous run's reports</div><div class="prose">${md(V.prose)}</div>${V.has ? `<div style="margin-top:.4rem">${receiptHtml(V)}</div>` : ""}</div></div>`;
    } else detail = `<div class="detail"><div class="prose">${md(u.msg.content)}</div></div>`;
  }
  return `<div class="lrow" ${optAttrs(u, i)}><div class="head">${ago(u.ts)}<span class="kg" title="${esc(g[1])}">${g[0]}</span>${mid}${rec}${conv}${seats}${marks}</div>${detail}</div>`;
}
function render() {
  const us = units(hist()), S = standing(us), V = S ? parseVerdict(S.moderator.content) : null, dock = document.getElementById("dock");
  if (level === "collapsed") {
    dock.innerHTML = `<div class="bar">${levelBtns()}<span class="eyebrow">standing call</span>${standingLine(S, V)}<span class="grow"></span>${considering()}<button class="btn primary" onclick="setLevel('partial')">Ask</button></div>`;
    return;
  }
  let html = `<header class="dh"><span class="wordmark">The Prytaneum</span><span class="eyebrow">Gold Wyrm Dynasty · ${us.length} entries · now is ${new Date(NOW * 1000).toISOString().slice(0, 16).replace("T", " ")} UTC</span><span class="grow"></span>${levelBtns()}</header>
    <div class="body2">${verdictPanel(S, V)}${askPanel(us)}</div>`;
  if (level === "full") {
    const rows = us.slice().reverse();
    html += `<div class="ledger"><div class="lh"><span class="eyebrow"><b>ledger</b> · every decision and exchange in this league's chat · newest first · ${rows.filter(u => u.kind === "debate").length} full runs, ${rows.filter(u => u.kind === "followup").length} follow-ups</span><span class="eyebrow">open a row for the three reports</span></div><div class="rows scroll" role="listbox" aria-label="ledger">${rows.map(ledgerRow).join("")}</div></div>`;
  }
  dock.innerHTML = html;
  wire(dock);
}
"""

# ---------------------------------------------------------------------------------------
# D2 THREAD
# ---------------------------------------------------------------------------------------
THREAD_CSS = r"""
.bar { display: flex; align-items: center; gap: .7rem; min-height: 2.2rem; min-width: 0; }
.bar .grow { flex: 1; }
.bar .x { font-size: .86rem; color: var(--muted); min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1 1 0; }
.bar .x[data-fact="question"] { flex: 0 1 auto; min-width: 22ch; }
.bar .x b { color: var(--ink); font-weight: 500; }
.bar .rec { font-size: .9rem; flex: none; }
.bar .seats, .bar .mark, .bar .btn, .bar .age { flex: none; }
.th { display: flex; align-items: center; gap: .8rem; flex: none; }
.th .grow { flex: 1; }
.thread { display: flex; flex-direction: column; gap: .5rem; flex: 1 1 auto; min-height: 0; padding-right: .3rem; }
.sys { text-align: center; font-family: "JetBrains Mono", monospace; font-size: .7rem; color: var(--muted); padding: .1rem 0; cursor: help; }
.sys .absent { font-size: .7rem; }
.sys[aria-expanded="true"] { text-align: left; }
.sys[aria-expanded="true"] .prose { text-align: left; margin-top: .3rem; font-size: .8rem; color: var(--muted); }
.you { display: flex; gap: .5rem; align-items: baseline; font-size: .88rem; color: var(--ink); padding: .1rem 0 0; }
.you .seat { vertical-align: middle; }
.msg { border: 1px solid var(--line-2); border-radius: 10px; padding: .5rem .8rem .6rem; box-shadow: inset 3px 0 0 var(--rail, var(--line-2)); background: color-mix(in srgb, var(--surface) 80%, transparent); }
.msg[aria-expanded="true"] { border-color: var(--line-2); box-shadow: inset 3px 0 0 var(--rail, var(--line-2)), 0 0 0 1px var(--gold); }
.msg .mh { display: flex; gap: .5rem; align-items: center; flex-wrap: wrap; margin-bottom: .3rem; }
.msg .mh .who { font-family: "JetBrains Mono", monospace; font-size: .7rem; letter-spacing: .06em; text-transform: uppercase; color: var(--ink); }
.msg .mh .grow { flex: 1; }
.msg .call { display: flex; gap: .7rem; align-items: baseline; flex-wrap: wrap; margin: .3rem 0 .3rem; }
.msg .call .rec { font-size: 1.05rem; }
.msg .receipt { margin-top: .25rem; }
.tabs2 { display: flex; gap: 0; margin-top: .45rem; border-top: 1px dashed var(--line-2); padding-top: .35rem; align-items: stretch; }
.tab { background: transparent; border: 0; border-bottom: 2px solid transparent; color: var(--muted); font-family: "JetBrains Mono", monospace; font-size: .7rem; letter-spacing: .05em; text-transform: uppercase; padding: .25rem .6rem; cursor: pointer; display: inline-flex; gap: .4rem; align-items: center; }
.tab:hover { color: var(--ink); }
.tab .absent { font-size: .7rem; }
.tabpane { margin-top: .4rem; padding: .45rem .7rem; border: 1px solid var(--line-2); border-radius: 8px; }
.tabpane .prose { font-size: .83rem; }
.askrow { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: .5rem 1rem; align-items: end; flex: none; border-top: 1px solid var(--line); padding-top: .5rem; }
.askrow .chips { grid-column: 1 / -1; display: flex; gap: .4rem; flex-wrap: wrap; align-items: center; }
.askrow textarea { height: 2.6rem; }
.askrow .btns { display: flex; gap: .4rem; }
html[data-level="partial"] .prose.clamp { -webkit-line-clamp: 5; }
"""

THREAD_JS = r"""
function askRow(us) {
  const hasDebate = us.some(u => u.kind === "debate");
  return `<div class="askrow"><div class="chips">${considering()}<span class="eyebrow">plain text continues with the Moderator · /debate reconvenes the panel · /quant, /beat route explicitly</span></div>
    <textarea class="ask" placeholder="${hasDebate ? "Continue the conversation with the Moderator…" : "Ask about a start/sit, trade, or waiver decision…"}"></textarea>
    <div class="btns"><button class="btn primary">Ask</button><button class="btn quiet">Full Prytaneum</button><button class="btn quiet">Quant</button><button class="btn quiet">Beat</button><button class="btn icon quiet" title="Attach a file to this chat (this session only)">+</button></div></div>`;
}
function youLine(u) { return u.question ? `<div class="you"><span class="seat" data-role="user" title="You">Y</span><span>${esc(u.question.content)}</span>${ago(u.question.ts)}</div>` : ""; }
function tabsHtml(u) {
  const id = uid(u), cs = chairs(u), sel = tabOf[id];
  const tabs = cs.map(c => {
    const name = PAYLOAD.roleNames[c.role];
    const lab = c.status === "failed" ? `${esc(name)} · <span class="absent" title="${esc(failText(c.msg))}">no report</span>` : `${esc(name)} · ${c.msg.content.length.toLocaleString()} chars`;
    return `<button class="tab" role="tab" data-role="${c.role}" aria-selected="${sel === c.role}" onclick="setTab('${id}','${c.role}')" title="${esc(c.status === "failed" ? "No report reached the panel from this chair. Missing information, never a finding." : `${name} · ${ROLE_JOB[c.role]} · ${c.msg.model || "model not recorded"}`)}">${seatHtml(c)}${lab}</button>`;
  }).join("");
  let pane = "";
  if (sel) {
    const c = cs.find(x => x.role === sel);
    pane = c.status === "failed" ? `<div class="tabpane absent-report" data-field="report" data-role="${c.role}"><b>${esc(PAYLOAD.roleNames[c.role])}</b> · <span class="absent" title="${esc(failText(c.msg))}">no report reached the panel</span> — whether the call never ran, ran and was lost, or ran and could not be read is not known here. The Moderator's verdict above rests on the other two.</div>`
      : `<div class="tabpane" data-field="report" data-role="${c.role}"><div class="eyebrow" style="margin-bottom:.3rem">${esc(PAYLOAD.roleNames[c.role])} · ${modelOf(c.msg)} · ${ago(c.msg.ts)}</div><div class="prose">${md(c.msg.content)}</div></div>`;
  }
  return `<div class="tabs2" role="tablist" aria-label="the reports behind this verdict"><span class="eyebrow" style="align-self:center;margin-right:.4rem">reports</span>${tabs}<span class="grow"></span>${reachedHtml(u)}</div>${pane}`;
}
function modMsg(u, i, isNewest) {
  const V = parseVerdict(u.moderator.content), id = uid(u), open = openId === id, isDebate = u.kind === "debate";
  const clamp = level === "partial" && !open;
  const who = isDebate ? "Moderator verdict" : "Moderator";
  const marks = `${pinned(u.moderator) ? '<span class="mark on" title="Pinned: kept easy to find in the Pinned Messages panel.">◉ pinned</span>' : ""}${V.fields.action_item && objectiveFor(V.fields.action_item) ? `<span class="mark on" title="This verdict's ACTION ITEM is tracked as objective #${objectiveFor(V.fields.action_item).id}.">→ objective #${objectiveFor(V.fields.action_item).id}</span>` : ""}`;
  const call = V.has ? `<div class="call">${recHtml(V.fields)}${convHtml(V.fields, true)}${isDebate ? seatsHtml(u, false) : ""}</div>` : (isDebate ? "" : `<div class="call"><span class="mark" title="A conversational follow-up: the Moderator talked it through and did not re-issue the block. The earlier call stands.">no new call · the earlier verdict stands</span></div>`);
  const receipt = V.has ? (clamp ? `<div class="receipt"><span class="k">reason</span><span class="v" data-field="reason">${esc(V.fields.reason || "")}</span></div>` : receiptHtml(V)) : "";
  return `${youLine(u)}<div class="msg" data-role="moderator" ${optAttrs(u, i)}>
    <div class="mh"><span class="seat" data-role="moderator" title="Moderator · ${esc(ROLE_JOB.moderator)}">M</span><span class="who">${who}</span><span class="eyebrow">${modelOf(u.moderator)}${isDebate ? "" : " · on the previous run's reports"}</span>${marks}<span class="grow"></span>${ago(u.moderator.ts)}</div>
    <div class="prose${clamp ? " clamp" : ""}">${md(V.prose)}</div>${call}${receipt}
    ${isDebate ? tabsHtml(u) : ""}${clamp ? `<div class="fold" style="margin-top:.35rem">open · the full reply and the receipt</div>` : ""}
  </div>`;
}
function sysLine(u, i) {
  const open = openId === uid(u), isNotice = u.kind === "notice";
  const glyph = isNotice ? `<span class="attn">!</span> ` : "▤ ";
  return `<div class="sys" ${optAttrs(u, i)} title="${esc(u.msg.content)}">${glyph}${isNotice ? "notice" : "memory summary"} · ${open ? "" : trunc(u.msg.content, 96)} ${ago(u.ts)}${open ? `<div class="prose">${md(u.msg.content)}</div>` : ""}</div>`;
}
function render() {
  const us = units(hist()), S = standing(us), dock = document.getElementById("dock");
  const newest = us.slice().reverse().find(u => u.moderator);
  if (level === "collapsed") {
    let line = `<span class="x">Nothing asked yet.</span>`;
    if (newest) {
      const V = parseVerdict(newest.moderator.content);
      const ans = V.has ? `${recHtml(V.fields)} <span class="x" data-fact="reason">— ${trunc(V.fields.reason || V.prose, 96)}</span>` : `<span class="x" data-fact="reply">Moderator: ${trunc(V.prose, 96)}</span>`;
      const stand = !V.has && S ? `<span class="mark" title="The newest reply talked it through without a new call; this is the call that still stands, from ${new Date(S.ts * 1000).toISOString().slice(0, 16).replace("T", " ")} UTC.">stands: ${esc(parseVerdict(S.moderator.content).fields.recommendation)}</span>` : "";
      line = `${seatsHtml(newest, true)}<span class="x" data-fact="question"><b>${trunc(questionOf(newest) || "(no question recorded)", 64)}</b></span><span class="mono" style="color:var(--dim)">→</span>${ans}${stand}${ago(newest.ts)}`;
    }
    dock.innerHTML = `<div class="bar">${levelBtns()}${line}<span class="grow"></span><button class="btn primary" onclick="setLevel('partial')">Ask</button></div>`;
    return;
  }
  let html = `<header class="th"><span class="wordmark">The Prytaneum</span><span class="eyebrow">Gold Wyrm Dynasty · ${level === "partial" ? "newest exchange" : `the whole thread · ${us.length} entries`} · now is ${new Date(NOW * 1000).toISOString().slice(0, 16).replace("T", " ")} UTC</span><span class="grow"></span>${S && S !== newest ? `<span class="mark on" title="The call that stands, re-read from the newest block-bearing verdict.">stands: ${esc(parseVerdict(S.moderator.content).fields.recommendation)} · ${parseVerdict(S.moderator.content).fields.conviction.toLowerCase()}</span>` : ""}${levelBtns()}</header>`;
  const shown = level === "partial" ? (newest ? [newest] : []) : us;
  html += `<div class="thread scroll" role="listbox" aria-label="thread">${shown.map((u, i) => u.moderator ? modMsg(u, i, u === newest) : (u.kind === "user" ? `<div class="you" ${optAttrs(u, i)}><span class="seat" data-role="user">Y</span><span>${esc(u.msg.content)}</span>${ago(u.ts)}</div>` : sysLine(u, i))).join("")}</div>`;
  html += askRow(us);
  dock.innerHTML = html;
  wire(dock);
  if (level === "full") { const t = dock.querySelector(".thread"); t.scrollTop = t.scrollHeight; }
}
"""

# ---------------------------------------------------------------------------------------
# D3 CHAIRS
# ---------------------------------------------------------------------------------------
CHAIRS_CSS = r"""
.bar { display: flex; align-items: center; gap: .6rem; min-height: 2.2rem; min-width: 0; }
.bar .grow { flex: 1; }
.cell { display: inline-flex; align-items: center; gap: .4rem; border: 1px solid var(--line-2); border-radius: 6px; padding: .18rem .5rem .18rem .3rem; font-size: .78rem; color: var(--ink); white-space: nowrap; flex: none; }
.bar .eyebrow, .bar .mark, .bar .btn, .bar .age { flex: none; white-space: nowrap; }
.cell .st { font-family: "JetBrains Mono", monospace; font-size: .7rem; color: var(--muted); }
.cell .rec { font-size: .8rem; }
.cell .absent { font-size: .72rem; }
.bar .x { font-size: .84rem; color: var(--muted); min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar .x b { color: var(--ink); font-weight: 500; }
.ch { display: flex; align-items: center; gap: .8rem; flex: none; }
.ch .grow { flex: 1; }
.scrub { display: inline-flex; align-items: center; gap: .5rem; font-size: .84rem; color: var(--ink); min-width: 0; }
.scrub .q { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 48ch; }
.scrub .btn.icon { padding: .15rem .45rem; }
.cols { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1.55fr); gap: .55rem; flex: 1 1 auto; min-height: 0; }
.col { border: 1px solid var(--line-2); border-radius: 10px; display: flex; flex-direction: column; min-height: 0; min-width: 0; background: color-mix(in srgb, var(--surface) 75%, transparent); box-shadow: inset 0 2px 0 var(--rail, var(--line-2)); }
.col[aria-expanded="true"] { box-shadow: inset 0 2px 0 var(--rail, var(--line-2)), 0 0 0 1px var(--gold); }
.col .head { display: flex; gap: .45rem; align-items: center; padding: .45rem .6rem .35rem; border-bottom: 1px solid var(--line); flex: none; flex-wrap: wrap; }
.col .head .who { font-family: "JetBrains Mono", monospace; font-size: .7rem; letter-spacing: .06em; text-transform: uppercase; color: var(--ink); }
.col .head .eyebrow { font-size: .7rem; }
.col .body { padding: .45rem .6rem .5rem; overflow-y: auto; min-height: 0; }
.col .prose { font-size: .8rem; line-height: 1.45; }
.col .call { display: flex; gap: .6rem; align-items: baseline; flex-wrap: wrap; margin-bottom: .35rem; }
.col .call .rec { font-size: 1.25rem; line-height: 1; }
.col .receipt { font-size: .78rem; margin-bottom: .45rem; grid-template-columns: minmax(0, 1fr); gap: 0 0; }
.col .receipt .k { margin-top: .3rem; }
.col .receipt .k:first-child { margin-top: 0; }
.col .fu { border-top: 1px dashed var(--line-2); margin-top: .5rem; padding-top: .4rem; }
.col .fu .you { font-size: .8rem; color: var(--muted); margin-bottom: .2rem; }
.col .fu .you b { color: var(--ink); font-weight: 500; }
.col .absent-report { margin: 0; }
.strip { display: flex; gap: .4rem; align-items: center; flex-wrap: wrap; flex: none; }
.strip .sess { font-family: "JetBrains Mono", monospace; font-size: .7rem; color: var(--muted); border: 1px solid var(--line-2); border-radius: 5px; padding: .18rem .5rem; cursor: pointer; background: transparent; display: inline-flex; gap: .45rem; align-items: center; }
.strip .sess[aria-pressed="true"] { color: var(--ink); border-color: var(--ink); }
.strip .sess .rec { font-size: .7rem; }
.askrow { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: .4rem 1rem; align-items: end; flex: none; border-top: 1px solid var(--line); padding-top: .45rem; }
.askrow .chips { grid-column: 1 / -1; display: flex; gap: .4rem; flex-wrap: wrap; align-items: center; }
.askrow textarea { height: 2.6rem; }
.askrow .btns { display: flex; gap: .4rem; }
html[data-level="partial"] .col .prose.clamp { -webkit-line-clamp: 8; }
"""

CHAIRS_JS = r"""
let sel = null;   // index into the debates list; null = newest
function debates(us) { return us.filter(u => u.kind === "debate"); }
function current(us) { const ds = debates(us); if (!ds.length) return null; const k = sel === null || sel >= ds.length ? ds.length - 1 : sel; return { d: ds[k], k, n: ds.length }; }
function followupsOf(us, d) { const i = us.indexOf(d), next = us.slice(i + 1).findIndex(u => u.kind === "debate"); return us.slice(i + 1, next < 0 ? undefined : i + 1 + next).filter(u => u.kind === "followup"); }
function go(k) { sel = k; openId = null; render(); }
function cellHtml(c, u) {
  const name = PAYLOAD.roleNames[c.role];
  if (c.status === "failed") return `<span class="cell" data-fact="seat-${c.role}">${seatHtml(c)}<span class="absent" title="${esc(failText(c.msg))}">no report</span></span>`;
  if (c.status === "silent") return `<span class="cell" data-fact="seat-${c.role}">${seatHtml(c)}<span class="st">not asked</span></span>`;
  return `<span class="cell" data-fact="seat-${c.role}">${seatHtml(c)}<span class="st" title="${esc(`${name} reported · ${c.msg.content.length.toLocaleString()} chars · ${c.msg.model || "model not recorded"}`)}">reported</span></span>`;
}
function modCell(d) {
  const V = parseVerdict(d.moderator.content);
  return `<span class="cell" data-fact="seat-moderator"><span class="seat" data-role="moderator" title="Moderator · ${esc(ROLE_JOB.moderator)}">M</span>${recHtml(V.fields)}${convHtml(V.fields)}</span>`;
}
function askRow(us) {
  const hasDebate = us.some(u => u.kind === "debate");
  return `<div class="askrow"><div class="chips">${considering()}<span class="eyebrow">plain text continues with the Moderator on this debate's reports · /debate reconvenes all four seats</span></div>
    <textarea class="ask" placeholder="${hasDebate ? "Continue with the Moderator…" : "Ask about a start/sit, trade, or waiver decision…"}"></textarea>
    <div class="btns"><button class="btn primary">Ask</button><button class="btn quiet">Full Prytaneum</button><button class="btn quiet">Quant</button><button class="btn quiet">Beat</button><button class="btn icon quiet" title="Attach a file to this chat (this session only)">+</button></div></div>`;
}
function chairCol(c, i) {
  const name = PAYLOAD.roleNames[c.role], id = `${c.role}-${c.msg.ts}`, open = openId === id;
  const clamp = level === "partial" && !open;
  const head = `<div class="head">${seatHtml(c)}<span class="who">${esc(name)}</span><span class="eyebrow">${c.status === "failed" ? "" : modelOf(c.msg) + " · "}${ago(c.msg.ts)}</span></div>`;
  const body = c.status === "failed"
    ? `<div class="body"><div class="absent-report" data-field="report" data-role="${c.role}"><span class="absent" title="${esc(failText(c.msg))}">no report reached the panel</span><br>Whether the call never ran, ran and was lost, or ran and could not be read is not known here. Missing information, never a finding that there is nothing to report.</div></div>`
    : `<div class="body" data-field="report" data-role="${c.role}"><div class="prose${clamp ? " clamp" : ""}">${md(c.msg.content)}</div>${clamp ? `<div class="fold" style="margin-top:.35rem">open · the whole report</div>` : ""}</div>`;
  return `<section class="col" data-role="${c.role}" role="option" data-unit="${id}" data-kind="chair" aria-expanded="${open}" tabindex="${i === 0 ? 0 : -1}" aria-label="${esc(name)}">${head}${body}</section>`;
}
function modCol(us, d) {
  const V = parseVerdict(d.moderator.content), id = `moderator-${d.moderator.ts}`, open = openId === id;
  const clamp = level === "partial" && !open;
  const fus = followupsOf(us, d);
  const marks = `${pinned(d.moderator) ? '<span class="mark on" title="Pinned.">◉ pinned</span>' : ""}${V.fields.action_item && objectiveFor(V.fields.action_item) ? `<span class="mark on" title="This verdict's ACTION ITEM is tracked as objective #${objectiveFor(V.fields.action_item).id}.">→ #${objectiveFor(V.fields.action_item).id}</span>` : ""}`;
  const fuHtml = level === "full" ? fus.map(f => { const W = parseVerdict(f.moderator.content); return `<div class="fu"><div class="you"><b>You</b> · ${esc(f.question ? f.question.content : "(no question recorded)")} ${ago(f.ts)}</div><div class="prose">${md(W.prose)}</div>${W.has ? receiptHtml(W) : `<div class="mark" style="margin-top:.3rem" title="Talked through; no new block. The call above stands.">no new call</div>`}</div>`; }).join("")
    : (fus.length ? `<div class="fu"><span class="mark" title="${esc(fus.map(f => f.question ? f.question.content : "").join(" · "))}">${fus.length} follow-up${fus.length === 1 ? "" : "s"} · full</span></div>` : "");
  return `<section class="col" data-role="moderator" role="option" data-unit="${id}" data-kind="chair" aria-expanded="${open}" tabindex="-1" aria-label="Moderator">
    <div class="head"><span class="seat" data-role="moderator" title="Moderator · ${esc(ROLE_JOB.moderator)}">M</span><span class="who">Moderator</span><span class="eyebrow">${modelOf(d.moderator)} · ${ago(d.moderator.ts)}</span>${marks}</div>
    <div class="body"><div class="call">${recHtml(V.fields)}${convHtml(V.fields, true)}${reachedHtml(d)}</div>${receiptHtml(V, { extraChars: 90 })}<div class="prose${clamp ? " clamp" : ""}" style="margin-top:.4rem">${md(V.prose)}</div>${clamp ? `<div class="fold" style="margin-top:.35rem">open · the whole reply</div>` : ""}${fuHtml}</div>
  </section>`;
}
function scrubber(us, cur) {
  if (!cur) return `<span class="scrub">No full run yet.</span>`;
  const q = questionOf(cur.d);
  return `<span class="scrub"><button class="btn icon quiet" ${cur.k === 0 ? "disabled" : ""} onclick="go(${cur.k - 1})" title="Previous debate">‹</button><span class="eyebrow"><b>debate ${cur.k + 1} of ${cur.n}</b></span><span class="q" title="${esc(q || "")}">${q ? esc(q) : absent("The question that opened this run was not recorded.")}</span>${ago(cur.d.ts)}<button class="btn icon quiet" ${cur.k === cur.n - 1 ? "disabled" : ""} onclick="go(${cur.k + 1})" title="Next debate">›</button></span>`;
}
function strip(us, cur) {
  const ds = debates(us);
  const sess = ds.map((d, k) => { const V = parseVerdict(d.moderator.content); return `<button class="sess" aria-pressed="${cur && cur.k === k}" onclick="go(${k})" title="${esc(questionOf(d) || "")}">${k + 1}${ago(d.ts)}${recHtml(V.fields)}${reachedHtml(d) ? (reached(d).n < 3 ? '<span class="attn" title="A chair sent no report.">⊘</span>' : "") : ""}</button>`; }).join("");
  const others = us.filter(u => u.kind === "summary" || u.kind === "notice").map(u => `<span class="sys" title="${esc(u.msg.content)}">${u.kind === "notice" ? '<span class="attn">!</span> notice' : "▤ memory summary"} · ${trunc(u.msg.content, 60)}</span>`).join("");
  return `<div class="strip"><span class="eyebrow">sessions</span>${sess}<span class="grow" style="flex:1"></span>${others}</div>`;
}
function render() {
  const us = units(hist()), cur = current(us), dock = document.getElementById("dock");
  if (level === "collapsed") {
    let cells = `<span class="x">No full run yet.</span>`;
    if (cur) cells = `${chairs(cur.d).map(c => cellHtml(c, cur.d)).join("")}${modCell(cur.d)}<span class="x" data-fact="question"><b>${trunc(questionOf(cur.d) || "(no question recorded)", 56)}</b></span>${ago(cur.d.ts)}${(() => { const f = followupsOf(us, cur.d).length; return f ? `<span class="mark" title="Follow-ups on this debate's reports, under the Moderator's column.">+${f} follow-up${f === 1 ? "" : "s"}</span>` : ""; })()}`;
    dock.innerHTML = `<div class="bar">${levelBtns()}<span class="eyebrow">the panel</span>${cells}<span class="grow"></span><button class="btn primary" onclick="setLevel('partial')">Ask</button></div>`;
    return;
  }
  let html = `<header class="ch"><span class="wordmark">The Prytaneum</span>${scrubber(us, cur)}<span class="grow"></span>${levelBtns()}</header>`;
  if (cur) html += `<div class="cols" role="listbox" aria-label="the four seats">${chairs(cur.d).map(chairCol).join("")}${modCol(us, cur.d)}</div>`;
  else html += `<div class="cols"><div class="col" style="grid-column:1/-1;padding:.6rem">Nothing decided yet in this league's chat.</div></div>`;
  if (level === "full") html += strip(us, cur);
  html += askRow(us);
  dock.innerHTML = html;
  wire(dock);
}
"""

VARIANTS = [
    ("dock_1_ledger", "D1 · Ledger", "the unit is the decision: standing call → receipt + ask → the ledger of every decision",
     {"collapsed": "One line: the recommendation, the conviction ladder, the question it answered (truncated at a word, full on hover), how many chairs it rests on, and its age — plus the attached context and the one action. It is the newest BLOCK-BEARING verdict, so a follow-up that only talked cannot blank it (the app's collapsed dock does blank: probe asis_collapsed_n8).",
      "partial": "The receipt of that call beside the ask panel, and nothing else. Every field of the Moderator's block as a labelled row (the four the prompt requires shown as absent when missing; the optional ones omitted, which is the Moderator's own statement that they do not apply), the ACTION ITEM marked when it is tracked as an objective, the dissenting chair named by its seat. No transcript: at 40vh a transcript is what the app currently spends its partial tier on and shows none of (probe: 0 messages visible).",
      "full": "Adds the ledger: one row per decision or exchange, newest first, in a scroll region of its own — time, kind, question, recommendation, conviction, the four seats, marks. A row opens to the three reports across (a failed chair as a labelled absence), the Moderator's prose and receipt. Follow-ups are their own rows and say when they issued no new call.",
      "sacrifices": "The conversation is not readable as a conversation: a follow-up's prose is a row's detail, not a bubble under its question. The receipt is repeated (standing call above, its row below) at full. The partial tier carries only ONE decision; if you want the one before it you go to full."},
     LEDGER_CSS, LEDGER_JS),
    ("dock_2_thread", "D2 · Thread", "the unit is the exchange: newest question → answer, input at the bottom, reports one tab away",
     {"collapsed": "One line: the four seats of the newest exchange, your question, an arrow, the Moderator's recommendation and REASON (or, for a block-less follow-up, its first words and a 'stands: BUY' mark for the call that still holds). It is the newest EXCHANGE, not the standing verdict — a conversation's collapsed state is its last turn.",
      "partial": "The newest exchange above the ask box: your question, the Moderator's reply (clamped to five lines, opening on Enter), the call with its conviction and seats, the REASON only, and the three reports as tabs in one line — the Beat chair's tab reads 'no report' as a hatched absence. The input sits at the bottom, where a conversation's input belongs, one line tall, with the routing rule stated once beside it.",
      "full": "The whole thread, oldest at the top and newest at the bottom, scrolled to the bottom on open, the input pinned beneath. Memory summaries and notices are one-line system rows (a notice takes the amber glyph). A verdict bubble carries the full receipt and the report tabs; a follow-up bubble says 'no new call' when it issued none. Pinned and objective are marks on the bubble.",
      "sacrifices": "The standing verdict is not the first thing you see when the newest turn is a follow-up — it is a mark in the header. Reports are one press away, never side by side. A long thread's early decisions are far up a scroll, with no index: this is a chat, not a ledger."},
     THREAD_CSS, THREAD_JS),
    ("dock_3_chairs", "D3 · Chairs", "the unit is the chair: four seat columns per debate, a scrubber between debates",
     {"collapsed": "The four seats as cells: three chairs each with reported / no report / not asked, and the Moderator's cell carrying the recommendation and the conviction ladder — then the debate's question and age and a count of follow-ups. This is the panel's STATE, which is what a panel's collapsed line should be; the app's has no notion of a chair that did not report.",
      "partial": "Four columns, one per seat, each scrolling on its own: the seat, the model that answered, the report clamped to eight lines (Enter opens the column). The Moderator's column leads with the call and the receipt, then its prose, and counts the follow-ups. A scrubber in the header moves between debates. The ask row sits below the columns.",
      "full": "The same columns with the whole report in each, the follow-ups in full under the Moderator, and a session strip of every debate (number, age, recommendation, a ⊘ where a chair sent no report) plus the summary and notice rows. History is navigated by debate, not by scrolling a transcript.",
      "sacrifices": "Four columns in 952px are 226px each: a chair's report wraps at ~34 characters and the Quant's bullet lists read tall. The thread order of a conversation is gone — you see one debate at a time. A user question with no answer, or a solo Quant/Beat lookup, has no column to live in and is shown only in the session strip."},
     CHAIRS_CSS, CHAIRS_JS),
]
