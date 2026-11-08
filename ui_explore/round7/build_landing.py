#!/usr/bin/env python3
"""THE LANDING PAGE, REBUILT AS WHAT IT ACTUALLY IS (`#347`).

THE OWNER'S CORRECTION, which is the whole reason this file exists and replaces `round5`'s:

    See you're not getting what I'm saying. This again just feels like a rebuild of the
    dashboard. The landing page just needs to say "these leagues need attention." "resync"
    "add league" and the connections options, no?
    ... league management and connections/setups too, maybe
    ... as in setting up new league, deleting leagues, and the like

That was the third miss on this surface, and the first two were the same mistake twice:
`round5/build_dashboard.py` rebuilt the in-league dashboard, and `round5/build_landing.py`
rebuilt the CLAIM BAND at twelve-league arity. Both are analysis. The landing page is not an
analysis surface at all -- it is the ENTRY AND MANAGEMENT page. Claim detail lives inside a
league; this page says which leagues want you and lets you operate the set.

    dashboard   ONE league, many facts   -> panels, a ledger, density
    round5 land MANY leagues, one claim  -> still analysis, just wider
    THIS PAGE   the LEAGUE SET itself    -> a list + the verbs that change it

So the content is: triage, resync, add, delete/archive, connections. Four of those five are
verbs. That is the tell -- a page whose job is mostly verbs is not a dashboard.

EVERY AFFORDANCE HERE WAS READ OUT OF `app.py` BEFORE IT WAS DRAWN. The hard law of this
project is that you may not invent a quantity; the same law applies to an ACTION, and a button
that promises something the engine cannot do is the same defect wearing a different hat. What
was checked, and what it changed about the drawing:

  Add a league     TWO REAL PATHS, not one. `app.py:2498` takes a raw Sleeper LEAGUE ID and
                   calls `client.get_league(id)` -- one league, appended. `app.py:2328`
                   `sync_leagues(username)` takes an account and REPLACES the whole list.
                   An earlier draft of this page had only the account path and would have
                   drawn "Add league" as a lie about what the button does.
  Delete           `app.py:1438 delete_league_completely` is REAL, LOCAL, and CONFIRMED
                   (`pending_delete_league_id`, app.py:3391). It is NOT a departure: its own
                   docstring says it never touches Sleeper, and a league you are still in
                   "will simply reappear, unsynced, next time they click Sync Leagues". The
                   page says that, because a delete button that reads as leaving the league
                   is the most expensive misunderstanding available on this surface.
  Archive/reorder  `league_prefs.toggle_archive` / `move_league` -- local, and Sleeper has no
                   concept of either (its own module docstring says so).
  Leagues you left `sync_leagues` diffs the fresh list against `order + archived` and sets
                   `left_league_ids`. Real, already computed, and currently has no surface.
  Connections      `providers.ids()` resolves to claude/gemini/openai ONLY after `llm_engine`
                   is imported (the registry is populated at its import, not at
                   `providers`'). Labels are read from the registry, never typed here:
                   openai's real label is "ChatGPT", which is not what I would have guessed.

WHAT THIS PAGE MAY STILL NOT DO. The round-6 forbidden list survives intact, and this surface
is where the worst of them is most tempting: N rows plus a summary is a shape that begs for a
portfolio grade. There is no cross-league total, no ranking of leagues by size, no score. The
headline is a COUNT of real things. Ordering is by RUNG (`front_claims.LADDER`), never by
figure, because two leagues' figures are different units wearing one label (`#341`).
"""
from __future__ import annotations

import glob
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ui_explore" / "round5"))

import design_system as ds
import front_claims as fc
# THE PROVIDER LIST IS READ, NEVER TYPED (`#348`, and the owner's rule that made it):
#
#     api keys need to be agnostic, not tied to specific models, companies, etc. if i wanted
#     to integrate kimi k2 or grok, that should not fight the language used
#
# `providers.py` is already a registry and already agnostic -- a frozen `Provider` dataclass
# with `id`, `label`, `key_field` and an `is_configured` callable. The registry is EMPTY at
# `providers`' own import and is populated at `llm_engine`'s (which is why this import is here
# and not decorative): `providers.ids()` returns `()` until then, and a page that read it too
# early would render an empty connections card and look correct.
#
# So this builder names no provider anywhere. It asks the registry for labels and credential
# names, which is how a provider registered tomorrow appears here with no edit to this file --
# and how I learned that openai's real label is "ChatGPT", which I would not have typed.
import llm_engine  # noqa: F401  -- imported for its registration side effect, not its API
import providers
# ONE HOME (`#126`) for the shared render vocabulary. The escaper, the absence grammar, the
# position pill, the brand mark and both build-time gates live in the dashboard builder.
from build_dashboard import WYRM, absent, esc, pill

TYPE_FLOOR_REM = 0.75          # 12px at a 16px root
NON_TEXT_FLOOR = 3.0           # WCAG non-text contrast
#: Every token this page uses as a MARK rather than as text -- the four row rails and the two
#: claim dots. Each must clear the non-text floor against the ground it is drawn on.
MARKS = (("hole rail", "gold-b"), ("bye rail", "gold"), ("thin rail", "tie-b"),
         ("quiet rail", "status-ok"), ("bye dot", "gold"), ("hole dot", "gold-b"))


def assert_marks_are_visible():
    """A rail nobody can see is not a quiet rail, it is a missing one.

    THIS IS NOT `build_dashboard._assert_ramp_is_visible`, AND THAT IS THE POINT. That function
    reads `build_dashboard.SEVERITY` -- its own module global. Imported and called from here it
    would check the dashboard's three tokens, pass unconditionally, and tell me nothing about
    this page's six. A gate that cannot fail on the file it is guarding is the hollow-instrument
    failure this session has now caught six times, so the gate is rewritten against this page's
    own marks rather than imported.
    """
    bad = [(name, token, round(ds.contrast_ratio(token, "bg"), 2))
           for name, token in MARKS if ds.contrast_ratio(token, "bg") < NON_TEXT_FLOOR]
    if bad:
        raise SystemExit(f"marks below the {NON_TEXT_FLOOR}:1 non-text floor: {bad}")


def font_vars() -> str:
    """Define the three face stacks as CSS custom properties, DERIVED from `design_system`.

    `design_system.root_css_block()` defines the colour tokens but NOT the faces -- those are
    Python constants (`FONT_SANS`/`FONT_MONO`/`FONT_DISPLAY`) that `round5` substitutes into its
    stylesheet with `.format()`. This file used `var(--sans)` without defining it, which does
    not fail loudly: an unresolvable `var()` inside a `font:` SHORTHAND makes the whole
    declaration invalid, so every rule that set size and face together was dropped entirely and
    the page rendered at inherited sizes. Measured: the type scale read 12->22px instead of
    12->54px, and the 3.4rem tally rendered at about 14. `assert_vars_resolve` below now fails
    the build on it. Defining them here from the same constants keeps one home (`#126`).
    """
    return (f":root{{--sans:{ds.FONT_SANS};--mono:{ds.FONT_MONO};"
            f"--display:{ds.FONT_DISPLAY}}}")


