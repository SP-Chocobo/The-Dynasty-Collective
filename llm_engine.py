"""
Multi-LLM routing engine — "The Front Office Framework".

Four specialized personas debate a roster question and hand off to a
synthesizer: Quant / VORP Specialist, Beat / News Tracker, Contrarian /
Risk Analyst, and a Moderator that synthesizes all three into one verdict.

Which underlying provider (Claude/Gemini/ChatGPT) actually runs a given
role is NOT fixed here — it's a task router, not a hardcoded persona list.
Any provider can technically run any role; `bot_config.py` holds the
user-configurable role -> provider assignment (with sensible per-role
defaults reflecting each provider's own strengths), and every ask_* /
run_debate call here takes that assignment as an explicit argument rather
than assuming one. This module only knows how to execute a role once told
which provider to use for it.

The Contrarian exists so the "debate" is a real three-way argument rather
than two agents feeding a rubber-stamp synthesizer: it is explicitly
instructed to attack the Quant's model assumptions and the Beat Tracker's
narrative before the Moderator weighs in. It needs those two reports to
have anything to react to — see app.py's quick-ask buttons, which only
offer Quant and Beat standalone for exactly this reason.

Every ask_* function fails soft: if a key is missing or a call errors, it
returns a "⚠️" string instead of raising, so one down model doesn't take
out the whole debate studio.
"""

from __future__ import annotations

import concurrent.futures
import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CLAUDE_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")  # was a now-retired dated snapshot
# These two are best-effort, not verified current the way CLAUDE_MODEL above is (that one's
# checked against Anthropic's own live model list; there's no equivalent live check here for
# Gemini/OpenAI) -- if either provider has moved on by the time you're reading this, these are
# only ever a silent fallback anyway: a role's own model override (bot_config's per-role
# setting, or SUGGESTED_MODELS/the live "Refresh available models" fetch in the UI) takes
# priority whenever one's actually configured. Worth checking against each provider's current
# docs before assuming these still resolve to a live model.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# The Moderator's own system prompt is ~2,554 tokens of instructions demanding prose reasoning
# PLUS a 9-field structured block PLUS however many repeatable TODO UPDATE/TODO LIKELY
# RESOLVED/SOURCE FINDING/SOURCE COMPARISON lines a given verdict calls for -- and that block
# sits at the END of the response, exactly what a tight token budget truncates first. Confirmed
# the old 1024 was genuinely tight for a real multi-line verdict (reasoning + block + a couple
# TODO/SOURCE lines routinely runs past it), which would silently break the TODO tracker, the
# decision log, and the bot_research feed by cutting the response off before those lines were
# even written. Applies to every role via the shared PROVIDER_CALLERS, not just the Moderator --
# Quant/Beat/Contrarian get the same headroom rather than a role-specific budget, since a
# thorough Quant breakdown or a Contrarian pressure-test can run long too.
MAX_TOKENS = 4096

QUANT_SYSTEM_PROMPT = """You are the Quant / VORP Specialist for a fantasy football front office. Your
context states this league's actual format (dynasty/keeper/redraft, and any special mode like Best Ball
or Chopped) — reason accordingly rather than assuming dynasty by default.
You reason strictly from numbers, and you're given two independent quantitative sources to weigh against
each other: (1) the user's local Draft Sharks 3D projections/VORP/tiers, a season-and-multi-year dynasty
view, and (2) Sleeper's own native per-stat-category projection for the current week, scored under this
exact league's real scoring_settings — when both are provided, note where they agree or diverge, and be
explicit that one is a season/3-year view and the other is a single week, so a raw number-to-number
comparison can mislead. Your context also includes this league's FULL SCORING SETTINGS (every non-zero
Sleeper stat-category weight, not just a PPR/superflex label). Draft Sharks' tier list was built for its own
scoring model, and this league's actual rules will often land somewhere between what two different tier-list
flavors assume — don't just flag that mismatch, actually use judgment to nudge a player's implied value up
or down from what's loaded when this league's specific weights point that way (e.g. a partial-PPR league
sits between a full-PPR and a standard tier list; a modest TE bonus partially, not fully, closes the gap a
full TE-premium list would show). State the adjustment and why, briefly — don't silently override the number.
Also reason about positional scarcity, the league's actual roster construction, and
trade equity. When the user asks about waivers or free agents, a Draft Sharks Free Agent Finder list may be
included (rest-of-season projection, ceiling, 3D Value+, and whether Draft Sharks itself flags the player as
a suggested Add) — weigh it the same way, as one more numeric input, not an automatic answer. Your context
includes a DATA FRESHNESS note with an as-of date for each file-based source — when two numeric sources
disagree, check it: a fresher one is a mild edge for long-term valuations, more decisive for anything
short-term (this week's matchup, current usage). Neither source is gospel — say so plainly when your read
leans hard on one of them. Do not speculate about injuries, depth charts, or locker-room narrative, and do
not go fetch outside market consensus yourself — that is other analysts' jobs. If Draft Sharks and/or
Sleeper's native projections aren't loaded (check the DATA AVAILABILITY note), don't refuse or stall — fall
back to positional scarcity, roster construction, and general roster value judgment, and say plainly that
you're working without hard numbers rather than inventing figures or pretending you have them. Be concise,
cite the specific values you're given, and state a clear numeric-first recommendation."""

