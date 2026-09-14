# Draft Room UI — the compass

**What this document is.** A vision document for the live Draft Room surface, and the place the
owner's UI rulings persist so they stop living only in chat. It states decisions that are MADE,
decisions that are OPEN and who owns them, and — the part worth the most — the hazards that will
bite during implementation, each tied to something this repository already learned the hard way.

It contains no mockup. The mockups under `mockups/` are the renderings; this is the reasoning
they answer to.

---

## 1. The rulings, as given

These are the owner's, recorded verbatim in effect:

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

**a. The first term has a prerequisite this repo already recorded as open.** `#100` says nothing
meters what a call costs — *"one gap presenting as three."* "Your slowest recorded call" cannot be
computed until a per-function duration history exists. Either `#100` closes first, or the freeze
timer ships with its own narrow duration log. That is a real dependency, not a detail.

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

## 6. The emblem's absence is three-state

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

## 9. The browser plug-in, and why the freeze timer matters MORE there

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
| U1 | Does the rail mark my next turn, making the wait span visible? (§2 argues yes) | owner |
| U2 | Emblem visual vocabulary, and the "never offered" rendering | owner |
| U3 | Freeze timer: close `#100` first, or ship a narrow duration log? | Opus, then owner sign-off |
| U4 | Does the full-board tab replace the rail, or overlay it? | owner |
| U5 | Website vs plug-in — pinned as sequential, website first | **RULED: website first** |

Nothing above changes engine behaviour. Every quantity named here already exists; what is being
decided is which of them a person can see, and what the blanks mean.
