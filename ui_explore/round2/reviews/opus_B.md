# Adversarial review — set B (round 2)

Method: read all twelve `_shots/` PNGs; re-rendered all four variants in all three states at
1440×900 with Chromium (`/opt/pw-browsers/chromium-1194`), measuring font sizes, scroll containers,
door interiors and occlusion; cropped four regions at 2× to confirm what the PNGs showed; checked
every numeric claim in `RATIONALE.md` against `states.json` directly.

**What round 2 genuinely fixed, stated once:** minimum resident font is **12.0px** in all twelve
renders (round 1's 9.6px is gone). No page scroll anywhere. `depth_exposure` prints a digit only
under `measured` — 3 rows at `late` (Vele 7.1, Concepcion 7.1, Mason 7.2), an absence-with-reason
everywhere else, no `0.0` anywhere (ADJ §2 satisfied in all four). The cliff neighbour is taken
from the **bpa** order and the surface says so (ADJ §5 satisfied — V1 `mid` names T. McLaurin at
3.2, which is McMillan's 48.08 − McLaurin's 44.84, not the display neighbour). `cliff.tier` is used
1:1 with no invented cut-points (ADJ §4). No field names, no "priced"/"UV" on any surface. No
variant re-bases the negative scale at `late`. `YOUR NEXT` is on screen in both rail variants
(ADJ §8). That is real progress and I am not going to re-litigate it.

Everything below is what is still wrong.

---

## 1. Verdict per variant

### V4 · Four cells — **survives, clearly first**

The only variant where I can find the answer to all four of the owner's words in under five seconds
at every state. At `late` the WHO cell puts `−34.6`, "the board's first by value", the declared tie,
**"Lineup slot · Bench · your starters are set"**, the 12-pick count and the WITHHELD chance in one
column with labelled rows and the biggest type in the set. The 2×2 is the owner's sentence drawn
literally, and the position strip does in 60px what V2 spends 420px on. Its cost is real and I
accept it: it never shows more than four alternatives, and it has **no rail at all** — which is a
RULED §1 item it quietly drops (see Finding 2). Its remaining defects are small and local. Revise
this one.

### V3 · Trio — **survives, second, but the comparison row is a trap**

The best `late` board in the set: seven names, no scroll, no clipping, no dead space, and
"Depth insurance · where measured" reading `7.1 / not measured / 7.2` is the cleanest absence
handling anyone wrote. The lettered roster strip at `mid` (A on WR2, B on RB2, C on QB) is the best
single idea in either set. But the grid's central device — one labelled row, three positions side by
side — **structurally forces the cross-position comparison §14 and ADJ §3 forbid**, and it is
visible at `mid`: the "Drop behind him" row reads `3.2 sharp drop` (WR) · `1.3 no cliff` (RB) ·
`3.4 no cliff` (QB). A drafter reads left to right and sees 3.4 called nothing and 3.2 called sharp.
That is not a styling slip; it is what a comparison table does to per-position quantities. Fix the
row or lose the variant.

### V1 · Ledger, cut — **survives on sufferance, third**

The span rail is the best answer to §2 in the set — eight named past boxes, one marked
`#127–#138 · 12 picks · rosters 7, 8, 9, 10, 11, 12`, then `YOUR NEXT #139`, no blank boxes. The
three-alternative INSTEAD column works. But the variant is held together by a side list it cannot
render: at `late`, with **seven** candidates and 500px of spare height, it truncates three of seven
names to "K. Conce…", "T. Lawren…", "T. Hocke…" in a 243px fixed-height box. At `early` and `mid`
that same box shows 9 of 24 and scrolls. And the WHY cell at `late` asserts "The last receiver this
board rates" while K. Concepcion, a receiver, sits 180px below it (Finding 3). It is the round-1
ledger with a haircut, and the haircut is good; the furniture underneath it was not re-sized for
this round's states.

### V2 · Doors — **does not survive. Not for the reason the rationale concedes.**

The brief asks whether three-name doors holding one name at `late` kills the concept. It does not —
that is an honest cost and I would accept it. What kills V2 is that the **fixed door height is
oversized at all three states, worst at `early`**, and that at `early` it paints its own content
underneath an opaque sibling. Measured: blank vertical gap inside the closed doors is **182px (WR)
and 173px (TE) at `early`**, 105px at `mid`, 128–147px at `late` — 25–40% of every closed door, at
every state. And at `early` the WR door's "THEN, BY VALUE" list renders three rows (J. Chase,
C. Lamb, N. Collins) of which **one is half-covered and two are entirely hidden** behind the
across-cells block; the TE door's two rows (T. McBride, C. Loveland) are **completely invisible** and
its section header is sliced through. I confirmed this in a 2× crop. Separately, at `late` the pool
strip cannot fit **seven** rows (clientHeight 111, scrollHeight 124 — row 7, T. Hockenson, is cut in
half), and the same small grey gap number means two different things on one screen (Finding 5).
V2 is the densest variant in the set and shows the least per pixel. Discard it; the salvage is one
sentence (§3).

