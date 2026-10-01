"""A-F5 / C-F2 / B-F6 -- one team count, and a rosterless pick means one thing.

`#126` (one home for a vocabulary) is the register item this module answers to, with `#166` (the
companion returned with the number) for the basis half. Named here rather than only in the class
docstrings below, because `suite_taxonomy` reads the MODULE docstring and refused this file for
answering to nothing -- correctly: a module whose subject lives only in its internals is a module
nobody can place.

`team_count` was built to be the single derivation and its docstring said so: "The engine reads the
same function, so a draft with fewer seats than the league has rosters can no longer give the two
different counts." **That was false for exactly the input it names.** The seats win over every other
rule, and only the screen could pass them: the engine called `team_count(league, picks=picks)`
because `league_for_engine` carried no seats. One function, two callers, two rules, two counts --
and the count is the denominator of every replacement level.

Measured on the finding: a 10-seat draft in a 12-roster league gave the screen 10 and the engine 12,
while `pick_synthesis` spelled a third derivation inline (without the `None` filter, so it answered
3 where `team_count` answered 2) and `_round_being_decided` spelled a fourth.

THE SEATS NOW TRAVEL ON THE LEAGUE DICT (`PICK_ORDER_KEY`) rather than through four call layers,
because every layer that has to forward them is a layer that can forget to -- which is how the
engine came to be unable to see them at all.
"""

from __future__ import annotations

import pathlib
import unittest

import draft_room as dr
import league_config as lc
import pick_synthesis as ps

#: The input the consolidation names as its own purpose: fewer seats than the league has rosters.
SEATS_10 = [f"{i}" for i in range(1, 11)]
LEAGUE_12 = {"total_rosters": 12, "roster_positions": ["QB", "RB", "WR", "TE", "FLEX", "BN"]}


class TheSplitTheDocstringPromisedToCloseTests(unittest.TestCase):

    def test_the_screen_and_the_engine_now_agree_on_the_split_input(self):
        """The finding itself, as a unit fact. The screen passes seats explicitly; the engine
        passes only the league dict -- and must now reach the same number through it."""
        league = dict(LEAGUE_12, **{lc.PICK_ORDER_KEY: SEATS_10})
        screen = lc.team_count(pick_order=SEATS_10)
        engine = lc.team_count(league, picks=[{"roster_id": "1"}])
        self.assertEqual(screen, 10)
        self.assertEqual(engine, 10,
                         "the engine still reads total_rosters where the draft has 10 seats; "
                         "every replacement level on this board is about a different league "
                         "than the caption is")

    def test_without_the_key_the_two_would_still_split(self):
        """NON-VACUITY, and it names what the key is actually doing. If this ever fails, the
        seats are reaching the engine by some other route and the test above proves nothing
        about `PICK_ORDER_KEY`."""
        self.assertEqual(lc.team_count(LEAGUE_12, picks=[{"roster_id": "1"}]), 12)
        self.assertEqual(lc.team_count(pick_order=SEATS_10), 10)

    def test_an_explicit_argument_still_beats_the_key(self):
        """The screen's own call site keeps working, and a caller holding fresher seats than the
        league dict is not overridden by it."""
        league = dict(LEAGUE_12, **{lc.PICK_ORDER_KEY: SEATS_10})
        self.assertEqual(lc.team_count(league, pick_order=["a", "b"]), 2)


