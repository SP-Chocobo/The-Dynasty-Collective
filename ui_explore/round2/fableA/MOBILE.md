# The doors room on a phone: three variants

Three phone sides of the doors draft room (v4_doors), built through the same pipeline as the
desktop: one fixture, one vocabulary dump, one withheld strip, one shared layer. They are meant
to be compared, not merged. Each is a template under _src that builds to the HTML file beside
this note, and each passes the render gate at 390x844, 360x800 and 430x932 across all six
formats and all three draft states, in both states a reader sits in: the bare URL, which is the
main display with nothing open, and ?open, which lands with the leader's door open.

This is the second iteration. Two reviewers read the first independently (reviews/opus_mobile_r1.md,
the contract and the information design; reviews/sonnet_mobile_r1.md, a thumb and a clock) and
converged on a verdict, ship m2 and drop m1. That verdict is the owner's to make, so all three
are kept and all three were fixed; what each reviewer found, what moved, and where this note
disagrees with a recommendation are set out below.

What they share, because the owner's words make it a hard requirement that they are two sides
of one UI: the same tokens, the same type, the same model (every number and every sentence is
the model's or the engine's vocabulary; nothing is computed or hand-written here), the same
structural names (a door is .door, its name is .who .nm inside #doors, the strip is .lineup,
the drawer is #shAll), and the same honesty: a dash is not measured, withheld means the number
exists and is not trusted, and no surface prints a number the desktop declines to print.

## The decisions that apply to all three

**What lands first: the recommendations, nothing open.** The first iteration landed with the
leader's door open and reached the main display through ?collapsed. Both reviewers, from
different angles, read the owner's sentence the other way: "the 4-5 main recommendations near
the top; click one door and the other options populate the lower end; X in corner to collapse
back to main display" makes the landing screen the four or five, and the tap is what the reader
does next. They were right, and the earlier note had already named this as the argument to
have. So the bare URL now lands collapsed on all three, ?open lands with the leader's door open
so the gate can still measure that state by URL, and ?collapsed is honoured as the brief
reserves it. What it buys: m2's landing screen no longer draws the same door twice (tile and
panel, six facts inside 300px); m1's landing screen shows three doors at 390x844 instead of
one; the state a drafter spends most of the clock in is the lighter one. What it costs: on m1
and m2 the full "why" for the leader, the wait line and the pool, is one tap away rather than
on screen. m3 pays nothing, because its hero carries the full why in both states, and now also
carries its two action buttons in both states, so the forfeit it prints always sits beside the
numbers button that reaches the forfeit's own qualification (a floor rather than an estimate).

**The cost a glance shows is the two cells that carry a conclusion.** A tile (m2) and a chip
(m3) used to show one cost cell, the gap now. That is the one cell the engine can disagree
with: in 12T_ppr/mid the tight end reads -58.3 now while the engine's own "both picks" cell is
+6.9, and the desktop calls tight end the dearest position to wait on. Measured across the
fixture, the two-pick plan reverses the sign of the now cell in 28 of the 72 non-leader doors,
so a glance that saw "now" alone concluded wrongly two times in five. Both cells are drawn now,
each with the model's own label, the favourable one in the desktop's amber: "now -58.3 · both
picks +6.9". The third cell, at your next turn, is the difference of the two and lives with
them in the open door. The cells are read from the model's costOf, never recomputed from the
values beside them. The alternative, Sonnet's "show the decisive cell", was not taken: a cell
whose meaning changes from tile to tile with only a word to say so is a rule the reader has to
learn, and always drawing both costs one line.

**The clock sticks.** On the desktop the clock cannot scroll (.room is 100vh and clips). On a
phone the page scrolls, and tapping a door used to scroll the pick timer clean off the screen
at the moment a reader was weighing an alternative (727px in m2, 364px in m3). The timer and
the pick are one line now and that line sticks to the top of the viewport; the next-turn span
and the seats are context and scroll with the page under it. What a tap reveals lands just
below the stuck clock, measured: after any door tap in any variant the clock sits at y=0-33
and the opened door's header at y=38. m1's tap had the mirror-image bug, no reveal at all, so
the opened door landed wherever the collapse above it left it; it is revealed now like the
others. The X stays in the opened door's corner, where the brief puts it; Sonnet's bottom
switcher would move its job into the thumb zone and is a design the owner should see as an
option rather than something added unasked.

