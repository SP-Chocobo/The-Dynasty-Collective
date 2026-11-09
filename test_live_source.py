"""`#356` / `#357` — the live bridge's absence vocabulary, and the server's read-only property.

ONE FILE FOR BOTH BECAUSE THE SERVER IS THIN AND THE BRIDGE IS THE SUBSTANCE. `server.py` reads a
snapshot, calls `live_source`, calls a builder, and returns the string. The only properties of it
worth pinning are that it writes nothing and that a failed read reaches the page LOUDLY; both
belong beside the vocabulary that decides the second one.

THE DEFECT THESE EXIST FOR, which no fixture ever required. `#187` makes an absence render as an
em dash carrying its reason, and that protects a reader from an invented number while giving them
NOTHING against a field that should have arrived and did not. A wrong Sleeper key yields
`league.name == None`, the page prints a tidy labelled em dash, and it is indistinguishable from
the contract working. The owner tests this against their own league; I cannot see it run. So the
distinction between "this source has no such field" and "this source owes this field and failed to
deliver it" is the one thing that makes a wiring error visible, and it is what is tested hardest
here.

These tests build their own tiny players_db rather than the real 6,594-row capture-backed one.
That is deliberate: the universe's correctness is `#201`'s subject and has its own tests, while
what is under test here is the ROW SHAPE and the STATE VOCABULARY, which a three-player db
exercises exactly as well and in milliseconds.
"""
from __future__ import annotations

import json
import pathlib
import tempfile
import unittest

import front_claims as fc
import live_source as ls

ROOT = pathlib.Path(__file__).resolve().parent

PLAYERS = {
    "1": {"full_name": "A Quarterback", "position": "QB", "fantasy_positions": ["QB"],
          "team": "KC"},
    "2": {"full_name": "A Runner", "position": "RB", "fantasy_positions": ["RB", "WR"],
          "team": "SF"},
    "3": {"full_name": "A Receiver", "position": "WR", "fantasy_positions": ["WR"],
          "team": "BUF"},
}
BYES = {"KC": 10, "SF": 9, "BUF": 7}
POSITIONS = ["QB", "RB", "WR", "TE", "K"]


def snapshot(**over) -> dict:
    """A snapshot in the shape `sleeper_client.sync_league` writes.

    Copied from the PRODUCER, not invented: `sync_league` builds
    `{synced_at, league, rosters, users, traded_picks, nfl_state, ...}`, and a hand-built input
    in the wrong shape is how a probe silently measures something else (`#222`).
    """
    snap = {
        "synced_at": 1762800000.0,
        "league": {"league_id": "118", "name": "The Dynasty Collective",
                   "roster_positions": list(POSITIONS)},
        "rosters": [{"owner_id": "u1", "players": ["1", "2", "3"], "starters": ["1", "2", "3"],
                     "settings": {"wins": 6, "losses": 3}}],
        "users": [{"user_id": "u1", "display_name": "SP-Chocobo"}],
        "nfl_state": {"season": "2026", "week": 10, "season_type": "regular"},
    }
    snap.update(over)
    return snap


