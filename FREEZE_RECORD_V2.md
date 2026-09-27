# v2 FREEZE RECORD — what it rests on, what it does not claim, and what was left open

> **THIS IS THE FREEZE.** The owner's ordering held throughout: *"freeze is the last item before
> audit. if we find more tinkering to do, that happens before freeze."* The last gate ran, the one
> finding it raised was investigated to the arithmetic, the owner ruled it a post-freeze design item,
> and the freeze was cut on that ruling: *"No production tinkering. #35 remains closed. The VDS gate
> has done its job and has not found a production-engine defect… And then: freeze."*
>
> `POST_AUDIT_PLAN.md` remains the numbered record and wins over any status flag anywhere (`#292`).
> Written to be read cold.
>
> **THE HISTORY OF THIS FILE IS PART OF THE RECORD.** It first declared v2 frozen at `43c8188`, and a
> local `v2-freeze` tag was cut there. Both were premature — the varied-field battery had not run, and
> under the ordering above a battery finding sends work back before the freeze rather than after it.
> The tag was deleted, the file was rewritten as a CANDIDATE naming its outstanding gate, and it
> becomes the record only now. A marker naming a commit that is not the freeze is the stale-marker
> failure this repository has already had once, when a branch name in a skill file sent finished work
> to a branch nobody reads.

## THE LAST GATE, AND WHAT IT ACTUALLY DID

`#29`, the varied-drafting-strategy battery: 36 arms (6 formats × 6 strategies), 32 effective, 76
findings, 6h43m, with `weekly_projection_weeks: 18` and `streaming_floor_exercised: true` — checked
before any number was read, because the previous run of this battery drafted every arm with `#30`
dormant and said so in a field nobody read.

- **Structure: clean.** 49 of the 73 `unfieldable_depth` findings are the raw-vs-bucket position
  artifact `draft_battery._position_of` documents. Of the 24 survivors, 17 come from an all-noisy
  field, and a replay puts all 7 over-ceiling picks at drawn rank 5–7 of candidate lists 7–9 with
  **zero at rank 0** — the backstop ordered every surplus body last and only a uniform draw over a
  list shorter than `k` could reach them. In the five non-IDP formats the engine exceeds no ceiling
  under any noiseless strategy; `12T_ppr_SHORT_DRAFT` finished with zero findings under all six.
- **Quality vs position-blind best-available: +118 to +496 a seat, all six formats, 9–12 of 12 seats.**
  On the two formats with dedicated K/DEF/IDP slots it carries a third to a fifth as many
  never-fielded roster spots (K_DEF 0.50 against 1.67 and 3.25; HEAVY_IDP 0.67 against 1.00 and 3.75).
- **Quality vs a need-aware chair: the pre-registered bar is NOT met.** −10.1 to +23.8 a seat, 5–7 of
  12 seats. Recorded as a miss and not reframed. The gap is −0.2% to +0.9%; the ruler's own
  resolution, measured from the same run, is about 1%.
- **It found one weird branch and traced it to the arithmetic.** `sharp_upside` is worse on fieldable
  value in all six formats. The investigation established that its differentiator is inert (positive
  growth on 2.9% of 6794 board rows, argmax identical to plain `bpa` in all six formats, positive on
  2 of 87 real chosen picks), that it also loses on `proj_3yr` — the horizon it is derived from — in
  all six formats, and that `app.py` cannot reach the branch at all. Two design items were carried
  forward instead of being fixed under the freeze. Full record in `evidence/upside_gap/` and in
  `POST_AUDIT_PLAN.md`.

**Nothing in the gate changed production code.** The engine frozen here is the engine the gate
graded.

## THE FROZEN COMMIT AND ITS CERTIFICATION

**Frozen commit: see `FREEZE_CERTIFICATION` below** — filled in from the suite run, never from
memory, on the branch this session was designated (`git rev-parse --abbrev-ref HEAD` — derived, never
restated, `#126`).

