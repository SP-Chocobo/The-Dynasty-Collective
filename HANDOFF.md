# Session handoff — read this before doing anything

Written against compaction. The register (`POST_AUDIT_PLAN.md`) holds the reasoning; **this
holds the STATE and the NEXT ACTIONS**, which are the two things a summary loses.

Branch: `claude/fantasy-football-control-center-ff6qlu`. Everything below is pushed unless the
"in flight" section says otherwise.

## WHERE THINGS STAND

| item | state |
|---|---|
| `#337` / `#337b` shared season projections | **CERTIFIED** 4467 tests / 1549.379s OK |
| `#339` thin_positions cross-interface | **CERTIFIED** 4444 / 1465.001s OK |
| `#342` `checks_run` + the quiet page | **CERTIFIED** 4467 / 1549.379s OK |
| `#340` landing-page cost measurement | measured, doc-only |
| `#341` grading currency ruled | recorded, **conversion unbuilt** (2 owner rulings open) |
| `#343` dashboard | built, 24 tests, 8 ratchets green — **full suite owed** |
| `#344` / `#344b` landing page | built, 16 tests, 8 ratchets green — **full suite owed** |
| `#345` / `#345b` round 6 | brief + 2 of 3 explorations committed |
| `#346` two defects in my own code | **RECORDED, NOT FIXED** — see sequence below |

## THE NEXT ACTIONS, IN THIS ORDER — the order is load-bearing

1. **Wait for the `standing` subagent.** `ui_explore/round6/standing/` is untracked because an
   unfinished directory and a finished one look identical from a listing. Commit it when it
   reports.
2. **Fix `#346`.** Both are verified; the register has the evidence.
   - `capture_front_fixture.py:157` writes `trade_value or 0.0`, so an UNPRICED player becomes
     `0.0`. **Do not change it to `None`** — measured, `optimize_lineup` and `bye_collision`
     both raise `TypeError` on a `None` value. Add a `priced` field beside the numeric one
     (`#190`'s shape) and have renderers read that.
   - `front_claims.byes_ahead` clears `worst_week` to `None` and KEEPS `worst_week_loss`.
3. **Regenerate every fixture and page.** `front_fixture.json`, `quiet_fixture.json`, the twelve
   `ui_explore/seats/*.json`, then every page built from them: `round3/front.html`,
   `round3/front_empty.html` (its OWN fixture — see trap below), `round3/front_quiet.html`,
   `round5/dashboard*.html`, `round5/landing.html`, and the round-6 builders.
4. **ONE full suite** covering `#343`, `#344`, `#344b`, `#346` and round 6 together. Then
   certify them in one commit.
5. **Present all three round-6 designs beside the base**, which is what the owner asked for.

## OWNER RULINGS — settled, do not re-litigate

1. **Expansions are POPOVERS**, not inline. "a popout or pop-over, not in-line."
2. **Record is OFF the front page.** The test is not "is it real?" but **"does it ask anything
   of me?"**
3. **`deck` is the in-league dashboard.** The owner prefers it and said so twice. The LANDING
   page is a different surface with a different shape — a list, one line per league. Confusing
   the two cost two rounds.
4. **Grading prices in points under the league's own rules**; trading keeps dynasty trade value.
   Two sub-rulings still OPEN and they are the owner's: which weeks a season-points grade sums,
   and what a partial-coverage floor means in the new currency.
5. **Restraint in INFORMATION, generosity in CRAFT.** Two passes were rejected for cutting the
   craft along with the information. The type scale must span ~12px to ~44px with real jumps;
   the FIGURE is the hero in mono.
6. The chop league eliminates the last-place team weekly, so each Monday is a gate. **The bye
   rung's magnitude ordering is the only one defensible** — risk ordering needs a last-place
   threshold the engine withholds the neighbours of.

## TRAPS THAT COST REAL TIME THIS SESSION

- **The tree is FROZEN from the moment a certifying suite launches until it returns.** Not just
  source: the register and design docs too, because tests read them. A COMMIT is safe (it moves
  the index, not working-tree files); an EDIT is not; **adding a NEW PATH to the index is not**,
  because `doc_index` and `prose_names` enumerate `git ls-files`. One run was voided this way.
- **Each builder has its OWN fixture.** `build_empty.py` defaults to `empty_fixture.json`.
  Handing it `front_fixture.json` silently rewrote the unsynced page's freshness grade — a
  699-byte corruption that `git status` showed only as ` M`. This happened TWICE (`#332`, then
  again this session). Read the diff, do not trust the rebuild.
- **`/usr/bin/python3`, never bare `python3`** — the other interpreter lacks numpy.
- **Mutation panels go hollow.** Five caught this session: a verdict piped away by
  `tail -3 | head -2`; an identity check on a file a failed patch never wrote; a type-floor
  mutation anchored on a CSS rule two redesigns deleted; and a forbidden-phrase ban that could
  not tell an assertion from its denial. **Anchor mutations on injected probes, not on text a
  redesign can delete**, and always print the `OK`/`FAILED` line.
- **Suite budget: 12 dated measurements in `.claude/skills/close-register-item/SKILL.md`.**
  Latest 4467 / 1549.4s. Size timeouts from the table's WORST total (1976.7s), not the latest;
  two runs of the same tree differ by ~5%.

## IN FLIGHT

- `standing` subagent, writing `ui_explore/round6/standing/`. Untracked on purpose.
- Nothing else. Working tree is otherwise clean and pushed.
