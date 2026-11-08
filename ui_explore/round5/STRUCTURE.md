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

## 3. n-scaling — the layout holds, and the compute is now MEASURED

The owner is in 9 leagues plus a chop league, and names people in 20+.

| n | the right opening surface |
|---|---|
| 1 | **skip the landing page.** Opening a one-league manager onto a chooser is a tax with no information in it. Go straight to the dashboard |
| 2–9 | the landing page is the home screen |
| 20+ | still one line each — twenty lines is scannable. The layout does not break |

What breaks at 20 is not layout. It is **cost** — and the shape is `#337`'s one level up: a
per-league price for work that does not vary per league. **Now measured (`#340`), on an idle
machine, instrumenting the production calls.**

### The answer: cost is `k` DISTINCT FORMATS, not `n` leagues

```
n=9, grouped by format     k=1  1024 ms     k=2  2006 ms     k=3  2975 ms
n=9, interleaved           flat ~7100 ms regardless of k
```

A format switch both reloads the rankings export (~330 ms) AND clears `merge_player`'s price
memo, which lives in `_load()`. So grouped is ~1.0 s per distinct format, interleaved pays it per
LEAGUE, and the warm marginal per extra league is **3-9 ms**. Grouped cost is therefore
essentially independent of `n`: twenty leagues in three formats costs about what nine in three
costs. **Sort order is worth 7x, and a merger pool was tested and loses to sorting.**

Three predictions of mine were wrong and `#340` records all three; the one that matters for this
document is that I expected `bye_collision` to dominate because it solves the lineup per week. It
is **0.4 ms**. The cost is `positional_depth` pricing a ~6,594-row universe. Cost here lives in
DATA VOLUME, not loop counts.

### What that settles

| arm | verdict |
|---|---|
| compute all N live | **VIABLE at `k <= 2`** (~1-2 s, inside the three-second test) — but only iterating GROUPED BY FORMAT |
| read persisted snapshots instead of the network | **MIS-FRAMED BY ME.** I assumed the cost was I/O; it is CPU. A snapshot read avoids nothing unless the snapshot CONTAINS the computed depth, which is the third arm |
| persist the crystallization at sync time | **the fallback, for large `k`.** At `k=5` the live path is ~5 s and over budget. Sync already pays this cost and already makes dozens of HTTP calls, so computing the band there is marginal |

**`k` is knowable, not guessable:** it is `league_format_hint` over the owner's actual leagues.
The open question is no longer "what does it cost" but "how many distinct formats do nine leagues
plus a chop league span".

### Two orderings, and they must not become one list

There is **no multi-league loop today** — `sync_league` runs once for the active league
(`app.py:1130`). But `league_prefs.py` already discovers the league list and keeps
`prefs["order"]`.

That order is a **display** preference. Format grouping is a **compute** order. Collapsing them
would either silently reorder the user's chosen display for performance, or make the compute
order follow a display preference and lose the 7x. One home each.


### The chop league — ANSWERED, and I was wrong TWICE before getting here

Both of my earlier positions are recorded because the second was a retraction of a correct one.

**First draft:** worried an elimination format breaks the bye rung, since a week-10 cost is
conditional on being alive in week 10.

**Second draft — WRONG, and withdrawn.** On being told elimination happens weekly rather than at
a season boundary, I concluded the concern dissolved: "you play every week either way, so a
future week's cost is actionable in exactly the same sense." That is false. The owner's
correction:

> if you're in last on that monday, however, you're done and gone, so

You play every week *until you don't*. **Each Monday is a gate.** Week 11 exists for you only if
you clear 6, 7, 8, 9 and 10. The first draft was right and the retraction was the error.

#### Scope: one rung of four

```
clock   a deadline you can actually miss          declared, UNREACHABLE, has never fired
hole    cannot field a legal lineup at all        immediate
bye     "a known future week with a measured cost, and planning only works in advance"
thin    a standing weakness, no deadline          standing
```

Only `bye` reasons about future weeks, so the entire impact is confined to one rung — and the
assumption sits in that rung's OWN justification string. The comment above `LADDER` says the
reason is written beside each rung "so the order can be argued with rather than merely obeyed."
This is that mechanism working: an owner argued with a stated reason and the reason lost.

#### The defect, stated precisely

`byes_ahead` picks its week with `max(ahead, key=lambda w: ahead[w])` — largest loss among weeks
at or after now, with **no term for distance**. On the fixture's real data the largest and the
nearest coincide (week 6, 95), which is why this has never surfaced. Invert them:

```
week 6: 51     week 10: 95     ->  the band names WEEK 10
```

In an elimination format that names a week the reader may never reach, while week 6 is the gate
they must actually pass. For a surface whose whole purpose is ranking claims on attention, that
is the worst available failure.

#### Why there is NO ranking fix, and what is already correct

- Ordering by elimination risk needs a LAST-PLACE THRESHOLD: forward-looking, distributional,
  the family this engine withholds alongside playoff odds.
- Ordering by nearness needs a MATERIALITY threshold — a week costing 4 is not a gate — and that
  is a constant nobody has argued for. `#56`: a bound is not a threshold; if a repair needs a
  magnitude nobody has defended, that IS the finding.

So the ordering stays as it is, and the thing that makes it safe already exists: **the week strip
shows every week ahead carrying its own cost.** The reader supplies the survival reasoning the
engine cannot. The owner's standing constraint is the licence, and it anticipated exactly this:

> for any pick you make, there are going to be multiple valid options, which means that not
> taking the engine's #1 isn't inherently wrong

#### THE ONE CONCRETE CHANGE — and it is against `VOICE.md`, which I wrote

`VOICE.md` rule 7 is "No superlative it cannot prove", and its applied table then marks
**"Week 6 is the one that hurts"** as `keep`, reasoned as "indicative, provable, the week is the
subject." It is indicative and the week is the subject. It is **not provable**: "the one that
hurts" is a superlative over an objective, and it only holds under maximisation. Under
floor-avoidance the week that hurts is the one that eliminates you, which the engine cannot
identify.

```
was        Week 6 is the one that hurts.
becomes    Week 6 costs 95, the largest of six weeks ahead.
```

Magnitude and scope, both measured; no claim about which week matters most. This is the same
defect class as `#336b` — prose outrunning its function — caught in a voice spec rather than in
shipped code, and caught by the owner describing their league rather than by any ratchet.

#### Reachable, not real: "am I near the bottom this week"

Computable from parts that exist — `optimize_lineup` per team, `compute_points_from_stats` under
this league's settings, rank the twelve — and **`#337` just made it cheaper**, since the per-week
projection lines are now fetched once per season rather than eighteen times per league.

Two qualifications to settle before anything is drawn:

1. It is a RANK, immediately after an item spent on a fabricated one. The difference is
   categorical: `#336b`'s rank was INFERRED from a ratio band that ranks nothing; this one would
   be COMPUTED from each team's own projected lineup. Computed is admissible, inferred is not.
2. Whether projected 11th separates from projected 10th is unmeasured. `estimate_future_pick_value`
   was withheld at 1.89 slots of error on 12; measure the separation before rendering an ordinal.

#### The risk posture is UNREACHABLE, which closes the question

Floor-avoidance implies a minimise-downside lineup. Sleeper publishes POINT ESTIMATES, not
distributions — there is no variance to minimise. Not unimplemented: unreachable. Saying so
settles it rather than parking it.

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
