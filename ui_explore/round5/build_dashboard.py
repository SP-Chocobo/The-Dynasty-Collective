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
body{{font:400 .95rem/1.55 {sans};-webkit-text-size-adjust:100%}}
.wrap{{max-width:84rem;margin:0 auto;padding:0 20px 56px}}

/* ---- TOP BAR. Horizontal, full width, with the rooms inline. The first two passes put a
   centred crest over a 760px column on a 1280px screen and left 60% of it empty, which is most
   of why the page read as "too plain": not the type, the COMPOSITION. ---- */
.top{{display:flex;align-items:center;gap:26px;padding:18px 0;border-bottom:1px solid var(--line);
  flex-wrap:wrap}}
.crest{{display:flex;align-items:center;gap:12px;flex:0 0 auto}}
.word{{font:600 1.32rem/1 {display};letter-spacing:.11em;text-transform:uppercase;margin:0;
  background:linear-gradient(176deg,#755024 0%,#ba9561 38%,#f9de99 68%,#fff4ce 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent}}
.word b{{display:block;font-size:.76rem;letter-spacing:.42em;font-weight:400;margin-top:5px}}
.doors{{display:flex;gap:4px;flex:1 1 auto;flex-wrap:wrap}}
.door{{display:inline-flex;align-items:center;min-height:44px;padding:0 13px;border-radius:4px;
  color:var(--muted);font:400 .8rem/1 {display};letter-spacing:.1em;text-decoration:none;
  border:1px solid transparent;white-space:nowrap}}
.door:hover,.door:focus-visible{{color:var(--gold-b);border-color:var(--line-2);
  background:linear-gradient(180deg,rgba(117,80,36,.22),rgba(117,80,36,.04))}}
.whoami{{display:flex;align-items:center;gap:10px;padding:9px 14px;border:1px solid var(--line);
  border-radius:4px;background:var(--surface);font-size:.8rem;color:var(--muted);
  flex:0 0 auto}}
.whoami b{{color:var(--ink);font-weight:600;font-family:{mono}}}

/* ---- THE VERDICT. deck's hero: the three-second answer as a STATEMENT, with the headline
   figure boxed beside it. This is the element both earlier passes lacked entirely. ---- */
.verdict{{display:grid;grid-template-columns:1fr 20rem;gap:28px;align-items:start;
  margin:26px 0 22px;padding:26px 28px;border:1px solid var(--line-2);border-radius:6px;
  background:linear-gradient(180deg,var(--surface),var(--surface-2));position:relative;
  overflow:hidden}}
.verdict::before{{content:"";position:absolute;inset:0 auto 0 0;width:180px;pointer-events:none;
  background:repeating-linear-gradient(135deg,transparent 0 4px,rgba(176,162,138,.06) 4px 5px);
  mask-image:linear-gradient(90deg,#000,transparent)}}
.verdict h1{{font:400 2.35rem/1.08 {display};color:var(--gold-b);margin:4px 0 14px;
  letter-spacing:.005em;position:relative}}
.verdict p{{margin:0;color:var(--muted);max-width:56ch;position:relative}}
.verdict p b{{color:var(--ink);font-family:{mono};font-weight:600;font-size:.9rem}}
.statbox{{border:1px solid var(--line-2);border-radius:5px;padding:18px 20px;
  background:linear-gradient(180deg,rgba(117,80,36,.16),rgba(117,80,36,.03));position:relative}}
.statbox .big{{font:600 3rem/1 {mono};color:var(--gold-b);letter-spacing:-.02em;display:block;
  font-variant-numeric:tabular-nums}}
.statbox .u{{font:400 .8rem/1 {display};letter-spacing:.14em;text-transform:uppercase;
  color:var(--dim);display:block;margin-top:8px}}
.statbox .sub{{margin:14px 0 0;padding-top:12px;border-top:1px solid var(--line);
  font-size:.8rem;color:var(--muted)}}

/* ---- the two-column body ---- */
.cols{{display:grid;grid-template-columns:1.45fr 1fr;gap:20px;align-items:start}}
.panel{{border:1px solid var(--line);border-radius:6px;
  background:linear-gradient(180deg,var(--surface),var(--surface-2));overflow:hidden}}
.ph{{display:flex;align-items:baseline;justify-content:space-between;gap:14px;
  padding:15px 20px;border-bottom:1px solid var(--line)}}
.eyebrow{{font:600 .78rem/1 {display};letter-spacing:.22em;text-transform:uppercase;
  color:var(--gold);margin:0}}
.ph .basis{{font:400 .76rem/1.4 {sans};color:var(--dim);font-style:italic;text-align:right}}
.pbody{{padding:16px 20px 20px}}

/* ---- THE LEDGER. A real table: this is the density the owner liked, and it is organised
   rather than piled -- every column labelled, every figure in mono, every player chipped in
   his own position colour. ---- */
table.led{{width:100%;border-collapse:collapse}}
.led thead th{{font:400 .76rem/1 {display};letter-spacing:.14em;text-transform:uppercase;
  color:var(--dim);text-align:left;padding:0 10px 9px 0;border-bottom:1px solid var(--line);
  white-space:nowrap}}
.led tbody td{{padding:9px 10px 9px 0;border-bottom:1px solid var(--surface-2);
  vertical-align:top}}
.led tbody tr:last-child td{{border-bottom:0}}
.led tbody tr.peak td{{background:rgba(117,80,36,.14)}}
.led .wk{{font:400 .82rem/1 {display};letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);white-space:nowrap}}
.led .peak .wk{{color:var(--gold-b)}}
.led .n{{font:600 1.05rem/1 {mono};color:var(--ink);text-align:right;white-space:nowrap;
  font-variant-numeric:tabular-nums}}
.led .peak .n{{color:var(--gold-b);font-size:1.25rem}}
.led .barcell{{width:34%}}
.bar{{display:block;height:9px;border-radius:2px;min-width:3px}}
.bar.recede{{background:var(--dim)}}
.bar.mid{{background:var(--gold)}}
.bar.hot{{background:linear-gradient(90deg,var(--gold),var(--gold-b))}}
.who{{display:flex;flex-wrap:wrap;gap:6px}}
.chip{{display:inline-flex;align-items:center;gap:6px;font-size:.8rem;color:var(--ink);
  white-space:nowrap}}
.chip i{{width:8px;height:8px;border-radius:2px;flex:0 0 auto}}
.chip s{{font-family:{mono};color:var(--muted);text-decoration:none;font-size:.78rem}}
.ledfoot{{display:flex;flex-wrap:wrap;gap:22px;margin-top:16px;padding-top:14px;
  border-top:1px solid var(--line);font-size:.8rem;color:var(--muted)}}
.ledfoot b{{font-family:{mono};color:var(--ink);font-weight:600}}

/* ---- claim cards in the right column, each with a position pill and a visible basis ---- */
.claim{{border:1px solid var(--line);border-radius:5px;padding:15px 17px;margin:0 0 12px;
  background:var(--surface-2);border-left-width:3px}}
.claim:last-child{{margin-bottom:0}}
.claim.hole{{border-left-color:var(--gold-b)}}
.claim.bye{{border-left-color:var(--gold)}}
.claim.thin{{border-left-color:var(--line-2)}}
.claim.none{{border-left-color:var(--gold)}}
.chead{{display:flex;align-items:center;gap:10px;margin:0 0 7px;flex-wrap:wrap}}
.pill{{display:inline-flex;align-items:center;height:21px;padding:0 8px;border-radius:3px;
  font:600 .76rem/1 {mono};letter-spacing:.04em}}
.claim h3{{font:400 1.02rem/1.3 {sans};margin:0;color:var(--ink)}}
.claim h3 b{{font-family:{mono};font-weight:600}}
.claim p{{margin:0;color:var(--muted);font-size:.86rem}}
.claim p b{{color:var(--ink);font-family:{mono};font-weight:600;font-size:.82rem}}
.basis{{display:block;margin-top:9px;font:400 .76rem/1.45 {mono};color:var(--dim)}}
.row{{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}}

/* ---- CLEARED. deck's six-column row: what was checked and passed, each with its basis. ---- */
.cleared{{margin-top:20px}}
.cgrid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:0;
  border-top:1px solid var(--line)}}
.cg{{padding:15px 18px;border-right:1px solid var(--line)}}
.cg:last-child{{border-right:0}}
.cg .t{{display:flex;gap:8px;align-items:baseline;color:var(--ink);font-size:.86rem}}
.cg .tick{{color:var(--status-ok);flex:0 0 auto}}

.btn{{display:inline-flex;align-items:center;min-height:44px;padding:0 15px;
  border:1px solid var(--line-2);border-radius:4px;
  background:linear-gradient(180deg,rgba(117,80,36,.26),rgba(117,80,36,.05));
  color:var(--gold-b);font:400 .78rem/1 {display};letter-spacing:.14em;text-transform:uppercase;
  cursor:pointer;text-decoration:none;white-space:nowrap}}
.btn:hover,.btn:focus-visible{{border-color:var(--gold);color:var(--pure)}}
.btn.route{{background:none;border-style:dashed;color:var(--muted)}}

[popover]{{border:1px solid var(--line-2);border-radius:6px;padding:26px;
  background:linear-gradient(180deg,var(--surface),var(--bg));color:var(--ink);
  max-width:min(36rem,92vw);box-shadow:0 24px 64px rgba(0,0,0,.8)}}
[popover]::backdrop{{background:rgba(4,3,2,.74)}}
[popover] h4{{font:600 .82rem/1 {display};letter-spacing:.2em;text-transform:uppercase;
  margin:0 0 16px;color:var(--gold)}}
.popnote{{color:var(--dim);font-size:.78rem;margin:14px 0 0;max-width:48ch}}
.popclose{{margin-top:18px}}
table.weeks{{width:100%;border-collapse:collapse;font-size:.84rem}}
.weeks th{{font:400 .76rem/1 {display};letter-spacing:.14em;text-transform:uppercase;
  text-align:left;color:var(--muted);padding:6px 12px 6px 0}}
.weeks td{{padding:6px 0}}
.weeks td.n{{font-family:{mono};text-align:right;padding-right:14px;color:var(--ink);
  font-variant-numeric:tabular-nums}}
.weeks .barcell{{width:46%}}
dl.kv{{display:grid;grid-template-columns:auto 1fr;gap:7px 16px;margin:0}}
dl.kv dt{{font:400 .78rem/1.4 {display};letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted)}}
dl.kv dd{{margin:0;color:var(--ink);font-size:.9rem}}
dl.kv dd.n{{font-family:{mono};font-variant-numeric:tabular-nums;font-size:1.05rem}}
ul.slots{{margin:0;padding-left:20px;font-size:.92rem}}

.absent{{color:var(--dim);cursor:help;border-bottom:1px dotted var(--dim)}}
.currency{{color:var(--muted);cursor:help;border-bottom:1px dotted var(--gold)}}
.dock{{margin-top:18px;padding-top:16px;border-top:1px dashed var(--line);
  display:flex;align-items:center;gap:14px;flex-wrap:wrap}}
.stamp{{font:400 .78rem/1.5 {sans};color:var(--dim)}}
.close{{margin-top:18px}}

@media (max-width:1040px){{
  .verdict{{grid-template-columns:1fr}}
  .cols{{grid-template-columns:1fr}}
}}
@media (max-width:560px){{
  .wrap{{padding:0 16px 44px}}
  .verdict{{padding:20px;margin:18px 0 16px}}
  .verdict h1{{font-size:1.72rem}}
  .statbox .big{{font-size:2.5rem}}
  .led .barcell{{display:none}}
  .cg{{border-right:0;border-bottom:1px solid var(--line)}}
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


def pill(position: str) -> str:
    """A position chip in its OWN colour, from `design_system.POSITION_PILL_TOKENS` -- one home
    for the palette (`#312` found three). Both earlier passes of this page used no position
    colour at all, which is a large part of why it read as flat: the roster's own vocabulary was
    rendered as plain text."""
    bg, fg = ds.position_pill_color(position)
    return f'<span class="pill" style="background:{bg};color:{fg}">{esc(position)}</span>'


def basis_note(basis: dict, key: str) -> str:
    """The provenance line deck prints under every figure, in mono.

    It is honesty made VISIBLE rather than merely true, and it doubles as texture -- a panel
    whose numbers each carry `measured - bye_collision` beneath them cannot read as an empty
    box. Absent and constructed stamps are rendered through the same grammar as any figure.
    """
    raw = (basis or {}).get(key) or ""
    kind = fp.stamp_kind(raw) if hasattr(fp, "stamp_kind") else (
        "absent" if raw.startswith("ABSENT") else
        "constructed" if raw.startswith("CONSTRUCTED") else "measured")
    body = raw.split("--", 1)[-1].strip() if "--" in raw else raw
    if kind == "absent":
        return f'<span class="basis">{absent(body or "not measured")}</span>'
    short = body if len(body) <= 72 else body[:69].rstrip() + "..."
    return f'<span class="basis" title="{esc(body)}">{esc(kind)} &middot; {esc(short)}</span>'


def bye_ledger(fx: dict, reason: str = "") -> str:
    """deck's densest panel, and the one the owner singled out: the weeks, what each costs, and
    WHO is away.

    The names are a FILTER on `roster[].bye`, not a computation -- every field shown is one the
    engine already put in the fixture (`#338`). The ledger adds no quantity; it arranges them.
    """
    weeks = (fx.get("bye_profile") or {}).get("weeks") or {}
    roster = fx.get("roster") or []
    cw = fx.get("current_week")
    if not weeks:
        # THE EXACT REASON WHEN THERE IS ONE (`#368`). `bye_profile_from` composes a sentence
        # naming how many rostered players are unpriced and why that forbids the measurement;
        # it reached the fixture and stopped there, so this panel said "no bye profile was
        # measured" -- true, unhelpful, and indistinguishable from "this roster has no byes".
        # Defaulted to the old wording, so callers that pass nothing render exactly as before.
        # VISIBLE PROSE, not only a tooltip. `absent` renders an em dash carrying its reason in
        # a `title`, which is right for a missing cell in a table and wrong for a panel this
        # size: the whole section is empty, there is nothing to hover on a phone, and a reader
        # is left guessing at what should be the clearest thing on the page. The em dash stays
        # as the marker; the sentence is spoken beside it.
        if reason:
            return (f'<p class="stamp">{absent(reason)} {esc(reason)}</p>')
        return ('<p class="stamp">'
                + absent("no bye profile was measured for this roster") + "</p>")
    losses = {w: (v.get("value_lost") if isinstance(v, dict) else v) for w, v in weeks.items()}
    numeric = [v for v in losses.values() if isinstance(v, (int, float))]
    peak = max(numeric) if numeric else 0
    worst = max(losses, key=lambda w: losses[w] if isinstance(losses[w], (int, float)) else -1)
    rows = []
    for wk in sorted(weeks, key=lambda w: int(w)):
        lost = losses[wk]
        away = [r for r in roster if str(r.get("bye")) == str(wk)]
        who = "".join(
            f'<span class="chip"><i style="background:'
            f'{ds.position_pill_color(r.get("position") or "")[1]}"></i>{esc(r.get("name"))}'
            f'<s>{esc(ds.figure(r.get("value")) or "--")}</s></span>' for r in away) or (
            f'<span class="stamp">{absent("no rostered player is away this week")}</span>')
        if not isinstance(lost, (int, float)):
            cell = f'<td class="n">{absent("this week carries no measured loss")}</td><td></td>'
        else:
            share = (lost / peak) if peak else 0
            tone = (SEVERITY[2][0] if share >= .75 else
                    SEVERITY[1][0] if share >= .35 else SEVERITY[0][0])
            cell = (f'<td class="n">{esc(ds.figure(lost))}</td>'
                    f'<td class="barcell"><span class="bar {tone}" '
                    f'style="width:{max(3, round(share * 100))}%"></span></td>')
        behind = cw is not None and int(wk) < int(cw)
        rows.append(f'<tr class="{"peak" if wk == worst and not behind else ""}">'
                    f'<td class="wk">Wk {esc(wk)}</td>{cell}'
                    f'<td><div class="who">{who}</div></td></tr>')
    total = ds.figure((fx.get("bye_profile") or {}).get("total_loss"))
    conc = (fx.get("bye_profile") or {}).get("concentration")
    unknown = (fx.get("bye_profile") or {}).get("unknown_byes")
    foot = (f'<div class="ledfoot"><span>season <b>{esc(total or "--")}</b></span>'
            f'<span>worst week <b>{esc(f"{conc:.0%}") if conc is not None else absent("a roster with nothing to lose has no shape, so this is None rather than 0%")}</b> of it</span>'
            f'<span>unknown byes <b>{esc(unknown)}</b></span></div>')
    return (f'<table class="led"><thead><tr><th>Week</th><th style="text-align:right">Lost</th>'
            f'<th></th><th>Away</th></tr></thead><tbody>{"".join(rows)}</tbody></table>{foot}')


def verdict_prose(claims: list, fx: dict) -> str:
    """The hero paragraph, composed as SENTENCES rather than enumerated as labels.

    The first build of this hero printed "Bye damage: Week 6. Thin room: DEF. Thin room: TE." --
    a mechanical list of the same cards that sit below it, which says nothing the band does not
    and reads as placeholder. `deck`, the design chosen for feel, wrote real prose here: the bye
    cost AGAINST the season total, then the thin rooms named together.

    Every figure is still the engine's. What changes is the grammar, not the source: thin rooms
    are COLLECTED into one clause instead of repeating a card each, which is the standing
    constraint applied to the sentence -- clean dissemination, not one line per variable.
    """
    bp = fx.get("bye_profile") or {}
    bits = []
    bye = next((c for c in claims if c["kind"] == "bye"), None)
    if bye is not None:
        total = ds.figure(bp.get("total_loss"))
        loss = ds.figure(bye.get("worst_week_loss"))
        against = (f" of the season's <b>{esc(total)}</b>" if total else "")
        bits.append(f'Week <b>{esc(bye["worst_week"])}</b> costs <b>{esc(loss)}</b>{against} '
                    f'in {currency_stamp("bye trade value")}.')
    holes = next((c for c in claims if c["kind"] == "hole"), None)
    if holes is not None:
        ps = holes.get("positions") or []
        bits.append(f'No rostered player can fill {esc(", ".join(ps))}.')
    thin = [c for c in claims if c["kind"] == "thin"]
    if thin:
        names = ", ".join(esc(c["position"]) for c in thin[:-1])
        last = esc(thin[-1]["position"])
        joined = f"{names} and {last}" if names else last
        label = thin[0].get("label") or "thin"
        verb = "rates" if len(thin) == 1 else "rate"
        floor = any(c.get("priced_floor") for c in thin)
        bits.append(f'{joined} {verb} <b>{esc(label)}</b> against this league\'s own rosters'
                    + (", one of them on a priced floor." if floor else "."))
    if fx.get("current_week") is None:
        bits.append("No current week is on file, so none of this carries a deadline.")
    return " ".join(bits)


def build(fx: dict) -> str:
    """One responsive page, rendered from `front_claims.compose`'s judgment."""
    _assert_ramp_is_visible()
    _assert_type_floor()
    band = fc.compose(fx)
    shown, hidden = band["shown"], band["hidden"]
    summary = fc.checks_summary(band["checks"])
    basis = (fx.get("_provenance") or {}).get("basis") or {}

    # ---- THE VERDICT: the three-second answer as a statement ---------------------------------
    n = len(shown) + len(hidden)
    words = {0: "Nothing", 1: "One thing", 2: "Two things", 3: "Three things", 4: "Four things"}
    headline = ("Nothing open this week." if not n
                else f'{words.get(n, str(n) + " things")} {"is" if n == 1 else "are"} open.')
    if shown:
        lead = claim_parts(shown[0])
        stat = (f'<span class="big">{lead["figure"]}</span>'
                f'<span class="u">{lead["unit"]}</span>'
                f'<p class="sub">{lead["eyebrow"]} &middot; {lead["headline"]}</p>')
        summary_prose = verdict_prose(shown + hidden, fx)
    else:
        stat = (f'<span class="big">{summary["ran"]}</span>'
                f'<span class="u">checks, all clean</span>'
                f'<p class="sub">{esc(", ".join(summary["clean"]))}</p>')
        summary_prose = ("Every check this page runs came back clean. It keeps the ledger "
                         "while you are gone.")

    # ---- the claims column -------------------------------------------------------------------
    cards, pops = [], []
    for i, c in enumerate(shown):
        parts, exp, pid = claim_parts(c), expansion(c, fx), f"exp{i}"
        pos = c.get("position") or (c.get("positions") or [None])[0]
        controls = [f'<a class="btn route" href="#{esc(c["route"].lower().replace(" ", "-"))}">'
                    f'{esc(c["route"])} &rsaquo;</a>']
        if exp:
            controls.insert(0, f'<button class="btn" popovertarget="{pid}">What it is '
                               f'made of</button>')
            pops.append(f'<div id="{pid}" popover><h4>{parts["eyebrow"]}</h4>{exp}'
                        f'<div class="popclose"><button class="btn" popovertarget="{pid}" '
                        f'popovertargetaction="hide">Close</button></div></div>')
        key = {"bye": "bye_profile", "thin": "thin_positions", "hole": "structural_holes"}.get(
            c["kind"], "")
        cards.append(
            f'<article class="claim {esc(c["kind"])}">'
            f'<div class="chead">{pill(pos) if pos else ""}'
            f'<h3>{parts["headline"]} &middot; {parts["figure"]} {parts["unit"]}</h3></div>'
            f'<p>{parts["body"]}</p>{basis_note(basis, key)}'
            f'<div class="row">{"".join(controls)}</div></article>')
    if not cards:
        cards.append('<p class="stamp">Nothing is standing. The ledger below is what was '
                     'examined to say so.</p>')
    if hidden:
        cards.append('<p class="stamp">Also standing: '
                     + "; ".join(claim_headline(c) for c in hidden) + ".</p>")

    # ---- CLEARED: what was checked and passed, each with its basis ---------------------------
    cgs = []
    for check in band["checks"]:
        key = {"byes": "bye_profile", "depth": "thin_positions",
               "holes": "structural_holes"}.get(check["name"], "")
        if check["state"] == fc.CHECK_CLEAN:
            cgs.append(f'<div class="cg"><div class="t"><span class="tick">&check;</span>'
                       f'<span>{esc(check["name"]).title()}: nothing found</span></div>'
                       f'{basis_note(basis, key)}</div>')
        elif check["state"] == fc.CHECK_ABSENT:
            cgs.append(f'<div class="cg"><div class="t"><span>{esc(check["name"]).title()}: '
                       f'{absent(check["reason"])}</span></div></div>')
    cleared = (f'<section class="panel cleared"><div class="ph">'
               f'<p class="eyebrow">Cleared &mdash; can wait</p>'
               f'<span class="basis">what was checked and passed, each with its basis</span>'
               f'</div><div class="cgrid">{"".join(cgs)}</div></section>') if cgs else ""

    doors = "".join(f'<a class="door" href="#{esc(r.lower().replace(" ", "-"))}">{esc(r)}</a>'
                    for r in ROOMS)
    team, lname = fx.get("team"), fx.get("league_name")
    week = fx.get("current_week")
    # AN ABSENCE MUST READ AS INFORMATION, NOT AS DAMAGE. The first build of this bar rendered
    # `Team 1 -- --`, two bare em dashes that look like a broken template rather than two
    # measured absences. The dash still carries its reason on hover, but it is now LABELLED, so
    # the reader can tell which quantity is missing without hovering anything.
    lname_html = (esc(lname) if lname else
                  f'no league name {absent(fp.reason_of(basis.get("league_name", "")) or "this capture carries no league name")}')
    week_html = (f'wk <b>{esc(week)}</b>' if week is not None else
                 f'no week {absent(fp.reason_of(basis.get("current_week", "")) or "no season position was read")}')
    whoami = (f'<div class="whoami"><b>{esc(team or "")}</b>'
              f'<span>{lname_html}</span><span>{week_html}</span></div>')

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
    <nav class="doors">{doors}</nav>
    {whoami}
  </header>

  <section class="verdict">
    <div>
      <p class="eyebrow">The three-second answer</p>
      <h1>{headline}</h1>
      <p>{summary_prose}</p>
    </div>
    <div class="statbox">{stat}</div>
  </section>

  <div class="cols">
    <section class="panel">
      <div class="ph"><p class="eyebrow">Bye ledger</p>
        <span class="basis">each week re-solved with that week's byes removed &middot;
        value lost, not bodies</span></div>
      <div class="pbody">{bye_ledger(fx)}</div>
    </section>
    <section class="panel">
      <div class="ph"><p class="eyebrow">Open</p>
        <span class="basis">ranked by kind, not by size &mdash; the units do not compare</span>
      </div>
      <div class="pbody">{"".join(cards)}</div>
    </section>
  </div>

  {cleared}

  <div class="dock">
    <a class="btn route" href="#prytaneum">{esc(DOCK)}</a>
    <span class="stamp">A dock rendered under every room, not a sixth room.</span>
  </div>
</div>
{"".join(pops)}
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
