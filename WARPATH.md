# Warpath — rulings of 2026-09-02, and the order they get built in

Written so this survives a context loss. Every item below carries the ruling **as given**, not
as I would have phrased it. Where a ruling was conditional or deferred, the condition is part of
the record.

---

## THE THING THAT GOVERNS TWO OF THESE

`ROADMAP.md`'s own "Open, unresolved questions" already names it, and the operator recalled it
unprompted:

> *"How does a centrally-hosted shared substrate coexist with the current 'Local data
> sovereignty' design principle? (…**this is the single biggest unresolved tension**.)"*

and immediately after:

> *"Who or what actually performs 'verification' for a candidate fact — a human, a stronger
> model, a corroboration-count threshold, an authoritative-source allowlist, some combination?"*

That second bullet **is §6.2a**, and §7.4's allowlist is one of the four mechanisms it lists. So
two of tonight's rulings are partial answers to a question the roadmap deliberately refuses to
answer, given under a stated lean toward **one independent cloud version we control**.

**This is recorded rather than acted on wholesale, deliberately.** The vendor-default calcification
this same session just unwound (see ENGINEERING_DOCTRINE's "retracted justification" rule) happened
exactly this way: a large architectural question answered by accretion of small local choices, none
of which announced itself as settling anything. The deployment model must be decided *as itself*.

**Standing rule for the items below: build the mechanism, do not let it imply the deployment.**

---

## RULINGS

| # | Item | Ruling | Status |
|---|---|---|---|
| 1 | §19.8 loosened-test detection | **Build the fingerprint** (failing, not warn-only) | build |
| 2 | §7.4 cited-source allowlist | **Allowlist what feeds the composite**; prose stays free | build |
| 3 | #94 Moderator contract failure | **Flag only** | build |
| 4 | §6.2a finding re-adjudication | **Gate behind a second pass, human eye if not** — because under a shared deployment an accepted finding affects *everybody*. Explicitly "for now, until that's more in place" | build, conditional |
| 5 | §6.3 fresh-finding-vs-stale-vendor crossover | **HOLD.** Leaning yes *if the full panel agrees*, but it touches the same manifesto contradiction — do not implement | **do not touch** |
| 6 | §7.10 provenance for the 11 CSVs | State origins where **not pay-locked**; **do not name the paid vendor**. Expectation is that inputs get reworked to public sources, making this moot | build, constrained |
| 7 | §19.9 audit cadence | **Weekly, Wednesdays** — after the week of regular-season play concludes | build |
| 8 | §19.10 devcontainer CORS/XSRF | **PIN.** Revisit when Streamlit is outgrown | **do not touch** |
| 9 | §19.11.2 baseline staleness | Not asked; **pre-empted by #6** — the input-source rework subsumes it | folded |

---

## ORDER OF WORK

0. **Land the provider-neutrality increment** (keys-derived chair assignment). In flight.
1. **The socket** — provider contract/registry. "True neutrality, infrastructure that plays
   nicely with whatever they shove into it." The explicit ask.
2. §19.10 — pin only, no code.
3. §7.10 — neutral origin records, vendor unnamed.
4. §19.9 — weekly Wednesday scheduled run.
5. #94 — flag only.
6. §7.4 — composite-feeding allowlist.
7. §19.8 — assertion fingerprint.
8. §6.2a — second-pass gate on findings.
9. §6.3 — **skipped by ruling.**
