#!/usr/bin/env python3
"""Render every variant at each width in WIDTHS x 900, in each of the three states, and ASSERT on:
   - console / page errors, page scroll, self-clipping under overflow:hidden (round 1's probes)
   - text overflow: any visible text node whose box is wider/taller than its clip (ellipsis or hidden)
   - occlusion: a visible text element whose centre point resolves to an element that is neither
     itself, an ancestor nor a descendant (an opaque sibling painted over it)
   - scrollers: every region that scrolls must carry a visible "↓ scroll · N more" affordance
   - a captioned count ("N names") never exceeds the rows actually drawn + the "more" count
   - minimum resident font 12px
   Then a PNG per render, to be looked at.

   THREE INDEPENDENT THINGS ARE BEING CERTIFIED HERE, and conflating them is how a green count
   comes to mean less than it looks like it means:

     FUNCTIONAL INTEGRITY   does each surface still draw correctly -- the asserts above, over
                            every format, draft state, viewport and open/closed combination.
     VISUAL CONVERGENCE     do the surfaces follow ONE design contract. Not this file's job:
                            _converge.py measures it (desktop against phone, four axes) and
                            _palette.py measures the palette against design_system.py.
     PROCESS INTEGRITY      is the artifact being certified the artifact being shipped. This is
                            the one that was missing, and its absence cost two voided runs in a
                            single session -- a rebuild landing mid-walk gave the first N renders
                            one build and the rest another, and both runs still printed a clean
                            verdict. It is answered three ways now: a lock (_gatelock.py, with
                            its own ten-arm test) stops the common accident, an immutable
                            snapshot makes the uncommon one unobservable, and the snapshot is
                            RE-HASHED at the end so immutability is demonstrated rather than
                            assumed. The run writes _certification.json naming the source commit
                            and the exact bytes, because "397 ok" identifies no artifact.

   A green count is only worth what the weakest of those three is worth."""
import sys, glob, pathlib, json, os, atexit, signal, shutil, tempfile, hashlib
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).resolve().parent
SHOTS = HERE / "_shots"; SHOTS.mkdir(exist_ok=True)

# The lock, and the reason it is a module: see _gatelock.py, which also records the hour in
# which this was twelve lines in each file and the two copies disagreed about the file format.
sys.path.insert(0, str(HERE))
import _gatelock

LOCK = HERE / ".gate.lock"

import json
FORMATS = list(json.loads(pathlib.Path("/home/user/The-Dynasty-Collective/ui_explore/fixture.json").read_text()).keys())
STATES = ["mid", "early", "late"]
# Viewports as WxH. Typography scales with viewport HEIGHT and is capped by the door's
# own width, so a width alone no longer describes a render. BOTH defaults are load-
# bearing. At 1440x900 the name lands 0.18px above its clamp floor, so the cross-state
# size assertion below has almost no headroom there — it happens to catch a planted
# door-count change, but a build sitting flat on the floor would hide one. 1700x1100 is
# a viewport where the cap binds with real margin (17.61px vs 19.1px on the same
# plant), so the assertion has something to measure.
_vp = lambda s: [tuple(int(n) for n in v.lower().split("x")) for v in s.split(",")]
VIEWPORTS = _vp(__import__("os").environ.get("SHOOT_VIEWPORTS", "1440x900,1700x1100"))
# A phone is not a narrow desktop and must not be measured as one. The mobile surfaces (m*)
# render at phone viewports, and three of the assertions below change meaning there:
#   - VERTICAL page scroll is the point of the surface, not a defect. What IS a defect is an
#     unbounded one, so it is replaced by a budget: the document may be at most
#     SHOOT_SCROLL_BUDGET screens tall, in every state, which is "not excessive scrolling"
#     stated as a number instead of a vibe. Horizontal scroll stays fatal.
#   - visibility stops meaning "inside the viewport" and starts meaning "inside the document",
#     so the content below the fold is checked too rather than silently skipped. Occlusion is
#     the one probe that cannot follow, since elementFromPoint only answers for the viewport.
#   - "cut off" is measured against the document's own height, which is what a reader can reach.
# Tap targets are asserted on mobile and only there: a 44px floor, the one metric a thumb cares
# about that a mouse does not.
# PHONE VIEWPORTS ARE NOT PHONE SCREENS, and this gate had them wrong from the day it grew a
# mobile path. 390x844, 360x800 and 430x932 are DEVICE SCREENS in points -- what a spec sheet
# says -- and a phone browser never hands a page that height: the tab bar and the toolbar take a
# fixed bite out of the top and bottom. Playwright ships the real numbers in its own device
# registry, and they are not close:
#
#     iPhone 12 / 13 / 14         390x664    (was being rendered at 390x844, +180px, +27%)
#     iPhone 13 / 12 Pro Max      428x746    (was 430x932, +186px)
#     Galaxy S24                  360x780    (was 360x800)
#     Pixel 7                     412x839    -- the tallest real one, and still short of 844
#
# So every mobile verdict taken before this line changed -- "screens=1.00", "the first door
# lands at y=194", "four doors on the first screen" -- was measured against about a quarter more
# height than a real browser shows, which is the house failure mode: a plausible number about
# something else. The owner's own aside is what prompted the check ("a desktop-first draft
# interface compressed onto a phone isn't necessarily a usable mobile draft interface"), and
# the registry rather than memory is what settled it.
#
# These three are the BINDING cases, not a spread: the modal iPhone, the narrowest current
# Android, and the widest iPhone -- which is also, counter-intuitively, shorter than the Pixel.
# Pixel 7's 412x839 is the most forgiving real viewport and is deliberately left out; a surface
# certified on the short ones fits the tall one for free, and the reverse is what went wrong.
MOBILE_VIEWPORTS = _vp(__import__("os").environ.get("SHOOT_MOBILE_VIEWPORTS", "390x664,360x780,428x746"))
# TWO budgets, because the surface has two states and they do not make the same promise.
# The MAIN DISPLAY is what a reader lands on and what the owner specified as "the 4-5 main
# recommendations near the top"; it is held tight. The EXPANDED state is the detail a reader
# asked for by tapping a door -- it must still be bounded, but bounding it at the main
# display's figure would mean a door could never carry more than the stack it sits in.
# Discriminated by whether a door is actually open, not by the query string, so a variant
# that chooses to open nothing by default is measured as the main display it is.
SCROLL_BUDGET_MAIN = float(__import__("os").environ.get("SHOOT_SCROLL_BUDGET_MAIN", "2.0"))
SCROLL_BUDGET_OPEN = float(__import__("os").environ.get("SHOOT_SCROLL_BUDGET_OPEN", "3.0"))
TAP_FLOOR = 44
is_mobile = lambda f: pathlib.Path(f).name.startswith("m")
# (file, query, [formats]) — v4 runs every format; the others are control-only
def _jobs_for(f):
    """Every format on the surfaces that carry all of them (v4 and every mobile surface, which
    are the same board); the first format only on the controls."""
    if is_mobile(f):
        # The bare URL is the MAIN DISPLAY with no door open -- the thing the owner specified as
        # "the 4-5 main recommendations near the top" -- and `?open` lands with the leader's door
        # open. Both are reachable by URL rather than only by tapping, so the suite asserts BOTH
        # states without an interaction script: the state a reader lands on and returns to is as
        # measurable as the one they open. (The phones used to land open and reach the main
        # display through `?collapsed`; they land collapsed now, and `?collapsed` is still
        # honoured as the brief reserves it.)
        # EVERY format in both states, not a sample of two. Sampling two formats left the main
        # display unmeasured on the hardest board in the fixture: m1's collapsed HEAVY_IDP
        # measured 1.96 screens against a 2.0 budget, so the format the sample skipped was the
        # one with the least margin. A budget that does not cover its tightest case is not a budget.
        return [(f, "", FORMATS), (f, "open", FORMATS)]
    return [(f, "", FORMATS if "v4_" in f else [FORMATS[0]])]


