"""#52 phase 7.4: the key over a cached snapshot must contain every input that can change it.

The Draft Room cached a built PickSnapshot in session state under a key written by hand at the
call site:

    (draft_id, target_index, my_roster_id, pool_scope, len(draft_picks), merger.freshest_date)

`build_snapshot` takes fifteen inputs. Three of those six are proxies for one of them, and
`len(draft_picks)` shows what a proxy costs: it is a COUNT standing in for CONTENTS. Measured
on the real rulebook, at one constant key (see TwoWorldsTheOldKeyCouldNotTellApartTests):

  * a commissioner undo and re-pick, count unchanged -- Drake London enters the top five at
    93.70, from absent.
  * season_projections arriving on a mid-draft sync -- the leader changes from Tyler Warren to
    Bijan Robinson and universal_value goes 76.32 -> 219.61.

Both were served from cache as the same world.

The repair is not "add the two missing dimensions". A hand-written key next to a fifteen-input
call is a second statement of what that call reads, and it will fall behind again the next time
an argument is added -- which is #126 (one home for a vocabulary) wearing a cache's clothes.
snapshot_input_key derives itself from build_snapshot's own signature, so the tests below are
about the DERIVATION, not about the six dimensions that happened to be wrong.
"""

from __future__ import annotations

import inspect
import unittest
from unittest import mock

import pandas as pd

import draft_room as dr
import pick_synthesis as ps


class _FakeMerger:
    """Just enough merger for the fingerprinter, which is all the KEY ever touches.

    These tests never call build_snapshot -- they measure the key over its inputs -- so nothing
    here needs a real pool, and that is what keeps this file a sub-second unit suite. The real
    boards live in the last class.
    """

    def __init__(self, salt: int = 0):
        for name in dr._ANCHOR_FRAMES:
            setattr(self, name, pd.DataFrame({"v": [salt, salt + 1]}))
        self.freshest_date = f"2026-09-{10 + salt:02d}"


def _base_inputs() -> dict:
    return dict(
        merger=_FakeMerger(0),
        players_db={"100": {"position": "RB", "team": "PHI", "fantasy_positions": ["RB"]}},
        picks=[{"player_id": "100", "roster_id": 1, "pick_no": 1}],
        pick_order=[1, 2, 3, 4],
        current_index=1,
        my_roster_id="2",
        league={"roster_positions": ["QB", "RB", "FLEX"], "total_rosters": 12,
                "scoring_settings": {"rec": 1.0}, "settings": {"type": 2}},
        pick_label="1.02",
        mode="balanced",
        pool_scope="all",
        top_n=8,
        user_selected_player_id=None,
        sleeper_projections=None,
        sleeper_basis=dr.SLEEPER_BASIS_WEEKLY,
        upside_rule=dr.UPSIDE_RULE_ROUND,
    )


#: One materially different value per build_snapshot parameter. Not a convenience table -- its
#: KEYS are asserted equal to the signature below, so an argument added to build_snapshot
#: cannot reach production until someone has said here what a change to it looks like. That
#: assertion is the ratchet; the loop under it is the measurement.
ALTERNATES = {
    "merger": _FakeMerger(7),
    "players_db": {"100": {"position": "WR", "team": "PHI", "fantasy_positions": ["WR"]}},
    "picks": [{"player_id": "999", "roster_id": 1, "pick_no": 1}],
    "pick_order": [4, 3, 2, 1],
    "current_index": 2,
    "my_roster_id": "3",
    "league": {"roster_positions": ["QB", "RB", "FLEX"], "total_rosters": 10,
               "scoring_settings": {"rec": 1.0}, "settings": {"type": 2}},
    "pick_label": "1.03",
    "mode": "upside",
    "pool_scope": "rookies",
    "top_n": 3,
    "user_selected_player_id": "100",
    "sleeper_projections": {"100": {"rec": 5.0}},
    "sleeper_basis": dr.SLEEPER_BASIS_SEASON_SUM,
    "upside_rule": dr.UPSIDE_RULE_CROSSING,
}


