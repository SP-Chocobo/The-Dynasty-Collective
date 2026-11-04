"""Marks `ui_explore` as a package so `unittest discover` can descend into it (`#308`).

NOT for importing. Nothing does `import ui_explore.anything`; the builders and captures under
here are run as scripts and put their own directory on `sys.path` first. This file exists for one
reason: `unittest discover` will not recurse into a directory that is not a package, so without
it the 34 tests in `round3/` were collected by NOTHING -- not by the full suite, not by
`assertion_floors`, not by `suite_reach`. They passed when run by hand and were absent from every
certification. `test_front_renders_its_basis.py` had been in that state since it was written.
"""
