# A main page for the Command Center

> **Status: live design brief, awaiting the owner's answers to the four questions at the end.**
> What this is: the argument for what the app's front page should be, what it may say today
> without one line of new engine work, and which of the repo's two design systems wins where
> they disagree. Nothing here is built yet. Every engine quantity named below was read out of
> its own source while writing this, and the function that produces it is named.

## What is there now

`app.py` opens on a banner — brand eyebrow, the league's name, a caption of format facts — and
then hands you a view picker: Matchup, Roster Maintenance, Draft Room, League, Import Audit,
The Prytaneum. With no league synced it is a title and one sentence telling you to sync.

So there is a header, and there are destinations, and **nothing in between**. Nothing answers
the question a person actually arrives with, which is not "which view do I want" but **"is
anything wrong, and what does it cost me to ignore it."** Today you answer that by opening
views in turn and reading them.

## The one idea

The draft room's constraint, applied one level up. The owner's words for the board were:

> clean who, why, and other valid options, at what cost

A front page is that same sentence about a **week** instead of a pick: what needs you, why, what
it costs to ignore, and what can wait. It is a **triage surface, not a dashboard**. A dashboard
shows numbers. A triage surface ranks claims on your attention and is honest about how strong
each claim is.

The test it has to pass is the three-second one the phone review used: a person opens the app
between two other things. In three seconds they should know **whether they can close it again.**

## What it can say today, and what each claim actually costs to wire

Every signal below already exists and is already tested. What differs — and what I got wrong in
the first draft of this file — is how far each one is from the app. Three are already on screen
somewhere; one is a single new call; one is real work. I checked each against `app.py` rather
than assuming, because "the engine already computes it" and "the app can show it" are not the
same sentence, and the gap between them is the whole build estimate.

| signal | where it comes from | wired today? | the claim it supports |
|---|---|---|---|
| starters filled vs the league's own slot count | `lineup_readiness.compute_readiness` → `filled_starting_slots` / `total_starting_slots` | **yes** — `app.py:3765`, Matchup | "7 of 9 starters set" |
| **material** injuries on starters only | same → `starter_injury_flags`, gated by `player_universe.is_material_injury_status` | **yes**, same call | "Etienne is Out" |
| positions where you are thin **against the league** | same → `thin_positions`, via `depth_ratings.depth_label` | **yes**, same call | "thin at TE" |
| record and place | `league_standings.team_standings`, reading Sleeper's own `settings.wins/losses` | **yes** — `app.py:6085`, League | "4-3, 6th" |
| positions you cannot field at all | `player_universe.league_usable_positions` against the roster's own positions | **no** — one call; `player_universe` is already imported | "no kicker on the roster" |
| the week your byes actually cost you | `lineup_optimizer.bye_concentration` → `worst_week`, `worst_week_loss`, `concentration` | **no, and it is the real work** — see below | "week 9 costs 127.0 — 62% of your season's bye damage, in one week" |
| whether any of the above is a floor | `bye_*.basis`, and `TeamDiagnostics.unpriced_players` where diagnostics are used | with the number it qualifies | "…and that is a floor: 2 players could not be priced" |

**So the claim band ships on day one from calls the app already makes.** Three of its four
likeliest claims come out of one `compute_readiness` result that the Matchup view already has in
hand, and the fourth is a set difference. That is the cheap, correct first version, and it is
worth saying plainly before the interesting signal below argues for more work.

Three of these deserve their own note, because each one encodes a decision this page must
inherit rather than quietly re-open.

**The injury gate.** `compute_readiness` deliberately excludes Questionable, and the code says
why: raising it would spend "a person's attention on a designation the engine has measured as
carrying nothing." A front page that widens the net to look busier breaks a ruling that is
already enforced in code, and it breaks it in the one place where a wider net is most tempting.

**The bye signal is the find.** It is the best unused claim in the repo for this surface, and it
is already computed, already tested, and already written up. `bye_collision` solves the lineup
with everyone on a given team's bye removed, so it measures **value lost, not bodies lost** —
its own docstring explains that counting heads ranks two rosters backwards. `bye_concentration`
then reports the *shape*: the share of a season's whole bye cost landing in the single worst
week, measured at 41–127 trade-value units across twelve real rosters that all sat at the
*same* headcount floor. "The bodies were spread; the value was not." That is exactly a what-does-
it-cost-to-ignore claim, it is knowable in advance, and no surface in the app shows it.

