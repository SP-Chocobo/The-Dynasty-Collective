# I-06/J-06: the defect is real, and step 1 cannot be written without a boundary ruling

**Characterized, not built. No engine code changed.**

`CDME_CONTRACTS.md` rules **separate basis token with its own scale**, and sets the execution
shape: *"introduce the basis token carrying the measured uncovered quantity, price nothing."*
I went to write that token and found that the obvious form of it recreates a failure mode this
repository has already ruled against. The measurement below confirms the defect is worth
fixing; the boundary is the owner's.

Probe here. Run from the repo root.

## 1. The defect is real, and larger than it reads

`draft_room` prices `worst_loss` only under `EXPOSURE_MEASURED`; every other basis contributes
`depth_exposure_value = 0.0`. Measured over 8 in-draft board states, 12-team PPR dynasty, real
capture, production's own `_team_roster_players` builder:

```
cells by basis (position x board state)        worst_loss by basis
   not_applicable  40 (55.6%)                     no_surplus  n=8  min 10.00  median 62.00  max 82.00
   vacant          18 (25.0%)                     measured    n=6  min 27.00  median 42.00  max 61.00
   no_surplus       8 (11.1%)
   measured         6 ( 8.3%)

no_surplus cells carrying a NON-ZERO worst_loss: 8 of 8
```

**The unpriced state carries the LARGER measured loss.** Median 62.00 against `measured`'s
42.00, topping out at 82.00 — and it is priced at exactly what a perfectly covered position
with no marginal loss is priced at: `0.0`. That is `#187`'s shape, and the contract already
says so: *"zero is a NUMBER, not an absence."*

Every one of those 8 cells has a real measurement sitting behind it. The state is not
"nothing to measure"; it is "measured, on a different scale."

## 2. Why the obvious step 1 cannot ship

The natural implementation is to add `EXPOSURE_UNCOVERED` and return it where
`not all(covered)`. That is the entire current population of `EXPOSURE_NO_SURPLUS` — the token
is returned from exactly one site, `basis = MEASURED if all(covered) else NO_SURPLUS` — so
adding it leaves `NO_SURPLUS` **unreachable**.

`basis_semantics.py` rules that out by name:

> REACHABILITY IS PART OF THE DECLARATION (the condition this ruling was made subject to). A
> vocabulary does not get a state it cannot emit; **that is the unreachable-predicate shape the
> 18th withdrawal was.**

And `test_depth_exposure.TheFourStatesOfKnowingTests.test_a_roster_with_no_bench_reports_no_surplus`
pins a live population for it.

## 3. Both available boundaries are things this repo has already rejected

To keep both tokens reachable, something must separate "you hold no backup **here**" from
"bench exists, and the solve still left a starter uncovered". There are two candidate
mechanisms, and each has a recorded rejection:

**(a) An eligibility rule** — "is any bench player eligible at a slot this position can
reach?". `depth_exposure`'s own docstring measured this and threw it out:

> A first attempt here did state it as a rule — *"a bench player who can occupy a slot this
> position can reach"* — and it was **WRONG** in a way worth recording, because it looks right:
> a bench RB can play FLEX, and a tight end can also reach FLEX, so the rule called TE covered.
> It is not.

**(b) The roster-wide "does this roster have any bench at all" boolean** — this is precisely
the sentinel `#52` phase 6 (the `6.1d` repair, found independently as I-06 and J-06) removed:

> This was one roster-wide boolean, `len(roster_players) > len(starting_ids)`, stamped onto
> every position alike... one irrelevant bench body switched pricing on for every position at
> once.

So the two obvious boundaries are the two this item's own repair already deleted.

## 4. What this rules OUT

- **Not a renaming exercise.** `#188` already considered and rejected collapsing these tokens:
  *"a rename would also be a data-format change — these tokens are keys in the label maps
  shipped across the Python/JS boundary (`#186`) and they participate in snapshot identity
  (`#92`)."* Any new token must also be declared in `basis_semantics.REACHABILITY` with how its
  reachability was established, `exercised` or `dormant_by_design`.
- **Not solvable by pricing it.** That is step 2 by the contract's own sequencing, and it needs
  a scale nobody has argued for (`#56`).
- **Not an artifact of the fixture.** The population is 8 of 8 cells with non-zero measured
  loss across 8 board states, built with production's own roster builder. (A first attempt at
  this probe hand-rolled that builder and produced an EMPTY roster — `n=0`. Caught by the
  engine-measurement rule about printing `n`, and the probe now calls
  `dr._team_roster_players` directly.)

## 5. What the owner has to rule

**What separates the two states, given that both obvious answers are already rejected?**
Three shapes, none of which I should pick:

1. **Accept one token.** Keep a single unpriced state and fix only its LABEL, which is the part
   that is plainly false today: *"not measured — you hold no backup here, so there is no
   surplus to value"* sits on a cell carrying a measured 82.00. Cheapest, honest, and it leaves
   the vocabulary's cardinality alone. It does not deliver the "separate token" the ruling
   names.
2. **Ask the solve a second question.** Something derived rather than ruled — e.g. whether the
   re-solve drew in *any* non-starter anywhere, as opposed to at this position. Needs its own
   derivation and its own evidence that it is not (b) in disguise.
3. **Declare `no_surplus` `dormant_by_design`.** Add the new token, accept that the old one has
   no live population, and register it in `basis_semantics.REACHABILITY` the way
   `pool_truncated` already is. This is the only path that adds a token without an unreachable
   predicate — but `pool_truncated` is dormant because *today's data* never reaches it, whereas
   `no_surplus` would be dormant *by construction*, which is a different and weaker claim.

My reading: **(1) now, and (3) only if the owner wants the second token badly enough to accept a
by-construction-dormant member.** The label is false today and fixing it costs nothing; the
token split cannot be derived without re-adopting a rejected mechanism.
