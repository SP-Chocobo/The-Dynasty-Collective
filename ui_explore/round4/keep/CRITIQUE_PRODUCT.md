# The Keep — PRODUCT adversary (FRONT 2)

**The question asked:** does every displayed element represent something CDME can actually
calculate or retrieve?

**Answer:** no. Most of it is, and the measured core is the best sourcing in the round — the bye
hero, its six-bar profile, its method caption and the Record absence are all exactly what the
named functions return, in the engine's own words. But the page carries **two fabricated facts that are not merely unsourced, they are false against the fixture
it draws from**, a basis legend that contradicts its own page in the quiet state, and a footer
sentence asserting something about the engine that four modules disprove.

Verified against source: `front_claims`, `front_page`, `lineup_optimizer`, `depth_ratings`,
`depth_chart`, `lineup_readiness`, `league_standings`, `pick_ledger`, `freshness`,
`player_universe`, `data_merger`, `draft_strategy`, `app.py`, `ui_explore/front_fixture.json`,
`ui_explore/capture_front_fixture.py`. One probe was run (read-only, scratch) that reproduces the
fixture's depth chart and prints the per-position peer field; its output is quoted below and is
the evidence for findings 1 and 6.

---

## FIRST: `BRIEF.md` IS WRONG, IN SIX PLACES, AND THIS DESIGN'S WORST COPY CAME STRAIGHT OUT OF IT

You asked to be told if the summary is wrong. It is wrong in the **permissive** direction in five
places and in the **attribution** direction in two. The most damaging one is not in the
Real/Forbidden table at all — it is in the *data block* underneath it, which designers read as
the licensed copy for this roster.

### B1. The data block licenses a rank the engine never computes — and the rank is false

> ```
> thin          DEF: 1 rostered (bottom of league)
>               TE:  2 rostered (bottom of league) — only 1 of 2 could be priced, so a FLOOR
> ```

`depth_ratings.depth_label` computes no rank. It computes a ratio to the **mean**:

```python
_STRONG_RATIO = 1.3
_WEAK_RATIO = 0.7
...
ratio = (cell["value"] if use_value else cell["count"]) / avg
return STRONG if ratio >= _STRONG_RATIO else WEAK if ratio <= _WEAK_RATIO else AVERAGE
```

`Weak` means "at or below 0.7× the league average at this position". It does not mean last, and
no function in `depth_ratings`, `depth_chart`, `lineup_readiness` or `front_claims` ranks teams
within a position. The only rank anywhere in the product is `app.py`'s team-level
`value_rank_order`, and even that one refuses to be computed when the field is incomplete:

```python
# app.py ~6315
# Win rank is over every team; an asset-base rank can only be over the teams
# that have one. Comparing a rank of 12 against a rank of 7 is not a
# comparison, so this says what it cannot do instead of doing it anyway.
```

That refusal is exactly what the brief's parenthetical overrode. And the brief's claim is **false
in fact** for both positions. Reproducing the fixture's own depth chart:

```
=== DEF === label='Weak'  ranked_on=count  league_avg=1.58  teams_with_a_cell=12 of 12
  count=1: Team 12, Team 1 (MINE), Team 4, Team 2, Team 5     <- five-way tie at the bottom
  count=2: Teams 8, 7, 9, 11, 10, 3, 6
  by VALUE: Team 8 0.0 · Team 4 1.0 · Team 5 2.0 · Team 2 4.0 · Team 3 6.0 ·
            Team 12 7.0 · Team 6 7.0 · Team 7 9.0 · Team 1 (MINE) 9.0
            -> my DEF is JOINT-HIGHEST priced DEF room in the league

=== TE === label='Weak'  ranked_on=value  league_avg=39.17
  rank  1/12: Team 4   value=10.0
  rank  2/12: Team 5   value=15.0
  rank  3/12: Team 1   value=23.0   <== MINE  (10th of 12 from the top; TWO teams below me)
```

Note also which field each label was earned on: **DEF's `Weak` came from `count`, not `value`**,
because three teams have `value: None` at DEF and `depth_label`'s `use_value` guard requires every
peer cell to be priced. So the DEF claim is a *headcount* comparison and the TE claim is a *value*
comparison — two different measurements drawn in identical frames (see finding 10).

### B2. Real table: holes are not produced by `league_usable_positions`

> | structural holes (no body who can fill a slot) | set difference against `league_usable_positions` |

`capture_front_fixture.py` argues at length that this is the wrong function and does not use it:

```python
# league_usable_positions EXPANDS flex slots -- its docstring says so ...
# Both behaviours are right for that job and wrong for this one: in a standard FLEX league
# with no dedicated TE slot it reports TE as a slot nobody can fill ...
# slot_coverage answers the counting question directly and takes no `value` by design.
slots = lo.slots_from_roster_positions(roster_positions)
cover = lo.slot_coverage(mine, slots)
```

The producer is `lineup_optimizer.slot_coverage` + `slots_from_roster_positions`. The fixture's
own `_provenance.basis.structural_holes` string still says `league_usable_positions`, so the stale
attribution is in the engine's output too — worth fixing at source, not just in the brief.
(`NOTES.md` repeats it: "Holes: none | set difference against `league_usable_positions`".)

### B3. Real table: "starters filled / total slots | `lineup_readiness.compute_readiness`"

True in production. **Not true of the number this page draws.** `compute_readiness` is never
called by the capture; it counts `slot == "Starter"`, which only exists when a human submitted a
lineup to Sleeper. The fixture's 10-of-10 comes from `lo.optimize_lineup` +
`len(slots_from_roster_positions(...))` — which is *why* the field is CONSTRUCTED. `NOTES.md`
repeats the wrong attribution ("`lineup_readiness.compute_readiness` on a replayed seat"). The
page's stamp is right; the lineage both documents give for it is not.

### B4. Real table: "which future picks you own | `pick_ledger.build_pick_ledger`"

The ledger does not answer that. Its own docstring:

> Sleeper only lists a pick here once it's actually moved from its original roster; an untouched
> pick is assumed to still belong to its original roster and isn't worth listing, so this ledger
> is deliberately just the **diffs, not a full inventory** of every hypothetical future pick.

It answers *which picks have moved*. "Which picks you own" is not a reachable quantity. This feeds
finding 16.

### B5. The Real table licenses a **grade**, which this design's footer says the engine cannot compute

> | data freshness grade + per-source ages | `freshness.build_freshness_manifest` + `recency_grade` |

against the page's own footer: *"Nothing here is a grade, a rating or a probability — the engine
does not compute those."* The brief's Real table and the design's footer directly contradict each
other, and the brief is the one that is right. See finding 5.

### B6. `The Prytaneum` is listed as a destination; in `app.py` it is not one

> `Matchup` · `Roster Maintenance` · `Draft Room` · `League` · `Import Audit` · `The Prytaneum`

```python
# app.py:3739
main_view = st.segmented_control(
    "Dashboard view",
    options=[MATCHUP_VIEW, MAINTENANCE_VIEW, DRAFT_VIEW, LEAGUE_VIEW, IMPORT_VIEW],
```

Five rooms. The Prytaneum is `with st.container(key="debate_dock")` at app.py:6917 —
a fixed-position dock rendered *under every view*, with `DOCK_LEVELS = ["collapsed", "partial",
"full"]`. The design is not at fault for following the brief; the brief should say "five rooms and
one dock", because a crest on a door-rail is the wrong affordance for a panel that is already on
screen.

**What is right in the table:** the bye rows, `bye_concentration`, the depth *label* vocabulary
(`Strong`/`Average`/`Weak`/`None — no rostered players here` — exact), the record row, the
`is_material_injury_status` gate, the Questionable exclusion, the pick-price withholding (verified:
`CDME_CONTRACTS.md:6922`, "mean absolute slot error **1.89 of 12 — 17% of the whole range**"), and
the ruling that positional strength may be four discrete steps and never a meter. The design obeys
every one of the Forbidden rows. No letter grade, no odds, no 0–100 depth bar, no "% rostered", no
Questionable, no pick price appears on either file.

---

## FINDINGS, MOST SEVERE FIRST

### 1. FABRICATED — "Bottom of this league at the position", drawn four times, false both times

**Where:** `desktop.html:376` (DEF), `desktop.html:388` (TE), `mobile.html:290` (DEF),
`mobile.html:297` (TE).

**What is wrong:** the page asserts an ordinal rank — last in a twelve-team league — from a label
that is a ratio band around the mean. Nothing computes a per-position rank, and when the rank is
computed by hand the claim is false for both positions.

**Evidence:** `depth_ratings.py:_WEAK_RATIO = 0.7` and the `ratio = cell/avg` line quoted in B1.
The probe output in B1: my DEF sits in a **five-way tie at count=1** and is the **joint-highest
priced DEF room in the league** (9.0, tied with Team 7); my TE ranks **10th of 12 by value with
Team 4 at 10.0 and Team 5 at 15.0 below me**. A reader who acts on "bottom of this league at DEF"
is acting on the inverse of the truth about DEF quality.

Worse, the TE figure the rank would be computed from is itself a floor — `valued_count: 1` of
`count: 2`, `depth_chart.depth_value_label` returns `" (>=23, 1 of 2 priced)"`. The true TE total
is ≥ 23, so the real position can only be *higher* than 10th. The page states a rank off a floor
and the floor's own marker is two lines away.

**Fix:** delete the sentence. Replace with what the engine says, which is a sentence the design
already has room for: *"At or below 0.7× this league's average TE room"* (or the four-step label
the design's own notes reserve the cut-stone block for). Cost to the design: **nothing**. It is
one clause of prose in a block whose layout does not change. The rhetorical punch of "bottom" is
the only loss, and it was borrowed punch.

---

### 2. FABRICATED — a `TE` position shield on the bye summons; week 6 is an RB

**Where:** `desktop.html:318`, `mobile.html:242` — the kicker on the gonfalon, the most prominent
non-numeric element on the page.

```html
<span class="pos" style="--c:var(--pos-te)">…<b>TE</b></span><span class="ins-sm">Bye collision · a starter sits</span>
```

**What is wrong:** `NOTES.md` states the rule for this component itself — *"Rule: hue means
**which position**, never severity"* — so on a bye-collision claim the shield can only be read as
"the position involved in this collision". That position is RB. The badge says TE.

**Evidence:** `front_fixture.json`. Exactly one rostered player has `bye: 6` —
`{"name": "Jahmyr Gibbs", "position": "RB", "value": 95.0, "bye": 6}` — and he is in `starters`
(`"9221"`). `bye_profile.worst_week_detail` = `{"starters_out": 1, "players_out": 1,
"value_lost": 95.0, "bench_used": 0}`. The two rostered TEs are Kyle Pitts (`bye: 11`) and Dawson
Knox (`bye: 7`). TE has **no bye in week 6 at all**, and weeks 7 and 11 cost 8 and 23 points
respectively — the two cheapest and second-cheapest weeks on the chart. The badge attributes the
page's single largest number to the position least implicated by it.

The `95` hero is Gibbs's entire trade value (`roster[0].value = 95.0`, `bench_used: 0`,
`bench_value_used: 0`), so the attribution is not even ambiguous.

**Fix:** either drop the badge from the summons (the kicker reads fine as `Bye collision · a
starter sits`), or make it `RB` and name him. `front_claims` does not return the player, but the
roster rows the same fixture carries do: `bye == worst_week` over `roster[]` intersected with
`starters` is a two-line derivation, which makes this **REACHABLE**, and `NOTES.md` already asks
for it ("If the engine can name the starter, that name belongs in the kicker"). Cost: nothing —
the slot already exists and the design wants to fill it.

---

### 3. ABSENCE NOT RENDERED — `current_week` is ABSENT, and the page draws the bye claim as a deadline anyway

