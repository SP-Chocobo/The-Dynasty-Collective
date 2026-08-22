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

    def test_default_role_providers_actually_matches_role_info(self):
        # The reset button's whole promise depends on these never drifting apart.
        for role in bc.ROLES:
            self.assertEqual(bc.DEFAULT_ROLE_PROVIDERS[role], bc.ROLE_INFO[role]["recommended"])

    # -- role names ---------------------------------------------------------------------------

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
