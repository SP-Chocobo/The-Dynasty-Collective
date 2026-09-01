"""One content-hashing primitive, shared.

Extracted from bot_benchmark.py's private `_fingerprint`, unchanged, because a second
consumer arrived (pick_synthesis.snapshot_identity) and two hand-rolled hashers that are
*supposed* to agree but live in different modules is exactly the drift this app has already
been bitten by elsewhere. §17.7/#111 recorded that content-hash identity existed for exactly
one artifact; this is the extraction that lets it cover more than one without forking.

Deliberately a hash rather than a hand-maintained version number: a number has to be
remembered and drifts out of sync with the thing it names, whereas this cannot disagree with
the content it was computed from.

Deliberately dependency-free -- stdlib only, imports nothing from this app. That is what
makes it safe for a CDME module (pick_synthesis) to import: there is no path through this
file by which LLM-originated or persisted data could reach the engine, because there is
nothing here to reach through. See test_cdme_ingestion_boundary.py's import-graph test.
"""

from __future__ import annotations

import hashlib

# Length of the returned hex digest. 12 hex chars = 48 bits. This is a CONTENT IDENTIFIER for
# a local, single-user store, not a security boundary and not a collision-proof key for an
# adversarial namespace: nothing here defends against a party deliberately constructing a
# collision, and nothing should be authorized on the basis of one of these matching.
FINGERPRINT_CHARS = 12


def fingerprint(*parts: str) -> str:
    """A short content hash of exactly the parts given, in the order given.

    Order matters and is part of the identity: ("a", "b") and ("b", "a") hash differently, on
    purpose. Parts are NUL-separated before hashing so that ("ab", "c") and ("a", "bc") also
    differ -- without the separator they would collide, and two genuinely different inputs
    reading as the same identity is the one failure mode this function exists to prevent.
    """
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()[:FINGERPRINT_CHARS]
