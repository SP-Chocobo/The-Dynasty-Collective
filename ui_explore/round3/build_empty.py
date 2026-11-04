#!/usr/bin/env python3
"""#301: build the EMPTY-STATE front page -- what the app shows before any league is synced.

WHY THIS IS A SECOND PAGE AND NOT THE FIRST ONE WITH HOLES IN IT. `app.py` has exactly one
`st.stop()`, at 3667, guarded by `if not snapshot`. The five-option view picker and all five
views sit BELOW it, so in this state none of them is reachable and none of the front page's
roster claims -- lineup holes, bye damage, thin positions -- has anything to compute from. A page
that rendered those fields with absent stamps would be a dashboard of em dashes, which is the
absence contract (`#187`) used as an excuse rather than honoured: `#187` is for a quantity that
could not be measured, not for a quantity that does not yet have a subject.

So this page answers the question the state actually poses -- "is this thing ready, and what do I
do?" -- out of the only material available above the stop.

THE SPLIT IS THE DESIGN. Four manifest rows, two of them undated, and the two undated ones do NOT
mean what the two dated ones mean:

    on disk now        Draft Sharks Dynasty Rankings      71d
                       Draft Sharks Trade Value Chart     76d   -> grade "Aging"
    arrives on sync    Sleeper player database            never fetched on this machine
                       Sleeper season projections         never fetched

Before a sync those two absences are the EXPECTED state of a machine with no league. After one
they would be damage. Rendering them in a section whose heading says what they are waiting for is
the difference between a page that reports and a page that alarms -- and the stamp stays
`ABSENT -- <reason>` either way, so the basis is not corrupted to get the framing.

ONE HOME FOR THE CHROME. `esc`, `absent`, `stamp_kind`, `reason_of`, `num` and the style block
come from `build_front`, which already owns them and already derives the palette from
`design_system.root_css_block()`. Importing a sibling builder is slightly odd, and the
alternative was worse: a second copy of the absence marker would let the two states of one page
disagree about what an em dash means (`#126`).

    python3 ui_explore/round3/build_empty.py [fixture.json] [out.html]
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path.cwd()))
import design_system as ds

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_front import absent, esc, reason_of, stamp_kind, style_css

HERE = pathlib.Path(__file__).resolve().parent
FIX = pathlib.Path("ui_explore/empty_fixture.json")
OUT = HERE / "front_empty.html"


def _row(label, stamp, value_html):
    """One source row: name, then either its age or its reason.

    `stamp=None` means "do not label this row's basis" -- used where the SECTION HEADING already
    says what the rows are. Stamping every row under "Arrives when you sync" with the word
    `absent` repeats the heading and reads as damage, which is the one thing this page must not
    do to a state that is merely early.
    """
    kind = stamp_kind(stamp) if stamp is not None else "measured"
    mark = "" if kind == "measured" else f' <span class="prov">{esc(kind)}</span>'
    return (f'<div class="fact"><span class="k">{esc(label)}{mark}</span>'
            f'<span class="v">{value_html}</span></div>')


def build(fx):
    have = fx.get("have") or []
    on_sync = fx.get("on_sync") or []
    grade = fx.get("grade")
    worst = fx.get("worst_days")

    # The verdict sentence. It grades ONLY what is on disk -- an undated row has no age to
    # average in, and folding it in as a zero or as a maximum would be inventing a number
    # (#56: a bound is not a threshold, and this is not even a bound).
    if grade is None:
        verdict = absent(reason_of(fx.get("grade_basis")))
        verdict_tail = "nothing on disk carries a date, so there is nothing to grade"
    else:
        verdict = f'<b>{esc(grade)}</b>'
        n = ds.figure(worst, 0)
        verdict_tail = (f"oldest input on disk is {esc(n)} days old"
                        if n is not None else "age not recorded")

    have_rows = "".join(
        _row(r.get("label", "?"), r.get("basis"),
             (f'{esc(ds.figure(r.get("days"), 0))}d <span class="prov">{esc(r.get("as_of") or "")}</span>'
              if ds.figure(r.get("days"), 0) is not None
              else absent(reason_of(r.get("basis")))))
        for r in have)
    # THE REASON IS THE CONTENT HERE, SO IT IS NOT HIDDEN IN A TOOLTIP. `absent()` renders an em
    # dash carrying its reason in `title=`, which is right when a number is MISSING -- the dash
    # stands in for the figure and the tooltip explains it. These rows have no number missing:
    # the measurement has not been taken yet, and saying so in words is strictly more
    # informative than a dash someone has to hover. Keeping the `.absent` class keeps it marked
    # as not-a-figure; dropping the `tabindex` with it removes an 18px focus target that the tap
    # floor would otherwise flag, and costs nothing because the text is already visible.
    sync_rows = "".join(
        _row(r.get("label", "?"), None,
             f'<span class="absent">{esc(reason_of(r.get("basis")))}</span>')
        for r in on_sync)

    have_block = (f'<h2>On disk now</h2><div class="facts">{have_rows}</div>' if have_rows else
                  '<h2>On disk now</h2><p class="more">No dated source is loaded.</p>')
    sync_block = (f'<h2>Arrives when you sync</h2><div class="facts">{sync_rows}</div>'
                  if sync_rows else "")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Command Center</title>
<meta name="description" content="Before a league is synced: what the engine already has, what arrives on sync, and the one thing to do.">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&display=swap">
<style>
{style_css()}
</style></head>
<body>
<main class="page">
  <h1 class="wm">Gold Wyrm</h1>
  <p class="who">No league synced</p>

  <h2>Is this ready</h2>
  <div class="claim"><h3>{verdict}</h3><p>{esc(verdict_tail)}.</p></div>

  {have_block}
  {sync_block}

  <h2>Do this</h2>
  <div class="claim"><h3>{esc(fx.get("action") or "No action recorded.")}</h3>
    <p>{esc(fx.get("action_cost") or "")}</p></div>
</main>
</body></html>
"""


def main(argv=None):
    args = list(argv if argv is not None else sys.argv[1:])
    fix = pathlib.Path(args[0]) if args else FIX
    out = pathlib.Path(args[1]) if len(args) > 1 else OUT
    fx = json.loads(fix.read_text())
    out.write_text(build(fx))
    print(f"wrote {out} ({len(out.read_text())} bytes) from {fix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
