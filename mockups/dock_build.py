"""Build the Debate Dock mockups: `python3 mockups/dock_build.py` from the repo root.

Writes dock_1_ledger.html, dock_2_thread.html, dock_3_chairs.html, dock_transcript.json and
dock_index.html (which folds in dock_density.json when the instrument has run). Each page is
self-contained. Run `python3 mockups/dock_smoke.py` afterwards for the gate and the density
instrument. Also prints the WCAG ratios of every foreground/ground pair the docks use, from
design_system's own contrast function -- the floor is written policy, so this reports.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import design_system as ds  # noqa: E402
import dock_common  # noqa: E402
import dock_data  # noqa: E402
import dock_variants  # noqa: E402

INDEX_CSS = """
h1 { font-family: "Cinzel", Georgia, serif; letter-spacing: .08em; font-weight: 600; margin: .2rem 0; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(22rem, 1fr)); gap: .8rem; margin-top: 1rem; }
.v { border: 1px solid var(--line); border-radius: 10px; padding: .9rem 1rem; background: var(--surface-2); display: flex; flex-direction: column; gap: .35rem; }
.v a { color: var(--gold-b); font-weight: 700; text-decoration: none; font-size: 1.05rem; }
.v .tag { color: var(--muted); font-size: .84rem; }
.v .k { font-family: "JetBrains Mono", monospace; font-size: .6rem; letter-spacing: .1em; text-transform: uppercase; color: var(--dim); margin-top: .3rem; }
.v p { margin: 0; font-size: .84rem; }
.sec { font-family: "JetBrains Mono", monospace; font-size: .64rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin: 1.6rem 0 .2rem; border-bottom: 1px solid var(--line-2); padding-bottom: .3rem; }
.gates { font-size: .84rem; color: var(--muted); max-width: 100ch; }
.gates li { margin: .15rem 0; }
.dens { border-collapse: collapse; font-family: "JetBrains Mono", monospace; font-size: .72rem; margin: .6rem 0 .2rem; }
.dens th, .dens td { border: 1px solid var(--line-2); padding: .28rem .55rem; text-align: right; }
.dens th:first-child, .dens td:first-child, .dens td:nth-child(2) { text-align: left; }
.dens th { color: var(--muted); font-weight: 600; }
.dens tr.base td { color: var(--muted); }
"""


def contrast_report() -> list[tuple[str, str, float, float]]:
    """(fg, ground, ratio, floor) for every pair the docks put meaning-bearing text on."""
    pairs = [
        ("ink", "surface", 4.5), ("muted", "surface", 4.5), ("dim", "surface", 3.0),
        ("amber-b", "surface", 4.5), ("gold-b", "surface", 4.5), ("emerald-b", "surface", 4.5),
        ("cliff-b", "surface", 4.5), ("violet-b", "surface", 4.5), ("crimson-b", "surface", 4.5),
        ("tie-b", "surface", 4.5), ("sky-b", "surface", 4.5),
        ("ink", "bg", 4.5), ("muted", "bg", 4.5), ("amber-b", "bg", 4.5),
        ("bg", "gold", 4.5),   # the primary button's label on its gold ground
    ]
    return [(a, b, ds.contrast_ratio(a, b), floor) for a, b, floor in pairs]


def density_table() -> str:
    path = HERE / "dock_density.json"
    if not path.exists():
        return '<p class="gates">Density not yet measured — run <code>python3 mockups/dock_smoke.py</code>.</p>'
    rows = json.loads(path.read_text())
    body = "".join(
        f"<tr class=\"{'base' if r['file'].startswith('baseline') else ''}\"><td>{r['file'].replace('.html', '')}</td><td>{r['level']}</td>"
        f"<td>{r['dockHeight']} / {r['cap']}{' · overflows' if r['overflows'] else ''}</td><td>{r['units']}</td><td>{r['fullyVisible']}</td>"
        f"<td>{r['pxPerUnit'] if r['pxPerUnit'] is not None else '—'}</td><td>{r['elementsPerUnit'] if r['elementsPerUnit'] is not None else '—'}</td>"
        f"<td>{r['chromeAbove'] if r['chromeAbove'] is not None else '—'}</td><td>{r['facts'] if r['facts'] is not None else '—'}</td><td>{r['minFontPx']}</td></tr>"
        for r in rows)
    return ('<table class="dens"><thead><tr><th>dock</th><th>level</th><th>height / cap px</th><th>units rendered</th><th>fully visible</th>'
            '<th>px / unit</th><th>elements / unit</th><th>chrome above first unit px</th><th>facts (collapsed)</th><th>min font px</th></tr></thead>'
            f'<tbody>{body}</tbody></table><p class="gates">Measured in Chromium at 1,400 × 1,400 with the 400px sidebar (the dock is 1,000px wide, as in the app), at rest: '
            'nothing open, no hover, no tab selected. A unit is one rendered message-bearing element (a ledger row, a bubble, a seat column); '
            '"fully visible" counts units whose box lies inside the dock\'s visible box and inside their own scroll region\'s visible box. '
            '"Elements" counts visible text-bearing elements per unit. "Facts" counts the named facts a collapsed line carries (data-fact). '
            'The baseline rows are the app\'s own dock, measured the same way (scratchpad/asis_measure2.json), where a unit is one chat message.</p>')


def index_html() -> str:
    def cards(variants):
        return "".join(
            f'<div class="v"><a href="{slug}.html">{title}</a><span class="tag">{tagline}</span>'
            f'<span class="k">collapsed</span><p>{a["collapsed"]}</p><span class="k">partial</span><p>{a["partial"]}</p>'
            f'<span class="k">full</span><p>{a["full"]}</p><span class="k">sacrifices</span><p>{a["sacrifices"]}</p></div>'
            for slug, title, tagline, a, *_ in variants)
    con = "".join(f"<tr><td>{a} on {b}</td><td></td><td>{r:.2f}:1</td><td>{f}:1</td><td>{'meets' if r >= f else 'BELOW'}</td></tr>" for a, b, r, f in contrast_report())
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Debate Dock mockups — index</title><style>{dock_common.common.BASE_CSS}{INDEX_CSS}.page {{ max-width: 1180px; margin: 0 auto; padding: 1.4rem 1.2rem 4rem; }}</style></head>
<body><div class="page">
<h1>Gold Wyrm Dynasty · Debate Dock directions</h1>
<div class="gates"><p>Three docks over the same constructed chat history (14 rows in app.append_message's shape: a memory summary, two Full Prytaneum runs, a block-less follow-up, a stale-data notice; the second run's Beat chair is llm_engine's own fail-soft string). Each page has a harness: the three levels, the sidebar on/off, a history cut after the follow-up (the standing verdict must survive it), and reduced motion.</p>
<p>Carried forward from the Draft Room rounds, and checked by <code>dock_gate.cjs</code> in a real Chromium:</p>
<ul><li><b>G1</b> a failed chair is a hatched, titled absence everywhere it appears — never a report, never a model badge claiming a 503.</li><li><b>G2</b> the standing verdict is the newest block-bearing Moderator message; cutting the history after a block-less follow-up leaves it standing.</li><li><b>G3</b> only a designated scroll region scrolls: the dock itself never overflows its tier's cap at 1,400 × 1,400.</li><li><b>G4</b> gold is the primary button and the focus ring only; amber is the one signal hue (below-Majority conviction, a missing chair, a notice); the recommendation is a word.</li><li><b>G5</b> no text in the dock under 11px; ratios below.</li><li><b>G6</b> the transcript's order is time's; pinned and objective are marks.</li><li><b>G7</b> every animation dies under prefers-reduced-motion.</li><li><b>G8</b> no colour emoji; the four seats are letters on their badge tokens.</li></ul></div>
<div class="sec">Density at 1,400 × 1,400 — the app's own dock (baseline) against the three</div>
{density_table()}
<div class="sec">Contrast, from design_system.contrast_ratio — written policy, reported not asserted</div>
<table class="dens"><thead><tr><th>pair</th><th></th><th>ratio</th><th>floor</th><th></th></tr></thead><tbody>{con}</tbody></table>
<div class="sec">The three</div>
<div class="grid">{cards(dock_variants.VARIANTS)}</div>
</div></body></html>"""


def main() -> None:
    (HERE / "dock_transcript.json").write_text(json.dumps(dock_data.payload(), indent=1))
    for slug, title, tagline, args, css, js in dock_variants.VARIANTS:
        (HERE / f"{slug}.html").write_text(dock_common.page(slug, title, tagline, args, css, "", js))
        print(f"wrote {slug}.html")
    (HERE / "dock_index.html").write_text(index_html())
    print("wrote dock_index.html")
    for a, b, r, f in contrast_report():
        print(f"  {a:10s} on {b:8s} {r:6.2f}:1  floor {f}:1  {'ok' if r >= f else 'BELOW THE WRITTEN FLOOR'}")


if __name__ == "__main__":
    main()
