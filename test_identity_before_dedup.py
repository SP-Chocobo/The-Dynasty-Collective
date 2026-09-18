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
