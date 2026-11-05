"""What an API would have to answer, sorted by WHOSE JOB each answer is -- so the API cannot
become a thin HTTP wrapper around Python's internal function structure.

WHY THIS FILE EXISTS, AND WHY IT IS NOT THE NUMBER I FIRST PUBLISHED. `boundary_census.py`
counts how far past the engine the hull reaches INTO THE VENDOR DATA LAYER -- 41 sites, 27
functions, three hand-written buckets. Asked "and how big is the engine half?", I ran the same
scanner with `DATA_MODULES` swapped for a hand-picked set of engine modules and reported **31
functions across 12 modules**. That number was an artifact of the pick. Run against EVERY module
the hull imports, the real figure is **145 distinct functions, 234 call sites, 35 modules** --
and the gap is not rounding, it is thirty modules (`todo_log`, `attachments`, `llm_engine`,
`bot_config`, ...) that a module-name heuristic quietly dropped.

So the honest shape of the problem is not "expose 31 functions". It is: THIRTY-FIVE MODULES, AND
THE WORK IS DECIDING WHOSE JOB EACH ONE IS. That decision cannot be derived -- `boundary_census`
says the same thing about its own `DATA_MODULES` ("hand-assigned on purpose: a derived rule would
mis-sort most of them") -- so this file hand-assigns a LAYER to each module, with the module's own
stated purpose as the evidence, and makes the ASSIGNMENT the thing that cannot go stale: a module
the hull newly reaches is unassigned, and an unassigned module fails `--check`.

THE OWNER ASKED FOR FIVE LAYERS. The measurement needs SEVEN, and the two extra ones are the
finding rather than a quibble:

  - `PRODUCT_STORE` -- per-league state a person reads AND WRITES (to-dos, pinned messages,
    attachments, decisions). Six modules, and none of the five named layers fits: it is not
    engine knowledge, not orchestration, not the vendor data layer, and emphatically not admin.
    A browser talks to it constantly. Left unnamed, it would have been filed under whichever
    neighbouring layer was closest, and then inherited that layer's auth.
  - `RENDER` -- the Streamlit-side rendering the rewrite REPLACES rather than exposes. Three
    modules. Naming it is what keeps them out of the API: `draft_board_ui.render_board_html` is
    a reach the hull makes 16 times and is not an endpoint under any reading.

WHAT THE LAYER NAMES MEAN, AND WHAT THEY DELIBERATELY DO NOT SETTLE. `WARPATH.md`'s standing
rule is "build the mechanism, do not let it imply the deployment", because the local-first /
central-substrate question is one `ROADMAP.md` refuses to answer and the owner's lean toward
"one independent cloud version we control" is recorded as a lean, not a decision. So read every
layer below as an EXECUTION AND TRUST boundary -- what runs outside the browser, and what holds
credentials -- never as a hosting claim. That boundary exists identically in both futures: today
Streamlit is already a local server, so "server-side" means "not in the page", not "in a data
centre". `ORCHESTRATION` holds the provider credentials whether it runs on a laptop or a host;
`PRODUCT_STORE` is per-league state a person reads and writes whether that store is a local JSON
file or a row somewhere. Nothing here should be cited as having settled the deployment model --
that must be decided as itself, which is exactly the accretion failure WARPATH names.

WHAT THIS FILE DOES NOT DECIDE. Which public operations exist. `PUBLIC_OPERATIONS` below is
DECLARED, not derived, because the operations do not exist yet -- and an operation is a product
judgement about what one coherent client request is, which is exactly the judgement that stops
the API mirroring the call graph. What IS checked: every function an operation names must really
exist, and must live in a module assigned to the layer the operation claims it from. A declared
operation that composes a function nobody wrote fails here rather than at integration.
"""

from __future__ import annotations

import argparse
import collections
import importlib
import pathlib
import sys
from unittest import mock

import boundary_census as bc

HULL = bc.HULL

#: Modules the scanner must not count as the hull's own: the hull itself, the vendor data layer
#: (`boundary_census` owns that census -- one home, `#126`), and the two shared helpers that are
#: presentation primitives rather than a layer anyone would route a request to.
NOT_A_LAYER = frozenset({"app"}) | bc.DATA_MODULES | frozenset({"design_system", "ui_source"})


#: ---------------------------------------------------------------------------------------------
#: THE LAYER ASSIGNMENT. Hand-made, one line of evidence each, for the reason
#: `boundary_census.DATA_MODULES` is hand-made. The quoted fragments are from each module's own
#: docstring: the assignment is defended by what the module says it is FOR, not by its name.
#: ---------------------------------------------------------------------------------------------

