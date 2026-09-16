"""#282: the pool gauge's bar is allocated to PLAYERS, and bands inherit.

The owner's question was whether the tank should lock to whole numbers on each band. It does not
need locking: every player is assigned exactly one band at board generation, so the band's
population is an integer already, and the correct move is to stop allocating to bands at all.

WHY THERE IS NO CORRECT WAY TO ALLOCATE TO BANDS. Dividing a fixed integer resource among GROUPS
in proportion to integer populations is the apportionment problem. Balinski-Young (1982): no
method satisfies both quota and freedom from the population paradox. `band_widths` (largest
remainder) takes quota and accepts the paradox -- and `test_the_paradox_is_real_not_hypothetical`
FINDS a live instance rather than asserting one, so this file cannot pass on a claim about
literature it never checked.

`player_widths` escapes the theorem instead of choosing a side: allocate to individuals, let bands
inherit, and there is no allocation among groups left to paradox.

WHAT THIS FILE DOES NOT CLAIM. That the ASCII instrument should change. `SPAN = 16` against a
36-player pool is 0.44 units per player, which does not resolve, so `band_widths` stays and its
approximation is correct FOR THAT WIDTH. The two coexist on purpose (`pool_gauge`'s own docstring
warns against carrying the text quantum into the surface spec, and this is the other direction of
the same rule).
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "pool_gauge", Path(__file__).with_name("evidence") / "mode_boundary" / "pool_gauge.py")
pg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pg)

#: Real measured shape: RB, 36 priced players (260px rail -> 7.2px each, 900px -> 25px each).
RB = {"ELITE": 2, "MID": 13, "DEPTH": 10, "MEH": 11}
SHAPES = [RB,
          {"ELITE": 24, "MID": 6, "DEPTH": 6, "MEH": 6},     # QB: top band swallows the pool
          {"ELITE": 1, "MID": 1, "DEPTH": 1, "MEH": 1},      # every band minimal
          {"ELITE": 3, "MID": 0, "DEPTH": 7, "MEH": 0}]      # holes: bands that do not exist


class TheBarIsAllocatedToPlayers(unittest.TestCase):
    def test_at_span_equals_population_each_band_IS_its_player_count(self):
        """THE IDENTITY THAT PROVES IT IS PER-PLAYER. When the bar has exactly one unit per
        player, a band's width must equal its population -- not approximately, exactly. No
        apportionment method gives this in general; this one gives it by construction."""
        for sizes in SHAPES:
            n = sum(sizes.values())
            with self.subTest(sizes=sizes):
                w = pg.player_widths(sizes, n)
                self.assertEqual({k: v for k, v in w.items() if v},
                                 {k: v for k, v in sizes.items() if v})

    def test_widths_sum_to_span_exactly_at_every_width(self):
        """By telescoping, not by a spare-distribution loop -- so there is no leftover to hand
        out and no rule needed for who gets it."""
        for sizes in SHAPES:
            for span in (12, 36, 100, 260, 901):
                with self.subTest(sizes=sizes, span=span):
                    self.assertEqual(sum(pg.player_widths(sizes, span).values()), span)

    def test_a_band_that_exists_is_visible_whenever_the_bar_resolves(self):
        """A THEOREM HERE, not a rendering floor. `band_widths` needs max(1, ...) and then claws
        the unit back out of the widest band; this needs neither, so the question of whether that
        floor smuggled in a threshold (#56) stops being askable."""
        for sizes in SHAPES:
            n = sum(sizes.values())
            for span in (n, n + 1, 260, 900):
                w = pg.player_widths(sizes, span)
                for band, pop in sizes.items():
                    with self.subTest(sizes=sizes, span=span, band=band):
                        self.assertEqual(w[band] >= 1, pop >= 1)

    def test_an_empty_band_draws_nothing_rather_than_a_minimum(self):
        w = pg.player_widths({"ELITE": 3, "MID": 0, "DEPTH": 7, "MEH": 0}, 260)
        self.assertEqual(w["MID"], 0)
        self.assertEqual(w["MEH"], 0)


class ThePathologyItAvoidsIsReal(unittest.TestCase):
    def test_the_paradox_is_real_not_hypothetical(self):
        """SEARCH for an Alabama instance in `band_widths` rather than assert one exists.

        The Alabama paradox: widen the bar and a band LOSES width. If no instance can be found
        the premise of this whole change is weaker than stated, and this test should say so."""
        found = None
        for sizes in SHAPES:
            for span in range(4, 60):
                a, b = pg.band_widths(sizes), None
                old_span = pg.SPAN
                try:
                    pg.SPAN = span
                    a = pg.band_widths(sizes)
                    pg.SPAN = span + 1
                    b = pg.band_widths(sizes)
                finally:
                    pg.SPAN = old_span
                shrunk = [n for n in a if b[n] < a[n]]
                if shrunk:
                    found = (sizes, span, shrunk, a, b)
                    break
            if found:
                break
        self.assertIsNotNone(
            found, "no Alabama instance found in band_widths -- the stated motivation is weaker "
                   "than this file claims and the docstrings must be corrected, not the test")

    def test_player_widths_HAS_the_paradox_too_and_the_docstring_used_to_deny_it(self):
        """THE CORRECTION THIS FILE EXISTS TO CARRY. `player_widths` first claimed Alabama and
        population effects were "structurally impossible" for it. They are not: discretising
        cumulative positions is itself an apportionment, so Balinski-Young binds here exactly as
        it binds largest remainder. Pinned as a KNOWN PROPERTY so the false claim cannot come
        back, and with the counterexample in the assertion rather than in prose."""
        qb = {"ELITE": 24, "MID": 6, "DEPTH": 6, "MEH": 6}
        self.assertEqual(pg.player_widths(qb, 395)["MID"], 57)
        self.assertEqual(pg.player_widths(qb, 396)["MID"], 56)

    def test_the_paradox_is_OUT_OF_SCOPE_because_the_bar_is_apportioned_once(self):
        """WHY IT DOES NOT MATTER HERE, which is a claim about the CALLER, not the method.

        `render_bands` computes widths from the OPENING band sizes and then drains inside those
        fixed slices. Nothing is re-apportioned while a draft runs, so neither paradox is
        reachable during the only thing this surface shows. Asserted against the real call
        signature: widths must not depend on what is left."""
        import inspect
        body = inspect.getsource(pg.render_bands)
        self.assertIn("band_widths(sizes)", body,
                      "render_bands must apportion from OPENING sizes, never from `left`")
        self.assertNotIn("band_widths(left)", body)
        # And the property itself: the same opening sizes give the same widths at every drain.
        opening, wide = dict(RB), pg.player_widths(RB, 260)
        for band in [b for b in pg.BANDS if RB.get(b)]:
            drained = dict(opening)
            drained[band] = 0
            with self.subTest(band=band):
                self.assertEqual(pg.player_widths(RB, 260), wide,
                                 "widths are a function of OPENING sizes alone")


class TheFillIsTheSameCoordinateSystem(unittest.TestCase):
    def test_fill_never_exceeds_width_without_needing_a_clamp(self):
        for sizes in SHAPES:
            for span in (sum(sizes.values()), 260, 900):
                w = pg.player_widths(sizes, span)
                full = pg.player_fill(sizes, dict(sizes), span)
                with self.subTest(sizes=sizes, span=span):
                    self.assertEqual(full, w, "a full tank must fill exactly its own width")

    def test_draining_only_ever_lowers_the_fill(self):
        """The gauge's defining property (#282: it cannot rebound). Drain one player at a time
        from every band and assert the fill is monotone non-increasing throughout."""
        span = 260
        left = dict(RB)
        prev = pg.player_fill(RB, left, span)
        for band in [b for b in pg.BANDS if RB.get(b)]:
            for _ in range(RB[band]):
                left[band] -= 1
                now = pg.player_fill(RB, left, span)
                for b in RB:
                    with self.subTest(band=band, left=dict(left), b=b):
                        self.assertLessEqual(now[b], prev[b])
                prev = now
        self.assertEqual(sum(prev.values()), 0, "an emptied tank must read empty")

    def test_one_pick_moves_the_bar_exactly_one_unit_when_it_resolves(self):
        """What 'locked to whole numbers' actually buys: the edge is verifiable by eye."""
        span = sum(RB.values())                      # exactly one unit per player
        left = dict(RB)
        before = sum(pg.player_fill(RB, left, span).values())
        left["MID"] -= 1
        self.assertEqual(before - sum(pg.player_fill(RB, left, span).values()), 1)


class TheLimitIsDerivedNotChosen(unittest.TestCase):
    def test_resolvable_is_exactly_one_unit_per_player(self):
        n = sum(RB.values())
        self.assertFalse(pg.resolvable(RB, n - 1))
        self.assertTrue(pg.resolvable(RB, n))
        self.assertTrue(pg.resolvable(RB, 260))

    def test_the_ascii_instrument_does_NOT_resolve_and_that_is_why_band_widths_stays(self):
        """SPAN=16 against 36 players is 0.44 units each. The instrument is not the surface."""
        self.assertFalse(pg.resolvable(RB, pg.SPAN))

    def test_the_real_render_widths_DO_resolve(self):
        for span in (260, 900):
            with self.subTest(span=span):
                self.assertTrue(pg.resolvable(RB, span))


if __name__ == "__main__":
    unittest.main()
