# Independent review: can each Tier 0 instrument report success while measuring nothing?

> **STATUS: this document is a live adversarial review of the measuring instruments**, written
> by a session that was given the instrument list and the question and nothing else. It is
> IN PROGRESS — sections are added as each demonstration completes. Every claim below is
> labelled **PROVED** (a thing was broken and the instrument's own output is quoted) or
> **SUSPECTED** (read from the code, not yet demonstrated).

One question was asked of eight instruments plus two battery report builders: **can it report
success while measuring nothing?** The method was not reading — it was breaking something each
instrument claims to catch and quoting what it then said.

Probe scripts: `evidence/blind_pass_v4/probes/`.

## Environment note, recorded because it changes how two of these read

This container began with **no `pandas`, `numpy`, `scipy` or `streamlit` installed**. In that
state `invariant_registry.py` exits 1 with five `ModuleNotFoundError` rows — it fails loudly,
which is correct and is to its credit. `assertion_execution.py` in the same state printed
`9 of 1265 tests that ran executed no assertion (0 skipped, 179 errored)` and **exited 0**.
Dependencies were installed from `requirements.txt` before any measurement below was taken.

---

## Findings, severity order

(Populated as each demonstration completes. See the per-instrument sections for the full
record, including the instruments that came back clean.)