It also comes with two constraints, one principled and one practical.

The principled one: `bye_collision` is deliberately an **observable, not a valuation term** —
the measurement behind that decision is in its docstring. So the front page reports it as a fact
to notice and a week to plan around. It never ranks a trade by it and never folds it into a
score.

The practical one, and the correction to my own first draft: **this is not one line of wiring.**
`app.py` does not call `optimize_lineup` anywhere, and does not read a bye week anywhere — its
only use of `lineup_optimizer` is `slots_from_roster_positions` to count slots. `bye_collision`
needs an optimizer-shaped roster list (keyed `id`, carrying a value and a `bye`), and the bye
itself comes from `DataMerger.bye_week_by_team`, which the app has never touched. So the cost is
a shape adapter plus a mapping read plus one call — a day's careful work, not a sentence.

Note also which door this does *not* go through. `roster_diagnostics.compute_team_diagnostics`
carries the same bye numbers, but it takes a `DraftTrajectory` and its only non-test caller in
the tree is a baseline comparison script — a live league's roster is not a trajectory. The
front page should call `lineup_optimizer.bye_concentration` directly, which takes a plain player
list and needs no draft at all. Going through diagnostics would mean simulating a draft to
describe a roster that already exists.

**Absence stays visible.** `concentration` is `None`, never `0.0`, when a roster has no bye
damage — a roster with nothing to lose has no shape. `unpriced_players > 0` makes every value on
a `TeamDiagnostics` record a **floor** rather than a total, and `basis` can say `partial`. The
page carries the floor in the sentence (`starting_lineup_statement()` already shows the form) or
it does not show the number. This is register item #187, and four surfaces currently keep it.

## Shape

**One column, three bands, nothing below the fold at rest.**

1. **The claim band** — at most three cards, ranked by what it costs to ignore them, each one a
   sentence and a route. "You are on the clock, pick 5.06" outranks "week 9 costs you 127.0 in
   one week", which outranks "thin at TE". A Questionable starter is not on this list at all.
   If nothing has a claim, the band says so in one line and the page is allowed to be short.
   **An empty state reading "nothing needs you" is the feature, not a gap to fill.**
2. **The week band** — your matchup, the live score if there is one, filled/total starters, your
   record. Facts, no advice.
3. **The doors** — the existing views as a row of large targets, in a **fixed** order so they
   never move between visits. Same reasoning that kept the phone drawer's filter chips in slot
   order rather than board order: the board's own order moves in all six formats, and a control
   row that re-sorts itself moves eight tap targets between two visits.

Ordering the claim band is the one genuinely hard part, and it is a ranking **across incomparable
units** — a pick clock in minutes, a bye in trade-value, a thin position in a peer label. The
honest version is a fixed severity ladder with the reason written on each rung, not a computed
score that implies the units were commensurable. That is a decision to record, not to hide.

## Theming — it already exists, in two places that disagree

`design_system.py` is the real system, and it is more disciplined than I expected going in:
tokens separated by measured CIE Lab ΔE, a ruled decision that gold is brand chrome and may not
carry semantic load, base tokens as fills with `-b` brightenings as the text colours, and a
written legibility policy with an instrument (`legibility_report`) rather than a build ratchet.

How far apart they actually are, measured rather than eyeballed — `_palette.py` in the
prototype directory reads `design_system.TOKENS` and the prototype's own `:root`, and compares
them in CIE Lab ΔE using `test_design_system._delta_e`, which is where that function already
lives:

```
27 prototype tokens, 29 app tokens, 27 share a name
(`#327`: was "37 prototype tokens". `#320` moved the ten position pills out of the prototype's
 `:root` block and 37-10=27 exactly. This figure is read from `_palette.py`'s own output rather
 than recomputed -- an independent regex over the same file returned 32 because it counted the
 font and radius properties as tokens, and that reconstruction was briefly used to call the
 instrument's correct number wrong. Observe the production quantity, never rebuild it.)
26 of 27 shared token names carry a visibly different colour (dE > 2); 0 are identical.

 18.37  violet     #6d3fd6 -> #9457d4        3.71  bg         #0c0a07 -> #15120b
 16.20  sky        #1356c9 -> #1466c4        4.58  surface    #17130d -> #1f1a11
 15.15  emerald    #0b8f57 -> #1a9e4b        3.51  surface-2  #120f0a -> #1a1610
  7.57  dim        #897c61 -> #776d5a        2.41  ink        #f2ead9 -> #ece3d2
