# INVESTIGATION BRIEF — the next #216 session

Owner-written, 2026-09-10. Reproduced close to verbatim; the operational notes at the bottom
are mine. **This is a brief, not a task to "fix #216."** Inherit the epistemic state, then earn
the next move.

---

Start from `HANDOFF.md` and treat it as authoritative for the current #216 state. **Do not
resurrect any withdrawn finding**, especially the old B1/B2 coupling or the exonerated
`narrow_candidates` / selection-path theory.

The next question is narrowly defined:

> **What is the intended semantic meaning of the transition from roster-aware balanced
> valuation to roster-blind upside valuation, and can that meaning be derived from existing
> architecture?**

**Do not tune `UPSIDE_MODE_DEFAULT_ROUND`. Do not try candidate observables against the battery
merely to find the prettiest roster shape. Do not implement a transition rule yet.**

## Already established — do not re-derive

- `mode="auto"` switches at round 15.
- The switch is causally active: forcing balanced produces **168/168 identical picks** through
  round 14, then diverges exactly at round 15.
- In this league the switch accounts for **63%** of the observed late-round TE excess, but
  balanced mode still leaves **29.2% TE**, so it is not the whole explanation.
- Five existing observables were identified, but they represent **different concepts** and occur
  at **rounds 7–23**. None currently defines "roster-blind should begin now."
- **Therefore the transition concept itself is currently undefined.**

## Investigate the architecture, not the output histogram

1. Trace **why upside mode exists** and what its source comments/documentation say it is
   intended to accomplish.
2. Identify **every existing production quantity** that could semantically represent the point
   at which roster fit should cease to constrain valuation.
3. For each candidate, state **what question it answers**, its **scope (per-seat vs global)**,
   and whether it actually matches the **stated purpose** of upside mode.
4. Look for **existing tests, doctrine, or contracts** that already imply the intended meaning.
   Do not invent a definition merely because an observable is convenient.
5. If the architecture contains enough information to define the transition unambiguously,
   **write the proposed definition and prove the necessary inputs already exist.**
6. If it does not, **explicitly report a design gap** rather than choosing an observable.
7. Separately, keep the **residual 29.2% TE behaviour and B2 out of this investigation** unless
   the architecture trace demonstrates a direct causal connection.

## Measurement discipline

- Behavioural inputs require **production-equivalent schema**; do not use reduced fixtures when
  omitted fields can change behaviour.
- If a probe produces **all-zero / all-identical / all-never** behaviour, validate the interface
  and derived inputs before interpreting it.
- **Instrument production quantities** rather than reconstructing them downstream.
- **Pre-register any ablation before running it.**
- **No engine behaviour changes** without a demonstrated mechanism and a falsifiable test.

## The deliverable

An evidence-backed answer to **one** question:

> **"Does the existing architecture already define what should trigger the balanced→upside
> transition, or is that concept genuinely missing?"**

**If the answer is "missing," STOP THERE. Do not solve the design question yet.**

---

## Operational notes (mine, not the owner's)

- Branch: `worktree-agent-ab5e1af412aeb9182`. Last green suite 2760 OK at `6487a22`.
- **No engine source has been changed in this entire investigation** — keep it that way for the
  duration of this brief. Steps 1–4 are reads; step 5 is a written definition, not a wiring.
- The five doctrine clauses live in `.claude/skills/engine-measurement/SKILL.md`. Read them
  before writing any probe; four of them exist because a published finding here had to be
  withdrawn.
- Start points for step 1: `draft_room.py`'s module docstring (the UPSIDE MODE paragraph),
  `upside_score`'s own docstring, the `use_upside` branch's inline comments, and
  `UPSIDE_MODE_DEFAULT_ROUND`'s comment at its definition.
- Step 2's five known candidates are already measured in
  `PHASE5_THE_TRANSITION_IS_UNDEFINED.md` — inherit those numbers rather than re-running the
  probe, but the enumeration is explicitly NOT closed: finding a sixth is in scope.
- The trap, stated once so it is not rediscovered the hard way: lineup-completion fires
  **earlier** than round 15 and would produce **more** tight ends; demand-exhaustion fires
  later. The direction of any change follows from the choice, so choosing before defining is
  selection on the outcome.
