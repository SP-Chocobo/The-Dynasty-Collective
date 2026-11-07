# Round 4 — the front page, designed for the rewrite

**Read this whole file before drawing anything.** Then read the reference images in `_ref/`.

## What you are making

A **paired desktop + mobile front page** for Gold Wyrm Dynasty, as standalone HTML you can open
in a browser. Two files that are obviously the same product, not two unrelated designs.

This is **not** a Streamlit page. `api_surface.py` names the Streamlit layer as "the rendering
**the rewrite REPLACES**". You are designing for the real web front end that replaces it, so
nothing in Streamlit's widget set constrains you. Real CSS, real SVG, real type.

## The product, in one sentence

A dynasty fantasy football **triage surface**: what needs you, why, what it costs to ignore, and
what can wait. Not a dashboard. A dashboard shows numbers; a triage surface ranks claims on your
attention and is honest about how strong each claim is.

**The test it must pass:** a person opens the app between two other things. **In three seconds
they should know whether they can close it again.** Most weeks the honest answer is "nothing
needs you" — and that is the feature, not an empty state to apologise for.

## The owner's standing constraint, verbatim

> Emphasize clean dissemination of information over just having as much on the screen as you can
> fit. I dont need all the variables, i dont need every everything. clean who, why, and other
> valid options, at what cost. for any pick you make, there are going to be multiple valid
> options, which means that not taking the engine's #1 isn't inherently wrong

And their reaction to the current built page: **"That's too sterile, and that makes it ugly."**
Then: *"Icons, images, emblems, graphs or charts or something."* Then: *"Varying text sizing,
fonts, display. We have a gorgeous logo idea, and no cohesion to it."*

So: **restraint in INFORMATION, generosity in CRAFT.** The previous failure was treating visual
warmth as a variable to cut.

## The brand — this is the thing to cohere to

`_ref/logo_goldwyrm.jpg` is the real mark: a gold wyrm head, coiled, in beveled metallic relief
on pure black, with **GOLD WYRM** in a gilded Trajan/Cinzel serif and **D Y N A S T Y** widely
letterspaced beneath, separated by a thin rule with a diamond ornament.

Gold stops **measured off that logo**, not invented — use these, and use them as a *gradient*,
because the mark is brushed metal, not flat paint. A flat `#c9961a` beside it looks like a
different brand:

```
deep / shadow   #755024
body            #ba9561      <- note: only 39% saturation. Metal, not yellow.
bright          #f9de99
specular        #fff4ce
ground          #000000      <- the logo sits on pure black
```

Display face is **Cinzel** (fallback Trajan Pro, Georgia, serif) — `design_system.FONT_DISPLAY`
already declares it with a written rule: *"Brand voice, for the wordmark and top-level headings
ONLY — never for data."* Pair it with something that can carry body copy and numerals.

**Cinzel's numerals are a trap.** Letterspaced, "11" renders like Roman "II". Any number a
reader must read goes in a mono or text face, never Cinzel.

`_ref/wyrm_crop.png` is a crop of the mark (has a black box behind it — treat as placeholder;
a transparent 512px PNG is coming).

## Position colours — already ruled, use them

From `design_system.POSITION_PILL_TOKENS`, one home, do not invent others:

```
QB #2a81fc   RB #0ca89c   WR #4aa8ef   TE #ff6042   K  #fab87e
DEF #ef7fc0  DL #4cec4c   LB #ff45ed   DB #6ad8f0   IDP #99a851
absent/unknown #b0a28a
```

## THE HARD PART — what this engine will and will not say

This project has withdrawn published findings rather than keep a number it could not defend.
**A design that invents a quantity is not a design, it is a liability.** Six of the prior mocks
failed here. Treat this table as law.

### Real — you may draw these

| quantity | where it comes from |
|---|---|
| bye damage per week, in trade-value points | `lineup_optimizer.bye_collision` — solves the lineup with each week's byes removed. **Value lost, not bodies lost.** |
| share of season's bye damage in the worst week | `bye_concentration` |
| thin positions | `depth_ratings` WEAK + NO_PLAYERS, peer-relative |
| positional depth **label** | `depth_label` → exactly `Strong` / `Average` / `Weak` / `None — no rostered players here` |
| starters filled / total slots | `lineup_readiness.compute_readiness` **in production**. In THIS fixture it is `optimize_lineup` + `slots_from_roster_positions`, which is exactly why it is stamped CONSTRUCTED — no human submitted a lineup for a replayed seat. |
| material injuries **on starters** | same call, gated by `is_material_injury_status` |
| structural holes (no body who can fill a slot) | `lineup_optimizer.slots_from_roster_positions` + `slot_coverage`. **NOT `league_usable_positions`** — `capture_front_fixture.py:139-144` argues at length that it is wrong here because it expands flex slots. The fixture's own provenance string carries the same wrong attribution; both are defects. |
| record, points for / against | `league_standings.team_standings`, from Sleeper's own settings |
| which future picks have MOVED | `pick_ledger.build_pick_ledger` — its docstring says "deliberately just the diffs, not a full inventory". **"Which picks you own" is NOT reachable**; Sleeper lists a pick only once it has been traded. |
| data freshness grade + per-source ages | `freshness.build_freshness_manifest` + `recency_grade` |

### Forbidden — do not draw these, in any styling

