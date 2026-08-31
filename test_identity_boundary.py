"""Identity boundary invariants (repair boundaries R1-R3).

The failure class, not the individual cases: a resolution path without a rejection rule can
return a DIFFERENT REAL PERSON's row, and every field of that row -- projection, trade value,
3-year outlook -- then becomes that player's valuation input. Measured before the repair: on
the team-bearing external probe set, EVERY fuzzy match that resolved was cross-person (9 of 9),
so the path had no precision at all in the direction the valuation pool uses it.

Three invariants are asserted here:
  R1  a fuzzy candidate contradicted by a known team or a known position family is rejected,
      not returned; unknown on either side is not evidence of a mismatch and does not reject
  R2  ambiguity is a property of the RESOLUTION and is returned with it, so no consumer has to
      re-derive it (app.py's trade calculator did, which is why the gap was only closed there)
  R3  resolution into the valuation pool is injective -- one canonical row backs at most one
      pool row, because a duplicate is a phantom player that shifts a positional replacement
      level, a league-level quantity every player at that position is measured against
"""
import unittest

import pandas as pd

import data_merger as dm
import draft_room as dr


class PositionFamilyTests(unittest.TestCase):
    """position_family is the COMPARISON key (is this the same kind of player?), deliberately
    finer than _position_group, which is the dedup IDENTITY namespace and lumps all offensive
    skill positions together on purpose. Conflating the two would either let a WR match an RB
    or stop a Sleeper "S" from matching a Draft Sharks "DB"."""

    def test_vendor_synonyms_for_one_role_collapse(self):
        for synonym, family in (("S", "DB"), ("CB", "DB"), ("DE", "DL"), ("EDGE", "DL"),
                                ("OLB", "LB"), ("DST", "DEF"), ("PK", "K")):
            self.assertEqual(dm.position_family(synonym), family, synonym)

    def test_distinct_offensive_positions_stay_distinct(self):
        families = {dm.position_family(p) for p in ("QB", "RB", "WR", "TE")}
        self.assertEqual(len(families), 4)

    def test_group_would_not_separate_them_which_is_why_this_exists(self):
        groups = {dm._position_group(p) for p in ("QB", "RB", "WR", "TE")}
        self.assertEqual(len(groups), 1)

    def test_unknown_is_none_not_a_family(self):
        for absent in (None, "", float("nan")):
            self.assertIsNone(dm.position_family(absent))