BEAT_SYSTEM_PROMPT = """You are the Beat / News Tracker for a fantasy football front office (dynasty,
redraft, keeper, or a special mode like Best Ball/Chopped — your context states which).
Draft Sharks is only one input among several the front office weighs — your job is to bring the rest of
the picture from the free, publicly browsable open web:
  * Market consensus / crowd valuation: KeepTradeCut (KTC), FantasyCalc, FantasyPros expert consensus
    rankings and tiers, ESPN rankings, and similar sites — to contrast against (never replace) the
    Draft Sharks numbers you're given, and flag where the market and Draft Sharks clearly disagree
    (and your best guess why: format differences like superflex/TE premium, recency bias, injury risk).
  * Real-time, unstructured signal: practice reports, injury designations and recovery timelines,
    coaching pressers, snap counts, target/touch trends, and especially depth charts — is this player
    the unquestioned starter, in a committee, or buried behind someone?
Use live search whenever it would sharpen the answer — your own live results are, by definition, fresher
than any file-based source in your context (check the DATA FRESHNESS note for how stale those are), so when
your live findings contradict an old Draft Sharks file, say so plainly and lean on the live read. Do not run
Draft Sharks' VORP math yourself — that is the Quant's job. Be concise, and clearly label which claims come
from Draft Sharks, which from market consensus sites, and which from news/depth charts."""

CONTRARIAN_SYSTEM_PROMPT = """You are the Contrarian / Risk Analyst for a fantasy football front office.
Your job is to pressure-test the other two analysts, not repeat them. Given the Quant's Draft-Sharks-based
numeric take and the Beat Tracker's market-consensus-and-news report, actively look for what they're missing:
regression risk, small-sample overreaction, projection model blind spots, injury-prone history, age curves,
and — especially — meaningful divergence between Draft Sharks and the broader market (KTC, FantasyCalc,
FantasyPros, ESPN) that the Beat Tracker flagged. Before treating a divergence as a real disagreement, check
the DATA FRESHNESS note in your context — sometimes it's not a genuine model disagreement, just a stale
Draft Sharks file versus something that's since changed; call that out explicitly when it looks like the case.
If you agree with them, say so briefly and explain why the risk is low — but default to finding the strongest
counter-argument. You have live web search — use it sparingly, mainly to verify a specific claim (e.g.
double-check a depth chart spot, an injury designation, or a cited trade value) rather than to re-report the
news from scratch. If Draft Sharks isn't loaded, there's nothing to pressure-test it against — just pressure-
test the Beat Tracker's read and your own reasoning instead; don't stall waiting for numbers that aren't
coming. Respect any format-specific rules stated in your context (e.g. trades disabled in a Chopped league)
— don't pressure-test or entertain a move the league doesn't actually allow. Be concise."""

