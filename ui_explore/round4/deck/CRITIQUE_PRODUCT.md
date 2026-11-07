# The Deck — PRODUCT adversary

**Question:** does every displayed element represent something CDME can actually calculate or
retrieve?

**Scope:** `desktop.html` and `mobile.html`, both files, **both** `review` states (`live` and
`quiet`). Verified against source, not against `BRIEF.md`. Where a number needed checking I
re-ran the engine rather than trusting `NOTES.md` — the depth recompute, the league-wide depth
chart, the pricing coverage and the injury feed were all executed against the real capture on
python3.13 (pandas lives in `/usr/local/lib/python3.13/dist-packages`, not on the default
`python3`).

Verdict key: **REAL** (a named function returns it today) · **REACHABLE** (data exists, nothing
computes/persists it) · **WITHHELD** (engine can and deliberately does not — ruling named) ·
**FABRICATED** (no basis; a defect).

---

## READ THIS FIRST — `BRIEF.md`'s Real/Forbidden table is wrong in two places

You asked to be told. Both errors are in the **Real** table, both in the over-claiming
direction, and one of them is also wrong in the fixture itself.

### B1. "structural holes … set difference against `league_usable_positions`" — wrong function

`capture_front_fixture.py` does not use `league_usable_positions` and says at length why not:

```python
# A HOLE IS A SLOT THE SOLVER LEAVES EMPTY, not a position missing from a free-agent
# filter. league_usable_positions EXPANDS flex slots -- its docstring says so, because its
# job is "never suggest a free agent in a position with nowhere to start him" -- and it
# falls back to EVERY known position on empty roster_positions. Both behaviours are right
# for that job and wrong for this one: in a standard FLEX league with no dedicated TE slot
# it reports TE as a slot nobody can fill, and on a malformed league it reports all nine.
# slot_coverage answers the counting question directly and takes no `value` by design.
slots = lo.slots_from_roster_positions(roster_positions)
cover = lo.slot_coverage(mine, slots)
```

The producing function is **`lineup_optimizer.slot_coverage`** (over
`slots_from_roster_positions`). `player_universe.league_usable_positions` is a free-agent
filter whose own docstring confirms the expand-and-fallback behaviour. Using it would
manufacture holes in standard FLEX leagues.

**This is worse than a brief typo:** `front_fixture.json`'s own provenance carries the same
wrong attribution, three lines below the code that rejects it —

```json
"structural_holes": "measured -- league_usable_positions vs the roster"
```

A surface that does what this review asks (cite the function) would cite the wrong one off the
fixture's own basis string. **Fix the fixture string, then the brief.** The Deck dodges this by
stamping holes `measured` without naming a call — honest by omission, not by design.

### B2. "which future picks you own … `pick_ledger.build_pick_ledger`" — not what it returns

```
Sleeper only lists a pick here once it's actually moved from its original roster; an
untouched pick is assumed to still belong to its original roster and isn't worth listing,
so this ledger is deliberately just the diffs, not a full inventory of every hypothetical
future pick.
```

`build_pick_ledger` returns `roster_id -> {"acquired", "given_away"}` — **the diffs**, not
ownership. "Which future picks you own" is not computable from it. The Deck got this right and
the brief did not: the desktop strip is `Acquired` / `Sent away`, and `NOTES.md` states
"`build_pick_ledger` is diffs-only". The design beat the summary. (It then spends that credit
in finding 11.)

Everything else in the Real table held under test, including `depth_label`'s four labels and
`recency_grade`'s 7/30/90 bands.

---

## Findings, most severe first

---

### 1. The headline asserts an urgency the engine explicitly forbids without a current week — WITHHELD, violated

**Where** — `desktop.html:241-242`, `mobile.html:223-224`. The `<h1>`: **"One thing needs
you."** and the sentence beneath: "**Week 6** costs **95** … and one starter sits." Present in
the `live` state of both files. The `1 NEEDS YOU` tally cell (`desktop.html:252`,
`mobile.html:225`) and the hot gold WK 6 row are the same claim.

**What is wrong** — the bye rung's entire justification is *futurity*, and `front_claims` rules
that a bye claim which cannot establish futurity **must not borrow the urgency**. This fixture
cannot establish it: `current_week` is `null`. The page takes the urgency anyway, in the one
element the three-second test is about.

**The evidence** — `front_claims.LADDER` and `front_claims.byes_ahead`:

```python
("bye",    "a known future week with a measured cost, and planning only works in advance"),
```

```python
def byes_ahead(bye_profile, current_week):
    """...
    THE RUNG'S REASON IS FUTURITY, so a claim that cannot establish futurity must not borrow
    the urgency. With a known current week this re-picks the worst week from those at or
    after it; with none, the same numbers are a season-shape fact and the caller says that
    instead of implying a deadline. The first version of the page had no concept of now and
    would happily have put a week already played second on the band -- the one thing a triage
    surface must never do, because it spends the reader's trust in every other claim on it.
    """
    if current_week is None:
        return bp          # <- no _ahead_only flag; compose() then sets ahead_only=False
```

`compose()` ships `"ahead_only": bool(bp.get("_ahead_only"))` precisely so the surface can say
"season shape" instead of "deadline". On this fixture that flag is `False`.

`front_fixture.json` is unambiguous about why:

```json
"current_week": "ABSENT -- a replayed draft has no point in the season. A live league reads
season/week from Sleeper's NFL state; without it the bye claim cannot assert that a week is
still ahead"
```

And `capture_front_fixture.py` wrote that in capitals: *"WITHOUT THIS, THE BYE CLAIM CAN NAME A
WEEK ALREADY PLAYED … the page could rank a dead week second-highest."*

This is not a pedantic point. If the real current week is 12, week 6 is gone, the correct
headline is "Nothing needs you", and the page has put a dead week at 30px in Cinzel gold. The
`1 · 2 · 5` split is also downstream of it: the only thing separating "NEEDS YOU" from
"STANDING" is the LADDER's own distinction between a deadline and "a standing weakness with no
deadline attached" — remove futurity and all three claims are standing, and the honest verdict
is *"Nothing needs you. Three things stand."*

**Desktop discloses the dependency 1,300px below the headline** (`Current week —` in the absence
strip). **Mobile does not disclose it at all** — the mobile strip is four cells, `W – L / Pts
for / Pts agst / Picks` (`mobile.html:320-324`, confirmed by render). So on the phone the page
asserts a deadline and never mentions that it cannot know whether the deadline has passed.

