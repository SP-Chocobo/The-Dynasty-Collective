"""Parser row-integrity invariants (repair boundaries R4-R5).

The failure class: a parser that assembles one record from fields taken off MORE THAN ONE
source line is asserting an ordering invariant, and two of this codebase's nine ingestion paths
assert it without checking it. parse_draftsharks_pdf and parse_draftsharks_free_agents_pdf both
read a page as two independent blocks -- a stat block and a name block -- and join them by
positional index, with no shared key, no length assertion and no rank check.

Demonstrated against the real functions before the repair:
  * one player's TEAM/POS line missing -> every later row on the page inherits the previous
    player's stats, the dropped player vanishes, the surplus stat row is discarded, and the
    output is superficially perfect: valid name, team, position, contiguous rank, plausible
    numbers, no error anywhere
  * a stray stat-shaped line interleaved -> one row takes an out-of-range rank and the rest
    shift by one

The first of those leaves no trace at all, which is what makes it the dangerous one. The check
this file asserts already exists in this codebase -- parse_keeptradecut_pdf carries an
expected_rank and skips anything that does not fit, so a missed row TRUNCATES its table instead
of mis-assigning it. R4 gives the two Draft Sharks parsers the same ability to know they are
lost. R5 stops _sniff_pdf_kind handing an unrecognised file to a parser by default.
"""
import unittest

import pypdf

import data_merger as dm


class _StubPage:
    def __init__(self, text):
        self._text = text

    def extract_text(self):
        return self._text


class _StubReader:
    pages: list = []

    def __init__(self, *args, **kwargs):
        self.pages = _StubReader.pages


class _ParserHarness(unittest.TestCase):
    """Drives the real parser over synthetic page text. Nothing on disk is touched."""

    HEADER = "RK 1yr 3yr 3D"
    STATS = [(1, 300, 900, 99), (2, 280, 850, 90), (3, 260, 800, 80), (4, 240, 700, 70)]
    NAMES = [("A One", "CIN", "WR", 1), ("B Two", "ATL", "RB", 1),
             ("C Three", "MIN", "WR", 2), ("D Four", "SEA", "QB", 1)]

    def page(self, stats=None, names=None, extra=()):
        stats = self.STATS if stats is None else stats
        names = self.NAMES if names is None else names
        lines = [self.HEADER]
        lines += [f"{r} {a} {b} {c}" for r, a, b, c in stats]
        lines += list(extra)
        for name, team, position, pos_rank in names:
            lines += [name, f"{team}{position}{pos_rank}"]
        return "\n".join(lines)

    def parse(self, text):
        _StubReader.pages = [_StubPage(text)]
        real = pypdf.PdfReader
        pypdf.PdfReader = _StubReader
        try:
            return dm.parse_draftsharks_pdf("stub.pdf")
        finally:
            pypdf.PdfReader = real


class AlignedPagesStillParseTests(_ParserHarness):
    """The repair must not cost a single correct parse."""

    def test_a_well_formed_page_produces_one_record_per_player(self):
        df, _ = self.parse(self.page())
        self.assertEqual(len(df), 4)
        for (name, _team, _pos, _pr), (_, row), (rank, proj, three, value) in zip(
                self.NAMES, df.iterrows(), self.STATS):
            self.assertEqual(row["name"], name)
            self.assertEqual(row["rank"], rank)
            self.assertEqual(row["projection"], proj)
            self.assertEqual(row["proj_3yr"], three)
            self.assertEqual(row["trade_value"], value)

    def test_trailing_names_beyond_the_stats_keep_null_numerics(self):
        # The one shortfall the parser documents: "just missed the cut" names with no stat row.
        # Fewer stats than names is not evidence of a lost line, so it must stay a parse.
        df, _ = self.parse(self.page(stats=self.STATS[:2]))
        self.assertEqual(len(df), 4)
        self.assertTrue(df["rank"].iloc[:2].notna().all())
        self.assertTrue(df["rank"].iloc[2:].isna().all())

    def test_a_rank_gap_is_not_a_misalignment(self):
        # Real exports do skip ranks -- te_premium_dynasty_rankings.csv carries 7 gaps over 250
        # rows. Contiguity is therefore the wrong invariant; strictly increasing is the right
        # one, and this asserts the difference so the check can never be tightened by accident.
        stats = [(1, 300, 900, 99), (2, 280, 850, 90), (7, 260, 800, 80), (9, 240, 700, 70)]
        df, _ = self.parse(self.page(stats=stats))
        self.assertEqual(len(df), 4)
        self.assertEqual(list(df["rank"]), [1, 2, 7, 9])


