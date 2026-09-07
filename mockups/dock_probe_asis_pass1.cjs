// Baseline instrument for the EXISTING dock, in a real Chromium against the real app
// (scratch copy, seeded with mockups/dock_transcript.json). 1400 x 1400, one page per level.
const { chromium } = require("playwright");
const { writeFileSync } = require("node:fs");
const SP = process.env.DOCK_PROBE_OUT || __dirname;   // where the screenshots and asis_measure*.json land

(async () => {
  const browser = await chromium.launch();
  const out = [];
  for (const level of ["collapsed", "partial", "full"]) {
    const page = await browser.newPage({ viewport: { width: 1400, height: 1400 } });
    const errors = [];
    page.on("pageerror", e => errors.push(String(e)));
    await page.goto(`http://localhost:8765/?level=${level}`, { waitUntil: "networkidle" });
    await page.waitForSelector(".st-key-debate_dock", { timeout: 60000 });
    // Streamlit settles in a few reruns; wait for the running-man to go.
    await page.waitForFunction(() => !document.querySelector('[data-testid="stStatusWidget"]'), null, { timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(1500);
    await page.mouse.move(0, 0);
    await page.screenshot({ path: `${SP}/asis_${level}.png` });
    const m = await page.evaluate((level) => {
      const dock = document.querySelector(".st-key-debate_dock");
      const r = dock.getBoundingClientRect();
      const visible = el => { const b = el.getBoundingClientRect(); return b.height > 0 && b.width > 0 && getComputedStyle(el).visibility !== "hidden"; };
      const ownText = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      // The dock's top-level blocks, in order, with their heights and first words.
      const blocks = [...dock.querySelectorAll(':scope > div > div > [data-testid="stElementContainer"], :scope > div > div > [data-testid="stVerticalBlockBorderWrapper"], :scope > div > div > [data-testid="stHorizontalBlock"]')]
        .filter(visible).map(el => ({ h: Math.round(el.getBoundingClientRect().height), t: el.innerText.trim().replace(/\s+/g, " ").slice(0, 60) }));
      // The transcript scroll region: the bordered wrapper with an explicit height.
      const region = [...dock.querySelectorAll('[data-testid="stVerticalBlockBorderWrapper"]')].find(el => /^\d+px$/.test(el.style.height) || parseFloat(getComputedStyle(el).height) >= 100 && el.querySelector(".agent-block"));
      let transcript = null;
      if (region) {
        const rr = region.getBoundingClientRect();
        const blocks = [...region.querySelectorAll(".agent-block")];
        const badges = [...region.querySelectorAll(".badge")];
        const units = blocks.length;  // one .agent-block per rendered message
        // Elements a reader parses per message: badge, pin button, objective button, prose, verdict, toggle.
        const els = [...region.querySelectorAll("*")].filter(e => visible(e) && ownText(e));
        const fullyVisible = blocks.filter(b => { const bb = b.getBoundingClientRect(); return bb.top >= rr.top && bb.bottom <= rr.bottom; }).length;
        const partlyVisible = blocks.filter(b => { const bb = b.getBoundingClientRect(); return bb.bottom > rr.top && bb.top < rr.bottom; }).length;
        const literalMd = [...region.querySelectorAll(".agent-prose")].filter(p => /\*\*|^- |\n- /.test(p.innerText)).length;
        const boldMd = region.querySelectorAll(".agent-prose strong, .agent-prose b").length;
        const listMd = region.querySelectorAll(".agent-prose ul, .agent-prose li").length;
        transcript = {
          regionTop: Math.round(rr.top), regionHeight: Math.round(rr.height), scrollHeight: region.scrollHeight,
          messagesRendered: units, badges: badges.length, fullyVisible, partlyVisible,
          pxPerMessage: +(region.scrollHeight / units).toFixed(1),
          elementsPerMessage: +(els.length / units).toFixed(1),
          firstVisibleText: region.innerText.trim().replace(/\s+/g, " ").slice(0, 160),
          literalMarkdownBlocks: literalMd, renderedBold: boldMd, renderedListItems: listMd,
          buttonsInRegion: region.querySelectorAll("button").length,
        };
      }
      const captionText = [...dock.querySelectorAll('[data-testid="stCaptionContainer"]')].map(e => e.innerText.trim()).join(" | ").slice(0, 400);
      const buttons = [...dock.querySelectorAll("button")].filter(visible).map(b => b.innerText.trim().replace(/\s+/g, " ").slice(0, 32));
      const sidebar = document.querySelector('[data-testid="stSidebar"]');
      return {
        level, dockTop: Math.round(r.top), dockHeight: Math.round(r.height), dockLeft: Math.round(r.left), dockWidth: Math.round(r.width),
        dockScrollHeight: dock.scrollHeight, dockOverflows: dock.scrollHeight > dock.clientHeight + 1,
        sidebarExpanded: sidebar ? sidebar.getAttribute("aria-expanded") : null,
        blocks, transcript, captionText, buttons,
        textBearingInDock: [...dock.querySelectorAll("*")].filter(e => visible(e) && ownText(e)).length,
        emojiInDock: (dock.innerText.match(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu) || []).length,
      };
    }, level);
    m.errors = errors;
    out.push(m);
    console.log(JSON.stringify(m, null, 1));
    await page.close();
  }
  await browser.close();
  writeFileSync(`${SP}/asis_measure.json`, JSON.stringify(out, null, 1));
})();
