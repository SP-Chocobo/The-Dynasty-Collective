#!/usr/bin/env python3
"""`standing` -- what if nothing scrolls?

THE QUESTION. The round-5 base runs 1283px tall on a 900px desktop and 2746px on a 664px phone.
This builder explores the opposite: the whole answer stands on ONE viewport at 1280x900 AND at
390x664, and every further layer is reached through a popover. The product's own test is that a
person opens it between two other things and knows in three seconds whether they can close it
again -- so "no scroll" is used here as the constraint that forces the hierarchy honest. If a
thing does not fit on the front, the question asked is not "how do I shrink it" but "did it belong
on the front at all", and the owner's ruling already answered that for most of it: the front is
the claim band, what was checked, and one freshness stamp. Record is off the page. Everything else
is depth, and depth lives behind a button.

WHAT MOVED, AND WHERE. The base's bye LEDGER -- the panel the owner singled out -- is the first
casualty of the constraint and the clearest case for it: eighteen rows of weeks and names is the
second layer of ONE claim ("Week 6 costs 95"), and the base already drew it twice, once as a panel
and once in a popover. It now lives only in the popover, unchanged in content. The "Cleared" panel
became a three-row ledger inside the hero: what was checked is a FRONT item by ruling, and three
rows is what it is. Each row has a popover with its basis. The freshness stamp, which the base's
docstring names as the third front item and the base then never rendered, is on the front here.

THE LEAD CLAIM IS THE HERO, AT DISPLAY SCALE. The base's statbox repeated the lead claim's figure
beside the headline; this page gives that figure to the lead tile itself, at 6.6rem, and the rest
of the band at 3.4rem. Ladder order becomes type scale: the rung that outranks is the one you read
first. In the quiet state there is no claim, so the three checks ARE the band -- each as a tile
with a real figure and a popover -- because the quiet state is the primary design and three small
lines is what the first pass was rejected for.

THE HARD LAW HOLDS: every figure is read from the fixture or is a count of fixture rows (a filter,
not a computation). The one place this file reaches for a value the base did not is the capture
date in `_provenance.players_db`, and it is rendered as a DATE, not as an age or a grade, because
`recency_grade` needs today's clock and a built file has none.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

import design_system as ds
import front_claims as fc
import front_page as fp

#: (output page, fixture it is rendered from). Two states, one builder, one CSS -- the quiet
#: state is the primary design and is built from a REAL fixture, not from the loud one with the
#: claims deleted.
PAGES = (
    ("standing.html", ROOT / "ui_explore" / "front_fixture.json"),
    ("standing_quiet.html", ROOT / "ui_explore" / "quiet_fixture.json"),
)

# ---------------------------------------------------------------------------------------------
# BUILD-TIME GATES. Copied in pattern from the base: a check that runs at build and raises is
# cheaper than a fifth attempt to see a bar by eye.
# ---------------------------------------------------------------------------------------------
#: The severity ramp runs dark-to-light because a LOW value drawn as a DARK gold cannot clear
#: 3:1 on a near-black ground (`line` 1.27:1, `line-2` 1.73:1 -- exactly what round 4's three
#: failures measured).
SEVERITY = (("recede", "dim"), ("mid", "gold"), ("hot", "gold-b"))
NON_TEXT_FLOOR = 3.0
BODY_TEXT_FLOOR = 4.5
#: Every non-text MARK this page draws, by token, and the grounds it is drawn on. Rails on the
#: tiles, the state glyphs in the checks ledger, the bars in the bye popover. The position-pill
#: rails are checked separately below because they are not TOKENS entries.
MARKS = (
    ("tile rail / fired glyph", "gold-b"), ("bye rail / mid bar", "gold"),
    ("clean glyph", "status-ok"), ("absent glyph", "muted"), ("recede bar", "dim"),
)
GROUNDS = ("bg", "surface", "surface-2")
#: Tokens text is SET IN, held to the body-text floor on every ground they sit on.
TEXT_TOKENS = ("ink", "muted", "gold", "gold-b", "pure", "status-ok")
#: The hero headline's gradient. The logo's darkest stop `#755024` measures 2.76:1 on `bg` and
#: is therefore NOT in it -- the wordmark keeps the full logo gradient as brand chrome, but a
#: 2.75rem headline is information and is held to the large-text floor stop by stop.
HEADLINE_STOPS = ("#ba9561", "#f9de99", "#fff4ce")


def _assert_ramp_is_visible():
    """A bar nobody can see is not a quiet bar, it is a missing one. Checked on every ground the
    popover's gradient passes through, not only `bg`."""
    bad = [(name, token, ground, round(ds.contrast_ratio(token, ground), 2))
           for name, token in SEVERITY for ground in GROUNDS
           if ds.contrast_ratio(token, ground) < NON_TEXT_FLOOR]
    if bad:
        raise SystemExit("severity ramp below the %.1f:1 non-text floor: %s" % (NON_TEXT_FLOOR, bad))


def _assert_marks_visible():
    """Every rail and glyph >= 3:1 against every ground it can sit on, including the ten position
    colours used as tile rails."""
    bad = [(name, token, ground, round(ds.contrast_ratio(token, ground), 2))
           for name, token in MARKS for ground in GROUNDS
           if ds.contrast_ratio(token, ground) < NON_TEXT_FLOOR]
    bad += [("pill rail", pos, ground, round(ds._contrast_hex(hex_, ds.TOKENS[ground]), 2))
            for pos, hex_ in ds.POSITION_PILL_TOKENS.items() for ground in GROUNDS
            if ds._contrast_hex(hex_, ds.TOKENS[ground]) < NON_TEXT_FLOOR]
    if bad:
        raise SystemExit("non-text marks below the %.1f:1 floor: %s" % (NON_TEXT_FLOOR, bad))


def _assert_text_legible():
    """Body-text tokens >= 4.5:1 on every ground; headline gradient stops >= 3:1 (large text)."""
    bad = [(token, ground, round(ds.contrast_ratio(token, ground), 2))
           for token in TEXT_TOKENS for ground in GROUNDS
           if ds.contrast_ratio(token, ground) < BODY_TEXT_FLOOR]
    bad += [("headline stop", stop, ground, round(ds._contrast_hex(stop, ds.TOKENS[ground]), 2))
            for stop in HEADLINE_STOPS for ground in GROUNDS
            if ds._contrast_hex(stop, ds.TOKENS[ground]) < NON_TEXT_FLOOR]
    if bad:
        raise SystemExit("text below its contrast floor: %s" % bad)


TYPE_FLOOR_REM = 0.75          # 12px at a 16px root


def _assert_type_floor():
    """No declared size under 12px, and no `em` font-size anywhere, so the floor is checkable
    with a regex rather than a browser. The base failed this twice before its first render; the
    instructive failure was a `.5em` inside a wordmark that computed to 9.12px on a phone."""
    css = render_css("1fr")
    under = sorted({float(m.group(1)) for m in re.finditer(r"font(?:-size)?:[^;}]*?([\d.]+)rem", css)
                    if float(m.group(1)) < TYPE_FLOOR_REM})
    if under:
        raise SystemExit(f"declared font sizes below the {TYPE_FLOOR_REM}rem floor: {under}")
    ems = [m.group(0) for m in re.finditer(r"font(?:-size)?:[^;}]*?[\d.]+em\b(?!\w)", css)
           if "rem" not in m.group(0).split(":")[-1]]
    if ems:
        raise SystemExit(f"small type must be declared in rem, not em: {ems}")


