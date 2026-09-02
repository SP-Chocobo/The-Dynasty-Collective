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
    the source itself stated (never inferred), that NUMBER may eventually feed DataMerger's
    composite score at a low weight -- but only after clearing two gates it does not clear on
    arrival (7.4's cited-source allowlist and 6.2a's second adjudication; see
    composite_eligibility below). A qualitative claim never feeds it at all. The CLAIM itself is
    ungated in every case: stored, shown, and handed to future debates as reference context
    whether or not its number ever counts.
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
import source_policy
import store_io


FINDINGS_PATH = Path("data/baseline/bot_research.json")
COMPARISONS_PATH = Path("data/baseline/bot_comparisons.json")

# -- what has to be true before a finding's number may move a score ---------------------------
#
# Two rulings, one boundary, because they are the same question asked twice: 7.4 asks WHICH
# SOURCES may move a number, 6.2a asks WHO HAS TO AGREE before one does. A finding must clear
# both, and clearing neither costs it anything except its number -- it is still stored, still
# shown, still read by the panel. Prose stays free; only the arithmetic is gated.

#: 6.2a's states, in the order a finding can travel them. `PANEL_ONLY` is what the Moderator's
#: own gate establishes and it is NOT a second adjudication: app.py's own comment on the persist
#: site says so plainly -- "trusting the Moderator's own gate, not re-verifying it a second time
#: in code". 6.2a asked whether anything re-adjudicates; the answer was no queue and no second
#: adjudication, and this is the smallest honest version of one.
ADJUDICATION_PANEL_ONLY = "panel_only"
ADJUDICATION_HUMAN_CONFIRMED = "human_confirmed"

#: A row written before this gate existed has NO `adjudication` key, and that is a THIRD state:
#: never adjudicated, as distinct from adjudicated-and-not-confirmed. Both are treated as "does
#: not feed", but they are not the same fact and the reader must be able to tell them apart --
#: the never-checked-versus-checked-and-absent distinction (#112) that _finding_origin_note
#: already applies one field over.
ADJUDICATION_UNRECORDED = None


def composite_eligibility(source: str, rank: Optional[int], adjudication: Optional[str]) -> dict:
    """Whether this finding's number may reach composite_player_score, and why not when it may not.

    Returns the three fields a stored finding carries, computed in one place so the record and the
    ingestion filter cannot disagree about a row:

        cited_source_admitted   the canonical allowlisted source, or None            (7.4)
        adjudication            who has agreed so far                                (6.2a)
        composite_impact        the derived answer, in the same vocabulary as before

    WHY BOTH GATES AND NOT EITHER ALONE. The allowlist answers "does this citation name a source
    this repository has documented", which is checkable and mechanical -- and deliberately does
    NOT answer "is this claim true"; a fabricated claim naming ESPN passes it. The second
    adjudication is what stands against that one. Neither is sufficient; together they are the
    smallest gate that is honest about what each half can establish.

    THE BAR THIS RAISES, stated because it is a real behaviour change: a panel-vetted finding no
    longer feeds the composite on the Moderator's own say-so. On this repository that changes
    nothing observable -- the store has never held a row -- but it is the first time the app has
    declined to use something the panel approved. That is the ruling's own logic: an accepted
    finding is exactly the kind of thing that, under a shared substrate, would reach everybody.
    """
    admitted = source_policy.admits(source)
    if rank is None:
        # A qualitative claim has no number to gate. Unchanged, and the reason it reads "none" is
        # the same as it always was.
        reason = "none"
    elif admitted is None:
        reason = "none -- cited source is not on the composite allowlist"
    elif adjudication != ADJUDICATION_HUMAN_CONFIRMED:
        reason = "none -- awaiting a second adjudication"
    else:
        reason = "low-weight input"
    return {
        "cited_source_admitted": admitted,
        "adjudication": adjudication,
        "composite_impact": reason,
    }


