#!/usr/bin/env python3
"""Measure whether the desktop and the phone are two sides of ONE interface.

The brief for the phone was "they need to feel like 2 sides of the same ui, since they will
be". That is an aesthetic claim, and an aesthetic claim held only in someone's head drifts.
This turns it into four comparisons a machine can run.

What it compares, and why each one is the right axis:

  FACE     The typeface carrying a role. A role set in the display face on the desktop and the
           body face on the phone is two interfaces, full stop -- no amount of matching color
           saves it. Zero tolerance.

  COLOR    The ink on a role. The two surfaces share shared.css, so a role drawn in a different
           color on the phone means a template reached past the tokens. Zero tolerance.

  CASE     text-transform and letter-spacing. An uppercase tracked label on one side and a
           sentence-case untracked one on the other reads as two different voices for the same
           word. Zero tolerance.

  SIZE     NOT zero tolerance, on purpose. A phone legitimately sets smaller type, so the
           question is not "is it the same" but "is it the same SCALE". It reports the per-role
           ratio and flags the roles whose ratio is off the surface's own dominant factor --
           a role scaled 0.72 in a surface that otherwise scales 0.86 was resized by hand.

And one lexical comparison, which is the one that actually found something:

  WORDS    The chrome vocabulary each surface draws, with the fixture's own words subtracted so
           player names and team codes drop out. A word on one side and not the other is either
           a deliberate difference (the pointer's verb: "click" against "tap") or a drift.

A role is keyed by `tag.class`, which is only meaningful BECAUSE the surfaces share a
stylesheet: the same role wears the same class on both. A role present on one side only is
reported separately and is not a divergence -- the desktop has a flip animation and the phone
has folds, and neither should grow the other's.

WHAT IT FOUND ON ITS FIRST RUN, and what that says about the instrument. Nineteen
zero-tolerance divergences across 57 shared roles -- and triaging them improved the instrument
as much as the surfaces, which is the normal outcome for a first run and worth recording rather
than quietly fixing:

  REAL, and the one this instrument exists for. `.hm`, the availability marker, is emitted by
  shared.js -- every surface calls it -- but its RULES had been left behind in the desktop
  template when the emitter was hoisted, and no phone template ever carried a copy. The desktop
  drew the marker quiet and small; the three phones drew it at their parent's full --ink and
  full size. A markup diff cannot see that, by construction. Fixed by moving the rules into
  shared.css, and confirmed by re-harvest: the desktop's three `.hm` keys UNCHANGED, the
  phone's three moved from ink/16px to muted-and-dim/13.1px.

  REAL, found by the better keys. A blanket `.ctx2 b` rule on the phone was more specific than
  the shared `.tankcap b`, so a shared caption's bold drew in mono at full ink there and in the
  body face at --muted on the desktop. The template had already carved one exception by hand
  for `.dem`; a second exception is the signal the selector is wrong.

  REAL, and a naming problem rather than a styling one. The phone reused the class `.v` -- which
  means "numeric value, mono, tabular" in `.row` and `.srow` on every surface here -- for two
  PROSE summary lines. Same name, two meanings, which is #126 in CSS form. Renamed.

  REAL, and the one that proves the two modes ask two different questions. `.dem`, the demand
  line, is emitted by shared.js and had NO rule in shared.css at all -- all four surfaces styled
  it separately, each arriving at mono-and-muted by a different route. Giving it the shared
  default it had always been missing fixed m1 and BROKE m2 and m3, whose unscoped `.ctx2 b`
  blanket then outranked the new default and pushed their demand bold to --ink. The
  desktop-against-phone report cannot see that: it compares v4 with m1, by construction.
  `moved`, which watches every surface across a change, is what caught it.

  THE INSTRUMENT'S OWN FAULT, twice. Three findings were a bare tag key collapsing unrelated
  roles (see roleKey below), and three more were letter-spacing compared in PIXELS between two
  surfaces whose root font sizes differ -- both carried the identical em value. Nineteen became
  seven once those were fixed, and an instrument that cries wolf on a third of its findings gets
  ignored, which is worse than no instrument.

AND ONE PATTERN RUNS THROUGH EVERY REAL FINDING, which is the finding above the findings: a
component's markup is emitted by the shared layer and its STYLE is left behind in a template.
Four times, independently -- `.hm`, `.tankcap` (via a blanket that outranked it), `.dem`, and
`.then .ch`, whose rule m1 still carried for markup it had stopped drawing. A markup diff is
blind to all four by construction: the markup never changes, only the cascade does. That is the
gap this instrument exists to cover, and the rule it suggests is one line -- if shared.js emits
the class, shared.css owns the rule.

THE RESULT, re-measured after the last fix (the figure 49510d0 promised rather than asserted,
because its harvest was still running when that commit landed).

`report`, desktop against phone: 0 unruled findings, 7 ruled differences honoured, 0 stale
rulings, across 72 shared roles.

`moved`, from the commit before this work to the end of it -- every role whose drawn appearance
changed, named, with nothing left over:

    v4_doors.html   0 of 104    the desktop did not move for ANY of the five changes
    m1_stack.html   8 of  87    b@div.tankcap, 3x span.hm, and 4 keys from .v -> .sline
    m2_sheet.html   4 of 105    b@div.tankcap, 3x span.hm
    m3_hero.html    4 of 107    b@div.tankcap, 3x span.hm

AND `b@div.dem` IS IN NONE OF THEM, which is the quietest line here and the most reassuring. The
`.dem` work removed four duplicate rules and ended where it started on every surface: the shared
default gives each one exactly what its own template had been giving it separately. A role that
should always have had one home, moved into that home, drawing the same thing afterwards. The
m2/m3 excursion to --ink in the middle of that was a transient this instrument caught and the
`.ctx2 b` hoist closed; it is not in the before-and-after because it was never in either end.

Usage, from this directory:
    python3 _converge.py harvest . after.json      # or any built directory
    python3 _converge.py report after.json         # desktop against phone
    python3 _converge.py moved before.json after.json   # what changed between two harvests
"""
import sys, glob, json, re, pathlib, collections

