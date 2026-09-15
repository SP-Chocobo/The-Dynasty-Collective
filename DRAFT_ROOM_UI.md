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
- **No automatic PAID API calls, ever.** Calling out to a billed provider is an explicit user
  decision. *(Qualified by the owner this session: the constraint is about **cost**, not about
  network traffic. Free reads — Sleeper — are not covered and may happen on their own. This
  closes U13.)*
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

**BOUNDED, after FFCL Group A was captured.** Part of the argument above — that a person cannot
know when their next pick is without being told — rests on the gap being irregular, and it is
irregular *because picks move*. FFCL Group A forbids trading outright (fairness across its six
pods), so its gap is just the snake's arithmetic and a drafter could count it on their fingers.
The next-turn marker is still useful there; the NECESSITY argument holds only where picks can be
traded. Stated so the claim is not carried further than the evidence for it.

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
synced from Sleeper, our surface cannot draft anybody.

**AND THE LIVE SURFACE GETS NO TERMINAL ACTION AT ALL (owner, this session).** My first answer
here was that live-mode's terminal action becomes *"I have decided"* — a state the app records
before the user goes off to execute it. The owner cut that: *"honestly i dont even think the 'I've
decided' functionality is worth incorporating. just go to sleeper or wherever, make the pick, and
it updates with your pick in place. refresh button."*

That is the better answer and it removes a whole concept rather than renaming one. A decided-but-
not-yet-made state is a **fourth source of truth about who owns a player** — beside Sleeper, our
board, and the roster — and it can go stale the instant the user changes their mind in the other
tab. The app never has to reconcile a state it never records. **Sleeper stays the only authority
on what happened; we read it back.**

### What this collapses

**The two-stage commit is Mock-only, entirely.** Hold-to-lock (U8) is a Mock Draft affordance. In
a live draft there is no stage two, so there is no gesture to design and no misclick to protect
against — the card's click still opens the ledger (U7), and that is the end of our interaction.

**The round-trip rule (§4) splits by mode**, and the live side is smaller than what I wrote there:

| mode | what round-trips |
|---|---|
| **Mock Draft** | making a pick · calling Debate/Insight |
| **Live (Sleeper-synced)** | calling Debate/Insight · **refreshing the board** |

**The advisory surface has no button at its end.** If we never make the pick, the card's job ends
at *being read and carried to another application*. That is a real design consequence worth
stating before anyone builds the card: the last thing the user does with our recommendation is
take a NAME somewhere else and find it in a list. Legibility of the name, and getting it out of
our app cleanly, matter more than any action affordance we could put on the card.

**And it sharpens §9's case for the plug-in.** The website has a two-screen problem by
construction — read here, act there. The plug-in does not: it draws on top of the page where the
act happens. That is no longer just a convenience argument; it is the only configuration where
reading and acting are the same screen.

### U13, RAISED AND CLOSED IN ONE EXCHANGE

I flagged that §1's *"no automatic API pings, ever"* had been said about **paid** LLM calls, and
should not be read as having settled — by accident of wording — whether the live board may poll
Sleeper, whose reads are free. The owner qualified it immediately: **"no *paid* api calls
automatic."**

So the constraint is about **cost, not network traffic**, and the live board may update itself.
That is the better rule, because the thing being protected was never the request — it was the
user's money and the choice to spend it.

**And it matters more than a settings detail.** A board that only moves when someone presses a
button cannot feel live, and "game-like" (§1) is not reachable without motion that the user did
not have to ask for. The rail advancing on its own as picks land IS the game feel; the refresh
button becomes an immediate-update override for the impatient, not the only mechanism. Under the
literal reading I flagged, the whole surface would have been stuck waiting to be poked.

Poll cadence is left as a practical default rather than pinned here — it is a UX comfort choice,
not an engine constant, so `#56` does not reach it.

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
| U4 | Does the full-board tab replace the rail, or overlay it? | **SUPERSEDED by §15 — neither; there is no tab.** A button under the clock bar expands the board over the centre, and the left sidebar has its own pullout for rosters. Prior answer kept: *overlay, the rail stays pinned.* |
| U5 | Website vs plug-in — pinned as sequential | **RULED: website first** |
| U6 | Rail compression at 27 boxes | **WORKING: no shrink.** Every box stays full size; explicit ◀ ▶ pan controls move **5 picks per click, or jump to your last / next pick**. Legibility is not traded for fit. |
| U7 | Card zoom target | **WORKING: side-panel takeover** — the card expands into the context ledger that is already there. No new surface invented. |
| U8 | The gesture that spends the pick | **WORKING: hold to lock**, with a small rising bar showing how much hold remains. See §8b: this is a real pick only in Mock Draft. |

