"""#126 at the vocabulary layer: five constants, one word, nothing keeping them equal.

Five modules each define their own "this number was really measured" token, and all five are
the string `'measured'`:

    draft_room.APPETITE_MEASURED
    draft_strategy.DENIAL_MEASURED
    lineup_optimizer.EXPOSURE_MEASURED
    lineup_optimizer.DISPLACEMENT_MEASURED
    lineup_optimizer.BYE_MEASURED

That they agree today is a coincidence of five separate typings, not a property anything
enforces. The hazard is specific: consumers compare bases ACROSS quantities -- `pick_synthesis`
already binds `HORIZON_BASIS_MEASURED = dr.APPETITE_MEASURED` and uses it to reason about a
different quantity's basis -- so the day one module renames its token to `'measured_directly'`
or `'observed'`, every cross-quantity comparison silently starts answering "these bases differ"
for two numbers that were both measured. Nothing fails; a reader just gets a quieter, wronger
answer. That is this project's named failure mode.

WHAT THIS FILE DOES NOT DO. It does not merge the five into one constant. Whether the absence
vocabulary should have a single shared home is a live design question (#188, whose own premise
turned out to be inverted -- the "bounded/partial" state is already implemented five times under
five names, and the open decision is which name wins). Pre-empting that by collapsing these five
would be deciding it. These tests pin the CURRENT agreement so that a drift is loud, and leave
the naming decision where it belongs.

DERIVED, NOT HAND-LISTED (#126). The set is read out of the modules by suffix at runtime, so a
sixth `*_MEASURED` token added anywhere in these modules joins the invariant automatically
rather than sitting outside a list somebody forgot to extend.
"""
from __future__ import annotations

import unittest

import draft_room
import draft_strategy
import lineup_optimizer

MODULES = (draft_room, draft_strategy, lineup_optimizer)


def _measured_tokens() -> dict[str, str]:
    """Every module-level `*_MEASURED` string constant in the basis-carrying modules."""
    found: dict[str, str] = {}
    for module in MODULES:
        for name in dir(module):
            if name.endswith("_MEASURED") and not name.startswith("_"):
                value = getattr(module, name)
                if isinstance(value, str):
                    found[f"{module.__name__}.{name}"] = value
    return found


class TheMeasuredTokenIsOneWordEverywhere(unittest.TestCase):

    def test_the_population_is_not_empty_and_spans_every_module(self):
        """A rate over an empty set is not a rate. If a rename empties this, the invariant
        below would pass vacuously, so the population is asserted first."""
        tokens = _measured_tokens()
        self.assertGreaterEqual(len(tokens), 5, f"expected at least five, found {tokens}")
        for module in MODULES:
            with self.subTest(module.__name__):
                self.assertTrue(any(k.startswith(module.__name__ + ".") for k in tokens),
                                f"{module.__name__} contributes no *_MEASURED token")

    def test_every_measured_token_carries_the_same_word(self):
        tokens = _measured_tokens()
        distinct = set(tokens.values())
        self.assertEqual(
            distinct, {"measured"},
            "the 'measured' basis word has drifted apart across modules. Consumers compare "
            "bases ACROSS quantities (pick_synthesis binds HORIZON_BASIS_MEASURED to "
            f"draft_room.APPETITE_MEASURED), so this silently breaks them: {tokens}")

    def test_the_cross_quantity_binding_still_resolves(self):
        """pick_synthesis reaches into draft_room for its own measured token. That binding is
        the concrete reason the words have to agree, so it is pinned rather than described."""
        import pick_synthesis
        self.assertEqual(pick_synthesis.HORIZON_BASIS_MEASURED, draft_room.APPETITE_MEASURED)
        self.assertEqual(pick_synthesis.HORIZON_BASIS_MEASURED, "measured")


if __name__ == "__main__":
    unittest.main()