**Relationship to the earlier candidates.** `43c8188` was the `#35` certification. `04bccb5` added the
battery's weekly-lines loader (`#30`'s wiring fix) and is the commit the battery ran at. `63c58a2`
certified the tree after the battery was read. Everything since is documents, arm reports, evidence
instruments under `evidence/`, and the doc index — **no engine or scoring module has changed since
`43c8188`**, which was enumerated from `git diff --name-only`'s own output rather than asserted, twice,
after getting it wrong twice.

## THE TAG: THE PUSH IS BLOCKED FROM HERE, SO CUTTING IT IS AN OWNER ACTION

No tag exists in this container. One was cut at `43c8188` early and **deleted** when the ordering
above was made explicit; nothing has been tagged since, deliberately, because the freeze commit was
not settled until the gate had run. Pushing a tag from here is **refused with HTTP 403** by the
environment's gateway:

```
error: RPC failed; HTTP 403 curl 22 The requested URL returned error: 403
send-pack: unexpected disconnect while reading sideband packet
```

Branch pushes to the same remote succeed; **tag pushes specifically are refused**, and the GitHub
tooling available here exposes no ref- or tag-creation call. This is the identical blocker the
earlier v2 attempt hit. The container is ephemeral, so **the local tag will not survive it** — this
file is the durable marker, and publishing the tag is an owner action. Use the commit named in
`FREEZE_CERTIFICATION` below rather than one quoted from anywhere else:

```
git fetch origin && git tag -a v2-freeze <FREEZE_CERTIFICATION commit> && git push origin v2-freeze
```

v1 was published as a GitHub **pre-release**; v2 has been through `#52`'s blind adversarial pass
and its nine-phase repair, so that qualifier no longer applies for the same reason.

## What the candidate carries that v1 did not, with the measurement that licensed each

| | change | licence |
|---|---|---|
| `#30` | streaming replacement floors for K and DEF, **derived** from the drafted season's own weekly projections | 2024 K 121.78 → 164.50, DEF 107.95 → 146.05. No constant selected |
| A | the fieldability ceiling (`unfieldable_last`): at most `slots(P) + 1` of a dedicated position | **Mandatory.** Removing it costs **−103.5/seat on 2023 with 0 of 12 seats improving**, and hoards past the ceiling at **12 of 12 seats on both seasons** — kickers in 2023, defenses in 2024 |
| `#35` | `cap_levels_at_best_remaining`: no replacement level may exceed the best player left at its position | **+21.70/seat (2024), +43.69/seat (2023)**, paired, on realized outcomes — measured on the SHIPPED composition (`shipped_cap_ab.py`), 9 of 12 and 8 of 12 seats improved, cap firing 1,461 and 1,392 times |
| `#31` | the backtest anachronism guard — pool **and** board trimmed | ~540 points a seat of false signal removed |
| `#34` | two absence repairs: a reachable `TypeError` on an unpriced engine pick, and a registered invariant (`absence_kind` iff no price) that was **false** on a drained superflex board | reproduced before repair in both cases |

## The ruler, and its limits

Realized outcomes — the sum of each week's best legal lineup over the drafted season's actual
stats. **The first grade in this repository the engine cannot optimise toward.**

Shipped configuration, 12 seats, `12T_ppr_K_DEF`: **2024 wins 11 of 12 at +82.89 mean**;
**2023 4 of 12 at −49.91**. Roster shape WR 5–7, RB 2–6, QB 2, K 2, DEF 2, TE 1; first K/DST
round 8–12.

**Limits, so no one quotes a total as an expected score:** no waivers or trades, and the weekly
lineup is an **oracle** — it starts the best actual scorers, not the ones a manager would have
guessed on Saturday. Every arm shares the advantage so comparisons survive it; the absolute totals
are ceilings. The oracle also **rewards** hoarding, which makes the ceiling's measured value a
lower bound rather than an upper one.

## One claim was withdrawn and then reinstated, on measurement

The `#35` figures above were first produced by an experiment arm that composed the slot alternatives
differently from production:

    graded arm:  alt(s) = min( max L_uncapped(p),  max b(p) )   over the slot's eligible p
    SHIPPED:     alt(s) = max( min(L(p), b(p)) )                over the slot's eligible p