# ---------------------------------------------------------------------------------------
# KNOWN FAILURES, AND THE HALF OF THIS MECHANISM THAT MATTERS MORE THAN THE OBVIOUS HALF.
#
# This gate is red on two renders that are measured, understood, and NOT YET RULED ON -- the
# owner's chosen phone variant needs 2.04 and 2.01 screens of travel where the budget allows 2.0,
# and every lever that would close the gap changes how that variant looks, which is the owner's
# call rather than mine. Leaving the gate simply red is the hazard: the next run cannot tell "my
# change broke something" from "those two again", and a gate nobody can read is a gate nobody
# runs. The alternative hazard is worse -- raising the budget to make red go away would be moving
# the goalposts after measuring against them.
#
# So each known failure is named here with the number that was measured and why it stands. They
# stay counted in `renders_failed`, stay printed in full, and stay in the certification record.
# What changes is only the EXIT CODE: a new failure fails the run, a known one does not.
#
# AND AN EXPECTATION THAT STOPS DESCRIBING ANYTHING FAILS THE RUN TOO. If one of these renders
# starts passing, something changed that nobody measured -- a fix, a regression elsewhere, a
# viewport edit -- and the entry is now a fossil asserting a defect that is gone. That is the
# same reasoning _converge.py's STALE RULINGS carries, and it is the half an allow-list usually
# lacks: without it this table only ever grows, and every entry in it is permanent by default.
#
# The key is (file, query, format, state, viewport). The value is what was measured and why.
KNOWN_FAILURES = {
    ("m1_stack.html", "", "HEAVY_IDP", "late", (390, 664)):
        "scroll budget 2.01 (1336px against a 1328px allowance), over by 8px. It was 2.04 at "
        "1357px: the spacing levers MAIN_PAGE.md had costed -- .main gap 8->6 and its padding "
        "8/10->6/8, .db padding 5/8->4/6 -- reclaimed 21px of genuine slack, which closed "
        "LIGHT_IDP/late outright, so its entry is GONE from this table rather than kept. "
        "HEAVY_IDP is the seven-door format, the densest shape the fixture carries, and the "
        "last 8px would have to come out of spacing that is no longer slack. NOT TAKEN, on "
        "#56's rule that a bound is not a threshold: sizing a change to cross 1328 would be "
        "fitting it to a number whose own calibration is the open question, since 2.0 screens "
        "was authored against an 844px phone screen that no browser gives a page. "
        "Measured 2026-11-04.",
}
SEEN_FAILURES = set()

JOBS = []
if sys.argv[1:]:
    for f in sys.argv[1:]:
        JOBS += _jobs_for(f)
else:
    for f in sorted(str(p) for p in HERE.glob("v*.html") if "v3_" not in p.name):
        JOBS += _jobs_for(f)
    JOBS.append((str(HERE / "v4_doors.html"), "alldoors", ["HEAVY_IDP", "12T_ppr_K_DEF"]))
    JOBS.append((str(HERE / "v4_doors.html"), "notank", [FORMATS[0]]))
    for f in sorted(str(p) for p in HERE.glob("m*.html")):
        JOBS += _jobs_for(f)
