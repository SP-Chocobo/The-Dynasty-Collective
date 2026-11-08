# The three levels — landing page, in-league dashboard, expansion

Contemplation requested in this order: *"contemplate the main menu screen before addressing what
the main in-league-focus dashboard should include, then expand upon."* This file answers the
first and frames the second. It is argument, not a drawing.

Governed by `#338`: **the render layer computes nothing.** Every element below names the engine
function that returns it, or is marked as not reachable.

---

## 1. The landing page IS the claim band, one arity up

The in-league band ranks claims on your attention. The landing page ranks **leagues** on your
attention. That is the same question at a different arity, and it means the landing page needs
**no new engine concept**:

```
in-league     compose(fx)                  -> {shown, hidden, bye_profile}
landing       [compose(fx) for fx in Ls]   -> rank leagues by their own top claim
```

`front_claims.LADDER` already orders claim kinds (clock / hole / bye / thin). `CAP = 3` already
decides how much a surface may say. The absence grammar already distinguishes measured, floor,
constructed and absent. **All of it lifts unchanged.** A landing page that invents its own
ranking is re-deriving a judgment that exists — `#126`, and the mechanism behind `#336b`.

### The row

One line per league. The standing constraint, applied: *who, why, other valid options, at what
cost.*

| element | engine basis | verdict |
|---|---|---|
| league name | Sleeper league settings | REAL, free |
| the top claim, in the claim's own words | `compose(fx)["shown"][0]` | REAL — costs the fixture |
| how many more are open | `len(shown) + len(hidden)` | REAL — same fetch |
| the claim's own figure | carried on the claim | REAL |
| freshness | `freshness.recency_grade` | REAL, cheap — manifest only |

Nothing else. No per-league badge, no colour-coded health dot, no sparkline.

### The ordering

By ladder rung of the top claim, then by that claim's own magnitude. **Never alphabetical, never
by league name, never by last-viewed.** `#339` is the fresh evidence for why that matters: when
`thin_sort_key` lost its count, the order silently reverted to the alphabet and a one-QB room
could fall below the cap behind a two-man TE room. The same failure at league scale hides a
league, not a position.

### The quiet league is not hidden

`VOICE.md` rule 8: leaving is a success state. A league with an empty band gets a visible, quiet
line — not a collapsed section, not a filtered-out row. The page's whole value is that you can
see at a glance that six of nine leagues want nothing from you. Hiding them turns the feature
back into an absence.

---

## 2. THE HIGHEST-RISK SURFACE IN THE APP, and the one number that is honest

The landing page's natural visual form is *N rows plus a summary*. That shape begs for a summary
that **cannot exist**. Every tempting candidate is forbidden, and by the same ruling that already
withheld `survival_probability` and `estimate_future_pick_value`:

| the tempting summary | why not |
|---|---|
| portfolio health score / grade | no model behind it. `BRIEF.md`'s forbidden table, first row |
| "your worst league" | requires comparing claim magnitudes ACROSS leagues — see below |
| total bye damage across leagues | `bye_collision` returns trade-value points under ONE league's pricing; summing across leagues adds numbers on different scales. The `round3/front.html` "UV pts" defect, multiplied |
| leagues ranked by roster strength | nothing ranks teams. `depth_label` is a ratio band. This is `#336b` verbatim |

**Cross-league magnitude comparison is the subtle one and it is NOT reachable.** A bye cost of 95
in one league and 95 in another are not the same quantity: `bye_collision` prices in trade value,
each league applies its own scoring, and `set_league_format` selects a different rankings export
per format. Two leagues' point figures are different units wearing the same label. The ladder
RUNG is comparable across leagues (a hole is a hole). The FIGURE is not.

So: **order leagues by rung, which is comparable. Never by figure, which is not.** Within a rung,
order by the figure only among leagues of the same format, or not at all.

### The one honest headline

```
"3 of 9 leagues have something open."
```

A **count of real things**, not a score. It is `sum(1 for fx in Ls if compose(fx)["shown"])`,
every term of which the engine already returns, and it is exactly the three-second answer the
brief asks for — at portfolio scale. `VOICE.md` rule 5 in its natural home: name what was
checked, not a verdict.

**The headline is a count. Never a grade.**

---

## 3. n-scaling — the layout holds, the COMPUTE is the open question

