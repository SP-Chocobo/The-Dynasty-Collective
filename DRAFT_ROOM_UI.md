# Draft Room UI — the compass

**What this document is.** A vision document for the live Draft Room surface, and the place the
owner's UI rulings persist so they stop living only in chat. It states decisions that are MADE,
decisions that are OPEN and who owns them, and — the part worth the most — the hazards that will
bite during implementation, each tied to something this repository already learned the hard way.

It contains no mockup. The mockups under `mockups/` are the renderings; this is the reasoning
they answer to.

---

## 1. The decisions, as given

**TWO TIERS, and do not confuse them.** The owner's words on the second tier: *"this is just
spitballing, not to be all chiseled into stone as law."*

- **RULED** — stated as a decision, binding until the owner changes it.
- **WORKING** — chosen in a rapid option-picking pass to give the build a direction. Real
  preferences, not law. Revisit freely; a later contradiction is a change of mind, not a defect,
  and nothing here needs a withdrawal ceremony to move.

Everything in §1 below is RULED. The §10 table marks each entry's tier.

Recorded verbatim in effect:

- **Game-like.** Clean and functional, MOBA/LoL draft-selector flavour taken as *flavour*.
- **A rail across the top**, panning as players are taken, carrying the next on the clock. It
  **dims beneath the side UI** so only the upcoming few and the last few read. A **tab** opens
  the full rosters / draft board.
- **Rail boxes carry the drafting user's name**, so who is up is never ambiguous. **Your own
  picks glow.**
- **A re-center button** snaps the rail back to the current pick after the user has scrolled it.
- **Cards** carry name, team, position, projected stats and the draft context, with a **context
  ledger to the side**. **Click a card to zoom it and open the context window.**
- **Debate/Insight results attach to the drafted player as an emblem**, readable later from the
  rail or the full board.
- **No automatic API pings, ever.** Calling out is an explicit user decision.
- **The draft must function fully with no API at all** — that is a supported configuration, not
  a degraded one.
- **Debate is callable only while on the clock.**
- **A user-set freeze timer** warns before a late call. Recommendation ≈ the slowest recorded
  call for that function plus 10–15s. Manually editable, and disable-able.
- **There is no third emblem state for "someone else took him."** Ruled by the owner: a call is
  only reachable on the clock and its verdict is a snapshot valid in the context of who you
  *did* take, so attaching one to a player you passed on is a category error.

---

## 2. The rail is not chrome — it is `intervening_picks` drawn

The single most useful thing noticed while thinking about the rail: the engine already computes
the quantity the rail is a picture of.

`survival_probability`, `opportunity_cost`, `expected_value_of_waiting`, `positional_forfeit` and
`rival_premium` are every one of them integrated over **the picks between this turn and my next
one**. The engine-measurement skill states the rule in its own words: *the gap that matters is
the one AHEAD*. That gap is `intervening_picks`, it is already on the snapshot, and it is already
shown as a bare number.

The rail is that number made visible. If the rail marks MY NEXT TURN as well as the current pick,
the user is looking directly at the span every waiting-cost number on the card is about — the
sixteen boxes between "me now" and "me next" ARE the sixteen picks `survival_probability` is
integrating over.

Two consequences worth taking seriously:

**The window has a derived definition, not a chosen one.** "The last few and the next few" sounds
like it needs a constant — show 4 behind, 6 ahead. It does not. The principled window is *at
minimum, my previous turn through my next turn*, which comes straight out of `pick_order` and
varies correctly with snake, linear and 3RR without anyone tuning it. Anything beyond that span
is padding for visual balance and can be whatever fits. This matters because a hand-picked "show
6" is exactly the kind of number `#56` exists to stop, and here there is a real one available.

**The rail earns its space or it does not get any.** A rail that is only a list of names is
chrome competing with the cards for the fold. A rail that shows the user the shape of their own
wait is load-bearing. Design it as the latter.

---

## 3. Scale is the thing the MOBA reference does not carry

League of Legends' draft has **ten** slots, total, forever. A dynasty startup in the arms this
repository actually drafts has **312**. Take LoL's clarity, its two-stage commitment and the
weight of its lock-in moment; do NOT take its spacing, because its density is near zero and ours
is a hundred-plus rows. Copying its generosity with space would spend the entire fold on six
boxes.

The owner's own answer is the right one and it is a windowing answer: the rail shows a moving
window over a long sequence, the dimming marks the window's edges, the re-center button returns
the anchor after the user has panned away, and the full sequence lives behind the tab.

---

## 4. Two-stage commitment, and the one architectural rule that follows