#: Deterministic knowledge a client must NEVER recompute. The engine's answers. #52's rule -- one
#: figure reads the same on every surface -- is only keepable if these never run in a browser.
ENGINE: dict[str, str] = {
    "draft_room": "'a zero-LLM, deterministic valuation engine' -- the engine itself",
    "pick_synthesis": "'deterministic synthesis layer' over the board",
    "draft_strategy": "'strategic layer on top of draft_room.py's board'",
    "player_universe": "the pool and league ownership; who is even available",
    "depth_chart": "'team -> position -> how many, and what they are worth'",
    "depth_ratings": "'peer-relative depth rating ... shared by every surface'",
    "league_config": "round arithmetic and whether a config reads cleanly (#307's one home)",
    "lineup_optimizer": "'real lineup optimization' -- slot routing is engine work",
    "lineup_readiness": "'is there a problem with my active lineup right now'",
    "league_standings": "standings off each roster's own record",
    "freshness": "the freshness manifest (#300), liftable precisely because it is engine work",
    "corpus_state": "'which body of data this session's numbers are computed from'",
}

#: Server-side composition: coordinates engine answers, provider calls and stores into ONE
#: coherent operation. Never an endpoint of its own, and never reachable from a browser -- the
#: provider credentials and the SAYING/SHOWING trust boundary both live here.
ORCHESTRATION: dict[str, str] = {
    "pick_debate": "'the LLM synthesis layer for a live draft pick, built on top of' the board",
    "llm_engine": "'multi-LLM routing engine' -- holds the credentials",
    "providers": "'the socket: what a provider must supply, declared in one place'",
    "provider_meter": "'what each provider call actually cost' -- billing truth",
    "panel_independence": "'whether two chairs agreeing is two opinions or one'",
    "screen_context": "'the one shared contract every surface uses' to hand context over",
    "untrusted": "'the boundary between what this app is SAYING and what it is SHOWING'",
    "bot_research": "'durable logs of panel-vetted output' from live web search",
    "store_io": "'one read-modify-write discipline for every JSON store' -- server only",
    "draft_history": "'append-only, content-addressed record of what the Draft Room showed'",
    "sleeper_import_report": "'run on a machine that can reach the API' -- says so itself",
    "draft_state": "'which session values belong to ONE league' -- session lifecycle",
}

#: Per-league state a person reads AND WRITES. THE LAYER THE OWNER'S FIVE DID NOT HAVE. A browser
#: talks to these directly; they carry no engine knowledge and need no admin auth.
PRODUCT_STORE: dict[str, str] = {
    "todo_log": "'per-league to-do list -- active league objectives'",
    "decision_log": "'per-league record of every Moderator verdict -- a plain audit trail'",
    "pinned_messages": "'per-league record of chat messages the user has manually pinned'",
    "attachments": "'reference material -- screenshots ... articles, injury news'",
    "upload_batches": "'an upload is a SET of files with one story'",
    "league_prefs": "'per-Sleeper-user league display preferences'",
}

#: Wants its own auth, not an endpoint on the product API. Spends money or rewrites who answers.
ADMIN: dict[str, str] = {
    "bot_config": "'which LLM provider answers for each debate persona'",
    "bot_benchmark": "'empirical model benchmarking for the Configure Bots' surface",
}

#: Streamlit-side rendering the rewrite REPLACES. Naming the layer is what keeps these out of the
#: API: 24 of the hull's reaches land here, and not one of them is an operation.
RENDER: dict[str, str] = {
    "draft_board_ui": "'the production port of the validated merged board interaction model'",
    "trade_ledger_ui": "'pure formatting/data-shaping helpers' for the trade UI",
    "draft_history_ui": "'reading a stored draft board back' -- a reader, not a record",
}

LAYERS: dict[str, dict[str, str]] = {
    "ENGINE": ENGINE,
    "ORCHESTRATION": ORCHESTRATION,
    "PRODUCT_STORE": PRODUCT_STORE,
    "ADMIN": ADMIN,
    "RENDER": RENDER,
}

#: The vendor data layer is NOT re-counted here. `boundary_census.CENSUS` is its one home, and
#: its own `# EXPOSE` bucket already names the six functions an API must answer for.
DATA_LAYER_CENSUS = "boundary_census.CENSUS"


