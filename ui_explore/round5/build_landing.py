#!/usr/bin/env python3
"""THE LANDING PAGE (`#344`) -- which of my leagues needs me, and which want nothing.

WHY THIS IS A SEPARATE PAGE AND NOT A WIDER DASHBOARD. The owner's correction, and it is the
whole reason this file exists:

    i like deck more still. i think youre confounding the landing page with the deck dashboard,
    just recreating the same information type without addressing the need for the landing page

That was right. `deck` is the IN-LEAGUE dashboard -- one league, deep -- and `build_dashboard.py`
rebuilt that same job slightly worse while the surface that actually did not exist stayed
undrawn. These answer different questions and therefore want different shapes:

    dashboard   ONE league, many facts     -> panels with internal grids, a ledger, density
    landing     MANY leagues, one fact each -> a LIST, one line per league, scannable at twenty

A landing page built as a dashboard is a dashboard with twelve of everything, which is the
failure the standing constraint names: as much on the screen as you can fit.

IT IS THE CLAIM BAND AT A DIFFERENT ARITY. `front_claims.compose` per league; the LADDER orders
the rungs; `CAP` is irrelevant here because each league contributes exactly one line. No new
engine concept, and `ui_explore/round5/STRUCTURE.md` argues the rest.

THE ORDER IS BY RUNG, NEVER BY FIGURE. A hole is a hole in any league, so the RUNG compares.
A bye costing 95 in one league and 95 in another does NOT compare: `bye_collision` prices in
whatever currency its caller supplies, each league applies its own scoring, and
`set_league_format` selects a different rankings export per format -- so two leagues' figures are
different units wearing the same label (`#341`). Ordering twelve leagues by a number would be the
most confident wrong thing this surface could do.

THE HEADLINE IS A COUNT, NEVER A GRADE. "Ten of twelve leagues have something open" is a count of
real things. A portfolio score, a worst-league ranking, or a cross-league total are all
unreachable, and this is the page where they are most tempting -- its natural shape is N rows
plus a summary, and that shape begs for a summary that cannot exist.
"""
from __future__ import annotations

import glob
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

import design_system as ds
import front_claims as fc
# ONE HOME for the shared render vocabulary (`#126`): the escaper, the absence grammar, the
# currency stamp, the position pill, the brand mark and both build-time assertions all live in
# the dashboard builder and are imported rather than copied.
from build_dashboard import (WYRM, _assert_ramp_is_visible, _assert_type_floor, absent,
                             claim_parts, esc, pill)

SEATS = "ui_explore/seats/seat*.json"
OUT = HERE / "landing.html"

#: THE STAND-IN, STAMPED. These twelve "leagues" are twelve SEATS of one replayed battery league
#: on one clock. Real leagues differ in format, scoring and bye schedule; these share all three,
#: which is why every row's rung looks alike. It is a drawing of the LAYOUT, not a measurement of
#: a portfolio, and saying so on the page is the difference between a constructed fixture and a
#: fabricated claim (`#187`).
STANDIN = ("twelve seats of one replayed league, on one clock, standing in for twelve leagues. "
           "Real leagues differ in format, scoring and bye schedule; these do not, so the spread "
           "of rungs here is narrower than a real portfolio's")

RUNG_ORDER = {kind: i for i, (kind, _) in enumerate(fc.LADDER)}


def league_rows(paths):
    """`compose` per league, ordered by RUNG then by how much is open."""
    rows = []
    for path in paths:
        fx = json.loads(pathlib.Path(path).read_text())
        band = fc.compose(fx)
        summary = fc.checks_summary(band["checks"])
        shown, hidden = band["shown"], band["hidden"]
        rows.append({"fx": fx, "shown": shown, "open": len(shown) + len(hidden),
                     "summary": summary,
                     "top": shown[0] if shown else None,
                     "rung": RUNG_ORDER.get(shown[0]["kind"], 99) if shown else 99})
    rows.sort(key=lambda r: (r["rung"], -r["open"], str(r["fx"].get("team"))))
    return rows


