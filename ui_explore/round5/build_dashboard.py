#!/usr/bin/env python3
"""The dashboard, assembled from the round-4 explorations' solved rules (`#343`).

THE GRAFT, as the owner settled it. `deck` is the spine for FEEL; `threshold` supplies the
INTERACTION MODEL -- "an expansion of each module on the dashboard. a popout or pop-over, not
in-line" -- and its third state. Those are separable concerns, which is why picking one for look
and the other for behaviour is not a collage.

ONE RESPONSIVE PAGE, NOT A DESKTOP FILE AND A MOBILE FILE. Round 4 drew pairs and the brief
asked for pairs, and that was right for exploring. It is wrong to SHIP: two files for one design
are two homes for it (`#126`), and they drift silently -- `deck`'s own pair is what shipped
retired terminology on both halves, caught only when a committed-file scan finally ran over
`ui_explore/`. One page, two breakpoints, and the phone layout cannot fall out of step with the
desktop one because there is only one of them.

A GENERATOR, NOT HAND-AUTHORED HTML. Round 4's pages were drawn by hand and could assert
anything; this one renders `front_claims.compose`, so every claim on it is the engine's judgment
and the byte-identity guard can prove the committed page is what this file produces.

WHAT IS ON THE FRONT, and the ruling that decided it. Three things: the claim band, the checks
line, one freshness stamp. The test is not "is it real?" but "does it ask anything of me?" --
which is what removes `record` from the front page despite `team_standings` returning it cheaply.
Knowing you are 4-2 cannot be acted on and will say the same thing tomorrow. The front page is
not where true-but-inert facts go; truth is the floor, not the qualification.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

import design_system as ds
import front_claims as fc
import front_page as fp

FIX = pathlib.Path("ui_explore/front_fixture.json")
OUT = HERE / "dashboard.html"

#: THE SEVERITY RAMP, AND WHY IT RUNS DARK-TO-LIGHT RATHER THAN THE OBVIOUS WAY.
#: Every one of round 4's three independent designs failed non-text contrast on its chart --
#: five of six bars between 1.25:1 and 2.30:1 against a 3:1 floor, measured by three separate
#: adversaries sampling rendered pixels. Three designers, three constructions, one result, and
#: the shared cause is now measured rather than guessed: a LOW value drawn as a DARK gold cannot
#: clear the floor on a near-black ground. `line` is 1.27:1 and `line-2` is 1.73:1, which
#: brackets exactly what the adversaries found.
#:
#: So severity is encoded as BRIGHTNESS RISING, which is the only direction that works here, and
#: `_assert_ramp_is_visible` fails the build rather than trusting this comment.
SEVERITY = (("recede", "dim"), ("mid", "gold"), ("hot", "gold-b"))
NON_TEXT_FLOOR = 3.0


def _assert_ramp_is_visible():
    """A bar nobody can see is not a quiet bar, it is a missing one.

    This runs at BUILD time and raises, because the alternative is what happened in round 4: a
    chart shipped three times over with marks that did not render, and every designer compensated
    by putting a direct label on every bar -- which is the tell, not the fix. I also failed to
    verify this myself four separate times by eye and by probe before reading the markup instead.
    `design_system.contrast_ratio` is the instrument; an assertion is cheaper than a fifth
    attempt.
    """
    bad = [(name, token, ds.contrast_ratio(token, "bg"))
           for name, token in SEVERITY if ds.contrast_ratio(token, "bg") < NON_TEXT_FLOOR]
    if bad:
        raise SystemExit("severity ramp below the %.1f:1 non-text floor: %s"
                         % (NON_TEXT_FLOOR, bad))


TYPE_FLOOR_REM = 0.75          # 12px at a 16px root; the render gate's own floor


def _assert_type_floor():
    """No declared size under 12px, checked at BUILD time rather than hoped for.

    The prior pass failed this gate at 9.6px, and this file failed it twice before the first
    render: `nav h2` at .72rem, and the wordmark's DYNASTY line at .5em of the wordmark, which
    computes to 10.56px on desktop and 9.12px on the phone. The second is the instructive one --
    it is invisible to any check that reads declared sizes without resolving the em chain.
    SO SMALL TYPE IS DECLARED IN REM THROUGHOUT THIS FILE, which makes the floor verifiable with
    a regex instead of a browser, and this assertion the thing that enforces it.
    """
    import re
    css = CSS.format(sans=ds.FONT_SANS, mono=ds.FONT_MONO, display=ds.FONT_DISPLAY)
    under = sorted({float(m.group(1)) for m in re.finditer(r"font(?:-size)?:[^;}]*?([\d.]+)rem", css)
                    if float(m.group(1)) < TYPE_FLOOR_REM})
    if under:
        raise SystemExit(f"declared font sizes below the {TYPE_FLOOR_REM}rem floor: {under}")
    # An `em` font-size on small text defeats the check above, so it is refused outright.
    ems = [m.group(0) for m in re.finditer(r"font-size:\s*[\d.]+em", css)]
    if ems:
        raise SystemExit(f"small type must be declared in rem, not em, so the floor is "
                         f"checkable without a browser: {ems}")


#: The five rooms and the one dock. `BRIEF.md`'s own correction: the Prytaneum is NOT a sixth
#: view, it is `st.container(key="debate_dock")` rendered under every view. Every round-4 design
#: drew six identical doors and was wrong about one of them.
ROOMS = ("Matchup", "Roster Maintenance", "Draft Room", "League", "Import Audit")
DOCK = "The Prytaneum"


def esc(value) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def absent(reason: str) -> str:
    """The em dash carrying its reason. Never 0, never blank, never a reassuring default."""
    return (f'<span class="absent" tabindex="0" title="{esc(reason)}">&mdash;</span>')


# ---------------------------------------------------------------------------------------------
# THE CURRENCY STAMP -- the owner's ruling, and the one figure that does not yet obey it.
# ---------------------------------------------------------------------------------------------
#: `#341`: GRADING prices on points under the league's own scoring; TRADING keeps Draft Sharks
#: Dynasty Rankings trade value. `bye_collision` returns whatever currency its caller put in
#: `value`, and the fixture's caller puts `trade_value` there -- so this figure is dynasty asset
#: value, bucketed by a three-field format hint, and NOT this league's points. The ruling stands;
#: the conversion is unbuilt, because it waits on two sub-rulings that are the owner's (which
#: weeks a season-points grade sums, and what a partial-coverage floor means in the new currency).
#:
#: Until then the page SAYS SO. A figure whose currency is unstated is the `#336b` failure with a
#: unit instead of a rank: prose outrunning the function behind it. `#341` decided that the
#: currency is part of a basis and that no stamp carried one; this is that stamp.
CURRENCY_TRADE_VALUE = (
    "dynasty trade value, not this league's points. `bye_collision` prices whatever its caller "
    "supplies and this page supplies Draft Sharks Dynasty Rankings value, selected by a "
    "three-field format hint -- so a league's own bonuses never reach it. The ruling is that "
    "grading belongs in league points; that conversion is not built yet")


def currency_stamp(text: str) -> str:
    return (f'<span class="currency" tabindex="0" title="{esc(CURRENCY_TRADE_VALUE)}">'
            f'{esc(text)}</span>')


# ---------------------------------------------------------------------------------------------
# CLAIM PROSE AND ITS EXPANSION
# ---------------------------------------------------------------------------------------------
def claim_prose(c: dict) -> tuple[str, str]:
    """Headline and body for one claim. Indicative, never imperative; the week or the position is
    the subject and the app is never the subject (`VOICE.md` rules 1 and 2)."""
    kind = c["kind"]
    if kind == "hole":
        positions = c.get("positions") or []
        return ("No legal lineup",
                f'<b>{esc(len(positions))}</b> slot'
                f'{"s" if len(positions) != 1 else ""} no rostered player can fill: '
                f'{esc(", ".join(positions))}.')
    if kind == "bye":
        loss = ds.figure(c.get("worst_week_loss")) or "?"
        floor = "&ge;&thinsp;" if c.get("partial") else ""
        out = c.get("starters_out")
        # SAY THE MAGNITUDE AND ITS SCOPE, NOT A SUPERLATIVE (`VOICE.md` rule 7, corrected).
        # This read "Week 6 is the one that hurts" and the voice spec marked it keep. "The one
        # that hurts" is a superlative over an OBJECTIVE, true only under maximisation -- and in
        # the owner's chop league the week that hurts is the week that eliminates you, which
        # needs a last-place threshold this engine withholds the neighbours of. `byes_ahead`
        # picks by largest loss with NO term for distance, so it can name a week the reader may
        # never reach.
        return (f'Week <b>{esc(c["worst_week"])}</b> costs {floor}<b>{esc(loss)}</b>',
                f'the largest of the weeks still ahead, in {currency_stamp("trade value")}.'
                + (f' <b>{esc(out)}</b> starter{"s" if out != 1 else ""} out that week.'
                   if out else ""))
    if kind == "thin":
        count, covered = c.get("count") or 0, c.get("valued_count")
        band = c.get("label")
        # THE LABEL, NEVER A RANK (`#336b`). `depth_label` is a ratio band against the league
        # MEAN; nothing in this tree ranks teams within a position.
        rated = (f' Depth here rates <b>{esc(band)}</b> against this league\'s own rosters.'
                 if band else "")
        scope = (f' Only <b>{esc(covered)}</b> of {esc(count)} could be priced, so that '
                 f'comparison is a floor.' if c.get("priced_floor") else "")
        return (f'Thin at <b>{esc(c["position"])}</b>',
                f'<b>{esc(count)}</b> rostered.{rated}{scope}')
    return (esc(kind), "")


def expansion(c: dict, fx: dict) -> str:
    """The popout for one claim, or "" where the engine computes no second layer.

    RULE 2 OF EXPANSION, AND IT IS STRICT: what expands must be something the engine computes
    SEPARATELY. If opening a row would require this file to compute the detail, the detail is not
    expandable -- it is fabricated. Four of the five claim kinds pass. The injury flag does NOT:
    `is_material_injury_status` returns a BOOLEAN, there is no second layer, and a drill-down
    would have to invent severity. That is exactly where a designer would most want one.
    """
    kind = c["kind"]
    if kind == "bye":
        weeks = (fx.get("bye_profile") or {}).get("weeks") or {}
        rows = []
        losses = [v.get("value_lost") if isinstance(v, dict) else v for v in weeks.values()]
        peak = max([x for x in losses if isinstance(x, (int, float))] or [0]) or 1
        for wk in sorted(weeks, key=lambda w: int(w)):
            cell = weeks[wk]
            lost = cell.get("value_lost") if isinstance(cell, dict) else cell
            if not isinstance(lost, (int, float)):
                rows.append(f'<tr><th>Week {esc(wk)}</th><td colspan="2">'
                            f'{absent("this week carries no measured loss")}</td></tr>')
                continue
            share = lost / peak
            tone = SEVERITY[2][0] if share >= 0.75 else (
                SEVERITY[1][0] if share >= 0.35 else SEVERITY[0][0])
            rows.append(
                f'<tr><th>Week {esc(wk)}</th>'
                f'<td class="n">{esc(ds.figure(lost))}</td>'
                f'<td class="barcell"><span class="bar {tone}" '
                f'style="width:{max(2, round(share * 100))}%"></span></td></tr>')
        return (f'<p class="popnote">Every week with a measured bye cost, in '
                f'{currency_stamp("trade value")}. Each week is its own solve of the lineup with '
                f'that week\'s byes removed &mdash; eighteen separate results, not one number '
                f'spread out.</p>'
                f'<table class="weeks"><tbody>{"".join(rows)}</tbody></table>')
    if kind == "thin":
        count, covered = c.get("count") or 0, c.get("valued_count")
        return (f'<dl class="kv">'
                f'<dt>rostered</dt><dd class="n">{esc(count)}</dd>'
                f'<dt>priced</dt><dd class="n">{esc(covered) if covered is not None else absent("the merger priced none of this room")}</dd>'
                f'<dt>band</dt><dd>{esc(c.get("label") or "")}</dd>'
                f'</dl>'
                f'<p class="popnote">The band is a RATIO against this league\'s own mean, not a '
                f'rank. Nothing here orders teams within a position, so there is no "worst in '
                f'the league" to report.</p>')
    if kind == "hole":
        return ('<ul class="slots">' + "".join(
            f'<li>{esc(p)}</li>' for p in (c.get("positions") or [])) + '</ul>'
            + '<p class="popnote">A hole is a slot the solver leaves EMPTY, not a position '
              'missing from a filter. No amount of value fixes it.</p>')
    return ""


# ---------------------------------------------------------------------------------------------
# THE PAGE
# ---------------------------------------------------------------------------------------------
CSS = """
*{{box-sizing:border-box}}
html,body{{margin:0;background:var(--bg);color:var(--ink)}}
body{{font:400 1rem/1.55 {sans};-webkit-text-size-adjust:100%}}
.wrap{{max-width:46rem;margin:0 auto;padding:24px 16px 56px}}