class EveryInputIsInTheKeyTests(unittest.TestCase):

    def test_the_alternates_table_covers_the_signature_exactly(self):
        """The ratchet. Everything below is a loop over this table, so a parameter missing from
        it is a parameter silently untested -- the shape of the defect being repaired, rebuilt
        one layer up in the test that is supposed to catch it."""
        self.assertEqual(set(ALTERNATES), set(inspect.signature(ps.build_snapshot).parameters))

    def test_changing_any_single_input_changes_the_key(self):
        """The property, stated over the signature rather than over a list of dimensions."""
        base = ps.snapshot_input_key(**_base_inputs())
        unmoved = []
        for name, alternate in ALTERNATES.items():
            moved = ps.snapshot_input_key(**{**_base_inputs(), name: alternate})
            if moved == base:
                unmoved.append(name)
        self.assertEqual(unmoved, [],
                         "these inputs can change the snapshot and cannot change its key, so a "
                         "cache holding that key serves the wrong board")

    def test_no_two_inputs_are_interchangeable(self):
        """Distinctness, not just movement: fifteen different worlds must have fifteen keys, not
        one bucket that every change lands in."""
        keys = {name: ps.snapshot_input_key(**{**_base_inputs(), name: alternate})
                for name, alternate in ALTERNATES.items()}
        self.assertEqual(len(set(keys.values())), len(keys),
                         f"two single-input changes produced one key: {keys}")

    def test_renaming_an_input_changes_the_key(self):
        """What the part NAMES are actually for, which is not collision resistance.

        An earlier version of this file claimed the test above covered unnamed parts. It does
        not, and stripping the names survived the whole suite: the parts are emitted in
        signature order and NUL-separated, so two worlds of the same shape cannot collide by
        losing their names. What names buy is the case the value strings cannot see -- a
        parameter RENAMED while its value stays put. Without names that is the same key for a
        different call, which is silent identity reuse across a rename; snapshot_identity's own
        docstring makes exactly this argument about dataclass fields, and the reasoning does
        not change because these are parameters.

        Measured by substituting a stand-in whose signature carries the rename, since
        snapshot_input_key reads the signature at call time.
        """
        def renamed(merger, players_db, picks, pick_order, current_index, my_roster_id, league,
                    *, pick_label, scoring_mode="balanced", pool_scope="all", top_n=8,
                    user_selected_player_id=None, sleeper_projections=None,
                    sleeper_basis=dr.SLEEPER_BASIS_WEEKLY,
                    upside_rule=dr.UPSIDE_RULE_ROUND):
            raise AssertionError("signature only -- never called")

        inputs = _base_inputs()
        before = ps.snapshot_input_key(**inputs)
        renamed_inputs = {("scoring_mode" if k == "mode" else k): v for k, v in inputs.items()}
        with mock.patch.object(ps, "build_snapshot", renamed):
            after = ps.snapshot_input_key(**renamed_inputs)
        self.assertNotEqual(before, after,
                            "`mode` renamed to `scoring_mode`, every value unchanged -- a key "
                            "that cannot see the rename hands the new call the old call's "
                            "cached board")

    def test_the_same_world_keys_the_same_way_twice(self):
        """Or the cache never hits and the 870 ms it exists to save is paid every rerun."""
        self.assertEqual(ps.snapshot_input_key(**_base_inputs()),
                         ps.snapshot_input_key(**_base_inputs()))

    def test_a_fresh_but_equal_merger_keys_the_same_way(self):
        """CONTENT, not identity. Streamlit rebuilds objects across reruns, so a key that
        depended on object identity -- which is what repr() of a plain object gives, a memory
        address -- would miss on every rerun while claiming to be a content key."""
        self.assertEqual(ps.snapshot_input_key(**{**_base_inputs(), "merger": _FakeMerger(0)}),
                         ps.snapshot_input_key(**_base_inputs()))

    def test_defaults_are_in_the_key_so_an_omitted_argument_cannot_collide(self):
        """A default is still an input. A caller that stops passing `mode` must not key the same
        as one that passes something other than the default."""
        without = dict(_base_inputs())
        del without["mode"]
        self.assertEqual(ps.snapshot_input_key(**without),
                         ps.snapshot_input_key(**{**_base_inputs(), "mode": "balanced"}))
        self.assertNotEqual(ps.snapshot_input_key(**without),
                            ps.snapshot_input_key(**{**_base_inputs(), "mode": "upside"}))


class TheKeyRefusesWhatItCannotDescribeTests(unittest.TestCase):

    def test_an_incomplete_call_has_no_key(self):
        """You cannot name a world you could not build. `bind` raises rather than hashing a
        partial call, which would otherwise key every incomplete caller identically."""
        with self.assertRaises(TypeError) as caught:
            ps.snapshot_input_key(merger=_FakeMerger(), players_db={})
        self.assertIn("missing a required argument", str(caught.exception))

    def test_a_value_with_no_content_rendering_is_refused_not_repred(self):
        """repr() of a plain object is a MEMORY ADDRESS: stable inside one process while the
        object's contents change, which is a key that goes on matching across a real change.
        The fallback meant to be harmless is the one that would rebuild this whole defect."""
        class Opaque:
            pass
        with self.assertRaises(TypeError) as caught:
            ps.snapshot_input_key(**{**_base_inputs(), "league": Opaque()})
        self.assertIn("league", str(caught.exception))

    def test_the_refusal_reaches_inside_a_container(self):
        """A dict of DataFrames satisfies isinstance(value, dict) at the top and then hits the
        fallback one layer down, so the check has to recurse or it guards only the surface."""
        with self.assertRaises(TypeError) as caught:
            ps.snapshot_input_key(**{**_base_inputs(),
                                     "league": {"frames": {"x": pd.DataFrame({"a": [1]})}}})
        message = str(caught.exception)
        self.assertIn("league['frames']['x']", message,
                      "the refusal must say WHERE, or a caller cannot act on it")
        self.assertIn("DataFrame", message)

    def test_a_nested_container_of_plain_values_is_still_accepted(self):
        """The non-vacuity arm: the recursion must refuse a bad leaf, not every nested shape.
        A league dict is nested two deep in normal use, and a check that refused it would look
        exactly like a working guard while disabling the cache entirely."""
        key = ps.snapshot_input_key(**{**_base_inputs(),
                                       "league": {"a": {"b": [1, 2, {"c": "d"}]}}})
        self.assertEqual(len(key), 12)


