# Verbatim pass reports — v2 blind adversarial audit

**Why this directory exists.** `FINDINGS_V2.md` is my CONDENSATION of these reports. That
condensation is a lossy filter chosen by the person who commissioned the passes, which is the one
reading of an adversarial audit that should not be the only surviving one. The agent transcripts live
under `/tmp` and do not survive the container.

So each pass's final report is reproduced here **verbatim**, exactly as it was handed back, with no
editing, no reordering and no correction — including any claim a later pass narrowed or refuted.
Where a pass was later adjudicated (the SKEPTIC narrowed two of the five HIGH claims and corrected
one derivation), the original text stands unchanged here and the adjudication is in `FINDINGS_V2.md`
and in `skeptic.md`.

**These are model output, not measurements I verified.** Where I verified something myself, that is
stated in `FINDINGS_V2.md`, not here. Read a report as a claim with its evidence attached.

| file | lens | wave |
|---|---|---|
| `a_valuation_arithmetic.md` | pricing path, units, constants | 1 |
| `b_absence_and_contracts.md` | absence semantics, boundaries, prose claims | 1 |
| `c_measurement_apparatus.md` | tests, ratchets, guards, coverage instruments | 1 |
| `d_roster_geometry.md` | slots, eligibility, league shape, backstops | 1 |
| `e_ingestion_identity.md` | identity, provenance, vintage, scoring reach | 1 |
| `f_mutation_survival.md` | do the committed mutations survive the suite | 2 |
| `g_ui_state.md` | Streamlit state, caches, what the user sees | 2 |
| `h_robustness.md` | bad inputs, dependency failure, degenerate state | 2 |
| `skeptic.md` | adversarial adjudication of the five HIGH claims | 2 |

Wave 2's first attempt (six lenses) was killed by the five-hour session window before any pass
reported; there is nothing to reproduce from it. Its lenses are listed in `FINDINGS_V2.md`.