**The fold says so.** In 17 of 216 probed renders the first screen ended in a gutter with real
content below and nothing on screen saying so. A fixed band at the bottom of the viewport is
lit while the document runs on below it and says what is below, counted the way the scroll
affordance counts rows: "↓ 3 more doors below", "↓ 1 more name below", else "↓ more below". It
is pointer-through and its label is a pseudo-element, so it is a signpost over the content and
never content under a sibling; the gate asserts it is lit whenever the page is taller than the
viewport. It is re-read on scroll, on resize, and whenever the document changes height with
neither, because the fonts swap in after first paint and one render in 397 measured as fitting
one frame too early.

**What was cut from the chrome.** On a phone the first recommendation has to arrive on the
first screen, so the header keeps the four sheet buttons (Every name, Rosters, Draft board,
Debate) as one row of thumb-sized buttons and leaves Resync and Settings to the desktop; the
count line keeps the window's honesty (how many positions the league can start, how many are
showing, in what order, how many names are on the board, which doors are not shown) and drops
the lit-slot legend; the flex-share basis, which the desktop states once per surface on the
count line, now rides the demand line it qualifies, inside the open door, since that is the
only place demand is printed on a phone. The first door still starts 46-67% of the way down the
first screen (Sonnet's finding 3); nothing above it was removed this round, and the lineup
strip is the block to argue about.

**The lineup strip wraps.** The desktop insists on one line. On a phone one line means a strip
that scrolls sideways, and the gate treats a strip that runs off the right edge as names nobody
can reach. So the strip wraps, every chip stays reachable, and in the 13-starter formats it
costs up to five rows. That is the price of not hiding a roster.

**Cost is always against the board's first name.** The owner's constraint says not taking the
engine's first name is not inherently wrong, so the cost a reader needs is the cost of not
taking it. Every alternative is priced against the leader with the model's own cells (now, at
your next turn, both picks across positions; the plain gap within the leader's own position).
The desktop's then-list also carries each name's gap to its own door's best; the phone does
not, except where the door is the leader's and the two coincide. The lead-in to the cells is
the desktop's own sentence, "Instead of Etienne:", drawn by one function for all four surfaces;
the first iteration wrote "instead of Etienne" in three copies and had already drifted.

**A card is the tap target.** The desktop's cards carry a copy button and a numbers button each.
On a phone two 44px buttons per card cost more than the card. The card itself opens the
numbers sheet, whose header now carries the copy button; the open door's own best keeps both
buttons in a row.

**One home for the door's sentences.** The first iteration hoisted the position short forms,
the hold text and the tank's prose into shared.js. This one finishes the job: the window, the
default door, the demand line, the no-name sentence, the dearest-position mark, the
first-on-the-board and instead-of sentences, and the who block are shared.js's now, each the
desktop's code verbatim with the template's globals passed in, and v4 reads them through the
names it always had. "lasts to #N? withheld", a hand-written pair in four templates (v4 spelled
the word itself), is one function beside WITHHELD_LABEL, the label it is the short form of. The
phone-only pieces (the count line, the glance cells, the card strip, the context block, the
name with its mark glued) are shared.js's too, so the three phones draw one sentence each.
Certified: 0 of 60 desktop markup hashes moved (_domdiff.py against the commit before this
iteration), 0 console or page errors. Still copied: the drawer (four near-identical copies that
differ in the tank flag and "click" against "tap") and v4's two remaining copies of the dearest
sentence, listed under what to argue with.

**What the phone does not print.** Nothing the desktop withholds: "lasts to #N?" carries the
engine's withheld word, never a probability or a cost of waiting. Nothing the desktop marks as
not measured becomes a number. Streamable positions (K, DEF) are held back by default as on
the desktop and are one tap away, named on the count line with the one button that shows them.

## m1_stack: the doors as a stack, one opens in place

The same four or five doors, in the board's order, as a vertical stack of rows. Each closed
row carries the position, its place in the order, what you hold, the name, the value to your
roster now, and first-on-the-board or instead-of-the-leader with all three cost cells, so the
stack answers without a tap. Tapping a row opens it in place and reveals it under the stuck
clock, with its actions, the demand and the flex-share basis, the wait line, the
dearest-position mark, the pool, and the position's other names as cards priced against the
board's first name, with a dashed button into the drawer for the rest. The X in the row's
corner collapses it.

Measured, 108 of 108 renders ok in the 397-render gate: 1.12 to 1.97 screens on the main
display (bare URL, every format, every state, every viewport; the worst is HEAVY_IDP/late at
360x800, then LIGHT_IDP 1.91 and 12T_ppr_K_DEF 1.75) against the 2.0 main-display budget, so
the tightest case in the fixture clears it by 0.03 screens, about 24px; 1.71 to 2.47 screens
with a door open (?open; the worst is HEAVY_IDP/early at 360x800) against 3.0. The 13-starter
strip and the full three cells on every closed row are the reasons.

Where it refused: the closed rows carry no wait line and no demand; those arrive on open, as
the brief describes. Sonnet's suggestion that a closed row be "name + value + one cost, about
64px" was not taken: the three cells on every closed row are the thing both reviewers praised
in this variant, and one cell is the inversion the glance surfaces just had removed. Its cost
is the shape: a stack of full rows will always put part of the league below the fold, which is
what both reviewers held against it and what the fold cue now at least says.

## m2_sheet: the doors as a two-column grid, a panel opens under it

The same four or five doors as a tight grid of tiles, two across, in the board's order. Each
tile is the position, its place, its best name, the team, points and slot, the value, and
against the board's first name either "first" or the two glance cells, now and both picks;
then what you hold. The main display is the grid with nothing under it. Tapping a tile fills a
panel below the grid with what the desktop's open door and its card strip carry and reveals
the panel under the stuck clock; the X in the panel's corner clears it and the grid stands
bare. An odd fifth tile spans both columns rather than leaving a hole. At 360px a name wraps
before its availability mark, never after it.

Measured, 108 of 108 renders ok in the 397-render gate: 1.00 to 1.41 screens on the main
display (bare URL; the worst is HEAVY_IDP/late at 360x800, then LIGHT_IDP 1.35 and
12T_ppr_K_DEF 1.25; 12T_ppr is 1.12) against 2.0; 1.42 to 2.39 screens with the panel open
(?open; the worst is HEAVY_IDP/early at 360x800) against 3.0. The second glance cell on every
tile cost about a line per tile against the first iteration's 1.00 to 1.30.

Where it refused: a tile carries no face, so a name gets the tile's width, and no third cost
cell, which does not fit in half a phone; the value's unit, to your roster now, is stated once
on the count line rather than on every tile. The third cell and the face are in the panel. The
grid stands above the viewport while the panel is open, so switching doors is a flick up and a
tap; that is the shape of a panel under a grid, and the bottom switcher is the design that
would remove it.

## m3_hero: one hero door, the other doors as chips under it

One door is the hero, the top door full width, carrying what the desktop's open door carries:
what you hold, the name, the value, first on the board, the demand and its basis, the wait
line, the dearest-position mark, the pool, and its two action buttons. The other doors in the
window are chips under it, two across, each the position, its best name and the two glance
cells against the board's first name, so the row answers what else is valid and at what cost
without a tap. Tapping a chip swaps the hero to that position's best, tapping the hero opens
it, and either fills the block under the chips with its other names priced against the board's
first name and reveals the hero under the stuck clock. The X clears them and returns to the top
door, which is what its label now says: the top door is the board's first name except when
that name is streamable and set aside, as in 12T_ppr_K_DEF.

The count line is the same function the other two phones draw, and the chips are only the
window's other doors, so the number the line prints is the number of doors on the screen. The
first iteration drew every door the league can start as a chip, dim ones for the doors outside
the window and dashed ones for the streamable doors, under a sentence that said "showing 4" and
beside a button offering to show what was already shown. Doors outside the window are named on
the count line by their place ("not shown: DL 6th door · DB 7th door"), as on the desktop, and
open on a tap there; the bare ordinal that sat beside a signed gap on a dim chip went with it.

Measured, 108 of 108 renders ok in the 397-render gate: 1.00 to 1.42 screens on the main
display (bare URL; the worst is 12T_ppr_K_DEF/late at 360x800, then HEAVY_IDP 1.41 and
4WR_TE_PREMIUM 1.30) against 2.0; 1.09 to 1.91 screens with the hero's other names open
(?open; the worst is 12T_ppr_K_DEF/mid at 360x800) against 3.0. The hero's two action buttons
in the main display and the second glance cell on every chip are the difference from the first
iteration's 1.00 to 1.33; the chips drawn only for the window gave some of it back.

Where it refused: a chip carries the short name and the two cells, never the slot, the points
or the third cell; those are the hero's and the cards', one tap away. The alternatives sit
under the chips, not inside the hero, so the chip row stays near the top whatever is open. The
chips identify a door by its key (Opus F11), as the count line's chips and the desktop's
then-list do; the Cinzel title is spelled on the hero.

## Where this note disagrees with a reviewer, or did not get to one

- Opus F1 offered two fixes for the count line: "showing all 7", or draw the window and name the
  rest. The second was taken, because it is the desktop's discipline and the other two phones
  already kept it; "showing all 7" would have made m3 the one surface with no window.
- Sonnet 5, the decisive cell: not taken, see the glance cells above.
- Sonnet 1, a 64px closed row for m1: not taken, see m1 above.
- Sonnet 2's bottom door switcher and Sonnet 9's copy-on-the-card and bottom close bar: not
  built. They are designs for the owner to choose, not defects to fix, and the X in the corner is
  the brief's own sentence.
- Sonnet 3, the chrome: not reduced this round beyond m2's unit clause. The numbers stand as
  measured there: first door at 46-67% of the first screen, the lineup strip the largest block.
- Sonnet 10, touch firing the hover layer, and the marks' legend: not changed. Gating tooltips
  to hover-capable devices would leave the availability marks with no meaning at all on a phone;
  a tap on a mark shows its record today, and the stranded tip after a redraw is cosmetic.
- Sonnet 11, 100vh on iOS: done, min-height is 100dvh where the browser has it.
- Sonnet 13, the chip legend in the dim token: moved to the muted token. The other dim uses stand.
- Sonnet 8's draft board, a sideways scroller inside a sheet with no affordance: not touched;
  it is the shared sheet and the gate excludes sheets by design.
- Opus F13, the compound door's label saying "defense" where the engine's word is "defender":
  pre-existing in the shared door builder and read into v4's tooltips, so changing it moves the
  desktop; recorded, not touched.
- v3_trio still hand-writes the withheld word in its footer; it is a control surface outside
  this work and was left alone.

## What a reviewer should argue with

- Whether the lineup strip earns its rows in the 13-starter formats, or belongs in the Rosters
  sheet on a phone with only the lit slot kept on the main surface. It is the block that decides
  where the first door starts.
- Whether the two glance cells are the right two, against all three or against one.
- Whether the alternatives should also carry each name's gap to its own door's best, as the
  desktop's then-list does, beside the cost against the board's first name.
- Whether a tappable card with a "numbers" hint is a clean enough button, against the
  desktop's explicit copy and numbers buttons on every card.
- Whether the window of five should stay five on a phone, or become everything the league can
  start.
- The drawer, four copies, as the next hoist; and v4's two remaining copies of the dearest
  sentence.
- The hoist itself: a pure move, certified, but a move into the layer v1 and v2 also read.
