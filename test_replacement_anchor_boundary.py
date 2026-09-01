"""The pre-draft replacement anchor's own boundary -- what the board may and may not do once
a position's league-wide starter demand is exhausted.

The defect these pin down. replacement_levels is defined only while a position still has a
whole starting slot unfilled and correctly OMITS the position below that. compute_draft_board
turned that omission into final_score=None, and _board_order sorts unpriced rows last -- so a
position whose starters were all filled had EVERY remaining player fall below every priced
row. Kickers and defenses are drafted last and are therefore the last positions still carrying
demand, which made the inversion structural rather than incidental: measured on a 12-team 1QB
board at round 15, K and DEF were 100% priced (37/37 and 32/32) while QB/RB/TE/WR were 100%
unpriced (0 of 15/36/24/9), and the top five candidates were four defenses and a kicker ahead
of every remaining skill player.

Every test here is about SEMANTICS. Each one fails for a reason that can be stated in one
sentence about what the number means, and each one is written so that it CAN fail: the
control arms below are asserted to actually differ before any comparison is trusted.
"""

import unittest

import pandas as pd

import data_merger as dm
import draft_room as dr

NUM_TEAMS = 12
ROSTER_POSITIONS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"] + ["BN"] * 11
SUPERFLEX_POSITIONS = (
    ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "SUPER_FLEX", "K", "DEF"] + ["BN"] * 10
)
LEAGUE = {
    "roster_positions": ROSTER_POSITIONS, "total_rosters": NUM_TEAMS,
    "settings": {"type": 2}, "scoring_settings": {},
}
SKILL = ("QB", "RB", "WR", "TE")


IDP_LEAGUE = {
    "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "IDP_FLEX"]
                        + ["BN"] * 8,
    "total_rosters": NUM_TEAMS, "settings": {"type": 2}, "scoring_settings": {},
}


def _universe(merger, extra_positions=()):
    """A players_db over the merger's whole projection set, ordered by trade_value so a
    synthetic draft consumes the best players first the way a real one does."""
    players_db, by_position, next_id = {}, {}, 0
    for position in ("QB", "RB", "WR", "TE", "K", "DEF") + tuple(extra_positions):
        rows = merger.projections[merger.projections["position"] == position]
        if rows.empty:
            continue
        for _, row in rows.sort_values("trade_value", ascending=False).iterrows():
            next_id += 1
            parts = str(row["name"]).split()
            players_db[str(next_id)] = {
                "first_name": parts[0] if parts else "",
                "last_name": " ".join(parts[1:]) or (parts[0] if parts else ""),
                "position": position, "fantasy_positions": [position], "team": row.get("team"),
            }
            by_position.setdefault(position, []).append(str(next_id))
    return players_db, by_position


def _drain(by_position, rounds_by_position, num_teams=NUM_TEAMS):
    """Every team takes the requested count at each position -- enough to run a position's
    league-wide starter demand to zero, which is the state this whole module is about."""
    picks, taken = [], {}
    for position, count in rounds_by_position.items():
        for _ in range(count):
            index = taken.get(position, 0)
            for roster_id in range(1, num_teams + 1):
                if index >= len(by_position[position]):
                    break
                picks.append({
                    "player_id": by_position[position][index], "roster_id": str(roster_id),
                    "round": len(picks) // num_teams + 1, "pick_no": len(picks) + 1,
                })
                index += 1
            taken[position] = index
    return picks