**Where:** `desktop.html:319` / `mobile.html:243` (`Week 6 **is** the one that hurts.`),
`desktop.html:321` (`One starter **sits** in week 6 … **your schedule**`), `desktop.html:312`
(section header `Needs you · 1 of 1`), `desktop.html:344` (`Nothing stands against you **this
week**`), `desktop.html:300` (door sub-line `Matchup — **this week** · lineup`), and the whole
gonfalon-vs-block severity split, which exists to say "this one has a deadline".

**What is wrong:** the page has a four-state absence grammar and uses it for Record, Hurt and
Picks. The one absence that qualifies its headline is the one absence it never renders.

**Evidence:** `front_fixture.json` → `"current_week": null`, with its own basis string:

> `"current_week": "ABSENT -- a replayed draft has no point in the season. A live league reads
> season/week from Sleeper's NFL state; without it the bye claim cannot assert that a week is
> still ahead"`

and `front_claims.byes_ahead`'s docstring, which is a ruling, not a note:

> *"THE RUNG'S REASON IS FUTURITY, so a claim that cannot establish futurity must not borrow the
> urgency. … with none, the same numbers are a season-shape fact and **the caller says that
> instead of implying a deadline**. The first version of the page had no concept of now and would
> happily have put a week already played second on the band — the one thing a triage surface must
> never do, because it spends the reader's trust in every other claim on it."*

With `current_week = None`, `compose()` returns `ahead_only: False`. The page is the caller, and
it does the forbidden thing: present tense, "your schedule", a `Needs you` header, and the one
frame shape reserved for urgency.

Two corroborations. `front_claims.LADDER` justifies the bye rung *only* on futurity — `("bye", "a
known future week with a measured cost, and planning only works in advance")` — so without
futurity the page's ranking of bye above thin has lost its stated reason. And `app.py`'s own
`sleeper_proj_label` refuses the exact words the Matchup door uses: *"the week it reflects isn't
always 'this week' (during preseason it falls back to regular week 1), so it has to be computed
from the snapshot's own resolved projection_request"* — which is why production prints `Wk6 Proj`
and never "this week".

