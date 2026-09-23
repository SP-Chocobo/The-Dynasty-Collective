# VDS interim: the backstop caps exactly where it should, and nowhere else

Run `VDS_2026-09-23_varied_drafting_strategy_fb83e84.json`, in flight. Seven of 36 arms.
Recorded now rather than at the end because the two formats that matter most are already done,
and a multi-hour run should not hold its own answer hostage.

## The format where the backstop applies — `12T_ppr_K_DEF`, sharp control

All twelve chairs, position counts at the ceilinged positions:

```
K     2 2 2 2 2 2 2 2 2 2 2 2      ceiling 2
DEF   1 1 1 1 2 2 2 2 2 2 2 2      ceiling 2
QB    1 1 1 1 1 2 2 2 2 2 2 2      ceiling 2
```

**Not one chair of twelve exceeds the ceiling at any ceilinged position.** Against the base
engine's **nine defenses** on the same format (`evidence/kdst_streaming/ROOT_CAUSE.md`), that is
the hoarding gone — league-wide, not just in the seat that was measured.

An example finished roster: `RB 2, WR 5, QB 1, TE 4, K 2, DEF 2`. Sixteen players, every
starting slot coverable, depth sitting in the flex-reachable positions where it can actually be
fielded.

## The format where it must NOT apply — `12T_ppr_SF`, sharp control

```
QB    2 2 2 2 2 2 2 3 3 4 4 4      no ceiling: SUPER_FLEX makes QB flex-reachable
```

Every chair carries two to four quarterbacks, which is what a superflex roster should look like.
**`#20`/`#22` was an under-drafting-QB-in-superflex regression**, caught late by a different
instrument, and it is the specific failure this change had to avoid. It is not present: the
backstop derives no ceiling for QB there, so it cannot fire, and the engine drafts the position
the way the format demands.

That is the pair the whole design rests on — a cap where a body provably cannot be fielded, and
silence where depth is real — confirmed on live drafts rather than on fixtures.

## Findings so far: 1 of 7 arms

`12T_ppr_K_DEF__noisy_k8`, seat 2: three kickers against a ceiling of two. The five other arms of
that format returned zero, including all three sharp strategies and `crossing`. Under
`opponent_noise` the non-sharp seats choose uniformly from their own top_k rather than taking the
board's leader, so the ordering was overridden before the pick — the finding is true about the
roster and is evidence about the noise axis, not about the engine's board. See
`draft_battery.structural_findings`' own qualification.

**A finding on a CONTROL arm would be the one that means something.** None so far.

## What this run does NOT certify

`universe.weekly_projection_weeks = 0`, `universe.streaming_floor_exercised = false`. The
committed capture predates weekly projection lines, so this battery validates the board WITHOUT
`#30`'s streaming floor. The evidence for that half is the backtest, not this.
