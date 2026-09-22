# PRE-REGISTRATION — the VDS battery (varied drafting strategy)

**Written before any arm's result is read.** `#178` is the precedent and the battery README
states the rule: an acceptance criterion invented after the numbers exist is not a criterion.

## Why this battery exists

`#20`/`#22`. The first attempt to fix K/DST placement ordered the board on `acting_now_value`
instead of `team_acquisition_value`. It passed the format battery, and then **under-drafted QB in
superflex** — caught late, by a different instrument, and unwound.

The format battery could not see it. Of its 36 arms, **34 run `mode="auto"`** and the only two
that vary strategy are both `12T_ppr`. It varies FORMAT and holds strategy nearly fixed, so a
strategy regression has nowhere to show up.

## What varies, and the axes are already in the engine

Nothing here adds engine behaviour. A battery that needs new engine code is testing code that did
not ship.

| axis | values | source |
|---|---|---|
| `mode` | auto / balanced / upside | `compute_draft_board` |
| `upside_rule` | round / crossing | `#261` |
| `opponent_noise` | None / top_k 3 / top_k 8 | `#263b` |

Six strategies × six formats = 36 arms. Formats are chosen for where a strategy change has
somewhere to hide, not for coverage — the format battery already covers formats.

`simulate_full_draft`'s own comment already required this sweep and nothing performed it:
*"top_k is NOT a derived constant and must be swept and reported across, never chosen (#56)."*

## ALREADY MEASURED, BEFORE THE RUN: two of the six strategies are INERT on a short format

Run on `12T_ppr_SHORT_DRAFT` (8 rounds), pick sequences against the control:

```
sharp_balanced     0 of 96 picks differ   <-- INERT
crossing           0 of 96 picks differ   <-- INERT
sharp_upside      76 of 96 picks differ
noisy_k3          90 of 96 picks differ
noisy_k8          90 of 96 picks differ
```

Both for structural reasons: `auto` never reaches `UPSIDE_MODE_DEFAULT_ROUND` (15) in an 8-round
draft, so **auto IS balanced there**; and the crossing rule needs the board to exhaust positive
VOR, which 96 picks never do.

So a strategy can be listed, forwarded, and exercise nothing — exactly what the format battery's
own mode axis did before it was fixed ("the battery would have reported 'modes covered' while
exercising one"). **The runner therefore DERIVES inertness** by comparing each arm's pick sequence
to its own format's control, and reports `INERT_ARMS` and `effective_arms`. An arm that reproduces
its control is not evidence about its strategy, and counting it as a clean arm is counting the
control six times.

## Predictions, each falsifiable

1. **`sharp_balanced` is inert on `12T_ppr_SHORT_DRAFT` and NOT inert on the 14+ round formats.**
   Auto reaches round 15 only where the draft is long enough. If balanced is inert *everywhere*,
   the mode axis does not reach the board at all and this battery's control and its balanced arm
   are one arm.
2. **`crossing` is inert on `12T_ppr_SHORT_DRAFT` and fires on `HEAVY_IDP`.** The crossing rule
   needs positive VOR to run out; the deepest pool with the longest draft is where it should.
   If crossing is inert in all six formats, `#261` shipped a rule no format can reach.
3. **The noisy arms are never inert.** A uniform draw over a seat's top 3 changes a pick the
   moment the top 2 are not tied. If a noisy arm comes back inert, `opponent_noise` is not
   reaching the pick loop and `#263b` is decorative.
4. **`noisy_k8` produces at least as many structural findings as `noisy_k3`.** Worse rivals leave
   more legal-lineup damage. If k8 produces FEWER, the audits are measuring something that
   improves as rivals get worse, which would be a finding about the audits.
5. **Any structural finding that appears under all six strategies of a format is a FORMAT
   finding** already visible to the format battery, and the two batteries must agree on it. A
   finding present in the VDS run and absent from `BATTERY_2026-09-12_scoring_aware_full` for the
   same format, under the control strategy, means one of the two instruments changed.

## THE OWNER'S ACCEPTANCE BAR, and what this battery can and cannot do about it

The owner's stated bar for any future K/DST shape-forcing fix: **meet or beat raw `bpa` under
normal drafting, or at least be comparable.**

**This battery CANNOT evaluate that bar, and saying so now is the point of a pre-registration.**
It is self-play: every one of the twelve chairs runs the same engine with the same strategy. Change
the strategy and all twelve move together, so roster worth is measured against opponents who
changed identically. A self-play battery can detect that a strategy BREAKS something — which is
`#22`'s shape and is exactly what it is for — but it cannot say that one strategy drafts BETTER
than another.

What the bar needs is a **seat-level A/B**: one seat on the candidate strategy, the other eleven on
raw `bpa` normal drafting, comparing the treated seat's `total_value` against the same seat under
control. `simulate_full_draft` does not support that today — `opponent_noise`'s `sharp_seats`
exempts seats from NOISE, not from STRATEGY; `mode` and `upside_rule` are single values applied to
every seat in the pick loop.

So this run does two things for the bar and not a third:

- It **establishes the control baseline** — `sharp_auto`, raw `bpa`, normal drafting — per format,
  recorded with the commit that produced it, as the reference any future fix is read against.
- It **certifies that the strategy axis does not break legality**, which is the regression class
  `#22` belonged to.
- It **does not** and cannot rank strategies by draft quality. Any claim of that shape from this
  report would be the self-play blindness this programme has already recorded.

The seat-level A/B is a separate instrument and is named here as the missing capability rather
than quietly skipped.

## What a clean result licenses

That the engine does not break its league's rules under six drafting strategies across six
formats. It says nothing about whether the engine drafts WELL, nothing about K/DST placement being
correct, and nothing about `#21` or `#50`.

`total_value` is the roster-worth line (`ROSTER_WORTH_BASIS`). `starter_value` is NOT — `#211`
established it measures positional breadth and is contaminated by forced below-replacement
starters. No reading of this report may use `starter_value` as a quality measure.