STATES = ["mid", "early", "late"]
FIXTURE = pathlib.Path(__file__).resolve().parents[2] / "fixture.json"

# Every surface harvested, and the viewport each is DESIGNED for. Comparing the desktop at a
# phone viewport would measure its own reflow, not the two designs.
#
# ROWS ARE KEYED BY FILE, not by "desktop"/"phone", so the same harvest serves both jobs: the
# convergence report (which reads the two named surfaces below) and `moved`, which compares two
# harvests and says which roles on which surface changed appearance. That second job is the one
# a markup diff cannot do -- _domdiff hashes markup, so a CSS change is invisible to it BY
# CONSTRUCTION, and a certification from it is not evidence that appearance held still. That
# mistake was made in this directory and committed as a correction; this is the instrument that
# answers the question _domdiff cannot.
SURFACES = [("v4_doors.html", 1440, 900),
            ("m1_stack.html", 390, 844),
            ("m2_sheet.html", 390, 844),
            ("m3_hero.html", 390, 844)]
DESKTOP, PHONE = "v4_doors.html", "m1_stack.html"

HARVEST = r"""() => {
  // A bare tag is NOT a role. The first run of this instrument keyed on `tag.class` alone, so
  // every unclassed <em>, <i> and <span> on a surface collapsed into one key -- and three of its
  // nineteen findings were that collapse reporting itself: an <em> inside the phone's expand
  // button and an <em> inside a caption are different roles, and a key that cannot tell them
  // apart reports a divergence between two things that were never the same thing. Name an
  // unclassed element by the nearest classed ancestor that does have a role.
  const roleKey = (el) => {
    const own = el.getAttribute('class');
    if (own && own.trim()) return el.tagName.toLowerCase() + '.' + own.trim().split(/\s+/).join('.');
    let a = el.parentElement, hops = 0;
    while (a && hops < 4) {
      const c = a.getAttribute('class');
      if (c && c.trim()) return el.tagName.toLowerCase() + '@' + a.tagName.toLowerCase() + '.' + c.trim().split(/\s+/).join('.');
      a = a.parentElement; hops++;
    }
    return el.tagName.toLowerCase() + '@?';
  };
  const room = document.querySelector('.room');
  if (!room) return [];
  const out = [];
  const w = document.createTreeWalker(room, NodeFilter.SHOW_TEXT);
  while (w.nextNode()) {
    const t = w.currentNode.textContent.replace(/\s+/g, ' ').trim();
    if (!t) continue;
    const el = w.currentNode.parentElement;
    if (!el) continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    out.push({
      key: roleKey(el),
      face: cs.fontFamily.split(',')[0].replace(/["']/g, '').trim(),
      size: Math.round(parseFloat(cs.fontSize) * 10) / 10,
      weight: cs.fontWeight,
      ls: cs.letterSpacing === 'normal' ? 'normal'
            : String(Math.round(parseFloat(cs.letterSpacing) / parseFloat(cs.fontSize) * 1000) / 1000) + 'em',
      tt: cs.textTransform,
      color: cs.color,
      text: t
    });
  }
  return out;
}"""