def assert_vars_resolve(*blocks: str):
    """Every `var(--x)` this page uses must be defined by one of the blocks it ships with.

    This gate exists because the failure it catches is SILENT. A dropped `font:` shorthand
    does not warn, does not appear in the console, and renders a complete, plausible page at
    the wrong size -- the same shape as every measurement error in this repo's history.
    """
    import re
    joined = "".join(blocks)
    defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", joined))
    used = set(re.findall(r"var\((--[a-z0-9-]+)", joined))
    missing = sorted(used - defined)
    if missing:
        raise SystemExit(f"CSS variables used but never defined (a var() inside a font: "
                         f"shorthand silently drops the whole rule): {missing}")


def assert_type_floor(stylesheet: str):
    """No declared size under 12px, checked at build time against THE CSS PASSED IN.

    Same reasoning as above: the dashboard's version closes over its own `CSS` global, so it
    takes no argument and cannot be aimed at another file's stylesheet. This one takes the
    sheet as a parameter, which is what makes it capable of failing here.
    """
    import re
    under = sorted({float(m.group(1))
                    for m in re.finditer(r"font(?:-size)?:[^;}]*?([\d.]+)rem", stylesheet)
                    if float(m.group(1)) < TYPE_FLOOR_REM})
    if under:
        raise SystemExit(f"declared font sizes below the {TYPE_FLOOR_REM}rem floor: {under}")
    ems = [m.group(0) for m in re.finditer(r"font-size:\s*[\d.]+em", stylesheet)]
    if ems:
        raise SystemExit("small type must be declared in rem, not em, so the floor is "
                         f"checkable without a browser: {ems}")

SEATS = str(ROOT / "ui_explore" / "seats" / "seat*.json")
FIXTURE = HERE / "landing_fixture.json"
OUT = HERE / "landing.html"
OUT_EMPTY = HERE / "landing_unsynced.html"

#: THE STAND-IN, STAMPED (`#187`). The league ROWS are real composed claim bands, but they are
#: twelve SEATS of one replayed battery league on one clock standing in for twelve leagues.
#: Real leagues differ in format, scoring and bye schedule; these share all three, so the
#: spread of rungs here is narrower than a real portfolio's.
STANDIN = ("twelve seats of one replayed league standing in for twelve leagues -- they share a "
           "format, a scoring set and a bye schedule, so the spread of rungs is narrower here "
           "than a real portfolio's")

#: WHAT A DELETE COSTS, read off `delete_league_completely`'s own docstring rather than
#: summarised from memory. The last line is the one that matters most to a reader.
DELETE_COSTS = [
    "cached Sleeper snapshots for this league",
    "its own Draft Sharks uploads &mdash; never the shared rankings pool",
    "chat history and compaction backups",
    "decisions, objectives and pinned messages",
    "its format override, and any attachment scoped only to it",
]
DELETE_NOT = ("It never touches Sleeper. If you are still a member the league reappears, "
              "unsynced, the next time you sync the account.")

RUNG_ORDER = {kind: i for i, (kind, _) in enumerate(fc.LADDER)}
RUNG_CLASS = {"hole": "hole", "bye": "bye", "thin": "thin"}


# ---------------------------------------------------------------------------
# the rows


def summary_sentence(s: dict) -> str:
    """`checks_summary` returns a DICT, deliberately (`#338`: the surface never derives counts).

    It must therefore be composed into a sentence, not printed. An earlier draft of this file
    interpolated the dict straight into the row and shipped
    `{'ran': 3, 'clean': ['holes', 'byes', 'depth'], ...}` onto the page -- caught by looking at
    the render, which is the only thing that would have caught it.

    `all_clean` is read, never recomputed: it is False when every check was ABSENT, where
    "nothing fired" is vacuously true and "all clean" would be the most dishonest sentence
    available here.
    """
    ran, absent_names = s["ran"], s["absent"]
    if not ran and absent_names:
        return f"no check ran; {len(absent_names)} could not be measured"
    body = f'{ran} check{"" if ran == 1 else "s"}'
    if s["all_clean"]:
        return f'{body}, all clean &mdash; {", ".join(s["clean"])}'
    parts = []
    if s["fired"]:
        parts.append(f'{", ".join(s["fired"])} raised something')
    if s["clean"]:
        parts.append(f'{", ".join(s["clean"])} clean')
    if absent_names:
        parts.append(f'{", ".join(absent_names)} not measured')
    return f'{body} &mdash; {"; ".join(parts)}'


def league_rows(paths, archived_ids):
    """`front_claims.compose` per seat, split into (attention, quiet, archived).

    A PURE FUNCTION OF THE FIXTURES. The engine decides what is open; this only arranges.
    """
    rows = []
    for path in sorted(paths):
        stem = pathlib.Path(path).stem
        fx = json.loads(pathlib.Path(path).read_text())
        band = fc.compose(fx)
        shown, hidden = band["shown"], band["hidden"]
        top = shown[0] if shown else None
        rows.append({
            "seat": stem,
            "team": str(fx.get("team") or "").strip() or None,
            "arm": fx.get("arm") or fx.get("format"),
            "shown": shown,
            "hidden": hidden,
            "open": len(shown) + len(hidden),
            "top": top,
            "checks": band["checks"],
            "summary": summary_sentence(fc.checks_summary(band["checks"])),
            "rung": RUNG_ORDER.get(top["kind"], 99) if top else 99,
            "archived": stem in archived_ids,
        })

    live = [r for r in rows if not r["archived"]]
    archived = [r for r in rows if r["archived"]]
    attention = sorted([r for r in live if r["top"]],
                       key=lambda r: (r["rung"], -r["open"], r["team"] or ""))
    quiet = sorted([r for r in live if not r["top"]], key=lambda r: r["team"] or "")
    return attention, quiet, archived


# ---------------------------------------------------------------------------
# render helpers


def claim_line(row):
    """One line naming WHAT is open, by kind. Never a size, never a comparison."""
    top = row["top"]
    if top is None:
        return ('<span class="ok">&#10003;</span> <span class="txt">Nothing open. '
                f'{row["summary"]}</span>')
    kind, label = top["kind"], top.get("label") or top.get("position") or ""
    bits = []
    if kind == "thin" and top.get("position"):
        bits.append(pill(top["position"]))
        count = top.get("count")
        valued = top.get("valued_count")
        body = f'{top["position"]} rates <b>{esc(top.get("label") or "Weak")}</b>'
        if count is not None:
            body += f' &middot; <b>{count}</b> rostered'
        # `#190`: valued_count travels with count and names a DIFFERENT set.
        if valued is not None and count is not None and valued != count:
            body += f', <b>{valued}</b> priced'
        bits.append(f'<span class="txt">{body}</span>')
    elif kind == "bye":
        wk = top.get("week")
        bits.append('<span class="dot bye"></span>')
        bits.append(f'<span class="txt">Bye damage &middot; '
                    f'{"week <b>%s</b>" % esc(wk) if wk is not None else "a measured week"}'
                    f'</span>')
    elif kind == "hole":
        bits.append('<span class="dot hole"></span>')
        bits.append(f'<span class="txt">Unfilled starting slot &middot; '
                    f'<b>{esc(top.get("slot") or top.get("position") or "")}</b></span>')
    else:
        bits.append(f'<span class="txt">{esc(label)}</span>')
    more = row["open"] - 1
    if more > 0:
        bits.append(f'<span class="more">+{more} more</span>')
    return "".join(bits)


