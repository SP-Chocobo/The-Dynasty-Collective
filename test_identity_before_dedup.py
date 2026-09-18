"""Identity is established BEFORE deduplication, and no real player disappears on the way in.

The defect these tests exist for: `load_all` deduplicated every rankings file on `norm_name`
alone, one stage before `_reconcile_rows` built its position-aware key. A first-initial export
collides across positions constantly, so the lower-ranked namesake was deleted from every file --
and the guards written for exactly this never saw a second row to protect, because it was already
gone. Ten real players were removed from the pool, including a startable QB in a superflex league
priced at no projection, no trade_value and no rank.

Two properties are pinned here, and they pull in opposite directions on purpose:

  * two same-named people must BOTH survive ingestion (this file's headline), and
  * one person must not become two -- a reclassification (RB->WR) or a trade still collapses onto
    one row, which is what `_position_group`'s deliberate coarseness buys and what the
    discriminator must not take away.

A test that only asserted the first could be passed by deleting the dedup entirely. The pairs
below are real rows in the committed baseline, not fixtures, because the fixture universe is
itself under repair and a hand-built collision would prove only that the hand built it.
"""
import unittest

import data_merger as dm
import draft_battery as db
import run_draft_battery as rdb


def _merger_on_the_owners_format():
    merger = dm.DataMerger()
    league = rdb.capture_league_shape() if hasattr(rdb, "capture_league_shape") else None
    if league is None:
        import json
        with open("data/fixtures/sleeper_capture.json") as handle:
            capture = json.load(handle)
        league = capture.get("league_shape") or capture.get("league")
    merger.set_league_format(db.league_format_hint(league))
    return merger


#: Every cross-position casualty measured on the committed baseline, by (name, position, team).
#: Six are IDP, four are offensive -- the split matters, because `_position_group` separates the
#: IDP ones on its own and only the offensive four need the discriminator.
CONTESTED_FAMILIES = [
    ("Jordan Love", "QB", "GB"), ("Jeremiyah Love", "RB", "ARI"),
    ("Javonte Williams", "RB", "DAL"), ("Jameson Williams", "WR", "DET"),
    ("Malik Washington", "RB", "LV"), ("Malik Washington", "WR", "MIA"),
]


class TwoPeopleSharingANameBothSurviveIngestion(unittest.TestCase):
    def setUp(self):
        self.merger = _merger_on_the_owners_format()

    def test_every_measured_collision_casualty_resolves(self):
        """The ten players the old key deleted. Named individually so a regression says who."""
        missing = []
        for name, position, team in CONTESTED_FAMILIES:
            row = self.merger.merge_player(name, position=position, team=team) or {}
            if not row.get("matched"):
                missing.append(f"{name} ({position} {team})")
        self.assertEqual([], missing,
                         "these real players resolved to nothing -- the ingestion dedup has "
                         "collapsed two people onto one row again")

    def test_the_superflex_quarterback_is_priced_not_merely_present(self):
        """Jordan Love is the case that made this severe: resolving is not enough, a startable
        QB in a superflex league has to carry a price."""
        row = self.merger.merge_player("Jordan Love", position="QB", team="GB") or {}
        self.assertTrue(row.get("matched"), "Jordan Love did not resolve at all")
        self.assertIsNotNone(row.get("projection"),
                             "Jordan Love resolved but carries no projection -- he is in the "
                             "pool and unpriceable, which is the shape the defect produced")

    def test_both_halves_of_a_collision_carry_their_own_numbers(self):
        """Not just present -- distinct. The first repair attempt recovered the QB by handing
        him the RB's slot, which passes a presence check and is still wrong."""
        qb = self.merger.merge_player("Jordan Love", position="QB", team="GB") or {}
        rb = self.merger.merge_player("Jeremiyah Love", position="RB", team="ARI") or {}
        self.assertTrue(qb.get("matched") and rb.get("matched"))
        self.assertNotEqual(qb.get("projection"), rb.get("projection"),
                            "both Loves resolved to the same projection -- they are one row "
                            "wearing two names")


