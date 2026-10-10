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
VIEWPORTS = [tuple(int(n) for n in v.lower().split("x"))
             for v in __import__("os").environ.get("SHOOT_VIEWPORTS", "1440x900,1700x1100").split(",")]
# (file, query, [formats]) — v4 runs every format; the others are control-only
JOBS = []
if sys.argv[1:]:
    JOBS = [(f, "", FORMATS if "v4_" in f else [FORMATS[0]]) for f in sys.argv[1:]]
else:
    for f in sorted(str(p) for p in HERE.glob("v*.html") if "v3_" not in p.name):
        JOBS.append((f, "", FORMATS if "v4_" in f else [FORMATS[0]]))
    JOBS.append((str(HERE / "v4_doors.html"), "alldoors", ["HEAVY_IDP", "12T_ppr_K_DEF"]))
    JOBS.append((str(HERE / "v4_doors.html"), "notank", [FORMATS[0]]))
PROBE = """() => {
  const r = {};
  r.pageScroll = [document.documentElement.scrollWidth > innerWidth + 1, document.documentElement.scrollHeight > innerHeight + 1];
  const vis = el => { const cs = getComputedStyle(el); if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return false; const b = el.getBoundingClientRect(); if (!(b.width > 0 && b.height > 0 && b.bottom > 0 && b.top < innerHeight && b.right > 0 && b.left < innerWidth)) return false;
    // clipped away by an ancestor's overflow (a scroller's hidden rows, a clipped past row) is not visible
    const cx = b.left + Math.min(b.width, 40) / 2, cy = b.top + b.height / 2; let a = el.parentElement;
    while (a && a !== document.body) { const acs = getComputedStyle(a); if (acs.overflow !== 'visible' || acs.overflowY !== 'visible' || acs.overflowX !== 'visible') { const ab = a.getBoundingClientRect(); if (cx < ab.left || cx > ab.right || cy < ab.top || cy > ab.bottom) return false; } a = a.parentElement; } return true; };
  const inSheet = el => !!el.closest('.sheet,.hypbox');
  const all = [...document.querySelectorAll('.room *')].filter(el => !inSheet(el));
  const tag = el => (el.className && el.className.toString().split(' ')[0]) || el.tagName.toLowerCase();
  r.scrollers = all.filter(el => { const cs = getComputedStyle(el); return /(auto|scroll)/.test(cs.overflowY) && el.scrollHeight > el.clientHeight + 2; }).map(el => ({id: tag(el) + (el.dataset.list ? '[' + el.dataset.list + ']' : ''), more: el.dataset.more || null, moreVisible: !!(el.parentElement.querySelector(':scope > .more') && vis(el.parentElement.querySelector(':scope > .more')))}));
  r.badScrollers = r.scrollers.filter(s => !s.more || !s.moreVisible).map(s => s.id);
  r.clipped = all.filter(el => { const cs = getComputedStyle(el); return cs.overflow === 'hidden' && !/(auto|scroll)/.test(cs.overflowY) && el.scrollHeight > el.clientHeight + 2 && !el.classList.contains('face') && !el.classList.contains('room') && !el.classList.contains('past') && !el.classList.contains('scroll'); }).map(el => tag(el) + ' ' + el.scrollHeight + '/' + el.clientHeight).slice(0, 10);
  // text overflow: an element with its own text whose content is wider than its box and not scrollable
  r.textOverflow = all.filter(el => { if (!vis(el)) return false; const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if (!hasText) return false;
    const cs = getComputedStyle(el); const clipped = cs.overflow === 'hidden' || cs.overflowX === 'hidden' || cs.textOverflow === 'ellipsis' || (el.parentElement && getComputedStyle(el.parentElement).overflow === 'hidden');
    return clipped && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 2) && !el.closest('.past') && !el.classList.contains('face'); }).map(el => tag(el) + ': ' + el.textContent.trim().slice(0, 30)).slice(0, 12);
  // occlusion: centre of a text element resolves to an unrelated element
  r.occluded = all.filter(el => { if (!vis(el)) return false; const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if (!hasText) return false;
    const rects = el.getClientRects(); const b = rects.length ? rects[0] : el.getBoundingClientRect(); const x = Math.min(innerWidth - 1, Math.max(0, b.left + Math.min(b.width, 40) / 2)), y = Math.min(innerHeight - 1, Math.max(0, b.top + b.height / 2));
    const hit = document.elementFromPoint(x, y); if (!hit) return false; return !(hit === el || el.contains(hit) || hit.contains(el)) && !hit.classList.contains('scrim') && !hit.closest('.sheet'); }).map(el => tag(el) + ': ' + el.textContent.trim().slice(0, 30)).slice(0, 12);
  // cut off by the viewport: a text element not inside any scroller/clipper whose box runs past the fold
  const clippedByAncestor = el => { let a = el.parentElement; while (a && a !== document.body) { const acs = getComputedStyle(a); if (acs.overflow !== 'visible' || acs.overflowY !== 'visible') return a; a = a.parentElement; } return null; };
  r.cutOff = all.filter(el => { const cs = getComputedStyle(el); if (cs.display === 'none') return false; const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if (!hasText) return false;
    const b = el.getBoundingClientRect(); if (!(b.width > 0 && b.height > 0)) return false; const clip = clippedByAncestor(el); if (clip && !clip.classList.contains('room')) return false; return b.bottom > innerHeight + 1 || b.right > innerWidth + 1; }).map(el => tag(el) + ': ' + el.textContent.trim().slice(0, 30)).slice(0, 12);
  // captioned counts vs drawn rows
  r.counts = [...document.querySelectorAll('[data-list]')].filter(el => !inSheet(el)).map(el => { const rows = [...el.querySelectorAll('[data-row]')]; const drawn = rows.filter(x => vis(x)).length; return {list: el.dataset.list, rows: rows.length, drawn, more: el.dataset.more ? +el.dataset.more : 0}; });
  r.badCounts = r.counts.filter(c => c.drawn + c.more < c.rows).map(c => c.list + ' ' + c.drawn + '+' + c.more + '<' + c.rows);
  let min = 99, minEl = '';
  all.forEach(el => { if (!vis(el)) return; const t = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if (!t) return; const fs = parseFloat(getComputedStyle(el).fontSize); if (fs < min) { min = fs; minEl = tag(el) + ': ' + el.textContent.trim().slice(0, 20); } });
  r.minFont = [min, minEl];
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
          for W, H in VIEWPORTS:
            pg = b.new_page(viewport={"width": W, "height": H})
            errs = []
            pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
            pg.on("console", lambda m: errs.append(m.type + ": " + m.text) if m.type in ("error", "warning") else None)
            fpath = f; isv4 = "v4_" in f
            pg.goto("file://" + str(pathlib.Path(fpath).resolve()) + ("?" + q if q else "") + "#" + ((fmt + "/") if isv4 else "") + st, wait_until="load")
            pg.wait_for_timeout(600)
            out = SHOTS / f"{pathlib.Path(fpath).stem}{'_' + q if q else ''}{'_' + fmt if isv4 else ''}_{st}{'' if (W, H) == (1440, 900) else f'_{W}x{H}'}.png"
            pg.screenshot(path=str(out), full_page=False)
            r = pg.evaluate(PROBE)
            problems = []
            if errs: problems.append("errors " + json.dumps(errs))
            if any(r["pageScroll"]): problems.append("pageScroll")
            if r["clipped"]: problems.append("clipped " + json.dumps(r["clipped"]))
            if r["textOverflow"]: problems.append("textOverflow " + json.dumps(r["textOverflow"]))
            if r["occluded"]: problems.append("occluded " + json.dumps(r["occluded"]))
            if r["cutOff"]: problems.append("cut off by the viewport " + json.dumps(r["cutOff"]))
            if r["badScrollers"]: problems.append("scroller without affordance " + json.dumps(r["badScrollers"]))
            if r["badCounts"]: problems.append("count mismatch " + json.dumps(r["badCounts"]))
            if r["minFont"][0] < 12: problems.append("minFont " + json.dumps(r["minFont"]))
            if r["glyphOverlap"]: problems.append("text runs under a sibling " + json.dumps(r["glyphOverlap"]))
            if r.get("rail") and (not r["rail"]["now"] or r["rail"]["next"] is False): problems.append("rail " + json.dumps(r["rail"]))
            if r.get("nameFs"):
                NAME_FS.setdefault((pathlib.Path(fpath).name, q, fmt, (W, H)), {})[st] = r["nameFs"]
            bad += bool(problems)
            print(("!! " if problems else "ok ") + f"{pathlib.Path(fpath).name}{'?' + q if q else ''} [{fmt if isv4 else 'ctrl'}/{st}@{W}x{H}]  scrollers={[s['id'] + ':' + str(s['more']) for s in r['scrollers']]} counts={r['counts']} minFont={r['minFont'][0]} rail={r.get('rail')}")
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
