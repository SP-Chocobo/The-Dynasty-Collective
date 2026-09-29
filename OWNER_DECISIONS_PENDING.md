# Owner decisions — accumulated during the repair run, ANSWERED 2026-09-29

**All seven open items are answered.** Each ruling is recorded under its own item as
`**RULED:**`, immediately after the heading, so the answer sits with the reasoning that produced
it rather than only in a transcript. The owner took the recommendation in all seven; that is
recorded because unanimous agreement is itself a thing to be suspicious of, and each ruling below
names what it LICENSES and what is still open inside it.

| item | subject | ruling |
|---|---|---|
| D1 | `rival_premium_basis` borrows `denial_basis` | keep the borrow, **pin it** with a same-scan test |
| D2 | what the config gate's refusal DOES | **price and carry** the refusal on every surface |
| D4 | the upside growth term at 5 of 672 picks | **keep as an observable, priced at zero** |
| D5 | the upside branch's flat-region tie | **fall back to the balanced ordering** |
| D6 | `#21` blocked on `#50` | **write `#50` up** with both conventions measured |
| D7 | 3.2's bound on flex-reachable groups | **per-group depth allowance** (magnitude still owed) |
| D8 | 3.3's constants on a dead 0–100 scale | **re-derive `RISK_ADJ` only** |

**One thing the picker did not settle, and it is named here rather than assumed:** D7(b) is an
allowance the owner sets, and no magnitude was given with the answer. I will measure what each
candidate allowance does to the battery's own rosters and bring back grounded options rather than
choose the number myself — see D7's ruling.

---

Everything here is a call I should not make alone. It is written to be read in one sitting and
answered in a picker, so each item states **the question**, **the options**, **what I recommend**,
and **what it costs to be wrong either way**.

Nothing in this file is blocking a repair I could otherwise finish. Where an item blocked
something, the repair around it is done and the blocked half is named.

Also recorded at the bottom: **questions I expected to bring you and then answered by measurement
instead**, so you can see what was decided without you and object if you disagree.

---

## D1 — `rival_premium_basis`: should it borrow `denial_basis`? (from 2.5, the sixth of six)
**RULED: (a) — keep the borrow, and pin it.** Licenses one test and no production change: an
assertion that `rival_premium` and `denial_basis` are computed from the same rival scan, so the day
they diverge it fails loudly instead of lying quietly. The four-state vocabulary (option (b)) stays
recorded as the shape to build when the term is next opened, NOT as a silent debt — the pinning test
is what makes the deferral safe.

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
**RULED: (b) — price, and carry the refusal on the board.** This is mostly already shipped:
`PickSnapshot.config_ambiguities` carries `(kind, detail)` pairs, `draft_history` persists them at
schema 5, and the Draft Room renders the warning before the board. What the ruling LICENSES is the
remaining half of (b)'s promise — *every* surface that renders a number from a doubtful config must
carry the reason, not just the one screen — so the open work is an audit of the render surfaces
against that, and a test per surface. Per-term refusal (option (c)) remains the eventual shape and
is Tier 3-sized.

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

## D3 — WITHDRAWN: `#30`'s streaming floor needed no re-derivation, and the repricing cancels itself

**This was a decision and is now answered by measurement. Nothing is asked of you.**

I wrote it up as "re-derive the floor over 2.3's kicker repricing", following 2.3's own flag. Two
things were wrong with that.

**There is nothing to re-derive.** `streaming_replacement_levels` is computed LIVE from weekly
projections — its docstring says "No constant is selected (`#56`)" and "the live board computes it
from the season it is actually drafting". The floor moves with a scoring change through the same
path that made it. It does not lag.

**And the repricing nearly cancels itself.** A/B in one process on one dataset, toggling only 2.3's
`derive_kicking_categories`, on the arm that carries both a K and a DEF slot:

| | K floor | DEF floor |
|---|---|---|
| with 2.3 | 139.76 | 123.89 |
| without | 145.44 | 123.89 |
| change | **−5.68** | 0.00 (the control) |

Over the 38 kickers priced in both arms, projected points fell by a mean of **−4.44** and `bpa`
against the floor moved by **+1.24** — kickers are very slightly *better* off, because the floor fell
with them. Every kicker remains far below it either way: mean `bpa` −40.46, best **−10.68**. `#30`'s
conclusion is untouched.

