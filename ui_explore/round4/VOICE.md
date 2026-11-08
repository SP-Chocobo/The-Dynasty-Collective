# The voice

## One sentence

**The app wants nothing from you.**

It keeps the ledger. It reports what it knows, names what it does not, and gets out of the way.

That is the whole specification. Everything below is derived from it, and any copy question not
answered below should be settled by asking which reading wants less from the reader.

## Why this and not something else

Every other product in this category performs confidence it has not earned — team ratings,
playoff odds, letter grades, "you're crushing it". This engine withholds `survival_probability`,
withholds `estimate_future_pick_value` at 1.89 slots of error, excludes Questionable because it
measured the designation as carrying nothing, and renders an absence as an em dash with its
reason rather than a zero.

That restraint is not a limitation the copy has to work around. **It is the only thing here no
competitor can say**, and the voice exists to make it audible.

The failure mode this replaces: `NEEDS YOU` in letterspaced gold caps over heraldry is a
recruiting poster. It summons. A page whose entire thesis is that you should be able to close it
must not open by demanding your attention.

## The rules

1. **Indicative, never imperative.** It states; it does not instruct.
   *Week 6 costs 95.* — not *Review week 6.*

2. **The app is never the subject.** No "we", no "needs you", no "I found". The subject is the
   week, the roster, the position, the pick. The app has no first person and makes no requests.

3. **Never flatter.** No "All systems green", no "You're crushing it", no congratulation. A clean
   week is a fact, not a compliment, and the reader did not necessarily earn it.

4. **Every figure carries its basis.** `measured` / `≥ floor` / `constructed` / `— absent, with
   its reason`. Four states, visually distinct, never collapsed.

5. **Name the checks, not the conclusion.** *Five checks, all clean — starters, holes, depth,
   byes, record* beats *everything is fine*. A page that names what it checked can be audited; a
   page that pronounces cannot, and "all systems green" invites inventing systems to be green
   about.

6. **Absence is stated, never filled.** An em dash carrying why. Never a zero, never a blank,
   never a reassuring default.

7. **No superlative it cannot prove.** *The worst week still ahead* is computed and provable.
   *A strong roster* is not.

8. **Leaving is a success state.** The quiet page is the correct answer most weeks. It is not an
   empty state, not an apology, and not a prompt to go find something to do.

9. **Explain only what the engine knows.** Say *that* when only *that* is measured. `bye_collision`
   returns a value lost; it does not return a reason. A sentence explaining WHY a week costs 95
   is the designer reasoning, and must be marked as such or cut.

## Applied

| was | becomes | why |
|---|---|---|
| `NEEDS YOU` (band header) | *delete it* | The claim sentence is already the headline. The label says it twice — rule 1, and the standing constraint. |
| `Nothing needs you.` | `Nothing open this week.` | Report, not dismissal. Rule 2. |
| `One thing needs you.` | `One thing is open.` | Rule 1, rule 2. |
| `ALSO STANDING` | `CAN WAIT` | Names the reader's decision, not the app's taxonomy. |
| `ALL SYSTEMS GREEN` | `Five checks, all clean.` | Rule 5. Names them. |
| `YOU'RE GOOD THIS WEEK` | `The week is quiet.` | Rule 3 — the reader is not being graded. |
| `Week 6 is the one that hurts.` | `Week 6 costs 95, the largest of six weeks ahead.` | **CORRECTED — see below.** Rule 7. |
| `CLOSE THE APP` | **keep** | The single most on-voice element produced so far. It is the app getting out of the way, as a control. |
| `CLEARED — CAN WAIT` | **keep** | Rule 5 and rule 8 together. |

## The test

Read any line aloud. If it could appear on a poster that wants you to enlist, buy, or feel good
about yourself, it is wrong. If it could appear in a ledger kept by someone who works for you and
expects no thanks, it is right.

## The correction to this file's own table

The row above said **keep**, reasoned as "Indicative, provable, the week is the subject." Two of
those three are true. It is indicative and the week is the subject. **It is not provable.**

"The one that hurts" is a superlative over an OBJECTIVE, and it holds only under maximisation.
The owner's chop league decides last place weekly — eliminations run at midnight after the Monday
night game, and *"if you're in last on that monday, you're done and gone"*. Under that objective
the week that hurts is the week that ELIMINATES you, which is not the week with the largest
measured loss, and which this engine cannot identify: naming it would need a last-place
threshold, a forward-looking distributional quantity of exactly the kind already withheld
alongside playoff odds.

`byes_ahead` picks its week with `max(ahead, key=lambda w: ahead[w])` — largest loss among weeks
at or after now, with **no term for distance.** On the fixture's own data the largest and the
nearest coincide at week 6, which is why this never surfaced. Invert them (week 6 at 51, week 10
at 95) and the band names a week the reader may never reach while the nearer week is the gate.

So the figure stays and the superlative goes. `Week 6 costs 95, the largest of six weeks ahead`
states a magnitude and its scope, both measured, and claims nothing about which week matters
most. The reader supplies the survival reasoning, which the standing constraint already
anticipated: *"for any pick you make, there are going to be multiple valid options, which means
that not taking the engine's #1 isn't inherently wrong."*

**This is `#336b`'s defect class — prose outrunning its function — found in a voice spec rather
than in shipped code, and found by the owner describing their league rather than by any ratchet.**
Rule 7 was already written here and this file broke it three rows below stating it.