```

**An earlier draft of this file said the two share their three grounds. They do not** — the
prototype's are measurably darker, and not one of the twenty-seven shared token names carries
the same colour on both sides. That claim was written from reading the two files and seeing
similar-looking hex; the instrument disagreed, which is the whole argument for having one.

**SUPERSEDED (`#327`): the pill table below no longer measures anything.** `#320` made the
prototype's pills DERIVED from `design_system`, so all ten now measure **dE 0.00** prototype-vs-app
(read from the built `v4_doors.html`). The table's "app NO ENTRY" rows for DL, LB and DB have had
entries since `#311` (`#4cec4c`, `#ff45ed`, `#6ad8f0`), and its "app QB `#8f86f0`" was superseded
by `#318` (`#2a81fc`). Kept as the record of what the divergence was before it was closed.

The position pills diverge further, and there the difference is functional rather than cosmetic:

```
 33.28  WR   #2f7df0 -> #4aa8ef      --  DL   prototype #e35d7a, app NO ENTRY
 32.82  DEF  #e0406d -> #ef7fc0      --  LB   prototype #b08cf5, app NO ENTRY
 22.83  QB   #8366f1 -> #8f86f0      --  DB   prototype #d9a21c, app NO ENTRY
```

> **SUPERSEDED (`#327`).** The paragraph below was true when written and every clause of it is
> false now. It is kept rather than rewritten because a published claim that was wrong is
> restated with its evidence, not quietly edited.
>
> `#311` took `POSITION_PILL_TOKENS` from six entries to ten, giving DL, LB, DB and IDP their
> own hues, and replaced the K fallback with `POSITION_PILL_ABSENT` (`#a79a83`), a deliberately
> quiet non-colour. **The capability gap is closed**, and the direction of the remaining
> difference is the opposite of what this says.
>
> This is the SECOND HOME of this sentence. `#322` repaired the identical claim in
> `ui_explore/round2/fableA/_palette.py` and nobody grepped for the other copy — a `#126`
> duplication sitting underneath the stale-prose defect. It was found by an adversarial pass.
>
> ~~The app's `POSITION_PILL_TOKENS` has six entries and falls back to K's neutral for anything
> unmapped — so in an IDP league the app draws DL, LB and DB in one colour, and the prototype
> gives each a hue. Two of the fixture's six formats are IDP leagues. That is not a palette
> preference to reconcile; it is a capability the prototype has and the app does not.~~

**The front page is the right place to resolve that, and the resolution is one-directional:**
`design_system.py` is the system of record. It has the discipline, the instrument, and the
owner's ruling behind it. The prototype palette converges toward it, not the reverse.

**And the display face is not an exception at all — I had that backwards.** `design_system.py`
already defines `FONT_DISPLAY` as Cinzel, with a written rule beside it: "Brand voice, for the
wordmark and top-level headings ONLY — never for data," and a fallback chain ending at Georgia
so a machine with no webfont access still renders a classical serif. The prototype's three faces
are byte-for-byte the app's three, Cinzel included, and it uses the display face on door headers
— top-level headings, exactly as the rule says.

What is true is that **`app.py` never uses the face its own design system defines.** The only
consumers of `FONT_DISPLAY` in the tree are `mockups/common.py` and `mockups/dock_common.py`.
So there is nothing to adopt and nothing to drop: the system of record already ruled, the
prototype already complies, and the app is the side not following it.

One divergence is the owner's call and is **not** settled by "the app wins": the prototype's
`--dim` now measures 4.50:1 and the app's documented `dim` is 3.39:1 on purpose — it is the one
recede-into-the-page role, held to AA-large so that raising it would not make it
indistinguishable from `muted`, and that decision is pinned by a test. Two surfaces, two
defensible answers, one of which has to give.

## What I would not do

- **No charts.** Nothing on this page is a time series a person acts on. A sparkline of roster
  value is decoration, and the standing constraint rules it out. (The bye profile is the one
  thing with a shape — and `weeks` is six or seven numbers, which is a sentence, not a chart.)
