"""#196: the vendor abbreviates, the key inherits the abbreviation, and real players vanish.

A paid export publishes names first-initial-only -- "J Price", "A Brown", "B Robinson". The
canonical key is built from that, so one vendor row legitimately matches every namesake who
shares an initial and a surname. The contested-identity guard then correctly refuses to price
several people off one record, and dropped them all. Measured on the committed capture before
this repair: 58 contested keys, 142 rows dropped, 56 of them carrying a real league-scored
projection -- Bijan Robinson (405.2), Jonathan Taylor (355.9), Justin Jefferson (315.7),
A.J. Brown (303.7). The engine had no value for the RB1 in dynasty football.

Three changes, each measured, none of them a maintained mapping table:
  1. exact-position rejection INSIDE the offence group only (_different_offense_position);
  2. an unrostered player is SAID to be unrostered -- Sleeper's "no team" is a positive
     statement, so it travels as the NO_NFL_TEAM sentinel and contradicts a vendor row naming
     a club through the ordinary symmetric rule (_contradicted). It is emphatically NOT read
     off a falsy team: that conflates "unrostered" with "the caller did not say", and doing so
     broke every free-text lookup in the app;
  3. the guard declines the BORROWED PRICE rather than the player, which is what recovers the
     one case no key can split (two Robinsons, both RB, both ATL, one vendor row).

Result: 58 contested keys -> 1, 142 dropped rows -> 2 (and those 2 keep their own prices).

THE FULL LEDGER, both directions, measured by building the pool from the committed capture on
51f1819 (#193 alone) and on this change, same inputs both arms: 2041 rows -> 2105. 69 players
arrive, including Bijan Robinson, Caleb Williams, Jaelan Phillips and Terrance Ferguson; 43
more rows carry a trade value (294 -> 337) and the priced population goes 329 -> 371.

FIVE players leave, and they leave for the right reason: each was holding a vendor number that
the stricter rules now say is not his. Justin Simmons (DB, unrostered, tv 10), Javess Blue (WR,
tv 6 / proj 88), Lakiem Williams (LB, tv 2), Durron Neal (WR, tv 1) and Ben Sauls (K, proj 41).
Every one is unrostered in the capture, NONE carried a sleeper_points of his own, and the total
value withdrawn is 19 trade points against 43 rows of trade value recovered. A borrowed price is
not a loss when it is taken back.

(An adversarial pass over an INTERMEDIATE state of this branch -- one that still carried the
asymmetric team clause, since removed -- reported 76 departures summing to 1206 trade points.
That measurement is void: it described code that no longer exists, and re-running it against the
settled tree gives the five above. Recorded here rather than dropped, because a number that
large deserves to be visibly retired rather than quietly replaced.)

Every test here was mutation-checked -- see MUTATIONS at the bottom.
"""
import unittest

import pandas as pd

import data_merger as dm
import draft_room as dr
import run_draft_battery as rdb
from player_universe import league_usable_positions


def _row(**kw):
    return pd.Series(kw)


