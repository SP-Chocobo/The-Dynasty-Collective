# #153: `need_bonus` collapses roster states at TWO clamps, not one — and the register names the wrong one

The register records #153 as "`need_bonus`'s own **cap** collapses two distinct roster states in a
4WR format." The formula has two clamps, and the one that fires in the 4WR case is not the cap.

```python
need_bonus = round(min(
    NEED_BONUS_PER_DEDICATED_SLOT * dedicated_needed          # 4.0 per owed dedicated slot
      + NEED_BONUS_PER_FLEX_SHARE * min(flex_remaining, 1),   # 1.0 x a share clamped at ONE
    NEED_BONUS_MAX,                                           # 12.0
), 2)
```

## Both collapses, measured

**Clamp A — `min(flex_remaining, 1)`.** Holding `dedicated_needed = 0`:

| `flex_remaining` | 0 | 0.5 | **1** | **1.5** | **2** | **3** | **5** |
|---|---|---|---|---|---|---|---|
| `need_bonus` | 0.00 | 0.50 | **1.00** | **1.00** | **1.00** | **1.00** | **1.00** |

**Clamp B — `NEED_BONUS_MAX`.** Holding `flex_remaining = 0`:

| `dedicated_needed` | 0 | 1 | 2 | **3** | **4** | **5** | **8** |
|---|---|---|---|---|---|---|---|
| `need_bonus` | 0.00 | 4.00 | 8.00 | **12.00** | **12.00** | **12.00** | **12.00** |

## Which one is the 4WR case

**Clamp A.** A 4WR format gives WR four dedicated slots *plus* a large share of the FLEX slots, so
`flex_remaining` routinely exceeds 1 — and every roster above that threshold is priced identically.
That is the collapse the battery carries `4WR_TE_PREMIUM` to observe, and it is a clamp on the
flex **share**, not the cap.

Clamp B is real too and the register does not mention it: a roster owing **three** dedicated slots
at one position is priced the same as one owing **eight**. A 4WR roster reaches `dedicated_needed
= 4` from empty, so this saturates in round one of exactly the format #153 names.

## The important qualification — and why this does NOT contradict the docstring

`estimated_bench_demand`'s neighbouring docstring says "the whole reachable `need_bonus` is 8.67
and its cap never binds (`NEED_BONUS_MAX` at 1e9 is pick-for-pick identical)."

That reads as a contradiction of Clamp B and **is not one**, because the two statements are about
different things:

- **Arithmetically the cap binds.** `need_bonus(dedicated_needed=3, flex=0) = 12.00` exactly, and
  everything above saturates. Demonstrated above.
- **Behaviourally, raising it changed no pick.** That is an ablation result — `NEED_BONUS_MAX` at
  `1e9` producing a pick-for-pick identical draft — which is a statement about whether the
  collapsed states ever *decide* anything, not about whether they collapse.

Both can be true at once, and here both are: the states collapse, and the other terms dominate by
enough that un-collapsing them moves no pick in the arms measured. **That is the resolution of
#153, and it is why the item is correctly classified KNOWN-OPEN-ACCEPTABLE** — a real loss of
distinction with measured-zero decision authority, which is #55's OBSERVABLE-vs-AUTHORITY
distinction in a different dress.

## What is NOT established, and should not be assumed

**Whether that ablation covered `4WR_TE_PREMIUM`.** The docstring's 8.67 figure is quoted while
discussing a **one-TE league's** surplus-tight-end bias, and `4.0 x 2 + 1.0 x 0.67 = 8.67` — i.e.
`dedicated_needed = 2`, which is a two-slot position, not a four-slot one. So the "reachable"
figure is scoped to the context it was measured in, and a 4WR format reaches `dedicated_needed =
4` and saturates where that measurement never went.

The cap's inertness is therefore **evidenced for the arms it was measured on and assumed for 4WR**,
which is precisely the arm #153 exists to question. Settling it needs the `1e9` ablation re-run on
`4WR_TE_PREMIUM` specifically — one battery arm, not a full battery.

**No constant was changed and none should be.** Widening either clamp is calibration against an
observed regime, which #56 forbids without a derivation. The open question is a *measurement* —
does the collapse decide anything in 4WR — not a tuning.

## Prose note (#182 family)

The sentence "its cap never binds" is true as a behavioural claim and false as an arithmetic one,
and nothing in the sentence says which it is. A reader checking the formula will find the cap
binding at `dedicated_needed >= 3` and reasonably conclude the comment is stale. Worth one
qualifying clause when that file is next open for prose — not touched here, since `draft_room.py`
is under the #222 constraint.
