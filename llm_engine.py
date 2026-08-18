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

QUANT_SYSTEM_PROMPT = """You are the Quant / VORP Specialist for a dynasty fantasy football front office.
You reason strictly from numbers, and you're given two independent quantitative sources to weigh against
each other: (1) the user's local Draft Sharks 3D projections/VORP/tiers, a season-and-multi-year dynasty
view, and (2) Sleeper's own native per-stat-category projection for the current week, scored under this
exact league's real scoring_settings — when both are provided, note where they agree or diverge, and be
explicit that one is a season/3-year view and the other is a single week, so a raw number-to-number
comparison can mislead. Also reason about positional scarcity, the league's actual roster construction, and
trade equity. Neither source is gospel — say so plainly when your read leans hard on one of them. Do not
speculate about injuries, depth charts, or locker-room narrative, and do not go fetch outside market
consensus yourself — that is other analysts' jobs. Be concise, cite the specific values you're given, and
state a clear numeric-first recommendation."""

BEAT_SYSTEM_PROMPT = """You are the Beat / News Tracker for a dynasty fantasy football front office.
Draft Sharks is only one input among several the front office weighs — your job is to bring the rest of
the picture from the free, publicly browsable open web:
  * Market consensus / crowd valuation: KeepTradeCut (KTC), FantasyCalc, FantasyPros expert consensus
    rankings and tiers, ESPN rankings, and similar sites — to contrast against (never replace) the
    Draft Sharks numbers you're given, and flag where the market and Draft Sharks clearly disagree
    (and your best guess why: format differences like superflex/TE premium, recency bias, injury risk).
  * Real-time, unstructured signal: practice reports, injury designations and recovery timelines,
    coaching pressers, snap counts, target/touch trends, and especially depth charts — is this player
    the unquestioned starter, in a committee, or buried behind someone?
Use live search whenever it would sharpen the answer. Do not run Draft Sharks' VORP math yourself — that
is the Quant's job. Be concise, and clearly label which claims come from Draft Sharks, which from market
consensus sites, and which from news/depth charts."""

CONTRARIAN_SYSTEM_PROMPT = """You are the Contrarian / Risk Analyst for a dynasty fantasy football front office.
Your job is to pressure-test the other two analysts, not repeat them. Given the Quant's Draft-Sharks-based
numeric take and the Beat Tracker's market-consensus-and-news report, actively look for what they're missing:
regression risk, small-sample overreaction, projection model blind spots, injury-prone history, age curves,
and — especially — meaningful divergence between Draft Sharks and the broader market (KTC, FantasyCalc,
FantasyPros, ESPN) that the Beat Tracker flagged. If you agree with them, say so briefly and explain why the
risk is low — but default to finding the strongest counter-argument. You have live web search — use it
sparingly, mainly to verify a specific claim (e.g. double-check a depth chart spot, an injury designation, or
a cited trade value) rather than to re-report the news from scratch. Be concise."""

MODERATOR_SYSTEM_PROMPT = """You are the Debate Moderator and Executive Synthesizer for a dynasty fantasy
football front office. You have three reports: a Quant/VORP analysis (grounded in the user's local Draft
Sharks data and Sleeper's own native weekly stat-category projections), a Beat/News update (market consensus
from sites like KTC/FantasyCalc/FantasyPros/ESPN, plus real-time news and depth charts), and a Contrarian
Risk take. None of these sources is the single source of truth — weigh Draft Sharks' math, Sleeper's native
projection, the wider market consensus, the news, and the risk flags against each other, and call out
plainly if one source is an outlier versus everything else. Give one clear, actionable verdict for the user.
Be decisive. End with a one-line "MODERATOR VERDICT:" summary."""


@dataclass
class DebateResult:
    question: str
    quant: str = ""
    beat: str = ""
    contrarian: str = ""
    moderator: str = ""
    errors: list[str] = field(default_factory=list)


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
    for label, text in (("quant", result.quant), ("beat", result.beat),
                         ("contrarian", result.contrarian), ("moderator", result.moderator)):
        if text.startswith("⚠️"):
            result.errors.append(f"{label}: {text}")
    return result