class PreDraftAnchorEquivalence(unittest.TestCase):
    """The design rests on one measured equality: the last LIVE level equals the PRE-DRAFT
    level. That is what lets the anchor be a pure function of (player universe, league)
    instead of a memo of earlier calls -- a memo would have made a board's answer depend on
    which boards were built before it, breaking replacement_levels' own stated contract that
    nothing is cached across picks."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db, cls.by_position = _universe(cls.merger)

    def test_anchor_matches_the_first_live_level_for_every_position(self):
        seen = {}
        original = dr.replacement_levels

        def spy(pool, value_col, roster_positions, num_teams, remaining_demand=None,
                startable_floors=None):
            levels = original(pool, value_col, roster_positions, num_teams, remaining_demand,
                              startable_floors)
            for position, level in levels.items():
                seen.setdefault((value_col, position), level)
            return levels

        dr.replacement_levels = spy
        try:
            dr.compute_draft_board(self.merger, self.players_db, [], my_roster_id="1",
                                   league=LEAGUE, mode="balanced")
        finally:
            dr.replacement_levels = original

        self.assertTrue(seen, "vacuous: no replacement level was observed at all")
        anchor = dr.predraft_replacement_anchor(
            self.merger, self.players_db, dr.league_usable_positions(ROSTER_POSITIONS),
            ROSTER_POSITIONS, NUM_TEAMS, "_points",
        )
        self.assertTrue(anchor, "vacuous: the anchor produced no levels to compare against")
        compared = 0
        for (value_col, position), live in seen.items():
            if value_col != "_points":
                continue
            self.assertIn(position, anchor)
            self.assertAlmostEqual(anchor[position], live, places=9)
            compared += 1
        self.assertGreaterEqual(compared, 4, "vacuous: too few positions actually compared")

    def test_board_is_identical_when_built_twice_in_a_row(self):
        """No call-order state anywhere in the anchor path."""
        picks = _drain(self.by_position, {"WR": 4, "RB": 3, "TE": 2, "QB": 2})
        first = dr.compute_draft_board(self.merger, self.players_db, picks, my_roster_id="1",
                                       league=LEAGUE, mode="balanced")
        second = dr.compute_draft_board(self.merger, self.players_db, picks, my_roster_id="1",
                                        league=LEAGUE, mode="balanced")
        self.assertTrue(first, "vacuous: empty board")
        self.assertEqual([r["player_id"] for r in first], [r["player_id"] for r in second])
        self.assertEqual([r["final_score"] for r in first], [r["final_score"] for r in second])


class ExhaustedDemandKeepsItsPrice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db, cls.by_position = _universe(cls.merger)
        # Deep enough that several positions' league-wide starter demand reaches zero.
        cls.picks = _drain(cls.by_position, {"WR": 5, "RB": 4, "TE": 3, "QB": 2})
        cls.board = dr.compute_draft_board(
            cls.merger, cls.players_db, cls.picks, my_roster_id="1", league=LEAGUE,
            mode="balanced",
        )

    def _control_board(self):
        """The same board with the anchor disabled -- i.e. the behaviour before this repair.
        Used as a control, and asserted to actually differ so nothing here passes vacuously."""
        original = dr.predraft_replacement_anchor
        dr.predraft_replacement_anchor = lambda *a, **k: {}
        try:
            return dr.compute_draft_board(
                self.merger, self.players_db, self.picks, my_roster_id="1", league=LEAGUE,
                mode="balanced",
            )
        finally:
            dr.predraft_replacement_anchor = original

    def test_the_control_really_does_lose_prices(self):
        """Guards every comparison below: if the control priced everything too, the repair
        would be untested and the rest of this class would prove nothing."""
        control = {r["player_id"]: r["final_score"] for r in self._control_board()}
        unpriced = [pid for pid, score in control.items() if score is None]
        self.assertGreater(len(unpriced), 0,
                           "vacuous: nothing was unpriced without the anchor, so this draft "
                           "state does not exercise the defect at all")

    def test_anchor_only_adds_prices_and_never_changes_one(self):
        control = {r["player_id"]: r["final_score"] for r in self._control_board()}
        after = {r["player_id"]: r["final_score"] for r in self.board}
        for player_id, before in control.items():
            if before is None:
                continue
            self.assertIsNotNone(after.get(player_id),
                                 f"{player_id} lost a price it already had")
            self.assertAlmostEqual(after[player_id], before, places=9,
                                   msg=f"{player_id}'s existing price changed")

    def test_every_row_records_which_anchor_its_price_rests_on(self):
        self.assertTrue(self.board)
        bases = {r.get("replacement_basis") for r in self.board}
        self.assertTrue(bases <= {"live_starter_demand", "predraft_anchor"}, bases)
        self.assertIn("predraft_anchor", bases,
                      "vacuous: no row in this state rests on the pre-draft anchor")

    def test_a_skill_position_is_no_longer_wholly_unpriced(self):
        by_position = {}
        for row in self.board:
            priced, unpriced = by_position.setdefault(row["position"], [0, 0])
            by_position[row["position"]] = (
                [priced + 1, unpriced] if row["final_score"] is not None
                else [priced, unpriced + 1]
            )
        exercised = 0
        for position in SKILL:
            if position not in by_position:
                continue
            priced, _ = by_position[position]
            self.assertGreater(priced, 0,
                               f"every remaining {position} is unpriced, so all of them sort "
                               f"below every kicker -- the inversion this repair exists for")
            exercised += 1
        self.assertGreaterEqual(exercised, 3, "vacuous: too few skill positions on the board")


class StartableFloorIsNeverRevived(unittest.TestCase):
    """The startable_floors branch declines for a DIFFERENT reason -- no remaining player
    clears the startability threshold -- and a stale anchor must not be used to assert that a
    startable replacement exists where the measurement says none does. Kept separate from the
    demand case on purpose; see #66 for the two-clamp history."""

    def test_fill_skips_a_position_the_floor_branch_declined(self):
        levels = {"RB": 100.0}
        filled = dr._fill_omitted_from_anchor(
            levels, {"RB", "QB"}, {"QB": 250.0}, lambda: {"QB": 999.0, "RB": 111.0},
        )
        self.assertEqual(filled, set(), "a floor-declined position was revived")
        self.assertNotIn("QB", levels)

    def test_fill_takes_a_position_whose_demand_merely_ran_out(self):
        levels = {"RB": 100.0}
        filled = dr._fill_omitted_from_anchor(levels, {"RB", "QB"}, None, lambda: {"QB": 42.0})
        self.assertEqual(filled, {"QB"})
        self.assertEqual(levels["QB"], 42.0)

    def test_fill_cannot_invent_a_level_the_anchor_does_not_have(self):
        levels = {}
        filled = dr._fill_omitted_from_anchor(levels, {"RB"}, None, dict)
        self.assertEqual(filled, set())
        self.assertEqual(levels, {})

    def test_fill_does_not_call_the_builder_when_nothing_is_missing(self):
        """The unit-level half of the laziness property -- the callable signature exists for
        exactly this, and passing a built dict is what made it eager for one commit."""
        calls = []

        def build():
            calls.append(1)
            return {"RB": 1.0}

        filled = dr._fill_omitted_from_anchor({"RB": 100.0}, {"RB"}, None, build)
        self.assertEqual(filled, set())
        self.assertEqual(calls, [], "the anchor was built despite nothing needing it")

    def test_fill_never_overwrites_a_live_level(self):
        levels = {"RB": 100.0}
        dr._fill_omitted_from_anchor(levels, {"RB"}, None, lambda: {"RB": 999.0})
        self.assertEqual(levels["RB"], 100.0)

