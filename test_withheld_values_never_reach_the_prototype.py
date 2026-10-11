"""#295: the withheld survival family must not reach a person through the Doors A prototype.

`pick_synthesis.withheld_fields` states the rule: "A quantity withheld from presentation must
not reach a person, on any surface, under any name, as itself or as a delta of itself." Four
engine surfaces are audited for it. The UI-exploration prototype is a FIFTH, and it was the only
one enforcing the rule with nothing but a line of build script -- `_build.py` pops the withheld
keys out of each candidate before inlining the fixture, and no test said it had to.

An outside reviewer put the case exactly right: a hidden field in a pretty interface is not a
withheld result, it is a visible result with a curtain over it. The curtain here turned out to be
real -- 0 of 700 rows in every built artifact carry a value. What was missing is the thing that
keeps it real after the next refactor.

THE VACUITY GUARD IS THE POINT OF THE FIRST TEST. An artifact that never had the fields would
pass the absence check while proving nothing, so the SOURCE fixture is checked for their presence
first. That is the shape of the failure this repo keeps re-learning: the terminology guard whose
live population was zero could fire, but had nothing in range to fire at.
"""
import json
import pathlib
import unittest

import pick_synthesis as ps

_ART = pathlib.Path(__file__).parent / "ui_explore" / "round2" / "fableA"
_FIXTURE = pathlib.Path(__file__).parent / "ui_explore" / "fixture.json"
#: Every HTML in the directory, not just the five the build emits. A committed artifact is one
#: someone can open, and `_v1_ledger_rail_prev.html` carries an older payload schema -- which is
#: why the walk below is schema-agnostic rather than reaching for a known key path.
_HTML = sorted(_ART.glob("*.html"))
_PAYLOAD = "const DATA="

#: Committed artifacts the build no longer emits, whose inlined text therefore cannot be
#: regenerated. They are checked for withheld VALUES like everything else -- and carry none --
#: and are exempt only from the wording check below. A COUNT-PINNED set, not an open predicate:
#: the guard that used to scan one directory had a live population of zero and could not say so.
_FROZEN_CARRIERS = {"_v1_ledger_rail_prev.html"}


def _payload(path: pathlib.Path) -> dict:
    """The inlined DATA object, parsed. `raw_decode` rather than a regex: the payload embeds
    base64 fonts and arbitrary prose, and a non-greedy `.*?};` can end on a brace inside a
    string."""
    text = path.read_text()
    start = text.find(_PAYLOAD)
    assert start >= 0, f"{path.name} carries no {_PAYLOAD} payload"
    obj, _ = json.JSONDecoder().raw_decode(text, start + len(_PAYLOAD))
    return obj


