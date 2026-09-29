# Owner decisions pending — accumulated during the repair run

Everything here is a call I should not make alone. It is written to be read in one sitting and
answered in a picker, so each item states **the question**, **the options**, **what I recommend**,
and **what it costs to be wrong either way**.

Nothing in this file is blocking a repair I could otherwise finish. Where an item blocked
something, the repair around it is done and the blocked half is named.

Also recorded at the bottom: **questions I expected to bring you and then answered by measurement
instead**, so you can see what was decided without you and object if you disagree.

---

## D1 — `rival_premium_basis`: should it borrow `denial_basis`? (from 2.5, the sixth of six)

**Correction to how I first wrote this up.** I described the borrow as the *proposed* fix. It is
the CURRENT STATE: `draft_strategy.py` already emits `"rival_premium_basis": denial_basis`, and the
comment beside it presents the borrow as deliberate — *"the companion, same vocabulary denial_basis
uses"*. So the question is not whether to start borrowing; it is whether to keep doing so.

**The question.** Five of 2.5's six absence-contract breaks were repaired. The sixth is
`rival_premium`, whose basis string is not its own: it is `denial_basis`, computed for a different
quantity in the same loop.

**Why I stopped.** `denial_basis` answers *"why was this player's denial value what it was"*.
`rival_premium` is a different number, and a basis that describes a neighbouring one reads as
corroboration for the rest of the codebase's life (`#193`: an admission on evidence with no
number). The two agree today because they are computed from the same rival scan — but nothing
enforces that, and if they ever diverge every consumer has been told the wrong provenance and
nothing will notice.

**Options.**
  * **(a) Keep the borrow, and pin it.** Zero code change plus one test asserting the two are
    computed from the same scan, so a future divergence fails loudly instead of lying quietly.
  * **(b) Give `rival_premium` its own basis vocabulary.** Correct, and the work is a day: the term
    has four distinguishable states and each needs a name and a test.
  * **(c) Withdraw the borrowed label and report absence.** `None` is honest and consumers already
    handle it (`#187`), but it removes a string that is *correct today* from every surface.

**My recommendation: (a) now, (b) when the term is next touched.** This is a change from what I
first wrote, and the reason is the correction above: with the borrow already shipped, (c) is no
longer "leave it alone", it is a removal that makes surfaces less informative to guard against a
divergence that has not happened. (a) costs one test and converts the silent risk into a loud one.

---

## D2 — 2.2: what should the app DO when the config gate refuses? (policy, not mechanism)

**Status: the mechanism half is repaired and measured; only the policy is yours.** The gate used to
refuse **53 of 53** production-shaped leagues, for two wrong reasons, and both are fixed — see the
answered list below. After the repair it refuses exactly the leagues whose dynasty flag is genuinely
absent, which is the same verdict `draft_battery`'s own comment reaches independently, arm for arm.

**The question that remains.** The gate now gives a trustworthy verdict. What does the app do with
it? The mandate is explicit that one thing is NOT a design question: *a board built on a config the
gate would refuse should not be silently priced.* Everything past that is yours.

**Options.**
  * **(a) Refuse.** `decision_config` already raises. The Draft Room shows the reason and no board.
    Honest, and it means a league with an unreadable slot cannot be drafted from — including, today,
    a league whose dynasty flag never arrived.
  * **(b) Price, and carry the refusal on the board.** Build the board, and put the gate's reason on
    every surface that renders it, the way `availability_basis` already travels with a price. You
    keep drafting; nothing can read a number without reading what is doubtful about it.
  * **(c) Refuse only the terms that actually depend on the missing key.** An absent `type` makes
    `time_horizon_adj` and `risk_adj` unpriceable — withhold those two and price the rest. Most
    faithful to the engine's own absence contract, most work, and it needs a dependency map from
    each format-deciding key to the terms that read it.

**My recommendation: (b) now, (c) as the eventual shape.** (a) is correct and would have made the
app unusable on your own league for as long as the capture lacks a dynasty flag — which is not a
hypothetical, it is the state today. (b) satisfies the mandate's one non-negotiable and keeps you
drafting. (c) is where this should end up, and it is a Tier 3-sized job, not a 2.2-sized one.

