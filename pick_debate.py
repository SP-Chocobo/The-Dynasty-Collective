"""
"Debate My Pick" -- the LLM synthesis layer for a live draft pick, built on top of
pick_synthesis.py's frozen PickSnapshot. This module is a SYNTHESIS layer, not another scoring
engine: every number an LLM sees here was already computed by draft_room.py/draft_strategy.py/
pick_synthesis.py, and the models' entire job is arguing about what those numbers MEAN, never
producing new ones of their own.

In CDME's own terms (see README.md's "The Draft Engine" section): this is the optional
interpretive-debate escalation over a frozen PickSnapshot, never a replacement for CDME (the
Contextual Decision Matrix Engine, draft_room.py + pick_synthesis.py) as the deterministic
decision authority.

HARD ARCHITECTURAL REQUIREMENT: an LLM in this module is never allowed to invent or recompute
a player value, a survival probability, an opportunity cost, or any other number pick_synthesis
already produced. It may disagree with an input ("I think this survival estimate undersells a
run at QB") -- that's a real, useful signal -- but a disagreement is captured as an explicitly
labeled DISAGREE line (see parse_caller_verdict), never as a silently substituted number. This
is enforced structurally, not just by prompt instruction: debate_pick's own returned
`recommended` field is looked up directly from the snapshot's real CandidateSnapshot by name
match, never parsed out of the LLM's prose -- so even if a model garbles a number in its own
text, the decomposition this app actually displays is always the deterministic one.

Deliberately does NOT reuse llm_engine.py's PROVIDER_CALLERS: those unconditionally attach live
web search (right for the Beat Tracker/Contrarian roles in a roster-trade debate, which
genuinely need market consensus and news), but wrong here -- this feature exists specifically
to reason over a FROZEN snapshot, and a model quietly pulling in some other site's valuation
mid-debate would undermine the very "give the models the engine's numbers, nothing else"
requirement above. This module's own _call_* functions are deliberately search-free,
reusing llm_engine's API keys/model constants and fail-soft "⚠️" convention for consistency
without inheriting its tool access.

WORKFLOW (mirrors llm_engine.run_debate's shape, three roles instead of four -- there's no
Beat/News-equivalent role here since there's no live information to track, only frozen numbers
to interpret):

  Strategist -- builds the numeric case for the best real action right now, synthesizing
    across universal_value, team_acquisition_value, survival_probability, opportunity_cost,
    denial_value, and positional_cliff. Explicitly required to answer "if I don't take this
    player now, what do I realistically give up" -- not just re-rank by universal_value.
  Skeptic -- pressure-tests the Strategist's read: is the survival model's own assumptions
    (a detected run, an opponent's board) actually solid here, is a roster-fit concern being
    glossed over, does the numeric case actually hold up. Given the Strategist's report to
    react to, same dependency shape as llm_engine's Contrarian.
  Caller -- synthesizes both into ONE recommendation, with a structured closing block
    (RECOMMENDATION/CONFIDENCE/WHY/DISSENT/KEY FACTOR, plus any DISAGREE lines) parsed by
    parse_caller_verdict.

Never call this while the user isn't actually on the clock -- see this module's own
recommended usage in app.py's Draft Room view: an optional action the user triggers, not
something that runs on every board refresh (a live draft's per-pick LLM budget is real, but a
30s-2min pick clock can afford one debate call per pick, not one per board recompute).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from llm_engine import (
    ANTHROPIC_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY,
    CLAUDE_MODEL, GEMINI_MODEL, OPENAI_MODEL, MAX_TOKENS,
)
from pick_synthesis import CandidateSnapshot, PickSnapshot, diff_snapshots

DEFAULT_ROLE_PROVIDERS = {"strategist": "claude", "skeptic": "openai", "caller": "claude"}


def _call_claude(system_prompt: str, user_prompt: str, api_key: Optional[str] = None, model: Optional[str] = None) -> str:
    key = api_key or ANTHROPIC_API_KEY
    if not key:
        return "⚠️ ANTHROPIC_API_KEY not set — add it in the sidebar's Connect Your Accounts section, or in .env."
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=key)
        # No tools attached, deliberately -- see module docstring on why this doesn't reuse
        # llm_engine's web-search-equipped callers.
        response = client.messages.create(
            model=model or CLAUDE_MODEL, max_tokens=MAX_TOKENS, system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(block.text for block in response.content if hasattr(block, "text")).strip()
    except Exception as exc:  # noqa: BLE001
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
            model=model or GEMINI_MODEL, contents=user_prompt,
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=MAX_TOKENS),
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
            input=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            max_output_tokens=MAX_TOKENS,
        )
        return (getattr(response, "output_text", "") or "").strip()
    except Exception as exc:  # noqa: BLE001
        return f"⚠️ ChatGPT request failed: {exc}"


PROVIDER_CALLERS = {"claude": _call_claude, "gemini": _call_gemini, "openai": _call_openai}


STRATEGIST_SYSTEM_PROMPT = """You are the Draft Strategist for a live fantasy football draft, arguing for the
correct action THIS PICK. You are given a frozen snapshot of real, already-computed numbers -- universal_value
(position-agnostic player quality), team_acquisition_value (universal_value plus this specific roster's own need
and lineup-eligibility bonuses), survival_probability (the odds this player is still available at the user's next
pick), opportunity_cost (expected value lost if he doesn't survive), expected_value_of_waiting (the flip side --
what you'd expect to keep if you pass and gamble), denial_value (what the likeliest intervening opponent would
gain from him), positional_cliff (whether a real, computed gap sits between this player and the next-best
remaining player at his position), and pick_necessity (0-100, NOT another value score -- it answers "how badly do
I need to make this selection right now," and 100 means "no reasonable alternative exists," not "best player").
A candidate can have a lower universal_value than another candidate and still be the correct pick if his
pick_necessity is much higher -- that gap IS the interesting case, and your job is to explain it when it appears,
not paper over it.

Some candidates also carry a real-world market-consensus reach_label (WITHIN CONSENSUS BAND / MODEST REACH /
SIGNIFICANT REACH), built from KeepTradeCut's own crowd-sourced dynasty rankings -- real trade-value consensus,
NOT literal draft-position ADP, though the two correlate strongly for established players. This is a guardrail
against the engine quietly fighting the market, not a rule that overrides it: a justified reach is a completely
normal, legitimate recommendation. But the burden of proof scales with the label -- WITHIN CONSENSUS BAND needs no
special justification at all, MODEST REACH needs a real reason, and SIGNIFICANT REACH needs your case to be built
on genuinely strong evidence (a real positional cliff, a severe survival collapse, heavy denial risk) rather than
just "our own valuation ranks him higher than the market does." If you're recommending a SIGNIFICANT REACH,
say explicitly what justifies deviating from consensus this far -- don't recommend it and silently ignore the tag.

These numbers are the ONLY numbers that exist. Never invent, estimate, or silently recompute a value, a
probability, or a projection of your own -- reason only about what the GIVEN numbers mean and how they should be
weighed against each other. If a specific input looks wrong to you, say so as an explicit, separate flag (see the
DISAGREE format your Caller will use) rather than quietly substituting your own number anywhere in your reasoning.

Your central job is answering the real question: "if I don't take this player now, what do I realistically give
up?" That is NOT the same question as "who has the highest universal_value" -- a player who is only third-best
overall can still be the correct pick right now if he sits at a real positional cliff, has a low survival
probability because of a run or opponent need, and the best alternative has comfortably high survival odds. Make
that case explicitly, referencing the specific numbers you were given. Do not just re-rank the candidates by one
column; synthesize across all of them the way the numbers actually interact. Be concise but show your work --
reference the specific figures, don't just gesture at them."""

SKEPTIC_SYSTEM_PROMPT = """You are the Draft Skeptic for a live fantasy football draft. You're given the same
frozen snapshot of real numbers the Strategist saw, plus the Strategist's own case built from them. Your job is to
pressure-test that case, not restate it.

Look specifically for: whether the survival model's own assumptions actually hold here (a detected positional run
is a real signal from recent picks, not a certainty -- would this read differ without it?), whether a roster-fit
concern the numbers can't fully capture is being glossed over (these numbers don't know about bye weeks, a
player's specific injury history, or a personality clash with the rest of the roster -- say so if something like
that plausibly matters and isn't reflected in what you were given), and whether the numeric case genuinely
supports the Strategist's conclusion or is being stretched to fit it. If the Strategist recommended a candidate
tagged MODEST REACH or SIGNIFICANT REACH (real market-consensus deviation, from KeepTradeCut's crowd data, not
this engine's own math), that's exactly the kind of call worth pressure-testing hardest: is the evidence actually
strong enough to justify deviating from what the market itself expects here, or is the case really just "our
valuation disagrees with consensus" dressed up as urgency?

Same hard rule as the Strategist: these numbers are the only numbers that exist. Never invent or recompute a
figure of your own -- if you think a specific input is wrong, flag it explicitly and separately (your Caller will
capture this as a DISAGREE line) rather than substituting a different number anywhere in your own reasoning. If
you genuinely agree with the Strategist's case, say so plainly and explain why the risk is low -- but default to
finding the strongest real counter-argument. Be concise."""

CALLER_SYSTEM_PROMPT = """You are the Draft Caller for a live fantasy football draft -- the final synthesizer
between a Strategist's numeric case and a Skeptic's pressure test, both reasoning over the same frozen snapshot of
real, already-computed numbers (universal_value, team_acquisition_value, survival_probability, opportunity_cost,
expected_value_of_waiting, denial_value, positional_cliff, and a market-consensus reach_label from KeepTradeCut's
real crowd data where available). Give ONE clear, actionable recommendation: which candidate to take right now,
and why -- explicitly answering "what do I realistically give up if I don't take him now" using the actual
numbers you were given, not a vague hedge. If your recommendation carries a MODEST or SIGNIFICANT reach label,
your WHY must explicitly justify deviating from market consensus that far, not just restate his other numbers.

Never invent or recompute a number yourself -- if either analyst flagged that a specific input looks wrong, or you
believe one does, capture that as a DISAGREE line (format below), completely separate from your recommendation
itself. Your recommendation must be built entirely from the real numbers in the snapshot, never a number you
made up to make the case cleaner.

End your response with this exact structured block, one field per line, using these exact labels:

RECOMMENDATION: <the exact candidate name as given in the snapshot -- copy it exactly, do not paraphrase>
CONFIDENCE: Unanimous / Lean / Split
WHY: <the deciding case for this pick, one to three sentences, referencing the actual numbers -- the same
"here's why X is right even though he isn't the top-ranked player" reasoning the Strategist built>
DISSENT: <the strongest real counter-argument still standing after the debate -- omit only if there is genuinely
none>
KEY FACTOR: <the single number or combination that most drove this call, e.g. "19% survival with a QB run
detected and a HIGH positional cliff">

CONFIDENCE is never a percentage -- percentages from an LLM are fake precision. Unanimous means the Strategist and
Skeptic substantively agree; Lean means the Skeptic raised a real concern but the Strategist's case still holds;
Split means there's a genuine, unresolved disagreement between them and the user should weigh it themselves.

If either analyst flagged (or you believe) that a specific input number looks wrong, add one line per such flag
(after the block above):

DISAGREE: <the specific term, e.g. "survival_probability for Player X"> | <why you think it's wrong, one line>

Never invent a disagreement that wasn't actually raised or reasoned through in the debate -- omit this entirely
when there's nothing to flag. Be decisive."""


def _format_probability(value: Optional[float]) -> str:
    return f"{round(value * 100)}%" if value is not None else "unknown"


def _format_candidate(candidate: CandidateSnapshot, user_selected_player_id: Optional[str]) -> str:
    flag = " (USER-FLAGGED)" if user_selected_player_id == candidate.player_id else ""
    lines = [
        f"CANDIDATE: {candidate.name} ({candidate.position}{', ' + candidate.team if candidate.team else ''}){flag}",
        f"  Pick necessity: {candidate.pick_necessity}/100 -- {candidate.necessity_label} (NOT a value score -- see below for value)",
        f"  Universal value: {candidate.universal_value} (source: {candidate.bpa_source}, confidence: {candidate.confidence})"
        + (f" -- {candidate.projected_points} projected season points" if candidate.projected_points is not None else ""),
        f"  Team acquisition value: {candidate.team_acquisition_value} (need_bonus: {candidate.need_bonus:+}, eligibility_bonus: {candidate.eligibility_bonus:+})",
    ]
    if candidate.near_tie_with_leader:
        lines.append(
            "  NEAR-TIE: within the measured noise band of the top candidate -- the value "
            "ordering inside this group is NOT a real preference signal; the user's own "
            "player preference is a fully legitimate tiebreaker here."
        )
    if candidate.survival_probability is not None:
        lines.append(
            f"  Survival probability to your next pick: {_format_probability(candidate.survival_probability)} "
            f"({candidate.intervening_picks} intervening pick(s))"
        )
        lines.append(f"  Opportunity cost of waiting: {candidate.opportunity_cost}")
        lines.append(f"  Expected value if you wait: {candidate.expected_value_of_waiting}")
    if candidate.denial_value:
        lines.append(f"  Denial value: {candidate.denial_value} (would go to roster {candidate.denial_team})")
    if candidate.positional_cliff:
        cliff = candidate.positional_cliff
        lines.append(f"  Positional cliff: {cliff['tier']} (gap to next at position: {cliff['gap']}, typical gap: {cliff['typical_gap']})")
    if candidate.positional_forfeit is not None and candidate.positional_forfeit > 0:
        lines.append(
            f"  Cost of delaying {candidate.position} entirely: best remaining {candidate.position} at your next "
            f"pick expected ~{candidate.positional_forfeit} universal-value points worse than now "
            f"(~{candidate.position_expected_taken} {candidate.position} pick(s) expected before then)"
        )
    if candidate.position_run_detected:
        lines.append(f"  {candidate.position} run currently detected among recent picks")
    if candidate.reach_label is not None:
        lines.append(
            f"  Market consensus (KeepTradeCut, real crowd data -- trade-value consensus, NOT literal "
            f"ADP): rank {candidate.consensus_rank}, tier {candidate.consensus_tier} -- {candidate.reach_label}"
        )
    return "\n".join(lines)


def format_snapshot_for_llm(snapshot: PickSnapshot, diffs: Optional[list[dict]] = None) -> str:
    """The structured evidence block every role sees -- labeled real numbers, never prose
    summarizing them, so a model has no reason to paraphrase a figure into something slightly
    different from what pick_synthesis actually computed."""
    parts = [
        f"PICK {snapshot.pick_label} (round {snapshot.round}) -- roster {snapshot.my_roster_id}'s decision.",
        "The candidates below are the ONLY real numbers available. Do not invent, estimate, or recompute any "
        "value, probability, or projection not shown here.",
        "",
    ]
    parts.extend(
        _format_candidate(c, snapshot.user_selected_player_id) + "\n" for c in snapshot.candidates
    )
    if diffs:
        parts.append("WHAT CHANGED SINCE THE LAST SNAPSHOT:")
        for d in diffs:
            if d.get("entered") is True:
                parts.append(f"  {d['name']}: newly entered the candidate pool at rank {d['rank']}")
            elif d.get("entered") is False:
                parts.append(f"  {d['name']}: no longer a live candidate (was rank {d['rank']})")
            elif d.get("deltas"):
                delta_str = ", ".join(f"{k}: {v:+}" for k, v in d["deltas"].items())
                parts.append(f"  {d['name']}: rank moved by {d['rank_delta']:+} ({delta_str})")
    return "\n".join(parts)


CALLER_FIELDS = ("RECOMMENDATION", "CONFIDENCE", "WHY", "DISSENT", "KEY FACTOR")


def parse_caller_verdict(text: str) -> dict:
    """Pull the structured closing block (and any DISAGREE lines) out of the Caller's response.
    Fails soft, same posture as llm_engine.parse_moderator_verdict: whatever fields aren't
    found are simply absent, never raised as an error."""
    verdict: dict = {}
    disagreements: list[dict] = []
    for line in text.splitlines():
        stripped = line.strip().lstrip("-*# ").rstrip()
        upper = stripped.upper()
        if upper.startswith("DISAGREE:"):
            parts = [p.strip() for p in stripped[len("DISAGREE:"):].split("|")]
            if len(parts) >= 2 and parts[0] and parts[1]:
                disagreements.append({"term": parts[0], "reason": parts[1]})
            continue
        for field_name in CALLER_FIELDS:
            prefix = f"{field_name}:"
            if upper.startswith(prefix):
                value = stripped[len(prefix):].strip()
                if value:
                    verdict[field_name.lower().replace(" ", "_")] = value
                break
    verdict["disagreements"] = disagreements
    return verdict


def _match_candidate(snapshot: PickSnapshot, recommendation_text: Optional[str]) -> Optional[CandidateSnapshot]:
    """Look up the Caller's named recommendation against the snapshot's REAL candidates --
    never trust a number out of the LLM's own prose. Exact case-insensitive match first, falling
    back to substring containment (a model paraphrasing "Brock Purdy" as "Purdy" shouldn't lose
    the match) -- returns None (never a guess) if nothing lines up, so a caller can tell the
    debate didn't cleanly resolve rather than silently displaying the wrong player's numbers."""
    if not recommendation_text:
        return None
    target = recommendation_text.strip().lower()
    for c in snapshot.candidates:
        if c.name.strip().lower() == target:
            return c
    for c in snapshot.candidates:
        name = c.name.strip().lower()
        if name in target or target in name:
            return c
    return None


def _best_alternative(snapshot: PickSnapshot, recommended: Optional[CandidateSnapshot]) -> Optional[CandidateSnapshot]:
    """The highest team_acquisition_value candidate OTHER than the recommended one -- computed
    deterministically here, never left for the LLM to name in its own prose (a model could
    misstate which alternative is actually best, or its survival number). None if there's no
    other real candidate to point to (a single-candidate snapshot) or nothing was recommended
    at all.

    Candidates the board could not price are excluded: "the best alternative" is a claim about
    value, and a row with no team_acquisition_value cannot support it. None when every other
    candidate is unpriced -- naming one anyway would tell the debate layer that a player the
    engine has no opinion about is the runner-up."""
    others = [c for c in snapshot.candidates
              if (recommended is None or c.player_id != recommended.player_id)
              and c.team_acquisition_value is not None]
    if not others:
        return None
    return max(others, key=lambda c: c.team_acquisition_value)


@dataclass
class PickDebateResult:
    pick_label: str
    recommended_player_id: Optional[str] = None
    recommended: Optional[CandidateSnapshot] = None
    best_alternative: Optional[CandidateSnapshot] = None
    confidence: Optional[str] = None
    why: str = ""
    dissent: str = ""
    key_factor: str = ""
    disagreements: list = field(default_factory=list)
    diff: list = field(default_factory=list)
    strategist_report: str = ""
    skeptic_report: str = ""
    caller_report: str = ""
    errors: list = field(default_factory=list)
    role_providers: dict = field(default_factory=dict)


def debate_pick(
    snapshot: PickSnapshot,
    *,
    previous_snapshot: Optional[PickSnapshot] = None,
    role_providers: Optional[dict] = None,
    api_keys: Optional[dict] = None,
    role_models: Optional[dict] = None,
) -> PickDebateResult:
    """Run the full three-role debate over an already-built PickSnapshot: Strategist -> Skeptic
    -> Caller. Never computes anything itself beyond formatting and parsing -- see module
    docstring for the hard "no invented/recomputed numbers" requirement this enforces
    structurally (the returned `recommended` field is looked up from the snapshot's own real
    CandidateSnapshot, never parsed as numbers out of LLM text). `best_alternative` is likewise
    computed deterministically here (the highest team_acquisition_value candidate other than
    the recommended one), never trusted from the Caller's own prose -- a model naming the wrong
    alternative, or misstating its survival odds, can't corrupt what this app actually displays.

    previous_snapshot, when given, is diffed against snapshot (pick_synthesis.diff_snapshots)
    and folded into the evidence every role sees as a "what changed" section -- the structured
    audit trail the debate can reference directly rather than needing to notice board movement
    on its own.

    role_providers/api_keys/role_models mirror llm_engine.run_debate's own shape (a
    role -> provider dict, a provider -> api_key dict, an optional role -> model override) for
    consistency with the rest of this app's provider routing, even though this feature's roles
    aren't part of bot_config.py's persisted UI configuration (see module docstring: this is an
    orchestration layer, exposing its own defaults, not a slot in the existing four-role trade-
    debate roster)."""
    role_providers = {**DEFAULT_ROLE_PROVIDERS, **(role_providers or {})}
    api_keys = api_keys or {}
    role_models = role_models or {}

    diffs = diff_snapshots(previous_snapshot, snapshot) if previous_snapshot is not None else []
    evidence = format_snapshot_for_llm(snapshot, diffs)

    def _call(role: str, system_prompt: str, user_prompt: str) -> str:
        provider = role_providers.get(role, DEFAULT_ROLE_PROVIDERS[role])
        return PROVIDER_CALLERS[provider](system_prompt, user_prompt, api_keys.get(provider), role_models.get(role))

    strategist_report = _call("strategist", STRATEGIST_SYSTEM_PROMPT, evidence)
    skeptic_prompt = f"{evidence}\n\n--- STRATEGIST'S CASE ---\n{strategist_report}"
    skeptic_report = _call("skeptic", SKEPTIC_SYSTEM_PROMPT, skeptic_prompt)
    caller_prompt = (
        f"{evidence}\n\n--- STRATEGIST'S CASE ---\n{strategist_report}\n\n"
        f"--- SKEPTIC'S CHALLENGE ---\n{skeptic_report}\n\nSynthesize these into one final recommendation."
    )
    caller_report = _call("caller", CALLER_SYSTEM_PROMPT, caller_prompt)

    verdict = parse_caller_verdict(caller_report) if not caller_report.startswith("⚠️") else {}
    recommended = _match_candidate(snapshot, verdict.get("recommendation"))
    best_alternative = _best_alternative(snapshot, recommended)

    errors = [
        f"{role}: {text}" for role, text in (
            ("strategist", strategist_report), ("skeptic", skeptic_report), ("caller", caller_report),
        ) if text.startswith("⚠️")
    ]

    return PickDebateResult(
        pick_label=snapshot.pick_label,
        recommended_player_id=recommended.player_id if recommended else None,
        recommended=recommended,
        best_alternative=best_alternative,
        confidence=verdict.get("confidence"),
        why=verdict.get("why", ""),
        dissent=verdict.get("dissent", ""),
        key_factor=verdict.get("key_factor", ""),
        disagreements=verdict.get("disagreements", []),
        diff=diffs,
        strategist_report=strategist_report, skeptic_report=skeptic_report, caller_report=caller_report,
        errors=errors, role_providers=dict(role_providers),
    )
