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
# CSS


def css():
    return """
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--ink)}
body{font:400 .95rem/1.55 var(--sans);-webkit-text-size-adjust:100%}
.wrap{max-width:68rem;margin:0 auto;padding:0 20px 72px}
a{color:inherit}

/* ---- top: identity on the left, the CONNECTION and its one verb on the right ---- */
.top{display:flex;align-items:center;gap:20px;padding:18px 0;flex-wrap:wrap;
  border-bottom:1px solid var(--line)}
.crest{display:flex;align-items:center;gap:12px}
.word{font:600 1.3rem/1 var(--display);letter-spacing:.11em;text-transform:uppercase;margin:0;
  background:linear-gradient(176deg,#755024 0%,#ba9561 38%,#f9de99 68%,#fff4ce 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent}
.word b{display:block;font-size:.75rem;letter-spacing:.42em;font-weight:400;margin-top:5px}
.conn{margin-left:auto;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.who{font:400 .82rem/1.4 var(--mono);color:var(--muted);text-align:right}
.who b{color:var(--ink)}
.btn{font:600 .78rem/1 var(--display);letter-spacing:.17em;text-transform:uppercase;
  padding:13px 17px;min-height:44px;border-radius:5px;cursor:pointer;
  border:1px solid var(--gold);color:var(--gold-b);
  background:linear-gradient(180deg,rgba(117,80,36,.3),rgba(117,80,36,.12))}
.btn.ghost{border-style:dashed;border-color:var(--line-2);color:var(--muted);background:none}
.btn:hover{border-color:var(--gold-b)}

/* ---- the count. A COUNT, never a grade. ---- */
.verdict{display:grid;grid-template-columns:auto 1fr;gap:26px;align-items:center;
  margin:26px 0 8px;padding:22px 26px;border:1px solid var(--line-2);border-radius:6px;
  background:linear-gradient(180deg,var(--surface),var(--surface-2));overflow:hidden;position:relative}
.verdict::before{content:"";position:absolute;inset:0 auto 0 0;width:160px;pointer-events:none;
  background:repeating-linear-gradient(135deg,transparent 0 4px,rgba(176,162,138,.06) 4px 5px);
  mask-image:linear-gradient(90deg,#000,transparent)}
.tally{font:600 3.4rem/1 var(--mono);color:var(--gold-b);letter-spacing:-.03em;position:relative;
  font-variant-numeric:tabular-nums;white-space:nowrap}
.tally s{font-size:1.4rem;color:var(--dim);text-decoration:none;margin-left:3px}
.verdict h1{font:400 1.6rem/1.2 var(--display);color:var(--gold-b);margin:0 0 7px;position:relative}
.verdict div p{margin:0;color:var(--muted);font-size:.89rem;position:relative;max-width:60ch}

.eyebrow{font:600 .78rem/1 var(--display);letter-spacing:.22em;text-transform:uppercase;
  color:var(--gold);margin:30px 0 9px}
.bnote{margin:0 0 12px;color:var(--dim);font-size:.84rem;max-width:68ch}

/* ---- THE LIST. One line per league: that is what makes twenty scannable. ---- */
.leagues{border:1px solid var(--line);border-radius:6px;overflow:hidden;
  background:linear-gradient(180deg,var(--surface),var(--surface-2))}
.lrow{display:grid;grid-template-columns:4px 13rem 1fr auto;gap:0 18px;align-items:center;
  border-bottom:1px solid var(--line)}
.lrow:last-child{border-bottom:0}
.lrow:hover{background:rgba(117,80,36,.09)}
.rail{align-self:stretch}
.lrow.hole .rail{background:var(--gold-b)}
.lrow.bye .rail{background:var(--gold)}
.lrow.thin .rail{background:var(--tie-b)}
.lrow.quiet .rail{background:var(--status-ok);opacity:.45}
.lid{padding:15px 0 15px 17px;text-decoration:none;display:block;min-height:44px}
.lname{font:400 1rem/1.25 var(--sans);color:var(--ink);margin:0}
.lmeta{font:400 .76rem/1.4 var(--mono);color:var(--dim);margin:3px 0 0}
.lclaim{padding:15px 0;display:flex;align-items:center;gap:9px;flex-wrap:wrap;min-width:0}
.lclaim .txt{font-size:.9rem;color:var(--muted)}
.lclaim .txt b{color:var(--ink);font-family:var(--mono);font-weight:600;font-size:.85rem}
.more{font:400 .75rem/1 var(--display);letter-spacing:.14em;text-transform:uppercase;color:var(--dim)}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block;flex:0 0 auto}
.dot.bye{background:var(--gold)}
.dot.hole{background:var(--gold-b)}
.ok{color:var(--status-ok)}
.off{color:var(--dim)}
.lacts{display:flex;align-items:center;gap:4px;padding-right:12px}
.act,.go{min-width:44px;min-height:44px;display:grid;place-items:center;border:0;background:none;
  color:var(--dim);cursor:pointer;font-size:1.1rem;text-decoration:none;border-radius:4px}
.act:hover,.go:hover{color:var(--gold-b);background:rgba(117,80,36,.16)}
.go{font-size:1.4rem}

/* ---- popovers, per the owner's ruling: a popout, never inline disclosure ---- */
/* ---- the set-up half, collapsed to commands. The owner's question, and the answer:
   the triage list is why you opened the page; add/manage/connect are monthly. Four
   always-open cards spent half the page height on the least-used half. ---- */
.commands{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.cmd{text-align:left;min-height:44px;padding:15px 17px;cursor:pointer;border-radius:6px;
  border:1px solid var(--line-2);color:var(--gold-b);
  font:600 .8rem/1.2 var(--display);letter-spacing:.14em;text-transform:uppercase;
  background:linear-gradient(180deg,var(--surface),var(--surface-2))}
.cmd:hover{border-color:var(--gold)}
.cmd s{display:block;margin-top:7px;text-decoration:none;color:var(--dim);
  font:400 .78rem/1.3 var(--mono);letter-spacing:0;text-transform:none}
.pop.wide{max-width:34rem;padding:0;border:0;background:none}
.pop.wide .card{margin:0}
.pop{border:1px solid var(--line-2);border-radius:7px;padding:18px 20px;max-width:27rem;
  background:linear-gradient(180deg,var(--surface),var(--surface-2));color:var(--ink)}
.pop::backdrop{background:rgba(0,0,0,.62)}
.popttl{font:400 1.1rem/1.2 var(--sans);margin:0 0 3px}
.popmeta{font:400 .76rem/1.4 var(--mono);color:var(--dim);margin:0 0 15px}
.pact{display:block;width:100%;text-align:left;min-height:44px;margin:0 0 2px;cursor:pointer;
  font:600 .76rem/1 var(--display);letter-spacing:.15em;text-transform:uppercase;
  padding:14px 15px;border-radius:5px;border:1px solid var(--line-2);color:var(--gold-b);
  background:linear-gradient(180deg,rgba(117,80,36,.22),rgba(117,80,36,.08))}
.pact.danger{color:var(--tie-b);border-color:rgba(176,80,70,.4)}
.pcost{margin:0 0 14px;font-size:.8rem;color:var(--dim);line-height:1.5}

/* ---- the operating bands: add, manage, connect ---- */
.cols{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.card{border:1px solid var(--line);border-radius:6px;padding:20px 22px;
  background:linear-gradient(180deg,var(--surface),var(--surface-2))}
.card h2{font:400 1.05rem/1.25 var(--sans);color:var(--ink);margin:0 0 4px}
.card p.sub{margin:0 0 16px;color:var(--dim);font-size:.82rem;line-height:1.5}
.field{display:flex;gap:8px;margin:0 0 7px;flex-wrap:wrap}
.field input{flex:1 1 11rem;min-height:44px;padding:11px 13px;border-radius:5px;
  border:1px solid var(--line-2);background:rgba(0,0,0,.3);color:var(--ink);
  font:400 .88rem/1 var(--mono)}
.field input::placeholder{color:var(--dim)}
.hint{margin:0 0 18px;font-size:.79rem;color:var(--dim);line-height:1.5}
.hint:last-child{margin-bottom:0}

.crow{display:grid;grid-template-columns:7rem 1fr auto;gap:12px;align-items:center;
  padding:11px 0;border-bottom:1px solid var(--line)}
.crow:last-of-type{border-bottom:0}
.cname{font-size:.9rem}
.ckey{font:400 .76rem/1 var(--mono);color:var(--dim)}
.cstate{font:400 .8rem/1 var(--mono);white-space:nowrap}
.cstate.on{color:var(--status-ok)}
.cstate.no{color:var(--dim)}

.srow{display:flex;justify-content:space-between;gap:14px;padding:9px 0;
  border-bottom:1px solid var(--line);font-size:.84rem;color:var(--muted)}
.srow:last-of-type{border-bottom:0}
.sage{font:400 .8rem/1 var(--mono);color:var(--dim);white-space:nowrap}
.sage b{color:var(--ink)}

.absent{color:var(--dim);border-bottom:1px dotted var(--line-2);cursor:help}
.stamp{display:inline-block;font:400 .75rem/1 var(--mono);letter-spacing:.08em;
  text-transform:uppercase;color:var(--gold);border:1px dashed var(--line-2);
  border-radius:3px;padding:4px 7px}
.foot{margin-top:34px;padding-top:18px;border-top:1px solid var(--line);
  color:var(--dim);font-size:.8rem;line-height:1.6}

@media (max-width:860px){
  .cols{grid-template-columns:1fr}
  .commands{grid-template-columns:1fr 1fr}
  .lrow{grid-template-columns:4px 1fr auto;row-gap:0}
  .lclaim{grid-column:2/4;padding:0 0 15px}
  .verdict{grid-template-columns:1fr;gap:12px}
  .tally{font-size:2.6rem}
}
"""


