# 6.1d·1: the ceiling is `max`, not `sum` — and the badge means "multi-eligible", not "fit"

**Partly executed, partly raised.** `CDME_CONTRACTS.md` rules: *derive a threshold from the
sum's own ceiling*. The derivation is done and shipped — **behaviour-free today** — but it does
not make the badge live, and why it cannot is the finding.

Probes here. Run from the repo root.

## 1. The two capped terms are MUTUALLY EXCLUSIVE

`context_elevated` fires on `team_acquisition_value − universal_value`, which is
`need_bonus + depth_exposure + displacement_adj`.

`need_bonus` is large when a slot at the position is **empty**. `depth_exposure` requires
**surplus** there. Those are opposite roster states, so the two never carry value together.
Measured across **4 formats × 8 in-draft board states, 10,887 priced rows**, of which **9,793**
carry a nonzero value on at least one term:

```
rows where need_bonus AND depth_exposure are both nonzero:   0 of 10,887
```

Zero. Not rare — none.

## 2. So the ceiling is `max(TEAM_SPECIFIC_CAPS)`, and the shipped formula was right by accident

The constant read `sum(TEAM_SPECIFIC_CAPS) / len(TEAM_SPECIFIC_CAPS)`, and its own comment
claimed that expressing it that way made the relationship *"stop being a coincidence and start
being maintained."* It did not. The mean equals the max here **only because the two surviving
caps happen to be equal** (12.0, 12.0). Let either move and the mean lands somewhere the
quantity cannot reach, silently.

Since the two capped terms contribute at most **one cap between them**, and
`displacement_adj ≤ 0` for a single-position probe (`lineup_optimizer.displacement_level`, THE
SIGN — 0 of 120 single-position probes go positive across 960), the gap's ceiling over the
single-position population is exactly `max(TEAM_SPECIFIC_CAPS)`.

**Shipped:** `CONTEXT_ELEVATED_THRESHOLD = max(TEAM_SPECIFIC_CAPS)`. Still `12.0` today, so no
behaviour changed; what changed is that the number now tracks a ceiling that is real rather than
one that is arithmetic.

## 3. The badge is dead, and correcting the derivation makes that clearer, not smaller

The threshold now sits **at** the derived ceiling, and the observed distribution never gets
near it:

```
format         rnd     n  max gap   >=12   max nb  max de  max nb+de  both>4
12T_ppr          0   476     8.67   0.0%     8.67    0.00       8.67       0
12T_ppr          8   380     4.67   0.0%     4.67    7.32       7.32       0
10T_ppr_TEP     10   376    -0.01   0.0%     0.00    9.60       9.60       0

ALL 10,887 priced rows:  gap min -122.00, max 8.72, mean -3.46
share >= CONTEXT_ELEVATED_THRESHOLD (12.0): 0.00%
```

The gap's **mean is negative** (−3.46), because `displacement_adj` only ever subtracts over this
population. A flag meaning "ranked highly substantially because of fit" is reading a quantity
that is usually a penalty.

## 4. Across all 36 battery formats, it fires on ONE row in the entire corpus

```
HEAVY_IDP                 n=538  max gap  8.33  fired 0  (0.00%)
LIGHT_IDP                 n=538  max gap  8.33  fired 0  (0.00%)
CAPTURE_fourth_and_forever n=481 max gap  9.00  fired 0  (0.00%)
CAPTURE_owner_league      n=820  max gap 87.82  fired 1  (0.12%)   <- multi-eligible
    Travis Hunter   gap 87.82   pos WR   fantasy_positions ['DB','WR']   disp +79.44
```

**So in practice `context_elevated` does not mean "ranked highly because of fit." It means
"multi-eligible player with a cheap second slot."** One player, one league. Everywhere else the
badge cannot light at all.

## 5. What this rules OUT

- **Not fixable by lowering the threshold to the observed max.** That is `#56` exactly —
  choosing a number to make a badge fire is fitting to the distribution.
- **Not fixed by `6.1b`.** Retiring `eligibility_bonus` removed a cap member and moved
  `NECESSITY_DENIAL_SATURATION` 36.0 → 24.0, but the gap's own ceiling was never the sum, so
  the badge's deadness is untouched by it.
- **Not an IDP-supply artifact.** Both IDP rulebooks fire 0.00%; the single firing row is a
  multi-eligible probe in the owner's own capture, not an IDP-population effect.
- **Not caused by `depth_exposure` being roster-wide** (the `6.1d` repair). That repair pulled
  the max gap 13.21 → 8.33; even at 13.21 the badge fired 7.72%, which the class that owned it
  already warned was "a bound being read as a threshold".

## 6. What is NOT fixed, and why — `#184`

The derivation is shipped. **The product question is not, and it is the owner's:** a flag that
fires on one row of one league out of 36 formats either needs a different quantity or should be
retired. Choosing which is a valuation/product decision, and picking a threshold that makes the
current quantity fire would be `#56` with a friendlier face.

`test_threshold_reachability.py` keeps two `expectedFailure`s pinning the deadness — they are
the executable statement of what must become true again once a ruling lands.

Related: `DRAFT_ROOM_UI` U24 asks whether the *necessity* tag should be kept, re-scoped or
retired, on the same grounds (95.4% of its mass in two of five bands). This is the same shape,
one flag over.
