#!/usr/bin/env python3
"""Build the front page from the fixture, in the app's own tokens.

THE PALETTE IS DERIVED, NOT COPIED, and that is the main architectural difference from round 2.
Those prototypes hand-wrote their `:root` block, and `_palette.py` later measured the result: 26
of 27 shared token names carried a visibly different colour and NOT ONE was identical, including
the three page grounds a design note had claimed were shared. This file calls
`design_system.root_css_block()` -- the one place the app's hex values are spelled out, which
every other consumer already calls for the same reason -- so the front page cannot drift from the
app by construction rather than by being checked afterwards.

Numbers go through `design_system.figure()`. Python's `format` rounds half to EVEN and the
browser's `toFixed` rounds half AWAY FROM ZERO, so one figure landing on .5 renders as 16 in
Streamlit and 17 on the board; that was measured on a real value and the module exists partly to
state the rule once. A front page quoting engine figures has to use it or it becomes a third
answer.

THE BASIS DRIVES THE RENDERING. The fixture stamps every field `measured`, `CONSTRUCTED` or
`ABSENT`, and this reads those stamps rather than knowing which is which itself. A constructed
number is drawn with its marker and an absent one as an em dash with its reason, wherever it
appears -- so editing the fixture by hand cannot quietly promote a demo value into a measurement,
and a field added later arrives with its basis already honoured.

    python3 ui_explore/round3/build_front.py
"""
import html
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path.cwd()))
import design_system as ds
import front_claims as fc
import front_page as fp
import lineup_optimizer as lo

#: Re-exported from their one home (`#333`) so a reader of this file still finds them
#: here, without this file becoming a second place they are spelled.
LADDER, CAP = fc.LADDER, fc.CAP

HERE = pathlib.Path(__file__).resolve().parent
FIX = pathlib.Path("ui_explore/front_fixture.json")
OUT = HERE / "front.html"

def esc(s):
    return html.escape(str(s), quote=True)


def absent(reason):
    """#187: an em dash means NOT MEASURED, and it carries why. Never a zero standing in for one."""
    return f'<span class="absent" title="{esc(reason)}" tabindex="0">&mdash;</span>'


def stamp_kind(stamp):
    """measured / constructed / absent, from the stamp's own leading token.

    THE BASIS HAS TO DECIDE THE RENDERING, which an earlier version of this file claimed and did
    not do. It read two of five stamps and only into `title=` tooltips, while the footer asserted
    in hardcoded prose that three fields were measured -- so stamping all three CONSTRUCTED
    changed nothing on the page, and the page that claimed hand-editing could not promote a demo
    value into a measurement was itself the proof that it could. Dispatching on the token is the
    whole repair: a field added later arrives with its basis honoured because nothing here knows
    the field names."""
    t = (stamp or "").strip().upper()
    if t.startswith("CONSTRUCTED"):
        return "constructed"
    if t.startswith("ABSENT"):
        return "absent"
    return "measured"


#: Re-exported from its one home (`#334`): `app.py` renders these stamps too, so the parse rule
#: cannot live in a prototype. `build_empty` imports it from here, which still resolves.
reason_of = fp.reason_of


def num(value, digits, why):
    """A figure, or the absence marker -- never the string "None".

    ds.figure() returns None for None/NaN/inf BY DESIGN: "None in, None out -- the caller chooses
    the absence marker (#187)". Four call sites here passed that straight into esc(), which
    stringifies it, so the page painted the literal word None where a number was missing."""
    out = ds.figure(value, digits)
    return esc(out) if out is not None else absent(why)


