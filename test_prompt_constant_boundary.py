"""#90 / ARCHITECTURE_AUDIT 8.3 + 4.6: the engine's constants must not travel to a model
provider, and that must be ENFORCED rather than merely conventional.

§8.3 of the Build Guide's mandate is that "the master CDME equation, coefficients,
normalization and proprietary implementation details must not depend on prompt compliance
for confidentiality." The Pass-1 audit found the property held -- and that nothing held it:
no mechanism prevented a future prompt edit from pasting a coefficient in, and no test would
have caught it. This file is that mechanism. It is deliberately a *contract* test, not a
characterization of today's strings: it discovers the engine's constants and the app's
prompt surface by walking the source, so a constant added tomorrow, or a prompt added
tomorrow, is covered without anyone remembering to update a list here.

Two scans, for two different failure shapes:

  NAME scan (decisive).  An engine constant's identifier appearing anywhere in prompt text
  is never innocent -- prose has no reason to say NECESSITY_STANDOUT_WEIGHT. One deliberate
  exception is recorded in DISCLOSED_BY_DESIGN below, with its reasoning.

  VALUE scan (advisory, and narrow on purpose).  A bare number cannot be scanned for: 12,
  0.5 and 17 all occur legitimately in English. So the value scan covers only constants
  whose literal is distinctive enough that an appearance is evidence rather than noise
  (see _DISTINCTIVE_VALUE_MIN_DECIMALS), and it is the reason this file does not claim to
  prove the absence of every coefficient -- only the absence of the recognizable ones. The
  name scan is what actually holds the boundary; the value scan is a second net with
  honestly-stated holes.

Scope note: the prompt surface is not just the *_SYSTEM_PROMPT constants. app.py's
build_context() assembles the largest single block of text any provider receives, and
screen_context's builders assemble what the Trade Calculator seeds a question with. Both
are string-literal sources inside the prompt path, so both are scanned. A future prompt
producer must be added to PROMPT_SOURCE_MODULES or _app_prompt_prose to be covered -- see
PromptSurfaceCoverageTests, which fails if the discovered surface shrinks below what this
file was written against.
"""

import ast
import re
import unittest
from pathlib import Path

import bot_config
import llm_engine
import pick_debate
import ui_source

_HERE = Path(__file__).parent

# Every module whose module-level UPPER_CASE numeric constants are engine parameters --
# the quantities §8.3 says must not depend on prompt compliance for confidentiality.
ENGINE_MODULES = (
    "draft_room", "pick_synthesis", "draft_strategy", "rookie_draft",
    "data_merger", "lineup_optimizer",
)

# Modules whose string constants can be sent verbatim to a provider.
PROMPT_SOURCE_MODULES = (llm_engine, pick_debate, bot_config)

# The one engine identifier a prompt is allowed to name, and why.
#
# build_context() hands each chair a per-player "composite score" and then explains what
# that number is: a blend across loaded vendor sources. Naming COMPOSITE_SOURCE_WEIGHTS
# (and data_merger.py) is how the chair is told the figure is a *weighted* read rather than
# an average, so it can weigh the per-source disagreement beside it instead of treating the
# blend as settled. It discloses the weight set's existence and direction, never a weight:
# the values 1.3 / 1.0 / 0.7 / 0.5 do not appear, and this is a vendor-blending parameter in
# data_merger, not a term in the CDME valuation equation -- universal_value, its
# normalization, and its coefficients remain absent from every prompt.
#
# Anything added here needs the same two sentences: what is disclosed, and why the decision
# layer is worse off without it.
DISCLOSED_BY_DESIGN = {"COMPOSITE_SOURCE_WEIGHTS"}

# A value is only scannable when seeing it in prose is evidence. Two decimal places is the
# line: 0.5 and 12.0 are ordinary English, 1.6 and 2.5 are borderline, 0.32 and 0.55 are not
# numbers anybody writes by accident in a fantasy-football instruction.
_DISTINCTIVE_VALUE_MIN_DECIMALS = 2


def _decimal_places(value: float) -> int:
    """Digits after the point in repr(). Exponent-form floats (DEMAND_WHOLE_SLOT_TOLERANCE
    reprs as '1e-09') have no point at all -- they are not text a prompt would ever contain,
    so they score 0 and drop out of the distinctive set rather than raising."""
    text = repr(value)
    if "e" in text or "E" in text or "." not in text:
        return 0
    return len(text.split(".")[1])


