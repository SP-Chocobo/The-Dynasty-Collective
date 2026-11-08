#!/usr/bin/env python3
"""THE DISPATCH -- the dashboard as something composed to be READ, not parsed (round 6).

THE QUESTION THIS SLUG ANSWERS. The base (`round5/build_dashboard.py`) presents its facts as
labelled cards and a table, and the eye PARSES them: find the label, find the cell, read the
number. This page tries the opposite: a front page, written. A lede that states the situation in
sentences, the figures that carry weight pulled out at display scale, and the supporting detail
set as short written entries around them. The same ten quantities, arranged as language.

WHY THAT IS THE MOST DANGEROUS THING TO TRY HERE, and what this file does about it. Prose
outrunning its function is this project's worst recorded defect: `#336b` shipped "bottom of this
league at the position" for months on a figure that ranks nothing. A page MADE of sentences is
the easiest place in the world to assert something untrue, because a sentence can be grammatical
without being measured. So the discipline is mechanical rather than hoped for:

  * EVERY SENTENCE IS A FUNCTION OF A FIXTURE FIELD. The composers below take the claim or the
    profile and return the sentence; there is no free-text paragraph anywhere. If the field is
    absent the sentence is not written -- the em dash carrying its reason is written instead.
  * EVERY FIGURE GOES THROUGH `design_system.figure` and is wrapped as `<b class="n">`, so a
    number in running text is still mono, still tabular, still visibly a quantity -- never a
    word pretending to be one.
  * SCOPE IS STATED, NEVER IMPLIED. "the largest of the six weeks measured" (`len(weeks)`, and
    `max`) -- not "the one that hurts", which `VOICE.md`'s own correction withdrew. "rates Weak
    against this league's own rosters" (`depth_label`) -- never a rank.
  * THE CHECKS ARE NAMED, NOT CONCLUDED. `front_claims.checks_run` is the only source of what was
    examined; the page never counts its own checks (`#338`).

A ZERO THE BASE PRINTS THAT IS NOT A ZERO. `capture_front_fixture.py:157` writes a roster
player's `value` as `priced.get("trade_value") or 0.0`, so a 0.0 on the roster is "unpriced OR
priced at exactly zero", collapsed. The base's ledger prints `Tyler Bass 0`; the TE room on the
same page says "1 of 2 priced" about Pitts (23) and Knox (0.0). Those cannot both be read as
written. This page renders a roster value of exactly 0.0 as an ABSENCE carrying that reason,
which is `#187`'s contract applied at the one place the fixture cannot keep it itself.

A READING FACE, DECLARED HERE AND FLAGGED. `design_system` holds a display face, a mono and a
sans; the deck the owner chose for feel set its running text in Source Serif 4, and a page whose
thesis is "this reads" needs a face built for reading. It is declared ONCE below as FONT_TEXT
and `NOTES.md` says plainly that if this direction is taken, the constant belongs in
`design_system` and not here (`#126`: one home).

Renders from the fixtures, never hand-authored. `front_claims.compose` supplies the judgment;
this file supplies the grammar.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

import design_system as ds  # noqa: E402
import front_claims as fc   # noqa: E402
import front_page as fp     # noqa: E402

FIXTURES = (
    (ROOT / "ui_explore/front_fixture.json", HERE / "dispatch.html"),
    (ROOT / "ui_explore/quiet_fixture.json", HERE / "dispatch_quiet.html"),
)

#: The reading face. NOT a design_system token today -- see the module docstring. Georgia and
#: Times are the fallbacks so the page still reads as a broadsheet with the web font blocked.
FONT_TEXT = '"Source Serif 4", Georgia, "Times New Roman", serif'

ROOMS = ("Matchup", "Roster Maintenance", "Draft Room", "League", "Import Audit")
DOCK = "The Prytaneum"

# ---------------------------------------------------------------------------------------------
# THE GATES, AS ASSERTIONS THAT FAIL THE BUILD. Copied in pattern from the base.
# ---------------------------------------------------------------------------------------------
NON_TEXT_FLOOR = 3.0
TEXT_FLOOR = 4.5
TYPE_FLOOR_REM = 0.75  # 12px at a 16px root

#: Every colour this page uses as a MARK rather than as text -- the position squares beside each
#: name, the tick on a clean check, the gold on the pulled figure and the peak-week rail -- each
#: checked against both grounds it can sit on. No severity ramp exists on this page: the bye
#: weeks are told by the SIZE of their figure, not by a bar, so there is no bar to fail.
MARK_TOKENS = ("gold", "gold-b", "status-ok", "muted", "dim")
GROUNDS = ("bg", "surface", "surface-2")
#: Text colours, and the grounds they sit on, held to the AA body floor.
TEXT_TOKENS = ("ink", "muted", "dim", "gold", "gold-b", "pure")


def _assert_marks_visible():
    """A mark nobody can see is a missing mark. Round 4 shipped three charts whose bars sat at
    1.25:1-2.30:1 and nobody noticed by eye; `design_system.contrast_ratio` is the instrument,
    and position pill hexes -- which are not TOKENS -- go through the same arithmetic."""
    bad = []
    for ground in GROUNDS:
        for tok in MARK_TOKENS:
            r = ds.contrast_ratio(tok, ground)
            if r < NON_TEXT_FLOOR:
                bad.append((tok, ground, round(r, 2)))
        for pos, hexv in ds.POSITION_PILL_TOKENS.items():
            r = ds._contrast_hex(hexv, ds.TOKENS[ground])
            if r < NON_TEXT_FLOOR:
                bad.append((pos, ground, round(r, 2)))
    if bad:
        raise SystemExit(f"marks below the {NON_TEXT_FLOOR}:1 non-text floor: {bad}")


def _assert_text_legible():
    bad = [(tok, ground, round(ds.contrast_ratio(tok, ground), 2))
           for ground in GROUNDS for tok in TEXT_TOKENS
           if ds.contrast_ratio(tok, ground) < TEXT_FLOOR]
    if bad:
        raise SystemExit(f"text below the {TEXT_FLOOR}:1 body floor: {bad}")


def _assert_type_floor():
    """No declared size under 12px. Small type is declared in rem throughout so this is a regex,
    not a browser; an `em` font-size would defeat it and is refused outright."""
    css = render_css()
    under = sorted({float(m.group(1))
                    for m in re.finditer(r"font(?:-size)?:[^;}]*?([\d.]+)rem", css)
                    if float(m.group(1)) < TYPE_FLOOR_REM})
    if under:
        raise SystemExit(f"declared font sizes below the {TYPE_FLOOR_REM}rem floor: {under}")
    ems = [m.group(0) for m in re.finditer(r"font(?:-size)?:[^;}]*?[\d.]+em\b", css)]
    if ems:
        raise SystemExit(f"small type must be declared in rem, not em: {ems}")


# ---------------------------------------------------------------------------------------------
# THE GRAMMAR OF A FIGURE -- four states, visibly distinct, never collapsed.
# ---------------------------------------------------------------------------------------------
def esc(value) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def n(value, digits: int = 0, floor: bool = False) -> str:
    """A measured figure set INTO a sentence: mono, tabular, bold. A floor carries `>=` as part
    of the figure itself, never as a footnote the eye can skip."""
    text = ds.figure(value, digits)
    if text is None:
        return absent("this quantity was not measured")
    pre = '<span class="ge" title="a floor: part of this room could not be priced">&ge;</span>' if floor else ""
    return f'<b class="n{" floor" if floor else ""}">{pre}{esc(text)}</b>'


def pct(value) -> str:
    if value is None:
        return absent("a roster with nothing to lose has no shape, so this is None rather than 0%")
    return f'<b class="n">{esc(f"{value:.0%}")}</b>'


def absent(reason: str) -> str:
    """The em dash carrying its reason. Never 0, never blank, never a reassuring default."""
    return f'<span class="absent" tabindex="0" title="{esc(reason)}">&mdash;</span>'


def constructed(label: str, reason: str) -> str:
    return (f'<span class="stamp" tabindex="0" title="{esc(reason)}">{esc(label)}</span>')


#: The owner's ruling (`#341`): grading belongs in league points; `bye_collision` prices in
#: whatever its caller supplies, and this page supplies dynasty trade value. The conversion is
#: unbuilt, so the figure says what it is.
CURRENCY = ("dynasty trade value, not this league's points. `bye_collision` prices whatever "
            "its caller supplies and this page supplies Draft Sharks Dynasty Rankings value, "
            "selected by a three-field format hint, so a league's own bonuses never reach it. "
            "The ruling is that grading belongs in league points; that conversion is not built")


def currency(text: str = "trade value") -> str:
    return f'<span class="currency" tabindex="0" title="{esc(CURRENCY)}">{esc(text)}</span>'


def basis_kind(raw: str) -> str:
    raw = raw or ""
    return ("absent" if raw.startswith("ABSENT") else
            "constructed" if raw.startswith("CONSTRUCTED") else "measured")


def provenance(basis: dict, key: str) -> str:
    """The mono line under a figure: `measured - what measured it`. It is the honesty, made
    visible, and it is also texture: a column whose entries each end in a provenance line
    cannot read as an empty div."""
    raw = (basis or {}).get(key) or ""
    kind = basis_kind(raw)
    body = fp.reason_of(raw) if raw else "no basis recorded for this quantity"
    if kind == "absent":
        return f'<p class="prov">{absent(body)}</p>'
    short = body if len(body) <= 84 else body[:81].rstrip() + "..."
    return f'<p class="prov" title="{esc(body)}">{esc(kind)} &middot; {esc(short)}</p>'


def mark(position: str) -> str:
    """The position's own colour, from one home (`design_system.POSITION_PILL_TOKENS`), as a
    small square and the abbreviation beside it -- the roster's vocabulary kept in colour even
    inside a sentence."""
    _, fg = ds.position_pill_color(position or "")
    return (f'<span class="pos" style="color:{fg}"><i style="background:{fg}"></i>'
            f'{esc(position or "?")}</span>')


def pill(position: str) -> str:
    bg, fg = ds.position_pill_color(position or "")
    return f'<span class="pill" style="background:{bg};color:{fg}">{esc(position)}</span>'


def player_value(r: dict) -> str:
    """A roster value, with the capture's one collapse undone. `capture_front_fixture.py` writes
    `trade_value or 0.0`, so exactly 0.0 cannot be told from "no price" -- and on the same page
    the TE room is counted as 1 of 2 priced with Knox at 0.0. A zero here is therefore an
    absence until the capture carries None, and it is rendered as one."""
    v = r.get("value")
    if v is None or (isinstance(v, (int, float)) and float(v) == 0.0):
        return absent("unpriced: the capture writes 0.0 where the merger returned no price "
                      "(`trade_value or 0.0`), so a zero here cannot be told from an absence")
    return n(v)


#: Small COUNTS set as words, the way a broadsheet sets them. This is deliberately narrow: it
#: applies to the SCOPE of a sentence (how many weeks were measured, how many checks ran), never
#: to a measured figure. A cost, a week number, a roster count or a share is always mono --
#: "Week 6 costs 95, the largest of six weeks measured" keeps the two kinds of number apart.
WORDS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
         "eleven", "twelve")


def count_word(k, cap: bool = False) -> str:
    try:
        k = int(k)
    except (TypeError, ValueError):
        return n(k)
    if 0 <= k < len(WORDS):
        w = WORDS[k]
        return w.capitalize() if cap else w
    return n(k)


def join_names(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


# ---------------------------------------------------------------------------------------------
# THE SENTENCES. Each one is a function of the engine's fields and nothing else.
# ---------------------------------------------------------------------------------------------
def bye_sentence(c: dict, bp: dict, cw) -> str:
    """`Week 6 costs 95 in trade value, the largest of the six weeks measured, with one
    starter out.` Magnitude and scope, both measured; no superlative over an objective
    (`VOICE.md`, the correction)."""
    weeks = bp.get("weeks") or {}
    scope_n = len(weeks)
    scope = ("still ahead" if c.get("ahead_only") else "measured")
    out = c.get("starters_out")
    tail = ""
    if isinstance(out, int) and out > 0:
        tail = f", with {n(out)} starter{'s' if out != 1 else ''} out"
    scope_txt = (f", the largest of {count_word(scope_n)} weeks {scope}" if scope_n > 1 else
                 f", the only week {scope}" if scope_n == 1 else "")
    return (f'Week {n(c["worst_week"])} costs {n(c.get("worst_week_loss"), floor=bool(c.get("partial")))} '
            f'in {currency()}{scope_txt}{tail}.')


def holes_sentence(c: dict) -> str:
    ps = c.get("positions") or []
    return f'No rostered player can fill {esc(join_names([str(p) for p in ps]))}.'


def thin_sentence(thins: list[dict]) -> str:
    """Thin rooms COLLECTED by label into one clause each. `depth_label` is a ratio band against
    the league mean and nothing ranks teams, so the verb is `rate`, the object is the label, and
    the comparison set is named."""
    by_label: dict[str, list[dict]] = {}
    for t in thins:
        by_label.setdefault(t.get("label") or "thin", []).append(t)
    clauses = []
    for label, group in by_label.items():
        names = join_names([esc(t["position"]) for t in group])
        verb = "rates" if len(group) == 1 else "rate"
        if str(label).startswith("None"):
            clauses.append(f'{names} {"has" if len(group) == 1 else "have"} no rostered player at all')
        else:
            clauses.append(f'{names} {verb} <b class="lbl">{esc(label)}</b> against this league&rsquo;s own rosters')
    floors = [t for t in thins if t.get("priced_floor")]
    if floors:
        parts = [f'{esc(t["position"])} on a priced floor, {n(t.get("valued_count"))} of {n(t.get("count"))} priced'
                 for t in floors]
        return "; ".join(clauses) + "; " + "; ".join(parts) + "."
    return "; ".join(clauses) + "."


def week_on_file(fx: dict, basis: dict) -> str:
    cw = fx.get("current_week")
    if cw is None:
        return "No current week is on file, so none of this carries a deadline."
    stamp = ""
    if basis_kind(basis.get("current_week", "")) == "constructed":
        stamp = " " + constructed("constructed", fp.reason_of(basis.get("current_week", "")))
    return f"Week {n(cw)} is on file.{stamp}"


def lede(band: dict, fx: dict, basis: dict) -> tuple[str, str]:
    """(headline, lede paragraph). The headline is the count of open things -- the one honest
    headline (`STRUCTURE.md` section 2): a count, never a grade."""
    shown, hidden = band["shown"], band["hidden"]
    claims = shown + hidden
    k = len(claims)
    words = {0: "Nothing", 1: "One thing", 2: "Two things", 3: "Three things", 4: "Four things",
             5: "Five things"}
    headline = ("Nothing open this week." if not k else
                f'{words.get(k, str(k) + " things")} {"is" if k == 1 else "are"} open.')
    sents = []
    bp = band["bye_profile"] or {}
    if k:
        hole = next((c for c in claims if c["kind"] == "hole"), None)
        if hole:
            sents.append(holes_sentence(hole))
        bye = next((c for c in claims if c["kind"] == "bye"), None)
        if bye:
            sents.append(bye_sentence(bye, bp, fx.get("current_week")))
        thins = [c for c in claims if c["kind"] == "thin"]
        if thins:
            sents.append(thin_sentence(thins))
        sents.append(week_on_file(fx, basis))
    else:
        summ = fc.checks_summary(band["checks"])
        if summ["ran"]:
            sents.append(f'{count_word(summ["ran"], cap=True)} check{"s" if summ["ran"] != 1 else ""} ran '
                         f'&mdash; {esc(", ".join(summ["clean"] + summ["fired"]))} &mdash; '
                         f'and none raised a claim.')
        if summ["absent"]:
            sents.append(f'{esc(join_names(summ["absent"]))} did not run: '
                         + absent("no data for this check in what the page was built from") + ".")
        cw = fx.get("current_week")
        weeks = bp.get("weeks") or {}
        if cw is not None and bp.get("_ahead_only") and bp.get("worst_week") is None and weeks:
            last = max(int(w) for w in weeks)
            stamp = ""
            if basis_kind(basis.get("current_week", "")) == "constructed":
                stamp = " " + constructed("constructed", fp.reason_of(basis.get("current_week", "")))
            sents.append(f'Week {n(cw)} is on file{stamp} and the last measured bye week was '
                         f'{n(last)}, so every bye is behind it.')
        else:
            sents.append(week_on_file(fx, basis))
        sents.append("What was examined to say so is set out below, each entry with its basis.")
    return headline, " ".join(sents)


def pulled_figure(band: dict, fx: dict, basis: dict) -> str:
    """THE FIGURE IS THE HERO. One number at display scale, pulled out of the lede the way a
    broadsheet pulls a figure into the margin, with what it is and where it came from beneath."""
    shown = band["shown"]
    if shown and shown[0]["kind"] == "bye":
        c = shown[0]
        fig = ds.figure(c.get("worst_week_loss")) or "?"
        ge = '<span class="ge">&ge;</span>' if c.get("partial") else ""
        return (f'<div class="pull"><span class="big">{ge}{esc(fig)}</span>'
                f'<span class="unit">{currency()} &middot; week {esc(c["worst_week"])}</span>'
                f'{provenance(basis, "bye_profile")}</div>')
    if shown and shown[0]["kind"] == "hole":
        ps = shown[0].get("positions") or []
        return (f'<div class="pull"><span class="big">{esc(len(ps))}</span>'
                f'<span class="unit">slot{"s" if len(ps) != 1 else ""} no one can fill</span>'
                f'{provenance(basis, "structural_holes")}</div>')
    if shown and shown[0]["kind"] == "thin":
        c = shown[0]
        return (f'<div class="pull">{pill(c["position"])}<span class="big">{esc(c.get("count") or 0)}</span>'
                f'<span class="unit">rostered &middot; {esc(c.get("label") or "")}</span>'
                f'{provenance(basis, "thin_positions")}</div>')
    summ = fc.checks_summary(band["checks"])
    names = " &middot; ".join(esc(x) for x in summ["clean"])
    close = ('<a class="btn close" href="#close">Close the app</a>')
    return (f'<div class="pull quiet"><span class="big">{esc(summ["ran"])}</span>'
            f'<span class="unit">checks ran, all clean</span>'
            f'<p class="prov">{names}</p>{close}</div>')


# ---------------------------------------------------------------------------------------------
# THE COLUMNS
# ---------------------------------------------------------------------------------------------
def who_is_away(away: list[dict], starters: set) -> str:
    """`Jahmyr Gibbs (RB - 95) is away.` A FILTER on roster[].bye -- arranging, not computing.
    Names in the constructed lineup are underlined, and the legend says so once."""
    if not away:
        return absent("no rostered player is away this week")
    bits = []
    for r in away:
        st = ' class="st"' if str(r.get("id")) in starters else ""
        bits.append(f'<span{st}>{esc(r.get("name") or "?")}</span> <span class="nw">({mark(r.get("position"))}'
                    f'&thinsp;&middot;&thinsp;{player_value(r)})</span>')
    verb = "is" if len(away) == 1 else "are"
    return f'{join_names(bits)} {verb} away.'


def bye_column(band: dict, fx: dict, basis: dict) -> str:
    raw = fx.get("bye_profile") or {}
    bp = band["bye_profile"] or {}
    # The RESOLVED profile narrows `weeks` to those ahead when a week is known and some remain;
    # with none remaining it keeps them all and sets worst_week None. Either way every week in
    # the raw profile is measured, and the page shows all of them, marking those behind.
    weeks = raw.get("weeks") or {}
    cw = fx.get("current_week")
    if not weeks:
        return (f'<section class="col"><h2 class="eyebrow">The bye weeks</h2>'
                f'<p class="intro">{absent("no bye profile was measured for this roster")}</p></section>')
    roster = fx.get("roster") or []
    starters = {str(s) for s in (fx.get("starters") or [])}
    live_worst = bp.get("worst_week")
    detail = raw.get("worst_week_detail") or {}
    raw_worst = raw.get("worst_week")
    partial = raw.get("basis") != "measured"
    entries = []
    for wk in sorted(weeks, key=lambda w: int(w)):
        cell = weeks[wk]
        lost = cell.get("value_lost") if isinstance(cell, dict) else cell
        behind = cw is not None and int(wk) < int(cw)
        peak = (live_worst is not None and int(wk) == int(live_worst)) or (
            live_worst is None and raw_worst is not None and int(wk) == int(raw_worst))
        away = [r for r in roster if str(r.get("bye")) == str(wk)]
        fig = (n(lost, floor=partial) if isinstance(lost, (int, float))
               else absent("this week carries no measured loss"))
        extra = ""
        if peak and detail and int(wk) == int(raw_worst):
            so, lv = detail.get("starters_out"), detail.get("lineup_value")
            bits = []
            if isinstance(so, int):
                bits.append(f'{count_word(so, cap=True)} starter{"s" if so != 1 else ""} out')
            if lv is not None:
                bits.append(f'the lineup that week {"was" if behind else "is"} worth {n(lv)}')
            if bits:
                extra = f' <span class="detail">{"; ".join(bits)}.</span>'
        cls = " ".join(x for x in ("wk", "peak" if peak else "", "behind" if behind else "") if x)
        # "Behind" is said ONCE, in the intro, and shown by the row's tone -- not repeated on
        # every row (`BRIEF.md`: an absence identical on every row is noise).
        verb_note = ""
        entries.append(
            f'<div class="{cls}"><div class="wkhead"><span class="wklabel">Week {esc(wk)}</span>'
            f'<span class="wkfig">{fig}</span></div>'
            f'<p class="wkwho">{who_is_away(away, starters)}{extra}{verb_note}</p></div>')
    total, conc, unknown = raw.get("total_loss"), raw.get("concentration"), raw.get("unknown_byes")
    past = live_worst is None
    if raw_worst is not None:
        foot = (f'Across the season the byes {"cost" if past else "cost"} {n(total)}; week '
                f'{n(raw_worst)} {"carried" if past else "carries"} {pct(conc)} of it.')
    else:
        foot = f'Across the season the byes cost {n(total)}.'
    foot += f' Unknown byes: {n(unknown) if unknown is not None else absent("unknown_byes was not reported")}.'
    intro = ("Each week below is the lineup solved again with that week&rsquo;s byes removed. "
             f"The figure is value lost in {currency()}, not bodies away.")
    if cw is not None:
        intro += f" Weeks before {n(cw)} have passed."
    legend = ""
    if starters:
        legend = (f'<p class="legend"><span class="st">Underlined</span> names are in the lineup '
                  f'{constructed("constructed", fp.reason_of(basis.get("starters", "")))} by '
                  f'<code>optimize_lineup</code>, not one a human submitted.</p>')
    pop = ""
    if detail and raw_worst is not None:
        pid = "pop-bye"
        rows = []
        for key, label in (("lineup_value", "lineup value that week"),
                           ("value_lost", "value lost"),
                           ("players_out", "players away"),
                           ("starters_out", "of them starters"),
                           ("bench_used", "bench bodies promoted"),
                           ("bench_value_used", "their value")):
            v = detail.get(key)
            rows.append(f'<dt>{esc(label)}</dt><dd>{n(v) if v is not None else absent("not reported for this week")}</dd>')
        pop = (f'<button class="btn" popovertarget="{pid}">What week {esc(raw_worst)} is made of</button>'
               f'<div id="{pid}" popover><h4>Week {esc(raw_worst)}, as measured</h4>'
               f'<dl class="kv">{"".join(rows)}</dl>'
               f'<p class="popnote">Six fields <code>bye_collision</code> returns for this week, in '
               f'{currency()}. Basis: {esc(detail.get("basis") or "unknown")}.</p>'
               f'<div class="popclose"><button class="btn" popovertarget="{pid}" '
               f'popovertargetaction="hide">Close</button></div></div>')
    route = '<a class="btn route" href="#matchup">Matchup &rsaquo;</a>'
    return (f'<section class="col byes"><h2 class="eyebrow">The bye weeks</h2>'
            f'<p class="intro">{intro}</p>{provenance(basis, "bye_profile")}'
            f'<div class="weeks">{"".join(entries)}</div>'
            f'<p class="foot">{foot}</p>{legend}'
            f'<div class="row">{pop}{route}</div></section>')


def open_column(band: dict, fx: dict, basis: dict) -> str:
    """Holes and thin rooms as short written entries. Returns "" when none is open, because a
    heading over nothing is the unfinished look the quiet state must not have."""
    shown = band["shown"]
    items = [c for c in shown if c["kind"] in ("hole", "thin")]
    if not items:
        return ""
    entries, pops = [], []
    for i, c in enumerate(items):
        if c["kind"] == "hole":
            ps = c.get("positions") or []
            entries.append(
                f'<article class="entry hole"><p class="line">{n(len(ps))} slot'
                f'{"s" if len(ps) != 1 else ""} no one can fill</p>'
                f'<p class="text">{holes_sentence(c)} A hole is a slot the solver leaves empty; '
                f'no amount of value fixes it.</p>{provenance(basis, "structural_holes")}'
                f'<div class="row"><a class="btn route" href="#roster-maintenance">Roster Maintenance &rsaquo;</a></div>'
                f'</article>')
            continue
        count, covered, label = c.get("count") or 0, c.get("valued_count"), c.get("label")
        pid = f"pop-thin-{i}"
        priced = (n(covered) if covered is not None else
                  absent("the merger priced none of this room"))
        text = (f'Depth here rates <b class="lbl">{esc(label)}</b> against this league&rsquo;s own rosters.'
                if label and not str(label).startswith("None") else
                "No rostered player here at all." if label else "")
        if c.get("priced_floor"):
            text += f' Only {n(covered)} of {n(count)} could be priced, so the comparison is a floor.'
        entries.append(
            f'<article class="entry thin">{pill(c["position"])}'
            f'<p class="line">{n(count)} rostered &middot; {priced} priced</p>'
            f'<p class="text">{text}</p>{provenance(basis, "thin_positions")}'
            f'<div class="row"><button class="btn" popovertarget="{pid}">What it is made of</button>'
            f'<a class="btn route" href="#league">League &rsaquo;</a></div></article>')
        pops.append(
            f'<div id="{pid}" popover><h4>{esc(c["position"])} &middot; depth</h4>'
            f'<dl class="kv"><dt>rostered</dt><dd>{n(count)}</dd>'
            f'<dt>priced</dt><dd>{priced}</dd>'
            f'<dt>band</dt><dd>{esc(label or "")}</dd></dl>'
            f'<p class="popnote">The band is a RATIO against this league&rsquo;s own mean, one of '
            f'four steps. Nothing here orders teams within a position, so there is no '
            f'&ldquo;worst in the league&rdquo; to report.</p>'
            f'<div class="popclose"><button class="btn" popovertarget="{pid}" '
            f'popovertargetaction="hide">Close</button></div></div>')
    return (f'<section class="col open"><h2 class="eyebrow">Open</h2>'
            f'<p class="intro">Ranked by kind, not by size; the units do not compare.</p>'
            f'{"".join(entries)}</section>{"".join(pops)}')


def checked_column(band: dict, fx: dict, basis: dict) -> str:
    """What was examined, in ladder order, as sentences. The names come from `checks_run`; the
    page does not count them."""
    bp = band["bye_profile"] or {}
    cw = fx.get("current_week")
    key_of = {"holes": "structural_holes", "byes": "bye_profile", "depth": "thin_positions"}
    shown_hidden = band["shown"] + band["hidden"]
    entries = []
    for ch in band["checks"]:
        name, state = ch["name"], ch["state"]
        if state == fc.CHECK_CLEAN:
            if name == "holes":
                s = "Nothing found. No slot the league defines is left empty by the solver."
            elif name == "byes":
                weeks = bp.get("weeks") or {}
                if cw is not None and bp.get("_ahead_only") and weeks:
                    s = f"Nothing ahead. Every measured bye week is behind week {n(cw)}."
                else:
                    s = "Nothing found. No week carries a measured bye cost."
            else:
                s = ("Nothing found. No position rates Weak against this league&rsquo;s own "
                     "rosters, and none is empty.")
            tick = '<span class="tick" aria-hidden="true">&check;</span>'
        elif state == fc.CHECK_FIRED:
            raised = [c for c in shown_hidden if c["kind"] == fc.CHECKS[[x[0] for x in fc.CHECKS].index(name)][2]]
            what = ""
            if name == "byes" and raised:
                what = f' Week {n(raised[0]["worst_week"])}, above.'
            elif name == "depth" and raised:
                what = f' {esc(join_names([c["position"] for c in raised]))}, above.'
            elif name == "holes" and raised:
                what = f' {esc(join_names([str(p) for p in raised[0].get("positions") or []]))}, above.'
            s = f"Raised.{what}"
            tick = '<span class="tick raised" aria-hidden="true">&bull;</span>'
        else:
            s = absent(ch.get("reason") or "this check did not run")
            tick = '<span class="tick absent" aria-hidden="true">&mdash;</span>'
        entries.append(f'<div class="check"><p class="line">{tick}<span class="cname">{esc(name).title()}</span></p>'
                       f'<p class="text">{s}</p>{provenance(basis, key_of.get(name, ""))}</div>')
    also = ""
    if band["hidden"]:
        heads = []
        for c in band["hidden"]:
            if c["kind"] == "thin":
                heads.append(f'{esc(c["position"])} rates {esc(c.get("label") or "thin")}')
            elif c["kind"] == "bye":
                heads.append(f'week {n(c["worst_week"])} costs {n(c.get("worst_week_loss"))}')
            elif c["kind"] == "hole":
                heads.append(f'no one can fill {esc(join_names(c.get("positions") or []))}')
        also = (f'<p class="also"><span class="cname">Also standing</span> &mdash; '
                f'{join_names(heads)}. Past the cap of {n(fc.CAP)}, not dropped.</p>')
    return (f'<section class="col checked"><h2 class="eyebrow">Checked</h2>'
            f'<p class="intro">What was examined to write this page, in the order it is ranked.</p>'
            f'{"".join(entries)}{also}</section>')


# ---------------------------------------------------------------------------------------------
# THE PAGE
# ---------------------------------------------------------------------------------------------
CSS = """
*{{box-sizing:border-box}}
html,body{{margin:0;background:var(--bg);color:var(--ink)}}
body{{font:400 1.1rem/1.5 {text};-webkit-text-size-adjust:100%;
  background:var(--bg) radial-gradient(70rem 26rem at 50% -8rem,rgba(117,80,36,.20),transparent 70%)}}
