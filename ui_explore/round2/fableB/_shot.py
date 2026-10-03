"""Render every built variant in every state at 1440x900: PNG + probes (page scroll, clipping,
console errors, minimum resident font size, rail window). Usage: python3 _shot.py [v1_ledger.html ...]"""
import glob, pathlib, sys
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).parent
OUT = HERE / "_shots"; OUT.mkdir(exist_ok=True)
files = sys.argv[1:] or sorted(str(p) for p in HERE.glob("v*.html") if "_src" not in p.name)
exe = (glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome") + glob.glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell"))[0]
PROBE = """() => {
  const r = {};
  r.docScroll = document.documentElement.scrollHeight > innerHeight + 1 || document.documentElement.scrollWidth > innerWidth + 1;
  const sc = document.querySelector('.screen'); r.screenH = Math.round(sc.getBoundingClientRect().height);
  const all = [...document.querySelectorAll('.screen *')].filter(el => !el.closest('.sheet'));
  r.clipped = all.filter(el => { const cs = getComputedStyle(el);
      return (cs.overflow === 'hidden' || cs.overflowY === 'hidden') && el.scrollHeight > el.clientHeight + 2 && !el.classList.contains('face') && !el.classList.contains('screen') && !el.classList.contains('pk') && !el.classList.contains('span') && !el.classList.contains('tick') && !el.classList.contains('railscroll'); })
    .map(el => (el.className.toString().slice(0, 36) || el.tagName) + ' ' + el.scrollHeight + '/' + el.clientHeight).slice(0, 8);
  r.scrollers = all.filter(el => { const cs = getComputedStyle(el); return /auto|scroll/.test(cs.overflowY) && el.scrollHeight > el.clientHeight + 2; })
    .map(el => (el.className.toString().slice(0, 30)) + ' ' + el.clientHeight + '/' + el.scrollHeight);
  const texts = all.filter(el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && getComputedStyle(el).display !== 'none');
  r.minFont = Math.min(...texts.map(el => parseFloat(getComputedStyle(el).fontSize)));
  r.under12 = texts.filter(el => parseFloat(getComputedStyle(el).fontSize) < 12).map(el => el.className.toString().slice(0, 30) + ':' + el.textContent.trim().slice(0, 20)).slice(0, 6);
  // text overflow: any element whose text is wider than its box (ellipsis or not), excluding sheets and the rail track
  const inScrolledOut = el => { const sc = el.closest('.list, .sc'); if (!sc) return false; const a = sc.getBoundingClientRect(), b = el.getBoundingClientRect(); return b.bottom > a.bottom + 1 || b.top < a.top - 1; };
  const leaf = all.filter(el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && getComputedStyle(el).display !== 'none' && !el.closest('.railscroll') && !el.closest('.topbar') && !el.closest('details:not([open])') && !inScrolledOut(el));
  r.textOverflow = leaf.filter(el => el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0).map(el => (el.className.toString().slice(0, 24) || el.tagName) + ':' + el.textContent.trim().slice(0, 22)).slice(0, 10);
  r.textOverflowCount = leaf.filter(el => el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0).length;
  // occlusion: the centre of every visible text leaf must hit-test to itself or its own subtree/ancestors
  const occ = []; for (const el of leaf) { const b = el.getBoundingClientRect(); if (b.width < 2 || b.height < 2) continue;
    if (b.bottom < 0 || b.top > innerHeight) { occ.push('OFFSCREEN ' + el.textContent.trim().slice(0, 22)); continue; }
    const hit = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2);
    if (hit && hit !== el && !el.contains(hit) && !hit.contains(el)) occ.push((el.className.toString().slice(0, 20) || el.tagName) + ':' + el.textContent.trim().slice(0, 20) + ' under ' + (hit.className.toString().slice(0, 20) || hit.tagName)); }
  r.occluded = occ.slice(0, 8); r.occludedCount = occ.length;
  // every list scroller: at late it must not scroll at all
  r.listScroll = [...document.querySelectorAll('.list')].filter(el => el.scrollHeight > el.clientHeight + 1).map(el => el.clientHeight + '/' + el.scrollHeight);
  const rs = document.querySelector('.railscroll');
  if (rs) { const rb = rs.getBoundingClientRect(); const vis = sel => { const n = rs.querySelector(sel); if (!n) return null; const b = n.getBoundingClientRect(); return b.left >= rb.left - 1 && b.right <= rb.right + 1; };
    r.rail = {now: vis('.pk.now'), next: vis('.pk.next'), namedVisible: [...rs.querySelectorAll('.pk.past')].filter(n => { const b = n.getBoundingClientRect(); return b.right > rb.left && b.left < rb.right; }).length,
              blankVisible: [...rs.querySelectorAll('.tick,.pk.future')].filter(n => { const b = n.getBoundingClientRect(); return b.right > rb.left && b.left < rb.right; }).length}; }
  return r; }"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe)
    for f in files:
        for state in (("early", "mid", "late", "early-notank", "mid-notank", "late-notank") if "v4" in f else ("early", "mid", "late")):
            pg = b.new_page(viewport={"width": 1440, "height": 900})
            errs = []
            pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
            pg.on("console", lambda m: errs.append(m.type + ": " + m.text) if m.type in ("error", "warning") else None)
            pg.goto("file://" + str(pathlib.Path(f).resolve()) + "#" + state, wait_until="domcontentloaded")
            pg.wait_for_timeout(900)
            out = OUT / f"{pathlib.Path(f).stem}_{state}.png"
            pg.screenshot(path=str(out), full_page=False)
            probe = pg.evaluate(PROBE)
            errs = [e for e in errs if "sleepercdn" not in e and "fonts.g" not in e and "net::ERR" not in e]
            fail = probe['docScroll'] or probe['clipped'] or probe['minFont'] < 12 or probe['occludedCount'] or probe['textOverflowCount'] or errs or (state == 'late' and probe['listScroll'])
            print(f"{'FAIL' if fail else 'ok  '} {pathlib.Path(f).name} #{state}: errors={errs or 'none'} docScroll={probe['docScroll']} minFont={probe['minFont']} clipped={probe['clipped']} textOverflow={probe['textOverflowCount']} {probe['textOverflow']} occluded={probe['occludedCount']} {probe['occluded']} listScroll={probe['listScroll']} rail={probe.get('rail')}")
            pg.close()
    b.close()
