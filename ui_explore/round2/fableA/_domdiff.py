#!/usr/bin/env python3
"""Prove a refactor of the shared layer changed nothing any surface DRAWS.

shared.css and shared.js are consumed by every variant in this directory, so moving code into
them -- hoisting something out of one template so the others can stop duplicating it -- puts a
shipping surface at risk for the benefit of a new one. "I only moved it" is a claim, and this is
how the claim gets checked.

It dumps the RENDERED .room markup for every (file, format, draft state, viewport) and hashes it.
Run it against a build of the old sources, run it against the new ones, diff the hashes.

MARKUP, NOT PIXELS, on purpose. These pages carry FLIP transforms and rAF-driven measurement, so
two renders of byte-identical source can differ by a pixel; a pixel diff would cry wolf and get
ignored, which is worse than no check. A markup hash also says WHAT moved rather than only that
something did.

Measured when this was written, against the hoist that moved the door logic (windowDoors,
doorLabel, DOOR_SHORT, tankHTML, holdText) out of the v4 template into shared.js so three phone
templates would not each carry a copy:

    60 renders both sides, 0 moved, 0 console or page errors.

And the instrument was mutation-tested in the same pass, because a diff that finds nothing is
exactly when to ask whether it could find anything. Planting ONE word of ONE vocabulary entry in
the old copy -- the TE label, de-spaced -- moved 52 of the 60. The eight that held still are the
renders that draw no tight end. So the zero above is a measurement, not a silence.

Usage, from the repo root:
    git archive HEAD ui_explore/round2/fableA | tar -x -C /tmp/old --strip-components=3
    (cd /tmp/old && python3 _build.py)
    python3 ui_explore/round2/fableA/_domdiff.py dump /tmp/old              /tmp/old.json
    python3 ui_explore/round2/fableA/_domdiff.py dump ui_explore/round2/fableA /tmp/new.json
    python3 ui_explore/round2/fableA/_domdiff.py diff /tmp/old.json /tmp/new.json

Mobile surfaces are deliberately NOT dumped: they are compared by the render gate at phone
viewports, and including them here would make the two sides non-comparable across a commit that
adds one.
"""
import sys, glob, json, hashlib, pathlib

STATES = ["mid", "early", "late"]
FIXTURE = pathlib.Path(__file__).resolve().parents[2] / "fixture.json"


def dump(directory, out, viewports="1440x900,1700x1100"):
    from playwright.sync_api import sync_playwright
    D = pathlib.Path(directory).resolve()
    vps = [tuple(int(n) for n in v.split("x")) for v in viewports.split(",")]
    formats = list(json.loads(FIXTURE.read_text()).keys())
    rows = {}
    with sync_playwright() as p:
        exe = (glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")
               + glob.glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell"))[0]
        b = p.chromium.launch(executable_path=exe)
        for f in sorted(D.glob("v*.html")):
            if f.name.startswith("_"):
                continue
            multi = "v4_" in f.name
            for fmt in (formats if multi else [formats[0]]):
                for st in STATES:
                    for W, H in vps:
                        pg = b.new_page(viewport={"width": W, "height": H})
                        errs = []
                        pg.on("pageerror", lambda e: errs.append(str(e)))
                        pg.on("console", lambda m: errs.append(m.type + ": " + m.text)
                              if m.type in ("error", "warning") else None)
                        pg.goto("file://" + str(f) + "#" + ((fmt + "/") if multi else "") + st,
                                wait_until="load")
                        pg.wait_for_timeout(600)
                        html = pg.evaluate("() => document.querySelector('.room').innerHTML")
                        lg = pg.evaluate("() => (document.getElementById('lg')||{}).textContent || ''")
                        rows[f"{f.name}|{fmt if multi else 'ctrl'}|{st}|{W}x{H}"] = {
                            "sha": hashlib.sha256(html.encode()).hexdigest()[:16],
                            "len": len(html), "lg": lg, "errs": errs}
                        pg.close()
        b.close()
    pathlib.Path(out).write_text(json.dumps(rows, indent=1, sort_keys=True))
    print(f"{len(rows)} renders -> {out}")
    return rows


def diff(old, new):
    a = json.loads(pathlib.Path(old).read_text())
    b = json.loads(pathlib.Path(new).read_text())
    shared = set(a) & set(b)
    for label, keys in (("MISSING from new", sorted(set(a) - set(b))),
                        ("NEW in new", sorted(set(b) - set(a)))):
        if keys:
            print(f"{label}: {keys}")
    moved = [k for k in sorted(shared) if a[k]["sha"] != b[k]["sha"]]
    errs = [k for k in sorted(b) if b[k]["errs"]]
    print(f"markup hash moved: {len(moved)} of {len(shared)}")
    for k in moved:
        print(f"  {k}\n      len {a[k]['len']} -> {b[k]['len']}  ({b[k]['len'] - a[k]['len']:+d})")
    print(f"renders with console or page errors: {len(errs)}")
    for k in errs:
        print("   ", k, b[k]["errs"][:2])
    ok = not moved and not errs
    print("VERDICT:", "nothing any surface draws has changed" if ok
          else "A SURFACE MOVED -- the change answers for this")
    return 0 if ok else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["dump"]:
        dump(*sys.argv[2:])
    elif sys.argv[1:2] == ["diff"]:
        sys.exit(diff(*sys.argv[2:4]))
    else:
        print(__doc__)
        sys.exit(2)
