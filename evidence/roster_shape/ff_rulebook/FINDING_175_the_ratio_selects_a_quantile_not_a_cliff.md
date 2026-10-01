# #175: the cliff ratio — REJECTED as a derivable threshold, and my first answer CORRECTED

> **STATUS: this file replaces an earlier version of itself.** The first #175 pass compared the
> engine's cliff ratios against the wrong null and published two conclusions that are both now
> withdrawn. The withdrawal is stated first, in full, before anything new is claimed.
>
> **No constant is changed by this work, and none should be.** The owner's sequencing was
> "battery characterization → derive or reject threshold → no constant change until then."
> This is the characterization, and it **rejects**.

---

## 1. The 25th correction: I used the null for an estimator this engine does not use

The first pass compared the observed exceedance of `gap / typical_gap` against the closed form

```
P(X >= r * median) = 2^-r
```

That is the null for a **plain median of adjacent gaps**. `detect_positional_cliff` does not
divide by one. Its yardstick (`pick_synthesis.py`) drops the zero gaps, drops the target's own
gap, and **trims away the largest ~10%** before taking a median. Every one of those shrinks the
denominator, so every ratio is inflated relative to a plain-median ratio — and the trim does it
hardest in the tail, because the trim removes only big gaps.

Run on genuinely memoryless (exponential) gaps, the engine's **own** estimator returns:

| r | closed form `2^-r` | plain median | **the engine's estimator** | understatement |
|---|---|---|---|---|
| 1.0 | 0.500 | 0.500 | **0.546** | 1.09× |
| 1.5 | 0.354 | 0.355 | **0.404** | 1.14× |
| 2.0 | 0.250 | 0.252 | **0.300** | 1.20× |
| **2.5** | **0.177** | 0.180 | **0.223** | **1.26×** |
| 3.0 | 0.125 | 0.128 | **0.166** | 1.33× |
| 4.0 | 0.062 | 0.066 | **0.092** | **1.48×** |

The plain-median column tracks the closed form closely, which is what identifies the **trim** as
the cause rather than the simulation. Pinned by `test_cliff_null_estimator.py`, so nobody
re-derives "the null" from the closed form again.

### The two claims that are withdrawn

**WITHDRAWN 1 — "at 2.5× the flagged population is RARER than a no-cliff null (0.83×)."**
False, and backwards. Against the engine's own null the enrichment at r=2.5 is **1.23×–1.63×**,
i.e. the flagged population is *enriched*, not rare. The "0.83×" was 0.177 in the denominator
where 0.223 belonged.

**WITHDRAWN 2 — "real structure exists and lives further out; the enrichment crosses 1.0 only
past 3× and reaches 1.21× at 4×."** False in the other direction. The enrichment at r=4.0 is
**2.37×–2.61×**, and it does not *cross* anywhere meaningful: it is above 1.0 from r=1.0 and
climbs monotonically. There is no crossing point, so there is nothing there to derive from.

Both errors came from one substitution, and neither was visible in the output — the numbers
looked perfectly plausible either way. That is the lesson, and it is the owner's: *don't just
instrument the answer; instrument whether the instrument is answering the question you think.*

A third, smaller correction: an intermediate power calculation I ran on the old pooled data
(n=252) reported the 4× enrichment as statistically indistinguishable from noise (z=0.85,
p=0.199). That conclusion was drawn from the same wrong null and is also void.

---

## 2. What is actually measured

Eight arms on the real capture universe (6,595 players, 5,346 season projections), real F&F
rulebook, format reaching the merger on every arm. Null **simulated through the engine's own
estimator** at each pool's observed size and tie rate, 3,000 replicates.

`12T_ppr`, opening board:

| pos | n | r=1.0 | r=1.5 | r=2.0 | **r=2.5** | r=3.0 | r=4.0 |
|---|---|---|---|---|---|---|---|
| QB | 41 | 0.99 | 1.01 | 0.92 | **1.23** | 1.18 | 1.28 |
| RB | 125 | 1.00 | 1.15 | 1.34 | **1.55** | 1.70 | 2.37 |
| TE | 114 | 1.01 | 1.09 | 1.32 | **1.63** | 1.82 | 2.61 |
| WR | 197 | 1.00 | 1.10 | 1.34 | **1.60** | 1.88 | 2.55 |

