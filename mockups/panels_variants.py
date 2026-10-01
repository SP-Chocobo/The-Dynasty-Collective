"""Three structural answers to "what is the panel group FOR", all built on the same test:

    Can a reader get WHAT was decided, WHY, WHAT UNCERTAINTY REMAINS and WHAT IT IS OPTIMISING
    without assembling four interfaces?

and all mapped onto the two chains that have to line up:

    ENGINE   signals  ->  synthesis  ->  decision  ->  proof
    UI       state    ->  decision   ->  evidence  ->  objective

  P1 CALLS      one surface; the unit is the DECISION and the row IS the chain. Each verdict
                carries what it decided (call + conviction), why (REASON), what remains
                (chairs reached, the dissenting seat, RECON, RISK), the objective it opened and
                that objective's state, the findings it produced and whether their numbers
                count, and how it played out (your rating). Records that came from no verdict
                -- hand-written objectives, findings from other leagues or before the gate, a
                pin on a chair's report -- sit in one tail and say so.
  P2 STANDING / RECORD   a governed group of five panels under one frame, in two tiers by WHEN
                the panel reads them: STANDING (every question: objectives, findings) above
                RECORD (only when a question relates: verdicts, closed objectives, pins). One
                header grammar for all five; a strip at the top that owns the one link neither
                the app nor the engine chain gives a surface: what remains uncertain and what
                only you can settle.
  P3 BRIEF      neither store nor verdict: the four QUESTIONS the test asks, in its order, each
                answered first in one computed sentence and then by the records that sentence
                rests on. Every record lands in exactly one section -- verdicts under "what was
                decided", findings/comparisons/pins together under "why", objectives under "what
                it is optimising". "What remains uncertain" is the only section whose rows are
                DERIVED: one per open question, split by author into what the panel could not
                settle (a chair that sent no report, dissent, RECON, conviction below majority)
                and what only you can settle. And the fourth question is answered with an
                ABSENCE, because no store in the system holds what the team is optimising.

The three axes are meant to be orthogonal: P1 sorts by what PRODUCED a record, P2 by WHEN the
panel reads it, P3 by WHICH QUESTION it answers.

All three obey the same fixes over the baseline (panels_common): the orphaned pin is a labelled
absence; a pinned verdict shows its block; a rec-less verdict shows a hatched absence; the
rating has no default; delete is never a peer of done; eligibility is recomputed; counts say
what they count; the global store says it is global.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import design_system as ds  # noqa: E402  the single source of design tokens

# ---------------------------------------------------------------------------------------
# Shared renderers: one grammar per kind, used by all three variants.
# ---------------------------------------------------------------------------------------
SHARED_JS = r"""
// A string argument inside an inline handler is inside a double-quoted HTML attribute, so
// its own quotes must be entity-escaped or the attribute ends early. OUTCOME_LABELS contains
// "Didn't Work"; the unescaped form truncated every rating handler to `rate(ts, `.
function jsArg(v) { return esc(JSON.stringify(v)); }
function when(ts) {
  const s = NOW - ts, d = new Date(ts * 1000).toISOString().slice(0, 16).replace("T", " ");
  if (s < 48 * 3600) return ago(ts);
  return `<span class="age" title="${d} UTC">${d.slice(5, 10)}</span>`;
}
function chairsOf(d) {
  // The chairs that reported to THIS verdict: the debate unit in the transcript whose
  // Moderator message is this row's (log_decision runs in the same second as append_message).
  const u = units(hist()).find(u => u.moderator && Math.abs(u.moderator.ts - d.ts) < 5);
  if (!u) return `<span class="mark" title="This verdict's transcript is not in the current chat history (compacted or from before this history), so which chairs reported is not recoverable here.">chairs not on record</span>`;
  if (u.kind !== "debate") return `<span class="mark" title="A Moderator-only follow-up: no chairs were asked.">follow-up</span>`;
  return reachedHtml(u);
}
function dissentSeat(d) {
  if (!d.dissent) return "";
  const who = /^(quant|beat|contrarian)/i.exec(d.dissent);
  const r = who ? who[1].toLowerCase() : null;
  return r ? `<span class="seat" data-role="${r}" title="${esc(`Dissent — ${d.dissent}`)}">${ROLE_LETTER[r]}</span>` : `<span class="mark" title="${esc(`Dissent — ${d.dissent}`)}">dissent</span>`;
}
function remainsMarks(d) {
  const out = [chairsOf(d), dissentSeat(d)];
  if (d.recon) out.push(`<span class="mark attn" title="${esc(`RECON — ${d.recon}`)}">? recon</span>`);
  if (d.risk) out.push(`<span class="mark" title="${esc(`RISK — ${d.risk}`)}">risk</span>`);
  return out.filter(Boolean).join("");
}
function findingsOf(d) { return stores().findings.filter(f => f.question && f.question.trim() === d.question.trim() && f.date === d.date); }
function comparisonsOf(d) { return stores().comparisons.filter(c => c.question && c.question.trim() === d.question.trim() && c.date === d.date); }
function pinnedDecision(d) { return stores().pinned.some(ts => Math.abs(ts - d.ts) < 5); }
function rerunOf(d) { return stores().decisions.filter(x => x !== d && x.question === d.question && x.date === d.date); }

// ---- rating: no default. Save is disabled until a rating is chosen; each row by its ts. ----
function rate(ts, outcome) { ratings[ts] = Object.assign({}, ratings[ts], { outcome }); render(); }
function saveRating(ts) {
  const r = ratings[ts]; if (!r || !r.outcome) return;
  const d = PAYLOAD.decisions.find(x => x.ts === ts); if (!d) return;
  d.outcome = r.outcome; d.outcome_note = (document.getElementById(`note-${ts}`) || {}).value || ""; d.outcome_date = new Date(NOW * 1000).toISOString().slice(0, 10);
  delete ratings[ts]; render();
}
function ratingHtml(d) {
  if (d.outcome) return `<div class="sub">Rated <b>${esc(d.outcome)}</b> on ${esc(d.outcome_date)}${d.outcome_note ? ` — ${esc(d.outcome_note)}` : ""}. <button class="btn quiet" onclick="event.stopPropagation(); rerate(${d.ts})">re-rate</button></div>`;
  const r = ratings[d.ts] || {};
  return `<div class="rate" data-field="rating">
    <span class="k eyebrow">how did it play out</span>
    ${PAYLOAD.outcomeLabels.map(o => `<button class="chip" aria-pressed="${r.outcome === o}" onclick="event.stopPropagation(); rate(${d.ts}, ${jsArg(o)})">${esc(o)}</button>`).join("")}
    <input class="note" id="note-${d.ts}" placeholder="what actually happened (optional)" onclick="event.stopPropagation()" onkeydown="event.stopPropagation()">
    <button class="btn primary" ${r.outcome ? "" : "disabled"} title="${r.outcome ? "Record this rating; future related debates will be shown it." : "Choose a rating first. There is no default: an unrated call stays unrated."}" onclick="event.stopPropagation(); saveRating(${d.ts})">save</button>
  </div>`;
}
function rerate(ts) { const d = PAYLOAD.decisions.find(x => x.ts === ts); d.outcome = ""; d.outcome_note = ""; d.outcome_date = null; render(); }