class TradeValueBranchIsAnchoredToo(unittest.TestCase):
    """The `~has_proj` branch -- and measurement says that branch IS the IDP path.

    compute_draft_board splits the pool: rows carrying a points projection are valued against a
    points replacement level, and rows without one fall back to a trade_value level. The anchor
    is wired identically on both, but every synthetic universe used to develop it was built
    from the projection set, so every row took the points path and only `_points` was ever
    observed as a value_col. This class closes that gap.

    It matters more than "an untested branch" suggests. Of the 764 rows in the real projection
    set, 76 carry a trade_value with no projection, and all 76 are IDP (LB 29, DL 24, DB 23).
    IDP starter demand is also tiny -- one IDP_FLEX slot splits to 0.333 per team, about 4
    league-wide -- so it exhausts around round 11 of 18, far earlier than any offensive
    position. The anchor is therefore MORE load-bearing for IDP than for offense, in the one
    branch that had no tests at all.
    """

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db, by_position = _universe(cls.merger, ("LB", "DL", "DB"))
        # Drained past the round where IDP demand runs out (measured: anchoring starts at 11).
        cls.picks = _drain(by_position, {"WR": 3, "RB": 3, "TE": 2, "QB": 2,
                                         "LB": 2, "DL": 2, "DB": 2})
        cls.board = dr.compute_draft_board(
            cls.merger, cls.players_db, cls.picks, my_roster_id="1", league=IDP_LEAGUE,
            mode="balanced")

    def _control_board(self):
        original = dr.predraft_replacement_anchor
        dr.predraft_replacement_anchor = lambda *a, **k: {}
        try:
            return dr.compute_draft_board(
                self.merger, self.players_db, self.picks, my_roster_id="1", league=IDP_LEAGUE,
                mode="balanced")
        finally:
            dr.predraft_replacement_anchor = original

    def test_the_fixture_actually_reaches_the_trade_value_branch(self):
        """Guards everything below. If no row takes the ~has_proj path this class is testing
        the points branch a second time under an IDP-shaped name."""
        on_the_branch = [r for r in self.board
                         if r.get("bpa_source") == "position_relative_trade_value_vor"]
        self.assertGreater(len(on_the_branch), 0,
                           "no row reached the trade_value branch -- fixture proves nothing")
        self.assertTrue(all(r["position"] in ("LB", "DL", "DB") for r in on_the_branch),
                        "the trade_value branch is expected to be the IDP path")

    def test_the_control_really_does_lose_idp_prices(self):
        """And guards the comparison: without the anchor, IDP must actually go unpriced here,
        or the branch is not exercised at the state this fixture builds."""
        control = self._control_board()
        lost = [r for r in control
                if r["position"] in ("LB", "DL", "DB") and r["final_score"] is None]
        self.assertGreater(len(lost), 0,
                           "IDP stays priced without the anchor, so this state does not "
                           "exercise the demand-exhausted case on the trade_value branch")

    def test_idp_keeps_its_price_once_league_demand_is_exhausted(self):
        idp = [r for r in self.board if r["position"] in ("LB", "DL", "DB")]
        self.assertGreater(len(idp), 0, "no IDP rows on the board at all")
        unpriced = [r for r in idp if r["final_score"] is None]
        self.assertEqual(unpriced, [], "IDP rows fell off the board despite the anchor")
        anchored = [r for r in idp if r.get("replacement_basis") == "predraft_anchor"]
        self.assertGreater(len(anchored), 0,
                           "no IDP row rests on the pre-draft anchor, so demand has not "
                           "actually run out at this draft state")

    def test_the_anchor_adds_idp_prices_without_changing_any_other(self):
        control = {r["player_id"]: r["final_score"] for r in self._control_board()}
        after = {r["player_id"]: r["final_score"] for r in self.board}
        for player_id, before in control.items():
            if before is None:
                continue
            self.assertIsNotNone(after.get(player_id), f"{player_id} lost a price it had")
            self.assertAlmostEqual(after[player_id], before, places=9,
                                   msg=f"{player_id}'s existing price changed")

