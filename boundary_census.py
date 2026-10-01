"""How far past the engine the hull reaches, counted so it cannot widen unnoticed.

Phase 2 of the post-freeze roadmap asked one question: what does `app.py` reach for that is NOT
the engine's public answer? The answer inverted the assumption -- the hull calls the vendor data
layer MORE times than it calls the engine (44 against 38). Every one of those 44 is something a
non-Streamlit client would have to reproduce, or that the API must answer.

WHY THIS IS A GUARD AND NOT JUST A REPORT. A markdown table of the census goes stale the first
time someone adds a call, and nothing says so -- which is the failure this repository spends most
of its instruments preventing. Executed, the census is a ratchet: a new reach fails the test, and
the fix is either to route it through the engine or to register it with a reason.

IT IS ALSO PHASE 6'S ACCEPTANCE TEST, BUILT EARLY. When the Streamlit app is rewritten as an API
client, the claim to prove is "it reaches the data layer zero times". That is this number going to
nought, mechanically, rather than by inspection. GROWTH is the regression here; shrinkage is the
project working.

WHAT IT DOES NOT CLAIM. A reach being in the data layer does not prove it is misplaced --
`pick_value` may belong to the engine or to a trade service, and this file does not decide that.
It counts where the hull goes, and refuses to let that number rise quietly.
"""

from __future__ import annotations

import argparse
import ast
import collections
import pathlib
import sys

HULL = pathlib.Path("app.py")

#: Modules that ARE the vendor data layer. Hand-assigned on purpose: "is this the data layer" is
#: a judgement about what a module is FOR, and a derived rule (does it read a file? live at
#: root?) would mis-sort most of them.
DATA_MODULES = frozenset({"data_merger", "sleeper_client", "league_format"})

#: Instance names in `app.py` that hold a data-layer object. `merger.merge_player(...)` is a reach
#: and is invisible to a module-level scan, which is how an earlier count of this boundary missed
#: 23 of its 44 call sites.
DATA_INSTANCES = frozenset({"merger", "client"})

#: The census as measured at `2918631`, the commit that first counted it. The number on the right
#: is a CEILING, not a target: it may fall freely -- that is Phase 6 happening -- and may not rise
#: without a deliberate edit here. Keyed by reach rather than by line, because line numbers move
#: under any edit and the set of distinct questions the hull asks does not.
CENSUS: dict[str, int] = {
    # EXPOSE -- the API must answer these. See evidence/boundary_audit/.
    "merger.merge_player": 5,
    "merger.pick_value": 4,
    "merger.composite_player_score": 1,
    "merger.external_player_values": 1,
    "merger.build_roster_table": 1,
    "merger.list_free_agents": 1,
    # MOVE SERVER-SIDE -- the client never talks to Sleeper.
    "client.sync_league": 2,
    "client.get_players": 2,
    "client.get_user": 1,
    "client.get_user_leagues": 1,
    "client.get_league": 1,
    "sleeper_client.SleeperClient": 1,
    "sleeper_client.compute_points_from_stats": 1,
    "sleeper_client.find_roster_for_user": 1,
    "sleeper_client.league_format_summary": 2,
    "sleeper_client.players_freshness_entry": 1,
    "sleeper_client.priceable_season_projections": 1,
    "sleeper_client.season_projection_freshness_entry": 1,
    # ADMIN SURFACE -- wants its own auth, not an endpoint on the product API.
    "merger.reload": 2,
    "merger.composite_capable_source_names": 1,
    "data_merger.DataMerger": 3,
    "data_merger.save_alias": 1,
    "data_merger.remove_alias": 1,
    "data_merger.load_projection_file": 1,
    "data_merger.external_upload_targets": 1,
    "data_merger.recency_grade": 1,
    "data_merger.horizon_gap_lines": 1,
    "league_format.get_format_override": 2,
    "league_format.set_format_override": 2,
}


def reaches(path: pathlib.Path = HULL) -> collections.Counter:
    """Every data-layer call site in the hull, as `{"owner.function": count}`.

    Catches BOTH shapes: `module.func(...)` for an imported module, and `instance.method(...)`
    for a held data-layer object. Missing the second is how this boundary reads as half its real
    size.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))

    alias_to_module, name_to_module = {}, {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                root = a.name.split(".")[0]
                if root in DATA_MODULES:
                    alias_to_module[a.asname or a.name] = root
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            if root in DATA_MODULES:
                for a in node.names:
                    name_to_module[a.asname or a.name] = root

    found: collections.Counter = collections.Counter()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            base = func.value.id
            if base in alias_to_module:
                found[f"{alias_to_module[base]}.{func.attr}"] += 1
            elif base in DATA_INSTANCES:
                found[f"{base}.{func.attr}"] += 1
        elif isinstance(func, ast.Name) and func.id in name_to_module:
            found[f"{name_to_module[func.id]}.{func.id}"] += 1
    return found


def widened(path: pathlib.Path = HULL) -> list[str]:
    """Reaches that are new, or more numerous than the census allows. Shrinkage is not reported:
    a reach going away is the whole point of the work this file guards."""
    found = reaches(path)
    out = []
    for reach, count in sorted(found.items()):
        allowed = CENSUS.get(reach)
        if allowed is None:
            out.append(f"NEW REACH: {reach} x{count} -- the hull now asks the data layer a "
                       f"question it did not before. Route it through the engine, or add it to "
                       f"CENSUS with a reason.")
        elif count > allowed:
            out.append(f"{reach}: {allowed} -> {count} call sites")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="fail if the boundary widened")
    args = parser.parse_args(argv)

    found = reaches()
    total, allowed_total = sum(found.values()), sum(CENSUS.values())
    if not args.check:
        for reach, count in sorted(found.items(), key=lambda kv: (-kv[1], kv[0])):
            ceiling = CENSUS.get(reach)
            mark = " NEW" if ceiling is None else ("" if count <= ceiling else " WIDENED")
            print(f"  {reach:48s} {count:3d}{mark}")
        print(f"\n{total} data-layer reaches in {HULL} (census allows {allowed_total})")
        return 0

    grew = widened()
    if grew:
        for line in grew:
            print(line)
        return 1
    gone = allowed_total - total
    print(f"the boundary has not widened: {total} data-layer reaches, census allows "
          f"{allowed_total}" + (f" ({gone} fewer than recorded -- that is progress)" if gone else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
