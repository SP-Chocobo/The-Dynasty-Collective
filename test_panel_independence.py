"""§6.2a / ROADMAP's trust boundary: is two chairs agreeing two opinions, or one?

WHY THIS IS NOT PARANOIA. The neutrality pass deals chairs round-robin across whichever
providers you have a key for, so a user with ONE key runs all four chairs on the same family --
frequently the same model. "The Contrarian didn't dispute it" is the bar the Moderator's own
prompt sets for writing a durable finding, and under one key that sentence can mean *one model
declined to argue with itself*. ROADMAP already states the principle; this is the enforcement.

THE STATE THAT MATTERS MOST is INDETERMINATE, and a boolean would have destroyed it: two chairs
on one provider where either is on the PROVIDER DEFAULT might be the same model, and #109 says
this app cannot tell -- the default ids are floating aliases. Not knowably distinct is not the
same as distinct, and the standing rule (absence is not a value) decides which way it falls.
"""

import unittest
from pathlib import Path

import bot_config
import panel_independence as pi
import ui_source

_HERE = Path(__file__).parent
_APP = ui_source.text()

_ONE_KEY = {role: "claude" for role in bot_config.ROLES}
_THREE_KEYS = {"quant": "claude", "beat": "gemini", "contrarian": "openai", "moderator": "claude"}


class TheFourStatesTests(unittest.TestCase):
    def test_same_provider_same_model_is_one_voice(self):
        models = {"moderator": "claude-opus-5", "contrarian": "claude-opus-5"}
        self.assertEqual(pi.relationship("moderator", "contrarian", _ONE_KEY, models),
                         pi.SAME_VOICE)

    def test_same_provider_different_explicit_models_is_correlated_but_two(self):
        models = {"moderator": "claude-opus-5", "contrarian": "claude-sonnet-5"}
        self.assertEqual(pi.relationship("moderator", "contrarian", _ONE_KEY, models),
                         pi.SAME_FAMILY)

    def test_different_providers_are_independent(self):
        self.assertEqual(pi.relationship("quant", "beat", _THREE_KEYS, {}), pi.INDEPENDENT)

    def test_a_provider_default_on_either_side_is_indeterminate_not_different(self):
        """#109: the default ids are floating aliases, so this app cannot say whether the
        default IS the explicitly-named model. Calling it 'different' would invent a
        distinction; calling it 'same' would invent an identity."""
        for models in ({"moderator": "claude-opus-5"}, {"contrarian": "claude-opus-5"}, {}):
            with self.subTest(models=models):
                self.assertEqual(pi.relationship("moderator", "contrarian", _ONE_KEY, models),
                                 pi.INDETERMINATE)

    def test_an_empty_model_string_is_treated_as_no_model_not_as_a_model_named_empty(self):
        """bot_config stores "" for 'no override' and callers pass None. Neither names a model,
        and treating "" as a distinct model id would report two defaults as SAME_VOICE for the
        wrong reason -- right answer, unsound derivation."""
        self.assertEqual(pi.voice("moderator", _ONE_KEY, {"moderator": ""}), ("claude", None))
        self.assertEqual(pi.voice("moderator", _ONE_KEY, {"moderator": None}), ("claude", None))


class TheBarIsTheCallersTests(unittest.TestCase):
    """The module reports the relationship; it does not decide what is good enough. Different
    blast radii legitimately want different bars, and baking one in would put a deployment
    decision inside a measurement."""

    def test_the_shared_acceptance_bar_admits_only_cross_provider(self):
        for state in (pi.SAME_VOICE, pi.SAME_FAMILY, pi.INDETERMINATE):
            with self.subTest(state=state):
                self.assertFalse(pi.counts_as_corroboration(state, require_cross_provider=True))
        self.assertTrue(pi.counts_as_corroboration(pi.INDEPENDENT, require_cross_provider=True))

    def test_the_provisional_bar_also_admits_same_family(self):
        self.assertTrue(pi.counts_as_corroboration(pi.SAME_FAMILY, require_cross_provider=False))
        self.assertTrue(pi.counts_as_corroboration(pi.INDEPENDENT, require_cross_provider=False))

    def test_indeterminate_never_counts_under_either_bar(self):
        """The rule that makes the four-state design worth having. 'We cannot tell' must not be
        read as 'they are different' -- absence is not a value."""
        for bar in (True, False):
            with self.subTest(require_cross_provider=bar):
                self.assertFalse(pi.counts_as_corroboration(pi.INDETERMINATE,
                                                            require_cross_provider=bar))

    def test_one_voice_never_counts_under_either_bar(self):
        for bar in (True, False):
            with self.subTest(require_cross_provider=bar):
                self.assertFalse(pi.counts_as_corroboration(pi.SAME_VOICE,
                                                            require_cross_provider=bar))

    def test_the_bar_has_no_default_so_a_caller_must_state_which_one_it_means(self):
        with self.assertRaises(TypeError):
            pi.counts_as_corroboration(pi.INDEPENDENT)


