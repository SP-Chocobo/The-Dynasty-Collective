"""
K/DST integration battery.

K and DEF were absent from CDME's candidate universe for one reason only: no source in the
committed baseline carried them, so build_available_pool dropped every one of them at its
"no honest anchor exists" gate. The scoring architecture itself already handled them -- this
battery exists to keep proving that, because the single most likely way to break K/DST later
is to "fix" a symptom by adding positional special-casing that the general model already
expresses.

The hard rule these tests defend: THERE IS NO K/DST-SPECIFIC SCORING LOGIC ANYWHERE. Their
burial, their interchangeability, their streamability, and their late-round conversion into
roster necessities all fall out of replacement level, VOR, survival, need_bonus and the
late-round necessity cap operating exactly as they do for every other position.

The distinction the battery is really built around, and the one worth preserving above all
the individual numbers:

    A required roster slot creates DEMAND.
    It does not, by itself, establish immediate draft URGENCY.

The engine must be able to say "you need a kicker eventually" and "there is essentially zero
cost to waiting" at the same time, without either statement being hardcoded.
"""

from __future__ import annotations

import unittest

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
import pick_synthesis as ps

KDST_LEAGUE = {
    "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF",
                          "BN", "BN", "BN", "BN", "BN", "BN"],
    "total_rosters": 12, "settings": {"type": 2}, "scoring_settings": {},
}
NO_KDST_LEAGUE = {
    "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "BN", "BN", "BN"],
    "total_rosters": 12, "settings": {"type": 2}, "scoring_settings": {},
}


def _players_db(merger: dm.DataMerger, include_kdst: bool = True) -> dict[str, dict]:
    """Real Sleeper-shaped rows off the committed baseline, offense plus (optionally) the
    real K/DEF entries -- never a synthetic fixture, since the whole point is what the engine
    does with the ACTUAL Draft Sharks numbers."""
    proj = merger.projections
    db: dict[str, dict] = {}
    pid = 0
    positions = ("QB", "RB", "WR", "TE") + (("K", "DEF") if include_kdst else ())
    for pos in positions:
        sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False)
        if pos in ("QB", "RB", "WR", "TE"):
            sub = sub.head(40)
        for _, row in sub.iterrows():
            pid += 1
            parts = row["norm_name"].split()
            db[str(pid)] = {
                "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
            }
    return db


