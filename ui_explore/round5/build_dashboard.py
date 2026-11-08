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
def claim_parts(c: dict) -> dict:
    """`{eyebrow, figure, unit, headline, body}` for one claim.

    THE FIGURE IS THE HERO, which is the structural correction this page needed. The first pass
    buried every number inside a sentence at 13.76px and the owner's verdict was "too spartan ...
    uninspiring font usage/sizing". `deck` -- the design chosen for feel -- carries its figures in
    `.big`: 44px mono, gold-bright, negative tracking. A triage surface must read at a GLANCE,
    and a glance reads a number, not a clause.

    The eyebrow is the device `deck` uses thirteen times: Cinzel, uppercase, heavily letterspaced.
    It names the KIND of claim, so the headline can be the subject and the body the
    qualification -- three tiers rather than one run-on sentence.

    MONO FOR EVERY FIGURE, NEVER THE DISPLAY FACE. `design_system.FONT_DISPLAY` carries a written
    rule -- brand voice, never for data -- and Cinzel's letterspaced numerals turn "11" into
    Roman "II".
    """
    kind = c["kind"]
    if kind == "hole":
        positions = c.get("positions") or []
        return {"eyebrow": "No legal lineup",
                "figure": str(len(positions)),
                "unit": "slot" + ("s" if len(positions) != 1 else ""),
                "headline": esc(", ".join(positions)) or "&mdash;",
                "body": "No rostered player can fill these. No amount of value fixes it."}
    if kind == "bye":
        loss = ds.figure(c.get("worst_week_loss")) or "?"
        floor = "&ge;&thinsp;" if c.get("partial") else ""
        out = c.get("starters_out")
        # SAY THE MAGNITUDE AND ITS SCOPE, NOT A SUPERLATIVE (`VOICE.md` rule 7, corrected).
        # "The one that hurts" is a superlative over an OBJECTIVE, true only under maximisation;
        # in the owner's chop league the week that hurts is the week that eliminates you, which
        # needs a last-place threshold this engine withholds the neighbours of.
        return {"eyebrow": "Bye damage",
                "figure": f"{floor}{esc(loss)}",
                "unit": currency_stamp("trade value"),
                "headline": f'Week <b>{esc(c["worst_week"])}</b>',
                "body": ("The largest of the weeks still ahead."
                         + (f' <b>{esc(out)}</b> starter{"s" if out != 1 else ""} out that week.'
                            if out else ""))}
    if kind == "thin":
        count, covered = c.get("count") or 0, c.get("valued_count")
        band = c.get("label")
        # THE LABEL, NEVER A RANK (`#336b`). `depth_label` is a ratio band against the league
        # MEAN, and nothing in this tree ranks teams within a position.
        rated = (f"Depth here rates <b>{esc(band)}</b> against this league's own rosters."
                 if band else "")
        scope = (f' Only <b>{esc(covered)}</b> of {esc(count)} could be priced, so that '
                 f'comparison is a floor.' if c.get("priced_floor") else "")
        return {"eyebrow": "Thin room",
                "figure": esc(count),
                "unit": "rostered",
                "headline": esc(c["position"]),
                "body": (rated + scope).strip()}
    return {"eyebrow": esc(kind), "figure": "", "unit": "", "headline": esc(kind), "body": ""}


def claim_headline(c: dict) -> str:
    """Plain text for the capped-out list, with no markup to strip downstream."""
    parts = claim_parts(c)
    return f'{parts["eyebrow"]}: {parts["headline"].replace("<b>", "").replace("</b>", "")}'


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
body{{font:400 1rem/1.6 {sans};-webkit-text-size-adjust:100%}}
.wrap{{max-width:50rem;margin:0 auto;padding:40px 20px 72px}}

/* ---- THE TYPE SCALE, with real jumps. A measured correction: the first pass of this page put
   ELEVEN sizes between 12.16px and 24px -- a 1.97:1 range -- which reads as "everything is the
   same size" no matter how correct the content is. `deck`, the design the owner chose for feel,
   spans 12px to 44px with deliberate jumps at 22, 30 and 44. The brief's own rule is RESTRAINT
   IN INFORMATION, GENEROSITY IN CRAFT, and the first pass cut the craft along with the
   information -- the exact failure the brief was written to prevent. ---- */
.eyebrow{{font:600 .78rem/1 {display};letter-spacing:.22em;text-transform:uppercase;
  color:var(--gold);margin:0 0 10px}}
.big{{font:600 2.75rem/1 {mono};letter-spacing:-.02em;color:var(--gold-b);
  font-variant-numeric:tabular-nums;display:block}}
.big .u{{font-size:.95rem;letter-spacing:.14em;text-transform:uppercase;color:var(--dim);
  font-family:{display};margin-left:10px;vertical-align:.42em}}
.n{{font:600 1.375rem/1 {mono};color:var(--ink);font-variant-numeric:tabular-nums}}

/* ---- brand. Cinzel carries the wordmark and every LABEL; figures are always mono, because
   Cinzel's numerals are letterspaced and "11" reads as Roman "II". ---- */
