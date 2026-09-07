"""Shared pieces for the Debate Dock mockups: tokens from design_system (never a second copy),
the constructed transcript (dock_data), the page shell that stands in for the app (a sidebar
placeholder and a page of faux content, so the dock is measured at the width and over the
ground it really has: 1,000px wide beside a 400px sidebar at 1,400), and the JS that turns
app.append_message rows into the units every variant renders.

WHAT THE JS FIXES THAT THE APP GETS WRONG, so the variants do not inherit the defects the
baseline probe measured (scratchpad/asis_measure*.json):
  - the STANDING verdict is the newest Moderator message that CARRIES a block, not the newest
    Moderator message (app.py:6127 reads only the latter, so a conversational follow-up hides
    the call the collapsed dock exists to show);
  - a chair's markdown is rendered by ONE renderer over the WHOLE message (app.py:6508 wraps
    the escaped text in a <div> and hands it to st.markdown, so CommonMark's HTML-block rule
    leaves the first paragraph literal and parses the rest);
  - a failed chair ("⚠️ ..." content, llm_engine's fail-soft string) is a labelled ABSENCE with
    a title, never a report with a model badge claiming authorship of a 503.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import design_system as ds  # noqa: E402
import common  # noqa: E402  the Draft Room's shared base (tokens, absent mark, spec card)
import dock_data  # noqa: E402


def role_css() -> str:
    """Seat glyphs and rails per chair, derived from the same tokens as design_system's badges:
    text = the token's -b brightening, border = the base token, tint = base at 0.18."""
    out = []
    for sel, tok in (("quant", "emerald"), ("beat", "cliff"), ("contrarian", "violet"), ("moderator", "crimson"),
                     ("user", "tie"), ("summary", "sky"), ("notice", "amber")):
        out.append(f'.seat[data-role="{sel}"], .msg[data-role="{sel}"] > .mh .seat {{ color: {ds.TOKENS[tok + "-b"]}; border-color: {ds.TOKENS[tok]}; background: {ds.token_rgba(tok, 0.18)}; }}')
        out.append(f'.msg[data-role="{sel}"] {{ --rail: {ds.TOKENS[tok]}; }}')
        out.append(f'.tab[data-role="{sel}"][aria-selected="true"] {{ border-bottom-color: {ds.TOKENS[tok + "-b"]}; color: {ds.TOKENS[tok + "-b"]}; }}')
    return "\n".join(out)