def render_css(cols: str) -> str:
    """ONE place that fills the CSS template, so the type-floor check reads exactly the
    stylesheet the page ships -- a check over a differently-formatted copy checks nothing."""
    return CSS.format(sans=ds.FONT_SANS, mono=ds.FONT_MONO, display=ds.FONT_DISPLAY, cols=cols,
                      stop0=HEADLINE_STOPS[0], stop1=HEADLINE_STOPS[1], stop2=HEADLINE_STOPS[2])


ROOMS = ("Matchup", "Roster Maintenance", "Draft Room", "League", "Import Audit")
DOCK = "The Prytaneum"


def esc(value) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def slug(text: str) -> str:
    return esc(text.lower().replace(" ", "-"))


def absent(reason: str) -> str:
    """The em dash carrying its reason. Never 0, never blank, never a reassuring default."""
    return f'<span class="absent" tabindex="0" title="{esc(reason)}">&mdash;</span>'


def constructed(reason: str, label: str = "constructed") -> str:
    """The third state of the grammar: a value built for this seat, not read from a league."""
    return f'<span class="constructed" tabindex="0" title="{esc(reason)}">{esc(label)}</span>'


#: `#341`: the bye figure is dynasty trade value, not this league's points. The ruling is that
#: grading belongs in league points; that conversion is unbuilt, so the page says what it is.
CURRENCY_TRADE_VALUE = (
    "dynasty trade value, not this league's points. `bye_collision` prices whatever its caller "
    "supplies and this page supplies Draft Sharks Dynasty Rankings value, selected by a "
    "three-field format hint -- so a league's own bonuses never reach it. The ruling is that "
    "grading belongs in league points; that conversion is not built yet")


def currency_stamp(text: str) -> str:
    return (f'<span class="currency" tabindex="0" title="{esc(CURRENCY_TRADE_VALUE)}">'
            f'{esc(text)}</span>')


def pill(position: str) -> str:
    bg, fg = ds.position_pill_color(position)
    return f'<span class="pill" style="background:{bg};color:{fg}">{esc(position)}</span>'


def chip(player: dict) -> str:
    """One rostered player: a dot in his position colour, his name, his value in mono. The value
    is the fixture's; `--` here means the merger priced him at nothing it could render."""
    _, fg = ds.position_pill_color(player.get("position") or "")
    val = ds.figure(player.get("value"))
    return (f'<span class="chip"><i style="background:{fg}"></i>{esc(player.get("name"))}'
            f'<s>{esc(val) if val is not None else "&mdash;"}</s></span>')


def basis_note(basis: dict, key: str) -> str:
    """The provenance line under each figure, in mono: `measured - what measured it`. Absent and
    constructed stamps render through the same grammar."""
    raw = (basis or {}).get(key) or ""
    kind = fp.stamp_kind(raw) if hasattr(fp, "stamp_kind") else (
        "absent" if raw.startswith("ABSENT") else
        "constructed" if raw.startswith("CONSTRUCTED") else "measured")
    body = raw.split("--", 1)[-1].strip() if "--" in raw else raw
    if not raw:
        return f'<span class="basis">{absent("no basis recorded for this quantity")}</span>'
    if kind == "absent":
        return f'<span class="basis">{absent(body or "not measured")}</span>'
    short = body if len(body) <= 64 else body[:61].rstrip() + "..."
    return f'<span class="basis" title="{esc(body)}">{esc(kind)} &middot; {esc(short)}</span>'


# ---------------------------------------------------------------------------------------------
# CLAIM TILES
# ---------------------------------------------------------------------------------------------
def claim_parts(c: dict, fx: dict) -> dict:
    """`{eyebrow, figure, unit, headline, body, who, rail, key}` for one claim.

    The FIGURE is the hero. Every figure is mono; Cinzel never carries a numeral. `who` is a
    FILTER on `roster[].bye` -- arranging the fixture's own rows, not computing anything.
    """
    kind = c["kind"]
    if kind == "hole":
        positions = c.get("positions") or []
        return {"eyebrow": "No legal lineup", "figure": str(len(positions)),
                "unit": "slot" + ("s" if len(positions) != 1 else ""),
                "headline": esc(", ".join(positions)) or "&mdash;",
                "body": "No rostered player can fill these. No amount of value fixes it.",
                "body_s": "No rostered player can fill these.",
                "who": "", "rail": "var(--gold-b)", "key": "structural_holes", "pos": None}
    if kind == "bye":
        loss = ds.figure(c.get("worst_week_loss"))
        floor = '<span class="floor" title="a floor: part of this roster could not be priced">&ge;</span>' if c.get("partial") else ""
        out = c.get("starters_out")
        weeks = (fx.get("bye_profile") or {}).get("weeks") or {}
        # MAGNITUDE AND SCOPE, NOT A SUPERLATIVE (VOICE.md rule 7, corrected). And the scope is
        # only "still ahead" when a current week established it; without one the same number is a
        # season-shape fact and the hero says so.
        scope = (f"the largest of the {len(weeks)} weeks still ahead" if c.get("ahead_only")
                 else f"the largest of {len(weeks)} measured weeks")
        body = scope[0].upper() + scope[1:] + "."
        body_s = (f"Largest of {len(weeks)} weeks ahead." if c.get("ahead_only")
                  else f"Largest of {len(weeks)} measured weeks.")
        if out:
            body += f' <b>{esc(out)}</b> starter{"s" if out != 1 else ""} out that week.'
            body_s += f' <b>{esc(out)}</b> starter{"s" if out != 1 else ""} out.'
        away = [r for r in (fx.get("roster") or []) if str(r.get("bye")) == str(c["worst_week"])]
        who = ('<div class="who"><span class="wl">away</span>' + "".join(chip(r) for r in away)
               + '</div>') if away else ""
        return {"eyebrow": "Bye damage", "figure": f"{floor}{esc(loss) if loss else '?'}",
                "unit": currency_stamp("trade value"),
                "headline": f'Week <b>{esc(c["worst_week"])}</b>', "body": body, "body_s": body_s,
                "who": who, "rail": "var(--gold)", "key": "bye_profile", "pos": None}
    if kind == "thin":
        count, covered = c.get("count") or 0, c.get("valued_count")
        band = c.get("label")
        # THE LABEL, NEVER A RANK (`#336b`): a ratio band against the league MEAN.
        rated = (f"Depth here rates <b>{esc(band)}</b> against this league's own rosters."
                 if band else "")
        scope = (f" Only <b>{esc(covered)}</b> of {esc(count)} could be priced, so that comparison "
                 f"is a floor." if c.get("priced_floor") else "")
        _, fg = ds.position_pill_color(c.get("position") or "")
        # WHO IS IN THE ROOM: a filter on `roster[].position`. The same chips the popover draws,
        # because a thin room's bodies are a glance-level fact and the position colour is what
        # keeps a tall tile from reading as an empty div.
        room = [r for r in (fx.get("roster") or []) if r.get("position") == c.get("position")]
        who = ('<div class="who"><span class="wl">in the room</span>' + "".join(chip(r) for r in room)
               + '</div>') if room else ""
        body_s = (f"Rates <b>{esc(band)}</b> against this league." if band else "") + (
            f" <b>{esc(covered)}</b> of {esc(count)} priced &mdash; a floor." if c.get("priced_floor") else "")
        return {"eyebrow": "Thin room", "figure": esc(count), "unit": "rostered",
                "headline": esc(c["position"]), "body": (rated + scope).strip(), "body_s": body_s.strip(),
                "who": who, "rail": fg, "key": "thin_positions", "pos": c.get("position")}
    return {"eyebrow": esc(kind), "figure": "", "unit": "", "headline": esc(kind), "body": "",
            "body_s": "", "who": "", "rail": "var(--line-2)", "key": "", "pos": None}


