"""#51, the IDP hostile-domain pass: what the pool can and cannot admit at IDP, and why.

IDP was picked as an adversarial domain because it is the one position family where this app's
data sources behave differently from everywhere else, and every valuation decision was designed
against offense. The pass found no arithmetic defect. It found a SUPPLY defect, and it is
structural rather than incidental.

MEASURED, against the committed baseline and the repo's own realistic IDP league shape
(run_idp_draft_validation.IDP_LEAGUE -- DL,DL,LB,LB,DB,DB,IDP_FLEX over 12 teams):

  * Draft Sharks projects 0 of 415 IDP players. Not few -- zero, for `projection` and
    `proj_3yr` alike, against 264 of 280 offensive players and 69 of 69 K/DEF.
  * It publishes a trade value for 76 of 415 (18%), against 264 of 280 offense (94%).
  * So the pool admits 76 IDP players. The other 339 are dropped by build_available_pool's
    "a real number means a projection OR a trade value" rule.
  * The drop is NOT an identity failure. All 415 match a canonical record; 339 match a record
    that is empty of numbers. This is source coverage, not name matching -- which matters,
    because the two have completely different remedies.
  * League-wide IDP STARTER demand in that shape is 84 (24 DL + 24 LB + 24 DB + 12 IDP_FLEX).
    Admitted supply is 76. DL is exactly 24 against 24 -- zero margin -- and DB is 23 against
    24, BELOW its own slot demand, before a single bench spot is considered.

WHY THIS IS NOT REPAIRED HERE, and what the actual remedy is.

The identical shape was already found and fixed at K/DEF: build_available_pool's own docstring
records supply capped at 13 of 37 kickers with no backfill, and the fix was widening admission
from "trade value" to "points OR trade value". That fix does nothing at IDP, because the widened
half is empty: there are no offline IDP points to admit.

The one remaining offline source with IDP rows is external_values -- 324 of them, from
FantasyPros and ESPN, and 124 of the 339 dropped players have a row there. It is not a latent
value source and must not be wired in as one:

  1. Those 324 rows carry `value_1qb` for exactly ZERO of them. They carry a RANK.
  2. Admitting a rank as a value is the cross-register laundering #61 and #70 spent the whole
     audit removing. A rank is a value comparison already collapsed into an integer.
  3. That filter IS the CDME ingestion boundary, the same standing rule that forbids solving the
     1QB consensus gap by adding FantasyPros to _consensus_lookup.

The real remedy is an INPUT, not a code change: live Sleeper IDP projections, scored through
this league's own scoring_settings. build_available_pool already has that wiring
(sleeper_projections + scoring_settings -> score_projection -> sleeper_points) and its docstring
already names IDP as the case it exists for. It is unreachable from this environment -- see #88
and #120, both blocked on network access -- so acquiring the input is the scheduled work, not
designing around its absence.

AND IT IS NOT A PAPER SHORTFALL. Simulated over 20 rounds of a 23-round league with each team
taking its own board's top row: DB exhausts outright in round 14, DL and LB in round 15, with a
third of the draft still to run. All 76 admitted IDP players get drafted and 8 of the 84 IDP
starter slots can never be filled by anyone. `unpriced` was 0 at every round, so this is not
#114's unpriced-tail phenomenon wearing a different hat -- the board does not run out of PRICES,
it runs out of ROWS. That simulation is 180 board builds and lives in POST_AUDIT_PLAN rather than
here; what is pinned below is the counting fact it confirms, which is cheap and equally decisive.

WHAT THIS FILE PINS. The numbers above, in the direction that matters: these tests fail if IDP
supply ever changes, in either direction. A source landing real IDP points is good news that
should still stop the build and be read, not absorbed silently -- and the shortfall quietly
getting worse should do the same.
"""

import collections
import unittest

import data_merger as dm
import draft_room as dr
from player_universe import player_name, player_position
from run_idp_draft_validation import IDP_LEAGUE, _build_pool_players_db

IDP = ("DL", "LB", "DB")
# The finer vendor codes are real IDP positions too -- see data_merger.IDP_POSITIONS for why
# _position_group has to recognise both schemes.
IDP_ANY = ("DL", "LB", "DB", "DE", "DT", "S", "CB", "EDGE")
OFFENSE = ("QB", "RB", "WR", "TE")


class IDPSourceCoverageTests(unittest.TestCase):
    """What the committed sources actually carry at IDP, before any board is built."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.proj = cls.merger.projections

    def _slice(self, positions):
        return self.proj[self.proj["position"].isin(positions)]

    def test_no_committed_source_projects_a_single_idp_player(self):
        idp = self._slice(IDP)
        self.assertEqual(len(idp), 415, "the IDP universe moved; re-read this whole module")
        self.assertEqual(idp["projection"].notna().sum(), 0)
        self.assertEqual(idp["proj_3yr"].notna().sum(), 0)

    def test_offense_and_kdst_are_projected_which_is_what_makes_idp_the_outlier(self):
        """Non-vacuity. Without this, "zero projections" could be a broken column read."""
        offense = self._slice(OFFENSE)
        self.assertGreater(offense["projection"].notna().sum(), 0.9 * len(offense))
        kdst = self._slice(("K", "DEF"))
        self.assertEqual(kdst["projection"].notna().sum(), len(kdst))

    def test_the_trade_value_branch_is_the_only_idp_pricing_path_and_it_covers_18_percent(self):
        idp = self._slice(IDP)
        priced = int(idp["trade_value"].notna().sum())
        self.assertEqual(priced, 76)
        offense = self._slice(OFFENSE)
        self.assertGreater(offense["trade_value"].notna().sum() / len(offense), 0.9,
                           "offense's coverage is what makes 18% a gap rather than a norm")

    def test_external_values_carries_idp_ranks_and_no_idp_values_at_all(self):
        """The reason external_values is not a latent fix. A rank is not a value, and admitting
        one as a value is the cross-register laundering #61/#70 removed."""
        ev = self.merger.external_values
        idp_rows = ev[ev["position"].isin(IDP_ANY)]
        self.assertGreater(len(idp_rows), 300, "precondition: there ARE IDP rows here")
        self.assertEqual(int(idp_rows["value_1qb"].notna().sum()), 0)
        self.assertEqual(int(idp_rows["value_2qb"].notna().sum()), 0)
        self.assertGreater(int(idp_rows["rank"].notna().sum()), 0,
                           "they carry a rank -- which is exactly the thing not to admit")


