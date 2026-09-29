"""D4 / D5 -- `#184`, `#126`, `#56`, task `#37`. The upside branch's two unfinished halves.

TWO READERS OF ONE INPUT PAIR, AT TWO RATES. `time_horizon_adj` and `upside_score`'s growth term
both read `_season_proj_pct` and `_proj3yr_pct` and convert the gap between them into points:

    time_horizon_adj    clamp((proj3yr_pct - season_pct) * TIME_HORIZON_SLOPE, +/-10)    0.20
    upside growth       clamp(max(0, gap)               * UPSIDE_GROWTH_WEIGHT, +/-10)   0.50

An earlier repair unified the BOUND and left the SLOPE, and its own comment shows it knew the
argument reached both: *"not invented here -- it is the rate this engine already applies to this
exact quantity."* It then kept 0.5. So one percentile pair had two conversion rates 2.5x apart --
`#126` with the clamp bolted on, and the half of `#184` that was still open.

THE REPAIR IS A DERIVATION, NOT A RETUNE (`#56`). No number is chosen here. Growth is converted at
the slope this engine already applies to this exact gap, and the second name for that rate is
DELETED rather than aliased, on Tier 4's precedent for `HORIZON_UNDRAFTED_SLOTS`: an alias lets two
spellings drift apart again, which is the defect rather than the cure.

WHY NOT D4(c), AND THIS IS A CORRECTION TO MY OWN WRITE-UP. The owner ruled (c) -- price growth at
zero, keep it as an observable -- on the strength of my claim that the term was never decisive,
measured at "5 of 672 picks above zero". That figure is real and it is about `mode="auto"`, which
enters upside scoring on 672 of the battery's 9336 picks and mostly on players carrying no 3yr
outlook at all. It is not about explicit upside mode. Measured there, over three league shapes and
rounds 10-22:

    rows carrying growth > 0                 1737 of 4584   37.9%
    boards whose TOP-1 PICK growth changes      5 of 39      12.8%
    boards whose winner carries growth > 0      6 of 39      15.4%   (the upper bound, and it holds)

So (c) would have removed working behaviour on a measurement about a different population. Adopting
the slope moves the top-1 pick on 2 of those 39 boards: the conversion becomes derived and the term
keeps the work it demonstrably does. My earlier "0 of 7" was a sampling artifact -- even rounds only,
one league shape -- and `POST_AUDIT_PLAN.md`'s committed claim that growth *"by round 15 changes
which player is taken"* was right where I was wrong.

D5 / TASK `#37` -- THE FLAT REGIONS. `bpa` collapses to 0.00 board-wide once positional demand is
exhausted, so late upside boards carry large exactly-tied blocks: 116 tied rows of 240 in round 8,
49 of 120 in round 18. The residual order inside a block was `player_id` -- deterministic (an
earlier fix made it so, having measured 37 of ~500 rows reordering when `players_db` key order was
reversed) and arbitrary, because a Sleeper player id is a registration number. 1.3's precedent
allows a convention for a residual tie where the convention is STATED, so it is stated: among
candidates the board cannot distinguish, prefer the one projected to score more this season.

WHAT WAS MEASURED AND DECLINED. The balanced board's `universal_value` resolves 87.8% of tied rows
against `projected_points`' 58.8% (769 tied rows, seven board states). Declined on `#126`: it would
put a SECOND notion of team-agnostic value on a board whose `universal_value` is defined as
`final_score` itself. What that 29 points would buy is which of two equal rows a person reads
second, and an architectural rule is not worth that.
"""

from __future__ import annotations

import collections
import unittest

import pandas as pd

import data_merger as dm
import draft_room as dr

ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"] + ["BN"] * 11
NUM_TEAMS = 12
LEAGUE = {"roster_positions": ROSTER, "total_rosters": NUM_TEAMS,
          "settings": {"type": 2}, "scoring_settings": {}}

#: Late enough that bpa has collapsed and tied blocks exist. The flat region is the whole subject
#: of D5, so a fixture that does not reach it tests nothing.
ROUNDS = (8, 12, 16, 18)


