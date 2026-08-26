# League captures

Reference data transcribed from one real Sleeper league, kept because several engine
findings are measured against it and the commit messages that cite those numbers would
otherwise point at evidence that does not exist in this repo.

**Nothing here is loaded at runtime.** DataMerger globs `data/baseline/rankings`,
`data/baseline/trade_value` and `data/projections/*` only; this directory is deliberately
outside all of them. It is evidence, not a source.

## Greatest Show on Paper 2

12-team superflex dynasty. Roster: QB / RB×2 / WR×2 / TE / FLEX×3 / SUPER_FLEX,
14 BN, 4 IR, 5 TAXI. No K, DEF or IDP slots.

| file | contents |
|---|---|
| `greatest_show_on_paper_2.json` | full scoring settings (all six tabs), roster, draft math, and every caveat found while capturing it |
| `*_qb/rb/wr/te_proj.csv` | Sleeper SEASON PROJ, league-scored, with the stat lines behind them |
| `greatest_show_on_paper_2_rookie_draft.csv` | the completed 4-round rookie draft, 48 picks |

### What was measured against it

- **`positional_bench_appetite` is wrong at the tail.** It predicts 80.6 QBs consumed;
  ~52 actually went. A replacement that fixed QB (52.3) broke K and DEF and was reverted.
- **Rookie consensus predicts rookie drafts.** KTC's rookie ranks vs actual pick order:
  Spearman ρ = +0.908 across 45 of 48 matched picks — higher than any vendor-vs-vendor
  agreement on veterans measured alongside it.
- **Placeholder picks are indistinguishable from real ones.** ~36 of ~360 startup picks
  were kickers standing in for future rookie picks, in a league rostering no kicker.
  `expected_positional_consumption` now filters picks at zero-starter-demand positions.
- **Transcription verified**: re-scoring the stat lines through the recorded scoring
  settings reproduces Sleeper's own PROJ column to a median residual of 0.0 (TE) to
  −3.96 (QB), and confirms the 0.75 TE reception bonus.

### Limits

ONE league, ONE rookie class, ONE room. Every number above is a single sample. The user's
own caveat applies and is recorded in the JSON: league settings vary enormously, and this
is a data point for testing, **not a benchmark for what dynasty looks like**. No engine
constant should be calibrated to it without replication.

Manager handles from the rookie board were stripped; `pick_was_traded` preserves the
finding (42 of 48 picks changed hands) without publishing anyone's name.
