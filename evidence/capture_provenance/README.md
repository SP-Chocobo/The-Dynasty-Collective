# A league capture holds three kinds of value, and nothing marks which is which

Surfaced by the owner's own question — *"startup draft sizes are based on bench and roster
slots, not a fixed amount"* — which is correct, and checking it turned up something else.

## The test

Recompute every stored value in `data/league_captures/fourth_and_forever.json` from that same
file's **primary** fields (`roster_positions`, `total_rosters`). Anything that reproduces is
cached derivation; anything that does not is either wrong or carries information from elsewhere.

| field | recomputes? | what it really is |
|---|---|---|
| `roster_positions` (29 slots), `total_rosters` (12) | — | **primary** — transcribed from Sleeper |
| `scoring_settings_observed` (30 keys) | — | **primary**, and externally verified: reproduces the live app to the cent on four real box scores (`evidence/rulebook_ground_truth/`) |
| `draft_math.draftable_slots_per_team` = 26 | **yes** — 29 slots − 3 IR | derived, cached, currently correct |
| `draft_math.total_picks_if_startup` = 312 | **yes** — 26 × 12 | derived, cached, currently correct |
| `draft_math.starter_slot_counts` | **NO** | **an engine constant in disguise** |
| `draft_math.league_starters` | **NO** | same, × 12 |

## The finding: an engine constant is sitting in a league capture

`starter_slot_counts` reads `{QB: 1.85, RB: 3.05, WR: 3.05, TE: 2.05}`. Decomposed: FLEX splits
evenly three ways, and **SUPER_FLEX contributes 0.85 to QB** and 0.05 to each of RB/WR/TE.

```
draft_room.SUPER_FLEX_QB_SHARE   = 0.85
capture's implied SF -> QB share = 0.85      identical
```

That number is **not an observation of Fourth and Forever.** It is the engine's own hand-set
constant, written into a file whose stated `capture_method` is *"transcribed from Sleeper Scoring
Settings screenshots supplied by the owner."* A reader — or an instrument — takes the whole file
as observation, and for two of its fields that is false. The engine can read back its own
assumption as though the league had confirmed it.

`run_216_flex_share_probe.py` already names the constant as the exception it is: *"SUPER_FLEX is
the one exception, and that exception is a hand-set constant (`SUPER_FLEX_QB_SHARE = 0.85`)."*
**#56** forbids exactly this shape, and **#216** (in progress) is the item that owns it. What
this adds is that the constant has **leaked out of the engine into the evidence**.

## What is NOT claimed

- **No number here is wrong today.** The two derivable fields recompute exactly; the two
  contaminated ones are internally consistent with the constant they encode.
- **Nothing currently reads the contaminated fields.** Grep finds no instrument consuming
  `starter_slot_counts` or `league_starters` from the capture; the engine computes its own.
  This is a provenance defect and a trap, not an active miscalculation.
- **`run_roster_proof_ff.py` is unaffected.** It reads only `draftable_slots_per_team`, which is
  purely derivable and verified to recompute.
- **Whether 0.85 is the right share is not settled here.** That is #216's question. This says
  only that the capture cannot be used as evidence for it.

## The second-order finding: nothing derives "draftable"

Every instrument in the repo sizes a draft as `rounds = len(roster_positions)`. For F&F that is
**29**; the real startup ran **26**, because the 3 IR slots are not drafted. Two hand-listed
vocabularies exist — `draft_battery.NON_STARTING_SLOTS` and `league_config.NON_PLAYING_SLOTS`,
identical strings in two homes (#126) — but **both mean "does not START", not "is not DRAFTED".**
Those differ: TAXI does not start and *is* drafted; IR does neither.

The draftable rule exists nowhere in code. It exists as prose in one JSON file.

**Latent, not active:** `build_mock_league` emits no IR or TAXI, so every committed measurement
is correct. It goes live the moment anyone drafts a real captured league — which is what
`run_roster_proof_ff.py` does. That run is right only because it read the capture's hand-written
26 instead of the idiom every other instrument uses. Writing the normal line would have produced
a 29-round result reported as Fourth and Forever.

## The remedy, stated but not taken

1. `draftable_slots(roster_positions)` in code, one home, with the IR/TAXI distinction tested —
   replacing the prose, so the next real-league measurement cannot get it wrong.
2. One slot vocabulary with three named questions: does not start / does not play / is not
   drafted. Currently two sets and a JSON comment.
3. Mark or remove the engine-derived fields in the capture so provenance is legible.

None is taken here. (1) and (2) touch shipped modules while two measurements are in flight, and
(3) is entangled with #216's open question about the constant itself.

## Method note

The first recomputation of `starter_slot_counts` used a naive even split (SUPER_FLEX → QB 0.25)
and reported "8 of 10 disagree." Both models sum to 10.0, which is what exposed it: two
allocations of the same ten slots cannot both be wrong about the total, so the disagreement was
in the model, not the data. Caught before publication by checking the sums. Same shape as #241,
one hour later.