// ---- objectives: the verbs, and delete behind the detail, dashed, two presses. ----
let armedDelete = null;
function objVerb(t, id) {
  const stop = "event.stopPropagation();";
  if (t.status === "likely_resolved") return `<button class="btn" title="Confirm the bot's proposal: closes it as done with the proposed reason." onclick="${stop} objAct(${t.id}, 'resolve')">confirm done</button><button class="btn quiet" title="Reject the proposal: back to open; the proposal is kept in the record as rejected." onclick="${stop} objAct(${t.id}, 'reopen')">keep open</button>`;
  if (t.status === "active") return `<button class="btn" title="Close as done. A note in the opened row travels with it into the closed list." onclick="${stop} objAct(${t.id}, 'resolve')">done</button><button class="btn quiet" title="Close as no longer relevant, never done." onclick="${stop} objAct(${t.id}, 'dismiss')">dismiss</button>`;
  return `<button class="btn quiet" title="Open it again as a new objective (the closed one stays closed)." onclick="${stop} objAct(${t.id}, 'revisit')">revisit</button>`;
}
function objAct(id, act) {
  const t = PAYLOAD.todos.find(x => x.id === id); if (!t) return;
  const note = (document.getElementById(`onote-${id}`) || {}).value || "";
  const today = new Date(NOW * 1000).toISOString().slice(0, 10);
  if (act === "resolve") { const was = t.status === "likely_resolved"; t.status = "resolved"; if (note) t.resolution_reason = note; else if (!t.resolution_reason) t.resolution_reason = "Marked done by user"; t.resolution_date = today; if (was) closeProposal(t, "accepted"); }
  if (act === "dismiss") { const was = t.status === "likely_resolved"; t.status = "dismissed"; t.resolution_reason = note || "Dismissed by user"; t.resolution_date = today; if (was) closeProposal(t, "superseded_by_dismissal"); }
  if (act === "reopen") { t.status = "active"; t.resolution_reason = ""; closeProposal(t, "rejected"); }
  if (act === "revisit") { const nid = Math.max(...PAYLOAD.todos.map(x => x.id)) + 1; PAYLOAD.todos.push({ id: nid, ts: NOW, date: today, text: t.text, source: "manual", question: `Revisit of #${t.id}`, decision_ts: null, status: "active", resolution_reason: "", resolution_date: null, revisions: [], notes: [], proposals: [] }); }
  if (act === "delete") { if (armedDelete !== id) { armedDelete = id; render(); return; } PAYLOAD.todos.splice(PAYLOAD.todos.indexOf(t), 1); armedDelete = null; }
  if (act === "addnote") { const v = (document.getElementById(`anote-${id}`) || {}).value || ""; if (v.trim()) t.notes.push({ ts: NOW, date: today, text: v.trim() }); }
  render();
}
function closeProposal(t, outcome) { for (const p of [...(t.proposals || [])].reverse()) if (p.outcome === "pending") { p.outcome = outcome; p.closed_date = new Date(NOW * 1000).toISOString().slice(0, 10); return; } }
function objDetail(t) {
  const d = decisionOfObjective(t);
  const hist = [];
  for (const r of t.revisions || []) hist.push(`<div>${esc(r.date)} · was <b>${esc(r.text)}</b>${r.reason ? ` — ${esc(r.reason)}` : ""}</div>`);
  for (const n of t.notes || []) hist.push(`<div>${esc(n.date)} · note: ${esc(n.text)}</div>`);
  for (const p of t.proposals || []) hist.push(`<div>${esc(p.date)} · proposed done: ${esc(p.reason)} → <b>${esc(p.outcome)}</b>${p.closed_date ? ` ${esc(p.closed_date)}` : ""}</div>`);
  if (t.last_referenced) hist.push(`<div>${esc(t.last_referenced)} · cited by id in a Moderator reply</div>`);
  const from = d ? `<div class="sub">Opened by the verdict <b>${esc(d.recommendation || "—")}</b> to “${trunc(d.question, 70)}” on ${esc(d.date)} (joined on the ACTION ITEM text — todo_log has a decision_ts slot and nothing writes it).</div>`
    : t.source === "moderator" ? `<div class="sub">Opened by a Moderator ACTION ITEM to “${trunc(t.question || "", 70)}”; that verdict is not in the log.</div>` : `<div class="sub">Written by you${t.question ? ` · ${esc(t.question)}` : ""}.</div>`;
  const live = t.status === "active" || t.status === "likely_resolved";
  const stop = "event.stopPropagation();";
  return `<div class="detail">${from}${hist.length ? `<div class="hist">${hist.join("")}</div>` : `<div class="sub">No revisions, notes or proposals on record.</div>`}
    ${live ? `<div class="acts"><input class="note" id="anote-${t.id}" placeholder="add a note while this is open" onclick="${stop}" onkeydown="${stop}"><button class="btn quiet" onclick="${stop} objAct(${t.id}, 'addnote')">add note</button></div>
    <div class="acts"><input class="note" id="onote-${t.id}" placeholder="resolution note (optional) — it is what a future debate will be told" onclick="${stop}" onkeydown="${stop}"><span class="sep"></span>
      <button class="btn danger" title="Erase this record entirely -- for a mistaken or duplicate entry, never for 'done'. Two presses." onclick="${stop} objAct(${t.id}, 'delete')">${armedDelete === t.id ? "press again to delete permanently" : "delete…"}</button></div>`
    : `<div class="acts"><span class="sep"></span><button class="btn danger" title="Erase this record entirely. Two presses." onclick="${stop} objAct(${t.id}, 'delete')">${armedDelete === t.id ? "press again to delete permanently" : "delete…"}</button></div>`}
  </div>`;
}
function objRow(t, i, opts) {
  opts = opts || {};
  const id = `objective-${t.id}`;
  return `<div class="row" ${optAttrs({ kind: "objective", ts: t.id }, i)} data-kind="objective" data-id="${t.id}" data-state="${t.status}">
    ${when(t.ts)}${kindHtml("objective")}${authorSeat(t.source === "moderator" ? "moderator" : "user")}
    <span class="line"><b>#${t.id}</b> ${esc(t.text)}</span>
    <span class="marks">${(t.revisions || []).length ? `<span class="mark" title="Revised ${(t.revisions || []).length} time(s) by a TODO UPDATE; the earlier text is kept.">revised</span>` : ""}${t.last_referenced ? `<span class="mark" title="Cited by id in a Moderator reply on ${t.last_referenced}.">cited</span>` : ""}</span>
    ${objectiveState(t)}<span class="verb">${objVerb(t)}</span>
    ${openId === id ? objDetail(t) : ""}</div>`;
}

// ---- findings and comparisons: the signals gate. ----
function findingVerb(f) {
  const e = findingFeeds(f), stop = "event.stopPropagation();";
  if (e.word === "awaiting you") return `<button class="btn" title="Says you looked, not that it is verified. Its number then counts at a low weight." onclick="${stop} findAct(${f.id}, 'confirm')">confirm</button>`;
  if (e.feeds) return `<button class="btn quiet" title="Take the number back out of circulation; the claim stays in the record." onclick="${stop} findAct(${f.id}, 'retract')">retract</button>`;
  if (e.word === "retracted") return `<button class="btn quiet" title="Undo the retraction: back to whatever adjudication it had, not straight to counting." onclick="${stop} findAct(${f.id}, 'restore')">restore</button>`;
  if (e.word === "never adjudicated") return `<button class="btn" title="Confirm as with any other: says you looked." onclick="${stop} findAct(${f.id}, 'confirm')">confirm</button>`;
  return "";
}
function findAct(id, act) {
  const f = PAYLOAD.findings.find(x => x.id === id); if (!f) return;
  const today = new Date(NOW * 1000).toISOString().slice(0, 10);
  if (act === "confirm") { f.adjudication = "human_confirmed"; f.confirmed_by = "human"; f.confirmed_at = today; if (!("cited_source_admitted" in f)) f.cited_source_admitted = f.source.toLowerCase().replace(/\s/g, ""); }
  if (act === "retract") f.retracted = { reason: "withdrawn", by: "human", at: today, note: "" };
  if (act === "restore") delete f.retracted;
  render();
}
function findingRow(f, i) {
  const e = findingFeeds(f), id = `finding-${f.id}`;
  return `<div class="row" ${optAttrs({ kind: "finding", ts: f.id }, i)} data-kind="finding" data-id="${f.id}" data-feeds="${e.feeds}">
    ${when(f.ts)}${kindHtml("finding")}${authorSeat("moderator")}
    <span class="line"><b>${esc(f.player_name)}</b> <span class="q">· ${esc(f.source)} ${rankHtml(f)} · ${trunc(f.claim, 80)}</span></span>
    <span class="marks">${leagueMark(f.league_id)}</span>
    ${stateHtml(e.cls, e.word, e.why)}<span class="verb">${findingVerb(f)}</span>
    ${openId === id ? `<div class="detail"><div class="prose">${esc(f.claim)}</div><div class="sub">${esc(e.why)}</div><div class="acts">${originHtml(f)}${f.conviction ? `<span class="mark" title="The verdict's conviction when this was surfaced.">${esc(f.conviction.toLowerCase())}</span>` : ""}<span class="scope">asked: ${trunc(f.question || "", 90)}</span></div></div>` : ""}</div>`;
}
function comparisonRow(c, i) {
  const id = `comparison-${c.id}`, verb = { ">": "ahead of", "<": "behind", "~": "about even with" }[c.direction];
  return `<div class="row" ${optAttrs({ kind: "comparison", ts: c.id }, i)} data-kind="comparison" data-id="${c.id}">
    ${when(c.ts)}${kindHtml("comparison")}${authorSeat("moderator")}
    <span class="line"><b>${esc(c.subject)}</b> <span class="q">${esc(verb)}</span> <b>${esc(c.compared_to)}</b> <span class="q">· ${esc(c.source)}${c.context ? ` · ${esc(c.context)}` : ""}</span></span>
    <span class="marks">${leagueMark(c.league_id)}</span>
    ${stateHtml("", "no number", "A relative claim: read by every debate as a cross-check on ordering, never as a number. It cannot count and nothing here offers to make it.")}<span class="verb"></span>
    ${openId === id ? `<div class="detail"><div class="prose">${esc(c.evidence)}</div><div class="sub">Panel-undisputed when surfaced; not re-verified by anything here.</div><div class="acts"><span class="scope">asked: ${trunc(c.question || "", 90)}</span></div></div>` : ""}</div>`;
}

