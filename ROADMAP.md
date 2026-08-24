# Shared Knowledge Substrate & Collective Intelligence Roadmap

> **Status: vision document, not an implementation plan.** Nothing in this file describes
> code that exists today, and nothing here should be built as a side effect of reading it.
> It exists so the architectural and business intent behind "The Dynasty Collective" as a
> *name* — not just a feature list — survives across future sessions, model changes, and
> contributors, rather than living only in one conversation's context window.
>
> See `README.md`'s "The Draft Engine" (CDME) and "The Prytaneum" sections for the
> architecture this roadmap extends. Nothing here changes either of those; this is what
> sits *upstream* of both, someday.

## The core idea, in one sentence

**One clean source of truth → many analytical consumers.** The Dynasty Collective should
ultimately operate from a centrally maintained, canonical, versioned, freshness-aware
knowledge substrate — player information, projections, valuations, market data, injuries/
availability, depth/role context, and any other CDME-relevant factual input — rather than
requiring every user's own session to independently assemble and maintain its own copy of
that same world.

```
Canonical Evidence / State
  -> CDME (contextual deterministic synthesis)
    -> Draft Room / Trade Ledger / Roster Management / League / Matchup / other surfaces
      -> optional Prytaneum escalation (discovery / deliberation / interpretation)
        -> user (final decision authority)
```

CDME computes over that state; the Prytaneum interprets and can discover *candidates* for
updating it; the user decides. None of that relationship changes — this roadmap is about
where the state CDME computes over ultimately *comes from*, not about touching CDME's own
math or the Prytaneum's own deliberation contract.

## Current architecture (what actually exists today)

This section exists specifically so a future reader can't mistake the vision above for
already-built infrastructure.

- **Local-first, single-user, no backend.** Per `README.md`'s own "Design Principles"
  section, this is an explicit, stated commitment, not an oversight: "Local data
  sovereignty. Draft Sharks exports never leave your machine or hit a vendor API — you
  export/save them yourself and upload them here." Every install's `data/` directory is its
  own independent world.
- **`DataMerger`** (`data_merger.py`) is the closest thing to a "canonical state" object
  today, but it is reconstructed fresh, per-install, from locally uploaded/committed files
  (Draft Sharks PDFs/CSVs, KeepTradeCut/FantasyPros/ESPN/DynastyProcess exports) plus live
  Sleeper API calls. There is no shared, versioned, cross-install state anywhere.
- **`bot_research.py`** is today's only precedent for "a model discovered something worth
  keeping" — panel-vetted findings from live web search, persisted to a per-install
  `bot_research.json`. This is the conceptual ancestor of the "candidate evidence" idea
  below, but it is entirely private to one local install; nothing propagates it anywhere,
  and (see `test_cdme_ingestion_boundary.py`) it is deliberately excluded from CDME's own
  computation inputs today (see "Relationship to CDME and the Prytaneum" below).
- **No user-contribution flywheel exists.** A finding one user's Prytaneum surfaces has no
  path to benefit any other install today, verified or not.