class OffencePositionIsUnambiguousTests(unittest.TestCase):
    """Measured on the capture: 63 of 383 matched offensive rows carried an exact-position
    disagreement and EVERY ONE was a different person. No counterexample exists to trade away."""

    def test_a_tight_end_does_not_match_a_running_backs_row(self):
        # The Josiah Price shape: TE with no team taking Jadarian Price's RB/SEA row.
        self.assertTrue(dm.DataMerger._different_offense_position(_row(position="RB"), {"TE"}))

    def test_the_same_position_is_never_a_contradiction(self):
        self.assertFalse(dm.DataMerger._different_offense_position(_row(position="RB"), {"RB"}))

    def test_idp_is_left_alone_because_its_vendors_genuinely_disagree(self):
        # 96 of 401 matched IDP rows disagree on exact position, overwhelmingly LB<->DL,
        # DB<->DL and LB<->DB -- a vocabulary split about one man, not two men.
        for queried, matched in (("LB", "DL"), ("DL", "LB"), ("DB", "DL"), ("LB", "DB")):
            with self.subTest(queried=queried, matched=matched):
                self.assertFalse(
                    dm.DataMerger._different_offense_position(_row(position=matched), {queried}))

    def test_a_cross_group_pair_is_left_to_the_coarse_rejection(self):
        # WR-onto-DB is a real misidentification, but _different_identity_namespace already
        # rejects it. This function must not also claim it, or the two rules become one and
        # the IDP tolerance above is silently lost.
        self.assertFalse(dm.DataMerger._different_offense_position(_row(position="DB"), {"WR"}))
        self.assertTrue(dm.DataMerger._different_identity_namespace(_row(position="DB"), "WR"))
        # ...and the mirror, which is the arm that actually needs the eligible-side guard: an
        # IDP query against an offensive row must ALSO be left to the coarse rejection, or this
        # function starts claiming cross-group pairs and the IDP tolerance above is lost.
        self.assertFalse(dm.DataMerger._different_offense_position(_row(position="WR"), {"DB"}))
        self.assertTrue(dm.DataMerger._different_identity_namespace(_row(position="WR"), "DB"))

    def test_it_takes_a_SET_so_a_multi_position_player_survives(self):
        """Forward compatibility with #172, which makes fantasy_positions available. A player
        eligible at RB and WR must match a vendor row at EITHER, and today's single-position
        callers pass a singleton so the measured behaviour is unchanged."""
        self.assertFalse(dm.DataMerger._different_offense_position(_row(position="WR"), {"RB", "WR"}))
        self.assertTrue(dm.DataMerger._different_offense_position(_row(position="TE"), {"RB", "WR"}))

    def test_absence_on_either_side_is_not_a_contradiction(self):
        self.assertFalse(dm.DataMerger._different_offense_position(_row(position="RB"), set()))
        self.assertFalse(dm.DataMerger._different_offense_position(_row(position=None), {"RB"}))


class NoTeamIsAStatementNotAGapTests(unittest.TestCase):
    """Unrostered is a FACT. Unspecified is a GAP. The merger must not confuse them.

    Sleeper reports a club for everyone who has one, so a player it returns with no team is
    positively unemployed, and that contradicts a vendor row naming a club. But the caller who
    simply did not supply a team -- app.py's trade calculator resolves free text with neither
    team nor position -- has asserted nothing at all. An earlier version of this repair read
    both as the first and turned 16 tests red, because a falsy value cannot carry a fact. The
    fact travels as NO_NFL_TEAM, a team value like any other, and the ordinary symmetric
    disagreement rule below does the rest -- no asymmetric clause, no second code path."""

    def test_the_sentinel_must_not_be_falsy(self):
        """The whole repair rests on this. An empty string would collapse back into
        'the caller said nothing' at the `if team` guard and silently restore the regression."""
        self.assertTrue(dm.NO_NFL_TEAM)

    def test_the_unrostered_sentinel_contradicts_a_club_bearing_row(self):
        self.assertTrue(
            dm.DataMerger._contradicted(_row(team="MIN", position="WR"), "WR", dm.NO_NFL_TEAM))

    def test_an_unspecified_team_contradicts_nothing(self):
        # The trade calculator's shape. Absence of a claim is not a claim.
        self.assertFalse(dm.DataMerger._contradicted(_row(team="MIN", position="WR"), "WR", None))

    def test_the_reverse_direction_is_NOT_a_contradiction(self):
        # A vendor export that omits the club says nothing about the player. Written with the
        # column PRESENT and empty, which is how a real export arrives -- a row missing the
        # column entirely takes a different branch and would not exercise this rule at all.
        self.assertFalse(dm.DataMerger._contradicted(_row(team=None, position="WR"), "WR", "MIN"))
        self.assertFalse(dm.DataMerger._contradicted(_row(team=float("nan"), position="WR"), "WR", "MIN"))

    def test_two_unrostered_sides_agree(self):
        # Symmetry cuts both ways: if the sentinel is a team value, it matches itself.
        self.assertFalse(dm.DataMerger._contradicted(
            _row(team=dm.NO_NFL_TEAM, position="WR"), "WR", dm.NO_NFL_TEAM))

    def test_two_known_and_disagreeing_teams_still_reject(self):
        self.assertTrue(dm.DataMerger._contradicted(_row(team="MIN", position="WR"), "WR", "GB"))

    def test_two_known_and_agreeing_teams_do_not(self):
        self.assertFalse(dm.DataMerger._contradicted(_row(team="MIN", position="WR"), "WR", "MIN"))


