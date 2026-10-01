"""MANDATE 2.6 / `#172`: three readers answered "where can this player be started", and disagreed.

`#172` already ruled that eligibility comes from `fantasy_positions`, never the primary `position`.
`player_universe.player_eligible_positions` is where that rule has a home. Two other places restated
it inline — `realized_ruler`'s backtest and `draft_battery`'s two lineup audits — and an inline
restatement is a second reader, which drifted in two ways at once:

  * NO `FANTASY_POSITIONS` FILTER, so a kicker listed `["K", "P"]` was offered to `optimize_lineup`
    at "P", a slot no league in this app has. 3 rows of the committed capture.
  * THE RAW `position` AS A FALLBACK, for a player whose own fantasy list says he is startable
    nowhere — the exact field `#172` says not to trust, reinstated by the reader meant to enforce it.

AND THE HOME ITSELF HAD THE SAME BUG THE REST OF THIS AUDIT IS ABOUT. It tested `if eligible:` and
fell back whenever the filtered set came out empty, which is TWO situations: `fantasy_positions`
absent (missing data — the fallback is right) and `fantasy_positions` present with nothing startable
in it (an ANSWER, which the fallback overrode). `#187`'s distinction, at a boundary nobody had looked
at.

MEASURED, and small: the capture has ONE such row — Bradley Sowell, `position: TE`,
`fantasy_positions: ["OL"]`, no team. The battery's universe goes 6595 → 6594, because that builder
admits on eligibility and he has none. Reported at that size rather than dressed up; `#172`'s
own note about a nearby finding applies here too — repair the mechanism cheaply, do not justify it
with a cost it does not have.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

import player_universe as pu


class TheTwoEmptySetsMeanDifferentThingsTests(unittest.TestCase):
    def test_an_absent_list_falls_back_to_the_one_position_we_know(self):
        self.assertEqual({"TE"}, pu.player_eligible_positions({"position": "TE"}))
        self.assertEqual({"TE"}, pu.player_eligible_positions(
            {"position": "TE", "fantasy_positions": []}))

    def test_a_list_with_nothing_startable_in_it_IS_the_answer(self):
        """Sleeper saying "offensive lineman" is not missing data, and reinstating the raw
        `position` over it is `#172` inverted."""
        self.assertEqual(set(), pu.player_eligible_positions(
            {"position": "TE", "fantasy_positions": ["OL"]}))

    def test_a_non_fantasy_slot_is_filtered_out_of_a_list_that_has_real_ones(self):
        self.assertEqual({"K"}, pu.player_eligible_positions(
            {"position": "K", "fantasy_positions": ["K", "P"]}))

    def test_a_genuinely_multi_eligible_player_keeps_both(self):
        """NON-VACUITY: the filter must not be eating real eligibility, which is the whole point
        of reading `fantasy_positions` at all."""
        self.assertEqual({"RB", "WR"}, pu.player_eligible_positions(
            {"position": "RB", "fantasy_positions": ["RB", "WR"]}))

    def test_a_record_with_nothing_at_all_is_unassignable_rather_than_guessed(self):
        self.assertEqual(set(), pu.player_eligible_positions({}))


class ThereIsExactlyOneReaderTests(unittest.TestCase):
    """The structural half. A rule with two implementations has two answers, and this one already
    had three."""

    #: The UI surface is NOT named here. It comes from `ui_source.units()`, so this covers every
    #: view module rather than whichever one still happens to be called app.py -- the rule
    #: test_ui_source enforces, and it caught this module naming the file directly.
    MODULES = ("realized_ruler.py", "draft_battery.py", "lineup_optimizer.py", "draft_room.py",
               "pick_synthesis.py", "player_universe.py")

    def _sources(self):
        import ui_source
        for name in self.MODULES:
            yield name, Path(name).read_text()
        yield from ui_source.units().items()

    def test_nothing_assigns_an_ELIGIBLE_set_it_built_itself(self):
        """The retired shape, searched as parsed code so reformatting it is not a pass.

        KEYED ON ELIGIBILITY, not on every read of `fantasy_positions`, and that distinction came
        out of this test failing. My first version flagged any `set()` over `fantasy_positions` and
        found five more sites in `draft_room` -- but only three of them were about eligibility. The
        other two build the set of buckets to look a player up under in the VENDOR TABLE, which
        legitimately wants the primary label included even when the fantasy list excludes it: a
        wider set for a different question. Flattening the two questions together would have been a
        worse repair than the one it replaced.

        So what is flagged is an inline set assigned to something CALLED eligible -- a variable of
        that name, or an `"eligible"` dict key. That is the population `#172` rules on."""
        offenders = []
        for name, source in self._sources():
            tree = ast.parse(source)
            for node in ast.walk(tree):
                inline_sets = []
                if isinstance(node, ast.Assign):
                    named = any(getattr(t, "id", "").startswith("eligible") for t in node.targets)
                    if named:
                        inline_sets.append(node.value)
                elif isinstance(node, ast.Dict):
                    for key, value in zip(node.keys, node.values):
                        if isinstance(key, ast.Constant) and key.value == "eligible":
                            inline_sets.append(value)
                for value in inline_sets:
                    rendered = ast.unparse(value)
                    if "fantasy_positions" in rendered:
                        offenders.append(f"{name}: {rendered}")
        self.assertEqual([], offenders,
                         "an inline eligibility reader came back -- call "
                         "player_eligible_positions instead")

    def test_the_two_vendor_MATCHING_readers_are_recorded_rather_than_unified(self):
        """CHARACTERIZATION of what this repair deliberately did not touch. Invert when repaired.

        `draft_room` builds the vendor-lookup bucket set twice, and the two are not the same
        expression: one is `fantasy_positions` UNION the primary label, the other is
        `fantasy_positions` OR the primary label. They differ for exactly one kind of row -- a
        player whose fantasy list contains nothing startable -- and on the committed capture they
        now agree on all 6,594 rows, because the single row that separated them is the one the
        eligibility fix drops from the universe.

        So it is a real divergence with no current observable consequence, in a vocabulary
        ("which buckets do I look him up under") that is not the one `#172` rules on. Recorded at
        that strength."""
        source = Path("draft_room.py").read_text()
        matching_calls = source.count("_merge_across_eligibility(")
        self.assertGreaterEqual(matching_calls, 3,
                                "the vendor-matching seam moved; re-read this note")
        self.assertIn('positions = set(info.get("fantasy_positions") or ())', source)
        self.assertIn('set(info.get("fantasy_positions") or ([player_position(info)]', source)

    def test_the_two_former_readers_now_call_the_one(self):
        self.assertIn("pu.player_eligible_positions(info)", Path("realized_ruler.py").read_text())
        battery = Path("draft_battery.py").read_text()
        self.assertEqual(2, battery.count("player_eligible_positions(info)"),
                         "the battery's two lineup audits must both go through the one reader")

    def test_the_universe_builder_admits_on_the_same_reader(self):
        """So "in the universe" and "startable somewhere" cannot disagree."""
        self.assertIn("player_universe.player_eligible_positions(info) & wanted",
                      Path("run_draft_battery.py").read_text())


class TheCaptureIsWhereThisWasMeasuredTests(unittest.TestCase):
    """The population, by value, so the numbers in this file's docstring are checkable rather than
    quoted. Slow: it builds the capture universe."""

    @classmethod
    def setUpClass(cls):
        import run_draft_battery as rdb
        cls.db, _ = rdb.build_players_db_from_capture()

    def test_the_multi_eligible_population_is_not_empty(self):
        """Non-vacuity for every claim `#172` makes: if nobody were multi-eligible, none of this
        would matter."""
        multi = [p for p, i in self.db.items() if len(pu.player_eligible_positions(i)) > 1]
        self.assertGreater(len(multi), 100, f"only {len(multi)} multi-eligible players")

    def test_nobody_in_the_universe_is_eligible_nowhere(self):
        """The property the builder and the reader now share: admission is eligibility, so a row
        in the universe has somewhere to be started."""
        stranded = [p for p, i in self.db.items() if not pu.player_eligible_positions(i)]
        self.assertEqual([], stranded)

    def test_no_row_carries_a_slot_no_league_here_has(self):
        for pid, info in self.db.items():
            outside = pu.player_eligible_positions(info) - pu.FANTASY_POSITIONS
            if outside:
                self.fail(f"{pid} is eligible at {sorted(outside)}, which no roster slot uses")


class TheComposedRuleFallsBackOnTheRECORDNotTheANSWERTests(unittest.TestCase):
    """`eligible_positions_for` -- "eligibility, or the row's own label when the pool has no record".

    WHY THIS CLASS EXISTS, STATED PLAINLY: the repair that gave this rule one home shipped with no
    test of its own. It was verified by hand against the real row and by reading the three call
    sites, and neither is a test -- a hand check does not run again, and the mutation gate had no
    arm that could survive. The three sites it replaced had each re-expressed the composition
    (`B-F4`/`C-F3`, review finding 16) and each had gotten it wrong the same way, which is exactly
    the kind of agreement an untested rule produces.

    THE DISTINCTION UNDER TEST is the one `player_eligible_positions` already draws and these
    callers were erasing: `fantasy_positions` ABSENT is missing data, and the row's primary bucket
    is the honest degradation; `fantasy_positions` PRESENT and startable nowhere is an ANSWER, and
    substituting the raw `position` overrides Sleeper with the field `#172` says not to trust
    (`#187`: absence is not a value).
    """

    #: The real shape, from the committed capture: `position: TE`, `fantasy_positions: ["OL"]`.
    #: One row of 6,595, and `build_players_db_from_capture` filters him out before any board is
    #: built -- so this is pinned on the FIXTURE rather than asserted of production, because the
    #: population production receives is 0 of 6,594 and a test over it would be vacuous.
    STARTABLE_NOWHERE = {"first_name": "Bradley", "last_name": "Sowell",
                         "position": "TE", "fantasy_positions": ["OL"]}

    def test_a_row_the_feed_says_starts_NOWHERE_stays_nowhere(self):
        """THE POINT. The mutation this refuses is `... or ({position} if position else ())`,
        which is what all three call sites did before the rule had one home."""
        db = {"1269": self.STARTABLE_NOWHERE}
        self.assertEqual(frozenset(),
                         pu.eligible_positions_for("1269", "TE", db),
                         "the raw `position` was resurrected for a man the feed says is startable "
                         "nowhere -- the #172 breach, reinstated by the fallback")

    def test_the_underlying_reader_AGREES_so_this_is_not_a_second_opinion(self):
        """Non-vacuity of the row itself. If `player_eligible_positions` returned anything for it,
        the test above would pass without the composition being right."""
        self.assertEqual(set(), pu.player_eligible_positions(self.STARTABLE_NOWHERE))

    def test_a_row_the_pool_does_NOT_KNOW_falls_back_to_its_own_label(self):
        """The other half, and the reason the fallback exists at all: a frame may carry `position`
        without a `player_id` the pool knows, and dropping it would remove it from every view."""
        db = {"1269": self.STARTABLE_NOWHERE}
        self.assertEqual(frozenset({"TE"}), pu.eligible_positions_for("nobody", "TE", db))

    def test_no_pool_at_all_falls_back_the_same_way(self):
        """`feasibility_first` is called with `players_db=None` by tests that build frames carrying
        `position` alone -- six of them errored on a KeyError when the first version of `B-F4`
        required an id. The degradation has to survive an absent pool, not just an absent row."""
        self.assertEqual(frozenset({"TE"}), pu.eligible_positions_for("1269", "TE", None))

    def test_a_row_with_neither_a_record_nor_a_label_claims_nothing(self):
        """No guessing when there is nothing to guess from -- and `frozenset()` here is an
        ABSENCE of any claim, which is why the view filter keys off `None` on the snapshot rather
        than off emptiness."""
        self.assertEqual(frozenset(), pu.eligible_positions_for(None, None, None))

    def test_a_MULTI_position_row_keeps_every_position_it_can_start_at(self):
        """The case `#172` was filed for, through the composed rule rather than the reader alone:
        Travis Hunter, `fantasy_positions: ["DB", "WR"]`, whose primary bucket is DB."""
        db = {"x": {"first_name": "Travis", "last_name": "Hunter",
                    "position": "DB", "fantasy_positions": ["DB", "WR"]}}
        self.assertEqual(frozenset({"DB", "WR"}), pu.eligible_positions_for("x", "DB", db))

    def test_the_three_former_sites_no_longer_spell_the_composition(self):
        """`#126`, mechanically. The repair is only done while the other readers keep calling it,
        and `or {position}` reappearing at any of them is the regression."""
        for name, needle in (("draft_room.py", "eligible_positions_for"),
                             ("pick_synthesis.py", "eligible_positions_for"),
                             ("draft_board_ui.py", "eligible_positions is not None")):
            with self.subTest(name):
                self.assertIn(needle, Path(name).read_text(encoding="utf-8"),
                              f"{name} stopped reading the one home for this rule")


if __name__ == "__main__":
    unittest.main()