class SourceIngestionTests(unittest.TestCase):
    """The data half: K and DEF must actually reach the merger, with real numbers and no
    fabricated ones."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.proj = cls.merger.projections

    def test_kicker_and_defense_are_present_in_the_baseline(self):
        self.assertGreater((self.proj["position"] == "K").sum(), 0, "no kickers in the baseline")
        self.assertGreater((self.proj["position"] == "DEF").sum(), 0, "no defenses in the baseline")

    def test_kickers_carry_a_real_points_projection_and_a_multi_year_outlook(self):
        k = self.proj[self.proj["position"] == "K"]
        self.assertTrue(k["projection"].notna().all(), "kickers must carry a real season projection")
        self.assertTrue(k["proj_3yr"].notna().all(), "the DS dynasty kicker table does carry 3yr")

    def test_defenses_carry_a_real_points_projection_but_no_fabricated_multi_year_outlook(self):
        # Draft Sharks publishes DST only as a REDRAFT table -- there is no 3yr column to
        # read, and a team defense has no career arc to project. The absence must survive
        # ingestion as an absence, never as a stand-in number.
        d = self.proj[self.proj["position"] == "DEF"]
        self.assertTrue(d["projection"].notna().all(), "defenses must carry a real season projection")
        self.assertTrue(d["proj_3yr"].isna().all(), "a 3yr outlook must NOT be invented for DST")

    def test_defense_position_is_normalised_to_sleepers_vocabulary(self):
        # The source writes "DST" in its title; Sleeper's player database says "DEF". A
        # mismatch here would silently half-match every defense.
        self.assertIn("DEF", set(self.proj["position"]))
        self.assertNotIn("DST", set(self.proj["position"]))

    def test_fantasypros_rank_only_data_never_becomes_a_valuation_anchor(self):
        # FantasyPros publishes K/DST as rank statistics (BEST/WORST/AVG/STD.DEV) with no
        # value column at all. Those rows may exist for display/tier context, but converting
        # a RANK into a synthetic VALUE is exactly the fabrication CDME forbids.
        ev = self.merger.external_values
        if ev.empty or "position" not in ev.columns:
            self.skipTest("no external values loaded")
        kd = ev[ev["position"].isin(["K", "DST", "DEF"])]
        if kd.empty:
            self.skipTest("no external K/DST rows present")
        for col in ("value_1qb", "value_2qb"):
            if col in kd.columns:
                self.assertTrue(kd[col].isna().all(),
                                f"external K/DST {col} must not be feeding a value anchor")


class PoolAdmissionTests(unittest.TestCase):
    """The gate: real projections get a player in; nothing else does."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.db = _players_db(cls.merger)

    def _pool(self, league):
        from player_universe import league_usable_positions
        return dr.build_available_pool(
            self.merger, self.db, set(), league_usable_positions(league["roster_positions"]),
        )

    def test_kicker_and_defense_enter_the_pool_when_the_league_rosters_them(self):
        pool = self._pool(KDST_LEAGUE)
        self.assertGreater((pool["position"] == "K").sum(), 0)
        self.assertGreater((pool["position"] == "DEF").sum(), 0)

    def test_a_league_without_those_slots_admits_neither(self):
        # Nothing about having the DATA should surface a position the league cannot start.
        pool = self._pool(NO_KDST_LEAGUE)
        self.assertEqual((pool["position"] == "K").sum(), 0)
        self.assertEqual((pool["position"] == "DEF").sum(), 0)

    def test_admitted_kickers_and_defenses_are_points_anchored_not_trade_value_fallbacks(self):
        # bpa_source is the module's own honesty field about which anchor was actually used.
        # K/DST have real projections, so they must ride the points path like everyone else.
        board = dr.compute_draft_board(
            self.merger, self.db, [], my_roster_id="1", league=KDST_LEAGUE, mode="balanced",
        )
        for pos in ("K", "DEF"):
            sources = {r["bpa_source"] for r in board if r["position"] == pos}
            self.assertTrue(sources, f"no {pos} on the board")
            self.assertTrue(
                all(s.startswith("points_vor") for s in sources),
                f"{pos} should be points-anchored, got {sources}",
            )