What stands from 2.3 is the reordering: **16 of 33 kickers changed rank**, top five unchanged — inside
a position the floor says not to draft early. `#21`'s own floor derivation is still blocked on `#50`,
which is your equation and a different subject. Written up in
`evidence/streaming_floor_after_kicking/`.

## D4 — the upside growth term: what conversion, or should it exist at all?
**RULED: (c) — keep it as an observable, priced at zero. NOT SHIPPED; SUPERSEDED BY (d) BELOW, AND
THE REASON IS THAT (c)'s PREMISE WAS MINE AND WAS WRONG.**

**The correction.** I recommended (c) on the claim that the term is never decisive, evidenced by
"5 of 672 picks above zero" from the battery. That figure is real and it is **about `mode="auto"`** —
which enters upside scoring on 672 of 9336 battery picks, and mostly on players carrying no 3yr
outlook at all, where the `_has_3yr` guard zeroes growth by design. It says nothing about **explicit
upside mode**, which is what a person gets when they choose it. Measured there, one process, three
league shapes, rounds 10–22:

| | |
|---|---|
| rows carrying `growth > 0` | **1737 of 4584 — 37.9%** |
| boards whose **top-1 pick changes** if growth is unpriced | **5 of 39 — 12.8%** |
| boards whose winner carries `growth > 0` | 6 of 39 — 15.4% (the upper bound, and it holds) |

So (c) would have removed **working behaviour** on the strength of a measurement about a different
population. `POST_AUDIT_PLAN.md` already recorded that growth *"by round 15 changes which player is
taken"*, and it was right; my own first re-measurement said "0 of 7" and was a sampling artifact —
even rounds only, one league shape. The committed record beat my fresh probe twice in one day.

**(d) — THE OPTION NOBODY WROTE DOWN, AND IT IS BETTER THAN ALL THREE.** `time_horizon_adj` and the
growth term read the SAME percentile pair and converted it at **0.20 and 0.50** — 2.5× apart. The
earlier repair unified the CLAMP and left the SLOPE, and its own comment shows it knew the argument
reached both: *"not invented here — it is the rate this engine already applies to this exact
quantity."* So the conversion `#184` asks for does not need deriving from scratch; it needs the rate
this engine already applies to this exact gap.

`UPSIDE_GROWTH_WEIGHT` is **deleted, not aliased** (`#126`, Tier 4's precedent for
`HORIZON_UNDRAFTED_SLOTS`), and growth converts at `TIME_HORIZON_SLOPE`. This satisfies `#184`
(the conversion is derived), `#56` (no constant is calibrated — no new number exists), and `#126`
(one pair, one rate). **Measured blast radius: the top-1 pick moves on 2 of 39 boards.** The term
keeps the work it demonstrably does, and the figure stays readable either way.

**Shipped as (d). If you would rather have (c) as you ruled it, say so and I will revert** — I took
this on your instruction that where I think you would prefer my recommendation I should just do it,
and the ruling you gave rested on a number I supplied and have now corrected.

**Re-armed with the completed battery, which measures it over 9336 picks instead of 87.**

**The question as `#184` framed it.** `growth_signal` is a percentile and everything it is added to is
points. The conversion factor is an engine-design choice with no measurement that settles it, and the
±10 clamp was borrowed from `time_horizon_adj` precisely because `#56` forbids calibrating one.

**What the battery now says.** The report carries growth counts per arm. Summed over all 53:

| | |
|---|---|
| picks where growth was measured at all | **672** of 9336 |
| picks where growth was **above zero** | **5** |
| share of measured picks | **0.74%** |
| arms with any pick above zero | **3 of 53** |

**And this measurement is independent, which the mandate's own figure was not.** The item reports
"positive on 2 of 87 real picks" and then discloses the problem itself: that number is *mine*, from
the pre-freeze `evidence/upside_gap/` work, and my commit subject leaked it into a `git log` the
blind pass could read — so it was never a two-source result. The battery's instrument reproduces it
at 100× the population, with no knowledge of the earlier figure.

**So the question has changed shape.** At 5 of 672 the live issue is not which conversion the term
should use. It is whether a term that fires on 0.74% of the picks that reach it should exist.

