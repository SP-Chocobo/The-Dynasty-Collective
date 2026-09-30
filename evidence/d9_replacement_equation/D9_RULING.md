# D9 / `#50` — the replacement equation. RULED (1), and (1) was already shipped.

**Status: CLOSED. No engine behaviour changed. `#21` and D7(a) are unblocked by this.**

The owner ruled convention **(1)** — price a demand-exhausted position against its PRE-DRAFT
ANCHOR — after challenging the framing twice and being right both times. This file records what was
measured, what was already true, and the reasoning errors made on the way, because the errors are
the reusable part.

---

## THE RULING IS THE BEHAVIOUR THE ENGINE ALREADY HAS

`_fill_omitted_from_anchor` (`draft_room.py:3379`) fills positions `replacement_levels` omitted for
exhausted demand from the pre-draft anchor, and stamps `replacement_basis = predraft_anchor` so the
row says which kind of claim its price rests on. That is convention (1), verbatim, already running.

Measured on the real capture, 12-team dynasty, balanced mode, `L` = live demand / `P` = anchored:

| round | QB | RB | WR | TE | K | DEF |
|---|---|---|---|---|---|---|
| 12 | 27L / 0P | 37L / 0P | 65L / 0P | 29L / 0P | 15L / 0P | 7L / 0P |
| 14 | 25L / 0P | 36L / 0P | 61L / 0P | 24L / 0P | **0L / 9P** | **0L / 1P** |
| 16 | 22L / 0P | 33L / 0P | 51L / 0P | 19L / 0P | 0L / 7P | 0L / 0P |
| 18 | 20L / 0P | **0L / 28P** | **0L / 43P** | 12L / 0P | 0L / 5P | 0L / 0P |
| 20 | **17L / 0P** | 0L / 22P | 0L / 35P | **0L / 8P** | 0L / 2P | 0L / 0P |

By round 18 the anchor governs 76 of 108 priced rows. The item was written as though it were a
proposal; it is a description.

**WHY THE ANCHOR NEVER REACHES QB, which is not an omission.** `_fill_omitted_from_anchor` declines
any position the `startable_floors` branch handled (`(startable_floors or {}).get(p) is None`), and
`compute_draft_board` passes `startable_floors={"QB": qb_startable_floor(...)}` on every call —
stated at `draft_room.py:312`. QB is excluded because it has a MORE SPECIFIC mechanism: an absolute
startability threshold anchored on the full committed baseline rather than the draining pool.

So `#50`'s motivating evidence — *"at chair 2's last pick the backstop bound correctly and found
zero QBs on the board"* — is not addressed by (1) and never could have been. (1) is a kicker,
defence and flex-depth behaviour. **The item's own example is at the one position its own preferred
convention does not touch.** That is worth knowing before anyone reopens it.

---

## THE DOUBLE-COUNT FINDING — the durable part of this investigation

The owner asked, while ruling: *make sure we're not doubling valuation on `depth_exposure`.* The
guard exists, it is load-bearing, and the reason it exists answers the whole D9 question.

`depth_exposure` has two states that look like one quantity and are not:

| basis | what the loss IS | already in `universal_value`? | priced? |
|---|---|---|---|
| `EXPOSURE_MEASURED` (a surplus exists) | the MARGINAL loss, `TE1 - TE2` — the solver promotes the backup | no | **yes** |
| `EXPOSURE_NO_SURPLUS` (thin here) | the starter's **ENTIRE** production — nothing covers the slot | **yes** | **no, deliberately** |

`lineup_optimizer.py:344-352` states it: *"with a starter uncovered, removing him returns HIS WHOLE
VALUE, not what a backup would have to cover. That is a real quantity on a DIFFERENT SCALE, and
`draft_room` prices `worst_loss` only under EXPOSURE_MEASURED for exactly that reason."*

**Pricing the NO_SURPLUS exposure WOULD BE the double count**, and it would be a large one: those
cells carry the biggest measurements in the vocabulary — median `worst_loss` 62.00 against
MEASURED's 42.00, max 82.00, over 8 in-draft board states. The engine measures its largest exposure
exactly where it refuses to charge for it, and that refusal is correct.

**MEASURED, balanced mode, to confirm the gate behaves as described** (`mode="balanced"` forced;
`mode="auto"` selects upside from round 15 and upside drops this term entirely):

