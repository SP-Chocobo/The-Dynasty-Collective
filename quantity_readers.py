"""Every quantity this engine produces, and what -- if anything -- reads it.

WHY (#141 / #138). This codebase keeps finding the same defect by hand: a value computed or
ingested, carried, sometimes displayed, and then read by nothing that decides. `waiting_cost`,
`marginal_value_full_eligibility`, `bye_week`, bench depth, `trend_30d` -- each found
individually, each costing a session. A quantity nobody reads is not merely waste: it reads as
capability the engine does not have, and it is invisible precisely because everything about it
looks correct.

WHY THE FIRST ATTEMPT WAS DISCARDED, because the failure is instructive. It scanned every dict
literal in the tree and produced 246 candidates that were mostly table headers and label
constants -- and it classified `waiting_cost` as a DECISION input, which was wrong. Its own
non-vacuity check caught it. Two things fixed that here:

  CLOSED SET. Candidates come from the engine's declared OUTPUT SURFACES -- the board's own
  column lists, the snapshot dataclasses, the analysis dicts -- not from every string that
  looks like a key. If a quantity is not on one of those surfaces it is not a quantity, it is
  a local.

  READS ARE PARSED, NOT GREPPED. A name inside a comment, a docstring, a column list, or a
  test is not a read. Only `x["name"]`, `x.get("name")` and attribute access in a PRODUCTION
  module count, which is what separates "displayed" from "decided on" from "dropped".

THE THREE ANSWERS, and the middle one is the whole point of having three:

  DECISION     -- read by a module that computes a value or an ordering. It participates.
  OBSERVABLE   -- read only by UI or diagnostics. Correct for many quantities, and this
                  codebase deliberately puts several here (bye_collision, marginal_lineup_value
                  when its contract is pinned but unwired). NOT a defect.
  WRITE_ONLY   -- read by nothing in production. The defect (#138).

Tests are deliberately NOT readers. A quantity exercised only by its own test is still
write-only in production, and counting tests would hide exactly the cases worth finding.
"""

from __future__ import annotations

import ast
from pathlib import Path

_HERE = Path(__file__).parent

DECISION = "decision"
OBSERVABLE = "observable"
#: Read by a module only to copy it straight into another output -- a relay, not a consumer.
#: THIS IS THE STATE THAT DEFEATED TWO EARLIER VERSIONS OF THIS SCANNER. `pick_synthesis` is a
#: scoring module and it reads `waiting_cost`, so a naive reader-module check calls that a
#: decision input. It is not: the read's only destination is another dict, and the quantity's
#: real terminus is the UI one hop later. Counting a relay as a consumer hides exactly the
#: write-only chains this exists to find.
CARRIED = "carried"

#: Emitted so a reader COULD reconstruct how a value was reached, while the local it was
#: computed from feeds that value directly. The number does real work; its published form is
#: unread. That is #119 -- an auditability gap, not a correctness one -- and collapsing it into
#: WRITE_ONLY would report a load-bearing term as dead weight.
DECOMPOSITION = "decomposition"
WRITE_ONLY = "write_only"

#: Modules whose reads mean a quantity participates in a value or an ordering.
SCORING_MODULES = (
    "draft_room.py", "pick_synthesis.py", "draft_strategy.py", "lineup_optimizer.py",
    "depth_ratings.py", "player_universe.py", "data_merger.py",
)

#: Modules whose reads mean a quantity is shown or reported, never scored.
OBSERVER_MODULES = (
    "app.py", "draft_board_ui.py", "roster_diagnostics.py", "screen_context.py",
    "pick_debate.py", "draft_simulation.py", "trade_analysis.py",
)


def _production_modules() -> list[Path]:
    """Every top-level module that is not a test and not a one-off measurement script.

    `run_*.py` are excluded on purpose: an instrument reading a quantity does not make that
    quantity load-bearing, and counting them would let a measurement script mask a real
    write-only finding -- the same reason tests are excluded.
    """
    return sorted(
        path for path in _HERE.glob("*.py")
        if not path.name.startswith(("test_", "run_"))
    )


def _dict_keys_returned_by(tree: ast.AST, function_name: str) -> set[str]:
    """String keys of dict literals built inside one function."""
    target = next((node for node in ast.walk(tree)
                   if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                   and node.name == function_name), None)
    if target is None:
        return set()
    keys = set()
    for node in ast.walk(target):
        if isinstance(node, ast.Dict):
            keys |= {k.value for k in node.keys
                     if isinstance(k, ast.Constant) and isinstance(k.value, str)}
    return keys


