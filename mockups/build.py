"""Regenerate every mockup: `python3 mockups/build.py` from the repo root.

Nine standalone HTML files (five Draft Room page directions, four quantity-surfacing
directions) plus an index that lists each variant's assertion and sacrifice side by side.
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
"""


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
<div class="gates"><p>Every mockup renders the same real snapshot (12-team superflex dynasty, on the clock at 3.03, 16 picks to the next turn) plus two real IDP rows, one real negative-value kicker, and two labelled fixture rows (an unpriced position-best with every Optional null; a row of measured zeros). Each page has a button to promote the unpriced row to leader and one to simulate reduced motion.</p>
<p>Gates every variant was built against and self-tested on (Node ran each page's JS on the fixture in both leader orders):</p>
<ul><li><b>G1</b> a None never renders as 0 / 0% / an empty slot — it is a hatched em-dash with a title.</li><li><b>G2</b> a measured 0.0 renders as 0.0.</li><li><b>G3</b> no bounded geometry on the UV-points scale; the one axis drawn (B3) is signed with a marked zero.</li><li><b>G4</b> gold marks user state and chrome only.</li><li><b>G5</b> meaning-bearing text ≥ 4.5:1 and glyphs ≥ 3:1 at rest — hierarchy is size, weight and detail, never faded data.</li><li><b>G6</b> the engine's order is never re-sorted; the relevance tier is the engine's own necessity vocabulary.</li><li><b>G7</b> every animation dies under prefers-reduced-motion.</li></ul></div>
<div class="sec">Track C — the Draft Room page: five answers to "what does hierarchy mean here"</div>
<div class="grid">{cards(c_variants.VARIANTS)}</div>
<div class="sec">Track B — surfacing the quantities no screen reads: four answers to "where does a state live"</div>
<div class="grid">{cards(b_variants.VARIANTS)}</div>
</div></body></html>
"""


def main() -> int:
    for variants in (c_variants.VARIANTS, b_variants.VARIANTS):
        for slug, title, tagline, asserts, sacrifices, css, body, js in variants:
            width = "1180px" if slug.startswith("draft_room") else "1100px"
            (HERE / f"{slug}.html").write_text(
                common.page(title, tagline, asserts, sacrifices, css, body, js, width=width))
            print("wrote", slug)
    (HERE / "index.html").write_text(index_html())
    print("wrote index")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