def harvest(directory, out):
    from playwright.sync_api import sync_playwright
    D = pathlib.Path(directory).resolve()
    formats = list(json.loads(FIXTURE.read_text()).keys())
    rows = collections.defaultdict(list)
    with sync_playwright() as p:
        _c = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")
                    + glob.glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-linux*/headless_shell"))
        if not _c:
            raise RuntimeError("no pre-provisioned chromium under /opt/pw-browsers")
        b = p.chromium.launch(executable_path=_c[0])
        for name, W, H in SURFACES:
            f, side = D / name, name
            phone = name.startswith("m")
            for fmt in formats:
                for st in STATES:
                    # The phone's main display collapses every door; its open state is where the
                    # roles under comparison are actually drawn. Harvest both and union them, or
                    # the phone looks like it has no card vocabulary at all.
                    for q in (("?open", "") if phone else ("",)):
                        pg = b.new_page(viewport={"width": W, "height": H})
                        errs = []
                        pg.on("pageerror", lambda e: errs.append(str(e)))
                        pg.goto("file://" + str(f) + q + "#" + fmt + "/" + st, wait_until="load")
                        pg.wait_for_timeout(700)
                        for rec in pg.evaluate(HARVEST):
                            rec["where"] = f"{fmt}/{st}{q}"
                            rows[side].append(rec)
                        if errs:
                            rows[side].append({"key": "!PAGEERROR", "text": errs[0], "where": fmt,
                                               "face": "", "size": 0, "weight": "", "ls": "",
                                               "tt": "", "color": ""})
                        pg.close()
        b.close()
    pathlib.Path(out).write_text(json.dumps(rows, indent=1, sort_keys=True))
    print(f"harvested: " + ", ".join(f"{k} {len(v)} drawn text nodes" for k, v in rows.items()) + f" -> {out}")