.crest{{display:flex;align-items:center;gap:14px;margin:0 0 6px}}
.word{{font:600 1.75rem/1 {display};letter-spacing:.12em;text-transform:uppercase;margin:0;
  background:linear-gradient(176deg,#755024 0%,#ba9561 38%,#f9de99 68%,#fff4ce 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent}}
.word b{{display:block;font-size:.78rem;letter-spacing:.44em;font-weight:400;margin-top:8px}}
/* the logo's own device: a hairline with a diamond, fading out rather than stopping dead */
.orn{{display:flex;align-items:center;gap:10px;margin:0 0 26px}}
.orn i{{height:1px;flex:1;background:linear-gradient(90deg,rgba(117,80,36,.55),
  rgba(117,80,36,.04))}}
.orn i:last-child{{background:linear-gradient(270deg,rgba(117,80,36,.55),rgba(117,80,36,.04))}}
.orn s{{width:5px;height:5px;background:var(--gold);transform:rotate(45deg);flex:0 0 auto}}
.seat{{font:400 .82rem/1.5 {display};letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted);margin:0;text-align:center}}
.seat .st{{color:var(--line-2)}}

/* ---- the band. Surfaces are vertical GRADIENTS, not flat fills, and severity is carried by
   FRAME WEIGHT as well as colour so it survives greyscale and forced-colours. ---- */
.claims{{display:flex;flex-direction:column;gap:14px;margin:0 0 18px}}
.claim{{background:linear-gradient(180deg,var(--surface),var(--surface-2));
  border:1px solid var(--line);border-left-width:1px;border-radius:5px;padding:22px 24px;
  position:relative;overflow:hidden}}
/* a 45-degree hatch at low opacity, bled from the left edge -- texture, not decoration: it is
   what keeps a near-black panel from reading as an empty div */
.claim::before{{content:"";position:absolute;inset:0 auto 0 0;width:92px;pointer-events:none;
  background:repeating-linear-gradient(135deg,transparent 0 3px,rgba(176,162,138,.07) 3px 4px);
  mask-image:linear-gradient(90deg,#000,transparent)}}
.claim.hole{{border-left:4px solid var(--gold-b)}}
.claim.bye{{border-left:3px solid var(--gold)}}
.claim.thin{{border-left:2px solid var(--line-2)}}
.claim.none{{border-left:2px solid var(--gold)}}
.claim h3{{font:400 1.375rem/1.25 {sans};margin:0 0 8px;color:var(--ink);
  letter-spacing:-.01em}}
.claim h3 b{{font-family:{mono};font-weight:600}}
.claim p{{margin:0;color:var(--muted);font-size:.9rem;max-width:44ch}}
.claim p b{{color:var(--ink);font-weight:600;font-family:{mono};font-size:.86rem}}
.figline{{display:flex;align-items:baseline;gap:14px;margin:0 0 4px}}
.row{{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:18px}}

/* ---- controls. Cinzel, letterspaced, 48px tall, on a gold wash rather than a grey box. ---- */
.btn{{display:inline-flex;align-items:center;min-height:48px;padding:0 20px;
  border:1px solid var(--line-2);border-radius:4px;
  background:linear-gradient(180deg,rgba(117,80,36,.28),rgba(117,80,36,.05));
  color:var(--gold-b);font:400 .82rem/1 {display};letter-spacing:.16em;
  text-transform:uppercase;cursor:pointer;text-decoration:none;white-space:nowrap}}
.btn:hover,.btn:focus-visible{{border-color:var(--gold);color:var(--pure)}}
.btn.route{{background:none;border-style:dashed;color:var(--muted)}}

[popover]{{border:1px solid var(--line-2);border-radius:6px;padding:26px;
  background:linear-gradient(180deg,var(--surface),var(--bg));color:var(--ink);
  max-width:min(34rem,92vw);box-shadow:0 24px 64px rgba(0,0,0,.8)}}
[popover]::backdrop{{background:rgba(4,3,2,.74)}}
[popover] h4{{font:600 .82rem/1 {display};letter-spacing:.2em;text-transform:uppercase;
  margin:0 0 18px;color:var(--gold)}}
.popnote{{color:var(--dim);font-size:.78rem;margin:16px 0 0;max-width:46ch}}
.popclose{{margin-top:20px}}

table.weeks{{width:100%;border-collapse:collapse;font-size:.84rem}}
.weeks th{{font:400 .78rem/1 {display};letter-spacing:.14em;text-transform:uppercase;
  text-align:left;color:var(--muted);padding:7px 12px 7px 0;white-space:nowrap}}
.weeks td{{padding:7px 0}}
.weeks td.n{{font-family:{mono};font-size:.95rem;text-align:right;padding-right:14px;
  color:var(--ink);font-variant-numeric:tabular-nums}}
.barcell{{width:50%}}
.bar{{display:block;height:10px;border-radius:2px}}
.bar.recede{{background:var(--dim)}}
.bar.mid{{background:var(--gold)}}
.bar.hot{{background:linear-gradient(90deg,var(--gold),var(--gold-b))}}

dl.kv{{display:grid;grid-template-columns:auto 1fr;gap:8px 18px;margin:0}}
dl.kv dt{{font:400 .78rem/1.4 {display};letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted)}}
dl.kv dd{{margin:0;color:var(--ink);font-size:.9rem}}
dl.kv dd.n{{font-family:{mono};font-variant-numeric:tabular-nums;font-size:1.05rem}}
ul.slots{{margin:0;padding-left:20px;font-size:.95rem}}

/* ---- the checks line. Most weeks this is the whole page, so it gets a rule and a label
   rather than being a sentence in the margin. ---- */
.checks{{margin:0;padding:18px 0 0;border-top:1px solid var(--line);color:var(--muted);
  font-size:.86rem}}
.checks .eyebrow{{margin-bottom:8px}}
.checks b{{font-family:{mono};color:var(--ink);font-size:1.05rem;font-weight:600}}

.absent{{color:var(--dim);cursor:help;border-bottom:1px dotted var(--dim)}}
.currency{{color:var(--muted);cursor:help;border-bottom:1px dotted var(--gold)}}
.stamp{{font:400 .76rem/1.5 {sans};color:var(--dim)}}

nav{{margin-top:36px}}
nav .orn{{margin:0 0 18px}}
.rooms{{display:flex;flex-wrap:wrap;gap:10px}}
.dock{{margin-top:18px;padding-top:18px;border-top:1px dashed var(--line)}}
.dock .stamp{{display:block;margin-top:9px}}
.close{{margin-top:26px}}
.close .btn{{border-color:var(--gold)}}

@media (max-width:460px){{
  .wrap{{padding:26px 16px 52px}}
  .word{{font-size:1.32rem}}
  .big{{font-size:2.25rem}}
  .claim{{padding:18px 18px}}
  .claim h3{{font-size:1.2rem}}
  .barcell{{width:42%}}
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
        parts = claim_parts(c)
        exp, pid = expansion(c, fx), f"exp{i}"
        controls = [f'<a class="btn route" href="#{esc(c["route"].lower().replace(" ", "-"))}">'
                    f'{esc(c["route"])} &rsaquo;</a>']
        if exp:
            controls.insert(0, f'<button class="btn" popovertarget="{pid}">What it is made of'
                               f'</button>')
        pop = (f'<div id="{pid}" popover><h4>{parts["eyebrow"]}</h4>{exp}'
               f'<div class="popclose"><button class="btn" popovertarget="{pid}" '
               f'popovertargetaction="hide">Close</button></div></div>') if exp else ""
        fig = (f'<p class="figline"><span class="big">{parts["figure"]}'
               f'<span class="u">{parts["unit"]}</span></span></p>') if parts["figure"] else ""
        cards.append(f'<article class="claim {esc(c["kind"])}">'
                     f'<p class="eyebrow">{parts["eyebrow"]}</p>'
                     f'{fig}<h3>{parts["headline"]}</h3><p>{parts["body"]}</p>'
                     f'<div class="row">{"".join(controls)}</div></article>{pop}')

    if not cards:
        # THE QUIET STATE IS THE PRIMARY DESIGN, not an empty state to apologise for. `VOICE.md`
        # rule 8: leaving is a success state. The brief's test is whether a person can tell in
        # three seconds that they may close the app, and `threshold`'s CLOSE THE APP control --
        # the best single idea in the whole prior round -- turns that test into an affordance.
        # THE QUIET STATE GETS A HERO FIGURE TOO, and it is the one number this page can
        # always defend: how many checks ran. A quiet page with no figure at all is what read as
        # "too spartan" -- correct, and indistinguishable from unfinished.
        cards.append(f'<article class="claim none">'
                     f'<p class="eyebrow">Nothing open this week</p>'
                     f'<p class="figline"><span class="big">{summary["ran"]}'
                     f'<span class="u">checks, all clean</span></span></p>'
                     f'<h3>{esc(", ".join(summary["clean"]))}</h3>'
                     f'<p>No unfillable slot, no bye week still ahead with a measured cost, no '
                     f'position thin against this league.</p></article>')

    more = (f'<p class="stamp">Also standing: '
            + "; ".join(claim_headline(c) for c in hidden) + ".</p>") if hidden else ""

    # ---- the checks line. DERIVED, never a hardcoded list (`#338`) ---------------------------
    if summary["all_clean"]:
        # The quiet card already carries this as its hero figure; repeating it below would be
        # the same fact twice, which the standing constraint names as the failure.
        checks = ""
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

    checks_block = (f'<div class="checks"><p class="eyebrow">What was examined</p>{checks}</div>'
                    if checks else "")
    orn = '<p class="orn"><i></i><s></s><i></i></p>'
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
  {orn}
  {seat}
  <div class="claims">{"".join(cards)}</div>
  {more}
  {checks_block}
  {close}
  <nav>
    {orn}
    <h2 class="eyebrow">Rooms</h2>
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
