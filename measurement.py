"""The instrument standard (ENGINEERING_DOCTRINE, "The instrument standard"), made runnable.

Doctrine that cannot be executed is doctrine that gets skipped under time pressure, and every
rule here exists because it was skipped under time pressure on 2026-09-06. This module makes
the correct path the easy one for the three rules that are mechanical. M5, M7 and M8 are
judgement and stay in prose; M2 is domain-specific and belongs in each experiment.

Deliberately dependency-free and side-effect-light so a probe can import it without dragging in
the engine.
"""
from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Callable, Optional


class VacuousPopulation(Exception):
    """M4: a rate over a population that cannot produce the phenomenon is not a rate."""


class NotReproduced(Exception):
    """M1: a number produced once has been observed, not measured."""


def rate(hits: int, n: int, of: str, *, digits: int = 1) -> str:
    """A percentage that CANNOT be formatted without its population and its scope (M4, M9).

    `of` is not decoration and is not optional: "34%" is unreadable and "34% of all priced board
    rows, three formats" is a finding. An empty population raises rather than returning "0.0%",
    because a rate over nothing is the shape #172 took -- a perfect measurement of a term that
    was structurally incapable of being anything else.
    """
    if n <= 0:
        raise VacuousPopulation(
            f"rate over an empty population ({of!r}): {hits}/{n}. "
            "Confirm the population CAN produce the phenomenon before reporting a rate (M4)."
        )
    if not of or not of.strip():
        raise ValueError("a rate must name its population and scope (M9)")
    return f"{hits}/{n} = {100.0 * hits / n:.{digits}f}% of {of}"


def counted(values, predicate=lambda v: v > 0) -> dict:
    """M6: absence and a measured zero counted SEPARATELY, in the instrument.

    `if value:` conflates them. Returns present/absent/matching so a caller cannot accidentally
    report "not measured" for a legitimate 0.0.
    """
    present = [v for v in values if v is not None]
    return {"n": len(values), "present": len(present),
            "absent": len(values) - len(present),
            "matching": sum(1 for v in present if predicate(v))}


def persist_each(path: str, payload: Any) -> None:
    """M3: durable partials. Write after EVERY unit of work, atomically.

    A long run will die -- #176's first attempt died seven completed runs into its first format
    and lost all of them, because the report was written once per format. Atomic replace so a
    death mid-write leaves the previous good file rather than a truncated one.

    `default=str` IS A DELIBERATE TRADE AND IT COSTS SOMETHING. It keeps numpy/pandas scalars
    (which every probe in this repo produces) from raising, at the price of stringifying an
    object that should have been caught -- a set lands as "{1, 2}", which is useless as data and
    silent as a bug. Structure the payload in plain types; do not rely on this to rescue one
    that is not. Genuinely unserialisable input (a cycle) still raises, and the previous good
    file still survives it, which is what the test pins.
    """
    d = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".part")
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(payload, fh, indent=2, default=str)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def reproduced(run: Callable[[], Any], *, key: Optional[Callable[[Any], Any]] = None) -> Any:
    """M1: run it twice from scratch and refuse to return a result that differs.

    A finding produced once has been observed, not measured. #176 was published on a single run
    and did not survive its first reproduction; this makes that failure loud at the point of
    measurement instead of an hour later in front of the owner.

    `key` extracts the part that must be stable, for results carrying wall-clock or paths.
    """
    a = run()
    b = run()
    ka = key(a) if key else a
    kb = key(b) if key else b
    if ka != kb:
        raise NotReproduced(
            "two runs of the same measurement disagree -- the instrument is not deterministic "
            "or is carrying state between runs (M1).\n"
            f"  first : {ka!r}\n  second: {kb!r}"
        )
    return a
