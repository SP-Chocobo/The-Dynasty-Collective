"""
Durable logs of panel-vetted output from the debate bots' own live web search (or the user's
own captioned reference material -- either can originate one) -- see
llm_engine.MODERATOR_SYSTEM_PROMPT's SOURCE FINDING / SOURCE COMPARISON instructions for
exactly when the Moderator is allowed to write one: a specific, named-source claim that the
whole panel, Contrarian very much included, did not successfully dispute. Both are global and
git-tracked, unlike decision_log/todo_log's per-league, gitignored JSON -- neither is scoped to
one league, and the entire point is for them to persist across sessions the same durable way
the rest of data/baseline/ does.

Two separate stores, deliberately not one shape stretched to cover both:

  * findings (FINDINGS_PATH) -- a claim about ONE player. When it carries a real rank number
    the source itself stated (never inferred), it also feeds DataMerger's composite score at a
    low weight, not just future debates' reference context; a qualitative claim never does.
  * comparisons (COMPARISONS_PATH) -- a RELATIVE claim between two players ("ESPN has Crosby
    ahead of Hutchinson"), which has no absolute number to feed a composite with at all. Kept
    as its own structured research layer -- composite_impact is always "none" today, an
    explicit stored fact rather than a silent omission. The reasoning for staying out of the
    composite for now: a handful of debate-surfaced comparisons is nowhere near KTC's millions
    of votes, and running an Elo/Bradley-Terry-style model on that thin a sample would produce
    noise dressed up as precision. If comparisons accumulate real volume and connectivity over
    time, a genuinely separate relative-valuation model built from them is a real future option
    -- deliberately not attempted here.

Both are append-only: a later entry about the same player(s)/source doesn't overwrite or
delete an earlier one, it just outranks it at READ time where that matters (see DataMerger's
newest-wins handling for findings) -- the full log stays a real record of what the panel has
found over time, not just today's latest opinion.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import store_io


FINDINGS_PATH = Path("data/baseline/bot_research.json")
COMPARISONS_PATH = Path("data/baseline/bot_comparisons.json")


def _load(path: Path) -> list[dict]:
    # #102: atomic, locked, and no longer able to turn a torn read into an empty store. That
    # mattered most here: these two files are git-tracked application data, and a rank-bearing
    # finding feeds the composite valuation score.
    return store_io.read(path, [])


def _save(path: Path, entries: list[dict]) -> None:
    store_io.write(path, entries)


def _next_id(entries: list[dict]) -> int:
    return (max((e.get("id", 0) for e in entries), default=0)) + 1


def load_findings() -> list[dict]:
    return _load(FINDINGS_PATH)


# The three states a stored finding's origin can be in, and the reason there are three rather
# than two (#106, §16.5). "The panel searched the web" and "the user captioned a screenshot" were
# indistinguishable here -- build_context's own prose said so out loud, hedging every finding with
# "whether that was a bot's live search or the user's own reference material". A finding now
# carries what the PROVIDER RESPONSES reported retrieving while it was produced, so the first
# case is evidenced rather than assumed.
#
# UNATTRIBUTED is not a failure state and must never be read as one. It is the honest answer for
# a finding produced by a debate whose responses reported no retrieval -- which covers a chair
# reasoning from the context it was given, a chair reasoning from its own training, a provider
# that reports grounding in a shape this app could not read, and a call that simply did not
# search. Those are four different things and nothing here can separate them; collapsing them
# into "no sources" would be the same false precision this app removed everywhere else.
ORIGIN_PANEL_RETRIEVED = "panel_retrieved"   # the debate's responses reported these pages
ORIGIN_UNATTRIBUTED = "unattributed"         # they reported none; see above for what that covers


@store_io.atomic(lambda *a, **k: FINDINGS_PATH)
def add_finding(
    player_name: str, source: str, claim: str, *, rank: Optional[int] = None,
    conviction: str = "", question: str = "", league_id: Optional[str] = None,
    debate_sources: Optional[list[dict]] = None,
) -> Optional[int]:
    """Persist one panel-vetted single-player finding. Returns its id, or None if there's
    nothing real to record (blank player/source/claim) -- a no-op, not an error, since the
    Moderator's SOURCE FINDING line is optional and legitimately absent from most verdicts.

    Also a no-op (returns the existing id) for an exact duplicate of a finding already logged
    TODAY -- process_moderator_output runs on every Moderator reply, including a follow-up
    reacting to the same debate, so a re-run /debate or a follow-up that restates its own
    verdict's finding (MODERATOR_FOLLOWUP_ADDENDUM tells it not to, but doesn't guarantee it
    never will) would otherwise append an identical row every time, inflating this finding's
    weight in whatever percentile pool it feeds. Scoped to same-day only, not forever: a
    genuine re-confirmation of a still-true finding days or weeks later is real information --
    see this module's own docstring on why a later entry "outranks" an earlier one at read time
    -- and should still get its own fresh-dated entry so its recency weight actually renews."""
    player_name, source, claim = player_name.strip(), source.strip(), claim.strip()
    if not player_name or not source or not claim:
        return None
    entries = load_findings()
    today = datetime.now().strftime("%Y-%m-%d")
    for entry in entries:
        if (
            entry.get("date") == today and entry.get("player_name") == player_name
            and entry.get("source") == source and entry.get("claim") == claim
            and entry.get("rank") == rank
        ):
            return entry.get("id")
    new_id = _next_id(entries)
    entries.append({
        "id": new_id,
        "ts": time.time(),
        "date": today,
        "player_name": player_name,
        "source": source,
        "claim": claim,
        "rank": rank,
        # Explicit and visible rather than something a reader has to infer from whether
        # `rank` happens to be null -- mirrors comparisons' own composite_impact field below.
        "composite_impact": "low-weight input" if rank is not None else "none",
        "conviction": conviction,
        "question": question,
        "league_id": league_id,
        # §6.5's evidence snapshot, at the scope the evidence actually supports. DEBATE-level,
        # never per-claim: `retrieved` lists what the panel that produced this verdict reported
        # fetching, and NOT which of those pages backs this particular claim. The finding line
        # carries no citation and no join exists; presenting these as this claim's sources would
        # be manufacturing provenance. `retrieved_at` is when this row was written, which is the
        # same debate turn -- it is not the page's own publication or crawl date, and nothing
        # here knows that.
        "evidence": {
            "origin": ORIGIN_PANEL_RETRIEVED if debate_sources else ORIGIN_UNATTRIBUTED,
            "retrieved_at": today,
            "debate_sources": [dict(entry) for entry in (debate_sources or [])],
        },
    })
    _save(FINDINGS_PATH, entries)
    return new_id


def findings_for_context(limit: int = 30) -> list[dict]:
    """Most recent findings first, capped -- for build_context's reference-material-style
    section in app.py, same cap-a-long-history posture as captioned reference material there
    already has, so accumulated findings don't balloon every context payload indefinitely."""
    return sorted(load_findings(), key=lambda e: e.get("ts", 0), reverse=True)[:limit]