#: ---------------------------------------------------------------------------------------------
#: DECLARED PUBLIC OPERATIONS. Not derived -- see the module docstring. Each names the engine
#: functions it composes, and `unbuildable()` checks they exist in an ENGINE-layer module.
#:
#: Only the Draft Room's are declared, deliberately: the owner's ruling is that the Draft Room
#: alpha must use "the smallest proven slice of the engine necessary to complete its actual
#: workflow", and a table of operations for pages nobody has built would be a wish-list that
#: `--check` cannot falsify. The Trade Ledger's operations get declared when that page is built,
#: because it -- not this file, and not the Draft Room -- establishes the comparison grammar.
#: ---------------------------------------------------------------------------------------------
PUBLIC_OPERATIONS: dict[str, dict[str, object]] = {
    "draft_room.board": {
        "why": "one request answers 'who, why, other valid options, at what cost' for a turn. "
               "The prototype's whole reading surface is built from one snapshot; splitting it "
               "per-figure would let a client assemble a board the engine never ordered.",
        "surfaces": ("draft_room",),
        "composes": {
            "pick_synthesis": ("build_snapshot", "snapshot_identity", "players_db_stamp",
                               "withheld_fields", "presentable_text"),
            "player_universe": ("build_player_universe", "available_players",
                                "league_usable_positions"),
            "league_config": ("round_of", "team_count"),
        },
    },
    "draft_room.depth": {
        "why": "the lineup strip and the door tanks both read positional depth; it is the same "
               "answer twice and must not be computed twice (#126).",
        "surfaces": ("draft_room",),
        "composes": {
            "depth_chart": ("positional_depth", "depth_value_label"),
            "depth_ratings": ("depth_label",),
        },
    },
    "draft_room.freshness": {
        "why": "the league line's 'as of' mark and the front page's staleness grade are the same "
               "manifest read at two altitudes.",
        "surfaces": ("draft_room", "front"),
        "composes": {"freshness": ("build_freshness_manifest",),
                     "corpus_state": ("assess",)},
    },
}


def reaches(path: pathlib.Path = HULL) -> collections.Counter:
    """Every call the hull makes into one of ITS OWN modules, as `{"module.function": count}`.

    Uses `boundary_census.reaches` with its module set swapped rather than a second scanner: the
    shape that census had to learn -- `instance.method(...)` is a reach and is invisible to a
    module-level scan, which is how an earlier count missed 23 of 44 sites -- is a lesson this
    file gets for free by not re-implementing it (#126).
    """
    population = frozenset(assignable(path.parent if path.parent.name else pathlib.Path(".")))
    with mock.patch.object(bc, "DATA_MODULES", population), \
         mock.patch.object(bc, "DATA_INSTANCES", frozenset()):
        return bc.reaches(path)


def assignable(root: pathlib.Path = pathlib.Path(".")) -> list[str]:
    """Every root module that is a candidate for a layer: the repo's own importable modules,
    less the hull, the vendor data layer, the presentation primitives, and the harnesses."""
    out = []
    for p in sorted(root.glob("*.py")):
        name = p.stem
        if name.startswith(("test_", "run_", "_")) or name in NOT_A_LAYER:
            continue
        out.append(name)
    return out


def layer_of(module: str) -> str | None:
    for name, members in LAYERS.items():
        if module in members:
            return name
    return None


def unassigned(path: pathlib.Path = HULL) -> list[str]:
    """Modules the hull reaches that no layer claims. THE RATCHET. A new module wired into the
    hull is a new thing somebody must decide the ownership of; until then it is not in the
    inventory, and an inventory with a hole in it is worse than one that says so."""
    return sorted({reach.split(".", 1)[0] for reach in reaches(path)
                   if layer_of(reach.split(".", 1)[0]) is None})


def double_assigned() -> list[str]:
    """A module in two layers. Two owners is no owner."""
    seen: collections.Counter = collections.Counter()
    for members in LAYERS.values():
        seen.update(members.keys())
    return sorted(m for m, n in seen.items() if n > 1)


def unbuildable() -> list[str]:
    """Declared operations that name something nobody wrote, or that reach outside ENGINE.

    An operation composing an ORCHESTRATION or PRODUCT_STORE function is not wrong in principle,
    but it is not what this check is for: it would mean a public operation reaching past the
    engine's answers, which is the shape `boundary_census` exists to count. So it is reported
    here and routed deliberately rather than admitted quietly.
    """
    out = []
    for op, spec in sorted(PUBLIC_OPERATIONS.items()):
        for module, functions in sorted(spec["composes"].items()):  # type: ignore[union-attr]
            layer = layer_of(module)
            if layer != "ENGINE":
                out.append(f"{op}: composes {module}, which is {layer or 'UNASSIGNED'}, not ENGINE")
                continue
            try:
                mod = importlib.import_module(module)
            except BaseException as exc:
                out.append(f"{op}: {module} does not import ({type(exc).__name__}: {exc})")
                continue
            for fn in functions:
                if not hasattr(mod, fn):
                    out.append(f"{op}: {module}.{fn} does not exist")
    return out