# ---------------------------------------------------------------------------------------
_gatelock.take(LOCK)

# CERTIFY A SNAPSHOT, NOT A DIRECTORY. The lock above stops the common accident, but it is a
# convention: it only works because _build.py agrees to check it, and nothing stops a stray
# editor, a git checkout or a second tool from rewriting these files mid-walk. So the gate
# stops reading the working directory at all. It copies the builds it is about to certify into
# a temp directory and renders from there, which makes an accidental rebuild IMPOSSIBLE to
# observe rather than merely unlikely -- the run is reading bytes nothing else has a path to.
#
# And it prints the digest of each, which is the part that makes a verdict defensible later.
# "397 ok" names no artifact; a reader cannot tell whether the run certified the commit in front
# of them. These twelve hex characters tie the verdict to exact bytes, so a green run can be
# checked against the tree it claims to be about. Cost: about 10 MB of temp space, removed on
# exit (and on SIGTERM, through the same handler the lock registers).
SNAP = pathlib.Path(tempfile.mkdtemp(prefix="gate-snapshot-"))
_gatelock.also_remove(SNAP)   # released with the lock, on exit AND on signal
_DIGESTS = {}
for _src in sorted({pathlib.Path(j[0]) for j in JOBS}):
    shutil.copy2(_src, SNAP / _src.name)
    _DIGESTS[_src.name] = hashlib.sha256((SNAP / _src.name).read_bytes()).hexdigest()[:12]
JOBS = [(str(SNAP / pathlib.Path(f).name), q, fmts) for f, q, fmts in JOBS]
print(f"certifying a snapshot of {len(_DIGESTS)} builds (nothing else can reach these bytes):")
for _n, _h in sorted(_DIGESTS.items()):
    print(f"    {_h}  {_n}")

