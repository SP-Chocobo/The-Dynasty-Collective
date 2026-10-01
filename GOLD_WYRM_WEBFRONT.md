# Gold Wyrm webfront — performance and architecture, for contemplation

> **WHERE CURRENT STATE LIVES — not in this file.** This document is long-lived and does
> not track the live path. `FREEZE_CHECKLIST.md`'s top block carries the current state and
> what is outstanding; `POST_AUDIT_PLAN.md` is the numbered record and wins over any status
> flag anywhere, including the session task list (`#292`). A pointer rather than a copied
> status, deliberately: a copy goes stale silently, a pointer cannot (`#126`).

> **STATUS: FOR CONTEMPLATION. NOT AN IMPLEMENTATION MANDATE.** The owner's own framing, kept
> verbatim from the source. Nothing here is a commitment to a framework, deployment model,
> caching technology or rendering strategy, and no repair or register item derives from it. It
> belongs to the Gold Wyrm UI phase — `POST_AUDIT_PLAN.md` Step 6 and open question **D7** —
> not to the engine work in flight.

**Provenance.** Written by the project owner after watching a video on why McMaster-Carr's site is
fast, then translated from those observations into modern principles. Converted verbatim from
`Gold_Wyrm_Webfront_Performance_For_Contemplation.docx`; the headings, bullets and priority labels
are the owner's. Nothing was added to the body, and nothing was removed from it.

**Where it sits beside the other UI documents.** `DRAFT_ROOM_UI.md` is the compass for the live
Draft Room surface and the place the owner's UI *rulings* persist. This file is upstream of that
and wider: it is about how the webfront should be *built and measured*, not what it should show.
Where the two touch — the draft board's layout stability, the Debate chip's cost, what a player
card must prove about the snapshot behind it — `DRAFT_ROOM_UI.md` owns the surface decision and
this file owns the delivery principle.

---
GOLD WYRM

Webfront Performance & Architecture — For Contemplation

Modernizing lessons observed from McMaster-Carr for the Gold Wyrm application

Working design notes • Not an implementation mandate


## Purpose

This document captures a performance-focused reference the project owner encountered while watching a video explaining why the McMaster-Carr website is fast, then translates those observations into modern principles for contemplation during Gold Wyrm webfront/UI design.

The intent is not to reproduce McMaster-Carr's historical technology stack. The intent is to preserve the underlying engineering ideas—early useful rendering, selective delivery, aggressive but correct caching, predictable layout, stateful navigation, and measurement—using modern browser and application architecture.


## Reference: McMaster-Carr observations

- Server-rendering HTML
- Pre-fetching HTML / DNS (for images)
- Push State
- Aggressive caching
- CDN to store pre-rendered content
- Squid-cache.org
- Service worker for HTML
- Link pre-load for web fonts
- CSS before <head> / critical CSS
- Fixed width/height for images based on screen parameters
- Sprite images / splitting image resources
- Only load the JavaScript needed for that page
- Dependency injection
- window.performance and performance.mark
- YUI and jQuery
Interpretation note: several of these are historical implementation techniques. Their continued value lies in the underlying principle, not necessarily the original technology. YUI, jQuery, Squid-specific architecture, bitmap sprites, and other legacy mechanisms should not be adopted simply for historical fidelity.


## Gold Wyrm context

Gold Wyrm is not a conventional content site. The webfront will sit over a deterministic CDME engine and expose draft state, player information, rosters, frozen snapshots, Insight functionality, and potentially Full Debate or other gated AI capabilities.

- The CDME should remain authoritative.
- The UI should primarily present and interact with authoritative engine state.
- Frozen/versioned snapshots are fundamentally different from live draft state.
- AI functionality is optional/gated and should not impose unnecessary client cost on users who are not using it.
- Performance work must not create a second, silently divergent source of truth.
- The frontend should be measurable in the same spirit as the engine: deterministic where appropriate, traceable, versioned, and auditable.

## Modernized recommendations for contemplation


### 1. Server-render useful initial HTML — HIGH PRIORITY

The first response should contain meaningful application content whenever practical. Do not make the browser wait for a large JavaScript bundle merely to construct the application shell. JavaScript should enhance/hydrate the experience rather than being the sole source of visible content.

Gold Wyrm implication: Potential targets: draft board, current pick, roster, player card, CDME snapshot metadata, league configuration, and other immediately knowable state.


### 2. Establish an explicit caching model — VERY HIGH PRIORITY

Separate immutable/versioned assets and snapshots from live state. Static hashed JS/CSS, fonts, icons, and immutable/versioned CDME artifacts can have long cache lifetimes. Live draft state, user-specific state, and rapidly changing values need different semantics.

