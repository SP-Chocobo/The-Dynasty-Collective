// The live app's own panel group, measured at 1,400 × 1,400 in a real Chromium, against the
// seeded scratch copy (mockups/panels_probe_app.py on :8766). Written to
// mockups/panels_baseline_measure.json; screenshots to mockups/panels_shots/.
//
// Per panel (the five st.expanders: Pinned Messages, Decision Log, Bot Research, Active
// Objectives, Archive), two states:
//   as shipped   the page at rest exactly as app.py leaves it -- only Active Objectives open
//   opened       that expander opened, everything else as shipped
// and per state: the expander's height, the items it holds (a pin, a decision row, a
// finding/comparison row, an objective, an archived objective), px per item, visible
// text-bearing elements per item, buttons and inputs at rest, the header text and its count,
// the caption's word count, and the smallest font in it.
const { chromium } = require("playwright");
const { writeFileSync, mkdirSync, existsSync } = require("node:fs");
const { resolve } = require("node:path");

const PORT = process.env.PANELS_PORT || 8766;
const OUT = resolve(__dirname, "panels_baseline_measure.json");
const SHOTS = resolve(__dirname, "panels_shots");
const PANELS = ["Pinned Messages", "Decision Log", "Bot Research", "Active Objectives", "Archive"];
const ITEMS = { "Pinned Messages": 2, "Decision Log": 6, "Bot Research": 8, "Active Objectives": 4, "Archive": 3 };

async function settle(page) {
  await page.waitForSelector('[data-testid="stExpander"]', { timeout: 90000 });
  await page.waitForFunction(() => !document.querySelector('[data-testid="stStatusWidget"]'), null, { timeout: 90000 }).catch(() => {});
  await page.waitForTimeout(1500);
  await page.mouse.move(0, 0);
}

const MEASURE = (names) => {
  const visible = el => { const b = el.getBoundingClientRect(); return b.height > 0 && b.width > 0 && getComputedStyle(el).visibility !== "hidden"; };
  const ownText = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
  const exps = [...document.querySelectorAll('[data-testid="stExpander"]')];
  const out = {};
  for (const name of names) {
    const ex = exps.find(e => (e.querySelector("summary") || e).innerText.includes(name));
    if (!ex) { out[name] = { present: false }; continue; }
    const summary = ex.querySelector("summary");
    const details = ex.querySelector("details");
    const open = details ? details.open : null;
    const r = ex.getBoundingClientRect();
    const body = [...ex.querySelectorAll('[data-testid="stExpanderDetails"]')][0] || null;
    const bodyR = body && open ? body.getBoundingClientRect() : null;
    const texts = [...ex.querySelectorAll("*")].filter(e => visible(e) && ownText(e));
    const buttons = [...ex.querySelectorAll("button")].filter(visible).filter(b => !summary.contains(b));
    const inputs = [...ex.querySelectorAll("input, textarea")].filter(visible);
    const selects = [...ex.querySelectorAll('[data-testid="stSelectbox"]')].filter(visible);
    const caption = ex.querySelector('[data-testid="stCaptionContainer"]');
    const emoji = (ex.innerText.match(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu) || []).length;
    const fonts = texts.map(e => parseFloat(getComputedStyle(e).fontSize));
    const dataframes = [...ex.querySelectorAll('[data-testid="stDataFrame"]')].filter(visible);
    out[name] = {
      present: true, open, headerText: summary.innerText.trim().replace(/\s+/g, " "),
      top: Math.round(r.top + window.scrollY), height: Math.round(r.height),
      bodyHeight: bodyR ? Math.round(bodyR.height) : 0,
      textElements: texts.length, buttons: buttons.length, inputs: inputs.length, selects: selects.length,
      dataframes: dataframes.length, dataframeHeights: dataframes.map(d => Math.round(d.getBoundingClientRect().height)),
      captionWords: caption ? caption.innerText.trim().split(/\s+/).length : 0,
      colourEmoji: emoji, minFontPx: fonts.length ? +Math.min(...fonts).toFixed(1) : null,
    };
  }
  const main = document.querySelector('[data-testid="stMain"]') || document.body;
  out._page = { scrollHeight: document.documentElement.scrollHeight, viewport: innerHeight,
    firstPanelTop: Math.min(...Object.values(out).filter(o => o.present).map(o => o.top)),
    lastPanelBottom: Math.max(...Object.values(out).filter(o => o.present).map(o => o.top + o.height)) };
  return out;
};

