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

---

# Applied, and re-measured

## The repair

One line in `compute_draft_board`, immediately after `bpa` is computed and beside the line that
already nulls `replacement_basis` for the same population:

```python
pool.loc[pool["_vor"].isna() & pool["absence_kind"].isna(),
         "absence_kind"] = ABSENCE_NO_REPLACEMENT
```

`.isna()` is the same predicate the `replacement_basis` line above uses, not a second reading of the
same columns. A row that already carries a kind keeps it, because `no_input` is the first and
stronger fact about a row nothing could price at all.

## Re-measured on the same drained `12T_ppr_SF` board

```
board 935 rows
IFF BREACHES: 0                        (was 8)
absence_kind census: {None: 439, 'no_input': 488, 'no_replacement_level': 8}
NO_REPLACEMENT rows: 8    positions ['QB']
kind on a PRICED row: 0                (must be 0)
NO_INPUT rows still: 488               (unchanged -- not overwritten)
example: Michael Penix QB  bpa=None  final_score=None  kind='no_replacement_level'
```

So the 8 breaching rows are now the 8 `no_replacement_level` rows, the 488-row `no_input`
population is untouched, and no priced row acquired a kind.

## The guard can now see it, and IS SENSITIVE

`test_absence_kind.TheIFFHoldsWHEREITUSEDTOBEFALSE` — a **drained superflex** fixture, built by
reading an opening board's own `projected_points` and drafting every quarterback who clears
`dr.qb_startable_floor(merger)`, the engine's sole producer of that threshold. Neither the threshold
nor the projections are typed into the test, so it cannot drift from the branch it exercises.

Sensitivity proven rather than assumed. Setting `dr.ABSENCE_NO_REPLACEMENT = None` in memory makes
the new line write `None` and reproduces the pre-repair board exactly, without touching a file:

```
WITH THE STAMP UNDONE -- iff breaches: 1
  S Sanders   bpa=None  basis=None  kind=None  source='points_vor_draftsharks'
```

One row rather than eight because this fixture is the small one — but it is the same shape
(a projected player, no level, no stated reason), and `test_the_iff_holds_here_too` fails on it.
The shipped class's board **cannot contain such a row at all**, which is the whole finding.

## Two mistakes made building the guard, both caught by its own non-vacuity test

1. The first fixture drafted "all but the last two" quarterbacks. Three of the four left still
   cleared the floor, so no decline fired and the class was vacuous.
2. The second derived the drain list by reconstructing `norm_name` and looking it up in the
   projections frame. Two rows shared one name, `.iloc[0]` took the wrong one, and **the four best
   quarterbacks were left undrafted** — Josh Allen at 379 projected points sat on the board as
   "remaining". Reading the board's own numbers removed the lookup entirely.

Both were caught by `test_the_population_this_class_exists_for_is_not_empty`, which is the reason
that test exists and is worth more than the three assertions it guards.

## What this did not do

* No value moved. The 8 rows keep `final_score = None`; they now say why.
* `ABSENCE_BELOW_SOURCE_CUTOFF` still has no producer and still needs evidence this pool does not
  carry. `WhatTheFieldMayNotBecome` was renamed from "the kinds nobody produces" to the singular and
  says which one, so the docstring is not left claiming two.
* `#50` is untouched. Whether an anchor should fill a startable-floor decline at all remains open,
  and the measured counterfactual says filling it moves no pick on the data we have.
