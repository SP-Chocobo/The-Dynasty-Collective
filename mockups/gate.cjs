// The gate, executed in a real Chromium via Playwright -- not a DOM stub. Run through
// `python3 mockups/smoke.py`, which sets NODE_PATH so `playwright` resolves. CommonJS on
// purpose: an ES module's `import` ignores NODE_PATH, a CommonJS `require` honours it.
//
// Per page, in BOTH leader orders (as built; then with the unpriced fixture promoted):
//   G1  the unpriced fixture row: EVERY [data-field] cell in the row and in its opened receipt
//       carries the hatched .absent mark with a non-empty title. Per field, not "one anywhere".
//   G2  the measured-zeros row: EVERY [data-field] cell reads as a zero (0 / 0.0 / 0% / free),
//       in the row and in its receipt. The negative row keeps its sign.
//   --  no `null`, `NaN` or `undefined` in any visible text or any title attribute.
//   --  height at rest <= 1400px (the production iframe's cap); expanded height reported.
//   --  keyboard: the first row is focusable, ArrowDown moves focus, Enter opens (aria-expanded
//       and a receipt with >= 12 fields, each with a unit), Escape closes.
//   --  necessity word >= 11.2px (.7rem) on every row.
//   G7  under emulated prefers-reduced-motion every animation and transition duration is ~0.
const { chromium } = require("playwright");
const { readFileSync } = require("node:fs");
const { resolve } = require("node:path");