**What it costs to be wrong.** Choosing (b) and then never doing (c) means a board that is
technically labelled but practically trusted. Choosing (a) means the Draft Room goes dark on a
config you could have read around.

---

## D3 — `#30`'s streaming floor: re-derive over the kicker repricing?

**The question.** 2.3 repaired kicker scoring: the league scores a generic `fgmiss`, Sleeper
projects only bucketed misses, and neither vocabulary could reach the other, so **no missed field
goal of any length was ever scored**. Repaired with the total (`fga − fgm`) rather than the
vendor's bucketed sum, because the buckets are incomplete.

**What it moved.** Every kicker loses **4.22–6.44** points (mean **−5.40**) and none gains, because
a miss can only cost. **16 of 33 kickers change rank.** The top five hold their identity and order.

**Why it is yours.** `#30`'s streaming floor was DERIVED from K ordering (register `#56`: constants
are derived, not calibrated). The ordering it was derived from has changed for half the position.
Re-deriving is a measurement I can run; whether the floor should move is a judgement about whether
the *derivation* is still the one you want, given `#21` is already blocked on `#50` for the same
constant family.

**Options.** (a) Re-derive now and ship whatever falls out. (b) Re-derive and report, ship nothing
until you have read it. (c) Leave it; the top five are unchanged and streaming decisions live at
the top.

**My recommendation: (b).** The measurement is cheap and I should not ship a moved constant on my
own authority. (c) is defensible — the argument that streaming only cares about the top of the
position is real — but it is an argument you should get to make rather than inherit.

---

## D4 — `#184` / task #36: a percentile-to-points conversion for the upside growth term

Carried from 1.3. `growth_signal` is a percentile; everything it is added to is points. The
conversion factor is an engine-design choice with no measurement that settles it, which is exactly
what `#184` marks. Deferred post-freeze by agreement; listed here so it is not lost.

## D5 — task #37: a deliberate ordering policy for the upside branch's flat regions

`mode="auto"`'s upside switch has regions where several candidates tie exactly. Today the residual
tie is broken by whatever order the frame arrived in. 1.3's repair established the precedent — a
stated CONVENTION for a residual tie is acceptable where it is *stated* — so this needs a chosen
convention, not a discovered one.

## D6 — task #21: blocked on `#50`

The floor cannot be derived while the board asserts two conventions. Unchanged since `27c54ee`;
recorded so the block is visible rather than implicit.

---

## D7 — 3.2: should the fieldability bound extend to flex-reachable groups? (needs a depth allowance)

**Status: the derivable half is repaired and certified; this half needs a number you choose.**

**What was repaired.** `fieldable_ceiling` bounds one position at a time — `slots(P) + 1`, the
second term being the one bye week every team has. A player eligible at TWO ceilinged positions
consumes a slot from either, and the engine was counting a pick only when it had exactly one
eligible position, so every multi-eligible player was counted at no position at all. The battery
measured the cost on HEAVY_IDP: **ten rosters over the ceiling, each by exactly its number of
multi-eligible holdings** — roster 2 held 6 LB, being 3 counted and 3 skipped edge rushers eligible
at {DL, LB}. The bound is now taken over the group a roster's own players span, which for a
one-position group is the old number exactly.

**The question.** 3.2 asks for the same bound on flex-reachable groups, and names the case: a
roster at `slots_reachable(P) + 1` for DL, LB *and* DB holds six IDP and the optimizer starts one,
because a single `IDP_FLEX` admits all three. The joint bound there is `1 slot + 1` = **2**, and it
would catch what nothing catches today.

**Why I stopped.** The same arithmetic applied to the offence group is not survivable. Measured on
the battery's own rosters: it would flag **12 of 12 seats in 12T_ppr** (holding 12–13 players
eligible within RB/WR/TE against `7 slots + 1`) and **9 of 12 in HEAVY_IDP**. Those are ordinary,
correct rosters — a 14-round draft into 7 offensive slots *must* carry about twelve. And
`unfieldable_last`'s own docstring sets the test this fails: *"IT IS A BACKSTOP AND MUST STAY ONE,
by `feasibility_first`'s own test -- whether it binds on a roster that was never in danger."*

