# #206 — the value-share take model, measured against the rank table

Produced by `evidence/survival_calibration/value_model_arm.py` on the real Greatest Show on
Paper 2 board (360 real picks, 301 resolved). **6,277 pairs, identical population in all three
arms** — same turns, same exclusions, same boards. Only the take model differs.

Engine at measurement time: `1ac8a63` + the `_board_take_probability` seam
(`draft_strategy.py` sha256_12 `f33dc549932a`). Each report carries its own source hash.

## Headline

| arm | engine Brier | constant | oracle | ceiling | beats constant | vs constant |
|---|---|---|---|---|---|---|
| `rank` (production) | 0.16127 | 0.14224 | 0.0 | holds | **no** | −13.4% |
| `value_floor` | 0.15050 | 0.14224 | 0.0 | holds | **no** | −5.8% |
| `value_zero` *(bound)* | **0.13755** | 0.14224 | 0.0 | holds | **yes** | **+3.3%** |

The `rank` arm reproduces the previously published 0.16127 **digit for digit**, which is what
licenses the other two: the seam is inert when it is not substituted, so the difference between
arms is the take model and nothing else.

## Reliability by board rank — where the model actually changed

Predicted → observed (error). Rank 0 is the engine's own top candidate.

| band | n | `rank` | `value_floor` | `value_zero` |
|---|---|---|---|---|
| 0–0 | 71 | 0.809 → 0.451 (**+0.359**) | 0.599 → 0.451 (+0.149) | 0.208 → 0.451 (−0.243) |
| 1–2 | 306 | 0.862 → 0.726 (+0.136) | 0.764 → 0.726 (**+0.039**) | 0.482 → 0.726 (−0.243) |
| 3–4 | 352 | 0.903 → 0.707 (+0.196) | 0.854 → 0.707 (+0.147) | 0.675 → 0.707 (**−0.033**) |
| 5–9 | 1193 | 0.941 → 0.786 (+0.154) | 0.905 → 0.786 (+0.119) | 0.775 → 0.786 (**−0.011**) |
| 10–19 | 1614 | 0.932 → 0.819 (+0.113) | 0.917 → 0.819 (+0.098) | 0.841 → 0.819 (**+0.023**) |
| 20+ | 2741 | 0.972 → 0.889 (+0.082) | 0.971 → 0.889 (+0.082) | 0.936 → 0.889 (**+0.047**) |

n-weighted mean |error|: `rank` **0.1162**, `value_floor` **0.0954**, `value_zero` **0.0448**.

Production's worst band is its own top candidate — it claims 0.809 survival for a player who
survives 45% of the time. The value model cuts that error by 58%; removing the floor removes it
entirely and overshoots the other way.

## What this establishes, and what it does not

**Established.** The rank table is the larger error source, exactly as `#206` predicted: it
cannot distinguish an opponent's coin-flip top two from a locked one. Reading the opponent's own
`final_score` through `exp((score − leader) / scale)`, with `scale` derived per board, improves
every band and is monotone in the right direction.

**Not established — and this is the blocker.** `value_floor` is the honest straight wiring and
it still LOSES to a constant predictor. The whole remaining gap is the unpriced floor:

* 638 unpriced rows × `RANK_TAKE_PROBABILITY_FLOOR` (0.02) = **2.0×–3.4× the entire priced
  mass** on real boards, so the good priced shape is diluted threefold.
* That constant was derived against a rank table whose leader was 0.55. The value model's leader
  weighs 1.0. Carrying it across unchanged is the unit drift `#75` names — the same defect, in a
  new place.
* The block's share therefore depends on **how many players the vendor failed to price**, which
  is a coverage fact about the export, not a fact about the draft. That is the artifact.

**`value_zero` is a bound, not a candidate.** It wins only by asserting "unpriced means safe",
which the owner ruled against and which the real drafts refute: 31 of 301 resolved picks took a
player who was not on the picking team's priced board at all. It is reported so the floor's cost
is measurable rather than argued — it says the value model has ~3.3% of headroom over the
constant available, and the floor is currently spending all of it and more.

## The open decision

The unpriced block needs a share that is derived rather than inherited, and it may not be set
from this capture (the LIMITS are binding: *"ONE league … a data point for testing, NOT a
benchmark. No engine constant may be calibrated to it."*). The structurally correct move is to
make the BLOCK's share the quantity and divide it among its rows, so a vendor's coverage stops
setting it — but what that share is derived FROM is a design question, not an arithmetic one.

The most promising internal derivation: unpriced rows are not random, they are concentrated in
positions whose starter demand is already met, so the probability a rival takes one relates to
how much of that rival's remaining roster is bench rather than starting slots — a quantity the
engine already holds. That is Phase 3 work, not a patch.

**Until it is settled, production is unchanged and `SURVIVAL_IS_CALIBRATED` stays False.**
