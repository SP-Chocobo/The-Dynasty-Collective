# Roadmap to a version we stop reworking

Written 2026-09-29, at the owner's instruction: *"until we need to rework data leveraging due to
new input, i just want it to work and be done... I don't want to have never-ending reworks of the
engine and its support testing layers."*

This file exists to make "done" a **specific, checkable state** rather than a feeling, and to name
in advance the things that will NOT reopen it. Its whole purpose is to be closable.

> **SUPERSEDED AS A ROADMAP — KEPT AS THE DATED RECORD OF ITS OWN CYCLE (read 2026-10-01).**
> Its finish line has been reached and passed. `v3-freeze` was cut at `eac7491` and published
> (tag `1f3affa`); the cycle in flight is **v4**, whose gate is `V4_GATE_CRITERIA.md` and whose
> numbered record is `POST_AUDIT_PLAN.md` (`#292`: the record wins over any status flag). Every
> status below — including "the upcoming tag is `v3-freeze`" and the HEAD distance in the table —
> is **as of 2026-09-29** and is not maintained. This file was itself corrected once for trusting a
> stale status flag, so it is scoped here rather than quietly refreshed: the numbers are a record of
> what was true that day, not a claim about today.

---

## The finish line already exists, and it is one tag: `v3-freeze`

**Corrected 2026-09-29 at the owner's challenge, and the correction matters.** This file first said
the finish line was "cut `v2-freeze` for real", on the strength of task `#35`'s summary line —
*"freeze NOT cut; premature tag deleted; v2 is a CANDIDATE pending the battery."* That was a
stale status flag describing a moment that had already been superseded.

What actually happened, from the record rather than the flag:

| | |
|---|---|
| `v1-freeze` | `6599b1e` |
| premature v2 tag at `43c8188` | cut, then **deleted** — the varied-field battery had not run |
| **`v2-freeze` at `a8d1627`** | **cut for real and published to the remote**, full suite 3512 OK |
| `#52` — the Fable blind adversarial pass | unbriefed, after the freeze; nine pass reports recorded verbatim |
| `REPAIR_MANDATE_V2.md`, 26 items | the four tiers, all certified |
| the 53-arm battery | complete, 9336 picks, no repair follows |
| **HEAD** | **91 commits past `a8d1627`** |

So the upcoming tag is **`v3-freeze`**, and it needs its own `FREEZE_RECORD_V3.md` the way v2 got
one. `FREEZE_RECORD_V2.md` records the premature-tag episode itself, which is why the correction was
one `git tag -l` away — I did not look.

**The mistake is worth keeping, because the repo has a rule against exactly it.** `#292`:
*"POST_AUDIT_PLAN.md remains the numbered record and wins over any status flag anywhere."* I read a
task summary instead of the record. The task list is a convenience; the freeze records and
`POST_AUDIT_PLAN.md` are the record.

**And the v2 precedent sets this freeze's own gate**, in the owner's words quoted in
`FREEZE_RECORD_V2.md`: *"freeze is the last item before audit. if we find more tinkering to do, that
happens before freeze."* Under that ordering a battery finding sends work back *before* the freeze
rather than after it — which is precisely the cycle just completed: the blind pass found things, the
mandate repaired them, the battery re-ran clean. That is what earns v3.

## What each version boundary PROVES (owner-set, 2026-09-29)

The owner's instruction: *"make the version numbers correspond to evidence, not calendar time."*
So each tag carries a claim, and the claim names its evidence.

| tag | the claim | the evidence |
|---|---|---|
| `v2-freeze` `a8d1627` | known-good baseline | full suite 3512 OK, varied-field battery |
| `v3-freeze` | **every known finding repaired, all seven owner decisions resolved** | the four mandate tiers certified, the 53-arm battery clean, the seven rulings shipped |
| `v4-freeze` | **survived independent attack at the post-Fable architecture** | the three-instrument gate below |

