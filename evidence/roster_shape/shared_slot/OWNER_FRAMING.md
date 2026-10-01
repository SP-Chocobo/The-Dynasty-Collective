# The owner's own description of roster building, and what it settles (#221)

Recorded verbatim, in this session, unprompted by any of the measurements below:

> "in the context of roster building, usually you have your highest scoring players in the slots
> that are explicit to that position, so then when filling flex positions, you're doing so with
> the highest projections or best odds of popping off out of your remaining depth."

> "Granted, you swap flex players and main slot players in accordance with gameday, so your later
> games (sunday, monday, vs thursday) are on flexes as just in case insurance, so you can still do
> swaps on flex with more flexibility. but for the purposes of building, this is how you look at
> the roster"

## What the first paragraph settles

Restated as pricing: **a flex slot draws from ONE pooled remainder of the positions it admits, so
it has ONE alternative.** If I pass on this candidate, the seat is filled by the best of what is
left across RB/WR/TE — not by "the best remaining player at the candidate's own position."

That is `shared_slot_alternatives` exactly, and it is the premise the shipped engine violated: the
per-position phantom priced a tight end against the best free TIGHT END and a running back against
the best free RUNNING BACK **for the same seat**, which the description above says is not how the
seat is filled. This is independent confirmation of the construction from the board's side rather
than the arithmetic's, and it arrived after the change was measured, not before.

It also explains, without special pleading, the owner's-league result the waves flagged. His league
has no TE slot, so nobody in it drafts tight ends, so a free tight end really is the best thing
available for a flex — and TE's replacement level really is the highest of the four. Under his own
description the flex is therefore expensive for everybody, and the cheap seats are the dedicated
ones. That is a consequence of the rulebook, not a defect in the term. Whether the SHAPE it
produces there is the one he wants is a separate question and is not answered here.

## What the second paragraph does NOT settle, and is deliberately not folded in

Parking a late-slate player on a flex as gameday insurance is **lineup management, not draft
valuation**, and he says so himself ("for the purposes of building, this is how you look at the
roster"). Two reasons it stays out of the pricing path rather than being quietly absorbed:

  * The engine has no kickoff-time input. Adding one to satisfy this would be inventing a
    quantity nobody measured, which is #56.
  * It is a property of a WEEK, not of a roster. The draft-time question ("what is this player
    worth to this roster") does not change because a Monday game lets you swap later.

A third statement in the same exchange belongs to the same item, and he scoped it himself:

> "also, injured or questionable players usually you want on your flex slots instead of dedicated
> ones, due to the same flexibility, just in case, for things like game-day decisions"
> "but you're right, thats a non-factor on drafting, so irrelevant to this"

Same shape, same verdict, and confirmed by the owner rather than assumed by me. Note that this one
would have been the more tempting of the two to absorb, because the engine DOES carry injury status
(`risk_adj`, #191/#202) and so a wiring for it exists. It is still a WEEKLY placement preference
among players already rostered, not a statement about what a player is worth to acquire.

Registered as one item rather than as a silence: **preferring late-slate and questionable players
on flex slots is a LINEUP surface concern (start/sit), belongs wherever weekly lineups are set, and
never in `displacement_level` or any draft-time price.**
