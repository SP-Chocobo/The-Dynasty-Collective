# Phase 1, measurable half — what the engine produces and what crosses to a provider

Post-freeze roadmap v3, Phase 1. Measured at `a9eaae0` (Phase 2's commit), on the real capture
universe (6,595 players) and a real mid-draft `12T_ppr` board.

Phase 1's deliverable is the Surface Specification, and the roadmap constrains it with "a fact
inventory of what the engine actually computes, so screens cannot invent fields that do not
exist." The screens half needs product decisions **D1** (operating rung) and **D2** (which
surfaces ship) and is therefore the owner's. The inventory half is measurement, needs no decision
and is done here — along with the factual half of **Gate C**, which asks what a provider may see
and cannot be answered as a posture until someone has measured what it currently sees.

## 1. The population — not a new enumeration

`quantity_readers.produced_quantities()` already answers "what does this engine produce":
**103 quantities** drawn from the engine's declared output surfaces (the board's own column
lists, the snapshot dataclasses, the analysis dicts), each already classified by what reads it:

| class | count | meaning |
|---|---|---|
| `DECISION` | 41 | read by a module that computes a value or an ordering |
| `OBSERVABLE` | 36 | read only by UI or diagnostics — correct for many, not a defect |
| `WRITE_ONLY` | 12 | read by nothing in production (`#138`) |
| `DECOMPOSITION` | 10 | the term works; its published form is unread (`#119`) |
| `CARRIED` | 4 | relayed into another output, consumed by nobody |

Nothing here re-enumerates that. A second enumeration of the engine's vocabulary is the defect
this audit found in six costumes: two readers for one question, and the stale one easier to reach
(`#126`).

## 2. What crosses to a third-party model provider

`fact_exposure.py --check`, over `pick_debate.py`'s prompt-construction call graph:

```
103 produced quantities (quantity_readers)
48  read by the prompt path in pick_debate.py -- the upper bound
3   of those are WITHHELD today and gated off before emission:
        expected_value_of_waiting
        opportunity_cost
        survival_probability
45  actually reach a third-party provider today
```

**Read is not emitted, and the difference is load-bearing.** A scan that stopped at "the prompt
path reads `survival_probability`" would report the survival family as crossing to a third party
— contradicting a repair made specifically to stop it. `pick_debate.py:577` gates emission on
`survival_is_presentable()`; what the model receives instead is an explicit sentence that the
number is withheld and must not be reconstructed. Verified behaviourally on a real board, not
inferred from the gate's existence:

```
Picks before your next selection: 0. The survival probability is WITHHELD, not missing:
it is computed, and it failed its calibration check against real drafts, so do not
estimate one yourself from this count.
```

**The conditional class is the one a posture has to enumerate in advance.** Those three
quantities are one flag away from crossing with no code diff at all: the day
`SURVIVAL_IS_CALIBRATED` flips, three engine quantities begin reaching a third party and nothing
in the diff says so. That is why `withheld` is a named class in the census rather than folded
into either neighbour.

**Why field names were not searched for in the emitted text.** The formatters emit human labels
— `Pick necessity: 73.3/100`, `Universal value: 217.89 = bpa 219.91 + horizon -2.02 + risk +0.0`
— so the literal string `pick_necessity` appears in a 41,237-character prompt exactly **zero**
times. A name scan over the output would have reported almost nothing exposed, and the conclusion
would have been confidently wrong. The prompt builder's only source of engine facts is the
snapshot object, so the question is which attributes it reads, answered over the AST.

**Scope, stated rather than implied.** Two modules call providers. `pick_debate.py` is covered.
`llm_engine.py` — the Prytaneum panel path (`ask_beat`, `ask_quant`, `run_debate`,
`ask_moderator_followup`) — is **not**: its facts arrive through conversation and
`screen_context`, not off a snapshot object, so this technique would not answer the same question
about it. A second census is needed before Gate C's posture can claim to cover the whole product.

**The ratchet.** `CENSUS` records today's 48. A quantity entering it is a disclosure change and
must be a deliberate one; `--check` returns 1 and names what newly crosses. Widening only —
a quantity that stops crossing is a repair, and a check that failed on repairs would be disabled
within a week.

## 3. The cost envelope, sized

The call envelope was already **counted** (`test_cost_envelope_boundary`: `debate_pick` = 3
provider calls, no retry, no loop, no recursion — a real guarantee). It had never been **sized**.
Measured by stubbing `PROVIDER_CALLERS` and capturing what each call would have been handed; no
provider was called.

On a real 44-candidate mid-draft board:

| chair | system | user | est. tokens |
|---|---|---|---|
| strategist | 3,526 ch | 41,237 ch | ~11,191 |
| skeptic | 2,008 ch | 41,420 ch | ~10,857 |
| caller | 3,023 ch | 41,654 ch | ~11,169 |
| **per debate** | | **132,868 ch** | **~33,217** |

One debate per pick over 14 rounds ≈ **465,000 input tokens per seat per draft**:

| model | input-only, per seat per draft |
|---|---|
| Opus 5 ($5/1M) | ~$2.33 |
| Sonnet 5 ($3/1M) | ~$1.40 |
| Haiku 4.5 ($1/1M) | ~$0.47 |

Token figures are a 4-chars-per-token estimate, labelled as one — no tokenizer is available
offline. Output is **not** in these numbers: `MAX_TOKENS` is 4096 per call, so up to 12,288
output tokens per debate on top, at 5× the input rate.

Not to be confused with `test_context_budget_boundary`'s "roughly 8.4k tokens": that is the
*Prytaneum chair's* deterministic context on the `llm_engine` path. Different path, different
number.

### The finding that matters for Phase 4

**The 41k-character evidence block is sent three times and is 93% of the input cost.** It is a
literal prefix of all three user prompts — `evidence`, then `evidence + strategist`, then
`evidence + strategist + skeptic`.

It is nonetheless **not cacheable as the calls are currently shaped**, because a provider's
prompt cache matches on the request prefix in order, and each chair has a *different* system
prompt sitting ahead of the shared evidence. The prefix diverges before it reaches the part worth
caching. Capturing that redundancy is a deliberate restructuring — one shared system block ahead
of the role instruction, or the role moved into the user turn — not a flag.

This belongs to Phase 4, and it is the roadmap's own point that the economic shape is inverted
from normal software and needs measuring rather than asserting. Phase 2 found the LLM path is the
hull's largest consumer (75 of 260 calls, 28.8%); this says what those calls cost.

## 4. What this unblocks, and what it does not

Unblocked and delivered: the fact inventory's derivable columns — what the engine produces, what
reads it, what has a basis companion, what is withheld today, what crosses to a provider.

Still the owner's, and not guessed at here:

- **D1 / D2** — the Surface Specification's screens, and therefore the "what question does this
  answer?" column. A fact inventory constrains screens; it does not design them.
- **Gate C's posture** — what retention is acceptable, whether provider terms permit the
  commercial pattern, and what the user is told. The measurement above is the input to that
  decision, not the decision.
- **Gate A** — unchanged and untouched by this. Nothing here exposes anything to a third party
  that was not already being exposed.

One gap this creates work for rather than closes: `llm_engine.py`'s census, needed before Gate C
can claim product-wide coverage.
