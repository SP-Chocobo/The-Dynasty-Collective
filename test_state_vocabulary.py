"""`#329`. The census of how many vocabularies this product has for "what kind of thing is this
number", and the two ways that can get worse.

WHY A CENSUS AND NOT AN INVARIANT. The claim the owner's third coherence population wants --
the same semantic state means the same thing on every surface -- is FALSE today, measurably:
the draft room and the front page share exactly one word. Registering it in
`invariant_registry` would mean registering a claim the code contradicts. `boundary_census` is
the model: it allows the reaches that exist and watches for one more while the work to get to
zero proceeds. This allows three vocabularies and fails on a fourth.

WHAT IT DELIBERATELY DOES NOT ASSERT. The divergence itself. `room_only` is 5 and `front_only`
is 2, and a REPAIR makes those fall -- so pinning today's numbers would make the repair fail the
test. That is how a census stops being a ratchet and becomes a cast, and
`test_a_repair_does_not_fail_the_ratchet` below exists to keep it from happening.
"""
from __future__ import annotations

import pathlib
import unittest
from unittest import mock

import state_vocabulary as sv

_ROOT = pathlib.Path(__file__).parent


class TheReadersDeriveRatherThanRestateTests(unittest.TestCase):
    """Every word comes out of the surface's own declaration. A reader that silently returned
    nothing would make the census report a smaller, cleaner world than the one that exists."""

    def test_every_vocabulary_yields_words_from_its_own_source(self):
        self.assertGreaterEqual(len(sv.VOCABULARIES), 3,
                                "the census ranges over fewer surfaces than it was written for")
        for name in sv.VOCABULARIES:
            with self.subTest(vocabulary=name):
                words = sv.words_of(name, _ROOT)
                self.assertTrue(words, f"{name} derived no state words")
                self.assertTrue(all(w and w.strip() for w in words))

    def test_a_moved_declaration_raises_rather_than_reporting_an_empty_vocabulary(self):
        """The failure mode this guards is the one `#298` and `#222` keep producing: not a
        crash, a plausible report about something else. If a surface renames its vocabulary,
        this must say so loudly, not quietly report that the surface has no states."""
        broken = dict(sv.VOCABULARIES["draft_room"])
        broken["pattern"] = r"const NO_SUCH_THING = \{(.*?)\};"
        with mock.patch.dict(sv.VOCABULARIES, {"draft_room": broken}):
            with self.assertRaises(LookupError):
                sv.words_of("draft_room", _ROOT)

    def test_a_declaration_found_but_unreadable_also_raises(self):
        broken = dict(sv.VOCABULARIES["draft_room"])
        broken["members"] = r"(ZZZ_NOT_A_MEMBER_PATTERN)"
        with mock.patch.dict(sv.VOCABULARIES, {"draft_room": broken}):
            with self.assertRaises(LookupError):
                sv.words_of("draft_room", _ROOT)


class TheCensusRatchetsTests(unittest.TestCase):

    def test_the_tree_as_it_stands_passes(self):
        self.assertEqual(sv.widened(_ROOT), [])

    def test_a_fourth_vocabulary_fails(self):
        """The regression this exists to catch: a new place that decides what a number's kind is
        called. Each one is another home the words must be kept in step across by hand."""
        fourth = dict(sv.VOCABULARIES["front_page"])
        with mock.patch.dict(sv.VOCABULARIES, {"a_fourth_surface": fourth}):
            grew = sv.widened(_ROOT)
        self.assertTrue(grew, "a fourth state vocabulary did not trip the census")
        self.assertIn("FOURTH", grew[0])

    def test_losing_the_one_shared_word_fails(self):
        """`measured` is the only word the draft room and the front page both have. Below the
        floor, no semantic state means the same thing on both surfaces."""
        with mock.patch.object(sv, "SHARED_FLOOR", 2):
            grew = sv.widened(_ROOT)
        self.assertTrue(grew, "the shared-vocabulary floor is not load-bearing")
        self.assertIn("DRIFTED FURTHER APART", grew[0])

    def test_a_repair_does_not_fail_the_ratchet(self):
        """THE POINT OF THE DESIGN. If the draft room gained the front page's `constructed` --
        the word `#187`'s absence contract most needs and the room cannot currently say -- the
        shared set rises and the divergence falls. That is the repair, and it must PASS.

        A census that pins its own divergence turns the defect into a requirement, which is the
        failure `boundary_census` avoids by allowing today's reaches and watching for one more.
        """
        real = sv.words_of
        def repaired(name, root=_ROOT):
            words = real(name, root)
            return sorted(set(words) | {"constructed"}) if name == "draft_room" else words
        with mock.patch.object(sv, "words_of", repaired):
            d = sv.divergence(_ROOT)
            self.assertEqual(d["shared_by_user_facing"], ["constructed", "measured"])
            self.assertEqual(sv.widened(_ROOT), [],
                             "a REPAIR tripped the ratchet; the census has become a cast")


class TheCliSaysWhatItMeasuredTests(unittest.TestCase):

    def test_check_passes_on_the_tree_as_it_stands(self):
        self.assertEqual(sv.main(["--check"]), 0)

    def test_check_fails_when_a_fourth_appears(self):
        fourth = dict(sv.VOCABULARIES["front_page"])
        with mock.patch.dict(sv.VOCABULARIES, {"a_fourth_surface": fourth}):
            self.assertEqual(sv.main(["--check"]), 1)


if __name__ == "__main__":
    unittest.main()
