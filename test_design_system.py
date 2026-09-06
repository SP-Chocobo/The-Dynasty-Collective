import re
import unittest
import warnings
from unittest import mock

import design_system as ds


def _rgb(value):
    h = value.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lab(value):
    def inv(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (inv(c) for c in _rgb(value))
    x, y, z = (r * 0.4124 + g * 0.3576 + b * 0.1805,
               r * 0.2126 + g * 0.7152 + b * 0.0722,
               r * 0.0193 + g * 0.1192 + b * 0.9505)
    def f(t):
        return t ** (1 / 3) if t > 0.008856 else (7.787 * t + 16 / 116)
    fx, fy, fz = f(x / 0.95047), f(y / 1.0), f(z / 1.08883)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def _delta_e(a, b):
    """CIE Lab dE. Lives in the test, not the module: perceptual SEPARATION is a property the
    palette must hold, checked here, while contrast_ratio is a fact about a pair of tokens the
    design system itself should be able to state."""
    la, lb = _lab(a), _lab(b)
    return sum((x - y) ** 2 for x, y in zip(la, lb)) ** 0.5


def _contrast(a, b):
    def ch(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    def lum(v):
        r, g, bl = (ch(c) for c in _rgb(v))
        return 0.2126 * r + 0.7152 * g + 0.0722 * bl
    x, y = lum(a), lum(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)



class TokenRgbaTests(unittest.TestCase):
    def test_converts_a_known_token_to_its_exact_rgb_triplet(self):
        # emerald = #1a9e4b -> (26, 158, 75), the same triplet BADGE_NECESSITY_CSS's
        # "preferred" rule now derives rather than spelling out by hand.
        self.assertEqual(ds.token_rgba("emerald", 0.18), "rgba(26,158,75,0.18)")

    def test_a_different_token_produces_a_different_triplet(self):
        self.assertEqual(ds.token_rgba("crimson", 0.18), "rgba(176,25,60,0.18)")

    def test_alpha_is_passed_through_unchanged(self):
        self.assertEqual(ds.token_rgba("emerald", 0.5), "rgba(26,158,75,0.5)")

    def test_unknown_token_name_raises_rather_than_silently_producing_black(self):
        with self.assertRaises(KeyError):
            ds.token_rgba("not-a-real-token", 0.18)


class BadgeDerivationTests(unittest.TestCase):
    """The badge blocks are BUILT from TOKENS. Centralizing the text of those blocks in this
    module never stopped the hex values inside them from drifting, and two had drifted before
    they were derived: a "summary"/"strong" badge tinted with one sky and bordered with a
    different one, and a "notice" badge using an amber that was in no token at all. These
    tests are what make that class of drift impossible rather than merely discouraged."""

    def _hexes(self, css: str) -> set[str]:
        return {h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}", css)}

    def _rgb_triplets(self, css: str) -> set[tuple[int, int, int]]:
        return {tuple(int(p) for p in m)
                for m in re.findall(r"rgba\((\d+),(\d+),(\d+),", css)}

    def _token_triplets(self) -> set[tuple[int, int, int]]:
        out = set()
        for value in ds.TOKENS.values():
            h = value.lstrip("#")
            out.add(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
        return out

    def test_every_hex_in_the_badge_css_is_a_real_token_value(self):
        token_hexes = {v.lower() for v in ds.TOKENS.values()}
        for name, css in (("role", ds.BADGE_ROLE_CSS),
                          ("necessity", ds.BADGE_NECESSITY_CSS)):
            stray = self._hexes(css) - token_hexes
            self.assertEqual(stray, set(), f"{name} badge CSS carries non-token hex {stray}")

    def test_every_rgba_tint_in_the_badge_css_is_a_real_token_value(self):
        allowed = self._token_triplets()
        for name, css in (("role", ds.BADGE_ROLE_CSS),
                          ("necessity", ds.BADGE_NECESSITY_CSS)):
            stray = self._rgb_triplets(css) - allowed
            self.assertEqual(stray, set(), f"{name} badge CSS carries non-token rgba {stray}")

    def test_the_two_drifted_values_cannot_return(self):
        # #38bdf8 was the wrong sky (dE 10.6 from the sky token it sat next to); #f59e0b was
        # an untokenized amber that landed dE 9.6 from gold-b. Named explicitly so a future
        # hand-edit that reintroduces either one fails loudly instead of looking plausible.
        both = ds.BADGE_ROLE_CSS + ds.BADGE_NECESSITY_CSS
        for gone in ("#38bdf8", "#f59e0b", "#fbbf24", "56,189,248", "245,158,11"):
            self.assertNotIn(gone, both)

    def test_every_badge_follows_the_same_tint_text_border_rule(self):
        # One rule, no per-badge exceptions: tint = token at 0.18, text = that token's "-b",
        # border = the token. "user" used to deviate on two of the three.
        rules = [line for line in ds.BADGE_ROLE_CSS.splitlines()
                 if line.startswith(".badge-")] + ds.BADGE_NECESSITY_CSS.splitlines()
        self.assertEqual(len(rules), 13)
        for rule in rules:
            border = re.search(r"border: 1px solid (#[0-9a-fA-F]{6})", rule)
            text = re.search(r"color: (#[0-9a-fA-F]{6})", rule)
            tint = re.search(r"background: rgba\((\d+),(\d+),(\d+),0\.18\)", rule)
            self.assertIsNotNone(border, rule)
            self.assertIsNotNone(text, rule)
            self.assertIsNotNone(tint, rule)
            base = border.group(1).lower()
            token = next(k for k, v in ds.TOKENS.items() if v.lower() == base)
            self.assertEqual(text.group(1).lower(), ds.TOKENS[f"{token}-b"].lower(), rule)
            self.assertEqual(ds.token_rgba(token, 0.18),
                             f"rgba({tint.group(1)},{tint.group(2)},{tint.group(3)},0.18)", rule)

    def test_the_emphasis_glow_is_reserved_for_exactly_two_states(self):
        # A Moderator VERDICT and a MUST TAKE. The glow means "top of the scale"; a third
        # user would make it decoration.
        both = ds.BADGE_ROLE_CSS + ds.BADGE_NECESSITY_CSS
        self.assertEqual(both.count("box-shadow"), 2)


class PaletteLegibilityTests(unittest.TestCase):
    """WCAG AA is an external standard, so it can be written down as a floor without inventing
    a constant to fit the sample (#56). Until 2026-09-06 this class ASSERTED that floor on the
    live palette, and the owner ruled it out of the suite: a ratchet here is meant to prevent a
    DEMONSTRATED class of failure, no contrast failure has ever been demonstrated in this
    palette, and a build gate on a preference turns every visual adjustment into a test failure.
    The floor is now the LEGIBILITY POLICY in design_system's docstring, and nothing below
    asserts that the live palette clears it.

    What IS asserted is the instrument, because a test that only passes while the palette is
    pretty proves nothing about the thing that measures it: the written scope is exactly what
    the policy names, `meets` is the measured ratio against the floor and nothing else, a
    synthetic token below its floor is reported as a shortfall and raised as a warning rather
    than an error, and a palette inside policy warns about nothing. The live palette is run
    through it once, UNCAUGHT, so a real shortfall shows up in this run's output as a
    LegibilityWarning without failing it -- visible, not fatal, which is the ruling."""

    def test_the_written_scope_is_every_foreground_token_dim_and_every_pill(self):
        scope = ds.legibility_scope()
        expected = ({k for k in ds.TOKENS if k.endswith("-b")} | {"ink", "muted", "pure", "dim"}
                    | {f"pill:{p}" for p in ds.POSITION_PILL_TOKENS})
        self.assertEqual(set(scope), expected)
        # `dim` is the one recede-into-the-page role: held to AA-large, and meant to stay below
        # normal-text AA because raising it would make it indistinguishable from `muted`.
        self.assertEqual(scope["dim"], ds.WCAG_AA_LARGE_TEXT)
        for name, floor in scope.items():
            if name != "dim":
                with self.subTest(name=name):
                    self.assertEqual(floor, ds.WCAG_AA_NORMAL_TEXT)

    def test_the_floors_are_the_external_standard_not_numbers_fitted_to_the_palette(self):
        self.assertEqual(ds.WCAG_AA_NORMAL_TEXT, 4.5)
        self.assertEqual(ds.WCAG_AA_LARGE_TEXT, 3.0)

    def test_meets_is_the_measured_ratio_against_the_floor_and_nothing_else(self):
        # Checked against this file's own independent contrast implementation, so the report
        # cannot agree with itself by construction.
        for row in ds.legibility_report():
            with self.subTest(name=row["name"]):
                self.assertEqual(row["meets"], row["ratio"] >= row["floor"])
                self.assertGreaterEqual(row["ratio"], 1.0)
                self.assertLessEqual(row["ratio"], 21.0)
                self.assertAlmostEqual(row["ratio"], _contrast(row["hex"], ds.TOKENS["surface"]), places=9)

    def test_a_token_below_its_floor_is_reported_not_raised(self):
        # A "-b" token painted the surface colour itself: 1.0:1, the worst case there is.
        with mock.patch.dict(ds.TOKENS, {"ghost-b": ds.TOKENS["surface"]}):
            short = {row["name"]: row for row in ds.legibility_shortfalls()}
        self.assertIn("ghost-b", short)
        self.assertFalse(short["ghost-b"]["meets"])
        self.assertLess(short["ghost-b"]["ratio"], short["ghost-b"]["floor"])
        self.assertAlmostEqual(short["ghost-b"]["ratio"], 1.0, places=9)

    def test_a_shortfall_is_a_warning_not_a_failure(self):
        with mock.patch.dict(ds.TOKENS, {"ghost-b": ds.TOKENS["surface"]}):
            with self.assertWarns(ds.LegibilityWarning) as caught:
                short = ds.warn_if_out_of_policy()
        self.assertIn("ghost-b", str(caught.warning))
        self.assertIn("ghost-b", [row["name"] for row in short])

    def test_a_palette_inside_policy_warns_about_nothing(self):
        # A synthetic palette, not the live one -- asserting the live palette is clean would be
        # the ratchet the ruling removed, wearing a different name.
        white_on_black = {"surface": "#000000", "ink": "#ffffff", "muted": "#ffffff",
                          "pure": "#ffffff", "dim": "#ffffff", "only-b": "#ffffff"}
        with mock.patch.dict(ds.TOKENS, white_on_black, clear=True), \
                mock.patch.dict(ds.POSITION_PILL_TOKENS, {"QB": "#ffffff"}, clear=True), \
                warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            short = ds.warn_if_out_of_policy()
        self.assertEqual(short, [])
        self.assertEqual(caught, [])

    def test_the_live_palette_is_measured_every_run_and_a_shortfall_is_seen_not_fatal(self):
        # Deliberately NOT inside assertWarns or catch_warnings: if the live palette is below
        # the written floor, the LegibilityWarning has to reach this run's output. What is
        # asserted is consistency -- the warning names exactly the rows the report marks --
        # never that the list is empty.
        short = ds.warn_if_out_of_policy()
        self.assertEqual([row["name"] for row in short],
                         [row["name"] for row in ds.legibility_report() if not row["meets"]])

    def test_contrast_ratio_is_symmetric_and_bounded(self):
        self.assertAlmostEqual(ds.contrast_ratio("ink", "bg"),
                               ds.contrast_ratio("bg", "ink"), places=9)
        self.assertLessEqual(ds.contrast_ratio("ink", "bg"), 21.0)
        self.assertAlmostEqual(ds.contrast_ratio("gold", "gold"), 1.0, places=9)

    def test_the_ground_is_warm_which_is_the_whole_point_of_the_repaint(self):
        # R > B on every ground/surface tone. The previous palette was blue-biased, inherited
        # from a cold blue brand asset that the Gold Wyrm identity replaces.
        for token in ("bg", "surface", "surface-2", "line", "line-2"):
            with self.subTest(token=token):
                h = ds.TOKENS[token].lstrip("#")
                red, blue = int(h[0:2], 16), int(h[4:6], 16)
                self.assertGreater(red, blue)


class PositionPillTests(unittest.TestCase):
    """The old hand-written pill map CLAIMED its colors stayed clear of hues the app already
    uses to mean something, and two of the six were semantic token values copied verbatim (RB
    was cliff-b, TE was block-b) with a third carrying the drifted sky. The claim was never
    checked, so it was free to be false. These tests check the narrowed, real constraint."""

    def test_a_pill_never_collides_with_an_injury_pill_in_the_same_row(self):
        # THE actual co-occurrence: app.py renders a position pill and an injury pill in one
        # table row, so a TE pill the color of a Questionable pill says two things at once.
        # The Questionable pill is amber-b since the 2026-09-06 ruling (it was gold-b); the
        # nearest pill to it is TE at dE 39.8, measured when the move was made.
        for position, value in ds.POSITION_PILL_TOKENS.items():
            for injury in ("amber-b", "crimson-b"):
                with self.subTest(position=position, injury=injury):
                    self.assertGreaterEqual(_delta_e(value, ds.TOKENS[injury]), 25.0)

    def test_pills_are_separable_from_each_other(self):
        items = list(ds.POSITION_PILL_TOKENS.items())
        for i, (pa, va) in enumerate(items):
            for pb, vb in items[i + 1:]:
                with self.subTest(pair=(pa, pb)):
                    self.assertGreaterEqual(_delta_e(va, vb), 25.0)

    def test_no_pill_is_a_semantic_token_value_verbatim(self):
        # The specific way the old map went wrong: not "too close", but literally the same hex.
        semantic = {v.lower() for v in ds.TOKENS.values()}
        for position, value in ds.POSITION_PILL_TOKENS.items():
            with self.subTest(position=position):
                self.assertNotIn(value.lower(), semantic)

    # Pill legibility on `surface` used to be asserted here at 4.5:1. It is the same WCAG floor
    # the 2026-09-06 ruling made written policy, so it moved with it: every pill is inside
    # design_system.legibility_scope() (pinned in PaletteLegibilityTests) and a pill that drops
    # under the floor is warned about, not failed on.

    def test_dst_is_the_same_slot_as_def_and_unknown_falls_back_to_neutral(self):
        self.assertEqual(ds.position_pill_color("DST"), ds.position_pill_color("DEF"))
        self.assertEqual(ds.position_pill_color("NOT_A_POSITION"), ds.position_pill_color("K"))

    def test_the_pill_tint_is_the_same_0_18_convention_the_badges_use(self):
        tint, fg = ds.position_pill_color("QB")
        h = ds.POSITION_PILL_TOKENS["QB"].lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        self.assertEqual(tint, f"rgba({r},{g},{b},0.18)")
        self.assertEqual(fg, ds.POSITION_PILL_TOKENS["QB"])


class RgbaMarkerTests(unittest.TestCase):
    def test_a_marker_expands_to_the_current_token_value(self):
        self.assertEqual(ds.expand_rgba_markers("b: __RGBA_sky_24__;"),
                         f"b: {ds.token_rgba('sky', 0.24)};")

    def test_a_hyphenated_token_name_survives_the_marker(self):
        self.assertEqual(ds.expand_rgba_markers("__RGBA_tie-b_18__"), ds.token_rgba("tie-b", 0.18))

    def test_text_with_no_marker_is_returned_unchanged(self):
        self.assertEqual(ds.expand_rgba_markers(".x { color: red; }"), ".x { color: red; }")

    def test_an_unknown_token_in_a_marker_raises_rather_than_rendering_black(self):
        with self.assertRaises(KeyError):
            ds.expand_rgba_markers("__RGBA_nosuchtoken_18__")


if __name__ == "__main__":
    unittest.main()