class AFailedReadIsNotAnAbsence(unittest.TestCase):
    """THE CENTRAL CONTRACT. The same missing field means different things by source."""

    def test_a_snapshot_missing_its_league_name_is_a_READ_FAILURE(self):
        """Fails on any design that only asks "is it None?" -- which is every prior renderer."""
        snap = snapshot()
        del snap["league"]["name"]
        _fx, report = ls.from_snapshot(snap, PLAYERS, BYES, owner_id="u1")
        field = report.by_name("league_name")
        self.assertEqual(field.state, ls.READ_FAILED,
                         "a snapshot owes a league name; its absence is a defect in the read")
        self.assertTrue(field.loud, "a failed read must not be drawn as a quiet em dash")
        self.assertIn("did not arrive", field.why)

    def test_the_same_field_missing_from_a_FIXTURE_is_structural(self):
        """The identical value, the opposite verdict -- which is why the source kind is data."""
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "f.json"
            path.write_text(json.dumps({"roster": [{"id": "1"}],
                                        "league": {"roster_positions": POSITIONS}}))
            _fx, report = ls.from_fixture(path)
        field = report.by_name("league_name")
        self.assertEqual(field.state, ls.STRUCTURAL)
        self.assertFalse(field.loud)

    def test_a_wired_snapshot_reports_no_failures_at_all(self):
        _fx, report = ls.from_snapshot(snapshot(), PLAYERS, BYES, owner_id="u1")
        self.assertEqual(report.failures, (), f"unexpected failures: {report.failures}")
        self.assertEqual(report.verdict, "every expected field arrived")

    def test_the_verdict_counts_the_failures_rather_than_describing_them(self):
        snap = snapshot()
        del snap["league"]["name"]
        snap["nfl_state"] = {}
        _fx, report = ls.from_snapshot(snap, PLAYERS, BYES, owner_id="u1")
        self.assertEqual(len(report.failures), 2)
        self.assertIn("WIRED WRONG", report.verdict)

    def test_every_expected_field_is_named_in_the_source_table(self):
        """The table is the only thing that can tell the two states apart, so it must be whole.

        A field the bridge reports but no source claims to owe would silently be structural
        forever -- the absence that can never be a bug.
        """
        _fx, report = ls.from_snapshot(snapshot(), PLAYERS, BYES, owner_id="u1")
        reported = {f.name for f in report.fields}
        self.assertTrue(ls.EXPECTS["snapshot"] <= reported,
                        f"owed but never reported: {ls.EXPECTS['snapshot'] - reported}")


class TheRowShapeTheSolversNeed(unittest.TestCase):

    def test_eligible_is_a_SET_in_memory_and_never_its_repr(self):
        """`#351`: the capture's `default=str` turns a set into `"{'RB'}"`, and `slot_coverage`
        does `player["eligible"] & slot["eligible"]`, which raises TypeError on a str."""
        rows = ls.roster_rows(["1", "2"], PLAYERS, BYES)
        for row in rows:
            self.assertIsInstance(row["eligible"], set, f"{row['name']}: eligible is not a set")
        self.assertEqual(rows[1]["eligible"], {"RB", "WR"}, "dual eligibility was flattened")

    def test_value_is_a_number_and_priced_travels_beside_it(self):
        """`#346` / `#190`: unpriced is not worth zero, and the solvers negate `value`."""
        for row in ls.roster_rows(["1", "2", "3"], PLAYERS, BYES):
            self.assertIsInstance(row["value"], float)
            self.assertIs(row["priced"], False, "this function prices nothing and must say so")

    def test_an_unknown_player_id_still_yields_a_row(self):
        """A roster naming a player the universe does not have must not crash the page."""
        rows = ls.roster_rows(["nope"], PLAYERS, BYES)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["eligible"], set())
        self.assertIsNone(rows[0]["bye"])

    def test_a_bye_week_is_none_rather_than_zero_when_the_team_is_unknown(self):
        rows = ls.roster_rows(["1"], PLAYERS, {})
        self.assertIsNone(rows[0]["bye"], "an unknown bye must be None, never 0 (`#187`)")


class ByeProfileRefusesAnUnpricedRoster(unittest.TestCase):
    """`#346` arriving through a different door, and the refusal is in the code."""

    def test_an_unpriced_roster_gets_no_profile_and_a_reason(self):
        rows = ls.roster_rows(["1", "2", "3"], PLAYERS, BYES)
        profile, why = ls.bye_profile_from(rows, POSITIONS)
        self.assertIsNone(profile, "a profile was built from unpriced rows")
        self.assertIn("unpriced", why)
        self.assertIn("0.0", why, "the reason must name the number it refuses to report")

    def test_a_priced_roster_does_get_a_profile(self):
        """The refusal must not be unconditional, or it is not a guard but a stub."""
        rows = [dict(r, value=10.0, priced=True)
                for r in ls.roster_rows(["1", "2", "3"], PLAYERS, BYES)]
        profile, why = ls.bye_profile_from(rows, POSITIONS)
        self.assertIsNotNone(profile, f"a fully priced roster was refused: {why}")
        self.assertEqual(why, "")
        self.assertIsNotNone(profile["worst_week"])
        self.assertIsNotNone(profile["worst_week_loss"])