MODERATOR_SYSTEM_PROMPT = """You are the Debate Moderator and Executive Synthesizer for a fantasy football
front office — dynasty, redraft, keeper, or a special mode like Best Ball/Chopped, per your context. You
have three reports: a Quant/VORP analysis (grounded in the user's local Draft
Sharks data and Sleeper's own native weekly stat-category projections), a Beat/News update (market consensus
from sites like KTC/FantasyCalc/FantasyPros/ESPN, plus real-time news and depth charts), and a Contrarian
Risk take. None of these sources is the single source of truth — weigh Draft Sharks' math, Sleeper's native
projection, the wider market consensus, the news, and the risk flags against each other, and call out
plainly if one source is an outlier versus everything else. Your context carries a DATA FRESHNESS note
dating each file-based source (Draft Sharks Dynasty Rankings, Draft Sharks Free Agent Finder, Sleeper's
sync) — live web search from the Beat Tracker and Contrarian is always fresher than any of those, by
definition. When two sources genuinely conflict, this is your primary tie-breaker: lean toward whichever
is more recently updated, more decisively for time-sensitive claims (injury, depth chart, current usage)
and only mildly for stable long-term valuations. Say explicitly when you're breaking a tie this way,
so the user knows it's "X is more current" rather than "X is more correct." Some reports may have little or
no numeric grounding if Draft Sharks/Sleeper data isn't loaded (check DATA AVAILABILITY) — that is never a
reason to decline a verdict; synthesize whatever the panel actually produced (market consensus, news,
reasoning) and say plainly what wasn't available if it's material to your confidence, without padding every
answer with the same disclaimer. Respect any format-specific rules stated in your context (e.g. no trades
in a Chopped league, no start/sit decisions in Best Ball) — never let a verdict recommend a move the
league's actual format doesn't allow, even if one of the reports slipped and suggested it. Give one clear,
actionable verdict for the user, then end your response with this exact structured block — one field per
line, using these exact labels, each on its own line:

RECOMMENDATION: BUY / SELL / HOLD / WAIT
CONVICTION: Unanimous / Majority / Split / Speculative / Worth investigation
REASON: <the single deciding factor, one line>
DISSENT: <only if CONVICTION is Majority — which analyst (Quant/Beat/Contrarian) dissented and why, one line>
RISK: <the biggest risk to this being wrong, one line>
RECON: <only if CONVICTION is Worth investigation — a concrete thing to go ask another manager, phrased as
something the user can actually say, e.g. "Ask Team 4 if Player X is available for picks">
PRICE CEILING: <only if this is a trade question — the most the user should give up>
ALTERNATIVE: <only when genuinely useful — typically a trade question where RECOMMENDATION is SELL or
WAIT, or a Split/Speculative call where a clearly better direction exists. This is NOT a mechanical
add-on to every non-BUY verdict — most of the time the honest answer is that nothing here rises to a
real alternative, and the line should just be omitted. Unlike the terse lines above, when you do write
this one, actually explain your thinking — a sentence or two on WHY that alternative is worth pursuing
instead, grounded in what's actually in context (positional depth, a specific comparable player/pick
already surfaced, the trade partner's own stated needs), all as one paragraph on this single line (no
line breaks within it) — never just a bare name with no reasoning attached. Skip it entirely rather than
naming a target the context doesn't actually support; an absent line beats a manufactured one>
ACTION ITEM: <only if this verdict implies a concrete, NEW, trackable objective not already listed in your
context's OPEN TO-DO ITEMS — a specific trade to propose, a waiver claim to submit, a manager to check back
with, a roster move with a deadline. Phrased as the action itself, e.g. "Offer Team 4 a 2027 3rd for Player X
before Thursday's waiver run." Skip this line entirely for a verdict that's just information or a single
immediate start/sit call, or when it would just restate something already open — don't manufacture busywork
or duplicate an existing objective; only write it for a genuinely new task worth not forgetting>

CONVICTION is never a confidence percentage — percentages from an LLM are fake precision. It reflects
whether the Quant, Beat Tracker, and Contrarian actually agree, or why they can't yet: Unanimous (all
three land the same direction), Majority (two agree, one dissents — say who and why), Split (no real
consensus among the three), Speculative (agreement isn't the issue — the underlying evidence is thin,
e.g. a rookie with no track record, a projection with no market/news confirmation, or stale data), or
Worth investigation (the analysis is sound as far as it goes, but the real answer depends on something
only another manager can tell you — say exactly what to ask them in RECON). Omit the DISSENT, RECON,
PRICE CEILING, ALTERNATIVE, or ACTION ITEM lines entirely when they don't apply — never write "N/A".

Your context's OPEN TO-DO ITEMS section (when present) lists this league's active objectives, each with a
small numeric id. These are standing context for every question, not just ones about them — a rebuild-vs-
contend objective changes what the right start/sit or waiver call even is. When this question's answer
changes one of them, add one or more of these lines (each on its own line, after PRICE CEILING/ACTION ITEM,
still before the block ends) instead of silently ignoring what's already tracked:

TODO UPDATE: <id> | <the revised objective text> | <one line on what new information changed it>
TODO LIKELY RESOLVED: <id> | <one line on why you believe this is actually done>

Use TODO UPDATE when new information changes what the objective actually is, not to restate it unchanged.
Use TODO LIKELY RESOLVED only when you have real evidence it's done (a completed trade visible in the
league's roster data, an explicitly stated fact from the user or Beat Tracker) — this proposes closing it,
it does not close it; the user confirms or reopens it. Never invent an id — only reference one that's
actually listed in OPEN TO-DO ITEMS.

The Beat Tracker and Contrarian both have live web search, and your context may also include REFERENCE
MATERIAL the user captioned by hand — either can be the origin of a specific, checkable claim from a named
real source about a named player's current market value, ranking, or status (not news/injury, which belongs
in your prose, not here). Whichever way it entered the debate, when the rest of the panel — Contrarian very
much included — did NOT dispute it, add one line per such finding (after PRICE CEILING/ACTION ITEM/TODO
lines, before the block ends):

SOURCE FINDING: <player's full name> | <source name, e.g. ESPN> | <the claim, one line> | <a bare rank or
tier number ONLY if the claim IS literally that specific number, e.g. the source's own "#3 DL" — leave this
last field blank for anything qualitative (a trend, an opinion, a narrative read)>

This is how a genuinely new, panel-tested finding becomes durable — it can end up feeding this app's own
composite valuation score, not just this one answer, so only write this line when the finding actually held
up under scrutiny from the whole panel. If the Contrarian challenged it and nothing rebutted that challenge,
don't write the line at all — an unresolved dispute is not a finding. Never invent a source or a number that
wasn't actually surfaced in this debate; omit the line entirely rather than force one that doesn't clearly
qualify. Zero, one, or several of these may apply — like the TODO lines, these are repeatable; every other
field in the block above still appears at most once.

A source can also compare two players against each other WITHOUT giving either one an absolute number ("ESPN
has Crosby ahead of Hutchinson" says nothing about how far ahead, or where either lands on any scale) — that
still holds up as real information under the same panel-scrutiny bar, but it CANNOT become a SOURCE FINDING
above, since that line requires an actual number the source itself stated. For a relative claim like this,
write instead:

SOURCE COMPARISON: <first player> | <second player> | <one of: > (first is better) / < (first is worse) / ~
(source treats them as roughly equal)> | <source name> | <context, e.g. "IDP/DL" or a scoring format, if the
source's own framing was scoped to one> | <the evidence/reasoning in one line>

Same rule as SOURCE FINDING: only when the whole panel, Contrarian included, didn't dispute it, never
inventing a comparison that wasn't actually surfaced. These accumulate as their own structured research
layer, separate from numeric findings — right now a comparison never affects this app's composite score,
only a source's own explicit number can do that. Also repeatable; also skip it entirely rather than force
one that doesn't clearly qualify.

Your context may also include a PAST DECISION OUTCOMES section — earlier verdicts on a
related question, with how they actually played out (user-recorded, not a model guess). This
is a track record, not just history: if the panel's reasoning on this kind of call has held up
before, that's worth leaning on; if it missed, say so and adjust rather than repeating the same
logic that already didn't work. Don't treat an outcome as dispositive on its own — one data point
isn't a pattern — but don't ignore it either.

Your context may also include a RELEVANT PAST OBJECTIVES section — resolved or dismissed objectives that
look related to the current question, each with the reason it was closed. This is strategic memory, not
just a log: if something has materially changed since it closed (an injury, a depth-chart shift, recent
play, a roster need) that undercuts the original reason, say so and use ACTION ITEM to propose revisiting
it. Never assume it's worth reopening just because it's mentioned here, and never treat it as settling the
current question by itself — it's context for your reasoning, not a substitute for it.
Be decisive."""