def _module_constants(module_name: str) -> dict[str, list[float]]:
    """{CONSTANT_NAME: [numeric literals inside it]} for one engine module.

    Both Assign and AnnAssign: COMPOSITE_SOURCE_WEIGHTS is annotated
    (`COMPOSITE_SOURCE_WEIGHTS: dict[str, float] = {...}`), and an Assign-only walk is
    silently blind to it and to every other annotated constant -- which is exactly the
    vacuity a boundary test must not have.
    """
    tree = ast.parse((_HERE / f"{module_name}.py").read_text())
    found: dict[str, list[float]] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            target = node.target
        else:
            continue
        if not isinstance(target, ast.Name) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", target.id):
            continue
        values = [
            n.value for n in ast.walk(node.value)
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
            and not isinstance(n.value, bool)
        ]
        if values:
            found[target.id] = values
    return found


def engine_constants() -> dict[str, list[float]]:
    merged: dict[str, list[float]] = {}
    for module_name in ENGINE_MODULES:
        for name, values in _module_constants(module_name).items():
            merged.setdefault(name, []).extend(values)
    return merged


def _module_prompt_strings(module) -> dict[str, str]:
    """Long string constants on a module that can reach a provider: the *_PROMPT /
    *_ADDENDUM constants themselves, plus the string values inside UPPER_CASE dicts (the
    Moderator personality directives are appended to that chair's system prompt)."""
    out: dict[str, str] = {}
    for attr in dir(module):
        if not attr.isupper():
            continue
        value = getattr(module, attr)
        if isinstance(value, str) and len(value) > 40:
            out[f"{module.__name__}.{attr}"] = value
        elif isinstance(value, dict):
            for key, item in value.items():
                if isinstance(item, str) and len(item) > 40:
                    out[f"{module.__name__}.{attr}[{key!r}]"] = item
    return out


def _function_prose(source: str, func_name: str) -> str:
    """Every string literal inside one top-level function, joined. Used for the two prompt
    producers that build their text inline rather than storing it in a constant."""
    start = source.index(f"def {func_name}(")
    end = source.index("\ndef ", start + 10)
    literals = [
        n.value for n in ast.walk(ast.parse(source[start:end]))
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    ]
    return "\n".join(literals)


def prompt_surface() -> dict[str, str]:
    """{label: text} for every string this app can put in front of a model provider."""
    surface: dict[str, str] = {}
    for module in PROMPT_SOURCE_MODULES:
        surface.update(_module_prompt_strings(module))
    app_source = ui_source.text()
    surface["app.build_context"] = _function_prose(app_source, "build_context")
    surface["screen_context (all literals)"] = "\n".join(
        n.value for n in ast.walk(ast.parse((_HERE / "screen_context.py").read_text()))
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    )
    return surface


class EngineConstantsDoNotAppearInPromptsTests(unittest.TestCase):
    def test_no_engine_constant_name_appears_in_any_prompt(self):
        constants = engine_constants()
        hits = [
            (label, name)
            for label, text in prompt_surface().items()
            for name in constants
            if name not in DISCLOSED_BY_DESIGN and name in text
        ]
        self.assertEqual(
            hits, [],
            "An engine constant's NAME reached the prompt surface. Either remove it, or -- if "
            "the decision layer genuinely needs it -- add it to DISCLOSED_BY_DESIGN with the "
            "two sentences that entry requires.",
        )

    def test_distinctive_engine_constant_values_do_not_appear_in_any_prompt(self):
        """The advisory half. Only constants whose literal is distinctive enough that an
        appearance is evidence -- see _DISTINCTIVE_VALUE_MIN_DECIMALS and this module's
        docstring on why the value scan cannot be complete."""
        distinctive: dict[float, str] = {}
        for name, values in engine_constants().items():
            for value in values:
                if isinstance(value, float) and not value.is_integer():
                    if _decimal_places(value) >= _DISTINCTIVE_VALUE_MIN_DECIMALS:
                        distinctive.setdefault(value, name)
        # Guard against the scan quietly emptying itself out.
        self.assertGreaterEqual(
            len(distinctive), 5,
            "The distinctive-value set collapsed -- the value scan would pass vacuously.",
        )
        hits = []
        for label, text in prompt_surface().items():
            for value, name in distinctive.items():
                # Word-bounded so 0.55 does not match inside 10.559.
                if re.search(rf"(?<![\d.]){re.escape(repr(value))}(?![\d])", text):
                    hits.append((label, name, value))
        self.assertEqual(hits, [], "A distinctive engine coefficient's VALUE reached the prompt surface.")

    def test_the_disclosed_exception_is_still_only_the_weight_set_name(self):
        """DISCLOSED_BY_DESIGN buys the *name*, never the numbers behind it. If someone
        later pastes the actual weights into that same sentence, the name scan would still
        pass on the exception -- this is what catches it."""
        weights = [v for v in engine_constants()["COMPOSITE_SOURCE_WEIGHTS"]]
        self.assertTrue(weights, "COMPOSITE_SOURCE_WEIGHTS carries no numeric literals to check.")
        prose = prompt_surface()["app.build_context"]
        leaked = [w for w in weights if re.search(rf"(?<![\d.]){re.escape(repr(w))}(?![\d])", prose)]
        self.assertEqual(leaked, [], "The composite weight VALUES leaked into build_context's prose.")


