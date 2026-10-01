# Wave 6, pass K — preserved verbatim

> **The pass's own words, unedited.** Running log: `FINDINGS_LOG.md`. Verdicts: `LEDGER.md`.
>
> Conditions: Fable, worktree isolation, `/tmp/audit_tree` with the six forbidden paths excluded,
> the Wave 6 mandate identical to pass L's. **This is Wave 6's relaunch**; the first attempt died on
> the account session limit with no report.
>
> **Self-reported contamination: none.** Exclusions verified absent before reading.

## Report

**Method.** Tree extracted with the required exclusions; verified absent before reading. No forbidden
path was opened. Repository unmodified; all probes ran in `/tmp/audit_tree` or copies. Real-data
probes use `data/fixtures/sleeper_capture.json` with
`merger.set_league_format(draft_battery.league_format_hint(league_shape))` (SF, PPR, no TE-premium,
12 teams). I did not run an end-to-end draft. I did not execute the Streamlit app; app.py findings
are from reading the code path and timing the merger calls it makes.

---

## HIGH

### 1. `load_all`'s per-file dedup keys on `norm_name` alone and deletes real players before the position-aware identity model can see them

**`data_merger.py:1186-1188`** — `df.sort_values("rank").drop_duplicates(subset="norm_name",
keep="first")` runs on every rankings file *before* `_reconcile_rows` builds its
`norm_name|position_group` key (line ~1455). The comment justifies it with the same-position
"B Robinson / B Robinson Jr." case, but a first-initial export collides across positions constantly.

Measured on the committed baseline: every one of the five offense rankings files carries `J Love`
(RB ARI, rank 6-16) and `J Love` (QB GB, rank 37-133); `J Williams` (WR DET) and `J Williams`
(RB DAL); `M Washington` (WR MIA) and `M Washington Jr.` (RB LV); te_premium adds `K Williams` RB LAR
vs WR NE. Both IDP files carry six more (`B Murphy`, `D Turner`, `D Walker`, `J Johnson`, `J Martin`,
…). The lower-ranked namesake is dropped from **every** file, so `_dedup_by_name_and_position`'s and
`_drop_contested_identities`' protections never get a second row to protect.

Failure scenario (real data): `merge_player("Jordan Love", position="QB", team="GB")` →
`matched: False` (key path finds only the surviving RB ARI row, club disagrees → correctly rejected).
Same for `Javonte Williams` RB DAL, `Kyle Williams` WR NE, `Malik Washington` RB LV. A starting
superflex QB has no vendor price, no trade_value, no proj_3yr, and no `rank` on the board — reported
as `NO_PRICEABLE_INPUT`-class absence, which is the absence contract broken by the merger's own
dedup. No test covers within-file cross-position collisions.

### 2. `positional_forfeits` uses the unnormalised take table that #206 repaired only for survival

**`draft_strategy.py:365-381`** sums raw `RANK_TAKE_PROBABILITY` over each rival's top-5
(`FORFEIT_OPPONENT_BOARD_DEPTH`) rows per position and caps *each position separately* at 0.90.
`board_take_mass`'s own docstring (line ~400) says both consumers read the table; the normalisation
was wired into `estimate_survival` only.

Measured, pre-draft, real capture, seat 1 (22 intervening picks): rival board top-5 = 3 RB + 2 WR.
Forfeits assign that one pick P(RB)=0.90, P(WR)=0.16 → 1.06 players per pick; the same five rows
carry **0.029** total take mass in the survival model (McCaffrey 0.013/pick). Over the 22 picks:
`expected_taken = {RB: 19.8, WR: 3.52, QB: 0.0, ...}` — **23.3 players from 22 picks**, and 0.0 QBs in
a superflex league whose own pace prior asserts ~6 QBs go in round 1. The RB curve is then read at
index 19.8, producing forfeits of 100+ points; `test_threshold_reachability.py` docstring
independently reports forfeit p50 54.81 / max 154.94, i.e. `forfeit_component`
(`pick_synthesis.py:704-708`) is pinned at its 10-point ceiling for scarce positions while
`survival_component` for the same player says he survives ~75% of the time. `pick_debate.py:488`
renders "~19.8 RB pick(s) expected before then" to the model. The mutation
`RUN_TAKE_PROBABILITY_CAP = 9.0` (a probability cap above 1) **survives all 51 tests in
test_draft_strategy** — nothing pins the per-pick mass bound on this path.

