#!/usr/bin/env python3
"""Round 2 build: inject states.json (verbatim, minus the withheld values) + the shared layer into
each template, write v*_<slug>.html beside this file, node --check every script."""
import json, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "_src"
data = json.loads((HERE.parent.parent / "states.json").read_text())
# Absence discipline at the contract boundary: the payload names a withheld family and still ships
# its values. The client never receives them, so no variant can leak one.
for st in data["states"].values():
    for c in st["candidates"]:
        for w in st.get("withheld", []):
            c.pop(w, None)
payload = "const DATA=" + json.dumps(data, separators=(",", ":")) + ";"
css = (SRC / "shared.css").read_text()
js = (SRC / "shared.js").read_text()
ok = True
for tpl in sorted(SRC.glob("v*.tpl.html")):
    html = tpl.read_text().replace("/*__CSS__*/", css).replace("/*__DATA__*/", payload).replace("/*__SHARED__*/", js)
    for m in ("__CSS__", "__DATA__", "__SHARED__"):
        assert m not in html, f"{tpl.name}: marker {m} left over"
    out = HERE / tpl.name.replace(".tpl.html", ".html")
    out.write_text(html)
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, flags=re.S)
    chk = HERE / ("_check_" + out.stem + ".js")
    chk.write_text("\n;\n".join(scripts))
    r = subprocess.run(["node", "--check", str(chk)], capture_output=True, text=True)
    chk.unlink()
    ok &= r.returncode == 0
    print(f"{'ok  ' if r.returncode == 0 else 'FAIL'} {out.name}  {out.stat().st_size // 1024} KB")
    if r.returncode:
        print(r.stderr)
sys.exit(0 if ok else 1)