class TheBasisIsReturnedWithTheNumberTests(unittest.TestCase):
    """`#166`. Two of the four rules are not team counts: the picks rule is a floor (a roster that
    has not picked is invisible) and the last is arithmetic protection. A caller cannot tell those
    from a real answer unless the basis comes back with it."""

    def test_each_rule_names_itself(self):
        cases = [
            ({lc.PICK_ORDER_KEY: SEATS_10}, {}, 10, lc.TEAM_BASIS_SEATS),
            (LEAGUE_12, {}, 12, lc.TEAM_BASIS_DECLARED),
            ({}, {"picks": [{"roster_id": "1"}, {"roster_id": "2"}]}, 2, lc.TEAM_BASIS_PICKS),
            ({}, {}, 1, lc.TEAM_BASIS_FLOOR),
        ]
        for league, kwargs, expected, basis in cases:
            with self.subTest(basis=basis):
                self.assertEqual(lc.team_count_with_basis(league, **kwargs), (expected, basis))

    def test_the_count_and_the_basis_come_from_ONE_body(self):
        """A companion computed beside the number instead of with it is `#166`'s own failure
        mode, so `team_count` must BE the first element and not a second implementation."""
        for league, kwargs in [({lc.PICK_ORDER_KEY: SEATS_10}, {}), (LEAGUE_12, {}),
                               ({}, {"picks": [{"roster_id": "7"}]}), ({}, {})]:
            with self.subTest(league=league):
                self.assertEqual(lc.team_count(league, **kwargs),
                                 lc.team_count_with_basis(league, **kwargs)[0])

    def test_the_floor_is_distinguishable_from_a_real_one_team_league(self):
        """The distinction `_round_being_decided` depends on. Both answer 1; only one of them
        knows anything."""
        self.assertEqual(lc.team_count_with_basis({}, )[1], lc.TEAM_BASIS_FLOOR)
        self.assertEqual(lc.team_count_with_basis({"total_rosters": 1})[1], lc.TEAM_BASIS_DECLARED)


class NoModuleSpellsItsOwnTeamCountTests(unittest.TestCase):
    """The consolidation is only real while it holds. Two of the four derivations this item is
    about were reintroduced AFTER `team_count` existed, in a module that already imported it."""

    #: The pre-consolidation form, as it actually appeared.
    RETIRED = 'league.get("total_rosters") or len({p.get("roster_id")'

    #: A test module NAMING the retired form is documenting it, not spelling it. This exclusion is
    #: the reason the check is written against the production modules only: the first version
    #: flagged this very file and `test_three_derivations_of_one_number.py`, both of which quote
    #: the form precisely so a reader can see what was retired.
    #: AN EXPLICIT LIST, not every module in the tree. `x // y + 1` is ordinary arithmetic and a
    #: tree-wide `ast` scan flagged fifteen sites -- thirteen of them one-off `run_*` probes and a
    #: trace fixture fabricating synthetic picks, none of which prices a board or labels a pick for
    #: a person. Naming the modules keeps the claim checkable and keeps it honest about its reach:
    #: this is the set where a wrong round or a wrong team count reaches a decision.
    #:
    #: `app.py` earns its place -- the scan found a real fourth copy there (the mock draft's own
    #: round label), which is the first of the three sites `round_of`'s docstring says it replaced.
    #: `app.py` is NOT here, and not because it is exempt -- it carries a real find below. The UI
    #: surface is read through `ui_source`, because an `app.py` read stops covering anything the
    #: moment a view is extracted from it (`test_ui_source`'s own rule, which caught this file).
    DECISION_MODULES = ("draft_room.py", "pick_synthesis.py", "draft_strategy.py",
                        "lineup_optimizer.py", "league_config.py")

    @classmethod
    def _production_modules(cls):
        return [pathlib.Path(n) for n in cls.DECISION_MODULES if pathlib.Path(n).exists()]

    def test_the_module_set_is_not_empty(self):
        """A scan over nothing passes trivially."""
        self.assertGreaterEqual(len(self._production_modules()), 4)

    def test_the_UI_surface_does_not_spell_the_round_arithmetic_either(self):
        """The fourth copy, found by the scan that flagged this file's own scope: the mock
        draft's round label read `current_index // settings["teams"] + 1`, which is the first of
        the three sites `round_of`'s docstring says it was built to replace. Checked through
        `ui_source.text()` so it keeps covering the view after that view is extracted."""
        import ui_source
        self.assertNotIn('// settings["teams"] + 1', ui_source.text(),
                         "the UI recomputes round_of's arithmetic for its round label")

    def test_the_inline_derivation_is_gone_from_the_tree(self):
        offenders = [str(q) for q in self._production_modules()
                     if self.RETIRED in q.read_text(encoding="utf-8")]
        self.assertEqual(offenders, [],
                         f"{offenders} spell the retired team-count derivation inline")

    def test_nothing_but_league_config_spells_the_round_arithmetic(self):
        """`round_of` is the one home for `n // teams + 1` (`#126`), and `_round_being_decided`
        was a second copy of it.

        READ AS CODE, NOT AS TEXT. A substring scan for `// teams + 1` matches the four comments
        and docstrings that EXPLAIN the consolidation -- including the one this repair added -- so
        it reported offenders that were prose about the fix. `ast` sees only the arithmetic."""
        import ast
        offenders = []
        for q in self._production_modules():
            if q.name == "league_config.py":
                continue
            for node in ast.walk(ast.parse(q.read_text(encoding="utf-8"))):
                if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)
                        and isinstance(node.left, ast.BinOp)
                        and isinstance(node.left.op, ast.FloorDiv)
                        and isinstance(node.right, ast.Constant) and node.right.value == 1):
                    offenders.append(f"{q}:{node.lineno}")
        self.assertEqual(offenders, [],
                         f"{offenders} recompute round_of's `n // teams + 1` in code")