def claim_headline(c: dict, fx: dict) -> str:
    parts = claim_parts(c, fx)
    return f'{parts["eyebrow"]}: {re.sub("<[^>]+>", "", parts["headline"])}'


def bye_ledger(fx: dict) -> str:
    """The week ledger -- the base's densest panel, now the bye claim's SECOND layer. Content
    unchanged: weeks, value lost, a bar on the severity ramp, who is away (a filter). Weeks behind
    the current week are marked so, when a current week is known."""
    bp = fx.get("bye_profile") or {}
    weeks = bp.get("weeks") or {}
    roster = fx.get("roster") or []
    cw = fx.get("current_week")
    if not weeks:
        return f'<p class="popnote">{absent("no bye profile was measured for this roster")}</p>'
    losses = {w: (v.get("value_lost") if isinstance(v, dict) else v) for w, v in weeks.items()}
    numeric = [v for v in losses.values() if isinstance(v, (int, float))]
    peak = max(numeric) if numeric else 0
    worst = max(losses, key=lambda w: losses[w] if isinstance(losses[w], (int, float)) else -1)
    rows = []
    for wk in sorted(weeks, key=lambda w: int(w)):
        lost = losses[wk]
        away = [r for r in roster if str(r.get("bye")) == str(wk)]
        who = "".join(chip(r) for r in away) or f'<span class="dimnote">{absent("no rostered player is away this week")}</span>'
        if not isinstance(lost, (int, float)):
            cell = f'<td class="n">{absent("this week carries no measured loss")}</td><td></td>'
        else:
            share = (lost / peak) if peak else 0
            tone = (SEVERITY[2][0] if share >= .75 else SEVERITY[1][0] if share >= .35
                    else SEVERITY[0][0])
            cell = (f'<td class="n">{esc(ds.figure(lost))}</td>'
                    f'<td class="barcell"><span class="bar {tone}" style="width:{max(3, round(share * 100))}%"></span></td>')
        behind = cw is not None and int(wk) < int(cw)
        cls = "behind" if behind else ("peak" if wk == worst else "")
        tag = ' <span class="tag">behind</span>' if behind else ""
        rows.append(f'<tr class="{cls}"><th>Wk {esc(wk)}{tag}</th>{cell}<td><div class="who">{who}</div></td></tr>')
    total = ds.figure(bp.get("total_loss"))
    conc = bp.get("concentration")
    unknown = bp.get("unknown_byes")
    foot = (f'<div class="kvrow"><span>season <b>{esc(total) if total else absent("no season total was measured")}</b></span>'
            f'<span>worst week <b>{esc(f"{conc:.0%}") if conc is not None else absent("a roster with nothing to lose has no shape, so this is None rather than 0%")}</b> of it</span>'
            f'<span>unknown byes <b>{esc(unknown) if unknown is not None else absent("not counted")}</b></span></div>')
    return (f'<p class="popnote top">Every week with a measured bye cost, in {currency_stamp("trade value")}. '
            f'Each week is its own solve of the lineup with that week&rsquo;s byes removed &mdash; '
            f'{len(weeks)} separate results, not one number spread out.</p>'
            f'<table class="weeks"><thead><tr><th>Week</th><th class="n">Lost</th><th></th><th>Away</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>{foot}')


def expansion(c: dict, fx: dict) -> str:
    """The popover for one claim, or "" where the engine computes no second layer. What expands
    must be something the engine computes SEPARATELY -- otherwise the detail is fabricated."""
    kind = c["kind"]
    if kind == "bye":
        return bye_ledger(fx)
    if kind == "thin":
        count, covered = c.get("count") or 0, c.get("valued_count")
        room = [r for r in (fx.get("roster") or []) if r.get("position") == c.get("position")]
        return (f'<dl class="kv"><dt>rostered</dt><dd class="n">{esc(count)}</dd>'
                f'<dt>priced</dt><dd class="n">{esc(covered) if covered is not None else absent("the merger priced none of this room")}</dd>'
                f'<dt>band</dt><dd>{esc(c.get("label") or "")}</dd></dl>'
                + (f'<div class="who pad">{"".join(chip(r) for r in room)}</div>' if room else "")
                + '<p class="popnote">The band is a RATIO against this league&rsquo;s own mean, not a '
                  'rank. Nothing here orders teams within a position, so there is no &ldquo;worst in '
                  'the league&rdquo; to report.</p>')
    if kind == "hole":
        return ('<div class="slots">' + "".join(pill(p) for p in (c.get("positions") or [])) + '</div>'
                '<p class="popnote">A hole is a slot the solver leaves EMPTY, not a position missing '
                'from a filter. No amount of value fixes it.</p>')
    return ""


# ---------------------------------------------------------------------------------------------
# THE QUIET BAND: the three checks as tiles, each with a real figure and a real second layer
# ---------------------------------------------------------------------------------------------
def check_tile_parts(check: dict, fx: dict, basis: dict) -> dict:
    """A check that found nothing, said with a FIGURE rather than a tick. Every figure is a
    field or a count of fixture rows. `absent` checks render the dash with its reason."""
    name = check["name"]
    key = {"holes": "structural_holes", "byes": "bye_profile", "depth": "thin_positions"}[name]
    if check["state"] == fc.CHECK_ABSENT:
        return {"eyebrow": f"{name.title()} &middot; not examined", "figure": absent(check["reason"]),
                "unit": "", "headline": "Not examined", "body": esc(check["reason"]),
                "body_s": esc(check["reason"]), "key": key, "rail": "var(--muted)", "pop": ""}
    if name == "holes":
        slots = (fx.get("league") or {}).get("starting_slots")
        shape = (fx.get("league") or {}).get("roster_positions") or []
        pop = ("".join(pill(p) if p != "BN" else '<span class="pill bn">BN</span>' for p in shape)
               if shape else absent("no roster shape in this capture"))
        return {"eyebrow": "Holes &middot; clean",
                "figure": esc(slots) if slots is not None else absent("no starting-slot count in this capture"),
                "unit": "starting slots", "headline": "Every slot has a body",
                "body": "The solver left no starting slot empty.", "body_s": "No starting slot left empty.",
                "key": key, "rail": "var(--status-ok)",
                "pop": f'<div class="slots">{pop}</div><p class="popnote">The league&rsquo;s slot shape, '
                       f'as `slots_from_roster_positions` read it. A hole would be one of these the solver '
                       f'could not fill from this roster; there is none.</p>'}
    if name == "byes":
        weeks = ((fx.get("bye_profile") or {}).get("weeks") or {})
        cw = fx.get("current_week")
        if not weeks:
            return {"eyebrow": "Byes &middot; clean", "figure": absent("no week carries a measured bye cost"),
                    "unit": "", "headline": "No measured bye cost", "body": "", "body_s": "", "key": key,
                    "rail": "var(--status-ok)", "pop": bye_ledger(fx)}
        headline = (f'All behind week <b>{esc(cw)}</b>' if cw is not None else "No week ahead carries a cost")
        return {"eyebrow": "Byes &middot; clean", "figure": str(len(weeks)), "unit": "bye weeks",
                "headline": headline,
                "body": "Each was measured as its own solve of the lineup; no week at or after now carries a cost.",
                "body_s": "No week at or after now carries a cost.",
                "key": key, "rail": "var(--status-ok)", "pop": bye_ledger(fx)}
    # depth
    roster = fx.get("roster") or []
    by_pos: dict[str, list] = {}
    for r in roster:
        by_pos.setdefault(r.get("position") or "", []).append(r)
    groups = "".join(f'<div class="room"><div class="rh">{pill(p)}<span class="n">{len(rs)}</span></div>'
                     f'<div class="who">{"".join(chip(r) for r in rs)}</div></div>'
                     for p, rs in sorted(by_pos.items(), key=lambda kv: (-len(kv[1]), kv[0])))
    return {"eyebrow": "Depth &middot; clean", "figure": str(len(roster)), "unit": "rostered",
            "headline": "No room rates Weak",
            "body": "Every position&rsquo;s depth label came back Strong or Average against this league&rsquo;s own rosters.",
            "body_s": "Every room rates Strong or Average here.",
            "key": key, "rail": "var(--status-ok)",
            "pop": f'<div class="rooms">{groups}</div><p class="popnote">The roster by room, with each '
                   f'man&rsquo;s priced value. This capture carries only the rooms that fell to Weak or '
                   f'None, and there are none; the full label table is not in it, so none is drawn.</p>'}


