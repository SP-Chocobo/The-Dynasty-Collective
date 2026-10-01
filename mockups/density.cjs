// The density instrument. For every board, in a real Chromium at 1,400 x 1,400:
//   readable  -- candidates whose collapsed card/row is FULLY inside the first 1,400px of
//                page height at rest (spec closed, fold closed, nothing open, no hover)
//   px/cand   -- the board's vertical extent divided by the candidates it renders at rest
//                (a two-column grid therefore counts half a row-height per candidate; the
//                raw row height is reported beside it)
//   elements  -- text-bearing elements a reader must parse in one collapsed candidate: every
//                element with non-empty own text that is visible at rest, averaged
//   height    -- the whole page at rest, against the 1,400px iframe cap
// Written to mockups/density.json for the index, and printed. Run via smoke.py.
const { chromium } = require("playwright");
const { writeFileSync, readFileSync } = require("node:fs");
const { resolve, basename } = require("node:path");

(async () => {
  const files = process.argv.slice(2);
  const dense = JSON.parse(readFileSync(resolve(__dirname, "_dense_rows.json"), "utf8")).rows;
  const out = [];
  const browser = await chromium.launch();
  for (const file of files) for (const population of ["fixture-14", "real-33"]) {
    const page = await browser.newPage({ viewport: { width: 1400, height: 1400 } });
    await page.goto("file://" + resolve(file));
    if (population === "real-33") await page.evaluate(rows => { candidates = rows; render(); }, dense);
    await page.evaluate(() => { document.querySelectorAll("details").forEach(d => d.open = false); });
    await page.mouse.move(0, 0);
    const m = await page.evaluate(() => {
      const cands = [...document.querySelectorAll('.row[role="option"]')];
      const visible = el => { const r = el.getBoundingClientRect(); return r.height > 0 && r.width > 0 && getComputedStyle(el).visibility !== "hidden"; };
      const ownText = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      // A candidate is readable when its collapsed box is fully inside the first 1400px.
      const boxes = cands.map(el => {
        // Overlapped (deck) cards: the readable box is the part not covered by the next card.
        const r = el.getBoundingClientRect();
        const next = el.nextElementSibling && el.nextElementSibling.matches('.row[role="option"]') ? el.nextElementSibling.getBoundingClientRect() : null;
        // Only a sibling that starts BELOW this card's top and above its bottom covers it; a
        // sibling beside it in a grid shares its top and covers nothing.
        const bottom = next && next.top > r.top + 1 && next.top < r.bottom ? next.top : r.bottom;
        return { top: r.top + scrollY, bottom: bottom + scrollY, height: bottom - r.top };
      });
      const readable = boxes.filter(b => b.top >= 0 && b.bottom <= 1400).length;
      const board = document.getElementById("board").getBoundingClientRect();
      const perCand = (board.height) / cands.length;
      const rawRow = boxes.reduce((a, b) => a + b.height, 0) / boxes.length;
      const elements = cands.map(el => {
        const detail = el.querySelector(".detail"), covered = el.querySelector(".lift-body");
        // .detail is collapsed; .lift-body (the deck) is under the next card at rest.
        return [...el.querySelectorAll("*")].filter(e => !(detail && detail.contains(e)) && !(covered && covered.contains(e)) && visible(e) && ownText(e)).length;
      });
      return {
        candidates: cands.length, readable, pxPerCandidate: +perCand.toFixed(1), rawRowPx: +rawRow.toFixed(1),
        elementsPerCandidate: +(elements.reduce((a, b) => a + b, 0) / elements.length).toFixed(1),
        elementsLeader: elements[0], pageHeight: document.documentElement.scrollHeight,
        boardTop: Math.round(board.top + scrollY),
      };
    });
    out.push({ file: basename(file), population, ...m });
    console.log(`${basename(file).padEnd(28)} ${population.padEnd(10)} readable ${String(m.readable).padStart(2)}/${m.candidates}  ${String(m.pxPerCandidate).padStart(6)} px/cand (row ${m.rawRowPx}px)  ${m.elementsPerCandidate} elements/cand (leader ${m.elementsLeader})  page ${m.pageHeight}px, board starts ${m.boardTop}px`);
    await page.close();
  }
  await browser.close();
  writeFileSync(resolve(__dirname, "density.json"), JSON.stringify(out, null, 1));
})();