class TheAnchorCacheKeyIsComplete(unittest.TestCase):
    """The cache is only as safe as its key.

    predraft_replacement_anchor is a pure function of (player universe, league settings), so
    caching it by CONTENT is legitimate in a way the rejected memo was not -- that one returned
    the first level a position was seen with, making its answer depend on which boards were
    built before it. This one returns the same value for the same inputs and nothing else.

    The failure mode that remains is a key that MISSES an input: it would serve a stale anchor
    after the underlying data changed and silently mis-price every row at that position -- an
    absence-shaped defect wearing a number. So each test below changes exactly one input and
    asserts the key moves. A key that ignored that input would fail here rather than in a
    draft six weeks from now.
    """

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db, _ = _universe(cls.merger)
        cls.usable = dr.league_usable_positions(ROSTER_POSITIONS)

    def _key(self, **overrides):
        args = dict(
            merger=self.merger, players_db=self.players_db, usable_positions=self.usable,
            roster_positions=ROSTER_POSITIONS, num_teams=NUM_TEAMS, value_col="_points",
            sleeper_projections=None, scoring_settings=None, pool_scope="all",
            startable_floors=None,
        )
        args.update(overrides)
        return dr.anchor_cache_key(**args)

    def test_the_same_inputs_give_the_same_key(self):
        # Guards every assertion below: if the key were unstable, they would all "pass".
        self.assertEqual(self._key(), self._key())

    def test_a_changed_roster_template_changes_the_key(self):
        other = ROSTER_POSITIONS + ["BN"]
        self.assertNotEqual(self._key(), self._key(roster_positions=other))

    def test_a_changed_team_count_changes_the_key(self):
        self.assertNotEqual(self._key(), self._key(num_teams=NUM_TEAMS + 1))

    def test_a_changed_value_col_changes_the_key(self):
        self.assertNotEqual(self._key(), self._key(value_col="trade_value"))

    def test_a_changed_pool_scope_changes_the_key(self):
        self.assertNotEqual(self._key(), self._key(pool_scope="rookies"))

    def test_changed_scoring_settings_change_the_key(self):
        self.assertNotEqual(self._key(), self._key(scoring_settings={"rec": 1.0}))

    def test_a_changed_startable_floor_changes_the_key(self):
        self.assertNotEqual(self._key(), self._key(startable_floors={"QB": 250.0}))

    def test_changed_usable_positions_change_the_key(self):
        self.assertNotEqual(self._key(), self._key(usable_positions=set(self.usable) | {"LB"}))

    def test_a_changed_players_db_changes_the_key(self):
        # A player's POSITION moving is the case that matters: same ids, same count, different
        # pool composition. A key over ids alone would miss it entirely.
        moved = {pid: dict(info) for pid, info in self.players_db.items()}
        victim = sorted(moved)[0]
        moved[victim]["position"] = "TE" if moved[victim]["position"] != "TE" else "WR"
        self.assertNotEqual(self._key(), self._key(players_db=moved))

    def test_changed_merger_data_changes_the_key(self):
        """The one a projections-only key would have missed: merge_player resolves against
        trade_values and external_values too."""
        import copy
        for frame_name in ("projections", "trade_values", "external_values"):
            with self.subTest(frame=frame_name):
                clone = copy.copy(self.merger)
                frame = getattr(self.merger, frame_name).copy()
                if frame.empty:
                    self.skipTest(f"{frame_name} is empty in this baseline")
                column = frame.columns[0]
                frame.iloc[0, frame.columns.get_loc(column)] = "MUTATED-FOR-TEST"
                setattr(clone, frame_name, frame)
                self.assertNotEqual(self._key(), self._key(merger=clone),
                                    f"a change to {frame_name} left the key unmoved")