DOCK_CSS = f"""
{common.BASE_CSS}
{ds.BADGE_ROLE_CSS}
{common.REDUCED_MOTION_CLASS_CSS}
{role_css()}
body {{ font-size: 14px; overflow-x: hidden; }}
/* The stand-in for the app: a 400px sidebar and a page of faux blocks. The dock is fixed over
   it exactly as .st-key-debate_dock is (left: sidebar width, right: 0, bottom: 0). */
.app {{ display: grid; grid-template-columns: 400px minmax(0, 1fr); min-height: 100vh; }}
html[data-sidebar="off"] .app {{ grid-template-columns: 0 minmax(0, 1fr); }}
html[data-sidebar="off"] .side {{ display: none; }}
html[data-sidebar="off"] .dock {{ left: 0; }}
.side {{ background: var(--surface-2); border-right: 1px solid var(--line); padding: 1.2rem; }}
.side .ph, .main .ph {{ border: 1px solid var(--line); border-radius: 8px; background: color-mix(in srgb, var(--surface) 70%, transparent); color: var(--dim); font-size: .78rem; padding: .5rem .8rem; margin-bottom: .6rem; }}
.main {{ padding: 1.4rem 5.7rem 0; }}
.main .banner {{ border: 1px solid var(--line); border-radius: 10px; padding: 1rem 1.4rem; margin-bottom: .6rem; background: var(--surface-2); }}
.main .banner .eyebrow {{ font-size: .72rem; letter-spacing: .09em; text-transform: uppercase; color: var(--tie-b); font-weight: 600; }}
.main .banner h1 {{ margin: .1rem 0 .2rem; font-size: 2rem; }}
.main .banner .sub {{ color: var(--muted); font-size: .84rem; }}
.tabs {{ display: flex; gap: 0; border: 1px solid var(--line-2); border-radius: 8px; overflow: hidden; width: max-content; margin: .6rem 0 1rem; }}
.tabs span {{ padding: .5rem .9rem; font-size: .84rem; color: var(--muted); border-right: 1px solid var(--line-2); }}
.tabs span:last-child {{ border-right: 0; }}
.tabs span.on {{ color: var(--ink); background: var(--surface); }}
/* Padding-bottom = the dock's cap, as the app does with [data-testid='stMain']. */
html[data-level="collapsed"] .main {{ padding-bottom: max(9vh, 64px); }}
html[data-level="partial"] .main {{ padding-bottom: 40vh; }}
html[data-level="full"] .main {{ padding-bottom: 94vh; }}

/* THE DOCK FRAME. The app's own: the four-stop hairline (flourish; gold allowed there), the
   line, the shadow, the caps per tier. overflow-y auto is kept so the instrument can SEE an
   overflow (dockScrollHeight > clientHeight); a variant that scrolls the whole dock has
   failed, and only its designated .scroll region may scroll. */
.dock {{ position: fixed; left: 400px; right: 0; bottom: 0; z-index: 9; box-sizing: border-box;
  background: linear-gradient(90deg, var(--emerald), var(--gold), var(--violet), var(--crimson)) top / 100% 2px no-repeat, var(--bg);
  border-top: 1px solid var(--line); box-shadow: 0 -4px 16px rgba(0,0,0,.45);
  padding: 8px 24px 10px; overflow-y: auto; display: flex; flex-direction: column; gap: .45rem;
  transition: left {ds.TRANSITION_FAST}, max-height {ds.TRANSITION_EXPAND}; }}
html[data-level="collapsed"] .dock {{ max-height: max(9vh, 64px); }}
html[data-level="partial"] .dock {{ max-height: 40vh; }}
html[data-level="full"] .dock {{ max-height: 94vh; }}
.dock .scroll {{ overflow-y: auto; min-height: 0; }}
/* The floating harness: level, sidebar, the history cut, reduced motion. Not part of the dock. */
.harness {{ position: fixed; top: .5rem; right: .8rem; z-index: 20; display: flex; gap: .4rem; flex-wrap: wrap; justify-content: flex-end; }}
.harness button {{ font-family: {ds.FONT_MONO}; font-size: .7rem; letter-spacing: .04em; text-transform: uppercase; background: var(--surface); color: var(--muted); border: 1px solid var(--line-2); border-radius: 6px; padding: .28rem .6rem; cursor: pointer; }}
.harness button[aria-pressed="true"] {{ color: var(--ink); border-color: var(--ink); }}

/* Shared vocabulary inside the dock. */
.eyebrow {{ font-family: {ds.FONT_MONO}; font-size: .7rem; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }}
.eyebrow b {{ color: var(--ink); font-weight: 600; }}
.wordmark {{ font-family: {ds.FONT_DISPLAY}; letter-spacing: .1em; font-size: .9rem; color: var(--ink); text-transform: uppercase; }}
.mono {{ font-family: {ds.FONT_MONO}; }}
.seat {{ display: inline-grid; place-items: center; width: 1.35rem; height: 1.35rem; border-radius: 4px; border: 1px solid; font-family: {ds.FONT_MONO}; font-size: .7rem; font-weight: 700; cursor: help; flex: none; }}
.seat.failed {{ color: var(--muted); border-style: dashed; background: repeating-linear-gradient(135deg, transparent 0 3px, color-mix(in srgb, var(--line-2) 75%, transparent) 3px 4px); }}
.seat.silent {{ color: var(--dim); border-color: var(--line-2); background: transparent; }}
.seats {{ display: inline-flex; gap: .22rem; align-items: center; }}
/* The recommendation is a WORD, weighted by size and never coloured: four values would need
   four hues. Conviction is a ladder of glyphs; below Majority it takes the one signal hue. */
.rec {{ font-family: {ds.FONT_MONO}; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ink); }}
.conv {{ font-family: {ds.FONT_MONO}; font-size: .74rem; color: var(--ink); cursor: help; white-space: nowrap; }}
.conv i {{ font-style: normal; letter-spacing: .12em; margin-right: .3em; }}
.conv.low {{ color: var(--amber-b); }}
.attn {{ color: var(--amber-b); }}
.age {{ font-family: {ds.FONT_MONO}; font-size: .7rem; color: var(--muted); white-space: nowrap; cursor: help; }}
.q {{ color: var(--ink); }}
.trunc {{ cursor: help; }}
.mark {{ font-family: {ds.FONT_MONO}; font-size: .7rem; letter-spacing: .05em; text-transform: uppercase; color: var(--muted); border: 1px solid var(--line-2); border-radius: 3px; padding: .04rem .34rem; cursor: help; white-space: nowrap; }}
.mark.on {{ color: var(--ink); border-color: var(--ink); }}
/* Buttons: primary is gold (user action, the one non-brand job gold has), label in bg. */
.btn {{ font-family: {ds.FONT_SANS}; font-size: .8rem; font-weight: 600; border: 1px solid var(--line-2); background: var(--surface); color: var(--ink); border-radius: 7px; padding: .38rem .8rem; cursor: pointer; white-space: nowrap; }}
.btn.primary {{ background: var(--gold); border-color: var(--gold); color: var(--bg); font-weight: 700; }}
.btn.quiet {{ color: var(--muted); font-weight: 500; }}
.btn.icon {{ padding: .3rem .5rem; font-family: {ds.FONT_MONO}; }}
.btn:hover {{ border-color: var(--ink); }}
textarea.ask {{ width: 100%; box-sizing: border-box; background: var(--surface); color: var(--ink); border: 1px solid var(--line-2); border-radius: 7px; padding: .5rem .7rem; font-family: {ds.FONT_SANS}; font-size: .86rem; resize: none; }}
textarea.ask::placeholder {{ color: var(--dim); }}
/* Prose: one renderer, one style, the whole message. */
.prose {{ font-size: .86rem; line-height: 1.5; color: var(--ink); }}
.prose p {{ margin: 0 0 .45rem; }}
.prose p:last-child {{ margin-bottom: 0; }}
.prose ul {{ margin: 0 0 .45rem; padding-left: 1.1rem; }}
.prose li {{ margin: 0 0 .12rem; }}
.prose b {{ font-weight: 700; }}
.prose.clamp {{ display: -webkit-box; -webkit-box-orient: vertical; overflow: hidden; }}
/* The receipt: the Moderator's block as labelled fields. */
.receipt {{ display: grid; grid-template-columns: auto minmax(0, 1fr); gap: .2rem .8rem; align-items: baseline; font-size: .84rem; }}
.receipt .k {{ font-family: {ds.FONT_MONO}; font-size: .7rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); white-space: nowrap; }}
.receipt .v {{ color: var(--ink); min-width: 0; }}
.receipt .v .absent {{ font-size: .8rem; }}
.extra {{ font-family: {ds.FONT_MONO}; font-size: .7rem; color: var(--muted); }}
.extra div {{ margin-top: .15rem; }}
/* An absent report: a card-sized labelled absence, not a message. */
.absent-report {{ border: 1px dashed var(--line-2); border-radius: 8px; padding: .55rem .8rem; color: var(--muted); font-size: .8rem;
  background: repeating-linear-gradient(135deg, transparent 0 6px, color-mix(in srgb, var(--line) 55%, transparent) 6px 7px); }}
.absent-report b {{ color: var(--ink); font-weight: 600; }}
.fold {{ font-family: {ds.FONT_MONO}; font-size: .7rem; color: var(--muted); border: 1px dashed var(--line-2); border-radius: 6px; padding: .3rem .7rem; text-align: center; cursor: pointer; }}
.fold:hover {{ color: var(--ink); }}
[role="option"] {{ cursor: pointer; }}
"""


