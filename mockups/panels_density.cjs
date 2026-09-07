// The density instrument for the panel group. For every page, in a real Chromium at 1,400 × 1,400
// with the 400px sidebar on, at rest (nothing open, no hover, no filter, scrolled to the top):
//   per [data-panel]  height, units ([data-unit] rows), units fully visible in the viewport
//                     above the collapsed dock, px / unit (the panel's row region height over
//                     its units), text-bearing elements / unit, buttons and inputs at rest,
//                     chrome above the first unit, min font
//   per kind          the same px / unit and elements / unit over rows of one data-kind, so a
//                     one-surface page can be compared with a per-kind panel
//   page              total height of the group, the page's scroll height, colour emoji
// Baseline rows come from panels_baseline_measure.json (the app's own panels, same columns).
// Shoots every page to mockups/panels_shots/. Written to panels_density.json.
const { chromium } = require("playwright");
const { writeFileSync, mkdirSync, existsSync, readFileSync } = require("node:fs");
const { resolve, basename } = require("node:path");

const MEASURE = () => {
  const visible = el => { const b = el.getBoundingClientRect(); return b.height > 0 && b.width > 0 && getComputedStyle(el).visibility !== "hidden"; };
  const ownText = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
  const dock = document.getElementById("dock").getBoundingClientRect();
  const viewBottom = Math.min(innerHeight, dock.top);
  const group = document.getElementById("group");
  const els = u => [...u.querySelectorAll("*")].filter(e => visible(e) && ownText(e)).length + (ownText(u) ? 1 : 0);
  const panels = [];
  for (const p of group.querySelectorAll("[data-panel]")) {
    const r = p.getBoundingClientRect();
    const units = [...p.querySelectorAll("[data-unit]")].filter(visible);
    const fully = units.filter(u => { const b = u.getBoundingClientRect(); return b.top >= 0 && b.bottom <= viewBottom; }).length;
    const region = p.classList.contains("rows") ? p : p.querySelector(".rows");
    const texts = [...p.querySelectorAll("*")].filter(e => visible(e) && ownText(e));
    const fonts = texts.map(e => parseFloat(getComputedStyle(e).fontSize));
    const kinds = {};
    for (const u of units) { const k = u.dataset.kind; kinds[k] = kinds[k] || { units: 0, px: 0, els: 0 }; kinds[k].units++; kinds[k].px += u.getBoundingClientRect().height; kinds[k].els += els(u); }
    for (const k in kinds) { kinds[k].pxPerUnit = +(kinds[k].px / kinds[k].units).toFixed(1); kinds[k].elementsPerUnit = +(kinds[k].els / kinds[k].units).toFixed(1); delete kinds[k].px; delete kinds[k].els; }
    panels.push({ panel: p.dataset.panel, open: p.dataset.open !== "false", height: Math.round(r.height), units: units.length, fullyVisible: fully,
      pxPerUnit: units.length && region ? +(region.getBoundingClientRect().height / units.length).toFixed(1) : null,
      elementsPerUnit: units.length ? +(units.map(els).reduce((a, b) => a + b, 0) / units.length).toFixed(1) : null,
      buttons: [...p.querySelectorAll("button")].filter(visible).filter(b => !b.classList.contains("ph")).length,
      inputs: [...p.querySelectorAll("input, textarea")].filter(visible).length,
      chromeAbove: units.length ? Math.round(units[0].getBoundingClientRect().top - r.top) : null,
      minFontPx: fonts.length ? +Math.min(...fonts).toFixed(1) : null, kinds });
  }
  const gr = group.getBoundingClientRect();
  const gtexts = [...group.querySelectorAll("*")].filter(e => visible(e) && ownText(e));
  const emoji = (group.innerText.match(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu) || []).length;
  return { panels, group: { top: Math.round(gr.top), height: Math.round(gr.height), textElements: gtexts.length, buttons: [...group.querySelectorAll("button")].filter(visible).length,
    inputs: [...group.querySelectorAll("input, textarea")].filter(visible).length, colourEmoji: emoji, minFontPx: +Math.min(...gtexts.map(e => parseFloat(getComputedStyle(e).fontSize))).toFixed(1) },
    page: { scrollHeight: document.documentElement.scrollHeight, viewBottom: Math.round(viewBottom) } };
};

(async () => {
  const files = process.argv.slice(2);
  const shots = resolve(__dirname, "panels_shots"); if (!existsSync(shots)) mkdirSync(shots);
  const out = [];
  const base = resolve(__dirname, "panels_baseline_measure.json");
  if (existsSync(base)) {
    const b = JSON.parse(readFileSync(base, "utf8"));
    for (const [name, m] of Object.entries(b.opened)) {
      const asShipped = b.asShipped[name];
      out.push({ file: "baseline (app.py)", panel: name, open: asShipped.open, height: asShipped.open ? asShipped.height : m.height, units: b.items[name], fullyVisible: null,
        pxPerUnit: +(m.bodyHeight / b.items[name]).toFixed(1), elementsPerUnit: +(m.textElements / b.items[name]).toFixed(1), buttons: m.buttons, inputs: m.inputs + m.selects,
        chromeAbove: null, minFontPx: m.minFontPx, note: asShipped.open ? "open as shipped" : `closed as shipped (${asShipped.height}px); numbers are the panel opened`, captionWords: m.captionWords, colourEmoji: m.colourEmoji });
    }
  }
  const browser = await chromium.launch();
  for (const file of files) {
    const page = await browser.newPage({ viewport: { width: 1400, height: 1400 } });
    await page.goto("file://" + resolve(file));
    await page.evaluate(() => { document.querySelectorAll("details").forEach(d => d.open = false); window.scrollTo(0, 0); });
    await page.mouse.move(0, 0);
    await page.waitForTimeout(350);
    const m = await page.evaluate(MEASURE);
    await page.screenshot({ path: `${shots}/${basename(file, ".html")}.png`, fullPage: true });
    await page.screenshot({ path: `${shots}/${basename(file, ".html")}_viewport.png` });
    for (const p of m.panels) out.push({ file: basename(file), ...p });
    out.push({ file: basename(file), panel: "(group)", ...m.group, page: m.page });
    console.log(`${basename(file)}  group ${m.group.height}px from y=${m.group.top}  text ${m.group.textElements}  buttons ${m.group.buttons}  inputs ${m.group.inputs}  emoji ${m.group.colourEmoji}  min ${m.group.minFontPx}px  page ${m.page.scrollHeight}px`);
    for (const p of m.panels) console.log(`  ${p.panel.padEnd(11)} ${p.open ? "open  " : "closed"} h ${String(p.height).padStart(4)}  units ${String(p.units).padStart(2)} visible ${String(p.fullyVisible).padStart(2)}  ${p.pxPerUnit === null ? "   —" : String(p.pxPerUnit).padStart(6)} px/unit  ${p.elementsPerUnit === null ? "—" : p.elementsPerUnit} el/unit  buttons ${p.buttons} inputs ${p.inputs}  chrome ${p.chromeAbove}  min ${p.minFontPx}  ${Object.entries(p.kinds).map(([k, v]) => `${k}:${v.units}×${v.pxPerUnit}px/${v.elementsPerUnit}el`).join(" ")}`);
    await page.close();
  }
  await browser.close();
  writeFileSync(resolve(__dirname, "panels_density.json"), JSON.stringify(out, null, 1));
})();
