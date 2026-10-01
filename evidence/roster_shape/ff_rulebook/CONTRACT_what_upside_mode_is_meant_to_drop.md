# Is upside mode meant to remove roster fit only, or roster fit AND positional scarcity?

Documentary. **No engine source changed, no probe run, no measurement taken for this document.**
Every citation is a production docstring, `CDME_CONTRACTS.md`, `POST_AUDIT_PLAN.md`, a committed
test, or git history. The observed TE composition is not used as evidence anywhere below, and no
numerical adjustment is proposed.

---

# ANSWER: the contract DOES answer it. **Roster fit only. The positional anchor is retained by design.**

The code follows the contract on both halves. Five independent sources agree.

## 1. The founding architecture names the axis, and it is not scarcity-vs-production

`draft_room.py`'s module docstring, and the founding commit `44ef3c6` (2026-08-20) in almost the
same words:

> conflating **"how good is this player"** (comparable across every team watching the draft) with
> **"how good is this player FOR THIS ROSTER"** (inherently team-specific). Kept as two explicit
> numbers:
>
>     universal_value        = BPA + time_horizon_adj + risk_adj
>     team_acquisition_value = universal_value + need_bonus + eligibility_bonus + depth_exposure
>                              + displacement_adj

The commit is explicit that `universal_value` is *"what any manager at the draft would compute —
**league-wide scarcity**, market read, season-vs-long-term trajectory, a health discount"*.

**So league-wide scarcity is, by the founding definition, part of the TEAM-AGNOSTIC half.** Upside
mode's rule — zero the team-specific terms, keep the rest — therefore retains it *by construction*,
and that is the architecture working, not failing.

## 2. Every operational statement treats `bpa`-in-upside as the design

- `CDME_CONTRACTS.md`: *"`upside_score` is `bpa + UPSIDE_GROWTH_WEIGHT * growth`"* — stated as the
  design and then measured, with the comparison column literally headed **"rows reordered vs.
  pure-`bpa` order"**. That table is only meaningful if pure-`bpa` is the intended reference the
  growth term perturbs.
- The same section rules: **"`UPSIDE_GROWTH_WEIGHT` is not on the open-decisions list."** The
  composition was examined and closed.
- `POST_AUDIT_PLAN.md`: `growth_signal` is *"upside mode's **whole distinguishing output**"* —
  which makes `bpa` the deliberately *shared* part, not an oversight.
- `test_decision_qualifiers.py` pins it as an identity: *"upside mode's own identity is
  `final_score = bpa + UPSIDE_GROWTH_WEIGHT * growth_signal`."*

## 3. The repo already has a name for what upside mode drops, and it is not the anchor

`POST_AUDIT_PLAN.md` uses the phrase in quotation marks as an established property:
**"upside mode has no positional gate"**. The positional *gate* is `need_bonus` — that is #87's
ruling (*"need_bonus is a POSITIONAL GATE, load-bearing"*). What upside mode is recorded as
lacking is the gate, never the anchor.

## 4. The constant's comment is the outlier — and I over-weighted it

`UPSIDE_MODE_DEFAULT_ROUND`'s comment says a deep-bench pick is *"not filling a need or respecting
positional scarcity that barely matters by then."*

`FINDING_upside_intent_inversion.md` read that as half the stated intent being inverted.
**That framing is withdrawn.** It weighed one uncommitted comment against the founding
architecture, four contract statements and a pinned test, all of which say the anchor is retained
deliberately. The comment is a loose paraphrase in a place with no contract force — the repo's own
test on that constant calls the boundary *"a calibration decision"* and pins the number, not a
meaning. **The code is not violating an intent; one comment is describing the code wrongly.**

## 5. History confirms nobody ever chose otherwise

`git log -S` over `draft_room.py`:

| symbol | commits that ever touched it |
|---|---|
| `upside_score` body / `UPSIDE_GROWTH_WEIGHT` | **`44ef3c6` only** — the founding engine commit |
| `UPSIDE_MODE_DEFAULT_ROUND` | `44ef3c6`, plus `c18ac16` (#154's feasibility backstop — no formula change) |

**Upside mode's composition has never been revisited since the engine was written.**

---

# AND THE CONTRACT DOES NOT ANSWER THE CONSEQUENCE. This is the missing design decision.

`displacement_adj` is classified **two ways, in the same docstring**, and the two classifications
have opposite implications at the mode boundary.

**Classification A — a team-specific term.** *"`displacement_adj` (#216) is the FOURTH team-specific
term and the only one that can be negative."* This places it squarely under upside mode's rule:
zero every team-specific term. Under A, zeroing it is correct and is exactly the stated intent —
a deep-bench pick is not about filling a need.

**Classification B — a correction to the universal anchor.** From the same file, justifying why it
alone carries no cap:

> this term **only ever removes credit the league anchor gave for a slot the roster cannot offer**
> — the reason `TEAM_SPECIFIC_CAPS` remains an upper bound on the sum of the team terms **with no
> fourth cap**.

Under B it is not team *preference* at all. It is the retraction of an over-credit in
`universal_value` itself. And under B, zeroing it while retaining the anchor does not remove a
roster preference — it **leaves the retained universal number carrying credit the contract says it
should not have**.

**The exemption from the cap is granted on reading B. The exposure to upside mode's rule follows
from reading A. Nothing anywhere in the repo reconciles them, and nothing chooses.**

## Why the collision was invisible until now — the class grew and the rule did not

The founding commit is explicit: `team_acquisition_value` was *"universal_value plus need_bonus,
**the ONLY team-specific term**, capped low enough to nudge a close call but never flip a large
universal-value gap."*

**"Zero every team-specific term" was written when that class had ONE member, and that member was a
capped nudge.** The class then grew to four — `eligibility_bonus`, `depth_exposure` (#139), and
`displacement_adj` (#216, `d3c22af`/`492d358`, roughly three weeks after the founding commit) — and
the fourth member is, by its own docstring, *not* a nudge. Upside mode's rule was never re-examined
against the new member.

So the category "team-specific" now does two jobs: **three bounded roster-preference nudges, and
one unbounded correction to the universal anchor.** One rule, written for the first job, silently
also performs the second.

## Two contract invariants are stale, and this is where it shows

`CDME_CONTRACTS.md`'s invariant block still reads:

> **1.** `team_acquisition_value == universal_value + need_bonus + eligibility_bonus +
> depth_exposure`, in every mode. *(`depth_exposure` joined the sum in #139 …)*
>
> **4.** None of the **three** team-specific terms may flip a large `universal_value` gap; each is
> capped for exactly this reason (`NEED_BONUS_MAX`, `ELIGIBILITY_BONUS_MAX`, `DEPTH_EXPOSURE_MAX`
> — the same number three times, deliberately: they are one class of term).

Both predate the fourth term. Invariant 1 records the #139 expansion of the class and misses
#216's; the production identity in `draft_room.py`'s own docstring carries `+ displacement_adj`
and this one does not.

**Invariant 4 matters more.** Its guarantee is *"team-specific terms nudge, they never flip."* The
fourth term is **designed to flip** — the module docstring says so in as many words: *"no bounded
nudge could span the 43-60 point bias."* The capping *mechanism* still bounds what it was built to
bound (the three positive nudges, and `TEAM_SPECIFIC_CAPS` is still a correct upper bound on their
sum). The invariant's *statement* is now false of the class it names.

That is not a bug to fix by adding a cap — #216's derivation for having none is on the record and
this document does not reopen it. It is a contract that enumerates a class, had the class grow
under it twice, and updated itself once.

---

# The design decision to record

> **Upside mode's rule is "zero every team-specific term." Is `displacement_adj` in scope of that
> rule as a roster preference, or exempt from it as a correction to the anchor upside mode
> retains?**
>
> The contract asserts both classifications and reconciles neither. The rule was authored when the
> class it names contained a single capped nudge, and has not been revisited across two expansions
> of that class.

**Implications of each answer, stated without recommending one:**

- **In scope (status quo).** Upside mode is correct as written and the composition needs no
  change. What then needs stating is that `universal_value` in the upside half carries credit for
  slots a roster cannot offer, deliberately — and that `CONTRACT_deep_bench_cross_position.md`'s
  gap (the domain of validity is keyed on the anchor, never the candidate) is the place that would
  have to speak to whether that is acceptable for a bench seat.
- **Exempt.** Then "team-specific" is one word covering two categories and the vocabulary needs
  splitting — a roster-preference class (capped, dropped in upside) and an anchor-correction class
  (uncapped, travelling with the anchor). That is a #126-shaped question (one home for one
  vocabulary), not a numerical one.

**Explicitly out of scope of this document:** whether either answer produces better rosters. No
composition figure appears above; the question is what the design intends, and it is unresolved for
a reason that is documentary, not empirical.

## Kept separate

The 1-vs-15 seat-allocation phenomenon (#226) is not cited above and is not evidence for or against
any of it. RESIDUAL5 established it is a roster-distribution phenomenon with no aggregate authority.