HARNESS_HTML = """
<div class="harness" aria-label="mockup harness">
  <button id="lv-collapsed" onclick="setLevel('collapsed')">collapsed</button>
  <button id="lv-partial" onclick="setLevel('partial')">partial</button>
  <button id="lv-full" onclick="setLevel('full')">full</button>
  <button id="btn-sidebar" aria-pressed="true" onclick="toggleSidebar(this)">sidebar 400px</button>
  <button id="btn-cut" aria-pressed="false" onclick="toggleCut(this)" title="Cut the history after the Moderator's block-less follow-up (8 messages): the standing verdict must still be the BUY two messages up.">history cut at follow-up</button>
  <button id="btn-motion" aria-pressed="false" onclick="toggleMotion(this)">reduced motion</button>
</div>
"""

PAGE_BEHIND = """
<div class="app">
  <aside class="side" aria-hidden="true">
    <div class="ph">Activity Log (0)</div><div class="ph">Connections &amp; Models</div><div class="ph">Roles &amp; Routing</div><div class="ph">Data Uploads</div><div class="ph">External Valuation Sources</div>
    <div class="ph" style="margin-top:2rem">Status · Data Freshness: Recent</div>
  </aside>
  <div class="main">
    {spec}
    <div class="banner"><div class="eyebrow">Fantasy Football Command Center</div><h1>Gold Wyrm Dynasty</h1><div class="sub">Dynasty · 12-team · Superflex · Full PPR · Taxi: 4</div></div>
    <div class="tabs"><span class="on">Matchup</span><span>Roster Maintenance</span><span>Draft Room</span><span>League</span><span>Import Audit</span></div>
    <div class="ph" style="height:3rem">Lineup Readiness</div>
    <div class="ph" style="height:2.4rem">Pinned Messages (1)</div>
    <div class="ph" style="height:14rem">Active Objectives (2)</div>
    <div class="ph" style="height:22rem">Roster by position</div>
    <div class="ph" style="height:22rem">Projections</div>
  </div>
</div>
"""