PROBE = """(opt) => {
  const r = {}, MOB = !!(opt && opt.mobile);
  r.pageScroll = [document.documentElement.scrollWidth > innerWidth + 1, document.documentElement.scrollHeight > innerHeight + 1];
  // THE HARNESS IS NOT THE PRODUCT. `.rev` is this directory's own review bar -- the variant
  // tag, the early/mid/late buttons, the format picker, the hypothesis toggle -- injected by
  // wireChrome() so a human can drive the prototype. It is 36px tall on a phone and it will not
  // exist in the app, and it was being counted into the scroll budget as though a user had to
  // scroll past it. Measured, and stated because it matters that the correction is not a rescue:
  // taking it out moves HEAVY_IDP/late from 2.11 screens to 2.05 and LIGHT_IDP/late from 2.07 to
  // 2.02, so both still FAIL the 2.0 budget at 390x664. An instrument fix that made the failure
  // disappear would be worth distrusting; this one does not.
  r.harnessH = [...document.querySelectorAll('.rev, .hypbox')]
      .reduce((m, el) => m + Math.round(el.getBoundingClientRect().height), 0);
  r.docH = document.documentElement.scrollHeight - r.harnessH; r.vh = innerHeight;
  // On mobile the reachable surface is the DOCUMENT, not the window: content below the fold is
  // content a reader scrolls to, so it is checked rather than skipped as "offscreen".
  const BOT = MOB ? Math.max(innerHeight, document.documentElement.scrollHeight) : innerHeight;
  const vis = el => { const cs = getComputedStyle(el); if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return false; const b = el.getBoundingClientRect(); if (!(b.width > 0 && b.height > 0 && b.bottom > 0 && b.top < BOT && b.right > 0 && b.left < innerWidth)) return false;
    // clipped away by an ancestor's overflow (a scroller's hidden rows, a clipped past row) is not visible
    const cx = b.left + Math.min(b.width, 40) / 2, cy = b.top + b.height / 2; let a = el.parentElement;
    while (a && a !== document.body) { const acs = getComputedStyle(a); if (acs.overflow !== 'visible' || acs.overflowY !== 'visible' || acs.overflowX !== 'visible') { const ab = a.getBoundingClientRect(); if (cx < ab.left || cx > ab.right || cy < ab.top || cy > ab.bottom) return false; } a = a.parentElement; } return true; };
  const inSheet = el => !!el.closest('.sheet,.hypbox');
  const all = [...document.querySelectorAll('.room *')].filter(el => !inSheet(el));
  const tag = el => (el.className && el.className.toString().split(' ')[0]) || el.tagName.toLowerCase();
  r.scrollers = all.filter(el => { const cs = getComputedStyle(el); return /(auto|scroll)/.test(cs.overflowY) && el.scrollHeight > el.clientHeight + 2; }).map(el => ({id: tag(el) + (el.dataset.list ? '[' + el.dataset.list + ']' : ''), more: el.dataset.more || null, moreVisible: !!(el.parentElement.querySelector(':scope > .more') && vis(el.parentElement.querySelector(':scope > .more')))}));
  r.badScrollers = r.scrollers.filter(s => !s.more || !s.moreVisible).map(s => s.id);
  r.deepScroll = all.filter(el => { const cs = getComputedStyle(el); return /(auto|scroll)/.test(cs.overflowY); })
    .reduce((m, el) => Math.max(m, el.scrollHeight), 0);
  r.clipped = all.filter(el => { const cs = getComputedStyle(el); return cs.overflow === 'hidden' && !/(auto|scroll)/.test(cs.overflowY) && el.scrollHeight > el.clientHeight + 2 && !el.classList.contains('face') && !el.classList.contains('room') && !el.classList.contains('past') && !el.classList.contains('scroll'); }).map(el => tag(el) + ' ' + el.scrollHeight + '/' + el.clientHeight).slice(0, 10);
  // text overflow: an element with its own text whose content is wider than its box and not scrollable
  r.textOverflow = all.filter(el => { if (!vis(el)) return false; const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if (!hasText) return false;
    const cs = getComputedStyle(el); const clipped = cs.overflow === 'hidden' || cs.overflowX === 'hidden' || cs.textOverflow === 'ellipsis' || (el.parentElement && getComputedStyle(el.parentElement).overflow === 'hidden');
    return clipped && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 2) && !el.closest('.past') && !el.classList.contains('face'); }).map(el => tag(el) + ': ' + el.textContent.trim().slice(0, 30)).slice(0, 12);
  // occlusion: centre of a text element resolves to an unrelated element
  r.occluded = all.filter(el => { if (!vis(el)) return false; const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if (!hasText) return false;
    const rects = el.getClientRects(); const b = rects.length ? rects[0] : el.getBoundingClientRect();
    // elementFromPoint answers only for the viewport, so below-fold rows are not asked about
    if (MOB && (b.top < 0 || b.bottom > innerHeight)) return false; const x = Math.min(innerWidth - 1, Math.max(0, b.left + Math.min(b.width, 40) / 2)), y = Math.min(innerHeight - 1, Math.max(0, b.top + b.height / 2));
    const hit = document.elementFromPoint(x, y); if (!hit) return false; // A fixed nav bar or fold cue painted over content is a DELIBERATE overlay, the same class of
    // thing as the scrim, not an accidental sibling. What a fixed bar can genuinely break is
    // different and is asserted separately below: content TRAPPED under it, unreachable at any
    // scroll position. Exempting it here without that assertion would be a hole.
    return !(hit === el || el.contains(hit) || hit.contains(el)) && !hit.classList.contains('scrim') && !hit.closest('.sheet,.dock,.fold'); }).map(el => tag(el) + ': ' + el.textContent.trim().slice(0, 30)).slice(0, 12);
  // cut off by the viewport: a text element not inside any scroller/clipper whose box runs past the fold
  const clippedByAncestor = el => { let a = el.parentElement; while (a && a !== document.body) { const acs = getComputedStyle(a); if (acs.overflow !== 'visible' || acs.overflowY !== 'visible') return a; a = a.parentElement; } return null; };
  r.cutOff = all.filter(el => { const cs = getComputedStyle(el); if (cs.display === 'none') return false; const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if (!hasText) return false;
    const b = el.getBoundingClientRect(); if (!(b.width > 0 && b.height > 0)) return false; const clip = clippedByAncestor(el); if (clip && !clip.classList.contains('room')) return false; return b.bottom > BOT + 1 || b.right > innerWidth + 1; }).map(el => tag(el) + ': ' + el.textContent.trim().slice(0, 30)).slice(0, 12);
  // captioned counts vs drawn rows
  r.counts = [...document.querySelectorAll('[data-list]')].filter(el => !inSheet(el)).map(el => { const rows = [...el.querySelectorAll('[data-row]')]; const drawn = rows.filter(x => vis(x)).length; return {list: el.dataset.list, rows: rows.length, drawn, more: el.dataset.more ? +el.dataset.more : 0}; });
  r.badCounts = r.counts.filter(c => c.drawn + c.more < c.rows).map(c => c.list + ' ' + c.drawn + '+' + c.more + '<' + c.rows);
  // HORIZONTAL clipping. badScrollers only ever asked about overflowY, because on a desktop a
  // row that runs past its box is a layout bug caught by textOverflow. On a phone it is the
  // normal way a strip of chips fails: the lineup strip runs off the right edge and the names
  // past the fold are simply unreachable, with nothing on screen saying so. Containers only
  // (two or more element children), so this does not re-report what textOverflow already covers.
  r.hClip = !MOB ? [] : all.filter(el => vis(el) && !el.closest('#rev,#hyp') && el.children.length >= 2
      && el.scrollWidth > el.clientWidth + 2)
    .map(el => { const cs = getComputedStyle(el);
      const scrollable = /(auto|scroll)/.test(cs.overflowX);
      return `${tag(el)} ${el.clientWidth}<${el.scrollWidth}px ${scrollable ? "(scrolls, needs an affordance)" : "(CLIPPED, unreachable)"}`; })
    .slice(0, 8);
  // TRAPPED UNDER THE DOCK. A fixed bottom bar hides whatever is behind it at every scroll
  // position, so the document must carry at least the bar's height of clearance below its
  // lowest content -- otherwise the last row can never be scrolled out from under it and is
  // unreachable rather than merely covered.
  r.dockTrap = null;
  if (MOB) { const dock = document.querySelector('.dock');
    if (dock) { const dh = dock.getBoundingClientRect().height, sy = scrollY;
      let low = 0;
      all.forEach(el => { if (el.closest('.dock,.fold') || !el.textContent.trim()) return;
        const b = el.getBoundingClientRect(); if (b.width > 0 && b.height > 0) low = Math.max(low, b.bottom + sy); });
      const clear = document.documentElement.scrollHeight - low;
      if (clear < dh - 1) r.dockTrap = `lowest content ends ${Math.round(clear)}px above the document bottom, under a ${Math.round(dh)}px dock`; } }
  // tap targets: a thumb needs 44px, and a control that misses it is a control that gets
  // mis-pressed under a draft clock. Asserted on mobile only -- a mouse does not care.
  r.tap = !MOB ? [] : all.filter(el => vis(el) && !el.closest('#rev,#hyp')
      && el.matches('button,a[href],[role="button"],[data-door],[data-open],[data-f],[data-sheet],[data-close]')
      && !el.querySelector('button,a[href],[role="button"]'))
    .map(el => { const b = el.getBoundingClientRect(); return {t: tag(el), w: Math.round(b.width), h: Math.round(b.height), x: el.textContent.trim().slice(0, 18)}; })
    .filter(o => o.h < 44 - 0.5 || o.w < 32)
    .map(o => `${o.t} ${o.w}x${o.h}: ${o.x}`).slice(0, 12);
  let min = 99, minEl = '';
  all.forEach(el => { if (!vis(el)) return; const t = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if (!t) return; const fs = parseFloat(getComputedStyle(el).fontSize); if (fs < min) { min = fs; minEl = tag(el) + ': ' + el.textContent.trim().slice(0, 20); } });
  r.minFont = [min, minEl];
  // WHICH BOARD LOADED. The format is carried in the URL hash and read by wireChrome, but ONLY
  // when the surface passes {formats:true}; pass false and it silently forces the first format,
  // so all six format renders would show the SAME board and every one of them would come back
  // ok. That is this repo's signature failure -- a plausible render of the wrong thing -- and
  // nothing here would have caught it. The league line names the format it actually built, so
  // the render is made to say what it is rather than being trusted.
  r.lg = (document.getElementById('lg') || {}).textContent || null;
  r.doorOpen = !!document.querySelector('.door.open, [data-door].open, .door[aria-expanded="true"]');
  const _nm = document.querySelector('#doors .door .who .nm');
  r.nameFs = _nm ? getComputedStyle(_nm).fontSize : null;
  r.glyphOverlap = [];
  // per-LINE boxes on both sides: an inline element's bounding rect is the union of its line
  // boxes, so it spans lines it does not occupy and reads as an overlap that isn't there.
  const lineRects = el => { let n = null; el.childNodes.forEach(c => { if (c.nodeType === 3 && c.textContent.trim()) n = c; }); if (!n) return [];
    const rg = document.createRange(); rg.selectNodeContents(n);
    return [...rg.getClientRects()].filter(b => b.width > 0 && b.height > 0); };
  all.forEach(el => { if (!vis(el) || getComputedStyle(el).position !== 'static') return;
    const as = lineRects(el); if (!as.length) return;
    for (let s2 = el.nextElementSibling; s2; s2 = s2.nextElementSibling) {
      if (!vis(s2) || getComputedStyle(s2).position !== 'static' || !s2.textContent.trim()) continue;
      const bs = [...s2.getClientRects()].filter(b => b.width > 0 && b.height > 0);
      const hit = as.some(a => bs.some(b => Math.min(a.right, b.right) - Math.max(a.left, b.left) > 1
                                         && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 1));
      if (hit) r.glyphOverlap.push(tag(el) + ': "' + el.textContent.trim().slice(0, 24) + '" runs under ' + tag(s2)); } });
  // THE FOLD. The page-level sibling of the scroller rule: when the document runs on below the
  // viewport, the cue at the fold must be drawn and lit, or a first screen that happens to end
  // in a gutter reads as a finished page (17 of 216 probed renders did before the cue existed).
  const fold = document.querySelector('.fold');
  r.foldMissing = MOB && document.documentElement.scrollHeight > innerHeight + 6
    && !(fold && fold.classList.contains('on') && +getComputedStyle(fold).opacity > 0.5);
  const now = document.querySelector('.pk.now'), nxt = document.querySelector('.pk.next');
  if (now) { const nb = now.getBoundingClientRect(), xb = nxt ? nxt.getBoundingClientRect() : null; r.rail = {now: nb.left >= 0 && nb.right <= innerWidth, next: xb ? xb.left >= 0 && xb.right <= innerWidth : null, namedPast: [...document.querySelectorAll('.pk')].filter(p => { const b = p.getBoundingClientRect(); return b.left >= 0 && b.right <= innerWidth && !p.classList.contains('between') && !p.classList.contains('future') && !p.classList.contains('now') && !p.classList.contains('next'); }).length}; }
  return r; }"""
