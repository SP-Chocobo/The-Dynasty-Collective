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
                # NOTE: eligibility is FLATTENED here -- one position per player. The
                # committed baseline carries a single `position` per row, and real
                # multi-position listings (Travis Hunter is WR/DB) only exist in Sleeper's
                # own players_db. Never write a test that infers "no dual-eligible players
                # exist" from this fixture; it would be reading its own construction back.
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

    def test_kickers_carry_a_real_points_projection_but_no_fabricated_multi_year_outlook(self):
        # Kicker points now come from the league's own scoring_settings rather than a vendor
        # export (sleeper_kicker_projections.csv, regenerable via
        # sleeper_client.build_baseline_projection_rows). Sleeper publishes no multi-year
        # outlook, so -- exactly as with DST below -- that absence has to survive ingestion
        # as an absence rather than as a stand-in number.
        k = self.proj[self.proj["position"] == "K"]
        self.assertTrue(k["projection"].notna().all(), "kickers must carry a real season projection")
        self.assertTrue(k["proj_3yr"].isna().all(), "a 3yr outlook must NOT be invented for kickers")

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

    def test_a_real_projection_admits_a_player_with_no_vendor_trade_value(self):
        # The rule that used to require trade_value outright. It was equivalent to "has a
        # real number" until league-scored points began arriving from a source that
        # publishes no trade values at all.
        pool = self._pool(KDST_LEAGUE)
        no_tv = pool[pool["trade_value"].isna()]
        self.assertGreater(len(no_tv), 0, "nobody is riding the projection-only path")
        self.assertTrue(no_tv["projection"].notna().all(),
                        "a projection-only admission must still carry a real projection")

    def test_widening_the_gate_adds_nobody_at_an_offensive_position(self):
        # The blast-radius guarantee that made this change safe to make at all: every
        # offensive player the ranking sources project also carries a trade value, so the
        # old and new rules are still exactly equivalent there. If this ever fails, the
        # change has started moving players it was measured not to touch.
        pool = self._pool(KDST_LEAGUE)
        for pos in ("QB", "RB", "WR", "TE"):
            rows = pool[pool["position"] == pos]
            self.assertTrue(rows["trade_value"].notna().all(),
                            f"{pos} gained a projection-only admission; blast radius has widened")

    def test_position_depth_backfills_instead_of_running_dry(self):
        # The failure this replaced: the admitted players were a permanent allowlist, so
        # drafting them emptied the position to zero while real projected players sat
        # unused. A 12-team league where managers take a second defense for bye/matchup
        # coverage needs the position to outlast 12 picks, not exactly reach it.
        from player_universe import league_usable_positions
        usable = league_usable_positions(KDST_LEAGUE["roster_positions"])
        pool = dr.build_available_pool(self.merger, self.db, set(), usable)
        teams = KDST_LEAGUE["total_rosters"]
        for pos in ("K", "DEF"):
            ids = list(pool[pool["position"] == pos]["player_id"])
            self.assertGreater(len(ids), teams,
                               f"{pos} supply must outlast one per team")
            after = dr.build_available_pool(self.merger, self.db, set(ids[:teams]), usable)
            self.assertGreater(
                (after["position"] == pos).sum(), 0,
                f"{pos} ran dry after {teams} were drafted -- no backfill from the baseline",
            )