The owner is in 9 leagues plus a chop league, and names people in 20+.

| n | the right opening surface |
|---|---|
| 1 | **skip the landing page.** Opening a one-league manager onto a chooser is a tax with no information in it. Go straight to the dashboard |
| 2–9 | the landing page is the home screen |
| 20+ | still one line each — twenty lines is scannable. The layout does not break |

What breaks at 20 is not layout. It is **cost**, and the shape of the problem is `#337`'s
exactly one level up: a per-league loop over a quantity whose price nobody measured.

`compose(fx)` needs `structural_holes`, `bye_profile`, `thin_positions`, `current_week`. Of
those, `bye_profile` comes from `lineup_optimizer.bye_collision`, which **solves the lineup once
per week** — and `thin_positions` needs `positional_depth` across every team in the league.

```
UNMEASURED: the wall-clock cost of one league's claim band.
```

That number decides the design, and it has not been taken. `#337` is the precedent for why a
guess is not good enough here: `get_season_projections` *looked* like one request and was
eighteen, and nine leagues made it 162.

Three designs follow from three possible answers, and it is not worth choosing between them
before the measurement:

- **cheap (< ~100ms/league)** — compute all N live on load. Simplest; no new state.
- **middling** — compute on load from the **persisted** snapshot (`load_latest_snapshot` already
  writes `{league_id}_latest.json`), never from the network. The landing page becomes a disk read.
- **expensive (> ~1s/league)** — the crystallization must be **persisted with the snapshot** at
  sync time, so the landing page reads a stored claim rather than recomputing one. This is the
  only arm that needs new engine work, and it is also the only arm that makes the landing page
  instant at n=20.

**Next action: measure it, on an idle machine, before drawing anything.** A timing taken while
the test suite is running would be a plausible number about something else.

### The chop league — what is actually known, and the one question worth asking

Checked rather than assumed. `draft_battery.league_format_hint` discriminates on exactly
`{scoring, superflex, te_premium}`, derived from `scoring_settings` and `roster_positions`.
**There is no elimination concept anywhere in this engine.** A chop league therefore presents to
it as an ordinary league, and `compose` would say TRUE things about that roster — holes, byes and
depth are roster facts and do not care about the format.

The narrow thing that does not survive: **the bye rung's justification is futurity.** The ladder
earns the bye claim its place because it is "a known FUTURE week with a measured cost, and
planning only works in advance". In an elimination format a week-10 cost is conditional on still
being alive in week 10, and nothing here models elimination. The claim is not false; its WEIGHT
rests on an assumption the engine cannot check.

*(Not to be confused with `survival_probability`, which this engine DOES compute and deliberately
withholds — `test_withheld_propagation.py` exists to prove it never leaks, including as a delta.
That quantity is DRAFT-PICK availability, "will this player last to my next turn". It has nothing
to do with league elimination, and I nearly connected the two while writing this section.
Conflating them would have invented a capability.)*

So the question for the owner is specific rather than open-ended: **in your chop league, does
elimination happen early enough to change which week you should care about?** If yes, the bye
rung is mis-weighted there and that is a real ruling to make. If the chop is a side pot over an
otherwise normal season, nothing changes.

---

## 4. What this settles for the dashboard, and what it does not

Settled by the above, and carried into the next contemplation:

1. The dashboard is `compose(fx)` for the focused league — the band, already built and certified
   under `#333`.
2. **`CHECKS_RUN` is needed by both levels** and is the one genuine engine gap (`#338`). The
   landing page's honest headline is a count of open leagues; the dashboard's is a count of clean
   checks. Neither exists yet. `compose` returns `{shown, hidden, bye_profile}` — no count of
   what it checked. Spec says five, two designers drew four, engine returns none.
3. Expansion obeys two rules already agreed: **a crystallization may hide the detail but never
   the basis**, and **what expands must be something the engine computes separately.** The second
   rule is `#338` read forward — if expanding a row requires the UI to compute the detail, the
   detail is not expandable, it is fabricated.

**CORRECTION to my own deferral.** An earlier draft of this file deferred the dashboard's
CONTENTS pending the per-league timing measurement. That was wrong: the measurement is about
cost at N leagues, and a focused dashboard pays one league's cost, which the app already pays
today. The content question is answerable now and is answered in section 5. What genuinely waits
is `deck` as the visual spine and any wiring, the latter on `#339`.

