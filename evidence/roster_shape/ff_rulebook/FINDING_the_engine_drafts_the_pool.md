# The engine drafts the pool. The humans don't. And the big deviation is QB, not TE.

Pure artifact read across four committed arms plus the production opening board. No engine run,
no engine source changed.

---

## The observation

| | QB | RB | WR | TE |
|---|---|---|---|---|
| **priced pool offers** | **8.7** | **26.2** | **41.2** | **23.9** |
| AUTO baseline | 10.3 | 26.9 | 30.4 | 32.4 |
| 3RR | 10.3 | 26.9 | 30.4 | 32.4 |
| force balanced | 10.3 | 25.6 | 42.0 | 21.8 |
| NARROW (displacement) | 10.3 | 25.3 | 42.0 | 22.1 |
| **twelve real managers** | **20.0** | **27.4** | **37.1** | **15.5** |

Deviation from the priced pool, in percentage points:

| | QB | RB | WR | TE |
|---|---|---|---|---|
| force balanced | +1.6 | −0.6 | +0.8 | −2.1 |
| NARROW | +1.6 | −0.9 | +0.8 | −1.8 |
| **twelve real managers** | **+11.3** | +1.2 | −4.1 | **−8.4** |

**With roster awareness on, the engine drafts the priced pool — every position within two points.
The humans do not.** The engine-versus-human gap *is* the pool-versus-human gap.

That is FINDING_01's original thesis with the sign reversed. It claimed *"the humans drafted
approximately the pool and the engine deviates"* — on the 764-row vendor board, and it was
retracted for the wrong universe. On the real universe the opposite is true, and
`CORRECTION_wrong_universe` said so in one line. Nobody connected it to the arms until now.

## The bigger deviation has been sitting in plain sight

|engine − human| per position, NARROW arm (the best-behaved roster-aware arm):

```
  QB   9.7          <-- the largest
  TE   6.6
  WR   4.9
  RB   2.1
```

**#222 spent its entire length on the second-largest deviation.**

## And QB is invariant to everything #222 tested

| arm | QB share | QB bodies per seat |
|---|---|---|
| AUTO | 10.3% | `[2,2,2,2,2,2,2,2,2,4,4,6]` — **9 of 12 seats take exactly 2** |
| 3RR | 10.3% | `[2,2,2,2,2,2,2,3,3,3,3,6]` |
| force balanced | 10.3% | `[2,2,2,2,2,2,2,2,2,4,4,6]` — identical to AUTO |
| NARROW | 10.3% | `[2,2,2,2,2,2,2,2,2,4,4,6]` — identical to AUTO |

**10.3% in every arm. The per-seat vector is byte-identical in three of the four.** The mode
boundary does not touch it, the counterweight does not touch it, pick-order permutation barely
touches it. PHASE4 already recorded this — *"QB is 0.0% in rounds 15–26 in BOTH arms"* — and it has
now survived two further arms.

**This is a superflex league.** QB and SUPER_FLEX are both started every week, so two quarterbacks
is the starting requirement with **zero backup**, and nine of twelve seats finish exactly there.

## Why QB is the better target than TE — four reasons, not one

1. **It is larger.** 9.7 points against 6.6.
2. **It is invariant.** Nothing measured in #222 moves it, so it is upstream of everything
   #222 examined. The TE question terminates in a design gap; this one has not been looked at.
3. **It is IN-DOMAIN, and this is the important one.** QB starter demand is 1.85/team = 22.2
   league-wide and the engine takes 32 QBs — so the deviation sits *inside* the region where
   `replacement_levels` is contractually defined and cross-position VOR is explicitly authorized.
   The TE problem lives below starter depth where the contract is silent (#229). **A QB defect
   would be a defect, not a design gap.**
4. **There is already a registered, unrepaired defect on exactly this path.** QB in a superflex
   league does not use the demand-rank model at all — it uses `startable_floors` /
   `qb_startable_floor`. Measured this session: production's QB level is **243.29**, while the
   plain demand-rank model on the same pool gives **329.0**. And **#185 is open**:
   *"replacement_basis says 'live_starter_demand' on all 39 superflex QB rows, where starter
   demand was never consulted."* A separate model, a known mislabel, and the largest deviation,
   all on the same path.

## The honest caveat, and it is the same one as before

**"Humans take more quarterbacks" is not "the engine is wrong."** Superflex convention is to draft
quarterbacks early and often; that could be humans pricing something VOR does not see, or it could
be convention. What is *not* a matter of taste is the roster-construction consequence: nine of
twelve seats finishing with two quarterbacks in a league that starts two means **one injury or one
bye week leaves a seat unable to field a legal lineup**, and #154's feasibility backstop exists
because that has been observed.

**Nothing here is proposed and nothing is measured about the QB path yet.** This document is the
argument for where to look next, and the evidence for it.