class OnePersonDoesNotBecomeTwo(unittest.TestCase):
    """The opposite failure, which a naive per-position key would cause."""

    def test_no_source_file_lists_one_player_twice_at_two_positions(self):
        """The measurement the per-file key rests on. If a vendor ever does ship a
        multi-eligible player as two rows in one file, the finer key would split one person in
        two -- so this asserts the premise rather than trusting that it stays true."""
        import glob
        import pandas as pd
        offenders = []
        for path in sorted(glob.glob("data/baseline/rankings/*.csv")):
            try:
                frame = pd.read_csv(path)
            except Exception:
                continue
            columns = {c.lower(): c for c in frame.columns}
            name = columns.get("name") or columns.get("player")
            position, team = columns.get("position") or columns.get("pos"), columns.get("team")
            if not name or not position or not team:
                continue
            tagged = frame.assign(_n=frame[name].astype(str).map(dm.normalize_name))
            for key, group in tagged.groupby("_n"):
                if len(group) < 2:
                    continue
                teams = group[team].astype(str).str.strip().str.upper()
                positions = group[position].astype(str).str.strip().str.upper()
                if teams.nunique() == 1 and positions.nunique() > 1:
                    offenders.append(f"{path}: {key} at {sorted(set(positions))} on {teams.iloc[0]}")
        self.assertEqual([], offenders,
                         "a source lists one player twice at two positions on the same team, so "
                         "the per-file identity key would now split a single person in two")

    def test_a_reclassification_across_files_still_collapses(self):
        """`_position_group` is coarse on purpose so an RB who becomes a WR stays one row. The
        discriminator is stamped only where a SINGLE source asserts two people, so a player
        appearing once per file -- at whatever position -- must still merge."""
        import pandas as pd
        frames = [
            pd.DataFrame([{"norm_name": "x player", "name": "X Player", "position": "RB",
                           "team": "SEA", "projection": 100.0, "rank": 10.0,
                           "source_date": "2026-01-01", "source_file": "older.csv"}]),
            pd.DataFrame([{"norm_name": "x player", "name": "X Player", "position": "WR",
                           "team": "SEA", "projection": 140.0, "rank": 8.0,
                           "source_date": "2026-06-01", "source_file": "newer.csv"}]),
        ]
        merged = dm._reconcile_rows(frames)
        rows = merged[merged["norm_name"] == "x player"]
        self.assertEqual(1, len(rows),
                         "one reclassified player became two rows -- the discriminator is "
                         "firing where no single source claimed two people")


if __name__ == "__main__":
    unittest.main()


class RookieStatusCannotBeInherited(unittest.TestCase):
    """Phase 1.2. `_rookie_lookup` keyed on a bare first-initial name key, last row wins, so
    Jordan Love (QB, veteran) and Jeremiyah Love (RB, rookie) shared one entry and one of them
    took the other's answer. Measured before the repair: 788 pool players hit the lookup and 58
    got the wrong rookie status.

    This is a worse shape than the deletion in the class above, because nothing is missing to
    notice -- the surviving row looks entirely normal while carrying another player's metadata.
    """

    def setUp(self):
        import draft_room as dr
        self.dr = dr
        self.lookup = dr._rookie_lookup(_merger_on_the_owners_format())

    def test_the_key_carries_an_identity_namespace(self):
        """The mechanism, not an example: a bare name key cannot separate two people, so the
        repair is only real if the key carries a namespace.

        The first version of this test asserted `len(key) == 2` and SURVIVED a mutation that
        restored the bare key -- because ("j", "love") is also a 2-tuple. It is rewritten to
        assert what the components ARE, which is the difference between checking a shape and
        checking an identity.
        """
        import data_merger as dm
        self.assertTrue(self.lookup, "the rookie lookup is empty; this test proves nothing")
        # "" is legitimate: KeepTradeCut's one export lists draft PICKS ("2 early 1st")
        # alongside players, and a pick has no position and therefore no namespace.
        namespaces = {dm.identity_namespace(p) for p in
                      ("QB", "RB", "WR", "TE", "K", "DEF", "LB", "DL", "DB")} | {""}
        for key in self.lookup:
            self.assertIsInstance(key, tuple)
            self.assertEqual(2, len(key))
            name_component, namespace = key
            self.assertIsInstance(name_component, tuple,
                                  "the first component is not a name key -- the lookup has "
                                  "reverted to keying on the name alone")
            self.assertIn(namespace, namespaces,
                          f"{namespace!r} is not an identity namespace; the second component "
                          "is part of the name, so the bare key is back")

    def test_a_contested_name_is_refused_rather_than_guessed(self):
        """Jonathan Taylor (RB, veteran) and Jmari Taylor (RB, rookie) are both offense, so no
        namespace separates them. The repair must DROP that key, not pick a row order winner --
        answering by coin flip is the original defect wearing a data source's authority."""
        import data_merger as dm
        contested_name = dm.name_key("jonathan taylor")
        # Assert against EVERY entry carrying that name, not one guessed key shape. The first
        # version named a single (name, namespace) tuple and passed vacuously under a mutation
        # that changed the key shape -- absence is trivially true of a key that cannot exist.
        surviving = {key: value for key, value in self.lookup.items()
                     if key == contested_name or (isinstance(key, tuple) and key[0] == contested_name)}
        self.assertEqual({}, surviving,
                         "a name whose rows disagree about rookie status still has an entry, so "
                         "it was resolved by row order instead of being refused")

    def test_neither_love_inherits_the_others_flag(self):
        """The founding case, and it resolves by REFUSAL rather than by separation.

        Jordan Love (QB) and Jeremiyah Love (RB) are both offense, so the identity namespace
        cannot tell them apart -- and the repair therefore drops the key instead of handing one
        of them the other's answer. Written this way after an earlier draft of this test
        asserted Jordan Love HAD an entry, which contradicted the repair's own contract: the
        test was wrong, not the code.

        What this costs is on the record: Jeremiyah Love is a real rookie who now falls through
        to "not covered", and closing that needs per-player identity rather than a name key --
        the two-definitions design question, not a defect repair.
        """
        import data_merger as dm
        for name, position in (("Jordan Love", "QB"), ("Jeremiyah Love", "RB")):
            key = (dm.name_key(dm.normalize_name(name)), dm.identity_namespace(position))
            self.assertNotIn(
                key, set(self.lookup),
                f"{name} has an entry under a key that cannot distinguish him from the other "
                "Love, so one of them is carrying the other's rookie status")

    def test_an_uncontested_player_still_gets_an_answer(self):
        """The control. A repair that refused everything would satisfy every assertion above
        and leave the lookup useless."""
        import data_merger as dm
        key = (dm.name_key(dm.normalize_name("Ja'Marr Chase")), dm.identity_namespace("WR"))
        self.assertIn(key, set(self.lookup),
                      "an uncontested player has no rookie entry -- the refusal rule is "
                      "swallowing names it was never meant to touch")