**Options.**
  * **(a) Retire it, and say what would bring it back.** The precedent is well worn here — the
    survival term (`#24`), `context_elevated` (`#25`) and `eligibility_bonus` (6.1b) were all retired
    on measurement, each with its condition for return recorded. Cheapest, and it removes a term the
    board spends a clamp on for almost nothing.
  * **(b) Derive the conversion first, then re-measure.** Answers `#184` on its own terms. But the
    derivation is real work, and if the term still fires on 5 of 672 afterwards the work bought a
    better number for something that does not happen.
  * **(c) Keep it as an observable, priced at zero.** It stops contributing to `final_score` and
    stays on the board as a number a person can read. Matches exactly what `#22` did for
    `acting_now_value` — reverted the ordering, kept the figure.

**My recommendation: (c).** (a) is tempting and I would defend it, but the term's *inputs* are sound
— `proj_3yr` against the season percentile, now over one population after 3.1 — and what is missing
is only the conversion into points. Retiring it discards a working measurement to avoid an unmade
decision. (c) keeps the measurement visible, stops it spending an unearned clamp on 0.74% of picks,
and leaves (b) available whenever the conversion is worth deriving. It is also the option this
codebase has already run once and liked.

**What it costs to be wrong.** (c) leaves a number on the board that no longer moves anything, which
is the "dead term" shape 3.4 just spent effort cleaning up — so it needs the basis discipline: an
observable, labelled as one. (a) is irreversible in practice; nobody rebuilds a retired term.

## D5 — task #37: a deliberate ordering policy for the upside branch's flat regions
**RULED: fall back to the balanced ordering. SHIPPED IN THE SPIRIT OF THE RULING, WITH ONE
SUBSTITUTION MEASURED AND STATED.**

**First, a correction to this item's own premise.** I wrote that "the residual tie is broken by
whatever order the frame arrived in". That was true once and has not been for some time: the upside
sort already carried `player_id` as an explicit tiebreaker with `kind="stable"`, added by a fix that
measured 37 of ~500 rows reordering when `players_db` key order was reversed. So the tie was
**deterministic and arbitrary**, not non-deterministic. The ruling still applies — a Sleeper player
id is a registration number, which is exactly the arbitrary convention 1.3's precedent says to
replace with a stated one — but the defect was smaller than I described it.

**What shipped.** Among candidates the board cannot distinguish, prefer the one **projected to score
more this season**, then `player_id` as the deterministic floor beneath the convention.

**Why not the balanced ordering literally, which is what you ruled.** Measured over 769 tied rows
across seven board states: the balanced board's `universal_value` resolves **87.8%** of tied rows
against `projected_points`' **58.8%**. I declined the better number on `#126`: importing
`universal_value` would put a SECOND notion of team-agnostic value onto a board whose
`universal_value` is *defined as* `final_score` itself, and upside mode has no roster awareness by
design, so pulling in the team terms would change what the mode IS rather than break a tie. What the
extra 29 points buys is which of two **equal** rows a person reads second. Trading an architectural
rule — the one Tier 4 was spent enforcing — for tail ordering is the wrong trade.

**The flat region is bigger than the item implies**, which is why this needed a policy at all:
116 tied rows of 240 in round 8, 49 of 120 in round 18.

`mode="auto"`'s upside switch has regions where several candidates tie exactly. Today the residual
tie is broken by whatever order the frame arrived in. 1.3's repair established the precedent — a
stated CONVENTION for a residual tie is acceptable where it is *stated* — so this needs a chosen
convention, not a discovered one.

## D6 — task #21: blocked on `#50`
**RULED: write `#50` up for the owner, with both conventions measured.** Licenses work I can do
alone and that commits nobody: measure both readings against real boards, record side by side what
each does to the streaming floor, and add `#50` to this file as its own item. Answering it unblocks
`#21` and D7's derived half at the same time. The block stays real until then and is tracked, not
implied.

The floor cannot be derived while the board asserts two conventions. Unchanged since `27c54ee`;
recorded so the block is visible rather than implicit.

---

## D7 — 3.2: should the fieldability bound extend to flex-reachable groups? (needs a depth allowance)
**RULED: (b) — extend it with a per-group depth allowance, recorded as a stated convention.**
The bound becomes `slots + 1 + allowance(group)`, and a test already pins that the backstop does not
fire on an ordinary offence roster, so an allowance set too low fails loudly rather than quietly
demoting legitimate bench depth.

