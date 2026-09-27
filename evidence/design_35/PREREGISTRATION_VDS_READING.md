# Pre-registration — how the completed VDS battery gets read, and what a second instrument must show

Written **after** the 36 arms landed and after the structural findings were counted, and **before**
either comparison instrument below was built or run. The battery's own gate
(`GATE_FOR_VDS.md`) fixed what would launch it; it did not fix how to read it, and the reading
turned out to need two things the report cannot answer by itself.

## What the battery settled on its own

36 arms, 32 effective (4 reproduced their control byte-for-byte), 76 findings, 6h43m at `04bccb5`
with `streaming_floor_exercised: true` and 18 weeks of lines — so `#30` fired on the one format
carrying K and DEF slots, which the stopped run could not have shown.

Read strategy-wise as the report's own `_comment` instructs:

- `STRATEGY_SPECIFIC_FINDINGS` names exactly one strategy, `noisy_k8`, in four formats. That is the
  shape `#22` had, and it is why this battery exists.
- `12T_ppr_SHORT_DRAFT` finished with **zero** findings under all six strategies.
- 73 of the 76 findings are `unfieldable_depth`. **49 of those 73 do not survive a roster-bucket
  recount** — `draft_battery._position_of` returns the RAW Sleeper position by deliberate design
  (its docstring records this as a latent issue kept for comparability with five committed
  batteries), so a player whose `fantasy_positions` are `['DL','LB']` is counted as an LB even
  though `player_universe.player_position` buckets him DL, which is the slot family the engine
  fields him in. Recounted through the bucket the optimizer actually uses, every flagged HEAVY_IDP
  roster under a sharp strategy sits at LB 3 against a ceiling of 3.

## The two questions the report cannot answer, and the instruments for them

### 1. Under `noisy_k8`, whose decision was the over-ceiling hold?

`sharp_seats: []` means **every** seat draws uniformly from its own top 8, so no seat in that arm is
the sharp engine. `snap.candidates` is the engine's own order with surplus bodies sorted last by
`unfieldable_last`, so rank 0 means the engine ranked that player first and rank > 0 means the draw
reached past the engine's choice. `noise_replay.py` records the drawn rank on every pick of
`12T_ppr_K_DEF__noisy_k8` and asserts the replayed `pick_sequence` equals the report's before
reading anything.

- **Attributable to the noise model** if the over-ceiling picks are drawn at rank > 0. Then the arm
  measures what a uniform draw over eight candidates does to a roster, which is its purpose, and it
  is not evidence about the engine's ranking.
- **Attributable to the engine** if any over-ceiling pick was taken at rank 0. Then the board itself
  ranked a surplus body first and `unfieldable_last` did not bind — a real defect, and it goes back
  before the freeze.

### 2. Does it draft well on a varied field — meet or beat the chairs?

The battery grades structure, not quality. It drafted on the 2026 capture, for which no realized
season exists, so the realized ruler cannot be pointed at these arms at all. The instrument is the
**projected** analogue of the realized ruler: sum, over the 18 weeks on disk, each roster's best
legal starting lineup under `lineup_optimizer`, which is the same optimizer production fields.

**Stated as a limit, not buried:** this cannot show the engine picks better players than a
best-available chair, because both draft off the same projections. It shows whether the engine turns
the same numbers into a more fieldable, higher-scoring season of lineups — slot coverage, depth
where a bye or an absence needs it, and bodies it can actually play. **Value over BPA is what the
2023/2024 realized work speaks to; this speaks to structure on a varied field.** Two claims, two
rulers, and conflating them is how `#17` got withdrawn.

Two baselines, same pool, same pick order, same format, paired per seat:

| baseline | rule |
|---|---|
| `raw_bpa` | highest season projection available, position-blind. The strawman the owner named. |
| `sane_bpa` | best available at any position whose STARTING slot is not yet filled; once every slot is covered, best available overall. The honest human chair. |

**What passes.** Against `raw_bpa`: engine ahead in aggregate in every format. Against `sane_bpa`:
engine ahead in aggregate in every format **and** ahead on a majority of the 12 seats in each
format. Against either: a format where the engine loses is a finding that goes back before the
freeze, not a caveat on it.

**What is not evidence either way.** A format where `sane_bpa` and the engine produce the same
rosters — a tie there says the format gave the rule nothing to disagree about, exactly as the
battery's own `INERT_ARMS` say of an arm that reproduces its control. Reported as inert, not as a
pass.

**Which arms get graded.** The four noiseless strategies. A noisy arm's rosters are the draw's, not
the engine's, so grading them against a sharp baseline would measure the noise.
