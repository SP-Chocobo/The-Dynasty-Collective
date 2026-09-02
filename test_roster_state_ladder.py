"""B(#45/#69/#72) -- the roster-state ladder that already exists.

The hypothesis put to this investigation was that roster-state information (starting coverage,
positional depth, saturation, bench capacity, draft stage, flexibility) might be a MISSING
contextual layer in the decision path. The instruction attached to it was the right one: find
out whether the architecture already represents these things before adding anything, and do not
duplicate an existing concept merely because it is not obvious from the final ranking.

It does represent them, and the representation reaches the decision layer. `need_bonus` is
already a monotone ladder keyed to how much of a position's reachable starting coverage the
roster has filled, derived from the league's own roster_positions rather than invented:

    position   reachable slots   need_bonus by players rostered
    QB         1                 0:4.00  1:0.00  2:0.00  3:0.00
    RB         3                 0:8.33  1:4.33  2:0.33  3:0.00  4:0.00  5:0.00
    WR         3                 0:8.33  1:4.33  2:0.33  3:0.00  4:0.00  5:0.00
    TE         2                 0:4.33  1:0.33  2:0.00  3:0.00  4:0.00

Measured across 288 same-slot-count position pairs on real boards: ZERO monotonicity
violations. And in the tie groups where a contextual tiebreak would engage, need_bonus already
favoured the least-covered candidate in 19 of 19 groups with differing coverage, changed the
winner outright in 6 of 52, and fell short in 10 of 52 -- neither inert nor dominant.

WHAT THIS FILE PINS, and why it did not exist before: the ladder is load-bearing behaviour that
nothing asserted. A change to NEED_BONUS_PER_DEDICATED_SLOT, to the flex-share arithmetic, or to
how coverage is counted could invert the coverage/need relationship -- turning "you already have
three of these" into a REASON to draft a fourth -- and no test would have failed.

WHAT IT DELIBERATELY DOES NOT PIN: the SIZE of the ladder's steps. Whether 4.0 per dedicated
slot gives roster fit the right authority is a product decision, quantified in
CDME_CONTRACTS.md and not settled here.
"""
import collections
import unittest

import data_merger as dm
import draft_room as dr
import lineup_optimizer as lo


ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"] + ["BN"] * 11
NUM_TEAMS = 12
DYNASTY = {"roster_positions": ROSTER, "total_rosters": NUM_TEAMS,
           "settings": {"type": 2}, "scoring_settings": {}}
SKILL = ("QB", "RB", "WR", "TE")


