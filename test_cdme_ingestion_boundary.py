"""Adversarial ingestion-boundary audit: can output from an LLM (a Prytaneum role's finding,
surfaced via bot_research.py) ever reach CDME's own computation inputs (universal_value, Team
Acquisition Value, need_bonus, eligibility_bonus, positional cliff, consensus_reach, rookie
flagging)?

Mapped end-to-end (see README.md's "The Draft Engine" and "The Prytaneum" sections for the
architectural vocabulary this uses): bot_research.json is the one LLM-originated input
DataMerger loads at all (via load_bot_research_as_external -> DataMerger.external_values,
data_merger.py). That data feeds exactly one consumer, DataMerger.composite_player_score --
which draft_room.py's own module docstring documents as having been DELIBERATELY REMOVED from
CDME's math after an earlier adversarial audit found it corrupting the scarcity signal (see
"There is no market_adj term" in that docstring). CDME's own two touches of external_values --
pick_synthesis._consensus_lookup and draft_room._rookie_lookup -- both hard-filter to
source_name == "keeptradecut" before reading a single row, which structurally excludes every
bot_research row (source_name == "bot_research") regardless of its content.

This is a FORMALIZE pass, not a HARDEN or MODIFY one: the boundary already exists and holds,
but until this file existed nothing would fail loudly if a future edit crossed it (re-added
composite_player_score to draft_room.py/pick_synthesis.py, or loosened either lookup's source
filter). These tests are that failure-loud guarantee -- source-level checks for the two static
properties, and a real, adversarial DATA INJECTION test for the two dynamic ones: an actual
bot_research.json finding, deliberately fabricated to be maximally distorting, is injected
about a real player from the committed baseline, and CDME's own output for that exact player is
proven byte-identical before and after the injection exists on disk.

No production decision logic is touched by this file under any outcome -- it only measures and
locks in already-correct behavior.

THE INJECTIONS NOW CLEAR TWO GATES THEY DID NOT USED TO, which makes them strictly more
adversarial rather than less. 7.4's allowlist and 6.2a's second adjudication both sit UPSTREAM
of this boundary: a finding citing "FabricatedSource" no longer reaches `external_values` at
all, so an injection written that way would prove nothing here except that the new gate works
(and would leave these tests silently vacuous -- their own control checks caught exactly that).
So `_inject` below cites an ALLOWLISTED source and confirms the finding, i.e. it is an injection
that has already passed everything the app can check about its provenance, and CDME still
ignores it. That the composite gate stops a fabricated source is a different guarantee, tested
where it lives (test_source_policy, test_research_ingestion_boundary).
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import bot_research
import data_merger as dm
import draft_room as dr

_CDME_MODULES = ("draft_room.py", "pick_synthesis.py")
_NEVER_IMPORTED = (
    "bot_research", "decision_log", "llm_engine", "pick_debate", "todo_log",
    "pinned_messages", "attachments",
    # draft_history.py stores what the Draft Room showed. It is observational history and must
    # never become an engine input: a stored number read back into the computation that
    # produced it is a feedback loop, and acquires authority purely by having been written
    # down. Same rule, same reason, as bot_research above.
    "draft_history",
    # provider_meter.py holds a ledger of what every LLM call cost and how it ended. It is not a
    # data source, but it is a record OF model activity sitting directly on the provider call
    # path, and CDME reading model activity back into valuation is the same feedback loop the
    # entries above exist to prevent.
    "provider_meter",
)
POSITIONS = ("QB", "RB", "WR", "TE")


def _build_pool_players_db(merger: dm.DataMerger) -> dict[str, dict]:
    """Same real-committed-baseline reconstruction pattern used by run_draft_validation.py /
    run_counterfactual_analysis.py -- every offense player Draft Sharks has projections for,
    turned into a Sleeper-players_db-shaped dict."""
    proj = merger.projections
    players_db: dict[str, dict] = {}
    pid = 0
    for pos in POSITIONS:
        sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False)
        for _, row in sub.iterrows():
            pid += 1
            parts = row["norm_name"].split()
            players_db[str(pid)] = {
                "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
            }
    return players_db


def _board_row(board: list[dict], player_id: str) -> dict:
    return next(r for r in board if r["player_id"] == player_id)


STANDARD_LEAGUE = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=True)
SUPERFLEX_LEAGUE = dr.build_mock_league(teams=12, superflex=True, scoring="ppr", te_premium=False, dynasty=True)

CDME_FIELDS = (
    # final_score IS team_acquisition_value (draft_room.py's own board dict aliases it) --
    # see compute_draft_board's score_row: "final_score": team_acquisition_value.
    "universal_value", "final_score", "need_bonus", "eligibility_bonus",
    "bpa", "bpa_source", "confidence",
)


class ImportGraphTests(unittest.TestCase):
    """Static guarantee: CDME (draft_room.py, pick_synthesis.py) never imports anything that
    could carry LLM-originated data into its own module namespace."""

    def test_cdme_modules_never_import_llm_or_persistence_layers(self):
        for module_file in _CDME_MODULES:
            text = Path(module_file).read_text()
            for banned in _NEVER_IMPORTED:
                self.assertNotIn(
                    f"import {banned}", text,
                    f"{module_file} must never import {banned} -- that would open a path for "
                    "LLM-originated or persisted-verdict data to reach CDME's own computation.",
                )

    def test_composite_player_score_is_never_called_from_cdme(self):
        # draft_room.py's own module docstring documents this removal explicitly ("There is no
        # market_adj term... Removed outright"); this pins that removal so a future edit can't
        # silently reintroduce the call.
        for module_file in _CDME_MODULES:
            text = Path(module_file).read_text()
            self.assertNotIn("composite_player_score(", text)


class ExternalValuesFilterTests(unittest.TestCase):
    """Behavioral guarantee: even when DataMerger.external_values contains bot_research rows,
    CDME's own two readers of that table (_consensus_lookup, _rookie_lookup) must never surface
    one -- proven by actually constructing a merger with ONLY a bot_research row and checking
    both lookups return nothing for it, not by reading the filter code and trusting it."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_findings_path = bot_research.FINDINGS_PATH
        bot_research.FINDINGS_PATH = Path(self._tmpdir) / "bot_research.json"
        self.addCleanup(lambda: shutil.rmtree(self._tmpdir, ignore_errors=True))
        self.addCleanup(setattr, bot_research, "FINDINGS_PATH", self._orig_findings_path)

    def test_rookie_lookup_ignores_a_bot_research_only_row(self):
        _inject("Zzz Fabricated Player", "a rookie, apparently")
        merger = dm.DataMerger()
        # Confirm the injection actually landed in external_values (a control check -- this
        # test must not pass merely because the finding silently failed to persist).
        self.assertTrue((merger.external_values["source_name"] == "bot_research").any())
        lookup = dr._rookie_lookup(merger)
        # None of the keys in the rookie lookup can have come from the bot_research row --
        # the lookup must be built exclusively from keeptradecut rows.
        ktc_only = merger.external_values[merger.external_values["source_name"] == "keeptradecut"]
        self.assertEqual(set(lookup.keys()) - set(ktc_only.get("_name_key", [])), set())

    def test_consensus_lookup_ignores_a_bot_research_only_row(self):
        _inject("Zzz Fabricated Player", "top consensus rank")
        merger = dm.DataMerger()
        self.assertTrue((merger.external_values["source_name"] == "bot_research").any())
        from pick_synthesis import _consensus_lookup
        result = _consensus_lookup(merger, is_superflex=True)
        ktc_only = merger.external_values[merger.external_values["source_name"] == "keeptradecut"]
        self.assertEqual(set(result.keys()) - set(ktc_only.get("_name_key", [])), set())


