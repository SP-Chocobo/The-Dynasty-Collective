"""What each provider call actually cost, and whether its answer arrived whole.

WHY THIS IS A SIDE CHANNEL AND NOT A RETURN VALUE. Every provider caller in this app returns a
bare `str` -- the response object, which carries token usage, the stop reason and the resolved
model id, is discarded inside the function. That single fact is the structural cause of #100
(nothing meters a call), the recoverable half of #99 (truncation is undetectable), and part of
#109 (the served model is unrecoverable). The obvious repair is to return something richer than
a string, but that return value is passed straight through by twelve call sites up into app.py,
and §14 established the strongest property this app has: EVERY provider caller returns a
"⚠️ ..." string rather than raising, so one dead provider cannot take out the panel. Rebuilding
that chain to carry a new type would put that property at risk to gain bookkeeping.

So the metadata is recorded HERE, beside the call, while the string keeps flowing unchanged.
Nothing in this module can alter what a caller returns.

NOTHING HERE MAY EVER RAISE. A metering failure that broke a provider call would be strictly
worse than no metering: it would convert a working answer into a failure, in exactly the code
path whose whole design goal is that it cannot fail hard. Every public function is total, and a
test plants a response object that raises on attribute access to prove it.

ABSENCE IS RECORDED AS ABSENCE. A provider that does not report usage yields None, never 0 --
"this call used no tokens" and "this call's cost is unknown" are different claims, and only one
of them is ever true. Same rule the board applies to an unpriced row.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

# How many call records are kept. A long Draft Room session makes a lot of calls and this lives
# in memory for the life of the process, so it is a ring buffer rather than an unbounded list:
# the oldest record is dropped, never the newest. Sized so a full multi-chair debate plus a
# benchmark sweep fits comfortably.
LEDGER_CAPACITY = 500

# ---------------------------------------------------------------------------------------------
# Completion state. FOUR states, not two.
#
# "Did the answer arrive whole" has more than a yes and a no, and collapsing them is the mistake
# §18/#112 named: a provider that did not tell us must not be recorded as though it said
# "complete". UNKNOWN is a real answer and the honest one when an SDK shape changes underneath
# an unchanged model name (#110's class), which is precisely when a silent wrong reading would
# be most damaging.
COMPLETE = "complete"      # the provider said it finished normally
TRUNCATED = "truncated"    # the provider said it hit the output cap -- the text is a fragment
BLOCKED = "blocked"        # the provider stopped for its own policy reasons, not for length
UNKNOWN = "unknown"        # nothing usable was reported; make no claim either way
FAILED = "failed"          # a request WAS made and it raised
# The request never left this machine -- no API key configured, or the provider SDK is not
# installed. §14 recorded that four distinct causes collapse into one "⚠️ ... request failed"
# signal, separable only by reading the exception text. This is the half of that collapse which
# can be separated with certainty, and separating it matters: a call that never ran cost
# nothing, could not have been truncated, and is a configuration problem rather than a provider
# outage. §22's unavailability marker has to stay agnostic about which of three things happened
# to a call that DID run; it never had to be agnostic about one that did not.
NOT_ATTEMPTED = "not_attempted"


@dataclass
class CallRecord:
    """One provider call, as observed from the outside."""
    provider: str
    role: str
    model_requested: Optional[str] = None
    # What the provider said it actually served. Distinct from model_requested on purpose:
    # #109 recorded that all three default model ids are floating aliases, so the requested name
    # does not identify what ran. Whether a given SDK really resolves an alias here is NOT yet
    # verified against a live call -- see this module's own tests, which pin the extraction, not
    # the provider's behaviour.
    model_reported: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    completion_state: str = UNKNOWN
    completion_detail: Optional[str] = None
    latency_ms: Optional[float] = None
    ok: bool = True
    error: Optional[str] = None
    ts: float = field(default_factory=time.time)

    @property
    def total_tokens(self) -> Optional[int]:
        """None unless BOTH halves are known. A half-known total is a wrong total, and the one
        place a plausible-looking number would do real damage is a cost estimate."""
        if self.input_tokens is None or self.output_tokens is None:
            return None
        return self.input_tokens + self.output_tokens


_lock = threading.Lock()
_ledger: deque[CallRecord] = deque(maxlen=LEDGER_CAPACITY)
_sequence = 0


def _int_or_none(value: Any) -> Optional[int]:
    """A token count, or None. Booleans are rejected (bool subclasses int, and True would
    otherwise become a token count of 1), as is anything that will not cleanly become an int."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _chain(root: Any, *names: str) -> Any:
    """Walk an attribute path, returning None the moment it stops existing.

    Deliberately tolerant: these paths describe THIRD-PARTY SDK response shapes, which change
    without this repo changing (#110), and a metering read must degrade to "unknown" rather than
    take down a working provider call. getattr is also wrapped, because a response object is
    free to raise from a property.
    """
    current = root
    for name in names:
        if current is None:
            return None
        try:
            current = getattr(current, name, None)
        except Exception:  # noqa: BLE001 - an SDK property that raises must not break metering
            return None
    return current