def _withheld_values(obj, path="$"):
    """Every (location, field, value) in the payload holding a withheld field with a value.

    Walks the WHOLE object rather than the candidate rows, so a future schema that moves
    candidates, or adds a second place carrying them, is covered without this file being told.
    A None is not a leak: the absence contract (#187) uses a present key with no value to say
    "this was asked and does not exist", which is a different statement from a suppressed one.
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in ps.SURVIVAL_DERIVED_FIELDS and value is not None:
                yield (path, key, value)
            yield from _withheld_values(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from _withheld_values(value, f"{path}[{i}]")


def _candidates(obj):
    for arm in (obj.get("formats") or {}).values():
        for state in (arm.get("states") or {}).values():
            yield state, state.get("candidates", [])


class TheSourceFixtureActuallyCarriesWhatTheArtifactMustNotTests(unittest.TestCase):
    """The vacuity guard. Without this, every assertion below passes on an empty file."""

    def test_every_candidate_in_the_fixture_carries_the_withheld_family_as_numbers(self):
        fixture = json.loads(_FIXTURE.read_text())
        rows = missing = 0
        for arm in fixture.values():
            for state in arm["states"].values():
                for cand in state.get("candidates", []):
                    rows += 1
                    for field in ps.SURVIVAL_DERIVED_FIELDS:
                        if not isinstance(cand.get(field), (int, float)):
                            missing += 1
        self.assertGreater(rows, 0, "the fixture has no candidates; every check here is vacuous")
        self.assertEqual(
            missing, 0,
            "the source fixture no longer carries the withheld family on every row, so the "
            "absence checks below prove nothing. Re-capture the fixture, or retire this file.")

    def test_the_fixture_takes_the_family_from_the_engine_and_not_from_a_second_list(self):
        # capture_fixture.py writes `sorted(ps.withheld_fields())`. If the calibration flag ever
        # flips, withheld_fields() empties, the committed fixture goes stale, and this fails --
        # which is the trigger to re-capture, in the spirit of test_threshold_reachability. It is
        # not a silencer.
        fixture = json.loads(_FIXTURE.read_text())
        expected = sorted(ps.withheld_fields())
        for fmt, arm in fixture.items():
            for name, state in arm["states"].items():
                self.assertEqual(sorted(state.get("withheld", [])), expected,
                                 f"{fmt}/{name} declares a withheld list the engine did not give it")


class NoBuiltArtifactCarriesAWithheldValueTests(unittest.TestCase):
    def test_the_directory_holds_artifacts_to_check(self):
        self.assertGreaterEqual(len(_HTML), 5, "the built artifacts are missing; nothing was checked")

    def test_no_committed_artifact_carries_a_withheld_value_anywhere_in_its_payload(self):
        for path in _HTML:
            with self.subTest(artifact=path.name):
                leaks = list(_withheld_values(_payload(path)))
                self.assertEqual(
                    leaks[:5], [],
                    f"{path.name} ships {len(leaks)} withheld value(s) inside its inlined data, "
                    "one view-source away from a reader")

    def test_the_strip_is_targeted_and_leaves_the_shown_quantities_alone(self):
        # A blanket drop would also pass the check above while gutting the board. `waiting_cost`
        # is shown, is NOT part of the survival family, and must survive the build.
        for path in _HTML:
            obj = _payload(path)
            rows = [c for _, cands in _candidates(obj) for c in cands]
            if not rows:
                continue              # `_v1_ledger_rail_prev.html` has an older, formats-less schema
            with self.subTest(artifact=path.name):
                kept = sum(1 for c in rows if c.get("waiting_cost") is not None)
                self.assertGreater(kept, 0, f"{path.name} lost waiting_cost, a quantity it shows")

    def test_the_withheld_names_survive_so_the_panel_says_withheld_and_not_nothing(self):
        # Stripping the names too would leave the reader with silence, which #187 forbids: a
        # suppressed number must read as suppressed, never as absent and never as missing.
        for path in _HTML:
            obj = _payload(path)
            states = [s for s, _ in _candidates(obj)]
            if not states:
                continue
            with self.subTest(artifact=path.name):
                for state in states:
                    self.assertEqual(sorted(state.get("withheld", [])), sorted(ps.withheld_fields()))


class TheReasonForWithholdingHasOneHomeTests(unittest.TestCase):
    """`WITHHELD_REASON` exists because "a hand-copied sentence in each is four places to go stale
    the day SURVIVAL_IS_CALIBRATED flips". The prototype had hand-copied a fifth. Its wording was
    accurate -- the calibration failure is real and evidenced -- which is exactly the state a
    second home is in right before it drifts."""

    def test_every_artifact_carries_the_engine_sentence_verbatim(self):
        for path in _HTML:
            obj = _payload(path)
            vocab = obj.get("vocab")
            if vocab is None:
                continue
            with self.subTest(artifact=path.name):
                self.assertEqual(vocab.get("WITHHELD_REASON"), ps.WITHHELD_REASON)
                self.assertEqual(vocab.get("WITHHELD_CARD_TEXT"), ps.WITHHELD_CARD_TEXT)

    def test_the_hand_written_sentence_has_not_come_back(self):
        """Caught a live carrier on its first run: `_v1_ledger_rail_prev.html`, a committed
        artifact the build no longer emits, so its inlined copy of the old sentence cannot be
        regenerated away. Nothing references the file and the build has no rule for it -- it
        arrived incidentally in 96105d2 ("Add the Fable sources the previous commit silently
        dropped"). Exempted BY NAME and pinned, the way the terminology guard pins its mockup
        debt, so the exemption cannot quietly widen to cover a live source. Deleting the file is
        the owner's call, not a test's; when it goes, drop it from the set below and this fails
        until someone does."""
        stale = "it failed calibration against real drafts"
        sources = [p for p in sorted((_ART / "_src").glob("*")) + _HTML if p.is_file()]
        self.assertGreater(len(sources), 5, "nothing was scanned")
        carriers = {p.name for p in sources if stale in p.read_text(errors="ignore")}
        self.assertEqual(
            sorted(carriers - _FROZEN_CARRIERS), [],
            "the withheld reason is written out again instead of read from pick_synthesis")
        self.assertEqual(
            carriers, _FROZEN_CARRIERS,
            "the frozen-carrier set moved. If the stale artifact was deleted, remove it from "
            "_FROZEN_CARRIERS; if one was added, that is the regression this pins")


if __name__ == "__main__":
    unittest.main()
