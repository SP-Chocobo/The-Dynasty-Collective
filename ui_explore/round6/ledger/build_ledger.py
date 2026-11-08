#!/usr/bin/env python3
"""Round 6, slug `ledger`: the LEDGER is the spine -- one continuous record, not a set of panels.

THE QUESTION THIS FILE ANSWERS. The base (`round5/build_dashboard.py`) chops the same facts into
a hero, a two-column body and a cleared row: four containers, each with its own header and its
own border, and the reader learns the page by learning the boxes. This page has ONE container --
a register read top to bottom, in which the verdict, the open claims, the bye weeks, the checks
and the provenance are all ROWS, differentiated by what KIND of row they are rather than by which
box they sit in. A ship's log or a court docket: structure comes from row typology and rhythm,
not from panels.

THE RISK, STATED SO IT CAN BE CHECKED AGAINST THE RENDER. A long undifferentiated list is worse
than panels, not better. If every row looks alike the page is a spreadsheet, and the owner's
standing constraint is "clean dissemination of information over just having as much on the
screen as you can fit." So the typology is deliberate and SMALL -- seven row kinds -- and each is
told apart by four things at once: the MARGIN label (Cinzel, in a fixed left column, naming the
kind), the MARKER on the rail (size and fill), the FIGURE scale (3rem / 1.75rem / 1.05rem / none)
and the ROW WEIGHT (a bordered gradient box for what is open, bare for what is only recorded).

    caption   the register's first entry: the three-second answer, with the lead figure at hero scale
    open      one claim the band raised; boxed, position-coloured, with its popover and its route
    head      a divider naming what the rows beneath it are; the title lives in the margin column
    week      one bye week: who is away, what it costs, a bar; receded when the week is behind
    sum       a ledger total line under the weeks: season, share in the worst week, unknown byes
    check     one check the engine ran: clean (ring), fired (dot, pointing back up), or absent
    stamp     provenance: every absence and every constructed value, stated ONCE and labelled

WHAT IS KEPT FROM THE BASE, because it was ruled rather than chosen: `front_claims.compose` is the
only judgment on the page; every figure is mono and Cinzel never carries a numeral; the currency
stamp on every bye figure; popovers, not inline disclosure; the severity ramp running dark-to-
light and asserted visible at build time; small type in rem and asserted >= 12px at build time;
`design_system` as the single palette home; the five rooms and the one dock; record off the front.

WHAT CHANGES IN THE COMMUNICATION, in one line each; `NOTES.md` carries the argument:
  * The checks row lists ALL THREE checks, not only the clean one. A fired check says "raised,
    above" and names what it raised, so the audit line is complete rather than complementary.
  * Weeks that are BEHIND the current week collapse to one row, stated once, with the full list
    in a popover. Seven played weeks each wearing the same "behind" stamp is the absence-as-noise
    failure the brief names; on the quiet fixture it is the whole difference between a page that
    is quiet and one that is merely short.
  * The bye popover shows `worst_week_detail` -- starters out, players out, bench promoted and
    its value, lineup value -- which the engine computes separately and the base never surfaces.
    It does NOT repeat the week table, because the weeks are already rows of the register.
  * Absences are gathered into ONE provenance row at the foot, each labelled with its quantity
    and carrying its reason, instead of two bare dashes in the top bar.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))

import design_system as ds
import front_claims as fc
import front_page as fp

ROOT = HERE.parents[2]
FIXTURES = (
    (ROOT / "ui_explore/front_fixture.json", HERE / "ledger.html"),
    (ROOT / "ui_explore/quiet_fixture.json", HERE / "ledger_quiet.html"),
)

# ---------------------------------------------------------------------------------------------
# BUILD-TIME GATES. Both copied from the base's pattern: they raise, they do not warn.
# ---------------------------------------------------------------------------------------------
#: Brightness RISING with severity, the only direction that clears 3:1 on a near-black ground
#: (`line` is 1.27:1, `line-2` 1.73:1 -- which is exactly the band round 4's five failing bars
#: fell in). The ramp is reused for the rail markers, so one assertion covers both.
SEVERITY = (("recede", "dim"), ("mid", "gold"), ("hot", "gold-b"))
NON_TEXT_FLOOR = 3.0

#: EVERY non-text mark this page draws, and the token it is drawn in. The rail is in here because
#: it is the page's one structural line and the brief names rails explicitly; a rail in `line-2`
#: would have been invisible at 1.73:1 and read as "no spine at all". Checked against `bg`, the
#: ground every mark here actually sits on -- the open rows' box gradient runs surface -> surface-2
#: and both are a hair lighter than bg, so bg is the worst case by only ~0.03;
#: `_assert_marks_visible` measures all three grounds rather than trusting that.
MARKS = {
    "rail": "dim",
    "marker:week": "dim", "marker:open": "gold", "marker:caption": "gold-b",
    "marker:check-clean": "status-ok", "marker:check-fired": "gold",
    "bar:recede": "dim", "bar:mid": "gold", "bar:hot": "gold-b",
    "check tick": "status-ok",
}
GROUNDS = ("bg", "surface", "surface-2")

#: Every token TEXT is set in, held to WCAG AA normal text on every ground it can land on. `dim`
#: is 4.51:1 on `surface` -- in, by a hundredth -- and that number is why this is measured here
#: rather than inherited from design_system's policy, which floors `dim` at 3.0 as a recede role.
#: On this page `dim` carries basis lines a reader is expected to READ, so it is held to 4.5.
TEXT_TOKENS = ("ink", "muted", "dim", "gold", "gold-b", "status-ok")
TEXT_FLOOR = 4.5


def _assert_ramp_is_visible():
    """The base's assertion, kept verbatim in spirit: a bar nobody can see is a missing bar."""
    bad = [(name, token, ds.contrast_ratio(token, "bg"))
           for name, token in SEVERITY if ds.contrast_ratio(token, "bg") < NON_TEXT_FLOOR]
    if bad:
        raise SystemExit("severity ramp below the %.1f:1 non-text floor: %s"
                         % (NON_TEXT_FLOOR, bad))