| | why |
|---|---|
| Team Rating / Team Index / letter grades (A, A-) | does not exist, no model behind it |
| Playoff odds, title odds, win probability | does not exist |
| positional strength as a **0-100 bar or meter** | the LABEL is real; the continuous score is not. Draw four discrete steps tied to the four labels, never a meter. |
| "% rostered", trending adds, "primary add" | no ownership/trending call exists in `sleeper_client` |
| anything about **Questionable** players | `compute_readiness` deliberately excludes it — the engine measured that designation as carrying nothing, and surfacing it spends attention on noise |
| a POSITIVE all-clear for injuries | production renders an empty `starter_injury_flags` as **silence**, not as "no injuries". Absence of a flag is not evidence of health — the fixture's own starters include a player on IR. |
| rookie pick **value** | `estimate_future_pick_value` is withheld: 1.89 slots mean error on 12. Pick COUNTS are fine; pick PRICES are not. |

### Absence has a grammar

A value that was not measured renders as an **em dash carrying its reason**, never as `0`, never
as blank, never as a reassuring default. A value that is a floor rather than a total says so
(`≥`). A value fabricated for a demo is stamped `CONSTRUCTED` on the page. These are four
different states and a reader must be able to tell them apart.

## The data you are designing against (a real replayed roster)

```
bye profile   wk6 95   wk7 8   wk8 51   wk9 4   wk10 56   wk11 23      (trade-value pts)
              worst week 6, carrying 40% of the season's bye damage, 1 starter out
thin          DEF: 1 rostered, label `Weak`  -- earned on the COUNT branch (three peers unpriced)
              TE:  2 rostered, label `Weak`  -- earned on the VALUE branch, 1 of 2 priced, a FLOOR

              *** CORRECTION. An earlier version of this block said "(bottom of league)" for both,
              and three designs drew that sentence because I licensed it. IT IS FALSE AND THE
              ENGINE COMPUTES NO RANK. `depth_label` is a ratio band against the league mean
              (>=1.3 Strong, <=0.7 Weak, else Average); nothing in the tree ranks teams within a
              position. Two independent replays measured this seat: DEF is a FIVE-WAY TIE at
              count 1 and is the JOINT-HIGHEST PRICED DEF room in the league; TE's count of 2 is
              the MODAL count, held by 8 of 12 teams. Say the label. Never say the rank. ***
holes         none
lineup        10 of 10 filled    [CONSTRUCTED — a replayed battery seat, not a live roster]
record        absent — no capture holds a roster's result
pool          5,357 players
```

Also design the **quiet state**: no holes, no thin positions, byes spread evenly. Most weeks
look like this and it must not look like a broken page.

## Destinations that actually exist

`Matchup` · `Roster Maintenance` · `Draft Room` · `League` · `Import Audit` — **five** views in
`app.py`'s `st.segmented_control`. **The Prytaneum is NOT a sixth view**: it is
`st.container(key="debate_dock")`, a persistent dock rendered under every view. Five rooms and
one dock, and a design that draws six identical doors is wrong about one of them.

Trade Calculator, Free Agents and Standings exist **inside** those views, not as top-level
destinations. **Player Compare, Trade Finder, Waiver Wire, Pick Calculator, Roster Health,
League Notes and Analytics do not exist** — several mocks advertised them. Do not add doors to
rooms that aren't built.

## Prior art in `_ref/` — read it, then beat it

- `mock_60/61` — "The Keep": full stone-hall environment, gold shield doors. Gorgeous; 60 spends
  ~25% of page height on scenery and puts a castle photo behind the most important sentence.
- `mock_62` — modern SaaS dashboard. Competent, generic, and **six of its panels are fabricated**.
- `mock_63` — mobile triage. Best mobile shape so far; its claims drifted into waiver-wire adds
  the engine doesn't fetch.
- `mock_64` — the quiet state. Contains the best single idea in all six: a **"CLOSE THE APP"**
  affordance, which turns the three-second test into a control. (Its logo art has a typo,
  "DYNASTYY".)
- `mock_65` — "Command Deck": densest, and the most fabricated.
- `claude_c_brand.png` — my own pass. Right palette, right type, but the doors are inert and the
  smallest text is 9.6px.

## Constraints that are not negotiable

- **Mobile viewport is 390 × 664 CSS px** — a real iPhone browser viewport, not the 844pt spec
  sheet. The tab bar and toolbar take a fixed bite. Budget **two screens of scroll, maximum**.
- **No text below 12px**, computed. The render gate enforces this and the prior pass failed it.
- **Contrast**: body text ≥ 4.5:1 on its own background. One recede-role may sit at AA-large.
- **Tap targets ≥ 44px.**
- Standalone HTML, inline CSS, no build step. Google Fonts is the only external host; everything
  else inline or SVG.
- Dark only. This brand has one world.

## Deliverable

Write into `ui_explore/round4/<your-slug>/`:

- `desktop.html` and `mobile.html` — the pair, sharing one visual language
- `NOTES.md` — what you decided and **why**, where you deviated from this brief and what it
  bought, plus anything you believe is wrong with your own design. Be specific; a note saying
  "clean and modern" is worthless.

Draw the real numbers above. Use SVG for icons and emblems — generated raster is coming later for
large crests, but nothing you draw should depend on art that doesn't exist yet. If you want a
crest slot, draw a placeholder that is obviously a placeholder.

**Open your own pages and look at them before you finish.** Playwright and Chromium are
installed; `browser_binary.find_chromium()` from the repo root gives the path. Screenshot both
files, check the computed minimum font size, check nothing overflows at 390px. A design that was
never rendered is a guess.
