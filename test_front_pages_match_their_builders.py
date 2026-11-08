"""The committed front pages must be what their builders produce RIGHT NOW.

WHY THIS FILE EXISTS. `ui_explore/round3/` carries three generated pages -- `front.html`,
`front_empty.html` and `front_quiet.html` -- committed to the tree as artifacts a reader opens. Thirty-four tests
already cover them, and every one of those tests calls `build()` IN MEMORY and compares the
string it returns. Not one reads the file on disk. So the builders were tested and the artifacts
were not, and the two drifted apart without a single failure.

HOW FAR APART. Measured when this guard was written: 27 of the 29 colour tokens on the committed
`front.html` were the pre-`#312` palette. `#312` adopted the prototype's token values into
`design_system.TOKENS` -- the one home the page derives its colours from, by calling
`root_css_block()` -- and nothing rebuilt the page. Its headline was "one palette, 27 names 0
disagreeing", and a committed page painted entirely in the abandoned one sat in the tree while
4,373 tests passed. Every colour on the certified front page was wrong and the suite was green.

WHY THE OTHER GUARDS DO NOT COVER IT. The render gate (`ui_explore/round2/fableA/_shoot.py`)
hashes round 2's built pages and has no knowledge of `round3` -- checked, not assumed. So these
two files were held by nothing: not the suite, not the gate.

THIS IS `#328`'S DEFECT IN A SECOND PLACE. That item found 28 stale committed mockup pages and
shipped `test_mockups_palette.py` beside the emitter so the next drift would fail loudly. The
same shape existed here and nobody grepped for the other generator. A guard written for one
emitter is not a guard on the practice.

WHERE IT LIVES, AND WHY NOT BESIDE ITS SUBJECT. The other two front-page test files sit in
`ui_explore/round3/`, and `#308` found that directory had been INVISIBLE to the certification
suite for its whole life -- 34 tests that passed when run by hand and were never once reached by
`unittest discover`, because neither `ui_explore/` nor `ui_explore/round3/` had an `__init__.py`.
Both exist now and `#308` closed that. But a guard whose entire purpose is to catch an unguarded
artifact should not sit in the directory that was recently unreachable, so this one is top level,
where the suite has always reached and where `#328` put the equivalent.
"""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

#: (name, builder module, fixture path, committed page) -- every generated page in `round3`.
#: A TABLE RATHER THAN TWO TEST METHODS, so a third page added later is one row and arrives with
#: its guard, which is the half `#328` got right and the half missing here.
PAGES = [
    ("front", "ui_explore.round3.build_front",
     "ui_explore/front_fixture.json", "ui_explore/round3/front.html"),
    ("empty", "ui_explore.round3.build_empty",
     "ui_explore/empty_fixture.json", "ui_explore/round3/front_empty.html"),
    # THE QUIET STATE, which had no committed page until `checks_run` gave it something true to
    # say. The brief calls this the most frequent state and the feature; it is also the state
    # whose ENTIRE content is the checks line, so a page that goes stale here goes stale in the
    # one place a reader has nothing else to read. Same builder as `front`, a different seat and
    # a clock: seat 11 of the replayed league is measurably quiet (0 holes, 0 thin) and week 15
    # puts every one of its byes behind us.
    ("quiet", "ui_explore.round3.build_front",
     "ui_explore/quiet_fixture.json", "ui_explore/round3/front_quiet.html"),
]


def _rebuild(module_name, fixture):
    """The builder's own `build()` against the fixture at its own default path.

    `build()`, not `main()`: `main()` WRITES, and a guard that invokes the repair cannot report
    that the repair was needed -- it would make the tree clean and pass, every time, which is the
    failure mode of a check that fixes what it measures. Both builders resolve their fixture
    relative to the CURRENT DIRECTORY (`FIX = pathlib.Path("ui_explore/...")`), so the path is
    passed explicitly here rather than relying on the suite's cwd.
    """
    import importlib
    mod = importlib.import_module(module_name)
    return mod.build(json.loads((ROOT / fixture).read_text()))