**Cost to fix** — small, and it does not cost the design anything worth having. Two states for
the bye claim, keyed on `ahead_only`:
- `ahead_only=True` → today's page, unchanged.
- `ahead_only=False` → headline becomes a count of *standing* claims ("Three things stand"), the
  bye panel's eyebrow reads "season shape, not a deadline — no current week on file", and the
  hot-row treatment moves from "urgent" to "largest". Add `Current week —` to the mobile strip.

The quiet state has the same dependency ("the worst bye week carries only 19%" →
`desktop.html:247`) and the same fix.

---

### 2. "Bottom of this league at the position" is fabricated, and for DEF it is backwards — FABRICATED

**Where** — `desktop.html:307` ("**Bottom of this league at the position.**") and `:308`
("**Bottom of this league.**"); `mobile.html:273` and `:276` ("**bottom of league**"). These two
sentences are the entire *why* under both Standing claims — the only justification the page
gives for its second-tier urgency.

**What is wrong** — it is an **ordinal rank**. `depth_ratings.depth_label` returns four
categorical labels and nothing else; no function in the tree returns a league rank at a
position. The claim is also **false on every measure the engine has**, and for DEF it is
inverted.

**The evidence** — I ran `depth_chart.positional_depth` over all twelve teams on this exact
seat/format/strategy:

```
--- DEF across the 12 teams ---                  --- TE across the 12 teams ---
  Team 4    bodies=1 value=1.0                     Team 4    bodies=2 value=10.0
  Team 5    bodies=1 value=2.0                     Team 5    bodies=2 value=15.0
  Team 2    bodies=1 value=4.0                     Team 1    bodies=2 value=23.0  <== THE SEAT
  Team 12   bodies=1 value=7.0                     Team 8    bodies=2 value=25.0
  Team 1    bodies=1 value=9.0  <== THE SEAT       Team 6    bodies=2 value=37.0
  Team 9/10/11  bodies=2 value=None                Team 11   bodies=2 value=38.0
  Team 8    bodies=2 value=0.0                     Team 3    bodies=2 value=50.0
  Team 3    bodies=2 value=6.0                     Team 12   bodies=2 value=68.0
  Team 6    bodies=2 value=7.0                     Team 7/10/9  bodies=3
  Team 7    bodies=2 value=9.0                     Team 2    bodies=7 value=59.0
```

- **DEF, on bodies:** Team 1 is in a **five-way tie** for lowest (Teams 2, 4, 5, 12). *Nobody is
  below it and four teams are level with it.* "Bottom" asserts a unique last place that does not
  exist.
- **DEF, on value — the only quality measure the engine has:** Team 1's 9.0 is the **joint
  highest priced DEF room in the league**. Seven of the nine priced rooms are strictly below it;
  **none is above.** The page prints `1 · 9` in the ladder row two panels away and the prose
  beside it says "bottom of this league".
- **TE, on bodies:** an **eight-way tie** at 2; nobody below.
- **TE, on value:** 23.0 is **third lowest of twelve** — Team 4 (10) and Team 5 (15) are below
  it. And 23 is a *floor* (`1 of 2 priced`), so the true figure is `≥23`, which can only move it
  further from the bottom.

The `Weak` labels themselves are **REAL** and correctly drawn (DEF body ratio 0.6316 ≤ 0.7, TE
value ratio 0.5872 ≤ 0.7 — both reproduced exactly). It is only the rank prose that is invented,
and it is the part a reader will act on.

**Cost to fix** — near zero, and it makes the claims *stronger*. The engine gives you the real
comparison for free: `depth_ratings`'s own thresholds and `positional_depth`'s peer cells.
Replace with what is true and checkable:

> **DEF · Thin · 1 rostered** — one of five teams with a single DEF, against a league average
> of 1.6 bodies. One injury or a bye is an empty slot; week 8 is the Texans' bye.
>
> **TE · Thin · 2 rostered · ≥23** — ≥23 against a league average of 39 at the position. Only
> Pitts could be priced, so the room's value is a floor, not a total.

If you want a rank, it is **REACHABLE** — `positional_depth` already holds every team's cell —
but it must be a rank *with its ties and its basis* ("tied 8th-equal on bodies"), and it must
say which measure it ranks on, because for DEF the two measures disagree completely.

---

### 3. The seat's one real lineup problem is drawn as "not measured", with a false reason — REAL, suppressed; the reason is FABRICATED

**Where** — `desktop.html:374`: "Material injuries on starters — **—** *no live injury feed for
a replayed seat*". `mobile.html:304`: "Lineup 10/10 · injuries **—** *no feed*", inside a row
with a green check. And in the `quiet` state of both files, the cleared list asserts "**Material
injuries on starters: none**" (`constructed`).

**What is wrong** — three things, compounding:
1. The reason is **false**. The injury feed is in the capture this fixture was built from.
2. The quantity is **computable today** from that capture.
3. The answer is **not "none"** — it is **one, and he is in the lineup the page draws**.

**The evidence** — `data/fixtures/sleeper_capture.json` carries `injury_status` on 494 of its
6,595 players:

```
injury statuses: [(None, 6101), ('Questionable', 290), ('IR', 126), ('NA', 46),
                  ('PUP', 21), ('Sus', 8), ('DNR', 2), ('Out', 1)]
```