# ---------------------------------------------------------------------------------------------
# THE FRESHNESS STAMP -- a date, deliberately, not a grade
# ---------------------------------------------------------------------------------------------
def capture_stamp(fx: dict) -> dict:
    """`{date, source, pool, captured, season}` read out of `_provenance.players_db`, or Nones.

    The fixture carries that field as a truncated repr string, so the read is a regex, and a read
    that fails renders as an absence with its reason rather than as today. The page prints the
    DATE: `recency_grade` grades an AGE in days, an age needs today's clock, and a built file has
    none -- so a grade here would be a quantity this builder invented.
    """
    raw = str((fx.get("_provenance") or {}).get("players_db") or "")
    pick = lambda k: (re.search(rf"'{k}':\s*'?([^',}}]+)'?", raw) or [None, None])[1]
    date = pick("captured_at")
    return {"date": date[:10] if date else None, "source": pick("source"),
            "pool": pick("players_in_pool"), "captured": pick("players_in_capture"),
            "season": pick("season")}


# ---------------------------------------------------------------------------------------------
# THE PAGE
# ---------------------------------------------------------------------------------------------
CSS = """
*{{box-sizing:border-box}}
html{{height:100%}}
html,body{{margin:0;background:var(--bg);color:var(--ink)}}
body{{font:400 .95rem/1.5 {sans};-webkit-text-size-adjust:100%;min-height:100vh;min-height:100dvh;
  display:flex;flex-direction:column}}
.stage{{flex:1 1 auto;width:100%;max-width:92rem;margin:0 auto;padding:0 24px 16px;
  display:grid;grid-template-columns:minmax(0,1fr);grid-template-rows:auto auto 1fr auto;gap:18px}}
.stage>*{{min-width:0}}

/* ---- TOP BAR: crest, the five rooms, who this is about. One row, 64px. ---- */
.top{{display:flex;align-items:center;gap:22px;min-height:64px;position:relative}}
.top::after{{content:"";position:absolute;left:0;right:0;bottom:0;height:1px;
  background:linear-gradient(90deg,rgba(117,80,36,.42),rgba(117,80,36,.06))}}
.crest{{display:flex;align-items:center;gap:12px;flex:0 0 auto}}
.word{{font:600 1.3rem/1 {display};letter-spacing:.11em;text-transform:uppercase;margin:0;
  background:linear-gradient(176deg,#755024 0%,#ba9561 38%,#f9de99 68%,#fff4ce 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent}}
.word b{{display:block;font-size:.76rem;letter-spacing:.42em;font-weight:400;margin-top:5px}}
.doors{{display:flex;gap:2px;flex:1 1 auto;flex-wrap:nowrap}}
.door{{display:inline-flex;align-items:center;min-height:44px;padding:0 13px;border-radius:4px;
  color:var(--muted);font:400 .8rem/1 {display};letter-spacing:.1em;text-decoration:none;
  border:1px solid transparent;white-space:nowrap}}
.door:hover,.door:focus-visible{{color:var(--gold-b);border-color:var(--line-2);
  background:linear-gradient(180deg,rgba(117,80,36,.22),rgba(117,80,36,.04))}}
.btn.roomsbtn{{display:none}}
.hh{{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}}
.whoami{{display:flex;align-items:center;gap:12px;min-height:34px;padding:0 12px;
  border:1px solid var(--line-2);border-radius:4px;background:var(--surface-2);font-size:.8rem;
  color:var(--muted);flex:0 1 auto;flex-wrap:wrap}}
.whoami b{{color:var(--ink);font-weight:600;font-family:{mono}}}

/* ---- THE HERO: the three-second answer as a statement, and beside it the ledger of what
   was checked. Gradient surface, hatch, fading gold hairline. ---- */
.hero{{display:grid;grid-template-columns:1fr 21rem;gap:30px;align-items:stretch;
  padding:22px 30px 22px;border:1px solid var(--line-2);border-radius:6px;position:relative;
  overflow:hidden;background:linear-gradient(180deg,var(--surface),var(--surface-2))}}
.hero::before{{content:"";position:absolute;inset:0 auto 0 0;width:260px;pointer-events:none;
  background:repeating-linear-gradient(135deg,transparent 0 4px,rgba(176,162,138,.07) 4px 5px);
  mask-image:linear-gradient(90deg,#000,transparent);-webkit-mask-image:linear-gradient(90deg,#000,transparent)}}
.hero>div{{position:relative}}
.eyebrow{{font:600 .78rem/1 {display};letter-spacing:.24em;text-transform:uppercase;
  color:var(--gold);margin:0}}
.hero h1{{font:400 2.75rem/1.05 {display};margin:10px 0 12px;letter-spacing:.005em;
  background:linear-gradient(176deg,{stop0} 0%,{stop1} 60%,{stop2} 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent}}
.hero p.lede{{margin:0;color:var(--muted);max-width:64ch;font-size:1.02rem}}
.hero p.lede b{{color:var(--ink);font-family:{mono};font-weight:600;font-size:.95rem}}
.hero p.lede.short{{display:none}}
.tile p.body.short{{display:none}}
.res-s{{display:none}}
.checks{{border-left:1px solid var(--line-2);padding-left:28px;display:flex;flex-direction:column}}
.checks ul{{list-style:none;margin:12px 0 0;padding:0;display:grid;gap:9px}}
.checks li{{display:grid;grid-template-columns:12px auto 1fr;gap:12px;align-items:center}}
.st{{width:10px;height:10px;border-radius:2px;display:block}}
.st.clean{{background:var(--status-ok)}}
.st.fired{{background:var(--gold-b);box-shadow:0 0 0 3px rgba(245,201,63,.18)}}
.st.absent{{background:none;border:2px solid var(--muted);width:10px;height:10px}}
.checks .nm{{font:400 .8rem/1 {display};letter-spacing:.14em;text-transform:uppercase;color:var(--ink)}}
.checks .res{{font-size:.84rem;color:var(--muted)}}
.checks .res b{{font-family:{mono};color:var(--gold-b);font-weight:600}}
.checks .row{{margin-top:auto;padding-top:14px}}

/* ---- THE BAND. The claims as tiles, the lead at display scale. In the quiet state the three
   checks stand here instead, each with a figure of its own. The row is 1fr of the viewport:
   the tiles stretch to the fold and the figures sit on the baseline of the stretch. ---- */
.band{{display:grid;gap:18px;grid-template-columns:{cols};min-height:0}}
.tile{{position:relative;display:flex;flex-direction:column;padding:20px 24px 20px 26px;
  border:1px solid var(--line);border-radius:6px;overflow:hidden;min-height:0;
  background:linear-gradient(180deg,var(--surface),var(--surface-2))}}
.tile::before{{content:"";position:absolute;inset:0 0 auto auto;width:55%;height:110px;pointer-events:none;
  background:repeating-linear-gradient(45deg,transparent 0 5px,rgba(176,162,138,.065) 5px 6px);
  mask-image:linear-gradient(225deg,#000,transparent 85%);-webkit-mask-image:linear-gradient(225deg,#000,transparent 85%)}}
.tile::after{{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--rail)}}
.tile>*{{position:relative}}
.th{{display:flex;justify-content:space-between;align-items:center;gap:10px}}
.pill{{display:inline-flex;align-items:center;height:22px;padding:0 9px;border-radius:3px;
  font:600 .76rem/1 {mono};letter-spacing:.04em}}
.pill.bn{{background:var(--surface-2);color:var(--muted);border:1px solid var(--line-2)}}
.hair{{height:1px;margin:12px 0 0;background:linear-gradient(90deg,rgba(117,80,36,.42),rgba(117,80,36,.04))}}
.fig{{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin:auto 0;padding:16px 0 10px}}
.fig .n{{font:600 4.2rem/.95 {mono};color:var(--gold-b);letter-spacing:-.035em;
  font-variant-numeric:tabular-nums}}
.fig .n .floor{{font-size:2rem;vertical-align:baseline;margin-right:.08em;color:var(--gold)}}
.fig .n .absent{{font-size:2.2rem}}
.fig .u{{font:400 .78rem/1.3 {display};letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}}
.lead .fig .n{{font-size:8rem;letter-spacing:-.05em}}
.quiet .fig .n{{font-size:5rem}}
.lead .fig .n .floor{{font-size:3.4rem}}
.tile h3{{font:400 1.3rem/1.25 {sans};margin:0 0 4px;color:var(--ink)}}
.tile h3 b{{font-family:{mono};font-weight:600}}
.lead h3{{font-size:1.55rem}}
.tile p.body{{margin:0;color:var(--muted);font-size:.92rem;max-width:46ch}}
.tile p.body b{{color:var(--ink);font-family:{mono};font-weight:600;font-size:.86rem}}
.who{{display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center}}
.tile .who{{margin-top:10px}}
.who .wl{{font:400 .75rem/1 {display};letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-right:2px}}
.chip{{display:inline-flex;align-items:center;gap:6px;font-size:.84rem;color:var(--ink);white-space:nowrap}}
.chip i{{width:8px;height:8px;border-radius:2px;flex:0 0 auto}}
.chip s{{font-family:{mono};color:var(--muted);text-decoration:none;font-size:.8rem}}
.basis{{display:block;margin-top:12px;font:400 .75rem/1.45 {mono};color:var(--muted)}}
.row{{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}}

.btn{{display:inline-flex;align-items:center;min-height:44px;padding:0 15px;
  border:1px solid var(--line-2);border-radius:4px;
  background:linear-gradient(180deg,rgba(117,80,36,.26),rgba(117,80,36,.05));
  color:var(--gold-b);font:400 .78rem/1 {display};letter-spacing:.14em;text-transform:uppercase;
  cursor:pointer;text-decoration:none;white-space:nowrap}}
.btn:hover,.btn:focus-visible{{border-color:var(--gold);color:var(--pure)}}
.btn.route{{background:none;border-style:dashed;color:var(--muted)}}
.btn.ghost{{background:none;color:var(--muted);border-color:var(--line)}}
.btn.more .glyph{{display:none;font:400 1.6rem/1 {sans}}}

/* ---- THE FOOT: the dock, anything the cap hid, and the one freshness stamp. ---- */
.foot{{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;
  padding-top:12px;position:relative}}
.foot::before{{content:"";position:absolute;left:0;right:0;top:0;height:1px;
  background:linear-gradient(90deg,rgba(117,80,36,.06),rgba(117,80,36,.34),rgba(117,80,36,.06))}}
.foot .left{{display:flex;align-items:center;gap:14px;flex-wrap:wrap}}
.note{{font-size:.8rem;color:var(--muted);margin:0}}
.stamp{{display:inline-flex;align-items:center;gap:12px;min-height:44px;padding:0 14px 0 16px;
  border:1px solid var(--line);border-radius:4px;background:var(--surface);cursor:pointer;color:var(--muted)}}
.stamp .k{{font:400 .75rem/1 {display};letter-spacing:.18em;text-transform:uppercase;color:var(--muted)}}
.stamp .d{{font:600 .95rem/1 {mono};color:var(--ink);font-variant-numeric:tabular-nums}}
.stamp:hover,.stamp:focus-visible{{border-color:var(--gold)}}

/* ---- the grammar of absence: four states, visually distinct ---- */
.absent{{color:var(--muted);cursor:help;border-bottom:1px dotted var(--muted)}}
.currency{{color:var(--muted);cursor:help;border-bottom:1px dotted var(--gold)}}
.constructed{{display:inline-block;font:600 .75rem/1 {mono};letter-spacing:.08em;text-transform:uppercase;
  color:var(--amber-b);border:1px solid var(--amber);border-radius:3px;padding:3px 5px;cursor:help}}
.tag{{display:inline-block;font:400 .75rem/1 {mono};color:var(--muted);border:1px solid var(--line-2);
  border-radius:3px;padding:2px 5px;margin-left:6px;text-transform:none;letter-spacing:0}}

/* ---- POPOVERS: every second layer. The page never scrolls; a popover may, inside itself. ---- */
[popover]{{border:1px solid var(--line-2);border-radius:6px;padding:26px 28px;
  background:linear-gradient(180deg,var(--surface),var(--bg));color:var(--ink);
  width:min(40rem,92vw);max-height:min(84vh,46rem);overflow:auto;box-shadow:0 24px 64px rgba(0,0,0,.8)}}
[popover]::backdrop{{background:rgba(4,3,2,.74)}}
[popover] h4{{font:600 .82rem/1 {display};letter-spacing:.22em;text-transform:uppercase;margin:0 0 16px;color:var(--gold)}}
.popnote{{color:var(--muted);font-size:.82rem;margin:14px 0 0;max-width:56ch}}
.popnote.top{{margin:0 0 14px}}
.popclose{{margin-top:18px;display:flex;gap:8px;flex-wrap:wrap}}
table.weeks{{width:100%;border-collapse:collapse;font-size:.86rem}}
.weeks thead th{{font:400 .75rem/1 {display};letter-spacing:.14em;text-transform:uppercase;text-align:left;
  color:var(--muted);padding:0 10px 8px 0;border-bottom:1px solid var(--line)}}
.weeks tbody th{{font:400 .82rem/1 {display};letter-spacing:.1em;text-transform:uppercase;text-align:left;
  color:var(--muted);padding:9px 12px 9px 0;white-space:nowrap;vertical-align:top}}
.weeks td{{padding:8px 10px 8px 0;vertical-align:top;border-bottom:1px solid var(--surface-2)}}
.weeks tbody th{{border-bottom:1px solid var(--surface-2)}}
.weeks th.n,.weeks td.n{{font-family:{mono};text-align:right;padding-right:14px;color:var(--ink);
  font-variant-numeric:tabular-nums;font-weight:600;font-size:1.02rem}}
.weeks thead th.n{{font:400 .75rem/1 {display};letter-spacing:.14em}}
.weeks tr.peak th{{color:var(--gold-b)}}
.weeks tr.peak td.n{{color:var(--gold-b);font-size:1.2rem}}
.weeks tr.behind th,.weeks tr.behind td.n{{color:var(--muted);font-weight:400}}
.weeks tr.behind .bar{{opacity:.55}}
.weeks .barcell{{width:30%}}
.bar{{display:block;height:9px;border-radius:2px;min-width:3px;margin-top:5px}}
.bar.recede{{background:var(--dim)}}
.bar.mid{{background:var(--gold)}}
.bar.hot{{background:linear-gradient(90deg,var(--gold),var(--gold-b))}}
.kvrow{{display:flex;flex-wrap:wrap;gap:22px;margin-top:14px;padding-top:12px;border-top:1px solid var(--line);
  font-size:.84rem;color:var(--muted)}}
.kvrow b{{font-family:{mono};color:var(--ink);font-weight:600}}
dl.kv{{display:grid;grid-template-columns:auto 1fr;gap:8px 18px;margin:0}}
dl.kv dt{{font:400 .78rem/1.4 {display};letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
dl.kv dd{{margin:0;color:var(--ink);font-size:.92rem}}
dl.kv dd.n{{font-family:{mono};font-variant-numeric:tabular-nums;font-size:1.05rem;font-weight:600}}
.who.pad{{margin-top:14px}}
.slots{{display:flex;flex-wrap:wrap;gap:6px}}
.rooms{{display:grid;gap:12px}}
.room .rh{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
.room .rh .n{{font:600 .95rem/1 {mono};color:var(--ink)}}
.cklist{{list-style:none;margin:0;padding:0;display:grid;gap:14px}}
.cklist li{{display:grid;grid-template-columns:12px 1fr;gap:12px;align-items:start}}
.cklist .st{{margin-top:5px}}
.cklist .nm{{font:400 .84rem/1 {display};letter-spacing:.14em;text-transform:uppercase;color:var(--ink)}}
.cklist .res{{color:var(--muted);font-size:.86rem;margin-left:10px}}
.cklist .basis{{margin-top:6px}}
.kvs{{display:grid;grid-template-columns:auto 1fr;gap:8px 18px;margin:14px 0 0;font-size:.86rem}}
.kvs dt{{font:400 .75rem/1.5 {display};letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
.kvs dd{{margin:0;font-family:{mono};color:var(--ink)}}
.roomlist{{display:grid;gap:4px}}
.roomlist .door{{min-height:48px;font-size:.9rem;color:var(--ink)}}
.dimnote{{font-size:.82rem;color:var(--muted)}}

/* ---- PHONE: 390x664. The rooms fold into a popover, the hero's ledger becomes one line, the
   tiles become rows with the figure at left. No column is narrower than its longest word. ---- */
@media (max-width:760px){{
  .stage{{padding:0 16px 10px;gap:10px}}
  .top{{min-height:52px;gap:10px;justify-content:space-between}}
  .word{{font-size:1.05rem}}
  .word b{{display:none}}
  .doors{{display:none}}
  .btn.roomsbtn{{display:inline-flex}}
  .hero{{grid-template-columns:1fr;gap:10px;padding:12px 14px 12px}}
  .hero::before{{width:160px}}
  .hh{{gap:6px 12px}}
  .hh .eyebrow{{display:none}}
  .whoami{{min-height:auto;padding:0;border:0;background:none;gap:6px 8px;font-size:.78rem}}
  .constructed{{letter-spacing:.03em;padding:2px 4px}}
  .hero h1{{font-size:1.42rem;margin:6px 0 6px}}
  .hero p.lede{{display:none}}
  .hero p.lede.short{{display:block;font-size:.88rem;line-height:1.4}}
  .hero p.lede b{{font-size:.84rem}}
  .checks{{border-left:0;padding-left:0;border-top:1px solid var(--line);padding-top:10px}}
  .checks .eyebrow{{display:none}}
  .checks ul{{margin:0;display:flex;flex-wrap:wrap;gap:6px 14px}}
  .checks li{{grid-template-columns:10px auto auto;gap:7px}}
  .checks .res{{display:none}}
  .checks .res-s{{display:inline;font-size:.78rem;color:var(--muted)}}
  .checks .res-s.clean{{display:none}}
  .checks .nm{{font-size:.75rem}}
  .checks .row{{display:none}}
  .band{{grid-template-columns:1fr;gap:10px}}
  .tile{{padding:10px 10px 10px 14px;display:grid;grid-template-columns:auto minmax(0,1fr) auto;
    grid-template-areas:"fig th row" "fig body row";column-gap:14px;row-gap:2px;align-items:center}}
  .tile::before{{height:100%;width:40%}}
  .th{{grid-area:th;justify-content:flex-start;gap:8px;align-self:end}}
  .hair{{display:none}}
  .fig{{grid-area:fig;flex-direction:column;align-items:flex-start;gap:3px;padding:0;margin:0;min-width:4.4rem}}
  .fig .n,.lead .fig .n{{font-size:2.6rem;letter-spacing:-.04em}}
  .fig .n .floor,.lead .fig .n .floor{{font-size:1.2rem}}
  .fig .n .absent{{font-size:1.8rem}}
  .fig .u{{font-size:.75rem;letter-spacing:.1em}}
  .tbody{{grid-area:body;min-width:0;align-self:start}}
  .tile h3,.lead h3{{font-size:1.05rem;margin:0 0 2px}}
  .tile p.body{{display:none}}
  .tile p.body.short{{display:block;font-size:.8rem;line-height:1.35}}
  .tile p.body b{{font-size:.78rem}}
  .tile .who{{display:none}}
  .basis{{display:none}}
  .row{{grid-area:row;margin:0;gap:6px}}
  .row .route{{display:none}}
  .btn.more{{width:44px;padding:0;justify-content:center}}
  .btn.more .lbl{{display:none}}
  .btn.more .glyph{{display:inline}}
  .foot{{padding-top:10px;gap:10px;justify-content:flex-end}}
  .foot .left{{display:none}}
  .stamp{{padding:0 10px 0 12px;gap:8px}}
  .stamp .k{{font-size:.75rem;letter-spacing:.12em}}
  .stamp .d{{font-size:.86rem}}
  [popover]{{padding:20px 18px}}
  .weeks .barcell{{display:none}}
}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
"""

