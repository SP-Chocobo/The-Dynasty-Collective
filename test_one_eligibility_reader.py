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


if __name__ == "__main__":
    unittest.main()