**v3 is explicitly NOT production, and its record must say so.** That is the point of it: v3 is a
claim about the COMPLETENESS OF KNOWN WORK, not about correctness. v4 is the claim about correctness
under an adversary. `FREEZE_RECORD_V2.md` set the habit that makes this legible — state what the
freeze does not claim — and `FREEZE_RECORD_V3.md` must carry that sentence in its opening.

### "The Fable battery" is TWO instruments, and they answer the gate question oppositely

This distinction decides whether a v3 -> v4 gate is real or ceremonial, and the phrase hides it.

* **The blind adversarial pass (`#52`)** — an unbriefed model reading the frozen tree, nine lenses,
  two waves. A **discovery** instrument. Its yield comes from reading code no adversary has read,
  which makes it effectively **one-shot per tree**.
* **The draft battery (`run_draft_battery.py`)** — 53 arms, 9336 picks, structural findings on real
  drafted rosters. A **regression** instrument: deterministic given code and data, fixed assertions
  over fixed fixtures.

So: **the existing battery is sufficient as a regression gate and cannot serve as a discovery gate.**
Re-running it against v3 proves nothing known broke — necessary, and not a gate. Replaying v2's
lenses would be ceremonial for the same reason. A FRESH pass over the 91-commit diff is not, because
that code has never been read adversarially by anything but its author.

### The independence hole is the author

Every one of those 91 commits is mine. If I also design the lenses that read them, the pass inherits
my blind spots and can only look where I thought to point it. Two mitigations, honestly ranked:

* **Weak** — keep the pass unbriefed: give it TERRITORY (the diff range) and no CONCLUSIONS, nothing
  about what the repairs claimed or where I think the risk is. Bounding territory is a mild briefing
  and that is a real cost, recorded rather than hidden.
* **Strong** — **write v4's pass/fail criteria BEFORE the pass runs.** This is the one that matters,
  because it removes the judgement my own review is least able to police: moving the bar after seeing
  the results.

### The v3 -> v4 gate: three instruments, three distinct jobs

| instrument | what it proves | ceremonial risk |
|---|---|---|
| fresh blind pass over the diff | discovery — what nobody anticipated | low, if the lenses are new and it stays unbriefed |
| battery re-run | regression — nothing known broke | **high; label it confirmatory, never discovery** |
| **mutation gate** over the new surface | the detection power of the test layer itself | none — it is a measurement |

**The mutation gate is the one with demonstrated yield in this repo, and it is the only one whose
value does not depend on who designed it.** `dbc4d4a`, from the v2 blind pass: all three invariant
mutations SURVIVED the engine suite, and the two committed "caught" verdicts were wrong — artifacts
of `--failfast` tripping on an unrelated anchors module. A self-certification instrument was
reporting false positives about its own detection power. "4018 tests" is a number; "catches 9 of 12
injected defects" is evidence.

D1's own pinning test was mutation-checked this way before it was believed (three mutants: a
constant `measured` companion, `#207`'s zero-initialised premium, and a basis decided off the value
— 4, 97 and 2 failures respectively). That is the standard the gate generalises.

### What stops v4 becoming v5

This structure sits against the owner's other instruction — *"I don't want never-ending reworks"* —
and adding a gate is structurally another cycle. The only thing that bounds it is that the gate's
criteria are written in advance **including what is out of scope**: a finding outside the stated
scope is RECORDED, not repaired. That is the stopping rule further down this file, applied to the
gate itself. Without it, "v4 after a final battery" becomes v5 after the next one by exactly the
mechanism that produced v3.

---

## What is actually left: the seven rulings, and nothing else

The four mandate tiers are complete and certified. The battery is clean. The only outstanding
*code* is the work the owner's seven answers just licensed — there is no other open defect.

### Phase A1 — the three small ones
| item | work | risk |
|---|---|---|
| **D1** | one test pinning `rival_premium` and `denial_basis` to the same rival scan | none; no production change |
| **D5** | the upside branch's flat regions fall back to the balanced ordering | low; a residual tie-break, no priced term moves |
| **D4** | `growth_signal` leaves `final_score`, stays on the board as an observable with a basis | low; it fires on 0.74% of the picks that reach it |