`run_draft_battery.build_players_db_from_capture`'s docstring names it as a reason that function
exists: *"it has to draft from the universe the engine actually gets: **injury_status**,
fantasy_positions, years_exp, status and team, per player, exactly the fields
build_available_pool reads."* `player_universe.py:442` then emits `"injury_status":
info.get("injury_status")` onto every universe row.

Joining the capture's statuses to this fixture's own `starters` array:

```
STARTER Jayden Higgins        WR   inj='IR'            <- material
STARTER Wan'Dale Robinson     WR   inj='Questionable'  <- correctly immaterial
(the other 14 rostered players: inj=None)
```

`player_universe.is_material_injury_status('IR')` → `True` (verified; `IMMATERIAL_INJURY_STATUSES
= ("Questionable",)`). So `lineup_readiness.compute_readiness`'s `starter_injury_flags` on this
seat returns **exactly one flag: Jayden Higgins, WR, IR** — and the only input it still needs,
`slot`, is the thing `capture_front_fixture.py` already constructs with `optimize_lineup`.

Higgins is on this page **three times**: the FLEX slot at `desktop.html:366` (`Higgins · 21`),
the WK 8 bye row as a starter (`desktop.html:276`), and the mobile chip row
(`mobile.html:305`). The page knows about him as an asset and renders him as healthy.

Credit where it is due: **Robinson being absent is correct.** `compute_readiness` deliberately
excludes `Questionable` (*"A Questionable starter is not a lineup problem, and raising him as one
spends a person's attention on a designation the engine has measured as carrying nothing"*), and
the page does not surface him. The grammar works — it was pointed at the wrong fact.

**This is the single most dangerous element on the page**, because it is the inverse of
fabrication and therefore invisible to a "did you invent a number" review: a *real, material,
actionable* finding suppressed behind a reassuring absence with a reason that is not true.
`front_page.split_reason` rules on exactly this: *"a wrong reason reads as reassurance, which is
worse than a clumsy one."*

**Cost to fix** — about four lines in `capture_front_fixture.py` (carry `injury_status` into
`mine`, build the `roster_table` shape `compute_readiness` wants from the constructed `starters`
set, call it, write `starter_injury_flags`). The design already has the slot to render it and the
CLEARED→claim machinery to rank it. It will change the verdict: the live tally becomes at least
`2 NEEDS YOU`, and the quiet state must not claim "none" from a check it did not run.

---

### 4. "Every row below was measured and cleared" — false in both states; six of eight quiet rows are constructed — basis collapse

**Where** — `desktop.html:247` (quiet verdict): "**Every row below was measured and cleared.**"
And `desktop.html:242` (live verdict): "**Everything else was measured and cleared.**" Both sit
inside the verdict band, the most prominent prose on the page.

**What is wrong** — the sentence asserts a basis the rows below it contradict. The design's own
component rule (`NOTES.md` #4) is that the four states "must be distinguishable at a glance and
no value may appear without one"; the verdict then collapses all of them into "measured" one
line above the stamps.

**The evidence** — rendered, reading the visible `.b` stamps in each state:

| | visible cleared rows | stamps |
|---|---|---|
| desktop live | 5 | measured, measured, measured, **constructed**, measured |
| desktop quiet | 8 | measured, **constructed ×3**, measured, **constructed ×3** |
| mobile live | 5 | measured ×4, **constructed** |
| mobile quiet | 6 | measured, **constructed ×2**, measured, **constructed ×2** |

So the quiet verdict's "every row below was measured" is true of **two of eight** rows. The live
verdict's "everything else was measured" is true of **four of five**.

Worse, in the quiet state `desktop.html:310` escalates it to a totality claim: "**Every check the
engine ran on this seat is listed below with its basis.**" Six of those eight "checks" are
constructed — i.e. not checks the engine ran at all. The sentence asserts both completeness and
measurement, and has neither.

**Cost to fix** — a word. "Everything else was **cleared — see each row's basis**." Or, better
and barely longer: "Everything else cleared: **4 measured, 1 constructed**." That second version
*is* the design's best idea applied to its own summary line, and it costs nothing.

---

### 5. The CLEARED tally is editorial, not measured — and the two files disagree about it — invented denominator

**Where** — the `5 CLEARED` / `8 CLEARED` tally cell, `desktop.html:254` and `:259`;
`mobile.html:225` and the quiet prose `mobile.html:230` ("**6** cleared below").

**What is wrong** — the tally is drawn at 30px mono beside two counts that *are* real
(`1 NEEDS YOU` = the bye claim, `2 STANDING` = `len(thin_positions)`, both straight out of
`front_claims.compose`). The third number has no producer. `compose()` returns
`{"shown", "hidden", "bye_profile"}` — **there is no cleared list, no check inventory, and no
count of passed checks anywhere in the engine.** The number is however many negatives the
designer chose to draw.

**The evidence** — the same `quiet` state reports a different number on each file:

```
desktop.html [quiet]  ->  8 CLEARED
mobile.html  [quiet]  ->  6 cleared below
```

(Rendered. Desktop quiet carries two extra rows — "Picks: every original round still held" and
"Thin positions: none" — that mobile drops for space.) A quantity that changes when the viewport
changes is not a measurement. Put beside `1` and `2`, which *are* measurements, it reads as one.

**Cost to fix** — either (a) drop the third cell and let the cleared list be a list, which costs
the tally its visual rhythm and nothing else; or (b) make the inventory real — define the set of
checks in `front_claims` (`CHECKS_RUN`, alongside `RUNGS_PRODUCED_HERE`, which already exists to
pin exactly this kind of known gap) and have both surfaces render all of them. (b) is the better
product and is genuinely REACHABLE; (a) is today's honest answer.

---

### 6. "5,357 players priced in the pool" — 347 are priced — FABRICATED

**Where** — `desktop.html:389`, the Data Age panel's closing basis line: "measured ·
build_freshness_manifest · **5,357** players priced in the pool".

**What is wrong** — `5,357` is **REAL** (`_provenance.universe_rows`, verified: my own run
returned `universe rows=5357`). The word **"priced"** is fabricated, and it is wrong by 15×.

**The evidence** — measured on the same universe, calling `merger.merge_player` per row:

```
universe rows=5357   rows with a trade_value=347 (6.5%)
ROSTERED rows=192    of which priced=169
```

Six and a half percent of the pool carries a price. The page's own ladder proves it two panels
over — `K  2 · — 0 of 2` and `TE 2 · ≥23 1 of 2`. Partial pricing coverage is the exact thing
`depth_chart.depth_value_label` and #190 exist to surface: *"a reader who takes `value` for the
room's total is reading a floor as a sum."* This line asserts the opposite, globally.

Two lesser problems in the same sentence: `build_freshness_manifest` returns
`(label, as_of, days)` tuples and knows nothing about pool size, so the stamp names a function
that cannot produce the number it qualifies; and the sentence picks the big number (5,357, the
pool) with the reassuring adjective (priced, which describes 347).

**Cost to fix** — one word out, or two numbers in: "**5,357** in the pool · **347** priced". The
second is better — it is the honest coverage figure and nothing else on the page carries it.

---

### 7. The `×LG` ratio column — REACHABLE, not REAL; `·n` is not honest about the fallback; delete it

You asked for a ruling. Here it is, in four parts. **The designer was right to flag it and the
column should go.**

**Where** — `desktop.html:331-341` and `mobile.html:267-276`, the `×lg` column: `1.02`, `1.14`,
`0.97`, `0.59`, `1.20·n`, `0.63·n`.

#### 7a. It is REACHABLE, not REAL

`depth_ratings.depth_label` computes `ratio` and **throws it away**:

```python
use_value = cell["value"] is not None and all(c["value"] is not None for c in peer_cells)
avg = (sum(c["value"] for c in peer_cells) if use_value else sum(c["count"] for c in peer_cells)) / len(peer_cells)
if not avg:
    return None