SPEC_HTML = """
<details class="spec">
  <summary><span class="k">Variant</span> <b>{title}</b> — {tagline} <span class="hint">· open for the hierarchy argument, sacrifice and data</span></summary>
  <div class="specbody">
  <span class="k">Collapsed</span><span>{collapsed}</span>
  <span class="k">Partial</span><span>{partial}</span>
  <span class="k">Full</span><span>{full}</span>
  <span class="k">Sacrifices</span><span>{sacrifices}</span>
  <span class="k">Data</span><span>One league's chat history in app.append_message's own shape (14 rows: a memory summary, two Full Prytaneum runs, a block-less follow-up, a stale-data notice), constructed because no history is stored in this tree; the attached context is the real Draft Room seed for pick 3.03. The second run's Beat chair is llm_engine's own fail-soft string, so the panel that produced the standing WAIT verdict was two chairs of three. Two objectives are open, one of them the first verdict's ACTION ITEM; the first verdict is pinned.</span>
  </div>
</details>
"""

BASE_JS = r"""
const ABSENT = "—";
const ROLE_WORD = { quant: "Quant", beat: "Beat Tracker", contrarian: "Contrarian", moderator: "Moderator", user: "You", summary: "Memory summary", notice: "Notice" };
const ROLE_LETTER = { quant: "Q", beat: "B", contrarian: "C", moderator: "M" };
const ROLE_JOB = { quant: "numbers: VORP, scarcity, trade math", beat: "market consensus and news, via live search", contrarian: "pressure-tests the other two", moderator: "synthesises the three reports into one verdict" };
const CHAIRS = ["quant", "beat", "contrarian"];
const FIELDS = PAYLOAD.verdictFields;
const FIELD_KEY = f => f.toLowerCase().replace(/ /g, "_");
const CONV = { unanimous: ["●●●", "Unanimous: all three chairs land the same direction.", false],
               majority: ["●●○", "Majority: two chairs agree, one dissents — DISSENT names who and why.", false],
               split: ["●○○", "Split: no real consensus among the three.", true],
               speculative: ["◌◌◌", "Speculative: the chairs may agree, but the evidence under them is thin.", true],
               "worth investigation": ["?", "Worth investigation: the answer depends on something only another manager can tell you — RECON says what to ask.", true] };
//: A fixed "now" so ages are stable: five hours after the newest row. Stated on the page.
const NOW = Math.max(...PAYLOAD.history.map(m => m.ts)) + 5 * 3600;
function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
function absent(why) { return `<span class="absent" title="${esc(why)}">${ABSENT}</span>`; }
function ago(ts) {
  const s = NOW - ts, d = new Date(ts * 1000).toISOString().slice(0, 16).replace("T", " ");
  const w = s < 90 ? "just now" : s < 3600 ? `${Math.round(s / 60)}m ago` : s < 86400 ? `${Math.round(s / 3600)}h ago` : `${Math.round(s / 86400)}d ago`;
  return `<span class="age" title="${d} UTC">${w}</span>`;
}
function trunc(s, n) {
  s = String(s).replace(/\s+/g, " ").trim();
  if (s.length <= n) return esc(s);
  const cut = s.slice(0, n).replace(/\s+\S*$/, "");
  return `<span class="trunc" title="${esc(s)}">${esc(cut)}…</span>`;
}
// ONE markdown renderer over the WHOLE message: paragraphs on blank lines, "- " bullets,
// **bold**. Escaped first. Nothing else is interpreted.
function md(text) {
  const blocks = String(text).trim().split(/\n\s*\n/);
  return blocks.map(b => {
    const lines = b.split("\n");
    if (lines.every(l => /^\s*[-*•]\s+/.test(l))) return `<ul>${lines.map(l => `<li>${inline(l.replace(/^\s*[-*•]\s+/, ""))}</li>`).join("")}</ul>`;
    return `<p>${lines.map(inline).join("<br>")}</p>`;
  }).join("");
}
function inline(s) { return esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>"); }
// The Moderator's block, parsed the way llm_engine.parse_moderator_verdict does (each labelled
// line at most once; TODO / SOURCE lines collected separately). Prose is everything before the
// first RECOMMENDATION: line, exactly app.format_agent_content's split.
function parseVerdict(text) {
  const m = /^RECOMMENDATION:/m.exec(text);
  if (!m) return { prose: text, fields: {}, extra: [], has: false };
  const prose = text.slice(0, m.index).trim(), block = text.slice(m.index);
  const fields = {}, extra = [];
  for (const raw of block.split("\n")) {
    const line = raw.trim().replace(/^[-*# ]+/, "");
    let hit = false;
    for (const f of FIELDS) { if (line.toUpperCase().startsWith(f + ":")) { const v = line.slice(f.length + 1).trim(); if (v && !(FIELD_KEY(f) in fields)) fields[FIELD_KEY(f)] = v; hit = true; break; } }
    if (!hit && /^(TODO UPDATE|TODO LIKELY RESOLVED|SOURCE FINDING|SOURCE COMPARISON):/i.test(line)) extra.push(line);
  }
  return { prose, fields, extra, has: true };
}
function failed(msg) { return msg.content.startsWith("⚠️"); }
function failText(msg) { return msg.content.replace(/^⚠️\s*/, ""); }
// Units: a Full Prytaneum run is exactly [quant, beat, contrarian, moderator]; the user line
// immediately before it is its question. A Moderator alone after a user line is a follow-up.
function units(history) {
  const out = []; let i = 0;
  while (i < history.length) {
    const r = history[i];
    if (i + 3 < history.length && ["quant", "beat", "contrarian", "moderator"].every((role, k) => history[i + k].role === role)) {
      const u = { kind: "debate", ts: history[i + 3].ts, quant: history[i], beat: history[i + 1], contrarian: history[i + 2], moderator: history[i + 3], question: null, followups: [] };
      takeQuestion(out, u); out.push(u); i += 4; continue;
    }
    if (r.role === "moderator") {
      const u = { kind: "followup", ts: r.ts, moderator: r, question: null };
      takeQuestion(out, u); out.push(u); i += 1; continue;
    }
    out.push({ kind: r.role === "user" ? "user" : r.role, ts: r.ts, msg: r }); i += 1;
  }
  return out;
}
// The user line that opened a run sits before it, possibly behind a notice: app.py appends the
// question, then maybe_nudge_stale_free_agents' notice, then the chairs. Look back past notices.
function takeQuestion(out, u) {
  for (let k = out.length - 1; k >= 0 && k >= out.length - 2; k--) {
    if (out[k].kind === "user") { u.question = out[k].msg; out.splice(k, 1); return; }
    if (out[k].kind !== "notice") return;
  }
}
// The standing verdict: the newest unit whose Moderator text CARRIES a block. A follow-up
// that re-emitted the block counts; one that only talked does not, and the earlier call stands.
function standing(us) {
  for (let k = us.length - 1; k >= 0; k--) { const u = us[k]; if (u.moderator && parseVerdict(u.moderator.content).has) return u; }
  return null;
}
function chairs(u) {
  if (u.kind !== "debate") return CHAIRS.map(r => ({ role: r, msg: null, status: "silent" }));
  return CHAIRS.map(r => ({ role: r, msg: u[r], status: failed(u[r]) ? "failed" : "reported" }));
}
function reached(u) { const cs = chairs(u); return { n: cs.filter(c => c.status === "reported").length, of: u.kind === "debate" ? 3 : 0 }; }
function seatHtml(c) {
  const name = PAYLOAD.roleNames[c.role];
  const t = c.status === "reported" ? `${name} · ${ROLE_JOB[c.role]} · reported (${c.msg.model || "model not recorded"})`
    : c.status === "failed" ? `${name}: no report reached the panel — ${failText(c.msg)}. Missing information, never a finding that there is nothing to report.`
    : `${name} was not asked: this was a Moderator-only follow-up.`;
  return `<span class="seat ${c.status}" data-role="${c.role}" data-status="${c.status}" title="${esc(t)}">${ROLE_LETTER[c.role]}</span>`;
}
function seatsHtml(u, withM) {
  let s = chairs(u).map(seatHtml).join("");
  if (withM) s += `<span class="seat" data-role="moderator" title="${esc(`Moderator · ${ROLE_JOB.moderator} (${u.moderator.model || "model not recorded"})`)}">M</span>`;
  return `<span class="seats">${s}</span>`;
}
function reachedHtml(u) {
  const r = reached(u); if (!r.of) return "";
  return r.n === r.of ? `<span class="mark" title="All three chairs reported to the Moderator.">3 of 3 chairs</span>`
    : `<span class="mark attn" title="${esc(`${r.of - r.n} chair${r.of - r.n === 1 ? "" : "s"} sent no report; the verdict rests on ${r.n} of ${r.of}. Named in the seats.`)}">${r.n} of ${r.of} chairs</span>`;
}
function convHtml(fields, big) {
  const c = fields.conviction; if (!c) return `<span class="conv">${absent("The Moderator's block carried no CONVICTION line.")}</span>`;
  const k = c.toLowerCase(), e = CONV[k];
  if (!e) return `<span class="conv" title="${esc(c)}">${esc(c)}</span>`;
  return `<span class="conv${e[2] ? " low" : ""}" title="${esc(e[1])}"><i>${e[0]}</i>${big ? esc(c) : esc(c.toLowerCase())}</span>`;
}
function recHtml(fields, cls) { return fields.recommendation ? `<span class="rec ${cls || ""}" data-fact="rec">${esc(fields.recommendation)}</span>` : `<span class="rec ${cls || ""}" data-fact="rec">${absent("The Moderator's block carried no RECOMMENDATION line.")}</span>`; }
function questionOf(u) { return u.question ? u.question.content : null; }
function modelOf(m) { return m.model ? esc(m.model) : absent("The model that answered was not recorded on this message; it is not the current default."); }
function objectiveFor(text) { return PAYLOAD.todos.find(t => t.status === "active" && t.text.trim() === String(text).trim()) || null; }
function pinned(m) { return PAYLOAD.pinned.includes(m.ts); }
// The receipt: fields present, in the block's own order; the four the prompt requires are
// shown as absent when missing, the optional ones are omitted (the prompt says omit, so an
// omitted optional line is the Moderator's own statement that it does not apply).
function receiptHtml(v, opts) {
  opts = opts || {};
  const req = ["recommendation", "conviction", "reason", "risk"], rows = [];
  for (const f of FIELDS) {
    const k = FIELD_KEY(f), val = v.fields[k];
    if (k === "recommendation" || k === "conviction") continue;
    if (val === undefined) { if (req.includes(k)) rows.push([f, absent(`The Moderator's block carried no ${f} line; the prompt requires one.`)]); continue; }
    let html = esc(val);
    if (k === "action_item") { const t = objectiveFor(val); html += t ? ` <span class="mark on" title="Tracked as objective #${t.id}, opened by this verdict.">→ objective #${t.id}</span>` : ` <span class="mark" title="Not found among the open objectives.">not tracked</span>`; }
    if (k === "dissent") { const who = /^(quant|beat|contrarian)/i.exec(val); if (who) html = `<span class="seat" data-role="${who[1].toLowerCase()}" style="width:1.2rem;height:1.2rem;font-size:.7rem;vertical-align:-3px;margin-right:.3rem">${ROLE_LETTER[who[1].toLowerCase()]}</span>` + html; }
    rows.push([f, html]);
  }
  const ex = v.extra.length && !opts.noExtra ? `<div class="extra">${v.extra.map(l => `<div title="${esc(l)}">${trunc(l, opts.extraChars || 140)}</div>`).join("")}</div>` : "";
  return `<div class="receipt">${rows.map(([k, h]) => `<span class="k">${k}</span><span class="v" data-field="${FIELD_KEY(k)}">${h}</span>`).join("")}</div>${ex}`;
}
function openObjectives() { return PAYLOAD.todos.filter(t => t.status === "active").length; }
function considering() {
  const a = PAYLOAD.attached; if (!a) return "";
  return `<span class="mark on" title="${esc(`${a.surface} · ${a.looking_at}\n${a.decision}\n${a.evidence}\nInvolved: ${a.entities.join(", ")}`)}">considering · ${esc(a.looking_at.replace(/\.$/, ""))} · ${a.entities.length} names</span>`;
}

// ---- state and harness -----------------------------------------------------------------
let level = "partial", openId = null, focusedId = null, tabOf = {}, cut = false;
function hist() { return cut ? PAYLOAD.history.slice(0, 8) : PAYLOAD.history; }
function setLevel(l) { level = l; document.documentElement.dataset.level = l; for (const x of ["collapsed", "partial", "full"]) document.getElementById("lv-" + x).setAttribute("aria-pressed", x === l); render(); }
function toggleSidebar(b) { const on = b.getAttribute("aria-pressed") !== "true"; b.setAttribute("aria-pressed", on); document.documentElement.dataset.sidebar = on ? "on" : "off"; }
function toggleCut(b) { cut = b.getAttribute("aria-pressed") !== "true"; b.setAttribute("aria-pressed", cut); openId = null; render(); }
function toggleMotion(b) { const on = b.getAttribute("aria-pressed") !== "true"; b.setAttribute("aria-pressed", on); document.documentElement.classList.toggle("reduced-motion", on); }
function levelBtns() {
  const up = level !== "full" ? `<button class="btn icon quiet" onclick="setLevel('${level === "collapsed" ? "partial" : "full"}')" title="Expand one tier">▲</button>` : "";
  const dn = level !== "collapsed" ? `<button class="btn icon quiet" onclick="setLevel('${level === "full" ? "partial" : "collapsed"}')" title="Collapse one tier">▼</button>` : "";
  return `<span class="levels">${up}${dn}</span>`;
}
function uid(u) { return `${u.kind}-${u.ts}`; }
function optAttrs(u, i) { const id = uid(u); return `role="option" data-unit="${id}" data-kind="${u.kind}" aria-expanded="${openId === id}" tabindex="${(focusedId ? focusedId === id : i === 0) ? 0 : -1}"`; }
function wire(root) {
  const opts = [...root.querySelectorAll('[role="option"]')];
  opts.forEach(el => {
    el.addEventListener("click", ev => { if (ev.target.closest("button, a, textarea, .tab")) return; openId = openId === el.dataset.unit ? null : el.dataset.unit; focusedId = el.dataset.unit; render(); });
    el.addEventListener("keydown", ev => {
      const k = opts.indexOf(el);
      if (ev.key === "ArrowDown" && opts[k + 1]) { ev.preventDefault(); focusedId = opts[k + 1].dataset.unit; opts[k + 1].focus(); opts[k].tabIndex = -1; opts[k + 1].tabIndex = 0; }
      else if (ev.key === "ArrowUp" && opts[k - 1]) { ev.preventDefault(); focusedId = opts[k - 1].dataset.unit; opts[k - 1].focus(); opts[k].tabIndex = -1; opts[k - 1].tabIndex = 0; }
      else if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); openId = openId === el.dataset.unit ? null : el.dataset.unit; focusedId = el.dataset.unit; render(); }
      else if (ev.key === "Escape" && openId) { ev.preventDefault(); openId = null; render(); }
    });
  });
  if (focusedId && (document.activeElement === document.body || root.contains(document.activeElement))) { const f = root.querySelector(`[data-unit="${focusedId}"]`); if (f && document.activeElement !== f) { opts.forEach(o => o.tabIndex = o === f ? 0 : -1); f.focus(); } }
}
function setTab(id, role) { tabOf[id] = tabOf[id] === role ? null : role; render(); const t = document.querySelector(`[data-unit="${id}"] .tab[data-role="${role}"]`); t && t.focus(); }
"""


def page(slug: str, title: str, tagline: str, args: dict, css: str, dock_html: str, js: str) -> str:
    spec = SPEC_HTML.format(title=title, tagline=tagline, **args)
    return f"""<!doctype html>
<html lang="en" data-level="partial" data-sidebar="on"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{common.esc_title(title)} — Debate Dock mockup</title>
<style>
{DOCK_CSS}
{css}
</style></head>
<body>
{HARNESS_HTML}
{PAGE_BEHIND.format(spec=spec)}
<div class="dock" id="dock" aria-label="The Prytaneum">{dock_html}</div>
<script>
const PAYLOAD = {common.safe_json(dock_data.payload())};
{BASE_JS}
{js}
setLevel("partial");
</script>
</body></html>
"""