class ARosterlessPickBelongsToNoRosterTests(unittest.TestCase):
    """B-F6. `team_count` filtered a `None` roster id out; `team_slots_filled` keyed it as the
    STRING "None", which is a perfectly good dict key -- so one such pick made the per-team census
    cover one more roster than the league had teams, and the board build raised."""

    PLAYERS = {
        "1": {"first_name": "A", "last_name": "One", "position": "QB", "fantasy_positions": ["QB"]},
        "2": {"first_name": "B", "last_name": "Two", "position": "RB", "fantasy_positions": ["RB"]},
    }
    ROSTER = ["QB", "RB", "WR", "TE", "FLEX", "BN"]

    def test_the_phantom_roster_is_not_created(self):
        picks = [{"player_id": "1", "roster_id": "1"}, {"player_id": "2", "roster_id": None}]
        filled = dr.team_slots_filled(picks, self.PLAYERS, self.ROSTER)
        self.assertNotIn("None", filled, "a rosterless pick still creates a phantom roster")
        self.assertEqual(set(filled), {"1"})

    def test_the_two_functions_agree_on_what_a_rosterless_pick_MEANS(self):
        """The actual defect was not either rule; it was that they disagreed (`#126`).

        ASKS THE QUESTION, NOT FOR GENERAL EQUALITY. This asserted
        `len(team_slots_filled(...)) == team_count(picks=...)`, which is not a property of the two
        functions: the census ALSO skips a pick whose player the pool cannot resolve to an eligible
        position, and the count does not, so the equality held on this two-pick fixture and would
        have failed for a reason with nothing to do with rosterless picks. Measured: a roster whose
        only pick is a player the pool does not know gives census 1 against count 2.
        """
        picks = [{"player_id": "1", "roster_id": "1"}, {"player_id": "2", "roster_id": None}]
        self.assertNotIn("None", dr.team_slots_filled(picks, self.PLAYERS, self.ROSTER),
                         "the census still invents a roster for a rosterless pick")
        self.assertEqual(1, lc.team_count(picks=picks),
                         "the count still counts a rosterless pick as a team")

    def test_a_pick_whose_PLAYER_IS_UNKNOWN_is_why_general_equality_is_not_the_property(self):
        """The control for the test above, and the measurement that retired its old assertion.

        Not a defect in either function -- the census is about slots that got FILLED and an
        unresolvable player fills none, while the count is about who is DRAFTING and he was
        drafted by someone. Pinned so the equality is not reinstated by someone reading the two
        numbers as the same question."""
        picks = [{"player_id": "1", "roster_id": "1"}, {"player_id": "9999", "roster_id": "2"}]
        self.assertEqual(1, len(dr.team_slots_filled(picks, self.PLAYERS, self.ROSTER)))
        self.assertEqual(2, lc.team_count(picks=picks))

    def test_the_two_rules_read_a_roster_id_AS_THE_SAME_TYPE(self):
        """The residue B-F6 left (review finding 7). `0` and `"0"` are one roster to the census
        and were two teams to the count, because the picks rule was the only one of the three not
        keying on `str(...)`. Sleeper hands integers; several app paths stringify."""
        picks = [{"player_id": "1", "roster_id": 0}, {"player_id": "2", "roster_id": "0"}]
        self.assertEqual(1, len(dr.team_slots_filled(picks, self.PLAYERS, self.ROSTER)),
                         "non-vacuity: the census must see ONE roster for this history")
        self.assertEqual(1, lc.team_count(picks=picks),
                         "the picks rule counts `0` and `\"0\"` as two teams")

    def test_the_seats_rule_was_ALREADY_type_insensitive(self):
        """Why the repair went in the picks rule rather than anywhere else: the authority it was
        supposed to match already behaved this way, in the same function."""
        self.assertEqual(1, lc.team_count(pick_order=[0, "0"]))

    def test_remaining_starter_demand_no_longer_raises(self):
        """End to end, because the consequence was a crash and not a discrepancy."""
        picks = [{"player_id": "1", "roster_id": "1"}, {"player_id": "2", "roster_id": None}]
        demand = dr.remaining_starter_demand(self.ROSTER, 1, picks, self.PLAYERS)
        self.assertIsInstance(demand, dict)
        self.assertTrue(demand, "no demand was computed at all")

    def test_a_genuinely_foreign_history_is_STILL_refused(self):
        """The guard the fix must not disarm: more real rosters than the league has teams is a
        history from another league, and it is refused rather than modelled."""
        picks = [{"player_id": "1", "roster_id": "1"}, {"player_id": "2", "roster_id": "2"}]
        with self.assertRaises(ValueError):
            dr.remaining_starter_demand(self.ROSTER, 1, picks, self.PLAYERS)