Gold Wyrm implication: This is especially compatible with Gold Wyrm's frozen-snapshot philosophy. A snapshot/version identifier can make provenance and cache behavior explicit.


### 3. Design static delivery for a CDN — HIGH PRIORITY

Make JS, CSS, fonts, icons, images, and other immutable/versioned resources CDN-friendly. Do not assume every application response should be cached at the edge. Keep authoritative live state on the application side where appropriate.

Gold Wyrm implication: Conceptually: browser → CDN for static/versioned resources; browser → application for live draft state and dynamic operations.


### 4. Code-split by capability — VERY HIGH PRIORITY

Do not ship the entire Gold Wyrm client to every route. Separate the application shell from draft-room functionality, player cards, CDME dashboards, Insight, Full Debate, and commissioner/admin tools.

Gold Wyrm implication: AI-related capabilities are especially important here. A user who never opens Insight or Debate should not pay the JavaScript initialization/download cost for those systems.


### 5. Selective preloading and prefetching — HIGH VALUE

Use high-confidence predictions about the next user action. A draft room can anticipate player-card resources; a player card can anticipate Insight resources. Avoid indiscriminate preloading.

Gold Wyrm implication: The goal is to move likely future work earlier without turning speculation into unnecessary bandwidth and memory consumption.


### 6. Critical CSS and layout stability — HIGH VALUE

Provide enough CSS for the initial viewport to render immediately where useful. Reserve dimensions for images and asynchronous content so late-loading assets do not repeatedly reflow the interface.

Gold Wyrm implication: This matters for a dense draft dashboard where small layout shifts can make the interface feel substantially less stable.


### 7. Preserve meaningful URL/history state — HIGH VALUE

Use modern History API/routing techniques so meaningful application state is addressable and browser Back/Forward works naturally.

Gold Wyrm implication: Potential conceptual routes: /draft/{draft_id}, /draft/{draft_id}/player/{player_id}, /draft/{draft_id}/insight/{player_id}. The exact routing scheme should be determined during UI architecture.


### 8. Consider service-worker caching carefully — MEDIUM / LATER

A service worker could eventually cache the application shell and immutable resources for extremely fast repeat visits. Do not introduce this complexity until the cache invalidation/versioning model is mature.

Gold Wyrm implication: The main risk is stale application code interacting with fresh authoritative state. Versioning and invalidation need to be explicit first.


### 9. Fonts: preload only what matters — MEDIUM

If Gold Wyrm uses a distinctive typeface, preload only the font resources needed for first paint. Avoid downloading multiple weights/styles merely because they exist.

Gold Wyrm implication: A system-font fallback can be preferable to delaying useful rendering.


### 10. Images and sprites: modernize the principle — MEDIUM

Reserve known dimensions for images. Prefer modern SVG/icon techniques and optimized assets rather than reproducing legacy bitmap sprite-sheet architecture.

Gold Wyrm implication: The lasting principle is minimizing asset overhead and avoiding layout instability, not preserving the old mechanism.


### 11. Keep client dependencies deliberate — HIGH PRIORITY

Do not reproduce YUI, jQuery, or other historical dependencies unless there is an explicit modern reason. Prefer native browser APIs and focused libraries where they materially simplify the application.

Gold Wyrm implication: Every substantial frontend dependency should have a reason to exist. Avoid shipping an entire framework's machinery to accomplish a small task.


### 12. Instrument the frontend from the beginning — VERY HIGH PRIORITY

Use the Performance API and performance.mark/performance.measure to establish measurable boundaries through the application lifecycle.

Gold Wyrm implication: Useful events include HTML arrival, application-shell render, draft snapshot fetch, draft-board render, player-card render, Insight request/response/render, and interactive readiness.


## Suggested performance model

Treat frontend performance as a pipeline that can be decomposed rather than as a single page-load number:

- Network cost — how much was transferred and how quickly?
- Server cost — how long did authoritative state take to produce?
- Client boot cost — how much JavaScript was downloaded, parsed, and initialized?
- Render cost — how long did the UI take to become visually useful?
- Interaction cost — how long did a user action take to produce a stable result?
- AI/computation cost — where applicable, how much latency comes from Insight/Debate or other expensive operations?
Conceptual instrumentation:

performance.mark("draft.snapshot.fetch.start");...performance.mark("draft.snapshot.fetch.complete");performance.measure(  "draft.snapshot.fetch",  "draft.snapshot.fetch.start",  "draft.snapshot.fetch.complete");


## Potential Gold Wyrm performance boundaries

Boundary

What to measure

Why it matters

Initial HTML

request → useful HTML

Separates server/network delay from client boot.

Application shell

HTML → stable shell

Measures first useful visual state.

Draft snapshot

request → authoritative snapshot

Measures core application-state delivery.

