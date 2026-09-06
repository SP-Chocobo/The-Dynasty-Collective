"""Regenerate the mockups: `python3 mockups/build.py` from the repo root.

ROUND 3 builds the three banded boards (r_variants) and rebuilds the round-2 syntheses
(s_variants) on the same payload, plus the index. The nine round-1 pages are the scored
record -- the owner's verdicts and the critic's scores refer to them as they were -- so they
are NOT regenerated; their generator modules stay for reference.
Each file is self-contained -- tokens, data, CSS and JS inlined; no external requests.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import common  # noqa: E402
import b_variants  # noqa: E402
import c_variants  # noqa: E402
import s_variants  # noqa: E402
import r_variants  # noqa: E402

INDEX_CSS = """
h1 { font-family: "Cinzel", Georgia, serif; letter-spacing: .08em; font-weight: 600; margin: .2rem 0; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(22rem, 1fr)); gap: .8rem; margin-top: 1rem; }
.v { border: 1px solid var(--line); border-radius: 10px; padding: .9rem 1rem; background: var(--surface-2); display: flex; flex-direction: column; gap: .35rem; }
.v a { color: var(--gold-b); font-weight: 700; text-decoration: none; font-size: 1.05rem; }
.v .tag { color: var(--muted); font-size: .84rem; }
.v .k { font-family: "JetBrains Mono", monospace; font-size: .6rem; letter-spacing: .1em; text-transform: uppercase; color: var(--dim); margin-top: .3rem; }
.v p { margin: 0; font-size: .84rem; }
.sec { font-family: "JetBrains Mono", monospace; font-size: .64rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin: 1.6rem 0 .2rem; border-bottom: 1px solid var(--line-2); padding-bottom: .3rem; }
.gates { font-size: .84rem; color: var(--muted); max-width: 90ch; }
.gates li { margin: .15rem 0; }
.dens { border-collapse: collapse; font-family: "JetBrains Mono", monospace; font-size: .74rem; margin: .6rem 0 .2rem; }
.dens th, .dens td { border: 1px solid var(--line-2); padding: .3rem .6rem; text-align: right; }
.dens th:first-child, .dens td:first-child { text-align: left; }
.dens th { color: var(--muted); font-weight: 600; }
"""


def density_table() -> str:
    """The measured density of every gated board, from density.json when the instrument has
    run; a note when it has not. Numbers, not a verdict -- the report draws the conclusion."""
    import json
    path = HERE / "density.json"
    if not path.exists():
        return '<p class="gates">Density not yet measured -- run <code>python3 mockups/smoke.py</code>.</p>'
    rows = json.loads(path.read_text())
    body = "".join(
        f"<tr><td>{r['file'].replace('.html', '')}</td><td>{r['population']}</td><td>{r['readable']} / {r['candidates']}</td>"
        f"<td>{r['pxPerCandidate']}</td><td>{r['rawRowPx']}</td><td>{r['elementsPerCandidate']}</td><td>{r['pageHeight']}</td></tr>"
        for r in rows)
    return ('<table class="dens"><thead><tr><th>board</th><th>population</th><th>readable in 1,400px</th><th>px / candidate</th>'
            '<th>row height px</th><th>elements / candidate</th><th>page height px</th></tr></thead>'
            f'<tbody>{body}</tbody></table><p class="gates">Measured in Chromium at 1,400 × 1,400 at rest '
            '(spec closed, fold closed, nothing open, no hover). "Elements" counts visible text-bearing elements '
            'in one collapsed candidate. A two-column grid counts half a row height per candidate. Two populations: the 14-row contract fixture, and the first 33 candidates of the same real snapshot injected at measurement time.</p>')


def index_html() -> str:
    def cards(variants):
        return "".join(
            f'<div class="v"><a href="{slug}.html">{title}</a><span class="tag">{tagline}</span>'
            f'<span class="k">asserts</span><p>{asserts}</p><span class="k">sacrifices</span><p>{sacrifices}</p></div>'
            for slug, title, tagline, asserts, sacrifices, *_ in variants
        )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Draft Room mockups — index</title><style>{common.BASE_CSS}{INDEX_CSS}.page {{ max-width: 1180px; margin: 0 auto; padding: 1.4rem 1.2rem 4rem; }}</style></head>
<body><div class="page">
<h1>Gold Wyrm Dynasty · Draft Room directions</h1>
<p class="gates">Every page renders the same real snapshot plus the two labelled fixture rows; each has a button to promote the unpriced row to leader and one to simulate reduced motion.</p>
<div class="gates"><p>Every mockup renders the same real snapshot (12-team superflex dynasty, on the clock at 3.03, 16 picks to the next turn) plus two real IDP rows, one real negative-value kicker, and two labelled fixture rows (an unpriced position-best with every Optional null; a row of measured zeros). Each page has a button to promote the unpriced row to leader and one to simulate reduced motion.</p>
<p>Gates every variant was built against and self-tested on (Node ran each page's JS on the fixture in both leader orders):</p>
<ul><li><b>G1</b> a None never renders as 0 / 0% / an empty slot — it is a hatched em-dash with a title.</li><li><b>G2</b> a measured 0.0 renders as 0.0.</li><li><b>G3</b> no bounded geometry on the UV-points scale; the one axis drawn (B3) is signed with a marked zero.</li><li><b>G4</b> gold marks user state and chrome only.</li><li><b>G5</b> meaning-bearing text ≥ 4.5:1 and glyphs ≥ 3:1 at rest — hierarchy is size, weight and detail, never faded data.</li><li><b>G6</b> the engine's order is never re-sorted; the relevance tier is the engine's own necessity vocabulary.</li><li><b>G7</b> every animation dies under prefers-reduced-motion.</li></ul></div>
<div class="sec">Round 3 — the owner's direction: three bands of decreasing weight on the split field. Band 2 is derived from the engine's contiguous decide tier (2 or 3 across is the cap, never the count); band 3 is "keep an eye on"; the cliff is drawn as its size</div>
{density_table()}
<div class="grid">{cards(r_variants.VARIANTS)}</div>
<div class="sec">Round 2 — two list syntheses and three card directions on one spine (superseded by round 3; gated the same way)</div>
<div class="grid">{cards(s_variants.VARIANTS)}</div>
<div class="sec">Round 1 — the scored record (superseded; kept as the owner and the critic saw them)</div>
<p class="gates">Critic: C1 82 pass · C3 70 · C2 69 · C4 63 · C5 62 (four failed G4, gold on engine state) · B4 83 · B1 81 · B2 81 · B3 60. Owner: Reliquary liked; Hoard "interesting"; Ledger "too busy, 2ish details"; Verdict "the sub-bar may be right, cleaner, 2–3 driving factors"; Clock no; and "filter out garbage fluff" — sentences about absent or trivially-true facts.</p>
<div class="grid">{cards(c_variants.VARIANTS)}{cards(b_variants.VARIANTS)}</div>
</div></body></html>
"""


def main() -> int:
    for slug, title, tagline, asserts, sacrifices, css, body, js in r_variants.VARIANTS + s_variants.VARIANTS:
        (HERE / f"{slug}.html").write_text(
            common.page(title, tagline, asserts, sacrifices, css, body, js, width="1180px"))
        print("wrote", slug)
    (HERE / "index.html").write_text(index_html())
    print("wrote index")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
