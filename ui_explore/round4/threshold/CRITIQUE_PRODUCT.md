# The Threshold — PRODUCT adversary

**Charge:** does every displayed element represent something CDME can actually calculate or
retrieve? Verified against source, not against `BRIEF.md`. Targets: `desktop.html`,
`mobile.html` (quiet), `desktop_loud.html` (loud).

Independent replay used as evidence throughout: I re-derived the fixture's seat from
`evidence/batteries/VDS_2026-10-01_varied_drafting_strategy_dd4ade7.json` +
`data/fixtures/sleeper_capture.json` with stdlib only (snake order, 12 × 16), and reproduced
`front_fixture.json`'s roster exactly (seat 1: 1 DEF, 2 TE, 2 QB, 2 RB, 7 WR, 2 K; baseline
lineup value 315; week-6 loss 95). Every league-wide count below comes from that replay.

---

## BRIEF.md's Real/Forbidden table is wrong in four places

You asked to be told prominently. Three of these are against the design; one is in its favour and
indicts a *committed* file instead.

**1. WRONG — "structural holes (no body who can fill a slot) | set difference against
`league_usable_positions`".** `league_usable_positions` is never called by the fixture builder.
`ui_explore/capture_front_fixture.py:145-148` computes holes with
`lineup_optimizer.slots_from_roster_positions` + `slot_coverage`:

```python
slots = lo.slots_from_roster_positions(roster_positions)
cover = lo.slot_coverage(mine, slots)
occupied = {a["slot_id"] for a in cover["occupied"]}
unfilled = [sl for sl in slots if sl["slot_id"] not in occupied]
holes = sorted({sl["label"] for sl in unfilled})
```

and the script's own comment at `:139-144` explicitly *rejects* the function your table names:
"league_usable_positions EXPANDS flex slots … Both behaviours are right for that job and wrong
for this one: in a standard FLEX league with no dedicated TE slot it reports TE as a slot nobody
can fill". The fixture's own provenance string carries the same error —
`_provenance.basis.structural_holes = "measured -- league_usable_positions vs the roster"` — and
should be corrected, because `build_front.py` dispatches rendering on these strings. The
Threshold's *prose* ("There is a body for every slot this league uses") matches `slot_coverage`
and is therefore more accurate than both the brief and the fixture's basis string.