class TheRulesAreActuallyWIRED_INTO_resolveTests(unittest.TestCase):
    """The helpers above are unit-tested, and that is not the same as being CALLED.

    An adversarial pass found five mutations that no test caught, and every one was an
    integration gap rather than a logic gap: deleting the club rejection from _resolve's key
    path, deleting the _different_offense_position call, and narrowing either of them all left
    the suite green because the only tests were against the helpers in isolation. These run
    through the real merger."""

    @classmethod
    def setUpClass(cls):
        import data_merger
        cls.merger = data_merger.DataMerger()

    def test_an_unrostered_namesake_cannot_take_a_rostered_players_row(self):
        # Van Jefferson (unrostered) must not resolve onto Justin Jefferson's WR/MIN row.
        got = self.merger.merge_player("Van Jefferson", position="WR", team=dm.NO_NFL_TEAM)
        self.assertFalse(got.get("matched"), "an unrostered namesake took a rostered row")

    def test_the_same_query_without_the_sentinel_still_resolves(self):
        """Non-vacuity for the test above AND the regression guard: the rejection must come
        from the sentinel, not from the name failing to match at all. A caller that simply did
        not supply a club -- the trade calculator's free-text path -- still gets his match."""
        got = self.merger.merge_player("Justin Jefferson")
        self.assertTrue(got.get("matched"))
        self.assertEqual(got.get("match_path"), "key")

    def test_a_free_text_lookup_with_no_team_and_no_position_still_resolves(self):
        # The exact shape app.py's trade calculator uses. This is the call that 16 tests went
        # red over when "no team" was read as "unrostered".
        for name in ("Bijan Robinson", "Maxx Crosby", "Ja'Marr Chase"):
            with self.subTest(name=name):
                self.assertTrue(self.merger.merge_player(name).get("matched"), name)

    def test_an_offence_position_disagreement_is_rejected_through_the_real_merger(self):
        # Josiah Price is a TE; the vendor's 'j price' row is an RB. Same key, same group.
        got = self.merger.merge_player("Josiah Price", position="TE", team=dm.NO_NFL_TEAM)
        self.assertFalse(got.get("matched"))

    def test_the_rostered_running_back_behind_that_key_still_resolves(self):
        """Non-vacuity: the rejection above must be about the POSITION, not about the name
        being unmatchable. The real Jadarian Price -- RB, SEA -- keeps his row."""
        got = self.merger.merge_player("Jadarian Price", position="RB", team="SEA")
        self.assertTrue(got.get("matched"))
        self.assertEqual(got.get("position"), "RB")

    # The four above all resolve down the FUZZY path, which an adversarial mutation pass
    # proved: deleting the club rejection from _resolve's KEY path, deleting the
    # _different_offense_position call there, or narrowing its argument to the empty set all
    # left this file green. Both paths carry the rules and both must be pinned. The two cases
    # below were found by replaying the committed Sleeper capture (6595 players) through the
    # key path and reading off what it rejects: 549 club rejections and 1 offence-position
    # rejection reach it, and these are the cleanest of each.

    def test_the_key_path_rejects_a_club_disagreement(self):
        """Two real Byron Youngs, both DL, one vendor 'B Young' row (LAR, trade value 18).
        Same position and same identity namespace, so the club rule is the ONLY thing
        standing between the Eagle and the Ram's price."""
        got = self.merger.merge_player("Byron Young", position="DL", team="PHI")
        self.assertFalse(got.get("matched"), "a Philadelphia DL took a Los Angeles DL's row")
        self.assertIsNone(got.get("trade_value"))

    def test_the_ram_that_row_belongs_to_still_resolves_through_the_key(self):
        # Non-vacuity, and it pins the PATH: if this stopped being a key match the test above
        # would silently move to some other rule and stop guarding the one it names.
        got = self.merger.merge_player("Byron Young", position="DL", team="LAR")
        self.assertTrue(got.get("matched"))
        self.assertEqual(got.get("match_path"), "key")
        self.assertEqual(got.get("trade_value"), 18.0)

    def test_the_key_path_rejects_an_offence_position_disagreement(self):
        """The 1-of-61 case named in _different_offense_position's docstring: Jermar Jefferson
        (RB, MIN) resolving onto the WR/MIN row that belongs to Justin Jefferson. They agree on
        club, so the rejection above cannot fire, and they share an identity namespace, so the
        coarse rule cannot either. Without the offence rule he is priced at 82 / 292."""
        got = self.merger.merge_player("Jermar Jefferson", position="RB", team="MIN")
        self.assertFalse(got.get("matched"), "a Viking RB took a Viking WR's projection")
        self.assertIsNone(got.get("projection"))

    def test_that_same_key_resolves_when_the_position_agrees(self):
        """Non-vacuity: the key itself is live and the club matches, so the ONLY thing the
        test above measures is the position. Note what this call returns -- it is deliberately
        the wrong answer, asserted here as evidence that the rule is what prevents it."""
        got = self.merger.merge_player("Jermar Jefferson", position="WR", team="MIN")
        self.assertTrue(got.get("matched"))
        self.assertEqual(got.get("match_path"), "key")


