"""Interaction pass: clicks, state switches, sheets — collect page errors."""
import glob, pathlib
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).parent
exe = (glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))[0]
FLOWS = {
 "v1_ledger.html": [".crow[data-id]:nth-child(3)", "#posToggle", ".door .bst", ".alt[data-id]", "[data-p='QB']", "[data-sheet='shRosters']", ".sheet[data-open='1'] [data-close]", ".pk.past", "[data-state='late']", ".crow[data-id]:nth-child(2)", "[data-state='early']", "#posToggle"],
 "v2_doors.html": ["[data-door='QB']", ".crow[data-id]:nth-child(5)", "[data-door='TE']", "[data-p='RB']", "[data-sheet='shBoard']", ".sheet[data-open='1'] [data-close]", "[data-state='late']", "[data-door='QB']", "[data-state='early']", "[data-door='WR']"],
 "v3_trio.html": [".crow.abc:nth-child(4) [data-slot='A']", "[data-clear='B']", ".crow.abc:nth-child(6)", "[data-sheet='shPos']", ".door .load [data-slot='C']", "[data-state='late']", ".crow.abc:nth-child(2) [data-slot='B']", "[data-state='early']", "[data-p='TE']"],
 "v4_cells.html": [".cell.same .alt[data-id]", ".cell.other .alt[data-id]", ".pcell[data-id]", "[data-sheet='shPool']", ".crow[data-id]:nth-child(6)", "[data-state='late']", ".cell.other .alt[data-id]", "[data-state='early']", ".pcell[data-id]"],
}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe)
    for f, flow in FLOWS.items():
        pg = b.new_page(viewport={"width": 1440, "height": 900}); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" and "net::" not in m.text else None)
        pg.goto("file://" + str((HERE / f).resolve()) + "#mid", wait_until="domcontentloaded"); pg.wait_for_timeout(500)
        done = []
        for sel in flow:
            el = pg.query_selector(sel)
            if not el: done.append("MISSING " + sel); continue
            el.evaluate("e => e.click()"); pg.wait_for_timeout(120); done.append("ok")
        probe = pg.evaluate("() => ({docScroll: document.documentElement.scrollHeight > innerHeight + 1, clipped: [...document.querySelectorAll('.screen *')].filter(el => !el.closest('.sheet') && getComputedStyle(el).overflow === 'hidden' && el.scrollHeight > el.clientHeight + 2 && !/face|pk|span|tick|railscroll|screen/.test(el.className)).map(el => el.className.toString().slice(0,30) + ' ' + el.scrollHeight + '/' + el.clientHeight).slice(0,6)})")
        print(f, "steps:", [d for d in done if d != "ok"] or "all ok", "errors:", errs or "none", "after:", probe)
        pg.screenshot(path=str(HERE / "_shots" / (f.replace(".html", "_interacted.png"))))
        pg.close()
    b.close()
