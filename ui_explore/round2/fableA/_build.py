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
# §14 gauge: the engine's own counts (frame.json), bands collapsed to totals — the tank needs only the
# pool size, the starter line and the history of what is left. Validate the rail-derived drain against
# every engine sample so the per-state tank is a reproduction of engine data, not an estimate.
frame = json.loads((HERE.parent.parent / "frame.json").read_text())
g = frame["gauge"]
POSN = list(g["opening"].keys())
opening = {p: sum(g["opening"][p].values()) for p in POSN}
history = [{"at": h["at"], "left": {p: sum(h["left"][p].values()) for p in POSN}} for h in g["history"]]
exact = []
for h in history:
    drafted = {p: sum(1 for x in data["rail"] if x["no"] <= h["at"] and x["pos"] == p) for p in POSN}
    if all(opening[p] - h["left"][p] == drafted[p] for p in POSN): exact.append(h["at"])
# The rail reproduces the engine's drain only through #80; after that the engine drains for reasons the
# rail cannot see (unpriced picks, re-sampling). So the tank renders the ENGINE SAMPLE at or before the
# pick, disclosed as "as of #N", and never drains it by the rail.
data["gauge"] = {"opening": opening, "starterRank": g["starterRank"], "history": history, "coverage": g["coverage"], "rowsOnBoard": g["rowsOnBoard"]}
print("gauge: engine samples every 20 picks; the rail reproduces them exactly at", exact, "- tank uses samples only")
payload = "const DATA=" + json.dumps(data, separators=(",", ":")) + ";"
css = (SRC / "shared.css").read_text()
js = (SRC / "shared.js").read_text()
ok = True
jobs = []
for tpl in sorted(SRC.glob("v*.tpl.html")):
    if tpl.name.startswith("v1_"):
        jobs.append((tpl, tpl.name.replace(".tpl.html", ".html"), "const WITH_RAIL=false;"))
        jobs.append((tpl, tpl.name.replace(".tpl.html", "_rail.html"), "const WITH_RAIL=true;"))
    else:
        jobs.append((tpl, tpl.name.replace(".tpl.html", ".html"), ""))
for tpl, name, flag in jobs:
    html = tpl.read_text().replace("/*__CSS__*/", css).replace("/*__DATA__*/", payload + flag).replace("/*__SHARED__*/", js)
    for m in ("__CSS__", "__DATA__", "__SHARED__"):
        assert m not in html, f"{tpl.name}: marker {m} left over"
    out = HERE / name
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