NAME_FS = {}   # (file, query, format, viewport) -> {state: computed name size}




with sync_playwright() as p:
    # The pre-provisioned layout is NOT stable across container images: this directory has been
    # `chrome-linux/chrome` on one and `chrome-linux64/chrome` on another, and a glob knowing only
    # the first raises IndexError -- the whole gate refusing to start for a reason that has nothing
    # to do with the surfaces it measures. Match either, and fail with a sentence rather than a
    # subscript on an empty list.
    _cands = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")
                    + glob.glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-linux*/headless_shell"))
    if not _cands:
        raise RuntimeError("no pre-provisioned chromium under /opt/pw-browsers")
    exe = _cands[0]
    b = p.chromium.launch(executable_path=exe)
    bad = 0
    TOTAL = RENDER_BAD = 0   # renders walked, and renders with a problem
    for f, q, fmts in JOBS:
      for fmt in fmts:
        for st in STATES:
          for W, H in (MOBILE_VIEWPORTS if is_mobile(f) else VIEWPORTS):
            pg = b.new_page(viewport={"width": W, "height": H})
            errs = []
            pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
            pg.on("console", lambda m: errs.append(m.type + ": " + m.text) if m.type in ("error", "warning") else None)
            fpath = f; isv4 = "v4_" in f or is_mobile(f)
            pg.goto("file://" + str(pathlib.Path(fpath).resolve()) + ("?" + q if q else "") + "#" + ((fmt + "/") if isv4 else "") + st, wait_until="load")
            pg.wait_for_timeout(600)
            out = SHOTS / f"{pathlib.Path(fpath).stem}{'_' + q if q else ''}{'_' + fmt if isv4 else ''}_{st}{'' if (W, H) == (1440, 900) else f'_{W}x{H}'}.png"
            pg.screenshot(path=str(out), full_page=False)
            r = pg.evaluate(PROBE, {"mobile": is_mobile(f)})
            problems = []
            if errs: problems.append("errors " + json.dumps(errs))
            screens = max(r["docH"], r.get("deepScroll") or 0) / max(1, r["vh"])
            if is_mobile(f):
                if r["pageScroll"][0]: problems.append("horizontal pageScroll")
                budget = SCROLL_BUDGET_OPEN if r.get("doorOpen") else SCROLL_BUDGET_MAIN
                if screens > budget: problems.append(f"scroll budget: {screens:.2f} screens of travel "
                    f"({'expanded, a door is open' if r.get('doorOpen') else 'MAIN DISPLAY, nothing open'}; "
                    f"document {r['docH']}px excluding {r.get('harnessH', 0)}px of review bar, "
                    f"deepest scroller {r.get('deepScroll')}px, viewport {r['vh']}px), over {budget}")
                if r["tap"]: problems.append("tap target under 44px " + json.dumps(r["tap"]))
                if r["hClip"]: problems.append("runs off the right edge " + json.dumps(r["hClip"]))
                if r.get("dockTrap"): problems.append("content trapped under the dock: " + r["dockTrap"])
                if r.get("foldMissing"): problems.append("the page runs on below the fold and nothing at the fold says so")
            elif any(r["pageScroll"]): problems.append("pageScroll")
            if r["clipped"]: problems.append("clipped " + json.dumps(r["clipped"]))
            if r["textOverflow"]: problems.append("textOverflow " + json.dumps(r["textOverflow"]))
            if r["occluded"]: problems.append("occluded " + json.dumps(r["occluded"]))
            if r["cutOff"]: problems.append("cut off by the viewport " + json.dumps(r["cutOff"]))
            if r["badScrollers"]: problems.append("scroller without affordance " + json.dumps(r["badScrollers"]))
            if r["badCounts"]: problems.append("count mismatch " + json.dumps(r["badCounts"]))
            if r["minFont"][0] < 12: problems.append("minFont " + json.dumps(r["minFont"]))
            if isv4:
                # DELIMITED, not a substring: `12T_ppr` is a prefix of `12T_ppr_SF`, so a plain
                # `in` test would have passed a render that loaded superflex when asked for PPR
                # -- the false pass this check exists to prevent. The league line sets the format
                # off with " \u00b7 " on both sides, so the delimiters are what make it exact.
                want = " \u00b7 " + fmt.replace("_", " ") + " \u00b7 "
                if not r.get("lg"): problems.append("no league line, so which board loaded cannot be read")
                elif want not in r["lg"]: problems.append(f"WRONG BOARD: asked for {fmt}, the league line says {r['lg'][:70]!r}")
            if r["glyphOverlap"]: problems.append("text runs under a sibling " + json.dumps(r["glyphOverlap"]))
            if r.get("rail") and (not r["rail"]["now"] or r["rail"]["next"] is False): problems.append("rail " + json.dumps(r["rail"]))
            if r.get("nameFs"):
                NAME_FS.setdefault((pathlib.Path(fpath).name, q, fmt, (W, H)), {})[st] = r["nameFs"]
            _key = (pathlib.Path(fpath).name, q, fmt, st, (W, H))
            TOTAL += 1; RENDER_BAD += bool(problems)
            if problems:
                SEEN_FAILURES.add(_key)
                if _key not in KNOWN_FAILURES:
                    bad += 1
            print(("!! " if problems else "ok ") + ("[known] " if (problems and _key in KNOWN_FAILURES) else "") + f"{pathlib.Path(fpath).name}{'?' + q if q else ''} [{fmt if (isv4 or is_mobile(f)) else 'ctrl'}/{st}@{W}x{H}]  screens={screens:.2f} scrollers={[s['id'] + ':' + str(s['more']) for s in r['scrollers']]} counts={r['counts']} minFont={r['minFont'][0]} rail={r.get('rail')}")
            for pr in problems: print("     ", pr)
            pg.close()
    b.close()

