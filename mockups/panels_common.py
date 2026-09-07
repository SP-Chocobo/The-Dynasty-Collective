"""Shared pieces for the panel-group mockups: the Debate Dock's shell and tokens (dock_common,
never a second copy), the constructed stores (panels_data), a page that stands in for the app
with the four panels IN FLOW where app.py puts them -- under the view's content, above the
fixed dock, which is rendered collapsed so the group is measured over the ground and beside the
neighbour it really has -- and the JS that turns the stores' own rows into the units every
variant renders.

WHAT THE JS FIXES THAT THE APP GETS WRONG, so the variants do not inherit the defects the
baseline probe measured (panels_baseline_measure.json, and the defect list in panels_index):
  - a pin whose message is no longer in the chat (compaction does not consult the pin store)
    is a labelled absence, never silently dropped from a count that claims to be "pinned";
  - a pinned message is never cut at 500 characters without a mark; a pinned verdict shows
    its block, which is the part worth pinning;
  - a decision whose block carried no RECOMMENDATION line shows a hatched absence in the call
    slot, never a blank cell;
  - the rating control has NO default rating: unrated is the state until a person chooses,
    and each row is rated by its own timestamp, so a same-day re-run cannot collide;
  - a finding's "counts toward the composite" answer is RECOMPUTED from its fields, the way
    bot_research.feeds_composite does, never read from the stored composite_impact string;
  - delete is never a peer of done / dismiss;
  - "active" and "proposed done" are counted apart; a global store says it is global.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import design_system as ds  # noqa: E402
import common  # noqa: E402
import dock_common  # noqa: E402
import panels_data  # noqa: E402


PANELS_CSS = f"""
{dock_common.DOCK_CSS}
/* The panel group sits in the page's flow; the dock is collapsed beneath it. */
html[data-level="collapsed"] .main {{ padding-bottom: max(9vh, 64px); }}
.main {{ padding-top: 1.2rem; }}
.view {{ border: 1px solid var(--line); border-radius: 8px; background: color-mix(in srgb, var(--surface) 70%, transparent); color: var(--dim); font-size: .78rem; padding: .5rem .8rem; margin-bottom: .6rem; }}
.harness .lbl {{ font-family: {ds.FONT_MONO}; font-size: .66rem; color: var(--dim); align-self: center; letter-spacing: .06em; text-transform: uppercase; }}

/* THE GROUP FRAME. One frame for the whole group, so a reader meets one idea before four. */
.group {{ margin-top: 1rem; border-top: 1px solid var(--line-2); padding-top: .7rem; }}
.group-head {{ display: flex; align-items: baseline; gap: .9rem; flex-wrap: wrap; margin-bottom: .55rem; }}
.group-head .wordmark {{ font-size: .86rem; }}
.group-head .sub {{ color: var(--muted); font-size: .8rem; }}
.group-head .grow {{ flex: 1; }}
/* needs-you: the ONE UI-state hue on this surface (sky). Never used for a data signal. */
.needs {{ color: var(--sky-b); }}
.mark.needs {{ border-color: var(--sky); color: var(--sky-b); }}
.chip {{ font-family: {ds.FONT_MONO}; font-size: .68rem; letter-spacing: .05em; text-transform: uppercase; color: var(--muted); border: 1px solid var(--line-2); border-radius: 6px; padding: .22rem .6rem; background: var(--surface); cursor: pointer; white-space: nowrap; }}
.chip[aria-pressed="true"] {{ color: var(--ink); border-color: var(--ink); }}
.chip.needs[aria-pressed="true"] {{ color: var(--sky-b); border-color: var(--sky); }}
.chip .n {{ color: var(--dim); margin-left: .35em; }}
.chip[aria-pressed="true"] .n {{ color: var(--muted); }}
.chips {{ display: flex; gap: .4rem; flex-wrap: wrap; align-items: center; }}

