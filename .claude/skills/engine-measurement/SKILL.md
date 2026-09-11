---
name: engine-measurement
description: Stand up a correct real-data measurement against the CDME engine — boards, drafts, batteries, before/after comparisons. Use before writing ANY probe, ablation, A/B, or instrument that reads draft_room / pick_synthesis / draft_battery output, and before claiming any measured result. Encodes the fixture setup that six separate measurement errors in this repo came from getting wrong, plus the two instrumentation rules earned by withdrawing published findings in #222.
---

# Measuring this engine without fooling yourself

Every measurement error made during the #150 battery pass was a FIXTURE error, not a reasoning
error. The reasoning was checkable; the harness silently produced numbers about the wrong thing.
This file is the checklist that would have caught them.

**The failure mode to fear is not a crash. It is a plausible number about something else.**

#222 added a second family with the same shape but a different cause: the fixture was right and
the INSTRUMENT was wrong — it recomputed a quantity production already computes, and it captured
one of three calls to a function without recording which. Two published findings had to be
withdrawn. Those rules are in "Instrument the production quantity" below; read them before
writing any spy, wrapper or ablation.

## The fixture, and why each line is there

```python
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

merger = dm.DataMerger()                                    # 1. from the REPO ROOT
players_db, prov = rdb.build_players_db_from_capture()      # 2. the REAL universe, 6,595
season = rdb.season_projections_from_capture()              # 3. price the way production does
merger.set_league_format(db.league_format_hint(league))     # 4. NEVER SKIP THIS

snap = dr.build_snapshot(..., sleeper_projections=season,
                         sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)   # 3, cont.
```

1. **Run from the repo root. Never `cd` first.** `DataMerger()` resolves its baseline paths
   relative to the working directory. Backgrounding a probe with a `cd` into the scratchpad
   produced an empty frame and `KeyError: 'position'` — the merger loaded nothing and said so
   only by crashing three calls later. Put the probe file wherever you like; run it from root.

2. **`build_players_db_from_capture`, NOT `build_players_db`.** These are two different
   populations and the names do not warn you. `build_players_db` is the VENDOR
   RECONSTRUCTION: 764 rows, id space `"16"`/`"291"`, no `injury_status`, no
   `fantasy_positions`. `build_players_db_from_capture` is what production actually receives:
   6,595 rows, id space `"13384"`, health and eligibility present. Only 373 ids collide
   between them and **the collisions are coincidental** — an id that exists in both is a
   different player. #201 made the reconstruction raise-on-missing for the battery precisely
   so nothing would fall back to it silently; a hand-written probe bypasses that.
   `build_players_db` is kept only as the universe of measurements already recorded against
   it (`run_demand_reach_audit.py`), never for new work.

   This is the sixth fixture error of this class in this repo, and it is the one that is
   hardest to see, because the wrong universe produces a complete, plausible board. It
   surfaced in #222 only because **311 of a draft's 312 picks were not on the board being
   analysed** — four findings had already been written on it. If a probe builds a board and a
   draft separately, assert they share a universe before comparing them:

   ```python
   assert set(board["player_id"]) >= {p.chosen_player_id for p in traj.picks}
   ```

