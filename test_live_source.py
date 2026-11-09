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
R7 = ROOT / "ui_explore" / "round7"

PLAYERS = {
    "1": {"full_name": "A Quarterback", "position": "QB", "fantasy_positions": ["QB"],
          "team": "KC"},
    "2": {"full_name": "A Runner", "position": "RB", "fantasy_positions": ["RB", "WR"],
          "team": "SF"},
    "3": {"full_name": "A Receiver", "position": "WR", "fantasy_positions": ["WR"],
          "team": "BUF"},
    # NO `full_name`. This row is what makes the name test non-vacuous: `player_name` falls back
    # to first+last BEFORE the id, and an inline `full_name or id` spelling yields the raw
    # Sleeper id here -- a string `merge_player` can never match, so the player silently prices
    # as unpriced. Measured: four such rows in a 15-player roster.
    "4": {"first_name": "No", "last_name": "Fullname", "position": "TE",
          "fantasy_positions": ["TE"], "team": "KC"},
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


class TheServerHasExactlyOneWritePath(unittest.TestCase):
    """`#361`. THIS TEST REPLACES ONE THAT WAS TRUE AND IS NOT ANY MORE.

    It used to assert the server performed NO writes at all, and that was correct while the
    server only read snapshots `app.py` had synced. Wiring the sync buttons made it false. The
    wrong response would have been to delete the test, or to loosen it until it could not fail;
    the honest one is to replace a property that stopped holding with the narrower one that
    still does, and to say in the open that it narrowed:

        BEFORE  the server performs no writes at all.
        AFTER   the server's ONLY write is `sleeper_client.sync_league`, which persists through
                `store_io.replace_atomically`. No handler writes directly, and nothing writes
                outside `data/sleeper_snapshots/`.

    That is the property that actually protects a reader. `_write_snapshot`'s own comment is the
    argument: a torn read of `_latest.json` "looks exactly like a league that has never been
    synced", so the atomic replace is what stops a page rendering mid-sync from seeing one.
    """

    WRITE_IDIOMS = ("write_text(", "json.dump(", "open(", ".write(", "os.replace",
                    "store_io.write", "store_io.mutate", "mkdir(", "unlink(")

    def test_no_handler_writes_directly(self):
        """The scan still runs; what changed is that `sync_league` is the one allowed call."""
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
                         "a handler writes directly. The only write may be sync_league's, "
                         "which is atomic (`#361`)")

    def test_the_detector_would_catch_a_write(self):
        """Non-vacuity. The scan passes on a tree where nothing writes for any reason,
        including a broken scan, which is this session's recurring defect (`#352`)."""
        hits = [i for i in self.WRITE_IDIOMS if i in 'path.write_text(json.dumps(x))']
        self.assertTrue(hits, "the write detector recognises nothing")

    def test_the_one_write_is_sync_league_and_it_is_atomic(self):
        """Pins BOTH halves: that the route delegates, and that the delegate replaces atomically.

        Asserting only the first would let the write stop being atomic without failing; asserting
        only the second would let a handler grow its own write beside it.
        """
        import inspect
        import sleeper_client
        import server
        self.assertIn("sync_league", inspect.getsource(server.add),
                      "the add route does not delegate to sleeper_client.sync_league")
        self.assertIn("replace_atomically", inspect.getsource(sleeper_client.SleeperClient
                                                              ._write_snapshot),
                      "the snapshot write is no longer atomic, so a render can see a torn file")

    def test_the_server_implements_no_second_sync(self):
        """`#126`: one home. A route that re-implemented the sync would be a second source of
        truth for what a synced league IS."""
        src = (ROOT / "server.py").read_text()
        for forbidden in ("get_rosters(", "get_matchups(", "get_traded_picks("):
            self.assertNotIn(forbidden, src,
                             f"server.py calls {forbidden} itself rather than through "
                             f"sync_league")

    def test_the_server_binds_loopback_BY_DEFAULT(self):
        """Owner's ruling, and verified empirically: HTTP 000 on the container's own
        192.0.2.2:8765 while 127.0.0.1:8765 served 200.

        ASSERTS THE DEFAULT, NOT THE RESOLVED VALUE. `HOST` reads `GOLDWYRM_HOST`, which exists
        for the tunnel case where cloudflared sits in a different network namespace and the
        app's loopback is not the one it dials. Asserting the resolved value would make this
        test fail for anyone who had that variable set -- and, worse, would pass vacuously in
        the one configuration where the ruling matters least.
        """
        import os
        import server
        self.assertEqual(os.environ.get("GOLDWYRM_HOST", "127.0.0.1"), server.HOST)
        self.assertNotIn("GOLDWYRM_HOST", server.main.__doc__ or "",
                         "the override must not be documented as the way to run this")
        src = (ROOT / "server.py").read_text()
        self.assertIn('os.environ.get("GOLDWYRM_HOST", "127.0.0.1")', src,
                      "loopback is no longer the default bind")

    def test_a_non_loopback_bind_announces_itself(self):
        """An opt-in listener something else can reach is never silent."""
        src = (ROOT / "server.py").read_text()
        self.assertIn("BOUND TO", src)
        self.assertIn("reachable by anything that can route to this host", src)

    def test_health_answers_without_warming_the_engine(self):
        """The probe exists to separate CONNECTIVITY from warm-up when a tunnel returns 502.

        If it warmed, it would cost ~450ms and a cold-start probe would be indistinguishable
        from a slow origin -- which is the exact ambiguity it was added to remove.
        """
        import ast
        import asyncio
        import server
        # PARSED, NOT GREPPED. The first version scanned the function's source text and failed
        # on its own DOCSTRING, which explains why it does not warm -- a scan that cannot tell
        # prose from code is the same defect as a check that cannot fail.
        tree = ast.parse((ROOT / "server.py").read_text())
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.AsyncFunctionDef) and n.name == "health")
        calls = {ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n, ast.Call)}
        self.assertNotIn("ENGINE.ensure_warm", calls, "the health probe warms the engine")
        resp = asyncio.run(server.health(None))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"ok", resp.body)
        self.assertIn(b"writes=0", resp.body)

    def test_health_is_routed(self):
        import server
        self.assertIn("/health", {r.path for r in server.app.routes})

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