### 3. A league-specific upload with an untagged filename loses every field to the stale committed baseline; the DataMerger docstring claims the opposite

**`data_merger.py:1768`** ("a league-specific rankings/trade-value override … takes priority over the
global pool") — no such rule exists. `_precedence_sort_key` (1326) is basis → `_format_match_score` →
date → filename; `league_dir` confers nothing. `_detect_rankings_format` (1090) tags from **filename
only**; an upload named as users name things scores 2.0 against the baseline's 6.0 for this league,
and format_match precedes recency.

Measured: copy of `dynasty_ppr_superflex_rankings.csv` with every value doubled and
`source_date=2026-09-15`, placed in a league dir as `rankings_export.csv` →
`merge_player("Ja'Marr Chase")` still returns projection 339 / tv 84 from the 2026-08-18 baseline.
Renamed with format tokens → 678 / 168. The app stores uploads under `uploaded.name` unchanged
(`app.py` ~2996) and never asks or records a per-file format despite `upload_batches.py`'s docstring
saying format "is asked AFTER parsing". 3668 of 3670 conflicts on the plain baseline load are already
`format_match`. `test_data_merger.py:459` ("newer file wins regardless of name") uses two *untagged*
files, so it only pins the tie case.

### 4. Declared `source_date` is never validated; a non-ISO date wins precedence, exactly the failure `parse_as_of` says it prevents

**`upload_batches.parse_as_of`** validates only the user-*stated* date. `load_projection_file`
(`data_merger.py:1085-1087`) passes a CSV's declared column straight through `resolve_source_date`.
Measured with `_reconcile_rows`: a frame dated `8/28/26` beats `2026-08-18` on both projection and
trade_value with recorded reason "the newer source_date wins" (`_negated_date("8/28/26")` = `1/71/73`
< `7973-…`). Which malformed dates win is arbitrary (`1/5/26` loses). Also
`resolve_source_date(None, nan)` returns `nan` (truthy) with basis `declared`.

---

## MEDIUM

### 5. Two rookie definitions; the pool-scope one is a lossy `name_key` dict with last-row-wins

`draft_room.py:1009` `dict(zip(ktc["_name_key"], ktc["rookie"]))` vs `_admits_to_pool`'s
`years_exp == 0`. Measured: 25 KTC rows share a key; of 787 pool players with a KTC key, **58
disagree**. `Jeremiyah Love` (RB ARI, years_exp 0, tv 71 — the "J Love" that survives finding 1) is
flagged **not** a rookie because Jordan Love's row wins the key; Keon Coleman (years_exp 2) is
flagged a rookie. "Rookies only" mock scope excludes the class's RB1; "Veterans only" includes him.
Docstring claims it "DETECT[s] who's actually a rookie".

### 6. `_conflict_reason` is computed against the wrong row

`data_merger.py:1481` passes `winner` (= `ordered[0]`) even when the field's chosen value came from a
later candidate. Synthetic: winner has no `projection`, c2 (format 0.5, 2026-08-20) beats c3
(format 0.5, 2026-08-10) on recency; recorded reason: `format_match`. The reconciliation log's whole
purpose is naming which rule fired.

### 7. Mock-draft format override reloads the merger twice per rerun and wipes the resolution memo

`app.py:3524` reasserts the league format at the top of every run; `app.py:4879` sets the mock's. When
they differ, every rerun does two `reload()`s (0.32s each) and clears `_merge_memo`. Measured: board
build 0.87s with warm memo, **18.0-18.9s** cold — paid on every button click in the mock view. Also
anything reading the merger after line 4879 within DRAFT_VIEW runs under the mock's format.

### 8. Draft Room snapshot cache key omits what the snapshot depends on

`app.py:5366-5371` keys on `(draft_id, target_index, roster, pool_scope, len(draft_picks),
merger.freshest_date)`. `season_projections` (re-synced from Sleeper) and `league_format` are not in
it; nothing pops `draft_room_snapshot_cache` on sync. Scenario: sync the league mid-draft (new
projections), no new pick → stale snapshot served.

### 9. `build_roster_table` overwrites Sleeper's own `position`/`team` with the vendor row's

`data_merger.py:2528` `row.update(merge_player(...))` where the field list includes `position` and
`team`. Measured on 43 matched rows: 4 LB→DL (Nolan Smith, Byron Young, Nick Herbig, Cam Jones).
`app.py` ~3722-3738 groups the Matchup roster by `r["position"]`, so Sleeper LBs render under DL.
Also passes `team="FA"` (2519) while the pool passes `NO_NFL_TEAM` — two spellings of "unrostered".

### 10. `draft_counterfactual.regret_vs_bpa` "≥ 0 by construction" is false

`draft_counterfactual.py:77`. The engine's pick is `_board_order` (`pick_synthesis.py:215`), which
sorts `fills_required_slot` **before** `final_score`. Whenever the feasibility backstop binds, engine
TAV < BPA's TAV. `test_draft_counterfactual.py:57` asserts non-negativity on fixture drafts where the
backstop never fires.

### 11. `FORFEIT_SCALE_MAX = 100` is justified by a scale that no longer exists

`pick_synthesis.py:386-395` says universal_value "is CONSTRUCTED so 100 is the largest real VOR gap".
`draft_room._scale_vor_to_bpa` (2162) now returns raw VOR in points. The divisor is an orphaned
constant; combined with #2 the forfeit term saturates.

### 12. Late-round necessity label collapses to a knife-edge on the clamp

`pick_synthesis.py:724-728`: raw score can reach ~177 (50+30+20+12+6+30+19.2+10), clamped to 100;
from round 15 `score = raw*0.3 ≤ 30`. Labels: exactly 30.0 → "LOW URGENCY", anything else → "DOESN'T
MATTER MUCH". So from round 15 the label is a function of whether the *pre-clamp* sum exceeded 100 —
raw 99.9 → 29.97 → "DOESN'T MATTER", raw 140 → "LOW URGENCY".

---

## LOW / instrument

- **`load_all` `except Exception: continue`** (`data_merger.py:1177`, also 425, 1648): a damaged
  vendor file vanishes silently; `is_loaded` cannot distinguish "no file" from "unparseable file".
- **`_compute_percentiles` `position_by_key.setdefault`** (1882): 19 keys map to >1 position group on
  the real table (`j allen`, `j love`, `m brown`…); bot_research rows for the second person get the
  first person's group and the wrong percentile pool.
- **`_bye_week_map`** (2350): `KeyError: 'team'` when any external source carries `bye_week` without a
  `team` column (reproduced); reaches `roster_diagnostics.py:219`.
- **`pick_value`** (1984): `normalize_name` strips "." so `1.03` and `10.3` (and `1.12`/`11.2`)
  collide.
- **Zero guard** (`draft_room.py:1331-1345`): a measured season total of 0.0 is deliberately reported
  as unpriced — a documented, owner-ruled collapse; recorded because it contradicts the stated
  contract, not hidden.

## Test corpus (mutation battery, one constant per tree copy)

| mutation | result |
|---|---|
| `RANK_TAKE_PROBABILITY` all 0.99 | 3/167 fail (table monotonicity, float-noise tests) — no survival *value* test fails |
| `FORFEIT_OPPONENT_BOARD_DEPTH = 0` | 5/167 fail |
| `NECESSITY_BASELINE = 0.0` | 2/166 fail |
| `match_cutoff = 0.0` (fuzzy matches anything) | 2/118 fail |
| `_STRONG_RATIO = 0.0` | 4/50 fail |
| **`RUN_TAKE_PROBABILITY_CAP = 9.0`** | **0/51 fail — survives** |
| `CLIFF_HIGH_RATIO = 1000` | 3/116 fail |

Detection exists but is thin (2-5 tests per absurd constant, typically structural rather than
behavioural); the probability cap above 1.0 is undetected.

## Nulls with method

- `_resolve`'s branches enumerated (alias / exact / key / fuzzy; each `return`): the exact path
  applies neither namespace nor offence-position rejection, but with `position` supplied it narrows
  only when >1 row exists — I found no real-data case where a single wrong-position exact row was
  returned as verified; the 81 Sleeper same-name collisions resolve as misses or correct matches. Not
  confident this holds for the free-agent table (full names).
- `outcome_record`, `upload_batches.record/forget`, `league_prefs`, `decision_log`, `resume_join`,
  `basis_semantics`, `ordinals`, `measurement`: every `except` and early return read; each collapses
  absent/damaged only where its docstring says so (`carry_forward` returns [] for both, stated). No
  gap found.
- `lineup_optimizer.bye_concentration`: Hungarian solve is exact, so `value_lost ≥ 0` and
  `concentration ≤ 1` hold; all-unknown byes and an empty roster both yield `BYE_UNKNOWN` (minor
  conflation, stated in code).