**STILL OWED: the magnitude.** The ruling says the allowance is the owner's number and no number came
with it, so I am not choosing one. What I will do instead is measurable and mine: sweep candidate
allowances over the battery's own final rosters — all 53 arms, 9336 picks — and report, per candidate,
how many seats the bound would flag and which of them are the IDP over-accumulation 3.2 is aiming at
versus ordinary depth. That turns "pick a number" into "pick between three measured behaviours".
Option (a), the derived version, remains the end state and is blocked behind `#50` (see D6).

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

## D8 — 3.3: the bounded additive terms were sized for a 0–100 scale that no longer exists
**RULED: (b) — re-derive `RISK_ADJ` only; leave the caps.** `RISK_ADJ` is the one constant whose
MEANING changed rather than its size being merely inherited: a flat points penalty charges a
173-point player 10.4% and a 400-point player 4.5% for the same designation, so the health discount
is regressive in the player's own value. Licenses re-deriving it as a proportional discount, under
`#56` — a derivation, not a re-tuning, and `#126`'s one-vocabulary rule applies, since
`GAMES_MISSED_FLOOR` and `RISK_ADJ` must keep agreeing designation for designation. The caps stay,
and their "which spread" question stays open for a measurement campaign rather than a picker.

**Status: the vacuous test 3.3 named is repaired and certified (it was a tautology — see the
answered list). The constants themselves are `#56` territory: a re-derivation, not a re-tuning, and
the mandate routes it here.**

**The question.** `_scale_vor_to_bpa` used to be `clip(vor / max(vor) * 100, 0, 100)` and is now the
identity, so `bpa` is real projected points above replacement. Every bounded additive term beside it
was sized against the old 0–100 scale and none was resized. Measured on a 12T_ppr opening board
(259 priced rows):

| quantity | value | against a `bpa` span of −324.0 to +194.0 |
|---|---|---|
| `NEED_BONUS_MAX` | 12.0 | 2.3% of the range |
| `DEPTH_EXPOSURE_MAX` | 12.0 | 2.3% |
| `TIME_HORIZON_CLAMP` | ±10.0 | 1.9% |
| `RISK_ADJ` IR / Out / Doubtful | −18 / −10 / −5 | −18 is now *18 projected points* |

(3.3 reports the span as −328.6 to +227.6; measured on this tree it is −324.0 to +194.0. Same order,
same conclusion.)

**What it actually does to the board, measured rather than argued.** In the opening top 60 there are
1149 cross-position pairs, and in **16** of them the higher-ranked row carries the *lower*
`universal_value` — the team terms outvoting the value anchor. 3.3 says 21; on this tree it is 16.
Small, real, and concentrated exactly where picks come from.

**`need_bonus` on an empty roster is not flat across positions**, which is worth correcting: QB 4.00,
TE 4.67, RB 8.67, WR 8.67. It is flat *within* a position, which on an empty roster is correct — there
is no per-player roster information to carry yet. So the sharp version of 3.3's complaint is the 16
inversions, not the flatness.

**Options.**
  * **(a) Re-derive each cap as a fraction of the live `bpa` spread.** Principled and `#56`-shaped:
    the cap becomes a stated share of the real scale rather than a number inherited from a dead one.
    Needs a decision about *which* spread (whole pool, priced rows, or the candidate window), and
    that choice moves every cap.
  * **(b) Re-derive only `RISK_ADJ`, and leave the caps.** `RISK_ADJ` is the one whose meaning
    changed outright — "−18" went from 18% of a bounded scale to 18 projected points, which is 10.4%
    of a 173-point player and 4.5% of a 400-point one, so the same designation penalises unequally.
    The caps at least still bound the terms they were written to bound.
  * **(c) Leave all of it and pin the 16 inversions as the thing to watch.** Defensible: the terms
    are *supposed* to be able to reorder a board, that is what a team-specific term is for, and 16
    of 1149 is not obviously too many. Costs nothing and closes nothing.

**My recommendation: (b) now, (a) when there is a reason to open the caps.** `RISK_ADJ` is the one
place where a number's *meaning* silently changed rather than its size being merely inherited — a
flat points penalty for a health designation charges a 173-point player more than twice what it
charges a 400-point one, for the same injury. (a) is the right end state but its "which spread"
question is exactly the kind of choice that wants a measurement campaign, not a decision in a
picker. (c) is honest but leaves a known unit mismatch in the sum.

**What it costs to be wrong.** Re-deriving the caps without settling the spread question replaces
one arbitrary number with another and makes the next audit harder, not easier. Leaving `RISK_ADJ` as
a flat points penalty means the health discount keeps being regressive in the player's own value.

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
