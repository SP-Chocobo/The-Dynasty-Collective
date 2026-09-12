# Roster capacity is refuted too — and the reason is a fence, not a null

Three arms, one process, one code version, rounds pinned at 15, dose-response on one axis.
Pre-registered at `87a2f1b` before any number existed.

```
A3   fixture, draftable 15, spare  0   4/12  -0.28%  margin -6.99   CONTROL
F20  fixture, draftable 20, spare  5   4/12  -0.28%  margin -6.99   THE CUT, halfway
F26  fixture, draftable 26, spare 11   4/12  -0.28%  margin -6.99   THE CUT, matched to F&F
```

**0 differing values across three arms × 12 seats × every metric.** Not similar. Identical.

## Identical numbers are a broken instrument until proven otherwise

That is the `#245` rule, and it was earned: the draft-length cut returned identical numbers and
the cause was a harness defect (`ff_league()` never set `draft_rounds`). So this run is not
reported until the question *"did the thing under test actually fire?"* has an answer.

It fired. The leagues differ (`draftable=15/20/26`, `spare=0/5/11`), and
`remaining_draft_capacity` differs with them — measured at the opening board, **180.0 vs 312.0**.
The quantity moved. It simply cannot reach a pick.

## Where capacity goes, and where it stops

```
draftable_slots_per_team
  -> remaining_draft_capacity          180.0 (15 slots)  vs  312.0 (26 slots)
    -> estimated_bench_demand
      -> horizon_replacement
        -> horizon_floor, horizon_sensitivity, waiting_cost, horizon_basis   <- OBSERVABLES
```

`estimated_bench_demand` says so itself, in its own docstring:

> *"NEVER REACHES VALUATION. Nothing on the replacement_levels / VOR / bpa path reads this, by
> design and by test — see the module docstring on why a behavioural prior is allowed to inform
> the debate layer and not the anchor."*

And `#57` already recorded the other half: `waiting_cost` is computed, displayed, and **not
consumed**. So the whole capacity chain terminates in things a person reads.

**Proven at the board, not inferred from the call graph.** Opening board, same pool, same picks,
15 vs 26 draftable, every column compared:

| column | differs? |
|---|---|
| `horizon_floor` | **1111 of 1111 rows** |
| `horizon_sensitivity` | **1111 of 1111 rows** |
| `horizon_basis` | **665 of 1111 rows** |
| `waiting_cost` | **256 of 1111 rows** |
| `final_score`, `player_id` order, and every other column | **0 rows** |

Capacity changes four observables and nothing on the pick path. The three identical arms are a
**real null with a stated mechanism**, not a measurement failure.

## The second finding, which is larger than the one this run was for

Look at *which way* those observables changed. At 26 draftable slots the horizon floor does not
move — **it disappears.**

| after N picks | draftable 15 | draftable 26 |
|---|---:|---:|
| 0 | `horizon_floor` known on **1111/1111** | **446/1111** |
| 24 | **1087/1087** | **442/1087** |
| 60 | **1051/1051** | **433/1051** |
| 100 | **0/1011** | **0/1011** |
| 150 | **0/961** | **0/961** |

Two separate things are visible here.

**(a) The deeper the bench, the less the horizon layer can say — at the moment a person opens
the draft room.** 60% of the board loses its floor (`horizon_basis: "unavailable"`) purely
because the league rosters 26 instead of 15. This is the absence contract working exactly as
designed — `horizon_replacement` refuses to read a floor off the end of a truncated pool, which
is the `#51`/`#166` lesson — but the consequence is that the deeper the league, the less
guidance it gets. **Fourth and Forever, the league actually being played, is a 26-draftable
league.** Every fixture-measured claim about the horizon layer was taken at 15, where it is
fully available.

**(b) It goes dark for EVERYTHING, in every league, at a hard boundary.** Measured round by
round on the 15-slot fixture:

```
round  9 (96 picks)   horizon_floor known on 1015/1015
round 10 (108 picks)  horizon_floor known on    0/1003
```

A cliff, not a fade. **In a 15-round draft the entire waiting layer is unavailable for the last
six rounds**, on the board a person is reading, in both leagues. The mechanism is stated in the
code and is deliberate — `estimated_bench_demand` returns all-`None` the moment ANY position
loses its bench-appetite evidence, because *"a single unknown makes the SHARE undefined for
every position … a total with a hole in it cannot be normalised against"* — but the
**reachability** of that state, and that it is the normal state of the second half of every
draft, is not recorded anywhere.

This reaches the human, not the pick, so it is Gate 4. It sits next to `#112` (kind-of-absence
stops at the board) and `#206`.

## Where that leaves the reversal — honestly, nowhere yet

All three structural candidates are now refuted:

| candidate | verdict | evidence |
|---|---|---|
| draft length | REFUTED | `#245` — identical at 15 and 26 rounds |
| scoring rulebook | REFUTED | `#248` arm A→B — 4/12 either way |
| flex / startable count | REFUTED | the flex cut — both directions, no consistent sign |
| roster capacity | **REFUTED** | this run — fenced off from the pick path by design |

And yet arm A2 (`−0.28%`) and arm C2 (`+1.04%`) really do differ, on the same code and the same
pool. **Something reaches the pick that none of these four cuts isolated.** Saying so is the
honest position; the alternative is to keep naming mechanisms that the next cut refutes.

## The missing cell — and these arms were a factorial design nobody noticed

Laying the five measured arms on their real axes makes the gap obvious:

| roster | rulebook | FLEX | `points` |
|---|---|---:|---:|
| fixture | PPR | 2 | 4/12 |
| fixture | F&F | 2 | 4/12 |
| fixture | PPR | 3 | 3/12 |
| **fixture** | **F&F** | **3** | **NEVER RUN** |
| F&F | F&F | 3 | 10/12 |
| F&F | F&F | 2 | 9/12 |

Each arm was added one at a time to answer its own question, and together they are a 2×2×2 with
exactly one empty cell. That cell is the next cut, and it is decisive either way:

- **≈ 10/12** → it is an **interaction** between rulebook and flex that no single-variable cut
  could ever have found, and every cut so far was underpowered by construction rather than wrong.
- **≈ 4/12** → the F&F *roster* carries it beyond flex count, and since capacity cannot reach a
  pick, the remaining difference is **TAXI** (F&F 5, fixture 0) — which would then need its own
  path to the board found and named.
