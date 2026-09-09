# PHASE 2: the WR replacement level is CORRECT — and a new seam opened underneath it

Steps 1–2 of the agreed sequence. Probe: `phase2_replacement_read.py`, which intercepts
`replacement_levels` and locates the returned level's player **by identity** in the pool
production handed it. Nothing reconstructed.

FLEX has no level of its own — `shared_slot_alternatives` prices a flex as `max(level)`
over its eligible positions — so `FLEX_8`'s phantom **is** the WR level, and steps 1 and 2
collapse into one read.

## Step 1–2 answer: the level lands exactly where the contract says it should

At 2 tight ends held (pick 109), league starter demand WR = 36.6, RB = 36.6, TE = 24.6,
QB = 22.2:

| position | remaining pool | level | lands at rank | demand rank | the player |
|---|---|---|---|---|---|
| **WR** | 198 | **217.75** | **37** | 36.6 | **Jordan Addison** |
| **TE** | 115 | **149.17** | **25** | 24.6 | **Cade Otton** |

**Rank 37 against a demand of 36.6. Rank 25 against 24.6.** The level is the next receiver
after the league's starting slots are accounted for, on a real named player. That is
precisely what the contract promises.

**So the phantom is right too.** `__free_WR_3` worth 217.75 means "if you pass, this slot
gets a Jordan-Addison-tier receiver for free" — and with 198 receivers remaining against
36.6 league starting slots, **that is true**. A chair holding eight tight ends genuinely
should start a free WR37 ahead of its fourth-best tight end. The phantom out-starting a
chair's ninth and tenth-best players is correct behaviour, not a defect.

`startable_floors` was `{QB: 162.0}` — the documented superflex QB floor, applying to QB
only, exactly as designed.

## Three primitives now exonerated in sequence

1. **`displacement_level`** — Phase 1, Fork A: `displaced` is exactly the entity that leaves.
2. **The optimizer** — same read: one entity leaves, no cascade ambiguity.
3. **`replacement_levels`** — this read: the rank lands on the demand rank, on a real player.

All three produce correct numbers. **The engine still drafted 101 tight ends.** So the
defect is not in any of these three, and by elimination it is downstream — in what
selection does with correct inputs. That is **B4**: `simulate_full_draft` picks through
`pick_synthesis.build_snapshot` → `candidates[0]`, which re-sorts, and the board's
`final_score` order is not the pick order.

## NEW OBSERVATION — recorded, deliberately not interpreted

At **7 and 8 tight ends held (picks 182 and 206), `replacement_levels` returned EMPTY
dicts on every call** — `calls this board: [[], []]` — while the same board's
`displacement_adjustments` received `level_TE = 80.36` and `149.17` respectively.

**Levels reached the displacement term that `replacement_levels` did not return on that
board build.** Two calls, both empty, and a populated `point_replacement` downstream.

I am not claiming why. Candidates, none tested:
- a cached anchor path (one exists — see #123's anchor cache) supplying levels when the
  live computation declines;
- a second producer of `point_replacement` not on the path I traced;
- a legitimate domain omission (`replacement_levels` omits a position once demand drops
  below one whole slot) combined with a downstream fallback;
- an artifact of the interception itself, which must be ruled out first.

**This is the next read, and it is a bigger question than the one it interrupted:** if a
number can reach the valuation path without coming from the function that is supposed to
produce it, then "which quantity is authoritative" is unresolved at this boundary.

It also means the earlier question — *why do levels return exactly to prior values
mid-draft?* — cannot be answered until this is: 149.17 appearing at both 2 held and 8 held
may be the same computation twice, or it may be one computation and one fallback.

## Status

- No engine source modified anywhere in #222.
- Flex-anchor candidate still stranded, and now for a stronger reason.
- No battery. Still a semantic read.
- Next: rule out interception artifact, then find what supplied the levels at picks 182/206.
