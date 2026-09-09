# League captures

Reference data transcribed from one real Sleeper league, kept because several engine
findings are measured against it and the commit messages that cite those numbers would
otherwise point at evidence that does not exist in this repo.

**Nothing here is loaded at runtime.** DataMerger globs `data/baseline/rankings`,
`data/baseline/trade_value` and `data/projections/*` only; this directory is deliberately
outside all of them. It is evidence, not a source.

## Fourth and Forever

12-team superflex dynasty, HALF PPR with a 0.25 TE reception bonus. Startup opened
2026-08-09 (slow clock, 26 rounds); rookie draft 2026-08-14. Boards under
`evidence/real_drafts/boards/`.

| file | contents |
|---|---|
| `fourth_and_forever.json` | four of six scoring tabs (PASSING/RUSHING/RECEIVING/MISC), each category marked for whether stat data exists behind it |

**Starting lineup NOT captured.** Every replacement-level and free-alternative quantity
depends on it, so nothing surplus-shaped can be measured for this league yet.

### What makes it different from the other capture

These are the only two leagues with captured rulebooks and they are not close. Half vs
full PPR, TE reception 0.75 vs 1.75, passing TD 4 vs 5, interception -2 vs -1. And three
whole mechanics exist here and nowhere else: **first-down scoring** (rec_fd 0.5, rush_fd
0.25 -- receivers paid double what backs are for the same first down), a **completion
bonus** (0.1), and **40+/50+ big-play ladders** on all three phases. No battery format
carries any of them.

### Six rulebook categories have no stat data

`pass_td_50p`, `rush_td_50p`, `rec_td_50p` and the three PLAYER-side special-teams
categories have no matching key in `data/fixtures/sleeper_capture.json`. Small in points
-- all rare events -- but the 40+ variants of the same three bonuses DO exist, so the 50+
gap is a vocabulary hole, not a category Sleeper never tracks.

The mechanism is worth its own note: `compute_points_from_stats` and `score_projection`
both guard with `if value:`, so a category with no data and a category measured at zero
are indistinguishable, and neither can report which of a league's rulebook categories it
received nothing for. Harmless for the arithmetic, not harmless for knowing whether a
league is scored completely.

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
- **Re-verified 2026-09-09 by least-squares fit** (49 QB rows), after the owner
  challenged the 5-point passing TD:
  - `pass_td = 5` **CONFIRMED**. Free fit returns +5.20; forcing 4 moves the median
    residual to −15.04. Not a mistranscription.
  - A completion bonus is **RULED OUT** here — adding a completion proxy returns a
    coefficient of −0.008 and does not move RMSE. Fourth and Forever has one; this
    league does not.
  - `pass_int = -1` is **NOT supported** — the fit returns −1.47. Recorded as
    unresolved rather than corrected: int is collinear with volume over 49 rows.
  - The +3.96 QB residual is **systematic, not rounding**. Freeing the coefficients
    pulls both yardage terms below nominal (pass_yd 0.0394, rush_yd 0.0961), which is
    the signature of a missing negative that scales with volume. Consistent with the
    fumbles explanation in direction; larger than "rounding". The stat CSV has no
    fumble column, so it cannot be closed from data in hand.

### Limits

ONE league, ONE rookie class, ONE room. Every number above is a single sample. The user's
own caveat applies and is recorded in the JSON: league settings vary enormously, and this
is a data point for testing, **not a benchmark for what dynasty looks like**. No engine
constant should be calibrated to it without replication.

Manager handles from the rookie board were stripped; `pick_was_traded` preserves the
finding (42 of 48 picks changed hands) without publishing anyone's name.