3. **Season projections, or the league's own scoring never reaches a price.** A board built
   without `sleeper_projections` + `SLEEPER_BASIS_SEASON_SUM` is priced off the vendor's
   static pre-computed number, so every claim about `rec`, `bonus_rec_te`, `rush_fd` or any
   other rulebook category is vacuous (#180/#192/#204). Both halves of the universe must come
   from the SAME capture.

4. **`set_league_format` before every format you draft.** THIS IS THE BIG ONE. `rec` and
   `bonus_rec_te` do NOT propagate through `scoring_settings` into offensive valuation — Draft
   Sharks' season projection is a static pre-computed number. They propagate by FILE SELECTION:
   `set_league_format` picks a different rankings export. `app.py` calls it every rerun.
   A battery that never called it drafted all 32 formats from one export, and standard /
   half_ppr / ppr came back **byte-identical**. Nine of thirteen "findings" were artifacts.
   Derive the hint from the league's own settings (`db.league_format_hint`) rather than
   carrying it alongside — a hint that can disagree with its league is a second source of truth.

## Picking a turn to measure

`positional_forfeit`, `survival_probability` and `rival_premium` are all computed over the picks
between this turn and MY NEXT ONE. **The gap that matters is the one AHEAD.**

```python
nxt = next((j for j in range(i + 1, len(pick_order)) if pick_order[j] == me), None)
if nxt is not None and nxt - i > 1:   # real intervening picks
```

Filtering on the gap BEHIND is the same artifact mirrored: it rejects the round-opening turns
that carry ~22 intervening picks and keeps the round-closing ones that carry none. Measured the
wrong way round once: `rival_premium` was **0.00 for 269 of 269 candidates** and the run looked
like a clean null result.

Also: the board state must match the turn. Build `picks` from `opening[:index]` where `index` is
the turn being analysed — not from a round boundary chosen separately.

## Before/after comparisons

**Both arms must run the same code.** The only honest A/B is one process, one code version,
toggling the single thing under test:

```python
real = dr.feasibility_first
dr.feasibility_first = lambda scored, *a, **k: pd.Series(1, index=scored.index, dtype=int)
```

**Never compare a fresh run against a saved baseline from different code.** Tier 3 was reported
as fixing a format 2 findings -> 0; the 2 came from a run predating the scoring repair, and the
improvement was the scoring repair. Save the baseline JSON and record WHICH COMMIT produced it.

## Absence, in your own instrument

`if value:` conflates `None` (never computed) with `0.0` (measured zero). This engine forbids
that everywhere, and a reporting function broke it: an upside pick that legitimately measured
`growth_signal == 0.0` was counted as "no growth measured". Count `is not None` and `> 0`
**separately**, always.

## Instrument the production quantity, and name WHICH CALL you captured

Two rules, both earned by withdrawing a published finding in #222. They are cheap to obey and
each one cost a full investigation to learn.

**1. If the system already computes the quantity under test, OBSERVE that production quantity.
Never reconstruct it from downstream artifacts.**

Three separate probes "measured" the tight-end replacement level by recomputing it from
`compute_draft_board`'s OUTPUT ROWS — sorting the returned frame and reading off the row at the
demand rank. That is not the number production used. Production's number is
`replacement_levels`' own return value, which reaches the board through a cache, a fill-from-
anchor step and a displacement term, any of which can change it. The reconstruction agreed with
the real value at some board states and not others, which is exactly why it read as a defect
("the brake releases at 7 TEs") and survived three rounds of checking. The published finding B1
was wrong and had to be withdrawn.

The instrument for this is a wrapper, not a recomputation:

```python
real = dr.replacement_levels
captured = []
def spy(*a, **k):
    out = real(*a, **k)
    captured.append((tag_of(a, k), copy.deepcopy(out)))
    return out
dr.replacement_levels = spy
```

If the quantity is not reachable that way, say so and measure something else. A reconstruction
that "should" match is a second implementation, and a second implementation is a second source
of truth (#126).

**2. When a function is called more than once per operation, the instrument must identify WHICH
CALL it captured — not merely that it captured one.**

`replacement_levels` is called at least three times per board build: once inside
`predraft_replacement_anchor` (with `remaining_demand=None`, over the full pool), once live
against the remaining pool on `_points`, and once on `trade_value`. A spy that appends every
call and then reads `captured[0]` is sampling an arbitrary one of the three. Phase 2 of #222
reported a receiver "rank 37 of 198 REMAINING receivers" on exactly that mistake; the word
"remaining" had to be withdrawn, because the captured call was the pre-draft anchor over the
FULL pool.

Derive the tag from the ARGUMENTS, never from call order — order is an implementation detail
that a cache can silently change:

```python
def tag_of(args, kw):
    if kw.get("remaining_demand") is None and kw.get("flex_occupancy") is not None:
        return "ANCHOR(predraft, full pool)"
    if kw.get("value_col") == "trade_value":
        return "LIVE(trade_value)"
    return "LIVE(points, remaining pool)"
```

Then report the tag alongside the number, every time. "I observed X from function Y" is not
provenance when Y runs three times with three different meanings. And check the caching layer:
a cached call (`_ANCHOR_CACHE`) may not fire at all on the build you are watching, so a spy that
sees two calls where you expected three has told you something, not failed.

## Runtime budgets — set timeouts from these, not from hope

| what | cost |
|---|---|
| one board build | ~0.3-1.4s |
| full test suite | **~800-870s** (2100+ tests) |
| one 12-team draft (168 picks) | ~300s |
| one 12-team STARTUP (312 picks, 26 rounds) | **~640-1125s** |
| full 32-format battery | **~2.9 hours** |

A `timeout 580` on the suite kills it mid-run and tells you nothing. Background anything over a
couple of minutes and read the file.

## Two shell hazards that cost real cycles

- **`pkill -f "run_draft_battery"` matches its own launching shell.** The `bash -c` wrapper
  contains the pattern, so it kills the job it is starting. Use a character class that does not
  match itself: `pkill -f "run_draft_batter[y]"`.
- **Backticks inside `git commit -m "..."` are COMMAND SUBSTITUTION.** A double-quoted message
  quoting a docstring (`` `adjustment` ``, `` `0.0` ``) silently loses everything from the first
  backtick onward, and the commit still succeeds — so the log carries a truncated record while
  the working tree looks perfect. It cost a real commit here. Always pass a message on stdin
  with a quoted heredoc: `git commit -F - <<'EOF' … EOF`. The quoted `'EOF'` is the half that
  matters; an unquoted one substitutes too.
- **`unittest` buffers to a file.** `2>&1 | tail -N` discards the failure body. Redirect the
  whole run to a file and grep it: `> suite.txt 2>&1`, then `grep -n "^FAIL:" -A 25 suite.txt`.

## Build production's inputs in production's SHAPE, not just with its values

A probe that hand-builds an input must build it the way production builds it. A missing key is
not a missing value — it can silently select a different code path.

The one that cost a published finding (#222): `compute_draft_board(mode="auto")` resolves
upside-vs-balanced scoring from the CURRENT ROUND, and the round is read off the picks. Passing
picks as `{player_id, roster_id}` instead of production's
`{pick_no, round, roster_id, player_id}` therefore ran the whole probe in **balanced** mode
while production was in **upside** mode — two different valuations, no error, no warning, and a
completely different top of the board:

```
picks {player_id, roster_id}                 top 5:  WR WR WR WR WR   (balanced)
picks {pick_no, round, roster_id, player_id} top 5:  TE WR WR TE WR   (upside)
```

Same 915 rows, same 267 priced, same code, same process. Forcing `mode=` explicitly gives
identical results from both shapes — which is how you prove the shape mattered only through
round detection, and is the check to run when two of your own probes disagree.

So: copy the shape from the production caller (here `draft_simulation.simulate_full_draft`),
not from what the function appears to read. And when a probe and production disagree about the
same board, suspect the INPUT before the instrument — this is the same family as measuring the
wrong universe (#201) and capturing the wrong call (above).

**The rule that generalises: BEHAVIOURAL inputs need SCHEMA validation, not value validation.**
Checking that every pick has a plausible `player_id` and `roster_id` says nothing here. `round`
is not a value this code reads and reports — it is a field that SELECTS A BEHAVIOURAL MODE, and
a record missing it is not "the same record with one field absent", it is a semantically
different record. So, for any input that steers behaviour rather than being consumed as data:

```python
REQUIRED_PICK_FIELDS = {"pick_no", "round", "roster_id", "player_id"}
missing = REQUIRED_PICK_FIELDS - set(picks[0])
assert not missing, f"pick records are missing {missing}; mode='auto' reads `round`"
```

A harness has two honest options and no third: **reject the incomplete shape**, or **make the
derived behaviour explicit in its artifact** so a reader can tell which valuation produced the
numbers. `simulate_full_draft`'s trajectory config does the second — it records
`upside_from_round` and `picks_by_mode` alongside `priced_from`, for exactly the reason #204
records the pricing path: two runs made under different modes are not comparable, and without
the record the difference is invisible.

Ask of every hand-built input: **does any field of this steer a branch?** If yes, that field is
part of the input's identity, and omitting it is a silent A/B against yourself.

The same family, one layer down: **key-name mismatches across an interface.** `optimize_lineup`
takes players keyed `id` and returns assignments keyed `player_id`. A probe that hands it
`player_id` gets no crash and no warning — it gets an empty lineup, and "no seat can ever field
a complete lineup" reads exactly like a finding. Neither of these poisons the run loudly; both
poison it quietly. When a measurement comes back all-zeros, all-never, or all-identical, check
the interface before you believe it (the skill's own rule: if ON and OFF are identical, find out
why before concluding).

## Board rank is not pick order — say which one you mean

`simulate_full_draft` does not pick `board.iloc[0]`. It goes through
`pick_synthesis.build_snapshot`, whose `narrow_candidates` re-sorts every row through its own
`_board_order` key, and takes `candidates[0]` from THAT. So the board's `final_score` ordering
and the sequence of players actually taken are two different orderings, and several #222 probe
readings quietly assumed they were one.

Consequences worth stating out loud, because each one has been read the wrong way here:

- "the Nth row on the board" is not "the Nth player off the board".
- A rank measured on the FULL pool is not a rank among the REMAINING players — and "remaining"
  is the word that silently converts one into the other.
- A change that only reorders rows changes nothing, because `_board_order` re-sorts anyway.

So label every ordinal at the point you print it: `rank_on_board(full pool)`,
`rank_among_remaining`, `pick_number`. Three names, never one word doing all three jobs (#70,
#126). If a probe cannot say which of the three it computed, it has not measured an ordinal.

## Save the raw result before you derive anything from it

`simulate_full_draft` returning is the expensive part; everything after it is arithmetic. An
`AttributeError` in a reporting block — `DraftTrajectory` is not iterable, its picks live in
`.picks` as `PickRecord` with `.chosen_player_id` — destroyed a complete 312-pick draft and
1,125 seconds of engine time. Dump the raw object to JSON on the line after the call, before
computing a single percentage (#215):

```python
traj = dr.simulate_full_draft(...)
json.dump([{"pick": i, "roster": p.roster_id, "player": p.chosen_player_id}
           for i, p in enumerate(traj.picks, 1)], open(RAW, "w"))
print("RAW SAVED:", len(traj.picks), "picks", flush=True)
```

## An empty roster is not a neutral roster — it switches half the valuation off

The opening board looks like the cleanest possible measurement state: no picks, no roster, nothing
to confound. It is the opposite. **`displacement_adj` is 0.00 on all 481 priced rows of a board
built with an empty roster**, and structurally so: with every dedicated slot open, each position's
probe evicts its own position's phantom, `displaced == level`, and the term is identically zero for
every position at once.

So an opening board is not a preview of the draft. It is the one state in which the counterweight
to the replacement-level subtraction does not exist. A #222 result was published reading the
opening sort as though it governed the draft, and had to be withdrawn (the 19th) when a
mid-draft state showed the same term running at −60 to −89 on tight ends and 0.00 on receivers.

**Before measuring at a board state, ask which terms are structurally zero there** — and say so in
the write-up. `displacement_adj` is zero on an empty roster; `depth_exposure` is only `measured`
once a bench exists (round 9); the upside branch zeroes every team-specific term at once. A term
reading 0.00 because the state cannot produce it is not evidence that it does not matter.

Related fixture trap, from writing the tests for the same finding: **filling every slot with a
strong player does NOT produce the flex-phantom case.** A probe evicts the CHEAPEST thing it can
reach, so a roster whose flexes are all held by 370+ players evicts one of those — the first draft
of that test got `displaced == 360.0`, its own weakest starter, not the 217.75 phantom, and three
assertions failed for a fixture reason that looked like an engine finding. The phantom case needs a
reachable flex that is **open or weakly held**, which is the ordinary mid-draft state.

## Never name a production column from memory — take the row's own keys

`compute_draft_board` computes `_points` and `replacement_level` internally and emits NEITHER.
It emits `projected_points`; the level is not emitted at all (derive it as
`projected_points - bpa`, both of which are). A probe that asked for the internal names got
`None` on all 1,119 rows — which would have read as "no player in this league has a
projection" — because a `dict.get` on a missing key is indistinguishable from a measured
absence.

Print the emitted key set once, and assert on the column you need:

```python
df = pd.DataFrame(board)
print("EMITTED COLUMNS:", sorted(df.columns.tolist()))
PTS = "projected_points"
if PTS not in df.columns:
    raise RuntimeError(f"{PTS} absent; emitted columns are {sorted(df.columns)}")
```

The board's emitted set, for reference: `availability_basis bpa bpa_source confidence
depth_basis depth_exposure displacement_adj displacement_basis eligibility_bonus
fills_required_slot final_score horizon_basis horizon_floor horizon_sensitivity
identity_basis injury_status mode name need_bonus player_id position projected_points
replacement_basis risk_adj team time_horizon_adj universal_value waiting_cost`.

Seventh fixture error of this family. Reading the internal name in `draft_room.py` and
assuming it survives to the board is the same category as assuming the vendor pool is the real
pool: a plausible number about something else.

**Related: a board ROW count is not a PRICED count.** The F&F board is 1,119 rows of which
**481** carry `final_score`; 638 have `bpa_source == "no_priceable_input"`. A published
correction in this repo quoted 1,119 as the priced pool. Count `final_score.notna()`, and say
which of the two you mean.

## A rate of exactly zero: prove the detector could have fired

`if value:` conflating `None` with `0.0` is the version of this the file already covers. Here is
the harder version, and it survived a correct pre-registration.

RESIDUAL3 (#222) pre-registered three forks on the rate at which a term returns `adjustment ==
0.0` — its documented open-slot case — and reported "0.0 for every seat, in 144 observations."
That was Fork B, cleanly selected, and it was an artifact. `adjustment` is
`free_alternative - displaced`, so the predicate needs `displaced` to equal the candidate's own
replacement level; but under `slot_alternatives` a FLEX phantom is worth `max(levels)` across
every position the slot admits, which is above the candidate's level for every position but one.
In that population the predicate was **arithmetically unreachable**. 0 of 144 measured the
detector.

**Before you read a rate of exactly zero as a finding, state the condition under which your
detector fires and show it is reachable in the population you measured.** An unreachable
predicate returns 0.0 for every input and is indistinguishable, in the output, from a clean
null result.

The cheap version of this check: print the distribution of the quantity your predicate tests,
not just the count of hits. RESIDUAL3's own raw file had it — `displaced` took six distinct
values and none of them was the level — and nothing looked.

Note that RESIDUAL3's docstring named the hazard ("0.0 is a CONSTRUCTION, not a measured zero,
which is exactly why its RATE is the quantity") and then walked into it. Naming a hazard is not
checking for it.

## Before you report a number

- Is the population non-vacuous? Print `n`. A rate over an empty set is not a rate.
- Did the thing under test actually fire? If ON and OFF are identical, it did not — find out why
  before concluding it had no effect. (`narrow_candidates` re-sorts every board through its own
  `_board_order` key, so a decision expressed only as ROW ORDER is discarded before the pick.)
- Could this number be about a different question than the one asked? Say what would have to be
  true for it to be an artifact, then check that.

## A third shell hazard: `git push -u origin <name>` does not push HEAD

`git push -u origin my-branch` pushes the **local branch named `my-branch`**, not the commit you
are sitting on. In a worktree — where the checked-out branch routinely has a *different* name
from the branch you were told to deliver to — a stale local branch of the target name silently
absorbs every push. Git reports success and prints the branch-tracking line either way:

```
Everything up-to-date
branch 'claude/...' set up to track 'origin/claude/...'.
```

That second line is what makes it dangerous. It reads as confirmation, it appears on every
push, and it says nothing about whether a commit moved. An entire session's work went to the
worktree branch this way while the designated branch sat 164 commits behind, each push looking
clean.

- **Push an explicit refspec**: `git push origin HEAD:refs/heads/<target>`. It cannot resolve to
  something other than what you have.
- **Verify by the ref-update line, never the tracking line.** A real push prints
  `9fb5102..a020840  HEAD -> <target>`. No `old..new` pair means nothing moved.
- **`Everything up-to-date` right after a commit is a failure**, not a no-op.

Same shape as the fixture errors above: the instrument answered confidently about a different
object than the one asked about. Before fast-forwarding a branch that has drifted, prove there
is nothing to lose rather than assuming it — `git merge-base --is-ancestor <target> HEAD` and
`git log --oneline <target> ^HEAD` (must be empty). If either fails, it is not a fast-forward
and `--force` is not the remedy.

## A stale .pyc can serve you MUTATED code after you restore the source

The mutation-testing loop in this repo is: edit a source line, run the tests, `cp` the backup
back, repeat. That loop has a hole, and it was found the hard way.

CPython validates a cached `.pyc` against the source's **mtime and size**. A mutation that
preserves byte length — `0.0` → `1.0`, `>` → `<`, `+` → `-`, swapping two same-length
identifiers — and a mutate/restore cycle that completes inside **one mtime second** leaves a
`.pyc` that still looks valid. Every later `import` in that second gets the **mutated**
bytecode, from a source file that reads correctly on disk and shows a clean `git diff`.

How it presented: `estimated_bench_demand` returned a total of **1.0** in a board state where
`bench_capacity` provably floors to `0.0`, and `0.0 * anything` cannot be `0.97`. `git status`
was clean, `git diff` was empty, the line read `max(..., 0.0)`, and `inspect.getsource` on the
**bound function** showed the correct body — because `inspect` reads the source file, not the
bytecode actually executing. Four separate checks all confirmed innocent source while the
process ran the mutant. Deleting `__pycache__` produced `0.0` immediately.

**This is the project's named failure mode aimed at the instrument that exists to catch it.** A
mutation pass corrupted this way reports whatever the stale cache holds — a mutation can read as
"caught" when the tests never saw it, or as "survived" when they did.

- **Run every mutation arm under `PYTHONDONTWRITEBYTECODE=1`.** No `.pyc` is written, so no
  stale one can be served. This is the fix; use it by default for the whole loop, control arm
  included.
- Belt and braces for a long pass: `find . -name __pycache__ -type d -prune -exec rm -rf {} +`
  between arms.
- **When a measured number contradicts arithmetic you can do on paper, suspect the instrument
  before the arithmetic.** Re-deriving the same wrong number from the same poisoned process
  confirms nothing. `git diff` and `inspect.getsource` do NOT prove what is executing; only a
  cleared cache does.
- Never run a full background suite across a tree you are mutating. The suite imports at its own
  start and any source-reading test sees whatever the file held mid-cycle, so the result
  describes neither the clean tree nor the mutant. Re-run it clean afterwards.
