"""Execute every mockup's JS under Node against a DOM stub and check the gates that can be
checked without a browser: no null/NaN/undefined reaches the page; the unpriced fixture row
renders the absent mark and the measured-zero row renders a zero, in both leader orders; no
vendor name is in any committed file. `python3 mockups/smoke.py` from the repo root."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent

STUB = r"""
const _els = {};
function mk(id) {
  const el = { id, innerHTML: "", textContent: "", style: {}, dataset: {}, classList: { toggle() {}, add() {}, remove() {}, contains() { return false; } },
    addEventListener() {}, setAttribute() {}, getAttribute() { return "false"; }, focus() {}, getBoundingClientRect() { return { left: 0, top: 0, width: 100, height: 100 }; },
    querySelectorAll() { return []; }, contains() { return false; } };
  return el;
}
globalThis.document = {
  getElementById(id) { return _els[id] || (_els[id] = mk(id)); },
  querySelectorAll() { return []; },
  documentElement: { classList: { toggle() {}, contains() { return false; } } },
};
globalThis.matchMedia = () => ({ matches: false });
"""

FORBIDDEN = ("draft sharks", "draftsharks", "draft_sharks")


def run(html: str, promote: bool) -> dict:
    script = html.split("<script>", 1)[1].split("</script>", 1)[0]
    tail = ""
    if promote:
        tail = '\ntoggleLeader({ getAttribute() { return "false"; }, setAttribute() {} });\n'
    program = STUB + script + tail + '\nconsole.log(JSON.stringify(Object.fromEntries(Object.entries(_els).map(([k, v]) => [k, v.innerHTML + " " + v.textContent]))));\n'
    out = subprocess.run([shutil.which("node"), "-e", program], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise SystemExit(f"JS error: {out.stderr}")
    return json.loads(out.stdout.strip().splitlines()[-1])


def main() -> int:
    if shutil.which("node") is None:
        print("node not found; nothing executed")
        return 1
    failures = []
    for path in sorted(HERE.glob("*.html")):
        text = path.read_text()
        low = text.lower()
        for word in FORBIDDEN:
            if word in low:
                failures.append(f"{path.name}: names the vendor ({word})")
        if path.name == "index.html":
            continue
        for promote in (False, True):
            rendered = run(text, promote)
            joined = " ".join(rendered.values())
            # What a person can read: text between tags, plus every title tooltip. Inline event
            # handlers and class names are not readable and are not scanned.
            visible = re.sub(r"<[^>]*>", " ", joined) + " " + " ".join(re.findall(r'title="([^"]*)"', joined))
            for token in ("null", "NaN", "undefined"):
                if re.search(rf"(?<![A-Za-z_]){token}(?![A-Za-z_])", visible):
                    failures.append(f"{path.name} (leader promoted={promote}): rendered {token!r}")
            # The unpriced row must be a DESIGNED absence: the hatched mark, or -- in the
            # sentence variant, where absence is a clause -- the words that say so.
            if "H Butker" in joined and 'class="absent"' not in joined and 'class="gap"' not in joined and "an absence, not a zero" not in joined:
                failures.append(f"{path.name} (promoted={promote}): unpriced row has no absent mark")
            # The zeros row must show a zero somewhere as a value: a cell, a label, or a clause.
            if "C Boswell" in joined and not re.search(r"(>|\s)0(\.0)?(<|\s|%)", joined):
                failures.append(f"{path.name} (promoted={promote}): the measured-zero row renders no zero")
        print("ok", path.name)
    for f in failures:
        print("FAIL", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