class ValuationBurialTests(unittest.TestCase):
    """Priority: K/DST must be buried by real replacement math, with no positional rule."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.db = _players_db(cls.merger)
        cls.board = dr.compute_draft_board(
            cls.merger, cls.db, [], my_roster_id="1", league=KDST_LEAGUE, mode="balanced",
        )
        cls.rank = {r["player_id"]: i + 1 for i, r in enumerate(cls.board)}

    def _best(self, pos):
        return next(r for r in self.board if r["position"] == pos)

    def test_no_kicker_or_defense_reaches_the_early_board(self):
        for pos in ("K", "DEF"):
            best = self._best(pos)
            self.assertGreater(
                self.rank[best["player_id"]], 40,
                f"best {pos} ({best['name']}) surfaced at board rank "
                f"{self.rank[best['player_id']]} -- far too early",
            )

    def test_every_offensive_starter_position_outranks_the_best_kicker_and_defense(self):
        best_k = self.rank[self._best("K")["player_id"]]
        best_d = self.rank[self._best("DEF")["player_id"]]
        for pos in ("RB", "WR", "TE", "QB"):
            self.assertLess(self.rank[self._best(pos)["player_id"]], min(best_k, best_d))

    def test_replacement_rank_for_k_and_def_matches_real_league_demand(self):
        # One K slot x 12 teams = a replacement rank of 12, with no special-casing: the same
        # starter_slot_counts math every other position goes through.
        ranks = dr.replacement_ranks(KDST_LEAGUE["roster_positions"], num_teams=12)
        self.assertEqual(ranks["K"], 12)
        self.assertEqual(ranks["DEF"], 12)

    def test_positional_demand_collapses_as_the_position_is_drafted_out(self):
        drafted = {"K": 9}
        self.assertLess(
            dr.replacement_ranks(KDST_LEAGUE["roster_positions"], 12, drafted)["K"],
            dr.replacement_ranks(KDST_LEAGUE["roster_positions"], 12)["K"],
        )


class InterchangeabilityTests(unittest.TestCase):
    """Separation, which is a DIFFERENT question from priority: how much reason is there to
    prefer one candidate over the next at the same position?"""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.db = _players_db(cls.merger)
        cls.board = dr.compute_draft_board(
            cls.merger, cls.db, [], my_roster_id="1", league=KDST_LEAGUE, mode="balanced",
        )

    def _gaps(self, pos, n=6):
        vals = [r["bpa"] for r in self.board if r["position"] == pos][:n]
        return [round(vals[i] - vals[i + 1], 3) for i in range(len(vals) - 1)]

    def test_kicker_and_defense_separation_is_smaller_than_skill_position_separation(self):
        rb = sum(self._gaps("RB")) / max(len(self._gaps("RB")), 1)
        for pos in ("K", "DEF"):
            flat = sum(self._gaps(pos)) / max(len(self._gaps(pos)), 1)
            self.assertLess(flat, rb,
                            f"{pos} adjacent separation ({flat:.2f}) should be flatter than RB's ({rb:.2f})")

    def test_each_flat_position_contains_a_genuinely_interchangeable_block(self):
        # near_tie_with_leader is the EXISTING architectural concept for "the deterministic
        # ordering here must not be presented as a real preference," and it fires for
        # streamers without anyone teaching it what a streamer is.
        #
        # Deliberately NOT asserted at the top of the field: on the real Draft Sharks numbers
        # the leading kicker genuinely separates (adjacent tav gaps of 5.6/4.4/3.3 before the
        # field collapses to 0.06/0.47/0.08 from roughly K5 down), which is the engine
        # correctly reporting that "minimal separation" is not the same as "no separation."
        # What must be true is that each position CONTAINS a real interchangeable block.
        for pos in ("K", "DEF"):
            tavs = [r["final_score"] for r in self.board if r["position"] == pos]
            self.assertTrue(
                any(all(ps.near_tie_flags(tavs[s:s + 4])[1:]) for s in range(len(tavs) - 3)),
                f"{pos} should contain a window of mutually interchangeable candidates",
            )

    def test_the_leading_kicker_is_not_flattened_into_the_field(self):
        # The other half of the same point, and the thing a K/DST-specific "these are all the
        # same" hack would destroy: a genuinely better kicker must still read as better.
        tavs = [r["final_score"] for r in self.board if r["position"] == "K"]
        self.assertFalse(ps.near_tie_flags(tavs)[1],
                         "a real gap at the top of the kicker field must survive as a real gap")

    def test_top_skill_players_are_not_a_near_tie_group(self):
        # The contrast case: if everything flagged near-tie the flag would mean nothing.
        rb = [r["final_score"] for r in self.board if r["position"] == "RB"][:4]
        self.assertFalse(all(ps.near_tie_flags(rb)[1:]),
                         "top RBs are genuinely ordered and must not all read as ties")


class FlatPositionCliffTests(unittest.TestCase):
    """The latent defect K/DST exposed: a cliff is a RATIO, and a ratio is meaningless
    without dispersion to measure against."""

    def _board(self, pos, bpas):
        return [{"player_id": f"{pos}{i}", "position": pos, "bpa": b} for i, b in enumerate(bpas)]

    def test_a_hairline_gap_on_a_perfectly_flat_field_is_not_a_cliff(self):
        board = self._board("K", [5.0, 5.0, 5.0, 4.9, 4.9, 4.9, 4.9, 4.9])
        self.assertEqual(ps.detect_positional_cliff(board, "K2")["tier"], "LOW")

    def test_a_hairline_gap_on_a_near_flat_field_is_not_a_cliff(self):
        # The case a bare "typical_gap == 0" guard would have missed entirely: dispersion of
        # 0.01 is not zero, so the division succeeds and returns an enormous ratio.
        board = self._board("K", [5.00, 4.99, 4.98, 4.97, 4.87, 4.86, 4.85, 4.84])
        self.assertEqual(ps.detect_positional_cliff(board, "K3")["tier"], "LOW")

    def test_a_genuine_structural_cliff_still_reports_high(self):
        board = self._board("QB", [95.0, 60.0, 57.0, 54.0, 51.0, 48.0])
        self.assertEqual(ps.detect_positional_cliff(board, "QB0")["tier"], "HIGH")

    def test_a_real_standout_above_a_perfectly_tied_block_still_reports_high(self):
        # The case a naive "flat position => never a cliff" fix would have silently broken.
        board = self._board("K", [50.0, 5.0, 5.0, 5.0, 5.0, 5.0])
        self.assertEqual(ps.detect_positional_cliff(board, "K0")["tier"], "HIGH")

    def test_the_materiality_floor_is_derived_from_the_apps_own_noise_band(self):
        self.assertEqual(ps.CLIFF_MIN_MATERIAL_GAP, ps.NEAR_TIE_BAND)


class MissingMultiYearOutlookTests(unittest.TestCase):
    """Missing information is not negative information -- and, just as importantly, not
    positive information either."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.db = _players_db(cls.merger)
        cls.board = dr.compute_draft_board(
            cls.merger, cls.db, [], my_roster_id="1", league=KDST_LEAGUE, mode="balanced",
        )

    def test_defenses_get_exactly_no_time_horizon_opinion(self):
        # Not a penalty (the original min-fill) and not a bonus (what a "neutral 50th
        # percentile" produces when it stands on one side of a DIFFERENCE against a genuinely
        # low season percentile -- measured at +6.5 average before this was fixed).
        adjs = [r.get("time_horizon_adj", 0.0) for r in self.board if r["position"] == "DEF"]
        self.assertTrue(adjs, "no defenses on the board")
        for a in adjs:
            self.assertEqual(a, 0.0, "a missing 3yr outlook must produce no adjustment at all")

    def test_kickers_do_get_a_real_time_horizon_opinion(self):
        # The contrast: the DS dynasty kicker table DOES carry a 3yr column, so kickers must
        # still be scored on it. The guard is about absent data, not about the position.
        adjs = [r.get("time_horizon_adj", 0.0) for r in self.board if r["position"] == "K"]
        self.assertTrue(any(a != 0.0 for a in adjs),
                        "kickers carry a real 3yr outlook and should be adjusted on it")

    def test_the_change_is_a_no_op_for_every_player_carrying_a_full_projection(self):
        # Every row in the committed baseline that has a season projection also has a 3yr
        # projection, so this guard cannot have moved any pre-existing valuation.
        proj = self.merger.projections
        both_missing = proj[proj["projection"].notna() & proj["proj_3yr"].isna()]
        self.assertTrue(
            set(both_missing["position"]) <= {"DEF"},
            f"unexpected positions with points but no 3yr: {set(both_missing['position'])}",
        )