* `depth_exposure > 0` on **334 of 909 rows at round 12** and **171 of 837 at round 18** — the term
  fires, so a zero elsewhere is a measured zero and not a dead instrument.
* `depth_exposure == 0.0` on **all 703 demand-exhausted rows** across rounds 12-20 (QB, TE, WR, DEF).
* The unconfounded case: holding **exactly 1 TE against 1 TE slot** — maximally thin, TE drained —
  every one of 200 TE rows reads 0.0, basis `no_surplus`. Not a defect. The exposure there is the
  starter's whole value, which the candidate's own `universal_value` already carries.

### THE GENERAL RULE, for the next time this shape appears

**A quantity measured on a different scale is not the same quantity, and a term that declines to add
it is not a term with a hole.** Three separate things in this engine look like "the value of depth"
and only one of them is an increment:

1. the body's own production — `universal_value`;
2. the marginal upgrade over the man he replaces — `depth_exposure` under MEASURED;
3. the whole hole he would fill if nothing covers it — measured, never charged, because it IS (1).

Any future proposal to "price depth better" must say which of those three it means, and show it is
not already being paid for under another name. The owner's D9 criterion — depth as insurance against
lost starter production — is (3), and (3) cannot be added as a positive term without paying twice.
**The criterion is right and the engine already satisfies it, through (1) rather than through a
contingency credit.**

---

## WHY (2) WAS REJECTED, having been recommended twice — by me

Convention (2) makes a demand-exhausted row's price ABSENT on the ground that the engine has no
basis for saying what another body is worth. **That ground is false, and the table above says how
false:** 76 of 108 priced rows at round 18 would have gone absent while each carried a real,
anchored price for the player's own production. Absence is for a quantity with no basis (`#187`);
using it on a quantity that HAS one, because a DIFFERENT quantity (starter demand) is exhausted, is
the absence contract inverted — the mirror of `#193`.

The honest version of (2)'s insight survives, and it is small: what has no remaining basis is the
**starter-demand increment**, not the row. The row's `replacement_basis` already says so.

---

## THE THREE ERRORS, recorded because the shape repeats

Every one of them was a confident answer given before the relevant number was in hand.

1. **"The owner's criterion needs an injury base rate we do not have."** False. `depth_exposure`
   carries no probability by design and needs none — it measures severity, what the lineup loses,
   not likelihood. I had read the term's name and not its docstring, which says this explicitly.
2. **"The valuation transitions: `universal_value` goes absent and `depth_exposure` keeps pricing
   the row."** Asserted from the docstring's description of what the term prices. Measured: 0 of 703
   drained rows carry a positive `depth_exposure`. A docstring describing a term correctly does not
   tell you where that term fires.
3. **The measurement that refuted (2) was itself an artifact.** The probe used `mode="auto"`, and
   `UPSIDE_MODE_DEFAULT_ROUND = 15`, so every board from round 14 on ran the upside branch — which
   drops `universal_value`, `need_bonus` and `depth_exposure` entirely. I read `None` off a term the
   branch never computes and reported it as evidence about demand exhaustion.

**What caught the third one was the CONTROL ARM** — a position whose demand was still live, which
came back equally `None`. Without it, "depth_exposure is None on drained rows" would have shipped as
a finding. The engine-measurement skill already carries this rule (*if ON and OFF are identical, the
thing under test did not fire; find out why before concluding it had no effect*), and the probe that
broke it had no control at all.

**The common shape, stated for reuse:** reasoning about a term from its own prose instead of from
its output. The prose in this repository is unusually good, which makes it unusually tempting to
treat as a measurement. It is not one. `#245` applied to documentation: a plausible description is
a broken instrument until its output agrees with it.

---

## CONSEQUENCES

* `#21` and **D7(a)** were blocked behind this item. They are now unblocked: the replacement
  equation is settled and its basis is stated per row. Both remain OUT OF SCOPE for v4 by §8's
  predeclaration — each is a derivation campaign, not an edit — but they are no longer blocked.
* `POST_AUDIT_PLAN`'s framing of `#50` as an open choice between two conventions is superseded:
  one of them was the behaviour, and the other was unsound.
* No code change. The verification is the deliverable.
