"""Assemble each v*_src.html into a self-contained v*.html and node --check its script.
Markers: /*__CSS__*/ -> _core.css · /*__DATA__*/ -> const D = states.json (verbatim) · /*__CORE__*/ -> _core.js"""
import json, pathlib, re, subprocess, sys
HERE = pathlib.Path(__file__).parent
STATES = json.load(open(HERE.parent.parent / "states.json"))
G = json.load(open(HERE.parent.parent / "frame.json"))["gauge"]          # same draft (rail identical); opening pool + starter rank per position
STATES["gauge"] = {"opening": {p: sum(G["opening"][p].values()) for p in G["opening"]}, "starterRank": G["starterRank"], "coverage": G["coverage"], "arm": G["arm"]}
DATA = "const D=" + json.dumps(STATES, separators=(",", ":")) + ";"
CSS = (HERE / "_core.css").read_text(); JS = (HERE / "_core.js").read_text()
ok = True
for src in sorted(HERE.glob("v*_src.html")):
    out = HERE / src.name.replace("_src", "")
    html = src.read_text().replace("/*__CSS__*/", CSS).replace("/*__DATA__*/", DATA).replace("/*__CORE__*/", JS)
    for m in ("__CSS__", "__DATA__", "__CORE__"):
        assert m not in html, f"{src.name}: marker {m} left over"
    out.write_text(html)
    js = HERE / (out.stem + ".check.js"); js.write_text("\n".join(re.findall(r"<script>(.*?)</script>", html, re.S)))
    r = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True); js.unlink()
    ok &= r.returncode == 0
    print(f"{out.name}: {len(html)//1024} KB · node --check {'ok' if r.returncode == 0 else 'FAIL ' + r.stderr}")
sys.exit(0 if ok else 1)