// ---- pins: the message, or the labelled orphan. ----
function unpin(ts) { const i = PAYLOAD.pinned.indexOf(ts); if (i >= 0) PAYLOAD.pinned.splice(i, 1); render(); }
function pinRow(ts, i) {
  const m = pinMessage(ts), id = `pin-${ts}`;
  if (!m) return `<div class="row" ${optAttrs({ kind: "pin", ts }, i)} data-kind="pin" data-orphan="true">
    ${when(ts)}${kindHtml("pin")}<span class="seat silent" title="Unknown: the message is gone.">·</span>
    <span class="line">${absent("Pinned, but the message is no longer in this chat: it was older than a compaction cutoff and was summarised away. The pin store still holds it; a debate can no longer retrieve it.")} <span class="q">message no longer in this chat</span></span>
    <span class="marks"></span>${stateHtml("needs", "message gone", "The pin outlived its message. Unpin it, or accept that it can never surface again.")}<span class="verb"><button class="btn quiet" onclick="event.stopPropagation(); unpin(${ts})">unpin</button></span>
    ${openId === id ? `<div class="detail"><div class="prose">The pin store holds a timestamp and nothing else — <span class="mono">${new Date(ts * 1000).toISOString().slice(0, 16).replace("T", " ")} UTC</span>. The message it points at is no longer in this chat: <b>compact_chat_history</b> summarised it away without consulting the pin store, so nothing can retrieve it — not this panel, and not a debate.</div><div class="sub">The text is not recoverable from the pin store, and this is the only place in the product that says so: the app's own panel lists only pins whose message survives, and counts only those, so its header reads two where three are stored. Unpin to stop carrying a pointer to nothing.</div></div>` : ""}</div>`;
  const v = parseVerdict(m.content);
  return `<div class="row" ${optAttrs({ kind: "pin", ts }, i)} data-kind="pin" data-role="${m.role}">
    ${when(ts)}${kindHtml("pin")}${authorSeat(m.role, m.model)}
    <span class="line">${pinLine(m)}</span>
    <span class="marks">${v.has ? `<span class="mark" title="A verdict: its block is shown whole when opened.">verdict</span>` : ""}</span>
    ${stateHtml("", "in transcript", "Retrieved for a debate only when the question shares two or more words with it.")}<span class="verb"><button class="btn quiet" onclick="event.stopPropagation(); unpin(${ts})">unpin</button></span>
    ${openId === id ? `<div class="detail"><div class="prose">${md(v.has ? v.prose : m.content)}</div>${v.has ? receiptHtml(v) : ""}<div class="sub">${esc(m.content.length)} characters, shown whole. The app cuts a pinned message at 500 and hands a debate 400.</div></div>` : ""}</div>`;
}