The reason the arithmetic does not transfer is in `#30`. The `+ 1` is justified by the measured
finding that the churn a spare buys is **free on the waiver wire**, which is true of a flat,
dedicated, streamable position and false of RB/WR, where bench depth is the point of the bench. So
the joint bound is sound as a statement about ONE WEEK and needs a *depth allowance* before it can
be a backstop — and an allowance is a number somebody chooses, which is the line I did not cross.

**Options.**
  * **(a) Extend it only to groups whose positions are all streamable**, with the allowance derived
    from `#30`'s streaming baseline rather than chosen. Catches the IDP_FLEX case, leaves offence
    alone. Needs `#30` re-derived first (see D3), and needs "streamable" to be a derived property
    rather than a list of positions.
  * **(b) Extend it with a per-group depth allowance you set.** Honest and immediate: the bound
    becomes `slots + 1 + allowance(group)`, and the allowance is recorded as a stated CONVENTION
    the way 1.3's tie-break was. Cheap, and the number is visibly yours rather than derived.
  * **(c) Leave it.** The IDP_FLEX over-accumulation stays uncaught. It is real — 3.2 measured six
    of twelve rosters holding 6–7 IDP against a bound of 2 — so this is a decision to accept a
    known loss, not a no-op.

**My recommendation: (b) now, (a) when `#30` is re-derived.** (c) leaves a measured defect in place
for an unbounded time. (a) is the right end state and is blocked behind D3. (b) gets the guard
working against the case that motivates 3.2 while keeping the chosen number visible and revisable,
and a test already pins that the backstop does not fire on an ordinary offence roster, so the day
someone sets the allowance too low it fails loudly.

**What it costs to be wrong.** Too small an allowance demotes legitimate bench depth and the engine
starts declining players it should take. Too large and the guard never binds, which is where we are
now for flex-reachable groups.

---

# Answered by measurement instead of by you

These were heading for this file and did not need to. Recorded so you can object.

1. **2.2's `type` key — does it belong in the gate?** I expected to ask. It does, and no decision
   was needed: `draft_room` reads `league["settings"]["type"] == 2` and gates BOTH `time_horizon_adj`
   and `risk_adj`'s trajectory scaling on it, so an absent `type` prices a dynasty league as a
   redraft silently. It is the one of the gate's four keys with no safe default.

2. **2.2's `num_teams` — vendor name or engine name?** Not a judgement call: nothing on the
   valuation path reads `num_teams`. Every production reader takes `total_rosters` from the top
   level. `num_teams` absent in 53 of 53 battery leagues; `total_rosters` present in 53 of 53.

3. **2.2's omitted scoring keys — unknown or zero?** Zero. Sleeper returns a complete scoring dict
   and omits what the league does not score, and `league_format_hint` already draws exactly that
   conclusion (`.get("rec", 0)` → standard). Treating omission as an unknown was the second false
   refusal, at 47 of 53.

4. **2.6's demand model** — you answered this one (assignment-based, correct, repriced). Recorded
   because the mandate's −7.0 LB figure was the *rejected* by-eligibility reading; the real effect
   is 1.0, and DB moves the other way.

5. **2.3's split identity — one duplicate or two people?** One player, duplicated across two files.
   Measured at `dc2de79`: three `K Williams` rows, two of them RB/LAR from different files with
   disagreeing hints, one WR/NE who is a different man. Collapsing was correct, and a test comment
   claiming the withheld price was "the engine working, not a shortfall" was wrong and is withdrawn.

6. **The `bpa` magnitude invariant** — its test was failing on a coincidence (two four-player
   windows both spanning 33.0), not on a defect. Replaced with the property itself: within a
   position, bpa gaps equal projected-points gaps exactly, over 8161 pairs, worst deviation 0.0.
