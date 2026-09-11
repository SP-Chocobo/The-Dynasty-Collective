# B2 is not a valuation defect. The engine runs out of quarterbacks it can price.

Four artifact reads plus one capture read. No engine run, no engine source changed. This
redirects B2 and closes the question "why does the engine take half the quarterbacks a human does".

---

## 1. Pricing coverage, by position

| pos | admitted | priced | unpriced | **% priced** |
|---|---|---|---|---|
| **QB** | 155 | **42** | 113 | **27.1%** |
| RB | 256 | 126 | 130 | 49.2% |
| WR | 452 | 198 | 254 | 43.8% |
| TE | 256 | 115 | 141 | 44.9% |

**Quarterback coverage is 27.1% against 44–49% everywhere else.** The pricing layer is the only
thing between "who exists" and "what the engine can draft", and it moves QB hardest:

| | admitted share | priced share | shift |
|---|---|---|---|
| **QB** | 13.9% | 8.7% | **−5.1** |
| RB | 22.9% | 26.2% | +3.3 |
| WR | 40.4% | 41.2% | +0.8 |
| TE | 22.9% | 23.9% | +1.0 |

**In the direction of the observed gap, and larger than any other position's shift.**

## 2. The engine is not undervaluing quarterbacks — it is exhausting them

Share of each position's PRICED pool that the engine actually drafts:

```
   TE  101 of 115 = 87.8%
   QB   32 of  42 = 76.2%     <-- second highest
   RB   84 of 126 = 66.7%
   WR   95 of 198 = 48.0%
```

**It takes more than three-quarters of every quarterback it can see.**

## 3. The human number is arithmetically out of reach

```
   humans' 20.0% of 312 picks  =  62 quarterbacks
   the engine's pool prices    =  42 quarterbacks
   -> 20 of them carry no price at all
```

The engine cannot reach 20% QB without drafting rows that have no price — which `_board_order`
correctly sorts last, and which #61 ruled must never be substituted with a number. **The
behaviour is the absence contract working, not a valuation failure.**

## 4. Why those 113 have no price

Of the 113 unpriced quarterbacks, **90 ARE present in the season-projection capture** (5,346
players) — carrying only an ADP sentinel and no stat line:

```
   sample: {'adp_dd_ppr': 18000.0}   {'adp_dd_ppr': 18000.0}   ...
```

23 are absent from the file entirely. So the input has a row for most of them, an
"effectively undrafted" ADP marker, and **nothing to score**. The engine refuses to price them,
which is correct.

## The verdict

**B2 is a SUPPLY defect, and it belongs to the #193 / #209 / #210 family, not to valuation.**
That is the same verdict #51 reached for IDP in as many words: *"a SUPPLY defect, not an
arithmetic one — remedy is an input."* The remedy here is the same shape: backup-quarterback
projections, not an engine change.

**This also disposes of the lead I was about to chase.** `startable_floors` / `qb_startable_floor`
and #185's basis mislabel affect what a quarterback's *level* is. They cannot affect *how many
quarterbacks have a price*, which is the binding constraint. #185 remains a real defect and
remains worth repairing on its own terms — it is simply not the cause of B2.

## What this does NOT establish

**Not that 20% QB is correct.** Superflex convention may be humans pricing something the engine
cannot see, or it may be convention; this document takes no position, and the human figure is one
league's startup.

**Not that the coverage is wrong to be what it is.** A backup quarterback with no projection may
genuinely be unpriceable from the inputs available. What is established is only that the
*constraint is supply*, so no valuation change can move it.

**One hazard noticed and not chased:** `adp_dd_ppr: 18000.0` is a sentinel meaning "undrafted".
If anything downstream reads that as a real ordinal it would be a #70-family defect. Not measured
here; recorded so it is not lost.