.wrap{{max-width:78rem;margin:0 auto;padding:0 24px 56px}}
b.n{{font-family:{mono};font-weight:600;font-size:inherit;line-height:1;color:var(--ink);font-variant-numeric:tabular-nums;letter-spacing:-.01em}}
.n .ge,.pull .ge{{font-weight:400;color:var(--gold-b);margin-right:.05em}}
b.lbl{{font-weight:600;color:var(--gold-b)}}
.eyebrow{{font:600 .78rem/1 {display};letter-spacing:.24em;text-transform:uppercase;color:var(--gold);margin:0}}
.prov{{font:400 .75rem/1.5 {mono};color:var(--dim);margin:.5rem 0 0}}
.absent{{color:var(--muted);cursor:help;border-bottom:1px dotted var(--muted)}}
.currency{{color:var(--muted);cursor:help;border-bottom:1px dotted var(--gold)}}
.stamp{{display:inline-block;font:600 .75rem/1 {mono};letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted);border:1px solid var(--muted);padding:3px 5px 2px;border-radius:3px;
  vertical-align:middle;cursor:help;
  background:repeating-linear-gradient(135deg,transparent 0 3px,rgba(176,162,138,.14) 3px 4px)}}
code{{font:400 .95rem {mono};color:var(--muted)}}
.pos{{font:600 .75rem/1 {mono};letter-spacing:.04em;white-space:nowrap}}
.pos i{{display:inline-block;width:.5rem;height:.5rem;border-radius:2px;margin:0 .3rem 0 0;vertical-align:1px}}
.pill{{display:inline-flex;align-items:center;height:1.35rem;padding:0 .5rem;border-radius:3px;
  font:600 .75rem/1 {mono};letter-spacing:.04em;margin-bottom:.5rem}}