class TwoWorldsTheOldKeyCouldNotTellApartTests(unittest.TestCase):
    """The measurement that made this a repair rather than a tidy-up, on the real rulebook.

    Both worlds below key IDENTICALLY under the six-tuple the Draft Room used, and both produce
    a materially different board. Slow (two real board builds per case), and deliberately kept
    separate from the unit tests above so the derivation is checkable in under a second.
    """

    @classmethod
    def setUpClass(cls):
        import data_merger as dm, draft_battery as dbat, run_draft_battery as rdb
        cls.merger = dm.DataMerger()
        cls.players_db, _ = rdb.build_players_db_from_capture()
        cls.season = rdb.season_projections_from_capture()
        scoring = rdb.scoring_settings_from_capture()
        cls.league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr",
                                          te_premium=False, dynasty=True, base_scoring=scoring)
        cls.merger.set_league_format(dbat.league_format_hint(cls.league))
        teams = 12
        cls.pick_order = [(i % teams) + 1 if (i // teams) % 2 == 0 else teams - (i % teams)
                          for i in range(teams * 16)]
        board = dr.compute_draft_board(cls.merger, cls.players_db, [], my_roster_id=None,
                                       league=cls.league, mode="balanced")
        cls.ids = [r["player_id"] for r in board[:60]]
        cls.picks = [{"player_id": pid, "roster_id": cls.pick_order[i], "pick_no": i + 1}
                     for i, pid in enumerate(cls.ids[:24])]
        cls.target = 24

    def _inputs(self, picks, projections):
        return dict(
            merger=self.merger, players_db=self.players_db, picks=picks,
            pick_order=self.pick_order, current_index=self.target,
            my_roster_id=str(self.pick_order[self.target]), league=self.league,
            pick_label="3.01", pool_scope="all", sleeper_projections=projections,
            sleeper_basis=(dr.SLEEPER_BASIS_SEASON_SUM if projections
                           else dr.SLEEPER_BASIS_WEEKLY))

    @staticmethod
    def _old_key(picks, merger, target, me):
        """The key this repair replaced, verbatim in shape, so the collision is demonstrated
        rather than asserted from the finding log."""
        return ("draft1", target, me, "all", len(picks), merger.freshest_date)

    def _leaders(self, inputs):
        snap = ps.build_snapshot(**inputs)
        return [(c.name, None if c.universal_value is None else round(c.universal_value, 2))
                for c in snap.candidates[:5]]

    def test_a_mid_draft_sync_is_a_different_world(self):
        me = str(self.pick_order[self.target])
        self.assertEqual(self._old_key(self.picks, self.merger, self.target, me),
                         self._old_key(self.picks, self.merger, self.target, me),
                         "the old key cannot see season_projections at all")
        without = self._inputs(self.picks, None)
        with_proj = self._inputs(self.picks, self.season)
        self.assertNotEqual(self._leaders(without), self._leaders(with_proj),
                            "if these agreed the finding would be moot -- re-derive")
        self.assertNotEqual(ps.snapshot_input_key(**without),
                            ps.snapshot_input_key(**with_proj))

    def test_a_re_pick_at_a_constant_count_is_a_different_world(self):
        me = str(self.pick_order[self.target])
        altered = list(self.picks)
        altered[-1] = {**altered[-1], "player_id": self.ids[40]}
        self.assertEqual(len(altered), len(self.picks), "the premise: the COUNT does not move")
        self.assertEqual(self._old_key(self.picks, self.merger, self.target, me),
                         self._old_key(altered, self.merger, self.target, me),
                         "which is why the old key served one board for both")
        original = self._inputs(self.picks, self.season)
        repicked = self._inputs(altered, self.season)
        self.assertNotEqual(self._leaders(original), self._leaders(repicked),
                            "if these agreed the finding would be moot -- re-derive")
        self.assertNotEqual(ps.snapshot_input_key(**original),
                            ps.snapshot_input_key(**repicked))


if __name__ == "__main__":
    unittest.main()