class FuzzyPathRejectsADifferentPersonTests(unittest.TestCase):
    """The nine cross-person fuzzy matches measured on the real committed baseline. Three are
    caught by team (same position, different club), six by position family -- both rules are
    load-bearing and neither alone closes the class."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    CROSS_PERSON = [
        ("Bo Melton", "WR", "GB", "M Melton"),
        ("CJ Daniels", "WR", "LAR", "J Daniels"),
        ("James Mitchell", "TE", "CAR", "A Mitchell"),
        ("Jaret Patterson", "RB", "LAC", "R Patterson"),
        ("Noah Brown", "WR", "LV", "A Brown"),
        ("Skyy Moore", "WR", "GB", "K Moore"),
        ("Tahj Brooks", "RB", "CIN", "J Brooks"),
        ("Van Jefferson", "WR", "WAS", "J Jefferson"),
        ("Xavier Hutchinson", "WR", "HOU", "A Hutchinson"),
    ]

    def test_none_of_them_resolves_to_the_other_persons_row(self):
        """The contract: if one of these names resolves at all, it must not resolve to the
        other person. The MEASURED state is stronger -- after the R1 repair all nine are
        declined outright -- and both are asserted, because an assertion-reachability trace
        over the whole suite found the conditional body below had never executed once. A
        conditional assertion whose condition is always false is not a passing test."""
        resolved = []
        for name, position, team, stolen_from in self.CROSS_PERSON:
            with self.subTest(name):
                row = self.merger._find_match(name, position=position, team=team)
                if row is not None:
                    resolved.append(name)
                    self.assertNotEqual(str(row["name"]), stolen_from)
        self.assertEqual(resolved, [],
                         "these nine were all declined when the rejection rule landed; one "
                         "resolving again is a real change in matching behaviour, even if it "
                         "resolved to the right person")

    def test_and_therefore_none_of_them_inherits_a_projection(self):
        """Same pair of claims, one layer up: the contract is that a match must at least share
        a position family, and the measured state is that none of them matches at all."""
        matched = []
        for name, position, team, _ in self.CROSS_PERSON:
            with self.subTest(name):
                match = self.merger.merge_player(name, position=position, team=team)
                if match.get("matched"):
                    matched.append(name)
                    self.assertEqual(dm.position_family(match.get("position")),
                                     dm.position_family(position))
        self.assertEqual(matched, [],
                         "one of the nine measured cross-person cases matched again")


class FuzzyPathRejectionRuleTests(unittest.TestCase):
    """The rule itself, on a hand-built table -- so it is asserted independently of whichever
    players happen to be in the committed baseline this week."""

    def _merger(self, rows):
        merger = dm.DataMerger.__new__(dm.DataMerger)
        merger.match_cutoff = 0.82
        merger.aliases = {}
        df = pd.DataFrame(rows)
        df["norm_name"] = df["name"].map(dm.normalize_name)
        df["_name_key"] = df["norm_name"].map(dm.name_key)
        merger.projections = df
        return merger

    def test_a_known_position_family_mismatch_rejects(self):
        merger = self._merger([{"name": "R Patterson", "position": "K", "team": "MIA"}])
        self.assertIsNone(merger._find_match("Jaret Patterson", position="RB", team="MIA"))

    def test_a_known_team_mismatch_rejects_even_at_the_same_position(self):
        merger = self._merger([{"name": "J Jefferson", "position": "WR", "team": "MIN"}])
        self.assertIsNone(merger._find_match("Van Jefferson", position="WR", team="WAS"))

    def test_agreement_on_both_still_resolves(self):
        merger = self._merger([{"name": "J Jefferson", "position": "WR", "team": "MIN"}])
        row = merger._find_match("J Jeffersonn", position="WR", team="MIN")
        self.assertIsNotNone(row)

    def test_unknown_on_either_side_is_not_evidence_of_a_mismatch(self):
        # A free-text caller (the trade calculator) has neither. Absence must not reject --
        # that would be inventing a contradiction, the mirror of inventing a match.
        merger = self._merger([{"name": "J Jefferson", "position": "WR", "team": "MIN"}])
        self.assertIsNotNone(merger._find_match("J Jeffersonn"))
        self.assertIsNotNone(merger._find_match("J Jeffersonn", position="WR"))

    def test_a_vendor_synonym_is_not_a_mismatch(self):
        # Sleeper says "S", Draft Sharks says "DB". Same role, same person -- position_family
        # must not turn a vocabulary difference into a rejection. ("A Winfeild" is a
        # misspelling that clears the 0.82 cutoff, so this actually exercises the fuzzy path;
        # the full first name does not, which is the point of using the abbreviated form.)
        merger = self._merger([{"name": "A Winfield", "position": "DB", "team": "TB"}])
        self.assertIsNotNone(merger._find_match("A Winfeild", position="S", team="TB"))

    def test_it_walks_past_a_contradicted_candidate_to_a_valid_one(self):
        # Rejection must not mean "give up at the first candidate". difflib ranks "K Moore"
        # ahead of "K Moorse" here; the first is contradicted on position, so the second --
        # which agrees on everything known -- is the right answer, not None.
        merger = self._merger([
            {"name": "K Moore", "position": "DB", "team": "GB"},
            {"name": "K Moorse", "position": "WR", "team": "GB"},
        ])
        row = merger._find_match("K Mooree", position="WR", team="GB")
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "K Moorse")


class ResolutionMetadataTests(unittest.TestCase):
    """R2. Before this, merge_player returned {"matched": bool, ...} and nothing else, so a
    silent first-candidate pick was indistinguishable from an unambiguous exact hit at all 28
    call sites. app.py's trade calculator recomputed name_key itself to close that gap for one
    caller; ambiguity belongs to the producer."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    def test_an_exact_hit_reports_its_path_and_is_verified(self):
        row = self.merger.projections.iloc[0]
        match = self.merger.merge_player(str(row["name"]), position=row.get("position"))
        self.assertTrue(match.get("matched"))
        self.assertEqual(match.get("match_path"), "exact")
        self.assertTrue(match.get("match_verified"))

    def test_a_miss_reports_no_path_and_no_candidates(self):
        match = self.merger.merge_player("Zzzz Nonexistent", position="WR", team="GB")
        self.assertFalse(match.get("matched"))
        self.assertIsNone(match.get("match_path"))
        self.assertEqual(match.get("match_candidates"), 0)

    def test_a_shared_key_reports_more_than_one_candidate(self):
        # The real "Jaylen Allen resolved to Josh Allen's value" case, generalized: two rows
        # sharing a name_key must be reported as two, whichever one wins.
        keys = self.merger.projections["_name_key"].value_counts()
        shared = [k for k, n in keys.items() if n > 1]
        self.assertTrue(shared, "baseline should still contain a shared name_key to assert on")
        rows = self.merger.projections[self.merger.projections["_name_key"] == shared[0]]
        first, initial = rows.iloc[0], shared[0]
        probe = f"{initial[0].upper()}zzz {initial[1]}"
        match = self.merger.merge_player(probe)
        if match.get("matched"):
            self.assertGreaterEqual(match.get("match_candidates", 0), 2)
            self.assertFalse(match.get("match_verified"))

    def test_every_matched_result_carries_all_three_fields(self):
        for _, row in self.merger.projections.head(25).iterrows():
            match = self.merger.merge_player(str(row["name"]), position=row.get("position"))
            if not match.get("matched"):
                continue
            for field in ("match_path", "match_candidates", "match_verified"):
                self.assertIn(field, match)


