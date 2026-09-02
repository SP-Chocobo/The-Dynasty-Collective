"""§7.4: which cited sources may move a number, and which may only be read.

THE GAP, MEASURED. `llm_engine.parse_source_findings` accepts whatever the Moderator writes in
the source field. Run against the real parser, §7.4 recorded:

    SOURCE FINDING: Some Player | totally-not-a-real-site.example/paywalled | ... | 1
      -> accepted: source='totally-not-a-real-site.example/paywalled', rank=1

and there was no SOURCE_ALLOWLIST, PERMITTED_SOURCES or SOURCE_POLICY anywhere in the app. So
§7's question -- *can a model introduce an impermissible source merely because it appears
authoritative?* -- split in two: into the composite via a FILE, no (the loader's own source
table is a code allowlist already); into the durable research record and from there into the
composite via a rank, yes.

THE RULING THIS IMPLEMENTS, and the line it draws. **Allowlist what feeds the composite; prose
stays free.** Those are two different acts and only one of them needs governing:

    a claim a chair READS, quotes, or argues from   -- free text, no policy, never filtered
    a NUMBER that alters composite_player_score     -- must cite a source on this list

Nothing here deletes, hides, or refuses to store a finding. A finding citing an unlisted source
is written to bot_research.json exactly as before, shown in the UI exactly as before, and read
by the panel exactly as before. What it does not do is carry its rank into a score. The
distinction is ROADMAP's own four states arriving one layer down: a claim is not a fact merely
because it was stated confidently, and the gate belongs where the number enters the arithmetic.

WHY *THIS* LIST AND NOT A LONGER ONE. Every entry is a source this repository has already
written a provenance record for -- the four ATTRIBUTION.md files under data/baseline/external/,
plus Sleeper, whose data arrives from its own API rather than a citation. That rule is what
keeps the list from being my opinion about which brands are reputable: a source earns composite
authority by having its origin documented in this repo, and `test_source_policy` fails if the
list and the provenance records ever disagree in either direction. Adding a source is therefore
the same act as documenting it, which is the correct price.

WHY IT IS NOT IN A PROMPT. Telling the Moderator the list would make the model the enforcer, and
§4.6/§8.3 (test_prompt_constant_boundary) already forbids an engine constant reaching a prompt
for the related reason: a rule a model is asked to follow is not a rule the app enforces. The
check runs at the ingestion boundary, on the way into the composite, where it cannot be talked
out of.
"""

from __future__ import annotations

import re

#: canonical name -> the token sequences that name it in free text. Multiple spellings per
#: source because a model writes "KeepTradeCut", "Keep Trade Cut" and "keeptradecut.com" for the
#: same thing, and rejecting a real source over its spacing would be a false negative with a
#: real cost: a genuine panel-vetted finding silently losing its number.
COMPOSITE_ALLOWLIST: dict[str, tuple[tuple[str, ...], ...]] = {
    "espn": (("espn",),),
    "fantasypros": (("fantasypros",), ("fantasy", "pros")),
    "keeptradecut": (("keeptradecut",), ("keep", "trade", "cut"), ("ktc",)),
    "dynastyprocess": (("dynastyprocess",), ("dynasty", "process")),
    #: Not a citation source like the four above -- Sleeper's numbers arrive through its own API
    #: rather than a model quoting them -- but a finding CAN legitimately cite it ("Sleeper has
    #: him as the WR14"), and it is the one origin in this app with a stronger provenance record
    #: than an ATTRIBUTION.md: sleeper_projection_provenance.json carries the scoring rules.
    "sleeper": (("sleeper",),),
}

_TOKEN = re.compile(r"[a-z0-9]+")


def tokens(citation: str) -> tuple[str, ...]:
    """Lowercase alphanumeric runs. Punctuation, domains and possessives all fall apart into
    tokens, which is what makes the match below exact rather than a substring test:
    'espnfake.example' tokenizes to ('espnfake', 'example') and never matches ('espn',)."""
    return tuple(_TOKEN.findall((citation or "").lower()))


def admits(citation: str) -> str | None:
    """The canonical source name a citation names, or None.

    A source matches when one of its spellings appears as a CONSECUTIVE run of tokens, so
    "ESPN's Field Yates" and "per FantasyPros ECR" both match while
    "totally-not-a-real-site.example/paywalled" matches nothing. Consecutive rather than
    subset, because ("keep","trade","cut") scattered across an unrelated sentence is not a
    citation of KeepTradeCut.
    """
    found = tokens(citation)
    for canonical, spellings in COMPOSITE_ALLOWLIST.items():
        for spelling in spellings:
            width = len(spelling)
            if any(found[i:i + width] == spelling for i in range(len(found) - width + 1)):
                return canonical
    return None


def feeds_composite(citation: str) -> bool:
    """Whether a rank cited to this source may enter composite_player_score.

    The single question every caller actually asks, named so the call sites read as the policy
    rather than as a string check.
    """
    return admits(citation) is not None