(async () => {
  if (!existsSync(SHOTS)) mkdirSync(SHOTS);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1400, height: 1400 } });
  await page.goto(`http://localhost:${PORT}/`, { waitUntil: "networkidle" });
  await settle(page);
  const result = { note: "the app's own panel group, seeded with mockups/panels_data.py, Import Audit view, dock collapsed, 1400x1400", items: ITEMS };
  result.asShipped = await page.evaluate(MEASURE, PANELS);
  await page.screenshot({ path: `${SHOTS}/baseline_as_shipped.png`, fullPage: true });
  // Open each panel in turn (leaving the others as shipped) and measure it opened.
  result.opened = {};
  for (const name of PANELS) {
    const wasOpen = result.asShipped[name] && result.asShipped[name].open;
    if (!wasOpen) {
      const summ = page.locator('[data-testid="stExpander"] summary', { hasText: name }).first();
      await summ.click();
      await page.waitForTimeout(900);
      await page.mouse.move(0, 0);
    }
    const m = await page.evaluate(MEASURE, [name]);
    result.opened[name] = m[name];
    const ex = page.locator('[data-testid="stExpander"]', { hasText: name }).first();
    await ex.scrollIntoViewIfNeeded();
    await page.waitForTimeout(200);
    await ex.screenshot({ path: `${SHOTS}/baseline_${name.toLowerCase().replace(/ /g, "_")}_open.png` });
    if (!wasOpen) {
      const summ = page.locator('[data-testid="stExpander"] summary', { hasText: name }).first();
      await summ.click();
      await page.waitForTimeout(500);
    }
  }
  // Specific checks behind the defect list.
  result.checks = await page.evaluate(() => {
    const exps = [...document.querySelectorAll('[data-testid="stExpander"]')];
    const find = n => exps.find(e => e.innerText.includes(n));
    const pins = find("Pinned Messages"), dec = find("Decision Log");
    const out = {};
    out.pinnedHeader = pins ? pins.querySelector("summary").innerText.trim() : null;
    out.pinnedCaptionsEndWithEllipsis = pins ? [...pins.querySelectorAll('[data-testid="stCaptionContainer"]')].map(c => c.innerText.trim().slice(-40)) : null;
    out.pinnedShowsRecommendation = pins ? /RECOMMENDATION/.test(pins.innerText) : null;
    out.objectivesHeader = (find("Active Objectives") || { innerText: "" }).querySelector ? find("Active Objectives").querySelector("summary").innerText.trim() : null;
    out.dockHeaderCount = (document.querySelector(".st-key-debate_dock") || { innerText: "" }).innerText.replace(/\s+/g, " ").slice(0, 200);
    out.researchHeader = find("Bot Research") ? find("Bot Research").querySelector("summary").innerText.trim() : null;
    return out;
  });
  // The Decision Log's outcome picker: open it and read the options against the row count.
  const decOpen = page.locator('[data-testid="stExpander"] summary', { hasText: "Decision Log" }).first();
  await decOpen.click(); await page.waitForTimeout(800);
  const sel = page.locator('[data-testid="stExpander"]', { hasText: "Decision Log" }).locator('[data-testid="stSelectbox"] input').first();
  await sel.click(); await page.waitForTimeout(800);
  result.checks.decisionPickerOptions = await page.evaluate(() => [...document.querySelectorAll('[role="listbox"] [role="option"], [data-baseweb="menu"] li')].map(o => o.innerText.trim()));
  await page.keyboard.press("Escape"); await page.waitForTimeout(300);
  result.checks.outcomeDefault = await page.evaluate(() => { const ex = [...document.querySelectorAll('[data-testid="stExpander"]')].find(e => e.innerText.includes("Decision Log")); const sels = [...ex.querySelectorAll('[data-testid="stSelectbox"]')]; return sels.map(s => s.innerText.trim().replace(/\s+/g, " ")); });
  result.checks.decisionTableCells = await page.evaluate(() => { const ex = [...document.querySelectorAll('[data-testid="stExpander"]')].find(e => e.innerText.includes("Decision Log")); const df = ex.querySelector('[data-testid="stDataFrame"]'); return df ? df.innerText.replace(/\s+/g, " ").slice(0, 600) : null; });
  await page.screenshot({ path: `${SHOTS}/baseline_decision_log_open_full.png`, fullPage: true });
  await browser.close();
  writeFileSync(OUT, JSON.stringify(result, null, 1));
  for (const [state, m] of [["as shipped", result.asShipped], ["opened", result.opened]]) {
    console.log(`\n== ${state}`);
    for (const n of PANELS) {
      const p = m[n]; if (!p || !p.present) { console.log(`${n.padEnd(18)} absent`); continue; }
      const items = ITEMS[n];
      console.log(`${n.padEnd(18)} ${p.open ? "open  " : "closed"} h ${String(p.height).padStart(4)}px  body ${String(p.bodyHeight).padStart(4)}px  ${p.open ? (p.bodyHeight / items).toFixed(1).padStart(6) : "     —"} px/item  ${p.open ? (p.textElements / items).toFixed(1) : "—"} el/item  buttons ${p.buttons}  inputs ${p.inputs}  selects ${p.selects}  df ${p.dataframes} ${JSON.stringify(p.dataframeHeights)}  caption ${p.captionWords}w  emoji ${p.colourEmoji}  min ${p.minFontPx}px  · ${p.headerText}`);
    }
  }
  console.log("\npage", JSON.stringify(result.asShipped._page));
  console.log("checks", JSON.stringify(result.checks, null, 1));
})();
