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

import io
import json
import pathlib
import re
import tempfile
import sys
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


class TheServersWritePathsAreAllNamed(unittest.TestCase):
    """`#361`, NARROWED TWICE, and both narrowings are stated rather than quietly absorbed.

    It began by asserting the server performed NO writes at all -- true while it only read
    snapshots `app.py` had synced. Wiring the sync buttons made that false, and the honest
    response was to replace the property that stopped holding with the narrower one that still
    did, rather than delete the test or loosen it until it could not fail.

        FIRST   the server performs no writes at all.
        SECOND  the server's ONLY write is `sleeper_client.sync_league`.
        NOW     the server has THREE named write paths and no unnamed ones --
                `sleeper_client.sync_league` (snapshots), `save_identity` (which Sleeper user
                this install is), `save_archived` (which leagues are hidden). All three go
                through `store_io`, no handler writes directly, and nothing writes outside
                `data/`.

    THE SECOND LINE WAS ALREADY STALE BEFORE `#367` TOUCHED IT. `#362` added `save_identity`
    and this docstring went on claiming one write path, while the scan below -- which tests
    behaviour rather than prose -- kept passing and so never said so. Recorded because it is the
    small version of the thing this whole project keeps finding: the check was right and the
    sentence beside it was not.

    The property that actually protects a reader is unchanged. `_write_snapshot`'s own comment
    is the argument: a torn read of `_latest.json` "looks exactly like a league that has never
    been synced", so the atomic replace is what stops a page rendering mid-sync from seeing one.
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

    def test_the_second_write_path_is_the_identity_and_it_is_named(self):
        """`#362`. TWO write paths now, both named, both atomic, both inside `data/`.

        The identity exists because without it every league page renders as a read failure. The
        alternative the first version took was worse than useless: it silently described
        whichever roster Sleeper happened to list first.
        """
        import inspect
        import live_source
        self.assertIn("store_io.write", inspect.getsource(live_source.save_identity))
        self.assertTrue(str(live_source.IDENTITY).endswith("sleeper_identity.json"))
        self.assertIn("data", str(live_source.IDENTITY))

    def test_an_unreadable_identity_is_an_unknown_user_not_a_crash(self):
        import live_source
        self.assertEqual(live_source.load_identity.__doc__.count("Never raises"), 1)
        self.assertIsInstance(live_source.load_identity(), dict)

    def test_the_one_write_is_sync_league_and_it_is_atomic(self):
        """Pins BOTH halves: that the route delegates, and that the delegate replaces atomically.

        Asserting only the first would let the write stop being atomic without failing; asserting
        only the second would let a handler grow its own write beside it.
        """
        import ast
        import inspect
        import sleeper_client
        import server
        # `_sync_ids`, NOT `add`. `#367` lifted the body out so `/resync` could share it, and
        # this assertion went on passing against `add` purely because its DOCSTRING still said
        # the words "sleeper_client.sync_league". Removing that phrase is what exposed it --
        # the third text-scanning test in this file to be caught by one refactor, and the
        # second to have been passing on prose rather than on code.
        tree = ast.parse(inspect.getsource(server._sync_ids))
        calls = {(n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", ""))
                 for n in ast.walk(tree) if isinstance(n, ast.Call)}
        self.assertIn("sync_league", calls,
                      "the shared sync body does not call sleeper_client.sync_league")
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
        """"Added 3 of 5" without saying which two is a quiet absence.

        READS `_sync_ids`, not `add`. `#367` lifted the sync body out of `add` so `/resync`
        could share it, and this test kept passing against the wrong function for exactly as
        long as the text it searched for happened to still be there. It now points at where the
        behaviour lives.
        """
        import inspect
        src = inspect.getsource(__import__("server")._sync_ids)
        self.assertIn("failed.append", src)
        self.assertIn("207", src, "a partial result returns 200 as though it were complete")


class TheOwnersRosterIsResolvedNeverGuessed(unittest.TestCase):
    """`#362` — the defect that shipped to the owner's own domain.

    `_snapshot_pairs` called `from_snapshot` with no `owner_id`, and the fallback was
    `rosters[0]`. Every league row on the landing page then described whoever Sleeper happened
    to list first: real team names, real priced rosters, real depth labels, ALL ABOUT OTHER
    MANAGERS. Not a crash -- a complete, confident page about somebody else.

    `sleeper_client.find_roster_for_user` already owned this question and returns None rather
    than guessing ("never guesses ... the same fail-soft-not-fabricate posture as the rest of
    this client"). I wrote a second resolution beside it that fabricates (`#126`).
    """

    def test_no_owner_means_a_READ_FAILURE_not_another_managers_roster(self):
        """FAILS ON THE OLD CODE, which returned a fully-populated page for rosters[0]."""
        fx, report = ls.from_snapshot(snapshot(), PLAYERS, BYES)      # no owner_id
        field = report.by_name("whose_roster")
        self.assertEqual(field.state, ls.READ_FAILED)
        self.assertTrue(field.loud)
        self.assertIn("not substitute", field.why.lower(),
                      "the refusal no longer says it refuses to substitute")
        # `#371`: AND IT NAMES THE WAY OUT. "This server does not know which Sleeper user you
        # are" states the problem and leaves the reader stuck; the identity is recorded by one
        # specific action and the message now says which.
        self.assertIn("FIND LEAGUES", field.why,
                      "the refusal states the problem without naming the remedy")

    def test_an_owner_with_no_roster_in_this_league_is_also_a_READ_FAILURE(self):
        fx, report = ls.from_snapshot(snapshot(), PLAYERS, BYES, owner_id="not-in-this-league")
        self.assertEqual(report.by_name("whose_roster").state, ls.READ_FAILED)

    def test_the_right_owner_resolves(self):
        """Non-vacuity: a resolver that fails on everything is not a resolver."""
        fx, report = ls.from_snapshot(snapshot(), PLAYERS, BYES, owner_id="u1")
        self.assertEqual(report.by_name("whose_roster").state, ls.MEASURED)
        self.assertEqual(fx["team"], "SP-Chocobo")

    def test_resolution_goes_through_the_one_home(self):
        """`#126`. A second implementation of this question is what produced the wrong page."""
        import inspect
        self.assertIn("find_roster_for_user", inspect.getsource(ls.from_snapshot))

    def test_rosters_zero_is_never_substituted(self):
        """The specific fallback that shipped, named so it cannot come back.

        PARSED, NOT GREPPED -- for the third time tonight a text scan could not tell prose from
        code. The first version of this test searched the function's source for `rosters[0]` and
        failed on the COMMENT explaining that the fallback had been removed. `ast.unparse` drops
        comments, so what is checked is what runs.
        """
        import ast
        import inspect
        code = ast.unparse(ast.parse(inspect.getsource(ls.from_snapshot)))
        self.assertNotIn("rosters[0]", code,
                         "the arbitrary-first-roster fallback is back in executable code")


class AServerThatNeverServedDoesNotExitSuccessfully(unittest.TestCase):
    """`#364` -- `python server.py` on the owner's laptop printed its banner and exited 0 having
    served nothing, which read as a clean shutdown. An exit code is a claim about what happened,
    and 0 was the wrong claim.

    WHY THE GUARD IS TIMING AND NOT A CAUSE CHECK. The failure did not reproduce on this
    container, so the mechanism is unmeasured and `main` does not name one. What is certain is
    arithmetic: a server you leave open runs for longer than a second and a half, so a `run` that
    returns faster than that did not shut down -- it failed to start. The guard needs no cause.
    """

    def _run_main(self, duration):
        """Call `main` with `uvicorn.run` replaced by a fake that lasts `duration`."""
        import time
        import unittest.mock as mock
        import server
        seen = {}

        def fake_run(target, **kw):
            seen["target"] = target
            seen["kw"] = kw
            time.sleep(duration)

        with mock.patch.object(server, "MIN_SERVE_SECONDS", 0.05), \
                mock.patch("uvicorn.run", fake_run), \
                mock.patch("sys.stdout", io.StringIO()) as out:
            code = server.main()
        return code, seen, out.getvalue()

    def test_an_instant_return_is_reported_as_a_failure_to_start(self):
        code, _, said = self._run_main(0.0)
        self.assertEqual(code, 1, "a run that served nothing exited successfully")
        self.assertIn("FAILED TO START", said)

    def test_the_message_names_the_invocation_that_works(self):
        """The owner was handed this workaround in chat. Chat is not where it belongs."""
        _, _, said = self._run_main(0.0)
        self.assertIn("python -m uvicorn server:app", said)

    def test_a_run_that_lasted_exits_zero(self):
        """The other branch, so the guard cannot be satisfied by always failing (`#352`)."""
        code, _, said = self._run_main(0.1)
        self.assertEqual(code, 0)
        self.assertNotIn("FAILED TO START", said)

    def test_uvicorn_is_handed_the_import_string_not_the_app_object(self):
        """The app object is the spelling that failed; the import string is the one that worked.

        Asserted on the ARGUMENT rather than on source text, so it is the call that is pinned.
        """
        _, seen, _ = self._run_main(0.1)
        self.assertEqual(seen["target"], "server:app",
                         "main() passes the app OBJECT -- the spelling that served nothing")

    def test_nothing_at_module_scope_does_work_that_cannot_run_twice(self):
        """The import string costs a SECOND import of this module, under the name `server` beside
        the `__main__` copy. That is only safe while module scope is cheap and side-effect-free,
        so the thing that makes it safe is pinned here rather than left as a comment.

        `Engine()` takes locks and defers warming; `CSRF` is a fresh token per process and only
        the served process's forms are ever checked.
        """
        import ast
        import inspect
        import server
        tree = ast.parse(pathlib.Path(inspect.getfile(server)).read_text())
        for node in tree.body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            val = node.value
            if isinstance(val, ast.Call) and isinstance(val.func, ast.Name):
                self.assertIn(val.func.id, {"Engine", "Starlette", "_load", "dict", "list",
                                            "set", "frozenset", "tuple", "int", "str", "Path"},
                              f"module scope calls {val.func.id}() -- it runs TWICE under the "
                              "import string")

    def test_loading_a_builder_twice_returns_the_same_module(self):
        """`_load` IS on the whitelist above, and this is the reason it is allowed to be.

        It ran twice under the import string and built two module objects per builder: 0.712s of
        duplicated work, measured, and two live copies of one builder, which is `#126` by
        another route. The second call is now a lookup, and this is what says so.
        """
        import server
        first = server._load("probe_landing_idem", pathlib.Path(server.R7 / "build_landing.py"))
        second = server._load("probe_landing_idem", pathlib.Path(server.R7 / "build_landing.py"))
        self.assertIs(first, second, "_load built a second copy of the same builder")

    def test_the_two_builders_the_server_uses_are_the_cached_ones(self):
        """Not a synthetic name: the real registrations, so the whitelist covers what ships."""
        import sys
        import server
        self.assertIs(sys.modules.get("r7_dashboard_server"), server.DASH)
        self.assertIs(sys.modules.get("r7_landing_server"), server.LAND)

    def test_a_builder_that_fails_to_execute_is_not_left_registered(self):
        """A half-executed module in `sys.modules` would be SERVED as if complete -- the import
        system's oldest trap, and the reason the registration is rolled back on failure."""
        import sys
        import tempfile
        import server
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
            fh.write("raise RuntimeError('builder is broken')\n")
            broken = pathlib.Path(fh.name)
        with self.assertRaises(RuntimeError):
            server._load("probe_broken_builder", broken)
        self.assertNotIn("probe_broken_builder", sys.modules,
                         "a builder that raised is still registered and would be served")
        broken.unlink()



class ALeagueIsNamedByItsLeague(unittest.TestCase):
    """`#366` -- the landing page listed nine leagues and titled every row "spchocobo".

    `team` is the user's own Sleeper display name. It is the SAME STRING in every league they
    are in, so a list keyed on it is a list of identical rows. The league's own name was in the
    fixture the whole time, one key away, under `league_name`.

    The mockup never showed this because its twelve seat fixtures carry twelve different `team`
    values -- "Team 1".."Team 12" -- standing in for twelve leagues. One user across nine real
    leagues is the case the fixtures could not represent.
    """

    def _rows(self, **over):
        import importlib.util as ilu
        spec = ilu.spec_from_file_location(
            "r7_landing_test", ROOT / "ui_explore" / "round7" / "build_landing.py")
        mod = ilu.module_from_spec(spec)
        sys.modules.setdefault("r7_landing_test", mod)
        spec.loader.exec_module(mod)
        return mod

    def test_the_row_carries_the_leagues_own_name(self):
        land = self._rows()
        fx, _ = ls.from_fixture(ROOT / "ui_explore" / "front_fixture.json")
        fx = dict(fx, league_name="The Chocobo Stable", team="spchocobo")
        att, quiet, _arch = land.league_rows_from([("L1", fx)], set())
        row = (att + quiet)[0]
        self.assertEqual(row["league"], "The Chocobo Stable")

    def test_the_rendered_row_shows_the_league_not_the_username(self):
        land = self._rows()
        fx, _ = ls.from_fixture(ROOT / "ui_explore" / "front_fixture.json")
        fx = dict(fx, league_name="The Chocobo Stable", team="spchocobo")
        att, quiet, _a = land.league_rows_from([("L1", fx)], set())
        html_out = land.row_html((att + quiet)[0], 0)
        self.assertIn("The Chocobo Stable", html_out)
        self.assertNotIn("<p class=\"lname\">spchocobo", html_out)

    def test_a_fixture_with_no_league_name_still_falls_back_to_team(self):
        """Which is WHY the committed pages did not move: the seat fixtures have no
        `league_name`, so they render exactly as before and stay byte-identical."""
        land = self._rows()
        fx, _ = ls.from_fixture(ROOT / "ui_explore" / "front_fixture.json")
        fx = dict(fx, team="Team 1")
        fx.pop("league_name", None)
        att, quiet, _a = land.league_rows_from([("L1", fx)], set())
        self.assertIn("Team 1", land.row_html((att + quiet)[0], 0))


class TheFormatLabelSaysTheExceptionNotTheDefault(unittest.TestCase):
    """`#366`. The row's second line was EMPTY on every served page, because no snapshot ever
    carried `arm` or `format` and the builder read only those two keys."""

    LG = {"name": "x", "total_rosters": 12, "settings": {"type": 2, "num_teams": 12},
          "scoring_settings": {"rec": 1.0}, "roster_positions": ["QB", "RB", "WR"]}

    def test_dynasty_is_implied_and_not_printed(self):
        """In a dynasty app it is the default, and the owner's rule is that a page carries what
        is worth knowing rather than every variable there is."""
        self.assertEqual(ls.format_label(self.LG), "12 team \u00b7 Full PPR")

    def test_a_league_that_is_not_dynasty_says_so(self):
        """Informative by exception: the one redraft league among nine is the one worth naming."""
        lg = dict(self.LG, settings={"type": 0, "num_teams": 12})
        self.assertTrue(ls.format_label(lg).startswith("Redraft"), ls.format_label(lg))

    def test_superflex_is_named(self):
        lg = dict(self.LG, roster_positions=["QB", "QB", "RB"])
        self.assertIn("superflex", ls.format_label(lg))

    def test_the_scoring_key_is_the_one_that_exists(self):
        """THE BUG THIS PINS. The first version read `ppr_label`, which is not a key
        `league_format_summary` returns -- `.get` gave None, the branch was skipped, and every
        label came back silently short. A missing key is not a missing value (`#187`)."""
        self.assertIn("Full PPR", ls.format_label(self.LG))

    def test_a_renamed_key_fails_loudly_instead_of_shortening_the_label(self):
        import sleeper_client as sc
        real = sc.league_format_summary
        sc.league_format_summary = lambda lg: {"type": "Dynasty"}
        try:
            with self.assertRaises(KeyError):
                ls.format_label(self.LG)
        finally:
            sc.league_format_summary = real

    def test_an_empty_league_yields_no_label_rather_than_a_guess(self):
        self.assertEqual(ls.format_label({}), "")
        self.assertEqual(ls.format_label(None), "")

    def test_a_snapshot_carries_the_label(self):
        """The whole point: `from_snapshot` now fills the key the row reads."""
        snap = {"league": self.LG, "rosters": [], "users": [], "nfl_state": {"week": 15}}
        fx, _rep = ls.from_snapshot(snap, players_db=None, byes={}, merger=None, owner_id=None)
        self.assertEqual(fx["arm"], "12 team \u00b7 Full PPR")


class APageOffersNoDoorItHasNotGot(unittest.TestCase):
    """`#365`. Measured on the committed landing page before this: 18 fragment links, 0 of which
    resolved to an id that exists on the page. Every one dead."""

    def _land(self):
        import importlib.util as ilu
        spec = ilu.spec_from_file_location(
            "r7_landing_nav", ROOT / "ui_explore" / "round7" / "build_landing.py")
        mod = ilu.module_from_spec(spec)
        sys.modules.setdefault("r7_landing_nav", mod)
        spec.loader.exec_module(mod)
        return mod

    def test_the_server_routes_a_row_to_that_leagues_dashboard(self):
        land = self._land()
        self.assertEqual(land.seat_route("1180000000000000002"),
                         "/league/1180000000000000002")

    def test_the_committed_page_keeps_a_fragment_because_it_has_no_server(self):
        land = self._land()
        self.assertTrue(land.seat_fragment("seat01").startswith("#"))

    def test_an_unbuilt_room_is_not_a_link(self):
        """A dimmed label is honest; an anchor that goes nowhere is not. It is a <span>, so
        there is nothing for a keyboard or a screen reader to land on and then fail at."""
        land = self._land()
        bar = land.topbar(unbuilt=("Draft Room",))
        self.assertIn('<span class="room off"', bar)
        self.assertNotIn('href="#draft-room"', bar)

    def test_a_room_that_is_built_stays_a_link(self):
        land = self._land()
        bar = land.topbar(unbuilt=())
        self.assertIn('href="#draft-room"', bar)
        self.assertNotIn('room off', bar)

    def test_home_points_at_the_server_when_there_is_one(self):
        land = self._land()
        self.assertIn('href="/"', land.topbar(home_href="/"))

    def test_the_server_marks_every_room_it_cannot_serve(self):
        """Derived from the builder's own tuple, so adding a room cannot leave this behind."""
        import server
        land = self._land()
        self.assertEqual(set(server.UNBUILT_ROOMS), {lbl for _i, lbl in land.ROOMS})
        self.assertTrue(server.UNBUILT_ROOMS, "no rooms named -- the nav would lie again")




class LeagueManagementIsAControlNotASetupStep(unittest.TestCase):
    """`#367` -- the owner's ruling: "deleting leagues should be a control feature in that
    league's management, not an aspect of set-up". Resync and archive are reached from a
    league's own popover, and both were dead `<button>` elements with no form around them.

    NOTHING HERE TOUCHES THE NETWORK. Every case is one the route settles before it would build
    a client, which is deliberate: a test that needs Sleeper to be up is a test that fails for
    reasons that are not the code's.
    """

    def setUp(self):
        import tempfile
        from starlette.testclient import TestClient
        import server
        self.server = server
        self.client = TestClient(server.app)
        self._real = ls.ARCHIVED
        self.tmp = pathlib.Path(tempfile.mkdtemp()) / "archived_leagues.json"
        ls.ARCHIVED = self.tmp

    def tearDown(self):
        ls.ARCHIVED = self._real

    def _post(self, path, data, token=True):
        if token:
            data = dict(data, csrf=self.server.CSRF)
        return self.client.post(path, data=data, follow_redirects=False)

    def test_archiving_without_the_token_is_refused(self):
        r = self._post("/archive", {"league_id": "L1"}, token=False)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(ls.load_archived(), set(), "a refused post still wrote")

    def test_a_league_can_be_archived_and_brought_back(self):
        r = self._post("/archive", {"league_id": "L1", "action": "archive"})
        self.assertEqual(r.status_code, 303)
        self.assertEqual(ls.load_archived(), {"L1"})
        r = self._post("/archive", {"league_id": "L1", "action": "unarchive"})
        self.assertEqual(r.status_code, 303)
        self.assertEqual(ls.load_archived(), set())

    def test_archiving_names_no_league_is_refused(self):
        self.assertEqual(self._post("/archive", {"league_id": "  "}).status_code, 400)

    def test_archiving_never_deletes_the_snapshot(self):
        """The whole reason unarchiving needs no refetch. Pinned because "archive" is one
        keystroke from "delete" in someone's head, and this says which one it is."""
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(self.server.archive))
        calls = {(n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", ""))
                 for n in ast.walk(tree) if isinstance(n, ast.Call)}
        for word in ("unlink", "remove", "rmtree", "sync_league"):
            self.assertNotIn(word, calls, f"the archive route CALLS {word}")

    def test_the_archive_list_reaches_the_page(self):
        ls.save_archived({"L9"})
        self.assertIn("L9", ls.live_chrome([], {}, None)["archived_seats"])

    def test_resyncing_a_league_that_is_not_on_disk_is_refused_by_name(self):
        """`/resync` REFRESHES; it must never become a second way to add. An unknown id stops
        here, before any client exists, so a typo cannot pull down a league you never chose."""
        r = self._post("/resync", {"league_id": "definitely-not-on-disk"})
        self.assertEqual(r.status_code, 404)
        self.assertIn("nothing to bring", r.text.lower())

    def test_resync_without_the_token_is_refused(self):
        self.assertEqual(self._post("/resync", {}, token=False).status_code, 403)

    def test_there_is_exactly_one_sync_body(self):
        """`/add` and `/resync` differ by a word in the report, not by an implementation.

        CALL NODES, not unparsed text. The first version of this test read
        `ast.unparse(...)` and failed on `add`'s DOCSTRING, which mentions
        `sleeper_client.sync_league` while the code does not call it. `ast.unparse` drops
        comments but KEEPS docstrings, and that difference has now cost four tests in this repo.
        Walking for `ast.Call` asks about what RUNS, which is the only thing a rule like this
        can honestly be about.
        """
        import ast
        import inspect

        def called(fn):
            tree = ast.parse(inspect.getsource(fn))
            names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    f = node.func
                    names.add(f.attr if isinstance(f, ast.Attribute) else
                              getattr(f, "id", ""))
            return names

        for fn in (self.server.add, self.server.resync):
            names = called(fn)
            self.assertIn("_sync_ids", names, f"{fn.__name__} does not share the sync body")
            self.assertNotIn("sync_league", names,
                             f"{fn.__name__} CALLS sync_league directly -- that is the second "
                             "implementation this test exists to prevent")

    def test_the_single_flight_guard_still_covers_both(self):
        """Two writers on one league's file is the thing the single-process design prevents."""
        import ast
        import inspect
        code = ast.unparse(ast.parse(inspect.getsource(self.server._sync_ids)))
        self.assertIn("ENGINE.busy", code)


class TheServerStillHasOnlyNamedWritePaths(unittest.TestCase):
    """Archiving adds a THIRD write path, and a write path that nobody counted is how a
    read-only server stops being one. So it is counted."""

    def test_the_three_stores_are_all_under_data(self):
        for path in (ls.IDENTITY, ls.ARCHIVED):
            self.assertIn("data", path.parts, f"{path} is written outside data/")

    def test_archiving_goes_through_store_io(self):
        import ast
        import inspect
        code = ast.unparse(ast.parse(inspect.getsource(ls.save_archived)))
        self.assertIn("store_io.write", code,
                      "a store wrote its own file -- `#351` exists because that drifted once")

    def test_an_unreadable_archive_file_hides_nothing(self):
        """A degraded read must not hide a league the owner can still see. Failing CLOSED here
        would make leagues vanish for a reason the page could not explain."""
        import tempfile
        real = ls.ARCHIVED
        try:
            bad = pathlib.Path(tempfile.mkdtemp()) / "nope.json"
            bad.write_text("{not json")
            ls.ARCHIVED = bad
            self.assertEqual(ls.load_archived(), set())
        finally:
            ls.ARCHIVED = real




class AnAbsenceCarriesItsReasonAllTheWayToTheReader(unittest.TestCase):
    """`#368`. `bye_profile_from` composes an exact sentence naming how many rostered players
    are unpriced and why that forbids the measurement. Only the WORD "not_computed" crossed into
    the fixture, so every served dashboard showed a bare em dash where an exact answer existed.

    `#187` says an absence carries its reason. It was computed. It just never travelled.
    """

    def _fx(self, **over):
        snap = {"league": {"name": "L", "roster_positions": ["QB", "RB", "WR"],
                           "total_rosters": 12, "settings": {"type": 2, "num_teams": 12},
                           "scoring_settings": {"rec": 1.0}},
                "rosters": [{"roster_id": 1, "owner_id": "me", "players": ["1", "2"],
                             "settings": {}}],
                "users": [{"user_id": "me", "display_name": "me"}],
                "nfl_state": {"week": 15}}
        snap.update(over)
        return ls.from_snapshot(snap, {}, {}, owner_id="me")[0]

    def test_the_reason_reaches_the_fixture(self):
        why = (self._fx().get("_provenance") or {}).get("why") or {}
        self.assertIn("bye_profile", why, "the refusal was computed and then dropped")
        self.assertIn("carry no price", why["bye_profile"])

    def test_the_reason_names_the_count(self):
        """"Some players are unpriced" is not actionable; "16 of 17" is."""
        why = (self._fx().get("_provenance") or {}).get("why") or {}
        self.assertRegex(why["bye_profile"], r"\d+ of \d+ rostered players")

    def test_the_reason_is_not_stale(self):
        """IT WAS. It ended "Pricing is not wired in this pass" -- true when written, false from
        `#359`, and shown to the owner the whole time. A reason is part of the product and ages
        like one."""
        why = (self._fx().get("_provenance") or {}).get("why") or {}
        self.assertNotIn("not wired", why["bye_profile"])

    def test_the_reason_carries_no_leaked_markup(self):
        """This string is RENDERED. The house's ASCII `--` and a backticked item number read as
        leaked source when they land on a page."""
        why = (self._fx().get("_provenance") or {}).get("why") or {}
        text = why["bye_profile"]
        self.assertNotIn("--", text, "an ASCII double hyphen reached the page")
        self.assertNotIn("`", text, "a backticked item number reached the page")

    def test_the_capture_date_travels_when_the_caller_knows_it(self):
        """The server held it in a local variable and threw it away, so Provenance rendered an
        absence for a date it was holding."""
        snap = {"league": {"name": "L", "roster_positions": [], "total_rosters": 12,
                           "settings": {"type": 2, "num_teams": 12},
                           "scoring_settings": {"rec": 1.0}},
                "rosters": [], "users": [], "nfl_state": {"week": 15}}
        fx, _r = ls.from_snapshot(snap, {}, {}, owner_id=None,
                                  capture_prov={"captured_at": "2026-09-07T08:14:10"})
        self.assertEqual((fx["_provenance"] or {}).get("players_db"),
                         {"captured_at": "2026-09-07T08:14:10"})

    def test_a_caller_that_does_not_know_it_says_nothing_rather_than_guessing(self):
        self.assertIsNone((self._fx()["_provenance"] or {}).get("players_db"))

    def test_the_server_keeps_the_provenance_it_builds(self):
        import ast
        import inspect
        import textwrap
        import server
        # DEDENT FIRST: a method's source carries its class indentation, and `ast.parse` raises
        # IndentationError on it. The first version of this test errored rather than failed,
        # which looks different in a run and means the same thing.
        src = textwrap.dedent(inspect.getsource(server.Engine.ensure_warm))
        code = ast.unparse(ast.parse(src))
        self.assertIn("players_prov", code,
                      "the Engine discards the capture provenance again")


class AnEmptyPanelSpeaksRatherThanHovers(unittest.TestCase):
    """`#368`. `absent` renders an em dash with its reason in a `title`, which is right for one
    missing cell in a table and wrong for a panel this size: the whole section is empty, a phone
    has no hover at all, and the reader is left guessing at what should be the clearest thing on
    the page."""

    def _r5(self):
        import importlib.util as ilu
        spec = ilu.spec_from_file_location(
            "r5_dash_reason", ROOT / "ui_explore" / "round5" / "build_dashboard.py")
        mod = ilu.module_from_spec(spec)
        sys.modules.setdefault("r5_dash_reason", mod)
        spec.loader.exec_module(mod)
        return mod

    def test_the_reason_is_in_the_text_not_only_the_tooltip(self):
        r5 = self._r5()
        out = r5.bye_ledger({"bye_profile": None}, "14 of 17 rostered players carry no price")
        body = re.sub(r"<[^>]+>", "", out)
        self.assertIn("14 of 17 rostered players carry no price", body,
                      "the reason is only reachable by hovering")

    def test_the_em_dash_marker_is_still_there(self):
        """The visible sentence is added BESIDE the convention, not instead of it."""
        r5 = self._r5()
        self.assertIn("&mdash;", r5.bye_ledger({"bye_profile": None}, "a reason"))

    def test_a_caller_that_passes_no_reason_renders_exactly_as_before(self):
        """Which is why round5's own three committed pages did not move."""
        r5 = self._r5()
        self.assertIn("no bye profile was measured", r5.bye_ledger({"bye_profile": None}))


class NoPageClaimsAPositionTheLayoutCanTakeAway(unittest.TestCase):
    """`#368`. "The register on the left" is true at 1440px and false at 390px, where the
    columns stack and that register sits ABOVE. A sentence that a media query can falsify is a
    claim the page cannot keep."""

    def test_no_served_page_says_on_the_left(self):
        """OUTSIDE `<style>`, because a CSS comment describing the wide layout is not a claim
        made TO a reader. The first version of this test scanned the raw file and failed on
        `/* two rails: standing state on the left ... */` -- which is the fourth time in this
        repo that a scan caught prose it was never about."""
        for name in ("dashboard.html", "dashboard_quiet.html", "landing.html"):
            page = (ROOT / "ui_explore" / "round7" / name).read_text()
            visible = re.sub(r"<style\b.*?</style>", "", page, flags=re.S | re.I)
            self.assertNotIn("on the left", visible,
                             f"{name} claims a position the layout can take away")

    def test_the_answer_leads_once_the_columns_stack(self):
        """On a phone the page that exists to say WHICH LEAGUE WANTS ME put Connections and On
        Disk above its own headline, and the answer landed about two screens down. The markup's
        order is right for the wide layout and for a screen reader either way, so this is fixed
        in CSS rather than by moving the rails."""
        import importlib.util as ilu
        spec = ilu.spec_from_file_location(
            "r7_land_order", ROOT / "ui_explore" / "round7" / "build_landing.py")
        mod = ilu.module_from_spec(spec)
        sys.modules.setdefault("r7_land_order", mod)
        spec.loader.exec_module(mod)
        css = mod.css()
        self.assertIn(".rail-main{order:1}", css, "the verdict does not lead when stacked")
        self.assertIn(".rail-left{order:2}", css)
        self.assertLess(css.index("@media (max-width:1080px)"), css.index(".rail-main{order:1}"),
                        "the reorder is outside the stacked query, so it would apply at every "
                        "width and break the wide layout")


class TheBrowserStopsAskingForSomethingThatIsNotThere(unittest.TestCase):
    """`#368`. A browser requests /favicon.ico on every page load whether or not a page mentions
    one. There was no route, so every load logged a 404 -- harmless alone, and exactly the kind
    of standing noise that hides a real error when one appears."""

    def test_the_route_exists(self):
        import server
        self.assertIn("/favicon.ico", {r.path for r in server.app.routes})

    def test_it_serves_an_image_with_the_immutable_header(self):
        from starlette.testclient import TestClient
        import server
        r = TestClient(server.app).get("/favicon.ico")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["content-type"], "image/png")
        self.assertIn("immutable", r.headers.get("cache-control", ""))