class TheProducerKeepsTheAbsenceContract(unittest.TestCase):
    """The defect this bridge SHIPPED in its first draft, caught by running it.

    `checks_run`'s docstring states the grammar it depends on: "`[]` is a measured empty result
    -- holes were counted, there were none -- while a missing key or `None` never ran. A caller
    that hands `[]` for something it did not measure has broken the absence contract AT THE
    PRODUCER." The first draft wrote `"thin_positions": []`, and the depth check duly reported
    CLEAN on a check that never ran -- so a league with no structural holes would have rendered
    "nothing open" with two of three checks never performed.
    """

    def test_an_uncomputed_claim_is_OMITTED_from_the_fixture_not_emptied(self):
        fx, _report = ls.from_snapshot(snapshot(), PLAYERS, BYES, owner_id="u1")
        self.assertNotIn("thin_positions", fx,
                         "thin_positions was emptied rather than omitted, which reads to "
                         "`checks_run` as a check that ran and found nothing")
        self.assertNotIn("bye_profile", fx,
                         "bye_profile was supplied for an unpriced roster")

    def test_the_page_cannot_claim_all_clean_when_two_checks_never_ran(self):
        """THE CONSEQUENCE, asserted end to end rather than inferred from the key's absence."""
        fx, _report = ls.from_snapshot(snapshot(), PLAYERS, BYES, owner_id="u1")
        summary = fc.checks_summary(fc.compose(fx).get("checks"))
        self.assertEqual(summary["ran"], 1, f"expected one runnable check, got {summary}")
        self.assertEqual(sorted(summary["absent"]), ["byes", "depth"])
        self.assertFalse(summary["all_clean"],
                         "a page would have said 'all clean' on one of three checks")

    def test_a_measured_empty_hole_list_IS_a_list(self):
        """The other half of the grammar: holes were counted, so `[]` is the honest answer."""
        fx, _report = ls.from_snapshot(snapshot(), PLAYERS, BYES, owner_id="u1")
        self.assertIsInstance(fx["structural_holes"], list)
        summary = fc.checks_summary(fc.compose(fx).get("checks"))
        self.assertIn("holes", summary["clean"] + summary["fired"],
                      "the holes check must report as having RUN")


class TheServerWritesNothing(unittest.TestCase):
    """`#354`: one process is an architectural constraint that protects data integrity.

    `app.py` persists to local files with no locking and no notion of who is asking, so the
    server's value is that it is a pure READER beside that single writer. Asserted against the
    source rather than described in a docstring, because a docstring cannot fail.
    """

    WRITE_IDIOMS = ("write_text(", "json.dump(", "open(", ".write(", "os.replace",
                    "store_io.write", "store_io.mutate", "mkdir(", "unlink(")

    def test_no_write_idiom_appears_in_the_server(self):
        source = (ROOT / "server.py").read_text()
        offenders = []
        for lineno, line in enumerate(source.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"'):
                continue
            for idiom in self.WRITE_IDIOMS:
                if idiom in stripped:
                    offenders.append(f"server.py:{lineno}: {idiom}")
        self.assertEqual(offenders, [],
                         "the read-only server writes. That is the one property that makes it "
                         "safe beside app.py's single writer (`#354`)")

    def test_the_detector_would_catch_a_write(self):
        """Non-vacuity. The scan above passes on a tree where nothing writes for any reason,
        including a broken scan, which is this session's recurring defect (`#352`)."""
        hits = [i for i in self.WRITE_IDIOMS if i in 'path.write_text(json.dumps(x))']
        self.assertTrue(hits, "the write detector recognises nothing")

    def test_the_server_binds_loopback_only(self):
        """Owner's ruling, and verified empirically too: HTTP 000 on the container's own
        192.0.2.2:8765 while 127.0.0.1:8765 served 200."""
        import server
        self.assertEqual(server.HOST, "127.0.0.1")

    def test_a_failed_read_reaches_the_page_as_a_banner_not_an_em_dash(self):
        import server
        snap = snapshot()
        del snap["league"]["name"]
        fx, report = ls.from_snapshot(snap, PLAYERS, BYES, owner_id="u1")
        page = server._render(fx, report).body.decode()
        self.assertIn("WIRED WRONG", page)
        self.assertIn("league_name", page)
        self.assertIn("NOT absences in your data", page)

    def test_a_clean_read_gets_no_banner(self):
        import server
        fx, report = ls.from_snapshot(snapshot(), PLAYERS, BYES, owner_id="u1")
        page = server._render(fx, report).body.decode()
        self.assertNotIn("WIRED WRONG", page)


if __name__ == "__main__":
    unittest.main()
