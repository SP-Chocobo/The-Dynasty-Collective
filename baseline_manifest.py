"""#113 / §19.4: the suite's input set, declared instead of discovered.

THE DEFECT, DEMONSTRATED TWICE -- once in the audit and once again before this was written.
Plant one CSV in `data/projections/_global/`, which the app's own uploaders write to and which
`.gitignore` excludes:

    canonical pool rows: before=764  after=765  delta=+1
    the planted row is priced: trade_value=100.0, projection=9999.0
    git treats the planted file as: .gitignore:10:data/projections/**/*.csv
    suite (test_data_merger): OK

A fabricated player entered the priced universe, git reported the file as ignored, and the suite
stayed green. §19.3(a) measured 28 of 28 inputs tracked and concluded the baseline is
reproducible -- **true today by nobody having uploaded, not by construction.** Two developers on
the same commit, one of whom has used the app, run the same tests against different data and
both see green.

WHAT THIS IS NOT. It is not a lock on the data directories: uploading rankings IS the product,
and a manifest that forbade it would break the app to protect a test. The distinction is between
two populations that happen to share a directory:

  * the COMMITTED BASELINE -- the files a given commit declares, which a fresh clone gets and
    which every reproducibility claim rests on; and
  * a USER'S OWN UPLOADS -- legitimately on their machine, and illegitimate in a test run that
    claims to be reproducible.

So the rule is not "no extra files". It is: **a run is only reproducible if the loaded set equals
the declared set**, and a run that is not reproducible must say so rather than report green.

WHY A CONTENT HASH AND NOT A FILE LIST. A file list catches the planted-file case and misses the
worse one -- an EDIT to a tracked baseline file, which changes every price the engine computes
while the listing stays identical. Hashing is what makes "unchanged" checkable at all, and §19.2
recorded that this repo had no integrity primitive of any kind: `hashlib` appeared exactly once
in production, over a benchmark battery.

WHY IT LIVES BESIDE THE DATA rather than in a test. The manifest is a claim the REPOSITORY makes
about itself -- "this commit's engine was measured against exactly these bytes" -- and it is
useful to a human reading a diff, not only to a test runner. `--write` regenerates it, and
changing baseline data is then a deliberate commit that carries the new hashes with it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys

import store_io
from pathlib import Path

#: The directories DataMerger actually loads, in its own declaration order. Kept as a literal
#: rather than imported from data_merger to avoid a manifest that silently follows the code it
#: is supposed to be checking -- if these two ever disagree, that is a finding, and a test says
#: so rather than letting one define the other.
DECLARED_INPUT_DIRS = (
    "data/baseline",
    "data/projections/_global",
)

#: Extensions the loaders actually read. A README or an ATTRIBUTION.md sitting beside the data is
#: documentation, not input, and hashing it would make every prose edit look like a data change.
DATA_SUFFIXES = (".csv", ".json", ".pdf")

MANIFEST_PATH = Path("data/baseline/INPUT_MANIFEST.json")

#: Files under the declared directories that are this app's own bookkeeping rather than engine
#: input. store_io's lock sidecars are empty inodes; the manifest itself cannot contain its own
#: hash. Both would otherwise show up as undeclared inputs on every run.
_EXCLUDED_NAMES = (MANIFEST_PATH.name,)
_EXCLUDED_SUFFIXES = (".lock",)


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan(root: Path = Path(".")) -> dict[str, str]:
    """Every data file under the declared directories, relative path -> sha256.

    Sorted, so the manifest's diff is readable and its ordering is not an artifact of the
    filesystem's own listing order.
    """
    found: dict[str, str] = {}
    for directory in DECLARED_INPUT_DIRS:
        base = root / directory
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in DATA_SUFFIXES:
                continue
            if path.name in _EXCLUDED_NAMES or path.suffix in _EXCLUDED_SUFFIXES:
                continue
            found[path.relative_to(root).as_posix()] = _hash(path)
    return found


def load(path: Path = MANIFEST_PATH) -> dict[str, str]:
    """The declared set, or {} when no manifest exists. An absent manifest is not an empty
    declaration -- callers distinguish the two, since "nothing is declared" and "nothing is
    present" have opposite meanings here."""
    if not path.exists():
        return {}
    # Deliberately NOT store_io.read: that marks an unparseable file and then refuses to write
    # over it (#102), which is the right rule for a data store and exactly the wrong one here.
    # `--write` is how a broken manifest gets FIXED, and a guard that blocked the recovery
    # command would be a trap. The manifest is an integrity artifact, not user data -- losing it
    # costs one regeneration, and it must stay writable precisely when it is broken.
    try:
        return dict(json.loads(path.read_text())["files"])
    except (json.JSONDecodeError, KeyError, OSError, TypeError):
        return {}


def write(root: Path = Path("."), path: Path = MANIFEST_PATH) -> dict[str, str]:
    files = scan(root)
    # store_io.write, for its atomic replace (#102): an interrupted --write would otherwise
    # leave a truncated manifest, and every run afterwards would report every declared file as
    # undeclared -- a broken integrity check that looks like a catastrophic integrity failure.
    store_io.write(path, {
            "_comment": (
                "Declared input set for this commit's engine measurements -- see "
                "baseline_manifest.py. Regenerate with `python3 baseline_manifest.py --write` "
                "and commit the result ALONGSIDE the data change that caused it; a manifest "
                "updated on its own is a hash that agrees with whatever is on one machine."
            ),
            "directories": list(DECLARED_INPUT_DIRS),
            "files": files,
    })
    return files


def diff(root: Path = Path("."), path: Path = MANIFEST_PATH) -> dict[str, list[str]]:
    """Three ways the loaded set can disagree with the declared one, kept apart because they
    mean different things:

      missing    -- declared and not present. A fresh clone is broken, or a file was deleted.
      changed    -- present with different bytes. Every price computed from it has moved.
      undeclared -- present and not declared. The demonstrated case: a user's own upload, or a
                    planted file, silently entering the priced universe.
    """
    declared, present = load(path), scan(root)
    return {
        "missing": sorted(set(declared) - set(present)),
        "changed": sorted(name for name in set(declared) & set(present)
                          if declared[name] != present[name]),
        "undeclared": sorted(set(present) - set(declared)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--write", action="store_true",
                        help="regenerate the manifest from what is on disk now")
    parser.add_argument("--check", action="store_true",
                        help="report any disagreement; exit 1 if there is one")
    args = parser.parse_args(argv)
    if args.write:
        files = write()
        print(f"wrote {MANIFEST_PATH} -- {len(files)} declared input files")
        return 0
    result = diff()
    total = sum(len(v) for v in result.values())
    if not total:
        print(f"input set matches the manifest ({len(load())} files)")
        return 0
    for kind, names in result.items():
        for name in names:
            print(f"{kind:11} {name}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
