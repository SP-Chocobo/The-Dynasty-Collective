import pathlib
import re
import unittest
import warnings
from unittest import mock

import design_system as ds

#: The prototype's `shared.css` is where the reserved hues are RESERVED -- its own sentence at
#: lines 20-22 names them -- and `#320` already made that file derive its PILLS from
#: `design_system`. Its reserved-hue VALUES are still its own, and they are not
#: `design_system.TOKENS`': `emerald` differs by dE 15.2 between the two, `violet` by 18.4. So
#: `#321` reads them rather than restating them, because a literal here would be a third home
#: for a quantity that already has two too many.
_PROTOTYPE_CSS = pathlib.Path(__file__).with_name("ui_explore") / "round2" / "fableA" / "_src" / "shared.css"


def _prototype_reserved_hues():
    """`--<name>: #hex` for every reserved hue the prototype draws, read from its own CSS.

    Returns `{}` when the file is absent, and the caller treats that as a REASON TO FAIL rather
    than a reason to skip: a rule whose second population silently empties is the inverted
    instrument `#311` already shipped once.
    """
    if not _PROTOTYPE_CSS.exists():
        return {}
    found = dict(re.findall(r"--([a-z]+(?:-b)?):\s*(#[0-9a-fA-F]{6})",
                            _PROTOTYPE_CSS.read_text(encoding="utf-8")))
    return {k: v for k, v in found.items() if k in ds.RESERVED_SEMANTIC_HUES}


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
    """`#312`: THESE USED TO SPELL THE TRIPLETS OUT. They read
    `assertEqual(ds.token_rgba("emerald", 0.18), "rgba(26,158,75,0.18)")`, pinning emerald's
    #1a9e4b and crimson's #b0193c by hand -- so they were a THIRD-ORDER home for the palette,
    and `#312` broke all three by moving the tokens they had memorised.

    Retyping the new numbers would have rebuilt the same trap. What is under test here is the
    CONVERSION -- hex to an `rgba(...)` string with the alpha passed through -- and that is a
    property of the function, not of whichever colour the token currently holds. So the expected
    triplet is derived independently from the token's own hex: a second implementation of a pure
    conversion is exactly what a test oracle is for, and it cannot go stale when a value moves.

    The one thing deliberately still pinned is the FORMAT, because `rgba(26,158,75,0.18)` with no
    spaces is what the CSS consumes."""

    @staticmethod
    def _triplet(name):
        h = ds.TOKENS[name].lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    def test_converts_a_known_token_to_its_exact_rgb_triplet(self):
        r, g, b = self._triplet("emerald")
        self.assertEqual(ds.token_rgba("emerald", 0.18), f"rgba({r},{g},{b},0.18)")

    def test_a_different_token_produces_a_different_triplet(self):
        r, g, b = self._triplet("crimson")
        self.assertEqual(ds.token_rgba("crimson", 0.18), f"rgba({r},{g},{b},0.18)")
        self.assertNotEqual(ds.token_rgba("crimson", 0.18), ds.token_rgba("emerald", 0.18),
                            "two different tokens must not render the same rgba string")

    def test_alpha_is_passed_through_unchanged(self):
        r, g, b = self._triplet("emerald")
        self.assertEqual(ds.token_rgba("emerald", 0.5), f"rgba({r},{g},{b},0.5)")
        self.assertEqual(ds.token_rgba("emerald", 1), f"rgba({r},{g},{b},1)")

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
        # `#326`: WHICH pill is nearest is not stated here any more. This line used to end
        # "the nearest pill to it is TE at dE 39.8, measured when the move was made" -- the
        # hedge scoped the NUMBER to history but left the IDENTITY in the present tense, and
        # the identity rotted too: `#311` moved K to #fab87e, which is now nearest at 33.17,
        # and `#318` moved TE to 46.78. The floor below is the contract; which pill happens to
        # be closest to it is an output of this loop, not a fact worth asserting in a comment.
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

    def test_a_pill_is_never_a_colour_reserved_for_a_STATE(self):
        """`#318`. The prototype states this in prose at `shared.css:20-22` -- "gold is
        now/selected/yours, amber is caution and assumption, emerald is the slot a pick would
        fill, violet is withheld" -- and nothing encoded it. A position pill is an IDENTITY; one
        of these says what something is DOING. A pill wearing one answers the wrong question.

        THREE PILLS HAD DRIFTED IN, and they were the three OLDEST: QB dE 10.9 from the withheld
        violet, RB 21.4 from emerald, TE 21.7 from amber, measured against the palette that
        actually renders. None of the four added by `#311` was in breach. QB's was visible in a
        single viewport -- a violet `QB` chip beside a violet-bordered `WITHHELD` badge.

        THE FLOOR IS 25.0 AND 20.0 WAS THE TEMPTING WRONG ANSWER: it would have isolated QB alone
        and left RB and TE, turning a three-pill repair into a one-pill one. That is `#56` exactly
        -- a bound is not a threshold, and choosing the number that makes the repair small is
        sizing it to the sample. 25.0 is the floor every other pill rule already uses, applied to
        a new population, which is the same argument `#311` made for the quiet-text tier.

        VERIFIED UNDER BOTH PALETTES, because `#312` will swap the values these hues come from:
        worst margin 29.9 against `design_system`'s own tokens and 27.9 against the prototype's.
        """
        # NON-VACUITY FIRST, and it is here because `#311` shipped the quiet-text rule WITHOUT it
        # and the mutation pass found the hole: empty the population and every arm below is
        # skipped, so the rule reports OK. A guard that fires on compliance and is silent on the
        # violation is the inverted instrument this repository has already caught once.
        self.assertTrue(ds.RESERVED_SEMANTIC_HUES, "the reserved vocabulary is empty")
        self.assertGreaterEqual(len(ds.RESERVED_SEMANTIC_HUES), 8,
                                f"only {len(ds.RESERVED_SEMANTIC_HUES)} reserved hues; the "
                                f"vocabulary this rule ranges over has been thinned")
        for token, meaning in ds.RESERVED_SEMANTIC_HUES.items():
            self.assertIn(token, ds.TOKENS, f"{token} is reserved but is not a token")
            self.assertTrue(meaning.strip(), f"{token} is reserved for nothing in particular")
        self.assertTrue(ds.POSITION_PILL_TOKENS, "there are no pills to hold to the rule")

        # `#321`: BOTH HOMES. The reserved hues are defined twice -- here and in the
        # prototype's `shared.css` -- with different values, and this rule originally ranged
        # over `ds.TOKENS` alone while the breaches `#318` repaired had been measured against
        # the prototype's. The mutation arms proved the gap: reverting QB fired the rule,
        # reverting RB (29.6 here, 21.4 there) and TE (25.0 here -- exactly on the floor --
        # 21.7 there) did not. A pill is drawn on both surfaces, so it must clear both.
        # `#312` collapses the two sets and makes this loop range over one home twice.
        proto = _prototype_reserved_hues()
        self.assertEqual(
            set(proto), set(ds.RESERVED_SEMANTIC_HUES),
            f"the prototype defines {len(proto)} of the {len(ds.RESERVED_SEMANTIC_HUES)} "
            f"reserved hues; this rule's second population is incomplete, which would make it "
            f"report OK on a breach it simply could not see")
        homes = {"design_system.TOKENS": ds.TOKENS, "the prototype's shared.css": proto}

        for position, value in ds.POSITION_PILL_TOKENS.items():
            for token, meaning in ds.RESERVED_SEMANTIC_HUES.items():
                for home, palette in homes.items():
                    with self.subTest(position=position, reserved=token, home=home):
                        self.assertGreaterEqual(
                            _delta_e(value, palette[token]), 25.0,
                            f"the {position} pill is within 25.0 of {token} as {home} defines "
                            f"it, and {token} is reserved for \"{meaning}\" -- an identity "
                            f"wearing a state's colour")

    def test_a_pill_is_never_the_colour_of_the_text_around_it(self):
        """`#311`. The rule the four enforced rules could not see: they govern 8 of 29 tokens,
        and the quiet-text tier is not among them, so `K` sat at dE 2.8 from `muted` -- a
        position pill indistinguishable from body text -- and passed. Measured before it was
        written: this floor fails EXACTLY ONE of the six pills as they stood (K at 2.8); the
        other five clear it at 48.1 to 71.8, and the four added in `#311` at 33.7 to 103.5. It
        is the existing 25.0 floor applied to a new population, not a constant invented to fit
        a sample (`#56`).

        WHAT IT DELIBERATELY DOES NOT COVER. A floor against the ACCENT tokens would fail five
        of the six existing pills -- WR is dE 6.4 from `sky-b`, RB 12.5 from `cliff-b`, TE 15.5
        from `block`, QB 22.8 from `violet-b` -- so it is measured and recorded in `#311` rather
        than ratcheted in here, where it would turn one repair into six.
        """
        # NON-VACUITY FIRST, and it is here because the mutation pass found the hole: with
        # `QUIET_TEXT_TOKENS` emptied, every arm below is skipped and this test PASSES. A rule
        # whose population can be emptied without failing is the inverted guard this repository
        # already caught once -- `_python_rendered_figure_sites` fired on compliance and was
        # silent on the violation. So the population is asserted before it is used.
        self.assertTrue(ds.QUIET_TEXT_TOKENS, "the quiet-text population is empty")
        self.assertGreaterEqual(len(ds.QUIET_TEXT_TOKENS), 4,
                                f"only {len(ds.QUIET_TEXT_TOKENS)} quiet-text tokens; the tier "
                                f"this rule ranges over has been thinned")
        for quiet in ds.QUIET_TEXT_TOKENS:
            self.assertIn(quiet, ds.TOKENS, f"{quiet} is not a token, so nothing is compared")
        self.assertTrue(ds.POSITION_PILL_TOKENS, "there are no pills to hold to the rule")

        for position, value in ds.POSITION_PILL_TOKENS.items():
            for quiet in ds.QUIET_TEXT_TOKENS:
                with self.subTest(position=position, quiet=quiet):
                    self.assertGreaterEqual(
                        _delta_e(value, ds.TOKENS[quiet]), 25.0,
                        f"the {position} pill is within 25.0 of {quiet}, the colour of the text "
                        f"beside it")

    def test_the_absence_marker_is_not_a_pill_and_is_quiet_on_purpose(self):
        """The other half of `#311`, and it asserts the OPPOSITE of the rule above, which is why
        it has to be said out loud. `POSITION_PILL_ABSENT` means "no position known". It must be
        quiet -- an absence rendered loudly is an absence rendered as a value (`#187`) -- so it
        is derived from the quiet tier and held to none of the pill rules. What it must NOT be
        is any position's identity: that was the defect."""
        self.assertNotIn(ds.POSITION_PILL_ABSENT, ds.POSITION_PILL_TOKENS.values(),
                         "the absence marker is some position's pill colour")
        self.assertEqual(ds.TOKENS["muted"], ds.POSITION_PILL_ABSENT,
                         "the absence marker no longer derives from the quiet tier")
        # ...and an unknown position must no longer render as the kicker.
        self.assertNotEqual(ds.position_pill_color("NOT_A_POSITION"),
                            ds.position_pill_color("K"))

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
        # WAS: assertEqual(position_pill_color("NOT_A_POSITION"), position_pill_color("K")) --
        # which pinned the `#311` defect rather than the contract. An unmapped position renders
        # the ABSENCE marker now; the kicker keeps its own identity.
        bg, fg = ds.position_pill_color("NOT_A_POSITION")
        self.assertEqual(ds.POSITION_PILL_ABSENT, fg)
        self.assertNotEqual(ds.position_pill_color("K"), (bg, fg))
        # every real position still resolves to its own pill, which is what makes the line above
        # a narrowing rather than a hole.
        for position, value in ds.POSITION_PILL_TOKENS.items():
            with self.subTest(position=position):
                self.assertEqual(value, ds.position_pill_color(position)[1])

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