class ProjectionOnlyAdmissionScoringTests(unittest.TestCase):
    """Scoring a player who has points but no trade value at all."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.db = _players_db(cls.merger)
        cls.board = dr.compute_draft_board(
            cls.merger, cls.db, [], my_roster_id="1", league=KDST_LEAGUE, mode="balanced",
        )

    def test_the_board_builds_at_all(self):
        # Regression: eligibility_bonus is denominated in trade_value units, and passing a
        # missing one straight through reached the lineup optimizer's Hungarian cost matrix
        # and raised "matrix contains invalid numeric entries" outright.
        self.assertTrue(self.board)

    def test_a_missing_trade_value_declines_the_flexibility_premium_rather_than_inventing_one(self):
        # Same rule as a missing 3yr outlook: exactly 0.0, not a stand-in number, and not a
        # penalty either. K/DEF are single-slot positions with no flexibility to price anyway.
        from player_universe import league_usable_positions
        pool = dr.build_available_pool(
            self.merger, self.db, set(), league_usable_positions(KDST_LEAGUE["roster_positions"]))
        no_tv = set(pool[pool["trade_value"].isna()]["player_id"].astype(str))
        self.assertTrue(no_tv, "no projection-only players to check")
        checked = [r for r in self.board if str(r["player_id"]) in no_tv]
        self.assertTrue(checked)
        for row in checked:
            self.assertEqual(row["eligibility_bonus"], 0.0)
            self.assertEqual(row["final_score"],
                             round(row["universal_value"] + row["need_bonus"], 2))


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
        # What must be true is that each position CONTAINS a real interchangeable block.
        # (Kickers now satisfy this across the WHOLE field rather than only from K5 down --
        # see test_the_kicker_field_is_a_near_tie_under_league_scored_points for why that
        # changed when their points stopped coming from a vendor's scoring assumptions.)
        for pos in ("K", "DEF"):
            tavs = [r["final_score"] for r in self.board if r["position"] == pos]
            self.assertTrue(
                any(all(ps.near_tie_flags(tavs[s:s + 4])[1:]) for s in range(len(tavs) - 3)),
                f"{pos} should contain a window of mutually interchangeable candidates",
            )

    def test_the_kicker_field_is_a_near_tie_under_league_scored_points(self):
        # This assertion used to run the other way, and the reason it flipped is a data
        # change, not a scoring change: kicker points now come from the league's own
        # scoring_settings (sleeper_kicker_projections.csv) instead of a vendor export.
        #
        # Measured on the same 12 kickers, the K1-vs-K12 gap is 11 points league-scored,
        # against 33 in Draft Sharks' export and 31 in CBS's. A vendor export doesn't just
        # shift the level (VOR absorbs that) -- it inflates the SPREAD, which is precisely
        # what VOR reads as separation. On the vendor numbers the top kicker looked like a
        # genuinely separated leader (adjacent gaps 5.6/4.4/3.3); league-scored, every
        # adjacent gap in the field falls inside NEAR_TIE_BAND. Three points of season-long
        # separation between two kickers IS a tie, and the engine now says so on its own.
        #
        # The discriminating power of the flag is guarded by the RB contrast below: this is
        # the flag reporting a real property of the data, not a flag that fires on anything.
        tavs = [r["final_score"] for r in self.board if r["position"] == "K"]
        self.assertTrue(ps.near_tie_flags(tavs)[1],
                        "league-scored kickers separate by less than NEAR_TIE_BAND")

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
        cls.upside_board = dr.compute_draft_board(
            cls.merger, cls.db, [], my_roster_id="1", league=KDST_LEAGUE, mode="upside",
        )

    def test_defenses_get_exactly_no_time_horizon_opinion(self):
        # Not a penalty (the original min-fill) and not a bonus (what a "neutral 50th
        # percentile" produces when it stands on one side of a DIFFERENCE against a genuinely
        # low season percentile -- measured at +6.5 average before this was fixed).
        adjs = [r.get("time_horizon_adj", 0.0) for r in self.board if r["position"] == "DEF"]
        self.assertTrue(adjs, "no defenses on the board")
        for a in adjs:
            self.assertEqual(a, 0.0, "a missing 3yr outlook must produce no adjustment at all")

    def test_positions_carrying_a_real_3yr_outlook_do_get_a_time_horizon_opinion(self):
        # The contrast that keeps the guard honest: it must suppress the adjustment for
        # ABSENT data, not for particular positions. The offensive skill positions still
        # carry a real 3yr column and must still be scored on it.
        #
        # (Kickers were this contrast case until their points moved off the Draft Sharks
        # dynasty table, which carried a 3yr column, onto league-scored Sleeper projections,
        # which carry none. They are now covered by the DEF case above instead.)
        for pos in ("RB", "WR", "TE"):
            adjs = [r.get("time_horizon_adj", 0.0) for r in self.board if r["position"] == pos]
            self.assertTrue(adjs, f"no {pos} on the board")
            self.assertTrue(any(a != 0.0 for a in adjs),
                            f"{pos} carries a real 3yr outlook and should be adjusted on it")

    def test_upside_growth_is_exactly_zero_without_a_3yr_outlook(self):
        # The exact mirror of test_defenses_get_exactly_no_time_horizon_opinion, for the OTHER
        # consumer of the same percentile pair. upside_score read _season_proj_pct and
        # _proj3yr_pct without checking _has_3yr, so a row with real points and no 3yr outlook
        # produced growth = 50 - season_pct: a signal made entirely of the missing half.
        for pos in ("K", "DEF"):
            growths = [r.get("growth_signal", 0.0) for r in self.upside_board if r["position"] == pos]
            self.assertTrue(growths, f"no {pos} on the upside board")
            for g in growths:
                self.assertEqual(g, 0.0, f"{pos}: a missing 3yr outlook must produce no growth at all")

    def test_positions_carrying_a_real_3yr_outlook_still_get_a_growth_signal(self):
        # Same contrast as the time_horizon version: the guard must suppress the signal for
        # ABSENT data, not for particular positions. QB/WR/TE all carry real 3yr outlooks that
        # exceed their season percentile for at least some players, and must still score on it.
        # RB is deliberately NOT in this list -- see the next test for why its zero is a
        # different kind of zero.
        for pos in ("QB", "WR", "TE"):
            growths = [r.get("growth_signal", 0.0) for r in self.upside_board if r["position"] == pos]
            self.assertTrue(growths, f"no {pos} on the upside board")
            self.assertTrue(any(g > 0.0 for g in growths),
                            f"{pos} carries a real 3yr outlook and should still be scored on it")

    def test_a_measured_zero_and_an_absent_data_zero_are_different_things(self):
        # The distinction this whole class exists to protect, and the one the bug erased.
        # Every RB on a full-pool board scores growth 0.0 -- not because the data is missing
        # but because it is present and says so: an RB's 3yr outlook sits BELOW his season
        # percentile across the board, which is the aging cliff showing up exactly where it
        # should, then clipped at 0 because upside mode does not carry negative growth.
        # K and DEF also score 0.0, from having no 3yr outlook at all.
        #
        # Identical output, opposite meaning, and only _has_3yr tells them apart. A future
        # change that "fixes" one of these zeroes by relaxing the guard would silently
        # resurrect the artifact, so both are pinned here together with the flag that
        # separates them.
        rb = [r for r in self.upside_board if r["position"] == "RB"]
        kdef = [r for r in self.upside_board if r["position"] in ("K", "DEF")]
        self.assertTrue(rb and kdef)
        self.assertTrue(all(r.get("growth_signal", 0.0) == 0.0 for r in rb),
                        "an RB with a positive 3yr trajectory would invalidate this test's premise")
        self.assertTrue(all(r.get("growth_signal", 0.0) == 0.0 for r in kdef))
        # The measured group has the data; the absent group does not.
        proj = self.merger.projections
        rb_rows = proj[proj["position"] == "RB"]
        kdef_rows = proj[proj["position"].isin(["K", "DEF"])]
        self.assertTrue(rb_rows["proj_3yr"].notna().any(), "RB must actually carry 3yr data")
        self.assertFalse(kdef_rows["proj_3yr"].notna().any(), "K/DEF must actually lack it")

    def test_the_artifact_grew_as_the_player_got_worse(self):
        # Why this one mattered so much more than its size suggests. The fabricated signal was
        # 50 MINUS the season percentile, so it was LARGEST for the lowest-projected player --
        # the ranking it produced was inversely correlated with value, not merely noisy. On a
        # real 20-round board the 22-point kicker, last in the remaining pool, scored 48.10 and
        # ranked first overall. Pinning the direction, not the magnitude: among rows with no
        # 3yr outlook, a WORSE projection must never yield a HIGHER growth signal.
        rows = [r for r in self.upside_board
                if r["position"] in ("K", "DEF") and r.get("projected_points") is not None]
        self.assertGreater(len(rows), 10, "not enough points-but-no-3yr rows to test the direction")
        rows.sort(key=lambda r: r["projected_points"])
        worst, best = rows[0], rows[-1]
        self.assertLess(worst["projected_points"], best["projected_points"])
        self.assertLessEqual(
            worst.get("growth_signal", 0.0), best.get("growth_signal", 0.0),
            f"{worst['name']} projects {worst['projected_points']} vs {best['name']}'s "
            f"{best['projected_points']} but scored higher on growth",
        )

    def test_both_readers_of_the_percentile_pair_agree_on_what_absent_means(self):
        # The defect in one sentence: two functions read the same two columns, one checked
        # _has_3yr and the other did not. Any future third reader has to pass this too.
        by_id = {r["player_id"]: r for r in self.board}
        checked = 0
        for up in self.upside_board:
            bal = by_id.get(up["player_id"])
            if bal is None or up["position"] not in ("K", "DEF"):
                continue
            checked += 1
            self.assertEqual(bal.get("time_horizon_adj", 0.0), 0.0, up["name"])
            self.assertEqual(up.get("growth_signal", 0.0), 0.0, up["name"])
        self.assertGreater(checked, 10, "no shared rows compared")

    def test_only_sources_without_a_3yr_column_are_missing_one(self):
        # Points-but-no-3yr is confined to exactly the two positions whose committed source
        # publishes no multi-year outlook at all (DST's redraft-only table, and kickers'
        # league-scored Sleeper projections). Any other position appearing here would mean
        # a 3yr column went missing somewhere it actually exists.
        proj = self.merger.projections
        both_missing = proj[proj["projection"].notna() & proj["proj_3yr"].isna()]
        self.assertTrue(
            set(both_missing["position"]) <= {"DEF", "K"},
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


class ProjectionOnlyRosterVisibilityTests(unittest.TestCase):
    """A drafted player with no vendor trade value is invisible to the lineup optimizer.

    build_available_pool admits on "a projection OR a trade value", but _team_roster_players
    can only price in trade_value units, so it drops what it cannot price. The two
    team-specific terms therefore disagree about whether a roster slot is filled.

    These tests pin the CURRENT behaviour and the reason it is currently harmless, so the day
    it stops being harmless is a test failure rather than a silent mispricing. See
    _team_roster_players' own comment for why substituting a value is the wrong repair.
    """

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.db = _players_db(cls.merger)
        from player_universe import league_usable_positions
        cls.pool = dr.build_available_pool(
            cls.merger, cls.db, set(), league_usable_positions(KDST_LEAGUE["roster_positions"]))

    def _projection_only_rows(self):
        return self.pool[self.pool["trade_value"].isna()]

    def test_the_two_team_specific_terms_disagree_about_a_filled_slot(self):
        row = self._projection_only_rows().iloc[0]
        picks = [{"player_id": row["player_id"], "round": 14, "roster_id": "1"}]
        self.assertEqual(dr._team_starters_filled(picks, self.db, "1").get(row["position"]), 1,
                         "need_bonus must see the slot filled")
        self.assertEqual(len(dr._team_roster_players(picks, self.db, "1", self.merger)), 0,
                         "eligibility_bonus cannot price him, so he is dropped")

    def test_a_dual_eligible_projection_only_player_is_dropped_from_the_roster(self):
        """The defect made concrete, rather than a claim that it cannot happen.

        An earlier version of this test asserted every projection-only row was
        single-position and therefore harmless. That was VACUOUS: _players_db above sets
        fantasy_positions to [pos] for everyone, so the assertion tested the fixture, not the
        engine. Real Sleeper eligibility is multi-position for real players -- Travis Hunter is
        listed WR but is WR/DB, and he is named in lineup_optimizer's own module docstring and
        in draft_room's ELIGIBILITY_BONUS_MAX comment as the case that machinery was built for.

        So this pins the actual behaviour instead: give a projection-only player real dual
        eligibility and show he is still dropped, because _team_roster_players keys on
        trade_value and not on eligibility. His flexibility -- the whole thing
        eligibility_bonus exists to price -- is invisible to the optimizer.
        """
        from player_universe import player_eligible_positions
        row = self._projection_only_rows().iloc[0]
        player_id = str(row["player_id"])
        db = dict(self.db)
        info = dict(db[player_id])
        info["fantasy_positions"] = [info["position"], "WR"]   # a real Hunter-shaped listing
        db[player_id] = info

        self.assertEqual(len(player_eligible_positions(info)), 2, "fixture must be dual-eligible")
        picks = [{"player_id": player_id, "round": 14, "roster_id": "1"}]
        self.assertEqual(
            len(dr._team_roster_players(picks, db, "1", self.merger)), 0,
            "a projection-only player is dropped no matter how eligible he is")

    def test_offline_eligibility_cannot_prove_the_blind_spot_is_dormant(self):
        """Why there is no "it's currently harmless" assertion here any more.

        Multi-position eligibility lives in Sleeper's players_db, which this environment has
        no access to; the committed baseline carries a single `position` per row. Any offline
        test claiming projection-only players are single-position would be reading its own
        fixture back to itself. The honest statement is that the blind spot's live impact is
        UNKNOWN offline and must be checked against a real players_db.
        """
        from player_universe import player_eligible_positions
        flattened = {len(player_eligible_positions(v)) for v in self.db.values()}
        self.assertEqual(flattened, {1},
                         "fixture is single-position by construction -- so it can never "
                         "demonstrate the absence of dual-eligible projection-only players")