- **No insights feed.** An endless list of generated observations is the opposite of triage: it
  weights every claim equally and therefore makes none of them urgent.
- **No number without a basis.** The engine withholds three quantities on purpose. A front page
  that re-derives something to fill a card would break a contract four surfaces keep — and
  `rookie_draft.estimate_future_pick_value` is sitting right there, unwired, for exactly that
  reason.

## One thing a prototype cannot fake

The draft-room prototypes work because `ui_explore/fixture.json` holds real board states,
replayed from recorded pick sequences. A front-page prototype can be fed the same way for the
readiness, depth and bye signals — all three are functions of a roster, and a replayed draft
produces real rosters.

**The record cannot.** `team_standings` reads Sleeper's own `settings.wins/losses`, and nothing
in `data/league_captures/` holds a roster's contents or a result — those files capture a
league's *rules* (roster_positions, scoring, format), which is what they were built for. So a
week-band prototype either marks the record as unavailable or invents one, and inventing one in
this repo is the thing four surfaces are built not to do. The honest prototype shows the band
with the record absent and labelled, which also usefully exercises the absence contract on the
one surface where a reader is least likely to tolerate a dash.

## And one thing a prototype can only reach sideways

`positional_depth` — the function behind the "thin at TE" claim, and behind the Trade
Calculator and the League Depth Map — **lives in `app.py` and nowhere else.** `app.py` has 69
top-level Streamlit calls and no `__main__` guard, so importing it runs the application. That
means no fixture, no harness and no prototype can call this quantity directly.

The repo already works around it: `test_positional_depth_coverage.py` reaches the function by
parsing `app.py` and loading the function's source out of it (`_load_function`). That is an
established pattern here rather than a hack, and a front-page fixture can use the same door.