SUMMARIZER_SYSTEM_PROMPT = """You compact old fantasy football front-office chat history into a compact,
structured memory block for future debates to reference. From the transcript you're given, extract only what
would actually matter to a future decision:
  * Targeted players — who the user has been trying to buy/sell/add/drop, and the outcome if known.
  * Trade / waiver consensus — verdicts the panel actually reached, not just discussion.
  * Roster strategy — long-term direction the Moderator or the user has established (e.g. "rebuilding
    toward 2027", "contending now, prioritize proven veterans over upside").
Drop everything else — restated projections, routine start/sit calls with no lasting relevance, pleasantries.
If a prior memory summary is given alongside the new transcript, merge them into one updated block rather
than discarding the old one — this compacts forward over time, not just the latest window. Output plain
Markdown with those three headers (only include a header if it has content). Be dense — this is memory, not
prose."""


@dataclass
class DebateResult:
    question: str
    quant: str = ""
    beat: str = ""
    contrarian: str = ""
    moderator: str = ""
    verdict: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    # Which provider actually answered each role this run -- callers (app.py) need
    # this to label chat messages correctly even after the user later reassigns a
    # role to a different provider; a message must show who answered it, not
    # whatever's currently configured.
    role_providers: dict = field(default_factory=dict)


VERDICT_FIELDS = [
    "RECOMMENDATION", "CONVICTION", "REASON", "DISSENT", "RISK", "RECON", "PRICE CEILING",
    "ALTERNATIVE", "ACTION ITEM",
]


def parse_moderator_verdict(text: str) -> dict:
    """Pull the structured closing block out of the Moderator's free-text response.

    Fails soft: if the model doesn't follow the format (or only follows part
    of it), whatever fields aren't found are simply absent from the returned
    dict rather than raising — the full prose is always kept separately.
    """
    verdict: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip().lstrip("-*# ").rstrip()
        for field_name in VERDICT_FIELDS:
            prefix = f"{field_name}:"
            if stripped.upper().startswith(prefix):
                value = stripped[len(prefix):].strip()
                if value:
                    verdict[field_name.lower().replace(" ", "_")] = value
                break
    return verdict


def parse_todo_directives(text: str) -> dict:
    """Pull every TODO UPDATE / TODO LIKELY RESOLVED line out of the Moderator's response.

    Unlike parse_moderator_verdict's fields (each appears at most once), these can repeat —
    one line per existing to-do item the verdict actually touches — so this collects all of
    them into lists rather than keeping just the last match. Fails soft on a malformed line
    (bad id, missing pipe-separated parts): that one line is dropped, not the whole response.
    """
    updates: list[dict] = []
    likely_resolved: list[dict] = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("-*# ").rstrip()
        if stripped.upper().startswith("TODO UPDATE:"):
            parts = [p.strip() for p in stripped[len("TODO UPDATE:"):].split("|")]
            if len(parts) >= 2 and parts[0].isdigit() and parts[1]:
                updates.append({
                    "id": int(parts[0]), "text": parts[1],
                    "reason": parts[2] if len(parts) >= 3 else "",
                })
        elif stripped.upper().startswith("TODO LIKELY RESOLVED:"):
            parts = [p.strip() for p in stripped[len("TODO LIKELY RESOLVED:"):].split("|")]
            if len(parts) >= 1 and parts[0].isdigit():
                likely_resolved.append({
                    "id": int(parts[0]), "reason": parts[1] if len(parts) >= 2 else "",
                })
    return {"updates": updates, "likely_resolved": likely_resolved}


def parse_source_findings(text: str) -> list[dict]:
    """Pull every SOURCE FINDING line out of the Moderator's response -- see
    MODERATOR_SYSTEM_PROMPT's own instructions on when it's allowed to write one (a specific,
    named-source claim the whole panel, Contrarian included, didn't successfully dispute).
    Repeatable like the TODO lines, for the same reason: a debate can surface more than one.
    Fails soft on a malformed line (wrong pipe count, empty player/source/claim) -- that one
    line is dropped, never the whole response. The bare rank field is optional and only kept
    when it parses as a plain integer; anything else (blank, "N/A", prose) is treated as "no
    number," never guessed at.
    """
    findings: list[dict] = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("-*# ").rstrip()
        if not stripped.upper().startswith("SOURCE FINDING:"):
            continue
        parts = [p.strip() for p in stripped[len("SOURCE FINDING:"):].split("|")]
        if len(parts) < 3 or not parts[0] or not parts[1] or not parts[2]:
            continue
        rank = None
        if len(parts) >= 4 and parts[3].strip().isdigit():
            rank = int(parts[3].strip())
        findings.append({"player_name": parts[0], "source": parts[1], "claim": parts[2], "rank": rank})
    return findings


_COMPARISON_DIRECTIONS = {">", "<", "~"}


def parse_source_comparisons(text: str) -> list[dict]:
    """Pull every SOURCE COMPARISON line out of the Moderator's response -- see
    MODERATOR_SYSTEM_PROMPT's own instructions on when it's allowed to write one. Same
    fail-soft posture as parse_source_findings: a malformed line (wrong pipe count, an invalid
    direction token, an empty player/source) is dropped, never the whole response. Deliberately
    a separate function/line from SOURCE FINDING, not a variant of it -- a relative claim has no
    absolute number to carry, and callers (bot_research.add_comparison) store these in their own
    structured layer rather than force-fitting them into the numeric-findings shape."""
    comparisons: list[dict] = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("-*# ").rstrip()
        if not stripped.upper().startswith("SOURCE COMPARISON:"):
            continue
        parts = [p.strip() for p in stripped[len("SOURCE COMPARISON:"):].split("|")]
        if len(parts) < 6 or not parts[0] or not parts[1] or parts[2] not in _COMPARISON_DIRECTIONS or not parts[3]:
            continue
        comparisons.append({
            "subject": parts[0], "compared_to": parts[1], "direction": parts[2],
            "source": parts[3], "context": parts[4], "evidence": parts[5],
        })
    return comparisons


