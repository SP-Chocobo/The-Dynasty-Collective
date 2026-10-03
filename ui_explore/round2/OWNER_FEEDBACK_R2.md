# Owner feedback on the eight round-2 variants (verbatim), 2026-10-03

> Ledger A isn't bad. May be a cleaner option without the rail, but not bad. Lanes A does the
> comparisons well, but the actual "who is better than who" is muddy. the resizing does help
> though. Trio A is a no.
>
> Doors A has a lot good going for it. I think I'd want an updated version of this before taking
> it to others, tbh. It reorders based on recommendation, which is nice. has clear 1,2,3,4 in each
> position, easily filtered. good. door order is a little unclear what it's trying to tell you,
> both on the tags and the "the orders disagree at this pick" message, since every pick says that,
> and it always follows the board. cards may be a little unclear on the "wait, and # leaves X -
> costs X" so that could get cleaned up a little. dont love the clock/roster bar, that'd need
> reworking. the doors at the bottom feel a little empty, so either those get resized smaller, or
> find a more effective way to use the space. rosters button may need a little love, but the other
> buttons look fine. theres some other stuff, but not bad. genuinely intuitive.
>
> GW ledger wants to be clever, but misses it a bit i think. GW Doors is ok. meh. dont love the
> way the order shows up near the bottom. GW Trio, no. GW 4 cells... not bad. genuinely intuitive,
> clean dissemination of information. may need some rework as well, but genuinely a strong contender

Follow-up: *"rewworks of those versions I latched onto as not awful. ideally with the same bot that
made them. let's try to super-polish these into submission. also contemplate if the gas-tank idea
is worth reviving or not."* — **"without the meh grouping"**, which cuts GW Doors.

## Disposition

| variant | verdict | action |
|---|---|---|
| Doors A (`fableA/v4_doors`) | front-runner, "genuinely intuitive" | deep polish; his 5-item list |
| GW Four Cells (`fableB/v4_cells`) | "genuinely a strong contender" | deep polish; no defect list given |
| Ledger A (`fableA/v1_ledger`) | "isn't bad" | rail-less variant, single-variable change |
| Lanes A (`fableA/v2_lanes`) | comparisons good, ranking muddy | make the better-than relation legible |
| GW Doors (`fableB/v2_doors`) | **"ok. meh."** | CUT by "without the meh grouping" |
| Trio A, GW Trio, GW Ledger | "no" / "misses it" | CUT |

## Verified against the payload, not taken on trust

Doors A's order line is coded as a conditional (`agree ? … : …`) but resolves to **disagree in all
three reference states**, while the doors follow board value order in all three. It is a constant
dressed as a conditional (`#254`) announcing something with no consequence. The owner found this
unaided ("every pick says that, and it always follows the board").