---

## 2. Findings, most severe first

### F1 · V2 `early` — the closed doors paint five player names underneath the across-cells. SEVERE.
**What.** `v2_doors.html#early`, the WR and TE doors. The `.nxt` ("then, by value") block is in the
DOM at y 556–635 (WR: Chase, Lamb, Collins) and 584–635 (TE: McBride, Loveland), and the
across-cells strip is drawn opaque over the same region. Visible in your own
`_shots/v2_doors_early.png`: "I. Chase 158.7" has its lower half sliced, "THEN. BY VALUE" in the TE
column is cut through its baseline, and Lamb/Collins/McBride/Loveland are not on screen at all.
**Why it hurts.** The drafter is told these doors answer "what else at this position" and two of
four doors answer it with nothing, while the markup says they answered. This is round 1's twelve
blank boxes wearing a different coat: in the PNG, passing every check.
**Why the harness missed it.** `_shot.py` line 14's `r.clipped` only catches *self*-clipping
(`scrollHeight > clientHeight` under `overflow:hidden`). Occlusion by an opaque sibling is invisible
to it, and `r.scrollers` is printed but never asserted on. The rationale says "Every PNG in
`_shots/` was looked at." It was in the PNG.
**Fixed =** no door content outside the door's painted box at any state, verified by an occlusion
check (element centre point hit-tests to itself), not by a self-overflow check.

### F2 · V2 and V4 drop four RULED §1 items without flagging it as a ruling change. SEVERE (process).
**What.** §1 RULES: a rail across the top carrying the next on the clock; rail boxes carrying the
drafting user's name; your own picks glow; a re-center button. V2 and V4 have no rail, so all four
go. The defence in `RATIONALE.md` — "the owner raised it three times and never positively" — is an
argument for changing the ruling, not evidence that it changed.
**Why it hurts.** Nothing on either surface says a binding decision is being contested, so a reader
comparing four variants will read the rail's absence as a layout preference.
**My view on the merits, since you will be asked.** V4's replacement is *better* than every rail
here: `12 picks until you choose again · your next turn is #139` in the clock bar plus
`since your last turn (#115): 5 TE · 3 RB · 1 WR · 1 QB left the board` carries both load-bearing
facts §2 says the rail is a picture of, in one line, legibly, at desk distance. §2 itself concedes
"the rail earns its space or it does not get any" and BOUNDS its own necessity argument for
no-trade leagues. So V4's trade is defensible and should go to the owner as an explicit §1 change
request. **V2 gets no such credit**: it drops the rail and spends the reclaimed 120px on doors that
are 25–40% empty.
**Fixed =** both variants carry a visible "this contests §1" note, or the rail returns.