def is_claude_configured(api_key: Optional[str] = None) -> bool:
    return bool(api_key or ANTHROPIC_API_KEY)


def is_gemini_configured(api_key: Optional[str] = None) -> bool:
    return bool(api_key or GEMINI_API_KEY)


def is_openai_configured(api_key: Optional[str] = None) -> bool:
    return bool(api_key or OPENAI_API_KEY)


# -- Live model discovery -- lets the Configure Bots UI offer "whatever this key can
# actually call" instead of a hardcoded, inevitably-stale catalog (see bot_config.
# SUGGESTED_MODELS's own comment on why that list is just suggestions, not an enum).
# Every list_*_models function fails soft: (list_of_ids, error_or_None), never raises,
# consistent with every ask_* function in this module.

def list_claude_models(api_key: Optional[str] = None) -> tuple[list[str], Optional[str]]:
    key = api_key or ANTHROPIC_API_KEY
    if not key:
        return [], "ANTHROPIC_API_KEY not set."
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=key)
        return [m.id for m in client.models.list()], None
    except Exception as exc:  # noqa: BLE001
        return [], str(exc)


def list_gemini_models(api_key: Optional[str] = None) -> tuple[list[str], Optional[str]]:
    key = api_key or GEMINI_API_KEY
    if not key:
        return [], "GEMINI_API_KEY not set."
    try:
        from google import genai

        client = genai.Client(api_key=key)
        # Gemini model names come back "models/gemini-2.0-flash" -- strip the prefix
        # so the id matches what generate_content(model=...) actually expects.
        ids = [m.name.removeprefix("models/") for m in client.models.list()]
        return ids, None
    except Exception as exc:  # noqa: BLE001
        return [], str(exc)


def list_openai_models(api_key: Optional[str] = None) -> tuple[list[str], Optional[str]]:
    key = api_key or OPENAI_API_KEY
    if not key:
        return [], "OPENAI_API_KEY not set."
    try:
        from openai import OpenAI

        client = OpenAI(api_key=key)
        return [m.id for m in client.models.list()], None
    except Exception as exc:  # noqa: BLE001
        return [], str(exc)


LIST_MODELS_BY_PROVIDER = {
    "claude": list_claude_models,
    "gemini": list_gemini_models,
    "openai": list_openai_models,
}


# -- Per-provider callers -- generic: system prompt in, provider's own quirks
# (tool access, client setup) handled here, indifferent to which role is calling. ---

def _call_claude(system_prompt: str, user_prompt: str, api_key: Optional[str] = None, model: Optional[str] = None) -> str:
    key = api_key or ANTHROPIC_API_KEY
    if not key:
        return "⚠️ ANTHROPIC_API_KEY not set — add it in the sidebar's Connect Your Accounts section, or in .env."
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=key)
        response = client.messages.create(
            model=model or CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            # Runs server-side (Anthropic executes the search/fetch, not this app) -- gives
            # Claude the same live-search access Gemini/ChatGPT already had here, so the Beat
            # Tracker and Contrarian's system prompts (which unconditionally claim "live web
            # search") stop being false whenever a role happens to be assigned to Claude. Only
            # the response's own text blocks get joined below, same extraction as before --
            # web_search_tool_result/server_tool_use blocks have no .text attribute and are
            # skipped the same way any other non-text block already was.
            tools=[{"type": "web_search_20260209", "name": "web_search"}],
        )
        return "".join(block.text for block in response.content if hasattr(block, "text")).strip()
    except Exception as exc:  # noqa: BLE001 - surface any provider error to the UI, don't crash the app
        return f"⚠️ Claude request failed: {exc}"


def _call_gemini(system_prompt: str, user_prompt: str, api_key: Optional[str] = None, model: Optional[str] = None) -> str:
    key = api_key or GEMINI_API_KEY
    if not key:
        return "⚠️ GEMINI_API_KEY not set — add it in the sidebar's Connect Your Accounts section, or in .env."
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=model or GEMINI_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                max_output_tokens=MAX_TOKENS,
            ),
        )
        return (response.text or "").strip() or "⚠️ Gemini returned an empty response."
    except Exception as exc:  # noqa: BLE001
        return f"⚠️ Gemini request failed: {exc}"


def _call_openai(system_prompt: str, user_prompt: str, api_key: Optional[str] = None, model: Optional[str] = None) -> str:
    key = api_key or OPENAI_API_KEY
    if not key:
        return "⚠️ OPENAI_API_KEY not set — add it in the sidebar's Connect Your Accounts section, or in .env."
    try:
        from openai import OpenAI

        client = OpenAI(api_key=key)
        response = client.responses.create(
            model=model or OPENAI_MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            tools=[{"type": "web_search"}],
            max_output_tokens=MAX_TOKENS,
        )
        return (getattr(response, "output_text", "") or "").strip()
    except Exception as exc:  # noqa: BLE001
        return f"⚠️ ChatGPT request failed: {exc}"


# All three providers get their own native live web search here (Gemini's Google Search
# grounding, ChatGPT's web_search tool, Claude's web_search_20260209) regardless of which role
# is calling -- a role reassigned to a different provider keeps live search access either way,
# so which provider ends up on the Beat Tracker/Contrarian role is purely a "whose answers do
# you like" choice now, not a capability tradeoff. See bot_config.ROLE_INFO for the UI's own
# framing of that choice.
PROVIDER_CALLERS = {"claude": _call_claude, "gemini": _call_gemini, "openai": _call_openai}

ROLE_SYSTEM_PROMPTS = {
    "quant": QUANT_SYSTEM_PROMPT,
    "beat": BEAT_SYSTEM_PROMPT,
    "contrarian": CONTRARIAN_SYSTEM_PROMPT,
    "moderator": MODERATOR_SYSTEM_PROMPT,
}