(enrichment = observed exceedance ÷ the engine-estimator null at that pool size)

**Every offensive gap distribution is heavier-tailed than memoryless, monotonically, with no
inflection anywhere on the grid.** That is a real and reproducible property of the pool.

**It is not, by itself, evidence of cliffs.** Rejecting an exponential fit is a goodness-of-fit
result. A smooth power-law decay with no discrete tiers at all would reject it exactly the same
way. Section 5 is where that distinction bites.

---

## 3. Q1 — is the crossing stable across formats and arms?

**The question partly dissolves, and the part that survives has a structural answer.**

`bpa` is points minus that position's replacement level, and **the replacement level is one
constant per position**. `detect_positional_cliff` reads only *differences* between adjacent
bpa values, so the constant cancels — in the gaps, in the yardstick, in the ratio, and in the
`CLIFF_MIN_MATERIAL_GAP` floor alike.

Measured on the real universe rather than argued:

| axis varied from 12T_ppr | QB gaps changed | RB | WR | TE | top bpa moved |
|---|---|---|---|---|---|
| superflex on | **0 / 41** | **0 / 125** | **0 / 197** | **0 / 114** | 48.51 → 163.06 |
| 10 teams | **0 / 41** | **0 / 125** | **0 / 197** | **0 / 114** | 48.51 → 39.81 |
| 14 teams | **0 / 41** | **0 / 125** | **0 / 197** | **0 / 114** | 48.51 → 55.22 |
| `rec` ppr → standard | 0 / 41 | 124 / 125 | 189 / 197 | 113 / 114 | 48.51 → 48.51 |
| `rec` ppr → half_ppr | 0 / 41 | 123 / 125 | 190 / 197 | 113 / 114 | 48.51 → 48.51 |
| `bonus_rec_te` raised | 0 / 41 | 0 / 125 | 0 / 197 | 113 / 114 | TE only |

Superflex moves the top QB price by **3.4×** and changes **not one gap**. League size likewise.
QB is untouched by `rec` because quarterbacks catch no passes — correct, not an artifact.

So: **league size and superflex cannot change a single cliff tier, ever.** Only the axes that
reshape the points curve — `rec`, `bonus_rec_te` — can, and `bonus_rec_te` only at TE. Of the
eight arms run, **three are independent** on this quantity. Running the full 32-arm battery
would buy no further evidence on this axis, and a battery that counted 32 arms here would be
inflating its own denominator.

Pinned structurally by `TheCliffTierCannotSeeTheReplacementLevel`, with a control proving the
detector *is* sensitive to curve shape — without which the invariance would be consistent with
the detector being insensitive to everything.

---

## 4. Q2 — how many observations does a departure need?

**The power formula, validated by simulating the test it sizes** (not against a recalled
textbook number — I got that wrong twice before checking): at the sample sizes in play,
simulated power 0.78–0.84 against a 0.80 target, type-I 0.04–0.08 against 0.05.

**But the ratios are not independent observations.** Every ratio at a position is divided by a
yardstick built from the same gaps. Measured design effect — the variance of the exceedance
count over the binomial variance:

| pool n | D at r=2.5 | D at r=4.0 |
|---|---|---|
| 41 | 1.29 | 1.58 |
| 114 | 1.30 | 1.52 |
| 197 | 1.22 | 1.53 |

Effective n is **65–82% of naive n**, worst in the tail. Applying it at r=2.5:

| pos | n | n_eff | min detectable | observed | verdict |
|---|---|---|---|---|---|
| WR | 197 | ~161 | ~1.37× | 1.60× | detectable |
| TE | 114 | ~88 | ~1.49× | 1.63× | detectable |
| RB | 125 | ~97 | ~1.47× | 1.55× | marginal |
| QB | 41 | ~32 | ~1.9× | 1.23× | **not detectable** |
| LB | 26 | ~20 | ~2.3× | 2.02× | **not detectable** |
| DB | 41 | ~32 | ~2.4× | 0.56× | **not detectable** |
| DL | 12 | ~9 | ~2.7× | 0.48× | **not detectable** |

