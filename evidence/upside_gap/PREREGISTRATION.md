# `sharp_upside` — what the −20.8 to −86.6 actually represents

Owner's ruling: *"First determine what the result actually represents… Do not modify production code
unless the investigation establishes a real defect."* Four candidate readings were named, and this
file fixes what would distinguish them **before any of the measurements below were run**. Investigated
against the frozen candidate `63c58a2`; no production code is touched by this investigation.

## What the code says before anything is measured

Read, not measured, and recorded first so a later number cannot be mistaken for the source of these
facts:

1. **`upside_score` computes `final_score = bpa + growth_points`**, where
   `growth = max(0.0, proj3yr_pct − season_pct)` gated on `_has_3yr`, and
   `growth_points = clamp(UPSIDE_GROWTH_WEIGHT × growth, TIME_HORIZON_CLAMP)` with
   `UPSIDE_GROWTH_WEIGHT = 0.5` and `TIME_HORIZON_CLAMP = (−10.0, +10.0)`.
   So the term that makes upside mode *upside* **can move a candidate by at most 10 points**, and it
   is ADDED to `bpa` — season points above replacement — rather than substituted for it. Upside mode
   is not a different horizon; it is season value with a capped tilt.
2. **The upside branch removes every roster-aware term.** Its own comment: *"upside_score reads
   nothing off the roster… the layer identity holds with all three team-specific terms at 0.0"*, and
   *"this branch has no roster awareness of any kind"*. `need_bonus`, `eligibility_bonus`,
   `depth_exposure`, `displacement_adj`, `time_horizon_adj` and `risk_adj` are all absent. What
   remains above value is only the two hard structural backstops, `feasibility_first` and
   `unfieldable_last`, and the final order is
   `["_feasible", "_unfieldable", "final_score", "player_id"]`.
3. **Production never enters this branch.** All three `build_snapshot` call sites in `app.py`
   (lines 5003, 5067, 5460) omit `mode`, and the `**snapshot_inputs` dict at 5431–5445 has no `mode`
   key, so `build_snapshot`'s default `mode="balanced"` applies; it threads that same value into
   `compute_draft_board` and into `pick_analysis` → `_build_opponent_boards`, so the rival boards are
   balanced too. `detect_positional_run` takes no mode and builds no board. Audited by AST over the
   call sites rather than by reading for the word "upside". The upside branch is reached by
   `draft_simulation.simulate_full_draft` (default `mode="auto"`, upside from round 15) and by an
   explicit `mode="upside"` — batteries and instruments, not the app.

## The four readings, and what decides between them

| | reading | what would establish it |
|---|---|---|
| **H1** | an intentional horizon tradeoff | the same rosters come out AHEAD for `sharp_upside` on a multi-year ruler. Measured as the best legal starting lineup under `proj_3yr`, per seat, paired. H1 holds if `sharp_upside` beats `sharp_auto` there in a majority of the six formats. |
| **H2** | the projected fieldable ruler cannot see upside's objective | the objective is a horizon the ruler does not span. Bounded rather than argued: the growth tilt's TOTAL possible contribution is ≤10 points per pick, and its ACTUAL contribution is observable per arm. H2 holds only if the realised tilt is large enough to account for a material share of the 20.8–86.6 gap. |
| **H3** | an interaction that systematically overvalues the upside behaviour | the differentiating term is inert while roster awareness is discarded, so the mode is roster-blind season-VOR wearing another name. H3 holds if `growth_points` is 0 for the overwhelming majority of chosen picks AND for the top of the board. |
| **H4** | a genuine optimization defect | the board cannot discriminate: `final_score` ties across the top of the board once positions are capped (`bpa` is exactly 0.00 for a capped position's best remaining), leaving `player_id` as the operative tiebreak. H4 holds if a material share of upside picks are decided by that tiebreak among candidates with equal `final_score`. |

H3 and H4 are not exclusive, and neither is H1 with H2. The ruling the owner asked for turns on one
thing: **is there an engine-level defect that reaches production?** Reading 3 above already bounds
that, and the measurements below are what say whether a defect exists at all.

## Measurements to run

- **M1 — degeneracy and the growth term, on real drained boards.** Build upside-mode and
  balanced-mode boards at the same real drained states from the frozen candidate, and report: the
  share of the pool with `_has_3yr`; the distribution of `growth` and `growth_points`; how many
  top-of-board rows tie at `final_score`; and whether the top row is the lowest `player_id` in its
  tied group. Non-vacuity: `n` printed for every population.
- **M2 — the multi-year ruler.** Re-grade the committed VDS rosters (no re-drafting) on the best
  legal starting lineup under `proj_3yr`. Limit stated up front: `proj_3yr` is a season-total-shaped
  outlook with no weekly lines, so this is ONE solve, not a weekly one, and it cannot see absences.
  It is the only multi-year number this repository has.

## What I will not do

Tune toward the result. If H1 or H2 holds, the answer is "behaving as designed" and the engine is not
touched. If H4 holds, the finding is stated with its production reachability attached — a defect on a
path the app cannot reach is still a defect, but it is not a reason to change the engine before a
freeze unless the owner rules that way.