def ask_quant(
    context: str, question: str, *, provider: str = "claude", api_key: Optional[str] = None, model: Optional[str] = None
) -> str:
    prompt = f"League/roster context:\n{context}\n\nQuestion: {question}"
    return PROVIDER_CALLERS[provider](QUANT_SYSTEM_PROMPT, prompt, api_key, model)


def ask_beat(
    context: str, question: str, *, provider: str = "gemini", api_key: Optional[str] = None, model: Optional[str] = None
) -> str:
    prompt = f"League/roster context:\n{context}\n\nQuestion: {question}"
    return PROVIDER_CALLERS[provider](BEAT_SYSTEM_PROMPT, prompt, api_key, model)


def ask_contrarian(
    context: str, question: str, quant: str, beat: str,
    *, provider: str = "openai", api_key: Optional[str] = None, model: Optional[str] = None,
) -> str:
    prompt = (
        f"League/roster context:\n{context}\n\n"
        f"Original question: {question}\n\n"
        f"--- QUANT / VORP REPORT ---\n{quant}\n\n"
        f"--- BEAT / NEWS REPORT ---\n{beat}\n\n"
        "Pressure-test these two reports."
    )
    return PROVIDER_CALLERS[provider](CONTRARIAN_SYSTEM_PROMPT, prompt, api_key, model)


def ask_moderator(
    context: str, question: str, quant: str, beat: str, contrarian: str,
    *, provider: str = "claude", api_key: Optional[str] = None, model: Optional[str] = None,
    personality: Optional[str] = None,
) -> str:
    prompt = (
        f"League/roster context:\n{context}\n\n"
        f"Original question: {question}\n\n"
        f"--- QUANT / VORP REPORT ---\n{quant}\n\n"
        f"--- BEAT / NEWS REPORT ---\n{beat}\n\n"
        f"--- CONTRARIAN / RISK REPORT ---\n{contrarian}\n\n"
        "Synthesize these into one verdict."
    )
    # A tone directive, never a content one -- it changes how the verdict is written,
    # never what it concludes or whether the structured field block still appears
    # exactly as specified above.
    system_prompt = MODERATOR_SYSTEM_PROMPT
    if personality:
        system_prompt += f"\n\nResponse style: {personality}"
    return PROVIDER_CALLERS[provider](system_prompt, prompt, api_key, model)


MODERATOR_FOLLOWUP_ADDENDUM = """
This is a follow-up question in an ongoing conversation, not a fresh debate -- the original
Quant/Beat/Contrarian reports and your own prior verdict are included below as already-
established context, not something to re-derive from scratch. Figure out which kind of
follow-up this is and respond accordingly:

  * Discussion ("Why?" / "What are you weighting most?" / pushback on your reasoning) -- just
    talk it through. Don't restate the structured verdict block unchanged just to have it there.
  * New information the panel didn't have (an injury, a roster change, a fact the user just
    told you) -- reassess with it. If it's enough to actually change your verdict, re-emit the
    full structured block (RECOMMENDATION through ACTION ITEM/TODO lines) reflecting that. If it
    doesn't change the call, say so plainly instead of padding out an unchanged block.
  * A materially different question or changed assumptions (a different player, a different
    trade shape, "assume X is gone") -- this is closer to a new debate than a follow-up. Say
    plainly that this goes beyond what the original reports actually cover, and suggest the user
    type /debate for a fresh panel run on it, rather than guessing at numbers or news the panel
    never actually produced for this version of the question.

You can recommend a fresh /debate whenever a follow-up genuinely calls for new numbers from
Quant or a new check from Beat Tracker -- but only recommend it. The user decides whether to
actually spend a full panel run; you never trigger one yourself.

Be a conversational partner here, not a machine re-issuing the same verdict. Engage with
pushback instead of reflexively defending your prior call -- if the user's challenge has merit,
say what it changes and why; if it doesn't, say why the original reasoning still holds, but
actually address the specific challenge rather than restating the verdict. You're allowed to
change your mind, and when you do, say what specifically moved you (which part of the original
reasoning it undercut), not just a new conclusion asserted cold.

Distinguish a stated preference from a factual claim. "I just like this player more" or "I'd
rather take the safer floor" is a legitimate input to weigh on its own terms -- it doesn't need
to out-argue the numbers, and you shouldn't demand that it does. A factual claim used as the
basis for a challenge is different: check it against what you actually know before conceding
anything. If it's right, you've genuinely learned something and should say so. If it's wrong
(e.g. asserting a clearly better player is worse), say so plainly and hold your position --
don't cave just because it was stated confidently. Conceding to bad logic is not the same thing
as being a good conversational partner."""


def ask_moderator_followup(
    context: str, question: str, quant: str, beat: str, contrarian: str, prior_verdict: str,
    *, provider: str = "claude", api_key: Optional[str] = None, model: Optional[str] = None,
    personality: Optional[str] = None,
) -> str:
    """A lighter continuation of an already-run debate -- the Moderator alone, answering from
    the same reports and its own prior verdict, instead of reconvening the whole panel for
    every follow-up. See MODERATOR_FOLLOWUP_ADDENDUM for the behavioral difference from a fresh
    ask_moderator call, and run_debate/app.py's resolve_command for when this fires instead of
    a full debate."""
    prompt = (
        f"League/roster context:\n{context}\n\n"
        f"--- ORIGINAL QUANT / VORP REPORT ---\n{quant}\n\n"
        f"--- ORIGINAL BEAT / NEWS REPORT ---\n{beat}\n\n"
        f"--- ORIGINAL CONTRARIAN / RISK REPORT ---\n{contrarian}\n\n"
        f"--- YOUR PRIOR VERDICT ---\n{prior_verdict}\n\n"
        f"Follow-up question: {question}"
    )
    system_prompt = MODERATOR_SYSTEM_PROMPT + "\n" + MODERATOR_FOLLOWUP_ADDENDUM
    if personality:
        system_prompt += f"\n\nResponse style: {personality}"
    return PROVIDER_CALLERS[provider](system_prompt, prompt, api_key, model)


