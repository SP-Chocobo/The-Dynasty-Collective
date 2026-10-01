# Phase 0 — the two disputes, adjudicated before their code is touched

> Required by `REPAIR_MANDATE.md` §0.2. Both were cross-pass disagreements; in neither case was
> either pass wholly right, and resolving them changes what gets repaired.

## Dispute 1 — `assertion_floors`: defect, or declared limit?

Pass I filed it as defective four ways. Pass J filed it as a **limit**, judging the hole inside the
docstring's declared scope. The docstring states its limits explicitly, so the adjudication is
mechanical: check each of I's four against what is declared.

Declared, verbatim: *a vacuous assertion*; **an assertion moved behind a condition that never
holds**; *a weakened expected value*; *anything in a module not discovered as `test_*.py`*.

| I's claim | verdict |
|---|---|
| (a) weaken `assertEqual → assertIsNotNone` in one test **and** add another `assertEqual` in the same edit → `drops() == []` | **REAL DEFECT.** The docstring promises the opposite in terms: *"any substitution — one assertion name swapped for another — **FAILS, either way**"*. Per-name counts netting to zero across a module defeats a guarantee that is stated without qualification. Not declared anywhere. |
| (b) `@unittest.skip` on a test → `[]` | **DECLARED LIMIT.** A skip is an assertion behind a condition that never holds. **J is right.** |
| (c) assertion moved under `if False:` → `[]` | **DECLARED LIMIT**, in those words. **J is right.** |
| (d) floors file `{}` + an empty test module → `[]`, and `--check` prints *"no guarantee has shrunk (0 modules held to a floor)"* and **exits 0** | **REAL DEFECT — but not where I put it.** `load()` returning `{}` for a damaged file is deliberate and documented, so that `--write` can repair it. What is not defensible is `--check` reporting **success** over zero floors. The bug is in the reporting, not the loader: an integrity check that holds nothing must not exit 0 with a reassuring sentence. |

**Resolution: two of four are real.** Repair (a) — substitution must fail even when per-name counts
net out — and (d) — `--check` must refuse to report success when it is holding no floors. Leave (b)
and (c); they are honestly declared, and repairing a stated limit as though it were a defect is how
a docstring stops being trustworthy.

## Dispute 2 — `W4-15`: cross-format mixing, hazard or null?

Pass G: 18 players' vendor `projection` and 15 winning rows come from `dynasty_superflex_rankings.csv`,
which `_detect_rankings_format` tags **standard**, in a **PPR** league. Pass H: measured **0 rows**
with `projection_source ≠ proj_3yr_source`, and called the area a null.

Re-measured once, this session, on the owner's own league hint
(`{scoring: ppr, superflex: True, te_premium: False}`):

```
--- projection_source ---
     18  dynasty_superflex_rankings.csv    detected={'scoring': 'standard', 'superflex': True, ...}
--- source_file (winning row) ---
     15  dynasty_superflex_rankings.csv    detected={'scoring': 'standard', ...}

rows with BOTH per-field sources present: 764   rows where they DIFFER: 500
```

**G is confirmed on both numbers — 18 and 15, exactly.** And **H's null is refuted**: not 0 rows but
**500 of 764** carry a `projection` and a `proj_3yr` drawn from different files.

**Resolution: W4-15 is a real finding**, and it belongs to Phase 2 (provenance), because the
mechanism is the same one that lets a filename decide a format.

---

## What this says about nulls, for the fourth time

A pass's null has now been refuted four times, across four different passes: pass G on `store_io`,
pass G on the untrusted fence, pass I on `store_io` **while stating its method**, and now pass H on
cross-format mixing — this one refuted by a measurement off by a factor of infinity, 0 against 500.

Twelve passes, and **not one pass's null result has proven reliable when checked**. The Wave 6
mandate's evidentiary standard improved how nulls were *written* — pass L's identity-namespace null
enumerated its branches and stated its own lack of confidence — but no standard has yet made one
*correct*.

For the repair program this is a rule, not an observation: **a null is where a pass looked. It is
never evidence that nothing is there, and nothing in Phase 8's certification may rest on one.**
