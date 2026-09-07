"""Build the panel-group mockups: `python3 mockups/panels_build.py` from the repo root.

Writes panels_1_calls.html, panels_2_standing.html, panels_3_brief.html, panels_payload.json
and panels_index.html
(which folds in panels_density.json and panels_baseline_measure.json when the instruments have
run). Each page is self-contained. Run `python3 mockups/panels_smoke.py` afterwards for the
gate and the density instrument. Also prints the WCAG ratios of every foreground/ground pair
the pages use, from design_system's own contrast function -- the floor is written policy, so
this reports.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import design_system as ds  # noqa: E402
import dock_build  # noqa: E402  the index's CSS and contrast pairs, reused
import panels_common  # noqa: E402
import panels_data  # noqa: E402
import panels_variants  # noqa: E402

INDEX_CSS = dock_build.INDEX_CSS + """
.chain { border-collapse: collapse; font-size: .8rem; margin: .6rem 0; }
.chain th, .chain td { border: 1px solid var(--line-2); padding: .35rem .6rem; text-align: left; vertical-align: top; }
.chain th { color: var(--muted); font-weight: 600; font-family: "JetBrains Mono", monospace; font-size: .66rem; letter-spacing: .08em; text-transform: uppercase; }
.chain td.k { font-family: "JetBrains Mono", monospace; font-size: .72rem; color: var(--ink); white-space: nowrap; }
.chain td.v { color: var(--ink); font-weight: 600; white-space: nowrap; }
.chain td.v.no { color: var(--amber-b); }
.defects { font-size: .84rem; max-width: 110ch; }
.defects li { margin: .4rem 0; }
.defects b { color: var(--ink); }
.defects code { font-family: "JetBrains Mono", monospace; font-size: .74rem; color: var(--muted); }
.defects .tag { font-family: "JetBrains Mono", monospace; font-size: .62rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); border: 1px solid var(--line-2); border-radius: 3px; padding: .02rem .3rem; margin-left: .3rem; }
.test { border: 1px solid var(--line-2); border-radius: 10px; padding: .8rem 1rem; background: var(--surface-2); max-width: 110ch; font-size: .9rem; margin: .8rem 0; }
.test b { color: var(--ink); }
.dens td.n { color: var(--muted); font-size: .66rem; }
"""


def contrast_report():
    pairs = [
        ("ink", "surface", 4.5), ("muted", "surface", 4.5), ("dim", "surface", 3.0),
        ("amber-b", "surface", 4.5), ("sky-b", "surface", 4.5), ("gold-b", "surface", 4.5),
        ("emerald-b", "surface", 4.5), ("cliff-b", "surface", 4.5), ("violet-b", "surface", 4.5),
        ("crimson-b", "surface", 4.5), ("tie-b", "surface", 4.5),
        ("ink", "bg", 4.5), ("muted", "bg", 4.5), ("dim", "bg", 3.0), ("amber-b", "bg", 4.5), ("sky-b", "bg", 4.5),
        ("bg", "gold", 4.5),
    ]
    return [(a, b, ds.contrast_ratio(a, b), floor) for a, b, floor in pairs]


def density_table() -> str:
    path = HERE / "panels_density.json"
    if not path.exists():
        return '<p class="gates">Density not yet measured — run <code>python3 mockups/panels_smoke.py</code>.</p>'
    rows = json.loads(path.read_text())
    body = []
    for r in rows:
        if r["panel"] == "(group)":
            body.append(f"<tr><td>{r['file'].replace('.html', '')}</td><td><b>whole group</b></td><td>—</td><td>{r['height']}</td><td>—</td><td>—</td><td>—</td><td>—</td><td>{r['buttons']}</td><td>{r['inputs']}</td><td>{r['minFontPx']}</td><td class='n'>{r['textElements']} text elements · {r['colourEmoji']} colour emoji · page {r['page']['scrollHeight']}px</td></tr>")
            continue
        kinds = " · ".join(f"{k}: {v['units']} × {v['pxPerUnit']}px / {v['elementsPerUnit']} el" for k, v in (r.get("kinds") or {}).items())
        note = r.get("note", "")
        if r.get("captionWords") is not None:
            note += f" · caption {r['captionWords']} words · {r['colourEmoji']} colour emoji"
        cls = "base" if r["file"].startswith("baseline") else ""
        body.append(f"<tr class=\"{cls}\"><td>{r['file'].replace('.html', '')}</td><td>{r['panel']}</td><td>{'open' if r['open'] else 'closed'}</td><td>{r['height']}</td><td>{r['units']}</td><td>{r['fullyVisible'] if r['fullyVisible'] is not None else '—'}</td>"
                    f"<td>{r['pxPerUnit'] if r['pxPerUnit'] is not None else '—'}</td><td>{r['elementsPerUnit'] if r['elementsPerUnit'] is not None else '—'}</td><td>{r['buttons']}</td><td>{r['inputs']}</td><td>{r['minFontPx']}</td><td class='n'>{kinds}{(' · ' if kinds and note else '') + note}</td></tr>")
    return ('<table class="dens"><thead><tr><th>page</th><th>panel</th><th>at rest</th><th>height px</th><th>items</th><th>fully visible</th><th>px / item</th><th>elements / item</th><th>buttons</th><th>inputs</th><th>min font px</th><th>per kind · notes</th></tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table>'
            '<p class="gates">Measured in Chromium at 1,400 × 1,400 with the 400px sidebar, at rest: nothing opened, no hover, no filter, scrolled to the top, the dock collapsed beneath. '
            'An item is one record: a verdict, an objective, a finding or comparison, a pin. "px / item" is the panel\'s row region height over its items; "elements / item" counts visible text-bearing elements per item; "fully visible" counts items whose box lies inside the viewport above the dock. '
            'The baseline rows are the app\'s own five expanders measured the same way against the same seeded stores (panels_probe_asis.cjs on a scratch copy; Import Audit view; only Active Objectives is open as shipped, so its numbers are the at-rest cost under every view, while the other four are measured opened). '
            'The app\'s Decision Log and Bot Research render their rows in st.dataframe canvases, whose cells are not DOM text, so their "elements / item" undercounts; their px / item is real.</p>')


def baseline_checks() -> dict:
    p = HERE / "panels_baseline_measure.json"
    return json.loads(p.read_text()).get("checks", {}) if p.exists() else {}


CHAIN_ROWS = [
    ("Decision Log", "decision (+ proof, once rated)", "decision (+ evidence: REASON / RISK in the block)",
     "The Moderator's closing block per verdict, and the one place an outcome can be recorded. It IS the decision link — but the table drops DISSENT, the field that names who disagreed, and the proof control defaults to a rating nobody chose.", "earns its place", False),
    ("Active Objectives + Archive", "— (no engine link: the engine has no objective store)", "objective, by name only",
     "ACTION ITEMs: a specific trade to propose, a claim to submit, a manager to ask. Tasks a verdict set, carried forward and closed by you. Nothing in any store says what the team is optimising (contend / rebuild / horizon): league_prefs holds display order, the draft engine's mode is a per-view control. A to-do list wearing the word.", "earns its place as decision → action; the OBJECTIVE link is missing", True),
    ("Bot Research (findings, comparisons)", "signals — an admission gate on an input", "looks like evidence; is not",
     "A finding's NUMBER feeds the composite score, upstream of every synthesis, once you confirm it; the prose is handed to every debate as an input. Nothing joins a finding to the decision it was surfaced in except the question text. It is global where everything else is per-league. A signals gate filed among the memory panels; it could as well sit beside the sidebar's External Valuation Sources.", "belongs here only as a labelled signals gate", True),
    ("Pinned Messages", "—", "—",
     "A bookmark on a transcript message, retrieved for a debate on word overlap. Maps to no link in either chain. The dock's own variants already carry pinned as a mark on the message; a panel of 500-character excerpts adds a second, worse, view of the same transcript.", "maps to no link; belongs to the dock", True),
    ("(nothing)", "synthesis → what remains uncertain", "the gap between decision and evidence",
     "Conviction, the dissenting seat, RECON, RISK and which chairs reported are in the dock's receipt for the STANDING call and as table cells (minus dissent) in the log. No surface owns the question the test asks: what remains uncertain, and what only you can settle (unrated calls, proposed-done objectives, held-back numbers).", "MISSING", True),
    ("(outside the group)", "state · evidence", "state · evidence",
     "The roster, data freshness and the attached context live in the sidebar Status and the dock's Considering chip; the chairs' reports live in the transcript. Rightly outside the group — but a verdict row cannot open its own debate (the join is a timestamp within seconds), so the decision link cannot reach its evidence link.", "outside, and unlinked", True),
]


def defects_html(checks: dict) -> str:
    picker = checks.get("decisionPickerOptions") or []
    items = [
        ("PRODUCT", "A pinned verdict loses its call.", "<code>st.caption(pm['content'][:500])</code> (app.py ~5695) cuts a pinned message at 500 characters with no mark, and <code>pinned_messages.find_relevant</code> hands a debate <code>[:400]</code>. The constructed first verdict's block starts at character 609. Live: the Pinned panel renders it with no RECOMMENDATION anywhere (<code>pinnedShowsRecommendation: false</code>). Pin × verdict shape: the part worth pinning is the part cut."),
        ("PRODUCT", "A pin outlives its message in silence.", "<code>compact_chat_history</code> (app.py ~1364) summarises old messages away without consulting the pin store; the panel lists only pins whose message is still in <code>chat_history</code> and counts those. Live: three pins stored, header reads <b>Pinned Messages (2)</b>, nothing says a third exists."),
        ("PRODUCT", "The outcome control defaults to <b>Worked</b>.", "<code>st.selectbox('Outcome', options=OUTCOME_LABELS)</code> (app.py ~5738) has no empty state; one press of Save records the first label for whichever decision the picker shows. That outcome is then what <code>search_decisions_with_outcomes</code> feeds the next debate as the panel's track record. A default in a consumer is a contract change — here it invents proof."),
        ("PRODUCT", "A same-day re-run cannot be rated, and the picker says nothing.", "The picker's options are a dict keyed by <code>date + question[:70]</code>; two verdicts to the same question on one day share a key and the LAST write over <code>reversed(decisions)</code> wins, i.e. the older one. Live: " + (f"the picker offers <b>{len(picker)} options for 6 decisions</b>" if picker else "the picker collapses the pair") + "; choosing the 09-06 label rates the original run and the re-run is unreachable. The store does not dedupe same-day rows (<code>bot_research.add_finding</code> does, for exactly this reason)."),
        ("PRODUCT", "Two absences, two renderings, one table.", "A block logged without a RECOMMENDATION line (the parser is per-field; <code>log_decision</code> keeps any block with one field) renders a <b>blank</b> Call cell, while an unrated Outcome renders <code>—</code>. Live: the 08-15 row's Call is empty. A blank in a column of BUY/HOLD/WAIT reads as \"no call\", not \"the line was missing\"."),
        ("PRODUCT", "DISSENT is logged and never shown.", "The Decision Log table's columns are Date, Question, Call, Conviction, Reason, Risk, Recon, Price Ceiling, Alternative, Outcome. <code>dissent</code>, <code>provider</code>, <code>model</code>, <code>outcome_note</code> and <code>outcome_date</code> are stored and dropped. The one field that names who disagreed — the uncertainty the test asks about — is invisible."),
        ("PRODUCT", "The findings table disagrees with the list above it about the same row.", "The table's <b>Composite impact</b> column prints the STORED string; a row written before the gate carries <code>low-weight input</code> while <code>feeds_composite</code> recomputes it as not counting, so the same finding is listed under <b>Awaiting your confirmation</b> with a Confirm button and, two inches lower, as counting. bot_research's own docstring says the stored string is a record, not the decision; the panel reads the record. Also: the <b>Rank</b> column mixes integers with <code>—</code>, which makes pyarrow raise <code>ArrowInvalid</code> on every render — Streamlit falls back to text and logs a full traceback each time."),
        ("PRODUCT", "Delete is a peer of Done.", "<code>d1, d2, d3 = st.columns(3)</code>: <b>Mark Done</b>, <b>Dismiss</b>, <b>Delete</b> at equal width, one press, no confirm. todo_log's own docstring: \"Full erasure — no undo. Meant for a mistaken/duplicate/spam entry, not for 'this objective is done'.\" The archive repeats it as <b>Delete permanently</b> beside Revisit."),
        ("STRUCTURAL", "The objective → verdict join does not exist.", "<code>todo_log.add_todo</code> accepts <code>decision_ts</code>; no caller passes it (grep: the only writer is the default <code>None</code>). An objective knows only that a Moderator wrote it and which question was asked. Any one-surface design must join by ACTION ITEM text, and a revision breaks the join. Likewise a finding carries <code>question</code> but no decision key, and a decision carries no message key (its <code>ts</code> lands within a second of the message's)."),
        ("PRODUCT", "\"Active Objectives (N)\" counts proposed-done as active.", "<code>ACTIVE_STATUSES = ('active', 'likely_resolved')</code>; the header, the dock header's \"N active objective(s)\" and the bots' OPEN TO-DO ITEMS all use the pair. Live: <b>(4)</b> for three open and one the panel proposed as done."),
        ("PRODUCT", "The at-rest cost under every view.", "Active Objectives is <code>expanded=bool(active_items)</code>: open on every tab whenever anything is open. Live: <b>1,483px, 18 buttons, 8 inputs, 23 colour emoji</b> for four items (360.8 px / item, 10.3 text elements / item) below Matchup, Draft Room, League and Import Audit alike. The five captions total <b>250 words</b> (38 + 24 + 78 + 76 + 34) explaining, five ways, that the bots read this."),
        ("MINOR", "Smaller ones, recorded.", "<b>Revisit as new objective</b> writes <code>source='manual'</code>, so a Moderator ACTION ITEM revisited becomes a hand-written one. The Archive's search filters <code>text + resolution_reason</code>; the bots' <code>search_archived</code> matches <code>text + question</code> — two different \"relevant\". <b>Bot Research (6 findings …)</b> counts retracted findings and is global under a league's page; only the caption says so. The Dock's own constructed transcript writes a SOURCE COMPARISON line with five fields; <code>parse_source_comparisons</code> needs six and drops it silently, so the dock's payload records a comparison the app would never have stored."),
    ]
    return "".join(f"<li><b>{i + 1}. {t}</b><span class=\"tag\">{tag}</span> {body}</li>" for i, (tag, t, body) in enumerate(items))


def index_html() -> str:
    def cards(variants):
        return "".join(
            f'<div class="v"><a href="{v["slug"]}.html">{v["title"]}</a><span class="tag">{v["tagline"]}</span>'
            f'<span class="k">the group is for</span><p>{v["purpose"]}</p><span class="k">structure</span><p>{v["structure"]}</p>'
            f'<span class="k">earns its place</span><p>{v["earns"]}</p><span class="k">sacrifices</span><p>{v["sacrifices"]}</p></div>'
            for v in variants)
    chain = "".join(
        f"<tr><td class=\"k\">{p}</td><td>{e}</td><td>{u}</td><td>{what}</td><td class=\"v{' no' if bad else ''}\">{verdict}</td></tr>"
        for p, e, u, what, verdict, bad in CHAIN_ROWS)
    contrast = "".join(f"<tr><td>{a} on {b}</td><td></td><td>{r:.2f}:1</td><td>{f}:1</td><td>{'meets' if r >= f else 'BELOW'}</td></tr>" for a, b, r, f in contrast_report())
    checks = baseline_checks()
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Panel group mockups — index</title><style>
{panels_common.common.BASE_CSS}
{INDEX_CSS}
.page {{ max-width: 1180px; margin: 0 auto; padding: 1.4rem 1.2rem 4rem; }}</style></head>
<body><div class="page">
<h1>Gold Wyrm Dynasty · the panel group</h1>
<div class="gates"><p>The four panels app.py renders under every view, between the view's content and the Debate Dock: Pinned Messages, Decision Log, Bot Research, Active Objectives (and its Archive, a fifth expander). Built at different times, never designed as a group. Three structural answers over the same constructed stores — sorted by what produced a record, by when the panel reads it, and by which of the reader's questions it answers — the app's own panels measured against them, and the defects the measurement found.</p></div>
<div class="test"><b>The test.</b> Can someone understand what the system decided, why it decided it, what uncertainty remains, and what it is optimising — without mentally assembling four interfaces? Held against the two chains that have to line up: <span class="mono">engine: signals → synthesis → decision → proof</span> and <span class="mono">ui: state → decision → evidence → objective</span>.</div>

<div class="sec">What the group is for, and what each panel earns its place by</div>
<div class="gates"><p>Every one of the four stores is written during a debate and read back by the next one. Collectively they are the front office's <b>memory</b> — what the next debate is handed, and what only a person can add to it. Each store has exactly one human verb the system cannot perform for itself: a verdict is <b>rated</b> (until it is, <code>search_decisions_with_outcomes</code> excludes it — the log has nothing to teach a future debate), an objective is <b>closed</b> (a bot may open, revise or propose; only the user resolves or dismisses), a finding's number is <b>confirmed</b> (the second adjudication), a message is <b>kept</b> (the one store the user authors). That is one idea. The reader today meets it as five expanders whose order is neither by liveness nor by verb nor by author, whose counts each count something different (pins found in history, decisions including re-runs, findings across every league including retracted ones, objectives including proposed-done), whose captions restate "the bots read this" five ways in 250 words, and of which the only one open by default is the one carrying eighteen buttons.</p>
<p>Mapped onto the chain, panel by panel:</p></div>
<table class="chain"><thead><tr><th>panel</th><th>engine link</th><th>ui link</th><th>what it actually is</th><th>verdict</th></tr></thead><tbody>{chain}</tbody></table>
<div class="gates"><p>Two of the four map cleanly (Decision Log to <i>decision</i>, Objectives to <i>decision → action</i>), one is a signals gate wearing evidence's clothes, one maps to nothing. And the link the test names — <b>what uncertainty remains</b> — has no surface: it is a column in the dock's receipt for one call and a set of table cells, minus DISSENT, in the log. That is the finding worth more than either layout: the interface presents a decided system, and the engine's own uncertainty vocabulary (conviction, dissent, chairs reached, RECON) reaches the reader only for the standing call and only in the dock. All three pages below give it a surface, and each gives it a different weight: a chip and a mark on the row in P1, a strip above the panels in P2, and in P3 a whole numbered section whose rows exist nowhere else in the product.</p></div>

<div class="sec">Defects in the live code, from the measurement</div>
<ol class="defects">{defects_html(checks)}</ol>

<div class="sec">Density at 1,400 × 1,400 — the app's own panels (baseline) against the three</div>
{density_table()}

<div class="sec">Contrast, from design_system.contrast_ratio — written policy, reported not asserted</div>
<table class="dens"><thead><tr><th>pair</th><th></th><th>ratio</th><th>floor</th><th></th></tr></thead><tbody>{contrast}</tbody></table>
<p class="gates">Colour is spent as the constraints say: <b>sky</b> is the one UI-state hue (a row waiting on you: unrated, proposed done, awaiting confirmation, a pin without a message; the pressed need-you chip). <b>amber</b> is the one analytical-signal hue (a call that did not work, a retracted number, conviction below Majority, a missing chair) — the dock's own signal hue, unchanged. The two never share an element and the gate checks it. Gold is the primary button and the focus ring. Kinds are letters on bordered boxes in the ink; authors are the dock's seat tokens, so a row here and a bubble there say "Moderator" the same way. Recommendations and outcomes are words.</p>

<div class="sec">The three</div>
<div class="grid">{cards(panels_variants.VARIANTS)}</div>

<div class="sec">Gates, checked by panels_gate.cjs in a real Chromium</div>
<div class="gates"><ul>
<li><b>A1</b> absence is a labelled state: every store empty still renders the frame and a titled absence per part; the rec-less verdict's call is a hatched absence; the orphaned pin says its message is gone.</li>
<li><b>A2</b> a pinned verdict shows its block when opened.</li>
<li><b>A3</b> the rating control has no default and a same-day re-run is its own row with its own control.</li>
<li><b>A4</b> delete is never a peer of done / dismiss.</li>
<li><b>A5</b> a finding's eligibility is recomputed from its fields, never read from the stored string.</li>
<li><b>C1</b> gold carries no text; the signal hue and the UI-state hue never share an element.</li>
<li><b>C2</b> no colour emoji; nothing under 11px; no null / NaN / undefined.</li>
<li><b>K1</b> keyboard: ArrowDown moves, Enter opens, Escape closes.</li>
<li><b>M1</b> every animation dies under prefers-reduced-motion.</li>
</ul></div>

<div class="sec">What is constructed</div>
<div class="gates"><p><b>Every record.</b> All four stores are empty in this tree. panels_data.py writes them in the stores' own shapes: the verdict fields come from <code>llm_engine.parse_moderator_verdict</code> over the Debate Dock's constructed transcript (so the rows are what <code>app.process_moderator_output</code> would have written), the objective revision from <code>parse_todo_directives</code>, every finding's eligibility triple from <code>bot_research.composite_eligibility</code>. The stores are made to hold every state they can: a rec-less block, a same-day re-run, rated and unrated verdicts; open, revised, cited, proposed-done, resolved (with and without a real note) and dismissed objectives; a pin whose message a compaction took; a finding per reason a number does or does not count, including a legacy row with no adjudication key; comparisons from two leagues. The league snapshot behind the live probe is a minimal one with no rosters. Nothing here is a claim about any league.</p></div>
</div></body></html>"""


def main() -> None:
    (HERE / "panels_payload.json").write_text(json.dumps(panels_data.payload(), indent=1))
    for v in panels_variants.VARIANTS:
        html = panels_common.page(v["slug"], v["title"], v["tagline"],
                                  dict(purpose=v["purpose"], structure=v["structure"], earns=v["earns"], sacrifices=v["sacrifices"]),
                                  v["css"], v["html"], v["js"])
        (HERE / f"{v['slug']}.html").write_text(html)
        print(f"wrote {v['slug']}.html ({len(html):,} chars)")
    (HERE / "panels_index.html").write_text(index_html())
    print("wrote panels_index.html")
    print("\ncontrast (design_system.contrast_ratio):")
    for a, b, r, f in contrast_report():
        print(f"  {a:10s} on {b:8s} {r:6.2f}:1  floor {f}:1  {'meets' if r >= f else 'BELOW'}")


if __name__ == "__main__":
    main()
