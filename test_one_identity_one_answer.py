"""#214/F5 and #207: one resolution per player, and a premium that says when it wasn't measured.

F5 -- TWO MERGE PATHS. The pool resolved a player with `_merge_across_eligibility` (every
position he can be started at, NO_NFL_TEAM when Sleeper reports no club); `_team_roster_players`
called `merge_player` directly (primary bucket only, team=None). Measured on the capture, 3 of
181 dual-eligible players diverged on whether they can be priced AT ALL:

    Travis Hunter   DB/WR   pool prices him, the roster did NOT
    B.J. Daniels    QB/WR   the roster priced him, the pool does not
    Bryson Young    DL/LB   the roster priced him, the pool does not

Hunter is the user-visible one: once DRAFTED he vanished from his own roster's
eligibility_bonus and depth_exposure, so the lineup solved against a team one player emptier
than it really was. #172 repaired the pool side and stopped there.

The two who move the other way LOSE their roster price, and that is the point: a player the pool
will not price is one this engine has decided it cannot identify, and the roster does not get a
second, looser opinion about who he is.

#207 -- rival_premium held 0.0 where denial_value had already been made None by #187, in the
SAME LOOP. It matters more here because rival_premium FEEDS pick_necessity.
"""

from __future__ import annotations

import inspect
import unittest

import draft_room as dr
import draft_strategy as ds
import pick_synthesis as ps


class OneResolutionPerPlayerTests(unittest.TestCase):

    def test_the_roster_path_uses_the_same_resolver_as_the_pool(self):
        src = inspect.getsource(dr._team_roster_players)
        self.assertIn("_merge_across_eligibility", src,
                      "the roster and the pool must agree about who a player IS")
        self.assertNotIn("merger.merge_player(", src,
                         "a direct call here is the second, looser opinion this removes")

    def test_the_roster_path_reports_no_club_the_way_the_pool_does(self):
        """Asserted on the CALL, via AST, not by scanning the source text.

        The first version of this test did `assertIn("NO_NFL_TEAM", src)` and SURVIVED a
        mutation that removed the fallback from the code -- because the explanatory comment
        three lines above the call contains the phrase. A test that can be satisfied by its
        own subject's prose is testing the prose.
        """
        import ast
        tree = ast.parse(inspect.getsource(dr._team_roster_players).lstrip())
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call)
                 and getattr(n.func, "id", None) == "_merge_across_eligibility"]
        self.assertEqual(len(calls), 1, "exactly one resolution per player")
        # (merger, name, eligible, primary, team) -- team is the FIFTH argument
        self.assertEqual(len(calls[0].args), 5)
        team_arg = calls[0].args[4]
        self.assertIsInstance(team_arg, ast.BoolOp,
                              "the team argument must be `info.get('team') or NO_NFL_TEAM`; "
                              "'on no roster' and 'unspecified' are different facts (#196)")
        names = {getattr(v, "id", None) for v in team_arg.values}
        self.assertIn("NO_NFL_TEAM", names,
                      "passing a bare None makes the roster lenient where the pool is strict")

    def test_a_dual_eligible_player_survives_on_his_own_roster(self):
        """Travis Hunter, the measured case, end to end."""
        import data_merger as dm
        import run_draft_battery as rdb
        merger = dm.DataMerger()
        players_db, _ = rdb.build_players_db_from_capture()
        merger.set_league_format({"scoring": "ppr", "te_premium": False})
        hunter = next((pid for pid, p in players_db.items()
                       if f"{p.get('first_name','')} {p.get('last_name','')}".strip()
                       == "Travis Hunter"), None)
        if hunter is None:
            self.skipTest("Travis Hunter is not in the committed capture")
        rows = dr._team_roster_players(
            [{"roster_id": "1", "player_id": hunter}], players_db, "1", merger)
        self.assertEqual(len(rows), 1,
                         "he is on the roster and occupies a slot; dropping him makes the "
                         "lineup solve against a team one player emptier than it is")
        self.assertEqual(rows[0]["eligible"], {"DB", "WR"},
                         "and he keeps both eligibilities, not just his primary")


class APremiumSaysWhenItWasNotMeasuredTests(unittest.TestCase):

    def test_rival_premium_starts_absent_not_at_zero(self):
        src = inspect.getsource(ds.pick_analysis)
        self.assertIn("rival_premium = None", src,
                      "0.0 asserts 'no rival wanted him more' off no evidence at all")

    def test_the_max_still_works_from_an_absent_start(self):
        src = inspect.getsource(ds.pick_analysis)
        self.assertIn("if rival_premium is None or premium > rival_premium:", src,
                      "starting at None must not stop the first real premium being taken")

    def test_it_travels_with_the_same_basis_vocabulary_denial_uses(self):
        src = inspect.getsource(ds.pick_analysis)
        self.assertIn('"rival_premium_basis": denial_basis', src,
                      "same question about the same rivals -- one vocabulary, one home (#126)")

    def test_the_companion_crosses_the_snapshot_boundary_and_is_required(self):
        fields = {f.name: f for f in __import__("dataclasses").fields(ps.CandidateSnapshot)}
        self.assertIn("rival_premium_basis", fields)
        import dataclasses
        self.assertIs(fields["rival_premium_basis"].default, dataclasses.MISSING,
                      "a defaulted companion is one a new call site can forget to set")

    def test_necessity_treats_an_absent_premium_as_no_contribution_not_as_a_measured_zero(self):
        src = inspect.getsource(ps.pick_necessity_for_candidates
                               if hasattr(ps, "pick_necessity_for_candidates")
                               else ps.build_snapshot)
        self.assertNotIn('c.get("rival_premium") or 0.0', src,
                         "the bare `or 0.0` idiom launders absence into a measured zero")


class TheDeferralIsDischargedNotSweptAlongTests(unittest.TestCase):
    """#207 was deferred once, on the record, because it "would move real necessity scores".

    It does not. This pins the equivalence rather than restating the reasoning."""

    def test_an_absent_premium_contributes_exactly_what_a_zero_did(self):
        import inspect
        src = inspect.getsource(ps.compute_pick_necessity)
        self.assertIn("measured_premium if measured_premium is not None else 0.0", src,
                      "absent must map to a zero CONTRIBUTION -- identical arithmetic to the "
                      "`or 0.0` it replaced, so no necessity score moves")

    def test_a_real_premium_is_untouched_by_the_change(self):
        import inspect
        src = inspect.getsource(ps.compute_pick_necessity)
        self.assertNotIn("rival_premium = 0.0", src,
                         "only the ABSENT case is mapped; a measured premium passes through")


if __name__ == "__main__":
    unittest.main()
