# Deriving the flex share — pre-registered acceptance criterion

Written BEFORE any line of the change exists and before any measurement of a fixed engine. The
only thing measured so far is the instrument in this directory (`run_216_flex_share_probe.py`),
which reads no board and drafts nothing. Implementer: Opus. Base: `worktree-agent-ab5e1af412aeb9182`
@ acd1d66 (Fable's `displacement_adj` fix, shipped and suite-verified).

## What I intend to build (hypothesis, NOT yet measured against a board)

`starter_slot_counts` splits a flex slot's capacity evenly across the positions it admits, and
defends that in its docstring with a claim about the world that the instrument measures FALSE in
every format tried. Those counts set every replacement RANK, which picks the LEVEL that `bpa`
subtracts, so the error lands on every price.

1. **`fielded_flex_shares(pool, value_col, roster_positions, num_teams)`** — ONE home for "who
   wins each flex slot type in this league". One league-wide optimal fielding through the
   existing lineup optimizer (`num_teams` copies of every starting slot; eligibility from
   `fantasy_positions`), returning per-team occupancy per slot type, or `None` when it cannot be
   measured. No new solver (#126), no constant.
2. **`starter_slot_counts(roster_positions, flex_occupancy=None)`** — with occupancy, a flex
   slot's capacity goes to the positions that actually win it; without, the even split, exactly
   as today. Every existing caller that passes nothing keeps today's numbers.
3. **A basis companion** so a consumer can tell a MEASURED share from an assumed one, and so an
   assumed one cannot masquerade as measured. The absence contract applies here like everywhere
   else: the fallback is marked, never silent.
4. **Wiring**: `compute_draft_board` measures the occupancy ONCE from the pool it already prices
   and threads it into `remaining_starter_demand` and `replacement_levels`. The share is a
   STRUCTURAL property of the league and the pool, computed from the full pool, not recomputed
   as the draft drains — draining is already carried by `remaining_demand`, and doing it twice
   would double-count.
5. **`SUPER_FLEX_QB_SHARE = 0.85`** is measured 1.00 at every league size 8-16. When occupancy
   is measured, SUPER_FLEX stops being special-cased, because the measurement covers it. The
   constant survives ONLY as the no-pool fallback and may lose callers, never gain a sibling.

Rejected before measuring, with reasons: re-anchoring per SLOT at score time (a player is priced
once, and a per-slot price is a second ordering authority — #155); hand-setting a TE share per
format (the invented constant #56 forbids); reading occupancy off finished ROSTERS (circular —
they were drafted by the anchor under test).

## Gates. Measured with Fable's own probes, unedited, on 6 lab seats + 3 owner-league seats

- **H1 — the anchor lands where the instrument says.** With occupancy wired, the live
  `replacement_ranks` equal the DERIVED column of `TABLES_flex_share.md`: 12T_ppr TE 12 / WR 44 /
  RB 28; owner's league TE 18 / RB 26 / WR 40. Pure arithmetic. Failure means the wiring is
  wrong, not that the world is.
- **H2 — the owner's league fields a tight end, and does not hoard one.** At least 1 TE in no
  fewer than 2 of 3 seats (his own roster carries 2), AND no seat above the derived band's
  ceiling of 2. **A seat that comes back with four tight ends is a FAILURE, not a success** —
  that is the over-correction, the same defect wearing the opposite sign.
- **H3 — the lab does not regress.** In 12T_ppr and 12T_ppr_SF the per-seat TE count must not
  RISE in any seat and must FALL in at least 3 of 6; lineup points must not fall in any seat
  against the displacement-only arm.
- **H4 — legality survives.** `feasibility_first` still binds ZERO picks in every seat of every
  format, backstop OFF composition equal to ON (Fable's G1, unedited).
- **H5 — the owner's ordering.** `WR >= RB > TE` passes in no fewer seats than the
  displacement-only arm, in all three formats.
- **H6 — no new constant.** The diff introduces no numeric literal into the value path. If one
  turns out to be needed, I stop and say so rather than picking a number.
- **H7 — no silent behaviour change anywhere else.** Every existing caller of
  `starter_slot_counts` that passes no occupancy produces byte-identical numbers; the suite is
  the proof, and any test that changes is listed with the premise that moved.
- **H8 — suite green** (2710 + what I add), mutation-checked, survivors recorded.
- **H9 — the asset ruler, reported not resolved.** `total` / `floored` / `starter` on
  `run_216_asset_ruler_probe`'s three sets, engine-vs-engine and engine-vs-control, for
  displacement-only vs displacement+flex-share. A reversal against the control that the
  displacement-only arm did NOT already carry is a NEW failure and is reported as one. The
  exchange rate stays #50 and the owner's; I do not resolve it and I do not re-gate G9 on a
  ruler of my choosing.

## What makes me reject my own change

- H2 fails toward MORE tight ends than the band -> over-correction -> rejected.
- H3 regresses in any seat -> rejected, whatever the owner's league does.
- H4 fails -> the board still cannot draft a legal roster -> rejected.
- H6 fails -> stop, do not tune.
- H1 fails -> the wiring is wrong; fix the wiring, do not adjust the target.

## What partial success looks like, and how it will be reported

- The lab improves and the owner's league does not (or the reverse): reported as exactly that,
  per seat, with the ranks, and NOT presented as a fix. One format is not a result.
- The ranks move as H1 predicts but no composition changes: that would mean the anchor is not
  what drives the composition, which contradicts the whole #216 trace and would be reported as a
  contradiction of my own account rather than buried.

## The thing I must not do

I have published and withdrawn four mechanism claims on #216 already. This file exists so the
fifth is checked against a number before it is written down. No claim about what the fix DOES
belongs in any report until a probe has produced it.
