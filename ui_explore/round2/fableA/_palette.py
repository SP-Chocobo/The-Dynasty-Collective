#!/usr/bin/env python3
"""How far the prototype palette has drifted from the app's own design system, in dE.

The second convergence pass. The first (_converge.py) asks whether the desktop and the phone
are one interface; this one asks whether that interface is the APP's interface, and it answers
in CIE Lab dE rather than by eye, because "close enough" is not a measurement and two surfaces
that each look fine alone are exactly the pair that drifts.

TWO INSTRUMENTS, NEITHER OF THEM NEW. The tokens come from `design_system.TOKENS`, which is the
only place the app's hex values are spelled out -- `root_css_block()` renders that dict and
every consumer calls it, so the app's palette cannot drift by copying. The dE comes from
`test_design_system._delta_e`, which is where that function already lives, deliberately: its own
docstring says perceptual SEPARATION is a property the palette must hold and is therefore
checked in the test, while contrast is a fact the module itself states. Importing from the test
rather than re-deriving the formula is the #126 rule applied to the instrument instead of to the
quantity -- a second Lab conversion in this file would be a second source of truth about colour.

WHAT A NUMBER HERE MEANS. dE is perceptual distance: ~1 is the just-noticeable threshold under
ideal conditions, and the app's own palette work treats 35 as the comfortable separation between
two tokens that must never be confused and records anything under ~26 as a squeeze. So for the
SAME token name on two surfaces, a dE of 0 is convergence and anything above about 2 is a
visible difference a reader could catch with both surfaces in front of them.

WHAT IT MEASURED ON ITS FIRST RUN, kept here because an instrument should carry its own number
-- a reader who opens this file should not have to go to a commit message to find out what it
found, and the figure in a brief is a quotation rather than a record.

    37 prototype tokens, 29 app tokens, 27 share a name
    26 of 27 shared names carry a visibly different colour (dE > 2); NONE are identical

      18.37  violet     #6d3fd6 -> #9457d4        3.71  bg         #0c0a07 -> #15120b
      16.20  sky        #1356c9 -> #1466c4        4.58  surface    #17130d -> #1f1a11
      15.15  emerald    #0b8f57 -> #1a9e4b        3.51  surface-2  #120f0a -> #1a1610
       7.57  dim        #897c61 -> #776d5a        2.41  ink        #f2ead9 -> #ece3d2

IT CORRECTED A CLAIM MADE WITHOUT IT. A design note had said the prototype shares the app's three
grounds, written from reading the two files and seeing similar-looking hex. It does not: the
prototype's grounds are measurably darker, and not one of the twenty-seven shared names is the
same colour. That is the whole argument for having this file rather than an opinion.

The position pills diverge further, and there the difference is a CAPABILITY rather than a
preference: the app's POSITION_PILL_TOKENS has six entries and falls back to K's neutral for
anything unmapped, so an IDP league draws DL, LB and DB in one colour where the prototype gives
each a hue. Two of the fixture's six formats are IDP leagues.

And the three FACES are identical, Cinzel included -- which settled a question that had been
posed backwards. design_system.py already defines FONT_DISPLAY with a written rule ("the wordmark
and top-level headings ONLY -- never for data"); the prototype follows it on door headers, and
app.py is the side not using its own token. Nothing to adopt, nothing to drop.

Run from the repo root:
    python3 ui_explore/round2/fableA/_palette.py
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import design_system as ds
from test_design_system import _delta_e, _rgb

CSS = pathlib.Path(__file__).resolve().parent / "_src" / "shared.css"
HEX = re.compile(r"--([a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,8})")


def proto_tokens():
    """The prototype's :root tokens. Comments in that file carry hex values too (the --dim
    derivation quotes three of them), so only the first :root block is read, and only
    declarations -- a hex inside a /* */ never becomes a token."""
    text = CSS.read_text()
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    i = text.find(":root")
    assert i >= 0, "no :root in shared.css"
    block = text[i: text.find("}", i)]
    return dict(HEX.findall(block))


def main():
    p, a = proto_tokens(), ds.TOKENS
    shared = sorted(set(p) & set(a))
    rows = []
    for k in shared:
        pv, av = p[k].lower(), a[k].lower()
        rows.append((_delta_e(p[k], a[k]), k, pv, av))
    rows.sort(reverse=True)

    print(f"{len(p)} prototype tokens, {len(a)} app tokens, {len(shared)} share a name\n")
    print(f"{'dE':>6}  {'token':<12} {'prototype':<10} {'app':<10}")
    print(f"{'-'*6}  {'-'*12} {'-'*10} {'-'*10}")
    for de, k, pv, av in rows:
        mark = "  <-- same name, different colour" if de > 2 else ("" if de else "  identical")
        print(f"{de:6.2f}  {k:<12} {pv:<10} {av:<10}{mark}")

    moved = [r for r in rows if r[0] > 2]
    print(f"\n{len(moved)} of {len(shared)} shared token names carry a visibly different colour "
          f"(dE > 2); {sum(1 for r in rows if r[0] == 0)} are identical.")

    only_p, only_a = sorted(set(p) - set(a)), sorted(set(a) - set(p))
    print(f"\nprototype only ({len(only_p)}): {' '.join(only_p)}")
    print(f"app only       ({len(only_a)}): {' '.join(only_a)}")

    # The POSITION pills, which the app keeps in their own dict rather than in TOKENS, so the
    # "prototype only" list above reports them as absent when they are merely elsewhere.
    print("\n--- position pills ---")
    pos = {k.upper(): v for k, v in p.items() if k.upper() in
           ("QB", "RB", "WR", "TE", "K", "DEF", "DL", "LB", "DB", "IDP")}
    app_pos = ds.POSITION_PILL_TOKENS
    for k in sorted(set(pos) | set(app_pos)):
        if k in pos and k in app_pos:
            de = _delta_e(pos[k], app_pos[k])
            print(f"  {de:6.2f}  {k:<4} prototype {pos[k]:<9} app {app_pos[k]:<9}"
                  f"{'  <-- different hue' if de > 10 else ''}")
        elif k in pos:
            print(f"  {'--':>6}  {k:<4} prototype {pos[k]:<9} app (no entry; falls back to the "
                  f"neutral {ds.POSITION_PILL_TOKENS.get('K')} that K uses)")
        else:
            print(f"  {'--':>6}  {k:<4} prototype (absent)  app {app_pos[k]}")

    # The faces, which are the other half of a palette and are stated in the same module.
    print("\n--- faces ---")
    text = re.sub(r"/\*.*?\*/", "", CSS.read_text(), flags=re.S)
    i = text.find(":root"); block = text[i: text.find("}", i)]
    for var, name, app_val in (("--f-s", "sans", ds.FONT_SANS),
                               ("--f-m", "mono", ds.FONT_MONO),
                               ("--f-d", "display", ds.FONT_DISPLAY)):
        m = re.search(re.escape(var) + r"\s*:\s*([^;]+);", block)
        got = (m.group(1).strip() if m else "(absent)")
        first = lambda s: s.split(",")[0].strip().strip("\"'")
        same = "same first face" if m and first(got) == first(app_val) else "DIFFERENT first face"
        print(f"  {name:<8} prototype {first(got):<14} app {first(app_val):<14} {same}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