class FakeMerger:
    """A merger that prices by name, so pricing's CONTRACT is tested without the real pool.

    The real `DataMerger` reads baseline rankings off disk and its correctness is `#201`'s
    subject with its own tests. What is under test here is the COMPANION-FIELD RULE and the
    join, which a dict exercises exactly as well and in microseconds.
    """

    #: `positional_depth` reads this before it sums any value -- with no rankings loaded it
    #: leaves `value` None for every cell and callers fall back to count alone. True here so the
    #: valued path is the one under test.
    is_loaded = True

    def __init__(self, prices):
        self.prices = prices
        self.format_set_before_pricing = None
        self._priced_any = False

    def set_league_format(self, hint):
        self.format_set_before_pricing = (hint, self._priced_any)

    def merge_player(self, name, position=None, team=None):
        self._priced_any = True
        return {"trade_value": self.prices.get(name)}

    def bye_week_by_team(self):
        return BYES


class PricingKeepsTheCompanionFieldRule(unittest.TestCase):
    """`#346` / `#190`, applied to live rows."""

    def test_a_player_measured_at_zero_IS_priced(self):
        """THE INVERSE ERROR, and the one `or 0.0` would reintroduce.

        `is not None`, never truthiness: a player genuinely valued at 0.0 is priced, and
        collapsing that back into "unpriced" is the same defect mirrored.
        """
        rows = ls.roster_rows(["1"], PLAYERS, BYES)
        priced = ls.price_rows(rows, FakeMerger({rows[0]["name"]: 0.0}))
        self.assertEqual(priced[0]["value"], 0.0)
        self.assertIs(priced[0]["priced"], True, "a measured zero was read as unpriced")

    def test_an_unmatched_player_keeps_a_number_and_says_it_is_unpriced(self):
        rows = ls.roster_rows(["1"], PLAYERS, BYES)
        priced = ls.price_rows(rows, FakeMerger({}))
        self.assertEqual(priced[0]["value"], 0.0, "the solvers negate value; it must be a number")
        self.assertIs(priced[0]["priced"], False)

    def test_pricing_does_not_disturb_the_rest_of_the_row(self):
        rows = ls.roster_rows(["2"], PLAYERS, BYES)
        priced = ls.price_rows(rows, FakeMerger({rows[0]["name"]: 7.5}))
        self.assertEqual(priced[0]["eligible"], {"RB", "WR"})
        self.assertEqual(priced[0]["bye"], BYES["SF"])

    def test_the_name_comes_from_its_one_home(self):
        """`#126`, and the fixture has to DISCRIMINATE or this proves nothing.

        The first draft spelled the derivation inline and the two disagreed: 11 of 15 rows
        priced where `player_name` priced 15. But asserting on a player WITH a `full_name` is
        vacuous -- both spellings agree there, and a mutation reintroducing the inline version
        survived exactly that test. `player_name` falls back to first+last BEFORE the id, so
        player "4" (no full_name) is where they part company.
        """
        import player_universe as pu
        rows = ls.roster_rows(["1", "4"], PLAYERS, BYES)
        self.assertEqual(rows[0]["name"], pu.player_name(PLAYERS["1"], "1"))
        self.assertEqual(rows[1]["name"], "No Fullname",
                         "a player with no full_name fell back to its id, which merge_player "
                         "can never match -- that row would price as unpriced forever")
        self.assertNotEqual(rows[1]["name"], "4")


