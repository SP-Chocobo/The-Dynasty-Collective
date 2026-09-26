# v2 Freeze Record — what was frozen, on what evidence, and what it does not claim

> Same standing as `FREEZE_RECORD.md` does for v1. `POST_AUDIT_PLAN.md` remains the numbered
> record and wins over any status flag anywhere (`#292`). Written to be read cold.

**Frozen commit: `43c8188`** on the branch this session was designated
(`git rev-parse --abbrev-ref HEAD` — derived, never restated, `#126`).

**Certified at that commit:** full suite **3512 tests, OK, 1761.3s**, `__pycache__` cleared first
per `#240`. `assertion_floors --check` clean over 196 modules.

The local tag sits at that commit exactly, and **this record is one commit past it** — the commit
that writes it down. No engine or test code differs: this commit adds only this file and
`DOC_INDEX.md`. So the tree frozen is the tree measured. Quote `43c8188` as the freeze.

## THE TAG IS CUT LOCALLY AND COULD NOT BE PUBLISHED

`v2-freeze` is an annotated tag at `43c8188` in this container, and the push was **refused with
HTTP 403** by the environment's gateway:

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

## What v2 carries that v1 did not, with the measurement that licensed each

| | change | licence |
|---|---|---|
| `#30` | streaming replacement floors for K and DEF, **derived** from the drafted season's own weekly projections | 2024 K 121.78 → 164.50, DEF 107.95 → 146.05. No constant selected |
| A | the fieldability ceiling (`unfieldable_last`): at most `slots(P) + 1` of a dedicated position | **Mandatory.** Removing it costs **−103.5/seat on 2023 with 0 of 12 seats improving**, and hoards past the ceiling at **12 of 12 seats on both seasons** — kickers in 2023, defenses in 2024 |
| `#35` | `cap_levels_at_best_remaining`: no replacement level may exceed the best player left at its position | **+21.7/seat (2024), +43.69/seat (2023)**, paired, on realized outcomes |
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

## Open at the freeze, named rather than omitted

- **`#21`** — blocked on `#50`.
- **`#29`** — the varied-drafting-strategy battery, stopped at 13 of 36 arms. Separate; ruled not
  to gate v2.
- **`#30` live-sync verification** — blocked by the environment's network policy on
  `api.sleeper.app` (403 on CONNECT). An environment issue, not an engine one.
- **`#35` / `pure_value`** — exercised, but never on a level-capped row, so that one consumer
  exposure is untested. Documented rather than claimed in either direction, by ruling.
- **A naming inversion, pre-existing and untouched:** `BALANCED_BOARD_COLUMNS` and
  `UPSIDE_BOARD_COLUMNS` are swapped relative to the branches that use them. Left alone at the
  freeze; it is why "on BOTH serializations" is the rule for any new companion column.

## What the freeze does NOT claim

That the engine is right about value. It claims the engine drafts **competitively** and in a
**fieldable shape**, on a ruler it cannot game, with every constant derived rather than chosen —
and that where a claim is untested, this record says so.