class OneRateForOnePercentilePairTests(unittest.TestCase):

    def test_the_second_conversion_rate_is_gone_rather_than_aliased(self):
        self.assertFalse(hasattr(dr, "UPSIDE_GROWTH_WEIGHT"),
                         "the old name survives, so one percentile pair can be priced two ways")

    def test_growth_converts_at_the_slope_the_other_reader_uses(self):
        row = pd.Series({"bpa": 40.0, "_has_3yr": True, "_season_proj_pct": 10.0,
                         "_proj3yr_pct": 30.0, "bpa_source": None})
        out = dr.upside_score(row)
        self.assertAlmostEqual(out["final_score"], 40.0 + dr.TIME_HORIZON_SLOPE * 20.0, places=2)
        self.assertAlmostEqual(out["growth_signal"], 20.0, places=1)

    def test_the_two_readers_agree_term_for_term_on_the_same_gap(self):
        """The property, not the constant: whatever the slope becomes, both readers move together.
        time_horizon_adj's arithmetic is inlined at its call site, so it is restated here in the
        one place that is allowed to -- a test whose whole subject is that the two agree."""
        for season, three_year in ((10.0, 30.0), (40.0, 95.0), (50.0, 50.0), (80.0, 81.0)):
            gap = three_year - season
            with self.subTest(gap=gap):
                horizon = min(max(gap * dr.TIME_HORIZON_SLOPE, dr.TIME_HORIZON_CLAMP[0]),
                              dr.TIME_HORIZON_CLAMP[1])
                out = dr.upside_score(pd.Series(
                    {"bpa": 0.0, "_has_3yr": True, "_season_proj_pct": season,
                     "_proj3yr_pct": three_year, "bpa_source": None}))
                self.assertAlmostEqual(out["final_score"], horizon, places=6)

    def test_the_clamp_still_binds_at_the_shared_bound(self):
        """Non-vacuity for the clamp: at the new slope it takes a 50-point gap to reach +10, so a
        rate change could silently make the bound unreachable."""
        out = dr.upside_score(pd.Series(
            {"bpa": 0.0, "_has_3yr": True, "_season_proj_pct": 0.0, "_proj3yr_pct": 100.0,
             "bpa_source": None}))
        self.assertAlmostEqual(out["final_score"], dr.TIME_HORIZON_CLAMP[1], places=6)

    def test_the_new_rate_is_lower_so_the_term_was_moderated_not_amplified(self):
        """States the direction of the change, because `#184`'s complaint was that a percentile was
        being treated as worth more than a point. 0.5 -> 0.20 answers it downward; a repair that
        moved it the other way would satisfy every assertion above."""
        self.assertLess(dr.TIME_HORIZON_SLOPE, 0.5)

    def test_growth_is_still_reported_whatever_it_is_priced_at(self):
        """D4's three options all agreed the FIGURE stays readable; only the pricing was in
        question. A repair that dropped the observable would be answering a different item."""
        out = dr.upside_score(pd.Series(
            {"bpa": 5.0, "_has_3yr": True, "_season_proj_pct": 20.0, "_proj3yr_pct": 44.0,
             "bpa_source": None}))
        self.assertAlmostEqual(out["growth_signal"], 24.0, places=1)

    def test_an_absent_three_year_outlook_still_yields_no_growth_rather_than_a_manufactured_one(self):
        """The `_has_3yr` guard, which is why auto-mode's 672 picks measured almost no growth and
        why D4(c)'s premise did not transfer to explicit upside mode. Pinned here so the rate
        change cannot be read as having touched it."""
        out = dr.upside_score(pd.Series(
            {"bpa": 5.0, "_has_3yr": False, "_season_proj_pct": 2.0, "_proj3yr_pct": 50.0,
             "bpa_source": None}))
        self.assertAlmostEqual(out["growth_signal"], 0.0, places=2)
        self.assertAlmostEqual(out["final_score"], 5.0, places=2)