# ---------------------------------------------------------------------------------------------
# Per-provider extraction.
#
# One function per SDK family, because the three shapes genuinely differ and a single "find the
# tokens" heuristic would be guessing. Each reads defensively and each is pinned by tests that
# feed it a stand-in response object -- the tests prove THIS CODE reads a given shape correctly,
# and deliberately do not claim to prove what a live provider actually returns. That second
# claim needs a live call and is recorded as still unverified.

def _anthropic_completion(response: Any) -> tuple[str, Optional[str]]:
    reason = _chain(response, "stop_reason")
    if reason is None:
        return UNKNOWN, None
    reason = str(reason)
    if reason == "max_tokens":
        return TRUNCATED, reason
    if reason in ("end_turn", "stop_sequence", "tool_use"):
        return COMPLETE, reason
    if reason == "refusal":
        return BLOCKED, reason
    return UNKNOWN, reason


def _gemini_completion(response: Any) -> tuple[str, Optional[str]]:
    candidates = _chain(response, "candidates")
    reason = None
    try:
        if candidates:
            reason = _chain(candidates[0], "finish_reason")
    except Exception:  # noqa: BLE001 - candidates may be any sequence-ish object
        reason = None
    if reason is None:
        return UNKNOWN, None
    # finish_reason is an enum; its name is what carries the meaning across SDK versions.
    text = str(getattr(reason, "name", reason)).upper()
    if "MAX_TOKEN" in text:
        return TRUNCATED, text
    if text == "STOP":
        return COMPLETE, text
    if text in ("SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII"):
        return BLOCKED, text
    return UNKNOWN, text


def _openai_completion(response: Any) -> tuple[str, Optional[str]]:
    status = _chain(response, "status")
    detail = _chain(response, "incomplete_details", "reason")
    detail = str(detail) if detail is not None else None
    if status is None:
        return UNKNOWN, detail
    status = str(status)
    if status == "completed":
        return COMPLETE, detail
    if status == "incomplete":
        if detail == "max_output_tokens":
            return TRUNCATED, detail
        if detail == "content_filter":
            return BLOCKED, detail
        return UNKNOWN, detail
    return UNKNOWN, detail


_EXTRACTORS = {
    # provider -> (completion reader, usage path pair)
    "claude": (_anthropic_completion, (("usage", "input_tokens"), ("usage", "output_tokens"))),
    "gemini": (_gemini_completion, (("usage_metadata", "prompt_token_count"),
                                    ("usage_metadata", "candidates_token_count"))),
    "openai": (_openai_completion, (("usage", "input_tokens"), ("usage", "output_tokens"))),
}


