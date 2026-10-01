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

### 3. HIGH — two repairs in this range converge on a false sentence to the chair: the engine *does* price IR and PUP

**Files / identifiers:** `pick_debate._format_candidate` (the new three-way health branch) ×
`draft_room.health_penalty` (the new `return 0.0`)

**What they claim.** `pick_debate`'s new comment: "THREE states, because there are three (`#187`):
already in the projection; charged on top; and **reported but deliberately not priced** — which a
chair instructed never to recompute cannot work out for itself". Its third branch renders:

> NO discount was applied for it — this engine does not price this designation, so his value
> below is the value of a fully fit player

**What the code does.** The branch is selected by `_charged = candidate.risk_adj is not None and
candidate.risk_adj != 0.0`, i.e. by `risk_adj == 0.0`. But `health_penalty` returns `0.0` from
**four** different returns, for four different reasons:

| | cause | is the designation priced? |
|---|---|---|
| A | `availability_basis == RULE_FLOOR` | yes — already inside the projection |
| B | `HEALTH_DISCOUNT_RATE.get(status) is None` | **no** — the only case the sentence describes |
| C | `projected_points` absent → **the new `return 0.0` made in this range** | **yes** |
| D | `rate * projected_points` where the projection is exactly `0.0` | **yes** |

A is caught by the first branch. B, C and D all fall through to the third, so the sentence asserts
"this engine does not price this designation" about designations the engine prices at
`-0.2353` of the projection.

**Input on which they differ.** The two rows `health_penalty`'s own comment names. On a HEAVY_IDP
board built without season projections, Harold Landry (PUP, bpa 2.0) and DeShon Elliott (IR, bpa
15.0) are priced on the trade-value fallback, so `_points` is NaN, so the new `return 0.0` fires
(cause C), so `risk_adj == 0.0`, so the chair is told the engine does not price PUP/IR:

```
  DeShon Elliott    IR    bpa=  15.0  risk_adj=0.0  basis=None
     HEALTH_DISCOUNT_RATE[IR] = -0.23529411764705882
     pick_debate says -> IR -- NO discount was applied for it -- this engine does not price
                         this designation, so his value below is the value of a fully fit player
  Harold Landry     PUP   bpa=   2.0  risk_adj=0.0  basis=None
     HEALTH_DISCOUNT_RATE[PUP] = -0.23529411764705882
     pick_debate says -> PUP -- NO discount was applied ... does not price this designation ...
```

Cause D reaches it on the ordinary offensive board too: 2 of 259 `health_penalty` calls on a
12T_ppr board (`IR`, projection exactly 0.0), and 2 of 481 with season projections.

Neither repair is wrong on its own. `health_penalty` returning 0.0 is right — measured below, it
restores `universal_value` and `final_score` on exactly the rows it names. The defect is that
`risk_adj == 0.0` is not a reader for "this designation is unpriced", and the sentence that reads
it as one was written in the same range. The authority that answers the question the sentence asks
is `HEALTH_DISCOUNT_RATE.get(status) is None` — derivable, one line away, and not consulted.

**How established.**
`evidence/blind_pass_v4/probes/probe_risk_adj_zero_has_four_causes.py` spies the production
`health_penalty` and tags every call by its arguments (never by call order), censusing the causes
of each 0.0 on both pricing arms;
`evidence/blind_pass_v4/probes/probe_cf3_eligibility_and_views.py` takes the two named rows' field
values **from the board** onto a `CandidateSnapshot` that `build_snapshot` itself produced, and
reports what the production formatter says about them.

---

### 4. LOW — `health_penalty`'s repair is sound, but its stated reach is not, and a contradicting claim is still live in the same file

**File / identifier:** `draft_room.health_penalty` (the new comment) and
`draft_room.compute_draft_board`'s `#112` absence-kind comment

**Verified sound first.** The repair does what it says. On HEAVY_IDP and LIGHT_IDP boards built
without season projections, the trade-value population is 62 rows, 8 of them carrying a
designation, and Harold Landry (PUP, bpa 2.0) and DeShon Elliott (IR, bpa 15.0) now emit
`universal_value` and `final_score` rather than NaN with `absence_kind` unset — the exact damage
the comment describes, repaired.

**What is overstated.** "reachable from any board built without season projections." It is not. The
population requires a league shape that gives the trade-value positions a replacement level.
Measured on a `build_mock_league(12T_ppr)` board built without season projections: the population
is **0 of 961 rows**, and the repaired branch fired **0 of 259** `health_penalty` calls. It fires
2 of 313 on HEAVY_IDP and LIGHT_IDP.

**And the wide version is still asserted elsewhere, in the opposite direction.**
`compute_draft_board`'s `#112` comment, ~2,500 lines earlier in the same file, says of that same
branch: *"the error was invisible on every board measured because that branch currently has zero
rows (0 of 1,119)"*. That reason is now false — 62 rows on two of the battery's own formats — and
it is the stated ground for a latent absence-contract breach being judged latent. The conclusion
there still holds (no `absence_kind` is assigned on that branch, confirmed: `absence_kind` is NaN
on all 62 rows); only its justification is stale. `#133`.

**How established.** `evidence/blind_pass_v4/probes/probe_a2_trade_value_branch_scope.py`, three
league shapes in one process, with `health_penalty` spied so the branch that fired is observed:

```
12T_ppr   : TRADE-VALUE POPULATION n = 0   branch census {B:251, E:6, D:2}
HEAVY_IDP : TRADE-VALUE POPULATION n = 62  branch census {B:311, E:6, D:2, C:2}
LIGHT_IDP : TRADE-VALUE POPULATION n = 62  branch census {B:311, E:6, D:2, C:2}
```

---

## Attacked and found sound

### `B-F4` — `feasibility_first` reads eligibility, and the repaired path is the one production takes

The repair keeps a `if "player_id" not in scored.columns:` fallback to the old primary-bucket
reading. If production never supplied `player_id`, the repair would be a guard that cannot fire.
It does supply it: spying the production `feasibility_first` across a `build_snapshot` on
HEAVY_IDP recorded **13 calls, every one with `player_id` present** on a 1,850-row frame. The
fallback is the test-only arm, as the comment says. (`probe_cf3_eligibility_and_views.py`.)

### `C-F3` — eligibility crosses the snapshot boundary, and the census is not uniform

A populated-but-uniform `eligible_positions` would make `filter_candidates_by_view` a no-op while
looking repaired. Measured on an 84-candidate HEAVY_IDP snapshot at pick 1.01: **0 candidates fell
back to `{position}`**, set sizes `{1: 73, 2: 11}`. Running both rules in one process over the same
candidate tuple:

```
  view LB   pre-repair  12  post-repair  23  newly visible 11: Will Anderson, Byron Young,
                                             Andrew Van Ginkel, Nik Bonitto, T.J. Watt, ...
  view DL   pre-repair  12  post-repair  12  newly visible 0
  view DB   pre-repair  12  post-repair  12  newly visible 0
```

T.J. Watt appears in the LB view, which is the finding's own example. Non-vacuous and uneven — the
shape a real repair has. (`probe_cf3_eligibility_and_views.py`.)

---

*(review in progress — further findings appended below as they are established)*