Draft board

snapshot → rendered board

Measures client transformation/render cost.

Player card

selection → stable card

Measures high-frequency interaction latency.

Insight

request → result → rendered result

Separates AI/backend latency from UI latency.

Interactive readiness

navigation → meaningful interaction

Provides a practical user-facing metric.


## What NOT to cargo-cult

- Do not adopt YUI or jQuery simply because McMaster used them.
- Do not build a Squid-specific caching architecture unless a concrete infrastructure requirement emerges.
- Do not create bitmap sprite sheets merely to reduce HTTP requests.
- Do not add a service worker before cache/version semantics are understood.
- Do not prefetch everything 'just in case.'
- Do not SSR every possible view if a simpler architecture gives the same measured result.
- Do not optimize before identifying an actual bottleneck.
- Do not let client-side caches become an alternate source of truth for CDME state.

## Design principle to carry forward

Make Gold Wyrm feel instantaneous without sacrificing architectural clarity, correctness, or maintainability.

The McMaster-Carr reference is valuable because it demonstrates a coherent philosophy: deliver useful information early, avoid unnecessary work, cache what is truly immutable, predict likely next actions, keep the browser's layout stable, load only what is needed, and measure the actual experience.

For Gold Wyrm, the modernized version of that philosophy should be anchored to the CDME's existing discipline: deterministic authoritative state, explicit versioning, narrow-scope operations, auditable behavior, and evidence-driven optimization.


## Questions for the UI architecture phase

1. What is the smallest useful HTML/state payload for each major route?
1. Which data is immutable, versioned, slowly changing, live, user-specific, or AI-generated?
1. Which resources can safely be cached for hours, days, or effectively forever?
1. What are the highest-confidence next actions from each major screen?
1. Which capabilities deserve independent JavaScript bundles?
1. Which views benefit materially from server rendering?
1. What should be represented in the URL/history?
1. What is the cache invalidation/versioning strategy before a service worker is considered?
1. What performance marks will become part of normal development and regression testing?
1. How will the UI prove which CDME snapshot/version produced a displayed value?
1. Where does client state end and authoritative CDME state begin?
1. What performance budget is appropriate for initial render, interaction, and capability-specific operations?

## Status

FOR CONTEMPLATION. These notes are intended to inform the eventual Gold Wyrm webfront/UI architecture. They are not a commitment to a specific framework, deployment model, caching technology, or rendering strategy.

---

## Reading notes added on ingestion, kept separate from the owner's text

These are mine, not the owner's, and they are recorded here rather than in the body so the source
stays clean. Three of the twelve recommendations restate something this engine has already been bitten
by, which is the main reason this document is worth keeping rather than filing:

**Recommendation 2 (caching) and question 10 (which snapshot produced a displayed value) are the same
problem the freeze exists to solve.** The engine's answer is already built: a snapshot carries its
own provenance, and `#187`'s absence contract says an unpriced quantity crosses as `None` and never
as `0.0`. A client cache that serves a value without the version that produced it would break that
contract on the far side of the boundary, where no test in this repository can see it. The v2 audit
found exactly this shape twice — `season_projection_coverage` recorded and read by nobody (`2.1`),
and `get_players` caching an error-shaped body for 24 hours (`2.4`).

**Recommendation 12 (instrument from the beginning) is the lesson this repository paid the most for.**
The suggested marks are the right ones. The hazard is not missing instrumentation, it is
instrumentation that reports a number about something else: `0.1` had an acceptance battery certifying
a board the shipped engine does not build; `0.3` had a render trace recording every view in its empty
state while reporting five views and 619 calls; `0.2` had a mutation harness whose "caught" verdicts
were its own self-test failing. A frontend mark is worth having only if something fails when it stops
measuring what its name says. Whatever `performance.mark` names get chosen, they need the equivalent
of a ratchet and a non-vacuity check, or they will read green over a blank screen.

**"Do not let client-side caches become an alternate source of truth for CDME state" is `#126`.** One
concept, one home. The v2 audit's whole Tier 4 is the cost of that rule being broken inside a single
process — two spellings of a flex slot, three team-count readers, three injury vocabularies that
already disagree on screen. A browser cache is a second home with a network in between.

**One thing the document does not yet ask, and should.** Every boundary in the table measures
*latency*. None measures *correctness of what was displayed* — whether the board the user saw is the
board the engine produced. That is the question `0.3` turned out to be about: the instrument was fast,
complete, and blind. A frontend equivalent would be a recorded render trace of the real board, not
just a timing mark around it.

**No production change follows from this file.** It is filed, indexed, and pointed at from the UI
phase. If any of it hardens into a decision, that belongs in `DRAFT_ROOM_UI.md` or a numbered
register item, not here.