class IDPPoolAdmissionTests(unittest.TestCase):
    """Why 339 of 415 never reach the board, and why the answer is 'source coverage'."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db = _build_pool_players_db(cls.merger)

    def test_every_dropped_idp_player_matched_a_record_that_was_simply_empty(self):
        """Identity vs coverage, and they have different remedies. If these were unmatched, the
        fix would be at the name boundary (#82's territory). They are matched and numberless, so
        the fix is a data source."""
        tally = collections.Counter()
        for player_id, info in self.players_db.items():
            position = player_position(info)
            if position not in IDP:
                continue
            match = self.merger.merge_player(
                player_name(info, player_id), position=position, team=info.get("team"))
            if not match.get("matched"):
                tally["unmatched"] += 1
            elif match.get("trade_value") is None and match.get("projection") is None:
                tally["matched_but_numberless"] += 1
            else:
                tally["admitted"] += 1
        self.assertEqual(tally["unmatched"], 0,
                         "an identity failure appeared -- that is a DIFFERENT defect from this one")
        self.assertEqual(tally["matched_but_numberless"], 339)
        self.assertEqual(tally["admitted"], 76)


class IDPSupplyCannotFillTheLeagueTests(unittest.TestCase):
    """The finding itself: admitted supply is below the league's own starting-lineup demand."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db = _build_pool_players_db(cls.merger)
        cls.board = dr.compute_draft_board(
            cls.merger, cls.players_db, [], my_roster_id="1", league=IDP_LEAGUE, mode="balanced")
        cls.supply = collections.Counter(
            row["position"] for row in cls.board if row["position"] in IDP)
        slots = collections.Counter(p for p in IDP_LEAGUE["roster_positions"] if p != "BN")
        teams = IDP_LEAGUE["total_rosters"]
        cls.demand = {position: slots[position] * teams for position in IDP}
        # IDP_FLEX draws from the same three positions, so it is real demand on the same supply.
        cls.total_demand = sum(cls.demand.values()) + slots["IDP_FLEX"] * teams

    def test_the_admitted_idp_pool_cannot_fill_the_leagues_idp_starting_slots(self):
        total_supply = sum(self.supply.values())
        self.assertEqual(total_supply, 76)
        self.assertEqual(self.total_demand, 84)
        self.assertLess(total_supply, self.total_demand,
                        "supply caught up with demand -- good news, and it still means this "
                        "module's numbers are stale and need re-reading")

    def test_db_supply_is_below_its_own_slot_demand_and_dl_has_zero_margin(self):
        self.assertEqual(self.supply["DB"], 23)
        self.assertEqual(self.demand["DB"], 24)
        self.assertLess(self.supply["DB"], self.demand["DB"])
        self.assertEqual(self.supply["DL"], 24)
        self.assertEqual(self.demand["DL"], 24)

    def test_offense_has_real_margin_in_the_same_league_so_this_is_not_a_pool_wide_bug(self):
        """Non-vacuity for the shortfall, and the contrast that makes it a finding rather than a
        fact about fantasy football. Same board, same call, same fixture, same league: offense
        clears its own starter demand 2.75x while IDP comes in at 0.90x. The pool is not
        globally thin; it is thin at exactly the position family no committed source projects."""
        offense_supply = sum(1 for row in self.board if row["position"] in OFFENSE)
        slots = collections.Counter(p for p in IDP_LEAGUE["roster_positions"] if p != "BN")
        offense_demand = (sum(slots[p] for p in OFFENSE) + slots["FLEX"]) * IDP_LEAGUE["total_rosters"]
        self.assertEqual((offense_supply, offense_demand), (264, 96))
        offense_ratio = offense_supply / offense_demand
        idp_ratio = sum(self.supply.values()) / self.total_demand
        self.assertGreater(offense_ratio, 2.0)
        self.assertLess(idp_ratio, 1.0)

    def test_every_admitted_idp_row_is_priced_off_the_trade_value_branch_and_says_so(self):
        """The board does not hide which branch priced these -- bpa_source names it and
        confidence is 35.0 against offense's 80.0. Pinned because #51's whole premise was that
        the trade_value branch IS the IDP path, and an untested branch on a hostile domain is
        exactly where a silent change would land."""
        idp_rows = [row for row in self.board if row["position"] in IDP]
        self.assertEqual(len(idp_rows), 76)
        self.assertEqual({row["bpa_source"] for row in idp_rows},
                         {"position_relative_trade_value_vor"})
        self.assertEqual({row["confidence"] for row in idp_rows}, {35.0})
        self.assertTrue(all(row["final_score"] is not None for row in idp_rows),
                        "an admitted row must be priced -- admission is 'we have a number'")
        offense_rows = [row for row in self.board if row["position"] in OFFENSE]
        self.assertEqual({row["bpa_source"] for row in offense_rows}, {"points_vor_draftsharks"})
        self.assertEqual({row["confidence"] for row in offense_rows}, {80.0})


if __name__ == "__main__":
    unittest.main()
