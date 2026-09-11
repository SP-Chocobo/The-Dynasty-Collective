# The battery's TE-premium axis is not exercised: all 33 arms hint `te_premium=True`

Found while answering #175's Q1, not looked for. Registering it separately because it is about
`league_matrix`'s coverage, not about the cliff ratio.

## What was measured

`draft_battery.league_format_hint(league)` produces the `{scoring, superflex, te_premium}`
triple that `DataMerger.set_league_format` discriminates on — it is what decides **which
rankings export an arm draws from**. Across the 33 arms of `league_matrix(real_rulebook)`:

```
scoring=half_ppr  superflex=False te_premium=True   ->  4 arms
scoring=half_ppr  superflex=True  te_premium=True   ->  4 arms
scoring=ppr       superflex=False te_premium=True   -> 13 arms
scoring=ppr       superflex=True  te_premium=True   ->  4 arms
scoring=standard  superflex=False te_premium=True   ->  4 arms
scoring=standard  superflex=True  te_premium=True   ->  4 arms
```

**`te_premium=False` appears zero times.** Including on the arms that exist to be the control:

```
12T_ppr_TEP_dynasty    bonus_rec_te=0.5    hint te_premium=True
12T_ppr_redraft        bonus_rec_te=0.25   hint te_premium=True
12T_ppr_TEP_redraft    bonus_rec_te=0.5    hint te_premium=True
4WR_TE_PREMIUM         bonus_rec_te=0.5    hint te_premium=True
```

## Why

`league_format_hint` reads `bonus_rec_te > 0` off the league's merged `scoring_settings`. Since
**#213**, every arm carries the REAL Fourth & Forever rulebook as its `base_scoring` — and that
league is itself TE-premium, `bonus_rec_te = 0.25`. So `build_mock_league(te_premium=False)`
adds no bonus but cannot *remove* the one the base rulebook already supplies. Its output is a
TE-premium league either way.

This is a **side effect of a correct repair**, not a regression in it. #213 fixed 27 arms that
were scoring quarterbacks against a one-key rulebook; the price was that one axis of the matrix
stopped varying, silently, because nothing checks the hint distribution.

## What it does and does not invalidate

**Does not invalidate the TEP arms' findings.** The `bonus_rec_te` VALUE still differs (0.25 vs
0.5), and that difference does reach valuation through the scoring-aware path: raising it
changed 113 of 114 TE gaps on a real opening board, and 0 gaps at every other position. The
TE-premium *scoring* axis is exercised.

**Does invalidate any claim about export selection under TE premium.** All 33 arms draw the
same TE-premium-side export. `te_premium_dynasty_rankings.csv` and
`dynasty_te_premium_superflex_rankings.csv` are preferred on every arm;
`fantasy_football_dynasty_rankings.csv` and `dynasty_ppr_rankings.csv` never win the
non-TE-premium tiebreak, because no arm ever asks for it. If a defect lives in that branch, this
battery cannot see it.

**It also means the matrix's `independent_formats` count is right for the wrong reason on this
axis** — the arms are not duplicates (their scoring values differ), so `duplicate_arms` does not
flag them, yet one of the four axes the matrix advertises is constant.

## The shape of the remedy, not a recommendation

Two separable options, both decisions:

1. **Let an arm state a rulebook OVERRIDE, not just an addition** — so `te_premium=False` can
   zero `bonus_rec_te` rather than merely decline to raise it. Cheapest, and it restores the
   advertised axis. Cost: an arm then measures a league Fourth & Forever is not.
2. **Report the exercised hint distribution in the battery report**, next to
   `independent_formats`, so a constant axis announces itself the way a duplicate arm already
   does. Does not restore coverage; makes its absence impossible to miss.

(2) is strictly an instrument improvement and matches how `duplicate_arms` already works —
derived from what the arms actually produced, never hand-listed. (1) is a judgment about what
the battery is FOR, which is the owner's.

## Reproduction

```
PYTHONPATH=. python3 -c "
import json, draft_battery as db
CAP = json.load(open('data/league_captures/fourth_and_forever.json'))
BASE = {k: v['value'] for k, v in CAP['scoring_settings_observed'].items()}
import collections
c = collections.Counter(db.league_format_hint(e['league'])['te_premium']
                        for e in db.league_matrix(BASE))
print(c)"
```