# The door names scale with the viewport and are capped by the door's own width. Door
# width depends on door count, which comes from the league's startable slots and not
# from what has been drafted — so the size must not move as a draft progresses. Type
# that resizes between picks reads as a glitch. This asserts the invariant rather than
# trusting it: if doors are ever made to appear or disappear mid-draft, this fails here
# instead of the type quietly breathing on the owner's screen.
# ---------------------------------------------------------------------------------------
# AWAY AND RETURN. Every render above is a FRESH LOAD, and a draft interface that works until
# somebody leaves the page and comes back is not certified. This is the cheapest honest version
# of that axis for a standalone prototype: drive the URL the way a browser does, and assert the
# one property that has to hold however history is used --
#
#   THE URL MUST NEVER NAME A BOARD THAT IS NOT ON SCREEN.
#
# Not "Back must restore everything" -- these pages are not an app and cannot be held to that
# yet. Just that the address bar and the board agree. The reason it is the load-bearing property
# is that a disagreement is not cosmetic: a reload is one keystroke, and a reload resolves the
# URL, so a URL describing a different board is a board switch the user never asked for, one
# gesture away at all times.
#
# MEASURED BEFORE IT WAS ASSERTED, ASSERTED BEFORE IT WAS FIXED, and it is the assertion that
# keeps it fixed. When this went in it failed on all four surfaces: shared.js wrote the URL with
# history.replaceState and nothing in the directory listened for popstate or hashchange, so the
# URL was write-only -- editing the hash moved the address bar and left the board where it was,
# and Back moved it again and still left the board where it was. wireChrome's applyHash now runs
# the same parse it already ran on load, so all four pass. What is still NOT asserted, because no
# standalone page can answer it, is returning to a LIVE draft: scroll position, which door was
# open, the clock. That needs an app around the board, and the record below names the gap.
print("\n--- away and return: does the URL ever name a board that is not drawn? ---")
NAV_BAD = 0
with sync_playwright() as _p:
    _b = _p.chromium.launch(executable_path=exe)
    A, B = FORMATS[0], ("HEAVY_IDP" if "HEAVY_IDP" in FORMATS else FORMATS[-1])
    for _f, _q, _fmts in [(j[0], j[1], j[2]) for j in JOBS if len(j[2]) > 1 and not j[1]]:
        W, H = (MOBILE_VIEWPORTS if is_mobile(_f) else VIEWPORTS)[0]
        pg = _b.new_page(viewport={"width": W, "height": H})
        pg.goto("about:blank")                       # give Back somewhere to go
        pg.goto("file://" + _f + "#" + A + "/mid", wait_until="load"); pg.wait_for_timeout(600)
        def _seen():
            lg = pg.evaluate("() => (document.getElementById('lg')||{}).textContent || ''") or ""
            url = pg.evaluate("() => location.hash") or ""
            named = next((x for x in FORMATS if " \u00b7 " + x.replace("_", " ") + " \u00b7 " in lg), None)
            asked = url.replace("#", "").split("/")[0] or None
            return asked, named
        steps = []
        steps.append(("on load", *_seen()))
        pg.evaluate(f"() => {{ location.hash = '#{B}/late'; }}"); pg.wait_for_timeout(500)
        steps.append(("hash edited", *_seen()))
        pg.go_back(); pg.wait_for_timeout(600)
        steps.append(("browser Back", *_seen()))
        pg.go_forward(); pg.wait_for_timeout(600)
        steps.append(("browser Forward", *_seen()))
        wrong = [(w, a, n) for w, a, n in steps if a and n and a != n]
        name = pathlib.Path(_f).name
        if wrong:
            NAV_BAD += 1
            print(f"!! {name}: the URL names a board that is not drawn")
            for w, a, n in steps:
                mark = "  <-- URL says one board, screen shows another" if (a and n and a != n) else ""
                print(f"      {w:<18} url says {str(a):<16} screen shows {str(n):<16}{mark}")
        else:
            print(f"ok {name}: url and board agree at every step "
                  + " / ".join(f"{w}={a}" for w, a, n in steps))
        pg.close()
    _b.close()
