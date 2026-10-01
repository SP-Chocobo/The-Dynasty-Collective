# ADVISORY (Fable) — the per-seat correlated resolution of near-ties

**Status: ADVISORY. Read-and-think mandate — no probe, no draft, no test, no file modified,
no code written. Prose only.** Recorded verbatim as received. Nothing in it is a measurement
and nothing in it is authorized work. Where I have since checked one of its claims, the check
is recorded in its own document and cited below.

## What I have checked since

- Its **RESIDUAL3 criticism is CONFIRMED** against `residual3_raw.json` — see
  `WITHDRAWAL_18_residual3_detector.md`. `adj == 0.0` fired 0 of 144 times because the
  predicate was arithmetically unreachable, not because the mechanism was quiet.
- Its **candidate mechanism #1 (pool contention between snake neighbours) SURVIVES its own
  falsifier** — see `RESIDUAL5_THE_TOTAL_IS_CONSERVED.md` Part 2. Balanced arm lag-1
  r = −0.487, P = 0.0495; both auto arms null, as it predicted.
- Its claim that `team_acquisition_value` decomposes into five subterms is **not this
  engine**: `draft_strategy.py:647` sets `team_acquisition_value = my_row["final_score"]`.
  The seven-term reconciliation in RESIDUAL4 already IS its full decomposition. (This
  correction applies to a separate advisory, not to Fable's — recorded here to keep both
  in one place.)
- Everything else below is **unchecked**.

---

I've read the scoreboard, the four residual documents, `score_row`, `displacement_level`'s contract, `shared_slot_alternatives`, the percentile setup, and the final sort. Prose only from here.

## One derivation that reframes everything below

`displaced` for a candidate at position P is `min` over the cheapest thing P's probe can evict along the chain: P's dedicated slot(s) and the shared FLEX slots. So for a TE-vs-WR near-tie the roster-dependent quantity is not `d_te` but **Δd = d_alt − d_te**, and Δd is non-zero **only when the cheapest reachable holder sits in a DEDICATED slot**. If the weakest reachable player is in a FLEX, both probes evict him and Δd = 0 — the decision is pure `points`, seat-independent. That is consistent with everything you measured: displaced at pick 9 is either 217.75 (the flex phantom — `max(levels)` from `shared_slot_alternatives`) or a number below it (200.90, 209.20, 213.93, 211.65, 212.03), and every value below 217.75 can only be a seat's own TE1 sitting in the one dedicated TE slot.

The asymmetry that matters: TE has ONE dedicated slot, WR has several, and after round 9 the pool contains no TE that beats an incumbent TE1. So a weak TE1 pins `d_te` for the rest of the draft (a drafted TE2 weaker than TE1 goes to bench or flex and changes nothing), whereas a weak WR3 is replaced by the next WR taken and `d_wr` self-heals. A one-slot position has a sticky pin; a multi-slot position has a transient one. None of your probes measured Δd — RESIDUAL2 measured `d_te` alone, RESIDUAL4 measured margins pooled by outcome.

## (a) Ranked candidate mechanisms

**1. Pool contention between snake neighbours at near-ties (coupling through `points`, not `displaced`).** Look at the final counts in seat order: 1, **9**, 1, 4, **9**, 3, 7, 1, **14**, 2, 2, **15**. Every hoarder is flanked by starvers: 2:(1,3), 5:(4,6), 9:(8,10), 12:(11). My back-of-envelope lag-1 neighbour autocorrelation is about −0.5 on the linear lattice (12 and 1 are not adjacent in a snake; 12 picks twice in a row). Mechanism: at a near-tie the hoarder takes the top remaining TE immediately before its neighbour picks; the neighbour's TE alternative is now one rung worse, loses its near-tie, takes the WR; next round the hoarder's WR alternative is one rung worse and its TE wins again. Two seats running identical code, each depleting exactly the position the other would have taken. This is per-seat correlated, needs no roster term, and only appears in the balanced arm because only there does the level cancel and produce the near-tie (upside mode hands TE a flat +68 and everyone hoards evenly, 5–12 — which is what AUTO shows). **Falsifier:** permutation test of the lag-1 neighbour autocorrelation over the 12! seat labellings; if not significantly negative, dead. Second falsifier: at each hoarder TE pick in 9–20, the taken TE was not the top remaining TE by points, or the immediately-following neighbour's TE-minus-alt margin is not degraded by roughly the rung gap. **Cost:** cheap, saved data only.