(async () => {

const files = process.argv.slice(2);
const CAP = 1400;
const fails = [];
const fail = (f, m) => fails.push(`${f}: ${m}`);
const ZERO = /^(-?0(\.0+)?%?|free)(\s|$|·)/;

const browser = await chromium.launch();
for (const file of files) {
  const url = "file://" + resolve(file);
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const errors = [];
  page.on("pageerror", e => errors.push(String(e)));
  await page.goto(url);
  const html = readFileSync(file, "utf8").toLowerCase();
  for (const w of ["draft sharks", "draftsharks", "draft_sharks"]) if (html.includes(w)) fail(file, `names the vendor (${w})`);

  for (const promote of [false, true]) {
    const tag = promote ? "unpriced leader" : "as built";
    await page.reload();   // a clean page per pass: no fold or row state carried over
    if (promote) await page.click("#btn-leader");
    await page.evaluate(() => { document.querySelectorAll("details").forEach(d => d.open = false); });

    const visible = await page.evaluate(() => document.body.innerText + " " + [...document.querySelectorAll("[title]")].map(e => e.getAttribute("title")).join(" "));
    for (const t of ["null", "NaN", "undefined"]) if (new RegExp(`(?<![A-Za-z_])${t}(?![A-Za-z_])`).test(visible)) fail(file, `[${tag}] rendered ${t}`);

    const restHeight = await page.evaluate(() => document.documentElement.scrollHeight);
    if (restHeight > CAP) fail(file, `[${tag}] height at rest ${restHeight}px > ${CAP}px`);

    // Open every fixture row in turn and check its fields.
    for (const [id, kind] of [["fx-unpriced", "absent"], ["fx-zeros", "zero"], ["296", "negative"]]) {
      const row = page.locator(`.row[data-id="${id}"]`);
      if (await row.count() === 0) {
        // The row may be behind the fold.
        const fold = page.locator(".fold");
        if (await fold.count()) await fold.first().click();
      }
      if (await row.count() === 0) { fail(file, `[${tag}] fixture row ${id} not rendered`); continue; }
      // Click the card's visible top band, as a person does; a stacked deck's geometric centre
      // is under the next card at rest and a synthetic centre-click is intercepted there.
      await row.first().click({ position: { x: 40, y: 18 } });
      const cells = await page.locator(`.row[data-id="${id}"] [data-field]`).evaluateAll(els => els.map(e => ({
        field: e.dataset.field, text: e.innerText.trim(),
        absent: !!e.querySelector(".absent") || e.classList.contains("absent"),
        title: (e.querySelector(".absent") || e).getAttribute("title") || "",
      })));
      if (cells.length < 12) fail(file, `[${tag}] row ${id}: only ${cells.length} data-field cells after opening`);
      for (const c of cells) {
        if (kind === "absent" && !(c.absent && c.title.length > 10)) fail(file, `[${tag}] unpriced row field ${c.field} is not a titled absent mark (${JSON.stringify(c.text)})`);
        if (kind === "zero" && !ZERO.test(c.text)) fail(file, `[${tag}] zeros row field ${c.field} does not read as a zero (${JSON.stringify(c.text)})`);
        if (kind === "negative" && c.field === "tav" && !c.text.startsWith("-2")) fail(file, `[${tag}] negative row lost its sign (${JSON.stringify(c.text)})`);
      }
      await row.first().click({ position: { x: 40, y: 18 } }); // close
    }

    // Keyboard model.
    await page.evaluate(() => { const r = document.querySelector('.row[role="option"][tabindex="0"]'); r && r.focus(); });
    const first = await page.evaluate(() => document.activeElement && document.activeElement.dataset.id);
    if (!first) fail(file, `[${tag}] no focusable row`);
    await page.keyboard.press("ArrowDown");
    const second = await page.evaluate(() => document.activeElement && document.activeElement.dataset.id);
    if (!second || second === first) fail(file, `[${tag}] ArrowDown did not move focus`);
    await page.keyboard.press("Enter");
    const opened = await page.evaluate(() => { const r = document.activeElement; return r && r.getAttribute("aria-expanded"); });
    if (opened !== "true") fail(file, `[${tag}] Enter did not open the focused row`);
    const receiptOk = await page.evaluate(() => {
      const r = document.activeElement; const lines = [...r.querySelectorAll(".receipt [data-field]")];
      return lines.length >= 12 && lines.every(l => (l.closest(".val") && l.closest(".val").nextElementSibling && l.closest(".val").nextElementSibling.innerText.trim().length > 0));
    });
    if (!receiptOk) fail(file, `[${tag}] the opened row's receipt lacks 12 unit-bearing fields`);
    const expandedHeight = await page.evaluate(() => document.documentElement.scrollHeight);
    await page.keyboard.press("Escape");
    const closed = await page.evaluate(() => { const r = document.activeElement; return r && r.getAttribute("aria-expanded"); });
    if (closed !== "false") fail(file, `[${tag}] Escape did not close the row`);

    const necPx = await page.locator(".row .nec").evaluateAll(els => Math.min(...els.map(e => parseFloat(getComputedStyle(e).fontSize))));
    if (!(necPx >= 11.2)) fail(file, `[${tag}] necessity word is ${necPx}px, below .7rem`);
    console.log(`ok   ${file} [${tag}] rest ${restHeight}px, one row expanded ${expandedHeight}px`);
  }

  // G7. Emulate the OS preference and read every animation/transition duration.
  await page.emulateMedia({ reducedMotion: "reduce" });
  const motion = await page.evaluate(() => {
    const bad = [];
    for (const el of document.querySelectorAll("*")) {
      for (const pseudo of [null, "::before", "::after"]) {
        const cs = getComputedStyle(el, pseudo);
        for (const p of ["animationDuration", "transitionDuration"]) {
          const d = cs[p]; if (!d || d === "0s") continue;
          const ms = d.split(",").map(x => x.trim().endsWith("ms") ? parseFloat(x) : parseFloat(x) * 1000);
          if (ms.some(v => v > 1)) bad.push(`${el.className || el.tagName}${pseudo || ""} ${p}=${d}`);
        }
      }
    }
    return bad.slice(0, 5);
  });
  if (motion.length) fail(file, `motion survives prefers-reduced-motion: ${motion.join("; ")}`);
  if (errors.length) fail(file, `page errors: ${errors.join(" | ")}`);
  await page.close();
}
await browser.close();
for (const f of fails) console.log("FAIL " + f);
process.exit(fails.length ? 1 : 0);
})();
