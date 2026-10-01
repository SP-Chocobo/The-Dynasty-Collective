// The panel group's gate, in a real Chromium at 1,400 × 1,400. Per page:
//   A1  absence is a labelled state: with every store empty, the group and every panel or list
//       still render, each empty part carrying a hatched .absent with a title; the rec-less
//       verdict's call slot is a titled absence, never blank; the orphaned pin is a titled
//       absence with the words "no longer", never dropped.
//       With every store empty no unit renders, every panel still carries a labelled absence,
//       and no bare 0 appears anywhere -- a counted zero reads "none", an uncomputed one "—".
//   A2  a pinned verdict shows its block when opened (a receipt with a REASON field).
//   A3  the rating control has no default: on an unrated verdict opened, no rating chip is
//       pressed and save is disabled; pressing a chip enables it; the same-day re-run renders as
//       its own unit with its own control.
//   A4  delete is never a peer of done / dismiss: every delete button is inside a .detail, is
//       .danger, and is not inside a .row > .verb.
//   A5  the legacy finding (no adjudication key) reads "never adjudicated" and never
//       "low-weight input" in its state.
//   C1  gold is chrome only: no text-bearing element in the group has gold or gold-b as its
//       colour; .attn (signal, amber) and .needs (UI state, sky) never share an element.
//   C2  no colour emoji, no null / NaN / undefined in text or titles, no text under 11px.
//   K1  keyboard: a first option is focusable, ArrowDown moves, Enter opens, Escape closes.
//   M1  every animation and transition dies under prefers-reduced-motion.
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
    await page.evaluate(() => { openPanels = Object.fromEntries(Object.keys(openPanels).map(k => [k, true])); if (typeof filters !== "undefined") filters.kind = null; render(); });
    await page.waitForTimeout(200);
    const text = await page.evaluate(() => { const g = document.getElementById("group"); return g.innerText + " " + [...g.querySelectorAll("[title]")].map(e => e.getAttribute("title")).join(" "); });
    for (const t of ["null", "NaN", "undefined"]) if (new RegExp(`(?<![A-Za-z_])${t}(?![A-Za-z_])`).test(text)) fail(file, `C2 rendered ${t}`);
    if (/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u.test(text)) fail(file, `C2 colour emoji in the group`);
    const minFont = await page.evaluate(() => { const vis = el => { const b = el.getBoundingClientRect(); return b.height > 0 && b.width > 0; }; const own = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); return Math.min(...[...document.querySelectorAll("#group *")].filter(e => vis(e) && own(e)).map(e => parseFloat(getComputedStyle(e).fontSize))); });
    if (minFont < 11) fail(file, `C2 text at ${minFont}px`);
    // A1 the rec-less verdict and the orphaned pin.
    const a1 = await page.evaluate(() => {
      const rec = [...document.querySelectorAll('#group [data-kind="decision"][data-date="2025-08-15"] .rec')];
      const recAbsent = rec.length && rec.every(r => r.querySelector(".absent") && (r.querySelector(".absent").getAttribute("title") || "").length > 10);
      const orphan = document.querySelector('#group [data-kind="pin"][data-orphan="true"]');
      const orphanOk = orphan && orphan.querySelector(".absent") && /no longer/.test(orphan.querySelector(".absent").getAttribute("title") || "");
      return { recRows: rec.length, recAbsent, orphan: !!orphan, orphanOk };
    });
    if (!a1.recRows || !a1.recAbsent) fail(file, `A1 the rec-less verdict's call slot is not a titled absence (${JSON.stringify(a1)})`);
    if (!a1.orphan || !a1.orphanOk) fail(file, `A1 the orphaned pin is not a titled absence saying the message is gone (${JSON.stringify(a1)})`);
    // A5 the legacy finding.
    const a5 = await page.evaluate(() => { const u = document.querySelector('#group [data-kind="finding"][data-id="1"]'); return u ? u.querySelector(".state").innerText : null; });
    if (!a5 || !/never adjudicated/i.test(a5) || /low-weight/i.test(a5)) fail(file, `A5 the legacy finding's state reads ${JSON.stringify(a5)}`);
    // A4 delete placement (open every objective to render its detail).
    const a4 = await page.evaluate(() => {
      const bad = [];
      for (const b of document.querySelectorAll("#group button")) { if (!/delete/i.test(b.innerText)) continue; if (!b.closest(".detail") || !b.classList.contains("danger") || b.closest(".row > .verb")) bad.push(b.innerText); }
      return bad;
    });
    if (a4.length) fail(file, `A4 delete is a peer of done/dismiss: ${a4.join(", ")}`);
    // A3 rating without a default, and the re-run as its own unit.
    const rerun = await page.evaluate(() => [...document.querySelectorAll('#group [data-kind="decision"][data-date="2025-09-06"]')].map(u => u.dataset.unit));
    if (new Set(rerun).size < 2) fail(file, `A3 the same-day re-run is not its own unit (${rerun.length} rows for 2025-09-06)`);
    const firstUnrated = await page.evaluate(() => { const u = document.querySelector('#group [data-kind="decision"][data-rated="false"]'); return u ? u.dataset.unit : null; });
    if (!firstUnrated) fail(file, "A3 no unrated verdict rendered");
    else {
      await page.evaluate(id => { openId = id; render(); }, firstUnrated);
      await page.waitForTimeout(150);
      const st = await page.evaluate(id => { const u = document.querySelector(`[data-unit="${id}"]`); const r = u.querySelector('[data-field="rating"]'); if (!r) return null; return { pressed: [...r.querySelectorAll(".chip[aria-pressed='true']")].length, saveDisabled: r.querySelector(".btn.primary").disabled, chips: r.querySelectorAll(".chip").length }; }, firstUnrated);
      if (!st) fail(file, "A3 the opened unrated verdict has no rating control");
      else { if (st.pressed !== 0 || !st.saveDisabled) fail(file, `A3 the rating control has a default (${JSON.stringify(st)})`); if (st.chips !== 4) fail(file, `A3 ${st.chips} rating chips, expected the store's 4 OUTCOME_LABELS`); }
      await page.evaluate(id => { const u = document.querySelector(`[data-unit="${id}"]`); u.querySelector('[data-field="rating"] .chip').click(); }, firstUnrated);
      await page.waitForTimeout(150);
      const st2 = await page.evaluate(id => { const u = document.querySelector(`[data-unit="${id}"]`); return u.querySelector('[data-field="rating"] .btn.primary').disabled; }, firstUnrated);
      if (st2) fail(file, "A3 choosing a rating did not enable save");
      await page.evaluate(() => { ratings = {}; openId = null; render(); });
    }
    // A2 a pinned verdict's block.
    const pinUnit = await page.evaluate(() => { const u = [...document.querySelectorAll('#group [data-kind="pin"][data-role="moderator"]')][0]; return u ? u.dataset.unit : null; });
    const decUnit = await page.evaluate(() => { const u = [...document.querySelectorAll('#group [data-kind="decision"]')].find(u => /pinned/i.test(u.innerText)); return u ? u.dataset.unit : null; });  // innerText is as-rendered, and the mark is text-transform: uppercase
    const target = pinUnit || decUnit;
    if (!target) fail(file, "A2 the pinned verdict is rendered nowhere (no pin row for it and no verdict row marked pinned)");
    else {
      await page.evaluate(id => { openId = id; render(); }, target);
      await page.waitForTimeout(150);
      const ok = await page.evaluate(id => { const u = document.querySelector(`[data-unit="${id}"]`); return !!u.querySelector('.receipt [data-field="reason"]'); }, target);
      if (!ok) fail(file, "A2 the pinned verdict opened without its receipt");
      await page.evaluate(() => { openId = null; render(); });
    }
    // C1 gold and the two hues.
    const c1 = await page.evaluate(() => {
      const hex = h => { const n = parseInt(h.slice(1), 16); return `rgb(${n >> 16}, ${(n >> 8) & 255}, ${n & 255})`; };
      const gold = [hex("#d4a017"), hex("#f7cf4a")];
      const vis = el => { const b = el.getBoundingClientRect(); return b.height > 0 && b.width > 0; };
      const own = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      const goldText = [...document.querySelectorAll("#group *")].filter(e => vis(e) && own(e) && gold.includes(getComputedStyle(e).color)).map(e => e.className || e.tagName).slice(0, 4);
      const both = document.querySelectorAll("#group .attn.needs, #group .needs.attn").length;
      return { goldText, both, attn: document.querySelectorAll("#group .attn").length, needs: document.querySelectorAll("#group .needs").length };
    });
    if (c1.goldText.length) fail(file, `C1 gold carries text in the group: ${c1.goldText.join(", ")}`);
    if (c1.both) fail(file, `C1 an element carries both the signal hue and the UI-state hue`);
    // A1 the empty-stores state.
    await page.evaluate(() => document.getElementById("btn-empty").click());
    await page.waitForTimeout(200);
    const e1 = await page.evaluate(() => {
      const g = document.getElementById("group");
      const panels = [...g.querySelectorAll("[data-panel]")];
      const empties = [...g.querySelectorAll("[data-empty]")].filter(e => e.querySelector(".absent") && (e.querySelector(".absent").getAttribute("title") || "").length > 10);
      const units = g.querySelectorAll("[data-unit]").length;
      // A counted zero must read "none", never "0": a bare numeral 0 beside a hatched absence
      // makes the reader tell two different states apart by eye. (A quantity never computed
      // is the absence itself, checked above.)
      const bareZero = (g.innerText.match(/(?<![\d.,])0(?![\d.,%])/g) || []).length;
      return { panels: panels.length, empties: empties.length, units, bareZero, headPresent: !!g.querySelector(".group-head"), text: g.innerText.slice(0, 200) };
    });
    if (!e1.headPresent) fail(file, "A1 with every store empty the group frame is gone");
    if (e1.units) fail(file, `A1 with every store empty ${e1.units} units still render`);
    if (e1.empties < 1) fail(file, "A1 with every store empty no labelled absence renders");
    if (e1.panels && e1.empties < e1.panels) fail(file, `A1 with every store empty ${e1.panels} panels but only ${e1.empties} labelled absences`);
    if (e1.bareZero) fail(file, `A1 with every store empty a bare 0 renders ${e1.bareZero} time(s); a counted zero must read "none"`);
    await page.evaluate(() => document.getElementById("btn-empty").click());
    await page.waitForTimeout(200);
    // K1 keyboard.
    await page.evaluate(() => { const r = document.querySelector('#group [role="option"][tabindex="0"]'); r && r.focus(); });
    const first = await page.evaluate(() => document.activeElement && document.activeElement.dataset.unit);
    if (!first) fail(file, "K1 no focusable option");
    await page.keyboard.press("ArrowDown");
    const second = await page.evaluate(() => document.activeElement && document.activeElement.dataset.unit);
    if (!second || second === first) fail(file, "K1 ArrowDown did not move focus");
    await page.keyboard.press("Enter"); await page.waitForTimeout(150);
    const opened = await page.evaluate(() => document.activeElement && document.activeElement.getAttribute("aria-expanded"));
    if (opened !== "true") fail(file, `K1 Enter did not open (aria-expanded=${opened})`);
    await page.keyboard.press("Escape"); await page.waitForTimeout(150);
    const closed = await page.evaluate(() => document.activeElement && document.activeElement.getAttribute("aria-expanded"));
    if (closed !== "false") fail(file, `K1 Escape did not close (aria-expanded=${closed})`);
    // M1.
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
    if (motion.length) fail(file, `M1 motion survives prefers-reduced-motion: ${motion.join("; ")}`);
    if (errors.length) fail(file, `page errors: ${errors.join(" | ")}`);
    console.log(`checked ${basename(file)}`);
    await page.close();
  }
  await browser.close();
  for (const f of fails) console.log("FAIL " + f);
  console.log(fails.length ? `${fails.length} failures` : "all gates pass");
  process.exit(fails.length ? 1 : 0);
})();
