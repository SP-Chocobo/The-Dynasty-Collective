# `#35` contemplation — what is the replacement unit for a bench player's value?

*A design contemplation, not an implementation. No engine code was edited. Everything numeric
below was produced by two read-only probes against the real capture, and every number is
labelled with the state it came from. The owner rules (`#184`); this proposes.*

## The short version

1. **The question as posed has a literal answer, and the literal answer is wrong.** "Compared
   with spending this roster slot on the best available player at ANY position" is a common
   constant subtracted from every bench candidate — it ranks bench bodies by raw projection, and
   raw projection takes Barner (179.5) over Shaheed (170.2) too. Removing the positional anchor
   removes the wrong *reason*; it does not add the missing *content*, which is fieldability.

2. **The engine has no bench objective at all.** `bpa + displacement_adj` is `points − displaced`,
   the candidate's *deficit* against the weakest thing in a slot he can reach, in a one-week,
   no-absence world with a phantom "free" player in every unheld slot. A deficit is a distance to
   starting. Two bench bodies are therefore ranked by *how far below starting they sit*, and —
   this is the mechanism — against **different reference objects**: a tight end against my own
   TE1 (real, 190.3), a receiver against the FLEX phantom (fictional, 216.25, the pre-draft WR
   anchor, 43 points above any receiver left on the board). The 18-point preference for the
   fourth tight end is the difference between those two objects. Nothing in it is about the bench.

3. **A bench body's replacement unit is the waiver wire in the weeks he would actually play.**
   His value is `Σ over those weeks of (his week − the wire's week)` when he is the best cover
   available. The weeks he plays are set by two things: the **schedule** (byes — a league fact,
   derivable, no constant) and **injuries** (a rate the engine does not have and, by its own
   doctrine, must not invent). The core can price the first. The second is a preference or a
   base-rate layer, and saying so plainly is the finding.

4. **Measured on seat 5's real roster at the documented pick, every roster-global formulation
   returns the same value for Barner and for Shaheed** — 0 and 0 in three phantom worlds, 10.56 and
   10.01 in the fourth (one bye week, week 8, when three of the roster's bench bodies sit out at
   once). Three better bench bodies already exist; a fourth insures nothing. The roster objective is
   *indifferent*; the engine is not, for a reason unrelated to the roster.

5. **The pick before that one is different, and worse.** At round 12 (the third tight end), the
   same FLEX phantom hid a running back who would have **started** in FLEX over the roster's TE2
   (+13.05 on the roster's own single-lineup objective) and the engine ranked him 10.4 points below
   a tight end who would not. That is the anchor's staleness reaching the price, exactly where
   `displacement_level`'s docstring says it does ("a position with an OPEN reachable slot … the
   price is `points − level` with nothing to cancel it. That is bpa's business").

6. **Verdicts.** One formulation is admissible under `#56` and answers the bench question
   (season objective over the schedule, formulation B); it introduces no magnitude and its bench
   component is small and honest. One is admissible and is not a bench valuation but a repair to
   the reference object both the shipped price and B stand on (cap each slot's free alternative at
   the best remaining eligible player — an exact bound, formulation C). Two need a chosen
   magnitude and belong above the core (single-absence insurance A; anything with an injury rate).
   None of them needs a third backstop, and B makes `unfieldable_last` provably redundant for the
   nine-defense case without a ceiling.

---

## 0. Fixture, provenance, and what was run

- Capture: `data/fixtures/sleeper_capture.json` (season 2026, captured 2026-09-07, 6,595 players,
  `build_players_db_from_capture`), season projections from the same capture priced under the
  capture's own `scoring_settings` with `SLEEPER_BASIS_SEASON_SUM`, `set_league_format` called from
  `league_format_hint`. **The capture carries no weekly lines** (`weekly_projections_from_capture`
  → `{}`), so `#30`'s streaming floor is *not* on this board (K 121.78, DEF 107.95 are the
  rank-based levels) and no weekly-churn quantity could be measured here.
