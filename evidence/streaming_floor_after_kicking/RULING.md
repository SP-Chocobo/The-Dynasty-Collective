# `#30`'s streaming floor after 2.3's kicker repricing — ANSWERED, no re-derivation needed

**Status: the question 2.3 raised is closed by measurement. It does not need the owner (this was
D3 in `OWNER_DECISIONS_PENDING.md`, now withdrawn as a decision).**

## What 2.3 flagged

> K ordering is what `#30`'s streaming floor is derived from, so **that floor is worth re-deriving
> over this** — flagged, not claimed to be unaffected.

2.3 repaired kicker scoring: the league scores a generic `fgmiss`, Sleeper projects only bucketed
misses, and neither vocabulary could reach the other, so no missed field goal was ever scored. Every
kicker lost 4.22–6.44 points and **16 of 33 changed rank**.

## The first thing to establish: there is nothing to re-derive

`streaming_replacement_levels` is **computed live from weekly projections**, not stored. Its own
docstring says so — *"No constant is selected (`#56`)"*, and *"the live board computes it from the
season it is actually drafting"*. So the floor does not lag a scoring change; it moves with it,
through the same scoring path that repriced the kickers. "Re-derive the floor" describes work that
does not exist.

What *could* have needed re-measuring is `#30`'s published **worth** figures (K 121.78 → 164.50,
DEF 107.95 → 146.05), and those were measured on the **2024 season against realized outcomes**.
Comparing them to a number computed from this capture's projections would be a different season and
a different quantity — the error the measurement discipline warns about. So they are left alone, and
the question is asked the way it can be answered.

## The A/B: one process, one dataset, one variable

Only `player_universe.derive_kicking_categories` — 2.3's change — is toggled. Arm
`12T_ppr_K_DEF`, whose roster carries both a K and a DEF slot.

| | K floor | DEF floor |
|---|---|---|
| with 2.3 | **139.76** | 123.89 |
| without 2.3 | **145.44** | 123.89 |
| change | **−5.68** | **0.00** |

DEF at exactly 0.00 is the control: a kicking derivation cannot touch a defense, and if it had, the
toggle would be reaching something it should not.

## The result: the repricing nearly cancels itself at VOR

Over the 38 kickers priced in both arms:

| | mean | min | max |
|---|---|---|---|
| projected points | **−4.44** | −6.44 | 0.00 |
| `bpa` (VOR against the floor) | **+1.24** | −0.76 | **+5.68** |

Each kicker lost about 4.44 projected points, and the floor fell 5.68 with them — because the floor
is the sum of weekly maxima over the wire, and if every kicker loses roughly the same amount each
week then so does the best of them. So kickers end up **very slightly better** against the floor than
before, not worse.

**And it changes nothing about `#30`'s conclusion.** Every kicker's `bpa` is deeply negative in both
arms — mean −40.46, best **−10.68**. The best kicker available is still more than ten points below
what streaming the position is projected to yield, which is exactly what `#30` says and why the first
K/DST pick moved from round 4 to round 12.

## What is left, and it is not this

2.3's real consequence stands: **16 of 33 kickers changed rank** relative to each other, and the top
five hold their identity and order. That is a reordering *within* a position nobody should be drafting
early, measured against a floor that moved with them. `#21`'s own floor derivation remains blocked on
`#50`, which is the owner's equation and a different subject entirely.