def row_html(row, idx):
    """One league line: identity, what is open, and the verbs that act on it."""
    kind = RUNG_CLASS.get(row["top"]["kind"], "") if row["top"] else "quiet"
    name = row["team"] or "this league"
    pop = f'pop-{row["seat"]}'
    team_absent = "" if row["team"] else absent("no league name in this capture")
    return f"""
<div class="lrow {kind}">
  <span class="rail"></span>
  <a class="lid" href="#{esc(row['seat'])}">
    <p class="lname">{esc(name) if row['team'] else team_absent}</p>
    <p class="lmeta">{esc(row['arm'] or '')}</p>
  </a>
  <div class="lclaim">{claim_line(row)}</div>
  <div class="lacts">
    <button class="act" popovertarget="{pop}" aria-label="Manage {esc(name)}">&middot;&middot;&middot;</button>
    <a class="go" href="#{esc(row['seat'])}" aria-label="Open {esc(name)}">&rsaquo;</a>
  </div>
  <div popover id="{pop}" class="pop">
    <p class="popttl">{esc(name)}</p>
    <p class="popmeta">{esc(row['arm'] or '')} &middot; {row['summary']}</p>
    <button class="pact">Resync this league</button>
    <p class="pcost">Re-pulls rosters and this week&rsquo;s projections for this league only.</p>
    <button class="pact">{'Unarchive' if row['archived'] else 'Archive'}</button>
    <p class="pcost">Hides it from the list. Local only &mdash; Sleeper has no concept of it.</p>
    <button class="pact danger">Delete local data&hellip;</button>
    <p class="pcost">Asks first. Removes {len(DELETE_COSTS)} local stores.
      {DELETE_NOT}</p>
  </div>
</div>"""


def section(title, note, rows, empty=None):
    if not rows:
        return f"""
<section class="band">
  <p class="eyebrow">{esc(title)}</p>
  <p class="bnote">{empty or ''}</p>
</section>"""
    body = "".join(row_html(r, i) for i, r in enumerate(rows))
    return f"""
<section class="band">
  <p class="eyebrow">{esc(title)}</p>
  {f'<p class="bnote">{note}</p>' if note else ''}
  <div class="leagues">{body}</div>
</section>"""


def provider_rows(configured_fields):
    """One row per REGISTERED provider, in registration order.

    `configured_fields` is the only part that is fixture data -- whether a given credential
    happens to be set is a property of the environment, not of the registry. The identities
    come from `providers`, so this function contains no vendor name and cannot go stale.

    The credential name shown is `key_field`, which the `Provider` docstring calls the ".env
    vocabulary" and which is deliberately NOT the id. The full environment-variable spelling
    is NOT reconstructed from it: that mapping lives in a hardcoded table in `app.py` that the
    registry does not reach (`#348`), and guessing it here would be inventing a second home
    for it (`#126`).
    """
    ids = providers.ids()
    if not ids:
        return ('<p class="hint">' +
                absent("no provider is registered, so there is nothing to configure") +
                "</p>")
    out = []
    for pid in ids:
        p = providers.get(pid)
        on = p.key_field in configured_fields
        state = ("<span class='ok'>&#10003;</span> configured" if on
                 else "<span class='off'>&mdash;</span> not set")
        out.append(f"""
    <div class="crow">
      <span class="cname">{esc(p.label)}</span>
      <code class="ckey">{esc(p.key_field)}</code>
      <span class="cstate {'on' if on else 'no'}">{state}</span>
    </div>""")
    return "".join(out)


def source_rows(sources):
    out = []
    for s in sources:
        if s["days"] is None:
            # ONE dash, not two. An absence is stated once; `— · —` reads as a broken template
            # rather than as information, which is the round-6 brief's own rule about absence.
            cell = absent("not loaded, so it has no date and no age to report")
        else:
            cell = f'<code>{esc(s["as_of"])}</code> &middot; <b>{s["days"]}</b>d'
        out.append(f'<div class="srow"><span>{esc(s["label"])}</span>'
                   f'<span class="sage">{cell}</span></div>')
    return "".join(out)




# ---------------------------------------------------------------------------
# ORNAMENT (`#349`). Drawn, not fetched.
#
# The owner's reference mockup carries a gold mountain-and-castle hero band. THAT ART DOES NOT
# EXIST. `assets/header_banner.jpg` is the repo's only banner and it is a BLUE football in
# space -- 1680x260, already embedded by `app.py:3682` as a base64 data URI. Blue beside this
# palette's gold is a clash, so it is used here the way `app.py` uses it: as texture under a
# gradient, at low opacity, never as a photograph.
#
# Everything else in the reference -- the crest, the laurels, the section glyphs, the glowing
# rules -- is INLINE SVG rather than an image. That is not a compromise: a glyph drawn in SVG
# is crisp at any size, takes its colour from the theme tokens, costs no network, and cannot
# ship a hardcoded hex that `#312` would have to find later. An illustration is worth an image;
# an icon is not.

#: Every glyph on the page, in one place. Stroked, not filled, so one `currentColor` drives
#: them all and a theme change cannot leave an icon behind (`#126`).
ICONS = {
    "crown":   "M3 17h18M4 17 3 7l5 4 4-6 4 6 5-4-1 10",
    "check":   "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M8 12l3 3 5-6",
    "archive": "M3 7h18v4H3zM5 11v9h14v-9M10 15h4",
    "gear":    "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6M12 2v3M12 19v3M2 12h3M19 12h3"
               "M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2",
    "plus":    "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18M12 8v8M8 12h8",
    "layers":  "M12 3 2 8l10 5 10-5zM2 14l10 5 10-5M2 11l10 5 10-5",
    "link":    "M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-2 2M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l2-2",
    "disk":    "M12 3c5 0 9 1.3 9 3s-4 3-9 3-9-1.3-9-3 4-3 9-3M3 6v12c0 1.7 4 3 9 3s9-1.3 9-3V6M3 12c0 1.7 4 3 9 3s9-1.3 9-3",
    "refresh": "M21 12a9 9 0 1 1-2.6-6.4M21 3v6h-6",
    "user":    "M12 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8M4 21a8 8 0 0 1 16 0",
    "chart":   "M4 20V10M10 20V4M16 20v-7M22 20H2",
    "search":  "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14M16 16l5 5",
    "swap":    "M4 8h14l-4-4M20 16H6l4 4",
}


def icon(name: str, size: int = 18, cls: str = "ic") -> str:
    d = ICONS[name]
    return (f'<svg class="{cls}" width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true"><path d="{d}"/></svg>')


def crest(figure: str, of: str) -> str:
    """The tally, set in a shield between two laurel sprigs.

    THE ORNAMENT MAY NOT OUTRANK THE NUMBER. The shield is a container; the figure inside it is
    still the largest type on the page, and the laurels are `--line-2` so they read as a frame
    rather than as a second mark competing with it. `#336b`'s lesson applied to decoration:
    ornament that implies an award -- a medal, a ribbon, a rosette -- would be asserting a
    JUDGEMENT about the number, and this number is a count of open things, not a score.
    """
    laurel = ('M11 4c-4 2-6 6-6 11 0 4 2 7 5 9M11 7c-3 0-5 1-6 3M10 12c-3 0-5 1-6 3'
              'M10 17c-2 0-4 1-5 2')
    return f"""
<div class="crest">
  <svg class="laurel l" width="26" height="62" viewBox="0 0 22 26" fill="none"
       stroke="currentColor" stroke-width="1.1" stroke-linecap="round" aria-hidden="true">
    <path d="{laurel}"/></svg>
  <svg class="shield" width="132" height="146" viewBox="0 0 66 73" aria-hidden="true">
    <defs><linearGradient id="sg" x1="0" y1="0" x2=".35" y2="1">
      <stop offset="0" stop-color="#755024"/><stop offset=".45" stop-color="#ba9561"/>
      <stop offset=".8" stop-color="#f9de99"/><stop offset="1" stop-color="#fff4ce"/>
    </linearGradient></defs>
    <path d="M33 2 62 10v27c0 18-14 29-29 34C19 66 4 55 4 37V10z"
          fill="rgba(117,80,36,.13)" stroke="url(#sg)" stroke-width="2"/>
    <path d="M33 7 57 13v24c0 15-12 25-24 29C21 62 9 52 9 37V13z"
          fill="none" stroke="rgba(186,149,97,.35)" stroke-width="1"/>
  </svg>
  <svg class="laurel r" width="26" height="62" viewBox="0 0 22 26" fill="none"
       stroke="currentColor" stroke-width="1.1" stroke-linecap="round" aria-hidden="true">
    <path d="{laurel}"/></svg>
  <p class="tally">{figure}<s>/{of}</s></p>
</div>"""