def _dataclass_fields(tree: ast.AST, class_name: str) -> set[str]:
    target = next((node for node in ast.walk(tree)
                   if isinstance(node, ast.ClassDef) and node.name == class_name), None)
    if target is None:
        return set()
    return {node.target.id for node in target.body
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)}


def _board_columns(tree: ast.AST) -> set[str]:
    """The board's own emitted column lists -- the literal lists compute_draft_board selects.

    Read from the source rather than by running a board, so the scanner needs no data and
    cannot be fooled by a column that happens to be absent from one particular pool.
    """
    target = next((node for node in ast.walk(tree)
                   if isinstance(node, ast.FunctionDef)
                   and node.name == "compute_draft_board"), None)
    if target is None:
        return set()
    columns = set()
    for node in ast.walk(target):
        if isinstance(node, ast.List) and len(node.elts) > 5:
            values = [e.value for e in node.elts
                      if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if len(values) == len(node.elts):
                columns |= set(values)
    return columns


def produced_quantities() -> dict[str, str]:
    """{quantity: the surface that emits it} -- the closed set this scanner is defined over."""
    out: dict[str, str] = {}

    def add(names, surface):
        for name in names:
            out.setdefault(name, surface)

    draft_room = ast.parse((_HERE / "draft_room.py").read_text())
    add(_board_columns(draft_room), "draft_room.compute_draft_board (board columns)")

    synthesis = ast.parse((_HERE / "pick_synthesis.py").read_text())
    add(_dataclass_fields(synthesis, "CandidateSnapshot"), "pick_synthesis.CandidateSnapshot")
    add(_dataclass_fields(synthesis, "PickSnapshot"), "pick_synthesis.PickSnapshot")

    strategy = ast.parse((_HERE / "draft_strategy.py").read_text())
    add(_dict_keys_returned_by(strategy, "pick_analysis"), "draft_strategy.pick_analysis")

    optimizer = ast.parse((_HERE / "lineup_optimizer.py").read_text())
    for name in ("optimize_lineup", "depth_exposure", "bye_collision", "bye_concentration",
                 "marginal_lineup_value"):
        add(_dict_keys_returned_by(optimizer, name), f"lineup_optimizer.{name}")

    diagnostics = ast.parse((_HERE / "roster_diagnostics.py").read_text())
    add(_dataclass_fields(diagnostics, "TeamDiagnostics"), "roster_diagnostics.TeamDiagnostics")
    return out


def _local_names_in(path: Path) -> set[str]:
    """Names used as plain VARIABLES in this module.

    A quantity that is emitted as a key and also used as a local is doing work even when its
    emitted form is unread -- draft_room computes `risk_adj` and sums it straight into
    universal_value, then publishes it as a column nobody indexes. Reporting that as write-only
    would call a load-bearing term dead.
    """
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return set()
    return {node.id for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}


def _relayed_in(path: Path) -> set[str]:
    """Names whose EVERY read in this module sits inside a dict literal's values.

    Such a read copies the quantity onward without consuming it. Distinguishing that from a
    real consumption is the difference between "pick_synthesis decides on waiting_cost" (false)
    and "pick_synthesis hands waiting_cost to the UI" (true).
    """
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return set()
    inside_dict_value, all_reads = set(), set()

    def names_read(node):
        found = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Subscript) and isinstance(child.ctx, ast.Load) \
                    and isinstance(child.slice, ast.Constant) \
                    and isinstance(child.slice.value, str):
                found.add(child.slice.value)
            elif isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) \
                    and child.func.attr == "get" and child.args \
                    and isinstance(child.args[0], ast.Constant) \
                    and isinstance(child.args[0].value, str):
                found.add(child.args[0].value)
        return found

    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for value in node.values:
                inside_dict_value |= names_read(value)
    all_reads = names_read(tree)
    # A name read ONLY inside dict values is relayed. One read anywhere else makes it consumed.
    return {name for name in inside_dict_value
            if _read_count(tree, name) == _read_count_in_dict_values(tree, name)}


def _read_count(tree: ast.AST, name: str) -> int:
    total = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load) \
                and isinstance(node.slice, ast.Constant) and node.slice.value == name:
            total += 1
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "get" and node.args \
                and isinstance(node.args[0], ast.Constant) and node.args[0].value == name:
            total += 1
    return total


