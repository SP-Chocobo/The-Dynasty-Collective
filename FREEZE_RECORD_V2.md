# v2 Freeze CANDIDATE — what it rests on, what is still gating it, and what it does not claim

> **THIS IS NOT YET THE FREEZE.** The owner's ordering: *"freeze is the last item before audit. if we
> find more tinkering to do, that happens before freeze."* So this document stands where
> `FREEZE_CHECKLIST.md` stood for v1 — what is left *before* — and becomes the record, in
> `FREEZE_RECORD.md`'s shape, once the freeze is actually cut. `POST_AUDIT_PLAN.md` remains the
> numbered record and wins over any status flag anywhere (`#292`). Written to be read cold.
>
> **CORRECTED.** This file first declared v2 frozen at `43c8188` and a local `v2-freeze` tag was cut
> there. Both were premature: the varied-field battery had not run, and under the ordering above a
> battery finding sends work back before the freeze rather than after it. **The tag has been
> deleted** — a marker naming a commit that is not the freeze is the stale-marker failure this
> repository has already had once, when a branch name in a skill file sent finished work to a branch
> nobody reads. Nothing is tagged until a commit clears the gate.

**THE GATE HAS RUN.** The varied-drafting-strategy battery (`#29`) completed all 36 arms at
`04bccb5` — 32 effective, 76 findings, 6h43m, with `streaming_floor_exercised: true` and 18 weeks of
lines, so `#30` fired. Full reading: `evidence/design_35/RESULT_VDS.md`. What it settled and what it
did not:

- **Structure: clean.** 49 of the 73 `unfieldable_depth` findings are the raw-vs-bucket position
  artifact `draft_battery._position_of` documents, not engine behaviour. 17 of the 24 survivors come
  from an all-noisy field, and a replay puts every one of the 7 over-ceiling picks at drawn rank 5–7
  of candidate lists 7–9, **zero at rank 0** — the backstop ordered them last and only a uniform draw
  over a list shorter than `k` could reach them. In the five non-IDP formats the engine exceeds no
  ceiling under any noiseless strategy; `12T_ppr_SHORT_DRAFT` finished with zero findings under all six.
- **Quality vs the strawman: decisive.** +118 to +496 a seat over position-blind best-available in all
  six formats, 9–12 of 12 seats. On the two formats with dedicated K/DEF/IDP slots it carries a third
  to a fifth as many never-fielded roster spots.
- **Quality vs a need-aware chair: THE PRE-REGISTERED BAR IS NOT MET.** −10.1 to +23.8 a seat, 5–7 of
  12 seats. Recorded as a miss, not reframed. The gap is −0.2% to +0.9% and the ruler's own resolution,
  measured from the same run, is ~1%.

**ONE DECISION IS OUTSTANDING, AND IT IS THE OWNER'S** (`#184`): upside mode (`mode="upside"` from
round 1) is worse on fieldable value in **all six formats**, by 20.8 to 86.6 a seat, ahead on only
2–5 of 12 seats. Same direction, six formats, no exceptions. Under the owner's own ordering — *"if we
find more tinkering to do, that happens before freeze"* — that is a finding that can send work back
before the freeze, so **the freeze is not cut here.** Separately and non-blocking: the `#261`
crossing rule is unexercised by this battery (`picks_with_growth_measured` is 0 for every `crossing`
arm in every format), so a listed axis of the run covers nothing.

**Candidate commit: `63c58a2`** on the branch this session was designated
(`git rev-parse --abbrev-ref HEAD` — derived, never restated, `#126`).

**Certified at that commit:** full suite **3512 tests, OK, 1026.4s**, `__pycache__` cleared first per
`#240`. `assertion_floors --check` clean over 196 modules, `doc_index --check` current. The run
before it, at `cb87404`, FAILED on one test — `test_doc_index_is_not_stale`, caused by this session's
own doc additions and fixed by running the generator the failure message names. Recorded because a
certification that mentions only the passing run is not a certification.

**What differs from the earlier candidate `43c8188`, enumerated from the command's own output rather
than from memory:**

```
$ git diff --name-only 43c8188 63c58a2
23 paths; .py files: evidence/design_35/bpa_projected_ruler.py,
evidence/design_35/idp_bucket_recount.py, evidence/design_35/noise_replay.py,
evidence/design_35/shipped_cap_ab.py, run_draft_battery.py
```

Four of the five `.py` files are instruments under `evidence/`; the fifth is `run_draft_battery.py`,
the battery's weekly-lines loader (`#30`'s wiring fix). **No engine or scoring module differs**, so
the engine certified here is the engine certified at `43c8188`. Everything else is a document, an arm
report or the doc index.

## THE TAG: NOT CUT, AND THE PUSH IS BLOCKED ANYWAY

No tag exists. One was cut at `43c8188` and **deleted** when the ordering above was made explicit.
Separately, and still true whenever a tag IS cut: pushing it is **refused with HTTP 403** by the
environment's gateway:

```
error: RPC failed; HTTP 403 curl 22 The requested URL returned error: 403
send-pack: unexpected disconnect while reading sideband packet
```

Branch pushes to the same remote succeed; **tag pushes specifically are refused**, and the GitHub
tooling available here exposes no ref- or tag-creation call. This is the identical blocker the
earlier v2 attempt hit. The container is ephemeral, so **the local tag will not survive it** — this
file is the durable marker, and publishing the tag is an owner action:

```
git fetch origin && git tag -a v2-freeze 43c8188 && git push origin v2-freeze
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
- **`#29` — the varied-drafting-strategy battery. RESTARTED, all 36 arms, against this frozen
  commit.** The earlier 13 were discarded rather than resumed: they predate `#35`, the `absence_kind`
  repair and the `draft_counterfactual` fix, and pairing new arms against stale ones is the rule this
  repo states as "never resume onto a report written by different code". **This is the one bar the
  freeze does not yet clear** — meet-or-beat on a varied field, which the realized-outcome grader
  structurally cannot see because it fields a fixed two-style table. The gate that authorised the
  restart is `evidence/design_35/GATE_FOR_VDS.md`, fixed before the A/B was read.
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
and that where a claim is untested, this record says so. **It does not yet claim the varied-field
bar is met**; that is what the running battery decides, and a finding there is tinkering to be done
*before* the freeze, not a footnote after it.