WYRM = """<svg class="wyrm" width="34" height="34" viewBox="0 0 34 34" aria-hidden="true">
<defs><linearGradient id="g" x1="0" y1="0" x2=".3" y2="1">
<stop offset="0" stop-color="#755024"/><stop offset=".4" stop-color="#ba9561"/>
<stop offset=".72" stop-color="#f9de99"/><stop offset="1" stop-color="#fff4ce"/>
</linearGradient></defs>
<path d="M17 2a15 15 0 1 0 10.6 25.6" fill="none" stroke="url(#g)" stroke-width="2.4" stroke-linecap="round"/>
<path d="M17 8a9 9 0 1 1-6.4 15.3" fill="none" stroke="url(#g)" stroke-width="1.9" stroke-linecap="round" opacity=".82"/>
<circle cx="21.4" cy="10.6" r="1.9" fill="url(#g)"/>
</svg>"""


def popover(pid: str, title: str, body: str, extra: str = "") -> str:
    """One popover. `extra` is any control that should also live here -- on the phone the tile
    shows a single chevron and the route link is reachable from the layer it opens."""
    return (f'<div id="{pid}" popover><h4>{title}</h4>{body}'
            f'<div class="popclose"><button class="btn ghost" popovertarget="{pid}" '
            f'popovertargetaction="hide">Close</button>{extra}</div></div>')