class TheLeagueFormatIsSetBeforeAnythingIsPriced(unittest.TestCase):
    """The single most expensive lesson in the engine-measurement skill.

    `rec` and `bonus_rec_te` do NOT propagate through `scoring_settings` into valuation -- they
    propagate by FILE SELECTION, and `set_league_format` is what selects. A battery that never
    called it drafted 32 formats from one export and returned standard / half_ppr / ppr
    BYTE-IDENTICAL; nine of thirteen findings were artifacts.
    """

    def test_set_league_format_runs_and_runs_FIRST(self):
        merger = FakeMerger({})
        ls.priced_claims(snapshot(), PLAYERS, merger, owner_id="u1")
        self.assertIsNotNone(merger.format_set_before_pricing,
                             "set_league_format was never called -- every league would be "
                             "priced off one rankings export")
        _hint, priced_already = merger.format_set_before_pricing
        self.assertFalse(priced_already,
                         "a player was priced BEFORE the format was set, so that price came "
                         "from whichever export happened to be loaded")

    def test_the_hint_is_derived_from_the_leagues_own_settings(self):
        """Never carried alongside: a hint that can disagree with its league is a second source
        of truth for the same fact."""
        merger = FakeMerger({})
        snap = snapshot()
        snap["league"]["scoring_settings"] = {"rec": 1.0}
        ls.priced_claims(snap, PLAYERS, merger, owner_id="u1")
        hint, _ = merger.format_set_before_pricing
        self.assertEqual(hint["scoring"], "ppr")

    def test_half_ppr_and_standard_are_distinguished(self):
        for rec, expected in ((0.5, "half_ppr"), (0, "standard"), (1.0, "ppr")):
            merger = FakeMerger({})
            snap = snapshot()
            snap["league"]["scoring_settings"] = {"rec": rec}
            ls.priced_claims(snap, PLAYERS, merger, owner_id="u1")
            self.assertEqual(merger.format_set_before_pricing[0]["scoring"], expected)


class AMissedJoinIsAWiringErrorNotAnAbsence(unittest.TestCase):
    """`positional_depth` keys on `owner_name or f"Roster {roster_id}"`.

    A missed users->owner_id join yields `{}` for that key, which reads downstream as "no thin
    positions and every slot unfillable" -- the most alarming page this surface can draw,
    produced by a lookup miss rather than by anything about the roster.
    """

    def test_the_depth_key_prefers_the_display_name(self):
        self.assertEqual(ls.depth_key({"roster_id": 3}, {"display_name": "SP-Chocobo"}),
                         "SP-Chocobo")

    def test_the_depth_key_falls_back_to_the_roster_id_spelling(self):
        self.assertEqual(ls.depth_key({"roster_id": 3}, {}), "Roster 3")

    def test_a_snapshot_with_no_rosters_states_that_rather_than_returning_empty(self):
        snap = snapshot()
        snap["rosters"] = []
        thin, key, failure = ls.priced_claims(snap, PLAYERS, FakeMerger({}), owner_id="u1")
        self.assertEqual(thin, [])
        self.assertTrue(failure, "an empty result was returned with no reason attached")
        self.assertIn("no rosters", failure)