#: Differences between the two surfaces that are DELIBERATE, each with the reason it was ruled.
#: An instrument with no way to accept a ruled difference re-reports it every run and gets
#: ignored -- the same reasoning that made _domdiff hash markup instead of pixels. The entry is
#: (role, axis) -> why.
#:
#: AND THE LIST IS CHECKED IN BOTH DIRECTIONS. A ruling whose difference has gone away is dead
#: config: it stops describing anything, and the next reader has no way to tell a live ruling
#: from a fossil. STALE RULINGS below is the half of this check that an allow-list normally
#: lacks, and it is reported as loudly as a finding.
RULED = {
    ("span.u", "CASE"): "the phone draws .u only inside the folding lineup row, where `.vs .u` "
                        "deliberately de-capses it so the slot label reads as part of a sentence "
                        "rather than as a column header",
    ("span.u", "TRACKING"): "same rule -- de-capsed text does not want the uppercase label's tracking",
    ("span.ck", "CASE"): "the phone's compact cost row (`.cost2 .cc .ck`) de-capses the cost key "
                         "for the same reason: at phone width the row reads as a phrase",
    ("span.ck", "TRACKING"): "same rule",
    # The desktop draws TWO roles under the class `.t` and the phone draws one of them. The
    # second is the gold uppercase label inside `.call`, the pick-confirmation call-out, which
    # is deliberately desktop-only (`callHTML`, like `flipDraw`). So the difference is real and
    # expected -- but it is worth recording WHY it hides here rather than in the one-side-only
    # list: two unrelated components both named their label `.t`, so a key that is per-class
    # cannot separate them. The ruling is the difference; the shared name is a note for whoever
    # next renames one of them.
    ("span.t", "FACE"): "the desktop's second `.t` is the gold label inside `.call`, the "
                        "pick-confirmation call-out, which is desktop-only by design; two "
                        "unrelated components share the class name `.t`",
    ("span.t", "COLOR"): "same: the gold is `.call .ch .t`, a desktop-only component",
    ("span.t", "TRACKING"): "same: 0.14em is `.call .ch .t`, a desktop-only component",
}

WORD = re.compile(r"[a-z][a-z'\-]{1,}")


def _words(recs):
    bag = collections.Counter()
    for r in recs:
        for m in WORD.findall(r["text"].lower()):
            bag[m] += 1
    return bag