/* A kind: a letter on a bordered box, like the dock's seats, in the ink -- kinds carry no hue.
   The AUTHOR seat beside it borrows the dock's own role tokens, so a row here and a bubble in
   the dock say "Moderator" the same way. */
.kind {{ display: inline-grid; place-items: center; min-width: 1.35rem; height: 1.35rem; padding: 0 .3rem; border-radius: 4px; border: 1px solid var(--line-2); font-family: {ds.FONT_MONO}; font-size: .66rem; font-weight: 700; letter-spacing: .04em; color: var(--muted); cursor: help; flex: none; }}
.kind.on {{ color: var(--ink); border-color: var(--ink); }}
.seat.you {{ color: var(--tie-b); border-color: var(--tie); background: {ds.token_rgba('tie', 0.18)}; }}
/* The state word, the SIGNAL hue (amber) only for what the data says: a call that missed, a
   number retracted, conviction below Majority. Never for what the UI wants from you. */
.state {{ font-family: {ds.FONT_MONO}; font-size: .68rem; letter-spacing: .05em; text-transform: uppercase; color: var(--muted); white-space: nowrap; cursor: help; }}
.state.attn {{ color: var(--amber-b); }}
.state.needs {{ color: var(--sky-b); }}
.state.closed {{ color: var(--dim); }}
.scope {{ font-family: {ds.FONT_MONO}; font-size: .66rem; letter-spacing: .05em; color: var(--dim); white-space: nowrap; cursor: help; }}

/* Rows. One grammar for every kind: when · kind · author · the line · state · the verb. */
.rows {{ border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }}
.row {{ display: grid; grid-template-columns: 4.2rem auto auto minmax(0, 1fr) auto auto; gap: .6rem; align-items: center; padding: .38rem .8rem; border-bottom: 1px solid var(--line); min-height: 2.15rem; }}
.row:last-child {{ border-bottom: 0; }}
.row[aria-expanded="true"] {{ background: color-mix(in srgb, var(--surface) 80%, transparent); }}
.row:hover {{ background: color-mix(in srgb, var(--surface) 60%, transparent); }}
.row .line {{ min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: .86rem; color: var(--ink); }}
.row .line b {{ font-weight: 600; }}
.row .line .q {{ color: var(--muted); }}
.row .verb {{ justify-self: end; display: flex; gap: .3rem; align-items: center; }}
.row .verb .btn {{ padding: .22rem .6rem; font-size: .74rem; }}
.row .age {{ font-size: .7rem; }}
.detail {{ grid-column: 1 / -1; padding: .35rem 0 .3rem 4.8rem; display: grid; gap: .5rem; }}
.detail .receipt {{ font-size: .82rem; }}
.detail .prose {{ font-size: .84rem; max-width: 92ch; }}
.detail .sub {{ color: var(--muted); font-size: .78rem; }}
.detail .acts {{ display: flex; gap: .4rem; flex-wrap: wrap; align-items: center; }}
.detail .acts .sep {{ flex: 1; }}
.detail .hist {{ font-family: {ds.FONT_MONO}; font-size: .7rem; color: var(--muted); display: grid; gap: .12rem; }}
.detail .hist b {{ color: var(--ink); font-weight: 600; }}
.detail input.note {{ width: min(60ch, 100%); background: var(--surface); color: var(--ink); border: 1px solid var(--line-2); border-radius: 6px; padding: .3rem .55rem; font-family: {ds.FONT_SANS}; font-size: .82rem; }}
.detail input.note::placeholder {{ color: var(--dim); }}
.detail .rate {{ display: flex; gap: .35rem; flex-wrap: wrap; align-items: center; }}
.detail .rate .chip {{ text-transform: none; letter-spacing: 0; font-family: {ds.FONT_SANS}; font-size: .78rem; }}
.detail .rate .chip[aria-pressed="true"] {{ color: var(--ink); border-color: var(--ink); }}
.btn[disabled] {{ opacity: .45; cursor: not-allowed; }}
.btn.danger {{ color: var(--muted); border-style: dashed; }}
.empty {{ padding: .55rem .8rem; color: var(--muted); font-size: .82rem; }}
.empty .absent {{ font-size: .8rem; }}