class TheRoundFallbackSurvivesTheConsolidationTests(unittest.TestCase):
    """`team_count` floors at 1, so routing `_round_being_decided` through it BARE would turn "no
    basis" into "a one-team league" and answer `len(picks) + 1` -- where this caller has a better
    answer in the round its own picks carry. That is the fallback `round_of` declines to guess at."""

    def test_a_label_still_answers_directly(self):
        self.assertEqual(ps._round_being_decided("7.03", [{"round": 2}], None), 7)

    def test_with_no_team_count_anywhere_the_recorded_round_wins(self):
        picks = [{"round": 3}, {"round": 3}, {"round": 3}]
        self.assertEqual(
            ps._round_being_decided(None, picks, None), 3,
            "the floor of 1 was read as a one-team league, so this answered len(picks) + 1")

    def test_with_a_real_count_the_arithmetic_is_round_of(self):
        league = {"total_rosters": 10}
        picks = [{"roster_id": str(i % 10)} for i in range(25)]
        self.assertEqual(ps._round_being_decided(None, picks, league),
                         lc.round_of(25, 10))

    def test_the_seats_reach_this_derivation_too(self):
        """It takes a league dict, so the key reaches it for free -- and must, or the round label
        splits from the board the same way the count did."""
        league = {"total_rosters": 12, lc.PICK_ORDER_KEY: SEATS_10}
        picks = [{"roster_id": str(i % 10)} for i in range(20)]
        self.assertEqual(ps._round_being_decided(None, picks, league), lc.round_of(20, 10))


if __name__ == "__main__":
    unittest.main()
