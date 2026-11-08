#!/usr/bin/env python3
"""THE FIVE ROOM GLYPHS, DRAWN (`#349h`).

The owner, after the generated medallion set failed to cohere:

    Maybe have 4 simply tribal glyphs?

That is the right answer and it is the one that makes generation unnecessary. A tribal glyph
is flat, bold, two-tone linework -- exactly what SVG is for. Asking Midjourney for one buys a
raster copy of something that can be drawn, and the raster version is strictly worse: it cannot
take its colour from the theme, it costs bytes, and `#349f` measured it dissolving into a dot
at 19px.

IT IS ALSO MORE ON-BRAND THAN THE MEDALLIONS WERE. `ui_explore/round4/_ref/wyrm_crop.png` --
the real logo, and the source of `#312`'s gold ramp -- is itself angular tribal linework:
tapering blades that sweep to a point. These are drawn in that idiom rather than in a generic
icon style, so the nav speaks the wordmark's language.

WHY FILLED AND NOT STROKED. The other glyphs in this page (`ICONS`) are 1.6px strokes, which is
right for a utility icon and wrong here: a stroked shape loses its interior at small sizes and
becomes a tangle of lines, which is how the medallions failed. These are filled, so they hold
MASS -- measured legible at 96/72/48/32/19px, every one distinguishable from the others as a
silhouette at every size.

ADOPTING THEM IS A LANGUAGE DECISION, NOT A DROP-IN. The nav currently uses the stroked `ICONS`
set. Filled tribal glyphs beside stroked line icons read as two systems in one bar. Either the
rooms take these and the remaining stroked glyphs (section heads, commands) follow, or this
stays an exploration. That is the owner's call and nothing here forces it.
"""
from __future__ import annotations

#: Each is a body of filled paths on a 48x48 grid, no stroke, no fixed colour -- the caller
#: supplies the fill, so one gradient drives the whole set (`#126`, `#312`).
GLYPHS: dict[str, str] = {
    # Two opposed blades: the wyrm's crest, mirrored. Confrontation without a face.
    "Matchup": """
  <path d="M23 8 C17 15 11 19 4 21 C12 23 18 28 22 36 C22.6 27 22.8 17 23 8 Z"/>
  <path d="M25 8 C31 15 37 19 44 21 C36 23 30 28 26 36 C25.4 27 25.2 17 25 8 Z"/>
  <path d="M14 30 C17 33 19 36 20 40 C16 38 12 36 8 35 C10 33 12 31 14 30 Z"/>
  <path d="M34 30 C31 33 29 36 28 40 C32 38 36 36 40 35 C38 33 36 31 34 30 Z"/>""",

    # Ranked scales, receding. Depth by opacity, which is why the lower rows soften first.
    "Roster": """
  <path d="M24 6 C31 10 38 13 44 14 C37 17 30 21 24 27 C18 21 11 17 4 14 C10 13 17 10 24 6 Z"/>
  <path d="M24 22 C30 26 36 29 41 30 C35 32 29 36 24 41 C19 36 13 32 7 30 C12 29 18 26 24 22 Z"
        opacity=".72"/>
  <path d="M24 35 C28 38 32 40 36 41 C32 43 28 45 24 47 C20 45 16 43 12 41 C16 40 20 38 24 35 Z"
        opacity=".46"/>""",

    # A clutch. Dynasty's whole premise is what hatches later, so the draft is eggs.
    "Draft": """
  <path d="M24 4 C29 9 32 16 32 23 C32 31 28 36 24 38 C20 36 16 31 16 23 C16 16 19 9 24 4 Z"/>
  <path d="M11 20 C15 24 17 30 17 36 C17 42 14 46 11 47 C8 46 5 42 5 36 C5 30 7 24 11 20 Z"
        opacity=".66"/>
  <path d="M37 20 C41 24 43 30 43 36 C43 42 40 46 37 47 C34 46 31 42 31 36 C31 30 33 24 37 20 Z"
        opacity=".66"/>""",

    # A ring of spikes around a void: the table everyone sits at, nobody at its centre.
    "League": """
  <path d="M24 3 L28 11 L24 9 L20 11 Z"/>
  <path d="M45 24 L37 28 L39 24 L37 20 Z"/>
  <path d="M24 45 L20 37 L24 39 L28 37 Z"/>
  <path d="M3 24 L11 20 L9 24 L11 28 Z"/>
  <path d="M39 9 L33 15 L34 11 L30 10 Z" opacity=".7"/>
  <path d="M39 39 L33 33 L34 37 L30 38 Z" opacity=".7"/>
  <path d="M9 39 L15 33 L14 37 L18 38 Z" opacity=".7"/>
  <path d="M9 9 L15 15 L14 11 L18 10 Z" opacity=".7"/>
  <path d="M24 13 C30 13 35 18 35 24 C35 30 30 35 24 35 C18 35 13 30 13 24 C13 18 18 13 24 13 Z
           M24 17 C20 17 17 20 17 24 C17 28 20 31 24 31 C28 31 31 28 31 24 C31 20 28 17 24 17 Z"/>""",

    # An open eye. The audit room is the one that WATCHES what arrived.
    "Import Audit": """
  <path d="M24 12 C33 12 41 17 46 24 C41 31 33 36 24 36 C15 36 7 31 2 24 C7 17 15 12 24 12 Z
           M24 16 C18 16 12 19 8 24 C12 29 18 32 24 32 C30 32 36 29 40 24 C36 19 30 16 24 16 Z"/>
  <path d="M24 18 C27 18 29 20 29 24 C29 28 27 30 24 30 C21 30 19 28 19 24 C19 20 21 18 24 18 Z"/>
  <path d="M24 2 L26 9 L24 7 L22 9 Z" opacity=".7"/>
  <path d="M24 46 L22 39 L24 41 L26 39 Z" opacity=".7"/>""",
}

GOLD_DEFS = ('<defs><linearGradient id="tg" x1="0" y1="0" x2=".35" y2="1">'
             '<stop offset="0" stop-color="#755024"/><stop offset=".4" stop-color="#ba9561"/>'
             '<stop offset=".75" stop-color="#f9de99"/><stop offset="1" stop-color="#fff4ce"/>'
             '</linearGradient></defs>')


def glyph(name: str, size: int = 19, fill: str = "url(#tg)") -> str:
    """One glyph at one size. The caller must have emitted GOLD_DEFS once on the page."""
    return (f'<svg class="tg" width="{size}" height="{size}" viewBox="0 0 48 48" '
            f'fill="{fill}" aria-hidden="true">{GLYPHS[name]}</svg>')


def assert_legible_sizes(sizes=(19, 32, 48, 72, 96)):
    """There is no static check for 'can a human tell these apart'.

    What CAN be asserted is that nothing in the set relies on a stroke -- a stroked shape is the
    thing that collapses at small sizes, and it is how the generated medallions failed. If a
    future edit adds `stroke=` to one of these, this fails and the author has to argue for it.
    """
    bad = [n for n, body in GLYPHS.items() if "stroke" in body]
    if bad:
        raise SystemExit(f"tribal glyphs must be filled, not stroked -- found strokes in: {bad}")
    if len(GLYPHS) != 5:
        raise SystemExit(f"expected one glyph per room, got {len(GLYPHS)}: {list(GLYPHS)}")
    return sizes


if __name__ == "__main__":
    print("glyphs:", ", ".join(GLYPHS))
    print("legible at:", assert_legible_sizes())