LoL separates *hovering* a champion from *locking* it. In a draft where a misclick spends a real
player, that separation is protective rather than decorative, and the owner has already asked for
its first half: **click a card to zoom it and open the context window.**

That is stage one. Stage two is an explicit confirm that actually spends the pick.

This maps onto the answer to the question that started the whole UI thread — *does what we want
outscope Streamlit?*

**It does not, and here is the line that keeps it that way.** The visuals were never the problem:
panning, zooming, dimming, hovering and re-centering are CSS and JS inside a component this
repository already ships (`st.components.v1.html`, the Draft Room port). What costs is **state
round-trips** — every interaction that must tell Python something is a rerun, and reruns are what
would make this feel like a form instead of a game.

So the rule:

> **Presentation-only interaction never round-trips.** Pan, zoom, dim, hover, re-center, open and
> close the context window, switch to the full-board tab — all of it lives inside the component
> and touches no Python. **Exactly two things round-trip: making a pick, and calling
> Debate/Insight.**

That is checkable, it is the difference between "game-like" and "web form," and it means the
answer to *outscopes Streamlit?* is **no** — provided nothing quietly adds a third round-trip.
Stage one of the two-stage commit is free under this rule; stage two is one of the two.

---

## 5. The freeze timer is two terms with different epistemic status, and one of them is missing

The owner's ruling is right about ownership: the user sets the timer, the app recommends. But the
recommendation has structure worth being honest about, because it is a **sum of one measured
quantity and one unmeasurable one**:

| term | what it is | status |
|---|---|---|
| model/tool latency | how long the Debate or Insight call itself takes | **measurable — but not measured today** |
| human action budget | noticing the verdict, switching to Sleeper, finding the player, clicking | **not measurable by us at all** |

The owner named both: *"different models or internet speeds can vary how fast the results can
come"* and *"the time for them to switch over to sleeper or whatever site and actually find and
click on the player."*

**Three things follow.**

**a. CORRECTED — the first term is ALREADY MEASURED, and I said otherwise.** This section
originally claimed the measured half was blocked behind `#100` and needed a new duration log. The
owner said *"wasn't this already going to be tracked via optimization of the models for the
chairs? dig into this, this may already be solved."* It is, and they were right:

`provider_meter.py` records **`latency_ms` on every real provider call**, taken with
`perf_counter` around the invocation, written on the success path AND the failure path, and
wired into `pick_debate.py`'s actual call sites through `metered()`. It is scoped **per provider
and per ROLE** — the chairs — which is exactly the shape the owner remembered. Absence is `None`,
never `0`, by the same rule the board applies to an unpriced row.

So no new logging is needed. What the freeze timer still needs is smaller, and it is three
specific things rather than one big one:

| gap | what exists today | what the timer needs |
|---|---|---|
| **durability** | a 500-entry in-memory ring buffer, gone on restart | survive a session, or the recommendation resets to "no recordings" every launch. `recent()`'s own docstring already anticipates *"a stored run record"* — the hook is there, the store is not |
| **the statistic** | `totals()` reports latency as a **SUM** | a **max** (or a percentile). Total time spent across calls is the wrong statistic for "how long does one call take" — this one is a real trap, because the field is present and named plausibly |
| **end-to-end vs per-call** | per-call records, per chair | the user waits on a WHOLE DEBATE, not one chair's call. Derivable today: `mark()` before and `since()` after bracket the entire multi-chair run |

`#100`'s cost/token/limit half stays open and is untouched by this. The duration half was never
part of the blockage.

**a-bis. AN UNSETTLED DETAIL IN THE OWNER'S OWN TWO STATEMENTS.** Earlier: *"10 or 15 seconds
longer than your slowest recorded call."* Later: *"based on the avg call time + X time."*
**Slowest and average are different recommendations** and will differ by a lot on a
heavy-tailed latency distribution. Not resolved here; flagged so whichever is chosen is chosen
deliberately. (A defensible third answer exists — a high percentile — but nothing has measured
the spread yet, so proposing one now would be inventing a constant, which `#56` forbids.)

**b. The two terms should not be blended into one number in the UI.** Showing a single
recommended value hides that half of it is measured from this user's own calls and half is a
default standing in for something nobody can measure. Show them separately — *"your slowest
recorded Debate: 41s · action budget: 15s · recommended lock: 56s"* — and the user can argue with
the half that deserves arguing with. This is the same discipline `#187` and `#203` applied to
`denial_value` and `risk_adj`: a number and its basis travel together.