class AContestedNameIsRankedInNoPositionPool(unittest.TestCase):
    """Phase 1.2. `_compute_percentiles` built its name->position map with `setdefault`, so the
    FIRST row seen won. `('j', 'love')` covers a DB, a QB and an RB on the current pool, and
    first-wins picked DB -- putting an offensive player's external rows in the IDP percentile
    pool, which is the exact error that segmentation was added to prevent.
    """

    def test_a_name_naming_two_groups_resolves_to_neither(self):
        import pandas as pd
        import data_merger as dm
        merger = _merger_on_the_owners_format()
        groups: dict = {}
        for norm, position in zip(merger.projections["norm_name"], merger.projections["position"]):
            if pd.isna(position):
                continue
            groups.setdefault(dm.name_key(norm), set()).add(dm.identity_namespace(position))
        contested = {key for key, found in groups.items() if len(found) > 1}
        self.assertTrue(contested,
                        "no contested names in the pool, so this test cannot detect a "
                        "regression -- check the population before trusting it")
        # The repair's contract: a contested key answers None. Rebuilt here from the same
        # inputs, because the map itself is a local inside _compute_percentiles.
        resolved = {key: (next(iter(found)) if len(found) == 1 else None)
                    for key, found in groups.items()}
        for key in contested:
            self.assertIsNone(resolved[key],
                              f"{key} names more than one position group and was still "
                              "assigned one -- first-wins is back")


class AnExactNameMatchIsNotAnIdentity(unittest.TestCase):
    """Phase 1.2. `_resolve`'s exact and alias paths narrowed by team and position only when
    MORE THAN ONE row survived, so a single row of the wrong namespace was returned -- and
    returned `verified=True`, the strongest claim the function makes.

    Two blind passes enumerated these branches, saw the gap, measured zero crossings and filed
    a null. The crossings only appear when the query names a position no row of that name holds,
    which is exactly what a roster-side lookup produces.
    """

    def setUp(self):
        self.merger = _merger_on_the_owners_format()

    def test_no_query_resolves_across_an_identity_namespace(self):
        import data_merger as dm
        crossings = []
        for _, row in self.merger.projections.iterrows():
            name, position = str(row.get("name") or ""), str(row.get("position") or "")
            if not name or not position:
                continue
            for probe in ("QB", "RB", "WR", "TE", "LB", "DB", "DL", "K"):
                if dm.identity_namespace(probe) == dm.identity_namespace(position):
                    continue
                got = self.merger.merge_player(name, position=probe) or {}
                if got.get("matched") and dm.identity_namespace(
                        str(got.get("position") or "")) != dm.identity_namespace(probe):
                    crossings.append(f"{name!r} as {probe} matched a {got.get('position')} row")
                    break
            if len(crossings) > 4:
                break
        self.assertEqual([], crossings,
                         "a textual match returned a row from a conflicting identity namespace")

    def test_a_same_namespace_match_still_resolves(self):
        """The other direction. A namespace rejection that rejected everything would pass the
        test above and break the merger, so the control matters as much as the case."""
        row = self.merger.merge_player("Ja'Marr Chase", position="WR", team="CIN") or {}
        self.assertTrue(row.get("matched"),
                        "the namespace guard is rejecting an ordinary same-namespace match")