class TheStreamlitThemeIsTheSamePaletteTests(unittest.TestCase):
    """#173: `.streamlit/config.toml` themed native widgets in a cool grey with an emerald
    primary while every custom surface was warm-black under gold -- two palettes meeting at
    the iframe edge, and a semantic hue (emerald = surplus/good) spent on a primary button.
    Every colour the theme file names must be a TOKENS value, verbatim."""

    def _theme(self):
        import tomllib
        from pathlib import Path
        return tomllib.loads((Path(__file__).parent / ".streamlit" / "config.toml").read_text())

    def test_every_theme_colour_is_a_token_value(self):
        theme = self._theme()["theme"]
        colours = {k: v for k, v in theme.items() if isinstance(v, str) and v.startswith("#")}
        colours.update({f"sidebar.{k}": v for k, v in theme.get("sidebar", {}).items()
                        if isinstance(v, str) and v.startswith("#")})
        self.assertGreaterEqual(len(colours), 8, "non-vacuity: the theme names its colours")
        values = set(ds.TOKENS.values())
        for name, hex_value in colours.items():
            with self.subTest(name=name):
                self.assertIn(hex_value.lower(), values, f"{name} is not a design_system token")

    def test_the_primary_is_gold_and_not_a_semantic_hue(self):
        primary = self._theme()["theme"]["primaryColor"].lower()
        self.assertEqual(primary, ds.TOKENS["gold"])
        for semantic in ("emerald", "amber", "crimson", "violet", "sky", "cliff", "block"):
            self.assertNotEqual(primary, ds.TOKENS[semantic])

    def test_the_label_on_a_gold_primary_button_clears_the_floor(self):
        # White on gold does not (2.3:1); bg on gold does. app.py paints the label in bg.
        self.assertLess(ds._contrast_hex("#ffffff", ds.TOKENS["gold"]), ds.WCAG_AA_NORMAL_TEXT)
        self.assertGreaterEqual(ds.contrast_ratio("bg", "gold"), ds.WCAG_AA_NORMAL_TEXT)
        import ui_source
        self.assertIn('[data-testid="stBaseButton-primary"]', ui_source.text())