def _assert_marks_visible():
    """Every mark in MARKS, every pill square, on every ground, >= 3:1. Fails the build."""
    bad = []
    for name, token in MARKS.items():
        for g in GROUNDS:
            r = ds.contrast_ratio(token, g)
            if r < NON_TEXT_FLOOR:
                bad.append((name, token, g, round(r, 2)))
    for pos, hexv in ds.POSITION_PILL_TOKENS.items():
        for g in GROUNDS:
            r = ds._contrast_hex(hexv, ds.TOKENS[g])
            if r < NON_TEXT_FLOOR:
                bad.append((f"pill:{pos}", hexv, g, round(r, 2)))
    if bad:
        raise SystemExit(f"non-text marks below the {NON_TEXT_FLOOR}:1 floor: {bad}")
    for token in TEXT_TOKENS:
        for g in GROUNDS:
            r = ds.contrast_ratio(token, g)
            if r < TEXT_FLOOR:
                bad.append((token, g, round(r, 2)))
    if bad:
        raise SystemExit(f"text tokens below the {TEXT_FLOOR}:1 floor: {bad}")


TYPE_FLOOR_REM = 0.75          # 12px at a 16px root


def _assert_type_floor():
    """No declared size under 12px, and no `em` font-size anywhere, so the floor is checkable
    with a regex instead of a browser. The base failed this twice before its first render on an
    `em` chain; refusing `em` outright is what makes the regex sufficient."""
    css = CSS.format(sans=ds.FONT_SANS, mono=ds.FONT_MONO, display=ds.FONT_DISPLAY)
    under = sorted({float(m.group(1)) for m in re.finditer(r"font(?:-size)?:[^;}]*?([\d.]+)rem", css)
                    if float(m.group(1)) < TYPE_FLOOR_REM})
    if under:
        raise SystemExit(f"declared font sizes below the {TYPE_FLOOR_REM}rem floor: {under}")
    ems = [m.group(0) for m in re.finditer(r"font(?:-size)?:[^;}]*?[\d.]+em(?![a-z])", css)]
    if ems:
        raise SystemExit(f"small type must be declared in rem, not em: {ems}")


ROOMS = ("Matchup", "Roster Maintenance", "Draft Room", "League", "Import Audit")
DOCK = "The Prytaneum"


def esc(value) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def absent(reason: str) -> str:
    """The em dash carrying its reason. Never 0, never blank, never a reassuring default."""
    return f'<span class="absent" tabindex="0" title="{esc(reason)}">&mdash;</span>'


CURRENCY_TRADE_VALUE = (
    "dynasty trade value, not this league's points. `bye_collision` prices whatever its caller "
    "supplies and this page supplies Draft Sharks Dynasty Rankings value, selected by a "
    "three-field format hint -- so a league's own bonuses never reach it. The ruling is that "
    "grading belongs in league points; that conversion is not built yet")


def currency(text: str = "trade value") -> str:
    return (f'<span class="currency" tabindex="0" title="{esc(CURRENCY_TRADE_VALUE)}">'
            f'{esc(text)}</span>')


def stamp_kind(raw: str) -> str:
    raw = raw or ""
    return ("absent" if raw.startswith("ABSENT") else
            "constructed" if raw.startswith("CONSTRUCTED") else "measured")


def basis_line(basis: dict, key: str) -> str:
    """The provenance line in mono under a figure -- honesty made visible, and texture."""
    raw = (basis or {}).get(key) or ""
    kind, body = stamp_kind(raw), fp.reason_of(raw)
    if kind == "absent":
        return f'<span class="basis">{absent(body)}</span>'
    short = body if len(body) <= 72 else body[:69].rstrip() + "..."
    return f'<span class="basis" title="{esc(body)}">{esc(kind)} &middot; {esc(short)}</span>'


def pill(position: str) -> str:
    bg, fg = ds.position_pill_color(position)
    return f'<span class="pill" style="background:{bg};color:{fg}">{esc(position)}</span>'


def chip(player: dict) -> str:
    """One player as a chip in his own position colour, value in mono, unpriced as a dash."""
    fg = ds.position_pill_color(player.get("position") or "")[1]
    val = ds.figure(player.get("value"))
    shown = esc(val) if val is not None else absent("the merger could not price this player")
    return (f'<span class="chip"><i style="background:{fg}"></i>{esc(player.get("name"))}'
            f'<s>{shown}</s></span>')


# ---------------------------------------------------------------------------------------------
# CLAIM PROSE. The engine returns values and flags; the surface writes the sentence.
# ---------------------------------------------------------------------------------------------
def claim_parts(c: dict, fx: dict) -> dict:
    """`{kind_label, figure, unit, headline, body}` -- figure in mono, never in Cinzel."""
    kind = c["kind"]
    if kind == "hole":
        ps = c.get("positions") or []
        return {"kind_label": "No legal lineup", "figure": esc(len(ps)),
                "unit": "slot" + ("s" if len(ps) != 1 else ""),
                "headline": esc(", ".join(ps)) or "&mdash;",
                "body": "No rostered player can fill these. No amount of value fixes it."}
    if kind == "bye":
        loss = ds.figure(c.get("worst_week_loss")) or "?"
        floor = "&ge;&thinsp;" if c.get("partial") else ""
        out = c.get("starters_out")
        n = len(((fx.get("bye_profile") or {}).get("weeks") or {}))
        # MAGNITUDE AND SCOPE, NEVER A SUPERLATIVE OVER AN OBJECTIVE (VOICE rule 7, corrected).
        # And "still ahead" only when futurity was established: with no current week on file
        # the page may not say the week is ahead of anything.
        scope = (f"The largest of the <b>{esc(n)}</b> weeks still ahead."
                 if c.get("ahead_only") else
                 f"The largest of <b>{esc(n)}</b> measured weeks; no current week is on file, so "
                 f"whether it is ahead is not known.")
        if out:
            scope += f' <b>{esc(out)}</b> starter{"s" if out != 1 else ""} out that week.'
        return {"kind_label": "Bye damage", "figure": f"{floor}{esc(loss)}",
                "unit": currency(), "headline": f'Week <b>{esc(c["worst_week"])}</b>',
                "body": scope}
    if kind == "thin":
        count, covered, band = c.get("count") or 0, c.get("valued_count"), c.get("label")
        rated = (f"Depth here rates <b>{esc(band)}</b> against this league's own rosters."
                 if band else "")
        floor = (f" Only <b>{esc(covered)}</b> of {esc(count)} could be priced, so that "
                 f"comparison is a floor." if c.get("priced_floor") else "")
        return {"kind_label": "Thin room", "figure": esc(count), "unit": "rostered",
                "headline": esc(c["position"]), "body": (rated + floor).strip()}
    return {"kind_label": esc(kind), "figure": "", "unit": "", "headline": esc(kind), "body": ""}


