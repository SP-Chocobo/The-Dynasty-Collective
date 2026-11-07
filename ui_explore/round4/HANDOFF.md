# Round 4 — state at session end

## Where this is

Three paired desktop+mobile front-page explorations, each attacked by two independent adversaries
(design and product, deliberately split), then sent back for refinement. **The refinement pass was
in flight when the session ended** — see "Unfinished" below.

```
ui_explore/round4/
  BRIEF.md        the design brief, CORRECTED in six places the adversaries found wrong
  ADVERSARY.md    the two-front critique brief
  VOICE.md        the voice spec — "the app wants nothing from you"
  HANDOFF.md      this file
  _ref/           the real logo, the six prior ChatGPT directions, my own first pass
  keep/           desktop.html mobile.html NOTES.md CRITIQUE_DESIGN.md CRITIQUE_PRODUCT.md
  deck/           desktop.html mobile.html NOTES.md CRITIQUE_DESIGN.md CRITIQUE_PRODUCT.md
  threshold/      desktop.html mobile.html desktop_loud.html NOTES.md CRITIQUE_* .md
```

All three verdicts: **worth refining, none close to shippable.**

## The three directions

| | bet | one component it would keep |
|---|---|---|
| `keep` | the app as a *place* — severity carried by frame SHAPE, crests as nav | the heraldic frame set |
| `deck` | honest density — bye ledger naming who sits, "cleared" list of measured negatives | the four-state value grammar |
| `threshold` | restraint as luxury — quiet state as the PRIMARY design | the CLOSE THE APP control |

Measured, independently, before refinement: mobile scroll 1296 / 1298 / 1299 against a 1328
budget; 12.0px font floor on all; zero console errors. `deck`'s only sub-44px tap target is its
wordmark link (153×32 mobile).

## Cross-cutting findings — these outlive any one design

1. **All three charts fail non-text contrast.** Five of six bars in every design, 1.25:1–2.30:1
   against a 3:1 floor, measured independently by three adversaries sampling rendered pixels.
   Three designers, three chart constructions, one result: **gold-on-near-black cannot carry a
   low-value bar.** It also explains why all three put a direct label on every bar — they were
   compensating for marks that do not render. This needs a real solution, not a hex nudge.
   *(I attempted to verify this myself twice and failed twice — first probe could not see
   gradient fills, second matched `display:none` elements. The finding rests on the three
   adversaries' measurements, not on mine.)*
2. **No design has an "I don't know" state.** Replace every value in `threshold`'s ledger with
   "not measured" and its first screen is byte-for-byte unchanged. Production already has this
   fourth tone (`app.py:3825-3828`); no mockup does.
3. **Every design drew six identical doors.** The Prytaneum is `st.container(key="debate_dock")`
   at `app.py:6917` — a persistent dock, not a view. Five rooms and one dock.
4. **Both designers' volunteered weaknesses were the safe ones.** `threshold` confessed a
   gradient defect that measures 4.42:1, not the 2.9:1 it claimed — wrong about its own design
   *pessimistically*.

## REPO DEFECTS found by adversaries sent to review drawings — recorded as `#336` / `#336b`, NOT YET REPAIRED

These are the most valuable output of the round and they are about shipped code, not mockups.

1. **`build_front.py:131` asserts a rank the engine never computes.** "bottom of this league at
   the position" — `depth_ratings.depth_label` is a ratio band (`>=1.3` Strong, `<=0.7` Weak),
   and nothing in the tree ranks teams within a position. **It is also false**: two independent
   replays agree DEF is a five-way tie at count 1 AND the joint-highest *priced* DEF room in the
   league. The page tells the reader their best room is their worst. It is carried in the
   byte-identity-guarded `round3/front.html:113`, certified under `#333`.
2. **The fixture's `structural_holes` basis names the function the code rejects.**
   `capture_front_fixture.py:146` calls `lo.slot_coverage`; lines 139-144 argue at length that
   `league_usable_positions` is wrong. Line 14's docstring and the emitted provenance string both
   cite it anyway.
3. **A material injury on a starter is suppressed behind a false reason.** Fixture starter
   `12484` is Jayden Higgins, `injury_status: "IR"`; `is_material_injury_status("IR")` is True.
   The fixture says "no live injury feed for a replayed seat". Verified independently.
4. **`round3/front.html` denominates in "UV pts"** while the value is a Draft Sharks trade-value
   figure. Different scales.

**The defect class, named: prose that outruns its function.** Every surface here stamps its
FIGURES with a basis. No surface stamps its SENTENCES, and no ratchet reads them. 4,393 tests and
a byte-identity guard pass with defect 1 in place, because every one of them checks a number.

## Unfinished

- **Three refinement agents were running when the session ended.** They were told to write only
  inside their own directory and to run no git commands. Check for `REFINEMENT.md` in each of
  `keep/`, `deck/`, `threshold/` — if present, that agent finished; if absent, its refined files
  may be partial. `git status` will show anything uncommitted.
- `#336` and `#336b` are recorded in `POST_AUDIT_PLAN.md` and **not repaired**. Repair was
  deliberately deferred so the critiques could read an unmodified fixture.
- The owner's stated next step after refinement: **take the strongest ideas from all three and
  assemble one version.** The method agreed: pick ONE as the spine and graft solved *rules* from
  the others — not a collage of best parts, which produces an incoherent whole. Each `NOTES.md`
  ends with a component inventory written for exactly this, with portability stated honestly.
- A live disagreement left deliberately unresolved for `deck` to settle in writing: its two
  adversaries split on the `×LG` ratio column. Design says keep (only mark distinguishing TE from
  QB; defect is priority inversion). Product says delete (nothing returns the ratio; the `·n`
  fallback notation fires on the peer set, not the room, so it is dishonest).

## Owner context a new session needs

Standing constraint, verbatim: *"Emphasize clean dissemination of information over just having as
much on the screen as you can fit. I dont need all the variables, i dont need every everything.
clean who, why, and other valid options, at what cost."*

On the first built page: *"That's too sterile, and that makes it ugly."* Then: *"Icons, images,
emblems, graphs or charts or something."* Then: *"We have a gorgeous logo idea, and no cohesion
to it."* Then, on all three round-4 designs: *"They feel like the old army ads. The army needs
You"* — which produced `VOICE.md`.

The brand is gold-on-black, a coiled wyrm, Cinzel. The gold is a **gradient** measured off the
real logo (`#755024 → #ba9561 → #f9de99 → #fff4ce`, body only 39% saturation), not
`design_system`'s flat `#c9961a`. `assets/` holds a football-in-a-nebula photo that has nothing
to do with the logo and is the original cohesion failure.