**c. The "+15s" is NOT an engine constant, and a future audit should not flag it as one.**
`#56` governs constants that reach valuation — a bound is not a threshold, and nothing that
decides may be hand-picked. This number decides nothing in the engine. It is a **default in a
user-editable preference**, disable-able by ruling, and it stands in for a quantity that is
unmeasurable in principle rather than merely unmeasured. Stating that here so nobody has to
re-litigate it later.

**d. Absence, in the recommendation itself.** A user with no recorded calls — brand new, or
running with no API — has no slowest call. That is three states, not one: *no recordings yet* /
*recordings exist* / *user has overridden*. A recommendation that renders `0s` for the first case
would be the exact defect this codebase keeps finding. It should decline to recommend and say why.

---

## 6. The emblem — WORKING direction, and it is richer than three states

**Where it lives (working).** A star/emblem sits on the **rail box** and on that player **in your
roster**. Clicking either expands the debate or insight; it collapses with a close button or a
click outside. The verdict travels with the player to both places a person looks for him.

**What the marks are (working).** Not one "has a verdict" glyph — the two call types are
*different questions* and read differently:

| state | mark |
|---|---|
| insight call | one symbol (eye? star? — glyph choice open) |
| full debate | a different symbol (scales?) |
| call failed for a real reason | a symbol, so a genuine failure is visible |
| **no API call on that pick** | **blank** |
| **denied — refused by settings, no result worth showing** | **blank, same as no call** |

**The sharp edge of this one, and why it holds up.** A denial that produced nothing renders
*identically* to never having called. That looks like it violates the absence contract and does
not: the contract forbids presenting an unmeasured thing as a measured zero. It does not demand
that every reason-for-absence get its own board glyph. A denial the user themselves configured
is not a fact about the player, so it does not belong on the player.

**Where the denial DOES get said (working).** In a clean message on the call itself — *per
settings* — not on the board. The message links to the settings so a vexed user can edit the
rule that just denied them. The owner's own note on why this stays calm: the user sets the
delay/lock timer themselves, or accepts one derived from call time, so a denial is their own
rule firing, not the app refusing them.

**Still open (U2a):** the actual glyphs. Eye vs star for insight, scales for debate, and what a
failure looks like without reading as alarm.

## 6b. The original three-state framing, kept for the reasoning

The emblem attaches a Debate/Insight verdict to a drafted player. The interesting question is not
the emblem; it is what **no emblem** means, and today it would mean three different things at once:

1. **Never offered** — this user has no API configured. A fully supported configuration, by
   ruling. Every player will lack an emblem forever and that is correct.
2. **Offered and declined** — the user was on the clock, could have called, chose not to.
3. **Called and failed** — the call went out and did not come back usable.

One blank state for all three is the `#187` / `#174` / `#203` defect class in a new surface, and
it is worse here than usual because state 1 is the *normal* state for a whole customer segment.
Whatever the emblem's visual vocabulary is, the no-emblem case needs at least the "never offered"
/ "nothing recorded here" split before this ships.

The owner has already closed the fourth state: no emblem for a player someone else took, because
a call is only reachable on the clock.

---

## 7. Headshots: design the fallback first

Settled by the owner's own test: the Sleeper headshots are real photos, and `thumb` falls back to
the full image when no thumbnail exists — the identical byte counts were not a placeholder, they
were the same file served twice. My contrary reading of that was withdrawn.

Two implementation facts that follow, both easy to get wrong:

**Published artifacts cannot load them.** The artifact CSP admits no external images, so
sleepercdn is blocked in every mockup published for review — while the real Streamlit app loads
them fine. A design that only looks right *with* photos will therefore look broken in every
single design review it ever gets, and look fine in production. Design the initials/silhouette
fallback as the primary state and treat the photo as enhancement, or every review will be
arguing about the wrong thing.

**Plenty of real players have no photo at all** — deep rookies, practice-squad bodies, and the
IDP tail. Same three states as everything else here: *never had one* / *failed to load* / *not
yet loaded*.

---

## 8. Two clocks on one screen

A hazard that only appears once the rail and the freeze timer are both real: **there are two
countdowns, and they mean different things.**

- The **league clock** — how long until this pick times out. External truth, owned by Sleeper.
- The **call lock** — our own derived moment after which starting a Debate is wasting money.

They tick in the same units, they are both urgent, and if they look alike the user will read the
wrong one at the worst time. They need different visual vocabularies and different names, and
the lock should probably be expressed against the league clock (*"lock in 12s"*) rather than as a
second independent countdown.

---

## 8b. WE CANNOT PUSH A PICK INTO SLEEPER, and that moves the terminal action