def asset_data_uri(name: str, mime: str):
    """Embed an asset, exactly as `app.py:127` embeds the banner.

    ONE HOME for the "asset or nothing" rule (`#126`): a missing file means that element is not
    drawn, never a broken header. Returns None on any read failure, and every caller treats that
    as "draw without it" -- which is also what happens in a checkout without `assets/`.
    """
    import base64
    try:
        return f"data:{mime};base64," + base64.b64encode(
            (ROOT / "assets" / name).read_bytes()).decode("ascii")
    except (FileNotFoundError, OSError):
        return None


def banner_data_uri():
    """The landing page's header art.

    NOT `header_banner.jpg`. That one is the blue football `app.py:3682` still uses for the
    Streamlit header, and it is left alone deliberately -- swapping the app's own banner is a
    change to the running product, not to this mockup, and it is the owner's call.
    `header_wyrm.jpg` is the gold wyrm generated for this page: the FULL 1600x538 frame rather
    than a pre-cropped strip, because the band is now full-bleed and on a wide monitor runs
    past 11:1, where a 6.46:1 strip would have nothing left to crop. `cover` plus
    `background-position` does the framing at render time and survives a layout change without
    a re-export.
    """
    return asset_data_uri("header_wyrm.jpg", "image/jpeg")


def emblem(size: int = 44) -> str:
    """THE REAL EMBLEM, not the stand-in arc.

    `WYRM` is a hand-drawn SVG crescent that stood in while no brand asset was reachable. The
    actual logo was in the tree the whole time at `ui_explore/round4/_ref/wyrm_crop.png` -- a
    510x420 RGB crop of goldwyrm.com's gold dragon. `assets/wyrm_emblem.png` is derived from it:
    alpha keyed from LUMINANCE (the mark is gold, its ground near-black, so the two separate
    without a hand-drawn mask), trimmed to content, and resized to 128px wide.

    WHY THE KEYING MATTERED. The crop has no alpha and its ground is a textured dark grey
    slightly LIGHTER than this page's `--bg`. Dropped in as-is it renders as a visible grey
    plaque behind the dragon, and neither `lighten` nor `screen` fixes that -- both leave the
    ground showing, because it is brighter than what it sits on. Keying is the only treatment
    that lets the mark antialias against the page instead of carrying its own rectangle.

    Falls back to `WYRM` when the asset is unreadable, per `asset_data_uri`'s rule.
    """
    uri = asset_data_uri("wyrm_emblem.png", "image/png")
    if not uri:
        return WYRM
    return (f'<img class="emblem" src="{uri}" width="{size}" height="{round(size * 108 / 128)}" '
            f'alt="" aria-hidden="true">')


def wyrm_mark():
    """The empty-state wyrm, composited by SCREEN rather than by an alpha channel.

    WHY NO ALPHA. The emblem needed keying because its ground was a textured dark grey
    measurably BRIGHTER than this page's --bg, so a blend mode would have left the ground
    showing. This image's void measures a maximum channel value of 1 -- effectively pure black
    -- and `screen` leaves the backdrop untouched wherever the source is darker than it. So the
    ground composites to nothing on its own, and the file ships with no alpha plane at all.

    That is not a stylistic choice, it is 3-6x the file. Keyed and graded with alpha the same
    art costs 150KB at 560px (and 490KB at 760px): WebP keeps alpha LOSSLESS by default, and the
    alpha plane of a filigree dragon is essentially noise, which is why dropping quality from 72
    to 55 moved the size by 4% and nothing else. Without the alpha plane it is 77KB.

    The rule this generalises to, for every future piece: ask for a PURE BLACK void and the art
    needs no mask. Ask for atmosphere and it needs one, and the mask costs more than the art.
    """
    uri = asset_data_uri("wyrm_coiled.webp", "image/webp")
    if not uri:
        return ""
    return f'<div class="wyrmmark" aria-hidden="true" style="background-image:url({uri})"></div>'


def hero_band(uri):
    """The art layer. A SLOT, so replacing the image is a one-line change.

    The reference mockup's gold hero does not exist yet; when it does it drops in here and
    nothing else moves. Until then the real blue banner runs at 0.22 under a gold gradient --
    enough to read as atmosphere, not enough to fight the palette.
    """
    if not uri:
        return '<div class="band" aria-hidden="true"></div>'
    return (f'<div class="band" aria-hidden="true">'
            f'<div class="bandart" style="background-image:url({uri})"></div></div>')


def sechead(name, label, note=None):
    rule = '<span class="rule"></span>'
    body = f'<p class="snote">{note}</p>' if note else ""
    return (f'<div class="sechead">{icon(name, 19)}'
            f'<p class="eyebrow">{esc(label)}</p>{rule}</div>{body}')


# ---------------------------------------------------------------------------
# CSS


