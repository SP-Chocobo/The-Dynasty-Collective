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
| `#343` dashboard | **CERTIFIED** |
| `#344` / `#344b` landing page | **CERTIFIED** |
| `#345` round 6 | brief + 2 of 3 explorations; **register entry written late — see `#353`** |
| `#346` two defects in my own code | **FIXED AT SOURCE + CERTIFIED** 4531 / 1356.954s OK |
| `#347` landing page is not an analysis surface | rebuilt as entry/management surface |
| `#348` provider registry agnostic; 3 tables in `app.py` are not | **RECORDED, NOT FIXED** |
| `#349` ornament + the art pipeline | shipped; contrast correction published at `e055a01` |
| `#350` in-league dashboard wired | **CERTIFIED** 4531 / 1356.954s OK |
| `#351` two serialization defects, one deliberate | **RECORDED, NOT FIXED** (needs its own pass) |
| `#352` a verification that cannot fail is not one | **STANDING RULE**, owner-adopted 2026-11-08 |
| `#353` register authority; `HANDOFF` is state, not findings | **STANDING RULE**, owner-adopted |
| `#354` server-rendered, one process, localhost first | **RULED**; milestone 1 not built |

## THE NEXT ACTIONS, IN THIS ORDER — the order is load-bearing

Everything in the previous list is DONE: the `standing` subagent reported, `#346` is fixed at
source, every fixture and page was regenerated, and one full suite certified `#343` / `#344` /
`#344b` / `#346` / `#350` together (4531 tests / 1356.954s OK at `409b8a9`).

1. **A REGISTER-COMPLETENESS RATCHET.** `#353` is a rule with no instrument, which `#352` says is
   the weak form. Nothing checks that an item number cited in code or docs resolves to a register
   heading — which is exactly how `#345`, `#349`, `#350` and `#351` went unrecorded while a test
   file asserted one of them WAS recorded. Measure the current population first; if the gap is
   large, baseline it and forbid growth the way `SKIP_GATES.json` does, rather than inventing
   entries to reach zero.
2. **MILESTONE 1 — the read-only server, on `127.0.0.1` ONLY** (`#354`, owner's ruling). Two routes
   rendering through the existing builders unchanged. Acceptance criteria are in `#354`, and the
   one most easily skipped is the last: measure END-TO-END REQUEST LATENCY and REAL TRANSFER SIZE.
   The 0.5 ms figure is composition and was never the request.
3. **The asset repair, inside milestone 1.** 83% of the dashboard page is three inlined base64
   images. Content-addressed filenames, `Cache-Control: public, max-age=31536000, immutable`.
   148.4 KB per navigation -> 9.9 KB after the first. The cache headers are not a nicety; without
   them the change is churn. Measure brotli then too — it is NOT installed here, so it is unmeasured.
4. **The passphrase gate into `app.py` only** (owner's ruling). `app_auth.py` is built and tested
   in scratchpad, three-state. Not the mockups: they are fixture-built and leak no league data.
5. **`#351`'s own pass.** Two mechanisms, one deliberate. Repairing the serializer changes every
   fixture's bytes, so it needs its own regeneration and its own suite run.
6. **Present all three round-6 designs beside the base**, which is what the owner asked for.
7. **`#348`** — three hardcoded provider tables in `app.py` that the registry does not reach.

**NOT a next action: redesigning the landing page.** Owner's call, 2026-11-08: hold it until the
first live deployment runs, because navigating the real thing will say what belongs on it better
than another mockup round will.

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