class PoolInjectivityTests(unittest.TestCase):
    """R3. build_available_pool emits one row per Sleeper player_id and used to place no
    constraint on the canonical row behind it, so N players resolving to one row produced N
    identical priced rows. Each duplicate is a phantom copy of a real player's points at that
    position, which moves that position's replacement rank -- measured at +1 to +8 real points,
    cutting top-of-position VOR by 2-5%. The error does not stay in the row it started in."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    def _db_from(self, rows):
        db = {}
        for i, (name, position, team) in enumerate(rows, start=1):
            parts = name.split()
            db[str(i)] = {"first_name": parts[0], "last_name": " ".join(parts[1:]) or parts[0],
                          "position": position, "fantasy_positions": [position], "team": team}
        return db

    def test_two_players_never_share_one_canonical_row_in_the_pool(self):
        canonical = self.merger.projections
        priced = canonical[canonical["projection"].notna()]
        self.assertFalse(priced.empty)
        first = priced.iloc[0]
        name = str(first["name"])
        # the real row, plus a made-up player whose name fuzzes onto it
        db = self._db_from([(name, first["position"], first.get("team")),
                            (f"Zzz {name.split()[-1]}", first["position"], first.get("team"))])
        pool = dr.build_available_pool(self.merger, db, set(), {"QB", "RB", "WR", "TE", "K", "DEF"})
        if "_canonical_key" in pool.columns:
            keys = [k for k in pool["_canonical_key"] if k is not None]
            self.assertEqual(len(keys), len(set(keys)))

    def test_the_real_baseline_pool_is_injective(self):
        canonical = self.merger.projections
        rows = [(str(r["name"]), r["position"], r.get("team"))
                for _, r in canonical.iterrows()
                if r["position"] in ("QB", "RB", "WR", "TE", "K", "DEF")]
        pool = dr.build_available_pool(self.merger, self._db_from(rows), set(),
                                       {"QB", "RB", "WR", "TE", "K", "DEF"})
        self.assertIn("_canonical_key", pool.columns)
        keys = [k for k in pool["_canonical_key"] if k is not None]
        self.assertEqual(len(keys), len(set(keys)),
                         "a canonical row backs more than one pool row")


class ManualAliasBranchContractTests(unittest.TestCase):
    """CHARACTERIZATION of a confirmed contract violation, not approval of it.
    Recorded by the architecture audit, ARCHITECTURE_AUDIT.md section 13.3.

    _resolve's own docstring states: "`verified` is True only when exactly one row survived, so
    a caller can tell 'this is the player' from 'this is the first of several that fit'." The
    R1-R3 repair made the automatic paths honour that. The MANUAL ALIAS branch was not repaired
    alongside them -- it returns `..., len(exact), True`, with True hard-coded regardless of how
    many rows survived.

    The alias map is written from a UI text input (app.py's "Save Alias") with no validation of
    the target, so this is the one client-reachable path into canonical identity resolution.

    These tests are the evidence, executable. If one FAILS, the branch has been repaired --
    delete the failing test and update ARCHITECTURE_AUDIT.md 13.3 in the same change."""

    def _merger(self):
        merger = dm.DataMerger.__new__(dm.DataMerger)   # no disk load
        merger.match_cutoff = 0.88
        frame = pd.DataFrame([
            {"name": "J Chase", "team": "CIN", "position": "WR", "trade_value": 100.0},
            {"name": "J Chase", "team": "NYJ", "position": "WR", "trade_value": 12.0},
            {"name": "P Nacua", "team": "LAR", "position": "WR", "trade_value": 94.0},
        ])
        frame["norm_name"] = frame["name"].map(dm.normalize_name)
        merger.projections = frame
        merger.aliases = {}
        return merger

    def test_a_nonexistent_alias_target_falls_through_rather_than_binding_wrongly(self):
        """The reassuring half, and worth pinning: a typo does NOT silently rebind a player."""
        merger = self._merger()
        merger.aliases = {"Some Player": "Nobody At All"}
        row, path, candidates, verified = merger._resolve("Some Player", position="WR", team="CIN")
        self.assertIsNone(row)
        self.assertIsNone(path)
        self.assertEqual(candidates, 0)
        self.assertFalse(verified)

    def test_DEFECT_an_ambiguous_alias_is_reported_as_verified(self):
        merger = self._merger()
        merger.aliases = {"Ambiguous Guy": "J Chase"}
        row, path, candidates, verified = merger._resolve("Ambiguous Guy")
        self.assertEqual(path, "alias")
        self.assertEqual(candidates, 2, "fixture must present a genuine collision")
        self.assertTrue(
            verified,
            "the alias branch now reports an ambiguous match as unverified -- the contract "
            "violation recorded in ARCHITECTURE_AUDIT.md 13.3 has been repaired; delete this "
            "test and update that section",
        )
        # And the arbitrary winner carries a materially different valuation.
        self.assertEqual(row["trade_value"], 100.0)

    def test_DEFECT_a_team_that_matches_nothing_does_not_prevent_the_verified_claim(self):
        merger = self._merger()
        merger.aliases = {"Ambiguous Guy": "J Chase"}
        row, path, candidates, verified = merger._resolve("Ambiguous Guy", team="DEN")
        self.assertEqual(candidates, 2)
        self.assertTrue(verified, "see the note on the test above")

    def test_the_automatic_path_gets_this_right_on_identical_data(self):
        """The control that makes the two tests above a DEFECT rather than a design choice:
        the repaired path, on the same ambiguous name, reports verified=False."""
        merger = self._merger()
        row, path, candidates, verified = merger._resolve("J Chase")
        self.assertEqual(candidates, 2)
        self.assertFalse(verified,
                         "the automatic path must still honour the contract the alias branch "
                         "breaks -- if this fails, the regression is on the repaired side")

    def test_the_collision_surface_is_real_in_the_committed_data(self):
        """Reach, so this is not filed as a purely theoretical inconsistency."""
        merger = dm.DataMerger()
        counts = merger.projections["norm_name"].dropna().value_counts()
        colliding = counts[counts > 1]
        self.assertGreater(
            len(colliding), 0,
            "no colliding normalized names remain in the projections table -- the alias "
            "ambiguity would be unreachable; re-measure ARCHITECTURE_AUDIT.md 13.3's reach",
        )


if __name__ == "__main__":
    unittest.main()


class KeyPathIdentityNamespaceTests(unittest.TestCase):
    """The key path narrows on team, but two same-team players can still share a name_key --
    confirmed live on the real baseline after the fuzzy repair landed: a WR resolved onto a DB
    at the same club and first initial, which no team check can see. _dedup_by_name_and_position
    already calls rows in different _position_group buckets two different people, so a
    resolution that crosses that boundary contradicts the merger's own identity model.

    Deliberately the COARSE group. Vendors disagree on whether an edge rusher is LB or DL and
    both are `idp`; 20 real matches on the committed baseline depend on that staying a match."""

    def _merger(self, rows):
        merger = dm.DataMerger.__new__(dm.DataMerger)
        merger.match_cutoff = 0.82
        merger.aliases = {}
        df = pd.DataFrame(rows)
        df["norm_name"] = df["name"].map(dm.normalize_name)
        df["_name_key"] = df["norm_name"].map(dm.name_key)
        merger.projections = df
        return merger

    def test_offense_does_not_resolve_onto_idp_even_on_the_same_team(self):
        merger = self._merger([{"name": "J Horn", "position": "DB", "team": "CAR"}])
        self.assertIsNone(merger._find_match("Jimmy Horn Jr.", position="WR", team="CAR"))

    def test_the_idp_vocabulary_split_between_vendors_is_still_a_match(self):
        merger = self._merger([{"name": "A Highsmith", "position": "DL", "team": "PIT"}])
        self.assertIsNotNone(merger._find_match("Alex Highsmith", position="LB", team="PIT"))

    def test_a_kicker_does_not_resolve_onto_an_offensive_skill_row(self):
        merger = self._merger([{"name": "J Sanders", "position": "TE", "team": "CAR"}])
        self.assertIsNone(merger._find_match("Jason Sanders", position="K", team="CAR"))