**2. The dedicated-slot pin, Δd.** Pre-register: at each seat's picks 9–12 (before the counts separate), compute Δd from the two board rows RESIDUAL4 already saved (the chosen/top TE row and the top non-TE row each carry `displacement_adj`, and the level is known, so `d_alt` and `d_te` fall out arithmetically), plus WHICH slot the TE probe's evictee occupies (dedicated vs flex, player vs phantom — the optimizer's returned dict should name it). Prediction: hoarders show Δd > 0 with the evictee in the dedicated TE slot. **Falsifier:** Δd at picks 9–12 does not separate the groups, or the TE evictee is a flex holder for hoarders as often as starvers. **Cost:** cheap read if the full rows were saved; otherwise 48 board rebuilds from saved rosters.

**3. Per-pick pivotality of the "small" terms.** Your "near-noise at the mean" judgement was made against the 70-point scale, but those 70 points cancel; the decision scale is the residual, 0.01–13 points, and against it `depth_exposure` (group means −0.38 vs −2.57), `need_bonus` (0.15 vs 0.61) and `time_horizon_adj` (±10) are all first-order. Note `depth_exposure` is only `measured` once a bench exists — round 9 — exactly the divergence onset, and its basis is `no_surplus` (hard 0.0) for a seat with one TE and `measured` once a surplus exists: an asymmetry by construction between seats that have and have not taken a second TE. `need_bonus`'s flex-share gives TE a relative +1.0 over WR for any WR-heavy seat until TE count ≥ 4. **Measure:** for each of the 67 decision picks, per term, "pivotal" = zeroing that term's margin flips the sign of the net margin. Count per term per seat. **Falsifier:** no term other than points/displaced is pivotal in more than a handful of picks. **Cost:** cheap, the seven-term reconciled data already exists.

**4. Pool-rank percentiles inside `time_horizon_adj`.** `_season_proj_pct` and `_proj3yr_pct` are `rank(pct=True)` over the REMAINING projected pool at build time (draft_room ~2929/2950), so a player's adjustment drifts pick-to-pick as the pool drains, and drifts differently by position depending on 3yr coverage. Seat-independent given the pool state, so it cannot produce per-seat correlation by itself — but it can decide individual near-ties, and adjacent seats (near-identical pool state) are the natural control. **Falsifier:** `time_horizon` margin pivotal in ≈0 picks, or identical sign for adjacent seats at matched picks. **Cost:** cheap.

**5. Exact ties at 2dp broken by `player_id` ascending.** `universal_value` and `final_score` are rounded to 0.01; observed margins are 0.01. An exact tie goes to the lowest Sleeper ID, i.e. the veteran. Seat-independent but systematic. **Falsifier:** zero decisive picks with net margin exactly 0.00. **Cost:** trivial.

## (b) Ruled-outs closed too fast

- **RESIDUAL2's "identical −68.58 at the 5th pick."** That number is `149.17 − 217.75`: the TE level minus the flex phantom. Every seat's TE probe evicts the phantom at pick 5. It is a measurement of a constant, so identity between groups carries zero information about feedback. And the pick-9 table compared `d_te` magnitudes across seats when the discriminant is Δd within a seat.
- **RESIDUAL3's "open-slot mechanism fires 0 times."** The detector was `adjustment == 0.0`, which under `slot_alternatives` can only fire when the DEDICATED TE slot is open — impossible after pick 9. The docstring's open-slot case in its flex form is `displaced == a phantom value` (217.75), and RESIDUAL2's own table shows it firing for seats 1, 9, 10, 11 at pick 9. Re-detect with `displaced ∈ values(slot_alternatives)`. (Caveat: when the phantom is the evictee, Δd = 0, so this is the neutral case, not a TE-favouring one — but "never fires" is wrong.)
- **The timing proxy.** "When TE1 was taken" is a proxy for TE1's quality; the trait that pins Δd is TE1's points relative to the flex phantom / weakest flex holder. Measure that trait at pick 9 directly.
- **Draft-slot position.** You checked early-vs-late; the signature here is neighbour alternation, a different slot-position structure entirely.
- **The mode boundary** is correctly excluded as the cause on this arm — but it is evidence for #1: removing roster terms removes the near-tie, and with it the bimodality.

## (c) Structural possibilities not yet named

Your premise — "any within-seat coupling must flow through `displaced`" — is false in one draft. `points` of the best available at each position is a function of the pool, and the pool at seat s's picks is a function of s's neighbours' choices, which are functions of s's choices. That is a reinforcement loop with no roster term in it (#1). The second unnamed channel is the slot-count asymmetry (#2): the chain min over 1 + F slots vs 3 + F slots, and the stickiness of a one-slot pin. Third: `depth_exposure`'s basis gate (`no_surplus` → hard 0.0) makes a term appear only after the first surplus body at a position — a step function keyed to the very event you are trying to explain. Fourth, minor: the percentile nonstationarity in `time_horizon_adj` means the "same" player is scored differently by the same seat at consecutive picks for reasons unrelated to either roster or projection.

## (d) Reinforcement vs twelve clustered coin flips

Within one draft you cannot make a population claim, but you can test exact nulls by permutation, and three of them separate the hypotheses:

1. **Homogeneous-binomial null.** With pooled p ≈ 33/144 over picks 9–20, two seats at 8/12 and three at 0/12 is far into the overdispersed tail (a chi-square on per-seat counts, or simulate). This kills "same p, independent flips" but not "per-seat p differs due to a fixed trait".
2. **Spatial null.** Independent flips, and fixed per-seat traits, both predict zero neighbour autocorrelation. Only a between-seat coupling (pool contention) predicts negative lag-1. Permutation over seat labels is exact and cheap.
3. **Temporal null, within seat.** Fixed trait predicts the pivotal term's margin is flat across a seat's picks; reinforcement predicts it trends with the seat's cumulative TE count (and with the neighbour's cumulative WR count). A Markov check — P(TE at k | TE at k−1) vs P(TE at k | not) — is the crude version.

The decisive experiment, if you can afford one 312-pick re-run: a butterfly test. Force a single near-tie pick (a hoarder's 10th, margin +0.01) the other way and re-run untouched. Independent flips move one count by one; reinforcement moves that seat's count by several AND moves its neighbours' counts in the opposite direction. That is a measurement of the production quantity, not a calibration, and it pre-registers cleanly: state the predicted signs for the perturbed seat and both neighbours before reading.

Suggested order given the discipline: #1's permutation test and #3's pivotality count first (both are reads of saved data and each can kill or promote several ideas at once), then #2's Δd at picks 9–12 pre-registered, then the butterfly re-run only if #1 and #2 both survive.