def slice_for(surface: str) -> dict[str, tuple[str, ...]]:
    """The engine functions one surface's declared operations need -- the Live Alpha boundary.

    The owner's ruling: the Draft Room alpha uses the smallest proven slice, not the whole
    inventory. This is that slice, derived from the operations rather than restated beside them.
    """
    out: dict[str, set[str]] = collections.defaultdict(set)
    for spec in PUBLIC_OPERATIONS.values():
        if surface not in spec["surfaces"]:  # type: ignore[operator]
            continue
        for module, functions in spec["composes"].items():  # type: ignore[union-attr]
            out[module].update(functions)
    return {m: tuple(sorted(fns)) for m, fns in sorted(out.items())}


def report(path: pathlib.Path = HULL) -> list[str]:
    found = reaches(path)
    per_layer: dict[str, collections.Counter] = {name: collections.Counter() for name in LAYERS}
    per_layer["UNASSIGNED"] = collections.Counter()
    for reach, n in found.items():
        per_layer[layer_of(reach.split(".", 1)[0]) or "UNASSIGNED"][reach] += n

    lines = [f"the hull reaches its own modules {sum(found.values())} times, "
             f"{len(found)} distinct functions, "
             f"{len({r.split('.', 1)[0] for r in found})} modules", ""]
    for name in list(LAYERS) + ["UNASSIGNED"]:
        counts = per_layer[name]
        if not counts and name == "UNASSIGNED":
            lines.append("UNASSIGNED           --  none; every module the hull reaches has an owner")
            continue
        mods = sorted({r.split(".", 1)[0] for r in counts})
        lines.append(f"{name:20s} {sum(counts.values()):4d} calls  "
                     f"{len(counts):3d} functions  {len(mods):2d} modules")
        for m in mods:
            fns = sorted(r.split(".", 1)[1] for r in counts if r.startswith(m + "."))
            lines.append(f"    {m:22s} {len(fns):2d}  {', '.join(fns[:6])}"
                         + (" ..." if len(fns) > 6 else ""))
    lines += ["", f"DATA LAYER            {sum(bc.CENSUS.values()):4d} calls  "
                  f"{len(bc.CENSUS):3d} functions   -- counted in {DATA_LAYER_CENSUS}, not here",
              "", f"declared public operations: {len(PUBLIC_OPERATIONS)}"]
    for op, spec in sorted(PUBLIC_OPERATIONS.items()):
        n = sum(len(f) for f in spec["composes"].values())  # type: ignore[union-attr]
        lines.append(f"    {op:24s} composes {n:2d} engine functions  "
                     f"for {', '.join(spec['surfaces'])}")  # type: ignore[arg-type]
    draft = slice_for("draft_room")
    lines += ["", "THE DRAFT ROOM LIVE ALPHA SLICE -- "
                  f"{sum(len(v) for v in draft.values())} engine functions in {len(draft)} modules"]
    for m, fns in draft.items():
        lines.append(f"    {m:22s} {', '.join(fns)}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="fail if a reached module has no layer, or an operation is unbuildable")
    args = parser.parse_args(argv)

    if not args.check:
        print("\n".join(report()))
        return 0

    problems = []
    for module in unassigned():
        problems.append(f"UNASSIGNED MODULE: {module} -- the hull reaches it and no layer claims "
                        f"it. Decide whose job it is (ENGINE / ORCHESTRATION / PRODUCT_STORE / "
                        f"ADMIN / RENDER) and record the evidence, or route the reach away.")
    for module in double_assigned():
        problems.append(f"TWO LAYERS CLAIM {module}: two owners is no owner.")
    problems += unbuildable()
    if problems:
        print("\n".join(problems))
        return 1
    draft = slice_for("draft_room")
    print(f"every module the hull reaches has an owner; {len(PUBLIC_OPERATIONS)} declared "
          f"operations all buildable; the draft room's slice is "
          f"{sum(len(v) for v in draft.values())} engine functions in {len(draft)} modules")
    return 0


if __name__ == "__main__":
    sys.exit(main())