**The open tension this roadmap does not resolve:** a centrally-hosted shared substrate is
architecturally the *opposite* of "Local data sovereignty... never leave your machine." Any
future implementation of this roadmap has to either revisit that design principle
explicitly (a real product decision, not a quiet default) or scope the shared substrate to
data that was never local-sovereignty-sensitive in the first place (e.g., publicly-sourced
market consensus, not a user's own paid Draft Sharks export). This document intentionally
leaves that unresolved rather than picking a side.

## User API-key philosophy (the business/product intent to preserve)

**Users should not need personal API keys to stay up to date.** The central Collective
backend, if and when it exists, maintains the shared canonical data so a user with no
personal model/API keys still receives the current deterministic intelligence and
analytical product. Personal API/model keys unlock *active generative participation* —
principally, invoking the Prytaneum for discovery, deliberation, and interpretation.

- **No keys → still receives the Collective's maintained intelligence.** The deterministic
  product (CDME's own math, over canonical shared state) does not degrade.
- **Own keys → can actively invoke the generative/intelligence layer** (the Prytaneum) and,
  per the flywheel below, potentially contribute discoveries back to the shared substrate.
- The absence of personal API keys should never make the *core deterministic product* stale
  or structurally crippled. Staleness is a property of the shared substrate's own freshness
  policy, not of whether a given user brought their own keys.

This reframes what a user is actually paying for: **not** a private database copy, and
**not** basic data availability — the product's core value is access to a maintained shared
intelligence substrate, plus optional active reasoning horsepower through the Prytaneum. The
substrate should get collectively better over time; users should not each be rebuilding the
same knowledge independently.

## The collective contribution flywheel (future capability, not built)

When a user with their own keys causes the Prytaneum to discover potentially relevant new
information, that information should not simply remain private to their session forever.
The intended shape:

```
User/model discovery
  -> candidate evidence
    -> verification / corroboration / source evaluation
      -> accepted canonical fact
        -> shared Collective knowledge state
          -> propagates to all users
```

Properly vetted information discovered by one user has the *potential* to improve the
shared substrate for everyone — a collective-intelligence flywheel: users discover, the
Collective verifies, the shared substrate improves, everyone benefits.

## The trust boundary this must never skip (non-negotiable)

**A model assertion must never automatically become shared truth.** This is the same
discipline `test_cdme_ingestion_boundary.py` already enforces for one user's *own* local
session (a bot_research finding cannot reach CDME's inputs without passing through a
structural filter) — this roadmap's job is to preserve that same discipline at the
*collective* scale, where the stakes of a bad acceptance are far higher (one bad fact could
propagate to every user, not just one install).

At minimum, four distinct states must stay distinct — collapsing any two of them is exactly
the failure mode this roadmap exists to prevent:

1. **Discovery** — "a model/user found something worth investigating."
2. **Claim / Evidence** — "this source appears to support a factual statement."
3. **Verified / Corroborated Evidence** — "the evidence has passed the appropriate source/
   verification policy."
4. **Accepted Canonical Fact** — "this information is now trusted enough to alter shared
   state."

Only an Accepted Canonical Fact may alter the shared factual substrate CDME and the rest of
the platform consume. This matters especially because the platform may intentionally seat
models of different capability/cost tiers — a weaker, cheaper model should be usable as a
high-recall *scout* ("look over here") without ever receiving the authority to *declare*
canonical truth. Source independence and source authority matter on their own terms:
multiple models agreeing is not, by itself, suf­ficient corroboration if they're all
downstream of the same single source.

```
Weak model:        "Look over here."               (Discovery)
Verification layer: "Is this actually true?"        (Claim -> Corroborated Evidence)
Canonical state:     "We have accepted this as fact." (Accepted Canonical Fact)
```

The governing principle, worth keeping verbatim: **if you poison the watering hole, it
doesn't matter how good the espresso press is.** CDME, Trade, Roster, League, Matchup, and
the Prytaneum can all be internally correct and deterministic, but if their shared upstream
factual inputs are contaminated, the entire platform becomes consistently, confidently
wrong. Information acceptance / provenance / freshness / verification is therefore a
first-class platform trust boundary, not an implementation detail to backfill later.

**Concrete example of the distinction that must be preserved:** the Prytaneum discovering
"Player X had an injury confirmed yesterday" should become `source -> evidence ->
verification -> accepted state update -> CDME recomputation`, never `model opinion ->
manually alter TAV`. A model's *disagreement* with CDME's read of already-accepted facts
("I think CDME is undervaluing this player") is deliberative and belongs entirely to the
Prytaneum; a model's *factual claim* ("this player's surgery was confirmed yesterday") is a
candidate for the acceptance pipeline above and cannot skip it just because a model stated
it confidently.

## Future workstreams to preserve (not implemented, not scheduled)

Captured as explicit future items so none of them get silently lost, not as a sprint plan:

1. Central canonical knowledge store
2. Evidence/provenance objects
3. Source authority classification
4. Freshness / expiration policy
5. Conflict resolution (independent sources disagreeing)
6. Model-independent acceptance policy (agreement among models is not itself corroboration)
7. Candidate evidence queue
8. Verification workflow
9. Shared propagation of accepted facts to all users
10. Audit trail for every canonical-state mutation
11. Ability to answer "Why does CDME believe this?" with a real, traceable chain
12. Separation of user-private discovery from shared accepted knowledge
13. Contribution/research flywheel where validated discoveries improve the shared substrate
14. Cost-aware model roles — cheaper/weaker models for discovery, stronger models or
    authoritative sources for verification
15. Product-wide freshness indicators sourced from one shared canonical freshness state
    (today's per-install "Values current / Values Nd stale" pattern, generalized)

## What already exists that partially anticipates this

Worth naming explicitly, since it means this roadmap is an extension of existing discipline,
not a break from it:

- **The CDME ingestion trust boundary** (`test_cdme_ingestion_boundary.py`,
  `pick_synthesis._consensus_lookup`, `draft_room._rookie_lookup`) already proves, today, at
  single-install scale, that an LLM-originated finding cannot silently become a CDME input.
  The four-state distinction above (Discovery -> Claim -> Corroborated -> Accepted) is the
  same shape as that boundary, generalized from "one install" to "the whole Collective."
- **`bot_research.py`'s own composite-scoring weight scheme** (`COMPOSITE_SOURCE_WEIGHTS`,
  recency weighting, a minimum trusted pool size before a thin source can move a score much)
  is a real, working precedent for "a low-authority source should matter proportionally
  less" — the same principle item 3/6 above would need to apply at Collective scale.
  Currently: (a) unavailable to CDME, since composite_player_score was deliberately excluded
  from CDME's inputs; and (b) UI-display-only. A future canonical-substrate design should
  reuse this weighting *philosophy*, not necessarily this exact mechanism.
- **The freshness pattern** ("Values current" / "Values Nd stale", `trade_ledger_ui.py`'s
  `freshness_pill`, `DataMerger.is_stale`/`staleness_days`) is already a real, shared,
  restrained UI vocabulary for per-source freshness — item 15 above is this same pattern,
  generalized to one canonical freshness state instead of N per-install ones.
- **The Prytaneum's own escalation contract** (README's "The Prytaneum" section: "It does
  not replace CDME... does not independently re-price players") is already the exact
  discipline this roadmap asks to be preserved at collective scale — a model may interpret
  or challenge, never directly mutate canonical state.

## Open, unresolved questions (deliberately not answered here)

- How does a centrally-hosted shared substrate coexist with the current "Local data
  sovereignty" design principle? (See "Current architecture" above — this is the single
  biggest unresolved tension.)
- Who or what actually performs "verification" for a candidate fact — a human, a stronger
  model, a corroboration-count threshold, an authoritative-source allowlist, some
  combination? Not decided here.
- What happens to a previously-accepted canonical fact that a later, better-verified claim
  contradicts? (Item 5, conflict resolution, is named but not designed.)
- Does a paid-data-vendor's licensing (Draft Sharks, KeepTradeCut, etc.) even permit
  redistributing derived facts across a shared multi-tenant substrate? Not a technical
  question, but a real gating one for any future implementation.
- What's the right unit of "a fact" for versioning/expiration purposes — a single claim
  about a single player, or a broader state snapshot? Not decided here.

---

*Cross-referenced from `README.md`'s "The Draft Engine" section. Do not implement any of the
future-facing sections above without a fresh, explicit product decision — this document
preserves the vision; it is not authorization to build it.*