### F3 · "The last receiver this board rates" is printed while another receiver is on screen. SEVERE.
**What.** `_core.js:158`. At `late`, V1's WHY and V4's WHY both print *"The last receiver this board
rates; the drop behind him (a sharp drop, 4.2) is to a player below this list."* for D. Vele. It is
true in **bpa** order (Concepcion's bpa −7.93 is *ahead* of Vele's −7.99). The screen is in **tav**
order, and K. Concepcion — a receiver — is rendered 180px below that sentence in V1's OR INSTEAD
list and directly below it in V4's INSTEAD AT WR cell.
**Why it hurts.** ADJ §5's repair was applied to *which neighbour gets named* but not to the
sentence that asserts there is no neighbour. "This board" and "this list" both denote the
tav-ordered thing the drafter is looking at. A flat contradiction, two seconds' reading apart, on
the hardest board.
**Fixed =** the sentence names its ordering the way the neighbour sentence does, e.g. "no receiver
behind him **in the order the drop was measured**", or it does not say "this list".

### F4 · V3's comparison rows force the cross-position comparison the contract forbids. SEVERE.
**What.** `v3_trio.html`, the "Drop behind him · within his position" row.
`mid`: `3.2 sharp drop · to T. McLaurin` | `1.3 no cliff · to T. Etienne` | `3.4 no cliff · to
J. Burrow`. `early`: `37.8 sharp drop` | `8.6 sharp drop` | `9.3 sharp drop`.
**Why it hurts.** The tier is correct and per-position (`typical_gap` WR 0.62, RB 0.79, QB 3.33), so
3.4 really is nothing for a QB and 3.2 really is a cliff for a WR. But a horizontal row under one
label is an instruction to compare, and the comparison is invalid — ADJ §3's exact failure mode
reached without dividing by anything. At `early` the row says RB 37.8 / WR 8.6 / TE 9.3 all
"sharp drop", which invites "the RB cliff is four times the WR cliff". It is not; the quantities do
not share a scale.
**Fixed =** drop the number from the row and keep only the engine's word plus the named neighbour,
or move the number inside the per-column block where no row-wise reading is offered. The same ban
applies to V3's "Skip his position now" row only if forfeit is ever normalised — it is not here
(raw points, 9.4 / 0.8 / 1.8), so that row is fine.