def css():
    return """
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--ink)}
body{font:400 .95rem/1.55 var(--sans);-webkit-text-size-adjust:100%}
.wrap{max-width:94rem;margin:0 auto;padding:0 22px 60px}
a{color:inherit}
.ic{flex:0 0 auto;vertical-align:-3px}

/* ---- top bar: wordmark, rooms, connection ---- */
.top{display:flex;align-items:center;gap:26px;padding:24px 0 16px;flex-wrap:wrap;position:relative;z-index:1}
.crestmark{display:flex;align-items:center;gap:12px}
.emblem{display:block;flex:0 0 auto}
.word{font:600 1.3rem/1 var(--display);letter-spacing:.11em;text-transform:uppercase;margin:0;
  background:linear-gradient(176deg,#755024 0%,#ba9561 38%,#f9de99 68%,#fff4ce 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent}
.word b{display:block;font-size:.75rem;letter-spacing:.42em;font-weight:400;margin-top:5px}
.rooms{display:flex;gap:4px;flex-wrap:wrap;position:relative}
/* The room tabs need the same protection as the connection block, and for the same reason.
   An earlier check on this page sampled only the FIRST inactive tab -- which happens to sit in
   the band's dark left region -- and reported 4.80:1, clean. Measuring EVERY tab showed the
   right-hand ones (Draft Room, League, Import Audit) at 3.34:1 over the lit part of the art.
   A gate that samples one member of a row and reports on the row is the same hollow instrument
   as a mutation whose verdict was piped away: it cannot fail where the failure actually is. */
.rooms::before{content:"";position:absolute;inset:-10px -22px;z-index:-1;pointer-events:none;
  background:radial-gradient(ellipse at 50% 50%,rgba(11,11,13,.97) 0%,rgba(11,11,13,.9) 58%,
    rgba(11,11,13,0) 86%)}
/* --muted, NOT --dim. `--dim` measures 4.82:1 on the flat background -- it clears the 4.5
   floor with 0.3 of headroom, which is fine for de-emphasised metadata and wrong for a
   clickable label, because ANY art behind it spends that headroom immediately. Three rounds of
   scrim-tuning were chasing a symptom: the tabs were at the floor before the band existed.
   `--muted` is 7.89:1, which is the margin a navigation label should have had all along. */
.room{display:flex;flex-direction:column;align-items:center;gap:5px;min-width:72px;
  min-height:44px;padding:9px 13px;border-radius:7px;text-decoration:none;color:var(--muted);
  font:400 .78rem/1 var(--sans);border:1px solid transparent}
.room:hover{color:var(--gold-b);background:rgba(117,80,36,.12)}
.room.on{color:var(--gold-b);border-color:var(--line-2);
  background:linear-gradient(180deg,rgba(117,80,36,.3),rgba(117,80,36,.08))}
.conn{margin-left:auto;display:flex;align-items:center;gap:14px;flex-wrap:wrap;z-index:1}
/* A LOCAL SCRIM, because a global overlay cannot solve this one. The band's art is anchored
   `right center`, so the wider the viewport the further the lit subject slides underneath this
   block -- measured on the league band at 4.59:1 at 1280px decaying to 4.40:1 at 2560px, i.e.
   passing the 4.5 floor on the sizes I happened to test and failing on a wide monitor. Darkening
   the whole band enough to fix that erases the art everywhere else; the fix belongs where the
   text is. Soft-edged so it never reads as a box. */
.conn::before{content:"";position:absolute;inset:-14px -10px -14px -26px;z-index:-1;
  background:radial-gradient(ellipse at 62% 50%,rgba(11,11,13,.97) 0%,rgba(11,11,13,.88) 55%,
    rgba(11,11,13,0) 84%);pointer-events:none}
.who{font:400 .82rem/1.45 var(--mono);color:var(--muted);text-align:right}
.who b{color:var(--ink)}
.btn{display:inline-flex;align-items:center;gap:9px;
  font:600 .78rem/1 var(--display);letter-spacing:.17em;text-transform:uppercase;
  padding:13px 17px;min-height:44px;border-radius:6px;cursor:pointer;
  border:1px solid var(--gold);color:var(--gold-b);
  background:linear-gradient(180deg,rgba(117,80,36,.34),rgba(117,80,36,.12));
  box-shadow:0 0 0 1px rgba(0,0,0,.4),0 2px 14px rgba(117,80,36,.3)}
.btn.ghost{border-style:dashed;border-color:var(--line-2);color:var(--muted);
  background:none;box-shadow:none}
.btn:hover{border-color:var(--gold-b);box-shadow:0 0 0 1px rgba(0,0,0,.4),
  0 2px 20px rgba(249,222,153,.26)}

/* ---- the art band: a SLOT. Real asset at low opacity under a gold wash. ---- */
/* FULL-BLEED, AND BEHIND EVERYTHING. The first cut ran this at 104px, 46% wide and .22
   opacity, and four completely different candidate images rendered INDISTINGUISHABLY in it --
   which is the tell that the slot, not the art, was the constraint. A band that reduces any
   image to warm noise cannot justify the 90KB it costs; CSS would do the same for nothing.
   Widened to the viewport, 215px, .64.
   The z-index is load-bearing: at full height the band covered the room tabs and the first
   panel's heading and washed them out. It sits at 0 and every content block is lifted to 2. */
.band{position:absolute;width:100vw;left:50%;transform:translateX(-50%);
  inset-block:-18px auto;height:215px;overflow:hidden;pointer-events:none;z-index:0}
.bandart{position:absolute;inset:0;background-size:cover;background-position:right center;
  opacity:.64;filter:saturate(.62);
  mask-image:linear-gradient(90deg,transparent 0%,#000 36%,#000)}
.band::after{content:"";position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(11,11,13,.28),rgba(11,11,13,.8) 58%,var(--bg) 97%)}
.wrap{position:relative}
.crestmark,.rooms,.conn,.shell,.hr,.foot,.verdict{position:relative;z-index:2}

/* ---- a fading gold hairline, the brief's own rule ---- */
.hr{height:1px;border:0;margin:10px 0 20px;
  background:linear-gradient(90deg,rgba(117,80,36,.42),rgba(117,80,36,.05))}

/* ---- two rails: standing state on the left, the leagues on the right ---- */
.shell{display:grid;grid-template-columns:21.5rem 1fr;gap:22px;align-items:start}
.panel{border:1px solid var(--line);border-radius:9px;
  background:linear-gradient(180deg,var(--surface),var(--surface-2));overflow:hidden}
.panel+.panel{margin-top:18px}
.phead{display:flex;align-items:center;gap:11px;padding:16px 19px 0;color:var(--gold)}
.phead h2{font:400 1.02rem/1.25 var(--display);letter-spacing:.1em;text-transform:uppercase;
  color:var(--gold-b);margin:0}
.pbody{padding:13px 19px 19px}
.pbody p.sub{margin:0 0 15px;color:var(--dim);font-size:.83rem;line-height:1.55}

/* ---- the verdict: a COUNT in a shield, never a grade ---- */
.verdict{display:grid;grid-template-columns:auto 1fr;gap:24px;align-items:center;
  padding:20px 26px 20px 20px;border:1px solid var(--line-2);border-radius:9px;
  background:linear-gradient(180deg,var(--surface),var(--surface-2));
  overflow:hidden;position:relative}
.verdict::before{content:"";position:absolute;inset:0;pointer-events:none;
  background:repeating-linear-gradient(135deg,transparent 0 5px,rgba(176,162,138,.05) 5px 6px);
  mask-image:linear-gradient(105deg,#000,transparent 62%)}
.crest{position:relative;display:flex;align-items:center;justify-content:center;
  color:var(--line-2)}
.crest .shield{display:block}
/* The empty state's wyrm. `screen` over a near-black ground, so the image's own void
   contributes nothing and no alpha channel is shipped. Sits behind the lede, which is capped
   at 64ch and therefore never reaches it. */
.wyrmmark{position:absolute;right:26px;top:50%;transform:translateY(-50%);
  height:calc(100% - 34px);aspect-ratio:1/.98;background-size:contain;
  background-repeat:no-repeat;background-position:center;mix-blend-mode:screen;
  opacity:.95;pointer-events:none;z-index:0}
/* The verdict card is sized by its text on every other page. The empty state has one short
   lede, so the card collapses to a height that crops the coil in half -- and a coil cropped in
   half stops reading as a dragon and becomes texture. The empty state gets its own floor. */
.verdict.empty{min-height:290px;padding-right:330px}
.verdict.empty .vtext{max-width:46ch}
@media (max-width:980px){.wyrmmark{display:none}.verdict.empty{min-height:0;padding-right:26px}
  .verdict.empty .vtext{max-width:64ch}}
.laurel{position:absolute;top:50%;transform:translateY(-50%)}
.laurel.l{left:-6px}
.laurel.r{right:-6px;transform:translateY(-50%) scaleX(-1)}
.tally{position:absolute;margin:0;font:600 3.4rem/1 var(--mono);color:var(--gold-b);
  letter-spacing:-.03em;font-variant-numeric:tabular-nums;white-space:nowrap;
  text-shadow:0 0 26px rgba(249,222,153,.3)}
.tally s{font-size:1.25rem;color:var(--dim);text-decoration:none;margin-left:2px}
.verdict h1{font:400 1.56rem/1.22 var(--display);color:var(--gold-b);margin:0 0 8px;
  position:relative}
.verdict .vtext p{margin:0;color:var(--muted);font-size:.89rem;position:relative;max-width:64ch}

/* ---- section heads: glyph, label, glowing rule ---- */
.sechead{display:flex;align-items:center;gap:11px;margin:26px 0 7px;color:var(--gold)}
.eyebrow{font:600 .8rem/1 var(--display);letter-spacing:.22em;text-transform:uppercase;
  color:var(--gold);margin:0;white-space:nowrap}
.rule{flex:1;height:1px;background:linear-gradient(90deg,rgba(117,80,36,.5),
  rgba(249,222,153,.14) 30%,rgba(117,80,36,.03))}
.snote{margin:0 0 11px;color:var(--dim);font-size:.84rem;max-width:72ch;line-height:1.55}

/* ---- THE LIST ---- */
.leagues{border:1px solid var(--line);border-radius:9px;overflow:hidden;
  background:linear-gradient(180deg,var(--surface),var(--surface-2))}
.lrow{display:grid;grid-template-columns:4px 12rem 1fr auto;gap:0 16px;align-items:center;
  border-bottom:1px solid var(--line)}
.lrow:last-child{border-bottom:0}
.lrow:hover{background:rgba(117,80,36,.1)}
.rail{align-self:stretch}
.lrow.hole .rail{background:linear-gradient(180deg,var(--gold-b),var(--gold))}
.lrow.bye .rail{background:var(--gold)}
.lrow.thin .rail{background:var(--tie-b)}
.lrow.quiet .rail{background:var(--status-ok);opacity:.5}
.lid{padding:13px 0 13px 16px;text-decoration:none;display:block;min-height:44px}
.lname{font:400 1rem/1.25 var(--sans);color:var(--ink);margin:0}
.lmeta{font:400 .76rem/1.4 var(--mono);color:var(--dim);margin:3px 0 0}
.lclaim{padding:13px 0;display:flex;align-items:center;gap:9px;flex-wrap:wrap;min-width:0}
.lclaim .txt{font-size:.9rem;color:var(--muted)}
.lclaim .txt b{color:var(--ink);font-family:var(--mono);font-weight:600;font-size:.85rem}
.more{font:400 .75rem/1 var(--display);letter-spacing:.14em;text-transform:uppercase;
  color:var(--dim)}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block;flex:0 0 auto}
.dot.bye{background:var(--gold)}
.dot.hole{background:var(--gold-b)}
.ok{color:var(--status-ok);display:inline-flex;vertical-align:-3px}
.off{color:var(--dim)}
.lacts{display:flex;align-items:center;gap:3px;padding-right:11px}
.act,.go{min-width:44px;min-height:44px;display:grid;place-items:center;border:0;background:none;
  color:var(--dim);cursor:pointer;font-size:1.05rem;text-decoration:none;border-radius:5px}
.act:hover,.go:hover{color:var(--gold-b);background:rgba(117,80,36,.18)}
.go{font-size:1.35rem}

/* ---- popovers: a popout, never inline disclosure ---- */
.pop{border:1px solid var(--line-2);border-radius:9px;padding:19px 21px;max-width:28rem;
  background:linear-gradient(180deg,var(--surface),var(--surface-2));color:var(--ink);
  box-shadow:0 18px 60px rgba(0,0,0,.66)}
.pop::backdrop{background:rgba(0,0,0,.64)}
.popttl{font:400 1.1rem/1.2 var(--sans);margin:0 0 3px}
.popmeta{font:400 .76rem/1.45 var(--mono);color:var(--dim);margin:0 0 15px}
.pact{display:flex;align-items:center;gap:10px;width:100%;text-align:left;min-height:44px;
  margin:0 0 2px;cursor:pointer;font:600 .76rem/1 var(--display);letter-spacing:.15em;
  text-transform:uppercase;padding:14px 15px;border-radius:6px;border:1px solid var(--line-2);
  color:var(--gold-b);background:linear-gradient(180deg,rgba(117,80,36,.24),rgba(117,80,36,.08))}
.pact.danger{color:var(--tie-b);border-color:rgba(176,80,70,.42)}
.pcost{margin:0 0 14px;font-size:.8rem;color:var(--dim);line-height:1.55}

/* ---- the set-up commands ---- */
.commands{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.cmd{display:flex;flex-direction:column;align-items:flex-start;gap:9px;text-align:left;
  min-height:44px;padding:16px 17px;cursor:pointer;border-radius:8px;
  border:1px solid var(--line-2);color:var(--gold-b);
  font:600 .8rem/1.2 var(--display);letter-spacing:.14em;text-transform:uppercase;
  background:linear-gradient(180deg,var(--surface),var(--surface-2))}
.cmd:hover{border-color:var(--gold);box-shadow:0 0 22px rgba(117,80,36,.3)}
.cmd s{display:block;text-decoration:none;color:var(--dim);
  font:400 .78rem/1.35 var(--mono);letter-spacing:0;text-transform:none}

/* ---- field rows ---- */
.field{display:flex;gap:8px;margin:0 0 7px;flex-wrap:wrap}
.field input{flex:1 1 9rem;min-width:0;min-height:44px;padding:11px 13px;border-radius:6px;
  border:1px solid var(--line-2);background:rgba(0,0,0,.34);color:var(--ink);
  font:400 .88rem/1 var(--mono)}
.field input::placeholder{color:var(--dim)}
.hint{margin:0 0 16px;font-size:.79rem;color:var(--dim);line-height:1.55}
.hint:last-child{margin-bottom:0}
.or{display:flex;align-items:center;gap:12px;margin:14px 0;color:var(--dim);
  font:400 .78rem/1 var(--display);letter-spacing:.2em;text-transform:uppercase}
.or::before,.or::after{content:"";flex:1;height:1px;background:var(--line)}

.crow{display:grid;grid-template-columns:auto 1fr auto;gap:11px;align-items:center;
  padding:11px 0;border-bottom:1px solid var(--line);font-size:.88rem}
.crow:last-of-type{border-bottom:0}
.ckey{font:400 .76rem/1 var(--mono);color:var(--dim);overflow:hidden;text-overflow:ellipsis}
.cstate{font:400 .8rem/1 var(--mono);white-space:nowrap}
.cstate.on{color:var(--status-ok)}
.cstate.no{color:var(--dim)}
.srow{display:grid;grid-template-columns:auto 1fr auto;gap:11px;align-items:center;
  padding:10px 0;border-bottom:1px solid var(--line);font-size:.85rem;color:var(--muted)}
.srow:last-of-type{border-bottom:0}
.sage{font:400 .8rem/1 var(--mono);color:var(--dim);white-space:nowrap}
.sage b{color:var(--ink)}

.absent{color:var(--dim);border-bottom:1px dotted var(--line-2);cursor:help}
.stamp{display:inline-flex;align-items:center;gap:7px;font:400 .75rem/1 var(--mono);
  letter-spacing:.08em;text-transform:uppercase;color:var(--gold);
  border:1px dashed var(--line-2);border-radius:4px;padding:6px 9px}
.standin{display:flex;gap:13px;align-items:flex-start;margin:11px 0 0;color:var(--dim);
  font-size:.82rem;line-height:1.55}
.foot{margin-top:30px;padding-top:17px;border-top:1px solid var(--line);
  color:var(--dim);font-size:.8rem;line-height:1.65}

/* Below ~1200 the top bar WRAPS: the connection block drops to a second row and lands in the
   band's bright lower half, measured at 3.40:1 where the unwrapped layout reads 5.46-7.63. The
   band is sized for a one-row header, so when the header stops being one row the band stops
   covering it. Found by reading the geometry at 1100 -- .conn at y=106 under a band running
   -18..197 -- rather than by tuning opacity until the number moved. */
@media (max-width:1200px){.band{height:124px}.bandart{opacity:.46}}
@media (max-width:1080px){
  .shell{grid-template-columns:1fr}
  .band{width:40%}
  .commands{grid-template-columns:1fr 1fr}
}
@media (max-width:720px){
  /* THE GLYPHS BECOME THE BUTTONS. The owner's call, and the measurements back it: the glyph
     is legible at 19px (`#349h` rendered the set down to it) while the LABEL is what overflows
     a 390px bar -- six labelled tabs cannot fit, six 48px glyph targets can, with room spare.
     The label is not deleted, it moves to `aria-label`/`title`, so the tab is still named for a
     screen reader and on a long press. Targets stay at 48px, over the 44px floor. */
  .room{min-width:48px;width:48px;height:48px;padding:0;place-items:center;display:grid;
    font-size:0;gap:0}
  .room .ic{width:22px;height:22px}
  .rooms{gap:6px;justify-content:space-between;width:100%}
  .rooms::before{inset:-8px -12px}
  .band{display:none}
  .commands{grid-template-columns:1fr}
  .lrow{grid-template-columns:4px 1fr auto;row-gap:0}
  .lclaim{grid-column:2/4;padding:0 0 13px}
  .verdict{grid-template-columns:1fr;gap:14px;justify-items:center;text-align:center}
  .rooms{order:3;width:100%;justify-content:space-between}
  .conn{margin-left:0}
}
"""