class TheGuardDeclinesThePriceNotThePlayerTests(unittest.TestCase):
    """The change that recovers the case no key can split."""

    @staticmethod
    def _contested_pool():
        # Both Robinsons: same position, same team, one vendor row between them. Each carries
        # his OWN league-scored projection, which is what makes keeping both rows honest.
        return pd.DataFrame([
            {"player_id": "1", "name": "Bijan Robinson", "position": "RB", "team": "ATL",
             "sleeper_points": 405.25, "trade_value": 99.0, "projection": 346.0,
             "proj_3yr": 1000.0, "source_file": "vendor.csv",
             "_canonical_key": ("b robinson", "RB"), "_match_verified": True,
             "_match_path": "key"},
            {"player_id": "2", "name": "Brian Robinson", "position": "RB", "team": "ATL",
             "sleeper_points": 89.41, "trade_value": 99.0, "projection": 346.0,
             "proj_3yr": 1000.0, "source_file": "vendor.csv",
             "_canonical_key": ("b robinson", "RB"), "_match_verified": True,
             "_match_path": "key"},
            {"player_id": "3", "name": "Someone Else", "position": "WR", "team": "KC",
             "sleeper_points": 210.0, "trade_value": 40.0, "projection": 200.0,
             "proj_3yr": 600.0, "source_file": "vendor.csv",
             "_canonical_key": ("s else", "WR"), "_match_verified": True,
             "_match_path": "key"},
        ])

    def test_both_contested_players_keep_their_rows(self):
        out = dr._drop_contested_identities(self._contested_pool())
        self.assertEqual(sorted(out["player_id"]), ["1", "2", "3"])

    def test_each_keeps_his_own_independently_scored_projection(self):
        out = dr._drop_contested_identities(self._contested_pool()).set_index("player_id")
        self.assertAlmostEqual(out.loc["1", "sleeper_points"], 405.25)
        self.assertAlmostEqual(out.loc["2", "sleeper_points"], 89.41)

    def test_the_one_number_neither_can_claim_is_claimed_by_neither(self):
        out = dr._drop_contested_identities(self._contested_pool()).set_index("player_id")
        # pd.isna, not assertIsNone: pandas stores an absent numeric as NaN inside the frame,
        # and the pool's boundary (see _records_with_normalized_nan) is what turns it into a
        # real None for consumers. Asserting None HERE would be asserting the wrong layer.
        for pid in ("1", "2"):
            # Named explicitly, NOT iterated from dr.VENDOR_DERIVED_COLUMNS. Iterating the
            # constant under test is a tautology: dropping "source_file" from it made this
            # assertion check three columns instead of four and passed either way.
            for column in ("trade_value", "projection", "proj_3yr", "source_file"):
                with self.subTest(player=pid, column=column):
                    self.assertTrue(pd.isna(out.loc[pid, column]),
                                    f"{pid} kept a disputed {column}")
            self.assertEqual(set(dr.VENDOR_DERIVED_COLUMNS),
                             {"trade_value", "projection", "proj_3yr", "source_file"},
                             "the vendor-field set changed; this test names them on purpose")
            self.assertTrue(pd.isna(out.loc[pid, "_canonical_key"]))
            self.assertFalse(out.loc[pid, "_match_verified"])
            # _match_path goes too. identity_basis reads path AND verified together, so a
            # surviving path relabelled these rows "ambiguous" -- provenance for a match that
            # no longer exists (#166's shape, found by the adversarial pass).
            self.assertTrue(pd.isna(out.loc[pid, "_match_path"]))

    def test_an_uncontested_row_is_not_touched(self):
        # Non-vacuity: the nulling is scoped to the dispute, not applied to the frame.
        out = dr._drop_contested_identities(self._contested_pool()).set_index("player_id")
        self.assertEqual(out.loc["3", "trade_value"], 40.0)
        self.assertEqual(out.loc["3", "projection"], 200.0)
        self.assertEqual(out.loc["3", "_canonical_key"], ("s else", "WR"))

    def test_the_fixture_above_carries_the_key_shape_merge_player_really_emits(self):
        """The hand-built pool above states its own `_canonical_key`, which means it cannot
        notice the real key changing shape underneath it -- and the real key DID change (#52
        phase 6): it was (norm_name, position GROUP) and is now (norm_name, position), because
        the group is coarse enough that a QB and an RB of the same name shared one key and were
        refused as though they had shared one vendor record. This ties the fixture to the
        producer so the two cannot drift apart silently."""
        merger = dm.DataMerger()
        priced = merger.projections[merger.projections["trade_value"].notna()]
        row = priced.iloc[0]
        emitted = merger.merge_player(row["name"], position=row["position"],
                                      team=row.get("team"))["match_canonical_key"]
        self.assertIsInstance(emitted, tuple)
        self.assertEqual(len(emitted), 2)
        fixture_key = self._contested_pool()["_canonical_key"].iloc[0]
        self.assertEqual(len(fixture_key), len(emitted))
        # The second element is the RAW position, not the coarse identity namespace.
        self.assertEqual(emitted[1], str(row["position"]))
        self.assertNotEqual(emitted[1], dm.identity_namespace(row["position"]),
                            "the key fell back to the coarse namespace, which is what made a "
                            "QB and an RB of the same name look like one vendor record")

    def test_two_namesakes_at_different_positions_are_two_records_not_one(self):
        """The defect the key shape caused, on real data. A first-initial export lists 'J Love'
        three times -- the GB quarterback, the ARI running back and a SEA defensive back -- and
        _resolve matches each to his own row, verified, exactly as it should. The canonical key
        then collapsed the QB and the RB onto ONE key, because both are `offense`, so the guard
        declared them contested and withdrew BOTH prices: a refusal invented by the key, not by
        the data. Measured on the IDP board: J Love, J Williams, K Williams and M Washington --
        eight pool rows, four distinct vendor records, all eight unpriced.
        """
        merger = dm.DataMerger()
        keys = {}
        for position, team in (("QB", "GB"), ("RB", "ARI")):
            match = merger.merge_player("J Love", position=position, team=team)
            if not match.get("matched"):
                self.skipTest("the committed baseline no longer carries both J Loves")
            keys[position] = match["match_canonical_key"]
            self.assertEqual(match["match_path"], "exact")
            self.assertTrue(match["match_verified"])
        self.assertNotEqual(keys["QB"], keys["RB"],
                            "two players matched to two different vendor rows still share one "
                            "canonical key, so the contested guard will refuse both")

    def test_one_vendor_record_behind_two_players_still_yields_ONE_key(self):
        """The other half, and the half that must not be traded away: the key is narrower now,
        so the case it exists for has to be shown still colliding. Two pool rows at the SAME
        position resolving to the same single row share a key, stay contested, and are still
        both refused -- which is what keeps Bijan and Brian Robinson from each claiming a trade
        value that belongs to exactly one of them."""
        merger = dm.DataMerger()
        first = merger.merge_player("Bijan Robinson", position="RB", team="ATL")
        second = merger.merge_player("Brian Robinson", position="RB", team="ATL")
        if not (first.get("matched") and second.get("matched")):
            self.skipTest("the committed baseline no longer carries the Robinson pair")
        self.assertEqual(first["match_canonical_key"], second["match_canonical_key"])
        pool = pd.DataFrame([
            {"player_id": "1", "name": "Bijan Robinson", "position": "RB", "team": "ATL",
             "sleeper_points": 405.25, "trade_value": 99.0, "projection": 346.0,
             "proj_3yr": 1000.0, "source_file": "vendor.csv",
             "_canonical_key": first["match_canonical_key"], "_match_verified": True,
             "_match_path": "key"},
            {"player_id": "2", "name": "Brian Robinson", "position": "RB", "team": "ATL",
             "sleeper_points": 89.41, "trade_value": 99.0, "projection": 346.0,
             "proj_3yr": 1000.0, "source_file": "vendor.csv",
             "_canonical_key": second["match_canonical_key"], "_match_verified": True,
             "_match_path": "key"},
        ])
        out = dr._drop_contested_identities(pool).set_index("player_id")
        for pid in ("1", "2"):
            with self.subTest(player=pid):
                self.assertTrue(pd.isna(out.loc[pid, "trade_value"]),
                                "a borrowed price survived the narrower key")
                self.assertAlmostEqual(out.loc[pid, "sleeper_points"],
                                       405.25 if pid == "1" else 89.41)

    #: The league these three read. K/DEF/IDP are deliberately absent: the contested pair this
    #: class is about are both running backs, and a wider universe only slows the pool build.
    ROSTER_POSITIONS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX"] + ["BN"] * 6

    @classmethod
    def _capture_players(cls):
        if not hasattr(cls, "_players"):
            cls._players, _ = rdb.build_players_db_from_capture()
        return cls._players

    def test_the_contest_survives_one_of_the_pair_being_DRAFTED(self):
        """#52 phase 7.1b. The guard counted canonical-key collisions among POOL rows, and
        drafting removes a row from the pool -- so the contest disappeared the moment either
        player was taken, which in a live draft is immediately.

        A contested identity is two different people resolving onto ONE vendor record. That is
        a fact about who they are; availability cannot decide it. Measured on the real capture
        before the repair: with both Robinsons available the guard fired and neither was priced;
        with Bijan drafted, Brian was alone in the pool, the count fell to one, and he inherited
        the 99.0 both of them had been refused -- while Bijan carried the same 99.0 onto his own
        roster. One value, claimed twice, by the machinery built to stop exactly that.
        """
        merger = dm.DataMerger()
        by_name = {}
        for pid, info in self._capture_players().items():
            name = dr.player_name(info, pid)
            if name in ("Bijan Robinson", "Brian Robinson"):
                by_name[name] = pid
        if len(by_name) != 2:
            self.skipTest("the committed capture no longer carries both Robinsons")
        bijan = by_name["Bijan Robinson"]
        usable = league_usable_positions(self.ROSTER_POSITIONS)

        both_available = dr.build_available_pool(
            merger, self._capture_players(), set(), usable)
        one_drafted = dr.build_available_pool(
            merger, self._capture_players(), {bijan}, usable)

        def brian(pool):
            rows = pool[pool["name"].astype(str) == "Brian Robinson"]
            self.assertEqual(len(rows), 1, "Brian Robinson is not in the pool")
            return rows.iloc[0]

        # Non-vacuity: the guard really does fire while both are available.
        self.assertTrue(pd.isna(brian(both_available)["trade_value"]),
                        "the contest is not firing even with both players on the board")
        # ...and it still fires once his twin is off it.
        self.assertTrue(
            pd.isna(brian(one_drafted)["trade_value"]),
            "drafting one of a contested pair handed the survivor the borrowed price")
        self.assertEqual(brian(one_drafted)["_contested_key"], ("b robinson", "RB"),
                         "the refusal was performed but not recorded, so nothing can read it")

    def test_a_player_drafted_out_of_a_contested_pair_is_not_priced_on_his_own_roster(self):
        """The other half of the same leak. _team_roster_players re-resolves each rostered
        player through the MERGER, where the contested price still sits -- so the number the
        board refuses to show was being used to solve that roster's own lineup.

        _team_roster_players' own docstring already states the principle it was breaking: "a
        player the pool will not price is one this engine has decided it cannot identify, and
        the roster does not get a second, looser opinion about who he is."
        """
        merger = dm.DataMerger()
        players = self._capture_players()
        bijan = next((pid for pid, info in players.items()
                      if dr.player_name(info, pid) == "Bijan Robinson"), None)
        if bijan is None:
            self.skipTest("the committed capture no longer carries Bijan Robinson")
        picks = [{"pick_no": 1, "round": 1, "roster_id": "1", "player_id": bijan}]
        usable = league_usable_positions(self.ROSTER_POSITIONS)
        pool = dr.build_available_pool(merger, players, {bijan}, usable)
        contested = frozenset(k for k in pool.get("_contested_key", []) if isinstance(k, tuple))
        self.assertIn(("b robinson", "RB"), contested, "the pool recorded no contest to honour")

        priced = dr._team_roster_players(picks, players, "1", merger, contested)
        self.assertEqual([r["id"] for r in priced], [],
                         "a contested price reached the roster's own lineup solve")
        # NON-VACUITY, and it is the whole of the check: without the contested set the same
        # call prices him, so the emptiness above is the refusal and not a broken fixture.
        unguarded = dr._team_roster_players(picks, players, "1", merger)
        self.assertEqual([r["id"] for r in unguarded], [bijan])
        self.assertEqual(unguarded[0]["value"], 99.0)

    def test_an_UNcontested_drafted_player_keeps_his_price(self):
        """The scope check. The refusal is keyed on the contest, not applied to every rostered
        player, or eligibility_bonus would solve against an empty roster everywhere."""
        merger = dm.DataMerger()
        players = self._capture_players()
        usable = league_usable_positions(self.ROSTER_POSITIONS)
        pool = dr.build_available_pool(merger, players, set(), usable)
        priced_rows = pool[pool["trade_value"].notna()]
        self.assertTrue(len(priced_rows) > 50, "not enough priced rows to choose from")
        target = str(priced_rows.iloc[0]["player_id"])
        picks = [{"pick_no": 1, "round": 1, "roster_id": "1", "player_id": target}]
        after = dr.build_available_pool(merger, players, {target}, usable)
        contested = frozenset(k for k in after.get("_contested_key", []) if isinstance(k, tuple))
        rows = dr._team_roster_players(picks, players, "1", merger, contested)
        self.assertEqual([r["id"] for r in rows], [target],
                         "an uncontested player lost his price to the contested-key guard")

    def test_a_pool_with_no_dispute_passes_through_unchanged(self):
        pool = self._contested_pool().iloc[[2]].reset_index(drop=True)
        out = dr._drop_contested_identities(pool)
        pd.testing.assert_frame_equal(out, pool)

    def test_the_phantom_duplicate_hazard_it_was_built_for_cannot_return(self):
        """The original guard existed because two players priced off ONE vendor row put a second
        copy of one man's value at his position, moving the replacement RANK every player there
        is measured against. Nulling the shared fields removes exactly that: after this, no two
        rows carry the same vendor number, which is the property the drop was buying."""
        out = dr._drop_contested_identities(self._contested_pool())
        priced = out[out["trade_value"].notna()]
        self.assertEqual(len(priced), 1, "a vendor number is still shared by two rows")
        self.assertEqual(list(priced["player_id"]), ["3"])