def describe(provider: str, response: Any) -> dict:
    """Read what one response object reports, without judging it. Total: any unreadable shape
    degrades to unknown/None rather than raising."""
    extractor = _EXTRACTORS.get(provider)
    if extractor is None:
        return {"completion_state": UNKNOWN, "completion_detail": None,
                "input_tokens": None, "output_tokens": None, "model_reported": None}
    completion, (in_path, out_path) = extractor
    try:
        state, detail = completion(response)
    except Exception:  # noqa: BLE001 - never let a shape change break the call being metered
        state, detail = UNKNOWN, None
    return {
        "completion_state": state,
        "completion_detail": detail,
        "input_tokens": _int_or_none(_chain(response, *in_path)),
        "output_tokens": _int_or_none(_chain(response, *out_path)),
        # Anthropic and OpenAI both echo the served model; Gemini uses model_version. Whichever
        # is present is recorded, absence stays absence.
        "model_reported": (_chain(response, "model") or _chain(response, "model_version") or None),
    }


# ---------------------------------------------------------------------------------------------
# The ledger.

def record(provider: str, role: str, *, response: Any = None, model_requested: Optional[str] = None,
           latency_ms: Optional[float] = None, ok: bool = True,
           error: Optional[str] = None) -> Optional[CallRecord]:
    """Append one call record. Returns it, or None if recording itself failed.

    Wrapped whole: a caller does `provider_meter.record(...)` beside its return statement, and
    NOTHING this function can do may change what that caller returns. If bookkeeping breaks, the
    answer still ships.
    """
    try:
        fields = {"completion_state": FAILED if not ok else UNKNOWN, "completion_detail": None,
                  "input_tokens": None, "output_tokens": None, "model_reported": None}
        if response is not None:
            fields = describe(provider, response)
        entry = CallRecord(
            provider=provider, role=role, model_requested=model_requested,
            latency_ms=latency_ms, ok=ok, error=error, **fields)
        with _lock:
            global _sequence
            _sequence += 1
            _ledger.append(entry)
        return entry
    except Exception:  # noqa: BLE001 - metering must never break a provider call
        return None


def mark() -> int:
    """A token naming 'now', for `since`. Lets one debate meter exactly its own calls without
    every caller having to thread an id through a chain it does not own."""
    with _lock:
        return _sequence


def since(marker: int) -> list[CallRecord]:
    """Every record appended after `marker`, oldest first.

    Records evicted by the ring buffer are simply absent; this reports what is still held, and
    `totals` says how many records it summed so a caller can see it is looking at fewer calls
    than it made rather than reading a quietly short total as complete.
    """
    with _lock:
        held = list(_ledger)
        current = _sequence
    take = max(0, min(current - marker, len(held)))
    return held[len(held) - take:] if take else []


def totals(records: Optional[list[CallRecord]] = None) -> dict:
    """Aggregate a set of records. Token totals are None unless EVERY record contributing to
    them reported its own -- a total assembled from some-known-some-unknown is a number that
    reads as authoritative and is not, which is the failure mode a cost display cannot afford.
    `..._reported` counts say how much of the set was actually measurable."""
    entries = list(_ledger) if records is None else records
    inputs = [e.input_tokens for e in entries]
    outputs = [e.output_tokens for e in entries]
    return {
        "calls": len(entries),
        "ok": sum(1 for e in entries if e.ok),
        "failed": sum(1 for e in entries if not e.ok),
        "truncated": sum(1 for e in entries if e.completion_state == TRUNCATED),
        "blocked": sum(1 for e in entries if e.completion_state == BLOCKED),
        "unknown_completion": sum(1 for e in entries if e.completion_state == UNKNOWN),
        "not_attempted": sum(1 for e in entries if e.completion_state == NOT_ATTEMPTED),
        "input_tokens": sum(inputs) if entries and all(v is not None for v in inputs) else None,
        "output_tokens": sum(outputs) if entries and all(v is not None for v in outputs) else None,
        "usage_reported": sum(1 for e in entries if e.total_tokens is not None),
        "latency_ms": (round(sum(e.latency_ms for e in entries if e.latency_ms is not None), 1)
                       if any(e.latency_ms is not None for e in entries) else None),
    }


