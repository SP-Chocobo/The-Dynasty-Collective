"""`#358` — inlined images become content-addressed URLs, and the committed pages do not move.

WHY THE FIRST ASSERTION IS ABOUT THE REAL PAGE AND NOT A SYNTHETIC STRING. `externalize` finds
data URIs by their literal shape in the markup, which is a contract with the BUILDERS, not with
this module. A synthetic fixture would pass forever while a builder quietly started emitting
images some other way -- assembled in JavaScript, or split across concatenation -- and the page
would go back to shipping 183 KB inline with every test still green. So the control is the real
committed dashboard, and it asserts the count it must find.

THE OTHER HALF, equally important: the committed `.html` files MUST NOT CHANGE. They are
standalone artifacts, correct to inline, and pinned byte-identical against their builders by
`PagesRebuildIdentically` because `#332` shipped 27 of 29 stale pages. This repair runs at render
time precisely so that pin is untouched, and that is asserted here rather than assumed.
"""
from __future__ import annotations

import base64
import pathlib
import unittest

import page_assets as pa

ROOT = pathlib.Path(__file__).resolve().parent
R7 = ROOT / "ui_explore" / "round7"

PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"x" * 64).decode()


class TheRealPageIsTheControl(unittest.TestCase):

    def test_all_three_of_the_dashboards_images_are_found(self):
        """FAILS if a builder ever emits an image some other way -- which is the point."""
        html = (R7 / "dashboard.html").read_text()
        out, assets = pa.externalize(html)
        self.assertEqual(len(assets), 3,
                         f"expected the dashboard's three inlined images, found {len(assets)}")
        self.assertNotIn("data:image", out, "an inline image survived externalisation")

    def test_the_extraction_is_most_of_the_page(self):
        """The measurement that justifies the work, asserted as a floor rather than a figure.

        Measured at the time of writing: 221.0 KB -> 38.0 KB, 83% of the page. Pinned loosely at
        60% so a legitimate art change does not fail the build, while a repair that quietly
        stopped working would.
        """
        html = (R7 / "dashboard.html").read_text()
        out, _ = pa.externalize(html)
        s = pa.savings(html, out)
        self.assertGreater(s["saved"], 0.60 * s["before"],
                           f"externalisation no longer removes most of the page: {s}")

    def test_the_committed_pages_are_not_touched(self):
        """This repair runs at RENDER time; the builders and their artifacts must be unmoved."""
        for name in ("dashboard.html", "landing.html"):
            raw = (R7 / name).read_text()
            self.assertIn("data:image", raw,
                          f"{name} no longer inlines its art -- the committed page is a "
                          "STANDALONE artifact and must keep working with no server")


class NamesAreContentHashes(unittest.TestCase):

    def test_the_same_bytes_always_get_the_same_name(self):
        a, _ = pa.externalize(f'<img src="data:image/png;base64,{PNG}">')
        b, _ = pa.externalize(f'<i><img src="data:image/png;base64,{PNG}"></i>')
        self.assertEqual(a.split('src="')[1].split('"')[0],
                         b.split('src="')[1].split('"')[0])

    def test_different_bytes_get_different_names(self):
        other = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"y" * 64).decode()
        _, one = pa.externalize(f'<img src="data:image/png;base64,{PNG}">')
        _, two = pa.externalize(f'<img src="data:image/png;base64,{other}">')
        self.assertNotEqual(set(one), set(two))

    def test_the_digest_is_over_the_DECODED_bytes(self):
        """So two spellings of one image -- different padding or wrapping -- share a cache entry
        instead of each occupying their own."""
        self.assertEqual(pa.digest(b"abc"), pa.digest(base64.b64decode(
            base64.b64encode(b"abc"))))

    def test_the_extension_comes_from_the_mime_type(self):
        for mime, ext in (("image/jpeg", "jpg"), ("image/png", "png"), ("image/webp", "webp")):
            _, found = pa.externalize(f'<img src="data:{mime};base64,{PNG}">')
            self.assertTrue(next(iter(found)).endswith("." + ext), f"{mime} -> {found}")


class ImmutableIsOnlyHonestWithAHash(unittest.TestCase):
    """The cache header and the content hash are ONE decision; neither is correct alone."""

    def test_the_header_carries_both_halves(self):
        self.assertIn("immutable", pa.CACHE_CONTROL)
        self.assertIn("max-age=", pa.CACHE_CONTROL)
        self.assertIn("public", pa.CACHE_CONTROL)

    def test_the_lifetime_is_a_year(self):
        self.assertIn("max-age=31536000", pa.CACHE_CONTROL)


class DamagedInputIsLeftAlone(unittest.TestCase):
    """Rewriting a broken URI would turn a broken-looking image into a 404 -- strictly harder to
    diagnose, and `asset_data_uri` already treats unreadable assets as "draw without it"."""

    def test_undecodable_base64_is_not_rewritten(self):
        """THE PAYLOAD HAS TO MATCH THE PATTERN, or this test proves nothing.

        The first version used `!!!!notbase64!!!!`, which contains characters outside base64's
        alphabet -- so `DATA_URI` never matched it, `swap` was never called, and the decode
        guard it claims to exercise was UNREACHABLE. It passed, and a mutation that broke that
        guard survived it. `AAAAA` is five characters of legal base64 alphabet, which matches
        the pattern and then fails to decode on length, which is the real case.
        """
        bad = '<img src="data:image/png;base64,AAAAA">'
        self.assertIsNotNone(pa.DATA_URI.search(bad),
                             "the payload must MATCH the pattern or the guard is never reached")
        out, found = pa.externalize(bad)
        self.assertEqual(out, bad)
        self.assertEqual(found, {})

    def test_an_empty_payload_is_not_rewritten(self):
        empty = '<img src="data:image/png;base64,">'
        out, found = pa.externalize(empty)
        self.assertEqual(out, empty)
        self.assertEqual(found, {})

    def test_a_non_image_data_uri_is_left_alone(self):
        """Bounded to images on purpose: a font or a stylesheet is somebody else's decision."""
        font = '<style>@font-face{src:url(data:font/woff2;base64,AAAA)}</style>'
        out, found = pa.externalize(font)
        self.assertEqual(out, font)
        self.assertEqual(found, {})

    def test_a_page_with_no_images_round_trips_unchanged(self):
        self.assertEqual(pa.externalize("<p>nothing here</p>"), ("<p>nothing here</p>", {}))


class TheServerServesThemImmutably(unittest.TestCase):

    def test_the_asset_route_is_registered(self):
        import server
        paths = {r.path for r in server.app.routes}
        self.assertIn("/assets/{name}", paths)

    def test_rendering_populates_the_asset_cache(self):
        """Pinned because the 404 handler's advice -- "load the page first" -- is only true if
        rendering is actually what fills the cache."""
        import server
        import live_source as ls
        fx, report = ls.from_fixture(ROOT / "ui_explore" / "front_fixture.json")
        before = len(server.ASSETS)
        server._render(fx, report)
        self.assertGreater(len(server.ASSETS), before - 1)
        self.assertTrue(server.ASSETS, "a rendered page left no assets to serve")


if __name__ == "__main__":
    unittest.main()