/* ---- brand. Cinzel for the wordmark and top-level headings ONLY, never for data: its
   numerals are letterspaced and "11" reads as Roman "II". ---- */
.crest{{display:flex;align-items:center;gap:12px;margin:0 0 4px}}
.wyrm{{flex:0 0 auto}}
.word{{font:600 1.5rem/1 {display};letter-spacing:.11em;text-transform:uppercase;
  background:linear-gradient(176deg,#755024 0%,#ba9561 38%,#f9de99 68%,#fff4ce 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent}}
/* IN REM, NOT EM. At .5em of the wordmark this computed to 10.56px desktop and 9.12px on
   the phone -- under the 12px floor, and invisible to any check that reads declared sizes
   without resolving the em chain. Small type is declared in rem throughout this file so
   `_assert_type_floor` can verify the floor WITHOUT a browser. */
.word b{{display:block;font-size:.78rem;letter-spacing:.44em;font-weight:400;margin-top:6px}}
.seat{{color:var(--muted);font-size:.84rem;margin:0 0 22px;padding-left:46px}}
.seat .st{{color:var(--dim)}}

/* ---- the band. Severity by FRAME SHAPE, grafted from `keep`: the hole rung gets a solid left
   rule, the bye rung a thinner one, the thin rung none. It survives greyscale and forced
   colours, which a colour-only encoding does not. ---- */
.claims{{display:flex;flex-direction:column;gap:10px;margin:0 0 14px}}
.claim{{background:var(--surface);border:1px solid var(--line);border-radius:3px;
  padding:14px 16px;position:relative}}
.claim.hole{{border-left:4px solid var(--gold-b)}}
.claim.bye{{border-left:3px solid var(--gold)}}
.claim.thin{{border-left:1px solid var(--line-2)}}
.claim.none{{border-left:1px solid var(--line);text-align:left}}
.claim h3{{font:400 1.06rem/1.35 {sans};margin:0 0 5px;color:var(--ink)}}
.claim p{{margin:0;color:var(--muted);font-size:.9rem}}
/* SPLIT, because the two parents differ (1.06rem and .9rem) and one em value cannot be
   resolved statically for both. .95em was SAFE here at 13.68px -- the rule rejects it
   anyway, so that the floor stays checkable without a browser rather than case by case. */
.claim h3 b,.claim p b{{color:var(--ink);font-weight:600;font-family:{mono}}}
.claim h3 b{{font-size:1rem}}
.claim p b{{font-size:.86rem}}
.row{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:11px}}

/* ---- controls. 44px minimum, which is why these are padded rather than text-sized. ---- */
.btn{{display:inline-flex;align-items:center;min-height:44px;padding:0 14px;
  border:1px solid var(--line-2);border-radius:3px;background:var(--surface-2);
  color:var(--ink);font:400 .82rem/1 {sans};cursor:pointer;text-decoration:none}}
.btn:hover,.btn:focus-visible{{border-color:var(--gold);color:var(--gold-b)}}
.btn.route{{border-style:dashed;color:var(--muted)}}

/* ---- popovers, not inline disclosure. The owner's ruling: "a popout or pop-over, not in-line
   in the dashboard". Native `popover`, so it is an overlay with keyboard and escape handling
   and no script. ---- */
[popover]{{border:1px solid var(--line-2);background:var(--surface);color:var(--ink);
  border-radius:4px;padding:18px;max-width:min(32rem,92vw);
  box-shadow:0 18px 50px rgba(0,0,0,.72)}}
[popover]::backdrop{{background:rgba(4,3,2,.66)}}
[popover] h4{{font:400 1rem/1.3 {sans};margin:0 0 10px;color:var(--gold-b)}}
.popnote{{color:var(--dim);font-size:.78rem;margin:12px 0 0}}
.popclose{{margin-top:14px}}

/* ---- the week table. A table, because it is tabular, and the bar is a second encoding beside
   a readable number rather than the only encoding. ---- */
table.weeks{{width:100%;border-collapse:collapse;font-size:.84rem}}
.weeks th{{text-align:left;font-weight:400;color:var(--muted);padding:5px 10px 5px 0;
  white-space:nowrap}}
.weeks td{{padding:5px 0}}
.weeks td.n{{font-family:{mono};text-align:right;padding-right:12px;color:var(--ink);
  font-variant-numeric:tabular-nums}}
.barcell{{width:52%}}
.bar{{display:block;height:9px;border-radius:2px}}
.bar.recede{{background:var(--dim)}}
.bar.mid{{background:var(--gold)}}
.bar.hot{{background:var(--gold-b)}}

dl.kv{{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;margin:0;font-size:.86rem}}
dl.kv dt{{color:var(--muted)}}
dl.kv dd{{margin:0;color:var(--ink)}}
dl.kv dd.n{{font-family:{mono};font-variant-numeric:tabular-nums}}
ul.slots{{margin:0;padding-left:20px;font-size:.88rem}}

/* ---- the checks line. Most weeks this is the whole page. ---- */
.checks{{margin:0 0 20px;padding:12px 14px;border:1px dashed var(--line-2);border-radius:3px;
  color:var(--muted);font-size:.84rem}}
.checks b{{font-family:{mono};color:var(--ink)}}

.absent{{color:var(--dim);cursor:help;border-bottom:1px dotted var(--dim)}}
.currency{{color:var(--muted);cursor:help;border-bottom:1px dotted var(--gold)}}
.stamp{{font-size:.76rem;color:var(--dim)}}

/* ---- five rooms and one dock. Not six doors. ---- */
nav{{border-top:1px solid var(--line);margin-top:26px;padding-top:18px}}
nav h2{{font:400 .78rem/1 {sans};letter-spacing:.17em;text-transform:uppercase;
  color:var(--dim);margin:0 0 10px}}
.rooms{{display:flex;flex-wrap:wrap;gap:8px}}
.dock{{margin-top:14px;padding-top:14px;border-top:1px dashed var(--line)}}
.dock .stamp{{display:block;margin-top:7px}}

.close{{margin-top:20px}}
.close .btn{{border-color:var(--gold);color:var(--gold-b)}}

@media (max-width:460px){{
  .wrap{{padding:18px 16px 44px}}
  .seat{{padding-left:0}}
  .word{{font-size:1.2rem}}
  .barcell{{width:44%}}
}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
"""

WYRM = """<svg class="wyrm" width="34" height="34" viewBox="0 0 34 34" aria-hidden="true">
<defs><linearGradient id="g" x1="0" y1="0" x2=".3" y2="1">
<stop offset="0" stop-color="#755024"/><stop offset=".4" stop-color="#ba9561"/>
<stop offset=".72" stop-color="#f9de99"/><stop offset="1" stop-color="#fff4ce"/>
</linearGradient></defs>
<path d="M17 2a15 15 0 1 0 10.6 25.6" fill="none" stroke="url(#g)" stroke-width="2.4"
 stroke-linecap="round"/>
<path d="M17 8a9 9 0 1 1-6.4 15.3" fill="none" stroke="url(#g)" stroke-width="1.9"
 stroke-linecap="round" opacity=".82"/>
<circle cx="21.4" cy="10.6" r="1.9" fill="url(#g)"/>
</svg>"""


def build(fx: dict) -> str:
    """One responsive page, rendered from `front_claims.compose`'s judgment."""
    _assert_ramp_is_visible()
    _assert_type_floor()
    band = fc.compose(fx)
    shown, hidden = band["shown"], band["hidden"]
    summary = fc.checks_summary(band["checks"])
    basis = (fx.get("_provenance") or {}).get("basis") or {}

    # ---- the band, each claim with its popout where the engine computes one ------------------
    cards = []
    for i, c in enumerate(shown):
        head, body = claim_prose(c)
        exp, pid = expansion(c, fx), f"exp{i}"
        controls = [f'<a class="btn route" href="#{esc(c["route"].lower().replace(" ", "-"))}">'
                    f'{esc(c["route"])} &rsaquo;</a>']
        if exp:
            controls.insert(0, f'<button class="btn" popovertarget="{pid}">What it is made of'
                               f'</button>')
        pop = (f'<div id="{pid}" popover><h4>{head}</h4>{exp}'
               f'<div class="popclose"><button class="btn" popovertarget="{pid}" '
               f'popovertargetaction="hide">Close</button></div></div>') if exp else ""
        cards.append(f'<article class="claim {esc(c["kind"])}"><h3>{head}</h3><p>{body}</p>'
                     f'<div class="row">{"".join(controls)}</div></article>{pop}')

    if not cards:
        # THE QUIET STATE IS THE PRIMARY DESIGN, not an empty state to apologise for. `VOICE.md`
        # rule 8: leaving is a success state. The brief's test is whether a person can tell in
        # three seconds that they may close the app, and `threshold`'s CLOSE THE APP control --
        # the best single idea in the whole prior round -- turns that test into an affordance.
        cards.append('<article class="claim none"><h3>Nothing open this week</h3>'
                     '<p>No unfillable slot, no bye week still ahead with a measured cost, no '
                     'position thin against this league.</p></article>')

    more = (f'<p class="stamp">Also standing: '
            + ", ".join(esc(claim_prose(c)[0].replace("<b>", "").replace("</b>", ""))
                        for c in hidden) + ".</p>") if hidden else ""

    # ---- the checks line. DERIVED, never a hardcoded list (`#338`) ---------------------------
    if summary["all_clean"]:
        checks = (f'<b>{summary["ran"]}</b> checks, all clean &mdash; '
                  f'{esc(", ".join(summary["clean"]))}.')
    else:
        bits = []
        if summary["clean"]:
            bits.append(f'Clean: {esc(", ".join(summary["clean"]))}.')
        for check in band["checks"]:
            if check["state"] == fc.CHECK_ABSENT:
                bits.append(f'{esc(check["name"]).title()} {absent(check["reason"])}.')
        checks = " ".join(bits) or "Nothing was examined."

    # ---- the seat line. Absences carry their reason, never a reassuring default --------------
    team = fx.get("team")
    league_name = fx.get("league_name")
    name_html = (esc(league_name) if league_name
                 else absent(fp.reason_of(basis.get("league_name", "")) or
                             "this capture carries no league name"))
    week = fx.get("current_week")
    week_html = (f'week <b>{esc(week)}</b>' if week is not None
                 else absent(fp.reason_of(basis.get("current_week", "")) or
                             "no season position was read"))
    seat = (f'<p class="seat">{name_html} <span class="st">&middot;</span> {esc(team or "")} '
            f'<span class="st">&middot;</span> {week_html}</p>')

    rooms = "".join(f'<a class="btn" href="#{esc(r.lower().replace(" ", "-"))}">{esc(r)}</a>'
                    for r in ROOMS)
    close = ('<div class="close"><button class="btn" popovertarget="bye-note">Close the app'
             '</button></div>'
             '<div id="bye-note" popover><h4>Nothing is waiting</h4>'
             '<p class="popnote">Every check this page runs came back clean. It will keep the '
             'ledger while you are gone.</p>'
             '<div class="popclose"><button class="btn" popovertarget="bye-note" '
             'popovertargetaction="hide">Close</button></div></div>') if summary["all_clean"] else ""

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
{css}
</style>
</head><body>
<main class="wrap">
  <div class="crest">{WYRM}<h1 class="word">Gold Wyrm<b>Dynasty</b></h1></div>
  {seat}
  <div class="claims">{"".join(cards)}</div>
  {more}
  <p class="checks">{checks}</p>
  {close}
  <nav>
    <h2>Rooms</h2>
    <div class="rooms">{rooms}</div>
    <div class="dock">
      <a class="btn" href="#prytaneum">{esc(DOCK)}</a>
      <span class="stamp">A dock rendered under every room, not a sixth room.</span>
    </div>
  </nav>
</main>
</body></html>
"""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    fix = pathlib.Path(argv[0]) if argv else FIX
    out = pathlib.Path(argv[1]) if len(argv) > 1 else OUT
    out.write_text(build(json.loads(fix.read_text())))
    print(f"{out}  {len(out.read_text()):,} bytes  from {fix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