CSS = """
*{{box-sizing:border-box}}
html,body{{margin:0;background:var(--bg);color:var(--ink)}}
body{{font:400 .95rem/1.55 {sans};-webkit-text-size-adjust:100%}}
.wrap{{max-width:66rem;margin:0 auto;padding:0 20px 64px}}

.top{{display:flex;align-items:center;gap:22px;padding:18px 0;
  border-bottom:1px solid var(--line);flex-wrap:wrap}}
.crest{{display:flex;align-items:center;gap:12px}}
.word{{font:600 1.32rem/1 {display};letter-spacing:.11em;text-transform:uppercase;margin:0;
  background:linear-gradient(176deg,#755024 0%,#ba9561 38%,#f9de99 68%,#fff4ce 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent}}
.word b{{display:block;font-size:.76rem;letter-spacing:.42em;font-weight:400;margin-top:5px}}
.top .stamp{{margin-left:auto;text-align:right;max-width:30rem}}

/* ---- the verdict: a COUNT, never a grade ---- */
.verdict{{display:grid;grid-template-columns:auto 1fr;gap:26px;align-items:center;
  margin:26px 0 20px;padding:24px 28px;border:1px solid var(--line-2);border-radius:6px;
  background:linear-gradient(180deg,var(--surface),var(--surface-2));position:relative;
  overflow:hidden}}
.verdict::before{{content:"";position:absolute;inset:0 auto 0 0;width:170px;pointer-events:none;
  background:repeating-linear-gradient(135deg,transparent 0 4px,rgba(176,162,138,.06) 4px 5px);
  mask-image:linear-gradient(90deg,#000,transparent)}}
.tally{{font:600 3.5rem/1 {mono};color:var(--gold-b);letter-spacing:-.03em;position:relative;
  font-variant-numeric:tabular-nums;white-space:nowrap}}
.tally s{{font-size:1.5rem;color:var(--dim);text-decoration:none;margin-left:4px}}
.verdict h1{{font:400 1.68rem/1.2 {display};color:var(--gold-b);margin:0 0 8px;position:relative}}
.verdict p{{margin:0;color:var(--muted);font-size:.9rem;position:relative;max-width:58ch}}
.eyebrow{{font:600 .78rem/1 {display};letter-spacing:.22em;text-transform:uppercase;
  color:var(--gold);margin:0 0 9px}}

/* ---- THE LIST. One line per league, which is what makes twenty scannable. The dashboard's
   panels would become twenty panels; this is the shape difference the owner named. ---- */
.leagues{{border:1px solid var(--line);border-radius:6px;overflow:hidden;
  background:linear-gradient(180deg,var(--surface),var(--surface-2))}}
.lrow{{display:grid;grid-template-columns:5px 14rem 1fr auto auto;gap:0 18px;align-items:center;
  padding:0;border-bottom:1px solid var(--line);text-decoration:none;color:inherit}}
.lrow:last-child{{border-bottom:0}}
.lrow:hover,.lrow:focus-visible{{background:rgba(117,80,36,.1)}}
.rail{{align-self:stretch}}
.lrow.hole .rail{{background:var(--gold-b)}}
.lrow.bye  .rail{{background:var(--gold)}}
.lrow.thin .rail{{background:var(--tie-b)}}
.lrow.quiet .rail{{background:var(--status-ok);opacity:.5}}
.lid{{padding:16px 0 16px 18px}}
.lname{{font:400 1rem/1.25 {sans};color:var(--ink);margin:0}}
.lmeta{{font:400 .78rem/1.4 {mono};color:var(--dim);margin:3px 0 0}}
.lclaim{{padding:16px 0;display:flex;align-items:center;gap:10px;flex-wrap:wrap;min-width:0}}
.lclaim .txt{{font-size:.9rem;color:var(--muted)}}
.lclaim .txt b{{color:var(--ink);font-family:{mono};font-weight:600;font-size:.86rem}}
.lclaim.q .txt{{color:var(--dim)}}
.tick{{color:var(--status-ok)}}
.more{{font:400 .78rem/1 {display};letter-spacing:.12em;text-transform:uppercase;
  color:var(--dim);white-space:nowrap;padding:16px 0}}
.go{{padding:16px 18px 16px 0;color:var(--gold);font-size:1.1rem}}
.pill{{display:inline-flex;align-items:center;height:21px;padding:0 8px;border-radius:3px;
  font:600 .76rem/1 {mono};letter-spacing:.04em;flex:0 0 auto}}

.foot{{display:flex;gap:26px;flex-wrap:wrap;margin-top:18px;font-size:.82rem;color:var(--muted)}}
.foot b{{font-family:{mono};color:var(--ink);font-weight:600}}
.stamp{{font:400 .78rem/1.5 {sans};color:var(--dim)}}
.absent{{color:var(--dim);cursor:help;border-bottom:1px dotted var(--dim)}}
.currency{{color:var(--muted);cursor:help;border-bottom:1px dotted var(--gold)}}

@media (max-width:760px){{
  .verdict{{grid-template-columns:1fr;gap:14px}}
  .lrow{{grid-template-columns:4px 1fr auto;row-gap:0}}
  .lid{{padding:14px 0 0 16px}}
  .lclaim{{grid-column:2/4;padding:6px 16px 14px 0}}
  .more{{padding:14px 0 0}}
  .go{{display:none}}
}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
"""


