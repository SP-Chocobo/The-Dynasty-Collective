# The doors room on a phone: three variants

Three phone sides of the doors draft room (v4_doors), built through the same pipeline as the
desktop: one fixture, one vocabulary dump, one withheld strip, one shared layer. They are meant
to be compared, not merged. Each is a template under _src that builds to the HTML file beside
this note, and each passes the render gate at 390x844, 360x800 and 430x932 across all six
formats and all three draft states, with and without a door open.

What they share, because the owner's words make it a hard requirement that they are two sides
of one UI: the same tokens, the same type, the same model (every number and every sentence is
the model's or the engine's vocabulary; nothing is computed or hand-written here), the same
structural names (a door is .door, its name is .who .nm inside #doors, the strip is .lineup,
the drawer is #shAll), and the same honesty: a dash is not measured, withheld means the number
exists and is not trusted, and no surface prints a number the desktop declines to print.

## The decisions that apply to all three

**What lands first.** On the bare URL each variant opens the board's first name, the leader's
door, and ?collapsed is the main display with nothing open, the state the X returns to. This
was a deliberate choice rather than the desktop's default inherited: a drafter on the clock
gets the fullest answer for the engine's first name without a tap, every other door still
answers who, why and at what cost as a closed row, tile or chip, and the gate measures the
heavier state on the bare URL, so the budget is proven on the state that carries the most.
The counter-argument is real and applies most to m1: the owner's own sentence reads as "the
main display is the four or five recommendations, tapping is what the reader does next", and
on m1 an open first door pushes the other four below the fold. Collapsed-first is a one-line
change in each template, and if a reviewer prefers it for m1 that is the right argument to
have.

**What was cut from the chrome.** On a phone the first recommendation has to arrive on the
first screen, so the header keeps the four sheet buttons (Every name, Rosters, Draft board,
Debate) as one row of thumb-sized buttons and leaves Resync and Settings to the desktop; the
count line keeps the window's honesty (how many positions the league can start, how many are
showing, in what order, how many names are on the board, which doors are not shown) and drops
the lit-slot legend; the flex-share basis, which the desktop states once per surface on the
count line, now rides the demand line it qualifies, inside the open door, since that is the
only place demand is printed on a phone.

**The lineup strip wraps.** The desktop insists on one line. On a phone one line means a strip
that scrolls sideways, and the gate now treats a strip that runs off the right edge as names
nobody can reach. So the strip wraps, every chip stays reachable, and in the 13-starter
formats it costs up to five rows. That is the price of not hiding a roster.

**Cost is always against the board's first name.** The owner's constraint says not taking the
engine's first name is not inherently wrong, so the cost a reader needs is the cost of not
taking it. Every alternative is priced against the leader with the model's own cells (now, at
your next turn, both picks across positions; the plain gap within the leader's own position).
The desktop's then-list also carries each name's gap to its own door's best; the phone does
not, except where the door is the leader's and the two coincide.

**A card is the tap target.** The desktop's cards carry a copy button and a numbers button each.
On a phone two 44px buttons per card cost more than the card. The card itself opens the
numbers sheet, whose header now carries the copy button; the open door's own best keeps both
buttons in a row.

**What the phone does not print.** Nothing the desktop withholds: "lasts to #N?" carries the
engine's withheld word, never a probability or a cost of waiting. Nothing the desktop marks as
not measured becomes a number. Streamable positions (K, DEF) are held back by default as on
the desktop and are one tap away. The door helpers the three templates share with v4
(DOOR_SHORT, doorLabel, the hold text, the tank and its caption) were moved into shared.js
rather than copied, so the short position forms and the tank's prose keep one home; the move
was certified render-identical on the desktop.

## m1_stack: the doors as a stack, one opens in place

The same four or five doors, in the board's order, as a vertical stack of compact rows. Each
closed row carries the position, its place in the order, what you hold, the name, the value to
your roster now, and first-on-the-board or instead-of-the-leader with the cost cells, so the
stack answers without a tap. Tapping a row opens it in place with its actions, the demand and
the flex-share basis, the wait line, the dearest-position mark, the pool, and the position's
other names as cards priced against the board's first name, with a dashed button into the
drawer for the rest. The X in the row's corner collapses it; the reader never loses their
place in the list.

Measured: 73 of 73 renders ok. 1.11 to 2.46 screens with a door open; 1.11 to 1.64 screens
collapsed on the two formats the collapsed pass covers. Measured by hand on the hardest format
the collapsed pass does not cover, HEAVY_IDP at 360x800: 1.96 screens late, 1.68 early, under
the 2.0 main-display budget by a hair in the late state. The 13-starter strip is the reason.

Where it refused: the closed rows carry no wait line and no demand; those arrive on open, as
the brief describes. Nothing else is held back.

## m2_sheet: the doors as a two-column grid, a panel opens under it

The same four or five doors as a tight grid of tiles, two across, in the board's order. Each
tile is the position, its place, its best name, the team, points and slot, the value, the gap
to the board's first name in the drawer row's own shorthand (first, or the signed gap), and
what you hold. The main display is the grid with nothing under it, and it fits one screen.
Tapping a tile fills a panel below the grid with what the desktop's open door and its card
strip carry; the X in the panel's corner clears it and the grid stands bare. An odd fifth tile
spans both columns rather than leaving a hole.

Measured: 73 of 73 renders ok. 1.32 to 2.25 screens with the panel open; 1.00 to 1.08 screens
bare on the two formats the collapsed pass covers; HEAVY_IDP bare at 360x800 by hand: 1.30
late, 1.25 early.

Where it refused: a tile carries no face, so a name gets the tile's width, and no cost cells,
which do not fit in half a phone; the value's unit, to your roster now, is stated once on the
count line rather than on every tile. The cells and the face are in the panel.

## m3_hero: one hero door, the other doors as chips under it

One door is the hero, the board's first name full width, carrying what the desktop's open door
carries: what you hold, the name, the value, first on the board, the demand and its basis, the
wait line, the dearest-position mark, the pool. The other doors in the window are a row of
thumb-sized chips under it, each the position, its best name and the gap to the board's first
name, so the row answers what else is valid and at what cost without a tap; doors the window
is not showing join the row dim and named by their place, and a streamable door is set aside
in the same row. Tapping a chip swaps the hero to that position's best and fills the block
under the chips with its other names, priced against the board's first name. The X returns to
the board's first name.

Measured: 73 of 73 renders ok. 1.07 to 1.85 screens with a door open; 1.00 to 1.15 screens
collapsed on the two formats the collapsed pass covers; HEAVY_IDP collapsed at 360x800 by
hand: 1.33 late, 1.22 early.

Where it refused: a chip carries the short name and one number, never the slot, the points or
the cost cells; those are the hero's and the cards', one tap away. The alternatives sit under
the chips, not inside the hero, so the chip row stays near the top whatever is open.

## What a reviewer should argue with

- Open-by-default against collapsed-by-default, above all on m1.
- Whether the lineup strip earns its rows in the 13-starter formats, or belongs in the Rosters
  sheet on a phone with only the lit slot kept on the main surface.
- Whether the alternatives should also carry each name's gap to its own door's best, as the
  desktop's then-list does, beside the cost against the board's first name.
- Whether a tappable card with a "numbers" hint is a clean enough button, against the
  desktop's explicit copy and numbers buttons on every card.
- Whether the window of five should stay five on a phone, where the hidden doors cost a chip
  row, or become everything the league can start.
- The hoist of the door helpers into shared.js: a pure move, but a move into the layer v1 and
  v2 also read.
