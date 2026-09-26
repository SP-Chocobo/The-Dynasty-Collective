# The gate on restarting the VDS battery — fixed BEFORE the shipped A/B was read

Owner: *"i agree, restart, provided the results are what we want."* That is a conditional
authorisation, and the condition is the shipped-vs-no-cap grade
(`shipped_cap_ab.py`). Written and committed **before either `shipped` arm reported**, because a gate
chosen after the number is not a gate.

The pairing is `shipped − cap_off` per seat, realized ruler, 12 seats, `12T_ppr_K_DEF`, both seasons.
`cap_off` has already reproduced the known pre-`#35` baselines exactly on both (2024 11/12 +82.9,
2023 4/12 −49.9), so the reference is sound.

## What launches the battery

**Positive on BOTH seasons, with a majority of seats improved on each.** Then `#35` pays on the
composition that actually ships, the freeze rests on a real number, and the open question becomes the
one the owner asked: does it draft well on a varied field. **Restart all 36 arms against the frozen
commit** — not a resume, because the existing 13 predate C′, the `absence_kind` repair and the
`draft_counterfactual` fix, and pairing new arms against stale ones is the rule this repo states as
"never resume onto a report written by different code".

## What does NOT launch it

- **Negative on either season.** Then the shipped composition is worse than the one graded, and the
  next decision is REVERT-OR-ADOPT — revert `#35`, or adopt the measured composition and re-certify —
  not a three-hour battery on a configuration that may not survive. Goes to the owner.
- **Indeterminate**, both seasons inside ±25 points per seat. By the same reading `#35`'s own
  pre-registration fixed, a change with a known cost and no measurable benefit is retired as "no
  measured benefit", not shipped on "no measured harm". Also a revert-or-adopt decision, not a
  battery.
- **`cap_stats.levels_capped == 0`** in either `shipped` arm. Then the arm is `cap_off` wearing
  another name and the comparison is vacuous regardless of what the totals say.

## What the battery would and would not settle

It answers **"does the frozen engine draft well on a varied field, meeting or beating raw BPA and the
sane-style chairs"** — the bar the owner set for the K/DST work and the one thing the realized-outcome
grader cannot see, because it fields a fixed two-style table. It does **not** re-answer whether `#35`
pays; that is this A/B's job, and the battery must not be read as a second opinion on it.

---

# AMENDMENT — the battery does NOT run at the frozen commit, and why

Recorded before any arm reported, and recorded because the gate above says "restart all 36 arms
against the frozen commit" and **that is not what happened**.

## What changed after the gate was written

The battery was launched at the frozen commit `43c8188` and **stopped ~20 minutes in**. The owner
asked whether an open item would invalidate it, and checking that surfaced a different problem:
`run_vds_battery` records `streaming_floor_exercised`, and it was **False**.
`weekly_projections_from_capture()` returned `{}`, so **`#30`'s streaming floor was derived for none
of the 36 arms** — the battery was grading the engine with its own K/DST repair missing, which is
precisely the behaviour the "meet or beat, no draft-quality drop-off" bar was set to police.

The remedy `weekly_projections_from_capture`'s docstring named was "re-capture", which needs the
Sleeper API and is denied by this environment's network policy. It was also unnecessary: the
per-week lines for the capture's **own season** were on disk (`capture_weekly_lines`, 18 weeks for
2026, the season the capture declares). The gap was **wiring**. Fixed at `04bccb5`, vintage-matched
with the season read from the capture rather than chosen.

## So the battery runs at `04bccb5`, one commit past the freeze

| | |
|---|---|
| frozen commit | `43c8188` |
| battery commit | `04bccb5` |
| what differs | 13 paths, of which 2 are `.py` and NEITHER is engine code: `run_draft_battery.py` (the battery's data loader) and `evidence/design_35/shipped_cap_ab.py` (an instrument) |

**No engine or scoring code differs between them.** Measured rather than asserted:

```
$ git diff --name-only 43c8188 04bccb5
DOC_INDEX.md
FREEZE_RECORD_V2.md
POST_AUDIT_PLAN.md
evidence/design_35/GATE_FOR_VDS.md
evidence/design_35/RESULT_UV_CONSUMERS.md
evidence/design_35/runs_shipped/SUMMARY_2023.json
evidence/design_35/runs_shipped/SUMMARY_2024.json
evidence/design_35/runs_shipped/cap_off_2023.json
evidence/design_35/runs_shipped/cap_off_2024.json
evidence/design_35/runs_shipped/shipped_2023.json
evidence/design_35/runs_shipped/shipped_2024.json
evidence/design_35/shipped_cap_ab.py
run_draft_battery.py

13 paths; .py files: evidence/design_35/shipped_cap_ab.py, run_draft_battery.py
```

Neither `.py` is engine or scoring code: one is the battery's own weekly-lines loader, the
other an instrument added under `evidence/`. Everything else is a document, an arm report or
the doc index.

(I wrote "is one file" here, ran the command I had just cited, corrected it to "14 paths,
exactly one .py" -- and that was wrong too. It is 13 paths and 2 .py files. Enumerated from
the command's own output above rather than from memory, because the commit relationship is
the entire point of this section and I had already got it wrong twice.)

So the ENGINE the battery grades is the frozen engine;
what changed is that the harness now feeds it the weekly lines the live path feeds it, which is what
makes the grade about the shipped configuration instead of a subset of it.

Stating it plainly because the alternative is a report whose commit line quietly disagrees with the
freeze and a reader who has to work out why.

## What this changes about the reading

Nothing in the launch gate — that was about the shipped A/B and it was cleared on its own terms
(+21.70 and +43.69 a seat, 9 of 12 and 8 of 12 seats improved). What it changes is **what a green
battery would now license**: before the fix, 0 of 36 arms exercised `#30`; after it, **6 of 36 do**
(`12T_ppr_K_DEF` × six strategies — the only one of the six formats carrying K and DEF roster slots).
The other 30 arms have no such slots and the floor correctly does not bite there.

So a clean battery now speaks to A + `#35` + `#30` on the formats where each can fire, rather than to
A + `#35` with `#30` invisible. That is a stronger statement than the run I stopped would have
supported, and it is the reason stopping was worth 20 minutes.
