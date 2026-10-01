# #188 DESIGN EVIDENCE: the "bounded/partial" state is not missing — it has been invented FIVE times

#188 records the absence vocabulary as needing "FIVE states, not four — 'bounded/partial' is the
gap," and two places in the code point at it: `player_universe`'s availability docstring ("see
#188, which is the register item for the 'bounded/partial' state this vocabulary still lacks")
and `test_availability_haircut`'s header, in the same words.

**That framing is inverted.** A complete derivation of the corpus finds the state already
implemented, independently, in five places under five different names — and shared by none of
them.

## Method, and why the first attempt was thrown away

A first scan filtered module-level constants through a hint regex of guessed keywords
(`_BASIS`, `MEASURED`, `NO_*`, …). It returned 25 tokens and **under-counted**: it caught
`APPETITE_MEASURED` while missing `APPETITE_IMPUTED` and `APPETITE_UNAVAILABLE`, which do not
match any guessed word. That is the same "plausible answer about something else" failure this
repo's measurement doctrine is built around, so it was discarded rather than reported.

The result below comes from parsing every non-test module's AST, taking **every** module-level
UPPER-CASE string constant (144 of them), grouping by name prefix into families, and then
reading each candidate's definition to confirm what it actually means. No keyword guessing.

## The five independent implementations

| module | token | value | what it declares |
|---|---|---|---|
| `lineup_optimizer` | `BYE_PARTIAL` | `'partial'` | some byes unknown, so the week's numbers are **a FLOOR, not the cost** |
| `lineup_optimizer` | `DISPLACEMENT_ROSTER_PARTIAL` | `'roster_partially_priced'` | the roster is only partly priced |
| `player_universe` | `RULE_FLOOR` | `'rule_floor'` | a rulebook-derived **floor**, not a point estimate |
| `draft_room` | `REPLACEMENT_BASIS_POOL_TRUNCATED` | `'pool_truncated'` | the pool ran out before the anchor |
| `provider_meter` | `TRUNCATED` | `'truncated'` | the output was cut short |

`BYE_PARTIAL` is the sharpest instance, and its own comment is almost a specification for the
state #188 asks for: *"The solve still runs over the ones that do, but the answer is a FLOOR
rather than the cost: a player whose bye is unknown might also be out that week, and treating
unknown as 'available' would understate every collision by exactly the players nobody could
resolve."*

**Excluded after checking, rather than pattern-matched in:**
`REPLACEMENT_BASIS_STARTABLE_FLOOR` contains "floor" but names **which anchor was used** (the
startability floor), not that the value is a bound — a different axis.
`INCOMPLETE_PLAYER_PROFILE` is a UI display string, not a basis token.

## What the evidence says

**The design question #188 poses is already answered by the code — five times, consistently.**
Every independent author reached for the same concept and the same semantics: *some evidence
was available, the computation ran on it, and the result is a bound rather than the quantity.*
Nobody invented a different meaning; they invented different **names**.

So the decision in front of the owner is not "should a fifth state exist" — the corpus has
settled that empirically. It is **"which of these five names becomes the shared one, and which
vocabularies adopt it."** That is a smaller and much safer decision than the item implies:
promoting a proven state to shared use is a refactor, whereas inventing one would be a design
commitment.

**This is #126's landmine at the vocabulary layer** — one concept, five homes, no single source
— and it is the same shape as the five separate constants all equal to the string `'measured'`
(`APPETITE_MEASURED`, `DENIAL_MEASURED`, `EXPOSURE_MEASURED`, `DISPLACEMENT_MEASURED`,
`BYE_MEASURED`). Verified: identical value, five definition sites. Nothing enforces that they
stay identical, and a consumer comparing bases across quantities would silently diverge the day
one drifts.

## What this does NOT decide

Which name wins, and whether every vocabulary should carry the state or only those that can
actually produce a bounded value. Both are the owner's, and #188 is filed as design evidence
precisely so the decision rests on something derived rather than asserted. The contribution here
is the enumeration and the inversion of the premise — not a ruling.

## Method note, and the reason it is stated here

This finding was written immediately after **my own #122 finding was withdrawn in full** for
claiming a repair was missing when it already existed. The correction cost is what prompted the
complete-enumeration method used above rather than a second keyword scan. The two errors have
the same shape — asserting absence without exhaustively looking — and #188's own premise turns
out to be a third instance of it. That is worth recording as a pattern rather than three
separate slips: **in a codebase this disciplined, "X is missing" is the claim most likely to be
wrong, and it is cheap to check before it is expensive to publish.**