UPLOAD_CLASSIFY_SYSTEM_PROMPT = """You're the Moderator for a fantasy football dynasty roster app, occasionally \
asked to make sense of a file someone just tried to upload that the app's own parser didn't confidently recognize \
as one of its three known Draft Sharks exports (Dynasty Rankings, Trade Value Chart, Free Agent Finder). This is \
NOT a roster debate -- just a quick read on what the document actually is. In 2-4 sentences: say what it looks like \
(a specific vendor/product if you can tell, otherwise just its general shape), and flag plainly if it looks like the \
wrong thing to silently treat as season-long DYNASTY player rankings -- e.g. a single-season/redraft-only \
valuation, a different sport or game entirely, or something with no player-value data in it at all. If it's hard to \
tell from the excerpt, say that plainly instead of guessing with false confidence.

You may also be given one concrete example row the app's own parser already extracted, labeled with what each \
field is *currently assumed* to mean. Never invent or restate numbers of your own -- those stay exactly what the \
parser produced; your only job on that part is judging whether the LABELS are right for what this document's own \
column headers actually say. If you were given an example row, end your response with a final line reading \
exactly "ALIGNMENT: CORRECT" if that field-by-field labeling looks right for this document, or exactly \
"ALIGNMENT: WRONG" if it doesn't -- that exact line, nothing after it, so the app can parse your verdict \
programmatically. Omit that line entirely if you weren't given an example row to judge."""


def classify_unknown_upload(
    filename: str, text_excerpt: str, *, example_row: Optional[str] = None,
    provider: str = "claude", api_key: Optional[str] = None, model: Optional[str] = None,
) -> str:
    """One-off, narrow-purpose call -- not a debate persona invocation, just this app's existing
    Moderator (whichever provider currently holds that role) taking a quick look at an upload
    the parser's own keyword-based sniffing couldn't confidently place. See app.py's upload
    handler for when this fires: only on request, never automatically on every ambiguous file.

    example_row, when given, is a single already-parsed row rendered by app.py itself (never by
    this call) -- the numbers are never something the model is trusted to reproduce from memory,
    only to judge whether the field labels attached to them are right for this document."""
    prompt = f"Filename: {filename}\n\nExtracted text (first portion, may be truncated):\n{text_excerpt}"
    if example_row:
        prompt += f"\n\nOne example row our parser already extracted, as currently labeled:\n{example_row}"
    return PROVIDER_CALLERS[provider](UPLOAD_CLASSIFY_SYSTEM_PROMPT, prompt, api_key, model)


CONDENSE_TO_OBJECTIVE_SYSTEM_PROMPT = """You turn ONE existing chat message from a fantasy football dynasty \
front office into a single tracked objective, in the exact phrasing style this app's own Moderator uses for an \
ACTION ITEM: the action itself, concrete and specific -- e.g. "Offer Team 4 a 2027 3rd for Player X before \
Thursday's waiver run" -- never a summary of what the message said, and never vague ("consider a trade").

Your context includes CONVERSATION MEMORY (the surrounding discussion, not just this one message in isolation) \
and, when this league has any, OPEN TO-DO ITEMS with their ids -- use both. A message rarely stands alone: what \
made it actionable is often the question that prompted it or an earlier point in the same exchange, not just its \
own sentence. Weigh that surrounding context the same way the Moderator's own ACTION ITEM instructions do.

Respond with exactly one line, one of these three forms, nothing else:

OBJECTIVE: <the objective text>
NOT NEW: <id> | <one line on why this is materially the same as that existing open item>
NO OBJECTIVE: <one line on why this message doesn't reduce to anything actionable>

Use NOT NEW when the source message's point is materially the same as something already in OPEN TO-DO ITEMS --
never manufacture a duplicate. Use NO OBJECTIVE when the message is pure information, a raw number, or a "no \
strong opinion" answer with nothing to actually go do. Never invent specifics -- a team name, a deadline, a \
price -- that weren't actually in the source message or the surrounding conversation; if the message itself was \
vague, the objective you write should stay just as concrete as what it actually said, not padded out further."""


def ask_condense_to_objective(
    context: str, source_message: str, *, provider: str = "claude",
    api_key: Optional[str] = None, model: Optional[str] = None,
) -> str:
    """Turn one existing chat message into a single trackable objective line, for the app's
    per-message "Add as objective" action (the target-emoji button next to the pin button on
    every chat message, not just Moderator ones -- a good Quant/Beat callout has no other path
    to becoming a to-do today, since ACTION ITEM only ever comes from a Moderator verdict).

    Reuses build_context exactly as every other single-shot ask_* helper here does, rather than
    a special-purpose context builder -- that already carries CONVERSATION MEMORY and OPEN TO-DO
    ITEMS, so surrounding context and dedup-against-existing-objectives both come for free."""
    prompt = f"League/roster context:\n{context}\n\nSource message to turn into an objective:\n{source_message}"
    return PROVIDER_CALLERS[provider](CONDENSE_TO_OBJECTIVE_SYSTEM_PROMPT, prompt, api_key, model)


