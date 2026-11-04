"""The roster depth chart: team -> position -> how many, and what they are worth.

WHY THIS IS A MODULE AND NOT TWO FUNCTIONS IN `app.py`. It was two functions in `app.py`, and the
cost showed up as a comment in each of its own consumers. `depth_value_label`'s docstring says it
is "a function rather than an inline ternary" because "app.py cannot be imported (it is a
Streamlit script), so a named top-level function is what makes the behaviour reachable by a test
at all" -- a workaround, named as one. And `test_positional_depth_coverage` reached
`positional_depth` by PARSING the surface and exec-ing the single FunctionDef out of it, with its
own docstring conceding that "the alternative -- moving it into an importable module -- is the
hull extraction (#137)".

This is that move, for the one function the front-page work needed. `app.py` has 69 top-level
Streamlit calls and no `__main__` guard, so importing it runs the application; a quantity three
surfaces depend on therefore had no reader outside the app. No fixture, no harness and no
prototype could compute "thin at TE" without re-implementing it, and a second implementation is a
second source of truth (`#126`).

IT IMPORTS NOTHING, deliberately -- the same posture `draft_state.py` and `content_hash.py` take,
and for the same reason: a module a test can import without standing up a session is the whole
point, and `DataMerger` appears here only as an annotation. `from __future__ import annotations`
makes that a string at runtime, so the type is available to a checker and costs nothing to import.

WHAT MOVED AND WHAT DID NOT. Both function bodies are byte-identical to what stood in `app.py` --
they were lifted by AST span rather than retyped, so there is no transcription to audit. The six
call sites in `app.py` are untouched: it imports the two names, so `positional_depth(player_universe,
merger)` still reads exactly as it did, which also keeps `test_maintenance_view_wiring`'s anchor
intact. What DID change is the boundary census: `app.py`'s direct `merger.merge_player` reaches
drop from 5 to 4, because the depth chart's call travelled with the function. `boundary_census`
calls that progress rather than a failure -- "a reach going away is the whole point of the work
this file guards" -- and the ceiling is tightened to 4 in the same commit so the hull cannot
silently re-widen into the slack it just gave up.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:                      # pragma: no cover - annotation only, never imported at runtime
    from data_merger import DataMerger


def positional_depth(player_universe: list[dict], merger: DataMerger) -> dict[str, dict[str, dict]]:
    """team -> position -> {"count": n, "value": sum or None}.

    Count alone treats a pile of backups the same as three stacked stars at the same
    position -- real depth is about quality, not just bodies. `value` sums each
    player's Draft Sharks trade_value (Dynasty Rankings) where a match exists, so a
    QB room with Mahomes/Dak/Lamar reads very differently from three replacement-level
    arms even though both are "3 QBs." Only computed when merger.is_loaded -- with no
    Draft Sharks data at all, value stays None for every cell and callers fall back to
    count alone, per this app's usual "work with whatever is loaded" rule.

    `valued_count` IS THE SCOPE OF `value`, AND IT IS NOT `count` (#190). Every rostered
    player raises `count`; only the ones the merger could price raise `value`. The two
    therefore describe DIFFERENT SETS while sitting in one cell, and a reader who takes
    `value` for the room's total is reading a floor as a sum. Measured against the real
    capture on a synthetic 12-team league: 33 of 96 cells had 0 < valued_count < count, the
    worst a seven-man WR room whose entire value came from ONE priced player.

    The number is NOT withdrawn when coverage is partial -- a partial sum is real evidence,
    and three priced stars still outrank three priced scrubs. What changes is that the cell
    carries what the sum COVERS, so a consumer can say "at least" instead of "is". Same shape
    as horizon_basis (#166), availability_basis (#191) and depth_basis (#174): the quantity
    was fine, it was crossing without the thing that scopes it.
    """
    depth: dict[str, dict[str, dict]] = {}
    for row in player_universe:
        if row.get("ownership") != "ROSTERED":
            continue
        team_label = row.get("owner_name") or f"Roster {row.get('roster_id', '?')}"
        position = row["position"]
        cell = depth.setdefault(team_label, {}).setdefault(
            position, {"count": 0, "value": None, "valued_count": 0})
        cell["count"] += 1
        if merger.is_loaded:
            match = merger.merge_player(row["name"], position=position, team=row.get("team"))
            trade_value = match.get("trade_value")
            if trade_value is not None:
                cell["valued_count"] += 1
                cell["value"] = (cell["value"] or 0) + trade_value
    return depth


def depth_value_label(cell: dict) -> str:
    """The parenthetical after a depth count -- "at least", not "is", when the sum is partial.

    #190: `count` rises for every rostered player and `value` only for the ones the merger
    could price, so the two describe different sets inside one cell. A chair handed `WR 7 (7)`
    reads seven receivers worth seven points; the truth was seven receivers of whom ONE could
    be priced, at seven points. Measured on the real capture: 33 of 96 cells were partial, the
    worst a seven-man room carrying one man's value.

    A FUNCTION RATHER THAN AN INLINE TERNARY, and for a reason a mutation found: written
    inline, a guard could only check that the format string was PRESENT in app.py, which a
    mutation that disabled the branch left untouched -- the test passed while a partial sum
    rendered as a plain total again. app.py cannot be imported (it is a Streamlit script), so
    a named top-level function is what makes the behaviour reachable by a test at all.
    """
    if cell.get("value") is None:
        return ""
    covered = cell.get("valued_count")
    if covered is not None and covered < cell.get("count", 0):
        return f" (>={cell['value']:.0f}, {covered} of {cell['count']} priced)"
    return f" ({cell['value']:.0f})"
