# WITHDRAWN: "the OWNER_LEAGUE fixture is not the owner's league"

## What I claimed

Earlier this session I recorded, as a CRITICAL DEFECT, that `OWNER_LEAGUE` in
`run_216_bench_probe.py` did not match the owner's real league, and that this
invalidated three findings measured on that arm -- "zero tight ends", "12 of 12 bench
receivers", and a seat-1 regression.

## Why it was wrong

I compared the fixture against **Greatest Show on Paper 2**, because that was the only
rulebook captured at the time. But "the owner's league" in that fixture means the
REDRAFT league already documented in `evidence/reference_rosters/OWNER_REDRAFT_2026-09-08.md`.
Against that document, every field matches:

| field | fixture | reference roster |
|---|---|---|
| starters | QB, WR, WR, RB, RB, FLEX, FLEX, WRRB_FLEX, SUPER_FLEX (9) | QB / 2 WR / 2 RB / 2 W-R-T flex / 1 W-R flex / 1 SUPER_FLEX (9) |
| bench | 5 | 5 |
| teams | 12 | 12 |
| `rec` | 1.0 | PPR |
| `bonus_rec_te` | 0.5 | 0.5 TE premium |
| `dynasty` | False | REDRAFT |
| `draft_type` | 3rr | 3RR |

The label itself -- `OWNER_3RR_SF_noTE` -- encodes three of them. Nothing is mislabelled.
I matched a fixture against the wrong league and called the fixture broken.

## What this restores

The three findings measured on that arm are NOT invalidated. They are findings about a
12-team PPR redraft with a 0.5 TE premium, NO dedicated TE slot, a W-R-only flex, 3RR,
and a 5-slot bench -- which is exactly the format that makes "zero tight ends" and
"bench receivers" interesting, and is why that arm exists. They stand, scoped to it.

## What was actually missing, and now is not

The owner has since supplied the rulebooks for both DYNASTY leagues. The real gap was
never a wrong fixture; it was that two of the owner's three documented leagues had no
capture at all. Both now do:

- `data/league_captures/greatest_show_on_paper_2.json` -- 12T SF dynasty, full PPR, TE 1.75/rec
- `data/league_captures/fourth_and_forever.json` -- 12T SF dynasty, half PPR, TE 0.75/rec
- `evidence/reference_rosters/OWNER_REDRAFT_2026-09-08.md` -- 12T SF redraft, PPR, no TE slot, 3RR

## The general failure

Twelfth withdrawal this session, and the second where the error was comparing a correct
thing against the wrong reference rather than mis-measuring anything. A fixture is only
"wrong" relative to a named league; I did not name one before declaring the mismatch.
The fixture's own label carried the answer.