bad += NAV_BAD

drift = {k: v for k, v in NAME_FS.items() if len(set(v.values())) > 1}
for k, v in sorted(drift.items(), key=lambda kv: str(kv[0])):
    print(f"!! name size moves between draft states  {k[0]}{'?' + k[1] if k[1] else ''} [{k[2]} @ {k[3][0]}x{k[3][1]}]  {v}")
bad += len(drift)
print(f"ok  name size is identical across draft states for all {len(NAME_FS)} (file, format, viewport) groups"
      if not drift else
      f"!! name size MOVES between draft states in {len(drift)} of {len(NAME_FS)} (file, format, viewport) groups")
# ---------------------------------------------------------------------------------------
# DEMONSTRATE IMMUTABILITY, DO NOT ASSUME IT. The snapshot was taken so that nothing could
# change the bytes under this run -- but "nothing could" is a claim about a temp directory, and
# the whole reason this machinery exists is that a claim of that shape was wrong twice today.
# So the digests are taken again now and compared with the ones printed at the start. If they
# match, the run certified one artifact and the record below names it. If they do not, the run
# is void and says so rather than printing a verdict about bytes that moved underneath it.
# Known failures, reconciled in both directions.
_expected = sorted(k for k in SEEN_FAILURES if k in KNOWN_FAILURES)
_stale = sorted(k for k in KNOWN_FAILURES if k not in SEEN_FAILURES)
print()
for k in _expected:
    print(f"ok  KNOWN failure, not counted against this run: {k[0]}{'?' + k[1] if k[1] else ''} "
          f"[{k[2]}/{k[3]}@{k[4][0]}x{k[4][1]}]\n      {KNOWN_FAILURES[k]}")
for k in _stale:
    print(f"!! STALE EXPECTATION: {k[0]}{'?' + k[1] if k[1] else ''} "
          f"[{k[2]}/{k[3]}@{k[4][0]}x{k[4][1]}] was listed as a known failure and PASSED.\n"
          f"      Something changed that nobody measured. Remove the entry and say what fixed it, "
          f"or find out what moved.")
bad += len(_stale)
if not _expected and not _stale:
    print("ok  no known failures listed, and none expected")

_moved = {n: h for n, h in _DIGESTS.items()
          if hashlib.sha256((SNAP / n).read_bytes()).hexdigest()[:12] != h}
