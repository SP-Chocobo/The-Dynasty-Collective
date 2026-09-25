# The `absence_kind` iff is FALSE on a drained superflex board, and its test cannot see it

Found while checking a claim from the `#34` investigation. The claim was that
`ABSENCE_NO_REPLACEMENT` is never stamped. That much is already documented in `draft_room` at
length — *"ONLY THE FIRST IS PRODUCED TODAY … The other two are named here and assigned by
`_derive_points_and_source` to nobody"* — with a correct reason for declining there:

> `ABSENCE_NO_REPLACEMENT` is not a property of this pool at all: whether a position has a
> replacement level is decided later against the league's own demand.

So the pool is right to decline. **But the decision IS made later, on the same board, and nothing
stamps it there either** — and a REGISTERED INVARIANT says something must.

## The invariant, and the breach

`test_absence_kind.TheBoardClassifiesOnlyWhatItActuallyKnows`:

> `test_a_kind_is_present_EXACTLY_when_the_row_has_no_price` — "The contract as one statement over
> every row, not a claim about a branch."
>
>     self.assertEqual(row.get("absence_kind") is not None, row.get("bpa") is None)

Measured on a **drained superflex board** — `12T_ppr_SF`, the capture's own 6,595-player universe,
season-summed and league-scored, with the top 40 quarterbacks by that scoring already drafted,
picks built directly rather than simulated so the probe costs one board build:

```
board 935 rows, QB 99, replacement_basis census {None: 99}

IFF BREACHES: 8
  unpriced with NO stated kind : 8
  kind on a PRICED row         : 0
  by position: {'QB': 8}
  example: Michael Penix QB  bpa=None  final_score=None  replacement_basis=None
           bpa_source='points_vor_draftsharks'  absence_kind=None
```

**Eight rows are unpriced and say nothing about why.** They are the floor-declined population, and
they are precisely the rows the `no_input` branch cannot reach: they HAVE a vendor projection, so
`bpa_source` is `points_vor_draftsharks` rather than `NO_PRICEABLE_INPUT`, so the one producing
branch skips them — and then `startable_floors` declines QB a level, `_fill_omitted_from_anchor`
deliberately never fills a startable-floor decline, `_vor` is NaN, `bpa` is None, and no kind is
ever written.

The other 91 QB rows satisfy the iff, but only because they carry `ABSENCE_NO_INPUT` from the
vendor's coverage gap — which is the honest *first* fact about them. That is why the breach is 8
and not 99, and it is worth stating, because it means the two populations are genuinely different
and the `#34` framing that called all of them "the floor's fault" was wrong.

## Why the guard is silent

`_fixture()` builds an **opening** board (`picks=[]`), in a **non-superflex** league
(`superflex=False`), over four positions and ~81 rows. `startable_floors` is produced only when
`SUPER_FLEX` is on the roster, and a decline needs a position the pool has drained past. **Neither
condition is reachable in that fixture**, so the violating population is empty there whether or not
the invariant holds. The test passes by sampling the wrong board.

This is the `#52` failure shape exactly, and the repository has named it before, in this very
codebase, about this very kind of change: *"the change EXPANDED THE POPULATION this function ranges
over, and an invariant proven over the old one was never re-checked against the new one."* Here
nothing expanded — the invariant was simply never checked against the population that breaks it.

## The repair, and why it is disclosure and not valuation

One line, at the site that already handles the mirror-image question. `replacement_basis` is nulled
for exactly this population two lines earlier, with the reason stated:

> `replacement_basis` EXPLAINS a price. A row that got no price has nothing for it to explain, and
> saying "live_starter_demand" there asserts that this league's starter demand produced a number it
> did not produce.

The mirror is that the absence must then be **stated**, because the kind is what says why. A row
that had a priceable input and still has no `_vor` got there for exactly one reason: its position
received no replacement level. That is `ABSENCE_NO_REPLACEMENT`'s own definition — *"his position
has no replacement level to price against — a STRUCTURAL absence, not a judgment about him."* It is
derived from the labelled facts already on the row, not from a fresh predicate (`#126`), and a row
that already carries `ABSENCE_NO_INPUT` keeps it, because no priceable input at all is the first
and stronger fact.

**This changes no value.** `absence_kind` feeds the surface that explains a blank to a person; it
enters no score, no ordering and no pick. The vocabulary's own docstring draws that line: *"Whether
that is the right ordering is a valuation question (`#50`), not a disclosure one; this vocabulary
only makes it askable at the surface where it would be answered."* Stamping the label is the
disclosure half. Whether an anchor should fill a floor-declined position at all remains `#50`'s,
and is untouched.

## What this does not do

* It does not price anybody. Eight rows go from "unpriced, no reason" to "unpriced, structural",
  and their `final_score` stays `None`.
* It does not produce `ABSENCE_BELOW_SOURCE_CUTOFF`, which still has no producer and still needs
  evidence this pool does not carry — that a source LISTS a player while declining to price him.
  That token stays named and unassigned, for the reason the vocabulary already gives.
* It does not touch the `#34`/`#168` design question. Those 8 rows are still declined; they now say
  so.