ratio = (cell["value"] if use_value else cell["count"]) / avg
return STRONG if ratio >= _STRONG_RATIO else WEAK if ratio <= _WEAK_RATIO else AVERAGE
```

It is a local. No function in the tree returns it; no consumer can read it. `NOTES.md` says "that
ratio is exactly what `depth_label` computes before it thresholds" — true, and not the same as
"returns". Exposing it is a one-line change, so the gap is small, but the verdict is REACHABLE.

More to the point, `depth_ratings` binds its output vocabulary deliberately:

```python
#: Every label depth_label can return. None is NOT in here on purpose -- it is the absence
#: state ("cannot be measured"), not a rating, and a consumer that maps it to a rating is the
#: defect this vocabulary exists to make visible.
LABELS = (STRONG, AVERAGE, WEAK, NO_PLAYERS_LABEL)
```

The ratio is not in `LABELS` because the module's position is that the four labels are the
product.

#### 7b. The thresholds it is printed against were never validated

Module header: *"Thresholds are unchanged from the original -- **relocated, not re-derived or
re-validated**."* And at the constants: *"Not re-tuned here."* So the scale has exactly two
calibration points, both inherited un-checked. Printing three significant figures against it
asserts a resolution nothing in the repo supports. `0.97` (WR) and `1.02` (QB) are the same
label; in a column built for scanning they read as a ranking of two rooms the engine declines to
separate. That is the precision-overclaim shape, and it is the one the brief names.

#### 7c. The `·n` suffix is dishonest about the fallback — three ways

I verified what the fallback actually is, and it is **not** "nobody in this room is priced":

```
DEF  | n=1 v=9.0 vc=1 | Weak    | 0.6316 | use_value=False | avg=1.5833(bodies)
       teams with value=None: 3 of 12   (Teams 9, 10, 11)
K    | n=2 v=None vc=0 | Average | 1.2000 | use_value=False | avg=1.6667(bodies)
       teams with value=None: 4 of 12
