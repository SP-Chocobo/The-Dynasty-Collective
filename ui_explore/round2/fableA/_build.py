#!/usr/bin/env python3
"""Build: inject the multi-format fixture (verbatim, minus the withheld values), the engine's own
vocabularies (read from the engine, never restated), the §14 gauge where the engine sampled it, and
the shared layer into each template; write v*_<slug>.html; node --check every script.

DATA = {formats: {<format>: {slots, teams, rounds, rail, states}}, vocab: {...}, gauge: {<format>: ...}}
Adding a format (LIGHT_IDP) is data: it lands in fixture.json and appears in the switcher."""
import json, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "_src"
REPO = pathlib.Path("/home/user/The-Dynasty-Collective")
fixture = json.loads((REPO / "ui_explore" / "fixture.json").read_text())
for F in fixture.values():
    for st in F["states"].values():
        for c in st["candidates"]:
            for w in st.get("withheld", []):
                c.pop(w, None)

# ---- the engine's vocabularies, imported from the engine (one home, #126). A cached copy is kept
#      beside the sources only so the build runs where the engine does not import. ----
VOCAB_CACHE = SRC / "_vocab.json"
dump = subprocess.run([sys.executable, "-c", """
import json, player_universe as pu, lineup_optimizer as lo, draft_room as dr, draft_strategy as ds
print(json.dumps({"FLEX_SLOT_POSITIONS": {k: sorted(v) for k, v in pu.FLEX_SLOT_POSITIONS.items()},
  "FANTASY_POSITIONS": sorted(pu.FANTASY_POSITIONS),
  "EXPOSURE": lo.EXPOSURE_BASIS_LABELS, "DISPLACEMENT": lo.DISPLACEMENT_BASIS_LABELS,
  "DENIAL": ds.DENIAL_BASIS_LABELS, "SLOT_SHARE": dr.SLOT_SHARE_LABELS}))
"""], cwd=REPO, capture_output=True, text=True)
if dump.returncode == 0:
    vocab = json.loads(dump.stdout.strip().splitlines()[-1]); VOCAB_CACHE.write_text(json.dumps(vocab, indent=1)); print("vocab: read from the engine")
else:
    vocab = json.loads(VOCAB_CACHE.read_text()); print("vocab: engine import failed, using the cached copy", dump.stderr[-200:])

# ---- §14 gauge: engine samples (frame.json) for the one format whose rail they belong to ----
frame = json.loads((HERE.parent.parent / "frame.json").read_text())
g = frame["gauge"]; POSN = list(g["opening"].keys())
opening = {p: sum(g["opening"][p].values()) for p in POSN}
history = [{"at": h["at"], "left": {p: sum(h["left"][p].values()) for p in POSN}} for h in g["history"]]
gauge = {}
for fmt, F in fixture.items():
    exact = [h["at"] for h in history if all(opening[p] - h["left"][p] == sum(1 for x in F["rail"] if x["no"] <= h["at"] and x["pos"] == p) for p in POSN)]
    if exact[:5] == [0, 20, 40, 60, 80]:
        gauge[fmt] = {"opening": opening, "starterRank": g["starterRank"], "history": history, "coverage": g["coverage"], "rowsOnBoard": g["rowsOnBoard"]}
        print(f"gauge: {fmt} rail reproduces the engine samples at {exact} - tank renders samples only")
print("gauge: no engine sample for", [f for f in fixture if f not in gauge], "- those formats render the tank's absence, never an estimate")

payload = "const DATA=" + json.dumps({"formats": fixture, "vocab": vocab, "gauge": gauge}, separators=(",", ":")) + ";"
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
