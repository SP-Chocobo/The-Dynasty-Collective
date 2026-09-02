import shutil
import tempfile
import unittest
from pathlib import Path

import bot_config as bc


class BotConfigTests(unittest.TestCase):
    """Points CONFIG_PATH at a throwaway temp file for the duration of each test, never
    touching real data/bot_config.json."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_path = bc.CONFIG_PATH
        bc.CONFIG_PATH = Path(self._tmpdir) / "bot_config.json"
        self.addCleanup(lambda: shutil.rmtree(self._tmpdir, ignore_errors=True))
        self.addCleanup(setattr, bc, "CONFIG_PATH", self._orig_path)

    # -- role providers ---------------------------------------------------------------------

    def test_no_config_saved_yet_returns_recommended_defaults(self):
        self.assertEqual(bc.load_role_providers(), bc.DEFAULT_ROLE_PROVIDERS)

    def test_set_role_provider_round_trips(self):
        bc.set_role_provider("beat", "openai")
        self.assertEqual(bc.load_role_providers()["beat"], "openai")

    def test_set_role_provider_leaves_other_roles_at_default(self):
        bc.set_role_provider("beat", "openai")
        providers = bc.load_role_providers()
        self.assertEqual(providers["quant"], bc.DEFAULT_ROLE_PROVIDERS["quant"])
        self.assertEqual(providers["moderator"], bc.DEFAULT_ROLE_PROVIDERS["moderator"])

    def test_set_role_provider_rejects_unknown_role(self):
        self.assertFalse(bc.set_role_provider("not_a_role", "claude"))
        self.assertEqual(bc.load_role_providers(), bc.DEFAULT_ROLE_PROVIDERS)

    def test_set_role_provider_rejects_unknown_provider(self):
        self.assertFalse(bc.set_role_provider("beat", "not_a_provider"))
        self.assertEqual(bc.load_role_providers()["beat"], bc.DEFAULT_ROLE_PROVIDERS["beat"])

    def test_reset_role_providers_clears_back_to_defaults(self):
        bc.set_role_provider("beat", "openai")
        bc.set_role_provider("quant", "gemini")
        bc.reset_role_providers()
        self.assertEqual(bc.load_role_providers(), bc.DEFAULT_ROLE_PROVIDERS)

    def test_the_default_assignment_is_an_openly_arbitrary_deal_not_a_vendor_claim(self):
        """INVERTS a test that asserted DEFAULT_ROLE_PROVIDERS matched ROLE_INFO's per-role
        `recommended` field. That field is gone, and its removal is the point.

        Measured: the four hand-justified picks (quant->claude, beat->gemini,
        contrarian->openai, moderator->claude) are EXACTLY what cycling PROVIDERS in
        declaration order across ROLES produces. They were arbitrary first and rationalised
        afterwards -- which is why three of the four `why` strings argued for something other
        than the vendor attached to them, and why one of them (beat) had its justification
        retracted in place at d871078 while the recommendation it justified stayed put.

        Nothing in this repository has ever measured which family suits which chair. A
        recommendation may come back when it carries the benchmark run that produced it; until
        then the assignment is a stated-arbitrary deal and this test holds it to that."""
        cycled = {role: bc.PROVIDERS[i % len(bc.PROVIDERS)] for i, role in enumerate(bc.ROLES)}
        self.assertEqual(bc.DEFAULT_ROLE_PROVIDERS, cycled)
        for role in bc.ROLES:
            self.assertNotIn("recommended", bc.ROLE_INFO[role],
                             "a per-role vendor recommendation came back -- it may, but only "
                             "with the measurement that supports it (see ASSIGNMENT_RULE)")
            self.assertNotIn("why", bc.ROLE_INFO[role])

    def test_a_single_key_user_gets_every_chair_rather_than_one(self):
        """The defect this replaced, measured against the old hardcoded defaults: a Gemini-only
        or OpenAI-only user got 1 of 4 chairs, and in both cases the dead one was the MODERATOR
        -- the chair that writes the verdict, the action item, the to-do directives and the
        source findings."""
        for only in bc.PROVIDERS:
            with self.subTest(only=only):
                assignment = bc.default_role_providers([only])
                self.assertEqual(set(assignment.values()), {only})
                self.assertEqual(len(assignment), len(bc.ROLES))

    def test_a_three_key_user_sees_exactly_what_they_saw_before(self):
        """The repair is free for anyone already set up: the keys-derived rule reproduces the
        previous shipped assignment when all three keys are present."""
        self.assertEqual(bc.default_role_providers(), 
                         {"quant": "claude", "beat": "gemini",
                          "contrarian": "openai", "moderator": "claude"})

    def test_two_keys_deal_across_both_rather_than_stranding_a_chair(self):
        assignment = bc.default_role_providers(["claude", "openai"])
        self.assertEqual(set(assignment.values()), {"claude", "openai"})

    def test_an_unknown_or_empty_provider_set_falls_back_rather_than_returning_nothing(self):
        """A config screen still has to render a selectable value before any key exists, and an
        empty assignment would be a different kind of lie than an unreachable one."""
        self.assertEqual(bc.default_role_providers([]), bc.DEFAULT_ROLE_PROVIDERS)
        self.assertEqual(bc.default_role_providers(["nosuchvendor"]), bc.DEFAULT_ROLE_PROVIDERS)

    def test_a_saved_choice_still_wins_even_when_its_key_is_missing(self):
        """`available` fills gaps; it does not overrule the user. Someone who deliberately
        pointed a chair at a provider they are about to add a key for should not find the app
        has quietly moved it."""
        bc.set_role_provider("quant", "openai")
        self.assertEqual(bc.load_role_providers(["claude"])["quant"], "openai")
        self.assertEqual(bc.load_role_providers(["claude"])["beat"], "claude")

    def test_no_names_saved_returns_default_labels(self):
        names = bc.load_role_names()
        for role in bc.ROLES:
            self.assertEqual(names[role], bc.ROLE_INFO[role]["default_name"])

    def test_set_role_name_round_trips_and_strips_whitespace(self):
        bc.set_role_name("beat", "  Freddy  ")
        self.assertEqual(bc.load_role_names()["beat"], "Freddy")

    def test_set_role_name_rejects_blank_name(self):
        self.assertFalse(bc.set_role_name("beat", "   "))
        self.assertEqual(bc.load_role_names()["beat"], bc.ROLE_INFO["beat"]["default_name"])

    def test_set_role_name_rejects_unknown_role(self):
        self.assertFalse(bc.set_role_name("not_a_role", "Freddy"))

    def test_reset_role_names_clears_back_to_defaults(self):
        bc.set_role_name("beat", "Freddy")
        bc.reset_role_names()
        self.assertEqual(bc.load_role_names()["beat"], bc.ROLE_INFO["beat"]["default_name"])

    # -- role models --------------------------------------------------------------------------

    def test_no_models_saved_defaults_to_empty_string_for_every_role(self):
        models = bc.load_role_models()
        for role in bc.ROLES:
            self.assertEqual(models[role], "")

    def test_set_role_model_round_trips_and_strips_whitespace(self):
        bc.set_role_model("quant", "  claude-opus-5  ")
        self.assertEqual(bc.load_role_models()["quant"], "claude-opus-5")

    def test_set_role_model_to_empty_string_is_a_valid_clear(self):
        bc.set_role_model("quant", "claude-opus-5")
        bc.set_role_model("quant", "")
        self.assertEqual(bc.load_role_models()["quant"], "")

    def test_set_role_model_rejects_unknown_role(self):
        self.assertFalse(bc.set_role_model("not_a_role", "claude-opus-5"))

    def test_reset_role_models_clears_every_override(self):
        bc.set_role_model("quant", "claude-opus-5")
        bc.set_role_model("beat", "gemini-2.0-pro")
        bc.reset_role_models()
        models = bc.load_role_models()
        self.assertEqual(models["quant"], "")
        self.assertEqual(models["beat"], "")

    # -- these three settings don't clobber each other -----------------------------------------

    def test_provider_name_and_model_settings_are_independent(self):
        bc.set_role_provider("quant", "gemini")
        bc.set_role_name("quant", "Freddy")
        bc.set_role_model("quant", "gemini-2.0-pro")
        self.assertEqual(bc.load_role_providers()["quant"], "gemini")
        self.assertEqual(bc.load_role_names()["quant"], "Freddy")
        self.assertEqual(bc.load_role_models()["quant"], "gemini-2.0-pro")
        bc.reset_role_providers()
        # Resetting providers shouldn't touch the name/model overrides.
        self.assertEqual(bc.load_role_names()["quant"], "Freddy")
        self.assertEqual(bc.load_role_models()["quant"], "gemini-2.0-pro")

    # -- moderator personality ------------------------------------------------------------------

    def test_no_personality_set_returns_empty_string(self):
        self.assertEqual(bc.load_moderator_personality(), "")

    def test_set_personality_round_trips(self):
        bc.set_moderator_personality("Blunt")
        self.assertEqual(bc.load_moderator_personality(), "Blunt")

    def test_set_personality_rejects_unknown_value(self):
        self.assertFalse(bc.set_moderator_personality("Sarcastic"))
        self.assertEqual(bc.load_moderator_personality(), "")

    def test_clearing_personality_with_empty_string_is_valid(self):
        bc.set_moderator_personality("Blunt")
        ok = bc.set_moderator_personality("")
        self.assertTrue(ok)
        self.assertEqual(bc.load_moderator_personality(), "")


if __name__ == "__main__":
    unittest.main()
