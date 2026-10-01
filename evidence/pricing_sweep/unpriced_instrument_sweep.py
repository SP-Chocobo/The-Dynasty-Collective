"""Which recorded findings were measured against a board this repository no longer builds?

`#256`, the step-4 sweep. `#253` wired `sleeper_projections` into the three live board-building
call sites that lacked it. On the fixture league that moves the board from **256 priced rows to
481** and adds a whole tier of players -- ones the vendor does not cover whom the league's own
scoring can price. A measurement taken against the 256-row board is not WRONG; it describes a
board that no longer exists, which is the same species as `#248`'s stale `#205` deficit and has
to be found the same way: by asking the instruments, not by remembering.

THE DISCRIMINATOR IS MECHANICAL. A board is scoring-aware if and only if its builder was handed
`sleeper_projections`. So this walks every tracked `.py`, finds every `compute_draft_board` and
`build_snapshot` call in its syntax tree, and reports which ones pass it. No judgement, no list.

WHAT A HIT MEANS, AND WHAT IT DOES NOT. Three quite different things land in the same bucket and
the report keeps them apart rather than summing them:

  PRODUCTION      a live surface. After `#253` there should be none, and `test_live_board_pricing`
                  is the ratchet that keeps it that way -- this sweep is its independent check.
  INSTRUMENT      a probe, ablation or battery whose published numbers may rest on the old board.
                  These are the step-4 candidates.
  DELIBERATE      an instrument whose whole question is the unpriced board -- the pricing-path
                  cut in `carried_rate_probe.py` needs an unpriced arm BY CONSTRUCTION. Flagging
                  it would be the sweep misreading its own evidence.

The DELIBERATE set is the one judgement call here, so it is named in the output with its reason
rather than silently excluded, and it is deliberately tiny.

WHAT THIS SWEEP CANNOT SEE, stated because it bounds every number it prints. It detects whether
`sleeper_projections` is PASSED, not whether the value passed is non-`None`. A caller handing it
a variable that happens to be `None` reads here as priced. Checked: zero board-building calls in
the tree pass a literal `None`, so the production count is sound today -- but a probe that
threads a nullable variable through (this repo has one, `carried_rate_probe.py`, whose unpriced
arm IS its experiment) is invisible to a syntax-tree scan by construction. An exemption list for
such cases was written and then removed: it stayed empty, and an exemption nobody needs is an
exemption that rots into a lie about coverage.

SECOND BLIND SPOT, undisclosed until `#260` and responsible for two of `#256`'s four named
instruments. A call that splats a pre-built dict -- `compute_draft_board(m, db, picks, **kw)` --
carries `kw.arg is None` for that entry, so the old `if kw.arg` filter dropped it and the call
reported an EMPTY kwarg set. Empty read as unpriced. `run_216_review_probe.py` (3 calls) and
`run_216_fix_probe.py` (1 call) both build `kw = dict(..., sleeper_projections=season, ...)` and
splat it; both were published as resting on the old board while passing pricing on every call.
The scan still cannot follow a dict into a splat -- that limit is real and unfixable statically
-- but such calls now report INDETERMINATE in their own section instead of being counted as
absent. A blind spot stated is a bound; a blind spot scored as a measurement is a false finding.

Static only: reads syntax trees, runs no engine, changes nothing.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDERS = ("compute_draft_board", "build_snapshot")
PRICING = "sleeper_projections"

def live_modules() -> set[str]:
    """The live surface, DERIVED: `app.py` plus every module it imports.

    The first draft of this sweep hand-listed the live set and got it wrong -- it named
    `draft_counterfactual`, `roster_diagnostics` and `prediction_record` as production, and
    `app.py` imports none of the three. That is `#126`'s failure (one home for a vocabulary,
    derived, never hand-listed) committed inside the instrument written to audit `#126`-shaped
    problems. `app.py` IS the live surface by construction -- it is the Streamlit script -- so
    its own import list is the answer and cannot go stale.

    One level, not transitive: a module app.py imports can put a board in front of a person;
    something four hops down a measurement harness cannot, and widening the net would re-import
    the same over-broad guess by another route.
    """
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    names = {"app.py"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] + ".py" for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0] + ".py")
    return {n for n in names if (ROOT / n).exists()}


def tracked_python() -> list[Path]:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z", "*.py"],
                         capture_output=True, text=True, check=True).stdout
    return [ROOT / p for p in out.split("\0") if p]


PRICED = "priced"
UNPRICED = "unpriced"
INDETERMINATE = "indeterminate"


def board_calls(path: Path) -> list[tuple[str, int, str]]:
    """(builder, line, verdict) for every board-building call in this file.

    THREE-STATE, and the third state is the whole point. This returned a bool until #260,
    and the bool was a lie of exactly the kind this repo forbids everywhere else: a call
    site that splats a pre-built dict (`dr.compute_draft_board(m, db, picks, **kw)`) has
    `kw.arg is None` for that entry, the `if kw.arg` filter drops it, and the call read as
    an EMPTY kwarg set -- indistinguishable from a caller that genuinely omitted pricing.
    Two of #256's four named findings were that artifact: `run_216_review_probe.py` and
    `run_216_fix_probe.py` both build `kw = dict(..., sleeper_projections=season, ...)` and
    splat it, and both were reported unpriced while passing the argument on every call.

    A syntax-tree scan cannot follow a dict into a splat. That is a real limit, and the
    honest report of a real limit is INDETERMINATE -- never `unpriced`. The absence
    contract the engine obeys (EXCLUDE / PROPAGATE / ORDER LAST, and never 0.0 for
    unmeasured) applies to the instrument that polices it.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name not in BUILDERS:
            continue
        named = {kw.arg for kw in node.keywords if kw.arg}
        splatted = any(kw.arg is None for kw in node.keywords)
        if PRICING in named:
            verdict = PRICED
        elif splatted:
            verdict = INDETERMINATE      # a dict went in; this scan cannot see inside it
        else:
            verdict = UNPRICED
        found.append((name, node.lineno, verdict))
    return found