.st{{text-decoration:underline dotted var(--gold);text-underline-offset:.2em}}
.nw{{white-space:nowrap}}

/* ---- MASTHEAD: a broadsheet's, centred, ruled above and below, with the dateline on the
   rule and the five sections set as a nav line beneath. ---- */
.mast{{padding-top:12px}}
.dateline{{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;
  padding:8px 0;border-top:1px solid var(--line-2);border-bottom:1px solid var(--line);
  font:400 .8rem/1.5 {mono};color:var(--muted)}}
.dateline b{{color:var(--ink);font-weight:600}}
.dateline span{{white-space:nowrap}}
.word{{text-align:center;margin:16px 0 14px}}
.crest{{display:flex;justify-content:center;margin-bottom:6px}}
.word h1{{font:600 2.4rem/1 {display};letter-spacing:.14em;text-transform:uppercase;margin:0;
  background:linear-gradient(180deg,#fff4ce 0%,#f9de99 30%,#ba9561 64%,#755024 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent;display:inline-block}}
.word small{{display:block;font:400 .8rem/1 {display};letter-spacing:.5em;text-transform:uppercase;
  color:var(--gold);margin-top:8px;padding-left:.5em}}
.sections{{display:flex;justify-content:center;gap:2px;flex-wrap:wrap;
  border-top:3px double var(--line-2);border-bottom:1px solid var(--line);padding:2px 0}}
.door{{display:inline-flex;align-items:center;min-height:44px;padding:0 14px;color:var(--muted);
  font:400 .8rem/1 {display};letter-spacing:.14em;text-transform:uppercase;text-decoration:none;
  white-space:nowrap;border-bottom:2px solid transparent}}
.door:hover,.door:focus-visible{{color:var(--gold-b);border-bottom-color:var(--gold)}}

/* ---- THE LEDE: headline, then the situation in sentences at reading scale, with the
   figure pulled out beside it at display scale. ---- */
.lede{{display:grid;grid-template-columns:1fr 19rem;gap:40px;align-items:start;
  padding:34px 0 30px;border-bottom:1px solid var(--line)}}
.lede h2{{font:400 2.75rem/1.1 {display};color:var(--gold-b);margin:10px 0 18px;letter-spacing:.01em}}
.lede .text{{font-size:1.35rem;line-height:1.5;color:var(--ink);margin:0;max-width:34em}}
.lede .text b.n{{font-size:1.2rem}}
.pull{{position:relative;padding:22px 0 0;border-top:3px double var(--line-2)}}
.pull .big{{display:block;font:600 4.5rem/1 {mono};color:var(--gold-b);letter-spacing:-.04em;
  font-variant-numeric:tabular-nums}}
.pull .unit{{display:block;margin-top:10px;font:400 .8rem/1.5 {display};letter-spacing:.16em;
  text-transform:uppercase;color:var(--muted)}}
.pull .unit .currency{{text-transform:none;letter-spacing:0;font:400 .95rem/1 {text};color:var(--muted)}}
.pull .pill{{position:absolute;top:22px;right:0}}
.pull .close{{margin-top:18px}}

/* ---- THE COLUMNS: the supporting detail set in columns under a rule, as a broadsheet
   sets its stories. The bye account is the wide one. ---- */
.cols{{display:grid;grid-template-columns:1.5fr 1fr 1fr;gap:0;padding-top:4px}}
.cols.two{{grid-template-columns:1.6fr 1fr}}
.cols.one{{grid-template-columns:1fr}}
.col{{padding:26px 28px 24px 0;border-right:1px solid var(--line);min-width:0}}
.col+.col{{padding-left:28px}}
.col:last-child{{border-right:0;padding-right:0}}
.intro{{font-size:1rem;line-height:1.5;color:var(--muted);margin:12px 0 0;font-style:italic}}
.intro b.n,.foot b.n{{font-style:normal}}
.weeks{{margin-top:18px;border-top:1px solid var(--line)}}
.wk{{padding:12px 0 12px;border-bottom:1px solid var(--line);position:relative}}
.wk.peak{{background:linear-gradient(90deg,rgba(117,80,36,.22),rgba(117,80,36,.04));
  margin:0 -12px;padding:14px 12px;border-bottom-color:var(--line-2)}}
.wk.peak::before{{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--gold-b)}}
.wkhead{{display:flex;align-items:baseline;gap:14px}}
.wklabel{{font:600 .8rem/1 {display};letter-spacing:.2em;text-transform:uppercase;color:var(--muted);min-width:5.5rem}}
.peak .wklabel{{color:var(--gold-b)}}
.wkfig b.n{{font-size:1.6rem;color:var(--ink)}}
.peak .wkfig b.n{{font-size:2.4rem;color:var(--gold-b)}}
.wkfig .absent{{font:400 1.2rem/1 {mono}}}
.wkwho{{margin:6px 0 0;font-size:1rem;line-height:1.55;color:var(--ink)}}
.wkwho b.n{{font-size:.9rem;color:var(--muted)}}
.wkwho .absent{{font-size:.95rem}}
.detail{{color:var(--muted)}}
.behind .wkfig b.n,.behind .wkwho,.behind .wkwho .detail{{color:var(--muted)}}
.behind .wklabel{{color:var(--dim)}}
.foot{{margin:16px 0 0;font-size:1.05rem;line-height:1.55;color:var(--ink)}}
.legend{{margin:10px 0 0;font-size:.85rem;line-height:1.6;color:var(--dim)}}
.legend .st{{color:var(--muted)}}
.row{{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}}

.entry{{padding:18px 0 20px;border-bottom:1px solid var(--line)}}
.entry:last-of-type{{border-bottom:0}}
.entry .line,.check .line{{margin:0;font:400 1.3rem/1.2 {text};color:var(--ink)}}
.entry .line b.n{{font-size:1.5rem}}
.entry .text,.check .text{{margin:8px 0 0;font-size:1rem;line-height:1.55;color:var(--ink)}}
.entry.hole .line b.n{{color:var(--gold-b)}}

.check{{padding:16px 0 18px;border-bottom:1px solid var(--line)}}
.check:last-of-type{{border-bottom:0}}
.check .line{{display:flex;align-items:baseline;gap:10px}}
.cname{{font:600 .8rem/1 {display};letter-spacing:.2em;text-transform:uppercase;color:var(--ink)}}
.tick{{font:600 1rem/1 {mono};color:var(--status-ok);min-width:1rem}}
.tick.raised{{color:var(--gold-b)}}
.tick.absent{{color:var(--muted);border:0}}
.also{{margin:18px 0 0;font-size:1rem;line-height:1.55;color:var(--muted)}}

.btn{{display:inline-flex;align-items:center;min-height:44px;padding:0 15px;
  border:1px solid var(--line-2);border-radius:4px;
  background:linear-gradient(180deg,rgba(117,80,36,.26),rgba(117,80,36,.05));
  color:var(--gold-b);font:400 .78rem/1 {display};letter-spacing:.14em;text-transform:uppercase;
  cursor:pointer;text-decoration:none;white-space:nowrap}}
.btn:hover,.btn:focus-visible{{border-color:var(--gold);color:var(--pure)}}
.btn.route{{background:none;border-style:dashed;color:var(--muted)}}
.btn.close{{border-color:var(--gold);min-height:48px}}

[popover]{{border:1px solid var(--line-2);border-radius:6px;padding:26px;
  background:linear-gradient(180deg,var(--surface),var(--bg));color:var(--ink);
  max-width:min(34rem,92vw);box-shadow:0 24px 64px rgba(0,0,0,.8);font:400 1rem/1.5 {text}}}
[popover]::backdrop{{background:rgba(4,3,2,.74)}}
[popover] h4{{font:600 .82rem/1 {display};letter-spacing:.2em;text-transform:uppercase;margin:0 0 16px;color:var(--gold)}}
.popnote{{color:var(--muted);font-size:.9rem;margin:14px 0 0;max-width:48ch}}
.popclose{{margin-top:18px}}
dl.kv{{display:grid;grid-template-columns:auto 1fr;gap:8px 18px;margin:0}}
dl.kv dt{{font:400 .78rem/1.5 {display};letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
dl.kv dd{{margin:0}}
dl.kv dd b.n{{font-size:1.1rem}}

.dock{{margin-top:28px;padding-top:18px;border-top:1px dashed var(--line-2);
  display:flex;align-items:center;gap:14px;flex-wrap:wrap}}
.dock .note{{font:400 .9rem/1.5 {text};color:var(--dim);font-style:italic}}
.colophon{{margin-top:22px;padding-top:12px;border-top:1px solid var(--line);
  display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;
  font:400 .75rem/1.6 {mono};color:var(--dim)}}

@media (max-width:1000px){{
  .cols,.cols.two{{grid-template-columns:1fr}}
  .col,.col+.col{{padding:22px 0;border-right:0;border-bottom:1px solid var(--line)}}
  .col:last-child{{border-bottom:0}}
  .lede{{grid-template-columns:1fr;gap:26px}}
  .pull{{display:grid;grid-template-columns:auto 1fr;gap:4px 22px;align-items:end}}
  .pull .unit{{margin-top:0;padding-bottom:10px}}
  .pull .prov{{grid-column:1/-1}}
  .pull .pill{{position:static;grid-column:1/-1;width:max-content}}
}}
@media (max-width:560px){{
  .wrap{{padding:0 16px 44px}}
  .word h1{{font-size:1.6rem;letter-spacing:.12em}}
  .lede{{padding:26px 0 24px}}
  .lede h2{{font-size:1.9rem}}
  .lede .text{{font-size:1.15rem}}
  .lede .text b.n{{font-size:1.05rem}}
  .pull .big{{font-size:3.4rem}}
  .wk.peak{{margin:0 -8px;padding:12px 8px}}
  .door{{padding:0 10px}}
}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
"""


def render_css() -> str:
    return CSS.format(text=FONT_TEXT, mono=ds.FONT_MONO, display=ds.FONT_DISPLAY)


WYRM = """<svg width="30" height="30" viewBox="0 0 34 34" aria-hidden="true">
<defs><linearGradient id="g" x1="0" y1="0" x2=".3" y2="1">
<stop offset="0" stop-color="#755024"/><stop offset=".4" stop-color="#ba9561"/>
<stop offset=".72" stop-color="#f9de99"/><stop offset="1" stop-color="#fff4ce"/>
</linearGradient></defs>
<path d="M17 2a15 15 0 1 0 10.6 25.6" fill="none" stroke="url(#g)" stroke-width="2.4" stroke-linecap="round"/>
<path d="M17 8a9 9 0 1 1-6.4 15.3" fill="none" stroke="url(#g)" stroke-width="1.9" stroke-linecap="round" opacity=".82"/>
<circle cx="21.4" cy="10.6" r="1.9" fill="url(#g)"/></svg>"""


def dateline(fx: dict, basis: dict) -> str:
    """Team, format, league, week -- each absence LABELLED and carrying its reason, stated
    here ONCE rather than on every row below (`BRIEF.md`: an absence identical on every row is
    noise)."""
    team = fx.get("team")
    team_html = (f'<b>{esc(team)}</b>' + (" " + constructed("constructed", fp.reason_of(basis.get("team", "")))
                                         if basis_kind(basis.get("team", "")) == "constructed" else "")
                 if team else "no team " + absent(fp.reason_of(basis.get("team", "")) or "no team label"))
    fmt = (fx.get("_provenance") or {}).get("format")
    fmt_html = f'<span>{esc(fmt)}</span>' if fmt else ""
    lname = fx.get("league_name")
    lname_html = (esc(lname) if lname else
                  "no league name " + absent(fp.reason_of(basis.get("league_name", "")) or "this capture carries no league name"))
    cw = fx.get("current_week")
    if cw is not None:
        wk = f'week <b>{esc(cw)}</b>' + (" " + constructed("constructed", fp.reason_of(basis.get("current_week", "")))
                                        if basis_kind(basis.get("current_week", "")) == "constructed" else "")
    else:
        wk = "no week on file " + absent(fp.reason_of(basis.get("current_week", "")) or "no season position was read")
    return (f'<div class="dateline"><span>{team_html}</span>{fmt_html}'
            f'<span>{lname_html}</span><span>{wk}</span></div>')


def build(fx: dict) -> str:
    _assert_marks_visible()
    _assert_text_legible()
    _assert_type_floor()
    band = fc.compose(fx)
    basis = (fx.get("_provenance") or {}).get("basis") or {}
    headline, text = lede(band, fx, basis)
    cols = [c for c in (bye_column(band, fx, basis), open_column(band, fx, basis),
                        checked_column(band, fx, basis)) if c]
    ncols = {1: "one", 2: "two"}.get(len(cols), "")
    doors = "".join(f'<a class="door" href="#{esc(r.lower().replace(" ", "-"))}">{esc(r)}</a>' for r in ROOMS)
    prov = fx.get("_provenance") or {}
    colophon_bits = [esc(x) for x in (prov.get("format"), prov.get("strategy"),
                                      f'seat {prov.get("seat")}' if prov.get("seat") is not None else None,
                                      f'{prov.get("rounds")} rounds' if prov.get("rounds") else None) if x]
    pool = prov.get("universe_rows")
    pool_html = (f'{n(pool)} players in the pool' if pool else "")
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gold Wyrm Dynasty &mdash; the dispatch</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=JetBrains+Mono:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap">
<style>
{ds.root_css_block()}
{ds.position_pill_css_block()}
{render_css()}
</style>
</head><body>
<div class="wrap">
  <header class="mast">
    {dateline(fx, basis)}
    <div class="word"><div class="crest">{WYRM}</div><h1>Gold Wyrm</h1><small>Dynasty</small></div>
    <nav class="sections" aria-label="Rooms">{doors}</nav>
  </header>

  <section class="lede">
    <div>
      <p class="eyebrow">The three-second answer</p>
      <h2>{headline}</h2>
      <p class="text">{text}</p>
    </div>
    {pulled_figure(band, fx, basis)}
  </section>

  <div class="cols {ncols}">{"".join(cols)}</div>

  <div class="dock">
    <a class="btn route" href="#prytaneum">{esc(DOCK)}</a>
    <span class="note">A dock rendered under every room, not a sixth room.</span>
  </div>
  <footer class="colophon"><span>{" &middot; ".join(colophon_bits)}</span><span>{pool_html}</span></footer>
</div>
</body></html>
"""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    jobs = [(pathlib.Path(argv[0]), pathlib.Path(argv[1]))] if len(argv) >= 2 else list(FIXTURES)
    for fix, out in jobs:
        out.write_text(build(json.loads(fix.read_text())))
        print(f"{out.relative_to(ROOT)}  {len(out.read_text()):,} bytes  from {fix.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