def recent(limit: int = 20) -> list[dict]:
    """The last few records as plain dicts, newest first -- for a UI or a stored run record."""
    with _lock:
        held = list(_ledger)
    return [asdict(e) for e in reversed(held[-limit:])]


def reset() -> None:
    """Empty the ledger. For tests and for a deliberate 'start counting from here'."""
    global _sequence
    with _lock:
        _ledger.clear()
        _sequence = 0


# ---------------------------------------------------------------------------------------------
# Resource limits (#105) and the metered call wrapper.

# The output cap already existed as llm_engine.MAX_TOKENS. These are the two knobs that did not.
#
# REQUEST_TIMEOUT_SECONDS: before this, no provider client or request carried a timeout of any
# kind, so a hung provider hung the Streamlit script with no user recourse -- a UI that can wait
# forever is a defect regardless of what the right number is. The VALUE is provisional and is a
# policy question (see the decision register): it must be generous, because every caller enables
# server-side web search and a search-and-synthesize turn is legitimately slow.
#
# CLIENT_MAX_RETRIES: §14 established that this app performs no retries. What it did NOT
# establish is that no retries HAPPEN -- the provider SDKs carry their own defaults (the
# Anthropic and OpenAI clients both retry automatically unless told otherwise), so "no retries"
# was true of this repo and possibly false of the running system. Setting it explicitly makes
# the app's intent real instead of merely stated. None means "leave the SDK's default alone".
REQUEST_TIMEOUT_SECONDS = 180.0
CLIENT_MAX_RETRIES: Optional[int] = None

# Which limit knobs were actually accepted by the installed SDKs, most recent attempt per
# provider. A knob the SDK does not accept is DROPPED rather than passed (passing an unknown
# kwarg would raise, and that exception would be caught by the caller's own handler and returned
# as "⚠️ <provider> request failed" -- i.e. a wrong kwarg name would silently disable the
# provider entirely). Dropping is safe; dropping SILENTLY would not be, so it is recorded here
# and surfaced, because a resource limit that quietly does not apply is worse than none.
applied_limits: dict[str, dict] = {}


def supported_kwargs(target: Any, **candidates: Any) -> tuple[dict, list[str]]:
    """(accepted, dropped_names) -- the subset of `candidates` that `target` will accept.

    Exists because the three provider SDKs are not installed in every environment this repo is
    developed in, their constructor signatures differ, and they change between majors. Rather
    than assume a kwarg name is right, this asks the callable. If the signature cannot be read
    at all, NOTHING is passed: declining to set a limit is recoverable, guessing wrong is not.
    """
    import inspect
    try:
        parameters = inspect.signature(target).parameters
    except (TypeError, ValueError):
        return {}, sorted(candidates)
    if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in parameters.values()):
        accepted = dict(candidates)          # **kwargs takes anything
    else:
        accepted = {k: v for k, v in candidates.items() if k in parameters}
    return accepted, sorted(k for k in candidates if k not in accepted)


def limit_kwargs(provider: str, target: Any, **candidates: Any) -> dict:
    """`supported_kwargs`, recording per provider which knobs applied and which were dropped."""
    accepted, dropped = supported_kwargs(target, **candidates)
    applied_limits[provider] = {"applied": sorted(accepted), "dropped": dropped}
    return accepted


def client_limits(provider: str, client_class) -> dict:
    """The resource-limit kwargs this provider's client class actually accepts (#105).

    Asks the SDK rather than assuming: an unknown kwarg would raise, and that exception would be
    caught by the caller's own handler and returned as "⚠️ <provider> request failed", i.e. a
    wrong name here would silently disable the provider outright. `limit_kwargs` drops what is
    not accepted and RECORDS the drop in applied_limits, so a limit that does not
    apply is visible rather than silently absent.
    """
    candidates = {"timeout": REQUEST_TIMEOUT_SECONDS}
    if CLIENT_MAX_RETRIES is not None:
        candidates["max_retries"] = CLIENT_MAX_RETRIES
    return limit_kwargs(provider, client_class, **candidates)


