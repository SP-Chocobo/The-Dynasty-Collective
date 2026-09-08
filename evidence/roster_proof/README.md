# Roster-proof evidence — #205

The control-vs-engine proof: does the engine build BETTER ROSTERS than a competent projection
ranking? Distinct from the #150 battery, which asks only whether the engine breaks its league's
rules. An engine that always drafts the highest-projected player available is perfectly legal
and completely pointless; both gates are needed and neither substitutes for the other.

Committed for the reason the instrument itself is committed: **#177's harness lived only in a
scratchpad and is gone**, so its numbers can be neither re-derived nor challenged (#208).

## Naming

    ROSTER_PROOF_<date>_<what-it-is>_<commit>.json

The commit is the one the run STARTED at.

## Runs

### ROSTER_PROOF_2026-09-08_partial_4of6_3198a9e — PARTIAL, 4 of 6 formats

`complete: false`, `formats_done: 4`, 1,586s. **The process was killed at 04:13** — no error, no
traceback, no OOM (14.4 GB free) and no disk pressure; it coincides with an unrelated background
watcher exiting. The two unrun formats are `12T_standard` and `12T_ppr_TEP`.

**This file exists at all only because the report is written after every format.** That change was
made hours earlier for exactly this reason and had not yet been needed. Recorded here because a
protection that silently pays off is worth naming when it does.

    format        rounds  [cdme / total]                    [points / starter]
    12T_ppr         14    eng   -5.98  ctl -168.28  12/12   eng  610.76  ctl  840.61   0/12
    12T_ppr_SF      15    eng  440.99  ctl  150.95  12/12   eng 1077.09  ctl 1147.53   0/12
    10T_ppr         14    eng  -24.30  ctl -173.21  10/10   eng  663.82  ctl  863.90   0/10
    10T_ppr_SF      15    eng  578.00  ctl  186.28  10/10   eng  988.58  ctl 1203.87   0/10

**Every seat, every format, both directions.** The engine wins the asset ruler 44/44 and loses
the season-points ruler 0/44. That is pre-registration outcome 3, and it is not close or noisy.

READ THIS WITH THE PRE-REGISTRATION, NOT INSTEAD OF IT. In particular:

- The cdme totals for the 1QB arms are NEGATIVE for both sides (engine −5.98 against control
  −168.28). That is the named contamination: `total_value` sums below-replacement negatives, and
  what a below-replacement player is worth to own is RESERVED (#155/#165). The engine wins by
  being far less negative. Both arms are contaminated identically so the COMPARISON stands; the
  absolute figures are not roster worth and must not be quoted as such.
- The points deficit is much larger in 1QB (−230, −200 on ~840–860) than in superflex (−70 on
  1147). Whatever drives it is stronger where the engine cannot spend a pick on a second QB.
- 4 of 6 formats is not the ordered run. `12T_standard` and `12T_ppr_TEP` are absent, and the
  scoring axis they were chosen to test is therefore untested here.