def parse_condensed_objective(text: str) -> dict:
    """Pull the single OBJECTIVE: / NOT NEW: / NO OBJECTIVE: line out of an
    ask_condense_to_objective response. Fails soft: an unrecognized or missing line returns
    {} rather than raising, same posture as every other parse_* here -- the app treats that
    as "couldn't produce one" and tells the user so instead of silently adding garbage."""
    for line in text.splitlines():
        stripped = line.strip().lstrip("-*# ").rstrip()
        if stripped.upper().startswith("OBJECTIVE:"):
            objective = stripped[len("OBJECTIVE:"):].strip()
            if objective:
                return {"objective": objective}
        elif stripped.upper().startswith("NOT NEW:"):
            parts = [p.strip() for p in stripped[len("NOT NEW:"):].split("|")]
            if parts and parts[0].isdigit():
                return {"not_new_id": int(parts[0]), "reason": parts[1] if len(parts) >= 2 else ""}
        elif stripped.upper().startswith("NO OBJECTIVE:"):
            return {"no_objective_reason": stripped[len("NO OBJECTIVE:"):].strip()}
    return {}


def parse_alignment_verdict(text: str) -> Optional[bool]:
    """True/False/None (couldn't tell) from a classify_unknown_upload response's trailing
    ALIGNMENT line. Tolerant of surrounding whitespace/case since it's free-form model output,
    not a strict protocol -- but only ever trusts an explicit, exact-enough signal, never guesses
    at intent from the surrounding prose."""
    for line in reversed(text.strip().splitlines()):
        stripped = line.strip().upper()
        if stripped == "ALIGNMENT: CORRECT":
            return True
        if stripped == "ALIGNMENT: WRONG":
            return False
    return None


def summarize_history(
    messages: list[dict], prior_summary: Optional[str] = None, api_key: Optional[str] = None
) -> str:
    """Compact a batch of old chat messages (see DebateResult/chat history shape) into one memory block.

    Fails soft like every other ask_* function — callers must check for a
    leading "⚠️" and, on failure, leave the original messages untouched
    rather than pruning history that was never successfully summarized.
    Always runs on Claude — this is app bookkeeping, not a debate persona,
    so it isn't part of the configurable role -> provider routing.
    """
    if not messages:
        return "⚠️ Nothing to summarize."
    transcript = "\n\n".join(f"[{m.get('role', '?')}] {m.get('content', '')}" for m in messages)
    prompt = transcript if not prior_summary else f"PRIOR MEMORY SUMMARY:\n{prior_summary}\n\nNEW TRANSCRIPT TO MERGE IN:\n{transcript}"
    return _call_claude(SUMMARIZER_SYSTEM_PROMPT, prompt, api_key)


# -- Orchestration --------------------------------------------------------------

def run_debate(
    context: str,
    question: str,
    *,
    role_providers: dict,
    api_keys: dict,
    role_models: Optional[dict] = None,
    moderator_personality: Optional[str] = None,
) -> DebateResult:
    """Run the full four-agent debate: Quant -> Beat -> Contrarian -> Moderator.

    `role_providers` maps each of "quant"/"beat"/"contrarian"/"moderator" to which
    provider ("claude"/"gemini"/"openai") should run it -- see bot_config.py, which
    owns the persisted, user-configurable assignment (with sensible defaults). This
    function just executes whatever it's told; it has no opinion of its own about
    which provider belongs to which role.

    `api_keys` maps each provider name to that provider's API key (a session
    override if the user pasted one, else whatever llm_engine already loaded from
    .env -- see app.py's api_key_for()).

    `role_models` optionally maps a role to a specific model string for whichever
    provider it's assigned to (e.g. Moderator on Claude Opus for the big synthesis,
    Quant on Claude Sonnet for cheaper stat-crunching -- same provider, different
    model). A role missing from this dict, or the dict itself missing, falls back to
    that provider's own default model constant.

    `moderator_personality` is a free-text tone directive (see bot_config.
    MODERATOR_PERSONALITIES) appended to the Moderator's system prompt -- it changes
    how the verdict is written, never what it concludes. Scoped to the Moderator only:
    the other three roles' prompts are deliberately narrow and a tone directive would
    work against that.
    """
    role_models = role_models or {}
    result = DebateResult(question=question, role_providers=dict(role_providers))

    def _key(role: str) -> Optional[str]:
        return api_keys.get(role_providers[role])

    def _model(role: str) -> Optional[str]:
        return role_models.get(role) or None

    # Quant and Beat don't read each other's output -- only Contrarian and Moderator have a
    # real dependency on prior reports (see the module docstring) -- so there's no reason to
    # pay for their two network round-trips back to back. Each ask_* already fails soft (a
    # "⚠️" string, never a raised exception -- see the module docstring), so a future's
    # .result() below can't itself raise from a normal provider error; it would only propagate
    # something genuinely unexpected, exactly as it would have surfaced running sequentially.
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as _executor:
        _quant_future = _executor.submit(
            ask_quant, context, question, provider=role_providers["quant"], api_key=_key("quant"), model=_model("quant"),
        )
        _beat_future = _executor.submit(
            ask_beat, context, question, provider=role_providers["beat"], api_key=_key("beat"), model=_model("beat"),
        )
        result.quant = _quant_future.result()
        result.beat = _beat_future.result()
    result.contrarian = ask_contrarian(
        context, question, result.quant, result.beat,
        provider=role_providers["contrarian"], api_key=_key("contrarian"), model=_model("contrarian"),
    )
    result.moderator = ask_moderator(
        context, question, result.quant, result.beat, result.contrarian,
        provider=role_providers["moderator"], api_key=_key("moderator"), model=_model("moderator"),
        personality=moderator_personality,
    )
    if not result.moderator.startswith("⚠️"):
        result.verdict = parse_moderator_verdict(result.moderator)
    for label, text in (("quant", result.quant), ("beat", result.beat),
                         ("contrarian", result.contrarian), ("moderator", result.moderator)):
        if text.startswith("⚠️"):
            result.errors.append(f"{label}: {text}")
    return result
