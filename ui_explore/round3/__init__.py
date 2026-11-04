"""Marks `round3` as a package so `unittest discover` reaches its tests -- see `ui_explore/__init__.py`.

The test modules here add their own directory to `sys.path` before importing `build_front` /
`build_empty` by bare name, so they import identically whether collected as top-level modules or
as part of this package. That is why this file can be empty of anything but its reason.
"""
