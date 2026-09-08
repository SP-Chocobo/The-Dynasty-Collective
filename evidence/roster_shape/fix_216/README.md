# #216 fix — result sets (implementer: Fable)

Produced by `run_216_fix_probe.py` (repo root; run with `PYTHONPATH=.` from the root, see the
engine-measurement skill). Report: `../FIX_216_fable.md`. Pre-registration, written before any
measurement: `../PREREGISTRATION_216_fix.md`.

- `FIX216_12T_ppr.json`, `FIX216_12T_ppr_SF.json` — four arms per seat (BASE_ON / BASE_OFF /
  FIX_ON / FIX_OFF: the displacement term switched off or on × `feasibility_first` as shipped
  or replaced by its documented no-op), seats 1, 6, 12. Per state: the chosen row's
  decomposition, whether the backstop bound, whether the pure `team_acquisition_value` argmax
  was overridden, the best remaining QB's price, the league and ledger WR−TE gaps, the
  displacement adjustment per position, the top five. Per draft: composition, legality by the
  shipped optimizer, lineup points on the season projections, the same for the control seat,
  and the G9 block (`g9_engine` / `g9_control`: `run_roster_proof.score_roster` on both rulers,
  mean age, mean pre-draft `time_horizon_adj`). `replay_matches_recorded` on every BASE_ON draft.
- `probe.log` — the console trace, one line per engine pick.
- `TABLES_compositions_invariants.md` — compositions/lineup/forced table, invariant 2 (QB price
  by round), invariant 4/5 (league vs ledger gap by round), bench compositions.
- `TABLES_G9_asset_age_horizon.md`, `TABLES_G9_asset_decomposition.md` — the owner's gate.
- `mutations/` — the runner, per-mutation unittest tails, `mutations.json` (9 applied, 9 killed).
- `battery_falsification_after_fix.txt` — `test_216_value_board_falsification` verbose run
  (19/19) on the fixed engine.
- `projection_control_guard_on_unfixed_code.txt` — the loose thread: the adversary's
  "board is not the projection control" guard run on the UNFIXED engine (passes).
- `targeted_tests_after_fix.txt` — the 16-module targeted run (497 tests) before the
  set-eligibility refinement; the one failure it shows is the IDP-flex wiring test that
  refinement was made for, green in the full suite.

Every arm: one process, one code version, the named thing toggled; non-engine seats on
`run_roster_proof.control_pick`; `set_league_format(league_format_hint(league))` per format;
`build_players_db_from_capture()`; shared pool of 481.
