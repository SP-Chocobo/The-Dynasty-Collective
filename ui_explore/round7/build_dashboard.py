#!/usr/bin/env python3
"""THE IN-LEAGUE DASHBOARD, IN THE ROUND-7 SHELL (`#350`).

What this is and -- more importantly -- what it is NOT.

IT IS NOT A FOURTH REDESIGN OF THE DASHBOARD. Three attempts at this surface have already been
made (`round5/build_dashboard.py`, and `round6`'s ledger/dispatch/standing), and the owner's
correction after the second was that I kept rebuilding the same job slightly differently
instead of building the thing that did not exist. So the CONTENT COMPOSITION here is imported
wholesale from `round5/build_dashboard.py` -- `claim_parts`, `claim_headline`, `expansion`,
`bye_ledger`, `verdict_prose`, `basis_note`, `pill`. Not one claim is composed in this file.

WHAT IS ACTUALLY NEW is the chrome: the room bar, the emblem, the league art band, the room
crest, and the two-rail layout, so that a league reads as the same product as the landing page
rather than as a separate artifact. That chrome is imported too (see below). This file is
therefore almost entirely ASSEMBLY, which is the point -- everything it draws already existed
and was already reviewed.

WHERE THE CHROME LIVES, AND THE DEBT THAT CREATES. It lives in `build_landing.py`, because that
is where it was built, measured and gated (`#349c`/`#349e` contrast-gated its top bar at nine
viewport widths). Importing it from there keeps ONE home (`#126`) and inherits those gates for
free. The cost is a module named for the landing page owning something shared, which is exactly
the kind of naming that rots. It is bounded on purpose: THE THIRD CONSUMER SHOULD TRIGGER AN
EXTRACTION into `chrome.py`. Two is not yet worth the risk, because the shell CSS cannot be
split by hand without a real chance of silently dropping a rule, and a CSS reorder destroys
byte-identity -- so the cheap safety check that made every other move here verifiable would not
be available for that one.

CLASS COLLISIONS, FOUND BEFORE THEY BIT. The imported content functions emit `.who` and
`.stamp`, and the chrome defines both for completely different jobs: `.who` is the right-aligned
Sleeper username block in the top bar and a flex row of away players in the bye ledger;
`.stamp` is a dashed badge and a line of dim prose. Every content rule here is therefore scoped
under `.dash`, which both raises specificity over the chrome's unscoped rules and keeps the top
bar's own `.who` out of reach. Checked by grepping the imported functions for their class
contract rather than by rendering and hoping.

A DEFECT THIS PAGE WILL SHOW YOU, AND IT IS NOT FIXED HERE. `#346` defect 1: the capture writes
`priced.get("trade_value") or 0.0`, so an UNPRICED player becomes a measured zero, and this page
prints `Dawson Knox 0` next to a TE card that says only one of two could be priced. The fix
belongs in `capture_front_fixture.py` (keep the numeric field, add `priced`), not in the
renderer -- `#338` says the render layer computes nothing, and quarantining it here would be a
second opinion about a quantity. It is left visible and said out loud rather than papered over.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ui_explore" / "round5"))
sys.path.insert(0, str(HERE))

import design_system as ds
import front_claims as fc

# ---- THE CONTENT: every claim on this page is composed by round 5, not here -----------------
#
# LOADED BY PATH, NOT BY NAME, and that is not fussiness. This file is ALSO called
# `build_dashboard.py`, and its own directory is on `sys.path` -- so a plain
# `import build_dashboard` resolves to THIS MODULE importing itself, and fails with an
# ImportError naming a symbol that plainly exists in round 5. The error points at the symbol and
# the cause is the filename, which is exactly the kind of misdirection that costs an hour.
# Keeping the shared name is deliberate (it says what the file is), so the import is explicit.
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location(
    "round5_dashboard", ROOT / "ui_explore" / "round5" / "build_dashboard.py")
_r5 = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_r5)
basis_note, bye_ledger, claim_headline = _r5.basis_note, _r5.bye_ledger, _r5.claim_headline
claim_parts, expansion, pill, verdict_prose = (_r5.claim_parts, _r5.expansion, _r5.pill,
                                               _r5.verdict_prose)
# ---- THE CHROME: one home, and it is the landing page's (see the module docstring) ----------
#
# ALSO LOADED BY PATH, AND FOR THE SAME REASON AS ROUND 5 ABOVE -- which I half-learned and then
# only half-applied. `build_landing.py` exists in BOTH round5 and round7. Run on its own this
# file's directory is first on sys.path and the plain import resolves correctly; under
# `unittest discover`, round5's directory is already on sys.path (its own tests put it there),
# so `from build_landing import ...` binds ROUND 5's module and fails with
# `ImportError: cannot import name 'asset_data_uri'` -- naming a symbol that plainly exists in
# the file I meant.
#
# It passed standalone and failed in the suite, which is exactly the trap `close-register-item`
# names: the full suite is what licenses a push, because a targeted run shares neither sys.path
# nor import order with it. Ten errors, one cause, and the cause was a filename I had already
# written a paragraph about twenty lines up.
_lspec = _ilu.spec_from_file_location("round7_landing", HERE / "build_landing.py")
_r7l = _ilu.module_from_spec(_lspec)
_lspec.loader.exec_module(_r7l)
asset_data_uri, assert_type_floor = _r7l.asset_data_uri, _r7l.assert_type_floor
assert_vars_resolve, shell_css = _r7l.assert_vars_resolve, _r7l.css
emblem, esc, font_vars = _r7l.emblem, _r7l.esc, _r7l.font_vars
hero_band, icon, panel = _r7l.hero_band, _r7l.icon, _r7l.panel
sechead, topbar = _r7l.sechead, _r7l.topbar

LOUD = ROOT / "ui_explore" / "front_fixture.json"
QUIET = ROOT / "ui_explore" / "quiet_fixture.json"
PAGES = ((HERE / "dashboard.html", LOUD), (HERE / "dashboard_quiet.html", QUIET))

#: This page is a ROOM, and the room is Matchup. The crest is the tribal mark banked in `#349i`;
#: it is drawn at 96px because `#349f` measured the medallion format dying below about 48.
ROOM = "Matchup"
ROOM_CREST = "room_matchup.webp"
CREST_PX = 96


def league_band():
    """The in-league art band -- a DIFFERENT image from the landing page's, deliberately.

    `#349e` chose it on the same measurements the landing band was chosen on, and gated it over
    this exact top bar at nine widths. The landing page is the hall you survey from; a league is
    one chamber inside it, so the landing band is the whole beast at distance and this one is
    the same beast close up. Same world, different room, which is the only job this image has.
    """
    return asset_data_uri("header_wyrm_league.jpg", "image/jpeg")


def room_crest():
    uri = asset_data_uri(ROOM_CREST, "image/webp")
    if not uri:
        return ""
    return (f'<img class="crestmark-room" src="{uri}" width="{CREST_PX}" height="{CREST_PX}" '
            f'alt="" aria-hidden="true">')


def seat_line(fx: dict, omit_league: bool = False) -> str:
    """WHO THIS IS ABOUT, with every absence labelled rather than blank (`#187`).

    `omit_league` drops the league's name from the line. The served page puts that name in the
    `<h1>` directly above, and repeating it there AND again under Provenance printed it three
    times on one screen -- "I dont need all the variables, i dont need every everything". The
    Provenance row still carries the full line, because that panel's job IS the full record.
    """
    from build_landing import absent
    bits = []
    team = str(fx.get("team") or "").strip()
    bits.append(f'<b>{esc(team)}</b>' if team else absent("no team name in this capture"))
    # `league_name` FIRST, and that ordering is `#366`. `from_snapshot` has always written the
    # league's name under `league_name`; this line read `league`, so every served dashboard
    # rendered the absence below while the name sat in the fixture one key away. Two names for
    # one fact (`#126`), and the page showed the emptier of them.
    #
    # `league` IS A CONFIG DICT in the committed fixtures, not a name --
    # {'roster_positions': [...], 'starting_slots': 10}. An earlier draft did
    # `str(fx.get("league") or "")` and printed that whole dict into the page header. Guard on
    # the TYPE, not on truthiness: a non-empty dict is truthy, so the falsy-check that reads as
    # a safe default was the thing that let it through.
    named = str(fx.get("league_name") or "").strip()
    league = fx.get("league")
    if named and omit_league:
        pass
    elif named:
        bits.append(esc(named))
    elif not omit_league:
        bits.append(esc(league.strip()) if isinstance(league, str) and league.strip()
                    else absent("this capture carries a league CONFIG but no league name"))
    arm = fx.get("arm") or fx.get("format")
    if arm:
        bits.append(f'<code>{esc(arm)}</code>')
    wk = fx.get("current_week")
    bits.append(f'week <b>{esc(wk)}</b>' if wk is not None
                else absent("no current week is on file, so nothing here carries a deadline"))
    return " &middot; ".join(bits)


def capture_date(players_db):
    """The capture date out of `_provenance.players_db`, which is a STRINGIFIED DICT.

    The fixture stores it as `"{'source': ..., 'captured_at': '2026-09-07T08:14:10.99...'}"` --
    a dict that was `str()`'d on the way in, so the structure survives as text and the types do
    not. That is a fixture defect worth its own item; this page is not the place to fix it.

    `ast.literal_eval` is the right tool and not a reconstruction (`#222`): it DECODES a repr
    back to the value that produced it, exactly, and refuses anything that is not a literal. A
    regex hunting for a date would be the reconstruction -- it would invent a parse rule the
    writer never used. Anything unparseable returns None and the caller renders an absence with
    its reason, never a guess and never a blank.
    """
    if isinstance(players_db, dict):
        rec = players_db
    elif isinstance(players_db, str):
        import ast
        try:
            rec = ast.literal_eval(players_db)
        except (ValueError, SyntaxError):
            # MEASURED: the fixture stores exactly 200 characters of this record and the rest is
            # gone -- it ends mid-string, inside a list. So the dict was str()'d AND truncated on
            # the way in. `captured_at` happens to survive inside those 200 characters, and
            # regexing it out would be exactly the reconstruction `#222` forbids: inventing a
            # parse rule the writer never used, on a record already known to be damaged. The
            # page renders an absence carrying the reason instead.
            return None
        if not isinstance(rec, dict):
            return None
    else:
        return None
    stamp = rec.get("captured_at") or rec.get("as_of")
    # A DATE, not a timestamp: the page says when, and the engine has no clock to say how long
    # ago, so it must not imply one (`standing`'s restraint in `#345d`, kept).
    return str(stamp)[:10] if stamp else None


def dash_css() -> str:
    """Dashboard-only rules. EVERY ONE SCOPED UNDER `.dash` -- see the docstring on collisions."""
    return """
