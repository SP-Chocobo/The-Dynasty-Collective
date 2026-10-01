// The density instrument for the docks. For every page × level, in a real Chromium at
// 1,400 × 1,400 with the 400px sidebar on (dock 1,000px wide, as in the app), at rest:
//   height / cap     the dock's rendered height against its tier's computed max-height, and
//                    whether the dock ITSELF overflows (scrollHeight > clientHeight) — a dock
//                    that scrolls as a whole has failed; only its .scroll region may scroll
//   units            [data-unit] elements rendered (a row, a bubble, a seat column)
//   fully visible    units whose box is inside the dock's visible box AND inside their own
//                    scroll region's visible box
//   px / unit        the scroll region's scrollHeight over the units it holds (the columns
//                    variant: the tallest column's scrollHeight, since the columns are side
//                    by side, over 1 — reported as such)
//   elements / unit  visible text-bearing elements per unit
//   chrome above     px from the dock's top to the first unit's top
//   facts            [data-fact] elements on a collapsed line (the named facts it carries)
//   min font         the smallest font-size of any visible text-bearing element in the dock
// Also shoots every page × level to mockups/dock_shots/. Written to dock_density.json.
const { chromium } = require("playwright");
const { writeFileSync, mkdirSync, existsSync, readFileSync } = require("node:fs");
const { resolve, basename } = require("node:path");

const MEASURE = () => {
  const dock = document.getElementById("dock");
  const dr = dock.getBoundingClientRect();
  const visible = el => { const b = el.getBoundingClientRect(); return b.height > 0 && b.width > 0 && getComputedStyle(el).visibility !== "hidden"; };
  const ownText = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
  const cap = Math.round(parseFloat(getComputedStyle(dock).maxHeight));
  const units = [...dock.querySelectorAll("[data-unit]")].filter(visible);
  const region = [...dock.querySelectorAll(".scroll, .cols")].find(r => r.querySelector("[data-unit]")) || null;
  const inside = (b, r) => b.top >= r.top - 1 && b.bottom <= r.bottom + 1;
  let fully = 0;
  for (const u of units) {
    const b = u.getBoundingClientRect();
    const sr = u.closest(".scroll") || region; const rr = sr ? sr.getBoundingClientRect() : dr;
    if (inside(b, dr) && inside(b, rr)) fully++;
  }
  const elementsPer = units.length ? units.map(u => [...u.querySelectorAll("*")].filter(e => visible(e) && ownText(e)).length + (ownText(u) ? 1 : 0)).reduce((a, b) => a + b, 0) / units.length : null;
  let pxPer = null, note = "";
  if (units.length) {
    if (dock.querySelector(".cols")) { pxPer = Math.max(...units.map(u => { const body = u.querySelector(".body") || u; return body.scrollHeight + (u.querySelector(".head") ? u.querySelector(".head").getBoundingClientRect().height : 0); })); note = "tallest column"; }
    else { const sr = region || dock; pxPer = sr.scrollHeight / units.length; }
  }
  const chromeAbove = region ? Math.round(region.getBoundingClientRect().top - dr.top) : (units.length ? Math.round(Math.min(...units.map(u => u.getBoundingClientRect().top)) - dr.top) : null);
  const facts = document.documentElement.dataset.level === "collapsed" ? dock.querySelectorAll("[data-fact], .seat, .age, .conv, .mark").length : null;
  const texts = [...dock.querySelectorAll("*")].filter(e => visible(e) && ownText(e));
  const minFont = Math.min(...texts.map(e => parseFloat(getComputedStyle(e).fontSize)));
  return { dockHeight: Math.round(dr.height), cap, overflows: dock.scrollHeight > dock.clientHeight + 1, dockScrollHeight: dock.scrollHeight,
           units: units.length, fullyVisible: fully, pxPerUnit: pxPer === null ? null : +pxPer.toFixed(1), pxNote: note,
           elementsPerUnit: elementsPer === null ? null : +elementsPer.toFixed(1), chromeAbove, facts, minFontPx: +minFont.toFixed(1),
           textBearing: texts.length, buttons: [...dock.querySelectorAll("button")].filter(visible).length };
};

(async () => {
  const files = process.argv.slice(2);
  const shots = resolve(__dirname, "dock_shots"); if (!existsSync(shots)) mkdirSync(shots);
  const out = [];
  // The baseline rows: the app's own dock, from the live probe, in the same columns.
  const base = resolve(__dirname, "dock_baseline_measure.json");   // the live app's dock, from dock_probe_asis.cjs
  if (existsSync(base)) {
    const b = JSON.parse(readFileSync(base, "utf8"));
    out.push({ file: "baseline (app.py dock)", level: "collapsed", dockHeight: b.collapsed_n0.dockHeight, cap: 126, overflows: false, units: 1, fullyVisible: 1, pxPerUnit: null, elementsPerUnit: 2, chromeAbove: 44, facts: 2, minFontPx: 14 });
    for (const lv of ["partial", "full"]) {
      const m = b[lv];
      out.push({ file: "baseline (app.py dock)", level: lv, dockHeight: m.dockHeight, cap: lv === "partial" ? 560 : 1316, overflows: m.dockScrollHeight > m.dockHeight + 1, units: m.messages, fullyVisible: m.fullyVisible, pxPerUnit: m.pxPerMessage, elementsPerUnit: m.elementsPerMessage, chromeAbove: m.chromeAboveRegion, facts: null, minFontPx: 14 });
    }
  }
  const browser = await chromium.launch();
  for (const file of files) for (const level of ["collapsed", "partial", "full"]) {
    const page = await browser.newPage({ viewport: { width: 1400, height: 1400 } });
    await page.goto("file://" + resolve(file));
    await page.evaluate(l => { document.querySelectorAll("details").forEach(d => d.open = false); setLevel(l); }, level);
    await page.mouse.move(0, 0);
    await page.waitForTimeout(350);
    const m = await page.evaluate(MEASURE);
    await page.screenshot({ path: `${shots}/${basename(file, ".html")}_${level}.png` });
    out.push({ file: basename(file), level, ...m });
    console.log(`${basename(file).padEnd(20)} ${level.padEnd(9)} h ${String(m.dockHeight).padStart(4)}/${m.cap}${m.overflows ? " OVERFLOWS" : ""}  units ${String(m.units).padStart(2)} visible ${String(m.fullyVisible).padStart(2)}  ${m.pxPerUnit === null ? "   —  " : String(m.pxPerUnit).padStart(6)} px/unit${m.pxNote ? " (" + m.pxNote + ")" : ""}  ${m.elementsPerUnit === null ? "—" : m.elementsPerUnit} el/unit  chrome ${m.chromeAbove === null ? "—" : m.chromeAbove}px  facts ${m.facts === null ? "—" : m.facts}  min ${m.minFontPx}px  buttons ${m.buttons}`);
    await page.close();
  }
  await browser.close();
  writeFileSync(resolve(__dirname, "dock_density.json"), JSON.stringify(out, null, 1));
})();
