"""#113 / §19.4: the suite says what it ran against, instead of running against whatever is there.

THE DEFECT, DEMONSTRATED TWICE -- once in the audit and once again before this was built. Plant
one CSV in `data/projections/_global/`, which the app's own uploaders write to and `.gitignore`
excludes:

    canonical pool rows: before=764  after=765  delta=+1
    the planted row is priced: trade_value=100.0, projection=9999.0
    git treats the planted file as: .gitignore:10:data/projections/**/*.csv
    suite (test_data_merger): OK

A fabricated player with a 9999-point projection entered the priced universe, git reported the
file as ignored, and the suite stayed green. §19.3(a) measured 28 of 28 inputs tracked and read
that as reproducibility -- but it was true by nobody having uploaded, not by construction.

WHAT THE FAILING TEST IS FOR, and why it is exactly one. Uploading rankings IS the product, so a
user who has used their own app legitimately has extra files, and failing their whole suite would
punish them for using it. One test fails, names the files, and says how to get a clean run; every
other test still reports what it found. On CI, which runs from a fresh clone, there are no extras
and it is silent.
"""

import subprocess
import unittest
from pathlib import Path

import baseline_manifest as bm

_HERE = Path(__file__).parent


class TheDeclaredSetIsTheLoadedSetTests(unittest.TestCase):
    def test_nothing_declared_is_missing_or_altered(self):
        """The half a file listing cannot do. An EDIT to a tracked baseline file moves every
        price the engine computes while the listing stays byte-for-byte identical -- which is why
        this hashes rather than enumerates."""
        result = bm.diff(_HERE)
        self.assertEqual(result["missing"], [],
                         "a declared input file is gone -- a fresh clone of this commit is broken")
        self.assertEqual(result["changed"], [],
                         "a declared input file's contents changed. If that was deliberate, run "
                         "`python3 baseline_manifest.py --write` and commit the manifest WITH the "
                         "data change; if it was not, the engine is being measured against bytes "
                         "this commit does not declare")

    def test_no_undeclared_file_is_in_the_loaded_set(self):
        """The demonstrated case. This is the one test a user with their own uploads will see
        fail, and the message is written for them rather than for CI."""
        undeclared = bm.diff(_HERE)["undeclared"]
        self.assertEqual(
            undeclared, [],
            "these files are loaded by the engine but not declared by this commit:\n  "
            + "\n  ".join(undeclared)
            + "\n\nThis run is NOT reproducible -- someone else on this commit would get "
              "different numbers. If they are your own uploads, move them aside for a clean run. "
              "If they belong to the baseline, `python3 baseline_manifest.py --write` and commit "
              "the manifest with them.")


class TheManifestActuallyCatchesThingsTests(unittest.TestCase):
    """Non-vacuity. The two tests above pass on a clean tree whether or not the mechanism works;
    these plant the exact failures and revert them."""

    def test_an_untracked_upload_is_reported_as_undeclared(self):
        planted = _HERE / "data" / "projections" / "_global" / "zz_manifest_probe.csv"
        planted.parent.mkdir(parents=True, exist_ok=True)
        planted.write_text("Name,Team,Pos,Rank,Projection,Trade Value\n"
                           "Fabricated Probeplayer,SF,WR,1,9999.0,100.0\n")
        try:
            self.assertIn(planted.relative_to(_HERE).as_posix(), bm.diff(_HERE)["undeclared"])
        finally:
            planted.unlink(missing_ok=True)
        self.assertEqual(bm.diff(_HERE)["undeclared"], [], "the probe was not cleaned up")

    def test_git_would_not_have_caught_it(self):
        """The reason a manifest exists at all rather than leaning on `git status`: the directory
        the app writes into is gitignored, so git reports a planted file as expected-absent."""
        planted = _HERE / "data" / "projections" / "_global" / "zz_manifest_probe.csv"
        planted.parent.mkdir(parents=True, exist_ok=True)
        planted.write_text("x\n")
        try:
            ignored = subprocess.run(["git", "check-ignore", str(planted)],
                                     capture_output=True, text=True, cwd=_HERE)
            self.assertEqual(ignored.returncode, 0,
                             "the upload directory is no longer gitignored -- if that is "
                             "deliberate, this test's premise changed and #113 should be re-read")
        finally:
            planted.unlink(missing_ok=True)

    def test_an_edit_to_a_declared_file_is_reported_as_changed(self):
        target = _HERE / "data" / "baseline" / "rankings" / "dynasty_ppr_rankings.csv"
        original = target.read_bytes()
        try:
            target.write_bytes(original + b"Edited Ghost,SF,WR,1,9999,100\n")
            self.assertIn(target.relative_to(_HERE).as_posix(), bm.diff(_HERE)["changed"])
        finally:
            target.write_bytes(original)
        self.assertEqual(bm.diff(_HERE)["changed"], [], "the probe was not reverted")

    def test_a_deleted_declared_file_is_reported_as_missing(self):
        target = _HERE / "data" / "baseline" / "sleeper_projection_provenance.json"
        original = target.read_bytes()
        try:
            target.unlink()
            self.assertIn(target.relative_to(_HERE).as_posix(), bm.diff(_HERE)["missing"])
        finally:
            target.write_bytes(original)
        self.assertEqual(bm.diff(_HERE)["missing"], [])