```

- **The trigger is the peer set, not this room.** `all(c["value"] is not None for c in
  peer_cells)` — one unpriced peer out of twelve flips the whole row to body counts. On the DEF
  row **Team 1's own room is fully priced** (`value=9.0`, `valued_count=1` of `count=1` — a
  complete total, not a floor). The ratio is on bodies because *three other teams* have no
  priced DEF. `·n (on bodies)` tells the reader nothing about that, and the one place it is
  explained is the desktop footnote; **mobile's footnote says only "`·n` on bodies"**
  (`mobile.html:287`) and never mentions peers at all.
- **It marks the ratio but not the label.** The desktop footnote states: *"The label is the
  room's priced value against the league average at that position."* **That is false for the two
  `·n` rows** — their labels came from body counts. One of them (DEF, `Weak`) drives a Standing
  claim. So the page's explanation of its own rule is wrong exactly where the rule bends, and
  wrong in the direction that makes a body-count judgment look like a value judgment.
- **It is a unit change rendered as a footnote marker.** `K 1.20` (bodies) sits directly under
  `QB 1.02` (trade-value points) in one column. `1.20 > 1.02` means nothing. The table's whole
  affordance is reading down the column; two characters of superscript do not suspend that.

The **DEF row is the proof of harm**: `1 · 9` (a complete priced total) + `0.63·n` (a body
ratio) + `Weak` (decided on bodies) — three bases in one row, disambiguated by two characters,
and then narrated in prose as "bottom of this league" (finding 2) when on value it is top of the
league. `depth_chart.positional_depth`'s own docstring is the warning: *"Count alone treats a
pile of backups the same as three stacked stars at the same position -- real depth is about
quality, not just bodies."*

#### 7d. The quiet ladder's own ratios break the rule printed beneath them

The footnote says the comparison is the room's value against the league average, and
`depth_label`'s `avg` includes the team's own cell (*"average over every team, self included"*).
Apply that rule to the quiet state's own numbers:

| quiet row | page shows | the stated rule gives | what the designer actually divided by |
|---|---|---|---|
| RB `4 · 171` | **1.42** | 171 / 123.42 = **1.39** | the *live* average 120.58 |
| TE `2 · 38` | **0.97** | 38 / 40.42 = **0.94** | the *live* average 39.17 |
| DEF `2` bodies | **1.27** | 2 / 1.667 = **1.20** | the *live* average 1.5833 |

Three of six quiet ratios do not follow the rule one line below them, because changing the
seat's own cell changes the denominator and the hand-computation did not. The panel is stamped
`constructed`, which covers "these numbers are made up" — it does not cover "these numbers are
made up in a way that contradicts the formula beside them". This is the argument for deletion
stated as evidence: **a continuous number that must be hand-maintained has already been got
wrong, in the state where nobody would check it.**

#### Ruling

Printing the ratio tells the reader something true about the *computation* and something false
about the *resolution*. The four labels are not a rounding of the ratio for want of precision —
they are the claim, with a bound vocabulary and an un-validated two-point scale behind them. The
ratio implies a resolution the labels deliberately refuse, and the `·n` notation is not honest
about the fallback it marks (it names the wrong cause, omits that the *label* fell back too, and
silently changes units mid-column).

**Delete the column.** The ladder stands without it, as `NOTES.md` says. If the owner's "why" has
to be answered — and it should be — answer it in the units the engine already holds, with no
derived quantity and no unit switch:

| pos | bodies · priced | league | | | | |
|---|---|---|---|---|---|---|
| TE | 2 · ≥23 | 2 · 39 | — | ● | — | — |
| DEF | 1 · 9 | 1.6 bodies | — | ● | — | — |

Two real numbers side by side say "my TE room is worth 23 against a typical 39" better than
`0.59` does, they cannot change units without the reader seeing it, and the DEF row then shows
its own basis honestly (bodies compared to bodies) instead of printing a value and a body ratio
as if they were one judgment.

**Cost of keeping it instead:** one line in `depth_ratings` to return `{"label", "ratio",
"basis"}` so nothing hand-computes it, `·n` replaced by an explicit basis column ("on value" /
"on bodies, n peers unpriced"), the footnote corrected to say the *label* falls back too, and the
quiet state regenerated from the function. That is more work than deleting it and buys a number
the four labels already cover.

---

### 8. The week-6 attribution sentence — the engine has a named ruling against it, and the fixture lets you check it for exactly one week

You called this the most important call in the review. It is the subtlest, and the honest answer
cuts both ways.

**Where** — `desktop.html:273`: "**RB room is two deep for two RB slots: nothing backfills him,
so his whole price is the loss.**" `mobile.html:239`: "**RB room 2 deep: no backfill.**"

**First, what `bye_collision` does and does not attribute.** It returns, per week:
`value_lost`, `lineup_value`, `players_out`, `starters_out`, `bench_used`, `bench_value_used`,
`basis`. **There is no per-player field.** And the refusal is deliberate and argued:

```python
# NO DEPTH RANK IS REPORTED, and the reason is worth keeping. Two were built and both were
# wrong, because FLEX substitution makes "how far down the bench" ill-defined:
#
#   A WR goes out. The naive reading promotes the best bench WR. What the solver actually
#   does -- verified on a real fixture -- is slide the WR already in FLEX up into the WR
#   slot and drop a BENCH RB into the vacated FLEX. The hole at WR was covered by an RB,
#   through a chain, and it cost 5 instead of the 16 the naive reading predicts.
#
# Both are plausible numbers with no sound definition behind them.
# What survives contact is the COUNT of bodies consumed and their total value, neither of
# which depends on routing. value_lost already carries the exact cost, chain included.
```

**That is the ruling: the engine reports the week's cost and the bodies consumed, and refuses any
per-player routing story, because substitution chains make the attribution undefined.** "His
whole price is the loss" is a routing story.

**Second, in fairness: on this week the sentence is defensible, clause by clause.**

| clause | verdict |
|---|---|
| "RB room is two deep" | **REAL** — `positional_depth` cell `count=2` |
| "for two RB slots" | **REAL** — fixture `league.roster_positions` = `[QB, RB, RB, WR, WR, TE, FLEX, FLEX, …]` |
| "nothing backfills him" | **REAL-adjacent** — `worst_week_detail.bench_used: 0`, `bench_value_used: 0` |
| "so his whole price is the loss" | the inference. `value_lost: 95.0` = Gibbs's `value: 95.0`, with `players_out: 1`, `starters_out: 1`, `bench_used: 0` |

I re-derived the solve: starters total 315, week 6 removes Gibbs, no RB-eligible body remains, the
RB slot goes empty, `lineup_value` 220, loss 95. The arithmetic holds and every input is in the
fixture. **This is not a fabricated number.**

**Third, and this is the finding: it is a template with no producer, and the one week it can be
checked is the only week the fixture lets you check.** `capture_front_fixture.py` persists
`worst_week_detail` for the worst week only —

```python
"worst_week_detail": weeks.get(shape.get("worst_week")) if shape.get("worst_week") else None
```

— so `bench_used` exists for week 6 and for **no other week in the same table**. Apply the same
sentence to its neighbours, which a production renderer would have to do, and it fails:

| week | out | their combined value | `value_lost` | the sentence |
|---|---|---|---|---|
| 6 | Gibbs | 95 | **95** | true |
| 9 | Robinson | 20 | **4** | **false by 5×** — a bench WR (Doubs, 16) backfilled the FLEX |
| 7 | four bodies | 38 | **8** | false |
| 10 | three bodies | 86 | **56** | false |
| 11 | four bodies | 54 | **23** | false |

`NOTES.md` flags "the verdict copy is hand-written" as a known weakness but does **not** flag this
sentence — and this is the more dangerous of the two, because it is a *causal* claim rather than
a summary, it is attached to the brightest row on the page, and it would be generated from a
template on a live league.

**What survives, and should be kept.** The row ledger's core decision is correct and is the best
thing on the page: the bar is `value_lost`, the names are bodies, **both are shown**, and the
header says so ("lineup re-solved with each week's byes removed · **value lost, not bodies**").
Week 9 — `Robinson 20` beside a bar of `4` — is the non-additivity made visible, which is
precisely what `bye_collision`'s docstring says a headcount cannot express. The legend naming
"Draft Sharks trade value · — unpriced" is right, and the unpriced players really do render as
`—` (verified: `Bass`, `Knox`, `Borregales` all have `trade_value = None`; the fixture collapses
them to `0.0` via `priced.get("trade_value") or 0.0` and **the design correctly refuses to print
that zero**, which is the absence-grammar working under pressure).

**Cost to fix** — replace the hand-written causal clause with the engine's own three numbers,
which are real, per-week, and already explain the gap:

> **WK 6** · 95 · Gibbs (95) — **1 of 1 out started · 0 bench promoted**
> **WK 9** · 4 · Robinson (20) — **1 of 1 out started · 1 bench promoted, 16**

That is `starters_out`, `players_out`, `bench_used` and `bench_value_used`, which
`bye_collision` returns for every week, and it says "nothing backfilled him" without claiming to
know *why*. It needs `capture_front_fixture.py` to persist `weeks` as the full per-week dicts
rather than only the loss figures plus one detail — about three lines, and it is a fixture gap
worth closing regardless, because today the design's only basis for its one causal sentence is a
field that exists for one row in six.

---

### 9. The six-row depth ladder — REAL, verified, and the designer's claim holds exactly

You asked for a ruling on this too, and it is a pass. I state it as a finding because the
distinction you asked about (REAL vs REACHABLE) changes what shipping costs.

**The claim under test** (`NOTES.md`): *"The fixture retains only the two thin rows; I ran the
fixture's own loop (`capture_front_fixture.py` lines 95–116) unfiltered in a scratch script …
Same code path, same seat."*

**Both halves verify.** The filter is real:

```python
label = depth_ratings.depth_label(depth[me][position], peers)
if label in depth_ratings.THIN_LABELS:
    ...
    thin.append({...})
