# `#52` Wave 3 — passes E and F, condensed

> Both declared **no contamination**; both verified the exclusions before reading. E additionally
> disclosed seeing ~40 prior-session probe *filenames* in an `ls` and opening none — exactly the
> self-report the mandate asks for. Both ran full multi-round drafts on the capture's own
> `league_shape`. E: 1,398s. F: 1,505s.

## THE HEADLINE — found INDEPENDENTLY by both passes

**On the owner's own league the engine drafts four to five kickers per roster.**

- **E:** 14-round draft — seats 11 and 12 finish with **5 K each**, seats 7 and 10 with 4.
  Rounds 8, 9, 11, 12, 13 are 5–6 kickers each. Verified through the production path: at pick 126
  `build_snapshot(...).candidates[0..5]` are **six kickers**, then an LB, then Stefon Diggs.
- **F:** 25-round draft — seats 6/7/10/11/12 hold 4–5 kickers; **28 of the 84 picks in rounds
  8–14 were kickers**; at pick 132 the top five rows on the board were all kickers. Also 7 DBs on
  two seats, 6 DL on another.

**Mechanism (arithmetic, not tuning).** From roughly pick 117 every position is underwater, so the
least-negative row wins. K has the flattest curve (K1 134 → K12 121.8), so a K2 costs −0.7…−4.9
while a WR6 costs −15…−60. F adds the second half: `displacement_level` treats a rostered player
who does not *beat* the phantom as "not an occupant" — but the player drafted to fill a
position's last starter slot sits *at* the level (VOR 0.00) by `replacement_levels`' own case (2),
so he ties the phantom and **his slot reads as open for the rest of the draft.**

**Every roster was legal.** No unfilled slot, so `unfilled_starting_slots` and
`undraftable_positions` report nothing. `displacement_level`'s docstring claims the term ended
"ELEVEN tight ends and no receiver"; the same hoarding is alive at K with the term on.

**WHY NOTHING CAUGHT IT — verified independently by this session:**

```
battery arms: 34
arms with a K slot: 0
arms with SUPER_FLEX *and* IDP: 0
owner league: K True | SUPER_FLEX True | IDP_FLEX 2 | BN 14
```

`run_roster_proof.py` and `run_smoke_seats.py` also use `build_mock_league`, which has no K.
**The owner's roster shape is structurally outside every instrument in the repository, on three
axes at once.**

## Other new findings

**E-5 (MEDIUM, NEW) — live level → pre-draft anchor is a discontinuity.**
`predraft_replacement_anchor`'s docstring says "the last live level is therefore the pre-draft
level -- verified directly". Spy on `replacement_levels`: WR drifted 225.49 → **214.06** by pick
125, then WR demand hit 0 and every WR row **snapped back to 225.49** — the position's top bpa
went 0.00 → −11.43 in one pick.

**E-7 (MEDIUM, NEW) — `waiting_cost` for K swings ~100 points on which branch the appetite model
takes.** Measured sequence across picks 96–144: 116.75 → 49.49 → 7.27 → 22.0 → None → 107.35 →
91.0 → 61.3 → 91.0. The user-visible sentence reads "projects 122 season points against 22 for
the best K expected to still be undrafted". The docstring says flat positions "are the ones it
estimates best"; it is inverted on the flattest position in the league.

**F-6 (MEDIUM, NEW) — `remaining_starter_demand` does not reach zero when every slot is filled**,
against its own docstring. Twelve rosters filling every starting slot legally leave
`{DB 8.0, DL 8.0, WR 4.6, TE 4.6}` = **25.2 phantom slots**; fill the flexes differently and it is
`{LB 8, TE 4.6, QB 10.2}`. So which positions flip to the pre-draft anchor depends on the fill
mix — two anchors for one state. In the full draft, 102 of 300 chosen rows were priced on
`predraft_anchor` and 166 on `live_starter_demand` at the same late states.

**F-8 (NEW) — `waiting_cost` is `None` for all 148 QB rows** in the superflex league
(`horizon_basis unavailable`: 42 priced QBs < 2×22 demand). **The scarcest position is the one
with no waiting cost.**

**F-5 (NEW) — the two projection sources treat zero oppositely.** A Sleeper season sum of 0
becomes `None` → `absence_kind no_input` ("no source carried a projection"), while a **vendor
projection of 0.0 is admitted as a measured number** (Milroe, Richardson priced at bpa −207.50,
`absence_kind None`). Same fact, two contracts.

**E-4 / F-3 (NEW detail) — the SF pace prior hands out `survival 0.000`.** Josh Allen, Burrow
0.000, Lamar 0.002 → `opportunity_cost 169.92` → **+20 necessity from a number the repo itself
measured as losing to a constant predictor**, displayed while survival is withheld.

**F-9 (NEW) — `test_cdme_certification.test_tav_never_falls_below_universal_value`** still says
"structurally impossible". On the owner's league at pick 1, **216 priced rows (all DB/DL) have
TAV < UV.** It passes only because it runs at an empty roster on a no-IDP mock.

## Corroborations (now at four to six passes each)

`time_horizon_adj` population mismatch (**6/6 passes**); survival leaking through `pick_necessity`
(**6/6**); the two take models (5/6); `prose_names` shield (4/6 — E measures 59.2% of *occurrences*
shielded); the `need_bonus` tautology (4/6); anchor cache key (4/6); `displacement_adj` positive
on multi-eligible (F reproduces +79.44, and **+129.40 on HEAVY_IDP**); the 0–100 scale prose
(5/6); `qb_startable_floor` unit mismatch (3/6).

## Null results (both)

Layer identity `TAV == UV + need + elig + depth + displacement` holds on every priced row of every
board and the full draft. `replacement_levels` sort/tiebreak; cross-position same-name resolution
(52 shared names, none crossed a position family); anchor caches content-keyed with no order
dependence; `_admits_to_pool` precedence; no unpriced row ever chosen in 300 picks;
`feasibility_first` never had to bind and all rosters legal.