# ---------------------------------------------------------------------------
# the page

#: THE FIVE ROOMS AND THE DOCK, from the owner's settled ruling -- NOT the reference mockup's
#: `Home / Leagues / Keep / Tools / Settings`, which is a different information architecture
#: nobody has ruled on. Using the settled names keeps this page honest; whether a landing page
#: should carry room tabs AT ALL is a real open question, because no league is selected here and
#: every room is per-league. Recorded in NOTES rather than decided by a mockup.
ROOMS = (("layers", "Matchup"), ("swap", "Roster"), ("chart", "Draft Room"),
         ("crown", "League"), ("search", "Import Audit"))


def topbar(sl=None, uri=None, home=True, active=None):
    """The shared top bar. `active` names the ROOM that is current, for the in-league pages.

    Default `None` keeps Home lit, which is what the landing pages want and what this rendered
    before the parameter existed -- so both landing pages still rebuild byte-identically, which
    is how this edit was checked rather than assumed.
    """
    rooms = "".join(
        f'<a class="room{" on" if label == active else ""}" title="{esc(label)}" '
        f'aria-label="{esc(label)}" '
        f'href="#{esc(label.lower().replace(" ", "-"))}">{icon(name, 19)}{esc(label)}</a>'
        for name, label in ROOMS)
    conn = ""
    if sl:
        conn = (f'<div class="conn"><p class="who">Sleeper <b>{esc(sl["username"])}</b><br>'
                f'synced {esc(sl["synced_at_human"])}</p>'
                f'<button class="btn">{icon("refresh", 17)}Resync all</button></div>')
    return f"""
  <header class="top">
    {hero_band(uri)}
    <div class="crestmark">{emblem()}<p class="word">Gold Wyrm<b>Dynasty</b></p></div>
    <nav class="rooms">
      <a class="room{' on' if home and not active else ''}" title="Home" aria-label="Home" href="#home">{icon("disk", 19)}Home</a>
      {rooms}
    </nav>
    {conn}
  </header>
  <hr class="hr">"""