def claim_prose(c):
    """One claim's (title, body) HTML. THE SENTENCES, not the judgment.

    Every string here was lifted verbatim from `build`'s own f-strings, which is why rebuilding
    `front.html` after `#333` reproduces the committed file's sha256 exactly -- the one check
    that makes a refactor of a certified artifact safe to make at all, and the one `#332` had to
    repair before it could be relied on.
    """
    k = c["kind"]
    if k == "hole":
        holes = c["positions"]
        # ESCAPED: position codes come from a league capture, i.e. upstream data, so an
        # unescaped one is injection and not merely a cosmetic slip.
        named = f"<b>{esc(holes[0])}</b>" if len(holes) == 1 else (
            " and ".join([", ".join(f"<b>{esc(h)}</b>" for h in holes[:-1]), f"<b>{esc(holes[-1])}</b>"]))
        title = (f"No <b>{esc(holes[0])}</b> on the roster" if len(holes) == 1
                 else f"{len(holes)} starting slots nobody you own can fill")
        return title, f"This league starts {named}. You hold none."
    if k == "bye":
        ge = "&ge;" if c["partial"] else ""
        unknown = c["unknown_byes"]
        floor = (f" These are floors: {esc(unknown)} player"
                 f"{'s' if (unknown or 0) != 1 else ''} on this roster has no known bye."
                 if c["partial"] else "")
        when = ("" if c["ahead_only"] else
                " This counts the whole season, including weeks already played &mdash; the app "
                "does not know today's week here.")
        out = c["starters_out"]
        who = (f"<b>{esc(out)}</b> of your starters "
               f"{'sits' if str(out) == '1' else 'sit'} that week. " if out is not None else "")
        share = c["concentration"]
        shape_txt = (f"{esc(ds.figure(share * 100, 0))}% of your season's bye damage lands in "
                     f"that one week" if share is not None
                     else f"its share of the season is {absent('bye damage has no shape: this roster carries none')}")
        return (f"Week <b>{esc(c['worst_week'])}</b> costs you "
                f"<b>{ge}{num(c['worst_week_loss'], 0, 'the worst week was not measured')} "
                f"{esc(ds.VALUE_UNIT_SHORT)}</b>",
                f"{who}{shape_txt}.{floor}{when}")
    # ONE WORD FOR ONE BUCKET. "Thin" is this page's name for the bucket whose members are
    # depth_ratings' WEAK and NO_PLAYERS labels.
    covered, count = c["valued_count"], c["count"]
    scope = (f" Priced depth only: {esc(covered)} of {esc(count)} could be priced, so "
             f"that comparison is a floor." if c["priced_floor"] else "")
    # SAY THE LABEL, NEVER A RANK (`#336b`). This read "bottom of this league at the position"
    # for months. `depth_label` is a ratio band against the league MEAN; no function in this tree
    # ranks teams within a position, and the sentence was false on the fixture it shipped with.
    # With no label the sentence states the count and stops, rather than reaching for a
    # comparison it cannot support.
    band = c.get("label")
    rated = (f" Depth here rates <b>{esc(band)}</b> against this league's own rosters."
             if band else "")
    return (f"Thin at <b>{esc(c['position'])}</b>",
            f"<b>{esc(count)}</b> rostered.{rated}{scope}")