**The three deep offensive pools can reject memorylessness. QB and every IDP position cannot,
on a real opening board, at any threshold.** A per-position runtime rule would be estimating a
tail quantile from 41 QB gaps and 12 DL gaps.

---

## 5. Q3 — does the crossing land where a human would put a cliff?

**Mixed, and the mixture is the finding.** The largest ratios at each position are two different
kinds of thing:

*Recognizable top-of-board tier breaks* — the ones a human would name:
```
ratio 26.28   RB3 Christian McCaffrey (208.3) -> RB4 Jonathan Taylor (176.2)
ratio 41.57   WR4 Ja'Marr Chase (135.2)       -> WR5 Nico Collins (105.2)
ratio 41.41   TE2 Trey McBride (124.7)        -> TE3 Colston Loveland (95.7)
```

*Deep-pool artifacts nobody would call a cliff:*
```
ratio 30.52   QB32 Fernando Mendoza (-114.5)  -> QB33 Michael Penix (-230.8)
ratio 15.14   RB42 Jonathon Brooks (-24.3)    -> RB43 Woody Marks (-42.8)
ratio 21.16   TE28 Mike Gesicki (-47.6)       -> TE29 Colby Parkinson (-62.4)
```

And the second kind frequently scores **higher** than the first. That is not noise — it is
structural: the yardstick is a median gap, and the median gap collapses toward zero where the
pool is compressed, which is exactly the deep pool. **The ratio is systematically largest where
it is least meaningful.**

This is also why §2's heavy tail is not yet evidence of cliffs. A ratio that fires hardest at
QB32 is measuring pool compression, not a tier boundary.

---

## 6. Verdict: REJECT

Per the owner's sequencing — *derive or reject* — this **rejects**.

1. **No null-crossing exists to derive from.** The enrichment is above 1.0 from r=1.0 and rises
   monotonically to r=4.0 with no inflection, in every arm and at every offensive position. The
   "crossing" my probe reports lands at 1.0–1.5, which is not a cliff threshold; it is the point
   at which the distribution stops being exponential, which is nearly everywhere.
2. **The format-stability question is answered but buys nothing**, because the quantity is
   exactly invariant to the axes a battery varies most cheaply.
3. **The tail is underpowered where a per-position rule would need it most** — QB and all IDP.
4. **The measure's largest values are concentrated where it means least**, which no choice of
   multiple or quantile repairs.

**No value for `CLIFF_HIGH_RATIO` is proposed, and the null-crossing basis offered by the
previous version of this file is withdrawn along with the rest of it.**

### What the "runtime-derived per position" fallback would have to overcome

Stated as conditions, not as a recommendation:

- It cannot anchor on a null crossing — there is none.
- A per-position empirical quantile *is* computable and inherits the replacement-level
  invariance of §3 for free, so it would be format-stable by construction.
- It would inherit §5 unchanged: the rule must first answer **where in the pool it applies**,
  which is a different question from what multiple. A depth bound is the missing concept, not a
  better ratio.
- It must survive §4: QB (41 gaps) and IDP (12–41) cannot support a per-position tail estimate.

### Why this is not urgent

`CLIFF_HIGH_RATIO` feeds `NECESSITY_CLIFF_POINTS` → `pick_necessity`, which **#55 ruled
OBSERVABLE with no selection authority**. A grep of the selection paths returns only UI and
mockup references. **Changing this constant cannot change a pick today.** The decision is a
reporting-quality decision, and it can wait for the depth concept §5 asks for.

---

## 7. Scope, stated rather than implied

- **Opening boards only.** A mid-draft board with a drained pool is not measured here, and §5's
  compression effect would plausibly be worse there, not better.
- **One universe, one rulebook.** The real F&F capture; `bonus_rec_te = 0.25`, `rec = 0.5`.
- **The null is exponential.** Rejecting it establishes a heavier tail, not tiers (§2).
- **The design effect is measured at three pool sizes and interpolated** between them.
- The probe is `cliff_null_characterization.py`; its private copy of the engine's yardstick is
  held in lock-step by `test_cliff_null_estimator.py`, mutation-checked 6 of 7 (the survivor is
  deliberate — see that file).