# ---------------------------------------------------------------------------
# the page


def build(fx, seat_paths) -> str:
    arch = set(fx.get("archived_seats") or [])
    attention, quiet, archived = league_rows(seat_paths, arch)
    total = len(attention) + len(quiet)
    sl = fx["sleeper"]
    left = fx.get("left_leagues") or []

    add_card = f"""
<div class="card">
  <h2>Add a league</h2>
  <p class="sub">Two different things, so they are two different fields.</p>
  <div class="field">
    <input type="text" placeholder="Sleeper league ID" aria-label="Sleeper league ID">
    <button class="btn">Add</button>
  </div>
  <p class="hint">Adds <b>one</b> league by its Sleeper ID and leaves the rest of the list
     alone. Use this for a league the account lookup does not return.</p>
  <div class="field">
    <input type="text" placeholder="Sleeper username" aria-label="Sleeper username"
           value="{esc(sl['username'])}">
    <button class="btn ghost">Sync account</button>
  </div>
  <p class="hint">Looks up the account and <b>replaces</b> the whole list with the leagues it
     returns &mdash; that is how a league you have left stops appearing. No password: Sleeper
     does not use one.</p>
</div>"""

    manage_card = f"""
<div class="card">
  <h2>Manage</h2>
  <p class="sub">Archiving and ordering are local conveniences. Sleeper has no concept of
     either, so nothing here changes anything on Sleeper.</p>
  <div class="crow">
    <span class="cname">Archived</span>
    <span class="ckey">hidden from the list</span>
    <span class="cstate {'on' if archived else 'no'}">{len(archived)}</span>
  </div>
  <div class="crow">
    <span class="cname">You left</span>
    <span class="ckey">{esc(left[0]['name']) if left else 'none detected'}</span>
    <span class="cstate {'on' if left else 'no'}">{len(left)}</span>
  </div>
  <p class="hint" style="margin-top:16px">Detected by diffing Sleeper&rsquo;s league list
     against the leagues this app was tracking &mdash; left, removed, or the league was deleted.</p>
  <button class="btn ghost" popovertarget="pop-delete">What deleting removes</button>
  <div popover id="pop-delete" class="pop">
    <p class="popttl">Deleting a league</p>
    <p class="popmeta">local purge &middot; asks first</p>
    <p class="pcost">It removes, for that league only:</p>
    <ul class="pcost" style="padding-left:18px;margin-bottom:14px">
      {''.join(f'<li>{c}</li>' for c in DELETE_COSTS)}
    </ul>
    <p class="pcost"><b>{DELETE_NOT}</b></p>
  </div>
</div>"""

    conn_card = f"""
<div class="card">
  <h2>Connections</h2>
  <p class="sub">Sleeper is where the leagues come from. Everything on this page is computed
     without a model provider &mdash; they are optional, and only the assistant uses them.</p>
  <div class="crow">
    <span class="cname">Sleeper</span>
    <code class="ckey">{esc(sl['username'])}</code>
    <span class="cstate on"><span class="ok">&#10003;</span> connected</span>
  </div>

  <p class="eyebrow" style="margin:20px 0 2px">Model providers</p>
  <p class="sub">Listed from the registry, not written into this page. A provider registered
     in the app appears here on its own.</p>
  {provider_rows(set(fx.get('configured_credentials') or []))}
  <p class="hint" style="margin-top:16px">Keys are read from the environment or pasted as a
     <code>.env</code> block. This page never shows a key&rsquo;s value, only whether one is
     set, and the name beside each is the credential it travels under.</p>
</div>"""

    sources_card = f"""
<div class="card">
  <h2>Data behind these rows</h2>
  <p class="sub">What a resync refreshes, and how old each source is now.</p>
  {source_rows(fx['sources'])}
  <p class="hint" style="margin-top:16px">A source with no date is not loaded. It renders as an
     em dash carrying its reason, never as a zero.</p>
</div>"""

    quiet_note = ("These were checked and nothing came back. They are listed, not hidden &mdash; "
                  "a league missing from the page would read as an error, not as calm.")

    # COLLAPSING MUST NOT SWALLOW STATE. The four set-up panels were always-open cards; folding
    # them into commands is cleaner only if the FACTS they showed at a glance survive the fold.
    # Each button therefore carries the one number its panel exists to report, so the page still
    # answers "is anything unconfigured?" without a click. A bare row of verbs would have hidden
    # that nothing is archived, or that no key is set, behind an interaction.
    configured = set(fx.get("configured_credentials") or [])
    n_prov = len(providers.ids())
    n_on = sum(1 for pid in providers.ids() if providers.get(pid).key_field in configured)
    dated = [s["days"] for s in fx["sources"] if s["days"] is not None]
    oldest = f"{max(dated)}d" if dated else "&mdash;"

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Your Leagues</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap">
<style>{ds.root_css_block()}{font_vars()}{ds.position_pill_css_block()}{css()}</style>
</head><body>
<div class="wrap">

  <header class="top">
    <div class="crest">{WYRM}<p class="word">Gold Wyrm<b>Dynasty</b></p></div>
    <div class="conn">
      <p class="who">Sleeper <b>{esc(sl['username'])}</b><br>synced {esc(sl['synced_at_human'])}</p>
      <button class="btn">Resync all</button>
    </div>
  </header>

  <section class="verdict">
    <p class="tally">{len(attention)}<s>/{total}</s></p>
    <div>
      <h1>{len(attention)} of your {total} leagues want something.</h1>
      <p>Ordered by what KIND of thing is open, never by its size &mdash; a hole is a hole in
         any league, but two leagues&rsquo; figures are different units wearing one label.
         Open a league for the detail; this page only says which.</p>
    </div>
  </section>
  <p class="bnote"><span class="stamp">Constructed</span> {STANDIN}.</p>

  {section("Needs you", None, attention)}
  {section("Nothing open", quiet_note, quiet,
           empty="Every league came back clean.")}
  {section("Archived", "Hidden from the list above. Still synced.", archived,
           empty="Nothing archived.") if archived else ""}

  <p class="eyebrow">Set up</p>
  <div class="commands">
    <button class="cmd" popovertarget="pop-add">Add a league
      <s>one by ID, or a whole account</s></button>
    <button class="cmd" popovertarget="pop-manage">Manage
      <s>{len(archived)} archived &middot; {len(left)} left</s></button>
    <button class="cmd" popovertarget="pop-conn">Connections
      <s>Sleeper &middot; {n_on} of {n_prov} providers</s></button>
    <button class="cmd" popovertarget="pop-data">Data
      <s>oldest source {oldest}</s></button>
  </div>
  <div popover id="pop-add" class="pop wide">{add_card}</div>
  <div popover id="pop-manage" class="pop wide">{manage_card}</div>
  <div popover id="pop-conn" class="pop wide">{conn_card}</div>
  <div popover id="pop-data" class="pop wide">{sources_card}</div>

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
    """
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Connect Sleeper</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap">
<style>{ds.root_css_block()}{font_vars()}{ds.position_pill_css_block()}{css()}</style>
</head><body>
<div class="wrap">
  <header class="top">
    <div class="crest">{WYRM}<p class="word">Gold Wyrm<b>Dynasty</b></p></div>
  </header>

  <section class="verdict">
    <p class="tally">0<s>/0</s></p>
    <div>
      <h1>No leagues yet.</h1>
      <p>Sleeper needs a username and no password. Syncing an account pulls every league it
         returns; a single league can be added by its ID instead.</p>
    </div>
  </section>

  <div class="cols">
    <div class="card">
      <h2>Connect</h2>
      <p class="sub">Either route works, and both can be used together later.</p>
      <div class="field">
        <input type="text" placeholder="Sleeper username" aria-label="Sleeper username">
        <button class="btn">Sync account</button>
      </div>
      <p class="hint">Pulls every league on the account.</p>
      <div class="field">
        <input type="text" placeholder="Sleeper league ID" aria-label="Sleeper league ID">
        <button class="btn ghost">Add one</button>
      </div>
      <p class="hint">For a league the account lookup does not return.</p>
    </div>
    <div class="card">
      <h2>What is already on disk</h2>
      <p class="sub">Loaded now, before any sync. These price the board; the sync adds your
         league&rsquo;s own rules.</p>
      {source_rows(fx['sources'])}
      <p class="hint" style="margin-top:16px"><b>Until you sync,</b> the board cannot price to a
         league&rsquo;s scoring: the player universe and the league-scored projections both
         arrive with the sync.</p>
    </div>
  </div>

  <p class="foot">This is the state the app is in before a username is entered &mdash; composed
    from the same freshness rows the synced page reports, so the two cannot disagree.</p>
</div>
</body></html>"""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    fx = json.loads(FIXTURE.read_text())
    seats = glob.glob(SEATS)
    if not seats:
        raise SystemExit(f"no seat fixtures matched {SEATS}")

    # BUILD-TIME GATES. A measured floor that fails the build is worth more than a measured
    # floor in a report nobody re-runs -- but only if it reads THIS page. Both of these take
    # their subject as an argument for exactly that reason; see their docstrings.
    assert_marks_are_visible()
    assert_type_floor(css())
    assert_vars_resolve(ds.root_css_block(), font_vars(), ds.position_pill_css_block(), css())
    page = build(fx, seats)
    empty = build_unsynced(fx)

    OUT.write_text(page)
    OUT_EMPTY.write_text(empty)
    for p in (OUT, OUT_EMPTY):
        print(f"{p}  {len(p.read_text()):,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
