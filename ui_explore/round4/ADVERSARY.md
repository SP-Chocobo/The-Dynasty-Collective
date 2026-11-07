# Round 4 — the two adversarial passes

Every paired design in `round4/` gets attacked twice, by two separate adversaries with different
jobs. They are deliberately **not** combined into one review, because a reviewer holding both
briefs at once reliably trades one against the other: "the fabricated panel makes the layout
work, so leave it", or "the honest version is uglier, so soften the finding". Split, neither can
make that trade.

Both adversaries are hostile by assignment. The design is not yours and you gain nothing by
liking it. A review that returns "strong work, minor nits" has failed — if the design is genuinely
good, say precisely *what* survives attack and why, which is a stronger compliment and a more
useful one.

---

## FRONT 1 — the DESIGN adversary

**The question: is this genuinely usable, distinctive, and coherent across desktop and mobile?**

Three separate charges. Do not let a pass on one cover a failure on another.

### Usable
- Can a person answer "does anything need me?" in three seconds, without scrolling? Time it by
  looking at the first screenful alone, not the full-page render.
- Is the most important claim the most visually prominent thing, or did decoration outrank it?
- Are tap targets ≥ 44px? Is any text under 12px computed? Does anything overflow at 390px?
- Does the mobile page fit two screens of scroll (≤ 1328px at 390×664)?
- Is contrast ≥ 4.5:1 for body text on its own background? Check the computed values, do not
  eyeball them — this repo has been wrong about colour by eye before.
- What happens in the states the designer did not draw: a very long player name, eight claims
  instead of three, every value absent, a position code nobody has styled?

### Distinctive
- Strip the logo. Would anyone know this from any other dark-mode sports product?
- Is the brand doing structural work, or is it a wordmark sitting on top of a generic layout?
- Does it avoid the current generated-design clichés — uniform rounded cards, one accent colour
  on near-black, a gradient hero, emoji or icon-font section markers, everything centred?
- Is there one real idea here, or an assembly of safe choices?

### Coherent across desktop and mobile
- Are these recognisably **one product**, or two designs that share a palette?
- Does the information hierarchy survive the compression, or does mobile silently demote
  something desktop called urgent?
- Is anything present on one and missing on the other without a stated reason?

**Method:** render both pages yourself and look at them. Measure the numbers rather than
accepting the designer's own NOTES.md figures — a self-reported measurement is a claim, not
evidence. Screenshot the first viewport-height of each separately from the full page; the
three-second test is about the first screen only.

---

## FRONT 2 — the PRODUCT adversary

**The question: does every displayed element represent something CDME can actually calculate or
retrieve?**

Go element by element. Every number, label, chart series, badge, status, icon-with-a-meaning and
piece of copy that asserts a fact. For each one, name the function or data path that produces it,
or flag it.

**Verify against the SOURCE, not against `BRIEF.md`'s table.** That table is a summary I wrote
and it has already been wrong once — it initially claimed positional depth labels were invented
when `depth_ratings.depth_label` genuinely returns `Strong`/`Average`/`Weak`/`None`. If you find
the table itself is wrong in either direction, that is a finding worth more than any design note.
Read the real modules: `lineup_optimizer`, `depth_ratings`, `depth_chart`, `lineup_readiness`,
`league_standings`, `pick_ledger`, `freshness`, `player_universe`, `front_claims`, `front_page`,
`sleeper_client`.

Four verdicts per element, and the distinctions matter:

| verdict | meaning |
|---|---|
| **REAL** | a named function returns it today. Name the function. |
| **REACHABLE** | the data exists but nothing computes it yet; say what the work is. |
| **WITHHELD** | the engine CAN compute it and deliberately does not. Name the ruling. |
| **FABRICATED** | no basis exists. This is a defect, not a design choice. |

Then the subtler failures, which matter as much as outright invention:

- **Precision overclaim.** A real label drawn as a continuous meter. A floor drawn as a total.
  A count drawn as a score. The quantity is real and the rendering lies about how precisely it
  is known.
- **Absence rendered as a value.** A `0`, a blank, or a reassuring default standing in for
  "not measured". Absence must carry its reason.
- **Basis collapse.** `measured`, `constructed`, `floor` and `absent` drawn identically, so a
  reader cannot tell a battery fixture's demo number from a real measurement.
- **Implied causation.** Copy that asserts *why* something is true when the engine only knows
  *that* it is true.
- **Doors to rooms that are not built.** Navigation advertising destinations that do not exist:
  Player Compare, Trade Finder, Waiver Wire, Pick Calculator, Roster Health, League Notes and
  Analytics are all absent from `app.py`.

**The standing rule this serves:** this project has withdrawn published findings rather than keep
a number it could not defend. A design that ships a fabricated quantity is a liability, and the
most dangerous version is the one that looks the most finished — the densest, most professional
mock in the prior round had six invented panels and was the most convincing of the six.

---

## Output from each adversary

A findings list, most severe first. Each finding carries:

1. **Where** — file and the element, specifically enough to find it in five seconds.
2. **What is wrong** — one sentence.
3. **The evidence** — a measured number, a rendered screenshot, a named function, or a quoted
   line of source. Not an impression.
4. **What it would take to fix** — and whether fixing it costs the design something worth having.

End with the single most important thing to change, and say plainly whether the design is worth
refining or should be abandoned. Both answers are acceptable.
