# Pre-registration: what I expect the guarded re-run to show

**Written while the base arm was still running, after reading seats 1–4 and before any
streaming-arm seat was printed.** Committed so the prediction cannot be edited after the fact.

## The state at the time of writing

Guarded 2024 base arm, `12T_ppr_K_DEF`, 573 draftable (101 dropped by `period_correct_pool`):

| seat | engine | field | delta | first K/DST |
|---:|---:|---:|---:|---:|
| 1 | 2085.5 | 2774.2 | **−688.7** | 4 |
| 2 | 2217.1 | 2760.4 | **−543.3** | 4 |
| 3 | 2183.0 | 2758.9 | **−575.9** | 4 |
| 4 | 2156.8 | 2761.6 | **−604.7** | 4 |

Before the guard, the same arm was 7/12 wins at mean −15.4. So **the ghost players were
flattering the engine relative to the field**, and removing them exposes a large, consistent
deficit against a plain `need_first` / `points_need` field. That is the owner's actual question
— "is this thing good at drafting" — and the honest current answer on this ruler is **no**.

## What I think is causing it

`bpa` is Value Over Replacement in the DRAFTED SEASON's own projected points
(`points_vor_sleeper_season_scored`), so the engine's anchor and the field's ranking read the
same period-correct signal. The loss is therefore **not** a valuation-source problem. It is an
allocation problem, and the visible allocation defect is right there in the table: **every seat
takes its first K or DEF in round 4.** Two of the first ~5 picks go to positions whose realized
contribution is a fraction of a skill player's, in a ruler that rewards depth.

## The prediction

1. **The streaming arm closes most of the gap.** If the round-4 K/DEF pick is the dominant
   cause, moving first K/DST to rounds 8–13 should recover on the order of **400–600 points a
   seat**, not the +226.6 the confounded run measured — because on the clean pool the deferred
   picks now buy real players instead of ghosts.
2. **It does not close all of it.** I expect the streaming arm to still trail the field, because
   two further horizon effects remain and neither is touched by `replacement_levels`:
   the dynasty `time_horizon_adj` (258 of 1181 rows) and the depth reward this ruler gives.
3. **Falsifier.** If the streaming arm recovers less than ~200 a seat, K/DST placement is NOT
   the dominant cause and I am looking in the wrong place — the next probe is a roster-level
   diff of one engine seat against one field seat, position by position, not more valuation work.

## What happens either way

- The `--redraft` arm (`redraft_league`, shipped alongside this) runs next regardless. It is the
  only way to separate "the engine paid for a future season on purpose" from "the engine drafts
  badly", and neither arm may be quoted without the other.
- `#30` stays BLOCKING until the guarded numbers exist. The freeze does not move on the
  confounded ones.