def plain(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


def kv(pairs) -> str:
    return ('<dl class="kv">' + "".join(
        f"<dt>{k}</dt><dd{' class=n' if n else ''}>{v}</dd>" for k, v, n in pairs) + "</dl>")


def expansion(c: dict, fx: dict) -> str:
    """The popover for one claim, or "" where the engine computes no second layer.

    Rule 2 of expansion: what expands must be something the engine computes SEPARATELY. The bye
    popover is `worst_week_detail` -- `bye_collision`'s own per-week solve fields -- and NOT the
    week table, because the weeks are already rows of this register and a popover that repeated
    them would be the page saying the same thing twice in two places.
    """
    kind = c["kind"]
    bp = fx.get("bye_profile") or {}
    if kind == "bye":
        d = bp.get("worst_week_detail") or {}
        if not d:
            return ""
        def f(key, reason):
            v = ds.figure(d.get(key))
            return esc(v) if v is not None else absent(reason)
        conc = bp.get("concentration")
        return (kv([
            ("value lost", f'{f("value_lost", "not measured")} {currency()}', True),
            ("lineup value that week", f("lineup_value", "not measured"), True),
            ("starters out", f("starters_out", "not measured"), True),
            ("players out", f("players_out", "not measured"), True),
            ("bench promoted", f("bench_used", "not measured"), True),
            ("value promoted", f("bench_value_used", "not measured"), True),
            ("share of the season", esc(f"{conc:.0%}") if conc is not None
             else absent("a roster with nothing to lose has no shape; None, not 0%"), True),
        ]) + '<p class="popnote">One solve of the lineup with that week\'s byes removed. '
             '"Promoted" is bench moved up by the solver and what it was worth; the loss is the '
             'gap the promotion could not close. Each week is its own solve, not one number '
             'spread out.</p>')
    if kind == "thin":
        count, covered = c.get("count") or 0, c.get("valued_count")
        return (kv([
            ("rostered", esc(count), True),
            ("priced", esc(covered) if covered is not None
             else absent("the merger priced none of this room"), True),
            ("band", esc(c.get("label") or ""), False),
        ]) + '<p class="popnote">The band is a RATIO against this league\'s own mean, not a '
             'rank. Nothing here orders teams within a position, so there is no "worst in the '
             'league" to report.</p>')
    if kind == "hole":
        return ('<ul class="slots">' + "".join(
            f"<li>{esc(p)}</li>" for p in (c.get("positions") or [])) + "</ul>"
            '<p class="popnote">A hole is a slot the solver leaves EMPTY, not a position missing '
            'from a filter. No amount of value fixes it.</p>')
    return ""


def verdict_prose(claims: list, fx: dict) -> str:
    """The caption's sentences. Thin rooms are COLLECTED into one clause, not one line each."""
    bp = fx.get("bye_profile") or {}
    bits = []
    bye = next((c for c in claims if c["kind"] == "bye"), None)
    if bye is not None:
        total, loss = ds.figure(bp.get("total_loss")), ds.figure(bye.get("worst_week_loss"))
        against = f" of the season's <b>{esc(total)}</b>" if total else ""
        bits.append(f'Week <b>{esc(bye["worst_week"])}</b> costs <b>{esc(loss)}</b>{against} '
                    f'in {currency("bye trade value")}.')
    hole = next((c for c in claims if c["kind"] == "hole"), None)
    if hole is not None:
        bits.append(f'No rostered player can fill {esc(", ".join(hole.get("positions") or []))}.')
    thin = [c for c in claims if c["kind"] == "thin"]
    if thin:
        names = ", ".join(esc(c["position"]) for c in thin[:-1])
        joined = f'{names} and {esc(thin[-1]["position"])}' if names else esc(thin[-1]["position"])
        label = thin[0].get("label") or "thin"
        floor = any(c.get("priced_floor") for c in thin)
        bits.append(f'{joined} {"rates" if len(thin) == 1 else "rate"} <b>{esc(label)}</b> '
                    f'against this league\'s own rosters'
                    + (", one of them on a priced floor." if floor else "."))
    if fx.get("current_week") is None:
        bits.append("No current week is on file, so none of this carries a deadline.")
    return " ".join(bits)


# ---------------------------------------------------------------------------------------------
# ROWS. One function per kind; `build` only decides the order.
# ---------------------------------------------------------------------------------------------
def row(kind: str, margin: str, content: str, figure: str = "", extra: str = "",
        marker: bool = True) -> str:
    return (f'<li class="row {esc(kind)}{(" " + extra) if extra else ""}">'
            f'<div class="m">{margin}</div>'
            f'<div class="k">{"<i></i>" if marker else ""}</div>'
            f'<div class="c">{content}</div>'
            f'<div class="f">{figure}</div></li>')


def margin(kind: str, qual: str = "") -> str:
    return f"<b>{kind}</b>" + (f"<span>{qual}</span>" if qual else "")


def week_rows(fx: dict, pops: list) -> list:
    """The weeks, as rows. Names are a FILTER on `roster[].bye`; nothing is computed here.

    Weeks BEHIND the current week collapse into ONE row. Seven rows each stamped "played" is the
    brief's "absence identical on every row is noise -- state it once", and it is what separates
    a quiet page from a short one. The full list survives in a popover (ruling 1).
    """
    bp = fx.get("bye_profile") or {}
    weeks = bp.get("weeks") or {}
    roster = fx.get("roster") or []
    cw = fx.get("current_week")
    if not weeks:
        return [row("sum", margin("Weeks"), absent("no bye profile was measured for this roster"),
                    marker=False)]
    losses = {w: (v.get("value_lost") if isinstance(v, dict) else v) for w, v in weeks.items()}
    numeric = [v for v in losses.values() if isinstance(v, (int, float))]
    peak = max(numeric) if numeric else 0
    order = sorted(weeks, key=lambda w: int(w))
    behind = [w for w in order if cw is not None and int(w) < int(cw)]
    ahead = [w for w in order if w not in behind]
    worst = max(ahead, key=lambda w: losses[w] if isinstance(losses[w], (int, float)) else -1) \
        if ahead else None

    def week_row(wk, cls=""):
        lost = losses[wk]
        away = [r for r in roster if str(r.get("bye")) == str(wk)]
        who = ('<div class="who">' + "".join(chip(r) for r in away) + "</div>") if away else (
            f'<span class="note">{absent("no rostered player is away this week")}</span>')
        if not isinstance(lost, (int, float)):
            fig = f'<span class="n">{absent("this week carries no measured loss")}</span>'
        else:
            share = (lost / peak) if peak else 0
            tone = (SEVERITY[2][0] if share >= .75 else
                    SEVERITY[1][0] if share >= .35 else SEVERITY[0][0])
            fig = (f'<span class="n">{esc(ds.figure(lost))}</span>'
                   f'<span class="bar {tone}" style="width:{max(3, round(share * 100))}%"></span>')
        # "Week" in Cinzel, the NUMBER in mono: Cinzel's letterspaced "11" reads as Roman II.
        return row("week", f'<b>Week</b><span class="wk">{esc(wk)}</span>', who, fig, cls)

    out = [week_row(w, "peak" if w == worst else "") for w in ahead]
    if behind:
        pid = "played"
        n = len(behind)
        label = (f"All <b>{esc(n)}</b> bye weeks are behind week <b>{esc(cw)}</b>."
                 if not ahead else
                 f"<b>{esc(n)}</b> bye week{'s' if n != 1 else ''} already behind week <b>{esc(cw)}</b>.")
        pops.append(
            f'<div id="{pid}" popover><h4>Weeks already played</h4>'
            f'<table class="weeks"><tbody>' + "".join(
                f'<tr><th>Week {esc(w)}</th><td class="n">'
                f'{esc(ds.figure(losses[w])) if isinstance(losses[w], (int, float)) else absent("no measured loss")}'
                f'</td><td>{", ".join(esc(r.get("name")) for r in roster if str(r.get("bye")) == str(w)) or absent("nobody away")}</td></tr>'
                for w in behind)
            + f'</tbody></table><p class="popnote">Each week was its own solve, in {currency()}. '
              f'They are behind the current week and ask nothing now; they are kept because a '
              f'ledger keeps what happened.</p>'
              f'<div class="popclose"><button class="btn" popovertarget="{pid}" '
              f'popovertargetaction="hide">Close</button></div></div>')
        out.append(row(
            "week", f'<b>Weeks</b><span class="wk">{esc(behind[0])}&ndash;{esc(behind[-1])}</span>',
            f'<span class="note">{label}</span>'
            f'<button class="btn quiet" popovertarget="{pid}">Each week</button>',
            "", "behind"))
    return out


def sum_row(fx: dict) -> str:
    bp = fx.get("bye_profile") or {}
    total, conc, unknown = ds.figure(bp.get("total_loss")), bp.get("concentration"), bp.get("unknown_byes")
    cells = [f'<span>season <b>{esc(total) if total is not None else absent("no season total was measured")}</b> {currency()}</span>']
    cells.append('<span>worst week <b>' + (
        esc(f"{conc:.0%}") if conc is not None else
        absent("a roster with nothing to lose has no shape, so this is None rather than 0%"))
        + "</b> of it</span>")
    cells.append(f'<span>unknown byes <b>{esc(unknown) if unknown is not None else absent("not counted")}</b></span>')
    return row("sum", margin("Season"), '<div class="sums">' + "".join(cells) + "</div>",
               "", marker=False)


def check_rows(band: dict, fx: dict, basis: dict) -> list:
    """ALL the checks, in ladder order. A fired check points back up the register to the row it
    raised, so the list is the complete audit rather than the complement of the claims."""
    out = []
    keymap = {"byes": "bye_profile", "depth": "thin_positions", "holes": "structural_holes"}
    raised = {}
    for c in band["shown"] + band["hidden"]:
        if c["kind"] == "bye":
            raised.setdefault("byes", []).append(f'week {esc(c["worst_week"])}')
        elif c["kind"] == "thin":
            raised.setdefault("depth", []).append(esc(c["position"]))
        elif c["kind"] == "hole":
            raised.setdefault("holes", []).append(", ".join(esc(p) for p in c.get("positions") or []))
    for ch in band["checks"]:
        name, key = ch["name"], keymap.get(ch["name"], "")
        if ch["state"] == fc.CHECK_CLEAN:
            out.append(row("check", margin(esc(name)),
                           f'<span class="t"><span class="tick">&check;</span>nothing found</span>'
                           f'{basis_line(basis, key)}', "", "clean"))
        elif ch["state"] == fc.CHECK_FIRED:
            what = ", ".join(raised.get(name, []))
            out.append(row("check", margin(esc(name)),
                           f'<span class="t">raised &mdash; {what}, above</span>'
                           f'{basis_line(basis, key)}', "", "fired"))
        else:
            out.append(row("check", margin(esc(name)),
                           f'<span class="t">not run {absent(ch["reason"])}</span>', "", "absent",
                           marker=False))
    return out


def provenance_row(fx: dict, basis: dict) -> str:
    """Every absence and every constructed value, ONCE, labelled, with its reason on the dash."""
    items = []
    team = fx.get("team")
    if team:
        items.append(f'<span><em>seat</em> <b>{esc(team)}</b> '
                     f'<span class="tag" tabindex="0" title="{esc(fp.reason_of(basis.get("team", "")))}">'
                     f'{esc(stamp_kind(basis.get("team", "")))}</span></span>')
    if fx.get("league_name"):
        items.append(f'<span><em>league</em> <b>{esc(fx["league_name"])}</b></span>')
    else:
        items.append(f'<span><em>league</em> {absent(fp.reason_of(basis.get("league_name", "")) or "no league name on file")}</span>')
    cw = fx.get("current_week")
    if cw is not None:
        kind = stamp_kind(basis.get("current_week", ""))
        items.append(f'<span><em>week</em> <b>{esc(cw)}</b>' + (
            f' <span class="tag" tabindex="0" title="{esc(fp.reason_of(basis["current_week"]))}">{esc(kind)}</span>'
            if kind != "measured" else "") + "</span>")
    else:
        items.append(f'<span><em>week</em> {absent(fp.reason_of(basis.get("current_week", "")) or "no season position was read")}</span>')
    prov = fx.get("_provenance") or {}
    m = re.search(r"captured_at': '(\d{4}-\d{2}-\d{2})", str(prov.get("players_db") or ""))
    if m:
        items.append(f'<span><em>players captured</em> <b>{esc(m.group(1))}</b></span>')
    fmt = " &middot; ".join(esc(x) for x in (prov.get("format"), prov.get("strategy")) if x)
    if fmt:
        items.append(f'<span><em>arm</em> <b>{fmt}</b></span>')
    items.append(f'<span><em>record</em> off this page <span class="why" tabindex="0" '
                 f'title="team_standings returns it and it is real, and it asks nothing of the reader. '
                 f'It lives in League.">why</span></span>')
    return row("stamp", margin("Provenance"), '<div class="prov">' + "".join(items) + "</div>",
               "", marker=False)


# ---------------------------------------------------------------------------------------------
# THE PAGE
# ---------------------------------------------------------------------------------------------
CSS = """
*{{box-sizing:border-box}}
html,body{{margin:0;background:var(--bg);color:var(--ink)}}
body{{font:400 .95rem/1.55 {sans};-webkit-text-size-adjust:100%}}
.wrap{{max-width:80rem;margin:0 auto;padding:0 20px 56px;--m:9.5rem;--r:2.25rem}}

/* ---- masthead: the one thing above the register ---- */
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
.seat{{font:600 .86rem/1 {mono};color:var(--ink);padding:14px 0;flex:0 0 auto}}

/* ---- THE REGISTER. One list; the rail is one line down its left; every row is a grid of
   four cells -- margin label, rail marker, content, figure -- and the KIND of row decides how
   each cell is weighted. No row has a header of its own: the margin column is the header. ---- */
.register{{list-style:none;margin:30px 0 0;padding:0;position:relative}}
.register::before{{content:"";position:absolute;top:0;bottom:0;left:calc(var(--m) + var(--r)/2);
  width:1px;background:var(--dim);z-index:0}}
.row{{display:grid;grid-template-columns:var(--m) var(--r) minmax(0,1fr) 12rem;
  position:relative;z-index:1}}
.row .m{{grid-column:1;grid-row:1;padding:14px 14px 0 0;text-align:right}}
.row .k{{grid-column:2;grid-row:1;position:relative}}
.row .c{{grid-column:3;grid-row:1;padding:12px 18px 12px 16px;min-width:0}}
.row .f{{grid-column:4;grid-row:1;padding:12px 18px 12px 12px;text-align:right}}
.row::after{{content:"";grid-column:3/-1;grid-row:2;height:1px;
  background:linear-gradient(90deg,rgba(117,80,36,.22),rgba(117,80,36,.04))}}
.row.open::after,.row.caption::after,.row.head::after,.row.stamp::after{{background:none}}

/* margin labels: Cinzel names the KIND; a second line qualifies it. Never a numeral in Cinzel --
   "Week 11" would read as Week II -- so the week number is set in mono. */
.m b{{display:block;font:600 .76rem/1.3 {display};letter-spacing:.2em;text-transform:uppercase;
  color:var(--gold)}}
.m span{{display:block;font:400 .76rem/1.4 {mono};color:var(--dim);margin-top:3px;
  letter-spacing:.02em}}
.m .wk{{font:600 .9rem/1 {mono};color:var(--muted);letter-spacing:0}}
.week .m b,.week .m .wk{{display:inline}}
.week .m .wk{{margin-left:7px;vertical-align:-1px}}

/* rail markers: the marker is the second signal of kind, after the margin label */
.k i{{position:absolute;left:50%;top:21px;transform:translate(-50%,-50%);border-radius:50%;
  width:5px;height:5px;background:var(--dim)}}
.caption .k i{{width:13px;height:13px;background:var(--gold-b);border-radius:2px;
  transform:translate(-50%,-50%) rotate(45deg);top:34px}}
.open .k i{{width:9px;height:9px;background:var(--gold);top:30px}}
.peak .k i{{width:7px;height:7px;background:var(--gold-b)}}
.check.clean .k i{{width:9px;height:9px;background:var(--bg);border:2px solid var(--status-ok)}}
.check.fired .k i{{width:7px;height:7px;background:var(--gold)}}

/* ---- caption: the first entry. The three-second answer, with the lead figure. ---- */
.caption .m{{padding-top:26px}}
.caption .c,.caption .f{{background:linear-gradient(180deg,var(--surface),var(--surface-2));
  border:1px solid var(--line-2);padding-top:22px;padding-bottom:24px}}
.caption .c{{border-right:0;border-radius:6px 0 0 6px;position:relative;overflow:hidden}}
.caption .c::before{{content:"";position:absolute;inset:0 auto 0 0;width:160px;pointer-events:none;
  background:repeating-linear-gradient(135deg,transparent 0 4px,rgba(176,162,138,.07) 4px 5px);
  mask-image:linear-gradient(90deg,#000,transparent);-webkit-mask-image:linear-gradient(90deg,#000,transparent)}}
.caption .f{{border-left:0;border-radius:0 6px 6px 0;grid-column:4;padding-left:0}}
.caption h1{{font:400 2.35rem/1.08 {display};color:var(--gold-b);margin:0 0 12px;
  letter-spacing:.005em;position:relative}}
.caption p{{margin:0;color:var(--muted);max-width:58ch;position:relative}}
.caption p b,.c b{{color:var(--ink);font-family:{mono};font-weight:600;font-size:.9rem}}
.big{{font:600 3rem/1 {mono};color:var(--gold-b);letter-spacing:-.02em;display:block;
  font-variant-numeric:tabular-nums}}
.f .u{{font:400 .78rem/1.3 {display};letter-spacing:.14em;text-transform:uppercase;
  color:var(--dim);display:block;margin-top:8px}}
.f .sub{{display:block;margin-top:12px;font-size:.8rem;color:var(--muted)}}

/* ---- open rows: boxed, because they are the rows that ask something ---- */
.open{{margin-top:12px}}
.open .c,.open .f{{background:linear-gradient(180deg,var(--surface),var(--surface-2));
  border:1px solid var(--line);padding-top:16px;padding-bottom:16px}}
.open .c{{border-right:0;border-radius:5px 0 0 5px;border-left-width:3px;border-left-color:var(--gold)}}
.open.lead .c{{border-left-color:var(--gold-b)}}
.open.thin .c{{border-left-color:var(--line-2)}}
.open .f{{border-left:0;border-radius:0 5px 5px 0}}
.open .f .n{{font:600 1.75rem/1 {mono};color:var(--ink);letter-spacing:-.02em;display:block;
  font-variant-numeric:tabular-nums}}
.open.lead .f .n{{color:var(--gold-b)}}
.chead{{display:flex;align-items:center;gap:10px;margin:0 0 6px;flex-wrap:wrap}}
.chead h2{{font:400 1.12rem/1.3 {sans};margin:0;color:var(--ink)}}
.chead h2 b{{font-size:1.05rem}}
.open p{{margin:0;color:var(--muted);font-size:.9rem;max-width:62ch}}
.pill{{display:inline-flex;align-items:center;height:21px;padding:0 8px;border-radius:3px;
  font:600 .76rem/1 {mono};letter-spacing:.04em}}
.basis{{display:block;margin-top:9px;font:400 .76rem/1.45 {mono};color:var(--dim)}}
.foot{{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px 18px;
  margin-top:8px}}
.foot .basis{{margin-top:0;flex:1 1 20rem}}
.controls{{display:flex;flex-wrap:wrap;gap:8px}}

/* ---- head rows: a divider. The title is in the MARGIN; the content is only the note. ---- */
.head{{margin-top:22px}}
.head .m{{padding-top:12px}}
.head .m b{{color:var(--gold-b);font-size:.82rem}}
.head .c{{padding-top:12px;padding-bottom:8px}}
.head .note,.note{{font:400 .82rem/1.5 {sans};color:var(--dim);font-style:italic}}
.head .c,.head .f{{border-bottom:1px solid var(--line-2)}}

/* ---- week rows: bare, rhythmic, chip-dense ---- */
.week .m{{padding-top:12px}}
.week .c{{padding-top:10px;padding-bottom:10px}}
.week .f{{padding-top:10px;padding-bottom:10px}}
.week .f .n{{font:600 1.05rem/1 {mono};color:var(--ink);display:block;
  font-variant-numeric:tabular-nums}}
.week.peak .f .n{{color:var(--gold-b);font-size:1.3rem}}
.week.peak .c,.week.peak .f{{background:rgba(117,80,36,.13)}}
.week.peak .m .wk{{color:var(--gold-b)}}
.bar{{display:block;height:7px;border-radius:2px;min-width:3px;margin:7px 0 0 auto}}
.bar.recede{{background:var(--dim)}}
.bar.mid{{background:var(--gold)}}
.bar.hot{{background:linear-gradient(90deg,var(--gold),var(--gold-b))}}
.who{{display:flex;flex-wrap:wrap;gap:6px 14px}}
.chip{{display:inline-flex;align-items:center;gap:6px;font-size:.86rem;color:var(--ink);
  white-space:nowrap}}
.chip i{{width:8px;height:8px;border-radius:2px;flex:0 0 auto}}
.chip s{{font-family:{mono};color:var(--muted);text-decoration:none;font-size:.8rem}}
.week.behind .c{{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center}}
.week.behind .note{{font-style:normal;color:var(--muted);font-size:.9rem}}
.week.behind .f .n{{color:var(--muted);font-size:1.3rem}}

/* ---- sum row: the ledger's total line ---- */
.sum .c{{padding-top:12px;padding-bottom:12px}}
.sums{{display:flex;flex-wrap:wrap;gap:6px 22px;font-size:.84rem;color:var(--muted)}}
.sums b{{font-family:{mono};color:var(--ink);font-weight:600}}
.sum .f .u{{margin-top:4px}}

/* ---- check rows ---- */
.check .m{{padding-top:12px}}
.check .c{{padding-top:11px;padding-bottom:11px}}
.check .t{{display:flex;gap:8px;align-items:baseline;color:var(--ink);font-size:.9rem}}
.check .tick{{color:var(--status-ok);flex:0 0 auto}}
.check .basis{{margin-top:5px}}
.check.fired .t{{color:var(--muted)}}

/* ---- provenance: every absence, once, labelled ---- */
.stamp{{margin-top:22px}}
.stamp .m{{padding-top:12px}}
.stamp .c{{padding-top:12px;border-top:1px dashed var(--line)}}
.stamp .f{{border-top:1px dashed var(--line)}}
.prov{{display:flex;flex-wrap:wrap;gap:8px 24px;font-size:.82rem;color:var(--muted)}}
.prov em{{font:400 .76rem/1 {display};letter-spacing:.14em;text-transform:uppercase;
  color:var(--dim);margin-right:6px}}
.prov b{{font-family:{mono};color:var(--ink);font-weight:600}}
.tag{{display:inline-block;margin-left:6px;padding:1px 6px;border:1px dashed var(--dim);
  border-radius:3px;font:400 .76rem/1.3 {mono};color:var(--dim);letter-spacing:.06em;
  text-transform:uppercase;cursor:help}}
.why{{color:var(--dim);border-bottom:1px dotted var(--dim);cursor:help}}

.btn{{display:inline-flex;align-items:center;min-height:44px;padding:0 15px;
  border:1px solid var(--line-2);border-radius:4px;
  background:linear-gradient(180deg,rgba(117,80,36,.26),rgba(117,80,36,.05));
  color:var(--gold-b);font:400 .78rem/1 {display};letter-spacing:.14em;text-transform:uppercase;
  cursor:pointer;text-decoration:none;white-space:nowrap}}
.btn:hover,.btn:focus-visible{{border-color:var(--gold);color:var(--pure)}}
.btn.route{{background:none;border-style:dashed;color:var(--muted)}}
.btn.quiet{{background:none;color:var(--muted);min-height:44px}}

[popover]{{border:1px solid var(--line-2);border-radius:6px;padding:26px;
  background:linear-gradient(180deg,var(--surface),var(--bg));color:var(--ink);
  max-width:min(36rem,92vw);box-shadow:0 24px 64px rgba(0,0,0,.8)}}
[popover]::backdrop{{background:rgba(4,3,2,.74)}}
[popover] h4{{font:600 .82rem/1 {display};letter-spacing:.2em;text-transform:uppercase;
  margin:0 0 16px;color:var(--gold)}}
.popnote{{color:var(--dim);font-size:.78rem;margin:14px 0 0;max-width:48ch}}
.popclose{{margin-top:18px}}
dl.kv{{display:grid;grid-template-columns:auto 1fr;gap:7px 18px;margin:0}}
dl.kv dt{{font:400 .78rem/1.5 {display};letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted)}}
dl.kv dd{{margin:0;color:var(--ink);font-size:.9rem}}
dl.kv dd.n{{font-family:{mono};font-variant-numeric:tabular-nums;font-size:1.05rem}}
table.weeks{{width:100%;border-collapse:collapse;font-size:.86rem}}
.weeks th{{font:400 .76rem/1 {display};letter-spacing:.14em;text-transform:uppercase;
  text-align:left;color:var(--muted);padding:6px 12px 6px 0;white-space:nowrap}}
.weeks td{{padding:6px 12px 6px 0;color:var(--muted)}}
.weeks td.n{{font-family:{mono};text-align:right;color:var(--ink);font-variant-numeric:tabular-nums}}
ul.slots{{margin:0;padding-left:20px;font-size:.92rem}}

.absent{{color:var(--dim);cursor:help;border-bottom:1px dotted var(--dim)}}
.currency{{color:var(--muted);cursor:help;border-bottom:1px dotted var(--gold);font-style:normal}}
.dock{{margin-top:22px;padding-top:16px;border-top:1px dashed var(--line);
  display:flex;align-items:center;gap:14px;flex-wrap:wrap}}
.dock .note{{font-style:normal}}

@media (max-width:900px){{
  .row{{grid-template-columns:var(--m) var(--r) minmax(0,1fr) 9rem}}
  .big{{font-size:2.5rem}}
}}
@media (max-width:640px){{
  .wrap{{padding:0 16px 44px;--m:0rem;--r:1.5rem}}
  .register{{margin-top:22px}}
  .register::before{{left:calc(var(--r)/2)}}
  .row{{grid-template-columns:var(--r) minmax(0,1fr) auto}}
  .row .m{{grid-column:2;grid-row:1;text-align:left;padding:12px 0 0 12px}}
  .m b,.m span{{display:inline}}
  .m span{{margin-left:8px}}
  .row .k{{grid-column:1;grid-row:1/3}}
  .row .c{{grid-column:2/-1;grid-row:2;padding:6px 12px 12px 12px}}
  .row .f{{grid-column:3;grid-row:1;padding:10px 12px 0 12px;max-width:11rem}}
  .f .u{{margin-top:4px}}
  .row::after{{grid-column:2/-1;grid-row:3}}
  .k i{{top:19px}}
  .caption .k i,.open .k i{{top:19px}}
  .caption .m,.open .m{{padding:14px 0 0 14px;border:1px solid var(--line-2);border-right:0;
    border-bottom:0;border-radius:6px 0 0 0;background:var(--surface)}}
  .caption .f,.open .f{{border:1px solid var(--line-2);border-left:0;border-bottom:0;
    border-radius:0 6px 0 0;background:var(--surface);padding:14px 14px 0 8px}}
  .open .m,.open .f{{border-color:var(--line)}}
  .open .m{{border-left-width:3px;border-left-color:var(--gold)}}
  .open.lead .m{{border-left-color:var(--gold-b)}}
  .open.thin .m{{border-left-color:var(--line-2)}}
  .caption .c,.open .c{{border-top:0;border-radius:0 0 6px 6px;padding:6px 14px 18px 14px}}
  .caption .c::before{{display:none}}
  .caption h1{{font-size:1.72rem;margin-top:6px}}
  .week.peak .f{{background:rgba(117,80,36,.13)}}
  .caption .f .sub{{display:none}}
  .week.peak .m{{background:rgba(117,80,36,.13)}}
  .week .bar{{display:none}}
  .head .m,.head .f,.stamp .f,.sum .f{{display:none}}
  .head .c{{padding-top:0}}
  .head .c::before{{content:attr(data-title);display:block;font:600 .82rem/1.3 {display};
    letter-spacing:.2em;text-transform:uppercase;color:var(--gold-b);margin:18px 0 4px}}
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


def head_row(title: str, note: str) -> str:
    """A divider. On the phone the margin column is gone, so the title is repeated from a data
    attribute by CSS rather than emitted twice in markup -- one home for the string."""
    return (f'<li class="row head"><div class="m"><b>{title}</b></div><div class="k"></div>'
            f'<div class="c" data-title="{esc(plain(title))}"><span class="note">{note}</span></div>'
            f'<div class="f"></div></li>')


def build(fx: dict) -> str:
    _assert_ramp_is_visible()
    _assert_marks_visible()
    _assert_type_floor()
    band = fc.compose(fx)
    shown, hidden = band["shown"], band["hidden"]
    summary = fc.checks_summary(band["checks"])
    basis = (fx.get("_provenance") or {}).get("basis") or {}
    rows, pops = [], []

    # ---- caption -----------------------------------------------------------------------------
    n = len(shown) + len(hidden)
    words = {0: "Nothing", 1: "One thing", 2: "Two things", 3: "Three things", 4: "Four things"}
    headline = ("Nothing open this week." if not n
                else f'{words.get(n, str(n) + " things")} {"is" if n == 1 else "are"} open.')
    if shown:
        lead = claim_parts(shown[0], fx)
        fig = (f'<span class="big">{lead["figure"]}</span><span class="u">{lead["unit"]}</span>'
               f'<span class="sub">{lead["kind_label"]} &middot; {lead["headline"]}</span>')
        prose = verdict_prose(shown + hidden, fx)
    else:
        fig = (f'<span class="big">{summary["ran"]}</span><span class="u">checks, all clean</span>'
               f'<span class="sub">{esc(", ".join(summary["clean"]))}</span>')
        prose = ("Every check this page runs came back clean. The register below is what was "
                 "examined to say so.")
    rows.append(row("caption", margin("The answer"), f"<h1>{headline}</h1><p>{prose}</p>", fig))

    # ---- open rows ---------------------------------------------------------------------------
    for i, c in enumerate(shown):
        parts, exp, pid = claim_parts(c, fx), expansion(c, fx), f"exp{i}"
        pos = c.get("position") or (c.get("positions") or [None])[0]
        controls = [f'<a class="btn route" href="#{esc(c["route"].lower().replace(" ", "-"))}">'
                    f'{esc(c["route"])} &rsaquo;</a>']
        if exp:
            controls.insert(0, f'<button class="btn" popovertarget="{pid}">What it is made of</button>')
            pops.append(f'<div id="{pid}" popover><h4>{parts["kind_label"]} &middot; '
                        f'{plain(parts["headline"])}</h4>{exp}<div class="popclose">'
                        f'<button class="btn" popovertarget="{pid}" popovertargetaction="hide">'
                        f'Close</button></div></div>')
        key = {"bye": "bye_profile", "thin": "thin_positions", "hole": "structural_holes"}[c["kind"]]
        content = (f'<div class="chead">{pill(pos) if pos else ""}<h2>{parts["headline"]}</h2></div>'
                   f'<p>{parts["body"]}</p>'
                   f'<div class="foot">{basis_line(basis, key)}'
                   f'<div class="controls">{"".join(controls)}</div></div>')
        figure = f'<span class="n">{parts["figure"]}</span><span class="u">{parts["unit"]}</span>'
        rows.append(row("open", margin("Open", parts["kind_label"]), content, figure,
                        f'{esc(c["kind"])}{" lead" if i == 0 else ""}'))
    if hidden:
        also = "; ".join(f'{claim_parts(c, fx)["kind_label"]}: {plain(claim_parts(c, fx)["headline"])}'
                         for c in hidden)
        rows.append(row("sum", margin("Also", "standing"),
                        f'<span class="note">Beyond the cap of {fc.CAP}: {also}.</span>', "",
                        marker=False))

    # ---- the weeks ---------------------------------------------------------------------------
    weeks = (fx.get("bye_profile") or {}).get("weeks") or {}
    if weeks:
        rows.append(head_row("The weeks", f"each re-solved with that week's byes removed &middot; "
                             f"value lost, not bodies &middot; in {currency()}"))
        rows.extend(week_rows(fx, pops))
        rows.append(sum_row(fx))

    # ---- the checks --------------------------------------------------------------------------
    rows.append(head_row("Checked", f"{esc(summary['ran'])} of {len(fc.CHECKS)} checks ran, in ladder "
                         f"order &middot; a check that raised something points back up the page"))
    rows.extend(check_rows(band, fx, basis))

    # ---- provenance --------------------------------------------------------------------------
    rows.append(provenance_row(fx, basis))

    doors = "".join(f'<a class="door" href="#{esc(r.lower().replace(" ", "-"))}">{esc(r)}</a>'
                    for r in ROOMS)
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
    <span class="crest">{WYRM}<span class="word">Gold Wyrm<b>Dynasty</b></span></span>
    <nav class="doors">{doors}</nav>
    <span class="seat">{esc(fx.get("team") or "")}</span>
  </header>

  <ol class="register">
{"".join(rows)}
  </ol>

  <div class="dock">
    <a class="btn route" href="#prytaneum">{esc(DOCK)}</a>
    <span class="note">A dock rendered under every room, not a sixth room.</span>
  </div>
</div>
{"".join(pops)}
</body></html>
"""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    jobs = [(pathlib.Path(argv[0]), pathlib.Path(argv[1]))] if len(argv) >= 2 else FIXTURES
    for fix, out in jobs:
        out.write_text(build(json.loads(fix.read_text())))
        print(f"{out}  {len(out.read_text()):,} bytes  from {fix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