class CountingVoicesTests(unittest.TestCase):
    def test_the_single_key_panel_is_measured_at_one_voice(self):
        """The shipped default, measured rather than asserted: one key deals all four chairs to
        one provider, and with no model overrides that is one voice, four times."""
        self.assertEqual(pi.distinct_voices(bot_config.ROLES, _ONE_KEY, {}), 1)

    def test_model_overrides_split_a_single_provider_into_several_voices(self):
        models = {"quant": "claude-haiku-4-5", "moderator": "claude-opus-5"}
        self.assertEqual(pi.distinct_voices(bot_config.ROLES, _ONE_KEY, models), 3)

    def test_three_keys_give_at_least_as_many_voices_as_providers(self):
        self.assertGreaterEqual(pi.distinct_voices(bot_config.ROLES, _THREE_KEYS, {}), 3)

    def test_a_default_is_counted_as_its_own_voice_which_undercounts_rather_than_over(self):
        """A named model and that provider's default are counted separately even though they
        might be the same thing. That inflates the count by at most one per provider -- but the
        alternative (merging them) asserts an identity nothing can establish, and errs toward
        claiming MORE independence than exists, which is the dangerous direction."""
        models = {"moderator": "claude-opus-5"}
        self.assertEqual(pi.distinct_voices(("moderator", "contrarian"), _ONE_KEY, models), 2)


class TheNoteSpeaksOnlyWhenItMattersTests(unittest.TestCase):
    def test_independent_chairs_produce_no_note(self):
        """Saying it every time would train a user to skip the line that matters."""
        self.assertEqual(pi.note("quant", "beat", _THREE_KEYS, {}), "")

    def test_every_other_state_produces_a_note_that_names_the_consequence(self):
        cases = {
            pi.SAME_VOICE: ({"moderator": "x", "contrarian": "x"}, "one opinion"),
            pi.SAME_FAMILY: ({"moderator": "x", "contrarian": "y"}, "correlated"),
            pi.INDETERMINATE: ({"moderator": "x"}, "not known to be different"),
        }
        for state, (models, phrase) in cases.items():
            with self.subTest(state=state):
                text = pi.note("moderator", "contrarian", _ONE_KEY, models)
                self.assertTrue(text)
                self.assertIn(phrase, text)

    def test_the_note_uses_the_users_own_chair_labels_when_given(self):
        text = pi.note("moderator", "contrarian", _ONE_KEY, {"moderator": "x", "contrarian": "x"},
                       labels={"moderator": "Freddy", "contrarian": "The Skeptic"})
        self.assertIn("Freddy", text)
        self.assertIn("The Skeptic", text)


class ItReachesTheScreenWhereItCanBeActedOnTests(unittest.TestCase):
    """A declaration nothing reads is worse than none -- it looks handled. Configure Bots is the
    right consumer specifically because it is the screen where the routing can be CHANGED."""

    def test_the_config_screen_counts_the_panels_voices(self):
        self.assertIn("panel_independence.distinct_voices(", _APP)

    def test_the_config_screen_singles_out_the_moderator_contrarian_pair(self):
        """The pair the whole design leans on: the Moderator writes the verdict and the
        Contrarian is the check on it."""
        self.assertIn('panel_independence.note(\n            "moderator", "contrarian"', _APP)

    def test_the_one_voice_case_is_called_out_explicitly_rather_than_left_to_arithmetic(self):
        """"1 distinct voice" is a number a user can read past. What it MEANS to the thing they
        are about to trust is the part that has to be in words."""
        self.assertIn("is not corroboration here", _APP)


if __name__ == "__main__":
    unittest.main()