.roomhead{display:flex;align-items:center;gap:20px;margin:4px 0 20px;position:relative;z-index:2}
/* A CIRCULAR MASK, NOT `mix-blend-mode`. The crest's own ground measures (0,0,0), so screen
   SHOULD composite it to nothing -- and it did not, because `.roomhead` carries `z-index:2` to
   sit above the art band, and a positioned element with a z-index creates a stacking context,
   which ISOLATES the blend from the page backdrop. The image then blended against nothing and
   rendered its square. Masking to the circle the crest already is removes the corners entirely,
   so it needs no blend, no stacking context and no isolation rule to reason about. */
.crestmark-room{display:block;flex:0 0 auto;opacity:.95;border-radius:50%;
  -webkit-mask-image:radial-gradient(circle at 50% 50%,#000 68%,transparent 71%);
  mask-image:radial-gradient(circle at 50% 50%,#000 68%,transparent 71%)}
.roomhead h1{font:400 1.75rem/1.15 var(--display);color:var(--gold-b);margin:0;
  letter-spacing:.04em}
.roomhead p{margin:7px 0 0;color:var(--muted);font-size:.86rem}
.roomhead code{font:400 .8rem/1 var(--mono);color:var(--dim)}

.dash .lead{display:grid;grid-template-columns:auto 1fr;gap:24px;align-items:center;
  padding:22px 26px;border:1px solid var(--line-2);border-radius:9px;position:relative;
  background:linear-gradient(180deg,var(--surface),var(--surface-2));overflow:hidden}
.dash .lead::before{content:"";position:absolute;inset:0;pointer-events:none;
  background:repeating-linear-gradient(135deg,transparent 0 5px,rgba(176,162,138,.05) 5px 6px);
  mask-image:linear-gradient(105deg,#000,transparent 62%)}
.dash .big{font:600 3.4rem/1 var(--mono);color:var(--gold-b);letter-spacing:-.03em;
  font-variant-numeric:tabular-nums;position:relative;text-shadow:0 0 26px rgba(249,222,153,.26)}
.dash .u{display:block;font:600 .78rem/1 var(--display);letter-spacing:.2em;
  text-transform:uppercase;color:var(--gold);margin-top:8px;position:relative}
.dash .lead h1{font:400 1.5rem/1.2 var(--display);color:var(--gold-b);margin:0 0 8px;
  position:relative}
.dash .lead p{margin:0;color:var(--muted);font-size:.9rem;max-width:62ch;position:relative}
.dash .lead p.sub{margin-top:6px;color:var(--dim);font-size:.82rem}

.dash .claim{border:1px solid var(--line);border-left-width:4px;border-radius:8px;
  padding:17px 19px;margin:12px 0 0;
  background:linear-gradient(180deg,var(--surface),var(--surface-2))}
.dash .claim.hole{border-left-color:var(--gold-b)}
.dash .claim.bye{border-left-color:var(--gold)}
.dash .claim.thin{border-left-color:var(--tie-b)}
.dash .chead{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.dash .chead h3{font:400 1.04rem/1.3 var(--sans);color:var(--ink);margin:0}
.dash .claim p{margin:9px 0 0;color:var(--muted);font-size:.9rem;line-height:1.55}
.dash .row{display:flex;gap:9px;flex-wrap:wrap;margin-top:14px}
.dash .basis{display:block;margin-top:9px;font:400 .78rem/1.5 var(--mono);color:var(--dim)}
.dash .stamp{display:block;font:400 .83rem/1.55 var(--sans);color:var(--dim);margin:12px 0 0;
  border:0;padding:0;letter-spacing:0;text-transform:none}
.dash .n{font-family:var(--mono);font-weight:600;color:var(--ink)}

/* the bye ledger -- the owner's favourite panel, imported unchanged from round 5 */
.dash .led{width:100%;border-collapse:collapse;font-size:.86rem}
.dash .led th{text-align:left;font:600 .75rem/1 var(--display);letter-spacing:.18em;
  text-transform:uppercase;color:var(--gold);padding:0 10px 9px 0;white-space:nowrap}
.dash .led td{padding:9px 10px 9px 0;border-top:1px solid var(--line);vertical-align:top}
.dash .wk{font:600 .84rem/1 var(--mono);color:var(--ink);white-space:nowrap}
.dash .who{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.dash .chip{display:inline-flex;align-items:center;gap:5px;font-size:.82rem;color:var(--muted)}
.dash .barcell{width:40%;min-width:110px}
.dash .barcell div{height:7px;border-radius:4px;background:var(--gold);min-width:2px}
.dash .ledfoot{display:flex;gap:18px;flex-wrap:wrap;margin-top:13px;font-size:.84rem;
  color:var(--muted)}
.dash .slots{display:flex;flex-wrap:wrap;gap:7px;margin:8px 0 0;padding:0;list-style:none}
.dash .slots li{font:400 .8rem/1 var(--mono);color:var(--muted);border:1px solid var(--line-2);
  border-radius:4px;padding:6px 9px}
.dash .kv{margin:0;display:grid;grid-template-columns:auto 1fr;gap:7px 14px;font-size:.85rem}
.dash .kv dt{color:var(--dim)}
.dash .kv dd{margin:0;color:var(--ink)}
.dash .popnote{margin:10px 0 0;font-size:.8rem;color:var(--dim);line-height:1.55}
.dash [popover]{border:1px solid var(--line-2);border-radius:9px;padding:20px 22px;
  max-width:34rem;background:linear-gradient(180deg,var(--surface),var(--surface-2));
  color:var(--ink);box-shadow:0 18px 60px rgba(0,0,0,.66)}
.dash [popover]::backdrop{background:rgba(0,0,0,.64)}
.backlink{color:var(--gold-b);text-decoration:none;border-bottom:1px solid var(--line-2)}
.backlink:hover{color:var(--gold)}
.dash [popover] h4{font:400 1.05rem/1.25 var(--sans);margin:0 0 12px;color:var(--gold-b)}
.dash .popclose{margin-top:16px}

.checkrow{display:grid;grid-template-columns:auto 1fr;gap:11px;align-items:start;
  padding:11px 0;border-bottom:1px solid var(--line)}
.checkrow:last-of-type{border-bottom:0}
.checkrow b{display:block;font:600 .76rem/1 var(--display);letter-spacing:.17em;
  text-transform:uppercase;color:var(--gold);margin-bottom:5px}
.checkrow span{font-size:.85rem;color:var(--muted)}
.checkrow .basis{margin-top:6px}

@media (max-width:1080px){
  .dash .lead{grid-template-columns:1fr;gap:14px}
  .roomhead{gap:14px}
  .crestmark-room{width:64px;height:64px}
}
"""


def room_title(fx: dict) -> str:
    """What this page is ABOUT, which is a league and not a room (`#366`).

    `ROOM` is the mockup's name for this layout -- the Matchup room -- and it shipped as the
    served `<h1>`, so opening any of nine leagues gave a page headed "Matchup" with no way to
    tell which league you were looking at. A fixture that names its league is titled by it; the
    committed fixtures carry no `league_name`, so those pages keep `ROOM` and rebuild
    byte-identically.
    """
    return str(fx.get("league_name") or "").strip() or ROOM


def build(fx: dict, *, home: str | None = None, unbuilt=()) -> str:
    title = room_title(fx)
    # Absence reasons the source layer computed. Empty for the committed fixtures, which is why
    # those pages do not move.
    why = (fx.get("_provenance") or {}).get("why") or {}
    # The nav rail marks a ROOM as current. When this page is one league rather than the mockup's
    # Matchup room, no room is current, and highlighting one would be a claim about where you are
    # that is not true.
    active = ROOM if title == ROOM else None
    band = fc.compose(fx)
    shown, hidden = band["shown"], band["hidden"]
    summary = fc.checks_summary(band["checks"])
    basis = (fx.get("_provenance") or {}).get("basis") or {}
    from build_landing import absent

    # ---- the lead claim. COMPOSED BY ROUND 5; this only places it. -------------------------
    n = len(shown) + len(hidden)
    words = {0: "Nothing", 1: "One thing", 2: "Two things", 3: "Three things", 4: "Four things"}
    headline = ("Nothing open this week." if not n
                else f'{words.get(n, str(n) + " things")} {"is" if n == 1 else "are"} open.')
    if shown:
        lead = claim_parts(shown[0])
        figure = (f'<div><span class="big">{lead["figure"]}</span>'
                  f'<span class="u">{lead["unit"]}</span></div>')
        prose = verdict_prose(shown + hidden, fx)
        sub = f'<p class="sub">{lead["eyebrow"]} &middot; {lead["headline"]}</p>'
    else:
        figure = (f'<div><span class="big">{summary["ran"]}</span>'
                  f'<span class="u">checks, all clean</span></div>')
        prose = ("Every check this page runs came back clean. The register on this page is what "
                 "was examined to say so.")
        sub = f'<p class="sub">{esc(", ".join(summary["clean"]))}</p>'

    cards, pops = [], []
    for i, c in enumerate(shown):
        parts, exp, pid = claim_parts(c), expansion(c, fx), f"exp{i}"
        pos = c.get("position") or (c.get("positions") or [None])[0]
        controls = [f'<a class="btn ghost" href="#{esc(c["route"].lower().replace(" ", "-"))}">'
                    f'{esc(c["route"])} &rsaquo;</a>']
        if exp:
            controls.insert(0, f'<button class="btn" popovertarget="{pid}">'
                               f'{icon("layers", 16)}What it is made of</button>')
            pops.append(f'<div id="{pid}" popover><h4>{parts["eyebrow"]}</h4>{exp}'
                        f'<div class="popclose"><button class="btn ghost" popovertarget="{pid}" '
                        f'popovertargetaction="hide">Close</button></div></div>')
        key = {"bye": "bye_profile", "thin": "thin_positions",
               "hole": "structural_holes"}.get(c["kind"], "")
        cards.append(
            f'<article class="claim {esc(c["kind"])}">'
            f'<div class="chead">{pill(pos) if pos else ""}'
            f'<h3>{parts["headline"]} &middot; {parts["figure"]} {parts["unit"]}</h3></div>'
            f'<p>{parts["body"]}</p>{basis_note(basis, key)}'
            f'<div class="row">{"".join(controls)}</div></article>')
    if not cards:
        cards.append('<p class="stamp">Nothing is standing. The register on this page is what '
                     'was examined to say so.</p>')
    if hidden:
        cards.append('<p class="stamp">Also standing: '
                     + "; ".join(claim_headline(c) for c in hidden) + ".</p>")

    # ---- the register: what ran, each with its basis. `checks_run` (`#342`) drives it. -----
    rows = []
    for check in band["checks"]:
        key = {"byes": "bye_profile", "depth": "thin_positions",
               "holes": "structural_holes"}.get(check["name"], "")
        glyph = {"clean": ("check", "ok"), "fired": ("crown", ""),
                 "absent": ("search", "off")}.get(check["state"], ("check", ""))
        said = {"clean": "nothing found", "fired": "raised something",
                "absent": "not measured"}.get(check["state"], check["state"])
        rows.append(f'<div class="checkrow">{icon(glyph[0], 17, "ic " + glyph[1])}'
                    f'<div><b>{esc(check["name"])}</b><span>{esc(said)}</span>'
                    f'{basis_note(basis, key)}</div></div>')

    # A LINK ONLY WHEN THERE IS SOMEWHERE TO GO. The committed pages are standalone files with
    # no server behind them, so they get no back link rather than a dead one -- the defect this
    # whole pass exists to stop repeating (`#365`).
    back = (f'<a class="backlink" href="{esc(home)}">&lsaquo; All leagues</a> &middot; '
            if home else "")
    prov = (fx.get("_provenance") or {})
    captured = capture_date(prov.get("players_db"))
    prov_rows = (f'<dl class="kv"><dt>Seat</dt><dd>{seat_line(fx)}</dd>'
                 f'<dt>Players captured</dt><dd>'
                 f'{"<code>" + esc(captured) + "</code>" if captured else absent("the capture carries no date")}'
                 f'</dd><dt>Record</dt><dd>off this page &mdash; it asks nothing of you</dd></dl>')

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap">
<style>{ds.root_css_block()}{font_vars()}{ds.position_pill_css_block()}{shell_css()}{dash_css()}</style>
</head><body>
<div class="wrap dash">
{topbar(None, league_band(), home=False, active=active, home_href=home, unbuilt=unbuilt)}

  <div class="roomhead">
    {room_crest()}
    <div>
      <h1>{esc(title)}</h1>
      <p>{seat_line(fx, omit_league=title != ROOM)}</p>
    </div>
  </div>

  <div class="shell">
    <div class="rail-left">
      {panel("check", "What was checked",
             '<p class="sub">Every check this page ran, in ladder order, each with the engine '
             'call behind it.</p>' + "".join(rows))}
      {panel("disk", "Provenance", prov_rows)}
    </div>

    <div class="rail-main">
      <section class="lead">
        {figure}
        <div><h1>{headline}</h1><p>{prose}</p>{sub}</div>
      </section>
      {"".join(cards)}
      {sechead("chart", "The bye weeks",
               "Each week below is the lineup solved again with that week&rsquo;s byes removed. "
               "The figure is value lost, not bodies away.")}
      {panel("swap", "Week by week", bye_ledger(fx, why.get("bye_profile", "")))}
    </div>
  </div>
  {"".join(pops)}

  <p class="foot">{back}
    One league, in depth. Which league wants you is the landing page&rsquo;s question, not this
    one&rsquo;s.<br>
    Every figure here is the engine&rsquo;s own; this page arranges them and computes nothing.
  </p>
</div>
</body></html>"""


def main(argv=None):
    assert_type_floor(shell_css() + dash_css())
    assert_vars_resolve(ds.root_css_block(), font_vars(), ds.position_pill_css_block(),
                        shell_css(), dash_css())
    for out, fixture in PAGES:
        out.write_text(build(json.loads(fixture.read_text())))
        print(f"{out}  {len(out.read_text()):,} bytes  from {fixture.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