def style_css():
    """The page's whole style block, so BOTH states of the front page wear one stylesheet.

    Lifted verbatim out of `build`'s own f-string for `build_empty.py` to import. The reason
    it is shared rather than copied is measured, not aesthetic: `_palette.py` compared the
    round-2 prototypes against the app and found 26 of 27 shared token names carrying a
    visibly different colour, with NOT ONE identical -- including three page grounds a design
    note had claimed were shared. Two states of one page defining `.fact` and `.claim`
    separately would drift exactly that way, and the drift would be invisible until someone
    put the two screenshots side by side.

    Verified byte-identical: rebuilding `front.html` after this lift reproduces the committed
    file's sha256 exactly, which is the only reason a refactor of a certified file is safe to
    make at all.
    """
    return f"""{ds.root_css_block()}
:root{{ --f-d:{ds.FONT_DISPLAY}; --f-s:{ds.FONT_SANS}; --f-m:{ds.FONT_MONO}; }}
*{{box-sizing:border-box}}
/* WRAP RATHER THAN CLIP OR PUSH. With no break rule a single 40-character token blew the page
   open by 2,112px at 390 wide, and `.facts{{overflow:hidden}}` threw text away with no
   scrollbar, no ellipsis and no horizontal scroll to detect it -- a silent failure that defeats
   the very check a gate would run. */
.claim h3,.claim p,.fact .k,.fact .v,.wk,.prov,.more,.door{{overflow-wrap:anywhere}}
.fact>*{{min-width:0}}
:root{{color-scheme:dark}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--f-s);line-height:1.5}}
.page{{max-width:52rem;margin:0 auto;padding:18px 16px 56px}}
.wm{{margin:0;font-family:var(--f-d);font-weight:700;letter-spacing:.12em;text-transform:uppercase;
    font-size:.95rem;color:var(--gold-b)}}
.who{{color:var(--muted);font-size:.84rem;margin:2px 0 20px}}
.who .absent,.who .made-up{{font-size:.78rem}}
h2{{font-family:var(--f-d);font-weight:700;letter-spacing:.06em;text-transform:uppercase;
   font-size:.78rem;color:var(--muted);margin:26px 0 8px}}
.claims{{display:flex;flex-direction:column;gap:8px}}
.claim{{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--line-2);
       border-radius:4px;padding:11px 13px}}
.claim h3{{margin:0 0 3px;font-size:1rem;font-weight:700}}
.claim p{{margin:0;color:var(--muted);font-size:.85rem}}
.claim b{{color:var(--ink);font-family:var(--f-m);font-weight:600}}
.claim.hole{{border-left-color:var(--crimson-b)}}
.claim.bye{{border-left-color:var(--amber-b)}}
.claim.thin{{border-left-color:var(--sky-b)}}
.claim.none{{border-left-color:var(--emerald-b)}}
/* A LINK, AT THE TAP FLOOR. This was a <span> styled gold-and-monospace with a chevron -- it
   read exactly like a link, was 18.7px tall, was not in the tab order, and did nothing when
   tapped. It is the "so do something" half of every card. */
.route{{display:inline-flex;align-items:center;min-height:44px;margin-top:2px;font-size:.78rem;
       color:var(--gold-b);font-family:var(--f-m);letter-spacing:.03em;text-decoration:none}}
.route:hover,.route:focus-visible{{text-decoration:underline}}
.more{{color:var(--muted);font-size:.78rem;margin:8px 0 0}}
.facts{{display:grid;grid-template-columns:1fr;gap:1px;background:var(--line);
       border:1px solid var(--line);border-radius:4px;overflow:hidden}}
.fact{{display:flex;justify-content:space-between;gap:12px;background:var(--surface);
      padding:8px 12px;font-size:.85rem}}
.fact .k{{color:var(--muted)}}
.fact .v{{font-family:var(--f-m);text-align:right}}
.fact .v b{{font-weight:600}}
/* --muted, NOT --dim. design_system documents dim as the one recede-into-the-page role held
   to AA-LARGE and deliberately below 4.5:1 -- measured 3.39:1 on --surface. These four roles are
   all 12-13.6px, i.e. normal text, so they need 4.5. The absence marker is the worst place to
   lose contrast: the glyph whose only job is to say "not measured" was the least legible text on
   the page. --muted measures 6.25:1 on surface. */
.absent{{color:var(--muted);cursor:help;font-family:var(--f-m)}}
.made-up{{color:var(--amber-b);font-size:.75rem;text-transform:uppercase;letter-spacing:.07em;
         cursor:help;margin-left:6px;font-family:var(--f-s)}}
.prof{{display:flex;gap:4px;flex-wrap:wrap;margin-top:8px}}
.wk{{background:var(--surface-2);border:1px solid var(--line);border-radius:3px;
    padding:3px 7px;font-family:var(--f-m);font-size:.76rem;color:var(--muted)}}
.wk em{{display:block;font-style:normal;color:var(--muted);font-size:.75rem}}
.wk.hot{{border-color:var(--amber);color:var(--amber-b)}}
/* 3x2, not auto-fit: six items in a 4-wide auto-fit grid renders 4+2 with two empty cells. */
.doors{{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}}
@media (max-width:560px){{ .doors{{grid-template-columns:repeat(2,1fr)}} }}
.door{{display:block;background:var(--surface);border:1px solid var(--line-2);border-radius:4px;
      padding:13px 12px;color:var(--ink);text-decoration:none;font-size:.88rem;min-height:44px}}
.door:hover{{border-color:var(--gold);color:var(--gold-b)}}
.prov{{margin-top:26px;color:var(--muted);font-size:.75rem;border-top:1px solid var(--line);
      padding-top:10px}}
.prov b{{color:var(--muted);font-weight:600}}
/* NOTHING BELOW 12px. The draft-room render gate asserts a 12px minimum resident font and this
   page is held to the same floor. Measured 10.56px on the first render -- `.wk em` at .66rem,
   with `.made-up` and `.prov` also under -- which is an accessibility defect rather than a
   stylistic choice, and it was invisible until the page was measured instead of looked at. */
@media (max-width:420px){{ .page{{padding:14px 16px 40px}} }}
"""