def head(title):
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap">
<style>{ds.root_css_block()}{font_vars()}{ds.position_pill_css_block()}{css()}</style>
</head><body>
<div class="wrap">"""


def panel(ic, title, body):
    return (f'<section class="panel"><div class="phead">{icon(ic, 19)}<h2>{esc(title)}</h2></div>'
            f'<div class="pbody">{body}</div></section>')


def build(fx, seat_paths) -> str:
    arch = set(fx.get("archived_seats") or [])
    attention, quiet, archived = league_rows(seat_paths, arch)
    total = len(attention) + len(quiet)
    sl, left = fx["sleeper"], (fx.get("left_leagues") or [])
    uri = banner_data_uri()

    configured = set(fx.get("configured_credentials") or [])
    n_prov = len(providers.ids())
    n_on = sum(1 for pid in providers.ids() if providers.get(pid).key_field in configured)
    dated = [s["days"] for s in fx["sources"] if s["days"] is not None]
    oldest = f"{max(dated)}d" if dated else "&mdash;"

    add_body = f"""
  <p class="sub">Two different things, so they are two different fields.</p>
  <div class="field">
    <input type="text" placeholder="Sleeper league ID" aria-label="Sleeper league ID">
    <button class="btn">{icon('plus', 17)}Add</button>
  </div>
  <p class="hint">Adds <b>one</b> league by its Sleeper ID and leaves the rest of the list
     alone. For a league the account lookup does not return.</p>
  <div class="or">or</div>
  <div class="field">
    <input type="text" placeholder="Sleeper username" aria-label="Sleeper username"
           value="{esc(sl['username'])}">
    <button class="btn ghost">{icon('user', 17)}Sync account</button>
  </div>
  <p class="hint">Looks up the account and <b>replaces</b> the whole list with the leagues it
     returns &mdash; that is how a league you have left stops appearing. No password: Sleeper
     does not use one.</p>"""

    manage_body = f"""
  <p class="sub">Archiving and ordering are local conveniences. Sleeper has no concept of
     either, so nothing here changes anything on Sleeper.</p>
  <div class="crow">{icon('archive', 17)}<span>Archived <span class="ckey">hidden from the
     list</span></span><span class="cstate {'on' if archived else 'no'}">{len(archived)}</span></div>
  <div class="crow">{icon('swap', 17)}<span>You left <span class="ckey">{esc(left[0]['name'])
     if left else 'none detected'}</span></span>
     <span class="cstate {'on' if left else 'no'}">{len(left)}</span></div>
  <p class="hint" style="margin-top:15px">Detected by diffing Sleeper&rsquo;s league list
     against the leagues this app was tracking &mdash; left, removed, or deleted.</p>
  <button class="btn ghost" popovertarget="pop-delete">What deleting removes</button>
  <div popover id="pop-delete" class="pop">
    <p class="popttl">Deleting a league</p>
    <p class="popmeta">local purge &middot; asks first</p>
    <p class="pcost">It removes, for that league only:</p>
    <ul class="pcost" style="padding-left:18px;margin-bottom:14px">
      {''.join(f'<li>{c}</li>' for c in DELETE_COSTS)}</ul>
    <p class="pcost"><b>{DELETE_NOT}</b></p>
  </div>"""

    conn_body = f"""
  <p class="sub">Sleeper is where the leagues come from. Everything on this page is computed
     without a model provider &mdash; they are optional, and only the assistant uses them.</p>
  <div class="crow">{icon('user', 17)}<span>Sleeper <span class="ckey">{esc(sl['username'])}
     </span></span><span class="cstate on">{icon('check', 15, 'ok')} connected</span></div>
  <div class="sechead" style="margin:17px 0 2px">{icon('link', 17)}
    <p class="eyebrow">Model providers</p><span class="rule"></span></div>
  <p class="sub" style="margin-bottom:6px">Listed from the registry, not written into this
     page. A provider registered in the app appears here on its own.</p>
  {provider_rows(configured)}
  <p class="hint" style="margin-top:15px">Keys are read from the environment or pasted as a
     <code>.env</code> block. This page never shows a key&rsquo;s value, only whether one is
     set, and the name beside each is the credential it travels under.</p>"""

    data_body = f"""
  <p class="sub">What a resync refreshes, and how old each source is now.</p>
  {source_rows(fx['sources'])}
  <p class="hint" style="margin-top:15px">A source with no date is not loaded. It renders as an
     em dash carrying its reason, never as a zero.</p>"""

    quiet_note = ("These were checked and nothing came back. They are listed, not hidden &mdash; "
                  "a league missing from the page would read as an error, not as calm.")

    return f"""{head('Your Leagues')}
{topbar(sl, uri)}

  <div class="shell">
    <div class="rail-left">
      {panel('link', 'Connections', conn_body)}
      {panel('disk', 'On disk', data_body)}
    </div>

    <div class="rail-main">
      <section class="verdict">
        {crest(str(len(attention)), str(total))}
        <div class="vtext">
          <h1>{len(attention)} of your {total} leagues want something.</h1>
          <p>Ordered by what KIND of thing is open, never by its size &mdash; a hole is a hole
             in any league, but two leagues&rsquo; figures are different units wearing one
             label. Open a league for the detail; this page only says which.</p>
        </div>
      </section>
      <p class="standin"><span class="stamp">{icon('layers', 14)}Constructed</span>
         <span>{STANDIN}.</span></p>

      {sechead('crown', 'Needs you')}
      <div class="leagues">{''.join(row_html(r, i) for i, r in enumerate(attention))}</div>

      {sechead('check', 'Nothing open', quiet_note)}
      <div class="leagues">{''.join(row_html(r, i) for i, r in enumerate(quiet))}</div>

      {sechead('archive', 'Archived', 'Hidden from the list above. Still synced.') if archived else ''}
      {'<div class="leagues">' + ''.join(row_html(r, i) for i, r in enumerate(archived)) + '</div>' if archived else ''}

      {sechead('gear', 'Set up')}
      <div class="commands">
        <button class="cmd" popovertarget="pop-add">{icon('plus', 21)}Add a league
          <s>one by ID, or a whole account</s></button>
        <button class="cmd" popovertarget="pop-manage">{icon('layers', 21)}Manage
          <s>{len(archived)} archived &middot; {len(left)} left</s></button>
        <button class="cmd" popovertarget="pop-conn">{icon('link', 21)}Connections
          <s>Sleeper &middot; {n_on} of {n_prov} providers</s></button>
        <button class="cmd" popovertarget="pop-data">{icon('disk', 21)}Data
          <s>oldest source {oldest}</s></button>
      </div>
      <div popover id="pop-add" class="pop">{add_body}</div>
      <div popover id="pop-manage" class="pop">{manage_body}</div>
      <div popover id="pop-conn" class="pop">{conn_body}</div>
      <div popover id="pop-data" class="pop">{data_body}</div>
    </div>
  </div>

  <p class="foot">
    Claim detail lives inside a league, not here. This page answers one question &mdash; which
    league wants me &mdash; and carries the verbs that change the set.<br>
    A count of real things, never a score. No portfolio grade, no worst-league ranking and no
    cross-league total exists to show.
  </p>