| U9 | Latency persistence shape | **WORKING: rolling summary per function** — count/max/mean, not the raw ledger. One home, ~200 bytes, exactly what the recommendation reads. |
| U10 | Slowest vs average for the recommendation | **WORKING: show both, user picks.** Settles the §5 a-bis contradiction by not settling it — the spread is visible and the user chooses. |
| U11 | Does the wait band carry the forfeit? | **WORKING: no.** The band states pick-order facts anyone can verify from the board; an engine projection alongside them would blend a certainty with an estimate. Forfeit stays on the cards. |
| U12 | "Since your last pick" digest | **WORKING: no** — the rail already shows it when you scroll back. A second surface for the same information is duplication. |
| U14 | Per-position upside: engine-decided, user-toggled, or notice-plus-toggle? | **SUPERSEDED by §14 — there is no toggle.** Prior answer, kept because its reasoning still applies to any future switch: *notice-plus-toggle (§11), derived trigger, user's action, toggle default-on inside the notice.* |
| U15 | One ranked list vs per-position lanes | **SUPERSEDED by §14 — the trigger cannot fire.** Prior answer: *derived from mode state (§11), shared mode → one list, diverged modes → lanes.* With no upside mode there is no mode divergence, so nothing splits the lanes. **The question of whether lanes are wanted for their OWN sake is now unasked, not answered.** |
| U16 | Multi-select position filter with slot presets | **SUPERSEDED by §15 — single-select.** Click-expand, pick one option, collapse to that category. Presets survive as single options (FLEX / SUPERFLEX / IDP_FLEX each cover several positions); only arbitrary combinations are lost. Prior answer kept: *multi-select is the extension.* |
| U17 | What to call all-toggles-on, given "ALL" is taken by the curated lens | **DISSOLVED by §15 — the state does not exist.** A single-select filter has no all-toggles-on condition to name; it is a list of options, one of which is ALL. The contingency flagged in the previous revision is resolved: the mixer survives, its naming collision does not. |
| U18 | Where does the debate squad expand to? | **WORKING: over the depth rows only** (§15) — the three recommendation cards stay visible, because they are what the debate is about. |
| U19 | Does the insight panel take typed input? | **WORKING: no** (§15) — read-only output; discussion happens in the debate. Keeps every typed character away from valuation, so `#107`/`#108` do not arise here. |
| U20 | What does "clear" do to the log? | **WORKING: snap-to-latest, never delete** (§15) — the same gesture as the rail's re-center. `forget_decisions` stays out of the log panel entirely. |
| U21 | Where do the freeze-timer controls live? | **WORKING: a settings button beside the Insight eye** (§15). Placement only; U3's substance is still open. |
| U13 | May the live board poll Sleeper on a timer, or is refresh strictly manual? | **RULED: polling is allowed.** The constraint is *no automatic **paid** API calls*. Sleeper reads are free and uncovered. The refresh button becomes an immediate-update override, not the only mechanism. |

### THE UPSIDE-MODE ROWS ARE SUPERSEDED — read §14 before acting on this table

U14 and U15 were ruled when a per-position upside MODE was still being built. §14 records the
owner's ruling that there is no upside mode at all, which removes the toggle U14 chose the shape
of and the mode divergence U15 keyed on. Their prior answers are kept above rather than deleted,
under the same discipline `CDME_CONTRACTS.md` applies to its own superseded proposal: the
reasoning outlived the thing it was reasoning about, and deleting it would cost the next person
the argument while saving them nothing.

**This table is the first thing a reader consults for "what did we decide?", which is exactly why
a stale row here is worse than a stale paragraph.** Anything §14 touches must be marked here too.

### On U6, because it settles something §2 left open

The owner's ruling adds what the derived window could not supply on its own: the window says how
WIDE the span is, but a 27-box span still needs a way to travel. Two pan steps, both derived
rather than chosen — **five picks** (a readable stride) and **jump to my last / next pick** (the
window's own two endpoints, which are exactly what §2 says the rail is about). The re-center
button remains the third: back to the current pick.

Nothing above changes engine behaviour. Every quantity named here already exists; what is being
decided is which of them a person can see, and what the blanks mean.

---

## 11. The depletion notice, and why it is the best answer we have found to the mode switch

**The owner's pattern**, from a spitballing pass: when a position's pool runs dry, raise a notice
that *recommends* upside grading for that position, and put the toggle **in the notice, already
on, selectable off**.

This is better than anything either of us proposed before it, for reasons worth writing down.

### The notice and the toggle are ONE OBJECT, which kills the footgun

I had argued against a bare per-position toggle because `#232` measured upside mode handing TE
**+68.58 at the flex**: a user who flips TE to upside sees TE climb and reads it as *"the engine
likes this TE"* when they caused it — a setting wearing a finding's clothes, the exact defect
class this repo keeps finding. **That failure needs the switch to be reachable without its
reason.** Here it is not. The toggle only exists attached to the evidence that produced it.

### It threads `#56` and `#55` at once, which those two usually will not allow

- The **trigger** stays derived — the per-position crossing, no invented constant (`#56`).
- The **action** is the user's — the engine proposes, the human disposes (`#55`'s philosophy,
  which kept `pick_necessity` observable).

