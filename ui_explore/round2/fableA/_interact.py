import glob, pathlib
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).resolve().parent; SH = HERE / "_shots"
STEPS = {
 "v1_ledger.html": [("click", "#posBtn", "v1_posgrid"), ("click", "[data-state=late]", None), ("click", ".row[data-id='12526']", None), ("click", "[data-state=mid]", None), ("click", ".alt[data-id]", None), ("click", "[data-work]", "v1_numbers")],
 "v2_lanes.html": [("click", "[data-lane=QB]", "v2_qb_focus"), ("click", "[data-state=late]", None), ("click", "[data-lane=TE]", "v2_late_te"), ("click", "[data-state=early]", None), ("click", ".rr[data-id]", None)],
 "v3_trio.html": [("click", "#byPos", "v3_bypos"), ("click", "[data-slot=C][data-id='4046']", None), ("click", "[data-state=late]", None), ("click", "[data-slot=A][data-id='4046']", "v3_late_pair"), ("click", "[data-state=early]", None)],
 "v4_doors.html": [("click", "[data-door=QB]", "v4_qb_open"), ("click", "[data-state=late]", "v4_late_resorted"), ("click", "[data-sheet=shAll]", "v4_sheet"), ("click", "[data-open=QB]", None), ("click", "[data-state=early]", None)],
}
with sync_playwright() as p:
    exe = (glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome") + glob.glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell"))[0]
    b = p.chromium.launch(executable_path=exe)
    for f, steps in STEPS.items():
        pg = b.new_page(viewport={"width": 1440, "height": 900}); errs = []
        pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
        pg.on("console", lambda m: errs.append(m.type + ": " + m.text) if m.type in ("error", "warning") else None)
        pg.goto("file://" + str(HERE / f) + "#mid", wait_until="load"); pg.wait_for_timeout(300)
        for kind, sel, shot in steps:
            el = pg.query_selector(sel)
            if not el: errs.append("MISSING " + sel); continue
            el.click(); pg.wait_for_timeout(550)
            if shot: pg.screenshot(path=str(SH / f"{shot}.png"))
        scroll = pg.evaluate("[document.documentElement.scrollWidth > innerWidth + 1, document.documentElement.scrollHeight > innerHeight + 1]")
        print(f, "errors:", errs or "none", "pageScroll:", scroll)
        pg.close()
    b.close()
