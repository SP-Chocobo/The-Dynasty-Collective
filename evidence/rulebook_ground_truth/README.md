# The captured rulebook, checked against the system that wrote it

`data/league_captures/fourth_and_forever.json` records its own `capture_method` as
**"transcribed from Sleeper Scoring Settings screenshots supplied by the owner."** Hand entry,
into a file every measurement under `evidence/roster_shape/ff_rulebook/` depends on — and until
this check it had never been compared against a number Sleeper itself computed.

**Why no existing test could have caught a bad transcription.** Every scoring test in the repo
asserts that `compute_points_from_stats` returns what the repo *believes* the rules to be. The
rulebook is the thing being asserted, so the loop is closed: a faithful implementation of the
wrong rules passes all of them, however many there are.

## The check

Four starters, week 1, itemised by the Sleeper app on the owner's screen with the app's own
scores beside them. Scored through the production function against the capture.

| player | line as Sleeper itemised it | app | ours | fixture league |
|---|---|---|---|---|
| C. McCaffrey | 10 car, 68 yd, 2 rush FD, 5/8 rec, 20 yd | **11.80** | 11.80 | 13.80 |
| J. Smith-Njigba | 8/11 rec, 122 yd, 1 TD, 4 rec FD, 1 rec 40+, 1 TD 40+ | **30.20** | 30.20 | 34.20 |
| R. Stevenson | 18 car, 51 yd, 2 rush FD, 5/6 rec, 44 yd, 1 rec FD | **13.00** | 13.00 | 14.50 |
| B. Purdy | 25/34 cmp, 205 yd, 3 TD, 1 INT, 5 car, 29 yd, 4 rush FD | **24.60** | 24.60 | 29.60 |
| | **team total** | **79.60** | **79.60** | 92.10 |

**4 of 4 exact, and the total is the number the app displayed for those four starters.**

## What it establishes — two things, not one

1. **The transcription is faithful**, across passing, rushing, receiving, first downs, a
   receiving TD, an interception, and both 40+ bonuses *together* (Smith-Njigba's line carries
   `rec_40p` and `rec_td_40p` at once, which is the most awkward case the rulebook has).
2. **`compute_points_from_stats` implements the rules Sleeper actually applies.** That function
   is what the entire scoring-aware path runs through (#192/#213), and this is its first
   external check. McCaffrey's line alone pins four terms: `rush_yd` 0.1, `rush_fd` 0.25, `rec`
   0.5, `rec_yd` 0.1 → 6.80 + 0.50 + 2.50 + 2.00 = 11.80.

## What it does NOT establish

Nothing about whether the engine drafts well, and nothing about the fixture league's own
correctness. It says the F&F rulebook is transcribed right and scored right. That is all.

## The number it gives the freeze

The right-hand column is the same four lines under `data/fixtures/sleeper_capture.json` — the
league the battery and the roster proof actually measure, which is full PPR with no TE bonus and
no first-down scoring. **92.10 against 79.60, +15.7%**, with Purdy alone swinging 5.00 on
`pass_int −2` and the completion bonus.

So the freeze's headline result — *asset 68/68, points 67/68, by 5–11%* — was measured in an
environment that pays this roster about 16% differently from the league being played. The
deficit could shrink, vanish, or invert under the real rulebook. **Unmeasured, not refuted.**
FREEZE_CHECKLIST carries that as a named decision.

## Guard

`test_capture_reproduces_the_live_app.py`, 4 tests, mutation-checked **6/6**: `rec_fd`
0.5→0.25, `rush_fd` 0.25→0.5, `pass_int` −2→−1, `rec_40p` 2→3, `pass_cmp` 0.1→0 (all corrupting
the capture), plus one breaking the scorer's first-down handling. The capture restores
byte-identical after each. A control test requires the fixture league NOT to reproduce these
numbers, so "the scorer ignores `scoring_settings`" cannot pass.

**Provenance:** Fourth and Forever, 2026 week 1, read from the live Sleeper app by the owner.
Team SPChocobo showed 79.60 from these four starters with six yet to play.