And it dissolves `#223` (*"the transition concept is GENUINELY MISSING — for lack of a decision,
not material"*) without anyone inventing a transition. It stops being an engine rule and becomes
a conversation.

**Default ON, opt off.** Default-off means the detection never does anything for anyone who does
not go looking, which is most people. Default-on means it works out of the box and the veto
exists.

### MODE DIVERGENCE IS THE TRIGGER FOR LANE DISPLAY

The one problem a per-position mode does not solve by itself: an upside-scored WR and a
balanced-scored RB in a single ranked list are two differently-produced numbers pretending to be
comparable. The notice pattern answers it, because the notice is per-position:

> While **every position shares a mode**, one ranked list is meaningful — `#229` authorizes
> cross-position VOR. The moment **modes diverge**, the board splits into per-position lanes,
> because no single function is producing the numbers any more.

That is derived from mode state, not chosen, and it collapses two open questions into one: the
per-position toggle and the R3 lanes swing from the mockup round are the same decision.

### The wording — OWNER'S CORRECTION TO ME

My first draft said *"WR — 2 left above replacement, from 41 at the opening board."* The owner:
**"2left above replacement feels obscure to someone who hasnt spent the last month chatting with
you. too technical."** Correct. That is this repository's vocabulary, not a drafter's.

What survives the rewrite is the **before/after pair**, which explains itself without defining
anything:

> **The WR pool is thinning out.**
> 41 receivers were worth taking when this draft opened. **2 are now.**
> From here, ranking them by upside makes more sense than by proven value.
> `[x] Rank WR by upside`

Nobody needs to know what a replacement level is; 41 → 2 does the work. *"Worth taking"* is a
fair plain gloss on above-replacement — and a better one than *"worth starting"*, which would
name a genuinely different quantity (`startable_floor`, `#185`).

Two alternates kept for the build:

- *"**WR is picked over.** After the next 2, they're all much of a muchness."* — says what it
  means for the DECISION: below the line the choice stops mattering, which is precisely why the
  mode should change.
- *"**41 WRs were worth taking at the open. 2 are left.** Rank by upside now?"* — shortest, and
  poses it as a question rather than a recommendation.

**The toggle label carries as much weight as the notice.** "Rank WR by upside" says what it does;
"upside grading" is half our word.

### Details that follow

**Dismissal is three-state and must stick.** never-offered / accepted / declined. Re-prompting a
declined position every pick is nagging, and a drained pool cannot un-drain, so there is no
honest reason to ask twice. Declined stays declined for that position for the draft.

**No inverse notice.** A position still deep when a round rule would have flipped it — the
owner's original complaint — gets no popup. Notices are for actions. That case is the indicator
sitting quietly: `RB · balanced · plenty left`.

### Two things that will bite during the build, recorded now

**REPLACEMENT LEVEL MOVES.** It is computed from remaining demand and RISES as good players
leave, so "41 at the open" and "2 now" are counted against DIFFERENT lines. Each statement is
true as of its moment, and arguably the moving bar is the better signal because it captures both
the drain and the rising floor — but **the count will fall faster than players are actually
taken**, and if nobody expects that, the first sighting will read as a bug.

**It needs state that does not exist.** One integer per position, captured at the opening board
and carried. Cheap, but new.

**And per `#270`, these notices fire on the POOL, not the calendar.** Against sharp opponents the
crossing may never fire and no notice ever appears; against noisy ones they land around r12–r17.
That is correct rather than broken — tracking the real pool is the whole reason to prefer this to
"round 15" — but it means *"how often will I see this?"* has the honest answer **"depends who you
are drafting against."**

---

## 12. The mixer — and how much of it already exists

The owner arrived here from the DAW metaphor: *"i cant help but have FL studio, DAW controls come
to mind"*, then *"off/on toggles for each position, with default combinations. ALL / FLEX / SUPER
FLEX / IDP. so you can display any one position, any combination you decide to have toggled on,
or can insta-switch to established mappings."*

### What the metaphor earns

**The meter is the real find.** A mixer shows eight channels' levels at a glance without anyone
reading a number, and the level FALLS. That is the depletion countdown (§11) in its natural
visual grammar, and the clip light is the notice firing. Not a metaphor stretched over a feature
— the same information problem.

**Arm = auto.** A channel armed to act without asking is exactly §11's per-position `auto`.
**Master strip = deny-for-all.** **Mute** arrives free and nobody had proposed it: *stop showing
me kickers*. **Solo** is lane-focus.

**And FLEX is literally a BUS.** RB/WR/TE send into it; SUPER_FLEX is a second bus QB also sends
into. That is not an analogy, it is the shape of `roster_positions`. `displacement_adj`
(`#216`/`#235`) — *how much of his value your lineup cannot use because the slot he would fill is
already held* — is **bus contention**: the flex is full, his signal has nowhere to go.

### THE TRAP IN THE METAPHOR, recorded because it would be fatal

A mixer's grammar says **everything is adjustable to taste** — faders, EQ, sends. This engine's
entire claim is the opposite: it MEASURES, and its integrity depends on nobody being able to tune
it until it agrees with them. A fader labelled RB means someone boosts RB until the board
recommends RBs, and the recommendation becomes their own prior with a number painted on it.

> **Borrow the display grammar. Firewall the control grammar.** Strips, meters, at-a-glance
> parallel state, mute, arm — yes. Anything continuous that touches valuation — never.
>
> **The naming rule that falls out of it:** if a control on that panel cannot be described as a
> CHOICE, and only as an AMOUNT, it does not belong there.

### MOST OF THE FILTER ALREADY EXISTS — checked, not assumed

`draft_board_ui.filter_candidates_by_view(candidates, view)` already filters the board, and its
docstring states both firewalls this conversation independently re-derived:

- *"Never touches ranking/scoring, only which already-computed candidates are shown."*
- *"a flex-slot view reuses that slot's own real eligible-position set (`FLEX_SLOT_POSITIONS`),
  the same semantics `draft_room.py`'s own need_bonus math already keys off of, **never a
  display-only reinterpretation of what "FLEX" means**."* `lineup_optimizer` builds real lineup
  slots from that same map.

`position_view_options(positions_present, roster_positions)` already DERIVES the option list per
league: a non-superflex league is never offered SUPER_FLEX, an IDP-less league never IDP_FLEX,
and a slot whose eligible set has no candidates left yields no empty view. **The owner's ALL /
FLEX / SUPER FLEX / IDP presets are not a list anyone must maintain** — they fall out of
`roster_positions` intersected with what is actually on the board.

**What is genuinely new is MULTI-SELECT.** Today the view is single-select: ALL, or WR, or FLEX.
Independent per-position toggles with the slot names as one-click shortcuts is a real extension,
and a cheap one, because the expensive parts — derivation, the ranking firewall, and
`POSITION_VIEW_DEPTH_CAP` giving each position real depth to show — are built.

### Two hazards for the multi-select build

**"ALL" IS ALREADY TAKEN, AND MEANS SOMETHING ELSE.** Its docstring: *"ALL is one particular LENS
over that same, now-larger candidate universe, not 'show every row in it': it reconstructs the
original curated overview (top overall by value, plus each position's own single best)... the
depth lives in the position views, not in ALL."* So **every-toggle-on is NOT the ALL view** — it
would be every position's full depth, a far bigger board. If both are called ALL, a user flips
every switch, gets a different and much longer list than the ALL button gives, and reasonably
concludes it is broken. They need separate words: `OVERVIEW` for the curated lens, `EVERYTHING`
for all-toggles-on.

**A FILTERED VIEW MUST NOT RENUMBER** (`#216` B4: *"board rank is not pick order — three
ordinals, three names"*). If WR-only shows rows 1, 2, 3, that is a FOURTH ordinal wearing the
engine's rank as a disguise. Filtered rows keep their real standing — 3rd, 7th, 12th — or the
filter silently becomes a re-recommendation.

---

## 13. The per-position question, now MEASURED — and why the mixer's meters are the honest view

§11 and §12 were designed from the owner's instinct: *"would it make more sense to have
displayed pools be relative of upside modes specific to each position, relative to their
respective drain rates? not one universal that starts to modulate some pools that are still
deep."* That instinct is now measured (`#274`), and it is stronger than it was proposed as.

### The one number that settles it

First pick at which each position's own best remaining player falls to or below its replacement
level, against the pick at which the GLOBAL rule fires:

| league | picks | QB | RB | WR | TE | **global rule** |
|---|---|---|---|---|---|---|
| 8 teams | 208 | 55 | 75 | 55 | never | **never** |
| 10 teams | 260 | 70 | 135 | 70 | 230 | **230** |
| 12 teams | 312 | 85 | 185 | 85 | never | **never** |
| 14 teams | 364 | 85 | never | 100 | never | **never** |

**Quarterback and receiver run dry around pick 55-100 in every league, and the board goes on
recommending them in balanced mode for another two hundred picks.** The global switch is not a
universal that "starts to modulate pools that are still deep" — it is a switch that never fires
at all, because it waits for the one position that never runs dry.

The owner's framing was that one universal mode wrongly modulates deep pools. The measurement
says the failure runs the other direction as well, and harder: the universal mode wrongly
withholds from DRAINED pools, for most of the draft, in three leagues out of four.

### The meter is not a metaphor. It is the missing instrument

§12 called the mixer meter "the depletion countdown in its natural visual grammar." That was an
aesthetic argument. Here is the functional one: **the engine already computes this quantity per
position and then throws the per-position part away.** `replacement_levels` returns a dict keyed
by position; the mode switch collapses it with `.any()` into one boolean for the whole board.

A channel strip per position, each showing its own headroom above replacement, is not a
decorative rendering of a global number — it is the only display that does not destroy what was
measured. Four meters at 8 teams, pick 120, would read: QB clipped, WR clipped, RB clipped, TE
still nodding along. One master meter reads: fine.

### THE HOLDOUT CHANNEL IS GOING TO LOOK BROKEN, AND IT IS NOT

**CORRECTED after the FFCL Group A arm — the holdout is not always TE, and the table above is
one roster shape.** In the four leagues above (1QB, dedicated TE slot) TE is the position that
never crosses. In FFCL Group A (superflex, NO dedicated TE slot, 0.5 TEP) it inverts completely:
**tight end crosses FIRST, at pick 90 of 168, and quarterback and running back never cross.**

| league | QB | RB | WR | TE | global |
|---|---|---|---|---|---|
| 12 teams, TE slot, 1QB | 85 | 185 | 85 | **never** | never |
| **FFCL Group A**, no TE slot, superflex | *demand-exhausted* | **never** | 115 | **90** | never |

**FFCL's QB cell is not a holdout and the panel must not draw it as one** (`#277`). Its starter
demand reaches 0.0 — every QB slot in the league filled — so the position leaves the measurable
set entirely. On a channel strip that is a DARK channel, not a hot one: nothing left to measure,
as opposed to RB's meter still reading above the line. Two absences, two renderings, or the
panel repeats the mistake this table originally made.

Same mechanism, opposite sign: superflex doubles QB starter demand so QB's replacement sits far
deeper and its headroom stays large; no TE slot leaves TE demand arriving only through the flex,
so TE's replacement is shallow and its headroom closes early. **The holdout is whichever position
this league's roster shape starves of demand relative to supply.** Which one that is cannot be
hardcoded — it is a per-league fact, and that is precisely why the panel must read the levels
rather than special-case a position.

**DIRECTLY TESTED (`#278`), not inferred.** A control league and a copy differing in ONE slot —
`TE` swapped for a `FLEX`, rounds/bench/scoring/teams held identical:

| arm | QB | RB | WR | TE | holdout | global rule |
|---|---|---|---|---|---|---|
| with TE slot | 85 | never | 85 | never | RB, TE | **never fires** |
| TE slot → FLEX | 80 | 155 | 85 | **120** | **none** | **fires at 155** |

TE's headroom goes from `137 → 93 → 58 → 24 → 17 → 22 → 28 → 20 → 30` (rebounding, immortal) to
`120 → 120 → 75 → 41 → 26 → 7 → 0 → 0 → 0` (decays and pins). **One roster slot is the difference
between a mode switch that never fires and one that fires with a sixth of the draft left.** For
the panel this means the holdout channel is not a quirk to annotate — it is the thing the whole
global switch is hostage to, and the per-position meters are what make that visible at all.

The holdout's headroom does not fall monotonically — it drops toward zero and climbs back,
several times per draft (8 teams, TE: 121 → 27 → 12 → 5 → 18 → 11). A meter that rises late in a
draft will read as a bug to anyone watching, so the UI has to be built knowing it is real.

The cause is in `replacement_levels`' own docstring: a BENCH pick drains the pool without
reducing any team's starter demand, so it moves the level — and at TE it moves the replacement
down faster than it moves the best-remaining down, widening the gap. **Deep benches do not drain
the holdout position toward the crossing. They push it away from it.** Which is also why §11's depletion
notice must be worded as a LEVEL, never as a countdown that only goes one way: "2 left worth
taking" can go back up to 5, and a countdown that reverses destroys trust in everything near it.

### What this changes in §11 and §12, concretely

**§11's depletion notice stops being a nicety.** It was proposed as a gentler alternative to a
hard mode flip. It is now the only surface that would tell a drafter something true at pick 85 —
*receivers are done, quarterbacks are done, the board is still pricing them as if they are not.*

**§12's per-position toggles inherit a default that is no longer arbitrary.** A position's own
crossing is the natural arm-point for its own channel, and unlike the global rule it actually
occurs. `auto` per channel is a rule that fires; `auto` globally is a rule that did not fire in
three of the four leagues measured.

**The ALL / EVERYTHING naming problem (U17) gains a third member, and it matters more now.**
There are three different boards: `OVERVIEW` (the curated lens — top overall plus each
position's best), `EVERYTHING` (all toggles on — every position's full depth), and now the
implied fourth question of WHICH channels are armed. Arming is orthogonal to display: a muted
channel can still be armed, and it should be, or the drafter loses the warning for the position
they stopped looking at. **Mute must not imply disarm.** That is the single most likely wiring
error in this panel and it is the one that loses information silently.

### STILL OPEN, and not answered by this measurement

**RESOLVED, and it inverted the attribution** — see the correction above and `#274`'s scope
correction. What remains untested is IDP: every league measured is offence-only, and an IDP
league adds three positions with their own demand shapes, each a candidate holdout. The
instrument runs in ~20s per league on a recorded draft; this is named as the next measurement,
not assumed.

---

## 14. The pool gauge — the surface, and what it is allowed to say

**This section supersedes §11's toggle and §12's per-position mode arming.** Owner's ruling:
*"So there will be no upside mode. Just this visual to give the drafter information on the pool.
Still available."* §11's reasoning about notices is kept — a setting reachable only through its own
evidence is the right shape for any future switch — but no switch is being built, so there is no
mode divergence, and the lane-splitting rule §11 derived from it has nothing left to trigger it.
The gauge changes no valuation and gates no candidate. `#55` exactly: the engine shows, the human
decides. Evidence and full derivation: `POST_AUDIT_PLAN.md` `#282`.

### What it is

One tank per **offensive** position — IDP is excluded, and for a supply reason given below, not a
shape one. Each is drawn as a row of segments. **It spans that position's whole priced pool**,
not only its starters — an earlier version stopped at the replacement bar and so covered just 92
of 312 picks, going fully dark by pick 130 (`#282d`). The replacement bar survives as a **marker
drawn inside the tank**, showing where the position stops producing starters and begins producing
bench. Every pick in the draft now lands in a band. It cannot rebound — that is a
property of how the quantity is defined, not a behaviour to test for.

**Self-normalised per position, and this is load-bearing.** Each tank is full at ITS OWN opening
count, so a QB bar never claims to equal a WR bar in value — the cross-position comparison `#75`/
`#76` found `bpa`'s unit could not support and `#229` left undefined for the deep-bench case.
**Positions draining at different rates is the signal, not an artifact**, and a shared scale would
destroy exactly that.

### The display contract — narrower than what the engine computes

| | |
|---|---|
| **SHOW** | segments; the band marks; optionally a percentage of the position's own full pool |
| **NEVER** | raw counts, point values, band sizes, or any engine-internal population |

A count is needed to compute the fraction and is never surfaced. Two reasons, and the second is
the one that generalises: the owner's *"2 left above replacement feels obscure to someone who
hasn't spent the last month chatting with you"*, and — a count invites the reader to reason about
WHICH two players, which a gauge has no standing to imply.

### The bands — MEMBERSHIP IS DERIVED, WIDTH IS NOT A CLAIM ABOUT IT

Three cuts per position give four bands: **ELITE / MID / DEPTH / MEH**. Every player is assigned
to one **once, at pool build**, from that league's own scoring settings applied through `bpa`.

**No band is a fixed percentage or a fixed count**, and the measured sizes prove it — the same
position changes shape entirely when the scoring changes:

| | ELITE / MID / DEPTH / MEH | share of that pool |
|---|---|---|
| TE, 12-team PPR | 2/2/5/10 | 11/11/26/53 |
| TE, Fourth and Forever | 3/6/11/4 | 12/25/46/17 |
| RB, Fourth and Forever | 4/13/9/10 | 11/36/25/28 |
| QB, Fourth and Forever | 9/9/9/4 | 29/29/29/13 |

ELITE runs from 11% to 29% across eight position/league cells. A position with only two or three
elite players is a true statement about that position under that rulebook, not a rendering floor.

**The assignment is STATIC, and that is required rather than merely allowed.** The cuts are made
on opening `bpa` — the league's scoring applied to the projection, minus that position's opening
replacement level. Re-banding mid-draft would re-read the yardstick against a shrinking pool,
which is the defect `#74`/`#76` cut out of `bpa` (the ruler carried 94.5% of its movement) and the
one that made the crossing rule useless in `#271`-`#280`. One case makes a static band go stale
and is named rather than hidden: a mid-draft IR or PUP designation moves a projection under
`#191`'s haircut after the cut was made.

**EACH BAND DRAINS INSIDE ITS OWN SLICE.** Taking a mid-grade player shortens the MID slice; the
ELITE slice does not move. The total still shortens by that player — the loss just comes from
where it actually happened. An aggregate fill edge over a *count* of survivors silently assumes
the players who left were the ones at the front; drawn per band, nothing has to be assumed,
because each departure is recorded in the band it came from and the display cannot make a claim
that could be wrong.

**WIDTH IS PROPORTIONAL TO POPULATION — REVERSED, on the owner's question and against my own
earlier answer.** This document previously specified equal slices, justified as *"equal slices
give every band the resolution to show partial drain"*. **That justification was false.** Four
segments give five fill states; across the sixteen position/league cells measured, **thirteen hold
more players than that** — RB's MID band holds 13 and needs 14. Equal slices did not solve the
resolution problem, they redistributed it, and perversely: one player moved a 2-player ELITE band
by 50% and a 13-player MID band by 7.7% in the same bar.

**Proportional width makes per-player resolution CONSTANT by construction.** If width tracks
population, every band spends the same room per player — measured at 47 / 38 / 25 / 29 px per
player on a 900px bar, identical within each position. So it wins on the very criterion equal
slices were chosen for, as well as on honesty about population.

**The fill is CONTINUOUS, not segmented, and that distinction is what made the original answer
look right.** The evidence instrument (`evidence/mode_boundary/pool_gauge.py`) renders ASCII, so
characters are its quantum and a 2-segment band really does hold three states. A drawn surface has
no such cap: the fill edge moves in sub-segment steps. **The earlier reasoning took the text
instrument's limit and applied it to the drawn surface** — two independent choices collapsed into
one, then argued from the wrong one.

**The cost, stated because it is real:** proportional width lets a reader eyeball *relative*
population ("MID is three times ELITE"). It discloses no counts — you cannot read 13 off the bar
— so it stays inside the display contract above, and relative distribution is information worth
having rather than leakage.

### Sizing, and the two states

Owner's requirement: *"It will need to be large enough that the data it is trying to show is clear
and intuitive. However. We can contemplate, if you want to expand it to get a little more
information and collapse it back into the default visual."*

**DEFAULT (collapsed).** Four rows, one per position, each a full-width tank divided into its
four band slices, with an optional percentage of that position's own pool. Sized so the fill level
and the mark positions are both readable without looking twice — it needs WIDTH, and §15's layout
gives it a bottom strip rather than a sidebar corner. The constraint is real and was nearly missed:
measured against the same pools, a 260px sidebar resolves the RB tank at 7.2px per player.

**EXPANDED.** The rule for what expansion may add: **it may add TIME, never VALUE.** A pick number
is a draft coordinate the reader already has on screen; a point total is a valuation the contract
excludes. So the expanded state may carry the drain history as a shape, the pick at which a band
edge was passed, and the pick at which the tank emptied. It may not carry counts, points, band
sizes, or player names. Collapsing returns to the default with nothing lost, because everything
expansion showed was a coordinate, not a quantity.

### QB IS CUT DIFFERENTLY, AND THE RULE THAT DOES IT CARRIES NO THRESHOLD

QB is the one position whose top band swallows the pool — **24 of 42 players, 57%**, against 6-8%
for RB, TE and WR — because its dead tail is proportionally the largest and the cutting chases the
biggest gulf. One-stage cutting leaves QB at 24/8/2/8, a **two-player band drawn across four
segments**, while hiding two clean cliffs inside the 24 (QB3 and QB12, both 3.5x+ the median
adjacent gap, both independently flagged by the engine's own cliff detector).

So the gauge falls back to cutting the live portion first when — and only when — one-stage produces
**a band holding fewer players than the segments allotted to draw it**. That is a display-capacity
rule, the same class as `SPAN`, not a judgment about value (`#56`). It fires for QB and only QB on
every arm measured, and the report names which positions took it so the claim cannot rot.

Two-stage was tested as the general rule and **lost everywhere else** — TE 94.3% → 87.4%, WR 93.9%
→ 87.2%, RB 93.7% → 91.7%. It is a fallback, never the default. Full evidence: `#282f`.

### COVERAGE: AN EMPTY TANK MEANS "NOTHING PRICED", NOT "NOTHING LEFT"

The gauge prices a minority of the rows a drafter can see — **QB 42 of 155, WR 198 of 452, TE 115
of 256, RB 126 of 256**, and on an IDP board roughly a third of each defensive position. The tank
is built from the priced players, so it reaches empty when those are gone regardless of how many
unpriced rows remain. **The surface must show the coverage fraction**, or an empty tank reads as
exhaustion when the true statement is that the engine stopped having opinions. Whether a real
draft ever reaches that point is **not established** — IDP is the case to watch, not a proven
failure. See `#282g`.

### IDP GETS NO TANK — and the reason is supply, not shape

**Offence only. Do not draw a gauge for LB, DB or DL**, and do not band them, until the supply
gap closes (`#210`, `#49`). This is a ruling the register carried and this document did not, which
is how it reads as "one tank per position" above — that sentence means one tank per OFFENSIVE
position.

**The case is the SOURCE, not the curve.** Two weaker arguments were offered first and neither is
the reason:

- *"The curve is linear."* It is — DB band means run 117 / 94 / 68 / 43, and margins over
  arbitrary equal slices are near-vacuous at **DB +0.5, LB +1.8, DL +2.0**, against +4.6 to +6.9
  for the skill positions. Tackle accumulation is smooth, so there is no tier structure to find.
  True, but it argues the bands would be uninformative, not that they would be wrong.
- *"IDP production is more volatile."* **Believed, and NOT measurable here** — there is no
  week-level data and no `std_dev` column anywhere in this repository. Stating it as fact would be
  asserting what we cannot check.

**The argument that actually stands: IDP has no vendor pricing at all.** Not thin — absent. The
valuation table carries **0 of 91 LB, 0 of 153 DB, 0 of 171 DL** with a projection or a
`proj_3yr`, against 39/40 QB, 72/79 RB, 105/109 WR, 48/52 TE. Every IDP number here comes from
Sleeper stat lines scored through the rulebook, with nothing to check them against. Offence
carries two independent sources; **IDP carries one**, in a system whose first principle is that no
single source is ground truth. Publishing four-grade bands off that would dress a supply defect as
a grade — and the gauge's whole claim is that its bands are derived.

**The trigger to revisit is an INPUT, not a rewrite:** a second IDP source, or the real board
`#49` names. Nothing about the banding math needs to change when it arrives.

### THE QB TANK IS GOING TO LOOK WRONG, AND IT IS NOT

Above the replacement bar, **QB is the flattest position, not the steepest** — the opposite of the
intuition most drafters (and the owner, in the exchange that produced this) bring to it. In a
12-team 1QB league the eleven quarterbacks clearing replacement run 369 / 350 / 343 / 334: a 10%
spread, against RB's 426 → 194. Banding beats arbitrary equal slices there by **+0.1 points** —
the honest null.

So the QB tank's marks will sit near even thirds and will look like they mean nothing. They mean
exactly one true thing: *this position is evenly graded, there is no elite tier to miss.* **No
suppression rule was added** — "hide the marks when the margin is small" is a threshold, and a
bound is not a threshold (`#56`). The gauge draws what is there and the prose carries the warning.

### What the gauge lets a drafter infer, and the one inference it does NOT support

When you take a player from below the starter line, the league's starting slots had no room for
him at the opening board — 181 of 312 picks in Fourth and Forever. **He is still a graded player**:
`#282d` corrected `#282`'s claim that nothing measured remained down there. What is absent below
the line is surplus over replacement, not production, and production separates those players
cleanly.

**It does not follow that such a pick is wrong.** Taking a player below the bar while the tank
still holds someone above it is a different state entirely — a CHOICE, made for reasons the gauge
cannot see, and in the measured drafts it happened exactly once in 312 picks. The two must never
render the same way. Collapsing a choice into an absence is the defect that had to be corrected
twice already (§13's holdout banner, `#277a`, `#280`), and this is the third surface where the
same mistake is available.

---

## 15. The layout pass — WORKING, all of it

**TIER: WORKING, in full.** The owner's framing, recorded because it governs how this section is
read: *"this is not law. This is inspiration. Ideas brainstorming. This may suck as a design."*
Nothing here is RULED. It exists so the build has a direction and so the next pass starts from
where this one stopped instead of reconstructing it. Contradict it freely — that is a change of
mind, not a defect, and it needs no withdrawal ceremony (§1's two-tier rule).

Source: an owner prose description, a hand sketch, and four rounds of notes on top of it.

### The frame

| region | holds |
|---|---|
| **header** | league name, scoring settings, format — e.g. *SF 12-man TEP Dynasty*. Logo, roster label, menu. |
| **top** | the pick rail (§2). Clock bar beneath it: time remaining, `Pick 3.07 — USER NAME IS UP`, and the on-the-clock card (pic, name, team, position, drafter). |
| **left sidebar** | your roster filling as you draft, scrollable. A **right-pullout expands it to ALL rosters**. |
| **centre** | three recommendation cards across the top; depth rows beneath; the positional filter control along the bottom. |
| **right sidebar** | Insight (eye) button and a settings button; the insight output panel; the chronological log; the pool gauges at the bottom. |

**THE FORMAT IS ON SCREEN AT ALL TIMES, and that is not decoration.** §14's bands are derived
from the league's own scoring, so the same position draws a different shape in a different
league. A user comparing two leagues needs the rulebook visible to know why.

### The three expansions, and what each one covers

Three surfaces slide out. **None of them replaces another panel's content** — each covers a
region and retreats:

- **The draft board.** A button under the clock bar, above the cards, expands the full board over
  the centre. The rail is what grows; there is no separate tab.
- **All rosters.** The left sidebar's pullout. This answers what §1 promised as "full rosters"
  and the earlier layouts had nowhere to put.
- **The debate squad.** The right sidebar's left arrow slides it over **the depth rows only,
  leaving the three recommendation cards visible.** That was the point: the cards are what the
  debate is *about*, so covering them would hide the subject while you read the argument.

**This supersedes U4.** The old question was *"does the full-board tab replace the rail or
overlay it?"* — the answer is neither. It also supersedes §1's RULED *"a tab opens the full
rosters / draft board"*: two different pullouts, two different regions, no tab.

### Insight is READ-ONLY; discussion lives in the debate

An earlier draft of this pass put a text input under the insight panel. **Removed.** The owner's
rule: *"Only the text generated from insight, no volley. You want to discuss? open the debate
slider."*

Two things fall out, and both are improvements:

- **The cost shape is bounded and already counted.** `run_debate` is **4** provider calls (one
  per chair), `debate_pick` is **3**, and `ask_moderator_followup` is **1**. The shipped default
  matches the owner's stated intent exactly: the first hit is the full squad, follow-ups are
  Moderator-only. So the total is `3or4 + 1×N`, and N is the only part a user controls. The
  panel should show the running follow-up count for the current pick — one number, no new
  machinery.
- **No typed text goes anywhere near a valuation.** `#107` and `#108` (overrides reaching
  valuation unattributed; no chair channel for *"this rests on your own override"*) simply do not
  arise on this screen. **Keep it that way.** The moment typed text can move a recommendation, it
  needs provenance, and that is a larger build than the box looks.

The Insight button still needs **on-clock gating** — §1 RULED debate is callable only while on
the clock, and an insight call is the same class of billed action.

### The log — a VIEW, never a store

Chronological, scrollable, carrying **both** Moderator verdicts and a notification on each pick
selection, so the picks act as chapter breaks in a long scroll.

**It persists nothing of its own.** It is a merged view over `decision_log.py` (per-league
verdicts) and the draft record (picks). Nothing new to write.

**"CLEAR" MEANS SNAP-TO-LATEST, NOT DELETE**, and the distinction is load-bearing rather than
pedantic. `decision_log.py` is an audit trail built to be read back much later: `set_outcome`
tags each verdict *Worked / Didn't Work / Mixed / Too Early To Tell*, and
`search_decisions_with_outcomes` reads them months on. That is the front office's track record.
`forget_decisions(league_id)` exists and wipes a league's log entirely. **A "Clear" button wired
to that would destroy the record the grading feature exists to read, and nobody would notice
until they went looking for a track record that was not there.**

So: snap-to-latest resets the *scroll*, not the data — and it is the same gesture as §1's
RULED re-center button on the rail. Make them look and behave identically; a user who learns one
has learned the other. A real deletion, if ever wanted, belongs in settings behind a
confirmation. A display choice is not a data operation.

### The positional filter — SINGLE-SELECT, which changes two prior rulings

Owner's description: *"Click to expand the full range, select the display option you want, it
collapses showing that new filter category only."*

- **U16 is SUPERSEDED.** It stands on the record as *"multi-select position filter with slot
  presets — WORKING: yes."* This is single-select.
- **U17 DISSOLVES.** It asked what to call all-toggles-on given ALL was taken by the curated
  lens. **There is no toggles-on state to name.** It is a list of options, one of which is ALL.

Nothing of value is lost: FLEX, SUPERFLEX and IDP_FLEX are each ONE option covering several
positions, so the presets survive intact. What goes is arbitrary combinations — "QB and TE only"
— which nobody asked for.

**The tanks are NOT the filter.** This was floated and the owner rejected it: *"i dont think I
want the tanks to operate as the display filters."* They sit near each other and share four
labels, which is what invited the idea; they stay separate controls.

**#216 B4 still binds:** a filtered view must not renumber. Filtered rows keep their real
standing.

### The gauges sit in a bottom strip — which dissolves a width worry

§14 said the gauge *"gets the width, not a corner."* The sketch puts the four tanks in a strip
under the sidebar, labelled **"Available Player Pool Strength"** — a better name than anything
previously written here, because it says *strength*, not *count*, which is exactly what §14's
display contract allows.

A strip is wide, so the corner-resolution problem never arises. **Recorded because it was nearly
a defect:** in a 260px sidebar the RB tank resolves at 7.2px per player and would have been
unreadable with segment rendering.

**The sketch drew variable-width bands before the reversal was implemented** — hatched blocks of
visibly different sizes, which is proportional banding arrived at independently of the
arithmetic in §14's width note.

### Parked, with the reasoning attached

Not dropped. Each needs a decision before the region it belongs to can be built:

| question | why it is still open |
|---|---|
| Does the log span the whole draft or reset per pick? | Whole-draft reads better *if* pick notifications are the dividers; untested either way. |
| Does the Moderator thread close when the pick lands? | §1 gates debate to the clock, which argues for closing it. The transcript would then persist onto the drafted player's emblem — a surface that already exists for exactly this. |
| Where is the commit gesture? | U8 ruled hold-to-lock with a rising bar. Nothing in this layout holds it. |
| One clock or two? | The sketch shows one (`1:27 remains`). §8 describes two — Sleeper's and the user's freeze timer. |
| Where does the coverage fraction go? | §14 requires it (an empty tank means *nothing priced*, not *nothing left*). A thin strip has no room for a caption per tank. The freed space under the read-only insight panel is the obvious candidate. |
