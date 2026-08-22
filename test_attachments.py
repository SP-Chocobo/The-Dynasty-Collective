import shutil
import tempfile
import unittest
from pathlib import Path

import attachments as att


class AttachmentsTests(unittest.TestCase):
    """Points ATTACHMENTS_DIR/CAPTIONS_PATH at a throwaway temp directory for the duration of
    each test, never touching real data/attachments/."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_dir = att.ATTACHMENTS_DIR
        self._orig_captions = att.CAPTIONS_PATH
        att.ATTACHMENTS_DIR = Path(self._tmpdir)
        att.CAPTIONS_PATH = att.ATTACHMENTS_DIR / "captions.json"
        self.addCleanup(lambda: shutil.rmtree(self._tmpdir, ignore_errors=True))
        self.addCleanup(setattr, att, "ATTACHMENTS_DIR", self._orig_dir)
        self.addCleanup(setattr, att, "CAPTIONS_PATH", self._orig_captions)

    # -- save_attachment -------------------------------------------------------------------

    def test_save_and_list_round_trips(self):
        att.save_attachment("note.txt", b"hello world", caption="a test note")
        items = att.list_attachments()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["filename"], "note.txt")
        self.assertEqual(items[0]["caption"], "a test note")
        self.assertEqual((att.ATTACHMENTS_DIR / "note.txt").read_bytes(), b"hello world")

    def test_saving_under_an_existing_name_dedupes_with_a_suffix(self):
        first = att.save_attachment("note.txt", b"first")
        second = att.save_attachment("note.txt", b"second")
        self.assertNotEqual(first, second)
        self.assertEqual(len(att.list_attachments()), 2)
        self.assertEqual((att.ATTACHMENTS_DIR / first).read_bytes(), b"first")
        self.assertEqual((att.ATTACHMENTS_DIR / second).read_bytes(), b"second")

    def test_saved_item_defaults_to_global_scope(self):
        name = att.save_attachment("note.txt", b"data")
        item = att.list_attachments()[0]
        self.assertIsNone(item["league_ids"])

    def test_image_extension_is_flagged_is_image(self):
        att.save_attachment("screenshot.png", b"fakepng")
        att.save_attachment("note.txt", b"text")
        by_name = {i["filename"]: i for i in att.list_attachments()}
        self.assertTrue(by_name["screenshot.png"]["is_image"])
        self.assertFalse(by_name["note.txt"]["is_image"])

    # -- set_caption / set_scope ------------------------------------------------------------

    def test_set_caption_updates_an_existing_item(self):
        att.save_attachment("note.txt", b"data", caption="old")
        att.set_caption("note.txt", "new caption")
        self.assertEqual(att.list_attachments()[0]["caption"], "new caption")

    def test_set_scope_to_specific_leagues(self):
        att.save_attachment("note.txt", b"data")
        att.set_scope("note.txt", ["league_a"])
        self.assertEqual(att.list_attachments()[0]["league_ids"], ["league_a"])

    def test_set_scope_back_to_none_makes_it_global_again(self):
        att.save_attachment("note.txt", b"data")
        att.set_scope("note.txt", ["league_a"])
        att.set_scope("note.txt", None)
        self.assertIsNone(att.list_attachments()[0]["league_ids"])

    def test_set_scope_with_empty_list_is_treated_as_global(self):
        att.save_attachment("note.txt", b"data")
        att.set_scope("note.txt", [])
        self.assertIsNone(att.list_attachments()[0]["league_ids"])

    # -- list_attachments filtering -----------------------------------------------------------

    def test_no_league_id_filter_returns_everything_regardless_of_scope(self):
        att.save_attachment("global.txt", b"g")
        att.save_attachment("scoped.txt", b"s", league_ids=["league_a"])
        self.assertEqual(len(att.list_attachments()), 2)

    def test_league_filter_includes_global_items(self):
        att.save_attachment("global.txt", b"g")
        items = att.list_attachments(league_id="league_a")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["filename"], "global.txt")

    def test_league_filter_includes_items_scoped_to_that_league(self):
        att.save_attachment("scoped.txt", b"s", league_ids=["league_a", "league_b"])
        items = att.list_attachments(league_id="league_a")
        self.assertEqual(len(items), 1)

    def test_league_filter_excludes_items_scoped_to_a_different_league(self):
        att.save_attachment("scoped.txt", b"s", league_ids=["league_b"])
        items = att.list_attachments(league_id="league_a")
        self.assertEqual(items, [])

    def test_empty_directory_returns_empty_list(self):
        self.assertEqual(att.list_attachments(), [])

    def test_newest_first_ordering(self):
        # Explicit uploaded_at timestamps rather than relying on real wall-clock gaps between
        # two rapid save_attachment calls, which could tie on a coarse clock.
        att.save_attachment("first.txt", b"1")
        att.save_attachment("second.txt", b"2")
        captions = att._load_captions()
        captions["first.txt"]["uploaded_at"] = 1000.0
        captions["second.txt"]["uploaded_at"] = 2000.0
        att._save_captions(captions)
        filenames = [i["filename"] for i in att.list_attachments()]
        self.assertEqual(filenames[0], "second.txt")
        self.assertEqual(filenames[1], "first.txt")

    # -- delete_attachment ----------------------------------------------------------------------

    def test_delete_removes_the_file_and_its_metadata(self):
        att.save_attachment("note.txt", b"data")
        att.delete_attachment("note.txt")
        self.assertEqual(att.list_attachments(), [])
        self.assertFalse((att.ATTACHMENTS_DIR / "note.txt").exists())

    def test_delete_on_a_nonexistent_file_is_a_safe_no_op(self):
        att.delete_attachment("never_existed.txt")  # should not raise


if __name__ == "__main__":
    unittest.main()