### F5 · V2 `late` — the same small grey number means two different things, 400px apart. SEVERE.
**What.** `v2_doors.html#late`. In the QB door: `S. Darnold −37.9 ₋₁.₅`, `K. Murray −38.7 ₋₂.₃`
(gap to *that door's* best, T. Lawrence). In the pool strip below, same typography, same position in
the row: `S. Darnold −37.9 ₋₃.₃`, `K. Murray −38.7 ₋₄.₁` (gap to the *board* leader, D. Vele).
**Why it hurts.** One player, one screen, two different numbers in identical styling. A drafter who
memorises "Darnold is 1.5 back" and glances at the strip gets 3.3. The brief's live question is
whether the **gap** is the signal; V2 renders the gap against two silently different anchors.
**Fixed =** one baseline per surface, stated once, or visibly different encodings for the two.

### F6 · V2 `late` — the open door says "all three" with two names in it; and no door says "bench".
**What.** `_core.js`/`v2_doors_src.html:131` hardcodes *"same position: waiting costs the same for
all three"* in the BETWEEN THEM strip. At `late` the WR door holds two names. Separately, every
door frame at `late` reads `· no slot` and the open card shows `−34.6 / value to your roster` with
no slot line at all — V1, V3 and V4 all print **"Bench · your starters are set"**.
**Why it hurts.** The literal miscount is trivial; the missing slot line is not. Your own rationale
(§"What rendering late taught", point 3) says *"A surface that showed value without the slot would
mislead here."* V2 is that surface. `−34.6` presented as BOARD'S FIRST with "no slot" beside it,
and nothing saying the starting lineup is full, is the single most alarming cell in twelve renders.
**Fixed =** the count comes from the rendered column; the open card carries the slot line.

### F7 · V2 `late` cannot fit seven rows; V1 `late` cannot fit seven names. HIGH.
**What.** V2 `#list` at `late`: clientHeight 111, scrollHeight 124 — row 7 (T. Hockenson) is cut
through the middle of its type, confirmed in a 2× crop. At `early`/`mid` the same strip shows 10 of
24 with 232px hidden behind a vertical scroll in a 140px band. V1 `#alts` shows 9 of 24 at
`early`/`mid` (482px hidden) and at `late` truncates **three of seven** names: "K. Conce…",
"T. Lawren…", "T. Hocke…". V3 `#list` shows ~12 of 24 at `early`/`mid` and all 7 at `late` — the
only pool in the set that passes its own hardest state.
**Why it hurts.** "Other valid options" is one of the owner's four words. Half the board behind a
140px scroll on a 30-second clock is not dissemination. Truncating a name is worse than omitting
the row: a drafter cannot act on "T. Lawren…".
**Fixed =** at `late` every candidate is fully visible and fully named with room to spare; at
`early`/`mid` the resident count is a design decision stated out loud, not a scrollbar.

### F8 · Positive wait costs and negative values share a cell at `late` with no unit and no bridge. HIGH, whole set.
**What.** V4's strip cell: `QB · T. Lawrence −36.4 … 0.8 skip cost · least`. V3's rows: Value
`−34.6 / −36.4 / −43.7`, Skip `9.4 / 0.8 / 1.8`. V1's WHY: `−34.6` headline, `"it costs about 9.4"`
in the body. Four numbers in two signs and two meanings, no unit printed anywhere in the set.
**Why it hurts.** This is the `late` board's whole legibility problem and no variant takes it on.
Three of four say "Bench · your starters are set", which is adjacent to the answer but never joined
to the minus sign. Nothing on any screen says *why* the best available player is negative. A drafter
who has not read a document reads "−34.6 · the board's first by value" and concludes the board is
broken or that he must not pick.
**Fixed =** one sentence at `late` that joins the slot state to the sign — the engine already has
`displacement_adj` (−33.7 for Vele) and `fills_required_slot: false` to justify it. No new field
needed, no re-basing.

### F9 · Five hand-picked visibility cut-points in client code, one of which hides measured values. MEDIUM-HIGH.
**What.** `_core.js`: `Math.abs(c.horizon) >= 2` (160), `Math.abs(r.dh) >= 2` (191),
`Math.abs(k.projToBest) >= 2` (155), `Math.abs(r.dproj) >= 2` (187), `takeProb >= 0.01` (126/159).
**Why it hurts.** V3 `early`, "Dynasty horizon · inside his value" row, column B: prints **"—"**
while the payload carries `time_horizon_adj = −0.90` for A. St. Brown (and +0.55 for Bowers). At
`mid`, column A prints "—" for McMillan's measured **−0.28** and column C prints "—" for Allen's
measured **0.00** — the same glyph for a measured small value and a measured zero, under a row
label that asserts the horizon is "inside his value". That is the mirror image of ADJ §2: not a
non-measurement printed as a number, a measurement printed as an absence. The `≥2` is a chosen
constant deciding what a person sees, in client code, with no evidence behind it (`#56`'s shape).
**Fixed =** either show every measured horizon, or render below-threshold as "measured, small"
rather than as the same dash used for absence — and name the constant as a disclosed display rule.
Lower priority but same family: `about 3%` vs `about 2%` in V3 `mid`'s Rival row is 0.026 vs 0.024.
Rounding to whole percent at that magnitude manufactures a 50% difference out of 0.2pp.

### F10 · The tie set shrinks depending on who you are looking at. MEDIUM.
**What.** `_core.js:109`: `tiedWith` only lists a partner when `c.rank === 1 || o.rank === 1`. At
`late` the engine puts `tie` in `forces` on **three** rows — Vele, Concepcion, Lawrence. V3 column A
therefore reads *"a tie with K. Concepcion and T. Lawrence"*; column B, 400px to its right, reads
*"a tie with D. Vele"* — Concepcion dropped. V2's Concepcion card says *"a tie with D. Vele"*,
dropping Lawrence.
**Why it hurts.** The tie is the single best piece of evidence on the `late` board that not taking
#1 is defensible — the thing the governing constraint is about. Two adjacent columns disagree about
how large it is, because of a rank-1 anchor condition the client invented. The engine's `tie` force
is membership, full stop.
**Fixed =** the tie set is the set of rows carrying `tie`, rendered identically from every subject.

### F11 · "order" is given equal visual weight to value, and the word collides with itself. MEDIUM-HIGH.
**What.** `edgeHTML` renders `+2.7 value McMillan` and `+2.2 order Judkins first` as two figures of
identical size and colour weight, with an `AGREE`/`SPLIT` verdict badge. The footnote 150px below
reads *"Value is what the board orders on; **order** is which to take first across two turns."*
**Why it hurts.** Two meanings of "order" in one viewport, one defined by contradicting the other,
and nobody on a 60-second clock reads the footnote. More importantly: the second figure is a
difference of `positional_forfeit`. §16a measured ordering on that family at **−6.090%** of
starting-lineup points, 10 seats won against 56. ADJ §1 permits forfeit to *inform* and forbids it
from *deciding*. The prose obeys that; the visual weighting does not — a 50/50 two-figure badge
reads as two co-equal rankings and `SPLIT` reads as a coin flip between them.
**This is the best thing in the set and I want it kept** — ADJ §6 asked for exactly this subtraction
and all four variants perform it, correctly (verified: early St. Brown/Taylor order 48.06−38.17=9.89
→ "+9.9", value 176.28−166.51=9.77 → "+9.8"; mid McMillan/Judkins 2.23→"+2.2", 2.73→"+2.7"; late
Vele/Lawrence 9.36−0.77=8.59→"+8.6").
**Fixed =** name the second figure for what it is ("costs less to defer", "waiting cost") and never
"order"; render it visually subordinate to value so the screen's weighting matches the ruling.

### F12 · "Amon-Ra St. Brown" is rendered "A. Brown" in all four variants. MEDIUM.
**What.** The initial+surname shortener drops "St." and produces "A. Brown". A.J. Brown is also
among the 24 at `early` and abbreviates identically; Chase Brown renders "C. Brown" two rows away.
Visible in V2 `early` (WR door head, pool row 2), V3 `early` (roster strip, pool row 2), V4 `early`
(position strip and both edge sentences), V1 `early` (INSTEAD head, OR INSTEAD row 2).
**Why it hurts.** ADJ §8 listed this as known-true and it is unchanged. V3 and V4 prove the fix is
available — their card heads print "Amon-Ra St. Brown" in full. The short form is used everywhere a
decision gets made.
**Fixed =** the shortener keeps name particles, and disambiguates on collision within the rendered
set.

### F13 · `no_surplus` is reported as "not measured". MEDIUM.
**What.** `_core.js:106` → *"not measured — no backup job here to cost"*. The engine's own label
(`EXPOSURE_BASIS_LABELS[no_surplus]`, quoted in ADJ §2) begins *"**measured**, but it is a starter's
whole value rather than a backup's job…"*.
**Why it hurts.** Suppressing the digit is correct and required. Calling it "not measured" is the
one place the surface puts a word in the engine's mouth that the engine disowns — and this file's
whole claim is that it uses the engine's own words.
**Fixed =** the second clause already paraphrases the label well; drop the "not measured —" prefix.

### F14 · V3's forward rail is round 1's blank boxes with a roster number in them. MEDIUM.
**What.** `v3_trio.html#late`: twelve ticks reading `R7 R8 R9 R10 R11 R12 R12 R11 R10 R9 R8 R7`,
none of them orange, above a legend that says *"named rivals in orange"*. At `late` no candidate
clears the 1% rival threshold, so the legend describes a colour that appears nowhere on screen.
**Why it hurts.** The brief's instruction on legends: challenge whether the visualisation belongs. A
legend for an absent encoding plus twelve boxes carrying one unactionable datum each is exactly the
rail §2 says does not earn its space. Your own rationale concedes it: *"it still reads as a row of
small boxes, just labelled ones. The span (V1) reads calmer."* Agreed — so take V1's span.
**Fixed =** V1's single marked span, or ticks only when at least one is marked.

### F15 · Smaller, worth one line each. LOW.
- **V2 `early`, QB door** states the same absence four times: `no wait cost measured here` ·
  `▽No quarterback has been drafted by anyone yet.` · *"No quarterback among the 24 this board rates
  here."* · `nothing to cost here`. The sentence is good. Four of it is the failure mode the brief
  names.
- **V4 `mid`, INSTEAD AT WR**: McLaurin's second figure is `3.2 sharp drop between` (points);
  Williams' is `2 places apart` (ordinal), same column, same styling. Two units in one column, and
  the second is the bare rank the rationale claims was cut.
- **V1, IF YOU WAIT rows** print two near-identical magnitudes with different bases and no labels:
  `early` → `D. Achane [sharp drop · 37.8] −36.7`; `mid` → `T. McLaurin [sharp drop · 3.2] −4.6`.
  One is the bpa drop, one the tav gap. Unreadable as a pair.
- **V1's rail label** reads *"the span is one marked count, not 12 empty boxes"* — a note to a
  reviewer rendered on the user surface.
- **The ▲/▽ legend** (`take now` / `wait`) appears in V1 and V4 at `late` where only ▲ is used; and
  ▲ is applied to "Depth insurance measured at 7.1", attaching a take/wait polarity to a number the
  engine did not sign.
- **Dead space** is honest in V1 and V4 and I will not call it a defect, but the rationale's
  self-report is wrong: V1's main column ends at y≈710 at `early` and y≈765 at `late`, so `early` is
  its emptiest state, not `late`.

---

## 3. The one idea worth keeping

**V3's lettered roster strip** — `QB [C] J. Allen · RB [B] Q. Judkins · WR [A] T. McMillan`, with
the five-word caption *"letters mark the slot each would fill"*.

It is the only element in either set that answers "which position?" without a number, a legend or a
comparison. It draws the position decision on the object the drafter already owns and already
trusts, it costs one line, and at `mid` it shows three candidates landing in three different slots —
which is the whole decision, pre-arithmetic, at a glance. It survives the position reordering
problem by construction: the slots never move, the letters do. It degrades honestly (at `late` all
three letters land in the same bench chip and the device goes quiet, which is the true statement).

Keep it in whatever survives, including V4, which currently has no equivalent.

Salvage from the variant I reject: V2's absence sentence — *"No tight end among the 24 this board
rates here; T. Warren holds the slot. A statement about the board, not the position."* That is the
best piece of absence copy anyone wrote in two rounds. Use it once.

---

## 4. What the set as a whole gets wrong

**It solved the comparison and then buried the answer in a second vocabulary.** ADJ §6 named the
missing subtraction as the headline; all four variants now perform it and get the arithmetic right
in every state. Then all four print the result as a pair of equal-weight figures under a word —
"order" — that the same screen uses to mean something else, and settle it with a verdict badge that
gives a measured-6%-worse criterion visual parity with the one that decides. The reader is handed
the comparison and a second ranking in the same breath. One word and one type weight away from
being finished.

**It designed for `mid` and audited for `mid`.** Every structural failure here lives at a pole.
`early` is where V2's doors occlude five names and where V1 hides 15 of 24 behind a scroll;
`late` is where V2 cannot fit seven rows, V1 cannot fit seven names, V3's comparison row goes
cross-position, and V2's headline loses the word "bench". The rationale's own "what `late` taught"
section lists seven lessons and misses all five of these, including the two that are plainly in the
PNGs it says were looked at. The harness improved — min-font, doc-scroll and rail-window probes are
all new and all good — and still has no occlusion check and does not assert on its own `scrollers`
output. The brief's sentence applies unchanged: assertions find what they were told to find.

**It never says why the `late` board is negative.** Three variants put "Bench · your starters are
set" one line from a −34.6 headline and none of them joins the two. The engine has the pieces
(`displacement_adj`, `fills_required_slot`) and nobody spent a sentence on it. That is the one place
where the set's commendable refusal to re-base the scale leaves the user holding a number they have
no way to read — and it is the state the owner will notice first, because it is the state where the
screen looks broken and is not.

**It is close.** V4 plus V3's roster strip, with F3, F8 and F11 fixed, is a surface I would put in
front of someone on a clock.