class SharedTreatmentsAreActuallyInjectedTests(unittest.TestCase):
    """A treatment declared "every surface's" that no surface injects is a dead wire.

    FOCUS_VISIBLE_CSS's own docstring says it is the one keyboard-focus treatment every
    interactive row/control on EVERY surface should share; its only consumer was mockups/
    common.py. REDUCED_MOTION_CSS was honoured in the Draft Room iframe only -- while app.py,
    the entire native Streamlit surface, defines global button transitions and inherited
    neither. Both are checked here against the real UI surface text, not against the mockups.
    """

    def setUp(self):
        import ui_source
        self.ui = ui_source.text()

    def test_the_focus_treatment_reaches_the_native_surface(self):
        self.assertIn('.replace("__DESIGN_SYSTEM_FOCUS_VISIBLE__", design_system.FOCUS_VISIBLE_CSS)', self.ui)
        self.assertIn("__DESIGN_SYSTEM_FOCUS_VISIBLE__\n", self.ui)

    def test_the_reduced_motion_treatment_reaches_the_native_surface(self):
        self.assertIn('.replace("__DESIGN_SYSTEM_REDUCED_MOTION__", design_system.REDUCED_MOTION_CSS)', self.ui)
        self.assertIn("__DESIGN_SYSTEM_REDUCED_MOTION__\n", self.ui)

    def test_every_placeholder_the_stylesheet_carries_is_substituted(self):
        # A placeholder with no matching .replace ships to the browser verbatim.
        placeholders = set(re.findall(r"__DESIGN_SYSTEM_[A-Z_]+__", self.ui))
        for marker in placeholders:
            self.assertIn(f'.replace("{marker}"', self.ui, f"{marker} is never substituted")

    def test_the_mono_stack_is_the_shared_one_not_eight_hand_copies(self):
        # Two of the eight hand-copied stacks had already dropped the DejaVu Sans Mono
        # fallback, which is the drift a single constant makes impossible.
        self.assertIn('.replace("__DESIGN_SYSTEM_FONT_MONO__", design_system.FONT_MONO)', self.ui)
        self.assertNotIn("JetBrains Mono", self.ui)

    def test_the_attribute_safe_mono_stack_is_derived_from_the_same_constant(self):
        # An inline style="..." attribute cannot carry the double-quoted form, which is why
        # the two chip builders hand-wrote a shortened one. Derived, so it cannot drift.
        self.assertEqual(ds.FONT_MONO_ATTR, ds.FONT_MONO.replace('"', "'"))
        self.assertIn("DejaVu Sans Mono", ds.FONT_MONO_ATTR)
        self.assertNotIn('"', ds.FONT_MONO_ATTR)
        self.assertIn("design_system.FONT_MONO_ATTR", self.ui)


if __name__ == "__main__":
    unittest.main()