class DemandIsNotUrgencyTests(unittest.TestCase):
    """The invariant this whole pass is really about.

    An empty required slot creates demand -- need_bonus says so, correctly, and it is
    deliberately NOT muted for K/DST. What must ALSO be true is that demand alone does not
    manufacture urgency while the position is still trivially available later.
    """

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.db = _players_db(cls.merger)

    def test_an_empty_kicker_slot_produces_real_demand(self):
        board = dr.compute_draft_board(
            self.merger, self.db, [], my_roster_id="1", league=KDST_LEAGUE, mode="balanced",
        )
        best_k = next(r for r in board if r["position"] == "K")
        self.assertGreater(best_k["need_bonus"], 0.0,
                           "an unfilled dedicated K slot must still register as demand")

    def test_need_bonus_is_not_muted_for_kickers_relative_to_other_dedicated_slots(self):
        # Guards against the tempting positional hack. The cost of an empty starting slot is
        # genuinely comparable across positions; a flat term is the correct model, and any
        # future "special-case K/DST need" would trip this.
        #
        # Compared against QB specifically, because the comparison has to be like-for-like:
        # QB, K and DEF all occupy a dedicated slot with NO flex eligibility, so all three
        # should price at exactly NEED_BONUS_PER_DEDICATED_SLOT. TE/RB/WR legitimately price
        # higher (4.33 / 8.33) because they carry real flex capacity on top -- that is the
        # slot structure differing, not the position being favoured.
        board = dr.compute_draft_board(
            self.merger, self.db, [], my_roster_id="1", league=KDST_LEAGUE, mode="balanced",
        )
        needs = {pos: next(r for r in board if r["position"] == pos)["need_bonus"]
                 for pos in ("K", "DEF", "QB")}
        self.assertAlmostEqual(needs["K"], needs["QB"], places=6,
                               msg="K's dedicated-slot demand must not be specially discounted")
        self.assertAlmostEqual(needs["DEF"], needs["QB"], places=6,
                               msg="DEF's dedicated-slot demand must not be specially discounted")
        self.assertAlmostEqual(needs["K"], dr.NEED_BONUS_PER_DEDICATED_SLOT, places=6)

    def test_demand_does_not_lift_a_kicker_into_the_early_board(self):
        # Demand exists, but it is added to a genuinely small universal_value -- it must not
        # be enough to promote a streamer past real skill players.
        board = dr.compute_draft_board(
            self.merger, self.db, [], my_roster_id="1", league=KDST_LEAGUE, mode="balanced",
        )
        rank = {r["player_id"]: i + 1 for i, r in enumerate(board)}
        best_k = next(r for r in board if r["position"] == "K")
        self.assertGreater(rank[best_k["player_id"]], 40)


