# Repair execution — working state

**Branch:** `claude/fantasy-football-control-center-ff6qlu`. Written so this survives a context
compaction or a container reclamation: everything here is either a decision already taken, a number
already measured, or a next step with its ordering dependency stated.

---

## OWNER RULINGS IN HAND — build to these

1. **2.6 starter demand → ASSIGNMENT-BASED.** Solve each roster's lineup and count the slots actually
   filled. Owner accepted that `remaining_starter_demand` stops being a per-position subtraction and
   that **every IDP board reprices**. I said I would re-measure the battery before and after; that is
   part of the job, not optional.
2. **1.3 pace vs normalisation → CONVENTION WINS, OTHERS SCALE DOWN.** Done and pushed (see below).
3. **2.1(b) degraded sync → keep overwriting, manifest warns.** My recommendation, owner delegated.
   *No code change required* — 2.1(a) already refuses to price a partial sum, and the manifest names
   the better snapshot. Reasoning: a degraded sync can no longer produce a wrong board, only a
   vendor-priced one; the rosters ride on the same sync and matter most mid-draft, so preserving
   projections by keeping an older snapshot would put a stale ROSTER in front of the user. "Write both
   and choose" was rejected as a second source of truth about which data priced the board.
4. **1.7 `draft_history` → MINIMAL READER (list and inspect).** My recommendation, owner delegated.
   A view listing stored boards with their staleness state, and one board's candidate table on
   selection. NOT full replay: that needs product decisions about what "what was shown" means and
   whether a replayed board may look live. The store's readers (`load_snapshot_record`,
   `list_snapshot_records`, `snapshot_ids`) already exist and work.

## STILL WITH THE OWNER

- **`rival_premium_basis` borrows `denial_basis`** — one companion for two quantities that can be
  absent for different reasons. The 0.0 in upside mode is a *measured* zero (the code's own rebuttal
  holds, and measurement agrees), so this is semantics: a reader cannot tell "no rival gains anything"
  from "this valuation has no notion of a rival gaining anything". Pinned as characterization in
  `test_an_absent_term_is_not_a_measured_zero.py`.
- **2.2's league-config gate** — mandate says partly a design question.
- The mandate's own standing Owner Decisions section, plus `#184` items (tasks #36, #37).

---

## DONE AND PUSHED

| commit | item |
|---|---|
| `07d7bc5` | **Tier 0 complete** (0.1–0.9) |
| `fbbf483` | 1.2 withheld family reaching a person |
| `cef20f3` | 1.6 matcher's mentioned-name guess |
| `0ed5823` | 1.5 Debate chip context never sent |
| `35c03a7` | 1.4 Live Draft Room never fetched picks |
| `22b788f` | 1.3 deficit that never closed |
| `6f2968a` | 1.7a cache fingerprint hashed 4 of 7 fields |
| `c475210` | 1.7b held debate now knows its world |
| `81f167d` | 1.7c league-switch leakage |
| `2891680` | **full suite 3648 OK** + the six failures targeted runs missed |
| `c492717` | 1.7d diff anchor |
| `6167f40`, `2056bd1` | 1.7e half-failed debate; markers |
| `008513a` | **Tier 1 complete** — 1.7f stored record carries all four stamp fields (schema 2→3) |
| `578d8ca` | 2.1(a) truncated season sum refused |
| `fb65ab0` | 2.1(b)+(c) coverage reaches a person |
| `e20ae8c` | 2.6 first half — eight eligibility readers unified |
| `d7a21fc` | 2.6 counting sized as evidence |
| `f47a773` | 2.5 first of six — `need_bonus` fabrication |
| `9dec716` | 1.3 second half (ruled) — the convention wins, others scale down |
| `43d3c21` | **2.6 second half (ruled)** — demand is solved, not subtracted. **Pushed RED** |
| `7aeb913` | the five failures that push exposed — **full suite 3760 OK** |

**Tree clean and certified at `7aeb913`.**

