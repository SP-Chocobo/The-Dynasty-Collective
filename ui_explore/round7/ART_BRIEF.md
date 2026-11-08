# What to bring back from Midjourney

The page has **slots**. `hero_band()` and the panels take an image without any other change, so
art can land whenever and nothing else moves.

## The constraints that matter more than the subject

Get these wrong and a beautiful image is unusable:

- **Near-black ground.** `--bg` is effectively `#0b0b0d`. Art with a lighter field shows a seam
  where it meets the page. Ask for "near-black background", not "dark".
- **Gold, and only gold.** The measured logo ramp is `#755024 -> #ba9561 -> #f9de99 -> #fff4ce`.
  **No blue.** The existing `assets/header_banner.jpg` is a blue football in space and it fights
  this palette, which is why it is currently run at 0.22 opacity under a gold wash.
- **No lettering.** Any text Midjourney renders will be wrong, unlocalisable and un-editable.
- **Dark on the side the text sits.** For the header band that is the LEFT third; `app.py`'s own
  comment records this rule for the existing banner.
- **Nothing important near an edge.** Everything here is `background-size:cover`, so edges crop
  at some viewport.

## Already done — do NOT generate these

**The emblem is sourced.** The real gold dragon was in the tree the whole time at
`ui_explore/round4/_ref/wyrm_crop.png` (a crop of goldwyrm.com). `assets/wyrm_emblem.png` is
derived from it with alpha keyed from luminance, trimmed and sized to 128px wide, and it is now
the mark in the top left. Nothing to generate here.

## The pieces, in the order they would earn their place

| # | slot | size | what it is |
|---|---|---|---|
| ~~1~~ | ~~landing header band~~ | **DONE** | `assets/header_wyrm.jpg`. See the note below on why the slot changed. |
| 2 | empty-state illustration | **~900x900** | for "No leagues yet" — one coiled gold wyrm on near-black, generous margin, more linework than render. |
| 3 | in-league dashboard band | **1680x260** | wants to read as a DIFFERENT room from the landing page while sharing the palette — the landing page is a hall, a league is a chamber. |
| 4 | five room marks | **512x512 each** | Matchup / Roster / Draft Room / League / Import Audit. Only if you want them; see the caution below. |

## Where art does NOT help, and why I did not ask for it

**Every icon on the page is inline SVG, deliberately.** A glyph drawn in SVG is crisp at any
size, takes its colour from the theme tokens, costs no network request, and cannot smuggle in a
hardcoded hex that `#312` would later have to hunt down. A raster icon has none of that and goes
blurry on a retina phone. **An illustration is worth an image; an icon is not** — so if you
generate the room marks, they are decoration beside the glyphs, not replacements for them.

Same for the crest, the laurels, the hairlines and the hatch texture: all drawn, all themeable.

## What the first band taught us about the SLOT

The first four candidates were rendered into the slot as it then was -- 104px tall, 46% wide,
0.22 opacity -- and **all four were indistinguishable**. Four completely different images,
identical result. That is the tell that the slot, not the art, was the constraint: a band that
reduces any image to warm noise cannot justify 90KB, because CSS produces the same effect for
nothing.

So the slot was widened to full-bleed, 215px, 0.64 before judging the art. Only then did the
candidates separate, and only then was it worth picking one.

**Two things that fell out of that, which apply to every band from here:**

- **Stacking is load-bearing.** At full height the band covered the room tabs and the first
  panel heading and washed them out. It sits at `z-index:0` with every content block lifted to
  `2`. A new full-bleed image needs that check repeated, by looking.
- **Text over art needs measuring, not eyeballing.** The "Sleeper <name> / synced" block sits
  over the brightest part of the dragon and LOOKED unsafe. Measured with the text hidden so the
  ground could be sampled: worst-case **7.73:1** against a 4.5:1 floor. The impression was
  wrong; the gradient overlay was already doing the work. (A first attempt at this measurement
  sampled the brightest pixels in the region and got `rgb(176,162,138)` -- which is the INK
  colour, not the ground. It measured the text against itself. Hiding the text first is the
  only way to see what is behind it.)

## Weight

The current page embeds the banner as base64 and is **111 KB, of which 64 KB is the image**.
That is acceptable for one band. A second full-bleed image per page is the point where these
should become real files rather than data URIs.