class ScanIsNotVacuousTests(unittest.TestCase):
    """A boundary test that cannot fail is worse than no test, because it reads as proof."""

    def test_the_constant_discovery_actually_finds_the_engine(self):
        constants = engine_constants()
        self.assertGreater(len(constants), 40, "Constant discovery collapsed.")
        # Named anchors across four modules and both assignment forms.
        for expected in ("NEED_BONUS_MAX", "NEAR_TIE_BAND", "RANK_TAKE_PROBABILITY",
                         "FUTURE_YEAR_RECORD_DISCOUNT", "COMPOSITE_SOURCE_WEIGHTS"):
            self.assertIn(expected, constants, f"{expected} was not discovered.")

    def test_annotated_constants_are_discovered(self):
        """COMPOSITE_SOURCE_WEIGHTS is an AnnAssign. An Assign-only walk missed it during
        this pass's own measurement, so the regression is pinned by name."""
        self.assertIn("COMPOSITE_SOURCE_WEIGHTS", _module_constants("data_merger"))

    def test_the_prompt_surface_actually_finds_the_prompts(self):
        surface = prompt_surface()
        for expected in ("llm_engine.QUANT_SYSTEM_PROMPT", "llm_engine.MODERATOR_SYSTEM_PROMPT",
                         "pick_debate.STRATEGIST_SYSTEM_PROMPT", "pick_debate.CALLER_SYSTEM_PROMPT",
                         "app.build_context"):
            self.assertIn(expected, surface, f"{expected} is not in the scanned prompt surface.")
        self.assertGreater(len(surface["app.build_context"]), 5000,
                           "build_context's prose came back too small to be the real function.")

    def test_the_name_scan_fires_when_a_constant_is_planted(self):
        constants = engine_constants()
        planted = "You are the Quant. Use NECESSITY_STANDOUT_WEIGHT when scoring."
        self.assertIn("NECESSITY_STANDOUT_WEIGHT", constants)
        self.assertTrue(
            any(name in planted for name in constants if name not in DISCLOSED_BY_DESIGN),
            "The name scan does not fire on a deliberately planted constant name.",
        )

    def test_the_value_scan_fires_when_a_coefficient_is_planted(self):
        planted = "Weight the top-ranked player at 0.55 and the second at 0.32."
        distinctive = {
            v for values in engine_constants().values() for v in values
            if isinstance(v, float) and not v.is_integer()
            and _decimal_places(v) >= _DISTINCTIVE_VALUE_MIN_DECIMALS
        }
        fired = [v for v in distinctive if re.search(rf"(?<![\d.]){re.escape(repr(v))}(?![\d])", planted)]
        self.assertTrue(fired, "The value scan does not fire on planted RANK_TAKE_PROBABILITY values.")


class PromptSurfaceCoverageTests(unittest.TestCase):
    """The scan is only as good as its idea of where prompts live. This fails if the
    surface shrinks -- a prompt producer renamed or moved out from under the scan looks
    identical to 'no violations found' otherwise."""

    def test_every_known_prompt_producer_is_covered(self):
        surface = prompt_surface()
        self.assertGreaterEqual(
            len(surface), 16,
            "The discovered prompt surface shrank. A prompt producer was renamed, moved, or "
            "dropped -- re-point the scan at it rather than accepting a smaller surface.",
        )

    def test_the_four_prytaneum_chairs_and_three_draft_room_chairs_are_all_scanned(self):
        surface = prompt_surface()
        for chair in ("QUANT", "BEAT", "CONTRARIAN", "MODERATOR"):
            self.assertIn(f"llm_engine.{chair}_SYSTEM_PROMPT", surface)
        for chair in ("STRATEGIST", "SKEPTIC", "CALLER"):
            self.assertIn(f"pick_debate.{chair}_SYSTEM_PROMPT", surface)


if __name__ == "__main__":
    unittest.main()