if _moved:
    print(f"!! THE SNAPSHOT MOVED under this run: {sorted(_moved)} -- this verdict is VOID")
    bad += len(_moved)
else:
    print(f"ok  the snapshot is byte-identical to what was certified ({len(_DIGESTS)} builds re-hashed)")

# A CERTIFICATION RECORD, so a verdict outlives the terminal it was printed in. "397 ok" names
# no artifact and no source: a reader six weeks later cannot tell whether a green run was about
# the commit in front of them. This names the source commit, the exact bytes, the axes covered,
# and the clock -- which is what makes a green run checkable rather than merely reassuring.
import subprocess as _sp
def _git(*a, empty_ok=False):
    """Git output, or None when git could not answer. `empty_ok` keeps an EMPTY answer as "".

    THAT FLAG EXISTS BECAUSE ITS ABSENCE MADE THIS RECORD LIE, in the small way that is hardest
    to notice: `or None` was written so a missing commit would read as null, and on a CLEAN tree
    `git status --porcelain` returns "" -- falsy -- so it returned None too. The field was then
    `_git(...) == ""`, which is False for None and False for a dirty tree alike, so
    `source_tree_clean` was CONSTANT FALSE and never once reported a clean tree. It read
    plausibly in every run ("tree DIRTY") and meant nothing. Caught by noticing the record say
    DIRTY on a tree deliberately kept clean for it -- which is the only reason a constant field
    gets caught at all.

    So: "" and None are different answers and this stops collapsing them. The three states are
    kept apart below rather than flattened into a boolean that cannot say "git did not answer".
    """
    try:
        out = _sp.run(["git"] + list(a), cwd=str(HERE), capture_output=True, text=True,
                      timeout=20).stdout.strip()
        return out if (out or empty_ok) else None
    except Exception:
        return None


# Nothing is excluded from this, INCLUDING the record file this run is about to overwrite: two
# gate runs without a commit in between genuinely leave a dirty tree, and a cleanliness field
# that quietly forgives its own side effects is the next version of the bug above.
_dirty = _git("status", "--porcelain", empty_ok=True)
_record = {
    "gate": "ui_explore/round2/fableA/_shoot.py",
    "finished_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
                      .isoformat(timespec="seconds"),
    "source_commit": _git("rev-parse", "HEAD"),
    # Tri-state on purpose: True clean, False dirty, null when git could not be asked.
    "source_tree_clean": None if _dirty is None else (_dirty == ""),
    # split(maxsplit=1), not l[3:]: `_git` strips its output, so the FIRST porcelain line has
    # lost the leading status space the others keep, and a fixed column slice eats a character
    # off exactly one path. maxsplit=1 keeps a path containing spaces intact.
    "source_tree_dirty_paths": None if _dirty is None
        else [l.split(maxsplit=1)[-1] for l in _dirty.splitlines() if l.strip()][:20],
    "snapshot_sha256_12": dict(sorted(_DIGESTS.items())),
    "snapshot_verified_unchanged": not _moved,
    "renders": TOTAL, "renders_failed": RENDER_BAD, "renders_ok": TOTAL - RENDER_BAD,
    "failures_total": bad,   # renders, plus the cross-render assertions -- EXCLUDING known ones
    "expected_failures": [f"{k[0]} [{k[2]}/{k[3]}@{k[4][0]}x{k[4][1]}]" for k in _expected],
    "stale_expectations": [f"{k[0]} [{k[2]}/{k[3]}@{k[4][0]}x{k[4][1]}]" for k in _stale],
    # THREE WORDS, NOT TWO. A bare "PASS" sitting next to `renders_failed: 2` is accurate and
    # coarse: it is the field a reader quotes out of context, and it should not be able to carry
    # "this surface has no failures" when two renders fail by design. So a run with nothing wrong
    # at all and a run whose only failures are the listed ones get different words.
    "verdict": "PASS" if (bad == 0 and not _expected)
               else ("PASS_WITH_KNOWN_FAILURES" if bad == 0 else "FAIL"),
    "axes": {
        "viewports_desktop": [f"{w}x{h}" for w, h in VIEWPORTS],
        "viewports_mobile": [f"{w}x{h}" for w, h in MOBILE_VIEWPORTS],
        "formats": FORMATS,
        "draft_states": STATES,
        # NAVIGATION IS AN AXIS NOW, and both halves of it are recorded: which states were
        # driven, and how many surfaces failed the one property asserted of them (the URL must
        # never name a board that is not on screen). A record that listed the states without
        # the failure count would read as coverage when it is a measurement of a known defect.
        "navigation_states": ["fresh load", "hash edit", "browser back", "browser forward"],
        "navigation_consistency_failures": NAV_BAD,
        # Still not covered, and named so this record cannot imply otherwise: returning to a
        # LIVE draft after leaving the page -- scroll position, which door was open, the clock.
        # Those need an app around the board; these prototypes are standalone pages.
        "navigation_states_not_covered": ["return to a live draft (scroll, open door, clock)"],
    },
}
(HERE / "_certification.json").write_text(json.dumps(_record, indent=1, sort_keys=True) + "\n")
print(f"certification record -> {HERE / '_certification.json'}"
      f"  (commit {(_record['source_commit'] or '?')[:9]}"
      f"{'' if _record['source_tree_clean'] else ', tree DIRTY: ' + ' '.join((_record['source_tree_dirty_paths'] or ['(git did not answer)'])[:3])})")
sys.exit(1 if bad else 0)