class TheCommittedPagesAreWhatTheirBuildersProduceTests(unittest.TestCase):
    def test_every_generated_page_in_round3_matches_its_builder_byte_for_byte(self):
        """The whole point. A page committed in a palette the system of record abandoned is a
        page that lies to whoever opens it, and it is invisible to a test that rebuilds."""
        for name, module, fixture, page in PAGES:
            with self.subTest(page=name):
                committed = (ROOT / page).read_text()
                self.assertEqual(
                    _rebuild(module, fixture), committed,
                    f"{page} is NOT what its builder produces. Rebuild it:\n"
                    f"    python3 -m {module.replace('.', '/')}.py\n"
                    f"  or from the repo root:  python3 {module.replace('.', '/')}.py\n"
                    f"This is how 27 of 29 colour tokens went stale after `#312`.")

    def test_the_palette_on_every_page_is_the_system_of_records_OWN_values(self):
        """The specific drift that happened, asserted against its cause rather than its symptom.

        The test above would also fail on a stale page whose builder changed for some unrelated
        reason, and the message would not say which. This one names the quantity: every colour
        token on a committed page has to be the hex `design_system.TOKENS` spells today. It fires
        on exactly the `#312` defect and says so, and it keeps firing if someone ever rebuilds the
        page from a COPY of the palette instead of from `root_css_block()`.
        """
        import re
        import design_system as ds
        expected = {k: v.lower() for k, v in ds.TOKENS.items()}
        for name, _module, _fixture, page in PAGES:
            with self.subTest(page=name):
                text = (ROOT / page).read_text()
                found = {k: v.lower() for k, v in
                         re.findall(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{3,8})", text)}
                shared = sorted(set(found) & set(expected))
                self.assertTrue(shared, f"{page} declares no token design_system also names")
                stale = {k: (found[k], expected[k]) for k in shared if found[k] != expected[k]}
                self.assertEqual(
                    {}, stale,
                    f"{page} carries {len(stale)} of {len(shared)} shared colour tokens at a hex "
                    f"design_system no longer spells: {stale}")


#: Phrases that assert a RANK AMONG PEERS. Nothing in this tree computes one: `depth_label` is a
#: ratio band against the league mean, and `grep -rn "def .*rank"` finds no per-position ranking.
#: "worst week" is deliberately NOT here -- `bye_collision` really does compute which week costs
#: most, so that superlative is earned. These are the ones that are not.
FORBIDDEN_RANK_PROSE = (
    "bottom of this league", "bottom of the league", "last in the league",
    "lowest in the league", "worst in the league", "best in the league",
    "top of the league", "ranked ", "rank of ",
)


class ThePagesDoNotAssertARankTheEngineNeverComputesTests(unittest.TestCase):
    """`#336b`. The guard this defect class did not have.

    `build_front.py` shipped "bottom of this league at the position" for months, inside a page
    held by a byte-identity guard, under 4,393 passing tests. Every one of those tests checks a
    NUMBER. This was PROSE, and nothing in the repo read a sentence and asked whether a function
    returns what it asserts.

    The defect class: PROSE THAT OUTRUNS ITS FUNCTION -- a rank from a band, a cause from a cost,
    a deadline from a season total. Every surface here stamps its FIGURES with a basis. This is
    the first thing that reads a SENTENCE.
    """

    def test_no_built_page_claims_a_rank_among_peers(self):
        for name, _module, _fixture, page in PAGES:
            text = (ROOT / page).read_text().lower()
            for phrase in FORBIDDEN_RANK_PROSE:
                with self.subTest(page=name, phrase=phrase):
                    self.assertNotIn(
                        phrase, text,
                        f"{page} asserts a rank. `depth_label` is a ratio band against the "
                        f"league MEAN and nothing in this tree ranks teams within a position. "
                        f"Say the label the engine returns, or say nothing.")

    def test_the_builder_itself_does_not_spell_a_rank_outside_a_comment(self):
        """The page is generated, so a rank could return the moment the emitter regains one.
        Checked against code lines only -- the comments explaining `#336b` quote the old phrase
        on purpose and must stay quotable."""
        for module in ("ui_explore/round3/build_front.py", "front_claims.py"):
            src = (ROOT / module).read_text()
            code = [ln for ln in src.splitlines()
                    if not ln.lstrip().startswith("#") and not ln.lstrip().startswith('"')]
            body = "\n".join(code).lower()
            for phrase in FORBIDDEN_RANK_PROSE:
                with self.subTest(module=module, phrase=phrase):
                    self.assertNotIn(phrase, body, f"{module} emits a rank in code")


class TheChecksSentenceIsDerivedNotHardcodedTests(unittest.TestCase):
    """`#338` on the one sentence whose job is to be auditable.

    The empty band used to render a HARDCODED list -- "No unfillable slot, no concentrated bye
    week, no position thin against the league" -- unconditionally. Three checks named by the
    renderer, regardless of whether any of them ran. A check that was never measured was
    reported as examined, which is `#187` inverted: not an absence drawn as a zero, an absence
    drawn as a clean bill of health.
    """

    RETIRED = "No unfillable slot, no concentrated bye week, no position thin against the league"

    def test_no_page_carries_the_hardcoded_checks_sentence(self):
        for name, _m, _f, page in PAGES:
            with self.subTest(page=name):
                self.assertNotIn(self.RETIRED, (ROOT / page).read_text())

    def test_the_quiet_page_names_exactly_the_checks_the_engine_ran(self):
        """The count and the names both come from `front_claims.CHECKS`, so this fails if the
        page ever states a number the engine did not produce -- the `VOICE.md` five / designers'
        four / engine's nothing disagreement that `#338` recorded."""
        import front_claims as fc
        text = (ROOT / "ui_explore/round3/front_quiet.html").read_text()
        fx = json.loads((ROOT / "ui_explore/quiet_fixture.json").read_text())
        summary = fc.checks_summary(fc.compose(fx)["checks"])
        self.assertEqual(3, summary["ran"])
        self.assertTrue(summary["all_clean"])
        self.assertIn(f"<b>{summary['ran']}</b> checks, all clean", text)
        for check_name in summary["clean"]:
            self.assertIn(check_name, text)

    def test_the_quiet_page_does_not_flatter(self):
        """`VOICE.md` rule 3. A clean week is a fact, not a compliment, and `#338`'s own argument
        is that "all systems green" invites inventing systems to be green about."""
        text = (ROOT / "ui_explore/round3/front_quiet.html").read_text().lower()
        for flattery in ("all systems", "you're good", "youre good", "crushing it",
                         "looking great", "well done", "congratulations", "nothing needs you"):
            self.assertNotIn(flattery, text)

    def test_the_quiet_page_stamps_its_clock_as_constructed_not_measured(self):
        """The one chosen value on an otherwise measured page. Week 15 is a clock reading, and a
        replayed draft has no point in a season -- so it must not inherit the measured stamp of
        the roster around it."""
        fx = json.loads((ROOT / "ui_explore/quiet_fixture.json").read_text())
        basis = (fx.get("_provenance") or {}).get("basis") or {}
        self.assertIn("CONSTRUCTED", basis.get("current_week", ""),
                      "a chosen clock must not be stamped measured")
        self.assertEqual(15, fx["current_week"])


if __name__ == "__main__":
    unittest.main()
