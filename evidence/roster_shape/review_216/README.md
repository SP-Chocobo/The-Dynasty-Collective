# #216 review — result sets (commit f580c11)

Produced by `run_216_review_probe.py` (repo root). Report: `../REVIEW_216_fable.md`. Tables: `TABLES_f580c11.md`.

- `r216_*` — arms CURRENT / NOFEAS / NEEDCAP. Compositions, sequences, per-state decompositions,
  replacement levels, demand and drafted counts are authoritative. **The `rf_*` / `raw_*` fields in
  these two files were computed with a defective phantom (a FLEX phantom eligible at every flex
  position) and are superseded by `r216c_*`.** Kept because the arms' picks did not depend on them.
- `r216b_*` — arms RFMLV_LEX / RFMLV_ADD / RAWMLV_LEX with the corrected phantom (eligible only at
  the position whose level it carries; reconciled by hand: Jefferson 99.44 = bpa 99.44).
- `r216c_*` — CURRENT re-recorded with the corrected phantom, for the static "rows moved" metric.

Every arm: one process, one code version, the named thing toggled; non-engine seats on
`run_roster_proof.control_pick`; `set_league_format(league_format_hint(league))` per format;
`build_players_db_from_capture()`; shared pool of 481 (WR 197, RB 126, TE 115, QB 42, DB 1).

---

## CORRECTION TO COMMIT 2393b73's MESSAGE (Opus, after the reviewer objected)

**Commit 2393b73's message is NOT the reviewer's finding.** I (Opus) committed these files
mid-flight and wrote that message myself from a partial reading. The reviewer identified three
material errors in it, and this note stands as the correction rather than a rewritten history:

1. **It omits the actual headline entirely.** `feasibility_first` is a 0/1 sort key
   (`_feasible` -> `fills_required_slot`) leading the sort in `compute_draft_board` and
   `_board_order`. It filters and substitutes nothing — it PARTITIONS the board, and binds only
   when `picks_remaining <= unfilled dedicated slots` (pick 12 of a 14-round roster). That is
   precisely where every receiver in every published roster appears. Unforced at pick 14 the
   board still takes Dulcich (TE, 124.3) over Concepcion (WR, 165.1). The board is INERT for WR
   and QB; nothing "falls through".

2. **It presents RAW-MLV as "THE HEADLINE".** The reviewer characterises RAW-MLV as *"an
   instructive control, not a fix"*. Its lineup totals are best for an ACCIDENTAL reason: with
   an empty roster every player's marginal lineup value is just his own points, so its early
   order is effectively raw points (Purdy at r1), which is the only way past a replacement that
   prices quarterbacks at 0.00. Its bench still ends TE7/TE9/TE7.

3. **It claims "every arm reproduces the recorded sequence".** Only the CURRENT arm does, by
   design — that is the replay gate. The other arms are supposed to diverge.

**Also**: the `r216_*` JSONs' `rf_*` fields came from a phantom bug the reviewer found and fixed
during the run. `r216c_*` supersedes them. Arm picks were unaffected.

The authoritative document is `../REVIEW_216_fable.md`. Read it, not 2393b73's message.