`min`-of-maxes and `max`-of-mins are not the same function, and on a drained 2024 board **226 of 1034
rows differ, by up to 16.68 points** in `final_score` and in `displacement_adj`. So the figures were
**withdrawn** as claims about shipped code and the shipped configuration was graded directly:
`cap_levels_at_best_remaining` toggled to a no-op for the OFF arm, which reproduced the known pre-`#35`
baselines exactly on both seasons (2024 11/12 +82.89, 2023 4/12 −49.91).

**Result: the shipped composition drafts IDENTICALLY** — max |seat delta| **0.0**, **0 of 12** rosters
differing, on both seasons. The numbers are reinstated on measurement rather than on argument, and the
board-value difference is real but never reaches a pick on this data.

## Open at the freeze, named rather than omitted

- **`#21`** — blocked on `#50`.
- **`#29` — RUN AND READ.** All 36 arms at `04bccb5`, `#30` exercised. Clean on structure, decisive
  over position-blind best-available, and a recorded MISS against the pre-registered bar for a
  need-aware chair (−0.2% to +0.9%, at or under the ruler's own ~1% resolution). Not open any more;
  the two findings it raised are the next two entries.
- **`#184` — `sharp_upside`'s differentiator is inert. A design item, ruled post-freeze by the
  owner.** Positive growth on 2.9% of 6794 board rows, argmax identical to plain `bpa` in all six
  formats, positive on 2 of 87 real chosen picks; and it loses to `sharp_auto` on `proj_3yr` — the
  horizon it is derived from — in all six formats. Not a broken implementation: the arithmetic does
  what its docstring says. The work is a DERIVED percentile-to-points conversion, since the ±10 clamp
  was borrowed from `time_horizon_adj` precisely because `#56` forbids calibrating one.
  `evidence/upside_gap/`.
- **The upside board's flat region.** 8 of 87 states have its top decided by `player_id` among
  candidates tied at value exactly 0.00, against 0 of 87 in balanced mode at the identical states, and
  what is tied is not equivalent. **`app.py` cannot reach the branch** — every `build_snapshot` call
  site omits `mode`, AST-audited. Carried forward as a separate finding; no measurement here licenses
  a replacement ordering, which is why nothing was changed under the freeze.
- **`#30` live-sync verification** — blocked by the environment's network policy on
  `api.sleeper.app` (403 on CONNECT). An environment issue, not an engine one.
- **`#35` / `pure_value`** — exercised, but never on a level-capped row, so that one consumer
  exposure is untested. Documented rather than claimed in either direction, by ruling.
- **A naming inversion, pre-existing and untouched:** `BALANCED_BOARD_COLUMNS` and
  `UPSIDE_BOARD_COLUMNS` are swapped relative to the branches that use them. Left alone at the
  freeze; it is why "on BOTH serializations" is the rule for any new companion column.

## What the candidate does NOT claim

That the engine is right about value. It claims the engine drafts **competitively** and in a
**fieldable shape**, on a ruler it cannot game, with every constant derived rather than chosen —
and that where a claim is untested, this record says so.

On the varied field specifically, stated at the precision the evidence supports and no further: the
engine **beats position-blind best-available in all six formats by 118 to 496 points a seat**, and it
**ties a need-aware best-available chair** at −0.2% to +0.9%, which is at or under the resolution that
same run demonstrates. It does **not** claim to beat a need-aware chair on that ruler. The
value-over-best-available claim rests on the 2023/2024 REALIZED work, not on this battery.

And it does not claim `mode="upside"` is a working strategy. It claims production never uses it, that
its differentiator was measured inert, and that two named design items were carried forward rather
than tuned away under a freeze.

## FREEZE_CERTIFICATION

Filled in from the suite's own output. The full suite is what licenses this, never a subset, with
`__pycache__` cleared first (`#240`).

- **Frozen commit:** `PENDING — the suite is running`
- **Full suite:** `PENDING`
- **`assertion_floors --check`:** `PENDING`
- **`doc_index --check`:** `PENDING`

This record is one commit past the certified tree — the commit that writes the result down — and the
only difference is this section and `DOC_INDEX.md`. The commit named above is the freeze.
