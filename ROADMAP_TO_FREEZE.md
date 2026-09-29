# Roadmap to a version we stop reworking

Written 2026-09-29, at the owner's instruction: *"until we need to rework data leveraging due to
new input, i just want it to work and be done... I don't want to have never-ending reworks of the
engine and its support testing layers."*

This file exists to make "done" a **specific, checkable state** rather than a feeling, and to name
in advance the things that will NOT reopen it. Its whole purpose is to be closable.

---

## The finish line already exists, and it is one tag

Task `#35` cut a `v2-freeze` tag, then deleted it, and recorded why: **v2 is a CANDIDATE, pending
the battery.** The battery is now complete — 53 arms, 9336 picks, no repair following from it — so
the one condition that was holding the freeze open is satisfied.

So "done" is not a judgement call. It is: **cut `v2-freeze` for real, on a green suite, with the
seven owner rulings shipped.** Everything below is the shortest honest path to that tag.

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

### Phase B — the freeze
One full suite, all Tier 0 instruments green, `assertion_floors --write`, then cut `v2-freeze`.

---

## Rough cost

| | |
|---|---|
| A1 | ~2h, then one full suite |
| A2 | ~2h, then one full suite |
| A3 | ~2h, gated on D7's number, then one full suite |
| B | ~30min on top of A3's suite |
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

After `v2-freeze` is cut, the engine and its test layers change for exactly two reasons:

1. **New or changed inputs** — a new vendor file, a scoring format the vocabulary does not cover, a
   season roll. This is the case the owner named, and it is the expected one.
2. **A catastrophic defect** — the board prices something it cannot justify, or a number reaches a
   person with a basis that is false. The absence contract (`#187`) and `#193` are what make this
   detectable rather than a matter of taste.

**Everything else goes on the deferred list above and waits.** An audit finding that is not one of
those two is recorded, not repaired. That is the difference between a frozen version and a
permanently open one, and it is the point of cutting the tag.