But it is worth naming as what it is. A production quantity three surfaces depend on has
exactly one home, and that home is the one module nothing else can import — so every consumer
outside the app either re-implements it (a second source of truth, which #126 forbids) or
text-extracts it. Lifting `positional_depth` into a module beside `depth_ratings`, which is
where its judgment already lives, is a small refactor with three existing callers and a test
that would get simpler. **It is the honest first cost of this page**, ahead of any layout.

## The gap the owner named: nothing navigates to or from the draft

> "The ui as designed for the draft doesn't account for buttons, commands, website navigation
> to or from the draft."

Correct, and worth stating as an inventory rather than an impression. What chrome each surface
actually carries, read off the templates:

| | what it has | what it does not |
|---|---|---|
| desktop `v4_doors` | a wordmark (`Gold Wyrm`) and a league line | no nav, no back, no commands |
| phone `m1_stack` | four bottom-dock buttons — Every name, Rosters, Draft board, Debate | **no wordmark, no league name, no view, no way out** |
| the real app | `st.segmented_control` over five views, `app.py:3685` — and it is BELOW the empty-state `st.stop()` at `app.py:3610` | no nav at all until a league is synced |

**CORRECTION, 2026-11-04 — this table said "six views, `app.py:3806`" and both halves were
wrong, and so was the count I reported from the running app.** Measured against `app.py` and
against the app actually serving on :8787:

* The picker carries **five** options, not six — `MATCHUP_VIEW, MAINTENANCE_VIEW, DRAFT_VIEW,
  LEAGUE_VIEW, IMPORT_VIEW` — declared **unconditionally** at `app.py:3685`. `3806` is near the
  `if main_view ==` branch chain that consumes it, not the control.
* I then reported "the view picker renders only 3 buttons, because most views are gated behind a
  synced league." **Both clauses were false.** Nothing gates the picker. What I counted was the
  single `stButtonGroup` in the DOM, and it is **in the sidebar** (`inSidebar: true`, three
  buttons) — a different control entirely. The view picker was not in the page at all.
* The reason it was not in the page is the finding worth keeping: `app.py:3610` runs
  `st.title(...)`, `st.info("Sync a Sleeper username ...")`, `st.stop()` when `not snapshot`.
  **Unsynced, the app renders zero view-picker buttons**, because the picker is seventy-five
  lines below a `stop`.

That sharpens the brief's own premise rather than softening it. The front page is meant to
replace that two-line empty state — so it cannot be a sixth view, or a branch of the existing
`if main_view ==` chain, or anything else below `app.py:3610`. Every one of those positions is
unreachable in exactly the state the page exists to serve. It has to live ABOVE the stop, which
makes "where does it go" a structural question about `app.py`'s top, not a navigation question.

The method note, since this is the second time in this session a count was reported before it was
understood: the number came from a selector I had not checked the provenance of. Source said five,
my own instrument said three, and the honest reading was that one of them was measuring something
else — which is what it turned out to be. `.claude/skills/engine-measurement/SKILL.md` already
names this family ("not a crash, a plausible number about something else"); it applies to DOM
queries exactly as it does to engine probes.

**SECOND CORRECTION, 2026-11-06 (`#332`) — every line pointer in this file was wrong, including
the two the correction above had just re-pinned two days earlier.** Measured against `app.py` as
it stands:

| pointer | this file said | measured |
|---|---|---|
| the only `st.stop()` | `app.py:3667` | **3610** |
| the five-view `st.segmented_control` | `app.py:3742` | **3685** |
| `lineup_readiness.compute_readiness` | `app.py:3886` | **3765** |
| `league_standings.team_standings` | `app.py:6200` | **6085** |

Four of four. That is not a maintenance lapse, it is the FORM failing: a line number in prose
decays on every edit above it, silently, and `app.py` is 7,326 lines of actively edited surface.
`#313` already ruled that a pointer is only as good as its target's maintenance. The durable
form is the one used throughout the table above — **name the symbol and let a reader grep** —
with the line number kept beside it as a convenience that is allowed to rot. All four are
corrected here, and all four are expected to rot again; the symbol names are what this file
actually relies on.

Two things follow from that table.

**The prototypes were briefed as a view and built as if they were the app.** In production the
view picker sits *above* the board, supplied by Streamlit, so the board never needed one. That
works on the desktop. On the phone it does not: a five-item picker at the top, a 68px dock at the
bottom and the board between them is chrome at both ends — and a five-item picker at the top is
precisely the "very busy at the top" that the header cleanup was asked to fix. The cleanup also
removed the only place a wordmark or a back could have lived, so **the phone currently cannot
say which league or which view you are looking at.**

**The dock is contested space, and the question is what a permanent bottom bar is for.** All
four of its buttons today are board-local: three reference sheets and one billed action. A
permanent bar is normally an app's spine, not one view's toolbox.

The geometry does not decide it, which is worth knowing before arguing from it. At 390px the
dock gives 97px per button at four across, 78px at five, 65px at six — all well clear of the
44px tap floor the render gate enforces. So the constraint is label legibility, not reach.

Two ways to resolve it, and I would take the first:

1. **The dock holds views; board tools move into the board.** The app's destinations are its
   permanent furniture; a view's own tools belong in the view. `Every name` is already the
   drawer and has a natural home on the board. `Rosters` and `Draft board` are reference
   overlays and can collapse into one affordance. `Debate` is billed and live only on the
   clock — a conditional action, which is the worst possible thing to put in permanent
   furniture, because most of the time it is a button that charges you for nothing.
2. **Keep the dock as it is and add one home affordance**, 5-up. Cheapest, preserves every
   certified behaviour, and gives the phone a way out — but it leaves the app's six
   destinations behind a single unlabelled hop, and leaves `Debate` where it is.

**And the clock makes leaving non-neutral.** The draft room is the one view with a timer. If you
navigate away while on the clock, coming back is not the same as never having left, and neither
surface has any concept of this — no badge, no persistent "you are on the clock", nothing. That
is the one piece of this that is a correctness requirement rather than a layout preference.

**This also fixes band 3 of the shape above.** The doors row is the route *in*; what the owner
is pointing at is the missing route *out*. They should be the same pair, so the whole app stays
one hop deep: the front page routes you to the board, the board routes you back to the front
page, and nothing else is ever more than two taps from either.

## Draft continuity and application navigation — a design requirement

The owner elevated the navigation aside into a requirement, with a second opinion attached. The
framing that survives checking, and the part of it I would adopt verbatim:

> The Draft Room must function as a persistent application state, not an isolated page.
> Navigation, contextual commands, supplemental player analysis, and browser-level movement
> must not inadvertently interrupt, reset, or compromise an active draft session.
>
> **The draft takes priority, but the draft must not imprison the user inside the Draft Room.**

**The sharpest line in it is the one about what you are leaving:** *leaving the Draft Room and
leaving the draft are not the same operation.* That is a correctness statement, not a layout
preference, and nothing in the prototypes or the app currently distinguishes them.

### Three layers, which supersede my "views or board tools" question

The dock question above framed this as a binary. Three layers is the better decomposition,
because the thing I was trying to squeeze into one of two buckets is a third kind of thing:

1. **The draft workspace** — selection, board, roster, timer, pick execution. The prototypes
   are this layer and only this layer.
2. **A contextual command layer** — player detail, analysis, navigation shortcuts, supplemental
   actions, reached *without losing the draft's context*.
3. **Persistent application navigation** — Matchup, Roster Maintenance, Draft Room, League,
   with the active draft session preserved across the move.

And the cut that makes the command layer tractable: **informational actions versus actions that
touch the draft.** Opening a player profile cannot cost you a pick; executing a recommendation
can. The UI has to mark which is which, and the current dock does not — three of its four
buttons are reference sheets and the fourth (`Debate`) is billed and live only on the clock,
all four rendered identically.

### What this app already has, and what it is actually missing

This is where the generic version of the requirement and this codebase part company, so it is
worth checking rather than restating. The state machinery exists and is already pointed the
right way:

- `draft_state.py` is a tested module whose whole job is **which session values belong to one
  league and what a league switch must drop.** It sweeps `draft_room_*` and `mock_draft*` by
  prefix, deny-by-default, with a narrow allowlist — written because league A's debate once
  rendered under league B's board with no staleness note.
- It keys on **league**, not on view. So a view change already preserves `draft_room_*` by
  construction, and a league change already drops it. The requirement above and the existing
  discipline are the same line drawn from opposite sides, and they do not conflict.
- `draft_room_position_view` and `draft_room_position_view_open` already round-trip through
  `st.session_state`, so the position drawer's filter and open state survive a rerun today.
- `pending_main_view` already exists as the mechanism for routing between views from inside
  another view's branch, with a comment explaining why `main_view` cannot be set directly.

So of the seven items on the state-preservation list, league/draft identity, round and pick, and
the drawer's filter state are **already handled**. What is genuinely missing is narrower and
more specific than the general requirement suggests:

- **The board's own in-page state beyond the drawer** — scroll position, which door is open,
  which detail panel is expanded. The prototypes hold these in page JS, where a Streamlit rerun
  does not reach. This is the one that needs new work.
- **Browser back and forward.** Tested, found broken, and now fixed on the prototype side.
  **The URL was write-only:** `shared.js` wrote it with `history.replaceState` and there was not
  one `popstate` or `hashchange` listener in the directory, so the address bar was a label the
  page never read back. Measured on `m1_stack` at 390×664:

  ```
  on load                      url #12T_ppr/mid     board 12T ppr round 5    open: none
  after editing the hash       url #HEAVY_IDP/late  board 12T ppr round 5    open: none
  after reload + opening RB    url #HEAVY_IDP/late  board HEAVY IDP round 14 open: RB
  after browser BACK           url #12T_ppr/mid     board HEAVY IDP round 14 open: RB
  ```

  Back does not lose the draft — which is luck, not design. What it does is leave the URL
  describing a board nobody is looking at. **So Back followed by a reload is a board switch the
  user never asked for**, from two of the most ordinary gestures a browser has. `history.state`
  is `null` at every step, so there would be nothing to restore from even if something were
  listening.

  **The prototype half is fixed** (`d806700`): `wireChrome`'s `applyHash` runs the same parse it
  already ran on load, on `popstate` and `hashchange`, so the four surfaces now agree at every
  step and the render gate asserts it. Verified as a listener-only change — 0 of 402 roles across
  the four surfaces changed what they draw on a fresh load.

  **The product half is still open, and it is the interesting half.** `replaceState` is kept on
  purpose: whether a board change should PUSH a history entry is the difference between Back
  stepping through your board states and Back leaving the app, and that belongs with the
  application's routing. The full mechanism the state-preservation requirement reduces to in a
  browser is a real state payload per transition (`{format, state, door, filter, scroll}`)
  restored in `popstate` — which is the same question as returning to a live draft, and needs an
  app around the board to answer.
- **Any on-the-clock indication outside the Draft Room.** There is none. If the clock is the
  reason the draft takes priority, then every other view needs to be able to say so, and the
  route back has to be one tap from wherever you are.

### Where I would push back

A "contextual command layer" is exactly where the busy-ness the owner rejected comes back. The
standing constraint on this project is *"clean dissemination of information over just having as
much on the screen as you can fit"*, and a command palette is the most inviting place in an
interface to park everything that has no other home. The layer earns its place only if it stays
a route to things, not a second screen of things.

And the recommendation's own strongest point argues for restraint rather than for more surface:
if leaving must be safe, then the user does not need everything reachable *from inside* the
draft. Safe exit is what makes a small workspace acceptable.

### The mobile point, measured

The pasted analysis closes on real estate — "a desktop-first draft interface compressed onto a
phone isn't necessarily a usable mobile draft interface." That prompted a check of the render
gate's own viewports, and it was wrong:

```
                        gate was using     real browser viewport (Playwright's device registry)
iPhone 12 / 13 / 14       390 x 844          390 x 664      -180px,  +27% of height assumed
iPhone 13 Pro Max         430 x 932          428 x 746      -186px
Galaxy S24                360 x 800          360 x 780       -20px
```

Those three were **device screens in points** — what a spec sheet says — and a phone browser
never hands a page that height; the tab bar and the toolbar take a fixed bite. So every mobile
verdict taken before this was caught — `screens=1.00`, "the first door lands at y=194", "four
doors on the first screen" — was measured against about a quarter more height than exists.

### What the correction costs, measured

The gate now runs the three binding real viewports, and the whole run comes back with **exactly
two failures out of roughly 530 renders.** Both are `m1_stack`, both are the scroll budget, both
only at 390×664, and both only in the `late` state of the two IDP formats:

```
!! m1_stack.html [HEAVY_IDP/late@390x664]  screens=2.11   (budget 2.0)
!! m1_stack.html [LIGHT_IDP/late@390x664]  screens=2.07
   the same states at 360x780 and 428x746:  1.79, 1.80, 1.76, 1.71  -- all pass
```

Everything else holds: every other format, state, viewport and open/closed combination on all
three phone surfaces, and the whole desktop. The failure is driven purely by the 180px of
height that was being assumed, in the two formats that draw the most doors.

Two corrections were applied, and it matters that **neither is a rescue**:

1. The gate was counting its own review bar — the variant tag and state buttons `wireChrome`
   injects — as 36px of product a user has to scroll past. Excluding it is the measurement
   becoming about the right thing. It moves the two renders to **2.05 and 2.02: still failing.**
2. `.room`'s bottom padding was 68px to clear a 57px dock. 61px clears it just as well. That is
   pure slack and removes no information.

### What is left, and why I did not take it

After both, the certified run reads:

```
verdict PASS_WITH_KNOWN_FAILURES   (certificate: e0061b4, clean tree, 396 renders)

!! [known] m1_stack.html [HEAVY_IDP/late@390x664]  screens=2.04   1357px against a 1328px budget, over by 29
!! [known] m1_stack.html [LIGHT_IDP/late@390x664]  screens=2.01   1333px, over by 5
ok  no other failure in 396 renders, and no stale expectation
ok  url and board agree at every step on all four surfaces (load / hash edit / back / forward)
ok  name size is identical across draft states for all 126 (file, format, viewport) groups
ok  the snapshot is byte-identical to what was certified (7 builds re-hashed)
```

The four navigation failures that first appeared beside these two are **closed** — `d806700` made
the URL readable and the gate asserts it. These two are the only ones left, they are listed as
known so a new failure is still visible against them, and the listing is reconciled in both
directions: if either ever starts passing, the run fails on that instead, because something would
have changed that nobody measured.

So `HEAVY_IDP/late` is over by 29px and `LIGHT_IDP/late` by 5. The remaining levers all change how the variant looks, on the variant the owner chose,
so they are costed here rather than taken:

| lever | saves | what it costs |
|---|---|---|
| `.main` row-gap 8px → 6px | 8px (4 gaps) | doors sit closer; the stack reads slightly denser |
| `.db` padding 13px → 9px | ~20px (5 doors) | every door's body tightens against its header |
| both | ~28px | clears `LIGHT_IDP`, leaves `HEAVY_IDP` within a pixel or two |

And one question that is not a lever but a ruling: **the 2.0 budget was authored when a screen
was assumed to be 844px, and has never been calibrated against 664.** Two screens of travel is
the right invariant — a reader scrolls in screenfuls, not pixels — so the honest reading is that
the design has to be shorter on a shorter screen. But the number itself was set against a
viewport that does not exist, and whether 2.0 is still the right figure at 664px is the owner's
call, not something to quietly adjust after measuring against it.

## Why there is nothing about dynasty on it, and the three reasons are not the same

The sharpest criticism of the built page is that **nothing on it is about dynasty** — no rookie
picks, no taxi squad, no pending trade offers — which makes a Command Center for a dynasty league
read as a redraft page with a bye-week chart. That is fair. But the three missing things are
missing for three different reasons, and only one of them is a gap to fill.

### 1. Rookie pick VALUE is withheld by a ruling, and must stay withheld

The most-wanted dynasty claim is "what are my picks worth". `rookie_draft.estimate_future_pick_value`
computes exactly that, and **it is wired to nothing but its own test** — confirmed by grep: every
reference outside `rookie_draft.py` is in `test_rookie_draft.py`. Its own audit note says why:

> across 400 simulated 12-team seasons the mean absolute slot error is **1.89 of 12** (17% of the
> range) … it placed the worst team within half a slot of 1.01 in **0 of 400 leagues**.

So a card reading "your 2027 1st is worth 29" would be the front page reaching past a documented
withholding to publish a number the engine refuses to publish — the same contract `#187` keeps on
`survival_probability`, which was measured, failed, and withheld everywhere. **This is not a
feature to build. A front page that prices picks is a regression**, and it is the single most
likely way someone later "fills the dynasty gap" and breaks the thing four surfaces protect.

What a page MAY say about picks is the countable part: how many you hold and in which rounds.
That is a fact, not a valuation.

### 2. Which picks you own is syncable TODAY and simply is not shown

`sleeper_client.get_traded_picks` exists and the sync already calls it — `"traded_picks":
self.get_traded_picks(league_id)` is in the league payload. So a live league already knows which
picks moved, which means "you own three 2027 firsts" and "you owe your 2028 second" are available
without one line of new estimation. Nothing in the app surfaces it. Same for the **taxi squad**:
membership comes straight off `roster.get("taxi")` and `app.py` already labels those rows TAXI,
and the front page ignores the one roster concept that only exists in dynasty.

**This is the gap worth building**, and it is cheap. It is also the honest answer to "make it feel
like dynasty": the facts that distinguish dynasty from redraft are pick ownership and the taxi
squad, and both are already in the payload.

### 3. Pending trade OFFERS are not synced at all

The adversarial review's top dynasty want was a pending offer — the one thing with a real deadline
and a rival waiting, and the only candidate that would genuinely satisfy the ladder's top rung.
`get_traded_picks` returns picks that have already moved; there is no offers or transactions call
in `sleeper_client`. So this needs new sync work before any surface can show it, and saying that
is more useful than designing a card for data nobody fetches.

### Why the fixture cannot demonstrate any of it

`data/league_captures/*.json` hold a league's RULES — scoring, roster_positions, format axes —
and carry no taxi, pick or trade keys at all (checked: zero matching keys). A replayed battery has
no traded picks because no picks were traded. So items 2 and 3 are only demonstrable against a
live synced league, which is the same boundary that keeps the record absent.

## Four questions for the owner

1. **Does the claim band cap at three?** Three is my recommendation: a capped list is a ranked
   list, an uncapped one is a feed. The cost is that a genuinely four-problem week hides one.
2. **Is "nothing needs you" an acceptable primary state?** It is the correct answer most days of
   the week. Designing it as the happy path rather than as an empty state is the whole
   difference between a triage surface and a dashboard.
3. **Does the phone dock hold views or board tools?** Recommendation above is views, with the
   board's own tools moving into the board — but option 2 is a third of the work and still
   closes the "no way out" gap, so it is a reasonable first move if the dock's current four are
   earning their place in real use.
4. **Which side's palette moves, and how far?** The display-face question is closed (the system
   already ruled; the app just isn't following its own rule). What is open is twenty-six
   token names carrying two colours, and the recommendation is not symmetric: the app is the
   system of record, so the prototype converges — **except** for the four IDP position pills,
   where the prototype has a capability the app lacks and the app should take them, and
   **except** for `--dim`, where both answers are defended by a measurement and one has to give.
