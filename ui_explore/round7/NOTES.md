# `#347` — the landing page, rebuilt as what it actually is

## The correction that produced it

Three attempts at this surface, and the first two were the same mistake:

| attempt | what it drew | why it was wrong |
|---|---|---|
| `round5/build_dashboard.py` | the in-league dashboard | not the landing page at all |
| `round5/build_landing.py` | the claim band at 12-league arity | still analysis, just wider |
| **this** | the league SET, and the verbs that change it | — |

The owner's words:

> This again just feels like a rebuild of the dashboard. The landing page just needs to say
> "these leagues need attention." "resync" "add league" and the connections options, no?
> ... league management and connections/setups too, maybe
> ... as in setting up new league, deleting leagues, and the like

Four of those five items are **verbs**. That is the tell: a page whose job is mostly verbs is
not a dashboard. Claim detail lives inside a league; this page says only which league wants you.

## Every affordance was read out of `app.py` before it was drawn

The hard law says you may not invent a quantity. The same applies to an ACTION — a button that
promises what the engine cannot do is that defect wearing a different hat. What reading changed:

- **Add a league is TWO paths, not one.** `app.py:2498` takes a raw Sleeper **league ID**
  (`client.get_league`) and appends one league. `app.py:2328 sync_leagues(username)` takes an
  **account** and *replaces* the whole list. An earlier draft of this page had only the account
  path, and would have drawn "Add league" as a lie about what the button does.
- **Delete is real, local, and confirmed** (`app.py:1438`, `pending_delete_league_id` at 3391).
  Its own docstring says it never touches Sleeper, and a league you are still in "will simply
  reappear, unsynced, next time they click Sync Leagues". The page says so, because a delete
  button that reads as *leaving the league* is the most expensive misunderstanding on offer here.
- **Leagues you left** are already computed (`sync_leagues` diffs against `order + archived`)
  and had no surface anywhere.
- **Archive/reorder** are local-only; `league_prefs`' own docstring says Sleeper has no concept
  of either.

## `#348` — the provider rows name nobody

> api keys need to be agnostic, not tied to specific models, companies, etc. if i wanted to
> integrate kimi k2 or grok, that should not fight the language used

`providers.py` is **already** a registry — a frozen `Provider` dataclass with `id`, `label`,
`key_field` and an `is_configured` callable. So this page names no provider: it asks the
registry. Registering Kimi K2 or Grok adds a row here with no edit to this file or the fixture.

Two things that reading taught me, neither of which I would have typed:

- the registry is **empty** at `providers`' own import and populated at `llm_engine`'s. A page
  that read it too early renders an empty card and looks correct.
- openai's real label is **"ChatGPT"**.

The page's language is the easy half. See `#348` in `POST_AUDIT_PLAN.md` for the three
hardcoded provider tables in `app.py` that the registry does not reach.

## Collapsing the set-up half

> Would any of these as collapseable buttons/commands be cleaner?

Yes, for the bottom half only. Four always-open cards spent ~700px — nearly half the page — on
the least-used controls, while the triage list is the reason you opened the page. Folded into
four commands the page went **2311px → 1606px (-30%)**, and it matches the owner's standing
ruling that expansions are popovers rather than inline disclosure.

**The cost, and what was done about it.** Collapsing hides *state*, not just controls. A bare
row of verbs would have concealed that nothing is archived, or that no key is set. So each
command carries the one number its panel exists to report — `2 archived · 1 left`,
`Sleeper · 1 of 3 providers`, `oldest source 62d` — and the page still answers "is anything
unconfigured?" without a click.

## Three build gates, all mutation-checked

`assert_marks_are_visible` / `assert_type_floor(css)` / `assert_vars_resolve(...)`.

**The first two are NOT imported from `build_dashboard`, and that is the point.** Its
`_assert_type_floor()` closes over its own module-global `CSS` and takes no argument: imported
and called from here it would check the dashboard's stylesheet, pass unconditionally, and say
nothing about this page. That is the hollow-instrument failure this session has caught six
times. Both gates here take their subject as a parameter, which is what makes them *capable* of
failing on this file.

| arm | result |
|---|---|
| real call, with `font_vars()` | passes |
| **drop `font_vars()`** (the defect that shipped) | **FIRES** |
| `font-size:.6rem` | **FIRES** |
| `font-size:0.9em` | **FIRES** |

The type floor fired on its very first run (`.7rem`, `.74rem`), which is how I know it is live.

## Three defects this page had, all found by rendering it

1. **`var(--sans)` / `--mono` / `--display` were never defined.** `design_system` defines the
   colour tokens but the faces are Python constants that `round5` substitutes with `.format()`.
   An unresolvable `var()` inside a `font:` **shorthand** invalidates the whole declaration, so
   every rule setting size and face together was dropped. Silent: no console error, no warning,
   a complete and plausible page at the wrong size. Measured: scale **12→22px**, and the 3.4rem
   tally rendering at **14.24px**. `assert_vars_resolve` now fails the build on it.
2. **A raw Python dict on the page.** `checks_summary` returns a dict *by design* (`#338`: the
   surface never derives its own counts), and an early draft interpolated it straight into the
   row — `{'ran': 3, 'clean': ['holes', 'byes', 'depth'], ...}` shipped onto the page.
   `summary_sentence` composes it now. Only looking at the render caught this.
3. **A cascade collision crushing the hero figure.** `.verdict p` (0,1,1) beat `.tally` (0,1,0),
   so the lead number rendered at 14.24px instead of 54.4px. Fixed by scoping to `.verdict div p`.
   Note this survived defect 1's fix — two independent causes of the same symptom, and fixing
   the first made the second look fixed.

Final: scale **12→54px (4.53:1)**, 18 sizes, min font 12.0px, 0 horizontal overflow at 390px,
0 console errors, both pages rebuild byte-identically.

## What I believe is still wrong with it

1. **The rows are twelve seats of ONE replayed league**, so five read `DEF rates Weak · 1
   rostered` almost identically. That is a fixture artifact, not a property of a real portfolio,
   and it is stamped CONSTRUCTED on the page. It means **this page has never been seen against
   leagues that actually differ**, which is the one test that matters for a list whose whole job
   is telling leagues apart.
2. **Connection state is entirely constructed** — there is no `data/` on a fresh clone. The
   username, sync age and which credentials are set are all stand-ins.
3. **No test file yet.** The gates are build-time; the composition (`summary_sentence`,
   `league_rows` ordering, the archived split) is untested. `#347` is not closeable until that
   exists and the full suite has run.
4. **The row popover offers Resync / Archive / Delete, but the page is static** — these are
   drawn affordances, not wired ones. Wiring is `#335`'s territory.
5. `synced_at_human` is a **phrase**, not a timestamp. The real app computes it through
   `league_config.describe_config_age`, which needs a clock a built file does not have.