**2. WRONG, and it put a false sentence on the page — the data block's "(bottom of league)".**
`BRIEF.md:120-121` writes "DEF: 1 rostered (bottom of league)" and "TE: 2 rostered (bottom of
league)". `depth_ratings.depth_label` returns a *ratio band*, never a rank: `STRONG if ratio >=
1.3 else WEAK if ratio <= 0.7 else AVERAGE`, where `ratio` is the cell against the mean over
peer cells. There is no rank anywhere in `depth_ratings`, `depth_chart` or the fixture. And on
this fixture the claim is false:

| | seat 1 | league counts | teams tied with seat 1 | count-ratio |
|---|---|---|---|---|
| DEF | 1 | `[1,1,2,1,1,2,2,2,2,2,2,1]` | **5 of 12 hold 1** | 0.632 → Weak |
| TE | 2 | `[2,7,2,2,2,2,3,2,3,3,2,2]` | **8 of 12 hold 2** (the modal count) | 0.750 → *Average* |

TE is not the bottom of anything; two TEs is what two-thirds of the league holds. Note also that
TE's count ratio is 0.750, i.e. *above* the Weak cutoff — so TE's `Weak` label did not come from
bodies at all, it came from the value branch (`use_value`) resting on the 1-of-2-priced floor.
This string is inherited, not invented: it is in the committed baseline at
`ui_explore/round3/build_front.py:130` ("bottom of this league at the position") and in the
committed `ui_explore/round3/front.html`. It is a repo-wide defect that your table propagated
into all three round-4 designs. `VOICE.md` rule 7 names it exactly: "No superlative it cannot
prove."

**3. INCOMPLETE — "bye damage per week, in trade-value points | `lineup_optimizer.bye_collision`".**
True as far as it goes, but the fixture feeds the solver a substituted zero for every unpriced
player (`capture_front_fixture.py:132`: `"value": priced.get("trade_value") or 0.0`), and
`bye_collision`'s basis token cannot report it: `unknown = [p for p in roster_players if
p.get("bye") is None]` degrades the basis on unknown *byes* only. Three of sixteen rostered
players carry `0.0`, one of them a starter. See finding 9 — the figures are not floors, they are
figures with an unpriced zero inside them and an error of unknown sign. The table should add:
"and it is not a clean measurement when any rostered player is unpriced; `BYE_PARTIAL` tracks
unknown byes, not unpriced ones."

**4. RIGHT where a committed file is wrong — the unit.** Your table and this design both say
**trade-value points**, and that is correct: the fixture prices from `trade_value`
(`capture_front_fixture.py:132`), `depth_chart.positional_depth` sums `trade_value`, and both
`bye_concentration` and `roster_diagnostics.py:33` state results "in trade_value units". The
committed prototype renders the same number as **"95 UV pts"** —
`build_front.py` uses `ds.VALUE_UNIT_SHORT`, and `design_system.py:289-290` defines
`VALUE_UNIT = "universal-value points"`, a different scale ("signed and unbounded and are NOT
fantasy points"). `ui_explore/round3/front.html` therefore ships the bye figure in the wrong
unit. Fix the committed page, not this design.

**One addition for the Forbidden list:** *a positive all-clear for `starter_injury_flags`.*
Production renders an empty flag list as **silence** (`app.py:3857`: `if
readiness["starter_injury_flags"]:` → chip, else nothing), on the same ruling that excludes
Questionable — "Silence is the honest output for a fact that carries nothing"
(`player_universe.py:60`). See finding 1.

---

## THE RULING on the stamped quiet state

You asked two questions. They have different answers.

**(a) Is a stamped fabrication acceptable as a demo of a state the real fixture cannot produce?**
In principle yes — the repo already has the machinery (`build_front.stamp_kind`/`field`), and
`BRIEF.md:112` sanctions it. **As built, no**, because this page does not meet the standard it
invokes:

- The three fabricated rows (Holes, Depth, Byes) carry **no stamp on their own rows**. The only
  `constructed` stamp in the ledger sits on the Starters row, which is constructed for a
  *different* reason (`optimize_lineup` in place of a submitted lineup).
- The ledger-head stamp `quiet state · constructed seat` is **`display:none` on mobile**
  (`mobile.html` CSS: `.ledger-head .stamp{display:none}`).
- The bye strip's `aria-label` recites six fabricated numbers — "31, 26, 38, 22, 29, 20" — with
  no basis at all, on both quiet pages.
- The page simultaneously asserts, in body copy above the fold, that those same rows are
  **measured** (finding 4).

So this is not a stamped fabrication. It is a fabrication with a disclaimer filed elsewhere, and
`ui_explore/round3/build_front.py:280-283` records the repo *already repairing this exact shape*:

> "It used to be a hardcoded sentence asserting that three fields were measured, which is how a
> page full of hand-written demo numbers came to print the word 'measured' under them."

Three edits clear it: move the stamp onto each fabricated row, delete the aside's "measured", and
stop hiding the stamp at 390px. Those cost the design nothing it should want to keep.

**(b) Would the same page be honest in production, where the numbers would be real?** **No** — and
this is the more important answer, because *the fabrication is the least dangerous thing on this
page*. Six findings below survive a real-data substitution completely untouched: the
five-check completeness claim (2), the affirmative injury all-clear (1), `synced · Fresh` (3),
"Every position rates Average or Strong" (10, 11), the invented week number (8), and "bottom of
the league" (brief correction 2 / finding 5). A production Threshold would still be wrong, and
would be wrong with no stamp anywhere to warn anyone. The quiet state's problem is not that its
numbers are made up; it is that the page has **no render state for "this check did not run."**
It has a value, a stamp and an em dash. Production's own readiness strip has four tones, and
`app.py:3825-3828` says why: "'unknown' is a fourth tone on purpose: it is neither an all-clear
nor a measured problem, and giving it either of those colours would state something."

---

## Findings, most severe first

### 1. "No material injury on a starter" is FABRICATED, and it is false on this fixture — all three files

**Where** — the Starters row, `desktop.html`, `mobile.html`, `desktop_loud.html`:
`<span class="n">10 of 10</span> filled. No material injury on a starter.`

**What is wrong** — the check was never run, and when run it returns one flag. On the loud page,
which the designer's own NOTES says is where "everything else there is measured", the page prints
a false statement about a player's health.

**Evidence** — `fx["starters"]` contains `"12484"`. In `data/fixtures/sleeper_capture.json`,
player `12484` is **Jayden Higgins, WR, `injury_status: "IR"`**.
`player_universe.is_material_injury_status("IR")` → `True` (`IMMATERIAL_INJURY_STATUSES =
("Questionable",)`), and `GAMES_MISSED_FLOOR["IR"] = 4` — "a player placed on injured reserve and
designated to return must miss at least four games". `lineup_readiness.compute_readiness` would
therefore return `starter_injury_flags = [{"name": "Jayden Higgins", "position": "WR",
"injury_status": "IR"}]`.

Three compounding facts:
- `compute_readiness` is **never called** by `capture_front_fixture.py`, and the fixture's
  `roster` rows carry no `injury_status` field at all — so nothing on the page could have
  computed this.
- `optimize_lineup` — which *built* this starting lineup — reads only `id`, `value`, `eligible`
  (`lineup_optimizer.py:67-105`). It has no notion of injury. So the page asserts health about a
  lineup chosen by a solver built to ignore health.
- The `constructed` stamp does not cover it. The fixture's basis string reads "CONSTRUCTED --
  optimize_lineup's best legal lineup", which explains the slot count and says nothing about
  injuries.

Production never says this sentence. `app.py:3857-3863` emits a chip only when the flag list is
non-empty; an empty list renders nothing.

**Cost to fix** — delete the sentence. Zero design cost: the row loses four words. Or thread
`injury_status` into the fixture's roster rows and call `compute_readiness`, which is about ten
lines, and the row then reads `10 of 10 filled. 1 starter flagged: Jayden Higgins (IR).` — which
is a *better* page, because the quiet state stops being quiet for a real reason.

---

### 2. "every check the engine can run came back clean" is a completeness claim, and it is false three ways

**Where** — `desktop.html`/`mobile.html` eyebrow note; `desktop_loud.html` ledger head
("five checks, every week, the same five"); the aside ("Five checks, named below").

**What is wrong** — naming your checks is the right instinct, but "every check the engine can
run" promises the list is exhaustive. It is not, and the page's own list contains a false entry.

**Evidence** —

(a) *One of the five is false.* Finding 1.

(b) *The ladder has a fourth rung the page does not name, and it outranks everything on the page.*
`front_claims.LADDER` is four rungs, not three: `("clock", "a deadline you can actually miss;
everything else keeps until tomorrow")` sits **above** hole, bye and thin. `front_claims.py:38-45`
is explicit that this is a known absence, not a dead branch: "when the app knows you are on the
clock, that claim outranks everything here and the ladder already says so." And the app *does*
know — `app.py:5707-5709`:

```python
on_clock_id = str(pick_order[current_index])
on_clock_name = owner_names_by_id.get(on_clock_id, f"Roster {on_clock_id}")
st.caption(f"Not your turn yet -- {on_clock_name} is on the clock.")
```

So the clock is REACHABLE, merely unwired to this surface. A quiet page saying "Nothing needs
you" and "every check the engine can run came back clean" while a live draft clock runs is the
worst false negative this product can produce, and the page's own completeness claim is what
makes it a lie rather than a gap.

(c) *Data freshness is a real check with real firing states and is not among the five.*
`freshness.build_freshness_manifest` + `data_merger.recency_grade` produce
`Fresh/Recent/Aging/Stale/Unknown` plus per-row failure labels that
`sleeper_client` writes: "never fetched on this machine", "past its daily refresh; a failed
refresh silently keeps using this copy", "FETCH FAILED (…); the board is priced from the vendor's
projection instead of your league's own rules", "This sync returned FEWER weeks than the one it
replaced". These fire as attention chips in production (`app.py:3990-3991`: `⚠️ FA data {n}d
old`) and as a pill on the Matchup surface (`trade_ledger_ui.freshness_pill`). The Threshold
demotes all of it to one reassuring word in the smallest type on the page (finding 3).

`VOICE.md` rule 5 sanctioned *"Five checks, all clean — starters, holes, depth, byes, record"*.
It did not sanction "every check the engine can run", and it warned about exactly this
direction: "'all systems green' invites inventing systems to be green about." The design
strengthened a licensed sentence into an unlicensed one.

**Cost to fix** — one word and one row. "Every check this page runs came back clean" is honest and
costs nothing. Adding a sixth row (`Clock — no draft clock reaches this page`) and a seventh
(`Sources — Aging, 76d; 2 of 4 never fetched`) costs 44px and converts the strongest objection to
the page into its strongest argument: a ledger that admits what it cannot see is the only kind
worth reading.

---

### 3. "synced 11 min ago · sources Fresh" — both halves fabricated; the second is contradicted by the repo's own committed measurement

**Where** — `.seat .mono` in the header of all three files. Mobile shortens it to
`synced 11 min ago · Fresh`, which drops the one word that scoped the grade.

**What is wrong** — neither quantity exists for a replayed seat, and the grade that *does* exist
on this machine is the opposite of the one printed.

**Evidence** —

*The sync age.* `league_config.config_age_seconds` reads `(snapshot or {}).get("synced_at")` and
returns **None**, "never a large number: 'never synced' and 'synced long ago' are different
answers and a caller rendering the second for the first would say the opposite of the truth"
(`league_config.py:345-347`). `describe_config_age` returns `None` on that. And
`build_freshness_manifest` adds the sync row **only** `if synced_at:` — so on a seat with no
snapshot there is no sync row at all. `front_fixture.json` holds no snapshot, no `synced_at`, no
freshness block of any kind. The phrase is also not the engine's: `describe_config_age` emits
`"11 minutes ago"`, not `"11 min ago"`.

*The grade.* `data_merger.COMPOSITE_RECENCY_GRADES = [("Fresh", 7), ("Recent", 30), ("Aging",
90)]`. The repo's own committed capture of this machine's freshness state,
`ui_explore/empty_fixture.json`, records:

```json
"grade": "Aging",
"grade_basis": "measured -- recency_grade over the oldest LOADED source (76d)",
"worst_days": 76,
"on_sync": [
  {"basis": "ABSENT -- never fetched on this machine", "label": "Sleeper player database"},
  {"basis": "ABSENT -- never fetched", "label": "Sleeper season projections (the league-scored board)"}
]
```

So: the grade is **Aging**, the oldest loaded source is **76 days**, and **two of four sources
have never been fetched**. The 76-day source is the *Draft Sharks Trade Value Chart* — the source
the loud page's 95 is denominated in. The page labels it Fresh.

Worse, "sources" plural is a basis collapse the engine was deliberately built to prevent.
`recency_grade` grades **one** number, and `front_page.compose_unsynced` computes it over the
oldest **loaded** row only — the absent rows are split off into `on_sync` precisely because "A
page that rendered all four as one table with two dashes would make the second pair look like
damage. **After a sync the same two absences WOULD be damage**" (`front_page.py:28-31`). One word
for four rows, two of which are absent, is that split thrown away.

This is also `VOICE.md` rule 6 — "Absence is stated, never filled. … Never a zero, never a
blank, never a reassuring default" — violated twice in one twelve-word line.

**Cost to fix** — one line of copy. `sync — never synced on this seat · sources Aging, 76d, 2 of 4
never fetched` is longer and uglier, and the design has already decided this is "deliberately the
quietest thing on the page" (NOTES). That decision is now the problem: the quietest thing on the
page is the only element that qualifies every number above it. The honest version needs the line
to be allowed to grow, not to shrink.

---

### 4. The quiet page asserts above the fold that its three fabricated rows are "measured"

**Where** — `desktop.html`, `.aside` beside the CLOSE THE APP control:

> "Five checks, named below. **Byes**, **holes** and **depth** are **measured against this
> league's own rosters**; the lineup is a replayed seat."

**What is wrong** — those are the exact three rows the footnote 1,500px below calls fabricated.
The page contradicts itself, with the false half above the fold and the true half under two
folds.

**Evidence** — the same file's `.basis` paragraph: "the bye profile, depth and holes above are
**fabricated** to show the shape of a clean week". And `build_front.py:280-283` records the repo
repairing this precise defect once already:

> "THE FOOTER IS DERIVED. It used to be a hardcoded sentence asserting that three fields were
> measured, which is how a page full of hand-written demo numbers came to print the word
> 'measured' under them. … the page that claimed hand-editing could not quietly promote a demo
> value into a measurement was itself the proof that it could."

Two further errors in the same sentence: "the lineup is a replayed seat" misnames the lineup's
basis — the *roster* is a replayed seat; the *lineup* is `optimize_lineup`'s output standing in
for Sleeper's `starters` array, which is what makes it constructed. And the whole aside is
`display:none` on mobile (`.aside{display:none}`), so the phrase "Five checks, named below" —
the page's own licence for the completeness claim — never reaches a phone at all.

**Cost to fix** — rewrite one sentence. On the quiet page it should say the opposite of what it
says. Zero design cost; the aside keeps its shape and its length.

---

### 5. "bottom of the league" — a rank nothing computes, false on this fixture

**Where** — `desktop_loud.html`, both "Can wait" rows: `Thin. 1 rostered — bottom of the league
at the position.` / `Thin. 2 rostered — bottom of the league.`

**What is wrong** — `depth_label` returns a band against the mean. It never ranks. And the TE
claim is flatly false.

**Evidence** — see brief correction 2 above for the full table. Summary: `depth_ratings.depth_label`
is `STRONG if ratio >= _STRONG_RATIO else WEAK if ratio <= _WEAK_RATIO else AVERAGE` with
`_STRONG_RATIO = 1.3`, `_WEAK_RATIO = 0.7` — a ratio to the peer mean, computed from
`positional_depth`'s cells, which carry `count`, `value`, `valued_count` and no rank. My replay:
5 of 12 teams hold 1 DEF; **8 of 12 hold exactly 2 TEs**, the modal count. Production's shipped
phrasing for the same judgment is deliberately rank-free — `app.py:4004`: `f"Thin at {', '.join(_attn_thin)}"`, with a comment saying it exists to avoid "a second opinion/ranking
engine".

Note the second-order finding this exposes: TE's count ratio is 0.750, *above* the Weak cutoff.
So TE is on this page only because `depth_label` took the value branch, and that value is the
1-of-2-priced floor the row itself discloses. The page's floor caveat is correct and well placed;
"bottom of the league" is the thing that makes the row assert more than the floor can support.

**Cost to fix** — strike five words. `Thin. 1 rostered — well under the league's own average at
the position.` is provable (0.632 against a 1.583 mean) and no shorter. A real rank is REACHABLE
(`positional_depth` holds every team's cell) but nothing computes it today, and "tied for fewest
with four other teams" is a weaker sentence than the ratio.

---

### 6. The quiet state's fabricated figures are not stamped where they are shown, and mobile hides two of three disclosures

**Where** — `desktop.html` / `mobile.html`: Holes row, Depth row, Byes row + strip.

**What is wrong** — basis is not attached to the figure. On mobile it is attached to almost
nothing.

**Evidence** — the `constructed` stamp appears on the Starters row only. The Holes, Depth and
Byes rows carry no stamp. `mobile.html` CSS adds `.ledger-head .stamp{display:none}` and
`.aside{display:none}`, leaving a single 14px italic line, after six nav rows on screen two, as
the only notice that the entire page is invented. The bye strip's accessible name on both quiet
pages is `"Bye damage by week, weeks 6 to 11, in trade-value points: 31, 26, 38, 22, 29, 20"` —
six fabricated figures with no basis, delivered to a screen-reader user as fact.

The house rule is stated in this round's own files. `VOICE.md` rule 4: "Every figure carries its
basis. `measured` / `≥ floor` / `constructed` / `— absent, with its reason`. **Four states,
visually distinct, never collapsed.**" `round4/keep/NOTES.md:266`: "a constructed value is
stamped where it is shown, not in a footnote."

**Cost to fix** — three stamps, and delete one `display:none`. The design cost is real and worth
naming: the quiet ledger gains three gold tags and stops looking serene. That is the correct
trade. A serene page is what this one is for; a serene page that is also invented is the thing
the project forbids.

---

### 7. Basis collapse across states: the quiet and loud Holes rows are byte-identical

**Where** — `desktop.html` and `desktop_loud.html`, Holes row.

**What is wrong** — the same string, same styling, same position: fabricated on one page,
measured on the other. A reader who sees both cannot tell which is which.

**Evidence** — both files contain, character for character:

```html
<div class="v">None. There is a body for every slot this league uses.</div>
```

On the loud page this is `structural_holes: []`, `basis: "measured"`. On the quiet page it is
invented. The Starters row is likewise identical across all three files while its truth value
differs (finding 1). This is the `ADVERSARY.md` definition of basis collapse: "`measured`,
`constructed`, `floor` and `absent` drawn identically, so a reader cannot tell a battery
fixture's demo number from a real measurement."

**Cost to fix** — covered by finding 6. One stamp distinguishes them.

---

### 8. "Week 6 needs you." asserts futurity the engine refuses to assert — and the committed baseline says so out loud

**Where** — `desktop_loud.html` `<h1>`, `<title>`, and the eyebrow "week 6". Also the quiet
pages' eyebrow "week 7".

**What is wrong** — the whole loud page is framed as a deadline. The engine has an explicit
ruling that it cannot claim a deadline on this data, and the committed prototype prints that
ruling on the card.

**Evidence** — the fixture:

```json
"current_week": null,
"current_week": "ABSENT -- a replayed draft has no point in the season. A live league reads
season/week from Sleeper's NFL state; without it the bye claim cannot assert that a week is
still ahead"
```

`front_claims.byes_ahead`: "THE RUNG'S REASON IS FUTURITY, so a claim that cannot establish
futurity must not borrow the urgency. … with none, the same numbers are a season-shape fact and
the caller says that instead of implying a deadline." The claim it emits carries `ahead_only:
False`. And `ui_explore/round3/build_front.py:111-113` renders exactly that, verbatim in the
committed `front.html`:

> " This counts the whole season, including weeks already played — the app does not know today's
> week here."

The Threshold deletes that sentence and promotes the opposite to 96px. The baseline's own title
for the same claim is indicative and provable — `Week 6 costs you 95 …` — which is also what
`VOICE.md` rule 1 asks for ("*Week 6 costs 95.* — not *Review week 6.*") and what its Applied
table rules, by name, against the two strings this design uses: `Nothing needs you.` →
`Nothing open this week.`; `One thing needs you.` → `One thing is open.` NOTES never mentions
`VOICE.md`.

Two secondary defects in the same slot:
- **The eyebrow means two different things on two pages.** Quiet: "week 7" = the current week.
  Loud: "week 6" = the claim's week. Same slot, same type, two quantities.
- **"week 7" is fabricated and unstamped.** NOTES admits the invention ("'Week 7' is an
  assumption … I chose 7") but the page does not: a value whose engine basis is ABSENT is printed
  as a bare number in the page's second-most-prominent line, in a design whose stated grammar is
  an em dash with a reason. It also makes the quiet strip internally odd — it draws week 6 as part
  of "the season's bye damage" while the eyebrow says the current week is 7, which is the one
  thing `byes_ahead` exists to prevent ("the first version of the page … would happily have put a
  week already played second on the band").

**Cost to fix** — on the loud page, either carry the baseline's disclosure in the dek, or change
the headline to the indicative ("Week 6 costs 95."). The first costs one line of 25px copy; the
second costs the page nothing and improves it. On the quiet pages, the eyebrow becomes
`week — not known on a replayed seat` or drops the week entirely. The design loses a number it
never had.

---

### 9. Every bye figure is computed over a roster with three players priced at a substituted `0.0`, the basis token cannot say so, and the error has no known direction

**Where** — `desktop_loud.html`: the 150px `95`, the dek's `95` and `40%`, the six labelled bars
`95 8 51 4 56 23`, the facts row `40%`. Inherited by the quiet strip's shape.

**What is wrong** — `capture_front_fixture.py` is scrupulous about this everywhere else and then
collapses "unpriced" into "worth nothing" on the roster it hands the solver. The page stamps the
result `measured` and draws it as the largest object on the page.

**Evidence** — `capture_front_fixture.py:132`:

```python
"value": priced.get("trade_value") or 0.0,
```

Three of sixteen roster rows carry `0.0`: Tyler Bass (K, **a starter** — id `7042`, in
`fx["starters"]`), Andy Borregales (K, bench), Dawson Knox (TE, bench). The fixture proves at
least one of those zeros is an *unpriced* player and not a worthless one: the TE depth cell is
`"value_label": " (>=23, 1 of 2 priced)"`, `count: 2`, `valued_count: 1` — two TEs, one priced,
and Pitts is the priced one at 23, so Knox's `0.0` is an absence.

`bye_collision` cannot report this. Its basis degrades only on unknown byes:

```python
unknown = [p for p in roster_players if p.get("bye") is None]
...
"basis": BYE_PARTIAL if unknown else BYE_MEASURED,
```

`unknown_byes` is 0, so the fixture reports `basis: "measured"` and the loud page's footer
hardcodes "Bye profile … are **measured**".

**Worked, because the direction matters.** Baseline lineup = 315 (I reproduced it: 95+42+52+24+23
+9+29+20+0+21). Week 11 removes Pitts (TE, 23) and three bench bodies; Knox is the only TE behind
him, so the TE slot is refilled at `0.0` and the reported loss is exactly 23 — matching the
fixture. Price Knox at any *v* > 0 and week 11's loss falls to 23 − *v*, `total_loss` falls below
237, and the headline share **rises above 40%**. Price starter Bass and the baseline rises, week
7's 8 rises, `total_loss` rises, and the share **falls**. So `95 / 8 / 51 / 4 / 56 / 23` and
`40%` are not floors and not ceilings; they are figures with a substituted zero inside them whose
error is of unknown sign. `basis_semantics` would call this `BOUNDED_INPUT` — "the computation ran
on INCOMPLETE INPUTS, so the result is a bound … a surface may honestly say 'still resolving'" —
if anything reported it.

Week 6's 95 is the one robust number on the page: Gibbs is priced at 95, he is the only player on
a week-6 bye, and `bench_used: 0` means his RB slot simply goes empty, so the loss is his full
value and no unpriced body enters the arithmetic. Worth saying, because it means the headline
survives and the strip does not.

Note the ranking error this creates: the design put a `≥ floor` stamp on a 2-rostered TE row and
no qualifier at all on the 150px figure that is the entire argument of the page. It has the right
vocabulary and applied it to the smaller number.

**Cost to fix** — mostly upstream: carry `valued_count` on the roster the way `depth_chart` already
does for its cells, and let the bye basis report pricing coverage. On the page, one stamp on the
figure (`3 of 16 unpriced`) and the six bar labels stop being exact. Design cost: the single
enormous number acquires a tag beneath it, which the figure component already has room for — the
caption line sits right there.

---

### 10. "Every position rates Average or Strong" overstates the check's scope and erases `depth_label`'s fifth state

**Where** — quiet Depth row (`desktop.html`, `mobile.html`); loud Depth row ("Every other
position rates Average or Strong").

**What is wrong** — two overclaims in one sentence. It asserts every position got a *rating*,
when `depth_label` has a sixth return value that is not a rating; and it says "every position"
when the check only ever looks at positions you already roster.

**Evidence** —

(a) `depth_label` returns Python `None` when `not peer_cells` or when `avg` is falsy, and
`depth_ratings.LABELS` says why that must not be rendered as a rating:

> "Every label depth_label can return. **None is NOT in here on purpose** -- it is the absence
> state ('cannot be measured'), not a rating, and **a consumer that maps it to a rating is the
> defect this vocabulary exists to make visible**."

"Nothing thin" is a safe statement (no `WEAK`, no `NO_PLAYERS_LABEL`). "Every position rates
Average or Strong" is not: it is true only if no position returned `None`, which nothing on the
page checked.

(b) `lineup_readiness.compute_readiness` iterates `for position in sorted(depth[my_team_label])`
— and `depth_chart.positional_depth` only creates a cell for a position where the team has at
least one `ROSTERED` row. So `cell["count"]` is never 0 on this path, which makes
`NO_PLAYERS_LABEL` — "None — no rostered players here", a member of `THIN_LABELS` — **structurally
unreachable** through the front page's depth check. An empty position room is invisible to it.
"Every position you roster" is the true scope; "every position" is what the page says, and the
difference is the one case the label vocabulary has a dedicated string for.

**Cost to fix** — two words ("Every position you roster rates…") plus a `None`-guard in whatever
assembles the sentence. The non-thin labels are REACHABLE — one loop over `depth[me]` calling
`depth_label` — but nothing assembles them today, so even the corrected sentence is currently
computing something no module returns.

---

### 11. `depth_label` silently switches between a value comparison and a body count, and one sentence covers both

**Where** — loud Depth row: "Every other position rates *Average* or *Strong*." Quiet Depth row:
"…against the league's own rosters."

**What is wrong** — the reader hears "I have enough bodies". The engine may have said "my few
bodies out-price the average room", which is a different and much narrower claim, and the page
never says which.

**Evidence** — `depth_ratings.depth_label`:

```python
use_value = cell["value"] is not None and all(c["value"] is not None for c in peer_cells)
```

The basis is chosen **per position**, at render time, with no token recording which was used. On
this fixture, RB: seat 1 holds 2 against league counts `[2,2,4,2,4,4,3,4,4,3,4,5]`, mean 3.417,
**ratio 0.585 — WEAK on bodies**. RB is not in `thin_positions`, so by elimination its
non-thin label came from the value branch (Gibbs at 95 carries the room). The loud page's "Every
other position rates Average or Strong" therefore covers the second-thinnest body count on the
roster. That is `depth_label` working as designed — `depth_chart` argues for it explicitly
("Count alone treats a pile of backups the same as three stacked stars") — but the page inherits
the ambiguity and resolves it in the reassuring direction.

**Cost to fix** — name the basis: "rates Average or Strong **on priced depth**". Three words, and
it is the same discipline the TE row already shows. Costs the design nothing.

---

### 12. "10 of 10 filled" cannot fail under the constructed basis, and the stamp does not say so

**Where** — Starters row, all three files.

**What is wrong** — a figure that is guaranteed before it is computed, drawn as a check that
passed.

**Evidence** — the fixture's starters come from `best = lo.optimize_lineup(mine, slots)`, which
"filters back out" only ineligible forced pairings and otherwise fills every slot it legally can.
`slot_coverage` independently reported nothing unfillable (`structural_holes: []`). So
`len(starters) == len(slots)` is a consequence of the construction, not a measurement of the
roster. The capture script's own docstring says it intended otherwise — "for one scenario, leaves
a slot deliberately open, because a front page whose only state is 'everything is fine' cannot be
judged" — but the committed fixture has 10 of 10.

The repo has fixed this exact shape before, in production, on the same quantity.
`app.py:3838-3843`:

> "An absent or empty roster_positions makes it 0 -- and `filled >= 0` is then True for every
> roster that has ever existed, so the most prominent element on this surface emitted an emerald
> all-clear ('0/0 starting slots filled') asserting readiness from a quantity that was never
> computed."

**Cost to fix** — the stamp's tooltip should say what the construction forecloses: "constructed —
the optimizer's best legal lineup, so this cannot read less than 10 of 10". One tooltip. Or draw
the fixture's intended second scenario and let the row fail once.

---

### 13. "Roster 5" is invented and contradicts the fixture; the league name's absence is deleted rather than rendered

**Where** — `.seat` in the header of all three files: `Roster 5 · a replayed battery seat`.

**What is wrong** — the page names a roster that exists nowhere, and silently drops a field whose
absence the engine records with a reason.

**Evidence** — the fixture: `"team": "Team 1"`, `_provenance.seat: 1`, and
`positional_depth` keys on `owner_name or f"Roster {roster_id}"`, so even the fallback form would
be "Roster 1". `5` appears in no fixture field, no brief line, and no engine output; the sibling
`round4/deck` design renders the fixture's actual `Team 1`. And `league_name` is `null` with
basis `"ABSENT -- a format label is a battery arm, not a league's name"`. The committed baseline
runs **both** through its stamp dispatcher (`build_front.py:299-303`), so the team wears
`constructed` and the league name renders as an em dash carrying that reason. The Threshold prints
neither.

Separately: "a replayed battery seat" reintroduces jargon the baseline deliberately removed — "No
format slugs, no strategy enums, no 'seat', no 'universe rows' -- four pieces of internal jargon
on a consumer page, naming a battery arm the reader has no concept of" (`build_front.py:291-292`).
The baseline put the constructed-ness in a stamp instead. That is the better tool and the design
already owns it.

**Cost to fix** — use `Team 1`, add the `constructed` stamp, render `league — a format label is a
battery arm, not a league's name` as an em dash with its title. The header grows by one dash.

---

### 14. The thin rows' door contradicts the one module that owns that judgment

**Where** — `desktop_loud.html`, both "Can wait" rows: `<a class="door">Roster Maintenance</a>`.

**What is wrong** — `front_claims` exists specifically so no surface grows a second opinion about
a claim, and it rules the route.

**Evidence** — `front_claims.compose`:

```python
claims.append({"kind": "thin", "route": "League", ...})
```

(`hole` → `"Roster Maintenance"`, `bye` → `"Matchup"`.) The module's docstring states its purpose:
production's two bad options without it were to "re-implement the ranking (a second source of
truth, which `#126` forbids) or text-extract it from a builder". The route is part of the
composed claim. NOTES argues the override on taste ("I picked the room where the action is, not
the evidence") and the argument is reasonable — Roster Maintenance does hold Free Agents and the
`Thin at X` chip — but a design that disagrees with `front_claims` should change
`front_claims`, not route around it.

**Cost to fix** — either use `League`, or change one literal in `front_claims.py` and say so. The
second is the right answer and costs the design nothing.

---

### 15. "Open Matchup" is the only primary door, and Matchup cannot show what the page just claimed

**Where** — `desktop_loud.html`, `.btn.primary` → "Open Matchup".

**What is wrong** — not a door to a nonexistent room; a door to a real room that does not contain
the thing.

**Evidence** — `bye_collision` and `bye_concentration` have **zero `app.py` call sites**. Their
only callers in the tree are `ui_explore/capture_front_fixture.py`,
`ui_explore/round3/build_front.py`, `roster_diagnostics.py` (a harness) and
`quantity_readers.py` (a census). The Matchup view (`app.py:3804-3976`) renders Lineup Readiness,
the decomposed roster, projections and the Prytaneum — no bye profile, no week strip, no
`value_lost`. A reader who follows the one primary control arrives somewhere that cannot discuss
week 6. `front_claims` does route `bye` to `"Matchup"`, so the design followed the ruling; the gap
is that the destination's content is REACHABLE and unwired.

**Cost to fix** — nothing in the design. It belongs on whoever wires the bye profile into Matchup,
and it is worth stating because this page makes that wiring load-bearing rather than optional.

---

### 16. Precision and vocabulary, smaller

- **"40% of the season's entire bye damage"** (loud dek). `total_loss` is a sum of six
  independent counterfactuals, each `baseline − without(week)`; `bye_concentration` sanctions it
  only as the ratio's denominator ("deliberately a RATIO, so shape is separated from severity")
  and never as a quantity to state. The ratio use is correct; "entire" promotes a denominator to
  a total. One word.
- **"every slot this league uses"** (Holes row). `slots_from_roster_positions` drops
  `BN/TAXI/IR` — "not a lineup slot, intentionally excluded". The claim is about *starting*
  slots; this league has six BN slots it also uses. One word.
- **"5,357 players in the pool."** REAL — `_provenance.universe_rows`, and the same prose ships in
  the committed baseline (`build_front.py:293`). But the same provenance block holds
  `players_in_capture: 6595, players_in_pool: 6594`, so "the pool" is the engine's name for a
  different number one level down. "in this league's player universe" is exact.
- **`≥ floor` is one stamp for two bound kinds.** `basis_semantics` splits `BOUNDED_INPUT`
  ("more evidence would sharpen it … a surface may honestly say 'still resolving'") from
  `BOUNDED_BY_RULE` ("this is already the most that can be said … a consumer must never re-check
  it hoping for a sharper answer"). The TE stamp is correctly `BOUNDED_INPUT` and its sentence
  says so. The risk is latent: the same stamp on an IR games-missed floor would invite a re-check
  that cannot help.
- **"The Prytaneum" is not a destination.** `app.py` navigation is a five-option
  `st.segmented_control`: `[MATCHUP_VIEW, MAINTENANCE_VIEW, DRAFT_VIEW, LEAGUE_VIEW,
  IMPORT_VIEW]`. The Prytaneum is a persistent band below every view (`st.subheader("The
  Prytaneum")` outside all four branches; the CSS calls it "The Prytaneum's dock: fixed to the
  bottom of the viewport"). The brief listed it as a sixth destination and the committed baseline
  draws six doors, so this is inherited — but a colophon that takes the trouble to say where
  Trade Calculator and Standings live should say that one of its six doors is not a room you go
  to.
- **Mobile drops the colophon sentence entirely** and shortens the seat line to `· Fresh`,
  removing the one word that scoped the grade to sources. Both make the 390px page assert *more*
  than the desktop one with less qualification.

---

## What survives attack

Named precisely, because a pass on these is the useful half of this review.

1. **The Record row is the best element in the round.** `record: null` with basis "ABSENT --
   team_standings reads Sleeper's settings.wins/losses, and no capture in data/league_captures/
   holds a roster's contents or a result", drawn as `— no capture holds a roster's result` in the
   row itself, on all three files, desktop and mobile, with the reason adjacent rather than in a
   tooltip. That is `league_standings`' absence contract ("ABSENCE IS NOT A ZERO") rendered
   correctly, and it is the one row on the page nothing I found touches.

2. **The unit is right, and the committed page is wrong.** "trade-value points" matches
   `trade_value` as fed (`capture_front_fixture.py:132`), summed (`depth_chart`) and described
   (`bye_concentration`, `roster_diagnostics.py:33` and `lineup_optimizer.py:886`: "in trade_value units").
   `ui_explore/round3/front.html` ships `95 UV pts` via `design_system.VALUE_UNIT_SHORT`, which
   is a different scale. Fix the baseline.

3. **The holes prose is more accurate than the fixture's own basis string and than the brief.**
   "There is a body for every slot this league uses" describes `slot_coverage`, which is what the
   capture actually calls. Brief correction 1.

4. **The loud page's claim ordering is faithful to `front_claims`, not re-derived.** Bye above
   thin is `LADDER` rank; DEF before TE is `thin_sort_key` = `(count, position)` with DEF at 1 and
   TE at 2 — the ordering that comment records was earned by a bug ("in one real league hid a
   ONE-quarterback room … below the cap"); three claims against `CAP = 3`; no hole claim because
   `structural_holes` is empty. "Two things can wait" is the ladder's own reason for the thin
   rung ("a standing weakness with no deadline attached"), not a designer's word.

5. **The TE floor is drawn, not footnoted, and phrased in the producer's own semantics.** "Only 1
   of 2 could be priced, so the comparison is a floor, not a total" is
   `depth_chart.depth_value_label`'s argument verbatim in spirit ("'at least', not 'is', when the
   sum is partial"), and it is on the row, beside the number, with a stamp. This is the page's
   best instinct and the one that should be copied onto the bye figure (finding 9).

6. **Both bar strips are honest charts.** I measured the geometry: quiet bars scale at
   0.6636–0.6658 px per unit, loud at 0.725–0.7391, both zero-baselined against a drawn hairline,
   one hue, worst week the only lit bar, no second axis, no meter, no gauge. Nothing on any of the
   three pages is a 0–100 bar, a letter grade, a rating, an odds figure, a "% rostered" or a pick
   price.

7. **Questionable is never mentioned, and the fixture contains a Questionable starter.**
   Wan'Dale Robinson (id `11560`, `injury_status: "Questionable"`) is in `fx["starters"]`, and the
   page says nothing about him — which is exactly `IMMATERIAL_INJURY_STATUSES`' ruling ("OUT OF
   THE ARITHMETIC AND OUT OF THE PROSE"). The page got the hard half of the injury contract right
   and the easy half wrong.

8. **Position diamonds use the ruled tokens.** DEF `#ef7fc0`, TE `#ff6042` —
   `design_system.POSITION_PILL_TOKENS` exactly, no invented hue.

9. **The six doors are the committed set** (`build_front.py:277-279`), and five of them are real
   `st.segmented_control` options. The colophon's claim that "Trade Calculator and Free Agents
   live inside Roster Maintenance; Standings inside League" is **true**: `hcol1.subheader("Trade
   Calculator")` at `app.py:4171` and `st.subheader("Free Agents")` at `:4022` both sit inside
   `elif main_view == MAINTENANCE_VIEW:` (`:3977`), and `LADDER_LENS = "🏆 Standings"` at `:6159`
   sits inside `elif main_view == LEAGUE_VIEW:` (`:6119`). Verified, correct.

---

## The single most important change

**Delete "No material injury on a starter." from all three files today, and replace "every check
the engine can run came back clean" with "every check this page runs came back clean."**

Those two edits remove the only *false statement about a player* on the page and the only claim
that the page's list of checks is complete. Everything else here is a qualification; those two
are a wrong fact and a wrong scope, and both travel into production unchanged because neither
depends on the quiet state being fabricated.

The structural change behind them, which is one component and not a rewrite: **the ledger needs a
fourth state.** It can say a value, a stamped value, and an em dash with a reason. It cannot say
*"this check did not run"* — and the injury sentence, the `synced · Fresh` line, the invented
week number and "Every position rates Average or Strong" are all that fourth state rendered as
one of the other three. Production's readiness strip already has it and already says why
(`app.py:3825-3828`: "'unknown' is a fourth tone on purpose: it is neither an all-clear nor a
measured problem, and giving it either of those colours would state something"). The Threshold is
a page whose entire thesis is that absence is information. It is missing the one mark that says
so.

## Verdict

**Worth refining. Do not abandon it.**

Of my sixteen findings, eleven are a sentence or a word, two are a stamp, two belong upstream of
the design, and one is a component. None requires the page to change shape. The architecture is
the most honest-shaped of the constructs I was asked to attack: a named-check ledger is
auditable in a way a score is not, the Record row is the best-rendered absence in the round, the
claim ordering is the engine's and not the designer's, the unit is right where a committed file
has it wrong, the holes prose is right where the brief has it wrong, the charts do not lie about
their scale, and the one position where the design chose a floor caveat over a clean number is
the position where it mattered.

What it is guilty of is the thing a named-check ledger is uniquely able to be guilty of: having
listed five checks, it got one of them wrong, implied there were no others, and then — in the
same breath that it fabricated three rows — wrote the word *measured* above the fold. A page that
names what it checked can be audited. This one was, and it did not pass. But it failed in the
direction that is cheap to fix, which is the opposite of the dense, polished, six-invented-panel
failure this round exists to avoid.

On the quiet state specifically: a stamped fabrication is a legitimate demo and this one is not
yet stamped. Three edits make it one. But the question that matters more is the second one, and
the answer is no — this page would not be honest in production with real numbers, because its
defects are not in the numbers. Fix the copy first and the fabrication second.