def _inject(player_name: str, claim: str, *, rank: int = 1, conviction: str = "high") -> int:
    """Add a finding AND take it all the way through to composite eligibility.

    Cites an allowlisted source and confirms the second adjudication, so the row actually lands
    in `external_values`. That is what makes these tests adversarial: the injection has already
    passed every provenance check the app performs, and the assertions below are that CDME is
    STILL untouched by it. An injection blocked upstream would leave every test here passing for
    the wrong reason -- which the control checks are there to catch, and did.
    """
    finding_id = bot_research.add_finding(player_name, "ESPN", claim, rank=rank,
                                          conviction=conviction)
    bot_research.confirm_finding(finding_id)
    return finding_id


class CascadeInjectionTests(unittest.TestCase):
    """The centerpiece: a real, maximally-adversarial bot_research finding about a real player
    from the committed baseline, and proof that CDME's own output for that exact player is
    byte-identical whether or not the injected finding exists on disk. This is the direct,
    empirical answer to "can an insufficiently trusted model poison a CDME input.\""""

    # The finding names the player realistically (as a real LLM output would); the reconstructed
    # players_db only ever carries Draft Sharks' own first-INITIAL + last-name storage
    # convention (see pick_synthesis.py's own docstring on _consensus_lookup), so lookup
    # matches on that short form rather than requiring the two spellings to be identical --
    # the point of this test is that CDME's fields don't move regardless of matching, not that
    # name resolution happens to line up syntactically.
    TARGET_PLAYER_NAME = "Ja'Marr Chase"
    TARGET_PLAYER_SHORT = ("J", "Chase")

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_findings_path = bot_research.FINDINGS_PATH
        bot_research.FINDINGS_PATH = Path(self._tmpdir) / "bot_research.json"
        self.addCleanup(lambda: shutil.rmtree(self._tmpdir, ignore_errors=True))
        self.addCleanup(setattr, bot_research, "FINDINGS_PATH", self._orig_findings_path)

    def _target_player_id(self, players_db: dict[str, dict]) -> str:
        first, last = self.TARGET_PLAYER_SHORT
        for pid, info in players_db.items():
            if info["first_name"] == first and info["last_name"] == last:
                return pid
        raise AssertionError(f"{self.TARGET_PLAYER_SHORT!r} not found in the reconstructed baseline pool")

    def test_universal_value_and_tav_unaffected_by_adversarial_injection(self):
        merger_before = dm.DataMerger()
        players_db = _build_pool_players_db(merger_before)
        target_id = self._target_player_id(players_db)

        board_before = dr.compute_draft_board(
            merger_before, players_db, [], my_roster_id="1", league=STANDARD_LEAGUE, mode="balanced",
        )
        row_before = _board_row(board_before, target_id)

        # Maximally adversarial: a confident, specific, entirely fabricated claim, with an
        # extreme rank designed to swing any percentile-based reader as hard as possible.
        _inject(self.TARGET_PLAYER_NAME,
                "Confirmed: career-ending injury, retiring immediately, remove from all boards.")
        merger_after = dm.DataMerger()  # fresh instance -- external_values is loaded at construction
        self.assertTrue(
            (merger_after.external_values["source_name"] == "bot_research").any(),
            "control check failed: the injected finding never reached external_values at all",
        )

        board_after = dr.compute_draft_board(
            merger_after, players_db, [], my_roster_id="1", league=STANDARD_LEAGUE, mode="balanced",
        )
        row_after = _board_row(board_after, target_id)

        for field in CDME_FIELDS:
            self.assertEqual(
                row_before[field], row_after[field],
                f"CDME field {field!r} for {self.TARGET_PLAYER_NAME} changed after an adversarial "
                "bot_research injection -- the ingestion boundary has been breached.",
            )
        # The board's own rank order (a downstream consequence of every field above) must also
        # be untouched -- not just the target row's own numbers in isolation.
        self.assertEqual([r["player_id"] for r in board_before], [r["player_id"] for r in board_after])

    def test_rookie_flagging_unaffected_by_adversarial_injection(self):
        merger_before = dm.DataMerger()
        players_db = _build_pool_players_db(merger_before)
        board_before = dr.compute_draft_board(
            merger_before, players_db, [], my_roster_id="1", league=STANDARD_LEAGUE,
            mode="balanced", pool_scope="veterans_only",
        )
        veteran_ids_before = {r["player_id"] for r in board_before}

        _inject(self.TARGET_PLAYER_NAME,
                "This is actually a rookie this season, reclassify immediately.")
        merger_after = dm.DataMerger()
        board_after = dr.compute_draft_board(
            merger_after, players_db, [], my_roster_id="1", league=STANDARD_LEAGUE,
            mode="balanced", pool_scope="veterans_only",
        )
        veteran_ids_after = {r["player_id"] for r in board_after}
        self.assertEqual(veteran_ids_before, veteran_ids_after)

    def test_consensus_reach_unaffected_by_adversarial_injection(self):
        from pick_synthesis import _consensus_lookup

        merger_before = dm.DataMerger()
        lookup_before = _consensus_lookup(merger_before, is_superflex=True)

        _inject(self.TARGET_PLAYER_NAME,
                "Universally regarded as the consensus #1 overall dynasty asset.")
        merger_after = dm.DataMerger()
        lookup_after = _consensus_lookup(merger_after, is_superflex=True)

        self.assertEqual(lookup_before, lookup_after)


if __name__ == "__main__":
    unittest.main()