- Arm: `12T_ppr_K_DEF` from `league_matrix`, 16 rounds, roster
  `QB RB RB WR WR TE FLEX FLEX BN×6 K DEF`, `mode="auto"`, `UPSIDE_RULE_ROUND`, every seat sharp
  (`opponent_noise=None`), drafted with `simulate_full_draft` — the production pricing path.
  821 s. Raw picks dumped before any derivation.
- Replay: boards rebuilt with `compute_draft_board` from `picks[:idx]` in production's pick shape
  (`pick_no, round, roster_id, player_id`), `replacement_levels` spied and tagged from its
  arguments, the roster priced through `roster_points_lookup` + `_team_roster_points_players`
  (what the displacement term itself sees), byes from `merger.bye_week_by_team()` (32 teams,
  weeks 5–14, 0 conflicts).
- Probes: `d35_draft.py`, `d35_analyse.py` in this session's scratchpad
  (`/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-…/scratchpad/`), outputs
  `d35_raw.json`, `d35_analyse.txt`, `d35_result.json`. Not committed; they are ordinary
  measurement scripts and can be moved under `evidence/` if the owner wants them kept.

**The documented state reproduces to the cent.** Seat 5, round 14, pick 164: AJ Barner
`projected_points 179.46, bpa +28.02, final −20.21`; Rashid Shaheed `170.24, −46.01, −38.28`. The
pathology in `DESIGN_35_BENCH_VALUE.md` is this fixture's, so what follows is the same pick, not
an analogue. Roster shapes of the run: five chairs with 3+ tight ends (seats 1, 2, 3, 5, 10),
seat 5 with **five**; every chair with two kickers; eight chairs with two defenses.

---

## 1. The mechanism, in code paths

### 1.1 Two anchors of different kinds

At pick 164 `replacement_levels` (tag `LIVE(_points, remaining pool)`) returned only
`{RB: 165.82, TE: 151.44}`. Every other position's starter demand was below one whole slot, so it
was OMITTED (correctly, per its domain) and `_fill_omitted_from_anchor` filled it from
`predraft_replacement_anchor`: WR 216.25, QB 328.6, K 121.78, DEF 107.95, basis `predraft_anchor`.

| position | level used | basis | best player still on the board |
|---|---:|---|---:|
| TE | **151.44** | live starter demand | 179.46 (Barner) |
| WR | **216.25** | pre-draft anchor | 173.00 |
| RB | 165.82 | live starter demand | 176.98 |

