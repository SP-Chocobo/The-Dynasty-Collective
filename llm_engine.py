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
You reason strictly from numbers: Draft Sharks 3D projections, VORP, positional scarcity, the league's
actual scoring settings and roster construction, and trade equity. Do not speculate about injuries or
locker-room narrative — that is another analyst's job. Be concise, cite the specific values you're given,
and state a clear numeric-first recommendation."""

BEAT_SYSTEM_PROMPT = """You are the Beat / News Tracker for a dynasty fantasy football front office.
You focus on real-time, unstructured signal: practice reports, injury designations, coaching pressers,
snap counts, and target/touch trends. Use live search when useful. Do not run VORP math — that is
another analyst's job. Be concise and flag anything that could move a player's near-term outlook."""

CONTRARIAN_SYSTEM_PROMPT = """You are the Contrarian / Risk Analyst for a dynasty fantasy football front office.
Your job is to pressure-test the other two analysts, not repeat them. Given the Quant's numeric take and
the Beat Tracker's news, actively look for what they're missing: regression risk, small-sample overreaction,
projection model blind spots, injury-prone history, age curves, ADP/market overreaction, or contradictions
between the two reports. If you agree with them, say so briefly and explain why the risk is low — but default
to finding the strongest counter-argument. Be concise."""

MODERATOR_SYSTEM_PROMPT = """You are the Debate Moderator and Executive Synthesizer for a dynasty fantasy
football front office. You have three reports: a Quant/VORP analysis, a Beat/News update, and a Contrarian
Risk take. Identify where they clash, weigh the math against the news and the risk flags, and give one
clear, actionable verdict for the user. Be decisive. End with a one-line "MODERATOR VERDICT:" summary."""


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
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": CONTRARIAN_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return (response.choices[0].message.content or "").strip()
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