def gemini_limits(genai, types) -> dict:
    """Gemini's timeout lives inside HttpOptions rather than on the client, and its unit is
    MILLISECONDS -- believed correct for google-genai, and NOT verified against a live SDK in
    the environment this was written in (none of the three provider SDKs is installed here).
    Constructing HttpOptions is therefore attempted, not assumed: if the field is named
    differently in the installed version the attempt is recorded as dropped and the client is
    built exactly as it was before, rather than failing the call."""
    try:
        options = types.HttpOptions(timeout=int(REQUEST_TIMEOUT_SECONDS * 1000))
    except Exception:  # noqa: BLE001 - an unknown field must not disable the provider
        applied_limits["gemini"] = {"applied": [], "dropped": ["http_options"]}
        return {}
    return limit_kwargs("gemini", genai.Client, http_options=options)


class _RoleScope:
    """Names the chair a provider call is being made for, without widening PROVIDER_CALLERS.

    §22 recorded chair-contract stability as a MET architectural mandate, so the caller
    signature is deliberately left exactly as it is; the role travels beside the call instead.
    """
    def __init__(self, role: str):
        self.role, self._token = role, None

    def __enter__(self):
        self._token = _role_var.set(self.role)
        return self

    def __exit__(self, *exc_info):
        if self._token is not None:
            _role_var.reset(self._token)
        return False


import contextvars  # noqa: E402 - kept beside its only user

_role_var: contextvars.ContextVar[str] = contextvars.ContextVar("provider_meter_role", default="")


def role_scope(role: str) -> _RoleScope:
    return _RoleScope(role)


def current_role() -> str:
    return _role_var.get()


# Set on an exception that `metered` has already recorded, so a caller's own outer handler can
# record pre-flight failures without double-counting the ones already seen here.
_RECORDED_FLAG = "_provider_meter_recorded"


def record_not_attempted(provider: str, reason: str) -> Optional[CallRecord]:
    """Record that no request was made at all, and why."""
    entry = record(provider, current_role(), ok=False, error=reason)
    if entry is not None:
        entry.completion_state = NOT_ATTEMPTED
        entry.completion_detail = reason
    return entry


def record_preflight_failure(provider: str, exc: BaseException) -> Optional[CallRecord]:
    """Record a failure that happened BEFORE a request was built -- typically the provider SDK
    not being installed. A failure `metered` already saw is skipped rather than counted twice.

    Total, like everything here: called from inside an `except` block whose only job is to
    return a "⚠️ ..." string, so it must not be able to raise on the way."""
    try:
        if getattr(exc, _RECORDED_FLAG, False):
            return None
        if isinstance(exc, ImportError):
            return record_not_attempted(provider, f"sdk_not_installed: {exc}")
        return record_not_attempted(provider, f"{type(exc).__name__}: {exc}")
    except Exception:  # noqa: BLE001
        return None


def metered(provider: str, invoke, *, model_requested: Optional[str] = None):
    """Run one provider call, record what it cost, and return the response object untouched.

    On failure the record is written and the exception is RE-RAISED, so each caller's own
    `except Exception` still produces its own "⚠️ <provider> request failed: ..." string exactly
    as before. This wrapper cannot convert a working call into a failed one and cannot change
    any caller's return value -- both pinned by tests.
    """
    started = time.perf_counter()
    try:
        response = invoke()
    except Exception as exc:  # noqa: BLE001 - recorded, then handed straight back to the caller
        record(provider, current_role(), model_requested=model_requested, ok=False,
               error=f"{type(exc).__name__}: {exc}",
               latency_ms=round((time.perf_counter() - started) * 1000, 1))
        try:
            setattr(exc, _RECORDED_FLAG, True)   # some exception types reject attributes
        except Exception:  # noqa: BLE001
            pass
        raise
    record(provider, current_role(), response=response, model_requested=model_requested,
           latency_ms=round((time.perf_counter() - started) * 1000, 1))
    return response