class TheManifestIsAboutDataNotProseTests(unittest.TestCase):
    def test_documentation_beside_the_data_is_not_hashed(self):
        """ATTRIBUTION.md and README files live in these directories. Hashing them would make
        every prose edit look like a data change, which trains a reader to regenerate the
        manifest without looking -- the exact habit that makes it worthless."""
        declared = bm.load()
        self.assertTrue(declared, "no manifest is committed")
        for name in declared:
            self.assertTrue(name.lower().endswith(bm.DATA_SUFFIXES), name)

    def test_the_manifest_does_not_contain_itself(self):
        self.assertNotIn(bm.MANIFEST_PATH.as_posix(), bm.load())

    def test_store_io_lock_sidecars_are_not_inputs(self):
        """#102's lock files are empty inodes under data/baseline/. Without the exclusion they
        would show up as undeclared inputs on any machine that has ever written a finding."""
        sidecar = _HERE / "data" / "baseline" / "zz_probe.json.lock"
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        sidecar.write_text("")
        try:
            self.assertEqual(bm.diff(_HERE)["undeclared"], [])
        finally:
            sidecar.unlink(missing_ok=True)


class TheDeclaredDirectoriesMatchTheLoaderTests(unittest.TestCase):
    """A manifest that followed the code it checks would agree with a bug. The directory list is
    a literal here, and this test is what makes the duplication safe rather than a drift hazard:
    if data_merger starts loading somewhere else, this fails instead of the manifest silently
    widening to cover it."""

    def test_every_directory_the_merger_loads_is_declared_or_named(self):
        import data_merger
        loaded = {
            data_merger.GLOBAL_PROJECTIONS_DIR.as_posix(),
            data_merger.BASELINE_DIR.as_posix(),
            data_merger.EXTERNAL_VALUES_DIR.as_posix(),
        }
        declared = set(bm.DECLARED_INPUT_DIRS)
        # A directory nested inside a declared one is already covered by the rglob.
        uncovered = {d for d in loaded
                     if not any(d == root or d.startswith(root + "/") for root in declared)}
        self.assertEqual(uncovered, set(),
                         "data_merger loads a directory the manifest does not cover")

    def test_the_per_league_upload_directory_is_deliberately_out_of_scope(self):
        """data/projections/<league_id>/ holds one user's own league uploads. It is not part of
        any commit's declared baseline and never should be -- declaring it would mean the
        manifest changed every time somebody used the app. The _global subdirectory IS declared,
        because that is where a shared baseline would land."""
        import data_merger
        self.assertNotIn(data_merger.PROJECTIONS_DIR.as_posix(), bm.DECLARED_INPUT_DIRS)
        self.assertIn(data_merger.GLOBAL_PROJECTIONS_DIR.as_posix(), bm.DECLARED_INPUT_DIRS)


if __name__ == "__main__":
    unittest.main()