The TE level is a player who exists (the rank-N remaining tight end). The WR level is a player who
does not: it is 43.25 points above the best receiver anyone can still draft. `displacement_level`'s
docstring records this staleness ("the level said a free tight end was worth 149.17 while the best
one left in the pool was worth 6.49") and argues it does not reach the price *where the term is
non-zero*. Correct — and the WR is exactly where the term is zero.

`bpa` is then `points − level`: Barner `179.46 − 151.44 = +28.02`, Shaheed `170.24 − 216.25 =
−46.01`. Of the 74.03-point swing, **64.81 is the level gap and 9.22 is projection.**

### 1.2 The FLEX phantom is the stale anchor

`shared_slot_alternatives` prices every slot at `max(level(p) for p in slot.eligible)` — one
slot, one alternative, deliberately the *best* free thing. For both FLEX slots that maximum is the
WR level, 216.25. So `displacement_level` solves seat 5's roster against phantoms of:

```
QB 328.6 | RB 165.82 RB 165.82 | WR 216.25 WR 216.25 | TE 151.44 | FLEX 216.25 FLEX 216.25 | K 121.78 | DEF 107.95
```

Seat 5's roster in projected points: Nacua 389.4, Prescott 344.5, Hampton 280.5, McMillan 264.3,
K. Williams 263.7, Watson 254.3, Deebo Samuel 197.8, Ferguson (TE) 190.3, J. Johnson (TE) 189.3,
Likely (TE) 184.7, Eagles DEF 127.1, Little K 123.6, Folk K 121.4.

The base solve seats Watson in FLEX_6 and **the 216.25 phantom in FLEX_7**, benching Deebo
(197.8) and Johnson (189.3), because the solver maximises total value and a fictional 216 beats
a real 198. The engine's picture of this roster has a free receiver it can never obtain starting
in its second flex.

### 1.3 Two probes, two reference objects

`displacement_level` adds a probe worth 1e6 at the candidate's position and reads off what it
evicts — the cheapest occupant of any reachable slot.

- **TE probe** reaches TE_5 (Ferguson 190.3), FLEX_6 (Watson 254.3), FLEX_7 (phantom 216.25).
  Cheapest: Ferguson. `displaced = 190.27`, `adjustment = 151.44 − 190.27 = −38.83`.
  Price: `bpa + adj = 179.46 − 190.27 = −10.81`.
- **WR probe** reaches WR_3 (Nacua), WR_4 (McMillan), FLEX_6 (Watson), FLEX_7 (phantom 216.25).
  Cheapest: the phantom. `displaced = 216.25 = level`, `adjustment = 0.00`.
  Price: `170.24 − 216.25 = −46.01`.

So `bpa + displacement_adj` is `points − displaced` for both — the algebra the docstring gives —
and `displaced` is **my own TE1** for one and **a receiver who will never exist** for the other.
The whole 35.2-point gap after displacement is 9.22 of projection plus 25.98 of "Ferguson versus
the phantom". Barner's final of −20.21 adds `time_horizon_adj −10.00` (dynasty clamp) and
`depth_exposure +0.60`; Shaheed's −38.28 adds `time_horizon_adj −2.47` and `depth_exposure
+10.20`. The team-specific terms move the pair by 8.7 in Shaheed's favour and cannot span it.

This is per-position, not per-candidate: at this state `displacement_adj` is **0.00 on all 145
WR rows, −38.83 on all 98 TE rows, −50.43 on all 94 RB rows, −19.12 on all 12 DEF rows.** The
term cannot tell a receiver who would start over Deebo from one who would not, because the
phantom sits above both. That is the `MECHANISM.md` observation — "the position whose level is
the MAXIMUM escapes this entirely" — seen from the candidate's side.

### 1.4 Why a deficit cannot rank bench bodies

`points − displaced` is the marginal value of the candidate in ONE lineup with NO absences, allowed
to go negative. For a body who does not start it is a distance, not a value: it says how much
better he would need to be to start today. Two distances to two different objects carry no
information about which body contributes more over a season, which is a question about the weeks
one of the roster's starters is *not there*. The engine's objective contains no such week. The only
absence-shaped terms it has are `need_bonus` (roster state, capped at 12.0, and zero here) and
`depth_exposure` (a capped nudge in trade_value units: +10.2 for Shaheed, +0.6 for Barner —
correctly ordered, and swamped), and both are bounded nudges set against an unbounded deficit.

**The nine-defense case is the same arithmetic at a flat position.** Every defense sits within
12 points of the DEF level, so its deficit against my own DEF1 is small (−19.12 here, −6.65 in the
2024 record). The WR tail's deficit against the 216.25 phantom is large. On this very board, at
pick 164, **rows 4–6 of the production order are three defenses** (Buccaneers −27.84, Chargers
−29.22, Panthers −29.39) ahead of the best remaining receiver (−38.28). Seat 5 avoided a second
defense only because four tight ends outranked them. Positions are exchanged; the defect is one.

### 1.5 The pick before: where the phantom changes the answer, not just the reason

Seat 5, round 12, pick 140 — before its **third** tight end. Roster then: the same starters,
TE Ferguson 190.3 and Johnson 189.3, no fourth receiver. Levels: TE 172.69 (live), RB 176.98
(live), WR 216.25 (pre-draft anchor; best remaining WR 197.8, best remaining RB 202.36).

| candidate | pts | bpa | disp | final | evicts | signed price | real FLEX_7 occupant is Johnson 189.3, so … |
|---|---:|---:|---:|---:|---|---:|---|
| Isaiah Likely (TE) | 184.73 | +12.04 | −17.58 | **−12.84** | Ferguson 190.3 | −5.54 | does not start; single-lineup marginal **0.00** |
| Jakobi Meyers (WR) | 194.53 | −21.72 | 0.00 | −23.38 | phantom 216.25 | −21.72 | **starts over Johnson: +5.22** |
| Rhamondre Stevenson (RB) | 202.36 | +25.38 | −39.27 | −23.22 | phantom 216.25 | −13.89 | **starts over Johnson: +13.05** |

(Marginals from `optimize_lineup` on the same roster with the FLEX phantom removed —
"empty_wire" world in §3.) The engine took Likely. Two candidates who would have started that
week on the roster's own objective were ranked below one who would not, and the only thing
separating them is a 216.25 phantom in a slot a 189.3 tight end actually occupies.

### 1.6 Upside mode, for completeness

Round 15 (pick 173) is upside mode: every team term is zero, `final_score = bpa + 0.5·growth`. The
TE live level had fallen to 137.73, so Gunnar Helm (151.44) carried `+13.71` and was taken as the
**fifth** tight end over Kenny Gainwell RB (+11.16); the best remaining WR (173.0) sat at −43.25
against the same 216.25 anchor. Helm's roster-global value is 0 in every world of §3. This is the
already-recorded open contract question (what upside mode is meant to drop), stated here only so
the five-TE roster is attributed correctly: four came from the mechanism above, the fifth from the
mode switch removing even the deficit's partial correction.

---

## 2. Why `displacement_adj` does not already fix it — mechanically

It is the closest thing to the answer, and it is worth being exact about what it does and does not
reach.

1. **It cancels the level only where every reachable slot is held above the phantom.** Then
   `bpa + adj = points − my weakest reachable starter`. That is a correct one-week marginal for a
   candidate who would *start*; for one who would not, it is a deficit (§1.4).
2. **It returns exactly 0.0 where any reachable slot is phantom-held**, and the phantom is
   `max(level)` over the slot's eligible positions — at every flex, the stale pre-draft WR anchor
   once WR demand is exhausted (round 9 or so in this format). From then on every WR row is priced
   `points − 216.25` with nothing cancelling it, and every RB/TE row that reaches a flex is priced
   against my own starter. The docstring names this: "the ~30-point half of the tight-end bias
   that survives this term today, because the term reports exactly 0.0 whenever a slot is merely
   OPEN". The slot is not open. It is held by a fiction.
3. **It has no absence model.** It is one solve of one lineup. A fourth tight end and a fourth
   receiver both have marginal 0 in that lineup; the term's job is to correct the *anchor*, and
   it does that, but the residual it leaves (`points − displaced`) is not a bench valuation and
   was never claimed to be one.
4. **It is per-position constant at a board state** (0.00 × 145 WR rows, −38.83 × 98 TE rows here),
   so it cannot separate candidates within a position by whether they would displace anyone real.
5. **For the defense case the deficit is small because the position is flat**, so the correction
   is small (−6.65 / −19.12). A small correction on a small over-credit still leaves a flat-tail
   defense ahead of a deep-tail receiver, because the receiver's deficit is measured against the
   phantom. `unfieldable_last` is what stops it, and only where there is no flex reach.

---

## 3. Candidate formulations of a roster-global bench value

All four were computed on seat 5's actual roster at the two states above, with the engine's own
`optimize_lineup`, `slots_from_roster_positions` and `displacement_level`'s pinned-phantom
construction (no second solver, `#126`). Because §1 showed that every such quantity depends on
what stands in an unheld slot, each was run in four **phantom worlds**:

| world | phantom in each slot | status |
|---|---|---|
| `level` | `shared_slot_alternatives(levels)` — the engine's own | shipped |
| `level_capped_by_pool` | `min(level alternative, best remaining eligible player)` | exact bound, no constant |
| `best_remaining` | best remaining eligible player | exact bound, no constant (vacuous for the top candidate at his position, by construction) |
| `empty_wire` | 0 — nothing is free | upper bound on any bench value |

### Formulation E — literal roster-slot opportunity cost

*What:* value = points − (best available player at any position). *Inputs:* the board. *Constant:*
none. *Barner/Shaheed:* a common constant subtracted → ranks by raw projection → **Barner**,
by 9.22. *Nine defenses:* a 121-point defense loses to every skill player above 121, so it helps
there, but only because defenses project low, not because they cannot be fielded.

*Verdict:* admissible under `#56` and **wrong** on the question's own example. It is what the
"any position" framing literally computes, and it is a useful negative result: the positional
anchor is not the whole disease. Removing it leaves a ranking with no fieldability content at all.

### Formulation A — single-absence insurance (the candidate side of `depth_exposure`)

*What:* `A(c) = Σ over my real starters s of [L(R − s + c) − L(R − s)]` — what the candidate covers
in each one-starter-out scenario; `A_max` is the single worst hole he covers. *Inputs:*
`_my_points_players`, the slots, phantoms — all exist; it is `depth_exposure`'s re-solve with the
candidate added. *Constant:* the *quantity* introduces none. **Commensurability does:** to add it
to a starter's one-week marginal you need P(absence) — a per-position injury rate the app does not
have (`depth_exposure`'s own docstring: "inventing 'RBs get hurt 1.4x more than WRs' would be
exactly the kind of unmeasured constant that has already had to be removed") — or a weight, which
is `#56`.

Measured, pick 164, seat 5:

| candidate | `level` | `capped` | `best_remaining` | `empty_wire` |
|---|---:|---:|---:|---:|
| Barner TE | 0.00 | 0.00 | 0.00 | **0.00** |
| Shaheed WR | 0.00 | 0.00 | 0.00 | **0.00** |
| Price RB (top RB row by final_score) | 10.44 | 10.44 | 0.00 | 342.08 |
| Buccaneers DEF | 0.00 | 0.00 | 0.00 | 99.23 |

Barner and Shaheed insure **nothing** in any world, including the one where the wire is empty:
Deebo (197.8), Johnson (189.3) and Likely (184.7) cover every single absence before either of them
is reached. The RB has a small real number because the RB level (165.82) is below him and both RB
slots are held far above it. The defense's 99.23 under `empty_wire` is a dedicated slot with no
cover and no wire — the case that genuinely needs a rate, and where `#30`'s streaming floor is the
honest wire.

*Nine defenses:* DEF2 insures DEF1's absence (once), DEF3+ insure nothing — A is exactly 0 for the
third defense onward without any ceiling. *QB4 in superflex:* the same shape; the fourth
quarterback's A is 0 unless three quarterbacks are out.

*Verdict:* **inadmissible as a core value term** — it needs a chosen magnitude to sit beside a
starter's marginal. **Admissible as an observable**, the way `bye_collision` was shipped:
"this body covers no single absence on your roster" is a derived, constant-free fact, and it is
the fact the owner wants to see next to a fourth tight end. It is the primitive an explicit
roster-preference layer would weight, which is where `UPGRADE_EXEMPTION.md` already says that
layer belongs.

### Formulation B — the season objective over the schedule

*What:* `V(P) = Σ over weeks w of L_w(P)`, where `L_w` is the best lineup that week from the
rostered players **not on bye that week**, plus a phantom in every slot for what the wire
offers; candidate value `= V(R + c) − V(R)`. With no weekly lines in the capture, a player's week
is `season / 17` in his 17 non-bye weeks and 0 in his bye; phantoms are `alternative / 17` every
week (the wire has no bye). *Inputs:* the roster in points (exists), byes (`bye_week_by_team`,
exists, 99.1% coverage), slots, alternatives (exist), the week set (a league fact —
`playoff_week_start` on a real league; this probe used the full 18-week schedule). *Constant:*
**none chosen.** The 17-game split is the same games-played fact `SLEEPER_WEEKLY_TO_SEASON_FACTOR`
already carries (and its docstring already flags as an assumption); it is what the weekly lines
replace the moment a capture carries them, on `#30`'s existing path.

What B *is*: for a candidate who starts, B is his one-week marginal × 17 = exactly today's
`points − displaced` (so B **contains** the shipped starter price as its no-absence limit); for a
candidate who does not, B is his bye coverage — the weeks the schedule forces a hole he is the
best body to fill, priced against the wire. That is the replacement unit the question asks for,
stated as an objective rather than as an anchor.

Measured, pick 164, seat 5 (season-point units):

| candidate | `level` | `capped` | `best_remaining` | `empty_wire` (which week) |
|---|---:|---:|---:|---:|
| Barner TE | 0.00 | 0.00 | 0.00 | **10.56** (wk 8: Deebo, Johnson, Likely all on bye) |
| Shaheed WR | 0.00 | 0.00 | 0.00 | **10.01** (wk 8, same hole) |
| Price RB | 0.30 | 0.31 | 0.00 | 20.13 |
| Buccaneers DEF | 0.00 | 0.00 | 0.00 | 0.00 (its bye collides with the Eagles') |
| Kyler Murray QB | 0.00 | 0.00 | 0.00 | 17.98 (wk 14, Prescott's bye) |

**The roster objective is indifferent between Barner and Shaheed** — identical in three worlds
and 0.55 apart in the fourth, and that 0.55 is Barner's 9.22 extra points spread over one week
of a hole they would both fill. There is no roster-global bench value on which Barner is 18 points
better; there is none on which Shaheed is, either. A fourth bench body on a roster that already
has three better ones is worth its share of one collided bye week, at most.

Measured, pick 140 (the TE3 state), `empty_wire`: Stevenson RB **57.61** (of which 13.05 is
starting every week), Meyers WR **49.79** (5.22 starting), Likely TE 32.58 (0 starting, three
bye weeks of cover). Under the exact bounds all three are 0 — the lower bound is vacuous at the
top of a position, by construction (best-remaining phantom equals the best-remaining candidate).

*Nine defenses:* with the streaming floor (146.05 in 2024) as the DEF slot's wire, DEF2's bye
cover is `(DEF2 − wire)/17 < 0 → 0`, and DEF3+ can never enter a week (one slot, one bye). **B
prices the entire hoard at 0 with no ceiling and no constant**, which is the "does a correct
roster-global valuation make `unfieldable_last` redundant" check `DESIGN_35_BENCH_VALUE.md` asks
for — answered yes for that case, provided the wire is the streaming baseline, which is already
derived. Without weekly lines (this capture) the DEF wire is 107.95 and DEF2 is worth
`(99 − 108)/17 → 0` anyway. *QB4 in superflex:* a fourth quarterback enters a week only when two
of the other three share a bye; B is 0 or one week's `(QB4 − wire)/17`, which is a number, not a
tie. The +0.40 / +5.55 / +2.18 margins the record calls "effectively tied" become a derived
decision either way.

*Verdict:* **admissible under `#56`.** It introduces no magnitude, uses one solver, and turns the
starter price and the bench price into one quantity. Two honest limits: (i) it inherits the phantom
problem — under the engine's own alternatives it is 0 for everyone, because a 216.25 receiver is
assumed free in every absence week; it only says anything once the phantom is bounded (C) or is the
wire (`horizon_replacement` / `#30`); (ii) it prices only *scheduled* absence. That is a design
commitment the engine already states ("does not independently value surplus roster slots for …
insurance … unless those preferences are explicitly modelled"), and B makes it exact rather than
implicit: injury insurance is worth `P(injury) × A`, and the engine does not own `P`.

### Formulation C — bound the reference object (not a bench valuation)

*What:* leave `bpa`'s anchor alone; in `board_slot_alternatives` (the seam that already exists to
be patched), cap each slot's alternative at the best remaining player eligible for that slot:
`alt(slot) = min(max level over eligible, max remaining points over eligible)`. *Why it is a
bound and not a choice:* the pool only drains, so no free player at draft end can be worth more
than the best one undrafted now. *Constant:* none. *Inputs:* the board already has both numbers.

Measured effect on the two states (signed price `points − displaced`, single-position probe):

| state | candidate | shipped | capped | what changed |
|---|---|---:|---:|---|
| pick 140 | Likely TE | −5.54 | −5.54 | still against Ferguson |
| pick 140 | Meyers WR | −21.72 | −7.83 | against the capped FLEX phantom (202.36 = the best remaining RB), no longer the 216.25 fiction |
| pick 140 | Stevenson RB | −13.89 | **0.00** | ties the capped phantom, which is himself: **now outranks the TE3** |
| pick 164 | Barner TE | −10.81 | −10.81 | still against Ferguson |
| pick 164 | Shaheed WR | −46.01 | **−27.56** | against Deebo 197.8, a real occupant, for the first time |

At the TE3 pick C flips the order to the roster's own answer; at the TE4 pick it halves the gap
and leaves both bodies as deficits (Barner is 10.8 short of unseating his TE1, Shaheed 27.6 short
of unseating Deebo). C repairs *which object* a deficit is measured against. It does not make a
deficit a bench value, and it must not be sold as one.

*Hazard, stated before anyone measures it:* capping at the best remaining player is the same
quantity whose use *as a level* produced the "rank-1 collapse" (every position's best remaining
priced at 0, cross-position order destroyed) that `predraft_replacement_anchor` was built to
avoid. C applies it to the **slot alternative in the displacement solve only**, never to `bpa`;
the cross-position number line stays the pre-draft anchor's. Whether that distinction holds up
across formats is exactly what the `#216` pre-registered gates (18 drafts, nine gates, the
two-sided over-correction guard) exist to test, and this seam was made patchable for that harness.

*Verdict:* **admissible under `#56`**, one seam, no new vocabulary, and it is the precondition for
A and B to say anything at all. It is an anchor-staleness repair that happens to be necessary
for `#35`, not `#35`'s answer.

### The frame, then

The replacement unit for a bench player is **the wire, in the weeks the schedule (and only the
schedule, in the core) puts him in the lineup.** VOR's positional level is the right unit for a
slot held all season, and it is what a bench body is *not*. So "change VOR's replacement level
for bench players" is not the shape of the answer: a bench body should not have a level at all;
he should have an objective, and B is the objective with the shipped starter price as its
no-absence limit. Whether the engine adopts the objective, or only publishes A as an observable
beside today's price, is the owner's call.

---

## 4. Verdict table

| formulation | computes | new inputs | chosen magnitude? | Barner vs Shaheed | nine DEF | admissible? |
|---|---|---|---|---|---|---|
| E literal opportunity cost | points − best anywhere | none | no | **Barner** by 9.2 | helps by accident | constant-free, wrong answer |
| A single-absence insurance | Σ cover over one-starter-out | none | **yes**, to compare with a starter | 0 = 0 (both insure nothing) | DEF3+ = 0 | observable only; value needs a rate → preference layer |
| B schedule objective | Σ_weeks best lineup, byes out, wire phantoms | week set (league fact) | no | 0 = 0, or 10.56 ≈ 10.01 | 0 with the streaming wire; no ceiling needed | **yes**; needs a non-fictional wire (C or `#30`/horizon) |
| C capped alternative | min(level, best remaining) per slot | none | no | −10.8 vs −27.6 (both deficits) | unchanged | **yes**; a repair, not a bench value |
| any injury-rate model | P(absence)·A | a rate | **yes** | — | — | product/preference layer |

---

## 5. What would falsify the preferred formulation, and the cheapest measurement

Preferred: **C as the reference-object repair, B as the objective**, and A published as an
observable rather than priced.

**Falsifiers for C** (one seam, `board_slot_alternatives`, already patchable in-process):

1. *It re-opens the collapse.* If, with the cap on, the pre-registered `#216` over-correction
   guard fires (a seat fielding zero tight ends in the owner's three-flex league, or a
   four-TE seat in `12T_ppr`), or lineup points fall on the 18-draft harness, the cap is reaching
   the cross-position ordering it is not supposed to touch.
2. *The hoard is not the phantom's doing.* If `12T_ppr_K_DEF` sharp, with the cap on, still
   produces ≥3 tight ends on 5 of 12 chairs, the deficit comparison alone is sufficient for the
   hoard and C is necessary but not the lever.

Cheapest: re-run this one arm (821 s) with `dr.board_slot_alternatives` patched to the capped
form, `reset_anchor_caches()` at the arm boundary, and compare `roster_shape` and
`roster_strength` against the run recorded here. One process, one toggle. Pre-register the two
outcomes above before running it.

**Falsifiers for B:**

1. *The bench component is not small in practice.* B says a fourth bench body is worth one
   collided bye week. If, on the 2024 backtest (which has weekly lines and realized outcomes),
   `realized_ruler`'s oracle lineup draws the fourth-best bench body into a lineup in materially
   more than the bye weeks — i.e. injuries dominate byes — then the schedule-only objective is
   pricing the smaller half of bench value, and the owner should know the size of the half it is
   not pricing. Cheapest: on the 2024 seat records already in `evidence/kdst_streaming/`, count
   per roster the weeks in which the oracle lineup used a body outside the top three bench values,
   split bye / non-bye. That is a count, not a run.
2. *Flat weekly split misorders positions.* If real weekly lines (when a capture carries them)
   make B's bench ranking disagree with the flat-split ranking on the same rosters at a rate
   comparable to the ranking gaps themselves, the flat split is a modelling error rather than a
   placeholder. Cheapest: `sleeper_weekly_2024.json` against the 2024 rosters, B both ways, count
   pair reversals among pure-bench picks.

**What would falsify the whole frame:** a roster on which A or B ranks a candidate above another
that a human drafter would call obviously worse *for a reason the engine can state* — the way the
Geno Smith 2.4-point "upgrade" falsified the exemption. The measured cases here do the opposite
(indifference where the engine was decisive); a case of decisiveness in the wrong direction is what
to look for first.

---

## 6. What I could not determine, and why

- **Whether the five-tight-end roster costs realized points on this fixture.** It is a 2026
  capture with no outcomes. The 2024 backtest has outcomes but a different player universe, so the
  two documents' numbers are not the same draft even where they look alike (the K 121.78 / DEF
  107.95 levels coincide across the two seasons' records; I did not chase why).
- **Whether weekly-projection churn makes bench bodies worth more than the flat split says.** No
  weekly lines in the capture. The module's own measurement (`STREAMABLE_POSITIONS`) found the
  week-max premium at RB/WR to be winner's-curse noise, which is why B here uses the flat split
  and treats weekly lines as a replacement input, not a modelling upgrade to assume.
- **Whether C survives the format matrix.** One arm, one seat, two states. The `#216` harness is
  the measurement; it was not run (five hours, and it is a proposal, not a repair).
- **The superflex QB4 case.** Predicted by §1 (a fourth quarterback's deficit is against my QB2
  in SUPER_FLEX, a real object; the alternative skill player's is against a phantom), not measured
  — different arm.
- **How the pre-draft anchor should compose with a live pool** in general. C bounds one use of it.
  The `SUPER_FLEX_QB_SHARE` note already records that the floor and the demand model "answer the
  same question and override each other"; the stale-anchor-at-FLEX finding here is a third
  instance of two anchors for one slot, and I have not tried to unify them.
- **Whether A as an observable would change what the owner does.** That is a product question.
  Its cost is one solve per rostered starter per candidate row at the top of the board, which is
  affordable; its value is that "this body covers no single absence" is the one sentence the
  fourth tight end's row is missing.
