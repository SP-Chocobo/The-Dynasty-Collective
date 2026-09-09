# The mechanism: late in a draft, VOR stops measuring scarcity and starts measuring pool depth

## The controlled test

RB and WR have **identical** starter demand in Fourth and Forever -- 3.05 slots per team,
36.6 league-wide, from `draft_room.starter_slot_counts`. Nothing on the demand side
prefers either. So drain both by the SAME NUMBER of players off the top and read the
anchor. Any divergence is pool depth alone.

`evidence/roster_shape/ff_rulebook/drain_probe.py`, real F&F rulebook, real priced board.

| drained from each | QB maxVOR | RB maxVOR | **WR maxVOR** | TE maxVOR |
|---|---|---|---|---|
| 0 | 104 | 208 | 161 | 154 |
| 10 | 220 | 155 | 85 | 136 |
| 20 | 276 | 140 | 73 | 145 |
| 30 | 108 | 125 | **82** | 83 |
| 35 | 28 | 116 | **82** | 43 |
| 40 | -- | 105 | **82** | 16 |
| 45 | -- | 72 | **85** | 3 |

**TE collapses 154 -> 3. QB exhausts entirely. RB decays 208 -> 72. WR stops decaying at
82 and stays flat.**

By the back half of a draft, WR is the only position still showing material VOR. An engine
ranking on a VOR-derived value therefore takes receivers, pick after pick, for the entire
bench phase -- not because receivers are scarce, but because they are the last position
whose number has not collapsed.

That is the +10 points of WR share. It is not a tuning error and no constant produced it.

## Why it happens

VOR = (best remaining at the position) - (the player at replacement rank). Both terms fall
as the pool drains. Whether their DIFFERENCE falls depends on the shape of the projection
curve between the top and the replacement rank:

- **Steep then flat** (TE, QB): drain the steep part and the top converges on replacement.
  VOR -> 0. This is VOR working correctly -- the position really is exhausted.
- **Long and near-linear** (WR, 105 priced against a rank of 36.6): the top and the
  replacement rank fall TOGETHER, so their difference is a constant. VOR never decays.

So in the bench phase VOR is reading **curve linearity**, not scarcity. Two positions with
identical demand and identical drain get different answers purely because one has more
bodies. Every fantasy pool has more receivers than backs, so the bias has one direction in
every league, always.

## This is the anchor being used outside its own stated domain

`replacement_levels`' docstring already contains the warning, from the #216 pass:

> "while demand stays positive and picks come off the TOP -- starter-filling picks -- rank
> shrinkage and pool drain cancel exactly... CORRECTED (#216): that cancellation holds ONLY
> for starter-filling picks. A BENCH pick at a position drains the pool without reducing any
> team's starter demand, so it moves the level."

The docstring identifies the regime and stops. Nothing in the code acts on it. In Fourth
and Forever, **10 of 26 rounds are starter-filling and 16 are not** -- so the anchor spends
62% of the draft outside the regime it documents, still returning a number, and that number
silently changes meaning from "what waiting costs" to "how deep is this pool".

The existing DOMAIN guard does not catch it. That guard omits a position once LEAGUE-wide
demand drops below one whole slot; league WR demand is 36.6, so it never fires in a
26-round draft. The domain is about league demand; the defect is about MY roster having no
slot left at stake. Those are different conditions and only the first is implemented.

## What this does NOT say

- It does not say the engine should draft 37% WR. That number belongs to twelve managers
  in one league and nothing may be calibrated to it (#56).
- It does not say WR is overvalued. At the top of the board WR carries the most NEGATIVE
  mean universal_value of any position (-33.40). The defect is confined to the bench phase.
- It does not yet say the fix. It says where to look, and it says the quantity that has
  gone wrong is already named and documented in the function that computes it.

## Next

The full 12x26 draft on this rulebook is running; its by-quarter composition drift is the
direct confirmation -- WR share should climb sharply in the back half. That measurement,
not this one, is what a repair has to move.