class _Rosters(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        proj = cls.merger.projections
        cls.players_db = {}
        pid = 0
        for position in ("QB", "RB", "WR", "TE", "K", "DEF"):
            for _, row in proj[proj["position"] == position].sort_values(
                    "trade_value", ascending=False).iterrows():
                pid += 1
                parts = str(row["name"]).split()
                cls.players_db[str(pid)] = {
                    "first_name": parts[0] if parts else "",
                    "last_name": " ".join(parts[1:]) or (parts[0] if parts else ""),
                    "position": position, "fantasy_positions": [position],
                    "team": row.get("team"),
                }
        cls.opening = dr.compute_draft_board(cls.merger, cls.players_db, [], my_roster_id="1",
                                             league=DYNASTY, mode="balanced")
        slots = lo.slots_from_roster_positions(ROSTER)
        # "Reachable" slots, not dedicated ones: a WR can fill a WR slot or a FLEX, and the
        # coverage question is how many lineup places he could actually occupy.
        cls.reachable = {p: sum(1 for s in slots if p in s["eligible"]) for p in SKILL}

    def _roster_with(self, wanted):
        """A picks list giving roster "1" exactly `wanted` players at each named position,
        taken off the top of the real opening board so the players are real."""
        picks, taken = [], collections.Counter()
        for row in self.opening:
            position = row["position"]
            if taken[position] >= wanted.get(position, 0):
                continue
            taken[position] += 1
            picks.append({"player_id": row["player_id"], "roster_id": "1",
                          "round": len(picks) // NUM_TEAMS + 1, "pick_no": len(picks) + 1})
        return picks

    def _need_for(self, position, wanted):
        board = dr.compute_draft_board(self.merger, self.players_db, self._roster_with(wanted),
                                       my_roster_id="1", league=DYNASTY, mode="balanced")
        row = next((r for r in board if r["position"] == position
                    and r.get("final_score") is not None), None)
        self.assertIsNotNone(row, f"no priced {position} left to read a need_bonus from")
        return row["need_bonus"]


class TheLadderIsMonotoneInCoverageTests(_Rosters):
    """More of a position must never buy MORE need for it. This is the invariant that keeps
    "you already have three of these" from becoming a reason to draft a fourth."""

    def test_need_never_increases_as_the_position_fills(self):
        for position in SKILL:
            previous = None
            for held in range(0, self.reachable[position] + 3):
                need = self._need_for(position, {position: held})
                if previous is not None:
                    self.assertLessEqual(
                        need, previous + 1e-9,
                        f"{position}: holding {held} bought MORE need than holding {held - 1} "
                        f"({need} > {previous})")
                previous = need

    def test_an_empty_position_carries_strictly_more_need_than_a_covered_one(self):
        for position in SKILL:
            empty = self._need_for(position, {position: 0})
            covered = self._need_for(position, {position: self.reachable[position]})
            self.assertGreater(empty, covered,
                               f"{position}: an empty position and a covered one are worth the "
                               "same contextual bonus")


class CoverageZeroesTheLadderTests(_Rosters):
    """Once a position's reachable starting coverage is filled, roster fit contributes nothing
    further. This is the boundary between 'context helps decide' and 'context is silent'."""

    def test_a_fully_covered_position_earns_no_need_bonus(self):
        for position in SKILL:
            self.assertAlmostEqual(
                self._need_for(position, {position: self.reachable[position]}), 0.0, places=6,
                msg=f"{position} still earns roster-fit credit at full coverage")

    def test_saturation_beyond_coverage_is_the_same_state_as_covered(self):
        # RECORDED, NOT ENDORSED. need_bonus cannot distinguish "you have exactly enough" from
        # "you have twice as many as you can start" -- both are 0.0. Expressing the difference
        # would require a NEGATIVE contribution to team_acquisition_value, i.e. charging a
        # player for his position's depth, which would put roster state inside player value.
        # Whether the difference deserves to exist somewhere else (a tiebreak or presentation
        # signal, never the valuation) is an open product decision recorded in
        # CDME_CONTRACTS.md. This test pins the CURRENT state so that decision is made
        # deliberately rather than discovered later.
        for position in ("RB", "WR"):
            covered = self._need_for(position, {position: self.reachable[position]})
            saturated = self._need_for(position, {position: self.reachable[position] + 3})
            self.assertEqual(covered, saturated,
                             f"{position}: covered and saturated have become distinguishable -- "
                             "that is a real change in the contextual contract, revisit the "
                             "open decision in CDME_CONTRACTS.md")

    def test_the_ladder_is_never_negative(self):
        # Roster fit may raise a candidate; it may never charge him for his position's depth.
        # That is the player-property/context boundary this engine's doctrine is built on.
        for position in SKILL:
            for held in range(0, self.reachable[position] + 4):
                self.assertGreaterEqual(self._need_for(position, {position: held}), 0.0,
                                        f"{position} with {held} rostered earns a NEGATIVE "
                                        "need_bonus -- context is penalising player value")


class TheLadderComesFromLeagueStructureTests(_Rosters):
    """The step sizes are derived from the league's own roster_positions, not from a table of
    invented per-position numbers -- so a position with more reachable slots starts higher."""

    def test_a_position_with_more_reachable_slots_starts_higher(self):
        empty = {p: self._need_for(p, {p: 0}) for p in SKILL}
        for a in SKILL:
            for b in SKILL:
                if self.reachable[a] > self.reachable[b]:
                    self.assertGreaterEqual(
                        empty[a], empty[b],
                        f"{a} reaches {self.reachable[a]} slots and {b} reaches "
                        f"{self.reachable[b]}, but {a} starts lower on the ladder")

    def test_the_ladder_is_bounded_by_the_declared_cap(self):
        for position in SKILL:
            for held in range(0, self.reachable[position] + 2):
                self.assertLessEqual(self._need_for(position, {position: held}),
                                     dr.NEED_BONUS_MAX)


if __name__ == "__main__":
    unittest.main()