class TheFirstScreenReadsItsOwnDisk(unittest.TestCase):
    """`#370`. The page a NEW USER meets first carries a panel headed WHAT IS ALREADY ON DISK
    and a footer promising it is "composed from the same freshness rows the synced page reports,
    so the two cannot disagree". It was built from `landing_fixture.json`.

        source rows compared          6
        rows that disagreed           6

    On somebody else's laptop it reported THIS repository's capture dates as theirs -- the same
    defect as `#363`, on the one screen where there is no live data to contrast it against, so
    nothing on the page could have given it away.

    The irony is in the file: the synced branch carries a comment reading "DERIVED CHROME, never
    the fixture's", and the unsynced branch two lines below it read the fixture.
    """

    def test_the_unsynced_page_is_not_built_from_the_committed_fixture(self):
        import ast
        import inspect
        import textwrap
        import server
        src = textwrap.dedent(inspect.getsource(server.landing))
        calls = {(n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", ""))
                 for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Call)}
        self.assertIn("live_chrome", calls)
        self.assertNotIn("read_text", calls,
                         "the front door reads a committed fixture off disk again")

    def test_live_chrome_works_with_no_leagues_at_all(self):
        """Which is the whole case: this path exists precisely when nothing has been synced."""
        chrome = ls.live_chrome([], {}, None)
        self.assertIn("sources", chrome)
        self.assertEqual(chrome["archived_seats"], [])

    def test_with_no_merger_the_manifest_is_never_consulted(self):
        """A GUARD, not a rescue, and the first version of this test said otherwise.

        It asserted `[]` and claimed "the manifest raises and the rows come back empty". The
        manifest is never CALLED -- `if merger is not None` stops short of it -- so the `[]`
        being measured was the initial assignment, and a mutation that made the except branch
        fabricate a date SURVIVED the test. Asserting the right value for the wrong reason is
        the vacuous-test shape this repo keeps finding; the fix is to exercise each path on its
        own input.
        """
        self.assertEqual(ls.live_chrome([], {}, None)["sources"], [])

    def test_a_merger_that_raises_yields_absences_never_a_fabricated_date(self):
        """THE EXCEPT PATH, on an input that actually reaches it. A plausible date belonging to
        another machine is worse than no date at all (`#187`)."""
        class Exploding:
            def __getattr__(self, name):
                raise RuntimeError("this merger is broken")
        self.assertEqual(ls.live_chrome([], {}, Exploding())["sources"], [])