**Fix:** two sentences and one stamp. Reframe the summons as a season-shape fact ("Week 6 is where
this roster's bye cost lands") and add a sixth ledger row, or a line in the gonfalon's kicker:
`Week — · not in this capture · a replayed draft has no point in a season, so nothing here can say
a week is still ahead`. Cost to the design: real but small — the gonfalon frame (urgency) is no
longer strictly earned in this state, so either the frame becomes the cut-stone block when
`ahead_only` is false, or the design states the caveat and keeps the frame. That is a genuine
design decision rather than a copy edit, and it is the one this page most needs to make.

---

### 4. THE BASIS LEGEND DOES NOT TOGGLE — in the quiet state the footer calls a CONSTRUCTED chart "measured"

**Where:** `desktop.html:422`, `mobile.html:331`.

> *"Bye profile and thin positions are **measured**. Lineup and seat are **constructed**. …"*

**What is wrong:** the toggle is `document.documentElement.classList.toggle('quiet')` and the
state machine is `.q{display:none}` / `html.quiet .q{display:block}` / `html.quiet
.live{display:none}` (desktop.html:209–211). The plinth's legend `<span>` carries **neither**
class. So in the quiet state the footer asserts the bye profile is measured while the bye profile
immediately above it is stamped `Constructed` with the sub-line *"an even profile, drawn for the
demo"* (desktop.html:349), and asserts thin positions are measured while the page shows zero of
them and a laurel saying none exist.

The design's whole claim to authority is that it is the page that tells you what its own numbers
are. In one of its two states its basis legend is the single most wrong sentence on it, and the
quiet state is the state the brief specifically warned invented reassurance would hide in.

**Fix:** two `<span class="live">` / `<span class="q">` variants of the legend. Cost: zero —
the mechanism is already in the file, used eight times.

---

### 5. THE FOOTER'S CLAIM ABOUT THE ENGINE IS FALSE — ruling, as requested

**Where:** `desktop.html:422`, last clause. (Dropped entirely on mobile, which is its own problem
— see 8.)

> *"Nothing here is a grade, a rating or a probability — the engine does not compute those."*

**Verdict: the first clause is nearly true of the page. The second clause is false about the
engine, on all three nouns.**

- **Rating.** `depth_ratings.py`, line 1: *"Peer-relative depth **rating** -- Strong/Average/Weak/
  None, shared by every surface that needs to say 'how does this team's depth at this position
  compare to the rest of the league.'"* The module's own `LABELS` comment distinguishes a rating
  from an absence state: *"None is NOT in here on purpose -- it is the absence state ('cannot be
  measured'), **not a rating**"*. This page displays that rating's output — "Thin at DEF" is
  `label in depth_ratings.THIN_LABELS`.
- **Grade.** `data_merger.recency_grade()` returns `Fresh`/`Recent`/`Aging`/`Stale` from
  `COMPOSITE_RECENCY_GRADES`, described in its own comment as *"a site-wide freshness **grade**
  across every loaded source"*. `front_page.compose_unsynced` returns a key literally named
  `"grade"`. `app.py:3440` renders `Data Freshness: {_grade}` **on every view**, including behind
  all six of this page's doors. And `data_merger.py:2857` returns `{"score": round(score, 1), …}`,
  rendered at `app.py:2013` as `f"{composite['score']:.0f}/100"` — a 0–100 score.
- **Probability.** `draft_strategy.py`: `survival_probability -- P(still on the board when it's my
  turn again)`, `position_pace_probability()`, `RANK_TAKE_PROBABILITY = {1: 0.55, 2: 0.32, …}`,
  `RUN_TAKE_PROBABILITY_CAP = 0.90`. There is a whole test file, `test_probability_bounds.py`,
  whose first line is *"A quantity called a probability must be one"*.

So the sentence is a confident, checkable, false assertion about the engine, printed on the page
whose entire credibility rests on being right about the engine. It is also internally
inconsistent with the brief's own Real table (B5), which licenses drawing the freshness grade.

The *page-level* half needs one word too: "Thin at DEF" is a thresholded view of a rating, so
"nothing here is a rating" is a stretch even about itself.

**Fix:** say what is true and narrower. *"No team rating, no letter grade, no odds — the engine
computes none of those, and the depth label behind 'thin' is four named steps, never a score."*
Cost: nothing. It is a better sentence: it names the three things prior mocks actually faked
instead of over-claiming a general innocence.

---

### 6. FABRICATED — quiet state: "Every position is at or above its league peers"

**Where:** `desktop.html:401`, `mobile.html:304` — the laurel block, the quiet state's reassurance.

**What is wrong:** "no position is thin" does **not** imply "at or above its league peers". `Weak`
is `ratio <= 0.7`; everything between 0.7 and 1.3 is `Average`, and most of that band is *below*
the mean. The sentence converts a floor at 0.7× into a floor at 1.0×.

**Evidence:** on this very roster, with the thin positions excluded, an `Average` position is
below its peers:

```
WR   label='Average' on=value mine=162.0 avg=167.25 ratio=0.969  -> BELOW peers
QB   label='Average' on=value mine=44.0  avg=43.25  ratio=1.017
RB   label='Average' on=value mine=137.0 avg=120.58 ratio=1.136
K    label='Average' on=count mine=2     avg=1.67   ratio=1.200
```

The live roster's WR room is not thin and is below the league average. The quiet-state sentence
is therefore not true even of the page's own live data, let alone of an arbitrary quiet roster.
This is precisely the "invented reassurance in the quiet state" the task predicted.

**Fix:** *"No position is at or below 0.7× its league peers, and every slot has a body who can
fill it."* Or shorter and fully safe: *"No position room is thin against this league."* Cost: none;
it is the same line length.

The second half of the sentence — "every slot has a body who can fill it" — is **REAL**
(`lineup_optimizer.slot_coverage`). Keep it.

---

### 7. PRECISION OVERCLAIM — the quiet chart's axis is an invented, undeclared 40, and it makes 26 taller than 51

**Where:** `desktop.html:351–356`, `mobile.html:272–277`. The `--p` values are `60 52 65 47 57 55`
against the live chart's `100 8.4 53.7 4.2 58.9 24.2`.

**What is wrong:** the CONSTRUCTED stamp declares the *numbers* are invented. It says nothing
about the *scale*, and the scale is invented separately, inconsistently, and in violation of the
design's own stated rule.

**Evidence.** `.bars{height:150px}` and `.bar .f{height:calc(var(--p) * 1%)}` (desktop.html:165,
169; mobile uses an 84px track, mobile.html:112, 115) — a fixed track in both states. Implied axis
maximum:

```
live  bars:  95/1.00  8/.084  51/.537  4/.042  56/.589  23/.242  -> axis max = 95  (the max bar)
quiet bars:  24/.60  21/.52  26/.65  19/.47  23/.57  22/.55      -> axis max = 40  (nothing)
```

`NOTES.md`'s own component rule for this piece: *"Never a meter, never a 0–100 scale — **the axis
is the max bar**."* The quiet state breaks it. Rendered consequence on the desktop 150px track:

```
live  51 points -> 80.5 px
quiet 26 points -> 97.5 px      a value half as large, drawn 21% taller, same component, one click apart
```

A reader who toggles — which is the only way to see both states, and the toggle is the page's own
affordance — reads the quiet week as roughly 60–65% as costly as week 6. It is 25%. The six quiet
values are legible, so the lie is recoverable; but the bars are the thing the eye reads in three
seconds and they are wrong by a factor of 2.4.

**Fix:** set the quiet `--p` off 26 as the max (`92 81 100 73 88 85`), or better, carry the axis
maximum as a visible tick on both charts. Cost: six numbers, or one label. Nothing is lost.

---

### 8. BASIS COLLAPSE AND SILENT ABSENCE — the mobile ledger

**Where:** `mobile.html:311–312`, `mobile.html:331`.

```html
<span class="k">Lineup</span><span class="v">10 of 10 filled, no holes <span class="stamp">Constructed</span></span>
```

**What is wrong, three ways:**

1. **One stamp over two different bases.** `10 of 10` is CONSTRUCTED (`front_fixture.json`:
   `"starters": "CONSTRUCTED -- optimize_lineup's best legal lineup …"`). `no holes` is MEASURED
   (`"structural_holes": "measured -- …"`, and genuinely `slot_coverage`). They are merged into one
   cell under one gold `Constructed` chip. A reader cannot recover that one of the two facts is
   real. This is the named "basis collapse" failure, in the one component built to prevent it.
2. **Two absences vanish.** Desktop carries `Hurt — not measured` and `Picks — not in this
   capture`, each with its reason. Mobile drops both rows. The brief's grammar is *"a value that
   was not measured renders as an em dash carrying its reason"*; a deleted row carries neither.
3. **The footer covers for the deletion.** `mobile.html:331` reads *"Byes and thin positions are
   measured; lineup and seat constructed; record absent. Pool 5,357."* — presented as the page's
   complete basis account, and it is not: injuries and picks are absent and unmentioned, holes is
   measured and unmentioned, and the whole "nothing here is a grade" sentence is gone. A mobile
   reader is told the page has one absence. It has three.

**Fix:** split the Lineup row (`Lineup · 10 of 10 [Constructed]` / `Holes · None`) and keep the
Hurt and Picks rows. `NOTES.md` says the mobile budget has 32px of slack against the 1328px
two-screen rule and three rows cost roughly 90px, so this one **does** cost the design: either the
two-screen budget or the door-wall at the bottom. That is a real trade and the right answer is to
spend the budget — an absence grammar that is desktop-only is not an absence grammar.

---

### 9. WRONG REASON FOR A REAL ABSENCE — "Hurt"

**Where:** `desktop.html:412`.

> `Hurt — — not measured · material injuries on starters are read off a live roster only`

**What is wrong:** injury statuses are in this capture. The reason given points at the wrong
missing input.

**Evidence:** `front_fixture.json._provenance.players_db`, truncated on disk but printed in full
by the probe:

```
'injury_statuses_present': ['DNR', 'IR', 'NA', 'Out', 'PUP', 'Questionable', 'Sus']
```

and `run_draft_battery.build_players_db_from_capture` records that field deliberately — *"Stated,
not assumed: the whole reason this function exists."* What is missing is not the injury data, it
is the *`slot == "Starter"` gate*: `lineup_readiness.compute_readiness` counts starters from
`app.py`'s roster_table, which is populated from Sleeper's submitted `starters` array, and a
drafted roster has none. So the honest reason is "the starting lineup here is constructed, so
'on starters' has no measured referent", and the honest status is **REACHABLE**: running
`is_material_injury_status` over the ten constructed starters returns a real count about a
constructed lineup, which the design already knows how to stamp.

**Fix:** correct the reason string, or draw the value with a CONSTRUCTED stamp. Cost: none. The
current line is the kind of plausible-sounding reason `front_page.split_reason` was written to
avoid — *"a wrong reason reads as reassurance, which is worse than a clumsy one"*.

---

### 10. BASIS COLLAPSE — the two thin claims are two different measurements in identical frames

**Where:** `desktop.html:372–390`, `mobile.html:288–298`.

**What is wrong:** the DEF claim's `Weak` was earned on **count**; the TE claim's on **value**.
Both render as `Thin at X` + a big mono number + "Bottom of this league at the position", so the
reader cannot tell that one says "you have fewer bodies than the league averages" and the other
says "your room is worth less than the league averages".

**Evidence:** `depth_ratings.depth_label`'s guard —
`use_value = cell["value"] is not None and all(c["value"] is not None for c in peer_cells)` —
and the probe: DEF `ranked_on=count` (Teams 9, 10, 11 carry `value: None` at DEF), TE
`ranked_on=value`. The numbers the page draws (`1 rostered`, `2 rostered`) are counts in both
cases, so for TE the displayed quantity is not even the quantity the label was computed from.

Related, in the same component: there is **no rendering for `None — no rostered players here`**,
the other member of `depth_ratings.THIN_LABELS` and the more severe of the two — a position room
with zero bodies. `front_claims` ranks a `hole` above a `thin`, but an empty *room* that is not
yet an unfillable *slot* still arrives as a `thin` claim with `count: 0`, and the cut-stone block
would print a 30px `0` under the word "rostered". The brief's grammar forbids exactly that (`never
as 0`).

**Fix:** carry the ranked-on field into the claim's one-line caveat ("fewer bodies than this
league averages" / "worth less than this league averages"), and give the block a `count: 0`
variant that prints the engine's own string. Cost: one extra micro-label per block, which the
block already has a slot for (the `.floor` chip's position).

---

### 11. PRECISION OVERCLAIM — the floor marker is attached to a count that is exact

**Where:** `desktop.html:389` and especially `mobile.html:297`.

```html
<h3>Thin at TE · <span class="num">2</span> rostered</h3>
<p>Bottom of this league. <span class="floor">≥ floor · 1 of 2 priced</span></p>
```

**What is wrong:** the quantity that is a floor is the **value** (`>=23`), not the **count**.
`count: 2` is exact — `positional_depth`'s docstring: *"Every rostered player raises `count`; only
the ones the merger could price raise `value`."* On mobile the `≥ floor` chip sits four words
after "2 rostered" with no explanatory prose, so it reads as "at least 2 TEs". On desktop the
prose rescues it — *"Only 1 of the 2 could be priced, so the comparison is a floor, not a total"*
— which is a genuinely well-written sentence and exactly right. Mobile cut the sentence and kept
the chip.

**Fix:** mobile chip reads `≥ value floor · 1 of 2 priced`, or draw the engine's own string,
`≥ 23 · 1 of 2 priced`, which attaches the `≥` to the number it qualifies. Cost: three words.

---

### 12. FABRICATED — `Seat 5`, where the fixture says seat 1

**Where:** `desktop.html:287`, `mobile.html:232`.

**What is wrong:** the only number on the page that could have been copied verbatim from the
fixture was invented instead.

**Evidence:** `capture_front_fixture.py`: `SEAT = 1  # the roster the page is "mine"`;
`front_fixture.json`: `"_provenance": {"seat": 1, …}`, `"team": "Team 1"`.

It carries a `Constructed` stamp, so the grammar is formally satisfied — but a constructed value
is for a quantity that *cannot* be measured here, and this one is sitting in the file. Shipping an
invented value where a real one exists is the habit the stamp is supposed to make unnecessary, and
it undermines every other stamp on the page: a reader who checks one `Constructed` value and finds
it arbitrary has no reason to trust that `10 of 10` is anything else.

**Fix:** `Seat 1`. Cost: one character.

---

### 13. DOORS — three of five sub-lines point at the wrong room or at nothing

The sub-lines carry real product weight: `NOTES.md`'s rule is *"the sub-line names what lives
**inside** (trades, free agents, standings) so those do not need doors of their own"*. If a
sub-line is wrong, the design's defence for having only six doors fails.

| door (desktop.html) | sub-line | verdict |
|---|---|---|
| Matchup (300) | `this week · lineup` | **lineup REAL** (`st.subheader("Lineup Readiness")`, app.py:3811). **"this week" not establishable** — `current_week` is ABSENT here, and `sleeper_proj_label` deliberately prints `Wk{N}` because *"the week it reflects isn't always 'this week'"*. |
| Roster Maintenance (301) | `depth · free agents` | **REAL** — `st.subheader("Free Agents")` (4022), `st.expander("Positional depth detail")` (4688). **But it omits the Trade Calculator, which is in this room** (`hcol1.subheader("Trade Calculator")`, ~4171). |
| Draft Room (302) | `boards · pick counts` | **boards REAL** (`st.expander("🗂 Boards stored for this league")`, 6011). **"pick counts" FABRICATED.** `build_pick_ledger` is called at app.py 2211 (prompt context), 4326 (Maintenance) and 6338 (League) — **never inside the Draft Room branch (4824–6118)**. And per B4 the engine has no pick *inventory* to count at all. The only literal pick count in that room is `st.expander(f"📋 Picks so far ({len(md['picks'])})")` — picks already made in a mock draft, not picks you own. |
| League (303) | `standings · trades` | **standings REAL** (`league_standings.team_standings`, 6139; `LADDER_LENS = "🏆 Standings"`, 6159). **"trades" MISROUTES.** League shows `"**Picks acquired via trade:** …"` (6348) — real — but the Trade Calculator is in Roster Maintenance, and League's own crosslink proves it: `st.session_state.pending_main_view = MAINTENANCE_VIEW` (6389). The brief's "Trade Calculator … exists inside those views" is satisfied by the *other* door, whose sub-line doesn't say so. |
| Import Audit (304) | `sources · freshness` | **sources REAL** (the view reports what Sleeper returns, plus unparsable projection files). **"freshness" FABRICATED.** `build_freshness_manifest` does not appear anywhere in 6397–6491. It renders in `build_context` (the LLM prompt), in a **global status band at app.py:3428 that is on every view**, and in the unsynced front page at 3632. Nothing about freshness is behind this door. |
| The Prytaneum (305) | `the council · four voices` | **REAL** — `bot_config.ROLES = ("quant", "beat", "contrarian", "moderator")`, and the source says *"With one key, all four chairs run on it."* The *door* is the problem, not the sub-line: see B6, it is a dock. |

**Also: mobile drops every sub-line** (`mobile.html:319–324` carry names only). So on mobile the
design's justification for six doors — the sub-lines — does not exist, and a mobile reader has no
way to learn that trades, standings and free agents live inside.

**Fix:** `Draft Room — boards · mock drafts`; `League — standings · rosters · picks acquired`;
`Roster Maintenance — depth · free agents · trades`; `Import Audit — sources · what Sleeper
returns`; `Matchup — your lineup`. Cost: nothing on desktop. On mobile, finding the room for five
two-word sub-lines does cost scroll, and the honest alternative is fewer doors on mobile rather
than nameless ones.

---

### 14. IMPLIED CAUSATION / ADVICE — "so no single week is worth a move", plus an arithmetic error

**Where:** `desktop.html:359`.

> `No week carries more than 19% of the season's bye damage, so no single week is worth a move.`

**Two problems.**

*The advice.* Nothing in the engine computes whether a week is worth a move. `bye_concentration`
returns a ratio and says so: *"deliberately a RATIO, so shape is separated from severity"*. Its
docstring will support "no week is decisive" at 0.19 (*"0.25 means the damage is spread thin
enough that no week is decisive"*) — which is a reading of shape. It will not support "worth a
move", which is a cost-benefit claim about a transaction, and `lineup_readiness`'s docstring is
the standing rule here: *"Explicitly **NOT** a recommendation."* Mobile drops the clause
(`mobile.html:280`), so the two files disagree about whether the page gives advice.

*The arithmetic.* The quiet profile is `24 21 26 19 23 22`; total 135; max 26; `26/135 = 19.26%`.
Week 8 carries **more** than 19%. The page's one quantitative claim about its own invented data is
false against that data by rounding in the flattering direction.

**Fix:** `No week carries more than a fifth of the season's bye damage, so the cost is spread.`
Cost: nothing.

---

### 15. REACHABLE, OMITTED ON A FALSE PREMISE — freshness

**Where:** absent from both files. `NOTES.md` justifies the omission:

> *"Freshness grade and per-source ages are real (`build_freshness_manifest`) but the replayed
> capture carries none, so the page does not draw them."*

**What is wrong:** `build_freshness_manifest` is never empty. Two of its rows are unconditional:

```python
entries.append(sleeper_client.players_freshness_entry())
entries.append(sleeper_client.season_projection_freshness_entry(snapshot))
```

and the Draft Sharks rows are unconditional in practice — app.py, ~1962: *"Dynasty Rankings and
the Trade Value Chart both ship as a committed baseline … is_loaded/is_trade_values_loaded are
unconditionally true now regardless of any live upload."* The module exists *because* it answers
with no league synced: *"a deliberate affordance so the Data Freshness grade renders before any
league is synced … That makes it the one piece of real content the app can honestly show in the
EMPTY state."* `front_page.compose_unsynced` is built on exactly that.

So the page omitted the one always-available measured quantity, and then advertised it behind a
door where it does not live (finding 13).

**Fix:** `build_freshness_manifest({}, merger)` in `capture_front_fixture.py`, which already holds
`merger = dm.DataMerger()` at line 72 — two lines, and then the sixth ledger row
`NOTES.md` already reserves. Cost: nothing but the row, and the page has a slot for it on desktop.

---

### 16. OVERCLAIMED PROMISE — "Picks — counts only, never prices, when it is"

**Where:** `desktop.html:414`.

**What is wrong:** the price withholding is **correctly honoured** — credit where due, and the
ruling is real (`CDME_CONTRACTS.md:6922`, mean absolute slot error 1.89 of 12). But the promise
that *counts* will appear is a promise about a quantity that does not exist. Per B4,
`build_pick_ledger` is "deliberately just the diffs, not a full inventory", so what the engine can
show is picks *acquired* and *given away* via trade — not how many picks you own.

**Fix:** `— not in this capture · picks acquired or given away, never priced`. Cost: nothing.

---

### 17. NO AFFORDANCE FOR THE CAP — `front_claims.hidden` has nowhere to go

**Where:** `desktop.html:312`/`367` (`1 of 1` and `2`), and the absence of any "+N more".

**What is wrong:** `front_claims.CAP = 3` with an explicit ruling about what the surface owes:

> *"The cost is that a genuinely four-problem week hides one, and `more` names what was hidden
> rather than dropping it."*

`compose()` returns `{"shown": claims[:3], "hidden": claims[3:]}`. Neither file has an element for
`hidden`, and `NOTES.md` concedes the page has no room for a third standing claim. So a
four-problem week silently drops a claim, which is the one outcome the cap's ruling forbids.

Separately, `1 of 1` has no referent. `compose()` on this fixture returns three shown claims and
zero hidden; nothing returns "1 of 1". If it means "one top-rung claim of one", the denominator is
invented; if it means "one of one claim", it contradicts the `2` beside it.

**Fix:** `Needs you · 1` and `Also standing · 2 (+1 more)` driven off `len(hidden)`. Cost: trivial
on desktop; on mobile `NOTES.md`'s own suggestion ("collapse into '+1 more' inside the second
block") is the right answer and should be built, not described.

---

### 18. UNQUALIFIED TENSE — "Holes: None" beside a chart whose whole point is that week 6 empties a slot

**Where:** `desktop.html:411`.

> `Holes — None · every slot has a rostered body who can fill it`

**What is wrong:** true today, false in week 6, and the page does not say which. `slot_coverage` is
run over the whole roster with no week removed. In week 6 the roster has two RBs, one is out
(Gibbs), the other (Barkley) is already starting, `bench_used: 0`, `bench_value_used: 0` — and
`optimize_lineup`'s own rule is *"an unfillable slot stays empty and that player stays benched,
never a fabricated invalid start."* So week 6 has an **empty starting slot**, which is why
`value_lost` equals Gibbs's full 95 rather than a replacement delta.

The engine knows the lineup breaks in week 6. The page states the cost in points and, two columns
away, reassures the reader that every slot has a body. Both are true of different moments and
neither says which moment.

**Fix:** `Holes — None today · every slot has a rostered body who can fill it`, and let the
summons say what it already knows: week 6 is not 95 points of degradation, it is a slot that
cannot be filled. That is a *stronger* claim and it is free — `bench_used` and `players_out` are
already in the fixture. Cost: none; it improves the headline.

---

### 19. ROUTE DIVERGES FROM THE ENGINE'S OWN RULING — thin claims go to Roster Maintenance

**Where:** `desktop.html:377`, `desktop.html:390`, `mobile.html:289`/`296`.

`front_claims.compose` sets the route in the claim object: `{"kind": "thin", "route": "League", …}`.
The page routes to Roster Maintenance. Both rooms carry depth (`Positional depth detail` at 4688;
`DEPTH_LENS = "📊 Depth Map"` at 6159), but the **peer comparison the claim rests on** — every
team's depth at every position — is the League Depth Map, and `depth_ratings`' own extraction note
says the Depth Map is one of the two consumers of this judgment. The page sends the reader to the
room that holds their own depth, not the comparison.

The bye claim's `Open Matchup` matches `{"kind": "bye", "route": "Matchup"}` exactly — correct,
and worth saying, even though Matchup is a current-week view that cannot act on a week-6 bye.
That weak route is the engine's ruling, not the design's defect.

**Fix:** follow the claim object. Cost: one word, twice.

---

### 20. LABEL — `Pool 5,357 players`

**Where:** `desktop.html:292`, `mobile.html:331`.

**REAL quantity, ambiguous name.** 5,357 is `_provenance.universe_rows` = `len(universe)` from
`player_universe.build_player_universe` — the players this league can price and rank, after the
`FANTASY_POSITIONS` and retired/stale filters. The same `_provenance` block carries a field
literally named `players_in_pool: 6594`. Two "pool" numbers in one provenance dict; the page prints
the smaller under the larger's name.

**Fix:** `5,357 players ranked for this league`. Cost: three words. Low severity, listed because
the page's authority is nomenclature discipline and this is the one place it borrows a word that
is already taken.

---

## WHAT SURVIVES ATTACK — precisely

Not a courtesy. These are the elements I tried to break and could not.

- **The bye hero and its chart.** `95` = `bye_profile.worst_week_loss` / `worst_week_detail.value_lost`;
  `worst_week: 6`; the six bars are `weeks` verbatim (`6:95, 7:8, 8:51, 9:4, 10:56, 11:23`);
  `40%` = `concentration: 0.401`; `56` is genuinely the runner-up. `basis: "measured"` with
  `unknown_byes: 0`, so `front_claims`' `partial` flag is correctly False and `95` is correctly
  drawn as a total with no `≥`. The live chart's axis **is** the max bar, to within rounding.
  This is the one page in this round I could not find a single wrong digit in.
- **"value lost, not bodies lost"** (`desktop.html:325`) quotes `bye_collision`'s own docstring
  (*"IT MEASURES VALUE LOST, NOT BODIES LOST, and that distinction is the whole point"*). The
  method caption at `desktop.html:335` is an accurate plain-English rendering of the solve, and
  *"Weeks 1–5 and 12+ carry no byes for this roster"* is exactly right:
  `weeks = sorted({int(p["bye"]) for p in roster_players if p.get("bye") is not None})`, and this
  roster's sixteen byes are exactly `{6,7,8,9,10,11}`. (Mobile drops this caption — the one
  sentence establishing basis for the page's biggest number is desktop-only. Put it back.)
- **The Record absence.** *"— absent · no capture holds a roster's result"* is verbatim correct.
  Checked: `data/league_captures/` holds three JSON files, none with a `rosters` or `wins` key;
  they capture league *rules*. `league_standings._reported` exists specifically so a missing field
  is not a 0, and the page honours it.
- **No forbidden quantity appears.** No team rating, no letter grade, no playoff/title/win
  probability, no 0–100 positional meter, no "% rostered", no trending adds, nothing about
  Questionable players, no pick price. Six prior mocks failed here and this one does not.
- **"Thin at X"** is the engine's own surface phrasing, reused rather than reinvented
  (`app.py:3866`, `f"Thin at {pos_list}"`), off the shared `depth_ratings.THIN_LABELS`.
- **The four-state grammar is genuinely differentiated in CSS**, not just in prose: measured is
  plain or large mono; constructed is a gold-bordered `.stamp`; a floor is a dotted-underline
  micro-label; absence is an em dash plus an italic reason in the same cell. No bare `0` and no
  blank cell appears anywhere in either file, in either state. That part of the design works, and
  it is why findings 4, 8 and 11 are so costly — they are failures of a mechanism that is
  otherwise correct.
- **Six doors, six rooms that exist.** No Player Compare, Trade Finder, Waiver Wire, Pick
  Calculator, Roster Health, League Notes or Analytics. The destination *set* is clean; only three
  sub-lines and the Prytaneum's room-ness are wrong.
- **`NOTES.md`'s "findings, not drawings" section** is the right instinct and three of its four
  items are correct. Two are not: the freshness premise is false (15) and the
  `compute_readiness` attribution is wrong (B3). And it asserts the headline "stays anonymous"
  while the artifact puts a TE shield on it (2).

---

## VERDICT TABLE

| element | verdict |
|---|---|
| `95` + unit, six bars, week labels, `40%`, `56`, method caption | **REAL** — `lineup_optimizer.bye_collision` / `bye_concentration` |
| "One starter sits" | **REAL** — `worst_week_detail.starters_out` |
| `Thin at DEF` / `Thin at TE`, `1` / `2` rostered | **REAL** — `depth_chart.positional_depth` + `depth_ratings.depth_label` (WEAK) |
| `≥ floor · 1 of 2 priced` | **REAL** — `valued_count` / `depth_value_label`, but attached to the wrong quantity (11) |
| `Holes · None` | **REAL** — `lineup_optimizer.slot_coverage` (not `league_usable_positions`); tense unqualified (18) |
| `10 of 10` + Constructed | **REAL + correctly stamped** — `optimize_lineup` + `slots_from_roster_positions` |
| `Record · — absent` | **REAL absence, right reason** |
| `Pool 5,357` | **REAL** — `len(build_player_universe(...))`; mislabelled (20) |
| `League · — name not in this capture` | **REAL absence** |
| Quiet bye profile, Constructed | **declared constructed**; axis invented and undeclared (7) |
| Freshness grade + per-source ages | **REACHABLE**, omitted on a false premise (15) |
| Which starter sits in week 6 | **REACHABLE** — `roster[].bye == worst_week` ∩ `starters`, two lines |
| Material injuries on starters | **REACHABLE** on the constructed lineup; absence given the wrong reason (9) |
| Pick prices | **WITHHELD, correctly** — `estimate_future_pick_value`, 1.89-of-12 mean slot error |
| Anything about Questionable | **WITHHELD, correctly** — `is_material_injury_status` |
| Positional strength as a meter | **WITHHELD, correctly** — not drawn |
| `current_week` / futurity | **WITHHELD by the capture, and the page spends it anyway** (3) |
| "Bottom of this league at the position" ×4 | **FABRICATED** — and false (1) |
| `TE` shield on the bye summons | **FABRICATED** — week 6 is an RB (2) |
| "Every position is at or above its league peers" | **FABRICATED** — WR is Average at 0.969× (6) |
| "so no single week is worth a move" | **FABRICATED** — no such computation; and 19% is 19.3% (14) |
| `Seat 5` | **FABRICATED** — the fixture says 1 (12) |
| Door sub-line "pick counts" (Draft Room) | **FABRICATED** — no pick data in that view, no inventory in the engine (13) |
| Door sub-line "freshness" (Import Audit) | **FABRICATED** — not in that view (13) |
| Footer "the engine does not compute those" | **FABRICATED claim about the engine** — rating, grade and probability all exist (5) |
| Footer basis legend in the quiet state | **contradicts its own page** (4) |
| `1 of 1` | no referent in `front_claims` (17) |

---

## THE SINGLE MOST IMPORTANT CHANGE

**Delete "Bottom of this league at the position" and replace it with what `depth_label` actually
returns.** It is four words in four places. It is the only element on either page that is both
fabricated *and* false against the fixture the page draws from, it is checkable in twenty lines of
Python, and it is the claim a reader would most plausibly act on — the DEF version tells them
their joint-best-priced position room is their worst. Everything else on this page is a sentence
that needs tightening, a stamp that needs toggling or an axis that needs setting. That one is a
number-shaped lie in prose clothing, which is precisely the form this project's own doctrine was
written to catch, and it got through because the brief handed it over pre-approved.

The second most important is finding 3, and it is the harder one: with `current_week` ABSENT, the
gonfalon's urgency is unearned and the ladder's own justification for ranking bye above thin is
void. That is a design decision, not a copy edit.

## PLAIN VERDICT

**Worth refining — and it is the strongest sourcing discipline I have seen in this round.** It is
not close to shippable: twenty findings, five of them fabrications, two of them false against the
fixture. But the distribution of those failures matters. The hard parts are right. The bye
engine's numbers are exact, in the engine's own words, with the right axis and no floor marker
where none belongs. The absence grammar has four visually distinct states and no bare `0` anywhere
in either file. Severity-by-frame-shape genuinely does keep every hue free for the position
tokens, and it means a greyscale print still ranks the claims — that idea survives attack
completely and should be lifted into the rewrite regardless of what happens to this page.

What failed is almost entirely **prose written past the number**. "Bottom of this league",
"at or above its league peers", "worth a move", "read off a live roster only", "the engine does not
compute those" — five sentences, each one a confident gloss a step beyond what the function beside
it returns. That is a correctable habit, not a broken design, and nothing on the fix list costs
this page anything it should want to keep except the two real trades: the mobile ledger's missing
rows (finding 8) and the gonfalon's unearned urgency (finding 3).

One standing caution. The page's authority is that it tells you what its own numbers are, and that
makes every basis assertion on it load-bearing in a way an ordinary dashboard's are not. Three of
this page's wrong claims are *claims about its own honesty* — the non-toggling legend, the
"no grade, no rating, no probability" footer, and the mobile legend that omits two absences it
drops. A page that is wrong about a bye week has a bug. A page that is wrong about what it can
know has a credibility problem, and it has one in the quiet state, which is the state most weeks
will show.