class _RealUpsideBoards(unittest.TestCase):

    boards: list = []

    @classmethod
    def setUpClass(cls):
        merger = dm.DataMerger()
        proj = merger.projections
        players_db = {}
        pid = 0
        for position in ("QB", "RB", "WR", "TE", "K", "DEF"):
            for _, row in proj[proj["position"] == position].sort_values(
                    "trade_value", ascending=False).iterrows():
                pid += 1
                parts = str(row["name"]).split()
                players_db[str(pid)] = {
                    "first_name": parts[0] if parts else "",
                    "last_name": " ".join(parts[1:]) or (parts[0] if parts else ""),
                    "position": position, "fantasy_positions": [position],
                    "team": row.get("team"),
                }
        opening = dr.compute_draft_board(merger, players_db, [], my_roster_id="1",
                                         league=LEAGUE, mode="balanced")
        cls.boards = []
        for rounds in ROUNDS:
            taken = rounds * NUM_TEAMS
            picks = [{"player_id": r["player_id"], "roster_id": str((i % NUM_TEAMS) + 1),
                      "round": (i // NUM_TEAMS) + 1, "pick_no": i + 1}
                     for i, r in enumerate(opening[:taken])]
            cls.boards.append((rounds, dr.compute_draft_board(
                merger, players_db, picks, my_roster_id="1", league=LEAGUE, mode="upside")))

    @staticmethod
    def _tied_blocks(board):
        """Consecutive runs sharing one final_score, inside one feasibility/fieldability tier --
        which is the only place the value tie-break governs anything."""
        priced = [r for r in board if r.get("final_score") is not None]
        blocks = []
        run = [priced[0]] if priced else []
        for row in priced[1:]:
            same = (row["final_score"] == run[-1]["final_score"]
                    and bool(row.get("fills_required_slot")) == bool(run[-1].get("fills_required_slot"))
                    and bool(row.get("cannot_be_fielded")) == bool(run[-1].get("cannot_be_fielded")))
            if same:
                run.append(row)
            else:
                if len(run) > 1:
                    blocks.append(run)
                run = [row]
        if len(run) > 1:
            blocks.append(run)
        return blocks


class TheFlatRegionHasAStatedConventionTests(_RealUpsideBoards):

    def test_the_flat_region_exists_at_all(self):
        """Non-vacuity, and the premise of the whole item: with no tied blocks there is no
        residual tie to have a policy about, and every assertion below is free."""
        total = sum(len(b) for _, board in self.boards for b in self._tied_blocks(board))
        self.assertGreater(total, 50,
                           f"only {total} rows sit in exactly-tied blocks; D5 has lost its "
                           f"subject and this class asserts nothing")

    def test_inside_a_tied_block_the_better_season_projection_is_listed_first(self):
        for rounds, board in self.boards:
            for block in self._tied_blocks(board):
                points = [r.get("projected_points") for r in block]
                present = [p for p in points if p is not None and p == p]
                with self.subTest(round=rounds, score=block[0]["final_score"]):
                    self.assertEqual(present, sorted(present, reverse=True),
                                     "a tied block is not ordered by projected_points, so the "
                                     "stated convention is not the one in force")

    def test_an_absent_projection_does_not_jump_the_queue(self):
        """The absence contract applied to an ORDERING (`#187` in a place it is easy to miss): a
        row with no projected points must not be sorted as though it had the highest."""
        for rounds, board in self.boards:
            for block in self._tied_blocks(board):
                seen_absent = False
                for row in block:
                    value = row.get("projected_points")
                    absent = value is None or value != value
                    if absent:
                        seen_absent = True
                    elif seen_absent:
                        self.fail(f"round {rounds}: a row with projected_points={value} is listed "
                                  f"after a row that has none")

    def test_player_id_remains_the_floor_under_the_convention(self):
        """A convention still needs something deterministic beneath it -- two players can tie on
        the score AND the projection, and the earlier fix that made this deterministic at all must
        survive the new key being inserted above it."""
        checked = 0
        for rounds, board in self.boards:
            for block in self._tied_blocks(board):
                by_points = collections.defaultdict(list)
                for row in block:
                    by_points[row.get("projected_points")].append(row["player_id"])
                for _points, ids in by_points.items():
                    if len(ids) > 1:
                        checked += 1
                        self.assertEqual(ids, sorted(ids),
                                         "rows tied on score AND projection are not in player_id "
                                         "order, so the deterministic floor is gone")
        self.assertGreater(checked, 0,
                           "no block contained two rows tied on both score and projection, so "
                           "the floor beneath the convention is untested")

    def test_the_convention_does_not_reach_across_the_backstops(self):
        """`feasibility_first` and `unfieldable_last` outrank value, and a tie-break inserted into
        the same sort must not be able to lift an unfieldable row over a fieldable one."""
        for rounds, board in self.boards:
            priced = [r for r in board if r.get("final_score") is not None]
            tiers = [(bool(r.get("fills_required_slot")), bool(r.get("cannot_be_fielded")))
                     for r in priced]
            fills = [not t[0] for t in tiers]
            self.assertEqual(fills, sorted(fills),
                             f"round {rounds}: required-slot rows are no longer grouped ahead")
            unfieldable = [t[1] for t in tiers]
            self.assertEqual(unfieldable, sorted(unfieldable),
                             f"round {rounds}: an unfieldable row has been lifted by the tie-break")


if __name__ == "__main__":
    unittest.main()