class MisalignedPagesFailLoudlyTests(_ParserHarness):
    """Both demonstrated failure modes, and the property that matters: the parser must raise
    rather than emit a record whose fields came from another player."""

    def test_a_missing_team_pos_line_raises_instead_of_shifting_every_later_row(self):
        text = self.page().split("\n")
        text.remove("MINWR2")
        with self.assertRaises(ValueError) as caught:
            self.parse("\n".join(text))
        self.assertIn("align", str(caught.exception).lower())

    def test_a_stray_stat_shaped_line_raises_instead_of_corrupting_two_rows(self):
        stats = self.STATS[:2] + [(2026, 1, 1, 1)] + self.STATS[2:]
        with self.assertRaises(ValueError):
            self.parse(self.page(stats=stats))

    def test_the_shifted_record_is_never_emitted(self):
        # The point of the whole boundary: before this, the page above produced a row for
        # "D Four" carrying C Three's rank, projection, 3-year outlook and trade value, with
        # nothing anywhere marking it. Nothing may come back at all now.
        text = self.page().split("\n")
        text.remove("MINWR2")
        try:
            df, _ = self.parse("\n".join(text))
        except ValueError:
            return
        self.fail(f"a misaligned page still produced {len(df)} records")


class FreeAgentParserSharesTheInvariantTests(unittest.TestCase):
    """The same two-block positional join, in the second parser that uses it. Named separately
    because the defect was found in the rankings parser and it would be easy to repair only the
    one that was measured."""

    def parse(self, text):
        _StubReader.pages = [_StubPage(text)]
        real = pypdf.PdfReader
        pypdf.PdfReader = _StubReader
        try:
            return dm.parse_draftsharks_free_agents_pdf("stub.pdf")
        finally:
            pypdf.PdfReader = real

    def page(self, stats, names):
        lines = [f"{r} {a} {b} {c} {d}" for r, a, b, c, d in stats]
        for name, team, position in names:
            lines += [name, f"{team}{position}"]
        return "\n".join(lines)

    STATS = [(1, 25.2, 25.4, 29.2, 100), (2, 20.1, 21.0, 24.0, 90), (3, 15.0, 16.0, 19.0, 80)]
    NAMES = [("A One", "CIN", "WR"), ("B Two", "ATL", "RB"), ("C Three", "MIN", "WR")]

    def test_an_aligned_page_still_parses(self):
        df, _ = self.parse(self.page(self.STATS, self.NAMES))
        self.assertEqual(len(df), 3)
        self.assertEqual(list(df["name"]), ["A One", "B Two", "C Three"])

    def test_a_missing_team_pos_line_raises(self):
        text = self.page(self.STATS, self.NAMES).split("\n")
        text.remove("MINWR")
        with self.assertRaises(ValueError):
            self.parse("\n".join(text))


class UnrecognisedFormatIsRefusedTests(unittest.TestCase):
    """R5. _sniff_pdf_kind chose the parser from the PDF's own text and fell through to the
    Draft Sharks rankings parser for anything it did not recognise, so a mis-sniff ran the
    wrong parser in silence. No parser is a default."""

    def test_text_matching_no_known_export_is_not_claimed_by_a_parser(self):
        self.assertIsNone(dm._sniff_pdf_kind_from_text("a shopping list\nmilk\neggs\n"))

    def test_each_known_export_is_still_recognised(self):
        for text, expected in (
            ("Free Agent Finder\nMine 1 25.2 25.4 29.2 100\n", "free_agents"),
            ("Trade Value Chart\n1.01 83\n", "trade_value_chart"),
        ):
            with self.subTest(expected):
                self.assertEqual(dm._sniff_pdf_kind_from_text(text), expected)


if __name__ == "__main__":
    unittest.main()
