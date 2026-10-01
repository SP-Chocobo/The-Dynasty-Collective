// Second pass on the existing dock: the transcript region located by its overflow, chrome vs
// content per message, elements per message, the markdown check behind the analysis toggle,
// and the collapsed dock when the newest Moderator message carries no verdict block.
const { chromium } = require("playwright");
const { writeFileSync } = require("node:fs");
const SP = process.env.DOCK_PROBE_OUT || __dirname;   // where the screenshots and asis_measure*.json land

async function settle(page) {
  await page.waitForSelector(".st-key-debate_dock", { timeout: 60000 });
  await page.waitForFunction(() => !document.querySelector('[data-testid="stStatusWidget"]'), null, { timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(1200);
  await page.mouse.move(0, 0);
}

const MEASURE = () => {
  const dock = document.querySelector(".st-key-debate_dock");
  const dr = dock.getBoundingClientRect();
  const visible = el => { const b = el.getBoundingClientRect(); return b.height > 0 && b.width > 0 && getComputedStyle(el).visibility !== "hidden"; };
  const ownText = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
  const first = dock.querySelector(".agent-block");
  let region = first;
  while (region && region !== dock) { const o = getComputedStyle(region).overflowY; if ((o === "auto" || o === "scroll") && region.scrollHeight > region.clientHeight - 1) break; region = region.parentElement; }
  if (!region || region === dock) { // fall back: the fixed-height wrapper
    region = first && [...document.querySelectorAll('[data-testid="stVerticalBlockBorderWrapper"]')].find(w => w.contains(first) && /px/.test(w.style.height || ""));
  }
  const rr = region.getBoundingClientRect();
  // Per message: the element containers between one .agent-block's container and the previous.
  const containers = [...region.querySelectorAll('[data-testid="stElementContainer"]')].filter(visible);
  const msgs = [];
  let cur = null;
  for (const c of containers) {
    const t = c.innerText.trim().replace(/\s+/g, " ");
    const isBadge = !!c.querySelector(".badge");
    const isBlock = !!c.querySelector(".agent-block");
    const isButton = !!c.querySelector("button");
    if (isBadge) { cur = { badge: t.slice(0, 40), chromePx: 0, contentPx: 0, chromeEls: 0, contentEls: 0, buttons: 0 }; msgs.push(cur); }
    if (!cur) continue;
    const h = c.getBoundingClientRect().height;
    const els = [...c.querySelectorAll("*")].filter(e => visible(e) && ownText(e)).length;
    if (isBlock) { cur.contentPx += h; cur.contentEls += els; }
    else { cur.chromePx += h; cur.chromeEls += els; if (isButton) cur.buttons++; }
  }
  // Message boxes (badge top to block bottom) fully inside the region's visible box.
  const blocks = [...region.querySelectorAll(".agent-block")];
  const badges = [...region.querySelectorAll(".badge")];
  const fully = blocks.filter((b, i) => { const top = badges[i] ? badges[i].getBoundingClientRect().top : b.getBoundingClientRect().top; const bot = b.getBoundingClientRect().bottom; return top >= rr.top - 1 && bot <= rr.bottom + 1; }).length;
  const partly = blocks.filter(b => { const bb = b.getBoundingClientRect(); return bb.bottom > rr.top && bb.top < rr.bottom; }).length;
  const chrome = msgs.reduce((a, m) => a + m.chromePx, 0), content = msgs.reduce((a, m) => a + m.contentPx, 0);
  const proseLiteral = [...region.querySelectorAll(".agent-prose")].filter(p => /\*\*/.test(p.innerText)).length;
  const proseBold = region.querySelectorAll(".agent-prose strong, .agent-prose b").length;
  const proseList = region.querySelectorAll(".agent-prose li").length;
  const proseP = region.querySelectorAll(".agent-prose p").length;
  return {
    dockTop: Math.round(dr.top), dockHeight: Math.round(dr.height), dockScrollHeight: dock.scrollHeight,
    regionTop: Math.round(rr.top), regionBottom: Math.round(rr.bottom), regionHeight: Math.round(rr.height), regionScrollHeight: region.scrollHeight,
    regionBelowDockEdge: Math.round(rr.top - dr.bottom), chromeAboveRegion: Math.round(rr.top - dr.top),
    messages: msgs.length, fullyVisible: fully, partlyVisible: partly,
    pxPerMessage: +(region.scrollHeight / msgs.length).toFixed(1),
    chromePxPerMessage: +(chrome / msgs.length).toFixed(1), contentPxPerMessage: +(content / msgs.length).toFixed(1),
    chromeShare: +(chrome / (chrome + content)).toFixed(2),
    elementsPerMessage: +(msgs.reduce((a, m) => a + m.chromeEls + m.contentEls, 0) / msgs.length).toFixed(1),
    buttonsPerMessage: +(msgs.reduce((a, m) => a + m.buttons, 0) / msgs.length).toFixed(2),
    perMessage: msgs.map(m => ({ b: m.badge, chrome: Math.round(m.chromePx), content: Math.round(m.contentPx), els: m.chromeEls + m.contentEls })),
    markdown: { proseBlocksWithLiteralStars: proseLiteral, renderedBold: proseBold, renderedListItems: proseList, renderedParagraphs: proseP },
  };
};

(async () => {
  const browser = await chromium.launch();
  const out = {};
  for (const level of ["partial", "full"]) {
    const page = await browser.newPage({ viewport: { width: 1400, height: 1400 } });
    await page.goto(`http://localhost:8765/?level=${level}`, { waitUntil: "networkidle" });
    await settle(page);
    out[level] = await page.evaluate(MEASURE);
    if (level === "full") {
      // Open the newest verdict's analysis and look at how a chair's markdown renders.
      const toggle = page.locator('button:has-text("Show the analysis behind this")').first();
      await toggle.click();
      await settle(page);
      await page.waitForTimeout(800);
      out.fullOpen = await page.evaluate(MEASURE);
      await page.screenshot({ path: `${SP}/asis_full_open.png` });
      // Scroll the transcript region to the Quant block and shoot it.
      await page.evaluate(() => { const q = [...document.querySelectorAll(".badge")].find(b => /QUANT/.test(b.innerText)); q && q.scrollIntoView({ block: "start" }); });
      await page.waitForTimeout(300);
      await page.screenshot({ path: `${SP}/asis_full_quant.png` });
      out.quantProseHtml = await page.evaluate(() => { const q = [...document.querySelectorAll(".badge")].find(b => /QUANT/.test(b.innerText)); const c = q && q.closest('[data-testid="stElementContainer"]'); let n = c; for (let i = 0; i < 6 && n; i++) { n = n.nextElementSibling; const p = n && n.querySelector(".agent-prose"); if (p) return p.innerHTML.slice(0, 700); } return null; });
    }
    await page.close();
  }
  // Collapsed, with the history cut after the Moderator's block-less follow-up (8 messages).
  for (const n of [0, 8]) {
    const page = await browser.newPage({ viewport: { width: 1400, height: 1400 } });
    await page.goto(`http://localhost:8765/?level=collapsed&n=${n}`, { waitUntil: "networkidle" });
    await settle(page);
    out[`collapsed_n${n}`] = await page.evaluate(() => {
      const dock = document.querySelector(".st-key-debate_dock");
      const r = dock.getBoundingClientRect();
      const cap = dock.querySelector('[data-testid="stCaptionContainer"]');
      return { dockHeight: Math.round(r.height), text: dock.innerText.trim().replace(/\s+/g, " ").slice(0, 300), hasLastCall: !!cap, lastCallChars: cap ? cap.innerText.length : 0 };
    });
    await page.screenshot({ path: `${SP}/asis_collapsed_n${n}.png`, clip: { x: 400, y: 1250, width: 1000, height: 150 } });
    await page.close();
  }
  await browser.close();
  writeFileSync(`${SP}/asis_measure2.json`, JSON.stringify(out, null, 1));
  const { perMessage: pm1, ...p } = out.partial; const { perMessage: pm2, ...f } = out.full; const { perMessage: pm3, ...fo } = out.fullOpen;
  console.log("PARTIAL", JSON.stringify(p)); console.log("FULL", JSON.stringify(f)); console.log("FULL+open", JSON.stringify(fo));
  console.log("perMessage(full)", JSON.stringify(pm2));
  console.log("perMessage(fullOpen)", JSON.stringify(pm3.slice(0, 5)));
  console.log("collapsed n0", JSON.stringify(out.collapsed_n0)); console.log("collapsed n8", JSON.stringify(out.collapsed_n8));
  console.log("quant prose html:", out.quantProseHtml);
})();
