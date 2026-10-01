# `#30` — the math behind streaming pick placement for K and DST

**BLOCKING on the v2 freeze (owner ruling, 2026-09-23).** The `v2-freeze` tag cut earlier was
withdrawn on this ruling; it had never been pushed, so nothing external referenced it.

## The thread, so it cannot be lost again

1. The engine drafts defenses about five rounds early. Owner's target is the bottom 25–30% of the
   draft — **rounds 12–16 of 16**. Measured on `12T_ppr_K_DEF`, HEAD: **first DEF round 5.08,
   first K round 7.00**, with 47 of 192 K/DEF picks gone before round 12.
2. `#16` forced the shape by ordering the board on `acting_now_value`. It **regressed**: −6.09
   mean on the independent `points` ruler across six formats, seat wins collapsing 11/12 → 2/12.
   Unwound at `#22`.
3. The replacement was to be a **per-position forecast-reliability shrink on `bpa`**, derived from
   historical K/DST accuracy. That is why the 2023/2024 pull was requested.
4. `#18` measured it to completion. **No shrink is derivable.** DEF's ordering skill (0.75 / 0.48)
   is about QB's; K is the weak position; the hindsight-free slope says DEF's projected spread is
   *compressed*, not inflated.
5. And it could never have worked. `KDST_VALUATION.md` already contained the disproof:
   **"Zeroing K/DEF `bpa` entirely still leaves them at +4.00, ahead of everything from round 8
   onward."** A shrink SCALES `bpa`; scaling it to zero does not fix placement. The promised
   solution was arithmetically excluded before the data was requested.

**So no solution landed, and the one that was promised cannot exist.** That is the state this
document exists to stop anyone rediscovering a third time.

## Why every projection-side lever failed, stated once

`KDST_VALUATION` measured three and found none could work: `positional_forfeit` never reaches the
board, `waiting_cost` points the wrong way, and every sane replacement choice leaves VOR near 30.
`#18` added a fourth — reliability — and it is not a defect. Five independent measurements now
exclude `bpa` magnitude, the last by *moving* the price 2.2× and watching placement shift by less
than a round.

They all failed for one reason: **they are all downstream of a replacement level that is wrong for
a streamed position.**

## THE LEAD: the replacement basis assumes you own one defense all season

`replacement_levels` prices DEF against `live_starter_demand` — teams × DEF slots = **DEF12**. That
encodes: *"if I do not take this defense, I own the 12th-best defense, all season."*

Nobody plays that way. **K and DST are streamed**: the alternative to drafting a defense is not
owning DEF12 for seventeen weeks, it is owning *the best defense available on the wire, each week*.

Those are very different quantities, and the difference runs in exactly the direction the
placement error does:

- Season-long DEF12 is one mediocre team's whole year.
- A streaming baseline is a **weekly maximum over whatever is unrostered** — far higher across a
  season, because it re-picks every week and never eats a bad matchup twice.

The higher the true baseline, the smaller DEF1's real edge, and the later a defense should go. An
engine measuring against DEF12 sees a 30.5-point edge that a streamer never actually gives up.

**This is a replacement-basis error, not a valuation error** — which is precisely why four
projection-side levers and a reliability measurement all came back clean. They were all correcting
a number whose *denominator* was the wrong question.

## Why this is derivable rather than chosen (`#56`)

The streaming baseline is measurable from data already committed. For 2023 and 2024 we hold 18
weeks of realized stats and 18 weeks of projections (`data/fixtures/weekly_*.json.gz`,
`sleeper_weekly_2024.json`).

For each week: rank defenses by what they ACTUALLY scored, take the best one outside the top
`teams × slots` rostered, and sum across the season. That is what a streamer really got. Every
input is either a league fact (`teams`, `roster_positions`) or a measured outcome. **No constant is
selected**, which is the bar `#56` sets and the bar the `acting_now` repair failed.

The same construction applies to K, and the two positions may well differ — `#18` found K's
ordering skill is the weak one (0.41 / 0.20, the 2024 figure within one standard error of zero)
while DEF's is about QB's.

## THE GATE this must pass before it lands (owner ruling)

**No production/draft quality drop-off of the kind the brute-forced version caused.** `#16` is the
counter-example and the bar: it bought the shape and paid −6.09 on the independent ruler.

Measured on `run_smoke_seats` — engine seat against a field of differing sane styles, seat
controlled, on the `points` ruler, which is the ruler the engine does not optimise toward. A
candidate must be at worst comparable to HEAD there.

**And the gate has a hole that must be closed first.** All six of the grader's formats carry
**zero K and zero DEF roster slots** (`build_mock_league` emits none), so the instrument that would
certify a K/DST fix cannot currently see K or DST at all. `12T_ppr_K_DEF` has to be wired in before
the gate means anything.

**ADP cannot serve as the human baseline here**: all 32 defenses share ONE ADP value (16983.0) and
35 kickers share three (17983–17999), against an "undrafted" sentinel of 18000.0. Those are vendor
placeholders, not market behaviour. `need_first` and `points_need` DO price K/DST from projections
(38 K and 32 DEF in the scoreable pool) and are the real comparison field.

## The independent ruler that now exists

Every quality number in this project scores rosters on PROJECTIONS. `#288` concluded no ruler
independent of the engine's own objective exists, so a deficit could not be converted into a claim
about real-world cost.

The historical pull changed that. With both projections and realized stats committed for two
seasons, a roster can be drafted on 2024 projections and scored on **what actually happened in
2024**. That is the first ruler in this project the engine cannot optimise toward, and it is the
honest way to settle whether a defense in round 5 costs real points.

## Status

**OPEN. BLOCKING v2.** Nothing is implemented. The lead above is a hypothesis with a derivation
path, not a result, and it must be pre-registered before it is run — the night this was written
produced eight withdrawn conclusions, every one measured and every one measuring the wrong object.