def main() -> int:
    live = live_modules()
    prod_hits, instrument_hits, test_hits, clean = [], [], [], []
    indeterminate: list[tuple[str, int, list]] = []
    for path in tracked_python():
        rel = path.relative_to(ROOT).as_posix()
        calls = board_calls(path)
        if not calls:
            continue
        unpriced = [(b, ln) for b, ln, v in calls if v == UNPRICED]
        unknown = [(b, ln) for b, ln, v in calls if v == INDETERMINATE]
        if unknown:
            indeterminate.append((rel, len(calls), unknown))
        if not unpriced:
            if not unknown:
                clean.append((rel, len(calls)))
            continue
        row = (rel, len(calls), unpriced)
        if path.name in live:
            prod_hits.append(row)
        elif path.name.startswith("test_"):
            # A unit test building an unpriced board is usually CORRECT: it is exercising a
            # function against a synthetic fixture, not publishing a finding about the engine.
            # Lumping these with the probes would have reported 34 step-4 candidates when the
            # real number is the probe count alone.
            test_hits.append(row)
        else:
            instrument_hits.append(row)

    print(f"tracked .py files building a board: "
          f"{len(clean) + len(prod_hits) + len(instrument_hits) + len(test_hits)}")
    print(f"live surface, derived from app.py's imports: {len(live)} modules\n")

    print(f"=== PRODUCTION with an unpriced board  ({len(prod_hits)}) ===")
    print("    after #253 this should be EMPTY; test_live_board_pricing is the standing ratchet")
    for rel, total, unpriced in prod_hits:
        print(f"  {rel}: {len(unpriced)} of {total} unpriced -> {unpriced}")
    if not prod_hits:
        print("  (none)")

    print(f"\n=== INSTRUMENTS whose numbers may rest on the OLD board  ({len(instrument_hits)}) ===")
    print("    step-4 candidates: stale evidence, not wrong evidence")
    for rel, total, unpriced in sorted(instrument_hits):
        print(f"  {rel}: {len(unpriced)} of {total} unpriced")

    print(f"\n=== UNIT TESTS with unpriced boards  ({len(test_hits)}) ===")
    print("    expected and usually correct -- synthetic fixtures, not published findings")
    print(f"    {sum(len(u) for _, _, u in test_hits)} unpriced calls across "
          f"{len(test_hits)} files; not step-4 work")

    print(f"\n=== INDETERMINATE: pricing passed via **kwargs, unreadable by a syntax scan  "
          f"({len(indeterminate)}) ===")
    print("    NOT a finding. A dict splat hides its keys from ast; reporting these as")
    print("    `unpriced` is what produced 2 of #256's 4 named instruments (#260).")
    for rel, total, unknown in sorted(indeterminate):
        print(f"  {rel}: {len(unknown)} of {total} indeterminate -> {unknown}")
    if not indeterminate:
        print("  (none)")

    print(f"\n=== files ALREADY fully scoring-aware  ({len(clean)}) ===")
    for rel, total in sorted(clean):
        print(f"  {rel}: {total} call(s), all priced")

    # Which of the suspect instruments does the register actually CITE? A stale instrument
    # nobody quoted has no finding to re-measure.
    plan = (ROOT / "POST_AUDIT_PLAN.md").read_text(encoding="utf-8")
    print(f"\n=== of the suspect instruments, cited in POST_AUDIT_PLAN ===")
    cited = [rel for rel, _, _ in instrument_hits if Path(rel).name in plan]
    for rel in sorted(cited):
        print(f"  {rel}")
    if not cited:
        print("  (none cited)")
    print(f"\nsuspect: {len(instrument_hits)}   of those cited by the register: {len(cited)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