/* Panels (the governed group): one header grammar. */
.panel {{ border: 1px solid var(--line); border-radius: 10px; margin-bottom: .55rem; background: color-mix(in srgb, var(--surface-2) 60%, transparent); }}
.panel > .ph {{ display: flex; align-items: center; gap: .7rem; padding: .45rem .8rem; cursor: pointer; border: 0; background: transparent; width: 100%; text-align: left; color: var(--ink); font-family: {ds.FONT_SANS}; }}
.panel > .ph .name {{ font-weight: 600; font-size: .9rem; }}
.panel > .ph .count {{ font-family: {ds.FONT_MONO}; font-size: .72rem; color: var(--muted); }}
.panel > .ph .grow {{ flex: 1; }}
.panel > .ph .read {{ font-family: {ds.FONT_MONO}; font-size: .66rem; letter-spacing: .06em; text-transform: uppercase; color: var(--dim); cursor: help; }}
.panel > .ph .tri {{ font-family: {ds.FONT_MONO}; color: var(--dim); width: 1rem; }}
.panel > .pb {{ padding: 0 .8rem .55rem; }}
.panel > .pb .rows {{ border-radius: 8px; }}
.tier {{ margin: .9rem 0 .4rem; display: flex; align-items: baseline; gap: .8rem; }}
.tier .eyebrow b {{ color: var(--ink); }}
.tier .sub {{ color: var(--dim); font-size: .76rem; }}
.strip {{ display: flex; gap: .5rem; flex-wrap: wrap; align-items: center; margin-bottom: .6rem; }}
"""


HARNESS_HTML = """
<div class="harness" aria-label="mockup harness">
  <span class="lbl">harness</span>
  <button id="btn-sidebar" aria-pressed="true" onclick="toggleSidebar(this)">sidebar 400px</button>
  <button id="btn-empty" aria-pressed="false" onclick="toggleEmpty(this)" title="Every store empty: the group must still say what it is and that each part is empty. The app hides three of the five panels entirely when their store is empty.">all stores empty</button>
  <button id="btn-motion" aria-pressed="false" onclick="toggleMotion(this)">reduced motion</button>
</div>
"""

#: The collapsed dock beneath the group -- D1 Ledger's collapsed line, as static HTML, so the
#: neighbour is present at its real height and the group's vocabulary can be checked against it.
DOCK_COLLAPSED_HTML = """
<div class="bar">
  <span class="wordmark">The Prytaneum</span>
  <span class="rec">WAIT</span>
  <span class="conv low" title="Worth investigation: the answer depends on something only another manager can tell you — RECON says what to ask."><i>?</i>worth investigation</span>
  <span class="q">to <b>Roster 6 just offered me their 2027 1st and Kyren Williams for Achane…</b></span>
  <span class="seats"><span class="seat" data-role="quant" title="Quant · reported">Q</span><span class="seat failed" data-role="beat" title="Beat Tracker: no report reached the panel — Gemini request failed: 503 Service Unavailable.">B</span><span class="seat" data-role="contrarian" title="Contrarian · reported">C</span></span>
  <span class="mark attn" title="1 chair sent no report; the verdict rests on 2 of 3.">2 of 3 chairs</span>
  <span class="age" title="2025-09-07 01:00 UTC">5h ago</span>
  <span class="grow"></span>
  <button class="btn primary">Ask</button>
  <button class="btn icon quiet" title="Expand one tier">▲</button>