# MUTATIONS -- each applied to the source, the file re-run, the named test observed to FAIL,
# then reverted:
#   1. _different_offense_position: `return candidate not in eligible` -> `return False`
#        -> OffencePositionIsUnambiguous.test_a_tight_end_does_not_match... FAILED
#   2. _different_offense_position: drop the `_position_group(candidate) != "offense"` guard
#        -> ...test_idp_is_left_alone_because_its_vendors_genuinely_disagree FAILED
#   3. _different_offense_position: drop the all-eligible-are-offence guard
#        -> ...test_a_cross_group_pair_is_left_to_the_coarse_rejection FAILED
#   4. _contradicted: delete the team-disagreement clause entirely
#        -> NoTeamIsAStatementNotAGap.test_the_unrostered_sentinel_contradicts... FAILED
#   5. _contradicted: read a falsy team as unrostered (`str(team or NO_NFL_TEAM)`), which is the
#      regression this repair replaced
#        -> ...test_an_unspecified_team_contradicts_nothing FAILED
#   5b. data_merger.NO_NFL_TEAM = "" (the sentinel made falsy)
#        -> ...test_the_sentinel_must_not_be_falsy FAILED, and 5's failure returns with it
#   6. _drop_contested_identities: revert to `pool[~keyed.isin(contested)]`
#        -> TheGuardDeclinesThePriceNotThePlayer.test_both_contested_players_keep_their_rows FAILED
#   7. _drop_contested_identities: null the vendor columns for EVERY row, not just disputed
#        -> ...test_an_uncontested_row_is_not_touched FAILED
#   8. _resolve KEY path: delete the club-disagreement rejection
#        -> TheRulesAreActuallyWIRED_INTO_resolve.test_the_key_path_rejects_a_club_disagreement FAILED
#   9. _resolve KEY path: delete the _different_offense_position call
#        -> ...test_the_key_path_rejects_an_offence_position_disagreement FAILED
#  10. _resolve KEY path: narrow that call's argument to the empty set
#        -> ...test_the_key_path_rejects_an_offence_position_disagreement FAILED
#  11. _resolve FUZZY path: bypass _contradicted (`if True:`)
#        -> ...test_an_unrostered_namesake_cannot_take_a_rostered_players_row FAILED
if __name__ == "__main__":
    unittest.main()