class AContestedIdentityIsRefusedOnTheRosterPath(unittest.TestCase):
    """`#360` — the defect the invariant registry caught, pinned so it cannot return.

    Two real men resolving onto ONE vendor record is a contested identity; at least one is a
    misidentification and nothing can say which, so neither may keep that record's numbers.
    The board refuses it in `_drop_contested_identities`. A DIRECT `merge_player` call does not,
    and `price_rows` was a direct call -- the exact shape the registry's population note
    describes: "the roster path went back to the merger and got the price anyway."

    MEASURED on the committed rankings before the repair: `Bijan Robinson` and `Brian Robinson`
    both returned `trade_value=99.0` from the single `B Robinson RB ATL` row, and both were
    priced at 99.0 -- a number belonging to exactly one of them, which `bye_collision` would
    then have counted twice.
    """

    @staticmethod
    def _rows():
        mk = lambda i, n: {"id": i, "name": n, "position": "RB", "team": "ATL", "bye": 9,
                           "value": 0.0, "priced": False, "eligible": {"RB"}}
        return [mk("a", "One Robinson"), mk("b", "Other Robinson"),
                {"id": "c", "name": "Nobody Else", "position": "QB", "team": "KC", "bye": 10,
                 "value": 0.0, "priced": False, "eligible": {"QB"}}]

    class _SharedRecordMerger(FakeMerger):
        """Both running backs resolve onto one canonical key, as the vendor row does."""

        def merge_player(self, name, position=None, team=None):
            self._priced_any = True
            if position == "RB":
                return {"trade_value": 99.0, "match_canonical_key": ("b robinson", "RB", "ATL")}
            return {"trade_value": 28.0, "match_canonical_key": (name.lower(), position, team)}

    def test_the_contest_is_detected_over_the_league_not_one_roster(self):
        merger = self._SharedRecordMerger({})
        self.assertEqual(len(ls.contested_keys(self._rows(), merger)), 1)

    def test_two_players_on_one_vendor_record_are_both_refused(self):
        """FAILS ON THE OLD CODE, which handed 99.0 to both."""
        merger = self._SharedRecordMerger({})
        priced = ls.price_rows(self._rows(), merger, ls.contested_keys(self._rows(), merger))
        for row in priced[:2]:
            self.assertIs(row["priced"], False,
                          f"{row['name']} kept a borrowed price the board refuses")
            self.assertEqual(row["value"], 0.0,
                             "the numeric field must stay a number -- the solvers negate it")

    def test_an_uncontested_player_keeps_his_price(self):
        """The guard must decline the PRICE, not the whole population (`#196`)."""
        merger = self._SharedRecordMerger({})
        priced = ls.price_rows(self._rows(), merger, ls.contested_keys(self._rows(), merger))
        self.assertIs(priced[2]["priced"], True, "an uncontested player lost his price")
        self.assertEqual(priced[2]["value"], 28.0)

    def test_the_player_survives_the_refusal(self):
        """What is declined is the borrowed number. The row keeps its identity and eligibility,
        because a phantom-free board that deletes real men is the older, worse defect."""
        merger = self._SharedRecordMerger({})
        priced = ls.price_rows(self._rows(), merger, ls.contested_keys(self._rows(), merger))
        self.assertEqual(len(priced), 3)
        self.assertEqual(priced[0]["eligible"], {"RB"})
        self.assertEqual(priced[0]["bye"], 9)

    def test_an_unmatched_row_is_not_treated_as_contested(self):
        """A `None` canonical key is NOT a shared record -- two unpriceable players must not
        contest each other into a false refusal."""
        merger = FakeMerger({})   # returns no canonical key at all
        self.assertEqual(ls.contested_keys(self._rows(), merger), set())