def more_button(pid: str, label: str) -> str:
    """The tile's one control. Desktop reads the label; the phone shows a 44px chevron and the
    label travels as the accessible name. Two spans, toggled by CSS -- never `font-size:0`."""
    return (f'<button class="btn more" popovertarget="{pid}" aria-label="{esc(label)}">'
            f'<span class="lbl">{esc(label)}</span><span class="glyph" aria-hidden="true">&rsaquo;</span></button>')


def short_prose(claims: list, fx: dict) -> str:
    """The phone's lede: the same facts as `verdict_prose`, fewer words. The figures and the
    deadline note survive; the qualifying clauses move into the tiles below it."""
    bp = fx.get("bye_profile") or {}
    bits = []
    bye = next((c for c in claims if c["kind"] == "bye"), None)
    if bye is not None:
        total = ds.figure(bp.get("total_loss"))
        loss = ds.figure(bye.get("worst_week_loss"))
        bits.append(f'Week <b>{esc(bye["worst_week"])}</b> costs <b>{esc(loss)}</b>'
                    + (f' of <b>{esc(total)}</b>' if total else "") + f' in {currency_stamp("bye trade value")}.')
    holes = next((c for c in claims if c["kind"] == "hole"), None)
    if holes is not None:
        bits.append(f'{esc(", ".join(holes.get("positions") or []))} cannot be filled.')
    thin = [c for c in claims if c["kind"] == "thin"]
    if thin:
        bits.append(", ".join(esc(c["position"]) for c in thin)
                    + f' rate{"s" if len(thin) == 1 else ""} <b>{esc(thin[0].get("label") or "thin")}</b>.')
    if fx.get("current_week") is None:
        bits.append("No current week on file, so no deadline.")
    return " ".join(bits)