```

`THIN_LABELS = (WEAK, NO_PLAYERS_LABEL)`, so `Average` and `Strong` rows are dropped and
`front_fixture.json`'s `thin_positions` holds only DEF and TE. And the recompute is correct — I
ran the loop unfiltered myself, on the same format/strategy/seat:

| pos | bodies | value | valued | ratio | basis | label | page shows |
|---|---|---|---|---|---|---|---|
| QB | 2 | 44.0 | 2 | 1.0173 | value | Average | `2 · 44` `1.02` Avg ✓ |
| RB | 2 | 137.0 | 2 | 1.1361 | value | Average | `2 · 137` `1.14` Avg ✓ |
| WR | 7 | 162.0 | 7 | 0.9686 | value | Average | `7 · 162` `0.97` Avg ✓ |
| TE | 2 | 23.0 | 1 | 0.5872 | value | Weak | `2 · ≥23 1 of 2` `0.59` Weak ✓ |
| K | 2 | None | 0 | 1.2000 | **bodies** | Average | `2 · — 0 of 2` `1.20·n` Avg ✓ |
| DEF | 1 | 9.0 | 1 | 0.6316 | **bodies** | Weak | `1 · 9` `0.63·n` Weak ✓ |

Every label, body count, value, floor marker, `n of m` coverage figure and ratio on the live
ladder is exactly what the engine returns. `depth_value_label(TE cell)` returns
`" (>=23, 1 of 2 priced)"` and the page draws `≥23 · 1 of 2`. This is the most thoroughly
correct panel in the deck, the `×LG` column excepted.

**Ruling: REAL.** `depth_chart.positional_depth` + `depth_ratings.depth_label` return all six
labels today, for any position, and I executed them to confirm. The gap is **persistence, not
computation** — `capture_front_fixture.py` discards four of six rows.

**Cost to ship:** about six lines, and `NOTES.md` already specifies them correctly ("the fixture
should retain `label`, `count`, `value`, `valued_count` for every position"). Move the `thin`
append outside the `if`, keep a `thin` flag on each row. No engine work, no new quantity, no new
ruling needed. This is the cheapest item in the whole review and it unblocks the ladder, the
"four positions at league-average" cleared row, and any future League Depth Map reuse.

---

### 10. The freshness panel collapses the split `front_page` exists to enforce, and both its absence reasons are wrong

**Where** — `desktop.html:381-389`, the Data Age panel: three dated rows on the axis, then
`League sync —` *nothing synced for a replayed seat* and `Season proj. sums —` *coverage not
carried by this fixture*, in the same list with the same label column. `mobile.html:317` merges
both into one dash: "`—` *sync, proj. sums: replayed seat*".

**What is wrong** — three separate things.

**(a) The structure is the one `front_page` was written to prevent.** Its module docstring:

```
THE SPLIT ITSELF, which is the whole design decision. The manifest returns four rows and two
of them are absent, but the two absences do NOT mean the same thing as the two ages:
  * `Draft Sharks *` are ON DISK NOW. An age is a judgement about them -- 76 days is Aging.
  * The two `Sleeper *` rows are absent because nothing has been synced yet. That is the
    EXPECTED state of a machine with no league, not a deficiency.
