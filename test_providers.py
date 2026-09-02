"""The provider socket: what a provider must supply, and what it must admit it cannot.

WHY THIS EXISTS. Role-to-provider routing was already neutral. The provider SET was not: adding
a fourth meant editing six files, with nothing anywhere declaring that six was the list. You
found it by archaeology, which is how the vendor defaults calcified in the first place.

TWO PROPERTIES CARRY IT, and the second is the one that is easy to get wrong.

  1. Every hand-kept per-provider table is DERIVED from the registry, so a registered provider
     cannot be missing from one and a table entry cannot exist without a registration.

  2. The `reports_*` flags are CHECKABLE, not editorial. A provider declaring it reports
     truncation must actually have a reader in provider_meter. A flag that could disagree with
     reality would be a claim the writing path cannot establish -- this codebase's oldest and
     most-repaired defect class -- and it would be worse than no flag, because the UI would
     print a capability the app does not have.
"""

import unittest
from pathlib import Path

import bot_config
import llm_engine
import provider_meter
import providers

_APP = (Path(__file__).parent / "app.py").read_text()


class TheRegistryIsTheOneListTests(unittest.TestCase):
    def test_three_providers_are_registered(self):
        self.assertEqual(providers.ids(), ("claude", "gemini", "openai"))

    def test_the_dispatch_table_is_derived_and_cannot_disagree(self):
        self.assertEqual(tuple(llm_engine.PROVIDER_CALLERS), providers.ids())
        for pid in providers.ids():
            self.assertIs(llm_engine.PROVIDER_CALLERS[pid], providers.get(pid).call)

    def test_bot_config_reads_the_registry_rather_than_a_copy(self):
        self.assertEqual(tuple(bot_config.PROVIDERS), providers.ids())
        self.assertEqual(bot_config.PROVIDER_LABELS, providers.labels())
        self.assertEqual(set(bot_config.SUGGESTED_MODELS), set(providers.ids()))

    def test_the_app_derives_its_two_tables_instead_of_hand_keeping_them(self):
        """app.py is source-scanned rather than imported, as every app-level contract here is."""
        self.assertIn("PROVIDER_KEY_FIELD = {pid: providers.get(pid).key_field", _APP)
        self.assertIn("IS_PROVIDER_CONFIGURED = {pid: providers.get(pid).is_configured", _APP)

    def test_no_module_hand_lists_the_provider_set_any_more(self):
        """The specific shape this replaced: a literal triple of vendor ids, written out in a
        module that then has to be remembered when a fourth arrives."""
        for name in ("bot_config.py", "pick_debate.py"):
            source = (Path(__file__).parent / name).read_text()
            self.assertNotIn('("claude", "gemini", "openai")', source, name)

    def test_registration_order_is_stable_because_the_chair_deal_depends_on_it(self):
        """The round-robin that assigns chairs is arbitrary and says so -- but it must be
        arbitrary the SAME WAY every run, or a user's assignment would shuffle between
        launches."""
        self.assertEqual(providers.ids(), tuple(providers.labels()))
        self.assertEqual(bot_config.default_role_providers(),
                         bot_config.default_role_providers())


class DeclaredCapabilitiesMatchRealityTests(unittest.TestCase):
    """The flags are claims about THIS repository's extractors, so they are checkable here."""

    def test_a_provider_claiming_truncation_detection_has_a_reader_for_it(self):
        for pid in providers.ids():
            with self.subTest(provider=pid):
                declared = providers.get(pid).reports_completion
                self.assertEqual(declared, pid in provider_meter._EXTRACTORS,
                                 f"{pid} declares reports_completion={declared} but "
                                 f"provider_meter {'has' if pid in provider_meter._EXTRACTORS else 'has no'} reader")

    def test_a_provider_claiming_retrieved_sources_has_a_reader_for_it(self):
        for pid in providers.ids():
            with self.subTest(provider=pid):
                declared = providers.get(pid).reports_sources
                self.assertEqual(declared, pid in provider_meter._SOURCE_EXTRACTORS)

    def test_usage_and_served_model_ride_the_same_extractor_as_completion(self):
        """describe() reads all three off one entry, so claiming one without the others would be
        a distinction the code cannot make."""
        for pid in providers.ids():
            provider = providers.get(pid)
            with self.subTest(provider=pid):
                self.assertEqual(provider.reports_usage, provider.reports_completion)
                self.assertEqual(provider.reports_model, provider.reports_completion)

    def test_an_unregistered_provider_is_reported_as_unknown_rather_than_guessed(self):
        """What actually happens when someone plugs in something this app has no reader for.
        Nothing lies: describe() says UNKNOWN and sources() returns empty."""
        described = provider_meter.describe("some-local-model", object())
        self.assertEqual(described["completion_state"], provider_meter.UNKNOWN)
        self.assertIsNone(described["input_tokens"])
        self.assertIsNone(described["model_reported"])
        self.assertEqual(described["sources"], [])
        self.assertEqual(provider_meter.sources("some-local-model", object()), [])