// ---- decisions ----
function decisionDetail(d, opts) {
  opts = opts || {};
  const t = objectiveOfDecision(d), fs = findingsOf(d), cs = comparisonsOf(d), rr = rerunOf(d);
  const joins = [];
  if (opts.joins !== false) {
    if (t) joins.push(`<div class="acts"><span class="eyebrow">objective it opened</span>${kindHtml("objective")}<b>#${t.id}</b> <span class="q">${trunc(t.text, 90)}</span> ${objectiveState(t)} <span class="verb">${objVerb(t)}</span></div>`);
    else if (parseVerdict(d.moderator_text).fields.action_item) joins.push(`<div class="sub">Its ACTION ITEM is not among the objectives (text join; nothing writes decision_ts).</div>`);
    for (const f of fs) { const e = findingFeeds(f); joins.push(`<div class="acts"><span class="eyebrow">finding it produced</span>${kindHtml("finding")}<b>${esc(f.player_name)}</b> <span class="q">· ${esc(f.source)} ${rankHtml(f)} · ${trunc(f.claim, 60)}</span> ${stateHtml(e.cls, e.word, e.why)} <span class="verb">${findingVerb(f)}</span></div>`); }
    for (const c of cs) joins.push(`<div class="acts"><span class="eyebrow">comparison it produced</span>${kindHtml("comparison")}<b>${esc(c.subject)}</b> <span class="q">${({ ">": "ahead of", "<": "behind", "~": "about even with" })[c.direction]}</span> <b>${esc(c.compared_to)}</b> <span class="q">· ${esc(c.source)}</span></div>`);
  }
  if (rr.length) joins.push(`<div class="sub attn-text">Asked again the same day: ${rr.map(x => `a ${x.ts > d.ts ? "later" : "earlier"} run ${Math.abs(Math.round(x.ts - d.ts))}s ${x.ts > d.ts ? "after" : "before"} this one called <b>${esc(x.recommendation || "—")}</b>`).join("; ")}. Each row is rated on its own.</div>`);
  return `<div class="detail">${decisionReceipt(d)}${joins.join("")}${ratingHtml(d)}</div>`;
}
function decisionRow(d, i, opts) {
  opts = opts || {};
  const id = `decision-${d.ts}`, t = opts.joins === false ? null : objectiveOfDecision(d), fs = opts.joins === false ? [] : findingsOf(d);
  const marks = [remainsMarks(d)];
  if (t) marks.push(`<span class="mark${t.status === "likely_resolved" ? " needs" : t.status === "active" ? " on" : ""}" title="${esc(`Opened objective #${t.id}: ${t.text} — ${t.status.replace("_", " ")}`)}">objective #${t.id}</span>`);
  if (fs.length) { const w = fs.filter(f => findingFeeds(f).cls === "needs").length; marks.push(`<span class="mark${w ? " needs" : ""}" title="${esc(`${fs.length} finding(s) from this debate${w ? `; ${w} awaiting your confirmation` : ""}`)}">${fs.length} finding${fs.length > 1 ? "s" : ""}</span>`); }
  if (pinnedDecision(d)) marks.push(`<span class="mark" title="You pinned this verdict in the transcript.">pinned</span>`);
  return `<div class="row" ${optAttrs({ kind: "decision", ts: d.ts }, i)} data-kind="decision" data-date="${d.date}" data-rated="${!!d.outcome}">
    ${when(d.ts)}${kindHtml("decision")}${authorSeat("moderator", d.model)}
    <span class="line">${decisionRec(d)} ${decisionConv(d)} <span class="q">to</span> ${trunc(d.question, 90)}</span>
    <span class="marks">${marks.join("")}</span>
    ${decisionState(d)}<span class="verb">${d.outcome ? "" : `<button class="btn" title="Open the row to rate it. Nothing is chosen for you." onclick="event.stopPropagation(); openId = openId === '${id}' ? null : '${id}'; focusedId = '${id}'; render()">rate</button>`}</span>
    ${openId === id ? decisionDetail(d, opts) : ""}</div>`;
}
function emptyRow(what, why) { return `<div class="empty" data-empty="${esc(what)}">${absent(why)} <span>${esc(what)}</span></div>`; }
"""


# ---------------------------------------------------------------------------------------
# P1 CALLS
# ---------------------------------------------------------------------------------------
CALLS_CSS = r"""
.row { grid-template-columns: 4.2rem auto auto minmax(0, 1fr) auto auto auto; }
.row .marks { display: inline-flex; gap: .25rem; align-items: center; white-space: nowrap; }
.divider { display: flex; align-items: baseline; gap: .8rem; padding: .45rem .8rem .3rem; border-bottom: 1px solid var(--line); background: color-mix(in srgb, var(--surface-2) 80%, transparent); }
.divider .sub { color: var(--dim); font-size: .74rem; }
.detail .acts .eyebrow { min-width: 11rem; }
.attn-text b { color: var(--ink); }
"""

CALLS_HTML = """
<div class="group-head">
  <span class="wordmark">Front office memory</span>
  <span class="sub" id="gh-sub"></span>
  <span class="grow"></span>
  <span class="chips" id="chips"></span>
</div>
<div class="rows" id="rows" data-panel="calls" role="listbox" aria-label="every verdict, with what it opened and what it produced"></div>
"""

CALLS_JS = r"""
function counts(S) {
  const n = needsYou(S);
  const fromVerdict = new Set();
  for (const d of S.decisions) { const t = objectiveOfDecision(d); if (t) fromVerdict.add(`o${t.id}`); for (const f of findingsOf(d)) fromVerdict.add(`f${f.id}`); for (const c of comparisonsOf(d)) fromVerdict.add(`c${c.id}`); }
  const tail = { todos: S.todos.filter(t => !fromVerdict.has(`o${t.id}`)), findings: S.findings.filter(f => !fromVerdict.has(`f${f.id}`)), comparisons: S.comparisons.filter(c => !fromVerdict.has(`c${c.id}`)),
                 pins: S.pinned.filter(ts => !S.decisions.some(d => Math.abs(d.ts - ts) < 5)) };
  return { n, tail, tailN: tail.todos.length + tail.findings.length + tail.comparisons.length + tail.pins.length };
}
function setFilter(k) { filters.kind = filters.kind === k ? null : k; openId = null; render(); }
function render() {
  const S = stores(), C = counts(S), n = C.n;
  const needs = n.unrated + n.proposed + n.awaiting + n.orphans;
  document.getElementById("gh-sub").innerHTML = S.decisions.length || C.tailN
    ? `${tally(S.decisions.length, "verdict")} · ${tally(n.open, "objective")} open · ${tally(S.findings.length, "finding")} · ${needs ? `<span class="needs" title="Rows waiting on you: ${n.unrated} unrated, ${n.proposed} proposed done, ${n.awaiting} awaiting confirmation, ${n.orphans} pin(s) without a message.">${needs} need you</span>` : `<span title="Nothing is waiting on you.">nothing needs you</span>`}`
    : `${absent("Every store is empty: no verdict has been logged, no objective opened, nothing pinned, nothing found. The next debate is handed nothing but the transcript.")} nothing on record yet`;
  const chips = [["all", null, S.decisions.length + C.tailN], ["need you", "needs", needs], ["open objectives", "open", n.open + n.proposed], ["rated", "rated", S.decisions.filter(d => d.outcome).length], ["not from a verdict", "tail", C.tailN]];
  document.getElementById("chips").innerHTML = chips.map(([w, k, c]) => `<button class="chip${k === "needs" ? " needs" : ""}" aria-pressed="${filters.kind === k}" onclick="setFilter(${jsArg(k)})">${w}<span class="n">${qty(c)}</span></button>`).join("");
  const keepD = d => filters.kind === null || (filters.kind === "needs" && (!d.outcome || (objectiveOfDecision(d) || {}).status === "likely_resolved" || findingsOf(d).some(f => findingFeeds(f).cls === "needs")))
    || (filters.kind === "open" && ["active", "likely_resolved"].includes((objectiveOfDecision(d) || {}).status)) || (filters.kind === "rated" && !!d.outcome);
  const ds = [...S.decisions].sort((a, b) => b.ts - a.ts).filter(keepD);
  let i = 0, html = "";
  if (filters.kind !== "tail") {
    html += ds.map(d => decisionRow(d, i++)).join("");
    if (!ds.length) html += emptyRow(S.decisions.length ? "no verdict matches this filter" : "no verdicts logged", S.decisions.length ? "The filter hides every verdict." : "No Moderator verdict has been logged in this league. A verdict is logged when the Moderator's reply carries its closing block.");
  }
  const T = C.tail;
  const keepT = t => filters.kind === null || filters.kind === "tail" || (filters.kind === "needs" && t.status === "likely_resolved") || (filters.kind === "open" && ["active", "likely_resolved"].includes(t.status));
  const keepF = f => filters.kind === null || filters.kind === "tail" || (filters.kind === "needs" && findingFeeds(f).cls === "needs");
  const keepP = ts => filters.kind === null || filters.kind === "tail" || (filters.kind === "needs" && !pinMessage(ts));
  const tailRows = [...T.todos.filter(keepT).map(t => ["o", t.ts, t]), ...T.findings.filter(keepF).map(f => ["f", f.ts, f]), ...T.comparisons.filter(() => filters.kind === null || filters.kind === "tail").map(c => ["c", c.ts, c]), ...T.pins.filter(keepP).map(ts => ["p", ts, ts])].sort((a, b) => b[1] - a[1]);
  if (filters.kind === null || filters.kind === "tail" || tailRows.length) {
    html += `<div class="divider"><span class="eyebrow"><b>Not from a verdict</b></span><span class="sub">objectives you wrote, findings from other leagues or from before the gate, pins on a chair's report — nothing here has a call to hang on</span></div>`;
    html += tailRows.map(([k, ts, x]) => k === "o" ? objRow(x, i++) : k === "f" ? findingRow(x, i++) : k === "c" ? comparisonRow(x, i++) : pinRow(x, i++)).join("");
    if (!tailRows.length) html += emptyRow("nothing outside the verdicts", "Every objective, finding and pin on record hangs on a verdict above.");
  }
  const root = document.getElementById("rows"); root.innerHTML = html; wire(root);
}
"""

# ---------------------------------------------------------------------------------------
# P2 STANDING / RECORD
# ---------------------------------------------------------------------------------------
STANDING_CSS = r"""
.row { grid-template-columns: 4.2rem auto auto minmax(0, 1fr) auto auto auto; }
.row .marks { display: inline-flex; gap: .25rem; align-items: center; white-space: nowrap; }
.strip .mark { font-size: .72rem; padding: .18rem .5rem; cursor: pointer; }
.strip .mark:hover { border-color: var(--ink); }
.strip .eyebrow { margin-right: .2rem; }
.detail .acts .eyebrow { min-width: 11rem; }
.attn-text b { color: var(--ink); }
"""

STANDING_HTML = """
<div class="group-head">
  <span class="wordmark">Front office memory</span>
  <span class="sub">what the next debate is handed, and what only you can tell it</span>
  <span class="grow"></span>
</div>
<div class="strip" id="strip" aria-label="what remains uncertain"></div>
<div class="tier"><span class="eyebrow"><b>Standing</b> · handed to the panel on every question</span><span class="sub">whether or not the question is about them</span></div>
<div id="standing"></div>
<div class="tier"><span class="eyebrow"><b>Record</b> · handed to the panel only when a question relates</span><span class="sub">by word overlap with the question; a verdict only once rated</span></div>
<div id="record"></div>
"""

STANDING_JS = r"""
openPanels = { objectives: true, findings: true, verdicts: false, closed: false, pins: false };
function togglePanel(k) { openPanels[k] = !openPanels[k]; render(); }
function jump(k) { openPanels[k] = true; render(); const el = document.querySelector(`[data-panel="${k}"]`); el && el.scrollIntoView({ block: "nearest" }); }
function panel(k, name, countHtml, readWord, readWhy, rows, emptyWhat, emptyWhy) {
  const open = openPanels[k];
  return `<section class="panel" data-panel="${k}" data-open="${open}">
    <button class="ph" aria-expanded="${open}" onclick="togglePanel('${k}')"><span class="tri">${open ? "▾" : "▸"}</span><span class="name">${name}</span><span class="count">${countHtml}</span><span class="grow"></span><span class="read" title="${esc(readWhy)}">read: ${readWord}</span></button>
    ${open ? `<div class="pb"><div class="rows" role="listbox" aria-label="${esc(name)}">${rows.length ? rows.join("") : emptyRow(emptyWhat, emptyWhy)}</div></div>` : ""}
  </section>`;
}
function render() {
  const S = stores(), n = needsYou(S);
  // The strip: the link with no surface -- what remains uncertain, and what only you can settle.
  const newest = [...S.decisions].sort((a, b) => b.ts - a.ts)[0];
  const marks = [];
  if (newest) {
    const low = newest.conviction && CONV[newest.conviction.toLowerCase()] && CONV[newest.conviction.toLowerCase()][2];
    marks.push(`<span class="mark${low ? " attn" : ""}" title="${esc(`The newest call, ${newest.recommendation || "—"}, is ${newest.conviction || "of unrecorded conviction"}${newest.recon ? ". RECON: " + newest.recon : ""}${newest.dissent ? ". DISSENT: " + newest.dissent : ""}`)}" onclick="jump('verdicts')">newest call: ${esc((newest.conviction || "conviction not recorded").toLowerCase())}</span>`);
    marks.push(`<span class="mark" onclick="jump('verdicts')" title="Which chairs reported to the newest call.">${chairsOf(newest).replace(/<span class="mark[^>]*>|<\/span>/g, "")}</span>`);
  }
  if (n.unrated) marks.push(`<span class="mark needs" onclick="jump('verdicts')" title="Verdicts you have not rated. Until rated they teach nothing to a future debate.">${n.unrated} verdict${n.unrated === 1 ? "" : "s"} unrated</span>`);
  if (n.proposed) marks.push(`<span class="mark needs" onclick="jump('objectives')" title="A bot proposed these are done; only you can close them.">${n.proposed} objective${n.proposed === 1 ? "" : "s"} proposed done</span>`);
  if (n.awaiting) marks.push(`<span class="mark needs" onclick="jump('findings')" title="Rank-bearing findings whose number is held back until you confirm.">${n.awaiting} finding${n.awaiting === 1 ? "" : "s"} awaiting you</span>`);
  if (n.orphans) marks.push(`<span class="mark needs" onclick="jump('pins')" title="Pins whose message a compaction summarised away.">${n.orphans} pin${n.orphans === 1 ? "" : "s"} without a message</span>`);
  document.getElementById("strip").innerHTML = `<span class="eyebrow"><b>Remains</b></span>` + (marks.length ? marks.join("") : `<span class="sub">${absent("Nothing is on record, so nothing is uncertain on record either. The transcript is the only memory the next debate gets.")} <span class="scope">nothing on record</span></span>`);

  let i = 0;
  const live = S.todos.filter(t => ["active", "likely_resolved"].includes(t.status)).sort((a, b) => (a.status === "likely_resolved" ? -1 : 0) - (b.status === "likely_resolved" ? -1 : 0) || b.ts - a.ts);
  const fl = [...S.findings.map(f => ["f", f]), ...S.comparisons.map(c => ["c", c])].sort((a, b) => b[1].ts - a[1].ts);
  const counting = S.findings.filter(f => findingFeeds(f).feeds).length;
  const standing = [
    panel("objectives", "Objectives", `${qty(n.open)} open${n.proposed ? ` · <span class="needs">${n.proposed} proposed done</span>` : ""}`, "every question",
      "Every open objective is in the context of every debate, as standing context: a rebuild-vs-contend objective changes what the right call even is. They are opened by a Moderator ACTION ITEM or by you; a bot can revise or propose one done; only you close one.",
      live.map(t => objRow(t, i++)), "no open objectives", "No objective is open. The next debate is handed none; ACTION ITEM lines in a verdict open them, or you can."),
    panel("findings", "Findings", `${qty(S.findings.length)} · ${tally(S.comparisons.length, "comparison")}${n.awaiting ? ` · <span class="needs">${n.awaiting} awaiting you</span>` : ""} · ${qty(counting)} counting · <span title="Stored globally and read by every league, unlike everything else here.">global</span>`, "every question",
      "The newest thirty findings and comparisons are in every debate's context, across every league. A finding's NUMBER also feeds the composite score, at a low weight, once its source is allowed and you have confirmed it. This is a signals gate, not evidence for any one verdict.",
      fl.map(([k, x]) => k === "f" ? findingRow(x, i++) : comparisonRow(x, i++)), "no findings", "No panel-vetted finding has been recorded in any league. The Moderator writes one only when the whole panel left a named-source claim undisputed."),
  ];
  const ds = [...S.decisions].sort((a, b) => (a.outcome ? 1 : 0) - (b.outcome ? 1 : 0) || b.ts - a.ts);
  const closed = S.todos.filter(t => ["resolved", "dismissed"].includes(t.status)).sort((a, b) => b.ts - a.ts);
  const record = [
    panel("verdicts", "Verdicts", `${qty(S.decisions.length)}${n.unrated ? ` · <span class="needs">${n.unrated} unrated</span>` : ""} · ${qty(S.decisions.length - n.unrated)} rated`, "when related and rated",
      "A past verdict reaches a debate only when the question shares words with it AND you have rated how it played out. Unrated verdicts are excluded: an unrated call has nothing to teach.",
      ds.map(d => decisionRow(d, i++, { joins: false })), "no verdicts logged", "No Moderator verdict has been logged in this league. One is logged whenever the Moderator's reply carries its closing block."),
    panel("closed", "Closed objectives", `${qty(closed.length)} · ${qty(closed.filter(t => t.status === "resolved").length)} done · ${qty(closed.filter(t => t.status === "dismissed").length)} dismissed`, "when related",
      "Resolved and dismissed objectives reach a debate when the question shares words with them, with their resolution note -- so the panel can say why a similar idea ended the way it did.",
      closed.map(t => objRow(t, i++)), "nothing closed", "No objective has been resolved or dismissed yet."),
    panel("pins", "Pins", `${qty(S.pinned.length)}${n.orphans ? ` · <span class="needs">${n.orphans} message gone</span>` : ""}`, "when related",
      "A pinned message reaches a debate only when the question shares two or more words with it. Pinning is findability, never priority. These are marks on the transcript; the dock shows them on the message.",
      [...S.pinned].sort((a, b) => b - a).map(ts => pinRow(ts, i++)), "nothing pinned", "You have pinned nothing. Pin from a message in the dock."),
  ];
  document.getElementById("standing").innerHTML = standing.join("");
  document.getElementById("record").innerHTML = record.join("");
  wire(document.getElementById("group"));
}
"""


# ---------------------------------------------------------------------------------------
# P3 BRIEF
# ---------------------------------------------------------------------------------------
BRIEF_CSS = r"""
.row { grid-template-columns: 4.2rem auto auto minmax(0, 1fr) auto auto auto; }
.row .marks { display: inline-flex; gap: .25rem; align-items: center; white-space: nowrap; }
.detail .acts .eyebrow { min-width: 11rem; }
.attn-text b { color: var(--ink); }
/* A question section: the number, the question, the answer in a sentence, then the record
   that answer rests on. No expander anywhere -- the brief is a document, not a drawer. */
.qsec { margin: 0 0 1.05rem; }
.qh { display: flex; align-items: baseline; gap: .6rem; }
.qh .qn { font-family: var(--mono, monospace); font-size: .72rem; color: var(--dim); border: 1px solid var(--line-2); border-radius: 3px; padding: 0 .38rem; flex: none; }
.qh .qq { font-size: .95rem; font-weight: 600; color: var(--ink); margin: 0; letter-spacing: 0; }
.qh .qc { font-family: var(--mono, monospace); font-size: .7rem; letter-spacing: .05em; text-transform: uppercase; color: var(--dim); }
.qh .grow { flex: 1; }
.qa { font-size: .88rem; color: var(--ink); max-width: 104ch; margin: .3rem 0 .55rem; line-height: 1.5; }
.qa b { font-weight: 600; }
.qa .q { color: var(--muted); }
.qa .rec { font-size: .82rem; }
.qf { font-size: .78rem; color: var(--muted); max-width: 104ch; margin: .4rem 0 0; }
/* The unresolved row: no timestamp and no author, because an open question has neither. */
.orow { grid-template-columns: auto minmax(0, 1fr) auto auto auto; }
.orow .kind { cursor: help; }
.divider { display: flex; align-items: baseline; gap: .8rem; padding: .45rem .8rem .3rem; border-bottom: 1px solid var(--line); background: color-mix(in srgb, var(--surface-2) 80%, transparent); }
.divider .eyebrow b { color: var(--ink); }
.divider .sub { color: var(--dim); font-size: .76rem; }
""".replace("var(--mono, monospace)", ds.FONT_MONO)

BRIEF_HTML = """
<div class="group-head">
  <span class="wordmark">Front office memory</span>
  <span class="sub">the brief — four questions, in the order the test asks them</span>
  <span class="grow"></span>
  <span class="sub" id="asof"></span>
</div>
<div id="brief"></div>
"""

BRIEF_JS = r"""
// A section = one of the test's four questions. Heading, the answer in a sentence, then the
// record that answer rests on. Every record in the four stores appears in exactly ONE section,
// under the question it answers -- that is the whole hierarchy.
function qsec(k, n, question, count, answer, rows, emptyWhat, emptyWhy, foot) {
  return `<section class="qsec" data-panel="${k}">
    <div class="qh"><span class="qn">${n}</span><h2 class="qq">${question}</h2><span class="grow"></span><span class="qc">${count}</span></div>
    <div class="qa">${answer}</div>
    <div class="rows" role="listbox" aria-label="${esc(question)}">${rows.length ? rows.join("") : emptyRow(emptyWhat, emptyWhy)}</div>
    ${foot ? `<div class="qf">${foot}</div>` : ""}
  </section>`;
}
function jumpUnit(unit) {
  openId = unit; focusedId = unit; render();
  const el = document.querySelector(`[data-unit="${unit}"]`);
  if (el) el.scrollIntoView({ block: "center" });
}
// A row whose unit is not a record but an OPEN QUESTION. It is the only derived unit in the
// group: it exists because something is unsettled, and it dies when that thing is settled.
function openRow(o, i) {
  const id = `open-${o.id}`;
  return `<div class="row orow" ${optAttrs({ kind: "open", ts: o.id }, i)} data-kind="open" data-id="${o.id}" data-who="${o.who}">
    <span class="kind" title="${esc(o.who === "panel" ? "The panel could not settle this: it is a limit of the debate that produced the call, not a task." : "Only you can settle this: the system cannot perform this verb for itself.")}">?</span>
    <span class="line">${o.line}</span>
    <span class="marks">${o.marks || ""}</span>
    ${stateHtml(o.cls, o.word, o.why)}
    <span class="verb">${o.verb ? `<button class="btn quiet" title="${esc(o.verb.title)}" onclick="event.stopPropagation(); jumpUnit(${jsArg(o.verb.unit)})">${esc(o.verb.label)}</button>` : ""}</span>
    ${openId === id ? `<div class="detail"><div class="prose">${o.detail}</div></div>` : ""}</div>`;
}
// The open questions, derived. Two authors: what the PANEL could not settle about the call
// that stands, and what only YOU can settle across the stores.
function briefOpen(S) {
  const out = [], ds = [...S.decisions].sort((a, b) => b.ts - a.ts), st = ds[0];
  if (st) {
    const u = units(hist()).find(x => x.moderator && Math.abs(x.moderator.ts - st.ts) < 5);
    const seeCall = { label: "see the call", unit: `decision-${st.ts}`, title: "Open the standing call above." };
    if (!u) {
      out.push({ id: "chairs-gone", who: "panel", cls: "", word: "not recoverable",
        line: `Which chairs reported to the standing call is <b>not on record here</b>`,
        why: "The transcript for that verdict is not in the current chat history -- compacted, or from before it. Missing information, never a finding that all three reported.",
        detail: "decision_log stores no message key: a verdict's ts lands within a second of the Moderator message's, which is the only join. Once a compaction summarises that message away, which chairs reported becomes unrecoverable from the log alone.", verb: seeCall });
    } else if (u.kind === "debate") {
      const r = reached(u);
      if (r.n < r.of) {
        const missing = chairs(u).filter(c => c.status !== "reported").map(c => PAYLOAD.roleNames[c.role]);
        out.push({ id: "chairs", who: "panel", cls: "attn", word: `${r.n} of ${r.of} chairs`,
          line: `The standing call rests on <b>${r.n} of ${r.of} chairs</b> <span class="q">— no report reached the panel from ${esc(missing.join(" and "))}</span>`,
          marks: chairs(u).filter(c => c.status !== "reported").map(seatHtml).join(""),
          why: `${missing.join(" and ")} sent no report. Whether the call never ran, ran and was lost, or ran and could not be read is not known here.`,
          detail: "A chair that sent no report is missing information, never a chair with nothing to say. The verdict was written on the two that did report and does not say so in its own block.", verb: seeCall });
      }
    }
    const cv = (st.conviction || "").toLowerCase();
    if (!st.conviction) out.push({ id: "conv", who: "panel", cls: "", word: "not recorded",
      line: `The standing call's conviction ${absent("The Moderator's block carried no CONVICTION line, so how firmly the panel held this call is not on record.")} <span class="q">— the block carried no CONVICTION line</span>`,
      why: "The prompt requires a CONVICTION line; this block has none. Not recorded is not the same as unanimous.", detail: "llm_engine.parse_moderator_verdict is per-field: a block missing a required line is still logged, with that field absent.", verb: seeCall });
    else if (CONV[cv] && CONV[cv][2]) out.push({ id: "conv", who: "panel", cls: "attn", word: cv,  // stateHtml escapes; escaping here too would double it
      line: `The standing call is <b>${esc(st.conviction)}</b> <span class="q">— ${esc(CONV[cv][1].replace(/^[^:]*: /, ""))}</span>`,
      why: CONV[cv][1], detail: esc(CONV[cv][1]), verb: seeCall });
    if (st.dissent) out.push({ id: "dissent", who: "panel", cls: "attn", word: "dissent",
      line: `A chair dissented from the standing call <span class="q">— ${trunc(st.dissent, 90)}</span>`, marks: dissentSeat(st),
      why: `DISSENT — ${st.dissent}`, detail: `${esc(st.dissent)}<br><br>The Decision Log's table has ten columns and this is not one of them: dissent is stored on every row and shown on none.`, verb: seeCall });
    if (st.recon) out.push({ id: "recon", who: "panel", cls: "attn", word: "recon",
      line: `The call turns on something only another manager can tell you <span class="q">— ${trunc(st.recon, 90)}</span>`,
      why: `RECON — ${st.recon}`, detail: `${esc(st.recon)}<br><br>RECON is the panel naming a question it cannot answer from any data it has. Nothing in the group tracks whether you asked.`, verb: seeCall });
  }
  const n = needsYou(S);
  if (n.unrated) { const first = ds.filter(d => !d.outcome).slice(-1)[0];
    out.push({ id: "unrated", who: "you", cls: "needs", word: "unrated",
      line: `<b>${n.unrated} verdict${n.unrated === 1 ? "" : "s"}</b> ${n.unrated === 1 ? "has" : "have"} no outcome <span class="q">— until rated, ${n.unrated === 1 ? "it teaches" : "they teach"} the next debate nothing</span>`,
      why: "search_decisions_with_outcomes excludes an unrated verdict entirely: rating is what turns the log into a track record.",
      detail: "The rating control is on each verdict in question 1, one per row, with no default -- a same-day re-run is rated on its own timestamp.", verb: { label: "rate the oldest", unit: `decision-${first.ts}`, title: "Open the oldest unrated verdict." } }); }
  if (n.proposed) { const t = S.todos.find(x => x.status === "likely_resolved");
    out.push({ id: "proposed", who: "you", cls: "needs", word: "proposed done",
      line: `<b>${n.proposed} objective${n.proposed === 1 ? "" : "s"}</b> a bot proposed as done <span class="q">— only you close one</span>`,
      why: "A bot may open, revise or propose an objective done. Confirming or keeping it open is the one verb the system cannot perform for itself.",
      detail: "The app counts these inside “Active Objectives (N)”, so a proposed-done objective is presented to you, to the dock header and to the bots as still active.", verb: { label: "see it", unit: `objective-${t.id}`, title: "Open the proposed-done objective in question 4." } }); }
  if (n.awaiting) { const f = S.findings.find(x => findingFeeds(x).cls === "needs");
    out.push({ id: "awaiting", who: "you", cls: "needs", word: "awaiting you",
      line: `<b>${n.awaiting} finding${n.awaiting === 1 ? "" : "s"}</b> ${n.awaiting === 1 ? "has a number" : "have numbers"} held back <span class="q">— confirming says you looked, not that it is verified</span>`,
      why: "A rank from an allowed source counts toward the composite only after a second pair of eyes. Until then the number is out of the score.",
      detail: "Recomputed from each row the way bot_research.feeds_composite does -- never read from the stored composite_impact string, which is a record of an older decision.", verb: { label: "see them", unit: `finding-${f.id}`, title: "Open the first held-back finding in question 2." } }); }
  if (n.orphans) { const ts = S.pinned.find(x => !pinMessage(x));
    out.push({ id: "orphans", who: "you", cls: "needs", word: "message gone",
      line: `<b>${n.orphans} pin${n.orphans === 1 ? "" : "s"}</b> outlived ${n.orphans === 1 ? "its" : "their"} message <span class="q">— a compaction summarised it away</span>`,
      why: "compact_chat_history does not consult the pin store. The pin remains; the message it points at cannot be retrieved by anything.",
      detail: "The app's own panel simply does not list these and does not count them, so the header says two pins where three are stored.", verb: { label: "see it", unit: `pin-${ts}`, title: "Open the orphaned pin in question 2." } }); }
  return out;
}
function render() {
  const S = stores(), n = needsYou(S), i0 = { i: 0 };
  const ds = [...S.decisions].sort((a, b) => b.ts - a.ts);
  const anything = S.decisions.length + S.todos.length + S.findings.length + S.comparisons.length + S.pinned.length;
  document.getElementById("asof").innerHTML = anything
    ? `as of ${new Date(NOW * 1000).toISOString().slice(0, 16).replace("T", " ")} UTC`
    : `${absent("Every store is empty: no verdict logged, no objective opened, nothing pinned, nothing found. The next debate is handed nothing but the transcript.")} nothing on record`;

  // 1 -- WHAT WAS DECIDED
  const rated = ds.filter(d => d.outcome).length, unrated = ds.length - rated;
  const st = ds[0];
  const a1 = st
    ? `The call that stands is ${decisionRec(st)} ${decisionConv(st)} <span class="q">to</span> ${trunc(st.question, 78)}, ${ago(st.ts)}. `
      + `<b>${ds.length}</b> call${ds.length === 1 ? "" : "s"} on record — ${rated ? `<b>${rated}</b> rated` : "<b>none</b> rated"}, `
      + (unrated ? `<span class="needs">${unrated} not</span>. A past call reaches the next debate only when the question relates <b>and</b> you have rated it.` : "all of them rated, so every related one can reach the next debate.")
    : `${absent("No Moderator verdict has been logged in this league. A verdict is logged when the Moderator's reply carries its closing block; nothing here has one.")} <b>Nothing has been decided on the record.</b> The transcript may hold calls the log does not: a block missing every field is not logged at all.`;
  // 2 -- WHY
  const fs = S.findings, counting = fs.filter(f => findingFeeds(f).feeds).length;
  const reasons = new Set(fs.filter(f => !findingFeeds(f).feeds).map(f => findingFeeds(f).word));
  const a2 = (fs.length + S.comparisons.length + S.pinned.length)
    ? `<b>${fs.length}</b> panel-vetted finding${fs.length === 1 ? "" : "s"} and <b>${S.comparisons.length}</b> comparison${S.comparisons.length === 1 ? "" : "s"} are read by every debate, in <b>every league</b>, alongside <b>${S.pinned.length}</b> message${S.pinned.length === 1 ? "" : "s"} you kept. `
      + `Of the numbers, ${counting ? `<b>${counting}</b> count${counting === 1 ? "s" : ""} toward the composite` : "<b>none</b> counts toward the composite"}; the rest do not, for <b>${reasons.size}</b> different reason${reasons.size === 1 ? "" : "s"} — the state word on each row says which, recomputed from the row.`
    : `${absent("No finding, no comparison and no pinned message is on record, so nothing here says why any call was made except the Moderator's own prose inside each verdict.")} <b>The system holds no evidence of its own.</b> The reasoning lives only inside the verdicts above.`;
  // 3 -- WHAT REMAINS UNCERTAIN
  const opens = briefOpen(S);
  const byPanel = opens.filter(o => o.who === "panel"), byYou = opens.filter(o => o.who === "you");
  const a3 = opens.length
    ? `<b>${opens.length}</b> thing${opens.length === 1 ? "" : "s"} ${opens.length === 1 ? "is" : "are"} unsettled: `
      + `${byPanel.length ? `<b>${byPanel.length}</b> the panel could not settle` : "<b>none</b> the panel could not settle"}, `
      + `${byYou.length ? `<span class="needs"><b>${byYou.length}</b> only you can</span>` : "<b>none</b> only you can"}. `
      + `This is the one question the app gives no surface at all: conviction, dissent, RECON and which chairs reported reach the reader only in the dock, and only for the standing call.`
    : `${absent("Nothing is on record, so nothing is unsettled on record either. That is not the same as a settled system.")} <b>Nothing is on record to be uncertain about.</b>`;
  // 4 -- WHAT IT IS OPTIMISING
  const live = S.todos.filter(t => ["active", "likely_resolved"].includes(t.status)).sort((a, b) => (b.status === "likely_resolved") - (a.status === "likely_resolved") || b.ts - a.ts);
  const closed = S.todos.filter(t => ["resolved", "dismissed"].includes(t.status)).sort((a, b) => b.ts - a.ts);
  const a4 = `${absent("No store in this system holds what the team is optimising. league_prefs holds display order; the draft engine's contend/rebuild mode is a per-view control, not a stored target. The engine chain has no objective link and the UI chain's is filled by something else.")} `
    + `<b>Nothing on record says what this team is optimising.</b> `
    + (live.length
        ? `The nearest answer is <b>${live.length}</b> open objective${live.length === 1 ? "" : "s"} — ACTION ITEMs a verdict set and you have not closed: a specific trade to propose, a claim to submit, a manager to ask. Tasks, not a target.`
        : `Not one objective is open either, so the nearest answer is empty too. An objective is a task a verdict set, never a target.`);

  let i = 0;
  const html = [
    qsec("decided", "1", "What was decided", `${tally(ds.length, "verdict")}`, a1,
      ds.map(d => decisionRow(d, i++, { joins: false })),
      "no verdicts logged", "No Moderator verdict has been logged in this league. One is logged whenever the Moderator's reply carries its closing block.",
      "A row opens to the Moderator's own prose and the receipt, DISSENT included, and to the rating control — no default, one per timestamp, so a same-day re-run is rated on its own. What each call opened and produced is not here: those answer questions 2 and 4."),
    qsec("why", "2", "Why", `${tally(fs.length + S.comparisons.length, "signal")} · ${qty(S.pinned.length)} kept`, a2,
      [...fs.map(f => ["f", f]), ...S.comparisons.map(c => ["c", c]), ...S.pinned.map(ts => ["p", ts])]
        .sort((a, b) => (b[0] === "p" ? b[1] : b[1].ts) - (a[0] === "p" ? a[1] : a[1].ts))
        .map(([k, x]) => k === "f" ? findingRow(x, i++) : k === "c" ? comparisonRow(x, i++) : pinRow(x, i++)),
      "no evidence on record", "No finding, comparison or pinned message exists. The panel's reasoning survives only inside each verdict's own prose.",
      "This is a <b>signals gate</b>, not evidence for any one call: nothing joins a finding to the verdict it was surfaced in except the question text, and the store is global — a finding from another league is read here, and is marked as such."),
    qsec("unresolved", "3", "What remains uncertain", opens.length ? `${qty(byPanel.length)} the panel · ${qty(byYou.length)} you` : "nothing open", a3,
      opens.map(o => openRow(o, i++)),
      "nothing unresolved", "Nothing is on record, so no question about it is open.",
      "The only derived rows in the group: each exists because something is unsettled and disappears when it is settled. The verb on the right goes to the record it is about."),
    qsec("optimising", "4", "What it is optimising", `${qty(live.length)} open · ${qty(closed.length)} closed`, a4,
      [...live.map(t => objRow(t, i++)), ...(closed.length ? [`<div class="divider"><span class="eyebrow"><b>Closed</b></span><span class="sub">kept because a future debate is shown them, with their resolution note</span></div>`] : []), ...closed.map(t => objRow(t, i++))],
      "no objectives", "No objective is open or closed. ACTION ITEM lines in a verdict open them, or you can by hand.",
      "todo_log has a <b>decision_ts</b> slot and nothing writes it, so the join back to question 1 is by ACTION ITEM text: rename an objective and it breaks. The opened row says which verdict it came from, or that the verdict is not in the log."),
  ].join("");
  document.getElementById("brief").innerHTML = html;
  wire(document.getElementById("group"));
}
"""

VARIANTS = [
    dict(
        slug="panels_1_calls", title="P1 · Calls", tagline="one surface; the unit is the verdict and the row is the chain",
        purpose="What the next debate will be handed, organised by the thing that produced it: a verdict. Every objective, finding and rating on record came out of one, so the ledger of verdicts IS the memory, and a row answers the test in one line — what was decided (call, conviction), why (REASON, in the receipt), what remains (which chairs reported, who dissented, RECON, RISK), what it set out to do (the objective it opened, with that objective's state and verb inline) and how it played out (your rating, with no default).",
        structure="One list, newest first, one row per verdict; chips for need-you / open objectives / rated. A row opens to the Moderator's prose, the receipt with DISSENT restored, the objective and findings it produced with their verbs, and the rating control. A single tail, 'Not from a verdict', holds what has no call to hang on and says why: hand-written objectives, findings from other leagues or from before the gate, pins on a chair's report, a pin whose message is gone.",
        earns="Verdicts: the decision link, and (rated) the proof link. Objectives: earn their place ONLY as the verdict's ACTION ITEM carried forward — as rows in the tail they are a to-do list. Findings: shown as what they are, a signals gate hung on the debate that produced them; the confirm/retract verb sits in the row. Pins: a mark on the verdict; a pinned chair report is a transcript feature and sits in the tail.",
        sacrifices="The stores' own kinds are gone as panels: 'all my objectives' is a filter, not a list, and a finding from another league is a tail row rather than a research table. The joins are by text and date (ACTION ITEM ↔ objective text; question ↔ finding.question), because todo_log's decision_ts is never written and findings carry no decision key — a renamed objective or a re-asked question breaks the join, and the page says so where it happens. Comparisons have no verb and little to say in a row.",
        css=CALLS_CSS, html=CALLS_HTML, js=SHARED_JS + CALLS_JS,
    ),
    dict(
        slug="panels_2_standing", title="P2 · Standing / Record", tagline="a governed group in two tiers by when the panel reads them, under one frame",
        purpose="The same memory, kept in its five kinds, but governed: one frame, one header grammar (name · count that says what it counts · what needs you · when the panel reads it), and a strip at the top that owns the link nothing else does — what remains uncertain and what only you can settle: the newest call's conviction and chairs, unrated verdicts, proposed-done objectives, findings awaiting confirmation, pins without a message.",
        structure="STANDING (open by default): Objectives and Findings, the two stores handed to every debate whether or not the question is about them. RECORD (closed by default): Verdicts, Closed objectives, Pins — handed to a debate only when the question relates, and a verdict only once rated. Each panel is one row grammar; a row opens to its detail and its verbs; delete is dashed and two presses, in the detail.",
        earns="Objectives: the closest thing to the UI's 'objective' link, and the frame says plainly that they are tasks (ACTION ITEMs), not the target the engine optimises — no store holds that. Findings: labelled as a signals gate, global, feeding the composite, not evidence for any one call; the frame notes they could as well live beside the sidebar's valuation sources. Verdicts: decision + proof, with DISSENT back in the receipt and the rating per row by timestamp. Closed objectives: the objective link's past tense, with the note a future debate is told. Pins: kept, demoted to the record tier, and told the truth about compaction.",
        sacrifices="Still five headers and a rule to learn (the two tiers). A verdict and the objective it opened live in different tiers, joined only by a sentence in the opened row. A reader who wants the chain for one decision must open the verdict, then find its objective above. The strip repeats counts the headers also carry.",
        css=STANDING_CSS, html=STANDING_HTML, js=SHARED_JS + STANDING_JS,
    ),
    dict(
        slug="panels_3_brief", title="P3 · Brief", tagline="the four questions the test asks, in that order; the fourth has no store behind it and says so",
        purpose="Answer the test literally. The group is not organised by store (P2) or by the verdict that produced each record (P1) but by the four questions a reader actually arrives with — what was decided, why, what remains uncertain, what it is optimising. Each question is answered first in one sentence, computed from the stores, and only then by the records that sentence rests on. Every record in all four stores appears in exactly one section: the section whose question it answers.",
        structure="Four numbered sections, none of them collapsible — the brief is a document, not a set of drawers. 1 What was decided: every verdict, newest first, with the rating control. 2 Why: findings, comparisons and pinned messages together as one body of evidence, labelled as the signals gate it is. 3 What remains uncertain: the only DERIVED rows in the group — one per open question, split by author into what the panel could not settle (chairs that sent no report, dissent, RECON, conviction below majority) and what only you can settle (unrated calls, proposed-done objectives, held-back numbers, orphaned pins), each with a verb that jumps to the record it is about. 4 What it is optimising: opens with an explicit absence, because no store holds it, then the open and closed objectives as the nearest available answer, labelled as tasks rather than a target.",
        earns="A section earns its place by being a question a reader has; a record earns its place by answering one. Verdicts answer 'what was decided' and nothing else here. Findings, comparisons and pins answer 'why' as one body — the reader never has to know they came from three stores. The uncertainty rows earn their place by existing nowhere else in the product: the app has no surface for conviction, dissent, RECON or a missing chair outside the dock. And question 4 earns its place by being ANSWERED WITH AN ABSENCE: the page states that nothing on record says what the team is optimising, rather than letting a to-do list stand in for a target.",
        sacrifices="The tallest of the three, and it cannot be shortened by collapsing — everything is at rest. One verdict's own chain is split across three sections: the call in 1, its findings in 2, its objective in 4, joined only by the uncertainty rows' verbs and by a sentence in each opened row. A reader who wants 'everything about this decision' is worse off here than in P1. The answer sentences are computed prose, so they restate counts the sections also carry, and they are the part most likely to go stale if a store gains a state nobody thought about. Comparisons and pins sit under 'why' by argument, not because either store knows anything about a call.",
        css=BRIEF_CSS, html=BRIEF_HTML, js=SHARED_JS + BRIEF_JS,
    ),
]