def _read_count_in_dict_values(tree: ast.AST, name: str) -> int:
    total = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for value in node.values:
                total += _read_count(value, name)
    return total


def _reads_in(path: Path) -> set[str]:
    """Names this module actually READS -- subscripts, .get() and attribute access.

    Parsed, never grepped. A name in a comment, a docstring, or an emitted column list is not
    a read, and conflating them is what made the first version of this scanner useless.
    """
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return set()
    names = set()
    for node in ast.walk(tree):
        # LOAD CONTEXT ONLY, and this is the correction that made the scanner work.
        # `scored["waiting_cost"] = ...` is a Subscript too, so counting every Subscript made
        # every producer look like a reader of its own output -- and the first fix for THAT
        # (excluding the producing module entirely) then hid the real readers, because
        # draft_room legitimately emits time_horizon_adj on the board AND sums it into
        # universal_value. Filtering on ctx separates writing a key from reading one, which is
        # the distinction the whole scanner rests on, and makes the module exclusion unnecessary.
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load) \
                and isinstance(node.slice, ast.Constant) \
                and isinstance(node.slice.value, str):
            names.add(node.slice.value)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ("get", "getdefault") and node.args \
                and isinstance(node.args[0], ast.Constant) \
                and isinstance(node.args[0].value, str):
            names.add(node.args[0].value)
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            names.add(node.attr)
    return names


def scan() -> list[dict]:
    """Every produced quantity with its verdict and the modules that read it."""
    produced = produced_quantities()
    modules = _production_modules()
    reads = {path.name: _reads_in(path) for path in modules}
    relayed = {path.name: _relayed_in(path) for path in modules}
    locals_by_module = {path.name: _local_names_in(path) for path in modules}

    rows = []
    for quantity, surface in sorted(produced.items()):
        # A module DOES count as reading its own output surface. draft_room emits
        # time_horizon_adj as a board column and also sums it into universal_value; excluding
        # self-reads called that write-only, which is the opposite of the truth. The Load-context
        # filter above already separates emitting a key from reading one, so no exclusion is
        # needed and adding one only manufactures false findings.
        readers = sorted(module for module, names in reads.items() if quantity in names)
        carriers = [m for m in readers if quantity in relayed.get(m, set())]
        consuming = [m for m in readers if m not in carriers]
        scoring = [m for m in consuming if m in SCORING_MODULES]
        observing = [m for m in consuming if m in OBSERVER_MODULES]
        producer = surface.split(".")[0] + ".py"
        used_as_local = quantity in locals_by_module.get(producer, set())
        if scoring:
            verdict = DECISION
        elif observing:
            verdict = OBSERVABLE
        elif used_as_local:
            verdict = DECOMPOSITION
        elif carriers:
            verdict = CARRIED
        else:
            verdict = WRITE_ONLY
        rows.append({"quantity": quantity, "surface": surface, "verdict": verdict,
                     "scoring_readers": scoring, "observing_readers": observing,
                     "carriers": carriers,
                     "used_as_local_in": producer if used_as_local else None})
    return rows


def write_only() -> list[dict]:
    return [row for row in scan() if row["verdict"] == WRITE_ONLY]


def main() -> int:
    rows = scan()
    by_verdict = {DECISION: [], OBSERVABLE: [], DECOMPOSITION: [], CARRIED: [], WRITE_ONLY: []}
    for row in rows:
        by_verdict[row["verdict"]].append(row)

    print(f"{len(rows)} produced quantities across the engine's declared output surfaces\n")
    for verdict, label in (
        (WRITE_ONLY, "WRITE-ONLY -- produced, read by nothing, not used as a local (#138)"),
        (DECOMPOSITION, "DECOMPOSITION -- the term works; its published form is unread (#119)"),
        (CARRIED, "CARRIED -- relayed into another output, consumed by nobody"),
        (OBSERVABLE, "OBSERVABLE -- read only by UI or diagnostics"),
        (DECISION, "DECISION -- participates in a value or an ordering"),
    ):
        group = by_verdict[verdict]
        print(f"{label}  ({len(group)})")
        for row in group:
            readers = ", ".join(row["scoring_readers"] + row["observing_readers"])
            if not readers and row.get("carriers"):
                readers = "relayed by " + ", ".join(row["carriers"])
            if not readers and row["used_as_local_in"]:
                readers = f"(local in {row['used_as_local_in']})"
            print(f"  {row['quantity']:34} {readers or '--'}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
