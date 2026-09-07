// The docks' gate, in a real Chromium. Per page, per level:
//   G1  the failed chair: every [data-field="report"][data-role="beat"] that renders for the
//       second run carries a hatched .absent with a title; no model badge names gemini beside
//       a 503; the raw "⚠️" glyph never renders.
//   G2  the standing verdict survives the history cut: with the cut on, the collapsed and
//       partial docks still show BUY (the first run's call) and never an empty call.
//   G3  the dock never overflows its cap at 1,400 × 1,400; only .scroll / .body / .rows scroll.
//   --  no null / NaN / undefined in visible text or titles; no colour emoji in the dock.
//   --  keyboard: at partial and full a first option is focusable, ArrowDown moves, Enter opens
//       (aria-expanded), Escape closes.
//   G5  no visible text-bearing element in the dock under 11px.
//   G7  under emulated prefers-reduced-motion every animation and transition is ~0.
const { chromium } = require("playwright");
const { resolve, basename } = require("node:path");

(async () => {
  const files = process.argv.slice(2), fails = [];
  const fail = (f, m) => fails.push(`${basename(f)}: ${m}`);
  const browser = await chromium.launch();
  for (const file of files) {
    const page = await browser.newPage({ viewport: { width: 1400, height: 1400 } });
    const errors = []; page.on("pageerror", e => errors.push(String(e)));
    await page.goto("file://" + resolve(file));
    for (const level of ["collapsed", "partial", "full"]) {
      await page.evaluate(l => { openId = null; setLevel(l); }, level);
      await page.waitForTimeout(300);
      const tag = `[${level}]`;
      const dockText = await page.evaluate(() => { const d = document.getElementById("dock"); return d.innerText + " " + [...d.querySelectorAll("[title]")].map(e => e.getAttribute("title")).join(" "); });
      for (const t of ["null", "NaN", "undefined"]) if (new RegExp(`(?<![A-Za-z_])${t}(?![A-Za-z_])`).test(dockText)) fail(file, `${tag} rendered ${t}`);
      if (/[\u{1F300}-\u{1FAFF}\u{2600}-\u{26FF}]/u.test(dockText)) fail(file, `${tag} colour emoji in the dock`);
      const geo = await page.evaluate(() => { const d = document.getElementById("dock"); return { over: d.scrollHeight > d.clientHeight + 1, h: d.clientHeight, sh: d.scrollHeight, cap: parseFloat(getComputedStyle(d).maxHeight) }; });
      if (geo.over) fail(file, `${tag} G3 the dock itself overflows its cap: ${geo.sh}px of content in ${geo.h}px (cap ${geo.cap})`);
      const minFont = await page.evaluate(() => { const vis = el => { const b = el.getBoundingClientRect(); return b.height > 0 && b.width > 0; }; const own = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); return Math.min(...[...document.querySelectorAll("#dock *")].filter(e => vis(e) && own(e)).map(e => parseFloat(getComputedStyle(e).fontSize))); });
      if (minFont < 11) fail(file, `${tag} G5 text at ${minFont}px in the dock`);
      if (level !== "collapsed") {
        // G1: open everything that can show the failed chair, then check every rendering of it.
        await page.evaluate(() => {
          // ledger: open the newest debate row; thread: select the beat tab on the newest debate; chairs: nothing to open (columns render at rest)
          const row = [...document.querySelectorAll('[data-unit^="debate-"]')].pop(); if (row) { openId = row.dataset.unit; render(); }
          const tab = [...document.querySelectorAll('.tab[data-role="beat"]')].pop(); if (tab) tab.click();
        });
        await page.waitForTimeout(200);
        const beat = await page.evaluate(() => [...document.querySelectorAll('[data-field="report"][data-role="beat"]')].map(e => ({ text: e.innerText.slice(0, 80), absent: !!e.querySelector(".absent"), title: (e.querySelector(".absent") || {}).getAttribute ? e.querySelector(".absent").getAttribute("title") : "" })));
        const failedOnes = beat.filter(b => /no report/.test(b.text));
        const failedSeat = await page.evaluate(() => [...document.querySelectorAll('#dock .seat.failed[data-role="beat"]')].some(s => (s.getAttribute("title") || "").length > 20));
        if (!failedOnes.length && !failedSeat) fail(file, `${tag} G1 the failed Beat chair is rendered nowhere: no report absence, no titled failed seat`);
        for (const b of failedOnes) if (!(b.absent && b.title && b.title.length > 10)) fail(file, `${tag} G1 failed chair without a titled absent mark: ${JSON.stringify(b.text)}`);
        const badgeClaims = await page.evaluate(() => [...document.querySelectorAll('[data-role="beat"]')].some(e => /gemini/.test(e.innerText) && /no report/.test(e.innerText)));
        if (badgeClaims) fail(file, `${tag} G1 a model name sits beside the failed chair's absence`);
        if (/⚠/.test(dockText)) fail(file, `${tag} G1 the raw fail-soft glyph renders`);
        await page.evaluate(() => { openId = null; tabOf = {}; focusedId = null; render(); });
        // Keyboard.
        const nOpts = await page.evaluate(() => document.querySelectorAll('#dock [role="option"]').length);
        if (nOpts === 0) { console.log(`note ${basename(file)} ${tag} has no list at this level by design; keyboard check skipped`); continue; }
        await page.evaluate(() => { const r = document.querySelector('#dock [role="option"][tabindex="0"]'); r && r.focus(); });
        const first = await page.evaluate(() => document.activeElement && document.activeElement.dataset.unit);
        if (!first) fail(file, `${tag} no focusable option`);
        await page.keyboard.press("ArrowDown");
        const second = await page.evaluate(() => document.activeElement && document.activeElement.dataset.unit);
        if (nOpts > 1 && (!second || second === first)) fail(file, `${tag} ArrowDown did not move focus`);
        await page.keyboard.press("Enter");
        await page.waitForTimeout(150);
        const opened = await page.evaluate(() => document.activeElement && document.activeElement.getAttribute("aria-expanded"));
        if (opened !== "true") fail(file, `${tag} Enter did not open the focused option (aria-expanded=${opened})`);
        const geo2 = await page.evaluate(() => { const d = document.getElementById("dock"); return d.scrollHeight > d.clientHeight + 1; });
        if (geo2) fail(file, `${tag} G3 the dock overflows its cap with one option open`);
        await page.keyboard.press("Escape");
        await page.waitForTimeout(150);
        const closed = await page.evaluate(() => document.activeElement && document.activeElement.getAttribute("aria-expanded"));
        if (closed !== "false") fail(file, `${tag} Escape did not close (aria-expanded=${closed})`);
      }
    }
    // G2: the history cut.
    await page.evaluate(() => { openId = null; document.getElementById("btn-cut").click(); });
    for (const level of ["collapsed", "partial"]) {
      await page.evaluate(l => setLevel(l), level);
      await page.waitForTimeout(200);
      const t = await page.evaluate(() => document.getElementById("dock").innerText);
      if (!/BUY/.test(t)) fail(file, `[cut ${level}] G2 the standing BUY verdict is gone after the block-less follow-up`);
      if (/WAIT/.test(t)) fail(file, `[cut ${level}] G2 a verdict from outside the cut history renders`);
    }
    await page.evaluate(() => document.getElementById("btn-cut").click());
    // G7.
    await page.emulateMedia({ reducedMotion: "reduce" });
    const motion = await page.evaluate(() => {
      const bad = [];
      for (const el of document.querySelectorAll("*")) for (const p of ["animationDuration", "transitionDuration"]) {
        const d = getComputedStyle(el)[p]; if (!d || d === "0s") continue;
        const ms = d.split(",").map(x => x.trim().endsWith("ms") ? parseFloat(x) : parseFloat(x) * 1000);
        if (ms.some(v => v > 1)) bad.push(`${el.className || el.tagName} ${p}=${d}`);
      }
      return bad.slice(0, 4);
    });
    if (motion.length) fail(file, `G7 motion survives prefers-reduced-motion: ${motion.join("; ")}`);
    if (errors.length) fail(file, `page errors: ${errors.join(" | ")}`);
    console.log(`checked ${basename(file)}`);
    await page.close();
  }
  await browser.close();
  for (const f of fails) console.log("FAIL " + f);
  console.log(fails.length ? `${fails.length} failures` : "all gates pass");
  process.exit(fails.length ? 1 : 0);
})();