class CapabilityGapsAreStatedTests(unittest.TestCase):
    """#112's distinction, arriving at the provider boundary: "this provider does not report
    that" is not the same as "this provider reported nothing this time", and a user plugging in
    a local model would otherwise see only the second."""

    def test_a_fully_capable_provider_reports_no_gaps(self):
        for pid in providers.ids():
            self.assertEqual(providers.get(pid).capability_gaps(), (), pid)

    def test_a_bare_provider_names_every_thing_it_cannot_tell_the_app(self):
        bare = providers.Provider(
            id="local", label="Local model", call=lambda *a: "", is_configured=lambda k: True,
            key_field="local")
        gaps = bare.capability_gaps()
        self.assertEqual(len(gaps), 4)
        joined = " ".join(gaps)
        for expected in ("cut off", "tokens", "actually served", "unattributed"):
            self.assertIn(expected, joined)

    def test_the_gap_wording_names_the_consequence_not_the_field(self):
        """"reports_sources=False" means nothing to a user. "findings from it stay unattributed"
        tells them what they will actually see and why."""
        bare = providers.Provider(
            id="local", label="Local", call=lambda *a: "", is_configured=lambda k: True,
            key_field="local")
        self.assertIn("findings from it stay unattributed", " ".join(bare.capability_gaps()))

    def test_gaps_are_surfaced_in_the_config_screen(self):
        """A declaration nothing reads is worse than none -- it looks handled."""
        self.assertIn("capability_gaps()", _APP)


class AddingAProviderIsAnInterfaceFillTests(unittest.TestCase):
    """The whole point, exercised: register something new and watch every derived table pick it
    up without any of them being edited."""

    def setUp(self):
        self._saved = dict(providers._REGISTRY)

    def tearDown(self):
        providers._REGISTRY.clear()
        providers._REGISTRY.update(self._saved)

    def test_a_newly_registered_provider_reaches_every_derived_surface(self):
        providers.register(providers.Provider(
            id="testvendor", label="Test Vendor", call=lambda *a: "hi",
            is_configured=lambda key: bool(key), key_field="testvendor",
            caveat="a stand-in, registered by a test"))
        self.assertIn("testvendor", providers.ids())
        self.assertEqual(providers.labels()["testvendor"], "Test Vendor")
        self.assertIn("testvendor", {p.id: p for p in providers._REGISTRY.values()})
        # available() finds it from a key lookup, with no table to update anywhere.
        self.assertIn("testvendor", providers.available(lambda field: "a-key"))
        self.assertNotIn("testvendor", providers.available(lambda field: None))

    def test_a_new_provider_with_no_readers_declares_its_gaps_rather_than_pretending(self):
        provider = providers.register(providers.Provider(
            id="testvendor", label="Test Vendor", call=lambda *a: "hi",
            is_configured=lambda key: True, key_field="testvendor"))
        self.assertEqual(len(provider.capability_gaps()), 4)
        self.assertNotIn("testvendor", provider_meter._EXTRACTORS)

    def test_re_registering_an_id_replaces_it_so_a_deployment_can_override_a_builtin(self):
        original = providers.get("claude")
        providers.register(providers.Provider(
            id="claude", label="Claude via a proxy", call=lambda *a: "",
            is_configured=lambda k: True, key_field="anthropic"))
        self.assertEqual(providers.get("claude").label, "Claude via a proxy")
        self.assertIsNot(providers.get("claude"), original)
        self.assertEqual(providers.ids().count("claude"), 1)


if __name__ == "__main__":
    unittest.main()
