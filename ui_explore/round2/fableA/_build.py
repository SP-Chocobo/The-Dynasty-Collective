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
print(json.dumps({"STREAMABLE_POSITIONS": list(dr.STREAMABLE_POSITIONS),
  "FLEX_SLOT_POSITIONS": {k: sorted(v) for k, v in pu.FLEX_SLOT_POSITIONS.items()},
  "FANTASY_POSITIONS": sorted(pu.FANTASY_POSITIONS),
  "EXPOSURE": lo.EXPOSURE_BASIS_LABELS, "DISPLACEMENT": lo.DISPLACEMENT_BASIS_LABELS,
  "DENIAL": ds.DENIAL_BASIS_LABELS, "SLOT_SHARE": dr.SLOT_SHARE_LABELS}))
"""], cwd=REPO, capture_output=True, text=True)
if dump.returncode == 0:
    vocab = json.loads(dump.stdout.strip().splitlines()[-1]); VOCAB_CACHE.write_text(json.dumps(vocab, indent=1)); print("vocab: read from the engine")
else:
    vocab = json.loads(VOCAB_CACHE.read_text()); print("vocab: engine import failed, using the cached copy", dump.stderr[-200:])

# ---- §14 gauge, per format, from each format's OWN opening board ----
# The bar is DERIVED (`projected_points - bpa`), so it never needed a borrowed sample: see
# ui_explore/capture_fixture.py, which calls evidence/mode_boundary/pool_gauge.py -- one home for
# the derivation (#126). History is the real measurements only: the opening count, then each
# captured state's surviving count at its own pick. Nothing between them is interpolated.
gauge = {}
for fmt, F in fixture.items():
    G = F.get("gauge")
    if not G:
        continue
    hist = [{"at": 0, "left": dict(G["opening"])}]
    for st in F["states"].values():
        sg = st.get("gauge")
        if sg:
            hist.append({"at": sg["atPick"], "left": sg["remaining"]})
    hist.sort(key=lambda h: h["at"])
    rows = {p: (round(G["opening"][p] / G["coverage"][p]) if G["coverage"].get(p) else G["opening"][p])
            for p in G["opening"]}
    gauge[fmt] = {"opening": G["opening"], "starterRank": G["starterRank"],
                  "history": hist, "coverage": G["coverage"], "rowsOnBoard": rows}
    print(f"gauge: {fmt} derived from its own opening board, {len(hist)} measured points")
missing = [f for f in fixture if f not in gauge]
if missing:
    print("gauge: none for", missing, "- those formats render the tank's absence, never an estimate")

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