</div>
"""

PAGE_BEHIND = """
<div class="app">
  <aside class="side" aria-hidden="true">
    <div class="ph">Activity Log (0)</div><div class="ph">Connections &amp; Models</div><div class="ph">Roles &amp; Routing</div><div class="ph">Data Uploads</div><div class="ph">External Valuation Sources</div>
    <div class="ph" style="margin-top:2rem">Status · Data Freshness: Stale</div>
  </aside>
  <div class="main">
    {spec}
    <div class="banner"><div class="eyebrow">Fantasy Football Command Center</div><h1>Gold Wyrm Dynasty</h1><div class="sub">Dynasty · 12-team · Superflex · Full PPR · Taxi: 4</div></div>
    <div class="tabs"><span>Matchup</span><span>Roster Maintenance</span><span>Draft Room</span><span>League</span><span class="on">Import Audit</span></div>
    <div class="view" style="height:3.2rem">Import Audit · what the Sleeper connection actually brings in (the view's own content; the lightest host, as in the probe)</div>
    <div id="group" class="group" aria-label="the panel group">{group}</div>
  </div>
</div>
"""

SPEC_HTML = """
<details class="spec">
  <summary><span class="k">Variant</span> <b>{title}</b> — {tagline} <span class="hint">· open for the argument, what each panel earns its place by, sacrifice and data</span></summary>
  <div class="specbody">
  <span class="k">The group is for</span><span>{purpose}</span>
  <span class="k">Structure</span><span>{structure}</span>
  <span class="k">Earns its place</span><span>{earns}</span>
  <span class="k">Sacrifices</span><span>{sacrifices}</span>
  <span class="k">Data</span><span><b>Every record on this page is constructed</b>: all four stores are empty in this tree. The rows are in the stores' own shapes (decision_log, todo_log, bot_research, pinned_messages), with the verdict fields produced by llm_engine.parse_moderator_verdict over the Debate Dock's constructed transcript and every finding's eligibility by bot_research.composite_eligibility. Six decisions (one whose block had no RECOMMENDATION line, one same-day re-run, three rated), seven objectives (three open from ACTION ITEMs, one proposed done, three closed), three pins (one orphaned by a compaction), six findings (one per reason a number does or does not count) and two comparisons from two leagues.</span>
  </div>
</details>
"""

BASE_JS = dock_common.BASE_JS + r"""
// ---- the panel group's own vocabulary ---------------------------------------------------
const KIND = { decision: ["V", "verdict", "A Moderator verdict, logged from its closing block. Read by the next debate only once you have rated how it played out."],
               objective: ["O", "objective", "An open objective: standing context for EVERY question the panel is asked."],
               finding: ["F", "finding", "A panel-vetted claim about one player from a named source. Read by every debate; its NUMBER counts toward the composite only after you confirm it."],
               comparison: ["C", "comparison", "A panel-vetted relative claim between two players. Read by every debate; never carries a number."],
               pin: ["P", "pin", "A chat message you pinned. Read by a debate only when the question relates to it -- a findability aid, not a priority."] };
function kindHtml(k, on) { const e = KIND[k]; return `<span class="kind${on ? " on" : ""}" title="${esc(e[2])}">${e[0]}</span>`; }
function authorSeat(role, model) {
  if (role === "user" || role === "manual") return `<span class="seat you" title="You wrote this.">Y</span>`;
  const r = role === "moderator" || role === "moderator" ? "moderator" : role;
  if (!ROLE_LETTER[r]) return `<span class="seat silent" title="${esc(role)}">·</span>`;
  const t = `${PAYLOAD.roleNames[r]} · ${ROLE_JOB[r]}` + (model ? ` (${model})` : " (model not recorded)");
  return `<span class="seat" data-role="${r}" title="${esc(t)}">${ROLE_LETTER[r]}</span>`;
}
function stateHtml(cls, word, why) { return `<span class="state ${cls}" title="${esc(why)}">${esc(word)}</span>`; }
// A decision's state: rated (the outcome word; Didn't Work takes the signal hue) or unrated
// (the needs-you hue: the row has nothing to teach a future debate until you rate it).
function decisionState(d) {
  if (d.outcome) return stateHtml(d.outcome === "Didn't Work" ? "attn" : "", d.outcome, `Rated ${d.outcome} on ${d.outcome_date}${d.outcome_note ? ": " + d.outcome_note : ""}. Past verdicts reach a debate only when rated and related.`);
  return stateHtml("needs", "unrated", "Not yet rated. An unrated verdict is excluded from what future debates are shown -- rating it is what turns the log into a track record.");
}
function decisionRec(d) { return d.recommendation ? `<span class="rec" data-fact="rec">${esc(d.recommendation)}</span>` : `<span class="rec" data-fact="rec">${absent("The block was logged without a RECOMMENDATION line (the parser is per-field); the rest of the verdict is here.")}</span>`; }
function decisionConv(d) { return convHtml({ conviction: d.conviction || undefined }, false); }
// Objectives: three live states and two closed ones, counted apart, never as one "active".
function objectiveState(t) {
  if (t.status === "likely_resolved") return stateHtml("needs", "proposed done", `A bot proposed this is done: ${t.resolution_reason}. Nothing closes until you confirm or keep it open.`);
  if (t.status === "active") return stateHtml("", "open", "Open. Handed to the panel on every question as standing context.");
  if (t.status === "resolved") return stateHtml("closed", "done", `Closed ${t.resolution_date}: ${t.resolution_reason}`);
  return stateHtml("closed", "dismissed", `Dismissed ${t.resolution_date}: ${t.resolution_reason}`);
}
// A finding's eligibility, RECOMPUTED as bot_research.feeds_composite does -- the stored
// composite_impact is a record of an old decision, not the decision.
function findingFeeds(f) {
  if (f.retracted) return { feeds: false, word: "retracted", cls: "attn", why: `Retracted (${f.retracted.reason}) by ${f.retracted.by} on ${f.retracted.at}${f.retracted.note ? ": " + f.retracted.note : ""}. Its number is out of circulation; the claim stays in the record.` };
  if (f.rank === null || f.rank === undefined) return { feeds: false, word: "no number", cls: "", why: "A qualitative claim: nothing to gate, nothing to count. Read by the panel as prose." };
  if (!("adjudication" in f)) return { feeds: false, word: "never adjudicated", cls: "needs", why: `Written before the confirmation gate existed: no adjudication was ever recorded. Its stored impact string says "${f.composite_impact}", but the decision is recomputed from the row and this number does NOT count until confirmed.` };
  if (f.cited_source_admitted === null) return { feeds: false, word: "source not allowed", cls: "", why: `"${f.source}" is not on the composite allowlist, so its number cannot count whatever you do. Confirming is not offered because it would change nothing.` };
  if (f.adjudication !== "human_confirmed") return { feeds: false, word: "awaiting you", cls: "needs", why: "A rank from an allowed source, panel-vetted, not yet confirmed by a second pair of eyes. Confirming says you looked -- not that it is verified." };
  return { feeds: true, word: "counting", cls: "", why: `Confirmed by ${f.confirmed_by} on ${f.confirmed_at}: this number feeds the composite score at a low weight. Retract to take it back out.` };
}
function rankHtml(f) { return f.rank === null || f.rank === undefined ? absent("The source stated no rank number; a qualitative claim.") : `<span class="mono">#${f.rank}</span>`; }
function originHtml(f) {
  const e = f.evidence;
  if (!e) return `<span class="mark" title="Written before the evidence snapshot existed: never checked, which is not the same as checked and found none.">origin not recorded</span>`;
  if (e.origin === "panel_retrieved") return `<span class="mark" title="The provider responses behind that debate reported fetching ${e.debate_sources.length} page(s) -- debate-level, not this claim's own citation.">panel retrieved ${e.debate_sources.length}</span>`;
  return `<span class="mark" title="Those responses reported fetching nothing: a chair reasoning from its context or its training, or simply not searching. Unknown provenance, never a source-less claim.">no retrieval reported</span>`;
}
function leagueMark(id) {
  if (!id) return `<span class="scope" title="No league recorded on this row.">league not recorded</span>`;
  if (id === PAYLOAD.league.id) return `<span class="scope" title="Asked in this league. Findings are stored globally and read by every league.">this league</span>`;
  return `<span class="scope" title="Asked in another league (${id}). Findings are stored globally and read by every league, including this one.">another league</span>`;
}
// Pins: the message, or a labelled orphan when compaction summarised the message away.
function pinMessage(ts) { return hist().find(m => m.ts === ts) || null; }
function pinLine(msg) { const v = parseVerdict(msg.content); return v.has ? `<b>${esc(v.fields.recommendation || "verdict")}</b> <span class="q">${trunc(v.prose, 110)}</span>` : trunc(msg.content, 130); }
// The one join the stores actually support: an objective's text against a verdict's ACTION
// ITEM. (todo_log has a decision_ts slot; nothing writes it.)
function objectiveOfDecision(d) { const v = parseVerdict(d.moderator_text); const a = v.fields.action_item; if (!a) return null; return PAYLOAD.todos.find(t => t.text.trim() === a.trim()) || null; }
function decisionOfObjective(t) { if (t.source !== "moderator") return null; return PAYLOAD.decisions.find(d => { const v = parseVerdict(d.moderator_text); return v.fields.action_item && v.fields.action_item.trim() === (t.revisions && t.revisions.length ? t.revisions[0].text : t.text).trim(); }) || null; }
function decisionReceipt(d) {
  const v = parseVerdict(d.moderator_text);
  const model = d.model ? esc(d.model) : absent("The model that answered was not recorded on this row (written before that field existed); it is not the current default.");
  return `<div class="prose">${md(v.prose)}</div>${receiptHtml(v)}<div class="sub">Answered by ${authorSeat("moderator", d.model)} ${model}${d.provider ? ` · ${esc(d.provider)}` : ""}</div>`;
}

// ---- state ------------------------------------------------------------------------------
let empty = false, filters = { kind: null, needs: false }, ratings = {}, openPanels = {};
function stores() {
  if (empty) return { decisions: [], todos: [], pinned: [], findings: [], comparisons: [] };
  return { decisions: PAYLOAD.decisions, todos: PAYLOAD.todos, pinned: PAYLOAD.pinned, findings: PAYLOAD.findings, comparisons: PAYLOAD.comparisons };
}
function toggleEmpty(b) { empty = b.getAttribute("aria-pressed") !== "true"; b.setAttribute("aria-pressed", empty); openId = null; render(); }
function setLevel() {}
function needsYou(S) {
  return { unrated: S.decisions.filter(d => !d.outcome).length,
           proposed: S.todos.filter(t => t.status === "likely_resolved").length,
           open: S.todos.filter(t => t.status === "active").length,
           awaiting: S.findings.filter(f => { const e = findingFeeds(f); return e.cls === "needs"; }).length,
           orphans: S.pinned.filter(ts => !pinMessage(ts)).length };
}
"""


def page(slug: str, title: str, tagline: str, args: dict, css: str, group_html: str, js: str) -> str:
    spec = SPEC_HTML.format(title=title, tagline=tagline, **args)
    return f"""<!doctype html>
<html lang="en" data-level="collapsed" data-sidebar="on"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{common.esc_title(title)} — panel group mockup</title>
<style>
{PANELS_CSS}
{css}
</style></head>
<body>
{HARNESS_HTML}
{PAGE_BEHIND.format(spec=spec, group=group_html)}
<div class="dock" id="dock" aria-label="The Prytaneum">{DOCK_COLLAPSED_HTML}</div>
<script>
const PAYLOAD = {common.safe_json(dict(panels_data.payload(), attached=None))};
{BASE_JS}
{js}
render();
</script>
</body></html>
"""