So they sort into `have` and `on_sync` rather than into one list with holes in it. A page that
rendered all four as one table with two dashes would make the second pair look like damage.
```

`compose_unsynced` returns `have` and `on_sync` as **two separate lists**. The Deck renders one
table with two dashes — verbatim the rendering that docstring rules against. Mobile is worse: it
merges the two absences into a single dash under a single reason.

**(b) "coverage not carried by this fixture" is false, and the row can never have a day-age
anyway.** The capture carries complete coverage:

```
season_projection_coverage = {"weeks_answered": [1..18], "weeks_failed": [], "weeks_requested": 18}
```

18 of 18. And `capture_front_fixture.py` literally loads it (`rdb.season_projections_from_capture()`).
So a **real and reassuring** value — full-season coverage — is drawn as an absence. Separately,
`sleeper_client.season_projection_freshness_entry` rules that this row's days column is `None`
*by design*: *"THE DATE IS THE SEASON ASKED FOR, not a fetch time … The days column is None for
the same reason: there is no per-day staleness to report, and a fabricated 0 there would sort
this row above inputs that genuinely are current today."* Drawing it as a dash *on a days axis*
frames it as "an age we happen to be missing" when it will never have one; its completeness is
weeks-of-18, which is a different axis.

**(c) The league-sync reason paraphrases away the engine's own.** `players_freshness_entry` and
`season_projection_freshness_entry` **write the reason into the label** after an em dash
("… — never fetched"), and `front_page.split_reason` exists solely to parse it back out, with the
rule: *"If the em dash ever goes away this returns the whole label as BOTH halves rather than
inventing a reason it does not have."* The page invents reasons instead of reading them.

**What is right here, and it is most of the panel.** The three ages are exact — I read them off
the live merger: `trade_values_freshest_date 2026-08-20 / 79d`, `freshest_date 2026-08-25 / 74d`,
capture `2026-09-07 / 61d`. The bands are real: `COMPOSITE_RECENCY_GRADES = [("Fresh", 7),
("Recent", 30), ("Aging", 90)]`. And "grade **Aging** · **oldest loaded** 79d" matches
`front_page`'s own basis string *word for word* — *"measured -- recency_grade over the oldest
LOADED source ({worst}d)"*, where `worst = max(ages)`. Someone read that function properly. The
axis is also the right form: days are genuinely continuous and the bands genuinely are the
meaning.

**Cost to fix** — small and it improves the panel: keep the axis for the three `have` rows, move
the two `on_sync` rows below a rule labelled "arrives with a sync" so they read as expected
rather than damaged, take each reason from the manifest label via `split_reason`, and render
season-projection coverage as what it is (`18 of 18 weeks` — a real, available, reassuring
number, and the only one on the page that currently shows as missing while being present).

---

### 11. "Picks: every original round still held, nothing moved" is a full inventory built from a diffs-only ledger

**Where** — `desktop.html:321`, quiet state, cleared list, stamped `constructed`.

**What is wrong** — `build_pick_ledger` is explicitly *"just the diffs, not a full inventory of
every hypothetical future pick"*, and *"an untouched pick is assumed to still belong to its
original roster and isn't worth listing."* "Every original round still held" is that
**assumption** restated as a measurement. Worse, an empty ledger cannot distinguish the three
states a reader cares about: no trades, no `traded_picks` key, no sync at all —
`build_pick_ledger({})` returns `{}` in all three. The quiet state renders that `{}` as a green
check.

Nothing in the tree knows how many future rounds a dynasty league's picks span, so "every
original round" also asserts a structure that has no producer.

**Cost to fix** — delete the row, or replace it with the diff the ledger can state:
"Picks: **0 acquired · 0 sent** — Sleeper lists a pick only once it has moved". The desktop
absence strip (`desktop.html:398`) already says this correctly, including the withholding —
*"a pick is only ever shown as held or sent, never priced"*, which matches
`estimate_future_pick_value` being *"wired to nothing but its own test"*. The cleared row
contradicts the strip four panels away.

---

### 12. The quiet state is not a coherent state: the Lineup panel is not gated and contradicts it

**Where** — `desktop.html:360` `<section class="panel" aria-label="Lineup">` carries no `l` or
`q` class, so it renders in **both** states. Same for the mobile chip row inside
`mobile.html:304`.

**What is wrong** — in the quiet state the page simultaneously asserts:

| quiet claim | quiet contradiction |
|---|---|
| ladder: `RB 4 · 171` (Strong) | Lineup/chips show exactly **2** RBs (Gibbs, Barkley) and a 6-man bench with no RB |
| cleared: "Material injuries on starters: **none**" | Lineup: "Material injuries on starters **—** *no live injury feed*" |
| cleared: "`QB · WR · TE · K · DEF` average, RB above" | Lineup shows the live seat's named players at live values |

Both contradictions were confirmed by render, in both files. `NOTES.md` justifies the shared
panels as *"properties of the machine, not the week"* — true of the freshness ages and the
record/pick absences, **not** of the roster. A lineup is the week.

The injury contradiction is the serious half: two rows of the same page, in the same state, say
"none" and "not measured" about the same quantity, and (per finding 3) the truth is "one".

**Cost to fix** — add `l` / `q` to the Lineup section and author a quiet lineup consistent with
the quiet ladder (4 RBs), or drop the Lineup panel from the quiet state entirely. Trivial.
Resolve the injury row once, per finding 3, and both copies follow.

---

### 13. Smaller things, each real

- **`mobile.html:328` — the `constructed` stamp is never legended on mobile.** The mobile footer
  key explains `measured`, `floor`, `absent` and `starter`. The desktop key has a fourth entry
  ("`constructed` built for this seat, not read from a league") and mobile drops it — while the
  stamp itself appears on mobile in the seat chip, the quiet bye totals, three cleared rows and
  the quiet ladder footnote. `NOTES.md` says the four-state grammar is *"the one I would keep if
  I could keep only one"*; on the phone it ships three-quarters legended, and the quarter missing
  is the one that marks a demo number. Add the entry.
- **`desktop.html:317` — "QB · RB · WR · K at league-average depth", stamped `measured`.** K's
  `Average` comes from the **body-count** fallback with `valued_count = 0` — the page's own
  ladder says `K 2 · — 0 of 2`. Calling a body-count tie "depth" is the elision
  `positional_depth`'s docstring warns about, and the same fallback basis produces a `measured`
  cleared check here (K) and an urgent Standing claim there (DEF) with nothing distinguishing
  either from the value-basis rows. Split the row: "QB · RB · WR at league-average value · K at
  league-average **bodies** (none priced)".
- **`desktop.html:404` — footer key calls `≥23` "a partial count".** It is a partial **value
  sum**, not a count. `depth_value_label` returns `" (>=23, 1 of 2 priced)"` — value, floored, with
  its coverage. One word: "a partial sum".
- **`×LG` denominator includes the team itself.** `depth_label`'s `avg` is over *"every team, self
  included"*, so `0.59` is not "59% of a typical rival's TE room" (peer-only: 0.566). For 12
  teams the gap is a few percent and no label changes, but a column headed `×LG` that a reader
  will quote should say which league it means. Moot if the column goes (finding 7).
- **`desktop.html:131` / `mobile.html:338` — `Matchup` marked `.here`.** The front page is not
  Matchup. `app.py` defines five segmented-control views plus The Prytaneum dock; Matchup is the
  `default`, so this is nearly right, but a front page that replaces the Streamlit layer is its
  own location and should not claim to be a destination it is not.
- **Quiet bars are scaled to the live state's maximum.** All six quiet bars are `value/95`
  (`41 → 43.2%`, `44 → 46.3%`), where 95 appears nowhere on the quiet page. Harmless because every
  bar is directly labelled and there is no axis — noted only so it is not mistaken for a scale.
- **`desktop.html:250-260` — in the quiet state the tally and `CLOSE THE APP` both render.**
  `NOTES.md` says *"the tally gives way to CLOSE THE APP"*; that is true on mobile and not on
  desktop (`.closebtn` is outside `.q`). Cosmetic, but it is how desktop quiet ends up showing
  `0 · 0 · 8` against mobile's `0 · 0 · 6` (finding 5).

---

## What survives attack

A review that returns "minor nits" has failed, and this one does not — but three things here are
genuinely better than the brief asked for, and they should be lifted out before any refinement
touches them.

1. **The bye row-ledger's core decision.** Bar = `value_lost`, names = bodies, both shown, header
   says which is which. Week 9 (`Robinson 20` beside a bar of `4`) renders non-additivity
   visibly — exactly what `bye_collision`'s docstring says a headcount cannot express — and the
   dashed line at `237/6 = 39.5` makes "40% in one week" a shape you can see rather than a
   statistic you must trust. The mean line is real arithmetic. Keep all of it; only the causal
   sentence (finding 8) has to go.

2. **Unpriced players render as `—`, including where the fixture hands the page a `0`.**
   `capture_front_fixture.py` writes `"value": priced.get("trade_value") or 0.0`, collapsing
   "unpriced" into "worth zero" — the exact defect the absence contract exists to stop, baked
   into the data. The design caught it: `Bass —`, `Knox —`, `Borregales —`, with a legend that
   names the convention, and `K 2 · — 0 of 2` in the ladder rather than `K 2 · 0`. That is the
   grammar working against the grain of its own input, which is the hardest test it gets. (The
   fixture should also be fixed: `priced.get("trade_value")`, no `or 0.0`.)

3. **The four-state grammar and the depth ladder's four discrete cells.** Four cells and never a
   meter, because `LABELS` has exactly four members and *"a fifth visual state would be a lie"* —
   correct, and correctly implemented. `≥` generated by CSS so a floor cannot be forgotten is a
   good mechanism, not just a good intention. Six doors and only the six that exist in `app.py`.
   `recency_grade`'s bands read off the real constant and the grade taken over the **oldest**
   loaded source, matching `front_page`'s basis string word for word. The pick strip naming its
   own withholding (*"never priced"*) rather than quietly omitting it. `Questionable` correctly
   absent while `compute_readiness`'s ruling is honoured.

The failures in this review are almost all of one kind, and it is worth naming: **this design
reads the engine's *quantities* carefully and its *rulings* carelessly.** Every number I checked
was right. Every place the engine had written down a rule about what may be *said* about a
number — futurity (1), per-player attribution (8), rank-vs-label (2), have/on_sync (10),
diffs-vs-inventory (11), reasons-not-paraphrases (3, 10) — the page crossed it. The prose is
where the fabrication lives, not the figures, which is why a numbers-only audit would have passed
this page.

---

## Verdict table

| element | verdict |
|---|---|
| bye damage per week, season total, worst-week share, starters out, unknown byes | **REAL** — `bye_collision` / `bye_concentration` |
| per-player names, byes, trade values in the who-column | **REAL** — fixture `roster`, from `DataMerger.merge_player` + `bye_week_by_team` |
| starter/bench marks on bye rows | **REAL** (constructed basis) — fixture `starters` from `optimize_lineup`; stamped |
| "nothing backfills him, so his whole price is the loss" | **WITHHELD** — `bye_collision`'s "NO DEPTH RANK IS REPORTED" ruling; true for wk 6, false for wks 7/9/10/11 |
| "One thing needs you" / week-6 urgency | **WITHHELD** — `front_claims.byes_ahead`; `current_week` is `null` |
| six depth labels, bodies, priced value, `≥` floor, `n of m` | **REAL** — `positional_depth` + `depth_label`; verified all six. Persisted nowhere (6-line fixture fix) |
| `×LG` ratio column | **REACHABLE** — a local in `depth_label`, returned by nothing; precision overclaim; `·n` misdescribes the fallback. **Delete** |
| "Bottom of this league at the position" | **FABRICATED** — no rank function; false on bodies (5-way / 8-way ties) and inverted on value for DEF |
| structural holes: none | **REAL** — `slot_coverage` (*not* `league_usable_positions`; brief and fixture both wrong) |
| lineup 10 of 10, slot grid, bench | **REAL** (constructed basis) — `optimize_lineup`; stamped |
| material injuries on starters | **REAL and suppressed** — `compute_readiness` + `is_material_injury_status` return **1** (Higgins, IR). Stated reason **FABRICATED** |
| three data ages, 7/30/90 bands, grade Aging, "oldest loaded" | **REAL** — `DataMerger` staleness + `COMPOSITE_RECENCY_GRADES` + `front_page`'s own basis |
| "5,357 players priced in the pool" | pool size **REAL**; **"priced" FABRICATED** — 347 of 5,357 (6.5%) |
| season-projection coverage absence | **REACHABLE** and present — capture holds 18 of 18; reason given is false |
| record / PF / PA / current week / picks absences | **REAL** absences — `team_standings`, `build_pick_ledger`, NFL state; reasons correct |
| "every original round still held, nothing moved" | **REACHABLE at best** — a diffs-only ledger cannot assert an inventory |
| `N CLEARED` tally | **FABRICATED denominator** — no check inventory exists; 8 on desktop vs 6 on mobile for the same state |
| "Every row below was measured and cleared" | **false** — 6 of 8 quiet rows stamped `constructed` |
| six doors | **REAL** — exactly `app.py`'s five views + The Prytaneum. No invented destinations |
| pool 5,357 | **REAL** — `_provenance.universe_rows` |

---

## The single most important change

**Fix the injury row (finding 3), and let it change the verdict.**

Not the ratio column — that one is a clean deletion the designer already offered. The injury row
is the one place where the page tells the reader "nothing is known here" about a fact that is
known, is material, is on the roster it is drawing, and is the only thing on this seat that a
person could act on today. `Jayden Higgins · WR · IR` is sitting in the FLEX slot at
`desktop.html:366` with a value of 21 beside his name, and the panel directly beneath him says
there is no injury feed. In the quiet state the page goes further and puts a green check next to
"Material injuries on starters: none".

It matters more than the fabrications because it is the failure mode this project's standing rule
does not cover. A fabricated quantity is caught by a reviewer asking "where does this come
from?". A *suppressed* one is caught by nobody, because absence with a confident reason looks
exactly like diligence — which is `front_page.split_reason`'s own argument: *"a wrong reason
reads as reassurance, which is worse than a clumsy one."* This page is at its most dangerous
precisely where it looks most careful.

The fix is ~4 lines in `capture_front_fixture.py` and it cascades correctly through the design
that already exists: the Lineup panel gets a real row, the cleared list loses a constructed
"none", the tally moves off `1 NEEDS YOU`, and the verdict sentence has a second clause that is
measured rather than hand-written. Do it alongside the `current_week` disclosure (finding 1) and
the two rank sentences (finding 2), and the three worst things on the page are gone for maybe
twenty lines of fixture and copy.

## Plainly: refine, do not abandon

**Refine.** This is the densest of the three and it earns the density honestly in most places —
I set out to find the six invented panels that the last round's densest mock carried, and there
are none. The two quantities I expected to be fabricated (the six depth labels, the per-player
bye values) both verified exactly against the engine, which is not what happened to
`mock_62` or `mock_65`. The absence grammar works, and in one place it works against a `0` its
own fixture handed it — which is the strongest thing I can say about a design under this brief.

What has to change is prose, not structure: four sentences deleted or rewritten (two rank
claims, one causal clause, two "measured and cleared" summaries), one word (`priced`), one column
deleted, one row told the truth, one panel split in two, and one `class="l"` added. None of that
costs the design anything it should want to keep. The `×LG` column is the only element whose
removal is visible, and it is the element the designer offered up first.

Two cautions on the refinement. First: the cleared list is the deck's best original idea — "the
densest honest version is the list of checks the engine actually ran and passed" — and it is
also, as built, the page's one invented quantity, because no such inventory exists. Make it real
in `front_claims` (a `CHECKS_RUN` tuple beside `RUNGS_PRODUCED_HERE`, which exists to pin exactly
this sort of known gap) or make it a list rather than a count. Do not leave a `5` and an `8` in
30px mono beside two numbers that *are* measured.

Second: `NOTES.md` is mostly accurate and its self-criticism is specific and mostly correct — the
mobile budget, the hand-written verdict copy, the ratio column, the faint mean line are all real
and all volunteered. But it closes with *"Nothing on the page needs a quantity that the engine
does not compute."* That is true of the quantities and false of the page. The rank claims, the
pricing-coverage claim and the cleared-count have no producer; the injury reason and the
season-projection reason are false; and the futurity, attribution, have/on_sync and
diffs-vs-inventory rulings are each crossed by a sentence. The gap between "every number traces"
and "every claim traces" is this entire review.