def report(path):
    data = json.loads(pathlib.Path(path).read_text())
    d, m = data[DESKTOP], data[PHONE]
    errs = [r for r in d + m if r["key"] == "!PAGEERROR"]
    if errs:
        print(f"!! {len(errs)} renders raised a page error; the comparison below is unsafe")
        for e in errs[:3]:
            print("   ", e["where"], e["text"][:140])
    d = [r for r in d if r["key"] != "!PAGEERROR"]
    m = [r for r in m if r["key"] != "!PAGEERROR"]

    def index(recs, field):
        out = collections.defaultdict(set)
        for r in recs:
            out[r["key"]].add(r[field])
        return out

    keys_d, keys_m = {r["key"] for r in d}, {r["key"] for r in m}
    both = sorted(keys_d & keys_m)
    print(f"\nroles: {len(keys_d)} desktop, {len(keys_m)} phone, {len(both)} shared")

    findings, ruled_hit, stale = 0, 0, []
    for field, label in (("face", "FACE"), ("color", "COLOR"),
                         ("tt", "CASE"), ("ls", "TRACKING")):
        di, mi = index(d, field), index(m, field)
        diverge = [k for k in both if di[k] != mi[k]]
        bad = [k for k in diverge if (k, label) not in RULED]
        ok_ruled = [k for k in diverge if (k, label) in RULED]
        stale += [(k, label) for (k, ax) in RULED if ax == label
                  for k in [k] if k in both and k not in diverge]
        print(f"\n=== {label}: {len(bad)} unruled, {len(ok_ruled)} ruled, of {len(both)} shared roles ===")
        for k in bad[:14]:
            print(f"  {k}\n      desktop {sorted(di[k])}\n      phone   {sorted(mi[k])}")
        if len(bad) > 14:
            print(f"  ... and {len(bad) - 14} more")
        for k in ok_ruled:
            print(f"  ruled  {k}: {RULED[(k, label)]}")
        findings += len(bad)
        ruled_hit += len(ok_ruled)

    # SIZE: ratios, and the roles off the surface's own factor.
    di, mi = index(d, "size"), index(m, "size")
    ratios = {}
    for k in both:
        a, b = max(di[k]), max(mi[k])
        if a:
            ratios[k] = round(b / a, 3)
    if ratios:
        vals = sorted(ratios.values())
        dom = vals[len(vals) // 2]
        off = sorted((k for k in ratios if abs(ratios[k] - dom) > 0.12), key=lambda k: ratios[k])
        print(f"\n=== SIZE: dominant phone/desktop factor {dom}; {len(off)} roles off it by >0.12 ===")
        for k in off[:16]:
            print(f"  {ratios[k]:.3f}  {k}   {max(di[k])}px -> {max(mi[k])}px")
        if len(off) > 16:
            print(f"  ... and {len(off) - 16} more")

    # WORDS: chrome vocabulary, with the fixture's own words subtracted.
    fixture_words = set(WORD.findall(FIXTURE.read_text().lower()))
    wd, wm = _words(d), _words(m)
    only_d = sorted(w for w in wd if w not in wm and w not in fixture_words)
    only_m = sorted(w for w in wm if w not in wd and w not in fixture_words)
    print(f"\n=== WORDS: chrome vocabulary, fixture's own words subtracted ===")
    print(f"  desktop only ({len(only_d)}): {' '.join(only_d)}")
    print(f"  phone only   ({len(only_m)}): {' '.join(only_m)}")

    print(f"\n=== roles on one side only (expected, not a divergence) ===")
    print(f"  {DESKTOP} only: {' '.join(sorted(keys_d - keys_m)[:18])}")
    print(f"  {PHONE} only:   {' '.join(sorted(keys_m - keys_d)[:18])}")
    if stale:
        print(f"\n=== STALE RULINGS: {len(stale)} ruled differences no longer exist ===")
        for k, ax in stale:
            print(f"  {k} / {ax} -- the two surfaces now agree; this ruling describes nothing")
    print(f"\nUNRULED FINDINGS (face/color/case/tracking): {findings}"
          f"   ruled differences honoured: {ruled_hit}   stale rulings: {len(stale)}")
    return 0 if not findings and not stale else 1


def moved(old, new):
    """Which roles, on which surface, changed how they are DRAWN between two harvests.

    This is the check a CSS change answers to. A markup hash cannot see a token change, a
    cascade reorder, or a rule that moved between files -- it is blind to all of them by
    construction -- so "0 of 60 markup moved" says nothing about appearance. Here, a role whose
    (face, size, weight, case, tracking, colour) set differs between the two harvests is
    reported, per surface, and an intended change shows up exactly as loudly as an accident.
    """
    a, b = (json.loads(pathlib.Path(p).read_text()) for p in (old, new))
    FIELDS = ("face", "size", "weight", "tt", "ls", "color")

    def shape(rows):
        out = collections.defaultdict(set)
        for r in rows:
            if r["key"] != "!PAGEERROR":
                out[r["key"]].add(tuple(str(r[f]) for f in FIELDS))
        return out

    total = 0
    for f in sorted(set(a) | set(b)):
        if f not in a or f not in b:
            print(f"\n{f}: present in only one harvest")
            continue
        x, y = shape(a[f]), shape(b[f])
        diff = sorted(k for k in set(x) | set(y) if x.get(k) != y.get(k))
        print(f"\n{f}: {len(diff)} of {len(set(x) | set(y))} roles changed")
        for k in diff[:12]:
            print(f"  {k}\n      before {sorted(x.get(k, []))}\n      after  {sorted(y.get(k, []))}")
        if len(diff) > 12:
            print(f"  ... and {len(diff) - 12} more")
        total += len(diff)
    print(f"\nroles whose drawn appearance changed: {total}")
    return 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["harvest"]:
        harvest(*sys.argv[2:4])
    elif sys.argv[1:2] == ["report"]:
        sys.exit(report(sys.argv[2]))
    elif sys.argv[1:2] == ["moved"]:
        sys.exit(moved(*sys.argv[2:4]))
    else:
        print(__doc__)
        sys.exit(2)