class TheSyncRoutesRefuseBeforeTheyAct(unittest.TestCase):
    """`#361` — every guard on the two routes that write, driven rather than described."""

    @staticmethod
    def _post(route, data):
        import asyncio
        import server
        from starlette.requests import Request

        body = "&".join(f"{k}={v}" for k, v in data).encode()

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        scope = {"type": "http", "method": "POST", "path": route, "headers": [
            (b"content-type", b"application/x-www-form-urlencoded"),
            (b"content-length", str(len(body)).encode())], "query_string": b""}
        handler = getattr(server, route.strip("/"))
        return asyncio.run(handler(Request(scope, receive)))

    def test_a_post_without_the_token_is_refused(self):
        """Cloudflare Access authenticates WHO is asking, never WHICH PAGE submitted the form."""
        for route in ("/discover", "/add"):
            with self.subTest(route=route):
                self.assertEqual(self._post(route, [("username", "x")]).status_code, 403)

    def test_a_post_with_the_WRONG_token_is_refused(self):
        for route in ("/discover", "/add"):
            with self.subTest(route=route):
                self.assertEqual(
                    self._post(route, [("csrf", "nope"), ("username", "x")]).status_code, 403)

    def test_the_right_token_gets_past_the_csrf_gate(self):
        """Non-vacuity: a gate that refuses EVERYTHING is not a gate, it is a wall."""
        import server
        resp = self._post("/add", [("csrf", server.CSRF)])
        self.assertNotEqual(resp.status_code, 403)
        self.assertEqual(resp.status_code, 400, "an empty selection should be named, not refused")

    def test_an_empty_submission_is_named_rather_than_blank(self):
        import server
        self.assertEqual(self._post("/discover",
                                    [("csrf", server.CSRF), ("username", "")]).status_code, 400)

    def test_a_sync_already_running_is_REFUSED_not_queued(self):
        """Single-flight. Two writers on one league's file is the thing one process exists to
        prevent, and queueing would merely delay it."""
        import server
        server.ENGINE.busy = "syncing something"
        try:
            resp = self._post("/add", [("csrf", server.CSRF), ("league_ids", "123")])
            self.assertEqual(resp.status_code, 409)
            self.assertIn(b"Refused rather than", resp.body)
        finally:
            server.ENGINE.busy = None

    def test_the_csrf_token_is_injected_into_every_post_form(self):
        page = '<form method="post" action="/add"></form><form method="post"></form>'
        import server
        out = server._with_csrf(page)
        self.assertEqual(out.count('name="csrf"'), 2)
        self.assertEqual(out.count(server.CSRF), 2)

    def test_the_token_is_not_baked_into_the_committed_page(self):
        """It is a property of THIS PROCESS. A builder that knew it would be writing a server's
        secret into a committed, standalone artifact."""
        for name in ("landing.html", "landing_unsynced.html"):
            self.assertNotIn('name="csrf"', (R7 / name).read_text(),
                             f"{name} carries a server token")

    def test_the_committed_pages_do_carry_the_forms(self):
        """The forms are the builder's; only the token is the server's."""
        page = (R7 / "landing_unsynced.html").read_text()
        self.assertIn('action="/discover"', page)
        self.assertIn('action="/add"', page)
        self.assertIn('name="username"', page)


class DiscoverOffersOnlyWhatIsNotAlreadyAdded(unittest.TestCase):
    """The owner's rule: setup ADDS; removing is a control on the league, not part of set-up."""

    def test_the_route_filters_against_what_is_on_disk(self):
        import inspect
        import server
        src = inspect.getsource(server.discover)
        self.assertIn("available_snapshots", src,
                      "discover does not consult what is already added")
        self.assertIn("lid not in have", src, "discover does not filter out added leagues")

    def test_it_detects_leagues_sleeper_no_longer_lists(self):
        """Both halves of the diff come from the one call, so nothing has to be REPLACED to
        notice you left a league."""
        import inspect
        import server
        self.assertIn("have - set(listed)", inspect.getsource(server.discover))

    def test_an_empty_result_says_so_rather_than_rendering_an_empty_box(self):
        """`#187` over a list rather than a number: an empty list and a failed lookup must not
        look the same."""
        import inspect
        self.assertIn("already added", inspect.getsource(__import__("server").discover))

    def test_a_league_that_fails_to_sync_is_named(self):
        """"Added 3 of 5" without saying which two is a quiet absence."""
        import inspect
        src = inspect.getsource(__import__("server").add)
        self.assertIn("failed.append", src)
        self.assertIn("207", src, "a partial result returns 200 as though it were complete")


if __name__ == "__main__":
    unittest.main()