def build(fx):
    # THE JUDGMENT IS NOT HERE ANY MORE (`#333`). Which claims fire, with what values and in
    # what order, is `front_claims.compose` -- one home, reachable by production, with no HTML in
    # it. What stays here is the PROSE, deliberately: two surfaces say the same thing differently
    # and a module that shipped copy would make this page's voice a thing production had to
    # override rather than write.
    basis = (fx.get("_provenance") or {}).get("basis") or {}
    band = fc.compose(fx)
    shown, hidden = band["shown"], band["hidden"]
    # The RESOLVED profile, which the week strip below also draws. Re-deriving it here is how one
    # quantity acquires two answers.
    bp = band["bye_profile"]

    rendered = [(c["kind"], *claim_prose(c), c["route"]) for c in shown]
    cards = "".join(
        f'<article class="claim {esc(k)}"><h3>{title}</h3><p>{body}</p>'
        f'<a class="route" href="#{esc(route.lower().replace(" ", "-"))}">{esc(route)} &rsaquo;</a></article>'
        for k, title, body, route in rendered) or (
        '<article class="claim none"><h3>Nothing needs you</h3>'
        '<p>No unfillable slot, no concentrated bye week, no position thin against the '
        'league.</p></article>')

    # No design rationale in the product. The sentence explaining why the band is restrained was
    # 18 of its 23 words and 37px tall, and on the phone it was what pushed the first real fact
    # below the fold -- the page's restraint, costing the page its fold.
    more = (f'<p class="more">Also: '
            + ", ".join(esc(claim_prose(c)[0].replace("<b>", "").replace("</b>", ""))
                         for c in hidden)
            + ".</p>") if hidden else ""

    filled = len(fx.get("starters") or [])
    total = (fx.get("league") or {}).get("starting_slots")
    total_html = (f"<b>{esc(total)}</b>" if total is not None
                  else absent("this league's starting-slot count was not read"))

    def field(value_html, stamp, absent_why):
        """Draw a field ACCORDING TO ITS STAMP -- measured plain, constructed marked, absent as
        the dash with its reason. The marker is no longer hardcoded per row, so a field whose
        stamp changes changes on the page."""
        kind = stamp_kind(stamp)
        if kind == "absent":
            return absent(reason_of(stamp) or absent_why)
        if kind == "constructed":
            return (f'{value_html} <span class="made-up" tabindex="0" '
                    f'title="{esc(reason_of(stamp))}">constructed</span>')
        return value_html

    # basis.get, not basis[...]: this dict is hand-maintainable and the file invites editing it,
    # so a missing key must not be a traceback.
    week_rows = [("Lineup", field(f"<b>{filled}</b> of {total_html} starting slots filled",
                                  basis.get("starters"), "no lineup basis recorded")),
                 ("Record", field(esc(fx.get("record") or ""), basis.get("record"),
                                  "no record basis recorded"))]
    week = "".join(f'<div class="fact"><span class="k">{esc(k)}</span><span class="v">{v}</span></div>'
                   for k, v in week_rows)

    doors = "".join(f'<a class="door" href="#">{esc(d)}</a>' for d in
                    ("Matchup", "Roster Maintenance", "Draft Room", "League",
                     "Import Audit", "The Prytaneum"))

    # THE FOOTER IS DERIVED. It used to be a hardcoded sentence asserting that three fields were
    # measured, which is how a page full of hand-written demo numbers came to print the word
    # "measured" under them. Grouping the field names by their own stamp means the sentence can
    # only ever say what the stamps say.
    groups = {}
    for fname, stamp in sorted(basis.items()):
        groups.setdefault(stamp_kind(stamp), []).append(fname.replace("_", " "))
    parts = [f"{', '.join(v)} {'is' if len(v) == 1 else 'are'} <b>{k}</b>"
             for k, v in sorted(groups.items())]
    # No format slugs, no strategy enums, no "seat", no "universe rows" -- four pieces of
    # internal jargon on a consumer page, naming a battery arm the reader has no concept of.
    prov_sentence = ("; ".join(parts) + ". " if parts else "") + (
        f"{esc(fx['_provenance'].get('universe_rows'))} players in the pool.")

    # WHOSE COMMAND CENTER IS THIS. The page said "Gold Wyrm" -- the brand -- and then named a
    # battery arm in the footer. A dynasty manager is in three to six leagues at once, and the
    # design argument this page is built from specifically faults the phone draft room for being
    # unable to say which league or view you are looking at. The lede it replaces was thirteen
    # words of mission statement that told the reader nothing they could act on.
    team_html = field(esc(fx.get("team") or ""), basis.get("team"), "no team recorded")
    league_html = field(esc(fx.get("league_name") or ""), basis.get("league_name"),
                        "no league name recorded")
    identity = f"{team_html} &middot; {league_html}"

    weeks = bp.get("weeks") or {}
    # int(kv[0]) raised ValueError on any non-numeric key and took the whole page with it.
    def _wk(kv):
        k = str(kv[0])
        return (0, int(k)) if k.lstrip("-").isdigit() else (1, 0)
    ge_chip = "&ge;" if bp.get("basis") != lo.BYE_MEASURED else ""
    profile = "".join(
        f'<span class="wk{" hot" if str(w) == str(bp.get("worst_week")) else ""}">'
        f'<em>wk {esc(w)}</em>{ge_chip}{num(v, 0, "not measured")}</span>'
        for w, v in sorted(weeks.items(), key=_wk))

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Command Center</title>
<meta name="description" content="A triage surface: what needs you, why, what it costs to ignore, and what can wait.">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&display=swap">
<style>
{style_css()}</style></head>
<body><div class="page">
<h1 class="wm">Gold Wyrm</h1>
<p class="who">{identity}</p>

<h2>Needs you</h2>
<div class="claims">{cards}</div>
{more}

<h2>This week</h2>
<div class="facts">{week}</div>
<div class="prof">{profile}</div>

<h2>Everything else</h2>
<div class="doors">{doors}</div>

<p class="prov"><b>Where these numbers come from.</b> {prov_sentence}</p>
</div></body></html>
"""


def main(argv=None):
    """`build_front.py [fixture.json] [out.html]` -- the paths are arguments so the renderer can
    be exercised against a synthetic fixture without a real one in the tree. A builder whose
    input path is a constant can only be tested by putting a fake where the real file goes, and a
    fake sitting at the real path is one `git add -A` away from being committed as data."""
    argv = sys.argv[1:] if argv is None else argv
    fix = pathlib.Path(argv[0]) if argv else FIX
    out = pathlib.Path(argv[1]) if len(argv) > 1 else OUT
    fx = json.loads(fix.read_text())
    out.write_text(build(fx))
    globals()["OUT"] = out
    print(f"{OUT}  {len(OUT.read_text()):,} bytes")
    print(f"  claims drawn from: {len(fx['structural_holes'])} holes, "
          f"{len(fx['thin_positions'])} thin, bye week {fx['bye_profile'].get('worst_week')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