class NoPathAnywhereSubstitutesARoster(unittest.TestCase):
    """`#371`. `#362` removed `rosters[0]` from `from_snapshot` and declared the rule kept. The
    test written for it parsed `from_snapshot` ALONE, so `priced_claims` went on substituting an
    arbitrary manager's roster for four days while the repair was reported as done.

    On the owner's own fourteen-team league that produced a page carrying BOTH failures at once:
    an empty roster above (his, unresolved) and depth claims below (someone else's, from that
    line) -- "RB . 6 rostered", "Unknown . 1 rostered" -- under a banner correctly reporting
    that five fields had failed to arrive.

    THE LESSON IS ABOUT THE TEST, NOT THE LINE. A rule that holds "in the function I fixed" is
    not a rule. This scans the WHOLE MODULE, so the next copy of that fallback fails here
    wherever someone puts it.
    """

    def test_no_function_in_live_source_indexes_a_roster_list(self):
        import ast
        tree = ast.parse(pathlib.Path(ls.__file__).read_text())
        offenders = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Subscript):
                continue
            base = node.value
            if not (isinstance(base, ast.Name) and base.id in {"rosters", "league_rows"}):
                continue
            idx = node.slice
            if isinstance(idx, ast.Constant) and isinstance(idx.value, int):
                offenders.append(f"line {node.lineno}: {base.id}[{idx.value}]")
        self.assertEqual(offenders, [],
                         "a roster is being picked by POSITION somewhere in live_source -- "
                         "`sleeper_client.find_roster_for_user` is the one home and it returns "
                         "None rather than guessing: " + "; ".join(offenders))

    def test_every_owner_resolution_routes_through_the_one_home(self):
        """Both functions that need to know whose roster it is must ask the same question."""
        import ast
        import inspect
        for fn in (ls.from_snapshot, ls.priced_claims):
            calls = {(n.func.attr if isinstance(n.func, ast.Attribute)
                      else getattr(n.func, "id", ""))
                     for n in ast.walk(ast.parse(inspect.getsource(fn)))
                     if isinstance(n, ast.Call)}
            self.assertIn("find_roster_for_user", calls,
                          f"{fn.__name__} resolves the owner some other way")

    def test_priced_claims_refuses_rather_than_substituting(self):
        snap = {"league": {"name": "L", "roster_positions": ["QB"], "total_rosters": 2,
                           "settings": {"type": 2, "num_teams": 2},
                           "scoring_settings": {"rec": 1.0}},
                "rosters": [{"roster_id": 1, "owner_id": "somebody_else", "players": ["1"]}],
                "users": [{"user_id": "somebody_else", "display_name": "Not Me"}],
                "nfl_state": {"week": 15}}
        thin, my_key, failure = ls.priced_claims(snap, {}, None, owner_id="me")
        self.assertEqual(thin, [])
        self.assertTrue(failure, "an unresolved owner produced no stated failure")
        self.assertIn("no roster in this league belongs to", failure)

    def test_an_unresolved_owner_computes_no_roster_claims_at_all(self):
        """An empty roster is not a measurement. `holes_from([])` reports that no rostered
        player can fill ANY slot, which rendered as "No rostered player can fill DB, DL, FLEX,
        IDP_FLEX, LB, QB, RB, SUPER_FLEX, TE, WR. No amount of value fixes it." -- a true
        statement about an empty list and a false one about a real team."""
        snap = {"league": {"name": "L", "roster_positions": ["QB", "RB"], "total_rosters": 2,
                           "settings": {"type": 2, "num_teams": 2},
                           "scoring_settings": {"rec": 1.0}},
                "rosters": [{"roster_id": 1, "owner_id": "somebody_else", "players": ["1"]}],
                "users": [{"user_id": "somebody_else", "display_name": "Not Me"}],
                "nfl_state": {"week": 15}}
        fx, report = ls.from_snapshot(snap, {}, {}, owner_id="me")
        basis = (fx["_provenance"] or {})["basis"]
        # `thin_positions` is NOT in this list, and that is a real distinction rather than an
        # omission: with no merger `priced_claims` is never called at all, so that field is
        # not_computed (nothing tried) rather than read_failed (something tried and broke).
        # Its refusal is pinned separately, where a merger exists to refuse with.
        for field in ("structural_holes", "bye_profile", "whose_roster"):
            self.assertEqual(basis[field], ls.READ_FAILED,
                             f"{field} was computed over a roster nobody could identify")

    def test_the_reason_is_the_same_one_the_banner_carries(self):
        """So the page cannot contradict its own header."""
        snap = {"league": {"name": "L", "roster_positions": ["QB"], "total_rosters": 2,
                           "settings": {"type": 2, "num_teams": 2},
                           "scoring_settings": {"rec": 1.0}},
                "rosters": [{"roster_id": 1, "owner_id": "x", "players": []}],
                "users": [], "nfl_state": {"week": 15}}
        fx, _r = ls.from_snapshot(snap, {}, {}, owner_id=None)
        why = (fx["_provenance"] or {})["why"]
        self.assertIn("does not know which Sleeper user you are", why["structural_holes"])


