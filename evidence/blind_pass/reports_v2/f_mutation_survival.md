# Wave 2 — the mutation-survival probe, finished

Reproduced verbatim from the agent's hand-back. Not edited, not corrected.

This finishes the measurement that pass C (`c_measurement_apparatus.md`, finding 3) left UNFINISHED
because I messaged it to hand back early while it was mid-probe. That interruption was my error and
is recorded as such in `FINDINGS_V2.md`.

---

## Verdict: all three committed mutations SURVIVE the engine's own tests once the anchors module is excluded

The committed "caught" verdicts in `evidence/invariant_confirmation.json` claim a guarantee the suite does not provide.

### Setup (disclosed)
- Worktree at `/home/user/The-Dynasty-Collective/.claude/worktrees/agent-ac875e365bf1705bd` was STALE as warned: HEAD `cf8fa0c`, `draft_room.py` = 2051 lines, `draft_battery.py`/`league_config.py`/`invariant_registry.py`/`invariant_confirmation.py` absent.
- Reconstructed the correct view with `git archive c638c05a2ec97789e83c3e62e236c6a9098b9c1f` (tip of `claude/fantasy-football-control-center-ff6qlu`) into scratchpad `/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/tree` (4445-line `draft_room.py`, all files present). Copied it to `mut0/`, `mut1/`, `mut2/`; applied one mutation per copy using the harness's own `apply_mutation`. Shared checkout never modified (`git status --porcelain` clean at end).
- No forbidden paths read. No `git log` subject lines used as evidence (I only ran `git rev-parse`).
- Note: `git archive` omits gitignored data, but the harness's own fingerprint script built a board from the archive (`dc52038a… 753 964` — backstop binds on 753 of 964 rows), so the tracked data suffices. The committed evidence shows `863 1113`; the pool differs from the run that produced the evidence. Disclosed; not load-bearing.

### What the harness applies (`invariant_confirmation.py:82-108`, three mutations, not two)
| # | name | anchor sites in draft_room.py | replacement |
|---|---|---|---|
| 0 | `feasibility_first never binds` | 4093 (upside branch), 4337 (balanced) | appends `scored["_feasible"] = 1` after `fills_required_slot` is derived |
| 1 | `board order ignores feasibility` | 4100, 4345 | `sort_values` key `_feasible` → constant `_nofeas=1` |
| 2 | `board order ignores fieldability` | 4100, 4345 | `sort_values` key `_unfieldable` → constant `_nofield=0` |

`evidence/invariant_confirmation.json` records verdicts for #0 and #1 only ("caught", 550.1s / 571.5s, 2 sites each). #2 has NO committed verdict. Both recorded first-failures are in `test_invariant_confirmation_anchors.py` (line 141 regex on the fingerprint; line 57 anchor count `0 != 2`) — the established defect, confirmed.

### Preflight (harness's own fingerprint script, per mutant tree)
- reference (clean): `dc52038a… 753 964`
- mut0: `dc723bc4… 753 964` — board CHANGES → non-inert, mutant runs
- mut1: `dc723bc4… 753 964` — board CHANGES (identical to mut0's, as expected) → non-inert
- mut2: `dc52038a… 753 964` — board IDENTICAL to reference → **INERT on the harness's own fixture** (the harness would score it "MUTATION IS INERT"; no fieldability demotion binds on that 7-slot fixture)

### Modules run (identical list for baseline and every mutant; `test_invariant_confirmation_anchors.py` EXCLUDED; no `--failfast`; `PYTHONDONTWRITEBYTECODE=1`, `__pycache__` cleared before/after; run from each tree's root)
`test_feasibility_backstop test_unfieldable_backstop test_draft_board_ui test_board_renders_absence test_216_value_board_falsification test_live_board_pricing test_which_call_prices_the_board test_acting_now_observable test_display_contract_boundary test_draft_room test_pick_synthesis test_draft_battery test_battery_pricing_path test_battery_universe_boundary test_vds_battery` — 482 tests.

### Results
| tree | Ran | result | failures | RC | seconds |
|---|---|---|---|---|---|
| baseline (clean) | 482 | OK (skipped=1) | none | 0 | 265.9 |
| mut0 `feasibility_first never binds` | 482 | OK (skipped=1) | **none** | 0 | 276.3 |
| mut1 `board order ignores feasibility` | 482 | OK (skipped=1) | **none** | 0 | 275.5 |
| mut2 `board order ignores fieldability` | 482 | OK (skipped=1) | **none** | 0 | 273.9 |

The single skip in every run is `test_draft_room.InvariantTests.test_trajectory_aware_risk_adj_fixes_the_thin_bpa_sign_flip_this_test_used_to_flag` (fixture limitation, present on baseline too).

**Per-mutation verdict:**
- **#0 feasibility_first never binds — SURVIVED.** Committed verdict "caught" is wrong: it was produced by the anchors module, not by any engine test.
- **#1 board order ignores feasibility — SURVIVED.** Committed verdict "caught" is wrong, same reason.
- **#2 board order ignores fieldability — SURVIVED** (and additionally inert on the harness fixture). No committed verdict exists for it.

Post-run integrity checks: each mutant tree still carries its mutation at 2 sites; 0 `__pycache__` dirs; each log's `TREE=` header names its mutant tree.

### Why nothing catches them (structural, from reading the tests)
- `test_feasibility_backstop.py:115-131` calls `dr.feasibility_first` directly then does its OWN `board.sort_values(["_feasible","final_score"])` — never goes through `compute_draft_board`'s sort.
- `test_unfieldable_backstop.py:266-289` tests `ps._board_order` (pick_synthesis's key function) on plain dicts; line 161-171 only AST-checks that `unfieldable_last(... pool_scope=...)` is called twice. Neither observes draft_room's `sort_values`.
- `test_draft_room.py` (98 tests) has zero references to `_feasible`/`fills_required_slot`/`_unfieldable`/`cannot_be_fielded`.
- `test_216_value_board_falsification.py` takes `compute_draft_board(...)[0]` as the pick (`_board` at line 92-97, `avail[0]` at line 170) and was the most plausible catcher — all 20 tests pass on every mutant, including `test_the_backstop_arm_is_legal_which_is_what_makes_the_off_arm_the_engine` and `test_with_the_backstop_on_it_never_has_to_override_the_value_board` (explicitly `... ok` on mut0/mut1/mut2).
- Mutations #0/#1 leave `fills_required_slot` (= `_feasible == 0`) intact and only remove `_feasible` from draft_room's row ordering; anything downstream that re-sorts via `ps._board_order` on `fills_required_slot` masks the change from the pick, and nothing asserts on the board's row order itself.

### Artifacts (scratchpad, not in repo)
- Logs: `.../scratchpad/{baseline,mut0,mut1,mut2}.log`
- Scripts: `.../scratchpad/apply_mut.py`, `.../scratchpad/run_mods.sh`, `.../scratchpad/fp.py` (harness fingerprint script extracted verbatim)
- Trees: `.../scratchpad/{tree,mut0,mut1,mut2}/`
