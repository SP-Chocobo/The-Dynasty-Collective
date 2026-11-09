"""`#358`: inlined images become content-addressed URLs at RENDER time, not at build time.

THE MEASUREMENT THAT MADE THIS WORTH DOING. The round-7 dashboard is 221.0 KB on disk, and
**83% of it is three inlined base64 images**:

    3 data URIs      183.1 KB raw    137.4 KB gzip-9   (75% -- already-compressed binaries)
    HTML + CSS        37.9 KB raw      9.9 KB gzip-9   (26%)

Inlining was CORRECT for a file you double-click: one file, no server, no broken images in a
checkout without `assets/`. It became wrong the moment there was a server, because **a data URI
cannot be cached** -- every navigation re-sends 183 KB that never changes.

    today                   148.4 KB gzipped, EVERY navigation
    content-addressed       ~147 KB once, then ~9.9 KB per navigation

The entire win is repeat navigation, and it exists ONLY if the cache headers are right. Which is
why `immutable` and the content hash are not decoration here: they ARE the repair.

WHY THIS RUNS AT RENDER TIME AND NOT IN THE BUILDERS, which was the first design and is worse.

The obvious repair is a mode switch inside `asset_data_uri` -- inline for the committed page, a
URL for the server. Three things argue against it:

  * The committed `.html` files are pinned BYTE-IDENTICAL against their builders by
    `PagesRebuildIdentically`, which exists because `#332` shipped 27 of 29 stale pages. Any
    builder change risks that pin, for a benefit the committed files never receive -- they are
    standalone artifacts and SHOULD inline.
  * A mode switch is global state read by a builder called from a THREADED server.
  * `asset_data_uri` is `#126`'s one home for the "asset or nothing" rule. Adding a second
    behaviour to it makes it two rules in one function.

Externalising afterwards keeps the builders untouched, keeps the committed pages correct as
standalone files, and makes the whole repair a PURE FUNCTION of the rendered string -- which is
testable, mutatable, and cannot drift from what is served.

WHAT IT CANNOT DO, stated because an unstated limit gets trusted past: it finds `data:` URIs by
their literal shape in the markup. An image assembled by JavaScript, or a URI split across string
concatenation, is invisible to it. The round-7 pages emit theirs whole, from `asset_data_uri`, so
the shape is the contract -- and `test_page_assets` asserts that all three of the real page's
images are found, which is the control that would fail if a builder ever started emitting them
some other way.
"""
from __future__ import annotations

import base64
import binascii
import dataclasses
import hashlib
import re

#: Matched on the SERVED STRING, not on a parsed DOM: these pages are built as text and this runs
#: on the same text. The charset is base64's own alphabet plus padding; the mime is bounded to
#: images so an unrelated `data:` (a font, a stylesheet) is left alone rather than silently moved.
DATA_URI = re.compile(r"data:(image/[a-zA-Z0-9.+-]+);base64,([A-Za-z0-9+/]+={0,2})")

#: One year, and `immutable` so a browser does not even revalidate. SAFE ONLY BECAUSE THE NAME IS
#: THE CONTENT HASH: change the image and the URL changes, so a stale cache entry is unreachable
#: rather than wrong. The two halves are a single decision and neither is correct alone.
CACHE_CONTROL = "public, max-age=31536000, immutable"

_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp",
        "image/gif": "gif", "image/svg+xml": "svg", "image/avif": "avif"}


@dataclasses.dataclass(frozen=True)
class Asset:
    """One extracted image: its bytes, its served type, and the digest that names it."""
    name: str
    body: bytes
    content_type: str

    @property
    def path(self) -> str:
        return f"/assets/{self.name}"


def digest(body: bytes) -> str:
    """16 hex chars of sha256 over the DECODED bytes.

    Over the decoded bytes rather than the base64 text so that two spellings of the same image
    -- different padding, different line wrapping -- resolve to one cache entry. 64 bits is far
    past collision concern for a handful of images and keeps the URL readable.
    """
    return hashlib.sha256(body).hexdigest()[:16]


def externalize(html: str) -> tuple[str, dict[str, Asset]]:
    """Rewrite every inline image data URI to a content-addressed path.

    Returns the rewritten page and `{name: Asset}` for the caller to serve. Pure: it reads
    nothing from disk and writes nothing, so the same input always yields the same output and
    the same names.

    A URI whose base64 does not decode is LEFT EXACTLY AS IT WAS. Rewriting it would turn a
    broken-looking image into a 404, which is strictly harder to diagnose -- and `asset_data_uri`
    already treats unreadable assets as "draw without it", so a damaged URI is a case the page
    is designed to survive.
    """
    found: dict[str, Asset] = {}

    def swap(match: re.Match) -> str:
        mime, b64 = match.group(1), match.group(2)
        try:
            body = base64.b64decode(b64, validate=True)
        except (binascii.Error, ValueError):
            return match.group(0)
        if not body:
            return match.group(0)
        name = f"{digest(body)}.{_EXT.get(mime, 'bin')}"
        found[name] = Asset(name, body, mime)
        return f"/assets/{name}"

    return DATA_URI.sub(swap, html), found


def savings(before: str, after: str) -> dict:
    """What the rewrite actually bought, in bytes. Reported, never estimated."""
    b, a = len(before.encode()), len(after.encode())
    return {"before": b, "after": a, "saved": b - a,
            "ratio": (a / b) if b else 1.0}
