#!/usr/bin/env python3
"""Render every variant at each width in WIDTHS x 900, in each of the three states, and ASSERT on:
   - console / page errors, page scroll, self-clipping under overflow:hidden (round 1's probes)
   - text overflow: any visible text node whose box is wider/taller than its clip (ellipsis or hidden)
   - occlusion: a visible text element whose centre point resolves to an element that is neither
     itself, an ancestor nor a descendant (an opaque sibling painted over it)
   - scrollers: every region that scrolls must carry a visible "↓ scroll · N more" affordance
   - a captioned count ("N names") never exceeds the rows actually drawn + the "more" count
   - minimum resident font 12px
   Then a PNG per render, to be looked at."""
import sys, glob, pathlib, json
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).resolve().parent
SHOTS = HERE / "_shots"; SHOTS.mkdir(exist_ok=True)
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
MOBILE_VIEWPORTS = _vp(__import__("os").environ.get("SHOOT_MOBILE_VIEWPORTS", "390x844,360x800,430x932"))
SCROLL_BUDGET = float(__import__("os").environ.get("SHOOT_SCROLL_BUDGET", "2.5"))
TAP_FLOOR = 44
is_mobile = lambda f: pathlib.Path(f).name.startswith("m")
# (file, query, [formats]) — v4 runs every format; the others are control-only
def _jobs_for(f):
    """Every format on the surfaces that carry all of them (v4 and every mobile surface, which
    are the same board); the first format only on the controls."""
    if is_mobile(f):
        # `?collapsed` is the main display with no door open. It is reachable by URL rather than
        # only by tapping the X, so the suite can assert BOTH states without an interaction
        # script -- the state a reader returns to is as measurable as the one they open.
        return [(f, "", FORMATS), (f, "collapsed", FORMATS[:2])]
    return [(f, "", FORMATS if "v4_" in f else [FORMATS[0]])]

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
PROBE = """(opt) => {
  const r = {}, MOB = !!(opt && opt.mobile);
  r.pageScroll = [document.documentElement.scrollWidth > innerWidth + 1, document.documentElement.scrollHeight > innerHeight + 1];
  r.docH = document.documentElement.scrollHeight; r.vh = innerHeight;
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
    const hit = document.elementFromPoint(x, y); if (!hit) return false; return !(hit === el || el.contains(hit) || hit.contains(el)) && !hit.classList.contains('scrim') && !hit.closest('.sheet'); }).map(el => tag(el) + ': ' + el.textContent.trim().slice(0, 30)).slice(0, 12);
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
  const now = document.querySelector('.pk.now'), nxt = document.querySelector('.pk.next');
  if (now) { const nb = now.getBoundingClientRect(), xb = nxt ? nxt.getBoundingClientRect() : null; r.rail = {now: nb.left >= 0 && nb.right <= innerWidth, next: xb ? xb.left >= 0 && xb.right <= innerWidth : null, namedPast: [...document.querySelectorAll('.pk')].filter(p => { const b = p.getBoundingClientRect(); return b.left >= 0 && b.right <= innerWidth && !p.classList.contains('between') && !p.classList.contains('future') && !p.classList.contains('now') && !p.classList.contains('next'); }).length}; }
  return r; }"""
NAME_FS = {}   # (file, query, format, viewport) -> {state: computed name size}
with sync_playwright() as p:
    exe = (glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome") + glob.glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell"))[0]
    b = p.chromium.launch(executable_path=exe)
    bad = 0
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
                if screens > SCROLL_BUDGET: problems.append(f"scroll budget: {screens:.2f} screens of travel (document {r['docH']}px, deepest scroller {r.get('deepScroll')}px, viewport {r['vh']}px), over {SCROLL_BUDGET}")
                if r["tap"]: problems.append("tap target under 44px " + json.dumps(r["tap"]))
                if r["hClip"]: problems.append("runs off the right edge " + json.dumps(r["hClip"]))
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
            bad += bool(problems)
            print(("!! " if problems else "ok ") + f"{pathlib.Path(fpath).name}{'?' + q if q else ''} [{fmt if (isv4 or is_mobile(f)) else 'ctrl'}/{st}@{W}x{H}]  screens={screens:.2f} scrollers={[s['id'] + ':' + str(s['more']) for s in r['scrollers']]} counts={r['counts']} minFont={r['minFont'][0]} rail={r.get('rail')}")
            for pr in problems: print("     ", pr)
            pg.close()
    b.close()

# The door names scale with the viewport and are capped by the door's own width. Door
# width depends on door count, which comes from the league's startable slots and not
# from what has been drafted — so the size must not move as a draft progresses. Type
# that resizes between picks reads as a glitch. This asserts the invariant rather than
# trusting it: if doors are ever made to appear or disappear mid-draft, this fails here
# instead of the type quietly breathing on the owner's screen.
drift = {k: v for k, v in NAME_FS.items() if len(set(v.values())) > 1}
for k, v in sorted(drift.items(), key=lambda kv: str(kv[0])):
    print(f"!! name size moves between draft states  {k[0]}{'?' + k[1] if k[1] else ''} [{k[2]} @ {k[3][0]}x{k[3][1]}]  {v}")
bad += len(drift)
print(f"ok  name size is identical across draft states for all {len(NAME_FS)} (file, format, viewport) groups"
      if not drift else
      f"!! name size MOVES between draft states in {len(drift)} of {len(NAME_FS)} (file, format, viewport) groups")
sys.exit(1 if bad else 0)