### Phase A2 — the two that touch prices
| item | work | risk |
|---|---|---|
| **D8** | re-derive `RISK_ADJ` as a proportional discount instead of a flat points penalty | real: it moves every injured player's price, and must keep agreeing with `GAMES_MISSED_FLOOR` designation for designation (`#126`) |
| **D2** | audit every surface that renders a number from a doubtful config; each must carry the reason | low; mostly shipped, this is the remaining half of (b)'s promise |

### Phase A3 — the two with an owner dependency
| item | work | dependency |
|---|---|---|
| **D6** | measure both of `#50`'s conventions against real boards, write `#50` up as its own item | none to do the work; answering it later unblocks `#21` and D7(a) |
| **D7** | sweep candidate depth allowances over the battery's own final rosters, bring back three measured behaviours, then implement the chosen one | **one number from the owner**, which is the only thing in this file that can stall |

### Phase B — the v3 candidate tag
One full suite, all Tier 0 instruments green, `assertion_floors --write`, `FREEZE_RECORD_V3.md`
written to be read cold and stating in its opening that **v3 is not production**, then cut and
publish **`v3-freeze`**.

### Phase C — the v4 gate
Write the pass/fail criteria FIRST, including what is out of scope. Then the three instruments
above. Then `v4-freeze`, which is the production claim. The record must state what the
freeze rests on, what it does NOT claim, and what was left open — the three headings v2's record
used, because they are what made this correction possible at all.

---

## Rough cost

| | |
|---|---|
| A1 | ~2h, then one full suite |
| A2 | ~2h, then one full suite |
| A3 | ~2h, gated on D7's number, then one full suite |
| B | ~30min on top of A3's suite, plus the v3 freeze record |
| **total** | **~7h of working time, of which ~1.5h is suite waiting** |

That is one session of the kind we have been running, not another thirteen-hour grind. The suite is
1300-1625s per run and a full suite is what licenses each push, so three pushes is three suites and
there is no way to compress that without lowering the bar that has been catching my own errors.

---

## What does NOT reopen this, stated in advance

These are real and are deliberately being left recorded rather than done. Each one already has its
reasoning written down in `OWNER_DECISIONS_PENDING.md`; none is a silent debt, and none is a defect.

* **D1(b)** — `rival_premium`'s own four-state basis vocabulary. The pinning test makes the
  deferral safe: it fails loudly if the borrow ever stops being true.
* **D2(c)** — per-term config refusal. The eventual shape; Tier 3-sized; (b) satisfies the
  mandate's one non-negotiable today.
* **D4(b)** — deriving the percentile-to-points conversion. Available to anyone who thinks 0.74%
  of picks is worth the work. (`#184` / task `#36` resolve here.)
* **D7(a)** — the derived allowance from `#30`'s streaming baseline. Blocked behind `#50`.
* **D8(a)** — re-deriving the bounded caps. Needs a decision about *which* spread, which wants a
  measurement campaign, not a picker.
* **`#21` / `#50`** — the floor cannot be derived while the board asserts two conventions. Tracked,
  visible, blocked.
* **The 16 inversions** — cross-position pairs in the opening top 60 where team terms outvote the
  value anchor. Pinned as a watched figure. Team-specific terms are *supposed* to be able to
  reorder a board.

## The stopping rule

After `v3-freeze` is cut, the engine and its test layers change for exactly two reasons:

1. **New or changed inputs** — a new vendor file, a scoring format the vocabulary does not cover, a
   season roll. This is the case the owner named, and it is the expected one.
2. **A catastrophic defect** — the board prices something it cannot justify, or a number reaches a
   person with a basis that is false. The absence contract (`#187`) and `#193` are what make this
   detectable rather than a matter of taste.

**Everything else goes on the deferred list above and waits.** An audit finding that is not one of
those two is recorded, not repaired. That is the difference between a frozen version and a
permanently open one, and it is the point of cutting the tag.