---

## MEASUREMENTS THAT WOULD BE EXPENSIVE TO REDO

Probes are committed under `evidence/` because the scratchpad dies with the container.

**1.3, `evidence/pace_conservation/`.** `12T_ppr_SF`, capture universe, season sums:

| state | gap | QB expected_taken | convention's increment | all positions |
|---|---|---|---|---|
| 1.01 | 22 | 15.54 → **7.02** | 8.92 | 26.15 → **17.63 / 22** |
| after 24 picks | 22 | 2.81 → **1.45** | 2.17 | 12.99 → **11.63 / 22** |

QB forfeit at 1.01: 63.10 → 33.98. **After the owner's ruling these real numbers are byte-identical**
— real boards never saturate a pick, so the scaling only engages on the hostile synthetic fixture
(29.02 across 22 → conserves). The ruling buys the guarantee at zero measured cost.

**2.6, `evidence/multi_eligible_counting/`.** 178 multi-eligible in the universe, **66** reach a board,
earliest at **row 199**, all IDP duals (`DL/LB`, `DB/LB`). Zero multi-eligible picks in the first three
rounds of any arm. `HEAVY_IDP`, same formula, only the count changing:

| after | duals held | LB demand by label | by eligibility | difference |
|---|---|---|---|---|
| round 5 | 7 | 20.0 | 13.0 | **−7.0 of 20 slots** |
| round 10 | 15 | 3.0 | 0.0 | −3.0 |
| round 15 | 26 | — | — | none |

Every other position identical at every round. **Beware:** an earlier probe of mine compared
`team_filled_by_position` (raw pick census, bench included) against slots-filled-by-assignment (capped
at capacity) and reported differences everywhere — WR 48 vs 24. Those are two different quantities and
the gap was mostly capacity. Do not reuse that comparison.

**2.1(a).** Weeks 1–9 only, superflex: 30 of top 40 rows move 3+ places, leader Gibbs 241.66 → Robinson
113.93, QBs in the top ten 3 → 0. **1.7a.** `injury_status` alone moves the leader 232.88 → 208.77,
first to third. `years_exp`+`status` together admit one player, 970 → 971. **2.6 reader fix:** universe
6595 → 6594 (one row: Bradley Sowell, `position: TE`, `fantasy_positions: ["OL"]`, no team).

---

## 2.6 IS BUILT, AND IT IS BIGGER THAN THE RULING WAS SIZED ON — read this before re-pricing

Full measurement in `evidence/multi_eligible_counting/RULING.md`. Two things, both from the ruling's own
mechanism, only one of which was visible when it was put to the owner:

1. **The multi-eligibility half is SMALLER than the mandate said.** The mandate's −7.0 LB figure was the
   BY-ELIGIBILITY reading, which the ruling rejected. Assignment-based: LB 10.0 → 9.0 at round 10, and
   **DB 12.0 → 13.0 — the other way**, because a DB/LB dual had been paying down a DB slot he does not
   occupy. Every top-40 LB −1.00 `final_score`, every DB +1.15, through the anchor. Top pick never moved
   on `HEAVY_IDP`.
2. **A second defect with nothing to do with eligibility, and it is the larger one.** The subtraction
   counted a position's share of every flex appearance as capacity *including flex slots already occupied
   by someone else*. After nine rounds of `12T_ppr_SF` — every slot coverable, zero duals held — it
   declared **7.17 RB and 8.60 TE slots open league-wide**. Assignment says zero. At round 5: RB −8.66,
   TE −10.04, WR −1.20 across the top 40, and **the top pick flips** (Breece Hall → Rashee Rice).

So the blast radius is every board, not every IDP board. **The battery has not run over this** — the
suite says nothing contradicts itself, not that the new board drafts better. A revert is one commit.

Also weakened deliberately: `remaining_starter_demand`'s per-position monotonicity is no longer a proof
(the total still is). An exhaustive 2,860-configuration search found no counterexample; that is committed
as evidence in `test_demand_is_assignment_based.py`, not promoted to a claim.

