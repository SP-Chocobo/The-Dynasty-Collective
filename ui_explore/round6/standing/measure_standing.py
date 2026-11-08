#!/usr/bin/env python3
"""Render the standing pages and MEASURE the gates, rather than assume them.

Run from the repo root with the interpreter that carries Playwright (in this container that is
`/usr/bin/python3.13`; `python3` on PATH is 3.11 and has no Playwright):

    /usr/bin/python3.13 ui_explore/round6/standing/measure_standing.py

For each page at 1280x900 and 390x664 it reports: whether the document fits the viewport with no
vertical scroll (scrollHeight <= clientHeight), horizontal overflow, the minimum COMPUTED font size
of any element carrying text, the smallest tap target among buttons and links, console errors, and
the contrast of every non-text mark sampled from its rendered colour against the pixel ground it
sits on. It also opens every popover once and screenshots it, because a layer that was never
opened is a layer that was never looked at. Screenshots land beside this file in `shots/`.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

import browser_binary  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    raise SystemExit("playwright is not importable under this interpreter; see the docstring")

OUT = HERE / "shots"
OUT.mkdir(exist_ok=True)
VIEWPORTS = ((1280, 900, "desk"), (390, 664, "phone"))

PROBE = """() => {
  const d = document.documentElement;
  const lum = (c) => { const [r,g,b] = c.match(/[\\d.]+/g).slice(0,3).map(Number).map(v => { v/=255; return v<=.03928? v/12.92 : Math.pow((v+.055)/1.055, 2.4); }); return .2126*r+.7152*g+.0722*b; };
  const ratio = (a,b) => { const la=lum(a), lb=lum(b); return (Math.max(la,lb)+.05)/(Math.min(la,lb)+.05); };
  const groundOf = (el) => { let p = el.parentElement; while (p) { const bg = getComputedStyle(p).backgroundColor; if (bg && !bg.startsWith('rgba(0, 0, 0, 0)') && bg !== 'transparent') return bg; p = p.parentElement; } return getComputedStyle(document.body).backgroundColor; };
  let minf = 1e9, minEl = null;
  for (const el of document.querySelectorAll('body *')) {
    if (el.closest('[popover]')) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    let direct = false;
    for (const n of el.childNodes) if (n.nodeType === 3 && n.textContent.trim()) direct = true;
    if (!direct) continue;
    const f = parseFloat(cs.fontSize);
    if (f < minf) { minf = f; minEl = el.tagName + '.' + el.className + ' "' + el.textContent.trim().slice(0,28) + '"'; }
  }
  let minTap = 1e9, tapEl = null;
  for (const el of document.querySelectorAll('button, a')) {
    if (el.closest('[popover]')) continue;
    const r = el.getBoundingClientRect(); if (r.width === 0 || r.height === 0) continue;
    const m = Math.min(r.width, r.height);
    if (m < minTap) { minTap = m; tapEl = el.className + ' "' + el.textContent.trim().slice(0,20) + '"'; }
  }
  const marks = [];
  for (const el of document.querySelectorAll('.st, .chip i, .tile')) {
    if (el.closest('[popover]')) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none') continue;
    if (el.classList.contains('tile')) {
      const rail = getComputedStyle(el, '::after').backgroundColor;
      marks.push({what: 'rail ' + el.className, fg: rail, bg: cs.backgroundColor.includes('gradient') ? getComputedStyle(document.body).backgroundColor : (cs.backgroundColor === 'rgba(0, 0, 0, 0)' ? groundOf(el) : cs.backgroundColor)});
      continue;
    }
    const fg = cs.backgroundColor !== 'rgba(0, 0, 0, 0)' ? cs.backgroundColor : cs.borderTopColor;
    marks.push({what: el.className || el.tagName, fg, bg: groundOf(el)});
  }
  const seen = {};
  const out = [];
  for (const m of marks) { const k = m.what + '|' + m.fg; if (seen[k]) continue; seen[k] = 1; out.push({...m, ratio: Math.round(ratio(m.fg, m.bg)*100)/100}); }
  // NATURAL height: the page with its viewport-filling rules switched off, so the slack under the
  // fold is measured rather than hidden by a stretched 1fr row.
  const stage = document.querySelector('.stage');
  const saved = [document.body.style.minHeight, stage.style.gridTemplateRows];
  document.body.style.minHeight = '0'; stage.style.gridTemplateRows = 'auto auto auto auto';
  const natural = Math.ceil(document.body.getBoundingClientRect().height);  // html{height:100%} pins d.scrollHeight to the viewport
  document.body.style.minHeight = saved[0]; stage.style.gridTemplateRows = saved[1];
  return {fits: d.scrollHeight <= d.clientHeight, natural, slack: d.clientHeight - natural,
          scrollH: d.scrollHeight, clientH: d.clientHeight,
          scrollW: d.scrollWidth, clientW: d.clientWidth, minFont: minf, minEl, minTap: Math.round(minTap*10)/10, tapEl, marks: out};
}"""


def main(pages=None):
    pages = pages or [HERE / "standing.html", HERE / "standing_quiet.html"]
    report = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=browser_binary.find_chromium(), args=["--no-sandbox"])
        for path in pages:
            path = pathlib.Path(path)
            for w, h, tag in VIEWPORTS:
                ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
                pg = ctx.new_page()
                errs = []
                pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto("file://" + str(path.resolve()))
                pg.wait_for_timeout(1500)
                m = pg.evaluate(PROBE)
                m["console_errors"] = errs
                pg.screenshot(path=str(OUT / f"{path.stem}_{tag}.png"), full_page=False)
                # every popover, opened once and looked at
                ids = pg.evaluate("() => [...document.querySelectorAll('[popover]')].map(e => e.id)")
                for pid in ids:
                    opened = pg.evaluate(f"() => {{ const e = document.getElementById('{pid}'); try {{ e.showPopover(); return true; }} catch (x) {{ return String(x); }} }}")
                    if opened is True:
                        pg.wait_for_timeout(150)
                        pg.screenshot(path=str(OUT / f"{path.stem}_{tag}_pop_{pid}.png"), full_page=False)
                        pg.evaluate(f"() => document.getElementById('{pid}').hidePopover()")
                    else:
                        errs.append(f"popover {pid} failed to open: {opened}")
                report[f"{path.stem}@{w}x{h}"] = m
                ctx.close()
        browser.close()
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main([pathlib.Path(a) for a in sys.argv[1:]] or None))
