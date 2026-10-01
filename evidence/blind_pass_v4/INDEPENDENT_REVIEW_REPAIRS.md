# Independent review of the v4 repair set

**Range reviewed:** `eac7491..7984b1d` (`git diff eac7491..HEAD -- '*.py'`), where `eac7491` is
the commit the `v3-freeze` tag dereferences to and `7984b1d` is the v4 freeze candidate.
32 Python files, +1538/−167.

**Stance.** Every docstring, comment, commit message and `evidence/` claim in the range was read
as a claim to be tested, not as information. Where a comment and the code disagree the comment is
reported as the defect (`#133`). Nothing was repaired — this is a review.

**Environment note.** The container had no project dependencies installed; `pip install -r
requirements.txt` was run first. Every probe below was run from the repository root with
`PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1` (the `.pyc` rule from `engine-measurement`).

Probes are committed under `evidence/blind_pass_v4/probes/` and are re-runnable.

---

## Findings, severity order

### 1. HIGH — `E-F5`'s new guard cannot fire on the way the season fetch actually fails

**File / identifier:** `sleeper_client.priceable_season_projections`

**What it claims.** The comment added in the range:

> A FAILED FETCH IS NOT AN ABSENT ONE (E-F5). When the season fetch fails outright the sync
> stores `season_projections = {}` and sets `coverage.error` — and `{} or None` is None, so this
> early return handed the caller no refusal string and the Draft Room rendered NO WARNING while
> the board was vendor-priced.

**What the code does.** The new branch is `if (coverage or {}).get("error"):`. `coverage.error`
is written in exactly one place: `sleeper_client.sync_league`'s `except Exception` around
`self.get_season_projections(...)`. But `get_season_projections` delegates to `_sum_weeks`, which
calls `get_weekly_projections` — and that method's own docstring says it **FAILS SOFT**: it
catches `SleeperAPIError` and returns `{}`. A failed week is appended to `weeks_failed` and the
loop continues. `_sum_weeks` then builds its coverage record, **which has no `error` key at
all** (`season`, `season_type`, `weeks_requested`, `weeks_answered`, `weeks_failed`, `players`,
`weeks_present_by_player`).

So for the ordinary outright failure — Sleeper unreachable, every week erroring — nothing raises,
`coverage["error"]` does not exist, `season_projections` is `{}` → `None`, and the new guard is
skipped. `priceable_season_projections` returns `(None, None)`: no refusal string, no warning,
vendor-priced board. That is the precise defect E-F5 claims to have closed, still reachable
through the sibling branch.

**Input on which they differ.** Any sync in which `_weekly_stat_lines` raises `SleeperAPIError`
for every week (connection failure, non-200, a 200 with an HTML body) rather than
`get_season_projections` itself raising.

**How established.** `evidence/blind_pass_v4/probes/probe_ef5_failed_fetch_is_silent.py`. The
coverage record is produced by `_sum_weeks` itself — not hand-built — by subclassing
`SleeperClient` so `_weekly_stat_lines` raises, then feeding the real `(totals, coverage)` pair
into the production consumer:

```
coverage keys          : ['players', 'season', 'season_type', 'weeks_answered',
                          'weeks_failed', 'weeks_present_by_player', 'weeks_requested']
coverage['error'] ?    : False -> None
weeks_failed (n)       : 18
season_sum_is_complete : False
priceable -> REFUSAL   : None
VERDICT: SILENT (no warning) -- E-F5 guard did not fire
```

The arm the comment describes (an exception out of the fetch, `error` hand-set) does warn, which
is what makes the repair look complete.

**Note on the test.** `test_a_partial_season_is_not_a_season.py` covers this with
`_coverage([], error="ConnectionError: x")` — a hand-built record carrying the key. The fixture
and the defect agree: the test passes whether or not the real producer ever writes that key. The
authority that *is* already correct for this state is `season_sum_is_complete(coverage)`, which
returns `False` for the fail-soft record; the guard was written against a key instead of against
that reader.

---

### 2. MEDIUM — the D10 ambiguity messages state a declared starting-slot count that is wrong whenever an unrecognised label repeats

**File / identifier:** `league_config.ambiguities`

**What it claims.** The `AMBIGUITY_UNKNOWN_SLOT_STARTER` detail tells the manager "the board was
priced on N starting slots where your league declares M"; the `AMBIGUITY_UNKNOWN_SLOT` detail
says "your league has **up to** M". The module docstring presents the bands as "THE MEASURED
IMPACT rather than a judgement about severity", and the loud band as saying "the bound is what is
missing rather than implying a size" — while in fact stating a bound.

**What the code does.** `unknown` is `sorted({slot for slot in slots if slot not in KNOWN_SLOTS})`
— a **set of distinct labels**. `M` is then computed as `parsed_starting + len(starters)` and
`parsed_starting + len(unresolved)`, i.e. distinct-label counts, while `slots` is a list that
preserves duplicates. A league declaring the same unrecognised starting label more than once is
under-reported by (occurrences − 1).

**Input on which they differ.** `roster_positions = [QB, RB, RB, WR, WR, TE, FLEX, K, DEF, BN,
BN, IR, "super-flex", "super-flex", "super-flex"]`. The solver parses 9 starting slots; the league
declares 12 (`league_config.starting_slots` over the list); the message says 10. Same for three
`WIZARD` slots: "has up to 10" where it has up to 12 — so the stated bound is not merely vague, it
is too tight, in the message whose stated purpose is to let the reader size the error.

**How established.** `evidence/blind_pass_v4/probes/probe_cf4_duplicate_unknown_slot.py`, which
compares the number in the rendered detail against `league_config.starting_slots` over the raw
roster list:

```
--- THREE occurrences of the same unrecognised STARTING label
    solver parsed   : 9
    league DECLARES : 12
    MESSAGE CLAIMS  : 10  ->  WRONG, understates by 2
--- THREE occurrences of the same unresolvable label
    MESSAGE CLAIMS  : 10  ->  WRONG, understates by 2
```

**Note on the test.** `test_a_warning_is_as_loud_as_its_consequence.
TheVolumeFollowsTheConsequenceTests.test_the_COUNT_matches_the_SOLVER_and_not_a_literal` is
written exactly as the repo's rule asks — the expectation is derived from
`lo.slots_from_roster_positions`, not from a literal — and it still passes, because every fixture
it iterates (`"Bn"`, `"super-flex"`, `"WIZARD"`) appends the unknown label **once**. It pins the
left-hand number (`parsed_starting`) against its authority and leaves the right-hand number
(`parsed_starting + len(...)`) unpinned against any authority at all. The fixture and the defect
agree.

---

*(review in progress — further findings appended below as they are established)*