def build(paths) -> str:
    _assert_ramp_is_visible()
    _assert_type_floor()
    rows = league_rows(paths)
    total = len(rows)
    open_n = sum(1 for r in rows if r["shown"])
    quiet = [r for r in rows if not r["shown"]]

    items = []
    for r in rows:
        fx, top = r["fx"], r["top"]
        team = esc(fx.get("team") or "")
        lname = fx.get("league_name")
        fmt = ((fx.get("_provenance") or {}).get("format") or "")
        # THE ROW MUST HAVE A NAME. When the league name is absent, the TEAM becomes the
        # identifier and the absence drops to the meta line -- it does not take the headline.
        # The first render put a bare em dash at the top of all twelve rows, so the most
        # prominent thing on a page about choosing a league was the thing that was missing.
        # An absence is information, and information that is identical on every row is noise.
        ident = esc(lname) if lname else esc(team)
        # AND THE ABSENCE IS STATED ONCE, NOT TWELVE TIMES. Every row shares the same missing
        # league name, so repeating it per row wrapped the meta line onto two and put the same
        # non-fact twelve times on a page whose job is to differentiate leagues. The standing
        # constraint is exactly this: clean dissemination, not every variable everywhere. The
        # absence still carries its reason -- once, in the header, where it is true of the whole
        # capture rather than of any one row.
        sub = (f'{team} &middot; {esc(fmt)}' if lname else esc(fmt))
        if top is None:
            kind, body = "quiet", (
                f'<span class="tick">&check;</span><span class="txt">Nothing open. '
                f'{r["summary"]["ran"]} checks, all clean &mdash; '
                f'{esc(", ".join(r["summary"]["clean"]))}.</span>')
            more = ""
        else:
            parts = claim_parts(top)
            pos = top.get("position") or (top.get("positions") or [None])[0]
            kind = top["kind"]
            body = ((pill(pos) if pos else "")
                    + f'<span class="txt">{parts["headline"]} &middot; '
                      f'<b>{parts["figure"]}</b> {parts["unit"]}</span>')
            extra = r["open"] - 1
            more = f'<span class="more">+{extra} more</span>' if extra else ""
        items.append(
            f'<a class="lrow {kind}" href="#{esc(str(team).lower().replace(" ", "-"))}">'
            f'<span class="rail"></span>'
            f'<span class="lid"><p class="lname">{ident}</p>'
            f'<p class="lmeta">{sub}</p></span>'
            f'<span class="lclaim{" q" if top is None else ""}">{body}</span>'
            f'{more}<span class="go">&rsaquo;</span></a>')

    quiet_line = ("" if not quiet else
                  " Quiet: " + ", ".join(esc(r["fx"].get("team") or "") for r in quiet) + ".")
    css = CSS.format(sans=ds.FONT_SANS, mono=ds.FONT_MONO, display=ds.FONT_DISPLAY)
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gold Wyrm Dynasty</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap">
<style>
{ds.root_css_block()}
{ds.position_pill_css_block()}
{css}
</style>
</head><body>
<div class="wrap">
  <header class="top">
    <span class="crest">{WYRM}<h1 class="word">Gold Wyrm<b>Dynasty</b></h1></span>
    <span class="stamp">{absent(STANDIN)} constructed stand-in data &middot;
      {"no league names in this capture" if not any(r["fx"].get("league_name") for r in rows) else ""}</span>
  </header>

  <section class="verdict">
    <div class="tally">{open_n}<s>/{total}</s></div>
    <div>
      <p class="eyebrow">Across your leagues</p>
      <h1>{open_n} of {total} have something open.</h1>
      <p>Ordered by what KIND of thing is open, never by its size &mdash; a hole is a hole in
      any league, but two leagues' point figures are different units wearing the same label.
      {quiet_line}</p>
    </div>
  </section>

  <div class="leagues">{"".join(items)}</div>

  <div class="foot">
    <span>leagues <b>{total}</b></span>
    <span>something open <b>{open_n}</b></span>
    <span>nothing open <b>{len(quiet)}</b></span>
  </div>
  <p class="stamp" style="margin-top:14px">A count of real things, never a score. No portfolio
  grade, no worst-league ranking and no cross-league total exists to show.</p>
</div>
</body></html>
"""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    paths = sorted(glob.glob(argv[0] if argv else SEATS))
    out = pathlib.Path(argv[1]) if len(argv) > 1 else OUT
    if not paths:
        raise SystemExit(f"no league fixtures matched {argv[0] if argv else SEATS}")
    out.write_text(build(paths))
    print(f"{out}  {len(out.read_text()):,} bytes  from {len(paths)} leagues")
    return 0


if __name__ == "__main__":
    sys.exit(main())