class AFailedReadNeverReportsAnAllClear(unittest.TestCase):
    """`#371`. A page that had read NOTHING printed "Nothing open this week. 0 checks, all
    clean" -- the all-clear sitting directly beneath a red banner naming eight fields that never
    arrived. It is the worst sentence this page can print and it printed it on the owner's own
    league.

    `checks_summary` has computed `all_clean` correctly since it was written, and its own comment
    says why: "TRUE ONLY IF SOMETHING RAN. With every check absent, `not fired` is vacuously
    true and 'all clean' would be the most dishonest sentence this page could print." The
    function was right. The renderer never asked it.
    """

    def _page(self, states):
        import importlib.util as ilu
        spec = ilu.spec_from_file_location(
            "r7_dash_verdict", ROOT / "ui_explore" / "round7" / "build_dashboard.py")
        mod = ilu.module_from_spec(spec)
        sys.modules.setdefault("r7_dash_verdict", mod)
        spec.loader.exec_module(mod)
        fx, _r = ls.from_fixture(ROOT / "ui_explore" / "front_fixture.json")
        fx = dict(fx)
        for key in states:
            fx.pop(key, None)
        fx["_provenance"] = dict(fx.get("_provenance") or {},
                                 basis={k: ls.READ_FAILED for k in states},
                                 why={k: "the read is at fault" for k in states})
        return mod.build(fx)

    def test_a_page_that_checked_nothing_says_so(self):
        page = self._page(["structural_holes", "bye_profile", "thin_positions"])
        self.assertIn("Nothing was checked", page)
        self.assertNotIn("checks, all clean", page)

    def test_it_does_not_claim_nothing_is_open(self):
        """"Nothing open" is a RESULT. It needs something to have run."""
        self.assertNotIn("Nothing open this week",
                         self._page(["structural_holes", "bye_profile", "thin_positions"]))

    def test_it_says_plainly_that_it_does_not_know(self):
        page = self._page(["structural_holes", "bye_profile", "thin_positions"])
        self.assertIn("it is reporting that it does not know", page)

    def test_a_genuinely_clean_page_still_says_all_clean(self):
        """The other branch, so the guard cannot be satisfied by never reporting clean
        (`#352`): a verification that cannot pass is no better than one that cannot fail."""
        import importlib.util as ilu
        spec = ilu.spec_from_file_location(
            "r7_dash_clean", ROOT / "ui_explore" / "round7" / "build_dashboard.py")
        mod = ilu.module_from_spec(spec)
        sys.modules.setdefault("r7_dash_clean", mod)
        spec.loader.exec_module(mod)
        fx, _r = ls.from_fixture(ROOT / "ui_explore" / "quiet_fixture.json")
        page = mod.build(fx)
        self.assertIn("all clean", page)



if __name__ == "__main__":
    unittest.main()
