# The mechanism, on the live board: the shipped phantom DOUBLE-COUNTS, and the shared one cancels

*#216 / #221. `bench_probe.py` / `bench_probe.txt` — 12T_ppr_SF seat 1, both arms, rounds 10 and 13,
every term decomposed, plus the best remaining body at every position.*

## Round 10, the first pure-bench pick

| arm | candidate | proj | bpa | displacement | FINAL |
|---|---|---|---|---|---|
| SELF (shipped) | WR Courtland Sutton | 199.7 | 0.0 | **−10.3** | −10.5 |
| SELF (shipped) | RB Tony Pollard | 186.3 | 20.5 | **−99.4** | **−89.0** |
| SELF (shipped) | TE Isaiah Likely | 184.7 | 22.1 | **−102.6** | **−88.0** |
| SHARED | WR Courtland Sutton | 199.7 | −15.4 | **0.0** | −16.4 |
| SHARED | RB Chuba Hubbard | 185.6 | 19.8 | **−49.2** | −38.7 |
| SHARED | TE Juwan Johnson | 189.3 | 26.7 | **−52.4** | −32.7 |

Read the two arms as differences rather than levels.

**SHARED cancels exactly.** TE nets `26.7 − 52.4 = −25.7`; WR nets `−15.4 + 0.0 = −15.4`. The gap
is **10.3**, and the raw projection gap is `199.7 − 189.3 = 10.4`. The league anchor goes in
through `bpa` and comes straight back out through the displacement term, leaving projection. That
is what "one slot, one alternative" means, arithmetically, and it is the whole content of the
change.

**SELF does not cancel — it double-counts.** TE nets `22.1 − 102.6 = −80.5`; WR nets `−10.3`. The
gap is **70.2** for the same ~15-point projection gap: a ~55-point penalty on top of the
arithmetic. The reason is structural and is now measured rather than argued. `bpa` already prices
a candidate against his OWN positional level. The shipped phantom then prices the SLOT against
that same level too. So a position whose rostered starters sit far above its own (low) league
level is charged for its own quality a second time — Brock Bowers and Colston Loveland make every
further tight end look 100 points worse, and Gibbs/Cook/Hampton do the same to every further
running back. Meanwhile WR's own level (215.1, the maximum here) sits ABOVE the receivers actually
rostered, so the WR phantom is still the weakest occupant of a WR slot and WR is barely deducted
at all.

**That is the "max-level position is never deducted" mechanism — and it belongs to the SHIPPED
engine, not to the shared alternative.** I recorded it against the wrong arm in DIALLED_IN.md §4.
It is also, exactly, why the shipped bench is 46 receivers out of 48.

## Round 13, and the reversal of a recommendation I had pending

| arm | rank | candidate | disp | depth_exposure | FINAL |
|---|---|---|---|---|---|
| SELF | 1 | WR KC Concepcion | 0.0 | 1.0 | −50.2 |
| SELF | — | RB Croskey-Merritt | −110.5 | 7.3 | **−104.1** |
| SHARED | 1 | WR KC Concepcion | 0.0 | 2.0 | −49.1 |
| SHARED | **2** | **RB Croskey-Merritt** | −60.3 | **9.6** | **−50.9** |
| SHARED | 4 | RB Jonathon Brooks | −60.3 | 9.6 | −52.6 |
| SHARED | 5 | TE T.J. Hockenson | −66.6 | 6.5 | −55.2 |

Under SHARED, running backs and tight ends hold **six of the top eight rows**, and the margin
between the receiver and the running back is **1.8 points**. `depth_exposure` reads RB 9.6,
TE 6.5, WR 2.0 — the insurance signal, correctly ordered, and large enough at this margin to
decide the pick. Under SELF the same term reads 7.3 for the same running back and is swamped by a
110-point displacement.

**So the `depth_exposure` demotion is DECLINED.** DIALLED_IN.md §3 recorded "SHARED +
`depth_exposure` demoted" as the best arm on band breaches (18 vs 19) and ordering (8/9 vs 7/9).
That is a one-breach difference over nine seats, and this dump shows the term doing precisely the
work the change needs done at precisely the state where the roster shape is decided. A
one-of-nine aggregate gain is not evidence against a term measured working at the margin; it is
inside the noise of the sample that produced it. The demotion is not carried, and the reason is
recorded here rather than left as a silence.

`depth_exposure` only becomes legible once the anchor stops shouting. That is an argument for the
shared alternative, not against #139.