def feeds_composite(finding: dict) -> bool:
    """The single question data_merger asks of a stored row.

    Recomputed from the row's own fields rather than trusting its stored `composite_impact`,
    because the stored string is a RECORD of a decision and this is the DECISION -- a row written
    under an older rule must not carry its old eligibility forward just because the string is
    still sitting there. That is the same discipline as recomputing a manifest rather than
    believing it.
    """
    verdict = composite_eligibility(
        finding.get("source", ""), finding.get("rank"), finding.get("adjudication"))
    return verdict["composite_impact"] == "low-weight input"


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
        # 7.4 + 6.2a, computed in one place (composite_eligibility) so the stored record and the
        # ingestion filter cannot disagree about a row. Three fields rather than one, because
        # "this number does not count" has more than one reason and a reader needs to know which:
        # an unlisted cited source is a policy answer, an unconfirmed adjudication is a queue
        # position. Still explicit and visible rather than inferred from whether `rank` happens
        # to be null -- mirrors comparisons' own composite_impact field below.
        **composite_eligibility(source, rank, ADJUDICATION_PANEL_ONLY),
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


@store_io.atomic(lambda *a, **k: FINDINGS_PATH)
def confirm_finding(finding_id: int, *, by: str = "human") -> Optional[dict]:
    """6.2a's second adjudication: a person looks at a stored finding and accepts its number.

    Returns the updated row, or None if there is no such finding. Idempotent -- confirming an
    already-confirmed row rewrites the same values and is not an error, because the caller is a
    UI button and a double-click is not a fact about the finding.

    WHAT THIS IS AND IS NOT. It is not verification of the claim; nothing here can check whether
    ESPN actually ranks that player third. It records that a SECOND party, not the panel that
    produced the finding, looked at it and let its number through. 6.2a's question was whether
    anything re-adjudicates at all, and the answer was no queue and no second adjudication. This
    is the smallest honest one: one more pair of eyes between a model's assertion and a score.

    WHY A HUMAN AND NOT A SECOND MODEL, for now. The ruling's reasoning, kept because it is the
    part that will be re-litigated: under a shared substrate an accepted finding reaches
    EVERYBODY, and ROADMAP's own trust boundary says agreement among models is not corroboration
    when they may all be downstream of one source. A stronger model or a corroboration threshold
    is a legitimate future adjudicator -- ROADMAP names four candidates and picks none -- but
    choosing one now would be answering the deployment question by accretion, which is exactly
    what this repository just spent a session unwinding. So: a person, explicitly "for now".

    Deliberately NO auto-confirm path, no bulk confirm, and no confirm-on-write. Each of those
    would turn the gate back into the thing it replaced.
    """
    entries = load_findings()
    for entry in entries:
        if entry.get("id") != finding_id:
            continue
        entry.update(composite_eligibility(
            entry.get("source", ""), entry.get("rank"), ADJUDICATION_HUMAN_CONFIRMED))
        # Records WHO and WHEN, under the rule #89 established for the alias branch: a stored
        # field may not claim a certainty its writing path cannot establish. "confirmed_by" is
        # honest about being an actor, not an authority.
        entry["confirmed_by"] = by
        entry["confirmed_at"] = datetime.now().strftime("%Y-%m-%d")
        _save(FINDINGS_PATH, entries)
        return dict(entry)
    return None


def findings_awaiting_adjudication() -> list[dict]:
    """Rank-bearing findings whose number is being held back, newest first.

    The queue 6.2a said did not exist -- deliberately a VIEW over the store rather than a second
    file, because a queue that can drift from the thing it queues is a new defect, not a
    mechanism. Includes findings blocked by either gate, since a user looking at this list wants
    to see everything that is not counting and why; `composite_impact` on each row says which.
    """
    return sorted(
        (f for f in load_findings()
         if f.get("rank") is not None and not feeds_composite(f)),
        key=lambda e: e.get("ts", 0), reverse=True,
    )


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
