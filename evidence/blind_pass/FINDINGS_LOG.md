# `#52` findings log — append-only, in arrival order

> **THIS FILE DOES NOT TRIAGE.** No verdicts, no novelty calls, no clustering, no merging of two
> passes' versions of one thing. Every pass's findings are logged as that pass stated them, in the
> order they arrived, and nothing already written here is edited when a later pass contradicts it.
> That is the point: the log is the record of *what was claimed when*, so the triage in
> `LEDGER.md` can always be checked against what it was built from.
>
> - **Raw text of each pass:** `wave<N>/PASS_*.md` — verbatim, the source of truth.
> - **Verdicts, novelty, clusters, disputes:** `LEDGER.md`.
> - **This file:** the running list, append-only.
>
> Waves 1–4 below are backfilled from the ledger's own enumeration and are marked as such; from
> Wave 5 on, entries are logged from each pass's report as it lands, before any triage.

---

## Wave 1 — passes A and B *(backfilled)*

20 findings logged, W1-01 … W1-20. Not restated here: the ledger's Wave 1 table is itself the
per-finding list as reported, and the verbatim text is in `wave1/PASS_A.md` and `wave1/PASS_B.md`.

Headline claims: `displacement_adj` positive against a non-positive contract; `time_horizon_adj`
percentiles over two populations; anchor cache fingerprint incomplete; the `need_bonus` invariant
test a tautology; the `prose_names` history shield exempting ~40% of prose; a comment citing a test
that does not exist; survival reaching a displayed score through `pick_necessity`; `league_config`'s
blocking gate uncalled.

## Wave 2 — passes C and D *(backfilled)*

10 findings logged, W2-01 … W2-10. Verbatim: `wave2/PASSES_C_AND_D.md`.

Headline claims: contested-identity guard a function of the remaining pool only; `qb_startable_floor`
in vendor units; superflex QBs unpriced with `absence_kind=None`; `block_opportunity` unreachable in
production; the `trade_value` branch clamping to a 2-row list on the owner's own league; TAV below UV
on 246 of 796 priced rows; thirteen test modules on the fixture the repo declares non-production;
`CDME_CONTRACTS.md` false in four places; the `round` off-by-one; `roster_id=None` as a phantom team.

## Wave 3 — passes E and F *(backfilled)*

8 findings logged, W3-01 … W3-08. Verbatim: `wave3/PASSES_E_AND_F.md`.

Headline claims: the engine drafts 4–5 kickers per roster on the owner's league with zero structural
findings; the live-level → pre-draft-anchor discontinuity; `remaining_starter_demand` not reaching
zero; `waiting_cost` None for all 148 superflex QB rows and swinging 7.27 → 116.75 for K; vendor 0.0
admitted while Sleeper 0 becomes None; 216 priced rows violating a "structurally impossible" test.

## Wave 4 — passes G and H *(backfilled; the wave is logged in full in the ledger)*

29 findings logged, W4-01 … W4-30 (W4-05 struck on checking as already-registered `#184`). Verbatim:
`wave4/PASS_G.md`, `wave4/PASS_H.md`. My own re-measurement: `wave4/MY_VERIFICATION.md`.

Headline claims: the flat per-dedicated-slot `need_bonus` worth 32% of a kicker's whole
above-replacement spread; two shipped constants derived from a bound the engine violates by 2.4×;
`_picks_by_mode` asserting what its docstring says it reports; the LLM prompt boundary offering
chairs a withheld number with a worked example; the snapshot diff printing the withheld survival
family in full to chairs and to the person, with the suite pinning that leak; `format_axes_exercised`
unable to see roster-slot composition at all; 51 LB / 51 DB / 16 DL into 24 IDP_FLEX slots;
`growth_signal > 0` on 0 of 131 upside picks; the necessity pill unable to read below CLOSE CALL
before round 15 and above LOW URGENCY after; `store_io` dropping writes after any `OSError`;
`pick_debate` carrying no untrusted fence; the evidence block at 84 candidates against a budget test
asserting on 5.

**Logged separately because it is about the audit, not the engine:** two of pass G's five null
results were wrong, and pass H found real defects in both areas. From Wave 5 the mandate requires a
null to state how it was established.

---

# Wave 5 onward — logged live, before triage

## Wave 5 — passes I and J

*Launched. Mandate adds a null-result evidentiary standard, a state/persistence/process-boundary
category, and steers toward the self-integrity instruments. Neither pass has reported.*

<!-- APPEND POINT: each pass's findings go below, in arrival order, unedited afterwards. -->