</div>
</body></html>"""


def build_unsynced(fx) -> str:
    """THE FIRST SCREEN, and the one a new user actually meets.

    `front_page.compose_unsynced` already composes this state with an `action` and an
    `action_cost`; this draws that shape rather than inventing a second empty state.

    NOTE THE LAYOUT DIFFERS FROM THE SYNCED PAGE ON PURPOSE. The reference mockup put the
    "No leagues yet / Connect to Sleeper" column BESIDE a list of ten synced leagues. As a way
    of showing both pages at once that is fine; as a UI it is a contradiction -- those two
    states are mutually exclusive, and a user who has synced can never see the connect panel.
    So the connect rail exists only here, and the synced page gives that column to standing
    state instead.
    """
    uri = banner_data_uri()
    connect_body = f"""
  <p class="sub">Either route works, and both can be used together later.</p>
  <div class="field">
    <input type="text" placeholder="Sleeper username" aria-label="Sleeper username">
    <button class="btn">{icon('user', 17)}Sync account</button>
  </div>
  <p class="hint">Pulls every league on the account. No password: Sleeper does not use one.</p>
  <div class="or">or</div>
  <div class="field">
    <input type="text" placeholder="Sleeper league ID" aria-label="Sleeper league ID">
    <button class="btn ghost">{icon('plus', 17)}Add one</button>
  </div>
  <p class="hint">For a league the account lookup does not return.</p>"""

    disk_body = f"""
  <p class="sub">Loaded now, before any sync. These price the board; the sync adds your
     league&rsquo;s own rules.</p>
  {source_rows(fx['sources'])}
  <p class="hint" style="margin-top:15px"><b>Until you sync,</b> the board cannot price to a
     league&rsquo;s scoring: the player universe and the league-scored projections both arrive
     with the sync.</p>"""

    return f"""{head('Connect Sleeper')}
{topbar(None, uri)}

  <div class="shell">
    <div class="rail-left">
      {panel('link', 'Connect to Sleeper', connect_body)}
    </div>
    <div class="rail-main">
      <section class="verdict empty">
        {wyrm_mark()}
        {crest('0', '0')}
        <div class="vtext">
          <h1>No leagues yet.</h1>
          <p>Sleeper needs a username and no password. Syncing an account pulls every league it
             returns; a single league can be added by its ID instead. Nothing on this page is
             computed until one of those happens.</p>
        </div>
      </section>
      {sechead('disk', 'What is already on disk')}
      {panel('chart', 'Sources', disk_body)}
    </div>
  </div>

  <p class="foot">This is the state the app is in before a username is entered &mdash; composed
    from the same freshness rows the synced page reports, so the two cannot disagree.</p>
</div>
</body></html>"""


def main(argv=None):
    fx = json.loads(FIXTURE.read_text())
    seats = glob.glob(SEATS)
    if not seats:
        raise SystemExit(f"no seat fixtures matched {SEATS}")

    # BUILD-TIME GATES. A measured floor that fails the build is worth more than a measured
    # floor in a report nobody re-runs -- but only if it reads THIS page. Each takes its
    # subject as an argument for exactly that reason; see their docstrings.
    assert_marks_are_visible()
    assert_type_floor(css())
    assert_vars_resolve(ds.root_css_block(), font_vars(), ds.position_pill_css_block(), css())

    OUT.write_text(build(fx, seats))
    OUT_EMPTY.write_text(build_unsynced(fx))
    for p in (OUT, OUT_EMPTY):
        print(f"{p}  {len(p.read_text()):,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
