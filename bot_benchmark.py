"""
Empirical model benchmarking for the Configure Bots role -> provider -> model
assignment -- lets the actual candidate models audition for a role instead of
being picked by reputation or brand.

Every candidate (provider, model) pair runs the same fixed battery of
scenarios for the role being benchmarked, so results are comparable across
models and stable rerun to rerun. Each answer is then scored by a separate
"judge" call against an explicit, weighted rubric -- the judge is never told
which model or provider produced the answer it's grading, which is the one
safeguard that actually matters here: an unstructured "which answer is
better?" prompt invites exactly the model/style bias this is trying to avoid.

This module only knows how to run the battery and score the results; it has
no opinion on which provider should judge, and it never writes to
bot_config.py itself -- applying a benchmark's recommendation is a UI action
(app.py), not something this module does on its own.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Callable, Optional

import llm_engine
from content_hash import fingerprint

RESULTS_PATH = Path("data/benchmark_results.json")

# How many past runs to keep per role. A report is a few KB of prose per candidate, so an
# unbounded log would grow without limit for a store nobody prunes -- same capped-history
# posture as bot_research.findings_for_context and app.RECENT_TURNS_IN_CONTEXT. The newest run
# is always index 0.
HISTORY_LIMIT = 20

# role -> the production parser its output must satisfy, for the chairs whose answers are
# consumed by machine rather than only read. The Moderator's system prompt requires a
# structured block that four consumers depend on (decision_log, todo_log, bot_research, and
# app.py's verdict card); a model can score well on every rubric dimension and still fail it,
# because no dimension looks.
#
# RULED (#94): FLAG ONLY. This does NOT feed the score and must not. 5.6a framed the choice as
# gate-versus-flag and left it open because it changes which model wins; 7.11 then supplied the
# consideration that settles it. The structured block is the entire channel through which model
# output acquires authority -- rewriting an objective, proposing a resolution, writing a rank
# into the composite, creating a to-do all run through it. So a Moderator that FAILS its machine
# contract is inert on every authority path, and a compliant one is the one that can rewrite a
# user's objectives and inject numbers. Disqualifying on failure would therefore SELECT FOR
# MODELS THAT EXERCISE MORE AUTHORITY, which is not what a quality gate is for.
#
# Flag-only is not the same as ignoring it. The flag is surfaced beside the candidate AND
# carried into the Apply outcome (app.py), because a flag the deciding action does not repeat is
# a declaration nothing reads.
MACHINE_CONTRACT_PARSERS = {"moderator": llm_engine.parse_moderator_verdict}


def _contract_ok(role: str, response: str) -> Optional[bool]:
    """True/False for a chair whose output is machine-parsed, None for one whose output is
    only read. None is 'no contract to satisfy', never 'passed by default'."""
    parser = MACHINE_CONTRACT_PARSERS.get(role)
    if parser is None:
        return None
    return bool(parser(response))


# The provider SDKs, by distribution name, whose installed version is worth recording on a
# run. A benchmark report is this app's only versioned audit event -- the one artifact that can
# answer "did this model get worse, or did something underneath it move?" -- and the SDK is one
# of the things that moves: a client library can change default parameters, request handling,
# tool encoding, or how a response is assembled, none of which touches this repo's own source.
_PROVIDER_SDK_DISTRIBUTIONS = ("anthropic", "google-genai", "openai")


def _provider_sdk_versions() -> dict[str, str]:
    """{distribution: installed version} for whichever provider SDKs are actually importable
    here. A distribution that isn't installed is OMITTED, never recorded as a version this run
    did not run against -- absent means "not recorded", the same rule decision_log.log_decision
    applies to provider/model. Never raises: a metadata lookup failing is not a reason to lose
    a benchmark run."""
    from importlib import metadata

    versions = {}
    for dist in _PROVIDER_SDK_DISTRIBUTIONS:
        try:
            versions[dist] = metadata.version(dist)
        except Exception:  # noqa: BLE001 -- not installed, or a broken/partial install
            continue
    return versions


# A short content hash of exactly what a run was conducted under -- deliberately a hash rather
# than a hand-maintained version number, since a number drifts out of sync with the thing it
# names while this cannot disagree with the battery, rubric or chair prompt it came from.
#
# The implementation moved to content_hash.py when snapshot identity became a second consumer
# (#111/#92). It is byte-identical to the private version this module used to carry, which is
# what keeps every fingerprint already written into results.json comparable with new ones --
# a changed hash would silently partition comparable_history into before and after.
_fingerprint = fingerprint

# Fixed, self-contained scenarios -- no live league data required, so every
# candidate model is judged against literally the same inputs. Three per
# role: enough to catch a model that's only strong on one style of question,
# small enough that a full run of several models stays a few minutes, not an
# hour.
BENCHMARK_BATTERY: dict[str, list[dict]] = {
    "quant": [
        {
            "label": "VORP trade comparison",
            "prompt": (
                "In a 12-team, full-PPR, Superflex dynasty league, compare two trade targets "
                "using VORP-style reasoning: Player A is a WR2 projected for 210 PPR points "
                "this season (replacement-level WR in this format is ~140 points). Player B is "
                "a rookie backup QB with a 25% chance of a starting job opening within 12 "
                "months, projected for 90 points if he starts a full season, 15 if he doesn't "
                "(replacement-level backup QB in Superflex is ~60 points). Which asset has more "
                "trade value right now, and by how much? Show your replacement-level math."
            ),
        },
        {
            "label": "Positional scarcity read",
            "prompt": (
                "In a 10-team, standard (non-PPR) dynasty league with only 1 flex spot and no "
                "Superflex, which is the scarcer, more valuable dynasty asset: a top-12 rookie "
                "TE or a top-24 rookie WR? Walk through the positional scarcity math, not just "
                "a gut call."
            ),
        },
        {
            "label": "Multi-player value stack",
            "prompt": (
                "Rank these three players by dynasty trade value and justify the ranking with "
                "more than vibes: (1) a 26-year-old RB1 coming off an age-cliff-adjacent "
                "season, 240 PPR points; (2) a 23-year-old WR2 on an ascending target share, "
                "195 PPR points and trending up; (3) a rookie 1st-round startup pick with no "
                "NFL profile yet. Assume a 12-team PPR dynasty league."
            ),
        },
    ],
    "beat": [
        {
            "label": "Confirmed vs. speculative injury news",
            "prompt": (
                "Given this report: 'A team beat writer posted that the starting RB was seen "
                "without a walking boot at practice on Wednesday, but the team's official "
                "injury report still lists him as Questionable with no practice participation "
                "logged. A separate fan account claims a source says he'll play Sunday.' "
                "Summarize what is actually confirmed here versus what is speculation, and "
                "state your confidence level for whether he plays Sunday."
            ),
        },
        {
            "label": "Depth-chart change interpretation",
            "prompt": (
                "A team signs a veteran RB to a one-year deal three weeks into the season, "
                "while their starting RB is dealing with a lower-body injury with no set "
                "return date. What are the concrete, near-term dynasty-relevant implications "
                "for both the starter and the new signee? Be specific about what actually "
                "changes versus what's still unknown."
            ),
        },
        {
            "label": "Distinguishing rumor from reporting",
            "prompt": (
                "You see two posts about the same player: one from a well-sourced NFL insider "
                "citing 'a person with knowledge of the situation' saying a trade request is "
                "likely; another from an anonymous fan account claiming the player 'is "
                "definitely getting traded this week.' How would you characterize the actual "
                "reliability of each, and what would you tell a dynasty manager to do right "
                "now?"
            ),
        },
    ],
    "contrarian": [
        {
            "label": "Pressure-test a trade recommendation",
            "prompt": (
                "A colleague just recommended: 'Trade your aging RB1 for a package of two "
                "future 2nd-round rookie picks -- his value will only decline from here, and "
                "the picks let you rebuild.' Argue the strongest case against this "
                "recommendation. What is it missing or getting wrong?"
            ),
        },
        {
            "label": "Challenge a roster construction plan",
            "prompt": (
                "A colleague just recommended: 'Since you're rebuilding, load up on as many "
                "rookie picks as possible and punt this season entirely -- win totals don't "
                "matter for a rebuilding dynasty team.' What's the strongest counter-argument "
                "to a total-tank strategy in dynasty formats?"
            ),
        },
        {
            "label": "Find the hidden assumption",
            "prompt": (
                "A colleague just claimed: 'This rookie WR is a lock to be a top-12 dynasty "
                "asset within two years because he ran a 4.4 forty and has elite college "
                "production.' What unstated assumptions is this claim resting on, and which of "
                "them are actually shaky?"
            ),
        },
    ],
    "moderator": [
        {
            "label": "Reconcile a three-way disagreement",
            "prompt": (
                "Three analysts gave you these takes on whether to trade your WR1 for two "
                "1st-round rookie picks:\n\n"
                "QUANT: 'Numerically, the WR1's current point-per-game value (18.2 PPG) is "
                "roughly equivalent to the blended expected value of two late-1st picks in a "
                "12-team rookie draft. It's a fair-value trade by the math, not clearly a win "
                "or loss.'\n\n"
                "BEAT: 'The WR1 is dealing with a minor but recurring soft-tissue injury that "
                "has cost him games in each of the last two seasons, and the team just drafted "
                "a rookie WR in round 2 who is already seeing expanded snaps.'\n\n"
                "CONTRARIAN: 'Two 1st-round rookie picks are not equivalent to two known "
                "assets -- draft picks have real bust risk, and rookie WRs specifically have a "
                "rough hit rate in year one. Trading a proven WR1 for unproven picks "
                "concentrates risk, it doesn't reduce it.'\n\n"
                "Weigh these three reports against each other and issue one clear final "
                "recommendation: trade or hold, and why, addressing where the reports actually "
                "conflict."
            ),
        },
        {
            "label": "Detect where reports agree vs. actually conflict",
            "prompt": (
                "Three analysts gave you these takes on a potential waiver-wire pickup at "
                "RB:\n\n"
                "QUANT: 'His per-touch efficiency (5.8 yards/carry over a small sample) is "
                "likely to regress toward the mean, so don't overpay in FAAB.'\n\n"
                "BEAT: 'The starting RB in front of him just landed on injured reserve for at "
                "least 4 weeks, so touches are opening up regardless of efficiency.'\n\n"
                "CONTRARIAN: 'Small-sample efficiency stats are noisy in both directions -- "
                "the Quant's regression point is right in isolation, but irrelevant if he's "
                "about to see a real workload increase.'\n\n"
                "Where do these three actually disagree, and where are they just emphasizing "
                "different (compatible) parts of the same picture? Give a final FAAB-bid "
                "recommendation."
            ),
        },
        {
            "label": "Know when to override the group",
            "prompt": (
                "Three analysts gave you these takes on starting a player this week:\n\n"
                "QUANT: 'Pure matchup-adjusted projection favors starting him -- QB4 among "
                "relevant options this week.'\n\n"
                "BEAT: 'He was a limited practice participant Wednesday and Thursday with a "
                "hamstring issue, officially Questionable, no clear signal yet on Friday's "
                "status.'\n\n"
                "CONTRARIAN: 'The Quant's projection assumes he plays a full snap share -- "
                "that assumption is exactly what's in doubt here, so the projection is only as "
                "good as an injury status we don't have yet.'\n\n"
                "Issue a clear start/sit verdict, explicitly stating what new information (if "
                "any) would change it."
            ),
        },
    ],
}

# role -> [(dimension_key, weight, description)], weights sum to 100. Deliberately
# different per role -- "accuracy" means something different for a Quant's math than
# for a Beat Tracker's news reporting, so a single generic rubric would grade every
# role against criteria that don't actually fit its job.
RUBRIC: dict[str, list[tuple[str, int, str]]] = {
    "quant": [
        ("accuracy", 30, "Are the value/VORP figures internally consistent and defensible?"),
        ("methodology", 25, "Does it apply a coherent, explained analytical framework rather than a bare assertion?"),
        ("relevance", 25, "Does it actually answer the specific question asked, not a generic version of it?"),
        ("consistency", 20, "Is the reasoning free of self-contradiction within the answer?"),
    ],
    "beat": [
        ("accuracy", 30, "Does it correctly represent the facts actually given in the prompt?"),
        ("attribution", 25, "Does it clearly separate confirmed information from speculation or rumor?"),
        ("relevance", 25, "Does it address what a dynasty manager actually needs to decide?"),
        ("caution", 20, "Does it avoid inventing specific facts (dates, grades, quotes) it can't support?"),
    ],
    "contrarian": [
        ("insight", 30, "Does it surface a real, non-obvious weakness rather than a generic disclaimer?"),
        ("rigor", 25, "Is the counter-argument logically sound, not just contrarian for its own sake?"),
        ("relevance", 25, "Does it engage with the specific claim given, not a strawman of it?"),
        ("constructiveness", 20, "Does it leave the reader with something actionable, not just doubt?"),
    ],
    "moderator": [
        ("synthesis", 30, "Does it actually weigh the input reports against each other rather than just picking one?"),
        ("disagreement_handling", 25, "Does it explicitly address where the reports conflict?"),
        ("clarity", 25, "Is the final recommendation clear and unambiguous?"),
        ("actionability", 20, "Could the reader actually act on this verdict as given?"),
    ],
}

JUDGE_SYSTEM_PROMPT = (
    "You are a strict, impartial evaluator of AI-generated fantasy football analysis. You do "
    "not know and must not guess which model or company produced the response you're grading "
    "-- score only what's on the page in front of you. Be skeptical: a confident, "
    "well-formatted answer that is actually generic, evasive, or unsupported should score low."
)


def _judge_response(
    role: str, question_prompt: str, response_text: str,
    judge_provider: str, judge_api_key: Optional[str], judge_model: Optional[str],
) -> tuple[dict[str, int], str]:
    rubric = RUBRIC[role]
    rubric_lines = "\n".join(f"- {key.upper()} (0-100, weight {weight}%): {desc}" for key, weight, desc in rubric)
    judge_prompt = (
        f"TASK GIVEN TO THE MODEL:\n{question_prompt}\n\n"
        f"MODEL'S RESPONSE:\n{response_text}\n\n"
        f"Score this response on each dimension below, 0-100:\n{rubric_lines}\n\n"
        "Respond with exactly one line per dimension in this format, then one NOTES line:\n"
        + "\n".join(f"{key.upper()}: <score>" for key, _, _ in rubric)
        + "\nNOTES: <one sentence on why>"
    )
    raw = llm_engine.PROVIDER_CALLERS[judge_provider](JUDGE_SYSTEM_PROMPT, judge_prompt, judge_api_key, judge_model)
    scores: dict[str, int] = {}
    notes = ""
    for line in raw.splitlines():
        stripped = line.strip().lstrip("-*# ")
        upper = stripped.upper()
        for key, _, _ in rubric:
            prefix = f"{key.upper()}:"
            if upper.startswith(prefix):
                match = re.search(r"\d+", stripped[len(prefix):])
                if match:
                    scores[key] = max(0, min(100, int(match.group())))
        if upper.startswith("NOTES:"):
            notes = stripped[len("NOTES:"):].strip()
    return scores, notes


def run_benchmark(
    role: str,
    candidates: list[tuple[str, str]],
    api_keys: dict[str, Optional[str]],
    judge_provider: str = "claude",
    judge_api_key: Optional[str] = None,
    judge_model: Optional[str] = None,
    on_progress: Optional[Callable[[str], None]] = None,
) -> dict:
    """Run every (provider, model) candidate through `role`'s fixed battery, score each
    answer with a blind judge call, and return a report sorted best-to-worst.

    `on_progress`, if given, is called with a short status string after every individual
    model call -- a full run makes `len(candidates) * len(battery)` real API calls plus
    one judge call each, so it can take minutes and the UI needs something to show while
    it waits.
    """
    battery = BENCHMARK_BATTERY[role]
    rubric = RUBRIC[role]
    weight_total = sum(w for _, w, _ in rubric)
    system_prompt = llm_engine.ROLE_SYSTEM_PROMPTS[role]

    results = []
    total_steps = len(candidates) * len(battery)
    step = 0
    for provider, model in candidates:
        key = api_keys.get(provider)
        per_question = []
        for q in battery:
            step += 1
            if on_progress:
                on_progress(f"[{step}/{total_steps}] {provider}:{model or 'default'} — {q['label']}")
            t0 = time.time()
            response = llm_engine.PROVIDER_CALLERS[provider](system_prompt, q["prompt"], key, model or None)
            latency = time.time() - t0
            failed = response.startswith("⚠️")
            if failed:
                scores, notes = {k: 0 for k, _, _ in rubric}, response
            else:
                scores, notes = _judge_response(role, q["prompt"], response, judge_provider, judge_api_key, judge_model)
            weighted = sum(scores.get(k, 0) * w for k, w, _ in rubric) / weight_total
            per_question.append({
                "label": q["label"], "response": response, "scores": scores,
                "weighted": round(weighted, 1), "notes": notes,
                "latency": round(latency, 2), "failed": failed,
                # Recorded, never scored -- ruled, not deferred (#94; see MACHINE_CONTRACT_PARSERS
                # for why disqualifying would select for models that exercise more authority). A
                # candidate that answers well and does not emit the structured block its chair
                # requires still ranks on its rubric average here; what changes is that whoever
                # presses Apply is told, twice.
                "contract_ok": None if failed else _contract_ok(role, response),
            })
        avg_score = round(sum(q["weighted"] for q in per_question) / len(per_question), 1) if per_question else 0.0
        avg_latency = round(sum(q["latency"] for q in per_question) / len(per_question), 2) if per_question else 0.0
        results.append({
            "provider": provider, "model": model or "",
            "score": avg_score, "avg_latency": avg_latency,
            "any_failed": any(q["failed"] for q in per_question),
            "any_contract_failure": any(q["contract_ok"] is False for q in per_question),
            "per_question": per_question,
        })
    results.sort(key=lambda r: r["score"], reverse=True)
    return {
        "role": role, "ran_at": time.time(),
        "judge_provider": judge_provider, "judge_model": judge_model or "",
        # What this run was actually conducted under. Without these, a stored report is a score
        # against inputs and grading criteria that can move underneath it -- two runs weeks
        # apart were previously indistinguishable in the record even if the battery, the rubric
        # or the chair's own prompt had been edited between them. Comparing reports across
        # differing fingerprints compares different experiments.
        "battery_fingerprint": _fingerprint(*(q["label"] + q["prompt"] for q in battery)),
        "rubric_fingerprint": _fingerprint(*(f"{k}:{w}:{d}" for k, w, d in rubric)),
        "chair_prompt_fingerprint": _fingerprint(system_prompt),
        # The operating envelope this run was conducted under, beside the three fingerprints.
        # Both of these can move without a single character of this repo changing, and both
        # change what a candidate is able to produce: max_tokens decides whether a chair's
        # structured block survives at all (see llm_engine.MAX_TOKENS on what a tight budget
        # truncates first), and a provider SDK upgrade can alter defaults and response handling
        # underneath an unchanged model name. Recorded, not gated on -- comparable_history
        # still keys off the three fingerprints alone, because deciding that a token-budget or
        # SDK change makes two runs incomparable is a judgment about what counts as the same
        # experiment, not a fact this module gets to assert.
        "max_tokens": llm_engine.MAX_TOKENS,
        "provider_sdk_versions": _provider_sdk_versions(),
        "candidates": results,
    }


def _load_all() -> dict:
    if RESULTS_PATH.exists():
        try:
            return json.loads(RESULTS_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_report(role: str, report: dict) -> None:
    """Prepend to this role's run history, newest first, capped at HISTORY_LIMIT.

    This used to overwrite: one report per role, no series -- so a model that had got WORSE was
    indistinguishable from one that was always this good, which is the degradation case a
    model optimizer is supposed to catch. History alone would not have been enough, and would
    have been worse than none: a trend across silently-changing batteries is a misleading
    trend. That is why the report now carries the battery/rubric/chair-prompt fingerprints it
    ran under, and why load_history is the accessor that exposes them together.

    The newest report also stays at the role's own key, so every existing reader keeps working
    unchanged.
    """
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_reports = _load_all()
    previous = all_reports.get(role)
    history = list(all_reports.get(_history_key(role)) or [])
    if previous and (not history or history[0] is not previous):
        # Adopt a pre-history store's single stored report as the first history entry rather
        # than losing it the first time this runs after the change.
        if not any(h.get("ran_at") == previous.get("ran_at") for h in history):
            history.insert(0, previous)
    history.insert(0, report)
    all_reports[role] = report
    all_reports[_history_key(role)] = history[:HISTORY_LIMIT]
    RESULTS_PATH.write_text(json.dumps(all_reports, indent=2))


def _history_key(role: str) -> str:
    return f"{role}__history"


def load_report(role: str) -> Optional[dict]:
    """The most recent run for this role. Unchanged by the move to a history."""
    return _load_all().get(role)


def load_history(role: str) -> list[dict]:
    """Every retained run for this role, newest first. Comparing two entries is only
    meaningful when their battery/rubric/chair_prompt fingerprints match -- see
    comparable_history."""
    return list(_load_all().get(_history_key(role)) or [])


def comparable_history(role: str) -> list[dict]:
    """The runs that can honestly be compared with the newest one: those conducted under the
    same battery, rubric and chair prompt. This is what makes 'has this model degraded?' a
    real question rather than a trend line across three different experiments."""
    history = load_history(role)
    if not history:
        return []
    newest = history[0]
    keys = ("battery_fingerprint", "rubric_fingerprint", "chair_prompt_fingerprint")
    return [h for h in history if all(h.get(k) == newest.get(k) for k in keys)]