class TheAnchorCacheIsSafeToReuse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db, _ = _universe(cls.merger)
        cls.usable = dr.league_usable_positions(ROSTER_POSITIONS)

    def _anchor(self):
        return dr.predraft_replacement_anchor(
            self.merger, self.players_db, self.usable, ROSTER_POSITIONS, NUM_TEAMS, "_points")

    def test_a_cached_answer_equals_a_freshly_built_one(self):
        dr._ANCHOR_CACHE.clear()
        first = self._anchor()
        self.assertTrue(first, "vacuous: the anchor produced no levels")
        self.assertEqual(self._anchor(), first)

    def test_the_caller_cannot_poison_the_cache_by_mutating_what_it_got(self):
        # _fill_omitted_from_anchor writes into the dict it is handed, so a shared reference
        # would let one board's fill leak into the next board's anchor.
        dr._ANCHOR_CACHE.clear()
        first = self._anchor()
        first["QB"] = -999.0
        self.assertNotEqual(self._anchor().get("QB"), -999.0)


    def test_no_anchor_is_built_when_no_position_needs_one(self):
        """The laziness the code claims, pinned as behaviour.

        This was a real defect for one commit: _fill_omitted_from_anchor took the built anchor
        as an ARGUMENT, so Python evaluated it eagerly on every board build and the "only if
        some position actually needs it" in its own comment was false. A comment asserting
        something the code does not do is the failure this repository's doctrine is named for,
        so the property gets a test rather than a promise.
        """
        merger = dm.DataMerger()
        players_db, by_position = _universe(merger)
        opening = dr.compute_draft_board(merger, players_db, [], my_roster_id="1",
                                         league=LEAGUE, mode="balanced")
        self.assertTrue(opening, "vacuous: the opening board is empty")
        # Early enough that every position still has unfilled starting slots league-wide.
        picks = [{"player_id": row["player_id"], "roster_id": str((i % NUM_TEAMS) + 1),
                  "round": (i // NUM_TEAMS) + 1, "pick_no": i + 1}
                 for i, row in enumerate(opening[:4 * NUM_TEAMS])]
        dr._ANCHOR_CACHE.clear()
        board = dr.compute_draft_board(merger, players_db, picks, my_roster_id="1",
                                       league=LEAGUE, mode="balanced")
        self.assertTrue(board, "vacuous: the early board is empty")
        self.assertEqual(
            [r for r in board if r.get("replacement_basis") == "predraft_anchor"], [],
            "a position was anchored this early, so this state does not test laziness")
        self.assertEqual(len(dr._ANCHOR_CACHE), 0,
                         "the anchor was built even though no position needed one")

    def test_the_cache_is_bounded(self):
        dr._ANCHOR_CACHE.clear()
        for extra in range(dr.ANCHOR_CACHE_ENTRIES + 3):
            dr.predraft_replacement_anchor(
                self.merger, self.players_db, self.usable,
                ROSTER_POSITIONS + ["BN"] * extra, NUM_TEAMS, "_points")
        self.assertLessEqual(len(dr._ANCHOR_CACHE), dr.ANCHOR_CACHE_ENTRIES)



if __name__ == "__main__":
    unittest.main()
