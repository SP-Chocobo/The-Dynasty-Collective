"""
Multi-LLM routing engine — "The Front Office Framework".

Four specialized personas, each backed by a different model, debate a
roster question and hand off to a synthesizer:

  * Quant / VORP Specialist      -> Claude (Anthropic)   ANTHROPIC_API_KEY
  * Beat / News Tracker          -> Gemini (Google)       GEMINI_API_KEY
  * Contrarian / Risk Analyst    -> ChatGPT (OpenAI)      OPENAI_API_KEY
  * Debate Moderator             -> Claude (Anthropic)   ANTHROPIC_API_KEY

The Contrarian exists so the "debate" is a real three-way argument rather
than two agents feeding a rubber-stamp synthesizer: it is explicitly
instructed to attack the Quant's model assumptions and the Beat Tracker's
narrative before the Moderator weighs in.

Every ask_* function fails soft: if a key is missing or a call errors, it
returns a "⚠️" string instead of raising, so one down model doesn't take
out the whole debate studio.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CLAUDE_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

MAX_TOKENS = 1024

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

CONVICTION is never a confidence percentage — percentages from an LLM are fake precision. It reflects
whether the Quant, Beat Tracker, and Contrarian actually agree, or why they can't yet: Unanimous (all
three land the same direction), Majority (two agree, one dissents — say who and why), Split (no real
consensus among the three), Speculative (agreement isn't the issue — the underlying evidence is thin,
e.g. a rookie with no track record, a projection with no market/news confirmation, or stale data), or
Worth investigation (the analysis is sound as far as it goes, but the real answer depends on something
only another manager can tell you — say exactly what to ask them in RECON). Omit the DISSENT, RECON, or
PRICE CEILING lines entirely when they don't apply — never write "N/A".
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


VERDICT_FIELDS = ["RECOMMENDATION", "CONVICTION", "REASON", "DISSENT", "RISK", "RECON", "PRICE CEILING"]


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


def is_claude_configured() -> bool:
    return bool(ANTHROPIC_API_KEY)


def is_gemini_configured() -> bool:
    return bool(GEMINI_API_KEY)


def is_openai_configured() -> bool:
    return bool(OPENAI_API_KEY)


# -- Claude (Quant + Moderator) ------------------------------------------------

def _ask_claude(system_prompt: str, user_prompt: str) -> str:
    if not is_claude_configured():
        return "⚠️ ANTHROPIC_API_KEY not set — add it to your .env file to enable Claude."
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(block.text for block in response.content if hasattr(block, "text")).strip()
    except Exception as exc:  # noqa: BLE001 - surface any provider error to the UI, don't crash the app
        return f"⚠️ Claude request failed: {exc}"


def ask_quant(context: str, question: str) -> str:
    prompt = f"League/roster context:\n{context}\n\nQuestion: {question}"
    return _ask_claude(QUANT_SYSTEM_PROMPT, prompt)


def ask_moderator(context: str, question: str, quant: str, beat: str, contrarian: str) -> str:
    prompt = (
        f"League/roster context:\n{context}\n\n"
        f"Original question: {question}\n\n"
        f"--- QUANT / VORP REPORT ---\n{quant}\n\n"
        f"--- BEAT / NEWS REPORT ---\n{beat}\n\n"
        f"--- CONTRARIAN / RISK REPORT ---\n{contrarian}\n\n"
        "Synthesize these into one verdict."
    )
    return _ask_claude(MODERATOR_SYSTEM_PROMPT, prompt)


def summarize_history(messages: list[dict], prior_summary: Optional[str] = None) -> str:
    """Compact a batch of old chat messages (see DebateResult/chat history shape) into one memory block.

    Fails soft like every other ask_* function — callers must check for a
    leading "⚠️" and, on failure, leave the original messages untouched
    rather than pruning history that was never successfully summarized.
    """
    if not messages:
        return "⚠️ Nothing to summarize."
    transcript = "\n\n".join(f"[{m.get('role', '?')}] {m.get('content', '')}" for m in messages)
    prompt = transcript if not prior_summary else f"PRIOR MEMORY SUMMARY:\n{prior_summary}\n\nNEW TRANSCRIPT TO MERGE IN:\n{transcript}"
    return _ask_claude(SUMMARIZER_SYSTEM_PROMPT, prompt)


# -- Gemini (Beat / News Tracker, with live search grounding) -----------------

def ask_beat(context: str, question: str) -> str:
    if not is_gemini_configured():
        return "⚠️ GEMINI_API_KEY not set — add it to your .env file to enable the Beat Tracker."
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"League/roster context:\n{context}\n\nQuestion: {question}"
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=BEAT_SYSTEM_PROMPT,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                max_output_tokens=MAX_TOKENS,
            ),
        )
        return (response.text or "").strip() or "⚠️ Gemini returned an empty response."
    except Exception as exc:  # noqa: BLE001
        return f"⚠️ Gemini request failed: {exc}"


# -- ChatGPT (Contrarian / Risk Analyst) ---------------------------------------

def ask_contrarian(context: str, question: str, quant: str, beat: str) -> str:
    if not is_openai_configured():
        return "⚠️ OPENAI_API_KEY not set — add it to your .env file to enable the Contrarian Analyst."
    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = (
            f"League/roster context:\n{context}\n\n"
            f"Original question: {question}\n\n"
            f"--- QUANT / VORP REPORT ---\n{quant}\n\n"
            f"--- BEAT / NEWS REPORT ---\n{beat}\n\n"
            "Pressure-test these two reports."
        )
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": CONTRARIAN_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            tools=[{"type": "web_search"}],
            max_output_tokens=MAX_TOKENS,
        )
        return (getattr(response, "output_text", "") or "").strip()
    except Exception as exc:  # noqa: BLE001
        return f"⚠️ ChatGPT request failed: {exc}"


# -- Orchestration --------------------------------------------------------------

def run_debate(context: str, question: str) -> DebateResult:
    """Run the full four-agent debate: Quant -> Beat -> Contrarian -> Moderator."""
    result = DebateResult(question=question)
    result.quant = ask_quant(context, question)
    result.beat = ask_beat(context, question)
    result.contrarian = ask_contrarian(context, question, result.quant, result.beat)
    result.moderator = ask_moderator(context, question, result.quant, result.beat, result.contrarian)
    if not result.moderator.startswith("⚠️"):
        result.verdict = parse_moderator_verdict(result.moderator)
    for label, text in (("quant", result.quant), ("beat", result.beat),
                         ("contrarian", result.contrarian), ("moderator", result.moderator)):
        if text.startswith("⚠️"):
            result.errors.append(f"{label}: {text}")
    return result