class StreamingBehaviorTests(unittest.TestCase):
    """Whether "there is no reason to take this yet" emerges from survival/opportunity cost
    rather than from a rule about kickers."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.db = _players_db(cls.merger)
        cls.pick_order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=16)

    def test_a_kicker_far_down_the_board_carries_a_low_take_probability(self):
        # The mechanism behind streaming: opponents' boards rank K/DST deep, so the per-pick
        # chance anyone takes one is the floor value, not a scarcity-driven number.
        self.assertEqual(ds._take_probability(60, is_run_position=False),
                         ds.RANK_TAKE_PROBABILITY_FLOOR)

    def test_waiting_costs_almost_nothing_when_survival_is_high(self):
        # expected_value_of_waiting is already the engine's own "what do I keep if I pass"
        # number. For a high-survival candidate it must be nearly the full value.
        uv = 15.0
        ev_wait = ps.expected_value_of_waiting(uv, 0.98)
        self.assertLess(uv - ev_wait, 1.0,
                        "passing on a ~98%-survival candidate should cost well under a point")


class LateRoundNecessityTests(unittest.TestCase):
    """The existing late-round damping already covers the rounds K/DST are actually drafted
    in -- which is why no K/DST-specific late-round penalty may be added on top."""

    def test_late_round_necessity_is_uniformly_damped_for_every_position(self):
        c = {"team_acquisition_value": 20.0, "universal_value": 18.0, "survival_probability": 0.98,
             "positional_cliff": None, "position_run_detected": False, "rival_premium": 0.0,
             "need_bonus": 4.0, "eligibility_bonus": 0.0}
        early = ps.compute_pick_necessity([c], round_num=1)[0][0]
        late = ps.compute_pick_necessity([c], round_num=ps.LATE_ROUND_THRESHOLD)[0][0]
        self.assertLess(late, early, "late-round necessity must be damped")
        self.assertLessEqual(late, ps.LATE_ROUND_NECESSITY_CAP)

    def test_the_damping_is_not_position_aware(self):
        # compute_pick_necessity never sees a position at all -- the strongest possible
        # guarantee that the damping cannot be secretly K/DST-specific.
        import inspect
        src = inspect.getsource(ps.compute_pick_necessity)
        for token in ('"K"', "'K'", '"DEF"', "'DEF'", '"DST"', "'DST'"):
            self.assertNotIn(token, src,
                             "pick necessity must contain no positional special cases")


class NoPositionalSpecialCasingTests(unittest.TestCase):
    """A blunt structural guard. If someone later "fixes" K/DST urgency by hardcoding the
    position into the valuation path, this fails loudly."""

    def test_no_kicker_or_defense_literals_in_the_scoring_paths(self):
        import inspect
        for fn in (dr.compute_draft_board, dr.replacement_levels, dr.starter_slot_counts,
                    ps.compute_pick_necessity, ps.detect_positional_cliff, ps.narrow_candidates):
            src = inspect.getsource(fn)
            for token in ('"K"', "'K'", '"DST"', "'DST'"):
                self.assertNotIn(
                    token, src,
                    f"{fn.__name__} must not special-case a position by literal",
                )


if __name__ == "__main__":
    unittest.main()