---

## 5. The in-league dashboard — what goes on it

The content budget is not a matter of taste: it is the ten quantities `BRIEF.md`'s verified table
lists, and nothing else exists. The design question is therefore **which of the ten earn the
front, and which live one level down.**

The deciding test comes from the brief: *"A dashboard shows numbers; a triage surface ranks
claims on your attention."* So the question for each quantity is not "is it real?" but **"does it
ask anything of me?"**

### On the front

| element | basis | why it earns the front |
|---|---|---|
| the claim band, `CAP = 3` | `front_claims.compose` | this IS the triage. Already built and certified under `#333` |
| the checks-run line | **`CHECKS_RUN` — does not exist yet (`#338`)** | see below; it is load-bearing, not decoration |
| one freshness stamp | `freshness.recency_grade` | it qualifies everything else on the page. A figure whose age is unknown is not a figure |

That is all. Three things.

### THE RULING THAT DOES THE MOST WORK: record does not belong on the front

`league_standings.team_standings` returns record and points for/against. It is **REAL, cheap, and
already computed** — and it should not be on the front page.

It is a number that **demands nothing.** Knowing you are 4-2 does not tell you to do anything;
it cannot be acted on, and it will be the same number tomorrow. On a triage surface it occupies
the most valuable space in the app to say something the reader cannot use. It belongs in
`League`, where someone has gone looking for it.

This generalises, and it is the sharpest form of the standing constraint — *"I dont need all the
variables"*:

> **The front page is not where true-but-inert facts go.** Truth is the floor, not the
> qualification. A fact earns the front page by asking something of the reader.

Three of the ten quantities fail that test and are named here so the question is settled rather
than re-litigated per design: **record / points for-against**, **which future picks have moved**
(a ledger, not a claim — it reports history), and **per-source freshness ages** (the grade asks;
the ages explain).

### Why `CHECKS_RUN` is load-bearing rather than nice-to-have

Most weeks the band is EMPTY — the brief says so, and that is the feature. When the band is
empty, the checks line is **the only content on the page.** The quiet state is not a degraded
version of the loud one; it is the common case, and `CHECKS_RUN` is the entirety of what it says.

So the gap recorded in `#338` is not a copy detail. **Without it, the most frequent state of the
app's most important screen has nothing true to display** — which is precisely the condition
that produced `#336b`: a surface with nothing true to say reaches for something false.

---

## 6. Expansion — the two rules, and what passes them

1. **A crystallization may hide the detail but never the basis.**
2. **What expands must be something the engine computes SEPARATELY** — `#338` read forward. If
   opening a row requires the UI to compute the detail, that detail is not expandable, it is
   fabricated.

Rule 2 is strict and it is what makes the list short. What passes:

| the claim | what expands under it | separately computed? |
|---|---|---|
| "Week 6 costs 95" | the full week strip, each week its own figure | YES — `bye_collision` solves the lineup per week; eighteen distinct results |
| "Thin at DEF" | the position × label table | YES — `depth_label` is evaluated per position against its own peer set |
| a hole card | which slots no body can fill | YES — `slot_coverage` is per slot |
| the freshness stamp | per-source ages | YES — `recency_grade` is DERIVED from them, so the ages are the real detail |
| a starter injury flag | nothing | **NO.** `is_material_injury_status` returns a boolean. There is no second layer, and an expansion would have to invent severity |

That last row is the rule earning its place: four of five claims expand, one does not, and the
one that does not is exactly where a designer would most want a drill-down.

### The absence that must survive expansion

An expansion is also where the absence grammar is most likely to be lost, because a detail panel
is a table and a table wants a value in every cell. The four states — measured, `>=` floor,
CONSTRUCTED, and absent-with-its-reason — have to survive the drill-down intact. A week strip
whose unmeasured weeks render as `0` is the `#187` defect at eighteen times the scale, and
`#339` is this session's proof that a composer will substitute a zero the moment the quantity
stops arriving.

---

Not settled, deliberately: what the dashboard shows BELOW the band, and `deck` as the visual
spine. Both wait on the measurement above and on `#339`'s repair, because a dashboard wired to
today's `compute_readiness` would print "0 rostered" about a two-man room.
