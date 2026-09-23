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

## The second finding, traced: superflex prices NO quarterback from round 15

`12T_ppr_SF__noisy_k8` took two `tav=None` backup QBs at 15.08 and 15.10. Replaying that arm's
own pick sequence to the round-15 board:

```
QB rows remaining: 102      unpriced: 102      replacement_basis: {None: 102}
top 12 of the board:        WR/RB, every one priced from predraft_anchor
unpriced rows in the top 12: 0
```

**Every remaining quarterback is unpriced, and that is BY DESIGN.** In a superflex league
`compute_draft_board` passes `startable_floors={"QB": ...}`, and `_fill_omitted_from_anchor`
deliberately fills positions omitted for EXHAUSTED DEMAND while never filling those the
startable-floor branch DECLINED — "no remaining player clears the startability threshold" is a
different fact from "this position's demand is used up", and the anchor is only the answer to
the second.

So the board is behaving as specified, and `_board_order` sorts unpriced rows last, which is why
all five other superflex arms are clean: the engine never takes one. Under `noisy_k8` the seat
does not take the board's leader — it draws uniformly from its own narrowed top_k, and the
narrowed list carries some QBs for positional depth. The unpriced row is reachable by a random
draw and by nothing else.

**Not caused by anything in this session, and that is checkable rather than asserted:**
`fieldable_ceiling('12T_ppr_SF')` is `{}`, so `unfieldable_last` returns all-zero,
`cannot_be_fielded` is constant `False`, and `_board_order` is element-for-element what it was.
The streaming floor is not exercised at all (`weekly_projection_weeks = 0`).

**What is worth the owner's attention anyway:** from round 15 a superflex board prices no
quarterback at all — 102 rows with `final_score=None`. The engine handles it. Any consumer that
reads the board without honouring `final_score is None` would not, and the noisy arm is a live
demonstration of what that looks like.

## What this run does NOT certify

`universe.weekly_projection_weeks = 0`, `universe.streaming_floor_exercised = false`. The
committed capture predates weekly projection lines, so this battery validates the board WITHOUT
`#30`'s streaming floor. The evidence for that half is the backtest, not this.