def load_comparisons() -> list[dict]:
    return _load(COMPARISONS_PATH)


@store_io.atomic(lambda *a, **k: COMPARISONS_PATH)
def add_comparison(
    subject: str, compared_to: str, direction: str, source: str, *, context: str = "",
    evidence: str = "", question: str = "", league_id: Optional[str] = None,
) -> Optional[int]:
    """Persist one panel-vetted relative claim between two players. direction is one of
    ">" (subject better), "<" (subject worse), "~" (roughly equal), matching
    llm_engine.parse_source_comparisons' own vocabulary. Returns the new entry's id, or None
    if there's nothing real to record (blank subject/compared_to/source, or an unrecognized
    direction) -- a no-op, not an error, since most verdicts legitimately have zero of these.

    Same same-day dedup as add_finding, for the same reason (process_moderator_output runs on
    every Moderator reply, including a follow-up reacting to the same debate) -- this never
    feeds the composite either way (composite_impact is always "none"), but an identical row
    appended every time a debate's re-run or followed up on is still just clutter in the Bot
    Research log for no new information."""
    subject, compared_to, source = subject.strip(), compared_to.strip(), source.strip()
    if not subject or not compared_to or not source or direction not in (">", "<", "~"):
        return None
    entries = load_comparisons()
    today = datetime.now().strftime("%Y-%m-%d")
    for entry in entries:
        if (
            entry.get("date") == today and entry.get("subject") == subject
            and entry.get("compared_to") == compared_to and entry.get("direction") == direction
            and entry.get("source") == source
        ):
            return entry.get("id")
    new_id = _next_id(entries)
    entries.append({
        "id": new_id,
        "ts": time.time(),
        "date": today,
        "subject": subject,
        "compared_to": compared_to,
        "direction": direction,
        "source": source,
        "context": context.strip(),
        "evidence": evidence.strip(),
        "evidence_type": "qualitative comparative",
        # Records WHAT IS KNOWN: the Moderator asserted, by emitting the SOURCE COMPARISON
        # line, that the panel did not dispute this. It is not a verification -- nothing here
        # re-adjudicates the claim, and this code cannot observe the debate that produced it.
        # It was written as "validated": True, which asserted exactly that. Renamed under the
        # rule #89 established for the alias branch (ARCHITECTURE_AUDIT.md 13.3): a stored
        # field may not claim a certainty its writing path cannot establish. Nothing reads it
        # today; test_research_ingestion_boundary fails the moment anything starts to, so it
        # has to be honest before it can be trusted.
        "panel_undisputed": True,
        "composite_impact": "none",  # see this module's own docstring for why, and when that could change
        "question": question,
        "league_id": league_id,
    })
    _save(COMPARISONS_PATH, entries)
    return new_id


def comparisons_for_context(limit: int = 30) -> list[dict]:
    """Most recent comparisons first, capped -- same posture as findings_for_context."""
    return sorted(load_comparisons(), key=lambda e: e.get("ts", 0), reverse=True)[:limit]