def verdict_prose(claims: list, fx: dict) -> str:
    """The hero paragraph as SENTENCES. Every figure is the engine's; thin rooms are collected
    into one clause rather than one card each."""
    bp = fx.get("bye_profile") or {}
    bits = []
    bye = next((c for c in claims if c["kind"] == "bye"), None)
    if bye is not None:
        total = ds.figure(bp.get("total_loss"))
        loss = ds.figure(bye.get("worst_week_loss"))
        against = f" of the season&rsquo;s <b>{esc(total)}</b>" if total else ""
        bits.append(f'Week <b>{esc(bye["worst_week"])}</b> costs <b>{esc(loss)}</b>{against} '
                    f'in {currency_stamp("bye trade value")}.')
    holes = next((c for c in claims if c["kind"] == "hole"), None)
    if holes is not None:
        bits.append(f'No rostered player can fill {esc(", ".join(holes.get("positions") or []))}.')
    thin = [c for c in claims if c["kind"] == "thin"]
    if thin:
        names = ", ".join(esc(c["position"]) for c in thin[:-1])
        last = esc(thin[-1]["position"])
        joined = f"{names} and {last}" if names else last
        label = thin[0].get("label") or "thin"
        verb = "rates" if len(thin) == 1 else "rate"
        floor = any(c.get("priced_floor") for c in thin)
        bits.append(f'{joined} {verb} <b>{esc(label)}</b> against this league&rsquo;s own rosters'
                    + (", one of them on a priced floor." if floor else "."))
    if fx.get("current_week") is None:
        bits.append("No current week is on file, so none of this carries a deadline.")
    return " ".join(bits)