Raised by the owner while ruling on the lock gesture — *"only really usable in mock, since
there's no push from our end into the sleeper api to select in the real draft (i think)."*
**Verified rather than assumed: there is not one `POST` or `PUT` anywhere in this codebase, and
every Sleeper call is a `/v1/` GET.** The hedge was correct.

Three consequences, and the third is a correction to this document.

**Stage two of the two-stage commit (§4) only spends a pick in MOCK DRAFT.** In a live draft
synced from Sleeper, our surface cannot draft anybody. Its terminal action is *"I have decided"*,
not *"he is mine"* — and the pick is then made by a person, in Sleeper.

**So the two modes need different terminal vocabulary.** A "Draft him" control that works in mock
and silently means something weaker in a live draft is the kind of same-word-two-meanings defect
this repository keeps finding in its own quantities (`#187`, `#174`). Mock locks a pick; live
marks a decision and starts the clock on the user going elsewhere to execute it.

**CORRECTION to §9.** That section said the freeze timer *"is least necessary in the surface it
was conceived for and most necessary in the one pinned for later,"* on the reasoning that only
the plug-in forces the user across an application boundary to act. **That is wrong, and this is
why:** if no surface of ours can push a pick, then the user crosses an application boundary in
*every* configuration, website included. The freeze timer is therefore load-bearing in the
website too, on exactly the same grounds. What remains true from §9 is narrower and still worth
keeping: the plug-in is read-only advice by construction, so it never has a stage two at all.

---

## 9. The browser plug-in, and its one structural constraint

Pinned by the owner as the next UI/UX step after the website: a DraftSharks-style overlay that
detects a Sleeper draft board and opens a collapsible sidebar of recommendations over it.

One structural note worth recording now, because it changes the design: **the plug-in cannot make
the pick.** Sleeper owns that interaction. The overlay is strictly read-only advice.

That simplifies it — no two-stage commit, no pick round-trip, one of §4's two round-trips gone.
But it *sharpens* §5: in the website the user acts where they are reading, while in the plug-in
the human must cross an application boundary to act on what they just read. **The freeze timer is
least necessary in the surface it was conceived for and most necessary in the one pinned for
later.** Worth knowing before either is built.

---

## 10. Open, and who owns each

| # | question | owner |
|---|---|---|
| U1 | Does the rail mark my next turn, making the wait span visible? | **RULED: yes** — built, `mockups/draft_rail.html` |
| U2 | Emblem visual vocabulary, and the "never offered" rendering | owner |
| U3 | Freeze timer: close `#100` first, or ship a narrow duration log? | Opus, then owner sign-off |
| U4 | Does the full-board tab replace the rail, or overlay it? | **WORKING: overlay, the rail stays pinned** |
| U5 | Website vs plug-in — pinned as sequential | **RULED: website first** |
| U6 | Rail compression at 27 boxes | **WORKING: no shrink.** Every box stays full size; explicit ◀ ▶ pan controls move **5 picks per click, or jump to your last / next pick**. Legibility is not traded for fit. |
| U7 | Card zoom target | **WORKING: side-panel takeover** — the card expands into the context ledger that is already there. No new surface invented. |
| U8 | The gesture that spends the pick | **WORKING: hold to lock**, with a small rising bar showing how much hold remains. See §8b: this is a real pick only in Mock Draft. |

| U9 | Latency persistence shape | **WORKING: rolling summary per function** — count/max/mean, not the raw ledger. One home, ~200 bytes, exactly what the recommendation reads. |
| U10 | Slowest vs average for the recommendation | **WORKING: show both, user picks.** Settles the §5 a-bis contradiction by not settling it — the spread is visible and the user chooses. |
| U11 | Does the wait band carry the forfeit? | **WORKING: no.** The band states pick-order facts anyone can verify from the board; an engine projection alongside them would blend a certainty with an estimate. Forfeit stays on the cards. |
| U12 | "Since your last pick" digest | **WORKING: no** — the rail already shows it when you scroll back. A second surface for the same information is duplication. |

### On U6, because it settles something §2 left open

The owner's ruling adds what the derived window could not supply on its own: the window says how
WIDE the span is, but a 27-box span still needs a way to travel. Two pan steps, both derived
rather than chosen — **five picks** (a readable stride) and **jump to my last / next pick** (the
window's own two endpoints, which are exactly what §2 says the rail is about). The re-center
button remains the third: back to the current pick.

Nothing above changes engine behaviour. Every quantity named here already exists; what is being
decided is which of them a person can see, and what the blanks mean.
