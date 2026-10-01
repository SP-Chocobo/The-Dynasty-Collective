"""Can `invariant_registry._python_rendered_figure_sites` fire for the event its own
`population` field names?

The entry "one engine figure reads the same on every surface" declares:

    population="The Python render sites. A new one added with a bare f-string is the whole
                defect returning: Python rounds half-to-even and toFixed rounds half away
                from zero ..."

The enumerator counts `ast.Call` nodes whose func is `ast.Name(id="_figure")` over
`ui_source.text()`. That counts the CONFORMING sites. This probe asks the two questions that
matter:

  (a) adding a BARE F-STRING render -- the named defect -- does it move the census?
  (b) adding a CONFORMING `_figure(...)` render -- does it move the census?

MUTATED IN MEMORY, not on disk (engine-measurement: "the escape hatch"). The enumerator is a
pure function of `ui_source.text()`, so patching that attribute is exactly what a file edit
would produce for this function, with no __pycache__ hazard and no risk to a run in flight.

Run from the repo root:
  PYTHONPATH=. python3 evidence/blind_pass_v4/probes/probe_invariant_registry_figure_sites.py
"""
import invariant_registry as ir
import ui_source

REAL = ui_source.text()


def main() -> None:
    recorded = next(e.census for e in ir.REGISTRY
                    if e.name == "one engine figure reads the same on every surface")
    real_text = REAL
    baseline = len(ir._python_rendered_figure_sites())
    print(f"recorded census                         : {recorded}")
    print(f"observed, tree as it stands             : {baseline}")

    # (a) THE NAMED DEFECT: a new render site that bypasses the rounding rule entirely.
    bare = '\n\ndef _trace_probe_bare(rec):\n    st.caption(f"{rec.universal_value:.0f} UV pts")\n'
    ui_source.text = lambda *a, **k: real_text + bare
    after_bare = len(ir._python_rendered_figure_sites())
    print(f"observed, + ONE BARE F-STRING render    : {after_bare}"
          f"   {'MOVED' if after_bare != recorded else 'census did NOT move -> reported ok'}")

    # (b) A CONFORMING addition, which is not a defect at all.
    good = '\n\ndef _trace_probe_good(rec):\n    st.caption(_figure(rec.universal_value))\n'
    ui_source.text = lambda *a, **k: real_text + good
    after_good = len(ir._python_rendered_figure_sites())
    print(f"observed, + ONE CONFORMING _figure call : {after_good}"
          f"   {'MOVED -> reported as needing re-verification' if after_good != recorded else 'no move'}")

    ui_source.text = lambda *a, **k: real_text
    print(f"restored                                : {len(ir._python_rendered_figure_sites())}")

    # And the render site that ALREADY bypasses `_figure` while still being a render site.
    import re
    direct = re.findall(r"design_system\.figure\(", real_text)
    print(f"\nrender sites calling design_system.figure DIRECTLY (not via _figure): {len(direct)}")
    print("  -> these are real Python render sites and are NOT in the counted population")


if __name__ == "__main__":
    main()