def build(fx: dict) -> str:
    """One responsive page that stands on one screen, rendered from `front_claims.compose`."""
    _assert_ramp_is_visible()
    _assert_marks_visible()
    _assert_text_legible()
    _assert_type_floor()
    band = fc.compose(fx)
    shown, hidden = band["shown"], band["hidden"]
    summary = fc.checks_summary(band["checks"])
    basis = (fx.get("_provenance") or {}).get("basis") or {}
    pops: list[str] = []

    # ---- THE HERO --------------------------------------------------------------------------
    n = len(shown) + len(hidden)
    words = {0: "Nothing", 1: "One thing", 2: "Two things", 3: "Three things", 4: "Four things"}
    headline = ("Nothing open this week." if not n
                else f'{words.get(n, str(n) + " things")} {"is" if n == 1 else "are"} open.')
    if shown:
        lede, lede_s = verdict_prose(shown + hidden, fx), short_prose(shown + hidden, fx)
    elif summary["ran"]:
        lede = (f'<b>{esc(summary["ran"])}</b> checks ran &mdash; {esc(", ".join(summary["clean"]))} '
                f'&mdash; and each came back clean. The page keeps the ledger while you are gone.')
        lede_s = (f'<b>{esc(summary["ran"])}</b> checks ran &mdash; {esc(", ".join(summary["clean"]))} '
                  f'&mdash; each clean.')
    else:
        lede = lede_s = "Nothing here was examined, so nothing here is clean."

    # ---- WHAT WAS CHECKED: the ledger in the hero, with a popover carrying each basis --------
    key_of = {"holes": "structural_holes", "byes": "bye_profile", "depth": "thin_positions"}
    rows, ck = [], []
    for check in band["checks"]:
        st = check["state"]
        res = {fc.CHECK_CLEAN: "nothing found", fc.CHECK_FIRED: "raised &mdash; below",
               fc.CHECK_ABSENT: "not examined"}[st]
        # The phone shows the short word, not the glyph alone: a state carried by colour only
        # is a state a colour-blind reader cannot read.
        short = {fc.CHECK_CLEAN: "clean", fc.CHECK_FIRED: "raised", fc.CHECK_ABSENT: "absent"}[st]
        rows.append(f'<li><i class="st {esc(st)}"></i><span class="nm">{esc(check["name"])}</span>'
                    f'<span class="res">{res}</span><span class="res-s {esc(st)}">{short}</span></li>')
        detail = (basis_note(basis, key_of[check["name"]]) if st != fc.CHECK_ABSENT
                  else f'<span class="basis">{absent(check["reason"])}</span>')
        ck.append(f'<li><i class="st {esc(st)}"></i><div><span class="nm">{esc(check["name"])}</span>'
                  f'<span class="res">{res}</span>{detail}</div></li>')
    pops.append(popover("checks", "What was checked",
                        f'<ul class="cklist">{"".join(ck)}</ul>'
                        f'<p class="popnote">Three checks, because three is what `compose` evaluates. '
                        f'Starters and record are not checked here; record is off the front by ruling, '
                        f'as true but inert. A check that was never run says so rather than reading clean.</p>'))
    checks_html = (f'<div class="checks"><p class="eyebrow">What was checked</p><ul>{"".join(rows)}</ul>'
                   f'<div class="row"><button class="btn ghost" popovertarget="checks">Each with its basis</button></div></div>')

    # ---- THE BAND --------------------------------------------------------------------------
    tiles = []
    if shown:
        for i, c in enumerate(shown):
            p, exp, pid = claim_parts(c, fx), expansion(c, fx), f"exp{i}"
            route = f'<a class="btn route" href="#{slug(c["route"])}">{esc(c["route"])} &rsaquo;</a>'
            controls = []
            if exp:
                controls.append(more_button(pid, "What it is made of"))
                pops.append(popover(pid, p["eyebrow"], exp, route))
            controls.append(route)
            tiles.append(
                f'<article class="tile {esc(c["kind"])}{" lead" if i == 0 else ""}" style="--rail:{p["rail"]}">'
                f'<div class="th"><p class="eyebrow">{p["eyebrow"]}</p>{pill(p["pos"]) if p["pos"] else ""}</div>'
                f'<div class="hair"></div>'
                f'<div class="fig"><span class="n">{p["figure"]}</span><span class="u">{p["unit"]}</span></div>'
                f'<div class="tbody"><h3>{p["headline"]}</h3><p class="body">{p["body"]}</p><p class="body short">{p["body_s"]}</p>{p["who"]}'
                f'{basis_note(basis, p["key"])}</div><div class="row">{"".join(controls)}</div></article>')
        cols = " ".join(["1.45fr"] + ["1fr"] * (len(shown) - 1))
    else:
        # THE QUIET BAND. No claim stands, so the checks do -- each with a figure and a layer.
        for i, check in enumerate(band["checks"]):
            p, pid = check_tile_parts(check, fx, basis), f"chk{i}"
            controls = []
            if p["pop"]:
                controls.append(more_button(pid, "What was examined"))
                pops.append(popover(pid, p["eyebrow"], p["pop"]))
            tiles.append(
                f'<article class="tile quiet" style="--rail:{p["rail"]}">'
                f'<div class="th"><p class="eyebrow">{p["eyebrow"]}</p></div><div class="hair"></div>'
                f'<div class="fig"><span class="n">{p["figure"]}</span><span class="u">{p["unit"]}</span></div>'
                f'<div class="tbody"><h3>{p["headline"]}</h3><p class="body">{p["body"]}</p><p class="body short">{p["body_s"]}</p>'
                f'{basis_note(basis, p["key"])}</div><div class="row">{"".join(controls)}</div></article>')
        cols = "repeat(3,1fr)"
    hidden_html = ('<p class="note">Also standing: ' + "; ".join(claim_headline(c, fx) for c in hidden) + ".</p>"
                   if hidden else "")

    # ---- THE FOOT: dock, one freshness stamp --------------------------------------------------
    cap = capture_stamp(fx)
    if cap["date"]:
        stamp_val = f'<span class="d">{esc(cap["date"])}</span>'
    else:
        stamp_val = f'<span class="d">{absent("no capture date in this fixture&rsquo;s provenance")}</span>'
    kv = "".join(f'<dt>{k}</dt><dd>{esc(v) if v else absent("not in this capture")}</dd>' for k, v in (
        ("captured", cap["date"]), ("source", cap["source"]), ("season", cap["season"]),
        ("in capture", cap["captured"]), ("in pool", cap["pool"])))
    pops.append(popover("fresh", "Player database",
                        f'<p class="popnote top">A capture DATE, deliberately not a grade. `recency_grade` grades an '
                        f'average age in days as Fresh, Recent, Aging or Stale, and an age needs today&rsquo;s '
                        f'clock, which a built page does not have. The date is what this fixture records; the '
                        f'subtraction is yours.</p><dl class="kvs">{kv}</dl>'))
    stamp = (f'<button class="stamp" popovertarget="fresh"><span class="k">Player database captured</span>'
             f'{stamp_val}</button>')

    # ---- TOP BAR: an absence LABELLED, a constructed value STAMPED -----------------------------
    doors = "".join(f'<a class="door" href="#{slug(r)}">{esc(r)}</a>' for r in ROOMS)
    pops.append(popover("roomsp", "Rooms",
                        f'<nav class="roomlist">{doors}<a class="door" href="#prytaneum">{esc(DOCK)}</a></nav>'
                        f'<p class="popnote">Five rooms and one dock. The Prytaneum is rendered under every '
                        f'room, not as a sixth.</p>'))
    # WHO THIS IS ABOUT. An absence is LABELLED so it reads as information, and a constructed value
    # is STAMPED -- but once: two CONSTRUCTED tags in one short line is the same stamp said twice,
    # which the grammar forbids as noise. The constructed items are grouped and the one tag
    # carries both reasons.
    team, lname, week = fx.get("team"), fx.get("league_name"), fx.get("current_week")
    built, plain = [], []
    team_item = f'<b>{esc(team or "")}</b>'
    (built if str(basis.get("team", "")).startswith("CONSTRUCTED") else plain).append(
        (team_item, fp.reason_of(basis.get("team", ""))))
    if week is not None:
        (built if str(basis.get("current_week", "")).startswith("CONSTRUCTED") else plain).append(
            (f'wk <b>{esc(week)}</b>', fp.reason_of(basis.get("current_week", ""))))
    else:
        plain.append((f'no week {absent(fp.reason_of(basis.get("current_week", "")) or "no season position was read")}', ""))
    plain.append((esc(lname) if lname else
                  f'no league name {absent(fp.reason_of(basis.get("league_name", "")) or "this capture carries no league name")}', ""))
    items = [f'<span>{html}</span>' for html, _ in built]
    if built:
        items.append(constructed("; ".join(f"{re.sub('<[^>]+>', '', h)}: {r}" for h, r in built)))
    items += [f'<span>{html}</span>' for html, _ in plain]
    whoami = f'<div class="whoami">{"".join(items)}</div>'

    css = render_css(cols)
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
<div class="stage">
  <header class="top">
    <span class="crest">{WYRM}<h1 class="word">Gold Wyrm<b>Dynasty</b></h1></span>
    <nav class="doors">{doors}</nav>
    <button class="btn ghost roomsbtn" popovertarget="roomsp">Rooms</button>
  </header>

  <section class="hero">
    <div class="answer">
      <div class="hh"><p class="eyebrow">The three-second answer</p>{whoami}</div>
      <h1>{headline}</h1>
      <p class="lede">{lede}</p>
      <p class="lede short">{lede_s}</p>
    </div>
    {checks_html}
  </section>

  <section class="band">{"".join(tiles)}</section>

  <footer class="foot">
    <div class="left"><a class="btn route" href="#prytaneum">{esc(DOCK)}</a>
      <p class="note">A dock rendered under every room, not a sixth room.</p>{hidden_html}</div>
    {stamp}
  </footer>
</div>
{"".join(pops)}
</body></html>
"""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        fix, out = pathlib.Path(argv[0]), pathlib.Path(argv[1] if len(argv) > 1 else HERE / "standing.html")
        jobs = [(out, fix)]
    else:
        jobs = [(HERE / name, fix) for name, fix in PAGES]
    for out, fix in jobs:
        out.write_text(build(json.loads(fix.read_text())))
        print(f"{out}  {len(out.read_text()):,} bytes  from {fix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