## NEXT, IN THIS ORDER

1. **Run the battery** (`python3 run_draft_battery.py`, ~2.9h, has `--resume` written for exactly the
   reclamation problem). It is the instrument 2.6 is missing. Record the commit it ran at.
2. **1.7 minimal reader** for `draft_history`.
4. **2.5's remaining four:** `diff_snapshots` dropping measured↔unmeasured transitions; board payload
   companions; injury status never crossing the boundary; `build_context` truncating silently.
5. **2.3** (11 defenses' `name_key`, kicker `fgm_50p`, `_identity_hint` split — the last measured at
   ≤0.12 points and zero rank change: repair the mechanism, do not justify it with a cost it lacks).
6. **2.4** (`load_all` swallows unparsable files; `get_players` caches an error-shaped body).
7. **Tier 3** (3.1 percentile populations, 3.2 joint bound, 3.3 constants sized for a dead scale,
   3.4 dead terms), then **Tier 4**.

---

## STANDING CONSTRAINTS — these have already cost real cycles

- **A FULL SUITE LICENSES A PUSH, never a subset.** Bent for seven commits once: next full run, six
  failures. Bent again for three (`e20ae8c`, `f47a773`, `43d3c21`): next full run, **five failures, two of
  them already red on the tree from the earlier two commits**. ~3760 tests, ~22 min. Clear `__pycache__`
  first. When a stop-hook or a reclamation risk forces a push before the suite lands, PUSH AND SAY IT IS
  UNCERTIFIED — the sin is claiming certification, not the push.
- **NEVER EDIT THE TREE WHILE A TEST RUN IS IN FLIGHT.** Imported modules keep the old code in memory but
  the source-reading instruments (`prose_names`, `assertion_floors`, `render_trace`, `suite_taxonomy`,
  `ui_source`) read the new text, so the verdict is neither the old tree's nor the new one's. Cost a
  whole 20-minute batch here.
- **`pkill -f <pattern>` matches the shell that runs it, and `pgrep -f` matches every waiter shell
  holding that pattern.** Three separate self-kills this session. Match on the full command
  (`ps -eo cmd= | grep "python3 -m unittest discover"`), never on a bare substring.
- **`render_trace --check` fails at midnight UTC** whenever a wall-clock-derived value reaches the
  recorded trace verbatim. Twice now: the freshness grade, then `trade_ledger_ui`'s "Values 34d stale".
  The blur is a LIST in `_Recorder._CALENDAR_DEPENDENT`, and the test states the rule (no elapsed-time
  quantity in any unit) rather than naming the strings it knows about.
- **Poll every ~90s while a suite runs** — the container is reclaimed on idleness and CPU does not
  count. Five background runs have already died this way.
- **Never `git checkout <file>` to undo a mutation test** — it takes HEAD and silently drops
  uncommitted work in that file. Copy the file aside first.
- **Backticks inside `git commit -m "…"` are command substitution.** Always `-F <file>`.
- **`assertIn` against a whole module dumps the module** into the failure output. Use
  `assertTrue(x in source, "short message")`.
- **Grep finds your own comment.** Two ratchets of mine flagged prose documenting the shape they had
  just removed. Read the AST, not the text (`#200`).
- Tier 0's instruments catch my prose repeatedly: `prose_names` (backticked names that exist nowhere),
  `test_prytaneum_terminology` (retired product names), `invariant_registry` (a proven population that
  grew — re-verify over the new population, THEN move the census).
- Run the meta-checks with every batch: `test_suite_taxonomy` (a new test module needs a `§N` or `#NNN`
  citation in its docstring), `test_prose_names`, `test_invariant_registry`, `python3
  render_trace.py --check`, `python3 assertion_floors.py --write`.
- Commit trailer: `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>` + the `Claude-Session:` line.
  No model identifier in any pushed artifact.
